# Phase 0: Skeleton + Models + Docs

## Goal

Create the repo, all scaffolding files, data models, config loading, and the
complete docs suite. No external dependencies beyond Python.

## Deliverables

- GitHub repo initialized with full directory tree
- `CLAUDE.md`, `docs/desiderata.md`, `docs/process.md`
- `docs/experiment-design.md` — migrated and expanded from conversation notes
- `pyproject.toml`, `Makefile`, `.gitignore`
- `src/ate/models.py` — Pydantic models for bugs, treatments, scores
- `config/bugs.yaml` + `config/treatments.yaml` — populated with all 12 bugs
  and 7 treatments
- `src/ate/config.py` — Load and validate YAML configs into Pydantic models
- `src/ate/cli.py` — Skeleton Typer app with `ate bugs list`, `ate treatments list`

## Test Plan

Unit tests only (no external dependencies):

- `test_models.py` — Model validation, serialization, edge cases
  - Bug model accepts valid data, rejects invalid
  - Treatment dimensions validate enum values
  - Score models enforce range constraints (0-2 for Tier 2)
  - Serialization round-trips (model → dict → model)
- `test_config.py` — YAML loading, validation errors
  - Load bugs.yaml → list of Bug models
  - Load treatments.yaml → list of Treatment models
  - Invalid YAML raises clear errors
  - Filter primary vs backup bugs

## Acceptance Criteria

- `make test` — all pass
- `make lint` — clean
- `make typecheck` — clean
- `uv run ate bugs list` — prints 8 primary bugs
- `uv run ate treatments list` — prints 7 treatments
