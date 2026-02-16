# Runbook: ty Type Checker Mini-Screening

**Goal**: Screen 6 ty bugs spanning the decomposability spectrum (D1-D5) to
determine if ty breaks the ceiling effect observed with Ruff linter bugs.

**Format**: Treatment 0b style — single Claude session, single bug, interactive.
30-minute hard time limit per candidate.

**Expected Duration**: 3-4 hours total (6 candidates x 30 min + overhead).

**ty Version**: 0.0.17 (ruff commit `10c082f616d8296df0cd3489a98db8c5d40628d1`)

**All 6 bugs verified**: Reproduction cases confirmed against pinned commit.

---

## 1. Pre-checks

```bash
cd ~/Documents/Personal/random_projects/others_projects_checkout/ate

# Verify ty build
data/ruff/target/debug/ty --version
# Expected: ty ruff/0.15.1+4 (10c082f61 2026-02-13)

# Verify Claude Code version
claude --version
# Note version: ___________

# Confirm no Agent Teams
echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS
# Should be empty / unset

# Verify Ruff is clean
git -C data/ruff status   # must be clean
```

- [ ] ty version confirmed: `ruff/0.15.1+4 (10c082f61)`
- [ ] Claude Code version noted: ___________
- [ ] Agent Teams env var is NOT set
- [ ] Ruff working tree is clean

---

## 2. Decision Criteria

| Result | Action |
|--------|--------|
| 0-1 bugs take 30+ min | ty also has ceiling effect. Abort switch. |
| 2-3 bugs take 30+ min | ty works! Commit to full switch. |
| 4+ bugs take 30+ min | Even D2 bugs are hard in ty. Recalibrate portfolio. |

---

## 3. Bug Sessions

Work through in D-level order (D1 first, D5 last).

---

### Bug 1 of 6: #2644 — getattr narrowing (D1)

**D-Level**: D1 | **Category**: narrowing | **Expected**: <15 min (DROP)

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min limit" with title "ty Screening"' ) &
claude
```

#### Paste this prompt

```
Investigate and fix ty type checker bug #2644: getattr narrowing with string literal
URL: https://github.com/astral-sh/ty/issues/2644

Bug: ty should narrow the type after a `getattr(x, "flag")` truthiness check,
since the attribute name is a string literal. Currently it does not narrow.

Reproduction file: data/screening-ty/bug-2644/reproduction.py

To run ty:
  cd data/ruff && cargo run --bin ty -- check ../screening-ty/bug-2644/reproduction.py

Expected output: reveal_type(x) shows C (narrowed from C | None)
Actual output: reveal_type(x) shows C | None (not narrowed)

The ty source lives in the `ty_*` crates under data/ruff/crates/. The primary
type checking logic is in crates/ty_python_semantic/. Tests use the mdtest
format (Markdown files in crates/ty_python_semantic/resources/mdtest/).
Run tests: cargo test -p ty_python_semantic --test mdtest
Update snapshots: cargo insta accept

Diagnose the root cause and produce a fix. Budget ~25 tool calls.
```

#### Hard stop at 30 min — press Escape

#### After (exit Claude first)

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note end time: ___________
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening-ty/bug-2644/patch
wc -l data/screening-ty/bug-2644/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
git -C data/ruff status   # must be clean
```

#### Record verdict

| Field | Value |
|-------|-------|
| Time (min) | |
| Dead ends | |
| Fix produced | |
| Fix correct | |
| Verdict | KEEP / MAYBE / DROP |
| Notes | |

- [ ] Patch saved (if produced)
- [ ] Ruff reset and clean

---

### Bug 2 of 6: #2480 — NoReturn narrowing at module scope (D2)

**D-Level**: D2 | **Category**: narrowing + scope | **Expected**: 10-20 min

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min limit" with title "ty Screening"' ) &
claude
```

#### Paste this prompt

```
Investigate and fix ty type checker bug #2480: NoReturn narrowing at module scope
URL: https://github.com/astral-sh/ty/issues/2480

Bug: After `if not api_key: exit(1)`, api_key should be narrowed from
str | None to str because exit() returns NoReturn. This works inside
functions but NOT at module/global scope.

Context: Parent issue #690 was closed after PR #23109 added TDD-based
narrowing constraints. However, maintainer sharkdp confirmed this specific
sub-case (module scope) was NOT fixed by that PR.

Reproduction file: data/screening-ty/bug-2480/reproduction.py

To run ty:
  cd data/ruff && cargo run --bin ty -- check ../screening-ty/bug-2480/reproduction.py

Expected output: reveal_type(api_key) shows str
Actual output: reveal_type(api_key) shows str | None

The ty source lives in the `ty_*` crates under data/ruff/crates/. The primary
type checking logic is in crates/ty_python_semantic/. Tests use the mdtest
format (Markdown files in crates/ty_python_semantic/resources/mdtest/).
Run tests: cargo test -p ty_python_semantic --test mdtest
Update snapshots: cargo insta accept

Diagnose the root cause and produce a fix. Budget ~25 tool calls.
```

#### Hard stop at 30 min — press Escape

#### After

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening-ty/bug-2480/patch
wc -l data/screening-ty/bug-2480/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
```

#### Record verdict

| Field | Value |
|-------|-------|
| Time (min) | |
| Dead ends | |
| Fix produced | |
| Fix correct | |
| Verdict | KEEP / MAYBE / DROP |
| Notes | |

---

### Bug 3 of 6: #2732 — bool|None narrowing after == (D2)

**D-Level**: D2 | **Category**: narrowing | **Expected**: 10-20 min

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min limit" with title "ty Screening"' ) &
claude
```

#### Paste this prompt

```
Investigate and fix ty type checker bug #2732: bool|None not narrowed after == comparison
URL: https://github.com/astral-sh/ty/issues/2732

Bug: After `if bn == b:` where bn: bool | None and b: bool, bn should be
narrowed to bool (since None == bool is always False). Currently it remains
bool | None.

Note: An open PR #22799 exists but has not been merged.

Reproduction file: data/screening-ty/bug-2732/reproduction.py

To run ty:
  cd data/ruff && cargo run --bin ty -- check ../screening-ty/bug-2732/reproduction.py

Expected output: reveal_type(bn) shows bool
Actual output: reveal_type(bn) shows bool | None

The ty source lives in the `ty_*` crates under data/ruff/crates/. The primary
type checking logic is in crates/ty_python_semantic/. Tests use the mdtest
format (Markdown files in crates/ty_python_semantic/resources/mdtest/).
Run tests: cargo test -p ty_python_semantic --test mdtest
Update snapshots: cargo insta accept

Diagnose the root cause and produce a fix. Budget ~25 tool calls.
```

#### After

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening-ty/bug-2732/patch
wc -l data/screening-ty/bug-2732/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
```

#### Record verdict

| Field | Value |
|-------|-------|
| Time (min) | |
| Dead ends | |
| Fix produced | |
| Fix correct | |
| Verdict | KEEP / MAYBE / DROP |
| Notes | |

---

### Bug 4 of 6: #2731 — Nonlocal writes ignored (D3-D4)

**D-Level**: D3-D4 | **Category**: control flow + closures | **Expected**: 20-30+ min

**Note**: All Python type checkers (pyright, pyrefly, mypy) fail on this bug.

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min limit" with title "ty Screening"' ) &
claude
```

#### Paste this prompt

```
Investigate and fix ty type checker bug #2731: Local reads ignore nonlocal writes
URL: https://github.com/astral-sh/ty/issues/2731

Bug: After calling bump() which increments count via `nonlocal`, ty still
thinks count is Literal[0]. This causes `assert count == 1` to appear
unreachable, cascading to Never for subsequent code.

This is a known hard problem — all major Python type checkers (pyright,
pyrefly, mypy) fail on this or equivalent variants.

Reproduction file: data/screening-ty/bug-2731/reproduction.py

To run ty:
  cd data/ruff && cargo run --bin ty -- check ../screening-ty/bug-2731/reproduction.py

Expected output: reveal_type(count) shows int (or at least not Literal[0])
Actual output: reveal_type(count) shows Literal[0], and everything after
  `assert count == 1` is treated as unreachable

The ty source lives in the `ty_*` crates under data/ruff/crates/. The primary
type checking logic is in crates/ty_python_semantic/. Tests use the mdtest
format (Markdown files in crates/ty_python_semantic/resources/mdtest/).
Run tests: cargo test -p ty_python_semantic --test mdtest
Update snapshots: cargo insta accept

Diagnose the root cause and produce a fix. Budget ~25 tool calls.
```

#### After

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening-ty/bug-2731/patch
wc -l data/screening-ty/bug-2731/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
```

#### Record verdict

| Field | Value |
|-------|-------|
| Time (min) | |
| Dead ends | |
| Fix produced | |
| Fix correct | |
| Verdict | KEEP / MAYBE / DROP |
| Notes | |

---

### Bug 5 of 6: #2808 — Loop hang (D4)

**D-Level**: D4 | **Category**: control flow + fatal | **Expected**: 20-30+ min

**WARNING**: ty will HANG on this reproduction. Use `timeout 30` when running.

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min limit" with title "ty Screening"' ) &
claude
```

#### Paste this prompt

```
Investigate and fix ty type checker bug #2808: Hang when analyzing loop
URL: https://github.com/astral-sh/ty/issues/2808

Bug: ty hangs (infinite loop) when analyzing a loop with recursive
self-referencing types. The recursive `b = [b]` creates types that cause
the fixpoint computation to not converge.

This is a regression — ty 0.0.16 did not hang. Introduced by PR #22794.

WARNING: ty will hang on this code. Use `timeout 30` when running:
  cd data/ruff && timeout 30 cargo run --bin ty -- check ../screening-ty/bug-2808/reproduction.py

Reproduction file: data/screening-ty/bug-2808/reproduction.py

Expected: ty terminates (with errors or warnings, but doesn't hang)
Actual: ty hangs indefinitely

The ty source lives in the `ty_*` crates under data/ruff/crates/. The primary
type checking logic is in crates/ty_python_semantic/. Tests use the mdtest
format (Markdown files in crates/ty_python_semantic/resources/mdtest/).
Run tests: cargo test -p ty_python_semantic --test mdtest
Update snapshots: cargo insta accept

Diagnose the root cause and produce a fix. Budget ~25 tool calls.
```

#### After

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening-ty/bug-2808/patch
wc -l data/screening-ty/bug-2808/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
```

#### Record verdict

| Field | Value |
|-------|-------|
| Time (min) | |
| Dead ends | |
| Fix produced | |
| Fix correct | |
| Verdict | KEEP / MAYBE / DROP |
| Notes | |

---

### Bug 6 of 6: #2799 — Constraint solver union heuristic (D5)

**D-Level**: D5 | **Category**: generics / constraint solver | **Expected**: 30+ min

#### Before

```bash
git -C data/ruff status   # must be clean
git -C data/ruff clean -fd
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

#### Start session

```bash
( sleep 1800 && osascript -e 'display notification "30 min limit" with title "ty Screening"' ) &
claude
```

#### Paste this prompt

```
Investigate and fix ty type checker bug #2799: Old constraint solver combines specializations using union
URL: https://github.com/astral-sh/ty/issues/2799

Bug: The constraint solver combines partial type mappings using union, which
is incorrect when type parameters have mixed variance across arguments.

Example: f[T](t: T, c: Callable[[T], int]) -> T called with f(Child(), callback)
where callback: Callable[[Base], int]. The solver should infer T = Child but
instead unions Child and Base (from the Callable's contravariant parameter)
to get T = Base.

The fix requires variance-aware constraint combination (lower/upper bounds)
instead of naive union. The issue contains a detailed theoretical explanation.

Reproduction file: data/screening-ty/bug-2799/reproduction.py

To run ty:
  cd data/ruff && cargo run --bin ty -- check ../screening-ty/bug-2799/reproduction.py

Expected output: reveal_type(result) shows Child
Actual output: reveal_type(result) shows Base

The ty source lives in the `ty_*` crates under data/ruff/crates/. The primary
type checking logic is in crates/ty_python_semantic/. Tests use the mdtest
format (Markdown files in crates/ty_python_semantic/resources/mdtest/).
Run tests: cargo test -p ty_python_semantic --test mdtest
Update snapshots: cargo insta accept

Diagnose the root cause and produce a fix. Budget ~25 tool calls.
```

#### After

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
git -C data/ruff diff --stat
git -C data/ruff diff > data/screening-ty/bug-2799/patch
wc -l data/screening-ty/bug-2799/patch
git -C data/ruff checkout .
git -C data/ruff clean -fd
```

#### Record verdict

| Field | Value |
|-------|-------|
| Time (min) | |
| Dead ends | |
| Fix produced | |
| Fix correct | |
| Verdict | KEEP / MAYBE / DROP |
| Notes | |

---

## 4. Post-Screening Tally

| # | Bug | D-Level | Time | Verdict | Fix? |
|---|-----|---------|------|---------|------|
| 1 | #2644 | D1 | | | |
| 2 | #2480 | D2 | | | |
| 3 | #2732 | D2 | | | |
| 4 | #2731 | D3-D4 | | | |
| 5 | #2808 | D4 | | | |
| 6 | #2799 | D5 | | | |

**KEEPs**: ___
**MAYBEs**: ___
**DROPs**: ___

### Decision

- [ ] 2+ bugs take 30+ min → Proceed with full ty switch
- [ ] 0-1 bugs take 30+ min → ty also has ceiling effect. Reconsider.
