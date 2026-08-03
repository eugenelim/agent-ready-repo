#!/usr/bin/env python3
"""workspace-status CLI — thin JSON frontend for the production engine.

Usage:
    python3 workspace_status.py status       --root "<repo-root>"
    python3 workspace_status.py explain      --root "<repo-root>" --item <selector>
    python3 workspace_status.py reconcile    --root "<repo-root>"
    python3 workspace_status.py repair-plan  --root "<repo-root>" [--plan-file <path>]
    python3 workspace_status.py repair-apply --root "<repo-root>" [--plan-file <path>]
    python3 workspace_status.py              --root "<repo-root>"   # compat alias for reconcile

Output (stdout): deterministic UTF-8 JSON with schema_version = 1.

Exit codes:
    0  — success
    1  — workspace.toml not found (workspace_present: false in JSON)
    2  — any other error (one-line message on stderr; no traceback, no internal paths)
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path, PurePosixPath

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
# Prevent Python from writing __pycache__ into the installed skill tree.
sys.dont_write_bytecode = True

# ── Load engine from the same scripts/ directory ──────────────────────────────

_here = Path(__file__).parent
_engine_path = _here / "workspace_status_engine.py"

try:
    _engine_spec = importlib.util.spec_from_file_location(
        "workspace_status_engine", _engine_path
    )
    _engine_mod = importlib.util.module_from_spec(_engine_spec)  # type: ignore[arg-type]
    # Register before exec_module so dataclass annotation resolution (from __future__ import
    # annotations + sys.modules lookup) works correctly.
    sys.modules.setdefault("workspace_status_engine", _engine_mod)
    _engine_spec.loader.exec_module(_engine_mod)  # type: ignore[union-attr]
    analyze = _engine_mod.analyze
    analyze_bounded = _engine_mod.analyze_bounded
    explain_item = _engine_mod.explain_item
    compute_type2_cleanup = _engine_mod.compute_type2_cleanup
    compute_repair_plan = _engine_mod.compute_repair_plan
    extract_spec_status = _engine_mod.extract_spec_status
    extract_spec_status_with_fingerprint = _engine_mod.extract_spec_status_with_fingerprint
    _safe_spec_path = _engine_mod._safe_spec_path
except Exception as _load_err:
    # Engine load failure must be exit 2, not exit 1 (reserved for absent workspace).
    # Emit only the exception type — the message may include the engine's install path.
    print(f"workspace-status: engine load failed: {type(_load_err).__name__}", file=sys.stderr)
    sys.exit(2)


# ── Subcommand routing ────────────────────────────────────────────────────────

_SUBCOMMANDS = frozenset({"status", "explain", "reconcile", "repair-plan", "repair-apply"})
_DEFAULT_PLAN_FILE = ".workspace-repair-plan.json"
_VALID_OPERATION_TYPES = frozenset({"queue-to-shipped", "queue-remove"})


# ── Serialisation helpers ─────────────────────────────────────────────────────

def _work_entry_dict(entry, ini_slug: str) -> dict:
    return {
        "path": entry.path,
        "slug": entry.slug,
        "needs": entry.needs,
        "ini_slug": ini_slug,
    }


def _classification_dict(c) -> dict:
    return {
        "path": c.entry.path,
        "slug": c.entry.slug,
        "needs": c.entry.needs,
        "ini_slug": c.ini_slug,
        "blocking_needs": c.blocking_needs,
    }


def _shaping_dict(c) -> dict:
    return {
        "slug": c.entry.slug,
        "entry_type": c.entry.entry_type,
        "needs": c.entry.needs,
        "ini_slug": c.ini_slug,
        "blocking_needs": c.blocking_needs,
    }


def _shaping_entry_dict(e) -> dict:
    return {"slug": e.slug, "entry_type": e.entry_type, "needs": e.needs}


def _finding_dict(f) -> dict:
    return {
        "finding_type": f.finding_type,
        "spec_path": f.spec_path,
        "spec_status": f.spec_status,
        "ini_slug": f.ini_slug,
        "list_name": f.list_name,
    }


def _brief_queue_dict(bq) -> dict | None:
    if bq is None:
        return None
    return {
        "executing": bq.executing,
        "ready": bq.ready,
        "draft": bq.draft,
    }


def _scan_dict(result) -> dict:
    return {
        "global_spec_scan_performed": result.global_scan_performed,
        "workspace_files_read": 1,
        "declared_spec_files_read": result.declared_spec_files_read,
        "global_scan_spec_files_read": result.global_scan_files_read,
    }


def _build_json(root: Path, result, mode: str) -> dict:
    # initiatives/work.active/work.shipped are filtered to active initiatives only;
    # reconciliation.* spans all initiatives (including paused/closed) — mirroring analyze().
    # A type2_cleanup_ops entry may therefore reference an ini_slug absent from initiatives[].
    initiatives_out: list[dict] = []
    active_entries: list[dict] = []
    shipped_entries: list[dict] = []
    # active_shaping_entries: per-entry provenance for shaping_queue.active.
    # Includes ALL active entries (signals and non-signals) so that shape: dep
    # resolution matches the engine's is_need_satisfied, which checks all active
    # entries regardless of type. Each entry carries ini_slug to avoid cross-initiative
    # slug collisions (two initiatives may share an initiative-scoped shaping slug).
    active_shaping_entries: list[dict] = []
    for ini in result.initiatives:
        if ini.status != "active":
            continue
        initiatives_out.append({
            "slug": ini.slug,
            "name": ini.name,
            "status": ini.status,
            "milestone": ini.milestone,
            "brief_queue": _brief_queue_dict(ini.brief_queue),
            "queue_empty": len(ini.work.queue) == 0,
        })
        for e in ini.work.active:
            active_entries.append(_work_entry_dict(e, ini.slug))
        for e in ini.work.shipped:
            shipped_entries.append(_work_entry_dict(e, ini.slug))
        for e in ini.shaping.active:
            active_shaping_entries.append({
                "slug": e.slug,
                "ini_slug": ini.slug,
                "entry_type": e.entry_type,
            })

    # Type 2 cleanup ops — one per Type 2 finding
    type2_cleanup_ops: list[dict] = []
    for f in result.type2:
        op = compute_type2_cleanup(
            ini_slug=f.ini_slug,
            source_list=f.list_name,
            spec_path=f.spec_path,
            spec_status=f.spec_status,
        )
        type2_cleanup_ops.append(op)

    types_performed = [1, 2, 3] if result.global_scan_performed else [2, 3]

    return {
        "schema_version": 1,
        "mode": mode,
        "workspace_present": True,
        "workspace_root": str(root.resolve()),
        "scan": _scan_dict(result),
        "initiatives": initiatives_out,
        "work": {
            "ready": [_classification_dict(c) for c in result.ready],
            "blocked": [_classification_dict(c) for c in result.blocked],
            "active": active_entries,
            "shipped": shipped_entries,
        },
        "shaping": {
            "ready": [_shaping_dict(c) for c in result.ready_shaping],
            "signals": [_shaping_dict(c) for c in result.signals],
            "blocked": [_shaping_dict(c) for c in result.blocked_shaping],
            "active_entries": active_shaping_entries,
            # [backlog].open typed entries (workspace-level, not per-initiative).
            # work-loop's shaping-item guard checks this list for slug matches.
            "top_level_backlog": [_shaping_entry_dict(e) for e in result.top_level_backlog],
        },
        "reconciliation": {
            "performed": True,
            "complete": result.global_scan_performed,
            "types_performed": types_performed,
            "type1": [_finding_dict(f) for f in result.type1],
            "type2": [_finding_dict(f) for f in result.type2],
            "type3": [_finding_dict(f) for f in result.type3],
            "type2_cleanup_ops": type2_cleanup_ops,
        },
        "diagnostics": {
            "workspace_files_read": 1,
            "spec_files_read": result.files_read,
        },
    }


def _build_explain_json(root: Path, result, selector: str, explain_result: dict) -> dict:
    return {
        "schema_version": 1,
        "mode": "explain",
        "workspace_present": True,
        "workspace_root": str(root.resolve()),
        "scan": _scan_dict(result),
        "selector": selector,
        **explain_result,
    }


def _build_repair_plan_json(root: Path, result, plan) -> dict:
    base = _build_json(root, result, "repair-plan")
    base["workspace_fingerprint"] = plan.workspace_fingerprint
    base["plan_id"] = plan.plan_id
    base["automatic_operations"] = [dataclasses.asdict(op) for op in plan.automatic_operations]
    base["manual_findings"] = [dataclasses.asdict(mf) for mf in plan.manual_findings]
    return base


def _recompute_plan_id(plan_data: dict) -> str:
    """Recompute the plan_id from plan JSON for tamper-detection.

    Uses the same canonical JSON as the engine: automatic_operations,
    manual_findings, schema_version=1, workspace_fingerprint.
    """
    auto_ops = plan_data.get("automatic_operations", [])
    manual = plan_data.get("manual_findings", [])
    fp = plan_data.get("workspace_fingerprint", "")
    canon = json.dumps({
        "automatic_operations": auto_ops,
        "manual_findings": manual,
        "schema_version": 1,
        "workspace_fingerprint": fp,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canon.encode("ascii")).hexdigest()


def _check_plan_file_confinement(plan_path: Path, root: Path, mode: str) -> Path | int:
    """Return resolved plan path if within root, else exit code 2.

    Callers must use the returned Path for all subsequent I/O to eliminate
    the TOCTOU window between the confinement check and the actual file
    operation (a parent-directory symlink retargeted after the check can
    otherwise redirect I/O outside the repository).
    """
    try:
        resolved = plan_path.resolve()
        resolved.relative_to(root.resolve())
        return resolved
    except (OSError, RuntimeError, ValueError):
        _emit({
            "schema_version": 1,
            "mode": mode,
            "applied": False,
            "reason": "plan_file_outside_root",
        })
        return 2


def _validate_plan_structure(data: dict) -> str | None:
    """Validate plan JSON structure. Return error reason string or None."""
    if not isinstance(data, dict):
        return "plan_invalid"
    if data.get("schema_version") != 1:
        return "plan_invalid"
    ops = data.get("automatic_operations")
    if not isinstance(ops, list):
        return "plan_invalid"
    for op in ops:
        if not isinstance(op, dict):
            return "plan_invalid"
        op_type = op.get("operation_type")
        spec_path = op.get("spec_path", "")
        ini_slug = op.get("ini_slug", "")
        spec_status = op.get("spec_status", "")
        if not isinstance(op_type, str) or op_type not in _VALID_OPERATION_TYPES:
            return "plan_invalid"
        if not spec_path or not isinstance(spec_path, str):
            return "plan_invalid"
        if not ini_slug or not isinstance(ini_slug, str):
            return "plan_invalid"
        # spec_path traversal guard — reject backslashes and Windows drive letters
        # before PurePosixPath; PurePosixPath("C:\\foo") treats it as a relative
        # string, so these must be caught explicitly.
        if "\\" in spec_path or (len(spec_path) >= 2 and spec_path[1] == ":"):
            return "plan_invalid"
        try:
            parts = PurePosixPath(spec_path).parts
        except Exception:
            return "plan_invalid"
        if ".." in parts or PurePosixPath(spec_path).is_absolute():
            return "plan_invalid"
        # operation_type ↔ spec_status coupling
        if op_type == "queue-to-shipped" and spec_status != "Shipped":
            return "plan_invalid"
        if op_type == "queue-remove" and spec_status != "Archived":
            return "plan_invalid"
        # spec_status_fingerprint is required (non-empty string)
        fp = op.get("spec_status_fingerprint", "")
        if not fp or not isinstance(fp, str):
            return "plan_invalid"
    return None


def _apply_operations(
    root: Path,
    operations: list[dict],
    workspace_toml_bytes: bytes,
    workspace_path: Path,
) -> tuple[int, list[dict]]:
    """Apply automatic operations using tomlkit. Returns (applied, per_operation)."""
    import stat

    import tomlkit  # noqa: PLC0415 — guarded CLI-only import

    doc = tomlkit.parse(workspace_toml_bytes.decode("utf-8"))
    applied = 0
    per_op: list[dict] = []

    for op in operations:
        spec_path = op["spec_path"]
        ini_slug = op["ini_slug"]
        expected_status = op["spec_status"]
        expected_fp = op.get("spec_status_fingerprint", "")

        # Confinement + re-verify spec status from disk
        slug = spec_path.removeprefix("spec/")
        spec_file = _safe_spec_path(root, slug)
        if spec_file is None:
            per_op.append(
                {"path": spec_path, "applied": False, "reason": "spec_status_unreadable"}
            )
            continue
        current_status, current_fp = extract_spec_status_with_fingerprint(spec_file)
        if current_status is None:
            per_op.append(
                {"path": spec_path, "applied": False, "reason": "spec_status_unreadable"}
            )
            continue
        if current_status != expected_status:
            per_op.append({"path": spec_path, "applied": False, "reason": "spec_status_changed"})
            continue
        # Fingerprint check: detect changes to the status line that keep the token the same
        if expected_fp and current_fp and current_fp != expected_fp:
            per_op.append(
                {"path": spec_path, "applied": False, "reason": "spec_status_fingerprint_changed"}
            )
            continue

        # Re-derive action from verified disk status (do not trust plan's operation_type)
        if current_status == "Shipped":
            effective_op_type = "queue-to-shipped"
        elif current_status == "Archived":
            effective_op_type = "queue-remove"
        else:
            per_op.append({"path": spec_path, "applied": False, "reason": "spec_status_changed"})
            continue

        ini_section = doc.get(ini_slug)
        if ini_section is None:
            per_op.append({"path": spec_path, "applied": False, "reason": "initiative_not_found"})
            continue
        work = ini_section.get("work", {})
        queue = work.get("queue", [])

        # In-place removal: find and delete first matching entry
        removed = False
        for i, entry in enumerate(queue):
            entry_path = entry if isinstance(entry, str) else entry.get("path", "")
            if entry_path == spec_path:
                del queue[i]
                removed = True
                break

        if not removed:
            per_op.append(
                {"path": spec_path, "applied": False, "reason": "entry_not_found_in_queue"}
            )
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

    # Only write when at least one operation succeeded
    if applied == 0:
        return applied, per_op

    tmp_path = None
    try:
        orig_mode = stat.S_IMODE(workspace_path.stat().st_mode)
        fd, tmp_path = tempfile.mkstemp(
            dir=workspace_path.parent,
            prefix=".workspace.toml.",
            suffix=".tmp",
        )
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(tomlkit.dumps(doc))
        # Preserve original mode; set after fd close (cross-platform — os.fchmod is Unix-only)
        Path(tmp_path).chmod(orig_mode)
        Path(tmp_path).replace(workspace_path)
        tmp_path = None
    finally:
        if tmp_path is not None:
            with contextlib.suppress(OSError):
                Path(tmp_path).unlink()

    return applied, per_op


def _emit(data: dict) -> None:
    sys.stdout.write(json.dumps(data, sort_keys=True, allow_nan=False) + "\n")
    sys.stdout.flush()


# ── Main ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    argv = list(argv)

    # Pre-dispatch: first token is a known subcommand → strip it
    if argv and argv[0] in _SUBCOMMANDS:
        subcommand = argv.pop(0)
        compat_alias = False
    else:
        subcommand = "reconcile"
        compat_alias = True

    if compat_alias:
        print(
            "workspace-status: no subcommand specified; defaulting to reconcile. "
            "Use 'reconcile' explicitly.",
            file=sys.stderr,
        )

    parser = argparse.ArgumentParser(
        description="workspace-status: parse workspace.toml and emit JSON"
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Absolute or relative path to the repository root",
    )
    if subcommand == "explain":
        parser.add_argument(
            "--item",
            required=True,
            help="Selector for the item to explain (slug or spec/ path)",
        )
    if subcommand in ("repair-plan", "repair-apply"):
        parser.add_argument(
            "--plan-file",
            default=None,
            help="Override plan file path (default: <root>/.workspace-repair-plan.json)",
        )
    if subcommand == "repair-apply":
        parser.add_argument(
            "--yes",
            action="store_true",
            default=False,
            help="Required explicit confirmation to apply the repair plan",
        )
    args = parser.parse_args(argv)
    root = Path(args.root)

    try:
        # Validate root before checking workspace.toml.
        # If root is a file (not a dir), Path.exists() returns False via ENOTDIR
        # without raising, which would falsely report workspace_present: false.
        if not root.is_dir():
            raise NotADirectoryError(f"--root is not a directory: {root}")

        workspace_toml = root / "workspace.toml"

        # repair-apply owns its workspace checks (needs exit 2, not exit 1).
        # The shared lstat + symlink guards below are skipped for repair-apply.
        if subcommand != "repair-apply":
            # Use lstat() so a dangling symlink (entry exists but target absent) is
            # not mistaken for a missing workspace — stat() follows the link and
            # raises FileNotFoundError, falsely reporting workspace_present: false.
            # lstat() only raises FileNotFoundError when no directory entry exists.
            try:
                workspace_toml.lstat()
            except FileNotFoundError:
                _emit({
                    "schema_version": 1,
                    "mode": subcommand,
                    "workspace_present": False,
                    "workspace_root": str(root.resolve()),
                })
                return 1
            # Path-confinement: if workspace.toml is a symlink, verify the target
            # stays within the repo root so session-start cannot read another tree's
            # initiative data through an escape link.
            # Resolve once here; repair-plan uses _ws_toml_resolved for TOCTOU-safe reads.
            _ws_toml_resolved = workspace_toml.resolve()
            if workspace_toml.is_symlink():
                try:
                    _ws_toml_resolved.relative_to(root.resolve())
                except (OSError, RuntimeError, ValueError):
                    print(
                        "workspace-status error: workspace.toml symlink escapes repository root",
                        file=sys.stderr,
                    )
                    return 2

        if subcommand == "repair-plan":
            plan_path = Path(args.plan_file) if args.plan_file else (root / _DEFAULT_PLAN_FILE)
            # Reject symlinked output paths: replace() renames a temp file over the
            # destination directory entry — on POSIX it follows the symlink and overwrites
            # the target, not the link itself, allowing any in-repo file to be clobbered.
            if plan_path.is_symlink():
                _emit({
                    "schema_version": 1,
                    "mode": "repair-plan",
                    "applied": False,
                    "reason": "plan_file_is_symlink",
                })
                return 2
            _plan_confinement = _check_plan_file_confinement(plan_path, root, "repair-plan")
            if isinstance(_plan_confinement, int):
                return _plan_confinement
            plan_path = _plan_confinement  # use resolved path for all I/O
            # Guard: reject plan-file == workspace.toml (symlink or alias clobber).
            # Use samefile() for identity — resolve()-equality fails on case-insensitive
            # filesystems where WORKSPACE.TOML and workspace.toml are the same inode.
            with contextlib.suppress(OSError, RuntimeError):
                if plan_path.samefile(workspace_toml):
                    _emit({
                        "schema_version": 1,
                        "mode": "repair-plan",
                        "applied": False,
                        "reason": "plan_file_is_workspace_toml",
                    })
                    return 2
            # Capture fingerprint BEFORE analyze() to bind the plan to this snapshot.
            # analyze() re-reads workspace.toml internally; by pre-capturing bytes here
            # we ensure the stored fingerprint reflects what we observed at plan-time,
            # not a later re-read that could race with a concurrent writer.
            # Read from the already-resolved path (set by the shared symlink guard above)
            # to avoid following a retargeted symlink between the guard and this read.
            _plan_ws_bytes = _ws_toml_resolved.read_bytes()
            _plan_ws_fp = hashlib.sha256(_plan_ws_bytes).hexdigest()
            result = analyze(root, workspace_bytes=_plan_ws_bytes)
            plan = compute_repair_plan(result, workspace_toml, workspace_fingerprint=_plan_ws_fp)
            data = _build_repair_plan_json(root, result, plan)
            # Emit stdout first — plan JSON always available even if file write fails
            _emit(data)
            tmp_plan: str | None = None
            try:
                fd, tmp_plan = tempfile.mkstemp(
                    dir=plan_path.parent,
                    prefix=".plan.",
                    suffix=".tmp",
                )
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(json.dumps(data, sort_keys=True, allow_nan=False) + "\n")
                Path(tmp_plan).replace(plan_path)
                tmp_plan = None
            except OSError as write_err:
                _wmsg = str(write_err)
                with contextlib.suppress(OSError, RuntimeError):
                    _wmsg = _wmsg.replace(str(root.resolve()), "<root>")
                if root.is_absolute():
                    _wmsg = _wmsg.replace(str(root), "<root>")
                print(f"workspace-status: plan file write failed: {_wmsg}", file=sys.stderr)
                return 2
            finally:
                if tmp_plan is not None:
                    with contextlib.suppress(OSError):
                        Path(tmp_plan).unlink()
            return 0

        if subcommand == "repair-apply":
            # Explicit confirmation required before any mutation
            if not getattr(args, "yes", False):
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": False,
                    "reason": "confirmation_required",
                })
                return 2
            # Workspace-absent check (exit 2, not exit 1 — subcommand-specific shape)
            try:
                workspace_toml.lstat()
            except FileNotFoundError:
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": False,
                    "reason": "workspace_absent",
                })
                return 2
            # Write-target confinement; save resolved path for TOCTOU-safe reads
            try:
                _ws_apply_resolved = workspace_toml.resolve()
                _ws_apply_resolved.relative_to(root.resolve())
            except (OSError, RuntimeError, ValueError):
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": False,
                    "reason": "workspace_outside_root",
                })
                return 2
            plan_path = Path(args.plan_file) if args.plan_file else (root / _DEFAULT_PLAN_FILE)
            _plan_confinement = _check_plan_file_confinement(plan_path, root, "repair-apply")
            if isinstance(_plan_confinement, int):
                return _plan_confinement
            plan_path = _plan_confinement  # use resolved path for all I/O
            # Load plan file
            try:
                plan_raw = plan_path.read_text(encoding="utf-8")
            except FileNotFoundError:
                print("workspace-status: plan file not found", file=sys.stderr)
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": False,
                    "reason": "plan_file_not_found",
                })
                return 2
            try:
                plan_data = json.loads(plan_raw)
            except json.JSONDecodeError as je:
                _jmsg = str(je)
                with contextlib.suppress(OSError, RuntimeError):
                    _jmsg = _jmsg.replace(str(root.resolve()), "<root>")
                print(f"workspace-status: plan file parse error: {_jmsg}", file=sys.stderr)
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": False,
                    "reason": "plan_file_parse_error",
                })
                return 2
            validation_reason = _validate_plan_structure(plan_data)
            if validation_reason:
                print(f"workspace-status: plan file invalid: {validation_reason}", file=sys.stderr)
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": False,
                    "reason": validation_reason,
                })
                return 2
            # Recompute plan_id to detect tampering
            stored_plan_id = plan_data.get("plan_id", "")
            recomputed_plan_id = _recompute_plan_id(plan_data)
            if stored_plan_id != recomputed_plan_id:
                print("workspace-status: plan_id mismatch", file=sys.stderr)
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": False,
                    "reason": "plan_id_invalid",
                })
                return 2
            ops = plan_data.get("automatic_operations", [])
            if not ops:
                # Validate fingerprint before accepting an empty plan — a stale empty
                # plan must be rejected; fingerprint check precedes empty-ops short-circuit.
                _empty_bytes = _ws_apply_resolved.read_bytes()
                _empty_digest = hashlib.sha256(_empty_bytes).hexdigest()
                _empty_expected = plan_data.get("workspace_fingerprint", "")
                if _empty_digest != _empty_expected:
                    print("workspace-status: fingerprint mismatch", file=sys.stderr)
                    _emit({
                        "schema_version": 1,
                        "mode": "repair-apply",
                        "applied": False,
                        "reason": "fingerprint_mismatch",
                    })
                    return 2
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": True,
                    "plan_id": stored_plan_id,
                    "before_workspace_digest": _empty_digest,
                    "after_workspace_digest": _empty_digest,
                    "operations_applied": 0,
                    "per_operation": [],
                })
                return 0
            # tomlkit guard — only needed when there are operations to apply
            try:
                import tomlkit as _tomlkit_check  # noqa: F401
            except ImportError:
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": False,
                    "reason": "tomlkit_unavailable",
                })
                return 2
            # Acquire cross-platform sibling lock before final validation + write
            lock_path = root / ".workspace-repair.lock"
            lock_fd = -1
            try:
                lock_fd = os.open(
                    str(lock_path),
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
            except FileExistsError:
                print("workspace-status: repair lock is held by another process", file=sys.stderr)
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": False,
                    "reason": "lock_busy",
                })
                return 2
            try:
                os.close(lock_fd)
                lock_fd = -1
                # Resolve first, then read — ensures the fingerprint and the write
                # both target the same inode. Resolving before reading closes the
                # TOCTOU window where a symlink retarget between read_bytes() and
                # resolve() would let the fingerprint authenticate target A while
                # _apply_operations writes target B.
                workspace_write_target = workspace_toml.resolve()
                try:
                    workspace_write_target.relative_to(root.resolve())
                except (OSError, RuntimeError, ValueError):
                    _emit({
                        "schema_version": 1,
                        "mode": "repair-apply",
                        "applied": False,
                        "reason": "workspace_outside_root",
                    })
                    return 2
                # Read from the resolved target so bytes and write target are in sync
                workspace_bytes = workspace_write_target.read_bytes()
                actual_fp = hashlib.sha256(workspace_bytes).hexdigest()
                expected_fp = plan_data.get("workspace_fingerprint", "")
                if actual_fp != expected_fp:
                    print("workspace-status: fingerprint mismatch", file=sys.stderr)
                    _emit({
                        "schema_version": 1,
                        "mode": "repair-apply",
                        "applied": False,
                        "reason": "fingerprint_mismatch",
                    })
                    return 2
                before_digest = actual_fp
                applied, per_op = _apply_operations(
                    root, ops, workspace_bytes, workspace_write_target
                )
                after_digest = (
                    hashlib.sha256(workspace_write_target.read_bytes()).hexdigest()
                    if applied > 0 else before_digest
                )
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": True,
                    "plan_id": stored_plan_id,
                    "before_workspace_digest": before_digest,
                    "after_workspace_digest": after_digest,
                    "operations_applied": applied,
                    "per_operation": per_op,
                })
                return 0
            finally:
                if lock_fd >= 0:
                    with contextlib.suppress(OSError):
                        os.close(lock_fd)
                with contextlib.suppress(OSError):
                    lock_path.unlink()

        if subcommand == "explain":
            result = analyze_bounded(root)
            explain_result = explain_item(result, args.item)
            data = _build_explain_json(root, result, args.item, explain_result)
        elif subcommand == "status":
            result = analyze_bounded(root)
            data = _build_json(root, result, "status")
        else:
            result = analyze(root)
            data = _build_json(root, result, "reconcile")

        _emit(data)
        return 0
    except Exception as exc:
        _msg = str(exc)
        # Redact the resolved (canonical) path first — covers symlink-redirected paths
        # (e.g. /var/... → /private/var/... on macOS).
        with contextlib.suppress(OSError, RuntimeError):
            _msg = _msg.replace(str(root.resolve()), "<root>")
        # Also redact the raw --root argument when it is absolute; skip when relative
        # ("." or a short name) to avoid corrupting unrelated parts of the message.
        if root.is_absolute():
            _msg = _msg.replace(str(root), "<root>")
        print(f"workspace-status error: {type(exc).__name__}: {_msg}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
