# Phase 3 Retro: Scoring Infrastructure

## What Worked

- **TDD caught a test design error, not an implementation bug**: `test_saves_score`
  expected `data["bug_id"]` (dict) but `record_tier2_score` stores a list to support
  appending multiple treatments per bug. The fix was `data[0]["bug_id"]`. This is
  exactly what the RED→GREEN cycle is for — validating that tests match the intended
  storage format before implementation.
- **Extraction from verify_bugs.py was trivial**: The original script had clean
  separation (data definitions, check functions, orchestration). Refactoring into
  an importable module took ~5 minutes with zero behavioral changes. Good structure
  in Phase 1 paid dividends in Phase 3.
- **Dict keyed by bug_id was a natural improvement**: Switching from `REPROS: list`
  to `REPRO_CASES: dict[int, BugReproCase]` emerged naturally from the scoring use
  case (look up one bug, not iterate all). The new consumer drove a better data
  structure.
- **All RED→GREEN transitions succeeded on first implementation pass** (except the
  one test design error above). 63 new tests, all green without implementation
  rework.

## Surprises

- **None.** Unlike Phase 2 (5 confounds discovered mid-phase), Phase 3 was pure
  infrastructure. No experimental design implications, no protocol changes, no
  deviations from plan. This is the first phase with zero surprises.

## Design Smells Noted (Not Fixed)

- **`check_range_format_bug` is a special case**: It's the only check function
  needing a `file_path` parameter (checks file content after formatting, not
  subprocess output). This creates an `if case.check_fn == "check_range_format_bug"`
  branch in `run_repro()`. Not worth refactoring now (only 5 check functions), but
  worth noting if check functions proliferate.
- **`tier1.py` duplicates `ruff.py` patterns**: `rebuild_ruff()` in tier1.py calls
  `cargo build` directly instead of reusing `build_ruff()` from `ruff.py`. Reason:
  `ruff.py`'s version raises `RuntimeError` on failure, while scoring needs a bool.
  The duplication is 5 lines — not worth an abstraction.

## Deviations from Plan

- **Test count slightly higher than estimated**: Plan estimated ~35 new tests,
  actual is 63 (9 persistence + 23 reproduction + 16 tier1 + 11 tier2 + 4 CLI).
  The reproduction module had more surface area to test than expected (5 check
  functions × positive/negative cases + setup_repro variants).
- **`score_all()` function dropped**: Plan included a `score_all()` function to
  loop over all treatment × bug pairs. Implemented the loop directly in the CLI
  command instead — a standalone function added no value since the CLI is the only
  consumer.

## Metrics

| Metric | Value |
|--------|-------|
| Files created | 10 (4 source, 5 test, 1 plan) |
| Files modified | 4 (cli.py, verify_bugs.py, scoring/__init__.py, CLAUDE.md) |
| New unit tests | 63 |
| Total tests | 164 (162 unit + 2 integration) |
| CLI commands added | 4 (tier1, tier2, tier2-scaffold, status) |
| Scoring modules | 4 (persistence, reproduction, tier1, tier2) |
| Design surprises | 0 |
| Deviations from plan | 2 minor |
