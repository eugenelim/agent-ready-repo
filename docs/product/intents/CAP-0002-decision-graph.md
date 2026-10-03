# Decision graph

- **Slug:** `decision-graph` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Accepted
- **Accepted:** 2026-10-03 owner ratification
- **Level:** capability
- **Owner:** Platform Core maintainer
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** opportunity:graph-powered-sdlc
- **De-risked:** 2026-10-03
- **Decomposed:** 2026-10-03 children

## Outcome

- **Steerable input:** Increase the share of human and agent work that checks attributable decision context before making a new decision or materially changing behavior.
- **Lagging outcome:** Humans and agents make future decisions with the accepted ADR and RFC corpus in view, can explain which records informed the choice, and can extend, refine, or supersede that corpus through its existing lifecycle when conditions change.
- **Guardrail:** The decision graph is a reference-policy surface, not a policy compiler. Canonical records carry authority; checked graph facts carry identity, lifecycle, and lineage. A view or context result never infers binding rules, claims complete applicability, turns an unknown into permission, or enforces behavior by itself.

## Opportunity

- **Functional job:** Find the standing decisions and rationale that may constrain or inform the work in front of me, understand how they relate, and check my proposed action against them before deciding.
- **Emotional job:** Trust that the context comes from canonical records, distinguishes checked facts from weaker references, and states what it may have missed.
- **Social job:** Show people and agents which prior decisions informed a choice without pretending that retrieval replaced judgment or governance.
- **Struggling moment:** Decisions are passive files. People reconstruct lineage and scope by hand, agents may never retrieve the relevant records, and list-only views hide how broad decisions, narrower guidance, and later supersession relate.

## Boundary

Inherits the parent's outcome, boundary, and exclusions. Within them, this child owns:

- the accepted ADR and RFC population as a reference-policy graph for humans and agents, preserving canonical identity, lifecycle, rationale, provenance, and checked lineage;
- multiple read-only projections over that population, including a corpus list, lifecycle and supersession navigation, scoped-guidance context, and focused record detail;
- visible trust classes for relationships: checked lifecycle or supersession facts remain distinct from explicit but unchecked references, search groupings, and absent relationships;
- bounded decision-context results that name their anchors, sources, search boundary, checked lineage, unresolved references, conflicts, and unknowns;
- human and agent use of that context as an explicit check during planning, implementation, review, or decision authoring;
- traceable observations that may inform an authorized future ADR or RFC without changing the graph automatically.

The list, graph, and scoped-guidance forms are rendering views over the same canonical records. They do not require a new core record shape. A view may arrange broader and narrower guidance only when an admitted directional fact or an explicit caller assertion supplies that direction. Otherwise scope similarity, search results, and contextual references remain a neutral grouping. Every relationship preserves whether it is checked, contextual, caller-supplied, grouped for navigation, or unresolved. A view must not promote `Related`, scope prose, filenames, proximity, or model interpretation into authoritative lineage or parentage.

It does not own the intent corpus or its identity (`intent-identity-and-registration`), the intent graph (`intent-graph-navigation`), the intent-to-delivery mapping (`intent-delivery-traceability`), workspace coordination (`workspace-coordination-reorganization`), or tracker projection (`external-tracker-projection`).

Explicitly out of scope:

- **Policy compilation or automatic applicability resolution.** The capability supplies attributable context; it does not convert record prose into executable rules or determine the complete policy governing an action.
- **Autonomous policy authorship or self-modification.** An agent may surface evidence and propose a change, but only the governing ADR or RFC lifecycle may accept, amend, supersede, or retire a decision.
- **A required policy-metadata schema.** The capability does not require every record to declare force, selectors, precedence, escalation, or rule-level rows.
- **Persisting a generated index.** Views derive on demand from canonical records. Disposable query results and HTML are not repository state.
- **Treating precedent as authority.** Prior actions and outcomes may inform evolution, but they do not amend an accepted record.
- **A hosted or cross-repository decision store.** This capability covers one repository and its file-backed records.

## Owner

- Platform Core maintainer. Accountable for this intent's outcome.

## Unresolved questions

- At which decision points does a lightweight context check provide enough value to justify making it an expected workflow step.
- How agents report the records checked, the search boundary, and unresolved conflicts without adding noisy ceremony to ordinary maintenance.
- Which existing record facts can support useful wider-to-narrower guidance views without implying a checked relationship the corpus does not carry.
- When outcome or exception evidence is valuable enough to justify a separate decision-evolution feature.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Grounding

Four checked facts bound the architecture:

- **Supersession is a trustworthy graph backbone.** `lint-adr-shape.py` verifies referenced decision identifiers and reciprocal full or partial supersession metadata, so those edges can be shown as checked lineage.
- **`Related` is useful context but not checked lineage.** The linter recognizes the field without validating its values or endpoints. A view may display it as unresolved or contextual evidence, but not as an authoritative edge.
- **Applicability is not machine-resolvable, and this capability does not require it to be.** `Applies to:` is optional prose and RFCs have no equivalent checked selector. Bounded retrieval can still expose candidate context as long as it states its boundary and does not claim completeness.
- **Generated views are the compatible shape.** ADR-0112 requires a document-corpus index to be generated or absent and fixes the existing flat index's columns. A separate disposable list or graph view can add navigation without changing that canonical index.

## Research

[Graph-powered SDLC — applied survey](../research/graph-powered-sdlc-survey.md) supports the trust boundary: checked supersession can carry lineage, while unvalidated `Related` text cannot. It also identifies negative decisions as useful context when their record and conditions are explicit. This capability uses those findings for reference and navigation; it does not turn them into a policy language.

## Assumptions

- People and agents can make better future decisions from a bounded, attributable context result even when relevance still requires judgment. **Supported by the pressure test below; representative use remains `to-validate`.**
- Multiple views over one corpus make different questions easier without creating competing truth: lists support orientation, lifecycle graphs support change history, scoped-guidance views support wider-to-narrower reading, and detail views preserve rationale. **Supported as an architecture shape; interaction value remains `to-validate`.**
- A context check can remain lightweight enough that maintenance does not trigger unnecessary ADR or RFC work. **Supported by the maintainer-reviewed maintenance cases below.**
- Agents can cite consulted decisions and disclose unknowns without treating a retrieved set as complete governing policy. **Untested in representative delivery work.**
- **Knowledge surface:** in-repo decision corpus, governance records, lint contracts, and accepted intent/spec artifacts (`docs/adr/`, `docs/rfc/`, `docs/product/intents/`, and `docs/specs/`).

**De-risked at the capability level for the lightweight reference-context model.** The earlier policy-compilation branch was killed and remains recorded below. Representative human-and-agent value and workflow fit remain validation hooks on the child features rather than blockers to decomposition.

## Reference-context de-risk record

- **Status:** survived on 2026-10-03; representative workflow value remains `to-validate`
- **Reversibility triage:** two-way door. Read-only context retrieval and disposable views can be withdrawn without changing canonical records or enforcement gates.
- **Prototype approach:** `validate-first`. Pressure-test the behavior against maintenance, conflict, missing-context, and mixed-trust scenarios before designing runtime machinery.

### Riskiest assumption

A checked reference graph can guide future decisions without a machine-resolvable applicability layer, mandatory policy metadata, or an enforcement engine.

What would have to be true: the result must keep canonical authority and provenance visible; distinguish checked lineage from contextual references; disclose its query boundary; leave applicability judgment with the actor; and avoid turning routine maintenance into decision ceremony.

### Kill condition, predeclared 2026-10-03

Kill the lightweight model or narrow it to navigation only if any pressure-test case requires the graph to invent applicability, select a winner between conflicting accepted records, treat a missing result as permission, promote an unchecked reference to lineage, or require a new ADR when the maintainer confirms no durable contract or policy changed.

### Probe

The paper probe used four classes of case:

1. three maintainer-reviewed changes where the operation remained maintenance and did not change a durable contract;
2. a potentially breaking change where the graph must surface the governing record but the actor and existing authoring workflow decide whether a new ADR is required;
3. conflicting or missing decision context where the result must report uncertainty rather than resolve or permit; and
4. list, supersession, and wider-to-narrower guidance views over the same record population, with checked and contextual relationships kept visually distinct.

The lightweight model handled each case without an applicability schema. Maintenance stayed maintenance. A potentially breaking change received cited context rather than an automatic ADR verdict. Conflict and absence remained explicit. Multiple views reused the same records and trust labels rather than adding a second graph contract.

### Verdict — survived with an honest boundary

No kill condition fired. The capability may proceed as a checked reference-policy surface with bounded context checks. It must not claim to identify all applicable policy or enforce compliance, and its first child implementations must test whether people and agents understand that boundary.

### Validation hook

```yaml
validation_hook:
  assumption: Bounded checked decision context improves future human and agent decisions without creating false completeness or excess ceremony.
  kill_condition: A representative run treats a missing result as permission, promotes an unchecked relation to authority, opens decision work for unchanged maintenance, or cannot cite the records and boundary it used.
  activity: to-validate — compare representative planning and review tasks with repository search, recording decision citations, missed context, false authority, and unnecessary governance work.
```

## Killed policy-compilation branch

- **Status:** killed on 2026-10-02
- **Assumption tested:** Existing ADRs and RFCs carry enough explicit applicability, behavioral force, precedence, and escalation metadata for a derived overlay to govern behavior without interpreting prose.
- **Probe:** A fixed ten-record packet—ADR-0129 through ADR-0133 and RFC-0101 through RFC-0105—was compiled against `scope selector + force + rule reference + precedence + escalation`.
- **Result:** Fewer than eight records could populate the tuple without inventing facts. RFCs had no common checked applicability, force, or escalation fields; missing values would not reliably fail closed. Checked partial supersession remained useful only for lineage.
- **Consequence:** Do not add a policy contract merely to rescue this model. The capability now supplies reference context and leaves applicability and behavioral judgment with humans and agents under their existing workflow authority.

This record is retained because it explains why the capability does not evolve into a policy resolver by accident.

## Navigation-slice de-risk record

- **Status:** survived on 2026-10-02 for deterministic corpus tasks; representative human-and-agent value remains `to-validate`
- **Probe result:** Ten of ten sampled ADR and RFC records were discoverable; every sampled checked lineage endpoint resolved; and ten of ten identity, lifecycle, lineage, and rationale questions were answerable from header facts plus an explicit body or source action. No `Related` text or body prose was promoted into a checked edge.
- **Boundary:** The result proves corpus sufficiency and honest navigation. It does not prove that a retrieved set is complete policy for an action.

```yaml
validation_hook:
  assumption: Humans and agents will use read-only decision navigation before a context-check workflow is integrated.
  kill_condition: Fewer than four of five representative runs complete lineage and constraint tasks unaided, or any run treats unresolved evidence as checked lineage or a lookup result as complete governing policy.
  activity: to-validate — compare navigate-decisions with repository search across status, lineage, rationale, scope, and source-handoff tasks.
```

## Decomposition

- [Decision navigation](FEAT-0029-decision-navigation.md) — list, lifecycle graph, scoped-guidance context, record detail, bounded agent queries, and a portable single-file human view over the ADR and RFC corpus.
- [Decision context checks](FEAT-0031-decision-context-checks.md) — lightweight use of bounded decision context during human and agent planning, implementation, review, and future decision authoring, with citations and explicit uncertainty rather than policy resolution.
- **Decision evolution evidence — not yet admitted as a child.** Conflicts, exceptions, and outcomes may later justify a distinct feature, but the current evidence does not show that it needs machinery beyond cited input to normal ADR and RFC authoring.

### Decomposition decisions

- **Views are one navigation outcome.** List, lifecycle graph, guidance context, and record detail are projections over the same corpus, not separate skills or core schemas.
- **Navigation and use remain separate.** FEAT-0029 makes the graph legible and queryable. FEAT-0031 owns when and how work checks that context.
- **No policy resolver sits between them.** Context checks consume bounded navigation results and leave judgment with the actor.
- **Authoring remains outside both children.** `new-adr` and `new-rfc` retain their separate admission and authoring contracts.
- **Evolution remains evidence-led and authorized.** Observations may inform a new or superseding record but cannot mutate the graph.
- **Implementation architecture is not an intent child.** Renderer, query, component, storage, and layout choices remain with implementation teams under accepted contracts.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** Platform Core lifecycle owner

Authored under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph. Reshaped on 2026-10-03 after the policy-compilation branch failed: the graph now supplies checked reference context to humans and agents rather than resolving or enforcing policy.
