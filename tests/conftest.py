from __future__ import annotations

import importlib
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli_script(monkeypatch: pytest.MonkeyPatch, relative_script_path: str, argv: list[str]) -> dict[str, Any]:
    """Execute a repository script with controlled argv and import paths."""
    script_path = PROJECT_ROOT / relative_script_path
    monkeypatch.chdir(PROJECT_ROOT)
    monkeypatch.syspath_prepend(str(PROJECT_ROOT))
    monkeypatch.syspath_prepend(str(script_path.parent))
    monkeypatch.setattr(sys, "argv", [script_path.name, *argv])
    importlib.invalidate_caches()
    return runpy.run_path(str(script_path), run_name="__main__")


@pytest.fixture(autouse=True)
def block_network_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail fast if a test accidentally performs a real HTTP request."""

    def _raise_for_network(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Tests must not perform real network calls.")

    monkeypatch.setattr(requests.sessions.Session, "request", _raise_for_network)
    monkeypatch.setattr(requests, "get", _raise_for_network)
    monkeypatch.setattr(requests, "head", _raise_for_network)

