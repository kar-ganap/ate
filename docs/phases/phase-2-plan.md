# Phase 2: Execution Harness

## Goal

Build the execution harness to scaffold interactive treatments with session guides,
directories, and checklists. All 8 treatments are interactive (no programmatic mode
in the core experiment).

## Context

Phases 0-1 are complete: skeleton, models, config, CLI, Ruff v0.14.14 pinned/built,
8/8 bugs verified, invocation smoke tests passed. Phase 2 builds the bridge between
configuration (Phase 0-1) and scoring (Phase 3).

## Mid-Phase Design Revision

During cost calibration smoke tests, we discovered that programmatic Treatment 0
(`claude -p`) introduced 5 confounds vs interactive Treatments 1-5: execution mode,
budget enforcement, model, tool access, and human presence. Making all treatments
interactive reduces the independent variable to a single clean bit: Agent Teams ON/OFF.

Key changes:
- Treatment 0 split into 0a (Full Context, 1×8) and 0b (Swim Lanes, 8×1)
- All 8 treatments now interactive with identical soft budget constraints
- `run_treatment0()` kept in harness.py for exploratory/supplementary use only
- CLI `treatment0` and `treatment0-all` commands removed from core experiment
- Key comparisons table audited: fixed confounds for 2a vs 3 and 2a vs 4, added
  1 vs 3 (clean decomposition comparison), added design limitations note
- Treatment 0a bug ordering specified (portfolio order, not agent-pair order)
- Protocol now pins Claude Code version and model

See experiment-design.md Change Log for full rationale.

## Key Design Decisions

1. **`str.format()` not Jinja2**: Prompts are simple enough. No new dependency.

2. **Timeout = data, not failure**: If `claude -p` times out (exploratory runs),
   captured as `RunResult` with `exit_code=-1`.

3. **Post-execution extraction is Phase 3**: Harness captures raw output only.
   Patch extraction, diagnosis parsing = Phase 3 (scoring).

4. **Communication guidance in session guides**: For `encourage`/`discourage`
   treatments, the session guide includes specific text for the human.

5. **All treatments interactive**: Eliminates confounds between control and
   agent team treatments. Cost = $0 (all subscription).

## Files Created

- `src/ate/harness.py` — Core execution harness (11 functions + 1 exception + 1 template)
- `tests/unit/test_harness.py` — 32 unit tests
- `tests/unit/test_cli_run.py` — 3 CLI tests
- `docs/phases/phase-2-plan.md` — This file

## Files Modified

- `src/ate/models.py` — Added `RunMetadata`, `RunResult`, `TeamSize.ONE_BY_EIGHT`
- `src/ate/cli.py` — Added `run` sub-app (preflight, scaffold, status)
- `config/treatments.yaml` — Split Treatment 0 into 0a/0b
- `docs/experiment-design.md` — Major revision (interactive Treatment 0, confounds
  audit, Tier 3 protocol, design limitations, model pinning)
- `tests/conftest.py` — Added 4 fixtures, updated sample_treatment_0 to 0b/interactive
- `tests/unit/test_config.py` — Updated for 8 treatments
- `tests/unit/test_models.py` — Added RunMetadata/RunResult tests
- `CLAUDE.md` — Updated phase status, added gotchas

## Harness Functions

| Function | Purpose |
|----------|---------|
| `get_run_dir()` | Create/return `data/transcripts/treatment-{id}/bug-{id}/` |
| `get_patch_path()` | Return `data/patches/treatment-{id}/bug-{id}.patch` |
| `save_metadata()` | Write `metadata.json` to run dir |
| `preflight_check()` | Verify Ruff binary exists and version matches |
| `render_treatment0_prompt()` | Render self-contained prompt (exploratory use) |
| `build_treatment0_command()` | Build `claude -p` command list (exploratory use) |
| `run_treatment0()` | Execute Treatment 0 programmatically (exploratory use) |
| `get_opening_prompt()` | Generate detailed/vague opening prompt |
| `render_session_guide()` | Render human-readable session guide |
| `scaffold_interactive_run()` | Create session_guide.md + notes.md + metadata.json |

## CLI Commands

| Command | Purpose |
|---------|---------|
| `ate run preflight` | Run pre-flight checks |
| `ate run scaffold <treatment_id> <bug_id>` | Scaffold interactive session |
| `ate run status` | Show execution completion grid |

## Acceptance Criteria

- `make test` — 99 unit tests pass
- `make lint` — clean
- `make typecheck` — clean
- `uv run ate run preflight` — all-clear (if Ruff built)
- `uv run ate run scaffold 0a 20945` — creates session files for full-context variant
- `uv run ate run scaffold 0b 20945` — creates session files for swim-lanes variant
- `uv run ate run scaffold 1 20945` — creates session files for structured team
- `uv run ate run status` — shows execution grid
