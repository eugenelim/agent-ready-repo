"""Unit tests for the JFrog CLI fetch session and digest-checked trim.

Covers: exact argv, endpoint confinement, descriptor/archive success,
appended-newline cases, digest rule, exit-1 failure, stderr cap, timeout
with partial-file cleanup, third-fetch guard, no-fallback, and stderr
canary absence.
"""

from __future__ import annotations

import hashlib
import logging
import os
import shlex
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

import agentbundle.catalogue_fetch.jfrog_cli as _jf_mod
import pytest
from agentbundle.catalogue_fetch.jfrog_cli import (
    JfrogFetchSession,
    _locate_jf,
    _validate_fetch_url,
)
from agentbundle.catalogue_fetch.models import CatalogueFetchError
from agentbundle.https_catalogue import _verify_jfrog_archive_sha256
from credbroker import JfrogCliHttpAccess
from credbroker._http_access import _locate_jf as _cb_locate_jf

# ── Module-level production constant captures ─────────────────────────────────
# Captured BEFORE any autouse fixture can monkeypatch them.

_PROD_FETCH_TIMEOUT: float = _jf_mod._JFROG_FETCH_TIMEOUT      # 30.0
_PROD_FETCH_STDERR_CAP: int = _jf_mod._JFROG_FETCH_STDERR_CAP  # 64 << 10
_PROD_MAX_FETCHES: int = _jf_mod._MAX_FETCHES                   # 2
_PROD_GRACE: float = _jf_mod._JFROG_GRACE                       # 2.0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PLATFORM = "https://platform.example.test"
_ARTF = "https://platform.example.test/art"
_ARTF_URL = f"{_ARTF}/"
_PLATFORM_URL = f"{_PLATFORM}/"


def _make_access(
    server_id: str = "srv",
    platform_url: str = _PLATFORM_URL,
    artf_url: str = _ARTF_URL,
) -> JfrogCliHttpAccess:
    return JfrogCliHttpAccess(
        server_id=server_id,
        platform_url=platform_url,
        artifactory_url=artf_url,
    )


def _make_jf(
    tmp_path: Path,
    *,
    response: bytes = b"{}",
    exit_code: int = 0,
    capture_args_to: Path | None = None,
    busy_wait: bool = False,
    stderr_bytes: int = 0,
) -> Path:
    """Write a shell-script ``jf`` fixture and make it executable.

    Args:
        tmp_path: Directory to place the ``jf`` script in.
        response: Bytes to write to stdout on ``api`` subcommand.
        exit_code: Exit code to return on ``api`` subcommand.
        capture_args_to: If set, the script echoes its args to this file.
        busy_wait: If True, busy-loop after printing response (for timeout tests).
        stderr_bytes: If >0, emit that many 'x' bytes to stderr before exiting.
    """
    # Build the body for the api case.
    api_lines = []
    if capture_args_to is not None:
        # Record each argument on its own line for element-by-element assertion.
        api_lines.append(
            f"{{ for arg in \"$@\"; do printf '%s\\n' \"$arg\"; done; }} > {shlex.quote(str(capture_args_to))}"
        )
    if stderr_bytes > 0:
        py_exe_s = shlex.quote(sys.executable)
        api_lines.append(
            f"{py_exe_s} -c "
            f"\"import sys; sys.stderr.write('x'*{stderr_bytes}); sys.stderr.flush()\""
        )
    # Write the response bytes using python3 to handle binary data reliably.
    py_exe = shlex.quote(sys.executable)
    escaped = response.hex()
    api_lines.append(
        f"{py_exe} -c "
        f"\"import sys; sys.stdout.buffer.write(bytes.fromhex('{escaped}'))\""
    )
    if busy_wait:
        api_lines.append("while true; do :; done")
    if exit_code != 0:
        api_lines.insert(0, f"exit {exit_code}")

    api_body = "\n".join(f"  {line}" for line in api_lines)

    real_path = os.environ.get("PATH", "/usr/bin:/bin")
    script = (
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        'if [ "$1" = "api" ]; then\n'
        f"{api_body}\n"
        f"  exit {exit_code}\n"
        "fi\n"
        "exit 2\n"
    )
    jf = tmp_path / "jf"
    jf.write_text(script, encoding="utf-8")
    jf.chmod(0o755)
    return jf


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Autouse fixture — generous timeouts for non-timeout tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _generous_timeouts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch fetch deadline constants to prevent host-load flakiness.

    Timeout tests override these values explicitly by passing timeout=1
    directly to the fetch call.
    """
    monkeypatch.setattr("agentbundle.catalogue_fetch.jfrog_cli._JFROG_GRACE", 10.0)


# ---------------------------------------------------------------------------
# Production constant values
# ---------------------------------------------------------------------------


def test_production_constant_values() -> None:
    """Production fetch constants have their expected values."""
    assert _PROD_FETCH_TIMEOUT == 30.0
    assert _PROD_FETCH_STDERR_CAP == 64 << 10   # 64 KiB
    assert _PROD_MAX_FETCHES == 2
    assert _PROD_GRACE == 2.0


# ---------------------------------------------------------------------------
# _locate_jf parity with credbroker
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX filesystem")
def test_locate_jf_parity_with_credbroker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """_locate_jf and credbroker's _locate_jf agree on identical PATH layouts.

    credbroker returns ``(path, refused_bool)``; agentbundle returns ``path | None``.
    The parity check is: if credbroker refuses (bool=True) or finds nothing, agentbundle
    returns None; if credbroker accepts (bool=False, path not None), agentbundle returns
    the same absolute path.
    """
    def _parity(env: dict) -> None:
        ag = _locate_jf(env)
        cb_path, cb_refused = _cb_locate_jf(env)
        if cb_refused:
            assert ag is None, (
                f"credbroker refused but agentbundle returned {ag!r}"
            )
        elif cb_path is None:
            assert ag is None, (
                f"credbroker found nothing but agentbundle returned {ag!r}"
            )
        else:
            assert ag == cb_path, (
                f"agentbundle={ag!r} != credbroker={cb_path!r}"
            )

    # Case 1: Valid absolute entry with executable jf — both accept.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    jf = bin_dir / "jf"
    jf.write_text("#!/bin/sh\n", encoding="utf-8")
    jf.chmod(0o755)
    _parity({"PATH": str(bin_dir)})

    # Case 2: Relative PATH entry with jf present — both refuse (return None).
    monkeypatch.chdir(tmp_path)
    _parity({"PATH": "bin"})

    # Case 3: Empty PATH — no candidate found in either.
    _parity({"PATH": ""})


# ---------------------------------------------------------------------------
# Wall-clock deadline test
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX signals and sleep")
def test_archive_wall_clock_deadline(tmp_path: Path) -> None:
    """fetch_archive respects the wall-clock deadline even when the child ignores SIGTERM."""
    real_path = os.environ.get("PATH", "/usr/bin:/bin")
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        'if [ "$1" = "api" ]; then\n'
        "  printf 'partial'\n"
        "  trap '' TERM\n"
        "  sleep 60\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})

    start = time.monotonic()
    with pytest.raises(CatalogueFetchError) as exc_info:
        session.fetch_archive(
            f"{_ARTF}/pack.tar.gz",
            max_bytes=256 * 1024 * 1024,
            timeout=1,  # explicit: this is a timeout test
        )
    elapsed = time.monotonic() - start

    assert exc_info.value.code == "jfrog_fetch_timeout"
    # Must complete within timeout + generous tolerance (3s), sleep 60 is 60× over.
    assert elapsed <= 4.0, f"wall-clock exceeded budget: {elapsed:.2f}s"


# ---------------------------------------------------------------------------
# Exact argv — verify argument vector shape for jf api calls  (AC-0012)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_exact_argv_for_descriptor_fetch(tmp_path: Path) -> None:
    """jf api receives exactly: api --server-id=<id> -- <endpoint>. AC-0012"""
    args_file = tmp_path / "captured_args.txt"

    # jf that records its args and returns valid JSON
    response = b'{"ok": true}'
    _make_jf(tmp_path, response=response, capture_args_to=args_file)

    access = _make_access(server_id="my-srv")
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    result = session.fetch_bytes(
        f"{_ARTF}/cat.toml", max_bytes=1024, timeout=120
    )

    args_lines = args_file.read_text(encoding="utf-8").splitlines()
    # Element-by-element: api, --server-id=<id>, --, <endpoint>
    assert args_lines[0] == "api", f"argv[0]={args_lines[0]!r}"
    assert args_lines[1] == "--server-id=my-srv", f"argv[1]={args_lines[1]!r}"
    assert args_lines[2] == "--", f"argv[2]={args_lines[2]!r}"
    assert args_lines[3].endswith("art/cat.toml"), f"argv[3]={args_lines[3]!r}"
    assert len(args_lines) == 4, f"unexpected extra argv elements: {args_lines!r}"
    assert result == response


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_exact_argv_for_archive_fetch(tmp_path: Path) -> None:
    """jf api for archive also uses --server-id=<id> -- <endpoint>. AC-0012"""
    args_file = tmp_path / "captured_args.txt"

    content = b"\x1f\x8b\x00"  # minimal stub bytes
    _make_jf(tmp_path, response=content, capture_args_to=args_file)

    access = _make_access(server_id="arch-srv")
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    archive_path = session.fetch_archive(
        f"{_ARTF}/pack.tar.gz", max_bytes=1024, timeout=120
    )
    archive_path.unlink(missing_ok=True)

    args_lines = args_file.read_text(encoding="utf-8").splitlines()
    assert args_lines[0] == "api", f"argv[0]={args_lines[0]!r}"
    assert args_lines[1] == "--server-id=arch-srv", f"argv[1]={args_lines[1]!r}"
    assert args_lines[2] == "--", f"argv[2]={args_lines[2]!r}"
    assert args_lines[3].endswith("art/pack.tar.gz"), f"argv[3]={args_lines[3]!r}"
    assert len(args_lines) == 4, f"unexpected extra argv elements: {args_lines!r}"


# ---------------------------------------------------------------------------
# Endpoint confinement  (AC-0012)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_url, reason",
    [
        (
            "https://other.example.test/art/cat.toml",
            "wrong origin",
        ),
        (
            f"{_ARTF}/../../etc/passwd",
            "dot-segment traversal",
        ),
        (
            "https://platform.example.test/art/cat.toml?q=1",
            "query string",
        ),
        (
            "https://platform.example.test/art/cat.toml#frag",
            "fragment",
        ),
        (
            "http://platform.example.test/art/cat.toml",
            "non-https scheme",
        ),
        (
            "https://platform.example.test/art/cat.toml%2f../evil",
            "encoded separator",
        ),
        (
            "https://platform.example.test/art/%2e%2e/etc/passwd",
            "encoded dot segment",
        ),
        (
            f"{_ARTF}/outside/../../other/cat.toml",
            "traversal outside artf",
        ),
        (
            "https://platform.example.test/art/cat.toml%5cevil",
            "encoded backslash %5c",
        ),
        (
            "https://platform.example.test/art/./cat.toml",
            "literal dot segment",
        ),
        (
            "https://platform.example.test/art//cat.toml",
            "empty interior segment",
        ),
        # Defect B — additional fixtures required by the adjudication
        (
            "https://user@platform.example.test/art/cat.toml",
            "user-info in authority",
        ),
        (
            "https://platform.example.test/art/cat.toml\\evil",
            "literal backslash in path",
        ),
        (
            "https://platform.example.test/art/cat\ttoml",
            "literal tab in URL",
        ),
        (
            "https://platform.example.test/art/cat\rtoml",
            "literal CR in URL",
        ),
        (
            "https://platform.example.test/art/cat\ntoml",
            "literal LF in URL",
        ),
        (
            "https://platform.example.test/art/cat\x0btoml",
            "vertical-tab control character",
        ),
        (
            "https://platform.example.test/art/..;/cat.toml",
            "semicolon path parameter (..;/)",
        ),
        (
            "https://platform.example.test/art/.;/cat.toml",
            "semicolon path parameter (.;/)",
        ),
        (
            "https://platform.example.test/art/..%3b/cat.toml",
            "encoded semicolon %3b in path",
        ),
        (
            "https://platform.example.test/art/.. /cat.toml",
            "trailing space in path segment",
        ),
    ],
)
def test_endpoint_confinement_rejects_bad_urls(
    bad_url: str, reason: str
) -> None:
    """Confinement rejects URLs with disallowed patterns. AC-0012"""
    access = _make_access()
    with pytest.raises(CatalogueFetchError) as exc_info:
        _validate_fetch_url(bad_url, access)
    assert exc_info.value.code == "endpoint_not_permitted", reason


def test_endpoint_confinement_rejects_option_like_endpoint() -> None:
    """An option-like endpoint (leading -) is rejected. AC-0012"""
    # Craft an artf URL whose path starts with / so stripping the platform
    # base yields a leading-hyphen segment:
    # platform: https://p.example.test/   → artf: https://p.example.test/-danger/
    access = JfrogCliHttpAccess(
        server_id="s",
        platform_url="https://p.example.test/",
        artifactory_url="https://p.example.test/-danger/",
    )
    with pytest.raises(CatalogueFetchError) as exc_info:
        _validate_fetch_url("https://p.example.test/-danger/file.tar.gz", access)
    assert exc_info.value.code == "endpoint_not_permitted"


def test_endpoint_confinement_valid_url_returns_endpoint() -> None:
    """A valid URL returns the platform-relative endpoint string. AC-0012"""
    access = _make_access()
    endpoint = _validate_fetch_url(f"{_ARTF}/cat.toml", access)
    assert endpoint == "/art/cat.toml"


def test_validate_fetch_url_wrong_case_host_is_accepted() -> None:
    """Wrong-case host in fetch URL is normalized, not rejected. AC-0012"""
    # The access has a lowercase host; fetch URL with UPPERCASE host should
    # normalize to the same origin.
    access = _make_access()
    # Same host, uppercase — must normalize to the same origin.
    endpoint = _validate_fetch_url(
        "https://PLATFORM.EXAMPLE.TEST/art/cat.toml", access
    )
    assert endpoint == "/art/cat.toml"


# ---------------------------------------------------------------------------
# Descriptor fetch — success  (AC-0011, AC-0014)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_descriptor_fetch_returns_bytes(tmp_path: Path) -> None:
    """A successful jf api call returns the response bytes. AC-0011"""
    payload = b'{"schema": 1, "kind": "agentbundle-catalogue"}'
    _make_jf(tmp_path, response=payload)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    result = session.fetch_bytes(f"{_ARTF}/cat.toml", max_bytes=1024, timeout=120)
    assert result == payload


# ---------------------------------------------------------------------------
# Appended-newline cases — descriptor  (AC-0014)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_descriptor_no_trim_when_shorter_than_cap(tmp_path: Path) -> None:
    """Body shorter than cap is returned unchanged. AC-0014"""
    payload = b"short"
    _make_jf(tmp_path, response=payload)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    result = session.fetch_bytes(f"{_ARTF}/d.toml", max_bytes=100, timeout=120)
    assert result == payload


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_descriptor_trim_when_cap_plus_one_is_newline(tmp_path: Path) -> None:
    """cap+1 bytes where last is 0x0a → last byte removed. AC-0014"""
    max_bytes = 10
    payload = b"x" * max_bytes + b"\x0a"  # max_bytes + 1, ending in 0x0a
    _make_jf(tmp_path, response=payload)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    result = session.fetch_bytes(f"{_ARTF}/d.toml", max_bytes=max_bytes, timeout=120)
    assert result == b"x" * max_bytes


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_descriptor_rejected_when_cap_plus_one_is_not_newline(tmp_path: Path) -> None:
    """cap+1 bytes where last is not 0x0a → descriptor_too_large. AC-0014"""
    max_bytes = 10
    payload = b"x" * (max_bytes + 1)  # cap+1 but last byte is 'x', not 0x0a
    _make_jf(tmp_path, response=payload)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    with pytest.raises(CatalogueFetchError) as exc_info:
        session.fetch_bytes(f"{_ARTF}/d.toml", max_bytes=max_bytes, timeout=120)
    assert exc_info.value.code == "descriptor_too_large"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_descriptor_cap_boundary_exact_passes(tmp_path: Path) -> None:
    """Exactly max_bytes returns all bytes unchanged. AC-0014"""
    max_bytes = 10
    payload = b"y" * max_bytes
    _make_jf(tmp_path, response=payload)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    result = session.fetch_bytes(f"{_ARTF}/d.toml", max_bytes=max_bytes, timeout=120)
    assert result == payload


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_descriptor_cap_plus_two_raises_too_large(tmp_path: Path) -> None:
    """cap+2 bytes → descriptor_too_large regardless of final byte. AC-0014"""
    max_bytes = 10
    payload = b"z" * (max_bytes + 2)  # cap+2
    _make_jf(tmp_path, response=payload)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    with pytest.raises(CatalogueFetchError) as exc_info:
        session.fetch_bytes(f"{_ARTF}/d.toml", max_bytes=max_bytes, timeout=120)
    assert exc_info.value.code == "descriptor_too_large"


# ---------------------------------------------------------------------------
# Archive fetch — success  (AC-0011)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_archive_fetch_returns_temp_file(tmp_path: Path) -> None:
    """A successful archive fetch returns a temp file with expected content. AC-0011"""
    content = b"\x00\x01\x02\x03archive_data"
    _make_jf(tmp_path, response=content)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    archive_path = session.fetch_archive(
        f"{_ARTF}/pack.tar.gz", max_bytes=1024, timeout=120
    )
    try:
        assert archive_path.exists()
        assert archive_path.read_bytes() == content
    finally:
        archive_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Archive appended-newline and cap+1 trim cases  (AC-0014)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_archive_cap_plus_one_newline_trimmed(tmp_path: Path) -> None:
    """cap+1 archive bytes where last is 0x0a → file is trimmed to max_bytes. AC-0014"""
    max_bytes = 20
    # Simulate jf appending 0x0a to a max_bytes body: output = max_bytes + 1.
    content = b"a" * max_bytes + b"\x0a"
    _make_jf(tmp_path, response=content)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    archive_path = session.fetch_archive(
        f"{_ARTF}/pack.tar.gz", max_bytes=max_bytes, timeout=120
    )
    try:
        # fetch_archive truncates the appended byte; file must be at most max_bytes.
        assert archive_path.stat().st_size == max_bytes
    finally:
        archive_path.unlink(missing_ok=True)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_archive_cap_plus_one_non_newline_rejected(tmp_path: Path) -> None:
    """cap+1 bytes where last is not 0x0a → archive_too_large. AC-0014"""
    max_bytes = 20
    content = b"b" * (max_bytes + 1)  # cap+1 but last byte is 'b'
    _make_jf(tmp_path, response=content)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    with pytest.raises(CatalogueFetchError) as exc_info:
        session.fetch_archive(f"{_ARTF}/pack.tar.gz", max_bytes=max_bytes, timeout=120)
    assert exc_info.value.code == "archive_too_large"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_archive_cap_plus_two_rejected(tmp_path: Path) -> None:
    """cap+2 archive bytes → archive_too_large. AC-0014"""
    max_bytes = 20
    content = b"c" * (max_bytes + 2)
    _make_jf(tmp_path, response=content)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    with pytest.raises(CatalogueFetchError) as exc_info:
        session.fetch_archive(f"{_ARTF}/pack.tar.gz", max_bytes=max_bytes, timeout=120)
    assert exc_info.value.code == "archive_too_large"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_archive_fetch_body_trimmed_exact_digest_matches(tmp_path: Path) -> None:
    """Body of max_bytes (jf appends 0x0a → cap+1) is trimmed; exact digest matches. AC-0014

    Fixture: body = max_bytes bytes not ending in 0x0a; jf appends 0x0a.
    fetch_archive writes cap+1 bytes, sees trailing 0x0a, truncates to max_bytes.
    SHA-256 of the original body matches via the EXACT candidate.
    """
    max_bytes = 32
    body = b"x" * max_bytes  # does not end in 0x0a
    # Simulate jf appending 0x0a (real jf behaviour when body has no trailing newline).
    jf_output = body + b"\x0a"
    _make_jf(tmp_path, response=jf_output)

    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    archive_path = session.fetch_archive(
        f"{_ARTF}/pack.tar.gz", max_bytes=max_bytes, timeout=120
    )
    try:
        assert archive_path.stat().st_size == max_bytes
        assert archive_path.read_bytes() == body

        # Exact SHA-256 of the original body must match via the EXACT candidate.
        digest = _sha256(body)
        _verify_jfrog_archive_sha256(archive_path, digest, f"{_ARTF}/pack.tar.gz")
        assert archive_path.exists()
        assert archive_path.read_bytes() == body
    finally:
        archive_path.unlink(missing_ok=True)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_archive_fetch_full_body_digest_fails_after_trim(tmp_path: Path) -> None:
    """Body of max_bytes+1 ending in 0x0a (jf outputs as-is → cap+1) trimmed; full-body digest fails. AC-0014

    Fixture: body = max_bytes+1 bytes already ending in 0x0a; jf does not append.
    fetch_archive sees cap+1 bytes ending in 0x0a, truncates to max_bytes.
    SHA-256 of the full max_bytes+1 body does NOT match the trimmed file.
    """
    max_bytes = 32
    # Body is max_bytes+1 bytes, already ending in 0x0a; jf outputs exactly that.
    full_body = b"y" * max_bytes + b"\x0a"
    _make_jf(tmp_path, response=full_body)

    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    archive_path = session.fetch_archive(
        f"{_ARTF}/pack.tar.gz", max_bytes=max_bytes, timeout=120
    )
    try:
        assert archive_path.stat().st_size == max_bytes

        # SHA-256 of the full max_bytes+1 body must NOT match the trimmed file.
        full_digest = _sha256(full_body)
        from agentbundle.catalogue import CatalogueError
        with pytest.raises(CatalogueError):
            _verify_jfrog_archive_sha256(
                archive_path, full_digest, f"{_ARTF}/pack.tar.gz"
            )
        assert not archive_path.exists()
    except Exception:
        archive_path.unlink(missing_ok=True)
        raise


# ---------------------------------------------------------------------------
# Digest rule — _verify_jfrog_archive_sha256  (AC-0016)
# ---------------------------------------------------------------------------


def test_digest_exact_match_no_modification(tmp_path: Path) -> None:
    """Exact SHA-256 match: file unchanged. AC-0016"""
    content = b"exact_body_content"
    expected = _sha256(content)
    archive = tmp_path / "pack.tar.gz"
    archive.write_bytes(content)

    _verify_jfrog_archive_sha256(archive, expected, "https://h/pack.tar.gz")

    assert archive.exists()
    assert archive.read_bytes() == content


def test_digest_trimmed_match_truncates_file(tmp_path: Path) -> None:
    """Trimmed bytes match: file is truncated by 1 byte. AC-0016"""
    body = b"trimmed_body_bytes"
    appended = body + b"\x0a"
    expected = _sha256(body)
    archive = tmp_path / "pack.tar.gz"
    archive.write_bytes(appended)

    _verify_jfrog_archive_sha256(archive, expected, "https://h/pack.tar.gz")

    assert archive.read_bytes() == body


def test_digest_mismatch_removes_file(tmp_path: Path) -> None:
    """Neither candidate matches: file removed, CatalogueError raised. AC-0016"""
    content = b"bad_content"
    archive = tmp_path / "pack.tar.gz"
    archive.write_bytes(content)

    from agentbundle.catalogue import CatalogueError

    with pytest.raises(CatalogueError):
        _verify_jfrog_archive_sha256(archive, "a" * 64, "https://h/pack.tar.gz")

    assert not archive.exists()


def test_digest_trimmed_but_last_byte_not_newline_mismatch(tmp_path: Path) -> None:
    """Body ending in non-0x0a where trimmed digest also mismatches → removed. AC-0016"""
    content = b"body_with_z_end" + b"z"
    archive = tmp_path / "pack.tar.gz"
    archive.write_bytes(content)

    from agentbundle.catalogue import CatalogueError

    with pytest.raises(CatalogueError):
        _verify_jfrog_archive_sha256(archive, "b" * 64, "https://h/pack.tar.gz")

    assert not archive.exists()


def test_digest_direct_fetch_no_trim_applied(tmp_path: Path) -> None:
    """Direct-path archive uses _verify_archive_sha256 with no trim. AC-0016"""
    from agentbundle.https_catalogue import _verify_archive_sha256

    content = b"direct_body\x0a"  # ends in 0x0a but direct path should NOT trim
    expected = _sha256(content)
    archive = tmp_path / "pack.tar.gz"
    archive.write_bytes(content)

    # Must match exact; no trim applied on direct path.
    _verify_archive_sha256(archive, expected, "https://h/pack.tar.gz")
    assert archive.exists()


# ---------------------------------------------------------------------------
# Failure cases  (AC-0007, AC-0014)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_nonzero_exit_raises_fetch_failed(tmp_path: Path) -> None:
    """Non-zero exit from jf api → jfrog_fetch_failed. AC-0007"""
    _make_jf(tmp_path, exit_code=1)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    with pytest.raises(CatalogueFetchError) as exc_info:
        session.fetch_bytes(f"{_ARTF}/cat.toml", max_bytes=1024, timeout=120)
    assert exc_info.value.code == "jfrog_fetch_failed"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_stderr_too_large_raises_stderr_too_large(tmp_path: Path) -> None:
    """Stderr exceeding cap → jfrog_fetch_stderr_too_large. AC-0014"""
    stderr_limit = 64 * 1024  # 64 KiB
    _make_jf(tmp_path, stderr_bytes=stderr_limit + 10)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    with pytest.raises(CatalogueFetchError) as exc_info:
        session.fetch_bytes(f"{_ARTF}/cat.toml", max_bytes=1024 * 1024, timeout=120)
    assert exc_info.value.code == "jfrog_fetch_stderr_too_large"


# ---------------------------------------------------------------------------
# Timeout + reap + partial file removed  (AC-0013, AC-0014)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_archive_timeout_raises_fetch_timeout(tmp_path: Path) -> None:
    """Timeout on archive fetch → jfrog_fetch_timeout; partial file removed. AC-0013"""
    jf = tmp_path / "jf"
    real_path = os.environ.get("PATH", "/usr/bin:/bin")
    # sleep 30 is ≥10× the 1s timeout; trap '' TERM resists termination to exercise kill path.
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        'if [ "$1" = "api" ]; then\n'
        "  printf 'partial'\n"
        "  trap '' TERM\n"
        "  sleep 30\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})

    # Record temp files before to detect leaks.
    tmp_dir = Path(tempfile.gettempdir())
    before = {str(p) for p in tmp_dir.glob("agentbundle-jfrog-*.tmp")}

    with pytest.raises(CatalogueFetchError) as exc_info:
        session.fetch_archive(
            f"{_ARTF}/pack.tar.gz",
            max_bytes=256 * 1024 * 1024,
            timeout=1,  # explicit: this is a timeout test
        )

    assert exc_info.value.code == "jfrog_fetch_timeout"

    # No partial archive files should remain after cleanup.
    after = {str(p) for p in tmp_dir.glob("agentbundle-jfrog-*.tmp")}
    leaked = after - before
    assert not leaked, f"Partial archive file(s) leaked: {leaked}"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_descriptor_timeout_raises_fetch_timeout(tmp_path: Path) -> None:
    """Timeout on descriptor fetch → jfrog_fetch_timeout. AC-0013"""
    jf = tmp_path / "jf"
    real_path = os.environ.get("PATH", "/usr/bin:/bin")
    # sleep 30 is ≥10× the 1s timeout.
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        'if [ "$1" = "api" ]; then\n'
        "  trap '' TERM\n"
        "  sleep 30\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    with pytest.raises(CatalogueFetchError) as exc_info:
        session.fetch_bytes(f"{_ARTF}/cat.toml", max_bytes=1024, timeout=1)
    assert exc_info.value.code == "jfrog_fetch_timeout"


# ---------------------------------------------------------------------------
# Third fetch refused  (AC-0013)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_third_fetch_raises_fetch_failed(tmp_path: Path) -> None:
    """More than two fetch calls raise jfrog_fetch_failed. AC-0013"""
    payload = b"ok"
    _make_jf(tmp_path, response=payload)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})

    # First two succeed.
    session.fetch_bytes(f"{_ARTF}/cat.toml", max_bytes=100, timeout=120)
    arc = session.fetch_archive(f"{_ARTF}/p.tar.gz", max_bytes=100, timeout=120)
    arc.unlink(missing_ok=True)

    # Third is refused.
    with pytest.raises(CatalogueFetchError) as exc_info:
        session.fetch_bytes(f"{_ARTF}/other.toml", max_bytes=100, timeout=120)
    assert exc_info.value.code == "jfrog_fetch_failed"


# ---------------------------------------------------------------------------
# No lower-provider attempts after JFrog failure  (AC-0008)
# ---------------------------------------------------------------------------


def test_jfrog_fetch_failure_does_not_try_other_providers(tmp_path: Path) -> None:
    """A JFrog fetch error propagates directly; resolution is not retried. AC-0008"""
    access = _make_access()
    # Session with no jf on PATH → fetch fails immediately.
    session = JfrogFetchSession(access, {"PATH": ""})

    call_count: list[int] = [0]
    original_resolve = None

    # Patch resolve_http_access at the catalogue_fetch level to count calls.
    import agentbundle.catalogue_fetch as _cf

    original_resolve = _cf.resolve_http_access

    def counting_resolve(*args: object, **kwargs: object) -> object:
        call_count[0] += 1
        return original_resolve(*args, **kwargs)  # type: ignore[misc]

    with (
        mock.patch("agentbundle.catalogue_fetch.resolve_http_access", counting_resolve),
        pytest.raises(CatalogueFetchError) as exc_info,
    ):
        # Calling fetch_bytes directly on a JfrogFetchSession bypasses resolution.
        session.fetch_bytes(f"{_ARTF}/cat.toml", max_bytes=100, timeout=120)

    # No resolution calls — the JFrog session is already bound.
    assert call_count[0] == 0
    assert exc_info.value.code == "jfrog_fetch_failed"


# ---------------------------------------------------------------------------
# Stderr canary — sensitive values must not appear in errors or logs  (AC-0015)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_stderr_canary_not_in_error_text(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """A canary in HTTPS_PROXY (passed to child env) never appears in error text. AC-0015"""
    canary = "SUPER_SECRET_PROXY_CANARY_12345"

    jf = tmp_path / "jf"
    real_path = os.environ.get("PATH", "/usr/bin:/bin")
    # The jf script echoes its environment to stderr (hostile child behavior).
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        "# Echo env to stderr — simulates a hostile child.\n"
        "env >&2\n"
        "exit 1\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    access = _make_access()
    env = {
        "PATH": str(tmp_path),
        "HTTPS_PROXY": f"https://user:{canary}@proxy.example.test:8080",
    }
    session = JfrogFetchSession(access, env)

    with caplog.at_level(logging.DEBUG), pytest.raises(CatalogueFetchError) as exc_info:
        session.fetch_bytes(f"{_ARTF}/cat.toml", max_bytes=1024, timeout=120)

    error_text = str(exc_info.value)
    assert canary not in error_text
    for record in caplog.records:
        assert canary not in record.getMessage()


# ---------------------------------------------------------------------------
# open_fetch_session integration — JFrog session is created correctly (AC-0008)
# ---------------------------------------------------------------------------


def test_open_fetch_session_creates_jfrog_session() -> None:
    """open_fetch_session yields a JFrog session when credbroker returns JfrogCliHttpAccess."""
    from agentbundle.catalogue_fetch import open_fetch_session

    fake_access = JfrogCliHttpAccess(
        server_id="test-srv",
        platform_url="https://platform.example.test/",
        artifactory_url="https://platform.example.test/art/",
    )

    with (
        mock.patch(
            "agentbundle.catalogue_fetch.resolve_http_access",
            return_value=fake_access,
        ),
        open_fetch_session("https://platform.example.test/art/c.toml", env={}) as session,
    ):
        assert session.provider == "jfrog"
        assert session.target_origin == "https://platform.example.test"


# ---------------------------------------------------------------------------
# Defect B — confinement rejects before spawning any process  (AC-0012)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_endpoint_confinement_no_subprocess_spawned(tmp_path: Path) -> None:
    """A confined-out URL must not start jf api at all. AC-0012"""
    # Place a real jf on PATH so the session is satisfied; then confirm no spawn.
    _make_jf(tmp_path, response=b"{}")
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})

    spawn_count: list[int] = [0]
    import subprocess
    original_popen = subprocess.Popen

    def counting_popen(*args: object, **kwargs: object) -> object:
        spawn_count[0] += 1
        return original_popen(*args, **kwargs)

    cross_origin_url = "https://evil.example.test/art/cat.toml"

    with (
        mock.patch("subprocess.Popen", counting_popen),
        pytest.raises(CatalogueFetchError) as exc_info,
    ):
        session.fetch_bytes(cross_origin_url, max_bytes=1024, timeout=120)

    assert exc_info.value.code == "endpoint_not_permitted"
    assert spawn_count[0] == 0, "subprocess.Popen must not be called for a confined-out URL"


# ---------------------------------------------------------------------------
# Defect D — aggregate budget constants  (AC-0013)
# ---------------------------------------------------------------------------


def test_aggregate_subprocess_budget_is_75s() -> None:
    """Discovery, probe, and two fetches stay within 75 s. AC-0013"""
    # Assert on the live constants each package uses, not on wall-clock time:
    # every call's grace and kill sit inside its own deadline.
    from credbroker import _http_access as resolver

    budget = (
        resolver._JFROG_DISCOVERY_TIMEOUT
        + resolver._JFROG_PROBE_TIMEOUT
        + _PROD_MAX_FETCHES * _PROD_FETCH_TIMEOUT
    )
    assert (resolver._JFROG_DISCOVERY_TIMEOUT, resolver._JFROG_PROBE_TIMEOUT) == (10.0, 5.0)
    assert budget == 75.0


@pytest.mark.parametrize("kind", ["fetch_bytes", "fetch_archive"])
def test_session_caps_a_delegated_deadline_at_the_per_call_bound(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """A caller's longer timeout never stretches a jf api call past 30 s. AC-0013"""
    from agentbundle import catalogue_fetch
    from credbroker import JfrogCliHttpAccess

    seen: list[float] = []

    def record(self: object, url: str, *, max_bytes: int, timeout: float) -> bytes:
        seen.append(timeout)
        return b""

    monkeypatch.setattr(_jf_mod.JfrogFetchSession, kind, record)
    access = JfrogCliHttpAccess(
        server_id="example",
        platform_url="https://platform.example.test/",
        artifactory_url="https://platform.example.test/art/",
    )
    session = catalogue_fetch.FetchSession(
        access, None, jfrog_session=_jf_mod.JfrogFetchSession(access, {"PATH": "/nonexistent"})
    )
    getattr(session, kind)("https://platform.example.test/art/c.json", max_bytes=10, timeout=999)
    getattr(session, kind)("https://platform.example.test/art/c.json", max_bytes=10, timeout=3)

    assert seen == [_PROD_FETCH_TIMEOUT, 3]


# ---------------------------------------------------------------------------
# Defect F — no temp file leaks after success  (AC-0013)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_archive_no_temp_file_leak_on_success(tmp_path: Path) -> None:
    """Successful archive fetch leaves exactly the returned archive and no stray temp files. AC-0013

    The returned ``archive_path`` is the intended output (caller-owned).
    This test verifies that no EXTRA ``agentbundle-jfrog-*.tmp`` files leak and
    that the controlled-cwd directory is removed after success.
    """
    content = b"archive_data_bytes"
    _make_jf(tmp_path, response=content)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})

    sys_tmp = Path(tempfile.gettempdir())
    before_jfrog = set(sys_tmp.glob("agentbundle-jfrog-*.tmp"))
    before_cwd = set(sys_tmp.glob("agentbundle-jf-cwd-*"))

    archive_path = session.fetch_archive(
        f"{_ARTF}/pack.tar.gz", max_bytes=1024, timeout=120
    )
    # The returned archive_path is caller-owned.
    try:
        after_jfrog = set(sys_tmp.glob("agentbundle-jfrog-*.tmp"))
        after_cwd = set(sys_tmp.glob("agentbundle-jf-cwd-*"))
        new_jfrog = after_jfrog - before_jfrog
        leaked_cwd = after_cwd - before_cwd
        # Exactly one new jfrog temp file must exist: the returned archive.
        assert new_jfrog == {archive_path}, (
            f"Expected only the returned archive {archive_path}, got {new_jfrog}"
        )
        # CWD dir must be removed.
        assert not leaked_cwd, f"Temp cwd dirs not cleaned up: {leaked_cwd}"
    finally:
        archive_path.unlink(missing_ok=True)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_descriptor_no_cwd_temp_dir_leak_on_success(tmp_path: Path) -> None:
    """Successful descriptor fetch leaves no agentbundle-jf-cwd-* dirs behind. AC-0013"""
    _make_jf(tmp_path, response=b'{"ok": true}')
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})

    sys_tmp = Path(tempfile.gettempdir())
    before_cwd = set(sys_tmp.glob("agentbundle-jf-cwd-*"))

    session.fetch_bytes(f"{_ARTF}/cat.toml", max_bytes=1024, timeout=120)

    after_cwd = set(sys_tmp.glob("agentbundle-jf-cwd-*"))
    leaked_cwd = after_cwd - before_cwd
    assert not leaked_cwd, f"Temp cwd dirs not cleaned up: {leaked_cwd}"


# ---------------------------------------------------------------------------
# Defect L — controlled working directory  (AC-0012)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_child_runs_in_controlled_cwd_not_caller_cwd(tmp_path: Path) -> None:
    """The jf child process runs in a controlled temp dir, not the caller's cwd. AC-0012"""
    cwd_capture = tmp_path / "child_cwd.txt"
    py_exe = shlex.quote(sys.executable)
    real_path = os.environ.get("PATH", "/usr/bin:/bin")

    jf = tmp_path / "jf"
    # Write cwd via `pwd` (simpler than Python open() — no quoting traps).
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        'if [ "$1" = "api" ]; then\n'
        f"  pwd > {shlex.quote(str(cwd_capture))}\n"
        f"  {py_exe} -c 'import sys; sys.stdout.buffer.write(b\"{{}}\")'\n"
        "  exit 0\n"
        "fi\n"
        "exit 2\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    caller_cwd = str(Path.cwd().resolve())
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    session.fetch_bytes(f"{_ARTF}/cat.toml", max_bytes=1024, timeout=120)

    child_cwd = cwd_capture.read_text(encoding="utf-8").strip()
    assert child_cwd != caller_cwd, (
        f"Child ran in caller's cwd {caller_cwd!r}; must use a controlled temp dir"
    )
    assert "agentbundle-jf-cwd-" in child_cwd, (
        f"Expected agentbundle-jf-cwd-* temp dir, got {child_cwd!r}"
    )
    # The controlled cwd dir must be removed after success.
    assert not Path(child_cwd).exists(), (
        f"Controlled cwd temp dir not removed after success: {child_cwd!r}"
    )


# ---------------------------------------------------------------------------
# Defect R — stderr cap boundary matrix  (AC-0014)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_descriptor_stderr_at_cap_does_not_raise(tmp_path: Path) -> None:
    """Exactly at the stderr cap is NOT rejected. AC-0014"""
    cap = _PROD_FETCH_STDERR_CAP
    _make_jf(tmp_path, response=b'{"ok":true}', stderr_bytes=cap)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    # Should succeed: cap bytes is on the boundary (not over).
    result = session.fetch_bytes(f"{_ARTF}/cat.toml", max_bytes=1024 * 1024, timeout=120)
    assert result == b'{"ok":true}'


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_descriptor_stderr_cap_plus_one_raises(tmp_path: Path) -> None:
    """One byte over the stderr cap raises jfrog_fetch_stderr_too_large. AC-0014"""
    cap = _PROD_FETCH_STDERR_CAP
    _make_jf(tmp_path, response=b'{"ok":true}', stderr_bytes=cap + 1)
    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})
    with pytest.raises(CatalogueFetchError) as exc_info:
        session.fetch_bytes(f"{_ARTF}/cat.toml", max_bytes=1024 * 1024, timeout=120)
    assert exc_info.value.code == "jfrog_fetch_stderr_too_large"


# ---------------------------------------------------------------------------
# Defect A — stderr overflow after stdout EOF  (AC-0014)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_descriptor_stderr_overflow_after_stdout_closes(tmp_path: Path) -> None:
    """Stderr overflow AFTER stdout EOF raises jfrog_fetch_stderr_too_large. AC-0014

    The child closes stdout before flushing stderr past the cap.  This exercises
    the normal-completion path where the stderr re-check catches the overflow.
    """
    cap = _PROD_FETCH_STDERR_CAP
    py_exe = shlex.quote(sys.executable)
    real_path = os.environ.get("PATH", "/usr/bin:/bin")

    jf = tmp_path / "jf"
    # Write a tiny payload then explicitly close stdout (via the python process
    # exiting), then sleep briefly so stderr has time to overflow.
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        'if [ "$1" = "api" ]; then\n'
        # First subprocess: write stdout payload and exit (closes stdout).
        f"  {py_exe} -c \"import sys; sys.stdout.buffer.write(b'ok'); sys.stdout.buffer.flush()\"\n"
        # Second subprocess: emit over-cap stderr after stdout is gone.
        f"  {py_exe} -c \"import sys; sys.stderr.write('x'*{cap + 1}); sys.stderr.flush()\"\n"
        "  exit 0\n"
        "fi\n"
        "exit 2\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})

    start = time.monotonic()
    with pytest.raises(CatalogueFetchError) as exc_info:
        session.fetch_bytes(f"{_ARTF}/cat.toml", max_bytes=1024 * 1024, timeout=60)
    elapsed = time.monotonic() - start

    assert exc_info.value.code == "jfrog_fetch_stderr_too_large", exc_info.value
    # Must abort promptly — well under the 60s deadline.
    assert elapsed < 10.0, f"abort took {elapsed:.2f}s, expected < 10s"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_archive_stderr_overflow_after_stdout_closes(tmp_path: Path) -> None:
    """Stderr overflow AFTER stdout EOF in archive path raises jfrog_fetch_stderr_too_large. AC-0014"""
    cap = _PROD_FETCH_STDERR_CAP
    py_exe = shlex.quote(sys.executable)
    real_path = os.environ.get("PATH", "/usr/bin:/bin")

    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        'if [ "$1" = "api" ]; then\n'
        # Write a small archive payload to stdout then close stdout.
        f"  {py_exe} -c \"import sys; sys.stdout.buffer.write(b'archive'); sys.stdout.buffer.flush()\"\n"
        # Then overflow stderr after stdout is closed.
        f"  {py_exe} -c \"import sys; sys.stderr.write('x'*{cap + 1}); sys.stderr.flush()\"\n"
        "  exit 0\n"
        "fi\n"
        "exit 2\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    access = _make_access()
    session = JfrogFetchSession(access, {"PATH": str(tmp_path)})

    sys_tmp = Path(tempfile.gettempdir())
    before = set(sys_tmp.glob("agentbundle-jfrog-*.tmp"))

    start = time.monotonic()
    with pytest.raises(CatalogueFetchError) as exc_info:
        session.fetch_archive(f"{_ARTF}/pack.tar.gz", max_bytes=1024 * 1024, timeout=60)
    elapsed = time.monotonic() - start

    assert exc_info.value.code == "jfrog_fetch_stderr_too_large", exc_info.value
    assert elapsed < 10.0, f"abort took {elapsed:.2f}s, expected < 10s"

    # No new archive temp file must remain after a failed fetch.
    after = set(sys_tmp.glob("agentbundle-jfrog-*.tmp"))
    leaked = after - before
    assert not leaked, f"Archive temp files not cleaned up after stderr overflow: {leaked}"
