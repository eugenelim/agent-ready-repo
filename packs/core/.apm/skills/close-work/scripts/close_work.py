#!/usr/bin/env python3
"""Deterministic Wave 4 closeout and immediate-disposition helpers.

The module classifies bounded facts and applies an exact, freshly confirmed file
deletion. It does not choose policy, infer authority, scan for work, count cooling
time, migrate records, or rewrite Git history.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import os
import re
import secrets
import stat
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

sys.stdout.reconfigure(encoding="utf-8", errors="strict")  # type: ignore[union-attr]
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")  # type: ignore[union-attr]

SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
MAX_TEXT_LENGTH = 512
MAX_SUMMARY_LENGTH = 160
MAX_TARGETS = 32
MAX_EVIDENCE_REFS = 32
MAX_ENUMERATION_ENTRIES = 256
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
IMMEDIATE_DISPOSITIONS = frozenset(
    {"discard-local", "delete-before-push", "delete-before-merge"}
)
POST_CLOSEOUT_RESULTS = frozenset(
    {"Cooling", "Retained", "Retired", "Reclassified", "ExternalAdvisory"}
)
_ISSUED_CONFIRMATIONS: dict[str, object] = {}
_ISSUED_PREVIEWS: dict[str, object] = {}
_CONFIRMED_PREVIEWS: set[str] = set()
_ISSUED_HUMAN_PROOFS: set[str] = set()
_CONSUMED_CONFIRMATIONS: set[str] = set()
_ISSUED_COORDINATION_AUTHORITIES: dict[str, object] = {}
_file_safety_module: object | None = None
_surface_resolver_module: object | None = None
_ACTOR_ROLE_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
_GRANT_PREFIXES = ("approval:", "grant:", "policy:")
_PROVENANCE_PREFIXES = ("host-session:", "session:")
_SOURCE_AUTHORITIES = frozenset({"repository-origin", "tool-session"})
_CLASSIFIER_SOURCE_AUTHORITIES = _SOURCE_AUTHORITIES | {"external-system"}
_WRITE_AUTHORITIES = frozenset({"repository-maintainer", "tool-session"})
_DELETE_AUTHORITIES = frozenset({"repository-owned", "tool-owned"})
_DIR_FD_EFFECT_SUPPORTED = all(
    function in os.supports_dir_fd
    for function in (os.link, os.open, os.stat, os.unlink)
)
_NOFOLLOW_STAT_SUPPORTED = os.stat in os.supports_follow_symlinks
_NOFOLLOW_LINK_SUPPORTED = os.link in os.supports_follow_symlinks


@dataclasses.dataclass(frozen=True)
class LifecycleProjection:
    """Read-only projection of one delivery record's current lifecycle phase."""

    lifecycle_phase: str
    blocker: str | None = None
    permission_granted: bool = False
    mutated: tuple[Path, ...] = ()


@dataclasses.dataclass(frozen=True)
class DispositionCandidate:
    """Closed facts used to recommend disposition intent."""

    lifecycle_outcome: str
    persisted: bool
    delivered: bool
    pushed: bool
    removal_change: bool = False
    removal_integrated: bool = False
    lasting_facts_settled: bool = False
    obligations_settled: bool = False
    live_dependencies: bool = False
    retain_exception: bool = False
    source_authority: str | None = None
    write_authority: str | None = None
    deletion_authority: str | None = None


@dataclasses.dataclass(frozen=True)
class DispositionDecision:
    """Mutation-free disposition recommendation or stable blocker."""

    disposition: str | None
    blocker: str | None = None
    permission_granted: bool = False
    mutated: tuple[Path, ...] = ()
    history_rewrite: bool = False


@dataclasses.dataclass(frozen=True)
class Assessment:
    """Small mutation-free semantic assessment result."""

    status: str
    code: str | None = None
    mutated: tuple[Path, ...] = ()


@dataclasses.dataclass(frozen=True)
class TargetFingerprint:
    """One confined target identity captured by a deletion preview."""

    relative_path: str
    sha256: str
    device: int
    inode: int
    size: int


@dataclasses.dataclass(frozen=True)
class DeletionPreview:
    """Exact mutation-free preview awaiting separate human confirmation."""

    code: str
    repository_root: Path
    enumeration_root: Path
    enumeration_mode: str
    surface_role: str
    logical_locator: str
    physical_locator: str
    revision_or_fingerprint: str
    surface_resolution_fingerprint: str
    surface_candidates: tuple[object, ...]
    targets: tuple[Path, ...]
    target_fingerprints: tuple[TargetFingerprint, ...]
    target_fingerprint: str
    disposition: str
    disposition_candidate: DispositionCandidate
    disposition_eligibility_fingerprint: str
    completion_evidence_ref: str
    durable_output_evidence_refs: tuple[str, ...]
    pushed: bool
    removal_integrated: bool
    source_state_evidence_ref: str
    source_authority: str
    source_authority_evidence_ref: str
    write_authority: str
    write_authority_evidence_ref: str
    deletion_authority: str
    deletion_authority_evidence_ref: str
    authorized_actor_role: str
    proposer_role: str
    proposer_evidence_ref: str
    grant_source: str
    action: str
    host_session_provenance: str
    authority_resource: str
    authority_resolution_evidence_ref: str
    authority_issue_digest: str
    confirmation_challenge: str
    binding_digest: str
    permission_granted: bool = False
    mutated: tuple[Path, ...] = ()


@dataclasses.dataclass(frozen=True)
class DeletionConfirmation:
    """Single-use human confirmation bound to every preview fact."""

    confirmation_id: str
    human_evidence_ref: str
    confirmation_challenge: str
    issue_digest: str
    binding_digest: str
    enumeration_mode: str
    surface_role: str
    logical_locator: str
    physical_locator: str
    revision_or_fingerprint: str
    surface_resolution_fingerprint: str
    resource_file_set: tuple[str, ...]
    target_fingerprints: tuple[TargetFingerprint, ...]
    target_fingerprint: str
    disposition: str
    disposition_eligibility_fingerprint: str
    completion_evidence_ref: str
    durable_output_evidence_refs: tuple[str, ...]
    pushed: bool
    removal_integrated: bool
    source_state_evidence_ref: str
    source_authority: str
    source_authority_evidence_ref: str
    write_authority: str
    write_authority_evidence_ref: str
    deletion_authority: str
    deletion_authority_evidence_ref: str
    authorized_actor_role: str
    proposer_role: str
    proposer_evidence_ref: str
    approver_role: str
    approver_evidence_ref: str
    grant_source: str
    action: str
    host_session_provenance: str
    authority_resource: str
    authority_resolution_evidence_ref: str
    authority_issue_digest: str
    proposed_mutation: str


@dataclasses.dataclass(frozen=True)
class HumanConfirmation:
    """Human-supplied restatement of every fact authorizing one file deletion."""

    confirmation_id: str
    human_evidence_ref: str
    confirmation_challenge: str
    enumeration_mode: str
    surface_role: str
    logical_locator: str
    physical_locator: str
    revision_or_fingerprint: str
    surface_resolution_fingerprint: str
    resource_file_set: tuple[str, ...]
    target_fingerprints: tuple[TargetFingerprint, ...]
    target_fingerprint: str
    disposition: str
    disposition_eligibility_fingerprint: str
    completion_evidence_ref: str
    durable_output_evidence_refs: tuple[str, ...]
    pushed: bool
    removal_integrated: bool
    source_state_evidence_ref: str
    source_authority: str
    source_authority_evidence_ref: str
    write_authority: str
    write_authority_evidence_ref: str
    deletion_authority: str
    deletion_authority_evidence_ref: str
    authorized_actor_role: str
    proposer_role: str
    proposer_evidence_ref: str
    approver_role: str
    approver_evidence_ref: str
    grant_source: str
    action: str
    host_session_provenance: str
    authority_resource: str
    authority_resolution_evidence_ref: str
    authority_issue_digest: str
    proposed_mutation: str


@dataclasses.dataclass(frozen=True)
class ResidualHardlinkEvidence:
    """Bounded inode evidence for a terminal residual-hardlink result."""

    confirmed_fingerprint: TargetFingerprint
    observed_link_count: int
    observed_device: int
    observed_inode: int
    observed_size: int


@dataclasses.dataclass(frozen=True)
class DeletionResult:
    """Terminal deletion result with a stable code and exact mutation list."""

    code: str
    mutated: tuple[Path, ...] = ()
    permission_granted: bool = False
    recovery_residue: tuple[Path, ...] = ()
    residual_evidence: ResidualHardlinkEvidence | None = None
    # Closed vocabulary, set on every terminal mutated *failure* outcome
    # (`rollback-failed`, `residual-hardlink`) so the maintainer recovery the
    # skill directs is aimed at content of known identity. A successful
    # `deleted` leaves it None: there is no residue to identify.
    #   "identity-confirmed"  a descriptor proved the residue is the confirmed inode
    #   "identity-mismatch"   a descriptor proved it is NOT the confirmed inode
    #   "unverified"          no descriptor, or inspection failed: identity unknown
    residue_state: str | None = None


@dataclasses.dataclass(frozen=True)
class MutationBinding:
    """Exact authority tuple for one proposed coordination mutation."""

    authorized_actor_role: str
    grant_source: str
    action: str
    resource: str
    evidence_ref: str
    host_session_provenance: str


@dataclasses.dataclass(frozen=True)
class ResolvedAuthorityFact:
    """Separately resolved grant fact bound to one coordination effect."""

    authorized_actor_role: str
    grant_source: str
    action: str
    resource: str
    evidence_ref: str
    host_session_provenance: str
    authority_evidence_ref: str
    issue_digest: str


@dataclasses.dataclass(frozen=True)
class PauseOverlay:
    """Reference-only pause envelope; never a copy of delivery content."""

    contract_locator: str
    contract_fingerprint: str
    plan_locator: str
    plan_fingerprint: str
    artifact_status: str
    evidence_refs: tuple[str, ...]
    coordination_locator: str
    restore_action: str


@dataclasses.dataclass(frozen=True)
class PauseResult:
    """Mutation-free pause decision and proposed restorable overlay."""

    code: str
    lifecycle_phase: str
    overlay: str | None = None
    disposition: str | None = None
    cooling_started: bool = False
    binding: MutationBinding | None = None
    record: PauseOverlay | None = None
    permission_granted: bool = False
    mutated: tuple[Path, ...] = ()


@dataclasses.dataclass(frozen=True)
class CompletionReceipt:
    """The only four fields retained for a live downstream dependency."""

    delivery_id: str
    outcome: str
    completion_event: str
    evidence_ref: str


@dataclasses.dataclass(frozen=True)
class ReceiptResult:
    """Mutation-free receipt write/removal decision."""

    code: str
    disposition: str | None = None
    schema_created: bool = False
    receipt: CompletionReceipt | None = None
    binding: MutationBinding | None = None
    confirmation_fingerprint: str | None = None
    permission_granted: bool = False
    mutated: tuple[Path, ...] = ()


@dataclasses.dataclass(frozen=True)
class InitiativeCloseoutResult:
    """Separate coordination compaction from artifact-family treatment."""

    code: str
    workspace_action: str | None = None
    artifact_action: str | None = None
    lifecycle_schema_created: bool = False
    binding: MutationBinding | None = None
    coordination_fingerprint: str | None = None
    permission_granted: bool = False
    mutated: tuple[Path, ...] = ()


@dataclasses.dataclass(frozen=True)
class ArtifactCloseoutResult:
    """Lifecycle classification for an artifact with contextual dependencies."""

    code: str
    lifecycle_phase: str
    disposition: str | None = None
    permission_granted: bool = False
    mutated: tuple[Path, ...] = ()


def _bounded_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    if len(value) > MAX_TEXT_LENGTH:
        raise ValueError(f"{name} exceeds {MAX_TEXT_LENGTH} characters")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"{name} contains a control character")
    return value


def _bounded_refs(name: str, values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence")
    if not values or len(values) > MAX_EVIDENCE_REFS:
        raise ValueError(f"{name} must contain 1..{MAX_EVIDENCE_REFS} references")
    result: list[str] = []
    for value in values:
        reference = _bounded_text(name, value)
        if reference not in result:
            result.append(reference)
    return tuple(result)


def resolve_mutation_authority(
    *,
    grant_record: Mapping[str, object],
    authority_evidence_ref: object,
) -> ResolvedAuthorityFact | None:
    """Mint one authority fact from a separately reacquired trusted grant record."""
    if not isinstance(grant_record, Mapping):
        return None
    expected = {
        "authorized_actor_role",
        "grant_source",
        "action",
        "resource",
        "evidence_ref",
        "host_session_provenance",
    }
    if set(grant_record) != expected:
        return None
    try:
        actor = _bounded_text(
            "authorized_actor_role", grant_record["authorized_actor_role"]
        )
        grant = _bounded_text("grant_source", grant_record["grant_source"])
        action = _bounded_text("action", grant_record["action"])
        resource = _bounded_text("resource", grant_record["resource"])
        evidence = _bounded_text("evidence_ref", grant_record["evidence_ref"])
        provenance = _bounded_text(
            "host_session_provenance", grant_record["host_session_provenance"]
        )
        authority_ref = _bounded_text(
            "authority_evidence_ref", authority_evidence_ref
        )
    except ValueError:
        return None
    if (
        not _ACTOR_ROLE_RE.fullmatch(actor)
        or not grant.startswith(_GRANT_PREFIXES)
        or not provenance.startswith(_PROVENANCE_PREFIXES)
    ):
        return None
    payload = {
        "authorized_actor_role": actor,
        "grant_source": grant,
        "action": action,
        "resource": resource,
        "evidence_ref": evidence,
        "host_session_provenance": provenance,
        "authority_evidence_ref": authority_ref,
    }
    digest = hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
    ).hexdigest()
    fact = ResolvedAuthorityFact(**payload, issue_digest=digest)
    _ISSUED_COORDINATION_AUTHORITIES[digest] = fact
    return fact


def _mutation_binding(
    *,
    authority_fact: object,
    authorized_actor_role: object,
    grant_source: object,
    action: object,
    resource: object,
    evidence_ref: object,
    host_session_provenance: object,
    expected_action: str,
) -> MutationBinding | None:
    """Validate the full non-personal authority tuple for one proposed effect."""
    try:
        actor = _bounded_text("authorized_actor_role", authorized_actor_role)
        grant = _bounded_text("grant_source", grant_source)
        requested_action = _bounded_text("action", action)
        exact_resource = _bounded_text("resource", resource)
        evidence = _bounded_text("evidence_ref", evidence_ref)
        provenance = _bounded_text(
            "host_session_provenance", host_session_provenance
        )
    except ValueError:
        return None
    if (
        not isinstance(authority_fact, ResolvedAuthorityFact)
        or _ISSUED_COORDINATION_AUTHORITIES.get(authority_fact.issue_digest)
        is not authority_fact
        or not _ACTOR_ROLE_RE.fullmatch(actor)
        or not grant.startswith(_GRANT_PREFIXES)
        or requested_action != expected_action
        or not provenance.startswith(_PROVENANCE_PREFIXES)
    ):
        return None
    binding = MutationBinding(
        authorized_actor_role=actor,
        grant_source=grant,
        action=requested_action,
        resource=exact_resource,
        evidence_ref=evidence,
        host_session_provenance=provenance,
    )
    if dataclasses.asdict(binding) != {
        key: value
        for key, value in dataclasses.asdict(authority_fact).items()
        if key not in {"authority_evidence_ref", "issue_digest"}
    }:
        return None
    return binding


def _bounded_fingerprint(name: str, value: object) -> str:
    fingerprint = _bounded_text(name, value)
    if not fingerprint.startswith("sha256:"):
        raise ValueError(f"{name} must be a sha256 fingerprint")
    return fingerprint


def plan_pause(
    *,
    work_mode: str,
    artifact_status: str,
    coordination_surface: str | None,
    writable: bool,
    authority_fact: object = None,
    authorized_actor_role: object = None,
    grant_source: object = None,
    action: object = None,
    resource: object = None,
    evidence_ref: object = None,
    host_session_provenance: object = None,
    contract_locator: object = None,
    contract_fingerprint: object = None,
    plan_locator: object = None,
    plan_fingerprint: object = None,
    restore_action: object = None,
    evidence_refs: Sequence[str] | None = None,
    **untrusted_content: object,
) -> PauseResult:
    """Plan a reference-only pause overlay without starting closeout."""
    phase = artifact_status if artifact_status in {"Ready", "Implementing"} else "Drafting"
    if untrusted_content:
        return PauseResult("untrusted-content-refused", phase)
    if work_mode == "direct-light":
        return PauseResult("work-intake-promotion-required", "Drafting")
    if work_mode != "spec-backed" or artifact_status not in {"Ready", "Implementing"}:
        return PauseResult("pause-state-ineligible", phase)
    if not writable or coordination_surface is None:
        return PauseResult("pause-surface-required", artifact_status)
    binding = _mutation_binding(
        authority_fact=authority_fact,
        authorized_actor_role=authorized_actor_role,
        grant_source=grant_source,
        action=action,
        resource=resource,
        evidence_ref=evidence_ref,
        host_session_provenance=host_session_provenance,
        expected_action="write-pause-overlay",
    )
    if binding is None or binding.resource != coordination_surface:
        return PauseResult("authorization-required", artifact_status)
    try:
        contract_ref = _bounded_text("contract_locator", contract_locator)
        contract_fp = _bounded_fingerprint(
            "contract_fingerprint", contract_fingerprint
        )
        plan_ref = _bounded_text("plan_locator", plan_locator)
        plan_fp = _bounded_fingerprint("plan_fingerprint", plan_fingerprint)
        restore = _bounded_text("restore_action", restore_action)
        if not re.fullmatch(r"resume-[a-z0-9-]{1,120}", restore):
            raise ValueError("restore_action must be structured")
        refs = _bounded_refs(
            "evidence_refs",
            evidence_refs if evidence_refs is not None else (str(evidence_ref),),
        )
    except ValueError:
        return PauseResult("pause-envelope-invalid", artifact_status)
    record = PauseOverlay(
        contract_locator=contract_ref,
        contract_fingerprint=contract_fp,
        plan_locator=plan_ref,
        plan_fingerprint=plan_fp,
        artifact_status=artifact_status,
        evidence_refs=refs,
        coordination_locator=coordination_surface,
        restore_action=restore,
    )
    return PauseResult(
        "pause-overlay-ready",
        artifact_status,
        overlay="Paused",
        binding=binding,
        record=record,
    )


def validate_pause_resume(
    overlay: PauseOverlay,
    *,
    contract_locator: str,
    contract_fingerprint: str,
    plan_locator: str,
    plan_fingerprint: str,
    artifact_status: str,
    evidence_refs: Sequence[str],
    coordination_locator: str,
    restore_action: str,
) -> PauseResult:
    """Reacquire every pause reference before restoring the same context."""
    if not isinstance(overlay, PauseOverlay):
        return PauseResult("pause-envelope-invalid", "Drafting")
    stored_phase = "Drafting"
    try:
        stored_contract_locator = _bounded_text(
            "stored_contract_locator", overlay.contract_locator
        )
        stored_contract_fingerprint = _bounded_fingerprint(
            "stored_contract_fingerprint", overlay.contract_fingerprint
        )
        stored_plan_locator = _bounded_text(
            "stored_plan_locator", overlay.plan_locator
        )
        stored_plan_fingerprint = _bounded_fingerprint(
            "stored_plan_fingerprint", overlay.plan_fingerprint
        )
        if overlay.artifact_status not in {"Ready", "Implementing"}:
            raise ValueError("stored artifact status is invalid")
        stored_phase = overlay.artifact_status
        stored_refs = _bounded_refs("stored_evidence_refs", overlay.evidence_refs)
        stored_coordination = _bounded_text(
            "stored_coordination_locator", overlay.coordination_locator
        )
        stored_restore = _bounded_text(
            "stored_restore_action", overlay.restore_action
        )
        if not re.fullmatch(r"resume-[a-z0-9-]{1,120}", stored_restore):
            raise ValueError("stored restore action is invalid")
        current_contract_locator = _bounded_text(
            "contract_locator", contract_locator
        )
        current_contract_fingerprint = _bounded_fingerprint(
            "contract_fingerprint", contract_fingerprint
        )
        current_plan_locator = _bounded_text("plan_locator", plan_locator)
        current_plan_fingerprint = _bounded_fingerprint(
            "plan_fingerprint", plan_fingerprint
        )
        current_coordination = _bounded_text(
            "coordination_locator", coordination_locator
        )
        current_restore = _bounded_text("restore_action", restore_action)
        if not re.fullmatch(r"resume-[a-z0-9-]{1,120}", current_restore):
            raise ValueError("current restore action is invalid")
        refs = _bounded_refs("evidence_refs", evidence_refs)
    except ValueError:
        return PauseResult("pause-evidence-unavailable", stored_phase)
    if (
        current_contract_locator != stored_contract_locator
        or current_contract_fingerprint != stored_contract_fingerprint
        or current_plan_locator != stored_plan_locator
        or current_plan_fingerprint != stored_plan_fingerprint
        or artifact_status != overlay.artifact_status
        or refs != stored_refs
        or current_coordination != stored_coordination
        or current_restore != stored_restore
    ):
        return PauseResult("pause-reference-drift", stored_phase)
    return PauseResult(
        "pause-restorable",
        overlay.artifact_status,
        overlay="Paused",
        record=overlay,
    )


def plan_completion_receipt(
    *,
    live_dependency: bool,
    compatible_surface: str | None,
    authority_fact: object = None,
    delivery_id: object = None,
    outcome: object = None,
    completion_event: object = None,
    evidence_ref: object = None,
    authorized_actor_role: object = None,
    grant_source: object = None,
    action: object = None,
    resource: object = None,
    host_session_provenance: object = None,
) -> ReceiptResult:
    """Plan the exact four-field receipt only on an established surface."""
    if not isinstance(live_dependency, bool):
        return ReceiptResult("dependency-evidence-invalid")
    if not live_dependency:
        return ReceiptResult("receipt-not-required")
    if compatible_surface is None:
        return ReceiptResult(
            "receipt-surface-required", disposition="retain-exception"
        )
    binding = _mutation_binding(
        authority_fact=authority_fact,
        authorized_actor_role=authorized_actor_role,
        grant_source=grant_source,
        action=action,
        resource=resource,
        evidence_ref=evidence_ref,
        host_session_provenance=host_session_provenance,
        expected_action="write-completion-receipt",
    )
    if binding is None or binding.resource != compatible_surface:
        return ReceiptResult("authorization-required")
    try:
        receipt = CompletionReceipt(
            delivery_id=_bounded_text("delivery_id", delivery_id),
            outcome=_bounded_text("outcome", outcome),
            completion_event=_bounded_text("completion_event", completion_event),
            evidence_ref=_bounded_text("evidence_ref", evidence_ref),
        )
    except ValueError:
        return ReceiptResult("receipt-evidence-required")
    return ReceiptResult(
        "receipt-write-confirmation-required", receipt=receipt, binding=binding
    )


def plan_receipt_removal(
    *,
    receipt_fingerprint: object,
    current_receipt_fingerprint: object | None = None,
    current_receipt_evidence_ref: object = None,
    authority_fact: object = None,
    authorized_actor_role: object = None,
    grant_source: object = None,
    action: object = None,
    resource: object = None,
    evidence_ref: object = None,
    host_session_provenance: object = None,
) -> ReceiptResult:
    """Require a separate exact confirmation for last-receipt compaction."""
    binding = _mutation_binding(
        authority_fact=authority_fact,
        authorized_actor_role=authorized_actor_role,
        grant_source=grant_source,
        action=action,
        resource=resource,
        evidence_ref=evidence_ref,
        host_session_provenance=host_session_provenance,
        expected_action="remove-last-completion-receipt",
    )
    if binding is None:
        return ReceiptResult("authorization-required")
    try:
        confirmed = _bounded_fingerprint(
            "receipt_fingerprint", receipt_fingerprint
        )
        if current_receipt_fingerprint is None:
            return ReceiptResult("receipt-fingerprint-unavailable")
        current = _bounded_fingerprint(
            "current_receipt_fingerprint",
            current_receipt_fingerprint,
        )
        _bounded_text(
            "current_receipt_evidence_ref", current_receipt_evidence_ref
        )
    except ValueError:
        return ReceiptResult("receipt-fingerprint-invalid")
    if current != confirmed:
        return ReceiptResult("confirmation-expired")
    return ReceiptResult(
        "receipt-removal-confirmation-required",
        binding=binding,
        confirmation_fingerprint=confirmed,
    )


def plan_initiative_closeout(
    *,
    shaping_residue: Sequence[object],
    build_residue: Sequence[object],
    live_dependencies: Sequence[object],
    contextual_anchor: object | None,
    coordination_fingerprint: object,
    current_coordination_fingerprint: object = None,
    current_coordination_evidence_ref: object = None,
    authority_fact: object = None,
    authorized_actor_role: object = None,
    grant_source: object = None,
    action: object = None,
    resource: object = None,
    evidence_ref: object = None,
    host_session_provenance: object = None,
) -> InitiativeCloseoutResult:
    """Plan workspace compaction independently from artifact retention."""
    binding = _mutation_binding(
        authority_fact=authority_fact,
        authorized_actor_role=authorized_actor_role,
        grant_source=grant_source,
        action=action,
        resource=resource,
        evidence_ref=evidence_ref,
        host_session_provenance=host_session_provenance,
        expected_action="compact-settled-coordination",
    )
    if binding is None:
        return InitiativeCloseoutResult("authorization-required")
    if any(
        isinstance(items, (str, bytes)) or not isinstance(items, Sequence)
        for items in (shaping_residue, build_residue, live_dependencies)
    ):
        return InitiativeCloseoutResult("initiative-evidence-invalid")
    if shaping_residue or build_residue or live_dependencies:
        return InitiativeCloseoutResult("initiative-not-settled")
    try:
        fingerprint = _bounded_fingerprint(
            "coordination_fingerprint", coordination_fingerprint
        )
        if current_coordination_fingerprint is None:
            return InitiativeCloseoutResult("coordination-fingerprint-unavailable")
        current_fingerprint = _bounded_fingerprint(
            "current_coordination_fingerprint", current_coordination_fingerprint
        )
        _bounded_text(
            "current_coordination_evidence_ref",
            current_coordination_evidence_ref,
        )
        anchor = (
            _bounded_text("contextual_anchor", contextual_anchor)
            if contextual_anchor is not None
            else None
        )
    except ValueError:
        return InitiativeCloseoutResult("initiative-evidence-invalid")
    if current_fingerprint != fingerprint:
        return InitiativeCloseoutResult("confirmation-expired")
    if anchor is not None and anchor in {"initiative", "initiative-only"}:
        return InitiativeCloseoutResult(
            "initiative-membership-not-retention-authority"
        )
    artifact_action = (
        "retain-or-reclassify-anchored-family"
        if anchor is not None
        else "classify-artifacts-independently"
    )
    return InitiativeCloseoutResult(
        "initiative-compaction-confirmation-required",
        workspace_action="compact-settled-coordination",
        artifact_action=artifact_action,
        binding=binding,
        coordination_fingerprint=fingerprint,
    )


def classify_artifact_closeout(
    *,
    delivery_status: str,
    live_dependencies: Sequence[str],
    contextual_anchor: str | None,
    durable_outputs_settled: bool,
) -> ArtifactCloseoutResult:
    """Keep an artifact family pending while accepted downstream work cites it."""
    if isinstance(live_dependencies, (str, bytes)) or not isinstance(
        live_dependencies, Sequence
    ):
        return ArtifactCloseoutResult("artifact-evidence-invalid", "Closeout-pending")
    if live_dependencies:
        return ArtifactCloseoutResult("live-dependency", "Closeout-pending")
    if delivery_status != "Shipped" or not durable_outputs_settled:
        return ArtifactCloseoutResult("durable-output-blocker", "Closeout-pending")
    if contextual_anchor is not None:
        return ArtifactCloseoutResult("anchor-review-required", "Closeout-pending")
    return ArtifactCloseoutResult("disposition-classification-ready", "Closeout-pending")


def _load_regular_sibling(path: Path, module_name: str, required: set[str]) -> Any:
    try:
        inspected = os.lstat(path)
    except OSError as exc:
        raise ImportError(f"required helper is unavailable: {path.name}") from exc
    if not stat.S_ISREG(inspected.st_mode) or stat.S_ISLNK(inspected.st_mode):
        raise ImportError(f"required helper is not a regular file: {path.name}")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"required helper cannot be loaded: {path.name}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    missing = sorted(required - set(vars(module)))
    if missing:
        sys.modules.pop(module_name, None)
        raise ImportError(
            f"required helper is incomplete: {path.name}: {', '.join(missing)}"
        )
    return module


def file_safety() -> Any:
    """Load only the co-located byte projection of the blessed helper."""
    global _file_safety_module
    if _file_safety_module is None:
        _file_safety_module = _load_regular_sibling(
            SCRIPT_DIR / "file_safety.py",
            "_close_work_file_safety",
            {
                "UnsafeContentError",
                "validate_confined_directory",
                "list_confined_regular_files",
                "read_confined_regular_file",
                "sha256_confined_regular_file",
            },
        )
    return _file_safety_module


def _in_installed_skills_tree() -> bool:
    """True when this module is running from an installed skills tree.

    `file_safety()` loads a co-located byte projection, so it works wherever
    this module sits. `surface_resolver()` is different: it reaches out of its
    own directory into a sibling skill. Under the packaged closure at
    `agentbundle/_data/` there are no sibling skills, so `SKILLS_DIR` resolves
    to an unrelated package directory and the reach would execute whatever
    happened to occupy that relative path. Every projected layout keeps the
    `skills/<skill>/scripts` shape, so its absence is the signal.
    """
    return SCRIPT_DIR.name == "scripts" and SKILLS_DIR.name == "skills"


def surface_resolver() -> Any:
    """Load the installed Wave 1 resolver from its sibling skill, with no fallback."""
    global _surface_resolver_module
    if not _in_installed_skills_tree():
        raise ImportError(
            "surface_resolver is unavailable outside an installed skills tree"
        )
    if _surface_resolver_module is None:
        _surface_resolver_module = _load_regular_sibling(
            SKILLS_DIR / "work-intake" / "scripts" / "surface_resolver.py",
            "_close_work_surface_resolver",
            {"SurfaceCandidate", "resolve_surface", "SURFACE_ROLES"},
        )
    return _surface_resolver_module


def project_lifecycle(
    *,
    spec_status: str | None,
    plan_status: str | None,
    work_mode: str,
    outcome: str | None,
    paused: bool,
    receipt_present: bool,
    workspace_room: str | None,
    post_closeout_result: str | None,
    live_dependencies: Sequence[str],
    initiative_residue: bool,
) -> LifecycleProjection:
    """Project the RFC lifecycle table without changing any source record."""
    del workspace_room
    if work_mode == "direct-light":
        if post_closeout_result is not None:
            if post_closeout_result not in POST_CLOSEOUT_RESULTS:
                return LifecycleProjection(
                    "Closeout-pending", "post-closeout-result-invalid"
                )
            return LifecycleProjection("Post-closeout")
        if outcome in {"completed", "abandoned", "superseded"}:
            if initiative_residue:
                return LifecycleProjection("Closeout-pending", "initiative-residue")
            if live_dependencies:
                return LifecycleProjection("Closeout-pending", "live-dependency")
            return LifecycleProjection("Closeout-pending")
        if paused:
            return LifecycleProjection("Drafting", "promote-through-work-intake")
        return LifecycleProjection("Drafting")

    phase_pairs = {
        ("Draft", "Drafting"): "Drafting",
        ("Approved", "Approved"): "Ready",
        ("Implementing", "Executing"): "Implementing",
        ("Shipped", "Done"): "Closeout-pending",
    }
    authoritative_phase = phase_pairs.get((spec_status, plan_status))
    if authoritative_phase is None:
        return LifecycleProjection("Drafting", "lifecycle-metadata-conflict")
    if authoritative_phase != "Closeout-pending":
        return LifecycleProjection(authoritative_phase)

    if post_closeout_result is not None:
        if post_closeout_result not in POST_CLOSEOUT_RESULTS:
            return LifecycleProjection("Closeout-pending", "post-closeout-result-invalid")
        return LifecycleProjection("Post-closeout")
    if receipt_present:
        return LifecycleProjection("Closeout-pending", "closeout-result-required")
    if outcome not in {"completed", "abandoned", "superseded"}:
        return LifecycleProjection("Closeout-pending", "completion-outcome-required")
    if initiative_residue:
        return LifecycleProjection("Closeout-pending", "initiative-residue")
    if live_dependencies:
        return LifecycleProjection("Closeout-pending", "live-dependency")
    return LifecycleProjection("Closeout-pending")


def classify_disposition(candidate: DispositionCandidate) -> DispositionDecision:
    """Recommend one RFC disposition intent without granting deletion permission."""
    if candidate.lifecycle_outcome not in {"completed", "abandoned", "superseded"}:
        return DispositionDecision(None, "lifecycle-outcome-invalid")
    boolean_facts = (
        candidate.persisted,
        candidate.delivered,
        candidate.pushed,
        candidate.removal_change,
        candidate.removal_integrated,
        candidate.lasting_facts_settled,
        candidate.obligations_settled,
        candidate.live_dependencies,
        candidate.retain_exception,
    )
    if any(not isinstance(value, bool) for value in boolean_facts):
        return DispositionDecision(None, "disposition-facts-invalid")
    if candidate.source_authority is None:
        return DispositionDecision(None, "source-authority-unknown")
    if candidate.source_authority not in _CLASSIFIER_SOURCE_AUTHORITIES:
        return DispositionDecision(None, "source-authority-invalid")
    if (
        candidate.write_authority is not None
        and candidate.write_authority not in _WRITE_AUTHORITIES
    ):
        return DispositionDecision(None, "write-authority-invalid")
    if (
        candidate.deletion_authority is not None
        and candidate.deletion_authority not in _DELETE_AUTHORITIES
    ):
        return DispositionDecision(None, "deletion-authority-invalid")
    if not candidate.lasting_facts_settled:
        return DispositionDecision(None, "lasting-facts-unsettled")
    if (
        candidate.retain_exception
        or not candidate.obligations_settled
        or candidate.live_dependencies
    ):
        if candidate.retain_exception:
            return DispositionDecision("retain-exception")
        return DispositionDecision(None, "obligations-or-dependencies-unsettled")
    if candidate.source_authority == "external-system":
        if candidate.write_authority is not None or candidate.deletion_authority is not None:
            return DispositionDecision(None, "authority-conflict")
        return DispositionDecision("external-advisory")
    if candidate.write_authority is None and not candidate.delivered:
        return DispositionDecision(None, "write-authority-unknown")
    if candidate.deletion_authority is None:
        return DispositionDecision("external-advisory")
    if candidate.write_authority is None:
        return DispositionDecision(None, "write-authority-unknown")
    if not candidate.persisted and candidate.source_authority == "tool-session":
        return DispositionDecision("discard-local")
    if not candidate.persisted:
        return DispositionDecision(None, "authority-conflict")
    if candidate.source_authority == "tool-session":
        return DispositionDecision(None, "authority-conflict")
    if candidate.delivered and not candidate.pushed:
        return DispositionDecision(None, "source-state-conflict")
    if not candidate.delivered and not candidate.pushed:
        return DispositionDecision("delete-before-push")
    if candidate.removal_change and not candidate.removal_integrated:
        return DispositionDecision("delete-before-merge")
    if (
        candidate.lifecycle_outcome == "completed"
        and candidate.delivered
        and candidate.pushed
    ):
        return DispositionDecision("cool-30-days")
    return DispositionDecision(None, "disposition-ineligible")


def assess_durable_output(
    *,
    applicable: bool,
    destination: str | None,
    freshness: str,
    finding_status: str,
) -> Assessment:
    """Report whether one applicable semantic owner is current and settled."""
    if not applicable:
        return Assessment("not-applicable")
    if not destination:
        return Assessment("blocked", "destination-unresolved")
    if freshness != "confirmed":
        return Assessment("blocked", "semantic-freshness-unconfirmed")
    if finding_status not in {"incorporated", "none"}:
        return Assessment("blocked", "implementation-finding-unsettled")
    return Assessment("settled")


def classify_lld_fact(
    *, kind: str, inferable_from_code: bool, owner: str | None
) -> Assessment:
    """Classify one design fact for extraction before container disposition."""
    if inferable_from_code and kind == "internal-shape":
        return Assessment("implementation-evidence")
    if kind == "task-order":
        return Assessment("delivery-residue")
    if owner:
        return Assessment("persist")
    return Assessment("blocked", "durable-owner-unresolved")


def validate_workspace_capture(
    *, summary: str, commentary: Sequence[str], needs: Sequence[str]
) -> Assessment:
    """Reject the mechanically detectable shapes of working history.

    This seam enforces exactly four things: a non-empty summary, a length bound,
    an empty `commentary`, and a well-formed `needs` list. It also rejects a
    small closed list of procedural fragments, which catches the common phrasings
    and nothing more — it is a tripwire, not a classifier.

    Judging whether prose is genuinely terse present-state coordination stays
    with the skill's eval set and the human reviewing the entry. A caller must
    not read an `accepted` result as a semantic guarantee.
    """
    if not isinstance(summary, str) or not summary.strip():
        return Assessment("rejected", "summary-required")
    if len(summary) > MAX_SUMMARY_LENGTH:
        return Assessment("rejected", "summary-too-long")
    if commentary:
        return Assessment("rejected", "commentary-forbidden")
    lowered = summary.casefold()
    procedural = (
        "run tests",
        "update docs",
        "ask reviewers",
        "then merge",
        "suggested order",
        "first we",
    )
    if any(fragment in lowered for fragment in procedural):
        return Assessment("rejected", "procedure-or-history-forbidden")
    if (
        isinstance(needs, (str, bytes))
        or not isinstance(needs, Sequence)
        or len(needs) > MAX_EVIDENCE_REFS
    ):
        return Assessment("rejected", "hard-dependencies-invalid")
    dependency_re = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$")
    if any(
        not isinstance(need, str) or dependency_re.fullmatch(need) is None
        for need in needs
    ):
        return Assessment("rejected", "hard-dependencies-invalid")
    return Assessment("accepted")


def _preflight_enumeration_limits(repository_root: Path, directory: Path) -> None:
    """Bound work before invoking the canonical recursive enumeration helper."""
    helper = file_safety()
    helper.validate_confined_directory(repository_root, directory)
    pending = [directory]
    entry_count = 0
    file_count = 0
    total_bytes = 0
    reparse_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    while pending:
        current = pending.pop()
        helper.validate_confined_directory(repository_root, current)
        with os.scandir(current) as entries:
            for entry in entries:
                entry_count += 1
                if entry_count > MAX_ENUMERATION_ENTRIES:
                    raise ValueError("enumeration entry limit exceeded")
                inspected = entry.stat(follow_symlinks=False)
                is_reparse = bool(
                    getattr(inspected, "st_file_attributes", 0)
                    & reparse_attribute
                )
                if stat.S_ISLNK(inspected.st_mode) or is_reparse:
                    raise ValueError("link-like enumeration entry")
                if stat.S_ISDIR(inspected.st_mode):
                    pending.append(Path(entry.path))
                    continue
                if not stat.S_ISREG(inspected.st_mode):
                    raise ValueError("non-regular enumeration entry")
                file_count += 1
                total_bytes += inspected.st_size
                if file_count > MAX_TARGETS:
                    raise ValueError("target limit exceeded")
                if inspected.st_size > MAX_FILE_BYTES:
                    raise ValueError("per-file byte limit exceeded")
                if total_bytes > MAX_TOTAL_BYTES:
                    raise ValueError("aggregate byte limit exceeded")


def _confined_target_set(
    repository_root: Path,
    enumeration_root: Path,
    targets: Sequence[Path],
    *,
    exact_file: bool,
) -> tuple[tuple[Path, ...], tuple[TargetFingerprint, ...], str]:
    helper = file_safety()
    if exact_file:
        if len(targets) != 1:
            raise ValueError("exact-file mode requires one target")
        helper.validate_confined_directory(repository_root, enumeration_root)
        inspected = targets[0].lstat()
        if (
            not stat.S_ISREG(inspected.st_mode)
            or inspected.st_nlink > 1
            or inspected.st_size > MAX_FILE_BYTES
        ):
            raise ValueError("exact-file target is unsafe or oversized")
        enumerated = tuple(targets)
    else:
        _preflight_enumeration_limits(repository_root, enumeration_root)
        enumerated = tuple(
            sorted(
                # Both bounds are passed, so the traversal that materialises
                # the list is bounded the same way the preflight walk was.
                # `max_files` alone left a directory-only tree unbounded: the
                # preflight measured a separate, earlier walk, so a concurrent
                # local writer under `enumeration_root` could grow the tree in
                # between and have it traversed in full.
                helper.list_confined_regular_files(
                    repository_root,
                    enumeration_root,
                    max_files=MAX_TARGETS,
                    max_entries=MAX_ENUMERATION_ENTRIES,
                ),
                key=lambda path: path.relative_to(repository_root).as_posix(),
            )
        )
    if not enumerated or len(enumerated) > MAX_TARGETS:
        raise ValueError("enumerated target set is empty or exceeds the target limit")
    normalized = tuple(
        sorted(targets, key=lambda path: path.relative_to(repository_root).as_posix())
    )
    if normalized != enumerated:
        raise ValueError("explicit targets do not match the confined enumeration")
    fingerprints: list[TargetFingerprint] = []
    total_bytes = 0
    for target in normalized:
        before = target.lstat()
        data = helper.read_confined_regular_file(
            repository_root, target, max_bytes=MAX_FILE_BYTES
        )
        after = target.lstat()
        if (before.st_dev, before.st_ino, before.st_size) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
        ):
            raise ValueError("target changed while fingerprinting")
        total_bytes += after.st_size
        if total_bytes > MAX_TOTAL_BYTES:
            raise ValueError("target byte limit exceeded")
        digest = hashlib.sha256(data).hexdigest()
        fingerprints.append(
            TargetFingerprint(
                relative_path=target.relative_to(repository_root).as_posix(),
                sha256=digest,
                device=after.st_dev,
                inode=after.st_ino,
                size=after.st_size,
            )
        )
    material = json.dumps(
        [dataclasses.asdict(item) for item in fingerprints],
        sort_keys=True,
        separators=(",", ":"),
    )
    aggregate = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return normalized, tuple(fingerprints), aggregate


def _preview_binding(payload: Mapping[str, object]) -> str:
    material = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def secure_effect_supported() -> bool:
    """Report whether this runtime can perform the required no-follow dir-fd effect."""
    return (
        hasattr(os, "O_NOFOLLOW")
        and hasattr(os, "O_NONBLOCK")
        and _DIR_FD_EFFECT_SUPPORTED
        and _NOFOLLOW_STAT_SUPPORTED
        and _NOFOLLOW_LINK_SUPPORTED
    )


def _disposition_fingerprint(
    candidate: DispositionCandidate, decision: DispositionDecision
) -> str:
    return _preview_binding(
        {
            "candidate": dataclasses.asdict(candidate),
            "decision": dataclasses.asdict(decision),
        }
    )


def _resolved_surface(
    *,
    repository_root: Path,
    role: str,
    logical_locator: str,
    expected_physical_locator: str,
    candidates: Sequence[object],
    source_authority: str,
    write_authority: str,
    deletion_authority: str,
    authority_evidence_refs: Mapping[str, str],
) -> tuple[Any, str]:
    """Resolve and validate one repository-owned deletion surface."""
    resolver = surface_resolver()
    result = resolver.resolve_surface(repository_root, role, candidates)
    physical = getattr(result, "physical_locator", None)
    authority = getattr(result, "authority", None)
    facts = (
        getattr(authority, "source", None),
        getattr(authority, "write", None),
        getattr(authority, "delete", None),
    )
    expected_refs = tuple(authority_evidence_refs[key] for key in ("source", "write", "delete"))
    expected_statuses = (
        "repository-owned" if source_authority == "repository-origin" else "delegated",
        "delegated" if write_authority in _WRITE_AUTHORITIES else "none",
        "delegated" if deletion_authority in _DELETE_AUTHORITIES else "none",
    )
    if (
        result.status != "resolved"
        or result.role != role
        or result.confinement != "repository-confined"
        or result.availability != "available"
        or result.writability != "writable"
        or result.logical_locator != logical_locator
        or physical is None
        or physical.kind != "repository-path"
        or physical.value != expected_physical_locator
        or result.revision_or_fingerprint is None
        or any(fact is None for fact in facts)
        or tuple(fact.status for fact in facts) != expected_statuses
        or tuple(fact.evidence_ref for fact in facts) != expected_refs
        or any(item.status == "required" for item in result.confirmations)
    ):
        raise ValueError("surface resolution is not deletion-eligible")
    payload = result.as_dict()
    return result, _preview_binding(payload)


def _open_validated_parent(repository_root: Path, directory: Path) -> int:
    """Walk from the repository root without following any directory component."""
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    relative = directory.relative_to(repository_root)
    descriptor = os.open(repository_root, flags)
    try:
        opened_root = os.fstat(descriptor)
        current_root = repository_root.stat(follow_symlinks=False)
        if (
            not stat.S_ISDIR(opened_root.st_mode)
            or not stat.S_ISDIR(current_root.st_mode)
            or (opened_root.st_dev, opened_root.st_ino)
            != (current_root.st_dev, current_root.st_ino)
        ):
            raise ValueError("repository root identity changed")
        for component in relative.parts:
            if component in {"", ".", ".."}:
                raise ValueError("directory component is unsafe")
            child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        opened = os.fstat(descriptor)
        current = directory.stat(follow_symlinks=False)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or not stat.S_ISDIR(current.st_mode)
            or (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino)
        ):
            raise ValueError("directory identity changed")
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


open_validated_parent = _open_validated_parent
load_regular_sibling = _load_regular_sibling


def _directory_path_matches_fd(directory: Path, descriptor: int) -> bool:
    try:
        opened = os.fstat(descriptor)
        current = directory.stat(follow_symlinks=False)
    except OSError:
        return False
    return stat.S_ISDIR(current.st_mode) and (opened.st_dev, opened.st_ino) == (
        current.st_dev,
        current.st_ino,
    )


def _fingerprint_descriptor(
    file_descriptor: int, relative_path: str
) -> tuple[TargetFingerprint, int]:
    """Hash one already-open file and return its stable link count."""
    before = os.fstat(file_descriptor)
    if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_FILE_BYTES:
        raise ValueError("target is not a bounded regular file")
    digest = hashlib.sha256()
    total = 0
    while True:
        chunk = os.read(file_descriptor, 1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_FILE_BYTES:
            raise ValueError("target exceeds byte limit")
        digest.update(chunk)
    after = os.fstat(file_descriptor)
    if (before.st_dev, before.st_ino, before.st_size, before.st_nlink) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_nlink,
    ):
        raise ValueError("target changed while fingerprinting")
    return (
        TargetFingerprint(
            relative_path=relative_path,
            sha256=digest.hexdigest(),
            device=after.st_dev,
            inode=after.st_ino,
            size=after.st_size,
        ),
        after.st_nlink,
    )


def _inspect_fingerprint_at(
    descriptor: int, name: str, relative_path: str
) -> tuple[TargetFingerprint, int]:
    """Open no-follow beneath a validated parent and inspect identity and links."""
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    file_descriptor = os.open(name, flags, dir_fd=descriptor)
    try:
        return _fingerprint_descriptor(file_descriptor, relative_path)
    finally:
        os.close(file_descriptor)


def _fingerprint_at(
    descriptor: int,
    name: str,
    relative_path: str,
    *,
    expected_links: int = 1,
) -> TargetFingerprint:
    """Hash a bounded regular file through an already validated parent handle."""
    fingerprint, link_count = _inspect_fingerprint_at(
        descriptor, name, relative_path
    )
    if link_count != expected_links:
        raise ValueError("target has an unexpected hard-link count")
    return fingerprint


def preview_deletion(
    *,
    repository_root: Path,
    surface_role: str,
    surface_candidates: Sequence[object],
    logical_locator: str,
    targets: Sequence[Path],
    disposition: str,
    disposition_candidate: DispositionCandidate,
    completion_evidence_ref: str,
    durable_output_evidence_refs: Sequence[str],
    pushed: bool,
    removal_integrated: bool,
    source_state_evidence_ref: str,
    source_authority: str,
    source_authority_evidence_ref: str,
    write_authority: str,
    write_authority_evidence_ref: str,
    deletion_authority: str,
    deletion_authority_evidence_ref: str,
    authorized_actor_role: str,
    proposer_role: str,
    proposer_evidence_ref: str,
    grant_source: str,
    action: str,
    host_session_provenance: str,
    authority_fact: object,
    enumeration_root: Path | None = None,
) -> DeletionPreview | DeletionResult:
    """Resolve, classify, inventory, and fingerprint one file without permission."""
    try:
        locator = _bounded_text("logical_locator", logical_locator)
        completion_ref = _bounded_text(
            "completion_evidence_ref", completion_evidence_ref
        )
        output_refs = _bounded_refs(
            "durable_output_evidence_refs", durable_output_evidence_refs
        )
        source_ref = _bounded_text(
            "source_state_evidence_ref", source_state_evidence_ref
        )
        source = _bounded_text("source_authority", source_authority)
        source_authority_ref = _bounded_text(
            "source_authority_evidence_ref", source_authority_evidence_ref
        )
        write = _bounded_text("write_authority", write_authority)
        write_authority_ref = _bounded_text(
            "write_authority_evidence_ref", write_authority_evidence_ref
        )
        delete = _bounded_text("deletion_authority", deletion_authority)
        deletion_authority_ref = _bounded_text(
            "deletion_authority_evidence_ref", deletion_authority_evidence_ref
        )
        actor = _bounded_text("authorized_actor_role", authorized_actor_role)
        proposer = _bounded_text("proposer_role", proposer_role)
        proposer_ref = _bounded_text(
            "proposer_evidence_ref", proposer_evidence_ref
        )
        grant = _bounded_text("grant_source", grant_source)
        requested_action = _bounded_text("action", action)
        provenance = _bounded_text(
            "host_session_provenance", host_session_provenance
        )
    except ValueError:
        return DeletionResult("authority-or-evidence-invalid")
    authority_binding = _mutation_binding(
        authority_fact=authority_fact,
        authorized_actor_role=actor,
        grant_source=grant,
        action=requested_action,
        resource=locator,
        evidence_ref=deletion_authority_ref,
        host_session_provenance=provenance,
        expected_action="delete-confirmed-file-set",
    )
    if authority_binding is None:
        return DeletionResult("authority-unavailable")
    assert isinstance(authority_fact, ResolvedAuthorityFact)
    if surface_role != "delivery-contract":
        return DeletionResult("surface-role-invalid")
    if (
        isinstance(surface_candidates, (str, bytes))
        or not isinstance(surface_candidates, Sequence)
        or not surface_candidates
    ):
        return DeletionResult("surface-resolution-refused")
    if disposition not in IMMEDIATE_DISPOSITIONS:
        return DeletionResult("disposition-not-immediate")
    if not isinstance(disposition_candidate, DispositionCandidate):
        return DeletionResult("disposition-eligibility-invalid")
    decision = classify_disposition(disposition_candidate)
    if decision.blocker is not None or decision.disposition != disposition:
        return DeletionResult("disposition-ineligible")
    if (
        disposition_candidate.pushed != pushed
        or disposition_candidate.removal_integrated != removal_integrated
        or disposition_candidate.source_authority != source
        or disposition_candidate.write_authority != write
        or disposition_candidate.deletion_authority != delete
    ):
        return DeletionResult("disposition-facts-conflict")
    eligibility_fingerprint = _disposition_fingerprint(
        disposition_candidate, decision
    )
    # Subsumed today: `_mutation_binding` above is called with
    # expected_action="delete-confirmed-file-set" and returns None on a
    # mismatch, which becomes `authority-unavailable`. Retained as
    # defence in depth so relaxing that guard cannot silently open this path.
    if requested_action != "delete-confirmed-file-set":
        return DeletionResult("action-not-authorized")
    if (
        source not in _SOURCE_AUTHORITIES
        or write not in _WRITE_AUTHORITIES
        or delete not in _DELETE_AUTHORITIES
    ):
        return DeletionResult("authority-conflict")
    # `actor` is already refused by `_mutation_binding` against the same regex;
    # `proposer` is checked nowhere else, so it is the reachable half.
    if not _ACTOR_ROLE_RE.fullmatch(proposer):
        return DeletionResult("proposer-role-invalid")
    # Both subsumed today by `_mutation_binding`'s prefix checks on the same two
    # values; retained as defence in depth against a future relaxation there.
    if not grant.startswith(_GRANT_PREFIXES):
        return DeletionResult("grant-not-authoritative")
    if not provenance.startswith(_PROVENANCE_PREFIXES):
        return DeletionResult("session-provenance-invalid")
    if not isinstance(pushed, bool) or not isinstance(removal_integrated, bool):
        return DeletionResult("source-state-invalid")
    if disposition == "discard-local" and (
        source != "tool-session"
        or write != "tool-session"
        or delete != "tool-owned"
        # These last two are subsumed today: `classify_disposition` only yields
        # `discard-local` for an unpushed, unintegrated candidate, and the
        # facts-conflict guard above already refuses a candidate whose facts
        # differ from these scalars. Retained as defence in depth.
        or pushed
        or removal_integrated
    ):
        return DeletionResult("source-state-ineligible")
    if disposition in {"delete-before-push", "delete-before-merge"} and (
        source != "repository-origin" or delete != "repository-owned"
    ):
        return DeletionResult("authority-conflict")
    if disposition == "delete-before-push" and pushed:
        return DeletionResult("source-state-ineligible")
    if disposition == "delete-before-merge" and (
        not pushed or removal_integrated
    ):
        return DeletionResult("source-state-ineligible")
    if not secure_effect_supported():
        return DeletionResult("secure-effect-unsupported")
    try:
        root_input = Path(repository_root)
        if root_input.is_symlink():
            raise ValueError("repository root is link-like")
        root = root_input.resolve(strict=True)
        if not root.is_dir():
            raise ValueError("repository root is not a directory")
        if isinstance(targets, (str, bytes)) or not targets:
            raise ValueError("targets are required")
        normalized_targets: list[Path] = []
        for raw_target in targets:
            target = Path(raw_target)
            if not target.is_absolute():
                target = root / target
            target.relative_to(root)
            if target not in normalized_targets:
                normalized_targets.append(target)
        if len(normalized_targets) != 1:
            return DeletionResult("one-file-confirmation-required")
        if enumeration_root is None:
            if len(normalized_targets) != 1:
                raise ValueError("explicit enumeration root required for file sets")
            boundary = normalized_targets[0].parent
            enumeration_mode = "exact-file"
        else:
            boundary = Path(enumeration_root)
            if not boundary.is_absolute():
                boundary = root / boundary
            enumeration_mode = "explicit-set"
        expected_physical = (
            normalized_targets[0].relative_to(root).as_posix()
            if enumeration_mode == "exact-file"
            else boundary.relative_to(root).as_posix()
        )
    except (OSError, RuntimeError, ValueError, ImportError):
        return DeletionResult("unsafe-target")
    try:
        resolution, resolution_fingerprint = _resolved_surface(
            repository_root=root,
            role=surface_role,
            logical_locator=locator,
            expected_physical_locator=expected_physical,
            candidates=surface_candidates,
            source_authority=source,
            write_authority=write,
            deletion_authority=delete,
            authority_evidence_refs={
                "source": source_authority_ref,
                "write": write_authority_ref,
                "delete": deletion_authority_ref,
            },
        )
    except (OSError, RuntimeError, ValueError, ImportError):
        return DeletionResult("surface-resolution-refused")
    resolved_physical = root / resolution.physical_locator.value
    if enumeration_mode == "exact-file":
        if normalized_targets != [resolved_physical]:
            return DeletionResult("surface-resolution-refused")
        boundary = resolved_physical.parent
        resolved_targets: tuple[Path, ...] = (resolved_physical,)
    else:
        if boundary != resolved_physical:
            return DeletionResult("surface-resolution-refused")
        resolved_targets = tuple(normalized_targets)
    try:
        exact_targets, fingerprints, aggregate = _confined_target_set(
            root,
            boundary,
            resolved_targets,
            exact_file=enumeration_mode == "exact-file",
        )
    except (OSError, RuntimeError, ValueError, ImportError):
        return DeletionResult("unsafe-target")
    confirmation_challenge = secrets.token_hex(32)
    binding_payload: dict[str, object] = {
        "repository_root": str(root),
        "enumeration_root": str(boundary),
        "enumeration_mode": enumeration_mode,
        "surface_role": surface_role,
        "logical_locator": locator,
        "physical_locator": expected_physical,
        "revision_or_fingerprint": resolution.revision_or_fingerprint,
        "surface_resolution_fingerprint": resolution_fingerprint,
        "resource_file_set": tuple(
            target.relative_to(root).as_posix() for target in exact_targets
        ),
        "target_fingerprints": tuple(
            dataclasses.asdict(item) for item in fingerprints
        ),
        "target_fingerprint": aggregate,
        "disposition": disposition,
        "disposition_eligibility_fingerprint": eligibility_fingerprint,
        "completion_evidence_ref": completion_ref,
        "durable_output_evidence_refs": output_refs,
        "pushed": pushed,
        "removal_integrated": removal_integrated,
        "source_state_evidence_ref": source_ref,
        "source_authority": source,
        "source_authority_evidence_ref": source_authority_ref,
        "write_authority": write,
        "write_authority_evidence_ref": write_authority_ref,
        "deletion_authority": delete,
        "deletion_authority_evidence_ref": deletion_authority_ref,
        "authorized_actor_role": actor,
        "proposer_role": proposer,
        "proposer_evidence_ref": proposer_ref,
        "grant_source": grant,
        "action": requested_action,
        "host_session_provenance": provenance,
        "authority_resource": authority_binding.resource,
        "authority_resolution_evidence_ref": authority_fact.authority_evidence_ref,
        "authority_issue_digest": authority_fact.issue_digest,
        "confirmation_challenge": confirmation_challenge,
    }
    preview = DeletionPreview(
        code="confirmation-required",
        repository_root=root,
        enumeration_root=boundary,
        enumeration_mode=enumeration_mode,
        surface_role=surface_role,
        logical_locator=locator,
        physical_locator=expected_physical,
        revision_or_fingerprint=resolution.revision_or_fingerprint,
        surface_resolution_fingerprint=resolution_fingerprint,
        surface_candidates=tuple(surface_candidates),
        targets=exact_targets,
        target_fingerprints=fingerprints,
        target_fingerprint=aggregate,
        disposition=disposition,
        disposition_candidate=disposition_candidate,
        disposition_eligibility_fingerprint=eligibility_fingerprint,
        completion_evidence_ref=completion_ref,
        durable_output_evidence_refs=output_refs,
        pushed=pushed,
        removal_integrated=removal_integrated,
        source_state_evidence_ref=source_ref,
        source_authority=source,
        source_authority_evidence_ref=source_authority_ref,
        write_authority=write,
        write_authority_evidence_ref=write_authority_ref,
        deletion_authority=delete,
        deletion_authority_evidence_ref=deletion_authority_ref,
        authorized_actor_role=actor,
        proposer_role=proposer,
        proposer_evidence_ref=proposer_ref,
        grant_source=grant,
        action=requested_action,
        host_session_provenance=provenance,
        authority_resource=authority_binding.resource,
        authority_resolution_evidence_ref=authority_fact.authority_evidence_ref,
        authority_issue_digest=authority_fact.issue_digest,
        confirmation_challenge=confirmation_challenge,
        binding_digest=_preview_binding(binding_payload),
    )
    _ISSUED_COORDINATION_AUTHORITIES.pop(authority_fact.issue_digest, None)
    _ISSUED_PREVIEWS[preview.binding_digest] = preview
    return preview


def _human_confirmation_matches(
    preview: DeletionPreview, supplied: HumanConfirmation
) -> bool:
    expected: dict[str, object] = {
        "confirmation_challenge": preview.confirmation_challenge,
        "enumeration_mode": preview.enumeration_mode,
        "surface_role": preview.surface_role,
        "logical_locator": preview.logical_locator,
        "physical_locator": preview.physical_locator,
        "revision_or_fingerprint": preview.revision_or_fingerprint,
        "surface_resolution_fingerprint": preview.surface_resolution_fingerprint,
        "resource_file_set": tuple(
            target.relative_to(preview.repository_root).as_posix()
            for target in preview.targets
        ),
        "target_fingerprints": preview.target_fingerprints,
        "target_fingerprint": preview.target_fingerprint,
        "disposition": preview.disposition,
        "disposition_eligibility_fingerprint": (
            preview.disposition_eligibility_fingerprint
        ),
        "completion_evidence_ref": preview.completion_evidence_ref,
        "durable_output_evidence_refs": preview.durable_output_evidence_refs,
        "pushed": preview.pushed,
        "removal_integrated": preview.removal_integrated,
        "source_state_evidence_ref": preview.source_state_evidence_ref,
        "source_authority": preview.source_authority,
        "source_authority_evidence_ref": preview.source_authority_evidence_ref,
        "write_authority": preview.write_authority,
        "write_authority_evidence_ref": preview.write_authority_evidence_ref,
        "deletion_authority": preview.deletion_authority,
        "deletion_authority_evidence_ref": preview.deletion_authority_evidence_ref,
        "authorized_actor_role": preview.authorized_actor_role,
        "proposer_role": preview.proposer_role,
        "proposer_evidence_ref": preview.proposer_evidence_ref,
        "grant_source": preview.grant_source,
        "action": preview.action,
        "host_session_provenance": preview.host_session_provenance,
        "authority_resource": preview.authority_resource,
        "authority_resolution_evidence_ref": (
            preview.authority_resolution_evidence_ref
        ),
        "authority_issue_digest": preview.authority_issue_digest,
        "proposed_mutation": "ordinary-file-removal",
    }
    return all(getattr(supplied, key) == value for key, value in expected.items())


def confirm_deletion(
    preview: DeletionPreview, *, human_confirmation: HumanConfirmation
) -> DeletionConfirmation:
    """Validate a human-supplied exact restatement; never fabricate approval."""
    if not isinstance(preview, DeletionPreview) or not isinstance(
        human_confirmation, HumanConfirmation
    ):
        raise ValueError("preview and structured human confirmation are required")
    if preview.binding_digest in _CONFIRMED_PREVIEWS:
        raise ValueError("confirmation was already issued for preview")
    issued_preview = _ISSUED_PREVIEWS.get(preview.binding_digest)
    if (
        issued_preview is not preview
        or len(preview.targets) != 1
        or len(preview.target_fingerprints) != 1
    ):
        raise ValueError("preview was not issued for exactly one file")
    identifier = _bounded_text(
        "confirmation_id", human_confirmation.confirmation_id
    )
    evidence_ref = _bounded_text(
        "human_evidence_ref", human_confirmation.human_evidence_ref
    )
    approver = _bounded_text("approver_role", human_confirmation.approver_role)
    approver_ref = _bounded_text(
        "approver_evidence_ref", human_confirmation.approver_evidence_ref
    )
    if not _ACTOR_ROLE_RE.fullmatch(approver):
        raise ValueError("approver role is invalid")
    if approver == preview.proposer_role:
        raise ValueError("human approver must differ from proposer")
    if approver != preview.authorized_actor_role:
        raise ValueError("human approver is not the authorized actor")
    if not _human_confirmation_matches(preview, human_confirmation):
        raise ValueError("human confirmation does not exactly match preview")
    proof_digest = _preview_binding(
        {
            "binding_digest": preview.binding_digest,
            "human_evidence_ref": evidence_ref,
            "proposer_role": preview.proposer_role,
            "proposer_evidence_ref": preview.proposer_evidence_ref,
            "approver_role": approver,
            "approver_evidence_ref": approver_ref,
        }
    )
    if proof_digest in _ISSUED_HUMAN_PROOFS:
        raise ValueError("human confirmation proof was already issued")
    issue_digest = _preview_binding(
        {"proof_digest": proof_digest, "confirmation_id": identifier}
    )
    payload = {
        field.name: getattr(human_confirmation, field.name)
        for field in dataclasses.fields(HumanConfirmation)
    }
    payload["confirmation_id"] = identifier
    payload["human_evidence_ref"] = evidence_ref
    confirmation = DeletionConfirmation(
        binding_digest=preview.binding_digest,
        issue_digest=issue_digest,
        **payload,
    )
    _ISSUED_HUMAN_PROOFS.add(proof_digest)
    _ISSUED_PREVIEWS.pop(preview.binding_digest, None)
    _CONFIRMED_PREVIEWS.add(preview.binding_digest)
    _ISSUED_CONFIRMATIONS[issue_digest] = confirmation
    return confirmation


def decline_deletion(preview: DeletionPreview) -> DeletionResult:
    """Record a declined recommendation without performing any effect."""
    if isinstance(preview, DeletionPreview):
        issued = _ISSUED_PREVIEWS.get(preview.binding_digest)
        if issued is preview:
            _ISSUED_PREVIEWS.pop(preview.binding_digest, None)
    return DeletionResult("confirmation-declined")


def _confirmation_matches(
    preview: DeletionPreview, confirmation: DeletionConfirmation
) -> bool:
    fields = (
        "binding_digest",
        "confirmation_challenge",
        "enumeration_mode",
        "surface_role",
        "logical_locator",
        "physical_locator",
        "revision_or_fingerprint",
        "surface_resolution_fingerprint",
        "target_fingerprints",
        "target_fingerprint",
        "disposition",
        "disposition_eligibility_fingerprint",
        "completion_evidence_ref",
        "durable_output_evidence_refs",
        "pushed",
        "removal_integrated",
        "source_state_evidence_ref",
        "source_authority",
        "source_authority_evidence_ref",
        "write_authority",
        "write_authority_evidence_ref",
        "deletion_authority",
        "deletion_authority_evidence_ref",
        "authorized_actor_role",
        "proposer_role",
        "proposer_evidence_ref",
        "grant_source",
        "action",
        "host_session_provenance",
        "authority_resource",
        "authority_resolution_evidence_ref",
        "authority_issue_digest",
    )
    if confirmation.resource_file_set != tuple(
        target.relative_to(preview.repository_root).as_posix()
        for target in preview.targets
    ):
        return False
    if confirmation.proposed_mutation != "ordinary-file-removal":
        return False
    return all(getattr(preview, field) == getattr(confirmation, field) for field in fields)


def apply_confirmed_deletion(
    *,
    repository_root: Path,
    preview: DeletionPreview,
    confirmation: DeletionConfirmation,
    current_surface_candidates: Sequence[object] | None = None,
    current_disposition_candidate: DispositionCandidate | None = None,
    current_source_state: Mapping[str, bool] | None = None,
    source_state_evidence_ref: str | None = None,
    current_authority_fact: object = None,
) -> DeletionResult:
    """Revalidate every bound fact immediately before one ordinary file deletion."""
    if not isinstance(preview, DeletionPreview) or not isinstance(
        confirmation, DeletionConfirmation
    ):
        return DeletionResult("confirmation-mismatch")
    if confirmation.issue_digest in _CONSUMED_CONFIRMATIONS:
        return DeletionResult("confirmation-reused")
    if not secure_effect_supported():
        return DeletionResult("secure-effect-unsupported")
    # A type-valid approval is terminal on its first application attempt. Drift,
    # mismatch, or missing current evidence never leaves an approval reusable.
    issued = _ISSUED_CONFIRMATIONS.pop(confirmation.issue_digest, None)
    _CONSUMED_CONFIRMATIONS.add(confirmation.issue_digest)
    _CONFIRMED_PREVIEWS.discard(preview.binding_digest)
    if issued is None or issued != confirmation:
        return DeletionResult("confirmation-not-issued")
    if not _confirmation_matches(preview, confirmation):
        return DeletionResult("confirmation-mismatch")
    if (
        len(preview.targets) != 1
        or len(preview.target_fingerprints) != 1
        or len(confirmation.resource_file_set) != 1
    ):
        return DeletionResult("one-file-confirmation-required")
    try:
        root_input = Path(repository_root)
        if root_input.is_symlink():
            raise ValueError("repository root is link-like")
        current_root = root_input.resolve(strict=True)
        if not current_root.is_dir():
            raise ValueError("repository root is not a directory")
    except (OSError, RuntimeError, ValueError):
        return DeletionResult("confirmation-expired")
    if current_root != preview.repository_root:
        return DeletionResult("confirmation-expired")
    if not isinstance(current_authority_fact, ResolvedAuthorityFact):
        return DeletionResult("authority-unavailable")
    current_authority_binding = _mutation_binding(
        authority_fact=current_authority_fact,
        authorized_actor_role=current_authority_fact.authorized_actor_role,
        grant_source=current_authority_fact.grant_source,
        action=current_authority_fact.action,
        resource=current_authority_fact.resource,
        evidence_ref=current_authority_fact.evidence_ref,
        host_session_provenance=current_authority_fact.host_session_provenance,
        expected_action="delete-confirmed-file-set",
    )
    if current_authority_binding is None:
        return DeletionResult("authority-unavailable")
    _ISSUED_COORDINATION_AUTHORITIES.pop(
        current_authority_fact.issue_digest, None
    )
    expected_authority_binding = MutationBinding(
        authorized_actor_role=preview.authorized_actor_role,
        grant_source=preview.grant_source,
        action=preview.action,
        resource=preview.authority_resource,
        evidence_ref=preview.deletion_authority_evidence_ref,
        host_session_provenance=preview.host_session_provenance,
    )
    if (
        current_authority_binding != expected_authority_binding
        or current_authority_fact.issue_digest != preview.authority_issue_digest
        or current_authority_fact.authority_evidence_ref
        != preview.authority_resolution_evidence_ref
    ):
        return DeletionResult("confirmation-expired")
    if not isinstance(current_disposition_candidate, DispositionCandidate):
        return DeletionResult("disposition-evidence-unavailable")
    current_decision = classify_disposition(current_disposition_candidate)
    if (
        current_decision.blocker is not None
        or current_decision.disposition != preview.disposition
        or _disposition_fingerprint(current_disposition_candidate, current_decision)
        != preview.disposition_eligibility_fingerprint
    ):
        return DeletionResult("confirmation-expired")
    if (
        isinstance(current_surface_candidates, (str, bytes))
        or not isinstance(current_surface_candidates, Sequence)
        or not current_surface_candidates
    ):
        return DeletionResult("surface-evidence-unavailable")
    try:
        resolution, resolution_fingerprint = _resolved_surface(
            repository_root=current_root,
            role=preview.surface_role,
            logical_locator=preview.logical_locator,
            expected_physical_locator=preview.physical_locator,
            candidates=current_surface_candidates,
            source_authority=preview.source_authority,
            write_authority=preview.write_authority,
            deletion_authority=preview.deletion_authority,
            authority_evidence_refs={
                "source": preview.source_authority_evidence_ref,
                "write": preview.write_authority_evidence_ref,
                "delete": preview.deletion_authority_evidence_ref,
            },
        )
    except (OSError, RuntimeError, ValueError, ImportError):
        return DeletionResult("confirmation-expired")
    if (
        resolution_fingerprint != preview.surface_resolution_fingerprint
        or resolution.revision_or_fingerprint != preview.revision_or_fingerprint
    ):
        return DeletionResult("confirmation-expired")
    resolved_physical = current_root / resolution.physical_locator.value
    if preview.enumeration_mode == "exact-file":
        boundary = resolved_physical.parent
        targets_for_read = (resolved_physical,)
    elif preview.enumeration_mode == "explicit-set":
        boundary = resolved_physical
        targets_for_read = preview.targets
    else:
        return DeletionResult("confirmation-expired")
    if preview.enumeration_root != boundary or preview.targets != targets_for_read:
        return DeletionResult("confirmation-expired")
    if not isinstance(current_source_state, Mapping) or source_state_evidence_ref is None:
        return DeletionResult("source-state-unavailable")
    try:
        current_source_ref = _bounded_text(
            "source_state_evidence_ref", source_state_evidence_ref
        )
    except ValueError:
        return DeletionResult("source-state-unavailable")
    if current_source_ref != preview.source_state_evidence_ref:
        return DeletionResult("confirmation-expired")
    current_pushed = current_source_state.get("pushed")
    current_integrated = current_source_state.get("removal_integrated")
    if not isinstance(current_pushed, bool) or not isinstance(current_integrated, bool):
        return DeletionResult("source-state-unavailable")
    if (
        current_pushed != preview.pushed
        or current_integrated != preview.removal_integrated
    ):
        return DeletionResult("confirmation-expired")
    try:
        targets, fingerprints, aggregate = _confined_target_set(
            current_root,
            boundary,
            targets_for_read,
            exact_file=preview.enumeration_mode == "exact-file",
        )
    except (OSError, RuntimeError, ValueError, ImportError):
        return DeletionResult("confirmation-expired")
    if fingerprints != preview.target_fingerprints or aggregate != preview.target_fingerprint:
        return DeletionResult("confirmation-expired")
    if len(targets) != 1 or len(fingerprints) != 1:
        return DeletionResult("one-file-confirmation-required")

    target = targets[0]
    fingerprint = fingerprints[0]
    staging_name = f".close-work-{preview.binding_digest[:24]}.pending"
    descriptor: int | None = None
    staged = False
    original_removed = False
    staging_path = target.with_name(staging_name)

    def residual_evidence(
        observed: TargetFingerprint, link_count: int
    ) -> ResidualHardlinkEvidence:
        return ResidualHardlinkEvidence(
            confirmed_fingerprint=fingerprint,
            observed_link_count=link_count,
            observed_device=observed.device,
            observed_inode=observed.inode,
            observed_size=observed.size,
        )

    def rollback_staged_link() -> DeletionResult | None:
        nonlocal staged, original_removed
        # Subsumed: unreachable as written. Every call site is downstream of the
        # `descriptor` assignment, whose failure returns before staging, and the
        # outermost caller is itself guarded on `descriptor is not None`. Kept
        # as a total function rather than an assert so a future call site added
        # ahead of that assignment degrades to a refusal rather than a crash.
        if descriptor is None:
            return DeletionResult(
                "rollback-failed",
                (target,) if original_removed else (),
                original_removed,
                (staging_path,),
                residue_state="unverified",
            )
        try:
            staged_fingerprint, link_count = _inspect_fingerprint_at(
                descriptor, staging_name, fingerprint.relative_path
            )
        except (OSError, RuntimeError, ValueError):
            return DeletionResult(
                "rollback-failed",
                (target,) if original_removed else (),
                original_removed,
                (staging_path,),
                residue_state="unverified",
            )
        if staged_fingerprint != fingerprint:
            # The descriptor proved the residue is not the confirmed inode, so
            # restoring it would restore unknown content.
            return DeletionResult(
                "rollback-failed",
                (target,) if original_removed else (),
                original_removed,
                (staging_path,),
                residual_evidence(staged_fingerprint, link_count),
                residue_state="identity-mismatch",
            )
        expected_links = 1 if original_removed else 2
        if link_count != expected_links:
            if original_removed and link_count > expected_links:
                return DeletionResult(
                    "residual-hardlink",
                    (target,),
                    True,
                    (staging_path,),
                    residual_evidence(staged_fingerprint, link_count),
                    residue_state="identity-confirmed",
                )
            if not original_removed and link_count > expected_links:
                try:
                    os.unlink(staging_name, dir_fd=descriptor)
                except OSError:
                    return DeletionResult(
                        "rollback-failed",
                        (),
                        False,
                        (staging_path,),
                        residual_evidence(staged_fingerprint, link_count),
                        residue_state="identity-confirmed",
                    )
                staged = False
                return DeletionResult("confirmation-expired")
            return DeletionResult(
                "rollback-failed",
                (target,) if original_removed else (),
                original_removed,
                (staging_path,),
                residual_evidence(staged_fingerprint, link_count),
                residue_state="identity-confirmed",
            )
        try:
            if original_removed:
                os.link(
                    staging_name,
                    target.name,
                    src_dir_fd=descriptor,
                    dst_dir_fd=descriptor,
                    follow_symlinks=False,
                )
                original_removed = False
            os.unlink(staging_name, dir_fd=descriptor)
            staged = False
        except OSError:
            # `staging_path` is a path built once from `target.parent`. One
            # trigger for reaching rollback is a *proven* parent-directory
            # substitution, and in that case this path no longer names the
            # directory the descriptor holds open, so reporting it would aim
            # maintainer recovery at content of unknown origin — under the very
            # `identity-confirmed` label that the guide says is safe to restore.
            # The inode evidence stays: it identifies the residue without
            # depending on the path resolving anywhere.
            parent_still_matches = _directory_path_matches_fd(
                target.parent, descriptor
            )
            return DeletionResult(
                "rollback-failed",
                (target,) if original_removed else (),
                original_removed,
                (staging_path,) if parent_still_matches else (),
                residual_evidence(staged_fingerprint, link_count),
                residue_state="identity-confirmed",
            )
        return None

    try:
        try:
            descriptor = _open_validated_parent(current_root, target.parent)
            current = _fingerprint_at(
                descriptor,
                target.name,
                target.relative_to(current_root).as_posix(),
            )
        except (OSError, RuntimeError, ValueError):
            return DeletionResult("confirmation-expired")
        if current != fingerprint or not _directory_path_matches_fd(
            target.parent, descriptor
        ):
            return DeletionResult("confirmation-expired")
        try:
            os.link(
                target.name,
                staging_name,
                src_dir_fd=descriptor,
                dst_dir_fd=descriptor,
                follow_symlinks=False,
            )
        except FileExistsError:
            return DeletionResult("unsafe-target")
        staged = True
        staged_fingerprint = _fingerprint_at(
            descriptor,
            staging_name,
            fingerprint.relative_path,
            expected_links=2,
        )
        current_after_link = _fingerprint_at(
            descriptor,
            target.name,
            fingerprint.relative_path,
            expected_links=2,
        )
        if (
            staged_fingerprint != fingerprint
            or current_after_link != fingerprint
            or not _directory_path_matches_fd(target.parent, descriptor)
        ):
            rollback_result = rollback_staged_link()
            return rollback_result or DeletionResult("confirmation-expired")
        os.unlink(target.name, dir_fd=descriptor)
        original_removed = True
        verification_flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        verification_descriptor = os.open(
            staging_name, verification_flags, dir_fd=descriptor
        )
        try:
            staged_fingerprint, _before_final_links = _fingerprint_descriptor(
                verification_descriptor, fingerprint.relative_path
            )
            if staged_fingerprint != fingerprint or not _directory_path_matches_fd(
                target.parent, descriptor
            ):
                rollback_result = rollback_staged_link()
                # `rollback_staged_link` returns None only after it relinked the
                # original and unlinked the staging path, i.e. restoration
                # succeeded. That is reachable here through the parent-path half
                # of the condition above, which the helper does not re-test. So
                # report no effect, exactly as the sibling seam does; claiming
                # `rollback-failed` with a staging path that was just unlinked
                # would aim maintainer recovery at a path that does not exist,
                # and under a substituted parent it could resolve to foreign
                # content.
                return rollback_result or DeletionResult("confirmation-expired")
            try:
                os.unlink(staging_name, dir_fd=descriptor)
            except OSError:
                rollback_result = rollback_staged_link()
                return rollback_result or DeletionResult("effect-failed")
            after_final_unlink = os.fstat(verification_descriptor)
        finally:
            os.close(verification_descriptor)
        staged = False
        original_removed = False
        if after_final_unlink.st_nlink != 0:
            observed = TargetFingerprint(
                relative_path=staged_fingerprint.relative_path,
                sha256=staged_fingerprint.sha256,
                device=after_final_unlink.st_dev,
                inode=after_final_unlink.st_ino,
                size=after_final_unlink.st_size,
            )
            return DeletionResult(
                "residual-hardlink",
                (target,),
                True,
                residual_evidence=residual_evidence(
                    observed, after_final_unlink.st_nlink
                ),
                residue_state="identity-confirmed",
            )
        return DeletionResult("deleted", (target,), True)
    except (OSError, RuntimeError, ValueError):
        if staged and descriptor is not None:
            rollback_result = rollback_staged_link()
            if rollback_result is not None:
                return rollback_result
        return DeletionResult("effect-failed")
    finally:
        if descriptor is not None:
            os.close(descriptor)


def wave4_capabilities() -> dict[str, bool]:
    """Expose the explicit later-wave boundary for contract tests and reports."""
    return {
        "timed_retirement": False,
        "migration_or_pruning": False,
        "workspace_context_exclusion": False,
        "history_rewrite": False,
        "second_resolver": False,
    }
