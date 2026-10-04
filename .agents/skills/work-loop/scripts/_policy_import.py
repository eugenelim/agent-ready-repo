"""_policy_import — policy import, reviewed envelope, initial plan review,
change classification, and reverse-read.

Atomic import of the current approved spec-policy decision as one
``approval-record.v1`` plus one ``initial-plan-review.v1`` record, bound to the
derived ``reviewed-execution-envelope.v1`` fingerprint and the authorized terminal
intent. Produces exactly zero or two visible records after any interruption.

Implements:

  Canonicalization — calls the current canonicalizer from ``_loop_guards`` through
             its owning module; never copies normalization code.
  Zero-or-two visibility — import exposes zero or two records; any interruption or
             validation failure before atomic commit leaves zero visible.
  Content-safety — every write boundary applies its named content-safety profile
             before persisting; a missing or unknown profile refuses without payload
             retention.
  Dual-read path — ``reverse_read`` reconstructs the original approved pair;
             ``compatibility_snapshot`` enforces snapshot invariants in the module:
             it calls an injected resolver that answers only whether an accepted
             authority-switch governance decision exists; the module then validates
             the decision's envelope fingerprint and terminal intent against the
             stored records, builds the snapshot itself (no target-authority grant),
             and verifies the store is byte-identical before and after.  The module
             default resolver refuses because no accepted governance record exists.
  Writer authority — verified via ``_security_events`` before any durable write;
             retry under the same denied record identity stays denied.
  Audit sink required — when the audit sink is unavailable the operation fails
             closed; zero records are exposed and no protected data is persisted.

Standard library only. Loads sibling modules by path using the
``importlib.util.spec_from_file_location`` pattern established in
``_confined_mutation.py`` and ``loop-cohort.py``.

Python 3.11+.
"""

from __future__ import annotations

import importlib.util
import os
import secrets
import stat
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Final

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = [
    # Exceptions
    "PolicyImportRefused",
    # Store
    "ImportStore",
    # Public entry points
    "import_policy",
    "reverse_read",
    "compatibility_snapshot",
    # Digest helpers
    "compute_spec_digest",
    "compute_plan_digest",
    # In-code schema validation
    "validate_approval_dict",
    "validate_initial_review_dict",
    # Schema version constants
    "SUPPORTED_APPROVAL_SCHEMA_VERSION",
    "SUPPORTED_INITIAL_REVIEW_SCHEMA_VERSION",
]

# ── Schema version constants ──────────────────────────────────────────────────

SUPPORTED_APPROVAL_SCHEMA_VERSION: Final[int] = 1
SUPPORTED_INITIAL_REVIEW_SCHEMA_VERSION: Final[int] = 1

# ── Scripts directory ─────────────────────────────────────────────────────────

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parent

# ── Exception ─────────────────────────────────────────────────────────────────


class PolicyImportRefused(Exception):
    """A policy-import operation was refused with a stable denial code.

    ``denial_code`` carries a stable string that callers may log without
    sensitive payload bytes. It does not include excerpts or content-derived
    hashes.
    """

    def __init__(self, denial_code: str, message: str = "") -> None:
        super().__init__(message or denial_code)
        self.denial_code: str = denial_code


# ── Sibling module loader ─────────────────────────────────────────────────────
#
# Each sibling is loaded lazily on first use and cached. The loader pattern
# follows _confined_mutation.py and loop-cohort.py:
#   - lstat + S_ISREG on the path before exec_module.
#   - sys.dont_write_bytecode saved and restored to its prior value.
#   - NOT registered in sys.modules (avoids session-global singleton leaks and
#     failed-load cleanup complexity).

_guards_module: ModuleType | None = None
_acceptance_module: ModuleType | None = None
_content_safety_module: ModuleType | None = None
_security_events_module: ModuleType | None = None


def _load_sibling(name: str, filename: str) -> ModuleType:
    """Load a sibling module by path, unregistered."""
    path = _SCRIPTS_DIR / filename
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise ImportError(f"cannot locate {filename}: {exc}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise ImportError(f"{filename} is not a regular file")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"no import spec for {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        return module
    finally:
        sys.dont_write_bytecode = previous


def _guards() -> ModuleType:
    """Lazily load _loop_guards.py."""
    global _guards_module
    if _guards_module is None:
        _guards_module = _load_sibling("_pi_loop_guards", "_loop_guards.py")
    return _guards_module


def _acceptance() -> ModuleType:
    """Lazily load _acceptance.py."""
    global _acceptance_module
    if _acceptance_module is None:
        _acceptance_module = _load_sibling("_pi_acceptance", "_acceptance.py")
    return _acceptance_module


def _content_safety() -> ModuleType:
    """Lazily load _content_safety.py."""
    global _content_safety_module
    if _content_safety_module is None:
        _content_safety_module = _load_sibling("_pi_content_safety", "_content_safety.py")
    return _content_safety_module


def _security_events() -> ModuleType:
    """Lazily load _security_events.py."""
    global _security_events_module
    if _security_events_module is None:
        _security_events_module = _load_sibling("_pi_security_events", "_security_events.py")
    return _security_events_module


# ── Digest helpers ────────────────────────────────────────────────────────────
#
# These call the current canonicalizer from _loop_guards through its owning
# module. They never copy normalization code; the single canonical implementation
# in _loop_guards governs both current and target digests.


def compute_spec_digest(spec_path: Path) -> str:
    """SHA-256 of canonical_contract(spec.md) — calls through _loop_guards.

    Normalizes status token, AC-section checkboxes, line endings (CRLF/CR→LF),
    and trailing whitespace per the canonical_contract algorithm.
    """
    return _guards().sha256_canonical_contract(spec_path)


def compute_plan_digest(plan_path: Path) -> str:
    """SHA-256 of canonical_contract(plan.md) — calls through _loop_guards.

    Normalizes checkboxes file-wide (plans have no AC-section boundary),
    line endings, and trailing whitespace per the canonical_contract algorithm.
    """
    return _guards().sha256_canonical_contract(plan_path)


# ── ImportStore ───────────────────────────────────────────────────────────────
#
# In-memory append store that exposes records only when a two-record atomic
# commit succeeds. Staging allows rollback on any interruption between writes.
# The 0-or-2 invariant is enforced here: commit() is the only path from staged
# to visible, and it requires the staging area to hold exactly two records.


class ImportStore:
    """In-memory store for policy-import records.

    Records become durably visible only when ``commit()`` is called with exactly
    two staged records (spec-policy approval + initial-plan-review). Any
    interruption before that call leaves zero records visible.

    This is an in-memory store for test use and shadow operation.
    File-backed persistence with crash-recovery guarantees is owned by the
    evidence-store module.
    """

    def __init__(self) -> None:
        self._staged: list[dict] = []
        self._visible: list[dict] = []

    def _stage(self, record: dict) -> None:
        """Stage a record for atomic commit. Called by import_policy only."""
        self._staged.append(record)

    def _commit(self) -> None:
        """Atomically move all staged records to visible.

        The commit is all-or-nothing: both staged records become visible together.
        Clears the staging area on success.
        """
        if len(self._staged) != 2:
            raise PolicyImportRefused(
                "denied-incomplete-staging",
                f"commit requires exactly 2 staged records, got {len(self._staged)}",
            )
        self._visible.extend(self._staged)
        self._staged.clear()

    def _rollback(self) -> None:
        """Discard all staged records without persisting them."""
        self._staged.clear()

    def record_count(self) -> int:
        """Return the count of durably visible records."""
        return len(self._visible)

    def get_records(self) -> list[dict]:
        """Return all durably visible records (a defensive copy)."""
        return list(self._visible)


# ── Content-safety helpers ────────────────────────────────────────────────────


def _check_record_safety(
    record: dict,
    record_type: str,
    *,
    record_id: str,
) -> None:
    """Apply the content-safety profile for *record_type* to *record*'s bytes.

    Refuses (raising PolicyImportRefused) without persisting payload bytes if
    the profile is missing, unknown, or the record does not pass the check.

    Every write boundary applies its named content-safety profile before persisting.
    """
    cs = _content_safety()
    profile = cs.SLICE_1_WRITER_BOUNDARIES.get(record_type)
    if profile is None:
        raise PolicyImportRefused(
            "denied-missing-profile",
            f"no content-safety profile registered for {record_type!r}",
        )
    import json as _json
    payload = _json.dumps(record, sort_keys=True, ensure_ascii=True).encode("utf-8")
    decision = cs.check_content_safety(
        profile,
        payload,
        source_record_id=record_id,
        classification="repository-internal",
    )
    if not decision.accepted:
        raise PolicyImportRefused(
            f"denied-content-safety-{decision.decision_code}",
            f"content-safety check failed for {record_type!r}: {decision.decision_code}",
        )


# ── Authority check helper ────────────────────────────────────────────────────


def _check_writer_authority(
    issuer: object,
    grant: object,
    *,
    audit_sink: Callable[[Any], None],
    record_scope: str,
    required_operations: list[str],
) -> None:
    """Validate writer authority and emit a durable security event.

    Raises PolicyImportRefused if authority is denied, and with
    ``denied-audit-sink-unavailable`` if the audit sink is unavailable; the
    caller fails closed.

    Before any durable write, the named writer is validated against its
    capability and record scope.
    """
    se = _security_events()
    operation_id = se.make_operation_id()
    if grant is None or not hasattr(grant, "grant_id"):
        # None or non-grant objects fail the authority check before the issuer call.
        # Still emit an event before refusing.
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        event = se.SecurityEvent(
            schema_version=1,
            operation_id=operation_id,
            correlation_id="unknown",
            event_type="capability-check",
            outcome="denied",
            reason_code="denied-invalid-grant",
            timestamp=timestamp,
        )
        try:
            se.emit_security_event(audit_sink, event)
        except Exception as exc:  # noqa: BLE001 — a sink failure from any module load
            raise PolicyImportRefused(
                "denied-audit-sink-unavailable",
                "audit sink unavailable; failing closed",
            ) from exc
        raise PolicyImportRefused(
            "denied-invalid-grant",
            "writer grant is None or not a CapabilityGrant",
        )
    # Delegate to the security_events module's combined authority-check-and-emit.
    # AuditSinkUnavailable is caught by its base class (Exception) because the
    # module may be loaded under a different name in tests, making isinstance
    # checks across module copies unreliable. Any non-PolicyImportRefused exception
    # from this call is a sink failure and fails closed.
    try:
        allowed = se.check_writer_authority_and_emit(
            issuer=issuer,
            grant=grant,
            record_scope=record_scope,
            required_operations=required_operations,
            sink=audit_sink,
            operation_id=operation_id,
            correlation_id=grant.grant_id,
        )
    except PolicyImportRefused:
        raise
    except Exception as exc:  # noqa: BLE001 — includes AuditSinkUnavailable from any load
        raise PolicyImportRefused(
            "denied-audit-sink-unavailable",
            "audit sink unavailable; failing closed",
        ) from exc
    if not allowed:
        raise PolicyImportRefused(
            "denied-writer-authority",
            f"writer authority denied for record scope {record_scope!r}",
        )


# ── Refs ambiguity check ──────────────────────────────────────────────────────
#
# A refs dict is ambiguous when any value is not a non-empty string, or when the
# same value appears under two or more distinct keys (two criteria reference the
# same approval, making neither uniquely identifiable).  Both cases prevent the
# reviewed-execution-envelope fingerprint from being unambiguous.


def _check_refs_unambiguous(refs: object) -> None:
    """Raise PolicyImportRefused when refs contains empty or duplicate values.

    Grounds the definition: a criterion is ambiguous when its ref value is empty
    or blank (cannot name the approval), or when the same non-empty string value
    appears for two distinct keys (two different criteria claim the same approval,
    so neither can be uniquely identified).

    Called before derive_envelope so the refusal carries the stable code
    ``denied-ambiguous-criterion`` rather than a generic derivation error.
    """
    if not isinstance(refs, dict):
        raise PolicyImportRefused(
            "denied-ambiguous-criterion",
            "refs must be a dict of approval reference strings",
        )
    seen: dict[str, str] = {}  # value → first key that claimed it
    for key, value in refs.items():
        if not isinstance(value, str) or not value.strip():
            raise PolicyImportRefused(
                "denied-ambiguous-criterion",
                f"ref {key!r} is empty or not a string; cannot uniquely identify the approval",
            )
        if value in seen:
            raise PolicyImportRefused(
                "denied-ambiguous-criterion",
                f"refs {seen[value]!r} and {key!r} share the same value "
                f"{value!r}; criterion cannot be uniquely identified",
            )
        seen[value] = key


# ── RFC 3339 timestamp ────────────────────────────────────────────────────────


def _now_rfc3339() -> str:
    """Current UTC instant as RFC 3339."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Repo-relative spec reference ──────────────────────────────────────────────
#
# Approval records store spec_ref as a portable repository-relative path.
# Absolute caller paths (e.g. from os.getcwd()) are not portable across
# machines and are not meaningful as a spec identity.


def _repo_relative_spec_ref(spec_path: Path) -> str:
    """Return a repo-relative path string for spec_path when under a git root.

    Walks parent directories looking for a ``.git`` entry.  If found and
    spec_path is under that root, returns the POSIX-style relative path.
    Without a git root, returns ``<spec-dir-name>/<file-name>`` so a host
    path, which may include a home directory, never enters the record.
    """
    resolved = spec_path.resolve()
    current = resolved.parent
    while current != current.parent:
        if (current / ".git").exists():
            try:
                return resolved.relative_to(current).as_posix()
            except ValueError:
                break
        current = current.parent
    return f"{resolved.parent.name}/{resolved.name}"


# ── Record builders ───────────────────────────────────────────────────────────


def _build_approval_record(
    *,
    approval_id: str,
    authority_identity: str,
    authority_role: str,
    decision_scope: str,
    manifest_ref: str,
    spec_ref: str,
    spec_policy_fingerprint: str,
    decision: str,
    timestamp: str,
) -> dict:
    """Build an approval-record.v1 dict."""
    return {
        "schema_version": SUPPORTED_APPROVAL_SCHEMA_VERSION,
        "approval_id": approval_id,
        "authority": {
            "identity": authority_identity,
            "role": authority_role,
        },
        "decision_scope": decision_scope,
        "base": {"manifest_ref": manifest_ref},
        "lineage": {"spec_ref": spec_ref},
        "spec_policy_fingerprint": spec_policy_fingerprint,
        "decision": decision,
        "timestamp": timestamp,
    }


def _build_initial_review(
    *,
    review_id: str,
    envelope_fingerprint: str,
    plan_hash: str,
    authorized_terminal_intent: str,
    reviewer_identity: str,
    reviewer_role: str,
    decision: str,
    timestamp: str,
) -> dict:
    """Build an initial-plan-review.v1 dict."""
    return {
        "schema_version": SUPPORTED_INITIAL_REVIEW_SCHEMA_VERSION,
        "review_id": review_id,
        "envelope_fingerprint": envelope_fingerprint,
        "plan_hash": plan_hash,
        "authorized_terminal_intent": authorized_terminal_intent,
        "reviewer": {
            "identity": reviewer_identity,
            "role": reviewer_role,
        },
        "decision": decision,
        "timestamp": timestamp,
    }


# ── import_policy ─────────────────────────────────────────────────────────────


def import_policy(
    *,
    spec_path: Path,
    plan_path: Path,
    refs: dict[str, str],
    terminal_intent: str,
    writer_grant: object,
    issuer: object,
    audit_sink: Callable[[Any], None],
    store: ImportStore,
    approval_identity: str,
    approval_role: str,
    reviewer_identity: str,
    reviewer_role: str,
    approved_spec_digest: str,
    approved_plan_digest: str,
    approved_envelope_fingerprint: str | None,
) -> tuple[dict, dict]:
    """Atomically import the current approved spec-policy decision.

    Produces exactly one ``approval-record.v1`` and one ``initial-plan-review.v1``
    record, both visible together in *store* after a successful call, or neither
    on any failure.

    Parameters
    ----------
    spec_path:
        Path to the spec file whose canonical digest is computed and compared.
    plan_path:
        Path to the plan file whose canonical digest is computed and compared.
    refs:
        Ordered mapping from each approval-reference role to its opaque ref
        string.  All values must be non-empty strings; the same value appearing
        under two distinct keys is refused as ambiguous.
    terminal_intent:
        The authorized terminal intent string bound to the initial plan review.
    writer_grant:
        Capability grant authorising this import operation.
    issuer:
        Issuer that issued *writer_grant*.
    audit_sink:
        Callable that durably persists a security event before any durable write.
    store:
        Import store to commit records into.
    approval_identity, approval_role:
        Identity and role of the spec-policy approval authority.
    reviewer_identity, reviewer_role:
        Identity and role of the plan-review authority.
    approved_spec_digest:
        Expected SHA-256 of the canonical spec (the current approval pin).
        The computed digest must equal this value; any mismatch refuses.
    approved_plan_digest:
        Expected SHA-256 of the canonical plan (the current approval pin).
        The computed digest must equal this value; any mismatch refuses.
    approved_envelope_fingerprint:
        Required keyword.  When not ``None``, the fingerprint derived from
        *refs* must equal this value; any mismatch refuses.  Pass ``None``
        only for non-authoritative callers that have no envelope to compare
        (e.g. a shadow facade whose legacy approval pin stores no fingerprint).
        Any caller that grants authority must supply a real envelope pin.

    Returns
    -------
    tuple[dict, dict]
        ``(approval_record, initial_plan_review)`` on success.

    Raises
    ------
    PolicyImportRefused
        On any validation, authority, pin-mismatch, or content-safety failure.

        Stable denial codes:
        ``denied-already-imported``       — store already contains records.
        ``denied-ambiguous-criterion``    — refs has duplicate or empty values.
        ``denied-spec-digest-mismatch``   — computed spec digest != approved pin.
        ``denied-plan-digest-mismatch``   — computed plan digest != approved pin.
        ``denied-envelope-mismatch``      — derived envelope fp != approved pin.
        ``denied-schema-invalid-approval`` — built approval record fails validation.
        ``denied-schema-invalid-review``  — built initial review fails validation.
    """
    # Replay protection: if the store already has records this is a double-import.
    if store.record_count() > 0:
        raise PolicyImportRefused(
            "denied-already-imported",
            "store already contains records; re-import is not permitted",
        )

    # Step 1 — validate writer authority.
    _check_writer_authority(
        issuer,
        writer_grant,
        audit_sink=audit_sink,
        record_scope="delivery/policy-import",
        required_operations=["append"],
    )

    # Step 2 — validate terminal intent.
    if not isinstance(terminal_intent, str) or not terminal_intent.strip():
        raise PolicyImportRefused(
            "denied-invalid-terminal-intent",
            "terminal_intent must be a non-empty string",
        )

    # Step 3 — refuse ambiguous criterion references before computing digests.
    _check_refs_unambiguous(refs)

    # Step 4 — compute digests via _loop_guards.
    try:
        spec_digest = compute_spec_digest(spec_path)
        plan_digest = compute_plan_digest(plan_path)
    except (OSError, ValueError, ImportError) as exc:
        raise PolicyImportRefused(
            "denied-canonicalization-failed",
            "failed to compute canonical digests",
        ) from exc

    # Step 5 — compare computed digests against the caller's approval pins.
    if spec_digest != approved_spec_digest:
        raise PolicyImportRefused(
            "denied-spec-digest-mismatch",
            "computed spec digest does not match the approved pin",
        )
    if plan_digest != approved_plan_digest:
        raise PolicyImportRefused(
            "denied-plan-digest-mismatch",
            "computed plan digest does not match the approved pin",
        )

    # Step 6 — derive the reviewed-execution-envelope.
    acc = _acceptance()
    try:
        envelope = acc.derive_envelope(refs)
    except Exception as exc:  # noqa: BLE001 — map AcceptanceRefused to PolicyImportRefused
        raise PolicyImportRefused(
            "denied-envelope-derivation",
            "envelope derivation failed",
        ) from exc
    envelope_fingerprint: str = envelope["envelope_fingerprint"]

    # Step 7 — optionally compare envelope fingerprint against the caller's pin.
    if (
        approved_envelope_fingerprint is not None
        and envelope_fingerprint != approved_envelope_fingerprint
    ):
        raise PolicyImportRefused(
            "denied-envelope-mismatch",
            "derived envelope fingerprint does not match the approved pin",
        )

    # Validate approval authority identity and role.
    if not isinstance(approval_identity, str) or not approval_identity.strip():
        raise PolicyImportRefused(
            "denied-invalid-authority-identity",
            "approval_identity must be a non-empty string",
        )
    if not isinstance(approval_role, str) or not approval_role.strip():
        raise PolicyImportRefused(
            "denied-invalid-authority-role",
            "approval_role must be a non-empty string",
        )

    # Step 8 — build the approval-record.v1.
    approval_id = "appr-" + secrets.token_hex(12)
    timestamp = _now_rfc3339()
    approval_record = _build_approval_record(
        approval_id=approval_id,
        authority_identity=approval_identity,
        authority_role=approval_role,
        decision_scope="spec-policy",
        manifest_ref=plan_digest,
        spec_ref=_repo_relative_spec_ref(spec_path),
        spec_policy_fingerprint=spec_digest,
        decision="approved",
        timestamp=timestamp,
    )

    # Validate the built approval record against its contract before staging.
    _val_ok, _val_code = validate_approval_dict(approval_record)
    if not _val_ok:
        raise PolicyImportRefused(
            "denied-schema-invalid-approval",
            f"built approval record failed schema validation: {_val_code}",
        )

    # Apply content-safety profile before staging.
    _check_record_safety(
        approval_record,
        "approval-record.v1",
        record_id=approval_id,
    )

    # Step 9 — stage the approval record.
    store._stage(approval_record)

    # Validate reviewer identity.
    if not isinstance(reviewer_identity, str) or not reviewer_identity.strip():
        store._rollback()
        raise PolicyImportRefused(
            "denied-invalid-reviewer-identity",
            "reviewer_identity must be a non-empty string",
        )
    if not isinstance(reviewer_role, str) or not reviewer_role.strip():
        store._rollback()
        raise PolicyImportRefused(
            "denied-invalid-reviewer-role",
            "reviewer_role must be a non-empty string",
        )

    # Step 10 — build the initial-plan-review.v1.
    review_id = "rev-" + secrets.token_hex(12)
    initial_review = _build_initial_review(
        review_id=review_id,
        envelope_fingerprint=envelope_fingerprint,
        plan_hash=plan_digest,
        authorized_terminal_intent=terminal_intent,
        reviewer_identity=reviewer_identity,
        reviewer_role=reviewer_role,
        decision="accepted",
        timestamp=timestamp,
    )

    # Validate the built initial review against its contract before staging.
    _val_ok, _val_code = validate_initial_review_dict(initial_review)
    if not _val_ok:
        store._rollback()
        raise PolicyImportRefused(
            "denied-schema-invalid-review",
            f"built initial review failed schema validation: {_val_code}",
        )

    # Apply content-safety profile before staging.
    try:
        _check_record_safety(
            initial_review,
            "initial-plan-review.v1",
            record_id=review_id,
        )
    except PolicyImportRefused:
        store._rollback()
        raise

    # Step 11 — stage the initial-plan-review record.
    store._stage(initial_review)

    # Step 12 — commit atomically.
    try:
        store._commit()
    except PolicyImportRefused:
        store._rollback()
        raise

    return approval_record, initial_review


# ── reverse_read ─────────────────────────────────────────────────────────────
#
# Dual-read path.  Returns the original (approval, initial_review) pair
# reconstructed from the store.  No resolver, no snapshot production.


def reverse_read(store: ImportStore) -> tuple[dict, dict]:
    """Reconstruct the original approved pair from the store (dual-read).

    Returns:
        ``(approval_record, initial_plan_review)`` as stored.

    Raises PolicyImportRefused when the store is empty or does not contain
    exactly two identifiable records.
    """
    records = store.get_records()
    if len(records) == 0:
        raise PolicyImportRefused(
            "denied-empty-store",
            "reverse_read requires records in the store",
        )
    if len(records) != 2:
        raise PolicyImportRefused(
            "denied-incomplete-store",
            "reverse_read requires exactly 2 records",
        )

    approval_record: dict | None = None
    initial_review: dict | None = None
    for rec in records:
        if rec.get("decision_scope") == "spec-policy":
            approval_record = rec
        elif rec.get("authorized_terminal_intent") is not None:
            initial_review = rec

    if approval_record is None or initial_review is None:
        raise PolicyImportRefused(
            "denied-unrecognized-record-types",
            "reverse_read could not identify approval and initial-review records",
        )

    return approval_record, initial_review


# ── compatibility_snapshot ────────────────────────────────────────────────────
#
# Post-cutover compatibility path.
#
# The resolver answers whether an accepted authority-switch governance decision
# exists; it returns a decision dict carrying its governance reference, envelope
# fingerprint, and terminal intent.  It never builds the snapshot.
#
# This module:
#   1. Calls the resolver.
#   2. Validates the decision's envelope_fingerprint and terminal_intent against
#      the stored records (refusing lossy or boundary-crossing projections).
#   3. Builds the snapshot itself with grants_target_authority=False (enforced
#      regardless of any field in the resolver's decision dict).
#   4. Verifies the store's records are byte-identical before and after.
#
# The module default resolver refuses with "denied-no-governance-record"
# because no accepted authority-switch governance record exists.
# Test fixtures (defined in the test file) supply a resolver that returns
# the decision dict.


def _default_governance_resolver() -> dict:
    """Module default: refuses because no accepted authority-switch governance record exists."""
    raise PolicyImportRefused(
        "denied-no-governance-record",
        "no accepted authority-switch governance record exists",
    )


def compatibility_snapshot(
    store: ImportStore,
    *,
    authority_resolver: Callable[[], dict] = _default_governance_resolver,
) -> dict:
    """Produce a within-envelope compatibility snapshot.

    The *authority_resolver* answers whether an accepted authority-switch
    governance decision exists.  It returns a decision dict with at minimum
    ``envelope_fingerprint`` and ``terminal_intent`` fields (plus a governance
    reference for audit provenance).

    This module enforces all snapshot invariants: it validates the decision's
    fields against stored records, builds the snapshot itself, and verifies
    the store is byte-identical before and after (no semantic fact deleted or
    changed).

    The snapshot always carries ``grants_target_authority=False``; no value in
    the resolver's decision dict can override this.

    Refusal codes:
      - ``denied-empty-store`` / ``denied-incomplete-store``: store is wrong size.
      - ``denied-unrecognized-record-types``: records are not identifiable.
      - ``denied-no-governance-record``: default resolver; no governance record exists.
      - ``denied-invalid-decision-shape``: resolver returned a non-dict or dict
        missing required fields.
      - ``denied-lossy-projection``: decision fingerprint ≠ stored fingerprint.
      - ``denied-boundary-crossing-projection``: decision intent ≠ stored intent.
      - ``denied-semantic-mutation``: store records changed during production.
      - ``denied-resolver-error``: resolver raised an unexpected exception.

    Returns:
        A dict with ``is_compatibility_snapshot=True`` and
        ``grants_target_authority=False``.
    """
    import json as _json

    records = store.get_records()
    if len(records) == 0:
        raise PolicyImportRefused(
            "denied-empty-store",
            "compatibility_snapshot requires records in the store",
        )
    if len(records) != 2:
        raise PolicyImportRefused(
            "denied-incomplete-store",
            "compatibility_snapshot requires exactly 2 records",
        )

    approval_record: dict | None = None
    initial_review: dict | None = None
    for rec in records:
        if rec.get("decision_scope") == "spec-policy":
            approval_record = rec
        elif rec.get("authorized_terminal_intent") is not None:
            initial_review = rec

    if approval_record is None or initial_review is None:
        raise PolicyImportRefused(
            "denied-unrecognized-record-types",
            "compatibility_snapshot could not identify approval and initial-review records",
        )

    stored_fp: str = initial_review.get("envelope_fingerprint", "")
    stored_intent: str = initial_review.get("authorized_terminal_intent", "")

    # Fingerprint the store before any operation (byte-identical check later).
    def _bytes(rec: dict) -> str:
        return _json.dumps(rec, sort_keys=True, ensure_ascii=True)

    before = [_bytes(r) for r in store.get_records()]

    # Step 1 — call the resolver.  Default refuses; test fixtures grant.
    try:
        decision = authority_resolver()
    except PolicyImportRefused:
        raise
    except Exception as exc:  # noqa: BLE001
        raise PolicyImportRefused(
            "denied-resolver-error",
            "authority resolver raised an unexpected error",
        ) from exc

    # Step 2 — validate decision shape.
    if not isinstance(decision, dict):
        raise PolicyImportRefused(
            "denied-invalid-decision-shape",
            "authority resolver must return a dict",
        )
    decision_fp = decision.get("envelope_fingerprint", "")
    decision_intent = decision.get("terminal_intent", "")
    if not isinstance(decision_fp, str) or not decision_fp:
        raise PolicyImportRefused(
            "denied-invalid-decision-shape",
            "decision missing envelope_fingerprint",
        )
    if not isinstance(decision_intent, str) or not decision_intent:
        raise PolicyImportRefused(
            "denied-invalid-decision-shape",
            "decision missing terminal_intent",
        )

    # Lossy-projection check.
    if decision_fp != stored_fp:
        raise PolicyImportRefused(
            "denied-lossy-projection",
            "decision envelope_fingerprint does not match stored records",
        )
    # Boundary-crossing check.
    if decision_intent != stored_intent:
        raise PolicyImportRefused(
            "denied-boundary-crossing-projection",
            "decision terminal_intent does not match stored records",
        )

    # Step 3 — build the snapshot.  grants_target_authority is always False;
    # the resolver's decision dict cannot override this module-enforced invariant.
    snapshot: dict = {
        "is_compatibility_snapshot": True,
        "grants_target_authority": False,
        "envelope_fingerprint": stored_fp,
        "terminal_intent": stored_intent,
        "approval_id_ref": approval_record.get("approval_id", ""),
        "review_id_ref": initial_review.get("review_id", ""),
    }

    # Step 4 — verify the store is byte-identical (no semantic mutation).
    after = [_bytes(r) for r in store.get_records()]
    if before != after:
        raise PolicyImportRefused(
            "denied-semantic-mutation",
            "store records were mutated during snapshot production",
        )

    return snapshot


# ── In-code schema validation ─────────────────────────────────────────────────
#
# Every module that emits delivery records validates them in code and refuses
# each schema-invalid case with a stable denial code.

# Required fields for approval-record.v1.
_APPROVAL_REQUIRED: Final[frozenset[str]] = frozenset({
    "schema_version",
    "approval_id",
    "authority",
    "decision_scope",
    "base",
    "lineage",
    "spec_policy_fingerprint",
    "decision",
    "timestamp",
})

# All permitted fields for approval-record.v1 (additionalProperties: false).
_APPROVAL_ALLOWED: Final[frozenset[str]] = _APPROVAL_REQUIRED

# Valid values for approval-record.v1 decision.
_APPROVAL_DECISIONS: Final[frozenset[str]] = frozenset({"approved", "superseded"})

# Required fields for initial-plan-review.v1.
_REVIEW_REQUIRED: Final[frozenset[str]] = frozenset({
    "schema_version",
    "review_id",
    "envelope_fingerprint",
    "plan_hash",
    "authorized_terminal_intent",
    "reviewer",
    "decision",
})

# All permitted fields for initial-plan-review.v1 (additionalProperties: false).
# timestamp is optional in the schema ("required" excludes it).
_REVIEW_ALLOWED: Final[frozenset[str]] = _REVIEW_REQUIRED | frozenset({"timestamp"})

# Valid values for initial-plan-review.v1 decision.
_REVIEW_DECISIONS: Final[frozenset[str]] = frozenset({"accepted"})


def validate_approval_dict(record: object) -> tuple[bool, str]:
    """Validate *record* against the ``approval-record.v1`` contract.

    Returns ``(True, "ok")`` on success or ``(False, denial_code)`` on failure.
    Checks schema_version first, then required fields, then allowed fields,
    then decision enum.

    Denial codes are stable across versions.
    """
    if not isinstance(record, dict):
        return False, "denied-not-a-dict"
    sv = record.get("schema_version")
    if sv != SUPPORTED_APPROVAL_SCHEMA_VERSION:
        return False, "denied-unknown-schema-version"
    for field in _APPROVAL_REQUIRED:
        if field not in record:
            return False, "denied-missing-required-field"
    unknown = set(record) - _APPROVAL_ALLOWED
    if unknown:
        return False, "denied-unknown-authority-field"
    if record.get("decision") not in _APPROVAL_DECISIONS:
        return False, "denied-invalid-enum"
    return True, "ok"


def validate_initial_review_dict(record: object) -> tuple[bool, str]:
    """Validate *record* against the ``initial-plan-review.v1`` contract.

    Returns ``(True, "ok")`` on success or ``(False, denial_code)`` on failure.
    Checks schema_version first, then required fields, then allowed fields,
    then decision enum.

    Denial codes are stable across versions.
    """
    if not isinstance(record, dict):
        return False, "denied-not-a-dict"
    sv = record.get("schema_version")
    if sv != SUPPORTED_INITIAL_REVIEW_SCHEMA_VERSION:
        return False, "denied-unknown-schema-version"
    for field in _REVIEW_REQUIRED:
        if field not in record:
            return False, "denied-missing-required-field"
    unknown = set(record) - _REVIEW_ALLOWED
    if unknown:
        return False, "denied-unknown-authority-field"
    if record.get("decision") not in _REVIEW_DECISIONS:
        return False, "denied-invalid-enum"
    return True, "ok"
