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

import asyncio
import logging
import secrets
from dataclasses import dataclass
from typing import Any, AsyncIterator, Mapping
from urllib.parse import urlparse

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
class Credentials:
    base_url: str
    token: str
    flavor: str  # "cloud" or "onprem" — informational; auth header is identical


def detect_flavor(base_url: str) -> str:
    host = (urlparse(base_url).hostname or "").lower()
    if host.endswith(".jiraalign.com") or host.endswith(".agilecraft.com"):
        return FLAVOR_CLOUD
    return FLAVOR_ONPREM


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
    ) -> None:
        base_url = credentials.base_url
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")

        self._base = base_url.rstrip("/")
        self._flavor = credentials.flavor
        headers = {
            "Accept": "application/json",
            "User-Agent": "atlassian-jira-align/0.1",
            # Jira Align requires lowercase "bearer" per their docs; HTTP
            # header values are case-insensitive per RFC but we match docs.
            "Authorization": f"bearer {credentials.token}",
        }
        self._client = httpx.AsyncClient(
            base_url=self._base,
            headers=headers,
            timeout=timeout_s,
            verify=verify_tls,
            follow_redirects=True,
        )
        # Concurrency is gated by the semaphore alone. Throttling for
        # rate-limited endpoints comes from the API's own 429 + Retry-After
        # response, which the request loop honors.
        self._sem = asyncio.Semaphore(concurrency)

    async def __aenter__(self) -> "JiraAlignClient":
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
        async with self._sem:
            last_exc: Exception | None = None
            for attempt in range(MAX_RETRIES):
                try:
                    resp = await self._client.request(
                        method, path, params=params, json=json_body
                    )
                except httpx.TransportError as exc:
                    last_exc = exc
                    await asyncio.sleep(self._backoff(attempt))
                    continue

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
                        float(retry_after)
                        if retry_after and retry_after.replace(".", "", 1).isdigit()
                        else self._backoff(attempt)
                    )
                    log.warning(
                        "HTTP %s on %s — retrying in %.1fs",
                        resp.status_code, path, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                if resp.status_code >= 400:
                    raise JiraAlignError(
                        f"HTTP {resp.status_code} on {path}: {resp.text[:300]}"
                    )
                return resp

            raise JiraAlignError(
                f"Exhausted {MAX_RETRIES} retries for {path}"
                + (f" (last error: {last_exc})" if last_exc else "")
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
