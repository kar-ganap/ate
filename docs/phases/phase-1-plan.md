# Phase 1: Invocation Validation + Ruff Integration + Bug Verification

## Goal

Validate that both subagent and agent team invocation mechanisms work reliably,
then pin Ruff to v0.14.14 and verify all 8 bugs reproduce. Invocation validation
gates everything else.

## Ruff Pin

- Tag: `0.14.14`
- Commit: `8b2e7b36f246b990fe473a84eef25ff429e59ecf`
- Date: January 22, 2026
- Rationale: All 8 target bugs confirmed open and unfixed as of this release.
  0.15.0 has breaking style guide changes; 0.14.14 is stable and recent.

## Part 1: Invocation Smoke Tests (gate)

### Smoke Test 1: Subagent via `claude -p`

```bash
claude -p "What is 2+2?" --max-turns 2 --output-format json
```

Verify: valid JSON output, `.result` contains "4", `num_turns <= 2`.

### Smoke Test 2: Agent Definition Loading

```bash
claude -p --agent bug-investigator "What is your role?" --output-format json --max-turns 1
```

Verify: `.claude/agents/bug-investigator.md` personality reflected in response.

### Smoke Test 3: Agent Team Formation

```bash
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude
# Then interactively: "Create a team with 2 teammates for a quick brainstorm"
```

Verify: `~/.claude/teams/` directory created, config.json has 2+ members.

### Smoke Test Results (2026-02-09)

**Test 1 — PASS**: `claude -p` with `--model haiku`, `--max-turns 3`,
`--output-format json`, `--allowedTools "Read,Grep,Glob"`. Read `pyproject.toml`
and returned "agent-teams-eval". 2 turns, $0.013 cost, session ID captured.

**Test 2 — PASS**: `claude -p --agent bug-investigator` with `--model haiku`.
Agent definition loaded. Response referenced coding/debugging role. $0.004 cost.

**Test 3 — PASS**: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude` interactive.
Team "hello-team" created with @analyst and @reviewer teammates. Both spawned in
parallel (`ctrl+o` to expand, `shift+up` to manage). Both sent hello messages.
Graceful shutdown and full cleanup — no leftover team files or task lists.

**Key observations**:
- Agent teams work with the env var, no model restriction observed
- Teammates can be named and run in parallel
- `ctrl+o` expands agent view, `shift+up` manages teammates
- Cleanup is graceful (shutdown then delete)
- `--model haiku` works for `-p` mode (cost-effective for smoke tests)
- `--max-budget-usd` flag also available for `-p` mode (discovered in `--help`)

## Part 2: Ruff Integration

### Files

- `scripts/pin_ruff.sh` — Clone Ruff into `data/ruff/`, checkout v0.14.14
- `src/ate/ruff.py` — Python wrappers for Ruff operations
- `scripts/verify_bugs.py` — Verify all 8 bugs reproduce
- CLI commands: `ate ruff pin`, `ate ruff build`, `ate ruff verify`

### Test Plan

Unit tests (mocked subprocess):
- `test_ruff.py::test_build_command` — correct `cargo build` command
- `test_ruff.py::test_check_command` — correct `ruff check` with rules
- `test_ruff.py::test_version_parsing` — parse version output
- `test_ruff.py::test_cargo_test_command` — correct test filter

Integration tests (real Ruff, auto-skip if cargo unavailable):
- `test_ruff_build.py::test_build_succeeds` — cargo build completes
- `test_ruff_build.py::test_version_matches` — reports 0.14.14

## Part 3: Bug Verification

For each of the 8 primary bugs, create a minimal reproduction case and run it
against the pinned Ruff build. If any bug doesn't reproduce:
1. Check if it was fixed between the issue date and v0.14.14
2. If so, swap from backup list per experiment-design.md rules
3. Update config/bugs.yaml and experiment-design.md Change Log

## Acceptance Criteria

- All 3 invocation smoke tests pass (documented in this file)
- `make test` — all pass
- `make test-int` — pass (with Ruff built)
- `uv run ate ruff verify` — all 8 primary bugs confirmed reproducible
