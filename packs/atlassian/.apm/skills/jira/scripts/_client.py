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

import asyncio
import base64
import json
import logging
import os
import secrets
import ssl
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, AsyncIterator, Mapping
from urllib.parse import urlparse

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
class Credentials:
    base_url: str
    token: str
    flavor: str          # "cloud" or "server"
    email: str | None    # required for cloud (Basic auth username), unused on server


def detect_flavor(base_url: str) -> str:
    host = (urlparse(base_url).hostname or "").lower()
    if (
        host.endswith(".atlassian.net")
        or host.endswith(".jira.com")
        or host.endswith(".jira-dev.com")
    ):
        return FLAVOR_CLOUD
    return FLAVOR_SERVER


def _api_prefix(flavor: str) -> str:
    return "/rest/api/3" if flavor == FLAVOR_CLOUD else "/rest/api/2"


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
    ) -> None:
        base_url = credentials.base_url
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")

        self._base = base_url.rstrip("/")
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
                f"{credentials.email}:{credentials.token}".encode("utf-8")
            ).decode("ascii")
            auth_header = f"Basic {basic}"
        else:
            auth_header = f"Bearer {credentials.token}"

        headers = {
            "Accept": "application/json",
            "User-Agent": "atlassian-jira/0.1",
            "Authorization": auth_header,
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

    @classmethod
    def from_sso_cookies(
        cls,
        sso_config: "SsoConfig",
        *,
        concurrency: int = DEFAULT_CONCURRENCY,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> "JiraClient":
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
        parsed = urlparse(base_url)
        # Defense-in-depth https guard at construction: the cookie jar is a
        # bearer secret, so the token path's http:// tolerance must not extend
        # here, even though the config layer already rejects a non-https URL.
        if parsed.scheme != "https":
            raise AuthError(
                "SSO-cookie base_url must be https (the session cookie is a bearer secret)"
            )
        host = parsed.hostname or ""
        # Send-host confinement + fail-closed jar resolution. Both
        # credbroker fail-closed paths re-raise as AuthError so the skill surfaces
        # them as a single user-action (the remediation text is preserved).
        try:
            credbroker.require_host_in_cookie_domains(host, sso_config.cookie_domains)
            jar_path = credbroker.load_sso_cookies(sso_config.profile)
        except credbroker.SsoError as exc:
            raise AuthError(str(exc)) from exc

        # Confine the deliberately over-broad captured jar to the declared domains
        # before attaching it; the result is never written back.
        raw_cookies = json.loads(jar_path.read_text(encoding="utf-8"))
        confined = credbroker.filter_jar_to_domains(
            raw_cookies, sso_config.cookie_domains
        )

        self = cls.__new__(cls)
        self._base = base_url.rstrip("/")
        self._flavor = FLAVOR_SERVER  # DC only — Cloud cookie auth is out of scope
        self._api = _api_prefix(self._flavor)
        self._auth_mode = "sso-cookie"
        self._profile = sso_config.profile

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
        self._client = httpx.AsyncClient(
            base_url=self._base,
            headers=headers,
            cookies=cookies,
            timeout=timeout_s,
            verify=_sso_ssl_context(),
            trust_env=True,  # corporate proxy + SSL_CERT_FILE/SSL_CERT_DIR
            follow_redirects=False,  # never re-attach the cookie cross-host
        )
        self._sem = asyncio.Semaphore(concurrency)
        return self

    async def __aenter__(self) -> "JiraClient":
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

        async with self._sem:
            last_exc: Exception | None = None
            last_status: int | None = None
            for attempt in range(MAX_RETRIES):
                try:
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
                    await asyncio.sleep(self._backoff(attempt))
                    continue

                if resp.status_code == 401:
                    if self._auth_mode == "sso-cookie":
                        # Stop using the known-stale jar — no further
                        # cookie-bearing request with this session. The
                        # remediation names the profile, never the cookie bytes.
                        self._client.cookies.clear()
                        raise AuthError(
                            f"401 Unauthorized — SSO session expired; run "
                            f"'sso-broker register {self._profile}' to re-authenticate"
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
                    raise AuthError(
                        f"SSO session may have expired (HTTP {resp.status_code} "
                        f"redirect, not followed); run 'sso-broker register "
                        f"{self._profile}' to re-authenticate"
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
                f"Exhausted {MAX_RETRIES} retries for {path}{suffix}"
            )

    @staticmethod
    def _backoff(attempt: int) -> float:
        # SystemRandom for the jitter so security scanners don't flag the
        # PRNG; value is not security-sensitive.
        return min(30.0, (2 ** attempt) * 0.5 + secrets.SystemRandom().uniform(0, 0.5))

    # --- identity / health -------------------------------------------------

    async def whoami(self) -> dict:
        """Return the authenticated user record.

        Cloud: GET /rest/api/3/myself.
        Server: GET /rest/api/2/myself (same path under the v2 prefix).
        """
        resp = await self._request("GET", f"{self._api}/myself")
        data = resp.json()
        return data if isinstance(data, dict) else {"value": data}

    async def server_info(self) -> dict:
        resp = await self._request("GET", f"{self._api}/serverInfo")
        return resp.json()

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
        return resp.json()

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
        return resp.json()

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
        data = resp.json()
        return data.get("transitions", []) if isinstance(data, dict) else []

    async def transition_issue(
        self,
        issue_key: str,
        *,
        transition_id: str | None = None,
        transition_name: str | None = None,
        fields: Mapping[str, Any] | None = None,
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
        )

    async def add_comment(self, issue_key: str, body_text: str) -> dict:
        if self._flavor == FLAVOR_CLOUD:
            payload = {"body": _adf_paragraph(body_text)}
        else:
            payload = {"body": body_text}
        resp = await self._request(
            "POST",
            f"{self._api}/issue/{issue_key}/comment",
            json_body=payload,
        )
        return resp.json() if resp.content else {}

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
        data = resp.json()
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
                    "POST", f"{self._api}/search/jql", json_body=body
                )
                data = resp.json()
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
                data = resp.json()
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
        return resp.json()

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
            data = resp.json()
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
        return resp.json()

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
            data = resp.json()
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
            return resp.json()
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
