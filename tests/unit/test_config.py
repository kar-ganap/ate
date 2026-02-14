"""Tests for ate.config."""

from __future__ import annotations

from pathlib import Path

import pytest

from ate.config import load_bugs, load_treatments
from ate.models import BugCategory, Complexity, Decomposition, ExecutionMode


class TestLoadBugs:
    def test_load_valid_bugs(self, bugs_yaml_path: Path) -> None:
        portfolio = load_bugs(config_dir=bugs_yaml_path)
        assert len(portfolio.primary) == 2
        assert len(portfolio.backup) == 1

    def test_primary_bug_fields(self, bugs_yaml_path: Path) -> None:
        portfolio = load_bugs(config_dir=bugs_yaml_path)
        bug = portfolio.primary[0]
        assert bug.id == 20945
        assert bug.rule == "FAST001"
        assert bug.category == BugCategory.SEMANTIC_ANALYSIS
        assert bug.complexity == Complexity.SIMPLE

    def test_backup_bug_can_replace(self, bugs_yaml_path: Path) -> None:
        portfolio = load_bugs(config_dir=bugs_yaml_path)
        backup = portfolio.backup[0]
        assert backup.can_replace == [20945]

    def test_get_bug_from_loaded(self, bugs_yaml_path: Path) -> None:
        portfolio = load_bugs(config_dir=bugs_yaml_path)
        bug = portfolio.get_bug(7847)
        assert bug is not None
        assert bug.rule == "B023"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="bugs.yaml not found"):
            load_bugs(config_dir=tmp_path)

    def test_load_real_config(self) -> None:
        """Load the actual config/bugs.yaml to verify it's valid."""
        portfolio = load_bugs()
        assert len(portfolio.primary) == 8
        assert len(portfolio.backup) == 4
        # Verify all categories are valid enums
        for bug in portfolio.all_bugs:
            assert isinstance(bug.category, BugCategory)
            assert isinstance(bug.complexity, Complexity)


class TestLoadTreatments:
    def test_load_valid_treatments(self, treatments_yaml_path: Path) -> None:
        config = load_treatments(config_dir=treatments_yaml_path)
        assert len(config.treatments) == 2

    def test_treatment_fields(self, treatments_yaml_path: Path) -> None:
        config = load_treatments(config_dir=treatments_yaml_path)
        t0 = config.treatments[0]
        assert t0.id == "0b"
        assert t0.label == "Control: Swim Lanes"
        assert t0.dimensions.decomposition == Decomposition.EXPLICIT
        assert t0.execution.mode == ExecutionMode.INTERACTIVE
        assert t0.execution.soft_budget == "~25 tool calls per bug"

    def test_interactive_treatment(self, treatments_yaml_path: Path) -> None:
        config = load_treatments(config_dir=treatments_yaml_path)
        t1 = config.treatments[1]
        assert t1.execution.mode == ExecutionMode.INTERACTIVE
        assert t1.execution.soft_budget == "~25 tool calls per bug"

    def test_bug_assignments(self, treatments_yaml_path: Path) -> None:
        config = load_treatments(config_dir=treatments_yaml_path)
        explicit = config.bug_assignments.explicit
        assert explicit.agent_1 == [20945, 22528]
        assert explicit.agent_4 == [4384, 22221]

    def test_correlation_pairs(self, treatments_yaml_path: Path) -> None:
        config = load_treatments(config_dir=treatments_yaml_path)
        assert len(config.correlation_pairs) == 1
        assert config.correlation_pairs[0].name == "semantic"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="treatments.yaml not found"):
            load_treatments(config_dir=tmp_path)

    def test_load_real_config(self) -> None:
        """Load the actual config/treatments.yaml to verify it's valid."""
        config = load_treatments()
        assert len(config.treatments) == 8
        assert len(config.correlation_pairs) == 3
        # Verify treatment IDs cover expected range
        ids = [t.id for t in config.treatments]
        assert "0a" in ids
        assert "0b" in ids
        assert 5 in ids
        assert "2a" in ids
        assert "2b" in ids
