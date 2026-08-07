# Spec: guides-sidebar-generation

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** `contracts/guide.schema.json` (frontmatter contract), [`docs-site/AGENTS.md`](../../../docs-site/AGENTS.md) (build order), [`guides/AGENTS.md`](../../../guides/AGENTS.md) (publication routing)
- **Brief:** user direction in-session (2026-08-06): the docs site must carry a narrative arc a reader can follow front to back, not a taxonomy bucket list. The hand-maintained sidebar cannot express reading order and silently drops pages.
- **Contract:** none
- **Shape:** build

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it.

## Objective

The docs-site guides sidebar is generated from what is on disk, so every
published guide appears in navigation and threaded sequences read in their
intended order.

Today the sidebar is a 460-line literal tree in `docs-site/astro.config.ts`
(lines 87–547) listing 118 guide entries by hand. There are 182 guide files on
disk, so **64 published pages are absent from navigation** — reachable only by
search or direct link. The tree also groups strictly pack → Diátaxis kind,
which sorts by what a page *is* rather than what a reader should read next, so
an ordered explanation sequence cannot be expressed at all.

`generate_sidebar_config()` in `tools/build-site.py:668` already generates the
pack-catalogue portion of the sidebar into the gitignored
`docs-site/src/sidebar-config.json`. This spec extends that generator to cover
guides and deletes the hand-maintained block.

**Path structure is the source; frontmatter refines it.** Only 20 of the 182
guide files carry frontmatter and none currently sets `order`, so a
frontmatter-sourced sidebar would omit 162 pages. Every file has a path, so
`guides/<pack>/<kind>/<slug>.md` supplies grouping and labels universally;
`title` and `order` override the derived values where present.

## Boundaries

### Always do

- Derive pack group, kind bucket, and a fallback label from the file path, so a
  page with no frontmatter still appears.
- Prefer frontmatter `title` over the path-derived label when present.
- Order a group's entries by `order` ascending when any sibling declares it;
  place undeclared siblings after ordered ones, alphabetically.
- Keep `README.md` as the group's index entry, matching the existing mirror
  behavior in `mirror_guides()`.
- Honour a `slug:` override when computing the sidebar link, so the entry points
  where `mirror_guides()` actually writes the page.
- Emit the generated guides groups into `docs-site/src/sidebar-config.json`
  alongside the existing pack-catalogue groups.
- Keep the generator deterministic — identical input tree produces byte-identical
  JSON, so a rebuild never produces a spurious diff.

### Ask first

- Changing the visible grouping vocabulary (the labels a reader sees for kind
  buckets, e.g. "How-to" vs "Guides").
- Adding a field to `contracts/guide.schema.json`. The schema is
  `additionalProperties: false`; `order` already exists and needs no change.
- Removing or renaming any existing published URL.

### Never do

- Drop a page from navigation that appears in the current hand-maintained tree.
- Require frontmatter for a page to appear — that would regress 162 pages.
- Hand-edit `docs-site/src/sidebar-config.json`; it is generated and gitignored.
- Change what `mirror_guides()` publishes or where. This spec changes navigation
  only, never routing.

## Testing Strategy

`tools/build-site.py` is pure-stdlib Python with an existing test file
(`tools/test_build_site_routing.py`), so the generator is unit-testable
against a synthetic tree without invoking Astro.

- **Unit (TDD)** — `generate_sidebar_config()` against a fixture tree covering:
  no frontmatter, `title` override, `order` sequencing, mixed ordered/unordered
  siblings, `slug` override, `README.md` as index, and determinism (two runs,
  identical bytes).
- **Coverage assertion (goal-based)** — every `.md` file under `guides/` yields
  exactly one sidebar entry. This is the regression guard for the 64-missing
  defect; assert on a computed count, not a hardcoded number.
- **Rendered check (manual QA)** — run the documented build sequence and confirm
  the sidebar renders, a threaded sequence appears in `order`, and a
  previously-missing page is now present.

## Acceptance Criteria

- [ ] AC1 — `generate_sidebar_config()` emits guides groups derived from the
      `guides/` tree, in addition to the existing pack-catalogue groups.
- [ ] AC2 — Every `.md` file under `guides/` produces exactly one sidebar entry;
      a test asserts entry count equals discovered file count.
- [ ] AC3 — A page with no frontmatter appears, labelled from its path.
- [ ] AC4 — Frontmatter `title` overrides the path-derived label.
- [ ] AC5 — Within a group, entries declaring `order` sort ascending ahead of
      undeclared siblings, which follow alphabetically.
- [ ] AC6 — A page declaring `slug:` links to its overridden path, matching
      `mirror_guides()` output.
- [ ] AC7 — The hand-maintained guides block is removed from
      `docs-site/astro.config.ts`; the file shrinks by ~460 lines and the
      remaining sidebar composes from `sidebar-config.json`.
- [ ] AC8 — Two consecutive generator runs on an unchanged tree produce
      byte-identical `sidebar-config.json`.
- [ ] AC9 — The documented build sequence completes and the rendered sidebar was
      inspected; observed result recorded.
- [ ] AC10 — `guides/AGENTS.md` § Traps no longer claims the sidebar is
      hand-maintained; it states the generated contract and how `order` works.

## Assumptions

- The gitignored `sidebar-config.json` is generated on every build by
  `tools/build-site.py`, which `.github/workflows/pages.yml` runs before both
  site builds. A generated guides sidebar therefore needs no CI change.
- Starlight accepts the same `{label, slug}` and `{label, items}` shapes for
  guides groups that the pack-catalogue groups already use.
- Kind-bucket labels stay as the current tree words them ("Explanation",
  "How-to", "Reference", "Tutorials") — no reader-visible vocabulary change.
- No published guide URL changes. This spec touches navigation only.
