from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "skills" / "cep-tutor" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PROTOCOLO = FIXTURES / "protocolo_exemplo"
sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Testes herméticos: qualquer requisição HTTP falha."""

    def _blocked(*args, **kwargs):
        raise AssertionError("Acesso à rede durante os testes")

    monkeypatch.setattr(urllib.request, "urlopen", _blocked)
