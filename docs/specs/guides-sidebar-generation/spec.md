# Spec: guides-sidebar-generation

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0020](../../adr/0020-per-pack-diataxis-hierarchy-for-guides.md) (per-pack Diátaxis hierarchy), [ADR-0055](../../adr/0055-starlight-replaces-mkdocs-for-reference-docs.md) (Starlight), [`guide-source-model`](../guide-source-model/spec.md) (frontmatter declares kind), `contracts/guide.schema.json`, `site.toml` (site recipe), [`docs-site/AGENTS.md`](../../../docs-site/AGENTS.md) (build order), [`guides/AGENTS.md`](../../../guides/AGENTS.md) (publication routing)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it.

## Intent

**A reader can follow an argument through the docs from one page to the next,
and no published page is unreachable.**

That is the outcome. A generated sidebar is one mechanism serving it — named
here so the spec is honest about what it builds, not because the sidebar is the
goal.

Two things block the intent today.

**Pages are missing.** The sidebar is a hand-maintained literal tree in
`docs-site/astro.config.ts` (lines 86–544) carrying 119 guide entries. 181
navigable guide files exist on disk, so **62 published pages are absent from
navigation** — reachable only by search or a direct link. Adding a page and
forgetting the config edit is the default outcome, not the exception.

**Sequence cannot be expressed where it is generated.** The hand tree nests
pack → Diátaxis kind, which sorts by what a page *is* rather than what a reader
should read next. `contracts/guide.schema.json` already defines `order` as
"sort weight within a pack group," and four `atlassian` pages already use it as
a cross-kind reading order (`tutorial → how-to → reference → explanation`, 1–4).
That sequence works only because someone hand-placed it; nothing generates it
and nothing protects it.

## Context

Shaped in-session (2026-08-06) from a walkthrough of the `iac-terraform` flow.
The request that produced it: an organization adopting central infrastructure
practice needs a narrative arc in human language that navigates well, and a
journey page is a preview that does not carry the process.

## Approach: collate before you project

The change is a translation and is specified as one. Source material is collated
into a **predictable inventory** first; the sidebar is projected from that
inventory second. The inventory is a real artifact — dumpable, diffable, and
testable on its own — not an intermediate hidden inside a generator.

This split is load-bearing. Every awkward fact about the source material
(curated labels, index-page slug normalization, files that must never reach
readers, `slug:` overrides, cross-kind ordering) becomes a **declared field on a
record** instead of a branch buried in projection logic. It also makes the
change reviewable: the before/after navigation diff is computable, so "no page
regressed" is proven rather than asserted.

### Layer 1 — Inventory

One deterministic pass over `guides/**/*.md` produces one record per file:

| Field | Source |
| --- | --- |
| `source_path` | the file |
| `pack` | first path segment (`_shared`, `_reference` included) |
| `kind` | `kind:` frontmatter when present, else the kind directory, else none |
| `order` | `order:` frontmatter; integer, else absent |
| `title` | `title:` frontmatter, else the frozen baseline label, else derived from the filename |
| `slug` | `slug:` frontmatter when present, else derived — **must equal the Starlight slug of the file `mirror_guides()` writes** |
| `is_index` | true for `README.md` at any depth |
| `nav_eligible` | false for `AGENTS.md`; true otherwise |

**On the `kind` directory fallback.** `guide-source-model` AC3 (shipped) states
that the physical directory does not determine kind. This spec relaxes that
**only for pages carrying no `kind:` frontmatter** — 162 of 182 files. Where
frontmatter declares a kind it always wins. The relaxation is deliberate and
scoped: the alternative is 162 uncategorized pages, and the long-term fix is
frontmatter migration, not a different fallback.

**Measurements** (single statement; the plan references this section rather than
restating): 182 `.md` files, 1 nav-ineligible (`guides/AGENTS.md`), 181
eligible, 181 distinct slugs (zero collisions), 119 entries in the hand tree,
**62 absent**. Extract nav slugs with the pattern `slug: '(guides(/…)?)'` — a
`guides/`-prefixed match silently drops the root `guides` entry and yields 118.

### Layer 2 — Projection

The inventory becomes sidebar groups.

**Group labels and order** come from a `[[guide_groups]]` table in `site.toml`,
**separate from the existing `[[groups]]` table**. The existing table is routed
through `discover_packs()`, which skips `_`-prefixed slugs and warns on any slug
without a `packs/<slug>/pack.toml` — so it structurally cannot express `_shared`
(39 pages) or `_reference` (1). A distinct table gives both a declared home.
Guide groups render as a **flat list of pack groups** under "Guides", matching
today's shape; `site.toml`'s six super-group labels are not inherited, which
avoids a five-level nesting Starlight has never been asked to render.

**Labels** resolve `title:` frontmatter → frozen baseline → filename-derived.
The frozen baseline is required: filename derivation alone changes **90 of the
119 existing labels** (`'Plan and Execute'` → `'Plan And Execute Non Trivial
Work'`, `'Foundation vs Map'` → `'Foundation Vs Map'`, every `'Overview'` →
`'Guides'`/`'Core'`). The baseline is transitional — a page gains `title:`
frontmatter and drops out of it, so the registry shrinks rather than becoming
permanent furniture.

**Ordering:** within a pack group, `order` sorts **across kinds**, matching the
schema and the existing `atlassian` sequence. Pages without `order` fall into
kind buckets beneath the ordered run.

## Boundaries

### Always do

- Build the inventory from path structure so a page with no frontmatter still
  appears. Only 20 of 182 files carry frontmatter.
- Derive a slug equal to the **Starlight slug of the file `mirror_guides()`
  writes** — its written path with a trailing `/index` stripped.
- Treat `order` as a pack-group-wide, cross-kind sort weight.
- Coerce a non-integer `order` to absent rather than raising.
- Declare guide group labels and order in `site.toml`'s `[[guide_groups]]`.
- Keep generation deterministic across filesystem enumeration order.

### Ask first

- Adding a field to `contracts/guide.schema.json`. It is
  `additionalProperties: false`; `order` already exists.
- Removing or renaming any published URL.
- Changing a reader-visible label beyond what the baseline and `site.toml`
  declare.

### Never do

- Drop a page or change a label that appears in the pre-change hand tree.
- Require frontmatter for a page to appear.
- Surface a `nav_eligible: false` file to readers.
- Modify `mirror_guides()`'s `canonical_slug`. It feeds alias redirect stubs;
  changing it is a routing change, which this spec forbids.
- Hand-edit `docs-site/src/sidebar-config.json`; it is generated and gitignored.

## Testing Strategy

`tools/build-site.py` is stdlib plus PyYAML, with an existing test module, so
both layers are unit-testable against a synthetic tree without invoking Astro.

- **Inventory (TDD)** — fixture trees covering no frontmatter, `title`/`slug`
  override, `README.md` at pack and nested depth, `_shared`/`_reference`,
  non-`.md` files, malformed frontmatter, non-integer `order`.
- **Slug parity (TDD)** — for every real file, the inventory slug equals the
  Starlight slug of what `mirror_guides()` writes. Guards against navigation
  pointing where the page is not.
- **Projection (TDD)** — cross-kind `order`, unordered fallback,
  `[[guide_groups]]` labels and order, and a pack absent from the table.
- **No-regression (goal-based)** — every `(slug, label)` pair in the frozen
  baseline appears unchanged in the generated output. Pairs, not slugs: a
  slug-only guard is blind to the 90 label regressions by construction.
- **Bijection (TDD)** — set equality between `nav_eligible` inventory slugs and
  generated sidebar slugs. A subset check passes while silently dropping pages.
- **Determinism (TDD)** — the inventory function accepts an injectable path
  enumerator; the test shuffles it and asserts byte-identical output. Without
  the seam the test re-globs and asserts nothing.
- **Live integration** — the `iac-terraform` arc below, plus the existing
  `atlassian` sequence as an independent regression witness.

## The live test: the infrastructure explanation arc

The generator is unproven until a real threaded sequence navigates in reading
order. This spec ships one and inherits a second.

The arc is not new doctrine. `iac-terraform` is the only pack declaring both
global gates G4 and G5, so it is the release loop specialized to infrastructure,
not a peer process. `_shared/the-three-loops` and
`release-engineering/the-release-loop` already carry the two-loop split, the
reversibility carve, and rehearse-then-release. The IaC pages **cite upward and
add only what is infrastructure-specific** — restating inherited doctrine
creates a second copy to drift.

| Page | `order` | Carries |
| --- | --- | --- |
| Infrastructure in the release loop | 1 | Where G4 and G5 land for infrastructure; what is identical to a code release and what is not |
| Deciding before generating | 2 | Recorded decisions before generation; the index as lookup, not library; why inventing a policy is the expensive failure |
| What the preview cannot tell you | 3 | Grounding against live provider schemas; why a preview is not a data-plane probe; the unmanaged-resource blind spot |

The `atlassian` pages are the witness that cross-kind ordering works.

## Acceptance Criteria

- [ ] AC1 — An inventory pass emits one record per `.md` file under `guides/`,
      each carrying every key in the Layer 1 table.
- [ ] AC2 — The set of generated sidebar slugs equals the set of `nav_eligible`
      inventory slugs exactly; `guides/AGENTS.md` appears in neither.
- [ ] AC3 — For every file, the inventory slug equals the Starlight slug of the
      file `mirror_guides()` writes (its path with trailing `/index` stripped),
      including `slug:` overrides. `mirror_guides()` is unmodified.
- [ ] AC4 — A page with no frontmatter appears in the projected sidebar,
      labelled from the baseline or its filename.
- [ ] AC5 — Label precedence in the projected sidebar is `title:` frontmatter →
      frozen baseline → filename-derived.
- [ ] AC6 — Within a pack group, entries declaring `order` sort ascending across
      kinds, ahead of undeclared siblings, which follow in kind buckets.
- [ ] AC7 — A non-integer `order` is treated as absent and does not raise.
- [ ] AC8 — Guide group labels and order come from `site.toml`'s
      `[[guide_groups]]` table; groups render as a flat list under "Guides"
      without inheriting the six `[[groups]]` super-groups; `_shared` and
      `_reference` have declared entries; a pack absent from the table still
      produces a group.
- [ ] AC9 — Every `(slug, label)` pair in the frozen baseline appears unchanged
      in the generated output. No page and no label regresses.
- [ ] AC10 — Shuffling the injected path enumerator produces byte-identical
      output.
- [ ] AC11 — The hand-maintained guides block (lines 86–544) is removed from
      `docs-site/astro.config.ts`; the surviving sidebar is exactly Home, Get
      Started, the `sidebar-config.json` spread, Changelog, and Contributing.
- [ ] AC12 — Three explanation pages exist under
      `guides/iac-terraform/explanation/` declaring `order` 1–3, each linking to
      `release-engineering/explanation/the-release-loop` in its opening section
      via the relative form the tree uses.
- [ ] AC13 — In the built sidebar the IaC arc renders 1–3, and the four ordered
      `atlassian` pages render as a flat run ahead of their kind buckets — the
      post-change shape, not the hand-placed one.
- [ ] AC14 — The documented build sequence completes; the rendered sidebar was
      inspected and the observation recorded in
      `docs/specs/guides-sidebar-generation/notes/rendered-check.md`.
- [ ] AC15 — `guides/AGENTS.md` § Traps states the generated contract, `order`
      semantics, the `[[guide_groups]]` declaration, and the transitional label
      baseline instead of claiming the sidebar is hand-maintained.

## Assumptions

- `tools/build-site.py` runs before both site builds in
  `.github/workflows/pages.yml`, so no CI change is needed.
- Starlight accepts the `{label, slug}` and `{label, items}` shapes the
  pack-catalogue groups already use.
- Kind-bucket labels keep their current words.
- No published guide URL changes. This spec touches navigation only.
- **Guide group order changes visibly.** Declaring order in `[[guide_groups]]`
  is an opportunity to fix today's ad-hoc sequence; the initial table reproduces
  today's order exactly, so this PR ships zero group reordering. Reordering is a
  later, separate, reviewable edit to one table.

## Out of scope

- **Migrating the 161 other frontmatter-less guides.** Confirmed with the user
  2026-08-06. The path-derived inventory and the frozen baseline make it
  unnecessary; migration proceeds incrementally with no further code change.
- **The `guides/iac-terraform/README.md` stage-count drift.** It claims an
  "8-stage generation loop" and "Stages 2–7" where `generate-iac/SKILL.md`
  defines Stage 0–6. Pre-existing, user-visible, invisible to the generator — it
  fails the bundled-fixes carve-out. This PR **will record** it in
  `workspace.toml [backlog].open` as `iac-guides-readme-stage-drift`.
- **`docsUrl` routing.** Already correct (`/docs/guides/<pack>/`) as of
  2026-08-06. Two register entries already cover the area —
  `web-docs-link-check-gate` and `phase4b-docsurl-instruction-stale`. Do not
  re-open; the same fix has landed and reverted twice (#852 → #854).
