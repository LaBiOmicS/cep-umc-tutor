# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Carrega as bases de conhecimento do plugin (Trilha A e Trilha B) e as consulta por ID.

- Trilha A (`base-conhecimento/`): requisitos do CEP-UMC com IDs estáveis (PROJ-, TCLE-, TAI-...).
  A severidade vem da linha do requisito; quando a linha não tem, vem do checklist consolidado (16);
  quando nenhum dos dois tem, fica `PENDÊNCIA` com `severidade_inferida: true`.
- Trilha B (`base-academica/`): sugestões de metodologia, estatística e escrita (SUG-MET-, SUG-EST-, SUG-ESC-),
  com núcleo comum e nível mínimo.

Uso: kb.py stats | kb.py show ID [ID...] | kb.py search TERMO
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

PLUGIN_ROOT = Path(os.environ.get("CEP_TUTOR_ROOT") or Path(__file__).resolve().parents[3])
KB_DIR = PLUGIN_ROOT / "base-conhecimento"
ACAD_DIR = PLUGIN_ROOT / "base-academica"

SEVERIDADES = ("BLOQUEANTE", "PENDÊNCIA", "RECOMENDAÇÃO")
SEV_ORDEM = {s: i for i, s in enumerate(SEVERIDADES)}
NIVEIS = ("graduacao", "especializacao", "mestrado", "doutorado", "docente")
NIVEL_ORDEM = {n: i for i, n in enumerate(NIVEIS)}

REQ_ID = re.compile(
    r"(?:GER-\d{2}|PROJ-[GNEPCMRB]\d{2}|TCLE-[FC]\d{2}|TCLEV-\d{2}|TALE-[TR]?\d{2}|AMOS-\d{2}|DISP-C?\d{2}|TAI-\d{2}"
    r"|ANU-\d{2}|PB-[USD]\d{2}|RESP-\d{2}|EMD-\d{2}|REC-\d{2}|DIR-\d{2})"
)
SUG_ID = re.compile(r"SUG-(?:MET|EST|ESC)-\d{2}")
DISC_ID = re.compile(r"D\d{1,2}")
ROW = re.compile(r"^\|\s*(?P<id>[A-Z][A-Z0-9-]+)\s*\|(?P<rest>.*)\|\s*$")
SEV_TAG = re.compile(r"\[(BLOQUEANTE|PENDÊNCIA|RECOMENDAÇÃO)\]")


@dataclass
class Item:
    id: str
    trilha: str  # "A" ou "B"
    arquivo: str
    secao: str
    texto: str
    severidade: str | None = None
    severidade_inferida: bool = False
    nucleo_comum: bool | None = None
    nivel_minimo: str | None = None
    fonte: str | None = None
    extra: dict = field(default_factory=dict)


def _plain(md: str) -> str:
    md = re.sub(r"\*\*|__|`", "", md)
    md = re.sub(r"\s+", " ", md)
    return md.strip()


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4 :].lstrip("\n")
    return text


def _cells(rest: str) -> list[str]:
    return [c.strip() for c in rest.split("|")]


def _iter_rows(path: Path):
    secao = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            secao = line.lstrip("#").strip()
            continue
        m = ROW.match(line)
        if m:
            yield secao, m.group("id"), _cells(m.group("rest")), line


def expand_id_list(spec: str) -> list[str]:
    """'PROJ-R01 a R05' -> R01..R05; 'PROJ-M04/M05' -> M04, M05; 'PROJ-N06/TALE-02' -> ambos."""
    out: list[str] = []
    for chunk in spec.split("/"):
        chunk = chunk.strip()
        rng = re.match(r"^(?P<a>[A-Z][A-Z0-9-]*?)(?P<n1>\d{2}) a (?P<b>[A-Z]*)(?P<n2>\d{2})$", chunk)
        if rng:
            prefix = rng.group("a")
            for n in range(int(rng.group("n1")), int(rng.group("n2")) + 1):
                out.append(f"{prefix}{n:02d}")
            continue
        if REQ_ID.fullmatch(chunk):
            out.append(chunk)
        elif out and re.fullmatch(r"[A-Z]?\d{2}", chunk):
            prev = out[-1]
            head = re.match(r"^(.*?)([A-Z]?\d{2})$", prev).group(1)
            if re.fullmatch(r"\d{2}", chunk):  # 'F04' herda a letra
                head = re.match(r"^(.*?)(\d{2})$", prev).group(1)
            cand = head + chunk
            if REQ_ID.fullmatch(cand):
                out.append(cand)
    return out


def _checklist_severities() -> dict[str, str]:
    path = KB_DIR / "16-checklist-pre-submissao.md"
    sev: dict[str, str] = {}
    if not path.exists():
        return sev
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^- \[ \] (?P<ids>.+?) — (?P<txt>.*)$", line)
        if not m:
            continue
        tag = SEV_TAG.findall(line)
        if not tag:
            continue
        for rid in expand_id_list(m.group("ids")):
            sev.setdefault(rid, tag[0])
    return sev


def _checklist_items() -> dict[str, Item]:
    """GER-xx só existem no checklist (16)."""
    path = KB_DIR / "16-checklist-pre-submissao.md"
    items: dict[str, Item] = {}
    secao = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            secao = line.lstrip("#").strip()
        m = re.match(r"^- \[ \] (?P<id>GER-\d{2}) — (?P<txt>.*)$", line)
        if m:
            tag = SEV_TAG.findall(line)
            txt = re.sub(r"·.*$", "", m.group("txt"))
            items[m.group("id")] = Item(m.group("id"), "A", path.name, secao, _plain(txt), tag[0] if tag else None)
    return items


@lru_cache(maxsize=1)
def load_requirements() -> dict[str, Item]:
    items: dict[str, Item] = {}
    for path in sorted(KB_DIR.glob("[0-9][0-9]-*.md")):
        if path.name.startswith(("15-", "16-", "17-", "19-")):
            continue  # triagem, checklist, padrões e guia citam IDs, não os definem
        for secao, rid, cells, line in _iter_rows(path):
            if not REQ_ID.fullmatch(rid) or rid in items:
                continue
            tags = SEV_TAG.findall(line)
            texto = " — ".join(c for c in cells if c and not SEV_TAG.fullmatch(c))
            items[rid] = Item(rid, "A", path.name, secao, _plain(texto), tags[-1] if tags else None)
    for rid, it in _checklist_items().items():
        items.setdefault(rid, it)
    sev16 = _checklist_severities()
    for rid, it in items.items():
        if it.severidade is None:
            if rid in sev16:
                it.severidade = sev16[rid]
            elif rid.startswith("DIR-"):
                it.severidade = None  # direitos: referência, não requisito
            else:
                it.severidade, it.severidade_inferida = "PENDÊNCIA", True
    return items


@lru_cache(maxsize=1)
def load_discrepancies() -> dict[str, Item]:
    path = KB_DIR / "00-fontes-e-discrepancias.md"
    out: dict[str, Item] = {}
    if path.exists():
        for secao, rid, cells, _ in _iter_rows(path):
            if DISC_ID.fullmatch(rid):
                out[rid] = Item(rid, "A", path.name, secao, _plain(" — ".join(cells)), None)
    return out


def _bool(cell: str) -> bool | None:
    c = _plain(cell).lower()
    if c in ("sim", "s", "yes"):
        return True
    if c in ("não", "nao", "n", "no"):
        return False
    return None


def _nivel(cell: str) -> str | None:
    c = _plain(cell).lower()
    c = c.replace("ç", "c").replace("ã", "a").replace("á", "a").replace("ê", "e")
    for n in NIVEIS:
        if c.startswith(n[:5]):
            return n
    return None


@lru_cache(maxsize=1)
def load_suggestions() -> dict[str, Item]:
    """Tabelas da base acadêmica: | ID | Sugestão | Núcleo comum | Nível mínimo | Por que importa | Fonte |"""
    items: dict[str, Item] = {}
    if not ACAD_DIR.exists():
        return items
    for path in sorted(ACAD_DIR.glob("[0-9][0-9]-*.md")):
        for secao, sid, cells, _ in _iter_rows(path):
            if not SUG_ID.fullmatch(sid) or len(cells) < 5:
                continue
            items[sid] = Item(
                sid, "B", path.name, secao, _plain(cells[0]),
                nucleo_comum=_bool(cells[1]), nivel_minimo=_nivel(cells[2]),
                fonte=_plain(cells[4]) if len(cells) > 4 else None,
                extra={"por_que": _plain(cells[3])},
            )
    return items


def get(item_id: str) -> Item | None:
    return load_requirements().get(item_id) or load_suggestions().get(item_id) or load_discrepancies().get(item_id)


def kb_file(name: str, academic: bool = False) -> str:
    base = ACAD_DIR if academic else KB_DIR
    return strip_frontmatter((base / name).read_text(encoding="utf-8"))


def search(term: str) -> list[Item]:
    t = term.lower()
    pool = list(load_requirements().values()) + list(load_suggestions().values()) + list(load_discrepancies().values())
    return [it for it in pool if t in it.texto.lower() or t in it.id.lower() or t in it.secao.lower()]


def stats() -> dict:
    req = load_requirements()
    sug = load_suggestions()
    sev: dict[str, int] = {}
    for it in req.values():
        sev[str(it.severidade)] = sev.get(str(it.severidade), 0) + 1
    return {
        "kb_dir": str(KB_DIR),
        "requisitos": len(req),
        "por_severidade": sev,
        "severidade_inferida": sum(1 for it in req.values() if it.severidade_inferida),
        "discrepancias": len(load_discrepancies()),
        "sugestoes": len(sug),
        "sugestoes_nucleo_comum": sum(1 for it in sug.values() if it.nucleo_comum),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats")
    s = sub.add_parser("show")
    s.add_argument("ids", nargs="+")
    q = sub.add_parser("search")
    q.add_argument("term")
    a = ap.parse_args(argv)
    if a.cmd == "stats":
        print(json.dumps(stats(), ensure_ascii=False, indent=2))
    elif a.cmd == "show":
        missing = 0
        for i in a.ids:
            it = get(i)
            if it is None:
                print(f"{i}: não encontrado", file=sys.stderr)
                missing += 1
            else:
                print(json.dumps(asdict(it), ensure_ascii=False, indent=2))
        return 1 if missing else 0
    else:
        for it in search(a.term):
            print(f"{it.id}\t[{it.severidade or it.nivel_minimo or '-'}]\t{it.arquivo}\t{it.texto[:140]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
