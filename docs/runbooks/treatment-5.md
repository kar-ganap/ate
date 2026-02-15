# Runbook: Treatment 5 — Max Parallelism (8x1)

**Treatment**: 5 (Max Parallelism)
**Description**: Agent Teams with explicit bug assignment, detailed prompts, delegate mode ON, **8 agents x 1 bug each** (maximum parallelism). Neutral communication. Primary comparison target: 0b vs 5.
**Expected Duration**: 1-2 hours (all bugs in parallel)
**Claude Code Version**: 2.1.42 (pinned)
**Agent Teams**: ON (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)

| Dimension | Value |
|-----------|-------|
| Decomposition | **Explicit** (you assign bugs) |
| Prompt specificity | Detailed |
| Delegate mode | ON |
| Team size | **8x1** (8 agents, 1 bug each) |
| Communication | Neutral |

**Key comparison**: Treatment 0b (8 sequential sessions, no teams) vs Treatment 5 (8 parallel agents in 1 session). Same bugs, same prompts — the only difference is parallelism via Agent Teams.

---

## 1. Pre-Session Setup

### 1.1 Verify Claude Code version

```bash
claude --version
# Must show 2.1.42
```

### 1.2 Scaffold all 8 bugs

```bash
for bug in 20945 18654 7847 4384 19301 22221 22528 22494; do
  uv run ate run scaffold 5 $bug
done
```

### 1.3 Create patches directory

```bash
mkdir -p data/patches/treatment-5
```

### 1.4 Verify Ruff is clean

```bash
git -C data/ruff status
# Must show: "nothing to commit, working tree clean"
```

### 1.5 Record start time

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

- [ ] Start time: `___________`

---

## 2. Opening Prompt

Start Claude with Agent Teams:

```bash
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude
```

Paste the following prompt verbatim:

````
I need you to form a team of 8 agents to fix 8 bugs in the Ruff Python linter (Rust codebase). The source code is in data/ruff/ (pinned to v0.14.14). Each agent handles exactly 1 bug. Use delegate mode.

Assign bugs as follows:
- Agent 1: #20945 (FAST001 false positive — None==None)
- Agent 2: #18654 (ARG001 false positive — @singledispatch)
- Agent 3: #7847 (B023 false positive — immediate invocation)
- Agent 4: #4384 (C901 false positive — closure complexity)
- Agent 5: #19301 (Parser — indentation after backslashes)
- Agent 6: #22221 (F401 — fix infinite loop, __all__ duplicates)
- Agent 7: #22528 (Parser — false syntax error, match-like)
- Agent 8: #22494 (Formatter — range formatting semicolons)

Budget: ~25 tool calls per bug before reporting findings.

Bug details:

**#20945 — FAST001 false positive (None==None)**
- Rule: FAST001 | Complexity: simple
- URL: https://github.com/astral-sh/ruff/issues/20945
- resolve_name returns None for undefined types, causing None==None to trigger false positive.

**#18654 — ARG001 false positive (@singledispatch)**
- Rule: ARG001 | Complexity: medium
- URL: https://github.com/astral-sh/ruff/issues/18654
- Singledispatch overload arguments incorrectly flagged as unused.

**#7847 — B023 false positive (immediate invocation)**
- Rule: B023 | Complexity: medium
- URL: https://github.com/astral-sh/ruff/issues/7847
- Warns about loop variable binding in immediately-invoked closures.

**#4384 — C901 false positive (closure complexity)**
- Rule: C901 | Complexity: medium
- URL: https://github.com/astral-sh/ruff/issues/4384
- Nested function complexity counted toward parent function.

**#19301 — Parser indentation after backslashes**
- Rule: parser | Complexity: hard
- URL: https://github.com/astral-sh/ruff/issues/19301
- Mishandles indentation after line continuation backslashes.

**#22221 — F401 fix infinite loop (__all__ duplicates)**
- Rule: F401 | Complexity: medium
- URL: https://github.com/astral-sh/ruff/issues/22221
- Autofix infinite loop when __all__ has duplicate entries.

**#22528 — Parser false syntax error (match-like)**
- Rule: parser | Complexity: hard
- URL: https://github.com/astral-sh/ruff/issues/22528
- Reports syntax error for valid Python using match-like patterns.

**#22494 — Formatter range formatting (semicolons)**
- Rule: formatter | Complexity: medium
- URL: https://github.com/astral-sh/ruff/issues/22494
- --range on semicolons introduces whitespace instead of line breaks.

IMPORTANT: Since all agents share the same data/ruff/ directory, agents must coordinate to avoid conflicts. After fixing a bug, save the patch: `git -C data/ruff diff > data/patches/treatment-5/bug-{id}.patch` then reset: `git -C data/ruff checkout .` before another agent starts modifying files. If agents work simultaneously, save an aggregate patch at the end.
````

---

## 3. Monitoring

### What to watch for

With 8 parallel agents, the session will be very active. Key signals:

| Signal | Action |
|--------|--------|
| Lead forming 8-agent team | Note confirmation |
| Multiple agents working simultaneously | Expected! This is the point of Treatment 5 |
| Git conflicts between agents | Note this — it's important data |
| Agent stuck on same error 3+ times | Nudge |
| Agents sharing findings across bugs | Note this (shouldn't happen much with neutral comms) |

### Escape thresholds (per agent/bug)

| Complexity | Bug IDs | Escape |
|------------|---------|--------|
| Simple | #20945 | ~20 min |
| Medium | #18654, #7847, #4384, #22221, #22494 | ~40 min |
| Hard | #19301, #22528 | ~60 min |

### Notes template

```markdown
# Notes: Treatment 5 — Max Parallelism (8x1)

## Team Formation
- HH:MM Lead formed 8-agent team
- All 8 assignments confirmed: yes/no

## Concurrency Observations
- How many agents ran simultaneously at peak: ___
- Any git conflicts observed: yes/no (details: ___)
- Did the lead coordinate sequencing: yes/no

## Per-Bug Outcomes
| Bug | Agent | Outcome | Approx Time | Notes |
|-----|-------|---------|-------------|-------|
| 20945 | 1 | | | |
| 18654 | 2 | | | |
| 7847 | 3 | | | |
| 4384 | 4 | | | |
| 19301 | 5 | | | |
| 22221 | 6 | | | |
| 22528 | 7 | | | |
| 22494 | 8 | | | |

## Nudges
- (timestamp): (what you said)

## Total wall clock: ___ min
```

---

## 4. Post-Session Steps

### 4.1 Handle patches

```bash
# Check for remaining changes
git -C data/ruff diff --stat

# Save aggregate if needed
git -C data/ruff diff > data/patches/treatment-5/remaining.patch

# Check what was already saved per-bug
ls -la data/patches/treatment-5/

# Verify non-empty
wc -l data/patches/treatment-5/*.patch

# Reset
git -C data/ruff checkout .
git -C data/ruff status
```

### 4.2 Record end time

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

### 4.3 Update all 8 metadata.json

Same session_id for all 8. Update `data/transcripts/treatment-5/bug-{id}/metadata.json`.

### 4.4 Finalize notes

Capture concurrency observations (key data for 0b vs 5 comparison).

---

## 5. Final Checklist

- [ ] Claude Code version 2.1.42
- [ ] Agent Teams env var was set
- [ ] 8-agent team formed (1 bug each)
- [ ] All 8 bugs attempted
- [ ] Patches saved
- [ ] Ruff is clean
- [ ] All 8 metadata.json updated
- [ ] Notes written (including concurrency observations)
- [ ] Session ID noted: `___________`
