# STUB: AC-0004 — the resolver returns the public anonymous result variant
from credbroker import AnonymousHttpAccess, resolve_http_access


def test_resolve_http_access_returns_public_anonymous_variant() -> None:
    result = resolve_http_access("https://catalogue.example.test/root/catalogue.toml", env={})

    assert isinstance(result, AnonymousHttpAccess)
    assert result.provider == "anonymous"
    assert result.origin == "https://catalogue.example.test"


# ── Additional T1 tests ───────────────────────────────────────────────────────

import socket  # noqa: E402
from collections.abc import Mapping  # noqa: E402

import credbroker  # noqa: E402
import pytest  # noqa: E402
from credbroker import (  # noqa: E402
    BearerHttpAccess,
    HttpAccessError,
    JfrogCliHttpAccess,
    NetrcHttpAccess,
)
from credbroker._http_access import VALID_CODES, _normalize_host  # noqa: E402

# ── Public surface: six new names ─────────────────────────────────────────────


NEW_NAMES = [
    "resolve_http_access",
    "HttpAccessError",
    "BearerHttpAccess",
    "NetrcHttpAccess",
    "JfrogCliHttpAccess",
    "AnonymousHttpAccess",
]


def test_six_new_names_in_module() -> None:
    """All six new names are importable from credbroker. AC-0004"""
    for name in NEW_NAMES:
        assert hasattr(credbroker, name), f"missing public name: {name}"


def test_six_new_names_in_all() -> None:
    """All six new names appear in credbroker.__all__. AC-0004"""
    for name in NEW_NAMES:
        assert name in credbroker.__all__, f"{name} not in credbroker.__all__"


def test_no_underscore_names_added_to_all() -> None:
    """The new names added to __all__ are not underscore-prefixed."""
    for name in NEW_NAMES:
        assert not name.startswith("_"), f"unexpected underscore name: {name}"


# ── Frozen dataclass invariants ───────────────────────────────────────────────


def test_bearer_access_is_frozen() -> None:
    """BearerHttpAccess is immutable after construction. AC-0004"""
    acc = BearerHttpAccess(origin="https://example.test", authorization="Bearer tok")
    with pytest.raises((AttributeError, TypeError)):
        acc.origin = "https://other.test"  # type: ignore[misc]


def test_netrc_access_is_frozen() -> None:
    """NetrcHttpAccess is immutable after construction."""
    acc = NetrcHttpAccess(origin="https://example.test", authorization="Basic abc")
    with pytest.raises((AttributeError, TypeError)):
        acc.origin = "https://other.test"  # type: ignore[misc]


def test_jfrog_access_is_frozen() -> None:
    """JfrogCliHttpAccess is immutable after construction."""
    acc = JfrogCliHttpAccess(
        server_id="sid",
        platform_url="https://platform.test/",
        artifactory_url="https://platform.test/artifactory/",
    )
    with pytest.raises((AttributeError, TypeError)):
        acc.platform_url = "https://other.test/"  # type: ignore[misc]


def test_anonymous_access_is_frozen() -> None:
    """AnonymousHttpAccess is immutable after construction."""
    acc = AnonymousHttpAccess(origin="https://example.test")
    with pytest.raises((AttributeError, TypeError)):
        acc.origin = "https://other.test"  # type: ignore[misc]


def test_all_variants_expose_provider_literal() -> None:
    """Each variant exposes the correct provider string. AC-0004"""
    bearer = BearerHttpAccess(
        origin="https://example.test", authorization="Bearer tok"
    )
    netrc = NetrcHttpAccess(
        origin="https://example.test", authorization="Basic abc"
    )
    jfrog = JfrogCliHttpAccess(
        server_id="sid",
        platform_url="https://platform.test/",
        artifactory_url="https://platform.test/artifactory/",
    )
    anon = AnonymousHttpAccess(origin="https://example.test")

    assert bearer.provider == "bearer"
    assert netrc.provider == "netrc"
    assert jfrog.provider == "jfrog"
    assert anon.provider == "anonymous"


def test_provider_not_settable_on_instance() -> None:
    """provider is a ClassVar and cannot be overridden on a frozen instance."""
    acc = AnonymousHttpAccess(origin="https://example.test")
    with pytest.raises((AttributeError, TypeError)):
        acc.provider = "other"  # type: ignore[misc]


def test_authorization_absent_from_repr() -> None:
    """Bearer authorization never appears in repr. AC-0015"""
    canary = "supersecret-canary-token-99"
    acc = BearerHttpAccess(
        origin="https://example.test", authorization=f"Bearer {canary}"
    )
    assert canary not in repr(acc)
    assert canary not in str(acc)


def test_netrc_authorization_absent_from_repr() -> None:
    """NetrcHttpAccess authorization never appears in repr. AC-0015"""
    canary = "netrc-canary-password-88"
    acc = NetrcHttpAccess(
        origin="https://example.test", authorization=f"Basic {canary}"
    )
    assert canary not in repr(acc)
    assert canary not in str(acc)


def test_jfrog_server_id_absent_from_repr() -> None:
    """JfrogCliHttpAccess server_id never appears in repr. AC-0015"""
    canary = "jfrog-server-canary-id-77"
    acc = JfrogCliHttpAccess(
        server_id=canary,
        platform_url="https://platform.test/",
        artifactory_url="https://platform.test/artifactory/",
    )
    assert canary not in repr(acc)
    assert canary not in str(acc)


# ── HttpAccessError ───────────────────────────────────────────────────────────


def test_http_access_error_valid_code() -> None:
    """HttpAccessError with a valid code exposes provider and code. AC-0004"""
    err = HttpAccessError("target", "invalid_target_host")
    assert err.provider == "target"
    assert err.code == "invalid_target_host"


def test_http_access_error_rejects_unknown_code() -> None:
    """Constructing HttpAccessError with an unknown code raises ValueError."""
    with pytest.raises(ValueError):
        HttpAccessError("target", "not_a_real_code_xyzzy")


def test_http_access_error_message_has_no_input_data() -> None:
    """HttpAccessError message uses only provider and code. AC-0015"""
    err = HttpAccessError("bearer", "invalid_bearer")
    msg = str(err)
    assert "invalid_bearer" in msg
    assert "bearer" in msg


def test_http_access_error_repr_has_no_secret() -> None:
    """HttpAccessError repr exposes no credential material. AC-0015"""
    err = HttpAccessError("bearer", "invalid_bearer")
    r = repr(err)
    assert "bearer" in r
    assert "invalid_bearer" in r


def test_valid_codes_set_is_complete() -> None:
    """VALID_CODES contains all codes named in the LLD."""
    expected = {
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
    assert expected == VALID_CODES


# ── Host normalization ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "hostname, expected",
    [
        # Pure-ASCII hostname: lowercased.
        ("catalogue.example.test", "catalogue.example.test"),
        ("CATALOGUE.EXAMPLE.TEST", "catalogue.example.test"),
        ("Catalogue.Example.Test", "catalogue.example.test"),
        # IPv4 literals: returned as-is in dotted-decimal form.
        ("127.0.0.1", "127.0.0.1"),
        ("192.168.0.1", "192.168.0.1"),
        # IPv6 literals: returned in bracketed form.
        ("::1", "[::1]"),
    ],
)
def test_normalize_host_basic(hostname: str, expected: str) -> None:
    """_normalize_host lowercases and IDNA-encodes correctly."""
    assert _normalize_host(hostname) == expected


def test_normalize_host_unicode_roundtrip() -> None:
    """A Unicode host and its punycode spelling normalize to the same origin."""
    unicode_host = "münchen.example.com"
    expected = unicode_host.lower().encode("idna").decode("ascii")
    assert _normalize_host(unicode_host) == expected
    # The punycode spelling must produce the same result.
    assert _normalize_host(expected) == expected


def test_normalize_host_beta_folding() -> None:
    """ß (sharp s) folds to 'ss' under the IDNA2003 nameprep mapping. AC-0009"""
    normalized = _normalize_host("straße.example.com")
    assert "strasse" in normalized
    assert "ß" not in normalized


def test_normalize_host_matches_the_codec_the_connection_uses() -> None:
    """Only ASCII is lowercased before the codec; the codec folds the rest.

    The compared form must be the form Python connects with, which is the
    IDNA codec applied to the host as written. ``str.lower()`` would fold
    non-ASCII letters first, so the compared form is checked against the
    codec applied to the raw host. AC-0010
    """
    for raw in ("BÜCHER.Example", "İSTANBUL.example", "ẞTRASSE.example"):
        assert _normalize_host(raw) == raw.encode("idna").decode("ascii").lower()


def test_target_host_is_taken_as_written() -> None:
    """The resolver normalizes the netloc host, not urlsplit's lowered copy."""
    upper = resolve_http_access("https://BÜCHER.Example:8443/x", env={})
    lower = resolve_http_access("https://bücher.example:8443/x", env={})
    puny = resolve_http_access("https://xn--bcher-kva.example:8443/x", env={})
    assert upper.origin == lower.origin == puny.origin
    assert upper.origin == "https://xn--bcher-kva.example:8443"


def test_normalize_host_rejects_too_long_label() -> None:
    """A label longer than 63 chars raises UnicodeError."""
    long_label = "a" * 64 + ".example.com"
    with pytest.raises(UnicodeError):
        _normalize_host(long_label)


# ── Target validation ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        # Non-HTTPS scheme.
        "http://catalogue.example.test/cat.toml",
        "ftp://catalogue.example.test/cat.toml",
        # No host.
        "https:///path/to/cat.toml",
        # User info present.
        "https://user@catalogue.example.test/cat.toml",
        "https://user:pass@catalogue.example.test/cat.toml",
        # Malformed port (not a number).
        "https://catalogue.example.test:abc/cat.toml",
    ],
)
def test_target_refusals_raise_invalid_target_host(url: str) -> None:
    """Invalid target URLs raise HttpAccessError before any provider runs. AC-0006, AC-0007"""
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(url, env={})
    assert exc_info.value.provider == "target"
    assert exc_info.value.code == "invalid_target_host"


def test_target_refusal_happens_before_bearer_evaluation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid target stops resolution before bearer is evaluated. AC-0007"""
    called: list[str] = []

    def fake_bearer(origin: str, env: Mapping[str, str]) -> None:
        called.append("bearer")
        return

    monkeypatch.setattr("credbroker._http_access._bearer_provider", fake_bearer)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access("http://catalogue.example.test/cat.toml", env={})
    assert exc_info.value.code == "invalid_target_host"
    assert "bearer" not in called, "bearer provider must not run when target is invalid"


def test_https_with_valid_port_accepted() -> None:
    """HTTPS URLs with a non-default port are accepted."""
    result = resolve_http_access(
        "https://catalogue.example.test:8443/root/cat.toml", env={}
    )
    assert isinstance(result, AnonymousHttpAccess)
    assert result.origin == "https://catalogue.example.test:8443"


def test_https_port_443_dropped_from_origin() -> None:
    """Port 443 is omitted from the origin string."""
    result = resolve_http_access(
        "https://catalogue.example.test:443/root/cat.toml", env={}
    )
    assert isinstance(result, AnonymousHttpAccess)
    assert result.origin == "https://catalogue.example.test"


def test_https_loopback_accepted() -> None:
    """IPv4 loopback address is accepted as a valid HTTPS target."""
    result = resolve_http_access("https://127.0.0.1/root/cat.toml", env={})
    assert isinstance(result, AnonymousHttpAccess)
    assert result.origin == "https://127.0.0.1"


def test_unencodable_host_raises_invalid_target() -> None:
    """A host the IDNA codec rejects raises invalid_target_host. AC-0009"""
    bad_host = "a" * 64 + ".example.com"
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(f"https://{bad_host}/cat.toml", env={})
    assert exc_info.value.provider == "target"
    assert exc_info.value.code == "invalid_target_host"


# ── Bearer provider ───────────────────────────────────────────────────────────


def test_bearer_unset_yields_anonymous() -> None:
    """Absent AGENTBUNDLE_HTTP_BEARER_TOKEN falls through to anonymous. AC-0006"""
    result = resolve_http_access(
        "https://catalogue.example.test/cat.toml", env={}
    )
    assert isinstance(result, AnonymousHttpAccess)


def test_bearer_empty_string_yields_anonymous() -> None:
    """Empty AGENTBUNDLE_HTTP_BEARER_TOKEN is treated as absent. AC-0006"""
    result = resolve_http_access(
        "https://catalogue.example.test/cat.toml",
        env={"AGENTBUNDLE_HTTP_BEARER_TOKEN": ""},
    )
    assert isinstance(result, AnonymousHttpAccess)


def test_bearer_valid_token_yields_bearer_access() -> None:
    """A valid bearer token produces BearerHttpAccess with origin and header. AC-0004"""
    result = resolve_http_access(
        "https://catalogue.example.test/cat.toml",
        env={"AGENTBUNDLE_HTTP_BEARER_TOKEN": "validtoken123"},
    )
    assert isinstance(result, BearerHttpAccess)
    assert result.origin == "https://catalogue.example.test"
    assert result.authorization == "Bearer validtoken123"


def test_bearer_authorization_header_format() -> None:
    """Bearer authorization header has the 'Bearer <token>' format."""
    result = resolve_http_access(
        "https://catalogue.example.test/cat.toml",
        env={"AGENTBUNDLE_HTTP_BEARER_TOKEN": "tok-abc-123"},
    )
    assert isinstance(result, BearerHttpAccess)
    assert result.authorization.startswith("Bearer ")
    assert result.authorization == "Bearer tok-abc-123"


@pytest.mark.parametrize(
    "bad_token",
    [
        "token with space",
        "token\twith\ttab",
        "token\nwith\nnewline",
        "token\rwith\rCR",
        "token\x00with\x00NUL",
        "token\x1fwith\x1fcontrol",
        "token\x7fwith\x7fdel",
        "token\x80with\x80highbyte",
        "tökèn",  # non-ASCII
    ],
)
def test_bearer_invalid_token_raises_invalid_bearer(bad_token: str) -> None:
    """Tokens with non-visible-ASCII characters raise invalid_bearer. AC-0007"""
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://catalogue.example.test/cat.toml",
            env={"AGENTBUNDLE_HTTP_BEARER_TOKEN": bad_token},
        )
    assert exc_info.value.provider == "bearer"
    assert exc_info.value.code == "invalid_bearer"


def test_bearer_broken_blocks_lower_providers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """invalid_bearer is terminal — JFrog and .netrc providers must not run. AC-0007"""
    jfrog_called: list[str] = []
    netrc_called: list[str] = []

    def fake_jfrog(origin: str, env: Mapping[str, str]) -> None:
        jfrog_called.append("jfrog")
        return

    def fake_netrc(origin: str, env: Mapping[str, str]) -> None:
        netrc_called.append("netrc")
        return

    monkeypatch.setattr("credbroker._http_access._jfrog_provider", fake_jfrog)
    monkeypatch.setattr("credbroker._http_access._netrc_provider", fake_netrc)

    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://catalogue.example.test/cat.toml",
            env={"AGENTBUNDLE_HTTP_BEARER_TOKEN": "bad token with space"},
        )
    assert exc_info.value.code == "invalid_bearer"
    assert not jfrog_called, "JFrog provider must not run after bearer failure"
    assert not netrc_called, ".netrc provider must not run after bearer failure"


# ── Provider order table ──────────────────────────────────────────────────────


def test_provider_order_bearer_wins_over_anonymous(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bearer is selected before anonymous when token is present. AC-0006"""
    jfrog_called: list[str] = []
    netrc_called: list[str] = []

    def record_jfrog(origin: str, env: Mapping[str, str]) -> None:
        jfrog_called.append("jfrog")
        return

    def record_netrc(origin: str, env: Mapping[str, str]) -> None:
        netrc_called.append("netrc")
        return

    monkeypatch.setattr("credbroker._http_access._jfrog_provider", record_jfrog)
    monkeypatch.setattr("credbroker._http_access._netrc_provider", record_netrc)

    result = resolve_http_access(
        "https://catalogue.example.test/cat.toml",
        env={"AGENTBUNDLE_HTTP_BEARER_TOKEN": "validtoken123"},
    )
    assert isinstance(result, BearerHttpAccess)
    assert not jfrog_called, "JFrog must not run when bearer is available"
    assert not netrc_called, ".netrc must not run when bearer is available"


def test_anonymous_is_fallback_when_all_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Anonymous is used only when all higher providers are unavailable. AC-0006"""
    bearer_called: list[str] = []
    jfrog_called: list[str] = []
    netrc_called: list[str] = []

    def record_bearer(origin: str, env: Mapping[str, str]) -> None:
        bearer_called.append("bearer")
        return

    def record_jfrog(origin: str, env: Mapping[str, str]) -> None:
        jfrog_called.append("jfrog")
        return

    def record_netrc(origin: str, env: Mapping[str, str]) -> None:
        netrc_called.append("netrc")
        return

    monkeypatch.setattr("credbroker._http_access._bearer_provider", record_bearer)
    monkeypatch.setattr("credbroker._http_access._jfrog_provider", record_jfrog)
    monkeypatch.setattr("credbroker._http_access._netrc_provider", record_netrc)

    result = resolve_http_access(
        "https://catalogue.example.test/cat.toml", env={}
    )
    assert isinstance(result, AnonymousHttpAccess)
    assert bearer_called, "bearer provider must be evaluated"
    assert jfrog_called, "jfrog provider must be evaluated"
    assert netrc_called, "netrc provider must be evaluated"


# ── Canary test (AC-0015) ─────────────────────────────────────────────────────


_CANARY = "canary-credential-value-9bXz2"


def test_canary_absent_from_anonymous_result() -> None:
    """Canary placed in env never appears in anonymous result repr or origin. AC-0015"""
    result = resolve_http_access(
        "https://catalogue.example.test/cat.toml",
        env={"SOME_OTHER_VAR": _CANARY},
    )
    assert _CANARY not in repr(result)
    assert _CANARY not in str(result)
    assert _CANARY not in result.origin


def test_canary_absent_from_bearer_result() -> None:
    """Bearer token canary never appears in repr or str. AC-0015"""
    result = resolve_http_access(
        "https://catalogue.example.test/cat.toml",
        env={"AGENTBUNDLE_HTTP_BEARER_TOKEN": _CANARY},
    )
    assert isinstance(result, BearerHttpAccess)
    assert _CANARY not in repr(result)
    assert _CANARY not in str(result)


def test_canary_absent_from_invalid_bearer_error() -> None:
    """Canary in a broken bearer token never appears in exception text. AC-0015"""
    bad_token = f"{_CANARY} with space"
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://catalogue.example.test/cat.toml",
            env={"AGENTBUNDLE_HTTP_BEARER_TOKEN": bad_token},
        )
    exc = exc_info.value
    assert _CANARY not in str(exc)
    assert _CANARY not in repr(exc)
    for arg in exc.args:
        assert _CANARY not in str(arg)


def test_env_not_mutated_by_resolve() -> None:
    """resolve_http_access does not mutate the supplied env mapping. AC-0015"""
    env: dict[str, str] = {"AGENTBUNDLE_HTTP_BEARER_TOKEN": "tok123"}
    original = dict(env)
    resolve_http_access("https://catalogue.example.test/cat.toml", env=env)
    assert env == original


def test_canary_absent_from_target_error() -> None:
    """Canary placed in env never reaches target error text. AC-0015"""
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "http://catalogue.example.test/cat.toml",
            env={"SOME_VAR": _CANARY},
        )
    exc = exc_info.value
    assert _CANARY not in str(exc)
    assert _CANARY not in repr(exc)


# ── No socket activity ────────────────────────────────────────────────────────


def test_resolve_performs_no_socket_activity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Discovery performs no network I/O. AC-0006"""

    def forbidden_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("resolve_http_access must not create a socket")

    monkeypatch.setattr(socket, "socket", forbidden_socket)
    monkeypatch.setattr(socket, "create_connection", forbidden_socket)

    result = resolve_http_access(
        "https://catalogue.example.test/cat.toml", env={}
    )
    assert isinstance(result, AnonymousHttpAccess)
