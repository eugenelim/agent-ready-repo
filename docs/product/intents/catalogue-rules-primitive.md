# Catalogue rules primitive

- **Status:** Draft
- **Level:** feature

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

## Source

- Mode: repo-origin
- Locator: docs/specs/cognitive-load-reduction/notes/guidance-pointer-patterns-survey.md
- Revision: local-2026-08-27
