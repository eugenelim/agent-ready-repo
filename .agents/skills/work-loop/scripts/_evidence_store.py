"""_evidence_store — append-only evidence transaction log.

All-or-none guarantee: each frame exposes all embedded records (receipts or
supersessions) together or not at all. An incomplete final frame (no trailing
newline) is truncated on restart. A frame with a bad checksum or mismatched
record IDs is a hard error; the store refuses to open.

Superseded-receipt exclusion: active-receipt evaluation excludes superseded
receipts. Stale exact-subject receipts (acceptance_fingerprint mismatch) are
filtered by the acceptance evaluator. Contradiction is evaluated before
satisfaction.

Producer authority: every append validates the named producer grant before
staging bytes. Missing, expired, mismatched, or out-of-scope grant exposes no
partial frame.

Idempotent retry: a retry passes the same producer-authority check and audit
requirement as a first append, so a retry under invalid authority or an
unavailable sink also fails.  An authorised retry with the same
transaction_id, identical record, and identical acceptance fingerprint
produces no second frame; the committed transaction is returned unchanged.  A
different record that reuses an already-admitted receipt_id, supersession_id,
or transaction_id is refused with a stable denial code via the audited
post-allow denial path.  Reuse is decided again against the durable log under
the same advisory lock as the write, so another open store instance cannot
admit a duplicate.

Duplicates on replay: replay rejects only checksum or reference corruption.  A
frame that reuses a transaction_id, receipt_id, or supersession_id already
seen in the log is skipped, so the first admitted record stays authoritative
and a log written by older or concurrent writers still opens.

Audit sink required: when the audit sink is unavailable the operation fails
closed with a stable redacted denial code. No frame is appended and no
protected data persists.

Advisory lock deadline: the exclusive advisory lock (fcntl.flock) is acquired
with a bounded deadline.  If the deadline expires before the lock is obtained,
the operation is refused with ``denied-lock-timeout`` (EvidenceStoreRefused)
and no bytes are staged.

Frame format (one JSON line per frame, terminated with newline):
  {"tx": <semantic-evidence-transaction.v1>, "records": [<receipt or supersession>...]}

The transaction's checksum field equals:
  sha256(<canonical JSON of {"tx": tx_without_checksum, "records": records}>)

prefixed with "sha256:". Identical frame contents always produce the same checksum.

Standard library only. Loads sibling modules by path using the pattern
established in _policy_import.py and _confined_mutation.py.

Python 3.11+.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import os
import stat
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Final, Generator

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = [
    # Exceptions
    "EvidenceStoreError",
    "EvidenceStoreRefused",
    # Store
    "EvidenceStore",
    # Schema version constants
    "SUPPORTED_TRANSACTION_SCHEMA_VERSION",
    "SUPPORTED_RECEIPT_SCHEMA_VERSION",
    "SUPPORTED_SUPERSESSION_SCHEMA_VERSION",
    # In-code validation
    "validate_transaction_dict",
    "validate_receipt_dict",
    "validate_supersession_dict",
]

# ── Schema version constants ───────────────────────────────────────────────────

SUPPORTED_TRANSACTION_SCHEMA_VERSION: Final[int] = 1
SUPPORTED_RECEIPT_SCHEMA_VERSION: Final[int] = 1
SUPPORTED_SUPERSESSION_SCHEMA_VERSION: Final[int] = 1

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parent

# ── Advisory locking (platform-optional) ──────────────────────────────────────
#
# When fcntl is available, every append and recovery truncation acquires an
# exclusive advisory lock on the log file to serialise them.  Recovery then
# never removes a frame that an appender just committed, and an appender never
# races with an in-progress in-place truncation.  The fallback (no fcntl) keeps
# the prior behaviour on platforms that do not ship the module (e.g. Windows).

try:
    import fcntl as _fcntl
    _HAS_FCNTL: bool = True
except ImportError:
    _HAS_FCNTL = False

# Upper bound on evidence log reads.  Measured from the 100,000-receipt
# benchmark corpus: each frame is ~574 bytes; 100,000 frames ≈ 57 MB.
# This constant is ~4.5× that corpus size, giving clear headroom for growth
# while preventing unbounded reads in _load_and_truncate.
_EVIDENCE_LOG_MAX_BYTES: Final[int] = 256 * 1024 * 1024  # 256 MiB

# Advisory lock acquisition parameters.  The lock is very briefly held
# (duration of a single confined_append call), so 5 s covers pathological
# contention while still bounding the wait.  Tests may monkeypatch these
# module-level constants to drive the timeout path without sleeping.
_LOCK_TIMEOUT: float = 5.0   # seconds to wait before refusing with denied-lock-timeout
_LOCK_POLL: float = 0.05     # poll interval (seconds) for the non-blocking retry loop


def _regular_file_identity(path: Path) -> tuple[int, int] | None:
    """Return ``(st_dev, st_ino)`` for a regular file at *path*, without following links."""
    try:
        info = os.lstat(path)
    except OSError:
        return None
    return (info.st_dev, info.st_ino) if stat.S_ISREG(info.st_mode) else None


@contextlib.contextmanager
def _advisory_lock(
    root: Path,
    path: Path,
    *,
    expected_identity: tuple[int, int] | None = None,
) -> Generator[int, None, None]:
    """Acquire an exclusive advisory lock on *path* via a confined parent-fd walk.

    Yield the open fd.  Opens the log through its parent directory fd with O_RDWR, O_NOFOLLOW,
    O_NONBLOCK, and O_CLOEXEC.  Refuses when the target is not a regular file,
    has more than one hard link, or (when expected_identity is supplied) its
    (st_dev, st_ino) differs from the identity recorded at read time.  A FIFO
    placed at the log path raises EvidenceStoreError without blocking.

    The lock is acquired with a bounded deadline using a non-blocking retry
    loop (``LOCK_EX | LOCK_NB``).  If ``_LOCK_TIMEOUT`` seconds elapse before
    the lock is obtained, raises ``EvidenceStoreRefused`` with the stable code
    ``denied-lock-timeout``.  The lock is released and the fd closed on exit
    regardless of exceptions.  Not called when _HAS_FCNTL is False.
    """
    fs = _file_safety()
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise EvidenceStoreError(
            f"advisory lock path is outside root: {path}"
        ) from exc

    open_flags = os.O_RDWR
    for _flag in ("O_NOFOLLOW", "O_NONBLOCK", "O_CLOEXEC"):
        if hasattr(os, _flag):
            open_flags |= getattr(os, _flag)

    fd = -1
    try:
        try:
            with fs._open_confined_parent(root, path, relative=relative) as (parent_fd, leaf):
                if parent_fd is None:
                    # Fallback host: open by path with the no-follow flags.
                    fd = os.open(str(path), open_flags)
                else:
                    fd = os.open(leaf, open_flags, dir_fd=parent_fd)
        except fs.UnsafeContentError as exc:
            raise EvidenceStoreError(
                f"advisory lock path failed confinement check: {exc}"
            ) from exc

        file_stat = os.fstat(fd)
        if not stat.S_ISREG(file_stat.st_mode):
            raise EvidenceStoreError(
                f"advisory lock target is not a regular file: {relative}"
            )
        if file_stat.st_nlink != 1:
            raise EvidenceStoreError(
                f"advisory lock target has more than one hard link: {relative}"
            )
        if expected_identity is not None and (
            file_stat.st_dev, file_stat.st_ino
        ) != expected_identity:
            raise EvidenceStoreError(
                f"advisory lock target identity changed since read: {relative}"
            )

        # Non-blocking retry loop with a deadline so the caller is never
        # suspended indefinitely.  LOCK_NB causes flock to raise
        # BlockingIOError (errno EWOULDBLOCK) immediately when the lock is
        # held by another open-file-description; we sleep and retry until
        # the deadline, then refuse with a stable code.
        _deadline = time.monotonic() + _LOCK_TIMEOUT
        while True:
            try:
                _fcntl.flock(fd, _fcntl.LOCK_EX | _fcntl.LOCK_NB)  # type: ignore[name-defined]
                break
            except BlockingIOError:
                if time.monotonic() >= _deadline:
                    raise EvidenceStoreRefused(
                        "denied-lock-timeout",
                        f"advisory lock on {path.name!r} not acquired within "
                        f"{_LOCK_TIMEOUT}s; failing closed",
                    ) from None
                time.sleep(_LOCK_POLL)
        try:
            yield fd
        finally:
            _fcntl.flock(fd, _fcntl.LOCK_UN)  # type: ignore[name-defined]

    except EvidenceStoreError:
        raise
    except OSError as exc:
        raise EvidenceStoreError(f"advisory lock failed: {exc}") from exc
    finally:
        if fd >= 0:
            with contextlib.suppress(OSError):
                os.close(fd)

# ── Exceptions ─────────────────────────────────────────────────────────────────


class EvidenceStoreError(Exception):
    """Base exception for evidence store operations.

    Raised when the store detects a hard error (e.g., checksum mismatch, reference
    corruption, or I/O failure). The caller must treat the store as unrecoverable.
    """


class EvidenceStoreRefused(EvidenceStoreError):
    """An evidence store operation was refused with a stable denial code.

    ``denial_code`` carries a stable string that callers may log without
    sensitive payload bytes, excerpts, or content-derived hashes. No identity,
    correlation, or retry key may be derived from refused bytes.
    """

    def __init__(self, denial_code: str, message: str = "") -> None:
        super().__init__(message or denial_code)
        self.denial_code: str = denial_code


# ── Sibling module loaders ─────────────────────────────────────────────────────
#
# Each sibling is loaded lazily on first use and cached. The loader pattern
# follows _confined_mutation.py and _policy_import.py:
#   - lstat + S_ISREG on the path before exec_module.
#   - sys.dont_write_bytecode saved and restored to its prior value.
#   - NOT registered in sys.modules (avoids session-global singleton leaks).

_confined_mutation_module: ModuleType | None = None
_content_safety_module: ModuleType | None = None
_security_events_module: ModuleType | None = None
_file_safety_module: ModuleType | None = None


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


def _confined_mutation() -> ModuleType:
    """Lazily load _confined_mutation.py."""
    global _confined_mutation_module
    if _confined_mutation_module is None:
        _confined_mutation_module = _load_sibling(
            "_es_confined_mutation", "_confined_mutation.py"
        )
    return _confined_mutation_module


def _content_safety() -> ModuleType:
    """Lazily load _content_safety.py."""
    global _content_safety_module
    if _content_safety_module is None:
        _content_safety_module = _load_sibling(
            "_es_content_safety", "_content_safety.py"
        )
    return _content_safety_module


def _security_events() -> ModuleType:
    """Lazily load _security_events.py."""
    global _security_events_module
    if _security_events_module is None:
        _security_events_module = _load_sibling(
            "_es_security_events", "_security_events.py"
        )
    return _security_events_module


def _file_safety() -> ModuleType:
    """Lazily load file_safety.py for no-follow confined reads of the evidence log."""
    global _file_safety_module
    if _file_safety_module is None:
        _file_safety_module = _load_sibling("_es_file_safety", "file_safety.py")
    return _file_safety_module


# ── Frame format helpers ───────────────────────────────────────────────────────


def _canonical_json(obj: Any) -> str:
    """Canonical JSON serialization with sorted keys and no extra whitespace."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _compute_frame_checksum(tx_without_checksum: dict, records: list) -> str:
    """Compute SHA-256 checksum over the frame content (tx header + records).

    The checksum covers the canonical JSON of::

        {"records": [...], "tx": {...tx without checksum...}}

    with ``sort_keys=True`` so identical content always yields the same checksum.
    Prefixed with "sha256:".
    """
    payload = {"tx": tx_without_checksum, "records": records}
    canonical = _canonical_json(payload)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _build_transaction(
    transaction_id: str,
    ordered_record_ids: list[str],
    acceptance_fingerprint: str,
    records: list[dict],
) -> dict:
    """Build a ``semantic-evidence-transaction.v1`` record with checksum.

    The checksum covers the transaction body (all fields except ``checksum``)
    and the embedded records, ensuring frame integrity.
    """
    tx_body: dict = {
        "schema_version": SUPPORTED_TRANSACTION_SCHEMA_VERSION,
        "transaction_id": transaction_id,
        "ordered_record_ids": ordered_record_ids,
        "acceptance_fingerprint": acceptance_fingerprint,
    }
    checksum = _compute_frame_checksum(tx_body, records)
    return {**tx_body, "checksum": checksum}


def _serialize_frame(tx: dict, records: list[dict]) -> bytes:
    """Serialize a frame to bytes: one JSON line terminated with ``\\n``.

    A frame without a trailing newline is incomplete; the store truncates to
    the last complete frame on restart.
    """
    line = _canonical_json({"tx": tx, "records": records})
    return (line + "\n").encode("utf-8")


def _verify_frame(tx: dict, records: list) -> None:
    """Verify a frame's checksum and record ID references.

    Raises ``EvidenceStoreError`` on any corruption:
      - Checksum mismatch: the frame bytes were modified after write.
      - Reference mismatch: ``ordered_record_ids`` does not match actual record IDs.
    """
    # Checksum check: recompute over the tx body (without checksum) and records.
    tx_without_checksum = {k: v for k, v in tx.items() if k != "checksum"}
    expected = _compute_frame_checksum(tx_without_checksum, records)
    stored = tx.get("checksum", "")
    if stored != expected:
        txid = tx.get("transaction_id", "?")
        raise EvidenceStoreError(
            f"frame checksum mismatch for transaction {txid!r}: "
            f"stored {stored!r} != expected {expected!r}"
        )

    # Reference check: ordered_record_ids must match the actual embedded record IDs.
    ordered_ids = tx.get("ordered_record_ids", [])
    if len(ordered_ids) != len(records):
        raise EvidenceStoreError(
            f"ordered_record_ids length {len(ordered_ids)} "
            f"does not match records length {len(records)}"
        )
    for expected_id, record in zip(ordered_ids, records, strict=True):
        # A record is either a receipt (receipt_id) or a supersession (supersession_id).
        actual_id = record.get("receipt_id") or record.get("supersession_id", "")
        if actual_id != expected_id:
            raise EvidenceStoreError(
                f"reference mismatch: expected record ID {expected_id!r}, "
                f"got {actual_id!r}"
            )


# ── In-code schema validation ──────────────────────────────────────────────────

_TRANSACTION_REQUIRED: Final[frozenset[str]] = frozenset({
    "schema_version",
    "transaction_id",
    "ordered_record_ids",
    "acceptance_fingerprint",
    "checksum",
})
_TRANSACTION_ALLOWED: Final[frozenset[str]] = _TRANSACTION_REQUIRED

_RECEIPT_REQUIRED: Final[frozenset[str]] = frozenset({
    "schema_version",
    "receipt_id",
    "acceptance_fingerprint",
    "lineage",
    "selector",
    "freshness_mode",
    "observation",
    "outcome",
    "producer",
})
_RECEIPT_ALLOWED: Final[frozenset[str]] = _RECEIPT_REQUIRED | {"task_projection_revision"}

# Closed nested objects: name -> (required keys, allowed keys).  Each value is a
# non-empty string.
_RECEIPT_NESTED: Final[dict[str, tuple[frozenset[str], frozenset[str]]]] = {
    "lineage": (frozenset({"criterion_ref"}), frozenset({"criterion_ref", "attestation_ref"})),
    "selector": (frozenset({"term"}), frozenset({"term"})),
    "observation": (frozenset({"type"}), frozenset({"type"})),
    "producer": (frozenset({"class", "identity"}), frozenset({"class", "identity"})),
}
_RECEIPT_FRESHNESS_MODES: Final[frozenset[str]] = frozenset({"exact-subject", "path-set"})

_SUPERSESSION_REQUIRED: Final[frozenset[str]] = frozenset({
    "schema_version",
    "supersession_id",
    "superseded_receipt_ids",
    "authority",
    "provenance",
})
_SUPERSESSION_ALLOWED: Final[frozenset[str]] = _SUPERSESSION_REQUIRED


def validate_transaction_dict(d: object) -> tuple[bool, str]:
    """Validate a ``semantic-evidence-transaction.v1`` record dict in code.

    Returns ``(True, "ok")`` on success or ``(False, denial_code)`` on any failure.
    Failure codes are stable:
      denied-not-a-dict              — d is not a dict.
      denied-unknown-schema-version  — schema_version is not 1.
      denied-missing-required-field  — a required field is absent.
      denied-unknown-authority-field — a field not in the schema is present.
      denied-empty-ordered-record-ids — ordered_record_ids is empty.
    """
    if not isinstance(d, dict):
        return False, "denied-not-a-dict"
    sv = d.get("schema_version")
    if sv != SUPPORTED_TRANSACTION_SCHEMA_VERSION:
        return False, "denied-unknown-schema-version"
    for field in _TRANSACTION_REQUIRED:
        if field not in d:
            return False, "denied-missing-required-field"
    unknown = set(d) - _TRANSACTION_ALLOWED
    if unknown:
        return False, "denied-unknown-authority-field"
    oids = d.get("ordered_record_ids")
    if not isinstance(oids, list) or len(oids) == 0:
        return False, "denied-empty-ordered-record-ids"
    return True, "ok"


def validate_receipt_dict(d: object) -> tuple[bool, str]:
    """Validate an ``evidence-receipt.v1`` record dict in code.

    Returns ``(True, "ok")`` on success or ``(False, denial_code)`` on any failure.
    Failure codes are stable:
      denied-not-a-dict              — d is not a dict.
      denied-unknown-schema-version  — schema_version is not 1.
      denied-missing-required-field  — a required field is absent.
      denied-unknown-authority-field — a field not in the schema is present.
      denied-invalid-enum            — freshness_mode is not in the permitted set.
      denied-invalid-nested-field    — lineage, selector, observation, or producer
                                       is not an object with exactly its permitted
                                       non-empty string fields.
    """
    if not isinstance(d, dict):
        return False, "denied-not-a-dict"
    sv = d.get("schema_version")
    if sv != SUPPORTED_RECEIPT_SCHEMA_VERSION:
        return False, "denied-unknown-schema-version"
    for field in _RECEIPT_REQUIRED:
        if field not in d:
            return False, "denied-missing-required-field"
    unknown = set(d) - _RECEIPT_ALLOWED
    if unknown:
        return False, "denied-unknown-authority-field"
    mode = d.get("freshness_mode")
    if mode not in _RECEIPT_FRESHNESS_MODES:
        return False, "denied-invalid-enum"
    for name, (required, allowed) in _RECEIPT_NESTED.items():
        nested = d[name]
        if (
            not isinstance(nested, dict)
            or not required <= set(nested)
            or not set(nested) <= allowed
            or not all(isinstance(v, str) and v for v in nested.values())
        ):
            return False, "denied-invalid-nested-field"
    return True, "ok"


def validate_supersession_dict(d: object) -> tuple[bool, str]:
    """Validate an ``evidence-supersession.v1`` record dict in code.

    Returns ``(True, "ok")`` on success or ``(False, denial_code)`` on any failure.
    Failure codes are stable:
      denied-not-a-dict               — d is not a dict.
      denied-unknown-schema-version   — schema_version is not 1.
      denied-missing-required-field   — a required field is absent.
      denied-unknown-authority-field  — a field not in the schema is present.
      denied-empty-superseded-ids     — superseded_receipt_ids is empty.
    """
    if not isinstance(d, dict):
        return False, "denied-not-a-dict"
    sv = d.get("schema_version")
    if sv != SUPPORTED_SUPERSESSION_SCHEMA_VERSION:
        return False, "denied-unknown-schema-version"
    for field in _SUPERSESSION_REQUIRED:
        if field not in d:
            return False, "denied-missing-required-field"
    unknown = set(d) - _SUPERSESSION_ALLOWED
    if unknown:
        return False, "denied-unknown-authority-field"
    sids = d.get("superseded_receipt_ids")
    if not isinstance(sids, list) or len(sids) == 0:
        return False, "denied-empty-superseded-ids"
    return True, "ok"


# ── Security and content-safety helpers ───────────────────────────────────────


def _check_record_safety(record: dict, record_type: str, *, record_id: str) -> None:
    """Apply the content-safety profile for ``record_type`` to the record's bytes.

    Raises ``EvidenceStoreRefused`` if the profile is missing, unknown, or the
    record does not pass the check. No payload bytes are retained on rejection.

    Every write boundary applies its named content-safety profile before persisting.
    """
    cs = _content_safety()
    profile = cs.SLICE_1_WRITER_BOUNDARIES.get(record_type)
    if profile is None:
        raise EvidenceStoreRefused(
            "denied-missing-profile",
            f"no content-safety profile registered for {record_type!r}",
        )
    payload = json.dumps(record, sort_keys=True, ensure_ascii=True).encode("utf-8")
    decision = cs.check_content_safety(
        profile,
        payload,
        source_record_id=record_id,
        classification="repository-internal",
    )
    if not decision.accepted:
        raise EvidenceStoreRefused(
            f"denied-content-safety-{decision.decision_code}",
            f"content-safety rejected {record_type!r}: {decision.decision_code}",
        )


def _emit_post_allow_denial(
    audit_sink: Callable[[Any], None],
    operation_id: str,
    denial_code: str,
) -> None:
    """Emit a best-effort denial event matching a prior allow event at the same boundary.

    When a boundary stores an allow event and then refuses further processing,
    a matching denied event must be stored so the audit log remains consistent.
    Uses ``emit_denial_best_effort`` so the original refusal is never suppressed.
    Both events share the same ``operation_id``; the correlation is set to
    ``"redacted"`` because the post-allow refusal carries no grant ID.
    """
    try:
        se = _security_events()
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        event = se.SecurityEvent(
            schema_version=1,
            operation_id=operation_id,
            correlation_id="redacted",
            event_type="capability-check",
            outcome="denied",
            reason_code=denial_code,
            timestamp=timestamp,
        )
        se.emit_denial_best_effort(audit_sink, event)
    except Exception:  # noqa: BLE001 — denial emission must not suppress the original refusal
        pass


def _check_producer_authority(
    issuer: object,
    grant: object,
    *,
    audit_sink: Callable[[Any], None],
    record_scope: str,
    required_operations: list[str],
) -> str:
    """Validate producer authority and emit a durable security event.

    Returns the ``operation_id`` used in the emitted event so that callers can
    attach a matching denial event for any subsequent post-allow refusal at the
    same boundary.

    Raises ``EvidenceStoreRefused`` if authority is denied or if the audit sink
    is unavailable. The caller must fail closed: no frame is staged.

    Producer authority: before any durable write the named producer is verified
    against its capability grant and record scope; missing, expired, or
    out-of-scope grants always refuse, and retry cannot turn a denial into an
    allow.

    Audit sink required: a security event is emitted before this function
    returns (whether allowed or denied). When the sink is unavailable the
    operation fails closed and no protected data persists.
    """
    se = _security_events()
    operation_id = se.make_operation_id()

    if grant is None or not hasattr(grant, "grant_id"):
        # None or non-grant objects: emit a denial event then refuse.
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
            se.emit_denial(audit_sink, event)
        except Exception as exc:  # noqa: BLE001 — a sink failure from any module load
            raise EvidenceStoreRefused(
                "denied-audit-sink-unavailable",
                "audit sink unavailable; failing closed",
            ) from exc
        raise EvidenceStoreRefused(
            "denied-invalid-grant",
            "producer grant is None or not a CapabilityGrant",
        )

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
    except EvidenceStoreRefused:
        raise
    except Exception as exc:  # noqa: BLE001 — wraps AuditSinkUnavailable from any module load
        raise EvidenceStoreRefused(
            "denied-audit-sink-unavailable",
            "audit sink unavailable; failing closed",
        ) from exc

    if not allowed:
        raise EvidenceStoreRefused(
            "denied-producer-authority",
            f"producer authority denied for scope {record_scope!r}",
        )

    return operation_id


# ── EvidenceStore ──────────────────────────────────────────────────────────────


def _index_record(
    record: dict,
    receipts: dict[str, dict],
    by_criterion: dict[Any, list[str]],
    supersessions: dict[str, dict],
    superseded: set[str],
) -> None:
    """Index one admitted receipt or supersession into the given maps.

    Shared by replay and the post-append update so both build the same view.
    """
    if "receipt_id" in record:
        receipt_id = record["receipt_id"]
        criterion_ref = record.get("lineage", {}).get("criterion_ref")
        by_criterion.setdefault(criterion_ref, []).append(receipt_id)
        receipts[receipt_id] = record
    elif "supersession_id" in record:
        supersessions[record["supersession_id"]] = record
        superseded.update(record.get("superseded_receipt_ids", []))


class EvidenceStore:
    """Append-only evidence transaction log with crash recovery.

    Each append commits one transaction containing one or more records that
    become visible together or not at all (all-or-none guarantee: a transaction
    is visible whole or not at all).

    In-memory indexes are derived from the log and are disposable: creating a
    new ``EvidenceStore`` instance and calling ``open()`` rebuilds them from the
    log. Deleting indexes cannot change the verdict (index deletion cannot
    change the verdict).

    Usage::

        store = EvidenceStore(log_path)
        store.open()                       # creates log if absent; replays + truncates
        tx = store.append_receipt(receipt, transaction_id=..., issuer=..., ...)
        verdicts = store.evaluate_verdicts(criteria, acceptance_fp, acc_module)

    ``log_path`` must be an absolute path.  All file operations are confined to
    its lexical parent directory via ``_confined_mutation.py`` and
    ``file_safety.py`` — symlinks are never followed when deriving the
    confinement root.  A symlinked, non-regular, or out-of-root log is refused
    at ``open()`` with a stable ``denied-log-not-regular`` code; no bytes are
    read from or written to the link target.
    """

    def __init__(self, log_path: Path) -> None:
        # Use the lexical parent as the confinement root — never resolve() the
        # log path, which would follow a symlink and escape confinement.
        self._log_path: Path = log_path
        self._root: Path = log_path.parent
        # In-memory indexes (derived from log, disposable).
        self._receipts: dict[str, dict] = {}
        # criterion_ref -> receipt IDs in insertion order, so a per-criterion
        # read does not scan every receipt (per-criterion index avoids scanning all receipts).
        self._receipts_by_criterion: dict[str, list[str]] = {}
        self._supersessions: dict[str, dict] = {}
        self._superseded: set[str] = set()
        self._transactions: list[dict] = []
        self._opened: bool = False
        # Set when a rollback after a failed append itself fails, or when a
        # re-read under the lock finds the log corrupt; the file state is then
        # unknown.  Cleared only by a fresh open() call.
        self._poisoned: bool = False
        # (st_dev, st_ino) of the log file recorded at the last read.
        # Used by _truncate_log_safe to refuse a truncation when the file
        # at the log path is not the file that was read.
        self._log_identity: tuple[int, int] | None = None
        # Size of the complete-frame prefix these indexes reflect; an append under
        # the lock re-reads the log when the file no longer has this size.
        self._log_size: int = 0
        # The audit sink given to open(); recovery truncation audits through it.
        self._audit_sink: Callable[[Any], None] | None = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def open(self, audit_sink: Callable[[Any], None] | None = None) -> None:
        """Open the store: create the log if absent, replay, truncate, build indexes.

        When *audit_sink* is given, this writer port audits its own log-file
        effects: creating the log, and truncating an incomplete final frame on
        recovery.  An allow event is stored before each effect, and a refused
        effect stores a denial event with the same operation ID.

        Idempotent: calling ``open()`` on an already-open store re-reads the log
        and rebuilds indexes (equivalent to ``rebuild_indexes()``).

        A symlinked, non-regular, or inaccessible log is refused before any
        bytes are read or written.  Use ``lstat`` (no-follow) to inspect the
        log path so a symlink placed at that location is detected without
        following it.

        Raises:
            EvidenceStoreError: on I/O failure, checksum mismatch, or reference
                corruption. The store must not be used after this exception.
            EvidenceStoreRefused: if the log is a symlink, non-regular file,
                or cannot be created (denied-* code).
        """
        cm = _confined_mutation()
        self._audit_sink = audit_sink

        # Validate the log path without following symlinks: it must be absent
        # (about to be created) or a regular file.  A symlink or directory is
        # refused before any read or write is attempted.
        try:
            log_info = os.lstat(self._log_path)
        except FileNotFoundError:
            log_info = None
        except OSError as exc:
            raise EvidenceStoreRefused(
                "denied-log-not-accessible",
                f"cannot inspect evidence log: {exc}",
            ) from exc
        if log_info is not None and not stat.S_ISREG(log_info.st_mode):
            raise EvidenceStoreRefused(
                "denied-log-not-regular",
                "evidence log must be a regular file, not a symlink or directory",
            )

        if log_info is None:
            se = _security_events() if audit_sink is not None else None
            operation_id = se.make_operation_id() if se is not None else ""
            if se is not None:
                try:
                    se.emit_security_event(
                        audit_sink,
                        self._file_event(se, operation_id, "allowed", "allowed-file-create"),
                    )
                except Exception as exc:  # noqa: BLE001 — a sink failure from any module load
                    raise EvidenceStoreRefused(
                        "denied-audit-sink-unavailable",
                        "audit sink unavailable; failing closed",
                    ) from exc
            try:
                cm.confined_create(self._root, self._log_path, b"")
            except cm.MutationDenied as exc:
                if se is not None:
                    se.emit_denial_best_effort(
                        audit_sink,
                        self._file_event(se, operation_id, "denied", "denied-staging-failed"),
                    )
                raise EvidenceStoreRefused(
                    "denied-create-failed",
                    f"cannot create evidence log: {exc.denial_code}",
                ) from exc
        self._load_and_truncate()
        self._opened = True
        self._poisoned = False  # fresh replay — state is now known.

    @staticmethod
    def _file_event(
        se: ModuleType, operation_id: str, outcome: str, reason_code: str
    ) -> object:
        """Build the security event for this store's own log-file effect."""
        return se.SecurityEvent(
            schema_version=1,
            operation_id=operation_id,
            correlation_id="evidence-store",
            event_type="file-write",
            outcome=outcome,
            reason_code=reason_code,
            timestamp=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    def rebuild_indexes(self) -> None:
        """Rebuild all derived indexes from the log without changing any record.

        After rebuilding, the verdicts produced by ``evaluate_verdicts()`` are
        semantically identical to the pre-rebuild state. Deleting indexes (by
        creating a new ``EvidenceStore`` instance) and calling ``open()`` also
        rebuilds them (index deletion cannot change the verdict).
        """
        self._load_and_truncate()

    # ── Internal: log replay and truncation ────────────────────────────────────

    def _load_and_truncate(self) -> None:
        """Read the log, truncate any incomplete final frame, and build indexes.

        The read is bounded by ``_EVIDENCE_LOG_MAX_BYTES``; a log that exceeds
        this limit raises ``EvidenceStoreError`` — the store is unrecoverable.

        When an incomplete final frame is found, truncation is serialised
        against concurrent appends via an exclusive advisory lock
        (``fcntl.flock``).  The lock is acquired only for the truncate step
        so that recovery never removes a frame a concurrent appender committed.
        """
        fs = _file_safety()
        _BoundExceeded = fs.BoundExceeded  # type: ignore[attr-defined]
        identity_before = _regular_file_identity(self._log_path)
        try:
            raw = fs.read_confined_regular_file(
                self._root, self._log_path, max_bytes=_EVIDENCE_LOG_MAX_BYTES
            )
        except _BoundExceeded as exc:
            raise EvidenceStoreError(
                f"evidence log exceeds the recoverable size limit "
                f"({_EVIDENCE_LOG_MAX_BYTES} bytes); treat the store as unrecoverable"
            ) from exc
        except fs.UnsafeContentError as exc:
            # The log failed a no-follow confinement check (e.g., a symlink was
            # placed at the log path between the open() lstat check and this read).
            raise EvidenceStoreRefused(
                "denied-log-not-regular",
                f"evidence log failed confinement check: {exc}",
            ) from exc
        except OSError as exc:
            raise EvidenceStoreError(f"cannot read evidence log: {exc}") from exc

        # Record the identity of the file just read so that _truncate_log_safe
        # can refuse a truncation when the file at the path differs from the one
        # that was read.  The same no-follow identity before and after the read
        # binds it to the bytes read; any mismatch records none, and recovery
        # then refuses to truncate.
        identity_after = _regular_file_identity(self._log_path)
        self._log_identity = (
            identity_before
            if identity_before is not None and identity_before == identity_after
            else None
        )

        if not raw:
            self._index_frames(b"")
            return

        # Detect and truncate an incomplete final frame.
        # A frame is complete iff it is followed by a newline byte.
        # After split on b"\n", the last element is b"" when raw ends with b"\n".
        if not raw.endswith(b"\n"):
            bytes_read = len(raw)
            last_nl = raw.rfind(b"\n")
            if last_nl < 0:
                # The entire content is one incomplete frame — truncate all.
                self._truncate_log_safe(b"", bytes_read=bytes_read)
                self._index_frames(b"")
                return
            complete_prefix = raw[: last_nl + 1]
            self._truncate_log_safe(complete_prefix, bytes_read=bytes_read)
            raw = complete_prefix

        self._index_frames(raw)

    def _index_frames(self, raw: bytes) -> None:
        """Rebuild every index from *raw*, a log prefix of complete frames.

        The new view is built aside and swapped in only when the whole prefix
        indexes cleanly, so a failure leaves the previous view untouched.
        Checksum or reference corruption raises ``EvidenceStoreError``.  A frame
        that reuses a transaction_id, receipt_id, or supersession_id already
        seen is skipped as a whole, so the first admitted record stays
        authoritative and the store still opens.
        """
        receipts: dict[str, dict] = {}
        by_criterion: dict[Any, list[str]] = {}
        supersessions: dict[str, dict] = {}
        superseded: set[str] = set()
        transactions: list[dict] = []
        seen_tx_ids: set[str] = set()
        for line in raw.split(b"\n"):
            if not line:
                continue
            try:
                frame = json.loads(line.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise EvidenceStoreError(
                    f"evidence log frame parse error: {exc}"
                ) from exc

            tx = frame.get("tx") if isinstance(frame, dict) else None
            records = frame.get("records", []) if isinstance(frame, dict) else None
            if (
                not isinstance(tx, dict)
                or not isinstance(records, list)
                or not all(isinstance(record, dict) for record in records)
            ):
                raise EvidenceStoreError(
                    "evidence log frame has invalid structure (tx or records is missing)"
                )

            # Verify checksum and record references — hard error on corruption.
            _verify_frame(tx, records)

            tx_id = tx.get("transaction_id", "")
            try:
                reused = tx_id in seen_tx_ids or any(
                    record.get("receipt_id") in receipts
                    or record.get("supersession_id") in supersessions
                    for record in records
                )
            except TypeError as exc:  # an unhashable identity
                raise EvidenceStoreError(
                    "evidence log frame holds a malformed record identity"
                ) from exc
            if reused:
                continue  # first-wins: a later reuse never replaces admitted evidence
            seen_tx_ids.add(tx_id)

            transactions.append(tx)
            try:
                for record in records:
                    _index_record(record, receipts, by_criterion, supersessions, superseded)
            except (AttributeError, TypeError, KeyError, ValueError) as exc:
                # A frame can carry a valid checksum yet a malformed record;
                # surface it as the one documented corruption error.
                raise EvidenceStoreError(
                    "evidence log frame holds a malformed record"
                ) from exc
        self._receipts = receipts
        self._receipts_by_criterion = by_criterion
        self._supersessions = supersessions
        self._superseded = superseded
        self._transactions = transactions
        self._log_size = len(raw)

    def _refresh_from_durable_log(self, current_size: int) -> None:
        """Re-read the log under the caller's advisory lock when another writer grew it.

        A log that no longer ends at a frame boundary needs recovery by
        reopening, so the append is refused rather than written after it.
        """
        if current_size == self._log_size:
            return
        fs = _file_safety()
        try:
            raw = fs.read_confined_regular_file(
                self._root, self._log_path, max_bytes=_EVIDENCE_LOG_MAX_BYTES
            )
        except (fs.UnsafeContentError, OSError) as exc:
            raise EvidenceStoreRefused(
                "denied-log-not-regular", "evidence log cannot be re-read safely"
            ) from exc
        if raw and not raw.endswith(b"\n"):
            raise EvidenceStoreRefused(
                "denied-log-needs-recovery",
                "evidence log ends in an incomplete frame; reopen the store to recover",
            )
        try:
            self._index_frames(raw)
        except EvidenceStoreError as exc:
            # The durable log is corrupt: keep the last consistent view and
            # refuse further appends until the store is reopened.
            self._poisoned = True
            raise EvidenceStoreRefused(
                "denied-log-corrupt",
                "evidence log failed verification on re-read; reopen the store",
            ) from exc

    def _decide_reuse(
        self,
        kind: str,
        record: dict,
        transaction_id: str,
        acceptance_fingerprint: str,
    ) -> tuple[str, dict | None]:
        """Decide whether an append is new, an idempotent retry, or a refused reuse.

        Returns ``("new", None)``, ``("idempotent", committed_tx)``, or
        ``(denial_code, None)``.  A retry is idempotent only when the committed
        transaction holds exactly this record under this acceptance fingerprint.
        """
        id_field = "receipt_id" if kind == "receipt" else "supersession_id"
        index = self._receipts if kind == "receipt" else self._supersessions
        record_id = record.get(id_field, "unknown")
        for prev_tx in self._transactions:
            if prev_tx.get("transaction_id") != transaction_id:
                continue
            prev_ids = prev_tx.get("ordered_record_ids", [])
            prev_record = index.get(prev_ids[0]) if len(prev_ids) == 1 else None
            if (
                prev_record is not None
                and _canonical_json(prev_record) == _canonical_json(record)
                and prev_tx.get("acceptance_fingerprint") == acceptance_fingerprint
            ):
                return "idempotent", prev_tx
            return "denied-duplicate-transaction-id", None
        if record_id in index:
            return f"denied-duplicate-{kind}-id", None
        return "new", None

    def _write_frame_once(
        self,
        kind: str,
        record: dict,
        tx: dict,
        frame_bytes: bytes,
        *,
        audit_sink: Callable[[Any], None],
        op_id: str,
    ) -> dict:
        """Append *frame_bytes* unless the durable log already decides the reuse.

        Under the advisory lock the log is re-read when another writer grew it,
        and the reuse decision is taken again; an idempotent retry then returns
        the committed transaction without writing.  Any refusal stores a denial
        sharing *op_id* with the allow event.
        """
        cm = _confined_mutation()
        transaction_id = tx["transaction_id"]
        acceptance_fp = tx.get("acceptance_fingerprint", "")

        def decide_and_write(current_size: int) -> dict | None:
            self._refresh_from_durable_log(current_size)
            decision, committed = self._decide_reuse(kind, record, transaction_id, acceptance_fp)
            if decision == "idempotent":
                return committed
            if decision != "new":
                raise EvidenceStoreRefused(
                    decision, f"{kind} or transaction identity already admitted"
                )
            cm.confined_append(self._root, self._log_path, frame_bytes)
            self._log_size += len(frame_bytes)
            return None

        try:
            if _HAS_FCNTL:
                with _advisory_lock(self._root, self._log_path) as lock_fd:
                    committed = decide_and_write(os.fstat(lock_fd).st_size)
            else:
                committed = decide_and_write(self._log_path.stat().st_size)
        except EvidenceStoreRefused as exc:
            _emit_post_allow_denial(audit_sink, op_id, exc.denial_code)
            raise
        except cm.MutationDenied as exc:
            if exc.denial_code == "denied-rollback-failed":
                self._poisoned = True
            denial_code = f"denied-append-failed-{exc.denial_code}"
            _emit_post_allow_denial(audit_sink, op_id, denial_code)
            raise EvidenceStoreRefused(
                denial_code,
                f"frame append failed: {exc.denial_code}",
            ) from exc
        if committed is not None:
            return committed
        self._transactions.append(tx)
        _index_record(
            record, self._receipts, self._receipts_by_criterion,
            self._supersessions, self._superseded,
        )
        return tx

    def _truncate_log(self, complete_bytes: bytes) -> None:
        """Replace the log with only the complete-frame prefix (recover to last complete frame).

        Used as a fallback when ``fcntl`` is unavailable.  Callers that can
        use the advisory lock should call ``_truncate_log_safe`` instead.
        """
        cm = _confined_mutation()
        try:
            cm.confined_atomic_replace(self._root, self._log_path, complete_bytes)
        except cm.MutationDenied as exc:
            raise EvidenceStoreError(
                f"cannot truncate evidence log: {exc.denial_code}"
            ) from exc

    def _truncate_log_safe(self, complete_bytes: bytes, *, bytes_read: int) -> None:
        """Truncate the log to complete_bytes, audited when open() was given a sink.

        The allow event is stored immediately before the truncation itself, so
        a skipped truncation stores none; a refused truncation stores a denial
        with the same operation ID.  An unavailable sink refuses the truncation.
        """
        sink = self._audit_sink
        if sink is None:
            self._truncate_log_unaudited(complete_bytes, bytes_read=bytes_read)
            return
        se = _security_events()
        operation_id = se.make_operation_id()

        def allow() -> None:
            try:
                se.emit_security_event(
                    sink, self._file_event(se, operation_id, "allowed", "allowed-file-write")
                )
            except Exception as exc:  # noqa: BLE001 — a sink failure from any module load
                raise EvidenceStoreRefused(
                    "denied-audit-sink-unavailable",
                    "audit sink unavailable; failing closed",
                ) from exc

        try:
            self._truncate_log_unaudited(
                complete_bytes, bytes_read=bytes_read, before_effect=allow
            )
        except EvidenceStoreError as exc:
            # An unavailable sink cannot store the denial either.
            if getattr(exc, "denial_code", None) != "denied-audit-sink-unavailable":
                se.emit_denial_best_effort(
                    sink, self._file_event(se, operation_id, "denied", "denied-staging-failed")
                )
            raise

    def _truncate_log_unaudited(
        self,
        complete_bytes: bytes,
        *,
        bytes_read: int,
        before_effect: Callable[[], None] = lambda: None,
    ) -> None:
        """Truncate the log to complete_bytes under an exclusive advisory lock.

        Acquires the lock, re-checks the file size, and truncates in-place
        with ``os.ftruncate`` only when the file has not grown since the
        caller read ``bytes_read`` bytes.  When the file has grown (a
        concurrent appender committed a new frame), the truncation is skipped
        to preserve that committed frame.

        Falls back to ``_truncate_log`` (atomic replace) when ``fcntl`` is
        unavailable so no committed frame is removed on those platforms either
        (best-effort; true serialisation requires the lock).
        """
        if self._log_identity is None:
            # The identity of the bytes read could not be bound, so the file at
            # the path cannot be shown to be the one read: never truncate it.
            raise EvidenceStoreError(
                "evidence log identity changed during recovery; refusing to truncate"
            )
        if not _HAS_FCNTL:
            # No advisory lock on this host: still refuse to replace a file that
            # is not the one that was read.
            if _regular_file_identity(self._log_path) != self._log_identity:
                raise EvidenceStoreError(
                    "evidence log identity changed during recovery; refusing to truncate"
                )
            before_effect()
            self._truncate_log(complete_bytes)
            return
        try:
            with _advisory_lock(
                self._root, self._log_path, expected_identity=self._log_identity
            ) as lock_fd:
                current_size = os.fstat(lock_fd).st_size
                if current_size > bytes_read:
                    # A concurrent appender committed a new frame; do not remove it.
                    return
                before_effect()
                os.ftruncate(lock_fd, len(complete_bytes))
        except OSError as exc:
            raise EvidenceStoreError(
                f"cannot truncate evidence log: {exc}"
            ) from exc

    # ── Append: receipts ───────────────────────────────────────────────────────

    def append_receipt(
        self,
        receipt: dict,
        *,
        transaction_id: str,
        issuer: object,
        grant: object,
        audit_sink: Callable[[Any], None],
    ) -> dict:
        """Append a receipt as a single-record transaction.

        Order of operations (authority verified and event emitted before any write):
          0. Idempotent-retry and duplicate-identity check (no side effects).
          1. Verify producer authority (emit security event before proceeding).
          1b. Post-allow duplicate checks: refuse a conflicting transaction_id
              or receipt_id via the post-allow denial path.
          2. Apply content-safety profile to the receipt bytes.
          3. Validate the receipt record structure.
          4. Apply content-safety profile to the transaction header bytes.
          5. Serialize and append the complete frame.
          6. Update in-memory indexes.

        Idempotent retry: a call with the same ``transaction_id`` and an
        identical ``receipt`` (by canonical JSON) produces no second frame and
        returns the previously committed transaction unchanged.

        Duplicate identity refusal: a different receipt that reuses an
        already-admitted ``receipt_id`` is refused with
        ``denied-duplicate-receipt-id``; a different receipt under an
        already-admitted ``transaction_id`` is refused with
        ``denied-duplicate-transaction-id``.  Both refusals use the post-allow
        denial path (the audit event shares ``op_id`` with the allow event).

        If any step before the filesystem write fails, no bytes are staged and
        the in-memory indexes are unchanged (all-or-none guarantee for
        single-record transactions).  If the write itself fails part-way, the
        append is rolled back by truncating to the pre-append file position.
        If the rollback also fails, the store is poisoned: it will refuse all
        further appends with ``denied-store-poisoned`` until reopened.

        Args:
            receipt:        A valid ``evidence-receipt.v1`` record dict.
            transaction_id: Stable unique identifier; a retry with the same ID
                            and identical record is idempotent.
            issuer:         ``CapabilityIssuer`` that owns the grant.
            grant:          ``CapabilityGrant`` with ``append`` in ``operations``.
            audit_sink:     Callable that accepts a ``SecurityEvent`` and stores it
                            durably. Unavailability fails closed.

        Returns:
            The committed ``semantic-evidence-transaction.v1`` record (existing
            transaction on idempotent retry, new transaction otherwise).

        Raises:
            EvidenceStoreRefused: on any refusal (stable denial_code).
            EvidenceStoreError: on I/O failure during the append.
        """
        if not self._opened:
            raise EvidenceStoreRefused(
                "denied-store-not-opened",
                "EvidenceStore.open() must be called before appending",
            )
        if self._poisoned:
            raise EvidenceStoreRefused(
                "denied-store-poisoned",
                "store is in a failed-closed state after a rollback error or a "
                "corrupt log; reopen to recover",
            )

        # Step 1: producer authority check, also for a retry.  Emits the allow
        # event before anything is acknowledged; its operation_id links any
        # post-allow denial to it.
        op_id = _check_producer_authority(
            issuer,
            grant,
            audit_sink=audit_sink,
            record_scope="evidence",
            required_operations=["append"],
        )

        # Step 1b: idempotent retry or refused reuse, against the in-memory view.
        # The decision is taken again against the durable log before writing.
        receipt_id = receipt.get("receipt_id", "unknown")
        acceptance_fp = receipt.get("acceptance_fingerprint", "")
        decision, committed = self._decide_reuse(
            "receipt", receipt, transaction_id, acceptance_fp
        )
        if decision == "idempotent" and committed is not None:
            return committed
        if decision != "new":
            _emit_post_allow_denial(audit_sink, op_id, decision)
            raise EvidenceStoreRefused(
                decision, "receipt or transaction identity already admitted"
            )

        # Step 2: content-safety check on the receipt.
        try:
            _check_record_safety(receipt, "evidence-receipt.v1", record_id=receipt_id)
        except EvidenceStoreRefused as exc:
            _emit_post_allow_denial(audit_sink, op_id, exc.denial_code)
            raise

        # Step 3: structural validation.
        ok, code = validate_receipt_dict(receipt)
        if not ok:
            denial_code = f"denied-invalid-receipt-{code}"
            _emit_post_allow_denial(audit_sink, op_id, denial_code)
            raise EvidenceStoreRefused(
                denial_code,
                f"receipt validation failed: {code}",
            )

        # Step 4: build transaction and apply content-safety to the header.
        records = [receipt]
        tx = _build_transaction(transaction_id, [receipt_id], acceptance_fp, records)
        try:
            _check_record_safety(
                tx, "semantic-evidence-transaction.v1", record_id=transaction_id
            )
        except EvidenceStoreRefused as exc:
            _emit_post_allow_denial(audit_sink, op_id, exc.denial_code)
            raise

        # Step 5: append the frame once, under the advisory lock, after the
        # reuse decision is retaken against the durable log.
        return self._write_frame_once(
            "receipt", receipt, tx, _serialize_frame(tx, records),
            audit_sink=audit_sink, op_id=op_id,
        )

    # ── Append: supersessions ──────────────────────────────────────────────────

    def append_supersession(
        self,
        supersession: dict,
        *,
        transaction_id: str,
        acceptance_fingerprint: str,
        issuer: object,
        grant: object,
        audit_sink: Callable[[Any], None],
    ) -> dict:
        """Append a supersession as a single-record transaction.

        Same authority, content-safety, idempotent-retry, and duplicate-identity
        guarantees as ``append_receipt``.

        Idempotent retry: a call with the same ``transaction_id`` and an
        identical ``supersession`` (by canonical JSON) produces no second frame
        and returns the previously committed transaction unchanged.

        Duplicate identity refusal: a different supersession that reuses an
        already-admitted ``supersession_id`` is refused with
        ``denied-duplicate-supersession-id``; a different supersession under an
        already-admitted ``transaction_id`` is refused with
        ``denied-duplicate-transaction-id``.  Both refusals use the post-allow
        denial path (the audit event shares ``op_id`` with the allow event).

        Args:
            supersession:          A valid ``evidence-supersession.v1`` record dict.
            transaction_id:        Stable unique identifier; a retry with the same ID
                                   and identical record is idempotent.
            acceptance_fingerprint: Acceptance fingerprint of the addressed subject.
            issuer:                ``CapabilityIssuer`` that owns the grant.
            grant:                 ``CapabilityGrant`` with ``append`` in ``operations``.
            audit_sink:            Callable that stores a ``SecurityEvent`` durably.

        Returns:
            The committed ``semantic-evidence-transaction.v1`` record (existing
            transaction on idempotent retry, new transaction otherwise).

        Raises:
            EvidenceStoreRefused: on any refusal (stable denial_code); a failed
                write is rolled back to the last complete frame.
            EvidenceStoreError: on I/O failure during the append.
        """
        if not self._opened:
            raise EvidenceStoreRefused(
                "denied-store-not-opened",
                "EvidenceStore.open() must be called before appending",
            )
        if self._poisoned:
            raise EvidenceStoreRefused(
                "denied-store-poisoned",
                "store is in a failed-closed state after a rollback error or a "
                "corrupt log; reopen to recover",
            )

        # Step 1: producer authority check, also for a retry.
        op_id = _check_producer_authority(
            issuer,
            grant,
            audit_sink=audit_sink,
            record_scope="evidence",
            required_operations=["append"],
        )

        # Step 1b: idempotent retry or refused reuse, against the in-memory view.
        sup_id = supersession.get("supersession_id", "unknown")
        decision, committed = self._decide_reuse(
            "supersession", supersession, transaction_id, acceptance_fingerprint
        )
        if decision == "idempotent" and committed is not None:
            return committed
        if decision != "new":
            _emit_post_allow_denial(audit_sink, op_id, decision)
            raise EvidenceStoreRefused(
                decision, "supersession or transaction identity already admitted"
            )

        # Step 2: content-safety check on the supersession.
        try:
            _check_record_safety(supersession, "evidence-supersession.v1", record_id=sup_id)
        except EvidenceStoreRefused as exc:
            _emit_post_allow_denial(audit_sink, op_id, exc.denial_code)
            raise

        # Step 3: structural validation.
        ok, code = validate_supersession_dict(supersession)
        if not ok:
            denial_code = f"denied-invalid-supersession-{code}"
            _emit_post_allow_denial(audit_sink, op_id, denial_code)
            raise EvidenceStoreRefused(
                denial_code,
                f"supersession validation failed: {code}",
            )

        # Step 4: build transaction and apply content-safety to the header.
        records = [supersession]
        tx = _build_transaction(transaction_id, [sup_id], acceptance_fingerprint, records)
        try:
            _check_record_safety(
                tx, "semantic-evidence-transaction.v1", record_id=transaction_id
            )
        except EvidenceStoreRefused as exc:
            _emit_post_allow_denial(audit_sink, op_id, exc.denial_code)
            raise

        # Step 5: append the frame once, under the advisory lock, after the
        # reuse decision is retaken against the durable log.
        return self._write_frame_once(
            "supersession", supersession, tx, _serialize_frame(tx, records),
            audit_sink=audit_sink, op_id=op_id,
        )

    # ── Read ───────────────────────────────────────────────────────────────────

    def get_active_receipts(self, criterion_ref: str) -> list[dict]:
        """Return active (non-superseded) receipts for *criterion_ref*, in insertion order.

        Superseded receipts are excluded by the store. Stale receipts (wrong
        acceptance_fingerprint) are filtered by the evaluator's freshness check.
        """
        return [
            self._receipts[rid]
            for rid in self._receipts_by_criterion.get(criterion_ref, ())
            if rid not in self._superseded
        ]

    def get_all_active_receipts(self) -> list[dict]:
        """Return all active (non-superseded) receipts in insertion order."""
        return [
            r
            for rid, r in self._receipts.items()
            if rid not in self._superseded
        ]

    def evaluate_verdicts(
        self,
        criteria: list[dict],
        current_acceptance_fingerprint: str,
        acc: object,
        *,
        adapter: str = "sequential-reference",
    ) -> list[dict]:
        """Evaluate verdicts for all criteria from stored active receipts.

        Measures from call entry to full verdict return. Uses in-memory indexes
        but they are disposable — rebuilding them yields the same verdicts
        (index deletion cannot change the verdict).

        Args:
            criteria:                     List of ``acceptance-property.v1`` dicts.
            current_acceptance_fingerprint: Acceptance fingerprint of the current subject.
            acc:                          The ``_acceptance`` module (or any module
                                          exposing ``evaluate_verdict``).
            adapter:                      Adapter label for the evaluator.

        Returns:
            A list of ``acceptance-verdict.v1`` dicts, one per criterion.
        """
        verdicts: list[dict] = []
        for prop in criteria:
            criterion_ref = prop.get("property_id", "")
            receipts = self.get_active_receipts(criterion_ref)
            v = acc.evaluate_verdict(  # type: ignore[union-attr]
                property_record=prop,
                receipts=receipts,
                current_acceptance_fingerprint=current_acceptance_fingerprint,
                adapter=adapter,
            )
            verdicts.append(v)
        return verdicts

    # ── Observable state ───────────────────────────────────────────────────────

    @property
    def transaction_count(self) -> int:
        """Number of committed transactions in the log."""
        return len(self._transactions)

    @property
    def receipt_count(self) -> int:
        """Total number of indexed receipts (including superseded)."""
        return len(self._receipts)

    @property
    def active_receipt_count(self) -> int:
        """Number of active (non-superseded) receipts."""
        return sum(1 for rid in self._receipts if rid not in self._superseded)

    @property
    def supersession_count(self) -> int:
        """Number of indexed supersessions."""
        return len(self._supersessions)
