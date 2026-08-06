# Plan: marketing-docs-link-repair

- **Status:** Drafting
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

- **Files touched:** `web/src/content/journeys/*.md` (17), `web/src/content/packs/*.md` (21),
  `packs/<pack>/JOURNEY.md` (11 — the projection sources for 11 of those 17 journeys).
- **Done is demonstrated by:** every `docsUrl` resolving into the route set the
  docs-site build emits, plus a `build-site.py` round-trip that leaves
  `git status` clean.
- **Not changing:** the docs-site mount (`astro.config.ts` `base`/`outDir`,
  `pages.yml`, `build-site.py` mirror target); the 5 hardcoded `/docs/…` hrefs
  and 3 relative body links that already resolve; `content.config.ts`; the
  Shipped `phase4b-product-docs-completion` spec.

## Declined patterns

- **Re-mounting the docs site to `/guides/`** — declined; the user ruled it out
  explicitly after being shown the option. It would have made all 38 values
  correct with zero data edits, but it moves ~209 published routes.
- **Committing a link-checker tool** — declined; the user scoped this to "just"
  the links, and fixing the 11 pack sources already closes the mechanical revert
  path. Surfaced as a follow-up instead.
- **Adding `startsWith('/docs/')` to the `content.config.ts` zod schema** —
  declined; encodes a site-layout fact in a content schema and inverts the day
  the mount moves.
- **Correcting the stale `/guides/…` instruction in the Shipped phase4b spec** —
  declined; it is historical record. Surfaced as a follow-up.
- **Normalising the neighbouring `packUrl` / `journeyUrl` frontmatter while in
  the same files** — declined; those resolve correctly today, so they fail the
  bundled-fixes "same concern" gate.

## Tasks

### T1 — Correct the 11 pack-local journey sources

**Tests:** no stub (goal-based). `Done when:` `grep -c 'docsUrl: /docs/guides/' packs/*/JOURNEY.md`
reports 11 and `grep -l 'docsUrl: /guides/' packs/*/JOURNEY.md` reports nothing.

**Approach:** rewrite `docsUrl: /guides/<pack>/` → `docsUrl: /docs/guides/<pack>/`
in each of the 11 `packs/<pack>/JOURNEY.md` files. Source-first so the
projection step in T2 reproduces the fix rather than fighting it.

### T2 — Correct the hand-maintained web content, then re-project

**Tests:** no stub (goal-based). `Done when:` `python3 tools/build-site.py` runs
and `git status --porcelain web/src/content` shows only the intended edits.

**Approach:** rewrite the same 6 web-only journeys and 21 pack pages in
`web/src/content/`, then run `build-site.py` so the 11 projected journeys are
regenerated from the T1 sources.

### T3 — Validate against the emitted route set

**Tests:** no stub (goal-based). `Done when:` the route-resolution check reports
38/38 resolved and 0 unresolved, and a second `build-site.py` run leaves
`git status` clean.

**Approach:** enumerate the docs-site routes from the generated content
(frontmatter `slug:` override, else path-derived with `index` → directory) and
assert each `docsUrl`, stripped of its `/docs` prefix, is a member. Then run the
gates in AC6.
