# Plan: workspace-status simplification — Order 2B

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files touched:**
- `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` — new dataclasses + `compute_repair_plan`
- `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` — new subcommand routing + write logic (tomlkit)
- `packs/core/.apm/skills/workspace-status/SKILL.md` — §1a table update + repair guidance
- `tools/test_workspace_status.py` — engine unit tests for `compute_repair_plan`
- `tools/test_workspace_status_cli.py` — CLI tests for `repair-plan`, `repair-apply`; `_STDLIB_MODULES` extension
- `.gitignore` — add `.workspace-repair-plan.json` and `.workspace.toml.*.tmp`

**Tests demonstrate "done":**
- `test_compute_repair_plan_queue_shipped` → automatic `queue-to-shipped` operation generated
- `test_compute_repair_plan_queue_archived` → automatic `queue-remove` operation generated
- `test_compute_repair_plan_active_source_is_manual` → active-source finding in manual list
- `test_compute_repair_plan_type1_and_type3_manual` → Type 1 and Type 3 in manual list
- `test_compute_repair_plan_approved_not_eligible` → Approved in queue is not an automatic operation
- `test_repair_plan_cli_json_contract` → stdout JSON has all required fields
- `test_repair_apply_queue_to_shipped` → workspace.toml updated correctly; entry removed from queue, appended to shipped
- `test_repair_apply_queue_remove` → archived entry removed from queue; nothing added to shipped
- `test_repair_apply_fingerprint_mismatch` → exits 2, `applied: false`, `reason: fingerprint_mismatch`
- `test_repair_apply_plan_not_found` → exits 2, `reason: plan_file_not_found`
- `test_repair_apply_no_writes` → repair-plan does not modify workspace.toml

**Not changing:**
- `status` / `explain` / `reconcile` subcommand behavior (no production change)
- `compute_type2_cleanup` function (existing SKILL.md cleanup-offer path unchanged)
- Any workspace.toml schema
- work-loop behavior
- Existing test assertions

**Declined temptations:**
- Implement `work.active` automatic removal — prohibited by architectural boundary; Order 2B cannot distinguish live work-loops from stale entries.
- Add POSIX file locking to `repair-apply` — adds complexity and cross-platform risk; fingerprint + spec-status re-verification provides sufficient staleness protection for the single-user CLI use case.
- Implement generic "repair anything" framework — scope creep; Order 3A/3B will redesign lifecycle ownership.
- Add `repair-plan` / `repair-apply` as engine entry points — they are CLI-level operations; the engine stays narrow.
- Use a fixed-name temp file — enables symlink-follow attack and concurrent write collision; use `tempfile.mkstemp` instead.

## Constraints

- Engine (`workspace_status_engine.py`) must remain stdlib-only.
- tomlkit import is CLI-only (workspace_status.py write path only).
- `os.replace()` for atomic write on all platforms.
- No `shell=True` in any subprocess call.

## Risks

| Risk | Mitigation |
|---|---|
| tomlkit fails to round-trip workspace.toml inline objects or multiline arrays | Test with a fixture that mirrors the real workspace.toml structure before implementation |
| Fingerprint not portable (file encoding differences across platforms) | Use bytes-level SHA-256 of raw `workspace.toml` read with `open('rb')`; never decode |
| `os.replace()` not atomic on Windows if target is open | Document; acceptable for this use case (single-user CLI) |
| `repair-apply` removes inline-object queue entry by finding the wrong match | Match on `path` field value, not line position; test with inline objects alongside bare strings |

## Prerequisite gate evidence

Verified before implementation — see spec.md §"Prerequisite gate evidence".

## Tasks

### T1: Engine — dataclasses and `compute_repair_plan`

- **Files:** `workspace_status_engine.py`
- **Verification mode:** TDD
- **Tests:**
  - `test_compute_repair_plan_queue_shipped` — Type 2 queue Shipped → `operation_type="queue-to-shipped"`, `spec_status="Shipped"` (pin both fields)
  - `test_compute_repair_plan_queue_archived` — Type 2 queue Archived → `operation_type="queue-remove"`, `spec_status="Archived"` (pin both fields)
  - `test_compute_repair_plan_active_source_is_manual` — Type 2 active → manual finding, `reason="type2-active-source"`
  - `test_compute_repair_plan_type1_manual` — Type 1 → manual finding, `reason="type1-untracked"`
  - `test_compute_repair_plan_type3_manual` — Type 3 → manual finding, `reason="type3-premature"`
  - `test_compute_repair_plan_approved_not_eligible` — Approved in queue → NOT in automatic_operations (Type 2 scan emits Shipped/Archived only, so this tests the defensive path for future-proofing)
  - `test_compute_repair_plan_path_in_queue_and_active` — same path in queue+active both Shipped → one RepairOperation (queue) + one ManualFinding (active-source); not collapsed
  - `test_compute_repair_plan_duplicate_path_in_queue` — same spec_path appears twice in Type 2 queue findings for same ini → both route to manual_findings with `reason="type2-queue-duplicate"`; NOT in automatic_operations
  - `test_compute_repair_plan_fingerprint_is_sha256` — fingerprint matches `hashlib.sha256(workspace_path.read_bytes()).hexdigest()`
  - `test_compute_repair_plan_planned_at_is_utc_isoformat` — `planned_at` ends with `"+00:00"` (not "Z"); `datetime.fromisoformat(planned_at).utcoffset() == datetime.timedelta(0)`
  - `test_compute_repair_plan_empty_reconciliation` — zero findings → empty automatic_operations, empty manual_findings
- **Approach:**
  1. Add `RepairOperation`, `ManualFinding`, `RepairPlan` dataclasses after `ReconciliationFinding`.
  2. Add `compute_repair_plan(result: WorkspaceStatusResult, workspace_path: Path) -> RepairPlan`:
     - build `duplicate_paths`: set of spec_path values that appear >1 time in Type 2 queue findings for the same ini_slug
     - iterate `result.type2`:
       - if duplicate → manual (reason=type2-queue-duplicate)
       - elif `list_name == "queue"` and `spec_status in ("Shipped", "Archived")` → automatic operation
       - else → manual (reason=type2-active-source or type2-queue-{status})
     - iterate `result.type1` → manual (reason=type1-untracked)
     - iterate `result.type3` → manual (reason=type3-premature)
     - fingerprint: `hashlib.sha256(workspace_path.read_bytes()).hexdigest()`
     - `planned_at`: `datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")`
  3. Export in module docstring entry point list.
  4. Add `hashlib`, `datetime` imports (stdlib only).

### T2: CLI — `repair-plan` subcommand

- **Files:** `workspace_status.py`
- **Verification mode:** TDD + Visual/manual QA
- **Tests:**
  - `test_repair_plan_json_contract` — stdout has schema_version, mode, workspace_present, workspace_root, workspace_fingerprint, planned_at, automatic_operations, manual_findings
  - `test_repair_plan_uses_full_reconcile` — `scan.global_spec_scan_performed: true`; `reconciliation.types_performed: [1, 2, 3]`
  - `test_repair_plan_writes_plan_file` — default plan file exists after invocation; contains valid JSON matching stdout
  - `test_repair_plan_custom_plan_file` — `--plan-file` path written
  - `test_repair_plan_empty_automatic_ops_exits_0` — exit 0 with empty automatic_operations; plan file still written
  - `test_repair_plan_absent_workspace_exits_1` — workspace absent → exit 1, mode=repair-plan in JSON
  - `test_repair_plan_no_writes_to_workspace_toml` — workspace.toml SHA-256 unchanged after repair-plan run
  - `test_repair_plan_stdout_emitted_on_plan_file_write_failure` — `--plan-file` pointing at unwritable path → stdout still valid JSON; exit 2
  - `test_repair_plan_plan_file_confinement` — `--plan-file` resolving outside root via symlink → exit 2, `reason="plan_file_outside_root"`
  - `test_repair_plan_plan_file_confinement_direct_path` — `--plan-file ../../evil.json` (no symlink) → exit 2, `reason="plan_file_outside_root"`
- **Approach:**
  1. Add `"repair-plan"` to `_SUBCOMMANDS`.
  2. Add `--plan-file` optional argument (available to both repair-plan and repair-apply).
  3. Load `compute_repair_plan` and `extract_spec_status` from the engine module at import time (add alongside the existing `analyze`, `analyze_bounded`, `explain_item`, `compute_type2_cleanup` bindings in the engine-load block).
  4. Implement `_build_repair_plan_json(root, result, plan)` — merges `_build_json(root, result, "repair-plan")` with plan fields; convert `RepairOperation` and `ManualFinding` dataclasses to dicts via `dataclasses.asdict()` before JSON serialization.
  5. In `main()` repair-plan branch: call `analyze(root)`, call `compute_repair_plan`, build JSON, emit to stdout, THEN write to plan file (stdout first so it's valid even on write failure); confinement-check plan file path before writing.
  6. Add `mode` to absent-workspace JSON for repair-plan (parallel to existing branches).
  7. `--plan-file` confinement: unconditional `plan_path.resolve().relative_to(root.resolve())` (not gated on `is_symlink()`) — covers direct paths, relative traversal, and symlinks alike.

### T3: CLI — `repair-apply` subcommand

- **Files:** `workspace_status.py`
- **Verification mode:** TDD + Visual/manual QA
- **Tests:**
  - `test_repair_apply_queue_to_shipped_bare_string` — bare string entry removed from queue in place, appended bare to shipped; assert `operation_type` and `spec_status` pinned
  - `test_repair_apply_queue_to_shipped_inline_object` — inline object entry removed in place by path-field match, bare string appended to shipped; other inline objects and their inline comments preserved
  - `test_repair_apply_queue_remove_archived` — archived entry removed from queue; shipped unchanged; assert shipped length is same
  - `test_repair_apply_deduplication` — path already in shipped → not appended again (shipped length unchanged)
  - `test_repair_apply_multiple_operations` — two operations spanning two initiatives both applied; `operations_applied == 2`
  - `test_repair_apply_fingerprint_mismatch` — modify workspace.toml after plan; exit 2; `applied: false; reason: fingerprint_mismatch`
  - `test_repair_apply_plan_not_found` — exit 2; `applied: false; reason: plan_file_not_found`
  - `test_repair_apply_malformed_plan` — exit 2; `applied: false; reason: plan_file_parse_error`
  - `test_repair_apply_invalid_plan_schema` — unknown `operation_type` in plan → exit 2; `reason: plan_invalid`
  - `test_repair_apply_empty_operations_exits_0_no_write` — empty plan → exit 0; workspace.toml SHA-256 unchanged
  - `test_repair_apply_workspace_absent` — workspace.toml missing at apply time → exit 2; `reason: workspace_absent`
  - `test_repair_apply_no_writes_to_active_list` — active-source in manual_findings only → workspace.toml work.active SHA-256 unchanged
  - `test_repair_apply_atomic_write_no_stray_temp` — no stray `.workspace.toml.*.tmp` file after successful apply
  - `test_repair_apply_spec_status_changed` — spec.md status changes from Shipped to Approved between plan and apply → operation skipped with `reason="spec_status_changed"`; `per_operation` in result JSON
  - `test_repair_apply_missing_shipped_key_created` — initiative with no `shipped` key → key created; bare string appended
  - `test_repair_apply_cross_initiative_dedup_independent` — same spec_path in two different initiatives' queues → each handled independently by ini_slug
  - `test_repair_apply_plan_file_confinement` — `--plan-file` resolving outside root via symlink → exit 2, `reason="plan_file_outside_root"`
  - `test_repair_apply_plan_file_confinement_direct_path` — `--plan-file ../../evil.json` (no symlink) → exit 2, `reason="plan_file_outside_root"`
  - `test_repair_apply_plan_invalid_spec_path_traversal` — `spec_path="spec/../../evil"` → exit 2, `reason="plan_invalid"`
  - `test_repair_apply_plan_invalid_spec_path_absolute` — `spec_path="/etc/passwd"` → exit 2, `reason="plan_invalid"`
  - `test_repair_apply_plan_invalid_coupling` — `operation_type="queue-to-shipped"` + `spec_status="Archived"` → exit 2, `reason="plan_invalid"`
  - `test_repair_apply_plan_invalid_empty_ini_slug` — `ini_slug=""` → exit 2, `reason="plan_invalid"`
  - `test_repair_apply_initiative_not_found` — AC20b: hand-edited plan with fingerprint match but ini_slug absent → `per_operation` `reason="initiative_not_found"`, `applied: false`
  - `test_repair_apply_entry_not_found_in_queue` — AC20b: hand-edited plan with fingerprint match but path not in queue → `per_operation` `reason="entry_not_found_in_queue"`, `applied: false`
  - `test_repair_apply_workspace_toml_symlink_escape` — AC16c: `workspace.toml` symlinked outside root → exit 2, `reason="workspace_outside_root"`
  - Stderr-assertion stubs: `test_repair_apply_fingerprint_mismatch`, `test_repair_apply_plan_not_found`, `test_repair_apply_malformed_plan` each assert the stderr substring ("fingerprint mismatch", "plan file not found", specific issue) and `assertNotIn(str(root), r.stderr)` (no absolute-path leak), mirroring `test_cli_generic_exception` at `test_workspace_status_cli.py:294`
  - `test_repair_apply_spec_status_changed` asserts workspace.toml SHA-256 unchanged after the single-op skip (all-skipped no-write, AC13)
  - `test_repair_apply_tomlkit_unavailable` — `PYTHONPATH`-shadowed stub raising `ImportError on import tomlkit` → exit 2, `reason="tomlkit_unavailable"`
  - `test_repair_apply_spec_status_unreadable` — one operation's spec.md deleted/corrupted → that op skipped with `reason="spec_status_unreadable"`; other op still applied
  - `test_repair_apply_queue_remove_archived_inline_object` — Archived entry as inline object `{path = "spec/foo"}` → removed in place; shipped unchanged
  - `test_repair_apply_round_trip` — end-to-end: run `repair-plan` on fixture, take produced plan file, run `repair-apply`, assert `operations_applied > 0` and workspace.toml mutated
  - `test_repair_apply_no_writes` — alias: `test_repair_plan_no_writes_to_workspace_toml` covers plan; this test confirms apply is the ONLY subcommand that writes workspace.toml
- **Approach:**
  1. Add `"repair-apply"` to `_SUBCOMMANDS`.
  2. Guard `import tomlkit` at repair-apply path only; `ImportError` → exit 2, `reason="tomlkit_unavailable"`.
  3. Implement `_load_and_verify_plan(root, plan_file_path)`:
     - unconditional confinement: `plan_file_path.resolve().relative_to(root.resolve())` (not `is_symlink()`-gated)
     - read bytes; parse JSON; structural validation:
       - `schema_version == 1`; `automatic_operations` is a list
       - each op: `operation_type` in `{"queue-to-shipped","queue-remove"}`; non-empty `spec_path` (no `..`, not absolute); non-empty `ini_slug`
       - `operation_type` ↔ `spec_status` coupling: `queue-to-shipped` only for `spec_status=="Shipped"`; `queue-remove` only for `spec_status=="Archived"`; mismatch → `reason="plan_invalid"`
     - read `workspace.toml` bytes once; SHA-256 compare to `workspace_fingerprint`; pass same bytes out (no re-open)
     - short-circuit: if `automatic_operations` is `[]`, return empty ops immediately (caller exits 0 without calling `_apply_operations`)
     - return (validated operations list, workspace_toml_bytes)
  4. Load `_safe_spec_path` and `extract_spec_status` from the engine module at import time (add alongside existing bindings; `_safe_spec_path` is a private engine helper importable via `_engine_mod._safe_spec_path`).
  5. Implement `_apply_operations(root, operations, workspace_toml_bytes, workspace_toml_path)` (parameter order matches LLD sketch: root, operations, bytes, path):
     - parse from bytes (`tomlkit.parse(workspace_toml_bytes.decode("utf-8"))`) — same bytes from fingerprint check
     - for each operation:
       - route slug through `_safe_spec_path(root, slug)` → returns `spec.md` Path or `None`; `None` → skip `reason="spec_status_unreadable"`
       - call `extract_spec_status(spec_md_path)` (engine helper, not `_read_spec_status`)
       - **re-derive action from disk status** (do not trust plan's `operation_type`): `Shipped` → `queue-to-shipped`; `Archived` → `queue-remove`; else skip `reason="spec_status_changed"`
       - verify disk status still matches plan's `spec_status`; mismatch → skip `reason="spec_status_changed"`
       - remove matched entry in place (`del queue[i]`) by path-field match (bare or inline-object)
       - for `queue-to-shipped`: create `work["shipped"] = tomlkit.array()` if absent; append if not already present
     - temp write: `fd, tmp_path = tempfile.mkstemp(dir=workspace_toml_path.parent, prefix=".workspace.toml.", suffix=".tmp")`; write via `os.fdopen(fd, "w")`; close; `os.replace(tmp_path, workspace_toml_path)`; `finally`: unlink tmp_path if replace failed
  6. In `main()` dispatch:
     - **Gate off the shared guard for repair-apply**: wrap `workspace_status.py:279-300`
       (the lstat absent-check + symlink confinement) in `if subcommand != "repair-apply":`.
       This prevents the generic exit-1/no-JSON path from preempting the subcommand-specific responses.
     - In the repair-apply branch:
       - Workspace-absent check: `try: workspace_toml.lstat() except FileNotFoundError: emit+return 2 reason="workspace_absent"`.
       - Write-target confinement: `workspace_toml.resolve().relative_to(root.resolve())`; failure → emit+return 2 `reason="workspace_outside_root"`.
       - Call `_load_and_verify_plan` — fingerprint check runs FIRST inside this call, then the empty-ops short-circuit; a stale fingerprint exits 2 `fingerprint_mismatch` even on empty `automatic_operations`.
       - If empty ops: emit `{…, "operations_applied":0, "per_operation":[]}` and return 0.
       - Otherwise call `_apply_operations`, emit result JSON with `per_operation` always present (records all ops, applied and skipped).

### T4: SKILL.md update

- **Files:** `packs/core/.apm/skills/workspace-status/SKILL.md`
- **Verification mode:** Goal-based check
- **Done when:** `grep -q "repair-plan" packs/core/.apm/skills/workspace-status/SKILL.md && grep -q "repair-apply" packs/core/.apm/skills/workspace-status/SKILL.md && grep -qE "repair-apply.*Yes|Yes.*repair-apply" packs/core/.apm/skills/workspace-status/SKILL.md`
- **Approach:**
  - Add `repair-plan` and `repair-apply` rows to §1a subcommand table (with `Writes: No` / `Yes` columns matching the existing table shape).
  - Add §1b (or extend §1a guidance) with repair invocation examples:
    - `repair-plan` usage, plan file location, when to run
    - `repair-apply` usage, fingerprint safety, manual-findings review guidance
    - Warning: `repair-apply` modifies `workspace.toml`; review `automatic_operations` in plan before applying

### T5: `.gitignore` update

- **Files:** `.gitignore`
- **Verification mode:** Goal-based check
- **Done when:** `git check-ignore -v .workspace-repair-plan.json` exits 0 AND `git check-ignore -v .workspace.toml.x.tmp` exits 0 (both match)
- **Approach:** Append `.workspace-repair-plan.json` and `.workspace.toml.*.tmp` to `.gitignore`.

### T6: `_STDLIB_MODULES` allowlist update

- **Files:** `tools/test_workspace_status_cli.py`
- **Verification mode:** Goal-based check
- **Done when:** `python3 tools/test_workspace_status_cli.py` exits 0 (existing `test_engine_stdlib_only` and `test_cli_stdlib_only` pass)
- **Approach:**
  - Add `"hashlib"` and `"datetime"` to `_STDLIB_MODULES` (engine-level additions).
  - Extend `_check_script` to accept an `allowed_extras: set[str] = frozenset()` parameter; use `_STDLIB_MODULES | allowed_extras` as the effective allowlist for that call.
  - `test_cli_stdlib_only` passes `allowed_extras={"tomlkit"}` — tomlkit is blessed CLI-only.
  - `test_engine_stdlib_only` passes no `allowed_extras` — engine check remains tomlkit-blind.
  - Add `test_engine_has_no_tomlkit_import` — asserts `tomlkit` does NOT appear in `workspace_status_engine.py` source; this negative test prevents engine contamination even if `_STDLIB_MODULES` is later amended.

### T7: build-self and gates

- **Files:** generated projections
- **Verification mode:** Goal-based check
- **Done when:** `make build-self` exits 0; `SKIP_SAST=1 make build-check` exits 0; `python3 tools/test_workspace_status.py` exits 0; `python3 tools/test_workspace_status_cli.py` exits 0

## Design (LLD)

### Engine — new types

```python
@dataclasses.dataclass
class RepairOperation:
    operation_type: str   # "queue-to-shipped" | "queue-remove"
    spec_path: str
    spec_status: str      # "Shipped" | "Archived"
    ini_slug: str

@dataclasses.dataclass
class ManualFinding:
    finding_type: int
    spec_path: str
    spec_status: str
    ini_slug: str
    list_name: str
    reason: str

@dataclasses.dataclass
class RepairPlan:
    automatic_operations: list[RepairOperation]
    manual_findings: list[ManualFinding]
    workspace_fingerprint: str
    planned_at: str
```

### Engine — `compute_repair_plan`

```python
def compute_repair_plan(
    result: WorkspaceStatusResult,
    workspace_path: Path,
) -> RepairPlan:
    import hashlib, datetime
    automatic: list[RepairOperation] = []
    manual: list[ManualFinding] = []

    # Duplicate detection: paths appearing >1 time in Type 2 queue findings per ini
    from collections import Counter
    queue_path_counts: Counter[tuple[str, str]] = Counter()
    for f in result.type2:
        if f.list_name == "queue":
            queue_path_counts[(f.ini_slug, f.spec_path)] += 1
    duplicate_keys = {k for k, n in queue_path_counts.items() if n > 1}

    for f in result.type1:
        manual.append(ManualFinding(
            finding_type=1, spec_path=f.spec_path, spec_status=f.spec_status,
            ini_slug=f.ini_slug, list_name=f.list_name, reason="type1-untracked",
        ))
    for f in result.type2:
        if f.list_name == "queue" and (f.ini_slug, f.spec_path) in duplicate_keys:
            reason = "type2-queue-duplicate"
            manual.append(ManualFinding(
                finding_type=2, spec_path=f.spec_path, spec_status=f.spec_status,
                ini_slug=f.ini_slug, list_name=f.list_name, reason=reason,
            ))
        elif f.list_name == "queue" and f.spec_status in ("Shipped", "Archived"):
            op_type = "queue-to-shipped" if f.spec_status == "Shipped" else "queue-remove"
            automatic.append(RepairOperation(
                operation_type=op_type, spec_path=f.spec_path,
                spec_status=f.spec_status, ini_slug=f.ini_slug,
            ))
        else:
            reason = (
                "type2-active-source" if f.list_name == "active"
                else f"type2-queue-{f.spec_status.lower()}"
            )
            manual.append(ManualFinding(
                finding_type=2, spec_path=f.spec_path, spec_status=f.spec_status,
                ini_slug=f.ini_slug, list_name=f.list_name, reason=reason,
            ))
    for f in result.type3:
        manual.append(ManualFinding(
            finding_type=3, spec_path=f.spec_path, spec_status=f.spec_status,
            ini_slug=f.ini_slug, list_name=f.list_name, reason="type3-premature",
        ))

    fingerprint = hashlib.sha256(workspace_path.read_bytes()).hexdigest()
    planned_at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    return RepairPlan(
        automatic_operations=automatic,
        manual_findings=manual,
        workspace_fingerprint=fingerprint,
        planned_at=planned_at,
    )
```

### CLI — `repair-apply` tomlkit write logic sketch

```python
# NOTE: `import tomlkit` is guarded in the repair-apply branch of main(),
# BEFORE _apply_operations is called, with try/except ImportError → exit 2,
# reason="tomlkit_unavailable". The sketch omits the guard for brevity.
def _apply_operations(
    root: Path,
    operations: list[dict],
    workspace_toml_bytes: bytes,
    workspace_path: Path,
) -> tuple[int, list[dict]]:
    """Returns (operations_applied, per_operation_results).
    Caller must short-circuit before this if operations is empty."""
    import tomlkit, os, tempfile
    doc = tomlkit.parse(workspace_toml_bytes.decode("utf-8"))
    applied = 0
    per_op: list[dict] = []

    for op in operations:
        ini_slug = op["ini_slug"]
        spec_path = op["spec_path"]
        expected_status = op["spec_status"]

        # Confinement + re-verify spec status from disk
        slug = spec_path.removeprefix("spec/")
        # _safe_spec_path returns the spec.md Path if within root/docs/specs/, else None
        spec_file = _safe_spec_path(root, slug)
        if spec_file is None:
            per_op.append({"path": spec_path, "applied": False, "reason": "spec_status_unreadable"})
            continue
        current_status = extract_spec_status(spec_file)  # engine helper (not _read_spec_status)
        if current_status is None:
            per_op.append({"path": spec_path, "applied": False, "reason": "spec_status_unreadable"})
            continue
        if current_status != expected_status:
            per_op.append({"path": spec_path, "applied": False, "reason": "spec_status_changed"})
            continue

        # Re-derive action from verified disk status (do not trust plan's operation_type)
        if current_status == "Shipped":
            effective_op_type = "queue-to-shipped"
        elif current_status == "Archived":
            effective_op_type = "queue-remove"
        else:
            per_op.append({"path": spec_path, "applied": False, "reason": "spec_status_changed"})
            continue

        ini = doc.get(ini_slug)
        if ini is None:
            per_op.append({"path": spec_path, "applied": False, "reason": "initiative_not_found"})
            continue
        work = ini.get("work", {})
        queue = work.get("queue", [])

        # In-place removal: find and delete first matching index
        removed = False
        for i, entry in enumerate(queue):
            entry_path = entry if isinstance(entry, str) else entry.get("path", "")
            if entry_path == spec_path:
                del queue[i]
                removed = True
                break

        if not removed:
            per_op.append({"path": spec_path, "applied": False, "reason": "entry_not_found_in_queue"})
            continue

        if effective_op_type == "queue-to-shipped":
            if "shipped" not in work:
                work["shipped"] = tomlkit.array()
            shipped = work["shipped"]
            existing = {e if isinstance(e, str) else e.get("path", "") for e in shipped}
            if spec_path not in existing:
                shipped.append(spec_path)

        per_op.append({"path": spec_path, "applied": True})
        applied += 1

    # Only write when at least one operation succeeded (AC13 / prevents inode churn)
    if applied == 0:
        return applied, per_op

    # Atomic write via mkstemp (canonical form per AC13)
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=workspace_path.parent,
            prefix=".workspace.toml.",
            suffix=".tmp",
        )
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(tomlkit.dumps(doc))
        os.replace(tmp_path, workspace_path)
        tmp_path = None  # replaced successfully; don't unlink
    finally:
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return applied, per_op
```

## Changelog

- Add `repair-plan` and `repair-apply` subcommands to workspace-status CLI
- Add `RepairOperation`, `ManualFinding`, `RepairPlan` dataclasses to engine
- Add `compute_repair_plan()` to engine
- Update SKILL.md §1a table and add §repair guidance
- New: tomlkit used in CLI write path (not engine)
