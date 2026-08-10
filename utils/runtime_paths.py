"""Filesystem paths that work in local and serverless runtimes.

Vercel Functions can read the deployed bundle but may only write to ``/tmp``.
Keep durable/static files under the project root locally, while directing
runtime-generated media and the ephemeral SQLite fallback to a writable
serverless directory.
"""

import os
import tempfile


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Kept as a public compatibility constant for existing diagnostics/tests.
PROJECT_ROOT = _PROJECT_ROOT


def get_project_root() -> str:
    """Return the project root, honoring the test-only override when present."""
    configured = os.getenv("PROJECT_ROOT_OVERRIDE")
    return os.path.abspath(os.path.expanduser(configured or _PROJECT_ROOT))


def get_runtime_root() -> str:
    """Return the directory used for files created while the app is running.

    ``SAVE_THE_WORLD_RUNTIME_DIR`` is useful for tests and for explicitly
    configured deployments. Vercel's only writable filesystem location is
    ``/tmp``; all other environments preserve the historical project-root
    behavior.
    """
    configured = os.getenv("SAVE_THE_WORLD_RUNTIME_DIR")
    if configured:
        return os.path.abspath(os.path.expanduser(configured))

    if os.getenv("VERCEL") == "1":
        return os.path.join(tempfile.gettempdir(), "save-the-world")

    return get_project_root()


def get_media_public_root() -> str:
    """Return the runtime directory backing ``/media`` URLs."""
    return os.path.join(get_runtime_root(), "public", "media")


def get_leaderboard_db_path() -> str:
    """Return the SQLite path, with an override for explicit storage config."""
    configured = os.getenv("LEADERBOARD_DB_PATH")
    if configured:
        return configured if configured == ":memory:" else os.path.abspath(os.path.expanduser(configured))
    return os.path.join(get_runtime_root(), "leaderboard.db")
