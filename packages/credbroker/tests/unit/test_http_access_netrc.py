# ruff: noqa: I001 — stub import block has a deliberate blank line; content is pinned
# STUB: AC-0009 — an exact machine record returns origin-bound netrc access
import os
from pathlib import Path

import pytest

from credbroker import NetrcHttpAccess, resolve_http_access


@pytest.mark.skipif(os.name == "nt", reason="stub fixture requires POSIX permission bits")
def test_netrc_exact_host_returns_origin_bound_access(
    tmp_path: Path,
) -> None:
    netrc_file = tmp_path / ".netrc"
    netrc_file.write_text(
        "machine catalogue.example.test login test-user password test-secret\n",
        encoding="utf-8",
    )
    netrc_file.chmod(0o600)

    result = resolve_http_access(
        "https://catalogue.example.test/root/catalogue.toml",
        env={"HOME": str(tmp_path)},
    )

    assert isinstance(result, NetrcHttpAccess)
    assert result.origin == "https://catalogue.example.test"


# ---------------------------------------------------------------------------
# Appended tests — T3 full matrix
# ---------------------------------------------------------------------------

import base64  # noqa: E402
import logging  # noqa: E402
from unittest import mock  # noqa: E402

from credbroker import AnonymousHttpAccess, HttpAccessError  # noqa: E402
from credbroker._http_access import _anonymous_provider, _resolve_home_dir  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_netrc(tmp_path: Path, content: str, *, mode: int = 0o600) -> Path:
    """Write a .netrc file and set permissions (POSIX only)."""
    netrc = tmp_path / ".netrc"
    netrc.write_text(content, encoding="utf-8")
    if os.name != "nt":
        netrc.chmod(mode)
    return netrc


def _expected_basic(login: str, password: str) -> str:
    token = base64.b64encode(f"{login}:{password}".encode()).decode("ascii")
    return f"Basic {token}"


# ---------------------------------------------------------------------------
# AC-0009 — default port (443): only the bare host key
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_default_port_bare_host_key(tmp_path: Path) -> None:
    """Default-port HTTPS matches the bare machine key."""
    _make_netrc(tmp_path, "machine catalogue.example.test login u password p\n")
    result = resolve_http_access(
        "https://catalogue.example.test/root/c.toml",
        env={"HOME": str(tmp_path)},
    )
    assert isinstance(result, NetrcHttpAccess)
    assert result.origin == "https://catalogue.example.test"
    assert result.authorization == _expected_basic("u", "p")


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_host_port_record_does_not_match_default_port(tmp_path: Path) -> None:
    """A host:port record does NOT match a request to the default port (443)."""
    _make_netrc(tmp_path, "machine catalogue.example.test:8080 login u password p\n")
    result = resolve_http_access(
        "https://catalogue.example.test/root/c.toml",
        env={"HOME": str(tmp_path)},
    )
    assert isinstance(result, AnonymousHttpAccess)


# ---------------------------------------------------------------------------
# AC-0009 — non-default port: host:port first, host fallback
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_non_default_port_exact_host_port_key(tmp_path: Path) -> None:
    """Non-default port with an exact host:port record returns that record."""
    _make_netrc(tmp_path, "machine catalogue.example.test:8080 login u2 password p2\n")
    result = resolve_http_access(
        "https://catalogue.example.test:8080/root/c.toml",
        env={"HOME": str(tmp_path)},
    )
    assert isinstance(result, NetrcHttpAccess)
    assert result.origin == "https://catalogue.example.test:8080"
    assert result.authorization == _expected_basic("u2", "p2")


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_non_default_port_falls_back_to_host_key(tmp_path: Path) -> None:
    """Non-default port falls back to the bare host key when no host:port record exists."""
    _make_netrc(tmp_path, "machine catalogue.example.test login u3 password p3\n")
    result = resolve_http_access(
        "https://catalogue.example.test:9000/root/c.toml",
        env={"HOME": str(tmp_path)},
    )
    assert isinstance(result, NetrcHttpAccess)
    assert result.origin == "https://catalogue.example.test:9000"
    assert result.authorization == _expected_basic("u3", "p3")


# ---------------------------------------------------------------------------
# AC-0009 — absent, default-only, missing-match → anonymous
# ---------------------------------------------------------------------------


def test_absent_netrc_returns_anonymous(tmp_path: Path) -> None:
    """No .netrc file → anonymous access."""
    result = resolve_http_access(
        "https://catalogue.example.test/c.toml",
        env={"HOME": str(tmp_path)},
    )
    assert isinstance(result, AnonymousHttpAccess)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_default_only_netrc_returns_anonymous(tmp_path: Path) -> None:
    """A .netrc with only a 'default' record → anonymous (default never authenticates)."""
    _make_netrc(tmp_path, "default login u password p\n")
    result = resolve_http_access(
        "https://catalogue.example.test/c.toml",
        env={"HOME": str(tmp_path)},
    )
    assert isinstance(result, AnonymousHttpAccess)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_missing_machine_match_returns_anonymous(tmp_path: Path) -> None:
    """A .netrc with a different host → anonymous."""
    _make_netrc(tmp_path, "machine other.example.test login u password p\n")
    result = resolve_http_access(
        "https://catalogue.example.test/c.toml",
        env={"HOME": str(tmp_path)},
    )
    assert isinstance(result, AnonymousHttpAccess)


def test_no_home_in_env_returns_anonymous(tmp_path: Path) -> None:
    """No HOME in env → anonymous (provider is unavailable)."""
    _make_netrc(tmp_path, "machine catalogue.example.test login u password p\n")
    result = resolve_http_access(
        "https://catalogue.example.test/c.toml",
        env={},
    )
    assert isinstance(result, AnonymousHttpAccess)


# ---------------------------------------------------------------------------
# AC-0009 — incomplete record → netrc_incomplete
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_incomplete_missing_password(tmp_path: Path) -> None:
    """Matched record with no password → netrc_incomplete."""
    _make_netrc(tmp_path, "machine catalogue.example.test login u\n")
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://catalogue.example.test/c.toml",
            env={"HOME": str(tmp_path)},
        )
    assert exc_info.value.code == "netrc_incomplete"
    assert exc_info.value.provider == "netrc"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_incomplete_missing_login(tmp_path: Path) -> None:
    """Matched record with no login → netrc_incomplete."""
    _make_netrc(tmp_path, "machine catalogue.example.test password p\n")
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://catalogue.example.test/c.toml",
            env={"HOME": str(tmp_path)},
        )
    assert exc_info.value.code == "netrc_incomplete"


# ---------------------------------------------------------------------------
# AC-0009 — malformed file → netrc_malformed
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_malformed_netrc_parse_error(tmp_path: Path) -> None:
    """A file with a parse error → netrc_malformed."""
    _make_netrc(tmp_path, "badtoken\n")
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://catalogue.example.test/c.toml",
            env={"HOME": str(tmp_path)},
        )
    assert exc_info.value.code == "netrc_malformed"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_malformed_utf8_decode_error(tmp_path: Path) -> None:
    """A file with invalid UTF-8 bytes → netrc_malformed."""
    netrc = tmp_path / ".netrc"
    netrc.write_bytes(b"\xff\xfe invalid utf-8\n")
    netrc.chmod(0o600)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://catalogue.example.test/c.toml",
            env={"HOME": str(tmp_path)},
        )
    assert exc_info.value.code == "netrc_malformed"


# ---------------------------------------------------------------------------
# AC-0009 — unsafe permissions (POSIX only) → netrc_unsafe
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_unsafe_permissions_0o644(tmp_path: Path) -> None:
    """A .netrc with mode 0o644 → netrc_unsafe."""
    _make_netrc(
        tmp_path,
        "machine catalogue.example.test login u password p\n",
        mode=0o644,
    )
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://catalogue.example.test/c.toml",
            env={"HOME": str(tmp_path)},
        )
    assert exc_info.value.code == "netrc_unsafe"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_unsafe_permissions_0o640(tmp_path: Path) -> None:
    """A .netrc with mode 0o640 → netrc_unsafe."""
    _make_netrc(
        tmp_path,
        "machine catalogue.example.test login u password p\n",
        mode=0o640,
    )
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://catalogue.example.test/c.toml",
            env={"HOME": str(tmp_path)},
        )
    assert exc_info.value.code == "netrc_unsafe"


# ---------------------------------------------------------------------------
# AC-0009 — not-a-regular-file → netrc_unreadable
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_directory_named_netrc_is_unreadable(tmp_path: Path) -> None:
    """A directory named .netrc → netrc_unreadable."""
    netrc_dir = tmp_path / ".netrc"
    netrc_dir.mkdir()
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://catalogue.example.test/c.toml",
            env={"HOME": str(tmp_path)},
        )
    assert exc_info.value.code == "netrc_unreadable"


# ---------------------------------------------------------------------------
# AC-0009 — host normalization
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_case_differing_record_matches(tmp_path: Path) -> None:
    """A record whose machine key differs only in case matches the target."""
    _make_netrc(tmp_path, "machine CATALOGUE.EXAMPLE.TEST login u password p\n")
    result = resolve_http_access(
        "https://catalogue.example.test/c.toml",
        env={"HOME": str(tmp_path)},
    )
    assert isinstance(result, NetrcHttpAccess)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_unicode_record_matches_punycode_target(tmp_path: Path) -> None:
    """A Unicode machine key and its punycode spelling match the same target.

    The lossy 'ß' → 'ss' IDNA2003 fold means the origin the connection
    uses equals the normalized form of the target host, never the raw
    Unicode spelling.
    """
    # "café.example.test" IDNA-encodes to "xn--caf-dma.example.test"
    # Use a simpler non-ASCII host that round-trips cleanly.
    unicode_host = "bücher.example.test"
    punycode_host = "xn--bcher-kva.example.test"
    _make_netrc(tmp_path, f"machine {unicode_host} login u password p\n")
    result = resolve_http_access(
        f"https://{punycode_host}/c.toml",
        env={"HOME": str(tmp_path)},
    )
    # The normalized bound origin uses the punycode form.
    assert isinstance(result, NetrcHttpAccess)
    assert result.origin == f"https://{punycode_host}"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_punycode_record_matches_unicode_target(tmp_path: Path) -> None:
    """A punycode machine key matches a Unicode target spelled differently."""
    unicode_host = "bücher.example.test"
    punycode_host = "xn--bcher-kva.example.test"
    _make_netrc(tmp_path, f"machine {punycode_host} login u password p\n")
    result = resolve_http_access(
        f"https://{unicode_host}/c.toml",
        env={"HOME": str(tmp_path)},
    )
    assert isinstance(result, NetrcHttpAccess)
    assert result.origin == f"https://{punycode_host}"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_lossy_fold_origin_matches_connected_host(tmp_path: Path) -> None:
    """The 'ß' → 'ss' IDNA2003 fold: the bound origin equals the IDNA form used to connect.

    IDNA2003 folds U+00DF (ß) to 'ss', so 'straße.example.test' and
    'strasse.example.test' normalize to the same host.  The bound origin
    is the IDNA-normalized form that Python would use to open the socket,
    not the raw Unicode spelling.
    """
    _make_netrc(tmp_path, "machine stra\u00dfe.example.test login u password p\n")
    # The target spells it differently — the IDNA2003 fold makes them equal.
    result = resolve_http_access(
        "https://strasse.example.test/c.toml",
        env={"HOME": str(tmp_path)},
    )
    assert isinstance(result, NetrcHttpAccess)
    # Bound origin must be the IDNA form the socket uses.
    import encodings.idna  # noqa: F401
    idna_form = "strasse.example.test".encode("idna").decode("ascii")
    assert result.origin == f"https://{idna_form}"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_unencodable_machine_key_is_malformed(tmp_path: Path) -> None:
    """A machine key that cannot be IDNA-encoded → netrc_malformed."""
    # A label longer than 63 characters cannot be IDNA-encoded.
    long_label = "a" * 64
    _make_netrc(tmp_path, f"machine {long_label}.example.test login u password p\n")
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://catalogue.example.test/c.toml",
            env={"HOME": str(tmp_path)},
        )
    assert exc_info.value.code == "netrc_malformed"


def test_unencodable_target_raises_before_file_open(tmp_path: Path) -> None:
    """An unencodable target host raises invalid_target_host before the .netrc is opened.

    Proven by monkeypatching os.open to assert it is never called.
    """
    _make_netrc(tmp_path, "machine catalogue.example.test login u password p\n")
    if os.name != "nt":
        (tmp_path / ".netrc").chmod(0o600)

    open_calls: list[str] = []
    original_open = os.open

    def recording_open(path: str, flags: int, *args: object, **kwargs: object) -> int:
        open_calls.append(str(path))
        return original_open(path, flags, *args, **kwargs)  # type: ignore[arg-type]

    long_label = "b" * 64
    unencodable_url = f"https://{long_label}.example.test/c.toml"

    with (
        mock.patch("os.open", side_effect=recording_open),
        pytest.raises(HttpAccessError) as exc_info,
    ):
        resolve_http_access(unencodable_url, env={"HOME": str(tmp_path)})

    assert exc_info.value.code == "invalid_target_host"
    assert exc_info.value.provider == "target"
    # .netrc file was never opened (os.open not called for the netrc path).
    netrc_path = str(tmp_path / ".netrc")
    assert not any(netrc_path in p for p in open_calls), (
        f"os.open was called for .netrc: {open_calls}"
    )


# ---------------------------------------------------------------------------
# Windows home resolution (USERPROFILE and HOMEDRIVE+HOMEPATH)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name != "nt", reason="Windows-only test")
def test_windows_userprofile_home_resolution(tmp_path: Path) -> None:
    """On Windows, USERPROFILE is used to locate .netrc."""
    _make_netrc(tmp_path, "machine catalogue.example.test login wu password wp\n")
    result = resolve_http_access(
        "https://catalogue.example.test/c.toml",
        env={"USERPROFILE": str(tmp_path)},
    )
    assert isinstance(result, NetrcHttpAccess)
    assert result.origin == "https://catalogue.example.test"


def test_nt_userprofile_home_resolution_cross_platform(tmp_path: Path) -> None:
    """USERPROFILE precedence is exercised on POSIX via _resolve_home_dir with _os_name='nt'."""
    home = _resolve_home_dir(
        {"USERPROFILE": str(tmp_path), "HOME": "/should-not-be-used"},
        _os_name="nt",
    )
    assert home == str(tmp_path)


def test_nt_homedrive_homepath_fallback_cross_platform() -> None:
    """HOMEDRIVE+HOMEPATH fallback is exercised via _resolve_home_dir with _os_name='nt'."""
    home = _resolve_home_dir(
        {"HOMEDRIVE": "C:", "HOMEPATH": "\\Users\\testuser"},
        _os_name="nt",
    )
    assert home == "C:\\Users\\testuser"


def test_nt_no_home_vars_returns_none_cross_platform() -> None:
    """Empty env with _os_name='nt' returns None (no home)."""
    home = _resolve_home_dir({}, _os_name="nt")
    assert home is None


# ---------------------------------------------------------------------------
# AC-0007 / ADR-0138 D4 — no fallback: netrc_* error stops resolution
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_netrc_error_stops_resolution_anonymous_not_evaluated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A netrc_unreadable / netrc_malformed error stops resolution; anonymous is NOT evaluated.

    Monkeypatches _anonymous_provider to record calls; it must not be called.
    """
    # Use a directory named .netrc to trigger netrc_unreadable.
    netrc_dir = tmp_path / ".netrc"
    netrc_dir.mkdir()

    anon_calls: list[str] = []
    original_anon = _anonymous_provider

    def recording_anon(origin: str) -> AnonymousHttpAccess:
        anon_calls.append(origin)
        return original_anon(origin)

    import credbroker._http_access as _ha
    monkeypatch.setattr(_ha, "_anonymous_provider", recording_anon)

    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://catalogue.example.test/c.toml",
            env={"HOME": str(tmp_path)},
        )

    assert exc_info.value.code == "netrc_unreadable"
    assert anon_calls == [], "anonymous provider must not be evaluated after a netrc error"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_bearer_wins_over_matching_netrc(tmp_path: Path) -> None:
    """A set bearer token wins over a matching .netrc; .netrc is not even opened."""
    _make_netrc(
        tmp_path,
        "machine catalogue.example.test login netrc-u password netrc-p\n",
    )
    open_calls: list[str] = []
    original_open = os.open

    def recording_open(path: str, flags: int, *args: object, **kwargs: object) -> int:
        open_calls.append(str(path))
        return original_open(path, flags, *args, **kwargs)  # type: ignore[arg-type]

    from credbroker import BearerHttpAccess

    with mock.patch("os.open", side_effect=recording_open):
        result = resolve_http_access(
            "https://catalogue.example.test/c.toml",
            env={
                "HOME": str(tmp_path),
                "AGENTBUNDLE_HTTP_BEARER_TOKEN": "valid-bearer-token",
            },
        )

    assert isinstance(result, BearerHttpAccess)
    # The .netrc file must not have been opened.
    netrc_path = str(tmp_path / ".netrc")
    assert not any(netrc_path in p for p in open_calls), (
        f"os.open was called for .netrc when bearer should have won: {open_calls}"
    )


# ---------------------------------------------------------------------------
# AC-0015 canary — login and password never in exception text, repr, or logs
# ---------------------------------------------------------------------------


CANARY_LOGIN = "CANARY-LOGIN-AC-0015"
CANARY_PASS = "CANARY-PASS-AC-0015"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_canary_not_in_incomplete_error(tmp_path: Path) -> None:
    """Canary login never appears in netrc_incomplete error text or args."""
    # Write a record with a login but no password to trigger netrc_incomplete.
    _make_netrc(tmp_path, f"machine catalogue.example.test login {CANARY_LOGIN}\n")
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://catalogue.example.test/c.toml",
            env={"HOME": str(tmp_path)},
        )
    assert exc_info.value.code == "netrc_incomplete"
    err = exc_info.value
    assert CANARY_LOGIN not in str(err)
    assert CANARY_LOGIN not in repr(err)
    for arg in err.args:
        assert CANARY_LOGIN not in str(arg)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_canary_not_in_result_repr_or_str(tmp_path: Path) -> None:
    """Canary login and password are absent from repr and str of NetrcHttpAccess."""
    _make_netrc(
        tmp_path,
        f"machine catalogue.example.test login {CANARY_LOGIN} password {CANARY_PASS}\n",
    )
    result = resolve_http_access(
        "https://catalogue.example.test/c.toml",
        env={"HOME": str(tmp_path)},
    )
    assert isinstance(result, NetrcHttpAccess)
    for secret in (CANARY_LOGIN, CANARY_PASS):
        assert secret not in repr(result), f"Secret {secret!r} found in repr"
        assert secret not in str(result), f"Secret {secret!r} found in str"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX permission bits")
def test_canary_not_in_logs(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Canary credentials are absent from DEBUG logs during netrc resolution."""
    _make_netrc(
        tmp_path,
        f"machine catalogue.example.test login {CANARY_LOGIN} password {CANARY_PASS}\n",
    )
    with caplog.at_level(logging.DEBUG):
        result = resolve_http_access(
            "https://catalogue.example.test/c.toml",
            env={"HOME": str(tmp_path)},
        )
    assert isinstance(result, NetrcHttpAccess)
    for record in caplog.records:
        msg = record.getMessage()
        assert CANARY_LOGIN not in msg
        assert CANARY_PASS not in msg


def test_env_not_mutated(tmp_path: Path) -> None:
    """The supplied env mapping is never mutated by the provider."""
    original_env: dict[str, str] = {"HOME": str(tmp_path)}
    env_copy = dict(original_env)
    # Absent file → anonymous; the env must still be unchanged.
    resolve_http_access(
        "https://catalogue.example.test/c.toml",
        env=original_env,
    )
    assert original_env == env_copy, "env mapping was mutated"


def test_no_socket_activity_during_resolution() -> None:
    """No socket I/O occurs during .netrc resolution."""
    import socket

    def forbidden_connect(self: socket.socket, *args: object, **kwargs: object) -> None:
        raise AssertionError("socket.connect must not be called during resolution")

    with mock.patch.object(socket.socket, "connect", forbidden_connect):
        resolve_http_access(
            "https://catalogue.example.test/c.toml",
            env={},  # no HOME → anonymous, no file opened
        )


@pytest.mark.skipif(os.name == "nt", reason="fixture requires POSIX permission bits")
def test_netrc_matches_ipv6_literal_with_port(tmp_path: Path) -> None:
    """A bracketed IPv6 machine key matches a bracketed IPv6 target. AC-0009"""
    netrc_file = tmp_path / ".netrc"
    netrc_file.write_text(
        "machine [::1]:8443 login v6-user password v6-secret\n", encoding="utf-8"
    )
    netrc_file.chmod(0o600)

    result = resolve_http_access("https://[::1]:8443/root/catalogue.toml", env={"HOME": str(tmp_path)})

    assert isinstance(result, NetrcHttpAccess)
    assert result.origin == "https://[::1]:8443"
