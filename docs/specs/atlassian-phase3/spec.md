---
**Feature:** atlassian-phase3
**Status:** Shipped
**Mode:** full (multi-feature, structural/public-interface, unfamiliar territory)
---

# Atlassian Phase 3 — Product Documentation Pilot

## Objective

Deliver the Atlassian pack as the first complete end-to-end pilot of the Product Documentation architecture (Phases 1–2D). Retrofit the Atlassian public experience so a first-time user can discover, understand, and act on the canonical whole-team-backlog workflow across six connected surfaces, without knowing a skill name.

## Boundaries

**In scope:**
- Six public surfaces: tutorial, how-to, pack README, canonical journey, skills reference, pack explanation
- One canonical Team Atlas scenario shared across all six surfaces
- JOURNEY.md for the atlassian pack (canonical pack-owned journey source)
- Retrofitting four existing guide files to use flat source paths with Phase 2A metadata
- Updating pack page data (`web/src/content/packs/atlassian.md`) body
- Updating sidebar (`docs-site/astro.config.ts`) to reflect new labels and new `how-the-atlassian-pack-works` page
- No pack version bump — documentation-only change, no skill content changed
- Full build validation: `validate_guides.py`, `lint-pack-journeys.py`, `build-site.py`, `make build-check`

**Not in scope:**
- Changing Atlassian skill behavior beyond verified Phase 2D integration
- Retrofitting other packs
- Migrating every journey
- Redesigning the global marketing homepage
- Creating a second guide schema, journey model, or component library
- Publishing to any live Jira or Confluence instance
- Deleting or restructuring `docs/guides/` maintainer content

## Assumptions

1. `packs/atlassian/.apm/skills/` contains exactly 11 skills; JOURNEY.md must list all 11 (count-parity lint rule).
2. The `docs-site/astro.config.ts` sidebar is hardcoded; every new or renamed page requires a manual entry.
3. The hand-authored `web/src/content/journeys/atlassian.md` must be deleted before `--journeys-only` runs (dual-ownership lint aborts the build if a non-generated central file shares pack name with a JOURNEY.md).
4. `slug:` frontmatter on flat guide files preserves public URLs without needing `aliases:`.
5. The `lint-pack-journeys.py` linter requires `**Output:**` and `**State:**` labels in each stage body; write stages also require `**You decide:**`.
6. `web/src/content/packs/atlassian.md` body (markdown rendered via `<Content />`) is the prose the pack page renders — it is separate from the skills array in frontmatter.

**Declined patterns:**
- Tempted to create a second component library for the docs-site renderer — declining; reuse the existing Phase 2C primitives from `web/src/components/primitives/`.
- Tempted to auto-generate the sidebar from guide frontmatter — declining; that is a separate architectural change not in scope.
- Tempted to change the `[journey].astro` template to support a different skills array format — declining; JOURNEY.md must conform to the existing schema.
- Tempted to add navigation auto-generation for guides — declining; hardcoded sidebar is existing convention.

## Source ownership

| Surface | Canonical source | Do not edit |
|---|---|---|
| Tutorial | `guides/atlassian/review-your-team-backlog.md` | generated `docs-site/src/content/docs/guides/` |
| How-to | `guides/atlassian/work-with-jira.md` | (same as above) |
| Skills reference | `guides/atlassian/atlassian-skills.md` | (same as above) |
| Explanation | `guides/atlassian/how-the-atlassian-pack-works.md` | (same as above) |
| Pack README | `packs/atlassian/README.md` | generated marketplace/projected output |
| Journey | `packs/atlassian/JOURNEY.md` | `web/src/content/journeys/atlassian.md` (generated) |
| Pack page body | `web/src/content/packs/atlassian.md` | `web/src/pages/packs/[pack].astro` |
| Canonical scenario | `packs/atlassian/docs/canonical-scenario.json` | (not a rendered page) |

## Public routes (preserved or established)

| Surface | Public route |
|---|---|
| Tutorial | `/agent-ready-repo/docs/guides/atlassian/tutorials/review-your-team-backlog/` |
| How-to | `/agent-ready-repo/docs/guides/atlassian/how-to/work-with-jira/` |
| Skills reference | `/agent-ready-repo/docs/guides/atlassian/reference/atlassian-skills/` |
| Explanation | `/agent-ready-repo/docs/guides/atlassian/explanation/atlassian-pack/` |
| Pack page | `/packs/atlassian/` |
| Journey | `/journeys/atlassian/` |

## Acceptance Criteria

- [x] AC1: Phase 1 and Phase 2A–2D prerequisites verified in source (pre-flight gate)
- [x] AC2: `author-product-docs` used in retrofit mode to establish the shared documentation contract
- [x] AC3: One canonical Team Atlas scenario (`packs/atlassian/docs/canonical-scenario.json`) drives all six surfaces — same counts, issue IDs, classifications, draft rewrites everywhere
- [x] AC4: Tutorial provides a complete 17-step start-to-finish experience including partial failure and recovery
- [x] AC5: Tutorial first useful request appears within 120 words
- [x] AC6: How-to exposes 7 common tasks without duplicating the tutorial; starts with "Review the whole team backlog"
- [x] AC7: How-to states plainly that reviewing and drafting do not change Jira
- [x] AC8: Pack README leads with "Run Jira and Confluence from a conversation" headline and "Starts read-only" trust indicator above the fold
- [x] AC9: Pack page shows four primary jobs before skill inventory
- [x] AC10: Journey page shows four connected stages (see / improve / act / communicate) before implementation inventory
- [x] AC11: Journey `packs/atlassian/JOURNEY.md` lists all 11 skills; `lint-pack-journeys.py` exits 0
- [x] AC12: Skills reference provides intent index before alphabetical records; complete entries for `jira-team-status`, `jira-story-triage`, `jira`, `confluence-publisher`
- [x] AC13: Explanation uses Ask→Orient→Improve→Act→Measure-or-Share mental model with one system diagram
- [x] AC14: Users can begin the canonical workflow without knowing a skill name (cold-read test: first request within 120 words on every surface)
- [x] AC15: Orientation is read-only; story improvements are draft-only until approval; exact writes require confirmation
- [x] AC16: Protected fields (status, assignee, sprint, priority, labels) documented as unchanged; partial failure has visible recovery path
- [x] AC17: Confluence publishing explicitly requires approval; not automatic
- [x] AC18: "Ready to pull" defined once; general team readiness not confused with Jira `To Do` status
- [x] AC19: "Agent-ready" only appears when the optional coding-agent lens is explicitly selected
- [x] AC20: All four retrofitted guide files use flat source paths with valid Phase 2A frontmatter (`title`, `summary`, `pack: atlassian`, `kind`, `slug:`); `validate_guides.py` exits 0
- [x] AC21: Old subdirectory guide files deleted; no duplicate canonical sources
- [x] AC22: `web/src/content/journeys/atlassian.md` (hand-authored) deleted; generated replacement produced by `--journeys-only`
- [x] AC23: `docs-site/astro.config.ts` sidebar updated to include `how-the-atlassian-pack-works` and correct labels
- [x] AC24: `packs/atlassian/pack.toml` version not bumped — documentation-only change, no skill content changed (user-confirmed)
- [x] AC25: `JOURNEY.md` write stages carry `**You decide:**` label; `lint-pack-journeys.py` exits 0
- [x] AC26: `build-site.py` full build exits 0; `make build-check` exits 0
- [x] AC27: Pack page links to journey and tutorial; tutorial links to how-to, reference, explanation; cross-linking complete
- [x] AC28: Terminology is consistent across all six surfaces (shared vocabulary list from brief)
- [x] AC29: `adversarial-reviewer` returns `Clean — ready to commit.`
- [x] AC30: No unrelated catalogue-wide migration or homepage redesign pulled in

## Testing Strategy

**Goal-based verification for all content surfaces:**

For each guide file:
```bash
python tools/validate_guides.py guides/atlassian/<file>.md
# Exit 0 required
```

For JOURNEY.md:
```bash
python tools/lint-pack-journeys.py
# Exit 0 required
```

Full build:
```bash
python tools/build-site.py
make build-check
```

Additional lint:
```bash
python tools/lint-skill-spec.py  # if exists
python .claude/skills/work-loop/scripts/lint-spec-status.py
```

**Manual verification:**
- Cold-read: does the first useful request appear within 120 words on every surface?
- Does orientation state "Jira was not changed" without a skill name visible?
- Is the write boundary visible before any confirmation step?
- Cross-link spot-check: follow links between all 6 surfaces
