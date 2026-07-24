# Spec: credbroker-security-hardening

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** `credential-broker-contract` spec (round-4 security review, Concerns 1 and 4 deferred)

Mode: full (security boundary — credbroker test hardening)

> **Spec contract:** this document defines what "done" means. The implementing PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Close three deferred security-hardening items recorded in the `credential-broker-contract` spec's 2026-05-26 Changelog (round-4 security review, Concerns 1 and 4 — deferred by that PR, unblocked now):

**D3 — substring scan is bypassable.** The dotfile-read detection in `tools/lint_credentialed_skills.py` (lines 908–925) is a line-by-line substring scan for `.agentbundle/credentials.env`. A consumer that constructs the path from concatenated string fragments — e.g. `Path.home() / (".agent" + "bundle") / ("credentials" + ".env")` then calls `.read_text()` — opens the dotfile without the literal substring `.agentbundle/credentials.env` ever appearing on any single source line. The fix rewrites D3 as an AST walk over `open()`, `.read_text()`, and `.read_bytes()` call sites, using the existing `_path_chain_components()` helper (already in the file) to reconstruct part-composed path chains before matching.

**`_is_canonical_shim` — exemption is not path-anchored.** The current shim exemption (`_is_canonical_shim`) grants bypass treatment to any file whose basename is in `SHIM_BASENAMES` and whose bytes match the canonical source. This means a file named `credentials_shim.py` at an arbitrary location in the repo tree (e.g. `packs/evil-pack/.apm/some-dir/credentials_shim.py`) would be exempt if it carries canonical bytes — even though the build pipeline never places files in such a location. The fix adds a path-anchor requirement: the file must reside inside a directory named `scripts` (consumer skill projection target) or `shared-libs` (canonical source directory) for the exemption to apply. Byte-equality is kept as a secondary check.

**`_load_cli_module()` — integration tests load from pack source only.** The SSO broker verb tests (`test_sso_broker_verbs.py`) load the broker exclusively from the pack source path. The user-scope invocation tests (`test_credential_user_scope_invocation.py`) stage consumer skills exclusively from the pack source. Neither test suite exercises the projected copies that `make build-self` emits (in `dist/apm/`) or that `agentbundle install` places in `~/.agentbundle/bin/`. The fix introduces a `_load_cli_module(path)` staging helper and parametrises affected tests over both the source path and the projected path, with `pytest.skip` when the projected copy is absent (unbuilt checkout).

## Acceptance Criteria

### D3: AST walk for dotfile-read detection

- [x] **AC1 (D3 — implementation):** The dotfile-read check in `tools/lint_credentialed_skills.py` is rewritten from a line-by-line substring scan to an AST walk implemented as a helper `_check_dotfile_read(py_path) -> list[tuple[int, str]]`. The walk visits every `ast.Call` node and raises a finding when: (a) the call is `open(<arg>)` (i.e. `func` is `ast.Name` with `id == "open"`) and the first positional argument resolves to the dotfile path; OR (b) the call is `<expr>.read_text(...)` or `<expr>.read_bytes(...)` (i.e. `func` is `ast.Attribute` with `attr` in `{"read_text", "read_bytes"}`) and the object expression `func.value` resolves to the dotfile path. Path resolution uses the existing `_path_chain_components()` helper; a finding is raised when the resolved components' last two entries match `(DOTFILE_PARENT, DOTFILE_BASENAME)` in order. The opt-out marker check is applied by reading the corresponding source line at the reported `lineno` and suppressing the finding when `OPTOUT_MARKER` appears on that line.

- [x] **AC2 (D3 — part-composition bypass caught):** A new test case in `tools/test-lint-credentialed-skills.py` supplies a fixture script that uses inline part-composition (fully inline in the method call, so `_path_chain_components()` can resolve it):
  ```python
  (Path.home() / ("." + "agentbundle") / ("credentials" + ".env")).read_text()
  ```
  The fixture verifies: (a) that no line in the fixture source contains `.agentbundle/credentials.env` as a contiguous substring (proving the old substring scan would miss it); and (b) the new AST walk catches the `.read_text()` call and reports a finding with the call's lineno. Note: `_path_chain_components()` resolves inline `BinOp(Add)` string concatenation within `BinOp(Div)` path chains, but cannot resolve identifiers bound to intermediate variables — the fixture must use the fully-inline form.

- [x] **AC3 (D3 — `Path.read_bytes()` form caught):** A second test case supplies a fixture script using the inline `.read_bytes()` form:
  ```python
  (Path.home() / ".agentbundle" / "credentials.env").read_bytes()
  ```
  The AST walk catches the `.read_bytes()` call on the inline-constructed path and reports a finding. (The cross-variable-assignment form — binding the path to a name then calling `.read_bytes()` on the name — is explicitly Declined; this AC covers the inline form only.)

- [x] **AC4 (D3 — opt-out still works):** The existing test case `dotfile-read-with-opt-out-allowed` continues to pass under the rewritten D3 check: a skill whose dotfile-read call is on the same line as `# credentialed-primitive: reads-creds-directly` exits the lint clean.

- [x] **AC5 (D3 — existing `dotfile-read-refused` test still passes):** The existing `dotfile-read-refused` case (a bare `open('.agentbundle/credentials.env').read()` call on one line) continues to be caught by the AST walk and exits non-zero.

### `_is_canonical_shim`: path-anchor

- [x] **AC6 (`_is_canonical_shim` — path anchor added):** `_is_canonical_shim(py: pathlib.Path) -> bool` adds a path-anchor check before the byte-equality comparison: the function returns `False` immediately when `py.parent.name` is not in `{"scripts", "shared-libs"}`, even if the file's bytes match the canonical source. The anchor uses `py.parent.name` (a single path segment, not a substring match) per `feedback_credentialed_lint_substring_trap`. Note: `credentials_shim.py` also ships tracked at `.agentbundle/bin/credentials_shim.py` (parent `bin`), but the lint's scan roots (`packs/*/.apm/skills/*`, `.claude/skills/*`, `skills/*`) never reach `.agentbundle/bin/`, so `bin`-projected shims are intentionally outside the scanned set and are not affected by this anchor.

- [x] **AC7 (`_is_canonical_shim` — non-canonical path not exempt):** A unit test asserts that a copy of `credentials_shim.py` placed at a non-canonical parent directory (e.g. `some-pack/arbitrary/credentials_shim.py` where `parent.name == "arbitrary"`) returns `False` from `_is_canonical_shim` even when its bytes match the canonical source byte-for-byte.

- [x] **AC8 (`_is_canonical_shim` — canonical paths remain exempt):** A unit test asserts that `credentials_shim.py` under a `scripts/` parent and under a `shared-libs/` parent (with matching canonical bytes) each return `True`.

### `_load_cli_module()`: parametrised integration tests

- [x] **AC9 (`_load_cli_module` helper added):** A helper `_load_cli_module(py_path: pathlib.Path) -> types.ModuleType` is added to the credbroker test suite (either as a module-level function in a new `packages/agentbundle/tests/unit/test_credbroker_lint_hardening.py` or as a shared helper imported from a new `packages/agentbundle/tests/_credbroker_helpers.py`). The implementation loads the file via `importlib.util.spec_from_file_location` with the file's directory prepended to `sys.path` for the duration of the load (the same pattern as the existing `_load_broker_module()` in `test_sso_broker_verbs.py`).

- [x] **AC10 (SSO broker verb tests — source + projected parametrisation):** The `broker` fixture in `packages/agentbundle/tests/unit/test_sso_broker_verbs.py` is parametrised over two paths:
  - **source**: `packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py` (existing behavior)
  - **projected**: `REPO_ROOT / ".agentbundle" / "bin" / "sso-broker.py"` (the `make build-self` output in this checkout)

  The projected variant uses `pytest.skip(f"{path} not present — run make build-self")` when the file is absent. Both variants must pass when the projected file exists.

- [x] **AC11 (user-scope invocation tests — source + projected parametrisation):** The `test_entry_point_imports_resolve_under_user_scope_layout` parametrisation in `packages/agentbundle/tests/integration/test_credential_user_scope_invocation.py` gains a second staging variant for each consumer skill:
  - **source**: `packs/<pack>/.apm/skills/<skill>/scripts/` (existing `PACKS / skill_relpath` staging — unchanged)
  - **projected**: `dist/apm/<pack>/.apm/skills/<skill>/scripts/` (the `make build-self` output)

  The projected variant uses `pytest.skip` when `dist/apm/` is absent or the specific skill path does not exist. Both variants must pass when built. Note: `dist/` is gitignored, so the projected variant always skips in CI unless `make build-self` runs first; AC13 (`make build-self FORCE=1`) must be run before AC15 (`pytest`) in the same gate pass to give the projected variant a non-absent `dist/apm/` to test against (see `plan.md` T4 ordering).

- [x] **AC12 (all existing tests pass):** All test cases that existed before this PR continue to pass. No existing test may be deleted or have its assertions weakened to satisfy this spec.

### Gates

- [x] **AC13:** `make build-self FORCE=1 && git status --short` shows no changes on the merged tree.
- [x] **AC14:** `python3 tools/hooks/pre-pr.py` exits 0.
- [x] **AC15:** `pytest packages/agentbundle/tests/ -x` exits 0 on the merged tree.
- [x] **AC16:** `python3 tools/test-lint-credentialed-skills.py` exits 0 on the merged tree.

## Boundaries

### Always do

- **New checks land with a failing fixture.** Each new D3 test case (AC2, AC3) must be verified to produce no finding under the old substring scan before showing the finding under the new AST walk. This asymmetry is the load-bearing proof that the bypass existed.
- **Path checks use `pathlib` parts, not substring matching.** The `_is_canonical_shim` path anchor uses `py.parent.name in {"scripts", "shared-libs"}` — a single-segment comparison via Python's standard attribute, not a string `in` substring check. This is consistent with `feedback_credentialed_lint_substring_trap`.
- **AST walk reuses `_path_chain_components()`.** Do not re-implement path chain resolution for D3; reuse the existing helper that already handles `BinOp(Add)` part-composition inside `BinOp(Div)` path chains.
- **Projected-path variants use `pytest.skip`, not `pytest.xfail`.** A missing projected copy is an expected state in an unbuilt checkout; `skip` is the correct disposition. `xfail` would imply the failure is a known bug.
- **`_load_cli_module` respects the no-synthesised-import convention.** Per `feedback_test_real_invocation_not_synthesised_import`, tests that exercise verb behaviour use real `subprocess.run` invocation (as in `test_credential_user_scope_invocation.py`). `_load_cli_module` using `importlib` is appropriate only for tests that inspect the module's namespace (attribute checks) rather than drive it as a CLI.

### Never do

- **No changes to production pack files.** The scope is test and lint hardening only. `packs/credential-brokers/.apm/`, `packs/*/skills/*/scripts/`, consumer skill `.py` files, `pack.toml` manifests, the canonical shim sources, and `sso-broker.py` are all out of scope.
- **No changes to `SHIM_BASENAMES` or `DOTFILE_PARENT`/`DOTFILE_BASENAME` constants.** The path anchor and AST walk use the existing named constants without widening them.
- **Do not delete or weaken the existing byte-equality check in `_is_canonical_shim`.** The path anchor is an additional narrowing requirement; the byte-equality check remains to prevent a file at a canonical-looking path but with different bytes from being treated as canonical.
- **No new third-party Python dependency** in `tools/lint_credentialed_skills.py` or in any new test file. The lint is stdlib-only (`ast`, `pathlib`); the tests use `pytest` and `unittest` (both already in dev dependencies).
- **No sign-and-verify at build time.** That approach requires a key-management surface that does not exist in this repo.

### Ask first

- Widening `SHIM_BASENAMES` to include new filenames.
- Adding a third canonical parent directory to the `_is_canonical_shim` path anchor.
- Extending the D3 AST walk to track dotfile paths across variable assignments.

## Testing Strategy

| Behaviour | Verification mode | Why this mode |
| --- | --- | --- |
| D3 AST walk catches part-composition bypass | TDD — write bypass fixture first, prove old scan misses it, then write AST walk that catches it | The bypass is only proved by running the old code against the fixture and observing silence |
| D3 AST walk catches `.read_bytes()` inline path | TDD — fixture + assertion | Same as above; different call form |
| D3 opt-out marker still suppresses findings | Regression — existing test case, no change needed | Existing test covers it; must continue to pass |
| `_is_canonical_shim` path anchor | Unit test — place canonical bytes at non-canonical parent, assert `False` | Pure function; deterministic over path position |
| `_is_canonical_shim` canonical paths remain exempt | Unit test — place canonical bytes at `scripts/` and `shared-libs/`, assert `True` | Regression pin on the positive case |
| `_load_cli_module` + SSO broker projected path | Integration — `pytest.skip` if absent, real file load if present | The projected file is real output of the build pipeline; load it as the real consumer does |
| User-scope invocation from projected path | Integration — `pytest.skip` if `dist/apm/` absent, subprocess invocation if present | Matches the `feedback_test_real_invocation_not_synthesised_import` convention |

## Assumptions

- **Python ≥ 3.11** on all CI platforms (source: `packages/agentbundle/pyproject.toml`).
- **`_path_chain_components()` resolves `BinOp(Add)` inside `BinOp(Div)` chains.** The existing helper calls `_literal_string()` on each right-hand side of the div chain; `_literal_string()` handles `BinOp(Add)` by recursion. This means `Path.home() / (".agent" + "bundle") / ("credentials" + ".env")` resolves to `(seed_kind="home", components=[".agentbundle", "credentials.env"])` — the AC2 bypass is provably caught.
- **`dist/apm/` is the `make build-self` output in this checkout.** The projected path parametrisation uses `REPO_ROOT / "dist" / "apm"` as the root for projected consumer skills.
- **`.agentbundle/bin/sso-broker.py` relative to `REPO_ROOT` is the local user-scope projection of the SSO broker.** This is confirmed by the presence of `pattaya-v2/.agentbundle/bin/sso-broker.py` in the working tree.
- **The opt-out marker suppression check works at the AST level via lineno lookup.** After finding a Call node at a given `lineno`, the implementation reads the corresponding line from the source text to check for `OPTOUT_MARKER`.
- **Two test roots exist.** Per `reference_agentbundle_two_test_roots`: `packages/agentbundle/tests/{unit,integration}/` and `packages/agentbundle/agentbundle/build/tests/`. The new tests go under `packages/agentbundle/tests/unit/`.

## Tasks

1. **D3: Rewrite dotfile-read check as AST walk** (`tools/lint_credentialed_skills.py`)
   - Implement `_check_dotfile_read(py_path) -> list[tuple[int, str]]` using `_path_chain_components()` to detect `open()`, `.read_text()`, and `.read_bytes()` calls on the dotfile path.
   - Replace the existing substring-scan block (lines 908–925) with a call to `_check_dotfile_read()`.
   - Handle opt-out marker by lineno lookup.
   - Construction tests: AC1, AC2 (bypass fixture), AC3 (read_bytes), AC4 (opt-out), AC5 (existing case).

2. **`_is_canonical_shim`: add path anchor** (`tools/lint_credentialed_skills.py`)
   - Add `py.parent.name not in {"scripts", "shared-libs"}` early-return guard in `_is_canonical_shim`.
   - Construction tests: AC7 (non-canonical path → `False`), AC8 (canonical paths under `scripts/` and `shared-libs/` → `True`).

3. **Integration: add `_load_cli_module()` and parametrise** (`packages/agentbundle/tests/unit/test_sso_broker_verbs.py`, `packages/agentbundle/tests/integration/test_credential_user_scope_invocation.py`)
   - Add `_load_cli_module(py_path)` helper (generalises `_load_broker_module`).
   - Parametrise `broker` fixture in `test_sso_broker_verbs.py` over source and projected SSO broker paths.
   - Add projected-path variant to `test_entry_point_imports_resolve_under_user_scope_layout` parametrisation.
   - Construction tests: AC9, AC10, AC11.

4. **Gate verification**: confirm AC13–AC16 pass on the merged tree.

## Declined

- **Cross-variable assignment tracking in D3.** The bypass `dotfile = Path.home() / ".agentbundle" / "credentials.env"; dotfile.read_text()` is not caught by the AST walk. Tracking assignments across statements would require dataflow analysis. Deferred until a concrete false-negative surfaces.

- **Keyword-arg `open(file=...)` form in D3.** `open(file=".agentbundle/credentials.env").read()` uses a keyword argument rather than a positional argument, so `node.args` is empty and the AST walk's `open()` branch (which reads `node.args[0]`) does not flag it. This form is out of scope — it is a second bypass pattern strictly simpler than the part-composition case this spec addresses. Deferred until a concrete false-negative surfaces.

- **Non-read sinks in D3 (shutil, subprocess).** The AST walk detects `open()` (builtin and pathlib), `.read_text()`, `.read_bytes()`, and `.open()` — the read family. A fallback substring scan inside `_check_dotfile_read` preserves old coverage for literal-path forms (`Path("~/.agentbundle/credentials.env").read_text()`, `open(os.path.expanduser("~/.agentbundle/credentials.env"))`) that `_path_chain_components` cannot resolve from the AST. Non-read sinks such as `shutil.copy(".agentbundle/credentials.env", ...)` or `subprocess.run(["cat", ".agentbundle/credentials.env"])` are categorically different; deferred until a concrete false-negative surfaces.

- **Sign-and-verify at build time for `_is_canonical_shim`.** Requires key-management infrastructure that doesn't exist in this repo. Path-anchoring (AC6) closes the immediate concern without new infrastructure.

- **Extending projected-path parametrisation to `test_sso_broker_verbs.py` in-process verb tests.** Adding projected-path parametrisation to the full verb test matrix would multiply test count significantly with redundant coverage. AC10 covers the load-from-projected-path case for the broker.
