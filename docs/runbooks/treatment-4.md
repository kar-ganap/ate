# Runbook: Treatment 4 — Player-Coach (Delegate OFF)

**Treatment**: 4 (Player-Coach)
**Description**: Agent Teams with autonomous bug assignment, vague prompts, **delegate mode OFF** (lead coordinates directly instead of delegating), 4x2, neutral communication. The lead acts as player-coach.
**Expected Duration**: 2-4 hours
**Claude Code Version**: 2.1.42 (pinned)
**Agent Teams**: ON (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)

| Dimension | Value |
|-----------|-------|
| Decomposition | **Autonomous** (lead decides) |
| Prompt specificity | **Vague** |
| Delegate mode | **OFF** (lead coordinates directly) |
| Team size | 4x2 (4 agents, 2 bugs each) |
| Communication | Neutral |

**Key difference**: Delegate mode is OFF. The lead coordinates directly rather than delegating tasks. This tests whether the lead's direct involvement (player-coach) vs pure delegation changes outcomes.

---

## 1. Pre-Session Setup

### 1.1 Scaffold all 8 bugs

```bash
for bug in 20945 18654 7847 4384 19301 22221 22528 22494; do
  uv run ate run scaffold 4 $bug
done
```

### 1.2 Create patches directory

```bash
mkdir -p data/patches/treatment-4
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
I need you to fix 8 bugs in the Ruff Python linter. The source code is in data/ruff/.

The bugs:

1. There's a bug in Ruff (#20945). See https://github.com/astral-sh/ruff/issues/20945 for details.
2. There's a bug in Ruff (#18654). See https://github.com/astral-sh/ruff/issues/18654 for details.
3. There's a bug in Ruff (#7847). See https://github.com/astral-sh/ruff/issues/7847 for details.
4. There's a bug in Ruff (#4384). See https://github.com/astral-sh/ruff/issues/4384 for details.
5. There's a bug in Ruff (#19301). See https://github.com/astral-sh/ruff/issues/19301 for details.
6. There's a bug in Ruff (#22221). See https://github.com/astral-sh/ruff/issues/22221 for details.
7. There's a bug in Ruff (#22528). See https://github.com/astral-sh/ruff/issues/22528 for details.
8. There's a bug in Ruff (#22494). See https://github.com/astral-sh/ruff/issues/22494 for details.

Form a team of 4 agents. Assign 2 bugs to each agent — you decide the assignment. Do NOT use delegate mode — coordinate the work directly as a player-coach.

Budget ~25 tool calls per bug before reporting. After fixing each bug, save your patch by running `git -C data/ruff diff > data/patches/treatment-4/bug-{id}.patch` (replacing `{id}` with the bug number), then reset the source with `git -C data/ruff checkout .` before starting the next bug.
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

---

## 4. Monitoring

### Delegate mode OFF is KEY data for this treatment

Watch for how the lead coordinates WITHOUT delegation:

- **Does the lead do work itself** (reading code, writing patches)?
- **How does it assign tasks to agents** without delegate mode?
- **Does the lead bottleneck** (agents waiting for lead)?
- **Is the lead more hands-on** compared to delegate-on treatments?
- **Does player-coach style improve or hurt agent quality?**

Record these observations in notes.md:

```markdown
## Player-Coach Observations
- Lead did its own code work: yes/no (details: ___)
- Lead bottlenecked agents: yes/no (details: ___)
- Lead's coordination style: ___
- How lead assigned without delegate: ___
- Agents waited for lead: yes/no (how long: ___)
```

### Standard monitoring

| Signal | Action |
|--------|--------|
| Lead coordinating directly | Expected (delegate off) |
| Lead doing its own code exploration | Note it |
| Agents working independently | Note it |
| Agent stuck 3+ times | Nudge |
| Lead bottlenecking | Note timing |

### Escape thresholds

| Complexity | Bug IDs | Escape |
|------------|---------|--------|
| Simple | #20945 | ~20 min |
| Medium | #18654, #7847, #4384, #22221, #22494 | ~40 min |
| Hard | #19301, #22528 | ~60 min |

### Notes template

```markdown
# Notes: Treatment 4 — Player-Coach (Delegate OFF)

## Lead's Assignment
- Agent 1: #_____ + #_____
- Agent 2: #_____ + #_____
- Agent 3: #_____ + #_____
- Agent 4: #_____ + #_____
- Rationale: ___

## Player-Coach Observations
- Lead did its own code work: ___
- Lead bottlenecked agents: ___
- Lead's coordination style: ___

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
```

---

## 5. Post-Session Steps

### 5.1 Verify patches

```bash
ls -la data/patches/treatment-4/
wc -l data/patches/treatment-4/*.patch 2>/dev/null
git -C data/ruff diff --stat
# If dirty: save remaining patch
git -C data/ruff diff > data/patches/treatment-4/remaining.patch
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
- [ ] **Delegate mode OFF** specified in prompt
- [ ] Autonomous assignment used (lead decided)
- [ ] **Lead's assignment recorded immediately**
- [ ] Correlation pair co-assignments checked
- [ ] Player-coach behavior documented
- [ ] All 8 bugs attempted
- [ ] Patches saved
- [ ] Ruff is clean
- [ ] All 8 metadata.json updated
- [ ] Notes written (including player-coach observations)
- [ ] Session ID noted: `___________`
