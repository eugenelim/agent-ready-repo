"""credbroker — a standalone, pip-installable credential resolver.

RFC-0023 replaces the build-projected ``credentials_shim`` (byte-copied into
every credentialed skill's ``scripts/`` by the build pipeline) with this
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
    load_credentials,
    parse_env_file,
)

# Public replacements for the private shim symbols ``credential-setup`` consumed
# (``_parse_schema`` / ``_tier2_backend_label``) so it imports no
# underscore-prefixed name (spec: credential-setup-public-surface AC). The
# credential *write* API that replaces ``_dotfile_write`` arrives with the vault
# (spec task T4); the deeper credential-setup wiring lands in T8.
from ._core import _parse_schema as parse_schema
from ._core import _tier2_backend_label as tier2_backend_label

__version__ = "0.1.0"

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
    "__version__",
]
