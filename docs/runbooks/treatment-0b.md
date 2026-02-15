# Runbook: Treatment 0b — Control: Swim Lanes

**Treatment**: 0b (Control: Swim Lanes)
**Description**: 8 SEPARATE Claude Code sessions, 1 bug per session. No Agent Teams. Fresh, independent sessions with detailed prompts. This is the primary control baseline for the experiment.
**Expected Duration**: 2-5 hours total (across 8 sessions)
**Claude Code Version**: 2.1.42 (pinned — do NOT update mid-experiment)
**Agent Teams**: OFF (plain `claude`, no env var)

---

## 1. Pre-Session Setup (do once)

### 1.1 Verify Claude Code version

```bash
claude --version
# Must show 2.1.42
```

- [ ] Claude Code version is 2.1.42

### 1.2 Scaffold all 8 bugs

```bash
for bug in 20945 18654 7847 4384 19301 22221 22528 22494; do
  uv run ate run scaffold 0b $bug
done
```

- [ ] All 8 scaffold commands succeeded

### 1.3 Create patches directory

```bash
mkdir -p data/patches/treatment-0b
```

- [ ] `data/patches/treatment-0b/` exists

### 1.4 Verify Ruff is clean

```bash
uv run ate run preflight
git -C data/ruff status
```

- [ ] Preflight passes
- [ ] Working tree is clean

---

## 2. Bug Sessions

Run these in order. Each bug is a completely independent session. Exit Claude between sessions. Never carry context from one session to the next.

---

### Bug 1: #20945 — FAST001 false positive (None==None)

**Rule**: FAST001 | **Complexity**: Simple | **Escape**: ~20 min

#### Before

```bash
git -C data/ruff status   # must be clean
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________
```

#### Start session

```bash
claude
```

#### Paste this prompt

```
Investigate Ruff bug #20945: FAST001 false positive (None==None)
URL: https://github.com/astral-sh/ruff/issues/20945
Rule: FAST001 | Category: semantic_analysis | Complexity: simple

The false positive occurs when resolve_name returns None for both sides (types are undefined / no BaseModel subclasses), causing a None==None comparison to be misinterpreted as a match. FAST001 should not flag when both types resolve to None.

The Ruff source is in data/ruff/ (pinned to v0.14.14). Diagnose the root cause and propose a fix. Budget ~25 tool calls.
```

#### Monitor

- Glance every 2-3 min. Escape at ~20 min if stuck.
- Take notes in `data/transcripts/treatment-0b/bug-20945/notes.md`

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note end time: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/patches/treatment-0b/bug-20945.patch
wc -l data/patches/treatment-0b/bug-20945.patch
git -C data/ruff checkout .
git -C data/ruff status   # must be clean
```

- [ ] Patch saved
- [ ] Ruff reset
- [ ] metadata.json updated
- [ ] notes.md written

---

### Bug 2: #18654 — ARG001 false positive (@singledispatch)

**Rule**: ARG001 | **Complexity**: Medium | **Escape**: ~40 min

#### Before

```bash
git -C data/ruff status   # must be clean
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________
```

#### Start session

```bash
claude
```

#### Paste this prompt

```
Investigate Ruff bug #18654: ARG001 false positive (@singledispatch)
URL: https://github.com/astral-sh/ruff/issues/18654
Rule: ARG001 | Category: semantic_analysis | Complexity: medium

ARG001 incorrectly flags singledispatch overload arguments as unused. The @singledispatch decorator's registered implementations have arguments that are used for dispatch but appear unused to the lint rule.

The Ruff source is in data/ruff/ (pinned to v0.14.14). Diagnose the root cause and propose a fix. Budget ~25 tool calls.
```

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note end time: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/patches/treatment-0b/bug-18654.patch
wc -l data/patches/treatment-0b/bug-18654.patch
git -C data/ruff checkout .
git -C data/ruff status   # must be clean
```

- [ ] Patch saved | [ ] Ruff reset | [ ] metadata.json updated | [ ] notes.md written

---

### Bug 3: #7847 — B023 false positive (immediate invocation)

**Rule**: B023 | **Complexity**: Medium | **Escape**: ~40 min

#### Before

```bash
git -C data/ruff status
date -u +"%Y-%m-%dT%H:%M:%SZ"   # start: ___________
```

#### Start session

```bash
claude
```

#### Paste this prompt

```
Investigate Ruff bug #7847: B023 false positive (immediate invocation)
URL: https://github.com/astral-sh/ruff/issues/7847
Rule: B023 | Category: scope_control_flow | Complexity: medium

B023 warns about binding a loop variable in a lambda/closure even when the closure is immediately invoked. If a lambda capturing a loop variable is called right away (e.g., `(lambda x=var: x)()`), the late-binding concern doesn't apply.

The Ruff source is in data/ruff/ (pinned to v0.14.14). Diagnose the root cause and propose a fix. Budget ~25 tool calls.
```

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # end: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/patches/treatment-0b/bug-7847.patch
wc -l data/patches/treatment-0b/bug-7847.patch
git -C data/ruff checkout .
git -C data/ruff status
```

- [ ] Patch saved | [ ] Ruff reset | [ ] metadata.json updated | [ ] notes.md written

---

### Bug 4: #4384 — C901 false positive (closure complexity)

**Rule**: C901 | **Complexity**: Medium | **Escape**: ~40 min

#### Before

```bash
git -C data/ruff status
date -u +"%Y-%m-%dT%H:%M:%SZ"   # start: ___________
```

#### Start session

```bash
claude
```

#### Paste this prompt

```
Investigate Ruff bug #4384: C901 false positive (closure complexity)
URL: https://github.com/astral-sh/ruff/issues/4384
Rule: C901 | Category: scope_control_flow | Complexity: medium

C901 counts nested function/closure complexity toward the parent function, inflating the parent's complexity score. Nested functions should have their own independent complexity count.

The Ruff source is in data/ruff/ (pinned to v0.14.14). Diagnose the root cause and propose a fix. Budget ~25 tool calls.
```

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # end: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/patches/treatment-0b/bug-4384.patch
wc -l data/patches/treatment-0b/bug-4384.patch
git -C data/ruff checkout .
git -C data/ruff status
```

- [ ] Patch saved | [ ] Ruff reset | [ ] metadata.json updated | [ ] notes.md written

---

### Bug 5: #19301 — Parser indentation after backslashes

**Rule**: Parser | **Complexity**: Hard | **Escape**: ~60 min

#### Before

```bash
git -C data/ruff status
date -u +"%Y-%m-%dT%H:%M:%SZ"   # start: ___________
```

#### Start session

```bash
claude
```

#### Paste this prompt

```
Investigate Ruff bug #19301: Parser indentation after backslashes
URL: https://github.com/astral-sh/ruff/issues/19301
Rule: parser | Category: parser | Complexity: hard

The parser mishandles indentation after line continuation backslashes in certain contexts, producing incorrect parse results or errors for valid Python code. The lexer/parser incorrectly tracks indentation level when a logical line is continued via backslash.

The Ruff source is in data/ruff/ (pinned to v0.14.14). Diagnose the root cause and propose a fix. Budget ~25 tool calls.
```

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # end: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/patches/treatment-0b/bug-19301.patch
wc -l data/patches/treatment-0b/bug-19301.patch
git -C data/ruff checkout .
git -C data/ruff status
```

- [ ] Patch saved | [ ] Ruff reset | [ ] metadata.json updated | [ ] notes.md written

---

### Bug 6: #22221 — F401 fix infinite loop (__all__ duplicates)

**Rule**: F401 | **Complexity**: Medium | **Escape**: ~40 min

#### Before

```bash
git -C data/ruff status
date -u +"%Y-%m-%dT%H:%M:%SZ"   # start: ___________
```

#### Start session

```bash
claude
```

#### Paste this prompt

```
Investigate Ruff bug #22221: F401 fix infinite loop (__all__ duplicates)
URL: https://github.com/astral-sh/ruff/issues/22221
Rule: F401 | Category: autofix_convergence | Complexity: medium

F401 autofix creates an infinite loop when __all__ contains duplicate entries. Running `ruff check --fix` repeatedly toggles between adding and removing an import when __all__ lists the same name more than once, never converging. Requires a package structure (foo/__init__.py with submodule imports), not simple stdlib imports.

The Ruff source is in data/ruff/ (pinned to v0.14.14). Diagnose the root cause and propose a fix. Budget ~25 tool calls.
```

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # end: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/patches/treatment-0b/bug-22221.patch
wc -l data/patches/treatment-0b/bug-22221.patch
git -C data/ruff checkout .
git -C data/ruff status
```

- [ ] Patch saved | [ ] Ruff reset | [ ] metadata.json updated | [ ] notes.md written

---

### Bug 7: #22528 — Parser false syntax error (match-like)

**Rule**: Parser | **Complexity**: Hard | **Escape**: ~60 min

#### Before

```bash
git -C data/ruff status
date -u +"%Y-%m-%dT%H:%M:%SZ"   # start: ___________
```

#### Start session

```bash
claude
```

#### Paste this prompt

```
Investigate Ruff bug #22528: Parser false syntax error (match-like)
URL: https://github.com/astral-sh/ruff/issues/22528
Rule: parser | Category: parser | Complexity: hard

The parser incorrectly reports a syntax error for valid Python code that uses match-like patterns. The parser's soft keyword handling for match/case misidentifies certain valid constructs as syntax errors.

The Ruff source is in data/ruff/ (pinned to v0.14.14). Diagnose the root cause and propose a fix. Budget ~25 tool calls.
```

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # end: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/patches/treatment-0b/bug-22528.patch
wc -l data/patches/treatment-0b/bug-22528.patch
git -C data/ruff checkout .
git -C data/ruff status
```

- [ ] Patch saved | [ ] Ruff reset | [ ] metadata.json updated | [ ] notes.md written

---

### Bug 8: #22494 — Formatter range formatting (semicolons)

**Rule**: Formatter | **Complexity**: Medium | **Escape**: ~40 min

#### Before

```bash
git -C data/ruff status
date -u +"%Y-%m-%dT%H:%M:%SZ"   # start: ___________
```

#### Start session

```bash
claude
```

#### Paste this prompt

```
Investigate Ruff bug #22494: Formatter range formatting (semicolons)
URL: https://github.com/astral-sh/ruff/issues/22494
Rule: formatter | Category: configuration | Complexity: medium

`ruff format --range` on semicolon-separated statements introduces whitespace instead of splitting onto separate lines. When formatting a byte range that includes semicolons, the formatter inserts spaces rather than line breaks.

The Ruff source is in data/ruff/ (pinned to v0.14.14). Diagnose the root cause and propose a fix. Budget ~25 tool calls.
```

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # end: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/patches/treatment-0b/bug-22494.patch
wc -l data/patches/treatment-0b/bug-22494.patch
git -C data/ruff checkout .
git -C data/ruff status
```

- [ ] Patch saved | [ ] Ruff reset | [ ] metadata.json updated | [ ] notes.md written

---

## 3. Monitoring Guidelines

You do not need to read or understand Rust code. You are watching the terminal for surface-level signals. Glance every few minutes.

### Signs of looping (press Escape)

- Same filenames scrolling by repeatedly
- Same compiler error appearing 3+ times
- Claude saying "let me try a different approach" then doing the same thing
- Claude re-reading a file it already read minutes ago
- No new files or errors for ~5 minutes

### Signs of progress (let it continue)

- New filenames appearing (exploring different parts of the codebase)
- Different error messages (means something changed)
- Claude running `cargo test` or `cargo build`
- Claude editing different files

### When to nudge (instead of Escape)

If Claude seems stuck but is not looping, type a follow-up:
- "What's your current theory about the root cause?"
- "Have you looked at the test files for this rule?"
- "Try a different approach."
- "Can you summarize what you've found so far?"

Record all nudges in notes.md with timestamps.

### Pressing Escape is not failure

"Claude got stuck after 15 minutes" is valid data. Note it in notes.md and move on.

---

## 4. Post-Session Metadata Template

After each bug session, update `data/transcripts/treatment-0b/bug-{id}/metadata.json`:

```json
{
  "treatment_id": "0b",
  "bug_id": "<bug_number>",
  "started_at": "2026-02-XXTXX:XX:XXZ",
  "completed_at": "2026-02-XXTXX:XX:XXZ",
  "wall_clock_seconds": null,
  "session_id": "<find most recent .jsonl in ~/.claude/projects/...>",
  "model": "claude-opus-4-6",
  "num_turns": null,
  "total_cost_usd": null,
  "exit_code": 0,
  "mode": "interactive"
}
```

---

## 5. Final Checklist (after all 8 sessions)

- [ ] All 8 bugs attempted in order
- [ ] 8 patch files in `data/patches/treatment-0b/`
- [ ] Ruff is clean after final bug
- [ ] All 8 metadata.json files updated
- [ ] All 8 notes.md files written
- [ ] Session IDs noted for all 8 sessions
- [ ] Claude Code version was 2.1.42 throughout
- [ ] No Agent Teams env var was set for any session
