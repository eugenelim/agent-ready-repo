"""Jira Align REST API 2.0 client.

Internal module — the skill agent dispatches to ``jira_align.py``; this file
is an implementation detail. The API token is resolved via the
in-process ``credbroker`` (Tier 1 env → Tier 2 OS keyring →
Tier 3 dotfile) and is never logged, echoed, or accepted on the command
line.

Authentication is the same for Cloud and self-hosted installs: a Personal
API Token the user generated on their Jira Align Profile page, sent as
``Authorization: bearer <token>``. The flavor field is retained purely so
callers can branch on it if product behavior ever diverges.
"""
from __future__ import annotations

import ipaddress
import json
import logging
import os
import secrets
import socket
import ssl
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Iterable, Mapping
from urllib.parse import urlparse
from urllib.request import proxy_bypass

import httpcore
import httpx

log = logging.getLogger("jira_align.client")

DEFAULT_CONCURRENCY = 4
DEFAULT_TIMEOUT_S = 30.0
MAX_RETRIES = 5
PAGE_SIZE_MAX = 100  # Jira Align caps $top at 100 per call.
API_PREFIX = "/rest/align/api/2"

FLAVOR_CLOUD = "cloud"
FLAVOR_ONPREM = "onprem"


class JiraAlignError(Exception):
    pass


class AuthError(JiraAlignError):
    pass


@dataclass(frozen=True)
class IntakeRequestPolicy:
    """Profile-bound controls for a credentialed, read-only intake request."""

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
    policy: IntakeRequestPolicy,
) -> httpx.AsyncHTTPTransport:
    """Build a proxy-aware transport whose actual socket is DNS-pinned."""
    proxy_url, proxy_pin = _https_proxy_settings(policy)
    transport = httpx.AsyncHTTPTransport(
        verify=_ssl_context(), retries=0, proxy=proxy_url, trust_env=True
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


def _ssl_context() -> ssl.SSLContext:
    """Load system and enterprise CA settings for credentialed intake."""
    context = ssl.create_default_context()
    cafile = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    capath = os.environ.get("SSL_CERT_DIR")
    if cafile or capath:
        context.load_verify_locations(cafile=cafile or None, capath=capath or None)
    return context


@dataclass(frozen=True)
class Credentials:
    base_url: str
    token: str
    flavor: str  # "cloud" or "onprem" — informational; auth header is identical


def detect_flavor(base_url: str) -> str:
    host = (urlparse(base_url).hostname or "").lower()
    if host.endswith((".jiraalign.com", ".agilecraft.com")):
        return FLAVOR_CLOUD
    return FLAVOR_ONPREM


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


class JiraAlignClient:
    """Async wrapper around Jira Align REST API 2.0.

    Provides a generic ``get``/``list``/``raw`` surface rather than one
    method per resource — the API is uniform (``/rest/align/api/2/<resource>``)
    so callers pass the resource name as a string.
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
        headers = {
            "Accept": "application/json",
            "User-Agent": "atlassian-jira-align/0.1",
            # Jira Align requires lowercase "bearer" per their docs; HTTP
            # header values are case-insensitive per RFC but we match docs.
            "Authorization": f"bearer {credentials.token}",
        }
        transport = _pinned_transport(intake_policy) if intake_policy is not None else None
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

    async def __aenter__(self) -> JiraAlignClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._client.aclose()

    @property
    def flavor(self) -> str:
        return self._flavor

    @property
    def base_url(self) -> str:
        return self._base

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any | None = None,
    ) -> httpx.Response:
        if self._intake_policy is not None and method.upper() not in ("GET", "HEAD"):
            raise JiraAlignError("tracker intake is read-only; request refused")
        async with self._sem:
            last_exc: Exception | None = None
            attempts = (
                self._intake_policy.max_attempts
                if self._intake_policy is not None
                else MAX_RETRIES
            )
            for attempt in range(attempts):
                try:
                    if self._intake_policy is not None:
                        self._intake_policy.assert_bound(self._base)
                        resp = await self._bounded_request(
                            method, path, params=params, json_body=json_body
                        )
                    else:
                        resp = await self._client.request(
                            method, path, params=params, json=json_body
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
                    raise JiraAlignError("tracker intake redirect was refused")

                if resp.status_code == 401:
                    raise AuthError(
                        "401 Unauthorized — the Jira Align API token is missing, "
                        "invalid, or expired. Re-run `credential-setup` skill."
                    )
                if resp.status_code == 403:
                    raise AuthError(
                        f"403 Forbidden for {path} — the token lacks permission "
                        "for this resource. Check the user's Jira Align role."
                    )
                if resp.status_code == 429 or 500 <= resp.status_code < 600:
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
                    raise JiraAlignError(
                        f"HTTP {resp.status_code} on {path}: {resp.text[:300]}"
                    )
                return resp

            raise JiraAlignError(
                f"Exhausted {attempts} attempts for {path}"
                + (f" (last error: {last_exc})" if last_exc else "")
            )

    async def _bounded_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None,
        json_body: Any | None,
    ) -> httpx.Response:
        """Stream one intake response and stop before its byte cap is crossed."""
        assert self._intake_policy is not None
        request = self._client.build_request(
            method, path, params=params, json=json_body
        )
        response = await self._client.send(request, stream=True)
        content = bytearray()
        try:
            async for chunk in response.aiter_bytes():
                if len(content) + len(chunk) > self._intake_policy.max_bytes:
                    raise JiraAlignError(
                        "tracker intake response exceeded its byte budget"
                    )
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
        # SystemRandom (rather than random) for the jitter so security
        # scanners don't flag the PRNG; value is not security-sensitive.
        return min(30.0, (2 ** attempt) * 0.5 + secrets.SystemRandom().uniform(0, 0.5))

    # --- High-level operations ---------------------------------------------

    async def whoami(self) -> dict:
        """Return the authenticated user record.

        Jira Align exposes the current user via ``/users/current``; we fall
        back to a minimal ``/users?$top=1`` ping if that path is not
        available on a given version.
        """
        try:
            resp = await self._request("GET", f"{API_PREFIX}/users/current")
            return resp.json()
        except JiraAlignError:
            resp = await self._request(
                "GET", f"{API_PREFIX}/users", params={"$top": 1}
            )
            return {"ping": "ok", "sample": resp.json()}

    async def get_one(
        self, resource: str, item_id: str, *, expand: str | None = None
    ) -> dict:
        params: dict[str, Any] = {}
        if expand:
            params["expand"] = expand
        resp = await self._request(
            "GET", f"{API_PREFIX}/{resource}/{item_id}", params=params or None
        )
        data = resp.json()
        return data if isinstance(data, dict) else {"value": data}

    async def iter_list(
        self,
        resource: str,
        *,
        filter_expr: str | None = None,
        select: str | None = None,
        orderby: str | None = None,
        expand: str | None = None,
        page_size: int = PAGE_SIZE_MAX,
        limit: int | None = None,
    ) -> AsyncIterator[dict]:
        """Iterate records from ``/rest/align/api/2/<resource>``.

        Uses ``$top`` + ``$skip`` to paginate. The API caps ``$top`` at 100;
        we clamp silently. ``limit`` is the total cap across all pages;
        ``None`` means "drain the collection".
        """
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        page_size = min(page_size, PAGE_SIZE_MAX)
        skip = 0
        yielded = 0
        while True:
            remaining = None if limit is None else max(0, limit - yielded)
            if remaining == 0:
                return
            top = page_size if remaining is None else min(page_size, remaining)
            params: dict[str, Any] = {"$top": top, "$skip": skip}
            if filter_expr:
                params["$filter"] = filter_expr
            if select:
                params["$select"] = select
            if orderby:
                params["$orderby"] = orderby
            if expand:
                params["expand"] = expand

            resp = await self._request(
                "GET", f"{API_PREFIX}/{resource}", params=params
            )
            data = resp.json()
            items = _extract_items(data)
            if not items:
                return
            for item in items:
                yield item
                yielded += 1
                if limit is not None and yielded >= limit:
                    return
            if len(items) < top:
                return
            skip += len(items)

    async def create(self, resource: str, body: Mapping[str, Any]) -> Any:
        """POST a new record to ``/rest/align/api/2/<resource>``.

        Returns the parsed JSON response (usually the created record with
        its server-assigned id), or ``None`` for 204 responses.
        """
        resp = await self._request(
            "POST", f"{API_PREFIX}/{resource}", json_body=dict(body)
        )
        if not resp.content:
            return None
        return resp.json()

    async def update(
        self,
        resource: str,
        item_id: str,
        body: Mapping[str, Any],
        *,
        method: str = "PUT",
    ) -> Any:
        """Update an existing record. Use ``method='PATCH'`` for endpoints
        that expose partial updates; ``PUT`` is the Jira Align default."""
        if method not in ("PUT", "PATCH"):
            raise ValueError("update method must be PUT or PATCH")
        resp = await self._request(
            method, f"{API_PREFIX}/{resource}/{item_id}", json_body=dict(body)
        )
        if not resp.content:
            return None
        return resp.json()

    async def delete(self, resource: str, item_id: str) -> None:
        await self._request("DELETE", f"{API_PREFIX}/{resource}/{item_id}")

    async def raw(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any | None = None,
    ) -> Any:
        """Perform an arbitrary request. ``path`` may be absolute
        (``/rest/align/api/2/foo``) or relative to the API prefix (``foo``)."""
        if not path.startswith("/"):
            path = f"{API_PREFIX}/{path}"
        resp = await self._request(method, path, params=params, json_body=json_body)
        if not resp.content:
            return None
        ctype = resp.headers.get("content-type", "")
        if "json" in ctype:
            return resp.json()
        return resp.text


def _extract_items(payload: Any) -> list[dict]:
    """Normalize a Jira Align list response to a plain list of dicts.

    Jira Align REST API 2.0 follows OData and returns either:
      - a bare JSON array (some endpoints), or
      - an OData envelope ``{"value": [...]}`` with optional metadata
        keys (``@odata.count``, ``@odata.nextLink``).

    We pin to those two shapes. If a response doesn't match, the
    iterator stops (logging the unexpected shape would leak payloads,
    so we fail closed instead).
    """
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        inner = payload.get("value")
        if isinstance(inner, list):
            return [x for x in inner if isinstance(x, dict)]
    return []


def load_base_url() -> str:
    """Resolve only the configured Jira Align origin, without loading a token."""
    from credbroker import CredentialsMissingError
    from credbroker import load_credentials as _resolver_load

    try:
        creds = _resolver_load("jiraalign", required_keys=["BASE_URL"])
    except CredentialsMissingError as exc:
        raise AuthError(str(exc)) from exc
    return creds.BASE_URL.rstrip("/")


def load_credentials() -> Credentials:
    """Resolve Jira Align credentials via the in-process ``credbroker``
    loader (Tier 1 env → Tier 2 OS keyring → Tier 3 dotfile).

    Namespace: ``jiraalign``. Required: ``BASE_URL``, ``API_TOKEN``.
    Optional (best-effort): ``FLAVOR`` (``cloud`` or ``onprem``;
    auto-detected from URL host when absent).

    Env-var shape: ``JIRAALIGN_BASE_URL``, ``JIRAALIGN_API_TOKEN``,
    ``JIRAALIGN_FLAVOR``. The schema lives at
    ``references/creds-schema.toml``; populate any tier with
    ``credential-setup`` skill.
    """
    from credbroker import (
        CredentialsMissingError,
    )
    from credbroker import (
        load_credentials as _resolver_load,
    )

    try:
        creds = _resolver_load(
            "jiraalign", required_keys=["BASE_URL", "API_TOKEN"]
        )
    except CredentialsMissingError as exc:
        raise AuthError(str(exc)) from exc

    base = creds.BASE_URL.rstrip("/")
    token = creds.API_TOKEN

    flavor_override: str | None = None
    try:
        opt = _resolver_load("jiraalign", required_keys=["FLAVOR"])
        flavor_override = (opt.FLAVOR or "").strip().lower() or None
    except CredentialsMissingError:
        pass

    flavor = flavor_override or detect_flavor(base)
    if flavor not in (FLAVOR_CLOUD, FLAVOR_ONPREM):
        raise AuthError(f"unsupported JIRAALIGN_FLAVOR: {flavor!r}")

    return Credentials(base_url=base, token=token, flavor=flavor)
