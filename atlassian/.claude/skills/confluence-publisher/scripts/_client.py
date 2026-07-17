"""Confluence REST client for publish operations (Cloud and Server/DC).

Internal module — agent should not invoke directly. The API token is
resolved via the in-process ``credbroker`` (Tier 1 env →
Tier 2 OS keyring → Tier 3 dotfile) and is never logged, echoed, or
placed on the command line.

Auth selection:
- Cloud  (host matches *.atlassian.net): HTTP Basic with email:api_token
- Server/DC (anything else):             Bearer <Personal Access Token>

Override auto-detection by setting CONFLUENCE_FLAVOR=cloud|server.

Mirrors the crawler's _client.py shape (same auth, flavor detection,
retry/backoff) so credentials configured for either skill work for
both. Duplicated rather than imported because packs install
independently — a shared helper would require both packs to be present
at runtime.
"""
from __future__ import annotations

import logging
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx

log = logging.getLogger("confluence_publisher.client")

DEFAULT_TIMEOUT_S = 30.0
MAX_RETRIES = 5

FLAVOR_CLOUD = "cloud"
FLAVOR_SERVER = "server"


class ConfluenceError(Exception):
    pass


class AuthError(ConfluenceError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ConflictError(ConfluenceError):
    """Raised on HTTP 409 — page version race."""


@dataclass(frozen=True)
class Credentials:
    base_url: str
    token: str
    flavor: str
    email: str | None


@dataclass(frozen=True)
class PageRef:
    id: str
    title: str
    version: int
    space_key: str
    webui_path: str


def detect_flavor(base_url: str) -> str:
    host = (urlparse(base_url).hostname or "").lower()
    return FLAVOR_CLOUD if host.endswith(".atlassian.net") else FLAVOR_SERVER


class ConfluenceClient:
    """Sync HTTP wrapper around the Confluence v1 REST API."""

    def __init__(
        self,
        credentials: Credentials,
        *,
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
            "User-Agent": "atlassian-confluence-publisher/0.1",
        }
        auth: httpx.Auth | None = None
        if credentials.flavor == FLAVOR_CLOUD:
            if not credentials.email:
                raise AuthError("Cloud auth requires CONFLUENCE_EMAIL")
            auth = httpx.BasicAuth(credentials.email, credentials.token)
        else:
            headers["Authorization"] = f"Bearer {credentials.token}"
        self._client = httpx.Client(
            base_url=self._base,
            headers=headers,
            auth=auth,
            timeout=timeout_s,
            verify=verify_tls,
            follow_redirects=True,
        )

    def __enter__(self) -> "ConfluenceClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self._client.close()

    @property
    def base_url(self) -> str:
        return self._base

    @staticmethod
    def _backoff(attempt: int) -> float:
        # SystemRandom (rather than random) for jitter to keep security
        # scanners quiet; value is not security-sensitive.
        return min(30.0, (2 ** attempt) * 0.5 + secrets.SystemRandom().uniform(0, 0.5))

    def _request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = self._client.request(method, path, **kwargs)
            except httpx.TransportError as exc:
                last_exc = exc
                time.sleep(self._backoff(attempt))
                continue
            if resp.status_code == 401:
                raise AuthError(
                    "401 Unauthorized — credentials missing, invalid, or expired. "
                    "Re-run `credential-setup` skill.",
                    status_code=401,
                )
            if resp.status_code == 403:
                raise AuthError(
                    f"403 Forbidden for {path} — token lacks permission for this resource.",
                    status_code=403,
                )
            if resp.status_code == 409:
                raise ConflictError(
                    f"409 Conflict on {path} — page version changed; re-read needed."
                )
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                retry_after = resp.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else self._backoff(attempt)
                log.warning("HTTP %s on %s — retrying in %.1fs", resp.status_code, path, delay)
                time.sleep(delay)
                continue
            if resp.status_code >= 400:
                raise ConfluenceError(f"HTTP {resp.status_code} on {path}: {resp.text[:300]}")
            return resp
        raise ConfluenceError(
            f"Exhausted {MAX_RETRIES} retries for {path}"
            + (f" (last error: {last_exc})" if last_exc else "")
        )

    # --- High-level operations ---

    def whoami(self) -> dict:
        return self._request("GET", "/rest/api/user/current").json()

    def get_page(self, page_id: str) -> PageRef:
        resp = self._request(
            "GET",
            f"/rest/api/content/{page_id}",
            params={"expand": "version,space"},
        )
        d = resp.json()
        return PageRef(
            id=str(d["id"]),
            title=d.get("title", ""),
            version=int((d.get("version") or {}).get("number", 1)),
            space_key=((d.get("space") or {}).get("key") or ""),
            webui_path=((d.get("_links") or {}).get("webui") or ""),
        )

    def find_page_by_title(self, space_key: str, title: str) -> list[PageRef]:
        resp = self._request(
            "GET",
            "/rest/api/content",
            params={
                "spaceKey": space_key,
                "title": title,
                "expand": "version,space",
                "limit": 25,
            },
        )
        data = resp.json()
        results: list[PageRef] = []
        for d in data.get("results", []):
            results.append(
                PageRef(
                    id=str(d["id"]),
                    title=d.get("title", ""),
                    version=int((d.get("version") or {}).get("number", 1)),
                    space_key=((d.get("space") or {}).get("key") or ""),
                    webui_path=((d.get("_links") or {}).get("webui") or ""),
                )
            )
        return results

    def create_page(
        self,
        *,
        space_key: str,
        title: str,
        body_storage: str,
        parent_id: str | None = None,
    ) -> PageRef:
        payload: dict = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {"storage": {"value": body_storage, "representation": "storage"}},
        }
        if parent_id:
            payload["ancestors"] = [{"id": str(parent_id)}]
        resp = self._request("POST", "/rest/api/content", json=payload)
        d = resp.json()
        return PageRef(
            id=str(d["id"]),
            title=d.get("title", title),
            version=int((d.get("version") or {}).get("number", 1)),
            space_key=space_key,
            webui_path=((d.get("_links") or {}).get("webui") or ""),
        )

    def update_page(
        self,
        *,
        page_id: str,
        title: str,
        space_key: str,
        body_storage: str,
        new_version: int,
        version_comment: str | None = None,
    ) -> PageRef:
        payload: dict = {
            "id": page_id,
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "version": {"number": new_version},
            "body": {"storage": {"value": body_storage, "representation": "storage"}},
        }
        if version_comment:
            payload["version"]["message"] = version_comment
        resp = self._request("PUT", f"/rest/api/content/{page_id}", json=payload)
        d = resp.json()
        return PageRef(
            id=str(d["id"]),
            title=d.get("title", title),
            version=int((d.get("version") or {}).get("number", new_version)),
            space_key=((d.get("space") or {}).get("key") or space_key),
            webui_path=((d.get("_links") or {}).get("webui") or ""),
        )

    def upload_attachment(self, page_id: str, path: Path) -> dict:
        # X-Atlassian-Token: no-check is required for multipart uploads.
        with path.open("rb") as fh:
            resp = self._request(
                "POST",
                f"/rest/api/content/{page_id}/child/attachment",
                headers={"X-Atlassian-Token": "no-check"},
                files={"file": (path.name, fh, "application/octet-stream")},
                params={"allowDuplicated": "true"},
            )
        return resp.json()

    def apply_label(self, page_id: str, label: str) -> None:
        self._request(
            "POST",
            f"/rest/api/content/{page_id}/label",
            json=[{"prefix": "global", "name": label}],
        )


def load_credentials() -> Credentials:
    """Resolve Confluence credentials via the in-process ``credbroker``
    loader. Shares the ``confluence`` namespace with confluence-crawler.
    """
    from credbroker import (
        CredentialsMissingError,
        load_credentials as _resolver_load,
    )

    try:
        creds = _resolver_load("confluence", required_keys=["BASE_URL", "API_TOKEN"])
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
