"""Integration tests for Ruff build and version verification."""

from __future__ import annotations

from ate.ruff import RUFF_TAG, get_ruff_version

from .conftest import RUFF_DIR, skip_no_ruff


class TestRuffBuild:
    @skip_no_ruff
    def test_version_matches_tag(self) -> None:
        """Pinned Ruff reports the expected version."""
        version = get_ruff_version(RUFF_DIR)
        assert version == RUFF_TAG

    @skip_no_ruff
    def test_binary_is_executable(self) -> None:
        """Ruff binary exists and is an actual executable file."""
        from .conftest import RUFF_BINARY

        assert RUFF_BINARY.exists()
        assert RUFF_BINARY.stat().st_size > 0
