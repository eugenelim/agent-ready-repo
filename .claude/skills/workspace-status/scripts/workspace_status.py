#!/usr/bin/env python3
"""workspace-status CLI — thin JSON frontend for the production engine.

Usage:
    python3 workspace_status.py --root "<repo-root>"

Output (stdout): deterministic UTF-8 JSON with schema_version = 1.

Exit codes:
    0  — success
    1  — workspace.toml not found (workspace_present: false in JSON)
    2  — any other error (one-line message on stderr; no traceback, no internal paths)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

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
    compute_type2_cleanup = _engine_mod.compute_type2_cleanup
except Exception as _load_err:
    # Engine load failure must be exit 2, not exit 1 (reserved for absent workspace).
    print(f"workspace-status: engine load failed: {_load_err}", file=sys.stderr)
    sys.exit(2)


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


def _build_json(root: Path, result) -> dict:
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

    return {
        "schema_version": 1,
        "workspace_present": True,
        "workspace_root": str(root.resolve()),
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
        },
        "reconciliation": {
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


def _emit(data: dict) -> None:
    sys.stdout.write(json.dumps(data, sort_keys=True, allow_nan=False) + "\n")
    sys.stdout.flush()


# ── Main ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="workspace-status: parse workspace.toml and emit JSON"
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Absolute or relative path to the repository root",
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
        # Use lstat() so a dangling symlink (entry exists but target absent) is
        # not mistaken for a missing workspace — stat() follows the link and
        # raises FileNotFoundError, falsely reporting workspace_present: false.
        # lstat() only raises FileNotFoundError when no directory entry exists.
        try:
            workspace_toml.lstat()
        except FileNotFoundError:
            _emit({
                "schema_version": 1,
                "workspace_present": False,
                "workspace_root": str(root.resolve()),
            })
            return 1
        result = analyze(root)
        data = _build_json(root, result)
        _emit(data)
        return 0
    except Exception as exc:
        print(f"workspace-status error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
