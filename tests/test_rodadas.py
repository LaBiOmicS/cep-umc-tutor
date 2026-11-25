"""A avaliação é finita: rodadas, tentativas e limites."""

import json
import shutil

import cep_tutor
from conftest import PROTOCOLO


def _prepare(inp, out, *extra):
    return cep_tutor.main(["prepare", "--input", str(inp), "--output-dir", str(out), "--hoje", "2026-11-25", *extra])


def _write(out, track, payload):
    (out / f"avaliacao_trilha_{track}.md").write_text("ok\n\n```json FINDINGS_JSON\n" + json.dumps(payload, ensure_ascii=False) + "\n```\n", encoding="utf-8")


def _round(inp, out, a, b, capsys, *extra):
    _prepare(inp, out, *extra)
    capsys.readouterr()
    _write(out, "a", a)
    if b is not None and (out / ".tasks" / "trilha_b.md").exists():
        _write(out, "b", b)
    assert cep_tutor.main(["compile", "--output-dir", str(out)]) == 0
    capsys.readouterr()
    return json.loads((out / "resumo.json").read_text())


def _copy(tmp_path):
    inp = tmp_path / "protocolo"
    shutil.copytree(PROTOCOLO, inp)
    return inp


A1 = {"achados": [
    {"id": "PROJ-R01", "documento": "projeto.md", "problema": "Nega riscos"},
    {"id": "PROJ-R06", "documento": "projeto.md", "problema": "UBS"},
    {"id": "PROJ-C02", "documento": "projeto.md", "problema": "Hipótese"}]}
B1 = {"sugestoes": [{"id": "SUG-MET-01", "sugestao": "pergunta", "impacto": 3}, {"id": "SUG-EST-02", "sugestao": "cálculo", "impacto": 2}]}


def test_second_round_shows_progress_and_blocks_new_items(tmp_path, capsys):
    inp, out = _copy(tmp_path), tmp_path / "out"
    r1 = _round(inp, out, A1, B1, capsys)
    assert r1["rodada"] == 1 and r1["progresso"] is None
    # o aluno corrige os riscos; o projeto muda → rodada 2
    p = inp / "projeto.md"
    p.write_text(p.read_text(encoding="utf-8").replace("Não há riscos para os participantes.", "Riscos mínimos: cansaço e constrangimento."), encoding="utf-8")
    prompt_state = None
    _prepare(inp, out)
    prompt_state = json.loads(capsys.readouterr().out)
    assert prompt_state["rodada"] == 2
    pa = (out / ".tasks" / "trilha_a.md").read_text()
    assert "Modo verificação" in pa and "`PROJ-R01`" in pa
    a2 = {"achados": [
        {"id": "PROJ-R06", "documento": "projeto.md", "problema": "UBS"},
        {"id": "PROJ-C02", "documento": "projeto.md", "problema": "Hipótese"},
        {"id": "PROJ-C14", "documento": "projeto.md", "problema": "ABNT"},  # recomendação nova: não entra
        {"id": "PROJ-C07", "documento": "projeto.md", "problema": "Sem plano de análise"}]}  # pendência nova: entra
    b2 = {"sugestoes": [{"id": "SUG-EST-02", "sugestao": "cálculo", "impacto": 2},
                        {"id": "SUG-ESC-10", "sugestao": "concisão", "impacto": 1},  # nova, fora do núcleo: não entra
                        {"id": "SUG-EST-08", "sugestao": "p não significativo", "impacto": 3}]}  # nova, núcleo comum: entra
    _write(out, "a", a2)
    _write(out, "b", b2)
    cep_tutor.main(["compile", "--output-dir", str(out)])
    capsys.readouterr()
    r2 = json.loads((out / "resumo.json").read_text())
    ids = {f["id"] for f in r2["trilha_a"]["achados"]}
    assert "PROJ-C14" not in ids and "PROJ-C07" in ids
    assert r2["trilha_a"]["omitidos_por_limite"] == 1
    prog = r2["progresso"]
    assert [x["id"] for x in prog["resolvidos"]] == ["PROJ-R01"]
    assert {x["id"] for x in prog["novos"]} == {"PROJ-C07"}
    b_ids = {s["id"] for s in r2["trilha_b"]["essencial"] + r2["trilha_b"]["aprofundar"]}
    assert b_ids == {"SUG-EST-02", "SUG-EST-08"}
    assert "SUG-MET-01" in prog["sugestoes_atendidas"]
    md = (out / "relatorio.md").read_text()
    assert "## Desde a rodada anterior" in md and "Rodada de revisão:** 2 de 3" in md


def test_cycle_closes_after_max_rounds(tmp_path, capsys):
    inp, out = _copy(tmp_path), tmp_path / "out"
    p = inp / "projeto.md"
    for k in range(3):
        _round(inp, out, A1, B1, capsys)
        p.write_text(p.read_text(encoding="utf-8") + f"\nAjuste {k}.\n", encoding="utf-8")
    _prepare(inp, out)
    s = json.loads(capsys.readouterr().out)
    assert s["rodada"] == 4 and s["ciclo_encerrado"]
    man = json.loads((out / ".tasks" / "manifest.json").read_text())
    assert [t["id"] for t in man["tasks"]] == ["trilha_a"]  # Trilha B não roda mais
    assert "Ciclo encerrado" in (out / ".tasks" / "trilha_a.md").read_text()
    _write(out, "a", A1)
    cep_tutor.main(["compile", "--output-dir", str(out)])
    capsys.readouterr()
    assert "Ciclo de revisão encerrado" in (out / "relatorio.md").read_text()


def test_recompile_same_documents_is_same_round(tmp_path, capsys):
    inp, out = _copy(tmp_path), tmp_path / "out"
    _round(inp, out, A1, B1, capsys)
    _prepare(inp, out)
    assert json.loads(capsys.readouterr().out)["rodada"] == 1


def test_attempts_are_limited(tmp_path, capsys):
    out = tmp_path / "out"
    _prepare(PROTOCOLO, out)
    capsys.readouterr()
    cep_tutor.main(["next", "--output-dir", str(out)])
    assert json.loads(capsys.readouterr().out)["tarefas_pendentes"] == 2
    cep_tutor.main(["next", "--output-dir", str(out)])
    res = json.loads(capsys.readouterr().out)
    assert res["tarefas_pendentes"] == 0 and set(res["falharam"]) == {"trilha_a", "trilha_b"}
    assert "aviso" in res
    assert cep_tutor.main(["compile", "--output-dir", str(out)]) == 0  # compila com as trilhas não avaliadas
    capsys.readouterr()
    md = (out / "relatorio.md").read_text()
    assert "falhou duas vezes" in md


def test_caps_by_level(tmp_path, capsys):
    out = tmp_path / "out"
    _prepare(PROTOCOLO, out, "--nivel", "mestrado")
    capsys.readouterr()
    _write(out, "a", {"achados": []})
    sugs = [{"id": f"SUG-MET-{i:02d}", "sugestao": str(i), "impacto": 2} for i in range(1, 17)]
    sugs += [{"id": f"SUG-EST-{i:02d}", "sugestao": str(i), "impacto": 1} for i in range(1, 15)]
    _write(out, "b", {"sugestoes": sugs})
    cep_tutor.main(["compile", "--output-dir", str(out)])
    capsys.readouterr()
    tb = json.loads((out / "resumo.json").read_text())["trilha_b"]
    assert len(tb["essencial"]) == cep_tutor.LIMITE_ESSENCIAL["mestrado"]
    assert len(tb["aprofundar"]) == cep_tutor.LIMITE_APROFUNDAR
    assert tb["omitidas_por_limite"] > 0


def test_supervisor_report_and_deadline(tmp_path, capsys):
    out = tmp_path / "out"
    _round(PROTOCOLO, out, A1, B1, capsys)
    o = (out / "relatorio_orientador.md").read_text()
    assert "Ainda não está pronto para submeter" in o
    assert "Assinaturas a providenciar" in o and "TAI-09" in o
    md = (out / "relatorio.md").read_text()
    assert "## Prazo para submeter" in md and "01/03/2027" in md and "10/01/2027" in md  # 01/03/2027 − 50 dias
    assert "já passou" in md  # 11/11/2026 é anterior à data de geração do relatório
    assert "## Comece por aqui" in md and "Quem submete" in md


def test_planejar_without_documents(tmp_path, capsys):
    assert cep_tutor.main(["planejar", "--output-dir", str(tmp_path), "--q", "Q2=sim", "--q", "Q7=sim", "--nivel", "graduacao", "--coleta", "2027-06-01"]) == 0
    res = json.loads(capsys.readouterr().out)
    assert {"TALE", "TCLE do responsável", "TAI (autorização institucional)"} <= set(res["documentos"])
    md = (tmp_path / "planejamento.md").read_text()
    assert "Quem assina" in md and "12/04/2027" in md  # 01/06/2027 − 50 dias
