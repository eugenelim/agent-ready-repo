**Mode: light (no risk trigger fired)**

# Spec: self-host preferred-adapter fix

**Status:** Shipped

## Objective

Fix two bugs in the self-host build path:

1. `run_self_host` ignores `preferred-adapter` from `catalogue.toml` — always projects `claude-code`
   and `codex`, causing false drift for downstream repos that use only `kiro-ide`.
2. `shutil.copy2` in the shadow-clone and seed-copy paths calls `os.utime`, which fails in some
   CI environments. Replace with `shutil.copy` (copies content + permissions, no timestamps).

## Acceptance Criteria

- [x] AC1: When `catalogue.toml` has `preferred-adapter = "<A>"` and `<A>` is NOT in
  `SELF_HOST_ADAPTERS`, `_project_all_adapters` uses only `<A>` as the effective adapter set.
- [x] AC2: When `preferred-adapter` resolves to an adapter already in `SELF_HOST_ADAPTERS`,
  or is absent, `_project_all_adapters` uses `SELF_HOST_ADAPTERS` unchanged (backward
  compatible).
- [x] AC3: `check_self_host` and `write_self_host` in `catalogue_tooling/self_host.py` read
  `config.distribution.agentbundle.preferred_adapter` and pass it to `run_self_host` as
  `preferred_adapter=`.
- [x] AC4: `shutil.copy2` is replaced with `shutil.copy` (and `shutil.copytree` uses
  `copy_function=shutil.copy`) in `_clone_target_subtree` and `_project_seeds`.
- [x] AC5: `.kiro/**` is removed from `EXCLUDED_PATTERNS` so kiro-projected files participate
  in drift comparison when kiro-ide is the effective adapter.
- [x] AC6: `Path(".kiro")` is added to `TARGET_PATHS` so the existing `.kiro/` tree is cloned
  into the shadow before projection (keeps merge semantics correct under dry-run).

## Tasks

1. `build/self_host.py` — TARGET_PATHS, EXCLUDED_PATTERNS, `_project_all_adapters`,
   `_build_projected_to_source_map`, `run_self_host`, shutil.copy2 → shutil.copy
2. `catalogue_tooling/self_host.py` — thread `preferred_adapter` from config into `run_self_host`
3. Tests — new assertions for preferred_adapter propagation and existing tests stay green

## Assumptions

- Touching: `build/self_host.py`, `catalogue_tooling/self_host.py`,
  `tests/unit/test_catalogue_tooling_self_host.py`
- Done when: `make lint-ruff` + `pytest packages/agentbundle/tests/ -q` pass; new tests
  assert `preferred_adapter` is propagated correctly
- Not changing: `self-host.toml` recipe, `cmd_self`/`cmd_check` (legacy; don't read
  catalogue.toml)

Declined: updating `_build_projected_to_source_map` to include kiro source hints — the
function would need to replicate kiro-ide projection rules; the drift message still fires
correctly, just without the "edit X" hint. Low value for this PR; follow up separately.

Declined: adding kiro-ide to `self-host.toml` targets — unnecessary once `preferred_adapter`
acts as the override for non-SELF_HOST_ADAPTERS adapters.
