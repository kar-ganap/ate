"""CLI entry point for ate."""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer

from ate.config import load_bugs, load_treatments
from ate.ruff import RUFF_TAG, build_ruff, get_ruff_version

app = typer.Typer(help="Agent Teams Eval — compare Claude Code Agent Teams vs Subagents")
bugs_app = typer.Typer(help="Bug portfolio management")
treatments_app = typer.Typer(help="Treatment configuration")
ruff_app = typer.Typer(help="Ruff integration")
app.add_typer(bugs_app, name="bugs")
app.add_typer(treatments_app, name="treatments")
app.add_typer(ruff_app, name="ruff")

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
    typer.echo("Bug verification not yet implemented (needs reproduction cases).")
    typer.echo("Run scripts/verify_bugs.py when ready.")
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
