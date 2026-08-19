"""Jira REST API client (Cloud v3 + Server / Data Center v2).

Internal module — the skill agent dispatches to ``jira.py``; this file is
an implementation detail. The API token is resolved via the
in-process ``credbroker`` (Tier 1 env → Tier 2 OS keyring →
Tier 3 dotfile) and is never logged, echoed, or accepted on the command
line.

Auth differs by flavor:
  - Cloud  : Basic auth where username=email, password=API token. Token
             generated at id.atlassian.com → API tokens.
  - Server : Bearer Personal Access Token. Generated in user Profile →
             Personal Access Tokens.

API path prefix differs too:
  - Cloud  : /rest/api/3/...   (ADF for description / comment.body)
  - Server : /rest/api/2/...   (plain string for description / comment.body)

JQL search differs:
  - Cloud  : POST /rest/api/3/search/jql with nextPageToken pagination.
  - Server : GET  /rest/api/2/search with startAt/maxResults pagination.
"""
from __future__ import annotations

import base64
import ipaddress
import json
import logging
import os
import secrets
import shlex
import socket
import ssl
import sys
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncIterator, Callable, Iterable, Mapping
from urllib.parse import urlparse
from urllib.request import proxy_bypass

import httpx

if TYPE_CHECKING:
    from _sso_config import SsoConfig

log = logging.getLogger("jira.client")

DEFAULT_CONCURRENCY = 4
DEFAULT_TIMEOUT_S = 30.0
MAX_RETRIES = 5
PAGE_SIZE_DEFAULT = 50
PAGE_SIZE_MAX = 100  # Practical cap; Cloud /search/jql allows up to 5000 but
#  large pages are slower and easier to throttle.

FLAVOR_CLOUD = "cloud"
FLAVOR_SERVER = "server"


class JiraError(Exception):
    pass


class AuthError(JiraError):
    pass


@dataclass(frozen=True)
class IntakeRequestPolicy:
    """Profile-bound controls for a credentialed tracker request."""

    origin: str
    addresses: frozenset[ipaddress.IPv4Address | ipaddress.IPv6Address]
    timeout_s: float
    max_attempts: int
    max_bytes: int
    backoff_s: tuple[float, ...]
    resolver: Callable[..., Iterable[tuple[Any, ...]]] = dataclass_field(
        repr=False, compare=False
    )

    @classmethod
    def from_profile(
        cls,
        profile_path: Path,
        destination: str,
        *,
        resolver: Callable[..., Iterable[tuple[Any, ...]]] = socket.getaddrinfo,
    ) -> IntakeRequestPolicy:
        """Load a strict profile and validate its destination before auth."""
        try:
            profile = json.loads(
                profile_path.read_text(encoding="utf-8"),
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValueError(f"non-standard JSON constant: {value}")
                ),
            )
            if not isinstance(profile, dict) or set(profile) != {
                "id", "version", "destination", "budget"
            }:
                raise ValueError("invalid intake profile")
            destination_policy = profile["destination"]
            budget = profile["budget"]
            if not isinstance(destination_policy, dict) or not isinstance(budget, dict):
                raise ValueError("invalid intake profile")
            allowed_hosts = destination_policy["allowed_hosts"]
            if destination_policy.get("allowed_schemes") != ["https"]:
                raise ValueError("intake profile must allow https only")
            if destination_policy.get("redirect_policy") != "disabled":
                raise ValueError("intake profile must disable redirects")
            if destination_policy.get("dns_policy") != "connect-time-recheck":
                raise ValueError("intake profile must require DNS rechecks")
            if not isinstance(allowed_hosts, list) or not allowed_hosts:
                raise ValueError("intake profile requires allowed hosts")
            backoff = tuple(float(value) for value in budget["backoff_seconds"])
            max_retries = int(budget["max_retries"])
            if (
                not profile["id"]
                or not profile["version"]
                or not backoff
                or any(value < 0 for value in backoff)
                or max_retries < 0
                or float(budget["timeout_seconds"]) <= 0
                or int(budget["max_bytes"]) <= 0
            ):
                raise ValueError("intake profile has invalid budget values")
            policy = cls(
                origin="",
                addresses=frozenset(),
                timeout_s=float(budget["timeout_seconds"]),
                max_attempts=max_retries + 1,
                max_bytes=int(budget["max_bytes"]),
                backoff_s=backoff,
                resolver=resolver,
            )
            origin, addresses = policy._validate_destination(
                destination, allowed_hosts=allowed_hosts
            )
            return cls(
                origin=origin,
                addresses=addresses,
                timeout_s=policy.timeout_s,
                max_attempts=policy.max_attempts,
                max_bytes=policy.max_bytes,
                backoff_s=policy.backoff_s,
                resolver=resolver,
            )
        except (KeyError, OSError, TypeError, UnicodeError, ValueError) as exc:
            raise AuthError("invalid or unsafe tracker intake profile") from exc

    def assert_bound(self, destination: str) -> None:
        """Require the credential destination and current DNS to stay pinned."""
        origin, addresses = self._validate_destination(
            destination, allowed_hosts=[urlparse(self.origin).hostname or ""]
        )
        if origin != self.origin or addresses != self.addresses:
            raise AuthError("tracker intake destination changed after validation")

    def pinned_address(self, host: str, port: int) -> str:
        """Return one validated address for the socket connect operation."""
        expected = urlparse(self.origin)
        if host.rstrip(".").lower() != (expected.hostname or "") or port != (
            expected.port or 443
        ):
            raise AuthError("tracker intake connection escaped its validated origin")
        origin, addresses = self._validate_destination(
            self.origin, allowed_hosts=[expected.hostname or ""]
        )
        if origin != self.origin or addresses != self.addresses:
            raise AuthError("tracker intake destination changed at connect time")
        return str(sorted(addresses, key=str)[0])

    def retry_delay(self, attempt: int, retry_after: str | None) -> float:
        """Return a profile-bounded retry delay."""
        configured = self.backoff_s[min(attempt, len(self.backoff_s) - 1)]
        if retry_after and retry_after.replace(".", "", 1).isdigit():
            return min(float(retry_after), configured)
        return configured

    def _validate_destination(
        self, destination: str, *, allowed_hosts: Iterable[str]
    ) -> tuple[str, frozenset[ipaddress.IPv4Address | ipaddress.IPv6Address]]:
        parsed = urlparse(destination)
        if (
            parsed.scheme.lower() != "https"
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in ("", "/")
        ):
            raise AuthError("tracker intake destination must be an HTTPS origin")
        host = (parsed.hostname or "").rstrip(".").lower()
        allowed = {str(value).rstrip(".").lower() for value in allowed_hosts}
        if not host or host not in allowed:
            raise AuthError("tracker intake destination host is not allowlisted")
        port = parsed.port or 443
        addresses = _public_addresses(host, port, self.resolver)
        origin = f"https://{host}" + (f":{port}" if port != 443 else "")
        return origin, addresses


class _PinnedAsyncNetworkBackend:
    """httpcore backend that connects only to a profile-validated address."""

    def __init__(
        self, policy: IntakeRequestPolicy, proxy_pin: tuple[str, int, frozenset[str]] | None = None
    ) -> None:
        import httpcore  # noqa: PLC0415 — only intake needs the pinned backend

        self._policy = policy
        self._proxy_pin = proxy_pin
        self._backend = httpcore.AnyIOBackend()

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[tuple[int, int, int | bytes]] | None = None,
    ) -> Any:
        if self._proxy_pin is None:
            address = self._policy.pinned_address(host, port)
        else:
            proxy_host, proxy_port, expected_addresses = self._proxy_pin
            if host.rstrip(".").lower() != proxy_host or port != proxy_port:
                raise AuthError("tracker intake connection escaped its configured proxy")
            addresses = _resolved_addresses(host, port, self._policy.resolver)
            if addresses != expected_addresses:
                raise AuthError("tracker intake proxy changed at connect time")
            address = sorted(addresses)[0]
        return await self._backend.connect_tcp(
            address, port, timeout, local_address, socket_options
        )

    async def connect_unix_socket(
        self,
        path: str,
        timeout: float | None = None,
        socket_options: Iterable[tuple[int, int, int | bytes]] | None = None,
    ) -> Any:
        return await self._backend.connect_unix_socket(path, timeout, socket_options)

    async def sleep(self, seconds: float) -> None:
        await self._backend.sleep(seconds)


def _pinned_transport(
    policy: IntakeRequestPolicy, *, verify: ssl.SSLContext
) -> httpx.AsyncHTTPTransport:
    """Build a proxy-aware transport whose actual socket is DNS-pinned."""
    proxy_url, proxy_pin = _https_proxy_settings(policy)
    transport = httpx.AsyncHTTPTransport(
        verify=verify, retries=0, proxy=proxy_url, trust_env=True
    )
    transport._pool._network_backend = _PinnedAsyncNetworkBackend(  # noqa: SLF001
        policy, proxy_pin
    )
    return transport


def _https_proxy_settings(
    policy: IntakeRequestPolicy,
) -> tuple[str | None, tuple[str, int, frozenset[str]] | None]:
    """Honor HTTPS_PROXY/NO_PROXY and pin the configured proxy socket."""
    destination_host = urlparse(policy.origin).hostname or ""
    if proxy_bypass(destination_host):
        return None, None
    proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if not proxy_url:
        return None, None
    parsed = urlparse(proxy_url)
    default_ports = {"http": 80, "https": 443, "socks5": 1080, "socks5h": 1080}
    if (
        parsed.scheme.lower() not in default_ports
        or not parsed.hostname
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise AuthError("HTTPS_PROXY is not a supported proxy origin")
    port = parsed.port or default_ports[parsed.scheme.lower()]
    host = parsed.hostname.rstrip(".").lower()
    addresses = _resolved_addresses(host, port, policy.resolver)
    return proxy_url, (host, port, addresses)


def _resolved_addresses(
    host: str,
    port: int,
    resolver: Callable[..., Iterable[tuple[Any, ...]]],
) -> frozenset[str]:
    """Resolve one trusted proxy host to a stable non-empty address set."""
    try:
        addresses = frozenset(
            str(ipaddress.ip_address(item[4][0])) for item in resolver(host, port)
        )
    except (IndexError, OSError, TypeError, ValueError) as exc:
        raise AuthError("tracker intake proxy resolution failed") from exc
    if not addresses:
        raise AuthError("tracker intake proxy resolution returned no addresses")
    return addresses


def _render_windows_command(argv: list[str], fallback: str) -> str:
    """Render only cmd/PowerShell-inert Windows argv; refuse everything else."""
    safe_punctuation = frozenset(" _./:\\-")
    if any(
        not value
        or any(
            not char.isascii()
            or (not char.isalnum() and char not in safe_punctuation)
            for char in value
        )
        for value in argv
    ):
        return f"{fallback} (use an argv-capable terminal)"
    return " ".join(f'"{value}"' if " " in value else value for value in argv)


def operator_command(entry_name: str, *args: str) -> str:
    """Render a bounded command for a verified entry in this scripts directory."""
    fallback = f"the installed {entry_name} entry point"
    try:
        scripts_dir = Path(__file__).resolve(strict=True).parent
        entry = (scripts_dir / entry_name).resolve(strict=True)
        entry.relative_to(scripts_dir)
        if not entry.is_file():
            return fallback
    except (OSError, RuntimeError, ValueError):
        return fallback

    argv = [sys.executable, str(entry), *args]
    if sys.platform == "win32":
        return _render_windows_command(argv, fallback)
    return shlex.join(argv)


# The one place this command is spelled. `jira.py` imports it rather than
# repeating the literal — renaming the flag should be one edit, not three.
REGISTER_COMMAND = operator_command("jira.py", "check", "--register")


class SsoSessionUnavailable(AuthError):
    """No usable SSO session — and re-authenticating could fix it.

    The typed signal `check`'s auto-recovery keys on. Raised at exactly five
    sites and nowhere else: the two construction-time jar failures, a `401` or
    an unfollowed `3xx`, and the two shapes of "a `2xx` that is not an identity"
    an SSO reverse proxy answers an expired session with. The last three are
    scoped to the cookie path.

    Deliberately **not** raised for a `403`, a failed confinement check, a
    missing engine, or a broker timeout: re-authenticating cannot fix any of
    them, and opening a browser for them would be worse than failing.

    Subclasses :class:`AuthError`, so every existing handler and exit code is
    unchanged.
    """


# The identity fields a Jira `myself` response may carry, in preference order.
# Single-sourced: the raise site below and `jira.py`'s `_cmd_check` display
# fallback must agree exactly. Listing a field the raise site accepts but the
# display does not still prints `as ?` at exit 0 — the failure the guard exists
# to stop — and omitting one the display uses would reject a valid response and
# open a browser for nothing.
_IDENTITY_FIELDS = ("displayName", "name", "emailAddress", "key", "accountId")


def identity_of(info: object) -> str | None:
    """The first non-empty ``str`` identity field in *info*, or ``None``.

    Presence is not the test. ``{"displayName": null}`` and ``{"name": ""}``
    both satisfy a presence check while leaving nothing to display, which is
    exactly the shape an expired-session proxy response takes.
    """
    if not isinstance(info, Mapping):
        return None
    for field in _IDENTITY_FIELDS:
        value = info.get(field)
        if isinstance(value, str) and value:
            return value
    return None


@dataclass(frozen=True)
class Credentials:
    base_url: str
    token: str
    flavor: str          # "cloud" or "server"
    email: str | None    # required for cloud (Basic auth username), unused on server


def detect_flavor(base_url: str) -> str:
    host = (urlparse(base_url).hostname or "").lower()
    if (
        host.endswith((".atlassian.net", ".jira.com", ".jira-dev.com"))
    ):
        return FLAVOR_CLOUD
    return FLAVOR_SERVER


def _public_addresses(
    host: str,
    port: int,
    resolver: Callable[..., Iterable[tuple[Any, ...]]],
) -> frozenset[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Resolve one stable, non-empty set of globally routable addresses."""
    snapshots = []
    for _ in range(2):
        addresses = set()
        for item in resolver(host, port, type=socket.SOCK_STREAM):
            try:
                addresses.add(ipaddress.ip_address(item[4][0]))
            except (IndexError, TypeError, ValueError) as exc:
                raise AuthError("tracker destination DNS answer was invalid") from exc
        snapshots.append(frozenset(addresses))
    if not snapshots[0] or snapshots[0] != snapshots[1]:
        raise AuthError("tracker destination DNS identity was unstable")
    if any(not address.is_global for address in snapshots[0]):
        raise AuthError("tracker destination resolved to a non-public address")
    return snapshots[0]


def _api_prefix(flavor: str) -> str:
    return "/rest/api/3" if flavor == FLAVOR_CLOUD else "/rest/api/2"


def _validate_jar_shape(raw: object) -> None:
    """Raise ``ValueError`` unless *raw* is a well-formed cookie jar.

    A list-of-dicts check is not sufficient. ``filter_jar_to_domains`` calls
    ``.lstrip()`` on ``domain`` and indexes ``c["name"]``, and the loader below
    passes ``c.get("path") or "/"`` straight to ``httpx.Cookies.set`` — so a
    non-``str`` ``domain``, a missing ``name``, or an ``int`` ``path`` raises
    ``AttributeError`` / ``KeyError`` / ``TypeError`` deep in the call and
    escapes as exit 1, which is the band the guard exists to close. Each record
    is validated field by field instead.
    """
    if not isinstance(raw, list):
        raise ValueError("cookie jar must be a list of cookie records")
    for record in raw:
        if not isinstance(record, dict):
            raise ValueError("cookie jar entry is not an object")
        for field in ("name", "domain", "value"):
            if not isinstance(record.get(field), str):
                raise ValueError(f"cookie record field {field!r} must be a string")
        path = record.get("path")
        if path is not None and not isinstance(path, str):
            raise ValueError("cookie record field 'path' must be a string when set")


def _sso_cafile_capath() -> tuple[str | None, str | None]:
    """Resolve the CA bundle file + dir for the cookie-path SSL context.

    httpx (``trust_env``) natively honors ``SSL_CERT_FILE`` / ``SSL_CERT_DIR`` but
    does **not** read ``REQUESTS_CA_BUNDLE``; we map it here. Precedence:
    ``SSL_CERT_FILE`` wins over ``REQUESTS_CA_BUNDLE`` when both are set (the
    native httpx env takes precedence over the requests-compat var).
    """
    cafile = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    capath = os.environ.get("SSL_CERT_DIR")
    return (cafile or None, capath or None)


def _sso_ssl_context() -> ssl.SSLContext:
    """SSL context for the cookie path: the system trust store *plus* any
    ``SSL_CERT_FILE`` / ``SSL_CERT_DIR`` / ``REQUESTS_CA_BUNDLE`` the corporate
    environment sets — loaded on top of (never clobbering) the default store, so a
    bare ``verify=True`` can't drop the corporate CA."""
    ctx = ssl.create_default_context()
    cafile, capath = _sso_cafile_capath()
    if cafile or capath:
        ctx.load_verify_locations(cafile=cafile, capath=capath)
    return ctx


class JiraClient:
    """Async wrapper around the Jira REST API.

    Provides issue, project, user, search, and raw operations. Cloud vs
    Server differences (auth header, API version, JQL pagination, ADF
    body wrapping) are handled internally so callers can stay flavor-
    agnostic.
    """

    def __init__(
        self,
        credentials: Credentials,
        *,
        concurrency: int = DEFAULT_CONCURRENCY,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        verify_tls: bool = True,
        intake_policy: IntakeRequestPolicy | None = None,
    ) -> None:
        base_url = credentials.base_url
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")

        self._base = base_url.rstrip("/")
        self._intake_policy = intake_policy
        if intake_policy is not None:
            if not verify_tls:
                raise AuthError("tracker intake cannot disable TLS verification")
            intake_policy.assert_bound(self._base)
            timeout_s = intake_policy.timeout_s
        self._flavor = credentials.flavor
        self._api = _api_prefix(self._flavor)
        # Token path. The SSO-cookie path is built via from_sso_cookies and sets
        # these to "sso-cookie" / the profile name; _request branches on them.
        self._auth_mode = "creds"
        self._profile: str | None = None

        if self._flavor == FLAVOR_CLOUD:
            if not credentials.email:
                raise AuthError(
                    "Cloud auth requires an email — run "
                    "`credential-setup` skill and supply JIRA_EMAIL."
                )
            basic = base64.b64encode(
                f"{credentials.email}:{credentials.token}".encode()
            ).decode("ascii")
            auth_header = f"Basic {basic}"
        else:
            auth_header = f"Bearer {credentials.token}"

        headers = {
            "Accept": "application/json",
            "User-Agent": "atlassian-jira/0.1",
            "Authorization": auth_header,
        }
        transport = (
            _pinned_transport(intake_policy, verify=_sso_ssl_context())
            if intake_policy is not None
            else None
        )
        self._client = httpx.AsyncClient(
            base_url=self._base,
            headers=headers,
            timeout=timeout_s,
            verify=verify_tls,
            follow_redirects=intake_policy is None,
            transport=transport,
            trust_env=True,
        )
        # Concurrency is gated by the semaphore alone. Throttling for
        # rate-limited endpoints comes from the API's own 429 + Retry-After
        # response, which the request loop honors.
        import asyncio  # lazy: avoids asyncio IOCP probe on Windows before --help runs
        self._sem = asyncio.Semaphore(concurrency)

    @classmethod
    def from_sso_cookies(
        cls,
        sso_config: SsoConfig,
        *,
        concurrency: int = DEFAULT_CONCURRENCY,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        intake_policy: IntakeRequestPolicy | None = None,
    ) -> JiraClient:
        """Build a Data Center client authenticated by a captured SSO cookie jar.

        Resolves the jar via credbroker (fail-closed, never downgrades to a
        token), filters it to the declared ``cookie_domains``, confirms the
        base host is within those domains, and builds an httpx client with
        the confined jar attached, **no** ``Authorization`` header,
        ``follow_redirects=False`` so the session cookie is never re-attached
        across a redirect, and the corporate proxy / trust store honored.
        The cookie path is GET/HEAD only, enforced in ``_request``.
        """
        import credbroker

        base_url = sso_config.base_url
        if intake_policy is not None:
            intake_policy.assert_bound(base_url.rstrip("/"))
            timeout_s = intake_policy.timeout_s
        parsed = urlparse(base_url)
        # Defense-in-depth https guard at construction: the cookie jar is a
        # bearer secret, so the token path's http:// tolerance must not extend
        # here, even though the config layer already rejects a non-https URL.
        if parsed.scheme != "https":
            raise AuthError(
                "SSO-cookie base_url must be https (the session cookie is a bearer secret)"
            )
        host = parsed.hostname or ""
        # Send-host confinement + fail-closed jar resolution. Every credbroker
        # fail-closed path re-raises as AuthError so the skill surfaces them as a
        # single user-action (the remediation text is preserved) — but only the
        # *session-unavailable* one carries the typed subclass, because that is
        # the only one a recapture could fix. A confinement failure, a missing
        # engine, or a broker timeout stays a plain AuthError: opening a browser
        # for any of them would be worse than failing.
        try:
            credbroker.require_host_in_cookie_domains(host, sso_config.cookie_domains)
            jar_path = credbroker.load_sso_cookies(sso_config.profile)
        except credbroker.SsoSessionUnavailableError as exc:
            raise SsoSessionUnavailable(str(exc)) from exc
        except credbroker.SsoError as exc:
            raise AuthError(str(exc)) from exc

        # Read, parse and **shape-check** the jar inside the guarded block. The
        # message is fixed remediation text naming only the profile, with the
        # cause chained rather than interpolated: a UnicodeDecodeError's own text
        # quotes the offending bytes of a cookie jar.
        try:
            raw_cookies = json.loads(jar_path.read_text(encoding="utf-8"))
            _validate_jar_shape(raw_cookies)
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            raise SsoSessionUnavailable(
                f"the stored SSO cookie jar for profile {sso_config.profile} is "
                f"unreadable or malformed; re-capture the session"
            ) from exc

        # Confine the deliberately over-broad captured jar to the declared domains
        # before attaching it; the result is never written back.
        confined = credbroker.filter_jar_to_domains(
            raw_cookies, sso_config.cookie_domains
        )

        self = cls.__new__(cls)
        self._base = base_url.rstrip("/")
        self._flavor = FLAVOR_SERVER  # DC only — Cloud cookie auth is out of scope
        self._api = _api_prefix(self._flavor)
        self._auth_mode = "sso-cookie"
        self._profile = sso_config.profile
        self._intake_policy = intake_policy

        cookies = httpx.Cookies()
        for c in confined:
            # Preserve the jar's domain verbatim (keep any leading dot): httpx's
            # cookiejar uses domain_initial_dot for subdomain matching, so a
            # ".corp.example.com" domain cookie must keep its dot to attach to
            # jira.corp.example.com. Stripping it would break attachment.
            cookies.set(
                c["name"],
                c.get("value", ""),
                domain=c.get("domain", ""),
                path=c.get("path") or "/",
            )

        headers = {
            "Accept": "application/json",
            "User-Agent": "atlassian-jira/0.1",
        }  # deliberately NO Authorization header on the cookie path
        transport = (
            _pinned_transport(intake_policy, verify=_sso_ssl_context())
            if intake_policy is not None
            else None
        )
        self._client = httpx.AsyncClient(
            base_url=self._base,
            headers=headers,
            cookies=cookies,
            timeout=timeout_s,
            verify=_sso_ssl_context(),
            trust_env=True,  # corporate proxy + SSL_CERT_FILE/SSL_CERT_DIR
            follow_redirects=False,  # never re-attach the cookie cross-host
            transport=transport,
        )
        import asyncio  # lazy: avoids asyncio IOCP probe on Windows before --help runs
        self._sem = asyncio.Semaphore(concurrency)
        return self

    async def __aenter__(self) -> JiraClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._client.aclose()

    @property
    def flavor(self) -> str:
        return self._flavor

    @property
    def base_url(self) -> str:
        return self._base

    @property
    def api_prefix(self) -> str:
        return self._api

    # --- low-level request -------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any | None = None,
        files: Mapping[str, Any] | None = None,
        extra_headers: Mapping[str, str] | None = None,
        idempotent: bool | None = None,
        guarded_write: bool = False,
    ) -> httpx.Response:
        if files is not None and json_body is not None:
            # Caller bug: httpx would silently drop the JSON body in favor
            # of the multipart form, masking the mistake. Fail loudly.
            raise ValueError("cannot send json_body and files in the same request")

        # Cookie-path write refusal. This chokepoint is the single point
        # every call funnels through — including the raw() escape hatch — so a
        # GET/HEAD allowlist here covers future verbs by construction. Raised
        # before any request reaches the wire (the transport records zero
        # requests for a refused verb).
        if self._auth_mode == "sso-cookie" and method.upper() not in ("GET", "HEAD"):
            raise JiraError(
                "writes over SSO-cookie auth are not supported yet; "
                "use a personal access token, or wait for the XSRF follow-on"
            )
        # Cloud JQL is a documented read endpoint that uses POST.  Only our
        # call sites may set ``idempotent=True``; other POSTs remain refused.
        is_idempotent = (
            method.upper() in ("GET", "HEAD") if idempotent is None else idempotent
        )
        if (
            self._intake_policy is not None
            and not is_idempotent
            and not guarded_write
        ):
            raise JiraError("tracker intake is read-only; request refused")

        async with self._sem:
            last_exc: Exception | None = None
            last_status: int | None = None
            attempts = 1 if guarded_write else (
                self._intake_policy.max_attempts
                if self._intake_policy is not None
                else MAX_RETRIES
            )
            for attempt in range(attempts):
                try:
                    if self._intake_policy is not None:
                        self._intake_policy.assert_bound(self._base)
                        resp = await self._bounded_request(
                            method,
                            path,
                            params=params,
                            json_body=json_body if files is None else None,
                            files=files,
                            extra_headers=extra_headers,
                        )
                    else:
                        resp = await self._client.request(
                            method,
                            path,
                            params=params,
                            json=json_body if files is None else None,
                            files=files,
                            headers=dict(extra_headers) if extra_headers else None,
                        )
                except httpx.TransportError as exc:
                    last_exc = exc
                    import asyncio  # noqa: PLC0415 — lazy, cached after __init__
                    delay = (
                        self._intake_policy.retry_delay(attempt, None)
                        if self._intake_policy is not None
                        else self._backoff(attempt)
                    )
                    await asyncio.sleep(delay)
                    continue

                if self._intake_policy is not None and 300 <= resp.status_code < 400:
                    raise JiraError("tracker intake redirect was refused")

                if resp.status_code == 401:
                    if self._auth_mode == "sso-cookie":
                        # Stop using the known-stale jar — no further
                        # cookie-bearing request with this session. The
                        # remediation names the profile, never the cookie bytes.
                        self._client.cookies.clear()
                        raise SsoSessionUnavailable(
                            f"401 Unauthorized — SSO session expired for profile "
                            f"{self._profile}; run "
                            f"{REGISTER_COMMAND!r} to re-authenticate"
                        )
                    raise AuthError(
                        "401 Unauthorized — Jira credentials are missing, "
                        "invalid, or expired. Re-run "
                        "`credential-setup` skill."
                    )
                if self._auth_mode == "sso-cookie" and 300 <= resp.status_code < 400:
                    # follow_redirects is disabled on the cookie path, so a
                    # 30x is surfaced, never followed (which would re-attach the
                    # session cookie to the redirect target). A redirect to login
                    # is the DC expired-session signal.
                    raise SsoSessionUnavailable(
                        f"SSO session may have expired for profile {self._profile} "
                        f"(HTTP {resp.status_code} redirect, not followed); run "
                        f"{REGISTER_COMMAND!r} to re-authenticate"
                    )
                if resp.status_code == 403:
                    # On Cloud, 403 with X-Seraph-LoginReason often means
                    # CAPTCHA; surface that hint when present.
                    seraph = resp.headers.get("X-Seraph-LoginReason", "")
                    hint = f" (X-Seraph-LoginReason: {seraph})" if seraph else ""
                    raise AuthError(
                        f"403 Forbidden for {path} — token lacks permission "
                        f"or anonymous access is blocked{hint}."
                    )
                if resp.status_code == 429 or 500 <= resp.status_code < 600:
                    last_status = resp.status_code
                    retry_after = resp.headers.get("Retry-After")
                    delay = (
                        self._intake_policy.retry_delay(attempt, retry_after)
                        if self._intake_policy is not None
                        else (
                            float(retry_after)
                            if retry_after
                            and retry_after.replace(".", "", 1).isdigit()
                            else self._backoff(attempt)
                        )
                    )
                    log.warning(
                        "HTTP %s on %s — retrying in %.1fs",
                        resp.status_code, path, delay,
                    )
                    import asyncio  # noqa: PLC0415 — lazy, cached after __init__
                    await asyncio.sleep(delay)
                    continue
                if resp.status_code >= 400:
                    raise JiraError(
                        f"HTTP {resp.status_code} on {path}: {resp.text[:300]}"
                    )
                return resp

            tail = []
            if last_status is not None:
                tail.append(f"last status: {last_status}")
            if last_exc is not None:
                tail.append(f"last error: {last_exc}")
            suffix = f" ({'; '.join(tail)})" if tail else ""
            raise JiraError(
                f"Exhausted {attempts} attempts for {path}{suffix}"
            )

    async def _bounded_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None,
        json_body: Any | None,
        files: Mapping[str, Any] | None,
        extra_headers: Mapping[str, str] | None,
    ) -> httpx.Response:
        """Stream one intake response and stop before its byte cap is crossed."""
        assert self._intake_policy is not None
        request = self._client.build_request(
            method,
            path,
            params=params,
            json=json_body,
            files=files,
            headers=dict(extra_headers) if extra_headers else None,
        )
        response = await self._client.send(request, stream=True)
        content = bytearray()
        try:
            async for chunk in response.aiter_bytes():
                if len(content) + len(chunk) > self._intake_policy.max_bytes:
                    raise JiraError("tracker intake response exceeded its byte budget")
                content.extend(chunk)
        finally:
            await response.aclose()
        return httpx.Response(
            response.status_code,
            headers=response.headers,
            content=bytes(content),
            request=request,
            extensions=response.extensions,
        )

    @staticmethod
    def _backoff(attempt: int) -> float:
        # SystemRandom for the jitter so security scanners don't flag the
        # PRNG; value is not security-sensitive.
        return min(30.0, (2 ** attempt) * 0.5 + secrets.SystemRandom().uniform(0, 0.5))

    # --- identity / health -------------------------------------------------

    def _json(self, resp):
        """Decode a 2xx body, treating a non-JSON one as an expired SSO session.

        On the **cookie path** a 2xx is not on its own evidence of a live
        session: an SSO reverse proxy commonly answers an expired one with
        ``200`` plus the IdP login page. `whoami` guarded that; every other read
        method called ``resp.json()`` directly, so the same login page reached
        them as a ``ValueError`` and surfaced as a generic exit 1 — "invalid
        JSON" where the true cause is "your session expired", which sends the
        operator debugging the wrong thing.

        On the token path the guard does not apply: a non-JSON 2xx there is a
        genuine server or proxy fault, not an expired session, and reporting it
        as one would be its own wrong answer. The original exception propagates.
        """
        try:
            return resp.json()
        except ValueError as exc:  # incl. json.JSONDecodeError
            if self._auth_mode == "sso-cookie":
                raise SsoSessionUnavailable(
                    f"the SSO session for profile {self._profile} returned a "
                    f"non-JSON body (an IdP login page is the usual cause); "
                    f"the session has expired"
                ) from exc
            raise

    async def whoami(self) -> dict:
        """Return the authenticated user record.

        Cloud: GET /rest/api/3/myself.
        Server: GET /rest/api/2/myself (same path under the v2 prefix).

        On the **cookie path** a ``2xx`` is not on its own evidence of a live
        session: an SSO reverse proxy commonly answers an expired one with
        ``200`` plus the IdP login page, or with a parseable body carrying no
        identity. Both are :class:`SsoSessionUnavailable` — the second
        especially, because without the guard it reports an expired session as
        exit 0, which is worse than a missed recovery.
        """
        resp = await self._request("GET", f"{self._api}/myself")
        # The non-JSON half of this guard now lives in `_json`, which every read
        # path shares. What stays here is the half that is genuinely specific to
        # `whoami`: a *parseable* body carrying no identity. Only this endpoint
        # promises an identity, so only here can its absence be diagnosed.
        data = self._json(resp)
        if self._auth_mode == "sso-cookie":
            if identity_of(data) is None:
                raise SsoSessionUnavailable(
                    f"the SSO session for profile {self._profile} returned no "
                    f"identity; the session has expired"
                )
            return data
        return data if isinstance(data, dict) else {"value": data}

    async def server_info(self) -> dict:
        resp = await self._request("GET", f"{self._api}/serverInfo")
        return self._json(resp)

    # --- issue operations --------------------------------------------------

    async def get_issue(
        self,
        issue_key: str,
        *,
        fields: str | None = None,
        expand: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {}
        if fields:
            params["fields"] = fields
        if expand:
            params["expand"] = expand
        resp = await self._request(
            "GET", f"{self._api}/issue/{issue_key}", params=params or None
        )
        return self._json(resp)

    async def create_issue(self, body: Mapping[str, Any]) -> dict:
        """POST /issue with a body that already has the `{"fields": {...}}`
        shape, or a flat fields dict (we'll wrap it)."""
        payload = _wrap_fields(body)
        # On Cloud v3, description / comment.body must be ADF if present
        # as a plain string. Wrap conservatively.
        if self._flavor == FLAVOR_CLOUD:
            payload = _adf_wrap_fields(payload)
        resp = await self._request("POST", f"{self._api}/issue", json_body=payload)
        if not resp.content:
            return {}
        return self._json(resp)

    async def update_issue(
        self, issue_key: str, body: Mapping[str, Any], *, notify_users: bool = True
    ) -> None:
        """PUT /issue/{key}. Returns 204 on success."""
        payload = _wrap_fields(body)
        if self._flavor == FLAVOR_CLOUD:
            payload = _adf_wrap_fields(payload)
        params = {} if notify_users else {"notifyUsers": "false"}
        await self._request(
            "PUT",
            f"{self._api}/issue/{issue_key}",
            params=params or None,
            json_body=payload,
        )

    async def delete_issue(
        self, issue_key: str, *, delete_subtasks: bool = False
    ) -> None:
        params = {"deleteSubtasks": "true"} if delete_subtasks else None
        await self._request(
            "DELETE", f"{self._api}/issue/{issue_key}", params=params
        )

    async def list_transitions(self, issue_key: str) -> list[dict]:
        resp = await self._request(
            "GET", f"{self._api}/issue/{issue_key}/transitions"
        )
        data = self._json(resp)
        return data.get("transitions", []) if isinstance(data, dict) else []

    async def transition_issue(
        self,
        issue_key: str,
        *,
        transition_id: str | None = None,
        transition_name: str | None = None,
        fields: Mapping[str, Any] | None = None,
        guarded_write: bool = False,
    ) -> None:
        if not transition_id and not transition_name:
            raise ValueError("transition_id or transition_name is required")
        if not transition_id:
            transitions = await self.list_transitions(issue_key)
            match = next(
                (
                    t for t in transitions
                    if (t.get("name") or "").lower() == transition_name.lower()
                ),
                None,
            )
            if not match:
                names = ", ".join(t.get("name", "?") for t in transitions) or "(none)"
                raise JiraError(
                    f"no transition named {transition_name!r} on {issue_key} "
                    f"— available: {names}"
                )
            transition_id = str(match["id"])
        payload: dict[str, Any] = {"transition": {"id": transition_id}}
        if fields:
            payload["fields"] = dict(fields)
        await self._request(
            "POST",
            f"{self._api}/issue/{issue_key}/transitions",
            json_body=payload,
            guarded_write=guarded_write,
        )

    async def add_comment(
        self, issue_key: str, body_text: str, *, guarded_write: bool = False
    ) -> dict:
        if self._flavor == FLAVOR_CLOUD:
            payload = {"body": _adf_paragraph(body_text)}
        else:
            payload = {"body": body_text}
        resp = await self._request(
            "POST",
            f"{self._api}/issue/{issue_key}/comment",
            json_body=payload,
            guarded_write=guarded_write,
        )
        return self._json(resp) if resp.content else {}

    async def add_attachment(self, issue_key: str, file_path: Path) -> list[dict]:
        """POST /issue/{key}/attachments. Requires the
        ``X-Atlassian-Token: no-check`` header to bypass XSRF check, and
        the multipart field name MUST be ``file``."""
        if not file_path.is_file():
            raise FileNotFoundError(file_path)
        with file_path.open("rb") as fh:
            files = {"file": (file_path.name, fh.read(), "application/octet-stream")}
        resp = await self._request(
            "POST",
            f"{self._api}/issue/{issue_key}/attachments",
            files=files,
            extra_headers={"X-Atlassian-Token": "no-check"},
        )
        if not resp.content:
            return []
        data = self._json(resp)
        return data if isinstance(data, list) else [data]

    # --- JQL search --------------------------------------------------------

    async def iter_search(
        self,
        jql: str,
        *,
        fields: str | None = None,
        expand: str | None = None,
        page_size: int = PAGE_SIZE_DEFAULT,
        limit: int | None = None,
    ) -> AsyncIterator[dict]:
        """Paginate JQL results.

        Cloud: POST /rest/api/3/search/jql with nextPageToken pagination
        (no `total`; loop until `isLast` or token absent).
        Server: GET /rest/api/2/search with startAt + maxResults.
        """
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        page_size = min(page_size, PAGE_SIZE_MAX)
        yielded = 0
        field_list: list[str] | None = (
            [f.strip() for f in fields.split(",") if f.strip()] if fields else None
        )

        if self._flavor == FLAVOR_CLOUD:
            next_token: str | None = None
            while True:
                remaining = None if limit is None else max(0, limit - yielded)
                if remaining == 0:
                    return
                top = page_size if remaining is None else min(page_size, remaining)
                body: dict[str, Any] = {"jql": jql, "maxResults": top}
                if field_list is not None:
                    body["fields"] = field_list
                if expand:
                    # Cloud /search/jql takes `expand` as a comma-separated
                    # string in the body, NOT an array (that's `fields`).
                    body["expand"] = expand
                if next_token:
                    body["nextPageToken"] = next_token

                resp = await self._request(
                    "POST", f"{self._api}/search/jql", json_body=body, idempotent=True
                )
                data = self._json(resp)
                issues = data.get("issues", []) if isinstance(data, dict) else []
                if not issues:
                    return
                for issue in issues:
                    yield issue
                    yielded += 1
                    if limit is not None and yielded >= limit:
                        return
                if data.get("isLast") or not data.get("nextPageToken"):
                    return
                next_token = data["nextPageToken"]
        else:
            start_at = 0
            while True:
                remaining = None if limit is None else max(0, limit - yielded)
                if remaining == 0:
                    return
                top = page_size if remaining is None else min(page_size, remaining)
                params: dict[str, Any] = {
                    "jql": jql,
                    "startAt": start_at,
                    "maxResults": top,
                }
                if fields:
                    params["fields"] = fields
                if expand:
                    params["expand"] = expand

                resp = await self._request(
                    "GET", f"{self._api}/search", params=params
                )
                data = self._json(resp)
                issues = data.get("issues", []) if isinstance(data, dict) else []
                if not issues:
                    return
                for issue in issues:
                    yield issue
                    yielded += 1
                    if limit is not None and yielded >= limit:
                        return
                if len(issues) < top:
                    return
                start_at += len(issues)

    # --- projects ----------------------------------------------------------

    async def get_project(self, key_or_id: str) -> dict:
        resp = await self._request("GET", f"{self._api}/project/{key_or_id}")
        return self._json(resp)

    async def iter_projects(
        self,
        *,
        query: str | None = None,
        page_size: int = PAGE_SIZE_DEFAULT,
        limit: int | None = None,
    ) -> AsyncIterator[dict]:
        page_size = min(page_size, PAGE_SIZE_MAX)
        start_at = 0
        yielded = 0
        while True:
            remaining = None if limit is None else max(0, limit - yielded)
            if remaining == 0:
                return
            top = page_size if remaining is None else min(page_size, remaining)
            params: dict[str, Any] = {"startAt": start_at, "maxResults": top}
            if query:
                params["query"] = query
            resp = await self._request(
                "GET", f"{self._api}/project/search", params=params
            )
            data = self._json(resp)
            values = data.get("values", []) if isinstance(data, dict) else []
            if not values:
                return
            for proj in values:
                yield proj
                yielded += 1
                if limit is not None and yielded >= limit:
                    return
            if data.get("isLast") or len(values) < top:
                return
            start_at += len(values)

    # --- users -------------------------------------------------------------

    async def get_user(
        self,
        *,
        account_id: str | None = None,
        username: str | None = None,
        key: str | None = None,
    ) -> dict:
        """Cloud: lookup by accountId. Server: lookup by username (or key).
        Pass exactly one identifier appropriate for your flavor."""
        params: dict[str, Any] = {}
        if account_id:
            params["accountId"] = account_id
        if username:
            params["username"] = username
        if key:
            params["key"] = key
        if not params:
            raise ValueError("account_id (cloud) or username/key (server) is required")
        resp = await self._request("GET", f"{self._api}/user", params=params)
        return self._json(resp)

    async def iter_users(
        self,
        query: str,
        *,
        page_size: int = PAGE_SIZE_DEFAULT,
        limit: int | None = None,
    ) -> AsyncIterator[dict]:
        page_size = min(page_size, PAGE_SIZE_MAX)
        start_at = 0
        yielded = 0
        while True:
            remaining = None if limit is None else max(0, limit - yielded)
            if remaining == 0:
                return
            top = page_size if remaining is None else min(page_size, remaining)
            if self._flavor == FLAVOR_CLOUD:
                params: dict[str, Any] = {
                    "query": query, "startAt": start_at, "maxResults": top,
                }
                path = f"{self._api}/users/search"
            else:
                params = {
                    "username": query, "startAt": start_at, "maxResults": top,
                }
                path = f"{self._api}/user/search"
            resp = await self._request("GET", path, params=params)
            data = self._json(resp)
            users = data if isinstance(data, list) else data.get("values", [])
            if not users:
                return
            for u in users:
                yield u
                yielded += 1
                if limit is not None and yielded >= limit:
                    return
            if len(users) < top:
                return
            start_at += len(users)

    # --- raw escape hatch --------------------------------------------------

    async def raw(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any | None = None,
    ) -> Any:
        """Arbitrary request. ``path`` may be absolute (``/rest/api/3/foo``)
        or relative to the API prefix (``foo`` → ``/rest/api/<v>/foo``)."""
        if not path.startswith("/"):
            path = f"{self._api}/{path}"
        resp = await self._request(method, path, params=params, json_body=json_body)
        if not resp.content:
            return None
        ctype = resp.headers.get("content-type", "")
        if "json" in ctype:
            return self._json(resp)
        return resp.text


# --- helpers ---------------------------------------------------------------


def _wrap_fields(body: Mapping[str, Any]) -> dict[str, Any]:
    """Allow callers to pass either {"fields": {...}} or a flat dict."""
    if "fields" in body or "update" in body or "transition" in body:
        return dict(body)
    return {"fields": dict(body)}


def _adf_paragraph(text: str) -> dict[str, Any]:
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }


def _adf_wrap_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    """If the caller passed a plain string for ``description`` or
    ``environment`` on Cloud v3, wrap it as ADF. Leave already-shaped ADF
    documents (dicts with ``type`` == ``doc``) untouched."""
    out = dict(payload)
    fields = dict(out.get("fields") or {})
    for key in ("description", "environment"):
        val = fields.get(key)
        if isinstance(val, str):
            fields[key] = _adf_paragraph(val)
    if fields:
        out["fields"] = fields
    return out


def load_base_url() -> str:
    """Resolve only the configured Jira origin, without loading a token."""
    from credbroker import CredentialsMissingError
    from credbroker import load_credentials as _resolver_load

    try:
        creds = _resolver_load("jira", required_keys=["BASE_URL"])
    except CredentialsMissingError as exc:
        raise AuthError(str(exc)) from exc
    return creds.BASE_URL.rstrip("/")


def load_credentials() -> Credentials:
    """Resolve Jira credentials through the in-process ``credbroker``
    loader (Tier 1 env → Tier 2 OS keyring → Tier 3 dotfile).

    Namespace: ``jira``. Required keys: ``BASE_URL`` and ``API_TOKEN``.
    Optional keys (best-effort, separate load): ``EMAIL`` (Cloud Basic
    auth username) and ``FLAVOR`` (``cloud`` or ``server``;
    auto-detected from URL host when absent).

    Env-var shape: ``<NAMESPACE>_<KEY>`` — ``JIRA_BASE_URL``,
    ``JIRA_API_TOKEN``, ``JIRA_EMAIL``, ``JIRA_FLAVOR``.

    Token bytes never traverse this function's return path other than
    through the ``Credentials`` dataclass into ``JiraClient.__init__``.
    Schema lives at ``references/creds-schema.toml`` — the
    ``credential-setup`` skill flow walks it interactively.
    """
    from credbroker import (
        CredentialsMissingError,
    )
    from credbroker import (
        load_credentials as _resolver_load,
    )

    try:
        creds = _resolver_load("jira", required_keys=["BASE_URL", "API_TOKEN"])
    except CredentialsMissingError as exc:
        raise AuthError(str(exc)) from exc

    base = creds.BASE_URL.rstrip("/")
    token = creds.API_TOKEN

    # Optional keys — resolved through the same Tier ladder but absent
    # is not fatal here. CredentialsMissingError on this second call
    # means the user didn't set EMAIL / FLAVOR; that's expected on
    # server-flavor installs.
    email: str | None = None
    flavor_override: str | None = None
    try:
        opt = _resolver_load("jira", required_keys=["EMAIL"])
        email = (opt.EMAIL or "").strip() or None
    except CredentialsMissingError:
        pass
    try:
        opt = _resolver_load("jira", required_keys=["FLAVOR"])
        flavor_override = (opt.FLAVOR or "").strip().lower() or None
    except CredentialsMissingError:
        pass

    flavor = flavor_override or detect_flavor(base)
    if flavor not in (FLAVOR_CLOUD, FLAVOR_SERVER):
        raise AuthError(f"unsupported JIRA_FLAVOR: {flavor!r}")

    if flavor == FLAVOR_CLOUD and not email:
        raise AuthError(
            "Cloud auth requires JIRA_EMAIL. Run "
            "`credential-setup` skill to supply it."
        )

    return Credentials(base_url=base, token=token, flavor=flavor, email=email)
