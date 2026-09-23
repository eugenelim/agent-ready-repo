# Digital experience doctrine

- **Slug:** `digital-experience-doctrine` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Draft
- **Level:** capability
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** none — see Placement
- **Governed by:** [RFC-0071 Digital Experience Doctrine](../../rfc/0071-digital-experience-doctrine.md) (Accepted)
- **Decomposed:** 2026-09-20 children
- **Delivery coordination:** [Digital Experience Doctrine completion](../briefs/digital-experience-doctrine-completion.md)

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

**The four packs' boundaries are right, and the defect is at the seams rather
than in how the lifecycle is divided.**

Everything below this intent assumes the seams are the problem. If the division
is wrong — if, say, experience-design and frontend-engineering are one job split
in two — then seven seam fixes will not compose, and the family will deliver
seven locally-correct artifacts that still fail at the render. That is the same
failure mode one altitude up, which is what makes it the bet rather than a
detail.

It is untested, and nothing available tests it. The obvious candidate does not:
`references/digital-experience-contract.md` ships as four byte-identical copies
named by no `SKILL.md`, which looks like disconfirming evidence and is not. Its
own spec, [`digital-experience-contract`](../../specs/digital-experience-contract/spec.md),
states the design: the template "is additive — it ships alongside existing skills without
changing any SKILL.md file. Downstream doctrine specs (M2a–M4) update skills to
reference and populate the contract; this spec ships the shared schema they will
reference." The consumer is unbuilt by plan, not missing by defect.

So the seam assumption is untested in the strict sense — the schema shipped, the
wiring is what the seven children carry, and no walked case exists yet. The
first child to land a consumer is what would settle it, which is why this stays
a named bet rather than a concern.

`de-risk-intent` owns testing this; it is named here, not tested here.

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

**This is the family, not the decomposition.** `## Decomposition` stays empty:
recording it is `decompose-intent`'s job, and `frame-intent` step 6 is explicit
that framing leaves the field alone.

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

Empty. The seven back-links are written and the family is recorded above, but
filling this field is `decompose-intent`'s job; framing does not do it.

## Assumptions

- The four packs' boundaries are right, and the defect is at the seams rather
  than in how the lifecycle is divided. If the division is wrong, seven seam
  fixes will not compose.
- A shared contract can be composed by a receiving pack without coupling the
  packs to each other. Untested rather than disproven: the contract that exists
  today (`references/digital-experience-contract.md`, four byte-identical
  copies) is named by no `SKILL.md` **by design** — its own spec defers the
  wiring to the downstream doctrine specs — so the mechanism is unbuilt, not
  failed. The first child to land a consumer is what would test it.
- The RFC-0071 / ADR-0052 tension over `design-system-foundations` resolves the
  way RFC-0071 anticipated. ADR-0052 D1 renamed `design-system-foundations` →
  `design-system`; RFC-0071 D3a asks for `design-system-foundations` back as a
  new skill, and its D3b proposes renaming `design-system` →
  `design-token-taxonomy` to remove the resulting activation overlap. So the RFC
  saw the collision and proposed a way through it rather than ignoring it — but
  neither D3a nor D3b has shipped, and `design-token-taxonomy` exists nowhere in
  `packs/`. Until one of the two records is acted on, M3b cannot be delivered.
- The foundation this capability inherits as closed may not be. `Boundary`
  excludes three seams on the grounds that shipped specs already carry them, and
  that exclusion is what makes the child set a partition rather than a set with
  a gap. For M1 that ground is weaker than it looks: three of its acceptance
  criteria assert that the phrase "Digital Experience Contract" appears in the
  `whatChanges` field of `web/src/content/journeys/product-strategy.md`,
  `experience-design.md` and `core.md`. All three are ticked; the phrase is in
  none of them today. Those pages declare `generated: true`, no generator in the
  tree produces them, and the only lint over them compares skill counts — so
  nothing would catch the drift. Until someone establishes what M1 actually
  delivered, this intent's claim to have inherited that seam closed rests on a
  tick rather than on the artifact.
- Knowledge surfaces consulted while framing: the repository's own documents
  (RFC-0071, ADR-0052, ADR-0119, `workspace.toml`, the four packs and the
  guides tree). No MCP knowledge tool or internal CLI was detected, so nothing
  external to this repository grounds the outcome above.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
