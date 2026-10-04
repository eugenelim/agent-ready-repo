"""_security_events — audit emitter and writer-authority check for the work-loop skill.

The audit emitter emits a durable ``SecurityEvent`` to the caller-supplied sink
BEFORE acknowledging success or refusal.  If the sink is unavailable the
operation fails closed with ``AuditSinkUnavailable``; no effect is returned and
no protected data is persisted.

Named writer authority (``check_writer_authority_and_emit``) validates the
writer's capability grant against the issuer, the required operations, and the
record scope, then emits one security event before returning the allow/deny
result.

Denial and reason codes are stable strings that carry no payload bytes, excerpts,
or content-derived hashes.  No identity, correlation, or retry key may be derived
from refused bytes.

Standard library only. No third-party imports, no packaging, no installation.
Python 3.11+.
"""

import contextlib
import importlib.util
import json
import os
import secrets
import stat
import sys
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Final

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = [
    "SecurityEvent",
    "AuditSinkError",
    "AuditSinkUnavailable",
    "KNOWN_REASON_CODES",
    "emit_security_event",
    "emit_denial_best_effort",
    "check_writer_authority_and_emit",
    "make_operation_id",
    "validate_event_dict",
]

# ── Sibling module loader ─────────────────────────────────────────────────────

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parent


def _load_sibling(alias: str, filename: str) -> object:
    """Load a sibling script module by filename, registered temporarily.

    Uses the same importlib.util loader pattern as other script modules.
    """
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
        spec = importlib.util.spec_from_file_location(alias, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"no import spec for {path}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[alias] = mod
        try:
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
        finally:
            sys.modules.pop(alias, None)
        return mod
    finally:
        sys.dont_write_bytecode = previous


# Loaded once at module import; used by emit_security_event to apply the
# registered content-safety profile before passing the event to the sink.
_cs = _load_sibling("_cs_se", "_content_safety.py")

# ── Stable reason codes ───────────────────────────────────────────────────────
#
# Every code is a stable string; callers may match against these values.
# No code is derived from request bytes.  Add codes here before use.

KNOWN_REASON_CODES: Final[frozenset[str]] = frozenset({
    "allowed-file-read",
    "allowed-file-write",
    "allowed-file-append",
    "allowed-file-create",
    "allowed-capability-issue",
    "allowed-semantic-append",
    "denied-path-violation",
    "denied-unsafe-host",
    "denied-size-exceeded",
    "denied-staging-failed",
    "denied-invalid-grant",
    "denied-out-of-scope",
    "denied-missing-operation",
    "denied-credential",
    "denied-personal-data",
    "denied-encoding",
    "denied-structure",
    "denied-unknown-class",
})


# ── SecurityEvent ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SecurityEvent:
    """Redacted audit record for a security-sensitive operation.

    Maps to the ``security-event.v1`` schema.  Fields carry no payload bytes,
    request content, or personal identifiers.  The ``reason_code`` is one of
    the strings in ``KNOWN_REASON_CODES`` (callers may extend for their own
    operations but must not derive codes from refused content).
    """

    schema_version: int
    operation_id: str
    correlation_id: str
    event_type: str
    outcome: str          # "allowed" | "denied"
    reason_code: str      # stable, no payload bytes
    timestamp: str        # RFC 3339


# ── Exceptions ────────────────────────────────────────────────────────────────


class AuditSinkError(Exception):
    """The audit sink raised an error during emission."""


class AuditSinkUnavailable(Exception):
    """The audit sink was unavailable; the operation fails closed.

    No effect success is returned and no protected data is persisted when
    this exception is raised.
    """


# ── Internal helpers ──────────────────────────────────────────────────────────


def _now_rfc3339() -> str:
    """Return the current UTC instant as an RFC 3339 string."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Public API ────────────────────────────────────────────────────────────────


def make_operation_id() -> str:
    """Generate a fresh random operation identifier.

    The identifier is not derived from any content or request bytes, so it
    carries no information that could be used to reconstruct refused content.
    """
    return "op-" + secrets.token_hex(16)


def emit_security_event(
    sink: Callable[[SecurityEvent], None],
    event: SecurityEvent,
) -> SecurityEvent:
    """Emit *event* to *sink* and return it.

    Applies the registered content-safety profile for ``security-event.v1``
    before passing the event to the sink.  A missing or unknown profile, or a
    failing check, raises ``AuditSinkUnavailable`` so the caller fails closed;
    audit failure never turns a denial into an allow.

    The sink is called BEFORE this function returns, so the event is durable
    (from the caller's perspective) before any success acknowledgment.

    Raises:
        AuditSinkUnavailable: when the content-safety check fails, the sink
            raises ``AuditSinkError``, or any ``OSError``.  In every case no
            success is returned and the caller must fail closed.
    """
    # Apply the registered content-safety profile before append.
    # The profile for security-event.v1 is "structured-control".
    # An unknown or missing profile refuses without persisting payload bytes.
    profile = _cs.SLICE_1_WRITER_BOUNDARIES.get("security-event.v1")  # type: ignore[attr-defined]
    if profile is None:
        raise AuditSinkUnavailable(
            "security-event.v1 has no registered content-safety profile; "
            "failing closed without persisting the event"
        )
    payload = json.dumps(
        {
            "schema_version": event.schema_version,
            "operation_id": event.operation_id,
            "correlation_id": event.correlation_id,
            "event_type": event.event_type,
            "outcome": event.outcome,
            "reason_code": event.reason_code,
            "timestamp": event.timestamp,
        },
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    decision = _cs.check_content_safety(  # type: ignore[attr-defined]
        profile,
        payload,
        source_record_id=event.operation_id,
    )
    if not decision.accepted:
        raise AuditSinkUnavailable(
            f"security-event content-safety check failed "
            f"({decision.decision_code}); failing closed without persisting"
        )

    try:
        sink(event)
    except Exception as exc:  # noqa: BLE001 — every sink failure fails closed
        # The message is fixed: sink error text can carry paths or payload.
        raise AuditSinkUnavailable("audit sink unavailable; failing closed") from exc
    return event


#: Correlation value used when a caller-supplied correlation ID is refused by
#: the content-safety check, so the denial is still audited without its bytes.
REDACTED_CORRELATION_ID: Final[str] = "redacted"


def emit_denial_best_effort(
    sink: Callable[[SecurityEvent], None],
    event: SecurityEvent,
) -> None:
    """Emit a denial event through the content-safety check; never raise.

    A denial is returned to its caller whether or not it can be audited.  If
    the event is refused (for example, a credential-shaped correlation ID),
    it is retried once with the correlation ID redacted, so no refused bytes
    reach the sink.  A sink that is still unavailable is ignored here because
    the operation is already failing closed.
    """
    try:
        emit_security_event(sink, event)
        return
    except AuditSinkUnavailable:
        pass
    with contextlib.suppress(AuditSinkUnavailable):
        emit_security_event(sink, replace(event, correlation_id=REDACTED_CORRELATION_ID))


def check_writer_authority_and_emit(
    *,
    issuer: object,
    grant: object,
    record_scope: str,
    required_operations: list[str],
    sink: Callable[[SecurityEvent], None],
    operation_id: str,
    correlation_id: str,
) -> bool:
    """Validate writer authority and emit a durable security event.

    Checks, in order:
    1. The grant is valid (issued by *issuer*, not expired, not revoked).
    2. All *required_operations* are present in the grant's operations.
    3. The *record_scope* is covered by at least one of the grant's
       ``writes.allowed_roots``.

    A security event is emitted to *sink* before this function returns,
    regardless of the allow/deny outcome.

    Raises:
        AuditSinkUnavailable: when the sink is unavailable.  The caller must
            fail closed: no effect is performed, no success is returned.

    Returns:
        True when the writer is authorized; False when refused.  The denial
        reason is recorded in the emitted event's ``reason_code``.

    No content from the refused request bytes enters the event or the
    ``operation_id``.  The ``correlation_id`` must be supplied by the caller
    from the capability grant_id or another non-content source.
    """
    timestamp = _now_rfc3339()
    outcome: str
    reason_code: str

    # 1. Verify the grant is registered and active.
    if not issuer.verify_grant(grant):  # type: ignore[union-attr]
        outcome = "denied"
        reason_code = "denied-invalid-grant"
    else:
        grant_ops = set(getattr(grant, "operations", ()))
        missing = [op for op in required_operations if op not in grant_ops]
        if missing:
            outcome = "denied"
            reason_code = "denied-missing-operation"
        else:
            # 3. Scope check: at least one allowed write root must prefix the scope.
            allowed_roots = list(getattr(getattr(grant, "writes", None), "allowed_roots", ()))
            scope_covered = any(
                record_scope == root or record_scope.startswith(root.rstrip("/") + "/")
                for root in allowed_roots
            )
            if not scope_covered:
                outcome = "denied"
                reason_code = "denied-out-of-scope"
            else:
                outcome = "allowed"
                reason_code = (
                    "allowed-semantic-append"
                    if "append" in required_operations
                    else "allowed-file-write"
                )

    event = SecurityEvent(
        schema_version=1,
        operation_id=operation_id,
        correlation_id=correlation_id,
        event_type="capability-check",
        outcome=outcome,
        reason_code=reason_code,
        timestamp=timestamp,
    )
    # Emit before returning — AuditSinkUnavailable propagates; caller fails closed.
    emit_security_event(sink, event)
    return outcome == "allowed"


# ── In-code schema validation ─────────────────────────────────────────────────

_VALID_OUTCOMES: Final[frozenset[str]] = frozenset({"allowed", "denied"})

_REQUIRED_EVENT_KEYS: Final[frozenset[str]] = frozenset({
    "schema_version",
    "operation_id",
    "correlation_id",
    "event_type",
    "outcome",
    "reason_code",
    "timestamp",
})

_ALLOWED_EVENT_KEYS: Final[frozenset[str]] = _REQUIRED_EVENT_KEYS


def validate_event_dict(d: dict) -> tuple[bool, str]:
    """Validate a security-event.v1 record dict in code.

    Checks schema_version, required fields, outcome enum, and absence of
    unknown authority-shaped fields.  Does not import jsonschema at runtime.

    Returns:
        (True, "ok") when the record is schema-valid.
        (False, denial_code) when invalid; denial_code is one of:
          denied-unknown-schema-version — unknown or wrong schema_version.
          denied-missing-required-field — a required field is absent.
          denied-invalid-enum — outcome is not "allowed" or "denied".
          denied-unknown-authority-field — an authority-shaped field not in the schema.
    """
    if not isinstance(d, dict):
        return False, "denied-missing-required-field"

    version = d.get("schema_version")
    if not isinstance(version, int) or version != 1:
        return False, "denied-unknown-schema-version"

    missing = _REQUIRED_EVENT_KEYS - set(d.keys())
    if missing:
        return False, "denied-missing-required-field"

    outcome = d.get("outcome")
    if outcome not in _VALID_OUTCOMES:
        return False, "denied-invalid-enum"

    # security-event.v1 is closed: no additional fields permitted.
    unknown = set(d.keys()) - _ALLOWED_EVENT_KEYS
    if unknown:
        return False, "denied-unknown-authority-field"

    return True, "ok"
