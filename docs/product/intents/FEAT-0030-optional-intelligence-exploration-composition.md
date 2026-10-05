# Optional intelligence in repository exploration

- **Slug:** `optional-intelligence-exploration-composition`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:optional-code-intelligence-composition
- **Shaping-reviewed:** 2026-10-04
- **De-risked:** 2026-10-04
- **Decomposed:** 2026-10-04 spec
- **Governed by:** [RFC-0079](../../rfc/0079-codebase-context-pack.md)

## Outcome

- **Input (steerable):** Repository-exploration methods that can select a
  relevant exposed capability, preserve its material limits, and fall back
  without adding provider steps to the activity that asked the question.
- **Outcome (lagging):** Debugging, review, implementation, architecture work,
  and future agentic loops can use richer code understanding through their
  existing repository questions instead of treating code intelligence as a
  separate archaeology-only phase.
- **Guardrail:** No consuming workflow gains a mandatory provider check, fixed
  investigation taxonomy, central broker, or permission to trust tool output as
  instruction or repository authority.

## Opportunity

- **Functional job:** Follow behavior, dependencies, impact, or context far
  enough to make the current development decision with evidence suited to the
  question.
- **Emotional job:** Stay oriented without learning every provider or wondering
  whether a successful query silently omitted decisive edges.
- **Social job:** Give collaborators a reviewable explanation of which evidence
  was used, what it could not establish, and why exploration stopped.
- **Struggling moment:** Each activity can either ignore an exposed semantic
  tool or reinvent discovery, invocation, caveat handling, and fallback in its
  main procedure.

## Boundary

This feature owns a reusable exploration method for semantic task-fit selection,
native invocation, attributed evidence, bounded stopping, and deliberate
fallback. It may be reused by inquiry owners; it is not a mandatory workflow
phase or a central runtime router.

It does not edit `work-loop`, spec authoring, review, debugging, or architecture
main flows merely to mention a provider. It does not freeze the five current
`code-intelligence` investigation patterns, claim all repository questions are
graph questions, or establish graph-assisted review effectiveness.

## Assumptions

- **Riskiest assumption:** Inquiry owners can use one small exploration method
  across heterogeneous native surfaces more easily than inventing local
  provider handling, without that method becoming a schema, broker, or new
  phase in their work.
- Consuming activities can ask repository questions through this method while
  retaining their own decision and stopping authority.
- Material caveats can be preserved in ordinary evidence-bearing output without
  imposing a result envelope on providers.
- **Knowledge surface:** CAP-0011, RFC-0079, ADR-0097, RFC-0104, the loop
  contract, and the shipped `code-intelligence` pack in this repository.

## De-risking

- **Door:** two-way. A reusable method can be tried by a small set of inquiry
  owners and removed without changing provider interfaces or workflow state.
- **Prototype approach:** `prototype-led`. The method is tested as a short
  decision trace over existing native surfaces before it becomes guidance.
- **What would have to be true:** The same reasoning steps — state the
  repository question, inspect exposed capabilities, choose a task-fit native
  action or fallback, carry material limits, verify load-bearing claims, and
  stop at the inquiry's bound — must work across unlike provider shapes without
  normalizing their commands or results.
- **Test target:** The riskiest assumption named above.
- **Kill condition (predeclared 2026-10-04):** Kill or split the shared method
  if fewer than four of the six parent construction questions can be routed by
  those reasoning steps across both the graph-CLI and editor/LSP shapes, or if
  routing any successful question requires a common request, result,
  capability, provenance, freshness, or workflow-state contract.
- **Probe:** Re-run the parent capability's six-question construction exercise
  as an exploration-method trace rather than as a provider-feasibility test.
  The trace must explain the choice, the native action or deliberate fallback,
  the evidence limit, the authoritative check when needed, and the stopping
  point.
- **Result:** Six of six questions can follow the same reasoning steps. Symbol
  definition and incoming calls use editor/LSP-native actions; transitive impact
  and dependency paths use Wicked Estate's native actions; authority and
  co-change questions deliberately use repository-native evidence. No common
  provider payload or provider lifecycle state is needed.
- **Evidence class:** Construction and desk feasibility using the provider
  surfaces already examined by CAP-0011. This does not prove that a cold user
  finds the method easier or that future provider shapes will fit it.
- **Verdict:** **Survived.** A compact shared method is viable across the two
  examined shapes and preserves deliberate fallback. Independent usability and
  future-shape fit remain `to-validate`.
- **Reviews (2026-10-04):** Independent shaping and adversarial reviews were
  rerun after decomposition and were clean. Only this updated receipt was added
  after the final review.

```yaml validation_hook
assumption: Inquiry owners can use one small exploration method across heterogeneous native surfaces more easily than inventing local provider handling, without turning it into a schema, broker, or workflow phase.
kill_condition: Kill or split the method if fewer than two of three maintainers complete at least four of five representative exploration tasks without coaching, if any needs a shared provider payload or provider-specific step in the consuming workflow, or if more than one fails to carry a material evidence limit or choose deliberate fallback for a poor-fit task.
activity: Give three maintainers five debugging, review, implementation, architecture, and task-context questions in at least two live provider environments. Withhold RFC and golden-example wording; observe their capability choice, native invocation, caveat handling, fallback, and stopping point.
```

## Decomposition

**One slice, `optional-intelligence-exploration-composition`,** projected to
`new-spec` as a delivery contract. The reusable method and the evaluations that
prove it across unlike native surfaces are one shippable behavior, so they need
one spec/plan pair.

### Why one slice

- Selection without caveat handling and fallback would be unsafe; caveat
  handling without a task-fit selection method would not be usable. They ship
  and test together.
- Debugging, review, implementation, architecture, and task-context questions
  are consumers and fixtures, not separate features or workflow integrations.
- CLI, MCP, editor, language-server, indexed, and hosted tools remain provider
  variants. Splitting by transport would recreate the schema-shaped model this
  feature rejects.

### Delivery contract

- **Outcome:** An inquiry owner can state a repository question, inspect only
  already-exposed capabilities, choose a task-fit native action or deliberate
  fallback, carry material evidence limits, verify load-bearing claims, and
  stop at its own bound without adding provider ceremony to the consuming
  activity.
- **Success evidence:** The method routes representative debugging, review,
  implementation, architecture, and task-context cases across at least two
  materially different provider shapes; includes a poor-fit fallback case;
  preserves native invocation and result forms; and introduces no common
  request, result, capability, provenance, freshness, or workflow-state schema.
- **In scope:** The reusable exploration method, task-fit selection, bounded
  invocation, attribution, caveat preservation, authoritative verification,
  fallback, stopping rules, and heterogeneous-provider evaluations.
- **Non-goals:** A provider broker or registry, a mandatory workflow phase,
  direct provider steps in consuming workflows, a fixed investigation
  taxonomy, or a claim that graph assistance improves review outcomes.
- **Dependencies:** Accepted RFC-0079 and the repository's existing exploration
  owners. FEAT-0029 is a sibling seam, not a prerequisite.
- **Design context:** The shared method governs the inquiry's reasoning and
  evidence discipline, never the provider's transport, verbs, payload, or
  maturity model.
- **Questions for `new-spec`:** Which existing owner holds the reusable method;
  how consumers invoke it without adding a new phase; which heterogeneous
  provider fixtures establish native-shape coverage; and what evidence proves
  a fallback was deliberate rather than an unnoticed provider miss.
- **Provenance:** This de-risked intent, CAP-0011, Accepted RFC-0079, ADR-0097,
  RFC-0104, and the shipped `code-intelligence` pack.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/product/intents/CAP-0011-optional-code-intelligence-composition.md`
- **Revision:** `working-tree-2026-10-04`
- **Authority:** eugenelim, parent capability owner
