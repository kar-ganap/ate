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
│   ├── bugs.yaml              # Round-aware: round1 (8+4 bugs), round2 (TBD)
│   ├── treatments.yaml        # 8 treatments (0a, 0b, 1, 2a, 2b, 3, 4, 5)
│   └── screening_candidates.yaml  # Round 2 candidate bugs for screening
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

**Round 2 screening infrastructure ready.** Config restructured to round-aware
format (`round1:`/`round2:` in `config/bugs.yaml`). Bug model has `round` field.
BugPortfolio supports `get_round()` with backward-compat `primary`/`backup`
properties. 16 screening candidates in `config/screening_candidates.yaml`
(4 Tier A, 4 Tier B, 8 Tier C). Round 2 Ruff pin: v0.15.1.

Round 1 complete (3 of 8 treatments). Treatments 0b, 2a, 5 executed on all
8 primary bugs. Ceiling effect confirmed: 8/8, zero inter-agent communication.
4 PRs submitted to astral-sh/ruff (#23294, #23296, #23297, #23299).

Next: Re-pin Ruff to v0.15.1, then screen candidates interactively (~30 min each).
Target ~8 bugs where Claude fails or takes 30+ min.

Scoring infrastructure (Phase 3) complete: Tier 1 automated pipeline, Tier 2
human scoring scaffolding. 176 unit + 2 integration tests.

## Phases

| Phase | Branch | Status |
|-------|--------|--------|
| 0 | `phase-0-skeleton` | Complete |
| 1 | `phase-1-ruff` | Complete |
| 2 | `phase-2-execution` | Complete |
| 3 | `phase-3-scoring` | Complete |
| R1 | `round1-learnings` | Complete |
| R2-screen | `round2-screening` | In Progress |
| 4 | `phase-4-advanced-scoring` | Pending (blocked on Round 2) |
| 5 | `phase-5-analysis` | Pending (blocked on Round 2) |

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
- **Ceiling effect**: All 8 primary bugs solved 8/8 by Claude Opus 4.6 in <10 min
  regardless of treatment. Bugs rated "hard" by humans are easy for the model.
- **Communication verification**: Only `SendMessage(recipient=<peer-agent>)` with
  system routing metadata counts as inter-agent communication. Agent-written logs
  are NOT evidence. Established in Phase 1, validated in Round 1.
- **Zero communication**: Both team treatments (2a, 5) had zero peer-to-peer
  SendMessage calls. Explicit encouragement ("share findings with teammates!")
  had no effect. Agent Teams = parallelism engine on easy bugs.
- **JSONL transcript path**: Has `-ate` suffix:
  `~/.claude/projects/-Users-kartikganapathi-Documents-Personal-random-projects-others-projects-checkout-ate/`
- **git clean needed after patches**: `git -C data/ruff checkout .` doesn't remove
  untracked files (test fixtures, snapshots). Use `git -C data/ruff clean -fd` too.
- **work/ directory**: Used for PR prep (fork clone). Gitignored, separate from
  experiment's data/ruff/.
- **Round-aware config**: `config/bugs.yaml` uses `round1:`/`round2:` top-level keys.
  Each round has `ruff_pin`, `primary`, `backup`. `BugPortfolio.primary`/`.backup`
  properties aggregate across all rounds for backward compatibility. Use
  `portfolio.get_round(n)` for round-specific access.
- **RUFF_TAG in ruff.py**: Still hardcoded to `0.14.14` (Round 1). Must be updated
  to `0.15.1` before Round 2 screening. The `ruff_pin` in bugs.yaml is the source
  of truth per round; `RUFF_TAG` is for the pin script and preflight checks.
