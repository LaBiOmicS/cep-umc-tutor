"""Classificação dos documentos do protocolo, triagem (Q1–Q21) e documentos esperados.

Tudo aqui é heurístico: o resultado traz evidência (trecho) e confiança, e o agente confirma com o usuário o que ficar
incerto. As perguntas e a matriz vêm de `base-conhecimento/15-matriz-documentos-por-tipo-de-estudo.md`.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

DOC_LABELS = {
    "folha_rosto": "Folha de rosto",
    "projeto": "Projeto detalhado",
    "tcle": "TCLE (papel)",
    "tcle_virtual": "TCLE em ambiente virtual",
    "tale": "TALE",
    "tcle_responsavel": "TCLE do responsável",
    "tcle_amostra": "TCLE de cessão de amostra biológica",
    "dispensa": "Solicitação de dispensa do TCLE",
    "tai": "TAI (autorização institucional)",
    "anuencia_assistencia": "Carta de anuência para assistência gratuita",
    "termo_anuencia": "Termo de anuência (coparticipante)",
    "instrumento": "Instrumento de coleta",
    "comprovante_financiamento": "Comprovante de financiamento",
    "carta_resposta": "Carta-resposta a pendências",
    "pb_informacoes_basicas": "Informações Básicas do Projeto (PDF da Plataforma Brasil)",
    "outro": "Outro documento",
}


def _fold(c: str) -> str:
    base = unicodedata.normalize("NFKD", c)[:1] or c
    low = base.lower()
    return low if len(low) == 1 else base


def norm(s: str) -> str:
    """Minúsculas sem acentos, preservando o comprimento (os índices valem também no texto original)."""
    return "".join(_fold(c) for c in s)


# (regex no nome do arquivo, [regex de conteúdo]) — tudo sobre texto normalizado (sem acentos, minúsculo)
DOC_RULES: dict[str, tuple[str | None, list[str]]] = {
    "folha_rosto": (r"folha.?de.?rosto", [r"folha de rosto para pesquisa envolvendo seres humanos"]),
    "projeto": (
        r"projeto|project",
        [r"\bmetodologia\b", r"\bcronograma\b", r"\borcamento\b", r"objetivo geral", r"\bintroducao\b", r"referencias", r"criterios de (in|ex)clusao"],
    ),
    "tcle_virtual": (r"virtual|online|eletronic|digital", [r"ambiente virtual", r"\(\s*\)\s*sim", r"aceito participar", r"concordo em participar", r"formulario (online|eletronico)"]),
    "tale": (r"\btale\b|assentimento", [r"termo de assentimento", r"\bassentimento\b"]),
    "tcle_responsavel": (r"respons", [r"seu\(?s?u?a?\)? filh", r"sua filha|seu filho", r"menor sob sua responsabilidade", r"responsavel legal"]),
    "tcle_amostra": (r"amostra|biolog", [r"cessao de amostra", r"material biologico", r"amostra biologica"]),
    "tcle": (r"tcle|consentimento", [r"termo de consentimento livre e esclarecido", r"voce esta sendo convidad", r"duas vias"]),
    "dispensa": (r"dispensa", [r"dispensa d[oa] (termo de consentimento|tcle)", r"solicit\w* a dispensa"]),
    "tai": (r"\btai\b|autoriza", [r"termo de autorizacao institucional", r"autorizo a realizacao", r"autorizacao para coleta"]),
    "anuencia_assistencia": (r"assist", [r"assistencia gratuita", r"prestara assistencia", r"atendimento gratuito"]),
    "termo_anuencia": (r"anuencia|copartic", [r"termo de anuencia", r"coparticipante"]),
    "instrumento": (r"question|roteiro|instrumento|formul|escala|ficha|entrevista", [r"\bquestionario\b", r"roteiro de entrevista", r"assinale", r"ficha de coleta"]),
    "comprovante_financiamento": (r"financ|fapesp|cnpq|capes|outorga", [r"termo de outorga", r"concessao de (bolsa|auxilio)", r"auxilio a pesquisa"]),
    "carta_resposta": (r"resposta|pendenc", [r"\bpendencia\b", r"\bresposta\s*:", r"parecer consubstanciado"]),
    "pb_informacoes_basicas": (r"pb_?informa|informacoes_?basicas", [r"informacoes basicas do projeto", r"plataforma brasil", r"desenho:", r"tamanho da amostra no brasil", r"instituicao proponente:"]),
}


@dataclass
class DocClass:
    tipo: str
    confianca: str
    contem: list[str] = field(default_factory=list)
    pontos: dict[str, int] = field(default_factory=dict)


def classify_document(filename: str, text: str) -> DocClass:
    fn = norm(filename)
    tx = norm(text[:60000])
    pontos: dict[str, int] = {}
    by_name: list[str] = []
    for tipo, (fpat, cpats) in DOC_RULES.items():
        score = 0
        if fpat and re.search(fpat, fn):
            score += 4
            by_name.append(tipo)
        for cp in cpats:
            if re.search(cp, tx):
                score += 1
        pontos[tipo] = score
    # projeto: precisa de vários marcadores de projeto, porque anexa TCLE, TAI etc.
    proj_markers = sum(1 for cp in DOC_RULES["projeto"][1] if re.search(cp, tx))
    if proj_markers >= 4:
        pontos["projeto"] += 3
    # TCLE genérico perde para as variantes específicas presentes
    for especifico in ("tcle_virtual", "tale", "tcle_responsavel", "tcle_amostra"):
        if pontos[especifico] >= 2:
            pontos["tcle"] -= 1
    ordem = sorted(pontos.items(), key=lambda kv: (-kv[1], list(DOC_RULES).index(kv[0])))
    tipo, top = ordem[0]
    if top < 2:
        return DocClass("outro", "baixa", [], pontos)
    second = ordem[1][1]
    confianca = "alta" if top >= 5 and top - second >= 2 else ("media" if top - second >= 1 else "baixa")
    contem = [t for t, sc in pontos.items() if t != tipo and sc >= 2 and t not in by_name and t != "projeto"]
    return DocClass(tipo, confianca, contem, pontos)


# ----------------------------------------------------------------------------- triagem

TRIAGE: dict[str, tuple[str, list[str]]] = {
    "Q2": ("Menores de 18 anos ou legalmente incapazes", [
        r"menores de (18|dezoito) anos", r"\bcriancas?\b", r"\badolescentes?\b", r"ensino fundamental", r"ensino medio",
        r"\bescolares\b", r"\bincapaz", r"deficiencia (intelectual|cognitiva)", r"\bdemencia\b", r"\bTALE\b"]),
    "Q3": ("Consentimento online", [
        r"google forms?", r"formulario (online|eletronico|virtual|digital)", r"questionario (online|eletronico|virtual)",
        r"ambiente virtual", r"microsoft forms", r"survey ?monkey", r"\blink\b.{0,60}(formulario|questionario)", r"redes sociais"]),
    "Q4": ("Material biológico", [
        r"amostras? biologic", r"material biologic", r"coleta de sangue", r"\bsaliva\b", r"\burina\b", r"\bfezes\b",
        r"biopsia", r"swab", r"\bdentes?\b.{0,40}(extraid|coleta)", r"\bDNA\b", r"tecido"]),
    "Q5": ("Armazenamento de amostra para uso futuro", [r"biobanco", r"biorrepositorio", r"armazenad\w*.{0,80}(futur|posterior)"]),
    "Q6": ("Só prontuários ou dados secundários", [
        r"prontuarios?", r"dados secundarios", r"\blaudos\b", r"base de dados (do|da|de)", r"retrospectiv", r"DATASUS"]),
    "Q7": ("Coleta em local específico", [
        r"\bhospital\b", r"\bclinica\b", r"\bescola\b", r"\bempresa\b", r"\bUBS\b", r"unidade basica", r"\bONG\b",
        r"policlinica", r"centro de (saude|reabilitacao|atencao)", r"\bCAPS\b", r"\blaboratorio\b", r"instituicao de ensino"]),
    "Q8": ("Promessa de encaminhamento a serviço", [
        r"encaminhad\w*", r"clinica[- ]escola", r"policlinica", r"atendimento psicologico", r"acolhimento psicologico", r"suporte psicologico"]),
    "Q9": ("Instituição coparticipante", [r"coparticipante"]),
    "Q10": ("Multicêntrico", [r"multicentric"]),
    "Q11": ("Financiamento externo", [
        r"\bFAPESP\b", r"\bCNPq\b", r"\bCAPES\b", r"\bPIBIC\b", r"\bPIBITI\b", r"financiad\w* (pel|por)", r"patrocinad\w*",
        r"termo de outorga", r"\bbolsa\b"]),
    "Q12": ("Imagem, áudio ou vídeo", [r"\bgravad\w*", r"\bgravacao\b", r"\bfilmag", r"\bfotograf", r"\bvideo\b", r"\baudio\b"]),
    "Q13": ("Grupo-controle", [r"grupo[- ]controle", r"grupo de controle", r"\bplacebo\b"]),
    "Q14": ("Intervenção terapêutica, diagnóstica ou dispositivo", [
        r"ensaio clinico", r"\bintervencao\b", r"\bmedicamento", r"\bdispositivo\b", r"\bprotocolo de tratamento",
        r"randomiz", r"\bterapeutic"]),
    "Q15": ("Área temática especial (CONEP)", [r"genetica humana", r"reproducao humana", r"\bindigenas?\b", r"povos indigenas", r"\bgenoma\b"]),
    "Q19": ("Brindes", [r"\bbrindes?\b", r"\bpresentes?\b.{0,30}participantes"]),
    "Q20": ("Dados pessoais em ambiente digital", [r"\bLGPD\b", r"dados pessoais", r"\be-?mail\b.{0,40}participante", r"armazenamento (em nuvem|digital)"]),
}

NIVEL_PATTERNS: list[tuple[str, str]] = [
    ("graduacao", r"trabalho de conclusao de curso|\bTCC\b|iniciacao cientifica|\bPIBIC\b|\bPIBITI\b|\bmonografia\b|bacharelado|licenciatura|curso de graduacao"),
    ("especializacao", r"especializacao|residencia (medica|multiprofissional|em)|lato sensu"),
    ("mestrado", r"\bmestrado\b|dissertacao|stricto sensu.{0,40}mestr"),
    ("doutorado", r"\bdoutorado\b|\btese\b|pos-doutor"),
    ("docente", r"projeto docente|pesquisa docente|projeto institucional de pesquisa"),
]


def _snippet(tx: str, m: re.Match, width: int = 70) -> str:
    a, b = max(0, m.start() - width), min(len(tx), m.end() + width)
    return " ".join(tx[a:b].split())


def triage(text_by_doc: dict[str, str], projeto_text: str | None = None) -> dict[str, dict]:
    """Respostas às perguntas de triagem, com evidência. valor=None significa 'sem evidência' (confirmar)."""
    raw = projeto_text or "\n".join(text_by_doc.values())
    corpus = norm(raw)
    # Critérios de exclusão citam populações que NÃO participam ("menores de 18 anos"): fora da triagem.
    corpus = re.sub(r"criterios? de exclusao.*?(?=\n\s*(?:#|\d+(?:\.\d+)*[.)]?\s+[a-z])|\Z)", lambda m: " " * len(m.group()), corpus, flags=re.S)
    out: dict[str, dict] = {}
    for q, (label, pats) in TRIAGE.items():
        hits = []
        for p in pats:
            m = re.search(p, corpus, re.IGNORECASE)
            if m:
                hits.append(_snippet(raw, m))
        out[q] = {
            "pergunta": label,
            "valor": True if hits else None,
            "confianca": "alta" if len(hits) >= 2 else ("media" if hits else "baixa"),
            "evidencias": hits[:3],
        }
    # Q1: adultos capazes (padrão sim, salvo estudo só com menores)
    adult = re.search(r"maiores de (18|dezoito)|\badultos?\b|acima de (18|dezoito)|\bprofessores\b|\bprofissionais\b|\buniversitarios\b|\bpais\b", corpus)
    out["Q1"] = {
        "pergunta": "Participantes adultos e capazes",
        "valor": True if adult or not out["Q2"]["valor"] else None,
        "confianca": "media" if adult else "baixa",
        "evidencias": [_snippet(raw, adult)] if adult else [],
    }
    nivel = detect_level(projeto_text or "\n".join(text_by_doc.values()))
    out["Q21"] = {"pergunta": "Nível do trabalho", **nivel}
    out["Q16"] = {
        "pergunta": "Pesquisador principal é aluno de graduação",
        "valor": True if nivel["valor"] == "graduacao" else None,
        "confianca": nivel["confianca"],
        "evidencias": nivel["evidencias"],
    }
    return dict(sorted(out.items(), key=lambda kv: int(kv[0][1:])))


def detect_level(text: str) -> dict:
    tx = norm(text)
    capa = tx[:2500]
    raw = text
    found: list[tuple[int, str, str]] = []
    for nivel, pat in NIVEL_PATTERNS:
        m = re.search(pat, capa, re.IGNORECASE)
        if m:
            found.append((0, nivel, _snippet(raw, m)))
            continue
        m = re.search(pat, tx, re.IGNORECASE)
        if m:
            found.append((1, nivel, _snippet(raw, m)))
    if not found:
        return {"valor": None, "confianca": "baixa", "evidencias": [], "assumido": "graduacao"}
    on_cover = [f for f in found if f[0] == 0]
    pool = on_cover or found
    # Mais de um nível na capa (ex.: "mestrado" no nome do programa e "TCC"): o de menor ordem fica, confiança média
    nivel = pool[0][1]
    conf = "alta" if len(pool) == 1 and on_cover else ("media" if on_cover else "baixa")
    return {"valor": nivel, "confianca": conf, "evidencias": [f[2] for f in pool[:3]]}


# ----------------------------------------------------------------------------- documentos esperados

def expected_documents(tri: dict[str, dict]) -> list[dict]:
    """Lista de documentos esperados, com o motivo e o ID do requisito (arquivo 15 da base)."""
    v = {q: d.get("valor") for q, d in tri.items()}
    exp: list[dict] = [
        {"tipo": "folha_rosto", "obrigatorio": True, "motivo": "Sempre exigida", "id": "PB-D01"},
        {"tipo": "projeto", "obrigatorio": True, "motivo": "Sempre exigido, com anexos e apêndices", "id": "PB-D03"},
    ]
    only_records = bool(v.get("Q6")) and not v.get("Q3") and not v.get("Q2") and not v.get("Q4")
    if only_records:
        exp.append({"tipo": "dispensa", "obrigatorio": False, "motivo": "Uso de prontuários ou dados secundários (Q6): dispensa, se o TCLE for inviável", "id": "DISP-01"})
    if v.get("Q2"):
        exp.append({"tipo": "tale", "obrigatorio": True, "motivo": "Menores ou incapazes (Q2)", "id": "TALE-01"})
        exp.append({"tipo": "tcle_responsavel", "obrigatorio": True, "motivo": "Menores ou incapazes (Q2)", "id": "TALE-01"})
    if v.get("Q3"):
        exp.append({"tipo": "tcle_virtual", "obrigatorio": True, "motivo": "Consentimento online (Q3)", "id": "PB-D02"})
    elif not only_records and (v.get("Q1") or not v.get("Q2")):
        exp.append({"tipo": "tcle", "obrigatorio": True, "motivo": "Participantes adultos (Q1)", "id": "PB-D02"})
    if v.get("Q4"):
        exp.append({"tipo": "tcle_amostra", "obrigatorio": True, "motivo": "Material biológico (Q4)", "id": "PB-D05"})
    if v.get("Q7") or only_records:
        exp.append({"tipo": "tai", "obrigatorio": True, "motivo": "Coleta em local específico ou dados de terceiros (Q7/Q6): um TAI por local", "id": "GER-04"})
    if v.get("Q8"):
        exp.append({"tipo": "anuencia_assistencia", "obrigatorio": True, "motivo": "Encaminhamento a serviço para assistência (Q8)", "id": "ANU-01"})
    if v.get("Q9"):
        exp.append({"tipo": "termo_anuencia", "obrigatorio": True, "motivo": "Instituição coparticipante (Q9)", "id": "PB-D04"})
    if v.get("Q11"):
        exp.append({"tipo": "comprovante_financiamento", "obrigatorio": False, "motivo": "Financiamento externo (Q11)", "id": "PROJ-C12"})
    exp.append({"tipo": "instrumento", "obrigatorio": False, "motivo": "Questionário, roteiro ou ficha de coleta, quando houver", "id": "PROJ-C15"})
    exp.append({"tipo": "pb_informacoes_basicas", "obrigatorio": False,
                "motivo": "Recomendado: o PDF gerado pela Plataforma permite conferir se o formulário é igual ao projeto", "id": "PB-S06"})
    return exp


def inventory(expected: list[dict], present_types: dict[str, list[str]]) -> list[dict]:
    """Compara esperados × recebidos. present_types: tipo -> [arquivos] (inclui documentos anexados dentro do projeto)."""
    out = []
    for e in expected:
        files = present_types.get(e["tipo"], [])
        out.append({**e, "rotulo": DOC_LABELS[e["tipo"]], "arquivos": files, "presente": bool(files)})
    return out
