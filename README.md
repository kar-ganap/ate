# Agent Teams Eval (ate)

Experimental comparison of Claude Code with Agent Teams (symmetric peers) vs
default Claude Code (hub-and-spoke subagents) for bug triage and fix on the
[Ruff](https://github.com/astral-sh/ruff) Python linter (Rust codebase).

**Key finding:** Ceiling effect — Claude Opus 4.6 solves all 8 bugs (8/8) in
under 10 minutes regardless of treatment condition. Zero peer-to-peer
communication observed across all team treatments. Agent Teams functions as a
parallelism engine, not a collaboration tool, for tasks within the model's
capability frontier.

First in the [ate-series](https://github.com/kar-ganap/ate-series). Successors:
[ate-features](https://github.com/kar-ganap/ate-features) (feature implementation),
[ate-arch](https://github.com/kar-ganap/ate-arch) (architecture design).

## Results at a Glance

| Treatment | Fix Rate | Mean Time | Peer Messages |
|-----------|----------|-----------|---------------|
| 0b (solo control) | 8/8 | 49 min | N/A |
| 2a (2-agent team) | 8/8 | 16 min | 0 |
| 5 (max parallelism) | 8/8 | 9.5 min | 0 |

See [findings](docs/findings.md) for full analysis and
[experiment-design.md](docs/experiment-design.md) for the protocol.

## Quick Start

```bash
uv sync --group dev
uv run ate bugs list
uv run ate treatments list
```

## Built On

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) — agentic coding tool
- [Agent Teams & Subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents) — the multi-agent infrastructure under study

## Validation Gates

```bash
make test       # Unit tests (162)
make test-int   # Integration tests (requires built Ruff)
make lint       # Ruff linter
make typecheck  # mypy strict
```
