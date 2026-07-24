---
**Feature:** atlassian-docs-retrofit
**Status:** In Progress
**Mode:** Full (multi-feature, structural change, user-facing surface)
---

# Spec: Atlassian documentation retrofit

## Objective

Retrofit the complete Atlassian documentation experience across six pages so a
first-time user can understand what the pack does, naturally ask for their team's
whole backlog, see what is ready or blocked, improve weak stories, approve specific
writes, and communicate the result.

## Acceptance Criteria

- [x] AC1. Tutorial contains one complete coherent start-to-finish backlog journey.
- [x] AC2. The other five pages derive from or link to that journey.
- [x] AC3. A user can begin without knowing a skill name.
- [x] AC4. Every task-oriented page shows a natural request near the top.
- [x] AC5. Every primary request shows a realistic expected result.
- [x] AC6. Read, draft, proposed-write, confirmed-write, and publish boundaries are explicit.
- [x] AC7. A request for the "whole backlog" states scope and result completeness.
- [x] AC8. "Ready to pull" is defined as product readiness, not merely Jira status.
- [x] AC9. The five-question bar is preserved from the canonical source.
- [x] AC10. No Jira write is implied during orientation or drafting.
- [x] AC11. Pack page leads with user jobs and product proof rather than inventory.
- [x] AC12. Journey page presents four connected stages before generated skill cards.
- [x] AC13. Reference page provides exact inputs, reads, writes, outputs, limits, coverage, and approval behavior.
- [x] AC14. Explanation page teaches workflow composition without repeating a procedural guide.
- [x] AC15. Six pages use consistent terminology, sample data (Team Atlas), and visual states.
- [x] AC16. MkDocs and Astro surfaces feel like parts of the same product.
- [x] AC17. Public URLs and links remain valid.
- [x] AC18. Tutorial is added to MkDocs nav.

## Surfaces changed

1. `docs/guides/atlassian/tutorials/review-your-team-backlog.md` — new
2. `docs/guides/atlassian/how-to/work-with-jira.md` — rewrite
3. `web/src/content/packs/atlassian.md` — frontmatter + body rewrite
4. `web/src/content/journeys/atlassian.md` — frontmatter + body rewrite
5. `docs/guides/atlassian/reference/atlassian-skills.md` — major rewrite
6. `docs/guides/atlassian/explanation/atlassian-pack.md` — major rewrite
7. `site/mkdocs.yml` — nav update (add tutorial)

## Shared example dataset

Team: Atlas · Projects: APP and API · Sprint 24
- Ready to pull (3): APP-203, APP-211, API-98
- In progress (2): APP-198, API-92
- Needs story work (3): APP-206, APP-219, API-104
- Blocked (2): APP-215, API-101
- Unassigned (2): APP-220, API-107
- Approved writes: APP-206, APP-219, API-104

## Canonical journey

1. ORIENT — see everything available to the team (read-only)
2. IMPROVE — make weak stories actionable (draft, no write)
3. APPROVE AND ACT — apply only explicitly approved Jira changes
4. COMMUNICATE — produce a stand-up or Confluence-ready summary
