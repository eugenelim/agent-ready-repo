# Plan: guides-sidebar-generation

- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I will touch**
- `tools/build-site.py` — extend `generate_sidebar_config()`; add path/frontmatter
  derivation helpers.
- `tools/test_build_site_routing.py` — new tests (or a sibling test module if the
  existing file's scope is strictly routing).
- `docs-site/astro.config.ts` — delete the hand-maintained guides block (lines
  87–547), leaving the spread of `sidebar-config.json`.
- `guides/AGENTS.md` — replace the hand-maintained-sidebar trap with the
  generated contract (AC10).

**Tests that demonstrate done**
- Unit tests over `generate_sidebar_config()` against a synthetic tree.
- A coverage test asserting one sidebar entry per discovered `.md` file.
- A determinism test asserting two runs match byte-for-byte.
- Rendered inspection of the built site.

**What I am NOT changing**
- `mirror_guides()` — routing and published URLs stay exactly as they are.
- `contracts/guide.schema.json` — `order` already exists; no schema change.
- Kind-bucket label vocabulary shown to readers.
- The pack-catalogue portion of the sidebar.
- `.github/workflows/pages.yml` — the generator already runs there.

## Declined patterns

- **Migrating all 162 frontmatter-less guides first.** Tempting because a
  frontmatter-sourced sidebar is conceptually cleaner. Declined: it is a
  162-file mechanical change riding along with a build-system change, and the
  path-derived fallback makes it unnecessary. Migration can proceed
  incrementally afterwards with no further code change.
- **Adding a `next:` frontmatter field for in-page continuation links.**
  Declined: the schema is `additionalProperties: false`, so it needs a schema
  change, and plain markdown links achieve the same thing today. Revisit only if
  authors actually find the manual links unmaintainable.
- **Auto-generating the sidebar directly in `astro.config.ts` via a filesystem
  walk.** Declined: it would split sidebar knowledge across two languages and
  duplicate the slug/routing rules `build-site.py` already owns.
- **A `sidebar_order` config file listing sequences explicitly.** Declined: a
  second source of truth beside frontmatter, and it rots the moment a file moves.
- **Introducing a "Start here" or arc-specific group type.** Declined: no second
  caller yet. `order` alone expresses sequence; a distinct group type is only
  warranted once a real arc exists and proves ordering insufficient.

## Tasks

### T1: Derivation helpers — path → (pack, kind, label, link)

Mode: TDD
Tests: `test_derive_entry_from_path` — asserts `guides/core/how-to/bug-fix.md`
yields pack `core`, kind `how-to`, label `Bug Fix`, link `guides/core/how-to/bug-fix`;
`guides/core/README.md` yields the pack index entry; a `_shared` path yields the
shared group.
Approach: pure functions taking a `Path` relative to `guides/`, returning a
dataclass or dict. No I/O, so they are trivially testable.
Done when: tests pass; helpers handle README, nested kind dirs, and `_shared`.
Depends on: none

### T2: Frontmatter overlay — `title`, `order`, `slug`

Mode: TDD
Tests: `test_frontmatter_overrides_label` (title wins over derived label);
`test_slug_override_changes_link` (link matches `mirror_guides()` placement);
`test_order_absent_is_none` (no `order` key → sorts after ordered siblings).
Approach: reuse the existing `_parse_frontmatter()` rather than adding a parser.
Read each file once; tolerate absent or malformed frontmatter by falling back to
derived values — never raise.
Done when: tests pass; a malformed-frontmatter fixture still yields an entry.
Depends on: T1

### T3: Group assembly and ordering

Mode: TDD
Tests: `test_ordered_before_unordered` (order 1, 2 precede alphabetical
undeclared); `test_stable_alphabetical_fallback`; `test_readme_is_group_index`.
Approach: group by pack, then by kind; sort within a group by
`(order is None, order, label)` so declared order wins and undeclared siblings
stay alphabetical.
Done when: tests pass for mixed ordered/unordered groups.
Depends on: T2

### T4: Wire into `generate_sidebar_config()`

Mode: TDD
Tests: `test_sidebar_includes_pack_catalogue_and_guides` (both present);
`test_every_guide_file_has_one_entry` (AC2 — computed count, not a literal);
`test_generation_is_deterministic` (AC8 — two runs, identical bytes).
Approach: extend the existing signature to take the guides root; append guides
groups after the pack-catalogue groups. Keep the JSON serialization path
unchanged so the gitignored artifact's shape stays compatible.
Done when: tests pass; `python3 tools/build-site.py` reports the generated
group count.
Depends on: T3

### T5: Remove the hand-maintained block from `astro.config.ts`

Mode: goal-based check
Tests: no stub (goal-based).
Done when: the literal guides block (lines 87–547) is deleted; the file's
sidebar array is Home + Get Started + the `sidebar-config.json` spread;
`grep -c "slug: 'guides/" docs-site/astro.config.ts` returns 0; the docs-site
build completes.
Depends on: T4

### T6: Rendered verification

Mode: visual / manual QA
Tests: no stub (manual QA).
Approach: run the load-bearing build sequence from `docs-site/AGENTS.md`
(`build-site.py`, then `web` build, then `docs-site` build). Inspect the rendered
sidebar. Confirm a page absent from the old tree now appears, and that an
`order`-bearing fixture sequence renders in order.
Done when: observed sidebar state recorded, including the page that was
previously missing (AC9).
Depends on: T5

### T7: Update `guides/AGENTS.md` § Traps

Mode: goal-based check
Tests: no stub (goal-based).
Done when: the hand-maintained-sidebar trap is replaced by the generated
contract and how `order` sequences a group; `python3 tools/lint-agents-md.py`
passes and the file stays under the 150-line subdirectory cap (AC10).
Depends on: T6

## Risks

- **Starlight may reject a group shape the pack-catalogue path never exercises**
  (deeply nested `items`). Mitigation: T6 is a real build, not a unit assertion;
  a shape failure surfaces there. If it fires, flatten one nesting level.
- **Entry-count parity is necessary but not sufficient** — a page could appear
  under the wrong group and still satisfy AC2. T1–T3 tests assert placement, not
  just presence.
- **`sidebar-config.json` is gitignored**, so a generator regression is invisible
  in review and only shows at build. The determinism and coverage tests are the
  compensating control.

## Changelog

- 2026-08-06 — initial draft. Design corrected at PLAN after measuring frontmatter
  coverage: 20 of 182 guide files carry frontmatter and none sets `order`, so
  path structure is the source and frontmatter the refinement, not the reverse.
