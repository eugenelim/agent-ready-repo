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
import http.client
import ipaddress
import json
import os
import re
import signal
import socket
import ssl
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

__all__ = [
    "SsoError",
    "SsoBrokerNotInstalledError",
    "SsoBrokerUnavailableError",
    "SsoSessionUnavailableError",
    "SsoStoreContendedError",
    "SsoProfileNotRegisteredError",
    "SsoRecaptureFailedError",
    "SsoInteractionRequiredError",
    "SsoConfigError",
    "load_sso_cookies",
    "refresh_sso_session",
    "register_sso_session",
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


class SsoStoreContendedError(SsoError):
    """Another process held this profile's store lock and did not release in time.

    Engine exit ``6``. **Recoverable, and recoverable in a way no other error
    here is:** the condition is transient and clears on its own, so the right
    response is to back off and retry the same call.

    Deliberately subclasses :class:`SsoError` directly and *neither*
    :class:`SsoSessionUnavailableError` nor :class:`SsoBrokerUnavailableError`.
    Under the first, a consumer's auto-recovery would launch a browser recapture
    over a perfectly valid session that was merely busy; under the second it
    would be treated as an engine failure and not retried at all.

    One caveat the caller should know: on a Windows ``%USERPROFILE%`` redirected
    to SMB, the engine cannot distinguish "someone holds it" from "this
    filesystem does not support locking" — both surface as the same errno — so
    this error can be *permanent* on such a machine rather than transient. A
    retry policy needs a bound.
    """


class SsoProfileNotRegisteredError(SsoSessionUnavailableError):
    """``refresh`` found no profile to refresh — first capture never happened.

    Subclasses :class:`SsoSessionUnavailableError` so every handler written
    against the older surface keeps working; the distinct type exists so a
    consumer can name the *register* remediation rather than a generic one.
    """


class SsoRecaptureFailedError(SsoError):
    """The engine attempted a recapture and could not complete it.

    Playwright absent, a sign-in the operator did not finish, a corrupt store —
    the engine returns ``3`` from many distinct sites and its stderr has already
    reached the operator, so this carries no guessed remediation of its own.
    """


class SsoInteractionRequiredError(SsoError):
    """A headless ``refresh`` could not re-establish the session unaided.

    The IdP session has expired too, so completing the flow needs a person.
    Terminal, not recoverable: retrying cannot help, and the engine deliberately
    did **not** put a login page on screen.
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
#   magnitude — see the per-operation timeout table below);
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
        popen = subprocess.Popen(  # noqa: S603 — argv is composed, never shell
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

    # The context manager closes the pipe and reaps on *every* exit path,
    # including the two below. Without it a consumer that retries after a
    # timeout leaks a file descriptor per attempt.
    with popen as proc:
        try:
            stdout, _ = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            _kill_process_tree(proc)
            raise SsoBrokerUnavailableError(
                f"sso-broker {_verb_of(argv)} exceeded its {timeout:g}s bound and "
                f"was terminated; the stored session was not changed"
            ) from exc
        except BaseException:
            # KeyboardInterrupt included, deliberately: a Ctrl-C must not leave a
            # headed Chromium holding the browser-state lock.
            _kill_process_tree(proc)
            raise
        returncode = proc.returncode

    return subprocess.CompletedProcess(argv, returncode, stdout, None)


def _verb_of(argv: list[str]) -> str:
    """The engine verb in *argv*, for messages. Never echoes the profile."""
    for arg in argv:
        if arg in ("register", "refresh", "get-cookies", "test", "rm", "list-profiles"):
            return arg
    return "engine"


def _require_broker(profile: str) -> Path:
    """Resolve the engine, or raise the not-installed remediation."""
    broker = _broker_path()
    if not broker.is_file():
        raise SsoBrokerNotInstalledError(
            f"sso-broker not installed at {broker}; install the credential-brokers "
            f"pack, then run 'sso-broker register {profile}'"
        )
    return broker


def load_sso_cookies(profile: str) -> Path:
    """Resolve *profile*'s captured SSO session to an on-disk cookie-jar path.

    Runs ``sso-broker.py get-cookies <profile>`` through the shared spawn
    helper — bounded, tree-killed, and with an explicitly composed environment
    minus the browser variables, since ``get-cookies`` launches no browser.
    Proceeds **only** on exit 0 with a readable jar path; every other outcome
    fails closed.

    The exit-code split is the security-relevant part. Only "the engine says
    there is no usable session" (exit 2) raises
    :class:`SsoSessionUnavailableError`, because that is what a consumer's
    auto-recovery keys on. A timeout, a spawn failure, or an engine-internal
    error raises :class:`SsoBrokerUnavailableError` instead: a slow or locked
    keychain holding a perfectly valid session must not trigger a browser
    recapture.

    :returns: the path to the ``0600`` cookie jar the engine materialised.
    :raises SsoConfigError: *profile* violates the grammar.
    :raises SsoBrokerNotInstalledError: the engine is absent at its expected path.
    :raises SsoSessionUnavailableError: the profile is unregistered, no jar
        exists, or the jar path is unreadable.
    :raises SsoStoreContendedError: engine exit 6 — another process holds this
        profile's store lock; retry the same call after a short back-off.
    :raises SsoBrokerUnavailableError: the engine could not be run to a
        conclusion, or failed internally.
    """
    validate_sso_profile(profile)
    broker = _require_broker(profile)

    remediation = (
        f"SSO session unavailable for profile {profile}; "
        f"run 'sso-broker register {profile}'"
    )

    result = _spawn_broker(
        [sys.executable, str(broker), "get-cookies", profile],
        timeout=_TIMEOUT_GET_COOKIES_S,
        env_profile="engine",
        capture=True,
    )

    if result.returncode == 2:
        raise SsoSessionUnavailableError(remediation)
    if result.returncode == 6:
        raise SsoStoreContendedError(
            f"the cookie store for {profile} is locked by another process; "
            f"retry after a short back-off"
        )
    if result.returncode != 0:
        raise SsoBrokerUnavailableError(
            f"sso-broker get-cookies failed for profile {profile} "
            f"(exit {result.returncode}); see the engine's output above"
        )

    jar_path = Path((result.stdout or "").strip())
    if not jar_path.is_file():
        raise SsoSessionUnavailableError(remediation)

    return jar_path


# --- recapture -----------------------------------------------------------------
#
# Two verbs, and the asymmetry between their signatures is the control.
#
# ``refresh_sso_session`` takes **only** a profile. That is how destination
# pinning is enforced: the function is structurally incapable of forwarding a
# sign-in destination, so no automated caller can choose where the browser goes
# — enforced by the signature rather than by a rule an implementer can forget.
# The engine reads the destination from the stored profile, which only a
# completed, operator-authorised ``register`` writes.
#
# The guarantee is a property of *this API*, not of the system. The engine is an
# executable on disk and any process running as the operator can invoke it
# directly with any destination. Consumers are expected to reach
# ``register_sso_session`` only from an operator-typed action — a convention
# each consumer's own skill rules enforce, not this library.


def refresh_sso_session(profile: str) -> None:
    """Re-establish *profile*'s expired session, without a human.

    Runs ``sso-broker refresh <profile>`` with **no** connection arguments. The
    signature accepts no destination parameter, and none is composed.

    The engine's ``refresh`` is headless: it succeeds only where the stored
    browser profile can complete the IdP flow unaided, and otherwise fails fast
    rather than presenting a login page.

    :raises SsoConfigError: *profile* violates the grammar.
    :raises SsoBrokerNotInstalledError: the engine is absent.
    :raises SsoProfileNotRegisteredError: engine exit 4 — nothing to refresh;
        the caller should route the operator to a first capture. **Recoverable.**
    :raises SsoInteractionRequiredError: engine exit 5 — a human is needed.
    :raises SsoStoreContendedError: engine exit 6 — the store is busy; retry.
    :raises SsoRecaptureFailedError: engine exit 3 or any unrecognised code.
    :raises SsoBrokerUnavailableError: timeout or spawn failure.
    """
    validate_sso_profile(profile)
    broker = _require_broker(profile)

    result = _spawn_broker(
        [sys.executable, str(broker), "refresh", profile],
        timeout=_TIMEOUT_REFRESH_S,
        env_profile="browser",
        capture=False,
    )
    code = result.returncode
    if code == 0:
        return
    if code == 4:
        raise SsoProfileNotRegisteredError(
            f"no SSO profile registered for {profile}; first capture has not "
            f"happened on this machine"
        )
    if code == 6:
        raise SsoStoreContendedError(
            f"the cookie store for {profile} is locked by another process; "
            f"retry after a short back-off"
        )
    if code == 5:
        raise SsoInteractionRequiredError(
            f"the stored browser session for {profile} could not re-authenticate "
            f"unaided; a person must sign in"
        )
    raise SsoRecaptureFailedError(
        f"sso-broker refresh failed for profile {profile} (exit {code}); "
        f"see the engine's output above"
    )


def register_sso_session(
    profile: str,
    *,
    login_url: str,
    success_url_pattern: str,
    cookie_domains: Iterable[str],
    validation_endpoint: str,
    session_filename: str | None = None,
    ttl_hint_minutes: int | None = None,
) -> None:
    """Perform *profile*'s **first** capture, at the supplied destination.

    The only function in this module that accepts a destination — see the note
    above. Always passes ``--ephemeral``: the capture runs in a throwaway
    browser context which then seeds the standing profile, rather than in the
    standing profile directly. The engine's ``register`` keeps ``persist=True``
    as its default, so a direct operator invocation is unaffected.

    Only connection parameters cross argv. No cookie value, cookie name, jar
    path, or ``Cookie:``-header shape appears in what this composes.

    :raises SsoConfigError: *profile* violates the grammar.
    :raises SsoBrokerNotInstalledError: the engine is absent.
    :raises SsoStoreContendedError: engine exit 6 — the store is busy; retry.
    :raises SsoRecaptureFailedError: engine exit 3 or any unrecognised code —
        including the ordinary "the operator did not finish signing in".
    :raises SsoBrokerUnavailableError: timeout or spawn failure.
    """
    validate_sso_profile(profile)
    broker = _require_broker(profile)

    argv = [
        sys.executable, str(broker), "register", profile,
        "--ephemeral",
        "--login-url", login_url,
        "--success-url-pattern", success_url_pattern,
        "--validation-endpoint", validation_endpoint,
    ]
    for domain in cookie_domains:
        argv += ["--cookie-domain", domain]
    if session_filename:
        argv += ["--session-filename", session_filename]
    if ttl_hint_minutes:
        argv += ["--ttl-hint-minutes", str(ttl_hint_minutes)]

    result = _spawn_broker(
        argv,
        timeout=_TIMEOUT_REGISTER_S,
        env_profile="browser",
        capture=False,
    )
    if result.returncode == 0:
        return
    if result.returncode == 6:
        # `_capture` serves both capture verbs, so `register` reaches the lock
        # too. Without this branch a contended register collapses into the
        # non-recoverable recapture-failed type.
        raise SsoStoreContendedError(
            f"the cookie store for {profile} is locked by another process; "
            f"retry after a short back-off"
        )
    raise SsoRecaptureFailedError(
        f"sso-broker register failed for profile {profile} "
        f"(exit {result.returncode}); see the engine's output above"
    )


# --- destination derivation ----------------------------------------------------
#
# Ask the **resource server** where to authenticate, instead of trusting the
# configured value. Vendor-agnostic by construction: the keying parameter is an
# explicit strategy list, because this broker is meant to serve any tool behind
# corporate SSO, not one vendor.
#
# **This is defence in depth, not the control.** It closes
# *login_url-poisoned-alone*. It does **not** close config poisoning, because
# the derivation target — ``base_url`` — lives in the same adopter- and
# agent-writable file: one write changes both, the attacker serves the redirect
# themselves, and the comparison passes. AWS's equivalent works only because its
# host suffix is hardcoded; there is no comparable invariant here, since
# everything we could compare against is also in the file. Consent for first
# capture rests on the operation being operator-typed.
#
# And it is bounded hard, because it is an outbound fetch on the credential
# path whose targets are partly attacker-influenceable: tier 1 fetches a URL
# read from a *response header*, then a second read from that document.

_DERIVE_SOCKET_TIMEOUT_S = 5.0
_DERIVE_TOTAL_BUDGET_S = 15.0
_DERIVE_BODY_CAP_BYTES = 64 * 1024

# No ``Authorization``, no ``Cookie``, no proxy-auth. Nothing that could turn a
# derivation probe into a credential-bearing request.
_DERIVE_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "credbroker-sso-derivation/1",
}


class _DerivationAbort(Exception):
    """One derivation hop refused or failed. Never leaves this module."""


class _DerivationBudget:
    """A monotonic deadline shared by every hop of one derivation."""

    def __init__(self, total: float) -> None:
        self._deadline = time.monotonic() + total

    def remaining(self) -> float:
        return self._deadline - time.monotonic()

    def check(self) -> None:
        if self.remaining() <= 0:
            raise _DerivationAbort("derivation budget exhausted")


class _DerivationResponse:
    """Status, headers and a capped body — the only shape the tiers see.

    Header names are lower-cased on the way in: urllib hands back an
    ``email.message.Message`` (case-insensitive), and normalising here means the
    tiers can look up a plain dict without caring which the server sent.
    """

    def __init__(self, status: int, headers: object, body: bytes) -> None:
        self.status = status
        items = getattr(headers, "items", None)
        self.headers: dict[str, str] = (
            {str(k).lower(): str(v) for k, v in items()} if items else {}
        )
        self.body = body

    def header(self, name: str, default: str = "") -> str:
        return self.headers.get(name.lower(), default)

    def json(self) -> dict:
        try:
            parsed = json.loads(self.body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise _DerivationAbort("derivation document is not JSON") from exc
        if not isinstance(parsed, dict):
            raise _DerivationAbort("derivation document is not an object")
        return parsed


def _derivation_ssl_context() -> ssl.SSLContext:
    """Strict verification, built explicitly.

    Never honours an ``--insecure``-style flag and never reuses a consumer's own
    TLS context. Constructed here rather than left to urllib's default so a
    process-wide ``ssl._create_default_https_context`` override cannot weaken
    the one request that decides where a human will type their password.

    Corporate trust stores are honoured the same way the cookie client honours
    them. ``create_default_context`` picks up ``SSL_CERT_FILE`` / ``SSL_CERT_DIR``
    through OpenSSL's default paths but knows nothing of ``REQUESTS_CA_BUNDLE``,
    which is where a MITM CA most often lands — and without it every derivation
    hop fails verification on exactly the corporate laptop this feature exists
    for. ``SSL_CERT_FILE`` wins when both are set, matching the cookie client.
    Strictness is unchanged: this adds a trust anchor, it never removes one.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    cafile = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    capath = os.environ.get("SSL_CERT_DIR")
    if cafile or capath:
        with contextlib.suppress(OSError, ssl.SSLError):
            ctx.load_verify_locations(cafile=cafile or None, capath=capath or None)
    return ctx


def _proxies_without_credentials(proxies: Mapping[str, str]) -> dict[str, str]:
    """Drop any userinfo from proxy URLs, so no ``Proxy-Authorization`` is sent."""
    cleaned: dict[str, str] = {}
    for scheme, url in proxies.items():
        parts = urlsplit(url)
        if parts.username or parts.password:
            host = parts.hostname or ""
            if parts.port:
                host = f"{host}:{parts.port}"
            cleaned[scheme] = urlunsplit(
                (parts.scheme, host, parts.path, parts.query, parts.fragment)
            )
        else:
            cleaned[scheme] = url
    return cleaned


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Hop cap 0: a 3xx is an *answer* here, never something to follow."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001, ANN201
        return None


def _derivation_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(
        _NoRedirect(),
        urllib.request.ProxyHandler(
            _proxies_without_credentials(urllib.request.getproxies())
        ),
        urllib.request.HTTPSHandler(context=_derivation_ssl_context()),
    )


# Read granularity. Small enough that the budget is re-checked often against a
# slow server, large enough that a healthy response is one or two reads.
_DERIVE_READ_CHUNK_BYTES = 8 * 1024


def _arm_socket_timeout(fp, seconds: float) -> None:  # noqa: ANN001
    """Best-effort: set the underlying socket's timeout to *seconds*.

    ``urllib`` fixes the timeout when the request is made, so it cannot shrink
    as a shared deadline drains. Reaching the socket is the only way to bound a
    late read by the time actually left. Guarded throughout: the attribute chain
    is an implementation detail, and losing it costs the tightening, not the
    read.
    """
    # Walk the `.fp` chain, bounded. The depth differs by object:
    #   HTTPResponse -> .fp (BufferedReader) -> .raw (SocketIO) -> ._sock
    #   HTTPError    -> .fp (HTTPResponse)   -> .fp -> .raw -> ._sock
    # Tier 1's expected 401 arrives as the second shape, so stopping at one
    # level left exactly that path on the original timeout.
    sock = None
    candidate = fp
    for _ in range(4):
        if candidate is None:
            break
        sock = getattr(getattr(candidate, "raw", None), "_sock", None)
        if sock is not None:
            break
        candidate = getattr(candidate, "fp", None)
    if sock is None:
        return
    with contextlib.suppress(OSError, ValueError, AttributeError):
        sock.settimeout(max(0.001, seconds))


def _read_capped(fp, budget: _DerivationBudget) -> bytes:  # noqa: ANN001
    """Read at most the cap, re-checking *budget* between reads.

    Uses ``read1``, not ``read``, and that is the whole point.
    ``HTTPResponse.read(n)`` delegates to a ``BufferedReader`` which blocks until
    it has *exactly* n bytes or EOF, while the socket timeout applies per
    ``recv`` — so one read can sit for chunk-size x timeout with no deadline
    consulted. Measured against a server sending one byte per 20 ms:
    ``read(8192)`` returned after 2.57 s, ``read1(8192)`` immediately. Chunking
    alone only divides that worst case by the chunk size; ``read1`` returns
    after a single ``recv``, which is what makes the budget an actual bound.

    It matters because the target can come out of an attacker-influenceable
    response header and ``check --register`` calls this synchronously.
    """
    chunks: list[bytes] = []
    total = 0
    # No `or fp.read` fallback: `read` is the unbounded call this function
    # exists to avoid, so its absence must be loud rather than a silent
    # reinstatement. Both `HTTPResponse` and `HTTPError` provide `read1`.
    reader = fp.read1
    while total <= _DERIVE_BODY_CAP_BYTES:
        budget.check()
        # Re-arm the socket to what is *left*, not to the per-hop cap. The
        # timeout is set once when the hop opens, so a server emitting one byte
        # just before each expiry keeps `read1` returning while the shared
        # deadline passes — overrunning the advertised total by nearly a full
        # socket timeout on the last read.
        _arm_socket_timeout(fp, min(_DERIVE_SOCKET_TIMEOUT_S, budget.remaining()))
        chunk = reader(min(_DERIVE_READ_CHUNK_BYTES, _DERIVE_BODY_CAP_BYTES + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
    if total > _DERIVE_BODY_CAP_BYTES:
        raise _DerivationAbort(
            f"derivation document exceeds the {_DERIVE_BODY_CAP_BYTES}-byte cap"
        )
    return b"".join(chunks)


def _resolves_to_internal_address(host: str, budget: _DerivationBudget) -> bool:
    """True when *host* resolves to any address a probe must not reach.

    Loopback, link-local (which is where cloud instance-metadata lives),
    unique-local and every RFC 1918 range. Checked against **resolved**
    addresses, not the literal, so a hostname pointing at ``127.0.0.1`` is
    caught too.

    Fails closed on a resolver error, and that is not merely conservative:
    ``_derivation_opener`` installs the environment's proxies, and a proxy
    resolves the hostname itself — so a name local DNS cannot see may still be
    reachable through it.

    **Known limit:** this resolves and then connects, so it does not close DNS
    rebinding. Closing that needs a pinned-address connection, which urllib
    does not offer.
    """
    # `getaddrinfo` is synchronous and takes no timeout, so a stalled resolver
    # would blow the derivation's advertised wall-clock bound by however long the
    # OS waits. Run it on a daemon thread and abandon it at the deadline — the
    # thread cannot be cancelled, but the caller stops waiting on it.
    resolved: list[list] = []
    failed: list[BaseException] = []

    def _resolve() -> None:
        try:
            resolved.append(socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP))
        except OSError as exc:
            failed.append(exc)

    worker = threading.Thread(target=_resolve, daemon=True)
    worker.start()
    worker.join(max(0.0, min(_DERIVE_SOCKET_TIMEOUT_S, budget.remaining())))
    if worker.is_alive():
        # Fail **closed**, for the same reason an `OSError` does below: an
        # unanswered lookup is not evidence the host is external.
        return True
    try:
        if failed:
            raise failed[0]
        infos = resolved[0]
    except OSError:
        # Fail **closed**. "Unresolvable locally" does not mean "unreachable":
        # `_derivation_opener` installs the environment's proxies, and a proxy
        # resolves the hostname itself — so a name local DNS cannot see is still
        # reachable through it. Treating a resolver failure as safe would let an
        # attacker-supplied hop reach proxy-visible internal services, which is
        # exactly what this guard exists to stop.
        return True
    for info in infos:
        try:
            address = ipaddress.ip_address(info[4][0])
        except ValueError:  # pragma: no cover — getaddrinfo returned a non-IP
            return True
        if (
            address.is_loopback
            or address.is_link_local
            or address.is_private
            or address.is_reserved
            or address.is_multicast
            or address.is_unspecified
        ):
            return True
    return False


def _derive_open(
    url: str, budget: _DerivationBudget, *, trusted_origin: str | None = None
) -> _DerivationResponse:
    """One bounded, https-only, unfollowed hop.

    :param trusted_origin: the ``scheme://authority`` the *operator configured*
        (``base_url``). Hops on that origin skip the internal-address check,
        because a corporate instance legitimately lives on an RFC 1918 host.

        Keyed to the origin rather than to "the first request", deliberately:
        RFC 9728 puts ``/.well-known/oauth-protected-resource`` on the resource
        server itself, so tier 1's *second* hop is normally the same origin as
        its first. Exempting only the first call would refuse that hop and
        silently kill tier 1 for every internally-hosted instance — the
        deployment this broker exists to serve.

        Every other hop's target is read out of a response header or body, so it
        is attacker-influenceable and must not be able to steer the operator's
        machine at loopback, the cloud metadata endpoint, or the corporate LAN.
    """
    try:
        parts = urlsplit(url)
    except ValueError as exc:
        # `urlsplit("https://[::1")` raises. Every caller past the first hop
        # passes a remote-controlled string, and this sits outside the request
        # try-block, so uncaught it escapes derivation entirely and surfaces as
        # exit 1 rather than the credential band.
        raise _DerivationAbort(f"derivation hop is not a parseable URL: {exc}") from exc
    scheme = parts.scheme.lower()
    if scheme != "https":
        # urllib honours file:// and ftp://, and tier 1's targets come out of an
        # attacker-influenceable header and document.
        raise _DerivationAbort(
            f"refusing a non-https derivation hop (scheme {scheme or '(none)'})"
        )
    origin = _origin(url)
    if origin != trusted_origin and _resolves_to_internal_address(
            parts.hostname or "", budget):
        raise _DerivationAbort(
            "refusing a derivation hop whose address is internal or could not "
            "be verified; the target came from a server response, not from "
            "your configuration"
        )
    budget.check()
    request = urllib.request.Request(url, headers=dict(_DERIVE_HEADERS), method="GET")
    # urllib applies one socket timeout to the connect and to each read, so this
    # bounds both phases; the shared budget bounds the whole chain.
    timeout = min(_DERIVE_SOCKET_TIMEOUT_S, max(0.001, budget.remaining()))
    try:
        with _derivation_opener().open(request, timeout=timeout) as resp:  # noqa: S310
            body = _read_capped(resp, budget)
            return _DerivationResponse(resp.status, resp.headers, body)
    except urllib.error.HTTPError as exc:
        # A 401 carrying WWW-Authenticate and a 302 carrying Location are the
        # answers two of the three tiers are looking for, not failures.
        with contextlib.closing(exc):
            return _DerivationResponse(exc.code, exc.headers, _read_capped(exc, budget))
    except _DerivationAbort:
        raise
    except (OSError, ValueError, http.client.HTTPException) as exc:
        # `HTTPException` (IncompleteRead, LineTooLong, …) is neither OSError nor
        # ValueError, and is raised during the body read — after urllib has
        # finished wrapping transport errors. Without it a malformed response
        # escapes derivation entirely and surfaces as a traceback.
        raise _DerivationAbort(f"derivation hop failed: {type(exc).__name__}") from exc


# The port a scheme implies when a URL omits it, so `https://host` and
# `https://host:443` are one origin. A server is free to spell either, and an
# RFC 9728 header spelling the explicit form would otherwise make the resource
# server's own metadata hop look off-origin.
_DEFAULT_PORTS = {"https": 443, "http": 80}


def _origin(url: str) -> str | None:
    """``scheme://host:port`` with the port made explicit, or ``None``.

    Two details that a naive `f"{scheme}://{hostname}:{port}"` gets wrong:

    * ``urlsplit(...).hostname`` **strips the brackets** from an IPv6 literal, so
      re-serialising without them produces ``https://::1:443`` — not a URL, and
      not comparable. They are put back.
    * ``port or default`` treats an explicit ``:0`` as absent, so
      ``https://h:0`` and ``https://h`` would compare equal. Only ``None``
      means "omitted".
    """
    try:
        parts = urlsplit(url)
    except ValueError:
        return None
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    if not host:
        return None
    try:
        port = parts.port
    except ValueError:
        return None
    if port is None:
        port = _DEFAULT_PORTS.get(scheme, 0)
    if ":" in host:          # IPv6 literal
        host = f"[{host}]"
    return f"{scheme}://{host}:{port}"


def _scheme_and_host(url: object) -> str | None:
    """The https origin of *url* as ``https://host:port``, or ``None``.

    Only the origin is ever compared: every tier's URL carries per-request
    ``state`` / ``SAMLRequest`` / ``nonce`` values that change on each call. The
    port is normalised so an implicit and an explicit ``:443`` compare equal.
    """
    if not isinstance(url, str):
        # Remote-supplied: a `Location` header or a JSON field. Unparseable, or
        # not a string, is "did not resolve a destination" — never an exception
        # out of derivation.
        return None
    origin = _origin(url)
    if origin is None or not origin.startswith("https://"):
        return None
    return origin


_RESOURCE_METADATA_RE = re.compile(r'resource_metadata\s*=\s*"([^"]+)"', re.IGNORECASE)


def _authorization_server_metadata_urls(issuer: str) -> list[str]:
    """The metadata URLs to try for an authorization-server *issuer*.

    The two standards build the URL differently, and appending both suffixes
    would miss every multi-tenant deployment:

    * **RFC 8414 § 3** inserts the well-known segment *between the authority and
      the path*, so issuer ``https://idp.example/tenant`` publishes at
      ``https://idp.example/.well-known/oauth-authorization-server/tenant``.
    * **OIDC Discovery** appends, giving
      ``https://idp.example/tenant/.well-known/openid-configuration``.

    Both are tried, in that order.
    """
    parts = urlsplit(issuer)
    path = parts.path.rstrip("/")
    authority = f"{parts.scheme}://{parts.netloc}"
    return [
        f"{authority}/.well-known/oauth-authorization-server{path}",
        f"{issuer.rstrip('/')}/.well-known/openid-configuration",
    ]


def _tier_protected_resource_metadata(
    base_url: str, budget: _DerivationBudget
) -> str | None:
    """RFC 9728 — OAuth 2.0 Protected Resource Metadata.

    The modern standard, adopted by MCP. Worth trying first and wrong to depend
    on: a live spike found Jira answering its REST 401 with the legacy
    ``WWW-Authenticate: OAuth realm="…"`` form instead.
    """
    trusted = _scheme_and_host(base_url)
    resp = _derive_open(base_url, budget, trusted_origin=trusted)
    if resp.status != 401:
        return None
    match = _RESOURCE_METADATA_RE.search(resp.header("WWW-Authenticate"))
    if not match:
        return None
    document = _derive_open(match.group(1), budget, trusted_origin=trusted).json()
    servers = document.get("authorization_servers")
    if not isinstance(servers, list):
        return None
    for issuer in servers:
        if _scheme_and_host(issuer) is None:
            continue
        for metadata_url in _authorization_server_metadata_urls(issuer):
            try:
                metadata = _derive_open(
                    metadata_url, budget, trusted_origin=trusted
                ).json()
            except _DerivationAbort:
                continue
            found = _scheme_and_host(metadata.get("authorization_endpoint"))
            if found:
                return found
    return None


def _tier_oidc_discovery(base_url: str, budget: _DerivationBudget) -> str | None:
    """OIDC Discovery / RFC 8414 — older than tier 1, far more widely deployed."""
    document = _derive_open(
        base_url.rstrip("/") + "/.well-known/openid-configuration",
        budget, trusted_origin=_scheme_and_host(base_url),
    ).json()
    return _scheme_and_host(document.get("authorization_endpoint"))


def _strategy_atlassian_seraph(base_url: str, budget: _DerivationBudget) -> str | None:
    """Atlassian/Seraph vendor probe.

    Verified by live spike 2026-08-05: ``GET https://jira.atlassian.com/login.jsp``
    answers ``302`` with ``Location: https://auth.atlassian.com/authorize?…``.

    **Named degradation.** Deriving from ``base_url`` does not work —
    ``/secure/Dashboard.jspa`` answers 200 — because SAML redirection fires only
    from ``login.jsp``. And ``login.jsp`` itself answers 302 only in forced-SSO
    mode; under SSO-with-local-fallback it answers 200 with a sign-in button and
    no ``Location``. Those adopters land on the cannot-derive branch.
    """
    resp = _derive_open(
        base_url.rstrip("/") + "/login.jsp", budget,
        trusted_origin=_scheme_and_host(base_url),
    )
    if not 300 <= resp.status < 400:
        return None
    return _scheme_and_host(resp.header("Location"))


# Opt-in per consumer: `confluence-crawler` and `bitbucket` share the Seraph
# framework and can ask for the same probe; a non-Atlassian consumer never runs
# it. SAML-only SPs expose no discovery at all — their SP metadata names the SP,
# never the IdP — which is why a vendor tier exists alongside the standards.
_DERIVATION_STRATEGIES = {
    "atlassian-seraph": _strategy_atlassian_seraph,
}


def derive_sso_destination(
    base_url: str, *, strategies: Sequence[str] = ()
) -> str | None:
    """Where does *base_url* send users to sign in? An **origin**, or ``None``.

    The origin is ``scheme://host:port`` with the port always explicit and an
    IPv6 host bracketed — ``https://idp.example:443``, not
    ``https://idp.example``. Compare it against a normalised form of your own
    configured destination, never against a raw string: a server is free to
    spell the default port either way, and treating the two as different
    refuses a correct destination.

    Tries, in order, and returns the first host it resolves: RFC 9728 protected
    resource metadata, OIDC discovery, then any *named* vendor strategies the
    caller opted into. ``None`` — "cannot derive" — is a real outcome, not a
    failure to handle: SAML-only SPs expose no discovery at all. A consumer that
    cannot derive must **refuse**, never fall back to the configured value.

    :param strategies: named vendor probes to append to the standards tiers.
        Default runs tiers 1–2 only.
    :raises SsoConfigError: *base_url* is not https, or a strategy name is
        unknown. Never raises for a network failure — that is ``None``.
    """
    validate_https_url(base_url, field="base_url")
    chain: list[Callable[[str, _DerivationBudget], str | None]] = [
        _tier_protected_resource_metadata,
        _tier_oidc_discovery,
    ]
    for name in strategies:
        strategy = _DERIVATION_STRATEGIES.get(name)
        if strategy is None:
            raise SsoConfigError(
                f"unknown SSO derivation strategy {name!r}; known: "
                f"{sorted(_DERIVATION_STRATEGIES)}"
            )
        chain.append(strategy)

    budget = _DerivationBudget(_DERIVE_TOTAL_BUDGET_S)
    for tier in chain:
        try:
            found = tier(base_url, budget)
        except _DerivationAbort:
            continue  # one tier refusing must not veto the next
        if found:
            return found
    return None


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
