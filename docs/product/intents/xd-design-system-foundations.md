# Design system foundations for experience design

- **Slug:** `xd-design-system-foundations` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Fulfilled
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:digital-experience-doctrine
- **Milestone:** M3b in RFC-0071's implementation sequence
- **Governed by:** [RFC-0071 D3a](../../rfc/0071-digital-experience-doctrine.md)
- **De-risked:** no
- **Shaping-reviewed:** no
- **Decomposed:** 2026-09-27 spec
- **Accepted:** 2026-10-01 by eugenelim as a catch-up closure record ratifying ADR-0128's 2026-09-27 decision to use one `design-system` skill with four routes
- **Fulfilled:** 2026-10-01 by eugenelim as a catch-up closure record verified against the `design-system-values` spec shipped on 2026-09-28 and its current skill, guide, eval, construction-test, and release evidence

## Outcome

Experience-design practitioners can take an approved token taxonomy into a working design-system foundation, with a clear compatibility posture for the tools that consume it.

## Opportunity

Projects needed a clear way to turn an approved taxonomy into project-specific
values and relationships. ADR-0128 assigned that work to routes inside the
existing `design-system` method.

## Assumptions

- Resolved: ADR-0128 preserves the distinction as routes inside one skill rather
  than as separate skill registrations.

## Riskiest assumption

Settled by ADR-0128: one `design-system` skill with route-based depth can carry
the foundation outcome without reopening ADR-0052's alias-free rename or adding
a second registration.

## Original decision requirements

- Add `design-system-foundations` as a distinct `experience-design` skill: it takes a token taxonomy and establishes a working token foundation for a specific project (RFC-0071 D3a).
- Its lightweight mode covers semantic color roles, typography, spacing, radius, focus, key statuses, responsive rules, and core components (RFC-0071 Area D).
- Its full mode covers a DTCG 2025.10-compatible token source, light and dark themes, semantic aliases, full component anatomy, and generated platform outputs (RFC-0071 Area D).
- Keep taxonomy derivation and foundation implementation as separate jobs with distinct triggers, outputs, and reviewers (RFC-0071 D3a).

### Fulfilment evidence — 2026-10-01

Each row is a check against the live tree (`packs/`, `guides/`, `web/`,
`docs-site/`, `tools/`, `packages/`), re-runnable rather than trusted. Frozen
spec bodies under `docs/specs/` are historical records and were not counted as
evidence. This is an observation on a date, not a status field.

| Requirement | Current result | Evidence |
| --- | --- | --- |
| establish a working project foundation from approved design authority | fulfilled | `design-system` now resolves project-specific values and relationships from stated constraints, the approved direction, the incumbent system, platform convention, and derivation authority |
| support proportional depth | fulfilled by route rather than `lightweight` / `full` labels | `inherit`, `extend`, `originate`, and `refine` select the amount and kind of system work without adding a second registration |
| preserve compatibility with implementation consumers | fulfilled | the artifact remains `<output_dir>/tokens/<slug>.md` with `type: token-taxonomy`; downstream readers retain the same address and identity |
| keep taxonomy and foundation work distinct | superseded in form, fulfilled in outcome | ADR-0128 explicitly replaces the two-skill requirement with four routes inside one `design-system` skill and records the accepted trade-off |

**This requirement contradicted an accepted decision, and
[ADR-0128](../../adr/0128-design-system-one-skill-resolves-project-values.md)
now answers it.**
[ADR-0052](../../adr/0052-nine-experience-pack-skill-renames.md) (Accepted) D1
renamed `design-system-foundations` → `design-system`, on the reasoning that
"'-foundations' was a qualifier that added friction". RFC-0071 asks for the name
back. ADR-0128 keeps ADR-0052's name and carries D3a's capability as four
routes inside the one skill, so the foundation half gains an owner without a
second registration. Read ADR-0128 for what that costs: D3a's requirement for
distinct triggers, outputs, and reviewers is the part not met.

Separately, four shipped `digital-experience-contract.md` copies still use the
old `design-system-foundations` wording. ADR-0128 records that residual; it is a
contract-vocabulary repair and does not reopen this delivered outcome.

### Current-standards pressure test — 2026-10-01

The [external survey](../research/digital-experience-doctrine-current-standards-survey.md)
keeps this intent Fulfilled. DTCG 2025.10 is a stable Final Community Group
Report intended for implementation, but it is not a W3C Standard and tool
support remains uneven. The delivered Markdown artifact is design authority,
not a DTCG interchange file. An adopter that needs cross-tool travel must
serialize and validate `.tokens`, `.tokens.json`, and optional `.resolver.json`
outputs against DTCG 2025.10 and the target tool. That is a separate
interoperability seam, not unfinished value-resolution work.

## Non-goals

- Generated Figma variables, iOS Swift UI tokens, and Android Material tokens are deferred until an adopter need surfaces (RFC-0071 Follow-on work).

## Superseded open question

- RFC-0071 asked a future full-mode spec to set a DTCG 2025.10 compatibility
  posture and fallback. ADR-0128 replaced the lightweight/full-mode shape with
  route-based depth. Tool-specific generated exports remain a non-goal until an
  adopter need surfaces.

## Decomposition

Delivered by the one same-repository
[`design-system-values`](../../specs/design-system-values/spec.md) spec and
plan. No delivery brief or further slice belongs to this intent. Reopen only if
the accepted route boundary fails; DTCG serialization stays a separate adapter
or interoperability feature.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
