# Plan: share-scope-state-path-resolver

- **Spec:** [`spec.md`](spec.md)
- **Status:** Draft

## Approach

Three small steps in strict TDD order. First, write the unit test for the
not-yet-existing `resolve_state_path` helper (red). Second, add the helper to
`_common.py` (green). Third, migrate the three call sites one file at a time,
running the full test suite after each migration to confirm parity.

The total diff: one new function (3 lines of body), one new test file (≤25
lines), and three command files with their inline path formulas replaced by a
single `resolve_state_path(scope, root)` call.

## Constraints

- `_common.py` is stdlib-only. `resolve_state_path` uses `pathlib.Path` (already
  imported).
- The path formulas (`".agentbundle-state.toml"` and `".agentbundle/state.toml"`)
  must not change — these are the persisted on-disk layout.
- No test assertion may change — the existing test suite is the regression baseline.

## Design (LLD)

### `resolve_state_path` signature

```python
def resolve_state_path(scope: str, root: Path) -> Path:
    """Return the state-file Path for *scope* rooted at *root*.

    ``scope == "repo"`` → ``root / ".agentbundle-state.toml"``;
    ``scope == "user"`` → ``root / ".agentbundle" / "state.toml"``.
    ``root`` must be the already-resolved scope root (absolute Path).
    """
    if scope == "user":
        return root / ".agentbundle" / "state.toml"
    return root / ".agentbundle-state.toml"
```

Pure, total function — no I/O, no exceptions.

### Duplicated code locations (confirmed by reading source)

`uninstall.py`:
- Line 54: `state_path = root / ".agentbundle-state.toml"` — repo formula
- Line 75: `user_state_path = user_root / ".agentbundle" / "state.toml"` — user formula

`upgrade.py`:
- Line 118: `repo_state_path = root / ".agentbundle-state.toml"` — repo formula
- Lines 131–133: `user_state_path = user_root_resolved / ".agentbundle" / "state.toml"` — user formula
- Lines 247–251: `state_path = root / ".agentbundle-state.toml"` in the `else` branch — repo formula (third occurrence)

`diff.py`:
- Line 60: `root / ".agentbundle-state.toml"` inline in `load_state()` call — repo formula
- Lines 67–68: `user_root_resolved / ".agentbundle" / "state.toml"` inline in `load_state()` call — user formula

## Tasks

### T1 — Unit test for `resolve_state_path` (red)

**Depends on:** none
**Verification:** TDD (AC4)
**Stub:** `packages/agentbundle/tests/unit/test_resolve_state_path.py` (materialized — fails ImportError until T2 adds the function)

Write `packages/agentbundle/tests/unit/test_resolve_state_path.py`:
- `resolve_state_path("repo", Path("/repo"))` → `Path("/repo/.agentbundle-state.toml")`
- `resolve_state_path("user", Path("/home/alice"))` → `Path("/home/alice/.agentbundle/state.toml")`

Run: must fail ImportError (function doesn't exist yet).

---

### T2 — Add `resolve_state_path` to `_common.py` (green)

**Depends on:** T1
**Verification:** goal-based (AC1, AC5)

Add the function after the existing imports block. Run T1: must pass green.
Verify: `grep -n "^import\|^from" _common.py` shows no new lines (AC5).

---

### T3 — Migrate `uninstall.py`

**Depends on:** T2

- Add a **function-local** `from agentbundle.commands._common import resolve_state_path` inside `run()` in `uninstall.py`. The existing `_common` imports at lines 144/244/262 are function-local to *other* functions; do not rely on module-level placement, as `uninstall.py` uses deliberate lazy imports for fast `--version` startup. The new import is inside `run()` alongside the existing scope-inference logic.
- Line 54: `state_path = resolve_state_path("repo", root)`
- Line 75: `user_state_path = resolve_state_path("user", user_root)`
- Run: `pytest packages/agentbundle/tests/` focusing on uninstall tests. Must pass unchanged (AC3).
- Verify (AC2): `grep -n '^\s*\S' uninstall.py | grep -v '^\s*#' | grep '/ "\.\(agentbundle-state\.toml\|agentbundle\)"'` → no hits.

---

### T4 — Migrate `upgrade.py`

**Depends on:** T2

- Add `resolve_state_path` to imports.
- Line 118: `repo_state_path = resolve_state_path("repo", root)`
- Lines 131–133: `user_state_path = resolve_state_path("user", user_root_resolved)`
- Lines 247–251 `else` branch: `state_path = resolve_state_path("repo", root)`
- Run upgrade tests. Must pass unchanged (AC3).
- Verify (AC2): `grep -n '^\s*\S' upgrade.py | grep -v '^\s*#' | grep '/ "\.\(agentbundle-state\.toml\|agentbundle\)"'` → no hits on path-build lines; the `state_relpath == ".agentbundle-state.toml"` comparison at line 724 is the expected carve-out and must still be present.

---

### T5 — Migrate `diff.py`

**Depends on:** T2

- Add `resolve_state_path` to existing `_common` import.
- Line 60: `load_state(resolve_state_path("repo", root), ...)`
- Lines 67–68: `load_state(resolve_state_path("user", user_root_resolved), ...)`
- Run diff tests. Must pass unchanged (AC3).
- Verify (AC2): `grep -n '^\s*\S' diff.py | grep -v '^\s*#' | grep '/ "\.\(agentbundle-state\.toml\|agentbundle\)"'` → no hits.

---

### T6 — Full regression pass

**Depends on:** T3, T4, T5

`pytest packages/agentbundle/` green, all pre-existing tests pass (AC3).
For each of `uninstall.py`, `upgrade.py`, `diff.py`: verify no non-comment path-build
expressions match `/ "\.agentbundle` (excluding `#`-prefixed lines). The `state_relpath == ".agentbundle-state.toml"` comparison in `upgrade.py` is expected and does not fail this check (AC2 exception).
