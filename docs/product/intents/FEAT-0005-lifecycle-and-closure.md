# Lifecycle and closure

- **Slug:** `lifecycle-and-closure` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:repository-work-graph

## Outcome

- **Steerable input:** The share of intents whose recorded status matches their real state, and the number of terminal transitions a person can make through a workflow rather than by editing a field.
- **Lagging outcome:** An intent whose work is delivered, abandoned or superseded carries a terminal status set through a workflow, so the graph distinguishes live bets from finished ones without a reader inspecting each artifact's descendants.
- **Guardrail:** A status is never set by a count. Closure is decided by a human on presented evidence, and a terminal transition passes whatever review gate governs it. A closed intent's record is retained or disposed of under the existing disposition contract rather than a second one invented here.

## Opportunity

- **Functional job:** Close an intent when its work is done, and have the graph show that.
- **Emotional job:** Trust that a list of open intents is a list of live bets rather than an archive nobody dares prune.
- **Social job:** Show a portfolio that distinguishes what is being pursued from what has been achieved.
- **Struggling moment:** An intent can be opened and ratified but never closed. `work-loop` sets a spec to `Shipped` and `close-work` recommends `Shipped`, `Withdrawn` or `Cancelled` for a delivery brief — but `Fulfilled` appears in **no skill in the repository**, and no workflow can mark an intent closed. The consequence is visible: nearly every intent on disk is `Draft`, including strategies whose delivery has substantially shipped.

## Boundary

Inherits the parent's outcome, boundary, and exclusions. Within them, this child owns:

- what each `Status` value means for an intent **and for a brief**, which transitions between them are legal, and which are terminal;
- the **cut-closed declaration** on a brief: the state that says no further slices are expected, without which mapped-specs-shipped cannot close it;
- which workflow may make each transition. **Owner decision 2026-09-18: `Fulfilled` is a supported status going forward and is set in the `close-work` flow**, alongside the brief terminal transitions that flow already owns;
- how a terminal transition is gated. `Accepted` has a documented independent shaping-review gate; `Fulfilled` currently has none, and whether it takes the same gate is this child's to settle;
- how the eligibility signal is presented for a human decision, and what evidence accompanies it.

It does not own computing that eligibility — the fulfilment rollup is the parent capability's, delivered jointly by [Intent graph navigation](FEAT-0002-intent-graph-navigation.md) and [Intent-to-delivery traceability](FEAT-0003-intent-delivery-traceability.md). It does not own identity, placement or admission, which are [Intent identity and registration](FEAT-0001-intent-identity-and-registration.md)'s: that child owns entry, this one owns exit. It does not own retention or disposal of a closed record, which is `close-work`'s existing disposition contract.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Unresolved questions

- Whether fulfilment is decidable by a lint over the graph rather than by review. The load-bearing bet of this child.
- Whether a closure-time staleness refresh stays affordable as the corpus grows.
- Whether the existing disposition contract covers a closed intent's record without extension.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## What gates a closure today

Measured 2026-09-18. The criterion is consistent across levels; the review is not, and the asymmetry runs the wrong way.

| Level | Criterion for terminal | Review at the moment of closure |
| --- | --- | --- |
| Spec → `Shipped` | acceptance criteria met and tasks complete | **Full reviewer roster** — every warranted mandatory reviewer clean, no unresolved Blocker or Concern, deferred Nits carrying citations |
| Brief → `Shipped` | non-empty materialized Spec map fully Shipped | **None.** `close-work` dispatches no reviewer at all; the gate is the criterion plus an explicit human confirmation |
| Intent → `Accepted` | contract is well-formed | **Independent shaping review** in intent mode, zero `MALFORMED` tokens, plus human confirmation |
| Intent → `Fulfilled` | all children terminal | **Does not exist** |

Two things follow, and the second reverses the obvious reading of the first.

The heaviest review sits at the **bottom** rung and the middle rung has none, so a brief's exit gate is lighter than an intent's *entry* gate. That looks like an accident of build order. It is not.

### Fulfilment is mechanically verifiable, and that is the point

The three closures are not the same kind of claim, and only one of them is a judgement about the artifact in front of you.

- A **spec** closing asserts the work is *correct*. Correctness is a judgement, so it takes reviewers.
- A **brief** closing asserts the *outcome is complete*. A fully-Shipped Spec map does not establish that, because a brief may need a slice that was never materialized — so a human confirms what the map cannot.
- An **intent** closing asserts *every child reached a terminal state*. That is not a judgement. It is a property of the graph, and a lint can decide it.

The reason an intent differs is that **its judgement was already paid, once, at `Accepted`.** The shaping review's fifth condition requires that the decomposition partitions the artifact's own outcome with no overlap and no gap. If that held at acceptance, then "every child is terminal" mechanically entails "the outcome is delivered" — there is no residue for a human to weigh, because the absence of a gap was established when the partition was ratified.

So the asymmetry is coherent design rather than accident: pay the judgement cost once where the partition is decided, and closure is computable from then on. The gate that is expensive to pass is what makes every later closure cheap.

**Consequence for this child:** `Fulfilled` needs no reviewer and no per-instance human confirmation. It needs a lint over the graph. What it does need is the conditions under which that lint is *entitled* to decide, which is this child's real work.

### The same rule applies to a brief, and one missing field is what blocks it

A brief's closure is the identical shape: its judgement is paid at the **slice confirmation**, where a second, distinct human confirmation ratifies the cut. Once that cut is ratified, "every mapped spec is Shipped" should be as decisive as "every child is terminal" is for an intent.

It is not decisive today, for one precise reason. A brief "remains Executing when every currently materialized child is Shipped but another slice has not yet been materialized" — and **no brief carries any state expressing that no further slices are coming.** So the human confirmation demanded at brief closure exists solely to answer a question the artifact cannot state, which is why it reads as judgement when it is really a missing field.

The remedy is the same as the intent's: make the ratified decomposition explicit. A brief declares its **cut closed**, and from that point "all mapped specs Shipped" closes it mechanically. Until it does, closure correctly refuses, because an open cut genuinely means the outcome may not be delivered.

This is why this child covers both artifact kinds rather than intents alone: it is one rule — *closure is mechanical once the decomposition it depends on has been ratified* — and two places where the ratification currently fails to leave a mark a lint can read.

### The ratification this depends on is not currently reliable

The argument above rests on the partition being ratified once at `Accepted`. Measured 2026-09-19, that ratification is **not stable**. Across two intents taken through the intent-mode shaping review, conditions 1, 2, 3, 4 and 6 returned consistent, actionable results every time, while condition 5 — *the decomposition partitions the outcome with no overlap and no gap* — returned opposite verdicts on byte-identical content in substantive runs, twice.

The cause is visible in the reviewer's own contract, which describes the mode as "nearly mechanical: six conditions, each decidable by reading the packet." Five are presence checks. Condition 5 asks for a judgement about coverage, and it behaves like one.

This is a precondition defect rather than a detail. A mechanical fulfilment verdict inherits whatever confidence the partition ratification had; if that ratification is a coin flip, the lint is deciding on a foundation nobody verified. Settling it is this child's work and it has two plausible shapes — make condition 5 decidable by giving a decomposition an explicit completeness statement a reader can check, or move partition coverage out of the well-formedness review into a separate verification with its own evidence, in the way fulfilment itself was separated from shape review.

### What "if we do it right" requires

A mechanical verdict is only as good as the graph it reads, and four preconditions must hold before a lint may assert fulfilment. Each is owned elsewhere and each is currently unmet:

- **The decomposition was ratified** — an intent's partition at `Accepted`, a brief's cut at slice confirmation. Only an intent that passed the `Accepted` gate has a decomposition anyone verified. An intent that reached terminal children without ever being accepted has no guarantee its children covered its outcome, and the lint must refuse rather than infer. Today nine intents are `Accepted` out of 143.
- **Every child is recorded as a child.** A missing edge makes an incomplete tree look complete — the lint's most dangerous failure, because it is silent. 9 of 140 intents record a parent.
- **`Level` and `Status` carry closed vocabularies.** A lint cannot evaluate "terminal" against an unenforced value set. Owned by [Intent identity and registration](FEAT-0001-intent-identity-and-registration.md).
- **Specs carry their up-edge.** Without it the walk has no first step. 84% of specs carry none, owned by [Intent-to-delivery traceability](FEAT-0003-intent-delivery-traceability.md).

Until those hold, a fulfilment lint must **fail closed and say which precondition was missing**, rather than return a verdict it is not entitled to.

## `Draft` is overloaded and must stop carrying shaping progress

`Draft` currently answers three questions at once: has this been de-risked, has it passed a shaping review, and is it still open. Only the third is a lifecycle state. The other two are shaping progress, and the corpus already contradicts reading them off `Draft` — a body scan finds de-risk records under 9 of the 130 Draft intents, this family's own `CAP-0001`, `CAP-0003` and `FEAT-0001` among them.

This child owns the consequence: **a transition may not be gated on anything inferred from a body.** Whether an intent has been de-risked or reviewed must be read from declared preamble metadata, whose shape [FEAT-0001](FEAT-0001-intent-identity-and-registration.md) owns, and `Draft` must narrow to meaning open. A closure rule that pattern-matches body headings is not mechanical verification — it is a guess that returns a clean answer whether or not the probe ever ran, which is the exact failure this intent's fulfilment claim cannot tolerate.

## Staleness refresh at closure

A closure decision is made against state that may have moved since anyone looked, so the criterion must be **re-derived at the moment of closure** rather than read from a cached rollup or a status recorded earlier.

The repository already treats freshness as gate-worthy and positions the gate in the wrong place for this. `check-base-freshness.py` verifies HEAD against the merge target and is run **before reading** `workspace.toml` or any spec — at entry to the work, not at the point a terminal status is written, which is when the claim being made is strongest and least recoverable.

The refresh owes three checks, and this child owns specifying them:

- **Children re-read, not remembered.** Every child's status is resolved from the artifacts at decision time. A rollup computed minutes earlier is evidence that a walk ran, not evidence that the tree is still in that state.
- **The base is current.** The same condition `check-base-freshness.py` already enforces, applied at the closing edge rather than only the opening one — a closure computed against a stale base can miss a child that moved on the merge target.
- **The artifact's own claims still hold.** An intent carries evidence, counts and citations that decay. Closing it ratifies that content as final, so a closure that does not revalidate its own assertions freezes whatever drift accumulated.

This is also where the fulfilment rollup's liveness gets tested rather than assumed. A rollup that stops walking because an edge is missing reports the same silence as a correct negative, and closure is the transition where that silence is most expensive.

## Assumptions

- **Fulfilment is decidable by a lint over the graph, not by a review.** The judgement is paid once at `Accepted`, where the shaping review verifies the decomposition partitions the outcome; after that, every child terminal mechanically entails the outcome delivered. **Untested**, and the load-bearing bet of this child — it is what makes closure scale, and it is only valid while the four preconditions above hold.
- A closure-time staleness refresh is affordable at the moment of decision. **Untested** — re-deriving every child's status on each closure is cheap at today's tree depth and is the kind of cost that grows with the corpus.
- Closure can be decided per intent without the decider re-reading the subtree. This is the rollup's promise and the reason eligibility is computed rather than asserted. **Untested.**
- The existing disposition contract covers a closed intent's record without extension. **Untested** — it was written for delivery outputs and temporary state, not for a product bet.

**Not de-risked.** No assumption above carries a kill condition. Re-enter `frame-intent` → `de-risk-intent` → `decompose-intent` before decomposing this intent.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.
