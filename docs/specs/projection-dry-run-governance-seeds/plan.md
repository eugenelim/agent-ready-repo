# Plan: projection-dry-run-governance-seeds

> This plan is the implementation strategy. The contract is [`spec.md`](spec.md).

## Approach

Two tasks in strict TDD order. T1 extracts `_classify_seeds` as a pure function and refactors `deliver_seeds` to call it. T2 adds seed preview to `install --dry-run`. T2 depends on T1; both are TDD tasks with compilable red stubs materialized before EXECUTE begins.

**Red stubs:** Before EXECUTE begins, create:
- `packages/agentbundle/tests/unit/test_common_classify_seeds.py` — stub with five test functions (`test_classify_seeds_absent`, `test_classify_seeds_identical`, `test_classify_seeds_differs`, `test_classify_seeds_agents_md_composition`, `test_classify_seeds_footer_excluded`, plus `test_classify_seeds_symlink_file_skipped`, `test_classify_seeds_symlink_dir_skipped`, `test_classify_seeds_no_write_invariant`). All should fail `ImportError` until T1 is complete.
- Extend `packages/agentbundle/tests/integration/test_install_cmd.py` with three stub cases: `test_dry_run_includes_seed_create_lines`, `test_dry_run_seed_companion_line`, `test_dry_run_writes_nothing_including_seeds`. Should fail with `AssertionError` until T2 is complete.

## Design (LLD)

### `_classify_seeds` signature

```python
def _classify_seeds(seeds_dir: Path, root: Path) -> list[SeedDelivery]:
    """Classify seeds without writing — same walk logic as deliver_seeds but read-only."""
```

Walk `seeds_dir` with `os.walk(followlinks=False)` (symlink-skip security invariant). For each seed file:
- Skip `_agents-footer.md` (composition fragment, not delivered as a seed)
- Skip symlinks (`Path.is_symlink()` check)
- Compose `AGENTS.md` bytes from body + footer fragment when `_agents-footer.md` is present
- Read `root / relpath` if it exists; compare bytes
- Return `SeedDelivery(relpath=relpath, action="wrote"|"skipped"|"companion", companion_relpath=...)`

No filesystem writes. No calls to `write_jailed`, `write_companion`, or `deliver_seeds`.

### `deliver_seeds` refactor

```python
def deliver_seeds(seeds_dir: Path, output: Path, ...) -> list[SeedDelivery]:
    records = _classify_seeds(seeds_dir, output)
    for record in records:
        if record.action == "wrote":
            write_jailed(...)
        elif record.action == "companion":
            write_companion(...)
        # "skipped" → no-op
    return records  # full list including "skipped" records
```

Return the full list so callers (e.g. `install.py` state recorder) can record all seeds including byte-identical ones.

### `install --dry-run` seed preview

In `install.run`'s dry-run branch (around line 929), after the existing projection plan lines are emitted, add:

```python
if plan.scope == "repo" and seeds_dir.is_dir():
    for record in _classify_seeds(seeds_dir, plan.root):
        if record.action == "skipped":
            continue
        verb = "create" if record.action == "wrote" else "companion"
        tier = "tier-1" if record.action == "wrote" else "tier-2"
        path_str = record.relpath if record.action == "wrote" else f"{record.relpath} -> {record.companion_relpath}"
        print(format_plan_line(verb, tier, path_str))
        actions.append(verb)
```

The `summarize_plan` count at the end already uses `actions`; seed entries naturally add to the count (AC4).

## Tasks

### T1 — Extract `_classify_seeds` and refactor `deliver_seeds`

**Depends on:** none
**Mode:** TDD (AC7, AC9)

Write red stubs (see above) first. Then implement:
- Add `_classify_seeds(seeds_dir: Path, root: Path) -> list[SeedDelivery]` above `deliver_seeds` in `_common.py`
- Refactor `deliver_seeds` to call `_classify_seeds(seeds_dir, output)` and drive writes from returned list; return full list to caller
- Ensure `deliver_seeds` continues to record `"skipped"` records in state (AC9)

**Done when:**
- `test_common_classify_seeds.py` passes (8 cases: all three action types, AGENTS.md composition, footer exclusion, symlink-file skip, symlink-dir skip, no-write invariant)
- `test_install_seed_delivery.py` passes unchanged (AC6 regression)
- `test_scaffold_cmd.py` passes unchanged (AC6 regression — symlink-skip invariant)
- `test_install_identical_seed_skipped` (or equivalent) asserts skipped seed is still recorded in state (AC9)

### T2 — Extend `install --dry-run` to preview seeds

**Depends on:** T1
**Mode:** TDD (AC3, AC4, AC5, AC8)

Write red stubs first. Then add seed preview to dry-run branch in `install.py`, guarded by `plan.scope == "repo"` and `seeds_dir.is_dir()`.

**Done when:**
- `test_dry_run_includes_seed_create_lines` passes: fresh install dry-run stdout contains `AGENTS.md`, `docs/CHARTER.md`, `docs/CONVENTIONS.md` as `create tier-1` lines
- `test_dry_run_seed_companion_line` passes: user-edited seed shows `companion tier-2 ... -> ...` line; no companion written to disk
- `test_dry_run_writes_nothing_including_seeds` passes: tree is byte-identical before and after dry-run
- All existing dry-run tests in `test_install_cmd.py` pass unchanged (AC6)

## Changelog

- 2026-07-23: Initial plan authored (tasks extracted from spec.md).
