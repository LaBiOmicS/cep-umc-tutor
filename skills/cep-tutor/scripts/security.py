"""Higienização Unicode e varredura de injeção de instruções nos documentos do protocolo.

Padrões adaptados do academic-peer-review e do congress-abstract-review (security.py), com a tag de delimitação deste
plugin e padrões em português dirigidos ao tutor ou ao CEP.
"""

from __future__ import annotations

import re
from typing import Any

UNTRUSTED_TAG = "UNTRUSTED_PROTOCOL_CONTENT"

# \x0c (quebra de página do pdftotext) é inofensivo e fica de fora.
INVISIBLE_AND_BIDI_REGEX = re.compile(
    r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff\x00-\x08\x0b\x0e-\x1f\x7f\U000e0000-\U000e007f]"
)

PROMPT_INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "instruction_override",
        re.compile(
            r"\b(?:ignore\s+(?:all\s+)?(?:previous|prior|above|system)\s+instructions|disregard\s+(?:all\s+)?(?:previous|prior)\s+instructions|"
            r"ignor[ea]\s+(?:todas\s+)?as\s+instruções\s+(?:anteriores|acima)|desconsidere\s+(?:todas\s+)?as\s+instruções)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "reviewer_verdict_manipulation",
        re.compile(
            r"\b(?:if\s+you\s+are\s+an?\s+(?:AI|LLM|language\s+model|automated)\s+(?:reviewer|tutor)|"
            r"(?:se\s+você\s+(?:é|for)\s+(?:uma?\s+)?(?:IA|inteligência\s+artificial|modelo\s+de\s+linguagem|tutor|avaliador\s+automático))|"
            r"(?:não\s+(?:aponte|mencione|liste)\s+(?:nenhum|nenhuma|problemas|pendências))|"
            r"(?:considere\s+(?:este|o)\s+(?:protocolo|projeto)\s+(?:aprovado|sem\s+pendências))|"
            r"(?:dê|faça)\s+(?:uma\s+)?(?:avaliação|revisão|parecer)\s+positiv[ao])\b",
            re.IGNORECASE,
        ),
    ),
    (
        "hidden_text_latex_or_css",
        re.compile(
            r"(?:\\textcolor\s*\{\s*white\s*\}|\\color\s*\{\s*white\s*\}|font-size\s*:\s*0(?:\.0+)?(?:px|pt|em)|opacity\s*:\s*0(?:\.0+)?\b|display\s*:\s*none)",
            re.IGNORECASE,
        ),
    ),
    (
        "delimiter_or_system_tag_spoofing",
        re.compile(
            r"(?:<\s*/?\s*UNTRUSTED_[A-Z_]+_CONTENT\s*/?\s*>|<\s*/?\s*SYSTEM_INSTRUCTION\s*>|<\s*\|im_start\|\s*>|<\s*\|endoftext\|\s*>)",
            re.IGNORECASE,
        ),
    ),
]


def sanitize_and_scan(text: str) -> tuple[str, dict[str, Any]]:
    """Remove caracteres invisíveis/bidi, neutraliza tags de delimitação e procura injeção de instruções."""
    invisible_hits = INVISIBLE_AND_BIDI_REGEX.findall(text)
    cleaned = INVISIBLE_AND_BIDI_REGEX.sub("", text)
    cleaned = re.sub(r"<\s*/?\s*UNTRUSTED_[A-Z_]+_CONTENT\s*/?\s*>", "[TAG_REMOVIDA]", cleaned, flags=re.IGNORECASE)
    findings: list[dict[str, str]] = []
    smuggled = "".join(chr(ord(ch) - 0xE0000) for ch in invisible_hits if 0xE0020 <= ord(ch) <= 0xE007E)
    if smuggled.strip():
        findings.append({"category": "unicode_tag_smuggling", "matched_text": " ".join(smuggled.split())[:120]})
    for category, pat in PROMPT_INJECTION_PATTERNS:
        for m in pat.finditer(text):
            findings.append({"category": category, "matched_text": " ".join(m.group(0).split())[:120]})
    return cleaned, {
        "invisible_or_bidi_chars_stripped": len(invisible_hits),
        "suspicious_prompt_injection_count": len(findings),
        "suspicious_patterns": findings[:15],
        "is_clean": len(findings) == 0 and len(invisible_hits) < 20,
    }
