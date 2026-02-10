"""Tests for ate.ruff."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ate.ruff import (
    build_ruff,
    get_ruff_binary,
    get_ruff_version,
    run_cargo_test,
    run_ruff_check,
)

RUFF_DIR = Path("/fake/ruff")


class TestGetRuffBinary:
    def test_returns_debug_binary_path(self) -> None:
        binary = get_ruff_binary(RUFF_DIR)
        assert binary == RUFF_DIR / "target" / "debug" / "ruff"


class TestBuildRuff:
    @patch("ate.ruff.subprocess.run")
    def test_build_command(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        build_ruff(RUFF_DIR)
        mock_run.assert_called_once()
        args = mock_run.call_args
        assert args[0][0] == ["cargo", "build"]
        assert args[1]["cwd"] == RUFF_DIR

    @patch("ate.ruff.subprocess.run")
    def test_build_failure_raises(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        with pytest.raises(RuntimeError, match="cargo build failed"):
            build_ruff(RUFF_DIR)


class TestGetRuffVersion:
    @patch("ate.ruff.subprocess.run")
    def test_version_parsing(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="ruff 0.14.14\n",
        )
        version = get_ruff_version(RUFF_DIR)
        assert version == "0.14.14"

    @patch("ate.ruff.subprocess.run")
    def test_version_failure(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="not found")
        with pytest.raises(RuntimeError, match="Failed to get ruff version"):
            get_ruff_version(RUFF_DIR)


class TestRunRuffCheck:
    @patch("ate.ruff.subprocess.run")
    def test_check_with_rules(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="All checks passed!\n")
        result = run_ruff_check(
            ruff_dir=RUFF_DIR,
            target_file=Path("/tmp/test.py"),
            rules=["FAST001"],
        )
        args = mock_run.call_args[0][0]
        binary = str(get_ruff_binary(RUFF_DIR))
        assert args[0] == binary
        assert "check" in args
        assert "--select" in args
        assert "FAST001" in args
        assert result.returncode == 0

    @patch("ate.ruff.subprocess.run")
    def test_check_without_rules(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        run_ruff_check(
            ruff_dir=RUFF_DIR,
            target_file=Path("/tmp/test.py"),
        )
        args = mock_run.call_args[0][0]
        assert "--select" not in args

    @patch("ate.ruff.subprocess.run")
    def test_check_returns_result(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="test.py:1:1: F401 `os` imported but unused\n",
        )
        result = run_ruff_check(
            ruff_dir=RUFF_DIR,
            target_file=Path("/tmp/test.py"),
        )
        assert result.returncode == 1
        assert "F401" in result.stdout


class TestRunCargoTest:
    @patch("ate.ruff.subprocess.run")
    def test_cargo_test_all(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="test result: ok\n")
        result = run_cargo_test(RUFF_DIR)
        args = mock_run.call_args[0][0]
        assert args == ["cargo", "test"]
        assert result.returncode == 0

    @patch("ate.ruff.subprocess.run")
    def test_cargo_test_with_filter(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        run_cargo_test(RUFF_DIR, test_filter="fast001")
        args = mock_run.call_args[0][0]
        assert args == ["cargo", "test", "fast001"]

    @patch("ate.ruff.subprocess.run")
    def test_cargo_test_with_package(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        run_cargo_test(RUFF_DIR, package="ruff_linter")
        args = mock_run.call_args[0][0]
        assert "--package" in args
        assert "ruff_linter" in args
