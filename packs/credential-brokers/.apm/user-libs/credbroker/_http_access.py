"""Target-bound HTTP access resolution for HTTPS catalogue acquisition.

This module resolves a provider for a given HTTPS target URL and environment
mapping, returning exactly one of four immutable result variants:
``BearerHttpAccess``, ``JfrogCliHttpAccess``, ``NetrcHttpAccess``, or
``AnonymousHttpAccess``.

Selection proceeds in fixed order — bearer, JFrog CLI, .netrc, anonymous —
stopping at the first available provider. A configured-but-broken provider
raises ``HttpAccessError`` rather than falling through.

The target URL is validated once before any provider is evaluated. An invalid
target raises ``HttpAccessError`` with provider class ``"target"`` and code
``"invalid_target_host"`` before provider selection begins.

No network I/O occurs during resolution. The supplied ``env`` mapping is the
only credential source; os.environ is never read.
"""

from __future__ import annotations

import ipaddress
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import ClassVar
from urllib.parse import urlsplit

# ── Closed code set ───────────────────────────────────────────────────────────

# Every code an HttpAccessError may carry. Constructing one with a code outside
# this set raises ValueError at construction time.
VALID_CODES: frozenset[str] = frozenset(
    {
        "invalid_bearer",
        "jfrog_discovery_failed",
        "jfrog_discovery_timeout",
        "jfrog_discovery_too_large",
        "jfrog_discovery_malformed",
        "jfrog_profile_ambiguous",
        "jfrog_profile_mismatch",
        "unsupported_jfrog_topology",
        "incompatible_jfrog_cli",
        "jfrog_probe_too_large",
        "jfrog_probe_timeout",
        "jfrog_probe_failed",
        "jfrog_cli_not_executable",
        "invalid_target_host",
        "netrc_unreadable",
        "netrc_unsafe",
        "netrc_malformed",
        "netrc_incomplete",
    }
)


# ── Error ─────────────────────────────────────────────────────────────────────


class HttpAccessError(Exception):
    """Terminal error from HTTP access resolution.

    Carries only a stable, non-secret provider class and failure code.
    The message is built exclusively from those two fields; no input value
    ever reaches exception text, repr, or args.

    Attributes:
        provider: Provider class: one of "target", "bearer", "jfrog", "netrc".
        code: Stable failure code from the closed ``VALID_CODES`` set.
    """

    def __init__(self, provider: str, code: str) -> None:
        if code not in VALID_CODES:
            raise ValueError(
                f"Unknown HttpAccessError code: {code!r}; "
                f"must be one of the VALID_CODES set"
            )
        self.provider: str = provider
        self.code: str = code
        # Fixed message text — provider and code only, never any input value.
        super().__init__(
            f"HTTP access resolution failed: provider={provider!r} code={code!r}"
        )

    def __repr__(self) -> str:
        return f"HttpAccessError(provider={self.provider!r}, code={self.code!r})"

    def __str__(self) -> str:
        return (
            f"HTTP access resolution failed: "
            f"provider={self.provider!r} code={self.code!r}"
        )


# ── Result variants ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BearerHttpAccess:
    """HTTP access via an explicit bearer token.

    The token is carried only as the full ``Authorization`` header value; it
    never appears in ``repr`` or ``str``.

    Attributes:
        origin: Normalized HTTPS origin the bearer token is bound to
            (e.g. ``"https://catalogue.example.test"``).
        authorization: Full ``Authorization`` header value, e.g.
            ``"Bearer <token>"``. Never shown in repr.
    """

    provider: ClassVar[str] = "bearer"
    origin: str
    authorization: str = field(repr=False)


@dataclass(frozen=True)
class NetrcHttpAccess:
    """HTTP access via a .netrc credential.

    The derived authorization header value never appears in ``repr`` or
    ``str``.

    Attributes:
        origin: Normalized HTTPS origin the .netrc credential is bound to.
        authorization: Full ``Authorization`` header value derived from the
            .netrc entry. Never shown in repr.
    """

    provider: ClassVar[str] = "netrc"
    origin: str
    authorization: str = field(repr=False)


@dataclass(frozen=True)
class JfrogCliHttpAccess:
    """HTTP access via JFrog CLI delegation.

    Discovery selects the JFrog CLI server profile whose Artifactory URL
    is the unique longest prefix of the target URL.

    Attributes:
        server_id: The JFrog CLI server profile ID selected for this target.
            Never shown in repr (server IDs must not appear in diagnostics).
        platform_url: JFrog platform base URL.
        artifactory_url: JFrog Artifactory base URL.
    """

    provider: ClassVar[str] = "jfrog"
    server_id: str = field(repr=False)
    platform_url: str
    artifactory_url: str


@dataclass(frozen=True)
class AnonymousHttpAccess:
    """Anonymous HTTP access — no credentials.

    Attributes:
        origin: Normalized HTTPS origin.
    """

    provider: ClassVar[str] = "anonymous"
    origin: str


# Union of all four result variants for type annotations.
HttpAccess = BearerHttpAccess | NetrcHttpAccess | JfrogCliHttpAccess | AnonymousHttpAccess


# ── Host normalization ────────────────────────────────────────────────────────


_ASCII_UPPER_TO_LOWER = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"
)


def _raw_hostname(netloc: str) -> str:
    """Return the host part of ``netloc`` exactly as written.

    ``urlsplit(...).hostname`` applies ``str.lower()``, which folds non-ASCII
    letters before the IDNA codec sees them, so the host is taken from the
    netloc directly: user info and port are removed, IPv6 brackets stripped.
    """
    hostport = netloc.rpartition("@")[2]
    if hostport.startswith("["):
        return hostport[1:].partition("]")[0]
    return hostport.partition(":")[0]


def _normalize_host(hostname: str) -> str:
    """Normalize a hostname to its ASCII IDNA form.

    IP literals (IPv4 and IPv6) are returned in canonical form without
    IDNA encoding. Other hostnames are ASCII-lowercased then IDNA-encoded
    under the stdlib's IDNA codec (IDNA2003 via ``encodings.idna``).

    IPv6 addresses are returned bracketed, ready for an origin string.

    Raises:
        UnicodeError: The hostname cannot be IDNA-encoded (e.g. a label
            longer than 63 characters, or a host the codec rejects).
    """
    # Attempt IPv4 or IPv6 address parsing.
    try:
        addr = ipaddress.ip_address(hostname)
        if isinstance(addr, ipaddress.IPv6Address):
            # Reconstruct the bracketed form for use in an origin string.
            return f"[{str(addr)}]"
        # IPv4: return the canonical decimal dotted form, already lowercase.
        return str(addr)
    except ValueError:
        pass

    # Hostname: ASCII-lowercase only (str.lower() would also fold non-ASCII
    # letters, which is the codec's job), then IDNA-encode label by label.
    ascii_lowered = hostname.translate(_ASCII_UPPER_TO_LOWER)
    try:
        return ascii_lowered.encode("idna").decode("ascii")
    except (UnicodeError, UnicodeDecodeError, UnicodeEncodeError) as exc:
        raise UnicodeError(
            f"hostname cannot be IDNA-encoded: {exc}"
        ) from exc


# ── Provider functions ────────────────────────────────────────────────────────


def _bearer_provider(
    origin: str, env: Mapping[str, str]
) -> BearerHttpAccess | None:
    """Resolve bearer-token access from the supplied environment mapping.

    Reads only ``AGENTBUNDLE_HTTP_BEARER_TOKEN``. Returns ``None`` when the
    key is absent or empty (unavailable). Raises ``HttpAccessError`` with code
    ``"invalid_bearer"`` when the token is present but contains a character
    outside visible ASCII (U+0021–U+007E); this is configured-but-broken and
    terminates resolution without falling through to lower providers.
    """
    token = env.get("AGENTBUNDLE_HTTP_BEARER_TOKEN", "")
    if not token:
        return None
    # Visible ASCII: 0x21 (!) through 0x7E (~), inclusive.
    if not all(0x21 <= ord(c) <= 0x7E for c in token):
        raise HttpAccessError("bearer", "invalid_bearer")
    return BearerHttpAccess(origin=origin, authorization="Bearer " + token)


def _jfrog_provider(
    origin: str, env: Mapping[str, str]
) -> JfrogCliHttpAccess | None:
    """Placeholder: JFrog CLI provider not yet implemented.

    Returns ``None`` unconditionally until non-secret profile discovery and
    version validation are implemented.
    """
    return None  # unavailable until JFrog discovery lands


def _netrc_provider(
    origin: str, env: Mapping[str, str]
) -> NetrcHttpAccess | None:
    """Placeholder: .netrc provider not yet implemented.

    Returns ``None`` unconditionally until exact-machine .netrc lookup and
    origin binding are implemented.
    """
    return None  # unavailable until .netrc lookup lands


def _anonymous_provider(origin: str) -> AnonymousHttpAccess:
    """Return anonymous access for the given origin."""
    return AnonymousHttpAccess(origin=origin)


# ── Public resolver ───────────────────────────────────────────────────────────


def resolve_http_access(
    target_url: str, *, env: Mapping[str, str]
) -> HttpAccess:
    """Resolve target-bound HTTP access for an HTTPS catalogue URL.

    Validates the target URL first (before any provider is evaluated), then
    selects the first available provider in fixed order: bearer, JFrog CLI,
    .netrc, anonymous.

    The result is bound to the normalized HTTPS origin derived from
    ``target_url``; the same result is reused for the descriptor and its
    resolved archive.

    Args:
        target_url: The initial HTTPS catalogue URL. Must be HTTPS, have a
            host, carry no user info, and use a valid port.
        env: Environment mapping used as the sole credential source. Never
            reads ``os.environ``; pass a controlled mapping (or ``{}`` for
            no-credential resolution).

    Returns:
        One of ``BearerHttpAccess``, ``JfrogCliHttpAccess``,
        ``NetrcHttpAccess``, or ``AnonymousHttpAccess``.

    Raises:
        HttpAccessError: The target URL is invalid (provider ``"target"``,
            code ``"invalid_target_host"``), or a configured provider is
            broken (provider ``"bearer"``, ``"jfrog"``, or ``"netrc"`` with
            the applicable code).
    """
    # ── Target check ─────────────────────────────────────────────────────────
    # Performed before any provider is evaluated; a bad target is a caller
    # error, not a provider error.

    try:
        parsed = urlsplit(target_url)
    except Exception:
        raise HttpAccessError("target", "invalid_target_host") from None

    if parsed.scheme != "https":
        raise HttpAccessError("target", "invalid_target_host")

    # Empty string means no host.
    hostname = _raw_hostname(parsed.netloc)
    if not hostname:
        raise HttpAccessError("target", "invalid_target_host")

    # Reject any user info embedded in the URL.
    if parsed.username is not None or parsed.password is not None:
        raise HttpAccessError("target", "invalid_target_host")

    # Port: None means "not present"; a ValueError means malformed.
    try:
        port = parsed.port
    except ValueError:
        raise HttpAccessError("target", "invalid_target_host") from None

    # Normalize the host under the single profile (IDNA2003 via stdlib codec).
    try:
        normalized_host = _normalize_host(hostname)
    except UnicodeError:
        raise HttpAccessError("target", "invalid_target_host") from None

    # ── Origin string ─────────────────────────────────────────────────────────
    # Omit the port when it is the HTTPS default (443).
    if port is not None and port != 443:
        origin = f"https://{normalized_host}:{port}"
    else:
        origin = f"https://{normalized_host}"

    # ── Provider selection ────────────────────────────────────────────────────
    # Fixed order: bearer → JFrog CLI → .netrc → anonymous. Each function is
    # referenced by module-global name so monkeypatching in tests replaces the
    # live lookup without requiring a list-entry update. Anonymous is
    # always the floor.
    #
    # A provider returning None means "unavailable — try the next one."
    # A provider raising HttpAccessError means "configured but broken —
    # stop selection and propagate the error."
    result: HttpAccess | None = _bearer_provider(origin, env)
    if result is not None:
        return result

    result = _jfrog_provider(origin, env)
    if result is not None:
        return result

    result = _netrc_provider(origin, env)
    if result is not None:
        return result

    return _anonymous_provider(origin)
