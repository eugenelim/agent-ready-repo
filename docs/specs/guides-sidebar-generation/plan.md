# Plan: guides-sidebar-generation

- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I will touch**
- `tools/build-site.py` — inventory pass, projection, extended
  `generate_sidebar_config()`.
- `tools/test_build_site_routing.py` (or a sibling test module) — tests for both
  layers.
- `site.toml` — declare guide group labels (spec Layer 2).
- `docs-site/astro.config.ts` — delete the hand-maintained guides block.
- `guides/iac-terraform/explanation/*.md` — three new pages, the live test.
- `guides/AGENTS.md` — replace the hand-maintained-sidebar trap.
- `workspace.toml` — `[backlog].open` entries for the two out-of-scope findings.

**Tests that demonstrate done**
- Inventory unit tests over fixture trees.
- Slug parity against `mirror_guides()` for every real file.
- Projection tests for cross-kind `order` and `site.toml` labels.
- No-regression against the frozen pre-change slug baseline.
- Determinism under shuffled enumeration order.
- The IaC arc and the existing `atlassian` sequence rendering in order.

**What I am NOT changing**
- `mirror_guides()` — routing and published URLs stay as they are.
- `contracts/guide.schema.json` — `order` already exists.
- Kind-bucket label vocabulary.
- `.github/workflows/pages.yml` — the generator already runs there.
- The 161 other frontmatter-less guides (confirmed with the user 2026-08-06).
- `the-release-loop.md` and `release-engineering` — the arc cites, never edits.

**Dependency note:** `tools/build-site.py` imports `yaml`, so the test
environment needs PyYAML (already in `tools/requirements.txt`).

## Declined patterns

- **Migrating all 161 frontmatter-less guides first.** Declined: the
  path-derived inventory makes it unnecessary, and it would swamp a
  build-system change with a bulk content edit.
- **Adding a `next:` frontmatter field.** Declined: the schema is
  `additionalProperties: false`, so it needs a schema change, and plain markdown
  links do the job today.
- **Walking the filesystem directly in `astro.config.ts`.** Declined: it splits
  sidebar knowledge across two languages and duplicates the slug rules
  `build-site.py` already owns.
- **A new config file for group labels.** Declined after discovering `site.toml`
  already exists and is titled "Site recipe — controls docs-site sidebar
  grouping and pack ordering." Extending it beats inventing a sibling.
- **Writing the IaC arc as a self-contained process narrative.** Tempting, and
  the drafted version did exactly this. Declined: it would restate the two-loop
  split, reversibility, and rehearse-then-release that `the-release-loop`
  already owns. The arc cites upward — which is why it is three pages, not six.
- **Asserting no-regression via entry-count parity.** Declined: a page can
  satisfy a count while sitting in the wrong group or pointing at a dead slug.
  The frozen slug baseline (T1) is the real guard.

## Tasks

### T1: Freeze the pre-change navigation baseline

Mode: goal-based check
Tests: no stub (goal-based); this task *produces* the fixture the later
no-regression test consumes.
Approach: extract the 118 `slug:` values from the current
`docs-site/astro.config.ts` guides block into a committed fixture file. **This
must happen before T8 deletes the block** — the baseline's only source is the
tree we are removing.
Done when: the fixture exists, contains 118 slugs, and is committed.
Depends on: none

### T2: Inventory derivation

Mode: TDD
Tests: `test_inventory_record_fields` (all Layer 1 fields populated);
`test_no_frontmatter_still_yields_record`; `test_title_override`;
`test_shared_and_reference_packs`; `test_non_md_excluded`;
`test_agents_md_not_nav_eligible`; `test_malformed_frontmatter_falls_back`;
`test_non_integer_order_coerced_to_absent` (AC7).
Approach: one pass over `guides/`, reusing the existing `_parse_frontmatter()`.
Pure derivation, no projection concerns. Return records; never raise on bad
input.
Done when: tests pass; inventory over the real tree yields 182 records, 181
`nav_eligible`.
Depends on: none

### T3: Slug parity with `mirror_guides()`

Mode: TDD
Tests: `test_slug_matches_mirror_for_every_real_file` — iterate every file under
`guides/`, assert inventory slug equals the slug `mirror_guides()` derives;
`test_readme_normalizes_to_parent` (`guides/core/README.md` → literal
`guides/core`, not `guides/core/index`); `test_slug_frontmatter_override`
(the four `atlassian` pages).
Approach: factor the slug rule into one function both call, so parity is
structural rather than two implementations kept in sync by hand.
Done when: parity holds for all 182 files (AC3).
Depends on: T2

### T4: Declare guide group labels in `site.toml`

Mode: goal-based check
Tests: no stub (goal-based).
Approach: add the curated guide group labels that no path or `pack.toml` field
can derive — `'The Build Loop (core)'` for `core`, `'Product Discovery'` for
`product-engineering`, and the rest read off the current hand tree. Reuse the
existing `[[groups]]` ordering.
Done when: every pack appearing in the current hand tree has a declared label;
`site.toml` parses; a pack absent from it still resolves to a fallback.
Depends on: none

### T5: Write the infrastructure arc — the live test

Mode: goal-based check
Tests: no stub; the arc is T6/T7's test input.
Approach: use `author-product-docs` in create mode. Read canonical sources
before any product claim — `generate-iac/SKILL.md`, `reconcile-iac/SKILL.md`,
`pack.toml`, `JOURNEY.md`. Anchor each page in the release loop and cite upward;
do not restate inherited doctrine.
Done when: three pages exist with `order` 1–3, each containing a link to
`guides/release-engineering/explanation/the-release-loop` in its opening section
(AC12, greppable); `python3 tools/validate_guides.py` passes.
Depends on: none

### T6: Projection — grouping, labels, cross-kind ordering

Mode: TDD
Tests: `test_order_sorts_across_kinds` (the `atlassian` 1–4 sequence spanning
four kinds stays 1–4); `test_unordered_fall_into_kind_buckets`;
`test_site_toml_labels_applied`; `test_pack_absent_from_site_toml_gets_group`;
`test_iac_arc_orders_1_2_3`.
Approach: sort within a pack group by `(order is None, order, label)` so
declared order wins across kinds and undeclared siblings stay alphabetical
inside their kind buckets.
Done when: tests pass, including both real ordered sequences.
Depends on: T3, T4, T5

### T7: Wire into `generate_sidebar_config()`

Mode: TDD
Tests: `test_sidebar_includes_pack_catalogue_and_guides`;
`test_no_baseline_slug_regressed` (every slug in T1's fixture appears — AC9);
`test_shuffled_enumeration_is_byte_identical` (AC10 — shuffle the discovered
list before the second run, so stable `sorted()` cannot make this pass on its
own).
Approach: append guides groups after the existing pack-catalogue groups; leave
the JSON serialization path unchanged.
Done when: tests pass; `python3 tools/build-site.py --dry-run` reports the
generated group count (the count prints only under `--dry-run`).
Depends on: T6

### T8: Remove the hand-maintained block

Mode: goal-based check
Tests: no stub (goal-based).
Done when: lines 86–544 of `docs-site/astro.config.ts` are gone; the surviving
sidebar is Home, Get Started, the `sidebar-config.json` spread, Changelog, and
Contributing (AC11); `! grep -q "slug: 'guides/" docs-site/astro.config.ts`
succeeds; `npm run build --prefix docs-site` completes.
Depends on: T7

### T9: Rendered verification

Mode: visual / manual QA
Tests: no stub (manual QA).
Approach: run the load-bearing sequence from `docs-site/AGENTS.md` —
`build-site.py`, then the `web` build, then the `docs-site` build. Inspect the
rendered sidebar.
Done when: the IaC arc renders 1–3; the `atlassian` sequence still renders 1–4
across four kinds (AC13); a page absent from the old tree now appears; observed
state recorded (AC14). Also check whether `docsUrl` resolves and record a
backlog entry if it does not.
Depends on: T8

### T10: Update `guides/AGENTS.md` and record deferrals

Mode: goal-based check
Tests: no stub (goal-based).
Done when: § Traps states the generated contract, `order` semantics, and the
`site.toml` declaration (AC15); `workspace.toml [backlog].open` carries entries
for the README stage drift and (if confirmed) the `docsUrl` routing gap;
`python3 tools/lint-agents-md.py` passes with the file under 150 lines.
Depends on: T9

## Risks

- **Reusing `site.toml`'s group order visibly reorders guide groups** relative
  to today's hand tree. Called out as an assumption in the spec; if the human
  rejects it at the gate, T4 declares a guides-specific order instead.
- **Starlight may reject a nesting depth the pack-catalogue path never
  exercises.** T9 is a real build, so a shape failure surfaces there; mitigation
  is flattening one level.
- **The no-regression baseline is only extractable before T8.** T1 exists solely
  to remove that ordering hazard.
- **`sidebar-config.json` is gitignored**, so a generator regression is invisible
  in review. The no-regression and determinism tests are the compensating
  control.
- **`tools/validate_guides.py` is not run over `guides/` in CI**, so the schema's
  integer-typed `order` is not an enforced boundary. T2's coercion test is the
  compensating control.

## Changelog

- 2026-08-06 — initial draft.
- 2026-08-06 — design corrected at PLAN after measuring frontmatter coverage:
  20 of 182 files carry frontmatter, so path structure is the source and
  frontmatter the refinement.
- 2026-08-06 — user direction: ship the IaC arc as the live integration test.
- 2026-08-06 — restructured intent-first with an explicit inventory layer after
  adversarial review returned six blockers. Corrected: `order` is already in use
  (four `atlassian` pages, cross-kind, pack-level); the config block is lines
  86–544 not 87–547; group labels are curated and underivable; README slugs
  normalize to the parent directory; `guides/AGENTS.md` must not reach readers;
  the absent-page count is 67. Group labels resolved to `site.toml`, which
  already owns sidebar grouping. Dropped the README stage-drift fix as failing
  the bundled-fixes carve-out.
