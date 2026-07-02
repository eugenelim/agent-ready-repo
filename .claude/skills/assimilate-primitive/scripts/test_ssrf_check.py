"""Tests for ssrf_check.py (RFC-0059 URL-source SSRF confinement). No network:
positive cases use IP literals or an unresolvable host; blocked cases use
private/metadata/loopback literals and `localhost` (resolved locally)."""

from __future__ import annotations

import pytest

import ssrf_check as s


@pytest.mark.parametrize("url", ["https://8.8.8.8/x", "https://example.invalid/y",
                                 "git://8.8.8.8/repo.git", "ssh://8.8.8.8/repo"])
def test_allowed_urls_pass(url: str) -> None:
    s.check_url(url)  # must not raise


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://8.8.8.8/x",
                                 "gopher://8.8.8.8/x", "http://8.8.8.8/x", "data:text/plain,hi"])
def test_rejected_schemes(url: str) -> None:
    with pytest.raises(s.SsrfRejected):
        s.check_url(url)


@pytest.mark.parametrize("url", [
    "https://169.254.169.254/latest/meta-data/",  # cloud metadata
    "https://127.0.0.1/x",                          # loopback
    "https://10.0.0.5/x",                           # private
    "https://192.168.1.1/x",                        # private
    "https://localhost/x",                          # resolves to loopback
])
def test_blocked_ip_ranges(url: str) -> None:
    with pytest.raises(s.SsrfRejected):
        s.check_url(url)


def test_no_host_rejected() -> None:
    with pytest.raises(s.SsrfRejected):
        s.check_url("https:///nohost")


def test_check_source_classifies() -> None:
    assert s.check_source("/local/path/skill") == "path"
    assert s.check_source("https://8.8.8.8/x") == "url"
    with pytest.raises(s.SsrfRejected):
        s.check_source("file:///etc/passwd")


def test_looks_like_url() -> None:
    assert s.looks_like_url("https://x")
    assert not s.looks_like_url("/local/path")
    assert not s.looks_like_url("./relative/path")


def test_windows_drive_path_is_a_path_not_url() -> None:
    # A single-letter scheme is a Windows drive, not a URL — must not be rejected.
    assert not s.looks_like_url(r"C:\Users\x\skill")
    assert s.check_source(r"C:\Users\x\skill") == "path"
    assert s.check_source("D:/repos/thing") == "path"
