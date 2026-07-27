"""HTTPS catalogue and archive fetcher for enterprise distribution (RFC-0072).

Implements ``catalogue+https://`` and ``archive+https://`` source URI schemes:

- ``catalogue+https://``: fetch a JSON channel descriptor, resolve the artifact
  URL, stream and SHA-256-verify the archive, extract it to a temp directory.
- ``archive+https://``: fetch a pinned archive URL directly; the ``#sha256=``
  fragment supplies the expected digest.

Security invariants:
- Bearer token read-only from ``AGENTBUNDLE_HTTP_BEARER_TOKEN`` env var.
  Never logged, printed, or forwarded to a different origin.
- Same-origin redirect enforcement: the originally-requested URL is the anchor.
  Cross-origin redirects are rejected before any outbound request is sent.
- HTTPS only — no ``HTTPHandler`` in the opener; HTTP redirects rejected.
- Archive extracted member-by-member; never ``extractall()`` without per-member
  safety checks. Path traversal, absolute paths, symlinks, hard links, and
  special files are all rejected.
- SHA-256 verified before extraction; temp dir cleaned up on any failure.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlunsplit, urlsplit

from agentbundle.catalogue import CatalogueError

# ---------------------------------------------------------------------------
# Named safety limits (RFC-0072; all enforced regardless of Content-Length)
# ---------------------------------------------------------------------------

_MAX_DESCRIPTOR_BYTES = 1 * 1024 * 1024          # 1 MiB
_MAX_ARCHIVE_BYTES = 256 * 1024 * 1024            # 256 MiB
_MAX_MEMBERS = 20_000
_MAX_EXPANDED_BYTES = 1 * 1024 * 1024 * 1024      # 1 GiB
_HTTP_TIMEOUT = 30                                 # seconds

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

_DESCRIPTOR_REQUIRED_FIELDS = ("schema", "kind", "bundle", "channel", "release", "artifact", "sha256")


# ---------------------------------------------------------------------------
# Redirect handler — rejects cross-origin, HTTP, and user-info redirects
# ---------------------------------------------------------------------------


class _OriginLockingRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Custom redirect handler that enforces same-origin redirect policy.

    The same-origin anchor is the ORIGINALLY-REQUESTED URL (captured before
    ``urlopen`` is called), not the post-redirect final URL. Cross-origin
    redirects are rejected before any request is sent to the redirect target.
    """

    def __init__(self, original_url: str) -> None:
        self._original = urlsplit(original_url)

    def _origin(self, parsed) -> tuple:
        return (
            parsed.scheme.lower(),
            (parsed.hostname or "").lower(),
            parsed.port,
        )

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        parsed_new = urlsplit(newurl)
        # Reject HTTP redirects (HTTPS only)
        if parsed_new.scheme.lower() != "https":
            raise CatalogueError(
                f"HTTPS-only: redirect to non-HTTPS URL rejected: {parsed_new.scheme}://..."
            )
        # Reject user-info in redirect URL
        if "@" in parsed_new.netloc:
            raise CatalogueError("redirect contains user-info in netloc; rejected")
        # Reject cross-origin (compare against ORIGINALLY requested URL)
        if self._origin(parsed_new) != self._origin(self._original):
            raise CatalogueError(
                "cross-origin redirect rejected (bearer token not forwarded)"
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


# ---------------------------------------------------------------------------
# Opener construction
# ---------------------------------------------------------------------------


def _build_opener(token: str | None, original_url: str) -> urllib.request.OpenerDirector:
    """Build a custom opener with proxy support, redirect enforcement, HTTPS only.

    - ``ProxyHandler()`` (no args) reads HTTPS_PROXY / NO_PROXY from
      ``os.environ`` automatically via ``urllib.request.getproxies()``.
    - No ``HTTPHandler`` — HTTP is disabled in the opener.
    - ``_OriginLockingRedirectHandler`` rejects cross-origin redirects before
      they are followed; same-origin redirects forward ``Authorization`` intact.
    - Bearer token is added as ``Authorization: Bearer <token>`` when present.
    """
    redirect_handler = _OriginLockingRedirectHandler(original_url)
    proxy_handler = urllib.request.ProxyHandler()
    https_handler = urllib.request.HTTPSHandler()

    opener = urllib.request.OpenerDirector()
    opener.addheaders = []  # prevent default User-Agent from leaking in some paths

    opener.add_handler(proxy_handler)
    opener.add_handler(redirect_handler)
    opener.add_handler(https_handler)
    opener.add_handler(urllib.request.UnknownHandler())

    if token:
        # Store token for use in _fetch_bytes_limited / _stream_and_verify
        # via a custom opener attribute; NOT logged anywhere.
        opener._bearer_token = token  # type: ignore[attr-defined]
    else:
        opener._bearer_token = None  # type: ignore[attr-defined]

    return opener


def _make_request(url: str, opener: urllib.request.OpenerDirector) -> urllib.request.Request:
    """Build a Request, adding Authorization header if the opener has a token."""
    req = urllib.request.Request(url)
    token = getattr(opener, "_bearer_token", None)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    return req


# ---------------------------------------------------------------------------
# HTTP fetch helpers
# ---------------------------------------------------------------------------


def _fetch_bytes_limited(
    url: str,
    opener: urllib.request.OpenerDirector,
    max_bytes: int,
    timeout: int,
) -> bytes:
    """Stream a response, enforcing ``max_bytes`` regardless of Content-Length.

    Raises ``CatalogueError`` if the byte limit is exceeded before the response
    body is consumed.
    """
    req = _make_request(url, opener)
    try:
        with opener.open(req, timeout=timeout) as resp:
            chunks = []
            total = 0
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise CatalogueError(
                        f"response from {url!r} exceeds {max_bytes} byte limit"
                    )
                chunks.append(chunk)
            return b"".join(chunks)
    except CatalogueError:
        raise
    except urllib.error.URLError as exc:
        raise CatalogueError(f"failed to fetch {url!r}: {exc.reason}") from exc
    except OSError as exc:
        raise CatalogueError(f"failed to fetch {url!r}: {exc}") from exc


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
            f"channel descriptor sha256 must be exactly 64 lowercase hex characters; got {sha256_val!r}"
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
            f"cross-origin artifact URL rejected: artifact origin does not match "
            f"channel descriptor origin (scheme+host+port must all match)"
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
# Archive streaming + SHA-256 verification
# ---------------------------------------------------------------------------


def _stream_and_verify(
    url: str,
    expected_sha256: str,
    opener: urllib.request.OpenerDirector,
    timeout: int,
) -> Path:
    """Stream archive to a temp file, compute SHA-256, raise on mismatch.

    Returns the path to the verified temp file. The caller is responsible for
    cleanup on success; this function cleans up on its own failures.
    """
    tmp_fd, tmp_path_str = tempfile.mkstemp(prefix="agentbundle-archive-", suffix=".tar.gz")
    tmp_path = Path(tmp_path_str)
    try:
        req = _make_request(url, opener)
        hasher = hashlib.sha256()
        total = 0
        try:
            with opener.open(req, timeout=timeout) as resp:
                with os.fdopen(tmp_fd, "wb") as tmp_file:
                    tmp_fd = -1  # fd now owned by tmp_file
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > _MAX_ARCHIVE_BYTES:
                            raise CatalogueError(
                                f"archive from {url!r} exceeds {_MAX_ARCHIVE_BYTES} byte limit"
                            )
                        hasher.update(chunk)
                        tmp_file.write(chunk)
        except CatalogueError:
            raise
        except urllib.error.URLError as exc:
            raise CatalogueError(f"failed to fetch archive {url!r}: {exc.reason}") from exc
        except OSError as exc:
            raise CatalogueError(f"failed to fetch archive {url!r}: {exc}") from exc

        received = hasher.hexdigest()
        if received != expected_sha256:
            raise CatalogueError(
                f"SHA-256 mismatch for archive {url!r}: "
                f"expected {expected_sha256!r}, received {received!r}"
            )
        return tmp_path
    except Exception:
        # Close the fd if it was never handed to fdopen
        if tmp_fd >= 0:
            try:
                os.close(tmp_fd)
            except OSError:
                pass
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Safe archive extraction
# ---------------------------------------------------------------------------


def _safe_extract(archive_path: Path, dest: Path) -> None:
    """Extract a tar.gz archive to ``dest`` with per-member safety checks.

    Rejects: path traversal (``..``), absolute paths, symlinks, hard links,
    device files, FIFOs. Enforces member count and expanded-bytes limits.
    Cleans up ``dest`` on any violation.
    """
    try:
        with tarfile.open(archive_path, "r:gz") as tf:
            member_count = 0
            expanded_bytes = 0
            for member in tf.getmembers():
                member_count += 1
                if member_count > _MAX_MEMBERS:
                    raise CatalogueError(
                        f"archive contains more than {_MAX_MEMBERS} members; rejected"
                    )
                # Path traversal check
                name = member.name
                if ".." in name.split("/") or name.startswith("/"):
                    raise CatalogueError(
                        f"archive member {name!r} has unsafe path (traversal or absolute); rejected"
                    )
                if os.path.isabs(name):
                    raise CatalogueError(
                        f"archive member {name!r} has absolute path; rejected"
                    )
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


def fetch_catalogue_archive(source_uri: str, *, env: dict | None = None) -> Path:
    """Fetch and extract a catalogue archive from a ``catalogue+https://`` or
    ``archive+https://`` source URI.

    Returns the path to the extracted temp directory. The caller is responsible
    for cleanup on success. On any failure, temp directories are cleaned up
    before the ``CatalogueError`` is re-raised.

    ``env`` defaults to ``os.environ``; injectable for testing (bearer token
    lookup). Note: proxy settings are always read from ``os.environ`` by
    ``ProxyHandler()``, not from ``env``.
    """
    if env is None:
        env = os.environ
    token = env.get("AGENTBUNDLE_HTTP_BEARER_TOKEN")

    if source_uri.startswith("catalogue+https://"):
        # Strip the "catalogue+" prefix to get the actual HTTPS URL
        channel_url = source_uri[len("catalogue+"):]
        opener = _build_opener(token, channel_url)

        dest = None
        archive_path = None
        try:
            raw = _fetch_bytes_limited(channel_url, opener, _MAX_DESCRIPTOR_BYTES, _HTTP_TIMEOUT)
            descriptor = _parse_descriptor(raw)
            _check_client_version(descriptor.get("minimum_agentbundle_version"))
            artifact_url = _resolve_artifact_url(channel_url, descriptor["artifact"])
            archive_path = _stream_and_verify(artifact_url, descriptor["sha256"], opener, _HTTP_TIMEOUT)
            dest = Path(tempfile.mkdtemp(prefix="agentbundle-"))
            _safe_extract(archive_path, dest)
            return dest
        except Exception:
            if dest is not None:
                shutil.rmtree(str(dest), ignore_errors=True)
            if archive_path is not None:
                try:
                    archive_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise

    elif source_uri.startswith("archive+https://"):
        # Strip "archive+" prefix, extract sha256 from fragment
        archive_url_with_fragment = source_uri[len("archive+"):]
        parsed = urlsplit(archive_url_with_fragment)
        fragment = parsed.fragment
        if not fragment.startswith("sha256="):
            raise CatalogueError(
                "archive+https:// URL must have #sha256=<64hex> fragment"
            )
        expected_sha256 = fragment[len("sha256="):]
        # Remove fragment from URL for actual request
        archive_url = urlunsplit(parsed._replace(fragment=""))
        opener = _build_opener(token, archive_url)

        dest = None
        archive_path = None
        try:
            archive_path = _stream_and_verify(archive_url, expected_sha256, opener, _HTTP_TIMEOUT)
            dest = Path(tempfile.mkdtemp(prefix="agentbundle-"))
            _safe_extract(archive_path, dest)
            return dest
        except Exception:
            if dest is not None:
                shutil.rmtree(str(dest), ignore_errors=True)
            if archive_path is not None:
                try:
                    archive_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise

    else:
        raise CatalogueError(
            f"https_catalogue: unsupported scheme in {source_uri!r}"
        )
