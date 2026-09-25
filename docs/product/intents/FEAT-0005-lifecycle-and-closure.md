# Lifecycle and closure

- **Slug:** `lifecycle-and-closure` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Accepted
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:repository-work-graph
- **De-risked:** 2026-09-23
- **Shaping-reviewed:** 2026-09-23
- **Decomposed:** 2026-09-23 brief
- **Accepted:** 2026-09-24 independent intent-mode shaping review returned zero MALFORMED tokens against a packet of this intent and CAP-0001; eugenelim confirmed

## Outcome

- **Steerable input:** The share of intents whose recorded status matches their real state, and the number of terminal transitions a person can make through a workflow rather than by editing a field.
- **Lagging outcome:** An intent whose work is delivered, abandoned or superseded carries a terminal status set through a workflow, so the graph distinguishes live bets from finished ones without a reader inspecting each artifact's descendants.
- **Guardrail:** A status is never set by a count. Closure is decided by a human on presented evidence, and a terminal transition passes whatever review gate governs it. A closed intent's record is retained or disposed of under the existing disposition contract rather than a second one invented here.

## Opportunity

- **Functional job:** Close an intent when its work is done, and have the graph show that.
- **Emotional job:** Trust that a list of open intents is a list of live bets rather than an archive nobody dares prune.
- **Social job:** Show a portfolio that distinguishes what is being pursued from what has been achieved.
- **Struggling moment:** An intent can be opened and ratified but never closed. No workflow can mark one closed, so the fourteen intents that do carry `Fulfilled` were all set by hand — and thirteen of them record nothing about who decided, when, or on what evidence.

## Boundary

Inherits the parent's outcome, boundary, and exclusions. Within them, this child owns five things, and § The lifecycle below is where each is specified.

1. **The state table and the legal transition set**, for an intent and for a brief. Which values exist, what each means, which are terminal, and which workflow may make each move.
2. **The `Draft` narrowing**, and what the three shipped shaping-progress fields mean for a transition.
3. **The three-way classify** at a closure check — refuse, not eligible, eligible — and specifically that a refusal is distinct from a "no".
4. **The evidence packet** `close-work` presents to the human who decides.
5. **The closure record** written when a terminal status is set, so the decision survives the session that made it.

Owner decision, 2026-09-18: `Fulfilled` is a supported status going forward, and it is set in the `close-work` flow, alongside the brief terminal transitions that flow already owns.

It does not own four neighbouring things. Computing eligibility is the parent capability's, delivered jointly by [Intent graph navigation](FEAT-0002-intent-graph-navigation.md) and [Intent-to-delivery traceability](FEAT-0003-intent-delivery-traceability.md). Identity, placement and admission are [Intent identity and registration](FEAT-0001-intent-identity-and-registration.md)'s — that child owns entry, this one owns exit. Retention or disposal of a closed record is `close-work`'s existing disposition contract. And the shape of any new **intent** preamble field named here is `FEAT-0001`'s to define. **Owner decision, 2026-09-23:** that boundary covers intents only. A **brief's** preamble field — the cut-closed declaration — is this child's, delivered in its third slice, because the surface is core-pack only and `FEAT-0001` is intent identity and registration.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Unresolved questions

Two of these were routed here by artifacts that could not settle them. Each names its router, so the obligation is traceable back.

- **Whether the shaping skills must write their field on every run.** The 2026-09-23 sweep's own disposition is closed — it was completed in-session, outside a spec, and is not re-homed. What stays open is the durable half: whether `decompose-intent` and `de-risk-intent` must record `Decomposed:` and `De-risked:` on every future run, so the corpus never needs a second sweep. May be `FEAT-0001`'s rather than this child's.
- **Whether the existing disposition contract covers a closed intent's record.** It was written for delivery outputs and temporary state, not for a product bet. **Owner decision, 2026-09-23:** the closure flow looks the contract up as an **optional** check rather than a required one, and must handle the case where no product-bet disposition exists — reporting the absence rather than assuming a default or failing. **Settled 2026-09-24: it does not.** The § Validation hook carries the reading and its verdict. Six intents are `Withdrawn` today — closed, not delivered, carrying no continuing obligation — and no row's eligibility clause reaches them, so the optional lookup this owner decision describes reports an absence for every one of them rather than for an edge case.
- **Whether a closure check firing on every descendant's terminal transition stays affordable** once the corpus is fully decomposed. Cheap today. The cost scales with tree depth, not corpus size, so it grows as the ladder is populated rather than as intents are added.

One question routed here has been settled, and § Legal transitions owns the answer: whether an intent may reach a terminal state without first passing `Accepted`. It may, but only `Withdrawn`.

## Projection

Projects to its delivery brief, [an intent and a brief can be closed through a workflow, on recorded evidence](../briefs/intent-lifecycle-and-closure.md). The brief owns its own status and its own Spec map. No outbound tracker projection: that surface is [CAP-0004](CAP-0004-external-tracker-projection.md)'s and is not yet shaped.

## Where closure stands today

**No workflow can close an intent.** The word `Fulfilled` appears exactly once anywhere under `packs/` — in the `frame-intent` template's list of allowed values. Nothing sets it.

**Closures that did happen left no trace.** Fourteen intents carry `Fulfilled`. One, `STRAT-0002-platform-core`, records who closed it, when, and on what evidence. The other thirteen record none of those. A terminal status with no reason behind it cannot be audited, questioned or reversed.

**The gate gets lighter as the claim gets bigger.**

| Closing | Criterion | Review at the moment of closure |
| --- | --- | --- |
| Spec → `Shipped` | acceptance criteria met, tasks complete | **Full reviewer roster.** Every warranted mandatory reviewer clean, no unresolved Blocker or Concern, deferred Nits carrying citations |
| Brief → `Shipped` | non-empty materialized Spec map fully Shipped | **No reviewer.** `close-work` dispatches none; the gate is the criterion plus an explicit human confirmation |
| Intent → `Accepted` | contract is well-formed | **Independent shaping review** in intent mode, zero `MALFORMED` tokens, plus human confirmation |
| Intent → `Fulfilled` | all children terminal | **Nothing. The transition does not exist.** |

A brief's exit gate is lighter than an intent's *entry* gate, and the intent's exit gate is absent. The lifecycle below closes both gaps.

## The lifecycle

### Intent states

The member set is **already shipped** and machine-enforced by [`intent-metadata-shape-contract`](../../specs/intent-metadata-shape-contract/spec.md), whose corpus lint refuses any other value. That spec fixes the members; this child fixes what they mean and who may move between them.


| State | Means | Terminal |
| --- | --- | --- |
| `Draft` | open, still being shaped | no |
| `Accepted` | contract ratified, decomposition verified | no |
| `Fulfilled` | outcome delivered | yes |
| `Withdrawn` | stopped before any execution | yes |
| `Cancelled` | stopped after execution evidence exists | yes |
| `Superseded` | replaced by the intent named in `Superseded by:` | yes |

### Legal transitions

| From → To | Who may make it | Gate |
| --- | --- | --- |
| `Draft` → `Accepted` | shaping review, then the owner | independent intent-mode review, zero `MALFORMED` tokens, human confirmation |
| `Draft` → `Withdrawn` | `close-work` | human confirmation; no execution evidence exists |
| `Accepted` → `Fulfilled` | `close-work` | the closure flow below |
| `Accepted` → `Cancelled` | `close-work` | human confirmation; execution evidence exists |
| `Draft` or `Accepted` → `Superseded` | admission of the superseding intent | a `Superseded by:` field names a live intent, and the slug resolves |

**Owner decision, 2026-09-23 — supersession splits into a bare status and a pointer field.** `Status` carries one lifecycle token and a separate `Superseded by:` field carries the pointer. This mirrors the ADR corpus rather than inventing a shape: [`checkable-adr-metadata`](../../specs/checkable-adr-metadata/spec.md) states the principle — "`Status` is one bare lifecycle token, supersession is a set of mirrored fields naming ordinals and constraint IDs rather than a sentence" — and both superseded ADRs on disk carry `Status: Superseded` beside `Superseded by: ADR-NNNN`. It also removes the anomaly that prompted the question: every terminal value becomes a claim about this artifact, and the only pointer moves to a field. **Delivering it is not this child's.** The Ready review of the delivery brief found that [`intent-metadata-shape-contract`](../../specs/intent-metadata-shape-contract/spec.md) is `Shipped` under a different brief, and its ticked AC-0002 fixes `Superseded by <slug>` inside the `Status` vocabulary while AC-0021 reads the pointer out of `Status`. Both need amending, and an intent preamble field's shape is `FEAT-0001`'s under § Boundary above. So the change is handed to [`intent-identity-and-registration`](../briefs/intent-identity-and-registration.md), whose § Post-Ready decisions carries it and whose Spec map already holds the spec. No intent carries the status today, so there is no corpus to migrate; the cost is the contract and the readers of the embedded pointer. This child's state table consumes whatever form that brief lands.

No other move is legal, and two consequences are deliberate.

**There is no `Accepted` → `Draft`.** Reopening a ratified contract is a new intent that supersedes the old one, so the ratification stays attached to what was actually ratified.

**Ten intents are already in a state this rule forbids.** Of the fourteen carrying `Fulfilled`, ten never reached `Accepted` at any point in their history. Adopting the transition rule makes them illegal, so it carries a migration obligation: each is either walked back through `Accepted` or reclassified to a terminal state it qualifies for. **Owner decision, 2026-09-23 — there is no recorded-exception outcome.** An exception would rest in a state the rule forbids, so reading it would need a declared marker field and a permanent contract surface, bought for a one-off migration. The two remaining outcomes both leave a state a corpus scan reads natively. The migration itself is a working session, not shipped functionality. The rule may not ship before it runs.

**An intent may reach a terminal state without passing `Accepted`, but only `Withdrawn`.** `intent-metadata-shape-contract` routes this question here and fixes only the member set. The answer: abandoning an unratified bet needs no ratification, so `Draft` → `Withdrawn` is legal. `Fulfilled` and `Cancelled` both assert something about delivery against a decomposition, so both require `Accepted` first. An unaccepted intent that claims delivery is claiming it against a partition nobody verified.

### The closure flow

**1. Trigger.** A descendant reaching a terminal state fires a closure check on its ancestors. `close-work` already runs at that moment, so the check rides on it. There is no sweep and no schedule: closure is considered exactly when something underneath finishes.

**2. Gather, at decision time.** Nothing is read from cache. Every child's state, every delivery artifact's state, and the freshness of the base are resolved from the artifacts when the decision is being made. § Staleness refresh at closure owns the three checks this owes.

**3. Classify into three.** The check returns one of three answers, and the first two are not the same answer.

| Answer | When | What it says |
| --- | --- | --- |
| **Refuse** | the walk is not entitled to an opinion | which precondition was missing — the intent never reached `Accepted`, a child edge is absent, or the status vocabulary is not closed |
| **Not eligible** | the walk ran and something live sits underneath | which descendant, and what state it is in |
| **Eligible** | everything below is terminal | the evidence, assembled for step 4 |

**Refuse and not-eligible must stay distinct.** Collapsing them is how a check returns a clean answer it never earned. An intent with nothing recorded beneath it and an intent whose work is genuinely finished produce the same silence. Only the three-way split tells the reader which one they are looking at.

**4. The human decides, on the presented evidence.** The Guardrail above already requires this — a status is never set by a count. The check's job is to assemble evidence and to refuse loudly when it cannot, not to reach a verdict a person then rubber-stamps.

**5. Record the decision.** A terminal transition writes a closure record carrying the date, who decided, and what evidence they saw. `STRAT-0002-platform-core` is the only intent on disk that does this today, and it is the model: a `Fulfilled:` preamble line naming the date and decider, with the evidence beneath it.

### Briefs take the same flow, and need one field

A brief runs `Draft` → `Ready` → `Executing` → `Shipped`, `Withdrawn` or `Cancelled`. Its child set is its mapped specs, so steps 2 to 5 above are identical.

One thing blocks it. A brief stays `Executing` when every materialized child is Shipped but another slice has not been materialized yet. **No brief carries any state saying the cut is closed and no further slices are coming.** So today's human confirmation at brief closure answers a question the artifact cannot state. Add the **cut-closed declaration** and "every mapped spec is Shipped" becomes a real criterion rather than a partial one.

## `Draft` narrows to mean open

`Draft` currently answers three questions at once: has this been de-risked, has it passed a shaping review, and is it still open. Only the last is a lifecycle state.

The other two are shaping progress, and the only way to ask them today is to read the body and pattern-match its headings. That is not a check. It returns a clean answer whether or not the probe ever ran, which is the same defect the three-way classify exists to prevent.

**So: no transition may be gated on anything read out of a body.**

Three declared fields already carry this, shipped by `intent-metadata-shape-contract`: `De-risked:` and `Shaping-reviewed:` each take an ISO 8601 date or the literal `no`, and `Decomposed:` takes `no`, or a date plus one terminus from `children`, `brief`, `spec`, `direct-light`.

So the fields exist and are enforced. What does not exist is any rule saying what their values mean for a transition, and that is this child's.

## Staleness refresh at closure

A closure is decided against state that may have moved since anyone looked. The criterion is therefore **re-derived at the moment of closure**, never read from a cached rollup or an earlier status.

The repository already treats freshness as gate-worthy but puts the gate in the wrong place for this. `check-base-freshness.py` checks HEAD against the merge target *before* the work reads `workspace.toml` or any spec. That is entry to the work, not the point a terminal status is written — which is when the claim is strongest and least recoverable.

Three checks, and this child owns specifying them.

1. **Children re-read, not remembered.** Every child's status resolves from the artifacts at decision time. A rollup computed minutes ago proves a walk ran, not that the tree is still in that state.
2. **The base is current.** The same condition `check-base-freshness.py` enforces, applied at the closing edge. A closure computed against a stale base can miss a child that moved on the merge target.
3. **The artifact's own claims still hold.** An intent carries evidence, counts and citations that decay. Closing it ratifies that content as final.

This is also where the rollup's liveness is tested rather than assumed. A rollup that stops walking because an edge is missing looks exactly like a correct negative — which is why step 3 refuses instead of answering.

Cost is not a constraint. A full re-derivation reading `Status` from every intent, brief and spec — 675 artifacts — takes under a second, so there is no reason to cache and every reason not to.

## Assumptions

- **A1 — Fulfilment is decidable by a lint alone, with no reviewer and no per-instance human confirmation.** **Withdrawn 2026-09-23.** Not on evidence, but because it contradicted this intent's own Guardrail, which says a status is never set by a count and closure is decided by a human on presented evidence. The De-risk record owns what replaced it.
- **A2 — A closure-time staleness refresh is affordable at the moment of decision.** **Survived 2026-09-23**, measured.
- **A3 — Closure can be decided without the decider re-reading the subtree.** The load-bearing bet, and **killed 2026-09-23** on a retrospective walk of all fourteen closed intents. The cause is precise and fixable: the packet carries the members and their states, but not the ratification that those members are the *complete* set.
- **A4 — The existing disposition contract covers a closed intent's record without extension.** **Untested**, and it has never carried a kill condition.
- **A5 — Shaping-review condition 5 is a reliable ratification.** `Accepted` is what entitles the closure check to run at all, so the flow inherits this condition's confidence. **Survived 2026-09-23 on a coarse gap**, with a subtle-gap arm still owed.

## De-risk record

- **Level kind:** feature, but the dominant assumption is **architectural**, not desirability. Nobody disputes that a closed intent should be able to say so. The risk is in the mechanism.
- **Reversibility triage:** one-way door. A wrongly-closed intent is not a visible error. It is an absence, and an absence reads as "nothing to do here" — this intent's own harm, inverted.
- **Prototype-approach:** `validate-first`.

### A1 — withdrawn on the Guardrail, not on measurement

A1 held that closure needs no reviewer and no per-instance human confirmation, because the judgement was paid once at `Accepted`. The Guardrail three sections above already says the opposite: *"A status is never set by a count. Closure is decided by a human on presented evidence."* The two cannot both stand, and the Guardrail is the accepted contract.

So the question was never whether a machine could decide. It was what the machine hands the human. A1 is withdrawn and replaced by the flow in § The lifecycle. The check assembles evidence, classifies three ways, and refuses when it is not entitled to an opinion. The human decides. The system records what they decided and why.

**What the replay did and did not show.** A replay of the `all children terminal` rule on 2026-09-23 returned eligible for six of sixteen `Accepted` intents. Five were decided on an empty child set.

That measured **a corpus nobody has decomposed yet**, not a defective predicate. Most intents have nothing beneath them because the work of fleshing them out has not happened. It is not evidence against the rule for a populated corpus, and it is not cited as such.

Two design constraints did come out of it, and both hold independently of how full the corpus is. They are C1 and C2 below.

### A5 — survived, on a coarse gap

`Accepted` is what entitles the closure check to run, so the flow inherits whatever confidence the acceptance review had. Condition 5 of that review — *the decomposition partitions the artifact's own outcome, with no overlap and no gap* — had been recorded on 2026-09-19 as returning opposite verdicts on byte-identical content, twice.

**Kill condition, predeclared** and written to file before any reviewer ran. Two arms against `CAP-0001-repository-work-graph`, three runs each, byte-identical within an arm, each reviewer given only its own packet.

- **Control** — `CAP-0001` unchanged. Its five children cover its outcome.
- **Mutant** — the `FEAT-0003` child removed, plus its two mentions in the decomposition rationale. The Outcome still requires each artifact's delivery mapping to be answerable, and nothing left owns it.

Kill A5 if **S1** the three runs within either arm disagree, or **S2** the mutant does not fire `MALFORMED(children)` in all three runs, or the control fires it in any run.

**Result — survived. Six runs, 3/3 in both arms.**

| Arm | Run 1 | Run 2 | Run 3 |
| --- | --- | --- | --- |
| Control | `MALFORMED(altitude)` | `MALFORMED(altitude)` | `MALFORMED(altitude)` |
| Mutant | `MALFORMED(altitude)` `MALFORMED(children)` | `MALFORMED(altitude)` `MALFORMED(children)` | `MALFORMED(altitude)` `MALFORMED(children)` |

Condition 5 was silent on the partition and fired on the gap, every time. `MALFORMED(altitude)` appears on all six runs because each packet names a parent it does not include, and the reviewer fails that closed. It is the same in both arms, so it does not bear on condition 5.

**The limit, stated rather than implied.** This tested a **coarse** gap — one whole child deleted from a five-child cut. It does not show condition 5 holds on a subtle gap, where the coverage call is genuinely close, and that is the likelier shape of the 2026-09-19 observation. This result does not refute that earlier one; different content, five days apart. What it establishes is narrower and still useful: condition 5 is not noise, and it can fail.

### A2 — survived

A full re-derivation reading `Status` from all 675 intents, briefs and specs completes in **0.27 s warm and 0.75 s cold**. Re-reading children at decision time costs nothing worth designing around, which is why § Staleness refresh at closure forbids caching outright rather than trading freshness against cost.

### A3 — killed on the retrospective closure walk

The fourteen intents already carrying `Fulfilled` were closed by hand with no recorded evidence, which makes them a free test set: build the packet the flow would have produced, then ask whether it would have been enough.

**Kill condition, predeclared** and written to file before any packet was built. The packet was fixed first, to steps 2 and 3 of the flow: the intent's `Status` and whether it ever reached `Accepted`; every child intent with its state; every delivery artifact declaring an up-edge to it, with its state; the three shaping-progress fields; and the classify verdict. Nothing else.

Kill A3 if **P1** deciding correctly requires, for any of the fourteen, a fact the packet does not carry — bar zero; or **P2** the classify returns eligible for an intent that was not delivered, or refuses one that plainly was *without naming a reason that is actually true*. A refusal naming a true missing precondition is a correct answer here. The flow is allowed to say it cannot tell.

**Result — 12 refuse, 2 eligible, 0 not-eligible.**

**P2 passes.** Every refusal named a true precondition. Ten intents never reached `Accepted` at any point in their git history, and two had nothing at all recorded beneath them. Both are real, and both are the check correctly declining to answer.

**P1 fires, on `cut-before-adding-solution-ladder`.** Its packet reads *six delivery artifacts, all Shipped*. Its Outcome is that adopters create fewer unnecessary artifacts while still moving from an idea, ticket, intent or brief into governed delivery. The packet says six things shipped that each *claimed* this intent as their source. It does not say those six cover that outcome, and nothing ratified that the set was complete: when the walk ran, `Decomposed:` was absent on every intent in the corpus. A backfill later that day put the field on this intent and 23 others, so the reframed assumption is now re-testable against this same case; § Validation hook owns that owed re-run. So the decider must open the Outcome and the six specs and judge coverage themselves, which is exactly the subtree re-reading A3 promised to remove.

**The fix is already half-built.** `Decomposed:` shipped with `intent-metadata-shape-contract` and takes a date plus one terminus from `children`, `brief`, `spec`, `direct-light`. That field is where the ratification belongs: it records that the delivery set was blessed and what shape it takes. Once an intent carries it, the packet's member list is a ratified set rather than whatever happened to point back, and the decider checks states instead of re-judging coverage. **A3 is therefore reframed, not abandoned:** the packet is self-sufficient for an intent whose `Decomposed:` records a ratified terminus, and refuses for one that does not.

**What the walk could not test.** The classify never returned not-eligible once, because nothing in the corpus has live work recorded beneath it. That branch is untested and the validation hook carries it.

### Constraints carried forward

Neither depends on how populated the corpus is. Both belong to whoever implements this child.

- **C1 — a carve-out must change the Outcome or name the co-owner.** Moving scope out of an intent to a peer is normal shaping. It leaves the original Outcome promising something it no longer wholly owns, and no edge records that, because the relation is neither parenthood nor delivery. `remote-ci-verification-parity` is the live instance. Its Outcome requires the native Windows and macOS portability contracts. Its body hands that half to `native-platform-verification-coverage`, and states plainly that the contract "describes the eventual state across both items, not this intent alone".

  The remedy belongs at carve-out time, not at closure time: amend the Outcome, or declare the co-owner. Defining the mark is `FEAT-0001`'s shape work; **refusing to close without it is this child's**, because this child is where the wrong answer would be written to disk.
- **C2 — an empty child set is a refusal, not a pass.** A universal over an empty set cannot fail, so "every child is terminal" is vacuously true for an intent with nothing recorded beneath it. That intent is in one of two states the check cannot tell apart: a real leaf that is complete, or a node nobody has decomposed yet. The three-way classify is the remedy — an empty child set returns **refuse**, naming the absence. `STRAT-0002-platform-core` shows the legitimate exception and its price: its decomposition says "the partition is closed, not empty" in prose, and its closure took an independent verification. A closed-and-empty decomposition needs a declared marker, not silence.

### Validation hook

```
validation_hook:
  assumption: The closure check can hand a decider an evidence packet complete enough that they decide without re-reading the subtree themselves.
  kill_condition: KILLED 2026-09-23 on P1. A retrospective walk of all 14 closed intents returned 12 refuse, 2 eligible, 0 not-eligible. Every refusal named a true precondition, so P2 passed. P1 fired on cut-before-adding-solution-ladder: its packet reads "six delivery artifacts, all Shipped" but carries nothing saying those six cover its outcome, because Decomposed: is absent on all 150 intents and no ratified delivery set exists. The reframed assumption is that the packet is self-sufficient for an intent whose Decomposed: field records a ratified terminus, and its kill condition is the same walk, re-run after adoption, returning any eligible verdict whose decider still had to open an artifact the packet did not name.
  activity: to-validate -- four activities were owed; the zeroth has now run and three remain. Zeroth, settle A4: read close-work's disposition contract against a closed product bet and record whether it covers one, with the line set before reading -- it covers the case if a closed intent's record needs no clause the contract does not already carry. RAN 2026-09-24, and the line was not met: A4 SETTLES AGAINST COVERAGE. The contract carries six intents. Four cannot reach a committed governance record at all -- discard-local requires tool-owned temporary state with no lasting content, delete-before-push requires a target never pushed, delete-before-merge requires a change not yet integrated, and external-advisory requires the environment to lack authority over the target. Of the two that can, cool-30-days is eligible on DELIVERED closed work, which reaches Fulfilled, and retain-exception is eligible where a longer obligation or live dependency requires retention. Neither reaches a bet that closed WITHOUT delivering and carries no continuing obligation, which is what Withdrawn and Cancelled assert, and the contract's fall-through for an unmatched case is to refuse classification -- a refusal, not a disposition. Measured against the corpus the same day: 6 Withdrawn, 0 Cancelled, so the gap is live rather than hypothetical. The missing clause is an eligibility row for closed-without-delivery. Consequence, per the delivery brief's retention non-goal: the retention extension returns to that brief's scope. Because the cut was already confirmed on 2026-09-23 with A4 open, it returns as a later slice rather than as a candidate inside the confirmed cut. First, populate Decomposed: on a handful of intents, re-run the walk, and have a human decide one eligible case for real, then state what they opened that the packet did not name; the line is that they opened nothing, set before the walk. Second, a not-eligible case, which this walk could not produce because nothing in the corpus has live work recorded beneath it: construct one and confirm the branch names the live descendant rather than refusing. Third, a subtle-gap arm for condition 5, since Accepted is what entitles the check to run -- the 2026-09-23 test used a coarse gap, one whole child deleted, and the arm owed narrows a child's scope so the cut still reads plausible, with a predeclared line of 3/3 MALFORMED(children) on the mutant and 3/3 silence on its control. Observation contributed 2026-09-24 by the catalogue-phase-4 session, attributed and NOT reproduced here, so it grounds no verdict and does not discharge this arm: five intent-mode runs across two artifacts that day; three MALFORMED(children) verdicts were diagnosed by inference, two of those inferences were wrong, and the correct cause -- overlap rather than gap -- was found by reading condition 5's text in the agent definition rather than the output. No run repeated on byte-identical content, so it bears on neither side of the 2026-09-19 non-determination. What it does bear on is the arm's cost: a token carrying no diagnosis is read by inference, and inference about this token was wrong more often than right in the one sample on record. A contributor's first count of six runs across three artifacts was corrected down by that contributor, who had folded in spec-mode runs; the figures above are the corrected ones.
```

**De-risked 2026-09-23.** A1 was withdrawn against this intent's own Guardrail rather than killed by evidence, and the flow in § The lifecycle replaces it. A3 was killed on the retrospective walk and reframed: the packet is self-sufficient once `Decomposed:` records a ratified delivery set, and refuses without it. A2 and A5 survived their predeclared bars, A5 with a subtle-gap arm still owed. A4 never carried a kill condition, but it did carry a line set before reading, and the § Validation hook's zeroth activity ran it on 2026-09-24: `close-work`'s disposition contract does not cover a bet that closed without delivering, so A4 is settled against coverage and the retention extension returns to the delivery brief's scope as a later slice. C1 and C2 travel into decomposition, and the transition rule carries a migration obligation for the ten intents already in a state it forbids. This intent is ready for `decompose-intent`.


## Decomposition

This intent is a `feature`, so it is the leaf: `decompose-intent` produces its delivery unit rather than child intents.

- [Brief: an intent and a brief can be closed through a workflow, on recorded evidence](../briefs/intent-lifecycle-and-closure.md) — the delivery unit this feature projects to.

The transition contract, the closure check in `close-work`, and the brief cut-closed declaration are **candidate** delivery slices. The cut between them belongs to the post-Ready decision, not here.

### Decomposition decisions

- **2026-09-23 — a delivery brief, not a single delivery contract.** [ADR-0077](../../adr/0077-feature-projection-and-tracker-authority.md) D1 routes one independently shippable change in one repository to a spec and several to a brief. Three candidates each ship and test alone: the transition contract is verifiable by a corpus lint refusing an illegal transition; the closure check is verifiable against a fixture tree; the brief cut-closed field serves a different artifact kind with a different criterion. A single spec would have bundled three verification surfaces into one contract.
- **2026-09-23 — the closure check was not split from its evidence packet.** Separating "classify" from "present" is a split by layer, not by shippability. Neither half delivers anything alone: a classification nobody sees, or a packet with no verdict attached. They stay one candidate slice.
- **2026-09-23 — the migration rides with the transition contract rather than becoming its own slice.** Ten intents reached `Fulfilled` without `Accepted`, so adopting the rule makes them illegal. The rule cannot ship leaving the corpus in a state it forbids, so the migration is part of that slice's completion rather than a follow-on.
- **2026-09-23 — the slice cut was deliberately not made here.** `author-delivery-brief` places the cut after a durable Ready transition, behind a second and distinct human confirmation. Naming slices now would pre-empt a review that has not run.
- **2026-09-23 — no ranking step.** Ranking applies to children competing for one appetite. The candidates are ordered by dependency: the closure check needs the transition contract for the meaning of terminal, and the cut-closed field is independent of both.
- **2026-09-23 — no tracker projection.** `CAP-0004` owns that surface and it is not yet shaped.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.
