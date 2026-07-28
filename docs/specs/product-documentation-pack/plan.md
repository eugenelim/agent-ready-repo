# Plan: Product Documentation Pack — Phase 1 Foundation

## T-01 — Create packs/product-documentation/ canonical pack (Lane B)

**Verification:** Goal-based
**Depends on:** none
**Touches:** `packs/product-documentation/`

**Done when:**
- `packs/product-documentation/pack.toml` valid (version 0.1.0, no core dep, user+repo scopes)
- `packs/product-documentation/.claude-plugin/plugin.json` present
- `packs/product-documentation/README.md` leads with outcomes
- `packs/product-documentation/.apm/skills/author-product-docs/SKILL.md` present with five modes
- All six reference files present
- `evals/eval_queries.json` ≥8 positive + ≥8 near-miss
- `evals/evals.json` has strong + weak output fixtures

**Tests:**
- T-D4: install tree has no four-quadrant seed paths
- T-D5: lint-skill-spec passes on canonical pack

---

## T-02 — Convert packs/user-guide-diataxis/ to deprecated compat shim (Lane D)

**Verification:** Goal-based
**Depends on:** T-01
**Touches:** `packs/user-guide-diataxis/`

**Done when:**
- pack.toml: version 0.3.0, display_name includes "(Deprecated)", dependency on `product-documentation`, `[pack.evals]` block removed
- plugin.json version bumped to 0.3.0
- README updated to deprecated notice with migration instructions
- `seeds/` directory removed
- `new-guide` SKILL.md replaced with thin compat redirect (≤30 lines, names author-product-docs, activates on legacy phrases only)
- `new-guide/evals/` directory removed

**Tests:**
- T-D1: bare shim install errors with "install product-documentation first"
- T-D3: shim install tree has no `seeds/guides/`

---

## T-03 — Update catalogue guides (Lane C)

**Verification:** Goal-based
**Depends on:** none (parallel with T-01)
**Touches:** `guides/`, `docs/guides/how-to/`

**Done when:**
- `guides/product-documentation/` directory exists (renamed from `guides/user-guide-diataxis/`)
- `guides/product-documentation/README.md` updated for new pack identity
- `guides/product-documentation/explanation/the-diataxis-framework.md` updated (pack name refs)
- `guides/product-documentation/how-to/write-a-guide.md` updated for `author-product-docs`
- New `guides/product-documentation/how-to/author-product-docs.md` created (main skill guide)
- `docs/guides/how-to/author-product-documentation.md` created (maintainer how-to)
- `guides/README.md` updated
- `guides/_shared/` references updated

**Tests:** (no new tests; structural check via `make build-check`)

---

## T-04 — Update manifests and cross-references (Integration)

**Verification:** Goal-based
**Depends on:** T-01, T-02, T-03
**Touches:** `site.toml`, `profiles/`, `README.md`, `AGENTS.local.md`, `web/src/content/`, `docs-site/`, `workspace.toml`, `docs/architecture/`, `docs/product/changelog.md`

**Done when:**
- `site.toml` "Content and design" group: `product-documentation` in packs list
- `profiles/full-ceremony.toml` updated to `product-documentation`
- Root `README.md` table row updated
- `AGENTS.local.md` `user-guide-diataxis`/`new-guide` refs updated
- `web/src/content/packs/product-documentation.md` created; `user-guide-diataxis.md` updated to shim description
- `web/src/content/journeys/product-documentation.md` created; `user-guide-diataxis.md` updated
- `docs-site/astro.config.ts` slugs updated; section label updated
- `docs-site/src/content/docs/index.mdx` table row updated
- `docs/product/changelog.md` new entries at top (product-documentation 0.1.0 + user-guide-diataxis 0.3.0)
- `workspace.toml` comment updated
- `docs/architecture/overview.md` pack table row updated (if present)

**Tests:** `grep -r "user-guide-diataxis" packs/ guides/ site.toml profiles/ README.md AGENTS.local.md --include="*.md" --include="*.toml"` returns only the shim's own files and frozen docs

---

## T-05 — Update agentbundle tests and tools (Lane D)

**Verification:** Goal-based — `pytest packages/agentbundle` green
**Depends on:** T-01, T-02
**Touches:** `packages/agentbundle/`, `tools/`

**Done when:**
- All test constants/tuples updated: `user-guide-diataxis` → `product-documentation`
- `packages/agentbundle/tests/fixtures/install_snapshot/product-documentation.paths.txt` created
- Old `user-guide-diataxis.paths.txt` fixture removed
- New T-D1/T-D2/T-D3/T-D4 deterministic tests added
- `packages/agentbundle/agentbundle/build/self_host.py` `_DEFAULT_SELF_HOST_PACKS` updated (add `product-documentation`)
- `packages/agentbundle/agentbundle/build/recipes/self-host.toml` `include` list updated (add `product-documentation`, keep `user-guide-diataxis`)
- `tools/add-rendering-directives.py` comment and `"new-guide"` key updated to `"author-product-docs"`

**Tests:** `pytest packages/agentbundle -x`

---

## T-06 — Draft ADR for future machine-ID migration

**Verification:** Goal-based
**Depends on:** T-01, T-02
**Touches:** `docs/adr/`

**Done when:**
- ADR present at `docs/adr/NNNN-rename-user-guide-diataxis-to-product-documentation.md`
- Documents the deprecation cycle, migration steps, and condition under which the machine ID can be retired

---

## T-07 — Run build-self + full gates

**Verification:** All gates green
**Depends on:** T-01 through T-06

**Done when:**
- `FORCE=1 make build-self` exits 0
- `git status --short` shows no unexpected uncommitted changes in projected dirs
- `make build-check` exits 0
- `python3 tools/lint-skill-spec.py` exits 0
- `python3 tools/lint-agent-artifacts.py` exits 0
- `pytest packages/agentbundle -x` exits 0

---

## Exit checklist

- [ ] All T-01 through T-07 done
- [ ] All AC-01 through AC-27 checked
- [ ] Gates green (lint, build-self, build-check, pytest)
- [ ] Adversarial reviewer returned `Clean — ready to commit.`
- [ ] `git status` clean
- [ ] `docs/specs/product-documentation-pack/spec.md` Status: Implementing → Shipped (after merge)
- [ ] `workspace.toml` updated with shipped spec entry if spec path is in active queue
