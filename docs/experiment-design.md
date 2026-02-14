# Experiment Design

The north star for the Agent Teams Eval project. All experimental choices live
here. Changes require a Change Log entry (see bottom).

## Hypothesis & Framing

We compare Claude Code's **Agent Teams** (experimental multi-agent coordination)
against **default Claude Code usage** (single-agent, no teams) for a bug triage and
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
| 4 | Team size | Controlled | 1×8 (control only) / 4×2 / 8×1 |
| 5 | Communication guidance | Semi-controlled | Neutral / Encourage / Discourage (N/A for controls) |
| 6 | Communication behavior | Observational | Measured via message count/content/impact |

## Treatment Matrix

| # | Label | Decomp | Prompt | Delegate | Size | Comm | Agent Teams |
|---|-------|--------|--------|----------|------|------|-------------|
| 0a | Control: Full Context | Explicit | Detailed | N/A | 1×8 | N/A | OFF |
| 0b | Control: Swim Lanes | Explicit | Detailed | N/A | 8×1 | N/A | OFF |
| 1 | Structured Team | Explicit | Detailed | On | 4×2 | Neutral | ON |
| 2a | Autonomous + Encourage | Autonomous | Vague | On | 4×2 | Encourage | ON |
| 2b | Autonomous + Discourage | Autonomous | Vague | On | 4×2 | Discourage | ON |
| 3 | Invest in Prompts | Autonomous | Detailed | On | 4×2 | Neutral | ON |
| 4 | Player-Coach | Autonomous | Vague | Off | 4×2 | Neutral | ON |
| 5 | Max Parallelism | Explicit | Detailed | On | 8×1 | Neutral | ON |

**Treatment 0 variants:**
- **0a (Full Context)**: 1 interactive session covering all 8 bugs sequentially.
  Represents a single developer using Claude for all bugs — the natural default.
- **0b (Swim Lanes)**: 8 separate interactive sessions, 1 bug each.
  Represents 8 developers independently using Claude ("stay in your swim lane").

Neither variant uses `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Claude may
internally use subagents (Task tool) — that's Claude's natural behavior, not a
confound. The only controlled variable vs Treatments 1-5 is: Agent Teams OFF.

## Bug Assignment

### Cross-Subsystem Pairing (explicit treatments: 0b, 1, 5)

Note: Treatment 0a presents all 8 bugs in a single opening prompt. The bugs are listed
in **primary portfolio order** (#20945, #18654, #7847, #4384, #19301, #22221, #22528,
#22494) — NOT grouped by agent pairing, to avoid priming cross-bug connections.

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

**Tier 3 analysis protocol for autonomous assignments**: If an autonomous lead
assigns both bugs from a hidden correlation pair to the same agent, that pair's
Tier 3 score is flagged as "structurally advantaged — not comparable." Only compare
Tier 3 scores for pairs where both treatments assigned correlated bugs to different
agents. This concern is specific to Tier 3; Tiers 1, 2, 4, 5 are minimally affected
by assignment differences.

## Key Comparisons

### Clean single-variable comparisons

| Comparison | What it isolates | Confounds |
|------------|-----------------|-----------|
| **0b vs 5** | **Agent Teams value** (primary question) | None — both 8×1, explicit, detailed |
| **0a vs 0b** | Cross-bug context value (single agent) | Session scope (1 vs 8) |
| **1 vs 5** | Team size effect (4×2 vs 8×1) | None |
| **1 vs 3** | Decomposition (explicit vs autonomous) | None — both detailed, on, 4×2, neutral |
| **2a vs 2b** | Communication guidance (encourage vs discourage) | None |

### Two-variable comparisons (directionally useful, not definitive)

| Comparison | What it targets | Confounds |
|------------|----------------|-----------|
| 0a vs 1 | Single agent vs organized team | Size (1×8 vs 4×2) + Agent Teams |
| 0a vs 5 | Full context vs parallel team | Size (1×8 vs 8×1) + Agent Teams |
| 2a vs 3 | Prompt investment effect | Comm guidance (encourage → neutral) |
| 2a vs 4 | Coordinator role purity (delegate on vs off) | Comm guidance (encourage → neutral) |
| 4 vs 3 | Prompt specificity (alternative) | Delegate mode (off → on) |

**Autonomous assignment caveat (all autonomous comparisons)**: At Tier 3 (correlation
discovery), these are only clean for correlation pairs where both treatments assigned
the correlated bugs to different agents. See Autonomous Treatment Rules above.
Tiers 1, 2, 4, 5 are minimally affected.

### Design limitations

This is a **fractional factorial design** (8 treatments covering 5+ dimensions). A full
factorial would require 32+ treatments, which is infeasible. As a result:

- **No clean single-variable comparison exists for prompt specificity or delegate mode.**
  Every pairing that varies prompt also varies communication guidance and/or delegate mode.
  The two-variable comparisons above are directionally informative but not definitive.
- Treatment 2a (Encourage) is the only treatment with non-Neutral communication guidance
  among the autonomous treatments. This makes 2a a useful anchor for the communication
  comparison (2a vs 2b) but introduces a communication confound in other 2a-based pairings.
- The clean comparisons (0b vs 5, 1 vs 5, 1 vs 3, 2a vs 2b) answer the most important
  questions: does Agent Teams help, does team size matter, does decomposition matter,
  and does communication guidance matter.

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
| Cross-treatment agreement | Cluster diagnoses per bug across all 8 treatments, compute % plurality agreement | Diagnostic clarity vs ambiguity per bug |
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
- Tier 2: 64 manual evaluations (8 bugs × 8 treatments), ~1 day
- Tier 2.5: Semi-automated (Claude session classifies, human validates)
- Tier 3: 24 assessments (3 pairs × 8 treatments)
- Tier 4: Only for 6 agent team runs (Treatments 1-5), from session logs

## Execution Protocol

All treatments are interactive with identical soft budget constraints. The only
controlled variable is whether `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set.

### Shared Protocol (all treatments)

- Interactive Claude Code session
- **Pin Claude Code version**: record `claude --version` before starting; do not
  update Claude Code mid-experiment. If an update is unavoidable, note it in the
  Change Log and re-run affected treatments.
- **Pin model**: use the same model for all treatments (record model name in metadata).
  Do not rely on default model selection — it may change across sessions.
- CLAUDE.md soft instruction: "Budget ~25 tool calls per bug before reporting"
- Human monitors in real-time, Escape if stuck
- Document actual turn count per agent per bug post-hoc from transcripts
- Ruff source at `data/ruff/` (pinned to v0.14.14)

### Treatment 0a (Full Context) — Single session, no Agent Teams

- `claude` (no env var)
- 1 session covering all 8 bugs sequentially
- Opening prompt lists all 8 bugs in primary portfolio order (see Bug Assignment)
- Claude may use Task tool (subagents) naturally — this is data, not a confound

### Treatment 0b (Swim Lanes) — 8 sessions, no Agent Teams

- `claude` (no env var)
- 8 fresh sessions, 1 bug per session
- Each session gets a single-bug opening prompt
- No cross-bug context (sessions are independent)

### Treatments 1–5 (Agent Teams) — Interactive with team formation

- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude`
- Form team per treatment config (size, delegate mode, communication guidance)
- For explicit treatments (1, 5): assign bugs per the assignment table
- For autonomous treatments (2a, 2b, 3, 4): let the lead assign; document choices
- Soft budget applies equally across all agent team treatments

## Reproducibility

### What's fully reproducible

- Bug portfolio and treatment definitions (committed YAML)
- Scoring rubrics and algorithms (committed code)
- Ruff pinned to v0.14.14 (committed script)
- Session guide templates (version-controlled)

### What's not reproducible (all treatments equally)

- Exact turn counts (soft budget, human judgment)
- Exact prompts typed (documented post-hoc via session guides)
- Session-level randomness (model non-determinism)

### Mitigations

- Session guides with standardized opening prompts (version-controlled)
- CLAUDE.md soft budget instruction ("~25 tool calls per bug")
- Document actual turn counts post-hoc from transcripts
- Screen recordings as supplementary evidence
- Fresh sessions per bug for scoring independence

All treatments share the same reproducibility profile — no asymmetry between
control and agent team treatments.

## Cost Model

- All 8 treatments run interactively under Claude Max subscription
- Total out of pocket: **$0** (no API costs)
- Token usage captured from session transcripts for cross-treatment comparison

## Presentation & Tooling

- **Primary source of truth**: GitHub repo
- **Language**: Python (for harness, analysis, scoring scripts)
- Derivative presentations (blog post, slides, etc.) can be spawned from the repo

## Change Log

| Date | Change | Rationale | Phase |
|------|--------|-----------|-------|
| 2026-02-05 | Initial design frozen | Consolidation from design conversations | 0 |
| 2026-02-09 | Swapped #17010 → #22494 | #17010 (server panic, glob braces) fixed in v0.14.14; replaced with #22494 (formatter range formatting) per backup rules | 1 |
| 2026-02-14 | Treatment 0 → interactive, split into 0a/0b | Programmatic `claude -p` introduced 5 confounds vs interactive treatments (execution mode, budget, model, tools, human presence). Making all treatments interactive reduces the independent variable to a single clean bit: Agent Teams ON/OFF. Split into 0a (1 session, all 8 bugs) and 0b (8 sessions, 1 bug each) for richer comparisons. Cost goes from ~$25-40 API to $0 (all subscription). | 2 |
| 2026-02-14 | Added Tier 3 analysis protocol for autonomous assignments | Autonomous leads may co-assign correlated bugs to the same agent, inflating Tier 3 scores. Protocol: document all assignments, flag co-assigned pairs as "structurally advantaged — not comparable." | 2 |
| 2026-02-14 | Key comparisons audit: fixed confounds, added missing comparisons | 2a vs 3 and 2a vs 4 incorrectly listed "None" confounds — both have communication guidance confound (Encourage→Neutral). Added 1 vs 3 (clean decomposition comparison). Split table into clean vs two-variable comparisons. Added design limitations note acknowledging fractional factorial trade-offs. Pinned model/version in protocol. Specified Treatment 0a bug ordering (portfolio order, not agent-pair order) to avoid priming. | 2 |
