"""Relatório de pré-submissão (Markdown e PDF) em duas partes separadas: Trilha A (CEP) e Trilha B (sugestões)."""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

NIVEL_LABEL = {
    "graduacao": "graduação (IC/TCC)",
    "especializacao": "especialização ou residência",
    "mestrado": "mestrado",
    "doutorado": "doutorado",
    "docente": "pesquisa docente",
}

AVISO_IA = (
    "> **Rascunho gerado com assistência de IA** pelo tutor de pré-submissão. Não é parecer do CEP-UMC nem previsão de "
    "aprovação. Confira cada apontamento com o orientador e, em caso de dúvida, consulte o CEP-UMC "
    "(cep@umc.br, (11) 4798-7085)."
)

PROXIMOS_PASSOS = """\
1. Corrija primeiro os itens **[BLOQUEANTE]**, depois as **[PENDÊNCIA]**.
2. Depois de cada correção, atualize **todos** os documentos e o formulário da Plataforma Brasil: título, equipe, locais,
   amostra, cronograma e orçamento devem ser idênticos em tudo (GER-01 a GER-06).
3. Remova os textos de instrução dos modelos e confira os nomes dos arquivos (sem acentos, espaços ou caracteres
   especiais).
4. Rode o tutor de novo sobre a versão corrigida.
5. **Prazos** (Regimento do CEP-UMC e NO 001/2013): checagem documental em até 10 dias; parecer em até 30 dias após a
   aceitação dos documentos; o CEP se reúne uma vez por mês. Preveja no cronograma a aprovação de 40 a 50 dias após o
   envio e a coleta depois dela (PROJ-C13). Se houver pendência, o pesquisador tem 30 dias para responder."""


LINK_MODELOS = "https://www.umc.br/comite-de-etica-cep/"
LIMITE_CONFERIR = 10

LEGENDA = """\
| Rótulo | O que significa | O que fazer |
|---|---|---|
| **[BLOQUEANTE]** | Documento essencial faltando ou problema que o CEP costuma tratar como motivo de recusa ou não aprovação | Corrigir antes de submeter |
| **[PENDÊNCIA]** | Problema que costuma gerar parecer pendente (atrasa a aprovação em semanas) | Corrigir antes de submeter |
| **[RECOMENDAÇÃO]** | Boa prática indicada pelo CEP | Corrigir se possível |
| **[SUGESTÃO]** | Melhoria acadêmica (Parte 2), **não cobrada pelo CEP** | Decidir com o orientador |

A classificação é do tutor, tirada da redação dos documentos do CEP-UMC; não é um critério oficial do comitê."""

ASSINATURAS = [
    ("Folha de rosto", "pesquisador responsável; responsável pela instituição proponente; patrocinador, se for \"Institucional Principal\"", "PB-D01"),
    ("TCLE / TCLE do responsável / TALE", "participante (ou responsável) e pesquisador, com rubrica em todas as páginas", "TCLE-F10"),
    ("TAI (um por local)", "responsável pelo local, em papel timbrado e com carimbo; **não** pode ser o pesquisador, o orientador ou um assistente", "TAI-09"),
    ("Carta de anuência (assistência)", "responsável pelo serviço que prestará a assistência, que não pode ser da equipe", "ANU-10"),
]


def _q(s: str | None) -> str:
    s = " ".join((s or "").split())
    return f"“{s}”" if s else ""


def _br(iso: str | None) -> str:
    return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}" if iso else ""


def prazo_submissao(coleta_iso: str | None, hoje: date | None = None) -> list[str]:
    """Datas-limite de envio a partir do início da coleta (arquivo 12 da base: 40–50 dias; +60 com uma pendência)."""
    if not coleta_iso:
        return []
    hoje = hoje or date.today()
    c = date.fromisoformat(coleta_iso)
    ideal, folga = c - timedelta(days=50), c - timedelta(days=110)
    txt = (f"Coleta prevista para **{c:%d/%m/%Y}**. Para chegar aprovado a essa data, submeta até **{ideal:%d/%m/%Y}** "
           f"(cerca de 50 dias antes) ou, com margem para uma rodada de pendência (30 dias para responder e 30 para o novo "
           f"parecer), até **{folga:%d/%m/%Y}**. A coleta só pode começar depois da aprovação (PROJ-C13).")
    if ideal < hoje:
        txt += (f"\n\n⚠️ **A data de {ideal:%d/%m/%Y} já passou:** mesmo sem pendências, a aprovação dificilmente sai antes de "
                f"{hoje + timedelta(days=50):%d/%m/%Y}. Ajuste o cronograma do projeto e da Plataforma.")
    elif folga < hoje:
        txt += "\n\n⚠️ **A margem para uma pendência já passou:** submeta o quanto antes ou adie a coleta no cronograma."
    return [txt]


def _finding_a(f: dict) -> list[str]:
    head = f"**[{f['severidade']}] {f.get('problema') or f.get('requisito', '')}** · `{f['id']}`"
    lines = [head]
    onde = ", ".join(x for x in (f.get("documento"), f.get("onde")) if x)
    if onde or f.get("trecho"):
        lines.append(f"- **Onde:** {onde}{' — ' if onde and f.get('trecho') else ''}{_q(f.get('trecho'))}")
    if f.get("por_que"):
        lines.append(f"- **Por quê:** {f['por_que']}")
    if f.get("sugestao"):
        lines.append(f"- **Como corrigir:** {f['sugestao']}")
    if f.get("requisito"):
        lines.append(f"- *Requisito {f['id']} ({f.get('arquivo_base', 'base')}): {f['requisito']}*")
    if f.get("origem"):
        lines.append(f"- *Origem: {f['origem']}.*")
    return lines


def _finding_b(s: dict, bloco: str) -> list[str]:
    sid = s.get("id") or "sem item na base"
    lines = [f"**[SUGESTÃO · {bloco}] {s.get('sugestao') or s.get('item', '')}** · `{sid}`"]
    onde = ", ".join(x for x in (s.get("onde"),) if x)
    if onde or s.get("trecho"):
        lines.append(f"- **Onde:** {onde}{' — ' if onde and s.get('trecho') else ''}{_q(s.get('trecho'))}")
    for k, label in (("por_que", "Por que importa"), ("reflexao", "Para refletir"), ("como_melhorar", "Como melhorar"), ("para_estudar", "Para estudar")):
        if s.get(k):
            lines.append(f"- **{label}:** {s[k]}")
    if s.get("movida_do_essencial"):
        lines.append("- *Movida para cá para manter o bloco Essencial curto; também é importante.*")
    return lines


def plano_de_acao(d: dict, n: int = 5) -> list[str]:
    acoes: list[str] = []
    for i in d["inventario"]:
        if i["obrigatorio"] and not i["presente"]:
            acoes.append(f"Providenciar: **{i['rotulo']}**. Motivo: {i['motivo']}. Modelos: {LINK_MODELOS}")
    for sev in ("BLOQUEANTE", "PENDÊNCIA"):
        for f in d["trilha_a"]["achados"]:
            if f["severidade"] == sev:
                acoes.append(f"[{sev}] {f.get('problema') or f['id']}: {f.get('sugestao') or 'ver Parte 1'}")
    total = len(acoes)
    out = [f"{k}. {a}" for k, a in enumerate(acoes[:n], 1)]
    if total > n:
        out.append(f"\n*Mais {total - n} item(ns) na Parte 1.*")
    return out


def _progresso_md(p: dict) -> list[str]:
    L = ["## Desde a rodada anterior", ""]
    L.append(f"- **Resolvidos:** {len(p['resolvidos'])}" + (": " + "; ".join(f"`{x['id']}`" for x in p["resolvidos"][:10]) if p["resolvidos"] else ""))
    L.append(f"- **Ainda pendentes:** {len(p['persistem'])}" + (": " + "; ".join(f"`{x['id']}`" for x in p["persistem"][:10]) if p["persistem"] else ""))
    if p["novos"]:
        L.append(f"- **Novos** (introduzidos pela correção ou não vistos antes): {len(p['novos'])}: " + "; ".join(f"`{x['id']}`" for x in p["novos"][:10]))
    if p.get("sugestoes_atendidas"):
        L.append(f"- **Sugestões acadêmicas atendidas:** {', '.join(p['sugestoes_atendidas'])}")
    return L + [""]


def build_report(d: dict) -> str:
    ta, tb = d["trilha_a"], d["trilha_b"]
    nivel = NIVEL_LABEL.get(d["nivel"], d["nivel"])
    rodada, maxr = d.get("rodada", 1), d.get("max_rodadas", 3)
    L: list[str] = ["# Relatório de pré-submissão ao CEP-UMC", ""]
    if d.get("aviso_ia", True):
        L += [AVISO_IA, ""]
    L += [
        f"- **Projeto:** {d.get('titulo') or 'título não identificado'}",
        f"- **Nível do trabalho:** {nivel} ({d['nivel_fonte']})",
        f"- **Rodada de revisão:** {rodada} de {maxr}",
        f"- **Gerado em:** {d['gerado_em'][:10]}",
    ]
    if d["nivel"] == "graduacao":
        L.append("- **Quem submete:** em trabalho de graduação, o **orientador** é o pesquisador responsável e submete na Plataforma "
                 "Brasil; o aluno entra como assistente (PB-U03).")
    L += [""]
    if d.get("ciclo_encerrado"):
        L += ["> **Ciclo de revisão encerrado.** Esta rodada só verificou os pontos éticos já apontados. Resolva o que falta com o "
              "orientador e submeta: novas rodadas do tutor não trazem ganho proporcional ao tempo.", ""]
    L += ["## Resumo", ""]
    c = d["contagem"]
    if d["trilha_a_avaliada"]:
        L.append(f"- **Parte 1 (CEP):** {c['BLOQUEANTE']} bloqueante(s), {c['PENDÊNCIA']} pendência(s), {c['RECOMENDAÇÃO']} recomendação(ões).")
    else:
        L.append("- **Parte 1 (CEP):** não avaliada; só os pontos detectados automaticamente estão listados.")
    falt = [i["rotulo"] for i in d["inventario"] if i["obrigatorio"] and not i["presente"]]
    if falt:
        L.append(f"- **Documentos obrigatórios não recebidos:** {', '.join(falt)}.")
    if tb is not None:
        if d["trilha_b_avaliada"]:
            L.append(f"- **Parte 2 (sugestões acadêmicas):** {len(tb['essencial'])} essencial(is), {len(tb['aprofundar'])} para aprofundar.")
        else:
            L.append("- **Parte 2 (sugestões acadêmicas):** não avaliada.")
    elif d.get("ciclo_encerrado"):
        L.append("- **Parte 2:** não refeita nesta rodada (ciclo encerrado).")
    for t in d.get("tarefas_falharam", []):
        L.append(f"- **Atenção:** a revisão `{t}` falhou duas vezes e não entrou no relatório.")
    if d["integridade"]:
        L.append("- ⚠️ **Integridade:** há texto oculto ou instruções dirigidas a ferramentas de IA nos documentos. Veja o fim do relatório.")
    if d["falhas"]:
        L.append(f"- **Arquivos não lidos:** {', '.join(f['arquivo'] for f in d['falhas'])}.")
    L.append("")
    acoes = plano_de_acao(d)
    if acoes:
        L += ["## Comece por aqui", ""] + acoes + [""]
    if d.get("progresso"):
        L += _progresso_md(d["progresso"])
    prazo = prazo_submissao((d.get("info") or {}).get("coleta_inicio"), date.fromisoformat(d["gerado_em"][:10]))
    if prazo:
        L += ["## Prazo para submeter", ""] + prazo + [""]
    L += ["## Como ler este relatório", "", LEGENDA, ""]
    L += ["## Documentos do protocolo", "", "| Documento | Obrigatório | Motivo | Recebido |", "|---|---|---|---|"]
    for i in d["inventario"]:
        rec = ", ".join(f"`{a}`" for a in i["arquivos"]) if i["arquivos"] else ("só dentro do projeto" if i.get("no_projeto") else "**não**")
        L.append(f"| {i['rotulo']} | {'sim' if i['obrigatorio'] else 'se aplicável'} | {i['motivo']} | {rec} |")
    L += ["", f"Modelos oficiais do CEP-UMC: {LINK_MODELOS}"]
    esperados = {i["tipo"] for i in d["inventario"]}
    outros = [x for x in d["documentos"] if x["tipo"] not in esperados]
    if outros:
        L += ["", "Outros documentos recebidos: " + ", ".join(f"`{x['arquivo']}` ({x['tipo']})" for x in outros) + "."]

    # ---------------------------------------------------------------- Parte 1
    L += ["", "## Parte 1 — Pontos éticos e documentais (avaliados pelo CEP)", ""]
    if ta["pontos_fortes"]:
        L += ["### Pontos fortes", ""] + [f"- {p}" for p in ta["pontos_fortes"]] + [""]
    for sev in ("BLOQUEANTE", "PENDÊNCIA", "RECOMENDAÇÃO"):
        fs = [f for f in ta["achados"] if f["severidade"] == sev]
        if not fs:
            continue
        L += [f"### {sev.capitalize()}", ""]
        for f in fs:
            L += _finding_a(f) + [""]
    if not ta["achados"] and d["trilha_a_avaliada"]:
        L += ["Nenhum problema identificado na Parte 1.", ""]
    if ta.get("omitidos_por_limite"):
        L += [f"*{ta['omitidos_por_limite']} recomendação(ões) de menor prioridade omitida(s) para manter o foco (lista completa em `resumo.json`).*", ""]
    if ta["avisos"]:
        L += ["### Avisos (divergências entre documentos do próprio CEP)", ""]
        for f in ta["avisos"]:
            L += [f"**{f.get('problema') or f['id']}** · `{f['id']}`", f"- {f.get('sugestao') or f.get('requisito', '')}", ""]
    if ta["sem_id"]:
        L += ["### Outros pontos (sem requisito correspondente na base)", "", "*Confira com o orientador ou com o CEP antes de alterar.*", ""]
        for f in ta["sem_id"]:
            L += [f"- {f.get('problema', '')} {_q(f.get('trecho'))} — {f.get('sugestao', '')}"]
        L.append("")
    nv = ta["sinais_nao_verificados"]
    if nv:
        L += ["### Pontos para conferir", "", "*Detectados automaticamente por padrão de texto e não confirmados pela revisão. Podem ser falsos alarmes: confira cada um.*", ""]
        for s in nv[:LIMITE_CONFERIR]:
            L.append(f"- {s['mensagem']} (`{s['arquivo']}`, `{s['id']}`) {_q(s['trecho'][:160])}")
        if len(nv) > LIMITE_CONFERIR:
            L.append(f"- *Mais {len(nv) - LIMITE_CONFERIR} ponto(s) em `triagem.md`.*")
        L.append("")
    L += ["### Próximos passos", "", PROXIMOS_PASSOS, ""]

    # ---------------------------------------------------------------- Parte 2
    if tb is not None:
        L += [
            "## Parte 2 — Sugestões acadêmicas (não são exigências do CEP)",
            "",
            "> Os itens abaixo **não serão cobrados pelo CEP**. São sugestões de metodologia, estatística e escrita para "
            "melhorar o trabalho; decida com seu orientador.",
            "",
        ]
        if c["BLOQUEANTE"]:
            L += ["*Resolva antes os itens bloqueantes da Parte 1: eles têm prioridade sobre estas sugestões.*", ""]
        if not d["trilha_b_avaliada"]:
            L += ["Parte 2 não avaliada.", ""]
        if tb["pontos_fortes"]:
            L += ["### Pontos fortes", ""] + [f"- {p}" for p in tb["pontos_fortes"]] + [""]
        if tb["essencial"]:
            L += ["### Essencial", ""]
            for s in tb["essencial"]:
                L += _finding_b(s, "Essencial") + [""]
        if tb["aprofundar"]:
            L += ["### Para aprofundar", "", "*Opcional: vai além do que se espera neste nível.*", ""]
            for s in tb["aprofundar"]:
                L += _finding_b(s, "Para aprofundar") + [""]
        if tb.get("omitidas_por_limite"):
            L += [f"*{tb['omitidas_por_limite']} sugestão(ões) omitida(s) para manter o foco.*", ""]
        if tb["resumo_orientador"]:
            L += ["### Resumo para o orientador", "", tb["resumo_orientador"].strip(), ""]

    # ---------------------------------------------------------------- integridade e método
    if d["integridade"]:
        L += ["## ⚠️ Integridade", "", "Os documentos contêm texto oculto ou instruções dirigidas a ferramentas de IA. Elas foram ignoradas na avaliação. "
              "Remova esse conteúdo antes de submeter.", ""]
        for x in d["integridade"]:
            if isinstance(x, dict):
                pats = "; ".join(p.get("matched_text", "") for p in x.get("suspicious_patterns", [])[:3])
                oc = "; ".join(x.get("texto_oculto", [])[:3])
                L.append(f"- `{x.get('arquivo', '?')}`: {pats or ''}{' | oculto: ' + oc if oc else ''}")
            else:
                L.append(f"- {x}")
        L.append("")
    L += [
        "## Como esta avaliação foi feita",
        "",
        "- **Parte 1** usa só a base de conhecimento do CEP-UMC (modelos de 2022, Regimento de 2025, Manual da Plataforma "
        "Brasil e Cartilha da CONEP). A severidade de cada item vem da base.",
        "- **Parte 2** usa a base acadêmica (diretrizes EQUATOR, normas ABNT e literatura metodológica), calibrada pelo nível do "
        "trabalho. \"Essencial\" e \"Para aprofundar\" seguem regra fixa (núcleo comum e nível mínimo de cada item).",
        f"- A revisão é **finita**: até {maxr} rodadas por protocolo; da segunda em diante, o tutor verifica o que já apontou e não "
        "abre frentes novas, salvo problema ético grave.",
        "",
    ]
    return "\n".join(L)


def build_supervisor_report(d: dict) -> str:
    """Uma página para o orientador (pesquisador responsável)."""
    tb = d["trilha_b"]
    c = d["contagem"]
    L = ["# Visão do orientador — pré-submissão ao CEP-UMC", ""]
    if d.get("aviso_ia", True):
        L += [AVISO_IA, ""]
    L += [f"- **Projeto:** {d.get('titulo') or 'título não identificado'}",
          f"- **Nível:** {NIVEL_LABEL.get(d['nivel'], d['nivel'])} · **Rodada:** {d.get('rodada', 1)} de {d.get('max_rodadas', 3)}",
          f"- **Parte 1 (CEP):** {c['BLOQUEANTE']} bloqueante(s), {c['PENDÊNCIA']} pendência(s), {c['RECOMENDAÇÃO']} recomendação(ões)", ""]
    pronto = c["BLOQUEANTE"] == 0 and c["PENDÊNCIA"] == 0 and not any(i["obrigatorio"] and not i["presente"] for i in d["inventario"])
    L += ["## Situação", "",
          "Sem bloqueantes, pendências ou documentos faltando: **pode seguir para a submissão** depois da sua leitura final."
          if pronto else "**Ainda não está pronto para submeter.** Itens a resolver:", ""]
    if not pronto:
        L += plano_de_acao(d, n=8) + [""]
    if d.get("progresso"):
        L += _progresso_md(d["progresso"])
    prazo = prazo_submissao((d.get("info") or {}).get("coleta_inicio"), date.fromisoformat(d["gerado_em"][:10]))
    if prazo:
        L += ["## Prazo", ""] + prazo + [""]
    L += ["## Assinaturas a providenciar", "", "| Documento | Quem assina | Ref. |", "|---|---|---|"]
    tipos = {i["tipo"] for i in d["inventario"]} | {x["tipo"] for x in d["documentos"]}
    for doc, quem, ref in ASSINATURAS:
        if doc.startswith("TAI") and "tai" not in tipos:
            continue
        if doc.startswith("Carta") and "anuencia_assistencia" not in tipos:
            continue
        L.append(f"| {doc} | {quem} | {ref} |")
    L.append("")
    if d["nivel"] == "graduacao":
        L += ["Em trabalho de graduação, **você** é o pesquisador responsável e submete na Plataforma Brasil (PB-U03).", ""]
    if tb is not None and (tb["essencial"] or tb["resumo_orientador"]):
        L += ["## Sugestões acadêmicas (não cobradas pelo CEP)", ""]
        if tb["resumo_orientador"]:
            L += [tb["resumo_orientador"].strip(), ""]
        L += [f"- {s.get('sugestao') or s.get('item', '')} (`{s.get('id') or '-'}`)" for s in tb["essencial"]] + [""]
    L += ["Relatório completo para o aluno: `relatorio.md`.", ""]
    return "\n".join(L)


def build_plan(tri: dict, exp: list[dict], nivel: str, coleta: date | None, niveis: dict) -> str:
    """Planejamento sem documentos: o que preparar, quem assina, prazos."""
    L = ["# Planejamento da submissão ao CEP-UMC", "", AVISO_IA, "",
         f"- **Nível do trabalho:** {niveis.get(nivel, nivel)}"]
    if nivel == "graduacao":
        L.append("- **Quem submete:** o orientador (pesquisador responsável); o aluno entra como assistente (PB-U03).")
    L += ["", "## Documentos a preparar", "", "| Documento | Obrigatório | Por quê | Ref. |", "|---|---|---|---|"]
    from classify import DOC_LABELS  # import tardio: report não depende de classify no uso normal

    for e in exp:
        L.append(f"| {DOC_LABELS[e['tipo']]} | {'sim' if e['obrigatorio'] else 'se aplicável'} | {e['motivo']} | {e['id']} |")
    L += ["", f"Baixe os modelos oficiais em {LINK_MODELOS} e mantenha a estrutura deles (inclusive o rodapé com página e rubrica).", ""]
    sem = [q for q, v in tri.items() if v.get("valor") is None and q in ("Q2", "Q3", "Q4", "Q6", "Q7", "Q8")]
    if sem:
        L += ["*Perguntas sem resposta (podem acrescentar documentos): " + ", ".join(f"{q} ({tri[q]['pergunta']})" for q in sem) + ".*", ""]
    L += ["## Quem assina", "", "| Documento | Quem assina | Ref. |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in ASSINATURAS]
    L += ["", "## Prazos", ""]
    if coleta:
        L += prazo_submissao(coleta.isoformat(), date.today())
    else:
        L.append("Informe a data desejada para começar a coleta para calcular a data-limite de submissão.")
    L += ["", "## Erros mais comuns a evitar", "",
          "- Escrever \"não há riscos\": toda pesquisa tem riscos, mesmo mínimos (PROJ-R01).",
          "- Encaminhar participantes ao SUS ou à UBS em caso de dano (PROJ-R06).",
          "- Critério de exclusão que é o contrário da inclusão (PROJ-M05).",
          "- Coleta marcada antes da aprovação prevista no cronograma (PROJ-C13).",
          "- Orçamento \"sem custos\" (PROJ-C12) e restos de instrução dos modelos (GER-07).",
          "- Título, amostra ou equipe diferentes entre os documentos (GER-01 a GER-05).",
          "", "Quando os documentos estiverem prontos, peça a revisão completa do protocolo.", ""]
    return "\n".join(L)


# ----------------------------------------------------------------------------- PDF

def _inline(s: str) -> str:
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", s)
    s = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", s)
    return s


def md_to_pdf(md: str, path: Path) -> Path | None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError:
        return None
    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9.5, leading=12.5)
    small = ParagraphStyle("s", parent=body, fontSize=8, leading=10)
    quote = ParagraphStyle("q", parent=body, leftIndent=10, textColor=colors.HexColor("#444444"), backColor=colors.HexColor("#f2f2f2"))
    bullet = ParagraphStyle("li", parent=body, leftIndent=12, bulletIndent=3)
    story: list = []
    table: list[list[str]] = []

    def flush_table() -> None:
        nonlocal table
        if not table:
            return
        rows = [r for r in table if not all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in r)]
        data = [[Paragraph(_inline(c), small) for c in r] for r in rows]
        t = Table(data, repeatRows=1, colWidths=[(A4[0] - 3.6 * cm) / max(len(rows[0]), 1)] * len(rows[0]))
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef5")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.extend([t, Spacer(1, 6)])
        table = []

    for line in md.splitlines():
        if line.startswith("|"):
            table.append([c for c in line.strip().strip("|").split("|")])
            continue
        flush_table()
        if line.startswith("# "):
            story.append(Paragraph(_inline(line[2:]), ss["Title"]))
        elif line.startswith("## "):
            story.append(Paragraph(_inline(line[3:]), ss["Heading2"]))
        elif line.startswith("### "):
            story.append(Paragraph(_inline(line[4:]), ss["Heading3"]))
        elif line.startswith("> "):
            story.append(Paragraph(_inline(line[2:]), quote))
        elif re.match(r"^\s*[-*] ", line):
            story.append(Paragraph(_inline(re.sub(r"^\s*[-*] ", "", line)), bullet, bulletText="•"))
        elif re.match(r"^\s*\d+\. ", line):
            m = re.match(r"^\s*(\d+)\. (.*)", line)
            story.append(Paragraph(_inline(m.group(2)), bullet, bulletText=f"{m.group(1)}."))
        elif line.strip():
            story.append(Paragraph(_inline(line.strip()), body))
        else:
            story.append(Spacer(1, 4))
    flush_table()
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
                            title="Relatório de pré-submissão ao CEP-UMC")
    doc.build(story)
    return path
