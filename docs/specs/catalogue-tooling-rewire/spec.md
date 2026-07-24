# Spec: Catalogue Tooling — Repository Rewiring

- **Status:** Draft
- **Owner:** eugenelim
- **Initiative:** ini-005 AgentBundle Portable Catalogue Tooling
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ini-005 brief Bucket 9; all prior Wave 1-4 specs
- **Shape:** service

> **Spec contract:** this document defines what "done" means.

## Objective

After the Wave 1-4 specs ship the portable engine, this repo's Makefile, CI
workflows, and `tools/` still call `python -m agentbundle.build lint-packs`,
`python -m agentbundle.build build`, and `python -m agentbundle.build check`
directly, and `tools/pre-pr-catalogue.py` performs verification that duplicates
`agentbundle catalogue verify`. The tools/ directory is flat with no separation
between portable-logic callers and repo-governance scripts.

This spec rewires the home repository to use the new public engine and organizes
`tools/` into the `tools/catalogue/` + `tools/repo/` split described in Bucket 9.
It also introduces the `make build-check` new flow: `agentbundle catalogue verify`
first, then repo-only policy gates.

## Boundaries

### Always do

- Repoint Makefile targets per Bucket 9:
  - `make lint-packs` → `agentbundle catalogue lint --root .`
  - `make build` → `agentbundle catalogue build --root . --output $(OUTPUT_DIR)`
  - `make build-self` → `agentbundle catalogue self-host --root . --write`
    (preserving FORCE=1 as `--write --force`)
  - `make build-self-dry-run` → `agentbundle catalogue self-host --root . --check`
  - portable portion of `make build-check` → `agentbundle catalogue verify --root .`
  - `make package` (new target) → `agentbundle catalogue package ...`
- Reorganize tools/ into `tools/catalogue/` and `tools/repo/`. Move only tools
  whose responsibilities clearly belong to one bucket:
  - `tools/publish-claude-plugins.py` → `tools/catalogue/publish_claude_plugins.py`
  - `tools/pre-pr-catalogue.py` → `tools/catalogue/pre_pr_catalogue.py` (thinned
    to call `agentbundle catalogue verify` + repo-specific checks only)
  - `tools/build_gate_chain.py` → `tools/repo/build_gate_chain.py`
  - `tools/check-contract-drift.py` → `tools/repo/check_contract_drift.py`
  - `tools/release-check.sh` → `tools/repo/release_check.sh`
- For every moved script: update all callers (Makefile, CI workflows, hooks.json,
  `settings.json`), add a shim at the old path that delegates to the new path
  and prints a one-line deprecation to stderr. Keep shims until at least the next
  minor release.
- Thin `tools/catalogue/pre_pr_catalogue.py` to: (1) call
  `agentbundle catalogue verify`, (2) then run repo-specific checks (spec state
  validation, traceability, brief coverage). Do not duplicate portable logic.
- The new `make build-check` sequence: (1) `agentbundle catalogue verify`,
  (2) repo-only policy gates from `tools/repo/build_gate_chain.py`, (3) SAST/SCA.
- All existing `tools/` callers work without modification through shims until
  explicitly deprecated.
- All existing tests pass.

### Ask first

- Moving any tool that doesn't have a clear single-bucket ownership.
- Deleting the flat `tools/lint-*.py` scripts (they are repo-governance, not
  portable; stay as-is unless a clear redesign is planned).
- Removing the `build_gate_chain.py` Windows cross-platform support.

### Never do

- Put portable linting, build, verification, or packaging logic inside tools/.
- Remove shims before the next minor AgentBundle release.
- Rename the `build_gate_chain.py` script in a way that breaks existing Windows
  contributors.
- Move hooks.json-referenced scripts without updating hooks.json first.

## Testing Strategy

- **Goal-based** for Makefile target wiring: `make lint-packs` produces the same
  result as `agentbundle catalogue lint --root .` (compare exit codes).
- **TDD** for shim delegation: each shim imports the delegate and calls it; test
  asserts the shim's exit code matches the delegate's.
- **Goal-based** for moved script existence: old paths exist (shims), new paths
  exist (real implementations).
- **Goal-based** for build-check sequence: `tools/repo/build_gate_chain.py
  build-check` runs verify first; assert it exits early if verify fails.

## Acceptance Criteria

- [ ] AC1: `make lint-packs` calls `agentbundle catalogue lint --root .`.
- [ ] AC2: `make build-self` calls `agentbundle catalogue self-host --root . --write`.
- [ ] AC3: `make build-self-dry-run` calls `agentbundle catalogue self-host --root . --check`.
- [ ] AC4: The full `make build-check` sequence first runs `agentbundle catalogue verify`
  then runs repo-only gates from `tools/repo/build_gate_chain.py`.
- [ ] AC5: `tools/publish-claude-plugins.py` redirects (shim) to
  `tools/catalogue/publish_claude_plugins.py`.
- [ ] AC6: `tools/pre-pr-catalogue.py` is thinned to call `agentbundle catalogue verify`
  and then repo-specific checks; shim at old path delegates.
- [ ] AC7: `tools/build_gate_chain.py` is a shim delegating to
  `tools/repo/build_gate_chain.py`; all existing CI workflow paths work.
- [ ] AC8: `hooks.json` and `settings.json` hook wiring paths are updated to
  new locations before shims are added (so hooks run the real scripts).
- [ ] AC9: No portable catalogue logic (linting, building, verification,
  packaging) remains implemented only inside `tools/`.
- [ ] AC10: An external catalogue can use `agentbundle catalogue lint`,
  `agentbundle catalogue verify`, `agentbundle catalogue build`,
  `agentbundle catalogue package` without copying the Makefile or tools/.
- [ ] AC11: All existing CI jobs pass.
- [ ] AC12: All existing tests pass.

## Assumptions

1. All Wave 1-4 specs ship before this spec begins.
2. The `tools/pre-pr-catalogue.py` script references no portable logic
   by the time this spec runs (Wave 2-4 specs moved it to agentbundle).
3. Windows contributors use `python tools/repo/build_gate_chain.py` — the shim
   at `tools/build_gate_chain.py` preserves this.
4. hooks.json wiring uses Python-relative paths; updating paths is safe.
