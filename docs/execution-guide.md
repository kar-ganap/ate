# Experiment Execution Guide

Step-by-step instructions for running all 8 treatments × 8 bugs.

## Prerequisites

```bash
# 1. Pin and build Ruff
uv run ate ruff pin       # clones Ruff, checks out v0.14.14
uv run ate ruff build     # cargo build (~5 min first time)
uv run ate ruff verify    # confirms all 8 bugs reproduce

# 2. Pre-flight
uv run ate run preflight  # binary exists + version matches

# 3. Record Claude Code version (pin for entire experiment)
claude --version
# Write this down. Do NOT update Claude Code mid-experiment.
```

## Concepts

### What is a "patch"?

A patch is a `git diff` output — a text file showing exactly what source code
changed. When Claude fixes a bug, it modifies Rust files in `data/ruff/`. The
patch captures those changes so they can be replayed later for scoring.

```bash
# After Claude modifies files in data/ruff/:
git -C data/ruff diff > data/patches/treatment-{id}/bug-{id}.patch

# Then reset Ruff for the next bug:
git -C data/ruff checkout .
```

Claude does NOT automatically save patches. You capture them manually after each
bug fix. See "Patch Workflow Step-by-Step" below for the exact sequence.

### What is a "transcript"?

The full conversation log (all messages, tool calls, outputs). Claude Code
automatically saves transcripts as JSONL files at:

```
~/.claude/projects/-Users-kartikganapathi-Documents-Personal-random-projects-others-projects-checkout/{session-id}.jsonl
```

Each session has a UUID. After a session ends, the most recent `.jsonl` file in
that directory is your transcript. You don't need to copy it during the session —
just note the session ID afterward and record it in `metadata.json`.

### What does `ate run scaffold` create?

Running `uv run ate run scaffold <treatment_id> <bug_id>` creates:

```
data/transcripts/treatment-{id}/bug-{id}/
├── session_guide.md   # Opening prompt + treatment config (read before session)
├── notes.md           # Pre-created with header (fill in during session)
└── metadata.json      # Pre-filled with nulls (update after session)
```

- **session_guide.md**: Contains the exact opening prompt to paste. Read it first.
- **notes.md**: Already exists — just open and type observations during the session.
  You do NOT need to create it from scratch.
- **metadata.json**: Already exists with `treatment_id`, `bug_id`, `mode`. Update
  the null fields after the session (see Post-Session Checklist below).

## Patch Workflow Step-by-Step

Concrete example: Treatment 0b, Bug #20945.

```bash
# ── BEFORE THE SESSION ──

# 1. Scaffold
uv run ate run scaffold 0b 20945

# 2. Verify Ruff is clean
git -C data/ruff status
# → "nothing to commit, working tree clean"

# 3. Create patches directory
mkdir -p data/patches/treatment-0b

# ── START THE SESSION ──

# 4. Start Claude
claude

# 5. Paste the opening prompt from session_guide.md

# 6. Claude works. It reads files, explores code, eventually
#    modifies some .rs files in data/ruff/. You watch and take notes.

# 7. Claude says something like "I've fixed the issue" or you
#    decide to stop. Exit the Claude session (/exit or Ctrl+C).

# ── AFTER THE SESSION ──

# 8. Check what Claude changed
git -C data/ruff diff --stat
# → Shows something like:
#   crates/ruff_linter/src/rules/fastapi/rules/fast001.rs | 5 +++--
#   1 file changed, 3 insertions(+), 2 deletions(-)
#
# If this shows "nothing to commit" → Claude didn't modify any files.
# That's fine (diagnosis only). Skip steps 9-10.

# 9. Save the patch
git -C data/ruff diff > data/patches/treatment-0b/bug-20945.patch

# 10. Verify it's not empty
wc -l data/patches/treatment-0b/bug-20945.patch
# → "12 data/patches/treatment-0b/bug-20945.patch"  (some number > 0)

# 11. Reset Ruff for the next bug
git -C data/ruff checkout .

# 12. Verify it's clean again
git -C data/ruff status
# → "nothing to commit, working tree clean"

# 13. Update metadata.json with session details (see Post-Session Checklist)

# 14. Move on to the next bug
```

**What if Claude's fix is wrong?** Save the patch anyway. Tier 1 scoring will
detect that the patch doesn't pass tests. A wrong fix is still data.

**What if Claude only diagnosed but didn't modify files?** That's valid. Note
"diagnosis only, no code changes" in notes.md. No patch to save.

**What if you forgot to reset Ruff before the next session?** The next bug's
patch will include the previous bug's changes. If this happens, reset Ruff
(`git -C data/ruff checkout .`) and re-run the session for that bug.

## Session Workflow

### Before each session

```bash
# Scaffold (creates session_guide.md, notes.md, metadata.json)
uv run ate run scaffold <treatment_id> <bug_id>

# Read the session guide
cat data/transcripts/treatment-{id}/bug-{id}/session_guide.md

# Ensure Ruff is clean (no leftover changes from previous session)
git -C data/ruff status   # should show "nothing to commit, working tree clean"
```

### During the session

1. **Start Claude** with the right environment:
   - Controls (0a, 0b): `claude`
   - Agent Teams (1-5): `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude`

2. **Paste the opening prompt** from `session_guide.md` (the text inside the
   ``` block under "Opening Prompt").

3. **Monitor** — see "When to Intervene" below.

4. **Take notes** in `data/transcripts/treatment-{id}/bug-{id}/notes.md`.
   See "What to Write in notes.md" below.

5. **When Claude finishes** (or you decide to stop), follow the Patch Workflow
   above (steps 7-14).

### Post-session checklist

Update `data/transcripts/treatment-{id}/bug-{id}/metadata.json`:

```json
{
  "treatment_id": "0b",
  "bug_id": 20945,
  "started_at": "2026-02-15T10:00:00Z",
  "completed_at": "2026-02-15T10:25:00Z",
  "wall_clock_seconds": 1500,
  "session_id": "abc12345-...",
  "model": "claude-sonnet-4-5-20250929",
  "num_turns": null,
  "total_cost_usd": null,
  "exit_code": 0,
  "mode": "interactive"
}
```

Fields to fill in:
- **started_at / completed_at**: Note when you start and end. Wall clock.
- **wall_clock_seconds**: Difference in seconds.
- **session_id**: The UUID from Claude Code (visible in the session, or find the
  most recent `.jsonl` file in `~/.claude/projects/...`).
- **model**: The model Claude used (check with `/model` in Claude Code if unsure).
- **num_turns**: Can be counted from the transcript later. OK to leave null for now.
- **total_cost_usd**: $0 for subscription. Can leave null.
- **exit_code**: 0 if session completed normally, 1 if you Escaped early.

## When to Intervene

### Do I need to babysit every session?

No. You don't need to read or understand the Rust code. You're watching the
terminal output for **surface-level signals**:

**Signs Claude is looping** (press Escape):
- Same filenames scrolling by repeatedly
- Same compiler error appearing 3+ times
- Claude saying "let me try a different approach" then doing the same thing
- Claude re-reading a file it already read minutes ago

**Signs Claude is making progress** (let it continue):
- New filenames appearing (exploring different parts of the codebase)
- Different error messages (means something changed)
- Claude running `cargo test` or `cargo build`
- Claude editing different files

You can glance at the terminal every few minutes — you're looking for patterns
(repetition vs exploration), not reading every line of Rust.

### When to press Escape

Press Escape if:
- Claude is clearly looping (same approach 3+ times)
- No new files or errors for ~5 minutes
- Claude is idle or waiting
- You've hit the time threshold (see below)

Pressing Escape is NOT failure. "Claude got stuck after 15 minutes" is valid data.
Note what happened in notes.md and move on.

### When to nudge

If Claude seems stuck but isn't looping — it's thinking or exploring slowly —
type a follow-up message instead of Escape. Nudging means typing something into
the Claude session to redirect it. Examples:

- "What's your current theory about the root cause?"
- "Have you looked at the test files for this rule?"
- "The bug report mentions [specific detail] — have you explored that?"
- "Try a different approach."
- "Can you summarize what you've found so far?"

Nudges are fine. Record them in notes.md ("Nudged at ~12 min to look at tests").

### Time guidelines per bug

| Complexity | Expected | Escape threshold |
|------------|----------|------------------|
| Simple (#20945) | 5-15 min | ~20 min |
| Medium (#18654, #7847, #4384, #22221, #22494) | 15-30 min | ~40 min |
| Hard (#19301, #22528) | 20-45 min | ~60 min |

These are guidelines, not rules. If Claude is making genuine progress at 30 tool
calls, let it continue. If it's stuck at 15, stop early.

## What to Write in notes.md

The file already exists (created by scaffold). Open it in a text editor alongside
the Claude session. Write short notes, not essays. Examples:

```markdown
# Notes: Treatment 0b — Bug #20945

- 10:02 Started session
- 10:04 Claude read the bug URL and reproduction case
- 10:06 Identified FAST001 rule in crates/ruff_linter/src/rules/fastapi/
- 10:08 Found resolve_name() returns None for undefined types
- 10:10 Proposed fix: check if both types are None before comparing
- 10:12 Modified fast001.rs, ran cargo test — 2 tests failed
- 10:15 Fixed the failing tests, all passing now
- 10:16 Session ended. Patch saved.
```

What to capture:
- **Timestamps** (approximate): when Claude found key things
- **Key diagnostic moments**: "identified root cause in X file"
- **Wrong turns**: "tried parser fix instead of semantic analysis, wasted ~10 min"
- **Nudges**: "nudged at ~12 min to look at tests"
- **Outcome**: "produced fix, all tests pass" or "diagnosis only, no fix" or
  "gave up after 20 min"
- **Agent Teams specific**: "Agent 1 messaged Agent 3 about shared parser code",
  "Lead assigned bugs X and Y to Agent 2"

What NOT to write:
- Don't transcribe the conversation (the transcript captures that)
- Don't explain the Rust code (you don't need to understand it)
- Don't evaluate quality (that's Tier 2 scoring)

## Treatment-Specific Instructions

### Treatment 0a — Full Context (1 session, all 8 bugs)

```bash
# Scaffold all 8
for bug in 20945 18654 7847 4384 19301 22221 22528 22494; do
  uv run ate run scaffold 0a $bug
done

# Create patches directory
mkdir -p data/patches/treatment-0a
```

Start: `claude` (no env var)

This is the trickiest treatment because one session handles all 8 bugs.
**Claude must reset Ruff between bugs** — otherwise the second bug's patch
includes the first bug's changes. Add this to your opening prompt after the
bug list:

> **Important**: After fixing each bug, save your patch by running
> `git -C data/ruff diff > data/patches/treatment-0a/bug-{id}.patch`
> (replacing `{id}` with the bug number), then reset the source with
> `git -C data/ruff checkout .` before moving to the next bug.

The session guide lists all 8 bugs in portfolio order:
#20945, #18654, #7847, #4384, #19301, #22221, #22528, #22494

Expected total: 2-4 hours for all 8 bugs.

### Treatment 0b — Swim Lanes (8 sessions, 1 bug each)

```bash
# Scaffold all 8
for bug in 20945 18654 7847 4384 19301 22221 22528 22494; do
  uv run ate run scaffold 0b $bug
done
```

Run 8 **fresh, independent** sessions. Each session: `claude` (no env var).
One bug per session. Paste the opening prompt from each bug's session guide.

Between sessions: capture patch, reset Ruff, update metadata (steps 8-13 of
the Patch Workflow).

### Treatments 1-5 — Agent Teams

```bash
# Scaffold for each treatment (example for Treatment 1)
for bug in 20945 18654 7847 4384 19301 22221 22528 22494; do
  uv run ate run scaffold 1 $bug
done

# Create patches directory
mkdir -p data/patches/treatment-1
```

Start: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude`

For **explicit treatments** (1, 5): assign bugs per the assignment table:
- Agent 1: #20945 + #22528
- Agent 2: #18654 + #22494
- Agent 3: #7847 + #19301
- Agent 4: #4384 + #22221

For **autonomous treatments** (2a, 2b, 3, 4): let the lead decide. **Document
what the lead assigns** in your notes — the assignment itself is data.

Communication guidance (add to your prompt when forming the team):
- **Treatment 2a (Encourage)**: "Actively share findings, ask questions of your
  teammates, and collaborate on diagnosis."
- **Treatment 2b (Discourage)**: "Work independently. Do not message other agents.
  Report findings only to the team lead."
- **All others (Neutral)**: No special communication instructions.

Delegate mode:
- **Treatment 4 (Off)**: The lead coordinates directly instead of delegating.
- **All others (On)**: Normal delegation to agents.

**Patch capture for Agent Teams**: Multiple agents modify `data/ruff/`
concurrently. After the team finishes all bugs, the aggregate diff contains all
changes. Add patch-saving instructions to your prompt:

> After fixing each bug, save your patch by running
> `git -C data/ruff diff > data/patches/treatment-{id}/bug-{bugid}.patch`
> then reset with `git -C data/ruff checkout .` before starting the next bug.

If agents work on bugs simultaneously (likely), you may need to capture an
aggregate patch and split manually later:

```bash
# Option A: Aggregate patch (split later based on which files changed)
git -C data/ruff diff > data/patches/treatment-{id}/all-bugs.patch

# Option B: Per-bug patches if Claude saved them during the session

# Then reset
git -C data/ruff checkout .
```

## Suggested Execution Order

Run the cleanest comparison pair first for early signal:

| Order | Treatment | Sessions | Why first |
|-------|-----------|----------|-----------|
| 1 | **0b** (Swim Lanes) | 8 | Control — baseline |
| 2 | **5** (Max Parallelism) | 1 | Primary comparison: 0b vs 5 |
| 3 | **1** (Structured Team) | 1 | Compares with 5 (size) and 3 (decomp) |
| 4 | **0a** (Full Context) | 1 | Other control variant |
| 5 | **2a** (Encourage) | 1 | Communication pair |
| 6 | **2b** (Discourage) | 1 | Communication pair |
| 7 | **3** (Invest in Prompts) | 1 | Remaining |
| 8 | **4** (Player-Coach) | 1 | Remaining |

Total: **15 sessions** (not 64 — most treatments handle all 8 bugs in 1 session).
Expected total time: **2-4 days** depending on bug difficulty and breaks.

## After All Sessions

```bash
# Check completion
uv run ate run status

# Automated scoring (Tier 1)
uv run ate score tier1

# Generate Tier 2 scoring guides
uv run ate score tier2-scaffold

# Check scoring progress
uv run ate score status
```

## Quick Reference: The 8 Primary Bugs

| Bug | Rule | Complexity | What to expect |
|-----|------|-----------|----------------|
| #20945 | FAST001 | Simple | False positive from None==None. Should be fast. |
| #18654 | ARG001 | Medium | @singledispatch false positive. Semantic analysis. |
| #7847 | B023 | Medium | Immediate invocation false positive. Scope tracking. |
| #4384 | C901 | Medium | Closure complexity counted toward parent. |
| #19301 | Parser | Hard | Indentation after backslashes. Deep parser work. |
| #22221 | F401 | Medium | Autofix infinite loop. Convergence issue. |
| #22528 | Parser | Hard | Match-like false syntax error. Parser work. |
| #22494 | Formatter | Medium | Range formatting semicolons. Formatter logic. |
