# /// script
# requires-python = ">=3.10"
# dependencies = ["pypdf>=4.0.0", "olefile>=0.47"]
# ///
"""Extração de texto dos documentos do protocolo.

- .docx: leitura direta do XML (sem dependências), na ordem do corpo, com tabelas, cabeçalhos e rodapés. Registra
  trechos em **vermelho ou azul** (as cores de instrução e de preenchimento dos modelos do CEP-UMC) e texto **oculto**
  (vanish, branco, fonte microscópica).
- .doc (Word 97-2003): tabela de peças do fluxo WordDocument (olefile).
- .pdf: pdftotext -layout; sem ele, pypdf.
- .md, .txt: leitura direta. .odt, .rtf, .html: pandoc, se instalado.

Uso: extract.py ARQUIVO [--json]
"""

from __future__ import annotations

import json
import re
import shutil
import struct
import subprocess
import sys
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SUPPORTED = {".docx", ".doc", ".pdf", ".md", ".txt", ".odt", ".rtf", ".html", ".htm"}

# Cores típicas dos modelos do CEP-UMC: vermelho = instrução; azul = campo a preencher.
RED = re.compile(r"^(FF0000|C00000|E60000|FF3333|CC0000|EE0000|D00000)$", re.I)
BLUE = re.compile(r"^(0000FF|0070C0|0066CC|1F4E79|2E74B5|0033CC|3366FF|0000CC|4472C4)$", re.I)
WHITE = re.compile(r"^(FFFFFF|FEFEFE|FDFDFD)$", re.I)


@dataclass
class Extraction:
    path: str
    text: str = ""
    method: str = ""
    ok: bool = True
    error: str | None = None
    colored: list[dict] = field(default_factory=list)  # [{"cor": "vermelho"|"azul", "trecho": ...}]
    hidden: list[str] = field(default_factory=list)
    words: int = 0


def _docx_runs_text(p: ET.Element, ext: Extraction) -> str:
    parts: list[str] = []
    groups: list[list] = []  # [cor, texto, índice do próximo run] de runs coloridos consecutivos
    for r in p.iter(f"{W}r"):
        rpr = r.find(f"{W}rPr")
        txt = "".join((t.text or "") for t in r.iter(f"{W}t"))
        if r.find(f"{W}tab") is not None:
            txt = "\t" + txt
        if r.find(f"{W}br") is not None:
            txt += "\n"
        hidden = False
        color = None
        if rpr is not None:
            if rpr.find(f"{W}vanish") is not None:
                hidden = True
            c = rpr.find(f"{W}color")
            if c is not None:
                color = c.get(f"{W}val")
            sz = rpr.find(f"{W}sz")
            if sz is not None and (sz.get(f"{W}val") or "99").isdigit() and int(sz.get(f"{W}val")) <= 4:
                hidden = True
        if color and WHITE.match(color):
            hidden = True
        if hidden and txt.strip():
            ext.hidden.append(txt.strip()[:200])
            continue
        cor = None
        if color and RED.match(color):
            cor = "vermelho"
        elif color and BLUE.match(color):
            cor = "azul"
        if cor and txt:
            if groups and groups[-1][0] == cor and groups[-1][2] == len(parts):
                groups[-1][1] += txt
                groups[-1][2] = len(parts) + 1
            else:
                groups.append([cor, txt, len(parts) + 1])
        parts.append(txt)
    for cor, trecho, _ in groups:
        trecho = " ".join(trecho.split())
        if len(re.findall(r"\w", trecho)) >= 3:
            ext.colored.append({"cor": cor, "trecho": trecho[:200]})
    return "".join(parts)


def _docx_block(el: ET.Element, ext: Extraction, out: list[str]) -> None:
    for child in el:
        if child.tag == f"{W}p":
            out.append(_docx_runs_text(child, ext))
        elif child.tag == f"{W}tbl":
            for tr in child.iter(f"{W}tr"):
                cells = []
                for tc in tr.findall(f"{W}tc"):
                    cells.append(" ".join(_docx_runs_text(p, ext) for p in tc.iter(f"{W}p")).strip())
                out.append("| " + " | ".join(cells) + " |")
        elif child.tag == f"{W}sdt":
            content = child.find(f"{W}sdtContent")
            if content is not None:
                _docx_block(content, ext, out)


def extract_docx(path: Path, ext: Extraction) -> None:
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        out: list[str] = []
        for part in sorted(n for n in names if re.match(r"word/header\d*\.xml", n)):
            _docx_block(ET.fromstring(z.read(part)), ext, out)
        body = ET.fromstring(z.read("word/document.xml")).find(f"{W}body")
        if body is not None:
            _docx_block(body, ext, out)
        footers = sorted(n for n in names if re.match(r"word/footer\d*\.xml", n))
        if footers:
            out.append("\n[RODAPÉ]")
            for part in footers:
                root = ET.fromstring(z.read(part))
                _docx_block(root, ext, out)
                # campos PAGE/NUMPAGES aparecem como instrução de campo, não como texto
                instr = " ".join((i.text or "") for i in root.iter(f"{W}instrText"))
                if "PAGE" in instr:
                    out.append("[campo: número de página" + (" de total" if "NUMPAGES" in instr else "") + "]")
    ext.text = "\n".join(out)
    ext.method = "docx-xml"


def extract_doc(path: Path, ext: Extraction) -> None:
    import olefile  # type: ignore

    ole = olefile.OleFileIO(str(path))
    wd = ole.openstream("WordDocument").read()
    flags = struct.unpack_from("<H", wd, 0x0A)[0]
    tbl = ole.openstream("1Table" if flags & 0x0200 else "0Table").read()
    fc_clx, lcb_clx = struct.unpack_from("<II", wd, 0x01A2)
    clx = tbl[fc_clx : fc_clx + lcb_clx]
    i = 0
    while clx[i] == 0x01:
        i += 3 + struct.unpack_from("<H", clx, i + 1)[0]
    if clx[i] != 0x02:
        raise ValueError("tabela de peças não encontrada")
    lcb = struct.unpack_from("<I", clx, i + 1)[0]
    plc = clx[i + 5 : i + 5 + lcb]
    n = (lcb - 4) // 12
    cps = struct.unpack_from(f"<{n + 1}I", plc, 0)
    out = []
    for k in range(n):
        pcd = plc[4 * (n + 1) + 8 * k : 4 * (n + 1) + 8 * k + 8]
        fc = struct.unpack_from("<I", pcd, 2)[0]
        cnt = cps[k + 1] - cps[k]
        if fc & 0x40000000:
            fc = (fc & ~0x40000000) // 2
            out.append(wd[fc : fc + cnt].decode("cp1252", "replace"))
        else:
            out.append(wd[fc : fc + 2 * cnt].decode("utf-16-le", "replace"))
    t = "".join(out)
    t = t.replace("\r", "\n").replace("\x07", "\t").replace("\x0b", "\n").replace("\x0c", "\n")
    t = re.sub(r"\x13[^\x14\x15]*\x14", "", t)
    ext.text = re.sub(r"[\x13\x14\x15\x01\x08]", "", t)
    ext.method = "doc-olefile"


def extract_pdf(path: Path, ext: Extraction) -> None:
    if shutil.which("pdftotext"):
        proc = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, check=False)
        if proc.returncode == 0 and proc.stdout.strip():
            ext.text, ext.method = proc.stdout, "pdftotext"
            return
    from pypdf import PdfReader  # type: ignore

    reader = PdfReader(str(path))
    ext.text = "\n\f".join((p.extract_text() or "") for p in reader.pages)
    ext.method = "pypdf"


def extract_pandoc(path: Path, ext: Extraction) -> None:
    if not shutil.which("pandoc"):
        raise RuntimeError("pandoc não instalado: converta o arquivo para .docx ou .pdf")
    proc = subprocess.run(["pandoc", str(path), "-t", "plain", "--wrap=none"], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[-300:])
    ext.text, ext.method = proc.stdout, "pandoc"


def extract(path: str | Path) -> Extraction:
    p = Path(path)
    ext = Extraction(path=str(p))
    suf = p.suffix.lower()
    try:
        if suf == ".docx":
            extract_docx(p, ext)
        elif suf == ".doc":
            extract_doc(p, ext)
        elif suf == ".pdf":
            extract_pdf(p, ext)
        elif suf in (".md", ".txt"):
            ext.text, ext.method = p.read_text(encoding="utf-8", errors="replace"), "texto"
        elif suf in (".odt", ".rtf", ".html", ".htm"):
            extract_pandoc(p, ext)
        else:
            raise ValueError(f"formato não suportado: {suf}")
    except Exception as e:  # noqa: BLE001 - relatar qualquer falha de leitura ao usuário
        ext.ok, ext.error = False, f"{type(e).__name__}: {e}"
    ext.text = re.sub(r"[ \t]+\n", "\n", ext.text)
    ext.text = re.sub(r"\n{3,}", "\n\n", ext.text).strip()
    ext.words = len(re.findall(r"\w+", ext.text))
    if ext.ok and suf == ".pdf" and ext.words < 30:
        ext.ok, ext.error = False, "PDF sem texto (provavelmente digitalizado): leia com o leitor multimodal e salve como .txt"
    return ext


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    e = extract(sys.argv[1])
    if "--json" in sys.argv:
        print(json.dumps(asdict(e), ensure_ascii=False, indent=2))
    else:
        print(e.text if e.ok else f"ERRO: {e.error}")
    sys.exit(0 if e.ok else 1)
