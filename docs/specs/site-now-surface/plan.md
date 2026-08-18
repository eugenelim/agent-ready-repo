# Plan: Site Now surface

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; substantive changes are recorded below.

## Approach

Extend the existing changelog contract with an optional relative Highlights
subsection, build a deterministic released-only projection, and then replace
the public work index with `/now/`. Seed launch content from the approved
seven-day released window and prove emitted content never leaks Unreleased or
development-state material. Shared chrome adopts the destination afterward.

## Constraints

- `docs/product/changelog.md` remains the sole initial editorial source.
- Existing changelog/release-impact management owns drafting and review.
- `/work/` is removed with no redirect or compatibility route.
- No model at build/release time, dependency, new editorial workflow, customer
  claim, or second publication pipeline.

## Construction tests

**Integration tests:** parse fixture changelogs, build the marketing site,
inspect `/now/` and its source fragments, assert `/work/` is absent, and run
the combined route/page/fragment checker.

**Manual verification:** the launch seed receives ordinary PR review for
outcome focus, source grounding, completeness within the seven-day window, and
absence of in-progress or invented claims.

## Design (LLD)

### Design decisions

- Highlights are an optional subsection of the existing changelog entry rather
  than a new content type or feed. Traces to: AC2, AC6.
- Release location plus version/date determines eligibility; date-like text
  beneath `Unreleased` never qualifies. Traces to: AC3.
- Projection is pure and deterministic. AI may help an author before review but
  is not part of the system. Traces to: AC6, AC7.

### Data & schema

- A projected item carries source release identity, release date, ordered
  highlight bullets, and a changelog fragment target. Traces to: AC3, AC4.
- The launch-window calculation is inclusive of launch day and the preceding
  six calendar dates. Traces to: AC5.

### Component / module decomposition

- Existing stdlib site-generation code parses eligible Highlights and projects
  renderer-local Now data.
- A marketing-local Now route renders the H1, release groups, source links, and
  exact empty state.
- Existing work-index route/projection code is removed rather than retained as
  an alternate surface. Traces to: AC1, AC8, AC9.

### Failure, edge cases & resilience

- Malformed release identity/date or ambiguous relative heading structure
  fails generation with source context.
- Missing Highlights is valid and omitted; zero eligible items renders the
  exact empty state. Unreleased leakage and broken fragments fail tests.
  Traces to: AC3, AC8, AC9.

## Tasks

### T1: The changelog contract projects only eligible released Highlights

**Depends on:** none

**Touches:** docs/product/changelog.md, tools/build-site.py, tools/test_build_site_routing.py, tools/test_check_release_impact.py

**Tests:**
- TDD: cover released/Unreleased placement, optional/missing Highlights,
  relative heading levels, malformed version/date, date ordering, equal-date
  source order, deterministic repeat output, and broken source fragments
  (AC2-AC4, AC7, AC9).
- TDD: prove the inclusive launch window accepts launch day and day minus six
  and rejects day minus seven (AC5).

**Approach:**
- Document optional Highlights in the existing changelog maintenance preamble
  and prove the current release-impact workflow still owns the update; do not
  create or amend a repository-wide convention for this one surface.
- Add the smallest pure parser/projection to the existing stdlib generator.

**Done when:** mutation-sensitive fixtures prove eligibility, order, source
links, window boundaries, and deterministic output.

### T2: `/now/` replaces the public work surface

**Depends on:** T1

**Touches:** web/src/pages/now/index.astro, web/src/pages/work/index.astro, web/src/components/work/WorkIndex.astro, web/src/components/layout/SiteNav.astro, web/src/lib/work-index.ts, web/src/test/work-index.test.ts, tools/export_work_index.py, tools/test_export_work_index.py, tools/build-site.py, tools/test_build_site_routing.py, tools/test_documentation_entry_links.py, docs/specs/README.md

**Tests:**
- Goal-based: build emitted `/now/`, assert its H1, eligible grouped content,
  source links, and exact empty state (AC1, AC3, AC4, AC8).
- Goal-based: assert no `/work/` page, redirect, route, or public work-index
  projection or exporter exists, its dedicated tests are absent, the frozen m6
  spec/plan are byte-unchanged, and the living spec index points to the
  approved successor (AC1, AC9, AC11).
- Goal-based: assert the existing marketing navigation replaces its `Work`
  label and `/work/` target in place with `Now` and `/now/`, without claiming
  the later shared-chrome taxonomy or placement work (AC1, AC10).

**Approach:**
- Add one marketing-local static Now route fed by generated released-highlight
  data.
- Delete the public work route, its site-only projection boundary, and the m6
  exporter and dedicated tests; do not change canonical workspace-status
  behavior or unrelated developer tools.
- Replace only the current marketing navigation's `Work` label and `/work/`
  target in place with `Now` and `/now/`; leave taxonomy, ordering, mobile
  behavior, and current-state treatment to `site-shared-chrome`.
- Keep the shipped m6 spec/plan as historical evidence. Update only the living
  specs index when the successor ships; a frozen Status supersession annotation
  would require an owning ADR and is neither authorized nor truthful before
  this approved implementation lands.

**Done when:** Now renders deterministically; Work is absent from emitted route
and navigation inventory; the public projection exporter and dedicated tests
are removed; and no development-state data reaches the public artifact.

### T3: Launch content covers the approved released seven-day window

**Depends on:** T2

**Touches:** docs/product/changelog.md

**Tests:**
- Goal-based: enumerate released entries in the inclusive seven-day launch
  window and prove every meaningful approved highlight projects and no other
  source does (AC5).
- Visual/manual QA: review each highlight against its released changelog entry,
  implementation diff, and verification evidence (AC5, AC6).

**Approach:**
- Add Highlights only to eligible released entries with meaningful adopter
  outcomes. Do not reconstruct copy from plans, backlog, commits, or
  Unreleased material.

**Done when:** the launch seed is complete, sourceable, outcome-led, and
ordinary-review approved.

### T4: Emitted Now content closes its public contract

**Depends on:** T3

**Touches:** tools/test_check_rendered_site_links.py, tools/test_build_site_routing.py

**Tests:**
- Goal-based: build both sites and verify the Now route, changelog fragments,
  base qualification, deterministic content, and absence of Work/Unreleased
  text (AC1-AC9).
- TDD: seed each forbidden condition named by AC9 and prove the emitted check
  fails.

**Approach:**
- Test generated HTML and route inventories rather than only parser objects or
  source headings.
- Leave navigation placement to `site-shared-chrome` after this task passes
  (AC10).

**Done when:** full emitted route/link checks pass and shared chrome can safely
consume `/now/`.

## Rollout

Land the changelog contract and parser before the route. Remove Work when Now
is emitted, add the source-grounded launch seed, then allow shared chrome to
adopt the new destination. Rollback is a normal source revert; no migration,
external system, dependency, or runtime service exists.

## Risks

- Highlights can drift into promotional claims; released-source grounding and
  ordinary code review keep them factual.
- Heading parsing can confuse Unreleased entries with released ones; structural
  fixtures and emitted leakage tests fail closed.
- The surface can become another editorial pipeline; the initial source and
  amendment boundary keep it inside existing changelog management.

## Changelog

- 2026-08-17: initial approved plan for released changelog Highlights at
  `/now/`, seven-day launch seeding, exact empty state, and complete retirement
  of the public `/work/` surface.
