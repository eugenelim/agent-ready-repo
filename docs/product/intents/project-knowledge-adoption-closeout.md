# Project-knowledge adoption closeout

- **Slug:** `project-knowledge-adoption-closeout`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** capability
- **Owner:** eugenelim
- **Decomposed:** 2026-11-05 brief

## Outcome

The portable project-knowledge programme closes on repository evidence that
its lifecycle is usable, bounded, and supportable across the approved workflow
classes, with explicit decisions for every conditional follow-on.

## Opportunity

The foundation and integration slices establish behavior, but programme
completion requires measured adoption evidence rather than another integration
claim. Closeout supplies the evidence needed to retain the portable baseline,
repair it, or activate a separately governed extension.

## Assumptions

- Engineering and operational integration completes before adoption closeout.
- Repository-contained verification is sufficient for programme closeout;
  physical-device or external-system evidence can follow when that capability
  is available.
- A measured follow-on activates only when closeout evidence meets its stated
  threshold; absence of pressure closes it without implementation.

## Decomposition

- Define adoption, repository-growth, enquiry-latency, capture-loss, privacy,
  and operator-support measures before authoring a closeout spec.
- Evaluate the complete portable lifecycle and record gaps against its existing
  contracts rather than reopening shipped slices by default.
- Decide the disposition of observation retention, derived indexing, external
  capture durability, and multi-project sharing from the measured evidence.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0077-distill-knowledge.md
- Revision: sha256-bytes-v1:94de8754c752838d99562a6b5bbcfbaf64ed688072d0e26149063f5fbac81016

## Readiness

Route: brief, [`project-knowledge-adoption-closeout-delivery`](../briefs/project-knowledge-adoption-closeout-delivery.md). First slice K1: a read-only measurement tool. Measured by hand 2026-11-05: 94 active topics, 17 repository-wide, 24 on the `tools` base alone (28 with subpaths). The `Depends on` header is removed: measurement does not need the engineering integration to finish. This intent now also owns the disposition of the four conditional follow-ons that `project-knowledge-measured-follow-ons` listed; the default for each is closed without implementation.

## Non-goals

- Implementing any follow-on (retention, derived index, external capture backend, shared bank) without measured pressure; each also needs its own RFC where storage or sharing is involved.
- Physical-device or external-system evidence.
- Reopening shipped slices by default.

**Riskiest assumption:** repository-contained measurement is enough to close the programme. Tested agent-only by a measurement tool that fails if any follow-on threshold cannot be measured from the repository.
