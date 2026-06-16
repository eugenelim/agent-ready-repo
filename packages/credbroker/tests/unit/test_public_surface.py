"""Public-surface parity (spec task T2; AC3).

credbroker re-exports the shim's full ``__all__`` (so a consumer swaps only
its import line) plus the public replacements for the private symbols
``credential-setup`` consumed (``parse_schema`` for ``_parse_schema``,
``tier2_backend_label`` for ``_tier2_backend_label``).
"""

from __future__ import annotations

import credbroker

# The shim's 11 ``__all__`` names — every one must import from credbroker.
SHIM_PUBLIC_NAMES = [
    "CredsSchema",
    "Credentials",
    "CredentialsMissingError",
    "DOTFILE_MAX_BYTES",
    "EnvParseError",
    "KeyDef",
    "PermissiveAclError",
    "SchemaError",
    "Tier2HardFailError",
    "load_credentials",
    "parse_env_file",
]


def test_full_shim_surface_is_reexported() -> None:
    for name in SHIM_PUBLIC_NAMES:
        assert hasattr(credbroker, name), f"missing public name: {name}"
        assert name in credbroker.__all__, f"{name} not in credbroker.__all__"


def test_public_replacements_for_private_shim_symbols() -> None:
    # credential-setup imported _parse_schema / _tier2_backend_label privately;
    # credbroker exposes them under public names so no underscore import is needed.
    assert credbroker.parse_schema is credbroker._core._parse_schema
    assert credbroker.tier2_backend_label is credbroker._core._tier2_backend_label
    assert "parse_schema" in credbroker.__all__
    assert "tier2_backend_label" in credbroker.__all__


# SSO web-session cookie family (RFC-0035) — the second consumer-resolution
# family; every name must be importable from the top-level package.
SSO_PUBLIC_NAMES = [
    "load_sso_cookies",
    "SsoError",
    "SsoBrokerNotInstalledError",
    "SsoSessionUnavailableError",
    "SsoConfigError",
    "validate_https_url",
    "validate_root_relative_endpoint",
    "domain_in_cookie_domains",
    "filter_jar_to_domains",
    "require_host_in_cookie_domains",
]


def test_sso_surface_is_reexported() -> None:
    for name in SSO_PUBLIC_NAMES:
        assert hasattr(credbroker, name), f"missing public name: {name}"
        assert name in credbroker.__all__, f"{name} not in credbroker.__all__"


def test_no_underscore_names_in_public_all() -> None:
    # The public surface must not advertise private/underscore names
    # (other than the dunder __version__).
    for name in credbroker.__all__:
        assert not name.startswith("_") or name == "__version__", name
