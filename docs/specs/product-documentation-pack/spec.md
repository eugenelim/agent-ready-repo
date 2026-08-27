---
**Feature:** product-documentation-pack
- **Status:** Shipped
**Mode:** full (structural public-interface change, multi-feature, multi-dependent-task)
---

# Spec: product-documentation pack (Phase 1)

## Objective

Replace `user-guide-diataxis` (skill: `new-guide`) with `product-documentation` (skill: `author-product-docs`) as the canonical product documentation capability. Preserve backward compatibility for one deprecation cycle via a minimal `user-guide-diataxis@0.3.0` compat pack that depends on `product-documentation` and exposes a thin `new-guide` shim.

The new skill must support five explicit modes (create, revise, retrofit, audit, verify), treat Diátaxis as a page contract rather than a mandatory directory scaffold, correctly distinguish catalogue-facing `guides/` from internal `docs/guides/`, and remain portable across adopter repositories.

## Assumptions

- agentbundle's `[[pack.dependencies.required]]` field supports same-catalogue pack dependencies — verified against `packs/user-guide-diataxis/pack.toml` which uses this exact shape for `core`.
- No pack-level alias or deprecated-pack mechanism exists in agentbundle (confirmed via Lane A inventory); the only available compatibility mechanism is a dependency-only stub pack.
- `product-documentation` dropping the `core` dependency is safe: the skill does not use `adapt-to-project` or any other `core` primitive at installed-runtime.
- The `full-ceremony.toml` profile lint checks "dependency-complete (core satisfies each addon's core ^0.1)"; since `product-documentation` does not depend on `core`, this invariant is not violated when the profile uses `product-documentation`.

## Declined patterns

- Tempted to build a new agentbundle alias mechanism for pack names — declining; the backlog explicitly defers this until a real adopter install-base need exists.
- Tempted to migrate the entire `guides/` tree to by-Diátaxis-kind layout — declining; mission explicitly scopes this to Phase 1 only.
- Tempted to delete `docs/guides/` or redirect it — declining; it is preserved as maintainer guidance.
- Tempted to change the journey renderer or redesign the docs-site frontend — declining; not in scope.

## Acceptance Criteria

- [x] AC1: `packs/product-documentation/` exists with `pack.toml`, `.claude-plugin/plugin.json`, `README.md`, `.apm/skills/author-product-docs/` containing `SKILL.md` + six reference files + evals.
- [x] AC2: `packs/user-guide-diataxis/` updated to v0.3.0, deprecated, seeds removed, `[[pack.dependencies.required]]` points to `product-documentation`, `new-guide` skill replaced with thin shim.
- [x] AC3: `author-product-docs` supports five modes: create, revise, retrofit, audit, verify. Mode is inferred from the request; user need not name it.
- [x] AC4: `author-product-docs` SKILL.md contains no hardcoded `docs/guides/` output path; it inspects the host repo's guide structure and defaults to appropriate location.
- [x] AC5: `author-product-docs` distinguishes catalogue-facing `guides/`, internal `docs/guides/`, and arbitrary adopter layouts — described in `references/repository-ownership.md`.
- [x] AC6: `packs/product-documentation/` has no `seeds/` directory; `packs/user-guide-diataxis/` seeds/ directory removed.
- [x] AC7: `site.toml` "Content and design" group uses `product-documentation`.
- [x] AC8: `profiles/full-ceremony.toml` uses `product-documentation`.
- [x] AC9: `workspace.toml` references updated (shaping_queue description, queue spec reference).
- [x] AC10: `AGENTS.local.md` updated — pack/skill names, `--internal` flag mention removed.
- [x] AC11: `guides/product-documentation/` contains at least README.md, one how-to, one explanation.
- [x] AC12: `docs/guides/how-to/author-product-documentation.md` added — maintainer how-to explaining the ownership split and how to use the skill.
- [x] AC13: `guides/README.md` updated — `user-guide-diataxis` entry replaced with `product-documentation`.
- [x] AC14: `packs/core/seeds/docs/CONVENTIONS.md` §5c updated to remove mandatory four-subdir prescription; `docs/CONVENTIONS.md` re-projected.
- [x] AC15: `docs/architecture/overview.md` pack table updated.
- [x] AC16: `web/src/content/packs/product-documentation.md` created; `web/src/content/packs/user-guide-diataxis.md` retained as a deprecation stub (no redirect mechanism exists in the Astro site). Journey files updated on the same basis.
- [x] AC17: agentbundle `self-host.toml`, fixture pack directory, and fixture README updated.
- [x] AC18: `eval_queries.json` contains ≥8 positive queries and ≥8 near-misses covering all five modes and all required near-miss categories.
- [x] AC19: `evals.json` contains at least two LLM-judge prompts with assertions for strong and weak fixture behavior (eval IDs 4 and 5 reference `fixture_strong_pack_readme.md` and `fixture_weak_folder_first.md`).
- [x] AC20: `FORCE=1 make build-self` succeeds; `git status --short` shows only intentional changes survive projection.
- [x] AC21: `make build-check` passes.
- [x] AC22: `python3 tools/lint-skill-spec.py` passes (gated inside `make build-check`).
- [x] AC23: `python3 tools/lint-agent-artifacts.py` passes (gated inside `make build-check`).
- [x] AC24: `tools/pre-pr-catalogue.py` (or equivalent full catalogue gate) passes (`make build-check` runs this via `build_gate_chain.py`).
- [x] AC25: old and new install paths produce collision-free installed state (tested deterministically in `test_product_documentation_pack.py`).
- [x] AC26: `packs/product-documentation/` scope updated to `["repo", "user"]`.

## Testing Strategy

- **Goal-based verification** for each AC — verified via grep, cat, agentbundle commands, and build tooling.
- **Deterministic tests** (Lane D) for: no hardcoded `docs/guides/` in shipped skill body, seeds not present, skill references valid, no duplicate canonical implementation, pack dependency wiring correct.
- **LLM-judge evals** (`evals.json`) for output quality — strong fixtures (task-first, verified, correct audience) and weak fixtures (folder-first, misdirected audience, invented behavior).
- **`agentbundle catalogue verify --root .`** for pack schema validity.
- **`FORCE=1 make build-self && git status`** to confirm projection correctness.
