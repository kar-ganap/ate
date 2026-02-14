# Phase 3: Scoring Infrastructure

## Goal

Build the scoring infrastructure needed to evaluate experiment results.
Covers Tier 1 (fully automated) and Tier 2 (human-scored with scaffolding).
Tiers 2.5, 3, 4, 5 deferred to Phase 4.

## Context

Phases 0-2 built the experiment skeleton, Ruff integration, and execution harness.
Phase 3 builds the tools used after execution. The experiment itself (running 8
treatments × 8 bugs) hasn't been executed yet.

## Key Design Decisions

1. **Reproduction module extracted from verify_bugs.py**: `scripts/verify_bugs.py`
   had all reproduction logic but wasn't importable. Created
   `src/ate/scoring/reproduction.py` with `BugReproCase` dataclass, `REPRO_CASES`
   dict, check functions, `run_repro()`, and `is_fixed()`. The script now imports
   from the module.

2. **Tier 1 pipeline**: For each (treatment, bug) pair with a patch: apply patch →
   rebuild Ruff → check reproduction fixed → run tests → revert. Each patch scored
   independently with Ruff reset between every patch.

3. **Tier 2 scoring guides per bug**: Generates one guide per bug (all treatments
   together) to reduce anchoring bias. Human scores using the rubric (localization,
   root cause, fix direction, confidence — 0-2 each).

4. **Per-bug JSON storage for Tier 2**: Scores stored as JSON arrays at
   `data/scores/tier2/bug-{id}.json`, supporting incremental scoring.

5. **No new dependencies**: All Tier 1 operations use subprocess (git, cargo).
   Tier 2 uses typer prompts. Persistence uses stdlib json.

## Files Created

| File | Purpose |
|------|---------|
| `src/ate/scoring/persistence.py` | Generic score save/load utilities |
| `src/ate/scoring/reproduction.py` | Bug reproduction cases + check functions |
| `src/ate/scoring/tier1.py` | Tier 1 automated scoring pipeline |
| `src/ate/scoring/tier2.py` | Tier 2 human scoring scaffolding + persistence |
| `tests/unit/test_scoring_persistence.py` | 9 tests |
| `tests/unit/test_scoring_reproduction.py` | 23 tests |
| `tests/unit/test_scoring_tier1.py` | 16 tests |
| `tests/unit/test_scoring_tier2.py` | 11 tests |
| `tests/unit/test_cli_score.py` | 4 tests |
| `docs/phases/phase-3-plan.md` | This file |

## Files Modified

| File | Change |
|------|--------|
| `src/ate/scoring/__init__.py` | Added docstring |
| `src/ate/cli.py` | Added `score` sub-app (tier1, tier2, tier2-scaffold, status) |
| `scripts/verify_bugs.py` | Refactored to import from `ate.scoring.reproduction` |
| `CLAUDE.md` | Updated phase status |

## CLI Commands

| Command | Purpose |
|---------|---------|
| `ate score tier1 [--bug-id ID] [--treatment-id ID] [--dry-run]` | Run Tier 1 automated scoring |
| `ate score tier2 <bug_id> <treatment_id>` | Record a Tier 2 human score |
| `ate score tier2-scaffold` | Generate Tier 2 scoring guides |
| `ate score status` | Show scoring completion status |

## Acceptance Criteria

- `make test` — 164 tests pass (99 existing + 63 new + 2 integration)
- `make lint` — clean
- `make typecheck` — clean
- `scripts/verify_bugs.py` still imports and works after refactor
- `uv run ate score status` — shows empty grid (no experiment data yet)
- `uv run ate score tier2-scaffold` — generates 8 scoring guides
- `uv run ate score tier1 --dry-run` — reports "no patches found"
