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
import stat
import sys
import time
import tomllib
from pathlib import Path, PurePosixPath
from typing import Any

# ── Data types ────────────────────────────────────────────────────────────────

WORKSPACE_ENTRY_CONTRACT_VERSION = "workspace-entry.v1"
WORKSPACE_ENTRY_REQUIRED_FIELDS = ("kind", "source", "summary", "needs")
WORKSPACE_ENTRY_OPTIONAL_FIELDS = ("path", "surface_role", "locator")
WORKSPACE_ARTIFACT_KINDS = ("intent", "research", "design", "brief", "spec", "defect")
SURFACE_ROLES = (
    "delivery-brief",
    "delivery-contract",
    "current-product-truth",
    "user-documentation",
    "product-history",
    "release-history",
    "current-architecture",
    "architecture-design",
    "decision-record",
    "operations",
    "interface-contract",
    "project-knowledge",
    "runtime-coordination",
)
NORMALIZED_INTAKE_CONTRACT_VERSION = "normalized-intake.v1"
NORMALIZED_INTAKE_ACTIONS = ("start", "remember", "refresh")
SOURCE_MODES = ("repo-origin", "tracker-origin")

_WORKSPACE_ENTRY_FIELDS = frozenset(
    (*WORKSPACE_ENTRY_REQUIRED_FIELDS, *WORKSPACE_ENTRY_OPTIONAL_FIELDS)
)
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
    "invalid_lifecycle_record": (
        "Repair or remove that record; other records still cool."
    ),
    "cooling_state_unavailable": (
        "Install close-work or repair docs/lifecycle/; no artifact is excluded this run."
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
class WorkspaceLocator:
    """Validated non-path locator carried by an additive workspace entry."""

    kind: str
    value: str


@dataclasses.dataclass(frozen=True)
class WorkspaceEntry:
    """Validated target workspace entry; eligibility is evaluated separately."""

    path: str | None
    kind: str
    source: SourceRecord
    summary: str
    needs: list[Dependency]
    surface_role: str | None = None
    locator: WorkspaceLocator | None = None

    @property
    def slug(self) -> str:
        if self.path is None:
            return f"surface:{self.surface_role or 'unresolved'}"
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
    handoff: NormalizedHandoff | None = None


@dataclasses.dataclass(frozen=True)
class HandoffDependency:
    """One closed, bounded dependency carried as upstream content."""

    relationship: str
    locator_kind: str
    locator: str
    semantic_role: str | None = None
    revision: str | None = None


@dataclasses.dataclass(frozen=True)
class NormalizedHandoff:
    """Validated optional shaping context; it has no routing authority."""

    boundaries: list[str]
    non_goals: list[str]
    dependencies: list[HandoffDependency]
    design_context: list[str]
    delivery_questions: list[str]


@dataclasses.dataclass(frozen=True)
class WorkspaceMembership:
    """One parsed target entry at a specific lifecycle collection."""

    entry: WorkspaceEntry
    ini_slug: str
    collection: str
    initiative_status: str
    entry_index: int = 0


@dataclasses.dataclass(frozen=True)
class LegacyWorkspaceMembership:
    """One compatibility entry retained for reader-first projections."""

    entry: LegacyWorkspaceEntry
    ini_slug: str
    collection: str
    initiative_status: str
    entry_index: int = 0


@dataclasses.dataclass(frozen=True)
class MigrationSelection:
    """Closed human-selected binding from one legacy finding to one target."""

    legacy_finding_id: str
    workspace_fingerprint: str
    source_membership: dict[str, object]
    target_entry: WorkspaceEntry
    target_entry_raw: dict[str, object]
    target_membership: dict[str, str]
    owning_processor: str
    provenance_reference: str
    legacy_content_approved_for_ledger: bool


@dataclasses.dataclass(frozen=True)
class MigrationPlan:
    """Deterministic read-only migration planning result."""

    result: dict[str, object]
    finding: dict[str, object] | None = None
    proposed_operation: dict[str, object] | None = None


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
    # `memberships` is deliberately unfiltered, so every consumer of it needs
    # the cooled set to know which entries it may not open. Carrying the set
    # here rather than threading a parameter is what makes that unmissable:
    # `canonical_repository_identity` consumed `memberships` and fingerprinted
    # each artifact by reading its body, which silently reopened every cooled
    # spec.md and plan.md on all four ordinary-orientation surfaces.
    cooled: frozenset[Path] = frozenset()


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
    shipped: list[str]
    withdrawn: list[str]
    cancelled: list[str]


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
    cooled: frozenset[Path] = dataclasses.field(default_factory=frozenset)
    cooling_findings: tuple[RoutingFinding, ...] = ()
    cooling_records: tuple[Any, ...] = ()
    cooling_module: Any | None = None
    now: datetime.datetime | None = None

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


@dataclasses.dataclass(frozen=True)
class CloseoutStatusProjection:
    """Read-only closeout facts; policy and effects remain with close-work."""

    paused: bool
    all_specs_shipped: bool
    closeout_blockers: tuple[str, ...]
    initiative_eligible: bool
    next_action: str
    cooling_context_visible: bool


def project_closeout_status(
    *,
    paused: bool,
    all_specs_shipped: bool,
    closeout_blockers: list[str] | tuple[str, ...],
    cooling_context_visible: bool,
) -> CloseoutStatusProjection:
    """Project pause/eligibility without distilling, deciding, or mutating."""
    if not all(
        isinstance(value, bool)
        for value in (paused, all_specs_shipped, cooling_context_visible)
    ):
        raise ValueError("closeout projection boolean facts are required")
    if not isinstance(closeout_blockers, (list, tuple)) or any(
        not isinstance(blocker, str) or not blocker.strip()
        for blocker in closeout_blockers
    ):
        raise ValueError("closeout blockers must be bounded strings")
    blockers = tuple(
        dict.fromkeys(
            [*closeout_blockers, *(() if all_specs_shipped else ("unshipped-specs",))]
        )
    )
    eligible = all_specs_shipped and not blockers and not paused
    if eligible:
        next_action = "invoke-close-work"
    elif paused:
        next_action = "resume-or-keep-paused"
    else:
        next_action = "settle-closeout-blockers"
    return CloseoutStatusProjection(
        paused=paused,
        all_specs_shipped=all_specs_shipped,
        closeout_blockers=blockers,
        initiative_eligible=eligible,
        next_action=next_action,
        cooling_context_visible=cooling_context_visible,
    )


# ── Group 2 contract parsing ──────────────────────────────────────────────────

_CONSTRAINT_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_SENSITIVE_CONSTRAINT_RE = re.compile(
    r"(?:^|_)(?:raw|payload|prompt|instruction|credential|credentials|secret|secrets|"
    r"password|passwords|passwd|pwd|(?:api|access|private)?_?(?:token|tokens|key|keys))"
    r"(?:_|$)"
)
_SENSITIVE_LOCATOR_RE = re.compile(
    r"(?i)(?:^|[/;:])(?:password|passwd|pwd|secret|api[_-]?key|"
    r"access[_-]?token|token)\s*[:=]\s*\S+"
)
_ABSOLUTE_LOCAL_LOCATOR_RE = re.compile(r"(?i)^(?:/|[a-z]:[/\\]|\\\\)")


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


def _is_strict_locator(value: object) -> bool:
    """Reject whitespace and control characters on top of `_is_safe_locator`.

    Workspace source references and external surface locators are consumed as
    identifiers rather than rendered as escaped data, so they carry the tighter
    form the semantic-surface contract requires. Normalized-intake locators stay
    on the looser predicate: they are untrusted source text that the intake
    guard escapes at render time.
    """
    if not _is_safe_locator(value):
        return False
    text = str(value)
    return (
        not _SENSITIVE_LOCATOR_RE.search(text)
        and not _ABSOLUTE_LOCAL_LOCATOR_RE.match(text)
        and "\\" not in text
        and not any(part in {".", ".."} for part in text.split("/"))
        and not any(
        character.isspace() or ord(character) <= 31 or ord(character) == 127
            for character in text
        )
    )


def _is_repository_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not 1 <= len(value) <= 1000:
        return False
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return False
    if "\\" in value:
        return False
    if any(ord(character) <= 31 or ord(character) == 127 for character in value):
        return False
    parts = value.split("/")
    return not (".." in parts or "." in parts or "" in parts)


_SINGLE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,199}$")

# Upper bound on any untrusted workspace value emitted as a finding identifier.
_MAX_FINDING_IDENTIFIER = 200


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
    if ref is not None and not _is_strict_locator(ref):
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
    if not set(WORKSPACE_ENTRY_REQUIRED_FIELDS).issubset(keys) or not keys.issubset(
        _WORKSPACE_ENTRY_FIELDS
    ):
        return None, [_finding("invalid_entry", detail="target entry fields are not exact")]
    path = raw.get("path")
    if path is None and "locator" not in raw:
        return None, [_finding("invalid_entry", detail="target entry needs path or locator")]
    if path is not None and not _is_repository_relative_path(path):
        return None, [_path_finding_or_invalid(path, "entry path is unsafe")]
    kind = raw.get("kind")
    if kind not in WORKSPACE_ARTIFACT_KINDS:
        return None, [_finding("invalid_entry", str(path), "entry kind is invalid")]
    if path is not None and kind == "spec" and not _is_canonical_spec_artifact_path(path):
        return None, [_finding("invalid_artifact_path", str(path), "spec path is invalid")]
    if path is not None and kind == "brief" and not _is_canonical_local_brief_path(path):
        return None, [_finding("invalid_artifact_path", str(path), "brief path is invalid")]
    surface_role = raw.get("surface_role")
    if surface_role is not None and surface_role not in SURFACE_ROLES:
        return None, [_finding("invalid_entry", str(path or ""), "surface role is invalid")]
    locator = None
    if "locator" in raw:
        if surface_role is None:
            return None, [
                _finding("invalid_entry", str(path or ""), "locator requires surface role")
            ]
        raw_locator = raw.get("locator")
        if (
            not isinstance(raw_locator, dict)
            or set(raw_locator) != {"kind", "value"}
            or raw_locator.get("kind") != "external"
            or not _is_strict_locator(raw_locator.get("value"))
            or re.fullmatch(
                r"[A-Za-z][A-Za-z0-9+.-]*:.+", str(raw_locator.get("value", ""))
            )
            is None
        ):
            return None, [
                _finding("invalid_entry", str(path or ""), "external locator is invalid")
            ]
        locator = WorkspaceLocator("external", raw_locator["value"])
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
        surface_role=surface_role,
        locator=locator,
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


def _validate_handoff(raw: object) -> NormalizedHandoff | None:
    """Validate the additive closed handoff object without interpreting text."""

    required = {
        "boundaries",
        "non_goals",
        "dependencies",
        "design_context",
        "delivery_questions",
    }
    if not isinstance(raw, dict) or set(raw) != required:
        return None
    text_arrays: dict[str, list[str]] = {}
    for key in ("boundaries", "non_goals", "design_context", "delivery_questions"):
        values = raw.get(key)
        if (
            not isinstance(values, list)
            or len(values) > 50
            or not all(_is_bounded_text(value, 2000) for value in values)
        ):
            return None
        text_arrays[key] = list(values)

    raw_dependencies = raw.get("dependencies")
    if not isinstance(raw_dependencies, list) or len(raw_dependencies) > 32:
        return None
    dependencies: list[HandoffDependency] = []
    required_dependency = {"relationship", "locator_kind", "locator"}
    allowed_dependency = required_dependency | {"semantic_role", "revision"}
    for raw_dependency in raw_dependencies:
        if (
            not isinstance(raw_dependency, dict)
            or set(raw_dependency) - allowed_dependency
            or not required_dependency.issubset(raw_dependency)
        ):
            return None
        relationship = raw_dependency.get("relationship")
        locator_kind = raw_dependency.get("locator_kind")
        locator = raw_dependency.get("locator")
        semantic_role = raw_dependency.get("semantic_role")
        revision = raw_dependency.get("revision")
        if relationship not in {"blocks", "informs"}:
            return None
        if locator_kind == "repository-path":
            if not _is_repository_relative_path(locator):
                return None
        elif locator_kind == "external":
            if (
                not _is_strict_locator(locator)
                or re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*:.+", str(locator))
                is None
                or not _is_bounded_text(revision, 300)
                or not _is_strict_locator(revision)
            ):
                return None
        else:
            return None
        if semantic_role is not None and semantic_role not in {
            "delivery-brief",
            "delivery-contract",
        }:
            return None
        if revision is not None and (
            not _is_bounded_text(revision, 300) or not _is_strict_locator(revision)
        ):
            return None
        dependencies.append(
            HandoffDependency(
                relationship=str(relationship),
                locator_kind=str(locator_kind),
                locator=str(locator),
                semantic_role=str(semantic_role) if semantic_role is not None else None,
                revision=str(revision) if revision is not None else None,
            )
        )
    return NormalizedHandoff(
        boundaries=text_arrays["boundaries"],
        non_goals=text_arrays["non_goals"],
        dependencies=dependencies,
        design_context=text_arrays["design_context"],
        delivery_questions=text_arrays["delivery_questions"],
    )


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
    allowed = required | {"refresh_target", "handoff"}
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
    handoff = None
    if "handoff" in raw:
        handoff = _validate_handoff(raw.get("handoff"))
        if handoff is None:
            return None, [_finding("invalid_entry", detail="handoff is invalid")]
    return NormalizedIntake(
        contract_version=NORMALIZED_INTAKE_CONTRACT_VERSION,
        action=action,
        content=content,
        source=source,
        constraints=constraints,
        proposed_authority=authority,
        refresh_target=refresh_target,
        handoff=handoff,
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


def _bounded_finding_identifier(value: str) -> str:
    """Bound an untrusted workspace value before it becomes a finding identifier.

    Findings are rendered back into an agent's context, so an unbounded or
    control-character-bearing value read from `workspace.toml` is an
    output-injection surface. Unsafe but *path-shaped* values survive this
    bound on purpose, so `invalid_artifact_path` can still name them; only
    unrenderable ones degrade to the unattributed fallback.
    """
    if len(value) > _MAX_FINDING_IDENTIFIER:
        return ""
    if any(char < " " or char == "\x7f" for char in value):
        return ""
    return value


def _legacy_path_finding(collection: str, raw: object) -> LegacyWorkspaceEntry:
    path = raw if isinstance(raw, str) else ""
    if isinstance(raw, dict):
        if isinstance(raw.get("path"), str):
            path = raw["path"]
        elif _is_legacy_slug(raw.get("slug")):
            # Single-segment by construction, so a promoted slug can never
            # satisfy the `path_like` test below. That is what keeps the record
            # `unsupported_legacy` instead of reclassifying it as
            # `invalid_artifact_path`; do not loosen this predicate.
            path = raw["slug"]
    path = _bounded_finding_identifier(path)
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
        "brief_queue.withdrawn",
        "brief_queue.cancelled",
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
    if not isinstance(raw, dict) or not ({"path", "locator"} & set(raw)):
        return False
    keys = set(raw)
    if keys.issubset(_WORKSPACE_ENTRY_FIELDS):
        path = raw.get("path")
        return bool(keys & {"kind", "source", "summary", "surface_role"}) or (
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
    "brief_queue": ("draft", "ready", "executing", "shipped", "withdrawn", "cancelled"),
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
    "brief_queue.withdrawn": {"brief"},
    "brief_queue.cancelled": {"brief"},
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
    "3531a8f8e26bcdbf0ec69357a9f6eeb8fe8f2039e2ab2cbcfb44555976ee0b67"
)
_NORMALIZED_INTAKE_SCHEMA_DIGEST = (
    "fcc077be35e968260c733503dcc3f773b16b8782a24ad9584ffa16a6245ceb54"
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


def _surface_metadata_payload(entry: WorkspaceEntry) -> dict[str, object]:
    """Project additive surface metadata only when an entry declares it."""
    payload: dict[str, object] = {}
    if entry.surface_role is not None:
        payload["surface_role"] = entry.surface_role
    if entry.locator is not None:
        payload["locator"] = dataclasses.asdict(entry.locator)
    return payload


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
            **_surface_metadata_payload(evaluation.entry),
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
        entry_identity = entry.path
        if entry_identity is None and entry.locator is not None:
            entry_identity = (
                f"{entry.surface_role}:{entry.locator.kind}:{entry.locator.value}"
            )
        identity_key = f"{membership.ini_slug}:{membership.collection}:{entry_identity}"
        semantic_memberships.append({
            "path": entry.path,
            "kind": entry.kind,
            **_surface_metadata_payload(entry),
            "source": source,
            "needs": needs,
            "ini_slug": membership.ini_slug,
            "collection": membership.collection,
            "initiative_status": membership.initiative_status,
        })
        if entry.path is None:
            status_fingerprints[identity_key] = hashlib.sha256(b"null").hexdigest()
            provenance_fingerprints[identity_key] = hashlib.sha256(
                json.dumps(
                    {"source": source, "artifact": None},
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                ).encode("ascii")
            ).hexdigest()
            profile = entry.source.tracker_profile
            if profile is not None:
                tracker_profiles.add((profile["id"], profile["version"]))
            continue
        artifact = _confined_artifact_path(root, entry.path)
        cooled_member = artifact is not None and artifact in result.cooled
        if cooled_member:
            # Identity for a cooled artifact is derived from its membership and
            # a constant marker. Both branches below open the body — a
            # `read_text` for the status fingerprint and an `open` for the
            # sibling plan — and a fingerprint is still a read, however little
            # of it reaches the output. That is what made this invisible: only
            # the SHA-256 was emitted, so every criterion asserting an absent
            # body value still passed.
            metadata = _metadata_from_membership(membership) or ArtifactMetadata(
                path=entry.path, kind=entry.kind, status=None, exists=True
            )
            status_fingerprint = _COOLED_IDENTITY_MARKER
        else:
            metadata = _metadata_from_root(root, entry)
            status_fingerprint = None
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


def _cooling_module_path() -> Path | None:
    """Return a confined filesystem cooling module when one is available."""
    engine_path = Path(__file__).resolve()
    skill_root = engine_path.parents[2]
    # Only reach a sibling skill from a real skills tree. Under the packaged
    # `_data/` layout `parents[2]` is the directory holding the `agentbundle`
    # package, so this candidate would resolve, confine and execute an
    # unrelated `close-work/scripts/cooling.py` placed beside it in preference
    # to the co-located module AC37 guarantees. Same predicate as
    # `close_work._in_installed_skills_tree`.
    sibling_reach_allowed = (
        engine_path.parent.name == "scripts" and skill_root.name == "skills"
    )
    candidates = tuple(
        candidate for candidate, allowed in (
            ((skill_root / "close-work" / "scripts" / "cooling.py", skill_root),
             sibling_reach_allowed),
            ((engine_path.parent / "cooling.py", engine_path.parent), True),
        )
        if allowed
    )
    for candidate, declared_root in candidates:
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(declared_root.resolve(strict=True))
        except (OSError, ValueError, RuntimeError):
            continue
        if resolved.is_file():
            return resolved
    if (
        os.environ.get("AGENTBUNDLE_ALLOW_DEV_SOURCE_AUTHORITY") == "1"
        and len(engine_path.parents) > 4
    ):
        checkout_root = engine_path.parents[4]
        candidate = (
            checkout_root / "packs" / "core" / ".apm" / "skills"
            / "close-work" / "scripts" / "cooling.py"
        )
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(checkout_root.resolve(strict=True))
        except (OSError, ValueError, RuntimeError):
            pass
        else:
            if resolved.is_file():
                return resolved
    return None


# The callables the projection and the cooled-set resolution reach for. The
# record *attributes* they read are guarded per record by _COOLING_RECORD_FIELDS,
# because a module can satisfy this contract while one record does not.
_COOLING_MODULE_CALLABLES = ("load_record", "is_due")

# Stands in for a cooled artifact's status fingerprint. The identity must still
# change when a workspace entry changes, and must not depend on a body this run
# may not read.
_COOLED_IDENTITY_MARKER = "cooled"

# Every attribute _cooling_projection reads off an accepted record. A record
# missing one raises AttributeError from inside the projection, which the
# top-level handler reports as configuration_mismatch with exit 2 — a record
# problem presented as a configuration one, and with no finding naming the file.
_COOLING_RECORD_FIELDS = (
    "delivery_id",
    "locator",
    "aliases",
    "disposition",
    "post_closeout_result",
    "completion_event",
    "completion_evidence_ref",
    "review_on",
    "exception",
)


def _load_cooling_module() -> Any:
    """Load the cooling module through a confined filesystem or package route."""
    module_path = _cooling_module_path()
    if module_path is None:
        try:
            module = importlib.import_module("agentbundle._data.cooling")
        except ImportError as exc:
            raise RuntimeError("cooling module unavailable") from exc
    else:
        module_name = "_workspace_status_cooling_" + hashlib.sha256(
            str(module_path).encode("utf-8")
        ).hexdigest()
        module = sys.modules.get(module_name)
        if module is None:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                raise RuntimeError("cooling module unavailable")
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            try:
                spec.loader.exec_module(module)
            except Exception as exc:
                sys.modules.pop(module_name, None)
                raise RuntimeError("cooling module unavailable") from exc
    # Guard everything the projection calls, not just the entry point. Loading
    # on `load_record` alone let a module missing `is_due` pass here and raise
    # AttributeError later, deep inside `_cooling_projection`, where the
    # top-level handler turns it into `configuration_mismatch` and exit 2 — a
    # module-shape problem reported as a configuration one.
    if any(
        not callable(getattr(module, name, None))
        for name in _COOLING_MODULE_CALLABLES
    ):
        raise RuntimeError("cooling module unavailable")
    return module


_COOLING_PAIRS = frozenset(
    {
        ("cool-30-days", "Cooling"),
        ("cool-30-days", "Retired"),
        ("retain-exception", "Retired"),
    }
)


def _cooled_locators(
    root: Path, module: Any, records_out: list[Any] | None = None
) -> tuple[frozenset[Path], tuple[RoutingFinding, ...]]:
    """Read accepted lifecycle records and return their resolved artifact paths."""
    lifecycle_dir = root / "docs" / "lifecycle"
    if not lifecycle_dir.exists() and not lifecycle_dir.is_symlink():
        return frozenset(), ()
    try:
        resolved_root = root.resolve()
        resolved_lifecycle = lifecycle_dir.resolve()
        resolved_lifecycle.relative_to(resolved_root)
        if not lifecycle_dir.is_dir():
            raise ValueError("lifecycle is not a directory")
        records = sorted(lifecycle_dir.glob("*.json"))
    except (OSError, ValueError, RuntimeError):
        return frozenset(), (_finding("cooling_state_unavailable"),)
    cooled: set[Path] = set()
    findings: list[RoutingFinding] = []
    for record_path in records:
        relative_path = record_path.relative_to(root).as_posix()
        if record_path.is_symlink() or not record_path.is_file():
            findings.append(_finding("invalid_lifecycle_record", relative_path))
            continue
        try:
            result = module.load_record(root, record_path)
        except Exception:
            # The module can be an older cooling.py resolved from an installed
            # skills tree, so its behaviour is not this engine's to assume. The
            # callable guard proves the name exists, not that it returns rather
            # than raises. Unhandled, this left analyze() as
            # `configuration_mismatch` and exit 2 — a record problem reported as
            # a configuration one, with no finding naming the file.
            findings.append(_finding("invalid_lifecycle_record", relative_path))
            continue
        record = getattr(result, "record", None)
        if (
            getattr(result, "code", None) is not None
            or record is None
            or any(not hasattr(record, name) for name in _COOLING_RECORD_FIELDS)
        ):
            findings.append(_finding("invalid_lifecycle_record", relative_path))
            continue
        if records_out is not None:
            records_out.append(record)
        if (record.disposition, record.post_closeout_result) not in _COOLING_PAIRS:
            continue
        for locator in (record.locator, *record.aliases):
            try:
                member = (root / locator).resolve()
            except (OSError, RuntimeError):
                continue
            if member.exists():
                cooled.add(member)
    return frozenset(cooled), tuple(findings)


def _resolve_cooled_state(
    root: Path,
    records_out: list[Any] | None = None,
    module_out: list[Any] | None = None,
) -> tuple[frozenset[Path], tuple[RoutingFinding, ...]]:
    """Resolve cooling support once, then load the repository's cooled set."""
    # An absent lifecycle directory is not a cooling failure, so decide it
    # before resolving the module. Resolving first meant an adopter with no
    # lifecycle records at all got `cooling_state_unavailable` on every run
    # whenever the closure was not installed — AC7 forbids that finding for
    # this input, while AC38 requires it for the all-routes-failed input, and
    # the two overlapped here.
    lifecycle_dir = root / "docs" / "lifecycle"
    if not lifecycle_dir.exists() and not lifecycle_dir.is_symlink():
        return frozenset(), ()
    try:
        module = _load_cooling_module()
    except RuntimeError:
        return frozenset(), (_finding("cooling_state_unavailable"),)
    if module_out is not None:
        module_out.append(module)
    return _cooled_locators(root, module, records_out)


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
            for entry_index, raw_entry in enumerate(entries):
                (
                    membership,
                    legacy_membership,
                    entry_findings,
                    blocked_path,
                ) = _parse_membership_entry(raw_entry, collection, "", "")
                if membership is not None:
                    memberships.append(
                        dataclasses.replace(membership, entry_index=entry_index)
                    )
                if legacy_membership is not None:
                    legacy_memberships.append(
                        dataclasses.replace(legacy_membership, entry_index=entry_index)
                    )
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
                for entry_index, raw_entry in enumerate(entries):
                    (
                        membership,
                        legacy_membership,
                        entry_findings,
                        blocked_path,
                    ) = _parse_membership_entry(raw_entry, collection, ini_slug, status)
                    if membership is not None:
                        memberships.append(
                            dataclasses.replace(membership, entry_index=entry_index)
                        )
                    if legacy_membership is not None:
                        legacy_memberships.append(
                            dataclasses.replace(legacy_membership, entry_index=entry_index)
                        )
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
    if membership.collection == "brief_queue.withdrawn":
        return "Withdrawn"
    if membership.collection == "brief_queue.cancelled":
        return "Cancelled"
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
    cooled: frozenset[Path],
    briefs_with_cooled_children: frozenset[str] = frozenset(),
) -> tuple[bool, RoutingFinding | None]:
    if dep.path in structurally_blocked_paths:
        return False, _finding("unsatisfied_dependency", dep.path, "dependency has findings")
    # Fail closed when a brief's child scope is unknown. A cooled child may
    # have changed the brief's terminal state without the workspace membership
    # reflecting it, so the brief's apparent state is not evidence.
    #
    # The refused set is exactly the normalized `source.parent` values declared
    # by cooled spec memberships. It is NOT initiative-scoped and does not
    # consider initiative status: a cooled spec in a paused initiative that
    # declares a brief owned by an active one still refuses that brief. The
    # value is also unvalidated against the artifact body, because the cooled
    # branch of `_structural_findings` returns before the provenance check —
    # for a cooled child the declaration is unverifiable by construction, which
    # is the point of failing closed rather than trusting it.
    brief_scope_unknown = dep.kind == "brief" and dep.path in briefs_with_cooled_children
    cooled_dependency = (
        root is not None and _confined_artifact_path(root, dep.path) in cooled
    )
    if dep.type == "cross-repo":
        if cooled_dependency:
            # RFC-0096 §7 with no exception. `_cross_repo_receipt_satisfied`
            # opens the brief body unconditionally, and the evidence it needs
            # is only there: the four-field receipt match asserted for this one
            # dependency. A lifecycle record cannot stand in — it is completion
            # evidence for the brief as a whole, and projecting the receipt
            # from its coordination surface is deferred to Wave 7 by
            # `wave6-dependency-scoped-completion-receipts`. Refusing surfaces
            # a real inconsistency rather than concealing one: a brief with a
            # live cross-repo dependant is retained as an exception, not cooled.
            return False, _finding(
                "unsatisfied_dependency",
                dep.path,
                "cooled dependency receipt is not readable",
            )
        return _cross_repo_receipt_satisfied(dep, root)

    matches = by_path.get(dep.path, [])
    if matches and not any(match.entry.kind == dep.kind for match in matches):
        return False, _finding("unsatisfied_dependency", dep.path, "dependency kind mismatch")
    if dep.kind == "defect" and not any(
        match.collection == "backlog.closed" for match in matches
    ):
        if cooled_dependency:
            return False, _finding(
                "unsatisfied_dependency", dep.path, "defect lacks closed membership"
            )
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
    # Decide every cooled dependency here, before any probe is built. Keying
    # this on `dep.kind == "spec"` let intent/research/design fall through to
    # the probe below and read the cooled body. The per-kind *outcome* is
    # preserved: `defect` already returned above when it lacks a closed
    # membership, so reaching this line means the dependency is satisfied by
    # its lifecycle record — which is completion evidence, and the only
    # evidence available once the body may not be read.
    if cooled_dependency:
        return True, None
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
    if brief_scope_unknown:
        # Deliberately after the safety check: a missing, unreadable or
        # invalid-path brief has a concrete cause, and reporting "re-establish
        # the child scope" for a brief that does not exist sends the maintainer
        # to the wrong repair.
        return False, _finding(
            "unsatisfied_dependency", dep.path, "brief child scope is unknown"
        )
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


def _legacy_membership_is_cooled(
    membership: LegacyWorkspaceMembership,
    root: Path | None,
    cooled: frozenset[Path],
) -> bool:
    """True when a legacy membership's canonical artifact is cooled.

    A legacy entry stores `spec/alpha`, so the canonical alias has to be
    recovered before the membership key applies. Resolving the stored form
    directly yields `<root>/spec/alpha`, which cannot equal any cooled path
    whatever the lifecycle record says, so the check silently never fires.
    """
    if root is None or not cooled:
        return False
    alias = _legacy_canonical_alias(membership.entry)
    if alias is None:
        return False
    return _confined_artifact_path(root, alias) in cooled


def _membership_is_cooled(
    membership: WorkspaceMembership,
    root: Path | None,
    cooled: frozenset[Path],
) -> bool:
    """True when this membership's artifact is named by a lifecycle record.

    The single membership-key rule for the whole engine: resolve through
    `_confined_artifact_path`, because every read site canonicalizes before
    opening and a raw string can never match a resolved cooled path.
    """
    if root is None or not cooled:
        return False
    return _confined_artifact_path(root, membership.entry.path or "") in cooled


def _brief_child_spec_states(
    memberships: list[WorkspaceMembership],
    workspace: dict,
    root: Path | None,
    cooled: frozenset[Path] = frozenset(),
) -> tuple[dict[str, set[str]], frozenset[str]]:
    """Map each brief to its children's observed states; flag briefs with cooled children.

    Returns (states, briefs_with_cooled_children).

    states maps each brief path to the set of states contributed by its
    non-cooled child spec memberships. A cooled child contributes no state at
    all: its status would come from `_membership_status`, which derives state
    from the collection alone and so fabricates "Shipped" for anything in
    `work.shipped`.

    briefs_with_cooled_children names every brief a cooled child declares
    through `source.parent`. For those briefs `invalid_child_scope` is
    unevaluable and any `kind="brief"` dependency fails closed, so a lifecycle
    record cannot erase or create a finding about a different artifact.

    A cooled child that declares no `source.parent` is not attributed, and the
    briefs it may belong to are therefore not protected. That gap is the
    recorded residual `cooling-brief-child-scope`; closing it conservatively
    would refuse every brief dependency whenever any ordinary parentless spec
    cooled, which is the common case rather than the exception.
    """
    states: dict[str, set[str]] = {}
    briefs_affected: set[str] = set()
    for membership in memberships:
        entry = membership.entry
        if entry.kind != "spec":
            continue
        if _membership_is_cooled(membership, root, cooled):
            # A cooled child's state is not observable without reading its
            # body, and its parent may be absent from the read-free source
            # record.  Both facts make the parent brief's child scope
            # unevaluable.  Exclude the child from states and record the
            # affected briefs instead.
            source_parent = _normalized_optional_artifact_value(entry.source.parent)
            if source_parent is not None:
                briefs_affected.add(source_parent)
            # A cooled child that declares no `source.parent` is deliberately
            # NOT attributed. Its brief link, if any, lives in the body this run
            # may not read — but so does the link of every parentless spec that
            # was never a child at all, and those are the overwhelming majority
            # (81 of 92 in this repository's main initiative). Marking every
            # brief in the initiative to cover the rare real child refused every
            # brief dependency whenever any ordinary spec cooled, which costs
            # far more availability than the bypass it closes. The residual is
            # recorded as `cooling-brief-child-scope`.
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
    return states, frozenset(briefs_affected)


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
            "brief_queue.withdrawn": {"Withdrawn"},
            "brief_queue.cancelled": {"Cancelled"},
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
    cooled: bool = False,
    briefs_with_cooled_children: frozenset[str] = frozenset(),
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
    if cooled:
        # Everything above is derived from the membership: the workspace entry,
        # its collection, and the duplicate/cycle sets. Everything below reads
        # the artifact body — existence, readability, parent provenance, plan
        # state, status lifecycle. For a cooled artifact those predicates are
        # not observable, so they are not evaluated rather than evaluated
        # against absent values. Passing read-free metadata down instead would
        # report a live artifact as `missing_artifact` and its declared parent
        # as a `provenance_mismatch`, which is how a cooled defect came to
        # block its own live dependants.
        return findings
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
        if not _brief_child_scope_is_valid(
            membership.collection,
            child_states,
            scope_unevaluable=entry.path in briefs_with_cooled_children,
        ):
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
    cooled: frozenset[Path] = frozenset(),
    briefs_with_cooled_children: frozenset[str] = frozenset(),
) -> DispatchEvaluation:
    """Evaluate the positive T2 dispatch predicate for one canonical membership."""
    entry = membership.entry
    if entry.path is None:
        return DispatchEvaluation(
            entry=entry,
            ini_slug=membership.ini_slug,
            collection=membership.collection,
            dispatchable=False,
            findings=[
                _finding(
                    "configuration_mismatch",
                    "workspace.toml",
                    "locator-only entries are visible but non-dispatchable",
                )
            ],
            authority_status=None,
        )
    metadata = _artifact_metadata(workspace, entry, root) or _metadata_from_membership(membership)
    findings = _structural_findings(
        membership,
        metadata,
        duplicate_paths,
        cycle_paths,
        brief_child_states,
        global_invalid_workspace,
        root,
        briefs_with_cooled_children=briefs_with_cooled_children,
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
            cooled,
            briefs_with_cooled_children=briefs_with_cooled_children,
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
    cooled: frozenset[Path] = frozenset(),
) -> CanonicalWorkspaceResult:
    """Parse target entries and evaluate T2 canonical findings without projection changes."""
    (
        memberships,
        legacy_memberships,
        parse_findings,
        parse_blocked_path_counts,
    ) = _extract_canonical_memberships(workspace)
    # Cooling is applied at evaluation and emission, never here. Every fact
    # derived below — by_path, duplicate_paths, cycle_paths, legacy_alias_counts
    # and the structural loop — must see a cooled artifact as *cooled*, not as
    # *absent*, or a lifecycle record silently erases unrelated conclusions
    # about it. What the cooled set governs is the artifact *body*: for a cooled
    # membership the structural loop and _brief_child_spec_states skip the
    # predicates that would have to open it, keeping the ones derived from the
    # workspace entry alone.
    parse_blocked_paths = set(parse_blocked_path_counts)
    local_memberships = [
        membership for membership in memberships if membership.entry.path is not None
    ]
    by_path: dict[str, list[WorkspaceMembership]] = {}
    for membership in local_memberships:
        assert membership.entry.path is not None
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
    cycle_paths = _dependency_cycles(local_memberships)
    brief_child_states, briefs_with_cooled_children = _brief_child_spec_states(
        local_memberships, workspace, root, cooled
    )
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
    cooled_membership_findings: list[RoutingFinding] = []
    for membership in local_memberships:
        membership_cooled = _membership_is_cooled(membership, root, cooled)
        metadata = (
            None
            if membership_cooled
            else (
                _artifact_metadata(workspace, membership.entry, root)
                or _metadata_from_membership(membership)
            )
        )
        member_findings = _structural_findings(
            membership,
            metadata,
            duplicate_paths,
            cycle_paths,
            brief_child_states,
            global_invalid_workspace,
            root,
            cooled=membership_cooled,
            briefs_with_cooled_children=briefs_with_cooled_children,
        )
        if member_findings:
            structurally_blocked_paths.add(membership.entry.path)
            if membership_cooled:
                # A cooled membership is excluded from `evaluations`, and the
                # emitted finding list is built from those, so everything raised
                # here reached no output — cooling both halves of a duplicate
                # pair erased `duplicate_membership` entirely. These findings are
                # membership-derived by construction (the cooled branch of
                # `_structural_findings` returns before any body-dependent
                # predicate), so they are facts about `workspace.toml` entries,
                # which AC20 settles are still owed whatever the artifact's
                # state.
                cooled_membership_findings.extend(member_findings)
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
            cooled,
            briefs_with_cooled_children=briefs_with_cooled_children,
        )
        for membership in memberships
        if not _membership_is_cooled(membership, root, cooled)
    ]
    dispatch_by_path = {
        evaluation.entry.path: evaluation
        for evaluation in evaluations
        if evaluation.entry.path is not None
    }
    findings = [
        *parse_findings,
        *legacy_only_duplicate_findings,
        *cooled_membership_findings,
        *(finding for evaluation in evaluations for finding in evaluation.findings),
    ]
    return CanonicalWorkspaceResult(
        cooled=cooled,
        memberships=memberships,
        # Emission, not derivation: `legacy_alias_counts` above still counts a
        # cooled legacy entry, so cooling one half of a duplicate pair does not
        # erase the duplicate finding for the half that stays visible.
        legacy_memberships=[
            membership
            for membership in legacy_memberships
            if not _legacy_membership_is_cooled(membership, root, cooled)
        ],
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
            shipped_raw = brief_raw.get("shipped", [])
            withdrawn_raw = brief_raw.get("withdrawn", [])
            cancelled_raw = brief_raw.get("cancelled", [])
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
            shipped = []
            if isinstance(shipped_raw, list):
                shipped = [
                    path
                    for raw in shipped_raw
                    if (path := _supported_brief_queue_path(raw)) is not None
                ]
            withdrawn = []
            if isinstance(withdrawn_raw, list):
                withdrawn = [
                    path
                    for raw in withdrawn_raw
                    if (path := _supported_brief_queue_path(raw)) is not None
                ]
            cancelled = []
            if isinstance(cancelled_raw, list):
                cancelled = [
                    path
                    for raw in cancelled_raw
                    if (path := _supported_brief_queue_path(raw)) is not None
                ]
            brief_queue = BriefQueue(
                executing=executing,
                ready=ready,
                draft=draft,
                shipped=shipped,
                withdrawn=withdrawn,
                cancelled=cancelled,
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

    # Brief: "brief:<path>" — satisfied if Ready, Executing, or Shipped.
    if need.startswith("brief:"):
        path = need[len("brief:"):]
        for ini in all_initiatives:
            if ini.slug == ini_slug and ini.brief_queue is not None:
                bq = ini.brief_queue
                if bq.executing == path:
                    return True
                return path in bq.ready or path in bq.shipped
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


def _brief_child_scope_is_valid(
    collection: str,
    child_states: set[str],
    scope_unevaluable: bool = False,
) -> bool:
    """Return whether child progress is compatible with a brief lifecycle.

    `scope_unevaluable` is True when a child this brief declares has cooled, so
    `child_states` may be missing a state that is really there. Only the arms
    that assert a state is PRESENT are suppressed, because only they are
    non-monotone: a missing child can flip them from satisfied to violated, and
    cooling would plant a finding on live work. The arms that assert a state is
    ABSENT read the states actually observed — an unknown extra child can only
    add a state, never remove one — so a violation found among live, readable
    children stays a violation whatever the cooled child is. Suppressing every
    arm would let cooling one child erase an `impossible_transition` that a
    different, fully readable child caused.
    """

    execution_evidence = bool(child_states & {"Implementing", "Shipped"})
    if collection in {
        "brief_queue.draft",
        "brief_queue.ready",
        "brief_queue.withdrawn",
    }:
        # Asserts execution evidence is absent: monotone, never suppressed.
        return not execution_evidence
    if collection in {"brief_queue.executing", "brief_queue.cancelled"}:
        # Asserts evidence is present: a cooled child can hide the only child
        # carrying it.
        return execution_evidence or scope_unevaluable
    if collection == "brief_queue.shipped":
        # Asserts no child is in a state other than Shipped: monotone, never
        # suppressed. Deliberately does NOT require the set to be non-empty.
        # Most specs declare no `source.parent`, so an empty set here means
        # "no child is attributed to this brief", not "this brief shipped
        # nothing". The non-empty requirement lives in the coverage lint, which
        # reads the brief's own Spec map; this projection cannot read the brief.
        return all(state == "Shipped" for state in child_states)
    return True


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
    cooled: frozenset[Path] = frozenset(),
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
            if _current_resolved / "spec.md" in cooled:
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
    cooled: frozenset[Path] = frozenset(),
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
                if spec_file in cooled:
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
            if spec_file in cooled:
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
    cooled: frozenset[Path] = frozenset(),
) -> tuple[list[ReconciliationFinding], int]:
    """Run all three reconciliation scan types. Returns (findings, files_read)."""
    all_tracked: set[str] = set()
    for ini in initiatives:
        for e in ini.work.queue + ini.work.active + ini.work.shipped:
            all_tracked.add(e.path)

    type1_findings, type1_files = _run_type1_scan(root, all_tracked, cooled)
    type23_findings, type23_files = _run_type23_scan(root, initiatives, cooled)
    return type1_findings + type23_findings, type1_files + type23_files


# ── Main analysis entry point ─────────────────────────────────────────────────

def analyze(
    root: Path,
    *,
    workspace_bytes: bytes | None = None,
    cooling_enabled: bool = True,
    now: datetime.datetime | None = None,
) -> WorkspaceStatusResult:
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
    # repair-plan and the migration paths keep pre-Wave-6 behaviour: they see an
    # empty cooled set so their operations still reach cooled entries. Whether
    # cooling constrains them is RFC-0096 Wave 7's decision.
    moment = now if now is not None else datetime.datetime.now(datetime.UTC)
    cooling_records: list[Any] = []
    cooling_modules: list[Any] = []
    cooled, cooling_findings = (
        _resolve_cooled_state(root, cooling_records, cooling_modules)
        if cooling_enabled else (frozenset(), ())
    )

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
    type1_findings, type1_files = _run_type1_scan(root, all_tracked, cooled)
    type23_findings, type23_files = _run_type23_scan(root, initiatives, cooled)
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
        cooled=cooled,
        cooling_findings=cooling_findings,
        cooling_records=tuple(cooling_records),
        cooling_module=cooling_modules[0] if cooling_modules else None,
        now=moment,
    )


def analyze_bounded(
    root: Path,
    autonomous_dispatch: bool = False,
    now: datetime.datetime | None = None,
) -> WorkspaceStatusResult:
    """Run bounded workspace-status analysis (Type 2+3 only; no global spec walk).

    Used by 'status' and 'explain' subcommands. Structurally guarantees no Type 1
    scan: calls _run_type23_scan only, never _run_type1_scan. Path confinement is
    preserved — _run_type23_scan routes all path resolution through _safe_spec_path().

    autonomous_dispatch=True applies conservative needs-resolution semantics (see
    is_need_satisfied and SKILL.md §2). workspace_status() passes autonomous_dispatch=True.
    """
    t0 = time.monotonic()
    moment = now if now is not None else datetime.datetime.now(datetime.UTC)
    cooling_records: list[Any] = []
    cooling_modules: list[Any] = []
    cooled, cooling_findings = _resolve_cooled_state(
        root, cooling_records, cooling_modules
    )

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

    type23_findings, declared_files = _run_type23_scan(root, initiatives, cooled)
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
        cooled=cooled,
        cooling_findings=cooling_findings,
        cooling_records=tuple(cooling_records),
        cooling_module=cooling_modules[0] if cooling_modules else None,
        now=moment,
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


# ── Legacy migration planning ────────────────────────────────────────────────

_MIGRATION_SELECTION_FIELDS = frozenset({
    "contract_version",
    "legacy_finding_id",
    "workspace_fingerprint",
    "source_membership",
    "target_entry",
    "target_membership",
    "owning_processor",
    "provenance_reference",
    "legacy_content_approved_for_ledger",
})
_MIGRATION_SOURCE_COLLECTIONS = frozenset({
    "work.queue",
    "work.active",
    "work.shipped",
    "shaping_queue.active",
    "shaping_queue.backlog",
    "brief_queue.draft",
    "brief_queue.ready",
    "brief_queue.executing",
    "brief_queue.shipped",
    "brief_queue.withdrawn",
    "brief_queue.cancelled",
    "backlog.open",
})
_MIGRATION_TARGET_COLLECTIONS = _MIGRATION_SOURCE_COLLECTIONS | {"backlog.closed"}
_MIGRATION_RESULT_CODES = frozenset({
    "planned",
    "artifact_missing",
    "manual_routing_required",
    "applied",
    "already_applied",
    "rolled_back",
    "already_rolled_back",
    "workspace_absent",
    "invalid_selection",
    "unsafe_path",
    "legacy_finding_missing",
    "selection_mismatch",
    "target_invalid",
    "privacy_review_required",
    "sensitive_legacy_content",
    "artifact_changed",
    "migration_policy_invalid",
    "confirmation_invalid",
    "confirmation_stale",
    "confirmation_reused",
    "confirmation_binding_mismatch",
    "unauthorized_approver",
    "ledger_invalid",
    "ledger_changed",
    "operation_missing",
    "operation_state_conflict",
    "workspace_changed",
    "lock_busy",
    "write_failed",
    "recovery_conflict",
    "dependency_unavailable",
})
_MIGRATION_PROCESSOR_RE = re.compile(r"^[a-z][a-z0-9-]{0,99}$")
_MIGRATION_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_MIGRATION_CREDENTIAL_PATTERNS = (
    re.compile(
        rb"\b(password|passwd|pwd|secret|client_secret|api_key|apikey|"
        rb"access_token|refresh_token|auth_token|bearer|private_key)\b"
        rb"\s*[:=]\s*[^\s#]+",
        re.IGNORECASE,
    ),
    re.compile(rb"\bauthorization\s*[:=]\s*(basic|bearer)\s+\S+", re.IGNORECASE),
    re.compile(
        rb"[?&](access_token|api_key|private_token|auth|token)=[^&#\s]+",
        re.IGNORECASE,
    ),
    re.compile(rb"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(rb"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(rb"(?:AKIA|ASIA)[A-Z0-9]{16}"),
)


def _migration_canonical_json(value: object) -> bytes:
    """Serialize deterministic runtime-neutral migration identity input."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _migration_entry_dict(entry: WorkspaceEntry) -> dict[str, object]:
    """Project a typed Group 2 entry back to its closed JSON shape."""
    return {
        "path": entry.path,
        "kind": entry.kind,
        "source": {
            key: value
            for key, value in dataclasses.asdict(entry.source).items()
            if value is not None and key not in {"locator", "object_type"}
        },
        "summary": entry.summary,
        "needs": [dataclasses.asdict(need) for need in entry.needs],
    }


def _migration_membership_valid(raw: object, *, target: bool) -> bool:
    """Validate a closed source or target lifecycle membership object."""
    required = {"ini_slug", "collection"}
    if not target:
        required |= {"entry_index", "legacy_slice_digest"}
    if not isinstance(raw, dict) or set(raw) != required:
        return False
    ini_slug = raw.get("ini_slug")
    if not isinstance(ini_slug, str) or len(ini_slug) > 200:
        return False
    if re.fullmatch(r"[a-z0-9-]*", ini_slug) is None:
        return False
    collections = _MIGRATION_TARGET_COLLECTIONS if target else _MIGRATION_SOURCE_COLLECTIONS
    if raw.get("collection") not in collections:
        return False
    if target:
        return True
    return (
        isinstance(raw.get("entry_index"), int)
        and not isinstance(raw.get("entry_index"), bool)
        and raw["entry_index"] >= 0
        and isinstance(raw.get("legacy_slice_digest"), str)
        and _MIGRATION_SHA256_RE.fullmatch(raw["legacy_slice_digest"]) is not None
    )


def _migration_target_membership_possible(kind: str, collection: str) -> bool:
    """Return whether a selected target kind can inhabit the lifecycle collection."""
    if collection.startswith("work."):
        return kind in {"spec", "defect"}
    if collection.startswith("brief_queue."):
        return kind == "brief"
    if collection.startswith("shaping_queue."):
        return kind in {"intent", "research", "design"}
    if collection.startswith("backlog."):
        return kind in WORKSPACE_ARTIFACT_KINDS
    return False


def validate_migration_selection(
    raw: object,
) -> tuple[MigrationSelection | None, str | None]:
    """Validate the closed reviewed selection without reading repository state."""
    if not isinstance(raw, dict) or set(raw) != _MIGRATION_SELECTION_FIELDS:
        return None, "invalid_selection"
    if raw.get("contract_version") != "work-intake-migration-selection.v1":
        return None, "invalid_selection"
    finding_id = raw.get("legacy_finding_id")
    fingerprint = raw.get("workspace_fingerprint")
    if (
        not isinstance(finding_id, str)
        or not 1 <= len(finding_id) <= 500
        or "\n" in finding_id
        or "\r" in finding_id
        or not isinstance(fingerprint, str)
        or _MIGRATION_SHA256_RE.fullmatch(fingerprint) is None
    ):
        return None, "invalid_selection"
    source_membership = raw.get("source_membership")
    target_membership = raw.get("target_membership")
    if not _migration_membership_valid(source_membership, target=False):
        return None, "invalid_selection"
    if not _migration_membership_valid(target_membership, target=True):
        return None, "invalid_selection"
    target_entry_raw = raw.get("target_entry")
    target_entry, findings = parse_workspace_entry(target_entry_raw)
    if findings or target_entry is None:
        return None, "target_invalid"
    if not _migration_target_membership_possible(
        target_entry.kind, str(target_membership["collection"])
    ):
        return None, "target_invalid"
    processor = raw.get("owning_processor")
    provenance = raw.get("provenance_reference")
    if not isinstance(processor, str) or _MIGRATION_PROCESSOR_RE.fullmatch(processor) is None:
        return None, "invalid_selection"
    if (
        not isinstance(provenance, str)
        or not 1 <= len(provenance) <= 1000
        or "\n" in provenance
        or "\r" in provenance
    ):
        return None, "invalid_selection"
    if raw.get("legacy_content_approved_for_ledger") is not True:
        return None, "privacy_review_required"
    expected_provenance = {
        target_entry.path,
        target_entry.source.ref,
        target_entry.source.parent,
    }
    if provenance not in expected_provenance:
        return None, "selection_mismatch"
    return MigrationSelection(
        legacy_finding_id=finding_id,
        workspace_fingerprint=fingerprint,
        source_membership=dict(source_membership),
        target_entry=target_entry,
        target_entry_raw=dict(target_entry_raw),
        target_membership=dict(target_membership),
        owning_processor=processor,
        provenance_reference=provenance,
        legacy_content_approved_for_ledger=True,
    ), None


def migration_selection_digest(selection: MigrationSelection) -> str:
    """Bind every closed reviewed-selection field to one stable digest."""
    content = {
        "contract_version": "work-intake-migration-selection.v1",
        "legacy_finding_id": selection.legacy_finding_id,
        "workspace_fingerprint": selection.workspace_fingerprint,
        "source_membership": selection.source_membership,
        "target_entry": selection.target_entry_raw,
        "target_membership": selection.target_membership,
        "owning_processor": selection.owning_processor,
        "provenance_reference": selection.provenance_reference,
        "legacy_content_approved_for_ledger": (
            selection.legacy_content_approved_for_ledger
        ),
    }
    return hashlib.sha256(_migration_canonical_json(content)).hexdigest()


def migration_candidate_routes(entry: LegacyWorkspaceEntry) -> list[dict[str, object]]:
    """Return explicit candidate route classes without selecting among them."""
    kinds: tuple[str, ...]
    collections: tuple[str, ...]
    if entry.collection.startswith("work."):
        kinds = ("spec", "defect")
        collections = ("work.queue", "work.active", "work.shipped")
    elif entry.collection.startswith("brief_queue."):
        kinds = ("brief",)
        collections = (
            "brief_queue.draft",
            "brief_queue.ready",
            "brief_queue.executing",
            "brief_queue.shipped",
            "brief_queue.withdrawn",
            "brief_queue.cancelled",
        )
    elif entry.collection.startswith("shaping_queue."):
        kinds = ("intent", "research", "design")
        collections = ("shaping_queue.active", "shaping_queue.backlog")
    else:
        kinds = WORKSPACE_ARTIFACT_KINDS
        collections = ("backlog.open", "backlog.closed")
    return [
        {"kind": kind, "target_collections": list(collections)}
        for kind in kinds
    ]


def _migration_legacy_context_safe(entry: LegacyWorkspaceEntry) -> bool:
    """Reject untrusted legacy dependency prose from exact CLI projection."""
    patterns = (
        re.compile(r"^work:spec/[a-z0-9][a-z0-9-]*$"),
        re.compile(r"^(?:shape|research|strategy|backlog):[a-z0-9][a-z0-9-]*$"),
        re.compile(r"^brief:docs/product/briefs/[a-z0-9][a-z0-9-]*\.md$"),
        re.compile(r"^ini-[0-9]{3}:work:spec/[a-z0-9][a-z0-9-]*$"),
    )
    return all(any(pattern.fullmatch(need) for pattern in patterns) for need in entry.needs)


def _toml_without_comments(value: str) -> str:
    """Remove TOML comments from a small array element for span classification."""
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
            continue
        if char in {'"', "'"}:
            quote = char
            output.append(char)
        elif char == "#":
            in_comment = True
        else:
            output.append(char)
    return "".join(output)


def extract_legacy_source_slice(
    workspace_bytes: bytes,
    ini_slug: str,
    collection: str,
    entry_index: int,
) -> str | None:
    """Return the exact UTF-8 TOML element slice, including comments and comma."""
    try:
        text = workspace_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None
    section_name, key = collection.split(".", 1)
    if ini_slug:
        escaped_ini = re.escape(ini_slug)
        escaped_section = re.escape(section_name)
        header = re.compile(
            rf"(?m)^\[(?:\"{escaped_ini}\"|{escaped_ini})\.{escaped_section}\]\s*$"
        )
    else:
        header = re.compile(rf"(?m)^\[{re.escape(section_name)}\]\s*$")
    match = header.search(text)
    if match is None:
        return None
    next_header = re.search(r"(?m)^\[[^\n]+\]\s*$", text[match.end():])
    block_end = match.end() + next_header.start() if next_header else len(text)
    assignment = re.search(
        rf"(?m)^[ \t]*{re.escape(key)}[ \t]*=[ \t]*",
        text[match.end():block_end],
    )
    if assignment is None:
        return None
    value_start = match.end() + assignment.end()
    if value_start >= len(text):
        return None
    if text[value_start] != "[":
        line_end = text.find("\n", value_start)
        line_end = len(text) if line_end < 0 else line_end + 1
        return text[value_start:line_end] if entry_index == 0 else None

    body_start = value_start + 1
    segments: list[str] = []
    segment_start = body_start
    square_depth = 0
    brace_depth = 0
    quote = ""
    escaped = False
    in_comment = False
    index = body_start
    while index < block_end:
        char = text[index]
        if in_comment:
            if char == "\n":
                in_comment = False
            index += 1
            continue
        if quote:
            if escaped:
                escaped = False
            elif char == "\\" and quote == '"':
                escaped = True
            elif char == quote:
                quote = ""
            index += 1
            continue
        if char in {'"', "'"}:
            quote = char
        elif char == "#":
            in_comment = True
        elif char == "[":
            square_depth += 1
        elif char == "]":
            if square_depth == 0 and brace_depth == 0:
                tail = text[segment_start:index]
                if _toml_without_comments(tail).strip():
                    segments.append(tail)
                elif segments:
                    segments[-1] += tail
                break
            square_depth -= 1
        elif char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth -= 1
        elif char == "," and square_depth == 0 and brace_depth == 0:
            segment = text[segment_start:index + 1]
            if _toml_without_comments(segment).strip().rstrip(",").strip():
                segments.append(segment)
            segment_start = index + 1
        index += 1
    if not 0 <= entry_index < len(segments):
        return None
    return segments[entry_index]


def _legacy_finding_id(
    ini_slug: str, collection: str, entry_index: int, slice_digest: str
) -> str:
    """Return a stable identifier for one exact legacy membership."""
    identity = {
        "ini_slug": ini_slug,
        "collection": collection,
        "entry_index": entry_index,
        "legacy_slice_digest": slice_digest,
    }
    return "legacy-" + hashlib.sha256(_migration_canonical_json(identity)).hexdigest()


def legacy_slice_contains_sensitive_content(legacy_slice: bytes) -> bool:
    """Apply the frozen no-echo credential detector to an exact raw slice."""
    return any(
        pattern.search(legacy_slice) is not None
        for pattern in _MIGRATION_CREDENTIAL_PATTERNS
    )


def scan_legacy_slice_for_sensitive_content(legacy_slice: bytes) -> bool:
    """Compatibility name for the frozen, non-echoing credential detector."""
    return legacy_slice_contains_sensitive_content(legacy_slice)


def build_migration_finding(
    workspace_bytes: bytes,
    membership: LegacyWorkspaceMembership,
) -> dict[str, object]:
    """Build a non-dispatchable review finding bound to the exact TOML slice."""
    legacy_slice = extract_legacy_source_slice(
        workspace_bytes,
        membership.ini_slug,
        membership.collection,
        membership.entry_index,
    )
    if legacy_slice is None:
        return {
            "code": "manual_routing_required",
            "dispatchable": False,
            "next_action": "route-manually",
        }
    encoded = legacy_slice.encode("utf-8")
    slice_digest = hashlib.sha256(encoded).hexdigest()
    source_membership = {
        "ini_slug": membership.ini_slug,
        "collection": membership.collection,
        "entry_index": membership.entry_index,
        "legacy_slice_digest": slice_digest,
    }
    sensitive = legacy_slice_contains_sensitive_content(encoded)
    unsafe_context = not _migration_legacy_context_safe(membership.entry)
    return {
        "code": (
            "sensitive_legacy_content"
            if sensitive
            else "manual_routing_required" if unsafe_context else "legacy_entry"
        ),
        "legacy_finding_id": _legacy_finding_id(
            membership.ini_slug,
            membership.collection,
            membership.entry_index,
            slice_digest,
        ),
        "source_membership": source_membership,
        "source_representation": None if sensitive or unsafe_context else legacy_slice,
        "candidate_routes": migration_candidate_routes(membership.entry),
        "dispatchable": False,
        "next_action": (
            "sanitize-legacy-source"
            if sensitive
            else "route-manually" if unsafe_context else "review-migration-selection"
        ),
    }


def confine_migration_path(
    root: Path,
    relative_path: str,
    *,
    require_file: bool = False,
) -> Path | None:
    """Resolve a repository-relative path while refusing link and alias escapes."""
    if not _is_repository_relative_path(relative_path):
        return None
    try:
        resolved_root = root.resolve(strict=True)
        if not resolved_root.is_dir() or root.is_symlink():
            return None
        candidate = resolved_root.joinpath(*relative_path.split("/"))
        cursor = resolved_root
        for part in relative_path.split("/"):
            cursor = cursor / part
            if cursor.exists() or cursor.is_symlink():
                info = cursor.lstat()
                if stat.S_ISLNK(info.st_mode):
                    return None
                reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
                if reparse and getattr(info, "st_file_attributes", 0) & reparse:
                    return None
        resolved = candidate.resolve(strict=require_file)
        resolved.relative_to(resolved_root)
        if require_file:
            before = resolved.stat()
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                return None
        return resolved
    except (FileNotFoundError, NotADirectoryError, OSError, RuntimeError, ValueError):
        return None


def _migration_file_bytes(root: Path, relative_path: str) -> bytes | None:
    """Read a confined regular single-link file with pre/post identity checks."""
    path = confine_migration_path(root, relative_path, require_file=True)
    if path is None:
        return None
    descriptor: int | None = None
    try:
        before = path.stat()
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            return None
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
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


def _migration_file_fingerprint(root: Path, relative_path: str) -> str | None:
    """Fingerprint a guarded migration file without a second path-based read."""
    content = _migration_file_bytes(root, relative_path)
    return hashlib.sha256(content).hexdigest() if content is not None else None


def build_migration_result(
    result_code: str,
    *,
    next_action: str,
    operation_id: str | None = None,
    operation_digest: str | None = None,
    ledger_state: str | None = None,
) -> dict[str, object]:
    """Build one closed migration-result object with stable applicability flags."""
    if result_code not in _MIGRATION_RESULT_CODES:
        raise ValueError("unknown migration result code")
    if _MIGRATION_PROCESSOR_RE.fullmatch(next_action) is None:
        raise ValueError("invalid migration next action")
    applicable = result_code in {
        "planned",
        "applied",
        "already_applied",
        "rolled_back",
        "already_rolled_back",
    }
    mutated = result_code in {"applied", "rolled_back"}
    result: dict[str, object] = {
        "contract_version": "work-intake-migration-result.v1",
        "result_code": result_code,
        "applicable": applicable,
        "mutated": mutated,
        "next_action": next_action,
    }
    if operation_id is not None:
        result["operation_id"] = operation_id
    if operation_digest is not None:
        result["operation_digest"] = operation_digest
    if ledger_state is not None:
        result["ledger_state"] = ledger_state
    return result


def _migration_operation_digest(
    operation: dict[str, object], repository_identity: str
) -> str:
    """Bind immutable reviewed operation material to its ledger repository."""
    content = {
        "repository_identity": repository_identity,
        **{
            key: operation[key]
            for key in (
            "workspace_path",
            "pre_apply_workspace_fingerprint",
            "selection_digest",
            "source_membership",
                "legacy_slice",
                "target_entry",
                "target_membership",
                "owning_processor",
                "artifact_receipt",
            )
        },
    }
    return hashlib.sha256(_migration_canonical_json(content)).hexdigest()


def compute_migration_plan(
    root: Path,
    workspace_path: Path,
    selection_raw: object,
) -> MigrationPlan:
    """Build a deterministic migration operation without creating durable state."""
    selection, error = validate_migration_selection(selection_raw)
    if selection is None:
        return MigrationPlan(
            result=build_migration_result(
                error or "invalid_selection", next_action="revise-selection"
            )
        )
    confined_workspace = confine_migration_path(root, "workspace.toml", require_file=True)
    if confined_workspace is None:
        return MigrationPlan(
            result=build_migration_result("unsafe_path", next_action="repair-repository-paths")
        )
    try:
        if workspace_path.resolve(strict=True) != confined_workspace:
            return MigrationPlan(
                result=build_migration_result("unsafe_path", next_action="repair-repository-paths")
            )
        workspace_bytes = _migration_file_bytes(root, "workspace.toml")
        if workspace_bytes is None:
            raise OSError("guarded workspace read failed")
        workspace = tomllib.loads(workspace_bytes.decode("utf-8"))
    except (OSError, RuntimeError, UnicodeDecodeError, tomllib.TOMLDecodeError, ValueError):
        return MigrationPlan(
            result=build_migration_result("unsafe_path", next_action="repair-repository-paths")
        )
    workspace_fingerprint = hashlib.sha256(workspace_bytes).hexdigest()
    if selection.workspace_fingerprint != workspace_fingerprint:
        return MigrationPlan(
            result=build_migration_result(
                "selection_mismatch", next_action="review-current-workspace"
            )
        )
    canonical = run_canonical_reconciliation(workspace, root)
    matches = [
        membership
        for membership in canonical.legacy_memberships
        if membership.ini_slug == selection.source_membership["ini_slug"]
        and membership.collection == selection.source_membership["collection"]
        and membership.entry_index == selection.source_membership["entry_index"]
    ]
    if len(matches) != 1:
        return MigrationPlan(
            result=build_migration_result(
                "legacy_finding_missing", next_action="review-current-workspace"
            )
        )
    finding = build_migration_finding(workspace_bytes, matches[0])
    if finding.get("code") == "sensitive_legacy_content":
        return MigrationPlan(
            result=build_migration_result(
                "sensitive_legacy_content", next_action="sanitize-legacy-source"
            ),
            finding=finding,
        )
    if finding.get("code") == "manual_routing_required":
        return MigrationPlan(
            result=build_migration_result(
                "manual_routing_required", next_action="route-manually"
            ),
            finding=finding,
        )
    source = finding.get("source_membership")
    if (
        finding.get("legacy_finding_id") != selection.legacy_finding_id
        or source != selection.source_membership
    ):
        return MigrationPlan(
            result=build_migration_result("selection_mismatch", next_action="revise-selection"),
            finding=finding,
        )
    target_ini = selection.target_membership["ini_slug"]
    target_collection = selection.target_membership["collection"]
    target_section, target_list = target_collection.split(".", 1)
    if target_section == "backlog":
        target_container = workspace.get("backlog") if target_ini == "" else None
    else:
        initiative = workspace.get(target_ini)
        target_container = (
            initiative.get(target_section) if isinstance(initiative, dict) else None
        )
    if not isinstance(target_container, dict) or target_list not in target_container:
        return MigrationPlan(
            result=build_migration_result("target_invalid", next_action="revise-selection"),
            finding=finding,
        )
    target_path = selection.target_entry.path
    target = confine_migration_path(root, target_path, require_file=False)
    if target is None:
        return MigrationPlan(
            result=build_migration_result("unsafe_path", next_action="repair-repository-paths"),
            finding=finding,
        )
    if not target.exists():
        return MigrationPlan(
            result=build_migration_result(
                "artifact_missing", next_action=selection.owning_processor
            ),
            finding=finding,
        )
    artifact_fingerprint = _migration_file_fingerprint(root, target_path)
    if artifact_fingerprint is None:
        return MigrationPlan(
            result=build_migration_result("unsafe_path", next_action="repair-repository-paths"),
            finding=finding,
        )
    if selection.target_entry.kind == "spec":
        plan_path = str(PurePosixPath(target_path).with_name("plan.md"))
        if _migration_file_fingerprint(root, plan_path) is None:
            return MigrationPlan(
                result=build_migration_result(
                    "artifact_missing", next_action=selection.owning_processor
                ),
                finding=finding,
            )
    duplicates = [
        membership
        for membership in canonical.memberships
        if membership.entry.path == target_path
    ]
    if duplicates:
        return MigrationPlan(
            result=build_migration_result("target_invalid", next_action="resolve-duplicate-route"),
            finding=finding,
        )
    operation_content = {
        "workspace_path": "workspace.toml",
        "pre_apply_workspace_fingerprint": workspace_fingerprint,
        "selection_digest": migration_selection_digest(selection),
        "source_membership": dict(selection.source_membership),
        "legacy_slice": finding["source_representation"],
        "target_entry": dict(selection.target_entry_raw),
        "target_membership": dict(selection.target_membership),
        "owning_processor": selection.owning_processor,
        "artifact_receipt": {
            "path": target_path,
            "fingerprint": artifact_fingerprint,
            "existed_before_apply": True,
            "processor": selection.owning_processor,
        },
    }
    repository_identity = canonical_repository_identity(workspace, canonical, root)
    operation_digest = _migration_operation_digest(
        operation_content, repository_identity
    )
    operation_id = f"migration-{operation_digest}"
    operation = {
        "operation_id": operation_id,
        "operation_digest": operation_digest,
        **operation_content,
        "state": "pending",
        "confirmation_receipts": [],
    }
    return MigrationPlan(
        result=build_migration_result(
            "planned",
            next_action="confirm-migration",
            operation_id=operation_id,
            operation_digest=operation_digest,
            ledger_state="absent",
        ),
        finding=finding,
        proposed_operation=operation,
    )


def validate_migration_ledger_invariants(ledger: object) -> str | None:
    """Return the exact semantic-invariant refusal code, or ``None`` when valid."""
    if not isinstance(ledger, dict) or not isinstance(ledger.get("operations"), list):
        return "ledger_invalid"
    repository_identity = ledger.get("repository_identity")
    if (
        not isinstance(repository_identity, str)
        or _MIGRATION_SHA256_RE.fullmatch(repository_identity) is None
    ):
        return "ledger_invalid"
    operation_ids: set[str] = set()
    confirmation_ids: set[str] = set()
    subjects: set[str] = set()
    for operation in ledger["operations"]:
        if not isinstance(operation, dict):
            return "ledger_invalid"
        operation_id = operation.get("operation_id")
        operation_digest = operation.get("operation_digest")
        if not isinstance(operation_id, str) or operation_id in operation_ids:
            return "ledger_invalid"
        operation_ids.add(operation_id)
        receipts = operation.get("confirmation_receipts")
        if not isinstance(receipts, list):
            return "operation_state_conflict"
        actions: list[str] = []
        for receipt in receipts:
            if not isinstance(receipt, dict):
                return "operation_state_conflict"
            confirmation_id = receipt.get("confirmation_id")
            subject = receipt.get("authorization_subject")
            if confirmation_id in confirmation_ids or subject in subjects:
                return "confirmation_reused"
            if not isinstance(confirmation_id, str) or not isinstance(subject, str):
                return "confirmation_reused"
            confirmation_ids.add(confirmation_id)
            subjects.add(subject)
            if (
                receipt.get("operation_id") != operation_id
                or receipt.get("operation_digest") != operation_digest
            ):
                return "confirmation_binding_mismatch"
            action = receipt.get("action")
            if action not in {"apply", "rollback"}:
                return "operation_state_conflict"
            actions.append(action)
        if not actions or actions[0] != "apply":
            return "operation_state_conflict"
        rollback_at = next((i for i, action in enumerate(actions) if action == "rollback"), None)
        if rollback_at is not None and any(action == "apply" for action in actions[rollback_at:]):
            return "operation_state_conflict"
        state = operation.get("state")
        expected_states = {
            "pending": rollback_at is None,
            "applied": rollback_at is None,
            "rollback_pending": rollback_at is not None,
            "rolled_back": rollback_at is not None,
        }
        if state not in expected_states or not expected_states[state]:
            return "operation_state_conflict"
    for operation in ledger["operations"]:
        try:
            expected_digest = _migration_operation_digest(
                operation, repository_identity
            )
        except (KeyError, TypeError, ValueError):
            return "ledger_invalid"
        if operation.get("operation_digest") != expected_digest:
            return "ledger_invalid"
    return None


def validate_migration_ledger_shape(ledger: object) -> str | None:
    """Validate the closed ledger shape before cross-record invariant checks."""
    if not isinstance(ledger, dict) or set(ledger) != {
        "contract_version",
        "repository_identity",
        "operations",
    }:
        return "ledger_invalid"
    if ledger.get("contract_version") != "work-intake-migration-ledger.v1":
        return "ledger_invalid"
    repository_identity = ledger.get("repository_identity")
    operations = ledger.get("operations")
    if (
        not isinstance(repository_identity, str)
        or _MIGRATION_SHA256_RE.fullmatch(repository_identity) is None
        or not isinstance(operations, list)
        or len(operations) > 10000
    ):
        return "ledger_invalid"
    required_operation = {
        "operation_id",
        "operation_digest",
        "workspace_path",
        "pre_apply_workspace_fingerprint",
        "selection_digest",
        "source_membership",
        "legacy_slice",
        "target_entry",
        "target_membership",
        "owning_processor",
        "artifact_receipt",
        "state",
        "confirmation_receipts",
    }
    optional_operation = {
        "applied_workspace_fingerprint",
        "rolled_back_workspace_fingerprint",
    }
    receipt_fields = {
        "confirmation_id",
        "action",
        "operation_id",
        "operation_digest",
        "authorization_subject",
        "authorization_role_digest",
        "confirmed_at",
        "authorization_source",
        "consumed_before_effect",
    }
    for operation in operations:
        if (
            not isinstance(operation, dict)
            or not required_operation.issubset(operation)
            or set(operation) - required_operation - optional_operation
        ):
            return "ledger_invalid"
        operation_id = operation.get("operation_id")
        operation_digest = operation.get("operation_digest")
        if (
            not isinstance(operation_id, str)
            or re.fullmatch(r"migration-[a-f0-9]{64}", operation_id) is None
            or not isinstance(operation_digest, str)
            or _MIGRATION_SHA256_RE.fullmatch(operation_digest) is None
            or operation.get("workspace_path") != "workspace.toml"
            or not isinstance(operation.get("pre_apply_workspace_fingerprint"), str)
            or _MIGRATION_SHA256_RE.fullmatch(
                operation["pre_apply_workspace_fingerprint"]
            ) is None
            or not isinstance(operation.get("selection_digest"), str)
            or _MIGRATION_SHA256_RE.fullmatch(operation["selection_digest"]) is None
            or not _migration_membership_valid(
                operation.get("source_membership"), target=False
            )
            or not _migration_membership_valid(
                operation.get("target_membership"), target=True
            )
        ):
            return "ledger_invalid"
        legacy_slice = operation.get("legacy_slice")
        if not isinstance(legacy_slice, str) or not 1 <= len(legacy_slice) <= 1_000_000:
            return "ledger_invalid"
        target_entry, target_findings = parse_workspace_entry(operation.get("target_entry"))
        if target_entry is None or target_findings:
            return "ledger_invalid"
        if not _migration_target_membership_possible(
            target_entry.kind, str(operation["target_membership"]["collection"])
        ):
            return "ledger_invalid"
        processor = operation.get("owning_processor")
        artifact = operation.get("artifact_receipt")
        if (
            not isinstance(processor, str)
            or _MIGRATION_PROCESSOR_RE.fullmatch(processor) is None
            or not isinstance(artifact, dict)
            or set(artifact) != {
                "path", "fingerprint", "existed_before_apply", "processor"
            }
            or artifact.get("path") != target_entry.path
            or artifact.get("existed_before_apply") is not True
            or artifact.get("processor") != processor
            or not isinstance(artifact.get("fingerprint"), str)
            or _MIGRATION_SHA256_RE.fullmatch(artifact["fingerprint"]) is None
        ):
            return "ledger_invalid"
        state = operation.get("state")
        if state not in {"pending", "applied", "rollback_pending", "rolled_back"}:
            return "ledger_invalid"
        if state in {"applied", "rollback_pending", "rolled_back"}:
            applied = operation.get("applied_workspace_fingerprint")
            if not isinstance(applied, str) or _MIGRATION_SHA256_RE.fullmatch(applied) is None:
                return "ledger_invalid"
        if state == "rolled_back":
            rolled_back = operation.get("rolled_back_workspace_fingerprint")
            if (
                not isinstance(rolled_back, str)
                or _MIGRATION_SHA256_RE.fullmatch(rolled_back) is None
            ):
                return "ledger_invalid"
        receipts = operation.get("confirmation_receipts")
        if not isinstance(receipts, list) or not 1 <= len(receipts) <= 100:
            return "ledger_invalid"
        for receipt in receipts:
            if not isinstance(receipt, dict) or set(receipt) != receipt_fields:
                return "ledger_invalid"
            if (
                re.fullmatch(
                    r"confirmation-[a-f0-9]{32}", str(receipt.get("confirmation_id"))
                ) is None
                or receipt.get("action") not in {"apply", "rollback"}
                or re.fullmatch(
                    r"migration-[a-f0-9]{64}", str(receipt.get("operation_id"))
                ) is None
                or _MIGRATION_SHA256_RE.fullmatch(
                    str(receipt.get("operation_digest"))
                ) is None
                or re.fullmatch(
                    r"subject-[a-f0-9]{32}", str(receipt.get("authorization_subject"))
                ) is None
                or _MIGRATION_SHA256_RE.fullmatch(
                    str(receipt.get("authorization_role_digest"))
                ) is None
                or not isinstance(receipt.get("confirmed_at"), str)
                or receipt.get("authorization_source") != "current-human-session"
                or receipt.get("consumed_before_effect") is not True
            ):
                return "ledger_invalid"
            try:
                confirmed = datetime.datetime.fromisoformat(
                    receipt["confirmed_at"].replace("Z", "+00:00")
                )
            except ValueError:
                return "ledger_invalid"
            if confirmed.tzinfo is None:
                return "ledger_invalid"
    return validate_migration_ledger_invariants(ledger)


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
