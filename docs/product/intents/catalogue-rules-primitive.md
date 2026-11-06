# Catalogue rules primitive

- **Slug:** `catalogue-rules-primitive`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim

## Outcome

Authors define a portable rule once and the catalogue projects it to each
supported adapter's native repository or user rule surface without duplicating
the source prose.

## Opportunity

The catalogue has no rule primitive today. Repository-wide behavior must use
shared context-file pointers, while native rule and steering files remain
adapter-specific and cannot be generated from one owned source.

## Assumptions

- Use `.apm/rules/` as the canonical authoring area.
- Adopt `.agents/rules/` as the shared fallback projection and manage bounded
  route rows in `AGENT_RULES.md`.
- Specify repository and user scope, precedence, path matching, and always-on
  behavior as typed contract data.
- Preserve adopter-owned singleton context files. Define merge, import, or
  refusal behavior before adding a projection that can touch one.
- Avoid loading the same rule through both root context and a native projection.
- Keep the current cognitive-load change independent. It uses the same router
  and shared fallback paths as seed-owned lookups until this primitive assumes
  their generation and migration contract.

## Current state — checked 2026-11-05

`.apm/rules/` and `.agents/rules/` do not exist in this repository, and `AGENT_RULES.md` exists as the shipped router with an empty row table. The primitive is still unbuilt.

## Readiness

- **Route:** brief, and an RFC first. A new primitive type is a one-way change to the pack contract, and its five assumptions above are design choices that nothing here has tested.
- **Parked:** no named consumer asks for this today. Do not start it until the owner names one or the cognitive-load work needs generated routing.
- **Proposed slices when started, in order:** (1) RFC and contract: typed rule data, scope, precedence, always-on, and refusal behaviour for adopter-owned singleton files; (2) authoring area and lint for `.apm/rules/`; (3) the shared fallback projection to `.agents/rules/` and managed route rows; (4) one native adapter per session.
- **Agent-only proof for slice 1:** a per-adapter survey from `docs/specs/cognitive-load-reduction/notes/guidance-pointer-patterns-survey.md` plus a contract schema with positive and negative fixtures.

## Source

- Mode: repo-origin
- Locator: docs/specs/cognitive-load-reduction/notes/guidance-pointer-patterns-survey.md
- Revision: local-2026-08-27
