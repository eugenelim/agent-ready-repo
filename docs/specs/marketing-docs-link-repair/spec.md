# Spec: marketing-docs-link-repair

- **Status:** Implementing
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none — this spec changes link data only; it does not
  change the docs-site mount, the adapter contract, or any published route.
- **Contract:** none.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light (work-loop). No risk trigger fired. The one conditional trigger —
structural / public-interface change — was checked and did NOT fire: the docs-site
mount (`base`, `outDir`, `pages.yml`) is explicitly out of scope, so no published
route moves. Lean fill: Objective + Acceptance Criteria + Boundaries + Testing
Strategy + Assumptions (the last three earn their place via the projection-source
trap and the twice-reverted history). -->

## Objective

Every "Read the reference" link on the marketing site (`web/`) should land on a
real page of the Starlight tech docs instead of a 404.

All 38 `docsUrl` values in `web/src/content/` read `/guides/<pack>/`, which
renders as `/agent-ready-repo/guides/<pack>/`. That path does not exist — the
tech docs are mounted at `/agent-ready-repo/docs/` (`docs-site/astro.config.ts`
`base: '/agent-ready-repo/docs'`). Verified live on 2026-08-06:
`/agent-ready-repo/guides/core/` → 404; `/agent-ready-repo/docs/guides/core/` →
200.

Success: every `docsUrl` resolves to a page the docs-site build actually emits,
and a `tools/build-site.py` round-trip does not revert the fix.

## Boundaries

### Always do

- Fix the 11 projected journeys at their **source** (`packs/<pack>/JOURNEY.md`),
  not only at the `web/src/content/journeys/` projection output. `build-site.py`
  regenerates those 11 from the pack sources on every run.
- Validate each corrected value against the route set the docs-site build
  actually emits, not against an assumed URL shape.

### Never do

- Move the docs-site mount. `docs-site/astro.config.ts` (`base`, `outDir`),
  `.github/workflows/pages.yml`, and `tools/build-site.py`'s mirror target are
  out of scope — the decision to keep the tech site at `/docs/` is the user's,
  taken 2026-08-06.
- Touch the 5 hardcoded `/docs/…` hrefs (`SiteNav`, `SiteFooter`, `404.astro`,
  `BuildYourOrg`, `packs/[pack].astro`) or the 3 relative body links in
  `journeys/core.md` and `packs/atlassian.md` — all 8 already resolve.
- Rewrite the Shipped `phase4b-product-docs-completion` spec. Its
  `/docs/guides/…` → `/guides/frontend-engineering/` line is the historical
  record of what that PR did; correcting history is not this PR's job.
- Add a `startsWith('/docs/')` refinement to `web/src/content.config.ts` — that
  encodes a site-layout fact into a content schema and breaks the day the mount
  does move.

## Testing Strategy

- **Goal-based check.** There is no compressible invariant to assert; the
  docs-site route set is the oracle. Two checks, both mechanical:
  1. Generate the docs-site content (`python3 tools/build-site.py`), enumerate
     every emitted route (frontmatter `slug:` override, else path-derived with
     `index` → directory), and assert every `docsUrl` in `web/src/content/`
     resolves into that set.
  2. Re-run `tools/build-site.py` after the edit and assert `git status` is
     clean — this is what proves the 11 projected journeys were fixed at source
     rather than at the projection output.
- No production test file. A committed link-checker is deliberately deferred
  (see Assumptions).

## Acceptance Criteria

- [ ] **AC1.** All 17 `docsUrl` values in `web/src/content/journeys/` read
  `/docs/guides/<pack>/` and each resolves to an emitted docs-site route.
- [ ] **AC2.** All 21 `docsUrl` values in `web/src/content/packs/` read
  `/docs/guides/<pack>/` and each resolves to an emitted docs-site route.
- [ ] **AC3.** The 11 pack-local sources (`packs/<pack>/JOURNEY.md`) carry the
  same corrected value, so `build-site.py` reproduces rather than reverts it.
- [ ] **AC4.** `python3 tools/build-site.py` followed by `git status --porcelain`
  produces no output — the projection is a fixed point of the fix.
- [ ] **AC5.** The 8 already-working links are untouched, and no published route
  moves: `docs-site/astro.config.ts`, `.github/workflows/pages.yml`, and
  `tools/build-site.py` are unmodified.
- [ ] **AC6.** Gates green: `make lint-ruff`, the journey lints
  (`lint-pack-journeys.py`, `lint-web-journey-parity.py`,
  `lint-journey-contract.py`), and `lint-spec-status.py` all exit 0.

## Assumptions

- Technical: the docs-site mount is `/agent-ready-repo/docs/` and stays there
  (source: `docs-site/astro.config.ts`; live 200/404 probe, 2026-08-06).
- Technical: exactly 11 of the 17 journey pages are projected from
  `packs/<pack>/JOURNEY.md`; the other 6 (contracts, converters,
  credential-brokers, figma, monorepo-extras, user-guide-diataxis) and all 21
  pack pages are hand-maintained in `web/` (source: `tools/build-site.py`
  journey sync, 2026-08-06).
- Technical: no test hashes, snapshots, or counts these values. The
  `docsUrl: /guides/test/` occurrences in `tools/test-lint-pack-journeys.py` are
  synthetic fixtures, and `lint-pack-journeys.py` does not validate the field
  (source: anchor-test sweep, 2026-08-06).
- Process: this fix has now been applied (#852) and reverted (#854) once each,
  and the Shipped `phase4b-product-docs-completion` spec still instructs the
  reverted direction. A committed link-checker and the reconciliation of that
  stale instruction are **surfaced as follow-ups, not built here** — the user
  scoped this change to the links alone. Editing the 11 pack sources removes the
  mechanical revert path; the documentation-drift revert path remains open.
