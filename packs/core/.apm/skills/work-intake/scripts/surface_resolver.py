"""Deterministic, read-only resolution of portable semantic surfaces.

Callers acquire a bounded set of candidate records from explicit input,
repository policy, established conventions, optional configuration adapters,
or established external destinations.  This module validates and ranks those
records; it never scans a repository, performs network access, or mutates a
destination.
"""

from __future__ import annotations

import dataclasses
import json
import re
from collections.abc import Sequence
from pathlib import Path

CONTRACT_VERSION = "semantic-surface-resolution.v1"
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
EVIDENCE_SOURCES = (
    "explicit",
    "repository-policy",
    "repository-convention",
    "external-destination",
    "configuration-adapter",
)
EVIDENCE_STRENGTHS = (
    "explicit",
    "mandatory-policy",
    "enforced",
    "confirmed",
    "inferred",
)
AUTHORITY_STATUSES = (
    "repository-owned",
    "external-owned",
    "delegated",
    "none",
    "unknown",
)
CONFIRMATION_KINDS = (
    "destination-selection",
    "convention-establishment",
    "policy-exception",
    "authority",
)
CONFIRMATION_STATUSES = ("required", "confirmed", "not-required")
NEXT_ACTIONS = (
    "confirm-established-repository-convention",
    "confirm-one-policy-permitted-destination",
    "reconcile-mandatory-repository-policy",
    "reduce-candidates-to-32-or-fewer",
    "reduce-confirmations-to-eight-or-fewer",
    "repair-authority-facts",
    "repair-candidate-evidence",
    "repair-candidate-facts",
    "repair-candidate-role-and-shape",
    "repair-confirmation-evidence",
    "repair-external-locator",
    "repair-logical-locator",
    "repair-physical-locator",
    "repair-revision-or-fingerprint",
    "select-confined-repository-path",
    "select-or-create-destination",
    "select-policy-permitted-destination",
    "supply-closed-candidates",
    "supply-existing-repository-root",
    "supply-one-to-four-evidence-records",
)

_SOURCE_RANK = {
    "explicit": 0,
    "repository-policy": 1,
    "configuration-adapter": 1,
    "repository-convention": 2,
    "external-destination": 3,
}
_EXTERNAL_LOCATOR_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:.+$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_RESULT_CODE_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


@dataclasses.dataclass(frozen=True)
class Evidence:
    """One bounded, safe provenance record for a candidate or decision."""

    source: str
    ref: str
    strength: str

    def as_dict(self) -> dict[str, str]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class Locator:
    """A tagged repository-relative or external physical locator."""

    kind: str
    value: str

    def as_dict(self) -> dict[str, str]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class AuthorityFact:
    """One authority dimension, independent from capability and ownership peers."""

    status: str = "unknown"
    evidence_ref: str | None = None

    def as_dict(self) -> dict[str, str]:
        payload = {"status": self.status}
        if self.evidence_ref is not None:
            payload["evidence_ref"] = self.evidence_ref
        return payload


@dataclasses.dataclass(frozen=True)
class Authority:
    """Independent source, write, and deletion authority facts."""

    source: AuthorityFact = dataclasses.field(default_factory=AuthorityFact)
    write: AuthorityFact = dataclasses.field(default_factory=AuthorityFact)
    delete: AuthorityFact = dataclasses.field(default_factory=AuthorityFact)

    def as_dict(self) -> dict[str, dict[str, str]]:
        return {
            "source": self.source.as_dict(),
            "write": self.write.as_dict(),
            "delete": self.delete.as_dict(),
        }


@dataclasses.dataclass(frozen=True)
class Confirmation:
    """One required, completed, or unnecessary human confirmation."""

    kind: str
    status: str
    evidence_ref: str | None = None

    def as_dict(self) -> dict[str, str]:
        payload = {"kind": self.kind, "status": self.status}
        if self.evidence_ref is not None:
            payload["evidence_ref"] = self.evidence_ref
        return payload


@dataclasses.dataclass(frozen=True)
class SurfaceCandidate:
    """Closed candidate record acquired outside this resolver."""

    role: str
    logical_locator: str
    physical_locator: Locator
    provenance: tuple[Evidence, ...]
    availability: str = "unknown"
    writability: str = "unknown"
    authority: Authority = dataclasses.field(default_factory=Authority)
    revision_or_fingerprint: str | None = None
    confirmations: tuple[Confirmation, ...] = ()
    policy_permitted: bool = True


@dataclasses.dataclass(frozen=True)
class SurfaceResolution:
    """Schema-aligned terminal result from one resolution attempt."""

    status: str
    role: str
    provenance: tuple[Evidence, ...]
    availability: str
    writability: str
    confinement: str
    authority: Authority
    confirmations: tuple[Confirmation, ...]
    logical_locator: str | None = None
    physical_locator: Locator | None = None
    revision_or_fingerprint: str | None = None
    code: str | None = None
    next_action: str | None = None
    contract_version: str = CONTRACT_VERSION

    def as_dict(self) -> dict[str, object]:
        """Return the closed JSON contract without absent optional fields."""
        payload: dict[str, object] = {
            "contract_version": self.contract_version,
            "status": self.status,
            "role": self.role,
            "provenance": [item.as_dict() for item in self.provenance],
            "availability": self.availability,
            "writability": self.writability,
            "confinement": self.confinement,
            "authority": self.authority.as_dict(),
            "confirmations": [item.as_dict() for item in self.confirmations],
        }
        if self.logical_locator is not None:
            payload["logical_locator"] = self.logical_locator
        if self.physical_locator is not None:
            payload["physical_locator"] = self.physical_locator.as_dict()
        if self.revision_or_fingerprint is not None:
            payload["revision_or_fingerprint"] = self.revision_or_fingerprint
        if self.code is not None:
            payload["code"] = self.code
        if self.next_action is not None:
            payload["next_action"] = self.next_action
        return payload


_DECISION_EVIDENCE: Evidence = Evidence(
    "explicit", "request:semantic-surface", "explicit"
)
_UNKNOWN_AUTHORITY = Authority()


@dataclasses.dataclass(frozen=True)
class _PreparedCandidate:
    candidate: SurfaceCandidate
    physical_locator: Locator
    identity: tuple[str, str, str]
    rank: int
    availability: str


def resolve_surface(
    repository_root: Path,
    role: str,
    candidates: Sequence[SurfaceCandidate],
) -> SurfaceResolution:
    """Resolve a role from caller-supplied candidates without discovery or writes."""
    if role not in SURFACE_ROLES:
        raise ValueError("unknown semantic surface role")
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Sequence):
        return _failure(role, "refused", "invalid_candidates", "supply-closed-candidates")
    if len(candidates) > 32:
        return _failure(
            role,
            "refused",
            "candidate_limit_exceeded",
            "reduce-candidates-to-32-or-fewer",
        )
    if not candidates:
        return _failure(
            role,
            "destination-required",
            "destination_absent",
            "select-or-create-destination",
        )

    prepared: list[_PreparedCandidate] = []
    for candidate in candidates:
        try:
            prepared.append(_prepare_candidate(repository_root, role, candidate))
        except _CandidateRefusal as refusal:
            return _failure(
                role,
                "refused",
                refusal.code,
                refusal.next_action,
                _safe_provenance(candidate),
            )

    mandatory = [
        item
        for item in prepared
        if any(evidence.strength == "mandatory-policy" for evidence in item.candidate.provenance)
    ]
    mandatory_identities = {item.identity for item in mandatory}
    if len(mandatory_identities) > 1:
        return _failure(
            role,
            "refused",
            "mandatory_policy_conflict",
            "reconcile-mandatory-repository-policy",
            _combined_provenance(mandatory),
        )

    explicit = [item for item in prepared if item.rank == 0]
    if any(not item.candidate.policy_permitted for item in explicit):
        return _failure(
            role,
            "refused",
            "mandatory_policy_violation",
            "select-policy-permitted-destination",
            _combined_provenance(explicit),
        )
    if mandatory_identities and any(
        item.identity not in mandatory_identities for item in explicit
    ):
        return _failure(
            role,
            "refused",
            "mandatory_policy_violation",
            "select-policy-permitted-destination",
            _combined_provenance([*explicit, *mandatory]),
        )

    permitted = [item for item in prepared if item.candidate.policy_permitted]
    if mandatory_identities:
        permitted = [item for item in permitted if item.identity in mandatory_identities]
    if not permitted:
        return _failure(
            role,
            "destination-required",
            "destination_absent",
            "select-or-create-destination",
            _combined_provenance(prepared),
        )

    best_rank = min(item.rank for item in permitted)
    peers = [item for item in permitted if item.rank == best_rank]
    by_identity: dict[tuple[str, str, str], list[_PreparedCandidate]] = {}
    for item in peers:
        by_identity.setdefault(item.identity, []).append(item)
    if len(by_identity) > 1:
        return _failure(
            role,
            "confirmation-required",
            "ambiguous_candidates",
            "confirm-one-policy-permitted-destination",
            _combined_provenance(peers),
            (Confirmation("destination-selection", "required"),),
        )

    winning_identity, best_equivalents = next(iter(by_identity.items()))
    best_selected = _merge_equivalent_candidates(best_equivalents)
    if _requires_convention_confirmation(best_selected):
        confirmations = _merge_confirmations(
            best_selected.candidate.confirmations,
            (Confirmation("convention-establishment", "required"),),
        )
        return _failure(
            role,
            "confirmation-required",
            "convention_confirmation_required",
            "confirm-established-repository-convention",
            tuple(best_selected.candidate.provenance),
            confirmations,
        )

    equivalents = [item for item in permitted if item.identity == winning_identity]
    selected = _merge_equivalent_candidates(equivalents)

    return SurfaceResolution(
        status="resolved",
        role=role,
        logical_locator=selected.candidate.logical_locator,
        physical_locator=selected.physical_locator,
        provenance=selected.candidate.provenance,
        availability=selected.availability,
        writability=selected.candidate.writability,
        confinement=(
            "repository-confined"
            if selected.physical_locator.kind == "repository-path"
            else "external"
        ),
        authority=selected.candidate.authority,
        revision_or_fingerprint=selected.candidate.revision_or_fingerprint,
        confirmations=selected.candidate.confirmations,
    )


def render_safe_result(result: SurfaceResolution) -> str:
    """Render only validated contract fields in deterministic JSON."""
    if not isinstance(result, SurfaceResolution):
        raise TypeError("result must be a SurfaceResolution")
    _validate_resolution_for_render(result)
    return json.dumps(
        result.as_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _validate_resolution_for_render(result: SurfaceResolution) -> None:
    """Refuse manually constructed results that bypass resolver validation."""
    try:
        if (
            result.contract_version != CONTRACT_VERSION
            or result.status
            not in {"resolved", "confirmation-required", "destination-required", "refused"}
            or result.role not in SURFACE_ROLES
            or not 1 <= len(result.provenance) <= 4
            or result.availability not in {"available", "unavailable", "unknown"}
            or result.writability not in {"writable", "read-only", "unknown"}
            or result.confinement not in {"repository-confined", "external", "unknown"}
            or len(result.confirmations) > 8
        ):
            raise ValueError
        for evidence in result.provenance:
            _validate_evidence(evidence)
        _validate_authority(result.authority)
        for confirmation in result.confirmations:
            _validate_confirmation(confirmation)
        if result.revision_or_fingerprint is not None and not _is_safe_revision(
            result.revision_or_fingerprint
        ):
            raise ValueError

        if result.status == "resolved":
            if (
                result.logical_locator is None
                or result.physical_locator is None
                or result.code is not None
                or result.next_action is not None
            ):
                raise ValueError
            _validate_logical_locator(result.logical_locator)
            if result.physical_locator.kind == "repository-path":
                _validate_repository_path(result.physical_locator.value)
                if result.confinement != "repository-confined":
                    raise ValueError
            elif result.physical_locator.kind == "external":
                _validate_external_locator(result.physical_locator.value)
                if result.confinement != "external":
                    raise ValueError
            else:
                raise ValueError
            return

        if (
            result.logical_locator is not None
            or result.physical_locator is not None
            or result.revision_or_fingerprint is not None
            or result.availability != "unknown"
            or result.writability != "unknown"
            or result.confinement != "unknown"
            or result.authority != _UNKNOWN_AUTHORITY
            or result.code is None
            or _RESULT_CODE_RE.fullmatch(result.code) is None
            or result.next_action is None
            or result.next_action not in NEXT_ACTIONS
            or (
                result.status == "confirmation-required"
                and not any(item.status == "required" for item in result.confirmations)
            )
        ):
            raise ValueError
    except (_CandidateRefusal, TypeError, ValueError):
        raise ValueError("result does not match resolution contract") from None


class _CandidateRefusal(ValueError):
    """Internal stable-code refusal; exception text never reaches a result."""

    def __init__(self, code: str, next_action: str) -> None:
        super().__init__(code)
        self.code = code
        self.next_action = next_action


def _prepare_candidate(
    repository_root: Path,
    role: str,
    candidate: SurfaceCandidate,
) -> _PreparedCandidate:
    if not isinstance(candidate, SurfaceCandidate) or candidate.role != role:
        raise _CandidateRefusal("invalid_candidate", "repair-candidate-role-and-shape")
    if not isinstance(candidate.policy_permitted, bool):
        raise _CandidateRefusal("invalid_candidate", "repair-candidate-role-and-shape")
    if not 1 <= len(candidate.provenance) <= 4:
        raise _CandidateRefusal("evidence_limit_exceeded", "supply-one-to-four-evidence-records")
    for evidence in candidate.provenance:
        _validate_evidence(evidence)
    _validate_logical_locator(candidate.logical_locator)
    _validate_authority(candidate.authority)
    if candidate.availability not in {"available", "unavailable", "unknown"}:
        raise _CandidateRefusal("invalid_candidate", "repair-candidate-facts")
    if candidate.writability not in {"writable", "read-only", "unknown"}:
        raise _CandidateRefusal("invalid_candidate", "repair-candidate-facts")
    if candidate.revision_or_fingerprint is not None and not _is_safe_revision(
        candidate.revision_or_fingerprint
    ):
        raise _CandidateRefusal("invalid_candidate", "repair-revision-or-fingerprint")
    if len(candidate.confirmations) > 8:
        raise _CandidateRefusal("invalid_candidate", "reduce-confirmations-to-eight-or-fewer")
    for confirmation in candidate.confirmations:
        _validate_confirmation(confirmation)

    locator = candidate.physical_locator
    if not isinstance(locator, Locator):
        raise _CandidateRefusal("invalid_locator", "repair-physical-locator")
    if locator.kind == "external":
        _validate_external_locator(locator.value)
        prepared_locator = locator
        availability = candidate.availability
    elif locator.kind == "repository-path":
        prepared_locator, availability = _resolve_repository_locator(
            repository_root, locator.value
        )
    else:
        raise _CandidateRefusal("invalid_locator", "repair-physical-locator")

    rank = min(_SOURCE_RANK[evidence.source] for evidence in candidate.provenance)
    return _PreparedCandidate(
        candidate,
        prepared_locator,
        (role, prepared_locator.kind, prepared_locator.value),
        rank,
        availability,
    )


def _validate_evidence(evidence: Evidence) -> None:
    if (
        not isinstance(evidence, Evidence)
        or evidence.source not in EVIDENCE_SOURCES
        or evidence.strength not in EVIDENCE_STRENGTHS
        or not _is_safe_ref(evidence.ref)
    ):
        raise _CandidateRefusal("invalid_evidence", "repair-candidate-evidence")


def _validate_authority(authority: Authority) -> None:
    if not isinstance(authority, Authority):
        raise _CandidateRefusal("invalid_authority", "repair-authority-facts")
    for fact in (authority.source, authority.write, authority.delete):
        if not isinstance(fact, AuthorityFact) or fact.status not in AUTHORITY_STATUSES:
            raise _CandidateRefusal("invalid_authority", "repair-authority-facts")
        if fact.evidence_ref is not None and not _is_safe_ref(fact.evidence_ref):
            raise _CandidateRefusal("invalid_authority", "repair-authority-facts")


def _validate_confirmation(confirmation: Confirmation) -> None:
    if (
        not isinstance(confirmation, Confirmation)
        or confirmation.kind not in CONFIRMATION_KINDS
        or confirmation.status not in CONFIRMATION_STATUSES
        or (
            confirmation.evidence_ref is not None
            and not _is_safe_ref(confirmation.evidence_ref)
        )
    ):
        raise _CandidateRefusal("invalid_confirmation", "repair-confirmation-evidence")


def _validate_logical_locator(value: object) -> None:
    if not _is_safe_ref(value):
        raise _CandidateRefusal("invalid_locator", "repair-logical-locator")


def _validate_external_locator(value: object) -> None:
    if (
        not isinstance(value, str)
        or not 3 <= len(value) <= 1000
        or not _EXTERNAL_LOCATOR_RE.fullmatch(value)
        or not _is_safe_ref(value)
    ):
        raise _CandidateRefusal("invalid_external_locator", "repair-external-locator")


def _resolve_repository_locator(
    repository_root: Path, value: object
) -> tuple[Locator, str]:
    if not isinstance(repository_root, Path):
        raise _CandidateRefusal("unsafe_repository_root", "supply-existing-repository-root")
    _validate_repository_path(value)
    try:
        resolved_root = repository_root.resolve(strict=True)
        if not resolved_root.is_dir():
            raise ValueError("repository root is not a directory")
        _validate_existing_symlink_chain(resolved_root, value)
        resolved_candidate = (resolved_root / value).resolve(strict=False)
        relative = resolved_candidate.relative_to(resolved_root).as_posix()
        if relative in {"", "."}:
            raise ValueError("candidate resolves to repository root")
        _validate_repository_path(relative)
        availability = "available" if resolved_candidate.exists() else "unavailable"
    except (OSError, RuntimeError, ValueError):
        raise _CandidateRefusal(
            "unsafe_repository_path", "select-confined-repository-path"
        ) from None
    return Locator("repository-path", relative), availability


def _validate_existing_symlink_chain(resolved_root: Path, value: str) -> None:
    """Reject looping, broken, or escaping symlinks in an existing path prefix."""
    probe = resolved_root
    for part in value.split("/"):
        probe = probe / part
        if not probe.is_symlink():
            continue
        resolved_link = probe.resolve(strict=True)
        resolved_link.relative_to(resolved_root)


def _validate_repository_path(value: object) -> None:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 1000
        or value.startswith("/")
        or _WINDOWS_DRIVE_RE.match(value)
        or "\\" in value
        or _has_control(value)
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise _CandidateRefusal("unsafe_repository_path", "select-confined-repository-path")


def _requires_convention_confirmation(item: _PreparedCandidate) -> bool:
    inferred_convention = any(
        evidence.source in {"repository-convention", "configuration-adapter"}
        and evidence.strength == "inferred"
        for evidence in item.candidate.provenance
    )
    confirmed = any(
        confirmation.kind == "convention-establishment"
        and confirmation.status == "confirmed"
        for confirmation in item.candidate.confirmations
    )
    return inferred_convention and not confirmed


def _merge_equivalent_candidates(
    items: Sequence[_PreparedCandidate],
) -> _PreparedCandidate:
    ordered = sorted(items, key=_prepared_sort_key)
    first = ordered[0]
    provenance = _combined_provenance(ordered)
    confirmations = _merge_confirmations(
        *(item.candidate.confirmations for item in ordered)
    )
    candidate = dataclasses.replace(
        first.candidate,
        physical_locator=first.physical_locator,
        provenance=provenance,
        authority=_merge_authority(tuple(item.candidate.authority for item in ordered)),
        confirmations=confirmations,
        availability=_merge_fact(tuple(item.availability for item in ordered), "unknown"),
        writability=_merge_fact(
            tuple(item.candidate.writability for item in ordered), "unknown"
        ),
        revision_or_fingerprint=_merge_optional_text(
            tuple(item.candidate.revision_or_fingerprint for item in ordered)
        ),
    )
    return dataclasses.replace(
        first,
        candidate=candidate,
        availability=candidate.availability,
    )


def _merge_authority(authorities: tuple[Authority, ...]) -> Authority:
    return Authority(
        source=_merge_authority_fact(tuple(item.source for item in authorities)),
        write=_merge_authority_fact(tuple(item.write for item in authorities)),
        delete=_merge_authority_fact(tuple(item.delete for item in authorities)),
    )


def _merge_authority_fact(facts: tuple[AuthorityFact, ...]) -> AuthorityFact:
    known = [fact for fact in facts if fact.status != "unknown"]
    if not known:
        return AuthorityFact()
    statuses = {fact.status for fact in known}
    if len(statuses) != 1:
        return AuthorityFact()
    refs = sorted({fact.evidence_ref for fact in known if fact.evidence_ref is not None})
    return AuthorityFact(known[0].status, refs[0] if len(refs) == 1 else None)


def _merge_fact(values: tuple[str, ...], unknown: str) -> str:
    known = {value for value in values if value != unknown}
    return next(iter(known)) if len(known) == 1 else unknown


def _merge_optional_text(values: tuple[str | None, ...]) -> str | None:
    known = {value for value in values if value is not None}
    return next(iter(known)) if len(known) == 1 else None


def _combined_provenance(
    items: Sequence[_PreparedCandidate],
) -> tuple[Evidence, ...]:
    evidence = {
        (record.source, record.ref, record.strength): record
        for item in items
        for record in item.candidate.provenance
        if _evidence_is_valid(record)
    }
    ordered = sorted(
        evidence.values(),
        key=lambda record: (
            _SOURCE_RANK[record.source],
            record.source,
            record.ref,
            record.strength,
        ),
    )
    return tuple(ordered[:4]) or (_DECISION_EVIDENCE,)


def _merge_confirmations(
    *groups: Sequence[Confirmation],
) -> tuple[Confirmation, ...]:
    confirmations = {
        (item.kind, item.status, item.evidence_ref): item
        for group in groups
        for item in group
    }
    return tuple(
        sorted(
            confirmations.values(),
            key=lambda item: (item.kind, item.status, item.evidence_ref or ""),
        )[:8]
    )


def _failure(
    role: str,
    status: str,
    code: str,
    next_action: str,
    provenance: tuple[Evidence, ...] = (),
    confirmations: tuple[Confirmation, ...] = (),
) -> SurfaceResolution:
    safe_provenance = tuple(item for item in provenance if _evidence_is_valid(item))[:4]
    if not safe_provenance:
        safe_provenance = (_DECISION_EVIDENCE,)
    if status == "confirmation-required" and not any(
        item.status == "required" for item in confirmations
    ):
        confirmations = _merge_confirmations(
            confirmations, (Confirmation("destination-selection", "required"),)
        )
    return SurfaceResolution(
        status=status,
        role=role,
        provenance=safe_provenance,
        availability="unknown",
        writability="unknown",
        confinement="unknown",
        authority=_UNKNOWN_AUTHORITY,
        confirmations=confirmations,
        code=code,
        next_action=next_action,
    )


def _safe_provenance(candidate: object) -> tuple[Evidence, ...]:
    if not isinstance(candidate, SurfaceCandidate):
        return ()
    return tuple(item for item in candidate.provenance if _evidence_is_valid(item))[:4]


def _evidence_is_valid(evidence: object) -> bool:
    return (
        isinstance(evidence, Evidence)
        and evidence.source in EVIDENCE_SOURCES
        and evidence.strength in EVIDENCE_STRENGTHS
        and _is_safe_ref(evidence.ref)
    )


def _prepared_sort_key(item: _PreparedCandidate) -> tuple[object, ...]:
    return (
        item.rank,
        item.identity,
        item.candidate.logical_locator,
        tuple(
            (record.source, record.ref, record.strength)
            for record in item.candidate.provenance
        ),
    )


def _is_safe_ref(value: object) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 1000
        and not any(character.isspace() for character in value)
        and not any(character in "@?#" for character in value)
        and not _has_control(value)
    )


def _is_safe_bounded_text(value: object, limit: int) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= limit
        and not _has_control(value)
    )


def _is_safe_revision(value: object) -> bool:
    """Accept an opaque revision token without credential or instruction channels."""
    return isinstance(value, str) and len(value) <= 300 and _is_safe_ref(value)


def _has_control(value: str) -> bool:
    return any(ord(character) <= 31 or ord(character) == 127 for character in value)
