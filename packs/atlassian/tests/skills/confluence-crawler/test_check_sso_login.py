"""Confluence ``--check`` SSO auto-recovery and its exact blast radius.

Every CredBroker, browser, credential, and HTTP behavior is stubbed. The suite
never reads a real profile, starts a browser, or reaches a network endpoint.
"""

from __future__ import annotations

import asyncio
import importlib
import json
import sys
from pathlib import Path
from types import ModuleType

import httpx
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[5]
_SKILL_ROOT = _REPO_ROOT / "packs/atlassian/.apm/skills/confluence-crawler"
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

pytest.importorskip("credbroker")

import credbroker  # noqa: E402
import scripts._client as _client  # noqa: E402
import scripts._sso_config as _sso_config  # noqa: E402
import scripts.crawl_space as crawl_space  # noqa: E402
from scripts._sso_config import SsoConfig  # noqa: E402

SSO = SsoConfig(
    profile="confluence",
    base_url="https://confluence.corp.example.com",
    login_url="https://sso.corp.example.com/login",
    success_url_pattern="https://confluence.corp.example.com/dashboard.action",
    cookie_domains=("corp.example.com",),
    validation_endpoint="/rest/api/user/current",
)


def _run(coro):
    return asyncio.run(coro)


class _Broker:
    """CredBroker surface used by the automatic path, with no browser verb."""

    SsoError = credbroker.SsoError
    SsoProfileNotRegisteredError = credbroker.SsoProfileNotRegisteredError
    SsoInteractionRequiredError = credbroker.SsoInteractionRequiredError

    def __init__(self) -> None:
        self.refresh_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
        self.refresh_error: Exception | None = None
        self.register_calls: list[object] = []

    def refresh_sso_session(self, *args: object, **kwargs: object) -> None:
        self.refresh_calls.append((args, kwargs))
        if self.refresh_error is not None:
            raise self.refresh_error


class _FakeClient:
    def __init__(self, responses: list[object], state: dict[str, object]) -> None:
        self._responses = responses
        self._state = state

    async def whoami(self) -> dict:
        self._state["probe_count"] = int(self._state["probe_count"]) + 1
        item = self._responses.pop(0)
        if isinstance(item, BaseException):
            raise item
        assert isinstance(item, dict)
        return item

    async def get_space_homepage_id(self, space: str) -> None:
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc: object) -> None:
        self._state["close_count"] = int(self._state["close_count"]) + 1


def _install_sso_check(
    monkeypatch: pytest.MonkeyPatch,
    responses: list[object],
    *,
    broker: _Broker | None = None,
) -> tuple[_Broker, dict[str, object]]:
    recorder = broker or _Broker()
    state: dict[str, object] = {
        "probe_count": 0,
        "close_count": 0,
        "clients": [],
    }

    def _factory(cls, config: SsoConfig, **kwargs: object) -> _FakeClient:
        client = _FakeClient(responses, state)
        clients = state["clients"]
        assert isinstance(clients, list)
        clients.append(client)
        return client

    monkeypatch.setattr(crawl_space, "_select_auth_path", lambda: ("sso-cookie", SSO))
    monkeypatch.setattr(
        crawl_space,
        "_credbroker_for_sso_check",
        lambda: (recorder, None),
    )
    monkeypatch.setattr(
        crawl_space.ConfluenceClient,
        "from_sso_cookies",
        classmethod(_factory),
    )
    return recorder, state


def _check() -> int:
    return _run(crawl_space.main_async(crawl_space.parse_args(["--check"])))


def test_session_unavailable_is_an_auth_error() -> None:
    assert issubclass(_client.SsoSessionUnavailable, _client.AuthError)


def test_broker_unavailable_signal_is_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        credbroker,
        "require_host_in_cookie_domains",
        lambda host, domains: None,
    )

    def _unavailable(profile: str) -> Path:
        raise credbroker.SsoSessionUnavailableError("unavailable")

    monkeypatch.setattr(credbroker, "load_sso_cookies", _unavailable)
    with pytest.raises(_client.SsoSessionUnavailable):
        _client.ConfluenceClient.from_sso_cookies(SSO)


def test_confinement_failure_remains_plain_auth_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _confined(host: str, domains: tuple[str, ...]) -> None:
        raise credbroker.SsoConfigError("domain mismatch")

    monkeypatch.setattr(credbroker, "require_host_in_cookie_domains", _confined)
    with pytest.raises(_client.AuthError) as exc:
        _client.ConfluenceClient.from_sso_cookies(SSO)
    assert not isinstance(exc.value, _client.SsoSessionUnavailable)


@pytest.mark.parametrize(
    "raw",
    [
        b"{not json",
        b'"wrong shape"',
        b"\xff",
        json.dumps([{"domain": "corp.example.com", "value": "v"}]).encode(),
        json.dumps([{"name": "sid", "domain": 7, "value": "v"}]).encode(),
        json.dumps([{"name": "sid", "domain": "corp.example.com", "value": None}]).encode(),
        json.dumps([
            {
                "name": "sid",
                "domain": "corp.example.com",
                "value": "v",
                "path": 7,
            }
        ]).encode(),
    ],
)
def test_bad_jar_is_typed_before_filter_or_attachment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    raw: bytes,
) -> None:
    jar = tmp_path / "session.jar"
    jar.write_bytes(raw)
    monkeypatch.setattr(
        credbroker,
        "require_host_in_cookie_domains",
        lambda host, domains: None,
    )
    monkeypatch.setattr(credbroker, "load_sso_cookies", lambda profile: jar)
    monkeypatch.setattr(
        credbroker,
        "filter_jar_to_domains",
        lambda *args, **kwargs: pytest.fail("invalid jar reached filtering"),
    )
    monkeypatch.setattr(
        _client.httpx,
        "AsyncClient",
        lambda *args, **kwargs: pytest.fail("invalid jar reached attachment"),
    )

    with pytest.raises(_client.SsoSessionUnavailable) as exc:
        _client.ConfluenceClient.from_sso_cookies(SSO)
    message = str(exc.value)
    assert "confluence" in message
    assert "not json" not in message
    assert "session.jar" not in message
    assert exc.value.__cause__ is not None


def test_unreadable_jar_is_typed_with_bounded_profile_only_diagnostic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_jar = tmp_path / "missing-session.jar"
    monkeypatch.setattr(
        credbroker,
        "require_host_in_cookie_domains",
        lambda host, domains: None,
    )
    monkeypatch.setattr(credbroker, "load_sso_cookies", lambda profile: missing_jar)
    monkeypatch.setattr(
        credbroker,
        "filter_jar_to_domains",
        lambda *args, **kwargs: pytest.fail("unreadable jar reached filtering"),
    )

    with pytest.raises(_client.SsoSessionUnavailable) as exc:
        _client.ConfluenceClient.from_sso_cookies(SSO)
    assert "confluence" in str(exc.value)
    assert "missing-session.jar" not in str(exc.value)
    assert isinstance(exc.value.__cause__, OSError)


@pytest.mark.parametrize("path", [pytest.param(..., id="missing"), None, "/wiki"])
def test_jar_shape_accepts_missing_null_or_string_path(path: object) -> None:
    record: dict[str, object] = {
        "name": "sid",
        "domain": "corp.example.com",
        "value": "v",
    }
    if path is not ...:
        record["path"] = path
    assert _client._validate_jar_shape([record]) is None


def _response_client(handler, *, auth_mode: str = "sso-cookie") -> _client.ConfluenceClient:
    client = _client.ConfluenceClient.__new__(_client.ConfluenceClient)
    client._base = SSO.base_url
    client._flavor = _client.FLAVOR_SERVER
    client._auth_mode = auth_mode
    client._profile = SSO.profile if auth_mode == "sso-cookie" else None
    client._client = httpx.AsyncClient(
        base_url=SSO.base_url,
        transport=httpx.MockTransport(handler),
        follow_redirects=auth_mode != "sso-cookie",
    )
    client._sem = asyncio.Semaphore(1)
    client._min_delay = 0
    client._last_request = 0.0
    client._lock = asyncio.Lock()
    return client


@pytest.mark.parametrize("status", [401, 302])
def test_http_expiry_signals_are_typed(status: int) -> None:
    client = _response_client(lambda request: httpx.Response(status))

    async def _go() -> None:
        try:
            with pytest.raises(_client.SsoSessionUnavailable):
                await client.whoami()
        finally:
            await client.__aexit__(None, None, None)

    _run(_go())


def test_403_is_not_typed() -> None:
    client = _response_client(lambda request: httpx.Response(403))

    async def _go() -> None:
        try:
            with pytest.raises(_client.AuthError) as exc:
                await client.whoami()
            assert not isinstance(exc.value, _client.SsoSessionUnavailable)
        finally:
            await client.__aexit__(None, None, None)

    _run(_go())


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, text="<html>sign in</html>"),
        httpx.Response(200, json={"displayName": None}),
        httpx.Response(200, json={"username": 7}),
    ],
)
def test_unusable_sso_identity_is_typed(response: httpx.Response) -> None:
    client = _response_client(lambda request: response)

    async def _go() -> None:
        try:
            with pytest.raises(_client.SsoSessionUnavailable):
                await client.whoami()
        finally:
            await client.__aexit__(None, None, None)

    _run(_go())


def test_identity_selector_is_exact_and_single_sourced() -> None:
    assert _client.identity_of({"username": "first", "displayName": "second"}) == "first"
    assert _client.identity_of({"displayName": None, "accountId": "abc"}) == "abc"
    assert _client.identity_of({"username": 7}) is None
    assert crawl_space.identity_of is _client.identity_of


def test_token_whoami_response_shape_is_unchanged() -> None:
    client = _response_client(
        lambda request: httpx.Response(200, json={"x": 1}),
        auth_mode="creds",
    )

    async def _go() -> dict:
        try:
            return await client.whoami()
        finally:
            await client.__aexit__(None, None, None)

    assert _run(_go()) == {"x": 1}


def test_healthy_initial_probe_does_not_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    broker, state = _install_sso_check(
        monkeypatch,
        [{"username": "Example User"}],
    )
    assert _check() == crawl_space.EXIT_OK
    assert broker.refresh_calls == []
    assert state["probe_count"] == 1
    assert state["close_count"] == 1


def test_main_async_uses_real_selector_and_sso_client_factory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = tmp_path / "sso-config.toml"
    config.write_text(
        """\
auth_default = "sso-cookie"

[sso]
profile = "confluence"
base_url = "https://confluence.corp.example.com"
login_url = "https://sso.corp.example.com/login"
success_url_pattern = "https://confluence.corp.example.com/dashboard.action"
cookie_domains = ["corp.example.com"]
validation_endpoint = "/rest/api/user/current"
""",
        encoding="utf-8",
    )
    jar = tmp_path / "session.jar"
    cookies = [
        {
            "name": "sid",
            "domain": "confluence.corp.example.com",
            "value": "stub-cookie",
            "path": "/",
        }
    ]
    jar.write_text(json.dumps(cookies), encoding="utf-8")
    broker = _Broker()
    requests: list[httpx.Request] = []
    real_async_client = httpx.AsyncClient

    def _transport(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"username": "Example User"})

    def _http_client(*args: object, **kwargs: object) -> httpx.AsyncClient:
        kwargs.pop("verify", None)
        kwargs.pop("trust_env", None)
        kwargs["transport"] = httpx.MockTransport(_transport)
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr(_sso_config, "_DEFAULT_CONFIG_PATH", config)
    monkeypatch.setattr(
        credbroker,
        "require_host_in_cookie_domains",
        lambda host, domains: None,
    )
    monkeypatch.setattr(credbroker, "load_sso_cookies", lambda profile: jar)
    monkeypatch.setattr(credbroker, "filter_jar_to_domains", lambda raw, domains: raw)
    monkeypatch.setattr(_client.httpx, "AsyncClient", _http_client)
    monkeypatch.setattr(
        crawl_space,
        "_credbroker_for_sso_check",
        lambda: (broker, None),
    )

    assert _check() == crawl_space.EXIT_OK
    assert broker.refresh_calls == []
    assert len(requests) == 1
    assert requests[0].url.path == "/rest/api/user/current"
    assert "authorization" not in requests[0].headers


def test_unavailable_probe_refreshes_once_then_reprobes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    broker, state = _install_sso_check(
        monkeypatch,
        [
            _client.SsoSessionUnavailable("expired"),
            {"username": "Example User"},
        ],
    )

    async def _must_not_run(client, flavor):
        raise AssertionError("SSO probe must call whoami directly")

    monkeypatch.setattr(crawl_space, "_run_check", _must_not_run)
    assert _check() == crawl_space.EXIT_OK
    assert broker.refresh_calls == [(("confluence",), {})]
    assert state["probe_count"] == 2
    assert state["close_count"] == 2
    stderr = capsys.readouterr().err.lower()
    for phrase in (
        "stored sso session is unavailable",
        "headlessly",
        "no browser window will be shown",
        "credbroker's registered profile",
    ):
        assert phrase in stderr
    assert broker.register_calls == []


def test_failed_post_refresh_probe_is_terminal_and_not_retried(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    broker, state = _install_sso_check(
        monkeypatch,
        [
            _client.SsoSessionUnavailable("expired"),
            _client.SsoSessionUnavailable("still expired"),
        ],
    )
    assert _check() == crawl_space.EXIT_USER_ACTION
    assert broker.refresh_calls == [(("confluence",), {})]
    assert state["probe_count"] == 2
    assert state["close_count"] == 2
    stderr = capsys.readouterr().err
    assert "python scripts/setup_sso.py" in stderr
    assert "still expired" not in stderr


def test_never_registered_requests_existing_manual_setup(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    broker = _Broker()
    broker.refresh_error = credbroker.SsoProfileNotRegisteredError("not registered")
    _install_sso_check(
        monkeypatch,
        [_client.SsoSessionUnavailable("expired")],
        broker=broker,
    )
    assert _check() == crawl_space.EXIT_USER_ACTION
    stderr = capsys.readouterr().err
    assert "python scripts/setup_sso.py" in stderr
    assert broker.register_calls == []


def test_interaction_required_says_no_browser_opened(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    broker = _Broker()
    broker.refresh_error = credbroker.SsoInteractionRequiredError("needs a human")
    _install_sso_check(
        monkeypatch,
        [_client.SsoSessionUnavailable("expired")],
        broker=broker,
    )
    assert _check() == crawl_space.EXIT_USER_ACTION
    stderr = capsys.readouterr().err
    assert "No browser was opened" in stderr
    assert "python scripts/setup_sso.py" in stderr
    assert broker.register_calls == []


def test_generic_broker_failure_is_bounded_and_secret_free(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    broker = _Broker()
    broker.refresh_error = credbroker.SsoRecaptureFailedError("SECRET ENGINE DETAIL")
    _, state = _install_sso_check(
        monkeypatch,
        [_client.SsoSessionUnavailable("expired")],
        broker=broker,
    )
    assert _check() == crawl_space.EXIT_USER_ACTION
    stderr = capsys.readouterr().err
    assert "SsoRecaptureFailedError" in stderr
    assert "SECRET ENGINE DETAIL" not in stderr
    assert state["probe_count"] == 1


@pytest.mark.parametrize(
    "failure",
    [
        _client.AuthError("403 Forbidden"),
        _client.AuthError("generic authentication failure"),
        _client.ConfluenceError("TLS failure"),
        _client.ConfluenceError("timeout"),
        _client.ConfluenceError("transport failure"),
        _client.ConfluenceError("server failure"),
    ],
)
def test_nonrecoverable_probe_failures_never_refresh(
    monkeypatch: pytest.MonkeyPatch,
    failure: Exception,
) -> None:
    broker, state = _install_sso_check(monkeypatch, [failure])
    expected = (
        crawl_space.EXIT_USER_ACTION
        if isinstance(failure, _client.AuthError)
        else crawl_space.EXIT_ERROR
    )
    assert _check() == expected
    assert broker.refresh_calls == []
    assert state["probe_count"] == 1
    assert state["close_count"] == 1


def test_malformed_config_never_refreshes(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = _Broker()

    def _malformed():
        raise credbroker.SsoConfigError("malformed SSO configuration")

    monkeypatch.setattr(crawl_space, "_select_auth_path", _malformed)
    monkeypatch.setattr(
        crawl_space,
        "_credbroker_for_sso_check",
        lambda: pytest.fail("malformed config must not feature-detect refresh"),
    )
    assert _check() == crawl_space.EXIT_USER_ACTION
    assert broker.refresh_calls == []


def test_token_check_never_feature_detects_or_refreshes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = {"probe_count": 0, "close_count": 0, "clients": []}

    class _TokenClient(_FakeClient):
        def __init__(self, credentials, **kwargs: object) -> None:
            super().__init__([{"username": "Example User"}], state)

    monkeypatch.setattr(crawl_space, "_select_auth_path", lambda: ("token", None))
    monkeypatch.setattr(
        crawl_space,
        "load_credentials",
        lambda: _client.Credentials(SSO.base_url, "stub", "server", None),
    )
    monkeypatch.setattr(crawl_space, "ConfluenceClient", _TokenClient)
    monkeypatch.setattr(
        crawl_space,
        "_credbroker_for_sso_check",
        lambda: pytest.fail("token path must not feature-detect refresh"),
    )
    assert _check() == crawl_space.EXIT_OK
    assert state["probe_count"] == 1


def test_sso_crawl_never_feature_detects_or_refreshes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses: list[object] = []
    broker, state = _install_sso_check(monkeypatch, responses)
    monkeypatch.setattr(
        crawl_space,
        "_credbroker_for_sso_check",
        lambda: pytest.fail("crawl path must not feature-detect refresh"),
    )

    async def _no_pages(client, root_id: str, depth: int) -> list[object]:
        return []

    monkeypatch.setattr(crawl_space, "_discover", _no_pages)
    args = crawl_space.parse_args([
        "--space",
        "ENG",
        "--root",
        "123",
        "--output",
        str(tmp_path / "crawl"),
    ])
    assert _run(crawl_space.main_async(args)) == crawl_space.EXIT_OK
    assert broker.refresh_calls == []
    assert state["probe_count"] == 0
    assert state["close_count"] == 1


def test_old_credbroker_on_sso_check_gets_bounded_upgrade_message(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def _old_selector():
        raise ImportError(
            "cannot import name 'validate_sso_profile' from 'credbroker'",
            name="credbroker",
        )

    monkeypatch.setattr(crawl_space, "_select_auth_path", _old_selector)
    monkeypatch.setattr(
        crawl_space,
        "_credbroker_for_sso_check",
        lambda: (None, "error: SSO --check needs credbroker>=0.5.0; upgrade it"),
    )
    assert _check() == crawl_space.EXIT_USER_ACTION
    stderr = capsys.readouterr().err
    assert "credbroker>=0.5.0" in stderr
    assert "Traceback" not in stderr


def test_feature_detect_reports_missing_or_old_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _missing(name: str) -> ModuleType:
        raise ModuleNotFoundError("missing", name="credbroker")

    monkeypatch.setattr(importlib, "import_module", _missing)
    module, error = crawl_space._credbroker_for_sso_check()
    assert module is None
    assert error is not None and "credbroker>=0.5.0" in error

    old = ModuleType("credbroker")
    old.__version__ = "0.4.1"
    monkeypatch.setattr(importlib, "import_module", lambda name: old)
    module, error = crawl_space._credbroker_for_sso_check()
    assert module is None
    assert error is not None and "0.4.1" in error and "credbroker>=0.5.0" in error


def test_requirements_keep_the_existing_dependency_floor() -> None:
    requirements = (_SKILL_ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "credbroker>=0.5.0" in requirements
    assert "credbroker>=0.6.0" not in requirements


def test_skill_guidance_allows_one_headless_attempt_before_manual_setup() -> None:
    text = (_SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
    for phrase in (
        "single headless recovery attempt",
        "no browser window",
        "registered profile",
        "manual setup",
    ):
        assert phrase in text
    assert "do not run any setup helper" in text
