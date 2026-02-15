# Round 1 Retrospective

## Summary

Round 1 executed 3 of 8 treatments (0b, 2a, 5) on all 8 primary bugs. All three
treatments achieved 8/8 bug fixes, confirming a **ceiling effect** that prevents
quality differentiation on these bugs. The experiment is pivoting to a hybrid
design: Round 1 data is preserved (speed/cost metrics remain valuable), and
Round 2 will use harder bugs where treatments may actually diverge.

## Treatments Executed

| Treatment | Structure | Wall Clock | Bugs Fixed | Communication |
|-----------|-----------|------------|------------|---------------|
| 0b (Swim Lanes) | 8 sessions × 1 bug | ~49 min (sequential) | 8/8 | N/A (no teams) |
| 5 (Max Parallelism) | 1 session, 8 agents × 1 bug | ~9.5 min | 8/8 | Zero peer msgs |
| 2a (Autonomous + Encourage) | 1 session, 4 agents × 2 bugs | ~20 min | 8/8 | Zero peer msgs |

## Key Findings

### 1. Ceiling Effect (Critical)

Every bug was solved correctly in under 10 minutes per bug, including the two
"hard" parser bugs (#19301, #22528). Claude Opus 4.6 treats these bugs as
straightforward — no treatment struggled with any of them.

**Implication**: Tier 1 scores (patch applies, tests pass, repro fixed) are
uniformly 8/8 across all treatments. Tier 2 rubric scores will likely be
uniformly high as well. The bugs do not discriminate between treatment
configurations.

### 2. Zero Inter-Agent Communication

Both Agent Teams treatments (2a and 5) showed **zero peer-to-peer SendMessage
calls**. Verification used the correct protocol established in Phase 1:

- `SendMessage` with routing metadata is the unforgeable proof of communication
- Agent-written log files are NOT evidence (can be fabricated)
- Only `SendMessage(recipient=<peer-agent>)` counts as inter-agent communication
- `SendMessage(recipient="team-lead")` is status reporting, not collaboration

**Treatment 5** (communication NOT encouraged): 24 total SendMessage calls —
8 lead→agent shutdowns, 8 agent→lead status reports, 8 shutdown acks. Zero
peer-to-peer.

**Treatment 2a** (communication ENCOURAGED): 17 total SendMessage calls —
4 lead→agent shutdowns, 9 agent→lead status reports, 4 shutdown acks. Zero
peer-to-peer. The explicit "COLLABORATION: You are encouraged to share findings
with teammates!" instruction in every agent's prompt had **no observable effect**
on communication behavior.

**Root cause hypothesis**: When bugs are easy enough to solve independently,
agents have no incentive to communicate. Communication may only emerge when an
agent gets stuck and needs help — which never happened in Round 1.

### 3. Agent Teams = Parallelism Engine, Not Collaboration Engine

On these bugs, Agent Teams provides a pure speed multiplier:
- 0b: 49 min (sequential baseline)
- 2a: 20 min (4× parallelism with sequential pairs)
- 5: 9.5 min (8× parallelism)

The "team" is functionally a task queue with fan-out/fan-in coordination.
No emergent collaboration, knowledge sharing, or mutual assistance was observed.

### 4. 4×2 Structure Is Slower Than 8×1

Treatment 2a (4 agents × 2 bugs) took ~20 min vs Treatment 5's ~9.5 min.
Having each agent handle 2 bugs sequentially means the slowest agent
(parser-agent at 16 min for 2 parser bugs) bottlenecks the entire run.
Treatment 5's 8×1 structure avoids this bottleneck.

### 5. Category Clustering Didn't Produce Communication

Treatment 2a's lead grouped bugs by domain (semantic, scope, parser, format),
hoping agents would "leverage shared expertise." They didn't — each agent
treated its bugs independently. The clustering created a structural advantage
for Tier 3 (correlation discovery) but did not produce the hypothesized
collaboration benefit.

### 6. Lead Coordination Is Pure Hub-and-Spoke

In both team treatments, the lead:
1. Created tasks upfront with detailed descriptions
2. Spawned all agents simultaneously
3. Passively monitored via TaskList
4. Sent shutdown requests when agents completed
5. Never redistributed work, facilitated communication, or provided feedback

The lead's role was purely administrative — task creation and lifecycle
management. No coaching, synthesis, or coordination beyond initial assignment.

## PR Submissions

4 of 8 bug fixes were submitted as PRs to astral-sh/ruff:

| Bug | PR | Status |
|-----|-----|--------|
| #7847 (B023 IIFE) | [#23294](https://github.com/astral-sh/ruff/pull/23294) | Submitted |
| #22494 (formatter) | [#23296](https://github.com/astral-sh/ruff/pull/23296) | Submitted |
| #22528 (parser match) | [#23297](https://github.com/astral-sh/ruff/pull/23297) | Submitted |
| #19301 (parser indent) | [#23299](https://github.com/astral-sh/ruff/pull/23299) | Submitted |

The other 4 bugs were either already closed (#20945, #22221) or have design
blockers (#18654 needs-design, #4384 needs-decision).

All 4 patches applied cleanly against latest Ruff main despite being written
against v0.14.14 (~361 commits behind).

## Decision: Hybrid Rounds (Option E)

### What we keep from Round 1
- All transcript data (0b, 2a, 5) — valuable for speed/cost analysis
- Patches and metadata — useful as PR contributions
- Communication analysis — important negative result
- Tier 4 baseline — what "no communication" looks like on easy bugs

### What Round 2 changes
- **Harder bugs**: Target bugs where Claude struggles or takes 30+ min
- **Bug categories**: red-knot type checker, LSP server, multi-rule autofix
  conflicts, configuration edge cases, cross-crate refactors
- **Screening protocol**: Test 15-20 candidates, keep ~8 where Claude fails
  or takes significantly longer
- **Same treatments**: Re-run the same 8 treatments for clean comparison
- **Stay with Ruff**: Same codebase, harder subsystems

### Why not just pick harder bugs from the start?
We couldn't know the bugs were too easy without running the experiment. The
Phase 1 complexity ratings (simple/medium/hard) were based on human assessment,
not Claude's actual performance. Round 1 empirically calibrated the difficulty
scale.

## Methodology Notes

### Timing estimates for Treatment 2a
Per-bug wall clock times within each agent pair are estimated. We have precise
timestamps for agent completion (all bugs done) but not for the boundary between
first and second bug within each pair. Agent-level completion timestamps are
precise.

### SendMessage verification protocol
Established in Phase 1 smoke test (docs/phases/phase-1-plan.md lines 59-103):
- System-generated routing metadata is the ground truth
- Agent-written logs are NOT evidence
- `SendMessage(recipient=<peer>)` = inter-agent communication
- `SendMessage(recipient="team-lead")` = status reporting
- Subagents (Task tool) have NO SendMessage primitive
