import classify as cl
from conftest import PROTOCOLO


def _read(name):
    return (PROTOCOLO / name).read_text(encoding="utf-8")


def test_norm_preserves_length():
    s = "Critérios de exclusão — São Paulo"
    assert len(cl.norm(s)) == len(s)
    assert cl.norm(s).startswith("criterios de exclusao")


def test_classify_fixture_documents():
    assert cl.classify_document("projeto.md", _read("projeto.md")).tipo == "projeto"
    assert cl.classify_document("tcle.md", _read("tcle.md")).tipo == "tcle"
    assert cl.classify_document("TAI_clinica.md", _read("TAI_clinica.md")).tipo == "tai"
    assert cl.classify_document("roteiro entrevista.md", _read("roteiro entrevista.md")).tipo == "instrumento"


def test_classify_by_content_only():
    txt = "TERMO DE ASSENTIMENTO LIVRE E ESCLARECIDO\nVocê está sendo convidado(a)..."
    assert cl.classify_document("doc1.md", txt).tipo == "tale"
    txt = "Solicito a dispensa do Termo de Consentimento Livre e Esclarecido, pois os prontuários..."
    assert cl.classify_document("doc2.md", txt).tipo == "dispensa"


def test_triage_ignores_exclusion_criteria():
    tri = cl.triage({}, _read("projeto.md"))
    assert tri["Q2"]["valor"] is None  # "menores de 18 anos" está só nos critérios de exclusão
    assert tri["Q1"]["valor"] is True
    assert tri["Q12"]["valor"] is True  # entrevistas gravadas
    assert tri["Q21"]["valor"] == "graduacao"
    assert tri["Q16"]["valor"] is True


def test_detect_level_variants():
    assert cl.detect_level("Dissertação apresentada ao Programa de Mestrado em Biotecnologia")["valor"] == "mestrado"
    assert cl.detect_level("Tese de doutorado")["valor"] == "doutorado"
    assert cl.detect_level("Residência multiprofissional em saúde")["valor"] == "especializacao"
    d = cl.detect_level("Projeto sem informação de curso")
    assert d["valor"] is None and d["assumido"] == "graduacao"


def test_expected_documents_rules():
    def tri(**vals):
        base = {q: {"valor": None} for q in ("Q1", "Q2", "Q3", "Q4", "Q6", "Q7", "Q8", "Q9", "Q11")}
        for k, v in vals.items():
            base[k] = {"valor": v}
        return base

    tipos = lambda t: {e["tipo"] for e in cl.expected_documents(t)}  # noqa: E731
    assert {"tale", "tcle_responsavel"} <= tipos(tri(Q2=True))
    assert "tcle_virtual" in tipos(tri(Q1=True, Q3=True)) and "tcle" not in tipos(tri(Q1=True, Q3=True))
    so_prontuario = tipos(tri(Q6=True))
    assert {"dispensa", "tai"} <= so_prontuario and "tcle" not in so_prontuario
    assert "tcle_amostra" in tipos(tri(Q1=True, Q4=True))
    assert "anuencia_assistencia" in tipos(tri(Q1=True, Q8=True))
