"""
Regression tests for issue #12: CORS wildcard + allow_credentials=True
misconfiguration.

Locks in that:
  - allow_origins defaults to ["http://localhost:3000"] (not wildcard) when
    CORS_ORIGINS env var is absent.
  - allow_origins is parsed from a comma-separated CORS_ORIGINS value.
  - allow_credentials is False (wildcard+credentials is a spec violation).
"""
import importlib
import os
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reload_app(monkeypatch, cors_origins_value=None):
    """
    Reload api.app under a controlled CORS_ORIGINS environment and return the
    module so callers can inspect _cors_origins and app.user_middleware.
    """
    if cors_origins_value is None:
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
    else:
        monkeypatch.setenv("CORS_ORIGINS", cors_origins_value)

    import api.app as app_mod
    importlib.reload(app_mod)
    return app_mod


def _cors_middleware_kwargs(app_mod):
    """
    Extract kwargs registered for CORSMiddleware from app.user_middleware.
    Returns a dict, or {} if not found.
    """
    from fastapi.middleware.cors import CORSMiddleware
    for mw in app_mod.app.user_middleware:
        # Starlette stores Middleware(cls, **kwargs) objects.
        if mw.cls is CORSMiddleware:
            return mw.kwargs
    return {}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCORSOriginsDefault:
    """When CORS_ORIGINS is unset, origins must default to localhost:3000."""

    def test_default_origins_not_wildcard(self, monkeypatch):
        """The default CORS origin list must NOT be the bare wildcard ['*']."""
        app_mod = _reload_app(monkeypatch)
        assert app_mod._cors_origins != ["*"], (
            "allow_origins must not be ['*'] — wildcard + credentials is a CORS spec violation"
        )

    def test_default_origins_is_localhost(self, monkeypatch):
        """The default CORS origin list must be ['http://localhost:3000']."""
        app_mod = _reload_app(monkeypatch)
        assert app_mod._cors_origins == ["http://localhost:3000"], (
            f"Expected ['http://localhost:3000'], got {app_mod._cors_origins!r}"
        )

    def test_middleware_origins_not_wildcard(self, monkeypatch):
        """CORSMiddleware registered on the app must not use the wildcard."""
        app_mod = _reload_app(monkeypatch)
        kwargs = _cors_middleware_kwargs(app_mod)
        assert kwargs.get("allow_origins") != ["*"]


class TestCORSOriginsEnvVar:
    """CORS_ORIGINS env var must be parsed as a comma-separated list."""

    def test_single_origin_from_env(self, monkeypatch):
        app_mod = _reload_app(monkeypatch, "https://prod.example.com")
        assert app_mod._cors_origins == ["https://prod.example.com"]

    def test_multiple_origins_from_env(self, monkeypatch):
        app_mod = _reload_app(
            monkeypatch, "https://app.example.com,https://api.example.com"
        )
        assert app_mod._cors_origins == [
            "https://app.example.com",
            "https://api.example.com",
        ]


class TestCORSCredentials:
    """allow_credentials must be False (wildcard + credentials is spec-invalid)."""

    def test_credentials_false_with_default_origins(self, monkeypatch):
        app_mod = _reload_app(monkeypatch)
        kwargs = _cors_middleware_kwargs(app_mod)
        assert kwargs.get("allow_credentials") is False, (
            f"allow_credentials must be False, got {kwargs.get('allow_credentials')!r}"
        )

    def test_credentials_false_with_explicit_origins(self, monkeypatch):
        app_mod = _reload_app(monkeypatch, "https://prod.example.com")
        kwargs = _cors_middleware_kwargs(app_mod)
        assert kwargs.get("allow_credentials") is False
