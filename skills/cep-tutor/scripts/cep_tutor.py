# /// script
# requires-python = ">=3.10"
# dependencies = ["pypdf>=4.0.0", "olefile>=0.47", "reportlab>=4.0.0"]
# ///
"""Tutor de pré-submissão ao CEP-UMC: orquestração determinística.

Subcomandos:
  prepare  extrai e classifica os documentos, faz a triagem, roda os sinais automáticos e escreve os prompts
  next     confere as avaliações escritas e lista as tarefas pendentes
  run      executa as tarefas pendentes por `claude -p` / `agy -p` / `gemini -p`
  compile  junta as avaliações, aplica as regras da base (IDs, severidade, nível) e escreve o relatório
  planejar sem documentos: a partir das respostas de triagem, lista os documentos necessários, assinaturas e prazos

A avaliação é finita: cada protocolo tem no máximo MAX_RODADAS rodadas de revisão (padrão 3); da 2ª em diante os
revisores verificam o que já foi apontado e não abrem frentes novas (salvo problema ético grave); cada tarefa tem no
máximo MAX_TENTATIVAS tentativas; cada bloco do relatório tem um número máximo de itens.

Exemplo:
  cep_tutor.py prepare --input protocolo/ --output-dir cep_tutor/meu-projeto
  (avaliar as tarefas de .tasks/manifest.json)
  cep_tutor.py compile --output-dir cep_tutor/meu-projeto
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import checks as ck  # noqa: E402
import classify as cl  # noqa: E402
import extract as ex  # noqa: E402
import kb  # noqa: E402
import report  # noqa: E402
from security import UNTRUSTED_TAG, sanitize_and_scan  # noqa: E402

VERSION = "0.2.0"
MAX_DOC_CHARS = 250000  # ~40 mil palavras: cobre projetos de dissertação e tese
MAX_RODADAS = 3
MAX_TENTATIVAS = 2
LIMITE_ESSENCIAL = {"graduacao": 5, "especializacao": 6, "mestrado": 8, "doutorado": 8, "docente": 8}
LIMITE_APROFUNDAR = 5
LIMITE_RECOMENDACOES = 8
TERMOS = ("tcle", "tcle_virtual", "tale", "tcle_responsavel", "tcle_amostra")

NIVEL_LABEL = {
    "graduacao": "graduação (IC/TCC)",
    "especializacao": "especialização ou residência",
    "mestrado": "mestrado",
    "doutorado": "doutorado",
    "docente": "pesquisa docente",
}

TOM_A = {
    "graduacao": "Formativo: o pesquisador pode ser aluno de graduação. Explique em uma frase por que cada requisito existe.",
    "especializacao": "Formativo e objetivo: explique brevemente por que cada requisito existe.",
    "mestrado": "Técnico e objetivo.",
    "doutorado": "Técnico e objetivo.",
    "docente": "Direto e conciso: o apontamento e a fonte.",
}
TOM_B = {
    "graduacao": "formativo e encorajador; conceito em linguagem simples com um exemplo",
    "especializacao": "formativo e objetivo",
    "mestrado": "técnico, com explicação breve e referência metodológica específica",
    "doutorado": "técnico, com explicação breve e referência metodológica específica",
    "docente": "direto e conciso: apontamento técnico e referência",
}
CAMPOS_B = {
    "graduacao": "`sugestao`, `por_que` (linguagem simples, com exemplo), `reflexao` (uma pergunta para o aluno), `como_melhorar`, `para_estudar`",
    "especializacao": "`sugestao`, `por_que`, `reflexao` (uma pergunta), `como_melhorar`, `para_estudar`",
    "mestrado": "`sugestao`, `por_que` (breve), `como_melhorar`, `para_estudar`; `reflexao` vazia",
    "doutorado": "`sugestao`, `por_que` (breve), `como_melhorar`, `para_estudar`; `reflexao` vazia",
    "docente": "`sugestao`, `como_melhorar`, `para_estudar`; `por_que` em uma linha; `reflexao` vazia",
}
FRONTEIRA_B = (
    "ortografia, gramática e frases completas (PROJ-G02, GER-08); presença e justificativa do número de participantes "
    "(PROJ-M02); presença do plano de análise (PROJ-C07); objetivos no infinitivo (PROJ-C04, PROJ-C05); hipótese afirmativa "
    "(PROJ-C02); exclusão como antítese da inclusão (PROJ-M05); referências em ABNT (PROJ-C14); riscos, benefícios, "
    "cronograma, orçamento, TCLE, TALE e demais documentos"
)

KB_ALWAYS = ["03-projeto-de-pesquisa.md", "11-plataforma-brasil-submissao.md", "16-checklist-pre-submissao.md", "17-erros-frequentes-e-sinais-de-alerta.md"]
KB_BY_TYPE = {
    "tcle": ["04-tcle.md", "14-direitos-dos-participantes.md"],
    "tcle_virtual": ["04-tcle.md", "05-tcle-ambiente-virtual.md", "14-direitos-dos-participantes.md"],
    "tale": ["04-tcle.md", "06-tale-e-tcle-responsavel.md"],
    "tcle_responsavel": ["04-tcle.md", "06-tale-e-tcle-responsavel.md"],
    "tcle_amostra": ["04-tcle.md", "07-tcle-cessao-amostra-biologica.md"],
    "dispensa": ["08-dispensa-tcle.md"],
    "tai": ["09-tai-autorizacao-institucional.md"],
    "termo_anuencia": ["09-tai-autorizacao-institucional.md"],
    "anuencia_assistencia": ["10-carta-anuencia-assistencia-gratuita.md"],
    "carta_resposta": ["12-tramitacao-pareceres-pendencias.md"],
}
KB_BY_Q = {"Q2": "06-tale-e-tcle-responsavel.md", "Q3": "05-tcle-ambiente-virtual.md", "Q4": "07-tcle-cessao-amostra-biologica.md",
           "Q6": "08-dispensa-tcle.md", "Q7": "09-tai-autorizacao-institucional.md", "Q8": "10-carta-anuencia-assistencia-gratuita.md"}
ACAD_FILES = ["01-metodologia.md", "02-estatistica.md", "03-escrita.md", "04-diretrizes-de-relato.md", "05-expectativas-por-nivel.md"]

CEP_LANGUAGE = re.compile(r"\b(o cep (exige|exigirá|vai exigir|cobra)|pode gerar pendência|gerar pendência|bloqueante|\[pendência\])", re.I)


# ----------------------------------------------------------------------------- utilidades

def slug(s: str) -> str:
    s = cl.norm(s)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60] or "documento"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def parse_findings(text: str) -> dict | None:
    blocks = re.findall(r"```json\s+FINDINGS_JSON\s*\n(.*?)\n```", text, re.S)
    if not blocks:
        return None
    try:
        return json.loads(blocks[-1])
    except json.JSONDecodeError:
        return None


def collect_inputs(inputs: list[str], output_dir: Path) -> list[Path]:
    files: list[Path] = []
    for i in inputs:
        p = Path(i)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix.lower() in ex.SUPPORTED and not any(part.startswith(".") for part in f.relative_to(p).parts):
                    if output_dir.resolve() in f.resolve().parents:
                        continue
                    files.append(f)
        elif p.is_file():
            files.append(p)
        else:
            raise SystemExit(f"Entrada não encontrada: {i}")
    return files


def parse_kv(items: list[str] | None, what: str) -> dict[str, str]:
    out = {}
    for it in items or []:
        if "=" not in it:
            raise SystemExit(f"{what}: use CHAVE=VALOR ({it!r})")
        k, v = it.split("=", 1)
        out[k.strip()] = v.strip()
    return out


# ----------------------------------------------------------------------------- prepare

def kb_for_track_a(types: set[str], tri: dict) -> str:
    files: list[str] = []
    for f in KB_ALWAYS:
        files.append(f)
    for t in sorted(types):
        files += KB_BY_TYPE.get(t, [])
    for q, f in KB_BY_Q.items():
        if tri.get(q, {}).get("valor"):
            files.append(f)
    seen: list[str] = []
    for f in files:
        if f not in seen:
            seen.append(f)
    order = sorted(seen)
    parts = []
    disc = kb.kb_file("00-fontes-e-discrepancias.md")
    m = re.search(r"## Discrepâncias.*?(?=\n## )", disc, re.S)
    parts.append("### Discrepâncias (00-fontes-e-discrepancias.md)\n\n" + (m.group(0).split("\n", 1)[1] if m else disc))
    for f in order:
        parts.append(f"### Arquivo `{f}`\n\n" + kb.kb_file(f))
    return "\n\n---\n\n".join(parts)


def kb_for_track_b() -> str:
    return "\n\n---\n\n".join(f"### Arquivo `{f}`\n\n" + kb.kb_file(f, academic=True) for f in ACAD_FILES if (kb.ACAD_DIR / f).exists())


def docs_block(docs: list[dict], types: tuple[str, ...] | None = None) -> str:
    out = []
    for d in docs:
        if types and d["tipo"] not in types:
            continue
        text = d["text"]
        cut = ""
        if len(text) > MAX_DOC_CHARS:
            text, cut = text[:MAX_DOC_CHARS], f"\n[... documento truncado em {MAX_DOC_CHARS} caracteres ...]"
        out.append(
            f"### Documento `{d['arquivo']}` — {cl.DOC_LABELS[d['tipo']]}\n\n<{UNTRUSTED_TAG}>\n{text}{cut}\n</{UNTRUSTED_TAG}>"
        )
    return "\n\n".join(out) or "(nenhum documento deste tipo)"


def triage_md(tri: dict) -> str:
    rows = ["| Q | Pergunta | Resposta | Confiança | Evidência |", "|---|---|---|---|---|"]
    for q, d in tri.items():
        v = d.get("valor")
        if q == "Q21":
            resp = NIVEL_LABEL.get(v, "não identificado") if v else f"não identificado (assumido: {NIVEL_LABEL['graduacao']})"
        else:
            resp = "sim" if v is True else ("não" if v is False else "sem evidência")
        ev = "; ".join(f"“…{e}…”" for e in d.get("evidencias", [])[:1])
        rows.append(f"| {q} | {d['pergunta']} | {resp} | {d.get('confianca', '')} | {ev} |")
    return "\n".join(rows)


def inventory_md(inv: list[dict]) -> str:
    rows = ["| Documento | Obrigatório | Motivo | Recebido |", "|---|---|---|---|"]
    for i in inv:
        rec = ", ".join(f"`{a}`" for a in i["arquivos"]) if i["arquivos"] else ("só dentro do projeto" if i.get("no_projeto") else "**não**")
        rows.append(f"| {i['rotulo']} | {'sim' if i['obrigatorio'] else 'se aplicável'} | {i['motivo']} | {rec} |")
    return "\n".join(rows)


def sinais_md(sinais: list[dict]) -> str:
    if not sinais:
        return "Nenhum."
    rows = ["| Ref | ID | Documento | Sinal | Trecho | Confiança |", "|---|---|---|---|---|---|"]
    for s in sinais:
        tr = s["trecho"].replace("|", "/")[:160]
        rows.append(f"| {s['ref']} | {s['id']} | `{s['arquivo']}` | {s['mensagem']} | {tr} | {s['confianca']} |")
    return "\n".join(rows)


def render(template: str, values: dict[str, str]) -> str:
    for k, v in values.items():
        template = template.replace(f"<<{k}>>", v)
    left = re.findall(r"<<[a-z_]+>>", template)
    if left:
        raise RuntimeError(f"Marcadores não preenchidos: {left}")
    return template


def fingerprint(docs: list[dict], extra: dict) -> str:
    h = hashlib.sha256()
    for d in sorted(docs, key=lambda x: x["arquivo"]):
        h.update(d["arquivo"].encode())
        h.update(d["tipo"].encode())
        h.update(d["text"].encode())
    h.update(json.dumps(extra, sort_keys=True).encode())
    return h.hexdigest()[:16]


def historico(out: Path) -> list[dict]:
    """Resumos compilados anteriores (um por versão dos documentos), do mais antigo ao mais recente."""
    hdir = out / "historico"
    if not hdir.exists():
        return []
    items = [load_json(p, {}) for p in hdir.glob("*.json")]
    return sorted((i for i in items if i), key=lambda i: i.get("gerado_em", ""))


def _anteriores_md(track: str, anterior: dict) -> str:
    if track == "A":
        rows = [f"- `{f['id']}` ({f.get('documento') or '-'}): {f.get('problema') or f.get('requisito', '')[:120]}"
                for f in (anterior.get("trilha_a") or {}).get("achados", [])]
    else:
        tb = anterior.get("trilha_b") or {}
        rows = [f"- `{s.get('id') or 'sem ID'}`: {s.get('sugestao', '')[:140]}" for s in tb.get("essencial", []) + tb.get("aprofundar", [])]
    return "\n".join(rows) or "(nenhum item na rodada anterior)"


def rodada_md(track: str, rodada: int, max_rodadas: int, anterior: dict | None) -> str:
    if rodada == 1 or not anterior:
        return f"Rodada 1 de no máximo {max_rodadas}. Avalie o protocolo completo."
    head = f"Rodada {rodada} de no máximo {max_rodadas}. O pesquisador corrigiu o protocolo depois da rodada anterior."
    if track == "A":
        regra = (
            "**Modo verificação.** Para cada item da rodada anterior, verifique se foi resolvido: repita no JSON só os que "
            "**persistem**, com o mesmo ID. Aponte itens **novos** apenas se forem [BLOQUEANTE] ou [PENDÊNCIA] (problema ético "
            "ou documental real que a correção introduziu ou que a rodada anterior não viu); recomendações novas não entram. "
            "Não reabra pontos resolvidos nem troque o ID de um mesmo problema."
        )
        if rodada > max_rodadas:
            regra += " **Ciclo encerrado:** esta é a última verificação; seja conciso."
    else:
        regra = (
            "**Modo verificação.** Verifique só as sugestões da rodada anterior: repita no JSON as que **persistem**, com o "
            "mesmo ID. **Não acrescente sugestões novas**, exceto itens de núcleo comum que a correção tenha introduzido. "
            "Não reabra pontos já resolvidos."
        )
    return f"{head}\n\n{regra}\n\nItens da rodada anterior:\n\n{_anteriores_md(track, anterior)}"


def cmd_prepare(a: argparse.Namespace) -> int:
    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = collect_inputs(a.input, out)
    if not files:
        raise SystemExit("Nenhum documento suportado na entrada (.docx, .doc, .pdf, .md, .txt, .odt, .rtf, .html).")
    tipo_override = parse_kv(a.tipo, "--tipo")
    q_override = parse_kv(a.q, "--q")
    trilhas = {t.strip().upper() for t in a.trilhas.split(",") if t.strip()}

    docs: list[dict] = []
    failures, integrity, alerts = [], [], []
    for f in files:
        e = ex.extract(f)
        if not e.ok:
            failures.append({"arquivo": f.name, "erro": e.error})
            continue
        text, scan = sanitize_and_scan(e.text)
        if not scan["is_clean"]:
            integrity.append({"arquivo": f.name, **scan})
        if e.hidden:
            integrity.append({"arquivo": f.name, "texto_oculto": e.hidden[:10]})
        c = cl.classify_document(f.name, text)
        tipo = tipo_override.get(f.name, c.tipo)
        if tipo not in cl.DOC_LABELS:
            raise SystemExit(f"--tipo {f.name}={tipo}: tipo inválido; use um de {sorted(cl.DOC_LABELS)}")
        docs.append({
            "arquivo": f.name, "caminho": str(f), "tipo": tipo, "confianca": "informado" if f.name in tipo_override else c.confianca,
            "contem": c.contem, "pontos_projeto": c.pontos.get("projeto", 0), "method": e.method, "words": e.words, "colored": e.colored, "hidden": len(e.hidden), "text": text,
        })
        write(out / "documentos" / f"{slug(f.stem)}.txt", text)
        if len(text) > MAX_DOC_CHARS:
            alerts.append(f"`{f.name}` tem {len(text)} caracteres e foi truncado em {MAX_DOC_CHARS} para a revisão: o final do documento não foi lido.")
        if e.colored:
            alerts.append(f"`{f.name}`: {len(e.colored)} trecho(s) em vermelho ou azul (cores dos modelos).")

    projetos = [d for d in docs if d["tipo"] == "projeto"]
    projeto = max(projetos, key=lambda d: d["pontos_projeto"]) if projetos else None
    if len(projetos) > 1:
        alerts.append("Mais de um documento classificado como projeto: " + ", ".join(f"`{d['arquivo']}`" for d in projetos)
                      + f". Usado na triagem: `{projeto['arquivo']}`.")
    tri = cl.triage({d["arquivo"]: d["text"] for d in docs}, projeto["text"] if projeto else None)
    for q, v in q_override.items():
        q = q.upper()
        if q not in tri:
            raise SystemExit(f"--q {q}: pergunta desconhecida")
        if q == "Q21":
            continue
        tri[q].update({"valor": v.lower() in ("sim", "s", "true", "1"), "confianca": "informado", "evidencias": []})
    if a.nivel:
        tri["Q21"].update({"valor": a.nivel, "confianca": "informado", "evidencias": []})
        tri["Q16"].update({"valor": a.nivel == "graduacao", "confianca": "informado"})
    nivel = tri["Q21"].get("valor") or "graduacao"
    nivel_fonte = "informado pelo usuário" if tri["Q21"]["confianca"] == "informado" else (
        f"identificado no projeto, confiança {tri['Q21']['confianca']}" if tri["Q21"].get("valor") else "não identificado: assumido graduação")

    present: dict[str, list[str]] = {}
    for d in docs:
        present.setdefault(d["tipo"], []).append(d["arquivo"])
    in_project = set(projeto["contem"]) if projeto else set()
    inv = cl.inventory(cl.expected_documents(tri), present)
    for i in inv:
        i["no_projeto"] = i["tipo"] in in_project

    sinais, info = ck.run_checks(docs, [d["arquivo"] for d in docs], date.fromisoformat(a.hoje) if a.hoje else None)
    nxt = len(sinais)

    def add_sinal(rid: str, arq: str, tipo: str, msg: str, conf: str) -> None:
        nonlocal nxt
        nxt += 1
        sinais.append({"ref": f"AUTO-{nxt:03d}", "id": rid, "arquivo": arq, "tipo_doc": tipo, "trecho": "", "mensagem": msg, "confianca": conf})

    for i in inv:
        if i["presente"]:
            continue
        if i["no_projeto"]:
            add_sinal(i["id"], "(protocolo)", i["tipo"], f"{i['rotulo']} aparece só dentro do projeto: anexar também como arquivo separado na Plataforma.", "media")
        elif i["obrigatorio"]:
            add_sinal(i["id"], "(protocolo)", i["tipo"], f"{i['rotulo']} não foi recebido. Motivo: {i['motivo']}.", "media" if i["tipo"] != "folha_rosto" else "baixa")
    if projeto:
        for d in docs:
            if d["tipo"] in (*TERMOS, "tai", "anuencia_assistencia", "termo_anuencia", "instrumento", "dispensa") and d["tipo"] not in in_project:
                add_sinal("PROJ-G07", d["arquivo"], d["tipo"], f"{cl.DOC_LABELS[d['tipo']]} não parece estar anexado ao final do projeto.", "baixa")

    extra = {"tipos": tipo_override, "q": q_override, "nivel": a.nivel, "trilhas": sorted(trilhas), "hoje": a.hoje}
    fp = fingerprint(docs, extra)
    state = load_json(out / "state.json", {})
    superseded = []
    if state.get("fingerprint") and state["fingerprint"] != fp:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        for f in ("avaliacao_trilha_a.md", "avaliacao_trilha_b.md"):
            if (out / f).exists():
                dest = out / "superseded" / stamp
                dest.mkdir(parents=True, exist_ok=True)
                shutil.move(str(out / f), dest / f)
                superseded.append(f"superseded/{stamp}/{f}")

    hist = historico(out)
    anteriores = [h for h in hist if h.get("fingerprint") != fp]
    rodada = len({h.get("fingerprint") for h in anteriores}) + 1
    max_rodadas = a.max_rodadas
    ciclo_encerrado = rodada > max_rodadas
    anterior = anteriores[-1] if anteriores else None
    if ciclo_encerrado and "B" in trilhas:
        trilhas.discard("B")
    triagem = {"nivel": nivel, "nivel_fonte": nivel_fonte, "respostas": tri, "inventario": inv, "info": info,
               "rodada": rodada, "max_rodadas": max_rodadas, "ciclo_encerrado": ciclo_encerrado}
    write(out / "triagem.json", json.dumps(triagem, ensure_ascii=False, indent=2))
    write(out / "sinais.json", json.dumps(sinais, ensure_ascii=False, indent=2))
    write(out / "extracao.json", json.dumps({"documentos": [{k: v for k, v in d.items() if k != "text"} for d in docs],
                                             "falhas": failures, "integridade": integrity}, ensure_ascii=False, indent=2))
    write(out / "triagem.md", "# Triagem\n\n" + triage_md(tri) + "\n\n# Documentos\n\n" + inventory_md(inv) + "\n\n# Sinais automáticos\n\n" + sinais_md(sinais) + "\n")

    tasks = []
    tasks_dir = out / ".tasks"
    tasks_dir.mkdir(exist_ok=True)
    alertas = alerts + [f"`{x['arquivo']}`: {x.get('suspicious_prompt_injection_count', 0)} padrão(ões) suspeito(s); texto oculto: {len(x.get('texto_oculto', []))}" for x in integrity]
    alertas += [f"`{x['arquivo']}`: não foi possível ler ({x['erro']})" for x in failures]
    titulo = info.get("titulo_projeto") or "não identificado"
    if "A" in trilhas:
        prompt = render((SKILL_DIR / "prompts" / "trilha_a.md").read_text(encoding="utf-8"), {
            "tom": TOM_A[nivel], "nivel": NIVEL_LABEL[nivel], "nivel_fonte": nivel_fonte, "titulo": titulo,
            "triagem_md": triage_md(tri), "inventario_md": inventory_md(inv), "sinais_md": sinais_md(sinais),
            "alertas_md": "\n".join(f"- {x}" for x in alertas) or "Nenhum.",
            "kb_md": kb_for_track_a({d["tipo"] for d in docs}, tri), "docs_md": docs_block(docs),
            "rodada_md": rodada_md("A", rodada, max_rodadas, anterior),
        })
        write(tasks_dir / "trilha_a.md", prompt)
        tasks.append({"id": "trilha_a", "kind": "trilha_a", "prompt_file": str((tasks_dir / "trilha_a.md").resolve()),
                      "output_file": str((out / "avaliacao_trilha_a.md").resolve())})
    if "B" in trilhas and projeto:
        prompt = render((SKILL_DIR / "prompts" / "trilha_b.md").read_text(encoding="utf-8"), {
            "fronteira": FRONTEIRA_B, "nivel": NIVEL_LABEL[nivel], "nivel_fonte": nivel_fonte, "tom": TOM_B[nivel],
            "campos": CAMPOS_B[nivel], "kb_md": kb_for_track_b(), "docs_md": docs_block(docs, ("projeto", "instrumento")),
            "rodada_md": rodada_md("B", rodada, max_rodadas, anterior), "limite_b": str(LIMITE_ESSENCIAL[nivel] + LIMITE_APROFUNDAR),
        })
        write(tasks_dir / "trilha_b.md", prompt)
        tasks.append({"id": "trilha_b", "kind": "trilha_b", "prompt_file": str((tasks_dir / "trilha_b.md").resolve()),
                      "output_file": str((out / "avaliacao_trilha_b.md").resolve())})
    write(tasks_dir / "manifest.json", json.dumps({"tasks": tasks}, ensure_ascii=False, indent=2))
    write(out / "state.json", json.dumps({"fingerprint": fp, "version": VERSION, "trilhas": sorted(trilhas), "rodada": rodada,
                                          "max_rodadas": max_rodadas, "ciclo_encerrado": ciclo_encerrado,
                                          "anterior": anterior.get("fingerprint") if anterior else None,
                                          "prepared_at": datetime.now().isoformat(timespec="seconds")}, indent=2))

    confirm = {
        "tipos_incertos": [{"arquivo": d["arquivo"], "tipo": d["tipo"], "confianca": d["confianca"]} for d in docs if d["confianca"] == "baixa" or d["tipo"] == "outro"],
        "nivel": None if tri["Q21"].get("valor") and tri["Q21"]["confianca"] in ("alta", "informado") else nivel_fonte,
        "triagem_sem_evidencia": [q for q in ("Q2", "Q3", "Q4", "Q6", "Q7", "Q8") if tri[q]["valor"] is None and tri[q]["confianca"] != "informado"],
    }
    summary = {
        "output_dir": str(out), "documentos": [{"arquivo": d["arquivo"], "tipo": d["tipo"], "confianca": d["confianca"], "palavras": d["words"]} for d in docs],
        "nivel": nivel, "nivel_fonte": nivel_fonte, "faltantes": [i["rotulo"] for i in inv if i["obrigatorio"] and not i["presente"]],
        "sinais": len(sinais), "confirmar": confirm, "integridade": integrity, "falhas": failures,
        "tarefas_pendentes": len(pending(out)), "manifest": str(tasks_dir / "manifest.json"), "superseded": superseded,
        "rodada": rodada, "max_rodadas": max_rodadas, "ciclo_encerrado": ciclo_encerrado,
    }
    if ciclo_encerrado:
        summary["aviso_ciclo"] = (f"Esta é a rodada {rodada}, acima do limite de {max_rodadas}: só a Trilha A roda, em modo de verificação "
                                  "dos itens já apontados. Recomende ao pesquisador concluir com o orientador e submeter.")
    if "B" in trilhas and not projeto:
        summary["aviso"] = "Sem projeto detalhado: a Trilha B não foi preparada."
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


# ----------------------------------------------------------------------------- next / run

def _manifest(out: Path) -> dict:
    return load_json(out / ".tasks" / "manifest.json", {"tasks": []})


def _done(t: dict) -> bool:
    p = Path(t["output_file"])
    return p.exists() and parse_findings(p.read_text(encoding="utf-8")) is not None


def pending(out: Path) -> list[dict]:
    """Tarefas sem saída válida que ainda têm tentativas (as que esgotaram ficam como 'falhou')."""
    return [t for t in _manifest(out)["tasks"] if not _done(t) and t.get("status") != "falhou"]


def register_attempt(out: Path, ids: list[str]) -> list[str]:
    """Conta uma tentativa para cada tarefa ainda pendente; marca 'falhou' ao atingir MAX_TENTATIVAS."""
    man = _manifest(out)
    failed = []
    for t in man["tasks"]:
        if t["id"] in ids and not _done(t):
            t["tentativas"] = t.get("tentativas", 0) + 1
            if t["tentativas"] >= MAX_TENTATIVAS:
                t["status"] = "falhou"
                failed.append(t["id"])
    write(out / ".tasks" / "manifest.json", json.dumps(man, ensure_ascii=False, indent=2))
    return failed


def cmd_next(a: argparse.Namespace) -> int:
    out = Path(a.output_dir)
    failed = register_attempt(out, [t["id"] for t in pending(out)])
    pend = pending(out)
    invalid = [t["id"] for t in pend if Path(t["output_file"]).exists()]
    res = {"tarefas_pendentes": len(pend), "pendentes": pend, "saidas_invalidas": invalid,
           "falharam": [t["id"] for t in _manifest(out)["tasks"] if t.get("status") == "falhou"]}
    if failed:
        res["aviso"] = (f"Tarefa(s) {', '.join(failed)} sem saída válida após {MAX_TENTATIVAS} tentativas: não tente de novo; "
                        "rode `compile` (a trilha aparecerá como não avaliada) e relate a falha.")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


def cmd_run(a: argparse.Namespace) -> int:
    import runners

    out = Path(a.output_dir)
    pend = pending(out)
    if a.limit:
        pend = pend[: a.limit]
    if not pend:
        print("Nenhuma tarefa pendente.")
        return 0
    runner = runners.detect_runner(a.runner)
    res = runners.run_tasks(pend, runner=runner, model=a.model, effort=a.effort, parallel=a.parallel, timeout=a.timeout, retries=1,
                            log=lambda s: print(s, file=sys.stderr))
    register_attempt(out, [t["id"] for t in pending(out)])
    register_attempt(out, [t["id"] for t in pending(out)])  # run já fez 2 tentativas por tarefa (retries=1)
    left = pending(out)
    print(json.dumps({"executadas": [{"id": r["id"], "status": r["status"]} for r in res], "tarefas_pendentes": len(left)}, ensure_ascii=False, indent=2))
    return 3 if left else 0


# ----------------------------------------------------------------------------- compile

def _sev_key(f: dict) -> tuple:
    return (kb.SEV_ORDEM.get(f.get("severidade") or "", 9), f.get("id") or "ZZZ")


def _key(f: dict) -> tuple[str, str]:
    return (f.get("id") or "", cl.norm(Path(str(f.get("documento") or "")).name))


def compile_track_a(data: dict | None, sinais: list[dict], anterior: dict | None = None) -> dict:
    reqs, disc = kb.load_requirements(), kb.load_discrepancies()
    achados, avisos, sem_id = [], [], []
    confirmed: set[str] = set()
    discarded: dict[str, str] = {}
    if data:
        for d in data.get("sinais_descartados", []) or []:
            discarded[str(d.get("ref"))] = d.get("motivo", "")
        for f in data.get("achados", []) or []:
            rid = (f.get("id") or "").strip() or None
            confirmed.update(f.get("auto_refs") or [])
            if rid and rid in reqs:
                it = reqs[rid]
                achados.append({**f, "id": rid, "severidade": it.severidade or "PENDÊNCIA", "requisito": it.texto, "arquivo_base": it.arquivo,
                                "severidade_inferida": it.severidade_inferida})
            elif rid and rid in disc:
                avisos.append({**f, "id": rid, "requisito": disc[rid].texto})
            else:
                sem_id.append({**f, "id_informado": rid})
    nao_verificados = [s for s in sinais if s["ref"] not in confirmed and s["ref"] not in discarded]
    if data is None:
        nao_verificados = list(sinais)
    achados.sort(key=_sev_key)
    descartados_limite = 0
    if anterior:  # rodada de verificação: recomendações novas não entram
        prev_ids = {f.get("id") for f in (anterior.get("trilha_a") or {}).get("achados", [])}
        keep = [f for f in achados if not (f["severidade"] == "RECOMENDAÇÃO" and f["id"] not in prev_ids)]
        descartados_limite += len(achados) - len(keep)
        achados = keep
    recs = [f for f in achados if f["severidade"] == "RECOMENDAÇÃO"]
    if len(recs) > LIMITE_RECOMENDACOES:
        drop = {id(f) for f in recs[LIMITE_RECOMENDACOES:]}
        descartados_limite += len(drop)
        achados = [f for f in achados if id(f) not in drop]
    return {"achados": achados, "avisos": avisos, "sem_id": sem_id, "sinais_nao_verificados": nao_verificados,
            "omitidos_por_limite": descartados_limite,
            "sinais_descartados": [{"ref": k, "motivo": v} for k, v in discarded.items()],
            "pontos_fortes": (data or {}).get("pontos_fortes", []), "integridade": (data or {}).get("integridade", [])}


def compile_track_b(data: dict | None, nivel: str, anterior: dict | None = None) -> dict:
    sugs = kb.load_suggestions()
    prev_ids: set | None = None
    if anterior and anterior.get("trilha_b"):
        tbp = anterior["trilha_b"]
        prev_ids = {s.get("id") for s in tbp.get("essencial", []) + tbp.get("aprofundar", [])}
    omitidas = 0
    essencial, aprofundar, alertas = [], [], []
    nv = kb.NIVEL_ORDEM.get(nivel, 0)
    for s in (data or {}).get("sugestoes", []) or []:
        sid = (s.get("id") or "").strip() or None
        it = sugs.get(sid) if sid else None
        s = {**s, "id": sid if it else None, "id_informado": sid if sid and not it else None}
        if it:
            s["item"] = it.texto
            s["nucleo_comum"] = bool(it.nucleo_comum)
            s["nivel_minimo"] = it.nivel_minimo
            if not s.get("para_estudar"):
                s["para_estudar"] = it.fonte
            is_ess = bool(it.nucleo_comum) or (it.nivel_minimo is not None and nv >= kb.NIVEL_ORDEM[it.nivel_minimo])
        else:
            is_ess = int(s.get("impacto") or 1) >= 3
        if prev_ids is not None and s.get("id") not in prev_ids and not s.get("nucleo_comum"):
            omitidas += 1  # rodada de verificação: sem sugestões novas fora do núcleo comum
            continue
        blob = " ".join(str(v) for v in s.values() if isinstance(v, str))
        if CEP_LANGUAGE.search(blob):
            alertas.append(f"Sugestão {sid or '(sem ID)'} usa linguagem de exigência do CEP: revise a redação.")
        (essencial if is_ess else aprofundar).append(s)

    def key(x: dict) -> tuple:
        return (-int(x.get("impacto") or 1), 0 if x.get("nucleo_comum") else 1, x.get("id") or "ZZZ")

    essencial.sort(key=key)
    aprofundar.sort(key=key)
    cortadas = 0
    lim = LIMITE_ESSENCIAL.get(nivel, 8)
    if len(essencial) > lim:
        extra = essencial[lim:]
        essencial = essencial[:lim]
        for x in extra:
            x["movida_do_essencial"] = True
        aprofundar = extra + aprofundar
        cortadas = len(extra)
    if len(aprofundar) > LIMITE_APROFUNDAR:
        omitidas += len(aprofundar) - LIMITE_APROFUNDAR
        aprofundar = aprofundar[:LIMITE_APROFUNDAR]
    return {"pontos_fortes": (data or {}).get("pontos_fortes", []), "essencial": essencial, "aprofundar": aprofundar,
            "cortadas_do_essencial": cortadas, "omitidas_por_limite": omitidas, "resumo_orientador": (data or {}).get("resumo_orientador", "") if nivel != "docente" else "",
            "encaminhar_trilha_a": (data or {}).get("encaminhar_trilha_a", []) or [], "alertas_redacao": alertas,
            "integridade": (data or {}).get("integridade", [])}


def cmd_compile(a: argparse.Namespace) -> int:
    out = Path(a.output_dir)
    tri = load_json(out / "triagem.json")
    if tri is None:
        raise SystemExit("triagem.json não encontrado: rode `prepare` primeiro.")
    sinais = load_json(out / "sinais.json", [])
    extr = load_json(out / "extracao.json", {})
    state = load_json(out / "state.json", {})
    pend = pending(out)
    falhas_tarefa = [t["id"] for t in _manifest(out)["tasks"] if t.get("status") == "falhou"]
    if pend and not a.parcial:
        print(json.dumps({"erro": "tarefas pendentes; avalie-as ou use --parcial", "pendentes": [t["id"] for t in pend]}, ensure_ascii=False, indent=2))
        return 3
    da = parse_findings((out / "avaliacao_trilha_a.md").read_text(encoding="utf-8")) if (out / "avaliacao_trilha_a.md").exists() else None
    dbb = parse_findings((out / "avaliacao_trilha_b.md").read_text(encoding="utf-8")) if (out / "avaliacao_trilha_b.md").exists() else None
    nivel = tri["nivel"]
    fp = state.get("fingerprint")
    anterior = next((h for h in reversed(historico(out)) if h.get("fingerprint") != fp), None)
    rodada = state.get("rodada", 1)
    ta = compile_track_a(da, sinais, anterior if rodada > 1 else None)
    tb = compile_track_b(dbb, nivel, anterior if rodada > 1 else None) if "B" in state.get("trilhas", ["A", "B"]) else None
    g05 = kb.get("PROJ-G05")
    if tb:
        for e in tb["encaminhar_trilha_a"]:
            ta["achados"].append({"id": "PROJ-G05", "severidade": g05.severidade if g05 else "PENDÊNCIA", "requisito": g05.texto if g05 else "",
                                  "documento": "projeto", "onde": "", "trecho": e.get("trecho", ""), "problema": e.get("descricao", ""),
                                  "por_que": e.get("risco_etico", ""), "sugestao": "Rever o ponto metodológico que gera o risco ético.",
                                  "origem": "Trilha B (metodologia com viés ético)"})
        ta["achados"].sort(key=_sev_key)
    counts = {s: sum(1 for f in ta["achados"] if f["severidade"] == s) for s in kb.SEVERIDADES}
    data = {
        "versao": VERSION, "gerado_em": datetime.now().isoformat(timespec="seconds"), "nivel": nivel, "nivel_fonte": tri["nivel_fonte"],
        "titulo": tri.get("info", {}).get("titulo_projeto"), "triagem": tri["respostas"], "inventario": tri["inventario"],
        "documentos": extr.get("documentos", []), "falhas": extr.get("falhas", []),
        "integridade": extr.get("integridade", []) + ta["integridade"] + (tb["integridade"] if tb else []),
        "trilha_a": ta, "trilha_b": tb, "contagem": counts, "trilha_a_avaliada": da is not None, "trilha_b_avaliada": dbb is not None,
        "aviso_ia": not a.sem_aviso_ia, "fingerprint": fp, "rodada": rodada, "max_rodadas": state.get("max_rodadas", MAX_RODADAS),
        "ciclo_encerrado": state.get("ciclo_encerrado", False), "tarefas_falharam": falhas_tarefa,
        "info": tri.get("info", {}), "progresso": progresso(anterior, ta, tb) if anterior and rodada > 1 else None,
    }
    md = report.build_report(data)
    write(out / "relatorio.md", md)
    write(out / "resumo.json", json.dumps(data, ensure_ascii=False, indent=2, default=str))
    if fp:
        write(out / "historico" / f"{fp}.json", json.dumps(data, ensure_ascii=False, indent=2, default=str))
    pdf = report.md_to_pdf(md, out / "relatorio.pdf")
    md_o = report.build_supervisor_report(data)
    write(out / "relatorio_orientador.md", md_o)
    report.md_to_pdf(md_o, out / "relatorio_orientador.pdf")
    print(json.dumps({
        "relatorio": str(out / "relatorio.md"), "pdf": str(pdf) if pdf else None, "resumo": str(out / "resumo.json"),
        "relatorio_orientador": str(out / "relatorio_orientador.md"), "rodada": rodada, "progresso": data["progresso"],
        "tarefas_falharam": falhas_tarefa,
        "contagem_trilha_a": counts, "avisos": len(ta["avisos"]), "sem_id": len(ta["sem_id"]),
        "sinais_nao_verificados": len(ta["sinais_nao_verificados"]),
        "trilha_b": {"essencial": len(tb["essencial"]), "aprofundar": len(tb["aprofundar"]), "alertas_redacao": tb["alertas_redacao"]} if tb else None,
        "integridade": len(data["integridade"]),
    }, ensure_ascii=False, indent=2))
    return 0


def progresso(anterior: dict, ta: dict, tb: dict | None) -> dict:
    """Compara com a rodada anterior pelo par (ID, documento)."""
    prev = {_key(f): f for f in (anterior.get("trilha_a") or {}).get("achados", [])}
    cur = {_key(f): f for f in ta["achados"]}
    res = {
        "resolvidos": [{"id": f["id"], "documento": f.get("documento"), "problema": f.get("problema")} for k, f in prev.items() if k not in cur],
        "persistem": [{"id": f["id"], "documento": f.get("documento"), "problema": f.get("problema")} for k, f in cur.items() if k in prev],
        "novos": [{"id": f["id"], "documento": f.get("documento"), "problema": f.get("problema"), "severidade": f["severidade"]} for k, f in cur.items() if k not in prev],
        "rodada_anterior": anterior.get("rodada", 1),
    }
    if tb is not None and anterior.get("trilha_b"):
        pb = anterior["trilha_b"]
        p_ids = {s.get("id") for s in pb.get("essencial", []) + pb.get("aprofundar", []) if s.get("id")}
        c_ids = {s.get("id") for s in tb["essencial"] + tb["aprofundar"] if s.get("id")}
        res["sugestoes_atendidas"] = sorted(p_ids - c_ids)
    return res


def cmd_planejar(a: argparse.Namespace) -> int:
    """Sem documentos: triagem por respostas do usuário → documentos, assinaturas, prazos (planejamento.md)."""
    out = Path(a.output_dir)
    q = parse_kv(a.q, "--q")
    tri: dict[str, dict] = {}
    for key, (label, _) in cl.TRIAGE.items():
        tri[key] = {"pergunta": label, "valor": None}
    tri["Q1"] = {"pergunta": "Participantes adultos e capazes", "valor": None}
    for k, v in q.items():
        k = k.upper()
        if k not in tri:
            raise SystemExit(f"--q {k}: pergunta desconhecida")
        tri[k]["valor"] = v.lower() in ("sim", "s", "true", "1")
    if tri["Q1"]["valor"] is None and not tri["Q2"]["valor"]:
        tri["Q1"]["valor"] = True
    nivel = a.nivel or "graduacao"
    exp = cl.expected_documents(tri)
    coleta = date.fromisoformat(a.coleta) if a.coleta else None
    md = report.build_plan(tri, exp, nivel, coleta, NIVEL_LABEL)
    write(out / "planejamento.md", md)
    report.md_to_pdf(md, out / "planejamento.pdf")
    print(json.dumps({"planejamento": str(out / "planejamento.md"), "documentos": [cl.DOC_LABELS[e["tipo"]] for e in exp if e["obrigatorio"]]},
                     ensure_ascii=False, indent=2))
    return 0


# ----------------------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=VERSION)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare", help="extrai, classifica, faz a triagem e escreve as tarefas")
    p.add_argument("--input", nargs="+", required=True, help="pasta do protocolo ou arquivos")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--nivel", choices=kb.NIVEIS, help="nível do trabalho (substitui a detecção)")
    p.add_argument("--trilhas", default="A,B", help="A, B ou A,B (padrão)")
    p.add_argument("--tipo", action="append", help="ARQUIVO=TIPO para corrigir a classificação (repetível)")
    p.add_argument("--q", action="append", help="QN=sim|nao para corrigir a triagem (repetível)")
    p.add_argument("--hoje", help="data de referência AAAA-MM-DD (testes)")
    p.add_argument("--max-rodadas", type=int, default=MAX_RODADAS, help=f"rodadas de revisão por protocolo (padrão {MAX_RODADAS})")
    pl = sub.add_parser("planejar", help="sem documentos: documentos necessários, assinaturas e prazos a partir da triagem")
    pl.add_argument("--output-dir", required=True)
    pl.add_argument("--q", action="append", help="QN=sim|nao (repetível)")
    pl.add_argument("--nivel", choices=kb.NIVEIS)
    pl.add_argument("--coleta", help="data desejada para iniciar a coleta, AAAA-MM-DD")
    n = sub.add_parser("next", help="lista as tarefas pendentes")
    n.add_argument("--output-dir", required=True)
    r = sub.add_parser("run", help="executa as tarefas pendentes em modo headless")
    r.add_argument("--output-dir", required=True)
    r.add_argument("--runner", default="auto", choices=["auto", "claude", "agy", "gemini"])
    r.add_argument("--model")
    r.add_argument("--effort")
    r.add_argument("--parallel", type=int, default=2)
    r.add_argument("--timeout", type=float, default=900)
    r.add_argument("--limit", type=int)
    c = sub.add_parser("compile", help="gera o relatório")
    c.add_argument("--output-dir", required=True)
    c.add_argument("--parcial", action="store_true", help="compila mesmo com tarefas pendentes")
    c.add_argument("--sem-aviso-ia", action="store_true", help="omite o aviso de assistência por IA (só a pedido do usuário)")
    a = ap.parse_args(argv)
    return {"prepare": cmd_prepare, "next": cmd_next, "run": cmd_run, "compile": cmd_compile, "planejar": cmd_planejar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
