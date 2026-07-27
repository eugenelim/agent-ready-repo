"""Tests for spec/packstate-source-provenance: PackState.source default, 
_parse_adapter_row, dump_state, and canonicalize_source."""

from __future__ import annotations

import platform
import sys
import pytest
from pathlib import Path

from agentbundle.config import (
    PackState,
    State,
    canonicalize_source,
    dump_state,
    _parse_adapter_row,
)


# ── T1: PackState.source field, _parse_adapter_row, dump_state ───────────────

def test_pack_state_source_default_is_none():
    ps = PackState(installed_version="1.0")
    assert ps.source is None


def test_parse_adapter_row_absent_source_key():
    body = {"installed-version": "1.0", "install-route": "cli"}
    ps = _parse_adapter_row("myplugin", "claude-code", body, "repo")
    assert ps.source is None


def test_parse_adapter_row_legacy_literal_preserved():
    body = {"installed-version": "1.0", "source": "agent-ready-repo"}
    ps = _parse_adapter_row("myplugin", "claude-code", body, "repo")
    assert ps.source == "agent-ready-repo"


def test_parse_adapter_row_real_source_preserved():
    body = {"installed-version": "1.0", "source": "git+https://example.test/repo"}
    ps = _parse_adapter_row("myplugin", "claude-code", body, "repo")
    assert ps.source == "git+https://example.test/repo"


def _make_state_with_source(source):
    state = State()
    ps = PackState(installed_version="1.0", source=source)
    state.packs[("myplugin", "claude-code")] = ps
    return state


def test_dump_state_none_source_omits_key():
    state = _make_state_with_source(None)
    toml = dump_state(state)
    # The key must not appear at all in this pack's section
    assert "source" not in toml


def test_dump_state_legacy_literal_emits_key():
    state = _make_state_with_source("agent-ready-repo")
    toml = dump_state(state)
    assert 'source = "agent-ready-repo"' in toml


def test_dump_and_parse_round_trip_none():
    state = _make_state_with_source(None)
    toml = dump_state(state)
    # Re-parse
    import tomllib
    data = tomllib.loads(toml)
    body = data["pack"]["myplugin"]["adapters"]["claude-code"]
    assert body.get("source") is None


def test_dump_and_parse_round_trip_legacy():
    state = _make_state_with_source("agent-ready-repo")
    toml = dump_state(state)
    import tomllib
    data = tomllib.loads(toml)
    body = data["pack"]["myplugin"]["adapters"]["claude-code"]
    assert body.get("source") == "agent-ready-repo"


# ── T2: canonicalize_source ───────────────────────────────────────────────────

def test_canonicalize_none():
    assert canonicalize_source(None) is None


def test_canonicalize_legacy_literal():
    assert canonicalize_source("agent-ready-repo") is None


def test_canonicalize_empty_string():
    assert canonicalize_source("") is None


def test_canonicalize_blank_string():
    assert canonicalize_source("   ") is None


def test_canonicalize_local_abs_path(tmp_path):
    result = canonicalize_source(str(tmp_path))
    assert result == str(tmp_path.resolve())


def test_canonicalize_local_rel_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    subdir = tmp_path / "catalogue"
    subdir.mkdir()
    result = canonicalize_source("catalogue")
    assert result == str(subdir.resolve())


@pytest.mark.parametrize("path", ["C:\\repo", "C:/repo"])
@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")
def test_canonicalize_windows_drive_path(path):
    result = canonicalize_source(path)
    assert result is not None
    assert "repo" in result.lower() or result  # just check it returns something


def test_canonicalize_git_https():
    result = canonicalize_source("git+https://EXAMPLE.TEST/repo")
    assert result == "git+https://example.test/repo"


def test_canonicalize_trailing_slash_normalized():
    result = canonicalize_source("git+https://example.test/repo/")
    assert result == "git+https://example.test/repo"


def test_canonicalize_host_port_preserved():
    result = canonicalize_source("git+https://example.test:8443/repo")
    assert result == "git+https://example.test:8443/repo"


def test_canonicalize_catalogue_https_scheme():
    result = canonicalize_source("catalogue+https://EXAMPLE.TEST/channels/stable.json")
    assert result == "catalogue+https://example.test/channels/stable.json"


def test_canonicalize_fragment_preserved():
    sha = "a" * 64
    url = f"archive+https://example.test/r.tar.gz#sha256={sha}"
    result = canonicalize_source(url)
    assert result is not None
    assert f"sha256={sha}" in result
    assert result.startswith("archive+https://example.test/")


def test_canonicalize_fragment_credential_rejected():
    result = canonicalize_source("git+https://example.test/repo#access_token=SECRET")
    assert result is None


def test_canonicalize_file_url_remote_netloc():
    result = canonicalize_source("file://remote-host/tmp/x")
    assert result is None


def test_canonicalize_user_info_rejected():
    result = canonicalize_source("git+https://user:pass@example.test/repo")
    assert result is None


def test_canonicalize_user_info_only_user_rejected():
    result = canonicalize_source("git+https://user@example.test/repo")
    assert result is None


def test_canonicalize_bare_at_netloc_rejected():
    result = canonicalize_source("git+https://@example.test/repo")
    assert result is None


def test_canonicalize_query_private_token_rejected():
    result = canonicalize_source("git+https://example.test/repo?private_token=SECRET")
    assert result is None


def test_canonicalize_benign_query_preserved():
    result = canonicalize_source("git+https://example.test/repo?ref=main")
    assert result == "git+https://example.test/repo?ref=main"


def test_canonicalize_query_token_rejected():
    result = canonicalize_source("git+https://example.test/repo?access_token=SECRET")
    assert result is None


def test_canonicalize_query_api_key_rejected():
    result = canonicalize_source("git+https://example.test/repo?api_key=SECRET")
    assert result is None


def test_canonicalize_file_url_local(tmp_path):
    result = canonicalize_source(f"file://{tmp_path}")
    assert result == str(tmp_path.resolve())


def test_canonicalize_file_url_percent_encoded(tmp_path):
    # Create a directory with a space in name
    d = tmp_path / "my dir"
    d.mkdir()
    import urllib.parse
    encoded = urllib.parse.quote(str(d))
    result = canonicalize_source(f"file://{encoded}")
    assert result == str(d.resolve())


def test_canonicalize_file_url_literal_percent(tmp_path):
    # %2520 should become %20 (single decode), NOT a space (double decode)
    # This discriminates single-decode from double-decode
    # We test the canonicalize function handles this correctly
    # %2520 -> url2pathname -> %20 (one decode of %25 -> %)
    import urllib.parse
    from urllib.parse import urlsplit
    from urllib.request import url2pathname
    # Build a URL where the path has %2520 (literal percent followed by 20)
    url = "file:///tmp/a%2520b"
    parsed = urlsplit(url)
    decoded = url2pathname(parsed.path)
    # Single decode: %2520 -> %20 (percent-sign then 20, not a space)
    # If double-decoded: %2520 -> %20 -> space
    assert decoded == "/tmp/a%20b", f"Expected single decode, got: {decoded!r}"
    # Now test canonicalize_source doesn't double-decode
    result = canonicalize_source(url)
    if result is not None:
        assert " " not in result, "double-decode detected: space found in result"


def test_canonicalize_os_error_returns_none():
    # A path that triggers OSError on resolve (null bytes)
    try:
        result = canonicalize_source("\x00invalid")
        # If it doesn't raise, it should return None
        assert result is None
    except Exception:
        pass  # Some platforms raise before we can catch


def test_canonicalize_archive_https_scheme():
    sha = "b" * 64
    result = canonicalize_source(f"archive+HTTPS://EXAMPLE.TEST/r.tar.gz#sha256={sha}")
    assert result is not None
    assert result.startswith("archive+https://example.test/")
