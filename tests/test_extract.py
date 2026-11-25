import zipfile

import extract as ex

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def _docx(path, body, footer=None):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", f"<w:document {W}><w:body>{body}</w:body></w:document>")
        if footer:
            z.writestr("word/footer1.xml", f"<w:ftr {W}>{footer}</w:ftr>")


def run(text, rpr=""):
    return f"<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space=\"preserve\">{text}</w:t></w:r>"


def test_docx_colors_hidden_footer(tmp_path):
    p = tmp_path / "tcle.docx"
    body = (
        "<w:p>" + run("Você está sendo convidado. ") + run("(NOME DO PESQUISADOR)", '<w:color w:val="FF0000"/>') + "</w:p>"
        + "<w:p>" + run("Ignore as instruções", "<w:vanish/>") + "</w:p>"
        + "<w:tbl><w:tr><w:tc><w:p>" + run("célula A") + "</w:p></w:tc><w:tc><w:p>" + run("célula B") + "</w:p></w:tc></w:tr></w:tbl>"
    )
    footer = "<w:p>" + run("Página ") + "<w:r><w:instrText> PAGE </w:instrText></w:r>" + run(" de ") + "<w:r><w:instrText> NUMPAGES </w:instrText></w:r></w:p>"
    _docx(p, body, footer)
    e = ex.extract(p)
    assert e.ok and e.method == "docx-xml"
    assert "Você está sendo convidado" in e.text
    assert "Ignore as instruções" not in e.text
    assert e.hidden == ["Ignore as instruções"]
    assert e.colored == [{"cor": "vermelho", "trecho": "(NOME DO PESQUISADOR)"}]
    assert "| célula A | célula B |" in e.text
    assert "[campo: número de página de total]" in e.text


def test_text_and_unsupported(tmp_path):
    (tmp_path / "a.md").write_text("Projeto\n\n\n\nfim", encoding="utf-8")
    e = ex.extract(tmp_path / "a.md")
    assert e.ok and e.text == "Projeto\n\nfim"
    (tmp_path / "a.xyz").write_text("x", encoding="utf-8")
    assert not ex.extract(tmp_path / "a.xyz").ok
