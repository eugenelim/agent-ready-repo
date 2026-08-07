# Spec: guides-sidebar-generation

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0020](../../adr/0020-per-pack-diataxis-hierarchy-for-guides.md) (per-pack Diátaxis hierarchy), [ADR-0055](../../adr/0055-starlight-replaces-mkdocs-for-reference-docs.md) (Starlight), [`guide-source-model`](../guide-source-model/spec.md) (frontmatter declares kind), `contracts/guide.schema.json`, `site.toml` (site recipe), [`docs-site/AGENTS.md`](../../../docs-site/AGENTS.md) (build order), [`guides/AGENTS.md`](../../../guides/AGENTS.md) (publication routing)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it.

## Intent

**A reader can follow an argument through the docs from one page to the next,
and no reader-facing page is unreachable.**

("Reader-facing" excludes two kinds of page, both still mirrored and so still
reachable by URL: `guides/AGENTS.md`, which is maintainer context, and any `README.md` more than one
directory below `guides/` — today the four `guides/_shared/<kind>/README.md`
section-authoring templates ("Writing a how-to"), which address whoever writes
the guides rather than the adopter who reads them. Neither was in the
pre-change sidebar, so keeping them out preserves the status quo. The rule is
stated by depth rather than by "kind directory" because that is what the code
enforces, and because a nested index that *were* included would derive the
label `Overview` and collide with its pack index. Each exclusion prints a
`note` at build time, so a future one is never silent. Excluding them from the *mirror* would be a routing change,
which this spec forbids.)

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
| `kind` | `kind:` frontmatter when present, else the kind directory **normalized to the schema enum**, else none |
| `order` | `order:` frontmatter; integer, else absent |
| `title` | `title:` frontmatter, or absent — the page's own title only. The label chain that consumes it is stated once, in § Layer 2 |
| `slug` | `slug:` frontmatter when present, else derived — **must equal the Starlight slug of the file `mirror_guides()` writes** |
| `is_index` | true for `README.md` at any depth |
| `nav_eligible` | false for `AGENTS.md` and for any `README.md` more than one directory below `guides/`; true otherwise |

**On the `kind` directory fallback.** `guide-source-model` AC3 (shipped) states
that the physical directory does not determine kind. This spec relaxes that
**only for pages carrying no `kind:` frontmatter** — 162 files carry none, 161
of them nav-eligible. Where frontmatter declares a kind it always wins. The
relaxation is deliberate and scoped: the alternative is 161 uncategorized pages,
and the long-term fix is frontmatter migration, not a different fallback.

**The directory fallback normalizes to the schema enum.** The on-disk directory
is `tutorials/`; the schema enum is `tutorial`. Without normalization, the first
page under `guides/core/tutorials/` to gain frontmatter splits `core` into a
`Tutorial` bucket and a `Tutorials` bucket. Today 13 packs derive `tutorials`
from the directory and 4 declare `tutorial` in frontmatter, so nothing trips it
yet — which is exactly why it must be pinned before migration begins.

**Pre-change measurements** (2026-08-06; single statement, the plan references
this section rather than restating — the shipped tree is larger, since this PR
adds the three arc pages): 182 `.md` files, 1 nav-ineligible (`guides/AGENTS.md`), 181
eligible, 181 distinct slugs (zero collisions), 119 entries in the hand tree,
**62 absent**. Extract nav slugs with the pattern `slug: '(guides(/…)?)'` — a
`guides/`-prefixed match silently drops the root `guides` entry and yields 118.

### Layer 2 — Projection

The inventory becomes sidebar groups.

**Group labels and order** come from a `[[guide_groups]]` table in `site.toml`,
**separate from the existing `[[groups]]` table**. The existing table is routed
through `discover_packs()`, which skips `_`-prefixed slugs and warns on any slug
without a `packs/<slug>/pack.toml` — so it structurally cannot express `_shared`
or `_reference`. A distinct table gives both a declared home.

Each entry is `dir` (a directory name under `guides/`) plus `label`. Table order
is group order. **An entry is required for every directory under `guides/`**,
not merely those the hand tree happens to carry — five real packs
(`_reference`, `catalogue-curation`, `github`, `iac-terraform`, `linear`) have
no group today, and `iac-terraform` is where this spec's own live test lands.
An undeclared directory falls back to a group labelled from its title-cased
directory name, appended after all declared groups.

Guide groups render as a **flat list of pack groups** under "Guides", matching
today's shape; `site.toml`'s six super-group labels are not inherited, which
avoids a five-level nesting Starlight has never been asked to render.

**Labels** resolve **frozen baseline → `title:` frontmatter → filename-derived**.
The baseline wins while an entry exists. This ordering matters: 13 pages already
carry a `title:` differing from their hand-tree label
(`guides/atlassian/work-with-jira.md` is `'Work with Jira'` in nav and
`'Work with Jira from a conversation'` in frontmatter), so putting frontmatter
first would silently rewrite 13 reader-facing labels and put AC5 in direct
conflict with AC9. Baseline-first makes *removing* an entry the deliberate,
reviewable act that adopts a page's own title — so the registry still shrinks,
but only on purpose.

An index page with neither a baseline entry nor a `title:` reads `Overview`
rather than the filename-derived `Readme`, matching every index entry in the
pre-change tree.

The baseline is required at all: filename derivation alone changes 90 of the 119
existing labels (`'Foundation vs Map'` → `'Foundation Vs Map'`, every
`'Overview'` → `'Guides'`/`'Core'`).

**Ordering.** Within a pack group:

1. `is_index` records are direct items of the group, ahead of everything else —
   preserving today's `{ label: 'Overview', slug: 'guides/core' }` shape. The
   root `guides/README.md` is a direct item of the "Guides" group itself; it has
   no pack path segment, so `pack` resolves to the tree root, not `README.md`.
2. Records declaring `order` follow, sorted ascending **across kinds**, matching
   the schema and the existing `atlassian` sequence.
3. Records with **no `kind` and no `is_index`** follow as direct group items.
   Without this rule `guides/_reference/catalogue-format.md` — no frontmatter,
   not a README, in no kind directory — falls through every other rule into a
   bucket that does not exist, and is silently droppable. It is the only such
   file in the tree today.
4. Remaining records fall into kind buckets, alphabetical within each. Bucket
   sequence is the canonical `Tutorials, How-to, Reference, Explanation`.
   Today's tree is not uniform, so pinning one sequence visibly reorders buckets
   — see § Assumptions for exactly which groups move. That is an accepted, named
   consequence, not an accident.

Emission order within a group is therefore: `is_index` → `order`-declaring →
kind-less non-index → kind buckets.

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
  non-`.md` files, malformed frontmatter, non-integer `order`, a `tutorials/`
  directory normalizing to kind `tutorial`, and a page carrying `kind: tutorial`
  frontmatter inside a `tutorials/` directory (the mixed case that would
  otherwise split one pack into two buckets).
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
- **Nesting depth (TDD)** — the guides portion has exactly one level of pack
  groups under "Guides", and none of the six `[[groups]]` super-group labels
  appears there.
- **Live integration (visual / manual QA)** — the `iac-terraform` arc below,
  plus the existing `atlassian` sequence as an independent regression witness.

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

- [x] AC1 — An inventory pass emits one record per `.md` file under `guides/`,
      each carrying every key in the Layer 1 table.
- [x] AC2 — The set of slugs under the generated **Guides** groups equals the set
      of `nav_eligible` inventory slugs exactly; `guides/AGENTS.md` and the
      kind-directory authoring templates appear in neither. Pack-catalogue and
      top-level slugs are outside this set. No two siblings of one group share a
      label — pages and kind buckets alike.
- [x] AC3 — For every file, the inventory slug equals the Starlight slug of the
      file `mirror_guides()` writes (its path with trailing `/index` stripped),
      including `slug:` overrides. `mirror_guides()` is unmodified.
- [x] AC4 — A page with no frontmatter appears in the projected sidebar,
      labelled from the baseline or its filename.
- [x] AC5 — Label precedence in the projected sidebar is frozen baseline →
      `title:` frontmatter → filename-derived, so the 13 pages whose `title:`
      differs from their baseline label keep the baseline label. An index page
      falling through to derivation reads `Overview`.
- [x] AC6 — Within a pack group the emission order is exactly: (1) `is_index`
      records as direct items, (2) `order`-declaring records ascending across
      kinds, (3) kind-less non-index records as direct items, (4) the remainder
      in kind buckets ordered `Tutorials, How-to, Reference, Explanation`,
      alphabetical within each. The root `guides/README.md` is a direct item of
      the "Guides" group.
- [x] AC7 — A non-integer `order` is treated as absent and does not raise; a
      `tutorials/` directory normalizes to kind `tutorial`.
- [x] AC8 — `site.toml`'s `[[guide_groups]]` entries are `dir` + `label`, table
      order is group order, and an entry exists for **every** directory under
      `guides/` — including `_shared`, `_reference`, `iac-terraform`,
      `catalogue-curation`, `github`, and `linear`. An undeclared directory
      produces a group labelled from its title-cased directory name, appended
      after all declared groups. Groups render as a flat list under "Guides"
      with no `[[groups]]` super-group label present.
- [x] AC9 — Every `(slug, label)` pair in the frozen baseline appears unchanged
      in the generated output. No page and no label regresses. (Pair equality is
      order-insensitive by design; AC6 governs sequence.)
- [x] AC10 — Shuffling the injected path enumerator produces byte-identical
      output.
- [x] AC11 — The hand-maintained `{ label: 'Guides', items: [...] }` entry —
      lines 86–544 at spec time, but identified by content, not line number — is
      removed from `docs-site/astro.config.ts`; the surviving top-level sidebar
      entries are exactly Home, Get Started, the `sidebar-config.json` spread,
      Changelog, and Contributing. This is the canonical statement of the range;
      Intent and the plan reference it.
- [x] AC12 — Three explanation pages exist under
      `guides/iac-terraform/explanation/` declaring `order` 1–3, each containing
      the literal `](../../release-engineering/explanation/the-release-loop.md)`
      within its first 40 lines. The relative form matters: an absolute
      `guides/…` path rewrites to a dead GitHub URL.
- [x] AC13 — In the built sidebar the IaC arc renders 1–3, and the four ordered
      `atlassian` pages render as a flat run ahead of their kind buckets — the
      post-change shape, not the hand-placed one.
- [x] AC14 — The documented build sequence completes; the rendered sidebar was
      inspected and the observation recorded in
      `docs/specs/guides-sidebar-generation/notes/rendered-check.md`.
- [x] AC15 — `guides/AGENTS.md` § Navigation is generated states the generated contract, `order`
      semantics, the `[[guide_groups]]` declaration, and the transitional label
      baseline instead of claiming the sidebar is hand-maintained.
- [x] AC16 — `workspace.toml [backlog].open` carries
      `iac-guides-readme-stage-drift` with a cold-start-sufficient comment.

## Assumptions

- `tools/build-site.py` runs before both site builds in
  `.github/workflows/pages.yml`, so no CI change is needed.
- Starlight accepts the `{label, slug}` and `{label, items}` shapes the
  pack-catalogue groups already use.
- Kind-bucket labels keep their current words.
- No published guide URL changes. This spec touches navigation only.
- **Pack-group order does not change; kind-bucket order does, in 11 of 17
  groups.** The initial `[[guide_groups]]` table reproduces today's pack-group
  sequence exactly, so no pack group moves — except the five that had no group
  at all and are now declared. Kind buckets *do* move: pinning
  `Tutorials, How-to, Reference, Explanation` reorders buckets in 11 of the 17
  existing pack groups. Six already match the canonical sequence and do not
  move: `frontend-engineering`, `atlassian`, `converters`, `figma`,
  `governance-extras`, `monorepo-extras`. This is a visible, intentional change
  and the approver is approving it.

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
