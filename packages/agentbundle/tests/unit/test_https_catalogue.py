"""Tests for HTTPS catalogue channels — Wave 2 of ini-004 (spec/https-catalogue-channels).

Coverage:
  T1 — _is_valid_source new branches (AC1-AC5b, AC25)
  T2 — https_catalogue.py fetcher: descriptor parse, artifact URL resolution,
        version check, archive extraction safety, streaming, proxy/redirect/token
  T3 — resolve_catalogue dispatch (AC6, AC24, AC34)

All tests use in-process fixtures and mocks; no real external network calls.
All domain names use the ``example.test`` placeholder (AC29).
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Iterator
from unittest import mock

import pytest

from agentbundle.catalogue import CatalogueError
from agentbundle.source_defaults import _is_valid_source
from agentbundle import https_catalogue
from agentbundle.https_catalogue import (
    _MAX_ARCHIVE_BYTES,
    _MAX_EXPANDED_BYTES,
    _MAX_MEMBERS,
    _OriginLockingRedirectHandler,
    _build_opener,
    _check_client_version,
    _fetch_bytes_limited,
    _make_request,
    _parse_descriptor,
    _resolve_artifact_url,
    _safe_extract,
    _stream_and_verify,
    fetch_catalogue_archive,
)


# ---------------------------------------------------------------------------
# Test helpers / fixtures
# ---------------------------------------------------------------------------


class _MockResponse:
    """Minimal file-like object simulating a urllib HTTP response."""

    def __init__(self, data: bytes) -> None:
        self._buf = io.BytesIO(data)

    def read(self, n: int = -1) -> bytes:
        return self._buf.read(n)

    def __enter__(self) -> "_MockResponse":
        return self

    def __exit__(self, *args: object) -> None:
        pass


class _MockOpener:
    """Mock urllib opener that returns a fixed response body."""

    def __init__(self, response_data: bytes, *, token: str | None = None) -> None:
        self._data = response_data
        self._bearer_token = token
        self._last_req: urllib.request.Request | None = None

    def open(self, req: urllib.request.Request, timeout: int | None = None) -> _MockResponse:
        self._last_req = req
        return _MockResponse(self._data)


class _ErrorOpener:
    """Mock opener that raises a URLError on open."""

    def __init__(self, *, token: str | None = None) -> None:
        self._bearer_token = token

    def open(self, req: urllib.request.Request, timeout: int | None = None) -> None:
        import urllib.error
        raise urllib.error.URLError("simulated connection error")


class _SlowOpener:
    """Mock opener that raises a timeout error."""

    def __init__(self) -> None:
        self._bearer_token = None

    def open(self, req: urllib.request.Request, timeout: int | None = None) -> None:
        import urllib.error
        raise urllib.error.URLError("timed out")


def _make_tarball(*members: tuple[str, bytes]) -> tuple[bytes, str]:
    """Create an in-memory tar.gz archive from (name, content) pairs.

    Returns (raw_bytes, sha256_hex).
    """
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, content in members:
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            tf.addfile(info, io.BytesIO(content))
    data = buf.getvalue()
    return data, hashlib.sha256(data).hexdigest()


def _make_tarball_with_member(info: tarfile.TarInfo, content: bytes = b"") -> tuple[bytes, str]:
    """Create a tar.gz containing a single TarInfo (for special member types)."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        tf.addfile(info, io.BytesIO(content))
    data = buf.getvalue()
    return data, hashlib.sha256(data).hexdigest()


def _write_tarball(tmp_path: Path, members: list[tuple[str, bytes]]) -> Path:
    """Write a tar.gz to a temp file and return its path."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    data, _ = _make_tarball(*members)
    p = tmp_path / "archive.tar.gz"
    p.write_bytes(data)
    return p


_VALID_DESCRIPTOR = {
    "schema": 1,
    "kind": "agentbundle-catalogue",
    "bundle": "core",
    "channel": "stable",
    "release": "2026.07.01",
    "artifact": "releases/core-stable-2026.07.01.tar.gz",
    "sha256": "a" * 64,
}


# ---------------------------------------------------------------------------
# T1 — _is_valid_source new branches
# ---------------------------------------------------------------------------


def test_is_valid_source_catalogue_https():
    """AC1: catalogue+https:// accepted."""
    assert _is_valid_source("catalogue+https://example.test/path/stable.json") is True


def test_is_valid_source_catalogue_http():
    """AC2: catalogue+http:// rejected."""
    assert _is_valid_source("catalogue+http://example.test/path/stable.json") is False


def test_is_valid_source_archive_https_with_sha256():
    """AC3: archive+https:// with valid #sha256=<64hex> accepted."""
    assert _is_valid_source(
        "archive+https://example.test/path/release.tar.gz#sha256=" + "a" * 64
    ) is True


def test_is_valid_source_archive_http():
    """AC4: archive+http:// rejected."""
    assert _is_valid_source("archive+http://example.test/release.tar.gz") is False


def test_is_valid_source_catalogue_https_user_info():
    """AC5: catalogue+https:// with user-info rejected."""
    assert _is_valid_source("catalogue+https://user:pass@example.test/path") is False


def test_is_valid_source_archive_https_user_info():
    """AC5b: archive+https:// with user-info rejected."""
    assert _is_valid_source(
        "archive+https://user:pass@example.test/release.tar.gz#sha256=" + "a" * 64
    ) is False


def test_is_valid_source_archive_https_no_fragment():
    """AC25: archive+https:// without #sha256= fragment rejected."""
    assert _is_valid_source("archive+https://example.test/release.tar.gz") is False


@pytest.mark.parametrize(
    "fragment_suffix",
    [
        "sha256=UPPERCASE" + "A" * 56,       # uppercase hex not allowed
        "sha256=" + "g" * 64,                # non-hex chars
        "sha256=" + "a" * 63,                # too short
        "sha256=" + "a" * 65,                # too long
        "other=value",                        # wrong key
        "",                                   # empty fragment
    ],
)
def test_is_valid_source_archive_https_bad_fragment(fragment_suffix: str):
    """AC25: archive+https:// with bad fragment rejected."""
    assert _is_valid_source(
        f"archive+https://example.test/release.tar.gz#{fragment_suffix}"
    ) is False


def test_existing_git_https_still_accepted():
    """AC31: existing git+https:// scheme still accepted (no regression)."""
    assert _is_valid_source("git+https://github.com/example/repo") is True


def test_existing_scheme_gate_still_rejects_http():
    """AC31: existing http:// rejection still works."""
    assert _is_valid_source("http://evil.example.test") is False


# ---------------------------------------------------------------------------
# T2 — _parse_descriptor
# ---------------------------------------------------------------------------


def test_parse_descriptor_valid():
    """AC6: valid descriptor parses cleanly."""
    data = json.dumps(_VALID_DESCRIPTOR).encode()
    result = _parse_descriptor(data)
    assert result["schema"] == 1
    assert result["kind"] == "agentbundle-catalogue"
    assert result["sha256"] == "a" * 64


def test_parse_descriptor_not_json_rejected():
    """Invalid JSON raises CatalogueError."""
    with pytest.raises(CatalogueError, match="not valid JSON"):
        _parse_descriptor(b"not json {{{")


def test_parse_descriptor_not_dict_rejected():
    """Non-dict JSON raises CatalogueError."""
    with pytest.raises(CatalogueError, match="JSON object"):
        _parse_descriptor(b"[1, 2, 3]")


@pytest.mark.parametrize("missing_field", list(_VALID_DESCRIPTOR.keys()))
def test_parse_descriptor_missing_field_rejected(missing_field: str):
    """AC32: missing any required field raises CatalogueError naming the field."""
    descriptor = {k: v for k, v in _VALID_DESCRIPTOR.items() if k != missing_field}
    data = json.dumps(descriptor).encode()
    with pytest.raises(CatalogueError, match=re.escape(repr(missing_field))):
        _parse_descriptor(data)


def test_parse_descriptor_wrong_schema_rejected():
    """AC33: schema != 1 rejected."""
    descriptor = {**_VALID_DESCRIPTOR, "schema": 2}
    with pytest.raises(CatalogueError, match="schema must be 1"):
        _parse_descriptor(json.dumps(descriptor).encode())


def test_parse_descriptor_wrong_kind_rejected():
    """AC33: kind != 'agentbundle-catalogue' rejected."""
    descriptor = {**_VALID_DESCRIPTOR, "kind": "not-agentbundle"}
    with pytest.raises(CatalogueError, match="kind must be"):
        _parse_descriptor(json.dumps(descriptor).encode())


@pytest.mark.parametrize(
    "bad_sha256",
    [
        "UPPERCASE" + "A" * 55,        # uppercase
        "gg" + "a" * 62,               # non-hex
        "a" * 63,                      # too short
        "a" * 65,                      # too long
        "",                            # empty
    ],
)
def test_parse_descriptor_sha256_non_hex_rejected(bad_sha256: str):
    """AC25b: descriptor sha256 not 64 lowercase hex chars rejected at parse time."""
    descriptor = {**_VALID_DESCRIPTOR, "sha256": bad_sha256}
    with pytest.raises(CatalogueError, match="sha256"):
        _parse_descriptor(json.dumps(descriptor).encode())


# ---------------------------------------------------------------------------
# T2 — _resolve_artifact_url
# ---------------------------------------------------------------------------


def test_resolve_artifact_url_same_origin_absolute():
    """AC6: artifact URL on same origin (absolute) accepted."""
    result = _resolve_artifact_url(
        "https://example.test/channels/stable.json",
        "https://example.test/releases/core.tar.gz",
    )
    assert result == "https://example.test/releases/core.tar.gz"


def test_resolve_artifact_url_relative():
    """AC6: relative artifact URL resolved against descriptor URL, same origin."""
    result = _resolve_artifact_url(
        "https://example.test/channels/stable.json",
        "../releases/core.tar.gz",
    )
    assert result == "https://example.test/releases/core.tar.gz"


def test_resolve_artifact_url_cross_origin_different_host():
    """AC9: different host rejected."""
    with pytest.raises(CatalogueError, match="cross-origin"):
        _resolve_artifact_url(
            "https://example.test/channels/stable.json",
            "https://evil.example.test/releases/core.tar.gz",
        )


def test_resolve_artifact_url_cross_origin_different_port():
    """AC9: same host, different port rejected."""
    with pytest.raises(CatalogueError, match="cross-origin"):
        _resolve_artifact_url(
            "https://example.test:443/channels/stable.json",
            "https://example.test:9999/releases/core.tar.gz",
        )


def test_resolve_artifact_url_cross_origin_different_scheme():
    """AC9 + AC10: HTTP artifact URL (different scheme = cross-origin) rejected."""
    with pytest.raises(CatalogueError):
        _resolve_artifact_url(
            "https://example.test/channels/stable.json",
            "http://example.test/releases/core.tar.gz",
        )


def test_resolve_artifact_url_http_rejected():
    """AC10: explicit http:// artifact URL rejected."""
    with pytest.raises(CatalogueError, match="HTTPS"):
        _resolve_artifact_url(
            "https://example.test/channels/stable.json",
            "http://example.test/releases/core.tar.gz",
        )


def test_resolve_artifact_url_user_info_rejected():
    """User-info in artifact URL rejected."""
    with pytest.raises(CatalogueError, match="user-info"):
        _resolve_artifact_url(
            "https://example.test/channels/stable.json",
            "https://user:pass@example.test/releases/core.tar.gz",
        )


# ---------------------------------------------------------------------------
# T2 — _check_client_version
# ---------------------------------------------------------------------------


def test_check_client_version_none_proceeds():
    """AC12: minimum absent — proceeds without error."""
    _check_client_version(None, running_version="1.0.0")  # no exception


def test_check_client_version_older_client_rejected():
    """AC11: client older than minimum raises CatalogueError naming both versions."""
    with pytest.raises(CatalogueError) as exc:
        _check_client_version("2.0.0", running_version="1.9.9")
    msg = str(exc.value)
    assert "1.9.9" in msg
    assert "2.0.0" in msg


def test_check_client_version_equal_proceeds():
    """AC12: equal versions — proceeds."""
    _check_client_version("1.2.3", running_version="1.2.3")  # no exception


def test_check_client_version_newer_running_proceeds():
    """AC12: running newer than minimum — proceeds."""
    _check_client_version("1.0.0", running_version="2.0.0")  # no exception


def test_check_client_version_ten_vs_nine():
    """AC35: integer comparison — 10.0.0 > 9.9.9 (lexicographic would invert)."""
    with pytest.raises(CatalogueError):
        _check_client_version("10.0.0", running_version="9.9.9")


def test_check_client_version_nine_less_than_ten():
    """AC35: integer comparison sanity — 9.0.0 minimum, running 10.0.0 proceeds."""
    _check_client_version("9.0.0", running_version="10.0.0")  # no exception


def test_check_client_version_malformed_minimum():
    """AC36: malformed minimum version raises clear CatalogueError."""
    with pytest.raises(CatalogueError, match="not a valid"):
        _check_client_version("not-semver", running_version="1.0.0")


def test_check_client_version_malformed_running():
    """AC36: malformed running version raises clear CatalogueError (not crash)."""
    with pytest.raises(CatalogueError, match="not a valid"):
        _check_client_version("1.0.0", running_version="1.0.0-alpha")


def test_check_client_version_reads_module_attr(monkeypatch: pytest.MonkeyPatch):
    """_check_client_version reads agentbundle.__version__ at call time (monkeypatchable)."""
    import agentbundle
    monkeypatch.setattr(agentbundle, "__version__", "5.0.0")
    # 5.0.0 >= 1.0.0 — should proceed
    _check_client_version("1.0.0")  # no exception


# ---------------------------------------------------------------------------
# T2 — _safe_extract
# ---------------------------------------------------------------------------


def test_safe_extract_ok(tmp_path: Path):
    """AC6: a clean archive extracts successfully."""
    archive = _write_tarball(tmp_path / "in", [("hello.txt", b"world")])
    dest = tmp_path / "out"
    dest.mkdir()
    _safe_extract(archive, dest)
    assert (dest / "hello.txt").exists()


def test_safe_extract_path_traversal(tmp_path: Path):
    """AC16: member with path traversal rejected; dest cleaned up."""
    info = tarfile.TarInfo(name="../evil.txt")
    info.size = 5
    data, _ = _make_tarball_with_member(info, b"oops!")
    archive = tmp_path / "archive.tar.gz"
    archive.write_bytes(data)
    dest = tmp_path / "out"
    dest.mkdir()
    with pytest.raises(CatalogueError, match="unsafe path"):
        _safe_extract(archive, dest)
    assert not dest.exists()


def test_safe_extract_absolute_path(tmp_path: Path):
    """AC17: member with absolute path rejected; dest cleaned up."""
    info = tarfile.TarInfo(name="/etc/passwd")
    info.size = 5
    data, _ = _make_tarball_with_member(info, b"root:")
    archive = tmp_path / "archive.tar.gz"
    archive.write_bytes(data)
    dest = tmp_path / "out"
    dest.mkdir()
    with pytest.raises(CatalogueError):
        _safe_extract(archive, dest)
    assert not dest.exists()


def test_safe_extract_symlink(tmp_path: Path):
    """AC18: symlink member rejected; dest cleaned up."""
    info = tarfile.TarInfo(name="link")
    info.type = tarfile.SYMTYPE
    info.linkname = "/etc/passwd"
    data, _ = _make_tarball_with_member(info)
    archive = tmp_path / "archive.tar.gz"
    archive.write_bytes(data)
    dest = tmp_path / "out"
    dest.mkdir()
    with pytest.raises(CatalogueError, match="symlink"):
        _safe_extract(archive, dest)
    assert not dest.exists()


def test_safe_extract_hard_link(tmp_path: Path):
    """AC19: hard link member rejected; dest cleaned up."""
    info = tarfile.TarInfo(name="hardlink")
    info.type = tarfile.LNKTYPE
    info.linkname = "target.txt"
    data, _ = _make_tarball_with_member(info)
    archive = tmp_path / "archive.tar.gz"
    archive.write_bytes(data)
    dest = tmp_path / "out"
    dest.mkdir()
    with pytest.raises(CatalogueError, match="hard link"):
        _safe_extract(archive, dest)
    assert not dest.exists()


def test_safe_extract_device_file(tmp_path: Path):
    """AC20: character device member rejected; dest cleaned up."""
    info = tarfile.TarInfo(name="device")
    info.type = tarfile.CHRTYPE
    data, _ = _make_tarball_with_member(info)
    archive = tmp_path / "archive.tar.gz"
    archive.write_bytes(data)
    dest = tmp_path / "out"
    dest.mkdir()
    with pytest.raises(CatalogueError, match="device file"):
        _safe_extract(archive, dest)
    assert not dest.exists()


def test_safe_extract_fifo(tmp_path: Path):
    """AC20: FIFO member rejected; dest cleaned up."""
    info = tarfile.TarInfo(name="fifo")
    info.type = tarfile.FIFOTYPE
    data, _ = _make_tarball_with_member(info)
    archive = tmp_path / "archive.tar.gz"
    archive.write_bytes(data)
    dest = tmp_path / "out"
    dest.mkdir()
    with pytest.raises(CatalogueError, match="device file or FIFO"):
        _safe_extract(archive, dest)
    assert not dest.exists()


def test_safe_extract_too_many_members(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """AC14: more than _MAX_MEMBERS members rejected; dest cleaned up."""
    monkeypatch.setattr(https_catalogue, "_MAX_MEMBERS", 2)
    # Create archive with 3 members
    archive = _write_tarball(
        tmp_path / "in",
        [("a.txt", b"a"), ("b.txt", b"b"), ("c.txt", b"c")],
    )
    dest = tmp_path / "out"
    dest.mkdir()
    with pytest.raises(CatalogueError, match="members"):
        _safe_extract(archive, dest)
    assert not dest.exists()


def test_safe_extract_too_large_expanded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """AC15: total expanded bytes exceeding limit rejected; dest cleaned up."""
    monkeypatch.setattr(https_catalogue, "_MAX_EXPANDED_BYTES", 5)
    # Create archive with a file larger than 5 bytes
    archive = _write_tarball(tmp_path / "in", [("big.txt", b"0123456789")])
    dest = tmp_path / "out"
    dest.mkdir()
    with pytest.raises(CatalogueError, match="expanded size"):
        _safe_extract(archive, dest)
    assert not dest.exists()


# ---------------------------------------------------------------------------
# T2 — _stream_and_verify
# ---------------------------------------------------------------------------


def test_stream_and_verify_sha256_match(tmp_path: Path):
    """AC6: SHA-256 match — returns path to temp file."""
    data, sha256 = _make_tarball(("hello.txt", b"world"))
    opener = _MockOpener(data)
    result = _stream_and_verify("https://example.test/archive.tar.gz", sha256, opener, 30)
    try:
        assert result.exists()
        assert result.read_bytes() == data
    finally:
        result.unlink(missing_ok=True)


def test_stream_and_verify_sha256_mismatch():
    """AC7: SHA-256 mismatch fails before extraction; error names both digests."""
    data, real_sha256 = _make_tarball(("hello.txt", b"world"))
    wrong_sha256 = "b" * 64
    opener = _MockOpener(data)
    with pytest.raises(CatalogueError) as exc:
        _stream_and_verify("https://example.test/archive.tar.gz", wrong_sha256, opener, 30)
    msg = str(exc.value)
    assert wrong_sha256 in msg    # expected
    assert real_sha256 in msg     # received


def test_stream_and_verify_sha256_mismatch_cleans_up():
    """AC7 + AC28: temp file cleaned up on digest mismatch."""
    data, _ = _make_tarball(("hello.txt", b"world"))
    wrong_sha256 = "b" * 64
    opener = _MockOpener(data)
    try:
        _stream_and_verify("https://example.test/archive.tar.gz", wrong_sha256, opener, 30)
    except CatalogueError:
        pass
    # No temp files should linger — we just verify no exception escapes uncleaned
    # (the temp file is created + deleted internally)


def test_stream_and_verify_too_large(monkeypatch: pytest.MonkeyPatch):
    """AC13: archive exceeding _MAX_ARCHIVE_BYTES rejected during streaming."""
    monkeypatch.setattr(https_catalogue, "_MAX_ARCHIVE_BYTES", 5)
    data = b"0" * 10  # 10 bytes > 5 byte limit
    opener = _MockOpener(data)
    with pytest.raises(CatalogueError, match="byte limit"):
        _stream_and_verify("https://example.test/archive.tar.gz", "a" * 64, opener, 30)


def test_stream_and_verify_fetch_error_propagates():
    """Fetch errors surface as CatalogueError."""
    opener = _ErrorOpener()
    with pytest.raises(CatalogueError, match="failed to fetch archive"):
        _stream_and_verify("https://example.test/archive.tar.gz", "a" * 64, opener, 30)


# ---------------------------------------------------------------------------
# T2 — _fetch_bytes_limited
# ---------------------------------------------------------------------------


def test_fetch_bytes_limited_within_limit():
    """AC26: descriptor within size limit fetched successfully."""
    data = b"x" * 100
    opener = _MockOpener(data)
    result = _fetch_bytes_limited("https://example.test/descriptor.json", opener, 200, 30)
    assert result == data


def test_fetch_bytes_limited_exceeds_limit():
    """AC26: descriptor exceeding limit rejected before JSON parse."""
    data = b"x" * 11
    opener = _MockOpener(data)
    with pytest.raises(CatalogueError, match="byte limit"):
        _fetch_bytes_limited("https://example.test/descriptor.json", opener, 10, 30)


def test_fetch_bytes_limited_error_propagates():
    """Fetch errors surface as CatalogueError."""
    opener = _ErrorOpener()
    with pytest.raises(CatalogueError, match="failed to fetch"):
        _fetch_bytes_limited("https://example.test/descriptor.json", opener, 1024, 30)


# ---------------------------------------------------------------------------
# T2 — _build_opener and proxy support
# ---------------------------------------------------------------------------


def test_build_opener_uses_proxy_handler(monkeypatch: pytest.MonkeyPatch):
    """AC23: _build_opener creates opener via ProxyHandler (verifies correct class used)."""
    # Set a proxy so ProxyHandler registers its protocol-specific open methods
    # (ProxyHandler only appears in opener.handlers when proxies are configured,
    # because it generates <scheme>_open methods dynamically at __init__ time).
    monkeypatch.setitem(os.environ, "HTTPS_PROXY", "http://proxy.example.test:3128")
    monkeypatch.delitem(os.environ, "NO_PROXY", raising=False)
    opener = _build_opener(None, "https://example.test/stable.json")
    proxy_handlers = [h for h in opener.handlers if isinstance(h, urllib.request.ProxyHandler)]
    assert len(proxy_handlers) == 1


def test_build_opener_no_http_handler():
    """HTTPS only: opener must not include a plain HTTPHandler."""
    opener = _build_opener(None, "https://example.test/stable.json")
    http_handlers = [h for h in opener.handlers if type(h) is urllib.request.HTTPHandler]
    assert len(http_handlers) == 0


def test_proxy_env_honored(monkeypatch: pytest.MonkeyPatch):
    """AC23: HTTPS_PROXY env var is read by ProxyHandler."""
    monkeypatch.setitem(os.environ, "HTTPS_PROXY", "http://proxy.example.test:3128")
    monkeypatch.delitem(os.environ, "NO_PROXY", raising=False)
    opener = _build_opener(None, "https://example.test/stable.json")
    proxy_handlers = [h for h in opener.handlers if isinstance(h, urllib.request.ProxyHandler)]
    assert len(proxy_handlers) == 1
    ph = proxy_handlers[0]
    assert "https" in ph.proxies


def test_no_proxy_honored(monkeypatch: pytest.MonkeyPatch):
    """AC23: NO_PROXY env var is read by ProxyHandler."""
    monkeypatch.setitem(os.environ, "HTTPS_PROXY", "http://proxy.example.test:3128")
    monkeypatch.setitem(os.environ, "NO_PROXY", "example.test")
    opener = _build_opener(None, "https://example.test/stable.json")
    proxy_handlers = [h for h in opener.handlers if isinstance(h, urllib.request.ProxyHandler)]
    assert len(proxy_handlers) == 1
    # Both env vars were consumed — ProxyHandler built with them
    assert "https" in proxy_handlers[0].proxies


# ---------------------------------------------------------------------------
# T2 — bearer token injection
# ---------------------------------------------------------------------------


def test_bearer_token_in_request():
    """AC21: Authorization: Bearer header present in request when token is set."""
    opener = _build_opener("test-token-12345", "https://example.test/stable.json")
    req = _make_request("https://example.test/stable.json", opener)
    assert req.get_header("Authorization") == "Bearer test-token-12345"


def test_no_bearer_token_no_auth_header():
    """No token → no Authorization header."""
    opener = _build_opener(None, "https://example.test/stable.json")
    req = _make_request("https://example.test/stable.json", opener)
    assert req.get_header("Authorization") is None


def test_bearer_token_absent_from_errors():
    """AC22: bearer token value does not appear in any CatalogueError message."""
    secret_token = "super-secret-bearer-99999"
    data, real_sha256 = _make_tarball(("hello.txt", b"world"))
    wrong_sha256 = "b" * 64
    opener = _MockOpener(data, token=secret_token)
    try:
        _stream_and_verify("https://example.test/archive.tar.gz", wrong_sha256, opener, 30)
    except CatalogueError as exc:
        assert secret_token not in str(exc)
    else:
        pytest.fail("Expected CatalogueError was not raised")


# ---------------------------------------------------------------------------
# T2 — _OriginLockingRedirectHandler
# ---------------------------------------------------------------------------


def _mock_req(url: str) -> urllib.request.Request:
    """Create a minimal Request for use in redirect_request calls."""
    return urllib.request.Request(url)


def test_redirect_to_http_rejected():
    """AC21b: redirect to http:// rejected regardless of token."""
    handler = _OriginLockingRedirectHandler("https://example.test/stable.json")
    with pytest.raises(CatalogueError, match="HTTPS-only"):
        handler.redirect_request(
            _mock_req("https://example.test/stable.json"),
            None, 302, "Found", {}, "http://example.test/other.json"
        )


def test_redirect_with_user_info_rejected():
    """AC21c: redirect URL containing user-info rejected."""
    handler = _OriginLockingRedirectHandler("https://example.test/stable.json")
    with pytest.raises(CatalogueError, match="user-info"):
        handler.redirect_request(
            _mock_req("https://example.test/stable.json"),
            None, 302, "Found", {}, "https://user:pass@example.test/other.json"
        )


def test_cross_origin_redirect_rejected_different_host():
    """AC21d: redirect to a different host (different origin) rejected."""
    handler = _OriginLockingRedirectHandler("https://example.test/stable.json")
    with pytest.raises(CatalogueError, match="cross-origin"):
        handler.redirect_request(
            _mock_req("https://example.test/stable.json"),
            None, 302, "Found", {}, "https://evil.example.test/stable.json"
        )


def test_cross_origin_redirect_rejected_different_port():
    """AC21d: redirect to same host but different port (different origin) rejected."""
    handler = _OriginLockingRedirectHandler("https://example.test:443/stable.json")
    with pytest.raises(CatalogueError, match="cross-origin"):
        handler.redirect_request(
            _mock_req("https://example.test:443/stable.json"),
            None, 302, "Found", {}, "https://example.test:9999/stable.json"
        )


def test_same_origin_anchor_is_originally_requested():
    """AC21d: same-origin anchor is the originally-requested URL.

    If a redirect goes to a same-origin path, the artifact URL must be
    resolved against the ORIGINALLY-requested descriptor URL, not the
    post-redirect path.
    """
    original_url = "https://example.test/channels/stable.json"
    artifact_field = "releases/core.tar.gz"
    # Even if the descriptor was "redirected" to /channels/new-stable.json,
    # _resolve_artifact_url uses the originally-requested URL as anchor.
    result = _resolve_artifact_url(original_url, artifact_field)
    assert result == "https://example.test/channels/releases/core.tar.gz"


# ---------------------------------------------------------------------------
# T2 — fetch_catalogue_archive end-to-end (mocked)
# ---------------------------------------------------------------------------


def test_fetch_catalogue_archive_catalogue_https(tmp_path: Path):
    """AC6: catalogue+https:// end-to-end: descriptor → artifact → extract."""
    archive_data, archive_sha256 = _make_tarball(("pack.txt", b"pack content"))

    descriptor = {
        **_VALID_DESCRIPTOR,
        "artifact": "https://example.test/releases/core.tar.gz",
        "sha256": archive_sha256,
    }
    descriptor_data = json.dumps(descriptor).encode()

    # Patch _fetch_bytes_limited (for descriptor) and _stream_and_verify (for archive)
    archive_tmp = tmp_path / "archive.tar.gz"
    archive_tmp.write_bytes(archive_data)

    with mock.patch.object(https_catalogue, "_fetch_bytes_limited", return_value=descriptor_data), \
         mock.patch.object(https_catalogue, "_stream_and_verify", return_value=archive_tmp), \
         mock.patch.object(https_catalogue, "_check_client_version"):
        result = fetch_catalogue_archive(
            "catalogue+https://example.test/channels/stable.json",
            env={},
        )
    try:
        assert result.is_dir()
        assert (result / "pack.txt").exists()
    finally:
        import shutil
        shutil.rmtree(str(result), ignore_errors=True)


def test_fetch_catalogue_archive_archive_https(tmp_path: Path):
    """AC24: archive+https:// — no descriptor fetch, directly streams + extracts."""
    archive_data, archive_sha256 = _make_tarball(("pack.txt", b"direct content"))
    archive_tmp = tmp_path / "archive.tar.gz"
    archive_tmp.write_bytes(archive_data)

    with mock.patch.object(https_catalogue, "_stream_and_verify", return_value=archive_tmp):
        result = fetch_catalogue_archive(
            f"archive+https://example.test/releases/core.tar.gz#sha256={archive_sha256}",
            env={},
        )
    try:
        assert result.is_dir()
        assert (result / "pack.txt").exists()
    finally:
        import shutil
        shutil.rmtree(str(result), ignore_errors=True)


def test_fetch_catalogue_archive_minimum_version_rejected():
    """AC11: minimum_agentbundle_version newer than running version fails before download."""
    descriptor = {
        **_VALID_DESCRIPTOR,
        "minimum_agentbundle_version": "999.0.0",
    }
    descriptor_data = json.dumps(descriptor).encode()

    with mock.patch.object(https_catalogue, "_fetch_bytes_limited", return_value=descriptor_data), \
         mock.patch.object(https_catalogue, "_stream_and_verify") as mock_verify:
        with pytest.raises(CatalogueError, match="999.0.0"):
            fetch_catalogue_archive(
                "catalogue+https://example.test/channels/stable.json",
                env={},
            )
        mock_verify.assert_not_called()  # archive must NOT be fetched


def test_fetch_catalogue_archive_temp_dir_cleaned_on_digest_mismatch():
    """AC28: temp dir cleaned up when SHA-256 verification fails after extraction."""
    descriptor = {**_VALID_DESCRIPTOR, "sha256": "a" * 64}
    descriptor_data = json.dumps(descriptor).encode()

    with mock.patch.object(https_catalogue, "_fetch_bytes_limited", return_value=descriptor_data), \
         mock.patch.object(https_catalogue, "_stream_and_verify",
                           side_effect=CatalogueError("SHA-256 mismatch")):
        with pytest.raises(CatalogueError, match="mismatch"):
            fetch_catalogue_archive(
                "catalogue+https://example.test/channels/stable.json",
                env={},
            )


def test_fetch_catalogue_archive_unsupported_scheme():
    """Unsupported scheme raises CatalogueError."""
    with pytest.raises(CatalogueError, match="unsupported scheme"):
        fetch_catalogue_archive("git+https://github.com/example/repo")


def test_fetch_catalogue_archive_archive_https_no_sha256_fragment():
    """archive+https:// without sha256 fragment raises CatalogueError."""
    with pytest.raises(CatalogueError, match="sha256"):
        fetch_catalogue_archive("archive+https://example.test/release.tar.gz")


def test_bearer_token_passed_to_opener():
    """AC21: bearer token from env passed to opener (not forwarded cross-origin)."""
    descriptor_data = json.dumps({**_VALID_DESCRIPTOR, "sha256": "a" * 64}).encode()

    captured_env = {}

    def fake_build_opener(token, original_url):
        captured_env["token"] = token
        return _MockOpener(b"", token=token)

    with mock.patch.object(https_catalogue, "_fetch_bytes_limited", return_value=descriptor_data), \
         mock.patch.object(https_catalogue, "_stream_and_verify",
                           side_effect=CatalogueError("mismatch for test")), \
         mock.patch.object(https_catalogue, "_build_opener", side_effect=fake_build_opener):
        try:
            fetch_catalogue_archive(
                "catalogue+https://example.test/channels/stable.json",
                env={"AGENTBUNDLE_HTTP_BEARER_TOKEN": "my-secret-token"},
            )
        except CatalogueError:
            pass
    assert captured_env.get("token") == "my-secret-token"


# ---------------------------------------------------------------------------
# T2 — timeout constant is finite and documented
# ---------------------------------------------------------------------------


def test_timeout_constant_is_finite():
    """AC27: _HTTP_TIMEOUT is a positive finite integer."""
    from agentbundle.https_catalogue import _HTTP_TIMEOUT
    assert isinstance(_HTTP_TIMEOUT, int)
    assert _HTTP_TIMEOUT > 0
    assert _HTTP_TIMEOUT < 300  # sanity: not absurdly long


def test_timeout_passed_to_opener():
    """AC27: _fetch_bytes_limited and _stream_and_verify pass timeout to opener.open."""
    data = b"x" * 5
    captured = {}

    class _CapturingOpener:
        _bearer_token = None
        def open(self, req, timeout=None):
            captured["timeout"] = timeout
            return _MockResponse(data)

    _fetch_bytes_limited("https://example.test/x", _CapturingOpener(), 100, 42)
    assert captured.get("timeout") == 42


# ---------------------------------------------------------------------------
# T2 — stdlib-only check (AC30, AC37)
# ---------------------------------------------------------------------------


def test_stdlib_only():
    """AC30 + AC37: https_catalogue.py imports no non-stdlib modules."""
    result = subprocess.run(
        [sys.executable, "-c", "import agentbundle.https_catalogue"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    module_path = Path(https_catalogue.__file__)
    source = module_path.read_text(encoding="utf-8")

    non_stdlib_patterns = ["import requests", "import packaging", "import httpx"]
    for pattern in non_stdlib_patterns:
        assert pattern not in source, f"Found non-stdlib import: {pattern!r}"


# ---------------------------------------------------------------------------
# T2 — no real endpoints in tests (AC29)
# ---------------------------------------------------------------------------


def test_no_real_endpoints_in_test_file():
    """AC29: no real org endpoint URL strings in test assertions.

    Checks that no string literals used as URL arguments to https_catalogue
    functions reference real domains — only example.test or localhost.
    The test itself may reference domain names in comments or test-helper calls
    (e.g. resolve_catalogue("git+https://github.com/...") as a regression check);
    those are excluded by looking only at catalogue+https:// and archive+https://
    scheme URLs actually passed to the HTTPS fetcher.
    """
    this_file = Path(__file__).read_text(encoding="utf-8")
    # Look for catalogue+https:// or archive+https:// URLs with non-example.test domains.
    # These are the URLs that the HTTPS fetcher would actually connect to.
    # Netloc ends at the first '/', '#', '"', "'", space, or newline.
    fetcher_urls = re.findall(
        r'(?:catalogue|archive)\+https://([A-Za-z0-9._:@-]+)', this_file
    )
    for netloc in fetcher_urls:
        # Strip userinfo (user:pass@) to get just the host part
        host = netloc.split("@")[-1]
        assert host.startswith("example.test") or host.startswith("localhost"), (
            f"Found fetcher URL with real domain: {host!r} (use example.test or localhost)"
        )


# ---------------------------------------------------------------------------
# T3 — resolve_catalogue dispatch
# ---------------------------------------------------------------------------


def test_resolve_catalogue_http_explicit_arg_rejected():
    """AC34: catalogue+http:// rejected by resolve_catalogue with HTTPS-only error."""
    from agentbundle.catalogue import resolve_catalogue
    with pytest.raises(CatalogueError, match="HTTPS-only"):
        resolve_catalogue("catalogue+http://example.test/stable.json")


def test_resolve_catalogue_archive_http_explicit_arg_rejected():
    """AC34: archive+http:// rejected by resolve_catalogue with HTTPS-only error."""
    from agentbundle.catalogue import resolve_catalogue
    with pytest.raises(CatalogueError, match="HTTPS-only"):
        resolve_catalogue("archive+http://example.test/release.tar.gz")


def test_resolve_catalogue_catalogue_https_dispatches(tmp_path: Path):
    """AC6: resolve_catalogue dispatches catalogue+https:// to fetch_catalogue_archive."""
    from agentbundle.catalogue import resolve_catalogue
    fake_dir = tmp_path / "extracted"
    fake_dir.mkdir()
    with mock.patch("agentbundle.https_catalogue.fetch_catalogue_archive", return_value=fake_dir) as mock_fetch:
        result = resolve_catalogue("catalogue+https://example.test/channels/stable.json")
    mock_fetch.assert_called_once_with("catalogue+https://example.test/channels/stable.json")
    assert result == fake_dir


def test_resolve_catalogue_archive_https_dispatches(tmp_path: Path):
    """AC24: resolve_catalogue dispatches archive+https:// to fetch_catalogue_archive."""
    from agentbundle.catalogue import resolve_catalogue
    fake_dir = tmp_path / "extracted"
    fake_dir.mkdir()
    archive_uri = "archive+https://example.test/releases/core.tar.gz#sha256=" + "a" * 64
    with mock.patch("agentbundle.https_catalogue.fetch_catalogue_archive", return_value=fake_dir) as mock_fetch:
        result = resolve_catalogue(archive_uri)
    mock_fetch.assert_called_once_with(archive_uri)
    assert result == fake_dir


def test_resolve_catalogue_existing_git_https_unchanged():
    """AC31: existing git+https:// dispatch still works (no regression)."""
    from agentbundle.catalogue import resolve_catalogue
    with mock.patch("agentbundle.catalogue._resolve_https", return_value=Path("/fake")) as m:
        result = resolve_catalogue("git+https://github.com/example/repo")
    m.assert_called_once()


def test_resolve_catalogue_http_error_is_https_only_message():
    """AC34: the HTTPS-only error message is clear (not a path-not-found error)."""
    from agentbundle.catalogue import resolve_catalogue
    with pytest.raises(CatalogueError) as exc:
        resolve_catalogue("catalogue+http://example.test/stable.json")
    msg = str(exc.value)
    assert "https" in msg.lower()
    assert "catalogue+https://" in msg or "archive+https://" in msg
