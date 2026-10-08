# Decision context checks

- **Slug:** `decision-context-checks` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Draft
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

## Source

- **Mode:** repo-origin
- **Locator:** `docs/product/intents/CAP-0002-decision-graph.md`
- **Authority:** Platform Core lifecycle owner

Created from the approved 2026-10-03 capability reshape. It separates use of decision context from the navigation surface that supplies it.
