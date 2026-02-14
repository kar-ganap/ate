# Phase 1 Retro: Invocation Validation + Ruff Integration + Bug Verification

## What Worked

- **Invocation smoke tests gated everything**: All 3 tests (subagent via `claude -p`,
  agent definition loading, agent team formation + peer messaging) passed before any
  Ruff work began. This validated the execution mechanisms the experiment depends on.
- **Peer-to-peer messaging evidence**: Grounded proof in system-generated `SendMessage`
  routing metadata, not agent-written log files. The distinction matters — agents can
  fabricate log entries but can't fabricate routing metadata.
- **Bug swap protocol worked**: #17010 (server panic) was fixed in v0.14.14. Detected
  during verification, swapped for backup #22494 (formatter range formatting) per
  documented rules. experiment-design.md Change Log updated. Clean process.
- **Reproduction edge cases documented**: Three bugs required non-obvious setup that
  became gotchas in CLAUDE.md — valuable for the experiment operator (future self).

## Surprises

- **#17010 fixed in the pinned version**: The bug was open when selected but fixed
  in v0.14.14 — the exact version we pinned. This validated the backup bug strategy.
- **Reproduction fragility**: 3 of 8 bugs needed specific conditions beyond "run ruff
  on this file":
  - #20945: Types must be undefined (no imports) + `--preview` flag
  - #22221: Requires package structure (`foo/__init__.py` with submodule imports)
  - #4384: Requires `ruff.toml` with `max-complexity = 3`
- **Async message delivery**: Agent team teammates can go idle before queued messages
  arrive. Team-lead had to "nudge" the Reviewer to process the Analyst's message.
  This is an operational consideration for interactive treatments.
- **`--max-budget-usd` flag**: Discovered in `claude --help` during smoke tests.
  Available for `-p` mode as an alternative to `--max-turns`.

## Deviations from Plan

- **Two commits instead of one**: Phase shipped in two commits (partial: invocation +
  Ruff integration, then complete: bug verification + integration tests). The partial
  commit was necessary because bug verification depended on Ruff being built.
- **Smoke test scripts created but not CI-integrated**: `scripts/smoke_test_*.sh` are
  manual run scripts, not automated tests. Acceptable since they require live Claude
  access and API costs.

## Implicit Assumptions Made Explicit

- **Bug reproduction is non-trivial**: Assumed bugs would reproduce with minimal setup.
  Reality: specific file structures, config files, and CLI flags are often required.
  Each reproduction case is now documented in `config/bugs.yaml` and
  `scripts/verify_bugs.py`.
- **Agent team message delivery is async**: Assumed messages would be synchronous
  (send → immediate delivery). Reality: messages queue and agents may exit their turn
  before processing. Experiment protocol should account for nudging idle agents.
- **`ruff.toml` format**: Uses flat `[lint.mccabe]` format, NOT `[tool.ruff.lint.mccabe]`.
  The `[tool.ruff.*]` format is only for `pyproject.toml` embedding.

## Scope Changes for Next Phase

None. Phase 2 proceeded as planned (execution harness), though mid-phase it expanded
to include a major experiment design revision (Treatment 0 → interactive).

## Metrics

| Metric | Value |
|--------|-------|
| Files created | 10 (commit 1) + 4 (commit 2) |
| Lines added | 535 + 484 = 1,019 |
| Unit tests added | 11 (45 → 56) |
| Integration tests added | 2 |
| Total tests | 58 |
| Bugs verified | 8/8 (after 1 swap) |
| Bug swaps | 1 (#17010 → #22494) |
| Smoke tests | 3/3 pass |
| Commits | 2 |
