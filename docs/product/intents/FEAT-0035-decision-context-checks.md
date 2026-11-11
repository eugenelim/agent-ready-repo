# Decision context checks

- **Slug:** `decision-context-checks` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** Platform Core maintainer
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:decision-graph

## Outcome

- **Steerable input:** Increase the share of material human and agent decisions that consult a bounded, attributable slice of the decision graph before the choice is made.
- **Lagging outcome:** Plans, reviews, implementations, and new decision records cite the prior decisions that informed them, disclose unresolved or missing context, and avoid both silent drift and unnecessary governance work.
- **Guardrail:** A context check supplies references for judgment. It never claims complete applicability, compiles record prose into rules, treats absence as permission, selects between conflicting accepted records, or opens an ADR or RFC merely because maintenance touched a decision-governed area.

## Opportunity

- **Functional job:** Before I make a material choice, give me the smallest useful set of canonical decisions and checked lineage to consider, then let me show what I consulted and what remained uncertain.
- **Emotional job:** Feel confident that I did not overlook an obvious standing decision while remaining free to apply judgment to the actual situation.
- **Social job:** Give reviewers and future authors a short, attributable account of which decisions shaped the work.
- **Struggling moment:** Navigation can expose the corpus, but a person or agent still has to remember when to consult it and how to communicate an incomplete or conflicting result honestly.

## Boundary

Inherits the parent capability's authority and trust boundaries. This child owns:

- lightweight context checks at selected planning, implementation, review, and decision-authoring moments;
- explicit anchors such as record identifiers, repository areas, changed surfaces, or a named decision question;
- a bounded result containing cited records, checked lifecycle or supersession, contextual references, conflicts, unknowns, and the search boundary;
- a compact receipt when a workflow needs proof of what was consulted.

It does not own decision navigation rendering, ADR or RFC authoring, automatic applicability, rule extraction, behavioral enforcement, or a universal gate on every task. It adds no required ADR/RFC metadata shape.

## Owner

- Platform Core maintainer. Accountable for this intent's outcome.

## Unresolved questions

- Which workflow moments merit an expected context check and which would create more ceremony than value.
- Which anchors yield useful context without implying exhaustive applicability.
- What the smallest useful receipt contains for humans and agents.

## Projection

Not yet selected.

## Assumptions

- **Riskiest assumption:** Selected workflow checks improve material decisions more than ordinary repository search without burdening maintenance. This remains `to-validate` through the comparison hook below.
- Actors can distinguish candidate decision context from complete governing policy when the result states its boundary.
- A compact receipt can improve reviewability without becoming mandatory narrative history.

**Not yet de-risked.** The parent pressure test established that the lightweight model is coherent. This child still needs representative workflow comparisons to find the useful check points and ceremony limit before decomposition into delivery work.

```yaml
validation_hook:
  assumption: Lightweight decision-context checks improve material work without burdening maintenance.
  kill_condition: Representative runs do not find relevant context more reliably than repository search, treat results as complete policy, or create ADR/RFC work for unchanged contracts.
  activity: to-validate — compare planning and review tasks at candidate check points, measuring relevant citations, misses, false authority, and unnecessary governance work.
```

## Readiness

- **Route:** not ready. It needs a replay spike first, then probably a new-spec.
- **Verified current truth (2026-11-05):** `navigate_decisions.py` already has an operation `context` (scoped guidance by identity) and a `search` operation with a `text` selector. What does not exist is a check that takes a work anchor and returns a bounded result with a receipt.
- **Replay protocol (run once, offline, repeatable):** take 20 shipped specs that name two or more ADR or RFC records in `Constrained by:`. The cited records are the answer key. The anchor is the spec title words. Compare recall at 10 for `navigate_decisions.py query --operation search` against a plain count of the same words across `docs/adr` and `docs/rfc`. Count false authority and ceremony by hand on a smaller sample.
- **First result, 2026-11-05 (title-word anchors, 20 random specs, 70 cited records):** navigation found 26 and plain search found 29. That is no lift, which is the kill condition in the validation hook. It does not test explicit anchors (record ids, areas, changed paths), which this intent proposes.
- **Next step:** rerun the protocol with explicit anchors taken from each spec's changed paths and the repository areas it names. If that still shows no lift over search, drop this intent and close `CAP-0002`. If it shows lift, write a spec for one `check` operation and a receipt.
- **Unresolved question answered:** expect a check at spec authoring and at decision authoring only. A review-time check adds ceremony before any lift is shown.

## De-risk result

- **Date:** 2026-11-05. **Ran:** a replay over 20 random shipped specs that name two or more ADR or RFC records in `Constrained by:` (70 cited records, the answer key). The anchor was the spec title words. I compared recall at 10 for `navigate_decisions.py query --operation search` against a plain word count over `docs/adr` and `docs/rfc`. Script: `.context/graph-replay.py` (not committed).
- **Observed:** navigation found 26 of 70 and plain search found 29 of 70. No lift.
- **Verdict:** the assumption is not supported on title-word anchors, and that is the kill condition's first half, so `De-risked` is not set. Explicit anchors (changed paths, areas) are untested. Rerun with them before any spec. If they also show no lift, withdraw this intent and close `CAP-0002`.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/product/intents/CAP-0002-decision-graph.md`
- **Authority:** Platform Core lifecycle owner

Created from the approved 2026-10-03 capability reshape. It separates use of decision context from the navigation surface that supplies it.
