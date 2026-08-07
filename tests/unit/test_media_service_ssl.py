"""
Regression tests for issue #11: SSL certificate verification was unconditionally
disabled in media_service.py's URL-fetch branch. These tests lock in that:
  - Default path (VERIFY_SSL unset / "true") does NOT disable verification.
  - Explicit opt-out (VERIFY_SSL=false) does disable verification.
"""
import os
import ssl
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_connector_captor():
    """Return a mock TCPConnector class and a list that captures ssl= kwargs."""
    seen_ssl = []

    class FakeConnector:
        def __init__(self, **kwargs):
            seen_ssl.append(kwargs.get("ssl", "NOT_SET"))

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        async def close(self):
            pass

    return FakeConnector, seen_ssl


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSSLVerificationDefault:
    """With VERIFY_SSL unset or 'true', certificate verification must be ON."""

    def _run_generate_video(self, env_override: dict):
        """
        Import (or reload) media_service with a patched environment and invoke
        the URL-fetch code path. We patch aiohttp.TCPConnector and
        aiohttp.ClientSession to avoid any real network call.
        """
        import importlib
        import services.media_service as ms_mod

        # Reload so VERIFY_SSL is re-evaluated at module level each time.
        with patch.dict(os.environ, env_override, clear=False):
            importlib.reload(ms_mod)
            verify_ssl = ms_mod.VERIFY_SSL
        return verify_ssl

    def test_verify_ssl_is_true_when_env_unset(self, monkeypatch):
        """VERIFY_SSL module constant must default to True when env var is absent."""
        monkeypatch.delenv("VERIFY_SSL", raising=False)
        import importlib
        import services.media_service as ms_mod
        importlib.reload(ms_mod)
        assert ms_mod.VERIFY_SSL is True

    def test_verify_ssl_is_true_when_env_is_true(self, monkeypatch):
        """VERIFY_SSL must be True when VERIFY_SSL='true'."""
        monkeypatch.setenv("VERIFY_SSL", "true")
        import importlib
        import services.media_service as ms_mod
        importlib.reload(ms_mod)
        assert ms_mod.VERIFY_SSL is True

    def test_verify_ssl_is_false_when_env_is_false(self, monkeypatch):
        """VERIFY_SSL must be False when VERIFY_SSL='false' (opt-out)."""
        monkeypatch.setenv("VERIFY_SSL", "false")
        import importlib
        import services.media_service as ms_mod
        importlib.reload(ms_mod)
        assert ms_mod.VERIFY_SSL is False


class TestSSLConnectorBehavior:
    """Assert that TCPConnector receives the correct ssl= argument."""

    def _patch_and_capture(self, verify_ssl_value: bool):
        """
        Monkeypatch VERIFY_SSL on the already-loaded module and run
        _fetch_video_from_url (or the inline code inside generate_video).
        We capture what ssl= argument TCPConnector was called with.
        """
        import asyncio
        import services.media_service as ms_mod

        captured = {}

        original_connector = __import__("aiohttp").TCPConnector

        class CapturingConnector:
            def __init__(self, **kwargs):
                captured["ssl"] = kwargs.get("ssl", "NOT_SET")

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def close(self):
                pass

        fake_response = AsyncMock()
        fake_response.status = 200
        fake_response.read = AsyncMock(return_value=b"fake_video_bytes")
        fake_response.__aenter__ = AsyncMock(return_value=fake_response)
        fake_response.__aexit__ = AsyncMock(return_value=False)

        fake_session = MagicMock()
        fake_session.get = MagicMock(return_value=fake_response)
        fake_session.__aenter__ = AsyncMock(return_value=fake_session)
        fake_session.__aexit__ = AsyncMock(return_value=False)

        fake_huggingface = MagicMock()
        fake_huggingface.generate_video = AsyncMock(
            return_value="https://example.com/video.mp4"
        )

        fake_r2 = MagicMock()
        fake_r2.upload_video = AsyncMock(return_value="https://r2.example.com/v.mp4")

        with (
            patch.object(ms_mod, "VERIFY_SSL", verify_ssl_value),
            patch("aiohttp.TCPConnector", CapturingConnector),
            patch("aiohttp.ClientSession", return_value=fake_session),
        ):
            svc = ms_mod.MediaService.__new__(ms_mod.MediaService)
            svc.huggingface_service = fake_huggingface
            svc.r2_service = fake_r2
            svc.logger = __import__("logging").getLogger("test")

            asyncio.get_event_loop().run_until_complete(
                svc.generate_video("test prompt", turn=1)
            )

        return captured

    def test_default_verify_ssl_does_not_disable_verification(self):
        """
        When VERIFY_SSL is True, the ssl= kwarg passed to TCPConnector must
        NOT be an ssl.SSLContext with check_hostname=False / CERT_NONE.
        Acceptable values: True, None, or a context with verification enabled.
        """
        captured = self._patch_and_capture(verify_ssl_value=True)
        ssl_arg = captured.get("ssl", "NOT_SET")
        # Must not be a broken SSLContext
        if isinstance(ssl_arg, ssl.SSLContext):
            assert ssl_arg.check_hostname is True, "check_hostname must remain True"
            assert ssl_arg.verify_mode != ssl.CERT_NONE, "verify_mode must not be CERT_NONE"
        else:
            # True or None — both are aiohttp defaults (verification on)
            assert ssl_arg in (True, None, "NOT_SET"), (
                f"Unexpected ssl= value when VERIFY_SSL=True: {ssl_arg!r}"
            )

    def test_opt_out_verify_ssl_disables_verification(self):
        """
        When VERIFY_SSL is False, the ssl= kwarg must produce a context with
        verification disabled (check_hostname=False, CERT_NONE).
        """
        captured = self._patch_and_capture(verify_ssl_value=False)
        ssl_arg = captured.get("ssl", "NOT_SET")
        assert isinstance(ssl_arg, ssl.SSLContext), (
            f"Expected an SSLContext when VERIFY_SSL=False, got {type(ssl_arg)}"
        )
        assert ssl_arg.check_hostname is False
        assert ssl_arg.verify_mode == ssl.CERT_NONE
