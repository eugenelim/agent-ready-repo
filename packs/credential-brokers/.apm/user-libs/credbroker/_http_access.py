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

import base64
import contextlib
import io
import ipaddress
import netrc as _netrc_module
import os
import stat
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
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


# ── .netrc helpers ───────────────────────────────────────────────────────────

# Maximum bytes read from a .netrc file; files over this limit are rejected
# as unreadable rather than potentially exhausting memory.
_NETRC_MAX_BYTES: int = 1 << 20  # 1 MiB


class _StringNetrc(_netrc_module.netrc):
    """Parse .netrc content from an in-memory string without re-opening the file.

    Subclasses stdlib ``netrc.netrc`` to call ``_parse`` on a ``StringIO``
    object, bypassing the constructor's ``open(file)`` call.  Passes
    ``default_netrc=False`` so the stdlib's own permission check is skipped;
    the caller performs that check directly on the open file descriptor.
    """

    def __init__(self, text: str) -> None:
        self.hosts: dict = {}
        self.macros: dict = {}
        self._parse("<netrc>", io.StringIO(text), False)  # type: ignore[attr-defined]


def _split_netrc_key(key: str) -> tuple[str, str | None]:
    """Split a .netrc machine key into a raw host string and optional port string.

    For a key of the form ``host:NNN`` where *NNN* is all decimal digits,
    returns ``(host, "NNN")``.  For an IPv6 bracketed form ``[addr]:NNN``,
    returns ``("[addr]", "NNN")``.  Otherwise returns ``(key, None)``.
    """
    if key.startswith("["):
        bracket_end = key.find("]")
        if bracket_end < 0:
            return key, None
        host_part = key[:bracket_end + 1]
        rest = key[bracket_end + 1:]
        if rest.startswith(":") and len(rest) > 1 and rest[1:].isdigit():
            return host_part, rest[1:]
        return key, None
    last_colon = key.rfind(":")
    if last_colon >= 0:
        port_str = key[last_colon + 1:]
        if port_str and port_str.isdigit():
            return key[:last_colon], port_str
    return key, None


def _normalize_netrc_host(raw_host: str) -> str:
    """Normalize a raw host string from a .netrc key under the single host profile.

    IPv6 addresses in bracketed notation have their brackets stripped before
    ``_normalize_host`` is called; ``_normalize_host`` adds them back.

    Raises:
        UnicodeError: The host cannot be IDNA-encoded.
    """
    if raw_host.startswith("[") and raw_host.endswith("]"):
        return _normalize_host(raw_host[1:-1])
    return _normalize_host(raw_host)


def _resolve_home_dir(
    env: Mapping[str, str], *, _os_name: str | None = None
) -> str | None:
    """Resolve the user home directory from the supplied ``env`` mapping.

    Uses platform-appropriate precedence — ``HOME`` on POSIX;
    ``USERPROFILE`` then ``HOMEDRIVE``+``HOMEPATH`` on Windows — so that
    ``expanduser`` is never called and the supplied mapping is the only
    credential source.

    Args:
        env: Environment mapping to consult.  ``os.environ`` is never read.
        _os_name: Override for ``os.name``; used in tests to exercise the
            Windows branch on POSIX without real platform changes.

    Returns:
        The home directory string, or ``None`` when none can be resolved.
    """
    name = _os_name if _os_name is not None else os.name
    if name == "nt":
        home: str | None = env.get("USERPROFILE") or None
        if not home:
            drive = env.get("HOMEDRIVE", "")
            path_part = env.get("HOMEPATH", "")
            home = (drive + path_part) or None
        return home
    return env.get("HOME") or None


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
    """Resolve .netrc Basic-auth access for *origin* from the standard user file.

    Reads only the standard per-user ``.netrc`` location derived from the
    supplied ``env`` mapping (``HOME`` on POSIX; ``USERPROFILE`` then
    ``HOMEDRIVE``+``HOMEPATH`` on Windows).  Never reads ``os.environ``.

    Returns ``None`` (unavailable) when no home directory can be resolved,
    the file is absent, or no exact machine key matches the target.  Raises
    ``HttpAccessError`` for configured-but-broken conditions:

    - ``netrc_unreadable``: file present but not a regular file, or any
      ``OSError`` on open or read, or file exceeds the 1 MiB bound.
    - ``netrc_unsafe`` (POSIX only): unsafe group/other permission bits or
      owner mismatch.
    - ``netrc_malformed``: UTF-8 decode failure, parse error, unencodable
      machine key, ambiguous normalized key, a login containing ``:``, or a
      control character in either value.
    - ``netrc_incomplete``: matched record lacks login or password.

    No input value (path, machine name, login, password, or file content)
    ever reaches exception text, args, repr, or logs; all exception chains
    are suppressed via ``from None``.
    """
    # 1. Home directory from env only — never os.environ or expanduser.
    home = _resolve_home_dir(env)
    if not home:
        return None

    # 2. Standard user .netrc path only; never a working-directory or input path.
    netrc_path = Path(home) / ".netrc"

    # 3. Open once; use os.fstat to check the open fd, avoiding TOCTOU races.
    try:
        fd = os.open(str(netrc_path), os.O_RDONLY)
    except FileNotFoundError:
        return None  # Absent → unavailable.
    except OSError:
        raise HttpAccessError("netrc", "netrc_unreadable") from None

    try:
        try:
            st = os.fstat(fd)
        except OSError:
            raise HttpAccessError("netrc", "netrc_unreadable") from None

        # Not a regular file (e.g. a directory named .netrc) → unreadable.
        if not stat.S_ISREG(st.st_mode):
            raise HttpAccessError("netrc", "netrc_unreadable") from None

        # POSIX permissions: any group/other bit or wrong owner → unsafe.
        # Windows has no comparable permission bits, so it skips this check.
        if os.name != "nt" and ((st.st_mode & 0o077) or st.st_uid != os.getuid()):
            raise HttpAccessError("netrc", "netrc_unsafe") from None

        # Bounded read: reject files over 1 MiB so a hostile file cannot
        # exhaust memory.
        try:
            raw = os.read(fd, _NETRC_MAX_BYTES + 1)
        except OSError:
            raise HttpAccessError("netrc", "netrc_unreadable") from None

        if len(raw) > _NETRC_MAX_BYTES:
            raise HttpAccessError("netrc", "netrc_unreadable") from None
    finally:
        with contextlib.suppress(OSError):
            os.close(fd)

    # 4. Decode as UTF-8; a decode error means the file is malformed.
    try:
        content = raw.decode("utf-8")
    except (UnicodeDecodeError, ValueError):
        raise HttpAccessError("netrc", "netrc_malformed") from None

    # 5. Parse with the stdlib netrc parser via _StringNetrc, which does not
    # re-open the file.  NetrcParseError → malformed; suppress context so
    # parser text (which may include file lines) never surfaces.
    try:
        parsed = _StringNetrc(content)
    except _netrc_module.NetrcParseError:
        raise HttpAccessError("netrc", "netrc_malformed") from None
    except HttpAccessError:
        raise
    except Exception:
        raise HttpAccessError("netrc", "netrc_malformed") from None

    # 6. Build a mapping from normalized key to (login, password), skipping
    # "default" entries, which never authenticate.  Two raw keys that normalize to the
    # same key with different credentials → ambiguous → malformed.
    normalized_map: dict[str, tuple[str, str]] = {}
    for raw_key, (login, _account, password) in parsed.hosts.items():
        if raw_key == "default":
            continue
        raw_host_str, port_str = _split_netrc_key(raw_key)
        try:
            norm_host = _normalize_netrc_host(raw_host_str)
        except UnicodeError:
            raise HttpAccessError("netrc", "netrc_malformed") from None
        norm_key = f"{norm_host}:{port_str}" if port_str else norm_host
        new_creds = (login or "", password or "")
        if norm_key in normalized_map and normalized_map[norm_key] != new_creds:
            raise HttpAccessError("netrc", "netrc_malformed") from None
        normalized_map[norm_key] = new_creds

    # 7. Derive lookup keys from the already-normalized origin: host:port first
    # for a non-default port, then host; host only for 443.
    # The origin is "https://<host>[:port]" with the host already normalized
    # (IPv6 bracketed, as the .netrc keys above are), and 443 never present.
    host_port = origin[len("https://"):]
    target_host, target_port = _split_netrc_key(host_port)
    lookup_keys = [host_port, target_host] if target_port else [target_host]

    match: tuple[str, str] | None = None
    for key in lookup_keys:
        if key in normalized_map:
            match = normalized_map[key]
            break

    if match is None:
        return None  # No exact match → unavailable.

    login, password = match

    # 8. Validate the matched record: login and password are both required.
    if not login or not password:
        raise HttpAccessError("netrc", "netrc_incomplete") from None

    # A colon in the login cannot form a safe Basic credential.
    if ":" in login:
        raise HttpAccessError("netrc", "netrc_malformed") from None

    # Control characters in either value (U+0000–U+001F and U+007F).
    for ch in login + password:
        cp = ord(ch)
        if cp < 0x20 or cp == 0x7F:
            raise HttpAccessError("netrc", "netrc_malformed") from None

    # 9. Derive the Basic authorization value and bind it to the origin.
    user_pass_bytes = f"{login}:{password}".encode()
    authorization = "Basic " + base64.b64encode(user_pass_bytes).decode("ascii")
    return NetrcHttpAccess(origin=origin, authorization=authorization)


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
