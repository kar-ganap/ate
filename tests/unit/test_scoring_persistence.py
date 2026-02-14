"""Tests for score persistence (save/load)."""

from __future__ import annotations

import json

from ate.models import Tier1Score, Tier2Score
from ate.scoring.persistence import load_scores, save_scores


class TestSaveScores:
    def test_save_tier1_scores(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        scores = [
            Tier1Score(
                bug_id=20945,
                treatment_id="0b",
                patch_applies=True,
                existing_tests_pass=True,
                reproduction_fixed=True,
                no_regressions=True,
                token_cost_usd=0.42,
                wall_clock_minutes=5.0,
            ),
        ]
        out = tmp_path / "tier1.json"
        result = save_scores(scores, out)
        assert result == out
        assert out.exists()
        data = json.loads(out.read_text())
        assert len(data) == 1
        assert data[0]["bug_id"] == 20945
        assert data[0]["patch_applies"] is True

    def test_save_tier2_scores(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        scores = [
            Tier2Score(
                bug_id=20945,
                treatment_id=1,
                localization=2,
                root_cause=1,
                fix_direction=2,
                confidence_calibration=0,
            ),
        ]
        out = tmp_path / "tier2.json"
        save_scores(scores, out)
        data = json.loads(out.read_text())
        assert data[0]["localization"] == 2
        assert data[0]["treatment_id"] == 1

    def test_save_empty_list(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        out = tmp_path / "empty.json"
        save_scores([], out)
        data = json.loads(out.read_text())
        assert data == []

    def test_save_overwrites_existing(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        out = tmp_path / "scores.json"
        out.write_text('[{"old": true}]')
        scores = [
            Tier1Score(
                bug_id=7847,
                treatment_id=1,
                patch_applies=False,
                existing_tests_pass=False,
                reproduction_fixed=False,
                no_regressions=False,
            ),
        ]
        save_scores(scores, out)
        data = json.loads(out.read_text())
        assert len(data) == 1
        assert data[0]["bug_id"] == 7847


class TestLoadScores:
    def test_load_tier1_scores(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        data = [
            {
                "bug_id": 20945,
                "treatment_id": "0b",
                "patch_applies": True,
                "existing_tests_pass": True,
                "reproduction_fixed": True,
                "no_regressions": True,
                "token_cost_usd": 0.42,
                "wall_clock_minutes": 5.0,
            },
        ]
        path = tmp_path / "tier1.json"
        path.write_text(json.dumps(data))
        result = load_scores(path, Tier1Score)
        assert len(result) == 1
        assert isinstance(result[0], Tier1Score)
        assert result[0].bug_id == 20945
        assert result[0].all_pass is True

    def test_load_tier2_scores(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        data = [
            {
                "bug_id": 7847,
                "treatment_id": 1,
                "localization": 2,
                "root_cause": 2,
                "fix_direction": 1,
                "confidence_calibration": 0,
            },
        ]
        path = tmp_path / "tier2.json"
        path.write_text(json.dumps(data))
        result = load_scores(path, Tier2Score)
        assert len(result) == 1
        assert isinstance(result[0], Tier2Score)
        assert result[0].total == 5

    def test_load_missing_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "nonexistent.json"
        result = load_scores(path, Tier1Score)
        assert result == []

    def test_load_empty_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "empty.json"
        path.write_text("[]")
        result = load_scores(path, Tier1Score)
        assert result == []

    def test_round_trip(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        original = [
            Tier1Score(
                bug_id=20945,
                treatment_id="0b",
                patch_applies=True,
                existing_tests_pass=True,
                reproduction_fixed=True,
                no_regressions=True,
                token_cost_usd=0.42,
                wall_clock_minutes=5.0,
            ),
            Tier1Score(
                bug_id=7847,
                treatment_id=1,
                patch_applies=False,
                existing_tests_pass=False,
                reproduction_fixed=False,
                no_regressions=True,
            ),
        ]
        path = tmp_path / "roundtrip.json"
        save_scores(original, path)
        loaded = load_scores(path, Tier1Score)
        assert len(loaded) == 2
        assert loaded[0].bug_id == original[0].bug_id
        assert loaded[0].treatment_id == original[0].treatment_id
        assert loaded[0].token_cost_usd == original[0].token_cost_usd
        assert loaded[1].patch_applies is False
