**Mode: light (no risk trigger fired)**

# Spec: self-host preferred-adapter fix

**Status:** Shipped

## Objective

Fix three bugs in the self-host build path:

1. `run_self_host` ignores `preferred-adapter` from `catalogue.toml` — always projects `claude-code`
   and `codex`, causing false drift for downstream repos that use only `kiro-ide`.
2. `shutil.copy2` in the shadow-clone and seed-copy paths calls `os.utime`, which fails in some
   CI environments. Replace with `shutil.copy` (copies content + permissions, no timestamps).
3. Claude Code-specific artifacts (`CLAUDE.md`, `.claude-plugin/marketplace.json`) are written
   unconditionally even when the effective adapter set does not include `claude-code`.

## Acceptance Criteria

- [x] AC1: When `catalogue.toml` has `preferred-adapter = "<A>"` and `<A>` is NOT in
  `SELF_HOST_ADAPTERS`, `_project_all_adapters` uses only `<A>` as the effective adapter set.
- [x] AC2: When `preferred-adapter` resolves to an adapter already in `SELF_HOST_ADAPTERS`,
  or is absent, `_project_all_adapters` uses `SELF_HOST_ADAPTERS` unchanged (backward
  compatible).
- [x] AC3: `check_self_host` and `write_self_host` in `catalogue_tooling/self_host.py` read
  `config.distribution.agentbundle.preferred_adapter` and pass it to `run_self_host` as
  `preferred_adapter=`.
- [x] AC4: `shutil.copy2` is replaced as follows — `shutil.copy` (content + permissions,
  no timestamps) in `_clone_target_subtree` (preserves mode so the drift gate never
  false-positives on permission bits) and `_project_seeds` (copies source mode regardless
  of umask — `copyfile` would create new files with umask-derived mode, which can differ
  from the source's 0o644 and cause false drift in strict-umask CI); `shutil.copyfile` +
  explicit `os.chmod` guarded with `contextlib.suppress(OSError)` in `adapter_root_bins.py`
  (real-write path — explicit chmod is guarded separately).
- [x] AC5: `.kiro/**` is removed from `EXCLUDED_PATTERNS` so kiro-projected files participate
  in drift comparison when kiro-ide is the effective adapter.
- [x] AC6: `Path(".kiro")` is added to `TARGET_PATHS` so the existing `.kiro/` tree is cloned
  into the shadow before projection (keeps merge semantics correct under dry-run).
- [x] AC7: When `claude-code` is NOT in the effective adapter set, `run_self_host` skips
  `_aggregate_marketplace` (`.claude-plugin/marketplace.json`) and `_recreate_claude_symlink`
  (`CLAUDE.md`) in both dry-run and real-write branches. Both artifacts are omitted from
  `extra_marker_paths` as well, so drift-check correctly ignores them.

## Tasks

1. `build/self_host.py` — TARGET_PATHS, EXCLUDED_PATTERNS, `_project_all_adapters`,
   `_build_projected_to_source_map`, `run_self_host`, shutil.copy2 → shutil.copy; gate
   `_aggregate_marketplace` + `_recreate_claude_symlink` on `_project_claude_artifacts`
2. `catalogue_tooling/self_host.py` — thread `preferred_adapter` from config into `run_self_host`
3. Tests — new assertions for preferred_adapter propagation and existing tests stay green

## Assumptions

- Touching: `build/self_host.py`, `catalogue_tooling/self_host.py`,
  `tests/unit/test_catalogue_tooling_self_host.py`
- Done when: `make lint-ruff` + `pytest packages/agentbundle/tests/ -q` pass; new tests
  assert `preferred_adapter` is propagated correctly
- Not changing: `self-host.toml` recipe, `cmd_self`/`cmd_check` (legacy; don't read
  catalogue.toml)

Declined: end-to-end integration test that runs `run_self_host` against a real kiro-ide
pack and asserts `.kiro` output exists / `.claude` absent — setting up a minimal kiro-ide
adapter fixture is disproportionate for this scope; AC1 is verified through the mocked
`_project_all_adapters` test plus the `_effective_adapters` unit tests. Follow up with a
kiro-ide fixture once the adapter has its own test pack.

Declined: updating `_build_projected_to_source_map` to include kiro source hints — the
function would need to replicate kiro-ide projection rules; the drift message still fires
correctly, just without the "edit X" hint. Low value for this PR; follow up separately.

Declined: adding kiro-ide to `self-host.toml` targets — unnecessary once `preferred_adapter`
acts as the override for non-SELF_HOST_ADAPTERS adapters.
