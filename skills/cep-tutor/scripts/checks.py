"""Sinais automáticos da Trilha A (determinísticos), derivados de `17-erros-frequentes-e-sinais-de-alerta.md`.

Cada sinal é **indicativo**: o revisor da Trilha A confirma ou descarta, com o contexto. O ID aponta para o requisito
da base; a severidade é atribuída depois, em `compile`, a partir da base (nunca pelo sinal).
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date

from classify import norm

TERMOS_TCLE = ("tcle", "tcle_virtual", "tale", "tcle_responsavel", "tcle_amostra")
TERMOS_PAPEL = ("tcle", "tale", "tcle_responsavel", "tcle_amostra")

SECOES = [
    "introducao", "justificativa", "hipotese", "objetivo", "desenho", "metodologia", "local", "amostra", "amostragem",
    "participantes", "recrutamento", "procedimento", "criterios de inclusao", "criterios de exclusao", "criterio de inclusao",
    "criterio de exclusao", "riscos", "beneficios", "analise", "plano de analise", "desfecho", "cronograma", "orcamento",
    "referencias", "anexo", "apendice", "suspensao", "encerramento", "divulgacao", "resultados esperados", "consideracoes eticas",
]
HEADING = re.compile(r"^\s*(?:#+\s*)?(?:\d+(?:\.\d+)*\.?\s*[-–)]?\s*)?(?P<h>[a-z][a-z ,/()-]{2,80})\s*:?\s*$")


@dataclass
class Sinal:
    ref: str
    id: str
    arquivo: str
    tipo_doc: str
    trecho: str
    mensagem: str
    confianca: str = "media"


def _snip(text: str, m: re.Match, w: int = 80) -> str:
    a, b = max(0, m.start() - w), min(len(text), m.end() + w)
    return " ".join(text[a:b].split())


def sections(text: str) -> dict[str, str]:
    """Divide o projeto por títulos conhecidos. Chave = título normalizado (primeira ocorrência)."""
    lines = text.splitlines()
    out: dict[str, list[str]] = {}
    cur = None
    for line in lines:
        nl = norm(line)
        m = HEADING.match(nl)
        if m and len(nl.strip()) <= 90 and any(m.group("h").strip().startswith(s) for s in SECOES):
            cur = m.group("h").strip()
            out.setdefault(cur, [])
            continue
        if cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def find_section(secs: dict[str, str], *names: str) -> tuple[str | None, str]:
    for k, v in secs.items():
        if any(k.startswith(n) for n in names):
            return k, v
    return None, ""


DATE_RE = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b")
MONTH_ONLY_RE = re.compile(r"\b(?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[a-z]*\.?\s*(?:/|de)?\s*\d{4}\b|\b\d{1,2}/\d{4}\b|\bsemestre\b|\bbimestre\b|\btrimestre\b")


def _dates(s: str) -> list[date]:
    out = []
    for d, m, y in DATE_RE.findall(s):
        try:
            out.append(date(int(y), int(m), int(d)))
        except ValueError:
            pass
    return out


class Collector:
    def __init__(self) -> None:
        self.items: list[Sinal] = []

    def add(self, rid: str, arquivo: str, tipo: str, trecho: str, msg: str, conf: str = "media") -> None:
        key = (rid, arquivo, trecho[:60], msg[:40])
        if any((s.id, s.arquivo, s.trecho[:60], s.mensagem[:40]) == key for s in self.items):
            return
        self.items.append(Sinal(f"AUTO-{len(self.items) + 1:03d}", rid, arquivo, tipo, trecho[:300], msg, conf))

    def search(self, rid: str, arquivo: str, tipo: str, raw: str, pattern: str, msg: str, conf: str = "media", limit: int = 1) -> int:
        """Procura no texto normalizado; o trecho sai do texto original (norm preserva os índices)."""
        n = 0
        for m in re.finditer(pattern, norm(raw), re.IGNORECASE | re.S):
            self.add(rid, arquivo, tipo, _snip(raw, m), msg, conf)
            n += 1
            if n >= limit:
                break
        return n


def check_projeto(c: Collector, arq: str, raw: str, today: date) -> dict:
    """Sinais do projeto. Devolve as datas do cronograma (início da coleta e aprovação prevista), se encontradas."""
    t = norm(raw)
    tp = "projeto"
    datas: dict = {}
    c.search("PROJ-R01", arq, tp, raw, r"nao (ha|havera|oferece|apresenta|existem?) (nenhum )?riscos?|sem riscos|risco zero|riscos? inexistentes?|isent[oa] de riscos?",
             "Afirma que não há riscos: toda pesquisa envolve algum risco, mesmo mínimo.")
    c.search("PROJ-R06", arq, tp, raw, r"encaminhad\w*.{0,80}(\bSUS\b|\bUBS\b|posto de saude|rede publica|unidade basica|servico publico)",
             "Encaminhamento ao SUS ou a serviço público para atender danos da pesquisa.")
    c.search("PROJ-R08", arq, tp, raw, r"\bvoce (podera|pode|sentira|tera)\b", "Texto dirigido ao participante dentro do projeto (riscos/benefícios devem estar na 3ª pessoa).", "baixa")
    c.search("PROJ-C12", arq, tp, raw, r"r\$\s*0+,00|(orcamento|custos? (da|do) (pesquisa|projeto)).{0,80}(nao havera|sem custo|nenhum custo|isento)",
             "Orçamento sem custos: toda pesquisa tem despesas (impressão, transporte, materiais).")
    c.search("PROJ-B01", arq, tp, raw, r"benefici\w*.{0,150}(\btcc\b|formacao do (pesquisador|aluno)|conclusao (de|do) curso|obtencao do titulo)",
             "Benefício descrito para o pesquisador; o benefício deve ser do participante ou da sociedade.")
    if not re.search(r"trabalho de conclusao|\btcc\b|iniciacao cientifica|monografia|dissertacao|\btese\b|mestrado|doutorado|especializacao|residencia|pibic|projeto docente", t[:4000]):
        c.add("PROJ-G06", arq, tp, raw[:200], "A capa não parece informar a finalidade acadêmica (TCC, IC, mestrado...).", "baixa")
    if not re.search(r"plano de analise|analise (estatistica|dos dados|de conteudo|tematica|descritiva)|teste (t|qui|de)|software (r|spss|stata|jamovi)", t):
        c.add("PROJ-C07", arq, tp, "", "Não foi encontrado plano de análise dos dados.", "media")
    if re.search(r"suspens\w*|encerramento", t) and not re.search(r"(autorizacao|aprovacao) previa do (sistema )?cep", t):
        m = re.search(r"suspens\w*|encerramento", t)
        c.add("PROJ-C11", arq, tp, _snip(raw, m), "Critérios de suspensão sem a frase de autorização prévia do Sistema CEP/CONEP.", "baixa")
    if not re.search(r"(recrutad|convidad|abordad|divulgad|contatad)\w*", t):
        c.add("PROJ-N08", arq, tp, "", "Não foi encontrada a descrição de como os participantes serão recrutados ou abordados.", "baixa")

    secs = sections(raw)
    _, hip = find_section(secs, "hipotese")
    if hip and "?" in hip:
        c.add("PROJ-C02", arq, tp, " ".join(hip.split())[:200], "Hipótese escrita como pergunta.", "media")

    _, inc = find_section(secs, "criterios de inclusao", "criterio de inclusao")
    _, exc = find_section(secs, "criterios de exclusao", "criterio de exclusao")
    ni, ne = norm(inc), norm(exc)
    if ni and ne:
        adult_in = re.search(r"(maiores|acima) de (18|dezoito)|(18|dezoito) anos ou mais|>=?\s*18|≥\s*18|idade (igual|superior) a 18", ni)
        minor_ex = re.search(r"menores de (18|dezoito)|abaixo de (18|dezoito)|<\s*18|idade inferior a 18", ne)
        if adult_in and minor_ex:
            c.add("PROJ-M05", arq, tp, " ".join(exc.split())[:200], "Exclusão por idade é a antítese da inclusão por idade.", "alta")
        m = re.search(r"(nao (aceitarem|concordarem|assinarem|quiserem)|recus\w+ (a )?(assinar|participar))", ne)
        if m:
            c.add("PROJ-M05", arq, tp, _snip(exc, m), "Recusar o TCLE não é critério de exclusão: quem não consente simplesmente não participa.", "media")

    _, crono = find_section(secs, "cronograma")
    nc = norm(crono)
    if crono:
        if not re.search(r"aprovac", nc):
            c.add("PROJ-C13", arq, tp, " ".join(crono.split())[:200], "Cronograma sem as linhas de encaminhamento e aprovação pelo CEP.", "media")
        if MONTH_ONLY_RE.search(nc) and not DATE_RE.search(nc):
            c.add("PROJ-N09", arq, tp, " ".join(crono.split())[:200], "Cronograma sem dia, mês e ano (só meses, semestres ou mm/aaaa).", "media")
        apr: list[date] = []
        col: list[date] = []
        for line in crono.splitlines():
            ln = norm(line)
            if "aprova" in ln:
                apr += _dates(ln)
            if re.search(r"coleta|aplicacao (do|dos) (questionario|instrumento)|entrevistas", ln):
                col += _dates(ln)
        if col:
            datas["coleta_inicio"] = min(col).isoformat()
        if apr:
            datas["aprovacao_prevista"] = max(apr).isoformat()
        if apr and col and min(col) < max(apr):
            c.add("PROJ-C13", arq, tp, " ".join(crono.split())[:200], f"Coleta prevista ({min(col):%d/%m/%Y}) antes da aprovação prevista ({max(apr):%d/%m/%Y}).", "alta")
        if col and min(col) < today:
            c.add("PROJ-C13", arq, tp, " ".join(crono.split())[:200], f"Coleta prevista para data já passada ({min(col):%d/%m/%Y}).", "alta")
    else:
        c.add("PROJ-N09", arq, tp, "", "Não foi encontrada a seção de cronograma.", "baixa")
    return datas


def check_termo(c: Collector, arq: str, tipo: str, raw: str, method: str) -> None:
    t = norm(raw)
    head = t[: max(600, len(t) // 7)]
    m = re.search(r"\beu,?\s*(_{3,}|\.{5,}|\(nome)", head)
    if m and not re.search(r"convidad", head[: m.start()]):
        c.add("TCLE-F02", arq, tipo, _snip(raw, m), "O termo começa como declaração do participante, e não como convite.", "media")
    c.search("TCLE-F04", arq, tipo, raw, r"comprometo-me|me comprometo|o participante se compromete|voce se compromete", "Compromisso imposto ao participante.")
    c.search("TCLE-C06", arq, tipo, raw, r"nao (ha|havera|oferece|apresenta|existem?) (nenhum )?riscos?|sem riscos|risco zero|isent[oa] de riscos?", "Afirma que não há riscos.")
    c.search("TCLE-C07", arq, tipo, raw, r"encaminhad\w*.{0,80}(\bSUS\b|\bUBS\b|posto de saude|rede publica|unidade basica)", "Encaminhamento ao serviço público.")
    c.search("TCLE-C15", arq, tipo, raw, r"(assistencia|atendimento).{0,80}(pelo tempo da pesquisa|ate o (fim|final|termino) (do estudo|da pesquisa)|durante a pesquisa)", "Assistência limitada ao tempo da pesquisa.")
    c.search("TCLE-C16", arq, tipo, raw, r"indeniza\w*.{0,60}seguro|conforme (o )?seguro", "Indenização condicionada a seguro.")
    c.search("TCLE-C18", arq, tipo, raw, r"voce recebera r\$|pagamento de r\$|sera pago|remunera(do|cao) (pela|por sua) participacao", "Pagamento ao participante (só cabe ressarcimento).")
    if re.search(r"ressarci", t) and not re.search(r"acompanhante", t):
        c.add("TCLE-C18", arq, tipo, _snip(raw, re.search(r"ressarci", t)), "Ressarcimento sem citar o acompanhante.", "media")
    c.search("TCLE-C08", arq, tipo, raw, r"benefici\w*.{0,150}(\btcc\b|formacao do (pesquisador|aluno)|conclusao (de|do) curso|obtencao do titulo)", "Benefício descrito para o pesquisador, não para o participante.")
    if tipo in TERMOS_PAPEL:
        c.search("TCLE-F08", arq, tipo, raw, r"\bcopia\b", "\"Cópia\" num termo em papel: o correto é \"via\".", "media", limit=1)
        if not re.search(r"pagina \d+ de \d+|\[campo: numero de pagina|rubrica", t):
            conf = "media" if method in ("docx-xml", "pdftotext", "pypdf") else "baixa"
            c.add("TCLE-F09", arq, tipo, "", "Não foram encontrados \"Página X de Y\" nem campos de rubrica no rodapé.", conf)
    if tipo == "tcle_virtual":
        c.search("TCLEV-02", arq, tipo, raw, r"\bduas vias\b|\buma via\b", "\"Via\" num TCLE online: o correto é \"cópia\".", "media", limit=1)
        if re.search(r"assinatura d[oa] participante|_{8,}\s*\n?\s*assinatura", t):
            c.add("TCLEV-01", arq, tipo, _snip(raw, re.search(r"assinatura", t)), "Campo de assinatura num TCLE online (deve ser aceite SIM/NÃO).", "media")
        if not re.search(r"\bsim\b.{0,80}\bnao\b|\(\s*\)\s*sim|aceito participar|concordo em participar", t):
            c.add("TCLEV-03", arq, tipo, "", "Não foi encontrado o aceite digital com SIM e NÃO.", "media")
    # contatos
    emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", raw)
    phones = re.findall(r"\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4}", raw)
    team_emails = [e for e in emails if not e.lower().startswith(("cep@", "conep"))]
    if not team_emails:
        c.add("TCLE-C11", arq, tipo, "", "Não há e-mail da equipe de pesquisa.", "media")
    if len(phones) < 2:
        c.add("TCLE-C11", arq, tipo, "", "Poucos telefones: incluir pesquisador responsável e assistentes.", "baixa")
    if not re.search(r"24 ?(h|horas)", t):
        c.add("TCLE-C11", arq, tipo, "", "Não informa disponibilidade da equipe 24 horas por dia, 7 dias por semana.", "media")
    if "cep@umc.br" not in t and "4798-7085" not in t:
        c.add("TCLE-C12", arq, tipo, "", "Faltam os contatos do CEP-UMC (cep@umc.br, (11) 4798-7085).", "alta")
    if "conep" not in t:
        c.add("TCLE-C12", arq, tipo, "", "Faltam os contatos da CONEP.", "media")
    m = re.search(r"\b0?8 ?h(00)? (as|a) 15 ?h|\b0?8 (as|a) 15 ?h", t)
    if m:
        c.add("D1", arq, tipo, _snip(raw, m), "Horário do CEP-UMC 8h–15h (modelo de 2022); o Regimento de 2025 diz 12h–18h. Confirmar com o CEP.", "alta")
    if tipo == "tcle_responsavel":
        if re.search(r"\bvoce (participara|sera (convidad|submetid))", t) and not re.search(r"seu\(?s?u?a?\)? filh|sua filha|seu filho|o\(a\) menor|a crianca", t):
            c.add("TALE-R02", arq, tipo, "", "TCLE do responsável trata o responsável como participante.", "media")
    if tipo == "tcle_amostra":
        c.search("AMOS-01", arq, tipo, raw, r"\bdoa(cao|r|da|do)\b", "\"Doação\" de amostra: o correto é \"cessão\".")
        c.search("AMOS-07", arq, tipo, raw, r"armazenad\w*.{0,80}(futur|posterior|outr[oa]s? (estudos|pesquisas))", "Armazenamento para uso futuro: consultar o CEP (biobanco/biorrepositório).")


def check_common(c: Collector, arq: str, tipo: str, raw: str, colored: list[dict]) -> None:
    t = norm(raw)
    for m in re.finditer(r"\bx{3,}\b", t):
        ctx = t[max(0, m.start() - 80) : m.end() + 40]
        if "parecer" not in ctx:
            c.add("GER-07", arq, tipo, _snip(raw, m), "\"XXX\" de modelo não preenchido.", "alta")
            break
    c.search("GER-07", arq, tipo, raw, r"\b(preencher|inserir|deletar|apagar) (se houver|aqui|essa informacao|este texto|antes de imprimir)|\(nome (completo|do (local|projeto|pesquisador))|titulo do projeto\)|nome do pesquisador responsavel \(",
             "Texto de instrução do modelo não removido.", "alta")
    reds = [x["trecho"] for x in colored if x["cor"] == "vermelho"]
    blues = [x["trecho"] for x in colored if x["cor"] == "azul"]
    if reds:
        c.add("GER-07", arq, tipo, " | ".join(reds[:3]), f"{len(reds)} trecho(s) em vermelho (cor de instrução nos modelos do CEP-UMC).", "media")
    if blues:
        c.add("GER-07", arq, tipo, " | ".join(blues[:3]), f"{len(blues)} trecho(s) em azul (cor de campo a preencher nos modelos).", "baixa")
    if tipo == "tai":
        if re.search(r"toda (a )?(infra)?estrutura necessaria", t) and not re.search(r"\bsalas?\b|equipament|computador|arquivo", t):
            c.add("TAI-06", arq, tipo, _snip(raw, re.search(r"toda (a )?(infra)?estrutura necessaria", t)), "Infraestrutura descrita de forma genérica.", "media")
    if tipo == "dispensa":
        if re.search(r"retrospectiv", t) and not re.search(r"obito|falecid|contato|endereco|telefone|perda de seguimento|inviav|impossivel localizar", t):
            c.add("DISP-C04", arq, tipo, _snip(raw, re.search(r"retrospectiv", t)), "Justificativa da dispensa apoiada só em ser retrospectivo.", "media")


def check_filenames(c: Collector, files: list[str]) -> None:
    for f in files:
        if re.search(r"[^A-Za-z0-9_.-]", f):
            c.add("PB-S10", f, "-", f, "Nome de arquivo com acento, espaço ou caractere especial (a Plataforma Brasil recusa).", "alta")


def _title(projeto: str) -> str | None:
    m = re.search(r"t[ií]tulo(?: d[oa] (?:projeto|pesquisa))?\s*[:\-–]\s*(.{15,250})", projeto, re.IGNORECASE)
    if m:
        return " ".join(m.group(1).split()).strip(" .\"“”")
    return None


def _key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", norm(s)).strip()


def check_consistency(c: Collector, docs: list[dict]) -> dict:
    projetos = [d for d in docs if d["tipo"] == "projeto"]
    proj = max(projetos, key=lambda d: d.get("pontos_projeto", 0)) if projetos else None
    info: dict = {"titulo_projeto": None}
    if not proj:
        return info
    title = _title(proj["text"])
    info["titulo_projeto"] = title
    if title and len(_key(title)) > 15:
        k = _key(title)
        for d in docs:
            if d is proj or d["tipo"] in ("instrumento", "outro", "comprovante_financiamento", "folha_rosto"):
                continue
            if k not in _key(d["text"]):
                c.add("GER-01", d["arquivo"], d["tipo"], title, "O título do projeto não aparece idêntico neste documento.", "media")
    nums_proj = {int(n) for n in re.findall(r"\b(\d{1,5}) (?:participantes|voluntarios|sujeitos|individuos|pacientes|alunos|criancas)", norm(proj["text"]))}
    for d in docs:
        if d["tipo"] in TERMOS_TCLE and nums_proj:
            nums = {int(n) for n in re.findall(r"\b(\d{1,5}) (?:participantes|voluntarios|pessoas|pacientes|alunos|criancas)", norm(d["text"]))}
            diff = nums - nums_proj
            if diff:
                c.add("GER-05", d["arquivo"], d["tipo"], f"projeto: {sorted(nums_proj)}; termo: {sorted(nums)}", "Número de participantes diferente entre o termo e o projeto.", "media")
    if re.search(r"\bgravad\w*|\bgravacao\b|\bfilmag|\bfotograf|\bvideo\b", norm(proj["text"])):
        for d in docs:
            if d["tipo"] in TERMOS_TCLE and not re.search(r"\bimagem\b|\bvoz\b|\bgravac|\bgravad|\baudio\b|\bvideo\b|\bfoto", norm(d["text"])):
                c.add("TCLE-C10", d["arquivo"], d["tipo"], "", "O projeto prevê gravação ou imagem, mas o termo não tem cláusula de imagem e som.", "alta")
    tale = next((d for d in docs if d["tipo"] == "tale"), None)
    base = next((d for d in docs if d["tipo"] in ("tcle_responsavel", "tcle")), None)
    if tale and base:
        sim = _jaccard(tale["text"], base["text"])
        info["similaridade_tale_tcle"] = round(sim, 2)
        if sim > 0.6:
            c.add("TALE-T01", tale["arquivo"], "tale", f"similaridade {sim:.0%}", "TALE quase igual ao TCLE: a linguagem deve ser adequada à idade.", "alta")
    return info


def _jaccard(a: str, b: str) -> float:
    def grams(s: str) -> set[tuple[str, ...]]:
        w = re.findall(r"[a-z]{3,}", norm(s))
        return {tuple(w[i : i + 3]) for i in range(len(w) - 2)}

    ga, gb = grams(a), grams(b)
    return len(ga & gb) / len(ga | gb) if ga and gb else 0.0


def run_checks(docs: list[dict], filenames: list[str], today: date | None = None) -> tuple[list[dict], dict]:
    """docs: [{arquivo, tipo, text, method, colored}] → (sinais, info)."""
    today = today or date.today()
    c = Collector()
    check_filenames(c, filenames)
    projetos = [d for d in docs if d["tipo"] == "projeto"]
    principal = max(projetos, key=lambda d: d.get("pontos_projeto", 0)) if projetos else None
    datas: dict = {}
    for d in docs:
        if d["tipo"] == "projeto":
            r = check_projeto(c, d["arquivo"], d["text"], today)
            if d is principal:
                datas = r
        if d["tipo"] in TERMOS_TCLE:
            check_termo(c, d["arquivo"], d["tipo"], d["text"], d.get("method", ""))
        check_common(c, d["arquivo"], d["tipo"], d["text"], d.get("colored", []))
    info = check_consistency(c, docs)
    info.update(datas)
    return [asdict(s) for s in c.items], info
