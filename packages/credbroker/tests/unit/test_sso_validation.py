"""SSO confinement primitives (spec task T2; AC3, AC4, AC6).

Table-driven over the security-control surface: the https-only scheme guard, the
root-relative endpoint guard, the cookie-domain confinement match (with the
label-boundary near-miss), the load-time over-broad-jar filter, and the send-host
membership fail-closed check.
"""

from __future__ import annotations

import pytest

from credbroker import _sso
from credbroker._sso import SsoConfigError

COOKIE_DOMAINS = ["corp.example.com", "jira.example.invalid"]


# --- https-only scheme guard (AC3) -------------------------------------------

@pytest.mark.parametrize("url", [
    "https://corp.example.com",
    "https://corp.example.com/rest/api/2/myself",
    "https://corp\\.example\\.com/dashboard.*",  # success_url_pattern shape
])
def test_validate_https_url_accepts_https(url: str) -> None:
    _sso.validate_https_url(url, field="login_url")  # no raise


@pytest.mark.parametrize("url", [
    "http://corp.example.com",          # plaintext
    "ftp://corp.example.com",           # smuggling scheme
    "corp.example.com/path",            # scheme-less
    "//corp.example.com",               # protocol-relative
])
def test_validate_https_url_rejects_non_https(url: str) -> None:
    with pytest.raises(SsoConfigError):
        _sso.validate_https_url(url, field="base_url")


# --- root-relative endpoint guard (AC3) --------------------------------------

@pytest.mark.parametrize("endpoint", [
    "/rest/api/2/myself",
    "/",
    "/wiki/rest/api/space",
])
def test_validate_root_relative_endpoint_accepts(endpoint: str) -> None:
    _sso.validate_root_relative_endpoint(endpoint)  # no raise


@pytest.mark.parametrize("endpoint", [
    "rest/api/2/myself",                       # no leading slash
    "https://corp.example.com/rest/api",       # scheme + host
    "//evil.example.com/rest",                 # protocol-relative
    "http://x/y",                              # scheme
    "",                                        # empty
])
def test_validate_root_relative_endpoint_rejects(endpoint: str) -> None:
    with pytest.raises(SsoConfigError):
        _sso.validate_root_relative_endpoint(endpoint)


# --- cookie-domain confinement match (AC3 membership, AC4 normalization) ------

@pytest.mark.parametrize("domain,expected", [
    ("corp.example.com", True),            # exact
    (".corp.example.com", True),           # leading dot (cookie domain shape)
    ("jira.corp.example.com", True),       # subdomain admitted
    ("CORP.EXAMPLE.COM", True),            # case-insensitive
    ("evil-corp.example.com", False),      # label-boundary near-miss — REJECTED
    ("example.com", False),                # parent, not subdomain
    ("corp.example.com.evil.net", False),  # suffix-injection attempt
    ("", False),                           # empty
])
def test_domain_in_cookie_domains(domain: str, expected: bool) -> None:
    assert _sso.domain_in_cookie_domains(domain, COOKIE_DOMAINS) is expected


# --- load-time over-broad-jar filter (AC4) -----------------------------------

def test_filter_jar_to_domains_reduces_overbroad_jar() -> None:
    # The engine captures the session cookies PLUS IdP / analytics cookies seen
    # across the redirect chain. The consumer keeps only the declared domains.
    jar = [
        {"name": "JSESSIONID", "domain": "corp.example.com", "value": "s1"},
        {"name": "crowd.token_key", "domain": ".corp.example.com", "value": "s2"},
        {"name": "atl_token", "domain": "jira.example.invalid", "value": "s3"},
        {"name": "idp_session", "domain": "login.okta.com", "value": "x"},       # IdP
        {"name": "_ga", "domain": ".doubleclick.net", "value": "x"},             # analytics
        {"name": "near_miss", "domain": "evil-corp.example.com", "value": "x"},   # near-miss
    ]
    filtered = _sso.filter_jar_to_domains(jar, COOKIE_DOMAINS)
    kept = {c["name"] for c in filtered}
    assert kept == {"JSESSIONID", "crowd.token_key", "atl_token"}
    # The over-broad source is not mutated (never written back; AC10).
    assert len(jar) == 6


def test_filter_jar_drops_domainless_cookie() -> None:
    jar = [{"name": "no_domain", "value": "x"}]
    assert _sso.filter_jar_to_domains(jar, COOKIE_DOMAINS) == []


# --- send-host membership, fail-closed (AC6) ---------------------------------

@pytest.mark.parametrize("host", ["corp.example.com", "jira.corp.example.com"])
def test_require_host_in_cookie_domains_passes(host: str) -> None:
    _sso.require_host_in_cookie_domains(host, COOKIE_DOMAINS)  # no raise


@pytest.mark.parametrize("host", ["evil-corp.example.com", "example.com", "other.net"])
def test_require_host_in_cookie_domains_fails_closed(host: str) -> None:
    with pytest.raises(SsoConfigError):
        _sso.require_host_in_cookie_domains(host, COOKIE_DOMAINS)
