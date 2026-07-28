# Plan: product-documentation pack (Phase 1)

## Task list

All tasks use **goal-based verification** except where noted.

---

### T1 — New canonical pack skeleton
**Depends on:** none  
**Lane:** B (integration owner executes all lanes sequentially)  
**Files:** `packs/product-documentation/pack.toml`, `.claude-plugin/plugin.json`, `README.md`  
**Done when:** `agentbundle catalogue verify --root .` passes on the new pack; `pack.toml` version is `0.1.0`, `allowed-scopes = ["repo", "user"]`, no `core` dependency.

---

### T2 — `author-product-docs` SKILL.md
**Depends on:** T1  
**Files:** `packs/product-documentation/.apm/skills/author-product-docs/SKILL.md`  
**Done when:** SKILL.md contains five modes (create/revise/retrofit/audit/verify), 14-step procedure, correct destination logic (inspects repo structure, no hardcoded `docs/guides/`), activates on natural docs requests, does NOT activate on spec/RFC/ADR/strategy/implementation.

---

### T3 — Six reference files
**Depends on:** T2  
**Files:** `references/{artifact-model,page-contracts,repository-ownership,conversation-first,rendered-verification,clear-prose}.md`  
**Done when:** all six exist; `artifact-model.md` defines pack README / journey / guide / guide-index / DESIGN / mandatory-vs-conditional; `repository-ownership.md` distinguishes guides/ vs docs/guides/ vs pack dirs vs adopter layouts; `page-contracts.md` defines four Diátaxis types without binding to physical dirs; `rendered-verification.md` defines proportionate verification levels; `conversation-first.md` preserved; `clear-prose.md` preserved and improved.

---

### T4 — Evals
**Depends on:** T2  
**Files:** `evals/eval_queries.json`, `evals/evals.json`, `evals/files/` (3 fixtures)  
**Done when:** `eval_queries.json` has ≥8 positive, ≥8 near-miss; `evals.json` has ≥2 judge prompts with strong+weak fixture assertions; fixture files exist.

---

### T5 — Compat pack update (`user-guide-diataxis@0.3.0`)
**Depends on:** T1  
**Files:** `packs/user-guide-diataxis/pack.toml`, `.claude-plugin/plugin.json`, `README.md`, `.apm/skills/new-guide/SKILL.md`; DELETE `packs/user-guide-diataxis/seeds/`  
**Done when:** `pack.toml` has `version = "0.3.0"`, `display_name` includes "Deprecated", `[[pack.dependencies.required]] pack = "product-documentation"`, `lint-seeds` removed, `[pack.first-value]` removed; seeds/ directory gone; `new-guide` SKILL.md is a thin shim redirecting to `author-product-docs`; evals removed (compat pack has no live skill to eval).

---

### T6 — Catalogue-facing guides (`guides/product-documentation/`)
**Depends on:** T2  
**Files:** `guides/product-documentation/README.md`, `guides/product-documentation/how-to/use-author-product-docs.md`, `guides/product-documentation/explanation/the-diataxis-framework.md`  
**Done when:** README leads with outcomes; how-to walks the five modes with natural-language activations; explanation preserves and updates the Diátaxis framework description with new skill name.

---

### T7 — Maintainer how-to in `docs/guides/`
**Depends on:** T2  
**Files:** `docs/guides/how-to/author-product-documentation.md`  
**Done when:** explains where public catalogue guides live (`guides/`), where internal guides live (`docs/guides/`), how to use `author-product-docs`, how to avoid editing generated outputs.

---

### T8 — `guides/README.md` update
**Depends on:** T6  
**Files:** `guides/README.md`  
**Done when:** "All packs" table row for `user-guide-diataxis` replaced with `product-documentation` entry with updated description and link.

---

### T9 — Manifests: `site.toml`, `profiles/full-ceremony.toml`, `workspace.toml`
**Depends on:** T1  
**Files:** `site.toml`, `profiles/full-ceremony.toml`, `workspace.toml`  
**Done when:** `site.toml` "Content and design" group has `"product-documentation"`; `full-ceremony.toml` has `pack = "product-documentation"`; `workspace.toml` shaping_queue description and any queue references updated.

---

### T10 — `AGENTS.local.md` and `docs/architecture/overview.md`
**Depends on:** T1  
**Files:** `AGENTS.local.md`, `docs/architecture/overview.md`  
**Done when:** `AGENTS.local.md` "Two guide trees" section and "House style" section have correct skill/pack names, `--internal` flag mention removed; `docs/architecture/overview.md` pack table row updated.

---

### T11 — `packs/core/seeds/docs/CONVENTIONS.md` §5c update
**Depends on:** none (independent)  
**Files:** `packs/core/seeds/docs/CONVENTIONS.md`  
**Done when:** §5c describes `guides/` purpose and Diátaxis kinds without mandating `tutorials/`, `how-to/`, `reference/`, `explanation/` as the directory structure; references `author-product-docs` skill; `docs/CONVENTIONS.md` will be re-projected by build-self.

---

### T12 — agentbundle fixture and self-host.toml updates
**Depends on:** T1  
**Files:** `packages/agentbundle/agentbundle/build/recipes/self-host.toml`, fixture pack directory rename, `packages/agentbundle/agentbundle/build/tests/fixtures/README.md`, `packages/agentbundle/tests/fixtures/brownfield-adapt/docs/guides/how-to/index.md`  
**Done when:** self-host.toml `include` has `"product-documentation"` instead of `"user-guide-diataxis"`; fixture `packs/product-documentation/pack.toml` exists with correct name; fixture README updated; brownfield fixture reference updated.

---

### T13 — web/ content files
**Depends on:** T6  
**Files:** `web/src/content/packs/product-documentation.md` (from rename), `web/src/content/journeys/product-documentation.md` (from rename)  
**Done when:** both files reference `product-documentation` pack identity and `author-product-docs` skill; old files deleted.

---

### T14 — Deterministic tests (Lane D)
**Depends on:** T1, T5  
**Files:** test script in `packages/agentbundle/tests/` or `tools/`  
**Done when:** tests verify: no hardcoded `docs/guides/` path in shipped skill body, no seeds dir in product-documentation, skill references exist, compat pack has product-documentation dependency.

---

### T15 — build-self, gates, lint
**Depends on:** T1–T14  
**Done when:** `FORCE=1 make build-self` succeeds; `git status --short` confirms projection; `make build-check` green; `python3 tools/lint-skill-spec.py` green; `python3 tools/lint-agent-artifacts.py` green; `agentbundle catalogue verify --root .` green.
