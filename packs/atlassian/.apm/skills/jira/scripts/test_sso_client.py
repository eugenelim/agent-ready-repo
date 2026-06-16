"""jira cookie-path client — mock-transport security contract (spec task T5).

Covers AC4/AC5 (cookie confinement on the outbound request), AC6 (send-host +
https guard at construction), AC7 (no Authorization header), AC8 (CA-bundle
precedence), AC9 (GET/HEAD allowlist incl. raw("POST")), AC10 (jar not rewritten),
AC11 (401 remediation, no cookie in error), AC13 (token path unchanged), AC20
(follow_redirects=False — off-domain 302 leaks no cookie).

All HTTP assertions are made on the *outbound request* via httpx.MockTransport,
not on internal client attributes.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

import _client
from _sso_config import SsoConfig

pytest.importorskip("credbroker")
import credbroker  # noqa: E402

JAR_COOKIES = [
    {"name": "JSESSIONID", "domain": "jira.corp.example.com", "value": "sess1", "path": "/"},
    {"name": "crowd.token_key", "domain": ".corp.example.com", "value": "tok1", "path": "/"},
    {"name": "_ga", "domain": ".doubleclick.net", "value": "analytics", "path": "/"},
    {"name": "near", "domain": "evil-corp.example.com", "value": "nearmiss", "path": "/"},
]

SSO = SsoConfig(
    profile="jira",
    base_url="https://jira.corp.example.com",
    login_url="https://sso.corp.example.com/login",
    success_url_pattern="https://jira.corp.example.com/secure/Dashboard.jspa",
    cookie_domains=("corp.example.com",),
    validation_endpoint="/rest/api/2/myself",
)


@pytest.fixture()
def broker_jar(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fake sso-broker that prints a real jar file's path; point Path.home() at it."""
    home = tmp_path
    bin_dir = home / ".agentbundle" / "bin"
    bin_dir.mkdir(parents=True)
    jar = home / "session.jar"
    jar.write_text(json.dumps(JAR_COOKIES), encoding="utf-8")
    (bin_dir / "sso-broker.py").write_text(
        "import sys\n" f"sys.stdout.write({str(jar)!r} + '\\n')\n" "sys.exit(0)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(credbroker._sso.Path, "home", staticmethod(lambda: home))
    return jar


def _cookie_client(monkeypatch, handler, sso: SsoConfig = SSO) -> _client.JiraClient:
    """Build a cookie-path JiraClient whose httpx client uses *handler* as transport."""
    mock = httpx.MockTransport(handler)
    real = httpx.AsyncClient
    monkeypatch.setattr(
        _client.httpx,
        "AsyncClient",
        lambda *a, **k: real(*a, **{**k, "transport": mock}),
    )
    return _client.JiraClient.from_sso_cookies(sso)


# --- AC7 / AC4 / AC5: no Authorization, confined cookies on the outbound request

def test_no_authorization_header_and_confined_cookies(broker_jar, monkeypatch):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"name": "me"})

    async def go():
        async with _cookie_client(monkeypatch, handler) as client:
            await client.whoami()

    asyncio.run(go())
    req = seen[0]
    assert "authorization" not in {k.lower() for k in req.headers}  # AC7
    cookie = req.headers.get("cookie", "")
    assert "JSESSIONID=sess1" in cookie  # in-domain (subdomain) kept
    assert "crowd.token_key=tok1" in cookie  # in-domain (dotted) kept
    assert "_ga" not in cookie and "near" not in cookie  # AC4/AC5 over-broad dropped


# --- AC9: GET/HEAD allowlist refuses writes (incl. raw("POST")) before the wire

@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
def test_writes_refused_records_zero_requests(broker_jar, monkeypatch, method):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200)

    async def go():
        async with _cookie_client(monkeypatch, handler) as client:
            with pytest.raises(_client.JiraError, match="writes over SSO-cookie auth"):
                await client.raw(method, "/rest/api/2/issue", json_body={})

    asyncio.run(go())
    assert seen == []  # nothing reached the wire


# --- AC9 accept arm: raw("GET") reaches the wire with confined cookies, no auth

def test_raw_get_reaches_wire_with_confined_cookies(broker_jar, monkeypatch):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    async def go():
        async with _cookie_client(monkeypatch, handler) as client:
            await client.raw("GET", "/rest/api/2/myself")

    asyncio.run(go())
    req = seen[0]
    assert req.method == "GET"
    assert "authorization" not in {k.lower() for k in req.headers}
    assert "JSESSIONID=sess1" in req.headers.get("cookie", "")


# --- AC20: follow_redirects=False — an off-domain 302 leaks no cookie

def test_off_domain_redirect_not_followed(broker_jar, monkeypatch):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(302, headers={"Location": "https://evil.example.net/steal"})

    async def go():
        async with _cookie_client(monkeypatch, handler) as client:
            with pytest.raises(_client.AuthError):
                await client.whoami()

    asyncio.run(go())
    # Exactly one request — to the permitted host — and no follow to the off-domain
    # target (which would re-attach the session cookie).
    assert len(seen) == 1
    assert seen[0].url.host == "jira.corp.example.com"


# --- AC11: 401 surfaces the re-register remediation; no cookie value in the error

def test_401_surfaces_reregister_without_cookie_value(broker_jar, monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401)

    async def go():
        async with _cookie_client(monkeypatch, handler) as client:
            with pytest.raises(_client.AuthError) as exc:
                await client.whoami()
            return str(exc.value)

    msg = asyncio.run(go())
    assert "sso-broker register jira" in msg
    assert "sess1" not in msg and "tok1" not in msg  # no cookie bytes in the error


# --- AC6: send-host + https guards fail closed at construction

def test_base_host_outside_cookie_domains_fails_closed(broker_jar, monkeypatch):
    bad = replace(SSO, base_url="https://jira.evil.net")
    with pytest.raises(_client.AuthError):
        _cookie_client(monkeypatch, lambda r: httpx.Response(200), bad)


def test_non_https_base_url_fails_closed(broker_jar, monkeypatch):
    bad = replace(SSO, base_url="http://jira.corp.example.com")
    with pytest.raises(_client.AuthError, match="must be https"):
        _cookie_client(monkeypatch, lambda r: httpx.Response(200), bad)


# --- AC10: the broker jar file is read, never rewritten

def test_jar_not_rewritten(broker_jar, monkeypatch):
    before = broker_jar.read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"name": "me"})

    async def go():
        async with _cookie_client(monkeypatch, handler) as client:
            await client.whoami()

    asyncio.run(go())
    assert broker_jar.read_bytes() == before


# --- AC8: CA-bundle precedence + trust-store wiring

def test_ca_bundle_precedence(monkeypatch):
    monkeypatch.setenv("SSL_CERT_FILE", "/etc/ssl/sslcert.pem")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/etc/ssl/requests.pem")
    monkeypatch.setenv("SSL_CERT_DIR", "/etc/ssl/dir")
    cafile, capath = _client._sso_cafile_capath()
    assert cafile == "/etc/ssl/sslcert.pem"  # SSL_CERT_FILE wins
    assert capath == "/etc/ssl/dir"

    monkeypatch.delenv("SSL_CERT_FILE")
    cafile, _ = _client._sso_cafile_capath()
    assert cafile == "/etc/ssl/requests.pem"  # falls back to REQUESTS_CA_BUNDLE


def test_ssl_context_is_built():
    import ssl

    assert isinstance(_client._sso_ssl_context(), ssl.SSLContext)


# --- AC13: token path is byte-identical (Authorization header, no cookies)

def test_token_path_unchanged(monkeypatch):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"name": "me"})

    mock = httpx.MockTransport(handler)
    real = httpx.AsyncClient
    monkeypatch.setattr(
        _client.httpx, "AsyncClient",
        lambda *a, **k: real(*a, **{**k, "transport": mock}),
    )
    creds = _client.Credentials(
        base_url="https://jira.corp.example.com", token="TOK", flavor="server", email=None
    )

    async def go():
        async with _client.JiraClient(creds) as client:
            await client.whoami()

    asyncio.run(go())
    req = seen[0]
    assert req.headers["authorization"] == "Bearer TOK"
    assert "cookie" not in {k.lower() for k in req.headers}


def test_token_path_follows_redirects(monkeypatch):
    # The token path keeps follow_redirects=True (unchanged); the cookie path
    # deliberately disables it (AC20). Pin the difference: a 302 is followed.
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if len(seen) == 1:
            return httpx.Response(
                302, headers={"Location": "https://jira.corp.example.com/rest/api/2/myself"}
            )
        return httpx.Response(200, json={"name": "me"})

    mock = httpx.MockTransport(handler)
    real = httpx.AsyncClient
    monkeypatch.setattr(
        _client.httpx, "AsyncClient",
        lambda *a, **k: real(*a, **{**k, "transport": mock}),
    )
    creds = _client.Credentials(
        base_url="https://jira.corp.example.com", token="TOK", flavor="server", email=None
    )

    async def go():
        async with _client.JiraClient(creds) as client:
            await client.whoami()

    asyncio.run(go())
    assert len(seen) == 2  # redirect followed on the token path
