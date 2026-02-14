"""Shared test fixtures for ate."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from ate.models import (
    Bug,
    ExecutionConfig,
    Treatment,
    TreatmentDimensions,
)


@pytest.fixture
def sample_bug_data() -> dict[str, Any]:
    """A single valid bug dict for testing."""
    return {
        "id": 99999,
        "rule": "TEST001",
        "title": "Test bug for unit tests",
        "category": "semantic_analysis",
        "complexity": "medium",
        "url": "https://github.com/astral-sh/ruff/issues/99999",
        "reproduction": "# test reproduction\n",
    }


@pytest.fixture
def sample_treatment_data() -> dict[str, Any]:
    """A single valid treatment dict for testing."""
    return {
        "id": 0,
        "label": "Test Treatment",
        "dimensions": {
            "decomposition": "explicit",
            "prompt_specificity": "detailed",
            "delegate_mode": None,
            "team_size": "8x1",
            "communication": None,
        },
        "execution": {
            "mode": "programmatic",
            "max_turns": 50,
            "timeout_seconds": 1800,
            "output_format": "json",
        },
    }


@pytest.fixture
def bugs_yaml_path(tmp_path: Path) -> Path:
    """Create a temporary bugs.yaml for testing."""
    data = {
        "primary": [
            {
                "id": 20945,
                "rule": "FAST001",
                "title": "FAST001 false positive",
                "category": "semantic_analysis",
                "complexity": "simple",
                "url": "https://github.com/astral-sh/ruff/issues/20945",
            },
            {
                "id": 7847,
                "rule": "B023",
                "title": "B023 false positive",
                "category": "scope_control_flow",
                "complexity": "medium",
                "url": "https://github.com/astral-sh/ruff/issues/7847",
            },
        ],
        "backup": [
            {
                "id": 13337,
                "rule": "RUF001",
                "title": "RUF001 emoji false positive",
                "category": "semantic_analysis",
                "complexity": "simple",
                "url": "https://github.com/astral-sh/ruff/issues/13337",
                "can_replace": [20945],
            },
        ],
    }
    path = tmp_path / "bugs.yaml"
    with open(path, "w") as f:
        yaml.dump(data, f)
    return tmp_path


@pytest.fixture
def treatments_yaml_path(tmp_path: Path) -> Path:
    """Create a temporary treatments.yaml for testing."""
    data = {
        "treatments": [
            {
                "id": "0b",
                "label": "Control: Swim Lanes",
                "dimensions": {
                    "decomposition": "explicit",
                    "prompt_specificity": "detailed",
                    "delegate_mode": None,
                    "team_size": "8x1",
                    "communication": None,
                },
                "execution": {
                    "mode": "interactive",
                    "soft_budget": "~25 tool calls per bug",
                },
            },
            {
                "id": 1,
                "label": "Structured Team",
                "dimensions": {
                    "decomposition": "explicit",
                    "prompt_specificity": "detailed",
                    "delegate_mode": True,
                    "team_size": "4x2",
                    "communication": "neutral",
                },
                "execution": {
                    "mode": "interactive",
                    "soft_budget": "~25 tool calls per bug",
                },
            },
        ],
        "bug_assignments": {
            "explicit": {
                "agent_1": [20945, 22528],
                "agent_2": [18654, 22494],
                "agent_3": [7847, 19301],
                "agent_4": [4384, 22221],
            },
            "autonomous": None,
        },
        "correlation_pairs": [
            {
                "name": "semantic",
                "bug_a": 20945,
                "bug_b": 18654,
                "shared": "ruff_python_semantic name resolution",
            },
        ],
    }
    path = tmp_path / "treatments.yaml"
    with open(path, "w") as f:
        yaml.dump(data, f)
    return tmp_path


@pytest.fixture
def sample_bug() -> Bug:
    """A Bug model instance for harness tests."""
    return Bug(
        id=20945,
        rule="FAST001",
        title="FAST001 false positive (None==None)",
        category="semantic_analysis",
        complexity="simple",
        url="https://github.com/astral-sh/ruff/issues/20945",
        reproduction="# FAST001 repro\nimport foo\n",
    )


@pytest.fixture
def sample_treatment_0() -> Treatment:
    """Treatment 0b (interactive swim lanes control)."""
    return Treatment(
        id="0b",
        label="Control: Swim Lanes",
        dimensions=TreatmentDimensions(
            decomposition="explicit",
            prompt_specificity="detailed",
            delegate_mode=None,
            team_size="8x1",
            communication=None,
        ),
        execution=ExecutionConfig(
            mode="interactive",
            soft_budget="~25 tool calls per bug",
        ),
    )


@pytest.fixture
def sample_interactive_treatment() -> Treatment:
    """Treatment 2a (interactive agent team)."""
    return Treatment(
        id="2a",
        label="Autonomous Vague Team",
        dimensions=TreatmentDimensions(
            decomposition="autonomous",
            prompt_specificity="vague",
            delegate_mode=True,
            team_size="4x2",
            communication="encourage",
        ),
        execution=ExecutionConfig(
            mode="interactive",
            soft_budget="~25 tool calls per bug",
        ),
    )


@pytest.fixture
def mock_claude_json_output() -> dict[str, Any]:
    """Simulated `claude -p --output-format json` response."""
    return {
        "result": "I investigated bug #20945 and found the root cause...",
        "num_turns": 8,
        "session_id": "test-session-abc123",
        "cost_usd": 0.42,
        "is_error": False,
    }
