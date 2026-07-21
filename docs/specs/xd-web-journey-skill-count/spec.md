---
**Feature:** xd-web-journey-skill-count
**Status:** Shipped
**Mode:** light (no risk trigger fired)
---

## Objective

Update `web/src/content/journeys/experience-design.md` to reflect the 9 skills added since the last journey update (6 genre-specific Direct skills + 3 connective/decision skills). The `skills:` frontmatter listed 9; the pack now has 18 (19 directory entries minus `experience-status`, which is a workflow/orient tool, not a design skill). Also update `whatChanges` text and stage prose to reflect the full chain.

## Testing Strategy

Goal-based check: `npm run build` passes (Astro Zod schema validates the frontmatter) and the rendered experience-design journey page reflects 18 skills.

## Acceptance Criteria

- [x] `skills:` frontmatter lists all 18 skills (9 original + 9 new: `analytical-design`, `content-design`, `conversion-design`, `design-principles`, `documentation-design`, `informational-design`, `marketplace-design`, `tone-of-voice`, `workspace-design`)
- [x] `whatChanges` text names the genre-specific skills and the connective thread (`content-design`, `tone-of-voice`, `design-principles`)
- [x] Stage 1 prose mentions `content-design` and `tone-of-voice` as connective-thread skills that run after journey-mapping
- [x] Stage 3 prose mentions `design-principles` as the decision-rules step before `creative-direction`
- [x] Stage 4 prose names each genre-specific Direct skill with its surface genre trigger

## Tasks

1. Update `skills:` frontmatter in `web/src/content/journeys/experience-design.md` — add 9 skills in workflow order
2. Update `whatChanges:` field to name genre-specific skills and connective thread
3. Update Stage 1 prose to mention `content-design` + `tone-of-voice`
4. Update Stage 3 prose to mention `design-principles`
5. Update Stage 4 prose to name genre-specific Direct skills with genre triggers
