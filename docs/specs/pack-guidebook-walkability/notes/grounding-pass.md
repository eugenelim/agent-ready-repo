# Grounding pass — destinations, before the spec body

Run 2026-09-11, after the durable outputs were named and before any criterion
was worded. This is discovery, not validation: it records what already owns
each destination, what governs it, what runs against it, and what an accepted
decision has already settled. Two of its results changed the design, and both
are marked.

## S1 — a new page under `guides/_shared/`

> **Superseded as a destination.** This pass was run when the slice was to add
> one cross-cutting page under `guides/_shared/`. The slice is now five
> pack-local guidebooks under `guides/<pack>/`, and **no task or criterion owns
> a `guides/_shared/` page** — creating one would add a sixth surface nobody
> owns. What survives and still applies to the real destinations: the frontmatter
> schema, the three validators, the title lint, and the derived inventory, all of
> which treat a pack-local guide exactly as described below.

- **Scoped guidance walk:** root `AGENTS.md`; root `AGENTS.local.md` (edit
  sources, never generated projections); `guides/AGENTS.md:7` (adopter-facing,
  published by `tools/build-site.py`, authoring routed to `author-product-docs`)
  and `guides/AGENTS.md:13` (frontmatter owned by `contracts/guide.schema.json`,
  `additionalProperties: false`, `title` must equal the leading H1). No
  `AGENTS.md` exists under `guides/_shared/` or below it.
- **Gates:** `contracts/guide.schema.json:6` requires `title`, `summary`,
  `pack`, `kind`; `pack: _shared` is explicitly allowed at line 21.
  `tools/validate_guides.py` validates the tree; its structural exemption at
  lines 61–70 covers `README.md` only, so a new page is not exempt.
  `tools/lint-guide-titles.py` enforces title/H1 agreement.
  `.github/workflows/docs.yml:111–162` runs both and rejects warnings.
  `make build-check` carries the paired tests at `Makefile:584`.
- **Owners:** `docs/CONVENTIONS.md:769–781` defines a tutorial as
  learning-oriented, "one path, one guaranteed outcome".
  `docs/specs/guides-sidebar-generation/spec.md` owns the sidebar contract.
- **Settled:** sidebar placement is derived, not hand-maintained.
  `tools/build-site.py:673–676` aliases the `tutorials` directory to
  `kind: tutorial`, and `:797` fixes the subgroup order. **Design consequence:**
  a page here needs no `site.toml` edit, so it adds no `[[guide_groups]]` entry
  and does not touch the navigation model `cohort-orientation-surfaces` owns.

## S2 — `guides/README.md` § P2b

- **Scoped guidance walk:** root `AGENTS.md`, root `AGENTS.local.md`,
  `guides/AGENTS.md`. No deeper scoped file.
- **Gates:** the guide schema and title lint apply to the page as a whole.
  `tools/check-guide-index.py:36–67` requires a direct `<pack>/` link for every
  active non-exempt pack. No P2b-specific script, target, test, schema or CI leg
  exists; searched `tools/`, `.github/workflows/`, `Makefile` and `docs/specs/`
  for `P2b`, `four product disciplines`, `wider alternative` and `P<n>b`.
- **Owners:** `docs/design/content/docs-guides-index.md:88` records P2b as the
  four-discipline path and fixes it adjacent to P2, before P3, reached by P2's
  "Wider alternative" pointer (lines 102–117). It carries no lifecycle status
  field.
- **Settled:** P2b is an alternative to P2, not a following stage
  (`guides/README.md:74–83`), and moving it to satisfy the historical
  five-stage test was explicitly rejected
  (`docs/design/content/docs-guides-index.md:119–131`).

## S3 — the four `packs/*/JOURNEY.md` sources

- **Scoped guidance walk:** root `AGENTS.md`, root `AGENTS.local.md`,
  `packs/AGENTS.md:43–47` (matching `pack.toml` and plugin version bumps for
  every non-cosmetic content change), `packs/AGENTS.md:49` (no internal
  governance citations in shipped pack content), `packs/AGENTS.local.md:28–42`
  (version bump, `FORCE=1 make build-self`, top-level changelog entry). No
  pack-local `AGENTS.md` under the four target packs.
- **Gates:** `tools/lint-pack-journeys.py` requires a unique `journey_id`,
  pack-local skill references, valid states, `Output` in every numbered stage,
  `State` in every stage, and `You decide` for write-state stages; it performs
  no semantic comparison between one pack's `youProvide` and another's
  `youReceive`. `tools/lint-journey-contract.py` freezes the stage label set and
  its order — `You provide < <Actor> does < You do < You decide < Output` — and
  leaves wording to review. `tools/lint-web-journey-parity.py` compares skill
  counts only.
- **Owners:** `docs/specs/catalogue-wave4-semantic-contracts-index/spec.md:124`
  (Shipped) requires the `contract` object and caps a tagline at 120
  characters; `contracts/catalogue-index.schema.json:109` keeps the object
  closed while permitting optional `youType`.
  `docs/specs/journey-template-revamp/spec.md:63,77,133` (Shipped) freezes the
  labels, not the prose. `docs/product/intents/skill-sequence-wayfinding.md`
  (Draft) states at lines 117–122 that **S7 owns the four-discipline walk's own
  next-links**, and that a later slice replaces them with a derived form.
- **Settled, and the reason this slice touches none of these files:** every
  non-cosmetic edit here is a released pack change — version bumps, changelog,
  self-host and marketplace regeneration. **Design consequence:** the owner
  decision of 2026-09-11 keeps the repair on the surfaces, so this destination
  is read-only for this slice.
- **The find that changed the design, and its later correction:** all four packs
  carry `contract.youType`, a literal request in machine-readable frontmatter.
  This pass concluded the missing literal request was therefore "a projection,
  not new authoring". **That was over-read and is superseded**: `youType` is one
  utterance *per pack*, not per stage, and only 13 of 25 stages carry one in
  their body. The spec's Objective fixes a source ladder per obligation with a
  stated fallback; this bullet is retained as the record of what the pass
  originally claimed.

## S4 — `web/src/content/journeys/*.md` (generated)

- **Scoped guidance walk:** root files, plus `web/AGENTS.md:7` — "Do not edit
  generated inputs by hand."
- **Regeneration:** `python3 tools/build-site.py --journeys-only`, contract
  "Sync pack-local JOURNEY.md files only" (`tools/build-site.py:2191–2195`).
  `sync_pack_journeys` injects `generated: true` (`:1324–1376`).
  `.github/workflows/pages.yml:127–136` regenerates before the Astro build.
- **Gap, measured:** no committed-byte parity check exists between a source
  `JOURNEY.md` and its generated projection. Searched `tools/`, `Makefile` and
  `.github/workflows/`. A source change committed without regeneration leaves
  the committed projection stale and fails nothing; CI regenerates before
  building rather than failing on a dirty post-generation diff. The work-loop's
  clean-tree finish check catches it only because `make site-build` runs the
  full `tools/build-site.py` via `site-sync` (`Makefile:687–692`). Routed as a
  follow-on rather than admitted — this slice edits no pack source, so it
  cannot red the gap it would add.

## S5 — `web/src/test/FourDisciplineSequence.test.ts`

- **Scoped guidance walk:** root files, plus `web/AGENTS.md:59`.
- **Prerequisite:** the test states it itself — `make site-build` — and reads
  `build/journeys/index.html`, skipping when absent (`:15–17`, `:23–38`, `:53`).
  **A skip is a silent pass**, so the build must be confirmed to have run.
  `make site-build` runs `site-sync`, the web build, then the docs-site build
  (`Makefile:687–692`). `npm test --prefix web` maps to `vitest run`.
- **Owners:** the file's header names `spec/four-discipline-sequence`, which no
  longer exists — that spec was discarded on 2026-09-11. This spec inherits it.
  `docs/design/content/journeys-index.md:72–82` owns the reader-facing grouping.
- **Settled:** assertions observe built output, never an invented source seam
  (`:5–10`).

## S6 — `web/src/pages/index.astro` and `site.toml [shared_chrome]`

- **Scoped guidance walk:** root files, plus `web/AGENTS.md:13` — anchor content
  changes in `docs/design/journeys/team-orientation-future-state.md`; changing a
  stage's actions or residual pains requires re-gating through `approve-journey`.
- **Gates:** `tools/test_build_site_routing.py:118` validates the shared-chrome
  vocabulary and already carries `journeys` as
  `("Journeys", "/journeys/", "internal")` at line 65; lines 379–388 reject
  unknown and duplicate header references. Included in `make build-check`
  (`Makefile:584`).
- **Owners:** `docs/specs/site-shared-chrome/spec.md` is **Shipped** and places
  adding or reordering a destination outside its approved contract under
  "Ask first" (lines 35–41); its approved Product footer already includes
  Journeys (lines 71–83). `docs/design/content/marketing-home.md:386–412`
  decides the fix — a header destination plus a zone 7 entry — and records it as
  "decided, not implemented" and "not authority to edit the header".
- **Settled:** `journeys` exists as a destination and a Product-footer member
  (`site.toml:219–224`, `:289–292`) and is absent from `header`, which holds six
  ids (`site.toml:148–156`). Two sources agree the entry belongs and neither
  authorizes implementing it, so this is routed to its owner, not built here.

## Contradictions found

1. **`docs/design/content/journeys-index.md:81`** says a route onward to the
   guides path "Does not exist today", while
   `web/src/pages/journeys/index.astro:125` ships that route and
   `FourDisciplineSequence.test.ts:172–180` guards it. The brief is stale
   against the shipped state. Repaired by this slice as a bundled fix.
2. **The walk's handoff premise.** Recorded in full in
   [`walk-premise-correction.md`](walk-premise-correction.md); it is the reason
   this spec's Objective differs from the brief's S7 row.
