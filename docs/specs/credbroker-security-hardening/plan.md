# Plan: credbroker-security-hardening

> This plan is the implementation strategy. The contract is [`spec.md`](spec.md).

## Approach

Three tasks that can run in parallel (D3 AST walk, shim path anchor, and test parametrisation have no shared edits). T4 runs final gates after all three are done. D3 has the highest security impact and the most verification overhead (TDD with bypass-proof fixtures). The shim path anchor is a pure function guard with two unit tests. The test parametrisation is purely additive.

## Design (LLD)

### D3: `_check_dotfile_read`

```python
def _check_dotfile_read(py_path: Path) -> list[tuple[int, str]]:
    """Walk AST, return (lineno, desc) for each dotfile-read call site."""
    source = py_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    lines = source.splitlines()
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            if node.args:
                arg = node.args[0]
                result = _path_chain_components(arg)
                if result and _is_dotfile_chain(result):
                    lineno = node.lineno
                    if OPTOUT_MARKER not in lines[lineno - 1]:
                        findings.append((lineno, "open() reads dotfile credentials"))
        elif isinstance(node.func, ast.Attribute) and node.func.attr in {"read_text", "read_bytes"}:
            result = _path_chain_components(node.func.value)
            if result and _is_dotfile_chain(result):
                lineno = node.lineno
                if OPTOUT_MARKER not in lines[lineno - 1]:
                    findings.append((lineno, f".{node.func.attr}() reads dotfile credentials"))
    return findings

def _is_dotfile_chain(result) -> bool:
    _, components = result
    return (len(components) >= 2
            and components[-2] == DOTFILE_PARENT
            and components[-1] == DOTFILE_BASENAME)
```

Replace the substring-scan block (lines 908–925) in `lint_credentialed_skills.py` with a call to `_check_dotfile_read(py_path)`.

### `_is_canonical_shim` path anchor

```python
def _is_canonical_shim(py: pathlib.Path) -> bool:
    if py.parent.name not in {"scripts", "shared-libs"}:  # ADD FIRST
        return False
    # ... existing byte-equality check ...
```

### `_load_cli_module` helper

```python
def _load_cli_module(py_path: pathlib.Path) -> types.ModuleType:
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location("_loaded_module", py_path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(py_path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module
```

## Tasks

### T1 — Rewrite D3 dotfile-read check as AST walk

**Depends on:** none
**Mode:** TDD (AC1–AC5)

Write TDD fixtures first:
- Fixture for AC2: inline part-composition `(Path.home() / ("." + "agentbundle") / ("credentials" + ".env")).read_text()` — verify it has no literal `.agentbundle/credentials.env` substring (AC2(a)), then confirm AST walk catches it.
- Fixture for AC3: inline `.read_bytes()` form `(Path.home() / ".agentbundle" / "credentials.env").read_bytes()`.

Then implement `_check_dotfile_read()` and `_is_dotfile_chain()`. Replace the substring-scan block with the AST walk.

**Verification:**
- `python3 tools/test-lint-credentialed-skills.py` exits 0 (AC1, AC4, AC5 regression)
- New test cases for AC2 (bypass fixture) and AC3 (read_bytes) pass
- `assert ".agentbundle/credentials.env" not in ac2_fixture_source` (AC2(a) inline assertion)

### T2 — Add `_is_canonical_shim` path anchor

**Depends on:** none (parallel with T1)
**Mode:** Unit/TDD (AC6, AC7, AC8)

Add `py.parent.name not in {"scripts", "shared-libs"}` early-return to `_is_canonical_shim`.

**Verification:**
- Unit test: canonical bytes at `arbitrary/credentials_shim.py` → `False` (AC7)
- Unit test: canonical bytes at `scripts/credentials_shim.py` → `True` (AC8a)
- Unit test: canonical bytes at `shared-libs/credentials_shim.py` → `True` (AC8b)
- `python3 tools/test-lint-credentialed-skills.py` exits 0 (AC6/AC8 regression)

### T3 — Add `_load_cli_module()` and parametrise integration tests

**Depends on:** none (parallel with T1/T2)
**Mode:** Integration (AC9, AC10, AC11)

Add `_load_cli_module()` helper. Parametrise `broker` fixture in `test_sso_broker_verbs.py` over source + projected paths. Add projected-path variant to `test_entry_point_imports_resolve_under_user_scope_layout`.

**Verification:**
- `pytest packages/agentbundle/tests/unit/test_sso_broker_verbs.py` passes (AC10)
- `pytest packages/agentbundle/tests/integration/test_credential_user_scope_invocation.py` passes (AC11)
- If `dist/apm/` absent, projected variants report skip (not error)

### T4 — Gate verification

**Depends on:** T1, T2, T3
**Mode:** Goal-based (AC12–AC16)

Run all gates in order (AC13 must run before AC15 — `make build-self` produces the `dist/apm/` projected copies that AC11's projected variant checks; without it, AC11's projected parametrisation will always skip):
1. `make build-self FORCE=1` → exits 0 (AC13 prerequisite for projected test variants)
2. `git status --short` → shows no changes (AC13)
3. `python3 tools/hooks/pre-pr.py` → exits 0 (AC14)
4. `pytest packages/agentbundle/tests/ -x` → exits 0 (AC15; projected variants now have build output to test against)
5. `python3 tools/test-lint-credentialed-skills.py` → exits 0 (AC16)

## Changelog

- 2026-07-23: Initial plan authored.
