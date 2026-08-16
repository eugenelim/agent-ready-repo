#!/usr/bin/env python3
"""Diagnose a TLS trust failure in ``agentbundle install``.

    python3 tools/diagnose-tls-trust.py [archive-url]

For an adopter whose install fails with::

    [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
    unable to get local issuer certificate

Read-only: makes one HTTPS request and changes nothing. Reports which
interpreter is running, which certificate store that interpreter reads, whether
the connection is being TLS-intercepted, and — on macOS — whether the
administrator keychain would repair it.

Background worth knowing before reading the output: macOS is the only platform
where Python ignores the operating system's trust store, which is how a
corporate authority can be trusted by every other tool on the machine and still
be invisible here. Windows reads its own certificate store directly; Linux reads
``/etc/ssl/certs``. A WSL distribution does *not* inherit the Windows store.

Creating a virtualenv changes none of this — a virtualenv inherits its base
interpreter's certificate store unchanged. Run this under each ``python3`` on
your PATH instead; that difference is usually the answer.

PRIVACY: the output names your organisation's certificate authority, and may
name proxy hosts and your username. Send it to your maintainer directly. Do not
paste it into a public issue, pull request, or commit.
"""

from __future__ import annotations

import os
import pathlib
import re
import shutil
import socket
import ssl
import subprocess  # nosec B404  # list argv, no shell, read-only diagnostics
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit

DEFAULT_URL = (
    "https://github.com/eugenelim/agent-ready-repo/archive/refs/heads/main.tar.gz"
)
SYSTEM_KEYCHAIN = "/Library/Keychains/System.keychain"

TRUST_VARS = (
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "REQUESTS_CA_BUNDLE",
    "CURL_CA_BUNDLE",
    "NODE_EXTRA_CA_CERTS",
    "AGENTBUNDLE_CA_BUNDLE",
    "AGENTBUNDLE_NO_SYSTEM_TRUST",
    "HTTPS_PROXY",
    "https_proxy",
    "NO_PROXY",
    "no_proxy",
)


def _looks_like_wsl() -> bool:
    """True when running inside a WSL distribution.

    Worth distinguishing: WSL reports `linux` but does not inherit the Windows
    certificate store, so an authority pushed to Windows is invisible here.
    """
    proc_version = pathlib.Path("/proc/version")
    if not proc_version.exists():
        return False
    try:
        text = proc_version.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return "microsoft" in text.lower()


def heading(text: str) -> None:
    print(f"\n{text}\n{'-' * len(text)}")


def fetch(url: str, context: ssl.SSLContext | None = None) -> tuple[bool, str]:
    """Return ``(ok, detail)`` for a one-byte GET of *url*."""
    try:
        with urllib.request.urlopen(url, timeout=30, context=context) as resp:  # nosec B310
            resp.read(1)
            return True, f"HTTP {resp.status}"
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        return False, f"{type(reason).__name__}: {reason}"
    except Exception as exc:  # noqa: BLE001 - diagnostics: report anything
        return False, f"{type(exc).__name__}: {exc}"


def run(argv: list[str], timeout: int = 60) -> str:
    """Run *argv*, returning stdout, or "" if it fails."""
    try:
        # argv[0] comes from shutil.which at both call sites, not a literal;
        # the remaining args are constants and there is no shell.
        proc = subprocess.run(  # nosec B603  # list argv, no shell
            argv, capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return ""
    return proc.stdout if proc.returncode == 0 else ""


def report_interpreter() -> None:
    heading("1. interpreter")
    in_venv = sys.prefix != sys.base_prefix
    print(f"sys.executable : {sys.executable}")
    print(f"version        : {sys.version.split()[0]}")
    print(f"platform       : {sys.platform}")
    print(f"inside venv    : {in_venv}")
    if in_venv:
        print(f"venv base      : {sys.base_prefix}")
        print("note           : a venv inherits its base interpreter's trust store")


def report_agentbundle() -> None:
    heading("2. agentbundle on PATH")
    path = shutil.which("agentbundle")
    print(f"path    : {path or 'NOT FOUND'}")
    if not path:
        return
    out = run([path, "--version"], timeout=30)
    print(f"version : {out.strip() or '(could not run)'}")
    try:
        with pathlib.Path(path).open(encoding="utf-8", errors="replace") as handle:
            print(f"shebang : {handle.readline().strip()}")
    except OSError:
        print("shebang : (binary or unreadable)")


def report_trust_store() -> None:
    heading("3. this interpreter's trust store")
    paths = ssl.get_default_verify_paths()
    print(f"OpenSSL    : {ssl.OPENSSL_VERSION}")
    print(f"cafile     : {paths.cafile}")
    print(f"  exists   : {bool(paths.cafile) and pathlib.Path(paths.cafile).exists()}")
    print(f"capath     : {paths.capath}")
    print(f"  exists   : {bool(paths.capath) and pathlib.Path(paths.capath).is_dir()}")
    try:
        count = len(ssl.create_default_context().get_ca_certs())
    except Exception as exc:  # noqa: BLE001
        print(f"CAs loaded : ERROR {exc}")
        return
    print(f"CAs loaded : {count}")
    if count == 0:
        print(
            "\n>> THIS IS ALMOST CERTAINLY YOUR PROBLEM. This interpreter trusts\n"
            ">> ZERO certificate authorities, so every HTTPS request from it fails —\n"
            ">> not just ones crossing an inspecting proxy. A python.org macOS build\n"
            ">> needs its certificate step run once:\n"
            '>>   open "/Applications/Python 3.x/Install Certificates.command"\n'
            ">> Or point it at the system bundle:\n"
            ">>   export SSL_CERT_FILE=/etc/ssl/cert.pem\n"
            ">> Read section 5 before assuming interception: a public issuer there\n"
            ">> with 'Verify return code: 0' means nothing is intercepting you."
        )
    if sys.platform == "win32":
        print("note       : Windows also loads the OS certificate store directly")
    elif sys.platform == "darwin":
        print("note       : macOS does NOT consult the keychain — only the file above")


def report_environment() -> None:
    heading("4. relevant environment")
    for name in TRUST_VARS:
        value = os.environ.get(name)
        if value is None:
            print(f"  {name:<28} unset")
            continue
        suffix = ""
        if "PROXY" not in name.upper():
            suffix = f"  (exists: {pathlib.Path(value).exists()})"
        print(f"  {name:<28} {value}{suffix}")
    print(f"urllib sees proxies: {urllib.request.getproxies()}")


_PRINTABLE = re.compile(rb"[ -~]{4,64}")
_PUBLIC_HINTS = (
    "DigiCert", "Sectigo", "USERTrust", "ISRG", "Let's Encrypt", "Baltimore",
    "GlobalSign", "Amazon", "Google Trust", "Entrust", "GoDaddy", "Comodo",
    "VeriSign", "Certum", "QuoVadis", "Actalis", "Buypass", "SSL.com",
)


def _readable_names(der: bytes) -> list[str]:
    """Pull human-readable strings out of a certificate.

    Crude on purpose: parsing X.509 properly needs a dependency this repository
    refuses, and a person reading this output only needs to recognise whether the
    issuer is a public authority or their own organisation.
    """
    out = []
    for match in _PRINTABLE.findall(der):
        text = match.decode("ascii", "replace").strip()
        if len(text) >= 4 and not text.startswith(("http", "//")) and " " in text or (
            len(text) >= 8 and text.isprintable()
        ):
            out.append(text)
    return out


def report_chain(url: str) -> None:
    heading("5. certificate chain the server presents")
    host = urlsplit(url).hostname or ""

    # Pure Python first: `openssl` is usually absent on Windows, and this check
    # is the one that distinguishes an inspected network from a broken store.
    chain: list[bytes] = []
    try:
        probe = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        # A bare SSLContext permits TLS 1.0/1.1. This probe only reads the
        # certificate the server presents, but there is no reason to offer
        # obsolete versions while doing it.
        probe.minimum_version = ssl.TLSVersion.TLSv1_2
        probe.check_hostname = False
        probe.verify_mode = ssl.CERT_NONE  # inspection only; nothing is trusted
        with (
            socket.create_connection((host, 443), timeout=30) as sock,
            probe.wrap_socket(sock, server_hostname=host) as tls,
        ):
            getter = getattr(tls, "get_unverified_chain", None)
            if getter is not None:
                chain = list(getter() or [])
            elif tls.getpeercert(binary_form=True):
                chain = [tls.getpeercert(binary_form=True)]
    except OSError as exc:
        print(f"could not connect to inspect the chain: {exc}")
        return

    if not chain:
        print("connected, but this Python cannot expose the chain "
              "(needs 3.13+ for get_unverified_chain)")
        return

    top = _readable_names(chain[-1])
    print(f"chain length: {len(chain)}")
    print("issuer-most certificate mentions:")
    for name in top[:8]:
        print(f"    {name}")

    joined = " ".join(top)
    if any(hint.lower() in joined.lower() for hint in _PUBLIC_HINTS):
        print(
            "\n>> That is a PUBLIC certificate authority, so your network is NOT\n"
            ">> intercepting this connection. If the fetch still fails, the problem\n"
            ">> is this interpreter's trust store — see section 3."
        )
    else:
        print(
            "\n>> No well-known public authority appears above. If you recognise a\n"
            ">> security vendor or your own organisation, TLS is being intercepted\n"
            ">> on this network — expected in many companies, and the case the\n"
            ">> corporate CA bundle exists for."
        )


def report_fetch(url: str) -> bool:
    heading("6. the fetch agentbundle performs")
    print(f"URL: {url}")
    ok, detail = fetch(url)
    print(f"default trust store -> {'OK' if ok else 'FAIL'}  ({detail})")
    return ok


def report_keychain_retry(url: str) -> None:
    heading("7. retry using the macOS administrator keychain")
    security = shutil.which("security") or "/usr/bin/security"
    if not pathlib.Path(security).exists():
        print("`security` not found — skipping")
        return
    admin = run([security, "find-certificate", "-a", "-p", SYSTEM_KEYCHAIN])
    print(f"administrator keychain: {admin.count('BEGIN CERTIFICATE')} certificates")
    if not admin:
        print(
            "\n>> The administrator keychain holds nothing to retry with, so your\n"
            ">> organisation's authority is installed somewhere else — a login\n"
            ">> keychain, or an application's own store. agentbundle reads only the\n"
            ">> administrator keychain, because it is the one store that requires\n"
            ">> administrator rights to write."
        )
        return

    ctx = ssl.create_default_context()
    loaded = 0
    for chunk in admin.split("-----END CERTIFICATE-----"):
        if "BEGIN CERTIFICATE" not in chunk:
            continue
        block = chunk[chunk.index("-----BEGIN") :] + "-----END CERTIFICATE-----\n"
        try:
            ctx.load_verify_locations(cadata=block)
            loaded += 1
        except (ssl.SSLError, ValueError, TypeError):
            continue
    print(f"anchors added to the default store: {loaded}")

    ok, detail = fetch(url, context=ctx)
    print(f"default store + admin keychain -> {'OK' if ok else 'FAIL'}  ({detail})")
    if ok:
        print(
            "\n>> DIAGNOSIS: your organisation's authority is trusted by macOS but is\n"
            ">> absent from the certificate file this Python reads. agentbundle 0.35.0\n"
            ">> and later repair this automatically — upgrade, and the install will\n"
            ">> retry against these anchors and report that it did so."
        )
    else:
        print(
            "\n>> The administrator keychain did not complete the chain either. Ask\n"
            ">> your IT team for the corporate CA bundle and set\n"
            ">> AGENTBUNDLE_CA_BUNDLE to it, or install from a local clone.\n"
            ">> Also confirm the proxy allows every host in the redirect chain — a\n"
            ">> GitHub archive fetch redirects github.com to codeload.github.com."
        )


def report_windows_stores() -> None:
    """Windows keeps its own certificate store, and Python reads it directly.

    So a Windows failure is *not* the macOS story: the corporate root is usually
    already trusted. This section exists to show whether it actually is, because
    the earlier assumption that Windows needs nothing turned out to be worth
    verifying rather than asserting.
    """
    heading("7. Windows certificate stores")
    enum = getattr(ssl, "enum_certificates", None)
    if enum is None:
        print("ssl.enum_certificates unavailable — not a Windows interpreter")
        return
    server_auth = "1.3.6.1.5.5.7.3.1"
    for store in ("ROOT", "CA"):
        try:
            entries = enum(store)
        except (OSError, PermissionError) as exc:
            print(f"  {store:<5} could not be read: {exc}")
            continue
        total = len(entries)
        usable = sum(
            1
            for _cert, encoding, trust in entries
            if encoding == "x509_asn" and (trust is True or server_auth in (trust or ()))
        )
        print(f"  {store:<5} {total:>4} certificates, {usable:>4} usable for server auth")
    print(
        "\n>> Python loads these stores automatically, so a root your IT team\n"
        ">> pushed by Group Policy or Intune should already be trusted. If the\n"
        ">> fetch still fails, check in this order:\n"
        ">>   1. Section 5 — is the chain actually being intercepted?\n"
        ">>   2. Is the interception root in CurrentUser rather than LocalMachine,\n"
        ">>      or restricted by trust settings so it is not usable for server\n"
        ">>      auth (compare the two counts above)?\n"
        ">>   3. Does the proxy require NTLM or Kerberos authentication? Python's\n"
        ">>      urllib cannot satisfy either, and no certificate fixes it.\n"
        ">>   4. Is codeload.github.com allowed as well as github.com? An archive\n"
        ">>      fetch redirects across both.\n"
        ">> If none of those explain it, send this whole output — the assumption\n"
        ">> that Windows needs no help is exactly what needs testing here."
    )


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    report_interpreter()
    report_agentbundle()
    report_trust_store()
    report_environment()
    report_chain(url)
    ok = report_fetch(url)
    if not ok and sys.platform == "win32":
        report_windows_stores()
    elif not ok and sys.platform == "darwin":
        report_keychain_retry(url)
    elif not ok and sys.platform == "linux":
        heading("7. Linux and WSL")
        wsl = _looks_like_wsl()
        if wsl:
            print(
                ">> This looks like WSL. A WSL distribution does NOT inherit the\n"
                ">> Windows certificate store, so an authority your IT team pushed to\n"
                ">> Windows is invisible here. Export it from Windows and install it\n"
                ">> into the distribution:\n"
                ">>   sudo cp corporate-ca.crt /usr/local/share/ca-certificates/\n"
                ">>   sudo update-ca-certificates"
            )
        else:
            print(
                ">> On Linux, OpenSSL reads /etc/ssl/certs. Install your\n"
                ">> organisation's authority there (update-ca-certificates), or set\n"
                ">> AGENTBUNDLE_CA_BUNDLE to a PEM bundle containing it."
            )

    heading("done")
    print(
        "Compare sections 1 and 3 across every python3 on your PATH — interpreters\n"
        "do not share a certificate store, and that difference is usually the\n"
        "answer. A virtualenv is not a variable here: it inherits its base\n"
        "interpreter's store unchanged."
    )
    try:
        host = urlsplit(url).hostname or ""
        print(f"{host} resolves to {socket.gethostbyname(host)}")
    except OSError as exc:
        print(f"name resolution failed: {exc}")


if __name__ == "__main__":
    main()
