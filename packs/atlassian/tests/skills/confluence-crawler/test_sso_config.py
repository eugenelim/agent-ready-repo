"""SSO config loader + selector (fail-closed).

Exercises the per-skill loader against the real placeholder reference file and a
table of crafted fixtures. Requires ``credbroker`` (the validation primitives) on
the path — pip-installed in CI.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import _sso_config
import pytest
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
        (
            'success_url_pattern = "https://jira.corp.example.com/secure/Dashboard.jspa"',
            'success_url_pattern = "jira.corp.example.com/x"',
        ),
        ('validation_endpoint = "/rest/api/2/myself"', 'validation_endpoint = "https://jira.corp.example.com/rest"'),
        (
            'validation_endpoint = "/rest/api/2/myself"',
            'validation_endpoint = "//evil.example.com/rest"',
        ),
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


# ----------------------------------------------------------------------
# AC20 — forwarded-field validation, before anything reaches an argv or the
# engine's profile writer.
# ----------------------------------------------------------------------


def _cfg_with(tmp_path: Path, **overrides: str) -> Path:
    """The valid fixture with `[sso]` lines replaced by raw TOML.

    Values are raw TOML text, not Python strings, so a fixture can carry a TOML
    *escape* — which is the whole point of the control-character cases: a source
    can write ``\\u0001`` and the parsed value then holds the bare character.
    """
    lines = []
    for line in _VALID_COOKIE.strip().splitlines():
        key = line.split("=", 1)[0].strip()
        if key in overrides:
            lines.append(f"{key} = {overrides[key]}")
        else:
            lines.append(line)
    return _write(tmp_path, "\n".join(lines) + "\n")


def test_profile_validated_before_str_coercion(tmp_path: Path) -> None:  # STUB: AC20
    # `profile=str(sso["profile"])` would turn an int 5 into "5" and make the
    # grammar's non-str rejection unreachable from this path.
    with pytest.raises(SsoConfigError):
        load_sso_config(_cfg_with(tmp_path, profile="5"))


def test_profile_grammar_is_enforced_at_load(tmp_path: Path) -> None:   # STUB: AC20
    with pytest.raises(SsoConfigError):
        load_sso_config(_cfg_with(tmp_path, profile='"../../../../tmp/pwn"'))


def test_ttl_hint_minutes_must_be_int(tmp_path: Path) -> None:          # STUB: AC20
    # Annotated `int | None` but passed through untyped, so a string reached
    # the argv builder and then `--ttl-hint-minutes`.
    with pytest.raises(SsoConfigError):
        load_sso_config(_cfg_with(tmp_path, ttl_hint_minutes='"480"'))


def test_ttl_hint_minutes_rejects_bool(tmp_path: Path) -> None:         # STUB: AC20
    # `isinstance(True, int)` is True in Python; a bool is not a duration.
    with pytest.raises(SsoConfigError):
        load_sso_config(_cfg_with(tmp_path, ttl_hint_minutes="true"))


def test_ttl_hint_minutes_accepts_an_int(tmp_path: Path) -> None:       # STUB: AC20
    assert load_sso_config(_cfg_with(tmp_path, ttl_hint_minutes="30")).ttl_hint_minutes == 30


# Every character a TOML basic string cannot carry literally. Written as TOML
# *escapes*, because that is the case a naive check misses: after parsing, the
# value holds the bare character with no literal backslash to notice.
_TOML_BREAKING_ESCAPES = (
    r"\"",       # quote
    r"\\",       # backslash
    "\\u0001",  # a C0 control, written as a TOML escape
    r"\n",       # newline — urlsplit() strips it, so validate_https_url cannot see it
    r"\r",       # carriage return — likewise
    "\\u007F",  # DEL, written as a TOML escape
)

_STRING_FIELDS = {
    "profile": "jira{}x",
    "base_url": "https://jira.corp.example.com/{}",
    "login_url": "https://sso.corp.example.com/login{}",
    "success_url_pattern": "https://jira.corp.example.com/secure/{}",
    "validation_endpoint": "/rest/api/2/myself{}",
    "session_filename": "jira-session{}.json",
}


@pytest.mark.parametrize("bad", _TOML_BREAKING_ESCAPES)
@pytest.mark.parametrize("field", sorted(_STRING_FIELDS))
def test_control_chars_rejected_in_every_sso_field(
    tmp_path: Path, field: str, bad: str
) -> None:                                                              # STUB: AC20
    # urlsplit() strips CR/LF before parsing, so validate_https_url cannot see
    # them — while the engine interpolates the value into `key = "value"`,
    # injecting lines into the profile store.
    value = '"' + _STRING_FIELDS[field].format(bad) + '"'
    with pytest.raises(SsoConfigError):
        load_sso_config(_cfg_with(tmp_path, **{field: value}))


@pytest.mark.parametrize("bad", _TOML_BREAKING_ESCAPES)
def test_control_chars_rejected_in_cookie_domains(tmp_path: Path, bad: str) -> None:
    # STUB: AC20 — the list-valued field is validated per entry.
    value = '["jira.corp.example.com", "corp' + bad + '.example.com"]'
    with pytest.raises(SsoConfigError):
        load_sso_config(_cfg_with(tmp_path, cookie_domains=value))
