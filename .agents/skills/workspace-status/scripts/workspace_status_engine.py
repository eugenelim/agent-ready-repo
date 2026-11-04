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
import errno
import hashlib
import importlib
import importlib.util
import json
import os
import re
import stat
import sys
import time
import tomllib
from collections.abc import Iterator
from pathlib import Path
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
SOURCE_MODES = ("repo-origin", "tracker-origin")

_WORKSPACE_ENTRY_FIELDS = frozenset(
    (*WORKSPACE_ENTRY_REQUIRED_FIELDS, *WORKSPACE_ENTRY_OPTIONAL_FIELDS)
)
_SOURCE_FIELDS = frozenset(
    {"mode", "ref", "revision", "parent", "coordination", "tracker_profile"}
)
_LOCAL_NEED_FIELDS = frozenset({"type", "kind", "path"})
_LOCAL_NEED_ALLOWED_FIELDS = frozenset({*_LOCAL_NEED_FIELDS, "receipt"})
_COMPLETION_RECEIPT_FIELDS = frozenset(
    {"delivery_id", "outcome", "completion_event", "evidence_ref"}
)
_MALFORMED_COMPLETION_RECEIPT = "malformed-completion-receipt"
# Matches close-work's MAX_TEXT_LENGTH so the producer cannot write a receipt
# this parser then refuses. Bounded here rather than at satisfaction time: an
# unbounded value is serialized into the routing identity on every run, long
# before any grammar is applied to it.
_COMPLETION_RECEIPT_MAX_FIELD_LENGTH = 512
_COMPLETION_RECEIPT_DELIVERY_ID_RE = r"^[a-z0-9][a-z0-9-]{0,127}$"
_COMPLETION_RECEIPT_EVENTS = ("merge", "release", "acceptance")
_COMPLETION_RECEIPT_EVIDENCE_REF_RE = (
    r"^(?:commit:[0-9a-f]{40}|pr:[0-9]+|run:[0-9]+)$"
)
_COMPLETION_RECEIPT_OUTCOMES = frozenset({"completed", "abandoned", "superseded"})
_CROSS_REPO_NEED_FIELDS = frozenset(
    {"type", "kind", "path", "containing_brief", "receipt_id", "accepted_revision"}
)
_FINDING_NEXT_ACTIONS = {
    "invalid_workspace": "Correct workspace.toml, then run `repair-plan` again.",
    "invalid_entry": "Rewrite the entry to the accepted target contract.",
    "legacy_entry": "Materialize and register a canonical target entry.",
    "unsupported_legacy": "Route the item manually; do not infer a target entry.",
    "invalid_artifact_path": "Replace it with a confined canonical repository-relative path.",
    "missing_artifact": "Create and review the canonical artifact before dispatch.",
    "unreadable_artifact": "Restore readable repository state, then run `repair-plan` again.",
    "invalid_captured_item": (
        "Fix the named field of that captured-item file, then run `repair-plan` again."
    ),
    "unmigrated_captured_item": (
        "Run workspace-status repair-plan to move this captured item into its "
        "own file under docs/product/captured/."
    ),
    "missing_plan": "Create and approve the plan before dispatch.",
    "unapproved_spec": "Complete the spec approval gate.",
    "duplicate_membership": (
        "Remove the duplicate after choosing the authoritative membership."
    ),
    "impossible_transition": (
        "Correct the artifact or membership through a reviewed transition."
    ),
    "provenance_mismatch": (
        "Resolve provenance in the canonical artifact and mirror it deliberately."
    ),
    "cooled_child_scope_unknown": (
        "Set parent on the spec's lifecycle record: a resolving brief path, or "
        "none only when that spec has no parent brief; a tracker-origin entry "
        "declares source.parent instead."
    ),
    "refresh_conflict": "Resolve the conflict through the artifact's authority workflow.",
    "unsatisfied_dependency": "Complete or explicitly revise the dependency.",
    "missing_dependency": "Materialize or correct the dependency target.",
    "dependency_cycle": "Break the cycle through an explicit plan change.",
    "invalid_dependency": (
        "Rewrite the item as a typed reference or a captured-item path, "
        "or correct its receipt, in the waiting item's header."
    ),
    "unmigrated_needs": (
        "Move the entry's needs into the waiting item's Depends on: header "
        "with workspace-status repair-plan, then repair-apply."
    ),
    "invalid_receipt": (
        "Replace it with a reviewed receipt matching the pinned dependency."
    ),
    "invalid_completion_receipt": (
        "Replace it with a valid reviewed completion receipt for that dependency."
    ),
    "inactive_initiative": (
        "Reactivate the initiative explicitly or move the work through governance."
    ),
    "configuration_mismatch": (
        "Install or select a consistent versioned configuration, then rerun."
    ),
    "invalid_source_authority": (
        "Correct the closed source-authority block, then run `repair-plan` again."
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
    receipt: dict[str, str] | str | None = None


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
class ParseBlockedWorkspaceMembership:
    """One target-like entry whose safe artifact identity survived parsing."""

    canonical_artifact_path: str
    ini_slug: str
    collection: str
    entry_index: int


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
    # Set only for a migrated captured membership, from its record: the record's
    # `Kind:`, or the one finding an invalid or unreadable record gives.
    captured_kind: str | None = None
    captured_finding: RoutingFinding | None = None


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
    # Each non-cooled local membership's header edges, keyed by waiting path.
    # They, not `entry.needs`, are what blocks and what the routing identity
    # fingerprints.
    header_edges: dict[str, tuple[Dependency, ...]] = dataclasses.field(
        default_factory=dict
    )


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
    # An open shaping or brief entry that no canonical parse accepted. Ordinary
    # reconciliation drops it from the typed lists above, so closeout reads this
    # flag to keep an unsupported entry from passing as an empty initiative.
    has_unsupported_open_entry: bool = False


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


# ── Group 2 contract parsing ──────────────────────────────────────────────────

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


# `\Z`, not `$`: in Python `$` also matches just before a trailing newline,
# so `brief:slug\n` matched and normalised through with the newline silently
# dropped, while a trailing tab, space or carriage return was refused. One
# character of the excluded set leaked because of the anchor.
_BRIEF_POINTER_RE = re.compile(r"^brief:(?P<slug>.*)\Z", re.S)


def _normalized_brief_pointer(value: str) -> str:
    """Normalize a well-formed `brief:<slug>` value to its canonical path.

    `brief:<slug>` is the canonical `Brief:` form. Normalizing
    here — before `_is_canonical_local_brief_path` runs — is what keeps that
    helper itself unrelaxed: it also guards `workspace.toml` entry and
    dependency paths, where a slug is meaningless and must keep failing. A
    malformed `brief:` value (wrong slug shape, a second colon, a space) is
    returned unchanged, so it falls through the existing checks and is
    refused exactly as before.
    """
    match = _BRIEF_POINTER_RE.match(value)
    if match and _SINGLE_SEGMENT_RE.fullmatch(match.group("slug")):
        return f"docs/product/briefs/{match.group('slug')}.md"
    return value


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
        keys = set(raw)
        if not _LOCAL_NEED_FIELDS.issubset(keys) or not keys.issubset(
            _LOCAL_NEED_ALLOWED_FIELDS
        ):
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
        receipt: dict[str, str] | str | None = None
        if "receipt" in raw:
            raw_receipt = raw.get("receipt")
            if (
                not isinstance(raw_receipt, dict)
                or set(raw_receipt) != _COMPLETION_RECEIPT_FIELDS
                or not all(
                    _is_bounded_text(value, _COMPLETION_RECEIPT_MAX_FIELD_LENGTH)
                    for value in raw_receipt.values()
                )
            ):
                receipt = _MALFORMED_COMPLETION_RECEIPT
            else:
                receipt = {field: raw_receipt[field] for field in _COMPLETION_RECEIPT_FIELDS}
        return Dependency(type="local", kind=kind, path=path, receipt=receipt), []
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
                and isinstance(entry_type, str)
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
            and isinstance(raw.get("type"), str)
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
    "b825a672cc70c674ac6d9b03cd05592621ea6f0cd765f271e05ea1c7d9c7a4a8"
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
            (
                dataclasses.asdict(need)
                for need in result.header_edges.get(entry.path or "", ())
            ),
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
        elif _captured_membership_form(entry.path) == "unmigrated":
            # An unmigrated captured item's file is never opened: its identity
            # comes from its membership and a constant marker.
            metadata = ArtifactMetadata(
                path=entry.path, kind=entry.kind, status=None, exists=True
            )
            status_fingerprint = _UNMIGRATED_IDENTITY_MARKER
        elif _captured_membership_form(entry.path) == "migrated":
            # A record reads only through the confined reader; one it cannot
            # read contributes a constant marker, never another file's content.
            metadata = _captured_record_metadata(root, entry)
            finding = metadata.captured_finding
            status_fingerprint = (
                _NONCONFINED_IDENTITY_MARKER
                if finding is not None and finding.code == "unreadable_artifact"
                else None
            )
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


def _confined_briefs_path(root: Path, rel_path: str) -> bool:
    """Whether `rel_path`, once resolved with symlinks followed, stays
    beneath the resolved `docs/product/briefs/` directory, which must itself
    stay beneath the resolved repository root.

    This boundary is stricter than `_confined_artifact_path`'s repository-root
    confinement: a brief path whose symlink resolves to another directory
    inside the repository passes repo-root confinement and must still be
    refused here, because the boundary is the briefs directory, not the
    repository root.

    Both halves are load-bearing, and neither replaces the other. Confining
    the candidate alone leaves the boundary itself unanchored: make
    `docs/product/briefs/` a symlink to an external directory and every
    target under it is correctly beneath the resolved briefs root while the
    root has escaped the repository.

    Both halves are strict. `relative_to` succeeds on equal paths, so each
    comparison rejects its equal case separately: a briefs root symlinked to
    the repository root would otherwise admit any file in the repository, and
    a target symlinked to the briefs directory is not a file beneath it.
    """
    try:
        root_resolved = root.resolve()
        briefs_root = (root_resolved / "docs" / "product" / "briefs").resolve()
        # The briefs root is confined before the candidate is resolved, so a
        # briefs root that already escaped never sends resolution walking
        # through an untrusted tree.
        if briefs_root == root_resolved:
            return False
        briefs_root.relative_to(root_resolved)
        candidate = (root_resolved / rel_path).resolve()
        if candidate == briefs_root:
            return False
        candidate.relative_to(briefs_root)
        return True
    except (OSError, RuntimeError, ValueError):
        return False


def _iter_preamble_lines(text: str) -> Iterator[str]:
    """Yield each preamble line with HTML comments hidden, in order.

    The preamble is the lines before the first `## ` heading, outside fenced
    blocks. A line that a fence or a multi-line comment hides is yielded as an
    empty string, so a caller that asks what directly follows a line never sees
    past hidden text.
    """
    fence_char: str | None = None
    fence_min_len = 0
    in_ml_comment = False
    for line in text.splitlines():
        if not in_ml_comment:
            fm = _FENCE_RE.match(line)
            if fm:
                marker = fm.group(1)
                char = marker[0]
                length = len(marker)
                if fence_char is None:
                    fence_char, fence_min_len = char, length
                    yield ""
                    continue
                rest = line[fm.end():]
                if char == fence_char and length >= fence_min_len and not rest.strip():
                    fence_char, fence_min_len = None, 0
                    yield ""
                    continue
        if fence_char is not None:
            yield ""
            continue
        if in_ml_comment:
            if "-->" in line:
                remainder = line[line.index("-->") + 3:]
                remainder_clean = _HTML_COMMENT_RE.sub("", remainder)
                in_ml_comment = "<!--" in remainder_clean
            yield ""
            continue
        if _SECTION_HEADING_RE.match(line):
            return
        clean = _HTML_COMMENT_RE.sub("", line)
        if "<!--" in clean:
            clean = clean[:clean.index("<!--")]
            in_ml_comment = True
        yield clean


def _parse_preamble_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    field_re = re.compile(r"^- \*\*(?P<name>[^*]+):\*\*\s*(?P<value>.*)$")
    for clean in _iter_preamble_lines(text):
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
    # to the co-located module that must win. Same predicate as
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
_UNMIGRATED_IDENTITY_MARKER = "unmigrated"
_COOLED_IDENTITY_MARKER = "cooled"
_NONCONFINED_IDENTITY_MARKER = "nonconfined"

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
        ("retain-exception", "Reclassified"),
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
    cooling_state_unavailable = False
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
        if getattr(result, "code", None) == "cooling-state-unavailable":
            cooling_state_unavailable = True
            continue
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
    if cooling_state_unavailable:
        # The complete record walk retains independent path-specific findings,
        # but no partial cooled set is safe to use when authority is unavailable.
        findings.append(_finding("cooling_state_unavailable"))
        return frozenset(), tuple(findings)
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
    # whenever the closure was not installed. An absent lifecycle directory
    # must not raise that finding, while a directory that exists whose every
    # resolution route fails must; the two inputs overlapped here.
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


def _resolved_provenance_parent(
    value: str | None, *, require_local_brief: bool
) -> str | None:
    """The one resolved form of a provenance parent value.

    Every consumer of a provenance parent reads it through this function --
    the path check, the source-vs-artifact equality comparison, and the brief
    child-state attribution. Resolving inside the path check alone is what
    caused the defect this replaces: the raw `brief:<slug>` value stayed in
    scope, and the equality check a few lines below compared a typed header
    against a path-form `source.parent`, reporting `provenance_mismatch` for
    every migrated spec. Handing the caller a resolved value is what stops the
    next consumer reaching for an unresolved one -- there is none left in scope
    to reach for.

    `require_local_brief` is the spec-provenance gate. Only there does
    `brief:<slug>` denote a path. At the shared helper's other call sites --
    `workspace.toml` entry, dependency, legacy-queue and receipt paths -- a
    slug is meaningless, so the value is returned untouched and
    `_is_canonical_local_brief_path` keeps refusing it.

    A value that is neither admitted form is returned unchanged, so it still
    mismatches and is still refused by the path check.
    """
    normalized = _normalized_optional_artifact_value(value)
    if normalized is None or not require_local_brief:
        return normalized
    return _normalized_brief_pointer(normalized)


def _path_presence(path: Path) -> str:
    """Return `present`, `missing`, or `unreadable` for one confined path.

    `Path.exists()` swallows every `OSError` on newer interpreters, which would
    report a file under an unsearchable directory as missing. `stat` raises on
    every supported version, so only an absent name or one the filesystem
    cannot hold reads as missing; any other failure is an unreadable artifact.
    """
    try:
        path.stat()
    except OSError as exc:
        if exc.errno in (errno.ENOENT, errno.ENOTDIR, errno.ENAMETOOLONG, errno.EINVAL):
            return "missing"
        return "unreadable"
    return "present"


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
    presence = _path_presence(artifact_path)
    if presence == "unreadable":
        return ArtifactMetadata(
            path=entry.path,
            kind=entry.kind,
            status=None,
            exists=True,
            readable=False,
        )
    if presence == "missing":
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


def _captured_membership_form(path: str | None) -> str | None:
    """Classify a canonical membership's path from the path alone, opening nothing.

    `None` is a path that is not a captured-item reference; `migrated` names a
    captured-item file directly in the captured-item directory; anything else
    that is a captured-item reference is `unmigrated`.
    """
    if path is None or not _is_captured_item_reference(path):
        return None
    directory, _, name = path.rpartition("/")
    if directory == _CAPTURED_DIR and _CAPTURED_FILE_RE.fullmatch(name):
        return "migrated"
    return "unmigrated"


def _captured_record_metadata(root: Path, entry: WorkspaceEntry) -> ArtifactMetadata:
    """Metadata for a migrated captured membership, read from its record."""
    path = entry.path or ""
    # Presence is decided without following a link: a linked or dangling record
    # is present, and the confined reader below reports it unreadable.
    if not os.path.lexists(root / path):
        return ArtifactMetadata(path=path, kind=entry.kind, status=None, exists=False)
    # Not cooled by construction: every caller skips a cooled membership first.
    item, finding = read_captured_item(root, path.rpartition("/")[2], frozenset())
    if finding is not None:
        return ArtifactMetadata(
            path=path, kind=entry.kind, status=None, exists=True,
            readable=finding.code != "unreadable_artifact",
            captured_finding=finding,
        )
    return ArtifactMetadata(
        path=path, kind=entry.kind, status=item["status"], exists=True,
        resolution=item["resolution"], captured_kind=item["kind"],
    )


def _artifact_metadata(
    _workspace: dict,
    entry: WorkspaceEntry,
    root: Path | None,
    *,
    registered: bool = True,
) -> ArtifactMetadata | None:
    """Read an artifact's metadata. `registered` is False for a dependency probe.

    A registered, non-cooled captured membership reads from its record when
    migrated and is not opened at all when unmigrated.
    """
    if root is None:
        return None
    if registered:
        form = _captured_membership_form(entry.path)
        if form == "unmigrated":
            return None
        if form == "migrated":
            return _captured_record_metadata(root, entry)
    else:
        # A probe of a file in the captured-item directory is a confined read
        # too, and only under the file's exact name; any other spelling of it is
        # refused, so the outcome does not depend on the filesystem.
        spelling = _captured_dir_spelling(entry.path)
        if spelling == "variant":
            return ArtifactMetadata(
                path=entry.path, kind=entry.kind, status=None, exists=True, readable=False
            )
        if spelling == "canonical":
            return _captured_record_metadata(root, entry)
    return _metadata_from_root(root, entry)


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
    list[RoutingFinding],
    str | None,
]:
    parsed, findings = parse_workspace_entry(raw)
    if parsed is not None:
        return WorkspaceMembership(parsed, ini_slug, collection, status), [], None
    raw_path = raw.get("path") if isinstance(raw, dict) else None
    if _is_repository_relative_path(raw_path):
        findings = [
            dataclasses.replace(finding, path=raw_path)
            if not finding.path else finding
            for finding in findings
        ]
    legacy = _legacy_path_finding(collection, raw)
    if legacy.finding.code == "invalid_artifact_path" and not _is_target_like_entry(raw):
        return None, [legacy.finding], None
    if legacy.finding.code == "unsupported_legacy" and not _is_target_like_entry(raw):
        return None, [legacy.finding], None
    if findings:
        blocks_dependencies = any(
            finding.code in {"invalid_entry", "invalid_artifact_path"}
            for finding in findings
        )
        blocked_path = _target_like_blocked_path(raw) if blocks_dependencies else None
        return None, findings, blocked_path
    return None, [legacy.finding], None


def _extract_canonical_memberships(
    workspace: dict,
) -> tuple[
    list[WorkspaceMembership],
    list[LegacyWorkspaceMembership],
    list[RoutingFinding],
    list[ParseBlockedWorkspaceMembership],
]:
    memberships: list[WorkspaceMembership] = []
    findings: list[RoutingFinding] = []
    parse_blocked_memberships: list[ParseBlockedWorkspaceMembership] = []
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
                    entry_findings,
                    blocked_path,
                ) = _parse_membership_entry(raw_entry, collection, "", "")
                if membership is not None:
                    memberships.append(
                        dataclasses.replace(membership, entry_index=entry_index)
                    )
                if blocked_path is not None:
                    parse_blocked_memberships.append(
                        ParseBlockedWorkspaceMembership(
                            canonical_artifact_path=blocked_path,
                            ini_slug="",
                            collection=collection,
                            entry_index=entry_index,
                        )
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
                        entry_findings,
                        blocked_path,
                    ) = _parse_membership_entry(raw_entry, collection, ini_slug, status)
                    if membership is not None:
                        memberships.append(
                            dataclasses.replace(membership, entry_index=entry_index)
                        )
                    if blocked_path is not None:
                        parse_blocked_memberships.append(
                            ParseBlockedWorkspaceMembership(
                                canonical_artifact_path=blocked_path,
                                ini_slug=ini_slug,
                                collection=collection,
                                entry_index=entry_index,
                            )
                        )
                    findings.extend(entry_findings)
    return memberships, [], findings, parse_blocked_memberships


def extract_legacy_migration_memberships(workspace: dict) -> list[LegacyWorkspaceMembership]:
    """Return accepted legacy memberships for explicit migration operations only."""

    memberships: list[LegacyWorkspaceMembership] = []
    for section_name, top_level_names in _TOP_LEVEL_ENTRY_COLLECTIONS.items():
        section = workspace.get(section_name, {})
        if not isinstance(section, dict):
            continue
        for list_name in top_level_names:
            entries = section.get(list_name, [])
            if not isinstance(entries, list):
                continue
            collection = _collection_label(section_name, list_name)
            for entry_index, raw_entry in enumerate(entries):
                legacy = parse_legacy_workspace_entry(collection, raw_entry)
                if legacy.finding.code == "legacy_entry":
                    memberships.append(
                        LegacyWorkspaceMembership(
                            legacy,
                            "",
                            collection,
                            "",
                            entry_index=entry_index,
                        )
                    )
    for raw_ini_slug, section in workspace.items():
        if not isinstance(raw_ini_slug, str) or not _CANONICAL_INITIATIVE_RE.fullmatch(
            raw_ini_slug
        ):
            continue
        if not isinstance(section, dict):
            continue
        status = section.get("status", "")
        status = status if isinstance(status, str) else ""
        for section_name, initiative_names in _INITIATIVE_ENTRY_COLLECTIONS.items():
            subsection = section.get(section_name, {})
            if not isinstance(subsection, dict):
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
                    continue
                collection = _collection_label(section_name, list_name)
                for entry_index, raw_entry in enumerate(entries):
                    legacy = parse_legacy_workspace_entry(collection, raw_entry)
                    if legacy.finding.code == "legacy_entry":
                        memberships.append(
                            LegacyWorkspaceMembership(
                                legacy,
                                raw_ini_slug,
                                collection,
                                status,
                                entry_index=entry_index,
                            )
                        )
    return memberships


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
    # `brief:<slug>` is normalized to its canonical path *here*, at the
    # provenance read, before any lexical check runs — never inside
    # `_is_canonical_local_brief_path`, which also guards `workspace.toml`
    # entry and dependency paths where a slug has no meaning.
    #
    # Callers inside this module pass a value already resolved by
    # `_resolved_provenance_parent`, and resolving is idempotent — a path form
    # has no `brief:` prefix to match. This line is kept so the helper stays
    # correct for a direct caller that holds only the declared value.
    candidate = _normalized_brief_pointer(path) if require_local_brief else path
    if not _is_repository_relative_path(candidate):
        return True
    if require_local_brief:
        if not _is_canonical_local_brief_path(candidate):
            return True
        # The boundary is the resolved briefs directory, stricter
        # than `_confined_artifact_path`'s repository-root confinement.
        return root is not None and not _confined_briefs_path(root, candidate)
    return root is not None and _confined_artifact_path(root, path) is None


def _dependency_metadata_safety_finding(
    path: str,
    kind: str,
    metadata: ArtifactMetadata | None,
    root: Path | None,
) -> RoutingFinding | None:
    if metadata is not None and metadata.captured_finding is not None:
        return metadata.captured_finding
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


def _completion_receipt_satisfied(
    dep: Dependency,
) -> tuple[bool, RoutingFinding | None]:
    """Validate an absent local dependency's receipt and decide satisfaction."""
    receipt = dep.receipt
    if receipt == _MALFORMED_COMPLETION_RECEIPT or not isinstance(receipt, dict):
        return False, _finding(
            "invalid_completion_receipt", dep.path, "completion receipt shape is invalid"
        )
    if (
        re.fullmatch(_COMPLETION_RECEIPT_DELIVERY_ID_RE, receipt["delivery_id"])
        is None
        or receipt["completion_event"] not in _COMPLETION_RECEIPT_EVENTS
        or re.fullmatch(
            _COMPLETION_RECEIPT_EVIDENCE_REF_RE, receipt["evidence_ref"]
        )
        is None
        or receipt["outcome"] not in _COMPLETION_RECEIPT_OUTCOMES
    ):
        return False, _finding(
            "invalid_completion_receipt", dep.path, "completion receipt value is invalid"
        )
    if receipt["outcome"] == "completed":
        return True, None
    return False, _finding(
        "unsatisfied_dependency", dep.path, "dependency delivery did not complete"
    )


def _dependency_is_satisfied(
    dep: Dependency,
    workspace: dict,
    by_path: dict[str, list[WorkspaceMembership]],
    structurally_blocked_paths: set[str],
    root: Path | None,
    cooled: frozenset[Path],
    briefs_with_cooled_children: frozenset[str] = frozenset(),
    cooled_scope_unknown: frozenset[str] = frozenset(),
    brief_child_states: dict[str, set[str]] | None = None,
) -> tuple[bool, RoutingFinding | None]:
    """Decide whether one dependency is satisfied, or return the finding why not.

    A captured-item file that no membership names settles by its own `Status:`
    and `Resolution:`; every other dependency follows its membership or its
    artifact's terminal state. An unregistered brief also has to keep the brief
    child-state rule, which reads only its `Status:` and its child specs.
    """
    if (
        dep.type != "cross-repo"
        and any(
            _captured_membership_form(match.entry.path) == "unmigrated"
            for match in by_path.get(dep.path, [])
        )
        and not (root is not None and _confined_artifact_path(root, dep.path) in cooled)
    ):
        return False, _finding("unsatisfied_dependency", dep.path, "captured item unmigrated")
    if dep.path in structurally_blocked_paths:
        return False, _finding("unsatisfied_dependency", dep.path, "dependency has findings")
    # Fail closed when a brief's child scope is unknown. A cooled child may
    # have changed the brief's terminal state without the workspace membership
    # reflecting it, so the brief's apparent state is not evidence.
    #
    # The refused set has two parts. Per brief: the `source.parent` values
    # declared by cooled spec memberships that resolve to a registered brief.
    # Repository-wide: every `kind = "brief"` dependency, while any cooled
    # entry's scope is unestablished — because the brief such an entry belongs
    # to is exactly what is unknown. Neither part is initiative-scoped and
    # neither considers initiative status: a cooled spec in a paused initiative
    # that declares a brief owned by an active one still refuses that brief. A
    # declared value is unvalidated against the artifact body, because the
    # cooled branch of `_structural_findings` returns before the provenance
    # check —
    # for a cooled child the declaration is unverifiable by construction, which
    # is the point of failing closed rather than trusting it.
    # Two ways a brief dependency's child scope is not established. A cooled
    # child that *declares* this brief makes that brief's scope unevaluable.
    # A cooled child whose parent is undeclared or unresolvable makes *every*
    # brief's scope unevaluable, because the brief it belongs to is exactly
    # what is unknown; a maintainer clears that by declaring a resolving path,
    # or `none` when the spec has no parent.
    brief_scope_unknown = dep.kind == "brief" and (
        dep.path in briefs_with_cooled_children or bool(cooled_scope_unknown)
    )
    cooled_dependency = (
        root is not None and _confined_artifact_path(root, dep.path) in cooled
    )
    if dep.type == "cross-repo":
        if cooled_dependency:
            # A cooled body is never opened, with no exception.
            # `_cross_repo_receipt_satisfied`
            # opens the brief body unconditionally, and the evidence it needs
            # is only there: the four-field receipt match asserted for this one
            # dependency. A lifecycle record cannot stand in — it is completion
            # evidence for the brief as a whole, and projecting the receipt
            # from its coordination surface is deliberately not done here.
            # Refusing surfaces
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
    if (
        not matches
        and root is not None
        and dep.kind
        and _captured_dir_spelling(dep.path) == "canonical"
        and not cooled_dependency
    ):
        # An unregistered captured item settles by its own file: one read, and
        # only `Closed` with `Resolution: fixed` satisfies.
        item, finding = read_captured_item(
            root, dep.path[len(_CAPTURED_DIR) + 1:], cooled
        )
        if finding is not None:
            return False, finding
        if item.get("cooled") or "status" not in item:
            # The reader re-checks the cooled set; a path that became cooled
            # between the two checks is refused without opening the file.
            return False, _finding(
                "unsatisfied_dependency", dep.path, "captured item became cooled"
            )
        if item["status"] == "Closed" and item["resolution"] == "fixed":
            return True, None
        return False, _finding(
            "unsatisfied_dependency", dep.path, "captured item is not closed as fixed"
        )
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
        metadata = _artifact_metadata(workspace, probe, root, registered=False)
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
        metadata = _artifact_metadata(workspace, probe, root, registered=False)
    safety_finding = _dependency_metadata_safety_finding(
        dep.path, dep.kind, metadata, root
    )
    if safety_finding is not None:
        if (
            not matches
            and dep.receipt is not None
            and safety_finding.code == "missing_dependency"
        ):
            return _completion_receipt_satisfied(dep)
        return False, safety_finding
    if brief_scope_unknown:
        # Deliberately after the safety check: a missing, unreadable or
        # invalid-path brief has a concrete cause, and reporting "re-establish
        # the child scope" for a brief that does not exist sends the maintainer
        # to the wrong repair.
        return False, _finding(
            "unsatisfied_dependency", dep.path, "brief child scope is unknown"
        )
    if not matches and dep.kind == "brief" and brief_child_states is not None:
        collection = f"brief_queue.{(metadata.status or '').lower()}"
        if collection in _ALLOWED_KIND_BY_COLLECTION and not _brief_child_scope_is_valid(
            collection,
            brief_child_states.get(dep.path, set()),
            scope_unevaluable=dep.path in briefs_with_cooled_children,
        ):
            return False, _finding(
                "unsatisfied_dependency", dep.path, "brief child state rule broken"
            )
    status = metadata.status
    if status is None and matches:
        status = _membership_status(matches[0])
    if _dependency_terminal_satisfied(dep.kind, status, metadata):
        return True, None
    return False, _finding("unsatisfied_dependency", dep.path, "dependency not terminal")


def _dependency_cycles(
    memberships: list[WorkspaceMembership],
    header_edges: dict[str, tuple[Dependency, ...]],
) -> set[str]:
    graph: dict[str, list[str]] = {}
    paths = {membership.entry.path for membership in memberships}
    for membership in memberships:
        graph[membership.entry.path] = [
            dep.path for dep in header_edges.get(membership.entry.path, ())
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


# ── Header dependencies ──────────────────────────────────────────────────────
#
# A waiting item's `- **Depends on:**` and `- **Dependency receipts:**` preamble
# lines are the one place an edge is written. The reader below turns them into
# the same `Dependency` values a typed `needs` entry produced, so every
# satisfaction rule and receipt validator runs unchanged on its output.

_TYPED_REFERENCE_RE = re.compile(
    r"(?P<kind>spec|brief|intent|outcome|opportunity|capability):"
    r"(?P<slug>[a-z0-9][a-z0-9-]*)"
)
_CAPTURED_SEGMENT_RE = re.compile(r"[A-Za-z0-9._-]+")
_LIVE_INTENT_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\.md")
_COORDINATION_TOKEN_RE = re.compile(r"[A-Za-z0-9._:/@+-]{1,200}")
_HEADER_FIELD_RE = re.compile(r"^- \*\*(?P<name>[^*]+):\*\*\s*(?P<value>.*)$")
_BRIEFS_DIR = "docs/product/briefs"
_INTENTS_DIR = "docs/product/intents"


@dataclasses.dataclass(frozen=True)
class ResolutionIndex:
    """Brief slugs and live-intent `(kind, slug)` pairs, built once per run.

    A directory whose listing failed, or one of whose admitted entries could not
    be read, is flagged unreadable: a reference into it is never a missing target.
    """

    briefs: dict[str, tuple[str, ...]]
    intents: dict[tuple[str, str], tuple[str, ...]]
    briefs_unreadable: bool = False
    intents_unreadable: bool = False


@dataclasses.dataclass(frozen=True)
class HeaderDependencies:
    """One waiting item's header edges and the findings its header earned."""

    dependencies: tuple[Dependency, ...]
    findings: tuple[RoutingFinding, ...]


def _normalized_field_value(value: str | None, *, first_word: bool = False) -> str:
    """A preamble field value with one pair of surrounding backticks stripped.

    The preamble walk already hides HTML comments. `Kind:` and `Level:` take
    their first word.
    """
    text = (value or "").strip()
    if len(text) >= 2 and text[0] == "`" and text[-1] == "`":
        text = text[1:-1]
    if first_word:
        words = text.split()
        return words[0] if words else ""
    return text


def _intent_kind(fields: dict[str, str]) -> str:
    kind = _normalized_field_value(fields.get("kind"), first_word=True)
    if kind in ("outcome", "opportunity"):
        return kind
    if _normalized_field_value(fields.get("level"), first_word=True) == "capability":
        return "capability"
    return "intent"


def _admitted_directory_names(root: Path, relative_dir: str) -> list[str] | None:
    """Names in `relative_dir` that match the live intent name pattern.

    `[]` when the directory is absent, `None` when it cannot be listed or its
    resolved location leaves the repository.
    """
    directory = root / relative_dir
    if _path_presence(directory) == "missing" and not directory.is_symlink():
        return []
    try:
        root_resolved = root.resolve()
        resolved = directory.resolve()
        resolved.relative_to(root_resolved)
        if resolved == root_resolved or not resolved.is_dir():
            return None
        names = sorted(entry.name for entry in resolved.iterdir())
    except (OSError, RuntimeError, ValueError):
        return None
    return [name for name in names if _LIVE_INTENT_NAME_RE.fullmatch(name)]


def _read_directory_entry(root: Path, relative_dir: str, name: str) -> str | None:
    """Read one admitted entry, or `None` when it is refused or unreadable."""
    relative = f"{relative_dir}/{name}"
    if relative_dir == _BRIEFS_DIR and not _confined_briefs_path(root, relative):
        return None
    candidate = _confined_artifact_path(root, relative)
    if candidate is None:
        return None
    try:
        candidate.relative_to((root.resolve() / relative_dir).resolve())
        if not candidate.is_file():
            return None
        return candidate.read_text(encoding="utf-8", errors="replace")
    except (OSError, RuntimeError, ValueError):
        return None


def build_resolution_index(
    root: Path, *, cooled: frozenset[Path] = frozenset()
) -> ResolutionIndex:
    """List `docs/product/briefs/` and `docs/product/intents/` once.

    A cooled entry's body is never opened: a cooled brief is indexed by its file
    stem and a cooled intent is left out, since neither can be matched by a
    `Slug:` field it was not allowed to read.
    """
    briefs: dict[str, list[str]] = {}
    intents: dict[tuple[str, str], list[str]] = {}
    unreadable = {_BRIEFS_DIR: False, _INTENTS_DIR: False}
    for relative_dir in (_BRIEFS_DIR, _INTENTS_DIR):
        names = _admitted_directory_names(root, relative_dir)
        if names is None:
            unreadable[relative_dir] = True
            continue
        for name in names:
            relative = f"{relative_dir}/{name}"
            if _confined_artifact_path(root, relative) in cooled:
                if relative_dir == _BRIEFS_DIR:
                    briefs.setdefault(name.removesuffix(".md"), []).append(relative)
                continue
            text = _read_directory_entry(root, relative_dir, name)
            if text is None:
                unreadable[relative_dir] = True
                continue
            fields = _parse_preamble_fields(text)
            slug = _normalized_field_value(fields.get("slug"))
            if relative_dir == _BRIEFS_DIR:
                if "slug" not in fields:
                    slug = name.removesuffix(".md")
                briefs.setdefault(slug, []).append(relative)
            elif "tombstone" not in fields and slug:
                intents.setdefault((_intent_kind(fields), slug), []).append(relative)
    return ResolutionIndex(
        briefs={key: tuple(paths) for key, paths in briefs.items()},
        intents={key: tuple(paths) for key, paths in intents.items()},
        briefs_unreadable=unreadable[_BRIEFS_DIR],
        intents_unreadable=unreadable[_INTENTS_DIR],
    )


def _captured_dir_spelling(path: str) -> str | None:
    """How `path` names the captured-item directory, if it names it at all.

    `canonical` is a captured-item file name directly in the directory, spelled
    exactly. `variant` is any other path that a case-insensitive or
    trailing-dot-dropping filesystem could map into the directory; it is
    refused, because it would reach a captured file under a name the confined
    reader and the cooled check do not compare. `None` is a path elsewhere.
    """
    folded = "/".join(part.rstrip(".").casefold() for part in path.split("/"))
    if not folded.startswith(f"{_CAPTURED_DIR}/"):
        return None
    name = path[len(_CAPTURED_DIR) + 1:] if path.startswith(f"{_CAPTURED_DIR}/") else ""
    return "canonical" if _CAPTURED_FILE_RE.fullmatch(name) else "variant"


def _is_captured_item_reference(item: str) -> bool:
    parts = item.split("/")
    if any(
        part in (".", "..") or _CAPTURED_SEGMENT_RE.fullmatch(part) is None
        for part in parts
    ):
        return False
    if len(parts) == 4 and parts[:2] == ["docs", "specs"] and parts[3] == "spec.md":
        return False
    return parts[:3] not in (
        _BRIEFS_DIR.split("/"),
        _INTENTS_DIR.split("/"),
    )


def _echoable_reference(item: str) -> str:
    """The item as a finding may echo it, or `""` when it must be withheld."""
    if _TYPED_REFERENCE_RE.fullmatch(item) is None and not _is_captured_item_reference(
        item
    ):
        return ""
    return _bounded_finding_identifier(item)


# The captured-item file grammar and the listing of its directory. A captured
# item is one file in `_CAPTURED_DIR`; its preamble fields say what it is. The
# listing is built from the directory and the cooled set only, never from the
# registry, so two registries over one tree give one listing.
_CAPTURED_DIR = "docs/product/captured"
_CAPTURED_FILE_RE = re.compile(r"[a-z0-9][a-z0-9-]*\.md")
_CAPTURED_STATUSES = frozenset({"Open", "Closed"})
_CAPTURED_KINDS = frozenset({"defect", "design", "research", "intent"})
_CAPTURED_RESOLUTIONS = frozenset({"fixed", "declined", "superseded"})
_CAPTURED_PARENT_KINDS = frozenset({"intent", "outcome", "opportunity", "capability"})
# Each shaping type routes to a skill, in the order the spec lists them.
_SHAPING_TYPE_ROUTES = {
    "shape": "intent",
    "research": "desk-research-project-start",
    "strategy": "frame-situation",
    "design": "experience-status",
    "signal": "(signal — no action)",
}
# The captured-item fields, in the order the first failing one is named.
_CAPTURED_FIELD_ORDER = (
    ("status", "Status"),
    ("kind", "Kind"),
    ("type", "Type"),
    ("resolution", "Resolution"),
    ("parent intent", "Parent intent"),
    ("detail", "Detail"),
)


def _captured_field_value(raw: str, name: str) -> str:
    """A preamble field's value: backticks off once, first word for `Kind`."""
    value = raw.strip()
    if len(value) >= 2 and value[0] == "`" and value[-1] == "`":
        value = value[1:-1].strip()
    if name == "kind":
        words = value.split()
        value = words[0] if words else ""
    return value


def parse_captured_item(text: str) -> tuple[dict[str, str | None] | None, str | None]:
    """Check one captured-item file's preamble against the grammar.

    `Resolution:` is required exactly when `Status:` is `Closed`, for every kind.

    Returns `(fields, None)` when valid and `(None, <first failing field>)`
    otherwise. Field lines are counted here through `_iter_preamble_lines`,
    because `_parse_preamble_fields` keeps only the first value of a repeat.
    """
    values: dict[str, list[str]] = {}
    for line in _iter_preamble_lines(text):
        match = _HEADER_FIELD_RE.match(line)
        if match:
            name = match.group("name").strip().lower()
            values.setdefault(name, []).append(
                _captured_field_value(match.group("value"), name)
            )

    def single(name: str) -> str | None:
        found = values.get(name, [])
        return found[0] if len(found) == 1 else None

    status, kind = single("status"), single("kind")
    for key, label in _CAPTURED_FIELD_ORDER:
        found = values.get(key, [])
        value = single(key)
        if len(found) > 1:
            return None, label
        if key == "status" and value not in _CAPTURED_STATUSES:
            return None, label
        if key == "kind" and value not in _CAPTURED_KINDS:
            return None, label
        if key == "type" and found and value not in _SHAPING_TYPE_ROUTES:
            return None, label
        if key == "resolution":
            required = status == "Closed"
            if required != bool(found) or (
                found and value not in _CAPTURED_RESOLUTIONS
            ):
                return None, label
        if key == "parent intent" and found:
            typed = _TYPED_REFERENCE_RE.fullmatch(value or "")
            if typed is None or typed.group("kind") not in _CAPTURED_PARENT_KINDS:
                return None, label
        if key == "detail" and found and not _is_captured_item_reference(value or ""):
            return None, label
    return {
        "status": status,
        "kind": kind,
        "type": single("type"),
        "resolution": single("resolution"),
        "parent_intent": single("parent intent"),
        "detail": single("detail"),
    }, None


def _captured_finding(code: str, path: str, field: str = "") -> RoutingFinding:
    """A finding that echoes `path` only when it fits the reference grammar."""
    return _finding(code, _echoable_reference(path), field)


def read_captured_item(
    root: Path, name: str, cooled: frozenset[Path]
) -> tuple[dict[str, Any], RoutingFinding | None]:
    """List one captured-item file, `name` being a name in the file grammar.

    A cooled file is never opened. Any other is read through the identity-checked
    reader, so a link, a non-regular file, or a swap between check and open is
    unreadable and none of its content is used.
    """
    relative = f"{_CAPTURED_DIR}/{name}"
    entry: dict[str, Any] = {"path": relative, "slug": name.removesuffix(".md")}
    if _confined_artifact_path(root, relative) in cooled:
        return {**entry, "cooled": True}, None
    content = _migration_file_bytes(root, relative)
    try:
        text = content.decode("utf-8") if content is not None else None
    except UnicodeDecodeError:
        text = None
    if text is None:
        return (
            {**entry, "unreadable": True},
            _captured_finding("unreadable_artifact", relative),
        )
    fields, failing = parse_captured_item(text)
    if fields is None:
        return (
            {**entry, "invalid": True},
            _captured_finding("invalid_captured_item", relative, failing or ""),
        )
    routed = fields["type"]
    return {
        **entry,
        "status": fields["status"],
        "kind": fields["kind"],
        "type": routed,
        "routes_to": _SHAPING_TYPE_ROUTES[routed] if routed else None,
        "resolution": fields["resolution"],
        "parent_intent": fields["parent_intent"],
        "detail": fields["detail"],
    }, None


def _header_finding(
    code: str, waiting_path: str, reason: str, item: str | None = None
) -> RoutingFinding:
    echoed = _echoable_reference(item) if item is not None else ""
    return _finding(
        code,
        _bounded_finding_identifier(waiting_path),
        f"{reason}: {echoed}" if echoed else reason,
    )


def _header_field_lines(text: str) -> list[tuple[str, str, bool]]:
    """Every `Depends on:` and `Dependency receipts:` preamble line.

    Each is `(lowercased name, value, followed by an indented non-blank line)`.
    """
    lines = list(_iter_preamble_lines(text))
    found: list[tuple[str, str, bool]] = []
    for position, line in enumerate(lines):
        match = _HEADER_FIELD_RE.match(line)
        if not match:
            continue
        name = match.group("name").strip().lower()
        if name not in ("depends on", "dependency receipts"):
            continue
        following = lines[position + 1] if position + 1 < len(lines) else ""
        wrapped = following[:1] in (" ", "\t") and following.strip() != ""
        found.append((name, match.group("value").strip(), wrapped))
    return found


def _split_items(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _parse_receipt_line(
    waiting_path: str,
    item: str,
    items: set[str],
    receipts: dict[str, tuple[str, tuple[str, ...]]],
) -> RoutingFinding | None:
    """Validate one receipt; record it under its reference when it is sound."""
    tokens = item.split()
    reference = tokens[0]
    keyword = tokens[1] if len(tokens) > 1 else ""
    refuse = lambda reason: _header_finding(  # noqa: E731
        "invalid_dependency", waiting_path, f"dependency receipt {reason}", reference
    )
    if keyword not in ("completion", "coordination"):
        return refuse("has an unknown keyword")
    if len(tokens) != (6 if keyword == "completion" else 5):
        return refuse("has the wrong token count")
    if reference not in items:
        return refuse("names no dependency item")
    if reference in receipts:
        return refuse("repeats a reference")
    typed = _TYPED_REFERENCE_RE.fullmatch(reference)
    if keyword == "coordination":
        if typed is None or typed.group("kind") != "brief":
            return refuse("coordination applies to a brief reference only")
        remote_kind, receipt_id, revision = tokens[2:]
        if remote_kind not in ("brief", "spec"):
            return _header_finding(
                "invalid_entry", waiting_path, "cross-repo need kind is invalid", reference
            )
        for value in (receipt_id, revision):
            if _COORDINATION_TOKEN_RE.fullmatch(value) is None:
                return _header_finding(
                    "invalid_entry", waiting_path, "receipt value is invalid", reference
                )
    elif typed is None and _is_captured_item_reference(reference):
        return refuse("completion does not apply to a captured item")
    receipts[reference] = (keyword, tuple(tokens[2:]))
    return None


def _brief_path_for(slug: str, index: ResolutionIndex) -> str:
    matches = index.briefs.get(slug, ())
    return matches[0] if len(matches) == 1 else f"{_BRIEFS_DIR}/{slug}.md"


def read_header_dependencies(
    root: Path,
    waiting_path: str,
    *,
    index: ResolutionIndex,
    membership_kinds: dict[str, str],
    cooled: frozenset[Path],
) -> HeaderDependencies:
    """Read one waiting item's header edges.

    `membership_kinds` maps each canonical membership path to its `kind`. A
    cooled waiting item is never opened and contributes nothing. A missing or
    unconfined waiting item contributes nothing here: reconciliation reports it.
    """
    waiting_file = _confined_artifact_path(root, waiting_path)
    if waiting_file is None or waiting_file in cooled:
        return HeaderDependencies((), ())
    presence = _path_presence(waiting_file)
    if presence == "missing":
        return HeaderDependencies((), ())
    unreadable = HeaderDependencies(
        (), (_header_finding("unreadable_artifact", waiting_path, "waiting item unreadable"),)
    )
    if presence == "unreadable":
        return unreadable
    try:
        text = waiting_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return unreadable
    return header_dependencies_from_text(
        root,
        waiting_path,
        text,
        index=index,
        membership_kinds=membership_kinds,
        cooled=cooled,
    )


def header_dependencies_from_text(
    root: Path,
    waiting_path: str,
    text: str,
    *,
    index: ResolutionIndex,
    membership_kinds: dict[str, str],
    cooled: frozenset[Path],
) -> HeaderDependencies:
    """Read header edges from a waiting item's text.

    The same rules `read_header_dependencies` applies to the file, so the repair
    can check what a planned header would read as before it writes one.
    """
    findings: list[RoutingFinding] = []
    items: list[str] = []
    receipt_lines: list[str] = []
    for name, value, wrapped in _header_field_lines(text):
        if wrapped:
            label = "Depends on:" if name == "depends on" else "Dependency receipts:"
            findings.append(
                _header_finding(
                    "invalid_dependency",
                    waiting_path,
                    f"an indented line follows {label} and would be dropped",
                )
            )
        if name == "dependency receipts":
            receipt_lines.extend(_split_items(value))
        elif value.split()[:1] and value.split()[0].lower() != "none":
            items.extend(_split_items(value))
    item_set = set(items)
    receipts: dict[str, tuple[str, tuple[str, ...]]] = {}
    for line in receipt_lines:
        finding = _parse_receipt_line(waiting_path, line, item_set, receipts)
        if finding is not None:
            findings.append(finding)
    dependencies: list[Dependency] = []
    for item in items:
        target, finding = _resolve_header_item(
            root, waiting_path, item, index, membership_kinds, cooled
        )
        if finding is not None:
            findings.append(finding)
        if target is None:
            continue
        kind, path, brief_slug = target
        receipt = receipts.get(item)
        if receipt is not None and receipt[0] == "coordination" and brief_slug:
            remote_kind, receipt_id, revision = receipt[1]
            brief_path = _brief_path_for(brief_slug, index)
            dependencies.append(
                Dependency(
                    type="cross-repo",
                    kind=remote_kind,
                    path=brief_path,
                    containing_brief=brief_path,
                    receipt_id=receipt_id,
                    accepted_revision=revision,
                )
            )
            continue
        completion: dict[str, str] | str | None = None
        if receipt is not None and receipt[0] == "completion":
            delivery_id, outcome, event, evidence = receipt[1]
            completion = {
                "delivery_id": delivery_id,
                "outcome": outcome,
                "completion_event": event,
                "evidence_ref": evidence,
            }
            if not all(
                _is_bounded_text(value, _COMPLETION_RECEIPT_MAX_FIELD_LENGTH)
                for value in completion.values()
            ):
                completion = _MALFORMED_COMPLETION_RECEIPT
        dependencies.append(
            Dependency(type="local", kind=kind, path=path, receipt=completion)
        )
    return HeaderDependencies(tuple(dependencies), tuple(findings))


def _resolve_header_item(
    root: Path,
    waiting_path: str,
    item: str,
    index: ResolutionIndex,
    membership_kinds: dict[str, str],
    cooled: frozenset[Path],
) -> tuple[tuple[str, str, str] | None, RoutingFinding | None]:
    """Resolve one item to `(kind, path, brief slug or "")`, or a finding.

    A typed reference with no target keeps the path the satisfaction logic needs
    to report it missing, and a captured item with no file and no membership
    keeps its path with no kind.
    """
    typed = _TYPED_REFERENCE_RE.fullmatch(item)
    if typed is not None:
        ref_kind, slug = typed.group("kind", "slug")
        if ref_kind == "spec":
            return ("spec", f"docs/specs/{slug}/spec.md", ""), None
        if ref_kind == "brief":
            unreadable, matches = index.briefs_unreadable, index.briefs.get(slug, ())
            kind = "brief"
        else:
            unreadable = index.intents_unreadable
            matches = index.intents.get((ref_kind, slug), ())
            kind = "intent"
        if unreadable:
            return None, _header_finding(
                "unreadable_artifact", waiting_path, "dependency directory unreadable", item
            )
        if len(matches) > 1:
            return None, _header_finding(
                "invalid_dependency", waiting_path, "dependency reference is ambiguous", item
            )
        return (kind, matches[0] if matches else item, slug if kind == "brief" else ""), None
    if not _is_captured_item_reference(item):
        return None, _header_finding(
            "invalid_dependency",
            waiting_path,
            "dependency item is neither a typed reference nor a captured-item path",
            item,
        )
    member_kind = membership_kinds.get(item)
    if member_kind:
        return (member_kind, item, ""), None
    spelling = _captured_dir_spelling(item)
    if spelling == "variant":
        return None, _header_finding(
            "unreadable_artifact", waiting_path, "captured item unreadable", item
        )
    captured_file = _confined_artifact_path(root, item)
    if captured_file is None:
        return ("", item, ""), None
    captured_presence = _path_presence(captured_file)
    if captured_presence == "unreadable":
        return None, _header_finding(
            "unreadable_artifact", waiting_path, "captured item unreadable", item
        )
    if captured_presence == "missing":
        return ("", item, ""), None
    kind = ""
    if captured_file not in cooled:
        try:
            if spelling == "canonical":
                # A captured-item file is read only as a confined file.
                content = _migration_file_bytes(root, item)
                if content is None:
                    raise OSError(item)
                text = content.decode("utf-8", errors="replace")
            else:
                text = captured_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None, _header_finding(
                "unreadable_artifact", waiting_path, "captured item unreadable", item
            )
        kind = _normalized_field_value(
            _parse_preamble_fields(text).get("kind"), first_word=True
        )
    if kind not in WORKSPACE_ARTIFACT_KINDS:
        return None, _header_finding(
            "invalid_dependency", waiting_path, "captured item has no kind", item
        )
    return (kind, item, ""), None


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


def _listed_brief_files(root: Path | None) -> frozenset[str]:
    """Return the paths of the regular files listed in the briefs directory.

    `docs/product/briefs/`, `docs/product/`, and `docs/` must each be a real
    directory, not a symbolic link, resolving beneath the resolved root. Any
    failed condition or `OSError` lists nothing, so a cooled child's scope stays
    unknown. Nothing is opened and no declared value is resolved through the
    filesystem: the caller compares strings against this listing.
    """
    if root is None:
        return frozenset()
    try:
        resolved_root = root.resolve()
        for directory in ("docs/product/briefs", "docs/product", "docs"):
            path = root / directory
            if not stat.S_ISDIR(os.lstat(path).st_mode):
                return frozenset()
            if not path.resolve().is_relative_to(resolved_root):
                return frozenset()
        directory_path = root / "docs/product/briefs"
        return frozenset(
            f"docs/product/briefs/{name}"
            for name in os.listdir(directory_path)  # noqa: PTH208
            if stat.S_ISREG(os.lstat(directory_path / name).st_mode)
        )
    except OSError:
        return frozenset()


def _brief_child_spec_states(
    memberships: list[WorkspaceMembership],
    workspace: dict,
    root: Path | None,
    cooled: frozenset[Path],
) -> tuple[dict[str, set[str]], frozenset[str], frozenset[str]]:
    """Map each brief to its children's observed states; flag unevaluable scope.

    Returns (states, briefs_with_cooled_children, cooled_scope_unknown).

    states maps each brief path to the set of states contributed by its
    non-cooled child spec memberships. A cooled child contributes no state at
    all: its status would come from `_membership_status`, which derives state
    from the collection alone and so fabricates "Shipped" for anything in
    `work.shipped`.

    briefs_with_cooled_children names the briefs a cooled child declares
    through `source.parent` **and whose declaration resolves** to a registered
    brief membership or a listed brief file. A declaration naming no registered
    brief membership and no listed brief file goes to
    cooled_scope_unknown instead. For the resolving briefs `invalid_child_scope`
    is unevaluable and a `kind="brief"` dependency on that brief fails closed,
    so a lifecycle record cannot erase or create a finding about a different
    artifact.

    cooled_scope_unknown names every cooled spec entry whose parent scope is
    not established: the `source.parent` key is absent, or it holds a value that
    names no registered brief membership and no listed brief file. Those entries are named in a
    `cooled_child_scope_unknown` finding and every `kind="brief"` dependency
    fails closed while any of them exists, because the brief such a child
    belongs to is precisely what is unknown.

    A declared *empty* value is a third, distinct answer: it says the spec has
    no parent brief, attributes nothing, and releases every dependency. That is
    what makes failing closed affordable — a maintainer clears the refusal by
    declaring the truth either way, rather than by having no way out.

    Accepted limitation: a declared empty value on an already-cooled entry is
    trusted rather than verified. The comparison against the artifact body runs
    only while the artifact is uncooled, so a value declared after the lifecycle
    record lands is never checked against anything.
    """
    states: dict[str, set[str]] = {}
    briefs_affected: set[str] = set()
    scope_unknown: set[str] = set()
    # Resolution is by entry *kind*, never by collection name. Three separate
    # reviews found the collection test wrong in both directions: it admitted a
    # mis-collected spec sitting in a brief queue, which resolved a declared
    # value that names no brief at all; and it missed a brief legitimately
    # registered in `backlog.open`, which refused a correctly declared child
    # with no repair available — declaring a resolving path was already done,
    # and declaring empty would be false.
    #
    brief_membership_paths = {
        membership.entry.path
        for membership in memberships
        if membership.entry.kind == "brief" and membership.entry.path is not None
    }
    # Listed on first need, once per reconciliation.
    brief_files: frozenset[str] | None = None
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
            # Three answers, read from the entry alone. The raw attribute is
            # what separates the second from the third: the normalizer collapses
            # a declared "none" and an absent key to the same None, so it cannot
            # tell "this spec has no parent" from "nobody recorded whether it
            # has one".
            raw_parent = entry.source.parent
            source_parent = _resolved_provenance_parent(
                raw_parent, require_local_brief=True
            )
            if source_parent is not None:
                if brief_files is None and source_parent not in brief_membership_paths:
                    brief_files = _listed_brief_files(root)
                if source_parent in brief_membership_paths or source_parent in (
                    brief_files or ()
                ):
                    briefs_affected.add(source_parent)
                else:
                    # A declared value naming no registered brief establishes
                    # nothing. Compared as declared, not through the filesystem:
                    # a case-insensitive volume would resolve `Brief-1.md` onto
                    # `brief-1.md` and silently attribute the child to a brief
                    # its entry does not name.
                    scope_unknown.add(entry.path)
            elif raw_parent is None:
                scope_unknown.add(entry.path)
            continue
        metadata = _artifact_metadata(workspace, entry, root)
        # Both sides resolved through the same function the routing checks
        # use. Read raw, a typed header would key `states` by `brief:<slug>`,
        # which no brief path lookup matches.
        parent_paths = {
            path for path in (
                _resolved_provenance_parent(
                    entry.source.parent, require_local_brief=True
                ),
                _resolved_provenance_parent(
                    metadata.parent if metadata is not None else None,
                    require_local_brief=True,
                ),
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
    return states, frozenset(briefs_affected), frozenset(scope_unknown)


def _append_impossible_transition(
    findings: list[RoutingFinding],
    entry: WorkspaceEntry,
    metadata: ArtifactMetadata,
    expected: set[str],
    detail: str,
) -> None:
    if metadata.status not in expected:
        findings.append(_finding("impossible_transition", entry.path, detail))


def _append_captured_lifecycle_findings(
    findings: list[RoutingFinding],
    membership: WorkspaceMembership,
    metadata: ArtifactMetadata,
) -> None:
    """Check a migrated captured membership against its record's `Status:`."""
    entry = membership.entry
    collection = membership.collection
    if metadata.captured_kind != entry.kind:
        findings.append(_finding("impossible_transition", entry.path, "captured kind"))
    elif metadata.status == "Closed" and collection in {
        "backlog.open",
        "shaping_queue.backlog",
        "shaping_queue.active",
    }:
        findings.append(
            _finding("impossible_transition", entry.path, "captured status is Closed")
        )
    elif collection == "backlog.closed":
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


def _append_lifecycle_findings(
    findings: list[RoutingFinding],
    membership: WorkspaceMembership,
    metadata: ArtifactMetadata,
) -> None:
    entry = membership.entry
    collection = membership.collection
    if metadata.captured_kind is not None:
        _append_captured_lifecycle_findings(findings, membership, metadata)
        return
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
    require_local_brief_parent = entry.kind == "spec"
    source_parent = _resolved_provenance_parent(
        entry.source.parent, require_local_brief=require_local_brief_parent
    )
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
    if _captured_membership_form(entry.path) == "unmigrated":
        # Judged from the path alone: the file is never opened.
        findings.append(
            _finding("unmigrated_captured_item", entry.path, "captured item unmigrated")
        )
        return findings
    if metadata is not None and metadata.captured_finding is not None:
        findings.append(metadata.captured_finding)
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
    if metadata.captured_kind is not None:
        # A record carries no provenance, plan, or authority block: only the
        # lifecycle rule applies.
        if not skip_status_lifecycle:
            _append_lifecycle_findings(findings, membership, metadata)
        return findings
    if metadata.authority_error is not None:
        findings.append(
            _finding(metadata.authority_error, entry.path, "source authority block")
        )
    if metadata.refresh_conflict:
        findings.append(_finding("refresh_conflict", entry.path, "unresolved refresh conflict"))
    artifact_parent = _resolved_provenance_parent(
        metadata.parent, require_local_brief=require_local_brief_parent
    )
    if _provenance_path_is_invalid(
        root,
        artifact_parent,
        require_local_brief=require_local_brief_parent,
    ):
        findings.append(
            _finding("invalid_artifact_path", artifact_parent or "", "artifact parent")
        )
    if source_parent != artifact_parent:
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


def _header_edges_by_path(
    memberships: list[WorkspaceMembership],
    root: Path | None,
    cooled: frozenset[Path],
) -> dict[str, HeaderDependencies]:
    """Read each non-cooled local membership's header once, by waiting path.

    A cooled membership is never opened and contributes no entry. Without a
    root nothing can be read, so no edge exists.
    """
    if root is None:
        return {}
    waiting = [
        membership for membership in memberships
        if membership.entry.path is not None
        and not _membership_is_cooled(membership, root, cooled)
        and _captured_membership_form(membership.entry.path) != "unmigrated"
    ]
    if not waiting:
        return {}
    index = build_resolution_index(root, cooled=cooled)
    kinds = {
        membership.entry.path: membership.entry.kind
        for membership in memberships
        if membership.entry.path is not None
    }
    headers: dict[str, HeaderDependencies] = {}
    for membership in waiting:
        path = membership.entry.path
        assert path is not None
        if path in headers:
            continue
        if _captured_membership_form(path) == "migrated":
            # A captured record is read only as a confined file, so a link or a
            # hard link to a cooled body is never opened; its lifecycle check
            # already reports it unreadable.
            content = _migration_file_bytes(root, path)
            headers[path] = (
                HeaderDependencies((), ())
                if content is None
                else header_dependencies_from_text(
                    root,
                    path,
                    content.decode("utf-8", errors="replace"),
                    index=index,
                    membership_kinds=kinds,
                    cooled=cooled,
                )
            )
            continue
        headers[path] = read_header_dependencies(
            root, path, index=index, membership_kinds=kinds, cooled=cooled
        )
    return headers


def _apply_header_edges_to_legacy_view(
    initiatives: list[Initiative], workspace: dict, root: Path, cooled: frozenset[Path]
) -> None:
    """Show each header edge of a canonical membership as the string a typed
    `needs` edge showed, and drop that entry's registry needs from this view.

    The string never resolves, so the legacy lists treat a header edge exactly
    as they treated a typed `needs` edge. Making it resolve would change
    behavior outside the header switch.
    """
    memberships = [
        membership
        for membership in _extract_canonical_memberships(workspace)[0]
        if membership.entry.path is not None
    ]
    if not memberships:
        return
    counts = {
        path: len(header.dependencies)
        for path, header in _header_edges_by_path(memberships, root, cooled).items()
    }
    canonical_paths = {membership.entry.path for membership in memberships}
    for ini in initiatives:
        for entry in (*ini.work.queue, *ini.work.active, *ini.work.shipped):
            if entry.path in canonical_paths:
                entry.needs = ["unsupported-typed-need"] * counts.get(entry.path, 0)
        for shaping_entry in (*ini.shaping.active, *ini.shaping.backlog):
            if shaping_entry.slug in canonical_paths:
                shaping_entry.needs = (
                    ["unsupported-typed-need"] * counts.get(shaping_entry.slug, 0)
                )


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
    cooled_scope_unknown: frozenset[str] = frozenset(),
    header: HeaderDependencies | None = None,
) -> DispatchEvaluation:
    """Evaluate the positive T2 dispatch predicate for one canonical membership.

    `header` holds the waiting item's dependency edges. `entry.needs` decides
    nothing: a non-empty array only earns `unmigrated_needs`.
    """
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
    if entry.needs:
        findings.append(_finding("unmigrated_needs", entry.path, "registry needs"))
    for header_finding in (header.findings if header is not None else ()):
        if header_finding.code == "unreadable_artifact" and any(
            existing.code == header_finding.code and existing.path == header_finding.path
            for existing in findings
        ):
            continue
        findings.append(header_finding)
    for dep in (header.dependencies if header is not None else ()):
        satisfied, finding = _dependency_is_satisfied(
            dep,
            workspace,
            by_path,
            structurally_blocked_paths,
            root,
            cooled,
            briefs_with_cooled_children=briefs_with_cooled_children,
            cooled_scope_unknown=cooled_scope_unknown,
            brief_child_states=brief_child_states,
        )
        if not satisfied and finding is not None:
            # The path came from a header item, so it is bounded like any other
            # echoed value: a failing path loses its content, not its code.
            findings.append(
                dataclasses.replace(
                    finding, path=_bounded_finding_identifier(finding.path)
                )
            )
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


def cooled_work_entry_paths(
    workspace: dict,
    root: Path | None,
    cooled: frozenset[Path],
) -> dict[str, set[tuple[str, int]]]:
    """Return reconciliation's cooled `work.*` membership positions by initiative.

    Closeout must not re-derive an artifact path from an entry to ask whether it
    is cooled: an entry may be canonical (`docs/specs/<slug>/spec.md`), legacy
    (`spec/<slug>`), a bare slug the canonical layer refuses to model at all, or
    a non-spec kind, and each has a different mapping — or none. Re-deriving
    picks one mapping and silently disagrees with reconciliation on the rest.

    Each identity is the `(collection, entry_index)` position the membership was
    parsed from. Position is the only thing that distinguishes two lifecycle
    entries in every case: no value carried by an entry is unique. A raw path is
    not identity — `{path = "spec/x", kind = "defect"}` is a valid canonical
    membership whose path equals a legacy `"spec/x"` entry's stored form — and
    neither is `(path, kind)`, because an entry the canonical layer rejects
    still reaches closeout through its own parse and can reproduce any pair.

    Both sides enumerate one raw TOML array in order and emit exactly one record
    per element: this function's caller walks `enumerate(entries)`, and the
    initiative parse builds `queue` and `active` by list comprehension over those
    same arrays. So index `i` names the same element on both sides.
    """
    memberships, _legacy_memberships, _findings, _blocked = (
        _extract_canonical_memberships(workspace)
    )
    by_initiative: dict[str, set[tuple[str, int]]] = {}
    for membership in memberships:
        if not membership.collection.startswith("work."):
            continue
        if _membership_is_cooled(membership, root, cooled):
            by_initiative.setdefault(membership.ini_slug, set()).add(
                (membership.collection, membership.entry_index)
            )
    return by_initiative


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
        parse_blocked_memberships,
    ) = _extract_canonical_memberships(workspace)
    parse_blocked_path_counts: dict[str, int] = {}
    for blocked in parse_blocked_memberships:
        path = blocked.canonical_artifact_path
        parse_blocked_path_counts[path] = parse_blocked_path_counts.get(path, 0) + 1
    # Cooling is applied at evaluation and emission, never here. Every fact
    # derived below — by_path, duplicate_paths, cycle_paths, and the structural
    # loop — must see a cooled artifact as *cooled*, not as *absent*, or a
    # lifecycle record silently erases unrelated conclusions about it. What the
    # cooled set governs is the artifact *body*: for a cooled membership the
    # structural loop and _brief_child_spec_states skip the predicates that would
    # have to open it, keeping the ones derived from the workspace entry alone.
    parse_blocked_paths = set(parse_blocked_path_counts)
    local_memberships = [
        membership for membership in memberships if membership.entry.path is not None
    ]
    by_path: dict[str, list[WorkspaceMembership]] = {}
    for membership in local_memberships:
        assert membership.entry.path is not None
        by_path.setdefault(membership.entry.path, []).append(membership)
    duplicate_paths = {
        path
        for path, items in by_path.items()
        if len(items) > 1
    }
    # Alias-refused paths: canonical reconciliation may decode a historical alias
    # only to refuse. A canonical entry stays non-dispatchable while any historical
    # entry that the retained decoder maps to the same artifact path survives
    # anywhere in the workspace. One extraction per reconciliation run.
    _alias_refused_paths = {
        _alias_path
        for _m in extract_legacy_migration_memberships(workspace)
        if (_alias_path := _legacy_canonical_alias(_m.entry)) is not None
        and _alias_path in by_path
    }
    duplicate_paths.update(_alias_refused_paths)
    parse_only_duplicate_paths = {
        path
        for path, count in parse_blocked_path_counts.items()
        if count > 1 and path not in by_path
    }
    parse_only_duplicate_findings = [
        _finding("duplicate_membership", path, "duplicate lifecycle entry")
        for path in sorted(parse_only_duplicate_paths)
    ]
    headers = _header_edges_by_path(local_memberships, root, cooled)
    header_edges = {path: header.dependencies for path, header in headers.items()}
    cycle_paths = _dependency_cycles(local_memberships, header_edges)
    brief_child_states, briefs_with_cooled_children, cooled_scope_unknown = (
        _brief_child_spec_states(
            local_memberships, workspace, root, cooled,
        )
    )
    # Emitted here rather than in `_structural_findings`, whose findings add
    # their entry to `structurally_blocked_paths` — which refuses every
    # dependency on that path before any kind test, widening this refusal past
    # `kind = "brief"`.
    cooled_scope_findings = [
        _finding("cooled_child_scope_unknown", path, "cooled child parent scope")
        for path in sorted(cooled_scope_unknown)
    ]
    global_invalid_workspace = any(
        finding.code == "invalid_workspace" for finding in parse_findings
    )
    duplicate_paths.update(path for path in parse_blocked_paths if path in by_path)
    structurally_blocked_paths: set[str] = {
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
                # which are still owed whatever the artifact's own state
                # is.
                cooled_membership_findings.extend(member_findings)
        if membership_cooled and membership.entry.needs:
            cooled_membership_findings.append(
                _finding("unmigrated_needs", membership.entry.path, "registry needs")
            )
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
            cooled_scope_unknown=cooled_scope_unknown,
            header=headers.get(membership.entry.path or ""),
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
        *parse_only_duplicate_findings,
        *cooled_membership_findings,
        *cooled_scope_findings,
        *(finding for evaluation in evaluations for finding in evaluation.findings),
    ]
    return CanonicalWorkspaceResult(
        cooled=cooled,
        memberships=memberships,
        legacy_memberships=[],
        findings=findings,
        evaluations=evaluations,
        dispatch_by_path=dispatch_by_path,
        header_edges=header_edges,
    )


def _has_unsupported_open_entry(shaping_raw: object, brief_raw: object) -> bool:
    """True when an open shaping or brief collection holds a non-canonical entry."""

    def raw_entries(section: object, name: str) -> list[object]:
        if not isinstance(section, dict):
            return []
        entries = section.get(name, [])
        if isinstance(entries, list):
            return entries
        return [] if entries in ("", None) else [entries]

    open_entries = [
        *raw_entries(shaping_raw, "active"),
        *raw_entries(shaping_raw, "backlog"),
        *raw_entries(brief_raw, "executing"),
        *raw_entries(brief_raw, "ready"),
        *raw_entries(brief_raw, "draft"),
    ]
    return any(parse_workspace_entry(raw)[0] is None for raw in open_entries)


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
            has_unsupported_open_entry=_has_unsupported_open_entry(
                shaping_raw, brief_raw
            ),
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

# `\Z`, not `$`: this validates a whole dependency token, not a line, and `$`
# also matches just before a trailing newline. `ini-002:work:spec/foo\n` matched
# and yielded the clean `spec/foo`, so a malformed token compared equal to a
# shipped entry's path and the dependency reported satisfied. A trailing tab was
# already fail-closed; only the newline leaked, and only because of the anchor.
_CROSS_INI_RE = re.compile(r'^(ini-[^:]+):work:(.+)\Z')


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
        # nothing". The non-empty requirement is enforced elsewhere, against a
        # different source: the brief-coverage lint reads the brief's own Spec
        # map and fails when a Shipped brief's mapped children are empty or not
        # all shipped. This projection deliberately does not read that section,
        # so the two checks cover the same rule over different inputs and
        # neither substitutes for the other.
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
    cooled: frozenset[Path] = frozenset(),
) -> tuple[list[ReconciliationFinding], int]:
    """Type 1 audit: counts the spec files it walks and reports nothing.

    A spec needs no workspace entry, so a spec no entry names is not a finding.
    Returns (findings, files_read) with findings always empty.

    Two callers: run_reconciliation and analyze. Never called by analyze_bounded.
    """
    findings: list[ReconciliationFinding] = []
    files_read = 0
    specs_dir = root / "docs" / "specs"

    # The walk and its `files_read` counter stay so the reconciliation output
    # still reports how many spec files the audit covered, though it reports none.
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
            # Skip a directory already visited (in-root junction to a previously
            # scanned sibling) so its spec.md is not counted twice.
            # dirnames.clear() prevents further descent.
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
            if _current_resolved / "spec.md" in cooled:
                continue
            files_read += 1
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
    # repair-plan and the migration paths predate cooling and keep their
    # original behaviour: they see an empty cooled set, so their operations
    # still reach cooled entries. Whether
    # cooling constrains them is a deliberate, separately decided change.
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
    _apply_header_edges_to_legacy_view(initiatives, workspace, root, cooled)

    all_classifications: list[EntryClassification] = []
    all_shaping: list[ShapingClassification] = []
    for ini in initiatives:
        if ini.status not in ("active",):
            continue   # Only active initiatives for ready/blocked and shaping
        all_classifications.extend(classify_entries(ini, initiatives))
        all_shaping.extend(classify_shaping_entries(ini, initiatives))

    # Call helpers directly (not via run_reconciliation) to obtain split file counts
    type1_findings, type1_files = _run_type1_scan(root, cooled)
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


# ── Argless work-loop resume helper ──────────────────────────────────────────


# ── work-loop shaping-item guard helper ──────────────────────────────────────

# Explicitly recognised shaping types. Only entries with one of these types
# in [backlog].open feed the `shaping.top_level_backlog` status key.
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


# ── work-loop Step 0 stale-queue check ───────────────────────────────────────


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
        # A registry `needs` array travels with the moved entry untouched, so
        # `unmigrated_needs` does not stop the move. The edge migration is its
        # own repair.
        if blocking_codes - {
            "impossible_transition",
            "unapproved_spec",
            "unmigrated_needs",
        }:
            return False, "type2-queue-canonical-blocked"
        # Defence in depth: canonical reconciliation already refuses dispatch
        # while a historical alias survives, but the repair seam also checks so
        # moving the entry does not leave the spec in two lifecycle collections.
        if any(
            _legacy_canonical_alias(membership.entry) == spec_path
            for membership in extract_legacy_migration_memberships(workspace)
        ):
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
