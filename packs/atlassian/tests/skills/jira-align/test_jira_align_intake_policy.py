"""Credentialed-request boundary tests for read-only Jira Align intake."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path

import httpx
import pytest

SKILL_ROOT = Path(__file__).resolve().parents[3] / ".apm/skills/jira-align"
PROFILE = (
    SKILL_ROOT.parent
    / "jira-align-brief-intake/references/intake-profile.json"
)


def _load_client():
    path = SKILL_ROOT / "scripts/_client.py"
    spec = importlib.util.spec_from_file_location("jira_align_intake_client", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _public_resolver(host: str, port: int, **_kwargs):
    assert host == "portfolio-tracker.example.test"
    return [(None, None, None, None, ("93.184.216.34", port))]


@pytest.fixture(autouse=True)
def _isolate_proxy_environment(monkeypatch) -> None:
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.delenv("https_proxy", raising=False)


def test_policy_binds_redirect_and_method_controls(monkeypatch) -> None:
    client_module = _load_client()
    with pytest.raises(client_module.AuthError):
        client_module.IntakeRequestPolicy.from_profile(
            PROFILE, "http://portfolio-tracker.example.test", resolver=_public_resolver
        )

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
        PROFILE, "https://portfolio-tracker.example.test", resolver=_public_resolver
    )
    credentials = client_module.Credentials(
        base_url="https://portfolio-tracker.example.test",
        token="fixture",
        flavor="onprem",
    )

    async def exercise() -> None:
        async with client_module.JiraAlignClient(
            credentials,
            intake_policy=policy,
        ) as client:
            assert client._client.follow_redirects is False
            with pytest.raises(client_module.JiraAlignError, match="redirect"):
                await client._request("GET", "/rest/align/api/2/features/1")
            with pytest.raises(client_module.JiraAlignError, match="read-only"):
                await client._request("PATCH", "/rest/align/api/2/features/1")

    asyncio.run(exercise())
    assert len(seen) == 1


def test_policy_rechecks_dns_before_each_request(monkeypatch) -> None:
    client_module = _load_client()
    calls = 0
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={}, request=request)
    )
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        client_module.httpx,
        "AsyncClient",
        lambda *args, **kwargs: real_client(
            *args, **{**kwargs, "transport": transport}
        ),
    )

    def resolver(host: str, port: int, **_kwargs):
        nonlocal calls
        calls += 1
        address = "93.184.216.34" if calls <= 4 else "93.184.216.35"
        return [(None, None, None, None, (address, port))]

    policy = client_module.IntakeRequestPolicy.from_profile(
        PROFILE, "https://portfolio-tracker.example.test", resolver=resolver
    )
    credentials = client_module.Credentials(
        base_url="https://portfolio-tracker.example.test",
        token="fixture",
        flavor="onprem",
    )

    async def exercise() -> None:
        async with client_module.JiraAlignClient(
            credentials,
            intake_policy=policy,
        ) as client:
            with pytest.raises(client_module.AuthError, match="changed"):
                await client._request("GET", "/rest/align/api/2/features/1")

    asyncio.run(exercise())


def test_socket_backend_connects_to_pinned_address() -> None:
    client_module = _load_client()
    policy = client_module.IntakeRequestPolicy.from_profile(
        PROFILE,
        "https://portfolio-tracker.example.test",
        resolver=_public_resolver,
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
    asyncio.run(backend.connect_tcp("portfolio-tracker.example.test", 443))
    assert connected == [("93.184.216.34", 443)]


def test_https_proxy_and_no_proxy_are_honored_and_proxy_socket_is_pinned(
    monkeypatch,
) -> None:
    client_module = _load_client()

    def resolver(host: str, port: int, **_kwargs):
        address = "93.184.216.35" if host == "proxy.example" else "93.184.216.34"
        return [(None, None, None, None, (address, port))]

    policy = client_module.IntakeRequestPolicy.from_profile(
        PROFILE,
        "https://portfolio-tracker.example.test",
        resolver=resolver,
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
