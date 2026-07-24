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

No subprocess calls anywhere in this module.
"""

from __future__ import annotations

import atexit
import re
import shutil
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

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

    # Dispatch new HTTPS catalogue schemes (RFC-0072)
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
    inner = _find_inner_dir(tmpdir)
    return inner


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


def _fetch_and_extract(url: str, dest: Path) -> None:
    try:
        # B310: constant github.com archive base assembled from parsed owner/repo/ref.
        with urllib.request.urlopen(url) as resp:  # nosec B310
            with tarfile.open(fileobj=resp, mode="r|gz") as tf:
                # filter="data" rejects unsafe members (absolute paths, ..
                # links, devices, setuid bits) — Python 3.12+ default but
                # explicit for 3.11 compatibility and to silence the 3.14
                # DeprecationWarning. Path-jail is belt; this is braces.
                tf.extractall(path=dest, filter="data")
    except urllib.error.URLError as exc:
        raise CatalogueError(
            f"Failed to fetch catalogue archive: {url} — {exc.reason}"
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
