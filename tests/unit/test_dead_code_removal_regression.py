"""
Regression tests for issue #18: `generate_media_for_turn` was dead code
with three undefined attributes (`tts_service`, `state_service`, `notify_progress`).

These tests lock in that the dead method is absent while the surrounding
`MediaService` API remains available.
"""
from services.media_service import MediaService


class TestGenerateMediaForTurnRemoved:
    """Assert that removing the dead method leaves the service intact."""

    def test_generate_media_for_turn_removed_without_truncating_service(self):
        """The dead method is gone, while the final R2 helper remains available."""
        assert not hasattr(MediaService, "generate_media_for_turn"), (
            "generate_media_for_turn is dead code and must be deleted from MediaService"
        )
        assert hasattr(MediaService, "test_r2_upload_download"), (
            "deleting generate_media_for_turn must not remove neighboring methods"
        )
