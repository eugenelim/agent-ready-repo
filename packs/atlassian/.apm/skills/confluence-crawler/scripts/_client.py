"""Async Confluence REST client for both Cloud and Server/Data Center.

Internal module — agent should not invoke directly. The API token is
resolved via the in-process ``credbroker`` (Tier 1 env →
Tier 2 OS keyring → Tier 3 dotfile) and is never logged, echoed, or
placed on the command line.

Auth selection:
- Cloud  (host matches *.atlassian.net): HTTP Basic with email:api_token
- Server/DC (anything else):             Bearer <Personal Access Token>

Override auto-detection by setting CONFLUENCE_FLAVOR=cloud|server.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import ssl
from dataclasses import dataclass
from typing import TYPE_CHECKING, AsyncIterator
from urllib.parse import urlparse

import httpx

if TYPE_CHECKING:
    from _sso_config import SsoConfig

log = logging.getLogger("confluence_crawler.client")

DEFAULT_CONCURRENCY = 4
DEFAULT_MIN_DELAY_MS = 100
DEFAULT_TIMEOUT_S = 30.0
MAX_RETRIES = 5
PAGE_SIZE = 50

FLAVOR_CLOUD = "cloud"
FLAVOR_SERVER = "server"


class ConfluenceError(Exception):
    pass


class AuthError(ConfluenceError):
    pass


@dataclass(frozen=True)
class Page:
    id: str
    title: str
    version: int
    updated: str
    author: str | None
    parent_id: str | None
    labels: tuple[str, ...]
    storage_xhtml: str
    webui_path: str
    space_key: str


@dataclass(frozen=True)
class Attachment:
    id: str
    filename: str
    media_type: str
    download_path: str
    file_size: int


@dataclass(frozen=True)
class Credentials:
    base_url: str
    token: str
    flavor: str  # "cloud" or "server"
    email: str | None  # required when flavor == "cloud"


def detect_flavor(base_url: str) -> str:
    host = (urlparse(base_url).hostname or "").lower()
    return FLAVOR_CLOUD if host.endswith(".atlassian.net") else FLAVOR_SERVER


def _sso_cafile_capath() -> tuple[str | None, str | None]:
    """Resolve the CA bundle file + dir for the cookie-path SSL context (AC8).

    httpx (``trust_env``) natively honors ``SSL_CERT_FILE`` / ``SSL_CERT_DIR`` but
    does **not** read ``REQUESTS_CA_BUNDLE``; we map it here. Precedence:
    ``SSL_CERT_FILE`` wins over ``REQUESTS_CA_BUNDLE`` when both are set.
    """
    cafile = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    capath = os.environ.get("SSL_CERT_DIR")
    return (cafile or None, capath or None)


def _sso_ssl_context() -> ssl.SSLContext:
    """SSL context for the cookie path: the system trust store *plus* any
    ``SSL_CERT_FILE`` / ``SSL_CERT_DIR`` / ``REQUESTS_CA_BUNDLE`` the corporate
    environment sets — loaded on top of (never clobbering) the default store (AC8).
    """
    ctx = ssl.create_default_context()
    cafile, capath = _sso_cafile_capath()
    if cafile or capath:
        ctx.load_verify_locations(cafile=cafile, capath=capath)
    return ctx


class ConfluenceClient:
    """Async wrapper around the Confluence v1 REST API (works for both
    Cloud and Server/Data Center)."""

    def __init__(
        self,
        credentials: Credentials,
        *,
        concurrency: int = DEFAULT_CONCURRENCY,
        min_delay_ms: int = DEFAULT_MIN_DELAY_MS,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        verify_tls: bool = True,
    ) -> None:
        base_url = credentials.base_url
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")

        self._base = base_url.rstrip("/")
        self._flavor = credentials.flavor
        # Token path. The SSO-cookie path is built via from_sso_cookies and sets
        # these to "sso-cookie" / the profile name; _request branches on them.
        self._auth_mode = "creds"
        self._profile: str | None = None
        headers = {
            "Accept": "application/json",
            "User-Agent": "atlassian-confluence-crawler/0.1",
        }
        auth: httpx.Auth | None = None
        if credentials.flavor == FLAVOR_CLOUD:
            if not credentials.email:
                raise AuthError("Cloud auth requires CONFLUENCE_EMAIL")
            auth = httpx.BasicAuth(credentials.email, credentials.token)
        else:
            headers["Authorization"] = f"Bearer {credentials.token}"

        self._client = httpx.AsyncClient(
            base_url=self._base,
            headers=headers,
            auth=auth,
            timeout=timeout_s,
            verify=verify_tls,
            follow_redirects=True,
        )
        self._sem = asyncio.Semaphore(concurrency)
        self._min_delay = min_delay_ms / 1000.0
        self._last_request = 0.0
        self._lock = asyncio.Lock()

    @classmethod
    def from_sso_cookies(
        cls,
        sso_config: "SsoConfig",
        *,
        concurrency: int = DEFAULT_CONCURRENCY,
        min_delay_ms: int = DEFAULT_MIN_DELAY_MS,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> "ConfluenceClient":
        """Build a Data Center client authenticated by a captured SSO cookie jar.

        Resolves the jar via credbroker (fail-closed), filters it to the declared
        ``cookie_domains`` (AC4), confirms the base host is within those domains
        (AC6), and builds an httpx client with the confined jar attached, **no**
        ``Authorization`` header (AC7), ``follow_redirects=False`` (AC20), and the
        corporate proxy / trust store honored (AC8). GET/HEAD only (AC9).
        """
        import credbroker

        base_url = sso_config.base_url
        parsed = urlparse(base_url)
        if parsed.scheme != "https":
            raise AuthError(
                "SSO-cookie base_url must be https (the session cookie is a bearer secret)"
            )
        host = parsed.hostname or ""
        try:
            credbroker.require_host_in_cookie_domains(host, sso_config.cookie_domains)
            jar_path = credbroker.load_sso_cookies(sso_config.profile)
        except credbroker.SsoError as exc:
            raise AuthError(str(exc)) from exc

        raw_cookies = json.loads(jar_path.read_text(encoding="utf-8"))
        confined = credbroker.filter_jar_to_domains(
            raw_cookies, sso_config.cookie_domains
        )

        self = cls.__new__(cls)
        self._base = base_url.rstrip("/")
        self._flavor = FLAVOR_SERVER  # DC only — Cloud cookie auth is out of scope
        self._auth_mode = "sso-cookie"
        self._profile = sso_config.profile

        cookies = httpx.Cookies()
        for c in confined:
            # Preserve the jar's domain verbatim (keep any leading dot) so httpx's
            # cookiejar subdomain matching attaches a ".corp.example.com" cookie
            # to jira/confluence.corp.example.com.
            cookies.set(
                c["name"],
                c.get("value", ""),
                domain=c.get("domain", ""),
                path=c.get("path") or "/",
            )

        headers = {
            "Accept": "application/json",
            "User-Agent": "atlassian-confluence-crawler/0.1",
        }  # deliberately NO Authorization header on the cookie path (AC7)
        self._client = httpx.AsyncClient(
            base_url=self._base,
            headers=headers,
            cookies=cookies,
            timeout=timeout_s,
            verify=_sso_ssl_context(),
            trust_env=True,  # corporate proxy + SSL_CERT_FILE/SSL_CERT_DIR (AC8)
            follow_redirects=False,  # AC20 — never re-attach the cookie cross-host
        )
        self._sem = asyncio.Semaphore(concurrency)
        self._min_delay = min_delay_ms / 1000.0
        self._last_request = 0.0
        self._lock = asyncio.Lock()
        return self

    async def __aenter__(self) -> "ConfluenceClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        # Cookie-path write refusal (AC9). confluence-crawler has no raw() escape
        # hatch, so the allowlist guards the _request method parameter directly;
        # raised before any request reaches the wire.
        if self._auth_mode == "sso-cookie" and method.upper() not in ("GET", "HEAD"):
            raise ConfluenceError(
                "writes over SSO-cookie auth are not supported yet (RFC-0035 v1); "
                "use a personal access token, or wait for the XSRF follow-on"
            )

        async with self._sem:
            async with self._lock:
                now = asyncio.get_running_loop().time()
                wait = self._min_delay - (now - self._last_request)
                if wait > 0:
                    await asyncio.sleep(wait)
                self._last_request = asyncio.get_running_loop().time()

            last_exc: Exception | None = None
            for attempt in range(MAX_RETRIES):
                try:
                    resp = await self._client.request(method, path, **kwargs)
                except httpx.TransportError as exc:
                    last_exc = exc
                    await asyncio.sleep(self._backoff(attempt))
                    continue

                if resp.status_code == 401:
                    if self._auth_mode == "sso-cookie":
                        # Stop using the known-stale jar; remediation names the
                        # profile, never the cookie bytes (AC11).
                        self._client.cookies.clear()
                        raise AuthError(
                            f"401 Unauthorized — SSO session expired; run "
                            f"'sso-broker register {self._profile}' to re-authenticate"
                        )
                    raise AuthError(
                        "401 Unauthorized — credentials are missing, invalid, or expired. "
                        "Re-run `credential-setup` skill."
                    )
                if self._auth_mode == "sso-cookie" and 300 <= resp.status_code < 400:
                    # follow_redirects disabled on the cookie path (AC20): surface a
                    # 30x, never follow it (which would re-attach the session cookie).
                    raise AuthError(
                        f"SSO session may have expired (HTTP {resp.status_code} "
                        f"redirect, not followed); run 'sso-broker register "
                        f"{self._profile}' to re-authenticate"
                    )
                if resp.status_code == 403:
                    raise AuthError(
                        f"403 Forbidden for {path} — token lacks permission for this resource."
                    )
                if resp.status_code == 429 or 500 <= resp.status_code < 600:
                    retry_after = resp.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after and retry_after.isdigit() else self._backoff(attempt)
                    log.warning("HTTP %s on %s — retrying in %.1fs", resp.status_code, path, delay)
                    await asyncio.sleep(delay)
                    continue
                if resp.status_code >= 400:
                    raise ConfluenceError(f"HTTP {resp.status_code} on {path}: {resp.text[:300]}")
                return resp

            raise ConfluenceError(
                f"Exhausted {MAX_RETRIES} retries for {path}"
                + (f" (last error: {last_exc})" if last_exc else "")
            )

    @staticmethod
    def _backoff(attempt: int) -> float:
        # SystemRandom (rather than random) for the jitter so security
        # scanners don't flag the PRNG; value is not security-sensitive.
        return min(30.0, (2 ** attempt) * 0.5 + secrets.SystemRandom().uniform(0, 0.5))

    # --- High-level operations ---

    async def whoami(self) -> dict:
        resp = await self._request("GET", "/rest/api/user/current")
        return resp.json()

    async def get_space_homepage_id(self, space_key: str) -> str | None:
        resp = await self._request(
            "GET",
            f"/rest/api/space/{space_key}",
            params={"expand": "homepage"},
        )
        data = resp.json()
        home = data.get("homepage") or {}
        hid = home.get("id")
        return str(hid) if hid else None

    async def get_page(self, page_id: str) -> Page:
        resp = await self._request(
            "GET",
            f"/rest/api/content/{page_id}",
            params={
                "expand": (
                    "body.storage,version,ancestors,space,"
                    "metadata.labels,history.createdBy,history.lastUpdated"
                )
            },
        )
        d = resp.json()
        ancestors = d.get("ancestors") or []
        parent_id = str(ancestors[-1]["id"]) if ancestors else None
        labels = tuple(
            lbl.get("name", "")
            for lbl in (d.get("metadata", {}).get("labels", {}).get("results") or [])
            if lbl.get("name")
        )
        history = d.get("history") or {}
        last_updated = (history.get("lastUpdated") or {}).get("when") or ""
        created_by = history.get("createdBy") or {}
        # username exists on Server/DC; Cloud only returns displayName/accountId.
        author = (
            created_by.get("username")
            or created_by.get("displayName")
            or created_by.get("publicName")
            or None
        )
        webui = ((d.get("_links") or {}).get("webui")) or ""
        return Page(
            id=str(d["id"]),
            title=d.get("title", ""),
            version=int((d.get("version") or {}).get("number", 1)),
            updated=last_updated,
            author=author,
            parent_id=parent_id,
            labels=labels,
            storage_xhtml=((d.get("body", {}).get("storage", {}) or {}).get("value") or ""),
            webui_path=webui,
            space_key=((d.get("space") or {}).get("key") or ""),
        )

    async def iter_children(self, page_id: str) -> AsyncIterator[dict]:
        start = 0
        while True:
            resp = await self._request(
                "GET",
                f"/rest/api/content/{page_id}/child/page",
                params={"start": start, "limit": PAGE_SIZE, "expand": "version"},
            )
            data = resp.json()
            for item in data.get("results", []):
                yield item
            size = int(data.get("size", 0))
            if size < PAGE_SIZE:
                return
            start += size

    async def iter_attachments(self, page_id: str) -> AsyncIterator[Attachment]:
        start = 0
        while True:
            resp = await self._request(
                "GET",
                f"/rest/api/content/{page_id}/child/attachment",
                params={"start": start, "limit": PAGE_SIZE},
            )
            data = resp.json()
            for item in data.get("results", []):
                ext = item.get("extensions") or {}
                links = item.get("_links") or {}
                yield Attachment(
                    id=str(item["id"]),
                    filename=item.get("title", str(item["id"])),
                    media_type=ext.get("mediaType", "application/octet-stream"),
                    download_path=links.get("download", ""),
                    file_size=int(ext.get("fileSize", 0) or 0),
                )
            size = int(data.get("size", 0))
            if size < PAGE_SIZE:
                return
            start += size

    async def download_attachment(self, download_path: str, dest: Path) -> None:
        if not download_path:
            raise ConfluenceError("attachment has no download path")
        # This streaming GET bypasses the _request chokepoint, so it carries the
        # cookie-path confinement inline: refuse an absolute / off-host download
        # link (server-supplied) so the session cookie can never leave the base
        # host. follow_redirects=False already blocks a cross-host 30x; this also
        # blocks an absolute Location-style `download` value (AC4/AC6/AC20 spirit).
        if self._auth_mode == "sso-cookie":
            parsed = urlparse(download_path)
            if parsed.scheme or parsed.netloc:
                raise ConfluenceError(
                    "refusing an absolute attachment download URL on the SSO-cookie "
                    f"path (must be a path relative to the base host): {download_path!r}"
                )
        dest.parent.mkdir(parents=True, exist_ok=True)
        async with self._sem:
            async with self._client.stream("GET", download_path) as resp:
                if resp.status_code >= 400:
                    raise ConfluenceError(
                        f"HTTP {resp.status_code} downloading {download_path}"
                    )
                tmp = dest.with_suffix(dest.suffix + ".part")
                with tmp.open("wb") as fh:
                    async for chunk in resp.aiter_bytes():
                        fh.write(chunk)
                tmp.replace(dest)


def load_credentials() -> Credentials:
    """Resolve Confluence credentials via the in-process ``credbroker``
    loader (Tier 1 env → Tier 2 OS keyring → Tier 3 dotfile).

    Namespace: ``confluence``. Required: ``BASE_URL``, ``API_TOKEN``.
    Optional (best-effort): ``EMAIL`` (required at validation time for
    Cloud only) and ``FLAVOR`` (auto-detected from URL host when absent).

    Env-var shape: ``CONFLUENCE_BASE_URL``, ``CONFLUENCE_API_TOKEN``,
    ``CONFLUENCE_EMAIL``, ``CONFLUENCE_FLAVOR``. Schema lives at
    ``references/creds-schema.toml``; populate any tier with
    ``credential-setup`` skill.
    """
    from credbroker import (
        CredentialsMissingError,
        load_credentials as _resolver_load,
    )

    try:
        creds = _resolver_load(
            "confluence", required_keys=["BASE_URL", "API_TOKEN"]
        )
    except CredentialsMissingError as exc:
        raise AuthError(str(exc)) from exc

    base = creds.BASE_URL.rstrip("/")
    token = creds.API_TOKEN

    email: str | None = None
    flavor_override: str | None = None
    try:
        opt = _resolver_load("confluence", required_keys=["EMAIL"])
        email = (opt.EMAIL or "").strip() or None
    except CredentialsMissingError:
        pass
    try:
        opt = _resolver_load("confluence", required_keys=["FLAVOR"])
        flavor_override = (opt.FLAVOR or "").strip().lower() or None
    except CredentialsMissingError:
        pass

    flavor = flavor_override or detect_flavor(base)
    if flavor not in (FLAVOR_CLOUD, FLAVOR_SERVER):
        raise AuthError(f"unsupported CONFLUENCE_FLAVOR: {flavor!r}")

    if flavor == FLAVOR_CLOUD and not email:
        raise AuthError(
            "Cloud authentication requires CONFLUENCE_EMAIL. Run "
            "`credential-setup` skill to supply it."
        )

    return Credentials(base_url=base, token=token, flavor=flavor, email=email)
