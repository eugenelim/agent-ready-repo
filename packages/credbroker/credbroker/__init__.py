"""credbroker — a standalone, pip-installable credential resolver.

This library replaces the build-projected ``credentials_shim`` (byte-copied into
every credentialed skill's ``scripts/`` by the build pipeline) with an
in-process library. The stdlib-only core resolves credentials through three
tiers — environment variable, OS keyring, then a ``0600`` dotfile floor — with
the same public surface the shim exposed, so consumer call sites change only
their import line. An optional ``credbroker[crypto]`` extra adds an
encrypted-at-rest vault (Argon2id -> KEK -> AES-256-GCM) for the floor tier;
the vault module is imported lazily so the base import graph stays free of any
third-party dependency.

The resolution core (``_core``) is a near-verbatim lift of the former shim; the
two Tier-2 backends (``_keychain_macos`` / ``_credman_windows``) travel inside
the package. This module re-exports the full public surface.
"""

from __future__ import annotations

# The shim's full ``__all__`` — re-exported verbatim so a credentialed consumer
# swaps only its import line (``from .credentials_shim import …`` ->
# ``from credbroker import …``).
from ._core import (
    DOTFILE_MAX_BYTES,
    Credentials,
    CredentialsMissingError,
    CredsSchema,
    EnvParseError,
    KeyDef,
    PermissiveAclError,
    SchemaError,
    Tier2HardFailError,
    VaultUnavailableError,
    crypto_available,
    keyring_available,
    load_credentials,
    parse_env_file,
    source_vault_master,
    store_in_dotfile,
    store_in_keyring,
    store_in_vault,
    store_vault_master,
)

# Public replacements for the private shim symbols ``credential-setup`` consumed
# (``_parse_schema`` / ``_tier2_backend_label``) so it imports no
# underscore-prefixed name (spec: credential-setup-public-surface AC).
from ._core import _parse_schema as parse_schema
from ._core import _tier2_backend_label as tier2_backend_label

# SSO web-session cookie family — a second consumer-resolution family alongside
# the token ``creds`` family above. Resolves a captured SSO session to an on-disk
# cookie-jar path via the unchanged ``sso-broker.py`` engine, with reusable
# validation primitives for the consumer's ``sso-config.toml`` and the load-time
# cookie-domain confinement. Imported eagerly: ``_sso`` is stdlib-only, so it
# keeps the base import graph free of any third-party dependency.
from ._sso import (
    SsoBrokerNotInstalledError,
    SsoConfigError,
    SsoError,
    SsoSessionUnavailableError,
    domain_in_cookie_domains,
    filter_jar_to_domains,
    load_sso_cookies,
    require_host_in_cookie_domains,
    validate_https_url,
    validate_root_relative_endpoint,
)

__version__ = "0.2.0"

__all__ = [
    # Resolver + container.
    "load_credentials",
    "Credentials",
    # Exceptions.
    "CredentialsMissingError",
    "Tier2HardFailError",
    "PermissiveAclError",
    "SchemaError",
    "EnvParseError",
    "VaultUnavailableError",
    # Parsers / schema types / constants.
    "parse_env_file",
    "parse_schema",
    "CredsSchema",
    "KeyDef",
    "DOTFILE_MAX_BYTES",
    # Tier-2 introspection.
    "tier2_backend_label",
    # Write API (T8) — per-tier writes for the interactive credential-setup skill.
    "keyring_available",
    "store_in_keyring",
    "store_in_dotfile",
    "crypto_available",
    "source_vault_master",
    "store_vault_master",
    "store_in_vault",
    # SSO web-session cookie family.
    "load_sso_cookies",
    "SsoError",
    "SsoBrokerNotInstalledError",
    "SsoSessionUnavailableError",
    "SsoConfigError",
    # SSO confinement primitives (security-control surface).
    "validate_https_url",
    "validate_root_relative_endpoint",
    "domain_in_cookie_domains",
    "filter_jar_to_domains",
    "require_host_in_cookie_domains",
    "__version__",
]
