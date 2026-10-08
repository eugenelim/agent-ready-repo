# Intent-to-delivery traceability

- **Slug:** `intent-delivery-traceability` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Accepted
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:repository-work-graph
- **De-risked:** 2026-10-03
- **Shaping-reviewed:** 2026-10-03
- **Decomposed:** 2026-10-03 spec

## Outcome

- **Steerable input:** Increase the share of feature intents whose ratified delivery route resolves from canonical preamble fields alone, and the share of delivering artifacts whose intent relations are returned with their distinct basis instead of collapsed into one parent.
- **Lagging outcome:** From an intent, product engineers and delivery agents can find the durable spec that directly delivers it or its coordinating brief and child specs. From a spec, they can see every typed intent relation it carries — direct delivery, coordinated delivery, or other provenance — without mistaking several valid relations for one ambiguous parent. When the ratified terminus is `direct-light` or `closed-empty`, the intent visibly states that no durable delivery child exists rather than presenting an unexplained gap.
- **Guardrail:** ADR-0077's projection rule is preserved — a feature projects by shippability and coordination need, so a one-spec brief stays permitted only as a repository projection of cross-repository work. Status and coverage keep their existing single homes; relation type never invents ownership, priority, or lifecycle state; existing briefs, specs, and registered memberships keep their meaning; and no session-local direct-light run is turned into persisted workspace work.

## Opportunity

- **Functional job:** Follow a shaped outcome down to the durable change that delivers it, and follow a change back through each declared intent relation without flattening delivery, coordination, and provenance into one parent; when there is deliberately no durable child, distinguish that decision from missing traceability.
- **Emotional job:** Be confident that shaped work has a delivery home, and that an intent with no downstream artifact is visibly unstarted rather than silently lost.
- **Social job:** Show a maintainer or a reviewer that a change is authorized by a shaped outcome, and show an outcome's owner where it stands in delivery.
- **Struggling moment:** Two production readers still build parts of the answer independently. `Decomposed:` records a ratified terminus; `lint-traceability.py` treats `Discovery:`, `Brief:`, and `Parent intent:` as alternative spec producers and selects one; and `close-work` follows both the direct discovery route and the brief route when both exist. A spec can legitimately carry more than one kind of upstream provenance, so the readers disagree precisely where a single-parent abstraction is weakest. Until the delivery slice replaces those private paths, a reader must know which consumer to imitate and must still reconstruct whether an absent child means legacy drift, `direct-light`, or `closed-empty`.

## Boundary

Inherits the parent's outcome, boundary, and exclusions. Within them, this child owns:

- the **typed delivery relations readable from the spec itself**: a direct spec reaches the feature it delivers through `Discovery:` when that value resolves to an intent whose ratified terminus is `spec`; a coordinated spec reaches the feature through `Brief:` and that brief's `Parent intent:` when the feature's ratified terminus is `brief`. Other declared provenance remains visible under its own basis rather than competing to become the one parent. These relations supply the bottom step of the capability's fulfilment rollup without asserting that every upstream reference is the same kind of edge;
- the visible mapping from a feature intent whose ratified terminus is `spec` to the independently shippable spec that delivers it;
- the visible mapping from a feature intent whose ratified terminus is `brief` to a delivery brief and its child specs when coordination requires that shape;
- the visible distinction between those durable routes, an incomplete or contradictory legacy mapping, and the deliberate no-durable-child termini `direct-light` and `closed-empty`;
- the coherence rule between the ratified `Decomposed:` terminus and the descendants found by reversing only the up-edge admitted for that route, including a fail-closed answer when a relation is missing or contradictory within its type;
- the rule that several typed relations may coexist on one spec, while two incompatible targets for the same delivery-relation type refuse rather than resolve by field order;
- how the projection choice is recorded and read consistently with ADR-0077 D1 and D2.

It does not own identity or placement (`intent-identity-and-registration`), parent-to-child-intent edges or the graph view that displays the mapping (`intent-graph-navigation`), operational coordination state (`workspace-coordination-reorganization`), or tracker rendering (`external-tracker-projection`). It does not own status, brief coverage, closure decisions, spec or brief authoring, or the direct-light execution record. It does not turn a contextual provenance edge into delivery ownership merely because both endpoints are local. It does not change the delivery loop. Existing fields and consumers are evidence that the outcome may be feasible, not a mechanism decision at this altitude; the delivery slice must implement one canonical typed read model and leave no second edge-inversion implementation beside it.


**Inbound 2026-09-24 — a second consumer already builds part of this graph.** [FEAT-0005](FEAT-0005-lifecycle-and-closure.md) § Boundary was amended while this intent was still Draft and undecomposed because its closure check could not wait. That child may build an **in-memory descendant set** by inverting declared up-edges, bounded by three conditions that FEAT-0005 states and owns. They are not reproduced here because a copy would drift. Persistence, publication, and any surface a second consumer reads remain this intent's, and **no ordering edge runs in either direction**. The delivery slice treats that per-decision resolver as a consumer to absorb rather than a rival implementation to preserve.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Delivery handoff

- The [delivery spec](../../specs/intent-delivery-traceability/spec.md) owns behavior, refusal semantics, security bounds, and the diagnostic vocabulary.
- Its [implementation plan](../../specs/intent-delivery-traceability/plan.md) owns the Core adapter-root resolver, consumer convergence, construction order, and verification placement.
- Product validation remains the three-maintainer walkthrough in the validation hook below; it is not an implementation acceptance criterion.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Assumptions

- Treating all producer pointers as alternatives for one parent can yield one coherent bidirectional mapping. **Killed by the first 2026-10-03 de-risk probe below; retained as a constraint against regression, not as an open assumption.**
- **Riskiest assumption:** The intent's ratified route and existing canonical preamble fields contain enough role information to derive a deterministic set of typed delivery relations from either end, without copying status or brief coverage or adding a new durable delivery record. **Survived the second 2026-10-03 probe below.**
- A ratified `Decomposed:` terminus can be checked against reversed producer edges strongly enough to distinguish missing, ambiguous, contradictory, and deliberate-empty outcomes. **Supported by the route matrix and corpus classifications below.**
- The corpus can adopt the mapping incrementally: an unmapped legacy intent remains valid but visibly unresolved, while a ratified mapping that contradicts its descendants fails closed. **Supported by eight missing and one overpopulated direct-spec mappings that the header-only probe distinguishes.**
- One shared read model can absorb `close-work`'s existing per-decision resolver without widening this intent into lifecycle or graph-view ownership. **The implementation plan bounds the remaining proof: failure to import the confinement helper or isolate either consumer seam requires a plan amendment rather than a second resolver.**
- **Knowledge surface:** the in-repository decision, product, skill, code, and test corpus on `main` at `afcc1eeb8b9111bb44d90d37fb37ee468a93c260`, plus attributed read-only evidence from the unlanded `adr-summary` worktree. No separate MCP knowledge surface or internal knowledge CLI was available. The accepted decisions, production readers, and their construction tests corroborate the current-landscape claims; no user study establishes desirability. Pending RFC-0105 is conditional evidence only until it lands.

## First de-risk record — killed as framed, 2026-10-03

- **Level kind:** feature, but the dominant unknown is architectural rather than desirability. The parent capability already names the bottom delivery edge as necessary, and `close-work` already consumes one privately. The risky question is whether one coherent contract can represent the feature's four delivery outcomes without creating a second status or coverage authority. Human usefulness remains unvalidated; a surviving reframe must still carry a validation hook rather than treat demand as established.
- **Reversibility triage:** one-way door. A read-only probe is cheap to discard, but field semantics shared by authoring skills, traceability, closure, and a migrated corpus would be expensive to unwind once published.
- **Prototype-approach:** `validate-first`. The cheapest probe that can fail is a contract-and-corpus walk over current `main`; no implementation is needed to decide whether the four outcomes are representable and coherent.

### Riskiest assumption

The existing preamble contracts can represent a feature's direct-spec route, brief-to-spec route, `direct-light` terminus, and `closed-empty` terminus as one coherent mapping without copying status or brief coverage into the intent.

What would have to be true: `Decomposed:` must distinguish the selected route; current producer pointers must resolve both durable routes back to exactly one feature intent; deliberate no-child termini must remain distinct from missing traceability; ambiguity and a terminus/descendant mismatch must refuse rather than guess; and an intent with no ratified terminus must remain a visible legacy case rather than becoming invalid by inference.

### Kill condition, predeclared

There is no traffic metric for an internal repository contract, so the bar is qualitative. **Kill the current boundary if any one of the four supported feature delivery outcomes — `spec`, `brief`, `direct-light`, or `closed-empty` — cannot be classified from existing canonical preamble fields without reading artifact bodies, copying status or brief coverage, or inventing a new durable delivery record. Also kill it if any accepted production consumer can resolve the same descendant to two different feature parents without refusing. One failing outcome or one plausible split-parent result is enough.**

This line was written into the intent before the prototype below was run. `children` is outside this test because parent-to-child-intent navigation belongs to `intent-graph-navigation`; this feature owns the leaf projection into delivery.

### Prototype results

The read-only contract-and-corpus probe found:

- The 2026-10-03 intent corpus snapshot contains 128 feature intents. Sixteen declare a `spec` terminus, five declare `brief`, one declares `children`, three declare `Decomposed: no`, and 103 have no `Decomposed:` field. No feature intent in that snapshot exercises `direct-light` or `closed-empty`.
- Eight of the 16 `spec` feature intents already resolve to a spec through its preamble `Discovery:` pointer. The other eight remain visibly unresolved; the contract can distinguish that legacy gap from a deliberate empty terminus without reading a body.
- All five `brief` feature intents resolve to their coordinating brief through the brief's `Parent intent:` field. Twenty-one specs then resolve to those briefs through their `Brief:` fields.
- `direct-light` and `closed-empty` are distinct canonical `Decomposed:` values. They are representable without a durable child, but the corpus contains no feature-level instance of either route, so this is contract evidence rather than exercised adoption evidence.
- The split-parent stop rule fired. `lint-traceability.py` treats `Contract:`, `Discovery:`, `Brief:`, and `Parent intent:` as alternative producer pointers and chooses one resolving candidate. `close-work` independently follows both a spec's intent-valued `Discovery:` pointer and its brief's intent-valued `Parent intent:` pointer. Those fields can legally name different feature intents, and neither consumer refuses that case. The repository already contains specs with both `Discovery:` and `Brief:` populated, so this is a plausible corpus shape rather than a purely theoretical syntax combination.

### Verdict — killed as framed

The predeclared kill condition was met. At this point in the sequence, the boundary's promise of one coherent bidirectional mapping over all existing producer pointers did not survive, so the intent was not yet de-risked or ready for decomposition.

The probe narrowed the problem: a downward lookup that starts from an intent can be route-qualified by its `Decomposed:` terminus — direct specs through `Discovery:`, coordinated specs through `Parent intent:` on the brief and `Brief:` on each spec, and no descendant for the two explicit empty termini. The unsafe part is treating all producer pointers as interchangeable evidence for one upward parent. The route-qualified reframe and its fresh probe appear below.

## Reframe and second de-risk — 2026-10-03

The owner decision after the cold shaping and adversarial reads is to retain upward traceability as a set of typed relations. Narrowing the feature to downward lookup alone would leave the parent capability's bottom edge unanswered. The reframe instead drops the assumption that a spec has one interchangeable intent parent: the intent's ratified route selects the fulfilment relation, while other declared pointers remain separately based provenance.

- **Reversibility triage:** one-way door. Relation semantics would become a shared contract for authoring, navigation, traceability, and closure consumers.
- **Prototype-approach:** `validate-first`. A header-only relation matrix and corpus walk can disprove the reframe before any implementation or migration is chosen.

### Riskiest assumption

The intent's ratified route and existing canonical preamble fields contain enough role information to derive a deterministic set of typed delivery relations from either end, without copying status or brief coverage or adding a new durable delivery record.

What would have to be true: each of `spec`, `brief`, `direct-light`, and `closed-empty` must select exactly one route meaning; direct and coordinated delivery must remain distinguishable when both `Discovery:` and `Brief:` are present; a reader must preserve rather than discard other provenance; missing legacy data must remain distinguishable from a same-type contradiction; and the parent capability and declared consumers must be able to consume the typed result without inferring a second authority.

### Kill condition, predeclared before the second probe

**Kill this reframe if any supported terminus cannot be classified from canonical headers alone; if a valid current or constructed corpus case yields two incompatible targets for the same delivery-relation type without a refusal; if preserving the upward walk still requires treating `Discovery:` and `Brief:` as interchangeable candidates; or if the parent capability or a declared consumer requires one unique intent parent rather than a typed relation set. One failing case is enough.**

### Prototype

The second probe built a route-to-edge matrix from accepted contracts, walked every feature intent decomposed in the 2026-10-03 snapshot and every spec carrying both `Discovery:` and `Brief:`, and tested the dual-provenance case against the parent capability, `close-work`, traceability, and the conditional RFC-0105 consumer boundary. It classified missing legacy data separately from same-type ambiguity and did not treat the first probe's observations as a new result until this narrower stop rule was applied.

### Prototype results

The route-to-edge matrix is deterministic from headers:

- `spec` admits the direct-delivery relation by resolving the spec's `Discovery:` value to the feature intent. A conforming `spec` route has exactly one matching spec; none is a visible missing mapping and more than one is a projection mismatch that refuses. The existing value may be a repository path or the typed `intent:<slug>` form; normalization changes no durable record.
- `brief` admits the coordinated-delivery relation by inverting a brief's `Parent intent:` and then each spec's `Brief:`. Several specs are valid beneath this route because the brief is the coordination boundary.
- `direct-light` and `closed-empty` are explicit no-durable-child termini. They admit no delivery child, so they cannot be mistaken for a missing `spec` or `brief` mapping.
- Other resolving pointers remain separately based provenance. Two relation types may name the same or different intents; only incompatible targets within one relation type are ambiguous.

The 2026-10-03 corpus snapshot exercises the matrix as follows:

- Sixteen feature intents declare `Decomposed: ... spec`. Seven resolve to exactly one spec, eight resolve to none and remain visibly missing, and `cut-before-adding-solution-ladder` resolves to six specs and is therefore a visible ADR-0077 projection mismatch rather than a guessed parent.
- Five feature intents declare `Decomposed: ... brief`. All five resolve to exactly one coordinating brief, and those briefs have 21 child specs through canonical `Brief:` pointers.
- Twelve specs populate both `Discovery:` and `Brief:`. Nine carry direct and coordinated routes that converge on the same feature intent. The other three have a brief with no feature parent or a `Discovery:` value that is research rather than an intent. Every case is classifiable without reading an artifact body. A constructed case whose two routes name different feature intents still returns two typed relations; it does not produce two candidates for one relation.
- No spec currently carries a `Parent intent:` preamble field, while every current direct feature mapping is carried by `Discovery:`. One uses the typed `intent:<slug>` value and the rest use admitted legacy path forms, so the durable contract can normalize the target without inventing a record.
- The parent capability requires the spec-to-feature bottom edge but does not require that every upstream reference collapse to one unique parent. `close-work` already returns a set of intent ancestors and derives descendants by the ratified terminus. Pending RFC-0105, if it lands, requires `navigate-intents` to consume this feature's mapping without inferring it and to preserve relationship basis and trust class. Both consumers fit a typed relation set.

### Verdict — survived after reframe

The second probe did not meet its predeclared kill condition. All four termini are classifiable from canonical headers, same-type multiplicity is detectable and can refuse, the upward walk preserves rather than arbitrates between `Discovery:` and `Brief:`, and neither the parent nor the declared consumers require one unique intent parent. The architectural bet **survived** and supports the decomposition below.

This verdict does not bless the current corpus as complete. Eight missing direct mappings, the six-spec projection mismatch, value-form normalization, and convergence of `close-work` with the eventual shared read model are decomposition inputs. Human usefulness is desk-grounded by the parent capability and existing consumers, not validated.

```yaml
validation_hook:
  assumption: Maintainers can use a route-qualified, typed relation result from either end without reopening artifact bodies or mistaking contextual provenance for feature fulfilment.
  kill_condition: In a four-case walkthrough covering direct, coordinated, deliberate-empty, and dual-provenance routes, stop if any of three maintainers opens an artifact body to classify a relation, chooses the wrong feature relation, or reports one unqualified parent for the dual-provenance case.
  activity: to-validate — give three maintainers header-derived results for the four cases and record their answers and any additional artifact they open; proceed only if all three classify all four cases correctly without opening a body.
```

## Decomposition

**One slice, [`intent-delivery-traceability`](../../specs/intent-delivery-traceability/spec.md)**, materialized directly as a spec rather than through a delivery brief. This is one independently shippable repository feature: derive one route-qualified relation set, expose its classifications and refusals, and converge the existing consumers on that answer.

### Why one and not several

Three cuts were considered and dropped:

- **Shared resolver first, consumer convergence second.** Rejected as a layer cut. A resolver that no workflow or query consumes changes nothing for a maintainer; adapting consumers independently before the shared answer exists preserves the duplicate implementations this intent removes.
- **Direct delivery first, coordinated delivery second.** Rejected because the feature's distinguishing case is a spec carrying both `Discovery:` and `Brief:`. Either half alone would still force an upward reader to flatten or ignore one route, so neither ships the stated outcome independently.
- **Corpus repair as a separate slice.** Not cut here. The delivery unit must classify the eight missing direct mappings and refuse the six-spec projection mismatch, but it must not invent delivery ownership or rewrite historical artifacts. A later repair is admitted only where the owning artifact supplies the missing fact.

The pending `navigate-intents` consumer is not a slice of this feature. If RFC-0105 lands, that sibling surface consumes the accepted mapping; FEAT-0003 supplies the contract and does not absorb the navigator. No ranking step applies because there is one delivery unit. No tracker projection is added; the existing Projection section remains unselected because no target is configured.

### Delivery contract

This shaping handoff is retained as provenance. The [delivery spec](../../specs/intent-delivery-traceability/spec.md) now owns the behavioral contract, and the [implementation plan](../../specs/intent-delivery-traceability/plan.md) owns construction and verification; this section is no longer delivery authority.

- **Outcome:** A maintainer or agent can start from a feature intent and find its direct spec, coordinating brief and child specs, or explicit no-child terminus; starting from a spec returns every intent relation with its route and basis preserved. Missing, contradictory, and multi-provenance cases are explicit rather than settled by field order.
- **Success signals:** All four ratified termini classify from canonical headers without reading bodies. A `spec` route resolves exactly one direct spec or returns a named missing/mismatch refusal. A `brief` route resolves exactly one coordinating brief and its specs. A spec with both routes returns both typed relations. The closure and traceability consumers obtain the same relation set, and no second edge-inversion implementation remains on their active paths.
- **Boundaries:** Read canonical preamble fields only. Normalize admitted `Discovery:` intent targets without changing their durable values. Select direct delivery through intent-valued `Discovery:` plus `Decomposed: ... spec`; select coordinated delivery through `Brief:` to the brief's `Parent intent:` plus `Decomposed: ... brief`; treat `direct-light` and `closed-empty` as successful no-child classifications. Preserve each relation's basis and refuse incompatible targets within one type. Keep all filesystem reads confined under the repository's existing file-safety contract.
- **Non-goals:** Changing intent identity, the parent/related-intent graph, status, brief coverage, closure policy, spec or brief authoring, tracker projection, or direct-light execution records. Bulk backfilling missing mappings, silently reclassifying `cut-before-adding-solution-ladder`, making `navigate-intents`, and persisting a graph or index are excluded. Contextual `Contract:` or research `Discovery:` provenance does not become feature-delivery ownership.
- **Dependencies:** FEAT-0001's shipped typed reference grammar supplies unambiguous `Parent intent:` and `Brief:` targets. FEAT-0005's shipped `close-work` descendant and ancestor resolver is the existing consumer to converge, not an ordering dependency. `lint-traceability.py` is the other current consumer. RFC-0105 and `navigate-intents` are conditional future consumers only if the `adr-summary` work lands.
- **Design context:** The 2026-10-03 corpus snapshot has 16 feature intents with the `spec` terminus: seven resolve exactly once, eight are missing, and one resolves six times. Its five `brief` feature intents resolve through five briefs to 21 specs. Twelve specs carry both `Discovery:` and `Brief:`. In that snapshot, `close-work` selects descendant edges by terminus but walks both ancestor routes, while traceability collapses producer candidates to one winner. No spec there uses a `Parent intent:` field; direct feature delivery is carried by `Discovery:` in legacy path and typed-intent forms.
- **Delivery resolution:** The spec and plan linked above own the resolver boundary, typed snapshot, consumer entry points, diagnostic vocabulary, confined normalization, resource limits, fallback refusal, and construction evidence. Those decisions are linked rather than copied here so the approved delivery contract has one home.
- **Provenance:** This intent, de-risked and decomposed 2026-10-03; [ADR-0077 D1 and D2](../../adr/0077-feature-projection-and-tracker-authority.md); the accepted [repository work graph capability](CAP-0001-repository-work-graph.md); the existing [lifecycle and closure consumer](FEAT-0005-lifecycle-and-closure.md); and conditional read-only evidence from unlanded RFC-0105 in the dirty `adr-summary` worktree.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.
