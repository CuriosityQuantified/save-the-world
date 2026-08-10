"""
Regression tests for issue #25 ("[16] `print()` debugging statements bypass
structured logging").

The original report cited seven ``print()`` calls in
``services/media_service.py`` (lines 643, 659, 670, 679, 681, 684, 687) inside
``generate_media_for_turn``. ``print()`` bypasses the configured ``logging``
system, ignores log levels, and is invisible to log aggregation.

Finding: that entire method (and all seven ``print()`` calls) was already
deleted by fix #18 (commit 1b7a376 / PR #40), so the module already satisfies
#25. The #18 regression only asserts the *method* is gone -- nothing guards the
acceptance criterion of #25 itself (no ``print()`` bypassing structured
logging). These tests are that missing recurrence guard: they will fail the
moment any ``print(...)`` is reintroduced into ``services/media_service.py``.

We parse the module source with the stdlib ``ast`` module rather than grepping
for the substring ``"print"`` so that occurrences inside strings, comments, or
identifiers like ``pprint``/``fingerprint`` never produce false positives.
"""
import ast
import logging
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MEDIA_SERVICE_PY = REPO_ROOT / "services" / "media_service.py"


def _print_call_line_numbers(source: str) -> list[int]:
    """Return the line numbers of every bare ``print(...)`` call in *source*.

    Only ``ast.Call`` nodes whose callable is the built-in name ``print`` are
    counted, so string/comment occurrences of the word "print" are ignored.
    """
    tree = ast.parse(source)
    lines: list[int] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ):
            lines.append(node.lineno)
    return sorted(lines)


class TestNoPrintInMediaService:
    """Lock in that media_service.py logs via ``logging``, never ``print()``."""

    def test_no_print_calls_in_media_service(self):
        """Zero ``print(...)`` calls may exist in services/media_service.py."""
        source = MEDIA_SERVICE_PY.read_text()
        offending = _print_call_line_numbers(source)
        assert offending == [], (
            "services/media_service.py must not use print() (issue #25); "
            "print() bypasses structured logging. Found print() calls at "
            f"line(s): {offending}. Use logger.info()/error()/debug() instead."
        )

    def test_module_configures_module_level_logger(self):
        """Positive control: the module wires up a stdlib ``logging`` logger."""
        source = MEDIA_SERVICE_PY.read_text()
        assert "logging.getLogger(__name__)" in source, (
            "services/media_service.py must configure a module-level logger via "
            "logging.getLogger(__name__) so structured logging is available."
        )

    def test_logger_object_is_a_logging_logger(self):
        """The imported ``logger`` really is a ``logging.Logger`` instance."""
        from services import media_service

        assert isinstance(media_service.logger, logging.Logger), (
            "services.media_service.logger must be a logging.Logger instance."
        )
