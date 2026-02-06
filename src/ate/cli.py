"""CLI entry point for ate."""

from __future__ import annotations

import typer

from ate.config import load_bugs, load_treatments

app = typer.Typer(help="Agent Teams Eval — compare Claude Code Agent Teams vs Subagents")
bugs_app = typer.Typer(help="Bug portfolio management")
treatments_app = typer.Typer(help="Treatment configuration")
app.add_typer(bugs_app, name="bugs")
app.add_typer(treatments_app, name="treatments")


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


if __name__ == "__main__":
    app()
