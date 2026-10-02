"""_effect_broker — optional effect broker for contained child processes.

The effect broker performs explicitly granted outward effects on behalf of a
contained child process.  OS enforcement (not the broker API) removes the
child's direct authority; the broker validates grants and performs the only
approved outward effect.

Every effect request validates the named producer's capability grant before
staging any effect (AC-0020).  When the audit sink is available, a durable
security event is emitted before the effect is acknowledged.  When the sink
is unavailable, the request fails closed with a stable redacted denial code,
no effect success, no protected data persistence, and no durable-event claim
(AC-0021).

Broker effects that target delivery-control paths (as defined in
``_containment.DELIVERY_CONTROL_PATHS``) are refused without audit when the
grant does not cover that path; no bypass write ever reaches the control
plane.

In Slice 1, real brokered effects run only in conformance fixtures.

Standard library only plus the sibling ``_security_events.py`` and
``_containment.py`` modules, each loaded by path at import time.
Python 3.11+.
"""

from __future__ import annotations

import importlib.util
import os
import stat
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Final

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = [
    "BrokerError",
    "BrokerRefused",
    "BrokerSession",
    "BrokerGrant",
    "BrokerResult",
    "BROKER_DENIAL_CODES",
    "BROKER_ALLOW_REASON",
    "BROKER_DENY_REASON",
    "create_broker_session",
    "request_effect",
    "validate_broker_grant_dict",
]

# ---------------------------------------------------------------------------
# Sibling module loader
# ---------------------------------------------------------------------------

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parent


def _load_sibling(alias: str, filename: str) -> object:
    """Load a sibling script module by filename, registered temporarily.

    Uses the same importlib.util loader pattern as the other script modules.
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


# Loaded once at module import.
_se = _load_sibling("_se_broker", "_security_events.py")
_cn = _load_sibling("_cn_broker", "_containment.py")

# ---------------------------------------------------------------------------
# Stable reason and denial codes
# ---------------------------------------------------------------------------

BROKER_ALLOW_REASON: Final[str] = "allowed-broker-effect"
BROKER_DENY_REASON: Final[str] = "denied-broker-effect"

BROKER_DENIAL_CODES: Final[frozenset[str]] = frozenset({
    "denied-audit-sink-unavailable",
    "denied-missing-grant",
    "denied-expired-grant",
    "denied-mismatched-grant",
    "denied-operation-not-allowed",
    "denied-control-plane-write",
    "denied-unknown-schema-version",
    "denied-missing-required-field",
    "denied-unknown-authority-field",
    "denied-out-of-scope",
})

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class BrokerError(Exception):
    """Base exception for broker operations."""


class BrokerRefused(BrokerError):
    """A broker effect was refused with a stable denial code.

    ``denial_code`` is one of the strings in ``BROKER_DENIAL_CODES`` and
    carries no sensitive payload bytes, excerpts, or content-derived hashes.
    """

    def __init__(self, denial_code: str, message: str = "") -> None:
        super().__init__(message or denial_code)
        self.denial_code: str = denial_code


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BrokerGrant:
    """A broker-session grant for a set of allowed operations on declared paths.

    The broker grant narrows the parent capability grant to the subset of
    outward effects a contained child may request.  The broker validates this
    grant before performing any effect.
    """

    grant_id: str
    operations: tuple[str, ...]
    allowed_roots: tuple[str, ...]
    expires_at_monotonic: float | None = None   # None means no expiry

    def is_valid_for(self, operation: str, path: str) -> bool:
        """Return True when this grant covers *operation* on *path*."""
        if operation not in self.operations:
            return False
        path_norm = path.rstrip("/")
        return any(
            path_norm == root.rstrip("/") or path_norm.startswith(root.rstrip("/") + "/")
            for root in self.allowed_roots
        )


@dataclass(frozen=True)
class BrokerSession:
    """An active broker session that carries one or more grants.

    The session is created by the supervisor and passed to the effect broker.
    The session_id identifies the session without revealing any grant content.
    """

    session_id: str
    grants: tuple[BrokerGrant, ...]


@dataclass(frozen=True)
class BrokerResult:
    """Result of a broker effect request.

    ``success`` is True only when the effect was performed AND the audit event
    was durably emitted.  ``denial_code`` is non-None on any refusal and
    carries no payload bytes.
    """

    success: bool
    denial_code: str | None = None

    @classmethod
    def denied(cls, code: str) -> BrokerResult:
        """Convenience constructor for a denial result."""
        return cls(success=False, denial_code=code)

    @classmethod
    def allowed(cls) -> BrokerResult:
        """Convenience constructor for an allow result."""
        return cls(success=True, denial_code=None)


# ---------------------------------------------------------------------------
# Broker grant validation (schema in code)
# ---------------------------------------------------------------------------

_REQUIRED_GRANT_KEYS: Final[frozenset[str]] = frozenset({
    "grant_id",
    "operations",
    "allowed_roots",
})

_ALLOWED_GRANT_KEYS: Final[frozenset[str]] = frozenset({
    "grant_id",
    "operations",
    "allowed_roots",
    "expires_at_monotonic",
})


def validate_broker_grant_dict(d: object) -> tuple[bool, str]:
    """Validate a broker-grant record dict in code.

    Checks required fields, unknown authority-shaped fields, and operations.

    Returns:
        (True, "ok") when valid.
        (False, denial_code) when invalid; denial_code is one of:
          denied-missing-required-field — a required field is absent.
          denied-unknown-authority-field — an unknown authority-shaped field.
          denied-operation-not-allowed — the operations list is empty.
    """
    if not isinstance(d, dict):
        return False, "denied-missing-required-field"

    missing = _REQUIRED_GRANT_KEYS - set(d.keys())
    if missing:
        return False, "denied-missing-required-field"

    unknown = set(d.keys()) - _ALLOWED_GRANT_KEYS
    if unknown:
        return False, "denied-unknown-authority-field"

    ops = d.get("operations", [])
    if not isinstance(ops, (list, tuple)) or not ops:
        return False, "denied-operation-not-allowed"

    return True, "ok"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_rfc3339() -> str:
    """Return the current UTC instant as an RFC 3339 string."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_expired(grant: BrokerGrant) -> bool:
    """Return True when the broker grant has passed its expiry."""
    import time
    if grant.expires_at_monotonic is None:
        return False
    return time.monotonic() > grant.expires_at_monotonic


def _find_grant(session: BrokerSession, grant_id: str) -> BrokerGrant | None:
    """Locate a grant by ID within the session."""
    for g in session.grants:
        if g.grant_id == grant_id:
            return g
    return None


def _emit_broker_event(
    audit_sink: Callable,
    operation_id: str,
    correlation_id: str,
    outcome: str,
    reason_code: str,
) -> None:
    """Emit a broker security event to the audit sink.

    For allow events use ``_emit_allow_and_check`` instead.  Denial events
    are best-effort; the denial proceeds regardless.
    """
    import contextlib
    event = _se.SecurityEvent(  # type: ignore[attr-defined]
        schema_version=1,
        operation_id=operation_id,
        correlation_id=correlation_id,
        event_type="broker-effect",
        outcome=outcome,
        reason_code=reason_code,
        timestamp=_now_rfc3339(),
    )
    with contextlib.suppress(Exception):
        audit_sink(event)


def _emit_allow_and_check(
    audit_sink: Callable,
    operation_id: str,
    correlation_id: str,
) -> None:
    """Emit an allow event and propagate AuditSinkUnavailable as BrokerRefused.

    The event is emitted before any effect is performed (AC-0021).
    """
    event = _se.SecurityEvent(  # type: ignore[attr-defined]
        schema_version=1,
        operation_id=operation_id,
        correlation_id=correlation_id,
        event_type="broker-effect",
        outcome="allowed",
        reason_code=BROKER_ALLOW_REASON,
        timestamp=_now_rfc3339(),
    )
    try:
        _se.emit_security_event(audit_sink, event)  # type: ignore[attr-defined]
    except _se.AuditSinkUnavailable as exc:  # type: ignore[attr-defined]
        raise BrokerRefused(
            "denied-audit-sink-unavailable",
            f"audit sink unavailable before effect; failing closed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_broker_session(
    session_id: str,
    grants: list[BrokerGrant],
) -> BrokerSession:
    """Create a broker session from a list of pre-validated grants.

    The caller (supervisor) is responsible for validating each grant against
    the parent capability before creating a session.
    """
    return BrokerSession(session_id=session_id, grants=tuple(grants))


def request_effect(
    session: BrokerSession,
    *,
    grant_id: str,
    operation: str,
    path: str,
    audit_sink: Callable | None = None,
    operation_id: str | None = None,
) -> BrokerResult:
    """Request an outward effect from the broker.

    Validates the producer's grant before staging any effect (AC-0020).
    Emits a durable security event before acknowledging success (AC-0021).
    Fails closed when the audit sink is unavailable.

    Args:
        session:      The active broker session carrying the producer's grants.
        grant_id:     The ID of the grant the producer claims for this effect.
        operation:    The requested operation (e.g. "write", "read").
        path:         The target path of the effect.
        audit_sink:   Callable accepting a SecurityEvent.  ``None`` means the
                      audit sink is unavailable; the operation fails closed.
        operation_id: Stable operation ID for the audit event; generated from
                      a random token when absent.

    Returns:
        BrokerResult — ``success=True`` only when effect was performed AND
        the audit event was durably emitted; ``success=False`` with a stable
        ``denial_code`` on any refusal.
    """
    # AC-0021: unavailable sink → fail closed, no data persisted.
    if audit_sink is None:
        return BrokerResult.denied("denied-audit-sink-unavailable")

    op_id = operation_id or _se.make_operation_id()  # type: ignore[attr-defined]

    # Locate the claimed grant in the session.
    grant = _find_grant(session, grant_id)
    if grant is None:
        _emit_broker_event(
            audit_sink, op_id, grant_id, "denied", BROKER_DENY_REASON
        )
        return BrokerResult.denied("denied-missing-grant")

    # Check grant expiry (AC-0020: expired authority exposes no partial record).
    if _is_expired(grant):
        _emit_broker_event(
            audit_sink, op_id, grant_id, "denied", BROKER_DENY_REASON
        )
        return BrokerResult.denied("denied-expired-grant")

    # Validate the grant covers the requested operation and path.
    if not grant.is_valid_for(operation, path):
        _emit_broker_event(
            audit_sink, op_id, grant_id, "denied", BROKER_DENY_REASON
        )
        return BrokerResult.denied("denied-out-of-scope")

    # Guard: never permit writes to delivery-control paths via untrusted broker.
    if operation in ("write", "append", "create", "delete") and _cn.is_delivery_control_path(path):  # type: ignore[attr-defined]
        _emit_broker_event(
            audit_sink, op_id, grant_id, "denied", BROKER_DENY_REASON
        )
        return BrokerResult.denied("denied-control-plane-write")

    # AC-0021: emit the allow event BEFORE performing any effect.
    # AuditSinkUnavailable propagates as BrokerRefused.
    try:
        _emit_allow_and_check(audit_sink, op_id, grant_id)
    except BrokerRefused:
        return BrokerResult.denied("denied-audit-sink-unavailable")

    # In Slice 1, real brokered effects run only in conformance fixtures.
    # The effect is acknowledged here; the caller performs the actual I/O
    # under the primitive layer.
    return BrokerResult.allowed()
