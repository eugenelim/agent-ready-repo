---
title: Guide Source Model — Phase 2A — Plan
status: Done
---

**Status:** Done

## Tasks

### T-01 — Guide metadata schema

**Mode:** Goal-based check  
**Owns:** `contracts/guide.schema.json`, `tools/requirements.txt`  
**Depends on:** none  

**Approach:**
Write a JSON Schema (draft-07) for guide frontmatter. Required: `title`, `summary`, `pack`, `kind`. Optional: `slug`, `journey`, `order`, `aliases`, `status`. `additionalProperties: false` enforces strict schema. Also add `jsonschema>=4.0` to `tools/requirements.txt` (new dev-time dependency, approved in spec Assumptions).

**Done when:** `contracts/guide.schema.json` exists; `python -c "import json; json.load(open('contracts/guide.schema.json'))"` exits 0; `jsonschema>=4.0` appears in `tools/requirements.txt`.

---

### T-02 — Guide validator

**Mode:** TDD  
**Owns:** `tools/validate_guides.py`, `tools/test_validate_guides.py`  
**Depends on:** T-01  

**Tests (stub first, then implementation):**
```python
# tools/test_validate_guides.py — 17 tests
# 1.  valid_required_fields            → passes
# 2.  missing_title                    → fails, "title" in error
# 3.  missing_summary                  → fails, "summary" in error
# 4.  missing_pack                     → fails, "pack" in error
# 5.  missing_kind                     → fails, "kind" in error
# 6.  invalid_kind_value               → fails
# 7.  unknown_pack_id                  → fails
# 8.  shared_pack_id                   → passes (_shared approved)
# 9.  duplicate_slug_within_pack       → fails, "duplicate"
# 10. aliases_collision_with_canonical → fails
# 11. duplicate_alias                  → fails
# 12. no_frontmatter                   → warns, does not fail
# 13. docs_guides_not_scanned          → docs/guides/ not scanned
# 14. unknown_field                    → fails (strict schema)
# 15. valid_optional_fields            → passes
# 16. dangling_alias                   → warns, does not fail
# 17. redirect_loop                    → fails (slug equals own alias)
```

**Approach:**
- Parse YAML frontmatter block (between first `---` pair) from each `.md` file using PyYAML
- Validate required/optional fields with `jsonschema` against `contracts/guide.schema.json`
- Discover valid pack IDs from `packs/*/pack.toml` glob (not a bare listdir)
- Track canonical slugs (derived from `slug:` frontmatter if present, else relative path from guides root) and aliases across all scanned files for duplicate/collision detection
- CLI: `validate_guides.py [paths...] [--guides-root ROOT] [--packs-root ROOT]`; default scan path = `guides/` (top-level); explicitly exclude any path under `docs/guides/`
- Exit codes: 0 = all checked files pass; 1 = any errors; 2 = usage error
- Warnings printed to stderr; errors to stderr; summary to stdout

**Done when:** All 17 tests pass.

---

### T-03 — Update build-site.py for frontmatter-aware routing

**Mode:** TDD (new tests in `tools/test_build_site_routing.py`)  
**Owns:** `tools/build-site.py`, `tools/test_build_site_routing.py`  
**Depends on:** none (runs parallel to T-01/T-02)  

**Tests (5 tests):**
```python
# tools/test_build_site_routing.py
# 1. slug_override_changes_output_path
# 2. alias_generates_redirect_stub
# 3. guide_metadata_stripped_from_output
# 4. no_frontmatter_passthrough_unchanged
# 5. docs_guides_excluded
```

**Approach — new helpers in build-site.py:**
- `_parse_frontmatter(text: str) -> dict` — extract YAML block from `---` delimiters; return `{}` if no frontmatter
- `_strip_guide_metadata(text: str) -> str` — remove guide-specific fields (`pack`, `kind`, `summary`, `slug`, `aliases`, `status`, `journey`, `order`) from frontmatter block before writing to docs-site; keep `title:` and any other Starlight fields
- `_make_redirect_stub(target_url: str, title: str = "Redirecting...") -> str` — generate a Markdown file with a meta-refresh HTML tag pointing to `target_url`

**Approach — update `mirror_dir` call for guides:**
- Parse frontmatter of each source guide file
- If `slug:` present: compute output path as `SITE_DOCS / <slug>.md` (relative to repo docs root) instead of default relative path
- If `aliases:` present: after writing the canonical file, generate redirect stub files at each alias path
- Apply `_strip_guide_metadata` on all guide `.md` files before writing to docs-site
- Preserve existing behavior for files without frontmatter

**Redirect stub format:**
```markdown
---
title: "Redirecting..."
---

<meta http-equiv="refresh" content="0; url=<TARGET_URL>">

This page has moved. [Click here](<TARGET_URL>) if you are not redirected automatically.
```

Where `TARGET_URL = base + "/" + canonical_slug + "/"` using the site base from `astro.config.ts` (hardcode as `/agent-ready-repo/docs` constant in build-site.py since it's already declared there via `GITHUB_BASE`).

**Done when:** All 5 new tests pass; `python tools/build-site.py --dry-run` exits 0.

---

### T-04 — Pilot flat guide

**Mode:** Goal-based check  
**Owns:** `guides/product-documentation/getting-started.md`  
**Depends on:** T-01  

**Approach:** Create a new flat guide at `guides/product-documentation/getting-started.md` with valid frontmatter and useful content (not placeholder). The guide should serve readers who want to understand and use the product documentation authoring workflow.

**Frontmatter:**
```yaml
---
title: "Getting Started with Product Documentation"
summary: "Create, revise, and maintain catalogue-facing guides using the author-product-docs skill."
pack: product-documentation
kind: tutorial
---
```

**Done when:** `python tools/validate_guides.py guides/product-documentation/getting-started.md` exits 0.

---

### T-05 — Add frontmatter to existing product-documentation guides

**Mode:** Goal-based check  
**Owns:** `guides/product-documentation/explanation/the-diataxis-framework.md`, `guides/product-documentation/how-to/author-product-docs.md`, `guides/product-documentation/how-to/write-a-guide.md`  
**Depends on:** T-01  

**Approach:** Prepend valid YAML frontmatter to each file. Each file already has an H1 heading; the `_inject_frontmatter` logic in build-site.py strips the H1 when injecting the `title:`. With explicit frontmatter, H1 is preserved in the body (Starlight renders both — but check the current file structure before prepending).

Files:
- `the-diataxis-framework.md`: `kind: explanation`
- `author-product-docs.md`: `kind: how-to`  
- `write-a-guide.md`: `kind: how-to`

All three: `pack: product-documentation`, `title:` from existing H1, `summary:` from first non-blank line after H1.

**Done when:** `python tools/validate_guides.py guides/product-documentation/` exits 0 on all 4 guides (3 existing + pilot).

---

### T-06 — Update sidebar for pilot guide

**Mode:** Goal-based check  
**Owns:** `docs-site/astro.config.ts`  
**Depends on:** T-04  

**Approach:** Add the pilot guide to the Product Documentation section as the first item, before the Explanation/How-to groups:
```typescript
{ label: 'Getting Started', slug: 'guides/product-documentation/getting-started' },
```

**Done when:** `grep -q "guides/product-documentation/getting-started" docs-site/astro.config.ts` passes.

---

### T-07 — Internal maintainer guide

**Mode:** Goal-based check  
**Owns:** `docs/guides/guide-source-model.md`  
**Depends on:** none  

**Approach:** Write a complete maintainer guide covering all 9 required topics from the spec. Keep it internal and maintainer-oriented; do not duplicate the Product Documentation user guide.

Topics required:
1. The difference between `guides/` and `docs/guides/`
2. The guide metadata contract (required and optional fields, with example)
3. Flat vs topic-first organization; when folders are justified
4. How public routes are preserved (via `slug:` frontmatter)
5. How aliases work (meta-refresh redirect stubs)
6. How to migrate one guide (6-step procedure)
7. How to validate guide ownership
8. How to avoid editing generated output
9. How to run the validator

**Done when:** File exists; all 9 topics covered.

---

### T-08 — Wire new tests into Makefile

**Mode:** Goal-based check  
**Owns:** `Makefile`  
**Depends on:** T-02, T-03  

**Approach:** Add `tools/test_validate_guides.py` and `tools/test_build_site_routing.py` to the `test:` target's explicit pytest invocation.

**Done when:** `grep -q "test_validate_guides" Makefile` passes; `grep -q "test_build_site_routing" Makefile` passes.

---

### T-09 — Gates, build, and verification

**Mode:** Manual QA  
**Owns:** nothing new  
**Depends on:** T-01 through T-08  

**Verification sequence:**
1. `python -m pytest tools/test_validate_guides.py tools/test_build_site_routing.py -v` → all 22 tests pass
2. `python tools/validate_guides.py guides/product-documentation/` → 0 errors, 4 passes
3. `python tools/build-site.py --dry-run` → pilot guide at correct path; `docs/guides/` absent
4. `make build-check` → passes
5. `python tools/lint-agent-artifacts.py` → passes (no new agent artifacts)
6. `FORCE=1 make build-self && git status --short` → only expected changes, no generated-file drift
7. `npm ci --prefix docs-site && python tools/build-site.py && npm run build --prefix docs-site` → succeeds; `build/docs/guides/product-documentation/getting-started/index.html` exists
8. `python .claude/skills/work-loop/scripts/lint-spec-status.py docs/specs/guide-source-model/spec.md` → no doc-drift violations
9. Adversarial reviewer pass on the final diff

**Done when:** All steps pass; git status clean (except gitignored); adversarial-reviewer returns `Clean`.
