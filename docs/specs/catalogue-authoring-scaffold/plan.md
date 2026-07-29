# Catalogue Authoring Scaffold — Plan

**Status:** Done

## Tasks

### T1: Reserved `_` path filter across all discovery call sites
**Mode:** TDD (unit + integration)
**Depends on:** none
**Tests:** `tests/integration/test_reserved_path_filter.py` — assert `_example` excluded from list-packs, build, lint, verify, self-host, package, profile_load_packs; assert valid pack named `_bad` is rejected/skipped with clear diagnostic.

**Approach:**
- `build/main.py discover_packs`: add `and not entry.name.startswith("_")` to the filter
- `commands/list_packs.py _discover_pack_dirs`: filter candidates by `not p.name.startswith("_")`
- `catalogue_tooling/lint.py _profile_load_packs`: skip `pack_dir.name.startswith("_")`
- `catalogue_tooling/lint.py _check_duplicate_identities`: skip `entry.name.startswith("_")`
- `catalogue_tooling/lint.py lint_catalogue`: skip `pack_dir.name.startswith("_")`
- `catalogue_tooling/verify.py`: three `iterdir()` loops — skip `_` prefix
- `build/self_host.py _project_seeds` and the other iterdir loop: skip `_` prefix
- `catalogue_tooling/package.py _scan_content`: filter `_` prefix subdirs at packs root level in os.walk

**Done when:** `agentbundle list-packs`, `catalogue build`, `catalogue lint`, `catalogue verify`, `catalogue self-host`, `catalogue package` all ignore a `packs/_example/` directory.

### T2: Pack authoring scaffold content
**Mode:** Goal-based
**Depends on:** T1
**Tests:** Structural presence checks; `agentbundle catalogue verify` on test catalogue with example pack.

**Approach:**
- Create `packs/README.md` (portable, 14 required sections)
- Create `packs/_example/README.md` (canonical pack README template)
- Create `packs/_example/pack.toml` (valid, `example-pack` identity)
- Create `packs/_example/.claude-plugin/plugin.json`
- Create `packs/_example/.apm/skills/example-skill/SKILL.md`
- Create `packs/_example/evals/eval_queries.json`

**Done when:** All files exist; copy to `packs/example-pack` + lint passes.

### T3: packs/AGENTS.md portability
**Mode:** Goal-based
**Depends on:** none (independent of T1)
**Tests:** Line count ≤ 150; no Make targets as portable requirements; references `AGENTS.local.md`.

**Approach:**
- Move host-specific sections to `packs/AGENTS.local.md`
- Rewrite `packs/AGENTS.md` as portable (no `make build-self`, no `docs/product/changelog.md`, no `FORCE=1`, etc.)
- Keep packs/AGENTS.md ≤ 150 lines

**Done when:** File is portable; `make build-check` passes; line count within limit.

### T4: Profile authoring scaffold content
**Mode:** Goal-based
**Depends on:** none
**Tests:** Structural presence; `list-profiles` returns empty for reserved example.

**Approach:**
- Create `profiles/README.md` (portable, 12 required sections)
- Create `profiles/AGENTS.md` (current profile schema contract)
- Create `profiles/_example/README.md`
- Create `profiles/_example/profile.toml` (composes `example-pack`)

**Done when:** All files exist; `list-profiles` doesn't include `_example`.

### T5: Blank catalogue validity
**Mode:** TDD
**Depends on:** T1, T2, T4
**Tests:** `tests/integration/test_blank_catalogue.py` — lint + verify + list-packs + list-profiles all succeed on a scratch catalogue with 0 packs, 0 profiles.

**Approach:**
- Check and fix any assumptions that a real pack must exist for lint/verify to pass
- Create a test fixture catalogue with only orientation files + reserved examples + empty marketplace
- Verify the fixture passes lint and verify

**Done when:** Blank catalogue passes all 4 portable commands.

### T6: AgentBundle package-data projection
**Mode:** TDD
**Depends on:** T2, T4
**Tests:** `tests/integration/test_scaffold_projection.py` — check/write idempotency, hash verification, no local overlays, wheel contains scaffold.

**Approach:**
- Create `packages/agentbundle/agentbundle/_data/catalogue-scaffold/` directory
- Create `tools/catalogue/sync_authoring_scaffold.py` (--check / --write)
- Create `packages/agentbundle/agentbundle/scaffold.py` (internal loader API)
- Update `pyproject.toml` package-data glob to `"_data/*", "_data/catalogue-scaffold/*", "build/recipes/*.toml"`

**Done when:** `python tools/catalogue/sync_authoring_scaffold.py --check` exits 0; wheel built and contains scaffold files.

### T7: Tests
**Mode:** TDD
**Depends on:** T1-T6
**Tests:** Files listed above.

**Approach:**
- Write all test files referenced in T1-T6

**Done when:** `pytest packages/agentbundle/tests/` passes.

### T8: Documentation updates and dogfooding
**Mode:** Goal-based
**Depends on:** T2, T4
**Tests:** `agentbundle catalogue lint --root .` passes.

**Approach:**
- Update `AGENTS.local.md` (release-impact policy)
- Update `packs/AGENTS.local.md` (clarify host-only boundary, projection notes)
- Check catalogue-curation pack skill for scaffold references

**Done when:** Lint green; AGENTS.local.md has release policy.
