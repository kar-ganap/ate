# Runbook: Treatment 1 — Structured Team (Explicit Assignment)

**Treatment**: 1 (Structured Team)
**Description**: Agent Teams with explicit bug assignment, detailed prompts, delegate mode ON, 4 agents x 2 bugs each, neutral communication. This is the structured baseline for all Agent Teams comparisons.
**Expected Duration**: 2-4 hours
**Claude Code Version**: 2.1.42 (pinned)
**Agent Teams**: ON (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)

| Dimension | Value |
|-----------|-------|
| Decomposition | **Explicit** (you assign bugs) |
| Prompt specificity | Detailed |
| Delegate mode | ON |
| Team size | 4x2 (4 agents, 2 bugs each) |
| Communication | Neutral (no special instructions) |

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
  uv run ate run scaffold 1 $bug
done
```

### 1.3 Create patches directory

```bash
mkdir -p data/patches/treatment-1
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
I need you to form a team of 4 agents to fix 8 bugs in the Ruff Python linter (Rust codebase). The source code is in data/ruff/ (pinned to v0.14.14). Use delegate mode.

Assign bugs as follows:
- Agent 1: #20945 (FAST001 false positive) + #22528 (parser false syntax error)
- Agent 2: #18654 (ARG001 false positive) + #22494 (formatter range formatting)
- Agent 3: #7847 (B023 false positive) + #19301 (parser indentation)
- Agent 4: #4384 (C901 closure complexity) + #22221 (F401 infinite loop)

Budget: ~25 tool calls per bug before reporting findings.

Here are the bug details:

**Bug #20945 — FAST001 false positive (None==None)**
- Rule: FAST001 | Category: semantic_analysis | Complexity: simple
- URL: https://github.com/astral-sh/ruff/issues/20945
- The false positive occurs when resolve_name returns None for both sides (types are undefined), causing None==None to be misinterpreted as a type match.

**Bug #18654 — ARG001 false positive (@singledispatch)**
- Rule: ARG001 | Category: semantic_analysis | Complexity: medium
- URL: https://github.com/astral-sh/ruff/issues/18654
- ARG001 incorrectly flags singledispatch overload arguments as unused.

**Bug #7847 — B023 false positive (immediate invocation)**
- Rule: B023 | Category: scope_control_flow | Complexity: medium
- URL: https://github.com/astral-sh/ruff/issues/7847
- B023 warns about binding a loop variable in a lambda/closure even when immediately invoked.

**Bug #4384 — C901 false positive (closure complexity)**
- Rule: C901 | Category: scope_control_flow | Complexity: medium
- URL: https://github.com/astral-sh/ruff/issues/4384
- C901 counts nested function complexity toward the parent, inflating complexity scores.

**Bug #19301 — Parser indentation after backslashes**
- Rule: parser | Category: parser | Complexity: hard
- URL: https://github.com/astral-sh/ruff/issues/19301
- Parser mishandles indentation after line continuation backslashes.

**Bug #22221 — F401 fix infinite loop (__all__ duplicates)**
- Rule: F401 | Category: autofix_convergence | Complexity: medium
- URL: https://github.com/astral-sh/ruff/issues/22221
- F401 autofix creates an infinite loop when __all__ contains duplicate entries.

**Bug #22528 — Parser false syntax error (match-like)**
- Rule: parser | Category: parser | Complexity: hard
- URL: https://github.com/astral-sh/ruff/issues/22528
- Parser incorrectly reports syntax error for valid Python using match-like patterns.

**Bug #22494 — Formatter range formatting (semicolons)**
- Rule: formatter | Category: configuration | Complexity: medium
- URL: https://github.com/astral-sh/ruff/issues/22494
- `ruff format --range` on semicolons introduces whitespace instead of line breaks.

After fixing each bug, save the patch: `git -C data/ruff diff > data/patches/treatment-1/bug-{id}.patch` then reset: `git -C data/ruff checkout .` before starting the next bug.
````

---

## 3. Monitoring

### What to watch for

| Signal | Action |
|--------|--------|
| Lead forming team and delegating | Note the confirmation |
| Agents exploring different crates | Progress |
| Agent stuck on same error 3+ times | Prepare to nudge |
| Agent forgot patch save/reset | Intervene immediately |
| No output for >2 minutes | Check if waiting |

### Escape thresholds

| Complexity | Bug IDs | Escape |
|------------|---------|--------|
| Simple | #20945 | ~20 min |
| Medium | #18654, #7847, #4384, #22221, #22494 | ~40 min |
| Hard | #19301, #22528 | ~60 min |

### Nudge examples

```
Agent [N] seems stuck on bug #[X]. Can it try a different approach?
```

```
Please make sure to save patches after each bug fix:
git -C data/ruff diff > data/patches/treatment-1/bug-{id}.patch
git -C data/ruff checkout .
```

### Notes template

Record in `data/transcripts/treatment-1/bug-20945/notes.md` (or any bug's notes file):

```markdown
# Notes: Treatment 1 — Team Session

## Assignment Confirmation
- Agent 1: #20945 + #22528 (confirmed by lead)
- Agent 2: #18654 + #22494 (confirmed by lead)
- Agent 3: #7847 + #19301 (confirmed by lead)
- Agent 4: #4384 + #22221 (confirmed by lead)

## Timeline
- HH:MM Session started
- HH:MM Lead formed team and delegated
- HH:MM Agent 1 started on #20945
- ...

## Per-Bug Outcomes
| Bug | Agent | Outcome | Time |
|-----|-------|---------|------|
| 20945 | 1 | fix/diagnosis/stuck | ~X min |
| ... | ... | ... | ... |

## Nudges
- (timestamp): (what you said)

## Inter-Agent Communication
- (any notable messages between agents)
```

---

## 4. Post-Session Steps

### 4.1 Check and save remaining patches

```bash
git -C data/ruff diff --stat
# If dirty, save aggregate
git -C data/ruff diff > data/patches/treatment-1/remaining.patch
git -C data/ruff checkout .
```

### 4.2 Verify patches

```bash
ls -la data/patches/treatment-1/
wc -l data/patches/treatment-1/*.patch
```

### 4.3 Verify Ruff is clean

```bash
git -C data/ruff status
```

### 4.4 Record end time

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

- [ ] End time: `___________`

### 4.5 Update all 8 metadata.json files

Same session_id for all 8 (single session). Update `data/transcripts/treatment-1/bug-{id}/metadata.json`.

### 4.6 Finalize notes

- [ ] Assignment confirmed
- [ ] Timeline recorded
- [ ] Per-bug outcomes noted
- [ ] Nudges documented
- [ ] Inter-agent communication noted

---

## 5. Final Checklist

- [ ] Claude Code version 2.1.42
- [ ] Agent Teams env var was set
- [ ] Explicit bug assignment used (not autonomous)
- [ ] All 8 bugs attempted
- [ ] Patches saved
- [ ] Ruff is clean
- [ ] All 8 metadata.json updated
- [ ] Notes written
- [ ] Session ID noted: `___________`
