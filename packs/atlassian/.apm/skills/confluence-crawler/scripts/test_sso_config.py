"""SSO config loader + selector (fail-closed).

Exercises the per-skill loader against the real placeholder reference file and a
table of crafted fixtures. Requires ``credbroker`` (the validation primitives) on
the path — pip-installed in CI.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

import _sso_config
from _sso_config import SsoConfig, load_sso_config

pytest.importorskip("credbroker")
from credbroker import SsoConfigError  # noqa: E402


_VALID_COOKIE = textwrap.dedent(
    """
    auth_default = "sso-cookie"

    [sso]
    profile = "jira"
    base_url = "https://jira.corp.example.com"
    login_url = "https://sso.corp.example.com/login"
    success_url_pattern = "https://jira.corp.example.com/secure/Dashboard.jspa"
    cookie_domains = ["jira.corp.example.com"]
    validation_endpoint = "/rest/api/2/myself"
    session_filename = "jira-session.json"
    ttl_hint_minutes = 480
    """
)


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "sso-config.toml"
    p.write_text(body, encoding="utf-8")
    return p


def test_real_reference_file_is_creds_path() -> None:
    # Upstream placeholder: auth_default = "creds" → None (token path).
    assert load_sso_config() is None


def test_absent_file_is_creds_path(tmp_path: Path) -> None:
    assert load_sso_config(tmp_path / "nope.toml") is None


def test_explicit_creds_default_is_none(tmp_path: Path) -> None:
    cfg = _write(tmp_path, 'auth_default = "creds"\n[sso]\nprofile = "x"\n')
    assert load_sso_config(cfg) is None


def test_valid_sso_cookie_config_parses(tmp_path: Path) -> None:
    cfg = load_sso_config(_write(tmp_path, _VALID_COOKIE))
    assert isinstance(cfg, SsoConfig)
    assert cfg.profile == "jira"
    assert cfg.base_url == "https://jira.corp.example.com"
    assert cfg.cookie_domains == ("jira.corp.example.com",)
    assert cfg.validation_endpoint == "/rest/api/2/myself"
    assert cfg.ttl_hint_minutes == 480


@pytest.mark.parametrize(
    "mutation",
    [
        ('base_url = "https://jira.corp.example.com"', 'base_url = "http://jira.corp.example.com"'),
        ('login_url = "https://sso.corp.example.com/login"', 'login_url = "ftp://sso.corp.example.com"'),
        ('success_url_pattern = "https://jira.corp.example.com/secure/Dashboard.jspa"', 'success_url_pattern = "jira.corp.example.com/x"'),
        ('validation_endpoint = "/rest/api/2/myself"', 'validation_endpoint = "https://jira.corp.example.com/rest"'),
        ('validation_endpoint = "/rest/api/2/myself"', 'validation_endpoint = "//evil.example.com/rest"'),
        ('cookie_domains = ["jira.corp.example.com"]', "cookie_domains = []"),
    ],
)
def test_fail_closed_on_malformed_values(tmp_path: Path, mutation: tuple[str, str]) -> None:
    old, new = mutation
    body = _VALID_COOKIE.replace(old, new)
    with pytest.raises(SsoConfigError):
        load_sso_config(_write(tmp_path, body))


def test_over_broad_single_label_cookie_domain_rejected(tmp_path: Path) -> None:
    body = _VALID_COOKIE.replace(
        'cookie_domains = ["jira.corp.example.com"]', 'cookie_domains = ["com"]'
    )
    with pytest.raises(SsoConfigError):
        load_sso_config(_write(tmp_path, body))


def test_base_host_outside_cookie_domains_rejected(tmp_path: Path) -> None:
    body = _VALID_COOKIE.replace(
        'cookie_domains = ["jira.corp.example.com"]',
        'cookie_domains = ["other.example.com"]',
    )
    with pytest.raises(SsoConfigError):
        load_sso_config(_write(tmp_path, body))


def test_session_filename_with_separator_rejected(tmp_path: Path) -> None:
    body = _VALID_COOKIE.replace(
        'session_filename = "jira-session.json"',
        'session_filename = "../../evil.json"',
    )
    with pytest.raises(SsoConfigError):
        load_sso_config(_write(tmp_path, body))


def test_unknown_sso_key_rejected(tmp_path: Path) -> None:
    body = _VALID_COOKIE.replace(
        'ttl_hint_minutes = 480', 'ttl_hint_minutes = 480\nrogue_key = "x"'
    )
    with pytest.raises(SsoConfigError):
        load_sso_config(_write(tmp_path, body))


def test_missing_required_key_rejected(tmp_path: Path) -> None:
    body = _VALID_COOKIE.replace(
        'validation_endpoint = "/rest/api/2/myself"\n', ""
    )
    with pytest.raises(SsoConfigError):
        load_sso_config(_write(tmp_path, body))


def test_missing_sso_table_rejected(tmp_path: Path) -> None:
    with pytest.raises(SsoConfigError):
        load_sso_config(_write(tmp_path, 'auth_default = "sso-cookie"\n'))


def test_schema_key_set_matches_reference_file() -> None:
    # The loader's allowed-key set must cover exactly the reference file's [sso]
    # keys (drift guard between the loader and the shipped placeholder).
    import tomllib

    data = tomllib.loads(_sso_config._DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
    assert set(data["sso"]) <= _sso_config._ALLOWED_SSO_KEYS
