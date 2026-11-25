import re

import kb


def test_requirements_loaded():
    req = kb.load_requirements()
    assert len(req) > 250
    for it in req.values():
        assert it.severidade in (*kb.SEVERIDADES, None)
        assert it.texto


def test_ids_cited_in_checklists_exist():
    req = kb.load_requirements()
    missing = set()
    for name in ("15-matriz-documentos-por-tipo-de-estudo.md", "16-checklist-pre-submissao.md", "17-erros-frequentes-e-sinais-de-alerta.md"):
        text = (kb.KB_DIR / name).read_text(encoding="utf-8")
        for rid in kb.REQ_ID.findall(text):
            if rid not in req:
                missing.add(rid)
    assert not missing, sorted(missing)


def test_known_severities():
    assert kb.get("PROJ-R06").severidade == "BLOQUEANTE"
    assert kb.get("PROJ-M05").severidade == "PENDÊNCIA"
    assert kb.get("GER-07").arquivo.startswith("16-")


def test_expand_id_list():
    assert kb.expand_id_list("PROJ-R01 a R05") == [f"PROJ-R0{i}" for i in range(1, 6)]
    assert kb.expand_id_list("TCLE-F02/F04/F05") == ["TCLE-F02", "TCLE-F04", "TCLE-F05"]
    assert kb.expand_id_list("PROJ-C10/N14/N15") == ["PROJ-C10", "PROJ-N14", "PROJ-N15"]
    assert kb.expand_id_list("PROJ-N06/TALE-02") == ["PROJ-N06", "TALE-02"]


def test_suggestions_have_level_and_core():
    sugs = kb.load_suggestions()
    assert len(sugs) >= 30
    for it in sugs.values():
        assert it.trilha == "B"
        assert it.nucleo_comum in (True, False), it.id
        assert it.nivel_minimo in kb.NIVEIS, it.id
        assert it.fonte, it.id
        assert re.fullmatch(r"SUG-(MET|EST|ESC)-\d{2}", it.id)


def test_no_suggestion_ids_in_track_a_base():
    for path in kb.KB_DIR.glob("[0-9][0-9]-*.md"):
        assert "SUG-" not in path.read_text(encoding="utf-8"), path.name


def test_discrepancies():
    d = kb.load_discrepancies()
    assert "D1" in d and "D10" in d
