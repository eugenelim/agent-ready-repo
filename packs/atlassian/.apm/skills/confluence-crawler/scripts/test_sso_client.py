"""confluence-crawler cookie-path client — mock-transport security contract.

Mirrors the jira cookie-path contract. The GET/HEAD allowlist differs:
confluence-crawler has no raw() escape hatch, so the GET/HEAD allowlist is asserted
directly on the _request chokepoint's method argument.
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
    {"name": "JSESSIONID", "domain": "confluence.corp.example.com", "value": "sess1", "path": "/"},
    {"name": "crowd.token_key", "domain": ".corp.example.com", "value": "tok1", "path": "/"},
    {"name": "_ga", "domain": ".doubleclick.net", "value": "analytics", "path": "/"},
    {"name": "near", "domain": "evil-corp.example.com", "value": "nearmiss", "path": "/"},
]

SSO = SsoConfig(
    profile="confluence",
    base_url="https://confluence.corp.example.com",
    login_url="https://sso.corp.example.com/login",
    success_url_pattern="https://confluence.corp.example.com/dashboard.action",
    cookie_domains=("corp.example.com",),
    validation_endpoint="/rest/api/space",
)


@pytest.fixture()
def broker_jar(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
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


def _cookie_client(monkeypatch, handler, sso: SsoConfig = SSO) -> _client.ConfluenceClient:
    mock = httpx.MockTransport(handler)
    real = httpx.AsyncClient
    monkeypatch.setattr(
        _client.httpx,
        "AsyncClient",
        lambda *a, **k: real(*a, **{**k, "transport": mock}),
    )
    return _client.ConfluenceClient.from_sso_cookies(sso)


def test_no_authorization_header_and_confined_cookies(broker_jar, monkeypatch):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"type": "known"})

    async def go():
        async with _cookie_client(monkeypatch, handler) as client:
            await client.whoami()

    asyncio.run(go())
    req = seen[0]
    assert "authorization" not in {k.lower() for k in req.headers}
    cookie = req.headers.get("cookie", "")
    assert "JSESSIONID=sess1" in cookie and "crowd.token_key=tok1" in cookie
    assert "_ga" not in cookie and "near" not in cookie


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
def test_writes_refused_at_chokepoint(broker_jar, monkeypatch, method):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200)

    async def go():
        async with _cookie_client(monkeypatch, handler) as client:
            with pytest.raises(_client.ConfluenceError, match="writes over SSO-cookie auth"):
                await client._request(method, "/rest/api/content")

    asyncio.run(go())
    assert seen == []


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
    assert len(seen) == 1
    assert seen[0].url.host == "confluence.corp.example.com"


def test_401_surfaces_reregister_without_cookie_value(broker_jar, monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401)

    async def go():
        async with _cookie_client(monkeypatch, handler) as client:
            with pytest.raises(_client.AuthError) as exc:
                await client.whoami()
            return str(exc.value)

    msg = asyncio.run(go())
    assert "sso-broker register confluence" in msg
    assert "sess1" not in msg and "tok1" not in msg


def test_base_host_outside_cookie_domains_fails_closed(broker_jar, monkeypatch):
    bad = replace(SSO, base_url="https://confluence.evil.net")
    with pytest.raises(_client.AuthError):
        _cookie_client(monkeypatch, lambda r: httpx.Response(200), bad)


def test_non_https_base_url_fails_closed(broker_jar, monkeypatch):
    bad = replace(SSO, base_url="http://confluence.corp.example.com")
    with pytest.raises(_client.AuthError, match="must be https"):
        _cookie_client(monkeypatch, lambda r: httpx.Response(200), bad)


def test_jar_not_rewritten(broker_jar, monkeypatch):
    before = broker_jar.read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"type": "known"})

    async def go():
        async with _cookie_client(monkeypatch, handler) as client:
            await client.whoami()

    asyncio.run(go())
    assert broker_jar.read_bytes() == before


def test_ca_bundle_precedence(monkeypatch):
    monkeypatch.setenv("SSL_CERT_FILE", "/etc/ssl/sslcert.pem")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/etc/ssl/requests.pem")
    cafile, _ = _client._sso_cafile_capath()
    assert cafile == "/etc/ssl/sslcert.pem"
    monkeypatch.delenv("SSL_CERT_FILE")
    cafile, _ = _client._sso_cafile_capath()
    assert cafile == "/etc/ssl/requests.pem"


def test_token_path_unchanged(monkeypatch):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"type": "known"})

    mock = httpx.MockTransport(handler)
    real = httpx.AsyncClient
    monkeypatch.setattr(
        _client.httpx, "AsyncClient",
        lambda *a, **k: real(*a, **{**k, "transport": mock}),
    )
    creds = _client.Credentials(
        base_url="https://confluence.corp.example.com", token="TOK", flavor="server", email=None
    )

    async def go():
        async with _client.ConfluenceClient(creds) as client:
            await client.whoami()

    asyncio.run(go())
    req = seen[0]
    assert req.headers["authorization"] == "Bearer TOK"
    assert "cookie" not in {k.lower() for k in req.headers}


def test_token_path_follows_redirects(monkeypatch):
    # Token path keeps follow_redirects=True; cookie path disables it.
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if len(seen) == 1:
            return httpx.Response(
                302,
                headers={"Location": "https://confluence.corp.example.com/rest/api/user/current"},
            )
        return httpx.Response(200, json={"type": "known"})

    mock = httpx.MockTransport(handler)
    real = httpx.AsyncClient
    monkeypatch.setattr(
        _client.httpx, "AsyncClient",
        lambda *a, **k: real(*a, **{**k, "transport": mock}),
    )
    creds = _client.Credentials(
        base_url="https://confluence.corp.example.com", token="TOK", flavor="server", email=None
    )

    async def go():
        async with _client.ConfluenceClient(creds) as client:
            await client.whoami()

    asyncio.run(go())
    assert len(seen) == 2  # redirect followed on the token path
