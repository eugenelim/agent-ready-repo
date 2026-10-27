# Cross-pack routing contract — `run-okr-cascade` → `frame-situation`

## Overview

`run-okr-cascade` is the integration point between the `product-strategy` pack and the PE pack's `frame-situation` skill. The contract is **agent-mediated** — no mechanical cross-pack call; the gap's captured-item file is the durable, session-independent handoff artifact.

## The six-step sequence

1. **Input:** Company OKRs (strategist-supplied or read from `docs/product/shaping/`); portfolio position from `portfolio-position.md` if available.
2. **Cascade:** `run-okr-cascade` derives team-level OKRs from company OKRs and identifies gaps between current state and OKR targets.
3. **Committed artifact:** `okr-cascade.md` written to `docs/product/shaping/` with company OKRs, derived team OKRs, and gap registry.
4. **Gap file format:** Each gap is written as a captured-item file at `docs/product/captured/<gap-slug>.md` holding `Status: Open`, `Kind: intent`, and `Type: strategy`, with the one-line gap under `## Summary`. The file alone records the gap: nothing is added to any index or queue.
5. **Handoff:** The product engineer (or the same person in the next session) invokes `frame-situation` on each gap file whose `Type:` is `strategy`; `frame-situation` routes the gap through the six-step shaping sequence producing a DoR-compliant brief.
6. **Absent PE pack diagnostic:** If `frame-situation` is not found in the installed skills, the skill surfaces: `"frame-situation not found — install PE pack to route OKR gaps into the shaping sequence"` rather than failing silently.

## Boundary

- **Product-strategy pack writes** one captured-item file per gap under `docs/product/captured/`.
- **PE pack reads** those files; neither calls the other directly.
- The gap file survives session boundaries — it is the durable handoff, not a live API call.

## `workspace-status` routing

`workspace-status` (core pack) routes a captured-item file with `Type: strategy` to `frame-situation` (PE pack — M2) or `intent frame` as interim. This routing was updated as part of this pack's M4 implementation.

## Co-install note

Both packs are user-scoped. In smaller organizations the strategist and PE may be the same person with both packs installed; the cross-pack dependency is agent-mediated, not a build-time constraint.
