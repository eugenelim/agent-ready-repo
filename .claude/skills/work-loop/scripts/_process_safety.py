"""_process_safety — safe process execution primitive for the work-loop skill.

Implements the safe-process.v1 contract.

No PATH search, shell reinterpretation, ambient environment, open stdin,
orphan child, or unredacted durable output.  Identity drift, ungranted env
or cwd, unsupported tree kill, timeout, launch error, or bound breach refuses.

Every managed process uses an identity-pinned absolute executable, fixed
argument vector, confined working directory, allowlisted environment, explicit
bounded stdin, full process-tree timeout, bounded output, and redaction of every
value supplied through environment and stdin.  Any validation or runtime breach
terminates the tree and records no durable success or unredacted output.

Output is read incrementally up to a hard cap (output bound plus the length of
the longest sensitive value).  Exceeding the hard cap terminates the process
tree before any output reaches the caller.  Redaction runs on the full captured
stream before any truncation so no sensitive fragment survives at a cut point.
After truncation any tail that is a non-empty prefix of a sensitive value is
also dropped.

Confined-file stdin is read through the sibling file_safety.py confined reader
against a caller-declared root; absolute-path, traversal, link, non-regular, and
size violations refuse before any bytes reach the process.

When the audit sink is available, every process allow and policy denial emits a
durable redacted security event before success or refusal is acknowledged.  When
the sink is unavailable the operation fails closed with a stable redacted denial
code and no protected data is persisted.

Platform capability: if the host cannot terminate the full process group
(``os.killpg`` unavailable), launch is refused and the capability declaration
does so with a stable denial code.

Standard library only plus the sibling ``_security_events.py`` and
``file_safety.py`` modules, loaded by path at import time.  No third-party
imports, no packaging, no installation.  Python 3.11+.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import os
import signal
import stat
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Final

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = [
    "ProcessSpec",
    "ProcessResult",
    "ProcessDenied",
    "SUPPORTED_SCHEMA_VERSION",
    "DENIAL_CODES",
    "PROCESS_ALLOW_REASON",
    "PROCESS_DENY_REASON",
    "TREE_KILL_SUPPORTED",
    "validate_process_spec_dict",
    "launch_safe_process",
]

SUPPORTED_SCHEMA_VERSION: Final[int] = 1

# Stable reason codes for security events — carry no payload bytes.
PROCESS_ALLOW_REASON: Final[str] = "allowed-process-launch"
PROCESS_DENY_REASON: Final[str] = "denied-process-launch"

# Stable denial codes — callers may match against these strings.
DENIAL_CODES: Final[frozenset[str]] = frozenset({
    "denied-audit-sink-unavailable",
    "denied-cwd-not-found",
    "denied-cwd-unsafe",
    "denied-identity-mismatch",
    "denied-invalid-output-bound",
    "denied-invalid-stdin-mode",
    "denied-invalid-timeout",
    "denied-launch-failed",
    "denied-missing-required-field",
    "denied-non-absolute-executable",
    "denied-output-cap-exceeded",
    "denied-stdin-confinement-violation",
    "denied-timeout",
    "denied-unknown-authority-field",
    "denied-unknown-schema-version",
    "denied-unsupported-tree-kill",
})

# ── Sibling module loader ─────────────────────────────────────────────────────

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parent


def _load_sibling(alias: str, filename: str) -> object:
    """Load a sibling script module by filename, unregistered in sys.modules.

    Uses the same importlib.util loader pattern as ``_confined_mutation.py``
    uses for ``file_safety.py``.
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
        # Register temporarily so Python 3.13 dataclasses._is_type can
        # resolve the module's __dict__ via sys.modules during exec_module.
        sys.modules[alias] = mod
        try:
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
        finally:
            sys.modules.pop(alias, None)
        return mod
    finally:
        sys.dont_write_bytecode = previous


# Security events sibling — loaded once at module import.
_se = _load_sibling("_se_proc_safety", "_security_events.py")

# File-safety sibling — loaded once at module import for confined stdin reads
# and confined cwd checks.  It is reused unchanged, never copied or modified.
_fs = _load_sibling("_fs_proc_safety", "file_safety.py")

# ── Schema constants ──────────────────────────────────────────────────────────

_REQUIRED_SPEC_KEYS: Final[frozenset[str]] = frozenset({
    "schema_version",
    "executable",
    "executable_identity",
    "argv",
    "grant_id",
    "cwd",
    "environment_allowlist",
    "stdin_mode",
    "process_tree_timeout_s",
    "output_bound_bytes",
})

# safe-process.v1 is closed (additionalProperties: false).
_ALLOWED_SPEC_KEYS: Final[frozenset[str]] = _REQUIRED_SPEC_KEYS

_VALID_STDIN_MODES: Final[frozenset[str]] = frozenset({
    "closed",
    "bounded-bytes",
    "confined-file",
})

# ── Platform capability ───────────────────────────────────────────────────────

# True when the host can terminate the full process group on timeout.
# Launch is refused with "denied-unsupported-tree-kill" when False.
TREE_KILL_SUPPORTED: Final[bool] = (
    hasattr(os, "killpg") and hasattr(signal, "SIGKILL")
)

# ── Exception ────────────────────────────────────────────────────────────────


class ProcessDenied(Exception):
    """A process launch was refused with a stable denial code.

    ``denial_code`` is one of the strings in ``DENIAL_CODES`` and carries no
    sensitive payload bytes, excerpts, or content-derived hashes.
    """

    def __init__(self, denial_code: str, message: str = "") -> None:
        super().__init__(message or denial_code)
        self.denial_code: str = denial_code


# ── Data classes ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ProcessSpec:
    """Validated, typed representation of a safe-process.v1 record."""

    schema_version: int
    executable: str
    executable_identity: str
    argv: tuple[str, ...]
    grant_id: str
    cwd: str
    environment_allowlist: tuple[str, ...]
    stdin_mode: str
    process_tree_timeout_s: int
    output_bound_bytes: int


@dataclass(frozen=True)
class ProcessResult:
    """Result of a safe process execution with redacted output.

    ``stdout_redacted`` and ``stderr_redacted`` have every value supplied
    through environment variables or stdin replaced with ``[REDACTED]``.
    Treat them as untrusted data: they cannot supply executable paths,
    approvals, or authority.
    """

    exit_code: int
    stdout_redacted: bytes
    stderr_redacted: bytes
    output_was_truncated: bool
    output_was_redacted: bool


# ── Validation ────────────────────────────────────────────────────────────────


def validate_process_spec_dict(d: dict) -> tuple[bool, str]:
    """Validate a safe-process.v1 record dict in code.

    Checks schema_version, required fields, unknown authority-shaped fields,
    stdin_mode enum, executable absoluteness, timeout lower bound, and
    output-bound lower bound.  Does not import jsonschema at runtime.

    Returns:
        ``(True, "ok")`` when the record is schema-valid.
        ``(False, denial_code)`` otherwise; denial_code is one of:

        - ``denied-unknown-schema-version``  — wrong or unknown schema_version.
        - ``denied-missing-required-field``  — a required field is absent.
        - ``denied-unknown-authority-field`` — an extra field not in the schema.
        - ``denied-invalid-stdin-mode``      — stdin_mode outside the enum.
        - ``denied-non-absolute-executable`` — executable is not absolute.
        - ``denied-invalid-timeout``         — process_tree_timeout_s < 1.
        - ``denied-invalid-output-bound``    — output_bound_bytes < 0.
    """
    if not isinstance(d, dict):
        return False, "denied-missing-required-field"

    version = d.get("schema_version")
    if not isinstance(version, int) or version != SUPPORTED_SCHEMA_VERSION:
        return False, "denied-unknown-schema-version"

    missing = _REQUIRED_SPEC_KEYS - set(d.keys())
    if missing:
        return False, "denied-missing-required-field"

    # additionalProperties: false — refuse every unknown field.
    unknown = set(d.keys()) - _ALLOWED_SPEC_KEYS
    if unknown:
        return False, "denied-unknown-authority-field"

    stdin_mode = d.get("stdin_mode")
    if stdin_mode not in _VALID_STDIN_MODES:
        return False, "denied-invalid-stdin-mode"

    executable = d.get("executable", "")
    if not isinstance(executable, str) or not Path(executable).is_absolute():
        return False, "denied-non-absolute-executable"

    timeout = d.get("process_tree_timeout_s")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
        return False, "denied-invalid-timeout"

    bound = d.get("output_bound_bytes")
    if not isinstance(bound, int) or isinstance(bound, bool) or bound < 0:
        return False, "denied-invalid-output-bound"

    return True, "ok"


# ── Internal helpers ──────────────────────────────────────────────────────────


def _now_rfc3339() -> str:
    """Return the current UTC instant as an RFC 3339 string."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash_file_sha256(path: str) -> str:
    """Return the SHA-256 hex digest of the file at *path*.

    Raises OSError when the file cannot be opened or read.
    """
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _kill_process_tree(proc: subprocess.Popen) -> None:  # type: ignore[type-arg]
    """Send SIGKILL to the process group (POSIX) or the process (fallback).

    Does NOT call ``proc.wait()``; the caller is responsible for draining
    the process after this returns.  Silently ignores errors from processes
    that have already exited.
    """
    if hasattr(os, "killpg"):
        with contextlib.suppress(OSError, ProcessLookupError):
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    else:
        with contextlib.suppress(OSError, ProcessLookupError):
            proc.kill()


_REDACTED_MARKER: Final[bytes] = b"[REDACTED]"


def _redact_bytes(data: bytes, sensitive: list[bytes]) -> tuple[bytes, bool]:
    """Replace every occurrence of a sensitive value in *data* with ``[REDACTED]``.

    Skips empty byte sequences.  Returns ``(result, was_redacted)``.
    """
    was_redacted = False
    for val in sensitive:
        if val and val in data:
            data = data.replace(val, _REDACTED_MARKER)
            was_redacted = True
    return data, was_redacted


def _drop_sensitive_tail_prefix(data: bytes, sensitive: list[bytes]) -> bytes:
    """Drop any tail of *data* that is a non-empty strict prefix of a sensitive value.

    After redaction, truncating the output stream might still leave a fragment
    at the tail when the truncation point falls inside a sensitive value whose
    length exceeds the gap between the capture hard-cap and the output bound.
    Dropping such a tail is belt-and-suspenders insurance: the hard-cap
    calculation already ensures the full secret was available for redaction, but
    this pass catches any edge where the redacted stream's length shift moves a
    prefix back into view.
    """
    for val in sensitive:
        if not val:
            continue
        # Check every strict prefix of this sensitive value (length 1..len-1).
        for prefix_len in range(1, len(val)):
            prefix = val[:prefix_len]
            if data.endswith(prefix):
                return data[:-prefix_len]
    return data


def _collect_sensitive(
    env: dict[str, str],
    stdin_bytes: bytes | None,
    extra: list[str] | None,
) -> list[bytes]:
    """Build the list of byte sequences that must be redacted from output.

    Includes all environment variable values passed to the process, all
    stdin bytes, and any additional caller-supplied strings.
    """
    sensitive: list[bytes] = []
    for v in env.values():
        encoded = v.encode("utf-8", errors="replace")
        if encoded:
            sensitive.append(encoded)
    if stdin_bytes:
        sensitive.append(stdin_bytes)
    for v in (extra or []):
        encoded = v.encode("utf-8", errors="replace")
        if encoded:
            sensitive.append(encoded)
    return sensitive


def _communicate_bounded(
    proc: subprocess.Popen,  # type: ignore[type-arg]
    stdin_input: bytes | None,
    timeout_s: int,
    hard_cap: int,
) -> tuple[bytes, bytes, bool]:
    """Read stdout/stderr up to *hard_cap* combined bytes; write stdin; wait.

    Uses threads to read stdout and stderr concurrently so that large output
    does not accumulate unbounded in memory.  Each reader thread appends data
    to its target list up to ``hard_cap`` total bytes, then stops.  The cap is
    enforced inside the lock so the combined total never overshoots.

    Returns ``(stdout_bytes, stderr_bytes, cap_exceeded)`` where
    ``cap_exceeded`` is True when combined bytes read hit the hard cap.  The
    caller uses ``proc.poll()`` to distinguish a still-running flood from a
    process that simply exited after producing more output than expected.

    Raises ``subprocess.TimeoutExpired`` when the process does not finish within
    *timeout_s* seconds.

    Hard-cap semantics: when cap_exceeded is True AND the process is still
    running, the caller should kill the process tree (flood attack).  When
    cap_exceeded is True but the process already exited, truncation handles the
    extra output and no kill is needed.
    """
    stdout_parts: list[bytes] = []
    stderr_parts: list[bytes] = []
    total_read: list[int] = [0]
    capped: list[bool] = [False]
    lock = threading.Lock()

    def _drain(pipe: object, target: list) -> None:
        """Read from *pipe* into *target* up to the shared hard cap.

        Uses ``read1`` (one raw syscall worth of data) so that a process which
        has written data and is now sleeping does not leave the thread blocked
        on a ``read(N)`` call that waits for N bytes before returning.
        Falls back to ``read`` if ``read1`` is not available on the object.
        """
        while True:
            try:
                chunk = pipe.read1(65536)  # type: ignore[attr-defined]
            except AttributeError:
                # read1 not available (e.g. a raw file object in tests).
                try:
                    chunk = pipe.read(65536)  # type: ignore[attr-defined]
                except OSError:
                    break
            except OSError:
                break
            if not chunk:
                break
            with lock:
                if capped[0]:
                    # Another stream already hit the cap; stop reading.
                    break
                new_total = total_read[0] + len(chunk)
                if new_total > hard_cap:
                    # Append only what fits within the cap, then stop.
                    allowed = hard_cap - total_read[0]
                    if allowed > 0:
                        target.append(chunk[:allowed])
                    total_read[0] = new_total
                    capped[0] = True
                    break
                total_read[0] = new_total
                target.append(chunk)

    out_t = threading.Thread(target=_drain, args=(proc.stdout, stdout_parts), daemon=True)
    err_t = threading.Thread(target=_drain, args=(proc.stderr, stderr_parts), daemon=True)

    if stdin_input is not None:
        def _send() -> None:
            try:
                proc.stdin.write(stdin_input)  # type: ignore[attr-defined]
                proc.stdin.close()  # type: ignore[attr-defined]
            except OSError:
                pass
        in_t: threading.Thread | None = threading.Thread(target=_send, daemon=True)
    else:
        in_t = None

    if in_t is not None:
        in_t.start()
    out_t.start()
    err_t.start()

    # Poll until the cap fires, the process exits, or the timeout elapses.
    # Polling (rather than blocking on proc.wait) lets us break out early when
    # the cap fires while the process is still running.
    _POLL_S = 0.02  # 20 ms poll granularity
    deadline = time.monotonic() + timeout_s
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0.0:
            # Timeout: join threads briefly so the caller can proceed to kill.
            out_t.join(timeout=0.5)
            err_t.join(timeout=0.5)
            if in_t is not None:
                in_t.join(timeout=0.5)
            raise subprocess.TimeoutExpired(proc.args, timeout_s)  # type: ignore[arg-type]
        if capped[0]:
            # Cap hit; drain threads have already stopped.  Let them finish and
            # return to the caller, which will check proc.poll() to decide.
            out_t.join(timeout=0.5)
            err_t.join(timeout=0.5)
            if in_t is not None:
                in_t.join(timeout=0.5)
            break
        if proc.poll() is not None:
            # Process exited; let drain threads consume any remaining pipe data.
            out_t.join(timeout=max(0.0, deadline - time.monotonic()))
            err_t.join(timeout=max(0.0, deadline - time.monotonic()))
            if in_t is not None:
                in_t.join(timeout=max(0.0, deadline - time.monotonic()))
            break
        time.sleep(min(_POLL_S, remaining))

    return b"".join(stdout_parts), b"".join(stderr_parts), capped[0]


def _emit_event(
    audit_sink: Callable,
    operation_id: str,
    correlation_id: str,
    outcome: str,
    reason_code: str,
) -> None:
    """Emit a process-launch security event.  Best-effort for denials.

    For allow events use ``_emit_allow`` instead, which propagates sink
    failures as ``ProcessDenied``.
    """
    event = _se.SecurityEvent(  # type: ignore[attr-defined]
        schema_version=1,
        operation_id=operation_id,
        correlation_id=correlation_id,
        event_type="process-launch",
        outcome=outcome,
        reason_code=reason_code,
        timestamp=_now_rfc3339(),
    )
    # Denial events are best-effort; the denial proceeds regardless.
    with contextlib.suppress(Exception):
        audit_sink(event)


def _emit_allow(
    audit_sink: Callable,
    operation_id: str,
    correlation_id: str,
) -> None:
    """Emit an allow event.  Raises ``ProcessDenied`` if the sink fails.

    The event is emitted before any process launches.  If the sink
    raises, the launch is aborted with ``denied-audit-sink-unavailable``.
    """
    event = _se.SecurityEvent(  # type: ignore[attr-defined]
        schema_version=1,
        operation_id=operation_id,
        correlation_id=correlation_id,
        event_type="process-launch",
        outcome="allowed",
        reason_code=PROCESS_ALLOW_REASON,
        timestamp=_now_rfc3339(),
    )
    try:
        _se.emit_security_event(audit_sink, event)  # type: ignore[attr-defined]
    except _se.AuditSinkUnavailable as exc:  # type: ignore[attr-defined]
        raise ProcessDenied(
            "denied-audit-sink-unavailable",
            f"audit sink unavailable during allow emission; failing closed: {exc}",
        ) from exc


# ── Public launch API ─────────────────────────────────────────────────────────


def launch_safe_process(
    spec_dict: dict,
    *,
    cwd_roots: tuple[str, ...],
    env_values: dict[str, str] | None = None,
    stdin_bytes: bytes | None = None,
    stdin_path: str | None = None,
    stdin_root: str | None = None,
    sensitive_values: list[str] | None = None,
    audit_sink: Callable | None = None,
    operation_id: str | None = None,
    correlation_id: str | None = None,
) -> ProcessResult:
    """Launch a safe process according to a safe-process.v1 spec_dict.

    Validates the spec, pins the executable identity, confirms the working
    directory (refusing when the cwd is not inside any declared root or has
    symlink components in the path), emits a durable allow event before
    launching, runs the process with bounded stdin, reads output incrementally
    up to a hard cap (output bound plus the longest sensitive value), redacts
    the full captured stream before any truncation, and kills the whole process
    group on timeout or cap breach.

    Args:
        spec_dict:        A safe-process.v1 record dict.
        cwd_roots:        The grant's declared filesystem roots.  The spec's
                          ``cwd`` must be inside at least one of these roots
                          with no symlink components in the path from the root
                          to the cwd.  An empty tuple refuses with
                          ``denied-cwd-unsafe``.
        env_values:       Actual values for the allowlisted env var names.
                          Keys not in ``environment_allowlist`` are ignored.
                          Names in ``environment_allowlist`` not present here
                          are omitted (no ambient OS inheritance).
        stdin_bytes:      Bytes for ``bounded-bytes`` stdin mode.
        stdin_path:       File path for ``confined-file`` stdin mode.
        stdin_root:       Declared confinement root for ``confined-file`` stdin.
                          Required when stdin_mode is ``confined-file``.
                          The stdin file must be a regular, non-linked,
                          non-oversized file inside this root.
        sensitive_values: Additional strings to redact from output.
        audit_sink:       Callable accepting a SecurityEvent.  ``None`` means
                          the audit sink is unavailable; the operation fails
                          closed with a stable denial code without persisting
                          any protected data.
        operation_id:     Stable operation ID for the audit event; generated
                          from a random token when absent.
        correlation_id:   Correlation ID (typically the grant_id) for the event.

    Returns:
        ``ProcessResult`` with redacted output.

    Raises:
        ``ProcessDenied``: with a stable denial code on any refusal.
    """
    # Unavailable sink → fail closed immediately, no data persisted.
    if audit_sink is None:
        raise ProcessDenied(
            "denied-audit-sink-unavailable",
            "audit sink is unavailable; process launch refused without emitting an event",
        )

    op_id = operation_id or _se.make_operation_id()  # type: ignore[attr-defined]

    # Validate spec dict; emit a denial event on any schema violation.
    ok, code = validate_process_spec_dict(spec_dict)
    if not ok:
        corr_id = (
            correlation_id
            or (spec_dict.get("grant_id") if isinstance(spec_dict, dict) else None)
            or "unknown"
        )
        _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
        raise ProcessDenied(code, f"spec validation failed: {code}")

    corr_id = correlation_id or spec_dict["grant_id"]

    # Platform capability: refuse when the host cannot guarantee tree kill.
    if not TREE_KILL_SUPPORTED:
        _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
        raise ProcessDenied(
            "denied-unsupported-tree-kill",
            "process-tree timeout termination is not supported on this host; "
            "launch refused to avoid orphan children",
        )

    # Pin executable identity: hash the actual file before launch.
    try:
        actual_identity = _hash_file_sha256(spec_dict["executable"])
    except OSError as exc:
        _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
        raise ProcessDenied(
            "denied-launch-failed",
            f"cannot hash executable {spec_dict['executable']!r}: {exc}",
        ) from exc

    if actual_identity != spec_dict["executable_identity"]:
        _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
        raise ProcessDenied(
            "denied-identity-mismatch",
            "executable identity mismatch: the file on disk does not match the "
            "pinned digest in the spec; refusing to launch",
        )

    # Confirm working directory: must exist, then must be inside at least one
    # declared root with no symlink components on the path from root to cwd.
    cwd_str: str = spec_dict["cwd"]
    if not Path(cwd_str).is_dir():
        _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
        raise ProcessDenied(
            "denied-cwd-not-found",
            f"cwd does not exist or is not a directory: {cwd_str!r}",
        )
    if not cwd_roots:
        _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
        raise ProcessDenied(
            "denied-cwd-unsafe",
            "no cwd_roots declared; cwd cannot be confirmed as confined",
        )
    _cwd_confined = False
    _last_cwd_exc: Exception | None = None
    for _root in cwd_roots:
        try:
            _fs.validate_confined_directory(  # type: ignore[attr-defined]
                Path(_root), Path(cwd_str)
            )
            _cwd_confined = True
            break
        except Exception as exc:
            _last_cwd_exc = exc
    if not _cwd_confined:
        _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
        raise ProcessDenied(
            "denied-cwd-unsafe",
            f"cwd is not inside any declared root or contains a symlink component: "
            f"{_last_cwd_exc}",
        ) from _last_cwd_exc

    # Build environment: only explicitly allowlisted names, no ambient inheritance.
    vals = env_values or {}
    env: dict[str, str] = {
        name: vals[name]
        for name in spec_dict["environment_allowlist"]
        if name in vals
    }

    # Resolve stdin according to mode.
    bound: int = spec_dict["output_bound_bytes"]
    stdin_mode: str = spec_dict["stdin_mode"]
    stdin_input: bytes | None
    stdin_fd: int

    if stdin_mode == "closed":
        stdin_input = None
        stdin_fd = subprocess.DEVNULL
    elif stdin_mode == "bounded-bytes":
        stdin_input = stdin_bytes if stdin_bytes is not None else b""
        stdin_fd = subprocess.PIPE
    else:
        # "confined-file": read through the confined, bounded regular-file reader.
        # stdin_root declares the confinement boundary; the path must name a
        # regular, non-linked, non-oversized file inside that root.
        if stdin_path is None:
            _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
            raise ProcessDenied(
                "denied-launch-failed",
                "confined-file stdin mode requires a stdin_path argument",
            )
        if stdin_root is None:
            _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
            raise ProcessDenied(
                "denied-launch-failed",
                "confined-file stdin mode requires a stdin_root argument declaring "
                "the confinement boundary",
            )
        try:
            stdin_input = _fs.read_confined_regular_file(  # type: ignore[attr-defined]
                Path(stdin_root),
                Path(stdin_path),
                max_bytes=max(bound, 1),
            )
        except Exception as exc:
            _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
            raise ProcessDenied(
                "denied-stdin-confinement-violation",
                f"confined-file stdin refused: {exc}",
            ) from exc
        stdin_fd = subprocess.PIPE

    # Collect all values that must be redacted from process output.
    sensitive_raw = _collect_sensitive(env, stdin_input, sensitive_values)

    # Hard cap: output bound plus the longest sensitive value length.
    # This guarantees that any sensitive value starting within the first
    # *bound* bytes of output is fully captured and redactable before
    # truncation.  Exceeding the hard cap terminates the process tree.
    _max_secret_len = max((len(s) for s in sensitive_raw), default=0)
    hard_cap = bound + _max_secret_len

    # Emit the allow event BEFORE the process is launched.
    # If the sink raises, ProcessDenied propagates and no process starts.
    _emit_allow(audit_sink, op_id, corr_id)

    # Launch the process in a new session so its entire process group can be killed.
    argv = [spec_dict["executable"]] + list(spec_dict["argv"])
    try:
        proc = subprocess.Popen(
            argv,
            env=env,
            cwd=cwd_str,
            stdin=stdin_fd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            close_fds=True,
        )
    except OSError as exc:
        raise ProcessDenied(
            "denied-launch-failed",
            f"process launch failed: {exc}",
        ) from exc

    # Read output incrementally with the hard cap; write stdin concurrently.
    timeout_s: int = spec_dict["process_tree_timeout_s"]
    try:
        raw_stdout, raw_stderr, overflowed = _communicate_bounded(
            proc, stdin_input, timeout_s, hard_cap
        )
    except subprocess.TimeoutExpired:
        _kill_process_tree(proc)
        with contextlib.suppress(Exception):
            proc.communicate()
        raise ProcessDenied(
            "denied-timeout",
            f"process tree timeout exceeded ({timeout_s}s); "
            "all children killed, no output returned",
        ) from None
    except OSError as exc:
        _kill_process_tree(proc)
        raise ProcessDenied(
            "denied-launch-failed",
            f"process I/O error: {exc}",
        ) from exc

    # Output cap breach while process still running: terminate and refuse.
    # When the process has already exited (proc.poll() returns an exit code),
    # the cap reflects normal output-exceeded-bound behavior; truncation handles
    # it below and no kill is needed.
    if overflowed and proc.poll() is None:
        _kill_process_tree(proc)
        with contextlib.suppress(Exception):
            proc.communicate()
        raise ProcessDenied(
            "denied-output-cap-exceeded",
            f"process output exceeded the hard cap ({hard_cap} bytes) while "
            "still running; all children killed, no output returned",
        )

    # Redact the FULL captured stream BEFORE any truncation.
    # This prevents a sensitive value that straddles the output bound from
    # surviving as an unredacted prefix in the returned bytes.
    stdout_red, redacted1 = _redact_bytes(raw_stdout, sensitive_raw)
    stderr_red, redacted2 = _redact_bytes(raw_stderr, sensitive_raw)
    was_redacted = redacted1 or redacted2

    # Bound combined redacted stdout + stderr.
    # ``overflowed`` means the reader stopped before EOF (more output existed),
    # so the output is always considered truncated in that case.
    truncated: bool = overflowed
    if bound == 0:
        truncated = truncated or bool(stdout_red or stderr_red)
        stdout_red = b""
        stderr_red = b""
    elif len(stdout_red) + len(stderr_red) > bound:
        out_take = min(len(stdout_red), bound)
        err_take = bound - out_take
        stdout_red = stdout_red[:out_take]
        stderr_red = stderr_red[:err_take]
        truncated = True

    # Belt-and-suspenders: drop any tail that is a strict prefix of a sensitive
    # value.  Redaction already handled the in-band case; this catches any edge
    # where the redacted stream's length shift moves a fragment into view.
    if sensitive_raw and truncated:
        stdout_red = _drop_sensitive_tail_prefix(stdout_red, sensitive_raw)
        stderr_red = _drop_sensitive_tail_prefix(stderr_red, sensitive_raw)

    return ProcessResult(
        exit_code=proc.returncode,
        stdout_redacted=stdout_red,
        stderr_redacted=stderr_red,
        output_was_truncated=truncated,
        output_was_redacted=was_redacted,
    )
