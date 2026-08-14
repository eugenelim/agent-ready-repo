"""Real-TLS proof of the two-attempt trust fallback — spec/catalogue-corporate-trust-store.

This is the only test that exercises an actual failing TLS handshake and its
recovery. Everything else stubs ``urlopen`` and therefore proves sequencing, not
verification.

Shape: a throwaway certificate authority signs a ``localhost`` server
certificate. The default trust store does not know that authority, so attempt
one fails exactly as an adopter behind a TLS-inspecting proxy fails. The
authority is then supplied through the same seam the macOS keychain uses, and the
retry must succeed.

No network access. Skipped when ``openssl`` is unavailable — generating an X.509
certificate needs a dependency this package refuses to add.
"""

from __future__ import annotations

import http.server
import io
import shutil
import ssl
import subprocess
import tarfile
import threading
from pathlib import Path

import pytest
from agentbundle import catalogue, system_trust
from agentbundle.catalogue import CatalogueError

pytestmark = pytest.mark.skipif(
    shutil.which("openssl") is None, reason="openssl CLI not available"
)

ARCHIVE_NAME = "repo-main.tar.gz"


def _openssl(*args: str) -> None:
    proc = subprocess.run(
        ["openssl", *args], capture_output=True, text=True, timeout=60, check=False
    )
    if proc.returncode != 0:
        pytest.skip(f"openssl could not generate fixtures: {proc.stderr[:200]}")


@pytest.fixture(scope="module")
def tls_fixtures(tmp_path_factory):
    """A throwaway CA plus a localhost server certificate signed by it."""
    d = tmp_path_factory.mktemp("tls")
    ca_key, ca_crt = d / "ca.key", d / "ca.crt"
    srv_key, srv_csr, srv_crt = d / "srv.key", d / "srv.csr", d / "srv.crt"

    # The CA needs a Subject Key Identifier of its own: under VERIFY_X509_STRICT
    # an anchor without one cannot be matched to the leaf's Authority Key
    # Identifier, and chain building fails with "unable to get local issuer
    # certificate" — which looks exactly like the bug under test and is not.
    _openssl("req", "-x509", "-newkey", "rsa:2048", "-nodes",
             "-keyout", str(ca_key), "-out", str(ca_crt), "-days", "1",
             "-subj", "/CN=Throwaway Test CA",
             "-addext", "subjectKeyIdentifier=hash",
             "-addext", "basicConstraints=critical,CA:TRUE",
             "-addext", "keyUsage=critical,keyCertSign,cRLSign")
    _openssl("req", "-newkey", "rsa:2048", "-nodes",
             "-keyout", str(srv_key), "-out", str(srv_csr),
             "-subj", "/CN=localhost")
    # Python 3.13's create_default_context() enables VERIFY_X509_STRICT, which
    # rejects a leaf with no Authority Key Identifier. Real certificates — a
    # corporate proxy's included — carry one; a hand-rolled fixture has to ask
    # for it explicitly, or this test fails on the fixture rather than on the
    # behaviour under test. Keeping strict verification on is the point.
    ext = d / "ext.cnf"
    ext.write_text(
        "subjectAltName=DNS:localhost,IP:127.0.0.1\n"
        "authorityKeyIdentifier=keyid,issuer\n"
        "subjectKeyIdentifier=hash\n"
        "basicConstraints=CA:FALSE\n"
    )
    _openssl("x509", "-req", "-in", str(srv_csr), "-CA", str(ca_crt),
             "-CAkey", str(ca_key), "-CAcreateserial", "-out", str(srv_crt),
             "-days", "1", "-extfile", str(ext))

    payload = b"catalogue\n"
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        info = tarfile.TarInfo("repo-main/pack.toml")
        info.size = len(payload)
        tf.addfile(info, io.BytesIO(payload))
    (d / ARCHIVE_NAME).write_bytes(buf.getvalue())

    return {"dir": d, "ca_pem": ca_crt.read_text(),
            "srv_crt": srv_crt, "srv_key": srv_key}


@pytest.fixture(scope="module")
def tls_server(tls_fixtures):
    """Serve the archive over TLS signed by the throwaway CA."""
    root = tls_fixtures["dir"]

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(root), **kw)

        def log_message(self, *a):  # keep test output clean
            pass

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=tls_fixtures["srv_crt"],
                        keyfile=tls_fixtures["srv_key"])
    httpd = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"https://localhost:{httpd.server_address[1]}/{ARCHIVE_NAME}"
    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=5)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in ("AGENTBUNDLE_CA_BUNDLE", "AGENTBUNDLE_NO_SYSTEM_TRUST",
                "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE"):
        monkeypatch.delenv(var, raising=False)


def test_attempt_one_genuinely_fails_against_an_unknown_authority(
    tls_server, tmp_path, monkeypatch
):
    """The premise: without the authority, real TLS verification fails."""
    monkeypatch.setattr(system_trust, "system_anchor_pem", lambda **k: None)
    with pytest.raises(CatalogueError) as exc:
        catalogue._fetch_and_extract(tls_server, tmp_path)
    assert "could not be verified" in str(exc.value)


def test_the_fallback_recovers_a_real_failing_handshake(
    tls_server, tls_fixtures, tmp_path, capsys
):
    """The whole feature, end to end, over a real TLS connection.

    Attempt one fails verification; the authority arrives through the same seam
    the macOS keychain populates; the retry completes and the archive extracts.
    """
    import agentbundle.system_trust as st

    original = st.system_anchor_pem
    st.system_anchor_pem = lambda **k: tls_fixtures["ca_pem"]
    try:
        catalogue._fetch_and_extract(tls_server, tmp_path)
    finally:
        st.system_anchor_pem = original

    assert (tmp_path / "repo-main" / "pack.toml").read_text() == "catalogue\n"
    err = capsys.readouterr().err
    assert "retrying with operating-system trust anchors" in err


def test_a_dirty_dump_still_recovers(tls_server, tls_fixtures, tmp_path):
    """The authority survives unparseable neighbours, in either position.

    This is the regression guard for per-block anchor loading: a combined load
    keeps nothing when the malformed block comes first.
    """
    import agentbundle.system_trust as st

    garbage = "-----BEGIN CERTIFICATE-----\nnot base64\n-----END CERTIFICATE-----\n"
    original = st.system_anchor_pem
    st.system_anchor_pem = lambda **k: garbage + tls_fixtures["ca_pem"] + garbage
    try:
        catalogue._fetch_and_extract(tls_server, tmp_path)
    finally:
        st.system_anchor_pem = original

    assert (tmp_path / "repo-main" / "pack.toml").exists()


def test_opt_out_refuses_to_recover(tls_server, tls_fixtures, tmp_path, monkeypatch):
    """With the fallback disabled, a recoverable failure stays a failure."""
    monkeypatch.setenv("AGENTBUNDLE_NO_SYSTEM_TRUST", "1")
    import agentbundle.system_trust as st

    original = st.system_anchor_pem
    st.system_anchor_pem = lambda **k: tls_fixtures["ca_pem"]
    try:
        with pytest.raises(CatalogueError) as exc:
            catalogue._fetch_and_extract(tls_server, tmp_path)
    finally:
        st.system_anchor_pem = original
    assert "was not attempted" in str(exc.value)
    assert not (tmp_path / "repo-main").exists()


def test_an_explicit_ca_bundle_also_recovers(tls_server, tls_fixtures, tmp_path,
                                             monkeypatch):
    """The env-var half of the feature, over the same real handshake."""
    bundle = Path(tls_fixtures["dir"]) / "bundle.pem"
    bundle.write_text(tls_fixtures["ca_pem"])
    monkeypatch.setenv("AGENTBUNDLE_CA_BUNDLE", str(bundle))
    catalogue._fetch_and_extract(tls_server, tmp_path)
    assert (tmp_path / "repo-main" / "pack.toml").exists()
