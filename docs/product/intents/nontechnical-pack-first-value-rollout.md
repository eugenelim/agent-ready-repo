# Nontechnical-pack first-value rollout

- **Slug:** `nontechnical-pack-first-value-rollout`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **De-risked:** 2026-11-05
- **Level:** capability
- **Owner:** eugenelim
- **Decomposed:** 2026-09-10 children
- **Depends on:** spec:portfolio-first-run-pilot-architect, spec:portfolio-first-run-pilot-figma

## Outcome

The remaining ratified Level B packs gain independently shippable first-value
adoption slices grounded in the three completed pilots.

## Opportunity

RFC-0064 Amendment #4 established the cross-pack adoption contract and the
architect, Figma, and governance pilots now supply evidence for shaping the
remaining rollout without imposing one generic onboarding flow.

## Non-goals

- One generic onboarding flow for every pack.
- Public outcome-to-pack routing (a separate design follow-on).
- P5 role guides and the enterprise rollout playbook, which keep their own phasing.
- **Unowned until the audit:** tutorial and evidence gaps for the other Level B packs have no child; the audit in Readiness names them and each gap then gets one.

## Assumptions

- **Riskiest assumption:** the remaining Level B packs lack tutorial and evidence coverage beyond the first-value contracts they already carry (nine of ten, measured 2026-11-05). Agent-only test: the audit in Readiness lists each pack's contract, tutorial, and eval evidence, and finds zero or more gaps without any live service.
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

**Superseded reasoning, retained:**
[`portfolio-pack-first-value-contract`](../../specs/portfolio-pack-first-value-contract/spec.md)
requires `surfaces ⊆ [pack.install].allowed-adapters`, and all four discipline
packs declare `surfaces = ["claude-code"]`, so no compliant Claude-apps
first-value record can be written today.

**Narrowed 2026-09-10: that is not a predecessor.** Plugin reach is derivable
from `[pack.install] allowed-scopes` plus the Claude-plugin route's user-scope
admission (`claude-plugin-route-scope`, Shipped) and ADR-0107, so the
vocabulary was never the gate. `surfaces` records *verified* first-value
surfaces, and no pack can declare one for the Claude apps until a dated
observation exists — but that declaration has no consumer, so it is **dropped
as a dependency** rather than carried. A Claude-apps slice is unblocked.
Separately, the recommended starting point is now Desktop's **Code tab**,
which is Claude Code and therefore already covered by the
`surfaces = ["claude-code"]` these packs declare.

| Slice | Owns | Status |
| --- | --- | --- |
| [`claude-apps-first-value-entry`](claude-apps-first-value-entry.md) | A no-terminal public route into installing at least one discipline pack in the Claude apps, plus one first-value walkthrough — as a *consumer* of each pack's `[pack.first-value]` contract | Draft; unblocked by the 2026-09-10 narrowing above |

**Named child, not yet created:** one slice per tutorial or evidence gap that the audit in Readiness finds for the other Level B packs. Until the audit runs, those gaps have no child.

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

## Boundary with `pack-guidebook-walkability`

[`pack-guidebook-walkability`](../../specs/pack-guidebook-walkability/spec.md)
owns walkable static guidebooks and makes no first-value claim. This capability
keeps pack-specific first-value adoption slices, including their surface,
safety, recovery, and evaluation evidence.

## Readiness

- **Route:** not ready for a brief. First step is an agent-only audit (direct-light, one session) that lists, for each of the ten Level B packs named in RFC-0064 Amendment 4, whether it has a `[pack.first-value]` record, a tutorial, and eval evidence.
- **Measured 2026-11-05:** nine of the ten Level B packs carry `[pack.first-value]` with a starter task and a next action in `pack.toml`; `user-guide-diataxis` does not. The architect and figma pilot specs and the contract spec are Shipped; no governance pilot spec exists under `docs/specs/`, though the intent's `Depends on` names only the first two. The remaining work is therefore per-pack tutorial and evidence gaps, not contracts.
- **Next step after the audit:** one slice per gap, authored as a brief only if more than two gaps exist; otherwise one spec each. The only recorded child, `claude-apps-first-value-entry`, proceeds on its own.
- **Close or narrow:** if the audit finds no gaps beyond the Claude-apps slice, close this capability when that slice ships.

## De-risk result

- **Date:** 2026-11-05.
- **Ran:** a read-only count for the ten Level B packs of `[pack.first-value]` in `pack.toml`, files under `guides/<pack>/tutorials/`, and `evals.json` files under `packs/<pack>`.
- **Observed:** nine of ten have a first-value record (only `user-guide-diataxis` lacks it). Six of ten have tutorial files; `atlassian`, `converters`, `experience-design` and `user-guide-diataxis` have none under `tutorials/`. Every pack has at least one `evals.json` (1 to 12 files).
- **Verdict:** supports the assumption. Four candidate gaps exist, so the audit has real work. The count is a directory check only: a pack may carry tutorial content under another name (`atlassian` has top-level how-to files), so the audit still reads each guide before a slice is cut.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0064-ini-001-ai-native-ecosystem.md
- Revision: sha256-bytes-v1:26693aa8f9a49eba83258db06be0795b664cb2c09d4c0742ed9b502666d8efca
