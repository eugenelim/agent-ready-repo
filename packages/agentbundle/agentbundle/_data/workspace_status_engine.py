#!/usr/bin/env python3
"""workspace-status production backend — stdlib-only, read-only.

Entry points:
  analyze(root: Path) -> WorkspaceStatusResult          — full analysis (Type 1+2+3)
  analyze_bounded(root: Path) -> WorkspaceStatusResult  — bounded analysis (Type 2+3 only)
  explain_item(result, selector: str) -> dict           — focused projection from bounded result
  compute_type2_cleanup(ini_slug, source_list, spec_path, spec_status) -> dict
                                              — non-authoritative repair descriptor
  compute_repair_plan(result, workspace_path: Path) -> RepairPlan
                                             — deterministic repair plan

This engine is the canonical implementation invoked by the workspace-status skill
via scripts/workspace_status.py. It reads workspace.toml and docs/specs/** to
produce DAG resolution, reconciliation, and cleanup-planning results.

Known gaps (preserved from Phase 0 characterization):
  KD-01: `backlog:<slug>` prefix absent from SKILL.md table
  KD-02: No cycle detection
  KD-03: Missing dep targets not warned
  KD-04: No quick mode (reconciliation always runs)
  KD-05: work.active/shipped duplicate spec.md Status
  KD-06: shape: resolved against .active only; wording inconsistency in SKILL.md/schema
  KD-07: brief:<path> needs underspecified; brief_queue structure varies
  KD-08: strategy:<slug> needs prefix absent from SKILL.md; treated conservatively
  KD-09: research:<slug> checks only backlog; item in .active (in-progress) erroneously
         reports satisfied — research findings should be committed before unblocking dependents
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import importlib
import importlib.util
import json
import math
import os
import re
import sys
import time
import tomllib
from pathlib import Path
from typing import Any

# ── Data types ────────────────────────────────────────────────────────────────

WORKSPACE_ENTRY_CONTRACT_VERSION = "workspace-entry.v1"
WORKSPACE_ENTRY_REQUIRED_FIELDS = ("path", "kind", "source", "summary", "needs")
WORKSPACE_ARTIFACT_KINDS = ("intent", "research", "design", "brief", "spec", "defect")
NORMALIZED_INTAKE_CONTRACT_VERSION = "normalized-intake.v1"
NORMALIZED_INTAKE_ACTIONS = ("start", "remember", "refresh")
SOURCE_MODES = ("repo-origin", "tracker-origin")

_WORKSPACE_ENTRY_FIELDS = frozenset(WORKSPACE_ENTRY_REQUIRED_FIELDS)
_SOURCE_FIELDS = frozenset(
    {"mode", "ref", "revision", "parent", "coordination", "tracker_profile"}
)
_LOCAL_NEED_FIELDS = frozenset({"type", "kind", "path"})
_CROSS_REPO_NEED_FIELDS = frozenset(
    {"type", "kind", "path", "containing_brief", "receipt_id", "accepted_revision"}
)
_FINDING_NEXT_ACTIONS = {
    "invalid_workspace": "Correct workspace.toml, then rerun reconciliation.",
    "invalid_entry": "Rewrite the entry to the accepted target contract.",
    "legacy_entry": "Materialize and register a canonical target entry.",
    "unsupported_legacy": "Route the item manually; do not infer a target entry.",
    "invalid_artifact_path": "Replace it with a confined canonical repository-relative path.",
    "missing_artifact": "Create and review the canonical artifact before dispatch.",
    "unreadable_artifact": "Restore readable repository state, then rerun reconciliation.",
    "missing_plan": "Create and approve the plan before dispatch.",
    "unapproved_spec": "Complete the spec approval gate.",
    "unregistered_work": "Register or reconcile the canonical entry explicitly.",
    "duplicate_membership": (
        "Remove the duplicate after choosing the authoritative membership."
    ),
    "impossible_transition": (
        "Correct the artifact or membership through a reviewed transition."
    ),
    "provenance_mismatch": (
        "Resolve provenance in the canonical artifact and mirror it deliberately."
    ),
    "refresh_conflict": "Resolve the conflict through the artifact's authority workflow.",
    "unsatisfied_dependency": "Complete or explicitly revise the dependency.",
    "missing_dependency": "Materialize or correct the dependency target.",
    "dependency_cycle": "Break the cycle through an explicit plan change.",
    "invalid_receipt": (
        "Replace it with a reviewed receipt matching the pinned dependency."
    ),
    "inactive_initiative": (
        "Reactivate the initiative explicitly or move the work through governance."
    ),
    "configuration_mismatch": (
        "Install or select a consistent versioned configuration, then rerun."
    ),
    "invalid_source_authority": (
        "Correct the closed source-authority block, then rerun reconciliation."
    ),
    "source_authority_migration_required": (
        "Add the reviewed source-authority block before using refresh."
    ),
}


@dataclasses.dataclass(frozen=True)
class RoutingFinding:
    """Stable refusal emitted while parsing or evaluating workspace state."""

    code: str
    path: str
    detail: str
    next_action: str
    dispatchable: bool = False


@dataclasses.dataclass(frozen=True)
class SourceRecord:
    """Validated source provenance shared by intake and workspace entries."""

    mode: str
    ref: str | None = None
    revision: str | None = None
    parent: str | None = None
    coordination: str | None = None
    tracker_profile: dict[str, str] | None = None
    locator: str | None = None
    object_type: str | None = None


@dataclasses.dataclass(frozen=True)
class Dependency:
    """Validated local or cross-repository hard dependency."""

    type: str
    kind: str
    path: str
    containing_brief: str | None = None
    receipt_id: str | None = None
    accepted_revision: str | None = None


@dataclasses.dataclass(frozen=True)
class WorkspaceEntry:
    """Validated target workspace entry; eligibility is evaluated separately."""

    path: str
    kind: str
    source: SourceRecord
    summary: str
    needs: list[Dependency]

    @property
    def slug(self) -> str:
        if self.path.startswith("docs/specs/") and self.path.endswith("/spec.md"):
            return self.path[len("docs/specs/"):-len("/spec.md")]
        return self.path.removeprefix("spec/")


@dataclasses.dataclass(frozen=True)
class LegacyWorkspaceEntry:
    """Accepted or rejected compatibility record that never dispatches."""

    collection: str
    raw: object
    path: str
    kind: str
    summary: str
    needs: list[str]
    finding: RoutingFinding

    @property
    def slug(self) -> str:
        return self.path.removeprefix("spec/")

    @property
    def dispatchable(self) -> bool:
        return False


@dataclasses.dataclass(frozen=True)
class NormalizedIntake:
    """Validated transient intake envelope."""

    contract_version: str
    action: str
    content: dict[str, list[str]]
    source: SourceRecord
    constraints: dict[str, object]
    proposed_authority: str
    refresh_target: str | None = None


@dataclasses.dataclass(frozen=True)
class WorkspaceMembership:
    """One parsed target entry at a specific lifecycle collection."""

    entry: WorkspaceEntry
    ini_slug: str
    collection: str
    initiative_status: str


@dataclasses.dataclass(frozen=True)
class LegacyWorkspaceMembership:
    """One compatibility entry retained for reader-first projections."""

    entry: LegacyWorkspaceEntry
    ini_slug: str
    collection: str
    initiative_status: str


@dataclasses.dataclass(frozen=True)
class ArtifactMetadata:
    """Artifact metadata needed for T2 reconciliation."""

    path: str
    kind: str
    status: str | None
    exists: bool
    readable: bool = True
    invalid_path: bool = False
    plan_invalid_path: bool = False
    plan_readable: bool = True
    plan_exists: bool | None = None
    parent: str | None = None
    ref: str | None = None
    revision: str | None = None
    refresh_conflict: bool = False
    resolution: str | None = None
    authority_status: dict[str, object] | None = None
    authority_error: str | None = None


@dataclasses.dataclass(frozen=True)
class DispatchEvaluation:
    """Positive dispatch predicate result for one parsed membership."""

    entry: WorkspaceEntry
    ini_slug: str
    collection: str
    dispatchable: bool
    findings: list[RoutingFinding]
    authority_status: dict[str, object] | None


@dataclasses.dataclass(frozen=True)
class CanonicalWorkspaceResult:
    """Canonical T2 reconciliation result before CLI/MCP projection."""

    memberships: list[WorkspaceMembership]
    legacy_memberships: list[LegacyWorkspaceMembership]
    findings: list[RoutingFinding]
    evaluations: list[DispatchEvaluation]
    dispatch_by_path: dict[str, DispatchEvaluation]


@dataclasses.dataclass
class WorkEntry:
    path: str    # e.g. "spec/m1-workspace-core"
    slug: str    # path with "spec/" stripped
    needs: list[str]


@dataclasses.dataclass
class ShapingEntry:
    slug: str
    entry_type: str   # shape | research | strategy | signal | design
    needs: list[str]


@dataclasses.dataclass
class RepoBacklogEntry:
    """Display-only projection of one repository-level backlog entry."""
    room: str
    needs: list[str | dict[str, object]]
    slug: str | None = None
    path: str | None = None
    kind: str | None = None
    entry_type: str | None = None
    source: str | dict[str, object] | None = None
    summary: str | None = None


@dataclasses.dataclass
class BriefQueue:
    executing: str
    ready: list[str]
    draft: list[str]


@dataclasses.dataclass
class InitiativeWork:
    active: list[WorkEntry]
    shipped: list[WorkEntry]
    queue: list[WorkEntry]


@dataclasses.dataclass
class InitiativeShaping:
    active: list[ShapingEntry]
    backlog: list[ShapingEntry]


@dataclasses.dataclass
class Initiative:
    slug: str
    name: str
    status: str      # active | paused | closed | complete
    milestone: str
    work: InitiativeWork
    shaping: InitiativeShaping
    brief_queue: BriefQueue | None


@dataclasses.dataclass
class EntryClassification:
    entry: WorkEntry
    ini_slug: str
    is_ready: bool
    blocking_needs: list[str]   # unsatisfied needs (empty when is_ready)


@dataclasses.dataclass
class ShapingClassification:
    entry: ShapingEntry
    ini_slug: str
    is_signal: bool      # True for entry_type == "signal" (active context, not actionable)
    is_ready: bool       # True when needs satisfied; always False for signals
    blocking_needs: list[str]


@dataclasses.dataclass
class ReconciliationFinding:
    finding_type: int   # 1, 2, or 3
    spec_path: str
    spec_status: str
    ini_slug: str
    list_name: str      # "queue" | "active" | "shipped" | ""


@dataclasses.dataclass
class WorkLoopStaleWarning:
    """A warn-only stale-queue finding emitted by work-loop Step 0.

    Distinct from workspace-status Type 2 reconciliation:
      - Only active initiatives are checked
      - Only Shipped status triggers a warning (Archived/Approved/Implementing do not)
      - When a path is in both queue and active, ONE warning names both lists
      - No cleanup offer; work-loop only warns
    """
    spec_path: str
    ini_slug: str
    source_lists: list[str]  # ["queue"], ["active"], or ["queue", "active"]


@dataclasses.dataclass
class RepairOperation:
    """A single automatically applicable repair operation derived from a Type 2 queue finding."""
    operation_type: str          # "queue-to-shipped" | "queue-remove"
    spec_path: str
    spec_status: str             # "Shipped" | "Archived"
    ini_slug: str
    finding_id: str              # stable string ID: "type2:<ini_slug>:queue:<spec_path>"
    operation_id: str            # SHA-256 of canonical operation content (excludes operation_id)
    spec_status_fingerprint: str  # SHA-256 of raw status-field line from spec.md at plan time


@dataclasses.dataclass
class ManualFinding:
    """A finding that requires human decision; not automatically repairable."""
    finding_type: int
    spec_path: str
    spec_status: str
    ini_slug: str
    list_name: str
    reason: str
    finding_id: str  # stable string ID: "type<N>:<ini_slug>:<list_name>:<spec_path>"


@dataclasses.dataclass
class RepairPlan:
    """Output of compute_repair_plan — a deterministic, read-only repair plan."""
    automatic_operations: list[RepairOperation]
    manual_findings: list[ManualFinding]
    workspace_fingerprint: str  # SHA-256 hexdigest of workspace.toml bytes at plan time
    plan_id: str                # SHA-256 of canonical plan content (excludes plan_id)


@dataclasses.dataclass
class WorkspaceStatusResult:
    initiatives: list[Initiative]
    classifications: list[EntryClassification]        # work queue entries (ready + blocked)
    shaping_classifications: list[ShapingClassification]  # shaping queue entries
    reconciliation: list[ReconciliationFinding]
    elapsed_s: float  # wall-clock seconds for analyze()
    # [backlog].open typed shaping entries (workspace-level, not per-initiative).
    # Populated by extract_top_level_backlog(); work-loop's shaping-item guard reads these.
    top_level_backlog: list[ShapingEntry] = dataclasses.field(default_factory=list)
    # Complete [backlog].open display projection. It is not passed to classifiers.
    repo_backlog: list[RepoBacklogEntry] = dataclasses.field(default_factory=list)
    global_scan_performed: bool = dataclasses.field(default=False)
    declared_spec_files_read: int = dataclasses.field(default=0)
    global_scan_files_read: int = dataclasses.field(default=0)

    @property
    def files_read(self) -> int:
        return self.declared_spec_files_read + self.global_scan_files_read

    @property
    def ready(self) -> list[EntryClassification]:
        return [c for c in self.classifications if c.is_ready]

    @property
    def blocked(self) -> list[EntryClassification]:
        return [c for c in self.classifications if not c.is_ready]

    @property
    def ready_shaping(self) -> list[ShapingClassification]:
        return [c for c in self.shaping_classifications if c.is_ready]

    @property
    def signals(self) -> list[ShapingClassification]:
        return [c for c in self.shaping_classifications if c.is_signal]

    @property
    def blocked_shaping(self) -> list[ShapingClassification]:
        return [
            c for c in self.shaping_classifications
            if not c.is_ready and not c.is_signal
        ]

    @property
    def type1(self) -> list[ReconciliationFinding]:
        return [f for f in self.reconciliation if f.finding_type == 1]

    @property
    def type2(self) -> list[ReconciliationFinding]:
        return [f for f in self.reconciliation if f.finding_type == 2]

    @property
    def type3(self) -> list[ReconciliationFinding]:
        return [f for f in self.reconciliation if f.finding_type == 3]


# ── Group 2 contract parsing ──────────────────────────────────────────────────

_CONSTRAINT_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_SENSITIVE_CONSTRAINT_RE = re.compile(
    r"(?:^|_)(?:raw|payload|prompt|instruction|credential|credentials|secret|secrets|"
    r"password|passwords|passwd|pwd|(?:api|access|private)?_?(?:token|tokens|key|keys))"
    r"(?:_|$)"
)


def _finding(code: str, path: str = "", detail: str = "") -> RoutingFinding:
    return RoutingFinding(
        code=code,
        path=path,
        detail=detail,
        next_action=_FINDING_NEXT_ACTIONS[code],
    )


def _is_bounded_text(value: object, max_length: int) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= max_length


def _is_safe_locator(value: object) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 1000 and not any(
        marker in value for marker in ("@", "?", "#")
    )


def _is_repository_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not 1 <= len(value) <= 1000:
        return False
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return False
    if "\\" in value:
        return False
    parts = value.split("/")
    return not (".." in parts or "." in parts or "" in parts)


_SINGLE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,199}$")


def _is_canonical_spec_artifact_path(path: object) -> bool:
    if not isinstance(path, str) or not _is_repository_relative_path(path):
        return False
    parts = path.split("/")
    return (
        len(parts) == 4
        and parts[:2] == ["docs", "specs"]
        and _SINGLE_SEGMENT_RE.fullmatch(parts[2]) is not None
        and parts[3] == "spec.md"
    )


def _is_canonical_local_brief_path(path: object) -> bool:
    if not isinstance(path, str) or not _is_repository_relative_path(path):
        return False
    parts = path.split("/")
    return (
        len(parts) == 4
        and parts[:3] == ["docs", "product", "briefs"]
        and _SINGLE_SEGMENT_RE.fullmatch(parts[3].removesuffix(".md")) is not None
        and parts[3].endswith(".md")
    )


def _path_finding_or_invalid(path: object, detail: str) -> RoutingFinding:
    code = "invalid_artifact_path" if not _is_repository_relative_path(path) else "invalid_entry"
    return _finding(code, str(path or ""), detail)


def _validate_tracker_profile(raw: object) -> dict[str, str] | None:
    if not isinstance(raw, dict):
        return None
    if set(raw) != {"id", "version"}:
        return None
    if not _is_bounded_text(raw.get("id"), 200):
        return None
    if not _is_bounded_text(raw.get("version"), 100):
        return None
    return {"id": raw["id"], "version": raw["version"]}


def _parse_source_record(raw: object) -> tuple[SourceRecord | None, list[RoutingFinding]]:
    if not isinstance(raw, dict):
        return None, [_finding("invalid_entry", detail="source must be an object")]
    if not set(raw).issubset(_SOURCE_FIELDS):
        return None, [_finding("invalid_entry", detail="source has unknown fields")]
    mode = raw.get("mode")
    if mode not in SOURCE_MODES:
        return None, [_finding("invalid_entry", detail="source.mode is not accepted")]
    ref = raw.get("ref")
    revision = raw.get("revision")
    parent = raw.get("parent")
    coordination = raw.get("coordination")
    tracker_profile = raw.get("tracker_profile")
    if ref is not None and not _is_safe_locator(ref):
        return None, [_finding("invalid_entry", detail="source.ref is not a safe locator")]
    if revision is not None and not _is_bounded_text(revision, 200):
        return None, [_finding("invalid_entry", detail="source.revision is invalid")]
    if parent is not None and not _is_repository_relative_path(parent):
        return None, [_path_finding_or_invalid(parent, "source.parent is not a safe path")]
    if coordination is not None and not _is_bounded_text(coordination, 300):
        return None, [_finding("invalid_entry", detail="source.coordination is invalid")]
    parsed_profile = None
    if tracker_profile is not None:
        parsed_profile = _validate_tracker_profile(tracker_profile)
        if parsed_profile is None:
            return None, [_finding("invalid_entry", detail="tracker_profile is invalid")]
    if mode == "tracker-origin" and (ref is None or revision is None):
        return None, [_finding("invalid_entry", detail="tracker-origin requires ref and revision")]
    return SourceRecord(
        mode=mode,
        ref=ref,
        revision=revision,
        parent=parent,
        coordination=coordination,
        tracker_profile=parsed_profile,
    ), []


def _parse_dependency(raw: object) -> tuple[Dependency | None, list[RoutingFinding]]:
    if not isinstance(raw, dict):
        return None, [_finding("invalid_entry", detail="need must be an object")]
    dep_type = raw.get("type")
    if dep_type == "local":
        if set(raw) != _LOCAL_NEED_FIELDS:
            return None, [_finding("invalid_entry", detail="local need fields are invalid")]
        kind = raw.get("kind")
        path = raw.get("path")
        if kind not in WORKSPACE_ARTIFACT_KINDS:
            return None, [_finding("invalid_entry", detail="local need kind is invalid")]
        if not _is_repository_relative_path(path):
            return None, [_path_finding_or_invalid(path, "local need path is unsafe")]
        if kind == "spec" and not _is_canonical_spec_artifact_path(path):
            return None, [_finding("invalid_artifact_path", str(path), "spec need path")]
        if kind == "brief" and not _is_canonical_local_brief_path(path):
            return None, [_finding("invalid_artifact_path", str(path), "brief need path")]
        return Dependency(type="local", kind=kind, path=path), []
    if dep_type == "cross-repo":
        if set(raw) != _CROSS_REPO_NEED_FIELDS:
            return None, [_finding("invalid_entry", detail="cross-repo need fields are invalid")]
        kind = raw.get("kind")
        path = raw.get("path")
        containing_brief = raw.get("containing_brief")
        receipt_id = raw.get("receipt_id")
        accepted_revision = raw.get("accepted_revision")
        if kind not in ("brief", "spec"):
            return None, [_finding("invalid_entry", detail="cross-repo need kind is invalid")]
        for label, candidate in (
            ("path", path),
            ("containing_brief", containing_brief),
        ):
            if not _is_repository_relative_path(candidate):
                return None, [_path_finding_or_invalid(candidate, f"{label} is unsafe")]
            if not _is_canonical_local_brief_path(candidate):
                return None, [
                    _finding("invalid_artifact_path", str(candidate), f"{label} is not brief")
                ]
        if not _is_bounded_text(receipt_id, 200):
            return None, [_finding("invalid_entry", detail="receipt_id is invalid")]
        if not _is_bounded_text(accepted_revision, 200):
            return None, [_finding("invalid_entry", detail="accepted_revision is invalid")]
        return Dependency(
            type="cross-repo",
            kind=kind,
            path=path,
            containing_brief=containing_brief,
            receipt_id=receipt_id,
            accepted_revision=accepted_revision,
        ), []
    return None, [_finding("invalid_entry", detail="need type is invalid")]


def parse_workspace_entry(
    raw: object,
) -> tuple[WorkspaceEntry | None, list[RoutingFinding]]:
    """Parse one target workspace entry through the Group 2 contract."""
    if not isinstance(raw, dict):
        return None, [_finding("invalid_entry", detail="target entry must be an object")]
    keys = set(raw)
    if keys != _WORKSPACE_ENTRY_FIELDS:
        return None, [_finding("invalid_entry", detail="target entry fields are not exact")]
    path = raw.get("path")
    if not _is_repository_relative_path(path):
        return None, [_path_finding_or_invalid(path, "entry path is unsafe")]
    kind = raw.get("kind")
    if kind not in WORKSPACE_ARTIFACT_KINDS:
        return None, [_finding("invalid_entry", str(path), "entry kind is invalid")]
    if kind == "spec" and not _is_canonical_spec_artifact_path(path):
        return None, [_finding("invalid_artifact_path", str(path), "spec path is invalid")]
    if kind == "brief" and not _is_canonical_local_brief_path(path):
        return None, [_finding("invalid_artifact_path", str(path), "brief path is invalid")]
    source, source_findings = _parse_source_record(raw.get("source"))
    if source_findings:
        return None, source_findings
    summary = raw.get("summary")
    if not _is_bounded_text(summary, 500):
        return None, [_finding("invalid_entry", str(path), "summary is invalid")]
    raw_needs = raw.get("needs")
    if not isinstance(raw_needs, list) or len(raw_needs) > 50:
        return None, [_finding("invalid_entry", str(path), "needs must be an array")]
    needs: list[Dependency] = []
    for raw_need in raw_needs:
        need, need_findings = _parse_dependency(raw_need)
        if need_findings:
            return None, need_findings
        needs.append(need)
    return WorkspaceEntry(
        path=path,
        kind=kind,
        source=source,
        summary=summary,
        needs=needs,
    ), []


def _parse_intake_source(raw: object) -> tuple[SourceRecord | None, list[RoutingFinding]]:
    allowed = {"mode", "locator", "revision", "tracker_profile", "object_type"}
    if not isinstance(raw, dict):
        return None, [_finding("invalid_entry", detail="source must be an object")]
    if not set(raw).issubset(allowed):
        return None, [_finding("invalid_entry", detail="source has unknown fields")]
    mode = raw.get("mode")
    locator = raw.get("locator")
    revision = raw.get("revision")
    if mode not in SOURCE_MODES:
        return None, [_finding("invalid_entry", detail="source.mode is not accepted")]
    if not _is_safe_locator(locator):
        return None, [_finding("invalid_entry", detail="source.locator is not safe")]
    if not _is_bounded_text(revision, 200):
        return None, [_finding("invalid_entry", detail="source.revision is invalid")]
    parsed_profile = None
    if "tracker_profile" in raw:
        parsed_profile = _validate_tracker_profile(raw["tracker_profile"])
        if parsed_profile is None:
            return None, [_finding("invalid_entry", detail="tracker_profile is invalid")]
    object_type = raw.get("object_type")
    if object_type is not None and not _is_bounded_text(object_type, 120):
        return None, [_finding("invalid_entry", detail="object_type is invalid")]
    return SourceRecord(
        mode=mode,
        revision=revision,
        tracker_profile=parsed_profile,
        locator=locator,
        object_type=object_type,
    ), []


def _validate_intake_content(raw: object) -> dict[str, list[str]] | None:
    required = {"outcomes", "constraints", "evidence", "behaviors", "assumptions", "named_gaps"}
    if not isinstance(raw, dict) or set(raw) != required:
        return None
    parsed: dict[str, list[str]] = {}
    for key, value in raw.items():
        if not isinstance(value, list) or len(value) > 50:
            return None
        if not all(_is_bounded_text(item, 2000) for item in value):
            return None
        parsed[key] = list(value)
    return parsed


def _validate_intake_constraints(raw: object) -> dict[str, object] | None:
    if not isinstance(raw, dict) or len(raw) > 40:
        return None
    for key, value in raw.items():
        if not _CONSTRAINT_NAME_RE.fullmatch(key):
            return None
        if _SENSITIVE_CONSTRAINT_RE.search(key):
            return None
        values = value if isinstance(value, list) else [value]
        if isinstance(value, list) and len(value) > 20:
            return None
        for item in values:
            if isinstance(item, str):
                if len(item) > 1000:
                    return None
            elif item is not None:
                if not isinstance(item, (int, float, bool)):
                    return None
                if isinstance(item, float) and not math.isfinite(item):
                    return None
    return dict(raw)


def validate_normalized_intake(
    raw: object,
) -> tuple[NormalizedIntake | None, list[RoutingFinding]]:
    """Validate one normalized-intake envelope through the Group 2 contract."""
    required = {
        "contract_version",
        "action",
        "content",
        "source",
        "constraints",
        "proposed_authority",
    }
    allowed = required | {"refresh_target"}
    if not isinstance(raw, dict):
        return None, [_finding("invalid_entry", detail="normalized intake must be an object")]
    if set(raw) - allowed or not required.issubset(raw):
        return None, [_finding("invalid_entry", detail="normalized intake fields are invalid")]
    if raw.get("contract_version") != NORMALIZED_INTAKE_CONTRACT_VERSION:
        return None, [_finding("invalid_entry", detail="contract_version is invalid")]
    action = raw.get("action")
    if action not in NORMALIZED_INTAKE_ACTIONS:
        return None, [_finding("invalid_entry", detail="action is invalid")]
    has_refresh_target = "refresh_target" in raw
    if action == "refresh" and not has_refresh_target:
        return None, [_finding("invalid_entry", detail="refresh requires refresh_target")]
    if action != "refresh" and has_refresh_target:
        return None, [_finding("invalid_entry", detail="only refresh accepts refresh_target")]
    refresh_target = raw.get("refresh_target")
    if has_refresh_target and not _is_repository_relative_path(refresh_target):
        return None, [_path_finding_or_invalid(refresh_target, "refresh_target is unsafe")]
    content = _validate_intake_content(raw.get("content"))
    if content is None:
        return None, [_finding("invalid_entry", detail="content is invalid")]
    source, source_findings = _parse_intake_source(raw.get("source"))
    if source_findings:
        return None, source_findings
    constraints = _validate_intake_constraints(raw.get("constraints"))
    if constraints is None:
        return None, [_finding("invalid_entry", detail="constraints are invalid")]
    authority = raw.get("proposed_authority")
    if authority not in SOURCE_MODES:
        return None, [_finding("invalid_entry", detail="proposed_authority is invalid")]
    return NormalizedIntake(
        contract_version=NORMALIZED_INTAKE_CONTRACT_VERSION,
        action=action,
        content=content,
        source=source,
        constraints=constraints,
        proposed_authority=authority,
        refresh_target=refresh_target,
    ), []


# ── TOML parsing helpers ──────────────────────────────────────────────────────

def _parse_needs(raw) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [
            item if isinstance(item, str) else "unsupported-typed-need"
            for item in raw
        ]
    return ["unsupported-typed-need"]


def _parse_work_entry(raw) -> WorkEntry:
    if isinstance(raw, str):
        path = raw
        needs: list[str] = []
    elif isinstance(raw, dict):
        path = raw.get("path", "")   # work inline objects use `path`; `slug` is shaping-only
        needs = _parse_needs(raw.get("needs"))
    else:
        path = ""
        needs = ["unsupported-work-entry"]
    slug = _spec_slug_from_workspace_path(path)
    return WorkEntry(path=path, slug=slug, needs=needs)


def _parse_shaping_entry(raw) -> ShapingEntry:
    if isinstance(raw, str):
        return ShapingEntry(slug=raw, entry_type="shape", needs=[])
    return ShapingEntry(
        slug=raw.get("slug", ""),
        entry_type=raw.get("type", "shape"),
        needs=_parse_needs(raw.get("needs")),
    )


def _parse_supported_shaping_entry(
    collection: str, raw: object
) -> ShapingEntry | None:
    legacy = parse_legacy_workspace_entry(collection, raw)
    if legacy.finding.code != "legacy_entry":
        return None
    return ShapingEntry(
        slug=legacy.slug,
        entry_type=legacy.kind,
        needs=list(legacy.needs),
    )


def _parse_supported_shaping_entries(
    collection: str, raw_entries: object
) -> list[ShapingEntry]:
    if not isinstance(raw_entries, list):
        return []
    entries: list[ShapingEntry] = []
    for raw in raw_entries:
        entry = _parse_supported_shaping_entry(collection, raw)
        if entry is not None:
            entries.append(entry)
    return entries


def parse_workspace(path: Path) -> dict:
    """Parse workspace.toml; return raw TOML dict. Raises on parse error."""
    with Path(path).open("rb") as f:
        return tomllib.load(f)


def _is_legacy_slug(value: object) -> bool:
    return isinstance(value, str) and _SINGLE_SEGMENT_RE.fullmatch(value) is not None


def _is_legacy_spec_path(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parts = value.split("/")
    return len(parts) == 2 and parts[0] == "spec" and _is_legacy_slug(parts[1])


def _legacy_path_finding(collection: str, raw: object) -> LegacyWorkspaceEntry:
    path = raw if isinstance(raw, str) else ""
    if isinstance(raw, dict) and isinstance(raw.get("path"), str):
        path = raw["path"]
    code = "unsupported_legacy"
    if path:
        path_like = (
            "/" in path
            or "\\" in path
            or path in {".", ".."}
            or re.match(r"^[A-Za-z]:", path) is not None
        )
        if path_like and not _is_repository_relative_path(path):
            code = "invalid_artifact_path"
    return LegacyWorkspaceEntry(
        collection=collection,
        raw=raw,
        path=path,
        kind="",
        summary="",
        needs=[],
        finding=_finding(code, str(path), "unsupported legacy shape"),
    )


def _accepted_legacy_entry(collection: str, raw: object) -> LegacyWorkspaceEntry | None:
    work_collections = {"work.queue", "work.active", "work.shipped"}
    shaping_collections = {"shaping_queue.active", "shaping_queue.backlog"}
    brief_collections = {
        "brief_queue.draft",
        "brief_queue.ready",
        "brief_queue.executing",
        "brief_queue.shipped",
    }
    if (
        collection in work_collections
        and isinstance(raw, str)
        and _is_legacy_spec_path(raw)
    ):
        return LegacyWorkspaceEntry(
            collection=collection,
            raw=raw,
            path=raw,
            kind="spec",
            summary="",
            needs=[],
            finding=_finding("legacy_entry", raw, "legacy work queue string"),
        )
    if collection in shaping_collections:
        if isinstance(raw, str) and _is_legacy_slug(raw):
            return LegacyWorkspaceEntry(
                collection=collection,
                raw=raw,
                path=raw,
                kind="shape",
                summary="",
                needs=[],
                finding=_finding("legacy_entry", raw, "legacy shaping string"),
            )
        if (
            isinstance(raw, dict)
            and "slug" in raw
            and set(raw).issubset({"slug", "type", "needs"})
        ):
            entry_type = raw.get("type", "shape")
            raw_needs = raw.get("needs")
            needs_are_supported = (
                raw_needs is None
                or isinstance(raw_needs, str)
                or (
                    isinstance(raw_needs, list)
                    and all(isinstance(need, str) for need in raw_needs)
                )
            )
            if (
                _is_legacy_slug(raw.get("slug"))
                and entry_type in _SHAPING_TYPES
                and needs_are_supported
            ):
                return LegacyWorkspaceEntry(
                    collection=collection,
                    raw=raw,
                    path=raw["slug"],
                    kind=entry_type,
                    summary="",
                    needs=_parse_needs(raw_needs),
                    finding=_finding("legacy_entry", raw["slug"], "legacy shaping object"),
                )
    if (
        collection == "backlog.open"
        and isinstance(raw, dict)
        and {"slug", "type"}.issubset(raw)
        and set(raw).issubset({"slug", "type", "needs", "source", "summary"})
    ):
        raw_needs = raw.get("needs")
        needs_are_supported = (
            raw_needs is None
            or isinstance(raw_needs, str)
            or (
                isinstance(raw_needs, list)
                and all(isinstance(need, str) for need in raw_needs)
            )
        )
        source_is_supported = "source" not in raw or isinstance(raw["source"], str)
        summary_is_supported = "summary" not in raw or isinstance(raw["summary"], str)
        if (
            _is_legacy_slug(raw.get("slug"))
            and raw.get("type") in _SHAPING_TYPES
            and needs_are_supported
            and source_is_supported
            and summary_is_supported
        ):
            return LegacyWorkspaceEntry(
                collection=collection,
                raw=raw,
                path=raw["slug"],
                kind=raw["type"],
                summary=raw.get("summary", ""),
                needs=_parse_needs(raw_needs),
                finding=_finding(
                    "legacy_entry", raw["slug"], "legacy top-level shaping object"
                ),
            )
    if (
        collection in brief_collections
        and isinstance(raw, str)
        and _is_canonical_local_brief_path(raw)
    ):
        return LegacyWorkspaceEntry(
            collection=collection,
            raw=raw,
            path=raw,
            kind="brief",
            summary="",
            needs=[],
            finding=_finding("legacy_entry", raw, "legacy brief queue string"),
        )
    if (
        collection == "backlog.open"
        and isinstance(raw, dict)
        and set(raw) == {"slug", "source", "summary", "needs", "type"}
    ):
        needs = raw.get("needs", [])
        if (
            _is_legacy_slug(raw.get("slug"))
            and isinstance(raw.get("source"), str)
            and isinstance(raw.get("summary"), str)
            and raw.get("type") == "spec"
            and isinstance(needs, list)
            and all(isinstance(need, str) for need in needs)
        ):
            return LegacyWorkspaceEntry(
                collection=collection,
                raw=raw,
                path=raw["slug"],
                kind="spec",
                summary=raw["summary"],
                needs=list(needs),
                finding=_finding("legacy_entry", raw["slug"], "legacy backlog object"),
            )
    return None


def parse_legacy_workspace_entry(collection: str, raw: object) -> LegacyWorkspaceEntry:
    """Return an explicit, non-dispatchable compatibility record."""

    accepted = _accepted_legacy_entry(collection, raw)
    if accepted is not None:
        return accepted
    return _legacy_path_finding(collection, raw)


def _is_target_like_entry(raw: object) -> bool:
    if not isinstance(raw, dict) or "path" not in raw:
        return False
    keys = set(raw)
    if keys.issubset(_WORKSPACE_ENTRY_FIELDS):
        path = raw.get("path")
        return bool(keys & {"kind", "source", "summary"}) or (
            isinstance(path, str) and path.startswith("docs/")
        )
    return {"kind", "source", "summary", "needs"}.issubset(keys)


def _target_like_blocked_path(raw: object) -> str | None:
    if not _is_target_like_entry(raw) or not isinstance(raw, dict):
        return None
    path = raw.get("path")
    if not _is_repository_relative_path(path):
        return None
    return path


def parse_legacy_fixture_file(path: Path) -> list[LegacyWorkspaceEntry]:
    """Parse every array entry in a Group 2 legacy fixture."""

    raw = parse_workspace(path)
    results: list[LegacyWorkspaceEntry] = []
    stack = [raw]
    while stack:
        section = stack.pop()
        for collection, entries in section.items():
            if isinstance(entries, list):
                for entry in entries:
                    results.append(parse_legacy_workspace_entry(collection, entry))
            elif isinstance(entries, dict):
                stack.append(entries)
    return results


# ── Canonical T2 reconciliation ───────────────────────────────────────────────

_INITIATIVE_ENTRY_COLLECTIONS = {
    "work": ("queue", "active", "shipped"),
    "shaping_queue": ("backlog", "active"),
    "brief_queue": ("draft", "ready", "executing", "shipped"),
}
_TOP_LEVEL_ENTRY_COLLECTIONS = {"backlog": ("open", "closed")}
_ALLOWED_KIND_BY_COLLECTION = {
    "backlog.open": {"intent", "research", "design", "brief", "spec", "defect"},
    "backlog.closed": {"defect"},
    "shaping_queue.backlog": {"intent", "research", "design"},
    "shaping_queue.active": {"intent", "research", "design"},
    "brief_queue.draft": {"brief"},
    "brief_queue.ready": {"brief"},
    "brief_queue.executing": {"brief"},
    "brief_queue.shipped": {"brief"},
    "work.queue": {"spec"},
    "work.active": {"spec"},
    "work.shipped": {"spec"},
}
_TERMINAL_STATUS_BY_KIND = {
    "spec": {"Shipped"},
    "defect": {"fixed"},
    "brief": {"Ready", "Executing", "Shipped"},
    "intent": {"Accepted", "Fulfilled"},
    "research": {"Complete"},
    "design": {"Approved"},
}
_CANONICAL_INITIATIVE_RE = re.compile(r"^ini-\d{3}$")
ROUTING_CONFIGURATION_VERSION = "workspace-routing.v1"
_WORKSPACE_ENTRY_SCHEMA_DIGEST = (
    "21fb3a4ffb01afcae330d53d7c15f4f580b990cf4342d8a57088acc2d5a72db4"
)
_NORMALIZED_INTAKE_SCHEMA_DIGEST = (
    "7d753d44b4af64979953dc32b094f27e5186f9bf21944357cfd3eb06a47fe4f4"
)
_ADAPTER_CONTRACT_DIGEST = (
    "52794c24aedaa11897a50fd758eacee8ebee767886a27d22795d24ae0efc4016"
)


def _canonical_finding_payload(finding: RoutingFinding) -> dict[str, object]:
    return {
        "code": finding.code,
        "path": finding.path,
        "dispatchable": finding.dispatchable,
        "next_action": finding.next_action,
    }


def canonical_result_snapshot(
    result: CanonicalWorkspaceResult,
    *,
    schema_ids: tuple[str, ...] = (
        "contracts/jsonschema/normalized-intake.schema.json",
        "contracts/jsonschema/workspace-entry.schema.json",
    ),
    schema_content_digests: dict[str, str] | None = None,
    contract_versions: tuple[str, ...] = (
        NORMALIZED_INTAKE_CONTRACT_VERSION,
        WORKSPACE_ENTRY_CONTRACT_VERSION,
    ),
    workspace_digest: str = "",
    semantic_workspace_digest: str = "",
    artifact_fingerprints: dict[str, str] | None = None,
    artifact_status_fingerprints: dict[str, str] | None = None,
    artifact_provenance_fingerprints: dict[str, str] | None = None,
    adapter_contract_version: str = "adapter-contract.v1",
    tracker_profile: dict[str, str] | None = None,
    routing_configuration_version: str = ROUTING_CONFIGURATION_VERSION,
) -> dict[str, object]:
    """Return deterministic canonical routing content for identity comparisons."""
    schema_content_digests = schema_content_digests or {}
    artifact_fingerprints = artifact_fingerprints or {}
    artifact_status_fingerprints = artifact_status_fingerprints or artifact_fingerprints
    artifact_provenance_fingerprints = artifact_provenance_fingerprints or {}
    tracker_profile = tracker_profile or {}
    evaluations = [
        {
            "path": evaluation.entry.path,
            "kind": evaluation.entry.kind,
            "ini_slug": evaluation.ini_slug,
            "collection": evaluation.collection,
            "dispatchable": evaluation.dispatchable,
            "findings": sorted(
                (_canonical_finding_payload(f) for f in evaluation.findings),
                key=lambda item: (str(item["path"]), str(item["code"])),
            ),
        }
        for evaluation in result.evaluations
    ]
    legacy = [
        {
            "path": membership.entry.path,
            "kind": membership.entry.kind,
            "ini_slug": membership.ini_slug,
            "collection": membership.collection,
            "finding": _canonical_finding_payload(membership.entry.finding),
        }
        for membership in result.legacy_memberships
    ]
    findings = [_canonical_finding_payload(f) for f in result.findings]
    return {
        "schema_ids": sorted(schema_ids),
        "schema_content_digests": dict(sorted(schema_content_digests.items())),
        "contract_versions": sorted(contract_versions),
        "semantic_workspace_digest": semantic_workspace_digest or workspace_digest,
        "artifact_fingerprints": dict(sorted(artifact_fingerprints.items())),
        "artifact_status_fingerprints": dict(sorted(artifact_status_fingerprints.items())),
        "artifact_provenance_fingerprints": dict(
            sorted(artifact_provenance_fingerprints.items())
        ),
        "adapter_contract_version": adapter_contract_version,
        "tracker_profile": dict(sorted(tracker_profile.items())),
        "routing_configuration_version": routing_configuration_version,
        "evaluations": sorted(
            evaluations,
            key=lambda item: (
                str(item["path"]),
                str(item["ini_slug"]),
                str(item["collection"]),
            ),
        ),
        "legacy_memberships": sorted(
            legacy,
            key=lambda item: (
                str(item["path"]),
                str(item["ini_slug"]),
                str(item["collection"]),
            ),
        ),
        "findings": sorted(findings, key=lambda item: (str(item["path"]), str(item["code"]))),
    }


def canonical_result_identity(result: CanonicalWorkspaceResult, **kwargs) -> str:
    """Return a stable SHA-256 identity for canonical routing content."""
    payload = canonical_result_snapshot(result, **kwargs)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _repository_contract_digest(root: Path, relative_path: str, fallback: str) -> str:
    """Hash an in-repository contract, or use the projected contract digest."""
    candidate = _confined_artifact_path(root, relative_path)
    if candidate is None or not candidate.is_file():
        return fallback
    try:
        return hashlib.sha256(candidate.read_bytes()).hexdigest()
    except OSError:
        return fallback


def canonical_repository_identity(
    workspace: dict,
    result: CanonicalWorkspaceResult,
    root: Path,
) -> str:
    """Derive the routing identity from repository state used by reconciliation."""
    semantic_memberships: list[dict[str, object]] = []
    status_fingerprints: dict[str, str] = {}
    provenance_fingerprints: dict[str, str] = {}
    tracker_profiles: set[tuple[str, str]] = set()
    for membership in result.memberships:
        entry = membership.entry
        source = dataclasses.asdict(entry.source)
        needs = sorted(
            (dataclasses.asdict(need) for need in entry.needs),
            key=lambda need: json.dumps(need, sort_keys=True),
        )
        identity_key = (
            f"{membership.ini_slug}:{membership.collection}:{entry.path}"
        )
        semantic_memberships.append({
            "path": entry.path,
            "kind": entry.kind,
            "source": source,
            "needs": needs,
            "ini_slug": membership.ini_slug,
            "collection": membership.collection,
            "initiative_status": membership.initiative_status,
        })
        metadata = _metadata_from_root(root, entry)
        artifact = _confined_artifact_path(root, entry.path)
        status_fingerprint: str | None = None
        if entry.kind == "spec" and artifact is not None:
            _status, status_fingerprint = extract_spec_status_with_fingerprint(artifact)
        status_fingerprints[identity_key] = status_fingerprint or hashlib.sha256(
            json.dumps(metadata.status, ensure_ascii=True).encode("ascii")
        ).hexdigest()
        provenance_fingerprints[identity_key] = hashlib.sha256(
            json.dumps({
                "source": source,
                "artifact": {
                    "parent": metadata.parent,
                    "ref": metadata.ref,
                    "revision": metadata.revision,
                    "refresh_conflict": metadata.refresh_conflict,
                },
            }, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            .encode("ascii")
        ).hexdigest()
        profile = entry.source.tracker_profile
        if profile is not None:
            tracker_profiles.add((profile["id"], profile["version"]))

    semantic_legacy = [
        {
            "path": membership.entry.path,
            "kind": membership.entry.kind,
            "needs": sorted(membership.entry.needs),
            "ini_slug": membership.ini_slug,
            "collection": membership.collection,
            "initiative_status": membership.initiative_status,
        }
        for membership in result.legacy_memberships
    ]
    initiative_statuses = {
        key: section.get("status", "")
        for key, section in workspace.items()
        if isinstance(key, str)
        and _CANONICAL_INITIATIVE_RE.fullmatch(key)
        and isinstance(section, dict)
    }
    semantic_workspace = {
        "memberships": sorted(
            semantic_memberships,
            key=lambda item: (
                str(item["path"]),
                str(item["ini_slug"]),
                str(item["collection"]),
            ),
        ),
        "legacy_memberships": sorted(
            semantic_legacy,
            key=lambda item: (
                str(item["path"]),
                str(item["ini_slug"]),
                str(item["collection"]),
            ),
        ),
        "initiative_statuses": dict(sorted(initiative_statuses.items())),
    }
    semantic_digest = hashlib.sha256(json.dumps(
        semantic_workspace,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")).hexdigest()
    profile_identity = {
        f"profile_{index}_id": profile_id
        for index, (profile_id, _version) in enumerate(sorted(tracker_profiles))
    }
    profile_identity.update({
        f"profile_{index}_version": version
        for index, (_profile_id, version) in enumerate(sorted(tracker_profiles))
    })
    schema_ids = (
        "contracts/jsonschema/normalized-intake.schema.json",
        "contracts/jsonschema/workspace-entry.schema.json",
    )
    return canonical_result_identity(
        result,
        schema_ids=schema_ids,
        schema_content_digests={
            schema_ids[0]: _repository_contract_digest(
                root, schema_ids[0], _NORMALIZED_INTAKE_SCHEMA_DIGEST
            ),
            schema_ids[1]: _repository_contract_digest(
                root, schema_ids[1], _WORKSPACE_ENTRY_SCHEMA_DIGEST
            ),
        },
        contract_versions=(
            NORMALIZED_INTAKE_CONTRACT_VERSION,
            WORKSPACE_ENTRY_CONTRACT_VERSION,
        ),
        semantic_workspace_digest=semantic_digest,
        artifact_status_fingerprints=status_fingerprints,
        artifact_provenance_fingerprints=provenance_fingerprints,
        adapter_contract_version=_repository_contract_digest(
            root, "contracts/adapter.toml", _ADAPTER_CONTRACT_DIGEST
        ),
        tracker_profile=profile_identity,
        routing_configuration_version=ROUTING_CONFIGURATION_VERSION,
    )


def _collection_label(section: str, list_name: str) -> str:
    return f"{section}.{list_name}"


def _confined_artifact_path(root: Path, rel_path: str) -> Path | None:
    if not _is_repository_relative_path(rel_path):
        return None
    try:
        root_resolved = root.resolve()
        candidate = (root_resolved / rel_path).resolve()
        candidate.relative_to(root_resolved)
        return candidate
    except (OSError, RuntimeError, ValueError):
        return None


def _parse_preamble_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    fence_char: str | None = None
    fence_min_len = 0
    in_ml_comment = False
    field_re = re.compile(r"^- \*\*(?P<name>[^*]+):\*\*\s*(?P<value>.*)$")
    for line in text.splitlines():
        if not in_ml_comment:
            fm = _FENCE_RE.match(line)
            if fm:
                marker = fm.group(1)
                char = marker[0]
                length = len(marker)
                if fence_char is None:
                    fence_char, fence_min_len = char, length
                    continue
                rest = line[fm.end():]
                if char == fence_char and length >= fence_min_len and not rest.strip():
                    fence_char, fence_min_len = None, 0
                    continue
        if fence_char is not None:
            continue
        if in_ml_comment:
            if "-->" in line:
                remainder = line[line.index("-->") + 3:]
                remainder_clean = _HTML_COMMENT_RE.sub("", remainder)
                in_ml_comment = "<!--" in remainder_clean
            continue
        if _SECTION_HEADING_RE.match(line):
            break
        clean = _HTML_COMMENT_RE.sub("", line)
        if "<!--" in clean:
            clean = clean[:clean.index("<!--")]
            in_ml_comment = True
        match = field_re.match(clean)
        if match:
            fields.setdefault(match.group("name").strip().lower(), match.group("value").strip())
    return fields


def _parse_generic_status(text: str, kind: str) -> str | None:
    if kind == "spec":
        status, _ = _parse_spec_status(text)
        return status
    value = _parse_preamble_fields(text).get("status")
    if not value:
        return None
    if "→" in value:
        if value.rstrip().endswith("→"):
            return None
        segments = _TRANSITION_ARROW_RE.findall(value)
        return segments[-1] if segments else None
    return value.split()[0] if value.split() else None


def _source_authority_module_path() -> Path | None:
    engine_path = Path(__file__).resolve()
    skill_root = engine_path.parents[2]
    installed_path = (
        skill_root / "work-intake" / "scripts" / "refresh.py"
    )
    try:
        installed_path = installed_path.resolve(strict=True)
        installed_path.relative_to(skill_root.resolve(strict=True))
    except (OSError, ValueError):
        installed_path = None
    if installed_path is not None and installed_path.is_file():
        return installed_path
    packaged_path = engine_path.parent / "work_intake_refresh.py"
    try:
        packaged_path = packaged_path.resolve(strict=True)
        packaged_path.relative_to(engine_path.parent.resolve(strict=True))
    except (OSError, ValueError):
        packaged_path = None
    if packaged_path is not None and packaged_path.is_file():
        return packaged_path
    # The package-data engine is exercised directly in development before the
    # installed skill projection exists. Resolve that checkout without relying
    # on the caller's working directory.
    if (
        os.environ.get("AGENTBUNDLE_ALLOW_DEV_SOURCE_AUTHORITY") == "1"
        and len(engine_path.parents) > 4
    ):
        source_path = (
            engine_path.parents[4]
            / "packs"
            / "core"
            / ".apm"
            / "skills"
            / "work-intake"
            / "scripts"
            / "refresh.py"
        )
        if source_path.is_file():
            return source_path
    return None


def _load_source_authority_parser() -> Any:
    parser_path = _source_authority_module_path()
    if parser_path is None:
        try:
            module = importlib.import_module(
                "agentbundle._data.work_intake_refresh"
            )
        except ImportError as exc:
            raise RuntimeError("source authority parser unavailable") from exc
        parser = getattr(module, "parse_source_authority", None)
        if not callable(parser):
            raise RuntimeError("source authority parser unavailable")
        return parser
    module_name = "_workspace_status_source_authority_" + hashlib.sha256(
        str(parser_path).encode("utf-8")
    ).hexdigest()
    module = sys.modules.get(module_name)
    if module is None:
        spec = importlib.util.spec_from_file_location(module_name, parser_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("source authority parser unavailable")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            sys.modules.pop(module_name, None)
            raise RuntimeError("source authority parser unavailable") from exc
    parser = getattr(module, "parse_source_authority", None)
    if not callable(parser):
        raise RuntimeError("source authority parser unavailable")
    return parser


def _parse_source_authority_status(
    text: str,
) -> tuple[dict[str, object] | None, str | None, str | None, str | None]:
    if "```toml source-authority" not in text:
        return None, "source_authority_migration_required", None, None
    try:
        parser = _load_source_authority_parser()
        authority = parser(text)
    except RuntimeError:
        return None, "configuration_mismatch", None, None
    except ValueError:
        return None, "invalid_source_authority", None, None
    refresh: dict[str, object] = {
        "compared_revision": authority.source_revision,
        "conflict": any(
            conflict.get("status") == "unresolved"
            for conflict in authority.conflicts
        ),
    }
    if authority.accepted_revision is not None:
        refresh["accepted_revision"] = authority.accepted_revision
    return refresh, None, authority.source_ref, authority.source_revision


def _normalized_optional_artifact_value(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if stripped.lower() in {"", "none"}:
        return None
    return stripped


def _metadata_from_root(root: Path, entry: WorkspaceEntry) -> ArtifactMetadata | None:
    artifact_path = _confined_artifact_path(root, entry.path)
    if artifact_path is None:
        return ArtifactMetadata(
            path=entry.path,
            kind=entry.kind,
            status=None,
            exists=False,
            readable=False,
            invalid_path=True,
        )
    if not artifact_path.exists():
        return ArtifactMetadata(path=entry.path, kind=entry.kind, status=None, exists=False)
    try:
        text = artifact_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ArtifactMetadata(
            path=entry.path,
            kind=entry.kind,
            status=None,
            exists=True,
            readable=False,
        )
    status = _parse_generic_status(text, entry.kind)
    plan_exists = None
    plan_readable = True
    fields = _parse_preamble_fields(text)
    parent = _normalized_optional_artifact_value(
        fields.get("brief") or fields.get("source parent") or fields.get("parent")
    )
    ref = fields.get("source ref") or fields.get("ref")
    revision = fields.get("source revision") or fields.get("revision")
    refresh_conflict = fields.get("refresh conflict", "").lower() == "true"
    resolution = fields.get("resolution")
    authority_status = None
    authority_error = None
    if entry.source.mode == "tracker-origin":
        authority_status, authority_error, authority_ref, authority_revision = (
            _parse_source_authority_status(text)
        )
        if authority_status is not None:
            ref = authority_ref
            revision = authority_revision
        refresh_conflict = bool(
            authority_status is not None and authority_status.get("conflict")
        )
    plan_invalid_path = False
    if entry.kind == "spec":
        plan_path = _confined_artifact_path(
            root, entry.path.removesuffix("/spec.md") + "/plan.md"
        )
        if plan_path is None:
            plan_invalid_path = True
            plan_exists = False
        else:
            plan_exists = plan_path.exists()
            if plan_exists:
                try:
                    plan_readable = plan_path.is_file()
                    if plan_readable:
                        with plan_path.open("rb") as handle:
                            handle.read(0)
                except OSError:
                    plan_readable = False
    return ArtifactMetadata(
        path=entry.path,
        kind=entry.kind,
        status=status,
        exists=True,
        readable=True,
        plan_invalid_path=plan_invalid_path,
        plan_readable=plan_readable,
        plan_exists=plan_exists,
        parent=parent,
        ref=ref,
        revision=revision,
        refresh_conflict=refresh_conflict,
        resolution=resolution,
        authority_status=authority_status,
        authority_error=authority_error,
    )


def _artifact_metadata(
    _workspace: dict,
    entry: WorkspaceEntry,
    root: Path | None,
) -> ArtifactMetadata | None:
    if root is not None:
        return _metadata_from_root(root, entry)
    return None


def _metadata_from_membership(membership: WorkspaceMembership) -> ArtifactMetadata | None:
    status = _membership_status(membership)
    if status is None:
        return None
    return ArtifactMetadata(
        path=membership.entry.path,
        kind=membership.entry.kind,
        status=status,
        exists=True,
    )


_COORDINATION_RECEIPT_FIELDS = frozenset(
    {
        "id",
        "remote_kind",
        "remote_ref",
        "accepted_revision",
        "required_status",
        "reported_status",
        "reviewed_by",
        "reviewed_at",
        "refresh_conflict",
    }
)
_COORDINATION_FENCE_RE = re.compile(
    r"^ {0,3}(?P<marker>`{3,}|~{3,})(?P<info>[^\r\n]*)$"
)
_RFC3339_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def _parse_reviewed_at(value: object) -> bool:
    if not isinstance(value, str) or not _is_bounded_text(value, 100):
        return False
    if not _RFC3339_DATETIME_RE.fullmatch(value):
        return False
    try:
        parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _coordination_receipt_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    fence_marker: str | None = None
    fence_char: str | None = None
    capture = False
    captured: list[str] = []
    for line in text.splitlines():
        match = _COORDINATION_FENCE_RE.match(line)
        if fence_marker is None:
            if not match:
                continue
            marker = match.group("marker")
            info = match.group("info").strip()
            fence_marker = marker
            fence_char = marker[0]
            capture = info == "toml coordination-receipts"
            captured = []
            continue
        if match:
            marker = match.group("marker")
            info = match.group("info").strip()
            if (
                marker[0] == fence_char
                and len(marker) >= len(fence_marker)
                and info == ""
            ):
                if capture:
                    blocks.append("\n".join(captured))
                fence_marker = None
                fence_char = None
                capture = False
                captured = []
                continue
        if capture:
            captured.append(line)
    return blocks


def _validated_receipt_match(
    receipt: object,
    dep: Dependency,
    seen: set[str],
) -> tuple[bool, bool]:
    if not isinstance(receipt, dict) or set(receipt) != _COORDINATION_RECEIPT_FIELDS:
        return False, False
    receipt_id = receipt.get("id")
    if not _is_bounded_text(receipt_id, 200) or receipt_id in seen:
        return False, False
    seen.add(receipt_id)
    if receipt.get("remote_kind") not in {"brief", "spec"}:
        return False, False
    if not _is_safe_locator(receipt.get("remote_ref")):
        return False, False
    if not _is_bounded_text(receipt.get("accepted_revision"), 200):
        return False, False
    if not _is_bounded_text(receipt.get("reviewed_by"), 200):
        return False, False
    if not _parse_reviewed_at(receipt.get("reviewed_at")):
        return False, False
    if receipt.get("required_status") != "Shipped":
        return False, False
    if receipt.get("reported_status") != "Shipped":
        return False, False
    if receipt.get("refresh_conflict") is not False:
        return False, False
    matches = (
        receipt_id == dep.receipt_id
        and receipt.get("remote_kind") == dep.kind
        and receipt.get("accepted_revision") == dep.accepted_revision
    )
    return True, matches


def _cross_repo_receipt_satisfied(
    dep: Dependency,
    root: Path | None,
) -> tuple[bool, RoutingFinding | None]:
    if root is None or dep.containing_brief is None or dep.path != dep.containing_brief:
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    if not _is_canonical_local_brief_path(dep.path):
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    brief_path = _confined_artifact_path(root, dep.containing_brief)
    if brief_path is None:
        return False, _finding("invalid_artifact_path", dep.containing_brief, "receipt path")
    if not brief_path.exists():
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    try:
        text = brief_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    blocks = _coordination_receipt_blocks(text)
    if len(blocks) != 1:
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    try:
        parsed = tomllib.loads(blocks[0])
    except tomllib.TOMLDecodeError:
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    if set(parsed) != {"coordination_receipts"}:
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    receipts = parsed.get("coordination_receipts")
    if not isinstance(receipts, list):
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    seen: set[str] = set()
    matched = False
    for receipt in receipts:
        valid, matches = _validated_receipt_match(receipt, dep, seen)
        if not valid:
            return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
        matched = matched or matches
    if not matched:
        return False, _finding("invalid_receipt", dep.path, "invalid dependency receipt")
    return True, None


def _parse_membership_entry(
    raw: object,
    collection: str,
    ini_slug: str,
    status: str,
) -> tuple[
    WorkspaceMembership | None,
    LegacyWorkspaceMembership | None,
    list[RoutingFinding],
    str | None,
]:
    parsed, findings = parse_workspace_entry(raw)
    if parsed is not None:
        return WorkspaceMembership(parsed, ini_slug, collection, status), None, [], None
    raw_path = raw.get("path") if isinstance(raw, dict) else None
    if _is_repository_relative_path(raw_path):
        findings = [
            dataclasses.replace(finding, path=raw_path)
            if not finding.path else finding
            for finding in findings
        ]
    legacy = parse_legacy_workspace_entry(collection, raw)
    if legacy.finding.code == "legacy_entry":
        return None, LegacyWorkspaceMembership(legacy, ini_slug, collection, status), [
            legacy.finding
        ], None
    if legacy.finding.code == "invalid_artifact_path" and not _is_target_like_entry(raw):
        return None, None, [legacy.finding], None
    if legacy.finding.code == "unsupported_legacy" and not _is_target_like_entry(raw):
        return None, None, [legacy.finding], None
    if findings:
        blocks_dependencies = any(
            finding.code in {"invalid_entry", "invalid_artifact_path"}
            for finding in findings
        )
        blocked_path = _target_like_blocked_path(raw) if blocks_dependencies else None
        return None, None, findings, blocked_path
    return None, None, [legacy.finding], None


def _extract_canonical_memberships(
    workspace: dict,
) -> tuple[
    list[WorkspaceMembership],
    list[LegacyWorkspaceMembership],
    list[RoutingFinding],
    dict[str, int],
]:
    memberships: list[WorkspaceMembership] = []
    legacy_memberships: list[LegacyWorkspaceMembership] = []
    findings: list[RoutingFinding] = []
    parse_blocked_path_counts: dict[str, int] = {}
    for section_name, top_level_names in _TOP_LEVEL_ENTRY_COLLECTIONS.items():
        section = workspace.get(section_name, {})
        if not isinstance(section, dict):
            findings.append(_finding("invalid_workspace", section_name, "invalid section"))
            continue
        for list_name in top_level_names:
            entries = section.get(list_name, [])
            if not isinstance(entries, list):
                findings.append(_finding("invalid_workspace", detail="invalid lifecycle list"))
                continue
            collection = _collection_label(section_name, list_name)
            for raw_entry in entries:
                (
                    membership,
                    legacy_membership,
                    entry_findings,
                    blocked_path,
                ) = _parse_membership_entry(raw_entry, collection, "", "")
                if membership is not None:
                    memberships.append(membership)
                if legacy_membership is not None:
                    legacy_memberships.append(legacy_membership)
                if blocked_path is not None:
                    parse_blocked_path_counts[blocked_path] = (
                        parse_blocked_path_counts.get(blocked_path, 0) + 1
                    )
                findings.extend(entry_findings)
    for raw_ini_slug, section in workspace.items():
        if not isinstance(raw_ini_slug, str) or not raw_ini_slug.startswith("ini-"):
            continue
        if not _CANONICAL_INITIATIVE_RE.fullmatch(raw_ini_slug):
            findings.append(
                _finding("invalid_workspace", "workspace.toml", "invalid initiative slug")
            )
            continue
        ini_slug = raw_ini_slug
        if not isinstance(section, dict):
            findings.append(_finding("invalid_workspace", detail="invalid initiative section"))
            continue
        status = section.get("status", "")
        status = status if isinstance(status, str) else ""
        for section_name, initiative_names in _INITIATIVE_ENTRY_COLLECTIONS.items():
            subsection = section.get(section_name, {})
            if not isinstance(subsection, dict):
                findings.append(
                    _finding("invalid_workspace", f"{ini_slug}.{section_name}", "invalid section")
                )
                continue
            for list_name in initiative_names:
                entries = subsection.get(list_name, [])
                if entries is None:
                    entries = []
                if (
                    section_name == "brief_queue"
                    and list_name == "executing"
                    and isinstance(entries, str)
                ):
                    entries = [] if entries == "" else [entries]
                if not isinstance(entries, list):
                    findings.append(_finding("invalid_workspace", detail="invalid lifecycle list"))
                    continue
                collection = _collection_label(section_name, list_name)
                for raw_entry in entries:
                    (
                        membership,
                        legacy_membership,
                        entry_findings,
                        blocked_path,
                    ) = _parse_membership_entry(raw_entry, collection, ini_slug, status)
                    if membership is not None:
                        memberships.append(membership)
                    if legacy_membership is not None:
                        legacy_memberships.append(legacy_membership)
                    if blocked_path is not None:
                        parse_blocked_path_counts[blocked_path] = (
                            parse_blocked_path_counts.get(blocked_path, 0) + 1
                        )
                    findings.extend(entry_findings)
    return memberships, legacy_memberships, findings, parse_blocked_path_counts


def _membership_status(membership: WorkspaceMembership) -> str | None:
    if membership.collection == "work.shipped":
        return "Shipped"
    if membership.collection == "brief_queue.draft":
        return "Draft"
    if membership.collection == "brief_queue.ready":
        return "Ready"
    if membership.collection == "brief_queue.executing":
        return "Executing"
    if membership.collection == "brief_queue.shipped":
        return "Shipped"
    return None


def _dependency_terminal_satisfied(
    kind: str,
    status: str | None,
    metadata: ArtifactMetadata,
) -> bool:
    if kind == "defect":
        return status == "Closed" and metadata.resolution == "fixed"
    terminals = _TERMINAL_STATUS_BY_KIND.get(kind, set())
    return status in terminals


def _provenance_path_is_invalid(
    root: Path | None,
    path: str | None,
    *,
    require_local_brief: bool = False,
) -> bool:
    if path is None:
        return False
    if not _is_repository_relative_path(path):
        return True
    if require_local_brief and not _is_canonical_local_brief_path(path):
        return True
    return root is not None and _confined_artifact_path(root, path) is None


def _dependency_metadata_safety_finding(
    path: str,
    kind: str,
    metadata: ArtifactMetadata | None,
    root: Path | None,
) -> RoutingFinding | None:
    if metadata is not None and metadata.invalid_path:
        return _finding("invalid_artifact_path", path, "dependency path")
    if metadata is None or not metadata.exists:
        return _finding("missing_dependency", path, "dependency target missing")
    if not metadata.readable:
        return _finding("unreadable_artifact", path, "dependency unreadable")
    if _provenance_path_is_invalid(
        root,
        metadata.parent,
        require_local_brief=kind == "spec",
    ):
        return _finding("invalid_artifact_path", metadata.parent or "", "dependency parent")
    if metadata.refresh_conflict:
        return _finding("refresh_conflict", path, "dependency refresh conflict")
    return None


def _dependency_is_satisfied(
    dep: Dependency,
    workspace: dict,
    by_path: dict[str, list[WorkspaceMembership]],
    structurally_blocked_paths: set[str],
    root: Path | None,
) -> tuple[bool, RoutingFinding | None]:
    if dep.path in structurally_blocked_paths:
        return False, _finding("unsatisfied_dependency", dep.path, "dependency has findings")
    if dep.type == "cross-repo":
        return _cross_repo_receipt_satisfied(dep, root)

    matches = by_path.get(dep.path, [])
    if matches and not any(match.entry.kind == dep.kind for match in matches):
        return False, _finding("unsatisfied_dependency", dep.path, "dependency kind mismatch")
    if dep.kind == "defect" and not any(
        match.collection == "backlog.closed" for match in matches
    ):
        probe = WorkspaceEntry(
            path=dep.path,
            kind=dep.kind,
            source=SourceRecord(mode="repo-origin"),
            summary="dependency probe",
            needs=[],
        )
        metadata = _artifact_metadata(workspace, probe, root)
        safety_finding = _dependency_metadata_safety_finding(
            dep.path, dep.kind, metadata, root
        )
        if safety_finding is not None:
            return False, safety_finding
        return False, _finding(
            "unsatisfied_dependency", dep.path, "defect lacks closed membership"
        )
    if matches:
        metadata = _artifact_metadata(workspace, matches[0].entry, root)
    else:
        probe = WorkspaceEntry(
            path=dep.path,
            kind=dep.kind,
            source=SourceRecord(mode="repo-origin"),
            summary="dependency probe",
            needs=[],
        )
        metadata = _artifact_metadata(workspace, probe, root)
    safety_finding = _dependency_metadata_safety_finding(
        dep.path, dep.kind, metadata, root
    )
    if safety_finding is not None:
        return False, safety_finding
    status = metadata.status
    if status is None and matches:
        status = _membership_status(matches[0])
    if _dependency_terminal_satisfied(dep.kind, status, metadata):
        return True, None
    return False, _finding("unsatisfied_dependency", dep.path, "dependency not terminal")


def _dependency_cycles(memberships: list[WorkspaceMembership]) -> set[str]:
    graph: dict[str, list[str]] = {}
    paths = {membership.entry.path for membership in memberships}
    for membership in memberships:
        graph[membership.entry.path] = [
            dep.path for dep in membership.entry.needs
            if dep.type == "local" and dep.path in paths
        ]
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: set[str] = set()

    def visit(path: str, stack: list[str]) -> None:
        if path in visiting:
            cycles.update(stack[stack.index(path):])
            return
        if path in visited:
            return
        visiting.add(path)
        for child in graph.get(path, []):
            visit(child, [*stack, child])
        visiting.remove(path)
        visited.add(path)

    for path in graph:
        visit(path, [path])
    return cycles


def _legacy_canonical_alias(entry: LegacyWorkspaceEntry) -> str | None:
    if entry.kind == "spec":
        if _is_legacy_spec_path(entry.path):
            return f"docs/specs/{entry.path.split('/')[1]}/spec.md"
        if entry.collection == "backlog.open" and _is_legacy_slug(entry.path):
            return f"docs/specs/{entry.path}/spec.md"
    if entry.kind == "brief" and _is_canonical_local_brief_path(entry.path):
        return entry.path
    if (
        entry.collection in {"shaping_queue.active", "shaping_queue.backlog"}
        and entry.kind in {"intent", "research", "design"}
        and isinstance(entry.raw, dict)
        and _is_legacy_slug(entry.path)
    ):
        directory = {
            "intent": "intents",
            "research": "research",
            "design": "design",
        }[entry.kind]
        return f"docs/product/{directory}/{entry.path}.md"
    return None


def _brief_child_spec_states(
    memberships: list[WorkspaceMembership],
    workspace: dict,
    root: Path | None,
) -> dict[str, set[str]]:
    states: dict[str, set[str]] = {}
    for membership in memberships:
        entry = membership.entry
        if entry.kind != "spec":
            continue
        metadata = _artifact_metadata(workspace, entry, root)
        parent_paths = {
            path for path in (
                _normalized_optional_artifact_value(entry.source.parent),
                metadata.parent if metadata is not None else None,
            )
            if path is not None
        }
        if not parent_paths:
            continue
        status = metadata.status if metadata is not None else None
        if membership.collection == "work.active":
            child_state = "Implementing"
        elif membership.collection == "work.queue":
            child_state = "Queued"
        elif status == "Shipped":
            child_state = "Shipped"
        elif status is None:
            child_state = "Unknown"
        else:
            child_state = status
        for parent_path in parent_paths:
            states.setdefault(parent_path, set()).add(child_state)
    return states


def _append_impossible_transition(
    findings: list[RoutingFinding],
    entry: WorkspaceEntry,
    metadata: ArtifactMetadata,
    expected: set[str],
    detail: str,
) -> None:
    if metadata.status not in expected:
        findings.append(_finding("impossible_transition", entry.path, detail))


def _append_lifecycle_findings(
    findings: list[RoutingFinding],
    membership: WorkspaceMembership,
    metadata: ArtifactMetadata,
) -> None:
    entry = membership.entry
    collection = membership.collection
    if collection == "backlog.open":
        if entry.kind == "defect":
            if metadata.status == "Closed":
                findings.append(
                    _finding("impossible_transition", entry.path, "open defect status")
                )
        else:
            _append_impossible_transition(
                findings, entry, metadata, {"Draft"}, "open backlog status"
            )
        return
    if collection == "backlog.closed":
        if entry.kind != "defect":
            findings.append(
                _finding("impossible_transition", entry.path, "closed backlog kind")
            )
        elif metadata.status != "Closed" or metadata.resolution not in {
            "fixed",
            "declined",
            "superseded",
        }:
            findings.append(
                _finding("impossible_transition", entry.path, "closed defect status")
            )
        return
    if entry.kind == "spec":
        if collection == "work.active":
            _append_impossible_transition(
                findings, entry, metadata, {"Implementing"}, "active spec status"
            )
        elif collection == "work.shipped":
            _append_impossible_transition(
                findings, entry, metadata, {"Shipped"}, "shipped spec status"
            )
        elif collection == "work.queue" and metadata.status in {"Implementing", "Shipped"}:
            findings.append(_finding("impossible_transition", entry.path, "queue spec status"))
    elif entry.kind == "brief":
        expected_by_collection = {
            "brief_queue.draft": {"Draft"},
            "brief_queue.ready": {"Ready"},
            "brief_queue.executing": {"Executing"},
            "brief_queue.shipped": {"Shipped"},
        }
        expected = expected_by_collection.get(collection)
        if expected is not None:
            _append_impossible_transition(
                findings, entry, metadata, expected, "brief lifecycle status"
            )
    elif collection.startswith("shaping_queue."):
        terminal = _TERMINAL_STATUS_BY_KIND.get(entry.kind, set())
        if collection == "shaping_queue.active" and metadata.status in terminal:
            findings.append(
                _finding("impossible_transition", entry.path, "active shaping status")
            )
        elif collection == "shaping_queue.backlog" and metadata.status in terminal:
            findings.append(
                _finding("impossible_transition", entry.path, "backlog shaping status")
            )


def _append_collection_kind_findings(
    findings: list[RoutingFinding],
    membership: WorkspaceMembership,
) -> bool:
    allowed_kinds = _ALLOWED_KIND_BY_COLLECTION.get(membership.collection)
    if allowed_kinds is None or membership.entry.kind in allowed_kinds:
        return False
    findings.append(
        _finding("impossible_transition", membership.entry.path, "collection kind")
    )
    return True


def _append_plan_findings(
    findings: list[RoutingFinding],
    membership: WorkspaceMembership,
    metadata: ArtifactMetadata,
) -> None:
    if membership.entry.kind != "spec" or not membership.collection.startswith("work."):
        return
    if metadata.plan_invalid_path:
        findings.append(
            _finding("invalid_artifact_path", membership.entry.path, "sibling plan path")
        )
    elif metadata.plan_exists is False:
        findings.append(_finding("missing_plan", membership.entry.path, "sibling plan missing"))
    elif not metadata.plan_readable:
        findings.append(
            _finding("unreadable_artifact", membership.entry.path, "sibling plan unreadable")
        )


def _authority_status_for_entry(
    entry: WorkspaceEntry,
    metadata: ArtifactMetadata | None,
) -> dict[str, object] | None:
    if (
        entry.source.mode == "tracker-origin"
        and metadata is not None
        and metadata.authority_error is not None
    ):
        return None
    profile = entry.source.tracker_profile
    refresh_available: bool | str = "unknown"
    write_back_available: bool | str = "unknown"
    if profile is None or entry.source.mode == "repo-origin":
        # No resolved profile, or a repo-origin entry that is definitionally
        # write-back incapable. Neither can report availability as True.
        refresh_available = False
        write_back_available = False
    elif metadata is not None and metadata.status in {
        "Implementing",
        "Executing",
        "Shipped",
    }:
        refresh_available = False
        if metadata.status != "Shipped":
            write_back_available = False
    refresh: dict[str, object] = {
        "available": refresh_available,
        "write_back_available": write_back_available,
        "conflict": bool(metadata.refresh_conflict) if metadata is not None else False,
    }
    if entry.source.revision is not None:
        refresh["compared_revision"] = entry.source.revision
    if metadata is not None and metadata.authority_status is not None:
        authority_refresh = metadata.authority_status
        if "compared_revision" in authority_refresh:
            refresh["compared_revision"] = authority_refresh["compared_revision"]
        if "accepted_revision" in authority_refresh:
            refresh["accepted_revision"] = authority_refresh["accepted_revision"]
        refresh["conflict"] = bool(refresh["conflict"]) or bool(
            authority_refresh.get("conflict")
        )
    status: dict[str, object] = {
        "origin_mode": entry.source.mode,
        "refresh": refresh,
    }
    if profile is not None:
        status["profile"] = dict(profile)
    return status


def _structural_findings(
    membership: WorkspaceMembership,
    metadata: ArtifactMetadata | None,
    duplicate_paths: set[str],
    cycle_paths: set[str],
    brief_child_states: dict[str, set[str]],
    global_invalid_workspace: bool = False,
    root: Path | None = None,
) -> list[RoutingFinding]:
    entry = membership.entry
    findings: list[RoutingFinding] = []
    if global_invalid_workspace:
        findings.append(_finding("invalid_workspace", entry.path, "invalid workspace state"))
    if entry.path in duplicate_paths:
        findings.append(_finding("duplicate_membership", entry.path, "duplicate lifecycle entry"))
    if entry.path in cycle_paths:
        findings.append(_finding("dependency_cycle", entry.path, "dependency cycle"))
    if membership.ini_slug and membership.initiative_status not in ("active",):
        findings.append(_finding("inactive_initiative", entry.path, "initiative is inactive"))
    source_parent = _normalized_optional_artifact_value(entry.source.parent)
    require_local_brief_parent = entry.kind == "spec"
    if _provenance_path_is_invalid(
        root,
        source_parent,
        require_local_brief=require_local_brief_parent,
    ):
        findings.append(_finding("invalid_artifact_path", source_parent or "", "source parent"))
    skip_status_lifecycle = _append_collection_kind_findings(findings, membership)
    if metadata is not None and metadata.invalid_path:
        findings.append(_finding("invalid_artifact_path", entry.path, "artifact path"))
        return findings
    if metadata is None or not metadata.exists:
        findings.append(_finding("missing_artifact", entry.path, "artifact is missing"))
        return findings
    if not metadata.readable:
        findings.append(_finding("unreadable_artifact", entry.path, "artifact is unreadable"))
        return findings
    if metadata.authority_error is not None:
        findings.append(
            _finding(metadata.authority_error, entry.path, "source authority block")
        )
    if metadata.refresh_conflict:
        findings.append(_finding("refresh_conflict", entry.path, "unresolved refresh conflict"))
    if _provenance_path_is_invalid(
        root,
        metadata.parent,
        require_local_brief=require_local_brief_parent,
    ):
        findings.append(
            _finding("invalid_artifact_path", metadata.parent or "", "artifact parent")
        )
    if source_parent != metadata.parent:
        findings.append(_finding("provenance_mismatch", entry.path, "parent mismatch"))
    if (
        entry.source.mode == "tracker-origin"
        and (entry.source.ref or metadata.ref)
        and entry.source.ref != metadata.ref
    ):
        findings.append(_finding("provenance_mismatch", entry.path, "source ref mismatch"))
    if (
        entry.source.mode == "tracker-origin"
        and (entry.source.revision or metadata.revision)
        and entry.source.revision != metadata.revision
    ):
        findings.append(
            _finding("provenance_mismatch", entry.path, "source revision mismatch")
        )
    if entry.kind == "brief" and membership.collection.startswith("brief_queue."):
        child_states = brief_child_states.get(entry.path, set())
        invalid_child_scope = (
            membership.collection == "brief_queue.ready"
            and "Implementing" in child_states
        ) or (
            membership.collection == "brief_queue.executing"
            and "Implementing" not in child_states
        ) or (
            membership.collection == "brief_queue.shipped"
            and any(state != "Shipped" for state in child_states)
        )
        if invalid_child_scope:
            findings.append(_finding("impossible_transition", entry.path, "brief child scope"))
    _append_plan_findings(findings, membership, metadata)
    if not skip_status_lifecycle:
        _append_lifecycle_findings(findings, membership, metadata)
    return findings


def evaluate_dispatch(
    membership: WorkspaceMembership,
    workspace: dict,
    by_path: dict[str, list[WorkspaceMembership]],
    duplicate_paths: set[str],
    cycle_paths: set[str],
    structurally_blocked_paths: set[str],
    brief_child_states: dict[str, set[str]],
    global_invalid_workspace: bool = False,
    root: Path | None = None,
) -> DispatchEvaluation:
    """Evaluate the positive T2 dispatch predicate for one canonical membership."""
    entry = membership.entry
    metadata = _artifact_metadata(workspace, entry, root) or _metadata_from_membership(membership)
    findings = _structural_findings(
        membership,
        metadata,
        duplicate_paths,
        cycle_paths,
        brief_child_states,
        global_invalid_workspace,
        root,
    )
    if (
        entry.kind == "spec"
        and membership.collection == "work.queue"
        and metadata is not None
        and metadata.exists
        and metadata.readable
    ):
        if not (entry.path.startswith("docs/specs/") and entry.path.endswith("/spec.md")):
            findings.append(_finding("invalid_artifact_path", entry.path, "spec path shape"))
        if metadata.status != "Approved":
            findings.append(_finding("unapproved_spec", entry.path, "spec is not Approved"))
    for dep in entry.needs:
        satisfied, finding = _dependency_is_satisfied(
            dep,
            workspace,
            by_path,
            structurally_blocked_paths,
            root,
        )
        if not satisfied and finding is not None:
            findings.append(finding)
    dispatchable = (
        entry.kind == "spec"
        and membership.collection == "work.queue"
        and membership.initiative_status == "active"
        and metadata is not None
        and metadata.exists
        and metadata.readable
        and metadata.status == "Approved"
        and metadata.plan_exists is True
        and metadata.plan_readable
        and entry.path.startswith("docs/specs/")
        and entry.path.endswith("/spec.md")
        and not findings
    )
    return DispatchEvaluation(
        entry=entry,
        ini_slug=membership.ini_slug,
        collection=membership.collection,
        dispatchable=dispatchable,
        findings=findings,
        authority_status=_authority_status_for_entry(entry, metadata),
    )


def run_canonical_reconciliation(
    workspace: dict,
    root: Path | None = None,
) -> CanonicalWorkspaceResult:
    """Parse target entries and evaluate T2 canonical findings without projection changes."""
    (
        memberships,
        legacy_memberships,
        parse_findings,
        parse_blocked_path_counts,
    ) = _extract_canonical_memberships(workspace)
    parse_blocked_paths = set(parse_blocked_path_counts)
    by_path: dict[str, list[WorkspaceMembership]] = {}
    for membership in memberships:
        by_path.setdefault(membership.entry.path, []).append(membership)
    legacy_alias_counts: dict[str, int] = {}
    for legacy_membership in legacy_memberships:
        alias = _legacy_canonical_alias(legacy_membership.entry)
        if alias is not None:
            legacy_alias_counts[alias] = legacy_alias_counts.get(alias, 0) + 1
    duplicate_paths = {
        path
        for path, items in by_path.items()
        if len(items) + legacy_alias_counts.get(path, 0) > 1
    }
    mixed_parse_legacy_duplicate_paths = {
        path
        for path in parse_blocked_paths
        if path not in by_path and legacy_alias_counts.get(path, 0) > 0
    }
    parse_only_duplicate_paths = {
        path
        for path, count in parse_blocked_path_counts.items()
        if count > 1 and path not in by_path
    }
    legacy_only_duplicate_paths = {
        path
        for path, count in legacy_alias_counts.items()
        if count > 1 and path not in by_path
    }
    legacy_only_duplicate_findings = [
        _finding("duplicate_membership", path, "duplicate lifecycle entry")
        for path in sorted(
            legacy_only_duplicate_paths
            | mixed_parse_legacy_duplicate_paths
            | parse_only_duplicate_paths
        )
    ]
    cycle_paths = _dependency_cycles(memberships)
    brief_child_states = _brief_child_spec_states(memberships, workspace, root)
    global_invalid_workspace = any(
        finding.code == "invalid_workspace" for finding in parse_findings
    )
    duplicate_paths.update(path for path in parse_blocked_paths if path in by_path)
    structurally_blocked_paths: set[str] = {
        *legacy_only_duplicate_paths,
        *mixed_parse_legacy_duplicate_paths,
        *parse_only_duplicate_paths,
        *parse_blocked_paths,
    }
    for membership in memberships:
        metadata = (
            _artifact_metadata(workspace, membership.entry, root)
            or _metadata_from_membership(membership)
        )
        if _structural_findings(
            membership,
            metadata,
            duplicate_paths,
            cycle_paths,
            brief_child_states,
            global_invalid_workspace,
            root,
        ):
            structurally_blocked_paths.add(membership.entry.path)
    evaluations = [
        evaluate_dispatch(
            membership,
            workspace,
            by_path,
            duplicate_paths,
            cycle_paths,
            structurally_blocked_paths,
            brief_child_states,
            global_invalid_workspace,
            root,
        )
        for membership in memberships
    ]
    dispatch_by_path = {evaluation.entry.path: evaluation for evaluation in evaluations}
    findings = [
        *parse_findings,
        *legacy_only_duplicate_findings,
        *(finding for evaluation in evaluations for finding in evaluation.findings),
    ]
    return CanonicalWorkspaceResult(
        memberships=memberships,
        legacy_memberships=legacy_memberships,
        findings=findings,
        evaluations=evaluations,
        dispatch_by_path=dispatch_by_path,
    )


def _supported_brief_queue_path(raw: object) -> str | None:
    """Return a canonical target or released scalar brief-queue path."""
    if isinstance(raw, str):
        return raw
    parsed, _findings = parse_workspace_entry(raw)
    if parsed is not None and parsed.kind == "brief":
        return parsed.path
    return None


def extract_initiatives(workspace: dict) -> list[Initiative]:
    """Extract all initiatives (ini-*) from a parsed workspace TOML dict."""
    initiatives: list[Initiative] = []
    for key, section in workspace.items():
        if not isinstance(key, str) or not _CANONICAL_INITIATIVE_RE.fullmatch(key):
            continue
        if not isinstance(section, dict):
            continue
        work_raw = section.get("work", {})
        shaping_raw = section.get("shaping_queue", {})
        brief_raw = section.get("brief_queue")
        if not isinstance(work_raw, dict):
            work_raw = {}
        if not isinstance(shaping_raw, dict):
            shaping_raw = {}

        work_active = work_raw.get("active", [])
        work_shipped = work_raw.get("shipped", [])
        work_queue = work_raw.get("queue", [])
        work_active = work_active if isinstance(work_active, list) else []
        work_shipped = work_shipped if isinstance(work_shipped, list) else []
        work_queue = work_queue if isinstance(work_queue, list) else []

        work = InitiativeWork(
            active=[_parse_work_entry(e) for e in work_active],
            shipped=[_parse_work_entry(e) for e in work_shipped],
            queue=[_parse_work_entry(e) for e in work_queue],
        )
        shaping = InitiativeShaping(
            active=_parse_supported_shaping_entries(
                "shaping_queue.active", shaping_raw.get("active", [])
            ),
            backlog=_parse_supported_shaping_entries(
                "shaping_queue.backlog", shaping_raw.get("backlog", [])
            ),
        )
        brief_queue: BriefQueue | None = None
        if isinstance(brief_raw, dict):
            executing_raw = brief_raw.get("executing", "")
            ready_raw = brief_raw.get("ready", [])
            draft_raw = brief_raw.get("draft", [])
            if isinstance(executing_raw, list):
                executing_paths = [
                    path
                    for raw in executing_raw
                    if (path := _supported_brief_queue_path(raw)) is not None
                ]
                executing = executing_paths[0] if executing_paths else ""
            else:
                executing = _supported_brief_queue_path(executing_raw) or ""
            ready = []
            if isinstance(ready_raw, list):
                ready = [
                    path
                    for raw in ready_raw
                    if (path := _supported_brief_queue_path(raw)) is not None
                ]
            draft = []
            if isinstance(draft_raw, list):
                draft = [
                    path
                    for raw in draft_raw
                    if (path := _supported_brief_queue_path(raw)) is not None
                ]
            brief_queue = BriefQueue(
                executing=executing,
                ready=ready,
                draft=draft,
            )
        initiatives.append(Initiative(
            slug=key,
            name=section.get("name", ""),
            status=section.get("status", ""),  # absent → "" (not silently promoted to active)
            milestone=section.get("milestone", ""),
            work=work,
            shaping=shaping,
            brief_queue=brief_queue,
        ))
    return initiatives


# ── Status extraction ─────────────────────────────────────────────────────────

# Captures the status content before any annotation (parenthetical or HTML comment).
# A spaced arrow inside "(root → leaf)" must never be read as a transition.
_STATUS_FIELD_RE = re.compile(r'\*\*Status:\*\*\s+(.*?)(?:\s*\(|\s*<!--|$)')
# Finds ALL segments after → (non-whitespace, non-arrow chars), so compact multi-hop
# "Draft→Approved→Shipped" yields ["Approved", "Shipped"] and a non-letter final
# segment (e.g. "→ 2026", trailing "→") still forces None instead of backtracking.
_TRANSITION_ARROW_RE = re.compile(r'→\s*([^→\s]+)')
# Stop at the first ##+ heading — status lines in body examples or tables are
# never authoritative. Matches lint-spec-status.py's canonical preamble boundary.
_SECTION_HEADING_RE = re.compile(r"^ {0,3}#{2,}(?:[ \t]|$)")
# HTML comments; stripped before the status-field check so that
# "<!-- - **Status:** Shipped -->" cannot satisfy the preamble guard.
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
# CommonMark fence opener/closer: 0-3 spaces indentation, then 3+ backticks or
# 3+ tildes. Opening type and minimum length must match the closer.
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def _safe_spec_path(root: Path, slug: str) -> Path | None:
    """Return the spec.md Path only if it resolves within root/docs/specs/.

    Rejects slugs containing `..` or absolute paths before joining — resolve()
    alone normalises traversal so the relative_to check would silently accept
    "foo/../bar"; the pre-join rejection closes that gap.
    """
    slug_path = Path(slug)
    if slug_path.is_absolute() or ".." in slug_path.parts:
        return None
    # RuntimeError guards against circular symlinks on Python 3.11/3.12.
    try:
        specs_dir = (root / "docs" / "specs").resolve()
        specs_dir.relative_to(root.resolve())
    except (OSError, RuntimeError, ValueError):
        return None
    try:
        candidate = (specs_dir / slug / "spec.md").resolve()
        candidate.relative_to(specs_dir)
        return candidate
    except (OSError, RuntimeError, ValueError):
        return None


def _spec_slug_from_workspace_path(path: str) -> str:
    if path.startswith("docs/specs/") and path.endswith("/spec.md"):
        return path[len("docs/specs/"):-len("/spec.md")]
    return path.removeprefix("spec/")


VALID_STATUSES = frozenset({"Draft", "Approved", "Implementing", "Shipped", "Archived"})


def _parse_spec_status(text: str) -> tuple[str | None, str | None]:
    """Parse a spec.md string and return (status_token, raw_status_line).

    Scans the preamble (before the first ## heading), skipping fenced code
    blocks and HTML comments, and returns the first `- **Status:**` field.
    Returns (None, None) when no valid status is found.
    """
    fence_char: str | None = None  # None = not in fence; "`" or "~" = in fence
    fence_min_len: int = 0         # minimum closing fence length
    in_ml_comment = False          # inside a multi-line HTML comment
    for line in text.splitlines():
        # Fence tracking — CommonMark: 0–3 spaces of indentation; opening delimiter
        # type (` or ~) and minimum length must match the closer. A `~~~` inside a
        # ``` fence does NOT close it; it is treated as fence body content.
        if not in_ml_comment:
            fm = _FENCE_RE.match(line)
            if fm:
                marker = fm.group(1)
                char = marker[0]
                length = len(marker)
                if fence_char is None:
                    # Opener: info strings (e.g. ```python) are allowed after the marker.
                    fence_char, fence_min_len = char, length
                    continue
                # Closer: same type, >= length, and NO non-whitespace after the marker.
                # A line like "```python" inside a fence is body content, not a closer.
                rest = line[fm.end():]
                if char == fence_char and length >= fence_min_len and not rest.strip():
                    fence_char, fence_min_len = None, 0
                    continue
                # else: different type or has trailing text — treat as fence body
        if fence_char is not None:
            continue
        # Multi-line HTML comment: skip until closing -->.
        if in_ml_comment:
            if "-->" in line:
                # After the closer, strip any COMPLETE inline comments from the
                # remainder (e.g. "--> <!-- note -->") before testing for an unclosed
                # opener. Without this, "--> <!-- note -->" sets in_ml_comment=True
                # even though the comment is fully closed on the same line.
                remainder = line[line.index("-->") + 3:]
                remainder_clean = _HTML_COMMENT_RE.sub("", remainder)
                in_ml_comment = "<!--" in remainder_clean
            continue
        # Stop at the first section heading — body examples live after ## headings.
        if _SECTION_HEADING_RE.match(line):
            break
        # Strip single-line HTML comments. If an unclosed <!-- remains, the rest of
        # this line and all subsequent lines until --> are inside a comment.
        clean = _HTML_COMMENT_RE.sub("", line)
        if "<!--" in clean:
            clean = clean[:clean.index("<!--")]
            in_ml_comment = True
        # Anchor to the canonical list-item field form: "- **Status:** ..."
        # A prose line containing **Status:** (example, comment) is not the field.
        if not clean.startswith("- **Status:**"):
            continue
        # Strip annotations before scanning — a spaced arrow in "(root → leaf)"
        # must never be read as a transition arrow.
        m = _STATUS_FIELD_RE.search(clean)
        if not m:
            continue
        content = m.group(1).strip()
        if "→" in content:
            # Transition form: "Draft → Approved → Shipped" (any arrow spacing).
            # A trailing bare arrow ("Draft → Approved →") has no final segment;
            # reject it explicitly so the preceding segment is never backtracked to.
            if content.rstrip().endswith("→"):
                return None, None
            # Take the LAST segment; if not a known status, return None — no backtrack.
            segments = _TRANSITION_ARROW_RE.findall(content)
            if segments:
                last = segments[-1]
                return (last, line) if last in VALID_STATUSES else (None, None)
        else:
            word = content.split()[0] if content.split() else ""
            return (word, line) if word in VALID_STATUSES else (None, None)
    return None, None


def extract_spec_status(spec_path: Path) -> str | None:
    """Read spec.md and return the Status vocabulary word, or None if absent/unreadable."""
    if not spec_path.exists():
        return None
    try:
        text = spec_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    status, _ = _parse_spec_status(text)
    return status


def extract_spec_status_with_fingerprint(spec_path: Path) -> tuple[str | None, str | None]:
    """Like extract_spec_status but also returns a SHA-256 fingerprint of the raw status line.

    Returns (status_token, fingerprint) where fingerprint is the SHA-256 hexdigest of
    the UTF-8 bytes of the exact status-field line used to derive the token.
    Returns (None, None) when the status is unreadable or invalid.
    """
    if not spec_path.exists():
        return None, None
    try:
        text = spec_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, None
    status, raw_line = _parse_spec_status(text)
    if status is None or raw_line is None:
        return None, None
    return status, hashlib.sha256(raw_line.encode("utf-8")).hexdigest()


# ── DAG / needs resolution ────────────────────────────────────────────────────

_CROSS_INI_RE = re.compile(r'^(ini-[^:]+):work:(.+)$')


def is_need_satisfied(
    need: str,
    ini_slug: str,
    all_initiatives: list[Initiative],
    autonomous_dispatch: bool = False,
) -> bool:
    """Return True if `need` is satisfied given the current workspace state.

    Implements the needs-resolution table from SKILL.md §2.

    When autonomous_dispatch=False (default): human-session semantics — absent targets
    are treated as satisfied (the human knows the workspace state).
    When autonomous_dispatch=True: conservative semantics — absent targets are unsatisfied
    so the control plane does not dispatch work before prerequisites are explicitly planned.
    See SKILL.md §2 for the shape:/research: asymmetry between the two modes.

    Known gaps (KD-01, KD-03):
      - `backlog:<slug>` prefix: not in SKILL.md table; treated as unsatisfied here.
      - Missing targets: silently treated as unsatisfied (no warning).
    """
    # Cross-initiative: "ini-002:work:spec/..."
    m = _CROSS_INI_RE.match(need)
    if m:
        target_ini_slug, path = m.group(1), m.group(2)
        for ini in all_initiatives:
            if ini.slug == target_ini_slug:
                return any(e.path == path for e in ini.work.shipped)
        return False  # Target initiative not found

    # Local work: "work:<path>" — satisfied only by shipped (schema.md:113).
    # An entry in work.active is "in-progress" but NOT yet satisfied;
    # its dependents remain blocked until the path reaches work.shipped.
    if need.startswith("work:"):
        path = need[len("work:"):]
        for ini in all_initiatives:
            if ini.slug == ini_slug:
                return any(e.path == path for e in ini.work.shipped)
        return False

    # Shape: "shape:<slug>" — SKILL.md §2.
    # Human-managed mode: satisfied when no longer in active (graduated from shaping).
    # Absent from active = treated as done regardless of backlog.
    # Autonomous mode: absent from both active AND backlog → never planned → unsatisfied.
    # Absent from active but present in backlog → planned, not yet started → satisfied.
    # (Intentional asymmetry with research: — see SKILL.md §2.)
    if need.startswith("shape:"):
        slug = need[len("shape:"):]
        for ini in all_initiatives:
            if ini.slug == ini_slug:
                active_slugs = {e.slug for e in ini.shaping.active}
                if autonomous_dispatch:
                    backlog_slugs = {e.slug for e in ini.shaping.backlog}
                    if slug not in active_slugs and slug not in backlog_slugs:
                        return False  # never planned
                return slug not in active_slugs
        return True  # Initiative not found → assume satisfied

    # Research: "research:<slug>" — SKILL.md §2.
    # Human-managed mode: satisfied when NOT in shaping backlog as type="research".
    # Absent from backlog = treated as satisfied (research completed or never needed).
    # Only entries explicitly typed "research" can block a research: need.
    # Note: autonomous_dispatch does NOT change research semantics — absence means completed.
    if need.startswith("research:"):
        slug = need[len("research:"):]
        for ini in all_initiatives:
            if ini.slug == ini_slug:
                research_slugs = {
                    e.slug for e in ini.shaping.backlog if e.entry_type == "research"
                }
                return slug not in research_slugs
        return True

    # Brief: "brief:<path>" — satisfied if in brief_queue.ready or executing
    if need.startswith("brief:"):
        path = need[len("brief:"):]
        for ini in all_initiatives:
            if ini.slug == ini_slug and ini.brief_queue is not None:
                bq = ini.brief_queue
                if bq.executing == path:
                    return True
                return path in bq.ready
        return False

    # `backlog:<slug>` — KD-01: not in SKILL.md table; treated conservatively as unsatisfied
    if need.startswith("backlog:"):
        return False

    # `strategy:<slug>` — KD-08: documented in workspace-toml-deps.md but absent from
    # SKILL.md needs-resolution table; treated conservatively as unsatisfied
    if need.startswith("strategy:"):
        return False

    # Unknown prefix — conservatively unsatisfied
    return False


def classify_entries(
    ini: Initiative,
    all_initiatives: list[Initiative],
    autonomous_dispatch: bool = False,
) -> list[EntryClassification]:
    """Classify queue entries as ready or blocked.

    Entries already in active or shipped are excluded — they are not surfaced
    as ready/blocked in the DAG output (SKILL.md §2: "unconditionally ready
    unless already in active or shipped").
    """
    active_paths = {e.path for e in ini.work.active}
    shipped_paths = {e.path for e in ini.work.shipped}
    results: list[EntryClassification] = []
    for entry in ini.work.queue:
        if entry.path in active_paths or entry.path in shipped_paths:
            continue  # already running or done — not classified
        if not entry.needs:
            results.append(EntryClassification(
                entry=entry, ini_slug=ini.slug, is_ready=True, blocking_needs=[],
            ))
        else:
            blocking = [
                n for n in entry.needs
                if not is_need_satisfied(n, ini.slug, all_initiatives, autonomous_dispatch)
            ]
            results.append(EntryClassification(
                entry=entry,
                ini_slug=ini.slug,
                is_ready=len(blocking) == 0,
                blocking_needs=blocking,
            ))
    return results


def classify_shaping_entries(
    ini: Initiative,
    all_initiatives: list[Initiative],
    autonomous_dispatch: bool = False,
) -> list[ShapingClassification]:
    """Classify shaping queue entries for an active initiative.

    shaping_queue.active — non-signals are ready; signals are active context.
    shaping_queue.backlog — classified by needs (same resolution as work entries).
    """
    results: list[ShapingClassification] = []

    # Active entries take precedence; deduplicate on (slug, type) so a shape:X active
    # entry does not suppress a research:X backlog entry — they are distinct items.
    active_typed = {(e.slug, e.entry_type) for e in ini.shaping.active}

    for entry in ini.shaping.active:
        is_sig = entry.entry_type == "signal"
        results.append(ShapingClassification(
            entry=entry,
            ini_slug=ini.slug,
            is_signal=is_sig,
            is_ready=not is_sig,
            blocking_needs=[],
        ))

    for entry in ini.shaping.backlog:
        if (entry.slug, entry.entry_type) in active_typed:
            continue  # Same slug + same type: active takes precedence
        is_sig = entry.entry_type == "signal"
        if is_sig:
            results.append(ShapingClassification(
                entry=entry, ini_slug=ini.slug,
                is_signal=True, is_ready=False, blocking_needs=[],
            ))
        elif not entry.needs:
            results.append(ShapingClassification(
                entry=entry, ini_slug=ini.slug,
                is_signal=False, is_ready=True, blocking_needs=[],
            ))
        else:
            blocking = [
                n for n in entry.needs
                if not is_need_satisfied(n, ini.slug, all_initiatives, autonomous_dispatch)
            ]
            results.append(ShapingClassification(
                entry=entry,
                ini_slug=ini.slug,
                is_signal=False,
                is_ready=len(blocking) == 0,
                blocking_needs=blocking,
            ))

    return results


# ── Reconciliation ────────────────────────────────────────────────────────────

def _run_type1_scan(
    root: Path,
    all_tracked: set[str],
) -> tuple[list[ReconciliationFinding], int]:
    """Type 1: Forward scan — untracked live specs. Returns (findings, files_read).

    Two callers: run_reconciliation and analyze. Never called by analyze_bounded.
    """
    findings: list[ReconciliationFinding] = []
    files_read = 0
    specs_dir = root / "docs" / "specs"

    # Recurse the full specs tree so nested specs (e.g. docs/specs/group/live/)
    # are discovered; slug is the parent path relative to specs_dir.
    # os.walk(followlinks=False) prevents escaping the repo via symlinked dirs
    # found DURING traversal (rglob follows symlinks on Python 3.11/3.12).
    # The root-confinement check guards against docs/specs or docs/ itself being
    # a symlink — followlinks=False does not apply to the initial top directory.
    _specs_root_safe = False
    if specs_dir.exists():
        try:
            specs_dir.resolve().relative_to(root.resolve())
            _specs_root_safe = True
        except ValueError:
            pass  # docs/specs resolved outside repo root (symlink) — skip walk
    if _specs_root_safe:
        _specs_root_resolved = specs_dir.resolve()
        _visited: set[Path] = set()
        for dirpath, dirnames, filenames in os.walk(str(specs_dir), followlinks=False):
            # Guard: skip this directory if already visited (in-root junction to a
            # previously-scanned sibling). Must run before processing filenames so a
            # junction alias doesn't produce duplicate Type 1 findings for the
            # real directory's spec.md. dirnames.clear() prevents further descent.
            # RuntimeError guards against circular symlinks on Python 3.11/3.12.
            try:
                _current_resolved = Path(dirpath).resolve()
            except (OSError, RuntimeError):
                dirnames.clear()
                continue
            if _current_resolved in _visited:
                dirnames.clear()
                continue
            _visited.add(_current_resolved)
            # Prune subdirs that escape the specs root OR have already been visited.
            # is_relative_to guards against junctions pointing outside the root;
            # the visited set guards against in-root cycles (a junction whose
            # resolved target is an ancestor within the tree).
            # RuntimeError guards against circular symlinks during resolve().
            safe: list[str] = []
            for d in dirnames:
                try:
                    resolved = (Path(dirpath) / d).resolve()
                    if (
                        resolved.is_relative_to(_specs_root_resolved)
                        and resolved not in _visited
                    ):
                        safe.append(d)
                except (OSError, ValueError, RuntimeError):
                    pass
            dirnames[:] = sorted(safe)  # deterministic traversal order
            if "spec.md" not in filenames:
                continue
            spec_file = Path(dirpath) / "spec.md"
            if spec_file.is_symlink():
                continue
            # Derive the slug from the resolved path so NTFS junction aliases
            # that sort before their real target still produce the canonical slug.
            try:
                rel = _current_resolved.relative_to(_specs_root_resolved)
            except ValueError:
                continue
            slug = rel.as_posix()
            slug_path = Path(slug)
            if slug_path.is_absolute() or ".." in slug_path.parts:
                continue
            files_read += 1
            status = extract_spec_status(spec_file)
            if status not in ("Approved", "Implementing"):
                continue
            legacy_path = f"spec/{slug}"
            target_path = f"docs/specs/{slug}/spec.md"
            if not {legacy_path, target_path}.intersection(all_tracked):
                findings.append(ReconciliationFinding(
                    finding_type=1,
                    spec_path=legacy_path,
                    spec_status=status or "",
                    ini_slug="",
                    list_name="",
                ))
    return findings, files_read


def _run_type23_scan(
    root: Path,
    initiatives: list[Initiative],
) -> tuple[list[ReconciliationFinding], int]:
    """Type 2 + 3: Backward and shipped scans. Returns (findings, files_read).

    Three callers: run_reconciliation, analyze, and analyze_bounded.
    All declared-spec path resolution goes through _safe_spec_path() — no
    confinement bypass in bounded mode.
    """
    findings: list[ReconciliationFinding] = []
    files_read = 0

    # ── Type 2: Backward scan — stale queue/active entries ────────────────────
    for ini in initiatives:
        for list_name, entries in [("queue", ini.work.queue), ("active", ini.work.active)]:
            for entry in entries:
                spec_file = _safe_spec_path(root, entry.slug)
                if spec_file is None or not spec_file.exists():
                    continue
                files_read += 1
                status = extract_spec_status(spec_file)
                if status in ("Shipped", "Archived"):
                    findings.append(ReconciliationFinding(
                        finding_type=2,
                        spec_path=entry.path,
                        spec_status=status or "",
                        ini_slug=ini.slug,
                        list_name=list_name,
                    ))

    # ── Type 3: Shipped scan — prematurely shipped entries ────────────────────
    for ini in initiatives:
        for entry in ini.work.shipped:
            spec_file = _safe_spec_path(root, entry.slug)
            if spec_file is None or not spec_file.exists():
                continue
            files_read += 1
            status = extract_spec_status(spec_file)
            if status in ("Approved", "Implementing"):
                findings.append(ReconciliationFinding(
                    finding_type=3,
                    spec_path=entry.path,
                    spec_status=status or "",
                    ini_slug=ini.slug,
                    list_name="shipped",
                ))

    return findings, files_read


def run_reconciliation(
    root: Path,
    initiatives: list[Initiative],
) -> tuple[list[ReconciliationFinding], int]:
    """Run all three reconciliation scan types. Returns (findings, files_read)."""
    all_tracked: set[str] = set()
    for ini in initiatives:
        for e in ini.work.queue + ini.work.active + ini.work.shipped:
            all_tracked.add(e.path)

    type1_findings, type1_files = _run_type1_scan(root, all_tracked)
    type23_findings, type23_files = _run_type23_scan(root, initiatives)
    return type1_findings + type23_findings, type1_files + type23_files


# ── Main analysis entry point ─────────────────────────────────────────────────

def analyze(root: Path, *, workspace_bytes: bytes | None = None) -> WorkspaceStatusResult:
    """Run full workspace-status analysis from a repo root.

    Reads workspace.toml, extracts initiatives, classifies queue entries,
    and runs the three reconciliation scans.

    Only active initiatives contribute to ready/blocked classifications.
    All initiatives (including paused/closed) participate in reconciliation
    scans (behavior per SKILL.md which does not filter by status in scans).

    workspace_bytes: when provided, parse from these bytes instead of re-reading
    from disk. Callers that fingerprint workspace.toml before calling analyze()
    should pass the same bytes to eliminate the TOCTOU window.
    """
    t0 = time.monotonic()

    workspace_path = root / "workspace.toml"
    if workspace_bytes is not None:
        workspace = tomllib.loads(workspace_bytes.decode("utf-8"))
    else:
        workspace = parse_workspace(workspace_path)
    initiatives = extract_initiatives(workspace)

    all_classifications: list[EntryClassification] = []
    all_shaping: list[ShapingClassification] = []
    for ini in initiatives:
        if ini.status not in ("active",):
            continue   # Only active initiatives for ready/blocked and shaping
        all_classifications.extend(classify_entries(ini, initiatives))
        all_shaping.extend(classify_shaping_entries(ini, initiatives))

    # Build all_tracked for the Type 1 scan
    all_tracked: set[str] = set()
    for ini in initiatives:
        for e in ini.work.queue + ini.work.active + ini.work.shipped:
            all_tracked.add(e.path)

    # Call helpers directly (not via run_reconciliation) to obtain split file counts
    type1_findings, type1_files = _run_type1_scan(root, all_tracked)
    type23_findings, type23_files = _run_type23_scan(root, initiatives)
    reconciliation = type1_findings + type23_findings

    top_level_backlog = extract_top_level_backlog(workspace)
    repo_backlog = extract_repo_backlog(workspace)

    elapsed = time.monotonic() - t0
    return WorkspaceStatusResult(
        initiatives=initiatives,
        classifications=all_classifications,
        shaping_classifications=all_shaping,
        reconciliation=reconciliation,
        elapsed_s=elapsed,
        top_level_backlog=top_level_backlog,
        repo_backlog=repo_backlog,
        global_scan_performed=True,
        declared_spec_files_read=type23_files,
        global_scan_files_read=type1_files,
    )


def analyze_bounded(root: Path, autonomous_dispatch: bool = False) -> WorkspaceStatusResult:
    """Run bounded workspace-status analysis (Type 2+3 only; no global spec walk).

    Used by 'status' and 'explain' subcommands. Structurally guarantees no Type 1
    scan: calls _run_type23_scan only, never _run_type1_scan. Path confinement is
    preserved — _run_type23_scan routes all path resolution through _safe_spec_path().

    autonomous_dispatch=True applies conservative needs-resolution semantics (see
    is_need_satisfied and SKILL.md §2). workspace_status() passes autonomous_dispatch=True.
    """
    t0 = time.monotonic()

    workspace_path = root / "workspace.toml"
    workspace = parse_workspace(workspace_path)
    initiatives = extract_initiatives(workspace)

    all_classifications: list[EntryClassification] = []
    all_shaping: list[ShapingClassification] = []
    for ini in initiatives:
        if ini.status not in ("active",):
            continue
        all_classifications.extend(classify_entries(ini, initiatives, autonomous_dispatch))
        all_shaping.extend(classify_shaping_entries(ini, initiatives, autonomous_dispatch))

    type23_findings, declared_files = _run_type23_scan(root, initiatives)
    top_level_backlog = extract_top_level_backlog(workspace)
    repo_backlog = extract_repo_backlog(workspace)

    elapsed = time.monotonic() - t0
    return WorkspaceStatusResult(
        initiatives=initiatives,
        classifications=all_classifications,
        shaping_classifications=all_shaping,
        reconciliation=type23_findings,
        elapsed_s=elapsed,
        top_level_backlog=top_level_backlog,
        repo_backlog=repo_backlog,
        global_scan_performed=False,
        declared_spec_files_read=declared_files,
        global_scan_files_read=0,
    )


def explain_item(result: WorkspaceStatusResult, selector: str) -> dict:
    """Focused projection of one work-queue item from a bounded status result.

    Lookup is restricted to active initiatives' work queues (queue/active/shipped).
    Shaping entries are not searched. No file I/O; selector is never used as a
    filesystem path component.

    Returns one of:
      {"selector_status": "matched", "explained_item": {...}}
      {"selector_status": "not_found"}
      {"selector_status": "ambiguous", "matches": [...]}
    """
    slug = normalize_for_shaping_guard(selector)
    target_path = f"spec/{slug}"

    # Collect matching active initiatives (one entry per initiative)
    matches: list[dict] = []
    for ini in result.initiatives:
        if ini.status != "active":
            continue
        found_in: list[str] = []
        for list_name, entries in [
            ("active", ini.work.active),
            ("shipped", ini.work.shipped),
            ("queue", ini.work.queue),
        ]:
            if any(e.path == target_path for e in entries):
                found_in.append(list_name)
        if found_in:
            matches.append({"ini_slug": ini.slug, "found_in": found_in})

    if len(matches) == 0:
        return {"selector_status": "not_found"}

    if len(matches) > 1:
        return {
            "selector_status": "ambiguous",
            "matches": [{"path": target_path, "ini_slug": m["ini_slug"]} for m in matches],
        }

    # Exactly one active initiative matched
    match = matches[0]
    ini_slug = match["ini_slug"]
    found_in = match["found_in"]
    ini = next(i for i in result.initiatives if i.slug == ini_slug)

    # Resolve list and classification: active > shipped > queue precedence
    if "active" in found_in:
        item_list = "active"
        classification = "active"
        entry = next(e for e in ini.work.active if e.path == target_path)
        blocking_needs: list[str] = []
        dependencies: list[dict] = []
        sole_blocker = f"work:{target_path}"
        downstream_unblocked: list[str] = [
            c.entry.path
            for c in result.blocked
            if c.ini_slug == ini_slug and c.blocking_needs == [sole_blocker]
        ]
    elif "shipped" in found_in:
        item_list = "shipped"
        classification = "shipped"
        entry = next(e for e in ini.work.shipped if e.path == target_path)
        blocking_needs = []
        dependencies = []
        downstream_unblocked = []
    else:
        item_list = "queue"
        entry = next(e for e in ini.work.queue if e.path == target_path)
        cls = next(
            (
                c for c in result.classifications
                if c.entry.path == target_path and c.ini_slug == ini_slug
            ),
            None,
        )
        if cls is not None:
            classification = "ready" if cls.is_ready else "blocked"
            blocking_needs = cls.blocking_needs
        else:
            classification = "ready"
            blocking_needs = []
        dependencies = [
            {"need": need, "satisfied": need not in blocking_needs}
            for need in entry.needs
        ]
        sole_blocker = f"work:{target_path}"
        downstream_unblocked = [
            c.entry.path
            for c in result.blocked
            if c.ini_slug == ini_slug and c.blocking_needs == [sole_blocker]
        ]

    return {
        "selector_status": "matched",
        "explained_item": {
            "path": target_path,
            "slug": slug,
            "ini_slug": ini_slug,
            "list": item_list,
            "classification": classification,
            "blocking_needs": blocking_needs,
            "dependencies": dependencies,
            "downstream_unblocked": downstream_unblocked,
        },
    }


# ── Argless work-loop resume helper ──────────────────────────────────────────

def get_active_specs(initiatives: list[Initiative]) -> list[tuple[str, str]]:
    """Return (ini_slug, spec_path) pairs for all active specs across active initiatives.

    Used by work-loop argless resume (3-branch logic):
      - len == 0: no active spec; point to workspace-status
      - len == 1: exactly one; begin on it
      - len >= 2: list all; ask user to pick
    """
    result: list[tuple[str, str]] = []
    for ini in initiatives:
        if ini.status != "active":
            continue
        for entry in ini.work.active:
            result.append((ini.slug, entry.path))
    return result


# ── work-loop shaping-item guard helper ──────────────────────────────────────

# Explicitly recognised shaping types. Only entries with one of these types
# in [backlog].open are treated as shaping work by check_shaping_guard.
# Untyped entries (ordinary build-backlog items) are excluded.
_SHAPING_TYPES: frozenset[str] = frozenset(
    {"shape", "research", "strategy", "signal", "design"}
)
_SHAPING_ARTIFACT_KINDS: frozenset[str] = frozenset(
    {"intent", "research", "design", "brief"}
)


def extract_repo_backlog(workspace: dict) -> list[RepoBacklogEntry]:
    """Project every supported [backlog].open inline object for display."""
    backlog_section = workspace.get("backlog", {})
    if not isinstance(backlog_section, dict):
        return []

    entries: list[RepoBacklogEntry] = []
    for raw in backlog_section.get("open", []):
        if not isinstance(raw, dict):
            continue

        if all(key in raw for key in ("path", "kind", "source", "summary", "needs")):
            kind = raw["kind"]
            entries.append(RepoBacklogEntry(
                path=raw["path"],
                kind=kind,
                source=raw["source"],
                summary=raw["summary"],
                needs=list(raw["needs"]),
                room="shape" if kind in _SHAPING_ARTIFACT_KINDS else "build",
            ))
            continue

        if "slug" not in raw:
            continue
        entry_type = raw.get("type")
        entries.append(RepoBacklogEntry(
            slug=raw["slug"],
            room="shape" if entry_type is not None else "build",
            entry_type=entry_type,
            needs=list(_parse_needs(raw.get("needs"))),
            source=raw.get("source"),
            summary=raw.get("summary"),
        ))
    return entries


def extract_top_level_backlog(workspace: dict) -> list[ShapingEntry]:
    """Extract typed shaping entries from [backlog].open.

    work-loop's shaping-item guard (SKILL.md §0 step 2) checks this list in addition
    to per-initiative shaping queues. Only entries with an explicit shaping type
    (shape | research | strategy | signal | design) are returned; untyped dict entries
    and ordinary build-backlog items without a type field are excluded.
    """
    backlog_section = workspace.get("backlog", {})
    if not isinstance(backlog_section, dict):
        return []
    entries: list[ShapingEntry] = []
    for e in backlog_section.get("open", []):
        entry = _parse_supported_shaping_entry("backlog.open", e)
        if entry is not None and entry.entry_type in _SHAPING_TYPES:
            entries.append(entry)
    return entries


_SHAPING_TYPE_TO_SKILL: dict[str, str] = {
    "shape":    "frame-intent",
    "research": "desk-research-project-start",
    "strategy": "frame-situation",
    "design":   "experience-status",
    "signal":   "(signal — no action)",
}


def check_shaping_guard(
    spec_slug: str,
    initiatives: list[Initiative],
    top_level_backlog: list[ShapingEntry] | None = None,
) -> str | None:
    """Return the routing skill if spec_slug is in a shaping queue; None otherwise.

    work-loop checks this guard at Step 0 (SKILL.md §0 step 2). Checks:
      - active initiatives' [shaping_queue].active and .backlog
      - top-level [backlog].open typed entries (pass via extract_top_level_backlog)

    Only active initiatives are checked; paused/closed/complete initiatives are skipped.
    If the spec is a shaping item, work-loop stops and suggests the appropriate skill.
    """
    for ini in initiatives:
        if ini.status != "active":
            continue
        for entry in ini.shaping.active + ini.shaping.backlog:
            if entry.slug == spec_slug:
                return _SHAPING_TYPE_TO_SKILL.get(entry.entry_type, "frame-intent")
    for entry in (top_level_backlog or []):
        if entry.slug == spec_slug:
            return _SHAPING_TYPE_TO_SKILL.get(entry.entry_type, "frame-intent")
    return None


def normalize_for_shaping_guard(raw_path: str) -> str:
    """Normalize a spec path to slug form for the shaping-item guard.

    Per work-loop SKILL.md §0 step 2: "Derive slug (strip docs/specs/ prefix + trailing /)."

    Accepted input forms:
      'docs/specs/example/'  → 'example'
      'docs/specs/example'   → 'example'
      'spec/example'         → 'example'
      'example'              → 'example'  (already normalized)
    """
    s = raw_path.rstrip("/")
    if s.startswith("docs/specs/"):
        return s[len("docs/specs/"):]
    if s.startswith("spec/"):
        return s[len("spec/"):]
    return s


# ── work-loop Step 0 stale-queue check ───────────────────────────────────────

def collect_work_loop_stale_warnings(
    root: Path,
    initiatives: list[Initiative],
) -> list[WorkLoopStaleWarning]:
    """Characterize work-loop Step 0 stale-queue check (SKILL.md §0 step 1).

    Checks active initiatives' queue and active entries. Emits a warn-only
    WorkLoopStaleWarning when the entry's spec.md Status is 'Shipped'.

    Differs from workspace-status Type 2 reconciliation:
      - Only active initiatives (paused/closed/complete skipped)
      - Only Shipped triggers a warning; Archived, Approved, Implementing do not
      - When a path appears in both queue and active, emits ONE warning naming both
      - Does not offer or perform cleanup (warn-only)
      - Missing spec.md → skipped without error
    """
    warnings: list[WorkLoopStaleWarning] = []
    for ini in initiatives:
        if ini.status != "active":
            continue
        # Collect all paths with their source lists; a path may appear in both
        path_sources: dict[str, list[str]] = {}
        for list_name, entries in [("queue", ini.work.queue), ("active", ini.work.active)]:
            for entry in entries:
                if entry.path not in path_sources:
                    path_sources[entry.path] = []
                path_sources[entry.path].append(list_name)

        for path, sources in path_sources.items():
            slug = _spec_slug_from_workspace_path(path)
            spec_file = _safe_spec_path(root, slug)
            if spec_file is None or not spec_file.exists():
                continue
            status = extract_spec_status(spec_file)
            if status != "Shipped":
                continue  # Only Shipped warns; Archived/Approved/Implementing skip
            warnings.append(WorkLoopStaleWarning(
                spec_path=path,
                ini_slug=ini.slug,
                source_lists=sources,
            ))
    return warnings


# ── workspace-status Type 2 cleanup compatibility projection ─────────────────
#
# work-loop no longer writes to workspace.toml
# active/shipped arrays. Its finish checklist only sets spec.md Status: Shipped.
# Repair-plan/repair-apply exclusively own stale queue writes. This function
# keeps the older status JSON field informative without emitting mutation data.

_TYPE2_VALID_STATUSES: frozenset[str] = frozenset({"Shipped", "Archived"})
_TYPE2_VALID_SOURCES: frozenset[str] = frozenset({"active", "queue"})


def _repair_entry_eligibility(
    workspace_path: Path,
    ini_slug: str,
    spec_path: str,
    op_type: str,
) -> tuple[bool, str | None]:
    try:
        workspace = parse_workspace(workspace_path)
    except Exception:
        return False, "type2-queue-canonical-blocked"
    work = workspace.get(ini_slug, {}).get("work", {})
    raw_entries = work.get("queue", [])
    if not isinstance(raw_entries, list):
        return False, "type2-queue-canonical-blocked"
    for entry in raw_entries:
        entry_path = entry.get("path", "") if isinstance(entry, dict) else entry
        if entry_path != spec_path:
            continue
        if not isinstance(entry, dict):
            if op_type == "queue-remove":
                if not _is_legacy_spec_path(spec_path):
                    return False, "type2-queue-canonical-blocked"
                alias = f"docs/specs/{spec_path.removeprefix('spec/')}/spec.md"
                canonical = run_canonical_reconciliation(workspace, workspace_path.parent)
                if any(finding.code == "invalid_workspace" for finding in canonical.findings):
                    return False, "type2-queue-canonical-blocked"
                lifecycle_lists: list[tuple[str, list[object]]] = []
                backlog = workspace.get("backlog", {})
                if not isinstance(backlog, dict):
                    return False, "type2-queue-canonical-blocked"
                for list_name in _TOP_LEVEL_ENTRY_COLLECTIONS["backlog"]:
                    entries = backlog.get(list_name, [])
                    if not isinstance(entries, list):
                        return False, "type2-queue-canonical-blocked"
                    lifecycle_lists.append((f"backlog.{list_name}", entries))
                for raw_ini_slug, section in workspace.items():
                    if _CANONICAL_INITIATIVE_RE.fullmatch(raw_ini_slug) is None:
                        continue
                    if not isinstance(section, dict):
                        return False, "type2-queue-canonical-blocked"
                    for section_name, list_names in _INITIATIVE_ENTRY_COLLECTIONS.items():
                        subsection = section.get(section_name, {})
                        if not isinstance(subsection, dict):
                            return False, "type2-queue-canonical-blocked"
                        for list_name in list_names:
                            entries = subsection.get(list_name, [])
                            if not isinstance(entries, list):
                                return False, "type2-queue-canonical-blocked"
                            lifecycle_lists.append(
                                (f"{section_name}.{list_name}", entries)
                            )
                aliases = {spec_path, alias}
                matches = 0
                for collection, entries in lifecycle_lists:
                    for other in entries:
                        other_path = (
                            other.get("path", "") if isinstance(other, dict) else other
                        )
                        if other_path in aliases:
                            matches += 1
                            continue
                        legacy = _accepted_legacy_entry(collection, other)
                        if (
                            legacy is not None
                            and _legacy_canonical_alias(legacy) == alias
                        ):
                            matches += 1
                if matches == 1:
                    return True, None
                return False, "type2-queue-canonical-blocked"
            return False, "type2-queue-structured-entry-required"
        parsed, findings = parse_workspace_entry(entry)
        if findings or parsed is None or parsed.kind != "spec":
            return False, "type2-queue-canonical-blocked"
        canonical = run_canonical_reconciliation(workspace, workspace_path.parent)
        eval_findings: list[RoutingFinding] = []
        for evaluation in canonical.evaluations:
            if (
                evaluation.ini_slug == ini_slug
                and evaluation.collection == "work.queue"
                and evaluation.entry.path == spec_path
            ):
                eval_findings.extend(evaluation.findings)
                break
        else:
            return False, "type2-queue-canonical-blocked"
        result_findings = [finding for finding in canonical.findings if finding.path == spec_path]
        blocking_codes = {
            finding.code for finding in [*eval_findings, *result_findings]
        }
        if blocking_codes - {"impossible_transition", "unapproved_spec"}:
            return False, "type2-queue-canonical-blocked"
        return True, None
    return False, "type2-queue-canonical-blocked"


def compute_type2_cleanup(
    ini_slug: str,
    source_list: str,
    spec_path: str,
    spec_status: str,
) -> dict:
    """Describe a non-authoritative Type 2 finding for repair-plan routing.

    Caller must supply the exact fields from a Type 2 ReconciliationFinding:
      ini_slug   — the initiative slug (e.g. "ini-001")
      source_list — "active" | "queue" (the list the finding came from)
      spec_path  — the spec path (e.g. "spec/my-feature")
      spec_status — "Shipped" | "Archived" (from the spec.md Status field)

    Raises ValueError for spec_status outside {"Shipped", "Archived"} or
    source_list outside {"active", "queue"} — these signal a caller bug
    (Type 1 / Type 3 findings should never reach this function).

    This compatibility projection never authorizes a write. The CLI's
    repair-plan/repair-apply flow is the only workspace.toml writer because it
    preserves structured entries and revalidates canonical eligibility.
    """
    if spec_status not in _TYPE2_VALID_STATUSES:
        raise ValueError(
            f"compute_type2_cleanup: spec_status must be 'Shipped' or 'Archived', "
            f"got {spec_status!r}. Type 1 / Type 3 findings are not eligible."
        )
    if source_list not in _TYPE2_VALID_SOURCES:
        raise ValueError(
            f"compute_type2_cleanup: source_list must be 'active' or 'queue', "
            f"got {source_list!r}."
        )
    return {
        "ini_slug": ini_slug,
        "source_list": source_list,
        "path": spec_path,
        "spec_status": spec_status,
        "authoritative": False,
        "next_action": "repair-plan",
    }


# ── Repair planning ───────────────────────────────────────────────────────────


def compute_repair_plan(
    result: WorkspaceStatusResult,
    workspace_path: Path,
    workspace_fingerprint: str | None = None,
) -> RepairPlan:
    """Build a deterministic, read-only repair plan from a full reconciliation result.

    Only Type 2 findings from work.queue with Shipped or Archived status become
    automatic_operations. Paths appearing more than once in the same initiative's
    queue (duplicates) and all other findings become manual_findings.

    workspace_fingerprint: pre-computed SHA-256 of workspace.toml bytes, captured
    before analyze() is called. When provided, binds the plan to that snapshot and
    eliminates the TOCTOU window between analysis and a separate read_bytes() call.
    """
    automatic: list[RepairOperation] = []
    manual: list[ManualFinding] = []

    # Duplicate detection: count (ini_slug, spec_path) pairs across Type 2 queue findings
    queue_counts: dict[tuple[str, str], int] = {}
    for f in result.type2:
        if f.list_name == "queue":
            key = (f.ini_slug, f.spec_path)
            queue_counts[key] = queue_counts.get(key, 0) + 1
    duplicate_keys = {k for k, n in queue_counts.items() if n > 1}

    for f in result.type1:
        fid = f"type1:{f.ini_slug}:{f.list_name}:{f.spec_path}"
        manual.append(ManualFinding(
            finding_type=1, spec_path=f.spec_path, spec_status=f.spec_status,
            ini_slug=f.ini_slug, list_name=f.list_name, reason="type1-untracked",
            finding_id=fid,
        ))

    for f in result.type2:
        if f.list_name == "queue" and (f.ini_slug, f.spec_path) in duplicate_keys:
            fid = f"type2:{f.ini_slug}:{f.list_name}:{f.spec_path}"
            manual.append(ManualFinding(
                finding_type=2, spec_path=f.spec_path, spec_status=f.spec_status,
                ini_slug=f.ini_slug, list_name=f.list_name, reason="type2-queue-duplicate",
                finding_id=fid,
            ))
        elif f.list_name == "queue" and f.spec_status in ("Shipped", "Archived"):
            op_type = "queue-to-shipped" if f.spec_status == "Shipped" else "queue-remove"
            fid = f"type2:{f.ini_slug}:{f.list_name}:{f.spec_path}"
            eligible, ineligible_reason = _repair_entry_eligibility(
                workspace_path,
                f.ini_slug,
                f.spec_path,
                op_type,
            )
            if not eligible:
                manual.append(ManualFinding(
                    finding_type=2, spec_path=f.spec_path, spec_status=f.spec_status,
                    ini_slug=f.ini_slug, list_name=f.list_name,
                    reason=ineligible_reason or "type2-queue-canonical-blocked",
                    finding_id=fid,
                ))
                continue
            slug = _spec_slug_from_workspace_path(f.spec_path)
            spec_file = _safe_spec_path(workspace_path.parent, slug)
            live_status, status_fp = (
                extract_spec_status_with_fingerprint(spec_file)
                if spec_file is not None else (None, None)
            )
            if status_fp is None or live_status != f.spec_status:
                # Spec unreadable, or its status changed between the scan and this
                # read (e.g. Shipped → Archived). An operation whose status and
                # fingerprint describe different snapshots would be skipped by
                # repair-apply and would block other valid operations. Route to manual.
                manual.append(ManualFinding(
                    finding_type=2, spec_path=f.spec_path, spec_status=f.spec_status,
                    ini_slug=f.ini_slug, list_name=f.list_name,
                    reason="type2-queue-spec-status-unreadable",
                    finding_id=fid,
                ))
            else:
                op_canon = json.dumps({
                    "finding_id": fid, "ini_slug": f.ini_slug,
                    "operation_type": op_type, "spec_path": f.spec_path,
                    "spec_status": live_status,
                    "spec_status_fingerprint": status_fp,
                }, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
                oid = hashlib.sha256(op_canon.encode("ascii")).hexdigest()
                automatic.append(RepairOperation(
                    operation_type=op_type, spec_path=f.spec_path,
                    spec_status=live_status, ini_slug=f.ini_slug,
                    finding_id=fid, operation_id=oid,
                    spec_status_fingerprint=status_fp,
                ))
        else:
            reason = (
                "type2-active-source" if f.list_name == "active"
                else f"type2-queue-{f.spec_status.lower()}"
            )
            fid = f"type2:{f.ini_slug}:{f.list_name}:{f.spec_path}"
            manual.append(ManualFinding(
                finding_type=2, spec_path=f.spec_path, spec_status=f.spec_status,
                ini_slug=f.ini_slug, list_name=f.list_name, reason=reason,
                finding_id=fid,
            ))

    for f in result.type3:
        fid = f"type3:{f.ini_slug}:{f.list_name}:{f.spec_path}"
        manual.append(ManualFinding(
            finding_type=3, spec_path=f.spec_path, spec_status=f.spec_status,
            ini_slug=f.ini_slug, list_name=f.list_name, reason="type3-premature",
            finding_id=fid,
        ))

    fingerprint = (
        workspace_fingerprint
        if workspace_fingerprint is not None
        else hashlib.sha256(workspace_path.read_bytes()).hexdigest()
    )
    # plan_id: SHA-256 of canonical plan content excluding plan_id itself.
    # Must be computed AFTER all operation_id and finding_id values are set.
    auto_dicts = [dataclasses.asdict(op) for op in automatic]
    manual_dicts = [dataclasses.asdict(mf) for mf in manual]
    plan_canon = json.dumps({
        "automatic_operations": auto_dicts,
        "manual_findings": manual_dicts,
        "schema_version": 1,
        "workspace_fingerprint": fingerprint,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    plan_id = hashlib.sha256(plan_canon.encode("ascii")).hexdigest()
    return RepairPlan(
        automatic_operations=automatic,
        manual_findings=manual,
        workspace_fingerprint=fingerprint,
        plan_id=plan_id,
    )
