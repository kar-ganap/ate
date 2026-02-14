"""Execution harness for running treatments and capturing data."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ate.models import Bug, ExecutionMode, RunMetadata, RunResult, Treatment
from ate.ruff import RUFF_TAG, get_ruff_binary, get_ruff_version


class PreflightError(Exception):
    """Raised when pre-flight checks fail."""


# ---------------------------------------------------------------------------
# Directory management
# ---------------------------------------------------------------------------


def get_run_dir(
    treatment_id: int | str,
    bug_id: int,
    *,
    base_dir: Path | None = None,
) -> Path:
    """Create and return the run directory for a treatment × bug pair."""
    base = base_dir or Path("data/transcripts")
    run_dir = base / f"treatment-{treatment_id}" / f"bug-{bug_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def get_patch_path(
    treatment_id: int | str,
    bug_id: int,
    *,
    base_dir: Path | None = None,
) -> Path:
    """Return the patch file path for a treatment × bug pair."""
    base = base_dir or Path("data/patches")
    patch_dir = base / f"treatment-{treatment_id}"
    patch_dir.mkdir(parents=True, exist_ok=True)
    return patch_dir / f"bug-{bug_id}.patch"


def save_metadata(metadata: dict[str, Any], run_dir: Path) -> Path:
    """Write metadata dict as JSON to run_dir/metadata.json."""
    path = run_dir / "metadata.json"
    path.write_text(json.dumps(metadata, indent=2, default=str))
    return path


# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------


def preflight_check(
    ruff_dir: Path,
    bug_id: int | None = None,
) -> list[str]:
    """Run pre-flight checks. Returns list of issues (empty = good)."""
    issues: list[str] = []

    binary = get_ruff_binary(ruff_dir)
    if not binary.exists():
        issues.append(f"Ruff binary not found at {binary}")
        return issues  # Can't check version without binary

    try:
        version = get_ruff_version(ruff_dir)
        if version != RUFF_TAG:
            issues.append(
                f"Ruff version mismatch: expected {RUFF_TAG}, got {version}"
            )
    except RuntimeError as e:
        issues.append(f"Failed to get Ruff version: {e}")

    return issues


# ---------------------------------------------------------------------------
# Treatment 0: Prompt rendering and execution
# ---------------------------------------------------------------------------

TREATMENT_0_PROMPT_TEMPLATE = """\
You are a bug investigator for the Ruff Python linter (a Rust codebase).
Your task is to investigate, diagnose, and fix a specific bug.

## Bug Details

- **Bug ID**: {bug_id}
- **Rule**: {rule}
- **Title**: {title}
- **URL**: {url}
- **Category**: {category}
- **Complexity**: {complexity}

## Reproduction

```
{reproduction}
```

## Instructions

1. Read the bug report at the URL above to understand the issue.
2. Explore the Ruff source code in `data/ruff/` to locate the relevant code.
3. Diagnose the root cause of the bug.
4. Write a fix and save it as a patch file at `{patch_path}`.

## Important

- The Ruff source code is at `data/ruff/` (Rust codebase).
- Generate a patch with `git diff` from the `data/ruff/` directory.
- Save your diagnosis and reasoning as you go.
- Focus on correctness — a correct diagnosis with no fix is better than a wrong fix.
"""


def render_treatment0_prompt(bug: Bug, patch_path: Path) -> str:
    """Render the Treatment 0 prompt template with bug details."""
    return TREATMENT_0_PROMPT_TEMPLATE.format(
        bug_id=bug.id,
        rule=bug.rule,
        title=bug.title,
        url=bug.url,
        category=bug.category,
        complexity=bug.complexity,
        reproduction=bug.reproduction,
        patch_path=patch_path,
    )


def build_treatment0_command(
    prompt: str,
    max_turns: int,
    model: str,
    allowed_tools: list[str] | None = None,
) -> list[str]:
    """Build the `claude -p` command list for Treatment 0."""
    cmd = [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "json",
        "--max-turns",
        str(max_turns),
        "--model",
        model,
    ]
    if allowed_tools:
        cmd.extend(["--allowedTools", ",".join(allowed_tools)])
    return cmd


def run_treatment0(
    bug: Bug,
    *,
    ruff_dir: Path,
    max_turns: int,
    timeout: int,
    model: str,
    dry_run: bool,
    transcripts_dir: Path | None = None,
    patches_dir: Path | None = None,
) -> RunResult | None:
    """Run Treatment 0 for a single bug.

    Returns RunResult on execution, None on dry_run.
    Raises PreflightError if pre-flight checks fail.
    """
    issues = preflight_check(ruff_dir, bug_id=bug.id)
    if issues:
        raise PreflightError("\n".join(issues))

    t_dir = transcripts_dir or Path("data/transcripts")
    p_dir = patches_dir or Path("data/patches")

    run_dir = get_run_dir(0, bug.id, base_dir=t_dir)
    patch_path = get_patch_path(0, bug.id, base_dir=p_dir)
    prompt = render_treatment0_prompt(bug, patch_path)
    cmd = build_treatment0_command(prompt, max_turns=max_turns, model=model)

    if dry_run:
        print(f"[DRY RUN] Would execute: {' '.join(cmd[:5])}...")
        print(f"[DRY RUN] Run dir: {run_dir}")
        print(f"[DRY RUN] Patch path: {patch_path}")
        return None

    started_at = datetime.now(tz=UTC)
    exit_code: int | None = None
    stdout = ""

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout = result.stdout
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        exit_code = -1

    completed_at = datetime.now(tz=UTC)
    wall_clock = (completed_at - started_at).total_seconds()

    # Parse JSON output
    session_id = None
    num_turns = None
    cost_usd = None
    result_text = None
    try:
        parsed = json.loads(stdout)
        session_id = parsed.get("session_id")
        num_turns = parsed.get("num_turns")
        cost_usd = parsed.get("cost_usd")
        result_text = parsed.get("result")
    except (json.JSONDecodeError, TypeError):
        result_text = stdout if stdout else None

    # Save raw output
    raw_output_path = run_dir / "raw_output.json"
    raw_output_path.write_text(stdout or "{}")

    metadata = RunMetadata(
        treatment_id=0,
        bug_id=bug.id,
        started_at=started_at,
        completed_at=completed_at,
        wall_clock_seconds=wall_clock,
        session_id=session_id,
        model=model,
        num_turns=num_turns,
        total_cost_usd=cost_usd,
        exit_code=exit_code,
        mode=ExecutionMode.PROGRAMMATIC,
    )

    save_metadata(metadata.model_dump(), run_dir)

    return RunResult(
        raw_output_path=raw_output_path,
        result_text=result_text,
        patch_path=patch_path,
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Interactive treatments: scaffolding
# ---------------------------------------------------------------------------


def get_opening_prompt(treatment: Treatment, bug: Bug) -> str:
    """Generate the opening prompt based on prompt_specificity."""
    if treatment.dimensions.prompt_specificity == "detailed":
        return (
            f"Investigate Ruff bug #{bug.id}: {bug.title}\n"
            f"URL: {bug.url}\n"
            f"Rule: {bug.rule} | Category: {bug.category} | "
            f"Complexity: {bug.complexity}\n\n"
            f"Reproduction:\n{bug.reproduction}\n"
            f"The Ruff source is in data/ruff/. "
            f"Diagnose the root cause and propose a fix."
        )
    # Vague
    return (
        f"There's a bug in Ruff (#{bug.id}). "
        f"See {bug.url} for details. "
        f"The source is in data/ruff/."
    )


def render_session_guide(
    treatment: Treatment,
    bug: Bug,
    assignment_text: str,
    run_dir: Path,
) -> str:
    """Render a human-readable session guide for interactive treatments."""
    comm = treatment.dimensions.communication
    comm_guidance = ""
    if comm == "encourage":
        comm_guidance = (
            "\n## Communication Guidance\n\n"
            "**Encourage** agents to communicate with each other. When forming the team,\n"
            "tell agents: 'You should actively share findings, ask questions of your\n"
            "teammates, and collaborate on diagnosis.'\n"
        )
    elif comm == "discourage":
        comm_guidance = (
            "\n## Communication Guidance\n\n"
            "**Discourage** inter-agent communication. When forming the team,\n"
            "tell agents: 'Work independently. Do not message other agents.\n"
            "Report findings only to the team lead.'\n"
        )

    opening = get_opening_prompt(treatment, bug)

    return f"""\
# Session Guide: Treatment {treatment.id} — Bug #{bug.id}

## Treatment Config

- **Label**: {treatment.label}
- **Decomposition**: {treatment.dimensions.decomposition}
- **Prompt Specificity**: {treatment.dimensions.prompt_specificity}
- **Team Size**: {treatment.dimensions.team_size}
- **Communication**: {treatment.dimensions.communication or 'N/A'}
- **Execution Mode**: {treatment.execution.mode}
- **Soft Budget**: {treatment.execution.soft_budget or 'N/A'}

## Bug Details

- **ID**: {bug.id}
- **Rule**: {bug.rule}
- **Title**: {bug.title}
- **URL**: {bug.url}
- **Category**: {bug.category}
- **Complexity**: {bug.complexity}

## Assignment

{assignment_text}
{comm_guidance}
## Opening Prompt

```
{opening}
```

## Data Collection Checklist

- [ ] Session transcript saved (automatic for agent teams)
- [ ] Notes recorded in `notes.md`
- [ ] Patch saved (if fix produced)
- [ ] metadata.json reviewed

## Run Directory

`{run_dir}`
"""


def scaffold_interactive_run(
    treatment: Treatment,
    bug: Bug,
    bug_assignments: str,
    *,
    transcripts_dir: Path | None = None,
) -> Path:
    """Create session scaffolding for an interactive treatment run."""
    t_dir = transcripts_dir or Path("data/transcripts")
    run_dir = get_run_dir(treatment.id, bug.id, base_dir=t_dir)

    # Session guide (always overwritten)
    guide = render_session_guide(treatment, bug, bug_assignments, run_dir)
    (run_dir / "session_guide.md").write_text(guide)

    # Notes placeholder (never overwritten)
    notes_path = run_dir / "notes.md"
    if not notes_path.exists():
        notes_path.write_text(
            f"# Notes: Treatment {treatment.id} — Bug #{bug.id}\n\n"
        )

    # Metadata
    metadata = RunMetadata(
        treatment_id=treatment.id,
        bug_id=bug.id,
        mode=ExecutionMode.INTERACTIVE,
    )
    save_metadata(metadata.model_dump(), run_dir)

    return run_dir
