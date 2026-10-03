"""Target-bound HTTP access resolution for HTTPS catalogue acquisition.

This module resolves a provider for a given HTTPS target URL and environment
mapping, returning exactly one of four immutable result variants:
``BearerHttpAccess``, ``JfrogCliHttpAccess``, ``NetrcHttpAccess``, or
``AnonymousHttpAccess``.

Selection proceeds in fixed order — bearer, JFrog CLI, .netrc, anonymous —
stopping at the first available provider. A configured-but-broken provider
raises ``HttpAccessError`` rather than falling through.

The target URL is validated once before any provider is evaluated. An invalid
target raises ``HttpAccessError`` with provider class ``"target"`` and code
``"invalid_target_host"`` before provider selection begins.

No network I/O occurs during resolution. The supplied ``env`` mapping is the
only credential source; os.environ is never read.
"""

from __future__ import annotations

import base64
import contextlib
import io
import ipaddress
import json
import netrc as _netrc_module
import os
import re
import shutil
import stat
import subprocess
import tempfile
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar
from urllib.parse import urlsplit

# ── Closed code set ───────────────────────────────────────────────────────────

# Every code an HttpAccessError may carry. Constructing one with a code outside
# this set raises ValueError at construction time.
VALID_CODES: frozenset[str] = frozenset(
    {
        "invalid_bearer",
        "jfrog_discovery_failed",
        "jfrog_discovery_timeout",
        "jfrog_discovery_too_large",
        "jfrog_discovery_malformed",
        "jfrog_profile_ambiguous",
        "jfrog_profile_mismatch",
        "unsupported_jfrog_topology",
        "incompatible_jfrog_cli",
        "jfrog_probe_too_large",
        "jfrog_probe_timeout",
        "jfrog_probe_failed",
        "jfrog_cli_not_executable",
        "invalid_target_host",
        "netrc_unreadable",
        "netrc_unsafe",
        "netrc_malformed",
        "netrc_incomplete",
    }
)


# ── Error ─────────────────────────────────────────────────────────────────────


class HttpAccessError(Exception):
    """Terminal error from HTTP access resolution.

    Carries only a stable, non-secret provider class and failure code.
    The message is built exclusively from those two fields; no input value
    ever reaches exception text, repr, or args.

    Attributes:
        provider: Provider class: one of "target", "bearer", "jfrog", "netrc".
        code: Stable failure code from the closed ``VALID_CODES`` set.
    """

    def __init__(self, provider: str, code: str) -> None:
        if code not in VALID_CODES:
            raise ValueError(
                f"Unknown HttpAccessError code: {code!r}; "
                f"must be one of the VALID_CODES set"
            )
        self.provider: str = provider
        self.code: str = code
        # Fixed message text — provider and code only, never any input value.
        super().__init__(
            f"HTTP access resolution failed: provider={provider!r} code={code!r}"
        )

    def __repr__(self) -> str:
        return f"HttpAccessError(provider={self.provider!r}, code={self.code!r})"

    def __str__(self) -> str:
        return (
            f"HTTP access resolution failed: "
            f"provider={self.provider!r} code={self.code!r}"
        )


# ── Result variants ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BearerHttpAccess:
    """HTTP access via an explicit bearer token.

    The token is carried only as the full ``Authorization`` header value; it
    never appears in ``repr`` or ``str``.

    Attributes:
        origin: Normalized HTTPS origin the bearer token is bound to
            (e.g. ``"https://catalogue.example.test"``).
        authorization: Full ``Authorization`` header value, e.g.
            ``"Bearer <token>"``. Never shown in repr.
    """

    provider: ClassVar[str] = "bearer"
    origin: str
    authorization: str = field(repr=False)


@dataclass(frozen=True)
class NetrcHttpAccess:
    """HTTP access via a .netrc credential.

    The derived authorization header value never appears in ``repr`` or
    ``str``.

    Attributes:
        origin: Normalized HTTPS origin the .netrc credential is bound to.
        authorization: Full ``Authorization`` header value derived from the
            .netrc entry. Never shown in repr.
    """

    provider: ClassVar[str] = "netrc"
    origin: str
    authorization: str = field(repr=False)


@dataclass(frozen=True)
class JfrogCliHttpAccess:
    """HTTP access via JFrog CLI delegation.

    Discovery selects the JFrog CLI server profile whose Artifactory URL
    is the unique longest prefix of the target URL.

    Attributes:
        server_id: The JFrog CLI server profile ID selected for this target.
            Never shown in repr (server IDs must not appear in diagnostics).
        platform_url: JFrog platform base URL.
        artifactory_url: JFrog Artifactory base URL.
    """

    provider: ClassVar[str] = "jfrog"
    server_id: str = field(repr=False)
    platform_url: str
    artifactory_url: str


@dataclass(frozen=True)
class AnonymousHttpAccess:
    """Anonymous HTTP access — no credentials.

    Attributes:
        origin: Normalized HTTPS origin.
    """

    provider: ClassVar[str] = "anonymous"
    origin: str


# Union of all four result variants for type annotations.
HttpAccess = BearerHttpAccess | NetrcHttpAccess | JfrogCliHttpAccess | AnonymousHttpAccess


# ── Host normalization ────────────────────────────────────────────────────────


_ASCII_UPPER_TO_LOWER = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"
)


def _raw_hostname(netloc: str) -> str:
    """Return the host part of ``netloc`` exactly as written.

    ``urlsplit(...).hostname`` applies ``str.lower()``, which folds non-ASCII
    letters before the IDNA codec sees them, so the host is taken from the
    netloc directly: user info and port are removed, IPv6 brackets stripped.
    """
    hostport = netloc.rpartition("@")[2]
    if hostport.startswith("["):
        return hostport[1:].partition("]")[0]
    return hostport.partition(":")[0]


def _normalize_host(hostname: str) -> str:
    """Normalize a hostname to its ASCII IDNA form.

    IP literals (IPv4 and IPv6) are returned in canonical form without
    IDNA encoding. Other hostnames are ASCII-lowercased then IDNA-encoded
    under the stdlib's IDNA codec (IDNA2003 via ``encodings.idna``).

    IPv6 addresses are returned bracketed, ready for an origin string.

    Raises:
        UnicodeError: The hostname cannot be IDNA-encoded (e.g. a label
            longer than 63 characters, or a host the codec rejects).
    """
    # Attempt IPv4 or IPv6 address parsing.
    try:
        addr = ipaddress.ip_address(hostname)
        if isinstance(addr, ipaddress.IPv6Address):
            # Reconstruct the bracketed form for use in an origin string.
            return f"[{str(addr)}]"
        # IPv4: return the canonical decimal dotted form, already lowercase.
        return str(addr)
    except ValueError:
        pass

    # Hostname: ASCII-lowercase only (str.lower() would also fold non-ASCII
    # letters, which is the codec's job), then IDNA-encode label by label.
    ascii_lowered = hostname.translate(_ASCII_UPPER_TO_LOWER)
    try:
        return ascii_lowered.encode("idna").decode("ascii")
    except (UnicodeError, UnicodeDecodeError, UnicodeEncodeError) as exc:
        raise UnicodeError(
            f"hostname cannot be IDNA-encoded: {exc}"
        ) from exc


# ── .netrc helpers ───────────────────────────────────────────────────────────

# Maximum bytes read from a .netrc file; files over this limit are rejected
# as unreadable rather than potentially exhausting memory.
_NETRC_MAX_BYTES: int = 1 << 20  # 1 MiB


class _StringNetrc(_netrc_module.netrc):
    """Parse .netrc content from an in-memory string without re-opening the file.

    Subclasses stdlib ``netrc.netrc`` to call ``_parse`` on a ``StringIO``
    object, bypassing the constructor's ``open(file)`` call.  Passes
    ``default_netrc=False`` so the stdlib's own permission check is skipped;
    the caller performs that check directly on the open file descriptor.
    """

    def __init__(self, text: str) -> None:
        self.hosts: dict = {}
        self.macros: dict = {}
        self._parse("<netrc>", io.StringIO(text), False)  # type: ignore[attr-defined]


def _split_netrc_key(key: str) -> tuple[str, str | None]:
    """Split a .netrc machine key into a raw host string and optional port string.

    For a key of the form ``host:NNN`` where *NNN* is all decimal digits,
    returns ``(host, "NNN")``.  For an IPv6 bracketed form ``[addr]:NNN``,
    returns ``("[addr]", "NNN")``.  Otherwise returns ``(key, None)``.
    """
    if key.startswith("["):
        bracket_end = key.find("]")
        if bracket_end < 0:
            return key, None
        host_part = key[:bracket_end + 1]
        rest = key[bracket_end + 1:]
        if rest.startswith(":") and len(rest) > 1 and rest[1:].isdigit():
            return host_part, rest[1:]
        return key, None
    last_colon = key.rfind(":")
    if last_colon >= 0:
        port_str = key[last_colon + 1:]
        if port_str and port_str.isdigit():
            return key[:last_colon], port_str
    return key, None


def _normalize_netrc_host(raw_host: str) -> str:
    """Normalize a raw host string from a .netrc key under the single host profile.

    IPv6 addresses in bracketed notation have their brackets stripped before
    ``_normalize_host`` is called; ``_normalize_host`` adds them back.

    Raises:
        UnicodeError: The host cannot be IDNA-encoded.
    """
    if raw_host.startswith("[") and raw_host.endswith("]"):
        return _normalize_host(raw_host[1:-1])
    return _normalize_host(raw_host)


def _resolve_home_dir(
    env: Mapping[str, str], *, _os_name: str | None = None
) -> str | None:
    """Resolve the user home directory from the supplied ``env`` mapping.

    Uses platform-appropriate precedence — ``HOME`` on POSIX;
    ``USERPROFILE`` then ``HOMEDRIVE``+``HOMEPATH`` on Windows — so that
    ``expanduser`` is never called and the supplied mapping is the only
    credential source.

    Args:
        env: Environment mapping to consult.  ``os.environ`` is never read.
        _os_name: Override for ``os.name``; used in tests to exercise the
            Windows branch on POSIX without real platform changes.

    Returns:
        The home directory string, or ``None`` when none can be resolved.
    """
    name = _os_name if _os_name is not None else os.name
    if name == "nt":
        home: str | None = env.get("USERPROFILE") or None
        if not home:
            drive = env.get("HOMEDRIVE", "")
            path_part = env.get("HOMEPATH", "")
            home = (drive + path_part) or None
        return home
    return env.get("HOME") or None


# ── JFrog CLI helpers ─────────────────────────────────────────────────────────

# Subprocess time limits (seconds)
_JFROG_DISCOVERY_TIMEOUT: float = 10.0
_JFROG_PROBE_TIMEOUT: float = 5.0

# Stream byte caps
_JFROG_DISCOVERY_STDOUT_CAP: int = 1 << 20   # 1 MiB
_JFROG_DISCOVERY_STDERR_CAP: int = 64 << 10  # 64 KiB
_JFROG_PROBE_CAP: int = 8 << 10             # 8 KiB each stream

# Terminate-before-kill grace period; accounted inside the call's own deadline.
_JFROG_GRACE: float = 2.0

# Minimum supported JFrog CLI version.
_JFROG_MIN_VERSION: tuple[int, int, int] = (2, 105, 0)

# Regex for "jf version X.Y.Z" on stdout of jf --version.
_JFROG_VERSION_RE: re.Pattern[str] = re.compile(
    r"^jf version (\d+)\.(\d+)\.(\d+)", re.MULTILINE
)

# Child env allowlist keys — common to both platforms.
_JFROG_CHILD_ENV_COMMON: frozenset[str] = frozenset(
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
_JFROG_CHILD_ENV_POSIX: frozenset[str] = frozenset({"PATH", "HOME"})
_JFROG_CHILD_ENV_WINDOWS: frozenset[str] = frozenset(
    {"PATH", "SystemRoot", "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "PATHEXT"}
)


class _ChildTimeout(Exception):
    """The bounded child process exceeded its monotonic deadline."""


class _ChildCapExceeded(Exception):
    """A bounded child process stream exceeded its byte cap.

    Attributes:
        stream: ``"stdout"`` or ``"stderr"``.
    """

    def __init__(self, stream: str) -> None:
        self.stream = stream
        super().__init__(stream)


def _build_jfrog_child_env(
    env: Mapping[str, str], *, _os_name: str | None = None
) -> dict[str, str]:
    """Build the allowlisted child environment from the supplied mapping.

    Passes only the keys in the closed allowlist appropriate for the platform.
    Drops everything else, including JFROG_CLI_SERVER_ID and all credential
    variables. Never reads os.environ.
    """
    name = _os_name if _os_name is not None else os.name
    if name == "nt":
        allowed = _JFROG_CHILD_ENV_COMMON | _JFROG_CHILD_ENV_WINDOWS
    else:
        allowed = _JFROG_CHILD_ENV_COMMON | _JFROG_CHILD_ENV_POSIX
    return {k: v for k, v in env.items() if k in allowed}


def _locate_jf(
    env: Mapping[str, str], *, _os_name: str | None = None
) -> tuple[str | None, bool]:
    """Search the supplied env PATH for the jf executable.

    Returns ``(abs_path, False)`` when a directly executable jf is found.
    Returns ``(None, False)`` when no candidate exists anywhere on PATH.
    Returns ``(None, True)`` when a candidate is found but is refused (shim,
    non-executable regular file, empty entry, relative entry, or an entry that
    resolves to the current working directory).

    Never invokes a shell. The returned path is always absolute.
    """
    name = _os_name if _os_name is not None else os.name
    path_str = env.get("PATH", "")
    cwd = Path.cwd()

    if name == "nt":
        pathext_str = env.get("PATHEXT", ".COM;.EXE;.BAT;.CMD")
        exts = [e.upper() for e in pathext_str.split(";") if e.strip()]
        _EXEC_EXTS: frozenset[str] = frozenset({".EXE", ".COM"})
        _SHIM_EXTS: frozenset[str] = frozenset({".BAT", ".CMD"})
        candidate_names = [("jf" + ext, ext in _EXEC_EXTS) for ext in exts]
    else:
        candidate_names = [("jf", True)]

    for raw_entry in path_str.split(os.pathsep):
        # Empty entry — refers to CWD; any candidate there is refused.
        if not raw_entry:
            for cname, _ in candidate_names:
                try:
                    if (cwd / cname).is_file():
                        return (None, True)
                except OSError:
                    pass
            continue

        entry = Path(raw_entry)

        # Relative entry — any candidate there is refused.
        if not entry.is_absolute():
            for cname, _ in candidate_names:
                try:
                    if (cwd / entry / cname).is_file():
                        return (None, True)
                except OSError:
                    pass
            continue

        # Absolute entry — refuse if it resolves to CWD.
        try:
            resolved = entry.resolve()
        except OSError:
            continue

        if resolved == cwd:
            for cname, _ in candidate_names:
                try:
                    if (resolved / cname).is_file():
                        return (None, True)
                except OSError:
                    pass
            continue

        # Valid entry — find the first candidate in PATHEXT order.
        for cname, is_exec_ext in candidate_names:
            candidate = resolved / cname
            try:
                is_file = candidate.is_file()
            except OSError:
                continue
            if not is_file:
                continue

            # Found a matching file.
            if name == "nt":
                # Shim (.bat/.cmd) is refused; .exe/.com is accepted.
                if not is_exec_ext:
                    return (None, True)
                return (str(candidate), False)
            # POSIX: needs regular file with X_OK.
            if os.access(str(candidate), os.X_OK):
                return (str(candidate), False)
            return (None, True)

    return (None, False)  # no candidate found anywhere


def _run_bounded(
    argv: list[str],
    child_env: dict[str, str],
    *,
    timeout: float,
    stdout_cap: int,
    stderr_cap: int,
) -> tuple[bytes, bytes, int]:
    """Run *argv* with bounded streams and a monotonic deadline.

    Creates a private temp directory (mode 0700) as the child's working
    directory and removes it after the child exits.  Reads stdout and stderr
    concurrently using daemon threads.  Terminates the child (then kills after
    the grace period) on a deadline or cap breach; the reap always runs against
    an already-terminated process.

    Returns ``(stdout_bytes, stderr_bytes, returncode)`` on normal exit.

    Raises:
        _ChildTimeout: The deadline was exceeded.
        _ChildCapExceeded: A stream exceeded its cap (before reap).
        OSError: Popen could not execute the binary.
    """
    grace = min(_JFROG_GRACE, timeout * 0.4)
    deadline = time.monotonic() + timeout
    work_deadline = deadline - grace

    tmp_dir = tempfile.mkdtemp(prefix="_jfrog_run_")
    with contextlib.suppress(OSError):
        Path(tmp_dir).chmod(0o700)

    try:
        proc = subprocess.Popen(  # noqa: S603
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=tmp_dir,
            env=child_env,
        )
    except OSError:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise

    stdout_buf: bytearray = bytearray()
    stderr_buf: bytearray = bytearray()
    _stdout_exceeded: list[bool] = [False]
    _stderr_exceeded: list[bool] = [False]
    _read_done: threading.Event = threading.Event()

    def _reader(
        stream: io.RawIOBase,
        buf: bytearray,
        cap: int,
        flag: list[bool],
    ) -> None:
        try:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    break
                buf.extend(chunk)
                if len(buf) > cap:
                    flag[0] = True
                    return
        except OSError:
            pass

    t_out = threading.Thread(
        target=_reader,
        args=(proc.stdout, stdout_buf, stdout_cap, _stdout_exceeded),
        daemon=True,
    )
    t_err = threading.Thread(
        target=_reader,
        args=(proc.stderr, stderr_buf, stderr_cap, _stderr_exceeded),
        daemon=True,
    )
    t_out.start()
    t_err.start()

    # Wait for work_deadline or cap breach.
    remaining = work_deadline - time.monotonic()
    if remaining > 0:
        t_out.join(timeout=remaining)

    cap_exceeded = _stdout_exceeded[0] or _stderr_exceeded[0]
    timed_out = time.monotonic() >= work_deadline and t_out.is_alive()

    if cap_exceeded or timed_out or t_out.is_alive():
        # Stop the child, then reap (always against already-terminated process).
        with contextlib.suppress(OSError):
            proc.terminate()
        # Wait up to grace for the readers to finish.
        grace_remaining = max(0.0, deadline - time.monotonic() - 0.1)
        t_out.join(timeout=grace_remaining)
        t_err.join(timeout=max(0.0, deadline - time.monotonic() - 0.05))
        with contextlib.suppress(OSError):
            if proc.poll() is None:
                proc.kill()
        proc.wait()
        shutil.rmtree(tmp_dir, ignore_errors=True)

        exceeded_stream = (
            "stdout" if _stdout_exceeded[0] else
            "stderr" if _stderr_exceeded[0] else None
        )
        if exceeded_stream:
            raise _ChildCapExceeded(exceeded_stream)
        raise _ChildTimeout()

    # Normal completion — wait for stderr reader then reap.
    remaining_err = max(0.0, deadline - time.monotonic())
    t_err.join(timeout=remaining_err)
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


def _normalize_jfrog_url(url_str: str) -> str | None:
    """Normalize a JFrog profile URL field into ``https://<host>[:<port>]<path/>``.

    Returns ``None`` when the URL is ineligible (not https, has user info,
    query, or fragment).  Raises ``HttpAccessError("jfrog",
    "jfrog_discovery_malformed")`` when the host cannot be IDNA-encoded.
    """
    try:
        parsed = urlsplit(url_str)
    except Exception:
        return None

    if parsed.scheme.lower() != "https":
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    if parsed.query:
        return None
    if parsed.fragment:
        return None

    raw_host = _raw_hostname(parsed.netloc)
    if not raw_host:
        return None
    try:
        norm_host = _normalize_host(raw_host)
    except UnicodeError:
        raise HttpAccessError("jfrog", "jfrog_discovery_malformed") from None

    try:
        port = parsed.port
    except ValueError:
        return None  # malformed port

    norm_netloc = f"{norm_host}:{port}" if port is not None and port != 443 else norm_host

    path = parsed.path if parsed.path else "/"
    if not path.endswith("/"):
        path = path + "/"

    return f"https://{norm_netloc}{path}"


# ── Provider functions ────────────────────────────────────────────────────────


def _bearer_provider(
    origin: str, env: Mapping[str, str]
) -> BearerHttpAccess | None:
    """Resolve bearer-token access from the supplied environment mapping.

    Reads only ``AGENTBUNDLE_HTTP_BEARER_TOKEN``. Returns ``None`` when the
    key is absent or empty (unavailable). Raises ``HttpAccessError`` with code
    ``"invalid_bearer"`` when the token is present but contains a character
    outside visible ASCII (U+0021–U+007E); this is configured-but-broken and
    terminates resolution without falling through to lower providers.
    """
    token = env.get("AGENTBUNDLE_HTTP_BEARER_TOKEN", "")
    if not token:
        return None
    # Visible ASCII: 0x21 (!) through 0x7E (~), inclusive.
    if not all(0x21 <= ord(c) <= 0x7E for c in token):
        raise HttpAccessError("bearer", "invalid_bearer")
    return BearerHttpAccess(origin=origin, authorization="Bearer " + token)


def _jfrog_provider(
    origin: str,
    target_url: str,
    env: Mapping[str, str],
    *,
    _os_name: str | None = None,
) -> JfrogCliHttpAccess | None:
    """Resolve JFrog CLI access by discovering a URL-matching profile.

    Locates ``jf`` on the supplied ``env`` PATH, runs a bounded profile
    discovery, selects the unique longest matching profile, validates the CLI
    version, and returns a pinned ``JfrogCliHttpAccess``.

    Returns ``None`` (unavailable) when: no candidate ``jf`` is found and no
    explicit JFrog server was requested; or successful discovery finds no
    URL-matching profile and no explicit server was requested.

    Raises ``HttpAccessError`` for every configured-but-broken condition.

    No profile data, server ID, path, or stream content ever reaches exception
    text, args, repr, or logs.  All exception chains are suppressed via
    ``from None``.

    Args:
        origin: Normalized HTTPS origin of the target URL.
        target_url: Full normalized HTTPS target URL (origin + path, no
            query/fragment/user-info).
        env: Environment mapping; ``os.environ`` is never read.
        _os_name: Override for ``os.name``; used in tests to exercise the
            Windows branch on POSIX CI.
    """
    explicit_id: str | None = env.get("JFROG_CLI_SERVER_ID") or None

    # ── Locate jf ────────────────────────────────────────────────────────────
    jf_path, refused = _locate_jf(env, _os_name=_os_name)
    if jf_path is None:
        # No executable candidate found (refused or absent).
        if explicit_id:
            raise HttpAccessError("jfrog", "jfrog_cli_not_executable")
        return None

    # ── Build child environment ───────────────────────────────────────────────
    child_env = _build_jfrog_child_env(env, _os_name=_os_name)

    # ── Profile discovery ─────────────────────────────────────────────────────
    try:
        disc_stdout, _disc_stderr, disc_rc = _run_bounded(
            [jf_path, "config", "show", "--format=json"],
            child_env,
            timeout=_JFROG_DISCOVERY_TIMEOUT,
            stdout_cap=_JFROG_DISCOVERY_STDOUT_CAP,
            stderr_cap=_JFROG_DISCOVERY_STDERR_CAP,
        )
    except _ChildTimeout:
        raise HttpAccessError("jfrog", "jfrog_discovery_timeout") from None
    except _ChildCapExceeded:
        raise HttpAccessError("jfrog", "jfrog_discovery_too_large") from None
    except OSError:
        raise HttpAccessError("jfrog", "jfrog_discovery_failed") from None

    if disc_rc != 0:
        raise HttpAccessError("jfrog", "jfrog_discovery_failed")

    # ── Parse discovery JSON ──────────────────────────────────────────────────
    try:
        profiles_raw = json.loads(disc_stdout)
    except (json.JSONDecodeError, ValueError):
        raise HttpAccessError("jfrog", "jfrog_discovery_malformed") from None

    if not isinstance(profiles_raw, list):
        raise HttpAccessError("jfrog", "jfrog_discovery_malformed")

    # ── Profile matching ──────────────────────────────────────────────────────
    # The target path for prefix matching (always ends with /).
    target_parsed = urlsplit(target_url)
    target_path = target_parsed.path or "/"

    # Dataclass-free: store eligible profiles as plain dicts.
    # Keys: server_id, norm_artf (full normalized artf URL), norm_platform,
    # artf_origin, artf_path (ends with /), artf_path_len.
    eligible: list[dict] = []

    for item in profiles_raw:
        if not isinstance(item, dict):
            raise HttpAccessError("jfrog", "jfrog_discovery_malformed")

        # Retain only the required fields; all others (including accessToken) are
        # not accessed and therefore never stored.
        server_id = item.get("serverId")
        url_field = item.get("url")
        artf_field = item.get("artifactoryUrl")

        if not (
            isinstance(server_id, str)
            and isinstance(url_field, str)
            and isinstance(artf_field, str)
        ):
            raise HttpAccessError("jfrog", "jfrog_discovery_malformed")

        # Normalize both URLs; ineligible scheme/user-info/query/fragment → skip.
        norm_artf = _normalize_jfrog_url(artf_field)  # may raise malformed
        if norm_artf is None:
            continue

        norm_platform = _normalize_jfrog_url(url_field)  # may raise malformed
        if norm_platform is None:
            continue

        # Split normalized artf URL into origin + path.
        artf_parsed = urlsplit(norm_artf)
        artf_origin = f"https://{artf_parsed.netloc}"
        artf_path = artf_parsed.path  # guaranteed to end with /

        # Eligibility: artf origin must equal target origin, and artf path must
        # be a segment-aligned prefix of the target path.
        if artf_origin != origin:
            continue
        if not target_path.startswith(artf_path):
            continue

        # Topology check: artf URL must be a same-origin, segment-aligned
        # descendant of the platform URL.
        plat_parsed = urlsplit(norm_platform)
        plat_origin = f"https://{plat_parsed.netloc}"
        plat_path = plat_parsed.path  # guaranteed to end with /

        if plat_origin != artf_origin or not artf_path.startswith(plat_path):
            raise HttpAccessError("jfrog", "unsupported_jfrog_topology")

        eligible.append(
            {
                "server_id": server_id,
                "norm_artf": norm_artf,
                "norm_platform": norm_platform,
                "artf_origin": artf_origin,
                "artf_path": artf_path,
                "artf_path_len": len(artf_path),
            }
        )

    # ── Profile selection ─────────────────────────────────────────────────────
    if explicit_id:
        matches = [p for p in eligible if p["server_id"] == explicit_id]
        if not matches:
            raise HttpAccessError("jfrog", "jfrog_profile_mismatch")
        selected = matches[0]
    else:
        if not eligible:
            return None  # No matching profile → unavailable.
        max_len = max(p["artf_path_len"] for p in eligible)
        longest = [p for p in eligible if p["artf_path_len"] == max_len]
        if len(longest) > 1:
            raise HttpAccessError("jfrog", "jfrog_profile_ambiguous")
        selected = longest[0]

    # ── Version probe ─────────────────────────────────────────────────────────
    try:
        ver_stdout, _ver_stderr, ver_rc = _run_bounded(
            [jf_path, "--version"],
            child_env,
            timeout=_JFROG_PROBE_TIMEOUT,
            stdout_cap=_JFROG_PROBE_CAP,
            stderr_cap=_JFROG_PROBE_CAP,
        )
    except _ChildTimeout:
        raise HttpAccessError("jfrog", "jfrog_probe_timeout") from None
    except _ChildCapExceeded:
        raise HttpAccessError("jfrog", "jfrog_probe_too_large") from None
    except OSError:
        raise HttpAccessError("jfrog", "jfrog_probe_failed") from None

    if ver_rc != 0:
        raise HttpAccessError("jfrog", "jfrog_probe_failed")

    try:
        ver_text = ver_stdout.decode("ascii", errors="replace")
    except Exception:
        raise HttpAccessError("jfrog", "jfrog_probe_failed") from None

    m = _JFROG_VERSION_RE.search(ver_text)
    if not m:
        raise HttpAccessError("jfrog", "jfrog_probe_failed")

    version: tuple[int, int, int] = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    if version < _JFROG_MIN_VERSION:
        raise HttpAccessError("jfrog", "incompatible_jfrog_cli")

    # ── Success ───────────────────────────────────────────────────────────────
    # Return with normalized URLs only; no profile data, server ID content,
    # or stream material is stored beyond the selected non-secret fields.
    return JfrogCliHttpAccess(
        server_id=selected["server_id"],
        platform_url=selected["norm_platform"],
        artifactory_url=selected["norm_artf"],
    )


def _netrc_provider(
    origin: str, env: Mapping[str, str]
) -> NetrcHttpAccess | None:
    """Resolve .netrc Basic-auth access for *origin* from the standard user file.

    Reads only the standard per-user ``.netrc`` location derived from the
    supplied ``env`` mapping (``HOME`` on POSIX; ``USERPROFILE`` then
    ``HOMEDRIVE``+``HOMEPATH`` on Windows).  Never reads ``os.environ``.

    Returns ``None`` (unavailable) when no home directory can be resolved,
    the file is absent, or no exact machine key matches the target.  Raises
    ``HttpAccessError`` for configured-but-broken conditions:

    - ``netrc_unreadable``: file present but not a regular file, or any
      ``OSError`` on open or read, or file exceeds the 1 MiB bound.
    - ``netrc_unsafe`` (POSIX only): unsafe group/other permission bits or
      owner mismatch.
    - ``netrc_malformed``: UTF-8 decode failure, parse error, unencodable
      machine key, ambiguous normalized key, a login containing ``:``, or a
      control character in either value.
    - ``netrc_incomplete``: matched record lacks login or password.

    No input value (path, machine name, login, password, or file content)
    ever reaches exception text, args, repr, or logs; all exception chains
    are suppressed via ``from None``.
    """
    # 1. Home directory from env only — never os.environ or expanduser.
    home = _resolve_home_dir(env)
    if not home:
        return None

    # 2. Standard user .netrc path only; never a working-directory or input path.
    netrc_path = Path(home) / ".netrc"

    # 3. Open once; use os.fstat to check the open fd, avoiding TOCTOU races.
    try:
        fd = os.open(str(netrc_path), os.O_RDONLY)
    except FileNotFoundError:
        return None  # Absent → unavailable.
    except OSError:
        raise HttpAccessError("netrc", "netrc_unreadable") from None

    try:
        try:
            st = os.fstat(fd)
        except OSError:
            raise HttpAccessError("netrc", "netrc_unreadable") from None

        # Not a regular file (e.g. a directory named .netrc) → unreadable.
        if not stat.S_ISREG(st.st_mode):
            raise HttpAccessError("netrc", "netrc_unreadable") from None

        # POSIX permissions: any group/other bit or wrong owner → unsafe.
        # Windows has no comparable permission bits, so it skips this check.
        if os.name != "nt" and ((st.st_mode & 0o077) or st.st_uid != os.getuid()):
            raise HttpAccessError("netrc", "netrc_unsafe") from None

        # Bounded read: reject files over 1 MiB so a hostile file cannot
        # exhaust memory.
        try:
            raw = os.read(fd, _NETRC_MAX_BYTES + 1)
        except OSError:
            raise HttpAccessError("netrc", "netrc_unreadable") from None

        if len(raw) > _NETRC_MAX_BYTES:
            raise HttpAccessError("netrc", "netrc_unreadable") from None
    finally:
        with contextlib.suppress(OSError):
            os.close(fd)

    # 4. Decode as UTF-8; a decode error means the file is malformed.
    try:
        content = raw.decode("utf-8")
    except (UnicodeDecodeError, ValueError):
        raise HttpAccessError("netrc", "netrc_malformed") from None

    # 5. Parse with the stdlib netrc parser via _StringNetrc, which does not
    # re-open the file.  NetrcParseError → malformed; suppress context so
    # parser text (which may include file lines) never surfaces.
    try:
        parsed = _StringNetrc(content)
    except _netrc_module.NetrcParseError:
        raise HttpAccessError("netrc", "netrc_malformed") from None
    except HttpAccessError:
        raise
    except Exception:
        raise HttpAccessError("netrc", "netrc_malformed") from None

    # 6. Build a mapping from normalized key to (login, password), skipping
    # "default" entries, which never authenticate.  Two raw keys that normalize to the
    # same key with different credentials → ambiguous → malformed.
    normalized_map: dict[str, tuple[str, str]] = {}
    for raw_key, (login, _account, password) in parsed.hosts.items():
        if raw_key == "default":
            continue
        raw_host_str, port_str = _split_netrc_key(raw_key)
        try:
            norm_host = _normalize_netrc_host(raw_host_str)
        except UnicodeError:
            raise HttpAccessError("netrc", "netrc_malformed") from None
        norm_key = f"{norm_host}:{port_str}" if port_str else norm_host
        new_creds = (login or "", password or "")
        if norm_key in normalized_map and normalized_map[norm_key] != new_creds:
            raise HttpAccessError("netrc", "netrc_malformed") from None
        normalized_map[norm_key] = new_creds

    # 7. Derive lookup keys from the already-normalized origin: host:port first
    # for a non-default port, then host; host only for 443.
    # The origin is "https://<host>[:port]" with the host already normalized
    # (IPv6 bracketed, as the .netrc keys above are), and 443 never present.
    host_port = origin[len("https://"):]
    target_host, target_port = _split_netrc_key(host_port)
    lookup_keys = [host_port, target_host] if target_port else [target_host]

    match: tuple[str, str] | None = None
    for key in lookup_keys:
        if key in normalized_map:
            match = normalized_map[key]
            break

    if match is None:
        return None  # No exact match → unavailable.

    login, password = match

    # 8. Validate the matched record: login and password are both required.
    if not login or not password:
        raise HttpAccessError("netrc", "netrc_incomplete") from None

    # A colon in the login cannot form a safe Basic credential.
    if ":" in login:
        raise HttpAccessError("netrc", "netrc_malformed") from None

    # Control characters in either value (U+0000–U+001F and U+007F).
    for ch in login + password:
        cp = ord(ch)
        if cp < 0x20 or cp == 0x7F:
            raise HttpAccessError("netrc", "netrc_malformed") from None

    # 9. Derive the Basic authorization value and bind it to the origin.
    user_pass_bytes = f"{login}:{password}".encode()
    authorization = "Basic " + base64.b64encode(user_pass_bytes).decode("ascii")
    return NetrcHttpAccess(origin=origin, authorization=authorization)


def _anonymous_provider(origin: str) -> AnonymousHttpAccess:
    """Return anonymous access for the given origin."""
    return AnonymousHttpAccess(origin=origin)


# ── Public resolver ───────────────────────────────────────────────────────────


def resolve_http_access(
    target_url: str, *, env: Mapping[str, str]
) -> HttpAccess:
    """Resolve target-bound HTTP access for an HTTPS catalogue URL.

    Validates the target URL first (before any provider is evaluated), then
    selects the first available provider in fixed order: bearer, JFrog CLI,
    .netrc, anonymous.

    The result is bound to the normalized HTTPS origin derived from
    ``target_url``; the same result is reused for the descriptor and its
    resolved archive.

    Args:
        target_url: The initial HTTPS catalogue URL. Must be HTTPS, have a
            host, carry no user info, and use a valid port.
        env: Environment mapping used as the sole credential source. Never
            reads ``os.environ``; pass a controlled mapping (or ``{}`` for
            no-credential resolution).

    Returns:
        One of ``BearerHttpAccess``, ``JfrogCliHttpAccess``,
        ``NetrcHttpAccess``, or ``AnonymousHttpAccess``.

    Raises:
        HttpAccessError: The target URL is invalid (provider ``"target"``,
            code ``"invalid_target_host"``), or a configured provider is
            broken (provider ``"bearer"``, ``"jfrog"``, or ``"netrc"`` with
            the applicable code).
    """
    # ── Target check ─────────────────────────────────────────────────────────
    # Performed before any provider is evaluated; a bad target is a caller
    # error, not a provider error.

    try:
        parsed = urlsplit(target_url)
    except Exception:
        raise HttpAccessError("target", "invalid_target_host") from None

    if parsed.scheme != "https":
        raise HttpAccessError("target", "invalid_target_host")

    # Empty string means no host.
    hostname = _raw_hostname(parsed.netloc)
    if not hostname:
        raise HttpAccessError("target", "invalid_target_host")

    # Reject any user info embedded in the URL.
    if parsed.username is not None or parsed.password is not None:
        raise HttpAccessError("target", "invalid_target_host")

    # Port: None means "not present"; a ValueError means malformed.
    try:
        port = parsed.port
    except ValueError:
        raise HttpAccessError("target", "invalid_target_host") from None

    # Normalize the host under the single profile (IDNA2003 via stdlib codec).
    try:
        normalized_host = _normalize_host(hostname)
    except UnicodeError:
        raise HttpAccessError("target", "invalid_target_host") from None

    # ── Origin string ─────────────────────────────────────────────────────────
    # Omit the port when it is the HTTPS default (443).
    if port is not None and port != 443:
        origin = f"https://{normalized_host}:{port}"
    else:
        origin = f"https://{normalized_host}"

    # ── Provider selection ────────────────────────────────────────────────────
    # Fixed order: bearer → JFrog CLI → .netrc → anonymous. Each function is
    # referenced by module-global name so monkeypatching in tests replaces the
    # live lookup without requiring a list-entry update. Anonymous is
    # always the floor.
    #
    # A provider returning None means "unavailable — try the next one."
    # A provider raising HttpAccessError means "configured but broken —
    # stop selection and propagate the error."
    # Normalized target URL for JFrog profile path-prefix matching.
    # Includes origin + path only; query and fragment are excluded.
    norm_target_path = parsed.path or "/"
    normalized_target = f"{origin}{norm_target_path}"

    result: HttpAccess | None = _bearer_provider(origin, env)
    if result is not None:
        return result

    result = _jfrog_provider(origin, normalized_target, env)
    if result is not None:
        return result

    result = _netrc_provider(origin, env)
    if result is not None:
        return result

    return _anonymous_provider(origin)
