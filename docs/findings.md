# Findings: Agent Teams vs Single Agent for Bug Fixing

## Abstract

We designed an experiment to compare Claude Code's Agent Teams (multi-agent
coordination) against single-agent Claude Code for bug triage and fixing in
the Ruff/ty codebase. After executing 3 of 8 planned treatments on 8 Ruff
linter bugs (Round 1) and screening 6 ty type checker bugs (Round 2
candidates), we report three findings: (1) a pervasive ceiling effect where
Claude Opus 4.6 solves bugs rated "hard" by humans in under 15 minutes
regardless of treatment configuration, (2) zero inter-agent communication
across all team treatments despite explicit encouragement, and (3) a
structural argument that bug-fixing in single codebases is biased toward
single-agent approaches, making the paradigm outcome predictable a priori.
We conclude that the experiment's core question — "are there tasks where the
outcome of teams vs solo is genuinely uncertain a priori?" — has a negative
answer for this task domain.

---

## 1. Research Question

### Original Formulation

> Does Claude Code with Agent Teams (multi-agent coordination) produce
> qualitatively different outcomes than default Claude Code (single agent)
> on bug triage and fixing tasks?

The experiment was designed around 8 treatments varying 5 dimensions:
decomposition strategy (explicit vs autonomous), prompt specificity
(detailed vs vague), delegate mode (on vs off), team size (1×8, 4×2, 8×1),
and communication guidance (neutral, encourage, discourage). See
`docs/experiment-design.md` for the full treatment matrix.

### Refined Formulation

After Round 1 revealed a ceiling effect, the question evolved:

> Are there problems where, a priori, it is hard to know whether Agent Teams
> outperforms the single-agent paradigm?

This is a fundamentally different question. We are not asking "do teams ever
beat solo?" (trivially yes — parallelism provides speed). We are asking
whether there exists a class of tasks where the outcome is genuinely
uncertain before execution — where a reasonable person cannot predict which
paradigm will perform better.

---

## 2. Method

### 2.1 Codebase

**Ruff** (Round 1): Python linter/formatter written in Rust. Pinned to
v0.14.14 (`ff158d2`). Build: `cargo build`, test: `cargo nextest run`,
snapshots: `cargo insta accept`.

**ty** (Round 2 screening): Python type checker sharing Ruff's codebase.
Pinned to ruff/0.15.1+4 (`10c082f`). Same build/test infrastructure.

### 2.2 Treatments Executed

| ID | Label | Agent Teams | Team Structure | Communication |
|----|-------|-------------|----------------|---------------|
| 0b | Control: Swim Lanes | Off | 8 separate sessions | N/A |
| 2a | Autonomous + Encourage | On | 4 agents × 2 bugs | Encouraged |
| 5 | Max Parallelism | On | 8 agents × 1 bug | Neutral |

All treatments used Claude Opus 4.6 via Claude Code (subscription, $0 API
cost). Interactive format with standardized opening prompts.

### 2.3 Round 1 Bug Portfolio

8 bugs spanning 5 subsystems, rated Simple to Hard by human assessment:

| Bug | Subsystem | Human Rating | Category |
|-----|-----------|-------------|----------|
| #20945 | Semantic | Simple | FAST001 false positive |
| #18654 | Semantic | Medium | ARG001 @singledispatch |
| #7847 | Scope | Medium | B023 IIFE false positive |
| #4384 | Scope | Medium | C901 closure complexity |
| #19301 | Parser | Hard | Backslash continuation indent |
| #22528 | Parser | Hard | Match-like false syntax error |
| #22221 | Autofix | Medium | F401 infinite loop (__all__) |
| #22494 | Formatter | Medium | Range formatting semicolons |

### 2.4 ty Screening Portfolio

6 bugs spanning D1–D5 on a decomposability spectrum:

| Bug | D-Level | Category |
|-----|---------|----------|
| #2644 | D1 | getattr narrowing |
| #2480 | D2 | NoReturn at module scope |
| #2732 | D2 | bool\|None narrowing after == |
| #2731 | D3–D4 | Nonlocal writes ignored |
| #2808 | D4 | Infinite loop in fixpoint |
| #2799 | D5 | Constraint solver variance |

Screening protocol: Treatment 0b style (single Claude session, single bug,
interactive), 30-minute hard time limit.

### 2.5 Measurement Framework

5-tier system (designed for full experiment, partially exercised):

- **Tier 1** (Objective): Patch applies, tests pass, repro fixed, no
  regressions. Automated.
- **Tier 2** (Diagnostic): Localization, root cause, fix direction,
  confidence calibration. Human-scored rubric (0–8 per bug).
- **Tier 3** (Correlation): Cross-bug connection discovery. Not exercised
  (requires multiple treatments on same bugs).
- **Tier 4** (Communication): Message count, directionality, taxonomy.
  Exercised — yielded the zero-communication finding.
- **Tier 5** (Process): Files explored, dead ends, time to first insight.
  Partially exercised.

### 2.6 Communication Verification Protocol

Only `SendMessage(recipient=<peer-agent>)` calls with system routing
metadata count as inter-agent communication. Agent-written log entries
("I shared my findings with the team") are NOT evidence — they are
hallucinated narration. This protocol was established in Phase 1 and
validated against all Round 1 transcripts.

---

## 3. Results

### 3.1 Round 1: Ceiling Effect

All 3 treatments achieved 8/8 fix rate. Every bug was solved correctly.

| Treatment | Wall Clock (total) | Mean per Bug | Fix Rate |
|-----------|-------------------|--------------|----------|
| 0b (solo, sequential) | 49 min | 6.1 min | 8/8 |
| 2a (4×2 team) | 16 min | N/A (parallel) | 8/8 |
| 5 (8×1 max parallel) | 9.5 min | N/A (parallel) | 8/8 |

**Per-bug timing (Treatment 0b, the solo baseline):**

| Bug | Time | Human Rating |
|-----|------|-------------|
| #7847 | 2.3 min | Medium |
| #22528 | 4.0 min | Hard |
| #19301 | 4.2 min | Hard |
| #18654 | 6.2 min | Medium |
| #22221 | 6.2 min | Medium |
| #4384 | 6.7 min | Medium |
| #22494 | 9.4 min | Medium |
| #20945 | 10.2 min | Simple |

Notable: The two bugs rated "Hard" by humans (#22528 parser, #19301 parser)
were solved in 4.0 and 4.2 minutes — faster than the "Simple" bug (#20945,
10.2 min). Human difficulty ratings do not predict model difficulty.

**Quality**: 4 of 8 fixes were submitted as PRs to astral-sh/ruff (#23294,
#23296, #23297, #23299). All applied cleanly against latest main despite
being written against v0.14.14. Two have been merged.

### 3.2 Round 1: Zero Communication

Both Agent Teams treatments produced zero peer-to-peer messages:

**Treatment 2a** (4 agents, encouraged communication):
- 17 total SendMessage calls
- 4 lead → agent (shutdown commands)
- 9 agent → lead (status reports)
- 4 shutdown acknowledgments
- **0 peer-to-peer**

**Treatment 5** (8 agents, neutral communication):
- 24 total SendMessage calls
- 8 lead → agent (shutdown commands)
- 8 agent → lead (status reports)
- 8 shutdown acknowledgments
- **0 peer-to-peer**

The explicit instruction "You are encouraged to share findings with
teammates!" (Treatment 2a) had no observable effect on communication
behavior. Agents solved bugs independently and reported completion to the
lead. No agent ever asked a peer for help, shared a partial finding, or
coordinated an investigation strategy.

### 3.3 Round 1: Agent Teams as Parallelism Engine

Without communication, Agent Teams functioned as a pure parallelism
multiplier:

| Treatment | Structure | Total Time | Speedup vs 0b |
|-----------|-----------|-----------|----------------|
| 0b | 1 agent, sequential | 49 min | 1.0× |
| 2a | 4 agents × 2 bugs | 16 min | 3.1× |
| 5 | 8 agents × 1 bug | 9.5 min | 5.2× |

Treatment 2a was slower than the theoretical 4× because the bottleneck was
the slowest agent pair (parser-agent: 524s for #22528). Treatment 5
achieved 5.2× because all 8 agents ran in parallel with no coordination
overhead.

### 3.4 ty Screening: Ceiling Persists

| Bug | D-Level | Time | Fix Produced | Fix Correct | Verdict |
|-----|---------|------|-------------|-------------|---------|
| #2644 | D1 | 10 min | Yes (65 lines, 2 files) | Yes | DROP |
| #2480 | D2 | 7 min | Yes (42 lines, 2 files) | Yes | DROP |
| #2732 | D2 | 8 min | Yes (25 lines, 1 file) | Yes | DROP |
| #2731 | D3–D4 | 15 min | Yes (148 lines, 4 files) | Partial | MAYBE |
| #2808 | D4 | 30 min | No (diagnosis only) | N/A | KEEP |
| #2799 | D5 | 12 min | Yes (82 lines, 1 file) | Yes | DROP |

**Summary**: 5 of 6 bugs solved in under 15 minutes. Only bug #2808
(infinite loop in fixpoint iteration) hit the 30-minute limit without
producing a fix — though the agent correctly diagnosed the root cause
(unbounded type growth when `Divergent` normalizes to `Unknown`).

Bug #2799 (D5, constraint solver variance) was rated the hardest by human
assessment. The agent produced a genuine variance-aware fix with lower/upper
bound tracking and a 4-case combining matrix in 12 minutes.

**Decision criteria outcome**: The screening runbook specified "0–1 bugs
take 30+ min → ty also has ceiling effect. Abort." With exactly 1 bug at
the limit, we hit the abort threshold.

---

## 4. Analysis

### 4.1 Why the Ceiling Effect?

The ceiling effect is not an artifact of easy bug selection. We specifically
chose bugs rated "Hard" by human maintainers and screened ty bugs up to D5
difficulty. The ceiling persists because:

1. **Search is trivially fast.** Claude Code's Grep/Glob/Read tools make
   file-space exploration near-instantaneous. The "find the right file"
   phase that would take a human 30+ minutes takes the model seconds.

2. **Pattern matching is the model's strength.** Most bug fixes follow a
   pattern: locate the relevant code, understand the logic error, apply
   a targeted fix. This is exactly what large language models excel at.

3. **Codebase familiarity compounds.** The model has seen Rust patterns,
   type checker architectures, and linter implementations in its training
   data. It doesn't start from zero the way a human contributor would.

4. **Human difficulty ≠ model difficulty.** Humans find parser bugs "hard"
   because they require understanding grammar specifications and edge
   cases. The model can pattern-match against the existing codebase's
   handling of similar constructs. Conversely, the "Simple" bug #20945
   took the longest (10.2 min) because it required understanding a
   specific rule's semantics that wasn't pattern-matchable.

### 4.2 Why Zero Communication?

Agents don't communicate because they have no incentive to. Communication
is a means to an end (getting help, sharing information needed by others).
When every agent can solve its assigned bug independently in minutes, the
expected value of communicating is zero:

- **No agent gets stuck.** Communication emerges from being stuck. If the
  bug is solvable in 5 minutes, there's no window where an agent would
  think "I should ask for help."

- **No information is needed from peers.** Each bug is self-contained
  within the codebase. An agent fixing a parser bug gains nothing from
  knowing that another agent fixed a semantic analysis bug.

- **Communication has overhead.** Composing and sending a message takes
  tool calls that could be spent on the actual fix. On easy bugs, the
  rational strategy is to just solve it.

This suggests communication would emerge only on tasks where: (a) agents
get stuck for extended periods, AND (b) peers have information that could
help. Neither condition was met.

### 4.3 Structural Bias of Bug-Fixing

Bug-fixing in a single codebase is structurally biased toward single-agent
approaches. The argument:

**The two paradigms differ only mechanistically.** Given zero communication,
the comparison is:
- **Solo**: 1 agent with full sequential context and concentrated effort
- **Teams**: N independent agents, each exploring separately

**This reduces to a simple model.** Teams = N independent draws from the
same success distribution. If P(single agent solves in time T) = p, then
P(any team member solves) = 1 - (1-p)^N. Teams always have P ≥ p.

**But the advantage is predictable.** The team advantage depends entirely
on p (the single-agent success probability):
- p ≈ 1 (easy bugs): Both succeed. No difference. This is Round 1.
- p ≈ 0 (impossible bugs): Both fail. No difference. This is bug #2808.
- 0 < p < 1: Teams have a mathematical advantage (more lottery tickets).
  But this advantage is **predictable from p** — it's not uncertain.

**The only source of genuine uncertainty** would be tasks where p itself is
uncertain — where you can't estimate the single-agent success probability
from the task description. For bug-fixing, p is usually estimable:
- Small, localized bugs → p ≈ 1
- Deep architectural issues → p depends on reasoning depth → solo favored
- Bugs requiring broad exploration of solution space → p benefits from
  multiple attempts → teams favored

In practice, most bugs fall cleanly into one of these categories. The
"genuinely uncertain" middle ground — where you can't tell whether the task
is exploration-bound or reasoning-bound — appears to be narrow or empty for
bug-fixing tasks.

### 4.4 The Decomposability Dimension

The experiment was designed around a decomposability spectrum (D1–D5),
hypothesizing that less decomposable tasks would favor solo while more
decomposable tasks would favor teams. The ty screening tested this:

| D-Level | Bugs | Mean Time | Ceiling? |
|---------|------|-----------|----------|
| D1 | 1 | 10 min | Yes |
| D2 | 2 | 7.5 min | Yes |
| D3–D4 | 2 | 22.5 min | Mostly (1 KEEP, 1 MAYBE) |
| D5 | 1 | 12 min | Yes |

The decomposability spectrum did not predict difficulty for the model.
The D5 bug (hardest by human assessment) was solved faster than D3–D4 bugs.
This further supports the finding that human difficulty ratings are poor
proxies for model difficulty.

---

## 5. Conclusions

### 5.1 Answer to the Core Question

> Are there problems where, a priori, it is hard to know whether Agent Teams
> outperforms the single-agent paradigm?

**For bug-fixing tasks in single codebases: No.**

The outcome is predictable: Agent Teams provides a speed multiplier
proportional to team size (empirically 3–5×) with no quality improvement.
This holds across both "easy" bugs (Round 1) and bugs spanning the full
D1–D5 difficulty spectrum (ty screening). The mechanism is transparent:
without communication, teams are parallel independent solvers. The paradigm
choice reduces to "do you want speed or do you want to conserve resources?"
— a question with an obvious, context-dependent answer.

### 5.2 Secondary Findings

1. **Human difficulty ratings are poor proxies for model difficulty.**
   Bugs rated "Hard" by maintainers were solved in 4 minutes. A "Simple"
   bug took 10 minutes. A D5 bug took 12 minutes while a D4 took 30.

2. **Communication is a luxury good.** It emerges only when agents are
   stuck and peers have useful information. On solvable tasks, the rational
   strategy is to skip communication entirely.

3. **Agent Teams is a parallelism engine, not a collaboration engine.**
   In its current implementation, it provides embarrassingly parallel
   execution without coordination overhead. This is useful (5× speedup)
   but predictable.

4. **The ceiling effect is robust.** It survives across two subsystems
   (Ruff linter, ty type checker), two programming domains (linting rules,
   type inference), and five difficulty levels. Claude Opus 4.6 treats
   most single-codebase bugs as straightforward.

### 5.3 What Would Change This Answer?

The answer could become "yes" (genuinely uncertain a priori) under
conditions that differ from our experimental setup:

- **Tasks requiring genuine exploration**, where the solution space is
  broad and multiple viable approaches exist (not just "find the bug, fix
  the bug").
- **Tasks spanning multiple codebases or systems**, where no single agent
  can hold the full context.
- **Agent Teams implementations that produce communication**, enabling
  actual collaboration rather than parallel independence.
- **Tasks where the model is near its capability boundary**, producing
  variable success rates (0 < p < 1) where the lottery-ticket effect of
  teams becomes material.

---

## 6. Implications

### For Practitioners

- **Use Agent Teams for speed, not quality.** On tasks within the model's
  capability, teams provide wall-clock speedup proportional to team size
  with no quality penalty. Use it when time-to-completion matters.
- **Don't expect emergent collaboration.** Agents will not spontaneously
  coordinate, share findings, or help each other. Design workflows
  accordingly.
- **Don't trust human difficulty ratings for model task assignment.**
  What's hard for humans (parser edge cases, grammar specifications) may
  be easy for models, and vice versa.

### For Future Research

- **The interesting question is about task domains, not bug difficulty.**
  Scaling to harder bugs within the same domain (bug-fixing) doesn't
  change the structural dynamics. A different task domain — feature
  implementation, multi-repo integration, system design — might.
- **Communication is the key variable.** The current experiment couldn't
  distinguish "teams don't help" from "teams without communication don't
  help." Inducing or enabling genuine inter-agent communication would
  test a different and more interesting hypothesis.
- **Model capability boundaries need mapping.** The ceiling effect means
  we never operated in the regime where paradigm choice matters (0 < p < 1).
  Finding that regime requires systematic capability evaluation, not just
  harder bugs.

---

## 7. Data Summary

### Round 1 (Ruff v0.14.14, 3 treatments × 8 bugs)

**Treatments executed**: 0b, 2a, 5
**Treatments not executed**: 0a, 1, 2b, 3, 4
**Fix rate**: 24/24 (100%)
**Peer-to-peer messages**: 0/41 total messages
**PRs submitted**: 4 (#23294, #23296, #23297, #23299)
**PRs merged**: 2

| Metric | Treatment 0b | Treatment 2a | Treatment 5 |
|--------|-------------|-------------|-------------|
| Total time | 49 min | 16 min | 9.5 min |
| Speedup | 1.0× | 3.1× | 5.2× |
| Fix rate | 8/8 | 8/8 | 8/8 |
| Peer messages | N/A | 0 | 0 |
| Agent Teams | Off | On (4×2) | On (8×1) |
| Communication | N/A | Encouraged | Neutral |

### ty Screening (ruff/0.15.1+4, Treatment 0b style × 6 bugs)

**Bugs screened**: 6 (D1–D5)
**Fixes produced**: 5/6
**30-minute limit reached**: 1/6 (#2808)
**Decision**: Ceiling effect confirmed. Abort threshold met.

### Tooling

- **Model**: Claude Opus 4.6
- **Claude Code version**: 2.1.47 (screening), version noted per session
- **Cost**: $0 (Claude Pro subscription)
- **Infrastructure**: macOS, local Ruff/ty builds via cargo

---

## Appendix A: Patch Quality Examples

### Bug #2799 (D5, constraint solver variance) — Solved in 12 min

The agent produced an 82-line patch adding variance-aware constraint
combination to the generics subsystem. The fix introduced a `has_lower_bound`
tracker and a 4-case combining matrix (both upper, both lower, mixed upper/
lower, mixed lower/upper). This is a genuine algorithmic contribution, not
a superficial workaround.

### Bug #2731 (D3–D4, nonlocal writes) — Solved in 15 min (partial)

The agent added an `IS_NONLOCAL_CAPTURED` flag to the symbol table and
widened captured variables with `Unknown`. This is a pragmatic workaround
that matches the maintainers' own TODO comments in the codebase. It does
not solve the hard problem of precise cross-closure mutation tracking, but
it eliminates false negatives (unreachable code warnings after `nonlocal`
writes).

### Bug #2808 (D4, infinite loop) — Not solved in 30 min

The agent correctly diagnosed the root cause: unbounded type growth in
fixpoint iteration when `Divergent` normalizes to `Unknown`, creating ever-
larger union types. It spent 12 of 30 minutes on rebuild cycles (Rust
compilation). The 55-line patch was debug instrumentation only (`eprintln!`),
not a fix. This was the only bug where the model hit its capability boundary.

---

## Appendix B: Communication Transcript Evidence

### Treatment 2a — All 17 SendMessage Calls

```
lead → semantic-agent:  "shutdown" (×2)
lead → parser-agent:    "shutdown" (×1)
lead → format-agent:    "shutdown" (×1)
semantic-agent → lead:  "status: complete" (×3)
parser-agent → lead:    "status: complete" (×2)
scope-agent → lead:     "status: complete" (×2)
format-agent → lead:    "status: complete" (×2)
shutdown acks:          (×4)
peer-to-peer:           0
```

### Treatment 5 — All 24 SendMessage Calls

```
lead → agent-N:         "shutdown" (×8)
agent-N → lead:         "status: complete" (×8)
shutdown acks:          (×8)
peer-to-peer:           0
```

Every message was either a shutdown command (lead → agent), a completion
report (agent → lead), or a shutdown acknowledgment. No agent ever initiated
contact with a peer.
