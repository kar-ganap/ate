# Runbook: Treatment 0a — Control: Full Context

**Treatment**: 0a (Control: Full Context)
**Description**: 1 interactive Claude Code session covering all 8 bugs sequentially. No Agent Teams. Detailed prompts with full bug context. This is the trickiest treatment because all 8 bugs are handled in a single session — Claude must save patches and reset Ruff between each bug.
**Expected Duration**: 2-4 hours total
**Claude Code Version**: 2.1.42 (pinned — do NOT update mid-session)
**Agent Teams**: OFF (plain `claude`, no env var)

---

## 1. Pre-Session Setup

Run these commands from the ate repo root (`~/Documents/Personal/random_projects/others_projects_checkout/ate/`).

### 1.1 Verify Claude Code version

```bash
claude --version
# Must show 2.1.42 — if not, pin it before proceeding
```

- [ ] Claude Code version is 2.1.42

### 1.2 Scaffold all 8 bugs

```bash
for bug in 20945 18654 7847 4384 19301 22221 22528 22494; do
  uv run ate run scaffold 0a $bug
done
```

- [ ] All 8 scaffold commands succeeded
- [ ] `data/transcripts/treatment-0a/` contains 8 subdirectories (bug-20945 through bug-22494)
- [ ] Each subdirectory has `session_guide.md`, `notes.md`, `metadata.json`

### 1.3 Create patch output directory

```bash
mkdir -p data/patches/treatment-0a
```

- [ ] `data/patches/treatment-0a/` exists

### 1.4 Verify Ruff is clean and at correct version

```bash
uv run ate run preflight
git -C data/ruff status
git -C data/ruff diff --stat
```

- [ ] Preflight passes (Ruff binary exists, version matches v0.14.14)
- [ ] `git status` shows clean working tree (no modifications, no untracked files)
- [ ] `git diff --stat` shows no changes

### 1.5 Record session start metadata

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

- [ ] Noted UTC start timestamp: `___________`

---

## 2. Opening Prompt

Launch Claude Code from the ate repo root with NO Agent Teams env var:

```bash
claude
```

- [ ] Confirmed: launched with plain `claude` (NOT `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude`)

### 2.1 Paste the combined opening prompt

Copy and paste the **entire block below** as a single message:

---

````
You are investigating 8 bugs in the Ruff Python linter (a Rust codebase). The Ruff source is in data/ruff/ (pinned to v0.14.14). Please investigate, diagnose, and fix each bug sequentially. Budget roughly 25 tool calls per bug before moving on.

CRITICAL: After fixing each bug, save your patch by running `git -C data/ruff diff > data/patches/treatment-0a/bug-{id}.patch` (replacing {id} with the bug number), then reset with `git -C data/ruff checkout .` before moving to the next bug. If you cannot produce a fix for a bug, save an empty patch and move on.

Here are the 8 bugs in order:

---

### Bug 1: #20945 — FAST001 false positive (None==None)
- **Rule**: FAST001
- **Category**: Semantic analysis
- **Complexity**: Simple
- **URL**: https://github.com/astral-sh/ruff/issues/20945
- **Issue**: FAST001 should not flag `if x is None and y is None` because None==None is a valid identity check pattern. The false positive occurs when resolve_name returns None for both sides (types are undefined / no BaseModel subclasses), causing a None==None comparison to be misinterpreted as a match.

---

### Bug 2: #18654 — ARG001 false positive (@singledispatch)
- **Rule**: ARG001
- **Category**: Semantic analysis
- **Complexity**: Medium
- **URL**: https://github.com/astral-sh/ruff/issues/18654
- **Issue**: ARG001 incorrectly flags singledispatch overload arguments as unused. The @singledispatch decorator's registered implementations have arguments that are used for dispatch but appear unused to the lint rule.

---

### Bug 3: #7847 — B023 false positive (immediate invocation)
- **Rule**: B023
- **Category**: Scope / control flow
- **Complexity**: Medium
- **URL**: https://github.com/astral-sh/ruff/issues/7847
- **Issue**: B023 warns about binding a loop variable in a lambda/closure even when the closure is immediately invoked. Immediate invocation means the variable is captured at the current iteration value, so the warning is a false positive.

---

### Bug 4: #4384 — C901 false positive (closure complexity)
- **Rule**: C901
- **Category**: Scope / control flow
- **Complexity**: Medium
- **URL**: https://github.com/astral-sh/ruff/issues/4384
- **Issue**: C901 counts nested function/closure complexity toward the parent function, inflating the parent's complexity score. Nested functions should have their own independent complexity count.

---

### Bug 5: #19301 — Parser indentation after backslashes
- **Rule**: Parser
- **Category**: Parser
- **Complexity**: Hard
- **URL**: https://github.com/astral-sh/ruff/issues/19301
- **Issue**: Ruff's parser mishandles indentation after line continuation backslashes in certain contexts, producing incorrect parse results or errors for valid Python code.

---

### Bug 6: #22221 — F401 fix infinite loop (__all__ duplicates)
- **Rule**: F401
- **Category**: Autofix convergence
- **Complexity**: Medium
- **URL**: https://github.com/astral-sh/ruff/issues/22221
- **Issue**: F401 autofix creates an infinite loop when __all__ contains duplicate entries. The fixer removes an import, updates __all__, but the duplicate causes it to re-add the import, creating a cycle. Requires a package structure (foo/__init__.py with submodule imports), not simple stdlib imports.

---

### Bug 7: #22528 — Parser false syntax error (match-like)
- **Rule**: Parser
- **Category**: Parser
- **Complexity**: Hard
- **URL**: https://github.com/astral-sh/ruff/issues/22528
- **Issue**: Ruff's parser incorrectly reports a syntax error for valid Python code that uses match-like patterns (soft keywords). The code is valid Python but Ruff rejects it.

---

### Bug 8: #22494 — Formatter range formatting (semicolons)
- **Rule**: Formatter
- **Category**: Configuration
- **Complexity**: Medium
- **URL**: https://github.com/astral-sh/ruff/issues/22494
- **Issue**: `ruff format --range` on semicolon-separated statements introduces whitespace instead of splitting onto separate lines. The range formatting mode does not handle semicolons correctly.

---

Remember: save each patch with `git -C data/ruff diff > data/patches/treatment-0a/bug-{id}.patch` and reset with `git -C data/ruff checkout .` before starting the next bug. Start with Bug 1.
````

---

- [ ] Pasted the full opening prompt
- [ ] Claude acknowledged the 8 bugs and began working on Bug 1 (#20945)

---

## 3. Monitoring Guidelines

### 3.1 Cadence

Glance at the session every **2-3 minutes**. You do not need to watch continuously, but check progress regularly to catch stalls early.

### 3.2 What to watch for

| Signal | Action |
|--------|--------|
| Claude is making steady progress (reading files, writing code, running tests) | No action needed |
| Claude is going in circles (reading same files, re-trying same approach) | Note the time; prepare to nudge at threshold |
| Claude asks a clarifying question | Answer it promptly |
| Claude forgot to save patch before moving to next bug | Immediately intervene (see nudge examples) |
| Claude forgot to reset Ruff (`git checkout .`) before next bug | Immediately intervene |
| Claude appears stuck on compilation errors unrelated to the bug fix | Nudge toward a different approach |
| Session appears hung (no output for >2 minutes) | Check if Claude is waiting for input |

### 3.3 Escape time thresholds

These are wall-clock time limits per bug. If Claude has not produced a patch (or acknowledged it cannot) within the threshold, intervene.

| Complexity | Bug IDs | Escape Threshold |
|------------|---------|-----------------|
| Simple | #20945 | ~20 minutes |
| Medium | #18654, #7847, #4384, #22221, #22494 | ~40 minutes |
| Hard | #19301, #22528 | ~60 minutes |

### 3.4 Nudge examples

Use these as templates. Adapt to the situation.

**If stuck on a bug past the threshold:**
```
Let's move on. Save whatever patch you have (even if incomplete) with:
git -C data/ruff diff > data/patches/treatment-0a/bug-{id}.patch
Then reset with: git -C data/ruff checkout .
And proceed to Bug {next}.
```

**If Claude forgot to save a patch:**
```
Before moving on, please save the patch for the bug you just finished:
git -C data/ruff diff > data/patches/treatment-0a/bug-{id}.patch
Then reset: git -C data/ruff checkout .
```

**If Claude forgot to reset Ruff:**
```
Please reset the Ruff source before starting the next bug:
git -C data/ruff checkout .
Verify with: git -C data/ruff diff --stat
```

**If Claude is going in circles:**
```
You seem to be revisiting the same approach. Can you try a different angle?
If you're stuck, it's OK to save what you have and move on to the next bug.
```

### 3.5 Per-bug tracking

Use this table to track progress in real time (fill in as you go):

| # | Bug ID | Rule | Started | Finished | Patch Saved | Reset Done | Notes |
|---|--------|------|---------|----------|-------------|------------|-------|
| 1 | 20945 | FAST001 | ___:___ | ___:___ | [ ] | [ ] | |
| 2 | 18654 | ARG001 | ___:___ | ___:___ | [ ] | [ ] | |
| 3 | 7847 | B023 | ___:___ | ___:___ | [ ] | [ ] | |
| 4 | 4384 | C901 | ___:___ | ___:___ | [ ] | [ ] | |
| 5 | 19301 | parser | ___:___ | ___:___ | [ ] | [ ] | |
| 6 | 22221 | F401 | ___:___ | ___:___ | [ ] | [ ] | |
| 7 | 22528 | parser | ___:___ | ___:___ | [ ] | [ ] | |
| 8 | 22494 | formatter | ___:___ | ___:___ | [ ] | [ ] | |

---

## 4. After-Session Steps

### 4.1 Record end timestamp

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

- [ ] Noted UTC end timestamp: `___________`

### 4.2 Verify patches exist

```bash
ls -la data/patches/treatment-0a/
```

Expected: up to 8 files (`bug-20945.patch`, `bug-18654.patch`, ..., `bug-22494.patch`). Some may be empty (0 bytes) if Claude could not fix that bug.

- [ ] Verified patch files present
- [ ] Noted which patches are non-empty: `___________`

### 4.3 Verify Ruff is clean after final bug

```bash
git -C data/ruff status
git -C data/ruff diff --stat
```

- [ ] Ruff working tree is clean

### 4.4 Capture session cost

Run `/cost` in the Claude session before exiting (or check the session summary).

- [ ] Noted total token cost: `___________`

### 4.5 Update metadata.json for each bug

For each of the 8 bugs, update `data/transcripts/treatment-0a/bug-{id}/metadata.json` with actual timing and outcome data. The scaffold pre-creates these files; update the following fields:

```json
{
  "started_at": "2026-02-XXTXX:XX:XXZ",
  "completed_at": "2026-02-XXTXX:XX:XXZ",
  "wall_clock_seconds": null,
  "session_id": null,
  "model": "claude-opus-4-6",
  "num_turns": null,
  "total_cost_usd": null,
  "exit_code": 0
}
```

Since all 8 bugs run in a single session, `session_id` and `total_cost_usd` will be the same across all 8. `wall_clock_seconds` and `num_turns` should be estimated per-bug from your observation notes.

- [ ] All 8 metadata.json files updated

### 4.6 Write session notes

For each bug, record observations in the pre-created notes file at `data/transcripts/treatment-0a/bug-{id}/notes.md`. Use this format:

```markdown
# Notes: Treatment 0a — Bug #20945

## Timeline
- Started: 14:05 UTC
- Finished: 14:18 UTC
- Wall clock: ~13 min

## Approach
- Claude read the issue URL first
- Located FAST001 rule in crates/ruff_linter/src/rules/fastapi/...
- Identified None==None comparison in resolve_name

## Diagnosis Quality
- Correct file: Yes
- Correct root cause: Yes/No/Partial
- Fix attempted: Yes/No

## Interventions
- None / "Nudged at 14:15 to move on" / etc.

## Observations
- Number of approximate tool calls: ~15
- Notable behavior: (anything interesting)
```

- [ ] Notes written for all 8 bugs

### 4.7 Save session transcript

Claude Code stores session transcripts automatically as JSONL files at:
```
~/.claude/projects/-Users-kartikganapathi-Documents-Personal-random-projects-others-projects-checkout/{session-id}.jsonl
```

- [ ] Session transcript captured or session ID noted: `___________`

---

## 5. Final Checklist

- [ ] Claude Code version was 2.1.42 throughout the session
- [ ] No Agent Teams env var was set (plain `claude`)
- [ ] All 8 bugs were attempted in portfolio order
- [ ] Patches saved for each bug attempted (even if empty)
- [ ] Ruff was reset between each bug
- [ ] Ruff is clean after final bug
- [ ] Per-bug timing recorded in monitoring table
- [ ] All 8 metadata.json updated with actual data
- [ ] All 8 notes.md written with observations
- [ ] Session cost captured
- [ ] Session transcript saved
- [ ] Total wall-clock time: `___________`

---

## Appendix: Bug Quick Reference

| # | ID | Rule | Category | Complexity | Escape |
|---|-----|------|----------|------------|--------|
| 1 | 20945 | FAST001 | Semantic analysis | Simple | 20 min |
| 2 | 18654 | ARG001 | Semantic analysis | Medium | 40 min |
| 3 | 7847 | B023 | Scope/control flow | Medium | 40 min |
| 4 | 4384 | C901 | Scope/control flow | Medium | 40 min |
| 5 | 19301 | parser | Parser | Hard | 60 min |
| 6 | 22221 | F401 | Autofix convergence | Medium | 40 min |
| 7 | 22528 | parser | Parser | Hard | 60 min |
| 8 | 22494 | formatter | Configuration | Medium | 40 min |

**Sum of escape thresholds**: 20 + 40 + 40 + 40 + 60 + 40 + 60 + 40 = **340 min (~5.7 hours)**. The expected actual time is 2-4 hours since most bugs should resolve well before their escape threshold.
