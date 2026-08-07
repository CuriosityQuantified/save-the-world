"""
Regression tests for issue #13: GET /debug/media-check crashed with
NameError (Mount, StaticFiles not imported) and AttributeError (router.app).

Locks in:
  - The endpoint returns HTTP 200 without raising.
  - Response JSON contains checked_directories.videos, checked_directories.audio,
    found_files, and configured_static_mounts (with audio/video/ui entries).
"""
import importlib
import pytest
from fastapi.testclient import TestClient


def _make_client(monkeypatch, tmp_path):
    """
    Reload api.app and return a TestClient.  Use tmp_path so the endpoint's
    os.makedirs calls land in the temp tree, not in the repo working directory.
    """
    # Point PROJECT_ROOT at tmp_path so media dirs are created there.
    monkeypatch.setenv("PROJECT_ROOT_OVERRIDE", str(tmp_path))

    import api.app as app_mod
    importlib.reload(app_mod)

    return TestClient(app_mod.app)


class TestDebugMediaCheck:
    """GET /debug/media-check must return 200 with expected structure."""

    def test_returns_200(self, monkeypatch, tmp_path):
        client = _make_client(monkeypatch, tmp_path)
        response = client.get("/debug/media-check")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    def test_checked_directories_shape(self, monkeypatch, tmp_path):
        client = _make_client(monkeypatch, tmp_path)
        data = client.get("/debug/media-check").json()
        checked = data["checked_directories"]
        assert "videos" in checked, "checked_directories must contain 'videos'"
        assert "audio" in checked, "checked_directories must contain 'audio'"

    def test_found_files_present(self, monkeypatch, tmp_path):
        client = _make_client(monkeypatch, tmp_path)
        data = client.get("/debug/media-check").json()
        assert "found_files" in data, "Response must contain 'found_files'"

    def test_configured_static_mounts_audio(self, monkeypatch, tmp_path):
        client = _make_client(monkeypatch, tmp_path)
        data = client.get("/debug/media-check").json()
        mounts = data.get("configured_static_mounts", {})
        assert "audio" in mounts, (
            f"configured_static_mounts must contain 'audio'; got keys: {list(mounts)}"
        )
        assert mounts["audio"]["path"] == "/media/audio"

    def test_configured_static_mounts_video(self, monkeypatch, tmp_path):
        client = _make_client(monkeypatch, tmp_path)
        data = client.get("/debug/media-check").json()
        mounts = data.get("configured_static_mounts", {})
        assert "video" in mounts, (
            f"configured_static_mounts must contain 'video'; got keys: {list(mounts)}"
        )
        assert mounts["video"]["path"] == "/media/videos"

    def test_configured_static_mounts_ui(self, monkeypatch, tmp_path):
        client = _make_client(monkeypatch, tmp_path)
        data = client.get("/debug/media-check").json()
        mounts = data.get("configured_static_mounts", {})
        assert "ui" in mounts, (
            f"configured_static_mounts must contain 'ui'; got keys: {list(mounts)}"
        )

    def test_project_root_present(self, monkeypatch, tmp_path):
        client = _make_client(monkeypatch, tmp_path)
        data = client.get("/debug/media-check").json()
        assert "project_root" in data, "Response must contain 'project_root'"
