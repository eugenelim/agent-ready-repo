# Plan: unify-path-jail-projection-probe

> This plan is the implementation strategy. The contract is [`spec.md`](spec.md).

## Approach

Three tasks in dependency order. T1 adds the new helper and its unit tests. T2 migrates `install.py` and `upgrade.py` dry-run. T3 adds upgrade non-dry-run pre-flight and routes `write_jailed`'s inline block. All existing regression tests must pass without modification after each task.

**Red stubs:** Before EXECUTE, create the five unit test functions for `assert_projection_jailed` in `tests/unit/test_safety.py`. Each should fail `AttributeError` (function doesn't exist yet) until T1 is complete.

## Design (LLD)

### `assert_projection_jailed` signature

```python
def assert_projection_jailed(
    root: Path,
    relpaths: Iterable[str],
    allowed_prefixes: list[str] | None,
    *,
    command: str,
) -> None:
    """Raise PathJailError if any relpath escapes root or violates allowed_prefixes.

    When allowed_prefixes is None, only root-escape is checked.
    root must be an absolute resolved Path.
    """
    for relpath in relpaths:
        target = root / relpath
        try:
            assert_under(root, target)
        except PathJailError as exc:
            raise PathJailError(f"{command}: {exc}") from exc
        if allowed_prefixes is not None:
            target_relpath = target.resolve().relative_to(root.resolve()).as_posix()
            if not any(
                target_relpath.startswith(p)
                for p in allowed_prefixes
            ):
                raise PathJailError(
                    f"{command}: path {relpath!r} is not within any declared prefix zone"
                )
```

Pure function — no I/O, no side effects. Placed immediately after `assert_under` in `safety.py`.

### Migration shape per call site

**`install.py` Step 8** — Replace the `for plan in plans: for relpath in projection.keys(): assert_under(...); if allowed_prefixes: ...` double loop with:
```python
for plan in plans:
    projection = ...
    if projection is None:
        continue
    try:
        safety.assert_projection_jailed(
            plan.root, projection.keys(), plan.allowed_prefixes, command="install"
        )
    except safety.PathJailError as exc:
        print(str(exc), file=sys.stderr)
        return 1
```

**`upgrade.py` dry-run probe** — Replace the `for relpath in sorted(work_projection): ...` probe block with:
```python
try:
    safety.assert_projection_jailed(
        root, sorted(work_projection), allowed_prefixes, command="upgrade"
    )
except safety.PathJailError as exc:
    print(str(exc), file=sys.stderr)
    return 1
```

**`upgrade.py` non-dry-run pre-flight (new)** — Insert before write loop:
```python
try:
    safety.assert_projection_jailed(
        root, sorted(work_projection), allowed_prefixes, command="upgrade"
    )
except safety.PathJailError as exc:
    print(str(exc), file=sys.stderr)
    return 1
for relpath, content in sorted(work_projection.items()):
    ...
```

**`write_jailed` prefix block** — Replace lines 342–347 with:
```python
assert_projection_jailed(root, [relpath], allowed_prefixes, command=f"scope={scope}")
```
The trailing-slash guard at lines 337–341 remains before this call.

## Tasks

### T1 — Extract `assert_projection_jailed` + unit tests

**Depends on:** none
**Mode:** TDD (AC1, AC6)

Write red stubs first (5 named test functions in `tests/unit/test_safety.py`). Then implement the helper.

**Verification:**
- `pytest tests/unit/test_safety.py::test_assert_projection_jailed_*` — all 5 cases pass (AC6)
- `grep -n "def assert_projection_jailed" safety.py` returns a match (AC1)

### T2 — Migrate `install.py` Step 8 + `upgrade.py` dry-run probe

**Depends on:** T1
**Mode:** Goal-based regression (AC2, AC3)

Apply both migrations. Run the two existing integration tests.

**Verification:**
- `pytest tests/integration/test_install_cmd.py::test_path_jail_probe_refused` passes (AC2)
- `pytest tests/integration/test_upgrade_cmd.py::test_dry_run_upgrade_preflight_path_jail_passthrough` passes (AC3)
- `python -c "s=open('agentbundle/commands/install.py').read(); step8=s[s.find('# ── Step 8'):s.find('# ── Step 9')]; bad=[l for l in step8.splitlines() if 'assert_under(' in l and not l.strip().startswith('#')]; assert step8 and not bad, f'Step 8 still calls assert_under inline (or delimiter not found): {bad}'"` exits 0
- `python -c "lines=[l for l in open('agentbundle/commands/upgrade.py').read().splitlines() if 'assert_under(' in l and not l.strip().startswith('#')]; assert not lines, f'upgrade.py still calls assert_under inline: {lines}'"` exits 0 (confirms dry-run probe also migrated)

### T3 — Add upgrade non-dry-run pre-flight + route `write_jailed`

**Depends on:** T1, T2
**Mode:** TDD for AC4 (new integration test); goal-based for AC5/AC7

Write the new integration test for AC4 first. Then add the pre-flight call and route `write_jailed`.

**Verification:**
- New integration test (AC4): `pytest tests/integration/test_upgrade_cmd.py::test_upgrade_prefix_violation_writes_nothing` passes
- `pytest tests/unit/test_safety_repo_scope_prefixes.py` — all cases pass (AC5, AC7)
- `python -c "import re; s=open('agentbundle/safety.py').read(); m=re.search(r'def write_jailed\b.*?(?=\ndef \w)', s, re.S); assert m and 'target_relpath' not in m.group(), 'write_jailed body still has inline target_relpath'"` exits 0

### T4 — Full regression

**Depends on:** T1, T2, T3
**Mode:** Goal-based (AC5)

`pytest packages/agentbundle/` — all tests pass. No modified assertions.

## Changelog

- 2026-07-23: Initial plan authored.
