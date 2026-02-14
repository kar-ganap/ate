"""Tests for bug reproduction module."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from ate.scoring.reproduction import (
    REPRO_CASES,
    check_convergence_failure,
    check_has_diagnostic,
    check_has_syntax_error,
    check_outer_flagged,
    check_range_format_bug,
    is_fixed,
    run_repro,
    setup_repro,
)

PRIMARY_BUG_IDS = [20945, 18654, 7847, 4384, 19301, 22221, 22528, 22494]


class TestReproCases:
    def test_all_primary_bugs_present(self) -> None:
        for bug_id in PRIMARY_BUG_IDS:
            assert bug_id in REPRO_CASES, f"Bug #{bug_id} missing from REPRO_CASES"

    def test_repro_case_count(self) -> None:
        assert len(REPRO_CASES) == 8

    def test_each_case_has_required_fields(self) -> None:
        for bug_id, case in REPRO_CASES.items():
            assert case.bug_id == bug_id
            assert len(case.code) > 0
            assert len(case.check_fn) > 0


class TestSetupRepro:
    def test_writes_code_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        case = REPRO_CASES[20945]
        target = setup_repro(case, tmp_path)
        assert target.exists()
        assert target.read_text() == case.code

    def test_writes_extra_files(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        case = REPRO_CASES[22221]  # Has extra_files (package structure)
        setup_repro(case, tmp_path)
        for rel_path in case.extra_files:
            assert (tmp_path / rel_path).exists()

    def test_writes_config(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        case = REPRO_CASES[4384]  # Has ruff.toml config
        setup_repro(case, tmp_path)
        config_path = tmp_path / "ruff.toml"
        assert config_path.exists()
        assert "mccabe" in config_path.read_text()

    def test_custom_filename(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        case = REPRO_CASES[22221]  # Uses foo/__init__.py
        target = setup_repro(case, tmp_path)
        assert target.name == "__init__.py"
        assert "foo" in str(target)


class TestCheckFunctions:
    def test_check_has_diagnostic_positive(self) -> None:
        result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="repro.py:1:1: FAST001 ...\n", stderr=""
        )
        case = REPRO_CASES[20945]
        assert check_has_diagnostic(result, case) is True

    def test_check_has_diagnostic_negative(self) -> None:
        result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        case = REPRO_CASES[20945]
        assert check_has_diagnostic(result, case) is False

    def test_check_outer_flagged_positive(self) -> None:
        result = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="repro.py:1:1: C901 `wrapper` is too complex (5 > 3)\n",
            stderr="",
        )
        case = REPRO_CASES[4384]
        assert check_outer_flagged(result, case) is True

    def test_check_outer_flagged_negative(self) -> None:
        result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        case = REPRO_CASES[4384]
        assert check_outer_flagged(result, case) is False

    def test_check_has_syntax_error_positive(self) -> None:
        result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="SyntaxError: invalid syntax", stderr=""
        )
        case = REPRO_CASES[19301]
        assert check_has_syntax_error(result, case) is True

    def test_check_has_syntax_error_in_stderr(self) -> None:
        result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="syntax error found"
        )
        case = REPRO_CASES[19301]
        assert check_has_syntax_error(result, case) is True

    def test_check_has_syntax_error_negative(self) -> None:
        result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="All checks passed", stderr=""
        )
        case = REPRO_CASES[19301]
        assert check_has_syntax_error(result, case) is False

    def test_check_convergence_failure_positive(self) -> None:
        result = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Fix did not converge after 100 iterations",
        )
        case = REPRO_CASES[22221]
        assert check_convergence_failure(result, case) is True

    def test_check_convergence_failure_negative(self) -> None:
        result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Fixed 1 error", stderr=""
        )
        case = REPRO_CASES[22221]
        assert check_convergence_failure(result, case) is False

    def test_check_range_format_bug_positive(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        target = tmp_path / "repro.py"
        target.write_text("class Foo:\n    x=1;x=2\n")
        result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        case = REPRO_CASES[22494]
        assert check_range_format_bug(result, case, file_path=target) is True

    def test_check_range_format_bug_negative(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        target = tmp_path / "repro.py"
        target.write_text("class Foo:\n    x=1\n    x=2\n")
        result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        case = REPRO_CASES[22494]
        assert check_range_format_bug(result, case, file_path=target) is False

    def test_check_range_format_bug_no_path(self) -> None:
        result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        case = REPRO_CASES[22494]
        assert check_range_format_bug(result, case) is False


class TestRunRepro:
    def test_returns_tuple(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="FAST001 error\n", stderr=""
        )
        with patch("ate.scoring.reproduction.subprocess.run", return_value=mock_result):
            reproduced, details = run_repro(20945, tmp_path)
        assert isinstance(reproduced, bool)
        assert isinstance(details, str)

    def test_reproduced_true(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="repro.py:1:1: FAST001 ...\n", stderr=""
        )
        with patch("ate.scoring.reproduction.subprocess.run", return_value=mock_result):
            reproduced, _details = run_repro(20945, tmp_path)
        assert reproduced is True


class TestIsFixed:
    def test_is_fixed_when_not_reproduced(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        with patch("ate.scoring.reproduction.subprocess.run", return_value=mock_result):
            assert is_fixed(20945, tmp_path) is True

    def test_not_fixed_when_reproduced(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="FAST001 error\n", stderr=""
        )
        with patch("ate.scoring.reproduction.subprocess.run", return_value=mock_result):
            assert is_fixed(20945, tmp_path) is False
