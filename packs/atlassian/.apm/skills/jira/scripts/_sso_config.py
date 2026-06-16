"""SSO config loader + ``auth_default`` selector (RFC-0035; spec task T3).

Reads ``references/sso-config.toml``, validates the ``[sso]`` connection params
with the shared ``credbroker`` confinement primitives, and decides the auth path.
The *schema* (the ``[sso]`` key set) is consumer-specific and lives here; the
security *primitives* it calls (https-only / root-relative guards) are
single-sourced in ``credbroker`` so they cannot drift between consumers.

The selector is the return value: ``None`` means the ``creds`` (token) path —
returned when the file is absent or ``auth_default = "creds"`` — and an
:class:`SsoConfig` means the SSO-cookie path. When ``auth_default = "sso-cookie"``
the ``[sso]`` table is validated and a malformed value raises (fail closed; never
downgrade to ``creds``).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

# The atlassian ``[sso]`` connection-param schema. The structural lint
# (``tools/lint-sso-config.py``) pins this key set; keep the two in sync.
_ALLOWED_SSO_KEYS = frozenset(
    {
        "profile",
        "base_url",
        "login_url",
        "success_url_pattern",
        "cookie_domains",
        "validation_endpoint",
        "session_filename",
        "ttl_hint_minutes",
    }
)
_REQUIRED_SSO_KEYS = frozenset(
    {
        "profile",
        "base_url",
        "login_url",
        "success_url_pattern",
        "cookie_domains",
        "validation_endpoint",
    }
)

_DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent / "references" / "sso-config.toml"
)


@dataclass(frozen=True)
class SsoConfig:
    """Validated ``[sso]`` connection config for the cookie path."""

    profile: str
    base_url: str
    login_url: str
    success_url_pattern: str
    cookie_domains: tuple[str, ...]
    validation_endpoint: str
    session_filename: str | None = None
    ttl_hint_minutes: int | None = None


def load_sso_config(config_path: Path | None = None) -> SsoConfig | None:
    """Resolve the auth path from ``sso-config.toml``.

    :returns: ``None`` for the ``creds`` (token) path (file absent or
        ``auth_default = "creds"``); an :class:`SsoConfig` for the SSO-cookie path.
    :raises credbroker.SsoConfigError: ``auth_default = "sso-cookie"`` but the
        ``[sso]`` table is missing, has unknown/missing keys, or carries a
        non-``https`` URL or non-root-relative endpoint (fail closed).
    """
    path = config_path or _DEFAULT_CONFIG_PATH
    if not path.is_file():
        return None
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("auth_default", "creds") != "sso-cookie":
        return None

    # Imported here (not at module top) so the credbroker user-scope floor the
    # skill bootstrap appends to sys.path is in place before resolution.
    from credbroker import (
        SsoConfigError,
        validate_https_url,
        validate_root_relative_endpoint,
    )

    sso = data.get("sso")
    if not isinstance(sso, dict):
        raise SsoConfigError(
            "auth_default = 'sso-cookie' but the [sso] table is missing"
        )

    unknown = set(sso) - _ALLOWED_SSO_KEYS
    if unknown:
        raise SsoConfigError(f"unknown [sso] keys: {sorted(unknown)}")
    missing = _REQUIRED_SSO_KEYS - set(sso)
    if missing:
        raise SsoConfigError(f"missing required [sso] keys: {sorted(missing)}")

    validate_https_url(sso["base_url"], field="base_url")
    validate_https_url(sso["login_url"], field="login_url")
    validate_https_url(sso["success_url_pattern"], field="success_url_pattern")
    validate_root_relative_endpoint(
        sso["validation_endpoint"], field="validation_endpoint"
    )

    domains = sso["cookie_domains"]
    if (
        not isinstance(domains, list)
        or not domains
        or not all(isinstance(d, str) for d in domains)
    ):
        raise SsoConfigError("cookie_domains must be a non-empty list of strings")

    return SsoConfig(
        profile=str(sso["profile"]),
        base_url=sso["base_url"],
        login_url=sso["login_url"],
        success_url_pattern=sso["success_url_pattern"],
        cookie_domains=tuple(domains),
        validation_endpoint=sso["validation_endpoint"],
        session_filename=sso.get("session_filename"),
        ttl_hint_minutes=sso.get("ttl_hint_minutes"),
    )
