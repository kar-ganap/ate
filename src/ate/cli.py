"""CLI entry point for ate."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import typer

from ate.config import load_bugs, load_treatments
from ate.harness import (
    preflight_check,
    scaffold_interactive_run,
)
from ate.models import Tier2Score
from ate.ruff import RUFF_TAG, build_ruff, get_ruff_version
from ate.scoring.tier1 import score_bug
from ate.scoring.tier2 import (
    load_tier2_scores,
    record_tier2_score,
    scaffold_tier2,
)

app = typer.Typer(help="Agent Teams Eval — compare Claude Code Agent Teams vs Subagents")
bugs_app = typer.Typer(help="Bug portfolio management")
treatments_app = typer.Typer(help="Treatment configuration")
ruff_app = typer.Typer(help="Ruff integration")
run_app = typer.Typer(help="Execution harness")
score_app = typer.Typer(help="Scoring infrastructure")
app.add_typer(bugs_app, name="bugs")
app.add_typer(treatments_app, name="treatments")
app.add_typer(ruff_app, name="ruff")
app.add_typer(run_app, name="run")
app.add_typer(score_app, name="score")

DATA_DIR = Path(__file__).parent.parent.parent / "data"
RUFF_DIR = DATA_DIR / "ruff"


@bugs_app.command("list")
def bugs_list(include_backup: bool = typer.Option(False, help="Include backup bugs")) -> None:
    """List bugs in the experiment portfolio."""
    portfolio = load_bugs()

    typer.echo("Primary Bugs:")
    typer.echo("-" * 80)
    for bug in portfolio.primary:
        typer.echo(
            f"  #{bug.id:<6} [{bug.category.value:<22}] "
            f"{bug.complexity.value:<7} {bug.title}"
        )

    if include_backup and portfolio.backup:
        typer.echo()
        typer.echo("Backup Bugs:")
        typer.echo("-" * 80)
        for bug in portfolio.backup:
            replacements = ", ".join(f"#{r}" for r in bug.can_replace)
            typer.echo(
                f"  #{bug.id:<6} [{bug.category.value:<22}] {bug.complexity.value:<7} "
                f"{bug.title}  (can replace: {replacements})"
            )


@treatments_app.command("list")
def treatments_list() -> None:
    """List treatments in the experiment."""
    config = load_treatments()

    typer.echo("Treatments:")
    typer.echo("-" * 90)
    for t in config.treatments:
        d = t.dimensions
        comm = d.communication.value if d.communication else "N/A"
        delegate = str(d.delegate_mode) if d.delegate_mode is not None else "N/A"
        typer.echo(
            f"  {str(t.id):<4} {t.label:<28} "
            f"decomp={d.decomposition.value:<11} "
            f"prompt={d.prompt_specificity.value:<9} "
            f"delegate={delegate:<6} "
            f"size={d.team_size.value:<4} "
            f"comm={comm}"
        )


@ruff_app.command("pin")
def ruff_pin() -> None:
    """Clone and pin Ruff to the experiment version."""
    typer.echo(f"Pinning Ruff to v{RUFF_TAG}...")
    script = Path(__file__).parent.parent.parent / "scripts" / "pin_ruff.sh"
    result = subprocess.run(["bash", str(script)], capture_output=False)
    if result.returncode != 0:
        typer.echo("FAILED to pin Ruff", err=True)
        raise typer.Exit(1)


@ruff_app.command("build")
def ruff_build() -> None:
    """Build Ruff from source."""
    if not (RUFF_DIR / "Cargo.toml").exists():
        typer.echo("Ruff not pinned. Run 'ate ruff pin' first.", err=True)
        raise typer.Exit(1)
    typer.echo("Building Ruff (this may take a few minutes)...")
    build_ruff(RUFF_DIR)
    version = get_ruff_version(RUFF_DIR)
    typer.echo(f"Built Ruff v{version}")


@ruff_app.command("verify")
def ruff_verify() -> None:
    """Verify all primary bugs reproduce against pinned Ruff."""
    script = Path(__file__).parent.parent.parent / "scripts" / "verify_bugs.py"
    result = subprocess.run(["uv", "run", "python", str(script)], capture_output=False)
    if result.returncode != 0:
        raise typer.Exit(1)


@run_app.command("preflight")
def run_preflight() -> None:
    """Run pre-flight checks for the execution harness."""
    issues = preflight_check(RUFF_DIR)
    if issues:
        typer.echo("Pre-flight issues:", err=True)
        for issue in issues:
            typer.echo(f"  - {issue}", err=True)
        raise typer.Exit(1)
    typer.echo("All pre-flight checks passed.")


@run_app.command("scaffold")
def run_scaffold(
    treatment_id: str = typer.Argument(..., help="Treatment ID (e.g., 1, 2a)"),
    bug_id: int = typer.Argument(..., help="Bug ID"),
) -> None:
    """Scaffold an interactive session for a treatment × bug pair."""
    portfolio = load_bugs()
    config = load_treatments()

    bug = portfolio.get_bug(bug_id)
    if bug is None:
        typer.echo(f"Bug #{bug_id} not found", err=True)
        raise typer.Exit(1)

    # Parse treatment_id (could be int or string)
    tid: int | str
    try:
        tid = int(treatment_id)
    except ValueError:
        tid = treatment_id

    treatment = None
    for t in config.treatments:
        if t.id == tid:
            treatment = t
            break

    if treatment is None:
        typer.echo(f"Treatment {treatment_id} not found", err=True)
        raise typer.Exit(1)

    run_dir = scaffold_interactive_run(
        treatment,
        bug,
        bug_assignments=f"Bug #{bug_id}",
    )
    typer.echo(f"Scaffolded: {run_dir}")
    typer.echo("  session_guide.md — review before starting")
    typer.echo("  notes.md — record observations during session")
    typer.echo("  metadata.json — pre-filled metadata")


@run_app.command("status")
def run_status() -> None:
    """Show execution status across all treatments and bugs."""
    transcripts_dir = DATA_DIR / "transcripts"
    if not transcripts_dir.exists():
        typer.echo("No transcripts directory found. No runs yet.")
        return

    portfolio = load_bugs()
    config = load_treatments()

    typer.echo("Execution Status:")
    typer.echo("-" * 70)

    for treatment in config.treatments:
        for bug in portfolio.primary:
            run_dir = transcripts_dir / f"treatment-{treatment.id}" / f"bug-{bug.id}"
            meta_path = run_dir / "metadata.json"
            if meta_path.exists():
                meta = json.loads(meta_path.read_text())
                exit_code = meta.get("exit_code")
                status = "done" if exit_code == 0 else f"exit={exit_code}"
                typer.echo(f"  T{treatment.id:<4} Bug #{bug.id:<6} {status}")
            else:
                typer.echo(f"  T{treatment.id:<4} Bug #{bug.id:<6} pending")


@score_app.command("tier1")
def score_tier1(
    bug_id: int | None = typer.Option(None, help="Score a specific bug"),
    treatment_id: str | None = typer.Option(None, help="Score a specific treatment"),
    dry_run: bool = typer.Option(False, help="Show what would be scored without scoring"),
) -> None:
    """Run Tier 1 automated scoring."""
    portfolio = load_bugs()
    config = load_treatments()
    patches_dir = DATA_DIR / "patches"

    if not patches_dir.exists():
        typer.echo("No patches directory found. No patches to score.")
        return

    pairs: list[tuple[int | str, int]] = []
    for treatment in config.treatments:
        for bug in portfolio.primary:
            if bug_id is not None and bug.id != bug_id:
                continue
            if treatment_id is not None:
                tid: int | str
                try:
                    tid = int(treatment_id)
                except ValueError:
                    tid = treatment_id
                if treatment.id != tid:
                    continue
            patch_path = patches_dir / f"treatment-{treatment.id}" / f"bug-{bug.id}.patch"
            if patch_path.exists():
                pairs.append((treatment.id, bug.id))

    if not pairs:
        typer.echo("No patches found to score.")
        return

    if dry_run:
        typer.echo(f"Would score {len(pairs)} treatment × bug pairs:")
        for tid, bid in pairs:
            typer.echo(f"  Treatment {tid}, Bug #{bid}")
        return

    for tid, bid in pairs:
        typer.echo(f"Scoring Treatment {tid}, Bug #{bid}...")
        result = score_bug(tid, bid, RUFF_DIR, patches_dir, DATA_DIR)
        status = "PASS" if result.all_pass else "FAIL"
        typer.echo(f"  {status}: patch={result.patch_applies} tests={result.existing_tests_pass} "
                   f"fixed={result.reproduction_fixed} regressions={not result.no_regressions}")


@score_app.command("tier2")
def score_tier2_cmd(
    bug_id: int = typer.Argument(..., help="Bug ID to score"),
    treatment_id: str = typer.Argument(..., help="Treatment ID"),
    localization: int = typer.Option(
        ..., prompt=True, min=0, max=2, help="Localization (0-2)",
    ),
    root_cause: int = typer.Option(
        ..., prompt=True, min=0, max=2, help="Root cause (0-2)",
    ),
    fix_direction: int = typer.Option(
        ..., prompt=True, min=0, max=2, help="Fix direction (0-2)",
    ),
    confidence: int = typer.Option(
        ..., prompt=True, min=0, max=2, help="Confidence (0-2)",
    ),
) -> None:
    """Record a Tier 2 human score for a treatment × bug pair."""
    tid: int | str
    try:
        tid = int(treatment_id)
    except ValueError:
        tid = treatment_id

    score = Tier2Score(
        bug_id=bug_id,
        treatment_id=tid,
        localization=localization,
        root_cause=root_cause,
        fix_direction=fix_direction,
        confidence_calibration=confidence,
    )
    scores_dir = DATA_DIR / "scores" / "tier2"
    path = record_tier2_score(score, scores_dir)
    typer.echo(f"Recorded score (total={score.total}/8) at {path}")


@score_app.command("tier2-scaffold")
def score_tier2_scaffold() -> None:
    """Generate Tier 2 scoring guides (one per bug)."""
    portfolio = load_bugs()
    config = load_treatments()
    treatment_ids = [t.id for t in config.treatments]
    output_dir = DATA_DIR / "scores" / "tier2" / "guides"
    scaffold_tier2(portfolio.primary, treatment_ids, output_dir)
    typer.echo(f"Generated {len(portfolio.primary)} scoring guides in {output_dir}")


@score_app.command("status")
def score_status() -> None:
    """Show scoring completion status."""
    portfolio = load_bugs()
    config = load_treatments()

    patches_dir = DATA_DIR / "patches"

    typer.echo("Scoring Status:")
    typer.echo("=" * 70)

    typer.echo("\nTier 1 (Automated):")
    typer.echo("-" * 40)
    patch_count = 0
    for treatment in config.treatments:
        for bug in portfolio.primary:
            patch_path = patches_dir / f"treatment-{treatment.id}" / f"bug-{bug.id}.patch"
            if patch_path.exists():
                patch_count += 1
    total = len(config.treatments) * len(portfolio.primary)
    typer.echo(f"  Patches available: {patch_count}/{total}")

    typer.echo("\nTier 2 (Human):")
    typer.echo("-" * 40)
    scores_dir = DATA_DIR / "scores" / "tier2"
    all_scores = load_tier2_scores(scores_dir)
    scored_pairs = {(s.bug_id, s.treatment_id) for s in all_scores}
    total_pairs = len(config.treatments) * len(portfolio.primary)
    typer.echo(f"  Scored: {len(scored_pairs)}/{total_pairs}")

    guides_dir = scores_dir / "guides"
    if guides_dir.exists():
        guide_count = len(list(guides_dir.glob("*-guide.md")))
        typer.echo(f"  Scoring guides: {guide_count}")
    else:
        typer.echo("  Scoring guides: not generated (run `ate score tier2-scaffold`)")


if __name__ == "__main__":
    app()
