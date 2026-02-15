"""Tests for ate.models."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from ate.models import (
    Bug,
    BugCategory,
    BugPortfolio,
    Complexity,
    CorrelationPair,
    Decomposition,
    ExecutionConfig,
    ExecutionMode,
    PromptSpecificity,
    RoundBugs,
    RunMetadata,
    RunResult,
    TeamSize,
    Tier1Score,
    Tier2Score,
    Tier3Score,
    Tier25Score,
    Treatment,
    TreatmentDimensions,
)


class TestBug:
    def test_valid_bug(self, sample_bug_data: dict[str, Any]) -> None:
        bug = Bug(**sample_bug_data)
        assert bug.id == 99999
        assert bug.category == BugCategory.SEMANTIC_ANALYSIS
        assert bug.complexity == Complexity.MEDIUM

    def test_invalid_category(self, sample_bug_data: dict[str, Any]) -> None:
        sample_bug_data["category"] = "nonexistent"
        with pytest.raises(ValidationError):
            Bug(**sample_bug_data)

    def test_invalid_complexity(self, sample_bug_data: dict[str, Any]) -> None:
        sample_bug_data["complexity"] = "impossible"
        with pytest.raises(ValidationError):
            Bug(**sample_bug_data)

    def test_optional_fields_default(self, sample_bug_data: dict[str, Any]) -> None:
        bug = Bug(**sample_bug_data)
        assert bug.swap_note is None
        assert bug.can_replace == []
        assert bug.note is None

    def test_with_swap_note(self, sample_bug_data: dict[str, Any]) -> None:
        sample_bug_data["swap_note"] = "If too hard, swap to #20891"
        bug = Bug(**sample_bug_data)
        assert bug.swap_note == "If too hard, swap to #20891"

    def test_with_can_replace(self, sample_bug_data: dict[str, Any]) -> None:
        sample_bug_data["can_replace"] = [20945, 18654]
        bug = Bug(**sample_bug_data)
        assert bug.can_replace == [20945, 18654]

    def test_round_default(self, sample_bug_data: dict[str, Any]) -> None:
        bug = Bug(**sample_bug_data)
        assert bug.round == 1

    def test_round_explicit(self, sample_bug_data: dict[str, Any]) -> None:
        sample_bug_data["round"] = 2
        bug = Bug(**sample_bug_data)
        assert bug.round == 2

    def test_serialization_roundtrip(self, sample_bug_data: dict[str, Any]) -> None:
        bug = Bug(**sample_bug_data)
        data = bug.model_dump()
        restored = Bug(**data)
        assert restored == bug


class TestRoundBugs:
    def test_all_bugs(self) -> None:
        primary = [
            Bug(id=1, rule="R1", title="Bug 1", category="semantic_analysis",
                complexity="simple", url="https://example.com/1"),
        ]
        backup = [
            Bug(id=2, rule="R2", title="Bug 2", category="parser",
                complexity="hard", url="https://example.com/2"),
        ]
        rb = RoundBugs(ruff_pin="0.14.14", primary=primary, backup=backup)
        assert len(rb.all_bugs) == 2
        assert len(rb.primary) == 1
        assert len(rb.backup) == 1
        assert rb.ruff_pin == "0.14.14"

    def test_empty_defaults(self) -> None:
        rb = RoundBugs()
        assert rb.primary == []
        assert rb.backup == []
        assert rb.ruff_pin == ""


class TestBugPortfolio:
    def _make_portfolio(self) -> BugPortfolio:
        """Helper to build a two-round portfolio."""
        r1 = RoundBugs(
            ruff_pin="0.14.14",
            primary=[
                Bug(id=1, rule="R1", title="Bug 1", category="semantic_analysis",
                    complexity="simple", url="https://example.com/1", round=1),
            ],
            backup=[
                Bug(id=2, rule="R2", title="Bug 2", category="parser",
                    complexity="hard", url="https://example.com/2", round=1),
            ],
        )
        r2 = RoundBugs(
            ruff_pin="abc1234",
            primary=[
                Bug(id=3, rule="R3", title="Bug 3", category="configuration",
                    complexity="medium", url="https://example.com/3", round=2),
            ],
        )
        return BugPortfolio(rounds={1: r1, 2: r2})

    def test_all_bugs(self) -> None:
        portfolio = self._make_portfolio()
        assert len(portfolio.all_bugs) == 3

    def test_primary_across_rounds(self) -> None:
        portfolio = self._make_portfolio()
        assert len(portfolio.primary) == 2
        ids = {b.id for b in portfolio.primary}
        assert ids == {1, 3}

    def test_backup_across_rounds(self) -> None:
        portfolio = self._make_portfolio()
        assert len(portfolio.backup) == 1
        assert portfolio.backup[0].id == 2

    def test_get_bug_found(self) -> None:
        portfolio = self._make_portfolio()
        bug = portfolio.get_bug(1)
        assert bug is not None
        assert bug.id == 1
        assert bug.round == 1

    def test_get_bug_from_round2(self) -> None:
        portfolio = self._make_portfolio()
        bug = portfolio.get_bug(3)
        assert bug is not None
        assert bug.id == 3
        assert bug.round == 2

    def test_get_bug_not_found(self) -> None:
        portfolio = BugPortfolio(rounds={})
        assert portfolio.get_bug(99999) is None

    def test_get_bug_from_backup(self) -> None:
        portfolio = self._make_portfolio()
        bug = portfolio.get_bug(2)
        assert bug is not None
        assert bug.id == 2

    def test_get_round(self) -> None:
        portfolio = self._make_portfolio()
        r1 = portfolio.get_round(1)
        assert r1 is not None
        assert r1.ruff_pin == "0.14.14"
        assert len(r1.primary) == 1

    def test_get_round_missing(self) -> None:
        portfolio = self._make_portfolio()
        assert portfolio.get_round(99) is None

    def test_empty_portfolio(self) -> None:
        portfolio = BugPortfolio(rounds={})
        assert portfolio.primary == []
        assert portfolio.backup == []
        assert portfolio.all_bugs == []


class TestTreatmentDimensions:
    def test_valid_dimensions(self) -> None:
        dims = TreatmentDimensions(
            decomposition="explicit",
            prompt_specificity="detailed",
            delegate_mode=True,
            team_size="4x2",
            communication="neutral",
        )
        assert dims.decomposition == Decomposition.EXPLICIT
        assert dims.prompt_specificity == PromptSpecificity.DETAILED
        assert dims.team_size == TeamSize.FOUR_BY_TWO

    def test_subagent_dimensions(self) -> None:
        dims = TreatmentDimensions(
            decomposition="explicit",
            prompt_specificity="detailed",
            delegate_mode=None,
            team_size="8x1",
            communication=None,
        )
        assert dims.delegate_mode is None
        assert dims.communication is None

    def test_invalid_decomposition(self) -> None:
        with pytest.raises(ValidationError):
            TreatmentDimensions(
                decomposition="random",
                prompt_specificity="detailed",
                team_size="4x2",
            )


class TestTreatment:
    def test_valid_treatment(self, sample_treatment_data: dict[str, Any]) -> None:
        treatment = Treatment(**sample_treatment_data)
        assert treatment.id == 0
        assert treatment.label == "Test Treatment"
        assert treatment.execution.mode == ExecutionMode.PROGRAMMATIC

    def test_string_id(self) -> None:
        treatment = Treatment(
            id="2a",
            label="Test",
            dimensions=TreatmentDimensions(
                decomposition="autonomous",
                prompt_specificity="vague",
                team_size="4x2",
            ),
            execution=ExecutionConfig(mode="interactive"),
        )
        assert treatment.id == "2a"

    def test_serialization_roundtrip(self, sample_treatment_data: dict[str, Any]) -> None:
        treatment = Treatment(**sample_treatment_data)
        data = treatment.model_dump()
        restored = Treatment(**data)
        assert restored == treatment


class TestCorrelationPair:
    def test_valid_pair(self) -> None:
        pair = CorrelationPair(
            name="semantic",
            bug_a=20945,
            bug_b=18654,
            shared="ruff_python_semantic name resolution",
        )
        assert pair.name == "semantic"
        assert pair.bug_a == 20945


class TestTier1Score:
    def test_all_pass(self) -> None:
        score = Tier1Score(
            bug_id=20945,
            treatment_id=0,
            patch_applies=True,
            existing_tests_pass=True,
            reproduction_fixed=True,
            no_regressions=True,
        )
        assert score.all_pass is True

    def test_not_all_pass(self) -> None:
        score = Tier1Score(
            bug_id=20945,
            treatment_id=0,
            patch_applies=True,
            existing_tests_pass=False,
            reproduction_fixed=True,
            no_regressions=True,
        )
        assert score.all_pass is False

    def test_optional_cost_fields(self) -> None:
        score = Tier1Score(
            bug_id=20945,
            treatment_id=0,
            patch_applies=True,
            existing_tests_pass=True,
            reproduction_fixed=True,
            no_regressions=True,
            token_cost_usd=1.50,
            wall_clock_minutes=12.5,
        )
        assert score.token_cost_usd == 1.50
        assert score.wall_clock_minutes == 12.5

    def test_string_treatment_id(self) -> None:
        score = Tier1Score(
            bug_id=20945,
            treatment_id="2a",
            patch_applies=True,
            existing_tests_pass=True,
            reproduction_fixed=True,
            no_regressions=True,
        )
        assert score.treatment_id == "2a"


class TestTier2Score:
    def test_valid_scores(self) -> None:
        score = Tier2Score(
            bug_id=20945,
            treatment_id=0,
            localization=2,
            root_cause=1,
            fix_direction=2,
            confidence_calibration=1,
        )
        assert score.total == 6

    def test_max_score(self) -> None:
        score = Tier2Score(
            bug_id=20945,
            treatment_id=0,
            localization=2,
            root_cause=2,
            fix_direction=2,
            confidence_calibration=2,
        )
        assert score.total == 8

    def test_min_score(self) -> None:
        score = Tier2Score(
            bug_id=20945,
            treatment_id=0,
            localization=0,
            root_cause=0,
            fix_direction=0,
            confidence_calibration=0,
        )
        assert score.total == 0

    def test_score_out_of_range_high(self) -> None:
        with pytest.raises(ValidationError):
            Tier2Score(
                bug_id=20945,
                treatment_id=0,
                localization=3,
                root_cause=0,
                fix_direction=0,
                confidence_calibration=0,
            )

    def test_score_out_of_range_low(self) -> None:
        with pytest.raises(ValidationError):
            Tier2Score(
                bug_id=20945,
                treatment_id=0,
                localization=-1,
                root_cause=0,
                fix_direction=0,
                confidence_calibration=0,
            )


class TestTier25Score:
    def test_valid_score(self) -> None:
        score = Tier25Score(
            bug_id=20945,
            cross_treatment_agreement=0.85,
            within_team_agreement=0.70,
            groupthink_flag=False,
        )
        assert score.cross_treatment_agreement == 0.85

    def test_groupthink_flagged(self) -> None:
        score = Tier25Score(
            bug_id=20945,
            cross_treatment_agreement=0.3,
            within_team_agreement=0.9,
            groupthink_flag=True,
        )
        assert score.groupthink_flag is True

    def test_agreement_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            Tier25Score(
                bug_id=20945,
                cross_treatment_agreement=1.5,
            )


class TestTier3Score:
    def test_valid_score(self) -> None:
        score = Tier3Score(
            pair_name="semantic",
            treatment_id=1,
            connection_identified=True,
            connection_correct=True,
            discovery_mechanism="inter-agent message",
            connection_depth="specific",
        )
        assert score.connection_identified is True
        assert score.connection_depth == "specific"

    def test_no_connection(self) -> None:
        score = Tier3Score(
            pair_name="parser",
            treatment_id=0,
            connection_identified=False,
        )
        assert score.connection_correct is None
        assert score.discovery_mechanism is None


class TestRunMetadata:
    def test_minimal(self) -> None:
        meta = RunMetadata(
            treatment_id=0,
            bug_id=20945,
            mode="programmatic",
        )
        assert meta.treatment_id == 0
        assert meta.bug_id == 20945
        assert meta.mode == ExecutionMode.PROGRAMMATIC
        assert meta.started_at is None
        assert meta.completed_at is None
        assert meta.wall_clock_seconds is None
        assert meta.session_id is None
        assert meta.model is None
        assert meta.num_turns is None
        assert meta.total_cost_usd is None
        assert meta.exit_code is None

    def test_full(self) -> None:
        from datetime import datetime

        now = datetime(2026, 2, 9, 12, 0, 0)
        meta = RunMetadata(
            treatment_id="2a",
            bug_id=7847,
            started_at=now,
            completed_at=now,
            wall_clock_seconds=120.5,
            session_id="abc123",
            model="claude-opus-4-6",
            num_turns=5,
            total_cost_usd=1.25,
            exit_code=0,
            mode="interactive",
        )
        assert meta.treatment_id == "2a"
        assert meta.wall_clock_seconds == 120.5
        assert meta.model == "claude-opus-4-6"
        assert meta.mode == ExecutionMode.INTERACTIVE

    def test_string_treatment_id(self) -> None:
        meta = RunMetadata(treatment_id="2b", bug_id=4384, mode="interactive")
        assert meta.treatment_id == "2b"

    def test_invalid_mode(self) -> None:
        with pytest.raises(ValidationError):
            RunMetadata(treatment_id=0, bug_id=20945, mode="unknown")

    def test_serialization_roundtrip(self) -> None:
        meta = RunMetadata(
            treatment_id=0,
            bug_id=20945,
            mode="programmatic",
            session_id="test-session",
            exit_code=0,
        )
        data = meta.model_dump()
        restored = RunMetadata(**data)
        assert restored == meta


class TestRunResult:
    def test_minimal(self) -> None:
        meta = RunMetadata(treatment_id=0, bug_id=20945, mode="programmatic")
        result = RunResult(metadata=meta)
        assert result.raw_output_path is None
        assert result.result_text is None
        assert result.patch_path is None
        assert result.metadata == meta

    def test_full(self) -> None:
        from pathlib import Path

        meta = RunMetadata(
            treatment_id=0,
            bug_id=20945,
            mode="programmatic",
            exit_code=0,
        )
        result = RunResult(
            raw_output_path=Path("data/transcripts/treatment-0/bug-20945/raw_output.json"),
            result_text="Fixed the bug by...",
            patch_path=Path("data/patches/treatment-0/bug-20945.patch"),
            metadata=meta,
        )
        assert result.raw_output_path == Path(
            "data/transcripts/treatment-0/bug-20945/raw_output.json"
        )
        assert result.result_text == "Fixed the bug by..."
        assert result.patch_path == Path("data/patches/treatment-0/bug-20945.patch")

    def test_serialization_roundtrip(self) -> None:
        meta = RunMetadata(treatment_id=1, bug_id=7847, mode="interactive")
        result = RunResult(
            result_text="Diagnosis: scope issue",
            metadata=meta,
        )
        data = result.model_dump()
        restored = RunResult(**data)
        assert restored == result
