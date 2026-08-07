# Spec: guides-sidebar-generation

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** `contracts/guide.schema.json` (frontmatter contract), `site.toml` (site recipe — sidebar grouping and pack ordering), [`docs-site/AGENTS.md`](../../../docs-site/AGENTS.md) (build order), [`guides/AGENTS.md`](../../../guides/AGENTS.md) (publication routing)
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

**Pages are missing.** The sidebar is a 460-line literal tree in
`docs-site/astro.config.ts` (lines 86–544) listing 118 guide entries by hand.
181 navigable guide files exist on disk, so **67 published pages are absent from
navigation** — reachable only by search or a direct link. Adding a page and
forgetting the config edit is the default outcome, not the exception.

**Sequence cannot be expressed where it is generated.** The hand tree nests
pack → Diátaxis kind, which sorts by what a page *is* rather than what a reader
should read next. `contracts/guide.schema.json` already defines `order` as
"sort weight within a pack group," and four `atlassian` pages already use it as
a cross-kind reading order (`tutorial → how-to → reference → explanation`, 1–4).
That sequence works only because someone hand-placed it in the config; nothing
generates it, and nothing protects it.

## Context

This spec was shaped in-session (2026-08-06) from a walkthrough of the
`iac-terraform` flow. The request that produced it: an organization adopting
central infrastructure practice needs a narrative arc in human language that
navigates well, and a journey page is a preview that does not carry the process.

## Approach: collate before you project

The change is a translation, and it is specified as one. Source material is
collated into a **predictable inventory** first; the sidebar is projected from
that inventory second. The inventory is a real artifact — dumpable, diffable,
and testable on its own — not an intermediate hidden inside a generator.

This split is load-bearing. Every awkward fact about the source material
(curated group labels, index-page slug normalization, files that must never
appear to readers, `slug:` overrides, cross-kind ordering) becomes a **declared
field on a record** instead of a branch buried in projection logic. It also
makes the change reviewable: the before/after navigation diff is computable from
the inventory, so "no page regressed" is proven rather than asserted.

### Layer 1 — Inventory

One deterministic pass over `guides/` produces one record per file:

| Field | Source |
| --- | --- |
| `source_path` | the file |
| `pack` | first path segment (`_shared`, `_reference` included) |
| `kind` | `kind:` frontmatter when present, else the kind directory, else none |
| `order` | `order:` frontmatter; integer or absent |
| `title` | `title:` frontmatter, else derived from the filename |
| `slug` | `slug:` frontmatter when present, else derived — **must equal what `mirror_guides()` writes** |
| `nav_eligible` | false for `AGENTS.md`; true otherwise |
| `in_nav_today` | whether the slug appears in the current hand tree |

Measured against the tree at spec time: 182 files, 1 nav-ineligible
(`guides/AGENTS.md`), 181 eligible, 181 distinct slugs (zero collisions), 118 in
navigation, **67 absent**. These are the spec's single statement of the
measurements; the plan references them rather than restating them.

### Layer 2 — Projection

The inventory becomes sidebar groups. Group labels and group order come from
`site.toml`, which already exists as the site recipe and already owns "sidebar
grouping and pack ordering" for the pack catalogue. Guide group labels are
curated editorial names that no path or `pack.toml` field can derive —
`'The Build Loop (core)'` where `pack.toml` says `"Core"`, `'Product Discovery'`
where it says `"Product Engineering"` — so they are declared, not inferred.

Within a pack group, `order` sorts **across kinds**, matching the schema's
definition and the existing `atlassian` sequence. Pages without `order` fall
into their kind buckets beneath the ordered run.

## Boundaries

### Always do

- Produce the inventory from path structure so a page with no frontmatter still
  appears. Only 20 of 182 guide files carry frontmatter; a frontmatter-sourced
  inventory would omit the rest.
- Derive a slug that equals `mirror_guides()`'s output, including its
  `README.md` → parent-directory normalization (`guides/core/README.md` →
  `guides/core`, never `guides/core/index`) and its `slug:` override handling.
- Treat `order` as a pack-group-wide, cross-kind sort weight.
- Coerce a non-integer `order` to absent rather than raising.
- Declare group labels and group order in `site.toml`.
- Keep generation deterministic across filesystem enumeration order.

### Ask first

- Adding a field to `contracts/guide.schema.json`. It is
  `additionalProperties: false`; `order` already exists and needs no change.
- Removing or renaming any published URL.
- Changing a reader-visible group label beyond what `site.toml` declares.

### Never do

- Drop a page that appears in the current hand-maintained tree.
- Require frontmatter for a page to appear.
- Surface a `nav_eligible: false` file to readers.
- Hand-edit `docs-site/src/sidebar-config.json`; it is generated and gitignored.
- Change what `mirror_guides()` publishes or where. This spec changes navigation
  only, never routing.

## Testing Strategy

`tools/build-site.py` is stdlib plus PyYAML, with an existing test module
(`tools/test_build_site_routing.py`), so both layers are unit-testable against a
synthetic tree without invoking Astro.

- **Inventory (TDD)** — records built from fixture trees covering: no
  frontmatter, `title` override, `slug` override, `README.md` at pack and
  nested depth, `_shared`/`_reference`, non-`.md` files, malformed frontmatter,
  and non-integer `order`.
- **Slug parity (TDD)** — for every real file under `guides/`, the inventory
  slug equals the slug `mirror_guides()` derives. This is the guard against
  navigation pointing where the page is not.
- **Projection (TDD)** — cross-kind `order` sorting, unordered fallback,
  `site.toml` label and order application, and a group for a pack absent from
  `site.toml`.
- **No-regression (goal-based)** — every slug in the current hand tree appears
  in the generated output. This is the real guard against the 67-missing defect;
  count parity alone would let a page satisfy the test while sitting in the
  wrong group.
- **Determinism (TDD)** — shuffle the discovered-file list before a second run
  and assert byte-identical output, so the test cannot pass merely because
  Python's `sorted()` is stable.
- **Live integration** — the `iac-terraform` arc below, plus the existing
  `atlassian` sequence as an independent regression witness.

## The live test: the infrastructure explanation arc

The generator is unproven until a real threaded sequence navigates in reading
order. This spec ships one, and inherits a second.

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

The `atlassian` pages (`order` 1–4, four different kinds) are the witness that
cross-kind ordering already works and must not regress.

## Acceptance Criteria

- [ ] AC1 — An inventory pass emits one record per file under `guides/` carrying
      every field in the Layer 1 table.
- [ ] AC2 — Every `nav_eligible` file yields exactly one sidebar entry;
      `guides/AGENTS.md` yields none.
- [ ] AC3 — For every file under `guides/`, the inventory slug equals the slug
      `mirror_guides()` derives, including `README.md` → parent-directory
      normalization and `slug:` overrides.
- [ ] AC4 — A page with no frontmatter appears, labelled from its path.
- [ ] AC5 — Frontmatter `title` overrides the path-derived label.
- [ ] AC6 — Within a pack group, entries declaring `order` sort ascending across
      kinds, ahead of undeclared siblings, which follow in kind buckets.
- [ ] AC7 — A non-integer `order` is treated as absent and does not raise.
- [ ] AC8 — Group labels and group order come from `site.toml`; a pack absent
      from `site.toml` still produces a group.
- [ ] AC9 — Every slug present in the pre-change hand tree is present in the
      generated output. No page regresses.
- [ ] AC10 — Shuffling the discovered-file order produces byte-identical output.
- [ ] AC11 — The hand-maintained guides block (lines 86–544) is removed from
      `docs-site/astro.config.ts`; the surviving sidebar is Home, Get Started,
      the `sidebar-config.json` spread, Changelog, and Contributing.
- [ ] AC12 — Three explanation pages exist under
      `guides/iac-terraform/explanation/` declaring `order` 1–3, each containing
      a link to `guides/release-engineering/explanation/the-release-loop` in its
      opening section.
- [ ] AC13 — The IaC arc renders in `order` in the built sidebar, and the
      `atlassian` sequence still renders 1–4 across its four kinds.
- [ ] AC14 — The documented build sequence completes and the rendered sidebar
      was inspected; observed result recorded.
- [ ] AC15 — `guides/AGENTS.md` § Traps states the generated contract, `order`
      semantics, and the `site.toml` group declaration instead of claiming the
      sidebar is hand-maintained.

## Assumptions

- `tools/build-site.py` runs before both site builds in
  `.github/workflows/pages.yml`, so a generated guides sidebar needs no CI change.
- Starlight accepts the same `{label, slug}` and `{label, items}` shapes for
  guides groups that the pack-catalogue groups already use.
- Kind-bucket labels keep their current words ("Explanation", "How-to",
  "Reference", "Tutorials").
- No published guide URL changes. This spec touches navigation only.
- Reusing `site.toml`'s existing group order for guides is acceptable and
  desirable — it makes the two sidebar sections consistent. It is a visible
  reordering of guide groups relative to today's hand tree.

## Out of scope

- **Migrating the 161 other frontmatter-less guides.** Confirmed with the user
  2026-08-06. The path-derived inventory makes it unnecessary; migration can
  proceed incrementally later with no further code change.
- **The `guides/iac-terraform/README.md` stage-count drift.** It claims an
  "8-stage generation loop" and "Stages 2–7" where
  `packs/iac-terraform/.apm/skills/generate-iac/SKILL.md` defines Stage 0–6.
  Pre-existing, user-visible, and invisible to the generator — it fails the
  bundled-fixes carve-out. Recorded in `workspace.toml [backlog].open`.
- **Whether `docsUrl` resolves.** The marketing site renders
  `withBase('/guides/<pack>/')` while guides publish under `/docs/guides/<pack>/`.
  If broken it affects all packs and is a routing fix, not a navigation one.
  Verify during the rendered check; record a backlog entry if confirmed.
