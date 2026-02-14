# Phase 2 Retro: Execution Harness

## What Worked

- **Cost calibration smoke tests before committing to the design**: Running actual
  `claude -p` calls with Haiku/Sonnet/Opus exposed the cost structure (~20K tokens
  for system prompt alone, ~$0.01/turn Haiku, ~$0.05/turn Sonnet) AND revealed the
  fundamental design flaw (5 confounds) before any real experiment runs were executed.
  This saved the entire experiment from producing incomparable results.
- **TDD**: 32 harness tests + 8 model tests written before implementation. All GREEN
  on first implementation pass (after expected RED phase).
- **Models flexible enough to survive redesign**: `treatment_id: int | str` and
  `ExecutionMode` enum absorbed the Treatment 0 → 0a/0b split without model changes
  (only added `TeamSize.ONE_BY_EIGHT`).
- **Confounds audit**: Systematically checking every row in the key comparisons table
  against the treatment matrix caught 2 errors (2a vs 3, 2a vs 4) and found a missing
  clean comparison (1 vs 3 for decomposition).
- **Fractional factorial framing**: Naming the design limitation honestly ("no clean
  single-variable comparison for prompt or delegate") is better than claiming false
  cleanliness.

## Surprises

- **The biggest surprise was how wrong the original Treatment 0 design was**. Five
  confounds (execution mode, budget enforcement, model, tool access, human presence)
  between programmatic and interactive treatments. This wasn't a subtle issue — it
  would have made the primary comparison (Treatment 0 vs 1-5) scientifically meaningless.
  The fix was obvious once identified: make everything interactive.
- **Subagents are not a confound**: Initially worried about whether Claude would spawn
  subagents (Task tool) in interactive mode, making it "unfair" vs Agent Teams. The
  resolution: subagents are Claude's natural behavior — the experiment question is
  "does Agent Teams help vs using Claude normally?", not "does Agent Teams help vs
  subagents specifically."
- **`--allowedTools` flag doesn't work reliably**: Multiple formats tried (comma-separated,
  space-separated) in zsh — all failed with argument parsing errors. Workaround: bake
  bug report details into the prompt to eliminate WebFetch dependency. Moot now that
  Treatment 0 is interactive, but worth noting for any future `claude -p` usage.
- **Treatment 0 naturally splits into two variants**: User insight — 0a (single session,
  all bugs) represents one developer; 0b (8 sessions) represents 8 developers in swim
  lanes. Both are realistic usage patterns and 0b vs 5 becomes the cleanest possible
  comparison (zero confounds).

## Deviations from Plan

- **Major: Treatment 0 redesigned mid-phase**. Originally planned as programmatic
  `claude -p` with hard limits. Revised to interactive 0a/0b with soft budget. This
  was the right call — it eliminated all confounds and reduced cost from ~$25-40 API
  to $0 (subscription).
- **CLI commands added then removed**: `treatment0` and `treatment0-all` CLI commands
  were implemented, tested (2 tests), then removed when Treatment 0 went interactive.
  The underlying harness functions (`run_treatment0()`, etc.) were kept for exploratory
  use. Test count went 101 → 99.
- **Desiderata item #4 updated**: Originally said "Treatment 0 uses `-p` mode with
  hard limits for maximum reproducibility." This was an implementation detail, not a
  principle. Updated to "Pin model and Claude Code version across all treatments."
  The desiderata header says "Immutable principles... Frozen after Phase 0" — this
  revision is justified because the original wording encoded a specific implementation
  choice that proved wrong, not the underlying principle (reproducibility where possible).
- **experiment-design.md underwent 4 Change Log entries in one phase**: Treatment 0
  interactive split, Tier 3 autonomous assignment protocol, key comparisons audit.
  Normally the north star doc evolves slowly; this phase required rapid iteration.

## Implicit Assumptions Made Explicit

- **"Reproducibility" was valued over "comparability"**: The original design optimized
  Treatment 0 for reproducibility (hard limits, JSON output, deterministic command).
  But reproducible results that can't be compared to anything aren't useful. The
  revised design prioritizes comparability (same execution conditions for all treatments)
  over reproducibility (which is now equally imperfect across all treatments).
- **Fractional factorial trade-off**: With 5+ dimensions and 8 treatments, clean
  single-variable comparisons don't exist for all dimensions. Specifically, prompt
  specificity and delegate mode have no clean pairings. This was always true but
  never stated — the key comparisons table implied "None" confounds where two
  variables actually differed.
- **Communication guidance ≠ communication behavior**: Split into two dimensions
  (semi-controlled guidance vs observational behavior). Treatment 2a's "Encourage"
  is the instruction; what agents actually do is measured separately in Tier 4.
- **Bug ordering in prompts can prime connections**: For Treatment 0a, listing
  correlated bugs adjacent could bias Tier 3 correlation discovery. Specified
  portfolio order (not agent-pair order) to mitigate.

## Scope Changes for Next Phase

- Phase 3 (Scoring) is unaffected by the design revision — scoring rubrics and
  automation are the same regardless of how treatments were executed.
- The Tier 3 analysis protocol (flag structurally advantaged pairs) adds a small
  amount of post-hoc analysis work but no code changes.
- No programmatic Treatment 0 results to score — all results come from interactive
  sessions, scored uniformly.

## Metrics

| Metric | Value |
|--------|-------|
| Files created | 3 (harness.py, test_harness.py, test_cli_run.py) |
| Files modified | 9 |
| Lines added/removed | +1,443 / -89 |
| Unit tests | 99 (peak was 101 before CLI command removal) |
| Harness functions | 11 |
| experiment-design.md changes | 4 Change Log entries |
| Commits | 2 (harness + design revision, retros) |
| Design revisions | 1 major (Treatment 0 interactive) |
| Cost of design revision | $0.13 in smoke test API calls |
