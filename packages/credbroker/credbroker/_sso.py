"""SSO web-session cookie resolution (RFC-0035).

A second consumer-resolution family alongside the token ``creds`` family. Where
``load_credentials`` resolves a token, ``load_sso_cookies`` resolves a *captured
SSO web session* into an on-disk cookie-jar path by subprocess-invoking the
unchanged ``sso-broker.py`` engine.

Two contracts shape this module:

* **Path-not-value handoff (RFC-0013 § 1).** The resolver returns the jar's
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

import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit

__all__ = [
    "SsoError",
    "SsoBrokerNotInstalledError",
    "SsoSessionUnavailableError",
    "SsoConfigError",
    "load_sso_cookies",
    "validate_https_url",
    "validate_root_relative_endpoint",
    "domain_in_cookie_domains",
    "filter_jar_to_domains",
    "require_host_in_cookie_domains",
]

# The engine is installed by the credential-brokers pack at this user-scope path
# (RFC-0013 § 1; mirrored by ``sso-broker.py``'s own module docstring). Composed
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


def _broker_path() -> Path:
    """Resolve the engine path under the user's home (``~/.agentbundle/bin``)."""
    return Path.home().joinpath(*_BROKER_TAIL)


def load_sso_cookies(profile: str) -> Path:
    """Resolve *profile*'s captured SSO session to an on-disk cookie-jar path.

    Subprocess-invokes ``sso-broker.py get-cookies <profile>`` with the parent
    interpreter, inheriting the process environment (corporate proxy / trust-store
    passthrough, RFC-0013 § 1). Proceeds **only** on exit 0 with a readable jar
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


# --- SSO confinement primitives (RFC-0035; spec task T2) ---------------------
#
# These are the security-control surface the unchanged ``sso-broker.py`` engine
# does *not* perform and that this RFC adds *above* it: an https-only scheme guard,
# a root-relative endpoint guard, and the cookie-domain confinement that filters
# the engine's deliberately over-broad captured jar down to the declared domains.
# They are pure functions (no I/O), reusable by any platform integration, so the
# control can't drift across consumers.


def validate_https_url(value: str, *, field: str) -> None:
    """Reject *value* unless its scheme is exactly ``https`` (AC3).

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
    """Reject *value* unless it is a root-relative path (AC3).

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
    ``lstrip('.')`` while cookie ``domain`` fields keep a leading dot (AC4)."""
    return domain.lstrip(".").lower()


def domain_in_cookie_domains(domain: str, cookie_domains: Iterable[str]) -> bool:
    """Normalized label-boundary suffix match (AC4, AC6).

    Both sides are dot-stripped and lower-cased; *domain* is admitted iff it
    equals an allowed domain or is a dot-delimited subdomain of one. The label
    boundary is load-bearing: ``evil-corp.example.com`` is rejected against
    ``corp.example.com`` (no ``.`` before ``corp``), while ``jira.corp.example.com``
    is admitted. This is the single normalization primitive shared by the
    cookie-jar filter (AC4) and the send-host check (AC6).
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
    """Reduce an over-broad captured jar to cookies within *cookie_domains* (AC4).

    The engine captures every cookie observed across the SSO/IdP/analytics
    redirect chain; the consumer filters that loaded jar to the declared domains
    at load time, before attaching it. Returns a new list; the caller must never
    write the result back to the broker path (AC10). A cookie with no ``domain``
    field is dropped (fail closed).
    """
    allowed = list(cookie_domains)
    return [c for c in cookies if domain_in_cookie_domains(c.get("domain", ""), allowed)]


def require_host_in_cookie_domains(host: str, cookie_domains: Iterable[str]) -> None:
    """Fail closed unless *host* is within the declared ``cookie_domains`` (AC6).

    The consumer client's request base host must be a member of the confinement
    set before any cookie-bearing request leaves the process; a mismatch (a
    downstream edit drifting the base URL off-domain) raises.
    """
    if not domain_in_cookie_domains(host, cookie_domains):
        raise SsoConfigError(
            f"request host {host!r} is not within the declared cookie_domains "
            f"{list(cookie_domains)!r}; refusing to send the session cookie"
        )
