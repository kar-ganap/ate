# Agent Teams Eval (ate)

Experimental comparison of Claude Code Agent Teams vs Subagents for bug triage
and fix on the [Ruff](https://github.com/astral-sh/ruff) Python linter.

See `docs/experiment-design.md` for the full experiment protocol.

## Quick Start

```bash
uv sync --group dev
uv run ate bugs list
uv run ate treatments list
```

## Validation Gates

```bash
make test       # Unit tests
make test-int   # Integration tests (requires built Ruff)
make lint       # Ruff linter
make typecheck  # mypy strict
```
