"""Tests for ate CLI score commands."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from ate.cli import app

runner = CliRunner()


class TestScoreTier1:
    def test_no_patches_dir(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        with patch("ate.cli.DATA_DIR", tmp_path):
            result = runner.invoke(app, ["score", "tier1"])
        assert result.exit_code == 0
        assert "no patches" in result.output.lower()

    def test_dry_run_no_patches(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        patches_dir = tmp_path / "patches"
        patches_dir.mkdir()
        with patch("ate.cli.DATA_DIR", tmp_path):
            result = runner.invoke(app, ["score", "tier1", "--dry-run"])
        assert result.exit_code == 0
        assert "no patches" in result.output.lower()


class TestScoreTier2Scaffold:
    def test_generates_guides(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        with patch("ate.cli.DATA_DIR", tmp_path):
            result = runner.invoke(app, ["score", "tier2-scaffold"])
        assert result.exit_code == 0
        assert "generated" in result.output.lower()
        guides_dir = tmp_path / "scores" / "tier2" / "guides"
        assert guides_dir.exists()
        guides = list(guides_dir.glob("*-guide.md"))
        assert len(guides) == 8


class TestScoreStatus:
    def test_no_data(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        with patch("ate.cli.DATA_DIR", tmp_path):
            result = runner.invoke(app, ["score", "status"])
        assert result.exit_code == 0
        assert "scoring status" in result.output.lower()
        assert "0/" in result.output
