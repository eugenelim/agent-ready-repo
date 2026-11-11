# Evidence-decided delivery completion

- **Slug:** `evidence-decided-completion`
- **Level:** capability
- **Owner:** eugenelim
- **Status:** Fulfilled
- **Accepted:** 2026-11-04 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review of revision `fa0c47dc1b339d41` returned zero MALFORMED tokens, after a first round on revision `72be1864dea98879` drew `MALFORMED(children)` and the `## Decomposition` section was added.
- **Shaping-reviewed:** 2026-11-04
- **Fulfilled:** 2026-11-09 eugenelim: both child briefs are Shipped (`repository-grounding-preservation` closed 2026-10-29, `acceptance-centered-work-loop` closed 2026-11-09) and every spec in their spec maps is Shipped, including `legacy-engine-cutover`; `brief-level-runner`, which cites this capability as its discovery, is Shipped too. The mechanical closure check refused on an empty descendant set from its delivery snapshot, so the descendants were read from each brief and spec `Status:` header instead.
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** opportunity:autonomous-product-team-operating-model
- **Decomposed:** 2026-11-04 brief

## Outcome

Delivery completion is decided by evidence against accepted criteria, not by
prose review. A change is complete when each accepted criterion has admissible
evidence. A reviewer's sentence that the work looks done does not complete it.

- **Guardrail:** Gates stay risk-calibrated rather than uniform, as the parent
  strategy requires. A low-risk change is not held to a high-risk evidence bar,
  and a high-risk change is not waved through on review prose.

## Boundary

Includes, for changes delivered through the work loop, two parts of the
outcome:

- **The decision:** how completion is decided from accepted criteria and their
  evidence.
- **The criteria it reads:** that a change to a shared repository substrate
  carries the existing behavior it must keep as accepted criteria, so the
  decision cannot pass while that behavior is unchecked.

Non-goals:

- The risk-calibrated gate ladder as doctrine, which the parent strategy owns.
- The work-loop's runtime mechanics, which the briefs and their specs own.
- Review that informs a change without deciding completion.
- Delivery speed and token cost, which
  [`work-loop-delivery-efficiency`](work-loop-delivery-efficiency.md) owns.

## Assumptions

- **Riskiest assumption:** Admissible evidence can be named for the criteria
  that decide completion, so an evidence verdict is not a prose verdict under a
  new label. **Untested** across the work loop as a whole.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this capability's
  outcome.

## Unresolved questions

- **Answered 2026-11-05:** the loops that execute the parent's doctrine sit under
  [Platform Core](STRAT-0002-platform-core.md), and that is where this
  capability's accountability stays. The `Parent intent:` pointer is unchanged.

## Projection

Projected to the two delivery briefs under § Decomposition. Each brief projects
its own slices to specs.

## Decomposition

Two delivery briefs, each pointing back here through `Parent intent:`. Each
owns its own slices, status, and closeout.

1. [`acceptance-centered-work-loop`](../briefs/acceptance-centered-work-loop.md)
   owns **the decision**: the work loop rehydrates completion from approved
   criteria, Git history, evidence, review facts, and explicit decisions, so
   review becomes evidence for accepted properties rather than the verdict.
2. [`repository-grounding-preservation`](../briefs/repository-grounding-preservation.md)
   owns **the criteria it reads** for a shared-substrate change: existing
   behavior that must survive becomes accepted preservation properties with
   admissible evidence before implementation.

The cut does not overlap: the first brief decides against whatever criteria are
accepted, and the second adds one class of criteria without deciding
completion. Together they cover both parts of § Boundary. New work enters this
tree only as a further child with its own part of the outcome.

## Readiness

**Route:** none. Both delivery briefs shipped: `repository-grounding-preservation` closed its cut on 2026-10-29 and `acceptance-centered-work-loop` on 2026-11-09, with all eight of its slices Shipped.

**Riskiest assumption, settled.** Admissible evidence for completion is named in running code: shipped acceptance, review-boundary, supervisor, protected-ref and parallelism code, with the legacy engine and capture gates removed.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/product/briefs/acceptance-centered-work-loop.md`
- **Revision:** `2fe8d6512`
- **Authority:** eugenelim, lifecycle owner
