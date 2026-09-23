# Design system foundations for experience design

- **Slug:** `xd-design-system-foundations` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:digital-experience-doctrine
- **Milestone:** M3b in RFC-0071's implementation sequence
- **Governed by:** [RFC-0071 D3a](../../rfc/0071-digital-experience-doctrine.md)

## Outcome

Experience-design practitioners can take an approved token taxonomy into a working design-system foundation, with a clear compatibility posture for the tools that consume it.

## Opportunity

The current design-system method stops at deriving a taxonomy, while projects still need a distinct, installable practice for establishing and reviewing the foundation that applies those tokens.

## Assumptions

- The settled XD skill boundaries will distinguish taxonomy naming from foundation implementation.

## What the decision requires

- Add `design-system-foundations` as a distinct `experience-design` skill: it takes a token taxonomy and establishes a working token foundation for a specific project (RFC-0071 D3a).
- Its lightweight mode covers semantic color roles, typography, spacing, radius, focus, key statuses, responsive rules, and core components (RFC-0071 Area D).
- Its full mode covers a DTCG 2025.10-compatible token source, light and dark themes, semantic aliases, full component anatomy, and generated platform outputs (RFC-0071 Area D).
- Keep taxonomy derivation and foundation implementation as separate jobs with distinct triggers, outputs, and reviewers (RFC-0071 D3a).

### Observed state — 2026-09-20

Each row is a check against the live tree (`packs/`, `guides/`, `web/`,
`docs-site/`, `tools/`, `packages/`), re-runnable rather than trusted. Frozen
spec bodies under `docs/specs/` are historical records and were not counted as
evidence. This is an observation on a date, not a status field.

| Requirement | Observed | Check |
| --- | --- | --- |
| add `design-system-foundations` as a distinct XD skill | not started, and **contradicted** — see below | no such directory in any pack; `packs/experience-design/.apm/skills/` holds 20 skills, none of them this |
| lightweight mode | not started | `lightweight mode` / `full mode` → 0 hits across `experience-design` and `frontend-engineering` |
| full mode (DTCG, light/dark, semantic aliases, component anatomy) | partial, wrong pack | the capability ships in `packs/frontend-engineering/.apm/skills/token-architecture/SKILL.md` (8 DTCG hits, a `## DTCG export` section, 4 light/dark, 3 semantic-alias), not in XD. `component anatomy` → 0 hits anywhere |
| keep taxonomy derivation and foundation implementation separate | not started | only one skill exists; `design-system/SKILL.md` states it "does not implement token values", so the implementation half has no XD owner |

**0 shipped · 1 partial · 3 not started.**

**This requirement contradicts an accepted decision.**
[ADR-0052](../../adr/0052-nine-experience-pack-skill-renames.md) (Accepted) D1
renamed `design-system-foundations` → `design-system`, on the reasoning that
"'-foundations' was a qualifier that added friction". RFC-0071 asks for the name
back. Two accepted records disagree, and this intent cannot be delivered until
one of them gives way. That is a decision, not an implementation task.

Separately, `design-system-foundations` is referenced by 4 shipped
`references/digital-experience-contract.md` copies although no such skill
exists — those references resolve to nothing today.

## Non-goals

- Generated Figma variables, iOS Swift UI tokens, and Android Material tokens are deferred until an adopter need surfaces (RFC-0071 Follow-on work).

## Open questions the RFC left

- The full-mode spec must set the DTCG 2025.10 compatibility posture and fallback for tooling that cannot export that format (RFC-0071 OQ1).

## What this absorbs

### design-system-foundations-skill-gap

RFC-0071 D3a accepted Option A: a new `design-system-foundations` skill. Implementation is tracked as `spec/xd-design-system-foundations` in `ini-003`. This entry closes when `spec/xd-design-system-foundations` ships.

Unblocks when: `spec/xd-design-system-foundations` is Shipped.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
