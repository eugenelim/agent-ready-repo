# Cross-pack routing contract — `run-okr-cascade` → `frame-situation`

## Overview

`run-okr-cascade` is the integration point between the `product-strategy` pack and the PE pack's `frame-situation` skill. The contract is **agent-mediated** — no mechanical cross-pack call; `workspace.toml` is the durable, session-independent handoff artifact.

## The seven-step sequence

1. **Input:** Company OKRs (strategist-supplied or read from `docs/product/shaping/`); portfolio position from `portfolio-position.md` if available.
2. **Cascade:** `run-okr-cascade` derives team-level OKRs from company OKRs and identifies gaps between current state and OKR targets.
3. **Committed artifact:** `okr-cascade.md` written to `docs/product/shaping/` with company OKRs, derived team OKRs, and gap registry.
4. **Gap entry format:** Each gap is written as `{slug = "<gap-slug>", type = "strategy"}` — no `needs` field (no-dependency entries omit it; the RFC-0063 literal `needs = "nothing"` is a malformed value superseded by this contract).
5. **Shaping queue target:** Gaps are appended to the active initiative's `["ini-NNN".shaping_queue].backlog` array in `workspace.toml`. "Active" means `status = "active"` in the `["ini-NNN"]` section header. If exactly one section is active, it is used automatically. If multiple are active, the skill elicits the target from the user before appending.
6. **Handoff:** The product engineer (or the same person in the next session) invokes `frame-situation` on each `{type = "strategy"}` queue entry; `frame-situation` routes the gap through the six-step shaping sequence producing a DoR-compliant brief in `[brief_queue]`.
7. **Absent PE pack diagnostic:** If `frame-situation` is not found in the installed skills, the skill surfaces: `"frame-situation not found — install PE pack to route OKR gaps into the shaping sequence"` rather than failing silently.

## Boundary

- **Product-strategy pack writes** to `["ini-NNN".shaping_queue].backlog`.
- **PE pack reads** from the shaping queue; neither calls the other directly.
- The shaping queue survives session boundaries — it is the durable handoff, not a live API call.

## `check-workspace` routing

`check-workspace` (core pack) routes `{type = "strategy"}` entries to `frame-situation` (PE pack — M2) or `frame-intent` as interim. This routing was updated as part of this pack's M4 implementation.

## Co-install note

Both packs are user-scoped. In smaller organizations the strategist and PE may be the same person with both packs installed; the cross-pack dependency is agent-mediated, not a build-time constraint.
