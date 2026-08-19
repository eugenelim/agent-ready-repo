"""Credentialed-request boundary tests for read-only Jira intake."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import httpx
import pytest

SKILL_ROOT = Path(__file__).resolve().parents[3] / ".apm/skills/jira"
PROFILE = SKILL_ROOT.parent / "jira-brief-intake/references/intake-profile.json"


def _load_client():
    path = SKILL_ROOT / "scripts/_client.py"
    spec = importlib.util.spec_from_file_location("jira_intake_client", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _public_resolver(host: str, port: int, **_kwargs):
    assert host == "tracker.example.test"
    return [(None, None, None, None, ("93.184.216.34", port))]


@pytest.fixture(autouse=True)
def _isolate_proxy_environment(monkeypatch) -> None:
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.delenv("https_proxy", raising=False)


def test_policy_rejects_scheme_host_and_credential_mismatch() -> None:
    client_module = _load_client()
    with pytest.raises(client_module.AuthError):
        client_module.IntakeRequestPolicy.from_profile(
            PROFILE, "http://tracker.example.test", resolver=_public_resolver
        )
    with pytest.raises(client_module.AuthError):
        client_module.IntakeRequestPolicy.from_profile(
            PROFILE, "https://untrusted.example.test", resolver=_public_resolver
        )

    policy = client_module.IntakeRequestPolicy.from_profile(
        PROFILE, "https://tracker.example.test", resolver=_public_resolver
    )
    credentials = client_module.Credentials(
        base_url="https://different.example.test",
        token="fixture",
        flavor="server",
        email=None,
    )
    with pytest.raises(client_module.AuthError):
        client_module.JiraClient(credentials, intake_policy=policy)


def test_policy_disables_redirects_and_refuses_writes(monkeypatch) -> None:
    client_module = _load_client()
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(302, headers={"Location": "https://example.test/"})

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        client_module.httpx,
        "AsyncClient",
        lambda *args, **kwargs: real_client(
            *args, **{**kwargs, "transport": transport}
        ),
    )
    policy = client_module.IntakeRequestPolicy.from_profile(
        PROFILE, "https://tracker.example.test", resolver=_public_resolver
    )
    credentials = client_module.Credentials(
        base_url="https://tracker.example.test",
        token="fixture",
        flavor="server",
        email=None,
    )

    async def exercise() -> None:
        async with client_module.JiraClient(
            credentials,
            intake_policy=policy,
        ) as client:
            assert client._client.follow_redirects is False
            with pytest.raises(client_module.JiraError, match="redirect"):
                await client._request("GET", "/rest/api/2/issue/EX-1")
            with pytest.raises(client_module.JiraError, match="read-only"):
                await client._request("POST", "/rest/api/2/issue")

    asyncio.run(exercise())
    assert len(seen) == 1


def test_guarded_write_policy_sends_once_without_retry(monkeypatch) -> None:
    client_module = _load_client()
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(503, request=request)

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        client_module.httpx,
        "AsyncClient",
        lambda *args, **kwargs: real_client(
            *args, **{**kwargs, "transport": transport}
        ),
    )
    policy = client_module.IntakeRequestPolicy.from_profile(
        PROFILE,
        "https://tracker.example.test",
        resolver=_public_resolver,
        allow_write=True,
    )
    credentials = client_module.Credentials(
        base_url="https://tracker.example.test",
        token="fixture",
        flavor="server",
        email=None,
    )

    async def exercise() -> None:
        async with client_module.JiraClient(
            credentials,
            intake_policy=policy,
        ) as client:
            with pytest.raises(client_module.JiraError, match="Exhausted 1 attempts"):
                await client._request(
                    "POST", "/rest/api/2/issue/EX-1/comment", guarded_write=True
                )

    asyncio.run(exercise())
    assert len(seen) == 1


def test_cloud_jql_search_retries_rate_limit_even_though_it_uses_post(monkeypatch) -> None:
    """Cloud's read-only JQL endpoint is POST but remains safe to retry."""
    client_module = _load_client()
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if len(seen) == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, request=request)
        return httpx.Response(
            200,
            json={"issues": [{"key": "EX-1"}], "isLast": True},
            request=request,
        )

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        client_module.httpx,
        "AsyncClient",
        lambda *args, **kwargs: real_client(*args, **{**kwargs, "transport": transport}),
    )

    async def no_sleep(_delay: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    policy = client_module.IntakeRequestPolicy.from_profile(
        PROFILE, "https://tracker.example.test", resolver=_public_resolver
    )
    credentials = client_module.Credentials(
        base_url="https://tracker.example.test",
        token="fixture",
        flavor="cloud",
        email="user@example.test",
    )

    async def exercise() -> list[dict]:
        async with client_module.JiraClient(credentials, intake_policy=policy) as client:
            return [issue async for issue in client.iter_search("project = EX")]

    assert asyncio.run(exercise()) == [{"key": "EX-1"}]
    assert len(seen) == 2
    assert all(request.method == "POST" for request in seen)


@pytest.mark.parametrize(
    ("method", "idempotent"),
    [("GET", None), ("POST", True)],
)
def test_read_only_policy_permits_explicit_read_intent(
    monkeypatch, method: str, idempotent: bool | None
) -> None:
    """GET/HEAD defaults and trusted idempotent POSTs share one read rule."""
    client_module = _load_client()
    seen: list[httpx.Request] = []
    transport = httpx.MockTransport(
        lambda request: seen.append(request) or httpx.Response(200, request=request)
    )
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        client_module.httpx,
        "AsyncClient",
        lambda *args, **kwargs: real_client(*args, **{**kwargs, "transport": transport}),
    )
    policy = client_module.IntakeRequestPolicy.from_profile(
        PROFILE, "https://tracker.example.test", resolver=_public_resolver
    )
    credentials = client_module.Credentials(
        base_url="https://tracker.example.test",
        token="fixture",
        flavor="server",
        email=None,
    )

    async def exercise() -> None:
        async with client_module.JiraClient(credentials, intake_policy=policy) as client:
            response = await client._request(
                method, "/rest/api/2/issue/EX-1", idempotent=idempotent
            )
            assert response.status_code == 200

    asyncio.run(exercise())
    assert [request.method for request in seen] == [method]


def test_existing_token_write_retries_transient_failure(monkeypatch) -> None:
    client_module = _load_client()
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if len(seen) == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, request=request)
        return httpx.Response(201, json={"id": "1"}, request=request)

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        client_module.httpx,
        "AsyncClient",
        lambda *args, **kwargs: real_client(*args, **{**kwargs, "transport": transport}),
    )

    async def no_sleep(_delay: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    policy = client_module.IntakeRequestPolicy.from_profile(
        PROFILE,
        "https://tracker.example.test",
        resolver=_public_resolver,
        allow_write=True,
    )
    credentials = client_module.Credentials(
        base_url="https://tracker.example.test",
        token="fixture",
        flavor="cloud",
        email="user@example.test",
    )

    async def exercise() -> None:
        async with client_module.JiraClient(credentials, intake_policy=policy) as client:
            await client.add_comment("EX-1", "Reviewed")

    asyncio.run(exercise())
    assert len(seen) == 2
    assert all(request.method == "POST" for request in seen)


def test_read_only_policy_refuses_non_idempotent_post(monkeypatch) -> None:
    """The Cloud-search exception does not authorize general POST requests."""
    client_module = _load_client()
    seen: list[httpx.Request] = []
    transport = httpx.MockTransport(
        lambda request: seen.append(request) or httpx.Response(200, request=request)
    )
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        client_module.httpx,
        "AsyncClient",
        lambda *args, **kwargs: real_client(*args, **{**kwargs, "transport": transport}),
    )
    policy = client_module.IntakeRequestPolicy.from_profile(
        PROFILE, "https://tracker.example.test", resolver=_public_resolver
    )
    credentials = client_module.Credentials(
        base_url="https://tracker.example.test",
        token="fixture",
        flavor="server",
        email=None,
    )

    async def exercise() -> None:
        async with client_module.JiraClient(credentials, intake_policy=policy) as client:
            with pytest.raises(client_module.JiraError, match="read-only"):
                await client._request("POST", "/rest/api/2/issue/EX-1/comment")

    asyncio.run(exercise())
    assert seen == []


def test_policy_enforces_response_bytes(tmp_path, monkeypatch) -> None:
    client_module = _load_client()
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    profile["budget"]["max_bytes"] = 2
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"too large", request=request)
    )
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        client_module.httpx,
        "AsyncClient",
        lambda *args, **kwargs: real_client(
            *args, **{**kwargs, "transport": transport}
        ),
    )
    policy = client_module.IntakeRequestPolicy.from_profile(
        profile_path, "https://tracker.example.test", resolver=_public_resolver
    )
    credentials = client_module.Credentials(
        base_url="https://tracker.example.test",
        token="fixture",
        flavor="server",
        email=None,
    )

    async def exercise() -> None:
        async with client_module.JiraClient(
            credentials,
            intake_policy=policy,
        ) as client:
            with pytest.raises(client_module.JiraError, match="byte budget"):
                await client._request("GET", "/rest/api/2/issue/EX-1")

    asyncio.run(exercise())


def test_socket_backend_connects_to_pinned_address() -> None:
    client_module = _load_client()
    policy = client_module.IntakeRequestPolicy.from_profile(
        PROFILE, "https://tracker.example.test", resolver=_public_resolver
    )
    backend = client_module._PinnedAsyncNetworkBackend(policy)
    connected: list[tuple[str, int]] = []

    class FakeBackend:
        async def connect_tcp(
            self, host: str, port: int, *_args: object, **_kwargs: object
        ) -> object:
            connected.append((host, port))
            return object()

    backend._backend = FakeBackend()
    asyncio.run(backend.connect_tcp("tracker.example.test", 443))
    assert connected == [("93.184.216.34", 443)]


def test_https_proxy_and_no_proxy_are_honored_and_proxy_socket_is_pinned(
    monkeypatch,
) -> None:
    client_module = _load_client()

    def resolver(host: str, port: int, **_kwargs):
        address = "93.184.216.35" if host == "proxy.example" else "93.184.216.34"
        return [(None, None, None, None, (address, port))]

    policy = client_module.IntakeRequestPolicy.from_profile(
        PROFILE, "https://tracker.example.test", resolver=resolver
    )
    monkeypatch.setenv("HTTPS_PROXY", "https://proxy.example:8443")
    monkeypatch.setattr(client_module, "proxy_bypass", lambda _host: False)
    proxy_url, proxy_pin = client_module._https_proxy_settings(policy)
    assert proxy_url == "https://proxy.example:8443"
    assert proxy_pin == ("proxy.example", 8443, frozenset({"93.184.216.35"}))

    backend = client_module._PinnedAsyncNetworkBackend(policy, proxy_pin)
    connected: list[tuple[str, int]] = []

    class FakeBackend:
        async def connect_tcp(
            self, host: str, port: int, *_args: object, **_kwargs: object
        ) -> object:
            connected.append((host, port))
            return object()

    backend._backend = FakeBackend()
    asyncio.run(backend.connect_tcp("proxy.example", 8443))
    assert connected == [("93.184.216.35", 8443)]

    monkeypatch.setattr(client_module, "proxy_bypass", lambda _host: True)
    assert client_module._https_proxy_settings(policy) == (None, None)
