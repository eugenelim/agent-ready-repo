# Optional intelligence in repository grounding

- **Slug:** `optional-intelligence-grounding-composition`
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

- **Input (steerable):** Grounding inquiries that prove the same accepted
  outcome and bar with no provider, while a provider-fit fixture contributes
  attributed evidence through its native surface.
- **Outcome (lagging):** An agent identifying repository constraints can use
  suitable exposed code intelligence to find stronger evidence without making
  an optional tool part of Core's grounding contract.
- **Guardrail:** Grounding stays bounded and report-never-decide; provider
  absence, failure, or poor fit does not block it or lower preservation,
  acceptance, security, or review requirements.

## Opportunity

- **Functional job:** Discover what governs, moves with, consumes, and verifies
  a contemplated change using the strongest permitted repository evidence.
- **Emotional job:** Trust that an optional accelerator cannot hide a weaker
  fallback or turn a derived graph into authority.
- **Social job:** Show reviewers that preservation claims are backed by
  attributed evidence rather than by tool availability.
- **Struggling moment:** A grounding inquiry can benefit from resolved
  relationships, but wiring those relationships into an authoring flow would
  make that flow provider-aware and make absence look like failure.

## Boundary

This feature owns optional capability discovery, invocation, evidence handling,
and absence behavior inside an existing repository-grounding owner. It includes
provider-fit, absent, partial, conflicting, and unsafe-result fixtures at that
seam.

It does not create a grounding phase, router, provider schema, or required
index. It does not add the probes owned by `grounding-probe-extensions`, define
the preservation properties owned by `repository-grounding-preservation`, or
move provider logic into `new-spec`, `work-loop`, or another consuming flow.

## Assumptions

- **Riskiest assumption:** Grounding owners have recurring repository questions
  where optional provider evidence is useful enough to justify a shared seam,
  while that seam can still preserve the same no-provider acceptance result and
  keep provider handling out of its consumers.
- A provider-assisted grounding answer can remain advisory and subordinate to
  repository guidance and source.
- The owning seam can test equivalence of outcomes without requiring identical
  evidence or wording.
- **Knowledge surface:** CAP-0011, RFC-0079, ADR-0037, the grounding-probes
  survey, `repository-grounding-preservation`, and
  `grounding-probe-extensions` in this repository.

## De-risking

- **Door:** two-way. The composition can be prototyped in one grounding owner
  and removed without changing the consuming workflow or its accepted result.
- **Prototype approach:** `prototype-led`. A four-case contract trace is the
  cheapest useful prototype because the feature is a seam, not a provider
  implementation.
- **What would have to be true:** One grounding owner must be able to treat an
  available provider as another bounded evidence source for a useful question,
  while absence, poor fit, failure, conflict, and unsafe results all preserve
  the existing repository-native result and decision authority.
- **Test target:** The riskiest assumption named above.
- **Kill condition (predeclared 2026-10-04):** Kill or reframe this feature if
  any of the four cases below requires provider lifecycle logic in a consuming
  workflow, lets provider output decide the inquiry, or changes the outcome or
  acceptance bar when no provider is available. Also reframe it as local
  provider work, rather than a shared seam, if no suitable case adds evidence
  beyond the existing seed-bounded probes.
- **Probe:** Trace the current repository-grounding contract and the golden
  provider's existing evidence rules through four distinct cases before
  specifying an implementation.

| Case | Construction result | Boundary preserved? |
| --- | --- | --- |
| No provider is exposed | Run the current seed-bounded repository-native inquiry and report its evidence | Yes; Core remains complete |
| A task-fit provider is exposed | Ask the native provider for a bounded relationship such as resolved callers or transitive impact, attribute it, then verify any load-bearing conclusion | Yes; the provider adds evidence but no authority |
| The provider is a poor fit or fails | Use the repository-native path and state what it cannot establish | Yes; selection failure is not workflow failure |
| The provider conflicts with source or returns an unsafe locator | Reject the locator or derived claim, preserve the conflict as evidence, and leave the acceptance question unresolved until an authoritative check exists | Yes; safety and acceptance bars do not fall |

- **Result:** All four cases fit one grounding-owner boundary without adding a
  provider step to `new-spec`, `work-loop`, or another consumer. The task-fit
  case adds resolved relationship evidence that the current path/reference,
  co-change, gate, content-pin, and guidance probes do not claim to provide.
- **Evidence class:** Contract construction against current in-repository
  grounding and provider guidance. It proves boundary fit, not that adopters
  find the added evidence valuable in live work.
- **Verdict:** **Survived.** The seam is coherent and has a distinct useful case.
  Its desirability and no-provider equivalence remain `to-validate` through the
  real-world hook below.
- **Reviews (2026-10-04):** Independent shaping and adversarial reviews were
  rerun after decomposition and were clean. Only this updated receipt was added
  after the final review.

```yaml validation_hook
assumption: Grounding owners have recurring repository questions where optional provider evidence is useful enough to justify a shared seam while preserving the same no-provider acceptance result.
kill_condition: Kill or localize the feature if, across three paired grounding tasks in at least two repositories, the no-provider run cannot reach the same constraint and acceptance result, any provider-assisted run needs provider ceremony in the consuming workflow, or fewer than two provider-assisted runs add material attributed evidence within the inquiry's existing bound.
activity: Run three real grounding tasks with the same owner and acceptance question, once with a suitable exposed provider and once without it. Compare the constraints found, accepted result, elapsed inquiry bound, added evidence, fallback behavior, and any provider-specific steps visible to the consumer.
```

## Decomposition

**One slice, `optional-intelligence-grounding-composition`,** projected to
`new-spec` as a delivery contract. This is one independently shippable change
to one Core inquiry seam, so it needs one spec/plan pair rather than a
coordinating delivery brief.

### Why one slice

- Capability discovery, native invocation, attributed evidence, conflict
  handling, and no-provider fallback are one observable grounding behavior.
  Shipping any one alone would leave either an unusable provider branch or an
  unproven baseline.
- Provider-fit, absent, partial, conflicting, and unsafe-result cases are
  variants of the same contract, not separate provider or component slices.
- New grounding probes and preservation-property authoring remain with their
  existing owners; neither is a child of this feature.

### Delivery contract

- **Outcome:** One existing repository-grounding owner can use a suitable
  exposed provider as an optional evidence source while producing the same
  accepted constraint and acceptance result when the provider is absent,
  unsuitable, fails, conflicts with source, or returns an unsafe locator.
- **Success evidence:** Paired provider-fit and no-provider fixtures prove the
  same acceptance bar; poor-fit and failure fixtures complete through the
  repository-native path; conflicting or unsafe results cannot decide the
  inquiry; and no consuming workflow contains provider-specific lifecycle
  logic.
- **In scope:** The owning seam's capability discovery, bounded native
  invocation, attribution, material-limit handling, authoritative checks,
  fallback, and the five case classes named in this intent.
- **Non-goals:** A provider schema, router, required index, new grounding phase,
  changes to `work-loop` or spec-authoring main flows, new grounding probes, or
  ownership of preservation-property discovery.
- **Dependencies:** Accepted RFC-0079 and the current repository-grounding
  baseline. FEAT-0030 and FEAT-0031 are not prerequisites.
- **Design context:** Keep the shared contract at outcome level. Provider
  commands, payloads, prerequisites, freshness semantics, and evidence fields
  remain native to the provider that owns them.
- **Questions for `new-spec`:** Which existing grounding owner holds the seam;
  how its current result is compared across paired fixtures; and which
  provider-result conflicts must block a conclusion rather than trigger
  ordinary fallback.
- **Provenance:** This de-risked intent, CAP-0011, Accepted RFC-0079, ADR-0037,
  the repository-grounding preservation brief, and the grounding-probes survey.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/product/intents/CAP-0011-optional-code-intelligence-composition.md`
- **Revision:** `working-tree-2026-10-04`
- **Authority:** eugenelim, parent capability owner
