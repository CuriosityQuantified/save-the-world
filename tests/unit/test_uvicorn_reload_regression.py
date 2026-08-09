"""
Regression tests for issue #21: main.py called
``uvicorn.run("api.app:app", reload=True, ...)`` unconditionally.

In production ``reload=True`` makes uvicorn spawn a file-system watcher over the
whole project tree and restart workers on any change, wasting CPU, breaking
graceful shutdown, and interfering with container/PaaS restart policies. The fix
gates reload on the ``RELOAD`` env var, defaulting OFF, via the pure importable
helper ``main.resolve_reload()``.

These tests are hermetic: stdlib only, no network, no server start. Importing
``main`` is safe because ``uvicorn.run`` lives under ``if __name__ == "__main__"``
and ``resolve_reload`` is a plain module-level function with no side effects.
"""
import re
from pathlib import Path

import pytest

import main


REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_PY = REPO_ROOT / "main.py"
ENV_EXAMPLE = REPO_ROOT / "env.example"


# ---------------------------------------------------------------------------
# Behavioural tests: resolve_reload() env semantics
# ---------------------------------------------------------------------------

def test_reload_defaults_off_when_unset(monkeypatch):
    """Core production-safety fix: unset RELOAD => reload disabled."""
    monkeypatch.delenv("RELOAD", raising=False)
    assert main.resolve_reload() is False


@pytest.mark.parametrize("value", ["true", "True", "TRUE", "tRuE"])
def test_reload_true_variants_enable(monkeypatch, value):
    """Case-insensitive "true" is the only thing that enables reload."""
    monkeypatch.setenv("RELOAD", value)
    assert main.resolve_reload() is True


@pytest.mark.parametrize("value", ["false", "False", "0", "", "yes", "1", "on", "no"])
def test_reload_non_true_values_stay_off(monkeypatch, value):
    """Anything that is not exactly (case-insensitively) "true" => disabled."""
    monkeypatch.setenv("RELOAD", value)
    assert main.resolve_reload() is False


def test_resolve_reload_returns_bool(monkeypatch):
    """Guard against accidentally returning a truthy string instead of a bool."""
    monkeypatch.setenv("RELOAD", "true")
    assert isinstance(main.resolve_reload(), bool)
    monkeypatch.setenv("RELOAD", "false")
    assert isinstance(main.resolve_reload(), bool)


# ---------------------------------------------------------------------------
# Static source guards: the hardcoded reload=True never returns
# ---------------------------------------------------------------------------

def test_main_source_has_no_hardcoded_reload_true():
    source = MAIN_PY.read_text()
    assert "reload=True" not in source, (
        "main.py must not hardcode reload=True (issue #21): it forces the "
        "uvicorn file-system watcher on in production."
    )


def test_uvicorn_run_wired_to_resolver():
    source = MAIN_PY.read_text()
    assert "reload=resolve_reload()" in source, (
        "uvicorn.run must pass reload=resolve_reload() so the RELOAD env var "
        "gates auto-reload."
    )


def test_env_example_documents_reload():
    """The RELOAD knob must stay discoverable in env.example."""
    assert ENV_EXAMPLE.exists(), f"Missing env.example: {ENV_EXAMPLE}"
    documented = any(
        re.match(r"^\s*RELOAD\s*=", line)
        for line in ENV_EXAMPLE.read_text().splitlines()
    )
    assert documented, "env.example must document the RELOAD variable."
