"""Tier 1: Automated scoring pipeline.

Applies patches, rebuilds Ruff, checks reproduction and test suites.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ate.models import Tier1Score
from ate.scoring.reproduction import is_fixed


def apply_patch(patch_path: Path, ruff_dir: Path) -> bool:
    """Apply a patch file with git apply. Returns True if successful."""
    if not patch_path.exists():
        return False
    result = subprocess.run(
        ["git", "apply", str(patch_path)],
        cwd=ruff_dir,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def revert_ruff(ruff_dir: Path) -> None:
    """Reset Ruff source to clean pinned state."""
    subprocess.run(
        ["git", "checkout", "."],
        cwd=ruff_dir,
        capture_output=True,
        text=True,
    )


def rebuild_ruff(ruff_dir: Path) -> bool:
    """Rebuild Ruff after patch. Returns True if build succeeds."""
    result = subprocess.run(
        ["cargo", "build"],
        cwd=ruff_dir,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def check_tests_pass(ruff_dir: Path) -> bool:
    """Run cargo test. Returns True if all pass."""
    result = subprocess.run(
        ["cargo", "test"],
        cwd=ruff_dir,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def extract_cost_and_time(
    data_dir: Path,
    treatment_id: int | str,
    bug_id: int,
) -> tuple[float | None, float | None]:
    """Extract token cost and wall-clock minutes from metadata.json."""
    meta_path = (
        data_dir
        / "transcripts"
        / f"treatment-{treatment_id}"
        / f"bug-{bug_id}"
        / "metadata.json"
    )
    if not meta_path.exists():
        return None, None

    meta = json.loads(meta_path.read_text())
    cost = meta.get("total_cost_usd")
    seconds = meta.get("wall_clock_seconds")
    minutes = seconds / 60.0 if seconds is not None else None
    return cost, minutes


def score_bug(
    treatment_id: int | str,
    bug_id: int,
    ruff_dir: Path,
    patches_dir: Path,
    data_dir: Path,
) -> Tier1Score:
    """Score a single treatment x bug pair. Full Tier 1 pipeline."""
    patch_path = patches_dir / f"treatment-{treatment_id}" / f"bug-{bug_id}.patch"
    cost, minutes = extract_cost_and_time(data_dir, treatment_id, bug_id)

    if not patch_path.exists():
        return Tier1Score(
            bug_id=bug_id,
            treatment_id=treatment_id,
            patch_applies=False,
            existing_tests_pass=False,
            reproduction_fixed=False,
            no_regressions=False,
            token_cost_usd=cost,
            wall_clock_minutes=minutes,
        )

    patch_ok = apply_patch(patch_path, ruff_dir)
    if not patch_ok:
        revert_ruff(ruff_dir)
        return Tier1Score(
            bug_id=bug_id,
            treatment_id=treatment_id,
            patch_applies=False,
            existing_tests_pass=False,
            reproduction_fixed=False,
            no_regressions=False,
            token_cost_usd=cost,
            wall_clock_minutes=minutes,
        )

    build_ok = rebuild_ruff(ruff_dir)
    if not build_ok:
        revert_ruff(ruff_dir)
        return Tier1Score(
            bug_id=bug_id,
            treatment_id=treatment_id,
            patch_applies=True,
            existing_tests_pass=False,
            reproduction_fixed=False,
            no_regressions=False,
            token_cost_usd=cost,
            wall_clock_minutes=minutes,
        )

    reproduction_fixed = is_fixed(bug_id, ruff_dir)
    tests_pass = check_tests_pass(ruff_dir)

    revert_ruff(ruff_dir)

    return Tier1Score(
        bug_id=bug_id,
        treatment_id=treatment_id,
        patch_applies=True,
        existing_tests_pass=tests_pass,
        reproduction_fixed=reproduction_fixed,
        no_regressions=tests_pass,
        token_cost_usd=cost,
        wall_clock_minutes=minutes,
    )
