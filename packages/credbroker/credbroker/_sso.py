"""SSO web-session cookie resolution.

A second consumer-resolution family alongside the token ``creds`` family. Where
``load_credentials`` resolves a token, ``load_sso_cookies`` resolves a *captured
SSO web session* into an on-disk cookie-jar path by subprocess-invoking the
unchanged ``sso-broker.py`` engine.

Two contracts shape this module:

* **Path-not-value handoff.** The resolver returns the jar's
  *path*, never its bytes. No cookie value crosses ``argv`` (only the profile
  name does), no cookie value is logged, and the engine writes the jar to its own
  ``0600`` floor — the consumer reads it in-process and is responsible for never
  echoing it (the at-rest floor is the broker's own responsibility).
* **Fail-closed.** Anything other than a clean exit-0-with-readable-path raises
  :class:`SsoSessionUnavailableError` with a verbatim re-``register`` remediation.
  It never returns a path it could not verify, and a caller on the cookie path
  must never fall through to the token path on this error.

The validation primitives that guard the consumer's ``sso-config.toml`` and the
load-time cookie-jar confinement live alongside this resolver (added in spec task
T2) so the security-control surface is single-sourced and reusable by any
platform integration, not just atlassian.
"""

from __future__ import annotations

import contextlib
import os
import re
import signal
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Literal
from urllib.parse import urlsplit

__all__ = [
    "SsoError",
    "SsoBrokerNotInstalledError",
    "SsoSessionUnavailableError",
    "SsoConfigError",
    "load_sso_cookies",
    "validate_sso_profile",
    "validate_https_url",
    "validate_root_relative_endpoint",
    "domain_in_cookie_domains",
    "filter_jar_to_domains",
    "require_host_in_cookie_domains",
]

# The engine is installed by the credential-brokers pack at this user-scope path
# (mirrored by ``sso-broker.py``'s own module docstring). Composed
# from parts so no full literal path string appears, matching the broker's own
# convention.
_BROKER_TAIL = (".agentbundle", "bin", "sso-broker.py")


class SsoError(Exception):
    """Base class for SSO consumer-resolution failures."""


class SsoBrokerNotInstalledError(SsoError):
    """The ``sso-broker.py`` engine is not installed at its expected path."""


class SsoSessionUnavailableError(SsoError):
    """No usable SSO session for the profile — the caller must re-``register``.

    Raised for every non-success branch of ``get-cookies`` (the engine returns a
    non-zero exit for both "profile not registered" and "no jar"), for an
    unreadable jar path, and for any uncaught engine exception. Fail-closed: the
    cookie path must surface this, never silently downgrade to the token path.
    """


class SsoConfigError(SsoError):
    """An ``sso-config.toml`` value, or a runtime host, violates the SSO
    confinement contract — a non-``https`` URL, a non-root-relative endpoint, or a
    send-host outside the declared ``cookie_domains``. Validation primitives raise
    this; the consumer fails closed before any cookie-bearing request leaves the
    process.
    """


class SsoBrokerUnavailableError(SsoError):
    """The engine could not be run to a conclusion — timeout, spawn failure, a
    materialisation write failure, or an unexpected exit code.

    Deliberately **not** a :class:`SsoSessionUnavailableError`: a consumer's
    auto-recovery keys on that type, and a slow or locked keychain holding a
    perfectly valid session must not trigger a browser recapture. A timeout is
    not an expired session.
    """


def _broker_path() -> Path:
    """Resolve the engine path under the user's home (``~/.agentbundle/bin``)."""
    return Path.home().joinpath(*_BROKER_TAIL)


# --- profile grammar ----------------------------------------------------------
#
# ``profile`` is interpolated into filesystem paths and a keychain target name by
# the engine, so it is confined to a charset that cannot escape either. The
# engine carries a byte-identical copy of both constants — it cannot import this
# package (``credbroker`` subprocesses it, never the reverse) — and
# ``test_sso_recapture.py``'s parity test pins the two equal. Change one, change
# the other.

_SSO_PROFILE_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"

# Case-insensitive Win32 reserved device names. On Windows ``CON.toml`` resolves
# to the console device regardless of the directory it is written to, so the
# check is applied to the name's first dot-separated component rather than to the
# whole string.
_RESERVED_DEVICE_NAMES = frozenset({
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
})

_PROFILE_RE = re.compile(_SSO_PROFILE_PATTERN)


def validate_sso_profile(profile: object) -> None:
    """Fail closed unless *profile* is a safe SSO profile name.

    ``re.fullmatch`` rather than ``re.match``: the pattern's ``$`` matches before
    a trailing newline, so ``re.match`` would admit ``"jira\\n"`` — which reaches
    the engine's argv and its path composition.

    A non-``str`` raises :class:`SsoConfigError` (the consumer's exit-2
    credential band), never ``TypeError`` (which would escape as exit 1).
    """
    if not isinstance(profile, str):
        raise SsoConfigError(
            f"sso profile must be a string, got {type(profile).__name__}"
        )
    if not _PROFILE_RE.fullmatch(profile):
        raise SsoConfigError(
            f"sso profile {profile!r} must match {_SSO_PROFILE_PATTERN} "
            f"(1–64 chars, leading alphanumeric, then alphanumerics, '.', '_', '-')"
        )
    if profile.split(".", 1)[0].upper() in _RESERVED_DEVICE_NAMES:
        raise SsoConfigError(
            f"sso profile {profile!r} is a Windows reserved device name"
        )


# --- bounded, environment-confined engine spawn -------------------------------
#
# One helper behind every engine invocation. Three properties it exists to
# guarantee, none of which a per-consumer ``subprocess.run`` reliably gets right:
#
# * a **wall-clock bound**, per operation (the three differ by an order of
#   magnitude — derivations are in the spec's AC3 table);
# * a **whole-tree kill** on timeout or interrupt, so playwright's Chromium
#   cannot survive holding a live corporate session and the ``browser-state``
#   lock;
# * an **explicitly composed environment**, so a browser spawned from an agent
#   session cannot inherit ``JIRA_API_TOKEN`` or an unrelated provider key.

# Per-operation wall-clock bounds. ``register`` carries a 300 s human sign-in
# poll and a second seeding launch; ``refresh`` is headless with a bounded
# silent-completion window and no poll at all; ``get-cookies`` is a keychain
# unlock and a read.
_TIMEOUT_REGISTER_S = 540.0
_TIMEOUT_REFRESH_S = 180.0
_TIMEOUT_GET_COOKIES_S = 30.0

# Grace between the polite and the forceful kill, per step.
_KILL_GRACE_S = 5.0

# Corporate-network reachability and trust-store passthrough. ``REQUESTS_CA_BUNDLE``
# and the lowercase proxy forms are load-bearing, not decorative: the former is
# where an enterprise's CA lands for the requests-compatible tools, and Chromium
# and curl read the lowercase names.
_ENV_ALLOWLIST_NETWORK = (
    "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
    "http_proxy", "https_proxy", "no_proxy",
    "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE",
)

# POSIX process basics: without these the interpreter starts but cannot find its
# own home, temp dir, or the ``security`` CLI the macOS keychain backend shells to.
_ENV_ALLOWLIST_POSIX_BASE = (
    "PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "USER", "LOGNAME",
)

# The Windows minimum without which Chromium and CPython's TLS initialisation
# fail to start at all.
_ENV_ALLOWLIST_WINDOWS_BASE = (
    "PATH", "PATHEXT", "COMSPEC", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR",
    "TEMP", "TMP", "APPDATA", "LOCALAPPDATA", "PROGRAMFILES",
    "USERPROFILE", "HOMEDRIVE", "HOMEPATH",
)

# Browser-only additions. ``NODE_EXTRA_CA_CERTS`` is where a corporate MITM CA
# must land for playwright's Node driver; the POSIX display/session variables are
# what let a headed Chromium find a screen. None of them belong on a
# ``get-cookies`` spawn, which launches no browser.
_ENV_ALLOWLIST_BROWSER_EXTRA = (
    "NODE_EXTRA_CA_CERTS", "PLAYWRIGHT_BROWSERS_PATH",
)
_ENV_ALLOWLIST_BROWSER_EXTRA_POSIX = (
    "DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY", "XDG_RUNTIME_DIR",
    "XDG_SESSION_TYPE", "DBUS_SESSION_BUS_ADDRESS",
)

_ENGINE_ENV_ALLOWLIST = frozenset(
    _ENV_ALLOWLIST_NETWORK
    + (_ENV_ALLOWLIST_WINDOWS_BASE if os.name == "nt" else _ENV_ALLOWLIST_POSIX_BASE)
)
_BROWSER_ENV_ALLOWLIST = frozenset(
    _ENGINE_ENV_ALLOWLIST
    | frozenset(_ENV_ALLOWLIST_BROWSER_EXTRA)
    | frozenset(() if os.name == "nt" else _ENV_ALLOWLIST_BROWSER_EXTRA_POSIX)
)

EnvProfile = Literal["browser", "engine"]


def _compose_env(env_profile: EnvProfile) -> dict[str, str]:
    """Build the child environment from the allowlist, never from ``os.environ``.

    A name absent from the parent is absent from the child; nothing is defaulted.
    """
    allowlist = (
        _BROWSER_ENV_ALLOWLIST if env_profile == "browser" else _ENGINE_ENV_ALLOWLIST
    )
    return {
        name: value
        for name, value in os.environ.items()
        if name in allowlist
    }


def _kill_process_tree(proc: subprocess.Popen) -> None:
    """Kill *proc* and everything it spawned.

    POSIX: the child was started with ``start_new_session=True``, so its pid is
    also its process-group id — SIGTERM the group, wait out a bounded grace, then
    SIGKILL the survivors. Windows has no ``os.killpg``; ``taskkill /T /F`` walks
    the process tree instead, with ``terminate()`` then ``kill()`` behind it for
    the case where ``taskkill`` is absent or refuses.
    """
    killpg = getattr(os, "killpg", None)
    if killpg is not None:
        with contextlib.suppress(OSError):
            killpg(proc.pid, signal.SIGTERM)
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=_KILL_GRACE_S)
        with contextlib.suppress(OSError):
            killpg(proc.pid, signal.SIGKILL)
    else:  # pragma: no cover — Windows arm; exercised on the parity runner
        with contextlib.suppress(OSError, subprocess.SubprocessError):
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                capture_output=True,
                check=False,
                timeout=_KILL_GRACE_S,
            )
        try:
            proc.wait(timeout=_KILL_GRACE_S)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(OSError):
                proc.terminate()
            try:
                proc.wait(timeout=_KILL_GRACE_S)
            except subprocess.TimeoutExpired:
                with contextlib.suppress(OSError):
                    proc.kill()
    with contextlib.suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=_KILL_GRACE_S)


def _spawn_broker(
    argv: list[str],
    *,
    timeout: float,
    env_profile: EnvProfile,
    capture: bool,
) -> subprocess.CompletedProcess[str]:
    """Run the engine under a wall-clock bound with a whole-tree kill.

    :param capture: when true, the child's **stdout** is captured and returned on
        the result (``get-cookies`` answers with the materialised jar path there,
        and ``load_sso_cookies`` parses it) while stderr stays inherited so engine
        diagnostics still reach the operator. When false — ``register`` and
        ``refresh``, both interactive — every stream is inherited and
        ``stdout`` on the result is ``None``.
    :returns: the completed process. Callers map its ``returncode`` onto the
        per-verb taxonomy; the helper itself is verb-agnostic.
    :raises SsoBrokerUnavailableError: the engine could not be spawned, exceeded
        *timeout*, or was interrupted. Never
        :class:`SsoSessionUnavailableError` — none of these means the stored
        session is gone.
    """
    env = _compose_env(env_profile)
    try:
        proc = subprocess.Popen(  # noqa: S603 — argv is composed, never shell
            argv,
            stdout=subprocess.PIPE if capture else None,
            env=env,
            # POSIX only (silently unused on Windows): puts the child and every
            # descendant in a fresh process group so the kill above reaches all
            # of them.
            start_new_session=True,
            text=True,
            encoding="utf-8",
            errors="surrogateescape",
        )
    except OSError as exc:
        raise SsoBrokerUnavailableError(
            f"could not run the sso-broker engine: {type(exc).__name__}"
        ) from exc

    try:
        stdout, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        _kill_process_tree(proc)
        raise SsoBrokerUnavailableError(
            f"sso-broker {_verb_of(argv)} exceeded its {timeout:g}s bound and was "
            f"terminated; the stored session was not changed"
        ) from exc
    except BaseException:
        # KeyboardInterrupt included, deliberately: a Ctrl-C must not leave a
        # headed Chromium holding the browser-state lock.
        _kill_process_tree(proc)
        raise

    return subprocess.CompletedProcess(argv, proc.returncode, stdout, None)


def _verb_of(argv: list[str]) -> str:
    """The engine verb in *argv*, for messages. Never echoes the profile."""
    for arg in argv:
        if arg in ("register", "refresh", "get-cookies", "test", "rm", "list-profiles"):
            return arg
    return "engine"


def load_sso_cookies(profile: str) -> Path:
    """Resolve *profile*'s captured SSO session to an on-disk cookie-jar path.

    Subprocess-invokes ``sso-broker.py get-cookies <profile>`` with the parent
    interpreter, inheriting the process environment (corporate proxy / trust-store
    passthrough). Proceeds **only** on exit 0 with a readable jar
    path; every other outcome fails closed.

    :returns: the path to the ``0600`` cookie jar the engine materialised.
    :raises SsoBrokerNotInstalledError: the engine is absent at its expected path.
    :raises SsoSessionUnavailableError: the profile is unregistered, no jar
        exists, the jar path is unreadable, or the engine raised.
    """
    broker = _broker_path()
    if not broker.is_file():
        raise SsoBrokerNotInstalledError(
            f"sso-broker not installed at {broker}; install the credential-brokers "
            f"pack, then run 'sso-broker register {profile}'"
        )

    remediation = (
        f"SSO session unavailable for profile {profile}; "
        f"run 'sso-broker register {profile}'"
    )

    try:
        result = subprocess.run(
            [sys.executable, str(broker), "get-cookies", profile],
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ},
        )
    except OSError as exc:
        # Engine present but unspawnable (permissions, interpreter gone, …).
        raise SsoSessionUnavailableError(remediation) from exc

    if result.returncode != 0:
        raise SsoSessionUnavailableError(remediation)

    jar_path = Path(result.stdout.strip())
    if not jar_path.is_file():
        raise SsoSessionUnavailableError(remediation)

    return jar_path


# --- SSO confinement primitives ----------------------------------------------
#
# These are the security-control surface the unchanged ``sso-broker.py`` engine
# does *not* perform and that this module adds *above* it: an https-only scheme guard,
# a root-relative endpoint guard, and the cookie-domain confinement that filters
# the engine's deliberately over-broad captured jar down to the declared domains.
# They are pure functions (no I/O), reusable by any platform integration, so the
# control can't drift across consumers.


def validate_https_url(value: str, *, field: str) -> None:
    """Reject *value* unless its scheme is exactly ``https``.

    Applied to ``login_url``, ``success_url_pattern``, and ``base_url`` — the
    cookie jar is a bearer secret, so a plaintext (``http``) or scheme-less
    destination is refused. ``success_url_pattern`` may carry pattern characters
    after the scheme; only the scheme is checked here.
    """
    scheme = urlsplit(value).scheme.lower()
    if scheme != "https":
        raise SsoConfigError(
            f"{field} must be an https URL (got scheme {scheme or '(none)'!r}): {value!r}"
        )


def validate_root_relative_endpoint(value: str, *, field: str = "validation_endpoint") -> None:
    """Reject *value* unless it is a root-relative path.

    Must lead with a single ``/`` and carry no scheme, host, or protocol-relative
    ``//`` prefix — so a validation endpoint can never be redirected off-host.
    """
    if not value.startswith("/") or value.startswith("//") or "://" in value:
        raise SsoConfigError(
            f"{field} must be a root-relative path (lead with '/', no scheme/host, "
            f"no '//'): {value!r}"
        )


def _normalize_domain(domain: str) -> str:
    """Lower-case and strip a leading dot — the broker stores domains via
    ``lstrip('.')`` while cookie ``domain`` fields keep a leading dot."""
    return domain.lstrip(".").lower()


def domain_in_cookie_domains(domain: str, cookie_domains: Iterable[str]) -> bool:
    """Normalized label-boundary suffix match.

    Both sides are dot-stripped and lower-cased; *domain* is admitted iff it
    equals an allowed domain or is a dot-delimited subdomain of one. The label
    boundary is load-bearing: ``evil-corp.example.com`` is rejected against
    ``corp.example.com`` (no ``.`` before ``corp``), while ``jira.corp.example.com``
    is admitted. This is the single normalization primitive shared by the
    cookie-jar filter and the send-host check.
    """
    cand = _normalize_domain(domain)
    if not cand:
        return False
    for allowed in cookie_domains:
        norm = _normalize_domain(allowed)
        if not norm:
            continue
        if cand == norm or cand.endswith("." + norm):
            return True
    return False


def filter_jar_to_domains(
    cookies: list[dict], cookie_domains: Iterable[str]
) -> list[dict]:
    """Reduce an over-broad captured jar to cookies within *cookie_domains*.

    The engine captures every cookie observed across the SSO/IdP/analytics
    redirect chain; the consumer filters that loaded jar to the declared domains
    at load time, before attaching it. Returns a new list; the caller must never
    write the result back to the broker path. A cookie with no ``domain``
    field is dropped (fail closed).
    """
    allowed = list(cookie_domains)
    return [c for c in cookies if domain_in_cookie_domains(c.get("domain", ""), allowed)]


def require_host_in_cookie_domains(host: str, cookie_domains: Iterable[str]) -> None:
    """Fail closed unless *host* is within the declared ``cookie_domains``.

    The consumer client's request base host must be a member of the confinement
    set before any cookie-bearing request leaves the process; a mismatch (a
    downstream edit drifting the base URL off-domain) raises.
    """
    if not domain_in_cookie_domains(host, cookie_domains):
        raise SsoConfigError(
            f"request host {host!r} is not within the declared cookie_domains "
            f"{list(cookie_domains)!r}; refusing to send the session cookie"
        )
