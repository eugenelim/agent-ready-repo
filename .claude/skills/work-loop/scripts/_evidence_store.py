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
import copy
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
    "validate_semantic_record",
    "derive_review_failure_receipt_id",
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
_review_contracts_module: ModuleType | None = None
_policy_import_module: ModuleType | None = None


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


def _review_contracts() -> ModuleType:
    """Lazily load the sibling structured-review validator module."""
    global _review_contracts_module
    if _review_contracts_module is None:
        _review_contracts_module = _load_sibling(
            "_es_review_contracts", "_review_contracts.py"
        )
    return _review_contracts_module


def _policy_import() -> ModuleType:
    """Lazily load the sibling policy-import module for approval validation."""
    global _policy_import_module
    if _policy_import_module is None:
        _policy_import_module = _load_sibling("_es_policy_import", "_policy_import.py")
    return _policy_import_module


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
        # Fast key check for the common receipt/supersession cases to avoid
        # calling _semantic_record_id (which calls _semantic_record_kind) on
        # every replay frame.
        actual_id = (
            record.get("receipt_id")
            or record.get("supersession_id")
            or _semantic_record_id(record)
        )
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


def _is_identity(value: object) -> bool:
    """Return True when *value* is a non-empty string, as every record identity must be."""
    return isinstance(value, str) and bool(value)


def _is_schema_v1(value: object) -> bool:
    """Return True for the integer 1 only; a boolean is not a schema version."""
    return type(value) is int and value == 1


def _is_closed_string_object(
    value: object, required: frozenset[str], allowed: frozenset[str]
) -> bool:
    """Return True for a closed object of non-empty strings with every *required* key."""
    return (
        isinstance(value, dict)
        and required <= set(value)
        and set(value) <= allowed
        and all(_is_identity(v) for v in value.values())
    )


def validate_transaction_dict(d: object) -> tuple[bool, str]:
    """Validate a ``semantic-evidence-transaction.v1`` record dict in code.

    Returns ``(True, "ok")`` on success or ``(False, denial_code)`` on any failure.
    Failure codes are stable:
      denied-not-a-dict              — d is not a dict.
      denied-unknown-schema-version  — schema_version is not 1.
      denied-missing-required-field  — a required field is absent.
      denied-unknown-authority-field — a field not in the schema is present.
      denied-empty-ordered-record-ids — ordered_record_ids is empty.
      denied-invalid-identity        — transaction_id or an ordered_record_ids
                                       item is not a non-empty string.
      denied-invalid-field           — acceptance_fingerprint or checksum is not
                                       a non-empty string.
    """
    if not isinstance(d, dict):
        return False, "denied-not-a-dict"
    sv = d.get("schema_version")
    if not _is_schema_v1(sv):
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
    if not _is_identity(d.get("transaction_id")) or not all(_is_identity(o) for o in oids):
        return False, "denied-invalid-identity"
    if not _is_identity(d.get("acceptance_fingerprint")) or not _is_identity(d.get("checksum")):
        return False, "denied-invalid-field"
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
      denied-invalid-identity        — receipt_id is not a non-empty string.
      denied-invalid-field           — acceptance_fingerprint, outcome, or
                                       task_projection_revision is not a
                                       non-empty string.
    """
    if not isinstance(d, dict):
        return False, "denied-not-a-dict"
    sv = d.get("schema_version")
    if not _is_schema_v1(sv):
        return False, "denied-unknown-schema-version"
    for field in _RECEIPT_REQUIRED:
        if field not in d:
            return False, "denied-missing-required-field"
    unknown = set(d) - _RECEIPT_ALLOWED
    if unknown:
        return False, "denied-unknown-authority-field"
    if not _is_identity(d.get("receipt_id")):
        return False, "denied-invalid-identity"
    if not _is_identity(d.get("acceptance_fingerprint")) or not _is_identity(d.get("outcome")):
        return False, "denied-invalid-field"
    if "task_projection_revision" in d and not _is_identity(d["task_projection_revision"]):
        return False, "denied-invalid-field"
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
      denied-invalid-identity         — supersession_id or a superseded_receipt_ids
                                        item is not a non-empty string.
      denied-invalid-nested-field     — authority or provenance is not a closed
                                        object of non-empty string fields.
    """
    if not isinstance(d, dict):
        return False, "denied-not-a-dict"
    sv = d.get("schema_version")
    if not _is_schema_v1(sv):
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
    if not _is_identity(d.get("supersession_id")) or not all(_is_identity(s) for s in sids):
        return False, "denied-invalid-identity"
    if not _is_closed_string_object(
        d.get("authority"), frozenset({"identity", "role"}), frozenset({"identity", "role"})
    ) or not _is_closed_string_object(
        d.get("provenance"), frozenset({"reason_code"}), frozenset({"reason_code", "source_ref"})
    ):
        return False, "denied-invalid-nested-field"
    return True, "ok"


def _validate_review_record(record_type: str, record: object) -> tuple[bool, str]:
    """Validate a review-owned semantic record through the closed review registry."""
    return _review_contracts().validate_review_record_dict(record_type, record)


def _review_record_id(field: str) -> Callable[[dict], object]:
    """Return an identity extractor for a review-owned record."""
    return lambda record: record.get(field)


_SEMANTIC_RECORDS: Final[dict[str, dict[str, Any]]] = {
    "evidence-receipt.v1": {
        "detect": lambda record: "receipt_id" in record,
        "id": lambda record: record.get("receipt_id"),
        "validate": validate_receipt_dict,
        "profile": "evidence-receipt.v1",
    },
    "evidence-supersession.v1": {
        "detect": lambda record: "supersession_id" in record,
        "id": lambda record: record.get("supersession_id"),
        "validate": validate_supersession_dict,
        "profile": "evidence-supersession.v1",
    },
    "review-subject.v1": {
        "detect": lambda record: "review_subject_id" in record,
        "id": _review_record_id("review_subject_id"),
        "validate": lambda record: _validate_review_record("review-subject.v1", record),
        "profile": "review-subject.v1",
    },
    "review-obligation.v1": {
        "detect": lambda record: "obligation_id" in record,
        "id": _review_record_id("obligation_id"),
        "validate": lambda record: _validate_review_record("review-obligation.v1", record),
        "profile": "review-obligation.v1",
    },
    "review-report.v1": {
        "detect": lambda record: (
            "report_id" in record
            and "assessment_id" not in record
            and "finding_id" not in record
        ),
        "id": _review_record_id("report_id"),
        "validate": lambda record: _validate_review_record("review-report.v1", record),
        "profile": "review-report.v1",
    },
    "finding-assessment.v1": {
        "detect": lambda record: "assessment_id" in record and "disposition_id" not in record,
        "id": _review_record_id("assessment_id"),
        "validate": lambda record: _validate_review_record("finding-assessment.v1", record),
        "profile": "finding-assessment.v1",
    },
    "finding-disposition.v1": {
        "detect": lambda record: "disposition_id" in record,
        "id": _review_record_id("disposition_id"),
        "validate": lambda record: _validate_review_record("finding-disposition.v1", record),
        "profile": "finding-disposition.v1",
    },
    "approval-record.v1": {
        # Detected by the presence of approval_id; no other registered kind uses this field.
        "detect": lambda record: "approval_id" in record and "disposition_id" not in record,
        "id": lambda record: record.get("approval_id"),
        "validate": lambda record: _policy_import().validate_approval_dict(record),
        "profile": "approval-record.v1",
    },
    "finding.v1": {
        "detect": lambda record: (
            "finding_id" in record
            and "assessment_id" not in record
            and "disposition_id" not in record
            and "report_id" not in record
        ),
        "id": _review_record_id("finding_id"),
        "validate": lambda record: _validate_review_record("finding.v1", record),
        "profile": "finding.v1",
    },
}

_REVIEW_RECORD_TYPES: Final[frozenset[str]] = frozenset({
    "review-subject.v1",
    "review-obligation.v1",
    "review-report.v1",
    "finding.v1",
    "finding-assessment.v1",
    "finding-disposition.v1",
})

# Closed lifecycle kinds and their required key sets.
# A lifecycle dict must have exactly the keys in the matching set.
_LIFECYCLE_KIND_SHAPES: Final[dict[str, frozenset[str]]] = {
    "finding-assessment": frozenset({"kind", "report_id", "finding_id", "affected_criteria"}),
    "review-report": frozenset({"kind"}),
    "source-invalidation": frozenset({"kind", "report_id", "finding_id"}),
    # finding-disposition carries a pre-validated approval-record.v1 and the
    # current review-subject.v1 so the store can compose and validate under lock.
    "finding-disposition": frozenset({"kind", "approval_record", "review_subject"}),
}


def _semantic_record_kind(record: dict) -> str | None:
    """Return the single registered semantic record kind for *record*."""
    matches = [
        kind for kind, spec in _SEMANTIC_RECORDS.items()
        if spec["detect"](record)
    ]
    return matches[0] if len(matches) == 1 else None


def _semantic_record_id(record: dict) -> object:
    """Return the registered semantic record identity, or an empty identity."""
    kind = _semantic_record_kind(record)
    if kind is None:
        return ""
    return _SEMANTIC_RECORDS[kind]["id"](record)


def _semantic_record_key(record: dict) -> tuple[str, str] | None:
    """Return the typed semantic record key for a validated record."""
    kind = _semantic_record_kind(record)
    if kind is None:
        return None
    # Inline the id lookup to avoid a second _semantic_record_kind call inside
    # _semantic_record_id; this halves the detect-lambda work for callers that
    # only need the key (e.g. the replay deduplication check in _index_frames).
    record_id = _SEMANTIC_RECORDS[kind]["id"](record)
    if not _is_identity(record_id):
        return None
    return kind, str(record_id)


def _is_review_report(record: dict) -> bool:
    """Return true when a semantic record is a structured review report."""
    return _semantic_record_kind(record) == "review-report.v1"


def validate_semantic_record(record: object) -> tuple[bool, str]:
    """Validate a closed semantic evidence-store record."""
    if not isinstance(record, dict):
        return False, "denied-not-a-dict"
    kind = _semantic_record_kind(record)
    if kind is None:
        return False, "denied-unknown-record-kind"
    return _SEMANTIC_RECORDS[kind]["validate"](record)


def _review_record_content_safety(record_type: str, record: dict) -> tuple[bool, str]:
    """Run the review validator's content-safety path for replay-time checks."""
    return _review_contracts().validate_review_record_dict(record_type, record)


# ── Security and content-safety helpers ───────────────────────────────────────


def _check_record_safety(record: dict, record_type: str, *, record_id: str) -> None:
    """Apply the content-safety profile for ``record_type`` to the record's bytes.

    Raises ``EvidenceStoreRefused`` if the profile is missing, unknown, or the
    record does not pass the check. No payload bytes are retained on rejection.

    Every write boundary applies its named content-safety profile before persisting.
    """
    cs = _content_safety()
    profile = cs.SLICE_1_WRITER_BOUNDARIES.get(record_type)
    if profile is None and record_type in _SEMANTIC_RECORDS:
        with contextlib.suppress(Exception):
            profile = _review_contracts().REVIEW_WRITER_BOUNDARIES.get(record_type)
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


def _parse_verified_frame(line: bytes) -> tuple[dict, list[dict]]:
    """Parse one log line into a schema-valid, checksum-verified frame.

    The checksum is unkeyed, so a writer can recompute it over a malformed
    body; the transaction header and every record are therefore also checked
    against their schemas.  Any failure raises ``EvidenceStoreError``.
    """
    try:
        frame = json.loads(line.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise EvidenceStoreError(f"evidence log frame parse error: {exc}") from exc
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
    ok, code = validate_transaction_dict(tx)
    if not ok:
        raise EvidenceStoreError(f"evidence log frame header is invalid: {code}")
    # Note: no content-safety re-check on TX here — receipts and supersessions
    # are safety-checked on the write path; the checksum guarantees integrity on
    # replay.  Review-owned records are validated below (Slice 2 addition).
    for record in records:
        if "receipt_id" in record:
            # Fast path: receipt was content-safety-checked on write.  Schema
            # validation is sufficient here; skipping _check_record_safety avoids
            # re-running the regex engine for every receipt on cold rehydration.
            ok, code = validate_receipt_dict(record)
            if not ok:
                raise EvidenceStoreError(f"evidence log frame record is invalid: {code}")
        elif "supersession_id" in record:
            # Same fast path for supersessions.
            ok, code = validate_supersession_dict(record)
            if not ok:
                raise EvidenceStoreError(f"evidence log frame record is invalid: {code}")
        else:
            # Review-owned or approval record (new in Slice 2): full semantic
            # validation plus content-safety on replay to catch forged records.
            ok, code = validate_semantic_record(record)
            if not ok:
                raise EvidenceStoreError(f"evidence log frame record is invalid: {code}")
            record_kind = _semantic_record_kind(record)
            if record_kind in _REVIEW_RECORD_TYPES:
                ok, code = _review_record_content_safety(record_kind, record)
                if not ok:
                    raise EvidenceStoreError(f"evidence log frame record is invalid: {code}")
            elif record_kind is not None:
                try:
                    _check_record_safety(
                        record,
                        record_kind,
                        record_id=str(_semantic_record_id(record)),
                    )
                except EvidenceStoreRefused as exc:
                    raise EvidenceStoreError(
                        f"evidence log frame record is invalid: {exc.denial_code}"
                    ) from exc
    _verify_frame(tx, records)
    return tx, records


def _empty_semantic_indexes() -> dict[str, dict[str, dict]]:
    """Return an empty per-kind semantic record index."""
    return {kind: {} for kind in _SEMANTIC_RECORDS}


def _index_record(
    record: dict,
    receipts: dict[str, dict],
    by_criterion: dict[Any, list[str]],
    supersessions: dict[str, dict],
    superseded: set[str],
    semantic_records: dict[str, dict[str, dict]] | None = None,
) -> None:
    """Index one admitted receipt or supersession into the given maps.

    Shared by replay and the post-append update so both build the same view.
    """
    kind = _semantic_record_kind(record)
    if kind is not None and semantic_records is not None:
        # Inline the id lookup to avoid a second _semantic_record_kind call
        # inside _semantic_record_id; the detect-lambda table has O(n) entries.
        record_id = _SEMANTIC_RECORDS[kind]["id"](record)
        if _is_identity(record_id):
            semantic_records.setdefault(kind, {})[str(record_id)] = copy.deepcopy(record)
    if "receipt_id" in record:
        receipt_id = record["receipt_id"]
        criterion_ref = record.get("lineage", {}).get("criterion_ref")
        by_criterion.setdefault(criterion_ref, []).append(receipt_id)
        receipts[receipt_id] = record
    elif "supersession_id" in record:
        supersessions[record["supersession_id"]] = record
        superseded.update(record.get("superseded_receipt_ids", []))


def derive_review_failure_receipt_id(
    *,
    report_id: str,
    finding_id: str,
    assessment_id: str,
    criterion_ref: str,
    acceptance_fingerprint: str,
) -> str:
    """Return the deterministic bridge-owned receipt ID for a review failure."""
    payload = _canonical_json({
        "acceptance_fingerprint": acceptance_fingerprint,
        "assessment_id": assessment_id,
        "criterion_ref": criterion_ref,
        "finding_id": finding_id,
        "report_id": report_id,
    }).encode("utf-8")
    return "review-failure-sha256-" + hashlib.sha256(payload).hexdigest()


def _is_bridge_review_failure_receipt(record: dict) -> bool:
    """Return true for receipts owned by the Slice 2 review bridge."""
    return (
        _semantic_record_kind(record) == "evidence-receipt.v1"
        and record.get("selector", {}).get("term") == "supported-review-failure"
        and record.get("producer", {}).get("class") == "review-bridge"
    )


def _find_report_finding(
    semantic_records: dict[str, dict[str, dict]],
    report_id: str,
    finding_id: str,
) -> tuple[dict | None, dict | None]:
    """Return the source report and embedded finding for an assessment."""
    report = semantic_records.get("review-report.v1", {}).get(report_id)
    if not isinstance(report, dict):
        return None, None
    for finding in report.get("findings", []):
        if isinstance(finding, dict) and finding.get("finding_id") == finding_id:
            return report, finding
    return report, None


def _is_current_report(
    semantic_records: dict[str, dict[str, dict]],
    report: dict,
) -> bool:
    """Return true when *report* is the latest report in its role/subject group."""
    subject = report.get("subject", {})
    policy_fp = report.get("lineage", {}).get("review_policy_fingerprint")
    sequence = report.get("lineage", {}).get("sequence")
    for candidate in semantic_records.get("review-report.v1", {}).values():
        if (
            candidate.get("role") == report.get("role")
            and _canonical_json(candidate.get("subject")) == _canonical_json(subject)
            and candidate.get("lineage", {}).get("review_policy_fingerprint") == policy_fp
            and candidate.get("lineage", {}).get("sequence", 0) > sequence
        ):
            return False
    return True


def _active_bridge_receipts_for_source(
    semantic_records: dict[str, dict[str, dict]],
    receipts: dict[str, dict],
    superseded: set[str],
    *,
    report_id: str,
    finding_id: str,
) -> list[dict]:
    """Return active bridge receipts for a report/finding source."""
    found: list[dict] = []
    assessments = [
        record for record in semantic_records.get("finding-assessment.v1", {}).values()
        if record.get("report_id") == report_id
        and record.get("finding_id") == finding_id
        and record.get("assessment") == "supported"
    ]
    _report, finding = _find_report_finding(semantic_records, report_id, finding_id)
    criteria = finding.get("affected_acceptance_criteria", []) if finding else []
    for assessment in assessments:
        for receipt_id, receipt in receipts.items():
            if receipt_id in superseded or not _is_bridge_review_failure_receipt(receipt):
                continue
            expected_ids = {
                derive_review_failure_receipt_id(
                    report_id=report_id,
                    finding_id=finding_id,
                    assessment_id=assessment["assessment_id"],
                    criterion_ref=criterion,
                    acceptance_fingerprint=receipt.get("acceptance_fingerprint", ""),
                )
                for criterion in criteria
            }
            if receipt_id in expected_ids:
                found.append(receipt)
    return found


def _find_receipt_source(
    semantic_records: dict[str, dict[str, dict]],
    receipt: dict,
) -> tuple[str | None, str | None]:
    """Return (report_id, finding_id) for a bridge-owned receipt via its deriving assessment.

    Searches supported assessments to find one whose derived receipt ID matches
    the given receipt's receipt_id.  Returns (None, None) when no match is found.
    """
    receipt_id = receipt.get("receipt_id", "")
    acceptance_fp = receipt.get("acceptance_fingerprint", "")
    criterion_ref = receipt.get("lineage", {}).get("criterion_ref", "")
    for assessment in semantic_records.get("finding-assessment.v1", {}).values():
        if assessment.get("assessment") != "supported":
            continue
        report_id = assessment.get("report_id", "")
        finding_id = assessment.get("finding_id", "")
        assessment_id = assessment.get("assessment_id", "")
        expected = derive_review_failure_receipt_id(
            report_id=report_id,
            finding_id=finding_id,
            assessment_id=assessment_id,
            criterion_ref=criterion_ref,
            acceptance_fingerprint=acceptance_fp,
        )
        if expected == receipt_id:
            return report_id, finding_id
    return None, None


def _build_bridge_receipt(
    *,
    report_id: str,
    finding_id: str,
    assessment_id: str,
    criterion_ref: str,
    acceptance_fingerprint: str,
) -> dict:
    """Build one bridge-owned review-failure receipt record."""
    return {
        "schema_version": 1,
        "receipt_id": derive_review_failure_receipt_id(
            report_id=report_id,
            finding_id=finding_id,
            assessment_id=assessment_id,
            criterion_ref=criterion_ref,
            acceptance_fingerprint=acceptance_fingerprint,
        ),
        "acceptance_fingerprint": acceptance_fingerprint,
        "lineage": {"criterion_ref": criterion_ref},
        "selector": {"term": "supported-review-failure"},
        "freshness_mode": "exact-subject",
        "observation": {"type": "review-failure"},
        "outcome": "review-failure",
        "producer": {"class": "review-bridge", "identity": "structured-review-boundary"},
    }


def _build_bridge_supersession(supersession_id: str, receipt_ids: list[str]) -> dict:
    """Build a supersession for bridge-owned review-failure receipts."""
    return {
        "schema_version": 1,
        "supersession_id": supersession_id,
        "superseded_receipt_ids": receipt_ids,
        "authority": {"identity": "structured-review-boundary", "role": "review-bridge"},
        "provenance": {"reason_code": "review-assessment-superseded"},
    }


def _validate_review_transition(
    records: list[dict],
    *,
    acceptance_fingerprint: str,
    semantic_records: dict[str, dict[str, dict]],
    receipts: dict[str, dict],
    superseded: set[str],
    record_tx_index: dict[tuple[str, str], int] | None = None,
    current_tx_index: int = 0,
    check_disposition_rules: bool = False,
    lifecycle_review_subject: dict | None = None,
) -> None:
    """Validate assessment and receipt deltas against the current semantic view.

    When *check_disposition_rules* is True (lifecycle and replay paths),
    disposition records in *records* are validated against rules 1–5 and the
    decision-authority guards (decision approved, role match, unexpected
    replacement).  When False (raw semantic batch path), any frame containing a
    finding-disposition.v1 record is refused with the stable code
    ``denied-disposition-authority-required``.

    *lifecycle_review_subject*, when provided, is used for an unconditional
    Rule 4 check (approval fingerprints vs. the subject passed via the lifecycle
    dict).  On the replay path it is None and Rule 4 is conditional on the
    review subject being separately durable.
    """
    # Classify every record's semantic kind exactly once.  Multiple downstream
    # checks filter on kinds; sharing this list avoids re-running the full
    # detect-lambda table (O(#kinds) per record) on every record per check.
    kinds: list[str | None] = [_semantic_record_kind(r) for r in records]
    frame_dispositions: list[dict] = [
        r for r, k in zip(records, kinds, strict=True) if k == "finding-disposition.v1"
    ]
    frame_approvals: list[dict] = [
        r for r, k in zip(records, kinds, strict=True) if k == "approval-record.v1"
    ]
    # Approval authority gate: approval-record.v1 is only admitted inside a
    # finding-disposition lifecycle frame.  A raw batch or any frame that
    # carries an approval without a paired disposition is refused, and any
    # superseding approval must have the same authority role as its predecessor.
    if frame_approvals:
        if not check_disposition_rules:
            raise EvidenceStoreRefused(
                "denied-approval-authority-required",
                "approval-record records require the finding-disposition lifecycle; "
                "raw semantic batch path is not permitted for approvals",
            )
        if not frame_dispositions:
            raise EvidenceStoreRefused(
                "denied-approval-authority-required",
                "approval-record.v1 must be paired with a finding-disposition in the same frame",
            )
        # Supersession authority binding: the successor must have the same
        # authority role as the predecessor approval it names.
        for _succ in frame_approvals:
            _pred_id = _succ.get("lineage", {}).get("predecessor_id")
            if _pred_id:
                _pred = semantic_records.get("approval-record.v1", {}).get(_pred_id)
                if _pred is not None and (
                    _succ.get("authority", {}).get("role")
                    != _pred.get("authority", {}).get("role")
                ):
                    raise EvidenceStoreRefused(
                        "denied-approval-authority-role-mismatch",
                        "superseding approval must have same authority role as predecessor",
                    )
    if frame_dispositions:
        if not check_disposition_rules:
            raise EvidenceStoreRefused(
                "denied-disposition-authority-required",
                "finding-disposition records require the finding-disposition lifecycle; "
                "raw semantic batch path is not permitted for dispositions",
            )
        # Validate rules 1–5 for each disposition in this frame.
        # (frame_approvals is already defined above)
        for disposition in frame_dispositions:
            authority_ref = disposition.get("lineage", {}).get("authority_ref", "")
            # Find paired approval: either in this frame or already durable.
            approval: dict | None = next(
                (a for a in frame_approvals if a.get("approval_id") == authority_ref),
                None,
            )
            if approval is None:
                approval = semantic_records.get("approval-record.v1", {}).get(authority_ref)
            if approval is None:
                raise EvidenceStoreRefused(
                    "denied-disposition-no-approval",
                    "disposition authority_ref has no durable or in-frame approval record",
                )
            # Rule 1: approval scope
            if approval.get("decision_scope") != "review-disposition":
                raise EvidenceStoreRefused(
                    "denied-disposition-invalid-scope",
                    "approval decision_scope must be 'review-disposition'",
                )
            # Rule 2: authority_ref ↔ approval_id
            if authority_ref != approval.get("approval_id", ""):
                raise EvidenceStoreRefused(
                    "denied-disposition-authority-mismatch",
                    "disposition lineage.authority_ref must match approval_id",
                )
            # Rule 3: identity match
            maker_identity = disposition.get("decision_maker", {}).get("identity", "")
            if maker_identity != approval.get("authority", {}).get("identity", ""):
                raise EvidenceStoreRefused(
                    "denied-disposition-identity-mismatch",
                    "disposition decision_maker.identity must match approval authority.identity",
                )
            # G1: approval.decision must be "approved" — superseded approvals do not
            # authorize new dispositions.  Single owner: this guard is enforced here
            # (write path and replay) and in disposition_closes; the port no longer
            # duplicates it.
            if approval.get("decision") != "approved":
                raise EvidenceStoreRefused(
                    "denied-disposition-decision-not-approved",
                    "approval.decision must be 'approved'; got '"
                    + str(approval.get("decision")) + "'",
                )
            # G2: decision_maker role must match approval authority role.  Same
            # single-owner policy as G1.
            maker_role = disposition.get("decision_maker", {}).get("role", "")
            if maker_role != approval.get("authority", {}).get("role", ""):
                raise EvidenceStoreRefused(
                    "denied-disposition-role-mismatch",
                    "disposition decision_maker.role must match approval authority.role",
                )
            # Rule 4: subject fingerprint and policy fingerprint match.
            # When lifecycle_review_subject is supplied (live path), use it as the
            # authoritative subject even if review-subject.v1 is not separately
            # durable (it is not written by the persistence port in tests).
            disp_fp = disposition.get("review_subject_fingerprint", "")
            durable_subject = next(
                (
                    s for s in semantic_records.get("review-subject.v1", {}).values()
                    if s.get("review_subject_fingerprint") == disp_fp
                ),
                None,
            )
            effective_subject: dict | None = durable_subject
            if lifecycle_review_subject is not None:
                if lifecycle_review_subject.get("review_subject_fingerprint") != disp_fp:
                    # The live lifecycle subject fingerprint differs from the disposition.
                    # Refuse immediately rather than silently skipping Rule 4.
                    raise EvidenceStoreRefused(
                        "denied-disposition-subject-mismatch",
                        "lifecycle review_subject fingerprint must match "
                        "review_subject_fingerprint in the disposition",
                    )
                if effective_subject is None:
                    # Use the lifecycle subject only when its fingerprint matches the
                    # disposition, so we never compare fingerprints across subjects.
                    effective_subject = lifecycle_review_subject
            # Manifest_ref check is unconditional on both the live path and replay so
            # that a frame with a forged manifest_ref is always refused.
            if approval.get("base", {}).get("manifest_ref", "") != disp_fp:
                raise EvidenceStoreRefused(
                    "denied-disposition-subject-mismatch",
                    "approval base.manifest_ref must match review_subject_fingerprint",
                )
            if effective_subject is not None and approval.get(
                "spec_policy_fingerprint", ""
            ) != effective_subject.get("review_policy_fingerprint", ""):
                raise EvidenceStoreRefused(
                    "denied-disposition-policy-mismatch",
                    "approval spec_policy_fingerprint must match subject policy fingerprint",
                )
            # G3: only fixed-by may carry replacement_report_id.  An accept-risk or
            # repair-request that includes this field is structurally invalid.
            disp_kind = disposition.get("disposition", "")
            if disp_kind != "fixed-by" and disposition.get("replacement_report_id"):
                raise EvidenceStoreRefused(
                    "denied-disposition-unexpected-replacement",
                    "only fixed-by dispositions may carry replacement_report_id; '"
                    + disp_kind + "' must not include it",
                )
            # Rule 5: fixed-by replacement must be durable with a different subject
            if disposition.get("disposition") == "fixed-by":
                replacement_id = disposition.get("replacement_report_id", "")
                if not replacement_id:
                    raise EvidenceStoreRefused(
                        "denied-disposition-missing-replacement",
                        "fixed-by disposition requires a non-empty replacement_report_id",
                    )
                replacement = semantic_records.get("review-report.v1", {}).get(replacement_id)
                if replacement is None:
                    raise EvidenceStoreRefused(
                        "denied-disposition-replacement-not-durable",
                        "fixed-by replacement_report_id is not durable at this log position",
                    )
                replacement_fp = replacement.get("subject", {}).get(
                    "review_subject_fingerprint", ""
                )
                if replacement_fp == disp_fp:
                    raise EvidenceStoreRefused(
                        "denied-disposition-replacement-same-subject",
                        "fixed-by replacement report must have a different subject fingerprint",
                    )
            # Eligibility: the referenced assessment must be durable, supported,
            # bound to the same subject, and its source finding must be material
            # and present in the source report.  Single owner: these guards run on
            # the write path and replay; the port no longer duplicates them.
            assessment_id = disposition.get("assessment_id", "")
            target_assessment = semantic_records.get("finding-assessment.v1", {}).get(
                assessment_id
            )
            if target_assessment is None:
                raise EvidenceStoreRefused(
                    "denied-disposition-no-assessment",
                    "disposition assessment_id is not durable at this log position",
                )
            if target_assessment.get("assessment") != "supported":
                raise EvidenceStoreRefused(
                    "denied-disposition-not-supported",
                    "disposition requires a 'supported' assessment; found '"
                    + str(target_assessment.get("assessment")) + "'",
                )
            if target_assessment.get("review_subject_fingerprint") != disp_fp:
                raise EvidenceStoreRefused(
                    "denied-disposition-subject-mismatch",
                    "assessment review_subject_fingerprint must match disposition "
                    "subject fingerprint",
                )
            source_report_id = target_assessment.get("report_id", "")
            source_report = semantic_records.get("review-report.v1", {}).get(source_report_id)
            if source_report is None:
                raise EvidenceStoreRefused(
                    "denied-disposition-no-report",
                    "assessment source report is not durable at this log position",
                )
            source_finding = next(
                (
                    f for f in source_report.get("findings", [])
                    if f.get("finding_id") == disposition.get("finding_id", "")
                ),
                None,
            )
            if source_finding is None:
                raise EvidenceStoreRefused(
                    "denied-disposition-no-finding",
                    "disposition finding_id is not in the assessment's source report",
                )
            if not source_finding.get("material", False):
                raise EvidenceStoreRefused(
                    "denied-disposition-not-material",
                    "only material findings require disposition; this finding is not material",
                )

    # Reuse the pre-computed kinds to avoid re-running the detect-lambda table.
    assessments = [r for r, k in zip(records, kinds, strict=True) if k == "finding-assessment.v1"]
    # Bridge review-failure receipts: kind is "evidence-receipt.v1" plus two
    # field checks that together match _is_bridge_review_failure_receipt.
    frame_receipts = [
        r for r, k in zip(records, kinds, strict=True)
        if k == "evidence-receipt.v1"
        and r.get("selector", {}).get("term") == "supported-review-failure"
        and r.get("producer", {}).get("class") == "review-bridge"
    ]
    frame_superseded: set[str] = set()
    for r, k in zip(records, kinds, strict=True):
        if k == "evidence-supersession.v1":
            frame_superseded.update(r.get("superseded_receipt_ids", []))

    if frame_receipts and not assessments:
        raise EvidenceStoreRefused(
            "denied-incomplete-review-assessment-delta",
            "bridge-owned receipts require a paired assessment",
        )

    bridge_superseded = [
        receipt_id for receipt_id in frame_superseded
        if receipt_id in receipts and _is_bridge_review_failure_receipt(receipts[receipt_id])
    ]
    frame_reports = [r for r, k in zip(records, kinds, strict=True) if k == "review-report.v1"]
    if bridge_superseded:
        frame_subjects = [
            r for r, k in zip(records, kinds, strict=True) if k == "review-subject.v1"
        ]
        # Universal per-receipt justification: every superseded bridge-owned receipt
        # must be justified by (a) an in-frame assessment for the same source
        # (report_id, finding_id), (b) an in-frame report that replaces the same
        # (role, subject, policy) group tip as the source report, or (c) subject-
        # invalidation context: same delivery entity but different fingerprint/policy,
        # either in the current frame or durable and admitted after the source report.
        for sup_receipt_id in bridge_superseded:
            sup_receipt = receipts[sup_receipt_id]
            src_report_id, src_finding_id = _find_receipt_source(semantic_records, sup_receipt)
            if src_report_id is None:
                raise EvidenceStoreRefused(
                    "denied-incomplete-review-assessment-delta",
                    "bridge supersession requires source lifecycle context",
                )
            source_report = semantic_records.get("review-report.v1", {}).get(src_report_id)
            if source_report is None:
                raise EvidenceStoreRefused(
                    "denied-incomplete-review-assessment-delta",
                    "bridge supersession requires source lifecycle context",
                )
            # (a) in-frame assessment for the same (report_id, finding_id)
            if any(
                a.get("report_id") == src_report_id and a.get("finding_id") == src_finding_id
                for a in assessments
            ):
                continue
            # (b) in-frame report replacing the same (role, subject, policy) group tip
            src_subject_json = _canonical_json(source_report.get("subject"))
            src_report_policy = source_report.get("lineage", {}).get("review_policy_fingerprint")
            src_role = source_report.get("role")
            if any(
                r.get("role") == src_role
                and _canonical_json(r.get("subject")) == src_subject_json
                and r.get("lineage", {}).get("review_policy_fingerprint") == src_report_policy
                for r in frame_reports
            ):
                continue
            # (c) subject-invalidation context: invalidating subject with same delivery
            # entity but different fingerprint/policy, either in the frame or durable
            # and admitted after the source report.
            source_subject = source_report.get("subject", {})
            src_delivery_id = (
                source_subject.get("delivery_subject_ref", {}).get("subject_id")
            )
            src_fp = source_subject.get("review_subject_fingerprint")
            src_policy_fp = source_subject.get("review_policy_fingerprint")
            src_report_tx_idx = (
                record_tx_index.get(("review-report.v1", src_report_id), -1)
                if record_tx_index is not None
                else -1
            )
            valid_subject = False
            for subj in frame_subjects:
                if subj.get("delivery_subject_ref", {}).get("subject_id") == src_delivery_id and (
                    subj.get("review_subject_fingerprint") != src_fp
                    or subj.get("review_policy_fingerprint") != src_policy_fp
                ):
                    valid_subject = True
                    break
            if not valid_subject and record_tx_index is not None:
                for subj_id, subj in semantic_records.get("review-subject.v1", {}).items():
                    subj_tx_idx = record_tx_index.get(("review-subject.v1", subj_id), -1)
                    if (
                        subj_tx_idx > src_report_tx_idx
                        and subj.get("delivery_subject_ref", {}).get("subject_id")
                        == src_delivery_id
                        and (
                            subj.get("review_subject_fingerprint") != src_fp
                            or subj.get("review_policy_fingerprint") != src_policy_fp
                        )
                    ):
                        valid_subject = True
                        break
            if not valid_subject:
                raise EvidenceStoreRefused(
                    "denied-incomplete-review-assessment-delta",
                    "bridge supersession requires source lifecycle context",
                )

    seen_assessment_sources: set[tuple[str, str]] = set()
    for assessment in assessments:
        source = (assessment.get("report_id", ""), assessment.get("finding_id", ""))
        if source in seen_assessment_sources:
            raise EvidenceStoreRefused(
                "denied-ambiguous-review-assessment-batch",
                "batch contains multiple assessments for one report and finding",
            )
        seen_assessment_sources.add(source)

    for report in frame_reports:
        subject = report.get("subject", {})
        policy_fp = report.get("lineage", {}).get("review_policy_fingerprint")
        for previous in semantic_records.get("review-report.v1", {}).values():
            if (
                previous.get("role") != report.get("role")
                or _canonical_json(previous.get("subject")) != _canonical_json(subject)
                or previous.get("lineage", {}).get("review_policy_fingerprint") != policy_fp
            ):
                continue
            for finding in previous.get("findings", []):
                active = _active_bridge_receipts_for_source(
                    semantic_records,
                    receipts,
                    superseded,
                    report_id=previous["report_id"],
                    finding_id=finding.get("finding_id", ""),
                )
                old_ids = [receipt["receipt_id"] for receipt in active]
                if any(receipt_id not in frame_superseded for receipt_id in old_ids):
                    raise EvidenceStoreRefused(
                        "denied-incomplete-review-assessment-delta",
                        "report replacement must supersede old review-failure receipts",
                    )

    if not assessments:
        return

    for assessment in assessments:
        report_id = assessment["report_id"]
        finding_id = assessment["finding_id"]
        assessment_id = assessment["assessment_id"]
        report, finding = _find_report_finding(semantic_records, report_id, finding_id)
        if report is None or finding is None:
            raise EvidenceStoreRefused(
                "denied-incomplete-review-assessment-delta",
                "assessment source report and finding must already be durable",
            )
        # R4: assessment subject fingerprint must match the source report's subject.
        # An assessment written against a report from a different subject cannot
        # be used as evidence for a disposition against the claimed subject.
        report_subject_fp = report.get("subject", {}).get("review_subject_fingerprint", "")
        if assessment.get("review_subject_fingerprint", "") != report_subject_fp:
            raise EvidenceStoreRefused(
                "denied-incomplete-review-assessment-delta",
                "assessment review_subject_fingerprint must match the source report subject",
            )
        if not _is_current_report(semantic_records, report):
            raise EvidenceStoreRefused(
                "denied-incomplete-review-assessment-delta",
                "assessment source report is not current",
            )
        active_source_receipts = _active_bridge_receipts_for_source(
            semantic_records, receipts, superseded,
            report_id=report_id,
            finding_id=finding_id,
        )
        if assessment["assessment"] == "supported":
            criteria = finding.get("affected_acceptance_criteria", [])
            expected_ids = {
                derive_review_failure_receipt_id(
                    report_id=report_id,
                    finding_id=finding_id,
                    assessment_id=assessment_id,
                    criterion_ref=criterion,
                    acceptance_fingerprint=acceptance_fingerprint,
                )
                for criterion in criteria
            }
            actual_ids = {record.get("receipt_id") for record in frame_receipts}
            if not expected_ids or not expected_ids <= actual_ids:
                raise EvidenceStoreRefused(
                    "denied-incomplete-review-assessment-delta",
                    "supported assessment must include every review-failure receipt",
                )
            for receipt in frame_receipts:
                if receipt.get("receipt_id") not in expected_ids:
                    continue
                if (
                    receipt.get("acceptance_fingerprint") != acceptance_fingerprint
                    or receipt.get("outcome") != "review-failure"
                    or receipt.get("observation", {}).get("type") != "review-failure"
                    or receipt.get("freshness_mode") != "exact-subject"
                    or receipt.get("selector", {}).get("term") != "supported-review-failure"
                    or receipt.get("producer", {}).get("class") != "review-bridge"
                    or receipt.get("lineage", {}).get("criterion_ref") not in criteria
                ):
                    raise EvidenceStoreRefused(
                        "denied-incomplete-review-assessment-delta",
                        "review-failure receipt does not match its assessment",
                    )
            old_ids = [
                receipt["receipt_id"]
                for receipt in active_source_receipts
                if receipt["receipt_id"] not in expected_ids
            ]
            if any(receipt_id not in frame_superseded for receipt_id in old_ids):
                raise EvidenceStoreRefused(
                    "denied-incomplete-review-assessment-delta",
                    "replacement assessment must supersede old review-failure receipts",
                )
        else:
            old_ids = [receipt["receipt_id"] for receipt in active_source_receipts]
            if any(receipt_id not in frame_superseded for receipt_id in old_ids):
                raise EvidenceStoreRefused(
                    "denied-incomplete-review-assessment-delta",
                    "unsupported assessment must supersede derived receipts",
                )


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
        self._semantic_records: dict[str, dict[str, dict]] = _empty_semantic_indexes()
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
        # (kind, record_id) -> 0-based transaction index; built identically by
        # replay (_index_frames) and live appends; used by _validate_review_transition
        # to enforce "durable later" ordering for invalidation context checks.
        self._semantic_tx_index: dict[tuple[str, str], int] = {}

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
        semantic_records = _empty_semantic_indexes()
        transactions: list[dict] = []
        seen_tx_ids: set[str] = set()
        seen_record_keys: set[tuple[str, str]] = set()
        semantic_tx_index: dict[tuple[str, str], int] = {}
        for line in raw.split(b"\n"):
            if not line:
                continue
            try:
                tx, records = _parse_verified_frame(line)
                tx_id = tx["transaction_id"]
                record_keys = [_semantic_record_key(record) for record in records]
                reused = (
                    tx_id in seen_tx_ids
                    or any(record_key is None for record_key in record_keys)
                    or len(record_keys) != len(set(record_keys))
                    or any(record_key in seen_record_keys for record_key in record_keys)
                )
                if reused:
                    continue  # first-wins: a later reuse never replaces admitted evidence
                try:
                    _validate_review_transition(
                        records,
                        acceptance_fingerprint=tx["acceptance_fingerprint"],
                        semantic_records=semantic_records,
                        receipts=receipts,
                        superseded=superseded,
                        record_tx_index=semantic_tx_index,
                        current_tx_index=len(transactions),
                        # Replay always permits disposition frames — they were admitted
                        # via the lifecycle port, and rules 1–5 are re-validated here.
                        check_disposition_rules=True,
                    )
                except EvidenceStoreRefused as exc:
                    raise EvidenceStoreError(
                        f"evidence log frame record is invalid: {exc.denial_code}"
                    ) from exc
                seen_tx_ids.add(tx_id)
                seen_record_keys.update(record_key for record_key in record_keys if record_key)
                tx_idx = len(transactions)
                transactions.append(tx)
                for record in records:
                    _index_record(
                        record,
                        receipts,
                        by_criterion,
                        supersessions,
                        superseded,
                        semantic_records,
                    )
                # Reuse the already-computed record_keys to build the
                # semantic_tx_index without re-calling _semantic_record_kind.
                for rkey in record_keys:
                    if rkey is not None:
                        semantic_tx_index.setdefault(rkey, tx_idx)
            except EvidenceStoreError:
                raise
            except Exception as exc:  # noqa: BLE001 - any fault in a frame is corruption
                # Corrupt bytes can fail anywhere (an over-long integer, deep
                # nesting, a malformed field behind a recomputed checksum);
                # every such fault surfaces as the one documented error.
                raise EvidenceStoreError("evidence log frame is malformed") from exc
        self._receipts = receipts
        self._receipts_by_criterion = by_criterion
        self._supersessions = supersessions
        self._superseded = superseded
        self._semantic_records = semantic_records
        self._transactions = transactions
        self._log_size = len(raw)
        self._semantic_tx_index = semantic_tx_index

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
        records: dict | list[dict],
        transaction_id: str,
        acceptance_fingerprint: str,
    ) -> tuple[str, dict | None]:
        """Decide whether an append is new, an idempotent retry, or a refused reuse.

        Returns ``("new", None)``, ``("idempotent", committed_tx)``, or
        ``(denial_code, None)``.  A retry is idempotent only when the committed
        transaction holds exactly this record under this acceptance fingerprint.
        """
        batch = records if isinstance(records, list) else [records]
        if kind == "receipt":
            record_keys = [("evidence-receipt.v1", record.get("receipt_id")) for record in batch]
        elif kind == "supersession":
            record_keys = [
                ("evidence-supersession.v1", record.get("supersession_id"))
                for record in batch
            ]
        else:
            record_keys = [_semantic_record_key(record) for record in batch]
        for index, record_key in enumerate(record_keys):
            if record_key is None or not _is_identity(record_key[1]):
                if kind in {"receipt", "supersession"}:
                    return f"denied-invalid-{kind}-denied-invalid-identity", None
                return "denied-invalid-review-record-denied-invalid-identity", None
            for later_key in record_keys[index + 1:]:
                if later_key == record_key:
                    return "denied-duplicate-record-id", None
        if not _is_identity(transaction_id):
            return "denied-invalid-transaction-denied-invalid-identity", None
        for prev_tx in self._transactions:
            if prev_tx.get("transaction_id") != transaction_id:
                continue
            prev_ids = prev_tx.get("ordered_record_ids", [])
            prev_records = [
                self._find_semantic_record_by_current_kind(record)
                for record in batch
            ]
            if (
                len(prev_ids) == len(record_keys)
                and all(prev_record is not None for prev_record in prev_records)
                and self._records_match_idempotent(prev_records, batch)
                and prev_tx.get("ordered_record_ids") == [
                    str(_semantic_record_id(record)) for record in batch
                ]
                and prev_tx.get("checksum") == _compute_frame_checksum(
                    {k: v for k, v in prev_tx.items() if k != "checksum"},
                    self._normalize_retry_records(prev_records, batch),
                )
                and prev_tx.get("acceptance_fingerprint") == acceptance_fingerprint
            ):
                return "idempotent", prev_tx
            return "denied-duplicate-transaction-id", None
        for record, record_key in zip(batch, record_keys, strict=True):
            record_kind = (
                record_key[0] if record_key is not None else _semantic_record_kind(record)
            )
            if (
                record_kind is not None
                and record_key is not None
                and record_key[1] in self._semantic_records.get(record_kind, {})
            ):
                if kind in {"receipt", "supersession"}:
                    return f"denied-duplicate-{kind}-id", None
                return "denied-duplicate-review-record-id", None
        return "new", None

    @staticmethod
    def _records_match_idempotent(prev_records: list[dict | None], batch: list[dict]) -> bool:
        """Return true when a retry carries the same semantic records."""
        normalized = EvidenceStore._normalize_retry_records(prev_records, batch)
        if len(normalized) != len(batch):
            return False
        return [_canonical_json(record) for record in prev_records] == [
            _canonical_json(record) for record in normalized
        ]

    @staticmethod
    def _normalize_retry_records(prev_records: list[dict | None], batch: list[dict]) -> list[dict]:
        """Align only port-owned retry fields against committed records."""
        normalized: list[dict] = []
        for prev_record, record in zip(prev_records, batch, strict=True):
            if prev_record is None:
                return []
            candidate = copy.deepcopy(record)
            if _is_review_report(prev_record) and _is_review_report(candidate):
                candidate["lineage"]["sequence"] = prev_record["lineage"]["sequence"]
                if "previous_report_id" in prev_record["lineage"]:
                    candidate["lineage"]["previous_report_id"] = (
                        prev_record["lineage"]["previous_report_id"]
                    )
                else:
                    candidate["lineage"].pop("previous_report_id", None)
            normalized.append(candidate)
        return normalized

    def _find_semantic_record_by_current_kind(self, record: dict) -> dict | None:
        """Return a deep-copied semantic record by the candidate's typed key."""
        key = _semantic_record_key(record)
        if key is None:
            return None
        found = self._semantic_records.get(key[0], {}).get(key[1])
        return copy.deepcopy(found) if found is not None else None

    @staticmethod
    def _refuse_invalid_header(
        tx: dict, *, audit_sink: Callable[[Any], None], op_id: str
    ) -> None:
        """Refuse a transaction header replay would reject, before any byte is staged.

        Append and replay share the validators, so the store never writes a
        frame it cannot reopen.
        """
        ok, code = validate_transaction_dict(tx)
        if not ok:
            denial_code = f"denied-invalid-transaction-{code}"
            _emit_post_allow_denial(audit_sink, op_id, denial_code)
            raise EvidenceStoreRefused(denial_code, f"transaction header is invalid: {code}")

    def _write_frame_once(
        self,
        kind: str,
        records: list[dict],
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
            decision, committed = self._decide_reuse(kind, records, transaction_id, acceptance_fp)
            if decision == "idempotent":
                return committed
            if decision != "new":
                raise EvidenceStoreRefused(
                    decision, f"{kind} or transaction identity already admitted"
                )
            # Enforce assessment/receipt delta rules on the single-record path
            # (same checker as replay and the semantic-batch path).
            _validate_review_transition(
                records,
                acceptance_fingerprint=acceptance_fp,
                semantic_records=self._semantic_records,
                receipts=self._receipts,
                superseded=self._superseded,
                record_tx_index=self._semantic_tx_index,
                current_tx_index=len(self._transactions),
            )
            if self._log_size + len(frame_bytes) > _EVIDENCE_LOG_MAX_BYTES:
                raise EvidenceStoreRefused(
                    "denied-log-size-limit",
                    "appending this frame would take the log past the size replay accepts",
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
        tx_idx = len(self._transactions)
        self._transactions.append(tx)
        for record in records:
            _index_record(
                record,
                self._receipts,
                self._receipts_by_criterion,
                self._supersessions,
                self._superseded,
                self._semantic_records,
            )
        for record in records:
            kind_r = _semantic_record_kind(record)
            if kind_r is not None:
                rid = _semantic_record_id(record)
                if rid is not None:
                    self._semantic_tx_index.setdefault((kind_r, str(rid)), tx_idx)
        return tx

    def _normalize_semantic_records_for_commit(self, records: list[dict]) -> list[dict]:
        """Assign commit-time fields that depend on the refreshed durable view."""
        normalized = copy.deepcopy(records)
        new_report_groups: set[tuple[str, str, str]] = set()
        for record in normalized:
            if not _is_review_report(record):
                continue
            subject = record["subject"]
            lineage = record["lineage"]
            policy_fp = lineage["review_policy_fingerprint"]
            group = (
                record["role"],
                subject["review_subject_fingerprint"],
                policy_fp,
            )
            if group in new_report_groups:
                raise EvidenceStoreRefused(
                    "denied-ambiguous-review-report-batch",
                    "batch contains multiple new reports for one role and subject",
                )
            new_report_groups.add(group)
            if policy_fp != subject["review_policy_fingerprint"]:
                raise EvidenceStoreRefused(
                    "denied-review-policy-mismatch",
                    "review report policy does not match its subject",
                )
            reports = [
                stored
                for stored in self._semantic_records.get("review-report.v1", {}).values()
                if stored.get("role") == record.get("role")
                and _canonical_json(stored.get("subject")) == _canonical_json(subject)
                and stored.get("lineage", {}).get("review_policy_fingerprint") == policy_fp
            ]
            current, code = _review_contracts().select_current_report(
                copy.deepcopy(reports),
                role=record["role"],
                review_subject_fingerprint=subject["review_subject_fingerprint"],
                review_policy_fingerprint=policy_fp,
            )
            if current is None and code != "denied-no-current-report":
                raise EvidenceStoreRefused(code, "current review report lineage is not safe")
            lineage["sequence"] = 1 if current is None else current["lineage"]["sequence"] + 1
            if current is None:
                lineage.pop("previous_report_id", None)
            else:
                lineage["previous_report_id"] = current["report_id"]
        return normalized

    def _write_semantic_frame_once(
        self,
        records: list[dict],
        transaction_id: str,
        acceptance_fingerprint: str,
        *,
        audit_sink: Callable[[Any], None],
        op_id: str,
    ) -> dict:
        """Normalize, serialize, and append a semantic batch under the store lock."""
        cm = _confined_mutation()

        def decide_and_write(current_size: int) -> tuple[dict | None, list[dict] | None]:
            self._refresh_from_durable_log(current_size)
            normalized = self._normalize_semantic_records_for_commit(records)
            record_ids = [str(_semantic_record_id(record)) for record in normalized]
            decision, committed = self._decide_reuse(
                "semantic", normalized, transaction_id, acceptance_fingerprint
            )
            if decision == "idempotent":
                return committed, None
            if decision != "new":
                raise EvidenceStoreRefused(
                    decision, "semantic record or transaction identity already admitted"
                )
            for record, record_id in zip(normalized, record_ids, strict=True):
                record_kind = _semantic_record_kind(record)
                if record_kind is None:
                    raise EvidenceStoreRefused(
                        "denied-unknown-record-kind", "unknown semantic record kind"
                    )
                _check_record_safety(
                    record,
                    _SEMANTIC_RECORDS[record_kind]["profile"],
                    record_id=record_id,
                )
            tx = _build_transaction(
                transaction_id,
                record_ids,
                acceptance_fingerprint,
                normalized,
            )
            self._refuse_invalid_header(tx, audit_sink=audit_sink, op_id=op_id)
            _check_record_safety(
                tx, "semantic-evidence-transaction.v1", record_id=transaction_id
            )
            _validate_review_transition(
                normalized,
                acceptance_fingerprint=acceptance_fingerprint,
                semantic_records=self._semantic_records,
                receipts=self._receipts,
                superseded=self._superseded,
                record_tx_index=self._semantic_tx_index,
                current_tx_index=len(self._transactions),
            )
            frame_bytes = _serialize_frame(tx, normalized)
            if self._log_size + len(frame_bytes) > _EVIDENCE_LOG_MAX_BYTES:
                raise EvidenceStoreRefused(
                    "denied-log-size-limit",
                    "appending this frame would take the log past the size replay accepts",
                )
            cm.confined_append(self._root, self._log_path, frame_bytes)
            self._log_size += len(frame_bytes)
            return tx, normalized

        try:
            if _HAS_FCNTL:
                with _advisory_lock(self._root, self._log_path) as lock_fd:
                    committed, committed_records = decide_and_write(os.fstat(lock_fd).st_size)
            else:
                committed, committed_records = decide_and_write(self._log_path.stat().st_size)
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
        if committed_records is None:
            if committed is None:
                raise EvidenceStoreError("semantic retry returned no committed transaction")
            return copy.deepcopy(committed)
        tx_idx = len(self._transactions)
        self._transactions.append(committed)
        for record in committed_records:
            _index_record(
                record,
                self._receipts,
                self._receipts_by_criterion,
                self._supersessions,
                self._superseded,
                self._semantic_records,
            )
        for record in committed_records:
            kind_r = _semantic_record_kind(record)
            if kind_r is not None:
                rid = _semantic_record_id(record)
                if rid is not None:
                    self._semantic_tx_index.setdefault((kind_r, str(rid)), tx_idx)
        return copy.deepcopy(committed)

    # ── Lifecycle-keyed frame composition ─────────────────────────────────────

    def _compose_finding_assessment_frame(
        self,
        seed_assessment: dict,
        lifecycle: dict,
        acceptance_fingerprint: str,
        transaction_id: str,
    ) -> list[dict]:
        """Derive the full finding-assessment frame from seed + durable view."""
        report_id = lifecycle["report_id"]
        finding_id = lifecycle["finding_id"]
        affected_criteria = list(lifecycle["affected_criteria"])
        assessment_id = seed_assessment.get("assessment_id", "")

        if seed_assessment.get("finding_id") != finding_id:
            raise EvidenceStoreRefused(
                "denied-invalid-review-lifecycle",
                "assessment finding_id does not match lifecycle finding_id",
            )
        if seed_assessment.get("report_id") != report_id:
            raise EvidenceStoreRefused(
                "denied-invalid-review-lifecycle",
                "assessment report_id does not match lifecycle report_id",
            )

        report, finding = _find_report_finding(self._semantic_records, report_id, finding_id)
        if report is None or finding is None:
            raise EvidenceStoreRefused(
                "denied-incomplete-review-assessment-delta",
                "assessment source report and finding must be durable",
            )
        if not _is_current_report(self._semantic_records, report):
            raise EvidenceStoreRefused(
                "denied-incomplete-review-assessment-delta",
                "assessment source report is not current",
            )
        finding_criteria = finding.get("affected_acceptance_criteria", [])
        if sorted(affected_criteria) != sorted(finding_criteria):
            raise EvidenceStoreRefused(
                "denied-invalid-review-lifecycle",
                "lifecycle affected_criteria must match finding affected_acceptance_criteria",
            )

        frame: list[dict] = [copy.deepcopy(seed_assessment)]

        expected_new_ids: set[str] = set()
        if seed_assessment.get("assessment") == "supported":
            expected_new_ids = {
                derive_review_failure_receipt_id(
                    report_id=report_id,
                    finding_id=finding_id,
                    assessment_id=assessment_id,
                    criterion_ref=criterion,
                    acceptance_fingerprint=acceptance_fingerprint,
                )
                for criterion in affected_criteria
            }

        active_source_receipts = _active_bridge_receipts_for_source(
            self._semantic_records, self._receipts, self._superseded,
            report_id=report_id, finding_id=finding_id,
        )
        old_ids = [
            r["receipt_id"]
            for r in active_source_receipts
            if r["receipt_id"] not in expected_new_ids
        ]
        if old_ids:
            sup_payload = _canonical_json({
                "assessment_id": assessment_id,
                "kind": "supersession",
                "report_id": report_id,
                "finding_id": finding_id,
                "transaction_id": transaction_id,
            }).encode("utf-8")
            sup_id = "supersession-bridge-" + hashlib.sha256(sup_payload).hexdigest()
            frame.append(_build_bridge_supersession(sup_id, old_ids))

        if seed_assessment.get("assessment") == "supported":
            for criterion in affected_criteria:
                frame.append(_build_bridge_receipt(
                    report_id=report_id,
                    finding_id=finding_id,
                    assessment_id=assessment_id,
                    criterion_ref=criterion,
                    acceptance_fingerprint=acceptance_fingerprint,
                ))

        return frame

    def _compose_review_report_frame(
        self,
        seed_report: dict,
        acceptance_fingerprint: str,
        transaction_id: str,
    ) -> list[dict]:
        """Derive the full review-report frame from seed + durable view."""
        normalized = self._normalize_semantic_records_for_commit([copy.deepcopy(seed_report)])
        report = normalized[0]
        frame: list[dict] = [report]

        prev_report_id = report.get("lineage", {}).get("previous_report_id")
        if prev_report_id is not None:
            prev_report = self._semantic_records.get("review-report.v1", {}).get(prev_report_id)
            if prev_report is not None:
                all_old_ids: list[str] = []
                for prev_finding in prev_report.get("findings", []):
                    prev_finding_id = prev_finding.get("finding_id", "")
                    if not prev_finding_id:
                        continue
                    old_receipts = _active_bridge_receipts_for_source(
                        self._semantic_records, self._receipts, self._superseded,
                        report_id=prev_report_id, finding_id=prev_finding_id,
                    )
                    all_old_ids.extend(r["receipt_id"] for r in old_receipts)
                if all_old_ids:
                    sup_payload = _canonical_json({
                        "kind": "report-supersession",
                        "prev_report_id": prev_report_id,
                        "transaction_id": transaction_id,
                    }).encode("utf-8")
                    sup_id = "supersession-report-" + hashlib.sha256(sup_payload).hexdigest()
                    frame.append(_build_bridge_supersession(sup_id, all_old_ids))

        return frame

    def _compose_source_invalidation_frame(
        self,
        seed_subject: dict,
        lifecycle: dict,
        acceptance_fingerprint: str,
        transaction_id: str,
    ) -> list[dict]:
        """Derive the full source-invalidation frame from seed + durable view."""
        report_id = lifecycle["report_id"]
        finding_id = lifecycle["finding_id"]

        source_report, _ = _find_report_finding(self._semantic_records, report_id, finding_id)
        if source_report is None:
            raise EvidenceStoreRefused(
                "denied-incomplete-review-assessment-delta",
                "source report must be durable for invalidation",
            )

        source_subject = source_report.get("subject", {})
        new_fp = seed_subject.get("review_subject_fingerprint")
        source_fp = source_subject.get("review_subject_fingerprint")
        new_policy_fp = seed_subject.get("review_policy_fingerprint")
        source_policy_fp = source_subject.get("review_policy_fingerprint")

        if new_fp == source_fp and new_policy_fp == source_policy_fp:
            raise EvidenceStoreRefused(
                "denied-review-source-current",
                "invalidation subject fingerprint must differ from source report subject",
            )

        new_delivery_id = seed_subject.get("delivery_subject_ref", {}).get("subject_id")
        source_delivery_id = source_subject.get("delivery_subject_ref", {}).get("subject_id")
        if new_delivery_id != source_delivery_id:
            raise EvidenceStoreRefused(
                "denied-review-source-current",
                "invalidation subject must share delivery subject id with source report",
            )

        active_receipts = _active_bridge_receipts_for_source(
            self._semantic_records, self._receipts, self._superseded,
            report_id=report_id, finding_id=finding_id,
        )
        if not active_receipts:
            raise EvidenceStoreRefused(
                "denied-empty-review-invalidation",
                "source invalidation has no active derived receipts to supersede",
            )

        frame: list[dict] = []

        subject_id = seed_subject.get("review_subject_id", "")
        existing_subject = self._semantic_records.get("review-subject.v1", {}).get(subject_id)
        if existing_subject is None:
            frame.append(copy.deepcopy(seed_subject))
        elif _canonical_json(existing_subject) != _canonical_json(seed_subject):
            raise EvidenceStoreRefused(
                "denied-incomplete-review-assessment-delta",
                "durable review-subject has different body for the same ID",
            )

        receipt_ids = [r["receipt_id"] for r in active_receipts]
        sup_payload = _canonical_json({
            "finding_id": finding_id,
            "kind": "invalidation",
            "report_id": report_id,
            "transaction_id": transaction_id,
        }).encode("utf-8")
        sup_id = "supersession-invalidation-" + hashlib.sha256(sup_payload).hexdigest()
        frame.append(_build_bridge_supersession(sup_id, receipt_ids))

        return frame

    def _compose_finding_disposition_frame(
        self,
        seed_disposition: dict,
        lifecycle: dict,
        acceptance_fingerprint: str,
        transaction_id: str,
    ) -> list[dict]:
        """Compose the finding-disposition frame from seed + durable view.

        The composed frame is [approval_record (unless already durable)] + [disposition].
        An approval with a matching approval_id but a different body is refused.
        """
        approval_record = lifecycle["approval_record"]
        approval_id = approval_record.get("approval_id", "")
        authority_ref = seed_disposition.get("lineage", {}).get("authority_ref", "")
        if approval_id != authority_ref:
            # The lifecycle carries an approval whose id does not match the
            # disposition's authority_ref.  This prevents an unreferenced approval
            # from riding along on an unrelated disposition.
            raise EvidenceStoreRefused(
                "denied-approval-authority-required",
                "lifecycle approval_record.approval_id must match the disposition "
                "lineage.authority_ref; got '"
                + approval_id + "' vs '" + authority_ref + "'",
            )

        frame: list[dict] = []

        # Include the approval record only when it is not already durable.
        existing_approval = self._semantic_records.get("approval-record.v1", {}).get(approval_id)
        if existing_approval is None:
            frame.append(copy.deepcopy(approval_record))
        elif _canonical_json(existing_approval) != _canonical_json(approval_record):
            raise EvidenceStoreRefused(
                "denied-disposition-changed-approval",
                "a durable approval record with this approval_id has a different body",
            )
        # If identical approval is already durable: omit from frame (already present).

        # Always include the disposition record.
        frame.append(copy.deepcopy(seed_disposition))
        return frame

    def _check_lifecycle_idempotent(
        self,
        seed_records: list[dict],
        lifecycle: dict,
        prev_tx: dict,
        acceptance_fingerprint: str,
        transaction_id: str = "",
    ) -> bool:
        """Return True when a lifecycle retry is idempotent against the committed tx."""
        if prev_tx.get("acceptance_fingerprint") != acceptance_fingerprint:
            return False
        kind = lifecycle.get("kind")
        committed_ids = prev_tx.get("ordered_record_ids", [])
        if not committed_ids or not seed_records:
            return False

        if kind == "finding-assessment":
            assessment = seed_records[0]
            assessment_id = assessment.get("assessment_id", "")
            if committed_ids[0] != assessment_id:
                return False
            # report_id and finding_id must match the lifecycle request
            if (
                assessment.get("report_id") != lifecycle.get("report_id")
                or assessment.get("finding_id") != lifecycle.get("finding_id")
            ):
                return False
            committed_assessment = self._semantic_records.get(
                "finding-assessment.v1", {}
            ).get(assessment_id)
            if committed_assessment is None:
                return False
            if _canonical_json(committed_assessment) != _canonical_json(assessment):
                return False
            if assessment.get("assessment") == "supported":
                affected_criteria = list(lifecycle.get("affected_criteria", []))
                expected_ids = {
                    derive_review_failure_receipt_id(
                        report_id=lifecycle["report_id"],
                        finding_id=lifecycle["finding_id"],
                        assessment_id=assessment_id,
                        criterion_ref=criterion,
                        acceptance_fingerprint=acceptance_fingerprint,
                    )
                    for criterion in affected_criteria
                }
                # Exact equality: committed bridge receipt IDs must equal the derived set.
                committed_bridge_ids = {
                    rid for rid in committed_ids
                    if rid in self._receipts
                    and _is_bridge_review_failure_receipt(self._receipts[rid])
                }
                if expected_ids != committed_bridge_ids:
                    return False
            else:
                # Unsupported: criteria must match the durable finding.
                _rpt, finding = _find_report_finding(
                    self._semantic_records,
                    lifecycle.get("report_id", ""),
                    lifecycle.get("finding_id", ""),
                )
                if finding is not None:
                    durable_criteria = set(finding.get("affected_acceptance_criteria", []))
                    if set(lifecycle.get("affected_criteria", [])) != durable_criteria:
                        return False
            return True

        if kind == "review-report":
            seed_report = seed_records[0]
            report_id = seed_report.get("report_id", "")
            if committed_ids[0] != report_id:
                return False
            committed_report = self._semantic_records.get("review-report.v1", {}).get(report_id)
            if committed_report is None:
                return False
            seed_copy = copy.deepcopy(seed_report)
            seed_copy.setdefault("lineage", {})
            seed_copy["lineage"]["sequence"] = committed_report["lineage"]["sequence"]
            if "previous_report_id" in committed_report["lineage"]:
                seed_copy["lineage"]["previous_report_id"] = (
                    committed_report["lineage"]["previous_report_id"]
                )
            else:
                seed_copy["lineage"].pop("previous_report_id", None)
            return _canonical_json(committed_report) == _canonical_json(seed_copy)

        if kind == "source-invalidation":
            seed_subject = seed_records[0]
            subject_id = seed_subject.get("review_subject_id", "")
            # Derive the expected supersession_id from (finding_id, kind, report_id,
            # transaction_id); the committed frame must contain exactly that supersession.
            sup_payload = _canonical_json({
                "finding_id": lifecycle.get("finding_id", ""),
                "kind": "invalidation",
                "report_id": lifecycle.get("report_id", ""),
                "transaction_id": transaction_id,
            }).encode("utf-8")
            expected_sup_id = (
                "supersession-invalidation-" + hashlib.sha256(sup_payload).hexdigest()
            )
            if expected_sup_id not in committed_ids:
                return False
            committed_subject = self._semantic_records.get("review-subject.v1", {}).get(subject_id)
            if committed_subject is None:
                # Subject was omitted from frame (already durable from a prior tx)
                # Nothing to compare; the invalidation supersession was still applied
                return True
            return _canonical_json(committed_subject) == _canonical_json(seed_subject)

        if kind == "finding-disposition":
            disp_kind = _semantic_record_kind(seed_records[0]) if seed_records else None
            if not seed_records or disp_kind != "finding-disposition.v1":
                return False
            disposition = seed_records[0]
            disposition_id = disposition.get("disposition_id", "")
            if disposition_id not in committed_ids:
                return False
            committed_disposition = self._semantic_records.get(
                "finding-disposition.v1", {}
            ).get(disposition_id)
            if committed_disposition is None:
                return False
            if _canonical_json(committed_disposition) != _canonical_json(disposition):
                return False
            # The approval may or may not have been in the same frame.
            # If the approval_id is in the committed frame, verify it matches.
            approval_record = lifecycle.get("approval_record", {})
            approval_id = approval_record.get("approval_id", "")
            if approval_id in committed_ids:
                committed_approval = self._semantic_records.get(
                    "approval-record.v1", {}
                ).get(approval_id)
                if committed_approval is None:
                    return False
                if _canonical_json(committed_approval) != _canonical_json(approval_record):
                    return False
            return True

        return False

    def _write_lifecycle_frame_once(
        self,
        seed_records: list[dict],
        lifecycle: dict,
        transaction_id: str,
        acceptance_fingerprint: str,
        *,
        audit_sink: Callable[[Any], None],
        op_id: str,
    ) -> dict:
        """Compose, validate, and append a lifecycle-keyed semantic batch under lock."""
        cm = _confined_mutation()

        def decide_and_write(current_size: int) -> tuple[dict | None, list[dict] | None]:
            self._refresh_from_durable_log(current_size)

            for prev_tx in self._transactions:
                if prev_tx.get("transaction_id") == transaction_id:
                    if self._check_lifecycle_idempotent(
                        seed_records, lifecycle, prev_tx, acceptance_fingerprint,
                        transaction_id,
                    ):
                        return prev_tx, None
                    raise EvidenceStoreRefused(
                        "denied-duplicate-transaction-id",
                        "lifecycle request differs from committed transaction",
                    )

            kind = lifecycle.get("kind")
            if kind == "finding-assessment":
                if (
                    not seed_records
                    or _semantic_record_kind(seed_records[0]) != "finding-assessment.v1"
                ):
                    raise EvidenceStoreRefused(
                        "denied-invalid-review-lifecycle",
                        "finding-assessment lifecycle requires one assessment seed record",
                    )
                composed = self._compose_finding_assessment_frame(
                    seed_records[0], lifecycle, acceptance_fingerprint, transaction_id
                )
            elif kind == "review-report":
                if (
                    not seed_records
                    or _semantic_record_kind(seed_records[0]) != "review-report.v1"
                ):
                    raise EvidenceStoreRefused(
                        "denied-invalid-review-lifecycle",
                        "review-report lifecycle requires one report seed record",
                    )
                composed = self._compose_review_report_frame(
                    seed_records[0], acceptance_fingerprint, transaction_id
                )
            elif kind == "finding-disposition":
                if (
                    not seed_records
                    or _semantic_record_kind(seed_records[0]) != "finding-disposition.v1"
                ):
                    raise EvidenceStoreRefused(
                        "denied-invalid-review-lifecycle",
                        "finding-disposition lifecycle requires one disposition seed record",
                    )
                composed = self._compose_finding_disposition_frame(
                    seed_records[0], lifecycle, acceptance_fingerprint, transaction_id
                )
            else:  # source-invalidation
                if (
                    not seed_records
                    or _semantic_record_kind(seed_records[0]) != "review-subject.v1"
                ):
                    raise EvidenceStoreRefused(
                        "denied-invalid-review-lifecycle",
                        "source-invalidation lifecycle requires one review-subject seed record",
                    )
                composed = self._compose_source_invalidation_frame(
                    seed_records[0], lifecycle, acceptance_fingerprint, transaction_id
                )

            composed_ids = [str(_semantic_record_id(record)) for record in composed]
            for record in composed:
                record_kind = _semantic_record_kind(record)
                if record_kind is None or record_kind not in _SEMANTIC_RECORDS:
                    raise EvidenceStoreRefused(
                        "denied-unknown-record-kind",
                        "composed record has unknown kind",
                    )
                record_id = _semantic_record_id(record)
                if not _is_identity(record_id):
                    raise EvidenceStoreRefused(
                        "denied-invalid-review-record-denied-invalid-identity",
                        "composed record has invalid identity",
                    )
                # Refuse a composed record whose semantic ID is already admitted.
                admitted = self._semantic_records.get(record_kind, {})
                if str(record_id) in admitted:
                    raise EvidenceStoreRefused(
                        "denied-duplicate-review-record-id",
                        f"composed record ID already admitted: {record_id}",
                    )
                _check_record_safety(
                    record, _SEMANTIC_RECORDS[record_kind]["profile"], record_id=str(record_id)
                )

            _validate_review_transition(
                composed,
                acceptance_fingerprint=acceptance_fingerprint,
                semantic_records=self._semantic_records,
                receipts=self._receipts,
                superseded=self._superseded,
                record_tx_index=self._semantic_tx_index,
                current_tx_index=len(self._transactions),
                # The lifecycle path always permits disposition frames.  For the
                # finding-disposition kind, pass the lifecycle's review_subject so
                # Rule 4 can run unconditionally even when review-subject.v1 is not
                # separately durable in the store.
                check_disposition_rules=True,
                lifecycle_review_subject=(
                    lifecycle.get("review_subject")
                    if kind == "finding-disposition"
                    else None
                ),
            )

            tx = _build_transaction(transaction_id, composed_ids, acceptance_fingerprint, composed)
            self._refuse_invalid_header(tx, audit_sink=audit_sink, op_id=op_id)
            _check_record_safety(
                tx, "semantic-evidence-transaction.v1", record_id=transaction_id
            )

            frame_bytes = _serialize_frame(tx, composed)
            if self._log_size + len(frame_bytes) > _EVIDENCE_LOG_MAX_BYTES:
                raise EvidenceStoreRefused(
                    "denied-log-size-limit",
                    "appending this frame would take the log past the size replay accepts",
                )
            cm.confined_append(self._root, self._log_path, frame_bytes)
            self._log_size += len(frame_bytes)
            return tx, composed

        try:
            if _HAS_FCNTL:
                with _advisory_lock(self._root, self._log_path) as lock_fd:
                    committed, committed_records = decide_and_write(os.fstat(lock_fd).st_size)
            else:
                committed, committed_records = decide_and_write(self._log_path.stat().st_size)
        except EvidenceStoreRefused as exc:
            _emit_post_allow_denial(audit_sink, op_id, exc.denial_code)
            raise
        except cm.MutationDenied as exc:
            if exc.denial_code == "denied-rollback-failed":
                self._poisoned = True
            denial_code = f"denied-append-failed-{exc.denial_code}"
            _emit_post_allow_denial(audit_sink, op_id, denial_code)
            raise EvidenceStoreRefused(
                denial_code, f"lifecycle frame append failed: {exc.denial_code}"
            ) from exc

        if committed_records is None:
            if committed is None:
                raise EvidenceStoreError("lifecycle retry returned no committed transaction")
            return copy.deepcopy(committed)
        tx_idx = len(self._transactions)
        self._transactions.append(committed)
        for record in committed_records:
            _index_record(
                record,
                self._receipts,
                self._receipts_by_criterion,
                self._supersessions,
                self._superseded,
                self._semantic_records,
            )
        for record in committed_records:
            kind_r = _semantic_record_kind(record)
            if kind_r is not None:
                rid = _semantic_record_id(record)
                if rid is not None:
                    self._semantic_tx_index.setdefault((kind_r, str(rid)), tx_idx)
        return copy.deepcopy(committed)

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
        self._refuse_invalid_header(tx, audit_sink=audit_sink, op_id=op_id)
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
            "receipt", records, tx, _serialize_frame(tx, records),
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
        self._refuse_invalid_header(tx, audit_sink=audit_sink, op_id=op_id)
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
            "supersession", records, tx, _serialize_frame(tx, records),
            audit_sink=audit_sink, op_id=op_id,
        )

    # ── Append: semantic record batches ───────────────────────────────────────

    def append_semantic_records(
        self,
        records: list[dict],
        *,
        transaction_id: str,
        acceptance_fingerprint: str,
        issuer: object,
        grant: object,
        audit_sink: Callable[[Any], None],
        lifecycle: dict | None = None,
    ) -> dict:
        """Append a closed batch of semantic records as one transaction.

        When ``lifecycle`` is provided it must be a dict whose ``kind`` is one of
        ``"finding-assessment"``, ``"review-report"``, or ``"source-invalidation"``
        and whose keys exactly match the registered shape.  The store composes the
        full frame (receipts, supersessions) from the seed records inside the
        advisory lock after refreshing from the durable log, so the composition
        is always consistent with the committed state.  Any unknown kind, extra key,
        or missing key refuses with ``"denied-invalid-review-lifecycle"`` after the
        authority check, using the post-allow denial path.

        When ``lifecycle`` is ``None`` the raw path is unchanged.
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
        if not isinstance(records, list) or not records:
            raise EvidenceStoreRefused(
                "denied-empty-semantic-records",
                "semantic record batch must contain at least one record",
            )

        # Peek at the lifecycle kind to choose the correct authority scope.
        # The finding-disposition lifecycle requires a "review" root grant;
        # a malformed lifecycle dict still uses the "evidence" scope and then
        # fails at the lifecycle shape check, with the denial paired to the same op_id.
        _lifecycle_kind_peek = (
            lifecycle.get("kind") if isinstance(lifecycle, dict) else None
        )
        _record_scope = (
            "review/disposition"
            if _lifecycle_kind_peek == "finding-disposition"
            else "evidence"
        )
        op_id = _check_producer_authority(
            issuer,
            grant,
            audit_sink=audit_sink,
            record_scope=_record_scope,
            required_operations=["append"],
        )

        if lifecycle is not None:
            if not isinstance(lifecycle, dict):
                denial_code = "denied-invalid-review-lifecycle"
                _emit_post_allow_denial(audit_sink, op_id, denial_code)
                raise EvidenceStoreRefused(denial_code, "lifecycle must be a dict")
            kind = lifecycle.get("kind")
            expected_keys = _LIFECYCLE_KIND_SHAPES.get(kind)  # type: ignore[arg-type]
            if expected_keys is None or set(lifecycle.keys()) != expected_keys:
                denial_code = "denied-invalid-review-lifecycle"
                _emit_post_allow_denial(audit_sink, op_id, denial_code)
                raise EvidenceStoreRefused(
                    denial_code, f"invalid lifecycle dict for kind {kind!r}"
                )
            safe_records = copy.deepcopy(records)
            for record in safe_records:
                ok, code = validate_semantic_record(record)
                if not ok:
                    denial_code = f"denied-invalid-semantic-record-{code}"
                    _emit_post_allow_denial(audit_sink, op_id, denial_code)
                    raise EvidenceStoreRefused(denial_code, f"seed record invalid: {code}")
            return self._write_lifecycle_frame_once(
                safe_records, lifecycle, transaction_id, acceptance_fingerprint,
                audit_sink=audit_sink, op_id=op_id,
            )

        safe_records = copy.deepcopy(records)
        for record in safe_records:
            ok, code = validate_semantic_record(record)
            if not ok:
                denial_code = f"denied-invalid-semantic-record-{code}"
                _emit_post_allow_denial(audit_sink, op_id, denial_code)
                raise EvidenceStoreRefused(
                    denial_code,
                    f"semantic record validation failed: {code}",
                )
            record_id = _semantic_record_id(record)
            if not _is_identity(record_id):
                denial_code = "denied-invalid-review-record-denied-invalid-identity"
                _emit_post_allow_denial(audit_sink, op_id, denial_code)
                raise EvidenceStoreRefused(
                    denial_code,
                    "semantic record identity is invalid",
                )

        return self._write_semantic_frame_once(
            safe_records,
            transaction_id,
            acceptance_fingerprint,
            audit_sink=audit_sink,
            op_id=op_id,
        )

    def get_semantic_records(self, record_type: str) -> list[dict]:
        """Return deep-copied semantic records of a registered kind."""
        if not isinstance(record_type, str):
            raise EvidenceStoreRefused(
                "denied-unknown-record-kind",
                "semantic record kind must be a string",
            )
        if record_type not in _SEMANTIC_RECORDS:
            raise EvidenceStoreRefused(
                "denied-unknown-record-kind",
                f"unknown semantic record kind: {record_type!r}",
            )
        return [
            copy.deepcopy(record)
            for record in self._semantic_records.get(record_type, {}).values()
        ]

    def current_finding_assessments(
        self, review_subject_fingerprint: str
    ) -> dict[tuple[str, str], dict]:
        """Return the latest finding assessment per (report_id, finding_id) key.

        Only assessments whose source report is the current tip for its group
        are included.  For ``"supported"`` assessments the receipt_ids list
        contains the IDs of the active bridge-owned receipts; the entry is
        omitted when none are active.  For other outcomes receipt_ids is empty
        and the entry is omitted when any derived receipt is still active.
        """
        if not self._opened:
            raise EvidenceStoreRefused(
                "denied-store-not-opened",
                "EvidenceStore.open() must be called before querying",
            )
        latest_by_source: dict[tuple[str, str], dict] = {}
        for tx in self._transactions:
            for record_id in tx.get("ordered_record_ids", []):
                assessment = self._semantic_records.get("finding-assessment.v1", {}).get(record_id)
                if assessment is None:
                    continue
                if assessment.get("review_subject_fingerprint") != review_subject_fingerprint:
                    continue
                key = (assessment.get("report_id", ""), assessment.get("finding_id", ""))
                latest_by_source[key] = assessment

        current: dict[tuple[str, str], dict] = {}
        for key, assessment in latest_by_source.items():
            report_id, finding_id = key
            report = self._semantic_records.get("review-report.v1", {}).get(report_id)
            if report is None:
                continue
            # Use select_current_report so a forked/duplicate-sequence group yields
            # no current tip (unlike _is_current_report which returns True for both
            # members of a forked group).
            subject = report.get("subject", {})
            policy_fp = report.get("lineage", {}).get("review_policy_fingerprint")
            group_reports = [
                r for r in self._semantic_records.get("review-report.v1", {}).values()
                if r.get("role") == report.get("role")
                and _canonical_json(r.get("subject")) == _canonical_json(subject)
                and r.get("lineage", {}).get("review_policy_fingerprint") == policy_fp
            ]
            tip_report, _ = _review_contracts().select_current_report(
                copy.deepcopy(group_reports),
                role=report["role"],
                review_subject_fingerprint=subject.get("review_subject_fingerprint", ""),
                review_policy_fingerprint=policy_fp,
            )
            if tip_report is None or tip_report.get("report_id") != report_id:
                continue
            # Compute the exact set of receipt IDs expected for the latest assessment.
            _rpt, finding = _find_report_finding(self._semantic_records, report_id, finding_id)
            criteria = finding.get("affected_acceptance_criteria", []) if finding else []
            assessment_tx_fp = ""
            for tx in self._transactions:
                if assessment.get("assessment_id", "") in tx.get("ordered_record_ids", []):
                    assessment_tx_fp = tx.get("acceptance_fingerprint", "")
                    break
            expected_ids = {
                derive_review_failure_receipt_id(
                    report_id=report_id,
                    finding_id=finding_id,
                    assessment_id=assessment.get("assessment_id", ""),
                    criterion_ref=criterion,
                    acceptance_fingerprint=assessment_tx_fp,
                )
                for criterion in criteria
            }
            active_receipts = _active_bridge_receipts_for_source(
                self._semantic_records, self._receipts, self._superseded,
                report_id=report_id, finding_id=finding_id,
            )
            active_ids = {r["receipt_id"] for r in active_receipts}
            if assessment.get("assessment") == "supported":
                # Include only when the active set is exactly the expected set.
                if not expected_ids or expected_ids != active_ids:
                    continue
                receipt_ids = [r["receipt_id"] for r in active_receipts]
            else:
                if active_receipts:
                    continue
                receipt_ids = []
            current[key] = {
                "assessment": copy.deepcopy(assessment),
                "receipt_ids": receipt_ids,
            }
        return current

    def disposition_closes(
        self,
        disposition_id: str,
        review_subject: dict[str, Any],
    ) -> bool:
        """Return True when a durable disposition currently closes its finding.

        Re-evaluates all disposition-authority rules against the current durable
        state, using the same functions as the write path and replay.  Returns
        False on any rule violation without raising.

        Checked rules (for all disposition kinds):
          - Disposition exists with matching subject fingerprint.
          - Paired approval is durable and not superseded by a later approval.
          - Rule 1: approval decision_scope == "review-disposition".
          - Rule 3: disposition decision_maker.identity == approval authority.identity.
          - G1: approval.decision == "approved".
          - G2: disposition decision_maker.role == approval authority.role.
          - The disposition's assessment_id is still the latest for the finding in
            current_finding_assessments.

        For fixed-by additionally (rule 5 extension):
          - Replacement report is durable with a different subject fingerprint.
          - Same role as the original report.
          - Shared delivery_subject_ref.subject_id with the review_subject.
          - Replacement is the current tip for its role/subject/policy group.
          - Replacement was admitted after the assessment (tx ordering).
          - Every replacement finding has a current assessment.
          - No replacement finding assessment is indeterminate.
          - No replacement finding has a supported assessment whose actual_failure
            matches the original finding's actual_failure.
        """
        if not self._opened:
            return False

        # 1. Find the disposition by ID.
        disposition = self._semantic_records.get("finding-disposition.v1", {}).get(
            disposition_id
        )
        if disposition is None:
            return False

        subject_fp = review_subject.get("review_subject_fingerprint", "")
        if disposition.get("review_subject_fingerprint") != subject_fp:
            return False

        # 2. Find the paired approval.
        authority_ref = disposition.get("lineage", {}).get("authority_ref", "")
        approval = self._semantic_records.get("approval-record.v1", {}).get(authority_ref)
        if approval is None:
            return False

        # 3. Approval must not be superseded: no later approval names it as predecessor.
        for _other in self._semantic_records.get("approval-record.v1", {}).values():
            if _other.get("lineage", {}).get("predecessor_id") == authority_ref:
                return False

        # Rule 1: approval scope.
        if approval.get("decision_scope") != "review-disposition":
            return False

        # Rule 3: identity match.
        if (
            disposition.get("decision_maker", {}).get("identity")
            != approval.get("authority", {}).get("identity")
        ):
            return False

        # G1: approval.decision must be "approved".  A superseded approval does not
        # authorize closure even when it was valid at write time.
        if approval.get("decision") != "approved":
            return False

        # G2: decision_maker role must match approval authority role.
        if (
            disposition.get("decision_maker", {}).get("role")
            != approval.get("authority", {}).get("role")
        ):
            return False

        # Assessment must still be the latest supported one on the current tip.
        assessment_id = disposition.get("assessment_id", "")
        finding_id = disposition.get("finding_id", "")
        assessment = self._semantic_records.get("finding-assessment.v1", {}).get(
            assessment_id
        )
        if assessment is None:
            return False
        report_id = assessment.get("report_id", "")

        current = self.current_finding_assessments(subject_fp)
        entry = current.get((report_id, finding_id))
        if entry is None:
            return False
        if entry["assessment"].get("assessment_id") != assessment_id:
            return False

        disp_kind = disposition.get("disposition", "")

        if disp_kind == "accept-risk":
            return True

        if disp_kind == "fixed-by":
            replacement_id = disposition.get("replacement_report_id", "")
            if not replacement_id:
                return False

            replacement = self._semantic_records.get("review-report.v1", {}).get(
                replacement_id
            )
            if replacement is None:
                return False

            # Replacement must belong to a different subject fingerprint.
            replacement_fp = replacement.get("subject", {}).get(
                "review_subject_fingerprint", ""
            )
            if replacement_fp == subject_fp:
                return False

            # Same role as the original report.
            original_report = self._semantic_records.get("review-report.v1", {}).get(
                report_id
            )
            if original_report is None:
                return False
            if replacement.get("role") != original_report.get("role"):
                return False

            # Shared delivery_subject_ref.subject_id.
            orig_delivery_id = review_subject.get("delivery_subject_ref", {}).get(
                "subject_id", ""
            )
            repl_delivery_id = replacement.get("subject", {}).get(
                "delivery_subject_ref", {}
            ).get("subject_id", "")
            if orig_delivery_id != repl_delivery_id:
                return False

            # Replacement must be the current tip for its role/subject/policy group.
            policy_fp = replacement.get("subject", {}).get("review_policy_fingerprint", "")
            group_reports = [
                r for r in self._semantic_records.get("review-report.v1", {}).values()
                if r.get("role") == replacement.get("role")
                and r.get("subject", {}).get("review_subject_fingerprint") == replacement_fp
                and r.get("subject", {}).get("review_policy_fingerprint") == policy_fp
            ]
            tip, _ = _review_contracts().select_current_report(
                copy.deepcopy(group_reports),
                role=replacement.get("role", ""),
                review_subject_fingerprint=replacement_fp,
                review_policy_fingerprint=policy_fp,
            )
            if tip is None or tip.get("report_id") != replacement_id:
                return False

            # Replacement must have been admitted after the assessment (tx ordering).
            assessment_tx_idx = self._semantic_tx_index.get(
                ("finding-assessment.v1", assessment_id), -1
            )
            replacement_tx_idx = self._semantic_tx_index.get(
                ("review-report.v1", replacement_id), -1
            )
            if replacement_tx_idx < 0 or replacement_tx_idx <= assessment_tx_idx:
                return False

            # All replacement findings must have a current assessment; none may be
            # indeterminate; none may be supported with the same actual_failure as
            # the original finding.
            original_failure = ""
            for _f in original_report.get("findings", []):
                if _f.get("finding_id") == finding_id:
                    original_failure = _f.get("actual_failure", "")
                    break

            repl_current = self.current_finding_assessments(replacement_fp)
            for repl_finding in replacement.get("findings", []):
                repl_finding_id = repl_finding.get("finding_id", "")
                repl_key = (replacement_id, repl_finding_id)
                repl_entry = repl_current.get(repl_key)
                if repl_entry is None:
                    return False  # No current assessment for this replacement finding.
                repl_assessment = repl_entry["assessment"]
                if repl_assessment.get("assessment") == "indeterminate":
                    return False
                if (
                    repl_assessment.get("assessment") == "supported"
                    and original_failure
                    and repl_finding.get("actual_failure", "") == original_failure
                ):
                    return False

            return True

        return False

    def get_transaction(self, transaction_id: str) -> dict | None:
        """Return a deep-copied committed transaction by ID, if present."""
        for tx in self._transactions:
            if tx.get("transaction_id") == transaction_id:
                return copy.deepcopy(tx)
        return None

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
