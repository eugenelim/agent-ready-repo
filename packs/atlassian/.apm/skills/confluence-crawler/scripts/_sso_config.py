"""SSO config loader + ``auth_default`` selector.

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
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import urlsplit

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

# Scalar `[sso]` string fields that can reach an engine argv or the engine's
# profile writer. `profile` is not here — it has its own grammar, which is
# strictly narrower.
_FORWARDED_STRING_KEYS = (
    "base_url",
    "login_url",
    "success_url_pattern",
    "validation_endpoint",
    "session_filename",
)

# Characters a TOML basic string cannot carry literally, which is what the
# engine writes profile values into. The whole C0 range plus DEL, not just
# `\n` / `\r` / `\t`: a TOML source can encode any of them as `\uXXXX`, so the
# parsed value carries the bare character with no literal backslash to notice.
_UNFORWARDABLE = frozenset(
    {'"', "\\"} | {chr(c) for c in range(0x20)} | {chr(0x7F)}
)


def _reject_unforwardable(value: object, *, field: str, error: type[Exception]) -> None:
    """Fail closed unless *value* is a string safe to forward to the engine.

    Two consumers downstream cannot defend themselves: ``urlsplit`` strips CR/LF
    before parsing, so the https guard cannot see them, and the engine writes
    values into a quoted TOML string.
    """
    if not isinstance(value, str):
        raise error(f"{field} must be a string, got {type(value).__name__}")
    for ch in value:
        if ch in _UNFORWARDABLE:
            raise error(
                f"{field} carries U+{ord(ch):04X}, which cannot be safely "
                f"forwarded to the SSO broker"
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
        domain_in_cookie_domains,
        validate_https_url,
        validate_root_relative_endpoint,
        validate_sso_profile,
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

    # Before any other check, and before any `str()` coercion: a `str()` here
    # would turn an int `5` into `"5"` and make the grammar's non-str rejection
    # unreachable from this path.
    validate_sso_profile(sso["profile"])

    # Every string field that can reach an argv or the engine's profile writer.
    # Runs before the URL guards because `urlsplit` strips CR/LF before parsing,
    # so `validate_https_url` structurally cannot see them — while the engine
    # interpolates the value into `key = "value"`, where a newline injects a
    # line into the profile store.
    for field in _FORWARDED_STRING_KEYS:
        value = sso.get(field)
        if value is None:
            continue
        _reject_unforwardable(value, field=field, error=SsoConfigError)
    for index, domain in enumerate(sso.get("cookie_domains") or []):
        if isinstance(domain, str):
            _reject_unforwardable(
                domain, field=f"cookie_domains[{index}]", error=SsoConfigError
            )

    # `int | None` in the annotation but passed through untyped, so a string
    # reached the argv builder and then `--ttl-hint-minutes`. `bool` is excluded
    # explicitly: `isinstance(True, int)` is True in Python, and a bool is not a
    # duration.
    ttl = sso.get("ttl_hint_minutes")
    if ttl is not None and (isinstance(ttl, bool) or not isinstance(ttl, int)):
        raise SsoConfigError(
            f"ttl_hint_minutes must be an integer, got {type(ttl).__name__}"
        )

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
    # Reject a dangerously broad confinement set: a single-label domain (no dot,
    # e.g. "com") would admit the over-broad captured jar against any corporate
    # host. The instance domain must have at least one label boundary.
    for dom in domains:
        if "." not in dom.strip("."):
            raise SsoConfigError(
                f"cookie_domains entry {dom!r} is too broad (single-label); "
                f"declare the instance domain (e.g. corp.example.com)"
            )
    # The base host must itself be within cookie_domains — the runtime client
    # also checks this, but pinning it at load fails a typo'd config closed early.
    base_host = urlsplit(sso["base_url"]).hostname or ""
    if not domain_in_cookie_domains(base_host, domains):
        raise SsoConfigError(
            f"base_url host {base_host!r} is not within cookie_domains {domains!r}"
        )

    # session_filename is forwarded to `sso-broker register --session-filename`;
    # confine it to a bare filename so an adopter-supplied value can't seed a
    # path-traversal into the broker's store.
    session_filename = sso.get("session_filename")
    if session_filename is not None:
        bad = (
            session_filename in ("", ".", "..")
            or "/" in session_filename
            or "\\" in session_filename
            or PurePosixPath(session_filename).name != session_filename
            or PureWindowsPath(session_filename).name != session_filename
        )
        if bad:
            raise SsoConfigError(
                f"session_filename must be a bare filename (no path separators): "
                f"{session_filename!r}"
            )

    return SsoConfig(
        profile=sso["profile"],
        base_url=sso["base_url"],
        login_url=sso["login_url"],
        success_url_pattern=sso["success_url_pattern"],
        cookie_domains=tuple(domains),
        validation_endpoint=sso["validation_endpoint"],
        session_filename=session_filename,
        ttl_hint_minutes=sso.get("ttl_hint_minutes"),
    )


def _select_auth_path(
    config_path: Path | None = None,
) -> tuple[str, SsoConfig | None]:
    """Resolve the auth path and return a typed selector tuple.

    :returns: ``("token", None)`` when :func:`load_sso_config` returns ``None``
        (config absent or ``auth_default = "creds"``); ``("sso-cookie", sso_config)``
        when an :class:`SsoConfig` is returned (valid ``auth_default = "sso-cookie"``).
    :raises: any exception from :func:`load_sso_config` is propagated unchanged —
        the caller maps this to ``EXIT_USER_ACTION``.
    """
    sso_config = load_sso_config(config_path)
    if sso_config is not None:
        return ("sso-cookie", sso_config)
    return ("token", None)
