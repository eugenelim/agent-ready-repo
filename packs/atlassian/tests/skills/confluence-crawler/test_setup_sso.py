"""setup_sso helper — seed the broker profile from the file.

Goal-based: the helper reads the validated config and drives
``credbroker.register_sso_session`` with connection params from the file (no
cookie value on argv, no broker path resolved here), a malformed config is
rejected *before* register is invoked, and every refusal lands in the skill's
exit-2 credential band.

Rewritten from the argv-building version: `build_register_argv`,
`_broker_path` and `subprocess` all left the skill scripts when the operation
moved into `credbroker`, so the four tests that bound those symbols could not
be adapted.
"""

from __future__ import annotations

import pytest
import setup_sso
from _sso_config import SsoConfig

pytest.importorskip("credbroker")
import credbroker  # noqa: E402

CFG = SsoConfig(
    profile="jira",
    base_url="https://jira.corp.example.com",
    login_url="https://sso.corp.example.com/login",
    success_url_pattern="https://jira.corp.example.com/secure/Dashboard.jspa",
    cookie_domains=("jira.corp.example.com", "corp.example.com"),
    validation_endpoint="/rest/api/2/myself",
    session_filename="jira-session.json",
    ttl_hint_minutes=480,
)


@pytest.fixture
def registered(monkeypatch):
    """Capture the kwargs `register_sso_session` is called with."""
    seen: dict = {}

    def _register(profile, **kwargs):
        seen["profile"] = profile
        seen.update(kwargs)

    monkeypatch.setattr(credbroker, "register_sso_session", _register)
    return seen


@pytest.fixture
def never_registers(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("register_sso_session must not be called")

    monkeypatch.setattr(credbroker, "register_sso_session", _boom)


def test_no_subprocess_or_broker_path_left_in_the_skill():   # STUB: AC2
    # The whole point of moving the operation into credbroker: no skill script
    # resolves a broker path, builds a broker argv, or calls subprocess.
    from pathlib import Path
    src = Path(setup_sso.__file__).read_text(encoding="utf-8")
    for banned in ("subprocess", "sso-broker.py", "build_register_argv", "_broker_path"):
        assert banned not in src, f"{banned} still present in setup_sso.py"


def test_connection_params_forwarded_no_cookie(monkeypatch, registered):  # STUB: AC2
    monkeypatch.setattr(setup_sso, "load_sso_config", lambda: CFG)
    assert setup_sso.main() == 0

    assert registered["profile"] == "jira"
    assert registered["login_url"] == CFG.login_url
    assert registered["validation_endpoint"] == "/rest/api/2/myself"
    assert tuple(registered["cookie_domains"]) == CFG.cookie_domains
    assert registered["ttl_hint_minutes"] == 480
    assert registered["session_filename"] == "jira-session.json"
    # No cookie *value* shape anywhere in what crosses (path-not-value).
    flat = repr(registered)
    for token in ("JSESSIONID", "Cookie:", "crowd.token"):
        assert token not in flat


def test_main_creds_default_is_noop(never_registers):
    # Real reference file is creds → load_sso_config() returns None; register
    # must NOT be invoked.
    assert setup_sso.main() == 0


def test_main_rejects_malformed_config_before_register(monkeypatch, never_registers):
    def _raise():
        raise credbroker.SsoConfigError("non-https base_url")

    monkeypatch.setattr(setup_sso, "load_sso_config", _raise)
    assert setup_sso.main() == 2


@pytest.mark.parametrize("error", [
    "SsoBrokerNotInstalledError",
    "SsoRecaptureFailedError",
    "SsoBrokerUnavailableError",
])
def test_every_broker_refusal_is_exit_2(monkeypatch, error):   # STUB: AC2
    # Previously this returned `subprocess.run(...).returncode` verbatim, so an
    # engine 3 surfaced as a functional error rather than a credential one.
    monkeypatch.setattr(setup_sso, "load_sso_config", lambda: CFG)

    def _raise(*a, **k):
        raise getattr(credbroker, error)("nope")

    monkeypatch.setattr(credbroker, "register_sso_session", _raise)
    assert setup_sso.main() == 2
