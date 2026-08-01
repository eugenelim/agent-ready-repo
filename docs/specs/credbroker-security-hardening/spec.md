# Spec: credbroker-security-hardening

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** `credential-broker-contract` spec (round-4 security review, Concerns 1 and 4 deferred)

Mode: full (security boundary — credbroker test hardening)

> **Spec contract:** this document defines what "done" means. The implementing PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Close three deferred security-hardening items recorded in the `credential-broker-contract` spec's 2026-05-26 Changelog (round-4 security review, Concerns 1 and 4 — deferred by that PR, unblocked now):

**D3 — substring scan is bypassable.** The dotfile-read detection in the credentialed-skills lint (now at `packages/agentbundle/agentbundle/catalogue_tooling/lint.py`, function `_cs_check_dotfile_read`) originally used a line-by-line substring scan for `.agentbundle/credentials.env`. A consumer that constructs the path from concatenated string fragments — e.g. `(Path.home() / ("." + "agentbundle") / ("credentials" + ".env")).read_text()` — opens the dotfile without the literal substring `.agentbundle/credentials.env` ever appearing on any single source line. The fix rewrites D3 as an AST walk over `open()`, `.read_text()`, `.read_bytes()`, and `.open()` call sites alongside a retained fallback substring scan (defense-in-depth), using the existing `_cs_path_chain_components()` helper to reconstruct part-composed path chains before matching.

**`_cs_is_canonical_shim` — exemption is not path-anchored.** The current shim exemption (`_cs_is_canonical_shim`) grants bypass treatment to any file whose basename is in `_CS_SHIM_BASENAMES` and whose bytes match the canonical source. This means a file named `credentials_shim.py` at an arbitrary location in the repo tree (e.g. `packs/evil-pack/.apm/some-dir/credentials_shim.py`) would be exempt if it carries canonical bytes — even though the build pipeline never places files in such a location. The fix adds a path-anchor requirement: the file must reside inside a directory named `scripts` (consumer skill projection target) or `shared-libs` (canonical source directory) for the exemption to apply. Byte-equality is kept as a secondary check.

**`_load_cli_module()` — integration tests load from pack source only.** The SSO broker verb tests (`test_sso_broker_verbs.py`) load the broker exclusively from the pack source path. The user-scope invocation tests (`test_credential_user_scope_invocation.py`) stage consumer skills exclusively from the pack source. Neither test suite exercises the projected copies that `make build-self` emits (in `dist/apm/`) or that `agentbundle install` places in `~/.agentbundle/bin/`. The fix introduces a `_load_cli_module(path)` staging helper and parametrises affected tests over both the source path and the projected path, with `pytest.skip` when the projected copy is absent (unbuilt checkout).

## Acceptance Criteria

### D3: AST walk for dotfile-read detection

- [x] **AC1 (D3 — implementation):** The dotfile-read check in `packages/agentbundle/agentbundle/catalogue_tooling/lint.py` is implemented as an AST walk in `_cs_check_dotfile_read(py_path) -> list[tuple[int, str]]`. The walk visits every `ast.Call` node and raises a finding when: (a) the call is `open(<arg>)` (i.e. `func` is `ast.Name` with `id == "open"`) and the first positional argument resolves to the dotfile path; OR (b) the call is `<expr>.read_text(...)`, `<expr>.read_bytes(...)`, or `<expr>.open(...)` (i.e. `func` is `ast.Attribute` with `attr` in `{"read_text", "read_bytes", "open"}`) and the object expression `func.value` resolves to the dotfile path. A retained fallback substring scan for `_CS_DOTFILE_SUBSTRING` catches any plain-string dotfile reference not resolved by the AST walk (defense-in-depth). Path resolution uses the existing `_cs_path_chain_components()` helper; a finding is raised when the resolved components' last two entries match `(_CS_DOTFILE_PARENT, _CS_DOTFILE_BASENAME)` in order. The opt-out marker check is applied by reading the corresponding source line at the reported `lineno` and suppressing the finding when `_CS_OPTOUT_MARKER` appears on that line.

- [x] **AC2 (D3 — part-composition bypass caught):** A new test class `TestD3CheckDotfileRead` in `packages/agentbundle/tests/unit/test_credbroker_lint_hardening.py` includes a case `test_part_composition_bypass_caught` that writes a temporary fixture file using inline part-composition (fully inline in the method call, so `_cs_path_chain_components()` can resolve it):
  ```python
  (Path.home() / ("." + "agentbundle") / ("credentials" + ".env")).read_text()
  ```
  The test verifies: (a) that no substring `.agentbundle/credentials.env` appears in the fixture source (proving the old substring scan would miss it); and (b) `_cs_check_dotfile_read(fixture_file)` returns a non-empty findings list with the call's lineno and a description containing `"read_text"`. Note: `_cs_path_chain_components()` resolves inline `BinOp(Add)` string concatenation within `BinOp(Div)` path chains, but cannot resolve identifiers bound to intermediate variables — the fixture uses the fully-inline form.

- [x] **AC3 (D3 — `Path.read_bytes()` form caught):** The same test class includes `test_read_bytes_inline_caught` with a fixture using the inline `.read_bytes()` form:
  ```python
  (Path.home() / ".agentbundle" / "credentials.env").read_bytes()
  ```
  `_cs_check_dotfile_read` on the fixture returns a non-empty list with a description containing `"read_bytes"`. (The cross-variable-assignment form is explicitly Declined; this AC covers the inline form only.)

- [x] **AC4 (D3 — opt-out still works):** The same test class includes `test_optout_marker_suppresses_finding` with a fixture placing the opt-out marker on the same line as the `.read_text()` call:
  ```python
  (Path.home() / ".agentbundle" / "credentials.env").read_text()  # credentialed-primitive: reads-creds-directly
  ```
  `_cs_check_dotfile_read` on this fixture returns an empty list.

- [x] **AC5 (D3 — bare `open()` form caught):** The same test class includes `test_bare_open_caught` with a fixture using a bare `open()` call whose first positional argument is the relative string path `'.agentbundle/credentials.env'`:
  ```python
  data = open('.agentbundle/credentials.env').read()
  ```
  `_cs_check_dotfile_read` on this fixture returns a non-empty list. (The inner `open()` call is visited by `ast.walk`; `_cs_path_chain_components` resolves the string literal to `("relative", [".agentbundle", "credentials.env"])`; `_cs_is_dotfile_chain` returns True.)

### `_cs_is_canonical_shim`: path-anchor

- [x] **AC6 (`_cs_is_canonical_shim` — path anchor added):** `_cs_is_canonical_shim(py: pathlib.Path, shim_source_dir: pathlib.Path) -> bool` adds a path-anchor check before the byte-equality comparison: the function returns `False` immediately when `py.parent.name` is not in `{"scripts", "shared-libs"}`, even if the file's bytes match the canonical source. The anchor uses `py.parent.name` (a single path segment, not a substring match) per `feedback_credentialed_lint_substring_trap`. Note: `credentials_shim.py` also ships tracked at `.agentbundle/bin/credentials_shim.py` (parent `bin`), but the lint's scan roots (`packs/*/.apm/skills/*`, `.claude/skills/*`, `skills/*`) never reach `.agentbundle/bin/`, so `bin`-projected shims are intentionally outside the scanned set and are not affected by this anchor.

- [x] **AC7 (`_cs_is_canonical_shim` — non-canonical path not exempt):** A unit test in `packages/agentbundle/tests/unit/test_credbroker_lint_hardening.py` asserts that a copy of `credentials_shim.py` placed at a non-canonical parent directory (e.g. `some-pack/arbitrary/credentials_shim.py` where `parent.name == "arbitrary"`) returns `False` from `_cs_is_canonical_shim(path, shim_source_dir)` even when its bytes match the canonical source byte-for-byte.

- [x] **AC8 (`_cs_is_canonical_shim` — canonical paths remain exempt):** A unit test asserts that `credentials_shim.py` under a `scripts/` parent and under a `shared-libs/` parent (with matching canonical bytes and the correct `shim_source_dir`) each return `True` from `_cs_is_canonical_shim`.

### `_load_cli_module()`: parametrised integration tests

- [x] **AC9 (`_load_cli_module` helper added):** A helper `_load_cli_module(py_path: pathlib.Path) -> types.ModuleType` exists in both `packages/agentbundle/tests/unit/test_credbroker_lint_hardening.py` and `packages/credbroker/tests/unit/test_sso_broker_verbs.py`. The implementation loads the file via `importlib.util.spec_from_file_location` with the file's directory prepended to `sys.path` for the duration of the load.

- [x] **AC10 (SSO broker verb tests — source + projected parametrisation):** The `broker` fixture in `packages/credbroker/tests/unit/test_sso_broker_verbs.py` is parametrised over two paths via `params=["source", "projected"]`:
  - **source**: `packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py`
  - **projected**: `REPO_ROOT / ".agentbundle" / "bin" / "sso-broker.py"` (the `make build-self` output)

  The projected variant uses `pytest.skip(f"{path} not present — run make build-self")` when the file is absent.

- [x] **AC11 (user-scope invocation tests — source + projected parametrisation):** The `test_entry_point_imports_resolve_under_user_scope_layout` parametrisation in `packages/agentbundle/tests/integration/test_credential_user_scope_invocation.py` is parametrised over `variant in ["source", "projected"]`. The projected variant uses `pytest.skip` when `dist/apm/` is absent or the specific skill path does not exist.

- [x] **AC12 (all existing tests pass):** All test cases that existed before this PR continue to pass. No existing test may be deleted or have its assertions weakened to satisfy this spec.

### Gates

- [x] **AC13:** `make build-self FORCE=1 && git status --short` shows no changes on the merged tree.
- [x] **AC14:** `python3 tools/hooks/pre-pr.py` exits 0.
- [x] **AC15:** `pytest packages/agentbundle/tests/ -x` exits 0 on the merged tree.
- [x] **AC16:** `SKIP_SAST=1 make build-check` exits 0 on the merged tree (covers `agentbundle catalogue verify --root .`, the credentialed-skills lint, and all build gates). Note: replaces the original `python3 tools/test-lint-credentialed-skills.py` gate — that standalone script was deleted in commit 96232e62 (v0.13.0) when standalone linters were folded into the agentbundle CLI.

## Boundaries

### Always do

- **New D3 tests verify the bypass proof.** Each new D3 test (AC2) must include the assertion `".agentbundle/credentials.env" not in source` to prove the old substring scan would miss it.
- **Path checks use `pathlib` parts, not substring matching.** The `_cs_is_canonical_shim` path anchor uses `py.parent.name in {"scripts", "shared-libs"}` — a single-segment comparison via Python's standard attribute, not a string `in` substring check.
- **AST walk reuses `_cs_path_chain_components()`.** Do not re-implement path chain resolution for D3; reuse the existing helper that already handles `BinOp(Add)` part-composition inside `BinOp(Div)` path chains.
- **Projected-path variants use `pytest.skip`, not `pytest.xfail`.** A missing projected copy is an expected state in an unbuilt checkout.
- **`_load_cli_module` respects the no-synthesised-import convention.** Per `feedback_test_real_invocation_not_synthesised_import`, tests that exercise verb behaviour use real `subprocess.run` invocation. `_load_cli_module` using `importlib` is appropriate only for tests that inspect the module's namespace.

### Never do

- **No changes to production pack files.** The scope is test and lint hardening only.
- **No changes to `_CS_SHIM_BASENAMES` or `_CS_DOTFILE_PARENT`/`_CS_DOTFILE_BASENAME` constants.**
- **Do not delete or weaken the existing byte-equality check in `_cs_is_canonical_shim`.**
- **No new third-party Python dependency** in `catalogue_tooling/lint.py` or in any new test file.
- **No sign-and-verify at build time.**

### Ask first

- Widening `_CS_SHIM_BASENAMES` to include new filenames.
- Adding a third canonical parent directory to the `_cs_is_canonical_shim` path anchor.
- Extending the D3 AST walk to track dotfile paths across variable assignments.

## Testing Strategy

| Behaviour | Verification mode | Why this mode |
| --- | --- | --- |
| D3 AST walk catches part-composition bypass | Regression/characterization — fixture written after code shipped; AC2(a) assertion proves old scan misses it, AST walk catches it | `_cs_check_dotfile_read` shipped in origin/main before tests; tests pin bypass invariants after the fact |
| D3 AST walk catches `.read_bytes()` inline path | Regression/characterization — fixture + assertion | Same rationale; different call form |
| D3 opt-out marker suppresses findings | Unit test — inline fixture with marker on same line | Pure function; deterministic |
| D3 bare `open()` form caught | Unit test — inline fixture with string-literal path | `_cs_path_chain_components` resolves string literals |
| D3 fallback scan catches literal keyword-arg `open(file=...)` | Regression/characterization — `open(file="<literal>")` fixture asserts fallback "skill reads" description | AST branch cannot fire (no positional arg); fallback is the only net for the literal form |
| `_cs_is_canonical_shim` path anchor | Unit test — canonical bytes at non-canonical parent → False | Pure function; deterministic over path position |
| `_cs_is_canonical_shim` canonical paths remain exempt | Unit test — canonical bytes at `scripts/` and `shared-libs/` → True | Regression pin on the positive case |
| `_load_cli_module` + SSO broker projected path | Integration — `pytest.skip` if absent, real file load if present | The projected file is real output of the build pipeline |
| User-scope invocation from projected path | Integration — `pytest.skip` if `dist/apm/` absent, subprocess invocation if present | Matches the `feedback_test_real_invocation_not_synthesised_import` convention |

## Assumptions

- **Python ≥ 3.11** on all CI platforms (source: `packages/agentbundle/pyproject.toml`).
- **Lint code is in `packages/agentbundle/agentbundle/catalogue_tooling/lint.py`.** The standalone `tools/lint_credentialed_skills.py` and `tools/test-lint-credentialed-skills.py` were deleted in commit 96232e62 (v0.13.0, "fold standalone linters into CLI as catalogue subcommands"). All symbols use the `_cs_` prefix (e.g. `_cs_check_dotfile_read`, `_cs_is_canonical_shim`, `_cs_path_chain_components`, `_CS_DOTFILE_PARENT`, `_CS_DOTFILE_BASENAME`, `_CS_OPTOUT_MARKER`).
- **`_cs_path_chain_components()` resolves `BinOp(Add)` inside `BinOp(Div)` chains.** The helper calls `_cs_literal_string()` on each segment; `_cs_literal_string()` handles `BinOp(Add)` by recursion. This means `Path.home() / ("." + "agentbundle") / ("credentials" + ".env")` resolves to `("home", [".agentbundle", "credentials.env"])`.
- **`dist/apm/` is the `make build-self` output in this checkout.**
- **`.agentbundle/bin/sso-broker.py` relative to `REPO_ROOT` is the local user-scope projection of the SSO broker.**
- **The SSO broker verb tests live at `packages/credbroker/tests/unit/test_sso_broker_verbs.py`.** Not `packages/agentbundle/tests/unit/`.
- **Two test roots exist.** Per `reference_agentbundle_two_test_roots`: `packages/agentbundle/tests/{unit,integration}/` and `packages/agentbundle/agentbundle/build/tests/`. New D3 tests go under `packages/agentbundle/tests/unit/test_credbroker_lint_hardening.py`.

## Tasks

1. **D3: Add bypass-proof fixture tests** (`packages/agentbundle/tests/unit/test_credbroker_lint_hardening.py`)
   - Add `TestD3CheckDotfileRead` class with test cases for AC1 (fallback), AC2, AC3, AC4, AC5.
   - Each test writes a fixture Python file to `tmp_path`, calls `_cs_check_dotfile_read(fixture_file)`, and asserts expected findings.
   - AC2 requires the `".agentbundle/credentials.env" not in source` assertion.
   - AC1 (fallback) uses `open(file="<literal>")` to exercise the substring-scan fallback independently of the AST branch.

2. **Gate verification**: mark AC2–AC5 [x] (tests written and passing); confirm AC12–AC16 pass on the merged tree; set `Status: Shipped` after all reviewers return Clean.

*Note: AC1 implementation is shipped in origin/main; the AC1 fallback regression test was added in this PR. AC6–AC11 are implemented and passing in origin/main. Implementation work is tasks 1–2 only.*

## Declined

- **Cross-variable assignment tracking in D3.** The bypass `dotfile = Path.home() / ".agentbundle" / "credentials.env"; dotfile.read_text()` is not caught by the AST walk. Tracking assignments across statements would require dataflow analysis.

- **Keyword-arg `open(file=...)` with part-composed path in D3.** `open(file=".agentbundle/credentials.env").read()` uses a keyword argument rather than a positional argument; the AST branch misses it (requires `node.args`), but the literal `.agentbundle/credentials.env` substring on the line is still caught by the retained fallback scan. The genuine uncaught form is the keyword-arg combined with part-composed arguments — e.g. `open(file="." + "agentbundle/credentials.env")` — where neither the AST branch nor the fallback fires. Deferred until a concrete false-negative surfaces in a PR review.

- **Sign-and-verify at build time for `_cs_is_canonical_shim`.** Requires key-management infrastructure that doesn't exist in this repo.

- **Recreating `tools/test-lint-credentialed-skills.py`.** This standalone script was intentionally deleted in v0.13.0 when the credentialed-skills lint was folded into `agentbundle catalogue lint`. Recreating it would reintroduce the standalone structure the refactor removed and create a `tools/` script importing from `packages/agentbundle`. Tests go in the existing `packages/agentbundle/tests/unit/` tree.

- **`os.environ["HOME"]`/`os.getenv("HOME")` home seeds in D3.** `Path(os.environ["HOME"]) / ".agentbundle" / "credentials.env"` uses a home seed that `_cs_literal_string` returns `None` for, so `_cs_path_chain_components` resolves the chain to `(None, [])` and the AST branch never fires. Because the path components are joined with `/` operators (not a contiguous string literal), the fallback substring scan also misses it. Fixing this requires extending `_cs_path_chain_components` to recognise `os.environ[...]`/`os.getenv()`/`os.environ.get()` seeds as equivalent to `Path.home()` — deferred until a concrete false-negative surfaces in a PR review.
