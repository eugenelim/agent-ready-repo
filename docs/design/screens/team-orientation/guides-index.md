---
type: screen-flow-brief
screen: guides-index
flow: team-orientation
surface: responsive-web
surface-genre: documentation
---

# Screen brief: guides-index · agent-ready-repo · surface: responsive-web

## Place in the whole

- **Type:** screen-brief
- Journey step(s): future-state Stage 4 (Roll out a cohort), Stage 5 (Make it the default)
- Enters from: S1 (transitional action) · terminal (⚠ install failed) · S4 partial · S5 no-results · search engine · direct
- Exits to: S4 (a path) · S5 (search) · S6 (the internal case) · guide page
- Traces to outcome: the reader has a named, ordered sequence they can hand to a colleague
- Surface genre: documentation — Diátaxis typing, TTFV, and navigation strategy apply

## Job

Get the reader to a followable sequence they can hand to someone else.

## States

- **success/default:** start-here promise, the six ordered paths, prominent
  search, then the outcome and role tables.
- **loading:** layout preserved so the page does not jump. This matters more than
  usual because the start-here promise is the first thing above the fold and a
  reflow moves it.
- empty / error / partial / disabled: **not applicable** to the index itself. The
  paths are static content. S4 owns partial; S5 owns empty and error.
- permission/denied: not applicable — not gated.

## Data & actions

- **Shows:** one start-here promise; six ordered paths, each with prerequisite,
  audience, time cost, first value, and end state; the statement that a path ends
  at a handoff rather than a document; prominent search; the seven job groups;
  the role list; a route to the internal case; which of the two generated
  hierarchies answers which kind of question.
- **Actions:**
  - Open a path → S4. Backing service: static page from the guides tree.
  - Search → S5. Backing service: the documentation search index. ⚠ No results →
    S5's no-results state, which recovers to the nearest job group and the six
    paths.
  - Navigate a job group to an area → guide page. Backing service: the generated
    guide navigation. **This action needs a spec amendment** — see the
    consistency invariants.
  - Follow the internal-case route → S6. Backing service: static marketing page.
    **S6 does not exist yet.**

## Interaction & behavior

See `interaction-design` enrichment. The only in-screen behaviour of substance is
the search control's focus and submit flow, and the sidebar's collapse at narrow
widths — where navigation must remain reachable without it.

## Copy

See `docs/design/content/docs-guides-index.md` for the content hierarchy and the
Pyramid Principle rationale. `copy-direction` **does not apply to this screen** —
its mode is `technical-editorial` and this is not an onboarding surface, so the
per-surface acquisition copy route is deliberately not taken. `ux-writing` owns
UI-state copy only: the search placeholder, which must name a real example query
that actually returns something, and the no-results recovery.

**No persuasion register.** The fourth tech-site principle governs the seam: what
crosses from marketing is vocabulary and destinations, never register.

## Shared contract — REFERENCE, do not restate

- Design system: `docs-site/src/styles/tokens.css` — 146 separately-named tokens.
  **Deliberately a different palette from the marketing renderer.** Do not
  converge them.
- Aesthetic direction: `docs/specs/docs-site-design-refresh/creative-direction.md`.
- Navigation / chrome: Starlight's header, sidebar, search, theme control,
  breadcrumbs, table of contents, and pagination, plus the docs
  product-orientation band. The band stays distinct from Starlight's own chrome.
- Quality floor: WCAG at the level this context requires · reduced-motion ·
  handle-all-states.

## Consistency invariants

- **Reuse, never reinvent:** Starlight's sidebar, search, and breadcrumbs. This
  screen introduces no navigation component.
- **Must stay consistent with:** S4 (the paths it lists), S5 (the search it
  launches), S1 (shares the seven job names and the work-lifecycle decision phrasing, and nothing else — the five adoption stations are marketing-side only).
- **The load-bearing invariant:** the seven job groups reuse the job names that
  already exist in the marketing outcome router and in this page's own
  achieve-table. Zero new vocabulary. Introducing an eighth name breaks the
  crossing.
- **The blocker this screen carries:** job grouping the sidebar requires amending
  `docs/specs/guides-sidebar-generation/spec.md`, which is **Status: Shipped**.
  Its `[[guide_groups]]` entries are `dir` plus `label` with table order as group
  order, and there is no field that nests pack directories inside a job group.
  Guide URLs are unaffected — they derive from the directory tree — so no
  redirects are needed, but the grouping is not a data edit.

## Done

- [ ] all applicable states designed
- [ ] every action wired to a named service, including the one that does not exist
- [ ] error/edge flows route to a real screen or state
- [ ] copy in per state
- [ ] WCAG + reduced-motion honored
- [ ] uses the docs design system (no marketing components leaking across)
- [ ] interaction/behavior section enriched
- [ ] the 17 frozen navigation baseline pairs verified to survive generation
- [ ] design-review clean

### If documentation

- **Diátaxis type:** explanation, functioning as a hub. This is a genuine typing
  problem: several area index pages carry an explanation kind while operating as
  navigation hubs. Either they retype or the type set needs a hub kind. Owner is
  the guide source model, not this brief.
- **TTFV target:** the reader can name a path to hand over within one screen of
  arriving. Note the tension recorded and unresolved: the first path is stated at
  about an hour, and a first-value on-ramp should be closer to twenty minutes of
  active work. `documentation-design` owns the split.
- **Navigation strategy:** search-first, with hub-and-spoke browsing behind it.
  Roughly 229 published pages puts this surface two tiers above the flat
  navigation it ships today, and a header search widget does not meet the
  search-first bar on its own.
- **Machine-readability:** the paths are a true sequence and must be marked up as
  an ordered one, not as prose with numbers. The outcome and role tables keep a
  consistent column structure so they stay parseable.
