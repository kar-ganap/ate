"""Tests for Tier 1 automated scoring pipeline."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import patch

from ate.models import Tier1Score
from ate.scoring.tier1 import (
    apply_patch,
    check_tests_pass,
    extract_cost_and_time,
    rebuild_ruff,
    revert_ruff,
    score_bug,
)


def _ok_result() -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")


def _fail_result() -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=[], returncode=1, stdout="error", stderr="failed"
    )


class TestApplyPatch:
    def test_success(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        patch_file = tmp_path / "fix.patch"
        patch_file.write_text("diff content")
        with patch("ate.scoring.tier1.subprocess.run", return_value=_ok_result()):
            assert apply_patch(patch_file, tmp_path) is True

    def test_failure(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        patch_file = tmp_path / "bad.patch"
        patch_file.write_text("bad diff")
        with patch("ate.scoring.tier1.subprocess.run", return_value=_fail_result()):
            assert apply_patch(patch_file, tmp_path) is False

    def test_missing_patch(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        patch_file = tmp_path / "missing.patch"
        assert apply_patch(patch_file, tmp_path) is False


class TestRevertRuff:
    def test_calls_git_checkout(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        with patch("ate.scoring.tier1.subprocess.run", return_value=_ok_result()) as mock:
            revert_ruff(tmp_path)
        mock.assert_called_once()
        cmd = mock.call_args[0][0]
        assert "git" in cmd
        assert "checkout" in cmd


class TestRebuildRuff:
    def test_success(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        with patch("ate.scoring.tier1.subprocess.run", return_value=_ok_result()):
            assert rebuild_ruff(tmp_path) is True

    def test_failure(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        with patch("ate.scoring.tier1.subprocess.run", return_value=_fail_result()):
            assert rebuild_ruff(tmp_path) is False


class TestCheckTestsPass:
    def test_pass(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        with patch("ate.scoring.tier1.subprocess.run", return_value=_ok_result()):
            assert check_tests_pass(tmp_path) is True

    def test_fail(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        with patch("ate.scoring.tier1.subprocess.run", return_value=_fail_result()):
            assert check_tests_pass(tmp_path) is False


class TestExtractCostAndTime:
    def test_valid_metadata(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        meta_dir = tmp_path / "transcripts" / "treatment-1" / "bug-20945"
        meta_dir.mkdir(parents=True)
        meta = {
            "total_cost_usd": 0.42,
            "wall_clock_seconds": 300.0,
        }
        (meta_dir / "metadata.json").write_text(json.dumps(meta))
        cost, minutes = extract_cost_and_time(tmp_path, 1, 20945)
        assert cost == 0.42
        assert minutes == 5.0

    def test_missing_metadata(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        cost, minutes = extract_cost_and_time(tmp_path, 1, 20945)
        assert cost is None
        assert minutes is None

    def test_partial_metadata(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        meta_dir = tmp_path / "transcripts" / "treatment-0b" / "bug-7847"
        meta_dir.mkdir(parents=True)
        meta = {"total_cost_usd": 0.10}
        (meta_dir / "metadata.json").write_text(json.dumps(meta))
        cost, minutes = extract_cost_and_time(tmp_path, "0b", 7847)
        assert cost == 0.10
        assert minutes is None


class TestScoreBug:
    def test_full_pipeline_success(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        ruff_dir = tmp_path / "ruff"
        ruff_dir.mkdir()
        patches_dir = tmp_path / "patches"
        patch_dir = patches_dir / "treatment-1"
        patch_dir.mkdir(parents=True)
        (patch_dir / "bug-20945.patch").write_text("diff")
        data_dir = tmp_path / "data"

        with (
            patch("ate.scoring.tier1.apply_patch", return_value=True),
            patch("ate.scoring.tier1.rebuild_ruff", return_value=True),
            patch("ate.scoring.tier1.is_fixed", return_value=True),
            patch("ate.scoring.tier1.check_tests_pass", return_value=True),
            patch("ate.scoring.tier1.revert_ruff"),
            patch(
                "ate.scoring.tier1.extract_cost_and_time",
                return_value=(0.42, 5.0),
            ),
        ):
            score = score_bug(1, 20945, ruff_dir, patches_dir, data_dir)

        assert isinstance(score, Tier1Score)
        assert score.patch_applies is True
        assert score.existing_tests_pass is True
        assert score.reproduction_fixed is True
        assert score.no_regressions is True
        assert score.all_pass is True
        assert score.token_cost_usd == 0.42
        assert score.wall_clock_minutes == 5.0

    def test_missing_patch(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        ruff_dir = tmp_path / "ruff"
        ruff_dir.mkdir()
        patches_dir = tmp_path / "patches"
        patches_dir.mkdir()
        data_dir = tmp_path / "data"

        score = score_bug(1, 20945, ruff_dir, patches_dir, data_dir)
        assert score.patch_applies is False
        assert score.existing_tests_pass is False
        assert score.reproduction_fixed is False
        assert score.no_regressions is False

    def test_patch_fails(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        ruff_dir = tmp_path / "ruff"
        ruff_dir.mkdir()
        patches_dir = tmp_path / "patches"
        patch_dir = patches_dir / "treatment-1"
        patch_dir.mkdir(parents=True)
        (patch_dir / "bug-20945.patch").write_text("bad diff")
        data_dir = tmp_path / "data"

        with (
            patch("ate.scoring.tier1.apply_patch", return_value=False),
            patch("ate.scoring.tier1.revert_ruff"),
            patch(
                "ate.scoring.tier1.extract_cost_and_time",
                return_value=(None, None),
            ),
        ):
            score = score_bug(1, 20945, ruff_dir, patches_dir, data_dir)

        assert score.patch_applies is False
        assert score.existing_tests_pass is False
        assert score.reproduction_fixed is False
        assert score.no_regressions is False

    def test_build_fails(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        ruff_dir = tmp_path / "ruff"
        ruff_dir.mkdir()
        patches_dir = tmp_path / "patches"
        patch_dir = patches_dir / "treatment-1"
        patch_dir.mkdir(parents=True)
        (patch_dir / "bug-20945.patch").write_text("diff")
        data_dir = tmp_path / "data"

        with (
            patch("ate.scoring.tier1.apply_patch", return_value=True),
            patch("ate.scoring.tier1.rebuild_ruff", return_value=False),
            patch("ate.scoring.tier1.revert_ruff"),
            patch(
                "ate.scoring.tier1.extract_cost_and_time",
                return_value=(None, None),
            ),
        ):
            score = score_bug(1, 20945, ruff_dir, patches_dir, data_dir)

        assert score.patch_applies is True
        assert score.existing_tests_pass is False
        assert score.reproduction_fixed is False
        assert score.no_regressions is False

    def test_reverts_after_scoring(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        ruff_dir = tmp_path / "ruff"
        ruff_dir.mkdir()
        patches_dir = tmp_path / "patches"
        patch_dir = patches_dir / "treatment-1"
        patch_dir.mkdir(parents=True)
        (patch_dir / "bug-20945.patch").write_text("diff")
        data_dir = tmp_path / "data"

        with (
            patch("ate.scoring.tier1.apply_patch", return_value=True),
            patch("ate.scoring.tier1.rebuild_ruff", return_value=True),
            patch("ate.scoring.tier1.is_fixed", return_value=True),
            patch("ate.scoring.tier1.check_tests_pass", return_value=True),
            patch("ate.scoring.tier1.revert_ruff") as mock_revert,
            patch(
                "ate.scoring.tier1.extract_cost_and_time",
                return_value=(None, None),
            ),
        ):
            score_bug(1, 20945, ruff_dir, patches_dir, data_dir)

        mock_revert.assert_called_once_with(ruff_dir)
