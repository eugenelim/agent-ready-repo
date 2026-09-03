# Intent: what a loop does when it discovers the contract is wrong

- **Slug:** `agent-loop-escalation-recovery`
- **Type:** `research`
- **Raised:** 2026-09-02
- **Owner:** Repository maintainers (`ini-002`)
- **Stage:** Shaping — outcome not yet defined, competing hypotheses

## Why this exists, and what it is not

Better input reduces what a loop has to find; it does not make the contract
right. When a loop discovers mid-flight that the artifact above it is wrong, it
has to decide **which level to return to** — and today it has no procedure, so
it does the only thing it knows: repair in place, repeatedly.

Prevention is the sibling brief,
[`docs/product/briefs/agent-authoring-input-quality.md`](../briefs/agent-authoring-input-quality.md), and it is
designable now. This one is not: the response is competing hypotheses that need
spikes before any contract.

**This item is not blocked on that brief.** The relationship is shared evidence,
not sequencing — the activation analysis lives there, and two of the hypotheses
below read the same review artifacts. Both are on disk today, so the first spikes
here can run before anything ships there. An earlier workspace edge asserted a
dependency and made this item undispatchable; that was wrong and was removed.

**Where it may eventually touch the projection.** The reason someone first put
non-convergence inside the `next` brief is that `next` is what an agent asks each
turn, so it is the natural surface to *display* a stop. That remains true and is
recorded so it is not rediscovered: if a response adopted here needs an agent-
facing surface, `next` is the candidate carrier. It is a possible future consumer
relationship, not a dependency in either direction, and the projection's brief
keeps enforcement out of scope.

## Scope: any phase, any level

The discovery can surface at PLAN, EXECUTE, GATES, or REVIEW, and the decision is
the same shape wherever it does: **what did the discovery invalidate, and what is
the highest artifact it reaches?**

| Discovery reaches | Return to |
| --- | --- |
| A fixture, an assertion, a helper choice | the plan |
| A criterion's observable, or a criterion that cannot hold | the spec |
| The outcome, the appetite, or a slice boundary | the brief |
| Whether the outcome is the right one at all | the intent |

The observed case reached the spec's model — a claim about what the system
observes that was never checked — and the loop kept repairing criteria for ten
rounds because nothing routed it upward. A wrong fixture reaches only the plan
and should not trigger any of this.

Restricting the item to review rounds was considered and rejected: implementation
and gates can each discover the same class, and a procedure designed for one
phase would be re-derived for the others.

## The situation

A review-and-repair loop can run indefinitely without converging, and nothing
stops it. Observed directly: one spec-authoring loop ran **eleven** pre-EXECUTE
review rounds in a single run before a human intervened. It was abandoned and
re-planned from scratch.

The loop was not blind. The protocol wrote an artifact per round the whole time —
forty-two files under its own run directory, surviving a context compaction.
Nothing consulted them, and nothing stopped.
## The two halves are not equally hard

**Detecting non-convergence is close to free.** The signal already exists on
disk. Counting findings-bearing rounds is a few lines. Any of several detectors
would have fired well before round eleven.

**Deciding what to do about it is the actual problem, and it is unsolved.** The
evidence for that is this session: non-convergence was arguably visible by round
seven, when a reviewer reported the sustained count as "flat, not falling". Four
more rounds ran anyway. The response eventually taken — stop, abandon the
contract, re-author from a brief — was improvised under pressure, not selected
from anything. It may well have been right. Nobody knows, because there was
nothing to compare it against.

An agent that detects non-convergence and has no playbook will do what this one
did: keep repairing, because repairing is the only move it knows.
## Competing hypotheses

Each is a candidate response, with what this session's evidence says about it.
None is validated. Several are mutually compatible; some conflict.

| # | Hypothesis | Evidence for | Evidence against, or unknown |
| --- | --- | --- | --- |
| H1 | Stop after N findings-bearing rounds and hand to a human for replanning | Ends the loop; a human found the real defect in one pass once asked | N is unjustified. Replanning cost a full re-author. Would stopping at 3 have been better, or merely earlier? |
| H2 | The signal is finding **composition**, not count | Sustained counts were flat (17, 16, 22, 23, 20, 19, 19, 23, 21, 17, 18) while the class shifted decisively — table defects, then cross-document drift, then defects introduced by the previous repair. A class-recurrence detector would fire earlier than a count | Requires classifying findings, which is judgement. Might be unmechanizable |
| H3 | Bound the **repair**, not the round count | Measured: a 377-line repair was followed by 8 blockers; a 124-line repair by 6; a 204-line repair by 3. Large repairs on long contracts introduce defects at roughly the rate they remove them | n=4, single artifact, confounded with which round it was |
| H4 | Split the artifact once repairs stop being local | The contract was ~18,000 words across a spec and plan when repairs began reliably breaking distant clauses | No idea where the threshold is, or whether size is cause or correlate |
| H5 | Escalate the **review question** rather than the review round — classify the model as viable / blocked / unstable before permitting clause-level findings | The one round that ran this way produced 4 substantive findings against 14 cosmetic, and named the root premise | Tried once, at the very end, on an artifact already being abandoned. Untested as an early intervention |
| H6 | Require oracle acquisition before criteria are written — no criterion over an unverified claim about the world | The defect that ended the loop was exactly this: a claim about what the system observes, never checked | Cost unknown. May stall authoring on unknowns that do not matter |
## The activation requirement applies here too

Every hypothesis above is a rule, and this repository has shipped rules that did
not fire — see the prevention brief's activation section for the mechanism and the
evidence. Any hypothesis adopted here must come with an activation point, a way
to tell activation from presence, and a stated failure mode for when it does not
activate. A response nobody invokes is worse than none, because it makes the gap
look covered.

## What we would need to know

- Which detector fires earliest **without** false positives on loops that are
  converging slowly. A detector that stops healthy work is worse than none.
- Whether the right response is uniform, or depends on what kind of defect is
  recurring. H1 through H6 may be a routing table, not a contest.
- Whether any of this generalises past spec authoring. The same shape plausibly
  occurs in implementation review and in gate-repair loops, and a response
  designed for one may not fit the others.
- What it costs to be wrong in each direction: a loop stopped too early wastes a
  replan; a loop stopped too late wastes what this one wasted.
## Shape of the work

Spikes before any contract, cheapest first.

Two hypotheses are measurable without running a fresh loop end to end: the
finding-composition signal and the repair-size bound. Those go first, and they
draw on different sources, which matters for how durable each answer is.

The repair-size bound reads **git history** — commit sizes against the next
round's findings — so it is durable and can be measured any time. The
composition signal needs the per-round review artifacts, which are gitignored and
machine-local: they sit in peer worktrees and can be cleaned up, so a scavenged
answer is one-shot.

**Prefer a generated eval where one can carry the question.** The repository
ships an eval harness (`agentbundle pack evals run`, Tier-A `trigger_rate` from
authored `eval_queries.json`) and generated evals are reproducible where a
scavenged corpus is not. Whether these hypotheses are eval-shaped is itself part
of the first spike — the sibling brief's activation slice asks the same question
about a different subject and should be settled once, not twice. The
escalation-routing hypotheses need a live loop and are more expensive. The plain
round cap needs no spike at all — it needs a justified threshold, which the
others would supply.

Detection is small enough to ship independently of all of it, and probably
should: a loop that surfaces "this is round eight and the finding classes are
repeating" is useful even while the response is still a human's judgement.

## Not in scope here

- Authoring quality, the failure-point rubric, and the pre-creation pressure
  test. Those are the prevention brief's.
- Rewriting how reviewers work or how findings are adjudicated.
- Any cross-session or committed state. The observed failure was inside one run,
  and the signal that would have caught it was already on disk.
- The `next` action projection, which is a delivery brief:
  `docs/product/briefs/work-loop-next-action.md`.
