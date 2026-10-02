"""_subject_projection — runtime-neutral delivery-subject projector.

Pure component (T6).  Takes a product manifest (canonical sorted path-hash pairs)
and metadata and produces a ``delivery-subject.v1`` record whose acceptance
fingerprint is deterministic over product paths and hashes, spec identity,
evidence policy, exclusions, and lineage.

Task-projection revision and hash are execution provenance only.  They are stored
in the optional fields of the record but are excluded from the acceptance
fingerprint computation so task-only changes never alter it (spec §4 invariant).

Parity rule (verification-ledger.md §Script-versus-schema parity): every task
that adds a module building delivery records carries parity tests.  This module
satisfies that obligation for T6 by exporting ``validate_subject_dict()`` which
the roster suite and pack tests use to verify refusal of schema-invalid inputs.

Standard library only.  No third-party imports, no packaging, no installation.
Python 3.11+.
"""

from __future__ import annotations

import hashlib
import json
import sys
from typing import Final

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = [
    "SUPPORTED_SUBJECT_SCHEMA_VERSION",
    "DENIAL_CODES",
    "SubjectProjectionRefused",
    "compute_acceptance_fingerprint",
    "project_delivery_subject",
    "validate_subject_dict",
]

SUPPORTED_SUBJECT_SCHEMA_VERSION: Final[int] = 1

# Stable denial codes — callers may match against these strings.
DENIAL_CODES: Final[frozenset[str]] = frozenset({
    "denied-not-a-dict",
    "denied-unknown-schema-version",
    "denied-missing-required-field",
    "denied-unknown-authority-field",
    "denied-invalid-enum",
})

# Required top-level fields (additionalProperties: false per the schema).
_REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "schema_version",
    "subject_id",
    "acceptance_fingerprint",
    "product",
    "spec",
    "evidence_policy_ref",
    "exclusions",
    "lineage",
)

# Optional execution-provenance fields excluded from the acceptance fingerprint.
_OPTIONAL_FIELDS: Final[frozenset[str]] = frozenset({
    "task_projection_revision",
    "task_projection_hash",
})

_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(_REQUIRED_FIELDS) | _OPTIONAL_FIELDS


class SubjectProjectionRefused(Exception):
    """A subject-projection operation was refused with a stable denial code.

    ``denial_code`` is one of the strings in ``DENIAL_CODES`` and carries no
    sensitive payload bytes, excerpts, or content-derived hashes.
    """

    def __init__(self, denial_code: str, message: str = "") -> None:
        super().__init__(message or denial_code)
        self.denial_code: str = denial_code


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _fingerprint(data: dict) -> str:
    """SHA-256 fingerprint of *data* serialised with sorted keys (ASCII-safe).

    ``sort_keys=True`` ensures deterministic output regardless of insertion order.
    ``ensure_ascii=True`` prevents locale-specific encoding differences.
    """
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_acceptance_fingerprint(
    *,
    manifest_pairs: tuple[tuple[str, str], ...],
    spec_path: str,
    spec_fingerprint: str,
    evidence_policy_ref: str,
    exclusions: tuple[str, ...],
    provider: str,
    projection_version: str,
) -> str:
    """Compute the acceptance fingerprint for a delivery subject.

    Deterministic over: sorted manifest pairs (path, sha256), spec path and
    fingerprint, evidence policy reference, sorted exclusions, and lineage
    (provider identity and projection version).

    Task-projection revision and hash are intentionally excluded: a task-only
    change must never alter the acceptance fingerprint.

    Returns the SHA-256 hex digest of the canonical serialisation.
    """
    data = {
        "exclusions": sorted(exclusions),
        "lineage": {"projection_version": projection_version, "provider": provider},
        "manifest": sorted(manifest_pairs),
        "spec": {"fingerprint": spec_fingerprint, "path": spec_path},
        "evidence_policy_ref": evidence_policy_ref,
    }
    return _fingerprint(data)


def project_delivery_subject(
    *,
    subject_id: str,
    base_ref: str,
    result_ref: str,
    spec_path: str,
    spec_fingerprint: str,
    evidence_policy_ref: str,
    exclusions: tuple[str, ...],
    provider: str,
    projection_version: str,
    manifest_pairs: tuple[tuple[str, str], ...],
    task_projection_revision: str | None = None,
    task_projection_hash: str | None = None,
) -> dict:
    """Produce a ``delivery-subject.v1`` record from a canonical product manifest.

    The acceptance fingerprint is deterministic over product, spec, evidence
    policy, exclusions, and lineage.  It never includes task-projection
    provenance.  Identical inputs always produce the same record on every
    conforming adapter (spec AC-0005 / AC-0007 determinism invariant).
    """
    sorted_exclusions = sorted(exclusions)
    fp = compute_acceptance_fingerprint(
        manifest_pairs=manifest_pairs,
        spec_path=spec_path,
        spec_fingerprint=spec_fingerprint,
        evidence_policy_ref=evidence_policy_ref,
        exclusions=tuple(sorted_exclusions),
        provider=provider,
        projection_version=projection_version,
    )
    record: dict = {
        "schema_version": SUPPORTED_SUBJECT_SCHEMA_VERSION,
        "subject_id": subject_id,
        "acceptance_fingerprint": fp,
        "product": {
            "base_ref": base_ref,
            "result_ref": result_ref,
        },
        "spec": {
            "path": spec_path,
            "fingerprint": spec_fingerprint,
        },
        "evidence_policy_ref": evidence_policy_ref,
        "exclusions": sorted_exclusions,
        "lineage": {
            "provider": provider,
            "projection_version": projection_version,
        },
    }
    if task_projection_revision is not None:
        record["task_projection_revision"] = task_projection_revision
    if task_projection_hash is not None:
        record["task_projection_hash"] = task_projection_hash
    return record


def validate_subject_dict(record: object) -> tuple[bool, str]:
    """Validate *record* against the ``delivery-subject.v1`` contract in code.

    Checks schema_version first (unknown major refused before field checks),
    then required fields, then unknown authority-shaped fields, then nested
    object shapes.

    Returns ``(True, "ok")`` on success or ``(False, denial_code)`` on any
    failure.  Failure codes are stable across versions.
    """
    if not isinstance(record, dict):
        return False, "denied-not-a-dict"
    sv = record.get("schema_version")
    if sv != SUPPORTED_SUBJECT_SCHEMA_VERSION:
        return False, "denied-unknown-schema-version"
    for field in _REQUIRED_FIELDS:
        if field not in record:
            return False, "denied-missing-required-field"
    unknown = set(record) - _ALLOWED_FIELDS
    if unknown:
        return False, "denied-unknown-authority-field"
    # Validate nested product object
    product = record.get("product")
    if not isinstance(product, dict):
        return False, "denied-missing-required-field"
    for sub in ("base_ref", "result_ref"):
        if sub not in product:
            return False, "denied-missing-required-field"
    # Validate nested spec object
    spec = record.get("spec")
    if not isinstance(spec, dict):
        return False, "denied-missing-required-field"
    for sub in ("path", "fingerprint"):
        if sub not in spec:
            return False, "denied-missing-required-field"
    # Validate nested lineage object
    lineage = record.get("lineage")
    if not isinstance(lineage, dict):
        return False, "denied-missing-required-field"
    for sub in ("provider", "projection_version"):
        if sub not in lineage:
            return False, "denied-missing-required-field"
    return True, "ok"
