# Runbook: Round 2 Bug Screening

**Goal**: Screen 11 candidate bugs to find ~8 where Claude Opus 4.6 genuinely
struggles (fails, takes 30+ min, or requires multiple dead ends).

**Format**: Treatment 0b style — single Claude session, single bug, interactive.
30-minute hard time limit per candidate.

**Expected Duration**: 6-8 hours total (11 candidates x 30 min + overhead).
Can be spread across multiple sittings.

**Ruff Version**: v0.15.1 (latest as of 2026-02-15)

**Pre-checks complete**: All 11 bugs verified OPEN, no competing PRs, reproduces
against v0.15.1. Reproduction files pre-built in `data/screening/bug-{id}/`.

---

## 1. One-Time Setup (ALREADY DONE)

The following steps were completed during infrastructure setup:

- [x] `ruff.py` RUFF_TAG updated to `0.15.1`
- [x] `pin_ruff.sh` RUFF_TAG updated to `0.15.1`
- [x] `ate ruff pin` succeeded
- [x] `ate ruff build` succeeded
- [x] `ate run preflight` passes
- [x] All 11 bugs verified open (no competing merged PRs)
- [x] All 11 bugs reproduce against v0.15.1
- [x] Reproduction files created in `data/screening/bug-{id}/`

### Before first screening session

```bash
cd ~/Documents/Personal/random_projects/others_projects_checkout/ate

# Verify Claude Code version
claude --version
# Note version: ___________

# Confirm no Agent Teams
echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS
# Should be empty / unset

# Verify Ruff is clean
git -C data/ruff status   # must be clean
```

- [ ] Claude Code version noted: ___________
- [ ] Agent Teams env var is NOT set
- [ ] Ruff working tree is clean

---

## 2. Verdict Criteria (reference)

| Verdict | Criteria | Action |
|---------|----------|--------|
| **KEEP** | Claude fails to produce a fix, OR takes 30 min and still struggling | Add to Round 2 primary |
| **MAYBE** | Claude succeeds in 15-30 min but with dead ends | Add to Round 2 backup |
| **DROP** | Claude succeeds in <15 min cleanly | Too easy, skip |

**Signs of struggling** (good for Round 2): Multiple dead-end approaches, re-reading
same files, incorrect fix attempts, "let me try a different approach" more than twice.

**Signs of easy solve** (bad): Root cause found in <5 min, single clean edit, done in
<15 min.

**Do NOT nudge or help.** This is a calibration session.

---

## 3. Stopping Criteria

You can stop screening early if:
- **8+ KEEPs**: You have enough primary bugs for Round 2
- **All Tier A+B screened**: If you have 6+ KEEPs from Tiers A and B, skip Tier C
- **Diminishing returns**: If Tier C candidates are all DROPs, stop

---

## 4. Bug Sessions

Work through in order: Tier A first, then B, then C.

---

### Bug 1 of 11: #21896 — Parser relexing + unclosed strings

**Tier**: A | **Category**: parser | **Why hard**: Lexer/parser state sync, f-string nesting, error recovery

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________
```

#### Start session

```bash
# Set 30-min timer (macOS)
( sleep 1800 && osascript -e 'display notification "30 min screening limit reached" with title "ATE Screening"' ) &

claude
```

#### Paste this prompt

```
Investigate and fix Ruff bug #21896: Parser relexing + unclosed strings
URL: https://github.com/astral-sh/ruff/issues/21896

Bug: Parser state desyncs when relexing after an unclosed f-string.
The nesting counter in the parser diverges from the lexer, causing
incorrect parse results.

Reproduction (save as reproduction.py):
  (c: int = 1,f"""{d=[
  def a(
  class A:
      pass

Command: ruff check reproduction.py
Expected: Parser should recover gracefully from malformed input
Actual: Parser state desyncs (nesting counter diverges from parser)

The Ruff source is in data/ruff/ (v0.15.1). Diagnose the root cause and
produce a fix. Budget ~25 tool calls.
```

#### Hard stop at 30 min — press Escape

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note end time: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening/bug-21896/patch
wc -l data/screening/bug-21896/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
git -C data/ruff status   # must be clean
```

#### Record verdict

Edit `data/screening/bug-21896/metadata.json`:

```json
{
  "bug_id": 21896,
  "screening_date": "2026-02-XX",
  "status": "<KEEP | MAYBE | DROP>",
  "time_minutes": null,
  "dead_ends": null,
  "fix_produced": false,
  "fix_correct": null,
  "notes": ""
}
```

Update `config/screening_candidates.yaml` — change `status: pending` to verdict.

- [ ] Patch saved (if produced)
- [ ] `metadata.json` updated with verdict
- [ ] `screening_candidates.yaml` status updated
- [ ] Ruff reset and clean

---

### Bug 2 of 11: #20891 — F401+I002+PYI025 infinite loop

**Tier**: A | **Category**: autofix_convergence | **Why hard**: 3-rule autofix conflict, fix application ordering

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min screening limit reached" with title "ATE Screening"' ) &

claude
```

#### Paste this prompt

```
Investigate and fix Ruff bug #20891: F401+I002+PYI025 autofix infinite loop
URL: https://github.com/astral-sh/ruff/issues/20891

Bug: Three rules create an autofix cycle that never converges.

Cycle:
  1. I002 adds `from collections.abc import Set` (required import)
  2. PYI025 rewrites to `from collections.abc import Set as Set`
  3. F401 removes it (Set is unused)
  4. Back to step 1

Reproduction:
  File: reproduction.py (contains `from collections.abc import Set` + `1`)
  Config: ruff.toml with [lint] select = ["F401", "I002", "PYI025"]
          and [lint.isort] required-imports = ["from collections.abc import Set"]

Command: ruff check reproduction.py --config ruff.toml --unsafe-fixes --fix
Expected: Converges to a stable state
Actual: "Failed to converge after 100 iterations"

The Ruff source is in data/ruff/ (v0.15.1). Diagnose the root cause and
produce a fix. Budget ~25 tool calls.
```

#### Hard stop at 30 min — press Escape

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note end time: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening/bug-20891/patch
wc -l data/screening/bug-20891/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
git -C data/ruff status   # must be clean
```

#### Record verdict

Edit `data/screening/bug-20891/metadata.json`:

```json
{
  "bug_id": 20891,
  "screening_date": "2026-02-XX",
  "status": "<KEEP | MAYBE | DROP>",
  "time_minutes": null,
  "dead_ends": null,
  "fix_produced": false,
  "fix_correct": null,
  "notes": ""
}
```

Update `config/screening_candidates.yaml` — change `status: pending` to verdict.

- [ ] Patch saved (if produced)
- [ ] `metadata.json` updated with verdict
- [ ] `screening_candidates.yaml` status updated
- [ ] Ruff reset and clean

---

### Bug 3 of 11: #12611 — E302+I001 infinite loop

**Tier**: A | **Category**: autofix_convergence | **Why hard**: 2-rule interaction, E302 fixer puts blank line in wrong place

**NOTE**: E302 moved to preview-only in v0.15.1. The `--preview` flag is required.

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min screening limit reached" with title "ATE Screening"' ) &

claude
```

#### Paste this prompt

```
Investigate and fix Ruff bug #12611: E302+I001 autofix infinite loop
URL: https://github.com/astral-sh/ruff/issues/12611

Bug: Two rules create an autofix cycle that never converges.

Cycle:
  1. E302 inserts blank line before def (but places it between import and comments)
  2. I001 removes it (breaks import block formatting)
  3. Back to step 1

Reproduction (save as reproduction.py):
  """Test that ruff fails"""

  import pytest

  # whatever
  # whatever 2

  # whatever 3
  @pytest.mark.skip
  def test_ruff_fails() -> None:
      """A test case that causes ruff to have an infinite loop"""
      return

Command: ruff check reproduction.py --select E302,I001 --no-cache --fix --unsafe-fixes --isolated --preview
Expected: Converges to a stable state
Actual: "Failed to converge after 100 iterations"

IMPORTANT: E302 requires --preview in Ruff v0.15.1 (it moved from stable to
preview). Make sure to include --preview when running ruff check for this bug.

The Ruff source is in data/ruff/ (v0.15.1). Diagnose the root cause and
produce a fix. Budget ~25 tool calls.
```

#### Hard stop at 30 min — press Escape

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note end time: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening/bug-12611/patch
wc -l data/screening/bug-12611/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
git -C data/ruff status   # must be clean
```

#### Record verdict

Edit `data/screening/bug-12611/metadata.json`:

```json
{
  "bug_id": 12611,
  "screening_date": "2026-02-XX",
  "status": "<KEEP | MAYBE | DROP>",
  "time_minutes": null,
  "dead_ends": null,
  "fix_produced": false,
  "fix_correct": null,
  "notes": ""
}
```

Update `config/screening_candidates.yaml` — change `status: pending` to verdict.

- [ ] Patch saved (if produced)
- [ ] `metadata.json` updated with verdict
- [ ] `screening_candidates.yaml` status updated
- [ ] Ruff reset and clean

---

### Bug 4 of 11: #12865 — DJ012 cross-file inheritance

**Tier**: B | **Category**: semantic_analysis | **Why hard**: Multi-file analysis, type inference needed

**NOTE**: The bug is a false negative — ruff says "All checks passed!" when it should
flag a DJ012 violation. The cross-file case (my_pkg/) and single-file aliasing
case (reproduction.py) both fail to detect the issue.

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min screening limit reached" with title "ATE Screening"' ) &

claude
```

#### Paste this prompt

```
Investigate and fix Ruff bug #12865: DJ012 false negative on cross-file inheritance
URL: https://github.com/astral-sh/ruff/issues/12865

Bug: DJ012 (Django model method ordering) fails to detect violations when the
Model base class comes from a cross-file import or an alias.

Case 1 — Cross-file (my_pkg/my_model.py inherits from my_pkg/parent_model.py):
  parent_model.py: class ParentModel(models.Model) with abstract Meta
  my_model.py: class MyModel(ParentModel) with __str__ before Meta
  Command: ruff check --select DJ012 my_pkg/my_model.py
  Expected: DJ012 error (Meta class should come before __str__)
  Actual: All checks passed! (Ruff can't resolve cross-file Model inheritance)

Case 2 — Single-file aliasing (reproduction.py):
  BaseModel = models.Model
  class MyModel(BaseModel) with __str__ before Meta
  Command: ruff check --select DJ012 reproduction.py
  Expected: DJ012 error
  Actual: All checks passed! (Ruff can't resolve aliased Model base)

Both reproduction files are in data/screening/bug-12865/.

The Ruff source is in data/ruff/ (v0.15.1). Diagnose the root cause and
produce a fix. Budget ~25 tool calls.
```

#### Hard stop at 30 min — press Escape

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note end time: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening/bug-12865/patch
wc -l data/screening/bug-12865/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
git -C data/ruff status   # must be clean
```

#### Record verdict

Edit `data/screening/bug-12865/metadata.json`:

```json
{
  "bug_id": 12865,
  "screening_date": "2026-02-XX",
  "status": "<KEEP | MAYBE | DROP>",
  "time_minutes": null,
  "dead_ends": null,
  "fix_produced": false,
  "fix_correct": null,
  "notes": ""
}
```

Update `config/screening_candidates.yaml` — change `status: pending` to verdict.

- [ ] Patch saved (if produced)
- [ ] `metadata.json` updated with verdict
- [ ] `screening_candidates.yaml` status updated
- [ ] Ruff reset and clean

---

### Bug 5 of 11: #10874 — F811 cross-scope in stubs

**Tier**: B | **Category**: scope_control_flow | **Why hard**: Scope boundaries, explicit re-exports in .pyi files

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min screening limit reached" with title "ATE Screening"' ) &

claude
```

#### Paste this prompt

```
Investigate and fix Ruff bug #10874: F811 false positive in stub files (cross-scope)
URL: https://github.com/astral-sh/ruff/issues/10874

Bug: F811 incorrectly flags a class attribute as a redefinition of a module-level
re-export in .pyi stub files. The class attribute is in a different scope and
should not shadow the module-level import.

Reproduction (reproduction.pyi):
  from x import y as y

  class Foo:
      y = 42

Command: ruff check --select F811 reproduction.pyi
Expected: No errors (class attribute is in different scope from module re-export)
Actual: F811 Redefinition of unused `y` from line 1

The file is in data/screening/bug-10874/.

The Ruff source is in data/ruff/ (v0.15.1). Diagnose the root cause and
produce a fix. Budget ~25 tool calls.
```

#### Hard stop at 30 min — press Escape

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note end time: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening/bug-10874/patch
wc -l data/screening/bug-10874/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
git -C data/ruff status   # must be clean
```

#### Record verdict

Edit `data/screening/bug-10874/metadata.json`:

```json
{
  "bug_id": 10874,
  "screening_date": "2026-02-XX",
  "status": "<KEEP | MAYBE | DROP>",
  "time_minutes": null,
  "dead_ends": null,
  "fix_produced": false,
  "fix_correct": null,
  "notes": ""
}
```

Update `config/screening_candidates.yaml` — change `status: pending` to verdict.

- [ ] Patch saved (if produced)
- [ ] `metadata.json` updated with verdict
- [ ] `screening_candidates.yaml` status updated
- [ ] Ruff reset and clean

---

### Bug 6 of 11: #19632 — F811 regression + typing-modules config

**Tier**: B | **Category**: semantic_analysis | **Why hard**: Config-dependent semantic, bisected to PR #10210

**NOTE**: Bug is specific to single-segment module names in `typing-modules` config.
Dotted names like `"std.std"` work fine; `"std"` does not.

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min screening limit reached" with title "ATE Screening"' ) &

claude
```

#### Paste this prompt

```
Investigate and fix Ruff bug #19632: F811 regression with typing-modules config
URL: https://github.com/astral-sh/ruff/issues/19632

Bug: F811 incorrectly flags overloaded function definitions when a custom
typing module is configured with a single-segment name.

Config (ruff.toml):
  [lint]
  typing-modules = ["std"]

Reproduction (reproduction.py):
  from std import overload

  @overload
  def func(a: str, b: int) -> int: ...
  @overload
  def func(a: int, b: str) -> int: ...
  def func(a: int | str, b: int | str) -> int:
      return 0

Command: ruff check --select F811 --config ruff.toml reproduction.py
Expected: No F811 errors (overload from custom typing module should suppress)
Actual: Two F811 errors on overloaded function definitions

Note: The bug is specific to single-segment module names like "std". Dotted
names like "std.std" work correctly. Bisected to PR #10210.

Files are in data/screening/bug-19632/.

The Ruff source is in data/ruff/ (v0.15.1). Diagnose the root cause and
produce a fix. Budget ~25 tool calls.
```

#### Hard stop at 30 min — press Escape

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note end time: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening/bug-19632/patch
wc -l data/screening/bug-19632/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
git -C data/ruff status   # must be clean
```

#### Record verdict

Edit `data/screening/bug-19632/metadata.json`:

```json
{
  "bug_id": 19632,
  "screening_date": "2026-02-XX",
  "status": "<KEEP | MAYBE | DROP>",
  "time_minutes": null,
  "dead_ends": null,
  "fix_produced": false,
  "fix_correct": null,
  "notes": ""
}
```

Update `config/screening_candidates.yaml` — change `status: pending` to verdict.

- [ ] Patch saved (if produced)
- [ ] `metadata.json` updated with verdict
- [ ] `screening_candidates.yaml` status updated
- [ ] Ruff reset and clean

---

### Bug 7 of 11: #14695 — ANN401 stack overflow (escape seqs)

**Tier**: B | **Category**: parser | **Why hard**: Parser recursion depth issue in quoted annotations with escape sequences

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min screening limit reached" with title "ATE Screening"' ) &

claude
```

#### Paste this prompt

```
Investigate and fix Ruff bug #14695: ANN401 stack overflow on quoted escape sequences
URL: https://github.com/astral-sh/ruff/issues/14695

Bug: Ruff crashes with a stack overflow when checking a function annotation
that contains nested quotes with hex escape sequences.

Reproduction (reproduction.py):
  def f(x: "'in\x74'"): pass

Command: ruff check --isolated --select ANN401 reproduction.py
Expected: Graceful lint result (error or no error, but no crash)
Actual: thread 'main' has overflowed its stack

The file is in data/screening/bug-14695/.

The Ruff source is in data/ruff/ (v0.15.1). Diagnose the root cause and
produce a fix. Budget ~25 tool calls.
```

#### Hard stop at 30 min — press Escape

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note end time: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening/bug-14695/patch
wc -l data/screening/bug-14695/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
git -C data/ruff status   # must be clean
```

#### Record verdict

Edit `data/screening/bug-14695/metadata.json`:

```json
{
  "bug_id": 14695,
  "screening_date": "2026-02-XX",
  "status": "<KEEP | MAYBE | DROP>",
  "time_minutes": null,
  "dead_ends": null,
  "fix_produced": false,
  "fix_correct": null,
  "notes": ""
}
```

Update `config/screening_candidates.yaml` — change `status: pending` to verdict.

- [ ] Patch saved (if produced)
- [ ] `metadata.json` updated with verdict
- [ ] `screening_candidates.yaml` status updated
- [ ] Ruff reset and clean

---

### Bug 8 of 11: #16500 — C416+C409 autofix conflict (preview)

**Tier**: C | **Category**: autofix_convergence | **Why hard**: Rule interaction in preview mode

**NOTE**: Requires `--unsafe-fixes` to trigger the autofix. Without it, ruff says
"1 hidden fix can be enabled with --unsafe-fixes".

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min screening limit reached" with title "ATE Screening"' ) &

claude
```

#### Paste this prompt

```
Investigate and fix Ruff bug #16500: C416+C409 autofix conflict in preview mode
URL: https://github.com/astral-sh/ruff/issues/16500

Bug: In preview mode, C416 and C409 autofix conflict. C416 simplifies
`tuple([x for x in range(10) if x % 2 == 0])` to
`tuple(x for x in range(10) if x % 2 == 0)` (removes list comprehension).
Then C409 should recognize this as a tuple of a generator and leave it alone,
but instead it converts the generator expression in a way that changes
performance characteristics.

Reproduction (reproduction.py):
  tuple([x for x in range(10) if x % 2 == 0])

Command: ruff check --preview --select C4 --fix --unsafe-fixes reproduction.py
Expected: Correct autofix (list comprehension preserved or properly simplified)
Actual: C409 converts to generator expression (performance regression)

Note: --unsafe-fixes is required to trigger the autofix.

The file is in data/screening/bug-16500/.

The Ruff source is in data/ruff/ (v0.15.1). Diagnose the root cause and
produce a fix. Budget ~25 tool calls.
```

#### Hard stop at 30 min — press Escape

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note end time: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening/bug-16500/patch
wc -l data/screening/bug-16500/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
git -C data/ruff status   # must be clean
```

#### Record verdict

Edit `data/screening/bug-16500/metadata.json`:

```json
{
  "bug_id": 16500,
  "screening_date": "2026-02-XX",
  "status": "<KEEP | MAYBE | DROP>",
  "time_minutes": null,
  "dead_ends": null,
  "fix_produced": false,
  "fix_correct": null,
  "notes": ""
}
```

Update `config/screening_candidates.yaml` — change `status: pending` to verdict.

- [ ] Patch saved (if produced)
- [ ] `metadata.json` updated with verdict
- [ ] `screening_candidates.yaml` status updated
- [ ] Ruff reset and clean

---

### Bug 9 of 11: #17558 — Formatter vs linter disagreement (lines-after-imports)

**Tier**: C | **Category**: configuration | **Why hard**: Formatter and linter disagree on blank lines after imports, creating infinite cycle

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min screening limit reached" with title "ATE Screening"' ) &

claude
```

#### Paste this prompt

```
Investigate and fix Ruff bug #17558: Formatter vs linter disagreement on lines-after-imports
URL: https://github.com/astral-sh/ruff/issues/17558

Bug: The formatter and isort linter disagree on the number of blank lines
after imports, creating an infinite cycle in editors:
  1. ruff check --select I --fix → sets 1 blank line (per lines-after-imports=1)
  2. ruff format → sets 2 blank lines (formatter's default before a function)
  3. ruff check --select I → flags it again
  ...ad infinitum

Config (ruff.toml):
  line-length = 120
  target-version = "py311"
  [lint.isort]
  lines-after-imports = 1

Reproduction (reproduction.py):
  import os
  import sys

  def test():
      pass

Steps to reproduce:
  ruff check reproduction.py --select I --fix --config ruff.toml
  ruff format reproduction.py --config ruff.toml
  ruff check reproduction.py --select I --config ruff.toml

Expected: No linter warning after formatting (they should agree)
Actual: Linter flags it again because formatter overrode the blank line count

Files are in data/screening/bug-17558/.

The Ruff source is in data/ruff/ (v0.15.1). Diagnose the root cause and
produce a fix. Budget ~25 tool calls.
```

#### Hard stop at 30 min — press Escape

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note end time: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening/bug-17558/patch
wc -l data/screening/bug-17558/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
git -C data/ruff status   # must be clean
```

#### Record verdict

Edit `data/screening/bug-17558/metadata.json`:

```json
{
  "bug_id": 17558,
  "screening_date": "2026-02-XX",
  "status": "<KEEP | MAYBE | DROP>",
  "time_minutes": null,
  "dead_ends": null,
  "fix_produced": false,
  "fix_correct": null,
  "notes": ""
}
```

Update `config/screening_candidates.yaml` — change `status: pending` to verdict.

- [ ] Patch saved (if produced)
- [ ] `metadata.json` updated with verdict
- [ ] `screening_candidates.yaml` status updated
- [ ] Ruff reset and clean

---

### Bug 10 of 11: #9958 — Formatter trims lines after semicolons

**Tier**: C | **Category**: configuration | **Why hard**: Trivia handling — semicolons confuse empty-line preservation

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min screening limit reached" with title "ATE Screening"' ) &

claude
```

#### Paste this prompt

```
Investigate and fix Ruff bug #9958: Formatter trims empty lines after semicolons
URL: https://github.com/astral-sh/ruff/issues/9958

Bug: The formatter incorrectly collapses blank lines and removes trailing
semicolons when a multiline string ends with a semicolon. Two blank lines
between statements should be preserved, but the semicolon confuses the
formatter's empty-line preservation logic.

Reproduction (reproduction.py):
  b = """
      This looks like a docstring but is not in a notebook because notebooks can't be imported as a module.
      Ruff should leave it as is
  """;


  a = "another normal string"

Command: ruff format reproduction.py
Expected: Two blank lines between statements preserved, semicolon left as-is
Actual: Blank lines collapsed and/or semicolon removed

The file is in data/screening/bug-9958/.

The Ruff source is in data/ruff/ (v0.15.1). Diagnose the root cause and
produce a fix. Budget ~25 tool calls.
```

#### Hard stop at 30 min — press Escape

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note end time: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening/bug-9958/patch
wc -l data/screening/bug-9958/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
git -C data/ruff status   # must be clean
```

#### Record verdict

Edit `data/screening/bug-9958/metadata.json`:

```json
{
  "bug_id": 9958,
  "screening_date": "2026-02-XX",
  "status": "<KEEP | MAYBE | DROP>",
  "time_minutes": null,
  "dead_ends": null,
  "fix_produced": false,
  "fix_correct": null,
  "notes": ""
}
```

Update `config/screening_candidates.yaml` — change `status: pending` to verdict.

- [ ] Patch saved (if produced)
- [ ] `metadata.json` updated with verdict
- [ ] `screening_candidates.yaml` status updated
- [ ] Ruff reset and clean

---

### Bug 11 of 11: #21098 — FURB142 generator parenthesization

**Tier**: C | **Category**: autofix_convergence | **Why hard**: Autofix drops parentheses, producing semantically wrong code

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min screening limit reached" with title "ATE Screening"' ) &

claude
```

#### Paste this prompt

```
Investigate and fix Ruff bug #21098: FURB142 autofix drops necessary parentheses
URL: https://github.com/astral-sh/ruff/issues/21098

Bug: FURB142 converts `for x in ...: s.add(c for c in x)` to
`s.update(c for c in x for x in ...)` without parenthesizing the inner
generator, which changes the semantics (flattens nested generators into one)
and produces a NameError at runtime.

Reproduction (reproduction.py):
  s = set()
  for x in ("abc", "def"):
      s.add(c for c in x)

Command: ruff check --isolated --select FURB142 --preview --fix reproduction.py
Expected: s.update((c for c in x) for x in ("abc", "def"))  [parenthesized]
Actual: s.update(c for c in x for x in ("abc", "def"))  [NameError at runtime]

The file is in data/screening/bug-21098/.

The Ruff source is in data/ruff/ (v0.15.1). Diagnose the root cause and
produce a fix. Budget ~25 tool calls.
```

#### Hard stop at 30 min — press Escape

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note end time: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening/bug-21098/patch
wc -l data/screening/bug-21098/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
git -C data/ruff status   # must be clean
```

#### Record verdict

Edit `data/screening/bug-21098/metadata.json`:

```json
{
  "bug_id": 21098,
  "screening_date": "2026-02-XX",
  "status": "<KEEP | MAYBE | DROP>",
  "time_minutes": null,
  "dead_ends": null,
  "fix_produced": false,
  "fix_correct": null,
  "notes": ""
}
```

Update `config/screening_candidates.yaml` — change `status: pending` to verdict.

- [ ] Patch saved (if produced)
- [ ] `metadata.json` updated with verdict
- [ ] `screening_candidates.yaml` status updated
- [ ] Ruff reset and clean

---

## 5. Post-Screening: Finalize Portfolio

After screening is complete (or 8+ KEEPs found):

### 5.1 Tally results

```bash
# Quick summary from metadata files
for d in data/screening/bug-*/metadata.json; do
  echo "$(basename $(dirname $d)): $(python3 -c "import json; print(json.load(open('$d')).get('status','?'))")"
done
```

### 5.2 Select Round 2 primary bugs

Pick 8 bugs from the KEEP pool. Aim for:
- Category diversity (not all parser bugs)
- Mix of difficulty levels (some where Claude gets close, some where it fails entirely)
- At least 2 correlation pairs (bugs that share a subsystem)

### 5.3 Update config

Add selected bugs to `config/bugs.yaml` under `round2: primary:` with their
reproduction cases, categories, and complexity ratings.

### 5.4 Add reproduction cases

Add Round 2 entries to `src/ate/scoring/reproduction.py` `REPRO_CASES` dict.

### 5.5 Generate Round 2 treatment runbooks

These will be similar to Round 1 runbooks but with the new bug list. Can be
generated with the existing harness (`uv run ate run scaffold <treatment> <bug>`).

---

## 6. Final Checklist

### Per candidate:
- [ ] Ruff clean before session (`git checkout . && git clean -fd`)
- [ ] 30-min Claude session (no nudges)
- [ ] Patch saved (if produced)
- [ ] `metadata.json` updated with verdict
- [ ] `screening_candidates.yaml` status updated
- [ ] Ruff reset after session

### After all screening:
- [ ] 8+ KEEP candidates identified
- [ ] Round 2 primary bugs selected (8)
- [ ] `config/bugs.yaml` round2 section populated
- [ ] Reproduction cases added to scoring module
