from datetime import date

import checks as ck
import classify as cl
from conftest import PROTOCOLO


def _docs():
    docs = []
    for f in sorted(PROTOCOLO.iterdir()):
        text = f.read_text(encoding="utf-8")
        docs.append({"arquivo": f.name, "tipo": cl.classify_document(f.name, text).tipo, "text": text, "method": "texto", "colored": []})
    return docs


def _run():
    docs = _docs()
    return ck.run_checks(docs, [d["arquivo"] for d in docs], today=date(2026, 11, 25))


def test_expected_signals_found():
    sinais, info = _run()
    ids = {s["id"] for s in sinais}
    expected = {"PB-S10", "TAI-06", "PROJ-R01", "PROJ-R06", "PROJ-C12", "PROJ-B01", "PROJ-C07", "PROJ-C02", "PROJ-M05", "PROJ-C13",
                "TCLE-C06", "TCLE-F08", "TCLE-C11", "TCLE-C12", "D1", "GER-07", "GER-01", "GER-05", "TCLE-C10"}
    assert expected <= ids, expected - ids
    assert info["titulo_projeto"].startswith("Ansiedade e qualidade do sono")


def test_no_false_positives_in_fixture():
    sinais, _ = _run()
    ids = [s["id"] for s in sinais]
    assert "TCLE-F02" not in ids  # a declaração "Eu, ___" está no fim, depois do convite
    assert "PROJ-G06" not in ids  # a capa diz TCC
    assert "PROJ-N08" not in ids  # "convidados em sala de aula"
    xxx = [s for s in sinais if s["id"] == "GER-07" and "XXX" in s["mensagem"]]
    assert not xxx  # o "XXX" do número do parecer é esperado (D10)


def test_snippets_keep_accents():
    sinais, _ = _run()
    r01 = next(s for s in sinais if s["id"] == "PROJ-R01")
    assert "Não há riscos" in r01["trecho"]


def test_refs_are_unique_and_sequential():
    sinais, _ = _run()
    refs = [s["ref"] for s in sinais]
    assert refs == [f"AUTO-{i:03d}" for i in range(1, len(refs) + 1)]


def test_cronograma_ok_has_no_c13():
    proj = (PROTOCOLO / "projeto.md").read_text(encoding="utf-8").replace("Coleta de dados | 01/03/2027", "Coleta de dados | 15/04/2027")
    c = ck.Collector()
    ck.check_projeto(c, "projeto.md", proj, date(2026, 11, 25))
    assert not [s for s in c.items if s.id == "PROJ-C13"]


def test_tale_identical_to_tcle():
    t = "Você está sendo convidado a participar desta pesquisa sobre o sono dos estudantes e seus hábitos noturnos " * 5
    docs = [{"arquivo": "p.md", "tipo": "projeto", "text": "Título: Um estudo qualquer sobre o sono\n"},
            {"arquivo": "tale.md", "tipo": "tale", "text": t}, {"arquivo": "resp.md", "tipo": "tcle_responsavel", "text": t}]
    sinais, info = ck.run_checks(docs, [], today=date(2026, 11, 25))
    assert "TALE-T01" in {s["id"] for s in sinais}
    assert info["similaridade_tale_tcle"] > 0.9
