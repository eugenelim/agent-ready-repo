---
title: Guide Source Model — Phase 2A
status: Shipped
created: 2026-07-28
---

**Status:** Shipped

## Objective

Make `guides/` the explicit canonical source for catalogue-facing product documentation while keeping `docs/guides/` as internal maintainer material. Introduce a minimal guide metadata contract enforced by a deterministic validator, add frontmatter-aware routing to the site build pipeline, and prove the model with one representative flat guide from the Product Documentation pack.

## Acceptance Criteria

- [x] AC1 — `guides/` is the canonical external guide source; `build-site.py` mirrors it (documented and tested, not just assumed).
- [x] AC2 — Flat paths `guides/<pack>/<slug>.md` are supported alongside existing `guides/<pack>/<diataxis-folder>/<slug>.md` paths; `build-site.py` handles both.
- [x] AC3 — Guide `kind` is declared in frontmatter (`tutorial | how-to | reference | explanation`); the physical directory does not determine kind.
- [x] AC4 — Required frontmatter fields (`title`, `summary`, `pack`, `kind`) are validated by `tools/validate_guides.py`; each missing field is named in the error.
- [x] AC5 — Optional fields (`slug`, `journey`, `order`, `aliases`, `status`) are validated when present; unknown fields fail validation.
- [x] AC6 — `slug:` frontmatter overrides the output file path in `build-site.py`, enabling a flat source to map to an existing stable public URL.
- [x] AC7 — `aliases:` frontmatter generates meta-refresh redirect stubs at alias paths; one canonical mechanism, no second redirect system.
- [x] AC8 — Duplicate canonical slugs, duplicate aliases, conflicting canonical sources, and redirect loops fail validation. Aliases pointing to no canonical route produce a warning (not a failure) to allow migration staging.
- [x] AC9 — `pack` values that are not a directory in `packs/` (checked via `packs/*/pack.toml` glob) and not `_shared` fail validation. `_reference` produces a warning (pending future designation). Invalid `kind` values fail validation.
- [x] AC10 — `docs/guides/` is excluded from the external corpus; the validator does not scan it; `build-site.py` does not mirror it. Both are tested.
- [x] AC11 — One representative flat guide (`guides/product-documentation/getting-started.md`) renders through the complete pipeline: validate → `python tools/build-site.py` → `npm run build --prefix docs-site`.
- [x] AC12 — Existing legacy guide sources without frontmatter continue to work; the validator warns but does not fail.
- [x] AC13 — Frontmatter added to at least 3 existing `guides/product-documentation/` files as migration examples.
- [x] AC14 — Internal migration guidance exists in `docs/guides/guide-source-model.md` covering the 9 required topics.
- [x] AC15 — `python tools/validate_guides.py guides/product-documentation/`, `python -m pytest tools/test_validate_guides.py tools/test_build_site_routing.py -q`, `make build-check`, `python tools/lint-agent-artifacts.py`, `FORCE=1 make build-self` all pass.
- [x] AC16 — No bulk content migration was pulled into this phase.

## Boundaries

**In scope:**
- `contracts/guide.schema.json` — new guide frontmatter JSON Schema (documentation + `jsonschema` runtime enforcement)
- `tools/validate_guides.py` — new validator tool; exit 0 = pass, exit 1 = errors
- `tools/test_validate_guides.py` — validator tests (TDD)
- `tools/build-site.py` — update: frontmatter-aware `slug:` routing, meta-refresh redirect stubs for `aliases:`, metadata strip before writing to docs-site
- `tools/test_build_site_routing.py` — new routing-focused tests for build-site.py additions
- `guides/product-documentation/getting-started.md` — new pilot flat guide with valid frontmatter
- Frontmatter added to 3 existing `guides/product-documentation/` files
- `docs-site/astro.config.ts` — add pilot guide to sidebar
- `docs/guides/guide-source-model.md` — new internal maintainer guide
- `Makefile` — add new test files to `test:` target; add `jsonschema` note to dev dependencies
- `tools/requirements.txt` — add `jsonschema>=4.0` (new dev-time dependency; recorded here per AGENTS.md)

**Out of scope:**
- Bulk-flattening or bulk-migrating the guide corpus
- Auto-generating the sidebar from frontmatter (requires RFC)
- Redesigning docs-site navigation or UI
- `docs/guides/` deletion or content changes beyond the new maintainer guide
- Retrofitting other pack guides with frontmatter
- Removing legacy route support
- Separate route manifest file (frontmatter `slug:` is sufficient)
- Making validation fail-fast in `build-site.py` (migration-safe requires warn-only during transition)

## Testing Strategy

**TDD — `tools/test_validate_guides.py`:**
1. `valid_required_fields` → passes
2. `missing_title` → fails with "title" in error
3. `missing_summary` → fails with "summary" in error
4. `missing_pack` → fails with "pack" in error
5. `missing_kind` → fails with "kind" in error
6. `invalid_kind_value` → fails
7. `unknown_pack_id` → fails
8. `shared_pack_id` → passes (`_shared` is approved)
9. `duplicate_slug_within_pack` → fails with "duplicate"
10. `aliases_collision_with_canonical` → fails
11. `duplicate_alias` → fails
12. `no_frontmatter` → warn only (not failure)
13. `docs_guides_not_scanned` → `docs/guides/` not included even if passed implicitly
14. `unknown_field` → fails (strict schema)
15. `valid_optional_fields` → passes
16. `dangling_alias` → warns (not fails) — migration staging allowed
17. `redirect_loop` → fails (slug equals one of its own aliases)

**TDD — `tools/test_build_site_routing.py`:**
1. `slug_override_changes_output_path` — guide with `slug: guides/core/alt-slug` is written to that path, not default
2. `alias_generates_redirect_stub` — guide with `aliases: [guides/core/old-slug]` generates a meta-refresh file at that path
3. `guide_metadata_stripped_from_output` — `pack:`, `kind:`, `summary:`, `slug:`, `aliases:`, `status:` absent from written file
4. `no_frontmatter_passthrough_unchanged` — file without frontmatter is injected with title only (existing behavior preserved)
5. `docs_guides_excluded` — `docs/guides/` is not mirrored

**Goal-based checks:**
- `contracts/guide.schema.json` exists; `python -c "import json; json.load(open('contracts/guide.schema.json'))"` exits 0
- `python tools/validate_guides.py --help` exits 0
- `python tools/validate_guides.py guides/product-documentation/` exits 0 on 4 valid guides (pilot + 3 existing)
- `python tools/build-site.py --dry-run` shows pilot guide at correct path; `docs/guides/` absent from output
- `grep -q "getting-started" docs-site/astro.config.ts` passes

**Manual QA:**
- `npm ci --prefix docs-site && npm run build --prefix docs-site` → build succeeds
- Pilot guide slug `guides/product-documentation/getting-started` appears in Starlight output (`build/docs/guides/product-documentation/getting-started/index.html`)
- `docs/guides/` content absent from `build/docs/`

## Assumptions

1. `jsonschema` 4.x is available in the tools environment (confirmed: v4.25.1 installed); it is added to `tools/requirements.txt` as a new dev-time dependency.
2. PyYAML is available for frontmatter parsing (already in `tools/requirements.txt`).
3. `packs/*/pack.toml` glob provides the authoritative set of valid pack IDs (21 packs as of 2026-07-28).
4. `_shared` is the only currently approved shared-doc identifier. `_reference` is undesignated; validator warns on `pack: _reference`.
5. Starlight 0.41.4 does not have a `redirect:` frontmatter key that this project relies on; meta-refresh HTML stubs are used for alias redirect stubs instead (conservative, verified to work with raw HTML in Markdown under Astro).
6. `npm ci --prefix docs-site` is available locally for the Starlight build verification step (npm 11.17.0 confirmed).
7. The existing Starlight sidebar slug convention (`guides/<pack>/<folder>/<slug>`) remains unchanged; auto-generating the sidebar is deferred.

## Resolve-vs-Surface Disposition Record

| Item | Disposition | Rationale |
|------|------------|-----------|
| Starlight `redirect:` frontmatter | Resolved — use meta-refresh HTML stubs | Conservative; avoids unverified schema assumption |
| Auto-sidebar generation | Deferred | RFC required; not Phase 2A scope |
| `_reference/` pack identifier | Resolved — warn-only | No content with frontmatter in guides/_reference/ yet |
| jsonschema dependency | Resolved — add to requirements.txt | Available v4.25.1; add as dev-time dep per AGENTS.md |
| Build-site.py routing tests | Resolved — add test_build_site_routing.py | Structural change to public-URL generation warrants tests |
| Dangling alias behavior | Resolved — warn not fail | Migration staging: alias declared before canonical exists |
