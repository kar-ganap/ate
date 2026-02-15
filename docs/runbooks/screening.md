# Runbook: Round 2 Bug Screening

**Goal**: Screen ~16 candidate bugs to find ~8 where Claude Opus 4.6 genuinely
struggles (fails, takes 30+ min, or requires multiple dead ends).

**Format**: Treatment 0b style — single Claude session, single bug, interactive.
30-minute hard time limit per candidate.

**Expected Duration**: 8-12 hours total (16 candidates x 30 min + overhead).
Can be spread across multiple sittings.

**Ruff Version**: v0.15.1 (latest as of 2026-02-15)

---

## 1. One-Time Setup

### 1.1 Re-pin Ruff to v0.15.1

The experiment Ruff is currently at v0.14.14 (Round 1). Re-pin for Round 2:

```bash
cd ~/Documents/Personal/random_projects/others_projects_checkout/ate
```

Edit `src/ate/ruff.py` line 8:
```python
RUFF_TAG = "0.15.1"  # was "0.14.14"
```

Edit `scripts/pin_ruff.sh` line 4:
```bash
RUFF_TAG="0.15.1"  # was "0.14.14"
```

Then pin and build:
```bash
# Remove old checkout
rm -rf data/ruff

# Re-pin
uv run ate ruff pin

# Build (takes a few minutes)
uv run ate ruff build

# Verify
uv run ate run preflight
```

- [ ] `ruff.py` RUFF_TAG updated to `0.15.1`
- [ ] `pin_ruff.sh` RUFF_TAG updated to `0.15.1`
- [ ] `ate ruff pin` succeeded
- [ ] `ate ruff build` succeeded
- [ ] `ate run preflight` passes

### 1.2 Verify Claude Code version

```bash
claude --version
```

- [ ] Version noted: ___________

### 1.3 Confirm no Agent Teams

```bash
echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS
# Should be empty / unset
```

- [ ] Agent Teams env var is NOT set

---

## 2. Per-Candidate Protocol

Repeat this protocol for each candidate. Work through Tier A first, then B, then C.
Stop once you have 8+ KEEPs (you don't need to screen them all).

### 2.1 Pre-Check

Run the helper script:

```bash
./scripts/screen_bug.sh <BUG_ID>
```

This will:
- Check if the issue is still open
- Check for competing PRs
- Create `data/screening/bug-<id>/` with templates

**Gate**: If the issue is closed or has a merged PR, mark as `closed`/`has-pr` in
`config/screening_candidates.yaml` and skip to the next candidate.

- [ ] Issue is still open
- [ ] No merged competing PRs

### 2.2 Verify Reproduction

Before spending 30 min on a Claude session, confirm the bug reproduces against
v0.15.1. Some Round 1 bugs were fixed in newer Ruff versions.

Write a minimal reproduction case and test it:

```bash
# Write repro (customize per bug — see candidate table below)
cat > /tmp/repro.py << 'EOF'
<reproduction code here>
EOF

# Test against pinned Ruff
data/ruff/target/debug/ruff check /tmp/repro.py
# or: data/ruff/target/debug/ruff format /tmp/repro.py
# or: data/ruff/target/debug/ruff check --fix /tmp/repro.py
```

Save the repro case:
```bash
cp /tmp/repro.py data/screening/bug-<BUG_ID>/reproduction.py
```

**Gate**: If the bug does NOT reproduce (already fixed in v0.15.1), mark as
`closed` in `config/screening_candidates.yaml` and skip.

- [ ] Bug reproduces against v0.15.1

### 2.3 Reset Ruff

```bash
git -C data/ruff checkout .
git -C data/ruff clean -fd
git -C data/ruff status   # must be clean
```

- [ ] Ruff working tree is clean

### 2.4 Start Screening Session

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note start time: ___________

# Set a 30-minute timer (macOS)
# Option A: Terminal timer
( sleep 1800 && osascript -e 'display notification "30 min screening limit reached" with title "ATE Screening"' ) &

# Option B: Just watch the clock

claude
```

### 2.5 Paste the Opening Prompt

Use this template (fill in from the candidate table below):

```
Investigate and fix Ruff bug #<BUG_ID>: <TITLE>
URL: <URL>
Category: <CATEGORY>

<REPRODUCTION / DESCRIPTION — copy from issue or use your repro case>

The Ruff source is in data/ruff/ (v0.15.1). Diagnose the root cause and
produce a fix. Budget ~25 tool calls.
```

### 2.6 Monitor (glance every 2-3 min)

**Signs of struggling (good — this is what we want for Round 2):**
- Multiple dead-end approaches
- Re-reading the same files without progress
- Incorrect fix attempts that fail tests
- "Let me try a different approach" more than twice
- Spending 5+ minutes in a single subsystem without a theory

**Signs of easy solve (bad — same as Round 1):**
- Locates root cause within 5 minutes
- Single clean edit that fixes the issue
- Done in under 15 minutes

**Do NOT nudge or help.** This is a calibration session — we need to see how
Claude performs unassisted.

### 2.7 Hard Stop at 30 Minutes

At 30 minutes, press Escape regardless of progress state. Record where Claude
was in the process.

### 2.8 Capture Results

Exit Claude, then:

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # note end time: ___________

# Check if a fix was produced
git -C data/ruff diff --stat

# If there's a diff, save it
git -C data/ruff diff > data/screening/bug-<BUG_ID>/patch

# Check patch line count
wc -l data/screening/bug-<BUG_ID>/patch

# Reset Ruff for next candidate
git -C data/ruff checkout .
git -C data/ruff clean -fd
```

### 2.9 Record Verdict

Update `data/screening/bug-<BUG_ID>/metadata.json`:

```json
{
  "bug_id": <BUG_ID>,
  "screening_date": "<today>",
  "status": "<KEEP | MAYBE | DROP>",
  "time_minutes": <actual time>,
  "dead_ends": <count of wrong approaches>,
  "fix_produced": <true | false>,
  "fix_correct": <true | false | null if not tested>,
  "notes": "<one-line summary>"
}
```

**Verdict criteria:**

| Verdict | Criteria | Action |
|---------|----------|--------|
| **KEEP** | Claude fails to produce a fix, OR takes 30 min and still struggling | Add to Round 2 primary |
| **MAYBE** | Claude succeeds in 15-30 min but with dead ends | Add to Round 2 backup |
| **DROP** | Claude succeeds in <15 min cleanly | Too easy, skip |

Update `config/screening_candidates.yaml` — change `status: pending` to
`status: keep`, `status: maybe`, or `status: drop`.

Write observations in `data/screening/bug-<BUG_ID>/notes.md`.

### 2.10 Move to Next Candidate

Repeat from 2.1 for the next candidate.

---

## 3. Candidate Reference Table

Screen in this order (Tier A first — most likely to be hard enough).

### Tier A — Very Hard

| # | Bug ID | Title | Category | Prompt Hint |
|---|--------|-------|----------|-------------|
| 1 | **21896** | Parser relexing + unclosed strings | parser | Lexer/parser state sync when relexing after an unclosed f-string or string literal. F-string nesting and error recovery paths are involved. |
| 2 | **22930** | Parser stack overflow handling | parser | Deeply nested Python code causes a stack overflow in the parser. Need graceful error handling (recursion depth limit or iterative rewrite). |
| 3 | **20891** | F401+I002+PYI025 infinite loop | autofix | Three-rule autofix conflict: F401 (unused import), I002 (missing future annotations), PYI025 (set alias). Applying fixes for one triggers another in a loop. |
| 4 | **12611** | E302+I001 infinite loop (non-ASCII) | autofix | E302 (expected blank lines) + I001 (import sorting) conflict. Autofix loops. Has a minimal ASCII reproduction case. |

### Tier B — Hard

| # | Bug ID | Title | Category | Prompt Hint |
|---|--------|-------|----------|-------------|
| 5 | **12865** | DJ012 cross-file inheritance | semantic | DJ012 (Django model field order) requires cross-file analysis — fields inherited from parent models in other files need type inference. |
| 6 | **10874** | F811 cross-scope in stubs | scope | F811 (redefined unused name) false positive in `.pyi` stub files where names are intentionally re-exported across scope boundaries. |
| 7 | **19632** | F811 regression + typing-modules config | semantic | F811 regression: `typing-modules` config setting stopped working after a refactor. Bisected to a specific commit. Config-dependent semantic analysis. |
| 8 | **14695** | ANN401 stack overflow (escape seqs) | parser | ANN401 (dynamically typed Any) triggers a stack overflow when processing string annotations with certain escape sequences. Recursion depth issue. |

### Tier C — Moderate-Hard

| # | Bug ID | Title | Category | Prompt Hint |
|---|--------|-------|----------|-------------|
| 9 | **16500** | C416+C409 autofix conflict (preview) | autofix | C416 (unnecessary list comprehension) + C409 (unnecessary literal in tuple/list) conflict in preview mode. Applying both autofixes produces invalid code. |
| 10 | **21332** | LSP unused-noqa diagnostic tags | config | LSP server reports unused `# noqa` comments with wrong diagnostic tags, causing IDE problems. Diagnostic structure changes needed. |
| 11 | **17558** | LSP formatter/linter race condition | config | LSP server has a race condition between formatting and linting — sometimes returns stale results. Server state management issue. |
| 12 | **20847** | LSP workspace config resolution | config | Multi-root workspace doesn't resolve `ruff.toml` correctly. Configuration hierarchy for nested projects is wrong. |
| 13 | **15510** | Parser diagnostic rendering regression | parser | Error messages render incorrectly for certain files — `annotate-snippets` crate edge case with multi-byte characters or specific line endings. |
| 14 | **9958** | Formatter trims lines after semicolons | config | Formatter strips trailing content after semicolons instead of splitting to new lines. Trivia (whitespace/comment) handling issue. |
| 15 | **21098** | FURB142 generator parenthesization | autofix | FURB142 autofix produces syntactically invalid code by dropping necessary parentheses around generator expressions. |

---

## 4. Stopping Criteria

You can stop screening early if:

- **8+ KEEPs**: You have enough primary bugs for Round 2. Remaining MAYBEs become backup.
- **All Tier A+B screened**: If you have 6+ KEEPs from Tiers A and B, skip Tier C.
- **Diminishing returns**: If Tier C candidates are all DROPs, stop — those subsystems
  are too easy.

---

## 5. Post-Screening: Finalize Portfolio

After screening is complete:

### 5.1 Tally results

```bash
# Quick summary
grep -r '"status"' data/screening/*/metadata.json | sort
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

## 6. Checklist Summary

### Per candidate:
- [ ] `screen_bug.sh` — issue open, no competing PRs
- [ ] Reproduction verified against v0.15.1
- [ ] Ruff clean before session
- [ ] 30-min Claude session (no nudges)
- [ ] Patch saved (if produced)
- [ ] `metadata.json` updated with verdict
- [ ] `notes.md` written
- [ ] `screening_candidates.yaml` status updated
- [ ] Ruff reset after session

### After all screening:
- [ ] 8+ KEEP candidates identified
- [ ] Round 2 primary bugs selected (8)
- [ ] `config/bugs.yaml` round2 section populated
- [ ] Reproduction cases added to scoring module
