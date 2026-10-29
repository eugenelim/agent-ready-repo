#!/usr/bin/env python3
"""workspace-status CLI — thin JSON frontend for the production engine.

Usage:
    python3 workspace_status.py status       --root "<repo-root>"
    python3 workspace_status.py selected-membership --root "<repo-root>" \
        --spec-dir docs/specs/<slug> [--spec-dir docs/specs/<slug> ...]
    python3 workspace_status.py explain      --root "<repo-root>" --item <selector>
    python3 workspace_status.py reconcile    --root "<repo-root>"
    python3 workspace_status.py repair-plan  --root "<repo-root>" [--plan-file <path>]
    python3 workspace_status.py repair-apply --root "<repo-root>" [--plan-file <path>]
    python3 workspace_status.py prune        --root "<repo-root>" \
        --select docs/specs/<slug> [--preview | --confirmation-file <path>]
    python3 workspace_status.py retirement-candidates --root "<repo-root>" \
        --run-date YYYY-MM-DD [--stale-after-days N]
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
import datetime
import hashlib
import importlib.util
import json
import os
import re
import secrets
import stat
import sys
import tempfile
import tomllib
from pathlib import Path, PurePosixPath
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
# Prevent Python from writing __pycache__ into the installed skill tree.
sys.dont_write_bytecode = True

_PUBLIC_PATH_CHARS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-/"
)
_ENGINE_BOUND = False
_engine: Any = None
analyze: Any = None
analyze_bounded: Any = None
explain_item: Any = None
compute_type2_cleanup: Any = None
compute_repair_plan: Any = None
compute_migration_plan: Any = None
extract_legacy_migration_memberships: Any = None
build_migration_finding: Any = None
build_migration_result: Any = None
confine_migration_path: Any = None
migration_candidate_routes: Any = None
validate_migration_ledger_invariants: Any = None
validate_migration_ledger_shape: Any = None
validate_migration_selection: Any = None
migration_selection_digest: Any = None
extract_legacy_source_slice: Any = None
extract_spec_status: Any = None
extract_spec_status_with_fingerprint: Any = None
parse_workspace: Any = None
run_canonical_reconciliation: Any = None
cooled_work_entry_paths: Any = None
canonical_repository_identity: Any = None
_safe_spec_path: Any = None
_spec_slug_from_workspace_path: Any = None
_repair_entry_eligibility: Any = None
_migration_operation_digest: Any = None
project_closeout_status: Any = None
selected_membership_status: Any = None
prune_preview: Any = None
prune_execute: Any = None
retirement_candidates_document: Any = None
validate_retirement_document: Any = None

# ── Load engine from the same scripts/ directory ──────────────────────────────


def _bind_engine() -> bool:
    """Load the sibling engine after subcommand parsing.

    Status-like public commands can then emit the canonical deny JSON with the
    requested mode instead of leaking an import traceback or installed path.
    """
    global _ENGINE_BOUND
    if _ENGINE_BOUND:
        return True
    engine_path = Path(__file__).parent / "workspace_status_engine.py"
    registered: list[str] = []
    try:
        engine_mod = sys.modules.get("workspace_status_engine")
        if engine_mod is None:
            engine_spec = importlib.util.spec_from_file_location(
                "workspace_status_engine", engine_path
            )
            engine_mod = importlib.util.module_from_spec(engine_spec)  # type: ignore[arg-type]
            # Register before exec_module so dataclass annotation resolution works
            # with `from __future__ import annotations`.
            sys.modules.setdefault("workspace_status_engine", engine_mod)
            registered.append("workspace_status_engine")
            engine_spec.loader.exec_module(engine_mod)  # type: ignore[union-attr]

        prune_mod = sys.modules.get("workspace_status_prune")
        if prune_mod is None:
            prune_path = engine_path.with_name("workspace_status_prune.py")
            prune_spec = importlib.util.spec_from_file_location(
                "workspace_status_prune", prune_path
            )
            prune_mod = importlib.util.module_from_spec(prune_spec)  # type: ignore[arg-type]
            sys.modules.setdefault("workspace_status_prune", prune_mod)
            registered.append("workspace_status_prune")
            prune_spec.loader.exec_module(prune_mod)  # type: ignore[union-attr]
    except Exception:
        # Registration happens before exec_module, so a raising exec leaves a
        # half-built module behind that a later attempt would reuse. Drop only
        # what this call registered.
        for partial in registered:
            sys.modules.pop(partial, None)
        return False
    globals().update({
        "_engine": engine_mod,
        "analyze": engine_mod.analyze,
        "analyze_bounded": engine_mod.analyze_bounded,
        "explain_item": engine_mod.explain_item,
        "compute_type2_cleanup": engine_mod.compute_type2_cleanup,
        "compute_repair_plan": engine_mod.compute_repair_plan,
        "compute_migration_plan": engine_mod.compute_migration_plan,
        "extract_legacy_migration_memberships": (
            engine_mod.extract_legacy_migration_memberships
        ),
        "build_migration_finding": engine_mod.build_migration_finding,
        "build_migration_result": engine_mod.build_migration_result,
        "confine_migration_path": engine_mod.confine_migration_path,
        "migration_candidate_routes": engine_mod.migration_candidate_routes,
        "validate_migration_ledger_invariants": (
            engine_mod.validate_migration_ledger_invariants
        ),
        "validate_migration_ledger_shape": engine_mod.validate_migration_ledger_shape,
        "validate_migration_selection": engine_mod.validate_migration_selection,
        "migration_selection_digest": engine_mod.migration_selection_digest,
        "extract_legacy_source_slice": engine_mod.extract_legacy_source_slice,
        "extract_spec_status": engine_mod.extract_spec_status,
        "extract_spec_status_with_fingerprint": (
            engine_mod.extract_spec_status_with_fingerprint
        ),
        "parse_workspace": engine_mod.parse_workspace,
        "run_canonical_reconciliation": engine_mod.run_canonical_reconciliation,
        "cooled_work_entry_paths": engine_mod.cooled_work_entry_paths,
        "canonical_repository_identity": engine_mod.canonical_repository_identity,
        "_safe_spec_path": engine_mod._safe_spec_path,
        "_spec_slug_from_workspace_path": engine_mod._spec_slug_from_workspace_path,
        "_repair_entry_eligibility": engine_mod._repair_entry_eligibility,
        "_migration_operation_digest": engine_mod._migration_operation_digest,
        "project_closeout_status": engine_mod.project_closeout_status,
        "selected_membership_status": engine_mod.selected_membership_status,
        "prune_preview": prune_mod.prune_preview,
        "prune_execute": prune_mod.prune_execute,
    })
    _ENGINE_BOUND = True
    return True


def _bind_retirement_command() -> bool:
    """Load the retirement command without loading the mutable engine surfaces."""
    global retirement_candidates_document, validate_retirement_document
    command_path = Path(__file__).with_name("workspace_status_retirement_command.py")
    module_name = "workspace_status_retirement_command"
    try:
        command_mod = sys.modules.get(module_name)
        if command_mod is None:
            command_spec = importlib.util.spec_from_file_location(module_name, command_path)
            if command_spec is None or command_spec.loader is None:
                return False
            command_mod = importlib.util.module_from_spec(command_spec)
            sys.modules[module_name] = command_mod
            command_spec.loader.exec_module(command_mod)
    except Exception:
        sys.modules.pop(module_name, None)
        return False
    retirement_candidates_document = command_mod.retirement_candidates_document
    validate_retirement_document = command_mod.validate_retirement_document
    return True


# ── Subcommand routing ────────────────────────────────────────────────────────

_SUBCOMMANDS = frozenset({
    "status",
    "selected-membership",
    "explain",
    "reconcile",
    "repair-plan",
    "repair-apply",
    "repair-rollback",
    "prune",
    "retirement-candidates",
})
_DEFAULT_PLAN_FILE = ".workspace-repair-plan.json"
_VALID_OPERATION_TYPES = frozenset({
    "queue-to-shipped",
    "queue-remove",
    "needs-to-header",
    "needs-drop-cooled",
    "captured-to-file",
    "intent-brief-drop",
})


class UnsafeMigrationPathError(RuntimeError):
    """Signal that migration projection could not safely read workspace state."""


# ── Serialisation helpers ─────────────────────────────────────────────────────

def _work_entry_dict(entry, ini_slug: str) -> dict:
    public_path = _public_canonical_path(entry.path)
    return {
        "path": public_path,
        "slug": _public_canonical_slug(entry.path),
        # Shipped compatibility records are not dispatch inputs. Omitting their
        # legacy needs prevents an unsafe raw value bypassing canonical redaction.
        "needs": [],
        "ini_slug": _public_ini_slug(ini_slug),
    }


def _classification_dict(c) -> dict:
    return {
        "path": c.entry.path,
        "slug": c.entry.slug,
        "needs": _public_needs(c.entry.needs),
        "ini_slug": _public_ini_slug(c.ini_slug),
        "blocking_needs": _public_needs(c.blocking_needs),
    }


def _shaping_dict(c) -> dict:
    return {
        "slug": c.entry.slug,
        "entry_type": c.entry.entry_type,
        "needs": _public_needs(c.entry.needs),
        "ini_slug": _public_ini_slug(c.ini_slug),
        "blocking_needs": _public_needs(c.blocking_needs),
    }


def _shaping_entry_dict(e) -> dict:
    return {
        "slug": e.slug,
        "entry_type": e.entry_type,
        "needs": _public_needs(e.needs),
    }


def _repo_backlog_entry_dict(entry) -> dict:
    """Project one backlog entry to the fields a consumer renders.

    `room`, `slug`-or-`path`, and `summary` are what `SKILL.md` renders;
    `needs` is load-bearing because `SKILL.md` forbids rereading raw TOML to
    determine dependencies. `kind`, `entry_type`, and `source` have no reader,
    so they are deliberately not projected — an emitted field with no consumer
    is re-sent to the model on every later request in an agent call. Narrowing
    applies to every mode, keeping `reconcile` and `status` identical here.

    `summary` and `needs` are projected as written, while sibling emitters in
    this module bound their values through a `_public_*` filter. That is
    deliberate. `workspace.toml` is working material for developers in the same
    repository and carries the same trust as the source code beside it, so its
    display prose needs no redaction on the way out. Reusing `_public_need`
    here would also be wrong on its own terms: it accepts only strings and
    returns the sentinel for anything else, so every typed dependency record
    would collapse to the sentinel and lose exactly the dependency data
    `SKILL.md` forbids recovering by rereading raw TOML.
    """
    result = {"room": entry.room, "needs": entry.needs}
    for key in ("slug", "path", "summary"):
        value = getattr(entry, key)
        if value is not None:
            result[key] = value
    return result


def _finding_dict(f) -> dict:
    return {
        "finding_type": f.finding_type,
        "spec_path": _public_canonical_path(f.spec_path),
        "spec_status": f.spec_status,
        "ini_slug": _public_ini_slug(f.ini_slug, allow_empty=True),
        "list_name": f.list_name,
    }


def _public_canonical_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        return "workspace.toml"
    if any(char not in _PUBLIC_PATH_CHARS for char in value):
        return "workspace.toml"
    if "\\" in value or (len(value) >= 2 and value[1] == ":"):
        return "workspace.toml"
    try:
        candidate = PurePosixPath(value)
    except Exception:
        return "workspace.toml"
    if candidate.is_absolute() or value != candidate.as_posix():
        return "workspace.toml"
    if not candidate.parts or any(
        part in {"", ".", ".."} or part.endswith(":") for part in candidate.parts
    ):
        return "workspace.toml"
    return value


def _public_canonical_slug(path: object) -> str:
    public_path = _public_canonical_path(path)
    if public_path.startswith("spec/") and public_path.count("/") == 1:
        return public_path.removeprefix("spec/")
    if (
        public_path.startswith("docs/specs/")
        and public_path.endswith("/spec.md")
        and public_path.count("/") == 3
    ):
        return public_path.split("/")[2]
    return public_path


def _is_public_slug_segment(value: object) -> bool:
    if not isinstance(value, str) or not 1 <= len(value) <= 200:
        return False
    slug_chars = _PUBLIC_PATH_CHARS - frozenset("./")
    return value[0] in slug_chars - frozenset("_-") and all(
        char in slug_chars for char in value
    )


def _is_public_ini_slug(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 7
        and value.startswith("ini-")
        and value[4:].isascii()
        and value[4:].isdigit()
    )


def _public_ini_slug(value: object, *, allow_empty: bool = False) -> str:
    if allow_empty and value == "":
        return ""
    return value if _is_public_ini_slug(value) else "workspace"


def _public_work_path(value: object) -> str:
    public_path = _public_canonical_path(value)
    parts = public_path.split("/")
    if (
        len(parts) == 2
        and parts[0] == "spec"
        and _is_public_slug_segment(parts[1])
    ):
        return public_path
    if (
        len(parts) == 4
        and parts[:2] == ["docs", "specs"]
        and _is_public_slug_segment(parts[2])
        and parts[3] == "spec.md"
    ):
        return public_path
    return "workspace.toml"


def _public_need(value: object) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 1000:
        return "workspace.toml"
    parts = value.split(":")
    if len(parts) == 2:
        prefix, target = parts
        if prefix in {"shape", "research", "strategy", "backlog"}:
            return value if _is_public_slug_segment(target) else "workspace.toml"
        if prefix == "work":
            return value if _public_work_path(target) == target else "workspace.toml"
        if prefix == "brief":
            return value if _public_brief_path(target) == target else "workspace.toml"
    if (
        len(parts) == 3
        and _is_public_ini_slug(parts[0])
        and parts[1] == "work"
        and _public_work_path(parts[2]) == parts[2]
    ):
        return value
    return "workspace.toml"


def _public_needs(values: object) -> list[str]:
    if not isinstance(values, list):
        return ["workspace.toml"]
    return [_public_need(value) for value in values]


def _public_brief_path(value: object, *, allow_empty: bool = False) -> str:
    if allow_empty and value == "":
        return ""
    public_path = _public_canonical_path(value)
    parts = public_path.split("/")
    if (
        len(parts) == 4
        and parts[:3] == ["docs", "product", "briefs"]
        and parts[3].endswith(".md")
        and _is_public_slug_segment(parts[3].removesuffix(".md"))
    ):
        return public_path
    return "workspace.toml"


def _public_brief_paths(values: object) -> list[str]:
    if not isinstance(values, list):
        return ["workspace.toml"]
    return [_public_brief_path(value) for value in values]


def _public_brief_queue_path(value: object, *, allow_empty: bool = False) -> str:
    if allow_empty and value == "":
        return ""
    public_path = _public_canonical_path(value)
    parts = public_path.split("/")
    if (
        len(parts) == 2
        and parts[0] == "briefs"
        and _is_public_slug_segment(parts[1])
    ):
        return public_path
    return _public_brief_path(value, allow_empty=allow_empty)


def _public_brief_queue_paths(values: object) -> list[str]:
    if not isinstance(values, list):
        return ["workspace.toml"]
    return [_public_brief_queue_path(value) for value in values]


def _canonical_finding_dict(f) -> dict:
    return {
        "code": f.code,
        "path": _public_canonical_path(f.path),
        "dispatchable": f.dispatchable,
        "next_action": f.next_action,
    }


def _captured_projection(root: Path, cooled: frozenset[Path]) -> dict:
    """The `captured` object, from the directory listing and cooled set only."""
    listing = _engine.list_captured_items(root, cooled)
    findings = []
    for found in listing.findings:
        item = {
            "code": found.code,
            "path": found.path,
            "dispatchable": found.dispatchable,
            "next_action": found.next_action,
        }
        if found.code == "invalid_captured_item":
            item["field"] = found.detail
        findings.append(item)
    return {"items": listing.items, "findings": findings}


def _canonical_failure_payload(mode: str, code: str = "configuration_mismatch") -> dict:
    next_actions = {
        "configuration_mismatch": (
            "Install or select a consistent versioned configuration, then rerun."
        ),
        "invalid_workspace": "Correct workspace.toml, then rerun reconciliation.",
        "unsafe_path": "Replace linked or aliased workspace input, then rerun.",
    }
    finding = {
        "code": code,
        "path": "workspace.toml",
        "dispatchable": False,
        "next_action": next_actions.get(code, next_actions["configuration_mismatch"]),
    }
    return {
        "schema_version": 1,
        "mode": mode,
        "workspace_present": True,
        "workspace_root": ".",
        "canonical": {
            "performed": True,
            "bounded": mode != "reconcile",
            "findings": [finding],
            "evaluations": [],
            "legacy_memberships": [],
            "ready": [],
            "active": [],
            "blocked": [{
                "path": "workspace.toml",
                "slug": "workspace.toml",
                "kind": "workspace",
                "ini_slug": "workspace",
                "collection": "workspace",
                "dispatchable": False,
                "findings": [finding],
            }],
        },
    }


def _canonical_evaluation_dict(e) -> dict:
    result = {
        "path": _public_canonical_path(e.entry.path),
        "slug": _public_canonical_slug(e.entry.path),
        "kind": e.entry.kind,
        "ini_slug": e.ini_slug,
        "collection": e.collection,
        "dispatchable": e.dispatchable,
        "findings": [_canonical_finding_dict(f) for f in e.findings],
    }
    if getattr(e.entry, "surface_role", None) is not None:
        result["surface_role"] = e.entry.surface_role
    if getattr(e.entry, "locator", None) is not None:
        result["locator"] = {
            "kind": e.entry.locator.kind,
            "value": e.entry.locator.value,
        }
    if getattr(e, "authority_status", None) is not None:
        authority_status = dict(e.authority_status)
        if set(result).intersection(authority_status):
            raise ValueError("authority status overlaps canonical evaluation fields")
        result.update(authority_status)
    return result


def _canonical_legacy_dict(m, workspace_bytes: bytes | None = None) -> dict:
    result = {
        "path": _public_canonical_path(m.entry.path),
        "slug": _public_canonical_slug(m.entry.path),
        "kind": m.entry.kind,
        "ini_slug": m.ini_slug,
        "collection": m.collection,
        "dispatchable": False,
        "findings": [_canonical_finding_dict(m.entry.finding)],
    }
    if workspace_bytes is not None:
        result["migration"] = build_migration_finding(workspace_bytes, m)
    return result


def _is_work_spec_item(item: dict) -> bool:
    return item.get("kind") == "spec" and str(item.get("collection", "")).startswith("work.")


def _cooling_selection(result, mode: str) -> tuple[frozenset[Path], tuple]:
    """Return the cooled set and its resolution findings for one mode.

    The two travel together because they are one decision. `repair-plan` and
    `repair-apply` predate cooling and keep their original behaviour, which
    means both an empty cooled set and no cooling findings; returning them
    separately let a caller
    suppress the exclusion while still emitting findings about it.
    """
    if mode not in {"status", "reconcile", "explain"}:
        return frozenset(), ()
    return result.cooled, tuple(result.cooling_findings)


def _canonical_projection(
    root: Path,
    result,
    cooled: frozenset[Path],
    cooling_findings: tuple = (),
) -> dict:
    """Build canonical dispatch data using the caller's cooling selection."""
    workspace_bytes = _migration_read_bytes(root, "workspace.toml")
    if workspace_bytes is None:
        raise UnsafeMigrationPathError
    workspace = tomllib.loads(workspace_bytes.decode("utf-8"))
    canonical = run_canonical_reconciliation(workspace, root, cooled)
    evaluations = [_canonical_evaluation_dict(e) for e in canonical.evaluations]
    legacy_memberships = [
        _canonical_legacy_dict(m, workspace_bytes) for m in canonical.legacy_memberships
    ]
    return {
        "performed": True,
        "bounded": not result.global_scan_performed,
        "input_identity": canonical_repository_identity(workspace, canonical, root),
        # Cooling findings are raised while resolving the cooled set, before
        # this reconciliation runs, so they have no other route to the emitted
        # surface. Six criteria name `canonical.findings` as their observable.
        "findings": [
            _canonical_finding_dict(f)
            for f in (*cooling_findings, *canonical.findings)
        ],
        "evaluations": evaluations,
        "legacy_memberships": legacy_memberships,
        "ready": [
            item
            for item in evaluations
            if item["dispatchable"]
            and item["kind"] == "spec"
            and item["collection"] == "work.queue"
        ],
        "active": [
            item
            for item in evaluations
            if item["kind"] == "spec"
            and item["collection"] == "work.active"
            and not item["findings"]
        ],
        "blocked": [
            item
            for item in evaluations
            if not item["dispatchable"] and item["findings"]
        ]
        + legacy_memberships,
    }


def _explain_selector_targets(selector: str) -> tuple[str, str] | None:
    """Return the canonical work path and legacy spelling for a confined selector."""
    if not isinstance(selector, str) or not selector or len(selector) > 240:
        return None
    if "\\" in selector or (len(selector) >= 2 and selector[1] == ":"):
        return None
    parts = selector.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None

    if len(parts) == 1:
        slug = parts[0]
    elif len(parts) == 2 and parts[0] == "spec":
        slug = parts[1]
    elif (
        (len(parts) == 3 and parts[:2] == ["docs", "specs"])
        or (
            len(parts) == 4
            and parts[:2] == ["docs", "specs"]
            and parts[3] == "spec.md"
        )
    ):
        slug = parts[2]
    else:
        return None

    if (
        not slug
        or len(slug) > 200
        or not slug[0].isalnum()
        or any(not (char.isascii() and (char.isalnum() or char in "_-")) for char in slug)
    ):
        return None
    return f"docs/specs/{slug}/spec.md", f"spec/{slug}"


def _canonical_explain(root: Path, result, selector: str) -> tuple[str, dict]:
    """Explain one canonical work entry using canonical-only resolution.

    The `spec/<slug>` selector spelling still maps to the canonical path through
    `_explain_selector_targets`. Legacy memberships are always empty after the
    ordinary-reader removal, so only `evaluations` is searched.
    """
    normalized_selector = selector
    if selector.endswith("/"):
        directory_parts = selector[:-1].split("/")
        if len(directory_parts) == 3 and directory_parts[:2] == ["docs", "specs"]:
            normalized_selector = selector[:-1]
    targets = _explain_selector_targets(normalized_selector)
    public_selector = _public_canonical_path(normalized_selector)
    if targets is None:
        return public_selector, {"selector_status": "not_found"}

    canonical_path, _legacy_path = targets
    projection = _canonical_projection(root, result, *_cooling_selection(result, "explain"))
    candidates = [
        item
        for item in projection["evaluations"]
        if item["kind"] == "spec"
        and str(item["collection"]).startswith("work.")
        and item["path"] == canonical_path
    ]
    by_initiative: dict[str, list[dict]] = {}
    for candidate in candidates:
        by_initiative.setdefault(candidate["ini_slug"], []).append(candidate)

    if not by_initiative:
        matching_findings = [
            finding
            for finding in projection["findings"]
            if finding["path"] == canonical_path
        ]
        if matching_findings:
            return public_selector, {
                "selector_status": "not_found",
                "findings": matching_findings,
            }
        return public_selector, {"selector_status": "not_found", "findings": []}
    if len(by_initiative) > 1:
        return public_selector, {
            "selector_status": "ambiguous",
            "matches": [
                {"path": items[0]["path"], "ini_slug": ini_slug}
                for ini_slug, items in sorted(by_initiative.items())
            ],
        }

    ini_slug, matches = next(iter(by_initiative.items()))
    priority = {"work.active": 0, "work.shipped": 1, "work.queue": 2}
    item = min(matches, key=lambda candidate: priority.get(candidate["collection"], 3))
    collection = item["collection"]
    if collection == "work.active":
        classification = "active"
    elif collection == "work.shipped":
        classification = "shipped"
    elif item["dispatchable"]:
        classification = "ready"
    else:
        classification = "blocked"
    finding_codes = [finding["code"] for finding in item["findings"]]
    return public_selector, {
        "selector_status": "matched",
        "explained_item": {
            "path": item["path"],
            "slug": item["slug"],
            "ini_slug": ini_slug,
            "list": collection.removeprefix("work."),
            "classification": classification,
            "blocking_needs": finding_codes,
            "dependencies": [],
            "downstream_unblocked": [],
            "dispatchable": item["dispatchable"],
            "findings": item["findings"],
        },
    }


def _brief_queue_dict(bq) -> dict | None:
    if bq is None:
        return None
    return {
        "executing": _public_brief_queue_path(bq.executing, allow_empty=True),
        "ready": _public_brief_queue_paths(bq.ready),
        "draft": _public_brief_queue_paths(bq.draft),
        "shipped": _public_brief_queue_paths(bq.shipped),
        "withdrawn": _public_brief_queue_paths(bq.withdrawn),
        "cancelled": _public_brief_queue_paths(bq.cancelled),
    }


def _scan_dict(result) -> dict:
    return {
        "global_spec_scan_performed": result.global_scan_performed,
        "workspace_files_read": 1,
        "declared_spec_files_read": result.declared_spec_files_read,
        "global_scan_spec_files_read": result.global_scan_files_read,
    }


def _projected_locator(value: object) -> str | None:
    """Return a locator safe to render, or None when it cannot be shown.

    `_public_canonical_path` degrades anything outside its charset to the
    literal `workspace.toml`. For a finding path that is a safe fallback; for a
    record locator it is a lie — the artifact is excluded correctly while the
    projection names a different, real file. The record contract admits any
    non-control character up to 1000 bytes, so this case is reachable.
    """
    public = _public_canonical_path(value)
    return public if public == value else None


def _cooling_projection(result) -> dict:
    """Project validated lifecycle records using the analysis-time clock."""
    records: list[dict] = []
    due: list[dict] = []
    exceptions: list[dict] = []
    unreadable_records: list = []
    for record in result.cooling_records:
        # `cooling_module` is never None here: a record can only exist because
        # the module that parsed it loaded. The guard proves `is_due` exists and
        # is callable, not that it returns rather than raises — the module may
        # be an older cooling.py from an installed skills tree. A raise here
        # left the whole run as `configuration_mismatch` and exit 2.
        try:
            due_now = (
                record.post_closeout_result not in {"Retired", "Reclassified"}
                and result.cooling_module.is_due(record, result.now).due
            )
        except Exception:
            # Degrading to "not due" silently under-reported the maintainer's
            # queue while `cooling_context_visible` still claimed a clean run.
            # This arm flips `cooling_context_visible` through `dueness_failed`,
            # withholds the affirmative, and emits no finding naming the record.
            due_now = False
            unreadable_records.append(record)
        records.append({
            "delivery_id": record.delivery_id,
            "locator": _projected_locator(record.locator),
            "disposition": record.disposition,
            "post_closeout_result": record.post_closeout_result,
            "completion_event": record.completion_event,
            "completion_evidence_ref": record.completion_evidence_ref,
            "review_on": record.review_on.isoformat(),
            "due": due_now,
        })
        if due_now:
            due.append({
                "delivery_id": record.delivery_id,
                "locator": _projected_locator(record.locator),
                "review_on": record.review_on.isoformat(),
            })
        # Gate on the post-closeout result, not on `exception is not None`.
        # `retain-exception` makes the block mandatory, so presence alone would
        # also admit ("retain-exception", "Retired") — a settled record that
        # must contribute nothing. `ExternalAdvisory` is the other live
        # obligation and was dropped entirely, losing its owner, reason and date.
        if (
            record.post_closeout_result in {"Retained", "ExternalAdvisory"}
            and record.exception is not None
        ):
            exception = dict(record.exception)
            exceptions.append({
                "delivery_id": record.delivery_id,
                "locator": _projected_locator(record.locator),
                "owner_role": exception["owner_role"],
                "reason": exception["reason"],
                "review_on": exception["review_on"],
            })
    return {
        "due_count": len(due),
        "due": due,
        "records": records,
        "exceptions": exceptions,
        "_unreadable": tuple(unreadable_records),
    }


def _surviving_work(
    initiative: Any, cooled_positions: set[tuple[str, int]]
) -> tuple[list, list]:
    """Return the single derivation both closeout consumers read.

    `cooled_positions` carries reconciliation's `(collection, entry_index)`
    verdict for this initiative. Position is matched rather than any value the
    entry holds, because no value is unique: a legacy `"spec/x"` string and a
    canonical `{path = "spec/x", kind = "defect"}` entry share a raw path, and an
    entry the canonical layer rejects still arrives here through this parse and
    can reproduce any `(path, kind)` pair. Matching a value therefore drops a
    live entry that merely resembles a cooled one, and closeout then advertises
    shippedness for an initiative that still has work.

    The two sides agree by construction: reconciliation walks
    `enumerate(entries)` over each lifecycle array, and these lists are built by
    comprehension over those same arrays, one entry per element.
    """
    return (
        [
            entry
            for index, entry in enumerate(initiative.work.queue)
            if ("work.queue", index) not in cooled_positions
        ],
        [
            entry
            for index, entry in enumerate(initiative.work.active)
            if ("work.active", index) not in cooled_positions
        ],
    )


def _closeout_projection(
    result,
    cooled_by_initiative: dict[str, set[tuple[str, int]]],
    *,
    dueness_failed: bool = False,
    canonical_shaping_records: list[dict],
) -> dict | None:
    """Project the first active or paused initiative's closeout facts, by slug.

    Returns None when no initiative is active or paused. There is no closeout
    state to project then, and synthesizing one from the absent initiative
    reported `unshipped-specs` against a workspace whose initiatives are all
    closed — a blocker naming work that does not exist. The block is omitted
    rather than emitted empty, which leaves the closed-workspace key set
    untouched.
    """
    active = sorted(
        (
            initiative
            for initiative in result.initiatives
            if initiative.status in {"active", "paused"}
        ),
        key=lambda initiative: initiative.slug,
    )
    if not active:
        return None
    initiative = active[0]
    paused = initiative.status == "paused"
    surviving_queue, surviving_active = _surviving_work(
        initiative, cooled_by_initiative.get(initiative.slug, set())
    )
    all_specs_shipped = not (surviving_queue or surviving_active)
    # A record whose dueness could not be judged is an incomplete run just as
    # a record that would not load is, so it flips the same claim. One blocker
    # is enough to withhold the affirmative: eligibility is
    # `all_specs_shipped and not blockers and not paused`.
    cooling_context_visible = bool(result.cooling_findings) or dueness_failed
    # `spec_path` is `entry.path` straight from workspace.toml with no charset
    # rule, and this string is rendered into agent context. Every sibling
    # emitter bounds its path through this same filter.
    blockers = [
        f"type{finding.finding_type}:{_public_canonical_path(finding.spec_path)}"
        for finding in result.reconciliation
        if finding.ini_slug == initiative.slug and finding.finding_type in {2, 3}
    ]
    # Shaping residue is read from the reconciled canonical evaluations, never
    # from `initiative.shaping`: that list is built from the raw TOML with no
    # cooling filter, so reading it would count a cooled entry as residue. An
    # open entry no canonical parse accepted appears in neither source, so
    # `has_unsupported_open_entry` keeps it from passing as an empty initiative.
    #
    # `brief_queue` has no such split. `.shipped`, `.withdrawn` and `.cancelled`
    # are terminal and are not residue. The brief *dependency* terminal set is
    # deliberately not reused here: it counts `Ready` and `Executing` as
    # terminal, which answers "is this dependency satisfied", not "is this
    # brief closed".
    brief_queue = initiative.brief_queue
    shaping_residue = any(
        record["ini_slug"] == initiative.slug
        and record["collection"] in {"shaping_queue.active", "shaping_queue.backlog"}
        for record in canonical_shaping_records
    )
    if (
        shaping_residue
        or initiative.has_unsupported_open_entry
        or (
            brief_queue is not None
            and (brief_queue.executing or brief_queue.ready or brief_queue.draft)
        )
    ):
        blockers.append("initiative-residue")
    if cooling_context_visible:
        blockers.append("cooling-context-incomplete")
    projection = project_closeout_status(
        paused=paused,
        all_specs_shipped=all_specs_shipped,
        closeout_blockers=blockers,
        cooling_context_visible=cooling_context_visible,
    )
    return dataclasses.asdict(projection)


def _build_json(root: Path, result, mode: str) -> dict:
    # initiatives/work.active/work.shipped are filtered to active initiatives only;
    # reconciliation.* spans all initiatives (including paused/closed) — mirroring analyze().
    # A type2_cleanup_ops entry may therefore reference an ini_slug absent from initiatives[].
    initiatives_out: list[dict] = []
    shipped_entries: list[dict] = []
    # active_shaping_entries: per-entry provenance for shaping_queue.active.
    # Includes ALL active entries (signals and non-signals) so that shape: dep
    # resolution matches the engine's is_need_satisfied, which checks all active
    # entries regardless of type. Each entry carries ini_slug to avoid cross-initiative
    # slug collisions (two initiatives may share an initiative-scoped shaping slug).
    # Reconciliation's cooled membership positions, read from the same workspace
    # bytes it parses. Closeout consumes those positions rather than re-deriving
    # an artifact path, or matching any value an entry carries.
    workspace_bytes = _migration_read_bytes(root, "workspace.toml")
    if workspace_bytes is None:
        raise UnsafeMigrationPathError
    cooled_by_initiative = cooled_work_entry_paths(
        tomllib.loads(workspace_bytes.decode("utf-8")), root, result.cooled
    )
    active_shaping_entries: list[dict] = []
    for ini in result.initiatives:
        if ini.status != "active":
            continue
        surviving_queue, _ = _surviving_work(
            ini, cooled_by_initiative.get(ini.slug, set())
        )
        initiatives_out.append({
            "slug": _public_ini_slug(ini.slug),
            # `workspace.toml` is working material for developers in the same
            # repository, carrying the same trust as the source beside it, so
            # its display prose projects as authored. `str()` coerces rather
            # than validates: a non-string here is an authoring error, and
            # reporting what arrived beats reconstructing TOML syntax.
            "name": str(ini.name),
            "status": ini.status if ini.status in {"active", "paused", "closed"} else "invalid",
            "milestone": str(ini.milestone),
            "brief_queue": _brief_queue_dict(ini.brief_queue),
            "queue_empty": len(surviving_queue) == 0,
        })
        for e in ini.work.shipped:
            shipped_entries.append(_work_entry_dict(e, ini.slug))
        for e in ini.shaping.active:
            active_shaping_entries.append({
                "slug": e.slug,
                "ini_slug": _public_ini_slug(ini.slug),
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
        op["ini_slug"] = _public_ini_slug(op.get("ini_slug"))
        op["path"] = _public_canonical_path(op.get("path"))
        type2_cleanup_ops.append(op)

    types_performed = [1, 2, 3] if result.global_scan_performed else [2, 3]

    canonical = _canonical_projection(root, result, *_cooling_selection(result, mode))
    canonical_failed = any(
        finding["code"] in {"invalid_workspace", "configuration_mismatch"}
        for finding in canonical["findings"]
    )
    if canonical_failed:
        type2_cleanup_ops = []
    output = {
        "schema_version": 1,
        "mode": mode,
        "workspace_present": True,
        "workspace_root": ".",
        "scan": _scan_dict(result),
        "initiatives": initiatives_out,
        "work": {
            "ready": canonical["ready"],
            "blocked": [item for item in canonical["blocked"] if _is_work_spec_item(item)],
            "active": canonical["active"],
            "shipped": shipped_entries,
        },
        "shaping": {
            "ready": [] if canonical_failed else [
                _shaping_dict(c) for c in result.ready_shaping
            ],
            "signals": [] if canonical_failed else [
                _shaping_dict(c) for c in result.signals
            ],
            "blocked": [] if canonical_failed else [
                _shaping_dict(c) for c in result.blocked_shaping
            ],
            "active_entries": [] if canonical_failed else active_shaping_entries,
            # [backlog].open typed entries (workspace-level, not per-initiative).
            # work-loop's shaping-item guard checks this list for slug matches.
            "top_level_backlog": [] if canonical_failed else [
                _shaping_entry_dict(e) for e in result.top_level_backlog
            ],
        },
        "repo_backlog": {
            "open": [_repo_backlog_entry_dict(e) for e in result.repo_backlog],
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
        "canonical": canonical,
        "diagnostics": {
            "workspace_files_read": 1,
            "spec_files_read": result.files_read,
        },
    }
    if mode in {"status", "reconcile"}:
        output["captured"] = _captured_projection(root, result.cooled)
        cooling = _cooling_projection(result)
        unreadable = cooling.pop("_unreadable")
        output["cooling"] = cooling
        closeout = _closeout_projection(
            result,
            cooled_by_initiative,
            dueness_failed=bool(unreadable),
            canonical_shaping_records=canonical["evaluations"],
        )
        if closeout is not None:
            output["closeout"] = closeout
    return output


def _build_explain_json(root: Path, result, selector: str, explain_result: dict) -> dict:
    return {
        "schema_version": 1,
        "mode": "explain",
        "workspace_present": True,
        "workspace_root": ".",
        "scan": _scan_dict(result),
        "selector": selector,
        "canonical": _canonical_projection(
            root, result, *_cooling_selection(result, "explain")
        ),
        **explain_result,
    }


def _build_repair_plan_json(
    root: Path, result, plan, workspace_bytes: bytes | None = None
) -> dict:
    base = _build_json(root, result, "repair-plan")
    canonical_failed = any(
        finding["code"] in {"invalid_workspace", "configuration_mismatch"}
        for finding in base["canonical"]["findings"]
    )
    automatic_operations: list[dict] = []
    for operation in [] if canonical_failed else plan.automatic_operations:
        item = dataclasses.asdict(operation)
        public_path = _public_canonical_path(item["spec_path"])
        item["ini_slug"] = _public_ini_slug(item["ini_slug"])
        item["spec_path"] = public_path
        item["finding_id"] = (
            f"type2:{item['ini_slug']}:queue:{public_path}"
        )
        operation_content = {
            key: value for key, value in item.items() if key != "operation_id"
        }
        item["operation_id"] = hashlib.sha256(json.dumps(
            operation_content,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")).hexdigest()
        automatic_operations.append(item)
    manual_findings: list[dict] = []
    for finding in [] if canonical_failed else plan.manual_findings:
        item = dataclasses.asdict(finding)
        public_path = _public_canonical_path(item["spec_path"])
        item["ini_slug"] = _public_ini_slug(item["ini_slug"], allow_empty=True)
        item["spec_path"] = public_path
        item["finding_id"] = (
            f"type{item['finding_type']}:{item['ini_slug']}:"
            f"{item['list_name']}:{public_path}"
        )
        manual_findings.append(item)
    if not canonical_failed:
        if workspace_bytes is None:
            workspace_bytes = _migration_read_bytes(root, "workspace.toml")
        if workspace_bytes is None:
            raise UnsafeMigrationPathError
        needs_operations, needs_findings = _build_needs_operations(root, workspace_bytes)
        automatic_operations.extend(needs_operations)
        manual_findings.extend(needs_findings)
        captured_operations, captured_findings = _build_captured_operations(
            root, workspace_bytes
        )
        automatic_operations.extend(captured_operations)
        manual_findings.extend(captured_findings)
        automatic_operations.extend(_build_drop_operations(workspace_bytes))
    base["workspace_fingerprint"] = plan.workspace_fingerprint
    base["automatic_operations"] = automatic_operations
    base["manual_findings"] = manual_findings
    base["plan_id"] = _recompute_plan_id(base)
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
        if op_type in _NEEDS_OPERATION_TYPES:
            needs_reason = _validate_needs_operation(op)
            if needs_reason:
                return needs_reason
            continue
        if op_type == _CAPTURED_TO_FILE:
            captured_reason = _validate_captured_operation(op)
            if captured_reason:
                return captured_reason
            continue
        if op_type == _INTENT_BRIEF_DROP:
            drop_reason = _validate_drop_operation(op)
            if drop_reason:
                return drop_reason
            continue
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
    edge_report: dict | None = None,
) -> tuple[int, list[dict], bytes | None]:
    """Apply automatic operations using tomlkit. Returns (applied, per_operation, written_bytes).

    written_bytes is the UTF-8 content written to workspace_path, or None when no
    operations were applied (caller should use before_digest as after_digest in that case).
    """
    import stat

    import tomlkit  # noqa: PLC0415 — guarded CLI-only import

    doc = tomlkit.parse(workspace_toml_bytes.decode("utf-8"))
    applied = 0
    per_op: list[dict] = []
    applied_spec_checks: list[tuple[str, str, str, Path, str, str | None]] = []
    needs_operations = [
        op for op in operations if op.get("operation_type") in _NEEDS_OPERATION_TYPES
    ]
    captured_operations = [
        op for op in operations if op.get("operation_type") == _CAPTURED_TO_FILE
    ]
    drop_operations = [
        op for op in operations if op.get("operation_type") == _INTENT_BRIEF_DROP
    ]
    operations = [
        op for op in operations
        if op.get("operation_type")
        not in _NEEDS_OPERATION_TYPES | {_CAPTURED_TO_FILE, _INTENT_BRIEF_DROP}
    ]
    # Every drop locator is checked against the registry read under the lock, and
    # bound to its entry object, before any operation below changes `doc`.
    bound_drops, drop_refusals = _bind_drop_entries(doc, workspace_toml_bytes, drop_operations)
    per_op.extend(drop_refusals)
    # Re-derived before any write of this run, so a source an earlier operation
    # in the same plan rewrites cannot change what the records are checked against.
    captured_plan = (
        _plan_captured_items(root, workspace_toml_bytes) if captured_operations else None
    )

    for op in operations:
        spec_path = op["spec_path"]
        public_spec_path = _public_work_path(spec_path)
        ini_slug = op["ini_slug"]
        expected_status = op["spec_status"]
        expected_fp = op.get("spec_status_fingerprint", "")

        # Confinement + re-verify spec status from disk
        slug = _spec_slug_from_workspace_path(spec_path)
        spec_file = _safe_spec_path(root, slug)
        if spec_file is None:
            per_op.append(
                {"path": public_spec_path, "applied": False, "reason": "spec_status_unreadable"}
            )
            continue
        current_status, current_fp = extract_spec_status_with_fingerprint(spec_file)
        if current_status is None:
            per_op.append(
                {"path": public_spec_path, "applied": False, "reason": "spec_status_unreadable"}
            )
            continue
        if current_status != expected_status:
            per_op.append({
                "path": public_spec_path,
                "applied": False,
                "reason": "spec_status_changed",
            })
            continue
        # Fingerprint check: detect changes to the status line that keep the token the same
        if expected_fp and current_fp and current_fp != expected_fp:
            per_op.append(
                {
                    "path": public_spec_path,
                    "applied": False,
                    "reason": "spec_status_fingerprint_changed",
                }
            )
            continue

        # Re-derive action from verified disk status (do not trust plan's operation_type)
        if current_status == "Shipped":
            effective_op_type = "queue-to-shipped"
        elif current_status == "Archived":
            effective_op_type = "queue-remove"
        else:
            per_op.append({
                "path": public_spec_path,
                "applied": False,
                "reason": "spec_status_changed",
            })
            continue
        still_eligible, _eligibility_reason = _repair_entry_eligibility(
            workspace_path,
            ini_slug,
            spec_path,
            effective_op_type,
        )
        if not still_eligible:
            per_op.append({
                "path": public_spec_path,
                "applied": False,
                "reason": "canonical_repair_ineligible",
            })
            continue

        ini_section = doc.get(ini_slug)
        if ini_section is None:
            per_op.append({
                "path": public_spec_path,
                "applied": False,
                "reason": "initiative_not_found",
            })
            continue
        work = ini_section.get("work", {})
        queue = work.get("queue", [])

        # In-place removal: find and delete first matching entry
        removed = False
        moved_entry = None
        structured_refused = False
        for i, entry in enumerate(queue):
            entry_path = (
                entry
                if isinstance(entry, str)
                else entry.get("path", "") if isinstance(entry, dict) else ""
            )
            if entry_path == spec_path:
                if effective_op_type == "queue-to-shipped" and not isinstance(entry, dict):
                    structured_refused = True
                    break
                moved_entry = entry
                del queue[i]
                removed = True
                break

        if structured_refused:
            per_op.append({
                "path": public_spec_path,
                "applied": False,
                "reason": "structured_entry_required",
            })
            continue

        if not removed:
            per_op.append(
                {"path": public_spec_path, "applied": False, "reason": "entry_not_found_in_queue"}
            )
            continue

        if effective_op_type == "queue-to-shipped":
            if "shipped" not in work:
                work["shipped"] = tomlkit.array()
            shipped = work["shipped"]
            existing = {
                e if isinstance(e, str) else e.get("path", "") if isinstance(e, dict) else ""
                for e in shipped
            }
            if spec_path not in existing:
                shipped.append(moved_entry)

        per_op.append({"path": public_spec_path, "applied": True})
        applied_spec_checks.append((
            ini_slug,
            spec_path,
            effective_op_type,
            spec_file,
            current_status,
            current_fp,
        ))
        applied += 1

    # Waiting files are replaced first, one atomic replace each; `needs` is
    # cleared in the one workspace.toml write below, only for operations that
    # applied. An interruption in between leaves `needs` in place.
    if needs_operations:
        needs_per_op, needs_applied, report = _apply_needs_operations(
            root, doc, workspace_toml_bytes, needs_operations
        )
        per_op.extend(needs_per_op)
        applied += needs_applied
        if edge_report is not None:
            edge_report.update(report)

    # Records are created first; `doc` is written once below, so an interruption
    # between the two leaves records that the rerun re-derives and keeps.
    if captured_plan is not None:
        captured_per_op, captured_applied, captured_report = _apply_captured_operations(
            root, doc, captured_operations, captured_plan
        )
        per_op.extend(captured_per_op)
        applied += captured_applied
        if edge_report is not None:
            for key in ("header_edges_before", "header_edges_after"):
                captured_report[key] = edge_report.get(key, []) + captured_report[key]
            edge_report.update(captured_report)

    # Drops run last, so each sees the `needs` its own run cleared.
    drop_per_op, drop_applied = _apply_bound_drops(bound_drops)
    per_op.extend(drop_per_op)
    applied += drop_applied

    # Only write when at least one operation succeeded
    if applied == 0:
        return applied, per_op, None

    serialized = tomlkit.dumps(doc)
    if serialized.encode("utf-8") == workspace_toml_bytes:
        return applied, per_op, None
    written_bytes = serialized.encode("utf-8")
    tmp_path = None
    try:
        orig_mode = stat.S_IMODE(workspace_path.stat().st_mode)
        fd, tmp_path = tempfile.mkstemp(
            dir=workspace_path.parent,
            prefix=".workspace.toml.",
            suffix=".tmp",
        )
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(serialized)
            fh.flush()
            os.fsync(fh.fileno())
        # Preserve original mode; set after fd close (cross-platform — os.fchmod is Unix-only)
        Path(tmp_path).chmod(orig_mode)
        # Re-hash immediately before replace to detect concurrent writes that
        # occurred between the under-lock fingerprint read (caller) and here.
        _precheck = workspace_path.read_bytes()
        _precheck_fp = hashlib.sha256(_precheck).hexdigest()
        _expected_fp = hashlib.sha256(workspace_toml_bytes).hexdigest()
        if _precheck_fp != _expected_fp:
            raise RuntimeError("workspace_concurrent_write")
        for (
            _ini_slug,
            _spec_path,
            _op_type,
            _spec_file,
            _observed_status,
            _observed_fp,
        ) in applied_spec_checks:
            _live_status, _live_fp = extract_spec_status_with_fingerprint(_spec_file)
            if (
                _live_status is None
                or _live_status != _observed_status
                or _live_fp != _observed_fp
            ):
                raise RuntimeError("workspace_concurrent_write")
            _still_eligible, _eligibility_reason = _repair_entry_eligibility(
                workspace_path,
                _ini_slug,
                _spec_path,
                _op_type,
            )
            if not _still_eligible:
                raise RuntimeError("workspace_concurrent_write")
        Path(tmp_path).replace(workspace_path)
        tmp_path = None
        _fsync_directory(workspace_path.parent)
    finally:
        if tmp_path is not None:
            with contextlib.suppress(OSError):
                Path(tmp_path).unlink()

    return applied, per_op, written_bytes


# ── needs-to-header repair ────────────────────────────────────────────────────
#
# `repair-plan` turns each canonical membership's typed `needs` edges into
# `Depends on:` and `Dependency receipts:` items for its waiting item, and
# `repair-apply` writes them. A cooled membership's file is never opened: its
# `needs` are dropped and reported.

_NEEDS_TO_HEADER = "needs-to-header"
_NEEDS_DROP_COOLED = "needs-drop-cooled"
_NEEDS_OPERATION_TYPES = frozenset({_NEEDS_TO_HEADER, _NEEDS_DROP_COOLED})
_NEEDS_FINDING_TYPE = 4
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_INTENTS_PARTS = ["docs", "product", "intents"]


class _NeedsRefusal(Exception):
    """One registry edge (or its waiting item) the repair will not express."""

    def __init__(self, reason: str, target: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.target = target


def _has_control_character(value: str) -> bool:
    return any(char < " " or char == "\x7f" for char in value)


def _dependency_tokens(dep) -> list[str] | None:
    """The receipt tokens a registry edge carries, or `None` when it has none."""
    if dep.type == "cross-repo":
        tokens = ["coordination", dep.kind, dep.receipt_id, dep.accepted_revision]
        if any(
            _engine._COORDINATION_TOKEN_RE.fullmatch(token) is None
            for token in tokens[2:]
        ):
            raise _NeedsRefusal("receipt-off-grammar", dep.path)
        return tokens
    receipt = dep.receipt
    if receipt is None:
        return None
    if not isinstance(receipt, dict):
        raise _NeedsRefusal("receipt-off-grammar", dep.path)
    tokens = [
        "completion",
        receipt["delivery_id"],
        receipt["outcome"],
        receipt["completion_event"],
        receipt["evidence_ref"],
    ]
    if any(
        not token or "," in token or any(char.isspace() for char in token)
        for token in tokens[1:]
    ):
        raise _NeedsRefusal("receipt-off-grammar", dep.path)
    return tokens


def _target_reference(root: Path, dep, index) -> str:
    """The typed reference for a spec, brief, or intent target, else its path."""
    path = dep.path
    parts = path.split("/")
    if dep.type == "cross-repo" or dep.kind == "brief":
        slug = next((s for s, paths in index.briefs.items() if path in paths), None)
        if slug is None:
            raise _NeedsRefusal("missing-brief-target", path)
        return f"brief:{slug}"
    if (
        dep.kind == "spec"
        and len(parts) == 4
        and parts[:2] == ["docs", "specs"]
        and parts[3] == "spec.md"
    ):
        return f"spec:{parts[2]}"
    if dep.kind == "intent" and len(parts) == 4 and parts[:3] == _INTENTS_PARTS:
        for (kind, slug), paths in index.intents.items():
            if path in paths:
                return f"{kind}:{slug}"
        file_path = _engine._confined_artifact_path(root, path)
        exists = file_path is not None and file_path.exists()
        raise _NeedsRefusal(
            "intent-target-unusable" if exists else "missing-intent-target", path
        )
    return path


def _read_single_edge(
    root: Path,
    waiting_path: str,
    reference: str,
    tokens: list[str] | None,
    index,
    kinds: dict[str, str],
    cooled: frozenset[Path],
):
    """Read one edge as the engine reads a header holding only that edge."""
    text = f"- **Depends on:** {reference}\n"
    if tokens is not None:
        text += f"- **Dependency receipts:** {reference} {' '.join(tokens)}\n"
    return _engine.header_dependencies_from_text(
        root,
        waiting_path,
        text,
        index=index,
        membership_kinds=kinds,
        cooled=cooled,
    )


def _same_edge(dep, parsed) -> str | None:
    """`None` when the engine reads `parsed` as the registry edge `dep`."""
    if parsed.type != dep.type or parsed.path != dep.path:
        return "edge-not-expressible"
    if dep.type == "cross-repo":
        same = (
            parsed.kind == dep.kind
            and parsed.containing_brief == dep.containing_brief
            and parsed.receipt_id == dep.receipt_id
            and parsed.accepted_revision == dep.accepted_revision
        )
        return None if same else "edge-not-expressible"
    if parsed.kind and parsed.kind != dep.kind:
        return "kind-mismatch"
    if parsed.receipt != dep.receipt:
        if parsed.receipt == _engine._MALFORMED_COMPLETION_RECEIPT:
            return "receipt-off-grammar"
        return "edge-not-expressible"
    return None


def _derive_needs_edges(
    root: Path,
    waiting_path: str,
    entry,
    index,
    kinds: dict[str, str],
    cooled: frozenset[Path],
) -> list[tuple[str, list[str] | None]]:
    """Derive `(reference, receipt tokens)` for each registry edge, in order.

    Raises `_NeedsRefusal` for an edge the header cannot hold as the same edge.
    """
    edges: list[tuple[str, list[str] | None]] = []
    seen: dict[str, list[str] | None] = {}
    for dep in entry.needs:
        if dep.type == "cross-repo" and dep.path != dep.containing_brief:
            raise _NeedsRefusal("cross-repo-path-mismatch", dep.path)
        tokens = _dependency_tokens(dep)
        reference = _target_reference(root, dep, index)
        if dep.type == "local" and reference == dep.path and tokens is not None:
            raise _NeedsRefusal("captured-item-receipt", dep.path)
        if reference in seen:
            if seen[reference] != tokens:
                raise _NeedsRefusal("duplicate-reference", dep.path)
            continue
        parsed = _read_single_edge(
            root, waiting_path, reference, tokens, index, kinds, cooled
        )
        if parsed.findings or len(parsed.dependencies) != 1:
            raise _NeedsRefusal("edge-not-expressible", dep.path)
        reason = _same_edge(dep, parsed.dependencies[0])
        if reason is not None:
            raise _NeedsRefusal(reason, dep.path)
        seen[reference] = tokens
        edges.append((reference, tokens))
    return edges


def _best_effort_edges(entry, index) -> list[tuple[str, list[str] | None]]:
    """Registry edges for a cooled membership, which no refusal rule governs."""
    edges: list[tuple[str, list[str] | None]] = []
    for dep in entry.needs:
        try:
            reference = _target_reference(Path(), dep, index)
        except _NeedsRefusal:
            reference = dep.path
        try:
            tokens = _dependency_tokens(dep)
        except _NeedsRefusal:
            tokens = None
        edges.append((reference, tokens))
    return edges


def _edge_dicts(
    waiting_path: str, edges: list[tuple[str, list[str] | None]]
) -> list[dict]:
    return [
        {"waiting_path": waiting_path, "reference": reference, "receipt": tokens}
        for reference, tokens in edges
    ]


def _edge_key(edge: dict) -> tuple:
    receipt = edge["receipt"]
    return (
        edge["waiting_path"],
        edge["reference"],
        tuple(receipt) if receipt is not None else None,
    )


# Echo rules: each part of an echoed value is judged alone, and a part that
# fails is withheld as an empty string while the others still appear.

def _echo_path(path: object, member_paths: frozenset[str] | None) -> str:
    if not isinstance(path, str):
        return ""
    if member_paths is not None and path not in member_paths:
        return ""
    return _engine._bounded_finding_identifier(path)


def _echo_reference(reference: object) -> str:
    return _engine._echoable_reference(reference) if isinstance(reference, str) else ""


def _receipt_token_valid(keyword: str, position: int, token: object) -> bool:
    if not isinstance(token, str):
        return False
    if position == 0:
        return token in ("completion", "coordination")
    if keyword == "completion":
        if position == 1:
            return re.fullmatch(_engine._COMPLETION_RECEIPT_DELIVERY_ID_RE, token) is not None
        if position == 2:
            return token in _engine._COMPLETION_RECEIPT_OUTCOMES
        if position == 3:
            return token in _engine._COMPLETION_RECEIPT_EVENTS
        if position == 4:
            return re.fullmatch(_engine._COMPLETION_RECEIPT_EVIDENCE_REF_RE, token) is not None
        return False
    if keyword == "coordination":
        if position == 1:
            return token in ("brief", "spec")
        if position in (2, 3):
            return _engine._COORDINATION_TOKEN_RE.fullmatch(token) is not None
    return False


def _echo_tokens(tokens: object) -> list[str] | None:
    if not isinstance(tokens, list):
        return None
    keyword = tokens[0] if tokens and isinstance(tokens[0], str) else ""
    return [
        _engine._bounded_finding_identifier(token)
        if _receipt_token_valid(keyword, position, token)
        else ""
        for position, token in enumerate(tokens)
    ]


def _echo_edge(edge: dict, member_paths: frozenset[str] | None) -> dict:
    return {
        "waiting_path": _echo_path(edge.get("waiting_path"), member_paths),
        "reference": _echo_reference(edge.get("reference")),
        "receipt": _echo_tokens(edge.get("receipt")),
    }


def _echo_target(value: object) -> str:
    """A refused edge's target: a reference, or a plain repository path."""
    if not isinstance(value, str) or not value:
        return ""
    reference = _echo_reference(value)
    if reference:
        return reference
    if all(char in _PUBLIC_PATH_CHARS for char in value):
        return _engine._bounded_finding_identifier(value)
    return ""


def _echo_repair_plan(data: dict) -> dict:
    """The plan as stdout shows it; the plan file keeps every value as derived."""
    operations = data.get("automatic_operations", [])
    findings = data.get("manual_findings", [])
    if not any(
        op.get("operation_type")
        in _NEEDS_OPERATION_TYPES | {_CAPTURED_TO_FILE, _INTENT_BRIEF_DROP}
        for op in operations
    ) and not any(f.get("finding_type") == _CAPTURED_FINDING_TYPE for f in findings):
        return data
    echoed: list[dict] = []
    for op in operations:
        if op.get("operation_type") == _CAPTURED_TO_FILE:
            echoed.append(_echo_captured_operation(op))
            continue
        if op.get("operation_type") == _INTENT_BRIEF_DROP:
            echoed.append(_echo_drop_operation(op))
            continue
        if op.get("operation_type") not in _NEEDS_OPERATION_TYPES:
            echoed.append(op)
            continue
        item = dict(op)
        item["waiting_path"] = _echo_path(op["waiting_path"], None)
        for key in ("registry_edges", "dropped_cooled"):
            if key in item:
                item[key] = [_echo_edge(edge, None) for edge in op[key]]
        if "depends_on_items" in item:
            item["depends_on_items"] = [_echo_reference(i) for i in op["depends_on_items"]]
        if "receipt_items" in item:
            item["receipt_items"] = [
                " ".join(
                    [_echo_reference(receipt.split(" ", 1)[0])]
                    + (_echo_tokens(receipt.split(" ")[1:]) or [])
                )
                for receipt in op["receipt_items"]
            ]
        echoed.append(item)
    return {
        **data,
        "automatic_operations": echoed,
        "manual_findings": [
            _echo_captured_finding(f) if f.get("finding_type") == _CAPTURED_FINDING_TYPE else f
            for f in findings
        ],
    }


# ── Plan ──────────────────────────────────────────────────────────────────────

def _needs_membership_context(root: Path, workspace_bytes: bytes):
    workspace = tomllib.loads(workspace_bytes.decode("utf-8"))
    memberships = _engine._extract_canonical_memberships(workspace)[0]
    cooled, cooling_findings = _engine._resolve_cooled_state(root)
    index = _engine.build_resolution_index(root, cooled=cooled)
    kinds = {
        m.entry.path: m.entry.kind for m in memberships if m.entry.path is not None
    }
    return memberships, cooled, cooling_findings, index, kinds


def _needs_manual_finding(membership, reason: str, target: str = "") -> dict:
    path = membership.entry.path or ""
    shown = _echo_path(path, None)
    ini_slug = _public_ini_slug(membership.ini_slug, allow_empty=True)
    return {
        "finding_type": _NEEDS_FINDING_TYPE,
        "spec_path": shown,
        "spec_status": "",
        "ini_slug": ini_slug,
        "list_name": membership.collection,
        "reason": reason,
        "edge": {"waiting_path": shown, "reference": _echo_target(target)},
        "finding_id": (
            f"type{_NEEDS_FINDING_TYPE}:{ini_slug}:{membership.collection}:{shown}:{reason}"
        ),
    }


def _preamble_anchor_ok(text: str) -> bool:
    """True when no header line is followed by an indented line the engine drops."""
    return not any(
        wrapped for _name, _value, wrapped in _engine._header_field_lines(text)
    )


def _build_needs_operations(root: Path, workspace_bytes: bytes) -> tuple[list[dict], list[dict]]:
    """Plan `needs-to-header` and `needs-drop-cooled` operations."""
    memberships, cooled, cooling_findings, index, kinds = _needs_membership_context(
        root, workspace_bytes
    )
    candidates = [m for m in memberships if m.entry.path is not None and m.entry.needs]
    if not candidates:
        return [], []
    path_counts: dict[str, int] = {}
    for membership in memberships:
        if membership.entry.path is not None:
            path_counts[membership.entry.path] = path_counts.get(membership.entry.path, 0) + 1
    cooling_unavailable = any(
        finding.code == "cooling_state_unavailable" for finding in cooling_findings
    )
    operations: list[dict] = []
    manual: list[dict] = []
    for membership in candidates:
        path = membership.entry.path
        assert path is not None
        if path_counts[path] > 1:
            manual.append(_needs_manual_finding(membership, "duplicate-membership"))
            continue
        if cooling_unavailable:
            manual.append(_needs_manual_finding(membership, "cooling-state-unavailable"))
            continue
        if _engine._membership_is_cooled(membership, root, cooled):
            edges = _edge_dicts(path, _best_effort_edges(membership.entry, index))
            operations.append({
                "operation_type": _NEEDS_DROP_COOLED,
                "waiting_path": path,
                "dropped_cooled": edges,
            })
            continue
        if _has_control_character(path):
            manual.append(_needs_manual_finding(membership, "waiting-path-control-character"))
            continue
        try:
            edges_raw = _derive_needs_edges(
                root, path, membership.entry, index, kinds, cooled
            )
        except _NeedsRefusal as refusal:
            manual.append(_needs_manual_finding(membership, refusal.reason, refusal.target))
            continue
        data = _engine._migration_file_bytes(root, path)
        try:
            text = data.decode("utf-8") if data is not None else None
        except UnicodeDecodeError:
            text = None
        if data is None or text is None:
            manual.append(_needs_manual_finding(membership, "waiting-item-unreadable"))
            continue
        if not _preamble_anchor_ok(text):
            manual.append(_needs_manual_finding(membership, "waiting-item-not-writable"))
            continue
        operations.append({
            "operation_type": _NEEDS_TO_HEADER,
            "waiting_path": path,
            "waiting_sha256": hashlib.sha256(data).hexdigest(),
            "registry_edges": _edge_dicts(path, edges_raw),
            "depends_on_items": [reference for reference, _ in edges_raw],
            "receipt_items": [
                f"{reference} {' '.join(tokens)}"
                for reference, tokens in edges_raw
                if tokens is not None
            ],
        })
    return operations, manual


# ── Apply ─────────────────────────────────────────────────────────────────────

def _insert_header_items(
    text: str,
    items: list[str],
    receipts: list[tuple[str, list[str]]],
) -> tuple[str, bool]:
    """Add `items` and `receipts` to the preamble, skipping those already there.

    Returns `(new text, changed)`. Only the lines it adds or extends change. A
    preamble with no `- **Field:**` line gains them after its `# ` title and the
    blank line that follows it, or at the top when it has no title.
    """
    lines = text.splitlines(keepends=True)
    clean = list(_engine._iter_preamble_lines(text))
    present_items: set[str] = set()
    present_receipts: set[str] = set()
    last_field: int | None = None
    last_depends: int | None = None
    last_receipts: int | None = None
    for position, line in enumerate(clean):
        match = _engine._HEADER_FIELD_RE.match(line)
        if match is None:
            continue
        last_field = position
        name = match.group("name").strip().lower()
        value = match.group("value").strip()
        words = value.split()
        if name == "depends on" and words and words[0].lower() != "none":
            present_items.update(_engine._split_items(value))
            last_depends = position
        elif name == "dependency receipts":
            for receipt in _engine._split_items(value):
                tokens = receipt.split()
                if tokens:
                    present_receipts.add(tokens[0])
            if words and words[0].lower() != "none":
                last_receipts = position
    new_items = [item for item in items if item not in present_items]
    new_receipts = [
        f"{reference} {' '.join(tokens)}"
        for reference, tokens in receipts
        if reference not in present_receipts
    ]
    if not new_items and not new_receipts:
        return text, False

    def extend(position: int, additions: list[str]) -> None:
        body = lines[position].rstrip("\r\n")
        terminator = lines[position][len(body):]
        comments = [m.group(0) for m in _engine._HTML_COMMENT_RE.finditer(body)]
        head = _engine._HTML_COMMENT_RE.sub("", body)
        opened = head.find("<!--")
        if opened != -1:  # a comment that closes on a later line
            comments.append(head[opened:])
            head = head[:opened]
        tail = "".join(f" {comment}" for comment in comments)
        lines[position] = f"{head.rstrip()}, {', '.join(additions)}{tail}{terminator}"

    added: list[str] = []
    if new_items:
        if last_depends is not None:
            extend(last_depends, new_items)
        else:
            added.append(f"- **Depends on:** {', '.join(new_items)}")
    if new_receipts:
        if last_receipts is not None:
            extend(last_receipts, new_receipts)
        else:
            added.append(f"- **Dependency receipts:** {', '.join(new_receipts)}")
    eol = "\r\n" if "\r\n" in text else "\n"
    if added and last_field is None:
        at = 0
        if lines and lines[0].startswith("# "):
            at = 1
            if len(lines) > 1 and not lines[1].strip():
                at = 2
        if at and not lines[at - 1].endswith(("\n", "\r")):
            lines[at - 1] += eol
        block = [line + eol for line in added]
        lines[at:at] = block
    elif added and last_field is not None:
        end = last_field
        while (
            end + 1 < len(clean)
            and lines[end + 1][:1] in (" ", "\t")
            and lines[end + 1].strip()
        ):
            end += 1
        if lines[end].endswith(("\n", "\r")):
            lines[end + 1:end + 1] = [line + eol for line in added]
        else:
            lines[end] = lines[end] + eol + eol.join(added)
    return "".join(lines), True


def _raw_header_edges(waiting_path: str, text: str) -> list[dict]:
    """Every item of the waiting item's `Depends on:` lines, with its receipt."""
    items: list[str] = []
    receipts: dict[str, list[str]] = {}
    for name, value, _wrapped in _engine._header_field_lines(text):
        if name == "dependency receipts":
            for receipt in _engine._split_items(value):
                tokens = receipt.split()
                if tokens and tokens[0] not in receipts:
                    receipts[tokens[0]] = tokens[1:]
        elif value.split()[:1] and value.split()[0].lower() != "none":
            items.extend(_engine._split_items(value))
    ordered = list(dict.fromkeys(items))
    return _edge_dicts(waiting_path, [(item, receipts.get(item)) for item in ordered])


def _read_header_edges(
    root: Path, waiting_path: str, text: str, index, kinds, cooled
) -> list[dict]:
    """The edges the engine reads from the text: items it accepts, alone."""
    accepted: list[dict] = []
    for edge in _raw_header_edges(waiting_path, text):
        parsed = _read_single_edge(
            root, waiting_path, edge["reference"], edge["receipt"], index, kinds, cooled
        )
        if not parsed.findings and len(parsed.dependencies) == 1:
            accepted.append(edge)
    return accepted


def _replace_waiting_file(
    root: Path, relative_path: str, expected_sha256: str, data: bytes
) -> None:
    """Replace one waiting item through the confined, identity-checked path."""
    target = confine_migration_path(root, relative_path, require_file=True)
    if target is None:
        raise _NeedsRefusal("unsafe_waiting_path")
    current = _engine._migration_file_bytes(root, relative_path)
    if current is None or hashlib.sha256(current).hexdigest() != expected_sha256:
        raise _NeedsRefusal("waiting_item_changed")
    _migration_atomic_replace(target, data, stage="waiting", failure_point=None)


def _entries_with_path(doc, waiting_path: str) -> list:
    """Every registry entry in the document whose `path` is `waiting_path`."""
    lists: list = []
    for section_name, list_names in _engine._TOP_LEVEL_ENTRY_COLLECTIONS.items():
        section = doc.get(section_name)
        if hasattr(section, "get"):
            lists.extend(section.get(name) for name in list_names)
    for key in doc:
        section = doc[key]
        if not (isinstance(key, str) and key.startswith("ini-") and hasattr(section, "get")):
            continue
        for section_name, list_names in _engine._INITIATIVE_ENTRY_COLLECTIONS.items():
            sub = section.get(section_name)
            if hasattr(sub, "get"):
                lists.extend(sub.get(name) for name in list_names)
    found = []
    for entries in lists:
        if entries is None or isinstance(entries, (str, dict)) or not hasattr(entries, "__iter__"):
            continue
        for entry in entries:
            if hasattr(entry, "get") and entry.get("path") == waiting_path:
                found.append(entry)
    return found


def _clear_needs(doc, waiting_path: str) -> bool:
    found = _entries_with_path(doc, waiting_path)
    if len(found) != 1 or not hasattr(found[0].get("needs"), "clear"):
        return False
    found[0]["needs"].clear()
    return True


def _apply_needs_operations(
    root: Path, doc, workspace_bytes: bytes, operations: list[dict]
) -> tuple[list[dict], int, dict]:
    """Apply the needs operations: waiting files first, then clear `needs` in `doc`."""
    memberships, cooled, cooling_findings, index, kinds = _needs_membership_context(
        root, workspace_bytes
    )
    cooling_unavailable = any(
        finding.code == "cooling_state_unavailable" for finding in cooling_findings
    )
    member_paths = frozenset(
        m.entry.path for m in memberships if m.entry.path is not None
    )
    per_op: list[dict] = []
    applied = 0
    before: list[dict] = []
    registry: list[dict] = []
    dropped: list[dict] = []
    after: list[dict] = []

    for op in operations:
        path = op["waiting_path"]
        shown = _echo_path(path, member_paths)

        def refuse(reason: str, shown: str = shown) -> None:
            per_op.append({"path": shown, "applied": False, "reason": reason})

        if cooling_unavailable:
            refuse("cooling_state_unavailable")
            continue
        matches = [m for m in memberships if m.entry.path == path]
        if len(matches) != 1:
            refuse("waiting_path_not_membership")
            continue
        membership = matches[0]
        is_cooled = _engine._membership_is_cooled(membership, root, cooled)
        if op["operation_type"] == _NEEDS_DROP_COOLED:
            if not is_cooled:
                refuse("no_longer_cooled")
                continue
            edges = _edge_dicts(path, _best_effort_edges(membership.entry, index))
            if edges != op["dropped_cooled"]:
                refuse("registry_edges_changed")
                continue
            if not _clear_needs(doc, path):
                refuse("entry_not_found")
                continue
            dropped.extend(edges)
            per_op.append({"path": shown, "applied": True})
            applied += 1
            continue
        if is_cooled:
            refuse("waiting_path_not_membership")
            continue
        try:
            derived = _derive_needs_edges(
                root, path, membership.entry, index, kinds, cooled
            )
        except _NeedsRefusal:
            refuse("items_changed")
            continue
        registry_edges = _edge_dicts(path, derived)
        if (
            registry_edges != op["registry_edges"]
            or [reference for reference, _ in derived] != op["depends_on_items"]
            or [
                f"{reference} {' '.join(tokens)}"
                for reference, tokens in derived
                if tokens is not None
            ] != op["receipt_items"]
        ):
            refuse("items_changed")
            continue
        data = _engine._migration_file_bytes(root, path)
        if data is None:
            refuse("unsafe_waiting_path")
            continue
        if hashlib.sha256(data).hexdigest() != op["waiting_sha256"]:
            refuse("waiting_item_changed")
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            refuse("waiting_item_not_writable")
            continue
        if not _preamble_anchor_ok(text):
            refuse("waiting_item_not_writable")
            continue
        before_edges = _raw_header_edges(path, text)
        inserted = _insert_header_items(
            text,
            [reference for reference, _ in derived],
            [(reference, tokens) for reference, tokens in derived if tokens is not None],
        )
        new_text, changed = inserted
        if changed:
            try:
                _replace_waiting_file(root, path, op["waiting_sha256"], new_text.encode("utf-8"))
            except _NeedsRefusal as refusal:
                refuse(refusal.reason)
                continue
            except OSError:
                refuse("waiting_write_failed")
                continue
        read_back = _engine._migration_file_bytes(root, path)
        try:
            back_text = read_back.decode("utf-8") if read_back is not None else None
        except UnicodeDecodeError:
            back_text = None
        if back_text is None:
            refuse("read_back_failed")
            continue
        after_edges = _read_header_edges(root, path, back_text, index, kinds, cooled)
        expected = {_edge_key(e) for e in before_edges} | {_edge_key(e) for e in registry_edges}
        before.extend(before_edges)
        registry.extend(registry_edges)
        after.extend(after_edges)
        if {_edge_key(e) for e in after_edges} != expected:
            refuse("edge_mismatch")
            continue
        if not _clear_needs(doc, path):
            refuse("entry_not_found")
            continue
        per_op.append({"path": shown, "applied": True})
        applied += 1

    expected_all = {_edge_key(e) for e in before} | {_edge_key(e) for e in registry}
    report = {
        "header_edges_before": [_echo_edge(e, member_paths) for e in before],
        "registry_edges": [_echo_edge(e, member_paths) for e in registry],
        "dropped_cooled": [_echo_edge(e, member_paths) for e in dropped],
        "header_edges_after": [_echo_edge(e, member_paths) for e in after],
        "edges_equal": {_edge_key(e) for e in after} == expected_all,
    }
    return per_op, applied, report


def _validate_needs_operation(op: dict) -> str | None:
    """Shape-check one needs operation; its content is re-derived at apply."""
    path = op.get("waiting_path")
    if not path or not isinstance(path, str):
        return "plan_invalid"
    if "\\" in path or (len(path) >= 2 and path[1] == ":") or _has_control_character(path):
        return "plan_invalid"
    if ".." in PurePosixPath(path).parts or PurePosixPath(path).is_absolute():
        return "plan_invalid"

    def edges_ok(value: object) -> bool:
        return isinstance(value, list) and all(
            isinstance(edge, dict)
            and isinstance(edge.get("waiting_path"), str)
            and isinstance(edge.get("reference"), str)
            and (
                edge.get("receipt") is None
                or (
                    isinstance(edge["receipt"], list)
                    and all(isinstance(token, str) for token in edge["receipt"])
                )
            )
            for edge in value
        )

    def strings_ok(value: object) -> bool:
        return isinstance(value, list) and all(isinstance(item, str) for item in value)

    if op["operation_type"] == _NEEDS_DROP_COOLED:
        if "waiting_sha256" in op or not edges_ok(op.get("dropped_cooled")):
            return "plan_invalid"
        return None
    sha = op.get("waiting_sha256")
    if (
        not isinstance(sha, str)
        or _SHA256_RE.fullmatch(sha) is None
        or not edges_ok(op.get("registry_edges"))
        or not strings_ok(op.get("depends_on_items"))
        or not strings_ok(op.get("receipt_items"))
    ):
        return "plan_invalid"
    return None


# ── captured-to-file repair ───────────────────────────────────────────────────
#
# `repair-plan` turns each captured item at migration into one record under
# `docs/product/captured/`; `repair-apply` writes the records, then re-points the
# migrated memberships' `path` in one `workspace.toml` write. A source file is
# only ever read, and no file is ever deleted.

_CAPTURED_TO_FILE = "captured-to-file"
_CAPTURED_FINDING_TYPE = 5
_CAPTURED_LEGACY_COLLECTIONS = frozenset({
    "backlog.open",
    "backlog.closed",
    "shaping_queue.backlog",
    "shaping_queue.active",
})
_CAPTURED_RECORD_KINDS = frozenset({"defect", "design", "research", "intent"})
_CAPTURED_SHAPING_TYPES = frozenset({"shape", "research", "strategy", "design", "signal"})
_LEGACY_KIND_BY_TYPE = {
    "shape": "intent",
    "strategy": "intent",
    "research": "research",
    "design": "design",
}
_CAPTURED_TERMINAL_BY_KIND = {
    "intent": frozenset({"Accepted", "Fulfilled"}),
    "research": frozenset({"Complete"}),
    "design": frozenset({"Approved"}),
}
_CAPTURED_RESOLUTION_VALUES = frozenset({"fixed", "declined", "superseded"})
_CAPTURED_DEFERRED_RE = re.compile(r"\(deferred:\s*([A-Za-z0-9][A-Za-z0-9._\-]*)\s*\)")
_CAPTURED_RECORD_PATH_RE = re.compile(r"docs/product/captured/[a-z0-9][a-z0-9-]*\.md")
_CAPTURED_ABSENT = object()


class _CapturedRefusal(Exception):
    """One operation `repair-apply` refuses; nothing is changed for it."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclasses.dataclass
class _CapturedItem:
    """One captured item at migration: a membership or a legacy slug-only entry."""

    form: str  # "legacy", "unmigrated", or "migrated"
    collection: str
    ini_slug: str
    index: int
    raw: Any
    path: str = ""
    kind: str = ""
    membership: Any = None
    cooled: bool = False
    base_slugs: tuple[str, ...] = ()
    final: str = ""


@dataclasses.dataclass
class _CapturedPlan:
    """What the planner derived: operations, findings, and the items it read."""

    operations: list[dict]
    findings: list[dict]
    items: list[_CapturedItem]
    cooling_unavailable: bool
    cooled_sources: frozenset[str]


def _raw_registry_entries(workspace: dict):
    """Yield `(initiative slug, collection, index, raw entry)` for every list entry."""
    for section_name, names in _engine._TOP_LEVEL_ENTRY_COLLECTIONS.items():
        section = workspace.get(section_name)
        if isinstance(section, dict):
            for name in names:
                entries = section.get(name)
                if isinstance(entries, list):
                    label = _engine._collection_label(section_name, name)
                    for position, raw in enumerate(entries):
                        yield "", label, position, raw
    for key, section in workspace.items():
        if not (isinstance(key, str) and _engine._CANONICAL_INITIATIVE_RE.fullmatch(key)):
            continue
        if not isinstance(section, dict):
            continue
        for section_name, names in _engine._INITIATIVE_ENTRY_COLLECTIONS.items():
            sub = section.get(section_name)
            if not isinstance(sub, dict):
                continue
            for name in names:
                entries = sub.get(name)
                if isinstance(entries, list):
                    label = _engine._collection_label(section_name, name)
                    for position, raw in enumerate(entries):
                        yield key, label, position, raw


def _captured_base_slug(path: str) -> str:
    """A source file's name without its last extension, as a record slug."""
    stem = PurePosixPath(path.rsplit("/", 1)[-1]).stem
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")


def _captured_slug_prefix(source_path: str) -> str:
    """The directory name that disambiguates a colliding or empty base slug."""
    parents = source_path.split("/")[:-1]
    if parents and parents[-1] == "notes":
        parents = parents[:-1]
    return parents[-1] if parents else ""


def _captured_title(slug: str) -> str:
    text = slug.replace("-", " ")
    return text[:1].upper() + text[1:]


def _has_non_lf_control(value: str) -> bool:
    # The C0 and C1 control characters; a line feed is allowed in a summary.
    return any(
        (char < " " and char != "\n") or "\x7f" <= char <= "\x9f" for char in value
    )


def _captured_slug_valid(slug: str) -> bool:
    return _engine._CAPTURED_FILE_RE.fullmatch(f"{slug}.md") is not None


def _captured_record_text(
    slug: str,
    status: str,
    kind: str,
    type_: str | None,
    resolution: str | None,
    parent_intent: str | None,
    detail: str | None,
    header_lines: list[str],
    summary: str,
) -> str:
    """Render the record's fields in their fixed order; the summary sits under its own heading."""
    lines = [f"# {_captured_title(slug)}", "", f"- **Status:** {status}", f"- **Kind:** {kind}"]
    if type_ is not None:
        lines.append(f"- **Type:** {type_}")
    if resolution is not None:
        lines.append(f"- **Resolution:** {resolution}")
    if parent_intent is not None:
        lines.append(f"- **Parent intent:** {parent_intent}")
    if detail is not None:
        lines.append(f"- **Detail:** {detail}")
    lines.extend(header_lines)
    if summary:
        lines.extend(["", "## Summary", "", summary.rstrip("\n")])
    return "\n".join(lines) + "\n"


def _copied_header(text: str) -> tuple[list[str], list[str], list[str]]:
    """The source's dependency lines, verbatim, with the items and receipts they hold."""
    lines: list[str] = []
    items: list[str] = []
    receipts: list[str] = []
    for name, value, _wrapped in _engine._header_field_lines(text):
        label = "Depends on" if name == "depends on" else "Dependency receipts"
        lines.append(f"- **{label}:** {value}".rstrip())
        if name == "dependency receipts":
            receipts.extend(_engine._split_items(value))
        elif value.split()[:1] and value.split()[0].lower() != "none":
            items.extend(_engine._split_items(value))
    return lines, items, receipts


def _source_status_conflict(collection: str, kind: str, text: str) -> bool:
    """True when the source's own `Status:` breaks its collection's rule."""
    status = _engine._parse_generic_status(text, kind)
    if collection == "backlog.open":
        return status == "Closed" if kind == "defect" else status != "Draft"
    if collection in ("shaping_queue.backlog", "shaping_queue.active"):
        return status in _CAPTURED_TERMINAL_BY_KIND.get(kind, frozenset())
    if collection == "backlog.closed" and kind == "defect":
        resolution = _engine._parse_preamble_fields(text).get("resolution")
        return status != "Closed" or resolution not in _CAPTURED_RESOLUTION_VALUES
    return False


def _live_intent_reference(index, path: object) -> str | None:
    """The typed reference of the one live intent at `path`, else `None`."""
    if not isinstance(path, str):
        return None
    for (kind, slug), paths in index.intents.items():
        if paths == (path,):
            return f"{kind}:{slug}"
    return None


def _captured_record_occupant(root: Path, record_path: str, cooled: frozenset[Path]):
    """`_CAPTURED_ABSENT`, the record's bytes, or `None` when it cannot be read."""
    try:
        os.lstat(root / record_path)
    except FileNotFoundError:
        return _CAPTURED_ABSENT
    except OSError:
        return None
    if _engine._confined_artifact_path(root, record_path) in cooled:
        return None
    return _engine._migration_file_bytes(root, record_path)


def _registry_fingerprint(item: _CapturedItem) -> str:
    return _entry_fingerprint(item.ini_slug, item.collection, item.index, item.raw)


def _entry_fingerprint(ini_slug: str, collection: str, index: int, raw: object) -> str:
    """Digest of one registry entry and where it sits, as each repair step binds it."""
    return hashlib.sha256(json.dumps(
        {
            "ini_slug": ini_slug,
            "collection": collection,
            "index": index,
            "entry": raw,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("ascii")).hexdigest()


def _deferral_anchors(
    root: Path, cooled: frozenset[Path]
) -> tuple[frozenset[str], tuple[str, ...]]:
    """Every `(deferred: <anchor>)` a spec carries, and each path that was not read.

    A cooled spec is never opened. A spec that could not be read, or a
    `docs/specs` that could not be listed, is named among the unread paths.
    """
    if not os.path.lexists(root / "docs/specs"):
        return frozenset(), ()
    specs = _engine.confine_migration_path(root, "docs/specs")
    if specs is None:
        return frozenset(), ("docs/specs",)
    try:
        names = sorted(entry.name for entry in os.scandir(specs) if entry.is_dir())
    except OSError:
        return frozenset(), ("docs/specs",)
    anchors: set[str] = set()
    unread: list[str] = []
    for name in names:
        relative = f"docs/specs/{name}/spec.md"
        if not os.path.lexists(root / relative):
            continue
        if _engine._confined_artifact_path(root, relative) in cooled:
            unread.append(relative)
            continue
        data = _engine._migration_file_bytes(root, relative)
        if data is None:
            unread.append(relative)
            continue
        anchors.update(_CAPTURED_DEFERRED_RE.findall(data.decode("utf-8", errors="replace")))
    return frozenset(anchors), tuple(unread)


def _dependency_items_by_path(
    root: Path, memberships: list, cooled: frozenset[Path]
) -> tuple[dict[str, set[str]], frozenset[str]]:
    """Each path a dependency item names, with the memberships that name it.

    Also returns the paths of the memberships whose own header could not be
    read. A cooled membership's file is never opened and names nothing.
    """
    named: dict[str, set[str]] = {}
    unread: set[str] = set()
    for membership in memberships:
        for dep in membership.entry.needs:
            named.setdefault(dep.path, set()).add(membership.entry.path or "")
        path = membership.entry.path
        if path is None:
            continue
        if _engine._membership_is_cooled(membership, root, cooled):
            continue
        if not os.path.lexists(root / path):
            continue
        data = _engine._migration_file_bytes(root, path)
        if data is None:
            unread.add(path)
            continue
        for name, value, _wrapped in _engine._header_field_lines(
            data.decode("utf-8", errors="replace")
        ):
            if name == "depends on" and value.split()[:1] and value.split()[0].lower() != "none":
                for item in _engine._split_items(value):
                    named.setdefault(item, set()).add(path)
    return named, frozenset(unread)


def _captured_finding(
    item: _CapturedItem, reason: str, slug: str = "", unread_paths: tuple[str, ...] = ()
) -> dict:
    record_path = f"{_engine._CAPTURED_DIR}/{slug}.md" if slug else ""
    named = item.path or (item.raw.get("slug", "") if isinstance(item.raw, dict) else "")
    extra = {"unread_paths": list(unread_paths)} if unread_paths else {}
    return {
        **extra,
        "finding_type": _CAPTURED_FINDING_TYPE,
        "spec_path": item.path,
        "spec_status": "",
        "ini_slug": item.ini_slug,
        "list_name": item.collection,
        "reason": reason,
        "slug": slug,
        "record_path": record_path,
        "entry_index": item.index,
        "finding_id": (
            f"type{_CAPTURED_FINDING_TYPE}:{item.ini_slug}:{item.collection}:{named}:{reason}"
        ),
    }


def _plan_captured_items(root: Path, workspace_bytes: bytes) -> _CapturedPlan:
    """Derive every `captured-to-file` operation and refusal from the current tree.

    Every base slug is computed in one pass before any operation is built, so a
    slug does not depend on which operations a run happens to emit.
    """
    workspace = tomllib.loads(workspace_bytes.decode("utf-8"))
    memberships = _engine._extract_canonical_memberships(workspace)[0]
    cooled, cooling_findings = _engine._resolve_cooled_state(root)
    cooling_unavailable = any(
        finding.code == "cooling_state_unavailable" for finding in cooling_findings
    )
    raw_entries = {
        (ini, collection, position): raw
        for ini, collection, position, raw in _raw_registry_entries(workspace)
    }
    path_counts: dict[str, int] = {}
    for membership in memberships:
        if membership.entry.path is not None:
            path_counts[membership.entry.path] = path_counts.get(membership.entry.path, 0) + 1

    items: list[_CapturedItem] = []
    for membership in memberships:
        path = membership.entry.path
        form = _engine._captured_membership_form(path)
        if form is None or path is None:
            continue
        items.append(_CapturedItem(
            form=form,
            collection=membership.collection,
            ini_slug=membership.ini_slug,
            index=membership.entry_index,
            raw=raw_entries.get(
                (membership.ini_slug, membership.collection, membership.entry_index)
            ),
            path=path,
            kind=membership.entry.kind,
            membership=membership,
            cooled=(
                form == "unmigrated"
                and _engine._membership_is_cooled(membership, root, cooled)
            ),
        ))
    for (ini, collection, position), raw in raw_entries.items():
        if (
            collection in _CAPTURED_LEGACY_COLLECTIONS
            and isinstance(raw, dict)
            and isinstance(raw.get("slug"), str)
            and "path" not in raw
            and raw.get("kind", "defect") == "defect"
        ):
            items.append(_CapturedItem(
                form="legacy", collection=collection, ini_slug=ini, index=position, raw=raw
            ))

    # One pass: every item's base slugs, then the finals.
    for item in items:
        if item.form == "legacy":
            item.base_slugs = (item.raw["slug"],)
            item.final = item.raw["slug"]
        elif item.form == "migrated":
            file_slug = item.path.rpartition("/")[2].removesuffix(".md")
            slugs = [file_slug]
            record, _finding = _engine.read_captured_item(root, f"{file_slug}.md", cooled)
            detail = record.get("detail") if isinstance(record, dict) else None
            if isinstance(detail, str):
                slugs.append(_captured_base_slug(detail))
            item.base_slugs = tuple(slugs)
            item.final = file_slug
        else:
            item.base_slugs = (_captured_base_slug(item.path),)
    owners: dict[str, set[int]] = {}
    for position, item in enumerate(items):
        for slug in item.base_slugs:
            owners.setdefault(slug, set()).add(position)
    for position, item in enumerate(items):
        if item.form != "unmigrated":
            continue
        base = item.base_slugs[0]
        if base == "" or owners.get(base, set()) - {position}:
            item.final = f"{_captured_slug_prefix(item.path)}-{base}"
        else:
            item.final = base
    final_counts: dict[str, int] = {}
    for item in items:
        final_counts[item.final] = final_counts.get(item.final, 0) + 1

    operations: list[dict] = []
    findings: list[dict] = []
    context = {
        "root": root,
        "index": _engine.build_resolution_index(root, cooled=cooled),
        "cooled": cooled,
        "cooling_unavailable": cooling_unavailable,
        "path_counts": path_counts,
        "final_counts": final_counts,
        "memberships": memberships,
        "named": None,
        "anchors": None,
    }
    for item in items:
        if item.form == "migrated" or item.cooled:
            continue
        if item.form == "legacy":
            outcome = _plan_legacy_item(context, item)
        else:
            outcome = _plan_membership_item(context, item)
        if isinstance(outcome, (str, tuple)):
            reason, unread = (outcome, ()) if isinstance(outcome, str) else outcome
            findings.append(_captured_finding(
                item, reason, item.final if _captured_slug_valid(item.final) else "", unread
            ))
        elif outcome is not None:
            operations.append(outcome)
    operations.sort(key=lambda op: op["record_path"])
    return _CapturedPlan(
        operations=operations,
        findings=findings,
        items=items,
        cooling_unavailable=cooling_unavailable,
        cooled_sources=frozenset(item.path for item in items if item.cooled),
    )


def _plan_common_fields(context: dict, item: _CapturedItem) -> str | None:
    """Checks both item forms share: slug, summary, and the live intent."""
    if not _captured_slug_valid(item.final):
        return "slug-invalid"
    if context["final_counts"][item.final] > 1:
        return "slug-collision"
    return None


def _derive_record(
    context: dict,
    item: _CapturedItem,
    status: str,
    kind: str,
    type_: str | None,
    resolution: str | None,
    detail: str | None,
    header_lines: list[str],
) -> tuple[str | None, str | None]:
    """Build the record text, or refuse. Returns `(text, refusal reason)`."""
    raw = item.raw if isinstance(item.raw, dict) else {}
    summary = raw.get("summary", "")
    if not isinstance(summary, str):
        return None, "summary-not-text"
    if _has_non_lf_control(summary):
        return None, "summary-control-character"
    parent: str | None = None
    if "intent" in raw:
        parent = _live_intent_reference(context["index"], raw["intent"])
        if parent is None:
            return None, "intent-not-live"
    text = _captured_record_text(
        item.final, status, kind, type_, resolution, parent, detail, header_lines, summary
    )
    fields, _failing = _engine.parse_captured_item(text)
    expected = {
        "status": status,
        "kind": kind,
        "type": type_,
        "resolution": resolution,
        "parent_intent": parent,
        "detail": detail,
    }
    if fields != expected:
        return None, "record-read-back"
    return text, None


def _plan_membership_item(context: dict, item: _CapturedItem):
    """An operation, a refusal reason, or `None` for an item needing nothing."""
    root: Path = context["root"]
    membership = item.membership
    path = item.path
    if context["cooling_unavailable"]:
        return "cooling-state-unavailable"
    if context["path_counts"][path] > 1:
        return "duplicate-membership"
    if item.kind not in _CAPTURED_RECORD_KINDS:
        return "kind-not-captured"
    if membership.entry.needs:
        return "typed-needs-remain"
    if not os.path.lexists(root / path):
        return "source-missing"
    data = _engine._migration_file_bytes(root, path)
    try:
        text = data.decode("utf-8") if data is not None else None
    except UnicodeDecodeError:
        text = None
    if data is None or text is None:
        return "source-unreadable"
    if context["named"] is None:
        context["named"] = _dependency_items_by_path(
            root, context["memberships"], context["cooled"]
        )
    named, unread_headers = context["named"]
    if named.get(path, set()) - {path}:
        return "source-is-dependency-target"
    if unread_headers - {path}:
        return "dependency-headers-unread", tuple(sorted(unread_headers - {path}))
    if _source_status_conflict(item.collection, item.kind, text):
        return "status-conflict"
    common = _plan_common_fields(context, item)
    if common is not None:
        return common
    if context["anchors"] is None:
        context["anchors"] = _deferral_anchors(root, context["cooled"])
    stem = PurePosixPath(path.rsplit("/", 1)[-1]).stem
    anchors, unread_specs = context["anchors"]
    if item.final != stem:
        if stem in anchors:
            return "deferral-anchor"
        if unread_specs:
            return "deferral-anchors-unread", unread_specs
    status = "Closed" if item.collection == "backlog.closed" else "Open"
    resolution = (
        _engine._parse_preamble_fields(text).get("resolution") if status == "Closed" else None
    )
    header_lines, depends_on_items, receipt_items = _copied_header(text)
    record_text, reason = _derive_record(
        context, item, status, item.kind, None, resolution, path, header_lines
    )
    if reason is not None or record_text is None:
        return reason or "record-read-back"
    record_path = f"{_engine._CAPTURED_DIR}/{item.final}.md"
    occupant = _captured_record_occupant(root, record_path, context["cooled"])
    if occupant is not _CAPTURED_ABSENT and occupant != record_text.encode("utf-8"):
        return "record-differs"
    return {
        "operation_type": _CAPTURED_TO_FILE,
        "record_path": record_path,
        "record_text": record_text,
        "entry_locator": {"collection": item.collection, "index": item.index},
        "source_path": path,
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "registry_fingerprint": _registry_fingerprint(item),
        "depends_on_items": depends_on_items,
        "receipt_items": receipt_items,
    }


def _plan_legacy_item(context: dict, item: _CapturedItem):
    root: Path = context["root"]
    raw = item.raw
    type_ = raw.get("type") if "type" in raw else None
    if "kind" in raw or "type" not in raw:
        kind = "defect"
    elif isinstance(type_, str) and type_ in _LEGACY_KIND_BY_TYPE:
        kind = _LEGACY_KIND_BY_TYPE[type_]
    else:
        kind = ""
    item.kind = kind
    common = _plan_common_fields(context, item)
    if common is not None:
        return common
    if not kind:
        return "legacy-kind-unassignable"
    type_line = type_ if isinstance(type_, str) and type_ in _CAPTURED_SHAPING_TYPES else None
    status = "Closed" if item.collection == "backlog.closed" else "Open"
    record_text, reason = _derive_record(
        context, item, status, kind, type_line, None, None, []
    )
    if reason is not None or record_text is None:
        return reason or "record-read-back"
    record_path = f"{_engine._CAPTURED_DIR}/{item.final}.md"
    occupant = _captured_record_occupant(root, record_path, context["cooled"])
    if occupant is _CAPTURED_ABSENT:
        return {
            "operation_type": _CAPTURED_TO_FILE,
            "record_path": record_path,
            "record_text": record_text,
            "entry_locator": {"collection": item.collection, "index": item.index},
            "slug": item.final,
        }
    if occupant == record_text.encode("utf-8"):
        return None
    return "record-differs"


def _build_captured_operations(
    root: Path, workspace_bytes: bytes
) -> tuple[list[dict], list[dict]]:
    """Plan `captured-to-file` operations and their manual findings."""
    plan = _plan_captured_items(root, workspace_bytes)
    return plan.operations, plan.findings


# Echo rules for the captured-to-file values: each is judged alone against its
# position's grammar, and a value that fails appears as an empty string. A
# record's text and a summary are free text and appear whole; `_emit` escapes
# every control and non-ASCII character in them.

def _echo_valid(value: object, pattern: re.Pattern[str] | frozenset[str]) -> str:
    if not isinstance(value, str) or len(value) > 200 or _has_control_character(value):
        return ""
    if isinstance(pattern, frozenset):
        return value if value in pattern else ""
    return value if pattern.fullmatch(value) else ""


def _echo_slug(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value if _captured_slug_valid(value) and len(value) <= 200 else ""


def _echo_sha(value: object) -> str:
    return _echo_valid(value, _SHA256_RE)


def _echo_collection(value: object) -> str:
    names = {
        _engine._collection_label(section, name)
        for table in (_engine._TOP_LEVEL_ENTRY_COLLECTIONS, _engine._INITIATIVE_ENTRY_COLLECTIONS)
        for section, section_names in table.items()
        for name in section_names
    }
    return _echo_valid(value, frozenset(names))


def _echo_index(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def _echo_locator(value: object) -> dict:
    locator = value if isinstance(value, dict) else {}
    return {
        "collection": _echo_collection(locator.get("collection")),
        "index": _echo_index(locator.get("index")),
    }


def _echo_receipt_item(receipt: object) -> str:
    if not isinstance(receipt, str):
        return ""
    reference, _, rest = receipt.partition(" ")
    tokens = _echo_tokens(rest.split(" ")) if rest else []
    return " ".join([_echo_reference(reference)] + (tokens or []))


def _echo_captured_operation(op: dict) -> dict:
    item = dict(op)
    item["record_path"] = _echo_reference(op.get("record_path"))
    if "slug" in item:
        item["slug"] = _echo_slug(op["slug"])
    if "source_path" in item:
        item["source_path"] = _echo_reference(op["source_path"])
        item["source_sha256"] = _echo_sha(op.get("source_sha256"))
        item["registry_fingerprint"] = _echo_sha(op.get("registry_fingerprint"))
        item["depends_on_items"] = [_echo_reference(i) for i in op.get("depends_on_items", [])]
        item["receipt_items"] = [_echo_receipt_item(r) for r in op.get("receipt_items", [])]
    item["entry_locator"] = _echo_locator(op.get("entry_locator"))
    return item


_REPOSITORY_PATH_SEGMENT_RE = re.compile(r"[A-Za-z0-9._-]+")


def _echo_repository_path(path: object) -> str:
    """A path that is `/`-separated plain segments, or `""`."""
    if not isinstance(path, str) or len(path) > 200:
        return ""
    parts = path.split("/")
    if any(
        part in (".", "..") or _REPOSITORY_PATH_SEGMENT_RE.fullmatch(part) is None
        for part in parts
    ):
        return ""
    return path


def _echo_captured_finding(finding: dict) -> dict:
    item = dict(finding)
    item["spec_path"] = _echo_reference(finding.get("spec_path"))
    item["slug"] = _echo_slug(finding.get("slug"))
    item["record_path"] = _echo_reference(finding.get("record_path"))
    item["list_name"] = _echo_collection(finding.get("list_name"))
    item["ini_slug"] = _public_ini_slug(finding.get("ini_slug"), allow_empty=True)
    item["entry_index"] = _echo_index(finding.get("entry_index"))
    if "unread_paths" in finding:
        item["unread_paths"] = [_echo_repository_path(p) for p in finding["unread_paths"]]
    named = item["spec_path"] or item["slug"]
    item["finding_id"] = (
        f"type{_CAPTURED_FINDING_TYPE}:{item['ini_slug']}:{item['list_name']}:"
        f"{named}:{finding.get('reason', '')}"
    )
    return item


def _echo_record_edge(edge: dict) -> dict:
    return {
        "waiting_path": _echo_reference(edge.get("waiting_path")),
        "reference": _echo_reference(edge.get("reference")),
        "receipt": _echo_tokens(edge.get("receipt")),
    }


def _captured_report_echo(report: dict) -> dict:
    return {
        "captured_before": [
            {
                "slug": _echo_slug(entry["slug"]),
                "kind": _echo_valid(entry["kind"], _engine._CAPTURED_KINDS),
                "source_path": (
                    _echo_reference(entry["source_path"])
                    if entry["source_path"] is not None else None
                ),
            }
            for entry in report["captured_before"]
        ],
        "captured_after": [
            {
                "slug": _echo_slug(entry["slug"]),
                "status": _echo_valid(entry.get("status"), _engine._CAPTURED_STATUSES),
                "kind": _echo_valid(entry.get("kind"), _engine._CAPTURED_KINDS),
                "type": (
                    _echo_valid(entry["type"], frozenset(_engine._SHAPING_TYPE_ROUTES))
                    if entry.get("type") is not None else None
                ),
                "resolution": (
                    _echo_valid(entry["resolution"], _engine._CAPTURED_RESOLUTIONS)
                    if entry.get("resolution") is not None else None
                ),
                "parent_intent": (
                    _echo_reference(entry["parent_intent"])
                    if entry.get("parent_intent") is not None else None
                ),
                "detail": (
                    _echo_reference(entry["detail"]) if entry.get("detail") is not None else None
                ),
            }
            for entry in report["captured_after"]
        ],
        "header_edges_before": [_echo_record_edge(e) for e in report["header_edges_before"]],
        "header_edges_after": [_echo_record_edge(e) for e in report["header_edges_after"]],
        "captured_equal": report["captured_equal"],
    }


# ── Apply ─────────────────────────────────────────────────────────────────────

def _ensure_record_directory(root: Path) -> str | None:
    """Create `docs/product/captured/` through the segment check; re-check it after."""
    resolved_root = root.resolve()
    relative = ""
    for part in _engine._CAPTURED_DIR.split("/"):
        relative = f"{relative}/{part}" if relative else part
        if _engine.confine_migration_path(root, relative) is None:
            return "record_directory_unsafe"
        target = resolved_root / relative
        try:
            try:
                info = os.lstat(target)
            except FileNotFoundError:
                target.mkdir(mode=0o755)
                info = os.lstat(target)
        except OSError:
            return "record_directory_unsafe"
        if not stat.S_ISDIR(info.st_mode):
            return "record_directory_unsafe"
    final = _engine.confine_migration_path(root, _engine._CAPTURED_DIR)
    if final is None or not final.is_dir():
        return "record_directory_unsafe"
    return None


def _write_all(descriptor: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        view = view[os.write(descriptor, view):]


def _write_record(root: Path, record_path: str, data: bytes) -> str:
    """Create one record by an exclusive create, or keep an identical confined one.

    Returns `created` or `kept`; raises `_CapturedRefusal` for anything else.
    """
    reason = _ensure_record_directory(root)
    if reason is not None:
        raise _CapturedRefusal(reason)
    target = root.resolve() / record_path
    if os.path.lexists(target):
        if _engine._migration_file_bytes(root, record_path) == data:
            return "kept"
        raise _CapturedRefusal("record_path_occupied")
    if _engine.confine_migration_path(root, record_path) is None:
        raise _CapturedRefusal("record_directory_unsafe")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(target, flags, 0o600)
    except FileExistsError:
        raise _CapturedRefusal("record_path_occupied") from None
    except OSError:
        raise _CapturedRefusal("record_write_failed") from None
    try:
        _write_all(descriptor, data)
        os.fsync(descriptor)
    except OSError:
        raise _CapturedRefusal("record_write_failed") from None
    finally:
        os.close(descriptor)
    try:
        _fsync_directory(target.parent)
    except OSError:
        raise _CapturedRefusal("record_write_failed") from None
    if _engine._migration_file_bytes(root, record_path) != data:
        raise _CapturedRefusal("record_read_back_failed")
    return "created"


def _captured_mismatch_reason(op: dict, plan: _CapturedPlan) -> str | None:
    """`None` when `op` is exactly an operation re-derived now, else why not."""
    if op in plan.operations:
        return None
    if plan.cooling_unavailable and "source_path" in op:
        return "cooling_state_unavailable"
    for key in ("source_path", "slug", "record_path"):
        value = op.get(key)
        candidate = next(
            (d for d in plan.operations if isinstance(value, str) and d.get(key) == value), None
        )
        if candidate is None:
            continue
        if candidate.get("source_sha256") != op.get("source_sha256"):
            return "source_changed"
        if candidate.get("registry_fingerprint") != op.get("registry_fingerprint"):
            return "registry_changed"
        return "operation_changed"
    if op.get("source_path") in plan.cooled_sources:
        return "membership_cooled"
    # The record path now holds something the planned bytes do not match.
    if any(
        f["reason"] == "record-differs" and f["record_path"] == op.get("record_path")
        for f in plan.findings
    ):
        return "record_path_occupied"
    return "operation_changed"


def _apply_captured_operations(
    root: Path, doc, operations: list[dict], plan: _CapturedPlan
) -> tuple[list[dict], int, dict]:
    """Write each record, then re-point its membership's `path` in `doc`.

    `plan` was derived before any write of this run. The caller holds the shared
    writer lock and writes `doc` once afterwards.
    """
    per_op: list[dict] = []
    applied = 0
    written: list[tuple[dict, bytes, str | None]] = []
    for op in operations:
        shown = _echo_reference(op.get("record_path"))
        reason = _captured_mismatch_reason(op, plan)
        if reason is not None:
            per_op.append({"path": shown, "applied": False, "reason": reason})
            continue
        data = op["record_text"].encode("utf-8")
        try:
            outcome = _write_record(root, op["record_path"], data)
        except _CapturedRefusal as refusal:
            per_op.append({"path": shown, "applied": False, "reason": refusal.reason})
            continue
        source_text: str | None = None
        if "source_path" in op:
            found = _entries_with_path(doc, op["source_path"])
            if len(found) != 1:
                per_op.append({"path": shown, "applied": False, "reason": "entry_not_found"})
                continue
            found[0]["path"] = op["record_path"]
            source_bytes = _engine._migration_file_bytes(root, op["source_path"])
            if source_bytes is not None and (
                hashlib.sha256(source_bytes).hexdigest() == op["source_sha256"]
            ):
                source_text = source_bytes.decode("utf-8", errors="replace")
        written.append((op, data, source_text))
        per_op.append({"path": shown, "applied": True, "record": outcome})
        applied += 1

    equal = True
    after: list[dict] = []
    edges_before: list[dict] = []
    edges_after: list[dict] = []
    for op, data, source_text in written:
        record_path = op["record_path"]
        slug = record_path.rpartition("/")[2].removesuffix(".md")
        planned, _failing = _engine.parse_captured_item(data.decode("utf-8"))
        back_bytes = _engine._migration_file_bytes(root, record_path)
        try:
            back_text = back_bytes.decode("utf-8") if back_bytes is not None else None
        except UnicodeDecodeError:
            back_text = None
        back, _back_failing = (
            _engine.parse_captured_item(back_text) if back_text is not None else (None, "")
        )
        after.append({"slug": slug, **(back or {})})
        if back is None or back != planned:
            equal = False
        before_set = (
            _raw_header_edges(record_path, source_text) if source_text is not None
            else ([] if "source_path" not in op else None)
        )
        after_set = _raw_header_edges(record_path, back_text) if back_text is not None else None
        if before_set is None or after_set is None:
            equal = False
            continue
        edges_before.extend(before_set)
        edges_after.extend(after_set)
        if {_edge_key(e) for e in before_set} != {_edge_key(e) for e in after_set}:
            equal = False
    report = {
        "captured_before": [
            {
                "slug": item.final,
                "kind": item.kind,
                "source_path": item.path if item.form == "unmigrated" else None,
            }
            for item in plan.items
        ],
        "captured_after": after,
        "header_edges_before": edges_before,
        "header_edges_after": edges_after,
        "captured_equal": equal,
    }
    return per_op, applied, _captured_report_echo(report)


def _validate_captured_operation(op: dict) -> str | None:
    """Shape-check one `captured-to-file` operation; its content is re-derived at apply."""

    def strings_ok(value: object) -> bool:
        return isinstance(value, list) and all(isinstance(item, str) for item in value)

    record_path = op.get("record_path")
    locator = op.get("entry_locator")
    if (
        not isinstance(record_path, str)
        or _CAPTURED_RECORD_PATH_RE.fullmatch(record_path) is None
        or not isinstance(op.get("record_text"), str)
        or not isinstance(locator, dict)
        or not isinstance(locator.get("collection"), str)
        or not isinstance(locator.get("index"), int)
        or isinstance(locator.get("index"), bool)
    ):
        return "plan_invalid"
    if "source_path" in op:
        if (
            "slug" in op
            or not isinstance(op["source_path"], str)
            or not isinstance(op.get("source_sha256"), str)
            or _SHA256_RE.fullmatch(op["source_sha256"]) is None
            or not isinstance(op.get("registry_fingerprint"), str)
            or _SHA256_RE.fullmatch(op["registry_fingerprint"]) is None
            or not strings_ok(op.get("depends_on_items"))
            or not strings_ok(op.get("receipt_items"))
        ):
            return "plan_invalid"
    elif not isinstance(op.get("slug"), str):
        return "plan_invalid"
    return None


# ── intent-brief-drop repair ──────────────────────────────────────────────────
#
# `repair-plan` holds one operation for each canonical repo-origin intent or
# brief entry, cooled or not; `repair-apply` removes it after the needs
# operations ran, and keeps an entry whose `needs` were not cleared.

_INTENT_BRIEF_DROP = "intent-brief-drop"
_DROP_KINDS = frozenset({"intent", "brief"})
_DROP_DIRECTORY_BY_KIND = {"intent": "docs/product/intents/", "brief": "docs/product/briefs/"}


def _is_droppable(entry) -> bool:
    """True for a repo-origin intent under the intents directory or brief under the briefs one.

    A captured item's entry is never droppable, whatever its `kind`.
    """
    directory = _DROP_DIRECTORY_BY_KIND.get(entry.kind)
    return (
        directory is not None
        and entry.path is not None
        and entry.path.startswith(directory)
        and entry.source.mode == "repo-origin"
    )


def _build_drop_operations(workspace_bytes: bytes) -> list[dict]:
    """Plan one `intent-brief-drop` operation per droppable canonical entry."""
    workspace = tomllib.loads(workspace_bytes.decode("utf-8"))
    memberships = _engine._extract_canonical_memberships(workspace)[0]
    raw_entries = {
        (ini, collection, position): raw
        for ini, collection, position, raw in _raw_registry_entries(workspace)
    }
    operations: list[dict] = []
    for membership in memberships:
        entry = membership.entry
        if not _is_droppable(entry):
            continue
        locator = (membership.ini_slug, membership.collection, membership.entry_index)
        operations.append({
            "operation_type": _INTENT_BRIEF_DROP,
            "entry_locator": {
                "ini_slug": locator[0],
                "collection": locator[1],
                "index": locator[2],
            },
            "path": entry.path,
            "kind": entry.kind,
            "registry_fingerprint": _entry_fingerprint(*locator, raw_entries.get(locator)),
        })
    return operations


def _doc_entry_list(doc, ini_slug: str, collection: str):
    """The list at a locator in the tomlkit document, or `None`."""
    section_name, _, list_name = collection.partition(".")
    if ini_slug:
        if not _engine._CANONICAL_INITIATIVE_RE.fullmatch(ini_slug):
            return None
        names = _engine._INITIATIVE_ENTRY_COLLECTIONS
        parent = doc.get(ini_slug)
    else:
        names = _engine._TOP_LEVEL_ENTRY_COLLECTIONS
        parent = doc
    if list_name not in names.get(section_name, ()) or not hasattr(parent, "get"):
        return None
    section = parent.get(section_name)
    entries = section.get(list_name) if hasattr(section, "get") else None
    if isinstance(entries, (str, dict)) or not hasattr(entries, "__delitem__"):
        return None
    return entries


def _bind_drop_entries(
    doc, workspace_bytes: bytes, operations: list[dict]
) -> tuple[list[tuple[dict, str, Any, Any]], list[dict]]:
    """Check each drop against the registry read under the lock; bind its entry.

    Returns `(op, shown path, list, entry)` for each drop that passes, and the
    refusals of the rest.
    """
    if not operations:
        return [], []
    workspace = tomllib.loads(workspace_bytes.decode("utf-8"))
    memberships = {
        (m.ini_slug, m.collection, m.entry_index): m
        for m in _engine._extract_canonical_memberships(workspace)[0]
    }
    raw_entries = {
        (ini, collection, position): raw
        for ini, collection, position, raw in _raw_registry_entries(workspace)
    }
    bound: list[tuple[dict, str, Any, Any]] = []
    refusals: list[dict] = []
    seen: set[int] = set()
    for op in operations:
        shown = _echo_path(op["path"], None)
        locator = op["entry_locator"]
        key = (locator["ini_slug"], locator["collection"], locator["index"])
        membership = memberships.get(key)
        if (
            membership is None
            or membership.entry.path != op["path"]
            or membership.entry.kind != op["kind"]
            or op["registry_fingerprint"] != _entry_fingerprint(*key, raw_entries.get(key))
        ):
            refusals.append({"path": shown, "applied": False, "reason": "entry_locator_mismatch"})
            continue
        if not _is_droppable(membership.entry):
            refusals.append({"path": shown, "applied": False, "reason": "entry_not_droppable"})
            continue
        entries = _doc_entry_list(doc, key[0], key[1])
        entry = entries[key[2]] if entries is not None and key[2] < len(entries) else None
        if not hasattr(entry, "get") or entry.get("path") != op["path"] or id(entry) in seen:
            refusals.append({"path": shown, "applied": False, "reason": "entry_not_found"})
            continue
        seen.add(id(entry))
        bound.append((op, shown, entries, entry))
    return bound, refusals


def _apply_bound_drops(bound: list[tuple[dict, str, Any, Any]]) -> tuple[list[dict], int]:
    """Remove each bound entry by identity unless it still has `needs`."""
    per_op: list[dict] = []
    applied = 0
    for _op, shown, entries, entry in bound:
        needs = entry.get("needs")
        if needs is not None and len(needs) > 0:
            per_op.append({"path": shown, "applied": False, "reason": "entry_has_needs"})
            continue
        position = next((i for i, item in enumerate(entries) if item is entry), None)
        if position is None:
            per_op.append({"path": shown, "applied": False, "reason": "entry_not_found"})
            continue
        del entries[position]
        per_op.append({"path": shown, "applied": True})
        applied += 1
    return per_op, applied


def _echo_drop_operation(op: dict) -> dict:
    locator = op.get("entry_locator")
    locator = locator if isinstance(locator, dict) else {}
    return {
        **op,
        "entry_locator": {
            "ini_slug": _public_ini_slug(locator.get("ini_slug"), allow_empty=True),
            "collection": _echo_collection(locator.get("collection")),
            "index": _echo_index(locator.get("index")),
        },
        "path": _echo_path(op.get("path"), None),
        "registry_fingerprint": _echo_sha(op.get("registry_fingerprint")),
    }


def _validate_drop_operation(op: dict) -> str | None:
    """Shape-check one drop operation; its entry is re-checked at apply."""
    path = op.get("path")
    locator = op.get("entry_locator")
    if (
        not isinstance(path, str)
        or not path
        or "\\" in path
        or (len(path) >= 2 and path[1] == ":")
        or _has_control_character(path)
        or ".." in PurePosixPath(path).parts
        or PurePosixPath(path).is_absolute()
        or op.get("kind") not in _DROP_KINDS
        or not isinstance(op.get("registry_fingerprint"), str)
        or _SHA256_RE.fullmatch(op["registry_fingerprint"]) is None
        or not isinstance(locator, dict)
        or not isinstance(locator.get("ini_slug"), str)
        or not isinstance(locator.get("collection"), str)
        or not isinstance(locator.get("index"), int)
        or isinstance(locator.get("index"), bool)
        or locator["index"] < 0
    ):
        return "plan_invalid"
    return None


# ── Legacy migration transaction ─────────────────────────────────────────────

_MIGRATION_LEDGER_FILE = ".workspace-migrations.json"
_MIGRATION_LOCK_FILE = ".workspace-repair.lock"
_MIGRATION_ROLES = frozenset({
    "migration-approver",
    "repository-maintainer",
    "security-approver",
})
_CONFIRMATION_FIELDS = frozenset({
    "contract_version",
    "confirmation_id",
    "action",
    "operation_id",
    "operation_digest",
    "authorization_subject",
    "role",
    "confirmed_at",
    "authorization_source",
})


def validate_migration_confirmation(
    raw: object,
    *,
    action: str,
    operation_id: str,
    operation_digest: str,
    now: datetime.datetime | None = None,
) -> tuple[dict[str, str] | None, str | None]:
    """Validate fresh, closed, one-effect confirmation evidence."""
    if not isinstance(raw, dict) or set(raw) != _CONFIRMATION_FIELDS:
        return None, "confirmation_invalid"
    if raw.get("contract_version") != "work-intake-migration-confirmation.v1":
        return None, "confirmation_invalid"
    confirmation_id = raw.get("confirmation_id")
    subject = raw.get("authorization_subject")
    role = raw.get("role")
    if (
        not isinstance(confirmation_id, str)
        or re.fullmatch(r"confirmation-[a-f0-9]{32}", confirmation_id) is None
        or not isinstance(subject, str)
        or re.fullmatch(r"subject-[a-f0-9]{32}", subject) is None
        or role not in _MIGRATION_ROLES
        or raw.get("authorization_source") != "current-human-session"
    ):
        return None, "confirmation_invalid"
    if raw.get("action") != action:
        return None, "confirmation_binding_mismatch"
    supplied_id = raw.get("operation_id")
    supplied_digest = raw.get("operation_digest")
    if (
        not isinstance(supplied_id, str)
        or not isinstance(supplied_digest, str)
        or not secrets.compare_digest(supplied_id, operation_id)
        or not secrets.compare_digest(supplied_digest, operation_digest)
    ):
        return None, "confirmation_binding_mismatch"
    confirmed_at = raw.get("confirmed_at")
    if not isinstance(confirmed_at, str):
        return None, "confirmation_invalid"
    try:
        parsed_time = datetime.datetime.fromisoformat(confirmed_at.replace("Z", "+00:00"))
    except ValueError:
        return None, "confirmation_invalid"
    if parsed_time.tzinfo is None:
        return None, "confirmation_invalid"
    current = now or datetime.datetime.now(datetime.UTC)
    current = current.astimezone(datetime.UTC)
    parsed_time = parsed_time.astimezone(datetime.UTC)
    age = current - parsed_time
    if age < datetime.timedelta(0) or age > datetime.timedelta(minutes=5):
        return None, "confirmation_stale"
    return {key: str(raw[key]) for key in _CONFIRMATION_FIELDS}, None


def resolve_migration_authorization(
    workspace: object,
    confirmation: dict[str, str],
) -> tuple[str | None, str | None]:
    """Resolve the closed repository migration role and return its public digest."""
    if not isinstance(workspace, dict):
        return None, "migration_policy_invalid"
    authorization = workspace.get("authorization")
    migration = authorization.get("migration") if isinstance(authorization, dict) else None
    if not isinstance(migration, dict) or set(migration) != {
        "contract_version", "approver_roles"
    }:
        return None, "migration_policy_invalid"
    roles = migration.get("approver_roles")
    if (
        migration.get("contract_version")
        != "work-intake-migration-authorization.v1"
        or not isinstance(roles, list)
        or not roles
        or len(roles) != len(set(roles))
        or any(role not in _MIGRATION_ROLES for role in roles)
    ):
        return None, "migration_policy_invalid"
    role = confirmation["role"]
    if role not in roles:
        return None, "unauthorized_approver"
    return hashlib.sha256(role.encode("ascii")).hexdigest(), None


def _migration_confirmation_receipt(
    confirmation: dict[str, str], role_digest: str
) -> dict[str, object]:
    """Project accepted evidence without retaining its raw public role label."""
    return {
        "confirmation_id": confirmation["confirmation_id"],
        "action": confirmation["action"],
        "operation_id": confirmation["operation_id"],
        "operation_digest": confirmation["operation_digest"],
        "authorization_subject": confirmation["authorization_subject"],
        "authorization_role_digest": role_digest,
        "confirmed_at": confirmation["confirmed_at"],
        "authorization_source": confirmation["authorization_source"],
        "consumed_before_effect": True,
    }


def _migration_evidence_reused(
    ledger: dict[str, object], confirmation: dict[str, str]
) -> bool:
    """Return whether either opaque one-effect identifier is already durable."""
    for operation in ledger.get("operations", []):
        for receipt in operation.get("confirmation_receipts", []):
            if (
                receipt.get("confirmation_id") == confirmation["confirmation_id"]
                or receipt.get("authorization_subject")
                == confirmation["authorization_subject"]
            ):
                return True
    return False


def _migration_read_bytes(root: Path, relative_path: str) -> bytes | None:
    """Read a confined regular single-link file with pre/post identity checks."""
    path = confine_migration_path(root, relative_path, require_file=True)
    if path is None:
        return None
    descriptor: int | None = None
    try:
        before = path.stat()
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            return None
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        after = path.stat()
        if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            return None
        return b"".join(chunks)
    except (OSError, RuntimeError, ValueError):
        return None
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _migration_load_ledger(root: Path) -> tuple[dict[str, object] | None, str | None]:
    """Load and validate the ledger shape and semantic invariants in order."""
    ledger_path = root / _MIGRATION_LEDGER_FILE
    if not ledger_path.exists() and not ledger_path.is_symlink():
        return None, None
    raw = _migration_read_bytes(root, _MIGRATION_LEDGER_FILE)
    if raw is None:
        return None, "unsafe_path"
    try:
        ledger = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "ledger_invalid"
    shape_error = validate_migration_ledger_shape(ledger)
    if shape_error is not None:
        return None, shape_error
    return ledger, None


def _fsync_directory(directory: Path) -> None:
    """Flush a directory's entries so a created or renamed file survives a crash.

    Where a directory cannot be opened or flushed, such as on Windows or on a
    filesystem without directory fsync, the flush is skipped: the file or rename
    it follows has already landed, so it is never reported as unapplied.
    """
    try:
        directory_fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    except OSError:
        pass
    finally:
        os.close(directory_fd)


def _migration_failure(failure_point: str | None, point: str) -> None:
    """Raise at a named deterministic transaction seam for construction tests."""
    if failure_point == point:
        raise OSError("injected migration write failure")


def _migration_atomic_replace(
    path: Path,
    data: bytes,
    *,
    stage: str,
    failure_point: str | None,
) -> None:
    """Fsync and atomically replace one already-confined repository file."""
    _migration_failure(failure_point, f"{stage}_stage_before")
    descriptor, temp_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            temp_path.chmod(stat.S_IMODE(path.stat().st_mode))
        _migration_failure(failure_point, f"{stage}_stage_after")
        _migration_failure(failure_point, f"{stage}_replace_before")
        temp_path.replace(path)
        _migration_failure(failure_point, f"{stage}_replace_after")
        _fsync_directory(path.parent)
    finally:
        with contextlib.suppress(FileNotFoundError, OSError):
            temp_path.unlink()


def _migration_write_ledger(
    root: Path,
    ledger: dict[str, object],
    failure_point: str | None,
) -> None:
    """Validate then durably replace the repository-root migration ledger."""
    error = validate_migration_ledger_shape(ledger)
    if error is not None:
        raise ValueError(error)
    path = confine_migration_path(root, _MIGRATION_LEDGER_FILE, require_file=False)
    if path is None or (path.exists() and confine_migration_path(
        root, _MIGRATION_LEDGER_FILE, require_file=True
    ) is None):
        raise ValueError("unsafe_path")
    data = json.dumps(
        ledger, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii") + b"\n"
    _migration_atomic_replace(
        path, data, stage="ledger", failure_point=failure_point
    )


def _migration_toml_value(value: object) -> str:
    """Serialize the closed Group 2 entry subset as a TOML inline value."""
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, list):
        return "[" + ", ".join(_migration_toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(
            f"{key} = {_migration_toml_value(item)}"
            for key, item in sorted(value.items())
        ) + "}"
    raise ValueError("target_invalid")


def _migration_collection_bounds(
    workspace_text: str, ini_slug: str, collection: str
) -> tuple[int, int] | None:
    """Locate the interior bounds of one TOML lifecycle array."""
    section_name, key = collection.split(".", 1)
    if ini_slug:
        header = re.compile(
            rf"(?m)^\[(?:\"{re.escape(ini_slug)}\"|{re.escape(ini_slug)})\."
            rf"{re.escape(section_name)}\]\s*$"
        )
    else:
        header = re.compile(rf"(?m)^\[{re.escape(section_name)}\]\s*$")
    match = header.search(workspace_text)
    if match is None:
        return None
    next_header = re.search(r"(?m)^\[[^\n]+\]\s*$", workspace_text[match.end():])
    block_end = match.end() + next_header.start() if next_header else len(workspace_text)
    assignment = re.search(
        rf"(?m)^[ \t]*{re.escape(key)}[ \t]*=[ \t]*\[",
        workspace_text[match.end():block_end],
    )
    if assignment is None:
        return None
    opening = match.end() + assignment.end() - 1
    square_depth = 0
    brace_depth = 0
    quote = ""
    escaped = False
    in_comment = False
    for index in range(opening + 1, block_end):
        char = workspace_text[index]
        if in_comment:
            if char == "\n":
                in_comment = False
            continue
        if quote:
            if escaped:
                escaped = False
            elif char == "\\" and quote == '"':
                escaped = True
            elif char == quote:
                quote = ""
            continue
        if char in {'"', "'"}:
            quote = char
        elif char == "#":
            in_comment = True
        elif char == "[":
            square_depth += 1
        elif char == "]":
            if square_depth == 0 and brace_depth == 0:
                return opening + 1, index
            square_depth -= 1
        elif char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth -= 1
    return None


def _migration_content_without_comments(value: str) -> str:
    """Remove comments while preserving quoted hash characters."""
    output: list[str] = []
    quote = ""
    escaped = False
    in_comment = False
    for char in value:
        if in_comment:
            if char == "\n":
                in_comment = False
                output.append(char)
            continue
        if quote:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\" and quote == '"':
                escaped = True
            elif char == quote:
                quote = ""
        elif char in {'"', "'"}:
            quote = char
            output.append(char)
        elif char == "#":
            in_comment = True
        else:
            output.append(char)
    return "".join(output)


def _migration_collection_insert_offset(
    workspace_text: str,
    bounds: tuple[int, int],
    entry_index: int,
) -> int:
    """Return the exact element boundary for restoring one lifecycle position."""
    start, end = bounds
    element_starts: list[int] = []
    segment_start = start
    square_depth = 0
    brace_depth = 0
    quote = ""
    escaped = False
    in_comment = False
    for index in range(start, end):
        char = workspace_text[index]
        if in_comment:
            if char == "\n":
                in_comment = False
            continue
        if quote:
            if escaped:
                escaped = False
            elif char == "\\" and quote == '"':
                escaped = True
            elif char == quote:
                quote = ""
            continue
        if char in {'"', "'"}:
            quote = char
        elif char == "#":
            in_comment = True
        elif char == "[":
            square_depth += 1
        elif char == "]":
            square_depth -= 1
        elif char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth -= 1
        elif char == "," and square_depth == 0 and brace_depth == 0:
            segment = workspace_text[segment_start:index + 1]
            if _migration_content_without_comments(segment).strip().rstrip(",").strip():
                element_starts.append(segment_start)
            segment_start = index + 1
    tail = workspace_text[segment_start:end]
    if _migration_content_without_comments(tail).strip():
        element_starts.append(segment_start)
    return element_starts[entry_index] if entry_index < len(element_starts) else end


def _migration_apply_workspace_bytes(
    workspace_bytes: bytes,
    operation: dict[str, object],
) -> bytes:
    """Replace the exact legacy slice with one deterministic target entry."""
    text = workspace_bytes.decode("utf-8")
    legacy_slice = operation["legacy_slice"]
    if not isinstance(legacy_slice, str) or text.count(legacy_slice) != 1:
        raise ValueError("workspace_changed")
    without_legacy = text.replace(legacy_slice, "", 1)
    membership = operation["target_membership"]
    bounds = _migration_collection_bounds(
        without_legacy, membership["ini_slug"], membership["collection"]
    )
    if bounds is None:
        raise ValueError("target_invalid")
    insertion = "\n  " + _migration_toml_value(operation["target_entry"]) + ","
    converted = without_legacy[:bounds[1]] + insertion + without_legacy[bounds[1]:]
    tomllib.loads(converted)
    return converted.encode("utf-8")


def _migration_rollback_workspace_bytes(
    workspace_bytes: bytes,
    operation: dict[str, object],
) -> bytes:
    """Remove the canonical target and restore the recorded exact legacy slice."""
    workspace = tomllib.loads(workspace_bytes.decode("utf-8"))
    canonical = run_canonical_reconciliation(workspace)
    target = operation["target_entry"]
    target_membership = operation["target_membership"]
    matches = [
        membership
        for membership in canonical.memberships
        if membership.entry.path == target["path"]
        and membership.ini_slug == target_membership["ini_slug"]
        and membership.collection == target_membership["collection"]
    ]
    if len(matches) != 1:
        raise ValueError("recovery_conflict")
    target_slice = extract_legacy_source_slice(
        workspace_bytes,
        matches[0].ini_slug,
        matches[0].collection,
        matches[0].entry_index,
    )
    if target_slice is None:
        raise ValueError("recovery_conflict")
    text = workspace_bytes.decode("utf-8")
    if text.count(target_slice) != 1:
        raise ValueError("recovery_conflict")
    without_target = text.replace(target_slice, "", 1)
    source = operation["source_membership"]
    bounds = _migration_collection_bounds(
        without_target, source["ini_slug"], source["collection"]
    )
    if bounds is None:
        raise ValueError("recovery_conflict")
    offset = _migration_collection_insert_offset(
        without_target, bounds, source["entry_index"]
    )
    restored = without_target[:offset] + operation["legacy_slice"] + without_target[offset:]
    parsed = tomllib.loads(restored)
    restored_legacy_memberships = extract_legacy_migration_memberships(parsed)
    restored_matches = [
        membership
        for membership in restored_legacy_memberships
        if membership.ini_slug == source["ini_slug"]
        and membership.collection == source["collection"]
        and membership.entry_index == source["entry_index"]
    ]
    if len(restored_matches) != 1:
        raise ValueError("recovery_conflict")
    return restored.encode("utf-8")


def _migration_workspace_state(
    workspace_bytes: bytes,
    operation: dict[str, object],
) -> str:
    """Classify guarded workspace bytes using the operation's durable state."""
    fingerprint = hashlib.sha256(workspace_bytes).hexdigest()
    operation_state = operation.get("state")
    if operation_state == "pending":
        if fingerprint == operation["pre_apply_workspace_fingerprint"]:
            return "pre_apply"
        if fingerprint == operation.get("applied_workspace_fingerprint"):
            return "target"
    elif operation_state == "applied":
        if fingerprint == operation.get("applied_workspace_fingerprint"):
            return "target"
    elif operation_state == "rollback_pending":
        if fingerprint == operation.get("applied_workspace_fingerprint"):
            return "target"
        if fingerprint == operation.get("rolled_back_workspace_fingerprint"):
            return "rolled_back"
    elif operation_state == "rolled_back":
        if fingerprint == operation.get("rolled_back_workspace_fingerprint"):
            return "rolled_back"
    return "conflict"


@contextlib.contextmanager
def _migration_lock(root: Path):
    """Acquire the shared non-waiting workspace repair lock."""
    path = confine_migration_path(root, _MIGRATION_LOCK_FILE, require_file=False)
    if path is None or path.exists() or path.is_symlink():
        raise FileExistsError("lock busy")
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        yield
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        with contextlib.suppress(FileNotFoundError):
            path.unlink()


def _migration_result_error(code: str) -> dict[str, object]:
    """Build a stable non-echoing failure result."""
    next_actions = {
        "artifact_changed": "rerun-migration-plan",
        "confirmation_invalid": "replace-confirmation",
        "confirmation_stale": "replace-confirmation",
        "confirmation_reused": "replace-confirmation",
        "confirmation_binding_mismatch": "replace-confirmation",
        "invalid_selection": "revise-selection",
        "ledger_invalid": "repair-migration-ledger",
        "ledger_changed": "rerun-migration-plan",
        "migration_policy_invalid": "repair-migration-policy",
        "operation_missing": "review-migration-ledger",
        "operation_state_conflict": "recover-migration-state",
        "recovery_conflict": "recover-migration-state",
        "selection_mismatch": "revise-selection",
        "sensitive_legacy_content": "sanitize-legacy-source",
        "unauthorized_approver": "use-authorized-approver",
        "unsafe_path": "repair-repository-paths",
        "workspace_changed": "rerun-migration-plan",
        "write_failed": "retry-migration-effect",
    }
    return build_migration_result(code, next_action=next_actions.get(code, "review-migration"))


def _migration_find_operation(
    ledger: dict[str, object], operation_id: str
) -> dict[str, object] | None:
    """Return exactly one ledger operation by identifier."""
    matches = [
        operation
        for operation in ledger["operations"]
        if operation.get("operation_id") == operation_id
    ]
    return matches[0] if len(matches) == 1 else None


def apply_migration_operation(
    root: Path,
    selection_raw: object,
    operation_id: str,
    confirmation_raw: object,
    *,
    now: datetime.datetime | None = None,
    failure_point: str | None = None,
) -> dict[str, object]:
    """Apply or recover one ledger-first migration under the shared lock."""
    try:
        with _migration_lock(root):
            workspace_bytes = _migration_read_bytes(root, "workspace.toml")
            if workspace_bytes is None:
                return _migration_result_error("unsafe_path")
            try:
                workspace = tomllib.loads(workspace_bytes.decode("utf-8"))
            except (UnicodeDecodeError, tomllib.TOMLDecodeError):
                return _migration_result_error("workspace_changed")
            ledger, ledger_error = _migration_load_ledger(root)
            if ledger_error is not None:
                return _migration_result_error(ledger_error)
            operation = _migration_find_operation(ledger, operation_id) if ledger else None
            if ledger is None:
                planned = compute_migration_plan(root, root / "workspace.toml", selection_raw)
                if (
                    planned.result["result_code"] != "planned"
                    or planned.proposed_operation is None
                ):
                    return planned.result
                operation = planned.proposed_operation
                if operation["operation_id"] != operation_id:
                    return _migration_result_error("selection_mismatch")
                canonical = run_canonical_reconciliation(workspace, root)
                ledger = {
                    "contract_version": "work-intake-migration-ledger.v1",
                    "repository_identity": canonical_repository_identity(
                        workspace, canonical, root
                    ),
                    "operations": [operation],
                }
            elif operation is None:
                return _migration_result_error("operation_missing")
            if operation["operation_digest"] != _migration_operation_digest(
                operation, ledger["repository_identity"]
            ):
                return _migration_result_error("ledger_changed")
            selection, selection_error = validate_migration_selection(selection_raw)
            if selection is None:
                return _migration_result_error(selection_error or "invalid_selection")
            if (
                migration_selection_digest(selection)
                != operation.get("selection_digest")
                or selection.workspace_fingerprint
                != operation["pre_apply_workspace_fingerprint"]
                or selection.source_membership != operation["source_membership"]
                or selection.target_entry_raw != operation["target_entry"]
                or selection.target_membership != operation["target_membership"]
                or selection.owning_processor != operation["owning_processor"]
            ):
                return _migration_result_error("selection_mismatch")
            confirmation, confirmation_error = validate_migration_confirmation(
                confirmation_raw,
                action="apply",
                operation_id=operation_id,
                operation_digest=operation["operation_digest"],
                now=now,
            )
            if confirmation is None:
                return _migration_result_error(
                    confirmation_error or "confirmation_invalid"
                )
            role_digest, authorization_error = resolve_migration_authorization(
                workspace, confirmation
            )
            if role_digest is None:
                return _migration_result_error(
                    authorization_error or "migration_policy_invalid"
                )
            if _migration_evidence_reused(ledger, confirmation):
                return _migration_result_error("confirmation_reused")
            state = _migration_workspace_state(workspace_bytes, operation)
            if operation["state"] == "applied":
                if state != "target":
                    return _migration_result_error("recovery_conflict")
                return build_migration_result(
                    "already_applied",
                    next_action="none-required",
                    operation_id=operation_id,
                    operation_digest=operation["operation_digest"],
                    ledger_state="applied",
                )
            if operation["state"] != "pending":
                return _migration_result_error("operation_state_conflict")
            if state == "conflict":
                return _migration_result_error("recovery_conflict")
            artifact = operation["artifact_receipt"]
            artifact_bytes = _migration_read_bytes(root, artifact["path"])
            if (
                artifact_bytes is None
                or hashlib.sha256(artifact_bytes).hexdigest()
                != artifact["fingerprint"]
            ):
                return _migration_result_error("artifact_changed")
            if state == "pre_apply":
                legacy_workspace_bytes = workspace_bytes
            else:
                try:
                    legacy_workspace_bytes = _migration_rollback_workspace_bytes(
                        workspace_bytes, operation
                    )
                except ValueError:
                    return _migration_result_error("recovery_conflict")
                if hashlib.sha256(legacy_workspace_bytes).hexdigest() != operation[
                    "pre_apply_workspace_fingerprint"
                ]:
                    return _migration_result_error("recovery_conflict")
            expected_converted = _migration_apply_workspace_bytes(
                legacy_workspace_bytes, operation
            )
            expected_applied = hashlib.sha256(expected_converted).hexdigest()
            recorded_applied = operation.get("applied_workspace_fingerprint")
            if recorded_applied is not None and recorded_applied != expected_applied:
                return _migration_result_error("ledger_changed")
            if state == "target" and expected_converted != workspace_bytes:
                return _migration_result_error("recovery_conflict")
            operation["applied_workspace_fingerprint"] = expected_applied
            converted = expected_converted if state == "pre_apply" else None
            operation["confirmation_receipts"].append(
                _migration_confirmation_receipt(confirmation, role_digest)
            )
            _migration_write_ledger(root, ledger, failure_point)
            if state == "pre_apply":
                assert converted is not None
                workspace_path = confine_migration_path(
                    root, "workspace.toml", require_file=True
                )
                if workspace_path is None:
                    return _migration_result_error("unsafe_path")
                _migration_atomic_replace(
                    workspace_path,
                    converted,
                    stage="workspace",
                    failure_point=failure_point,
                )
                workspace_bytes = converted
            if hashlib.sha256(workspace_bytes).hexdigest() != operation.get(
                "applied_workspace_fingerprint"
            ):
                return _migration_result_error("recovery_conflict")
            operation["state"] = "applied"
            _migration_write_ledger(root, ledger, failure_point)
            return build_migration_result(
                "applied",
                next_action="review-workspace-status",
                operation_id=operation_id,
                operation_digest=operation["operation_digest"],
                ledger_state="applied",
            )
    except FileExistsError:
        return _migration_result_error("lock_busy")
    except (OSError, RuntimeError, ValueError):
        return _migration_result_error("write_failed")


def rollback_migration_operation(
    root: Path,
    operation_id: str,
    confirmation_raw: object,
    *,
    now: datetime.datetime | None = None,
    failure_point: str | None = None,
) -> dict[str, object]:
    """Rollback or recover one operation without reading or deleting its artifact."""
    try:
        with _migration_lock(root):
            workspace_bytes = _migration_read_bytes(root, "workspace.toml")
            if workspace_bytes is None:
                return _migration_result_error("unsafe_path")
            try:
                workspace = tomllib.loads(workspace_bytes.decode("utf-8"))
            except (UnicodeDecodeError, tomllib.TOMLDecodeError):
                return _migration_result_error("workspace_changed")
            ledger, ledger_error = _migration_load_ledger(root)
            if ledger_error is not None:
                return _migration_result_error(ledger_error)
            if ledger is None:
                return _migration_result_error("operation_missing")
            operation = _migration_find_operation(ledger, operation_id)
            if operation is None:
                return _migration_result_error("operation_missing")
            if operation["operation_digest"] != _migration_operation_digest(
                operation, ledger["repository_identity"]
            ):
                return _migration_result_error("ledger_changed")
            confirmation, confirmation_error = validate_migration_confirmation(
                confirmation_raw,
                action="rollback",
                operation_id=operation_id,
                operation_digest=operation["operation_digest"],
                now=now,
            )
            if confirmation is None:
                return _migration_result_error(
                    confirmation_error or "confirmation_invalid"
                )
            role_digest, authorization_error = resolve_migration_authorization(
                workspace, confirmation
            )
            if role_digest is None:
                return _migration_result_error(
                    authorization_error or "migration_policy_invalid"
                )
            if _migration_evidence_reused(ledger, confirmation):
                return _migration_result_error("confirmation_reused")
            state = _migration_workspace_state(workspace_bytes, operation)
            if operation["state"] == "rolled_back":
                if state != "rolled_back":
                    return _migration_result_error("recovery_conflict")
                return build_migration_result(
                    "already_rolled_back",
                    next_action="none-required",
                    operation_id=operation_id,
                    operation_digest=operation["operation_digest"],
                    ledger_state="rolled_back",
                )
            operation_state = operation["state"]
            if operation_state not in {"applied", "rollback_pending"}:
                return _migration_result_error("operation_state_conflict")
            if (
                (operation_state == "applied" and state != "target")
                or (
                    operation_state == "rollback_pending"
                    and state not in {"target", "rolled_back"}
                )
            ):
                return _migration_result_error("recovery_conflict")
            if state == "target":
                restored = _migration_rollback_workspace_bytes(
                    workspace_bytes, operation
                )
                expected_rolled_back = hashlib.sha256(restored).hexdigest()
                recorded_rolled_back = operation.get(
                    "rolled_back_workspace_fingerprint"
                )
                if (
                    recorded_rolled_back is not None
                    and recorded_rolled_back != expected_rolled_back
                ):
                    return _migration_result_error("ledger_changed")
                operation["rolled_back_workspace_fingerprint"] = (
                    expected_rolled_back
                )
            else:
                restored = None
            operation["confirmation_receipts"].append(
                _migration_confirmation_receipt(confirmation, role_digest)
            )
            operation["state"] = "rollback_pending"
            _migration_write_ledger(root, ledger, failure_point)
            if state == "target":
                assert restored is not None
                workspace_path = confine_migration_path(
                    root, "workspace.toml", require_file=True
                )
                if workspace_path is None:
                    return _migration_result_error("unsafe_path")
                _migration_atomic_replace(
                    workspace_path,
                    restored,
                    stage="workspace",
                    failure_point=failure_point,
                )
                workspace_bytes = restored
            if hashlib.sha256(workspace_bytes).hexdigest() != operation.get(
                "rolled_back_workspace_fingerprint"
            ):
                return _migration_result_error("recovery_conflict")
            operation["state"] = "rolled_back"
            _migration_write_ledger(root, ledger, failure_point)
            return build_migration_result(
                "rolled_back",
                next_action="review-workspace-status",
                operation_id=operation_id,
                operation_digest=operation["operation_digest"],
                ledger_state="rolled_back",
            )
    except FileExistsError:
        return _migration_result_error("lock_busy")
    except (OSError, RuntimeError, ValueError):
        return _migration_result_error("write_failed")


def recover_migration_operation(
    root: Path,
    operation_id: str,
    confirmation_raw: object,
    *,
    action: str,
    selection_raw: object | None = None,
    now: datetime.datetime | None = None,
    failure_point: str | None = None,
) -> dict[str, object]:
    """Resume a pending apply or rollback with new one-effect evidence."""
    if action == "apply" and selection_raw is not None:
        return apply_migration_operation(
            root,
            selection_raw,
            operation_id,
            confirmation_raw,
            now=now,
            failure_point=failure_point,
        )
    if action == "rollback":
        return rollback_migration_operation(
            root,
            operation_id,
            confirmation_raw,
            now=now,
            failure_point=failure_point,
        )
    return _migration_result_error("operation_state_conflict")


def _migration_input_json(
    root: Path,
    relative_path: str,
    *,
    invalid_code: str = "confirmation_invalid",
) -> tuple[object | None, str | None]:
    """Read one human-authored closed JSON input without following links."""
    raw = _migration_read_bytes(root, relative_path)
    if raw is None:
        return None, "unsafe_path"
    try:
        return json.loads(raw.decode("utf-8")), None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, invalid_code


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
    elif argv and not argv[0].startswith("-"):
        print("workspace-status: unknown subcommand", file=sys.stderr)
        _emit({
            "schema_version": 1,
            "mode": "error",
            "reason": "unknown_subcommand",
        })
        return 2
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
        description="workspace-status: parse workspace.toml and emit JSON",
        epilog="migration rollback subcommand: repair-rollback",
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
    if subcommand == "status":
        parser.add_argument(
            "--include-evaluations",
            action="store_true",
            default=False,
            help="Restore canonical.evaluations, the full per-entry evaluation "
                 "list. It grows with the size of the workspace and can dominate "
                 "the payload; the dispatch decisions it carries are already in "
                 "canonical.ready/active/blocked/findings.",
        )
    if subcommand == "selected-membership":
        parser.add_argument(
            "--spec-dir",
            action="append",
            default=[],
            help="Repository-relative docs/specs/<slug> directory to inspect",
        )
    if subcommand == "prune":
        parser.add_argument(
            "--select",
            action="append",
            default=[],
            help="Repository-relative docs/specs/<slug> directory to remove",
        )
        parser.add_argument(
            "--preview",
            action="store_true",
            default=False,
            help="Emit the unsigned operation challenge without mutation",
        )
        parser.add_argument(
            "--confirmation-file",
            default=None,
            help="Confined JSON confirmation containing independent authorization",
        )
    if subcommand == "retirement-candidates":
        parser.add_argument(
            "--run-date",
            required=True,
            help="Calendar date to use for deterministic age reporting (YYYY-MM-DD)",
        )
        parser.add_argument(
            "--stale-after-days",
            type=int,
            default=30,
            help="Recorded-change age threshold in days (default: 30)",
        )
    migration_subcommand = subcommand in {
        "repair-plan", "repair-apply", "repair-rollback"
    }
    if migration_subcommand:
        parser.add_argument(
            "--plan-file",
            default=None,
            help="Override plan file path (default: <root>/.workspace-repair-plan.json)",
        )
    if migration_subcommand:
        parser.add_argument(
            "--migration-selection",
            default=None,
            help="Reviewed repository-relative migration selection JSON",
        )
    if migration_subcommand:
        parser.add_argument(
            "--operation-id",
            default=None,
            help="Exact migration operation identifier",
        )
        parser.add_argument(
            "--confirmation-file",
            default=None,
            help="Human-authored current-session confirmation JSON",
        )
    if migration_subcommand:
        parser.add_argument(
            "--yes",
            action="store_true",
            default=False,
            help="Required explicit confirmation to apply the repair plan",
        )
    args = parser.parse_args(argv)
    root = Path(args.root)

    if subcommand == "prune" and not args.select:
        print("workspace-status: prune: empty_selection", file=sys.stderr)
        _emit({"error": {"code": "empty_selection"}})
        return 2

    if subcommand == "selected-membership" and not args.spec_dir:
        print("workspace-status: selected-membership requires --spec-dir", file=sys.stderr)
        _emit({
            "schema_version": 1,
            "mode": "selected-membership",
            "reason": "empty_selection",
        })
        return 2

    if subcommand == "retirement-candidates":
        if not _bind_retirement_command():
            print(
                "workspace-status: retirement-candidates: command_load_failed",
                file=sys.stderr,
            )
            return 2
        try:
            document = retirement_candidates_document(
                root,
                run_date=args.run_date,
                stale_after_days=args.stale_after_days,
            )
            errors = validate_retirement_document(root, document)
        except (OSError, RuntimeError, ValueError):
            print(
                "workspace-status: retirement-candidates: invalid_input",
                file=sys.stderr,
            )
            return 2
        if errors:
            print(
                "workspace-status: retirement-candidates: contract_invalid",
                file=sys.stderr,
            )
            return 2
        _emit(document)
        return 0

    if not _bind_engine():
        if subcommand in {"status", "reconcile", "explain"}:
            _emit(_canonical_failure_payload(subcommand, "configuration_mismatch"))
        else:
            _emit({
                "schema_version": 1,
                "mode": subcommand,
                "applied": False,
                "reason": "engine_load_failed",
            })
        return 2

    if subcommand == "prune":
        try:
            if args.preview:
                prune_result = prune_preview(root, args.select)
            elif args.confirmation_file is None:
                prune_result = prune_execute(root, args.select, {})
            else:
                prune_result = prune_execute(
                    root,
                    args.select,
                    None,
                    confirmation_file=args.confirmation_file,
                )

            prune_error = prune_result.get("error")
            if isinstance(prune_error, dict):
                code = prune_error.get("code", "closure_failed")
                print(f"workspace-status: prune: {code}", file=sys.stderr)
                _emit(prune_result)
                return 2

            if args.preview:
                _emit(prune_result)
                return 0

            closure = prune_result.get("closure")
            if not isinstance(closure, dict) or not (
                closure.get("artifact_absent") is True
                and closure.get("membership_absent") is True
            ):
                print("workspace-status: prune: closure_failed", file=sys.stderr)
                _emit({"error": {"code": "closure_failed"}})
                return 2
            _emit(prune_result)
            return 0
        except Exception as exc:
            print(
                f"workspace-status: prune: invalid_workspace: {type(exc).__name__}",
                file=sys.stderr,
            )
            _emit({"error": {"code": "invalid_workspace"}})
            return 2

    try:
        # Validate root before checking workspace.toml.
        # If root is a file (not a dir), Path.exists() returns False via ENOTDIR
        # without raising, which would falsely report workspace_present: false.
        if not root.is_dir():
            raise NotADirectoryError(f"--root is not a directory: {root}")

        workspace_toml = root / "workspace.toml"

        migration_mode = (
            subcommand == "repair-rollback"
            or getattr(args, "migration_selection", None) is not None
            or getattr(args, "operation_id", None) is not None
            or getattr(args, "confirmation_file", None) is not None
        )

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
                if migration_mode:
                    _emit({
                        "schema_version": 1,
                        "mode": subcommand,
                        "workspace_present": False,
                        "workspace_root": ".",
                        "migration": build_migration_result(
                            "workspace_absent",
                            next_action="create-workspace",
                            ledger_state="absent",
                        ),
                    })
                    return 1
                _emit({
                    "schema_version": 1,
                    "mode": subcommand,
                    "workspace_present": False,
                    "workspace_root": ".",
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
                    if migration_mode:
                        _emit({
                            "schema_version": 1,
                            "mode": subcommand,
                            "workspace_present": True,
                            "workspace_root": ".",
                            "migration": _migration_result_error("unsafe_path"),
                        })
                    else:
                        _emit(
                            _canonical_failure_payload(
                                subcommand, "configuration_mismatch"
                            )
                        )
                    return 2

        if subcommand == "repair-apply" and migration_mode:
            supplied = (
                args.migration_selection,
                args.operation_id,
                args.confirmation_file,
            )
            if (
                not all(isinstance(value, str) and value for value in supplied)
                or args.plan_file is not None
                or args.yes
            ):
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "workspace_present": workspace_toml.exists(),
                    "workspace_root": ".",
                    "migration": _migration_result_error("confirmation_invalid"),
                })
                return 2
            if not workspace_toml.exists():
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "workspace_present": False,
                    "workspace_root": ".",
                    "migration": build_migration_result(
                        "workspace_absent",
                        next_action="create-workspace",
                        ledger_state="absent",
                    ),
                })
                return 1
            selection_raw, selection_input_error = _migration_input_json(
                root, args.migration_selection, invalid_code="invalid_selection"
            )
            confirmation_raw, confirmation_input_error = _migration_input_json(
                root, args.confirmation_file
            )
            if selection_input_error is not None or confirmation_input_error is not None:
                code = selection_input_error or confirmation_input_error or "confirmation_invalid"
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "workspace_present": True,
                    "workspace_root": ".",
                    "migration": _migration_result_error(code),
                })
                return 2
            migration_result = apply_migration_operation(
                root,
                selection_raw,
                args.operation_id,
                confirmation_raw,
            )
            _emit({
                "schema_version": 1,
                "mode": "repair-apply",
                "workspace_present": True,
                "workspace_root": ".",
                "migration": migration_result,
            })
            return 0 if migration_result["result_code"] in {
                "applied", "already_applied"
            } else 2

        if subcommand == "repair-rollback":
            if (
                not args.operation_id
                or not args.confirmation_file
                or args.migration_selection is not None
                or args.plan_file is not None
                or args.yes
            ):
                _emit({
                    "schema_version": 1,
                    "mode": "repair-rollback",
                    "workspace_present": True,
                    "workspace_root": ".",
                    "migration": _migration_result_error("confirmation_invalid"),
                })
                return 2
            confirmation_raw, input_error = _migration_input_json(
                root, args.confirmation_file
            )
            if input_error is not None:
                _emit({
                    "schema_version": 1,
                    "mode": "repair-rollback",
                    "workspace_present": True,
                    "workspace_root": ".",
                    "migration": _migration_result_error(input_error),
                })
                return 2
            migration_result = rollback_migration_operation(
                root, args.operation_id, confirmation_raw
            )
            _emit({
                "schema_version": 1,
                "mode": "repair-rollback",
                "workspace_present": True,
                "workspace_root": ".",
                "migration": migration_result,
            })
            return 0 if migration_result["result_code"] in {
                "rolled_back", "already_rolled_back"
            } else 2

        if subcommand == "repair-plan" and (
            args.operation_id is not None
            or args.confirmation_file is not None
            or args.yes
        ):
            _emit({
                "schema_version": 1,
                "mode": "repair-plan",
                "workspace_present": True,
                "workspace_root": ".",
                "migration": build_migration_result(
                    "invalid_selection", next_action="remove-mixed-arguments"
                ),
            })
            return 2

        if subcommand == "repair-plan" and args.migration_selection is not None:
            if args.plan_file is not None:
                _emit({
                    "schema_version": 1,
                    "mode": "repair-plan",
                    "workspace_present": True,
                    "workspace_root": ".",
                    "migration": build_migration_result(
                        "invalid_selection", next_action="remove-plan-file"
                    ),
                })
                return 2
            selection_raw, selection_input_error = _migration_input_json(
                root, args.migration_selection, invalid_code="invalid_selection"
            )
            if selection_input_error is not None:
                _emit({
                    "schema_version": 1,
                    "mode": "repair-plan",
                    "workspace_present": True,
                    "workspace_root": ".",
                    "migration": _migration_result_error(selection_input_error),
                })
                return 2
            migration_plan = compute_migration_plan(root, workspace_toml, selection_raw)
            payload = {
                "schema_version": 1,
                "mode": "repair-plan",
                "workspace_present": True,
                "workspace_root": ".",
                "migration": migration_plan.result,
            }
            if migration_plan.finding is not None:
                payload["migration_finding"] = migration_plan.finding
            if migration_plan.proposed_operation is not None:
                payload["proposed_operation"] = migration_plan.proposed_operation
            _emit(payload)
            return 0 if migration_plan.result["result_code"] in {
                "planned", "artifact_missing", "manual_routing_required"
            } else 2

        if subcommand == "repair-plan":
            plan_path = Path(args.plan_file) if args.plan_file else (root / _DEFAULT_PLAN_FILE)
            # Write-path symlink guard: check before confinement resolves the path.
            # If the output location is already a symlink, replace() on the resolved
            # path would silently overwrite the symlink's in-root target rather than
            # the named entry. Reject here so no source file is clobbered.
            if plan_path.is_symlink():
                _emit({
                    "schema_version": 1,
                    "mode": "repair-plan",
                    "applied": False,
                    "reason": "plan_file_is_symlink",
                })
                return 2
            # Confinement resolves the path and verifies it stays within root —
            # this covers direct paths and relative traversal.
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
            # Guard: reject plan-file == .workspace-repair.lock. The lock file is
            # ephemeral, so samefile() fails when it doesn't exist. Compare the
            # resolved parent (always canonical on HFS+/NTFS) plus a casefold on
            # the name to catch .WORKSPACE-REPAIR.LOCK on case-insensitive volumes.
            _lock_reserved_rp = (root / ".workspace-repair.lock").resolve()
            if (plan_path.name.casefold() == _lock_reserved_rp.name.casefold()
                    and plan_path.parent == _lock_reserved_rp.parent):
                _emit({
                    "schema_version": 1,
                    "mode": "repair-plan",
                    "applied": False,
                    "reason": "plan_file_is_lock_path",
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
            result = analyze(
                root,
                workspace_bytes=_plan_ws_bytes,
                cooling_enabled=False,
            )
            plan = compute_repair_plan(result, workspace_toml, workspace_fingerprint=_plan_ws_fp)
            data = _build_repair_plan_json(root, result, plan, _plan_ws_bytes)
            # Emit stdout first — plan JSON always available even if file write fails.
            # Echoed parts follow the echo rules; the plan file below keeps them whole.
            _emit(_echo_repair_plan(data))
            # Persisted plan must not contain workspace_root (an absolute path that
            # would violate the privacy policy if a custom --plan-file is committed).
            # repair-apply derives the root from --root at invocation time; it never
            # reads workspace_root from the plan file.
            file_data = {k: v for k, v in data.items() if k != "workspace_root"}
            tmp_plan: str | None = None
            try:
                fd, tmp_plan = tempfile.mkstemp(
                    dir=plan_path.parent,
                    prefix=".plan.",
                    suffix=".tmp",
                )
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(json.dumps(file_data, sort_keys=True, allow_nan=False) + "\n")
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
            # Guard: reject plan-file == .workspace-repair.lock. Use casefold on
            # the name to catch .WORKSPACE-REPAIR.LOCK on case-insensitive volumes.
            _lock_reserved_ra = (root / ".workspace-repair.lock").resolve()
            if (plan_path.name.casefold() == _lock_reserved_ra.name.casefold()
                    and plan_path.parent == _lock_reserved_ra.parent):
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": False,
                    "reason": "plan_file_is_lock_path",
                })
                return 2
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
            except UnicodeDecodeError:
                print("workspace-status: plan file is not valid UTF-8", file=sys.stderr)
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": False,
                    "reason": "plan_file_parse_error",
                })
                return 2
            except OSError as _re:
                _rmsg = str(_re)
                with contextlib.suppress(OSError, RuntimeError):
                    _rmsg = _rmsg.replace(str(root.resolve()), "<root>")
                print(f"workspace-status: plan file unreadable: {_rmsg}", file=sys.stderr)
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": False,
                    "reason": "plan_file_unreadable",
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
            # tomlkit guard — only needed when there are operations to apply
            if ops:
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
            # Acquire lock before ANY precondition validation — a concurrent non-empty
            # apply can rewrite workspace.toml between an out-of-lock read and result
            # emission. The lock serialises the fingerprint check for both empty and
            # non-empty plans so that before_workspace_digest is always authoritative.
            lock_path = root / ".workspace-repair.lock"
            lock_fd = -1
            try:
                lock_fd = os.open(
                    str(lock_path),
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
            except FileExistsError:
                # Fail closed immediately — no waiting, no stale recovery.
                # Stale-lock recovery via PID probing is racey: two concurrent
                # processes that both classify the same lock as stale can both
                # unlink and re-acquire it, breaking mutual exclusion.
                print("workspace-status: repair lock is held by another process", file=sys.stderr)
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": False,
                    "reason": "lock_busy",
                })
                return 2
            except OSError as _le:
                _lmsg = str(_le)
                with contextlib.suppress(OSError, RuntimeError):
                    _lmsg = _lmsg.replace(str(root.resolve()), "<root>")
                print(f"workspace-status: lock create failed: {_lmsg}", file=sys.stderr)
                _emit({
                    "schema_version": 1,
                    "mode": "repair-apply",
                    "applied": False,
                    "reason": "lock_create_failed",
                })
                return 2
            try:
                # Write PID to the lock file for diagnostics (e.g. manual
                # `cat .workspace-repair.lock`), then release the descriptor.
                with contextlib.suppress(OSError):
                    os.write(lock_fd, str(os.getpid()).encode())
                os.close(lock_fd)
                lock_fd = -1
                if not ops:
                    # Empty plan: re-resolve under the lock so a symlink retargeted
                    # between the initial confinement check and lock acquisition is
                    # caught here rather than passing with a stale fingerprint.
                    _empty_ws_target = workspace_toml.resolve()
                    try:
                        _empty_ws_target.relative_to(root.resolve())
                    except (OSError, RuntimeError, ValueError):
                        _emit({
                            "schema_version": 1,
                            "mode": "repair-apply",
                            "applied": False,
                            "reason": "workspace_outside_root",
                        })
                        return 2
                    try:
                        _empty_bytes = _empty_ws_target.read_bytes()
                    except OSError as _erb:
                        _emsg = str(_erb)
                        with contextlib.suppress(OSError, RuntimeError):
                            _emsg = _emsg.replace(str(root.resolve()), "<root>")
                        print(f"workspace-status: workspace read failed: {_emsg}", file=sys.stderr)
                        _emit({
                            "schema_version": 1,
                            "mode": "repair-apply",
                            "applied": False,
                            "reason": "workspace_read_failed",
                        })
                        return 2
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
                # Non-empty: resolve first, then read — ensures the fingerprint and the
                # write both target the same inode. Resolving before reading closes the
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
                try:
                    workspace_bytes = workspace_write_target.read_bytes()
                except OSError as _rbe:
                    _emsg = str(_rbe)
                    with contextlib.suppress(OSError, RuntimeError):
                        _emsg = _emsg.replace(str(root.resolve()), "<root>")
                    print(f"workspace-status: workspace read failed: {_emsg}", file=sys.stderr)
                    _emit({
                        "schema_version": 1,
                        "mode": "repair-apply",
                        "applied": False,
                        "reason": "workspace_read_failed",
                    })
                    return 2
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
                edge_report: dict = {}
                try:
                    applied, per_op, written_bytes = _apply_operations(
                        root, ops, workspace_bytes, workspace_write_target, edge_report
                    )
                except (OSError, RuntimeError) as _ae:
                    # mkstemp/write/chmod/replace failure OR concurrent-write
                    # detection: emit structured JSON so machine callers can
                    # distinguish this from other exit-2 reasons.
                    _ae_str = str(_ae)
                    _write_reason = (
                        "workspace_modified_concurrently"
                        if "concurrent" in _ae_str
                        else "repair_write_failed"
                    )
                    with contextlib.suppress(OSError, RuntimeError):
                        _ae_str = _ae_str.replace(str(root.resolve()), "<root>")
                    print(f"workspace-status: repair write error: {_ae_str}", file=sys.stderr)
                    _emit({
                        "schema_version": 1,
                        "mode": "repair-apply",
                        "applied": False,
                        "reason": _write_reason,
                    })
                    return 2
                # Compute after_digest from the serialized content captured inside
                # _apply_operations — avoids a second disk read and guarantees the
                # digest describes exactly what was written, even if a post-write
                # read_bytes() were to fail.
                after_digest = (
                    hashlib.sha256(written_bytes).hexdigest()
                    if written_bytes is not None
                    else before_digest
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
                    **edge_report,
                })
                return (
                    0
                    if edge_report.get("edges_equal", True)
                    and edge_report.get("captured_equal", True)
                    else 1
                )
            finally:
                if lock_fd >= 0:
                    with contextlib.suppress(OSError):
                        os.close(lock_fd)
                with contextlib.suppress(OSError):
                    lock_path.unlink()

        if subcommand == "selected-membership":
            selection = selected_membership_status(root, args.spec_dir)
            selection_error = selection.get("error")
            if isinstance(selection_error, dict):
                reason = selection_error.get("code", "invalid_workspace")
                print(f"workspace-status: selected-membership: {reason}", file=sys.stderr)
                _emit({
                    "schema_version": 1,
                    "mode": "selected-membership",
                    "reason": reason,
                })
                return 2
            data = {
                "schema_version": 1,
                "mode": "selected-membership",
                "results": selection["results"],
            }
        elif subcommand == "explain":
            result = analyze_bounded(root)
            public_selector, explain_result = _canonical_explain(root, result, args.item)
            data = _build_explain_json(root, result, public_selector, explain_result)
        elif subcommand == "status":
            result = analyze_bounded(root)
            data = _build_json(root, result, "status")
            if not args.include_evaluations:
                # Orientation payload. Dropped here, after _build_json's closeout
                # projection has consumed canonical["evaluations"] internally, so
                # narrowing the emitted surface cannot change any decision.
                data["canonical"].pop("evaluations", None)
        else:
            result = analyze(root)
            data = _build_json(root, result, "reconcile")

        _emit(data)
        return 0
    except Exception as exc:
        code = (
            "unsafe_path"
            if isinstance(exc, UnsafeMigrationPathError)
            else (
                "invalid_workspace"
                if isinstance(exc, tomllib.TOMLDecodeError)
                else "configuration_mismatch"
            )
        )
        # Only the unclassified fallback. `unsafe_path` and `invalid_workspace`
        # are recognized refusals that already carry their own emitted code, and
        # a shipped criterion requires them to stay silent on stderr;
        # `configuration_mismatch` is the branch that swallows genuine
        # programming errors, so it is the one that needs a diagnostic.
        #
        # The exception type only, never `str(exc)`: an exception message
        # routinely carries an absolute host path, and this stream is read into
        # agent context. The type name is the largest disclosure-free signal,
        # and it is what the exit-code contract at the top of this module
        # promises — one line on stderr, no traceback, no internal paths.
        if code == "configuration_mismatch":
            print(
                f"workspace-status: {code}: {type(exc).__name__}",
                file=sys.stderr,
            )
        payload = _canonical_failure_payload(subcommand, code)
        if subcommand in {"status", "reconcile"}:
            # The listing never reads the registry, so a failed registry
            # still gets the same `captured` object.
            with contextlib.suppress(Exception):
                payload["captured"] = _captured_projection(
                    root, _engine._resolve_cooled_state(root)[0]
                )
        _emit(payload)
        return 2


if __name__ == "__main__":
    sys.exit(main())
