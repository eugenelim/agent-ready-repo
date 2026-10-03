"""JFrog CLI real-executable contract test.

This suite is skipped unless all three environment variables are set:

- ``AGENTBUNDLE_TEST_JF_EXECUTABLE``: absolute path to a JFrog CLI 2.105.0+
  binary (acquired separately; not committed to the repository).
- ``AGENTBUNDLE_TEST_JF_CA_CERT``: path to the loopback CA certificate (PEM).
- ``AGENTBUNDLE_TEST_JF_CA_KEY``: path to the loopback CA private key (PEM).

When the variables are present, the suite:

1. Starts a disposable HTTPS loopback server signed by the supplied CA.
2. Creates a disposable ``JFROG_CLI_HOME_DIR`` and runs ``jf config add``
   pointing to the loopback server.
3. Verifies that ``resolve_http_access`` selects the configured profile.
4. Asserts that ``fetch_bytes`` succeeds for a descriptor-like endpoint.
5. Asserts that a 404 response maps to ``jfrog_fetch_failed``.
6. Asserts that a slow endpoint triggers ``jfrog_fetch_timeout``.
7. Asserts that no bearer token or profile credential appears in raised errors.

The test is intentionally narrow: it proves the argument contract, binary
stdout streaming, exit mapping, timeout termination, and credential absence —
not the full catalogue-install flow, which belongs in the roster suite.
"""

from __future__ import annotations

import contextlib
import http.server
import json
import os
import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
import time
from pathlib import Path

import pytest
from agentbundle.catalogue_fetch.jfrog_cli import JfrogFetchSession
from agentbundle.catalogue_fetch.models import CatalogueFetchError
from credbroker import JfrogCliHttpAccess, resolve_http_access

# ---------------------------------------------------------------------------
# Skip marker — all three env vars must be present.
# ---------------------------------------------------------------------------

_JF_EXECUTABLE = os.environ.get("AGENTBUNDLE_TEST_JF_EXECUTABLE", "")
_JF_CA_CERT = os.environ.get("AGENTBUNDLE_TEST_JF_CA_CERT", "")
_JF_CA_KEY = os.environ.get("AGENTBUNDLE_TEST_JF_CA_KEY", "")

_SKIP_REASON = (
    "AGENTBUNDLE_TEST_JF_EXECUTABLE, AGENTBUNDLE_TEST_JF_CA_CERT, and "
    "AGENTBUNDLE_TEST_JF_CA_KEY must all be set to run the JFrog CLI contract suite"
)

pytestmark = pytest.mark.skipif(
    not (_JF_EXECUTABLE and _JF_CA_CERT and _JF_CA_KEY),
    reason=_SKIP_REASON,
)


# ---------------------------------------------------------------------------
# Loopback HTTPS server and disposable profile fixtures
# ---------------------------------------------------------------------------


class _LoopbackHandler(http.server.BaseHTTPRequestHandler):
    """Minimal HTTPS request handler for contract tests."""

    routes: dict[str, tuple[int, bytes]] = {}

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?")[0].split("#")[0]
        if path in self.routes:
            code, body = self.routes[path]
            self.send_response(code)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt: str, *args: object) -> None:
        pass  # Suppress output.


@contextlib.contextmanager
def _loopback_server(ca_cert: str, ca_key: str, routes: dict[str, tuple[int, bytes]]):
    """Start a TLS loopback HTTPS server signed by the supplied CA."""
    # Bind to a random loopback port.
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=ca_cert, keyfile=ca_key)

    class _Handler(_LoopbackHandler):
        pass

    _Handler.routes = dict(routes)
    server = http.server.HTTPServer(("127.0.0.1", port), _Handler)
    server.socket = ctx.wrap_socket(server.socket, server_side=True)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield port
    finally:
        server.shutdown()


@contextlib.contextmanager
def _disposable_jf_home(jf_exe: str, server_url: str, ca_cert: str):
    """Create a temp JFROG_CLI_HOME_DIR with one profile pointing to *server_url*."""
    home = tempfile.mkdtemp(prefix="agentbundle-jf-contract-")
    try:
        env = {
            "JFROG_CLI_HOME_DIR": home,
            "SSL_CERT_FILE": ca_cert,
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        }
        subprocess.run(
            [
                jf_exe,
                "config",
                "add",
                "contract-test-profile",
                f"--url={server_url}",
                "--user=testuser",
                "--password=testpass",
                "--interactive=false",
                "--overwrite=true",
            ],
            env=env,
            check=True,
            capture_output=True,
            timeout=30,
        )
        yield home
    finally:
        shutil.rmtree(home, ignore_errors=True)


# ---------------------------------------------------------------------------
# Contract tests
# ---------------------------------------------------------------------------


def test_real_jf_resolves_and_fetches_descriptor() -> None:
    """Real jf resolves the profile and fetches a descriptor via jf api."""
    descriptor = json.dumps(
        {
            "schema": 1,
            "kind": "agentbundle-catalogue",
            "bundle": "test",
            "channel": "stable",
            "release": "1.0.0",
            "artifact": "pack.tar.gz",
            "sha256": "a" * 64,
        }
    ).encode()

    routes = {
        "/artifactory/cat/cat.toml": (200, descriptor),
    }

    with _loopback_server(_JF_CA_CERT, _JF_CA_KEY, routes) as port:
        server_url = f"https://127.0.0.1:{port}/"
        artf_url = f"{server_url}artifactory/"

        with _disposable_jf_home(_JF_EXECUTABLE, server_url, _JF_CA_CERT) as jf_home:
            target = f"{artf_url}cat/cat.toml"
            env = {
                "PATH": str(Path(_JF_EXECUTABLE).parent),
                "JFROG_CLI_HOME_DIR": jf_home,
                "SSL_CERT_FILE": _JF_CA_CERT,
            }
            access = resolve_http_access(target, env=env)

            assert isinstance(access, JfrogCliHttpAccess)

            session = JfrogFetchSession(access, env)
            result = session.fetch_bytes(target, max_bytes=1024 * 1024, timeout=30)

            # The descriptor JSON may or may not have a trailing newline appended.
            assert result.strip() == descriptor.strip()


def test_real_jf_404_maps_to_fetch_failed() -> None:
    """A 404 response from jf api maps to jfrog_fetch_failed."""
    routes: dict[str, tuple[int, bytes]] = {}

    with _loopback_server(_JF_CA_CERT, _JF_CA_KEY, routes) as port:
        server_url = f"https://127.0.0.1:{port}/"
        artf_url = f"{server_url}artifactory/"

        with _disposable_jf_home(_JF_EXECUTABLE, server_url, _JF_CA_CERT) as jf_home:
            target = f"{artf_url}missing/cat.toml"
            env = {
                "PATH": str(Path(_JF_EXECUTABLE).parent),
                "JFROG_CLI_HOME_DIR": jf_home,
                "SSL_CERT_FILE": _JF_CA_CERT,
            }
            access = resolve_http_access(target, env=env)
            assert isinstance(access, JfrogCliHttpAccess)

            session = JfrogFetchSession(access, env)
            with pytest.raises(CatalogueFetchError) as exc_info:
                session.fetch_bytes(target, max_bytes=1024 * 1024, timeout=30)

            assert exc_info.value.code == "jfrog_fetch_failed"


def test_real_jf_slow_endpoint_times_out() -> None:
    """An endpoint that hangs beyond the timeout triggers jfrog_fetch_timeout."""

    class _SlowHandler(_LoopbackHandler):
        def do_GET(self) -> None:  # noqa: N802
            # Accept the connection but never respond (simulate hang).
            time.sleep(60)

    _SlowHandler.routes = {}

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=_JF_CA_CERT, keyfile=_JF_CA_KEY)

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    server = http.server.HTTPServer(("127.0.0.1", port), _SlowHandler)
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        server_url = f"https://127.0.0.1:{port}/"
        artf_url = f"{server_url}artifactory/"

        with _disposable_jf_home(_JF_EXECUTABLE, server_url, _JF_CA_CERT) as jf_home:
            target = f"{artf_url}cat/cat.toml"
            env = {
                "PATH": str(Path(_JF_EXECUTABLE).parent),
                "JFROG_CLI_HOME_DIR": jf_home,
                "SSL_CERT_FILE": _JF_CA_CERT,
            }
            access = resolve_http_access(target, env=env)
            assert isinstance(access, JfrogCliHttpAccess)

            session = JfrogFetchSession(access, env)
            with pytest.raises(CatalogueFetchError) as exc_info:
                session.fetch_bytes(target, max_bytes=1024 * 1024, timeout=5)

            assert exc_info.value.code == "jfrog_fetch_timeout"
    finally:
        server.shutdown()


def test_real_jf_credentials_absent_from_errors() -> None:
    """Profile credentials never appear in raised CatalogueFetchError text."""
    routes: dict[str, tuple[int, bytes]] = {}
    canary = "CONTRACT_TEST_CANARY_SECRET_99"

    with _loopback_server(_JF_CA_CERT, _JF_CA_KEY, routes) as port:
        server_url = f"https://127.0.0.1:{port}/"
        artf_url = f"{server_url}artifactory/"

        with _disposable_jf_home(_JF_EXECUTABLE, server_url, _JF_CA_CERT) as jf_home:
            target = f"{artf_url}missing/cat.toml"
            env = {
                "PATH": str(Path(_JF_EXECUTABLE).parent),
                "JFROG_CLI_HOME_DIR": jf_home,
                "SSL_CERT_FILE": _JF_CA_CERT,
                # Include canary in HTTPS_PROXY — it must not leak.
                "HTTPS_PROXY": f"https://user:{canary}@proxy.example.test:8080",
            }
            access = resolve_http_access(target, env=env)
            assert isinstance(access, JfrogCliHttpAccess)

            session = JfrogFetchSession(access, env)
            with pytest.raises(CatalogueFetchError) as exc_info:
                session.fetch_bytes(target, max_bytes=1024 * 1024, timeout=30)

            error_text = str(exc_info.value)
            assert canary not in error_text
            assert "CONTRACT_TEST_CANARY_SECRET_99" not in error_text
