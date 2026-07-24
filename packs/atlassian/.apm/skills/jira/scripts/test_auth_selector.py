"""Integration tests for the auth-path selector (AC4).

Drives ``_select_auth_path`` end-to-end: the three selector outcomes
(absent → token, valid sso-cookie → sso-cookie, malformed → raises) each
get a test. Requires ``credbroker`` on the path — pip-installed in CI.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

pytest.importorskip("credbroker")
from credbroker import SsoConfigError  # noqa: E402

from _sso_config import SsoConfig, _select_auth_path  # noqa: E402


_VALID_SSO_COOKIE = textwrap.dedent(
    """
    auth_default = "sso-cookie"

    [sso]
    profile = "jira"
    base_url = "https://jira.corp.example.com"
    login_url = "https://sso.corp.example.com/login"
    success_url_pattern = "https://jira.corp.example.com/secure/Dashboard.jspa"
    cookie_domains = ["jira.corp.example.com"]
    validation_endpoint = "/rest/api/2/myself"
    """
)


def test_select_auth_path_absent_is_token(tmp_path: Path) -> None:
    path, cfg = _select_auth_path(tmp_path / "no-such.toml")
    assert path == "token"
    assert cfg is None


def test_select_auth_path_valid_sso_cookie(tmp_path: Path) -> None:
    fixture = tmp_path / "sso-config.toml"
    fixture.write_text(_VALID_SSO_COOKIE, encoding="utf-8")
    path, cfg = _select_auth_path(fixture)
    assert path == "sso-cookie"
    assert isinstance(cfg, SsoConfig)


def test_select_auth_path_malformed_raises(tmp_path: Path) -> None:
    fixture = tmp_path / "sso-config.toml"
    fixture.write_text('auth_default = "sso-cookie"\n', encoding="utf-8")
    with pytest.raises(SsoConfigError):
        _select_auth_path(fixture)
