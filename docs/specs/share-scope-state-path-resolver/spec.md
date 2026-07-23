# Spec: share-scope-state-path-resolver

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)

Mode: full (structural change — new public helper in `_common`; three commands migrated)

## Objective

The `agentbundle` CLI duplicates the same two-line scope-to-state-path mapping
in three command files (`uninstall.py`, `upgrade.py`, `diff.py`) — each
independently hard-coding that repo scope → `<root>/.agentbundle-state.toml` and
user scope → `<root>/.agentbundle/state.toml`. A single extracted helper,
`_common.resolve_state_path(scope, root)`, eliminates the duplication and gives
future commands a single, tested source of truth for scope-to-path resolution.

## Boundaries

### Always do

- Extract the common path mapping only — `resolve_state_path(scope, root)` is
  pure `pathlib.Path` arithmetic; no filesystem access, no subprocess calls, no
  imports beyond stdlib.
- Use only pure stdlib inside `_common.py`; the module restricts to stdlib, and
  `resolve_state_path` must comply.
- Keep each migrated call site behaviorally identical: the same `scope` string
  and `root` Path that were used inline must be passed through; no surrounding
  logic changes.
- Write a focused unit test for `resolve_state_path` that covers both scopes
  before migrating any call site (TDD order).

### Ask first

- Any change to the surrounding scope-inference logic (the "if both scopes,
  require `--scope`" and "infer from installed_at_*" blocks) in any of the
  three files — that logic is explicitly out of scope.
- Any change to the error message text or exit codes in `uninstall.py`,
  `upgrade.py`, or `diff.py`.
- Any new import added to `_common.py` beyond what already exists.

### Never do

- Change the resolved paths themselves: user state is `<root>/.agentbundle/state.toml`
  and repo state is `<root>/.agentbundle-state.toml`; these are the contract.
- Modify `install.py` — it resolves scope differently (via `_ScopePlan` + the
  six-step adapter resolution) and has its own tests that are not regression targets here.
- Change `list_installed.py` — it already does the path computation cleanly
  inline and is not a migration target.
- Add a new top-level module, directory, or dependency.
- Change any test assertion that currently passes — existing tests are the
  regression baseline; this spec adds coverage, never removes it.

## Testing Strategy

- **`resolve_state_path` helper (AC1, AC4):** TDD — write the unit test in
  `packages/agentbundle/tests/unit/` before adding the function, cover
  `scope="repo"` and `scope="user"`, assert exact `Path` values. The function
  has no side effects and the invariant is compressible, making this the
  canonical TDD shape.
- **Migration parity for `uninstall`, `upgrade`, `diff` (AC2, AC3):** goal-based
  check — the existing integration and unit tests for each command run green before
  and after the migration with no assertion changes. Each command's full test suite
  is the parity proof.

## Acceptance Criteria

- [x] AC1: `_common.resolve_state_path(scope, root)` exists, is public, and carries
  a docstring naming both scope values and their returned paths.
- [x] AC2: All three commands — `uninstall.py`, `upgrade.py`, `diff.py` — call
  `resolve_state_path` for their state-file path computation. No inline path-build
  expressions of the form `root / ".agentbundle-state.toml"` or
  `root / ".agentbundle" / "state.toml"` remain in non-comment, non-docstring code
  (verified by grep excluding `#`-prefixed lines). Exception: `upgrade.py`'s string
  comparison `state_relpath == ".agentbundle-state.toml"` at line 724 is a filename
  equality check — not a path build — and must remain unchanged.
- [x] AC3: Every existing regression test for `uninstall`, `upgrade`, and `diff`
  (unit and integration) passes unchanged — no assertion text, no helper count,
  no exit code asserted by a test is modified.
- [x] AC4: A new unit test for `resolve_state_path` covers `scope="repo"` and
  `scope="user"`, asserts the exact `Path` returned, and lives in
  `packages/agentbundle/tests/unit/`.
- [x] AC5: `_common.py` imports no new module — `resolve_state_path` uses only
  `pathlib.Path`, which is already imported at module level.

## Assumptions

- Technical: Python runtime is ≥3.11 (`packages/agentbundle/pyproject.toml`).
- Technical: `_common.py` is restricted to pure stdlib; `resolve_state_path`
  uses only `pathlib.Path` (already imported) and is compliant.
- Technical: The path formulas are already structurally uniform across all three
  files — the extraction is mechanical: user → `<root>/.agentbundle/state.toml`,
  repo → `<root>/.agentbundle-state.toml` (confirmed: `uninstall.py` lines 54/75,
  `upgrade.py` lines 118/131–133 and 247–251, `diff.py` lines 60/67–68).
- Scope: `install.py` and `list_installed.py` are not migration targets.
- Scope: The scope-inference logic (multi-scope disambiguation, error messages)
  is not changing — only the two-line path formula is extracted.

## Tasks

See `plan.md`.

## Declined

- Extracting the full multi-scope disambiguator pattern (the "if both scopes,
  require `--scope`" block) — the three commands have subtly different surrounding
  logic and the existing tests pin each command's error message text independently.
- Adding `scope` validation inside `resolve_state_path` — the call sites already
  control which scope string they pass; a guard adds defensive surface not needed.
- Migrating `list_installed.py` — it already does the path computation correctly
  inline and is not a source of the described duplication.
- Migrating `install.py`'s 9+ identical path-formula occurrences — `install.py`
  resolves scope via `_ScopePlan` and the six-step adapter resolution path rather
  than the simple two-branch disambiguator that `uninstall.py`, `upgrade.py`, and
  `diff.py` share. The scope-to-path formula in install.py is the same bytes but
  the surrounding scope-inference contract differs materially; a separate follow-on
  spec (`unify-path-jail-projection-probe` covers the jail side; a future scope
  spec would cover the path-formula side) is the right vehicle. The Objective
  "single, tested source of truth" is scoped to the three disambiguator commands.

## Changelog

- 2026-07-23: Implemented and shipped — `resolve_state_path` added to `_common.py`; `diff.py`, `uninstall.py`, `upgrade.py` migrated. Full regression suite passes.
