# Brief: an intent and a brief can be closed through a workflow, on recorded evidence

- **Slug:** `intent-lifecycle-and-closure`
- **Received:** 2026-09-23
- **Owner:** eugenelim, Platform Core maintainer
- **Status:** Ready
- **Parent intent:** intent:lifecycle-and-closure
- **Ready confirmed:** 2026-09-23 by eugenelim, lifecycle owner. Taken on a `Findings` result, not a `Clean` one — recorded here because `author-delivery-brief` expects a revision-bound `Clean` and this transition did not have one. Six delivery-brief shaping reviews ran. The first found two Blockers, both resolved by moving work rather than arguing: the supersession split went to [`intent-identity-and-registration`](intent-identity-and-registration.md), which owns the shipped spec it touches. The five rounds after that returned no Blocker. The last returned two Concerns and one Nit; all three are fixed above and were not re-reviewed. The owner judged the contract sound and the residual findings to be authoring craft rather than contract defects.
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/FEAT-0005-lifecycle-and-closure.md`](../intents/FEAT-0005-lifecycle-and-closure.md), de-risked 2026-09-23. Authored under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md).

## Outcome

An intent or a brief whose work is delivered, abandoned or superseded reaches a terminal status through a workflow rather than a hand edit, and the decision is recorded with the evidence it rested on. A reader of the open list sees live bets. A reader of a closed artifact sees who closed it, when, and on what basis.

## Current-state evidence

The parent intent's § Where closure stands today owns the measurement and its date. It establishes four things this brief builds on: no workflow can set `Fulfilled`; the intents that carry it were set by hand and almost none records why; most of those never reached `Accepted`, so they already sit in a state the transition rule would forbid; and the gate governing a closure gets lighter as the claim gets bigger, with the intent exit gate absent entirely.

Two further facts are this brief's own.

- **The field contract this brief gates transitions on already exists.** [`intent-metadata-shape-contract`](../../specs/intent-metadata-shape-contract/spec.md) establishes the closed `Status` vocabulary, the three shaping-progress fields (`De-risked:`, `Shaping-reviewed:`, `Decomposed:`) each validated when present, and preamble bounding under AC-0011. It routes the transition rule here. It is a spec, so it is cited here rather than in § Governance references, which carries RFCs and ADRs only.
- **Those fields were populated on 2026-09-23**, wherever the fact was verifiable from the artifact or from git, and left absent everywhere else. Absent and `no` are different claims: absent records that nobody decided, `no` asserts a decision against. § What sits outside the loop owns what that route means and what stays open.

## Scope / Non-goals

**In scope.**

- The state table and legal transition set for an intent and for a brief, including which workflow may make each move and what the three declared shaping-progress fields mean for a transition.
- `Draft` narrowed to mean open, and the rule that no transition may be gated on anything read out of an artifact body rather than from a declared preamble field.
- The three-way classify at a closure check — refuse, not eligible, eligible — with a refusal naming the precondition it is missing.
- The evidence packet presented to the human who decides, and the closure record written afterwards.
- The staleness refresh: children re-read rather than remembered, the base current at the closing edge, and the artifact's own claims revalidated.
- The cut-closed declaration on a brief.
- One reader-facing guide page covering the states, the transitions and the closure flow, extended by each slice as part of that slice's completion. This is this brief's own scope decision, not an inherited obligation.
- Migrating the intents that reached `Fulfilled` without `Accepted`. Each is walked back through `Accepted` or reclassified to a terminal state it qualifies for. There is no recorded-exception outcome, by owner decision of 2026-09-23; the parent's § Legal transitions owns the ground. The parent's decomposition decision places the migration inside the transition slice's completion, because the rule may not ship leaving the corpus in a state it forbids.

**Non-goals.**

- **Owning the derived graph and its traversal contract.** The parent capability's, delivered by [FEAT-0002](../intents/FEAT-0002-intent-graph-navigation.md) and [FEAT-0003](../intents/FEAT-0003-intent-delivery-traceability.md). The exclusion covers the graph as a durable surface other consumers read — its node and edge model, its traversal contract, and any persisted projection of it. It does **not** cover the closure check resolving a child's `Status` from the artifacts at decision time, which § Constraints requires of it. So the check may read child state; it may not become the repository's rollup.
- **Defining an *intent* preamble field's shape — its name, its value vocabulary and its validation.** [FEAT-0001](../intents/FEAT-0001-intent-identity-and-registration.md)'s, under the parent's § Boundary, which the owner amended on 2026-09-23 to say the boundary covers intents only. A **brief's** preamble field is not excluded: the cut-closed declaration's shape and its preamble bounding are slice 3's. The parent's § Boundary owns the ground. This brief decides what a field's value means for a transition, for both artifact kinds.

  A brief's preamble bounding is slice 3's third instance of a pattern that already exists for intents and for specs; that slice's Size paragraph names both.
- **Retention or disposal of a closed record**, *provided* `close-work`'s existing disposition contract covers a product bet. Whether it does is open — the parent carries it as A4, untested and never given a kill condition. If it does not cover the case, the extension returns to this brief's scope rather than becoming a second contract. **A4 is therefore settled before the slice-cut confirmation**, so the extension can enter the cut as a candidate rather than arriving after the delivery map is material-locked. The parent's § Validation hook carries A4 as its first owed activity.
- **Outbound tracker projection.** [CAP-0004](../intents/CAP-0004-external-tracker-projection.md)'s surface.
- **Deciding closure automatically.** The parent's § Outcome › Guardrail.

## Constraints / Appetite

Five constraints carry forward from the parent, which owns the reasoning and the case behind each. They are pointers, not copies — the parent's C1 in particular splits ownership in a way a one-line restatement loses.

- **C1** and **C2** — the parent's § De-risk record › Constraints carried forward. C1 governs when the check must refuse a carve-out; C2 forbids a verdict on an empty child set. Both are refusal conditions a delivery slice implements.
- The parent's **§ Outcome › Guardrail** forbids a status set by a count, its **§ The lifecycle** step 3 requires refuse and not-eligible to stay distinct, and its **§ Staleness refresh at closure** forbids reading any of it from cache.

No appetite ceiling is set, by owner decision of 2026-09-23: the capability has to land whole, so a scope cap would cut something the outcome needs rather than protect the cut. § Candidate delivery slices sizes each slice instead, to sequence them.

## Assumptions / Risks

- **[Survived]** A closure-time staleness refresh is affordable. The parent's A2 owns the measurement.
- **[Survived, with a gap]** Shaping-review condition 5 is stable and can fail, so `Accepted` is worth something as a precondition. Tested on a coarse gap only. A subtle-gap arm is owed.
- **[Killed, reframed, re-testable]** The evidence packet is self-sufficient only for an intent whose `Decomposed:` records a ratified delivery set. The parent's A3 owns the walk that killed the wider claim. The intent whose packet failed now carries `Decomposed:`, so the reframed assumption can be re-tested against the same case. That re-run is owed.
- **[Untested]** `close-work`'s disposition contract covers a closed intent's record without extension. Never carried a kill condition. The conditional non-goal above depends on it.
- **Risk: the not-eligible branch has never run.** The retrospective walk produced refusals and eligible verdicts but no not-eligible, because nothing in the corpus has live work recorded beneath it. It is the normal case once the ladder fills and the only path with no evidence behind it.
- **Risk: the check refuses most of the corpus for a long time.** Most intents have not been decomposed, so `Decomposed:` is legitimately absent and the check refuses them by design. Correct behaviour, and also almost all of the behaviour until the ladder fills.
- **Risk: the migration is a judgement per artifact.** Whether each one is walked back through `Accepted` or reclassified cannot be decided mechanically.

## What sits outside the loop, and what does not

`work-loop`'s own description sets this boundary. The risk-trigger block does not: it chooses between light and full **once the work is already in the loop**, so it cannot decide membership, and this section does not use it for that.

That description names what belongs in the loop — including **migration** — and names what does not, including **shaping**. Both halves matter here, because the same field can be written by either kind of work.

- **Writing a shaping-progress field on one intent, as part of that intent's own shaping, is shaping.** `decompose-intent` recording its own terminus is that skill's output. Excluded from the loop by name, and this is the shape the fields are meant to be maintained in.
- **Rewriting the field across the corpus in one pass is a migration.** It is not a by-product of shaping any single intent; it is a change to many artifacts made for its own sake, which is the include list's own term. That puts it in the loop.

The rule's live consumer is slice 1. Its migration walks a set of intents through a status decision each, which is a corpus migration and therefore in-loop work under the same rule.

The 2026-09-23 population described in § Current-state evidence was also the second kind and ran as though it were the first. Its disposition is closed; what remains open is the standing obligation on the shaping skills, which the parent's § Unresolved questions owns.

Mode selection for the slices below is not made here. `work-loop` selects it at the change in hand.

## Candidate delivery slices

Enumerated, not confirmed — and the two are different acts. The candidates are listed because [ADR-0077](../../adr/0077-feature-projection-and-tracker-authority.md) D1 routes on how many independently shippable changes there are, so the count has to exist for this artifact to be the right one.

**If the confirmed cut is one slice, this brief is retired.** D2 permits a one-spec brief only as a repository projection of a cross-repository feature, and this feature is single-repository. The trigger is the **slice-cut confirmation**, where `author-delivery-brief continue` presents the proposed cut as a set and the lifecycle owner confirms it; a confirmed set of one retires the brief there and the feature routes directly to a spec under D1. The owner performs the retirement: the brief moves to a terminal collection through `close-work`, and the surviving slice goes to `new-spec` with this brief's scope as its context. The rule lives here rather than in § Ready gaps because that section is dropped on leaving `Draft` and this trigger fires after that.

"That the cut finished at one" is not itself observable — [ADR-0098](../../adr/0098-artifact-admission-and-delivery-brief-lifecycle.md) D6 confirms *a* slice at a time, so a brief can materialize one and stop, and no brief can yet declare its cut closed. The confirmation moment is what makes the count readable. The **cut** is made *after* the Ready transition, as a separate human confirmation — [ADR-0098](../../adr/0098-artifact-admission-and-delivery-brief-lifecycle.md) D5 makes Ready its own confirmation and D6 lets a Ready brief carry zero specs, so the cut cannot be a Ready precondition. Nothing here binds it.

The guide page named in § Scope is not a fourth slice.

1. **The transition contract, for both artifact kinds.** The state table and legal move set for an intent **and for a brief**, one vocabulary decided once. It does not carry the cut-closed criterion, which slice 3 adds. What the three declared fields mean for a transition, `Draft` narrowed to open, and the migration of the intents that reached `Fulfilled` without `Accepted`. It does **not** carry the supersession split. The parent handed that to [`intent-identity-and-registration`](intent-identity-and-registration.md)'s § Post-Ready decisions, which owns both the spec it touches and, under the parent's § Boundary, an intent preamble field's shape. This slice's state table consumes whichever supersession form has landed when the slice is specified. If the split has not landed by then, the `Superseded` row carries the shipped `Superseded by <slug>` form and the split arrives later as a separate change. There is no blocking edge between the two. Verification has to observe a transition, which is a pair of states, so a single-snapshot corpus scan cannot establish it on its own; how many surfaces that takes and where they sit is the spec's to decide.

   **Size.** The largest slice. Measured 2026-09-23 against the working tree. It extends `intent_corpus_lint.py` with a transition rule and walks ten intents through a status decision each. The nearest comparables carry heavy criteria sets — `intent-metadata-shape-contract` 27 acceptance criteria, `checkable-adr-metadata` 32 — and this slice is the same kind of work: a field-and-state contract with a blocking gate. Expect that order.

2. **The closure check in `close-work`.** Trigger, gather-at-decision-time, three-way classify, the evidence packet, the human decision point, and the closure record. The disposition lookup is optional and must handle an absent product-bet disposition; the parent's § Unresolved questions owns that decision. Depends on slice 1 for the meaning of terminal, and on `Decomposed:` for a ratified delivery set. **How it obtains child state is unsettled and is this brief's to settle, not the spec's.** Both forms are legal under the boundary § Non-goals draws: invoking [FEAT-0002](../intents/FEAT-0002-intent-graph-navigation.md)/[FEAT-0003](../intents/FEAT-0003-intent-delivery-traceability.md)'s walker fresh at decision time, or reading child `Status` from the artifacts itself. What neither may do is read a cached rollup, which § Constraints forbids, or stand up a durable graph surface, which § Non-goals excludes. Decide which before specifying the slice; if it is the walker, record the ordering edge on those two features. Recording either answer here is a change to this brief's delivery map, which `author-delivery-brief` treats as material — so it returns a `Ready` brief to `Draft` for a fresh review. The same cost applies to the CAP-0003 trace below. Settling both before Ready avoids it. It may also depend on [CAP-0003](../intents/CAP-0003-workspace-coordination-reorganization.md): that capability exists to stop repository coordination depending on `workspace.toml`, and whether any part of this check touches the registry is untraced. Trace it before specifying the slice; if it does, the two need ordering.

   **Size.** Middle, measured 2026-09-23. One workflow change inside `close-work`, no new artifact field, and verification by fixture tree rather than corpus migration. Smaller than slice 1 because it adds no contract other artifacts must satisfy.

3. **The brief cut-closed declaration.** The field saying no further slices are coming, its shape and preamble bounding, and `close-work`'s brief path reading it. It ships after slice 1 and extends the brief state table that slice delivers; how many criteria that takes is the spec's to decide. Independently shippable and testable on its own terms: slice 1's table is complete and verifiable without it, and this slice is verifiable by a brief closing on a declared cut and refusing without one.

   **Size.** The smallest. It is the third instance of a pattern that already exists twice — `intent-metadata-shape-contract` AC-0011 bounds an intent's preamble, `lint-spec-status.py` bounds a spec's, and nothing bounds a brief's. Investigate both before choosing which to mirror. One additive field across the brief corpus, one reader in `close-work`, and `lint-brief-coverage.py` to teach. Measured 2026-09-23. Core-pack only.

## Governance references

- [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md) — retired the Initiative ladder into the recursive intent graph, which created the closure gap this brief fills.
- [ADR-0077](../../adr/0077-feature-projection-and-tracker-authority.md) — D1 routes a feature by shippability: one independently shippable change becomes a spec, several become a brief. That is why this artifact is a brief. D2 sets the one-spec floor that a single-slice cut would breach, which § Candidate delivery slices carries along with its trigger. D1 is superseded in part by ADR-0098, whose Clause-level replacements carry what moved: the feature-projection table is refined so sufficient direct artifact authority may bypass feature-intent *creation*. The shippability routing is untouched and D2 is not superseded.
- [ADR-0098](../../adr/0098-artifact-admission-and-delivery-brief-lifecycle.md) — the record that most constrains this brief. D5 makes the Ready transition its own human confirmation. D6 lets a Ready brief carry zero specs and makes selecting and materializing a slice a separate confirmation, which is why the cut sits after Ready and why the Spec map is empty here. D7 separates governance references from delivery slices, so only specs enter a rollup. It is superseded in part by ADR-0121, which replaces its D3 and reaches none of these three.
- [ADR-0121](../../adr/0121-a-repository-intent-declares-its-altitude.md) — D1 requires `Level` on a repository intent and replaces ADR-0098 D3's grouping of `level` with optional enrichment. It closes the supersession chain above: both ADR-0077 holdings this brief relies on are live.

## Spec map

One of three slices materialized. The Status column is auto-derived from each spec; it is not hand-edited.

| Spec | Status |
| --- | --- |
| `lifecycle-transition-contract` | <auto> |
