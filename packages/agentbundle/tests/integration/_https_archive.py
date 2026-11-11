"""A local HTTPS server for release-archive fixtures.

A throwaway certificate authority signs the server's certificate. Tests hand
the authority's certificate to the CLI through ``AGENTBUNDLE_CA_BUNDLE``, which
the archive fetch honours, so no product code is patched. A missing ``openssl``
fails the test on Linux and macOS instead of skipping it.
"""

from __future__ import annotations

import contextlib
import hashlib
import http.server
import shutil
import ssl
import subprocess
import sys
import threading
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ServedArchive:
    """An archive being served and the ``archive+https`` source that names it."""

    source: str
    sha256: str
    ca_bundle: Path
    requests: list[str]


def _openssl(*args: str, cwd: Path) -> None:
    exe = shutil.which("openssl")
    if exe is None:
        if sys.platform in ("linux", "darwin"):
            raise AssertionError("openssl is required on Linux and macOS")
        raise RuntimeError("openssl not available")
    subprocess.run([exe, *args], cwd=cwd, check=True, capture_output=True)  # noqa: S603


def make_certificates(directory: Path) -> tuple[Path, Path, Path]:
    """Return ``(ca_cert, server_cert, server_key)`` for ``127.0.0.1``."""
    directory.mkdir(parents=True, exist_ok=True)
    _openssl(
        "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "2",
        "-keyout", "ca.key", "-out", "ca.pem", "-subj", "/CN=Test Root CA",
        "-addext", "basicConstraints=critical,CA:TRUE",
        "-addext", "keyUsage=critical,keyCertSign,cRLSign",
        cwd=directory,
    )
    _openssl(
        "req", "-newkey", "rsa:2048", "-nodes", "-keyout", "server.key",
        "-out", "server.csr", "-subj", "/CN=127.0.0.1", cwd=directory,
    )
    (directory / "san.cnf").write_text(
        "subjectAltName=IP:127.0.0.1,DNS:localhost\n"
        "basicConstraints=CA:FALSE\n"
        "keyUsage=digitalSignature,keyEncipherment\n"
        "extendedKeyUsage=serverAuth\n",
        encoding="utf-8",
    )
    _openssl(
        "x509", "-req", "-in", "server.csr", "-CA", "ca.pem", "-CAkey", "ca.key",
        "-CAcreateserial", "-out", "server.pem", "-days", "2",
        "-extfile", "san.cnf", cwd=directory,
    )
    return directory / "ca.pem", directory / "server.pem", directory / "server.key"


@contextlib.contextmanager
def serve_archive(archive: Path, workdir: Path) -> Generator[ServedArchive, None, None]:
    """Serve *archive* over HTTPS on a free local port until the block exits."""
    ca, cert, key = make_certificates(workdir / "certs")
    body = archive.read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    requests: list[str] = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib hook name
            requests.append(self.path)
            if self.path.split("?", 1)[0] != "/catalogue.tar.gz":
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/gzip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args: object) -> None:
            return

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(str(cert), str(key))
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        yield ServedArchive(
            source=f"archive+https://127.0.0.1:{port}/catalogue.tar.gz#sha256={digest}",
            sha256=digest,
            ca_bundle=ca,
            requests=requests,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
