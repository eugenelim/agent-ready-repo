"""setup_sso helper — seed the broker profile from the file (spec task T7; AC14).

Goal-based: the helper reads the validated config and drives `sso-broker register`
with connection params from the file (no cookie value on argv), and a malformed
config is rejected *before* register is invoked.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import setup_sso
from _sso_config import SsoConfig

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


def test_build_register_argv_carries_connection_params_no_cookie(tmp_path):
    broker = tmp_path / "sso-broker.py"
    argv = setup_sso.build_register_argv(broker, CFG)

    assert argv[2:4] == ["register", "jira"]
    assert argv[argv.index("--login-url") + 1] == CFG.login_url
    assert argv[argv.index("--validation-endpoint") + 1] == "/rest/api/2/myself"
    # one --cookie-domain per declared domain
    assert argv.count("--cookie-domain") == 2
    assert "corp.example.com" in argv and "jira.corp.example.com" in argv
    assert argv[argv.index("--ttl-hint-minutes") + 1] == "480"
    # No cookie *value* shape anywhere on argv (AC14 path-not-value).
    assert not any(token in part for part in argv for token in ("JSESSIONID", "Cookie:", "crowd.token"))


def test_main_creds_default_is_noop(monkeypatch):
    # Real reference file is creds → load_sso_config() returns None; register
    # must NOT be invoked.
    called = {"run": False}

    def _no_run(*a, **k):
        called["run"] = True
        raise AssertionError("subprocess.run must not be called on the creds path")

    monkeypatch.setattr(setup_sso.subprocess, "run", _no_run)
    assert setup_sso.main() == 0
    assert called["run"] is False


def test_main_rejects_malformed_config_before_register(monkeypatch):
    def _raise():
        raise ValueError("non-https base_url")

    monkeypatch.setattr(setup_sso, "load_sso_config", _raise)

    def _no_run(*a, **k):
        raise AssertionError("register must not run when the config is malformed")

    monkeypatch.setattr(setup_sso.subprocess, "run", _no_run)
    assert setup_sso.main() == 2


def test_main_drives_register_when_configured(monkeypatch, tmp_path):
    broker = tmp_path / "sso-broker.py"
    broker.write_text("# fake", encoding="utf-8")
    monkeypatch.setattr(setup_sso, "load_sso_config", lambda: CFG)
    monkeypatch.setattr(setup_sso, "_broker_path", lambda: broker)

    seen = {}

    class _Result:
        returncode = 0

    def _capture(argv, *a, **k):
        seen["argv"] = list(argv)
        return _Result()

    monkeypatch.setattr(setup_sso.subprocess, "run", _capture)
    assert setup_sso.main() == 0
    assert "register" in seen["argv"] and "jira" in seen["argv"]
    assert str(broker) in seen["argv"]
