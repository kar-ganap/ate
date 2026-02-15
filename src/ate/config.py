"""Load and validate experiment configuration from YAML files."""

from __future__ import annotations

from pathlib import Path

import yaml

from ate.models import (
    Bug,
    BugAssignment,
    BugAssignments,
    BugPortfolio,
    CorrelationPair,
    ExecutionConfig,
    RoundBugs,
    Treatment,
    TreatmentConfig,
    TreatmentDimensions,
)

DEFAULT_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def load_bugs(config_dir: Path = DEFAULT_CONFIG_DIR) -> BugPortfolio:
    """Load bug portfolio from bugs.yaml.

    Supports round-aware format (round1:/round2: top-level keys).
    """
    bugs_path = config_dir / "bugs.yaml"
    if not bugs_path.exists():
        msg = f"bugs.yaml not found at {bugs_path}"
        raise FileNotFoundError(msg)

    with open(bugs_path) as f:
        raw = yaml.safe_load(f)

    rounds: dict[int, RoundBugs] = {}
    for key, value in raw.items():
        if not key.startswith("round"):
            continue
        round_num = int(key[5:])  # "round1" -> 1
        ruff_pin = value.get("ruff_pin", "")
        primary = [Bug(round=round_num, **bug) for bug in value.get("primary", [])]
        backup = [Bug(round=round_num, **bug) for bug in value.get("backup", [])]
        rounds[round_num] = RoundBugs(
            ruff_pin=ruff_pin,
            primary=primary,
            backup=backup,
        )
    return BugPortfolio(rounds=rounds)


def load_treatments(config_dir: Path = DEFAULT_CONFIG_DIR) -> TreatmentConfig:
    """Load treatment configuration from treatments.yaml."""
    treatments_path = config_dir / "treatments.yaml"
    if not treatments_path.exists():
        msg = f"treatments.yaml not found at {treatments_path}"
        raise FileNotFoundError(msg)

    with open(treatments_path) as f:
        raw = yaml.safe_load(f)

    treatments = []
    for t in raw.get("treatments", []):
        treatments.append(
            Treatment(
                id=t["id"],
                label=t["label"],
                dimensions=TreatmentDimensions(**t["dimensions"]),
                execution=ExecutionConfig(**t["execution"]),
            )
        )

    explicit_raw = raw.get("bug_assignments", {}).get("explicit", {})
    bug_assignments = BugAssignments(
        explicit=BugAssignment(**explicit_raw),
    )

    correlation_pairs = [
        CorrelationPair(**pair) for pair in raw.get("correlation_pairs", [])
    ]

    return TreatmentConfig(
        treatments=treatments,
        bug_assignments=bug_assignments,
        correlation_pairs=correlation_pairs,
    )
