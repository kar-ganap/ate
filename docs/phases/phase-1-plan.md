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

### Smoke Test 3: Agent Team Formation + Peer-to-Peer Messaging

```bash
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude
# Then interactively: spawn @analyst and @reviewer, have them exchange messages
```

Verify: (1) team forms, (2) `SendMessage` routing metadata proves peer addressing.

### Smoke Test Results (2026-02-09)

**Test 1 — PASS**: `claude -p` with `--model haiku`, `--max-turns 3`,
`--output-format json`, `--allowedTools "Read,Grep,Glob"`. Read `pyproject.toml`
and returned "agent-teams-eval". 2 turns, $0.013 cost, session ID captured.

**Test 2 — PASS**: `claude -p --agent bug-investigator` with `--model haiku`.
Agent definition loaded. Response referenced coding/debugging role. $0.004 cost.

**Test 3 — PASS**: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude` interactive.
Three team iterations were run; the final "peer-test" team is the definitive test.

Team "peer-test": @analyst and @reviewer spawned in parallel. Both ran as
`backendType: "in-process"` with `model: "sonnet"`, team-lead on `claude-opus-4-6`.

**Evidence of peer-to-peer messaging** (from raw JSONL transcripts, NOT agent-written
log files):

1. Analyst called `SendMessage(recipient="reviewer", content="Hey Reviewer, what's
   your role on this team?")`. System returned:
   ```json
   {"success": true, "routing": {"sender": "analyst", "target": "@reviewer"}}
   ```
2. Reviewer received the message as system-attributed:
   ```xml
   <teammate-message teammate_id="analyst">Hey Reviewer, what's your role?</teammate-message>
   ```
3. Reviewer called `SendMessage(recipient="analyst", content="I'm the Reviewer...")`.
   System returned:
   ```json
   {"success": true, "routing": {"sender": "reviewer", "target": "@analyst"}}
   ```
4. Reviewer separately messaged team-lead to report completion (different
   `SendMessage` call with `recipient="team-lead"`).

The routing metadata is **system-generated** — agents cannot fabricate it. This proves
the `SendMessage` API supports direct peer addressing (analyst <-> reviewer) without
team-lead in the routing path.

**Caveat — async message delivery**: The Reviewer went idle before the Analyst's
message arrived. Team-lead had to "nudge" the Reviewer to wake up and process the
queued message. This means message delivery is async and agents can miss queued
messages if their turn ends first. This is an operational consideration for the
experiment's interactive treatments.

**Transcript locations** (session `0a7e6057`):
- Analyst: `subagents/agent-a688881.jsonl` (sends to reviewer, waits for reply)
- Reviewer: `subagents/agent-acad5c9.jsonl` (receives from analyst, replies, logs)
- Team config: `~/.claude/teams/peer-test/config.json` (3 members, deleted after test)

**What the agent-written log files do NOT prove**: The agents also wrote
`data/team-logs/peer-test/{analyst,reviewer}.log`, but these are weak evidence because
team-lead's prompt dictated the exact message content and instructed agents to write
"PEER-TO-PEER VERIFIED". The logs are circular — the SendMessage routing metadata
is the actual proof.

**Key distinction from subagents**: `claude -p` (subagent mode) has no `SendMessage`
primitive. Subagents return JSON to the caller and cannot address each other. Agent
teams provide an addressable messaging bus — this is the fundamental architectural
difference the experiment measures.

**Key observations**:
- Agent teams work with the env var, no model restriction observed
- Teammates can be named and run in parallel
- `ctrl+o` expands agent view, `shift+up` manages teammates
- Cleanup is graceful (shutdown then delete)
- `--model haiku` works for `-p` mode (cost-effective for smoke tests)
- `--max-budget-usd` flag also available for `-p` mode (discovered in `--help`)
- Message delivery is async; agents may need nudging if idle when message arrives

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

### Bug Verification Results (2026-02-09)

All 8 bugs confirmed reproducible (after one swap):

| Bug | Status | Notes |
|-----|--------|-------|
| #20945 FAST001 | REPRODUCED | Needs undefined types + `--preview` |
| #18654 ARG001 | REPRODUCED | Straightforward repro |
| #7847 B023 | REPRODUCED | Straightforward repro |
| #4384 C901 | REPRODUCED | Needs ruff.toml with `max-complexity = 3` |
| #19301 Parser | REPRODUCED | Straightforward repro |
| #22221 F401 | REPRODUCED | Needs package structure (foo/__init__.py + submodules) |
| #22528 Parser | REPRODUCED | Straightforward repro |
| #22494 Formatter | REPRODUCED | Range formatting semicolons (SWAPPED from #17010) |

**Swap**: #17010 (server panic, glob braces) was fixed in v0.14.14. Replaced with
backup #22494 (formatter range formatting) per experiment-design.md swap rules.

## Acceptance Criteria

- All 3 invocation smoke tests pass (documented in this file)
- `make test` — 58 tests pass (56 unit + 2 integration)
- `make test-int` — 2 integration tests pass (Ruff built, version verified)
- `uv run ate ruff verify` — all 8 primary bugs confirmed reproducible
