# Plan: The catalogue specification on the docs site, at draft/

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `tools/build-site.py` (generation pass order, `--clean`, `--dry-run`, sibling loading at ~1413); `tools/schema_field_reference.py` (`render_page`, `field_rows`, the Wave 6 generator to reuse) and `tools/test_schema_field_reference.py`; `tools/catalogue/check_contract_parity.py:25-41` (path-loading the manifest loader); `docs-site/src/build-a-catalogue-nav.json` and `tools/test_build_a_catalogue_nav.py`; `.github/workflows/pages.yml` and `tools/test-pages-workflow.py`; `web/src/test/rendered-output.test.ts`

## Approach

One new stdlib module, `tools/catalogue_spec_site.py`, reads the manifest's
member rows and writes three things: page sources under the docs content
tree, raw files under `docs-site/public/`, and the version index. It reuses
Wave 6's `render_page` for JSON members and renders TOML members as a code
block. `build-site.py` calls it after the field references. The navigation
entry, workflow triggers and rendered-output check follow. The riskiest part is
the first real Astro build: slugs, the page budget and table wrapping are only
proven there.

## Constraints

- RFC-0109 D2: generated and gitignored, written by `build-site.py`; raw files under `public/` so Astro copies them under the docs base path.
- RFC-0109 D3: `draft/` `$id`s are rewritten so draft bytes never claim a release identity.
- RFC-0109 D6: generated field tables plus short narrative that never defines a field.
- `tools/AGENTS.md`: pure stdlib.
- `docs-site/AGENTS.md`: never edit generated content; edit sources.
- `tools/test_build_a_catalogue_nav.py`: the top-level D9 tree, the tab set and the two-`link` count stay fixed; the new entry is a `slug`.
- `web/src/test/rendered-output.test.ts`: `DOCS_PAGE_BUDGET = 330`; tables must sit in a focusable `.table-scroll` region.

## Construction tests

The rendered-output check (T4) spans T1–T3, since it reads the real build.

## Durable-output map

| Spec durable output | Task |
| --- | --- |
| generated section and `docs-site/spec-src/catalogue/` | T1, T2 |
| `docs-site/AGENTS.md` | T2 |
| RFC-0109 errata | T5 |

## Design (LLD)

### Component / module decomposition

`tools/catalogue_spec_site.py`:

- `DRAFT_BASE_URL = "https://eugenelim.github.io/agent-ready-repo/docs/spec/catalogue/draft/"`.
- `members(contracts_dir) -> list[ContractRow]`: path-loads `tools/catalogue/sync_contract_inventory.py` as `check_contract_parity.py` does, and returns the `member` rows in manifest order.
- `page_name(file_name) -> str`: `file_name.replace(".", "-")`, for example `pack-schema-json`.
- `draft_bytes(path) -> bytes`: works on bytes, never re-serializes. For `.json`, find the first line matching `^  "\$id": "[^"]*",?$` (the top-level member at two-space indent, as every member writes it). Replace only the quoted value with the draft URL. If no such line exists (`adapter.schema.json`), insert `  "$id": "<url>",\n` after the first line. Then assert that the result parses and its top-level `$id` equals the URL. For `.toml`, return the source bytes.
- `generate(content_dir: Path, public_dir: Path, *, contracts_dir: Path = REPO_ROOT / "contracts", spec_src: Path = REPO_ROOT / "docs-site" / "spec-src" / "catalogue", dry_run: bool = False) -> list[Path]`: writes
  - `content_dir/spec/catalogue/index.md` (slug `spec/catalogue`),
  - `content_dir/spec/catalogue/draft/index.md` (slug `spec/catalogue/draft`, from `docs-site/spec-src/catalogue/overview.md` plus a generated member table),
  - one `content_dir/spec/catalogue/draft/<page name>.md` per member,
  - `public_dir/spec/catalogue/draft/<file name>` per member,
  - `public_dir/spec/catalogue/index.json` as `{"releases": []}`.

`schema_field_reference.render_page` gains an optional `slug: str | None = None`,
emitted in frontmatter when given. Wave 6's two pages pass none, so their bytes
are unchanged.

Member pages: the JSON page is `render_page(schema, title=<file name>, source="contracts/<path>", narrative_href=<raw file URL>, narrative_label="the raw schema, which states every rule", slug=...)`. `contracts/` is normative (RFC-0076 D1), so the table's conditional-rules marker points at the schema itself. The page then adds a line linking the overview's member section. The `pack` and `skill` pages also link Wave 6's pages. The TOML page has a frontmatter title, one sentence, a fenced `toml` block of the file, and the raw-file link. `adapter.toml` also links `adapter-schema-json`.

Narrative: `docs-site/spec-src/catalogue/overview.md` holds the overview prose the spec AC lists, with one `##` section per member page name, which holds the purpose block. Links use site routes, so `check-rendered-site-links.py` resolves them.

### Interfaces & contracts

`build-site.py` gains `SITE_PUBLIC = REPO / "docs-site" / "public"` beside `SITE_PUBLIC_GUIDES`. Its main pass, after `_field_reference.generate(reference_out)`, calls
`_spec_site.generate(SITE_DOCS, SITE_PUBLIC, dry_run=...)`. A full pass writes many `REPO_ROOT` paths, so tests of it run `build-site.py` as a subprocess in the temp tree that `tools/test_build_site_routing.py::_generator_fixture` builds. `--clean` removes
`SITE_DOCS/"spec"` and `SITE_PUBLIC/"spec"`. `.gitignore` gains
`docs-site/src/content/docs/spec/` and `docs-site/public/spec/`.

## Tasks

### T1: Generator module and render_page slug

**Depends on:** none

**Tests:** `tools/test_catalogue_spec_site.py` (new):
- With a fixture manifest of 2 members, 1 bundled and 1 vendored row, `generate` writes exactly the member pages and raw files (AC 1).
- Every page has `slug: spec/catalogue/draft/<page name>`, and no page name equals a raw file name (AC 2).
- For each JSON member, the raw bytes equal the source bytes outside the `$id` value span (or outside the one inserted line, for `adapter.schema.json`). A schema without `$id` gains exactly that line. TOML raw is byte-identical (AC 3). Fixtures cover both cases at byte level.
- A JSON page contains the `field_rows` table, and its narrative link targets the raw file URL. A TOML page contains the file in a `toml` block and the raw link, and `adapter.toml` links `adapter-schema-json` (AC 4).
- The `pack` and `skill` pages link `reference/pack-toml` and `reference/skill-frontmatter` (AC 5).
- `index.json` is `{"releases": []}`, and the index page links `draft/` (AC 7).
- `dry_run=True` writes nothing (AC 11, generator half).
- On the real manifest, the page count equals the member count (10).
- `tools/test_schema_field_reference.py`: Wave 6 page bytes are unchanged with no slug.

**Done when:** `python -m pytest tools/test_catalogue_spec_site.py tools/test_schema_field_reference.py -q` passes.

### T2: Narrative sources, build-site wiring and maintainer note

**Depends on:** T1

**Tests:**
- In `tools/test_catalogue_spec_site.py`, the generated overview contains each AC 6 element as a key phrase: the three commands, `CAT-V-ARC`, `JOURNEY.md`, the init link, and the `draft/` statement.
- It also asserts one overview section per member page name.
- `build-site.py --clean` clears stale spec content (AC 11, wiring half). In the `_generator_fixture` temp tree, the test plants a stale file in `docs-site/src/content/docs/spec/` and in `docs-site/public/spec/`. It runs the script as a subprocess with `--clean`, as that file's full-pass tests do, then asserts both planted files are gone and the regenerated section is present. `--clean` keeps its clean-then-rebuild behaviour for every other tree.
- `_generator_fixture` in `tools/test_build_site_routing.py` also copies `tools/catalogue_spec_site.py`, `tools/catalogue/sync_contract_inventory.py`, `contracts/catalogue-spec.toml` with every file its rows name, and `docs-site/spec-src/catalogue/overview.md`, so its existing full-pass tests keep exiting 0.

**Approach:** write `docs-site/spec-src/catalogue/overview.md` in the plain-language style `docs/AGENTS.md` and `docs-site/AGENTS.md` set. Wire `build-site.py` and `.gitignore`. Update the `docs-site/AGENTS.md` generated-content note.

**Done when:** `python -m pytest tools/test_catalogue_spec_site.py tools/test_build_site_routing.py -q` passes, and `python tools/build-site.py` followed by `git status --short docs-site` shows no untracked generated file.

### T3: Navigation entry and workflow triggers

**Depends on:** T1

**Tests:**
- `tools/test_build_a_catalogue_nav.py`: the "Contract and schema reference" group's first item is `{"label": "Catalogue specification (draft)", "slug": "spec/catalogue/draft"}`, and the other three are kept. `_known_routes()` accepts the new slug (AC 8).
- `tools/test-pages-workflow.py`: `REQUIRED_PATHS` gains `contracts/**`, `tools/catalogue_spec_site.py` and `tools/catalogue/sync_contract_inventory.py` (AC 9).

**Approach:** wire `tools/test_catalogue_spec_site.py` into `.github/workflows/build-check.yml` (the guides sidebar generation step) and the `Makefile:677` line of `run-test-suite`. That line change needs three more edits:
- a `SUITE_DISPOSITION` entry in `tools/lint-ci-parity.py`, beside lines 1634–1641;
- the membership row in `tools/test_local_ci_shared_test_deduplication.py` (lines 274–275);
- re-pinned `APPROVED_STANDALONE_PLAN_DIGEST` and `APPROVED_COMPOSED_PLAN_DIGEST` with a dated cause note, as at lines 1045–1057.

**Done when:** `python -m pytest tools/test_build_a_catalogue_nav.py tools/test_local_ci_shared_test_deduplication.py -q`, `python3 tools/test-pages-workflow.py` and `python3 tools/lint-ci-parity.py` pass.

### T4: Rendered-output check and real build

**Depends on:** T2, T3

**Tests:** in `web/src/test/rendered-output.test.ts`, a new case gets the member file names by running `python3 -c` with `tools/catalogue/sync_contract_inventory.py`'s `load_manifest` through `child_process.execFileSync`. That is the canonical loader, so the check needs no TOML dependency and no generator output. The job already sets up Python. For each member, the case asserts that `build/docs/spec/catalogue/draft/<page name>/index.html` and `build/docs/spec/catalogue/draft/<file name>` exist, and that each JSON raw file's `$id` equals its served URL (AC 10). Change `DOCS_PAGE_BUDGET` only if the real build exceeds 330 docs pages. If it does, raise `--max-old-space-size` in `pages.yml`'s `NODE_OPTIONS` in the same edit, as the budget's comment requires.

**Approach:** run the documented local build (`python3 tools/build-site.py`, `npm run build --prefix web`, `npm run build --prefix docs-site`, `python3 tools/check-rendered-site-links.py --build-dir build`, `npm test --prefix web`) and record the outcome in the verification ledger. If Node dependencies cannot be installed locally, the PR's `pages.yml` run is the proof.

**Done when:** a `workflow_dispatch` run of `pages.yml` on this branch (`gh workflow run pages.yml --ref <branch>`) passes its build job. That job includes `check-rendered-site-links.py` and the rendered-output suite, and its deploy is gated to `main`. The run's URL is recorded in the verification ledger. A local build is optional extra evidence.

### T5: RFC errata entry

**Depends on:** none

**Tests:** goal-based.

**Approach:** append an entry under RFC-0109's existing `## Errata`. It records three facts:
- OQ1 is settled by this spec with the default placement.
- The Approver withdrew the S3 validation run on 2026-10-22.
- S1's load-inventory roster test remains the mechanical proof.

It names the passages it supersedes: the Risks mitigation "the validation below" (line 323), § Experiment / validation (lines 340–346), and acceptance item 4 (line 364).

**Done when:** the entry is present, and `python .claude/skills/work-loop/scripts/lint-spec-status.py --root .` is clean.

## Rollout

One PR, stacked on S2, reversible. It changes no package, so it needs no
version bump. Merging deploys the `draft/` section. Nothing versioned is
published.

## Risks

- `pages.yml` does not run on a pull request whose base is not `main`, so the stacked PR relies on a `workflow_dispatch` run.
- Adding 12 pages may push the rendered-output suite's memory or time limits. T4 changes the budget and heap together, and only if the real build needs it.

## Changelog

- 2026-10-22: spec approved by eugenelim
- 2026-10-22: plan approved by eugenelim
