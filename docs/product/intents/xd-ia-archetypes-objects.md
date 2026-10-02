# Information architecture archetypes and objects

- **Slug:** `xd-ia-archetypes-objects` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Accepted
- **Accepted:** 2026-10-01 by eugenelim, lifecycle owner. Revision `c8eb6d0cb3c1cede` returned zero `MALFORMED` tokens in an independent intent-mode shaping review, and a fresh adversarial intent read returned no material open question or replacement validation hook. The feature-level assumption survived its predeclared kill condition, and the remaining work stays one feature projected to one spec and plan.
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:digital-experience-doctrine
- **Milestone:** M3c in RFC-0071's implementation sequence
- **Governed by:** [RFC-0071 § Implementation sequence — M3c](../../rfc/0071-digital-experience-doctrine.md)
- **De-risked:** 2026-10-01
- **Shaping-reviewed:** 2026-10-01
- **Decomposed:** 2026-10-01 spec

## Outcome

- **Input (steerable):** the share of IA artifacts that bind surface genre to a task/page archetype and explicitly name the product object, authorized action, attention priority, and navigation behavior.
- **Outcome (lagging):** Experience Design and Frontend Engineering can derive a coherent surface, its available and denied actions, and its next-step structure without reconstructing the product model or confusing page purpose with visual genre.
- **Guardrail:** the method presents authoritative product policy but never becomes its enforcement layer, and it extends rather than replaces the shipped seven-genre router and per-screen contract.

## Opportunity

- **Functional job:** turn a surface's purpose and product model into a hierarchy of objects, actions, attention, and navigation that a user can understand and use.
- **Emotional job:** trust that the screen is organized around the user's task and authority rather than around the data schema or the design method's preferred layout.
- **Social job:** give design, product, security, and engineering a shared explanation of what the surface shows and permits without claiming that the UI enforces policy.
- **Struggling moment:** genre routing now selects a structural method, but no shared archetype and product-object contract connects that genre to page purpose, available actions, denied behavior, and navigation across the resulting screens.

## Product-to-experience handoff

- **Affected journey or surface:** every product surface whose page purpose, core object, available action, and next step must be made explicit before screen design.
- **User outcome and first-success behavior:** the user recognizes the object and state, understands the primary available action, and reaches the expected result or a recoverable denied/unavailable path.
- **Product mechanism or proof:** object identity and state, subject or role, action, relevant context, available result, denied behavior, attention priority, and navigation behavior.
- **Evidence for user-visible claims:** object, action, and authorization statements point to the product or service authority they present; unsupported policy claims remain unknown rather than being invented by design.
- **Constraints, prohibited claims, and material unknowns:** the UI may explain or reflect authoritative policy but cannot define or enforce it; genre, archetype, platform, and semantic landmarks remain distinct axes.

## Assumptions

- The shipped XD skill-boundary and genre-consolidation work leave `information-architecture` as the structural owner, with `user-flow`, `interaction-design`, and `design-review` as downstream consumers or enrichers. The repository probe below survived; practitioner fit remains `to-validate`.
- **Knowledge surface:** the in-repository RFC, pack, guide, contract, and spec corpus plus the 2026-10-01 current-standards survey.

## Riskiest assumption

Experience Design can own a single method for archetype, product object,
attention, authorized action, and navigation decisions without becoming the
security-policy enforcement layer.

## De-risk record — 2026-10-01

- **Level kind:** feature, so the dominant risk is whether practitioners can use one IA method to make the five connected decisions without confusing its axes or inventing policy.
- **Reversibility triage:** one-way door because the taxonomy and artifact fields become published inputs to user-flow, interaction, review, and frontend implementation.
- **Prototype approach:** `validate-first`; the cheapest failing probe was an ownership and artifact walk across the live Experience Design methods.

### Kill condition, predeclared

Kill or reframe if archetype, product object, attention, authorized action, and navigation cannot each map to an existing XD owner and shared artifact without duplicating the genre axis or enforcing security policy.

### Probe and verdict — survived

- `information-architecture` already owns hierarchy, disclosure, navigation structure, wayfinding, state-sensitive layout, one IA artifact, and the seven-genre routing axis. A task/page archetype can therefore refine page purpose without replacing genre.
- The per-screen brief already carries data and actions, including failed-action routes and `permission/denied`; `user-flow` owns cross-screen sequence and state applicability; `interaction-design` owns action behavior and navigation transitions. Those are downstream enrichers, not competing owners of the IA decision.
- The genre references already carry attention patterns, while the Digital Experience Contract names Surface Map, Information Architecture, Product Objects, Interaction and Attention Model, and States and Permissions as one Experience Design handoff.
- Existing language consistently treats authorization as an external authority the UI presents: denied behavior is designed, while roles, policy, and service enforcement stay outside IA.

All five concerns have an owner and a crossing artifact, and the genre/archetype and presentation/enforcement boundaries remain distinct. No kill arm fired. The spec must pin the seed catalogue and field contract, not create a policy engine or a second genre router.

### Validation hook

```yaml
validation_hook:
  assumption: Practitioners can use one IA method to distinguish genre from archetype and connect object, action, attention, authorization presentation, and navigation without inventing policy.
  kill_condition: Reframe if two or more of six representative surfaces cannot be described with a distinct genre and archetype plus one authoritative object/action/navigation contract, or if a practitioner must invent access policy to complete the artifact.
  activity: to-validate — test the seed catalogue on six real product surfaces spanning at least four genres with an information architect and an implementation reviewer; record collisions, missing archetypes, and policy inventions before accepting the spec's catalogue.
```

## What the decision requires

- Add `references/page-archetypes.md` with at least 12 surface types (RFC-0071
  Area D / M3c). Twelve is a local seed-catalogue minimum, not an industry
  taxonomy or exhaustive ceiling.
- Keep four axes distinct: surface genre, task/page archetype, semantic regions
  and landmarks, and product object plus authorized action.
- For each archetype, record its primary user, job, entry condition,
  first-screen contract, object identity and state, primary authorized action,
  expected result, critical alternative branches, next action, proof,
  unavailable or denied behavior, critical states, and navigation behavior.
- Add product-object mapping guidance and an attention contract. Interpret the
  RFC's read/write permission pair as the minimum of an action and
  authorization contract that records subject or role, object or resource,
  action, relevant context, available result, and denied or unavailable
  behavior. UI guidance presents authoritative policy; it does not enforce it.
- Deliver M3c after M3a and before M3d in the accepted implementation sequence (RFC-0071 § Implementation sequence).

### Observed state — 2026-10-01

Each row is a check against the live tree (`packs/`, `guides/`, `web/`,
`docs-site/`, `tools/`, `packages/`), re-runnable rather than trusted. Frozen
spec bodies under `docs/specs/` are historical records and were not counted as
evidence. This is an observation on a date, not a status field.

| Requirement | Observed | Check |
| --- | --- | --- |
| `references/page-archetypes.md` with ≥12 surface types | not started, but the starting structure changed | no file of that name exists. `information-architecture` now routes seven surface genres, but genre method is a broader axis than the twelve or more page archetypes this outcome requires. Four contract copies still reference the missing taxonomy |
| per-archetype field set | partial, wrong pack and wrong axis | the field set ships as a **per-screen** contract in `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md:368-386` (12 fields). No archetype axis, no navigation-behavior field, nothing equivalent in `packs/experience-design` |
| product-object mapping, attention contract, permission contract in the relevant skills | partial, template only | the three headings exist in the contract template copies. In XD skill bodies: `product object` → 0 hits, `attention contract` → 0, `permission contract` → 0 |
| deliver M3c after M3a, before M3d | ready to shape | M3a and the later genre consolidation are Shipped; no spec exists for this intent, and M3d still depends on it |

**0 shipped · 2 partial · 1 not started · 1 ready to shape.**

### Current-standards pressure test — 2026-10-01

The [external survey](../research/digital-experience-doctrine-current-standards-survey.md)
found no external canonical archetype count. The spec must validate the local
seed catalogue against representative product surfaces rather than claim that
twelve is universal.

## Non-goals

- Building an authorization engine or enforcing product policy.
- Declaring the twelve archetypes to be an external standard or exhaustive
  industry taxonomy.
- Replacing the shipped seven-genre router or frontend per-screen contract.

## Decomposition

One same-repository spec and plan at
`docs/specs/xd-ia-archetypes-objects/` own the M3c outcome: add the archetype
taxonomy and put product-object, attention, action, authorization, and
navigation reasoning into the relevant live experience-design methods without
duplicating the shipped seven-genre router. This remains one feature because
all five concerns establish one IA decision method. Re-decompose if security
policy enforcement or a standalone authorization engine enters scope.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
