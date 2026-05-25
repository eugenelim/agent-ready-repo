"""Figma REST API client (api.figma.com v1).

Internal module — the skill agent dispatches to ``figma.py``; this file is
an implementation detail. The Personal Access Token is resolved via the
``agentbundle.credentials`` loader (Tier 1 env → Tier 2 OS keyring →
Tier 3 dotfile) and is never logged, echoed, or accepted on the command
line.

Auth: ``X-Figma-Token: <PAT>``. Figma is SaaS-only; there is no on-prem
flavor, so this client has no flavor branching.

Rate limits: Figma documents per-endpoint tiers (Tier 1 ≈ generous, Tier 2
≈ ~25 req/min for image-render endpoints). The client honors
``Retry-After`` on 429 and retries with exponential backoff + jitter.
"""
from __future__ import annotations

import asyncio
import logging
import secrets
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse

import httpx

log = logging.getLogger("figma.client")

API_BASE = "https://api.figma.com"
DEFAULT_CONCURRENCY = 4
DEFAULT_TIMEOUT_S = 30.0
MAX_RETRIES = 5

# Image renders come back as presigned URLs on these hosts. Anything else
# is rejected by ``download()`` — Figma's render endpoint should never
# return third-party hosts, and if a malicious response (or MITM) tried
# to point the download at a token-stealing endpoint, the same client
# isn't carrying the Figma token but the host check is additional
# defence in depth.
#
# Two patterns accepted, checked in ``_is_allowed_download_host`` below:
#   1. ``figma.com`` and ``*.figma.com`` — Figma's own domain.
#   2. ``figma-alpha-api.s3.<region>.amazonaws.com`` — the documented
#      region-specific S3 bucket Figma uses for render output.
#
# A wider ``figma-*.s3.*.amazonaws.com`` was considered for robustness
# against Figma changing the bucket name, but rejected: S3 bucket names
# are a first-come-first-served global namespace, so an attacker could
# register e.g. ``figma-evil`` and serve poisoned content there. The
# narrow pattern keeps the surface to a host Figma actually owns. If a
# user hits a download rejection because Figma changed buckets, they
# report and we widen the allowlist explicitly for the new name.
def _is_allowed_download_host(host: str) -> bool:
    host = host.lower()
    if host == "figma.com" or host.endswith(".figma.com"):
        return True
    if (
        host.startswith("figma-alpha-api.s3.")
        and host.endswith(".amazonaws.com")
    ):
        return True
    return False


class FigmaError(Exception):
    pass


class AuthError(FigmaError):
    pass


class AccessError(FigmaError):
    """403/404 likely meaning the token lacks the scope (Variables /
    Dev Resources typically need Enterprise / Dev Mode)."""


@dataclass(frozen=True)
class Credentials:
    token: str


class FigmaClient:
    """Async wrapper around the Figma REST API."""

    def __init__(
        self,
        credentials: Credentials,
        *,
        concurrency: int = DEFAULT_CONCURRENCY,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        headers = {
            "Accept": "application/json",
            "User-Agent": "figma-skill/0.1",
            "X-Figma-Token": credentials.token,
        }
        self._client = httpx.AsyncClient(
            base_url=API_BASE,
            headers=headers,
            timeout=timeout_s,
            follow_redirects=True,
        )
        # Separate client for downloading rendered images — they come from
        # S3 presigned URLs that must NOT carry the Figma token header.
        # ``follow_redirects=False``: render presigned URLs point straight
        # at the bucket; a 30x response means something unexpected, and
        # silently following a redirect to an attacker-chosen host is
        # the threat model security-review flagged.
        self._download_client = httpx.AsyncClient(
            headers={"User-Agent": "figma-skill/0.1"},
            timeout=timeout_s,
            follow_redirects=False,
        )
        self._sem = asyncio.Semaphore(concurrency)

    async def __aenter__(self) -> "FigmaClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._client.aclose()
        await self._download_client.aclose()

    # --- low-level request -------------------------------------------------

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
            last_status: int | None = None
            for attempt in range(MAX_RETRIES):
                try:
                    resp = await self._client.request(
                        method, path, params=params, json=json_body,
                    )
                except httpx.TransportError as exc:
                    last_exc = exc
                    await asyncio.sleep(self._backoff(attempt))
                    continue

                if resp.status_code == 401:
                    raise AuthError(
                        "401 Unauthorized — Figma token missing, invalid, or "
                        "expired. Re-run `agentbundle creds setup figma`."
                    )
                if resp.status_code == 403:
                    # 403 on Figma typically means the token's scope doesn't
                    # cover this endpoint. Variables and Dev Resources are
                    # the common offenders (Enterprise / Dev Mode features).
                    raise AccessError(
                        f"403 Forbidden for {path} — token lacks scope, or "
                        "the endpoint requires Enterprise / Dev Mode access."
                    )
                if resp.status_code == 404:
                    # 404 may be a real not-found OR a hidden 403 for an
                    # endpoint the token can't see. The caller decides; we
                    # surface the body verbatim so it can be inspected.
                    raise FigmaError(
                        f"404 Not Found for {path}: {resp.text[:300]}"
                    )
                if resp.status_code == 429 or 500 <= resp.status_code < 600:
                    last_status = resp.status_code
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
                    raise FigmaError(
                        f"HTTP {resp.status_code} on {path}: {resp.text[:300]}"
                    )
                return resp

            tail = []
            if last_status is not None:
                tail.append(f"last status: {last_status}")
            if last_exc is not None:
                tail.append(f"last error: {last_exc}")
            suffix = f" ({'; '.join(tail)})" if tail else ""
            raise FigmaError(
                f"Exhausted {MAX_RETRIES} retries for {path}{suffix}"
            )

    @staticmethod
    def _backoff(attempt: int) -> float:
        # SystemRandom for the jitter so security scanners don't flag the
        # PRNG; value is not security-sensitive.
        return min(30.0, (2 ** attempt) * 0.5 + secrets.SystemRandom().uniform(0, 0.5))

    # --- identity ----------------------------------------------------------

    async def whoami(self) -> dict:
        """GET /v1/me — return the authenticated user record."""
        resp = await self._request("GET", "/v1/me")
        data = resp.json()
        return data if isinstance(data, dict) else {"value": data}

    # --- files -------------------------------------------------------------

    async def get_file(
        self,
        file_key: str,
        *,
        ids: str | None = None,
        depth: int | None = None,
        geometry: str | None = None,
        version: str | None = None,
        plugin_data: str | None = None,
        branch_data: bool = False,
    ) -> dict:
        """GET /v1/files/:key — full document or scoped subtree."""
        params: dict[str, Any] = {}
        if ids:
            params["ids"] = ids
        if depth is not None:
            params["depth"] = depth
        if geometry:
            params["geometry"] = geometry
        if version:
            params["version"] = version
        if plugin_data:
            params["plugin_data"] = plugin_data
        if branch_data:
            params["branch_data"] = "true"
        resp = await self._request(
            "GET", f"/v1/files/{file_key}", params=params or None
        )
        return resp.json()

    async def get_file_nodes(
        self,
        file_key: str,
        *,
        ids: str,
        depth: int | None = None,
        geometry: str | None = None,
        version: str | None = None,
    ) -> dict:
        """GET /v1/files/:key/nodes — fetch specific nodes by id."""
        params: dict[str, Any] = {"ids": ids}
        if depth is not None:
            params["depth"] = depth
        if geometry:
            params["geometry"] = geometry
        if version:
            params["version"] = version
        resp = await self._request(
            "GET", f"/v1/files/{file_key}/nodes", params=params,
        )
        return resp.json()

    async def get_file_meta(self, file_key: str) -> dict:
        """GET /v1/files/:key/meta — lightweight file metadata."""
        resp = await self._request("GET", f"/v1/files/{file_key}/meta")
        return resp.json()

    async def list_versions(
        self,
        file_key: str,
        *,
        page_size: int | None = None,
        before: int | None = None,
        after: int | None = None,
    ) -> dict:
        """GET /v1/files/:key/versions — version history."""
        params: dict[str, Any] = {}
        if page_size is not None:
            params["page_size"] = page_size
        if before is not None:
            params["before"] = before
        if after is not None:
            params["after"] = after
        resp = await self._request(
            "GET", f"/v1/files/{file_key}/versions", params=params or None,
        )
        return resp.json()

    # --- image rendering ---------------------------------------------------

    async def render_images(
        self,
        file_key: str,
        *,
        ids: str,
        format: str = "png",
        scale: float = 1.0,
        svg_outline_text: bool = True,
        svg_include_id: bool = False,
        svg_simplify_stroke: bool = True,
        use_absolute_bounds: bool = False,
        version: str | None = None,
    ) -> dict:
        """GET /v1/images/:key — render nodes to images.

        Returns ``{"err": null, "images": {"<node_id>": "<presigned URL>"}}``.
        Callers fetch each URL via ``download()`` to get the bytes.
        """
        if format not in ("png", "jpg", "svg", "pdf"):
            raise ValueError(f"unsupported format: {format!r}")
        if scale <= 0 or scale > 4:
            raise ValueError(f"scale must be in (0, 4]: {scale}")
        params: dict[str, Any] = {
            "ids": ids,
            "format": format,
            "scale": scale,
        }
        if format == "svg":
            params["svg_outline_text"] = str(svg_outline_text).lower()
            params["svg_include_id"] = str(svg_include_id).lower()
            params["svg_simplify_stroke"] = str(svg_simplify_stroke).lower()
        if use_absolute_bounds:
            params["use_absolute_bounds"] = "true"
        if version:
            params["version"] = version
        resp = await self._request(
            "GET", f"/v1/images/{file_key}", params=params,
        )
        data = resp.json()
        if data.get("err"):
            raise FigmaError(f"image render error: {data['err']}")
        return data

    async def download(self, url: str) -> bytes:
        """Fetch a presigned image URL (S3) without the Figma token header.

        URL is validated to point at figma.com or one of Figma's documented
        S3 buckets; redirects are not followed (a 30x is treated as an
        error rather than chased into an attacker-controlled host)."""
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.hostname:
            raise FigmaError(f"download URL has no host: {url[:80]}…")
        if parsed.scheme not in ("http", "https"):
            raise FigmaError(
                f"download URL must be http(s), got {parsed.scheme!r}"
            )
        host = parsed.hostname
        if not _is_allowed_download_host(host):
            raise FigmaError(
                f"download URL host {host!r} is not in the allow-list; "
                "render endpoint should return figma.com or a "
                "Figma-owned S3 bucket URL."
            )
        resp = await self._download_client.get(url)
        if 300 <= resp.status_code < 400:
            raise FigmaError(
                f"image download got {resp.status_code} redirect to "
                f"{resp.headers.get('Location', '?')[:80]}… "
                "(redirects are not followed)"
            )
        if resp.status_code >= 400:
            raise FigmaError(
                f"image download failed ({resp.status_code}) for {url[:80]}…"
            )
        return resp.content

    # --- comments ----------------------------------------------------------

    async def list_comments(self, file_key: str) -> dict:
        """GET /v1/files/:key/comments."""
        resp = await self._request(
            "GET", f"/v1/files/{file_key}/comments",
        )
        return resp.json()

    async def post_comment(
        self,
        file_key: str,
        *,
        message: str,
        client_meta: Mapping[str, Any] | None = None,
        comment_id: str | None = None,
    ) -> dict:
        """POST /v1/files/:key/comments.

        ``client_meta`` pins the comment to a node or absolute canvas
        coordinate. ``comment_id`` makes this a reply to an existing
        thread.
        """
        body: dict[str, Any] = {"message": message}
        if client_meta is not None:
            body["client_meta"] = dict(client_meta)
        if comment_id is not None:
            body["comment_id"] = comment_id
        resp = await self._request(
            "POST", f"/v1/files/{file_key}/comments", json_body=body,
        )
        return resp.json()

    # --- variables (Enterprise typically) ----------------------------------

    async def get_variables_local(self, file_key: str) -> dict:
        """GET /v1/files/:key/variables/local.

        Returns local variables + remote variables used in the file.
        Requires ``file_variables:read`` scope (typically Enterprise).
        """
        resp = await self._request(
            "GET", f"/v1/files/{file_key}/variables/local",
        )
        return resp.json()

    async def get_variables_published(self, file_key: str) -> dict:
        """GET /v1/files/:key/variables/published.

        Returns variables published from this file.
        Requires ``file_variables:read`` scope (typically Enterprise).
        """
        resp = await self._request(
            "GET", f"/v1/files/{file_key}/variables/published",
        )
        return resp.json()

    # --- dev resources (Dev Mode typically) --------------------------------

    async def list_dev_resources(self, file_key: str) -> dict:
        """GET /v1/files/:key/dev_resources.

        Returns dev resources attached to nodes in the file.
        Requires ``file_dev_resources:read`` scope (typically Dev Mode).
        """
        resp = await self._request(
            "GET", f"/v1/files/{file_key}/dev_resources",
        )
        return resp.json()

    # --- raw escape hatch --------------------------------------------------

    async def raw(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any | None = None,
    ) -> Any:
        """Arbitrary request. ``path`` may be absolute (``/v1/foo``) or
        relative (``foo`` → ``/v1/foo``).

        Refuses scheme-relative or full URLs — under RFC 3986 reference
        resolution, ``//evil.example.com/exfil`` would otherwise be
        resolved against ``base_url`` and sent the ``X-Figma-Token``
        header to the named host.
        """
        if "://" in path or path.startswith("//"):
            raise FigmaError(
                f"raw path must be a Figma API path "
                f"(e.g. /v1/files/KEY or files/KEY), not an absolute or "
                f"scheme-relative URL: {path!r}"
            )
        if not path.startswith("/"):
            path = f"/v1/{path}"
        resp = await self._request(method, path, params=params, json_body=json_body)
        if not resp.content:
            return None
        ctype = resp.headers.get("content-type", "")
        if "json" in ctype:
            return resp.json()
        return resp.text


def load_credentials() -> Credentials:
    """Resolve Figma credentials through the ``agentbundle.credentials``
    loader (Tier 1 env → Tier 2 OS keyring → Tier 3 dotfile).

    Namespace: ``figma``. Required key: ``API_TOKEN``.

    Env-var shape: ``<NAMESPACE>_<KEY>`` — ``FIGMA_API_TOKEN``.

    Token bytes never traverse this function's return path other than
    through the ``Credentials`` dataclass into ``FigmaClient.__init__``.
    Schema lives at ``references/creds-schema.toml`` — the
    ``agentbundle creds setup figma`` flow walks it interactively.
    """
    from agentbundle.credentials import (
        CredentialsMissingError,
        load_credentials as _agentbundle_load,
    )

    try:
        creds = _agentbundle_load("figma", required_keys=["API_TOKEN"])
    except CredentialsMissingError as exc:
        raise AuthError(str(exc)) from exc

    return Credentials(token=creds.API_TOKEN)
