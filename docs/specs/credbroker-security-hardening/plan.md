# Plan: credbroker-security-hardening

> This plan is the implementation strategy. The contract is [`spec.md`](spec.md).

## Approach

AC1, AC6–AC11 are already implemented and passing in origin/main (all three D3/shim/parametrisation fixes landed as part of the v0.13.0 CLI-fold and prior spec work). Remaining work is two sequential tasks:

- **T1** — Add `TestD3CheckDotfileRead` class to `packages/agentbundle/tests/unit/test_credbroker_lint_hardening.py` (AC2/AC3/AC4/AC5).
- **T2** — Run gate verification (AC13–AC16).

*Note on location: the standalone `tools/lint_credentialed_skills.py` and `tools/test-lint-credentialed-skills.py` were deleted in commit 96232e62 (v0.13.0). All lint logic is in `packages/agentbundle/agentbundle/catalogue_tooling/lint.py` under `_cs_`-prefixed symbols.*

## Design (LLD)

### D3 — `_cs_check_dotfile_read` (already shipped)

```python
# packages/agentbundle/agentbundle/catalogue_tooling/lint.py

def _cs_check_dotfile_read(py_path: Path) -> list[tuple[int, str]]:
    source = py_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines()
    results: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            if node.args:
                chain = _cs_path_chain_components(node.args[0])
                if _cs_is_dotfile_chain(chain):
                    lineno = node.lineno
                    if _CS_OPTOUT_MARKER not in lines[lineno - 1]:
                        results.append((lineno, "open() reads dotfile credentials"))
        elif (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {"read_text", "read_bytes", "open"}
        ):
            chain = _cs_path_chain_components(node.func.value)
            if _cs_is_dotfile_chain(chain):
                lineno = node.lineno
                if _CS_OPTOUT_MARKER not in lines[lineno - 1]:
                    results.append((lineno, f".{node.func.attr}() reads dotfile credentials"))
    # Fallback: substring scan for lines not already flagged (defense-in-depth).
    flagged_linenos = {lineno for lineno, _ in results}
    for i, line in enumerate(lines, start=1):
        if i in flagged_linenos:
            continue
        if _CS_DOTFILE_SUBSTRING in line and _CS_OPTOUT_MARKER not in line.rstrip():
            results.append((i, f"skill reads {_CS_DOTFILE_SUBSTRING} directly"))
    return results
```

### `_cs_is_canonical_shim` path anchor (already shipped)

```python
def _cs_is_canonical_shim(py: pathlib.Path, shim_source_dir: pathlib.Path) -> bool:
    if py.name not in _CS_SHIM_BASENAMES:
        return False
    if py.parent.name not in {"scripts", "shared-libs"}:  # path anchor
        return False
    expected_path = shim_source_dir / py.name
    try:
        expected = expected_path.read_bytes()
    except OSError:
        return False
    try:
        return py.read_bytes() == expected
    except OSError:
        return False
```

### `_load_cli_module` helper (already shipped)

```python
def _load_cli_module(py_path: pathlib.Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(py_path.stem, py_path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(py_path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(py_path.parent))
    return module
```

## Tasks

### T1 — Add D3 fixture tests to `test_credbroker_lint_hardening.py`

**Depends on:** none
**Mode:** Regression/characterization (AC2–AC5; `_cs_check_dotfile_read` already shipped in origin/main — tests pin bypass invariants after the fact)

Add `TestD3CheckDotfileRead` class to `packages/agentbundle/tests/unit/test_credbroker_lint_hardening.py`. Each test method writes a fixture file to `tmp_path` and calls `_cs_check_dotfile_read(fixture)` directly.

**Test cases:**
- `test_part_composition_bypass_caught` (AC2): fixture uses `("." + "agentbundle")` — assert (a) `".agentbundle/credentials.env" not in source` and (b) findings non-empty with `"read_text"` in description.
- `test_read_bytes_inline_caught` (AC3): `.read_bytes()` inline — assert findings non-empty with `"read_bytes"` in description.
- `test_optout_marker_suppresses_finding` (AC4): opt-out marker on same line — assert findings empty.
- `test_bare_open_caught` (AC5): `open('.agentbundle/credentials.env')` — assert findings non-empty with `"open() reads dotfile credentials"` in description (isolates AST `open()` branch from fallback substring scan).

**Verification:**
- `pytest packages/agentbundle/tests/unit/test_credbroker_lint_hardening.py -x` exits 0

### T2 — Gate verification

**Depends on:** T1
**Mode:** Goal-based (AC12–AC16)

Run all gates in order (AC13 must run before AC15 — `make build-self` produces the `dist/apm/` projected copies that AC11's projected variant checks):

0. Mark AC2–AC5 `[x]` in `spec.md` (tests exist and pass).
1. `make build-self FORCE=1` → exits 0
2. `git status --short` → shows no changes (AC13)
3. `python3 tools/hooks/pre-pr.py` → exits 0 (AC14)
4. `pytest packages/agentbundle/tests/ -x` → exits 0 (AC12, AC15)
5. `SKIP_SAST=1 make build-check` → exits 0 (AC16; covers `agentbundle catalogue verify --root .` and all build gates)
6. Set `Status: Shipped` in `spec.md` after all reviewers return Clean (done at REVIEW, not here).

## Changelog

- 2026-07-23: Initial plan authored.
- 2026-07-31: Plan reconciled with corrected spec after v0.13.0 (96232e62) folded standalone linters into agentbundle CLI. AC1/AC6–AC11 confirmed shipped; remaining work scoped to T1 (D3 fixture tests) + T2 (gates). All `_cs_` prefixes and correct file paths applied; LLD updated to match shipped implementation; AC16 gate updated from deleted `tools/test-lint-credentialed-skills.py` to `SKIP_SAST=1 make build-check`.
- 2026-08-01: Work-loop completed. Added AC1-fallback test (keyword-arg open(file=...) form caught by substring scan), narrowed Declined keyword-arg item to the part-composed-path gap, added os.environ["HOME"] bypass to Declined, fixed Testing Strategy to Regression/characterization, asserted AC2 line number per spec. Status → Shipped.
