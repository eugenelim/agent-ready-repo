# Spec: marketing-docs-link-repair

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [ADR-0050](../../adr/0050-astro-marketing-site-toolchain-and-deploy.md) — the Astro
    marketing site at `/agent-ready-repo` whose links this spec corrects
  - [ADR-0055](../../adr/0055-starlight-replaces-mkdocs-for-reference-docs.md) — the
    Starlight reference docs mounted at `/agent-ready-repo/docs/`, which is what makes
    `/docs/guides/<pack>/` the correct target
- **Contract:** none.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light (work-loop). No risk trigger fired. The one conditional trigger —
structural / public-interface change — was checked and did NOT fire: the docs-site
mount is explicitly out of scope, so no published route moves. Lean fill: Objective +
Acceptance Criteria + Boundaries + Testing Strategy + Assumptions (the last three earn
their place via the projection-source trap and the twice-reverted history). -->

## Problem

Before this change, all 38 `docsUrl` values in `web/src/content/` read
`/guides/<pack>/`, which renders as `/agent-ready-repo/guides/<pack>/`. That path
does not exist — the Starlight tech docs are mounted at `/agent-ready-repo/docs/`
(`docs-site/astro.config.ts` `base`). Verified live on 2026-08-06:
`/agent-ready-repo/guides/core/` → 404; `/agent-ready-repo/docs/guides/core/` → 200.

## Objective

Every "Read the reference" link on the marketing site (`web/`) lands on a real page
of the Starlight tech docs instead of a 404, and stays landed across a
`tools/build-site.py` run.

## Boundaries

### Always do

- Fix the projected journeys at their **source** (`packs/<pack>/JOURNEY.md`), not
  only at the `web/src/content/journeys/` projection output. `build-site.py`
  regenerates those from the pack sources on every run.
- Sweep the **living** authoring surfaces that prescribe the field, not just the data:
  `docs/specs/platform-site/journey-page-template.md` is a living template-reference
  doc (so designated by `journey-template-revamp/spec.md` AC), and a stale example in
  it re-seeds the defect into the next journey authored. Check **every** route-shaped
  value in its example block, not just `docsUrl` — `relatedJourneys` entries also
  render directly into links.
- Validate each corrected value against the route set the docs-site build actually
  emits, not against an assumed URL shape.

### Ask first

- Before touching any file outside `web/src/content/`, `packs/*/JOURNEY.md`, and this
  spec directory. The fix has ping-ponged twice; widening the blast radius without a
  decision is how it acquires unrelated risk.

### Never do

- Move the docs-site mount. `docs-site/astro.config.ts` (`base`, `outDir`),
  `.github/workflows/pages.yml`, and `tools/build-site.py`'s mirror target are out of
  scope — the decision to keep the tech site at `/docs/` is the user's, taken
  2026-08-06.
- Touch the 5 hardcoded `/docs/…` hrefs (`SiteNav`, `SiteFooter`, `404.astro`,
  `BuildYourOrg`, `packs/[pack].astro`) or the 3 relative body links in
  `journeys/core.md` and `packs/atlassian.md` — all 8 already resolve.
- Touch the placeholder hrefs in `web/src/pages/primitives-fixture.astro` (including
  its `/guides/github-auth`, which is *not* one of the 38 and does not resolve). It is
  a `noindex, nofollow` development fixture, absent from the sitemap and unlinked from
  any real page; its dead placeholders are pre-existing and deliberately excluded.
- Rewrite the Shipped `phase4b-product-docs-completion` spec. Its lines 24/66 and
  checked AC7 assert the superseded form; correcting a Shipped spec's history needs its
  own decision (see Assumptions).
- Add a `startsWith('/docs/')` refinement to `web/src/content.config.ts` — that encodes
  a site-layout fact into a content schema and breaks the day the mount does move.

## Testing Strategy

**Goal-based checks.** There is no compressible invariant to assert; the docs-site
route set and the built file tree are the oracles.

1. **Route-set membership.** Generate the docs-site content
   (`python3 tools/build-site.py`), enumerate every emitted route (frontmatter `slug:`
   override, else path-derived with `index` → directory), and assert every `docsUrl`
   in `web/src/content/` resolves into that set.
2. **End-to-end resolution against the built tree.** Build both sites in the canonical
   order (`web` first — it cleans `build/` — then `docs-site`), then resolve every
   internal `href` on the built marketing pages against `build/`. **Root-relative
   links must be checked whether or not they carry the `/agent-ready-repo` base
   prefix** — an earlier version of this check treated unprefixed links as off-site and
   silently skipped them. **Disclosed exclusion:** `build/primitives-fixture/` is
   excluded (8 pre-existing placeholder hrefs on a `noindex` dev fixture, listed in
   `[backlog].open` as `web-primitives-fixture-dead-placeholders`).

   > **Erratum (2026-08-15, spec/workspace-backlog-reconciliation AC1c):** the
   > disclosed exclusion above is **obsolete — do not implement it.** The eight
   > placeholder hrefs are gone; `web/src/pages/primitives-fixture.astro` now
   > carries exactly two, both live. A future link gate needs **no**
   > `primitives-fixture` carve-out, and adding one would re-disclose an exclusion
   > that no longer has a subject. The root-relative-prefix trap in the sentence
   > before it still stands. The backlog entry named here was removed as done in
   > the same change.
3. **Projection fixed-point.** Re-run `tools/build-site.py` and assert
   `git status --porcelain web/src/content packs` reports nothing beyond the commit's
   own changes. **This check is structurally blind to
   `web/src/content/journeys/product-documentation.md`**, which is listed in
   `web/src/content/journeys/.gitignore` and can never report dirty — assert its
   content directly instead:
   `grep -q 'docsUrl: /docs/guides/product-documentation/' web/src/content/journeys/product-documentation.md`.
4. **Mount untouched.** `git diff --name-only origin/main..HEAD` contains none of
   `docs-site/astro.config.ts`, `.github/workflows/pages.yml`, `tools/build-site.py`,
   `web/src/components/**`, `web/src/pages/**`.

No production test file, and no committed link-checker — both deferred (see
Assumptions).

## Acceptance Criteria

- [x] **AC1.** Every `docsUrl` value in `web/src/content/journeys/` reads
  `/docs/guides/<pack>/` and resolves to an emitted docs-site route.
- [x] **AC2.** Every `docsUrl` value in `web/src/content/packs/` reads
  `/docs/guides/<pack>/` and resolves to an emitted docs-site route. Observed across
  AC1+AC2: 38/38 resolved, 0 unresolved.
- [x] **AC3.** Every pack-local source (`packs/<pack>/JOURNEY.md`) carries the same
  corrected value, so `build-site.py` reproduces rather than reverts it. Observed: 11
  sources corrected, 0 remaining on the old form.
- [x] **AC4.** The projection is a fixed point: after re-running `build-site.py`,
  `git status --porcelain web/src/content packs` reports nothing beyond the commit's
  own changes, **and** the gitignored
  `web/src/content/journeys/product-documentation.md` asserts correct by direct
  content check (Testing Strategy 3).
- [x] **AC5.** The 8 already-working links are untouched and no published route moves,
  verified by the Testing Strategy 4 diff check.
- [x] **AC6.** Every route in the living authoring template
  `docs/specs/platform-site/journey-page-template.md`'s frontmatter example resolves:
  the superseded `/guides/<pack>/` `docsUrl` form is gone, and the `relatedJourneys`
  example no longer names `release` (not a journey slug; rendered straight into
  `/journeys/<slug>/` by `web/src/pages/journeys/[journey].astro`, so it seeded a dead
  link) — it now names `release-engineering`, matching the template's own worked
  exemplar `web/src/content/journeys/core.md`.
- [x] **AC7.** Gates green: `make lint-ruff`, `tools/lint-pack-journeys.py`,
  `tools/lint-web-journey-parity.py`, `tools/lint-journey-contract.py`,
  `python3 .claude/skills/work-loop/scripts/lint-spec-status.py --root .`, and
  `python3 .claude/skills/work-loop/scripts/lint-knowledge.py` all exit 0.

## Assumptions

- Technical: the docs-site mount is `/agent-ready-repo/docs/` and stays there
  (source: `docs-site/astro.config.ts`; live 200/404 probe, 2026-08-06).
- Technical: 11 of the 17 journey pages are projected from `packs/<pack>/JOURNEY.md`;
  the other 6 and all 21 pack pages are hand-maintained in `web/` (source:
  `tools/build-site.py` journey sync, 2026-08-06).
- Technical: no test hashes, snapshots, or counts these values. The
  `docsUrl: /guides/test/` occurrences in `tools/test-lint-pack-journeys.py` are
  synthetic fixtures, and `lint-pack-journeys.py` does not validate the field (source:
  anchor-test sweep, 2026-08-06).
- Process — **why this reverted before, stated precisely.** The fix landed in #852
  (`985ad083`) and was undone in #854 (`d6b78f42`). Two candidate mechanisms were
  checked against the git record and only one survives as *possible*:
  - *Projection revert* — real and still-live, but it explains **at most 11 of the 37**
    files #854 reverted. The other 26 (21 pack pages + 6 hand-maintained journeys) are
    never written by `build-site.py`.
  - *Stale base* — **disproved.** `git merge-base --is-ancestor 985ad083 d6b78f42`
    confirms #852 was already in #854's ancestry (#854's parent is #853, `f82f5bda`),
    so the base was current and a freshness check would not have fired.

  The actual mechanism for the other 26 is not determinable from the commit graph —
  #854's branch tree simply carried the old value. This PR closes the projection path
  (the one path it can close mechanically); the authoring-surface path is closed by
  AC6; the documentation-drift path (Shipped phase4b spec, below) remains open.
- Process: two follow-ups are registered in `workspace.toml [backlog].open` rather than
  built here — a committed link-checker (`web-docs-link-check-gate`) and reconciliation
  of the stale phase4b instruction (`phase4b-docsurl-instruction-stale`). The user
  scoped this change to the links themselves.
