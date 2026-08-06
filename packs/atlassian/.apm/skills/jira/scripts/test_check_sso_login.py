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
