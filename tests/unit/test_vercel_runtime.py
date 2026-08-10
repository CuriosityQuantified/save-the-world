"""Regression tests for the Vercel deployment runtime contract."""

import tempfile
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from utils.media import ensure_media_directories
from utils.runtime_paths import (
    get_leaderboard_db_path,
    get_media_public_root,
    get_runtime_root,
)


def test_vercel_runtime_uses_writable_configured_directory(monkeypatch, tmp_path):
    runtime_root = tmp_path / "runtime"
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("SAVE_THE_WORLD_RUNTIME_DIR", str(runtime_root))

    assert get_runtime_root() == str(runtime_root)
    assert get_media_public_root() == str(runtime_root / "public" / "media")
    assert get_leaderboard_db_path() == str(runtime_root / "leaderboard.db")

    ensure_media_directories()

    assert (runtime_root / "public" / "media" / "videos").is_dir()
    assert (runtime_root / "public" / "media" / "audio").is_dir()


def test_vercel_runtime_defaults_to_system_temp(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("SAVE_THE_WORLD_RUNTIME_DIR", raising=False)
    monkeypatch.delenv("LEADERBOARD_DB_PATH", raising=False)
    monkeypatch.delenv("PROJECT_ROOT_OVERRIDE", raising=False)

    runtime_root = Path(get_runtime_root())

    assert runtime_root == Path(tempfile.gettempdir()) / "save-the-world"
    assert Path(get_media_public_root()) == runtime_root / "public" / "media"
    assert Path(get_leaderboard_db_path()) == runtime_root / "leaderboard.db"


def test_local_runtime_preserves_project_root_behavior(monkeypatch, tmp_path):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("SAVE_THE_WORLD_RUNTIME_DIR", raising=False)
    monkeypatch.delenv("LEADERBOARD_DB_PATH", raising=False)
    monkeypatch.setenv("PROJECT_ROOT_OVERRIDE", str(tmp_path))

    assert get_runtime_root() == str(tmp_path)
    assert get_leaderboard_db_path() == str(tmp_path / "leaderboard.db")

    monkeypatch.setenv("LEADERBOARD_DB_PATH", ":memory:")
    assert get_leaderboard_db_path() == ":memory:"


def test_init_services_creates_nested_leaderboard_parent(monkeypatch, tmp_path):
    db_path = tmp_path / "nested" / "storage" / "leaderboard.db"
    monkeypatch.setenv("LEADERBOARD_DB_PATH", str(db_path))
    monkeypatch.delenv("VERCEL", raising=False)

    from api.app import init_services
    from api.routes import router

    init_services()
    try:
        assert db_path.is_file()
    finally:
        getattr(router, "leaderboard_service").close()


def test_vercel_api_prefix_reaches_backend_routes(monkeypatch):
    """The legacy Vercel catch-all forwards /api/* without stripping it."""
    from api.app import app
    from api.routes import router

    service = SimpleNamespace(
        state_service=SimpleNamespace(list_simulations=lambda: []),
    )
    monkeypatch.setattr(router, "simulation_service", service, raising=False)

    response = TestClient(app).get("/api/simulations")

    assert response.status_code == 200
    assert response.json() == []


def test_media_mounts_precede_ui_catchall():
    """The / mount must not shadow generated media mounts."""
    from api.app import app
    from starlette.routing import Mount

    mount_names = [route.name for route in app.routes if isinstance(route, Mount)]

    assert mount_names.index("media_audio") < mount_names.index("ui")
    assert mount_names.index("media_videos") < mount_names.index("ui")
