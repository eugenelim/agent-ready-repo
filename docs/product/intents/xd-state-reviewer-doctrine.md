# Experience state and reviewer doctrine

- **Slug:** `xd-state-reviewer-doctrine` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** [Digital experience doctrine](digital-experience-doctrine.md)
- **Milestone:** M3d in RFC-0071's implementation sequence
- **Governed by:** [RFC-0071 § Implementation sequence — M3d](../../rfc/0071-digital-experience-doctrine.md)

## Outcome

Teams can assess an experience across its required states and use an experience reviewer that examines cold-read comprehension, task completion, and contract conformance.

## Opportunity

The current experience-reviewer and quality floor do not cover the needed state set or provide the three complementary review passes required for a reliable experience evaluation.

## Assumptions

- Information-architecture object and state guidance will provide the reviewer’s shared surface model.

## What the decision requires

- Extend `quality-floor.md` from 8 to 18 states (RFC-0071 Area D / M3d).
- Restructure `design-review` (`experience-reviewer`) into cold-read, task-completion, and contract-review passes (RFC-0071 Area D).
- Use blocker, concern, and suggestion severity tiers, and require rendered evidence when a rendered surface exists (RFC-0071 Area D).
- Deliver M3d after M3c in the accepted implementation sequence (RFC-0071 § Implementation sequence).

### Observed state — 2026-09-20

Each row is a check against the live tree (`packs/`, `guides/`, `web/`,
`docs-site/`, `tools/`, `packages/`), re-runnable rather than trusted. Frozen
spec bodies under `docs/specs/` are historical records and were not counted as
evidence. This is an observation on a date, not a status field.

| Requirement | Observed | Check |
| --- | --- | --- |
| extend `quality-floor.md` from 8 to 18 states | not started in XD, shipped in FE | XD's `design-review/references/quality-floor.md` lists **7** states. All 18 exist only in `packs/frontend-engineering` and `guides/frontend-engineering` (`18 state` → 7 hits, none in XD). The intent's own baseline of "8" is itself stale — the live floor has 7 |
| restructure the reviewers into cold-read / task-completion / contract-review passes | not started | `design-review/SKILL.md` runs steps 0-7 on a different structure; `cold.read` → 10 hits, none in `packs/experience-design`; `task-completion pass` / `contract-review pass` → 0 |
| blocker / concern / suggestion tiers, rendered evidence required | partial, wrong tiers | the shipped ladder is blocker / major / minor / nit plus a 0-4 rubric. `suggestion tier` → 0 hits in XD. The reviewer's "Confirm before reviewing" gate does not require a render |
| deliver M3d after M3c | not started | neither this spec nor its M3c predecessor exists |

**0 shipped · 2 partial · 2 not started.**

The state-set split is the one to watch: XD's `user-flow` state matrix and
frontend-engineering's audit currently run against different state sets, 7
against 18.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
