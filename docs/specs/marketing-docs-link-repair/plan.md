# Plan: marketing-docs-link-repair

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

- **Files touched:** `web/src/content/journeys/*.md`, `web/src/content/packs/*.md`,
  the `packs/<pack>/JOURNEY.md` projection sources behind the projected journeys, and
  the living `docs/specs/platform-site/journey-page-template.md`. Exact counts are held
  canonically in the spec's Acceptance Criteria — not restated here.
- **Done is demonstrated by:** the four goal-based checks in the spec's Testing
  Strategy (route-set membership, end-to-end resolution against the built tree,
  projection fixed-point incl. the gitignored file, mount-untouched diff check).
- **Not changing:** the docs-site mount (`astro.config.ts` `base`/`outDir`,
  `pages.yml`, `build-site.py` mirror target); the already-resolving hardcoded and
  relative links; the `primitives-fixture` placeholders; `content.config.ts`; the
  Shipped `phase4b-product-docs-completion` spec.

## Declined patterns

- **Re-mounting the docs site to `/guides/`** — declined; the user ruled it out
  explicitly after being shown the option. It would have made every value correct with
  zero data edits, but it moves ~209 published routes.
- **Committing a link-checker tool** — declined *for this PR*, and the original
  justification was wrong and has been corrected. It read "fixing the pack sources
  closes the mechanical revert path"; per the spec's Assumptions, the projection path
  explains at most 11 of the 37 files #854 reverted, so closing it does not close the
  revert risk. The decline now rests on scope alone: a committed checker needs a
  `tools/` script plus CI wiring, and the user scoped this change to the links.
  Registered as `web-docs-link-check-gate` in `[backlog].open` rather than left in prose.
- **Adding `startsWith('/docs/')` to the `content.config.ts` zod schema** — declined;
  encodes a site-layout fact in a content schema and inverts the day the mount moves.
- **Correcting the stale instruction in the Shipped phase4b spec** — declined here;
  amending a Shipped spec's history needs its own decision. Registered as
  `phase4b-docsurl-instruction-stale` in `[backlog].open`.
- **Fixing the 8 dead placeholder hrefs on `primitives-fixture.astro`** — declined;
  pre-existing, on a `noindex` orphan dev fixture, outside this change's concern.
  Registered as `web-primitives-fixture-dead-placeholders` in `[backlog].open`.
  (Since resolved: the placeholders are gone and the entry was removed as done on
  2026-08-15 — see this spec's erratum at `spec.md` § disclosed exclusion.)
- **Normalising the neighbouring `packUrl` / `journeyUrl` frontmatter while in the same
  files** — declined; those resolve correctly today, so they fail the bundled-fixes
  "same concern" gate.

## Tasks

### T1 — Correct the pack-local journey sources

**Depends on:** none

**Tests:** no stub (goal-based). `Done when:`
`[ "$(grep -l 'docsUrl: /docs/guides/' packs/*/JOURNEY.md | wc -l)" -eq 11 ]` and
`! grep -q 'docsUrl: /guides/' packs/*/JOURNEY.md` (negated — a bare `grep -l` for an
absent pattern exits 1, which a CI harness reads as failure rather than "absent").

**Approach:** rewrite `docsUrl: /guides/<pack>/` → `docsUrl: /docs/guides/<pack>/` in
each `packs/<pack>/JOURNEY.md`. Source-first so T2's projection step reproduces the fix
rather than fighting it.

### T2 — Correct the hand-maintained web content, then re-project

**Depends on:** T1

**Tests:** no stub (goal-based). `Done when:` `python3 tools/build-site.py` exits 0 and
`git status --porcelain web/src/content` shows only the intended edits, **plus** the
direct content assertion on the gitignored
`web/src/content/journeys/product-documentation.md` (spec Testing Strategy 3).

**Approach:** rewrite the hand-maintained journeys and pack pages in
`web/src/content/`, then run `build-site.py` so the projected journeys are regenerated
from the T1 sources.

### T3 — Sweep the living authoring surface

**Depends on:** T1

**Tests:** no stub (goal-based). `Done when:`
`! grep -q 'docsUrl: /guides/' docs/specs/platform-site/journey-page-template.md`.

**Approach:** correct the `docsUrl` example in the living journey-page template so the
next journey authored from it does not re-seed the defect.

### T4 — Validate against the emitted route set and the built tree

**Depends on:** T2, T3

**Tests:** no stub (goal-based). `Done when:` all four spec Testing Strategy checks
pass and the gates in AC7 exit 0.

**Approach:** run the route-set membership check and the end-to-end built-tree link
resolution (no off-site escape hatch for unprefixed root-relative links; disclosed
`primitives-fixture` exclusion), then the gates.
