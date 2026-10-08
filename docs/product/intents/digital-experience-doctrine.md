# Digital experience doctrine

- **Slug:** `digital-experience-doctrine` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Accepted
- **Accepted:** 2026-10-01 by eugenelim, lifecycle owner. Revision `11e788ad445790c7` returned zero `MALFORMED` tokens in an independent intent-mode shaping review; a fresh adversarial intent read returned no open question or replacement validation hook after the Claude Code and Codex pair was named. The capability-level assumption survived its predeclared kill condition, and `decompose-intent` reconfirmed the seven-child cut without a re-slice.
- **Level:** capability
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** none <!-- see Placement -->
- **Governed by:** [RFC-0071 Digital Experience Doctrine](../../rfc/0071-digital-experience-doctrine.md) (Accepted)
- **De-risked:** 2026-10-01
- **Shaping-reviewed:** 2026-10-01
- **Decomposed:** 2026-09-20 children

## Outcome

- **Input (steerable):** the share of handoffs between the four lifecycle packs that carry a named contract the receiving pack can act on without re-deriving the context behind it.
- **Outcome (lagging):** an artifact that passes its own pack's rubric also composes into a working chain — "locally polished, globally broken" stops being the default result.
- **Guardrail:** each pack stays independently usable. Adopting the chain must not become a precondition for using one pack on its own.

This outcome is qualitative-but-falsifiable rather than numeric: there is no
baseline measurement of handoff quality in the repository today, so the signal
accepted as proof is a walked end-to-end case — a market signal carried through
strategy, bet, design and rendered implementation where no step re-derives what
the previous step already decided.

## Opportunity

- **Functional job:** take a product outcome from raw market signal through strategy, a testable bet, a designed experience, and a rendered implementation, without re-deriving context at each handoff.
- **Emotional job:** trust that what you hand on will be acted on as you meant it, rather than reinterpreted by whoever picks it up.
- **Social job:** be seen as contributing to one product rather than filing locally-correct artifacts into a void.
- **Struggling moment:** each pack passes its own rubric, so nothing flags that the chain is broken. The failure surfaces at the rendered artifact — the most expensive place to find it and the furthest from whoever caused it.

RFC-0071 states the diagnosis directly: four packs cover the digital product
lifecycle — `product-strategy` (raw market signal → strategic choices),
`product-engineering` (opportunity → testable bet), `experience-design` (bet →
designed whole experience), and `core`/`frontend-engineering` (design artifacts
→ rendered verified implementation) — and "each pack individually passes its own
rubric… artifacts can be locally polished and globally broken."

## Boundary

Includes the **seams** between the four lifecycle packs: what a handoff must
carry so the receiving pack can act without re-deriving it, and the evaluation
that tells you the chain composed rather than that each end passed its own
rubric. The seven intents under "The family this parents" are that surface,
sliced by pack and by milestone.

Excludes each pack's **internal** rubric — every pack owns and keeps its own.
Excludes the division of the lifecycle into these four packs, which RFC-0071
treats as settled and this intent does not reopen. Excludes the delivery of any
child, which each child owns. Excludes retiring the `ini-003` initiative entry,
which belongs to the ADR-0119 migration
([FEAT-0004](FEAT-0004-single-ladder-migration.md)) and needs its own
authorization.

**Excludes every seam already delivered**, which is why the children do not
cover all four packs evenly. The `core`/`frontend-engineering` seam named in the
Outcome has no child intent because
[`frontend-engineering-doctrine-update`](../../specs/frontend-engineering-doctrine-update/spec.md)
carries it as a spec; the shared contract schema the Outcome's "named contract"
depends on is carried by
[`digital-experience-contract`](../../specs/digital-experience-contract/spec.md);
and the experience-design skill boundaries the three XD children build on are
carried by [`xd-skill-boundaries`](../../specs/xd-skill-boundaries/spec.md).
Those are not gaps in the decomposition. They are seams this intent inherited
already closed, and a capability intent decomposes into intents rather than
adopting specs as children.

## Riskiest assumption

**The seven child outcomes can compose through stable handoffs without coupling
the four packs or leaving required work owned only by the deleted coordinating
brief.** This is the operational form of the capability-level assumption that
the lifecycle division is sound and the remaining defect is at its seams.

## De-risk record — 2026-10-01

- **Level kind:** capability, so this is an architectural and adoption probe.
- **Reversibility triage:** one-way door. Once pack methods, tests, and guides
  depend on this division of responsibility, undoing it would cross several
  published contracts.
- **Prototype approach:** `validate-first`. The cheapest probe that could fail
  was a repository walk over the accepted sequence, shipped cross-pack seams,
  live ownership, and the remaining dependency graph.

### Kill condition, predeclared

Reframe the capability if any one of these conditions holds:

1. the seven children do not form a complete, non-overlapping partition of the
   remaining doctrine outcome;
2. fewer than two shipped cross-pack seams already prove stable artifact
   handoffs without pack-internal coupling; or
3. the remaining dependency graph contains a cycle or an ownerless required
   outcome.

The line was recorded before the repository probe ran and was not moved.

### Probe

- **Partition — survives.** RFC-0071's eleven-node implementation sequence has
  four delivered foundations outside this child set: the shared contract,
  copy-direction, XD skill boundaries, and frontend doctrine. The seven named
  children are the sequence's remaining M2a, M2b, M3b, M3c, M3d, M5, and M6
  outcomes. Their boundaries are disjoint by pack or milestone, and each owns
  one independently shippable spec-and-plan projection. The fulfilled M3b child
  remains in the family as delivered coverage rather than disappearing from the
  partition.
- **Shipped seams — survives with two independent proofs.** The shipped
  [`design-output-addressing`](../../specs/design-output-addressing/spec.md)
  contract gives Experience Design stable `output_dir`-relative artifact
  addresses and a declared taxonomy consumer; shipped
  [`design-handoff-read`](../../specs/design-handoff-read/spec.md) makes Frontend
  Engineering consume those typed artifacts through those addresses. Separately,
  shipped
  [`frontend-experience-composition`](../../specs/frontend-experience-composition/spec.md)
  joins both pack journeys through byte-identical pack-local Digital Experience
  Contract copies, shared state/depth semantics, and named crossing artifacts.
  Both respect the repository rule that no pack infers a dependency from another
  pack's directory.
- **Graph and ownership — survives.** The live `workspace.toml` edges order M3c
  before M3d, all doctrine children before M5, and M5 before M6; M2a and M2b
  depend only on the shipped contract. That graph is acyclic. No live product or
  workspace record refers to the deleted coordinating brief, and its remaining
  obligations are owned either by one of these seven children or by the bounded
  repair and intake routes named under Current delivery shape.

### Verdict — survived

None of the three kill arms fired. The repository proves that the pack boundary
can carry stable artifact and semantic handoffs, that the seven-child cut covers
the remaining accepted sequence, and that the remaining work has an acyclic
owner path. This is architectural evidence, not proof of adopter success; the
walked journey in Outcome is still owed.

### Validation hook

```yaml
validation_hook:
  assumption: The seven child outcomes compose through stable handoffs without coupling the four packs or leaving required work without an owner.
  kill_condition: Reframe if either the Claude Code or Codex walk needs an undocumented pack-internal path, cannot identify the next artifact owner, or produces a locally passing but globally broken result.
  activity: to-validate — after the remaining children ship, run one representative strategy-to-shaping-to-XD-to-frontend journey through Claude Code and Codex, then inspect every crossing artifact and terminal outcome.
```

Claude Code and Codex are the predeclared pair because both are full supported
adapters while exercising different projection shapes. This sample does not
reduce M5's broader obligation to test every supported headless host.

## Placement

This intent has no parent. It sits directly beneath the repository's existing
strategy layer without being decomposed from it: the RFC-0071 family predates
the typed intent graph and was carried by an initiative instead.
[STRAT-0003](STRAT-0003-autonomous-product-team-operating-model.md) is the
nearest strategy, and its boundary explicitly assigns "the loops that execute
that doctrine" to [STRAT-0002](STRAT-0002-platform-core.md), whose decomposition
is closed. Neither is a clean parent, so claiming one would fabricate a tree
edge that was never taken. Naming that openly is more useful than a
back-formed lineage.

## The family this parents

Seven `feature` intents are this intent's children. Each carries a
`Parent intent:` back-link, so the edge reads from both ends, and each carries a
`Milestone:` naming its node in RFC-0071's implementation sequence.

- [product-strategy-adoption-doctrine](product-strategy-adoption-doctrine.md)
- [product-engineering-shaping-doctrine](product-engineering-shaping-doctrine.md)
- [xd-design-system-foundations](xd-design-system-foundations.md)
- [xd-ia-archetypes-objects](xd-ia-archetypes-objects.md)
- [xd-state-reviewer-doctrine](xd-state-reviewer-doctrine.md)
- [cross-pack-experience-eval](cross-pack-experience-eval.md)
- [digital-product-guides-update](digital-product-guides-update.md)

**Why these seven and not others.** RFC-0071 § "Implementation sequence" defines
the dependency DAG this family comes from; that section owns it and this intent
does not reproduce it. Read there for the full ordering and for the milestones
carried as specs rather than as intents. What this intent adds is the boundary
it draws over that sequence: the units still carried as intents are its
children, and the units already carried as specs are not, because a capability
intent decomposes into intents and those were never framed as any.

Four intents cite RFC-0071 in passing without belonging to its sequence and are
likewise not children: `adopter-catalogue-test-command`,
`frozen-record-errata-mechanism`, `pack-javascript-ci-workflow`,
`skill-description-semantic-drift-gate`.

## Current delivery shape — 2026-10-01

The capability is coordinated by its intent tree, not by a delivery brief. Each
feature child reduces to one independently shippable same-repository spec and
plan under the [current-standards pressure test](../research/digital-experience-doctrine-current-standards-survey.md).
If shaping crosses a split condition, the child must be re-decomposed before
spec authoring rather than wrapped in a capability-level brief.

| Feature intent | One-feature boundary | Spec and plan |
| --- | --- | --- |
| [`product-strategy-adoption-doctrine`](product-strategy-adoption-doctrine.md) | One portable strategy-to-adoption contract; split if growth operations or runtime telemetry implementation enters scope | `docs/specs/product-strategy-adoption-doctrine/` |
| [`product-engineering-shaping-doctrine`](product-engineering-shaping-doctrine.md) | One observable, learning-oriented shaping contract; split if adapter or protocol implementation enters scope | `docs/specs/product-engineering-shaping-doctrine/` |
| [`xd-design-system-foundations`](xd-design-system-foundations.md) | One project-value-resolution contract; DTCG serialization is a separate interoperability seam | [`docs/specs/design-system-values/`](../../specs/design-system-values/) |
| [`xd-ia-archetypes-objects`](xd-ia-archetypes-objects.md) | One IA method joining archetype, object, action, attention, and navigation; split if policy enforcement enters scope | `docs/specs/xd-ia-archetypes-objects/` |
| [`xd-state-reviewer-doctrine`](xd-state-reviewer-doctrine.md) | One reproducible state-and-review contract; split if a general browser runtime becomes the product | `docs/specs/xd-state-reviewer-doctrine/` |
| [`cross-pack-experience-eval`](cross-pack-experience-eval.md) | One layered journey evaluation; split if it becomes a general eval platform or remote-agent implementation | `docs/specs/cross-pack-experience-eval/` |
| [`digital-product-guides-update`](digital-product-guides-update.md) | One adoption surface joining verified indexes, a host-neutral tutorial, and host overlays | `docs/specs/digital-product-guides-update/` |

Each child owns its lifecycle status. All seven now carry the required identity,
hierarchy, scale, maturity, owner, source, and decomposition metadata. Optional
decision evidence is present only where a decision record exists; no
`De-risked`, `Shaping-reviewed`, or `Accepted` result has been invented. A
projected spec path enters `workspace.toml` only after its intent is ready and
the spec exists; until then, the intent remains the registered unit.

Two residual seams are not extra children of this capability. The three journey
projections that no longer contain `Digital Experience Contract` are a bounded
repair of the shipped contract projection. The executable design-handoff
resolver and product discriminator return through `work-intake`; one
independently shippable result becomes a spec, while a genuinely distinct
outcome must first become an intent.

Pack-local motion/platform craft, experience-design reference reconciliation,
the Agent Skills `allowed-tools` schema mismatch, and DTCG serialization remain
outside this capability's seam boundary. They require their own intake or
bounded repair and do not delay the seven-child family.

### Why this family, and why now

- **The children came first; the parent is retroactive.** `decompose-intent`'s
  retroactive-parent rule names this case — siblings that are architectural
  slices of one buildable thing take a `capability` parent — and seven slices of
  one doctrine across four packs is that shape.
- **`ini-003` is what this replaces.** The family is currently held by the
  `ini-003 "Digital Experience Doctrine"` initiative. ADR-0119 (Accepted)
  retires the initiative ladder into the recursive intent graph, so this intent
  is where that initiative's content belongs. Retiring the `ini-003` entry is a
  separate, explicitly authorized step and is not done by framing this.

## Decomposition

The seven feature intents under [The family this parents](#the-family-this-parents)
are this capability's decomposition. Each child owns one spec-and-plan boundary
as sized above. No delivery brief sits between the capability and those
children.

**Confirmed 2026-10-01 with `decompose-intent`: no re-cut is needed.** The
children are the next lower `feature` level, collectively cover every remaining
RFC-0071 milestone, and each passes the shippability test as one same-repository
delivery contract. Their dependency edges already supply the order, so no
separate ranking is useful. The split conditions recorded in Current delivery
shape remain the upward-feedback triggers: crossing one requires re-decomposing
that child before spec authoring, not adding a capability-level brief.

## Assumptions

- The four packs' boundaries are right, and the defect is at the seams rather
  than in how the lifecycle is divided. The 2026-10-01 architectural probe
  survived; the validation hook still owes a two-adapter end-to-end adoption
  walk.
- A shared contract can be composed by a receiving pack without coupling the
  packs to each other. Two shipped seams now prove the architectural mechanism;
  the remaining children and validation hook still test full lifecycle adoption.
- ADR-0128 resolved the RFC-0071 / ADR-0052 design-system tension through four
  routes inside `design-system`; the linked child owns the closure evidence.
- The three journey projections that omit `Digital Experience Contract` remain
  a bounded repair of the shipped projection, not an eighth feature intent.
- External evidence was refreshed on 2026-10-01 against current strategy,
  telemetry, accessibility, design-token, Agent Skills, host-adapter, MCP, and
  A2A sources. The linked survey owns those findings and their confidence.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
