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
    "MAX_STDIN_BYTES",
    "validate_process_spec_dict",
    "launch_safe_process",
]

SUPPORTED_SCHEMA_VERSION: Final[int] = 1

# Stable reason codes for security events — carry no payload bytes.
PROCESS_ALLOW_REASON: Final[str] = "allowed-process-launch"
PROCESS_DENY_REASON: Final[str] = "denied-process-launch"

# Hard ceiling for bounded-bytes stdin.  1 MiB is generous for structured
# data payloads while blocking run-away allocations; confined-file mode
# uses a separate per-call bound declared by the caller.
MAX_STDIN_BYTES: Final[int] = 1 * 1024 * 1024  # 1 MiB

# Stable denial codes — callers may match against these strings.
DENIAL_CODES: Final[frozenset[str]] = frozenset({
    "denied-audit-sink-unavailable",
    "denied-cwd-not-found",
    "denied-cwd-unsafe",
    "denied-executable-identity-changed",
    "denied-identity-mismatch",
    "denied-invalid-field-value",
    "denied-invalid-output-bound",
    "denied-invalid-stdin-mode",
    "denied-invalid-timeout",
    "denied-launch-failed",
    "denied-missing-required-field",
    "denied-non-absolute-executable",
    "denied-output-cap-exceeded",
    "denied-stdin-bound-exceeded",
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

# Upper bound for executable binary size.  256 MiB accommodates any realistic
# system binary (Python: ~20 MiB, git: ~10 MiB) while blocking oversized files
# that could exhaust memory or indicate a confused-deputy attack.
_MAX_EXECUTABLE_BYTES: Final[int] = 256 * 1024 * 1024

# ── Platform capability ───────────────────────────────────────────────────────

# True when the host can terminate the full process group on timeout.
# Launch is refused with "denied-unsupported-tree-kill" when False.
TREE_KILL_SUPPORTED: Final[bool] = (
    hasattr(os, "killpg") and hasattr(signal, "SIGKILL")
)

# True when /proc/self/fd is available for fd-based exec.
# On Linux, Popen executes the verified descriptor directly via
# executable="/proc/self/fd/<n>" + pass_fds=(n,), so the kernel runs exactly
# the inode that was hashed — no TOCTOU window between verification and exec.
# Elsewhere (macOS, …) a path-based exec is used with a final identity re-check.
_USE_PROC_FD: Final[bool] = (
    sys.platform.startswith("linux") and Path("/proc/self/fd").is_dir()
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


def validate_process_spec_dict(d: object) -> tuple[bool, str]:
    """Validate *d* without ever raising: any unexpected value refuses.

    A record of any shape returns a stable denial code instead of an
    exception, so every caller can audit the refusal.
    """
    try:
        return _validate_process_spec_dict_checked(d)
    except Exception:  # noqa: BLE001 — validation must never raise
        return False, "denied-invalid-field-value"


def _validate_process_spec_dict_checked(d: object) -> tuple[bool, str]:
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
    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or version != SUPPORTED_SCHEMA_VERSION
    ):
        return False, "denied-unknown-schema-version"

    missing = _REQUIRED_SPEC_KEYS - set(d.keys())
    if missing:
        return False, "denied-missing-required-field"

    # additionalProperties: false — refuse every unknown field.
    unknown = set(d.keys()) - _ALLOWED_SPEC_KEYS
    if unknown:
        return False, "denied-unknown-authority-field"

    stdin_mode = d.get("stdin_mode")
    if not isinstance(stdin_mode, str) or stdin_mode not in _VALID_STDIN_MODES:
        return False, "denied-invalid-stdin-mode"

    executable = d.get("executable", "")
    if not isinstance(executable, str) or not Path(executable).is_absolute():
        return False, "denied-non-absolute-executable"
    # A NUL byte in the executable path terminates the C-string at the OS
    # boundary, silently truncating the path and defeating identity pinning.
    if "\x00" in executable:
        return False, "denied-invalid-field-value"

    # These identifiers reach the filesystem and the audit trail, so each must
    # be a non-empty string without NUL before any filesystem call.
    for field in ("cwd", "grant_id", "executable_identity"):
        value = d.get(field)
        if not isinstance(value, str) or not value or "\x00" in value:
            return False, "denied-invalid-field-value"

    # argv must be a list of strings; a bare string turns into single-char args.
    argv_val = d.get("argv")
    if not isinstance(argv_val, list) or not all(isinstance(i, str) for i in argv_val):
        return False, "denied-invalid-field-value"
    # A NUL byte in any argv item terminates the C-string at the OS boundary,
    # silently splitting or truncating the argument.
    if any("\x00" in item for item in argv_val):
        return False, "denied-invalid-field-value"

    # environment_allowlist must be a list of strings with no '=' or NUL,
    # which would corrupt or escape the environment key on POSIX.
    env_allowlist = d.get("environment_allowlist")
    if not isinstance(env_allowlist, list):
        return False, "denied-invalid-field-value"
    for _env_name in env_allowlist:
        if (
            not isinstance(_env_name, str)
            or not _env_name
            or "=" in _env_name
            or "\x00" in _env_name
        ):
            return False, "denied-invalid-field-value"

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


def _open_and_verify_executable(path: str) -> tuple[str, int, int, int]:
    """Open *path* without following links, verify it, and hash it.

    Opens with O_RDONLY|O_NOFOLLOW|O_NONBLOCK so that:
    - a symlink at the final path component is refused (ELOOP / ENOTDIR);
    - a FIFO does not block the open call (O_NONBLOCK on open; no effect on
      reads from regular files).

    After a successful open, fstat verifies:
    - the target is a regular file (S_ISREG);
    - the file size is within _MAX_EXECUTABLE_BYTES (256 MiB).

    The SHA-256 is computed by reading from the open descriptor.  The inode
    identity (st_dev, st_ino) is recorded so the caller can detect a swap
    between verification and exec.

    Platform-specific exec guarantee:
    - Linux with /proc/self/fd (_USE_PROC_FD is True): the file descriptor is
      kept open and returned.  The caller executes
      ``executable="/proc/self/fd/<n>"`` with ``pass_fds=(n,)`` so the kernel
      runs exactly the inode that was hashed — no TOCTOU window.
    - Elsewhere (macOS and others): the descriptor is closed before this
      function returns (returned fd is -1).  The caller performs a final
      ``os.stat(path, follow_symlinks=False)`` immediately before Popen and
      refuses if the inode identity has changed.  A narrow TOCTOU window
      remains on these platforms; exploiting it requires write access to the
      executable's directory.

    Returns:
        (hex_digest, fd_or_neg1, st_dev, st_ino) — SHA-256 hex digest, open
        descriptor or -1, device number, inode number.

    Raises:
        OSError: when the file cannot be opened, is not a regular file, or
                 exceeds _MAX_EXECUTABLE_BYTES.
    """
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    src_fd = os.open(path, flags)
    try:
        info = os.fstat(src_fd)
        if not stat.S_ISREG(info.st_mode):
            raise OSError(
                f"executable is not a regular file "
                f"(mode {oct(info.st_mode)}): {path!r}"
            )
        if info.st_size > _MAX_EXECUTABLE_BYTES:
            raise OSError(
                f"executable size {info.st_size} bytes exceeds ceiling of "
                f"{_MAX_EXECUTABLE_BYTES} bytes: {path!r}"
            )
        st_dev = info.st_dev
        st_ino = info.st_ino
        # Hash the file content from the open descriptor.
        h = hashlib.sha256()
        while True:
            chunk = os.read(src_fd, 65536)
            if not chunk:
                break
            h.update(chunk)
        hex_digest = h.hexdigest()
    except Exception:
        os.close(src_fd)
        raise

    # On Linux with /proc/self/fd: keep the descriptor open for fd-based exec.
    if _USE_PROC_FD:
        return hex_digest, src_fd, st_dev, st_ino

    # Elsewhere: close now; the caller re-checks identity right before Popen.
    os.close(src_fd)
    return hex_digest, -1, st_dev, st_ino


def _kill_process_tree(proc: subprocess.Popen) -> None:  # type: ignore[type-arg]
    """Send SIGKILL to the process group (POSIX) or the process (fallback).

    Does NOT call ``proc.wait()``; the caller is responsible for draining
    the process after this returns.  Silently ignores errors from processes
    that have already exited.

    Because every managed launch uses ``start_new_session=True``, the
    process-group ID equals ``proc.pid``.  Using ``proc.pid`` directly
    avoids an ``os.getpgid`` call that fails once the leader is reaped.
    """
    if hasattr(os, "killpg"):
        with contextlib.suppress(OSError, ProcessLookupError, PermissionError):
            os.killpg(proc.pid, signal.SIGKILL)
    else:
        with contextlib.suppress(OSError, ProcessLookupError, PermissionError):
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


def _leader_exited(proc: subprocess.Popen) -> bool:  # type: ignore[type-arg]
    """Return whether the group leader has exited, without reaping it.

    Leaving the leader unreaped keeps its PID, and so the launch's process
    group ID, reserved until the caller signals the group; a reaped ID could
    be reused by an unrelated group.  Falls back to ``poll()`` (which reaps)
    where ``waitid`` with ``WNOWAIT`` is unavailable.
    """
    if proc.returncode is not None:
        return True
    if hasattr(os, "waitid") and hasattr(os, "WNOWAIT"):
        try:
            info = os.waitid(
                os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT
            )
        except ChildProcessError:
            return True
        return info is not None
    return proc.poll() is not None


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
        if _leader_exited(proc):
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
    _se.emit_denial_best_effort(audit_sink, event)  # type: ignore[attr-defined]


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
    except Exception as exc:  # noqa: BLE001 — any sink failure from any module load
        raise ProcessDenied(
            "denied-audit-sink-unavailable",
            "audit sink unavailable during allow emission; failing closed",
        ) from exc


# ── Public launch API ─────────────────────────────────────────────────────────


def _safe_correlation(*candidates: object) -> str:
    """Return the first candidate that is a non-empty string, else ``"unknown"``.

    Keeps every stored event's correlation ID a schema-valid string whatever a
    caller passed.
    """
    for value in candidates:
        if isinstance(value, str) and value:
            return value
    return "unknown"


def launch_safe_process(
    spec_dict: dict,
    *,
    cwd_roots: tuple[str, ...],
    env_values: dict[str, str] | None = None,
    stdin_bytes: bytes | None = None,
    stdin_path: str | None = None,
    stdin_root: str | None = None,
    stdin_bound_bytes: int | None = None,
    sensitive_values: list[str] | None = None,
    audit_sink: Callable | None = None,
    operation_id: str | None = None,
    correlation_id: str | None = None,
) -> ProcessResult:
    """Launch a safe process according to a safe-process.v1 spec_dict.

    A guard around the launch steps: a ``ProcessDenied`` passes through, and
    any other exception from any step becomes an audited ``ProcessDenied``
    with a stable code, so no refusal leaves without a stored denial event.
    See ``_launch_safe_process_unguarded`` for the full contract.
    """
    try:
        return _launch_safe_process_unguarded(
            spec_dict,
            cwd_roots=cwd_roots,
            env_values=env_values,
            stdin_bytes=stdin_bytes,
            stdin_path=stdin_path,
            stdin_root=stdin_root,
            stdin_bound_bytes=stdin_bound_bytes,
            sensitive_values=sensitive_values,
            audit_sink=audit_sink,
            operation_id=operation_id,
            correlation_id=correlation_id,
        )
    except ProcessDenied:
        raise
    except Exception:  # noqa: BLE001 — any unexpected failure refuses, audited
        if audit_sink is not None:
            grant_id = spec_dict.get("grant_id") if isinstance(spec_dict, dict) else None
            _emit_event(
                audit_sink,
                operation_id if isinstance(operation_id, str) and operation_id
                else _se.make_operation_id(),  # type: ignore[attr-defined]
                _safe_correlation(correlation_id, grant_id),
                "denied",
                PROCESS_DENY_REASON,
            )
        raise ProcessDenied(
            "denied-launch-failed",
            "process launch failed before completion; refusing",
        ) from None


def _launch_safe_process_unguarded(
    spec_dict: dict,
    *,
    cwd_roots: tuple[str, ...],
    env_values: dict[str, str] | None = None,
    stdin_bytes: bytes | None = None,
    stdin_path: str | None = None,
    stdin_root: str | None = None,
    stdin_bound_bytes: int | None = None,
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
        spec_dict:         A safe-process.v1 record dict.
        cwd_roots:         The grant's declared filesystem roots.  The spec's
                           ``cwd`` must be inside at least one of these roots
                           with no symlink components in the path from the root
                           to the cwd.  An empty tuple refuses with
                           ``denied-cwd-unsafe``.
        env_values:        Actual values for the allowlisted env var names.
                           Keys not in ``environment_allowlist`` are ignored.
                           Names in ``environment_allowlist`` not present here
                           are omitted (no ambient OS inheritance).
        stdin_bytes:       Bytes for ``bounded-bytes`` stdin mode.
        stdin_path:        File path for ``confined-file`` stdin mode.
        stdin_root:        Declared confinement root for ``confined-file`` stdin.
                           Required when stdin_mode is ``confined-file``.
                           The stdin file must be a regular, non-linked,
                           non-oversized file inside this root.
        stdin_bound_bytes: Optional caller-declared ceiling for ``bounded-bytes``
                           stdin, in bytes.  Must be between 1 and
                           ``MAX_STDIN_BYTES`` (inclusive); a value outside that
                           range is refused with ``denied-stdin-bound-exceeded``
                           before launch.  When ``None``, ``MAX_STDIN_BYTES``
                           applies.  This parameter may only lower the ceiling;
                           it cannot raise it above ``MAX_STDIN_BYTES``.
        sensitive_values:  Additional strings to redact from output.
        audit_sink:        Callable accepting a SecurityEvent.  ``None`` means
                           the audit sink is unavailable; the operation fails
                           closed with a stable denial code without persisting
                           any protected data.
        operation_id:      Stable operation ID for the audit event; generated
                           from a random token when absent.
        correlation_id:    Correlation ID (typically the grant_id) for the event.

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

    op_id = (
        operation_id
        if isinstance(operation_id, str) and operation_id
        else _se.make_operation_id()  # type: ignore[attr-defined]
    )

    # Validate spec dict; emit a denial event on any schema violation.
    ok, code = validate_process_spec_dict(spec_dict)
    if not ok:
        corr_id = _safe_correlation(
            correlation_id,
            spec_dict.get("grant_id") if isinstance(spec_dict, dict) else None,
        )
        _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
        raise ProcessDenied(code, f"spec validation failed: {code}")

    corr_id = _safe_correlation(correlation_id, spec_dict["grant_id"])

    # Validate caller-declared stdin ceiling before any further checks.
    # stdin_bound_bytes may only lower MAX_STDIN_BYTES; a value above the
    # ceiling or <= 0 is refused so callers cannot inadvertently widen it.
    _effective_stdin_ceiling: int = MAX_STDIN_BYTES
    if stdin_bound_bytes is not None:
        if stdin_bound_bytes <= 0 or stdin_bound_bytes > MAX_STDIN_BYTES:
            _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
            raise ProcessDenied(
                "denied-stdin-bound-exceeded",
                f"stdin_bound_bytes must be between 1 and {MAX_STDIN_BYTES} (inclusive); "
                f"got {stdin_bound_bytes}",
            )
        _effective_stdin_ceiling = stdin_bound_bytes

    # Platform capability: refuse when the host cannot guarantee tree kill.
    if not TREE_KILL_SUPPORTED:
        _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
        raise ProcessDenied(
            "denied-unsupported-tree-kill",
            "process-tree timeout termination is not supported on this host; "
            "launch refused to avoid orphan children",
        )

    # Pin executable identity: open without following links (O_NOFOLLOW),
    # refuse non-regular files (fstat S_ISREG), enforce the 256 MiB size
    # ceiling, and hash the content from the open descriptor.  The exec
    # mechanism is platform-specific (see _open_and_verify_executable).
    exec_fd: int = -1  # descriptor kept open on Linux; -1 on macOS/others
    try:
        actual_identity, exec_fd, exec_dev, exec_ino = _open_and_verify_executable(
            spec_dict["executable"]
        )
    except OSError as exc:
        _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
        raise ProcessDenied(
            "denied-launch-failed",
            f"cannot open or verify executable {spec_dict['executable']!r}: {exc}",
        ) from exc
    except Exception:
        # Any non-OSError (e.g. ValueError from a NUL that passed schema
        # validation through another path) must also store a denial event and
        # surface as ProcessDenied without leaking exception text.
        _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
        raise ProcessDenied(
            "denied-launch-failed",
            "cannot open or verify executable",
        ) from None

    # The open descriptor (Linux) must be closed after Popen starts.
    # This try/finally ensures closure even when validation or Popen raise.
    try:
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

        # Refuse a NUL byte in any supplied environment value before the allow
        # event.  A NUL terminates the C-string at the OS boundary, silently
        # truncating the value and potentially hiding injected content.
        for _env_val in env.values():
            if isinstance(_env_val, str) and "\x00" in _env_val:
                _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
                raise ProcessDenied(
                    "denied-invalid-field-value",
                    "environment value contains an invalid character",
                )

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
            if len(stdin_input) > _effective_stdin_ceiling:
                _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
                raise ProcessDenied(
                    "denied-stdin-bound-exceeded",
                    f"bounded-bytes stdin exceeds the ceiling of {_effective_stdin_ceiling} bytes "
                    f"({len(stdin_input)} bytes supplied); refusing before process launch",
                )
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

        # Launch the process in a new session so its entire process group can be
        # killed.  The exec mechanism depends on platform (see _USE_PROC_FD):
        # - Linux (/proc/self/fd available): execute the verified descriptor
        #   directly so the kernel runs exactly the inode that was hashed.
        # - macOS / others: perform a final no-follow stat to confirm the inode
        #   at the original path has not changed since verification, then run
        #   the original path.  A narrow TOCTOU window remains on these platforms
        #   (exploiting it requires write access to the executable's directory).
        argv_list = [spec_dict["executable"]] + list(spec_dict["argv"])
        _exec_path: str
        _pass_fds: tuple[int, ...] = ()
        if exec_fd >= 0:
            # Linux: execute via /proc/self/fd so exec runs the verified inode.
            _exec_path = f"/proc/self/fd/{exec_fd}"
            _pass_fds = (exec_fd,)
        else:
            # macOS/others: re-check the inode hasn't changed since verification.
            try:
                _recheck = Path(spec_dict["executable"]).stat(follow_symlinks=False)
            except OSError as exc:
                _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
                raise ProcessDenied(
                    "denied-executable-identity-changed",
                    f"executable disappeared or could not be stat'd before exec: {exc}",
                ) from exc
            if (
                (_recheck.st_dev, _recheck.st_ino) != (exec_dev, exec_ino)
                or not stat.S_ISREG(_recheck.st_mode)
            ):
                _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
                raise ProcessDenied(
                    "denied-executable-identity-changed",
                    "executable inode changed between verification and exec; "
                    "refusing to launch",
                )
            _exec_path = spec_dict["executable"]

        try:
            proc = subprocess.Popen(
                argv_list,
                executable=_exec_path,
                env=env,
                cwd=cwd_str,
                stdin=stdin_fd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
                close_fds=True,
                pass_fds=_pass_fds,
            )
        except OSError as exc:
            _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
            raise ProcessDenied(
                "denied-launch-failed",
                f"process launch failed: {exc}",
            ) from exc
        except Exception:
            # Any non-OSError (e.g. ValueError from an unexpected field type)
            # must also store a denial event and surface as ProcessDenied
            # without leaking exception text.
            _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
            raise ProcessDenied(
                "denied-launch-failed",
                "process launch failed",
            ) from None
        finally:
            # Close the verified descriptor now that the child has started
            # (or Popen failed).  The kernel keeps the binary mapped in the
            # child's address space independently of this fd.
            if exec_fd >= 0:
                with contextlib.suppress(OSError):
                    os.close(exec_fd)
                exec_fd = -1

        # Read output incrementally with the hard cap; write stdin concurrently.
        timeout_s: int = spec_dict["process_tree_timeout_s"]
        # Bounded post-kill drain timeout: after SIGKILL to the process group, a
        # descendant that left the group and holds the pipes could block
        # communicate() forever.  A small fixed bound ensures this path returns.
        _DRAIN_TIMEOUT_S = 5
        try:
            raw_stdout, raw_stderr, overflowed = _communicate_bounded(
                proc, stdin_input, timeout_s, hard_cap
            )
        except subprocess.TimeoutExpired:
            _kill_process_tree(proc)
            with contextlib.suppress(Exception):
                proc.communicate(timeout=_DRAIN_TIMEOUT_S)
            _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
            raise ProcessDenied(
                "denied-timeout",
                f"process tree timeout exceeded ({timeout_s}s); "
                "all children killed, no output returned",
            ) from None
        except OSError as exc:
            _kill_process_tree(proc)
            with contextlib.suppress(Exception):
                proc.communicate(timeout=_DRAIN_TIMEOUT_S)
            _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
            raise ProcessDenied(
                "denied-launch-failed",
                f"process I/O error: {exc}",
            ) from exc
        except Exception:
            # Any non-OSError from _communicate_bounded must also kill the tree,
            # store a denial event, and surface as ProcessDenied without leaking
            # exception text.
            _kill_process_tree(proc)
            with contextlib.suppress(Exception):
                proc.communicate(timeout=_DRAIN_TIMEOUT_S)
            _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
            raise ProcessDenied(
                "denied-launch-failed",
                "process I/O error",
            ) from None

        # Output cap breach: determine whether the process is still running.
        # A process that already wrote all its output and is in the process of
        # exiting may not yet be reaped when poll() is first called.  Give it a
        # small deterministic window before treating the cap breach as a flood.
        if overflowed and not _leader_exited(proc):
            grace_deadline = time.monotonic() + 0.2
            while not _leader_exited(proc) and time.monotonic() < grace_deadline:
                time.sleep(0.01)
        # If still running after the grace window, kill and refuse.
        if overflowed and not _leader_exited(proc):
            _kill_process_tree(proc)
            with contextlib.suppress(Exception):
                proc.communicate(timeout=_DRAIN_TIMEOUT_S)
            _emit_event(audit_sink, op_id, corr_id, "denied", PROCESS_DENY_REASON)
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

        # Signal the process group while the unreaped leader still reserves its
        # ID, so no background child survives and the signal cannot reach an
        # unrelated group that reused the ID.  start_new_session=True makes the
        # group ID equal proc.pid.  Then reap the leader for its exit code.
        if hasattr(os, "killpg"):
            with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
                os.killpg(proc.pid, signal.SIGKILL)
        with contextlib.suppress(Exception):
            proc.wait(timeout=_DRAIN_TIMEOUT_S)

        _result = ProcessResult(
            exit_code=proc.returncode,
            stdout_redacted=stdout_red,
            stderr_redacted=stderr_red,
            output_was_truncated=truncated,
            output_was_redacted=was_redacted,
        )

    finally:
        # Ensure the verified descriptor is closed if any step raised before
        # the Popen finally block could close it.
        if exec_fd >= 0:
            with contextlib.suppress(OSError):
                os.close(exec_fd)

    return _result
