"""`jira.py check` SSO auto-recovery — the typed discriminator and the flow.

Covers AC11–AC20, AC30 and AC31 of
``docs/specs/jira-check-sso-auto-login/spec.md``.

**Import route.** ``sys.path.insert(0, <skill root>)`` then ``import
scripts.jira``. A flat ``import jira`` raises ``ImportError: attempted relative
import with no known parent package`` — the bootstrap block at the top of
``jira.py`` is gated on ``__spec__ is None`` while the relative imports below it
are unconditional.

**Every symbol is reached through ``scripts.*``, never a flat ``import
_client``.** The two are distinct module objects with distinct class objects, so
``jira.py``'s ``except SsoSessionUnavailable`` — bound to the ``scripts.`` copy —
would not catch an exception raised from the flat copy. Sibling suites in the
same pytest session load the flat copies, so this is not hypothetical.

The SSO path is driven by pointing ``scripts._sso_config._DEFAULT_CONFIG_PATH``
at a ``tmp_path`` config, exercising the real loader — not by patching
``_select_auth_path``, which would bypass the very loader AC19 verifies.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

pytest.importorskip("credbroker")

import credbroker  # noqa: E402
import httpx  # noqa: E402
import scripts._client as _client  # noqa: E402
import scripts._sso_config as _sso_config  # noqa: E402
import scripts.jira as jira  # noqa: E402

SsoSessionUnavailable = _client.SsoSessionUnavailable
AuthError = _client.AuthError

SSO = _sso_config.SsoConfig(
    profile="jira",
    base_url="https://jira.corp.example.com",
    login_url="https://sso.corp.example.com/login",
    success_url_pattern="https://jira.corp.example.com/secure/Dashboard.jspa",
    cookie_domains=("corp.example.com",),
    validation_endpoint="/rest/api/2/myself",
)

_GOOD_JAR = [
    {"name": "JSESSIONID", "domain": "jira.corp.example.com", "value": "s", "path": "/"},
]


# ----------------------------------------------------------------------
# Harness: a real jar on disk, a stubbed credbroker resolution, and a mock
# transport so every assertion is made on observable behaviour.
# ----------------------------------------------------------------------


@pytest.fixture
def jar(tmp_path: Path) -> Path:
    path = tmp_path / "jira.jar"
    path.write_text(json.dumps(_GOOD_JAR), encoding="utf-8")
    return path


@pytest.fixture
def resolves(monkeypatch, jar):
    """Make ``credbroker.load_sso_cookies`` return *jar*, by default."""
    def _install(result=None):
        def _load(profile):
            if isinstance(result, Exception):
                raise result
            return Path(result) if result is not None else jar
        monkeypatch.setattr(credbroker, "load_sso_cookies", _load)
    _install()
    return _install


def _client_with(monkeypatch, handler, sso=SSO):
    """Build the cookie-path client, then swap in a mock transport."""
    client = _client.JiraClient.from_sso_cookies(sso)
    client._client = httpx.AsyncClient(
        base_url=sso.base_url,
        transport=httpx.MockTransport(handler),
        follow_redirects=False,
    )
    return client


def _run(coro):
    import asyncio
    return asyncio.run(coro)


# ----------------------------------------------------------------------
# AC11 — the typed discriminator, at exactly five sites and nowhere else.
# ----------------------------------------------------------------------


def test_session_unavailable_is_subclass_of_autherror():   # STUB: AC11
    # Keeps the exit band intact: every existing handler and exit code is
    # unchanged because the subclass *is* an AuthError.
    assert issubclass(SsoSessionUnavailable, AuthError)


def test_site1_credbroker_session_error_is_session_unavailable(resolves):  # STUB: AC11
    resolves(credbroker.SsoSessionUnavailableError("no session"))
    with pytest.raises(SsoSessionUnavailable):
        _client.JiraClient.from_sso_cookies(SSO)


def test_config_error_is_not_session_unavailable(resolves):   # STUB: AC11
    # A confinement failure is terminal — re-authenticating cannot fix it.
    resolves(credbroker.SsoConfigError("cookie_domains mismatch"))
    with pytest.raises(AuthError) as exc:
        _client.JiraClient.from_sso_cookies(SSO)
    assert not isinstance(exc.value, SsoSessionUnavailable)


def test_broker_not_installed_is_not_session_unavailable(resolves):   # STUB: AC11
    resolves(credbroker.SsoBrokerNotInstalledError("install the pack"))
    with pytest.raises(AuthError) as exc:
        _client.JiraClient.from_sso_cookies(SSO)
    assert not isinstance(exc.value, SsoSessionUnavailable)


def test_broker_unavailable_is_not_session_unavailable(resolves):   # STUB: AC11
    # A timeout on a slow keychain must not open a browser.
    resolves(credbroker.SsoBrokerUnavailableError("timed out"))
    with pytest.raises(AuthError) as exc:
        _client.JiraClient.from_sso_cookies(SSO)
    assert not isinstance(exc.value, SsoSessionUnavailable)


def test_construction_https_guard_is_not_session_unavailable(resolves):   # STUB: AC11
    from dataclasses import replace
    with pytest.raises(AuthError) as exc:
        _client.JiraClient.from_sso_cookies(
            replace(SSO, base_url="http://jira.corp.example.com")
        )
    assert not isinstance(exc.value, SsoSessionUnavailable)


def test_site3_401_on_cookie_path_is_session_unavailable(monkeypatch, resolves):  # STUB: AC11
    client = _client_with(monkeypatch, lambda r: httpx.Response(401))
    with pytest.raises(SsoSessionUnavailable):
        _run(client.whoami())


def test_site3_unfollowed_redirect_is_session_unavailable(monkeypatch, resolves):  # STUB: AC11
    # follow_redirects is off on the cookie path, and a redirect to login is
    # the DC expired-session signal.
    client = _client_with(
        monkeypatch,
        lambda r: httpx.Response(302, headers={"Location": "https://sso.corp.example.com/login"}),
    )
    with pytest.raises(SsoSessionUnavailable):
        _run(client.whoami())


def test_403_does_not_recapture(monkeypatch, resolves):     # STUB: AC11/AC19
    # A permission failure is terminal — re-authenticating cannot fix it.
    client = _client_with(monkeypatch, lambda r: httpx.Response(403))
    with pytest.raises(AuthError) as exc:
        _run(client.whoami())
    assert not isinstance(exc.value, SsoSessionUnavailable)


def test_site4_2xx_non_json_is_session_unavailable(monkeypatch, resolves):  # STUB: AC11 site 4
    # An SSO reverse proxy commonly answers an expired session with 200 plus
    # the IdP login page. resp.json() then raises JSONDecodeError, which is
    # neither AuthError nor JiraError — today that escapes as exit 1, outside
    # the exit-2 credential band, and no recovery fires.
    client = _client_with(
        monkeypatch,
        lambda r: httpx.Response(200, text="<html><body>Sign in</body></html>"),
    )
    with pytest.raises(SsoSessionUnavailable):
        _run(client.whoami())


@pytest.mark.parametrize(
    "field", ["displayName", "name", "emailAddress", "key", "accountId"]
)
def test_identity_field_accepted_no_recapture(monkeypatch, resolves, field, capsys):
    # STUB: AC11 site 5 — each must NOT raise and must NOT print "as ?".
    # Pins the raise site's accepted set equal to _cmd_check's display set:
    # listing a field the raise site accepts but _cmd_check does not still
    # prints `as ?` at exit 0.
    client = _client_with(monkeypatch, lambda r: httpx.Response(200, json={field: "someone"}))
    info = _run(client.whoami())
    assert info[field] == "someone"
    assert _run(jira._cmd_check(client)) == jira.EXIT_OK
    out = capsys.readouterr().out
    assert "as someone" in out
    assert "as ?" not in out


@pytest.mark.parametrize("body", [{"displayName": None}, {"name": ""}, {"key": 7}])
def test_present_but_unusable_identity_is_session_unavailable(monkeypatch, resolves, body):
    # STUB: AC11 site 5 — presence is not enough; the selector is the first
    # NON-EMPTY str. A presence test would pass while _cmd_check's truthiness
    # chain still fell through to `as ?` at exit 0.
    client = _client_with(monkeypatch, lambda r: httpx.Response(200, json=body))
    with pytest.raises(SsoSessionUnavailable):
        _run(client.whoami())


def test_falls_through_to_later_usable_field(monkeypatch, resolves, capsys):
    # STUB: AC11 site 5 — {"displayName": None, "accountId": "abc"} passes and
    # displays "abc".
    client = _client_with(
        monkeypatch,
        lambda r: httpx.Response(200, json={"displayName": None, "accountId": "abc"}),
    )
    assert _run(jira._cmd_check(client)) == jira.EXIT_OK
    assert "as abc" in capsys.readouterr().out


def test_2xx_json_without_identity_is_session_unavailable(monkeypatch, resolves):
    # STUB: AC11 site 5 — an SSO proxy answering an expired session with a
    # parseable non-identity body must not yield `ok: … as ?` / exit 0. That
    # is an expired session reported as success — worse than a missed recovery.
    client = _client_with(
        monkeypatch,
        lambda r: httpx.Response(200, json={"errorMessages": ["not authorised"]}),
    )
    with pytest.raises(SsoSessionUnavailable):
        _run(client.whoami())


def test_token_path_2xx_without_identity_is_unchanged(monkeypatch):   # STUB: AC11/AC19
    # Sites 3–5 are scoped to the cookie path. The token path behaves exactly
    # as today, including its `as ?` fallback.
    creds = _client.Credentials(
        base_url="https://jira.corp.example.com", token="t",
        flavor=_client.FLAVOR_SERVER, email=None,
    )
    client = _client.JiraClient(creds)
    client._client = httpx.AsyncClient(
        base_url=creds.base_url,
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"x": 1})),
    )
    assert _run(client.whoami()) == {"x": 1}


def test_selector_is_single_sourced():                       # STUB: AC11 site 5
    # Both halves are required, so there is one selector, not two lists that
    # happen to agree today.
    assert jira._identity_of is _client.identity_of


# ----------------------------------------------------------------------
# AC12 — jar failures are in the contract, without leaking bytes.
# ----------------------------------------------------------------------


def test_corrupt_jar_is_session_unavailable(monkeypatch, resolves, tmp_path):  # STUB: AC12
    bad = tmp_path / "corrupt.jar"
    bad.write_text("{not json", encoding="utf-8")
    resolves(bad)
    with pytest.raises(SsoSessionUnavailable):
        _client.JiraClient.from_sso_cookies(SSO)


def test_unreadable_jar_is_session_unavailable(monkeypatch, resolves, tmp_path):  # STUB: AC12
    resolves(tmp_path / "vanished.jar")
    with pytest.raises(SsoSessionUnavailable):
        _client.JiraClient.from_sso_cookies(SSO)


def test_undecodable_jar_is_session_unavailable(monkeypatch, resolves, tmp_path):  # STUB: AC12
    bad = tmp_path / "binary.jar"
    bad.write_bytes(b"\xff\xfe\x00\x01not-utf8")
    resolves(bad)
    with pytest.raises(SsoSessionUnavailable):
        _client.JiraClient.from_sso_cookies(SSO)


@pytest.mark.parametrize("raw", ['{"cookies": []}', '"a string"', "42"])
def test_wrong_shape_jar_is_session_unavailable(monkeypatch, resolves, tmp_path, raw):
    # STUB: AC12 — valid JSON, wrong top-level shape.
    bad = tmp_path / "shape.jar"
    bad.write_text(raw, encoding="utf-8")
    resolves(bad)
    with pytest.raises(SsoSessionUnavailable):
        _client.JiraClient.from_sso_cookies(SSO)


@pytest.mark.parametrize("record", [
    {"domain": 1, "name": "sid", "value": "v"},     # .lstrip() -> AttributeError
    {"domain": "corp.example.com", "value": "v"},   # c["name"] -> KeyError
    {"domain": "corp.example.com", "name": None, "value": "v"},
    {"domain": "corp.example.com", "name": "sid"},  # value missing
    {"domain": "corp.example.com", "name": "sid", "value": "v", "path": 7},
    "not-a-dict",
])
def test_bad_cookie_record_field_is_session_unavailable(monkeypatch, resolves, tmp_path, record):
    # STUB: AC12 — each must raise SsoSessionUnavailable -> exit 2, never
    # TypeError/AttributeError/KeyError escaping as exit 1. A list-of-dicts
    # check is not sufficient: filter_jar_to_domains calls .lstrip() on domain
    # and indexes c["name"], and _client passes `c.get("path") or "/"` straight
    # to httpx.Cookies.set, so {"path": 7} reaches the jar and raises mid-request.
    bad = tmp_path / "record.jar"
    bad.write_text(json.dumps([record]), encoding="utf-8")
    resolves(bad)
    with pytest.raises(SsoSessionUnavailable):
        _client.JiraClient.from_sso_cookies(SSO)


def test_null_path_is_accepted(monkeypatch, resolves, tmp_path):   # STUB: AC12
    # Only a *supplied non-null* path must be a str; the loader already
    # defaults a missing one to "/".
    ok = tmp_path / "nullpath.jar"
    ok.write_text(
        json.dumps([{"name": "sid", "domain": "corp.example.com", "value": "v", "path": None}]),
        encoding="utf-8",
    )
    resolves(ok)
    assert _client.JiraClient.from_sso_cookies(SSO) is not None


def test_jar_error_message_does_not_interpolate_exc(monkeypatch, resolves, tmp_path):
    # STUB: AC12 — a UnicodeDecodeError's text quotes the offending bytes of a
    # cookie jar. The message must be fixed remediation text naming only the
    # profile, with the cause chained via `from exc` rather than interpolated.
    bad = tmp_path / "leaky.jar"
    bad.write_bytes(b'[{"name":"sid","value":"SECRET-COOKIE-BYTES\xff"}]')
    resolves(bad)
    with pytest.raises(SsoSessionUnavailable) as exc:
        _client.JiraClient.from_sso_cookies(SSO)
    message = str(exc.value)
    assert "SECRET-COOKIE-BYTES" not in message
    assert "jira" in message
    assert exc.value.__cause__ is not None, "cause must be chained, not interpolated"


def test_401_remediation_names_no_cookie(monkeypatch, resolves):   # STUB: AC12
    client = _client_with(monkeypatch, lambda r: httpx.Response(401))
    with pytest.raises(SsoSessionUnavailable) as exc:
        _run(client.whoami())
    assert "JSESSIONID" not in str(exc.value)
    assert "jira" in str(exc.value)


# ----------------------------------------------------------------------
# AC13–AC19, AC30, AC31 — the `check` flow, driven through `_run`.
#
# The SSO path is selected by the real loader, pointed at a tmp_path config.
# Patching `_select_auth_path` instead would bypass the loader AC19 verifies.
# ----------------------------------------------------------------------


_SSO_CONFIG_TOML = """\
auth_default = "sso-cookie"

[sso]
profile = "jira"
base_url = "https://jira.corp.example.com"
login_url = "https://sso.corp.example.com/login"
success_url_pattern = "https://jira.corp.example.com/secure/Dashboard.jspa"
cookie_domains = ["jira.corp.example.com"]
validation_endpoint = "/rest/api/2/myself"
"""


@pytest.fixture
def sso_path(tmp_path, monkeypatch):
    """Route the real loader to an SSO-cookie config."""
    cfg = tmp_path / "sso-config.toml"
    cfg.write_text(_SSO_CONFIG_TOML, encoding="utf-8")
    monkeypatch.setattr(_sso_config, "_DEFAULT_CONFIG_PATH", cfg)
    return cfg


@pytest.fixture
def token_path(tmp_path, monkeypatch):
    cfg = tmp_path / "sso-config.toml"
    cfg.write_text('auth_default = "creds"\n', encoding="utf-8")
    monkeypatch.setattr(_sso_config, "_DEFAULT_CONFIG_PATH", cfg)
    return cfg


class _Recorder:
    """Stubs the two credbroker verbs at the `scripts.jira` binding."""

    def __init__(self):
        self.refresh_calls: list[tuple] = []
        self.register_calls: list[tuple] = []
        self.refresh_raises: Exception | None = None
        self.register_raises: Exception | None = None

    def install(self, monkeypatch):
        def _refresh(*args, **kwargs):
            self.refresh_calls.append((args, kwargs))
            if self.refresh_raises is not None:
                raise self.refresh_raises

        def _register(*args, **kwargs):
            self.register_calls.append((args, kwargs))
            if self.register_raises is not None:
                raise self.register_raises

        monkeypatch.setattr(jira.credbroker, "refresh_sso_session", _refresh)
        monkeypatch.setattr(jira.credbroker, "register_sso_session", _register)
        return self


@pytest.fixture
def recapture(monkeypatch):
    return _Recorder().install(monkeypatch)


@pytest.fixture
def responses(monkeypatch, resolves):
    """Drive `whoami` through a scripted list of responses, one per probe."""
    def _install(*sequence):
        remaining = list(sequence)
        seen: list[int] = []

        def _handler(request):
            seen.append(len(seen))
            item = remaining.pop(0) if remaining else remaining_last[0]
            remaining_last[0] = item
            return item() if callable(item) else item

        remaining_last = [httpx.Response(200, json={"displayName": "ok"})]
        original = _client.JiraClient.from_sso_cookies

        def _from_sso_cookies(cfg, **kwargs):
            client = original(cfg, **kwargs)
            client._client = httpx.AsyncClient(
                base_url=cfg.base_url,
                transport=httpx.MockTransport(_handler),
                follow_redirects=False,
            )
            return client

        monkeypatch.setattr(
            _client.JiraClient, "from_sso_cookies", classmethod(
                lambda cls, cfg, **kw: _from_sso_cookies(cfg, **kw)
            )
        )
        return seen
    return _install


def _check(*extra):
    """Parse and run `jira.py check [...]` the way main() does."""
    import asyncio
    args = jira._build_parser().parse_args(["check", *extra])
    return asyncio.run(jira._run(args))


_EXPIRED = httpx.Response(401)
_OK = httpx.Response(200, json={"displayName": "Example User"})


def test_expired_session_refreshes_then_retries(sso_path, recapture, responses, capsys):
    # STUB: AC14
    probes = responses(_EXPIRED, _OK)
    assert _check() == jira.EXIT_OK
    assert len(recapture.refresh_calls) == 1
    assert len(probes) == 2, "must re-probe after the recapture"
    assert "ok: connected" in capsys.readouterr().out


def test_refresh_called_with_profile_only(sso_path, recapture, responses):
    # STUB: AC1/AC14 — no destination may reach the refresh call.
    responses(_EXPIRED, _OK)
    _check()
    args, kwargs = recapture.refresh_calls[0]
    assert args == ("jira",)
    assert kwargs == {}


def test_healthy_session_never_recaptures(sso_path, recapture, responses):
    # STUB: AC14
    responses(_OK)
    assert _check() == jira.EXIT_OK
    assert recapture.refresh_calls == []


def test_unregistered_names_check_register(sso_path, recapture, responses, capsys):
    # STUB: AC14 — remediation addressed to the *user*, no retry, no register.
    recapture.refresh_raises = credbroker.SsoProfileNotRegisteredError("nope")
    probes = responses(_EXPIRED, _OK)
    assert _check() == jira.EXIT_USER_ACTION
    err = capsys.readouterr().err
    assert "ask the user to run: python scripts/jira.py check --register" in err
    assert len(probes) == 1, "no retry after a failed recapture"
    assert recapture.register_calls == []


def test_automatic_path_aborts_rather_than_showing_login_page(
    sso_path, recapture, responses, capsys
):
    # STUB: AC14a — the engine returns 5; check exits 2 with the
    # `check --register` remediation and NO login page.
    recapture.refresh_raises = credbroker.SsoInteractionRequiredError("needs a human")
    probes = responses(_EXPIRED, _OK)
    assert _check() == jira.EXIT_USER_ACTION
    err = capsys.readouterr().err
    assert "check --register" in err
    assert len(probes) == 1
    assert recapture.register_calls == [], "the automatic path never registers"


def test_recapture_failure_is_terminal(sso_path, recapture, responses):
    # STUB: AC14 — any other recapture failure yields exit 2 with no retry.
    recapture.refresh_raises = credbroker.SsoRecaptureFailedError("playwright absent")
    probes = responses(_EXPIRED, _OK)
    assert _check() == jira.EXIT_USER_ACTION
    assert len(probes) == 1


def test_post_recapture_probe_is_the_success_criterion(sso_path, recapture, responses):
    # STUB: AC14 — refresh returns 0 whenever the success-URL pattern matched,
    # so it can succeed while leaving nothing resolvable. Exit 0 is not enough.
    probes = responses(_EXPIRED, _EXPIRED)
    assert _check() == jira.EXIT_USER_ACTION
    assert len(probes) == 2


def test_recapture_invoked_at_most_once(sso_path, recapture, responses):
    # STUB: AC17
    responses(_EXPIRED, _EXPIRED)
    _check()
    assert len(recapture.refresh_calls) == 1


def test_403_does_not_recapture_through_check(sso_path, recapture, responses):
    # STUB: AC11/AC19 — terminal; a recapture cannot fix a permission failure.
    responses(httpx.Response(403))
    assert _check() == jira.EXIT_USER_ACTION
    assert recapture.refresh_calls == []


def test_probe_does_not_route_through_cmd_check(sso_path, recapture, responses, monkeypatch):
    # STUB: AC13 — `_cmd_check` catches AuthError and returns an int, so routing
    # the probe through it would swallow the typed subclass at the two primary
    # expired-session sites and no recovery would ever fire. Asserted by
    # behaviour: with `_cmd_check` poisoned, an expired session must still
    # recover.
    async def _must_not_be_called(client):
        raise AssertionError("_probe must not route through _cmd_check")

    monkeypatch.setattr(jira, "_cmd_check", _must_not_be_called)
    responses(_EXPIRED, _OK)
    assert _check() == jira.EXIT_OK
    assert len(recapture.refresh_calls) == 1


def test_probe_closes_the_client_on_failure(sso_path, recapture, responses):
    # STUB: AC13
    closed: list[bool] = []
    original = _client.JiraClient.__aexit__

    async def _aexit(self, *exc):
        closed.append(True)
        return await original(self, *exc)

    responses(_EXPIRED, _EXPIRED)
    import types
    _client.JiraClient.__aexit__ = _aexit
    try:
        _check()
    finally:
        _client.JiraClient.__aexit__ = original
    assert len(closed) >= 2, "each probe must close its client"
    del types


# --- AC19 / AC31: blast radius ------------------------------------------


@pytest.mark.parametrize("command", ["whoami", "get-issue"])
def test_non_check_subcommand_never_recaptures(sso_path, recapture, monkeypatch, command):
    # STUB: AC19/AC31 — `from_sso_cookies` is called for every subcommand
    # before dispatch, so the obvious implementation would recapture for all
    # of them.
    import asyncio
    calls = []

    def _from_sso_cookies(cls, cfg, **kw):
        calls.append(cfg)
        raise _client.SsoSessionUnavailable("expired")

    monkeypatch.setattr(
        _client.JiraClient, "from_sso_cookies", classmethod(_from_sso_cookies)
    )
    argv = [command] if command == "whoami" else [command, "PROJ-1"]
    args = jira._build_parser().parse_args(argv)
    assert asyncio.run(jira._run(args)) == jira.EXIT_USER_ACTION
    assert recapture.refresh_calls == []
    assert calls, "the shared construction path must still run for other commands"


def test_malformed_sso_config_fails_at_the_selector(tmp_path, monkeypatch, recapture):
    # STUB: AC19 — exit 2 at the selector, no recapture.
    cfg = tmp_path / "sso-config.toml"
    cfg.write_text(
        _SSO_CONFIG_TOML.replace("https://jira.corp", "http://jira.corp"),
        encoding="utf-8",
    )
    monkeypatch.setattr(_sso_config, "_DEFAULT_CONFIG_PATH", cfg)
    assert _check() == jira.EXIT_USER_ACTION
    assert recapture.refresh_calls == []


def test_token_path_check_is_unchanged(token_path, recapture, monkeypatch, capsys):
    # STUB: AC19 — absent/creds config runs the token path unchanged.
    import asyncio
    creds = _client.Credentials(
        base_url="https://jira.corp.example.com", token="t",
        flavor=_client.FLAVOR_SERVER, email=None,
    )
    monkeypatch.setattr(jira, "load_credentials", lambda: creds)
    real_init = _client.JiraClient.__init__

    def _init(self, credentials, **kwargs):
        real_init(self, credentials, **kwargs)
        self._client = httpx.AsyncClient(
            base_url=credentials.base_url,
            transport=httpx.MockTransport(lambda r: _OK),
        )

    monkeypatch.setattr(_client.JiraClient, "__init__", _init)
    args = jira._build_parser().parse_args(["check"])
    assert asyncio.run(jira._run(args)) == jira.EXIT_OK
    assert recapture.refresh_calls == []
    assert "ok: connected" in capsys.readouterr().out


# --- AC15 / AC16: --register, disclosure -------------------------------


def test_bare_check_never_registers(sso_path, recapture, responses):   # STUB: AC15
    responses(_EXPIRED, _OK)
    _check()
    assert recapture.register_calls == []


def test_register_flag_discloses_host_on_stderr(
    sso_path, recapture, responses, derives, capsys
):
    # STUB: AC15/AC16 — the headed-browser notice names the resolved login host.
    derives("https://sso.corp.example.com")
    responses(_OK)
    assert _check("--register") == jira.EXIT_OK
    err = capsys.readouterr().err
    assert "sso.corp.example.com" in err
    assert "browser" in err.lower()
    assert len(recapture.register_calls) == 1


def test_automatic_notice_promises_no_browser(sso_path, recapture, responses, capsys):
    # STUB: AC16 — the automatic notice must not mention a headed browser,
    # because AC14a forbids one, and must say where the destination comes from.
    responses(_EXPIRED, _OK)
    _check()
    err = capsys.readouterr().err
    assert "jira" in err
    assert "headless" in err.lower()
    assert "no browser" in err.lower()
    assert "stored profile" in err.lower()


def test_nothing_written_to_stdout_before_retry(sso_path, recapture, responses, capsys):
    # STUB: AC16 — the disclosure is stderr-only.
    responses(_EXPIRED, _EXPIRED)
    _check()
    assert capsys.readouterr().out == ""


def test_register_is_not_retried(sso_path, recapture, responses, derives, capsys):  # STUB: AC17
    derives("https://sso.corp.example.com")
    recapture.register_raises = credbroker.SsoRecaptureFailedError("not completed")
    responses(_OK)
    assert _check("--register") == jira.EXIT_USER_ACTION
    assert len(recapture.register_calls) == 1


def test_register_flag_exists_only_on_check(sso_path):     # STUB: AC15
    # "Ask first" before adding any CLI flag to check — and nothing else earns
    # one, so --register must not leak onto another subcommand.
    with pytest.raises(SystemExit):
        jira._build_parser().parse_args(["whoami", "--register"])


# --- AC18: --insecure is honest on both paths --------------------------


def test_insecure_warns_on_token_path(token_path, monkeypatch, capsys):   # STUB: AC18
    import asyncio
    creds = _client.Credentials(
        base_url="https://jira.corp.example.com", token="t",
        flavor=_client.FLAVOR_SERVER, email=None,
    )
    monkeypatch.setattr(jira, "load_credentials", lambda: creds)
    seen = {}
    real_init = _client.JiraClient.__init__

    def _init(self, credentials, **kwargs):
        seen.update(kwargs)
        real_init(self, credentials, **kwargs)
        self._client = httpx.AsyncClient(
            base_url=credentials.base_url,
            transport=httpx.MockTransport(lambda r: _OK),
        )

    monkeypatch.setattr(_client.JiraClient, "__init__", _init)
    args = jira._build_parser().parse_args(["--insecure", "check"])
    asyncio.run(jira._run(args))
    assert seen["verify_tls"] is False, "the flag must still take effect"
    assert "warning" in capsys.readouterr().err.lower()


def test_insecure_warns_ignored_on_sso_path(sso_path, recapture, responses, capsys):
    # STUB: AC18 — inert on the cookie path (from_sso_cookies hardcodes its own
    # SSL context), so say so rather than implying it worked.
    responses(_OK)
    args = jira._build_parser().parse_args(["--insecure", "check"])
    import asyncio
    assert asyncio.run(jira._run(args)) == jira.EXIT_OK
    err = capsys.readouterr().err.lower()
    assert "ignored" in err


def test_insecure_is_never_forwarded_to_the_engine(sso_path, recapture, responses):
    # STUB: AC18
    responses(_EXPIRED, _OK)
    args = jira._build_parser().parse_args(["--insecure", "check"])
    import asyncio
    asyncio.run(jira._run(args))
    flat = repr(recapture.refresh_calls)
    assert "insecure" not in flat


# --- AC30: the credbroker version floor --------------------------------


def test_old_credbroker_exits_2_with_upgrade_hint(sso_path, monkeypatch, capsys):
    # STUB: AC30 — the pip layer precedes the vendored floor on sys.path, so an
    # adopter pinned to 0.4.1 silently gets the old library. Only
    # `credbroker.refresh_sso_session` — a module attribute referenced here —
    # produces the uncaught-AttributeError exit-1 path.
    monkeypatch.delattr(jira.credbroker, "refresh_sso_session", raising=False)
    assert _check() == jira.EXIT_USER_ACTION
    err = capsys.readouterr().err
    assert "0.5.0" in err
    assert "credbroker" in err


def test_version_floor_guard_does_not_gate_the_token_path(token_path, monkeypatch, capsys):
    # STUB: AC30/AC19 — placing the guard in the shared bootstrap would break
    # every token-path subcommand.
    import asyncio
    monkeypatch.delattr(jira.credbroker, "refresh_sso_session", raising=False)
    creds = _client.Credentials(
        base_url="https://jira.corp.example.com", token="t",
        flavor=_client.FLAVOR_SERVER, email=None,
    )
    monkeypatch.setattr(jira, "load_credentials", lambda: creds)
    real_init = _client.JiraClient.__init__

    def _init(self, credentials, **kwargs):
        real_init(self, credentials, **kwargs)
        self._client = httpx.AsyncClient(
            base_url=credentials.base_url,
            transport=httpx.MockTransport(lambda r: _OK),
        )

    monkeypatch.setattr(_client.JiraClient, "__init__", _init)
    args = jira._build_parser().parse_args(["whoami"])
    assert asyncio.run(jira._run(args)) == jira.EXIT_OK


def test_requirements_pin_the_floor_in_both_skills():         # STUB: AC30
    # Both consuming skills: confluence-crawler inherits the mirrored files, so
    # a pin on only one side leaves it importing an API its loader now needs.
    skills_dir = Path(__file__).resolve().parents[2]
    for skill in ("jira", "confluence-crawler"):
        text = (skills_dir / skill / "requirements.txt").read_text(encoding="utf-8")
        assert "credbroker>=0.5.0" in text, f"{skill} does not pin the floor"


# ----------------------------------------------------------------------
# AC32 — the destination `--register` opens a browser at is attested against
# the instance where it can be. Defence in depth, not the control.
# ----------------------------------------------------------------------


@pytest.fixture
def derives(monkeypatch):
    """Stub `derive_sso_destination`, recording whether it was consulted."""
    calls: list[tuple] = []

    def _install(result):
        def _derive(base_url, *, strategies=()):
            calls.append((base_url, strategies))
            if isinstance(result, Exception):
                raise result
            return result

        monkeypatch.setattr(jira.credbroker, "derive_sso_destination", _derive)
        return calls

    return _install


def test_register_proceeds_when_derived_host_matches(sso_path, recapture, responses, derives):
    # STUB: AC32 — branch 1: the IdP-host topology, where derivation works.
    derives("https://sso.corp.example.com")
    responses(_OK)
    assert _check("--register") == jira.EXIT_OK
    assert len(recapture.register_calls) == 1


def test_register_refuses_on_host_mismatch(sso_path, recapture, responses, derives, capsys):
    # STUB: AC32 — exit 2, NO browser, naming both hosts and the escape.
    derives("https://attacker.example.com")
    responses(_OK)
    assert _check("--register") == jira.EXIT_USER_ACTION
    err = capsys.readouterr().err
    assert "sso.corp.example.com" in err
    assert "attacker.example.com" in err
    assert "setup_sso.py" in err
    assert recapture.register_calls == [], "no browser on a mismatch"


def test_cannot_derive_refuses_and_names_setup_sso(sso_path, recapture, responses, derives, capsys):
    # STUB: AC32 — SSO-with-local-fallback: login.jsp answers 200. It must
    # never fall back to the configured value.
    derives(None)
    responses(_OK)
    assert _check("--register") == jira.EXIT_USER_ACTION
    assert "setup_sso.py" in capsys.readouterr().err
    assert recapture.register_calls == []


def test_derivation_failure_is_treated_as_cannot_derive(sso_path, recapture, responses, derives):
    # STUB: AC32 — a network refusal must not be read as an attestation pass.
    derives(credbroker.SsoConfigError("bad base_url"))
    responses(_OK)
    assert _check("--register") == jira.EXIT_USER_ACTION
    assert recapture.register_calls == []


def test_branch2_short_circuits_without_a_derivation_request(
    tmp_path, monkeypatch, recapture, responses, derives
):
    # STUB: AC32 — where login_url's host equals base_url's host (SP-initiated
    # SAML, the majority topology) *no derivation request is made*, and the
    # cannot-derive outcome does not apply. Otherwise the majority topology
    # would be refused whenever /login.jsp answers 200.
    cfg = tmp_path / "sso-config.toml"
    cfg.write_text(
        _SSO_CONFIG_TOML.replace(
            'login_url = "https://sso.corp.example.com/login"',
            'login_url = "https://jira.corp.example.com/plugins/servlet/samlsso"',
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_sso_config, "_DEFAULT_CONFIG_PATH", cfg)
    calls = derives(None)      # would refuse, if it were ever consulted
    responses(_OK)

    assert _check("--register") == jira.EXIT_OK
    assert calls == [], "branch 2 must make no derivation request"
    assert len(recapture.register_calls) == 1


def test_the_vendor_strategy_is_requested_by_name(sso_path, recapture, responses, derives):
    # STUB: AC32 — the Seraph probe is opt-in; a non-Atlassian consumer of the
    # same credbroker function never runs it.
    calls = derives("https://sso.corp.example.com")
    responses(_OK)
    _check("--register")
    assert calls[0][1] == ("atlassian-seraph",)


def test_bare_check_never_derives(sso_path, recapture, responses, derives):   # STUB: AC32
    # The automatic path accepts no destination, so it needs no attestation.
    calls = derives("https://attacker.example.com")
    responses(_EXPIRED, _OK)
    assert _check() == jira.EXIT_OK
    assert calls == []
