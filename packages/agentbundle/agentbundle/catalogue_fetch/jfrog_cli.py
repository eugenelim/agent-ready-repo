"""Bounded JFrog CLI (`jf api`) executor for catalogue fetch.

This module is the only place in the catalogue-fetch subsystem that spawns
a subprocess.  Other AgentBundle modules (e.g. workspace_mcp, system_trust)
may spawn subprocesses for unrelated purposes; the credential-boundary
contract test enforces that only this module calls ``jf api``.

Each ``JfrogFetchSession`` issues at most two ``jf api`` subprocesses:
one for the channel descriptor and one for the archive (or one for a
standalone archive).  Every invocation runs with a closed stdin, a
closed child-environment allowlist, a private working directory, a hard
deadline, and terminate-then-kill cleanup on timeout or cap breach.
Partial output is removed before any exception propagates.

The ``jf api`` command appends one ``0x0a`` to stdout when the response
body does not already end in that byte.  ``fetch_bytes`` removes the
byte when stdout is exactly ``max_bytes + 1`` long and the final byte is
``0x0a``, so no more than ``max_bytes`` ever reaches descriptor parsing.
``fetch_archive`` applies the same trim in place: when the written file
is exactly ``max_bytes + 1`` bytes and the final byte is ``0x0a``, the
file is truncated to ``max_bytes`` before being returned.

Deadline model: each ``_run_bounded``/``_run_bounded_to_file`` call
reserves a ``grace`` window at the *end* of its ``timeout`` budget for
the terminate→kill sequence.  The stdout-reader is joined at
``deadline − grace`` (``work_deadline``); if it has not finished by
then, the process is terminated immediately.  All cleanup (terminate,
reader joins, kill, final wait) must complete before ``deadline``.
Total wall-clock time is therefore bounded by ``timeout``.
"""

from __future__ import annotations

import contextlib
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import unquote, urlsplit

from credbroker import HttpAccessError, JfrogCliHttpAccess

from agentbundle.catalogue_fetch.models import CatalogueFetchError

# ── Operational limits ────────────────────────────────────────────────────────

_JFROG_FETCH_TIMEOUT: float = 30.0       # seconds per jf api invocation
_JFROG_FETCH_STDERR_CAP: int = 64 << 10  # 64 KiB per-stream stderr cap
_JFROG_GRACE: float = 2.0               # terminate→kill grace (inside timeout)
_JFROG_CHUNK: int = 65536               # read/write chunk size (64 KiB)
_MAX_FETCHES: int = 2                    # at most two jf api calls per session

# ── Child environment allowlist ───────────────────────────────────────────────
# Mirrors the credbroker allowlist.  JFROG_CLI_SERVER_ID and all
# credential-bearing keys are excluded; the allowlist is closed.

_POSIX_ALLOWED: frozenset[str] = frozenset({"PATH", "HOME"})
_WIN_ALLOWED: frozenset[str] = frozenset(
    {"PATH", "SystemRoot", "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "PATHEXT"}
)
_BOTH_ALLOWED: frozenset[str] = frozenset(
    {
        "JFROG_CLI_HOME_DIR",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "NO_PROXY",
        "http_proxy",
        "https_proxy",
        "no_proxy",
    }
)

# ── URL safety patterns ───────────────────────────────────────────────────────

# Control characters (U+0000–U+001F, U+007F) and backslashes.
_CONTROL_OR_BACKSLASH_RE: re.Pattern[str] = re.compile(r"[\x00-\x1f\x7f\\]")
# Percent-encoded separators: / (%2f), . (%2e), ; (%3b), and backslash (%5c), any case.
_ENCODED_SEP_RE: re.Pattern[str] = re.compile(r"(?i)%2[ef]|%3b|%5c")


# ── Internal subprocess exceptions ────────────────────────────────────────────


class _ChildTimeout(Exception):
    """Raised when a subprocess exceeds its deadline."""


class _ChildCapExceeded(Exception):
    """Raised when a subprocess output stream exceeds its byte cap.

    Attributes:
        stream: ``"stdout"`` or ``"stderr"``.
    """

    def __init__(self, stream: str) -> None:
        self.stream = stream
        super().__init__(stream)


# ── Child environment builder ─────────────────────────────────────────────────


def _build_jfrog_child_env(
    env: Mapping[str, str], *, _os_name: str | None = None
) -> dict[str, str]:
    """Return a closed child environment for ``jf`` invocations.

    Only keys in the platform-appropriate allowlist pass through.  Every
    credential-bearing variable, including ``JFROG_CLI_SERVER_ID`` and
    ``AGENTBUNDLE_HTTP_BEARER_TOKEN``, is excluded by omission.

    Args:
        env: Source environment mapping.
        _os_name: Override for ``os.name``; used in tests to exercise the
            Windows branch on POSIX systems.

    Returns:
        A ``dict`` containing only the allowlisted keys present in ``env``.
    """
    effective_os = _os_name if _os_name is not None else os.name
    if effective_os == "nt":
        allowed = _WIN_ALLOWED | _BOTH_ALLOWED
    else:
        allowed = _POSIX_ALLOWED | _BOTH_ALLOWED
    return {k: v for k, v in env.items() if k in allowed}


# ── jf executable locator ────────────────────────────────────────────────────


def _locate_jf(
    env: Mapping[str, str], *, _os_name: str | None = None
) -> str | None:
    """Return the absolute path to a directly-executable ``jf`` binary.

    Applies the **first-hit-decides** rule matching credbroker: every PATH
    entry is checked for a candidate in candidate-name order.  The first
    entry that holds a candidate determines the outcome for the whole call —
    no later entry is tried.  A candidate is *accepted* (returned as a
    non-``None`` string) only when it is an executable regular file found
    in a valid absolute entry.  A candidate is *refused* (``None``) when
    found in an empty entry (implicit CWD), a relative entry, an absolute
    entry resolving to CWD, a non-executable regular file, or a shim
    extension (``.bat``/``.cmd``) on Windows.

    On Windows, candidates are tried in ``PATHEXT`` declaration order; only
    ``.exe``/``.com`` images are accepted.  ``.bat`` and ``.cmd`` shims are
    refused because the platform services them through a command interpreter,
    which would bypass the no-shell constraint transitively.

    Returns ``None`` when no qualifying candidate is found **or** when the
    first candidate is refused.

    Args:
        env: Environment mapping; ``os.environ`` is never read.
        _os_name: Override for ``os.name``; used in tests to exercise the
            Windows branch on POSIX systems.
    """
    effective_os = _os_name if _os_name is not None else os.name
    path_var = env.get("PATH", "")
    try:
        cwd = Path.cwd().resolve()
    except OSError:
        cwd = Path()

    if effective_os == "nt":
        pathext_str = env.get("PATHEXT", ".COM;.EXE;.BAT;.CMD")
        exts = [e.upper() for e in pathext_str.split(";") if e.strip()]
        _EXEC_EXTS: frozenset[str] = frozenset({".EXE", ".COM"})
        candidate_names: list[tuple[str, bool]] = [
            ("jf" + ext, ext in _EXEC_EXTS) for ext in exts
        ]
    else:
        candidate_names = [("jf", True)]

    for raw_entry in path_var.split(os.pathsep):
        # ── Empty entry: implicit CWD reference ──────────────────────────────
        if not raw_entry:
            # First-hit-decides: if jf is in CWD, refuse it; keep looking
            # only when nothing is there.
            for cname, _ in candidate_names:
                with contextlib.suppress(OSError):
                    if (cwd / cname).is_file():
                        return None  # refused: candidate at CWD
            continue

        entry = Path(raw_entry)

        # ── Relative entry: resolves via CWD ─────────────────────────────────
        if not entry.is_absolute():
            for cname, _ in candidate_names:
                with contextlib.suppress(OSError):
                    if (cwd / entry / cname).is_file():
                        return None  # refused: candidate at relative entry
            continue

        # ── Absolute entry: refuse if it resolves to CWD ─────────────────────
        try:
            resolved = entry.resolve()
        except (OSError, ValueError):
            continue

        if resolved == cwd:
            for cname, _ in candidate_names:
                with contextlib.suppress(OSError):
                    if (resolved / cname).is_file():
                        return None  # refused: candidate at CWD-resolving entry
            continue

        # ── Valid absolute entry: first candidate decides ─────────────────────
        for cname, is_exec_ext in candidate_names:
            candidate = resolved / cname
            try:
                is_file = candidate.is_file()
            except OSError:
                continue
            if not is_file:
                continue

            # Candidate found — decide accept or refuse.
            if effective_os == "nt":
                if not is_exec_ext:
                    return None  # refused: shim extension
                return str(candidate)  # accepted: .exe/.com
            # POSIX: must be executable.
            if os.access(str(candidate), os.X_OK):
                return str(candidate)  # accepted
            return None  # refused: non-executable regular file

    return None  # not found


# ── Endpoint validation and derivation ───────────────────────────────────────


def _validate_fetch_url(url: str, access: JfrogCliHttpAccess) -> str:
    """Validate *url* against the pinned Artifactory base and derive the endpoint.

    Checks that *url* is HTTPS, carries no user-info, query, fragment,
    control character, backslash, encoded separator (``%2f``/``%2e``/
    ``%5c``), literal ``.`` path segment, or empty interior path segment
    (``//``); that its normalized origin equals the pinned Artifactory
    origin; and that its path is a segment-aligned descendant of the
    pinned platform path.

    The returned endpoint is ``"/" + <platform-relative path>``.  The
    ``jf api`` call passes it after ``--``, so no option-parsing can
    reach it.  A leading-``-`` guard remains as defence in depth against
    misuse of the returned string.

    Args:
        url: The fully-qualified HTTPS fetch URL.
        access: The pinned JFrog CLI access result from credbroker.

    Returns:
        The endpoint string starting with ``/``, ready to pass as the
        ``jf api`` positional argument after ``--``.

    Raises:
        CatalogueFetchError: Any validation failure; code is always
            ``"endpoint_not_permitted"``.  No URL component is included in
            the error message.
    """
    # Inline import avoids a top-level circular dependency at load time;
    # direct_http does not import jfrog_cli.
    from agentbundle.catalogue_fetch.direct_http import _normalize_origin

    _NOT_PERMITTED = "endpoint_not_permitted"

    # Check the RAW url string before urlsplit strips control characters.
    # Python's urlsplit silently removes tab (\x09), CR (\x0d), LF (\x0a).
    if _CONTROL_OR_BACKSLASH_RE.search(url):
        raise CatalogueFetchError(
            "fetch URL contains disallowed characters", code=_NOT_PERMITTED
        )

    try:
        parsed = urlsplit(url)
    except Exception:
        raise CatalogueFetchError("fetch URL is not valid", code=_NOT_PERMITTED) from None

    if parsed.scheme.lower() != "https":
        raise CatalogueFetchError("fetch URL must use HTTPS", code=_NOT_PERMITTED)

    if parsed.username is not None or parsed.password is not None:
        raise CatalogueFetchError(
            "fetch URL contains user-info; rejected", code=_NOT_PERMITTED
        )

    if parsed.query:
        raise CatalogueFetchError(
            "fetch URL contains a query string; rejected", code=_NOT_PERMITTED
        )
    if parsed.fragment:
        raise CatalogueFetchError(
            "fetch URL contains a fragment; rejected", code=_NOT_PERMITTED
        )

    # Reject percent-encoded separators: %2f, %2e, %3b, %5c (any case).
    if _ENCODED_SEP_RE.search(url):
        raise CatalogueFetchError(
            "fetch URL contains an encoded separator character", code=_NOT_PERMITTED
        )

    # Reject dot-segments, semicolons (path-parameter ambiguity),
    # leading/trailing whitespace in segments, and empty interior segments.
    path_segments = parsed.path.split("/")
    for i, segment in enumerate(path_segments):
        if segment == "..":
            raise CatalogueFetchError(
                "fetch URL contains a dot-segment traversal", code=_NOT_PERMITTED
            )
        if segment == ".":
            raise CatalogueFetchError(
                "fetch URL contains a dot segment", code=_NOT_PERMITTED
            )
        # A semicolon in any segment may be normalized to a dot-segment by
        # some servlet containers (e.g. /..;/ treated as /../).
        if ";" in segment:
            raise CatalogueFetchError(
                "fetch URL path segment contains a semicolon; rejected",
                code=_NOT_PERMITTED,
            )
        # Leading or trailing whitespace on a segment is a dot-segment ambiguity.
        if segment != segment.strip():
            raise CatalogueFetchError(
                "fetch URL path segment has leading or trailing whitespace; rejected",
                code=_NOT_PERMITTED,
            )
        # The decoded form is what a server may act on, so an encoded control
        # character, padded segment, or dot segment is just as ambiguous.
        decoded = unquote(segment)
        if (
            _CONTROL_OR_BACKSLASH_RE.search(decoded)
            or decoded != decoded.strip()
            or decoded in {".", ".."}
        ):
            raise CatalogueFetchError(
                "fetch URL path segment decodes to an ambiguous segment; rejected",
                code=_NOT_PERMITTED,
            )
        # Interior empty segment means double slash.
        if segment == "" and 0 < i < len(path_segments) - 1:
            raise CatalogueFetchError(
                "fetch URL contains an empty path segment", code=_NOT_PERMITTED
            )

    # Normalize the fetch URL's origin using credbroker's codec.
    try:
        url_origin = _normalize_origin(url)
    except (CatalogueFetchError, HttpAccessError):
        raise CatalogueFetchError(
            "fetch URL origin is not normalizable", code=_NOT_PERMITTED
        ) from None

    # Compare against the pinned Artifactory origin (already normalized by credbroker).
    artf_parsed = urlsplit(access.artifactory_url)
    artf_origin = f"https://{artf_parsed.netloc}"
    artf_path = artf_parsed.path  # Guaranteed to end with / by credbroker.

    if url_origin != artf_origin:
        raise CatalogueFetchError(
            "fetch URL origin does not match pinned Artifactory base",
            code=_NOT_PERMITTED,
        )

    url_path = parsed.path or "/"
    if not url_path.startswith(artf_path):
        raise CatalogueFetchError(
            "fetch URL is not under the pinned Artifactory base",
            code=_NOT_PERMITTED,
        )

    # Derive endpoint relative to the pinned platform base.
    plat_parsed = urlsplit(access.platform_url)
    plat_path = plat_parsed.path  # Guaranteed to end with /.

    if not url_path.startswith(plat_path):
        raise CatalogueFetchError(
            "fetch URL is not under the pinned platform base",
            code=_NOT_PERMITTED,
        )

    # Strip the platform-path prefix; prepend / so the endpoint is always
    # path-like and can never be option-like by construction.
    endpoint = "/" + url_path[len(plat_path):]

    # Defence in depth: the -- delimiter already protects jf api, but reject
    # an option-like endpoint to prevent misuse of the return value.
    if endpoint.startswith("/-"):
        raise CatalogueFetchError(
            "derived endpoint is option-like; rejected", code=_NOT_PERMITTED
        )

    return endpoint


# ── Bounded subprocess runner (byte capture) ──────────────────────────────────


def _run_bounded(
    argv: list[str],
    child_env: dict[str, str],
    *,
    timeout: float,
    stdout_cap: int,
    stderr_cap: int,
) -> tuple[bytes, bytes, int]:
    """Run *argv* with bounded stdout and stderr byte capture.

    Starts two daemon threads to read stdout and stderr concurrently from
    a process running in a private, mode-0700 working directory.  Enforces
    a monotonic deadline; on expiry or cap breach the child is terminated
    (then killed after a bounded grace period) and the working directory is
    removed.

    Deadline model: ``grace = min(_JFROG_GRACE, timeout * 0.4)``.  The
    stdout reader is joined at ``work_deadline = deadline − grace``.  All
    cleanup (terminate, reader joins, kill, final ``proc.wait()``) must
    complete before ``deadline``.  Total wall-clock time is bounded by
    ``timeout``.

    Args:
        argv: Argument vector.  Must not use a shell.
        child_env: Closed child environment from ``_build_jfrog_child_env``.
        timeout: Hard deadline in seconds.
        stdout_cap: Maximum stdout bytes (raises ``_ChildCapExceeded`` if
            the buffer length exceeds this value).
        stderr_cap: Maximum stderr bytes (same semantic).

    Returns:
        ``(stdout_bytes, stderr_bytes, returncode)``.

    Raises:
        _ChildTimeout: Deadline exceeded.
        _ChildCapExceeded: A stream exceeded its cap.
        OSError: ``subprocess.Popen`` failed to start the process.
    """
    grace = min(_JFROG_GRACE, timeout * 0.4)
    deadline = time.monotonic() + timeout
    work_deadline = deadline - grace  # abort must start before deadline

    tmp_dir = tempfile.mkdtemp(prefix="agentbundle-jf-cwd-")
    with contextlib.suppress(OSError):
        Path(tmp_dir).chmod(0o700)

    try:
        proc = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=child_env,
            cwd=tmp_dir,
        )
    except OSError:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise

    stdout_buf = bytearray()
    stderr_buf = bytearray()
    _stdout_exceeded: list[bool] = [False]
    _stderr_exceeded: list[bool] = [False]
    # Signals promptly when either reader breaches its cap.
    _cap_breach: threading.Event = threading.Event()

    def _read_stdout() -> None:
        assert proc.stdout is not None
        try:
            while True:
                chunk = proc.stdout.read(_JFROG_CHUNK)
                if not chunk:
                    break
                stdout_buf.extend(chunk)
                if len(stdout_buf) > stdout_cap:
                    _stdout_exceeded[0] = True
                    _cap_breach.set()
                    return
        except OSError:
            pass

    def _read_stderr() -> None:
        assert proc.stderr is not None
        try:
            while True:
                # read1 returns what one system call delivers, so a reader at
                # the cap sees the first byte over it instead of waiting for a
                # full chunk that a still-open pipe may never complete.
                chunk = proc.stderr.read1(_JFROG_CHUNK)  # type: ignore[attr-defined]
                if not chunk:
                    break
                stderr_buf.extend(chunk)
                if len(stderr_buf) > stderr_cap:
                    _stderr_exceeded[0] = True
                    _cap_breach.set()
                    return
        except OSError:
            pass

    t_out = threading.Thread(target=_read_stdout, daemon=True)
    t_err = threading.Thread(target=_read_stderr, daemon=True)
    t_out.start()
    t_err.start()

    # Wait for stdout reader, cap breach, or work_deadline — whichever fires first.
    # Poll with short intervals so a stderr breach prompts an early abort.
    while t_out.is_alive() and not _cap_breach.is_set():
        wait = min(0.05, max(0.0, work_deadline - time.monotonic()))
        if wait <= 0:
            break
        t_out.join(timeout=wait)

    cap_exceeded = _stdout_exceeded[0] or _stderr_exceeded[0]

    if cap_exceeded or t_out.is_alive():
        # Abort: terminate, allow the grace, kill, and reap the direct child.
        with contextlib.suppress(OSError):
            proc.terminate()
        try:
            proc.wait(timeout=min(grace, max(0.0, deadline - time.monotonic())))
        except subprocess.TimeoutExpired:
            with contextlib.suppress(OSError):
                proc.kill()
        proc.wait()
        # The child is reaped. A reader still blocked on a pipe that a
        # descendant holds open is a daemon thread; it never holds the call
        # past its deadline.
        t_out.join(timeout=min(0.2, max(0.0, deadline - time.monotonic())))
        t_err.join(timeout=min(0.2, max(0.0, deadline - time.monotonic())))
        shutil.rmtree(tmp_dir, ignore_errors=True)
        exceeded_stream = (
            "stdout" if _stdout_exceeded[0] else
            "stderr" if _stderr_exceeded[0] else None
        )
        if exceeded_stream:
            raise _ChildCapExceeded(exceeded_stream)
        raise _ChildTimeout()

    # Normal completion: wait for stderr reader, then reap.
    remaining_err = max(0.0, deadline - time.monotonic())
    t_err.join(timeout=remaining_err)

    # Re-check: stderr may have breached after stdout closed.  The child may be
    # blocking on a full stderr pipe, so terminate before waiting.
    if _stderr_exceeded[0]:
        with contextlib.suppress(OSError):
            proc.terminate()
        with contextlib.suppress(OSError):
            if proc.poll() is None:
                proc.kill()
        proc.wait()
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise _ChildCapExceeded("stderr")

    try:
        rc = proc.wait(timeout=max(0.0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        with contextlib.suppress(OSError):
            proc.terminate()
        with contextlib.suppress(OSError):
            proc.kill()
        proc.wait()
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise _ChildTimeout() from None

    shutil.rmtree(tmp_dir, ignore_errors=True)
    return bytes(stdout_buf), bytes(stderr_buf), rc


# ── Bounded subprocess runner (file streaming) ────────────────────────────────


def _run_bounded_to_file(
    argv: list[str],
    child_env: dict[str, str],
    *,
    timeout: float,
    max_bytes: int,
    stderr_cap: int,
) -> tuple[Path, bytes, int]:
    """Run *argv*, streaming stdout to a temporary file (at most max_bytes+1 bytes).

    The ``jf api`` command may append one trailing ``0x0a`` to stdout, so
    the hard stdout cap is ``max_bytes + 1``.  If the process writes more,
    ``_ChildCapExceeded("stdout")`` is raised.

    Deadline model: same as ``_run_bounded`` — cleanup is bounded by the
    grace window inside the ``timeout`` budget.

    The returned archive temp file is the caller's responsibility on success.
    On any exception the partial file is removed before the exception
    propagates.

    Args:
        argv: Argument vector.  Must not use a shell.
        child_env: Closed child environment from ``_build_jfrog_child_env``.
        timeout: Hard deadline in seconds.
        max_bytes: Digest-verified content size cap (without the trailing byte).
        stderr_cap: Maximum stderr bytes.

    Returns:
        ``(archive_tmp_path, stderr_bytes, returncode)``.

    Raises:
        _ChildTimeout: Deadline exceeded.
        _ChildCapExceeded: A stream exceeded its cap.
        OSError: Process start or file I/O failed.
    """
    cap = max_bytes + 1

    grace = min(_JFROG_GRACE, timeout * 0.4)
    deadline = time.monotonic() + timeout
    work_deadline = deadline - grace

    # Temp file for the archive body.
    tmp_fd, tmp_path_str = tempfile.mkstemp(prefix="agentbundle-jfrog-", suffix=".tmp")
    archive_path = Path(tmp_path_str)

    # Private working directory for the subprocess.
    tmp_dir = tempfile.mkdtemp(prefix="agentbundle-jf-cwd-")
    with contextlib.suppress(OSError):
        Path(tmp_dir).chmod(0o700)

    try:
        proc = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=child_env,
            cwd=tmp_dir,
        )
    except OSError:
        with contextlib.suppress(OSError):
            os.close(tmp_fd)
        with contextlib.suppress(OSError):
            archive_path.unlink(missing_ok=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise

    stderr_buf = bytearray()
    _stdout_exceeded: list[bool] = [False]
    _stderr_exceeded: list[bool] = [False]
    _bytes_written: list[int] = [0]
    # Signals promptly when either reader breaches its cap.
    _cap_breach: threading.Event = threading.Event()

    def _write_stdout() -> None:
        assert proc.stdout is not None
        # The fd is owned by this thread; close it when done.
        try:
            with os.fdopen(tmp_fd, "wb") as fh:
                while True:
                    chunk = proc.stdout.read(_JFROG_CHUNK)
                    if not chunk:
                        break
                    _bytes_written[0] += len(chunk)
                    if _bytes_written[0] > cap:
                        _stdout_exceeded[0] = True
                        _cap_breach.set()
                        return
                    fh.write(chunk)
        except OSError:
            pass

    def _read_stderr() -> None:
        assert proc.stderr is not None
        try:
            while True:
                # read1 returns what one system call delivers, so a reader at
                # the cap sees the first byte over it instead of waiting for a
                # full chunk that a still-open pipe may never complete.
                chunk = proc.stderr.read1(_JFROG_CHUNK)  # type: ignore[attr-defined]
                if not chunk:
                    break
                stderr_buf.extend(chunk)
                if len(stderr_buf) > stderr_cap:
                    _stderr_exceeded[0] = True
                    _cap_breach.set()
                    return
        except OSError:
            pass

    t_out = threading.Thread(target=_write_stdout, daemon=True)
    t_err = threading.Thread(target=_read_stderr, daemon=True)
    t_out.start()
    t_err.start()

    def _abort_and_cleanup(grace_budget: float) -> None:
        with contextlib.suppress(OSError):
            proc.terminate()
        try:
            proc.wait(timeout=min(grace, grace_budget))
        except subprocess.TimeoutExpired:
            with contextlib.suppress(OSError):
                proc.kill()
        proc.wait()
        # The child is reaped. A reader still blocked on a pipe that a
        # descendant holds open is a daemon thread; it never holds the call
        # past its deadline.
        t_out.join(timeout=min(0.2, max(0.0, deadline - time.monotonic())))
        t_err.join(timeout=min(0.2, max(0.0, deadline - time.monotonic())))
        shutil.rmtree(tmp_dir, ignore_errors=True)
        with contextlib.suppress(OSError):
            archive_path.unlink(missing_ok=True)

    # Wait for stdout writer, cap breach, or work_deadline — whichever fires first.
    # Poll with short intervals so a stderr breach prompts an early abort.
    while t_out.is_alive() and not _cap_breach.is_set():
        wait = min(0.05, max(0.0, work_deadline - time.monotonic()))
        if wait <= 0:
            break
        t_out.join(timeout=wait)

    cap_exceeded = _stdout_exceeded[0] or _stderr_exceeded[0]

    if cap_exceeded or t_out.is_alive():
        _abort_and_cleanup(max(0.0, deadline - time.monotonic()))
        if _stdout_exceeded[0]:
            raise _ChildCapExceeded("stdout")
        if _stderr_exceeded[0]:
            raise _ChildCapExceeded("stderr")
        raise _ChildTimeout()

    # Normal completion: wait for stderr reader, then reap.
    remaining_err = max(0.0, deadline - time.monotonic())
    t_err.join(timeout=remaining_err)

    # Re-check: stderr may have breached after stdout closed.  The child may be
    # blocking on a full stderr pipe, so terminate before waiting.
    if _stderr_exceeded[0]:
        _abort_and_cleanup(max(0.0, deadline - time.monotonic()))
        raise _ChildCapExceeded("stderr")

    try:
        rc = proc.wait(timeout=max(0.0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        with contextlib.suppress(OSError):
            proc.terminate()
        with contextlib.suppress(OSError):
            proc.kill()
        proc.wait()
        t_out.join(timeout=1.0)
        t_err.join(timeout=1.0)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        with contextlib.suppress(OSError):
            archive_path.unlink(missing_ok=True)
        raise _ChildTimeout() from None

    shutil.rmtree(tmp_dir, ignore_errors=True)
    return archive_path, bytes(stderr_buf), rc


# ── Fetch session ─────────────────────────────────────────────────────────────


class JfrogFetchSession:
    """A bounded JFrog CLI fetch session pinned to one ``JfrogCliHttpAccess``.

    Issues at most ``_MAX_FETCHES`` (two) ``jf api`` subprocesses.  Each call
    validates and confines the fetch URL against the pinned Artifactory and
    platform bases, derives the platform-relative endpoint, and executes
    ``jf api --server-id=<id> -- <endpoint>``.

    The session does not parse catalogue descriptors, choose artifact URLs,
    verify digests, or extract archives.  Those operations remain in
    ``https_catalogue.py``.
    """

    def __init__(
        self,
        access: JfrogCliHttpAccess,
        env: Mapping[str, str],
        *,
        _os_name: str | None = None,
    ) -> None:
        self._access = access
        self._child_env = _build_jfrog_child_env(env, _os_name=_os_name)
        self._jf_path = _locate_jf(env, _os_name=_os_name)
        self._fetch_count = 0

    def _get_jf(self) -> str:
        """Return the jf path or raise if not found or refused."""
        if self._jf_path is None:
            raise CatalogueFetchError(
                "jf executable not found for fetch",
                code="jfrog_fetch_failed",
            )
        return self._jf_path

    def _check_and_increment_fetch(self) -> None:
        """Raise if the fetch budget is exhausted; otherwise increment the counter."""
        if self._fetch_count >= _MAX_FETCHES:
            raise CatalogueFetchError(
                "fetch budget exhausted: at most two jf api calls per session",
                code="jfrog_fetch_failed",
            )
        self._fetch_count += 1

    def fetch_bytes(
        self, url: str, *, max_bytes: int, timeout: float = _JFROG_FETCH_TIMEOUT
    ) -> bytes:
        """Fetch a bounded descriptor payload from *url* via ``jf api``.

        Applies the appended-newline rule: if stdout is exactly ``max_bytes + 1``
        bytes and the final byte is ``0x0a``, that byte is removed and the
        remaining ``max_bytes`` bytes are returned.  If stdout is ``max_bytes + 1``
        bytes and the final byte is not ``0x0a``, the response is rejected.

        Args:
            url: Fully-qualified HTTPS URL, must be under the pinned Artifactory base.
            max_bytes: Hard cap on response content bytes (after optional trim).
            timeout: Hard subprocess deadline in seconds.  Defaults to
                ``_JFROG_FETCH_TIMEOUT`` (30 s) which is the production value;
                pass a smaller value only in tests.

        Returns:
            The response body as bytes (at most ``max_bytes`` bytes).

        Raises:
            CatalogueFetchError: Any fetch failure, URL validation failure,
                size cap, or timeout.
        """
        self._check_and_increment_fetch()
        jf_path = self._get_jf()
        endpoint = _validate_fetch_url(url, self._access)

        # Allow max_bytes + 1 for the potential appended 0x0a.
        stdout_cap = max_bytes + 1
        argv = [jf_path, "api", f"--server-id={self._access.server_id}", "--", endpoint]

        try:
            stdout, _stderr, rc = _run_bounded(
                argv,
                self._child_env,
                timeout=float(timeout),
                stdout_cap=stdout_cap,
                stderr_cap=_JFROG_FETCH_STDERR_CAP,
            )
        except _ChildTimeout:
            raise CatalogueFetchError(
                "jf api timed out", code="jfrog_fetch_timeout"
            ) from None
        except _ChildCapExceeded as exc:
            if exc.stream == "stderr":
                raise CatalogueFetchError(
                    "jf api stderr exceeded limit", code="jfrog_fetch_stderr_too_large"
                ) from None
            raise CatalogueFetchError(
                "jf api response exceeds descriptor limit", code="descriptor_too_large"
            ) from None
        except OSError:
            raise CatalogueFetchError(
                "jf api failed to start", code="jfrog_fetch_failed"
            ) from None

        if rc != 0:
            raise CatalogueFetchError("jf api exited non-zero", code="jfrog_fetch_failed")

        # Apply the appended-newline rule.
        if len(stdout) == stdout_cap:
            if stdout[-1:] == b"\x0a":
                stdout = stdout[:-1]  # Remove the appended byte.
            else:
                raise CatalogueFetchError(
                    "jf api response exceeds descriptor limit", code="descriptor_too_large"
                )

        return stdout

    def fetch_archive(
        self, url: str, *, max_bytes: int, timeout: float = _JFROG_FETCH_TIMEOUT
    ) -> Path:
        """Stream a bounded archive from *url* via ``jf api`` to a temp file.

        The written file is at most ``max_bytes`` bytes.  When ``jf api``
        streams exactly ``max_bytes + 1`` bytes and the final byte is ``0x0a``
        (the appended trailing byte), the file is truncated in place to
        ``max_bytes`` before being returned.  A ``max_bytes + 1`` body whose
        final byte is not ``0x0a`` is rejected as ``archive_too_large``.

        The temp file is removed on any failure before the exception propagates.

        Args:
            url: Fully-qualified HTTPS URL, must be under the pinned Artifactory base.
            max_bytes: Hard cap on archive content bytes.
            timeout: Hard subprocess deadline in seconds.  Defaults to
                ``_JFROG_FETCH_TIMEOUT`` (30 s) which is the production value;
                pass a smaller value only in tests.

        Returns:
            ``Path`` of the temporary archive file (at most ``max_bytes``
            bytes).  The caller is responsible for cleanup on success.

        Raises:
            CatalogueFetchError: Any fetch failure, URL validation failure,
                size cap, or timeout.
        """
        self._check_and_increment_fetch()
        jf_path = self._get_jf()
        endpoint = _validate_fetch_url(url, self._access)

        argv = [jf_path, "api", f"--server-id={self._access.server_id}", "--", endpoint]

        try:
            archive_path, _stderr, rc = _run_bounded_to_file(
                argv,
                self._child_env,
                timeout=float(timeout),
                max_bytes=max_bytes,
                stderr_cap=_JFROG_FETCH_STDERR_CAP,
            )
        except _ChildTimeout:
            raise CatalogueFetchError(
                "jf api archive fetch timed out", code="jfrog_fetch_timeout"
            ) from None
        except _ChildCapExceeded as exc:
            if exc.stream == "stderr":
                raise CatalogueFetchError(
                    "jf api stderr exceeded limit", code="jfrog_fetch_stderr_too_large"
                ) from None
            raise CatalogueFetchError(
                "jf api archive exceeds size limit", code="archive_too_large"
            ) from None
        except OSError:
            raise CatalogueFetchError(
                "jf api failed to start", code="jfrog_fetch_failed"
            ) from None

        if rc != 0:
            with contextlib.suppress(OSError):
                archive_path.unlink(missing_ok=True)
            raise CatalogueFetchError(
                "jf api archive fetch exited non-zero", code="jfrog_fetch_failed"
            )

        # Apply the appended-newline constraint in-place.
        # The file is admitted up to max_bytes+1 bytes.  If it is exactly
        # max_bytes+1 bytes and the final byte is 0x0a, truncate the file
        # to max_bytes (removing the appended byte).  A non-0x0a final byte
        # means the archive is genuinely over the limit.
        cap = max_bytes + 1
        try:
            file_size = archive_path.stat().st_size
        except OSError:
            with contextlib.suppress(OSError):
                archive_path.unlink(missing_ok=True)
            raise CatalogueFetchError(
                "failed to stat archive temp file", code="jfrog_fetch_failed"
            ) from None

        if file_size == cap:
            try:
                with archive_path.open("rb") as fh:
                    fh.seek(-1, 2)
                    last_byte = fh.read(1)
            except OSError:
                with contextlib.suppress(OSError):
                    archive_path.unlink(missing_ok=True)
                raise CatalogueFetchError(
                    "failed to read archive temp file", code="jfrog_fetch_failed"
                ) from None
            if last_byte != b"\x0a":
                with contextlib.suppress(OSError):
                    archive_path.unlink(missing_ok=True)
                raise CatalogueFetchError(
                    "jf api archive exceeds size limit", code="archive_too_large"
                )
            # Trailing 0x0a — truncate to max_bytes so callers never see
            # more than the limit.
            try:
                with archive_path.open("r+b") as fh:
                    fh.truncate(max_bytes)
            except OSError:
                with contextlib.suppress(OSError):
                    archive_path.unlink(missing_ok=True)
                raise CatalogueFetchError(
                    "failed to truncate archive temp file", code="jfrog_fetch_failed"
                ) from None
        elif file_size > cap:
            with contextlib.suppress(OSError):
                archive_path.unlink(missing_ok=True)
            raise CatalogueFetchError(
                "jf api archive exceeds size limit", code="archive_too_large"
            )

        return archive_path


__all__ = ["JfrogFetchSession"]
