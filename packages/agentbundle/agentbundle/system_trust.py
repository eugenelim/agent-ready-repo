"""Corporate trust-store resolution for catalogue fetches.

Two jobs, both about one failure: an adopter on a TLS-inspecting corporate
network cannot verify ``github.com``, because the root CA their IT department
installed lives in the operating system's trust store and not in the PEM file
Python's OpenSSL reads.

  1. ``resolve_trust_paths`` / ``build_context`` — honour the trust-store
     environment variables ``CONVENTIONS.md`` § Corporate-network requirements
     mandates, for an adopter or IT department that already holds a bundle.
  2. ``system_anchor_pem`` — on macOS, export the *administrator* keychains so
     the fetch can recover without the adopter knowing what a PEM file is.

Three properties hold throughout, and the tests assert each one directly:

* **Strict, always.** Every context starts from ``ssl.create_default_context()``
  and keeps ``check_hostname`` on with ``CERT_REQUIRED``. Nothing here disables
  verification, and no ``--insecure``-style switch exists to ask it to.
* **Augment, never replace.** Anchors are added to the default store. A bundle
  holding only a private CA must not un-trust the public roots — a GitHub
  archive fetch redirects ``github.com`` → ``codeload.github.com``, and both
  hops have to verify.
* **Administrator material only.** The login keychain is writable without
  administrator rights, so a root landing there is not an IT trust decision.
  It is never read.

This module owns the one ``subprocess`` call the fetch path needs, so
``catalogue.py`` can keep making none of its own; it imports this module lazily
and delegates.

The fallback is macOS-only by necessity, not by scoping choice: macOS is the one
platform where Python ignores the operating system's trust store.
``ssl.SSLContext.load_default_certs`` carries a ``win32`` branch that loads the
Windows ``CA`` and ``ROOT`` stores via ``enum_certificates`` — filtering on each
certificate's trust settings, which is stricter than what this module can do on
macOS — and no ``darwin`` branch at all. Linux resolves through OpenSSL's default
paths. So Windows needs no fallback, and Linux needs none once the authority is
installed in ``/etc/ssl/certs``.

The exception worth knowing: a WSL distribution reports ``linux`` and does not
inherit the Windows certificate store, so an authority pushed to Windows is
invisible inside WSL until installed into the distribution. That is a
documentation matter — nothing here can reach across that boundary.

On any platform without administrator trust material, ``system_anchor_pem``
returns ``None`` and the caller reports that rather than retrying against an
identical trust store.
"""

from __future__ import annotations

import contextlib
import os
import ssl
import subprocess  # nosec B404 - fixed argv to /usr/bin/security, no shell
import sys
from pathlib import Path

from agentbundle.catalogue import CatalogueError

# One keychain, deliberately. ``System.keychain`` needs administrator or MDM
# rights to write, and it is where a corporate proxy root actually lands — so it
# is the only store that holds the material this feature exists to find.
#
# Apple's ``SystemRootCertificates.keychain`` is *not* read. The retry context
# already starts from ``create_default_context()``, so the public roots are
# present; adding Apple's root program on top would widen trust to a second,
# independently curated set for no gain. Measured on a corporate host: reading
# System.keychain alone produced exactly the same anchor count as reading both,
# i.e. Apple's keychain contributed nothing while enlarging the trust surface on
# the one fetch path with no post-transport integrity check.
#
# The user's ``login.keychain-db`` is absent and must stay absent: it is writable
# without administrator rights, so a root landing there is not an IT decision.
_ADMIN_KEYCHAINS = ("/Library/Keychains/System.keychain",)

_SECURITY_BIN = "/usr/bin/security"

_PEM_MARKER = "BEGIN CERTIFICATE"

# Opt-out for an adopter who wants the failure rather than the recovery.
NO_SYSTEM_TRUST_ENV = "AGENTBUNDLE_NO_SYSTEM_TRUST"

# Our own CA-bundle variable. https_catalogue.py reads the same name but
# spells it inline, and deliberately gives it replace-the-store semantics
# rather than the additive semantics used here.
CA_BUNDLE_ENV = "AGENTBUNDLE_CA_BUNDLE"


def _default_runner(argv: list[str]) -> str:
    """Run *argv* and return stdout, or "" when it fails.

    Seam: tests replace ``_RUNNER`` so no assertion depends on the developer's
    own keychain contents.
    """
    proc = subprocess.run(  # nosec B603 - fixed binary, no shell, argv is constant
        argv,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else ""


_RUNNER = _default_runner


def system_trust_disabled(env: dict | None = None) -> bool:
    """True when the adopter has opted out of the system-trust fallback."""
    source = os.environ if env is None else env
    return bool(source.get(NO_SYSTEM_TRUST_ENV))


def resolve_trust_paths(env: dict | None = None) -> tuple[str | None, str | None]:
    """Resolve ``(cafile, capath)`` from the trust-store environment variables.

    The precedence order is the one stated in the spec's acceptance criteria;
    this function implements it rather than restating it.

    ``AGENTBUNDLE_CA_BUNDLE`` is ours and is set by hand for this feature, so a
    path that does not exist raises rather than being absorbed — a typo there is
    worth reporting, and ``https_catalogue.py`` already raises on the same
    variable. The other two are frequently set fleet-wide by IT, where a stale
    value must not harden into an install failure, so the caller's ``suppress``
    validates them instead.
    """
    source = os.environ if env is None else env

    ours = source.get(CA_BUNDLE_ENV)
    if ours and not Path(ours).exists():
        raise CatalogueError(f"{CA_BUNDLE_ENV} path does not exist: {ours!r}")

    cafile = ours or source.get("SSL_CERT_FILE") or source.get("REQUESTS_CA_BUNDLE")
    capath = source.get("SSL_CERT_DIR")
    return (cafile or None, capath or None)


def system_anchor_pem() -> str | None:
    """Return administrator-keychain certificates as PEM text, or ``None``.

    macOS only, because it is the only platform where Python does not already
    consult the operating system's trust store — see the module docstring. Every
    other platform returns ``None`` without invoking the runner.

    Known limitation, deferred as ``catalogue-trust-store-trust-settings``:
    ``find-certificate`` dumps every certificate in the keychain and does not
    consult per-certificate trust settings, so a certificate an administrator
    explicitly marked "Never Trust" is still returned here — and a *Never Trust*
    marking is a revocation, which makes ignoring it subtractive of a control
    rather than purely additive. Bounded by reading the administrator keychain
    only and by augmenting rather than replacing the default store, so the
    fallback can only widen trust to material an administrator installed.
    Python's own Windows path does honour trust settings, which is the shape to
    match when this is closed.
    """
    if sys.platform != "darwin":
        return None

    chunks: list[str] = []
    for keychain in _ADMIN_KEYCHAINS:
        argv = [_SECURITY_BIN, "find-certificate", "-a", "-p", keychain]
        try:
            out = _RUNNER(argv)
        except (OSError, subprocess.SubprocessError, ValueError):
            # ValueError covers UnicodeDecodeError: the runner decodes strictly,
            # so one non-UTF-8 byte in the dump would otherwise escape from
            # inside the caller's own `except` block and crash the install.
            continue
        if out and _PEM_MARKER in out:
            chunks.append(out)

    if not chunks:
        return None
    return "".join(chunks)


def build_context(
    env: dict | None = None,
    *,
    system_anchors: str | None = None,
) -> ssl.SSLContext:
    """Build a strict ``SSLContext``, widened by whatever trust material exists.

    With no relevant variable set and no *system_anchors*, this is
    ``ssl.create_default_context()`` — the context ``urlopen`` would have built
    on its own, so the no-configuration path keeps today's trust decisions.

    *system_anchors* is PEM text supplied by the caller rather than fetched
    here, so a caller can establish whether a fallback is possible at all
    before announcing one.

    On ``SSL_CERT_FILE`` specifically: ``create_default_context`` resolves
    OpenSSL's default paths, so a *stale* ``SSL_CERT_FILE`` yields an empty
    store rather than falling back to the public roots, and reloading the same
    bad path cannot undo that. Only ``REQUESTS_CA_BUNDLE``, which OpenSSL does
    not read, is fully recoverable when stale.
    """
    ctx = ssl.create_default_context()

    cafile, capath = resolve_trust_paths(env)
    if cafile or capath:
        # A stale inherited path must not abort the fetch. Mirrors
        # credbroker/_sso.py.
        with contextlib.suppress(OSError, ssl.SSLError):
            ctx.load_verify_locations(cafile=cafile, capath=capath)

    if system_anchors:
        _load_pem_text(ctx, system_anchors)

    # Belt: a future edit must not be able to weaken these silently.
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


_PEM_END = "-----END CERTIFICATE-----"


def _pem_blocks(pem: str) -> list[str]:
    """Split PEM *text* into one string per certificate block."""
    blocks = []
    for chunk in pem.split(_PEM_END):
        if _PEM_MARKER in chunk:
            blocks.append(chunk[chunk.index("-----BEGIN") :] + _PEM_END + "\n")
    return blocks


def _load_pem_text(ctx: ssl.SSLContext, pem: str) -> None:
    """Load PEM *text* as anchors, one certificate at a time.

    Per-block loading is what makes the fallback dependable. OpenSSL stops at the
    first block it cannot parse, and a keychain dump legitimately contains
    material that is not a parseable certificate — so a single bad block early in
    the dump would otherwise discard every anchor after it, including the very
    corporate root this feature exists to find, while the caller has already
    announced a fallback on stderr. Measured: for one good certificate plus one
    malformed block, a combined load keeps 1 anchor when the good one comes
    first and **0** when it comes second. Loading block by block removes the
    ordering dependence entirely.

    ``cadata=`` is used rather than a temporary file so no employer-identifying
    certificate material rests on disk at any point, not even briefly.

    ``TypeError`` is suppressed alongside the rest because ``cadata`` rejects
    non-ASCII ``str`` with ``TypeError``, which is not a ``ValueError`` — an
    unlucky byte in a keychain dump must degrade this fallback, never crash the
    install.
    """
    for block in _pem_blocks(pem):
        with contextlib.suppress(OSError, ssl.SSLError, ValueError, TypeError):
            ctx.load_verify_locations(cadata=block)
