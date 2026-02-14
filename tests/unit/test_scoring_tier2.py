"""Tests for Tier 2 human scoring scaffolding and persistence."""

from __future__ import annotations

import json

from ate.models import Bug, Tier2Score
from ate.scoring.tier2 import (
    generate_scoring_guide,
    load_tier2_scores,
    record_tier2_score,
    scaffold_tier2,
)


def _make_bug(bug_id: int = 20945) -> Bug:
    return Bug(
        id=bug_id,
        rule="FAST001",
        title="FAST001 false positive",
        category="semantic_analysis",
        complexity="simple",
        url=f"https://github.com/astral-sh/ruff/issues/{bug_id}",
        reproduction="# repro code\n",
    )


def _make_bugs() -> list[Bug]:
    ids = [20945, 18654, 7847, 4384, 19301, 22221, 22528, 22494]
    return [
        Bug(
            id=bid,
            rule="TEST",
            title=f"Bug {bid}",
            category="semantic_analysis",
            complexity="simple",
            url=f"https://github.com/astral-sh/ruff/issues/{bid}",
        )
        for bid in ids
    ]


class TestGenerateScoringGuide:
    def test_contains_bug_details(self) -> None:
        bug = _make_bug()
        treatment_ids = ["0a", "0b", 1]
        guide = generate_scoring_guide(bug, treatment_ids)
        assert "20945" in guide
        assert "FAST001" in guide

    def test_contains_rubric(self) -> None:
        bug = _make_bug()
        guide = generate_scoring_guide(bug, [1, 2])
        assert "localization" in guide.lower()
        assert "root cause" in guide.lower() or "root_cause" in guide.lower()

    def test_contains_treatment_references(self) -> None:
        bug = _make_bug()
        treatment_ids = ["0a", "0b", 1, "2a"]
        guide = generate_scoring_guide(bug, treatment_ids)
        for tid in treatment_ids:
            assert str(tid) in guide

    def test_contains_score_range(self) -> None:
        bug = _make_bug()
        guide = generate_scoring_guide(bug, [1])
        assert "0" in guide
        assert "2" in guide


class TestScaffoldTier2:
    def test_creates_guide_files(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        bugs = _make_bugs()
        treatment_ids = ["0a", "0b", 1]
        scaffold_tier2(bugs, treatment_ids, tmp_path)
        for bug in bugs:
            guide_path = tmp_path / f"bug-{bug.id}-guide.md"
            assert guide_path.exists(), f"Missing guide for bug #{bug.id}"

    def test_creates_8_guides(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        bugs = _make_bugs()
        scaffold_tier2(bugs, [1], tmp_path)
        guides = list(tmp_path.glob("*-guide.md"))
        assert len(guides) == 8


class TestRecordTier2Score:
    def test_saves_score(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        score = Tier2Score(
            bug_id=20945,
            treatment_id=1,
            localization=2,
            root_cause=1,
            fix_direction=2,
            confidence_calibration=0,
        )
        path = record_tier2_score(score, tmp_path)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data[0]["bug_id"] == 20945
        assert data[0]["localization"] == 2

    def test_appends_to_existing(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        score1 = Tier2Score(
            bug_id=20945,
            treatment_id=1,
            localization=2,
            root_cause=1,
            fix_direction=2,
            confidence_calibration=0,
        )
        score2 = Tier2Score(
            bug_id=20945,
            treatment_id="0b",
            localization=1,
            root_cause=2,
            fix_direction=1,
            confidence_calibration=1,
        )
        record_tier2_score(score1, tmp_path)
        record_tier2_score(score2, tmp_path)

        scores = load_tier2_scores(tmp_path, 20945)
        assert len(scores) == 2


class TestLoadTier2Scores:
    def test_load_existing(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        score = Tier2Score(
            bug_id=7847,
            treatment_id=1,
            localization=0,
            root_cause=0,
            fix_direction=1,
            confidence_calibration=2,
        )
        record_tier2_score(score, tmp_path)
        loaded = load_tier2_scores(tmp_path, 7847)
        assert len(loaded) == 1
        assert loaded[0].total == 3

    def test_load_missing(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        loaded = load_tier2_scores(tmp_path, 99999)
        assert loaded == []

    def test_load_all_bugs(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        for bid in [20945, 7847]:
            score = Tier2Score(
                bug_id=bid,
                treatment_id=1,
                localization=1,
                root_cause=1,
                fix_direction=1,
                confidence_calibration=1,
            )
            record_tier2_score(score, tmp_path)

        all_scores = load_tier2_scores(tmp_path)
        assert len(all_scores) == 2
