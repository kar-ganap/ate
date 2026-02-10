# Experiment Design

The north star for the Agent Teams Eval project. All experimental choices live
here. Changes require a Change Log entry (see bottom).

## Hypothesis & Framing

We compare Claude Code's **Agent Teams** (experimental multi-agent coordination)
against **Subagents** (established single-agent delegation) for a bug triage and
fix pipeline on the Ruff Python linter.

This is an **observational study with partial determinism**. We don't claim
agent teams are better or worse — we measure where each approach excels, at what
cost, and what emergent behaviors arise.

Key framing choices:
- **Adversarial curation**: bugs are from different subsystems with genuine
  uncertainty about whether cross-bug connections exist. We don't pre-select
  known-correlated bugs (that would rig the experiment).
- **Diagnostic quality over correlation discovery**: we measure how well each
  approach diagnoses and fixes bugs, not just whether it finds connections.
- **Honest uncertainty**: some treatments will fail on some bugs. That's data.

## OSS Target

**Ruff** (https://github.com/astral-sh/ruff) — Python linter/formatter in Rust.

- Pin to a specific git commit before starting (determined in Phase 1)
- Build from source: `cargo build`
- Test: `cargo test` / `cargo nextest run`
- Snapshot testing with `cargo-insta`
- Has CLAUDE.md in repo

## Bug Portfolio

### Primary 8 Bugs

| # | Issue | Rule/Area | Category | Complexity |
|---|-------|-----------|----------|------------|
| 1 | #20945 | FAST001 false positive (None==None) | Semantic analysis | Simple |
| 2 | #18654 | ARG001 false positive (@singledispatch) | Semantic analysis | Medium |
| 3 | #7847 | B023 false positive (immediate invocation) | Scope/control flow | Medium |
| 4 | #4384 | C901 false positive (closure complexity) | Scope/control flow | Medium |
| 5 | #19301 | Parser indentation after backslashes | Parser | Hard |
| 6 | #22221 | F401 fix infinite loop (__all__ duplicates) | Autofix convergence | Medium |
| 7 | #22528 | Parser false syntax error (match-like) | Parser | Hard |
| 8 | #22494 | Formatter range formatting (semicolons) | Configuration | Medium |

### Backup 4 Bugs

| # | Issue | Can Replace |
|---|-------|-------------|
| 9 | #20891 | F401+I002+PYI025 infinite loop → replaces #19301 |
| 10 | #13337 | RUF001 emoji false positive → replaces any semantic bug |
| 11 | #17010 | Server panic (glob braces) — fixed in v0.14.14, dropped |
| 12 | #6432 | PD rules non-pandas → replaces any semantic bug |

### Swap Note

If #19301 (parser indentation) proves too hard or unworkable, swap back to
#20891 (infinite loop F401+I002+PYI025). #20891 was the original pick — it
pairs with #22221 as a matched autofix-convergence correlation pair. Swapping
it back in restores that pair at the cost of losing the parser correlation pair.

## Experimental Dimensions

| # | Dimension | Type | Values |
|---|-----------|------|--------|
| 1 | Decomposition | Controlled | Explicit (human assigns bugs) vs Autonomous (lead decides) |
| 2 | Prompt specificity | Semi-controlled | Detailed (full context) vs Vague (minimal guidance) |
| 3 | Delegate mode | Controlled, binary | On vs Off |
| 4 | Team size | Controlled | 4×2 vs 8×1 |
| 5 | Communication | Observational | Measured via message count/content/impact |

## Treatment Matrix

| # | Label | Decomp | Prompt | Delegate | Size | Comm |
|---|-------|--------|--------|----------|------|------|
| 0 | Control (Subagents) | Explicit | Detailed | N/A | 8×1 | N/A |
| 1 | Structured Team | Explicit | Detailed | On | 4×2 | Neutral |
| 2a | Autonomous + Encourage | Autonomous | Vague | On | 4×2 | Encourage |
| 2b | Autonomous + Discourage | Autonomous | Vague | On | 4×2 | Discourage |
| 3 | Invest in Prompts | Autonomous | Detailed | On | 4×2 | Neutral |
| 4 | Player-Coach | Autonomous | Vague | Off | 4×2 | Neutral |
| 5 | Max Parallelism | Explicit | Detailed | On | 8×1 | Neutral |

## Bug Assignment

### Cross-Subsystem Pairing (explicit treatments)

```
Agent 1: #20945 (semantic)  + #22528 (parser)
Agent 2: #18654 (semantic)  + #22494 (config/formatter)
Agent 3: #7847  (scope)     + #19301 (parser)
Agent 4: #4384  (scope)     + #22221 (autofix)
```

### Hidden Correlation Pairs (all split across agents)

| Pair | Bug A (Agent) | Bug B (Agent) | What they might share |
|------|---------------|---------------|----------------------|
| Semantic | #20945 (Agent 1) | #18654 (Agent 2) | ruff_python_semantic name resolution |
| Scope | #7847 (Agent 3) | #4384 (Agent 4) | Nested function scope tracking |
| Parser | #22528 (Agent 1) | #19301 (Agent 3) | Python grammar edge case handling |

### Autonomous Treatment Rules

For autonomous treatments (2a, 2b, 3, 4), the lead decides bug assignment.
Document what the lead chooses — the assignment itself is data.

## Key Comparisons

| Comparison | What it isolates |
|------------|-----------------|
| 0 vs 1 | Agent teams infrastructure value (structure held constant) |
| 1 vs 5 | Team size effect (4×2 vs 8×1) |
| 2a vs 2b | Communication encouragement effect |
| 2a vs 3 | Where to invest human effort (prompts vs assignment) |
| 2a vs 4 | Coordinator role purity (delegate on vs off) |
| 0 vs 5 | Most direct subagents-vs-teams (both 8×1, both detailed+explicit) |

## Measurement Framework

### Tier 1: Objective (automated, no human judgment)

| Metric | How | Scale |
|--------|-----|-------|
| Patch applies | `git apply` on pinned commit | Binary |
| Existing tests pass | `cargo test` after patch | Binary |
| Reproduction fixed | Run bug's repro case | Binary |
| No regressions | Full `cargo nextest run` | Binary |
| Token cost | Session JSON / `/cost` | Continuous ($) |
| Wall-clock time | Timestamps | Continuous (min) |

### Tier 2: Diagnostic rubric (human-scored, per bug per treatment)

| Criterion | 0 | 1 | 2 |
|-----------|---|---|---|
| Localization | Wrong file/module | Correct file, wrong function | Correct function/code path |
| Root cause | Wrong/no diagnosis | Right area, wrong mechanism | Correct mechanism |
| Fix direction | Wrong approach | Plausible but incomplete | Correct approach |
| Confidence calibration | High confidence + wrong | Roughly matched accuracy | Correctly flagged uncertainty |

Score per bug: 0–8. Per treatment (8 bugs): 0–64.

Scoring order: all treatments for Bug #1 together, then Bug #2, etc. (reduces
anchoring).

**Anchoring prevention**: Use a FRESH `claude` session for each bug (not
`/clear` — fully independent sessions). 8 independent scoring sessions, zero
anchoring risk.

### Tier 2.5: Consensus & Groupthink Analysis

| Metric | How | What it reveals |
|--------|-----|-----------------|
| Cross-treatment agreement | Cluster diagnoses per bug across all 7 treatments, compute % plurality agreement | Diagnostic clarity vs ambiguity per bug |
| Within-team agreement | Compare teammates' diagnoses before lead synthesis | Whether communication drove convergence |
| Agreement-accuracy correlation | Plot agreement level vs Tier 1 fix success | Whether consensus predicts correctness |
| Groupthink index | Cases where within-team agreement > cross-treatment agreement AND team's consensus fix fails Tier 1 | When communication produces confident wrong answers |

Diagnosis clustering: independent Claude session classifies each diagnosis into
categories, then compute agreement scores. More scalable and less biased than
pure human scoring.

**2×2 Interpretation Matrix**:

| | High within-team | Low within-team |
|---|---|---|
| **High cross-treatment** | Diagnostically clear, communication didn't matter | Healthy debate, truth won out |
| **Low cross-treatment** | GROUPTHINK RISK (teammates reinforced wrong answer) | Genuinely hard bug |

### Tier 3: Correlation Discovery (per potential correlation pair)

| Criterion | Measure |
|-----------|---------|
| Connection identified | Any agent/teammate claim bugs X and Y are related? (Binary) |
| Connection correct | Was claimed relationship valid? (Binary, post-hoc) |
| Discovery mechanism | Individual analysis / inter-agent message / lead synthesis / human prompt |
| Connection depth | Surface ("both parser bugs") vs specific ("both fail in handle_indentation() line 342") |

### Tier 4: Communication Metrics (agent teams only)

| Metric | How |
|--------|-----|
| Message count | Total inter-teammate messages per run |
| Directionality | Who messaged whom (adjacency matrix) |
| Taxonomy | Categorize: status update / finding shared / challenge / question / help request |
| Impact | Did recipient change approach after message? (Binary per message) |

### Tier 5: Process Metrics (secondary)

| Metric | How |
|--------|-----|
| Files explored | Unique files read per agent per bug |
| Exploration breadth vs depth | Files read : total lines read ratio |
| Dead ends | Approaches attempted then abandoned |
| Time to first correct insight | Wall-clock to first correct diagnostic statement |

### Ground Truth Layers

- **Objective** (Tier 1): Fully automated, binary outcomes. No human judgment
  enters. A patch either applies and passes tests, or it doesn't.
- **Subjective** (Tier 2): Human-scored with structured rubric. Scoring
  protocol minimizes bias (fresh session per bug, consistent ordering).
- **Semi-automated** (Tier 2.5): Claude classifies diagnoses into clusters,
  human validates the clustering. Explicitly hybrid.

### Scoring Logistics

- Tier 1: Fully automated via scripts
- Tier 2: 56 manual evaluations (8 bugs × 7 treatments), ~1 day
- Tier 2.5: Semi-automated (Claude session classifies, human validates)
- Tier 3: 21 assessments (3 pairs × 7 treatments)
- Tier 4: Only for 6 agent team runs, from session logs

## Execution Protocol

### Treatment 0 (Subagent Control) — `-p` mode with hard limits

```bash
timeout 1800 claude -p "Investigate Ruff issue #XXXXX..." \
  --max-turns 50 --model sonnet \
  --allowedTools "Read,Grep,Glob,Bash,Edit,Task" \
  --output-format json
```

- Hard budget: `--max-turns 50` + `timeout 1800` (30 min wall-clock)
- Structured JSON output captured automatically
- Subagent definitions in `.claude/agents/*.md` (version-controlled)
- Costs API tokens but bounded and fully reproducible

### Treatments 1–5 (Agent Teams) — Interactive with soft limits

- CLAUDE.md soft instruction: "Budget ~25 tool calls per bug before reporting"
- Human monitors in real-time, Escape if stuck
- Document actual turn count per teammate per bug post-hoc from transcripts
- Soft limit applies equally across all 6 agent team treatments
- Cross-team comparisons remain fair; only 0-vs-rest has hard/soft asymmetry

## Reproducibility

### What's fully reproducible

- Treatment 0 via `-p` mode (structured JSON output, `--max-turns 50`,
  `timeout 1800`, pinned commit, version-controlled agent definitions)
- Bug portfolio and treatment definitions (committed YAML)
- Scoring rubrics and algorithms (committed code)

### What's not reproducible in interactive mode

- Exact turn counts (soft budget, human judgment)
- Exact prompts typed (documented post-hoc)
- Session-level randomness (model non-determinism)

### Mitigations

- File-based subagent/agent definitions (version-controlled prompts)
- CLAUDE.md soft budget instruction ("~25 tool calls per bug")
- Document actual turn counts post-hoc from transcripts
- Screen recordings as supplementary evidence
- Fresh sessions per bug for scoring independence

### The asymmetry as a finding

"Subagents support hard programmatic budget controls; agent teams currently do
not." This is itself a data point about the two approaches, not a confound.

### What we chose NOT to do

Hooks-based enforcement (Option B) was considered and rejected — the added
complexity of shell-script turn counters was not worth the marginal
reproducibility gain for a portfolio project.

## Cost Model

- Claude Max subscription: all interactive sessions included
- $50 Extra Usage credits: buffer for overages
- Treatment 0 via `-p` mode: ~$25–40 API cost (only real expense)
- Total out of pocket: **~$25–40**
- If Treatment 0 run interactively instead: **~$0**

## Presentation & Tooling

- **Primary source of truth**: GitHub repo
- **Language**: Python (for harness, analysis, scoring scripts)
- Derivative presentations (blog post, slides, etc.) can be spawned from the repo

## Change Log

| Date | Change | Rationale | Phase |
|------|--------|-----------|-------|
| 2026-02-05 | Initial design frozen | Consolidation from design conversations | 0 |
| 2026-02-09 | Swapped #17010 → #22494 | #17010 (server panic, glob braces) fixed in v0.14.14; replaced with #22494 (formatter range formatting) per backup rules | 1 |
