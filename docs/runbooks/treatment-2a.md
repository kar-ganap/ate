# Runbook: Treatment 2a — Autonomous + Encourage Communication

**Treatment**: 2a (Autonomous + Encourage)
**Description**: Agent Teams with autonomous bug assignment, vague prompts, delegate mode ON, 4x2, and **encouraged** inter-agent communication. Paired with Treatment 2b (discourage) for the communication comparison.
**Expected Duration**: 2-4 hours
**Claude Code Version**: 2.1.42 (pinned)
**Agent Teams**: ON (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)

| Dimension | Value |
|-----------|-------|
| Decomposition | **Autonomous** (lead decides) |
| Prompt specificity | **Vague** |
| Delegate mode | ON |
| Team size | 4x2 (4 agents, 2 bugs each) |
| Communication | **ENCOURAGE** |

---

## 1. Pre-Session Setup

### 1.1 Scaffold all 8 bugs

```bash
for bug in 20945 18654 7847 4384 19301 22221 22528 22494; do
  uv run ate run scaffold 2a $bug
done
```

### 1.2 Create patches directory

```bash
mkdir -p data/patches/treatment-2a
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

Form a team of 4 agents. Assign 2 bugs to each agent — you decide the assignment. Use delegate mode.

Actively share findings, ask questions of your teammates, and collaborate on diagnosis.

Budget ~25 tool calls per bug before reporting. After fixing each bug, save your patch by running `git -C data/ruff diff > data/patches/treatment-2a/bug-{id}.patch` (replacing `{id}` with the bug number), then reset the source with `git -C data/ruff checkout .` before starting the next bug.
````

---

## 3. CRITICAL: Record the Lead's Bug Assignment

Since decomposition is **autonomous**, the lead will announce its own assignment. **Record this immediately** — it is primary experimental data.

As soon as the lead states its plan, write it down:

```markdown
## Lead's Bug Assignment
- Agent 1: #_____ + #_____
- Agent 2: #_____ + #_____
- Agent 3: #_____ + #_____
- Agent 4: #_____ + #_____
- Rationale given: ___________________________
```

### Correlation Pair Check

Did the lead co-assign any of these known pairs to the SAME agent?

| Pair | Bugs | Same Agent? | Agent # |
|------|------|-------------|---------|
| Semantic | #20945 + #18654 | [ ] | |
| Scope | #7847 + #4384 | [ ] | |
| Parser | #22528 + #19301 | [ ] | |

If yes to any: that pair's Tier 3 score is "structurally advantaged — not comparable."

---

## 4. Monitoring

### Communication is KEY data for this treatment

Treatment 2a explicitly encourages communication. Watch for:

- **Are agents actually messaging each other?** (They should be — that's the guidance)
- **What triggers messages?** (Found relevant info? Stuck? Sharing results?)
- **Does communication help or hurt?** (Did a message change an agent's approach?)
- **Is the lead synthesizing or just routing?**

Record communication observations in notes.md:

```markdown
## Communication Patterns
- Total inter-agent messages observed: ___
- Agent X messaged Agent Y about: ___
- Did agents follow "encourage" guidance: yes/partially/no
- Notable collaboration moments: ___
```

### Standard monitoring

| Signal | Action |
|--------|--------|
| New filenames, different errors | Progress — let continue |
| Same files/errors 3+ times | Prepare to nudge |
| Agent messaging teammate about findings | Note it! This is key data |
| No output for >2 minutes | Check if waiting |

### Escape thresholds

| Complexity | Bug IDs | Escape |
|------------|---------|--------|
| Simple | #20945 | ~20 min |
| Medium | #18654, #7847, #4384, #22221, #22494 | ~40 min |
| Hard | #19301, #22528 | ~60 min |

### Important: Do NOT intervene in communication patterns

The whole point of this treatment is to observe what "encourage" produces naturally. Do not prompt agents to communicate more or less. Only nudge on technical stuck-ness.

---

## 5. Post-Session Steps

### 5.1 Verify patches

```bash
ls -la data/patches/treatment-2a/
wc -l data/patches/treatment-2a/*.patch 2>/dev/null

# If aggregate patch needed:
git -C data/ruff diff --stat
git -C data/ruff diff > data/patches/treatment-2a/remaining.patch
```

### 5.2 Reset Ruff

```bash
git -C data/ruff checkout .
git -C data/ruff status
```

### 5.3 Record end time

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

### 5.4 Update all 8 metadata.json

Update `data/transcripts/treatment-2a/bug-{id}/metadata.json` for each bug.

### 5.5 Finalize notes

Ensure notes capture:
- [ ] Lead's bug assignment + rationale
- [ ] Correlation pair co-assignment check
- [ ] Communication count and patterns
- [ ] Whether agents followed "encourage" guidance
- [ ] Per-bug outcomes
- [ ] Nudges with timestamps
- [ ] Timeline

---

## 6. Final Checklist

- [ ] Claude Code version 2.1.42
- [ ] Agent Teams env var was set
- [ ] Autonomous assignment used (lead decided)
- [ ] **Lead's assignment recorded immediately**
- [ ] Correlation pair co-assignments checked
- [ ] Communication patterns documented
- [ ] "Encourage" compliance noted
- [ ] All 8 bugs attempted
- [ ] Patches saved
- [ ] Ruff is clean
- [ ] All 8 metadata.json updated
- [ ] Notes written
- [ ] Session ID noted: `___________`
