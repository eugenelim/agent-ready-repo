# Plan: documentation-entry-navigation

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)
- **Mode:** full

## Approach

Reduce the documentation surface by moving the argument outward and the detail
downward. The root README becomes a router. Existing marketing, catalogue,
technical-doc, and guide routes become the destinations, strengthened before
their duplicated README content is removed.

The change keeps current routes and visual systems. It edits only authored
sources: generated guide navigation, generated pack pages, adapter projections,
and build output remain untouched.

## Task sequence

### T1 — Reconcile governance ownership

**Depends on:** none  
**Verification mode:** goal-based check  
**Tests/artifacts:** `workspace.toml` TOML parse; unique-slug grep; archived-spec
header inspection; ini-007 dependency inspection.

- Archive `catalogue-wave8-readme-contributing` with a `Superseded by` link.
- Update ini-007 in `workspace.toml`: complete the active IA design item, make
  this spec the current-route implementation owner, archive Wave 8, and point
  Wave 9's former Wave 8 dependency here.
- Preserve Waves 6 and 7 with narrowed cold-start comments for the work still
  gated on Wave 4: neutral-index/generated-reference consumption, deep
  catalogue-builder navigation, `/evaluate/`, and integration relationships.
- Verify the confirmed `catalogue-package-guides` repo backlog item exists once
  with its cold-start context; append it only if absent.

**Verify:** no dependency points to the archived Wave 8 spec; the current-route
owner is singular; every index-dependent Wave 6–7 deliverable remains queued;
TOML remains parseable.

### T2 — Establish complete public destinations

**Depends on:** none  
**Verification mode:** goal-based check + visual/manual QA  
**Tests/artifacts:** content-migration matrix inspection;
`tools/validate_guides.py`; `tools/check-guide-index.py`; changed-guide link
target inventory.

- Tighten `guides/_shared/explanation/pack-catalogue.md` where needed so it
  explains packs, profiles, adapters, composition, ownership, and self-hosting.
- Confirm the existing three-loop, install-route, adapter-support,
  profile-install, preview, and upgrade pages contain the facts the README will
  stop carrying; amend only gaps.
- Replace `guides/README.md` with a compact outcome-and-role hub plus one
  authoring-contract link.
- Generalize `tools/check-guide-index.py` from an “All packs” table parser to
  direct pack-guide-home coverage so the gate preserves completeness without
  prescribing the old layout.

**Verify:** every migration-contract destination exists and has an actionable
next link; guide validation and index checks pass where runnable.

### T3 — Make the technical docs the action hub

**Depends on:** T2  
**Verification mode:** goal-based check + visual/manual QA  
**Tests/artifacts:** authored-route existence script; source walkthroughs for
product manager, infrastructure/SRE, engineer, and catalogue owner; relevant
`tools/test_build_site_routing.py` and `tools/test_build_site_sidebar.py` tests
where runnable.

- Rework `docs-site/src/content/docs/index.mdx` into outcome-first task routes,
  role shortcuts, “use” versus “build and operate” catalogue paths, and concise
  reference off-ramps.
- Update `docs-site/src/content/docs/getting-started/index.mdx` so product and
  infrastructure teams can choose a credible first path alongside the flagship
  build loop.
- Keep the generated pack index and generated guide sidebar as the exhaustive
  inventory; do not duplicate them on the landing page.

**Verify:** page source contains each required role/outcome route and every
local route target is backed by an authored or generated source.

### T4 — Make marketing reveal catalogue breadth

**Depends on:** T2  
**Verification mode:** goal-based check + visual/manual QA  
**Tests/artifacts:** `astro:content` inventory-source grep; `withBase()` route
check; source walkthroughs for product manager, infrastructure/SRE, and
catalogue owner; existing web unit tests where runnable.

- Reframe the hero so it names the catalogue/system while retaining supervised
  build work as the primary proof.
- Replace the homepage's hand-maintained pack preview with outcome paths backed
  by pack links and a route to the complete catalogue.
- Update primary navigation to “Use cases,” Catalogue, Docs, and a
  supervised-loop CTA; remove Journeys from primary navigation only.
- Add outcome and role discovery before the complete data-driven grid on
  `/catalogue/`.
- Replace adopt-by-forking copy in the organization closer with the
  `agentbundle catalogue init` and self-host model.

**Verify:** the catalogue grid still derives from `getCollection('packs')`;
product-management and infrastructure routes occur before it; existing journey
pages remain linked from contextual surfaces.

### T5 — Cut and reroute the README and contributor page

**Depends on:** T2, T3, T4  
**Verification mode:** goal-based check  
**Tests/artifacts:** README line count; removed-content grep; Markdown target
inventory; CONTRIBUTING authoring-source grep; completed content-migration
matrix.

- Rewrite `README.md` to the approved ≤90-line router contract only after T2–T4
  destinations are complete.
- Update `CONTRIBUTING.md` with the absorbed Wave 8 requirements and remove the
  obsolete root-pack-table instruction. Add a short public-doc/source
  orientation and decision chain for people changing the repository.
- Check every migration-contract row against its destination after the cut.

**Verify:** README line/count and negative-content checks; all root routes
resolve; CONTRIBUTING names the real authoring sources and standards.

### T6 — Verify and review

**Depends on:** T1, T2, T3, T4, T5  
**Verification mode:** goal-based check + visual/manual QA  
**Tests/artifacts:** feasible targeted test logs; `git diff --check`; scoped
diff inventory; adversarial review report; quality review report; final
environment-limitation record.

- Run static Markdown/TOML/Astro construction checks and repository tests that
  are read-only in this workspace.
- Run `git diff --check` and inspect the scoped diff.
- Run adversarial review; fix blockers and majors, then re-run until clean.
- Run quality review; fix blockers and majors, then re-run until clean.
- Record build/tempfile restrictions and provide the smallest manual
  verification command set only for checks that could not run here.

## Content ownership after the change

| Information | Canonical owner |
| --- | --- |
| Product promise and audience recognition | Marketing home |
| Outcome-to-pack discovery | Marketing catalogue |
| Complete pack inventory | Data-driven marketing and technical pack indexes |
| Install and first run | Technical getting-started |
| Pack task guidance | `guides/<pack>/` |
| Cross-pack system explanation | `guides/_shared/explanation/` |
| Pack detail | `packs/<pack>/README.md`, projected into technical docs |
| Catalogue authoring | Portable shared references plus `packs/README.md` |
| Repository internals | `docs/architecture/`, contracts, and CONTRIBUTING |
| Repository orientation | Root README |

## Rollback and risk

The change is documentation and authored-site source only. Reverting the diff
restores the previous navigation; no data or runtime migration is involved.

Main risks:

- **A README cut strands information.** Mitigation: T2–T4 precede T5 and the
  migration table is an acceptance checklist.
- **Outcome mappings drift from packs.** Mitigation: exhaustive inventory remains
  data-driven; editorial mappings link to stable pack routes and are much smaller
  than a duplicate pack catalogue.
- **Site links break under the GitHub Pages base path.** Mitigation: use
  `withBase()` in Astro and existing absolute `/agent-ready-repo/docs/` routes in
  Starlight content; construction-check each target.
- **Guide content is mistaken for archive payload.** Mitigation: preserve the
  explicit packaging boundary in the guide and docs copy and track engine work
  separately.

## Declined patterns

- New `/evaluate/` or role-specific routes: current anchors and hubs can prove
  the navigation model without expanding route ownership.
- A generated root README or shared-copy include system: the surfaces need
  different densities; generation would couple unlike page contracts.
- A hand-maintained complete pack table anywhere outside the canonical indexes:
  it caused the current currency and recognition problem.
- Editing scaffolded `packs/README.md` or `profiles/README.md`: useful follow-up
  polish, but it would turn this documentation change into an `agentbundle`
  release.
- Search/filter UI: the catalogue needs outcome context first; a new interaction
  and testing surface is not required for the first correction.
