# Experience state and reviewer doctrine

- **Slug:** `xd-state-reviewer-doctrine` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:digital-experience-doctrine
- **Milestone:** M3d in RFC-0071's implementation sequence
- **Governed by:** [RFC-0071 § Implementation sequence — M3d](../../rfc/0071-digital-experience-doctrine.md)
- **De-risked:** no
- **Shaping-reviewed:** no
- **Decomposed:** 2026-10-01 spec

## Outcome

Teams can assess an experience across its required states and use an experience reviewer that examines cold-read comprehension, task completion, and contract conformance.

## Opportunity

The current experience-reviewer and quality floor do not cover the needed state set or provide the three complementary review passes required for a reliable experience evaluation.

## Assumptions

- The approved M3c spec must pin the archetype, object, role, action, branch, and artifact contract that this reviewer consumes; until then, its applicability algorithm has no stable input contract.
- **Knowledge surface:** the in-repository RFC, pack, guide, contract, and spec corpus plus the 2026-10-01 current-standards survey.

## Riskiest assumption

Once M3c supplies the shared archetype, object, role, action, and branch model,
the reviewer can derive applicable states and required evidence without this
feature becoming a browser-automation runtime.

## What the decision requires

- Extend the shared quality floor to the 18-state taxonomy in RFC-0071 (Area D
  / M3d). Eighteen is a versioned local minimum, not a standards-derived
  closed set or ceiling.
- Restructure `design-review` (`experience-reviewer`) into cold-read, task-completion, and contract-review passes (RFC-0071 Area D).
- Use blocker, concern, and suggestion severity tiers, and require rendered
  evidence when a rendered surface exists (RFC-0071 Area D). Severity remains
  separate from WCAG A/AA/AAA conformance levels.
- Deliver M3d after M3c in the accepted implementation sequence (RFC-0071 § Implementation sequence).

### Observed state — 2026-10-01

Each row is a check against the live tree (`packs/`, `guides/`, `web/`,
`docs-site/`, `tools/`, `packages/`), re-runnable rather than trusted. Frozen
spec bodies under `docs/specs/` are historical records and were not counted as
evidence. This is an observation on a date, not a status field.

| Requirement | Observed | Check |
| --- | --- | --- |
| extend XD state doctrine to the shared 18-state set | partial | `design-review` now loads the Digital Experience Contract's shared state-coverage map and grades only the states a surface owes. The standalone quality floor still lists seven states, so XD has two state descriptions instead of one unambiguous contract |
| restructure the reviewers into cold-read / task-completion / contract-review passes | not started | `design-review/SKILL.md` runs steps 0-7 on a different structure; `cold.read` → 10 hits, none in `packs/experience-design`; `task-completion pass` / `contract-review pass` → 0 |
| blocker / concern / suggestion tiers, rendered evidence required | partial, wrong contract | the experience reviewer uses blocker / major / minor / nit and accepts design artifacts without requiring rendered evidence. Frontend's independent reviewer does inspect rendered output, but it does not replace the experience-review contract this intent owns |
| deliver M3d after M3c | blocked by M3c | no spec exists for either intent; the dependency remains valid |

**0 shipped · 2 partial · 1 not started · 1 blocked.**

The shared contract reduced the original state-set split, but it did not remove
it: the review procedure reads eighteen states while the local quality-floor
reference still presents seven.

### Current-standards pressure test — 2026-10-01

The [external survey](../research/digital-experience-doctrine-current-standards-survey.md)
confirms the M3c dependency and the three-pass shape. Derive applicable states
from the archetype, object, role, action, and branch contract. Pin WCAG 2.2 and
WAI-ARIA 1.2 as current baselines; monitor ARIA 1.3 without treating its Working
Draft as authority. Rendered evidence includes the relevant visual state, a
task or keyboard trace, and accessible role/name/state evidence. ARIA-dependent
checks record the target browser and assistive-technology baseline.

### Spec-authoring dependency

Refresh and de-risk this intent after the M3c spec is approved. That contract,
not M3c's implementation, is the minimum input needed to decide how applicable
states are derived and to test whether the three review passes stay bounded.
Authoring this spec first would force it to invent the upstream object and
branch model it is meant to consume.

## Non-goals

- Building a general screenshot, browser automation, or accessibility testing
  platform.
- Treating the local 18-state map as a W3C or ARIA taxonomy.
- Replacing frontend-engineering's independent rendered-page reviewer.

## Decomposition

One same-repository spec and plan at
`docs/specs/xd-state-reviewer-doctrine/` own the M3d outcome after M3c ships.
They make the state source unambiguous, establish the cold-read,
task-completion, and contract-review passes, and align severity and evidence
requirements across `design-review` and the independent experience reviewer.
This remains one feature because all surfaces implement one reproducible review
contract. Re-decompose if a general browser-automation runtime becomes a
product of the work rather than a proving fixture.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
