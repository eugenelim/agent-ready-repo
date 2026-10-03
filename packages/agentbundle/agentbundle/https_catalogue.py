"""HTTPS catalogue and archive fetcher for enterprise distribution.

Implements ``catalogue+https://`` and ``archive+https://`` source URI schemes:

- ``catalogue+https://``: fetch a JSON channel descriptor, resolve the artifact
  URL, stream and SHA-256-verify the archive, extract it to a temp directory.
- ``archive+https://``: fetch a pinned archive URL directly; the ``#sha256=``
  fragment supplies the expected digest.

Security invariants:
- Bearer credential resolved via ``credbroker``; never read directly or
  logged, printed, or forwarded to a different origin.
- Same-origin redirect enforcement and cross-origin rejection are delegated
  to ``catalogue_fetch``'s direct HTTP provider.
- HTTPS only — scheme-downgrade redirects are rejected before the redirected
  request is sent.
- Archive extracted member-by-member; never ``extractall()`` without per-member
  safety checks. Path traversal, absolute paths, symlinks, hard links, and
  special files are all rejected.
- SHA-256 verified before extraction; temp dir cleaned up on any failure.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlsplit, urlunsplit

from agentbundle.catalogue import CatalogueError


@dataclass
class CatalogueArchiveResult:
    """Provenance metadata returned alongside the extracted archive path."""

    path: Path
    artifact_uri: str | None = None
    archive_sha256: str | None = None
    source_revision: str | None = None


# ---------------------------------------------------------------------------
# Named safety limits (all enforced regardless of Content-Length)
# ---------------------------------------------------------------------------

_MAX_DESCRIPTOR_BYTES = 1 * 1024 * 1024          # 1 MiB
_MAX_ARCHIVE_BYTES = 256 * 1024 * 1024            # 256 MiB
_MAX_MEMBERS = 20_000
_MAX_EXPANDED_BYTES = 1 * 1024 * 1024 * 1024      # 1 GiB
_HTTP_TIMEOUT = 30                                 # seconds

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

_DESCRIPTOR_REQUIRED_FIELDS = (
    "schema", "kind", "bundle", "channel", "release", "artifact", "sha256"
)


# ---------------------------------------------------------------------------
# Descriptor parsing and validation
# ---------------------------------------------------------------------------


def _parse_descriptor(data: bytes) -> dict:
    """Parse and validate a JSON channel descriptor.

    Required fields: ``schema`` (must be 1), ``kind`` (must be
    ``"agentbundle-catalogue"``), ``bundle``, ``channel``, ``release``,
    ``artifact``, ``sha256`` (must be exactly 64 lowercase hex chars).
    """
    try:
        obj = json.loads(data)
    except (json.JSONDecodeError, ValueError) as exc:
        raise CatalogueError(f"channel descriptor is not valid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise CatalogueError("channel descriptor must be a JSON object")

    for field in _DESCRIPTOR_REQUIRED_FIELDS:
        if field not in obj:
            raise CatalogueError(
                f"channel descriptor missing required field: {field!r}"
            )

    if obj["schema"] != 1:
        raise CatalogueError(
            f"channel descriptor schema must be 1; got {obj['schema']!r}"
        )
    if obj["kind"] != "agentbundle-catalogue":
        raise CatalogueError(
            f"channel descriptor kind must be 'agentbundle-catalogue'; got {obj['kind']!r}"
        )
    sha256_val = obj["sha256"]
    if not isinstance(sha256_val, str) or not _SHA256_RE.fullmatch(sha256_val):
        raise CatalogueError(
            "channel descriptor sha256 must be exactly 64 lowercase hex characters; "
            f"got {sha256_val!r}"
        )
    return obj


# ---------------------------------------------------------------------------
# Artifact URL resolution and origin checking
# ---------------------------------------------------------------------------


def _resolve_artifact_url(descriptor_url: str, artifact_field: str) -> str:
    """Resolve artifact URL against descriptor URL; enforce same-origin + HTTPS.

    Same-origin is defined as scheme + host + port all equal to the
    ORIGINALLY-REQUESTED channel descriptor URL (not the post-redirect URL).
    """
    resolved = urljoin(descriptor_url, artifact_field)
    parsed = urlsplit(resolved)

    # Reject HTTP
    if parsed.scheme.lower() != "https":
        raise CatalogueError(
            f"artifact URL must use HTTPS; got scheme {parsed.scheme!r}"
        )
    # Reject user-info
    if "@" in parsed.netloc:
        raise CatalogueError("artifact URL contains user-info in netloc; rejected")

    # Same-origin check against originally-requested descriptor URL
    orig = urlsplit(descriptor_url)

    def _origin(p) -> tuple:
        return (p.scheme.lower(), (p.hostname or "").lower(), p.port)

    if _origin(parsed) != _origin(orig):
        raise CatalogueError(
            "cross-origin artifact URL rejected: artifact origin does not match "
            "channel descriptor origin (scheme+host+port must all match)"
        )
    return resolved


# ---------------------------------------------------------------------------
# Client version check
# ---------------------------------------------------------------------------


def _parse_semver(version_str: str, label: str) -> tuple[int, int, int]:
    """Parse a MAJOR.MINOR.PATCH version string into an integer tuple.

    Raises ``CatalogueError`` for non-numeric / malformed strings.
    """
    m = _SEMVER_RE.fullmatch(version_str.strip())
    if not m:
        raise CatalogueError(
            f"{label} version {version_str!r} is not a valid MAJOR.MINOR.PATCH string"
        )
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _check_client_version(minimum: str | None, *, running_version: str | None = None) -> None:
    """Fail if the running agentbundle version is older than ``minimum``.

    Uses integer-tuple ``(MAJOR, MINOR, PATCH)`` comparison, never lexicographic.
    ``running_version`` is injectable for testing; when ``None`` the module
    attribute ``agentbundle.__version__`` is read at call time (not a
    from-import copy, so it can be monkeypatched in tests).
    """
    if minimum is None:
        return
    if running_version is None:
        import agentbundle as _agentbundle
        running_version = _agentbundle.__version__

    min_tuple = _parse_semver(minimum, "minimum_agentbundle_version")
    running_tuple = _parse_semver(running_version, "running agentbundle")

    if running_tuple < min_tuple:
        raise CatalogueError(
            f"agentbundle {running_version} is older than the minimum required version "
            f"{minimum}; upgrade with: pip install --upgrade agentbundle"
        )


# ---------------------------------------------------------------------------
# Archive SHA-256 verification
# ---------------------------------------------------------------------------


def _sha256_of_file(path: Path) -> str:
    """Return the SHA-256 hex digest of *path*, reading in 64 KiB chunks."""
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def _verify_archive_sha256(path: Path, expected_sha256: str, url: str) -> None:
    """Hash ``path`` in 64 KiB chunks and verify against ``expected_sha256``.

    On mismatch the file at ``path`` is removed before the ``CatalogueError``
    is raised.  The error message includes both the expected and received
    digests.  The URL is included only for identification, never a credential.
    """
    try:
        received = _sha256_of_file(path)
    except OSError as exc:
        raise CatalogueError(f"failed to read archive {url!r}: {exc}") from exc
    if received != expected_sha256:
        with contextlib.suppress(OSError):
            path.unlink(missing_ok=True)
        raise CatalogueError(
            f"SHA-256 mismatch for archive {url!r}: "
            f"expected {expected_sha256!r}, received {received!r}"
        )


def _verify_jfrog_archive_sha256(path: Path, expected_sha256: str, url: str) -> None:
    """Verify the digest of a JFrog CLI archive, applying the appended-byte rule.

    The JFrog CLI appends one ``0x0a`` to stdout when the response body does
    not already end in that byte.  This function therefore tries two digest
    candidates in order:

    1. The exact file bytes (no trim).
    2. The file bytes with the last byte removed, provided the file is
       non-empty and its last byte is ``0x0a``.

    If the exact bytes match, no modification is made and the file is left
    as-is for extraction.  If the trimmed bytes match, the file is truncated
    by one byte so that only the verified candidate goes on to extraction.
    If neither candidate matches, the file is removed and ``CatalogueError``
    is raised.

    Args:
        path: Path to the downloaded archive temp file.
        expected_sha256: Expected 64-character lowercase hex SHA-256 digest.
        url: Archive URL, included only for identification in error messages.

    Raises:
        CatalogueError: Both candidates fail digest verification, or an
            I/O error occurs.
    """
    try:
        received = _sha256_of_file(path)
    except OSError as exc:
        raise CatalogueError(f"failed to read archive {url!r}: {exc}") from exc

    # Candidate 1: exact bytes.
    if received == expected_sha256:
        return

    # Candidate 2: trim one trailing 0x0a byte and re-verify.
    try:
        file_size = path.stat().st_size
    except OSError as exc:
        with contextlib.suppress(OSError):
            path.unlink(missing_ok=True)
        raise CatalogueError(f"failed to stat archive {url!r}: {exc}") from exc

    if file_size > 0:
        try:
            with path.open("rb") as fh:
                fh.seek(-1, 2)  # Seek to last byte.
                last_byte = fh.read(1)
        except OSError as exc:
            with contextlib.suppress(OSError):
                path.unlink(missing_ok=True)
            raise CatalogueError(f"failed to read archive {url!r}: {exc}") from exc

        if last_byte == b"\x0a":
            # Compute digest of all-but-last-byte without holding the full
            # content in memory: re-read the file up to file_size-1 bytes.
            hasher = hashlib.sha256()
            try:
                with path.open("rb") as fh:
                    remaining = file_size - 1
                    while remaining > 0:
                        chunk = fh.read(min(65536, remaining))
                        if not chunk:
                            break
                        hasher.update(chunk)
                        remaining -= len(chunk)
            except OSError as exc:
                with contextlib.suppress(OSError):
                    path.unlink(missing_ok=True)
                raise CatalogueError(
                    f"failed to read archive {url!r}: {exc}"
                ) from exc
            trimmed_digest = hasher.hexdigest()

            if trimmed_digest == expected_sha256:
                # Truncate the file to the verified length.
                try:
                    with path.open("r+b") as fh:
                        fh.truncate(file_size - 1)
                except OSError as exc:
                    with contextlib.suppress(OSError):
                        path.unlink(missing_ok=True)
                    raise CatalogueError(
                        f"failed to truncate archive {url!r}: {exc}"
                    ) from exc
                return

    # Both candidates failed.
    with contextlib.suppress(OSError):
        path.unlink(missing_ok=True)
    raise CatalogueError(
        f"SHA-256 mismatch for archive {url!r}: "
        f"expected {expected_sha256!r}, received {received!r}"
    )


# ---------------------------------------------------------------------------
# Safe archive extraction
# ---------------------------------------------------------------------------


def _validated_archive_destination(destination: Path, member_name: str) -> Path:
    """Return a confined destination for one POSIX-format tar member name."""
    if "\\" in member_name:
        raise CatalogueError(
            f"archive member {member_name!r} contains a Windows path separator; rejected"
        )

    member_path = PurePosixPath(member_name)
    if (
        member_path.is_absolute()
        or ".." in member_path.parts
        or (len(member_name) > 1 and member_name[1] == ":")
    ):
        raise CatalogueError(
            f"archive member {member_name!r} has unsafe path "
            f"(traversal or absolute); rejected"
        )

    try:
        resolved_destination = destination.resolve()
        resolved_member = (resolved_destination / Path(*member_path.parts)).resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        raise CatalogueError(
            f"archive member {member_name!r} cannot be resolved safely; rejected"
        ) from exc
    if not resolved_member.is_relative_to(resolved_destination):
        raise CatalogueError(
            f"archive member {member_name!r} resolves outside extraction root; rejected"
        )
    return resolved_member


def _safe_extract(archive_path: Path, dest: Path) -> None:
    """Extract a tar.gz archive to ``dest`` with per-member safety checks.

    Rejects: path traversal (``..``), absolute paths, symlinks, hard links,
    device files, FIFOs. Enforces member count and expanded-bytes limits.
    Cleans up ``dest`` on any violation.
    """
    try:
        with tarfile.open(archive_path, "r:gz") as tf:
            expanded_bytes = 0
            for member_count, member in enumerate(tf.getmembers(), start=1):
                if member_count > _MAX_MEMBERS:
                    raise CatalogueError(
                        f"archive contains more than {_MAX_MEMBERS} members; rejected"
                    )
                name = member.name
                _validated_archive_destination(dest, name)
                # Symlink check
                if member.issym():
                    raise CatalogueError(
                        f"archive member {name!r} is a symlink; rejected"
                    )
                # Hard link check
                if member.islnk():
                    raise CatalogueError(
                        f"archive member {name!r} is a hard link; rejected"
                    )
                # Device file / FIFO check
                if member.isdev() or member.isfifo():
                    raise CatalogueError(
                        f"archive member {name!r} is a device file or FIFO; rejected"
                    )
                expanded_bytes += member.size
                if expanded_bytes > _MAX_EXPANDED_BYTES:
                    raise CatalogueError(
                        f"archive expanded size exceeds {_MAX_EXPANDED_BYTES} byte limit; rejected"
                    )
                # Pass filter="fully_trusted" on Python 3.12+ to suppress the
                # DeprecationWarning: our per-member checks above already enforce
                # the safety invariants, so tarfile's built-in filter is redundant.
                if sys.version_info >= (3, 12):
                    tf.extract(member, path=dest, set_attrs=False, filter="fully_trusted")
                else:
                    tf.extract(member, path=dest, set_attrs=False)
    except CatalogueError:
        shutil.rmtree(str(dest), ignore_errors=True)
        raise
    except tarfile.TarError as exc:
        shutil.rmtree(str(dest), ignore_errors=True)
        raise CatalogueError(f"failed to extract archive: {exc}") from exc
    except OSError as exc:
        shutil.rmtree(str(dest), ignore_errors=True)
        raise CatalogueError(f"failed to extract archive: {exc}") from exc


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------


def fetch_catalogue_archive_with_provenance(
    source_uri: str, *, env: dict | None = None
) -> CatalogueArchiveResult:
    """Fetch and extract a catalogue archive, returning path and provenance.

    Returns a :class:`CatalogueArchiveResult` whose ``path`` is the extracted
    temp directory and whose remaining fields record the resolved artifact URL,
    the verified SHA-256, and the optional ``source_revision`` from the channel
    descriptor. The caller is responsible for cleanup of ``result.path`` on
    success. On any failure, temp directories are cleaned up before the
    ``CatalogueError`` is re-raised.

    ``env`` defaults to ``os.environ``; injectable for testing. Note: proxy
    settings are always read from ``os.environ`` by ``ProxyHandler()``, not
    from ``env``.
    """
    # Lazy import: catalogue_fetch imports credbroker; keeping it here means
    # importing agentbundle.https_catalogue does not trigger credbroker loading.
    from agentbundle.catalogue_fetch import open_fetch_session as _open_session

    if env is None:
        env = os.environ  # type: ignore[assignment]

    if source_uri.startswith("catalogue+https://"):
        channel_url = source_uri[len("catalogue+"):]

        dest: Path | None = None
        archive_path: Path | None = None
        try:
            with _open_session(channel_url, env=env) as session:
                raw = session.fetch_bytes(
                    channel_url,
                    max_bytes=_MAX_DESCRIPTOR_BYTES,
                    timeout=_HTTP_TIMEOUT,
                )
                descriptor = _parse_descriptor(raw)
                _check_client_version(descriptor.get("minimum_agentbundle_version"))
                artifact_url = _resolve_artifact_url(channel_url, descriptor["artifact"])
                archive_path = session.fetch_archive(
                    artifact_url,
                    max_bytes=_MAX_ARCHIVE_BYTES,
                    timeout=_HTTP_TIMEOUT,
                )
            is_jfrog = session.provider == "jfrog"
            if is_jfrog:
                _verify_jfrog_archive_sha256(
                    archive_path, descriptor["sha256"], artifact_url
                )
            else:
                _verify_archive_sha256(archive_path, descriptor["sha256"], artifact_url)
            dest = Path(tempfile.mkdtemp(prefix="agentbundle-"))
            _safe_extract(archive_path, dest)
            _raw_rev = descriptor.get("source_revision")
            return CatalogueArchiveResult(
                path=dest,
                artifact_uri=artifact_url,
                archive_sha256=descriptor["sha256"],
                source_revision=_raw_rev if isinstance(_raw_rev, str) else None,
            )
        except Exception:
            if dest is not None:
                shutil.rmtree(str(dest), ignore_errors=True)
            if archive_path is not None:
                with contextlib.suppress(OSError):
                    archive_path.unlink(missing_ok=True)
            raise

    elif source_uri.startswith("archive+https://"):
        archive_url_with_fragment = source_uri[len("archive+"):]
        parsed = urlsplit(archive_url_with_fragment)
        fragment = parsed.fragment
        if not fragment.startswith("sha256="):
            raise CatalogueError(
                "archive+https:// URL must have #sha256=<64hex> fragment"
            )
        expected_sha256 = fragment[len("sha256="):]
        # Strip fragment before session open: the fragment is never sent to a
        # server or passed into access resolution.
        archive_url = urlunsplit(parsed._replace(fragment=""))

        dest = None
        archive_path = None
        try:
            with _open_session(archive_url, env=env) as session:
                archive_path = session.fetch_archive(
                    archive_url,
                    max_bytes=_MAX_ARCHIVE_BYTES,
                    timeout=_HTTP_TIMEOUT,
                )
            is_jfrog = session.provider == "jfrog"
            if is_jfrog:
                _verify_jfrog_archive_sha256(archive_path, expected_sha256, archive_url)
            else:
                _verify_archive_sha256(archive_path, expected_sha256, archive_url)
            dest = Path(tempfile.mkdtemp(prefix="agentbundle-"))
            _safe_extract(archive_path, dest)
            return CatalogueArchiveResult(
                path=dest,
                artifact_uri=archive_url,
                archive_sha256=expected_sha256,
                source_revision=None,
            )
        except Exception:
            if dest is not None:
                shutil.rmtree(str(dest), ignore_errors=True)
            if archive_path is not None:
                with contextlib.suppress(OSError):
                    archive_path.unlink(missing_ok=True)
            raise

    else:
        raise CatalogueError(
            f"https_catalogue: unsupported scheme in {source_uri!r}"
        )


def fetch_catalogue_archive(source_uri: str, *, env: dict | None = None) -> Path:
    """Backward-compatible wrapper; returns only the extracted archive path.

    Prefer :func:`fetch_catalogue_archive_with_provenance` when provenance
    metadata (artifact URI, SHA-256, source revision) is needed.
    """
    return fetch_catalogue_archive_with_provenance(source_uri, env=env).path
