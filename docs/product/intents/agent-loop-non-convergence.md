# Intent: how an agent loop responds when it stops converging

- **Slug:** `agent-loop-non-convergence`
- **Raised:** 2026-09-02
- **Owner:** Repository maintainers (`ini-002`)
- **Stage:** Shaping — outcome not yet defined

## Why this is separate

This began as half of the `work-loop-next-action` delivery brief and does not
belong there. That brief has a defined outcome and two prior implementation
attempts. This does not have a defined outcome at all, and bundling them repeats
the failure that produced both: two problems in one artifact, where the tractable
half waits on the open one.

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

## The activation problem underneath all of them

Every hypothesis above proposes a rule. This repository has already shipped two
rules that should have prevented what happened, and neither fired. That is a
prior question, and it changes what any response has to include.

**The two instances, both in one session, with the authoring agent as subject.**

- The cognitive-load simplification and the cut-before-adding razor are both
  present, both routed from the root context, and both were in the agent's
  loaded context the whole time. The artifacts it then authored were long and
  dense with precise claims — the opposite of what the rules ask.
- The spec-authoring guidance already said a criterion names an observable
  outcome and that naming a helper or a call sequence means the content belongs
  in the plan. The agent read that rule, cited it to reviewers as governing
  authority, and still put mechanism into criteria repeatedly.

**Presence is not activation, and neither is enforcement — if the enforcement is
scoped elsewhere.** The cognitive-load rules are not prose-only; several gates
enforce them. But those gates read the packs, the root guidance, the seeds, and
the changelog. The progressive-disclosure lint goes further and has a case
asserting that an authored `docs/specs/<feature>/spec.md` is *not* in its
results. Authored work-loop artifacts are outside the enforcement boundary by
design.

So the rule is loaded at every turn and enforced nowhere near the moment it
would bind. An agent authoring a spec is holding the guidance in context and
receiving no signal from it.

**What this means for the work.** A response to non-convergence that is another
rule, shipped the same way, has no reason to behave differently. Any hypothesis
above must come with:

- **An activation point** — the moment in the loop where the rule is consulted
  and something changes as a result, not merely the file where it is written.
- **A measurement** — a way to tell activation from presence. The distinction is
  observable: compare what the rule asks for against what the agent produced,
  on artifacts the agent authored, not on the surfaces the rule was originally
  written to govern.
- **A failure mode when it does not activate.** A rule that silently does
  nothing is worse than an absent one, because it makes the gap look covered.

The cheapest available measurement is retrospective and needs no new mechanism:
the repository holds authored specs, plans, and briefs from many loops. Scoring
those against the guidance that was in force when each was written would say how
often these rules activate at all, and whether the two instances above are
typical or unlucky. That measurement should precede any new rule.

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

**Order matters: measure activation first.** Every hypothesis is a rule, and this
repository has evidence that rules of this kind do not fire. Scoring already-authored
specs and briefs against the guidance in force when they were written costs one
retrospective pass and decides whether the rest of this item is worth doing as
rules at all, or whether the response has to be a mechanism in the loop rather
than a statement in a document.

Then spikes before any contract. H3 and H2 are measurable against review artifacts
that already exist in this repository — several loops have run and left their
rounds on disk, so the detectors can be evaluated retrospectively rather than by
running fresh loops. H5 and H6 need a live loop to test and are more expensive.
H1 is the fallback and needs no spike; it needs a justified N, which the others
would supply.

Detection is small enough to ship independently and probably should, because a
loop that surfaces "this is round eight and the finding classes are repeating"
is useful even when the response is still a human's judgement call.

## Not in scope here

- The `next` action projection. Separate delivery brief,
  `docs/product/briefs/work-loop-next-action.md`.
- Rewriting the cognitive-load or cut-before-adding rules themselves. The
  question here is why they do not activate, not whether they are well written.
- Changing what reviewers do or how findings are adjudicated.
- Any cross-session or committed state. The observed failure was inside one run,
  and the signal that would have caught it was already on disk.
