"""Unit tests for the organization Artifactory bootstrap — Layer 3 of the
catalogue-source resolution chain (RFC-0072 D2).

Covers:
- T1: install-defaults.toml ships [organization.artifactory] disabled by default (AC1)
- T2: _source_from_org_bootstrap validation rules (AC2–AC16, AC21–AC22)
- T2: read_org_bootstrap public API (AC4, AC5, AC19 prerequisite)
- T3: Integration — Layer 3 position in resolve_default_source (AC17, AC18, AC19)
"""
from __future__ import annotations

import importlib.resources
import tomllib

import pytest

from agentbundle.catalogue import CatalogueError
from agentbundle.source_defaults import (
    _is_valid_source,
    _source_from_org_bootstrap,
    read_org_bootstrap,
    resolve_default_source,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_VALID_ORG_TOML = """\
[organization.artifactory]
enabled = true
base-url = "https://example.test/art"
repository = "repo-local"
bundle = "engineering"
channel = "stable"
"""

_DISABLED_ORG_TOML = """\
[organization.artifactory]
enabled = false
"""

_CONSTRUCTED_URL = (
    "catalogue+https://example.test/art"
    "/repo-local/catalogues/engineering/channels/stable.json"
)

# ---------------------------------------------------------------------------
# T1 — install-defaults.toml ships [organization.artifactory] disabled
# ---------------------------------------------------------------------------


def test_install_defaults_org_bootstrap_disabled_by_default():
    """AC1: Packaged file ships [organization.artifactory] with enabled = false only."""
    resource = importlib.resources.files("agentbundle").joinpath(
        "_data/install-defaults.toml"
    )
    text = resource.read_text(encoding="utf-8")
    data = tomllib.loads(text)
    assert data["organization"]["artifactory"]["enabled"] is False
    assert set(data["organization"]["artifactory"].keys()) == {"enabled"}


# ---------------------------------------------------------------------------
# T2 — _source_from_org_bootstrap: disabled paths (return None)
# ---------------------------------------------------------------------------


def test_org_bootstrap_absent_table_returns_none():
    """AC2: No [organization] section → None."""
    text = '[defaults]\nsource = "git+https://example.test/repo"\n'
    assert _source_from_org_bootstrap(text, config_path="test-path") is None


def test_org_bootstrap_absent_artifactory_key_returns_none():
    """AC2: [organization] present but no [organization.artifactory] → None."""
    text = '[organization]\nname = "myorg"\n'
    assert _source_from_org_bootstrap(text, config_path="test-path") is None


def test_org_bootstrap_organization_scalar_returns_none():
    """AC2: organization = 'typo' (non-dict TOML value) → None, not AttributeError."""
    text = 'organization = "typo"\n'
    assert _source_from_org_bootstrap(text, config_path="test-path") is None


def test_org_bootstrap_artifactory_scalar_returns_none():
    """AC2: [organization] with artifactory = true (non-dict) → None, not AttributeError."""
    text = "[organization]\nartifactory = true\n"
    assert _source_from_org_bootstrap(text, config_path="test-path") is None


def test_org_bootstrap_toml_decode_error_returns_none():
    """AC2b: Unparseable TOML → None (not CatalogueError; cannot read enabled)."""
    text = "not = valid = toml\n"
    assert _source_from_org_bootstrap(text, config_path="test-path") is None


def test_org_bootstrap_absent_enabled_returns_none():
    """AC3: [organization.artifactory] present but no enabled key → None."""
    text = '[organization.artifactory]\nbase-url = "https://example.test/art"\n'
    assert _source_from_org_bootstrap(text, config_path="test-path") is None


def test_org_bootstrap_enabled_false_returns_none():
    """AC4: enabled = false → None; other fields not inspected."""
    assert _source_from_org_bootstrap(_DISABLED_ORG_TOML, config_path="test-path") is None


# ---------------------------------------------------------------------------
# T2 — _source_from_org_bootstrap: non-boolean enabled raises (AC3b)
# ---------------------------------------------------------------------------


def test_org_bootstrap_enabled_string_nontrue_raises():
    """AC3b: enabled = 'true' (TOML string, not boolean) → CatalogueError naming enabled."""
    text = '[organization.artifactory]\nenabled = "true"\n'
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="sentinel-path")
    msg = str(exc.value)
    assert "enabled" in msg
    assert "sentinel-path" in msg


def test_org_bootstrap_enabled_integer_raises():
    """AC3b: enabled = 1 (TOML integer) → CatalogueError naming enabled."""
    text = "[organization.artifactory]\nenabled = 1\n"
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="sentinel-path")
    msg = str(exc.value)
    assert "enabled" in msg


# ---------------------------------------------------------------------------
# T2 — _source_from_org_bootstrap: URL construction (AC5, AC6)
# ---------------------------------------------------------------------------


def test_org_bootstrap_valid_config_constructs_url():
    """AC5: Valid enabled = true config → correct catalogue+https:// URL."""
    url = _source_from_org_bootstrap(_VALID_ORG_TOML, config_path="test-path")
    assert url == _CONSTRUCTED_URL


def test_org_bootstrap_trailing_slash_on_base_url_normalized():
    """AC6: Trailing slash on base-url stripped — no double-slash in constructed URL."""
    text = """\
[organization.artifactory]
enabled = true
base-url = "https://example.test/art/"
repository = "repo-local"
bundle = "engineering"
channel = "stable"
"""
    url = _source_from_org_bootstrap(text, config_path="test-path")
    assert url == _CONSTRUCTED_URL
    # Verify no double-slash after the scheme
    after_scheme = url.split("catalogue+https://", 1)[1]
    assert "//" not in after_scheme


def test_org_bootstrap_no_trailing_slash_on_base_url_unchanged():
    """AC6: No trailing slash → same URL as trailing-slash variant."""
    url = _source_from_org_bootstrap(_VALID_ORG_TOML, config_path="test-path")
    assert url == _CONSTRUCTED_URL


# ---------------------------------------------------------------------------
# T2 — base-url validation raises (AC7–AC11)
# ---------------------------------------------------------------------------


def test_org_bootstrap_http_base_url_raises():
    """AC7: http:// base-url → CatalogueError naming base-url."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "http://example.test/art"\n'
        'repository = "r"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "base-url" in str(exc.value)


def test_org_bootstrap_ftp_base_url_raises():
    """AC7: ftp:// base-url → CatalogueError naming base-url."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "ftp://example.test/art"\n'
        'repository = "r"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "base-url" in str(exc.value)


def test_org_bootstrap_uppercase_https_base_url_raises():
    """AC7: HTTPS:// base-url (uppercase scheme) → CatalogueError (case-sensitive prefix check)."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "HTTPS://example.test/art"\n'
        'repository = "r"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "base-url" in str(exc.value)


def test_org_bootstrap_user_info_colon_in_base_url_raises():
    """AC8: user:pass@host in base-url → CatalogueError; message must not contain credential."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://user:pass@example.test/art"\n'
        'repository = "r"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    msg = str(exc.value)
    assert "base-url" in msg
    assert "user" not in msg
    assert "pass" not in msg


def test_org_bootstrap_bare_user_in_base_url_raises():
    """AC8: user@host in base-url → CatalogueError; message must not contain the username."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://user@example.test/art"\n'
        'repository = "r"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    msg = str(exc.value)
    assert "base-url" in msg
    assert "user" not in msg


def test_org_bootstrap_query_string_in_base_url_raises():
    """AC9: Query string in base-url → CatalogueError naming base-url."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art?foo=bar"\n'
        'repository = "r"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "base-url" in str(exc.value)


def test_org_bootstrap_fragment_in_base_url_raises():
    """AC10: Fragment in base-url → CatalogueError naming base-url."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art#section"\n'
        'repository = "r"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "base-url" in str(exc.value)


def test_org_bootstrap_empty_base_url_raises():
    """AC11: Empty base-url → CatalogueError naming base-url."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = ""\n'
        'repository = "r"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "base-url" in str(exc.value)


def test_org_bootstrap_empty_netloc_in_base_url_raises():
    """AC11: Empty netloc (https:///path) → CatalogueError naming base-url."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https:///path"\n'
        'repository = "r"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "base-url" in str(exc.value)


def test_org_bootstrap_integer_base_url_raises():
    """Type-check: base-url = 123 (TOML integer) → CatalogueError naming base-url."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = 123\n'
        'repository = "r"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "base-url" in str(exc.value)


def test_org_bootstrap_missing_base_url_key_raises():
    """AC15: Missing base-url when enabled = true → CatalogueError naming base-url."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'repository = "r"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "base-url" in str(exc.value)


# ---------------------------------------------------------------------------
# T2 — path-segment validation raises (AC12–AC15)
# ---------------------------------------------------------------------------


def test_org_bootstrap_repository_slash_raises():
    """AC12: repository with / → CatalogueError naming repository."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art"\n'
        'repository = "my/repo"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "repository" in str(exc.value)


def test_org_bootstrap_repository_dotdot_raises():
    """AC12 defense-in-depth: repository = '..' → CatalogueError naming repository."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art"\n'
        'repository = ".."\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "repository" in str(exc.value)


def test_org_bootstrap_repository_percent_raises():
    """AC12: repository with % → CatalogueError naming repository."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art"\n'
        'repository = "my%20repo"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "repository" in str(exc.value)


def test_org_bootstrap_repository_space_raises():
    """AC12: repository with space → CatalogueError naming repository."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art"\n'
        'repository = "my repo"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "repository" in str(exc.value)


def test_org_bootstrap_repository_empty_raises():
    """AC12/AC15: Empty repository → CatalogueError naming repository."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art"\n'
        'repository = ""\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "repository" in str(exc.value)


def test_org_bootstrap_repository_integer_raises():
    """Type-check: repository = 42 (TOML integer) → CatalogueError naming repository."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art"\n'
        'repository = 42\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "repository" in str(exc.value)


def test_org_bootstrap_bundle_invalid_raises():
    """AC13: bundle with space → CatalogueError naming bundle."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art"\n'
        'repository = "r"\nbundle = "my bundle"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "bundle" in str(exc.value)


def test_org_bootstrap_bundle_dotdot_raises():
    """AC13 defense-in-depth: bundle = '..' → CatalogueError naming bundle."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art"\n'
        'repository = "r"\nbundle = ".."\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "bundle" in str(exc.value)


def test_org_bootstrap_channel_slash_raises():
    """AC14: channel with / → CatalogueError naming channel."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art"\n'
        'repository = "r"\nbundle = "b"\nchannel = "my/channel"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "channel" in str(exc.value)


def test_org_bootstrap_channel_dotdot_raises():
    """AC14 defense-in-depth: channel = '..' → CatalogueError naming channel."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art"\n'
        'repository = "r"\nbundle = "b"\nchannel = ".."\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "channel" in str(exc.value)


def test_org_bootstrap_missing_repository_raises():
    """AC15: Missing repository when enabled = true → CatalogueError naming repository."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art"\n'
        'bundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "repository" in str(exc.value)


def test_org_bootstrap_missing_bundle_raises():
    """AC15: Missing bundle → CatalogueError naming bundle."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art"\n'
        'repository = "r"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "bundle" in str(exc.value)


def test_org_bootstrap_missing_channel_raises():
    """AC15: Missing channel → CatalogueError naming channel."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art"\n'
        'repository = "r"\nbundle = "b"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    assert "channel" in str(exc.value)


# ---------------------------------------------------------------------------
# T2 — error message contract (AC16, AC8)
# ---------------------------------------------------------------------------


def test_org_bootstrap_error_message_contains_field_and_config_path():
    """AC16: Error messages name the malformed field and the config path."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "http://example.test/art"\n'
        'repository = "r"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="sentinel-path")
    msg = str(exc.value)
    assert "base-url" in msg
    assert "sentinel-path" in msg


def test_org_bootstrap_error_message_never_contains_raw_value():
    """AC8, AC16: Credential in base-url must not appear in error message."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://user:pass@example.test/art"\n'
        'repository = "r"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError) as exc:
        _source_from_org_bootstrap(text, config_path="test-path")
    msg = str(exc.value)
    assert "user" not in msg
    assert "pass" not in msg
    assert "user:pass" not in msg


# ---------------------------------------------------------------------------
# T2 — valid character acceptance and single-dot edge case
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("repo,bundle,channel", [
    ("my-repo", "my.bundle", "my_channel"),
    ("Repo123", "Bundle", "Channel"),
    ("a", "b", "c"),
    ("repo.name", "bundle-name", "channel_name"),
])
def test_org_bootstrap_valid_chars_accepted(repo, bundle, channel):
    """Valid [A-Za-z0-9._-]+ values for all segments produce a URL."""
    text = (
        f'[organization.artifactory]\nenabled = true\n'
        f'base-url = "https://example.test/art"\n'
        f'repository = "{repo}"\nbundle = "{bundle}"\nchannel = "{channel}"\n'
    )
    url = _source_from_org_bootstrap(text, config_path="test-path")
    assert url is not None
    assert url.startswith("catalogue+https://example.test/art/")


def test_org_bootstrap_single_dot_component_accepted():
    """Single '.' is valid — not '..' so the dotdot guard does not fire."""
    text = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "https://example.test/art"\n'
        'repository = "."\nbundle = "b"\nchannel = "c"\n'
    )
    url = _source_from_org_bootstrap(text, config_path="test-path")
    assert url is not None


# ---------------------------------------------------------------------------
# T2 — security invariants (AC22, AC17)
# ---------------------------------------------------------------------------


def test_org_bootstrap_constructed_url_has_no_user_info():
    """AC22: Constructed URL contains no '@' (no user-info in netloc)."""
    url = _source_from_org_bootstrap(_VALID_ORG_TOML, config_path="test-path")
    assert url is not None
    assert "@" not in url


def test_org_bootstrap_is_valid_source_accepts_constructed_url():
    """AC17: Constructed catalogue+https:// URL is accepted by _is_valid_source.

    Wave 2b (spec/https-catalogue-channels) has shipped; _is_valid_source now
    accepts catalogue+https:// URLs. This is a normal passing test (not xfail).
    """
    url = _source_from_org_bootstrap(_VALID_ORG_TOML, config_path="test-path")
    assert url is not None
    assert _is_valid_source(url) is True


# ---------------------------------------------------------------------------
# T2 — read_org_bootstrap via injected reader
# ---------------------------------------------------------------------------


def test_read_org_bootstrap_disabled_returns_none():
    """AC4 via public API: disabled TOML → None."""
    result = read_org_bootstrap(read_text=lambda: (_DISABLED_ORG_TOML, "mock-path"))
    assert result is None


def test_read_org_bootstrap_valid_returns_url():
    """AC5 via public API: valid enabled = true TOML → constructed URL."""
    result = read_org_bootstrap(read_text=lambda: (_VALID_ORG_TOML, "mock-path"))
    assert result == _CONSTRUCTED_URL


def test_read_org_bootstrap_invalid_raises():
    """AC19 prerequisite: invalid base-url propagates CatalogueError."""
    bad_toml = (
        '[organization.artifactory]\nenabled = true\n'
        'base-url = "http://example.test/art"\n'
        'repository = "r"\nbundle = "b"\nchannel = "c"\n'
    )
    with pytest.raises(CatalogueError):
        read_org_bootstrap(read_text=lambda: (bad_toml, "mock-path"))


def test_read_org_bootstrap_reader_returns_none_returns_none():
    """read_text returning None → read_org_bootstrap returns None."""
    result = read_org_bootstrap(read_text=lambda: None)
    assert result is None


# ---------------------------------------------------------------------------
# T3 — Integration: Layer 3 position in resolve_default_source
# ---------------------------------------------------------------------------


def test_resolve_layer3_fires_when_layers1_and_2_absent():
    """AC18: Layer 3 wins when Layer 1 (explicit) and Layer 2 (config_source) absent."""
    layer3_url = (
        "catalogue+https://example.test/art/r/catalogues/b/channels/stable.json"
    )
    out = resolve_default_source(
        None,
        config_source=None,
        dist=None,
        read_org=lambda: layer3_url,
        read_packaged=lambda: None,
    )
    assert out == layer3_url


def test_resolve_layer2_beats_layer3():
    """AC18: Layer 2 config_source wins over Layer 3; read_org is never called."""
    called: list[bool] = []

    def _read_org_spy() -> str | None:
        called.append(True)
        return "catalogue+https://example.test/art/r/catalogues/b/channels/stable.json"

    out = resolve_default_source(
        None,
        config_source="git+https://example.test/user-config",
        dist=None,
        read_org=_read_org_spy,
        read_packaged=lambda: None,
    )
    assert out == "git+https://example.test/user-config"
    assert called == [], "read_org must not have been called"


def test_resolve_layer3_fail_closed_does_not_fall_through():
    """AC19: CatalogueError from Layer 3 propagates; Layers 4 and 5 are not reached."""

    class _SentinelDist:
        def __getattr__(self, name: str):  # type: ignore[override]
            raise AssertionError(
                f"Layer 4 editable detection reached (attr: {name!r})"
            )

    sentinel_dist = _SentinelDist()

    with pytest.raises(CatalogueError, match="org config invalid"):
        resolve_default_source(
            None,
            config_source=None,
            dist=sentinel_dist,
            read_org=lambda: (_ for _ in ()).throw(CatalogueError("org config invalid")),
            read_packaged=lambda: (_ for _ in ()).throw(
                AssertionError("Layer 5 reached")
            ),
        )


def test_resolve_layer1_beats_layer3():
    """AC18 extension: Layer 1 explicit arg wins; read_org is never called."""
    called: list[bool] = []

    def _read_org_spy() -> str | None:
        called.append(True)
        raise AssertionError("read_org must not be called when explicit arg given")

    out = resolve_default_source(
        "explicit-arg",
        config_source=None,
        dist=None,
        read_org=_read_org_spy,
        read_packaged=lambda: None,
    )
    assert out == "explicit-arg"
    assert called == [], "read_org must not have been called"
