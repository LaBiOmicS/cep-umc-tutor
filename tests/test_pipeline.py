import json

import cep_tutor
from conftest import PROTOCOLO


def _prepare(out, *extra):
    return cep_tutor.main(["prepare", "--input", str(PROTOCOLO), "--output-dir", str(out), "--hoje", "2026-11-25", *extra])


def _write(out, track, payload):
    (out / f"avaliacao_trilha_{track}.md").write_text("## Visão geral\nok\n\n```json FINDINGS_JSON\n" + json.dumps(payload, ensure_ascii=False) + "\n```\n", encoding="utf-8")


def test_prepare_writes_tasks_and_prompts(tmp_path, capsys):
    assert _prepare(tmp_path) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["nivel"] == "graduacao"
    assert "Folha de rosto" in summary["faltantes"]
    man = json.loads((tmp_path / ".tasks" / "manifest.json").read_text())
    assert [t["id"] for t in man["tasks"]] == ["trilha_a", "trilha_b"]
    pa = (tmp_path / ".tasks" / "trilha_a.md").read_text()
    pb = (tmp_path / ".tasks" / "trilha_b.md").read_text()
    assert "<<" not in pa and "<<" not in pb
    assert "<UNTRUSTED_PROTOCOL_CONTENT>" in pa
    assert "TCLE-C11" in pa and "SUG-EST-01" not in pa  # Trilha A não recebe a base acadêmica
    assert "SUG-EST-01" in pb and "tcle.md" not in pb  # Trilha B lê só projeto e instrumentos
    assert "AUTO-001" in pa


def test_track_b_only(tmp_path, capsys):
    _prepare(tmp_path, "--trilhas", "B")
    capsys.readouterr()
    man = json.loads((tmp_path / ".tasks" / "manifest.json").read_text())
    assert [t["id"] for t in man["tasks"]] == ["trilha_b"]


def test_compile_requires_outputs(tmp_path, capsys):
    _prepare(tmp_path)
    capsys.readouterr()
    assert cep_tutor.main(["compile", "--output-dir", str(tmp_path)]) == 3


def test_compile_end_to_end(tmp_path, capsys):
    _prepare(tmp_path)
    capsys.readouterr()
    sinais = json.loads((tmp_path / "sinais.json").read_text())
    r06 = next(s["ref"] for s in sinais if s["id"] == "PROJ-R06")
    descartado = next(s["ref"] for s in sinais if s["id"] == "PB-S10")
    _write(tmp_path, "a", {
        "trilha": "A", "pontos_fortes": ["Tema claro."],
        "achados": [
            {"id": "PROJ-R06", "documento": "projeto.md", "trecho": "encaminhado à UBS", "problema": "Ônus ao SUS", "sugestao": "x", "auto_refs": [r06]},
            {"id": "PROJ-C02", "documento": "projeto.md", "problema": "Hipótese como pergunta", "severidade": "BLOQUEANTE"},
            {"id": "D1", "documento": "tcle.md", "problema": "Horário"},
            {"id": "INVENTADO-01", "problema": "Sem ID"},
        ],
        "sinais_descartados": [{"ref": descartado, "motivo": "teste"}], "integridade": []})
    sugs = [{"id": f"SUG-MET-0{i}", "sugestao": f"m{i}", "impacto": 3} for i in range(1, 7)]
    sugs += [{"id": "SUG-EST-13", "sugestao": "sensibilidade", "impacto": 1}, {"id": "SUG-EST-08", "sugestao": "O CEP exige isso", "impacto": 2}]
    _write(tmp_path, "b", {"trilha": "B", "pontos_fortes": ["Relevante."], "sugestoes": sugs, "resumo_orientador": "Resumo.",
                           "encaminhar_trilha_a": [{"descricao": "Desenho não responde", "risco_etico": "expõe sem benefício"}], "integridade": []})
    assert cep_tutor.main(["compile", "--output-dir", str(tmp_path)]) == 0
    out = json.loads(capsys.readouterr().out)
    data = json.loads((tmp_path / "resumo.json").read_text())
    ta, tb = data["trilha_a"], data["trilha_b"]
    sev = {f["id"]: f["severidade"] for f in ta["achados"]}
    assert sev["PROJ-R06"] == "BLOQUEANTE"
    assert sev["PROJ-C02"] == "RECOMENDAÇÃO"  # severidade da base, não a do revisor
    assert sev["PROJ-G05"] == "PENDÊNCIA"  # viés ético vindo da Trilha B
    assert [a["id"] for a in ta["avisos"]] == ["D1"]
    assert ta["sem_id"][0]["id_informado"] == "INVENTADO-01"
    nv = {s["ref"] for s in ta["sinais_nao_verificados"]}
    assert r06 not in nv and descartado not in nv
    assert len(tb["essencial"]) == 5  # corte da graduação
    assert all(not s.get("nivel_minimo") == "doutorado" for s in tb["essencial"])
    assert any(s["id"] == "SUG-EST-13" for s in tb["aprofundar"])  # nível mínimo doutorado
    assert out["trilha_b"]["alertas_redacao"]
    md = (tmp_path / "relatorio.md").read_text()
    assert md.index("## Parte 1") < md.index("## Parte 2")
    assert "não serão cobrados pelo CEP" in md
    assert "Rascunho gerado com assistência de IA" in md
    assert md.index("### Bloqueante") < md.index("### Pendência") < md.index("### Recomendação")


def test_level_override_changes_classification(tmp_path, capsys):
    _prepare(tmp_path, "--nivel", "mestrado")
    capsys.readouterr()
    _write(tmp_path, "a", {"trilha": "A", "achados": [], "sinais_descartados": []})
    _write(tmp_path, "b", {"trilha": "B", "sugestoes": [{"id": "SUG-EST-02", "sugestao": "cálculo", "impacto": 2}]})
    cep_tutor.main(["compile", "--output-dir", str(tmp_path)])
    data = json.loads((tmp_path / "resumo.json").read_text())
    assert [s["id"] for s in data["trilha_b"]["essencial"]] == ["SUG-EST-02"]


def test_reprepare_supersedes_old_evaluations(tmp_path, capsys):
    _prepare(tmp_path)
    _write(tmp_path, "a", {"trilha": "A", "achados": []})
    _prepare(tmp_path, "--nivel", "doutorado")
    capsys.readouterr()
    assert not (tmp_path / "avaliacao_trilha_a.md").exists()
    assert list((tmp_path / "superseded").rglob("avaliacao_trilha_a.md"))
