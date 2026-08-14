"""Catalogue URI resolver — T5 deliverable, reused by T6/T8/T11/T12.

Accepts:
  - Local relative or absolute paths.
  - ``git+https://github.com/<owner>/<repo>[@<ref>]``

For ``git+https://`` URIs the resolver:
  1. Parses owner, repo, and optional ref.
  2. Constructs a GitHub archive URL (tag, branch, or SHA — tried in
     that order by a light heuristic: tags contain only ``v`` + semver
     chars or no slash; SHAs are exactly 40 hex chars; everything else
     is a branch).
  3. Fetches with ``urllib.request.urlopen`` — no subprocess, no git.
  4. Extracts with ``tarfile`` into a per-call tempdir and returns the
     inner ``<repo>-<ref>/`` directory.

``git+ssh://`` URIs raise ``CatalogueError`` immediately — SSH is
deferred to v1.1.

Unreachable URLs raise ``CatalogueError`` with the tarball URL in the
message so the caller can report exactly what was attempted.

TLS trust is delegated to ``system_trust.py``: the fetch honours the
corporate CA-bundle environment variables, and a certificate-verification
failure is retried exactly once against operating-system trust anchors,
announced on stderr. Verification is never weakened on any path.

No subprocess calls in this module. The macOS keychain export that the
trust fallback needs lives in ``system_trust.py``, which this module
imports lazily and delegates to.
"""

from __future__ import annotations

import atexit
import re
import shutil
import ssl
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path

# A black-holing corporate proxy accepts the connection and never answers, so an
# unbounded fetch hangs forever rather than failing. The value matches
# https_catalogue._HTTP_TIMEOUT deliberately: both fetch archives over the same
# networks, and one number is easier to reason about than two. urllib applies it
# per socket operation, not to the whole transfer, so a large archive on a slow
# link is unaffected — only 30s of silence trips it.
_FETCH_TIMEOUT_S = 30

_SSH_PREFIX = "git+ssh://"
_HTTPS_PREFIX = "git+https://"

# Match git+https://github.com/<owner>/<repo>[@<ref>]
# Group 1: owner, Group 2: repo (no .git suffix), Group 3: ref (optional)
_HTTPS_RE = re.compile(
    r"^git\+https://github\.com/([^/]+)/([^/@]+?)(?:\.git)?(?:@([^@]+))?$"
)

# A SHA is exactly 40 lowercase hex digits (or 7–40 for abbreviated SHAs;
# we accept the full pattern only to keep the heuristic simple).
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


class CatalogueError(ValueError):
    """Raised when a catalogue URI cannot be resolved."""


def resolve_catalogue(uri: str) -> Path:
    """Resolve *uri* to a local directory rooted at the catalogue.

    Returns a ``Path`` to the local directory. For ``git+https://`` URIs
    the path lives inside a per-call tempdir registered with ``atexit``
    so it's removed at process exit — see ``_resolve_https``. Callers
    must not assume the directory survives past process termination.
    """
    if uri.startswith(_SSH_PREFIX):
        raise CatalogueError(
            "SSH git URLs deferred to v1.1; use https or local path."
        )

    # Explicit reject for http:// variants — layer-1 explicit arg bypasses
    # _is_valid_source, so we must guard here to avoid silent local-path fallback.
    if uri.startswith(("catalogue+http://", "archive+http://")):
        raise CatalogueError(
            "HTTPS-only: catalogue+http:// and archive+http:// are not supported; "
            "use catalogue+https:// or archive+https://"
        )

    # Dispatch new HTTPS catalogue schemes
    if uri.startswith(("catalogue+https://", "archive+https://")):
        from agentbundle.https_catalogue import fetch_catalogue_archive
        return fetch_catalogue_archive(uri)

    if uri.startswith(_HTTPS_PREFIX):
        return _resolve_https(uri)

    # Local path — relative or absolute.
    return Path(uri)


def _resolve_https(uri: str) -> Path:
    m = _HTTPS_RE.match(uri)
    if not m:
        raise CatalogueError(
            f"Cannot parse git+https URI: {uri!r}. "
            "Expected format: git+https://github.com/<owner>/<repo>[@<ref>]"
        )
    owner, repo, ref = m.group(1), m.group(2), m.group(3)
    if not ref:
        ref = "main"

    tarball_url = _github_archive_url(owner, repo, ref)
    tmpdir = Path(tempfile.mkdtemp(prefix="agentbundle-catalogue-"))
    # Best-effort cleanup at process exit — atexit handlers run on normal
    # interpreter shutdown; for crash paths the OS reaps /tmp eventually.
    atexit.register(shutil.rmtree, str(tmpdir), True)
    _fetch_and_extract(tarball_url, tmpdir)
    # The GitHub archive extracts to <repo>-<ref>/ (with '/' → '-' in SHAs).
    return _find_inner_dir(tmpdir)


def _ref_type(ref: str) -> str:
    """Heuristically classify a ref as 'tag', 'sha', or 'branch'.

    The plan specifies: try tag, then branch, then SHA order — but we
    need to pick exactly one URL at construction time because the caller
    doesn't retry across URL forms (the tarball fetch either succeeds or
    raises ``CatalogueError``).

    Heuristic:
      - Exactly 40 lowercase hex chars → SHA.
      - Looks like a version tag (optional 'v' + digits/dots, e.g. v1.0
        or 1.0.0) → tag.
      - Anything else → branch.

    This matches the plan's examples: ``v1.0`` → tag, ``main`` → branch,
    ``deadbeef`` (7 chars) or a full 40-char SHA → sha.

    Abbreviated SHAs (7–39 chars, all hex) are treated as SHA because
    that's the most likely intent and ``archive/<sha>`` accepts prefixes.
    """
    if _SHA_RE.match(ref):
        return "sha"
    # Version tag pattern: optional 'v', one or more numeric segments
    if re.match(r"^v?\d+(\.\d+)*$", ref):
        return "tag"
    return "branch"


def _github_archive_url(owner: str, repo: str, ref: str) -> str:
    rtype = _ref_type(ref)
    if rtype == "tag":
        return f"https://github.com/{owner}/{repo}/archive/refs/tags/{ref}.tar.gz"
    if rtype == "branch":
        return f"https://github.com/{owner}/{repo}/archive/refs/heads/{ref}.tar.gz"
    # SHA
    return f"https://github.com/{owner}/{repo}/archive/{ref}.tar.gz"


def _is_cert_verification_failure(exc: BaseException) -> bool:
    """True when *exc* is a certificate-verification failure.

    ``urlopen`` never lets ``ssl.SSLCertVerificationError`` escape directly — it
    wraps it in ``URLError.reason`` — so matching the bare exception type would
    silently never fire the fallback. Both shapes are accepted.
    """
    if isinstance(exc, ssl.SSLCertVerificationError):
        return True
    reason = getattr(exc, "reason", None)
    return isinstance(reason, ssl.SSLCertVerificationError)


def _verification_failure_message(
    url: str,
    detail: object,
    *,
    fallback_note: str,
    offer_opt_out: bool = True,
    empty_store: bool = False,
) -> str:
    """Explain a verification failure in terms of the adopter's next action.

    A raw OpenSSL string tells an adopter behind a TLS-inspecting proxy nothing
    they can act on, which is how this failure reaches a maintainer instead of
    being self-served.

    *fallback_note* keeps the diagnosis honest — the caller states what actually
    happened to the operating-system fallback, because claiming the anchors were
    exhausted when they were never consulted sends the adopter after the wrong
    cause. *offer_opt_out* is false once the adopter has already opted out, so
    the message never advises setting a variable that is already set.
    """
    host = urllib.parse.urlsplit(url).netloc

    # Numbered at render time: the empty-store step only appears when it applies,
    # and a hardcoded list would misnumber every step after it.
    steps: list[str] = []
    if empty_store:
        steps.append(
            "This Python trusts ZERO certificate authorities, so every HTTPS\n"
            "     request from it fails — this is not a corporate-proxy problem.\n"
            "     A python.org macOS install needs its certificate step run once:\n"
            '       open "/Applications/Python 3.x/Install Certificates.command"\n'
            "     Or point it at the system bundle:\n"
            "       export SSL_CERT_FILE=/etc/ssl/cert.pem"
        )
    steps += [
        "Install from a local clone — needs no HTTPS at all:\n"
        "       git clone <catalogue-repo> && agentbundle install --pack "
        "<pack> ./<clone>",
        "Ask your IT team for the corporate CA bundle, then:\n"
        "       export AGENTBUNDLE_CA_BUNDLE=/path/to/corporate-ca.pem",
        "Check whether a different Python already trusts this network. "
        "Interpreters\n"
        "     do not share a certificate store, so one may work where another "
        "fails:\n"
        '       python3 -c "import ssl; print(ssl.get_default_verify_paths())"\n'
        "     Run that under each python3 on your PATH. If one differs and "
        "works, point\n"
        "     SSL_CERT_FILE at its cafile. Creating a virtualenv does NOT "
        "change trust —\n"
        "     a venv inherits its base interpreter's store unchanged.",
        "Confirm your proxy allows every host in the redirect chain. A "
        "GitHub\n"
        "     archive fetch redirects github.com to codeload.github.com; an "
        "allowlist\n"
        "     permitting only the first host fails here even once "
        "certificates work.",
    ]
    if offer_opt_out:
        steps.append(
            "Set AGENTBUNDLE_NO_SYSTEM_TRUST=1 to see the raw verification error."
        )
    body = "\n\n".join(f"  {n}. {s}" for n, s in enumerate(steps, start=1))

    if empty_store:
        diagnosis = (
            f"The certificate for {host} could not be verified. {fallback_note}"
        )
    else:
        diagnosis = (
            f"The certificate for {host} could not be verified. {fallback_note} On "
            "a corporate network this usually means a TLS-inspecting proxy "
            "re-signs traffic with a private root CA that Python does not read."
        )
    return (
        f"Failed to fetch catalogue archive: {url} — {detail}\n"
        "\n"
        f"{diagnosis}\n"
        "\n"
        "Troubleshooting, cheapest first:\n"
        "\n"
        f"{body}"
    )


def _system_trust_module():
    """Import ``system_trust`` lazily.

    Deferred so this module keeps making no subprocess call of its own, and to
    avoid a circular import — ``system_trust`` raises ``CatalogueError``.
    """
    from agentbundle import system_trust

    return system_trust


def _fetch_and_extract(url: str, dest: Path) -> None:
    system_trust = _system_trust_module()

    def attempt(context: ssl.SSLContext) -> None:
        # B310: constant github.com archive base assembled from parsed owner/repo/ref.
        with urllib.request.urlopen(  # nosec B310
            url, timeout=_FETCH_TIMEOUT_S, context=context
        ) as resp, tarfile.open(fileobj=resp, mode="r|gz") as tf:
            # filter="data" rejects unsafe members (absolute paths, ..
            # links, devices, setuid bits) — Python 3.12+ default but
            # explicit for 3.11 compatibility and to silence the 3.14
            # DeprecationWarning. Path-jail is belt; this is braces.
            tf.extractall(path=dest, filter="data")

    try:
        attempt(system_trust.build_context())
    except (urllib.error.URLError, ssl.SSLError, TimeoutError) as exc:
        # ssl.SSLError and TimeoutError are caught alongside URLError because
        # urlopen only wraps failures raised during connect. A stall or TLS
        # error while the tarball body is still streaming escapes unwrapped,
        # which would break this module's documented promise that an
        # unreachable URL raises CatalogueError.
        detail = getattr(exc, "reason", None) or exc
        if not _is_cert_verification_failure(exc):
            raise CatalogueError(
                f"Failed to fetch catalogue archive: {url} — {detail}"
            ) from exc
        if system_trust.system_trust_disabled():
            raise CatalogueError(
                _verification_failure_message(
                    url,
                    detail,
                    fallback_note=(
                        "The operating-system trust fallback was not attempted, "
                        "because AGENTBUNDLE_NO_SYSTEM_TRUST is set."
                    ),
                    offer_opt_out=False,
                )
            ) from exc
        # Resolve the anchors BEFORE announcing anything. On a platform with no
        # administrator trust store to read, a second connection against an
        # identical context would be pure noise, and claiming the anchors "did
        # not complete the chain" would send the adopter after the wrong cause.
        # An interpreter with an empty trust store is a different fault from an
        # inspected network: nothing verifies, and the administrator keychain
        # alone cannot repair it because it holds private roots, not public ones.
        # Observed in the field on a python.org macOS build whose
        # Install Certificates.command was never run.
        empty_store = system_trust.default_store_is_empty()
        anchors = system_trust.system_anchor_pem(include_public_roots=empty_store)
        if not anchors:
            # Two different causes, and conflating them misdirects the adopter.
            # Off macOS the fallback does not apply at all. *On* macOS it applied
            # and found an empty administrator keychain, which means the
            # authority is installed somewhere this deliberately does not read.
            if sys.platform == "darwin":
                note = (
                    "The administrator keychain holds no certificates to retry "
                    "with, so the authority is likely installed somewhere else — "
                    "a login keychain, or an application's own store. Only "
                    "/Library/Keychains/System.keychain is read, because it is "
                    "the one store that requires administrator rights to write."
                )
            else:
                note = (
                    f"No operating-system trust anchors were consulted on "
                    f"{sys.platform}: the automatic fallback is macOS-only, "
                    "because macOS is the only platform where Python ignores "
                    "the operating system's trust store."
                )
            raise CatalogueError(
                _verification_failure_message(
                    url, detail, fallback_note=note, empty_store=empty_store
                )
            ) from exc
        _retry_with_system_trust(url, dest, attempt, anchors, empty_store=empty_store)
    except tarfile.TarError as exc:
        raise CatalogueError(
            f"Failed to extract tarball from {url}: {exc}"
        ) from exc


def _retry_with_system_trust(
    url: str,
    dest: Path,
    attempt: Callable[[ssl.SSLContext], None],
    anchors: str,
    *,
    empty_store: bool = False,
) -> None:
    """Retry *attempt* once against operating-system trust *anchors*.

    Announced on stderr unconditionally: a trust decision the adopter cannot see
    is a trust decision they cannot audit. Bounded at one extra attempt, reached
    only for a certificate-verification failure — never a timeout, DNS failure,
    or HTTP error — and only when *anchors* actually exist, so the notice never
    describes work that did not happen.
    """
    system_trust = _system_trust_module()
    host = urllib.parse.urlsplit(url).netloc
    print(
        f"agentbundle: certificate verification failed for {host}; "
        "retrying with operating-system trust anchors",
        file=sys.stderr,
    )
    if empty_store:
        exhausted = (
            "This Python trusts no certificate authority at all — its trust store "
            "is empty — and the operating-system anchors did not complete the "
            "chain either."
        )
    else:
        exhausted = (
            "The operating-system trust anchors did not complete the chain either."
        )
    # Attempt 1 may have extracted part of the archive before failing mid-stream.
    # Clearing the destination keeps the retry from layering a second download
    # over the first and producing a catalogue that is a mix of both.
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True, exist_ok=True)
    try:
        attempt(system_trust.build_context(system_anchors=anchors))
    except (urllib.error.URLError, ssl.SSLError, TimeoutError) as exc:
        # Same tuple as the first attempt: a read-phase stall or TLS error is not
        # wrapped by urlopen and would otherwise escape as a bare exception.
        detail = getattr(exc, "reason", None) or exc
        raise CatalogueError(
            _verification_failure_message(
                url, detail, fallback_note=exhausted, empty_store=empty_store
            )
        ) from exc
    except tarfile.TarError as exc:
        raise CatalogueError(
            f"Failed to extract tarball from {url}: {exc}"
        ) from exc


def _find_inner_dir(tmpdir: Path) -> Path:
    """Return the single top-level directory inside *tmpdir*.

    GitHub archives always produce exactly one top-level directory
    (``<repo>-<ref>/``). If the extraction produced something else,
    return *tmpdir* itself so callers still have something to work with.
    """
    children = [p for p in tmpdir.iterdir() if p.is_dir()]
    if len(children) == 1:
        return children[0]
    return tmpdir
