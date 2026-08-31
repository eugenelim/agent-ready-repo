"""Credential-free GitHub archive acquisition for the direct route.

The module owns E11's Family-1 acquisition bounds, the redirect equivalence
policy, and the interpreter runtime floor.  It deliberately holds no TLS
classifier and no trust retry of its own: both come from the one shared entry
point in ``agentbundle.catalogue``, because a per-route restatement would drift
from the catalogue route silently while passing every test written against this
module alone.
"""

from __future__ import annotations

import gzip
import re
import shutil
import ssl
import sys
import tarfile
import tempfile
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from agentbundle.catalogue import classify_transport_attempt, retry_with_system_trust
from agentbundle.catalogue_tooling.diagnostics import (
    DiagnosticCode,
    make_direct_diagnostic,
)
from agentbundle.catalogue_tooling.results import Diagnostic, Severity

# --- E11 Family-1 acquisition bounds -----------------------------------------
#
# Module constants rather than configuration on purpose: AC5 states that no
# flag, environment variable, or configuration may raise either family, and the
# injectable seams below may only tighten them.
MAX_DOWNLOAD_BYTES = 256 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 20_000
MAX_DECOMPRESSED_BYTES = 1024 * 1024 * 1024
SOCKET_TIMEOUT_SECONDS = 30
INACTIVITY_TIMEOUT_SECONDS = 90
MAX_REDIRECTS = 5

# E11 constants consumed by the `list-installed` status route.
LIST_INSTALLED_CHECK_DEADLINE_SECONDS = 90
LIST_INSTALLED_CHECK_MAX_RESOLUTIONS = 25

# E11's runtime floor, read at call time rather than at import. Each entry is
# the lowest admitted patch for that minor; a minor above the highest listed one
# is admitted outright, and a minor below the lowest refuses.
RUNTIME_FLOOR: dict[int, int] = {11: 13, 12: 11, 13: 4, 14: 0}

_SOURCE_PREFIX = "git+https://github.com/"
_OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
_REPO_RE = re.compile(r"^[A-Za-z0-9_.][A-Za-z0-9_.-]{0,99}$")
_REF_RE = re.compile(r"^[A-Za-z0-9._/-]{1,255}$")
_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DEFAULTED_REFS = frozenset({"main", "master", "HEAD"})

# AC18: the C0/C1 ranges and DEL are what turn a transport detail into log
# forgery or terminal control once it reaches a message or a remediation.
_UNSAFE_DETAIL = re.compile(r"[\x00-\x1f\x7f-\x9f]")

_UNSET: object = object()


class DirectAcquisitionError(ValueError):
    """A direct-route acquisition refusal carrying its registered diagnostic."""

    def __init__(self, diagnostic: Diagnostic) -> None:
        super().__init__(diagnostic.message)
        self.diagnostic = diagnostic


@dataclass(frozen=True)
class DirectSource:
    """A parsed `git+https` source and the exact string that produced it.

    ``requested`` is retained verbatim because AC4 builds every later request
    from the string that passed the grammar, with no re-canonicalisation between
    validation and request.  Rebuilding it from the parts would be a re-parse.
    """

    requested: str
    owner: str
    repository: str
    ref: str
    ref_kind: str  # "sha" | "abbreviated-sha" | "ref"


@dataclass(frozen=True)
class AcquiredArchive:
    """An extracted archive root and the revision its bytes are bound to.

    ``working`` is the temporary directory the caller must remove when it is
    done, carried explicitly rather than derived from ``root``. Deriving it by
    walking parents is wrong the moment ``root`` is not nested at the expected
    depth — with no wrapper directory to descend through, two levels up from
    ``root`` is the system temporary directory.
    """

    root: Path
    revision: str
    downloaded_bytes: int
    members: int
    working: Path


def _refuse(
    code: DiagnosticCode,
    message: str,
    *,
    path: str,
    remediation: str | None = None,
) -> DirectAcquisitionError:
    """Build a registered refusal; an unregistered code cannot reach a user."""

    return DirectAcquisitionError(
        make_direct_diagnostic(
            code, Severity.ERROR, message, path=path, remediation=remediation
        )
    )


def escape_transport_detail(detail: object) -> str:
    """Render an externally supplied transport string safe for any surface.

    A redirect `Location`, an HTTP reason phrase, and a TLS error detail are all
    attacker-influenced and none is publisher metadata, so they bypass AC18's
    publisher allowlist entirely.  Left raw they carry CR/LF log forgery and
    ANSI terminal escapes straight into `message` and `remediation`.
    """

    return _UNSAFE_DETAIL.sub(lambda m: f"\\x{ord(m.group()):02x}", str(detail))


def enforce_runtime_floor(source: str) -> None:
    """Refuse an interpreter below E11's floor, at acquisition entry.

    Read at call time rather than import time, and placed before any archive
    byte is read, so a route that refuses before ever reaching extraction still
    carries the floor.  `pyproject.toml`'s `requires-python` is advisory: it
    governs installation, not the interpreter that is already running.
    """

    lowest = min(RUNTIME_FLOOR)
    major, minor, patch = (
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro,
    )
    if major != 3 or minor < lowest:
        raise _refuse(
            DiagnosticCode.CAT_D005,
            f"Python {major}.{minor}.{patch} is below the supported floor "
            f"3.{lowest}.{RUNTIME_FLOOR[lowest]}",
            path=source,
            remediation="Upgrade to a supported Python before installing.",
        )
    floor = RUNTIME_FLOOR.get(minor)
    if floor is not None and patch < floor:
        raise _refuse(
            DiagnosticCode.CAT_D005,
            f"Python 3.{minor}.{patch} is below the supported patch floor "
            f"3.{minor}.{floor}",
            path=source,
            remediation=f"Upgrade to Python 3.{minor}.{floor} or later.",
        )


def parse_direct_source(source: str) -> DirectSource:
    """Validate a `git+https` source string against AC3's grammar."""

    if not source.startswith(_SOURCE_PREFIX):
        raise _refuse(
            DiagnosticCode.CAT_D001,
            "direct sources must be GitHub `git+https` URLs",
            path=escape_transport_detail(source),
            remediation=f"Use {_SOURCE_PREFIX}<owner>/<repository>@<ref>.",
        )
    remainder = source[len(_SOURCE_PREFIX) :]
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in remainder):
        raise _refuse(
            DiagnosticCode.CAT_D001,
            "source contains a control code point",
            path=escape_transport_detail(source),
            remediation="Remove the control character from the source.",
        )
    if "?" in remainder or "#" in remainder or "//" in remainder:
        raise _refuse(
            DiagnosticCode.CAT_D001,
            "a direct source carries no query or fragment component",
            path=source,
            remediation=f"Use {_SOURCE_PREFIX}<owner>/<repository>@<ref>.",
        )
    if remainder.count("@") > 1:
        raise _refuse(
            DiagnosticCode.CAT_D001,
            "a direct source carries no user-info component",
            path=source,
            remediation=f"Use {_SOURCE_PREFIX}<owner>/<repository>@<ref>.",
        )

    body, separator, ref = remainder.partition("@")
    parts = body.split("/")
    if len(parts) != 2 or not all(parts):
        raise _refuse(
            DiagnosticCode.CAT_D001,
            "a direct source names exactly one owner and one repository",
            path=source,
            remediation=f"Use {_SOURCE_PREFIX}<owner>/<repository>@<ref>.",
        )
    owner, repository = parts
    if repository.endswith(".git"):
        repository = repository[:-4]
    if not _OWNER_RE.match(owner) or not _REPO_RE.match(repository):
        raise _refuse(
            DiagnosticCode.CAT_D001,
            f"malformed owner or repository: {escape_transport_detail(body)}",
            path=source,
            remediation="Check the owner and repository spelling.",
        )
    if not separator or not ref:
        raise _refuse(
            DiagnosticCode.CAT_D002,
            "a direct source must pin an explicit revision",
            path=source,
            remediation=(
                "Append @<tag>, @<branch>, or @<40-hex-sha>. A defaulted branch "
                "is refused because it names different bytes over time."
            ),
        )
    if ref in _DEFAULTED_REFS:
        raise _refuse(
            DiagnosticCode.CAT_D002,
            f"{ref!r} is a defaulted branch and is not a revision pin",
            path=source,
            remediation="Pin a tag or a 40-hex commit SHA instead.",
        )
    if not _REF_RE.match(ref) or any(
        segment in {"", ".", ".."} for segment in ref.split("/")
    ):
        raise _refuse(
            DiagnosticCode.CAT_D001,
            f"malformed ref: {escape_transport_detail(ref)}",
            path=source,
            remediation="Use a tag, branch, or commit SHA with no dot segments.",
        )

    kind = "ref"
    if _HEX_RE.match(ref):
        if len(ref) == 40:
            kind = "sha"
        elif 7 <= len(ref) < 40:
            kind = "abbreviated-sha"
        else:
            # Hex-shaped but neither a SHA nor an abbreviation of one. Guessing
            # is unsafe in both directions: read as a tag it silently skips the
            # SHA binding, read as an abbreviation it fails against every
            # archive.
            raise _refuse(
                DiagnosticCode.CAT_D003,
                f"{ref!r} is hex-shaped but cannot be classified as an "
                f"abbreviated commit SHA",
                path=source,
                remediation=(
                    "Use a full 40-hex SHA, an abbreviation of at least seven "
                    "hex characters, or a tag that is not hex-shaped."
                ),
            )
    return DirectSource(source, owner, repository, ref, kind)


def _quoted(source: DirectSource) -> list[str]:
    """Percent-encode each component with an empty safe set.

    A git ref may legally contain `/`; encoding with `safe=""` is what stops
    that from introducing a path segment into the built URL.
    """

    return [
        urllib.parse.quote(part, safe="")
        for part in (source.owner, source.repository, source.ref)
    ]


def archive_url(source: DirectSource) -> str:
    """Build the requested archive URL and re-validate the re-parsed result."""

    url = "https://github.com/{}/{}/archive/{}.tar.gz".format(*_quoted(source))
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.netloc != "github.com"
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
    ):
        raise _refuse(
            DiagnosticCode.CAT_D001,
            "the constructed archive URL failed re-validation",
            path=source.requested,
            remediation="Report this as a bug: the source parsed but its URL did not.",
        )
    return url


def permitted_redirect_targets(source: DirectSource) -> frozenset[str]:
    """The only hosts and paths a redirect may land on.

    Compared in the same percent-encoded form as the request: comparing a
    decoded target against an encoded expectation would admit a target that
    merely decodes to the right place.
    """

    owner, repository, ref = _quoted(source)
    return frozenset(
        {
            f"https://github.com/{owner}/{repository}/archive/{ref}.tar.gz",
            f"https://codeload.github.com/{owner}/{repository}/tar.gz/{ref}",
            f"https://codeload.github.com/{owner}/{repository}/tar.gz/refs/tags/{ref}",
            f"https://codeload.github.com/{owner}/{repository}/tar.gz/refs/heads/{ref}",
        }
    )


class _BoundedRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Allow at most E11's redirects, and only to an equivalent target."""

    max_redirections = MAX_REDIRECTS

    def __init__(self, source: DirectSource) -> None:
        self._source = source
        self._permitted = permitted_redirect_targets(source)

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        parsed = urllib.parse.urlsplit(newurl)
        detail = escape_transport_detail(newurl)
        if parsed.scheme != "https":
            raise _refuse(
                DiagnosticCode.CAT_D001,
                f"refused a non-HTTPS redirect to {detail}",
                path=self._source.requested,
                remediation="The publisher's host must redirect over HTTPS only.",
            )
        if parsed.username is not None or parsed.password is not None:
            raise _refuse(
                DiagnosticCode.CAT_D001,
                f"refused a redirect carrying user-info to {detail}",
                path=self._source.requested,
                remediation="Credential-free acquisition rejects user-info in a URL.",
            )
        if newurl.split("?")[0] not in self._permitted:
            raise _refuse(
                DiagnosticCode.CAT_D001,
                f"refused a redirect to a non-equivalent target: {detail}",
                path=self._source.requested,
                remediation=(
                    "A redirect may only reach the same owner, repository, and "
                    "ref on github.com or codeload.github.com."
                ),
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _resolve_seam(value: object, constant: int, label: str, source: str) -> int:
    """Validate an injected numeric seam, then let it only tighten the bound.

    Order matters and AC5 asserts it: validate first, then `min`. Applying `min`
    to an unvalidated value would let `True` through as `1`, silently setting
    the tightest possible bound instead of refusing.
    """

    if value is _UNSET:
        return constant
    if value is None or isinstance(value, bool) or not isinstance(value, int):
        raise _refuse(
            DiagnosticCode.CAT_D006,
            f"{label} must be a non-negative integer",
            path=source,
            remediation="Remove the injected seam; it is a test-only parameter.",
        )
    if value < 0:
        raise _refuse(
            DiagnosticCode.CAT_D006,
            f"{label} must not be negative",
            path=source,
            remediation="Remove the injected seam; it is a test-only parameter.",
        )
    return min(constant, value)


def _validated_clock(candidate: object, source: str) -> Callable[[], float]:
    """Accept an injected clock only if it is callable and does not run back."""

    if not callable(candidate):
        raise _refuse(
            DiagnosticCode.CAT_D006,
            "the injected clock seam must be callable",
            path=source,
            remediation="Remove the injected seam; it is a test-only parameter.",
        )
    first, second = candidate(), candidate()
    if not isinstance(first, int | float) or not isinstance(second, int | float):
        raise _refuse(
            DiagnosticCode.CAT_D006,
            "the injected clock seam must return a number",
            path=source,
            remediation="Remove the injected seam; it is a test-only parameter.",
        )
    if second < first:
        raise _refuse(
            DiagnosticCode.CAT_D006,
            "the injected clock seam must not run backwards",
            path=source,
            remediation="Remove the injected seam; it is a test-only parameter.",
        )
    return candidate  # type: ignore[return-value]


def _validated_progress(candidate: object, source: str) -> Callable[[int], None]:
    """Accept an injected progress callback only if it is callable."""

    if not callable(candidate):
        raise _refuse(
            DiagnosticCode.CAT_D006,
            "the injected progress seam must be callable",
            path=source,
            remediation="Remove the injected seam; it is a test-only parameter.",
        )
    return candidate  # type: ignore[return-value]


def _download(
    url: str,
    source: DirectSource,
    spool: Path,
    *,
    context: ssl.SSLContext,
    max_bytes: int,
    inactivity: int,
    clock: Callable[[], float],
    progress: Callable[[int], None] | None,
) -> int:
    """Stream the archive to *spool*, bounded by bytes and by stall.

    The opener carries the *classified* context. Building one without an
    `HTTPSHandler` silently used urllib's ambient default instead, so
    `system_trust.build_context()`'s additive `load_verify_locations` never
    reached the request — `AGENTBUNDLE_CA_BUNDLE` was inert on this route while
    the certificate-failure remediation told adopters to set it.
    """

    opener = urllib.request.build_opener(
        _BoundedRedirectHandler(source),
        urllib.request.HTTPSHandler(context=context),
    )
    downloaded = 0
    last_progress = clock()
    with opener.open(url, timeout=SOCKET_TIMEOUT_SECONDS) as response:
        status = getattr(response, "status", 200)
        if status != 200:
            reason = escape_transport_detail(getattr(response, "reason", status))
            raise _refuse(
                DiagnosticCode.CAT_D006,
                f"archive request returned {status}: {reason}",
                path=source.requested,
                remediation="Check that the owner, repository, and ref exist.",
            )
        with spool.open("wb") as handle:
            while True:
                chunk = response.read(64 * 1024)
                now = clock()
                if not chunk:
                    break
                if now - last_progress > inactivity:
                    raise _refuse(
                        DiagnosticCode.CAT_D006,
                        f"archive transfer stalled for more than {inactivity}s",
                        path=source.requested,
                        remediation="Retry; the publisher's host stopped responding.",
                    )
                downloaded += len(chunk)
                if downloaded > max_bytes:
                    raise _refuse(
                        DiagnosticCode.CAT_D006,
                        f"archive exceeds the {max_bytes}-byte download limit",
                        path=source.requested,
                        remediation="The repository is too large to install directly.",
                    )
                handle.write(chunk)
                if progress is not None:
                    progress(downloaded)
                last_progress = now
    return downloaded


def _member_is_safe(name: str) -> bool:
    """Reject a member destination that is absolute, escaping, or poisonous."""

    if not name or name.startswith("/") or "\\" in name:
        return False
    pure = PurePosixPath(name)
    if pure.is_absolute():
        return False
    return all(part not in {"", ".", ".."} for part in pure.parts)


def _read_revision(archive: tarfile.TarFile, source: DirectSource) -> str:
    """Read the 40-hex commit SHA GitHub records in `pax_global_header`."""

    candidate = archive.pax_headers.get("comment", "").strip().lower()
    if not _SHA_RE.match(candidate):
        raise _refuse(
            DiagnosticCode.CAT_D004,
            "the archive carries no readable 40-hex commit SHA",
            path=source.requested,
            remediation="The archive is not a GitHub source archive.",
        )
    if source.ref_kind == "sha" and candidate != source.ref.lower():
        raise _refuse(
            DiagnosticCode.CAT_D004,
            "the archive SHA does not equal the requested 40-hex ref",
            path=source.requested,
            remediation="The publisher moved the ref; re-pin to the new SHA.",
        )
    if source.ref_kind == "abbreviated-sha" and not candidate.startswith(
        source.ref.lower()
    ):
        raise _refuse(
            DiagnosticCode.CAT_D004,
            "the archive SHA does not extend the requested abbreviated ref",
            path=source.requested,
            remediation="Re-pin to the full 40-hex SHA.",
        )
    return candidate


def _refuse_member(source: DirectSource, name: str, reason: str, fix: str) -> None:
    """One refusal shape for every AC6 member rule."""

    raise _refuse(
        DiagnosticCode.CAT_D007,
        f"{reason}: {escape_transport_detail(name)}",
        path=source.requested,
        remediation=fix,
    )


def _extract(
    spool: Path,
    destination: Path,
    source: DirectSource,
    *,
    max_members: int,
    max_decompressed: int,
) -> tuple[str, int, set[str]]:
    """Extract the archive under Family-1 bounds and AC6's link policy.

    Also returns the set of first path segments seen across every member. A
    GitHub source archive prefixes all of them with one `<repo>-<ref>/`
    directory, and the caller has to descend through it to reach the source
    root — admission looks for `SKILL.md`, `skills/`, or `pack.toml`, none of
    which sit beside the wrapper.
    """

    seen_casefolded: set[str] = set()
    root_segments: set[str] = set()
    members = 0
    decompressed = 0
    with (
        gzip.open(spool, "rb") as stream,
        tarfile.open(fileobj=stream, mode="r:") as archive,
    ):
        revision = _read_revision(archive, source)
        for member in archive:
            members += 1
            if members > max_members:
                raise _refuse(
                    DiagnosticCode.CAT_D006,
                    f"the archive exceeds the {max_members}-member limit",
                    path=source.requested,
                    remediation="The repository is too large to install directly.",
                )
            decompressed += max(member.size, 0)
            if decompressed > max_decompressed:
                raise _refuse(
                    DiagnosticCode.CAT_D006,
                    f"the archive exceeds the {max_decompressed}-byte "
                    f"decompressed limit",
                    path=source.requested,
                    remediation="The repository is too large to install directly.",
                )
            # The library-resolved name, never a reconstructed one.
            if not _member_is_safe(member.name):
                _refuse_member(
                    source,
                    member.name,
                    "archive member escapes its destination",
                    "The archive is malformed or hostile.",
                )
            if member.issym() or member.islnk():
                # Direct-only. The catalogue route deliberately retains
                # symlinks, because a catalogue legitimately ships
                # CLAUDE.md -> AGENTS.md.
                if member.linkname and not _member_is_safe(member.linkname):
                    _refuse_member(
                        source,
                        member.linkname,
                        "archive link target escapes the root",
                        "The archive is malformed or hostile.",
                    )
                _refuse_member(
                    source,
                    member.name,
                    "a direct source may not carry links",
                    "Ask the publisher to ship regular files only.",
                )
            if member.isdev() or member.isfifo():
                _refuse_member(
                    source,
                    member.name,
                    "the archive carries a device or FIFO member",
                    "The archive is malformed or hostile.",
                )
            folded = member.name.casefold()
            if folded in seen_casefolded:
                _refuse_member(
                    source,
                    member.name,
                    "archive members collide when case-folded",
                    "The archive cannot be extracted safely on a "
                    "case-insensitive filesystem.",
                )
            seen_casefolded.add(folded)
            root_segments.add(PurePosixPath(member.name).parts[0])
            archive.extract(member, path=destination, filter="data")
    return revision, members, root_segments


def _acquire_bytes(
    url: str,
    source: DirectSource,
    spool: Path,
    *,
    max_bytes: int,
    inactivity: int,
    clock: Callable[[], float],
    progress: Callable[[int], None] | None,
) -> int:
    """Run the download through the one shared transport classifier."""

    captured: dict[str, int] = {}

    def attempt(context: ssl.SSLContext) -> None:
        captured["downloaded"] = _download(
            url,
            source,
            spool,
            context=context,
            max_bytes=max_bytes,
            inactivity=inactivity,
            clock=clock,
            progress=progress,
        )

    outcome = classify_transport_attempt(attempt)
    if outcome.ok:
        return captured["downloaded"]
    exception = outcome.exception
    detail = escape_transport_detail(getattr(exception, "reason", None) or exception)
    if outcome.certificate_failure and outcome.anchors:
        # AC37's single retry against operating-system anchors, through the one
        # shared entry point rather than a per-route copy. Reached only for a
        # certificate-verification failure, only when anchors exist, and
        # disabled by AGENTBUNDLE_NO_SYSTEM_TRUST — which
        # `classify_transport_attempt` reports by leaving `anchors` unset.
        retry_with_system_trust(
            url, spool.parent, attempt, outcome.anchors, empty_store=outcome.empty_store
        )
        return captured["downloaded"]
    if outcome.certificate_failure:
        raise _refuse(
            DiagnosticCode.CAT_D006,
            f"the certificate for {url} could not be verified: {detail}",
            path=source.requested,
            remediation=(
                "Install the authority into the operating-system trust store, "
                "or set AGENTBUNDLE_CA_BUNDLE to a bundle that contains it."
            ),
        ) from exception
    raise _refuse(
        DiagnosticCode.CAT_D006,
        f"failed to fetch the source archive: {detail}",
        path=source.requested,
        remediation="Check network reachability and the source spelling.",
    ) from exception


def acquire_git_https_archive(
    source_string: str,
    *,
    parent: Path | None = None,
    _clock: object = _UNSET,
    _progress: object = _UNSET,
    _max_download_bytes: object = _UNSET,
    _max_members: object = _UNSET,
    _max_decompressed_bytes: object = _UNSET,
    _inactivity_seconds: object = _UNSET,
) -> AcquiredArchive:
    """Acquire and extract one credential-free GitHub source archive.

    The underscore-prefixed seams are keyword-only, private, and supplied by no
    production call site; they exist so deadline and bound tests run
    deterministically instead of downloading a gigabyte.  Each may only tighten
    its bound, never raise it.
    """

    enforce_runtime_floor(source_string)
    source = parse_direct_source(source_string)
    url = archive_url(source)

    max_download = _resolve_seam(
        _max_download_bytes, MAX_DOWNLOAD_BYTES, "download limit", source_string
    )
    max_members = _resolve_seam(
        _max_members, MAX_ARCHIVE_MEMBERS, "member limit", source_string
    )
    max_decompressed = _resolve_seam(
        _max_decompressed_bytes,
        MAX_DECOMPRESSED_BYTES,
        "decompressed limit",
        source_string,
    )
    inactivity = _resolve_seam(
        _inactivity_seconds,
        INACTIVITY_TIMEOUT_SECONDS,
        "inactivity timeout",
        source_string,
    )
    clock = (
        time.monotonic if _clock is _UNSET else _validated_clock(_clock, source_string)
    )
    progress = (
        None if _progress is _UNSET else _validated_progress(_progress, source_string)
    )

    working = Path(tempfile.mkdtemp(prefix="agentbundle-direct-src-", dir=parent))
    try:
        spool = working / "archive.tar.gz"
        extracted = working / "tree"
        extracted.mkdir()
        downloaded = _acquire_bytes(
            url,
            source,
            spool,
            max_bytes=max_download,
            inactivity=inactivity,
            clock=clock,
            progress=progress,
        )
        revision, members, root_segments = _extract(
            spool,
            extracted,
            source,
            max_members=max_members,
            max_decompressed=max_decompressed,
        )
        spool.unlink()
        # Descend through GitHub's single wrapper directory. Derived from the
        # member names rather than by listing the extracted tree, so a source
        # whose members genuinely sit at the archive root is left alone instead
        # of being descended into by accident.
        if len(root_segments) == 1:
            candidate = extracted / next(iter(root_segments))
            if candidate.is_dir():
                extracted = candidate
    except BaseException:
        # AC25: every refusal removes its temporary tree.
        shutil.rmtree(working, ignore_errors=True)
        raise
    return AcquiredArchive(extracted, revision, downloaded, members, working)
