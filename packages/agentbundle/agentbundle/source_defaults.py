"""Default catalogue-source resolution for ``install`` / ``upgrade`` (RFC-0046).

When the ``catalogue`` positional is omitted, the install/upgrade handlers
resolve a default source through a four-layer, trusted-by-construction,
first-match-wins chain (ADR-0036):

  1. the explicit ``catalogue`` arg — passed through verbatim (layer 1);
  2. the user ``[settings].source`` config value (layer 2);
  3. editable-install detection via PEP 610 ``direct_url.json`` (layer 3);
  4. the packaged ``_data/install-defaults.toml`` default (layer 4).

``resolve_catalogue`` (``catalogue.py``) stays a thin fetcher with no
path/marker validation; **all** validation lives here. Resolution is
stateless — it never writes config, never falls back to ``.``/cwd, and never
consults a repo-committed source. See
``docs/specs/convenient-install-defaults/spec.md``.
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Callable, TextIO
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname

from agentbundle.catalogue import CatalogueError

_GIT_HTTPS_PREFIX = "git+https://"
# A Windows drive path (``C:\repo`` / ``C:/repo``): a single drive letter, a
# colon, then a separator. Checked *before* the urlsplit scheme test because
# ``urlsplit("C:/x").scheme`` is ``"c"`` and would otherwise read as a URL.
_WIN_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")

_MARKER_DIR = "packs"
_MARKER_FILE = (".claude-plugin", "marketplace.json")

# The exact substring the spec pins for the all-layers-empty error.
_NO_SOURCE_MSG = (
    "no catalogue source: pass --catalogue, run 'agentbundle config set "
    "source …', or pip install -e the catalogue"
)

# Sentinel: distinguishes "caller did not pass a distribution" (load it
# lazily) from "caller passed None" (no distribution — skip layer 3).
_UNSET: object = object()


# ---------------------------------------------------------------------------
# Validation gate (layers 2 and 4)
# ---------------------------------------------------------------------------


def _has_catalogue_markers(root: Path) -> bool:
    """True iff *root* holds both catalogue markers (``packs/`` +
    ``.claude-plugin/marketplace.json``)."""
    return (root / _MARKER_DIR).is_dir() and (
        root / _MARKER_FILE[0] / _MARKER_FILE[1]
    ).is_file()


def _local_path_has_markers(value: str) -> bool:
    try:
        root = Path(value).resolve()
    except OSError:
        return False
    return _has_catalogue_markers(root)


def _is_valid_source(value: str) -> bool:
    """The scheme/marker gate applied to layer-2 and layer-4 sources.

    Exact allowlist discriminator (spec validation AC), in order:
      1. literal ``git+https://`` prefix (case-sensitive, matching
         ``catalogue.py``'s ``startswith`` sink) → accept;
      2. a Windows drive path (``^[A-Za-z]:[\\/]``) → local-path branch;
      3. any non-empty ``urlsplit`` scheme (``file://``, ``file:/``,
         ``http://``, ``git+ssh://``, mis-cased ``GIT+HTTPS://``) → reject;
      4. else (schemeless: ``/abs``, ``./rel``, ``rel``) → local-path branch.

    A local-path source is accepted iff both markers are present at its
    ``Path.resolve()``'d location.
    """
    if not value:
        return False
    if value.startswith(_GIT_HTTPS_PREFIX):
        return True
    if _WIN_DRIVE_RE.match(value):
        return _local_path_has_markers(value)
    if urlsplit(value).scheme:
        return False
    return _local_path_has_markers(value)


# ---------------------------------------------------------------------------
# Layer 3 — editable-install detection
# ---------------------------------------------------------------------------


def _enclosing_git_root(start: Path) -> Path | None:
    """Nearest ancestor (inclusive) of *start* containing a ``.git`` entry —
    a **file** (worktree / submodule gitdir pointer) or a directory.

    *start* must already be ``Path.resolve()``'d; ancestors of a resolved path
    are themselves canonical, so the returned root is canonical too.
    """
    cur = start
    while True:
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent


def _ascend_inclusive(start: Path, stop: Path):
    """Yield *start*, its parent, … up to and including *stop*.

    *stop* is an ancestor-or-equal of *start* (it is the enclosing ``.git``
    root), so every yielded candidate is an ancestor-or-equal of *start* and a
    descendant-or-equal of *stop* — the closed interval that confines the walk
    to inside the clone.
    """
    cur = start
    while True:
        yield cur
        if cur == stop or cur.parent == cur:
            return
        cur = cur.parent


def _detect_editable_source(dist: object, *, stream: TextIO | None = None) -> str | None:
    """Resolve the catalogue root from an editable install, or ``None``.

    Reads PEP 610 ``direct_url.json`` from *dist*, activates only when
    ``dir_info.editable is True``, parses the ``file://`` URL (rejecting a
    non-empty/non-localhost host), canonicalizes it, and walks **up** to the
    first ancestor (bounded by the enclosing ``.git`` root, inclusive) holding
    both catalogue markers. Emits a one-line stderr diagnostic and returns
    ``None`` when editable is detected but no catalogue root is found.
    """
    if stream is None:
        stream = sys.stderr
    if dist is None:
        return None
    try:
        raw = dist.read_text("direct_url.json")  # type: ignore[attr-defined]
    except Exception:
        return None
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    dir_info = data.get("dir_info")
    if not isinstance(dir_info, dict) or dir_info.get("editable") is not True:
        return None
    url = data.get("url")
    if not isinstance(url, str):
        return None
    parts = urlsplit(url)
    if parts.scheme != "file":
        return None
    if parts.netloc not in ("", "localhost"):
        return None
    pkg_path = Path(url2pathname(unquote(parts.path)))
    try:
        pkg_root = pkg_path.resolve(strict=True)
    except OSError:
        return None

    git_root = _enclosing_git_root(pkg_root)
    if git_root is None:
        print(
            "agentbundle: editable install detected but no enclosing .git "
            "repository found; deferring to packaged default.",
            file=stream,
        )
        return None

    for candidate in _ascend_inclusive(pkg_root, git_root):
        if _has_catalogue_markers(candidate):
            return str(candidate)

    print(
        f"agentbundle: editable install detected at {pkg_root} but no catalogue "
        f"root (packs/ + .claude-plugin/marketplace.json) found at or above it "
        f"within the repository {git_root}; deferring to packaged default.",
        file=stream,
    )
    return None


# ---------------------------------------------------------------------------
# Layer 4 — packaged default
# ---------------------------------------------------------------------------


def _source_from_install_defaults(text: str) -> str | None:
    """Parse ``[defaults].source`` from ``install-defaults.toml`` *text*.

    Returns ``None`` for malformed TOML, a missing ``[defaults]`` table, or an
    absent/blank ``source`` (the private-fork pattern).
    """
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return None
    defaults = data.get("defaults")
    if not isinstance(defaults, dict):
        return None
    source = defaults.get("source")
    if not isinstance(source, str) or not source.strip():
        return None
    return source


def read_packaged_default() -> str | None:
    """Return ``[defaults].source`` from the packaged
    ``_data/install-defaults.toml``, or ``None``.

    An absent file, an empty/blanked ``source``, or malformed TOML all yield
    ``None`` (no layer-4 default) — the private-fork pattern.
    """
    try:
        from importlib.resources import files

        resource = files("agentbundle").joinpath("_data/install-defaults.toml")
        if not resource.is_file():
            return None
        text = resource.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, OSError):
        return None
    return _source_from_install_defaults(text)


def _load_distribution() -> object | None:
    """Return the ``agentbundle`` distribution, **preferring** one that carries
    a ``direct_url.json`` (the editable record).

    A stale source-tree ``agentbundle.egg-info`` can sit on ``sys.path`` beside
    the venv's ``.dist-info`` after an editable install; a plain
    ``metadata.distribution("agentbundle")`` may then return the egg-info
    (which has no ``direct_url.json``), silently defeating editable detection —
    exactly the gateway-bound-fork case layer 3 exists for. Scanning and
    preferring the record-bearing distribution makes detection robust to that
    shadowing.
    """
    import importlib.metadata as _md

    def _norm(name: str) -> str:
        return re.sub(r"[-_.]+", "-", name).lower()

    fallback = None
    for dist in _md.distributions():
        # A corrupt dist-info may lack a Name (KeyError) or be unreadable
        # (OSError); skip just that entry rather than aborting the scan.
        try:
            name = dist.metadata["Name"]
            has_record = bool(dist.read_text("direct_url.json"))
        except (KeyError, OSError):
            continue
        if not name or _norm(name) != "agentbundle":
            continue
        if has_record:
            return dist
        if fallback is None:
            fallback = dist
    if fallback is not None:
        return fallback
    try:
        return _md.distribution("agentbundle")
    except _md.PackageNotFoundError:
        return None


# ---------------------------------------------------------------------------
# Composer
# ---------------------------------------------------------------------------


def resolve_default_source(
    explicit: str | None,
    *,
    config_source: str | None = None,
    dist: object = _UNSET,
    read_packaged: Callable[[], str | None] | None = None,
    stream: TextIO | None = None,
) -> str:
    """Resolve the catalogue source through the four-layer chain.

    First-match-wins, highest-first: explicit arg (verbatim, unvalidated —
    today's behaviour) › validated ``config_source`` › editable detection ›
    validated packaged default. Raises ``CatalogueError`` naming all recovery
    paths when no layer yields a source. Writes nothing on any path.

    Pure over its injected environment (``config_source``, ``dist``,
    ``read_packaged``) so the precedence and validation logic is unit-testable
    without touching the real filesystem or installed metadata.
    """
    if stream is None:
        stream = sys.stderr
    # Layer 1 — explicit positional: pass through verbatim, no validation
    # (identical to today; the default chain runs only when omitted).
    if explicit is not None:
        return explicit

    # Layer 2 — user [settings].source, validated.
    if config_source is not None:
        if _is_valid_source(config_source):
            return config_source
        print(
            f"agentbundle: ignoring invalid [settings].source ({config_source!r}); "
            f"clear it with 'agentbundle config unset source'.",
            file=stream,
        )

    # Layer 3 — editable detection.
    if dist is _UNSET:
        dist = _load_distribution()
    editable = _detect_editable_source(dist, stream=stream)
    if editable is not None:
        return editable

    # Layer 4 — packaged default, validated.
    if read_packaged is None:
        read_packaged = read_packaged_default
    packaged = read_packaged()
    if packaged is not None and _is_valid_source(packaged):
        return packaged

    raise CatalogueError(
        _NO_SOURCE_MSG
        + ". If you previously ran 'config set source', clear a stale value "
        "with 'agentbundle config unset source'."
    )
