# Phase 0 Retro: Skeleton + Models + Docs

## What Worked

- **Single-commit delivery**: Entire scaffold (29 files, 3020 lines) shipped in one
  clean commit. No partial states, no fixups.
- **TDD from day one**: 45 tests written before/alongside code. All gates (test, lint,
  mypy strict) clean from the first commit.
- **Pydantic models as the source of truth**: 13 models + 8 enums cover the full
  experiment surface (bugs, treatments, scores across all 5 tiers). Config loading
  validates against these models — invalid YAML fails fast with clear errors.
- **Experiment design doc as north star**: Writing the full design doc before any code
  forced clarity on dimensions, treatments, scoring tiers, and key comparisons. This
  investment paid off in later phases.
- **Process doc**: Codifying PLAN → TEST → IMPLEMENT → RETRO upfront set expectations
  for every phase.

## Surprises

- **Model count**: 13 models + 8 enums for what seemed like a simple experiment. The
  5-tier scoring framework (Tier 1 through Tier 5) and the treatment dimensions drove
  most of the complexity.
- **Treatment ID polymorphism**: Treatment IDs need to be `int | str` to support both
  numeric (1, 5) and string ("0a", "2a", "2b") identifiers. This was anticipated in
  the model but became important later when Treatment 0 was split.

## Deviations from Plan

None. All deliverables shipped as specified. Plan was appropriately scoped.

## Implicit Assumptions Made Explicit

- **"Subagents" framing**: The original hypothesis compared "Agent Teams vs Subagents."
  This framing assumed Treatment 0 would use `claude -p` (programmatic subagents) as
  the control. Phase 2 later revealed this comparison was flawed — the real question
  is "Agent Teams vs default Claude Code usage," which is a different (and better)
  framing. The Phase 0 models were flexible enough to survive this reframing.
- **pyproject.toml ordering**: `dependencies` must come before `[project.scripts]` in
  the `[project]` table — hatchling gives a confusing error otherwise. Captured as a
  gotcha in CLAUDE.md.

## Scope Changes for Next Phase

None. Phase 1 proceeded as originally planned (invocation validation + Ruff pin +
bug verification).

## Metrics

| Metric | Value |
|--------|-------|
| Files created | 29 |
| Lines added | 3,020 |
| Unit tests | 45 |
| Models | 13 |
| Enums | 8 |
| Config files | 2 (bugs.yaml, treatments.yaml) |
| Commits | 1 |
