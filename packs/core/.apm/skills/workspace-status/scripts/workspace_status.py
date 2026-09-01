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
analyze: Any = None
analyze_bounded: Any = None
explain_item: Any = None
compute_type2_cleanup: Any = None
compute_repair_plan: Any = None
compute_migration_plan: Any = None
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
canonical_repository_identity: Any = None
_safe_spec_path: Any = None
_spec_slug_from_workspace_path: Any = None
_repair_entry_eligibility: Any = None
_migration_operation_digest: Any = None
project_closeout_status: Any = None

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
    try:
        engine_spec = importlib.util.spec_from_file_location(
            "workspace_status_engine", engine_path
        )
        engine_mod = importlib.util.module_from_spec(engine_spec)  # type: ignore[arg-type]
        # Register before exec_module so dataclass annotation resolution works
        # with `from __future__ import annotations`.
        sys.modules.setdefault("workspace_status_engine", engine_mod)
        engine_spec.loader.exec_module(engine_mod)  # type: ignore[union-attr]
    except Exception:
        return False
    globals().update({
        "analyze": engine_mod.analyze,
        "analyze_bounded": engine_mod.analyze_bounded,
        "explain_item": engine_mod.explain_item,
        "compute_type2_cleanup": engine_mod.compute_type2_cleanup,
        "compute_repair_plan": engine_mod.compute_repair_plan,
        "compute_migration_plan": engine_mod.compute_migration_plan,
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
        "canonical_repository_identity": engine_mod.canonical_repository_identity,
        "_safe_spec_path": engine_mod._safe_spec_path,
        "_spec_slug_from_workspace_path": engine_mod._spec_slug_from_workspace_path,
        "_repair_entry_eligibility": engine_mod._repair_entry_eligibility,
        "_migration_operation_digest": engine_mod._migration_operation_digest,
        "project_closeout_status": engine_mod.project_closeout_status,
    })
    _ENGINE_BOUND = True
    return True


# ── Subcommand routing ────────────────────────────────────────────────────────

_SUBCOMMANDS = frozenset({
    "status",
    "explain",
    "reconcile",
    "repair-plan",
    "repair-apply",
    "repair-rollback",
})
_DEFAULT_PLAN_FILE = ".workspace-repair-plan.json"
_VALID_OPERATION_TYPES = frozenset({"queue-to-shipped", "queue-remove"})


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
    result = {"room": entry.room, "needs": entry.needs}
    for key in ("slug", "path", "kind", "entry_type", "source", "summary"):
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
    `repair-apply` keep pre-Wave-6 behaviour, which means both an empty cooled
    set and no cooling findings; returning them separately let a caller
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
    """Return canonical and legacy work paths for a confined selector."""
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
    """Explain one canonical or accepted legacy work entry without path I/O."""
    normalized_selector = selector
    if selector.endswith("/"):
        directory_parts = selector[:-1].split("/")
        if len(directory_parts) == 3 and directory_parts[:2] == ["docs", "specs"]:
            normalized_selector = selector[:-1]
    targets = _explain_selector_targets(normalized_selector)
    public_selector = _public_canonical_path(normalized_selector)
    if targets is None:
        return public_selector, {"selector_status": "not_found"}

    canonical_path, legacy_path = targets
    projection = _canonical_projection(root, result, *_cooling_selection(result, "explain"))
    candidates = [
        item
        for item in [
            *projection["evaluations"],
            *projection["legacy_memberships"],
        ]
        if item["kind"] == "spec"
        and str(item["collection"]).startswith("work.")
        and item["path"] in {canonical_path, legacy_path}
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
        return public_selector, {
            "selector_status": "not_found",
            "findings": [{
                "code": "unregistered_work",
                "path": canonical_path,
                "dispatchable": False,
                "next_action": (
                    "Register or reconcile the canonical entry explicitly."
                ),
            }],
        }
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
    projection names a different, real file. Wave 5 admits any non-control
    character up to 1000 bytes, so this case is reachable.
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
                record.post_closeout_result != "Retired"
                and result.cooling_module.is_due(record, result.now).due
            )
        except Exception:
            # Degrading to "not due" silently under-reported the maintainer's
            # queue while `cooling_context_visible` still claimed a clean run.
            # The finding both names the record and flips that claim.
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
        # also admit ("retain-exception", "Retired") — a settled record AC28
        # requires to contribute nothing. `ExternalAdvisory` is the other live
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


def _closeout_projection(result, *, dueness_failed: bool = False) -> dict | None:
    """Project the first active or paused initiative's closeout facts, by slug.

    Returns None when no initiative is active or paused. There is no closeout
    state to project then, and synthesizing one from the absent initiative
    reported `unshipped-specs` against a workspace whose initiatives are all
    closed — a blocker naming work that does not exist. The block is omitted
    rather than emitted empty, which leaves AC29's closed key set untouched.
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
    all_specs_shipped = not (initiative.work.queue or initiative.work.active)
    # `spec_path` is `entry.path` straight from workspace.toml with no charset
    # rule, and this string is rendered into agent context. Every sibling
    # emitter bounds its path through this same filter.
    blockers = [
        f"type{finding.finding_type}:{_public_canonical_path(finding.spec_path)}"
        for finding in result.reconciliation
        if finding.ini_slug == initiative.slug and finding.finding_type in {2, 3}
    ]
    projection = project_closeout_status(
        paused=paused,
        all_specs_shipped=all_specs_shipped,
        closeout_blockers=blockers,
        # A record whose dueness could not be judged is an incomplete run just
        # as a record that would not load is, so it flips the same claim.
        cooling_context_visible=bool(result.cooling_findings) or dueness_failed,
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
    active_shaping_entries: list[dict] = []
    for ini in result.initiatives:
        if ini.status != "active":
            continue
        initiatives_out.append({
            "slug": _public_ini_slug(ini.slug),
            "name": "workspace.toml",
            "status": ini.status if ini.status in {"active", "paused", "closed"} else "invalid",
            "milestone": "workspace.toml",
            "brief_queue": _brief_queue_dict(ini.brief_queue),
            "queue_empty": len(ini.work.queue) == 0,
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
        cooling = _cooling_projection(result)
        unreadable = cooling.pop("_unreadable")
        output["cooling"] = cooling
        closeout = _closeout_projection(result, dueness_failed=bool(unreadable))
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


def _build_repair_plan_json(root: Path, result, plan) -> dict:
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

    # Only write when at least one operation succeeded
    if applied == 0:
        return applied, per_op, None

    serialized = tomlkit.dumps(doc)
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
    finally:
        if tmp_path is not None:
            with contextlib.suppress(OSError):
                Path(tmp_path).unlink()

    return applied, per_op, written_bytes


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
        directory_fd = os.open(
            path.parent,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
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
    restored_canonical = run_canonical_reconciliation(parsed)
    restored_matches = [
        membership
        for membership in restored_canonical.legacy_memberships
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
            data = _build_repair_plan_json(root, result, plan)
            # Emit stdout first — plan JSON always available even if file write fails
            _emit(data)
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
                try:
                    applied, per_op, written_bytes = _apply_operations(
                        root, ops, workspace_bytes, workspace_write_target
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
            public_selector, explain_result = _canonical_explain(root, result, args.item)
            data = _build_explain_json(root, result, public_selector, explain_result)
        elif subcommand == "status":
            result = analyze_bounded(root)
            data = _build_json(root, result, "status")
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
        _emit(_canonical_failure_payload(subcommand, code))
        return 2


if __name__ == "__main__":
    sys.exit(main())
