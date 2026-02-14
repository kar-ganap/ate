"""Tests for ate CLI run commands."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from ate.cli import app

runner = CliRunner()


class TestRunPreflight:
    def test_all_clear(self) -> None:
        with patch("ate.cli.preflight_check", return_value=[]):
            result = runner.invoke(app, ["run", "preflight"])
        assert result.exit_code == 0
        assert "passed" in result.output.lower()

    def test_issues_found(self) -> None:
        with patch("ate.cli.preflight_check", return_value=["binary not found"]):
            result = runner.invoke(app, ["run", "preflight"])
        assert result.exit_code == 1


class TestRunStatus:
    def test_no_transcripts(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        with patch("ate.cli.DATA_DIR", tmp_path):
            result = runner.invoke(app, ["run", "status"])
        assert result.exit_code == 0
        assert "no" in result.output.lower() or "pending" in result.output.lower()
