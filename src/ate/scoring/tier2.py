"""Tier 2: Human scoring scaffolding and persistence.

Generates scoring guides per bug (all treatments together) to reduce anchoring
bias. Provides functions to record and load human-assigned scores.
"""

from __future__ import annotations

import json
from pathlib import Path

from ate.models import Bug, Tier2Score

RUBRIC = """\
## Rubric (0-2 each)

| Dimension | 0 | 1 | 2 |
|-----------|---|---|---|
| Localization | Wrong file/area | Right area, wrong spot | Exact location |
| Root Cause | Wrong or missing | Partial understanding | Correct root cause |
| Fix Direction | Wrong approach | Viable but suboptimal | Correct fix strategy |
| Confidence Calibration | Overconfident on wrong | Mixed signals | Calibrated correctly |
"""


def generate_scoring_guide(
    bug: Bug,
    treatment_ids: list[int | str],
) -> str:
    """Generate a Tier 2 scoring guide for a bug (all treatments)."""
    lines = [
        f"# Tier 2 Scoring Guide: Bug #{bug.id}",
        "",
        f"**Rule:** {bug.rule}",
        f"**Title:** {bug.title}",
        f"**URL:** {bug.url}",
        f"**Category:** {bug.category.value}",
        f"**Complexity:** {bug.complexity.value}",
        "",
        "## Reproduction",
        "",
        bug.reproduction or "_No reproduction details available._",
        "",
        RUBRIC,
        "",
        "## Treatments to Score",
        "",
    ]

    for tid in treatment_ids:
        lines.append(f"### Treatment {tid}")
        lines.append("")
        lines.append(
            f"Review transcript at: `data/transcripts/treatment-{tid}/bug-{bug.id}/`"
        )
        lines.append("")
        lines.append("| Dimension | Score (0-2) |")
        lines.append("|-----------|-------------|")
        lines.append("| Localization | |")
        lines.append("| Root Cause | |")
        lines.append("| Fix Direction | |")
        lines.append("| Confidence Calibration | |")
        lines.append("")

    return "\n".join(lines)


def scaffold_tier2(
    bugs: list[Bug],
    treatment_ids: list[int | str],
    output_dir: Path,
) -> None:
    """Generate scoring guides (one per bug) into output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for bug in bugs:
        guide = generate_scoring_guide(bug, treatment_ids)
        guide_path = output_dir / f"bug-{bug.id}-guide.md"
        guide_path.write_text(guide)


def record_tier2_score(score: Tier2Score, scores_dir: Path) -> Path:
    """Save a single Tier2Score to the per-bug JSON file."""
    scores_dir.mkdir(parents=True, exist_ok=True)
    path = scores_dir / f"bug-{score.bug_id}.json"

    existing: list[dict[str, object]] = []
    if path.exists():
        existing = json.loads(path.read_text())

    existing.append(score.model_dump())
    path.write_text(json.dumps(existing, indent=2, default=str))
    return path


def load_tier2_scores(
    scores_dir: Path,
    bug_id: int | None = None,
) -> list[Tier2Score]:
    """Load Tier2Scores. If bug_id given, load only that bug's scores."""
    if not scores_dir.exists():
        return []

    if bug_id is not None:
        path = scores_dir / f"bug-{bug_id}.json"
        if not path.exists():
            return []
        data = json.loads(path.read_text())
        return [Tier2Score.model_validate(item) for item in data]

    # Load all bugs
    scores: list[Tier2Score] = []
    for path in sorted(scores_dir.glob("bug-*.json")):
        data = json.loads(path.read_text())
        scores.extend(Tier2Score.model_validate(item) for item in data)
    return scores
