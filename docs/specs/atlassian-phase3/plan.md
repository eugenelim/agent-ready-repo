# Atlassian Phase 3 — Implementation Plan

## Status: Done

## Tasks

### Task 1 — Create canonical scenario source
**Verification mode:** goal-based
**Done when:** `packs/atlassian/docs/canonical-scenario.json` exists and contains all required fixture data (counts, issue IDs, titles, classifications, draft rewrites, protected fields, partial-failure example).
**Touches:** `packs/atlassian/docs/canonical-scenario.json` (new)

### Task 2 — Write tutorial
**Verification mode:** goal-based
**Done when:** `guides/atlassian/review-your-team-backlog.md` exists with valid frontmatter (`slug: guides/atlassian/tutorials/review-your-team-backlog`), 17-step complete journey, canonical scenario numbers and issue IDs, `validate_guides.py` exits 0 on the file.
**Touches:** `guides/atlassian/review-your-team-backlog.md` (new flat), `guides/atlassian/tutorials/review-your-team-backlog.md` (delete)

### Task 3 — Write how-to
**Verification mode:** goal-based
**Done when:** `guides/atlassian/work-with-jira.md` exists with valid frontmatter (`slug: guides/atlassian/how-to/work-with-jira`), 7 tasks, task selector, Review→Draft→Approve→Write progression, `validate_guides.py` exits 0.
**Touches:** `guides/atlassian/work-with-jira.md` (new flat), `guides/atlassian/how-to/work-with-jira.md` (delete)

### Task 4 — Write skills reference
**Verification mode:** goal-based
**Done when:** `guides/atlassian/atlassian-skills.md` exists with valid frontmatter (`slug: guides/atlassian/reference/atlassian-skills`), intent index, complete SkillRecord entries for jira-team-status/jira-story-triage/jira/confluence-publisher, `validate_guides.py` exits 0.
**Touches:** `guides/atlassian/atlassian-skills.md` (new flat), `guides/atlassian/reference/atlassian-skills.md` (delete)

### Task 5 — Write explanation
**Verification mode:** goal-based
**Done when:** `guides/atlassian/how-the-atlassian-pack-works.md` exists with valid frontmatter (`slug: guides/atlassian/explanation/atlassian-pack`), system diagram, composition narrative, `validate_guides.py` exits 0.
**Touches:** `guides/atlassian/how-the-atlassian-pack-works.md` (new flat), `guides/atlassian/explanation/atlassian-pack.md` (delete)

### Task 6 — Retrofit pack README
**Verification mode:** goal-based
**Done when:** `packs/atlassian/README.md` leads with outcome headline, four primary jobs, connected journey, "Starts read-only" trust indicator, skills below journey.

### Task 7 — Create JOURNEY.md
**Verification mode:** goal-based
**Done when:** `packs/atlassian/JOURNEY.md` exists with all required frontmatter fields (journey_id, pack, start_state, end_state, scope, tagline, contract, all 11 skills, humanGates, typicalSession, docsUrl, packUrl, relatedJourneys), 4 stage bodies with `**Output:**` and `**State:**` labels, write stages with `**You decide:**`, `lint-pack-journeys.py` exits 0.

### Task 8 — Update pack page data
**Verification mode:** goal-based
**Done when:** `web/src/content/packs/atlassian.md` body reflects new experience (outcome-led, four jobs, journey section, skills under the hood), `journeyUrl` present in frontmatter.

### Task 9 — Integration
**Verification mode:** goal-based
**Done when:**
- Old subdirectory guide files deleted
- `web/src/content/journeys/atlassian.md` (hand-authored) deleted
- `docs-site/astro.config.ts` sidebar updated
- `packs/atlassian/pack.toml` version unchanged at 0.7.0 (documentation-only change; AC24 user-confirmed no bump)
- `python tools/build-site.py --journeys-only` exits 0 and generates `web/src/content/journeys/atlassian.md`
- `python tools/build-site.py` exits 0
- `make build-check` exits 0

### Task 10 — Full gates pass
**Verification mode:** goal-based
**Done when:** `validate_guides.py guides/atlassian/`, `lint-pack-journeys.py`, `build-site.py`, `make build-check` all exit 0.

### Task 11 — Review
**Done when:** `adversarial-reviewer` returns `Clean — ready to commit.`
