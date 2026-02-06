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

    def test_serialization_roundtrip(self, sample_bug_data: dict[str, Any]) -> None:
        bug = Bug(**sample_bug_data)
        data = bug.model_dump()
        restored = Bug(**data)
        assert restored == bug


class TestBugPortfolio:
    def test_all_bugs(self) -> None:
        primary = [
            Bug(
                id=1,
                rule="R1",
                title="Bug 1",
                category="semantic_analysis",
                complexity="simple",
                url="https://example.com/1",
            ),
        ]
        backup = [
            Bug(
                id=2,
                rule="R2",
                title="Bug 2",
                category="parser",
                complexity="hard",
                url="https://example.com/2",
            ),
        ]
        portfolio = BugPortfolio(primary=primary, backup=backup)
        assert len(portfolio.all_bugs) == 2
        assert len(portfolio.primary) == 1
        assert len(portfolio.backup) == 1

    def test_get_bug_found(self) -> None:
        primary = [
            Bug(
                id=20945,
                rule="FAST001",
                title="Test",
                category="semantic_analysis",
                complexity="simple",
                url="https://example.com",
            ),
        ]
        portfolio = BugPortfolio(primary=primary)
        bug = portfolio.get_bug(20945)
        assert bug is not None
        assert bug.id == 20945

    def test_get_bug_not_found(self) -> None:
        portfolio = BugPortfolio(primary=[])
        assert portfolio.get_bug(99999) is None

    def test_get_bug_from_backup(self) -> None:
        backup = [
            Bug(
                id=13337,
                rule="RUF001",
                title="Test",
                category="semantic_analysis",
                complexity="simple",
                url="https://example.com",
            ),
        ]
        portfolio = BugPortfolio(primary=[], backup=backup)
        bug = portfolio.get_bug(13337)
        assert bug is not None
        assert bug.id == 13337


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
