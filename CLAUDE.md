# Agent Teams Eval (ate)

## Overview

Experimental comparison of Claude Code with Agent Teams vs default Claude Code
for bug triage and fix on the Ruff Python linter (Rust codebase). 8 treatments
(including 0a/0b control variants), 8 bugs, 5-tier measurement framework.
All treatments are interactive (no programmatic `claude -p` in core experiment).

## Tech Stack

- Python 3.11+ with uv
- Pydantic for data models
- Typer for CLI
- PyYAML for config
- pytest + ruff + mypy (strict)
- hatchling build backend

## Conventions

- TDD: tests before code, validation gates (`make test`, `make lint`, `make typecheck`)
- No Co-Authored-By in commits
- Phase branches off main, user merges manually
- `docs/experiment-design.md` is the north star — all experiment protocol decisions live there
- Raw data in `data/` (gitignored contents), config in `config/` (committed)
- Dependency groups: core (always), dev (always), scoring (Phase 3+), analysis (Phase 5+)

## Project Structure

```
ate/
├── CLAUDE.md                  # This file (living state)
├── Makefile                   # test, lint, typecheck shortcuts
├── pyproject.toml             # uv + hatchling + ruff + mypy + pytest
├── config/
│   ├── bugs.yaml              # 12 bugs (8 primary + 4 backup)
│   └── treatments.yaml        # 8 treatments (0a, 0b, 1, 2a, 2b, 3, 4, 5)
├── docs/
│   ├── desiderata.md          # Immutable principles
│   ├── process.md             # Phase lifecycle & validation gates
│   ├── experiment-design.md   # THE NORTH STAR
│   └── phases/                # plan + retro per phase
├── data/                      # Raw experiment data (gitignored contents)
├── src/ate/
│   ├── models.py              # Pydantic models
│   ├── config.py              # YAML loading
│   ├── cli.py                 # Typer CLI
│   ├── harness.py             # Execution harness (scaffolding + exploratory Treatment 0)
│   ├── scoring/               # Tiers 1, 2 (reproduction, persistence, tier1, tier2)
│   └── analysis/              # Aggregation, viz, communication
├── tests/
│   ├── unit/                  # Mocked tests
│   └── integration/           # Real Ruff tests
└── scripts/                   # Utility scripts
```

## Key References

- `docs/desiderata.md` — Immutable principles (9 items)
- `docs/process.md` — Phase lifecycle (PLAN → TEST → IMPLEMENT → RETRO)
- `docs/experiment-design.md` — Full experiment protocol

## Current State

Phase 3 complete. Scoring infrastructure implemented: Tier 1 automated pipeline
(apply patch → rebuild → check reproduction → run tests), Tier 2 human scoring
scaffolding (guides per bug, interactive score entry, per-bug JSON persistence).
Reproduction module extracted from `scripts/verify_bugs.py` into
`src/ate/scoring/reproduction.py`. 162 unit tests, 2 integration.

## Phases

| Phase | Branch | Status |
|-------|--------|--------|
| 0 | `phase-0-skeleton` | Complete |
| 1 | `phase-1-ruff` | Complete |
| 2 | `phase-2-execution` | Complete |
| 3 | `phase-3-scoring` | Complete |
| 4 | `phase-4-advanced-scoring` | Pending |
| 5 | `phase-5-analysis` | Pending |

## Known Gotchas

- pyproject.toml: `dependencies` must come before `[project.scripts]` in the
  `[project]` table, otherwise hatchling fails with a confusing error about
  "Object reference `dependencies` of field `project.scripts` must be a string"
- Bug #17010 (server panic, glob braces) was fixed in v0.14.14 — swapped to #22494
  (formatter range formatting). See experiment-design.md Change Log.
- ruff.toml uses flat `[lint.mccabe]` format, NOT `[tool.ruff.lint.mccabe]`
- Bug #20945 repro requires types to be UNDEFINED (no BaseModel subclasses) so
  resolve_name returns None for both → None==None false positive
- Bug #22221 repro requires package structure (foo/__init__.py with submodule imports)
  not simple stdlib imports
- Treatment 0 was originally programmatic (`claude -p`) but introduced 5 confounds
  vs interactive treatments. Revised to interactive 0a/0b. See experiment-design.md
  Change Log for full rationale.
- Autonomous treatments (2a, 2b, 3, 4): if lead co-assigns correlated bug pairs to
  same agent, Tier 3 scores are "structurally advantaged — not comparable"
