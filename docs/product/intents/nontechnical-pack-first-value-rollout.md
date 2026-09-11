# Nontechnical-pack first-value rollout

- **Status:** Draft
- **Level:** capability

## Outcome

The remaining ratified Level B packs gain independently shippable first-value
adoption slices grounded in the three completed pilots.

## Opportunity

RFC-0064 Amendment #4 established the cross-pack adoption contract and the
architect, Figma, and governance pilots now supply evidence for shaping the
remaining rollout without imposing one generic onboarding flow.

## Assumptions

- Each pack slice includes its guide, first-value surface, safety boundary,
  recovery path, and evaluation evidence.
- Existing P2/P3/P4 guides and tutorials are audited before new work is
  proposed.
- The rollout remains one appetite-bounded programme whose pack slices can ship
  independently.

## Derived work

[ADR-0107](../../adr/0107-claude-plugin-route-serves-non-technical-adopters.md)
(Accepted 2026-09-10) leaves this capability's abstract outcome unchanged, but it
**widens the supported-surface contract this capability depends on**. Before a
Claude-apps slice reaches spec, the first-value contract's owner must decide how
the Claude apps, per-surface registration, the absence of filesystem access, and
surface-specific degradation are represented — without duplicating those facts
into guides.

That decision is a hard predecessor, not a caveat.
[`portfolio-pack-first-value-contract`](../../specs/portfolio-pack-first-value-contract/spec.md)
requires `surfaces ⊆ [pack.install].allowed-adapters`, a closed set of adapter
names, and all four discipline packs currently declare
`surfaces = ["claude-code"]`. The Claude apps are not an adapter name, so no
compliant Claude-apps first-value record can be written today.

| Slice | Owns | Status |
| --- | --- | --- |
| [`claude-apps-first-value-entry`](claude-apps-first-value-entry.md) | A no-terminal public route into installing at least one discipline pack in the Claude apps, plus one first-value walkthrough — as a *consumer* of each pack's `[pack.first-value]` contract | Draft, blocked on the surfaces decision above |

Two further constraints every Claude-apps slice inherits:

- **Registration is per surface.** Claude Code and the Claude apps keep separate
  plugin stores, so a slice's instructions must say where to register and must
  not imply one install reaches both.
- **Sub-agents are inert in the chat tab.** Degradation is already owned per
  pack — `research-pack/spec.md` specifies inline fallback, and
  `experience-reviewer-work-loop-gate/spec.md` makes reviewer absence a named
  skip — so a slice picks a pack whose method survives the surface, and routes
  any deviation as a defect against the owning spec rather than restating a
  policy here.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0064-ini-001-ai-native-ecosystem.md
- Revision: sha256-bytes-v1:26693aa8f9a49eba83258db06be0795b664cb2c09d4c0742ed9b502666d8efca
