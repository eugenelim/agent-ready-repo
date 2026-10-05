"""JFrog CLI real-executable contract test.

Runs only when all three environment variables are set; otherwise every test
skips with that reason:

- ``AGENTBUNDLE_TEST_JF_EXECUTABLE``: absolute path to an official JFrog CLI
  2.105.0 or later, acquired outside the repository and never committed.
- ``AGENTBUNDLE_TEST_JF_CA_CERT`` and ``AGENTBUNDLE_TEST_JF_CA_KEY``: a
  disposable self-signed PEM certificate and key for ``127.0.0.1``.

``jf api`` trusts a private CA only through ``SSL_CERT_FILE`` on Linux, and only
through the system keychain on macOS, so this suite is meant to run in a
disposable Linux container. Each test serves fixtures from a loopback HTTPS
server, writes a disposable profile with a dummy token into a temporary
``JFROG_CLI_HOME_DIR``, and drives the real executable through credbroker
discovery and AgentBundle's bounded fetch session. AC-0011, AC-0013, AC-0014,
AC-0015, AC-0016, AC-0018.
"""

from __future__ import annotations

import contextlib
import hashlib
import http.server
import io
import json
import logging
import os
import shutil
import ssl
import subprocess
import tarfile
import threading
import time
from collections.abc import Generator
from pathlib import Path

import pytest
from agentbundle.catalogue_fetch import open_fetch_session
from agentbundle.catalogue_fetch.models import CatalogueFetchError
from agentbundle.https_catalogue import fetch_catalogue_archive_with_provenance
from credbroker import JfrogCliHttpAccess, resolve_http_access

_JF_EXECUTABLE = os.environ.get("AGENTBUNDLE_TEST_JF_EXECUTABLE", "")
_JF_CA_CERT = os.environ.get("AGENTBUNDLE_TEST_JF_CA_CERT", "")
_JF_CA_KEY = os.environ.get("AGENTBUNDLE_TEST_JF_CA_KEY", "")

pytestmark = pytest.mark.skipif(
    not (_JF_EXECUTABLE and _JF_CA_CERT and _JF_CA_KEY),
    reason=(
        "AGENTBUNDLE_TEST_JF_EXECUTABLE, AGENTBUNDLE_TEST_JF_CA_CERT, and "
        "AGENTBUNDLE_TEST_JF_CA_KEY must all be set to run the JFrog CLI contract suite"
    ),
)

_PROFILE = "pcat-profile-7f3a"
_TOKEN = "disposable-contract-token-0001"


class _Server(http.server.ThreadingHTTPServer):
    daemon_threads = True


class _Handler(http.server.BaseHTTPRequestHandler):
    """Serve fixed routes and record every request's path and Authorization."""

    routes: dict[str, bytes] = {}
    slow_paths: set[str] = set()
    seen: list[tuple[str, str | None]] = []

    def do_GET(self) -> None:  # noqa: N802
        self.seen.append((self.path, self.headers.get("Authorization")))
        if self.path in self.slow_paths:
            self.send_response(200)
            self.send_header("Content-Length", "10")
            self.end_headers()
            self.wfile.write(b"x")
            self.wfile.flush()
            time.sleep(60)
            return
        body = self.routes.get(self.path)
        if body is None:
            self.send_response(404)
            self.send_header("Content-Length", "9")
            self.end_headers()
            self.wfile.write(b"not found")
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        pass


@contextlib.contextmanager
def _catalogue_host(
    routes: dict[str, bytes], slow_paths: frozenset[str] = frozenset()
) -> Generator[tuple[str, type[_Handler]], None, None]:
    """Serve *routes* over loopback HTTPS; yield the base URL and handler class."""
    handler = type("_Bound", (_Handler,), {"routes": routes, "slow_paths": set(slow_paths), "seen": []})
    server = _Server(("127.0.0.1", 0), handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=_JF_CA_CERT, keyfile=_JF_CA_KEY)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"https://127.0.0.1:{server.server_address[1]}/", handler
    finally:
        server.shutdown()
        server.server_close()


def _profile_env(tmp_path: Path, base_url: str) -> dict[str, str]:
    """Write a disposable jf profile for *base_url* and return the resolver env."""
    jf_home = tmp_path / "jfrog-home"
    jf_home.mkdir()
    env = {
        "PATH": str(Path(_JF_EXECUTABLE).parent),
        "HOME": str(tmp_path),
        "JFROG_CLI_HOME_DIR": str(jf_home),
        "SSL_CERT_FILE": _JF_CA_CERT,
    }
    subprocess.run(
        [
            _JF_EXECUTABLE,
            "config",
            "add",
            _PROFILE,
            f"--url={base_url}",
            f"--artifactory-url={base_url}artifactory/",
            f"--access-token={_TOKEN}",
            "--interactive=false",
        ],
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
        timeout=60,
    )
    return env


def _tarball_not_ending_in_newline() -> bytes:
    """Return a gzip tarball whose final byte is not 0x0a."""
    for padding in range(64):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            content = b"contract" + b"!" * padding
            info = tarfile.TarInfo("pack/README.md")
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
        data = buffer.getvalue()
        if data[-1:] != b"\n":
            return data
    raise AssertionError("could not build a tarball without a trailing newline")


def _jf_api_processes() -> list[str]:
    """Return command lines of live ``jf api`` processes (Linux /proc only)."""
    proc = Path("/proc")
    if not proc.is_dir():
        return []
    found = []
    for entry in proc.iterdir():
        if entry.name.isdigit():
            with contextlib.suppress(OSError):
                cmdline = (entry / "cmdline").read_bytes().replace(b"\0", b" ")
                if b" api " in cmdline and _JF_EXECUTABLE.encode() in cmdline:
                    found.append(cmdline.decode(errors="replace"))
    return found


def test_real_jf_discovery_pins_the_profile(tmp_path: Path) -> None:
    """Discovery selects the disposable profile and passes the version floor."""
    with _catalogue_host({}) as (base, _handler):
        env = _profile_env(tmp_path, base)
        access = resolve_http_access(f"{base}artifactory/cat/channel.json", env=env)

    assert isinstance(access, JfrogCliHttpAccess)
    assert access.server_id == _PROFILE
    assert access.platform_url == base
    assert access.artifactory_url == f"{base}artifactory/"


def test_real_jf_descriptor_bytes_carry_only_the_appended_newline(tmp_path: Path) -> None:
    """``jf api`` returns the body plus the one newline it appends, and no more."""
    body = json.dumps({"schema": 1}).encode()
    with _catalogue_host({"/artifactory/cat/channel.json": body}) as (base, handler):
        env = _profile_env(tmp_path, base)
        url = f"{base}artifactory/cat/channel.json"
        with open_fetch_session(url, env=env) as session:
            assert session.provider == "jfrog"
            fetched = session.fetch_bytes(url, max_bytes=1024 * 1024, timeout=30)

    assert fetched == body + b"\n"
    assert ("/artifactory/cat/channel.json", f"Bearer {_TOKEN}") in handler.seen


def test_real_jf_installs_a_binary_archive_through_the_digest_rule(tmp_path: Path) -> None:
    """A real descriptor-and-archive acquisition verifies and extracts the archive."""
    archive = _tarball_not_ending_in_newline()
    digest = hashlib.sha256(archive).hexdigest()
    descriptor = json.dumps(
        {
            "schema": 1,
            "kind": "agentbundle-catalogue",
            "bundle": "contract",
            "channel": "stable",
            "release": "1.0.0",
            "artifact": "pack.tar.gz",
            "sha256": digest,
        }
    ).encode()
    routes = {
        "/artifactory/cat/channel.json": descriptor,
        "/artifactory/cat/pack.tar.gz": archive,
    }
    with _catalogue_host(routes) as (base, handler):
        env = _profile_env(tmp_path, base)
        result = fetch_catalogue_archive_with_provenance(
            f"catalogue+{base}artifactory/cat/channel.json", env=env
        )

    try:
        assert result.archive_sha256 == digest
        assert (result.path / "pack" / "README.md").read_bytes().startswith(b"contract")
        assert {path for path, _ in handler.seen} >= set(routes)
    finally:
        shutil.rmtree(result.path, ignore_errors=True)


def test_real_jf_404_maps_to_fetch_failed(tmp_path: Path) -> None:
    """A non-2xx response exits 1 and maps to ``jfrog_fetch_failed``."""
    with _catalogue_host({}) as (base, _handler):
        env = _profile_env(tmp_path, base)
        url = f"{base}artifactory/cat/missing.json"
        with open_fetch_session(url, env=env) as session, pytest.raises(CatalogueFetchError) as caught:
            session.fetch_bytes(url, max_bytes=1024 * 1024, timeout=30)

    assert caught.value.code == "jfrog_fetch_failed"


def test_real_jf_timeout_terminates_and_reaps_the_child(tmp_path: Path) -> None:
    """A stalled response ends within the deadline with the child reaped."""
    slow = "/artifactory/cat/slow.tar.gz"
    with _catalogue_host({}, frozenset({slow})) as (base, _handler):
        env = _profile_env(tmp_path, base)
        url = f"{base}artifactory{slow[len('/artifactory'):]}"
        with open_fetch_session(url, env=env) as session:
            started = time.monotonic()
            with pytest.raises(CatalogueFetchError) as caught:
                session.fetch_archive(url, max_bytes=1024 * 1024, timeout=4)
            elapsed = time.monotonic() - started

    assert caught.value.code == "jfrog_fetch_timeout"
    assert elapsed <= 4 + 1.0
    assert _jf_api_processes() == []


def test_real_jf_token_never_reaches_agentbundle_output(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The profile token and the jf stderr never surface in errors or logs."""
    caplog.set_level(logging.DEBUG)
    with _catalogue_host({}) as (base, _handler):
        env = _profile_env(tmp_path, base)
        url = f"{base}artifactory/cat/missing.json"
        with open_fetch_session(url, env=env) as session, pytest.raises(CatalogueFetchError) as caught:
            session.fetch_bytes(url, max_bytes=1024 * 1024, timeout=30)

    rendered = f"{caught.value!s} {caught.value!r} {caught.value.args!r} {caplog.text}"
    for secret in (_TOKEN, _PROFILE, "Http Status", url):
        assert secret not in rendered
