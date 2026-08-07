# Plan: guides-sidebar-generation

- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Spec:** [`spec.md`](spec.md)

> Measurements are stated once in [`spec.md` § Layer 1](spec.md#layer-1--inventory).
> This plan references them; it does not restate the numbers.

## Assumption trio

**Files I will touch**
- `tools/build-site.py` — inventory pass, projection, extended
  `generate_sidebar_config()`.
- `tools/test_build_site_routing.py` (or a sibling module) — tests for both layers.
- `site.toml` — new `[[guide_groups]]` table.
- `guide-nav-baseline.toml` — frozen `(slug, label)` pairs. Repo root, beside
  `site.toml`: it is a hand-curated build *input* read by `tools/build-site.py`,
  and `docs-site/` otherwise holds generated output.
- `docs-site/astro.config.ts` — delete the hand-maintained guides block.
- `guides/iac-terraform/explanation/*.md` — three new pages, the live test.
- `guides/AGENTS.md` — replace the hand-maintained-sidebar trap.
- `workspace.toml` — one `[backlog].open` entry.
- `Makefile`, `.github/workflows/{build-check,pages,docs}.yml` — wire the new
  tests into a gate and add the new build inputs to the path triggers.
- `AGENTS.local.md` — route agents to `guides/AGENTS.md`; agreed with the
  user before EXECUTE, listed here rather than as a bundled fix.
- `docs/specs/guides-sidebar-generation/notes/rendered-check.md` — the AC14 record.

**Tests that demonstrate done**
- Inventory unit tests over fixture trees.
- Slug parity against what `mirror_guides()` writes, for every real file.
- Projection tests for cross-kind `order`, label precedence, `[[guide_groups]]`.
- Bijection (set equality) between eligible inventory slugs and sidebar slugs.
- No-regression on frozen `(slug, label)` pairs.
- Determinism under a shuffled injected enumerator.
- The IaC arc and the existing `atlassian` sequence rendering correctly.

**What I am NOT changing**
- `mirror_guides()` — including its `canonical_slug`, which feeds alias
  redirect stubs. Routing and published URLs stay as they are.
- `contracts/guide.schema.json` — `order` already exists.
- Kind-bucket label vocabulary.
- `site.toml`'s existing `[[groups]]` table or `discover_packs()`.
- The other frontmatter-less guides (confirmed with the user 2026-08-06).
- `the-release-loop.md` and `release-engineering` — the arc cites, never edits.
- Guide group *order* — the initial `[[guide_groups]]` table reproduces today's
  sequence exactly, so this PR ships zero reordering.

**Dependency note:** `tools/build-site.py` imports `yaml`; the test environment
needs PyYAML (already in `tools/requirements.txt`).

## Declined patterns

- **Migrating all frontmatter-less guides first.** Declined: the path-derived
  inventory plus the frozen baseline make it unnecessary, and it would swamp a
  build-system change with a bulk content edit.
- **Adding a `next:` frontmatter field.** Declined: the schema is
  `additionalProperties: false`, and plain markdown links do the job today.
- **Walking the filesystem directly in `astro.config.ts`.** Declined: splits
  sidebar knowledge across two languages and duplicates slug rules
  `build-site.py` already owns.
- **Reusing `site.toml`'s existing `[[groups]]` table for guides.** Declined
  after discovering `discover_packs()` skips `_`-prefixed slugs and warns on
  slugs without a `pack.toml` — it structurally cannot express `_shared` or
  `_reference`. A separate table costs one table and covers the corpus.
- **Inheriting `site.toml`'s six super-groups as guide super-groups.** Declined:
  it yields five-level nesting (Guides → Foundation → pack → kind → page), a
  depth Starlight has never been asked to render here, for no reader benefit.
- **Deriving labels from filenames alone.** Declined: it changes most existing
  labels (count in spec § Layer 2). The frozen baseline preserves them at zero
  migration cost.
- **Putting `title:` frontmatter ahead of the baseline.** Tempting — it reads as
  the "cleaner" precedence and lets pages own their labels. Declined: 13 pages
  already carry a `title:` differing from their nav label, so frontmatter-first
  silently rewrites 13 reader-facing labels and puts AC5 in direct conflict with
  AC9. Baseline-first keeps the registry transitional while making its shrinkage
  a deliberate act rather than a side effect.
- **Asserting no-regression via slug subset or entry count.** Declined: a subset
  check passes while dropping pages, and neither sees a label change. Set
  equality on slugs plus pair equality on labels are the real guards.
- **Writing the IaC arc as a self-contained process narrative.** Tempting, and
  the first draft did exactly this. Declined: it would restate doctrine
  `the-release-loop` already owns. The arc cites upward — three pages, not six.

## Tasks

### T1: Freeze the pre-change navigation baseline

Mode: goal-based check
Tests: no stub; this task *produces* the fixture T6 and T7 consume.
Approach: extract every `(slug, label)` pair from the current
`docs-site/astro.config.ts` guides block into `guide-nav-baseline.toml`.
Use the `slug: '(guides(/…)?)'` pattern — a `guides/`-prefixed match drops the
root entry. **Must precede T8**, which deletes the only source.
Done when: the file exists, its pair count equals the count in spec § Layer 1,
and it is committed.
Depends on: none

### T2: Inventory derivation

Mode: TDD
Tests: `test_record_has_all_layer1_keys` (assert key presence, not truthiness —
`order` and `kind` are legitimately absent); `test_no_frontmatter_still_yields_record`;
`test_title_override`; `test_shared_and_reference_packs`; `test_non_md_excluded`;
`test_agents_md_not_nav_eligible`; `test_is_index_for_readme_at_any_depth`;
`test_malformed_frontmatter_falls_back`; `test_non_integer_order_coerced_to_absent`;
`test_tutorials_dir_normalizes_to_kind_tutorial` (AC7's second half);
`test_frontmatter_kind_wins_over_directory` (the mixed `tutorial`/`tutorials/` case);
`test_section_index_is_not_nav_eligible`; `test_non_string_slug_falls_back_to_derived`;
`test_non_string_title_coerced_to_absent`. Full set: `tools/test_build_site_inventory.py`.
Approach: one pass over `guides/**/*.md`, reusing `_parse_frontmatter()`. Pure
derivation, no projection concerns. Accept an **injectable path enumerator** so
T7's determinism test has a seam. Never raise on bad input.
Done when: tests pass; over the real tree `len(records) == len(list(guides.rglob("*.md")))`
and `nav_eligible` equals total minus `AGENTS.md` minus every README more than
one directory below the guides root — relational, not hard-coded, since T5 adds
files.
Depends on: none

### T3: Slug parity with what `mirror_guides()` writes

Mode: TDD
Tests: `test_slug_matches_what_mirror_guides_actually_writes` — for every file
under `guides/`, the inventory slug equals the Starlight slug of the file
`mirror_guides()` writes (written path, trailing `/index` stripped);
`test_readme_resolves_to_parent` (`guides/core/README.md` → literal `guides/core`);
`test_slug_frontmatter_override` (the `atlassian` pages).
Approach: read `mirror_guides()`'s output path; do **not** modify its
`canonical_slug` variable — that feeds alias redirect stubs and changing it is a
routing change the spec forbids.
Done when: parity holds for every file; `mirror_guides()` is byte-unchanged.
Depends on: T2

### T4: Declare `[[guide_groups]]` in `site.toml`

Mode: goal-based check
Tests: no stub (goal-based).
Approach: `dir` + `label` entries in a table separate from `[[groups]]`, not
routed through `discover_packs()`. Carry the curated labels no path can derive
(`'The Build Loop (core)'`, `'Product Discovery'`, `'Cross-cutting'` for
`_shared`) and reproduce today's pack-group sequence exactly.
Done when: an entry exists for **every** directory under `guides/` — not merely
those in the hand tree, which omits `_reference`, `catalogue-curation`,
`github`, `linear`, and `iac-terraform` (the pack carrying this spec's live
test); `site.toml` parses; `discover_packs()` emits no new warnings. The
undeclared-directory fallback is projection behaviour and is verified in T6.
Depends on: none

### T5: Write the infrastructure arc — the live test

Mode: goal-based check
Tests: no stub; the arc is T6/T7's test input.
Approach: `author-product-docs` in create mode. Read canonical sources before
any product claim — `generate-iac/SKILL.md`, `reconcile-iac/SKILL.md`,
`pack.toml`, `JOURNEY.md`. Anchor each page in the release loop and cite upward;
do not restate inherited doctrine.
Done when: three pages exist with `order` 1–3; each contains a relative link
matching `release-engineering/explanation/the-release-loop` in its opening
section (greppable — the tree uses relative links, so an absolute
`guides/…` form would rewrite to a dead GitHub URL); `python3
tools/validate_guides.py` passes.
Depends on: none

### T6: Projection — grouping, label precedence, cross-kind ordering

Mode: TDD
Tests: `test_order_sorts_across_kinds` (the `atlassian` 1–4 run spanning four
kinds); `test_index_records_are_direct_group_items`;
`test_root_readme_is_direct_item_of_guides_group`;
`test_kind_buckets_use_canonical_sequence`;
`test_kindless_non_index_record_precedes_kind_buckets` (naming
`_reference/catalogue-format.md` — no frontmatter, not a README, no kind
directory, so it falls through every other ordering rule; asserts position, not
merely presence);
`test_label_precedence_baseline_then_title_then_derived` (AC5 — assert the 13
`title:`-bearing pages keep their baseline label);
`test_no_frontmatter_page_is_projected` (AC4);
`test_guide_groups_labels_and_order_applied`;
`test_undeclared_dir_gets_titlecased_group_appended_last`;
`test_iac_arc_orders_1_2_3`.
Approach: emit in the four-step order stated in [`spec.md` § Layer
2](spec.md#layer-2--projection) — it is the sole statement, deliberately not
restated here. Resolve labels via the same section's precedence chain.
Done when: tests pass, including both real ordered sequences.
Depends on: T1, T3, T4, T5

### T7: Wire into `generate_sidebar_config()`

Mode: TDD
Tests: `test_sidebar_includes_pack_catalogue_and_guides`;
`test_guides_group_slugs_equal_eligible_slugs` (AC2 — set equality over the
Guides groups only, not the whole sidebar, and not a subset check);
`test_no_baseline_pair_regressed` (AC9 — `(slug, label)` pairs, so a label
change fails); `test_guides_nesting_is_one_group_level` (AC8 — no `[[groups]]`
super-group label appears under "Guides");
`test_shuffled_enumerator_is_byte_identical` (AC10 — shuffle the *injected*
enumerator from T2, so the test cannot pass by re-globbing). Plus the real-tree
invariants added at REVIEW — `test_nav_ineligible_set_is_exactly_the_declared_exceptions`,
`test_no_sibling_label_collision_anywhere_in_the_real_tree`,
`test_every_guides_directory_is_declared_in_site_toml`,
`test_atlassian_cross_kind_run_survives`,
`test_duplicate_slug_resolves_deterministically`, plus
`test_malformed_baseline_entry_is_skipped_not_raised` (a degradation case, not
a real-tree invariant). The sibling `[[guide_groups]]` degradation case lives
with T6 in `tools/test_build_site_projection.py`. Full set:
`tools/test_build_site_sidebar.py`.
Approach: append guides groups after the pack-catalogue groups; leave the JSON
serialization path unchanged.
Done when: tests pass; `python3 tools/build-site.py --dry-run` reports the
generated group count (the count prints only under `--dry-run`).
Depends on: T1, T6

### T8: Remove the hand-maintained block

Mode: goal-based check
Tests: no stub (goal-based).
Done when: the `{ label: 'Guides', items: [...] }` entry identified in AC11 is
gone; `! grep -qE "slug: 'guides('|/)" docs-site/astro.config.ts` succeeds —
**pre-verify this pattern exits 1 against the pre-change file**, since under
`-E` a backslash-escaped pipe is a literal and silently matches nothing, making
the negation vacuously true; the surviving top-level sidebar entries are exactly
Home, Get Started, the spread, Changelog, and Contributing — asserted, not
eyeballed; `python3 tools/build-site.py` (no `--dry-run`, so
`sidebar-config.json` is actually written) then `npm run build --prefix
docs-site` completes with the guides groups present in the built output.
Depends on: T7

### T9: Rendered verification

Mode: visual / manual QA
Tests: no stub (manual QA).
Approach: run the load-bearing sequence from `docs-site/AGENTS.md` —
`build-site.py`, then the `web` build, then the `docs-site` build.
**Scope — inspected:** guide group presence and order, the IaC arc rendering
1–3, the `atlassian` flat ordered run ahead of its kind buckets, one
previously-absent page, and one `_shared` page. **Not inspected:** styling,
contrast, mobile viewport, search — unchanged by this spec.
Done when: the above are confirmed and written to
`docs/specs/guides-sidebar-generation/notes/rendered-check.md` (AC14).
Depends on: T8

### T10: Update `guides/AGENTS.md` and record the deferral

Mode: goal-based check
Tests: no stub (goal-based).
Done when: § Traps states the generated contract, `order` semantics, the
`[[guide_groups]]` declaration, and the transitional label baseline (AC15);
`workspace.toml [backlog].open` carries `iac-guides-readme-stage-drift` with a
cold-start-sufficient comment (AC16); `python3 tools/lint-agents-md.py` passes.
Depends on: T9

## Risks

- **The no-regression baseline is only extractable before T8.** T1 exists to
  remove that hazard, and T7 declares the edge so the scheduler cannot reorder
  them.
- **Starlight may reject a nesting depth the pack-catalogue path never
  exercises.** Mitigated by declining super-group inheritance (flat pack groups,
  same depth as today) and by T9 being a real build.
- **`sidebar-config.json` is gitignored**, so a generator regression is invisible
  in review. Set-equality, pair-equality, and determinism tests are the
  compensating control.
- **`tools/validate_guides.py` is not run over `guides/` in CI**, so the schema's
  integer `order` is not an enforced boundary. T2's coercion test compensates.
- **The label baseline can rot** if a page is renamed without updating it. It is
  a fixture consumed by an assertion, so a stale entry fails T7 loudly rather
  than degrading silently.

## Changelog

- 2026-08-06 — initial draft.
- 2026-08-06 — design corrected at PLAN: most guides carry no frontmatter, so
  path structure is the source and frontmatter the refinement.
- 2026-08-06 — user direction: ship the IaC arc as the live integration test.
- 2026-08-06 — restructured intent-first with an explicit inventory layer after
  round-1 adversarial review (six blockers).
- 2026-08-06 — round-3 review folded in. Measurements re-verified independently
  and all held. Inverted label precedence to baseline-first after finding 13
  pages whose `title:` differs from their nav label, which made AC5 and AC9
  mutually unsatisfiable. Pinned the `[[guide_groups]]` entry schema and
  required an entry for every directory — the hand tree has no group for five
  packs, including `iac-terraform`, where the live test lands. Pinned kind
  normalization (`tutorials/` → `tutorial`), `is_index` placement, and canonical
  kind-bucket order, and corrected the assumption that claimed zero reordering.
  Fixed a vacuous `grep -E` pattern whose escaped pipe matched nothing, making
  the removal check always pass.
- 2026-08-06 — round-2 review folded in. Corrected the nav count (the extraction
  pattern dropped the root entry) and the absent count. Added the frozen
  `(slug, label)` baseline after finding filename derivation regresses 90 of 119
  labels. Moved guide groups to a separate `[[guide_groups]]` table after
  finding `discover_packs()` cannot express `_shared`. Restated slug parity
  against what `mirror_guides()` writes rather than its `canonical_slug`. Named
  the `kind` directory fallback as a scoped relaxation of `guide-source-model`
  AC3 and cited the governing ADRs. Dropped the stale `docsUrl` item — already
  correct, with two register entries already covering it.
