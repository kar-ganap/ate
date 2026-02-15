# Runbook: Treatment 3 — Invest in Prompts (Autonomous + Detailed)

**Treatment**: 3 (Invest in Prompts)
**Description**: Agent Teams with autonomous bug assignment, **detailed** prompts (full bug context), delegate mode ON, 4x2, neutral communication. Compared with Treatment 1 for the clean decomposition comparison (explicit vs autonomous).
**Expected Duration**: 2-4 hours
**Claude Code Version**: 2.1.42 (pinned)
**Agent Teams**: ON (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)

| Dimension | Value |
|-----------|-------|
| Decomposition | **Autonomous** (lead decides) |
| Prompt specificity | **Detailed** (full bug context) |
| Delegate mode | ON |
| Team size | 4x2 (4 agents, 2 bugs each) |
| Communication | Neutral |

**Key comparison**: Treatment 1 vs Treatment 3. Both are detailed, delegate-on, 4x2, neutral — only difference is explicit (T1) vs autonomous (T3) bug assignment. What the lead chooses is primary data.

---

## 1. Pre-Session Setup

### 1.1 Scaffold all 8 bugs

```bash
for bug in 20945 18654 7847 4384 19301 22221 22528 22494; do
  uv run ate run scaffold 3 $bug
done
```

### 1.2 Create patches directory

```bash
mkdir -p data/patches/treatment-3
```

### 1.3 Verify Ruff is clean

```bash
git -C data/ruff status
# Must show: "nothing to commit, working tree clean"
```

### 1.4 Verify Claude Code version

```bash
claude --version
# Must be 2.1.42
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
I need you to form a team of 4 agents to fix 8 bugs in the Ruff Python linter (Rust codebase). The source code is in data/ruff/ (pinned to v0.14.14). Each agent should handle 2 bugs. You decide which agent gets which bugs. Use delegate mode.

Budget: ~25 tool calls per bug before reporting findings.

Here are the 8 bugs with full context:

**Bug #20945 — FAST001 false positive (None==None)**
- Rule: FAST001 | Category: semantic_analysis | Complexity: simple
- URL: https://github.com/astral-sh/ruff/issues/20945
- The false positive occurs when resolve_name() returns None for both types (undefined), causing None==None to trigger the rule incorrectly.

**Bug #18654 — ARG001 false positive (@singledispatch)**
- Rule: ARG001 | Category: semantic_analysis | Complexity: medium
- URL: https://github.com/astral-sh/ruff/issues/18654
- ARG001 incorrectly flags singledispatch overload arguments as unused. The @singledispatch registered implementations have arguments used for dispatch but ARG001 doesn't recognize the pattern.

**Bug #7847 — B023 false positive (immediate invocation)**
- Rule: B023 | Category: scope_control_flow | Complexity: medium
- URL: https://github.com/astral-sh/ruff/issues/7847
- B023 warns about binding loop variable in lambda/closure even when immediately invoked. If called right away, late-binding concern doesn't apply.

**Bug #4384 — C901 false positive (closure complexity)**
- Rule: C901 | Category: scope_control_flow | Complexity: medium
- URL: https://github.com/astral-sh/ruff/issues/4384
- C901 counts nested function complexity toward the parent, inflating the parent's score. Nested functions should have independent complexity.

**Bug #19301 — Parser indentation after backslashes**
- Rule: parser | Category: parser | Complexity: hard
- URL: https://github.com/astral-sh/ruff/issues/19301
- Parser mishandles indentation after line continuation backslashes. The lexer incorrectly tracks indentation level on continued lines.

**Bug #22221 — F401 fix infinite loop (__all__ duplicates)**
- Rule: F401 | Category: autofix_convergence | Complexity: medium
- URL: https://github.com/astral-sh/ruff/issues/22221
- F401 autofix creates infinite loop when __all__ has duplicate entries. Fixer toggles between adding/removing import, never converging.

**Bug #22528 — Parser false syntax error (match-like)**
- Rule: parser | Category: parser | Complexity: hard
- URL: https://github.com/astral-sh/ruff/issues/22528
- Parser incorrectly reports syntax error for valid Python using match-like patterns. Soft keyword handling misidentifies valid constructs.

**Bug #22494 — Formatter range formatting (semicolons)**
- Rule: formatter | Category: configuration | Complexity: medium
- URL: https://github.com/astral-sh/ruff/issues/22494
- `ruff format --range` on semicolons introduces whitespace instead of splitting onto separate lines.

**Instructions:**
- You decide how to assign these 8 bugs across the 4 agents (2 bugs each). State your assignment plan before starting.
- After fixing each bug, save a patch: `git -C data/ruff diff > data/patches/treatment-3/bug-{id}.patch` then reset: `git -C data/ruff checkout .`
- If a bug can't be fixed, document the diagnosis and move on.
- Budget ~25 tool calls per bug.
````

---

## 3. CRITICAL: Record the Lead's Bug Assignment

**Record immediately** when the lead announces assignments.

```markdown
## Lead's Bug Assignment
- Agent 1: #_____ + #_____
- Agent 2: #_____ + #_____
- Agent 3: #_____ + #_____
- Agent 4: #_____ + #_____
- Rationale given: ___________________________
```

### Correlation Pair Check

| Pair | Bugs | Same Agent? | Agent # |
|------|------|-------------|---------|
| Semantic | #20945 + #18654 | [ ] | |
| Scope | #7847 + #4384 | [ ] | |
| Parser | #22528 + #19301 | [ ] | |

If yes: Tier 3 score is "structurally advantaged — not comparable."

---

## 4. Monitoring

### Standard monitoring

| Signal | Action |
|--------|--------|
| Lead announces assignment plan | Record immediately |
| Agents exploring different crates | Progress |
| Same error 3+ times per agent | Nudge |
| Agent forgot patch/reset | Intervene |
| Inter-agent communication | Note it (neutral means no guidance either way) |

### Escape thresholds

| Complexity | Bug IDs | Escape |
|------------|---------|--------|
| Simple | #20945 | ~20 min |
| Medium | #18654, #7847, #4384, #22221, #22494 | ~40 min |
| Hard | #19301, #22528 | ~60 min |

### Notes template

```markdown
# Notes: Treatment 3 — Invest in Prompts

## Lead's Assignment (RECORD THIS FIRST)
- Agent 1: #_____ + #_____
- Agent 2: #_____ + #_____
- Agent 3: #_____ + #_____
- Agent 4: #_____ + #_____
- Rationale: ___

## Correlation pairs co-assigned: ___

## Timeline
- HH:MM Session started
- HH:MM Lead announced assignments
- ...

## Per-Bug Outcomes
| Bug | Agent | Outcome | Time | Notes |
|-----|-------|---------|------|-------|
| 20945 | | | | |
| 18654 | | | | |
| 7847 | | | | |
| 4384 | | | | |
| 19301 | | | | |
| 22221 | | | | |
| 22528 | | | | |
| 22494 | | | | |

## Nudges
- (timestamp): (what)

## Communication observed
- (any notable inter-agent messages)
```

---

## 5. Post-Session Steps

### 5.1 Verify patches

```bash
ls -la data/patches/treatment-3/
wc -l data/patches/treatment-3/*.patch 2>/dev/null
git -C data/ruff diff --stat
# If dirty: save remaining patch
git -C data/ruff diff > data/patches/treatment-3/remaining.patch
```

### 5.2 Reset Ruff

```bash
git -C data/ruff checkout .
git -C data/ruff status
```

### 5.3 Update all 8 metadata.json + finalize notes

---

## 6. Final Checklist

- [ ] Claude Code version 2.1.42
- [ ] Agent Teams env var was set
- [ ] Autonomous assignment used (lead decided)
- [ ] **Lead's assignment recorded immediately**
- [ ] Correlation pair co-assignments checked
- [ ] Detailed prompts used (full bug context in opening prompt)
- [ ] All 8 bugs attempted
- [ ] Patches saved
- [ ] Ruff is clean
- [ ] All 8 metadata.json updated
- [ ] Notes written
- [ ] Session ID noted: `___________`
