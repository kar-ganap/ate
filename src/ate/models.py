"""Data models for the Agent Teams Eval experiment."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

# --- Enums ---


class BugCategory(StrEnum):
    SEMANTIC_ANALYSIS = "semantic_analysis"
    SCOPE_CONTROL_FLOW = "scope_control_flow"
    PARSER = "parser"
    AUTOFIX_CONVERGENCE = "autofix_convergence"
    CONFIGURATION = "configuration"


class Complexity(StrEnum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    HARD = "hard"


class Decomposition(StrEnum):
    EXPLICIT = "explicit"
    AUTONOMOUS = "autonomous"


class PromptSpecificity(StrEnum):
    DETAILED = "detailed"
    VAGUE = "vague"


class TeamSize(StrEnum):
    ONE_BY_EIGHT = "1x8"
    FOUR_BY_TWO = "4x2"
    EIGHT_BY_ONE = "8x1"


class CommunicationMode(StrEnum):
    NEUTRAL = "neutral"
    ENCOURAGE = "encourage"
    DISCOURAGE = "discourage"


class ExecutionMode(StrEnum):
    PROGRAMMATIC = "programmatic"
    INTERACTIVE = "interactive"


# --- Bug Models ---


class Bug(BaseModel):
    """A Ruff bug in the experiment portfolio."""

    id: int
    rule: str
    title: str
    category: BugCategory
    complexity: Complexity
    url: str
    reproduction: str = ""
    swap_note: str | None = None
    can_replace: list[int] = Field(default_factory=list)
    note: str | None = None


class BugPortfolio(BaseModel):
    """Complete bug portfolio: primary + backup."""

    primary: list[Bug]
    backup: list[Bug] = Field(default_factory=list)

    @property
    def all_bugs(self) -> list[Bug]:
        return self.primary + self.backup

    def get_bug(self, bug_id: int) -> Bug | None:
        for bug in self.all_bugs:
            if bug.id == bug_id:
                return bug
        return None


# --- Treatment Models ---


class TreatmentDimensions(BaseModel):
    """Experimental dimension values for a treatment."""

    decomposition: Decomposition
    prompt_specificity: PromptSpecificity
    delegate_mode: bool | None = None  # None for subagents (N/A)
    team_size: TeamSize
    communication: CommunicationMode | None = None  # None for subagents (N/A)


class ExecutionConfig(BaseModel):
    """Execution configuration for a treatment."""

    mode: ExecutionMode
    max_turns: int | None = None
    timeout_seconds: int | None = None
    output_format: str | None = None
    soft_budget: str | None = None


class Treatment(BaseModel):
    """A treatment in the experiment."""

    id: int | str  # int or "2a", "2b"
    label: str
    dimensions: TreatmentDimensions
    execution: ExecutionConfig


class CorrelationPair(BaseModel):
    """A hidden correlation pair between two bugs."""

    name: str
    bug_a: int
    bug_b: int
    shared: str


class BugAssignment(BaseModel):
    """Bug assignment for explicit treatments."""

    agent_1: list[int]
    agent_2: list[int]
    agent_3: list[int]
    agent_4: list[int]


class BugAssignments(BaseModel):
    """Bug assignments for all treatment types."""

    explicit: BugAssignment
    autonomous: None = None  # Lead decides


class TreatmentConfig(BaseModel):
    """Complete treatment configuration."""

    treatments: list[Treatment]
    bug_assignments: BugAssignments
    correlation_pairs: list[CorrelationPair]


# --- Run Models ---


class RunMetadata(BaseModel):
    """Metadata for a single treatment × bug execution run."""

    treatment_id: int | str
    bug_id: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    wall_clock_seconds: float | None = None
    session_id: str | None = None
    model: str | None = None
    num_turns: int | None = None
    total_cost_usd: float | None = None
    exit_code: int | None = None
    mode: ExecutionMode


class RunResult(BaseModel):
    """Result of a single treatment × bug execution run."""

    raw_output_path: Path | None = None
    result_text: str | None = None
    patch_path: Path | None = None
    metadata: RunMetadata


# --- Score Models ---


class Tier1Score(BaseModel):
    """Tier 1: Objective automated scoring."""

    bug_id: int
    treatment_id: int | str
    patch_applies: bool
    existing_tests_pass: bool
    reproduction_fixed: bool
    no_regressions: bool
    token_cost_usd: float | None = None
    wall_clock_minutes: float | None = None

    @property
    def all_pass(self) -> bool:
        return (
            self.patch_applies
            and self.existing_tests_pass
            and self.reproduction_fixed
            and self.no_regressions
        )


class Tier2Score(BaseModel):
    """Tier 2: Human-scored diagnostic rubric."""

    bug_id: int
    treatment_id: int | str
    localization: int = Field(ge=0, le=2)
    root_cause: int = Field(ge=0, le=2)
    fix_direction: int = Field(ge=0, le=2)
    confidence_calibration: int = Field(ge=0, le=2)

    @property
    def total(self) -> int:
        return (
            self.localization
            + self.root_cause
            + self.fix_direction
            + self.confidence_calibration
        )


class Tier25Score(BaseModel):
    """Tier 2.5: Consensus and groupthink analysis for a bug."""

    bug_id: int
    cross_treatment_agreement: float = Field(ge=0.0, le=1.0)
    within_team_agreement: float | None = Field(default=None, ge=0.0, le=1.0)
    groupthink_flag: bool = False
    diagnosis_cluster: str | None = None


class Tier3Score(BaseModel):
    """Tier 3: Correlation discovery for a pair in a treatment."""

    pair_name: str
    treatment_id: int | str
    connection_identified: bool
    connection_correct: bool | None = None
    discovery_mechanism: str | None = None
    connection_depth: str | None = None  # "surface" or "specific"
