"""Default catalogue-source resolution for ``install`` / ``upgrade`` (RFC-0046).

When the ``catalogue`` positional is omitted, the install/upgrade handlers
resolve a default source through a five-layer, trusted-by-construction,
first-match-wins chain (ADR-0036):

  1. the explicit ``catalogue`` arg — passed through verbatim;
  2. the user ``[settings].source`` config value;
  3. package-shipped org Artifactory bootstrap (RFC-0072 D2);
  4. editable-install detection via PEP 610 ``direct_url.json``;
  5. the packaged ``_data/install-defaults.toml`` default.

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

import re as _re

from agentbundle.catalogue import CatalogueError

_GIT_HTTPS_PREFIX = "git+https://"
_CATALOGUE_HTTPS_PREFIX = "catalogue+https://"
_ARCHIVE_HTTPS_PREFIX = "archive+https://"
_SHA256_FRAGMENT_RE = _re.compile(r"^sha256=[0-9a-f]{64}$")
# A Windows drive path (``C:\repo`` / ``C:/repo``): a single drive letter, a
# colon, then a separator. Checked *before* the urlsplit scheme test because
# ``urlsplit("C:/x").scheme`` is ``"c"`` and would otherwise read as a URL.
_WIN_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")
# Segment grammar for org-bootstrap path components (repository, bundle, channel).
_ORG_SEGMENT_RE = re.compile(r"[A-Za-z0-9._-]+")

_MARKER_DIR = "packs"
_MARKER_FILE = (".claude-plugin", "marketplace.json")

# The exact substring the spec pins for the all-layers-empty error. Names the
# real surface: the catalogue is a trailing positional argument, not a
# `--catalogue` flag (no such flag exists), so the recovery text must not send
# the user to one.
_NO_SOURCE_MSG = (
    "no catalogue source: pass a catalogue argument, run 'agentbundle config "
    "set source …', or pip install -e the catalogue"
)

# Sentinel: distinguishes "caller did not pass a distribution" (load it
# lazily) from "caller passed None" (no distribution — skip layer 4).
_UNSET: object = object()


# ---------------------------------------------------------------------------
# Validation gate (layers 2 and 5)
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
    """The scheme/marker gate applied to layer-2 and layer-5 sources.

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
    if value.startswith(_CATALOGUE_HTTPS_PREFIX):
        parsed = urlsplit(value)
        if "@" in parsed.netloc:
            return False
        return True
    if value.startswith(_ARCHIVE_HTTPS_PREFIX):
        parsed = urlsplit(value)
        if "@" in parsed.netloc:
            return False
        if not _SHA256_FRAGMENT_RE.fullmatch(parsed.fragment):
            return False
        return True
    if _WIN_DRIVE_RE.match(value):
        return _local_path_has_markers(value)
    if urlsplit(value).scheme:
        return False
    return _local_path_has_markers(value)


# ---------------------------------------------------------------------------
# Layer 3 — org Artifactory bootstrap (RFC-0072 D2)
# ---------------------------------------------------------------------------


def _source_from_org_bootstrap(text: str, *, config_path: str) -> str | None:
    """Parse ``[organization.artifactory]`` from ``install-defaults.toml`` text.

    Returns ``None`` when the bootstrap is disabled: absent table, absent or
    ``false`` ``enabled`` key, or unparseable TOML (the file cannot reveal
    ``enabled``, so fall-through is the only safe choice — AC2b).

    When ``enabled = true`` (TOML boolean), applies all validation rules before
    constructing the URL. On any validation failure raises ``CatalogueError``
    naming the malformed field and the ``config_path`` — fail-closed, never
    falls through to Layer 4.

    Returns a ``catalogue+https://…`` URI string when all fields are valid.
    """
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return None

    # Two-step isinstance-guarded nesting access — avoids AttributeError when
    # an intermediate key holds a non-dict TOML value (e.g. `organization = "typo"`).
    org = data.get("organization")
    if not isinstance(org, dict):
        return None
    org_block = org.get("artifactory")
    if not isinstance(org_block, dict):
        return None

    enabled = org_block.get("enabled")
    if enabled is None or enabled is False:
        return None
    if enabled is not True:
        raise CatalogueError(
            f"organization.artifactory.enabled: must be a boolean (true/false) "
            f"in {config_path}"
        )

    # --- enabled is True: fail-closed from here on ---

    # Validate base-url
    base_url = org_block.get("base-url")
    if base_url is None:
        raise CatalogueError(
            f"organization.artifactory.base-url: required field missing in {config_path}"
        )
    if not isinstance(base_url, str) or not base_url.strip():
        raise CatalogueError(
            f"organization.artifactory.base-url: must be a non-empty string "
            f"in {config_path}"
        )
    # Case-sensitive prefix check before urlsplit so uppercase schemes are
    # rejected here, guaranteeing the constructed URL starts with lower-case
    # `catalogue+https://` as required by _is_valid_source.
    if not base_url.startswith("https://"):
        raise CatalogueError(
            f"organization.artifactory.base-url: must start with 'https://' "
            f"in {config_path}"
        )
    parsed = urlsplit(base_url)
    if not parsed.netloc:
        raise CatalogueError(
            f"organization.artifactory.base-url: netloc must not be empty "
            f"in {config_path}"
        )
    if "@" in parsed.netloc:
        # Do NOT include the raw base_url in the message — it may contain credentials.
        raise CatalogueError(
            f"organization.artifactory.base-url: netloc must not contain '@' "
            f"in {config_path}"
        )
    if parsed.query:
        raise CatalogueError(
            f"organization.artifactory.base-url: must not contain a query string "
            f"in {config_path}"
        )
    if parsed.fragment:
        raise CatalogueError(
            f"organization.artifactory.base-url: must not contain a fragment "
            f"in {config_path}"
        )

    # Normalize trailing slash before joining path segments.
    base_url = base_url.rstrip("/")

    # Validate repository, bundle, channel
    segments: dict[str, str] = {}
    for fname in ("repository", "bundle", "channel"):
        val = org_block.get(fname)
        if val is None:
            raise CatalogueError(
                f"organization.artifactory.{fname}: required field missing "
                f"in {config_path}"
            )
        if not isinstance(val, str) or not val.strip():
            raise CatalogueError(
                f"organization.artifactory.{fname}: must be a non-empty string "
                f"in {config_path}"
            )
        # Defense-in-depth: explicit reject before regex (both `.` chars are
        # individually valid but the combination is a path-traversal pattern).
        if val == "..":
            raise CatalogueError(
                f"organization.artifactory.{fname}: must not be '..' "
                f"in {config_path}"
            )
        if not _ORG_SEGMENT_RE.fullmatch(val):
            raise CatalogueError(
                f"organization.artifactory.{fname}: contains invalid characters "
                f"(expected [A-Za-z0-9._-]+) in {config_path}"
            )
        segments[fname] = val

    return (
        f"catalogue+{base_url}"
        f"/{segments['repository']}/catalogues/{segments['bundle']}"
        f"/channels/{segments['channel']}.json"
    )


def read_org_bootstrap(
    read_text: "Callable[[], tuple[str, str] | None] | None" = None,
) -> str | None:
    """Return the org Artifactory bootstrap source URI, or ``None``.

    When ``read_text`` is ``None`` (production path): reads the packaged
    ``_data/install-defaults.toml`` via ``importlib.resources``; absorbs
    ``(FileNotFoundError, ModuleNotFoundError, OSError)`` as ``None``; passes
    ``config_path=str(resource)`` for error messages.

    When ``read_text`` is provided (test injection path): calls it; if it
    returns ``None``, returns ``None``; otherwise unpacks ``(text, config_path)``
    and delegates to ``_source_from_org_bootstrap``.

    Returns ``None`` when the bootstrap is disabled.  Raises ``CatalogueError``
    when ``enabled = true`` and any field is malformed (fail-closed).
    """
    if read_text is not None:
        result = read_text()
        if result is None:
            return None
        text, config_path = result
        return _source_from_org_bootstrap(text, config_path=config_path)

    # Production path: read from the packaged resource.
    try:
        from importlib.resources import files

        resource = files("agentbundle").joinpath("_data/install-defaults.toml")
        if not resource.is_file():
            return None
        text = resource.read_text(encoding="utf-8")
        config_path = str(resource)
    except (FileNotFoundError, ModuleNotFoundError, OSError):
        return None
    return _source_from_org_bootstrap(text, config_path=config_path)


# ---------------------------------------------------------------------------
# Layer 4 — editable-install detection
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
# Layer 5 — packaged default
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
    ``None`` (no layer-5 default) — the private-fork pattern.
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


def _preferred_adapter_from_install_defaults(text: str) -> str | None:
    """Parse ``[organization].preferred_adapter`` from ``install-defaults.toml`` text.

    Returns ``None`` for malformed TOML, a missing ``[organization]`` table, or an
    absent/blank ``preferred_adapter`` (the private-fork pattern).  Validation
    against the shipped adapter contract is left to the caller.
    """
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return None
    organization = data.get("organization")
    if not isinstance(organization, dict):
        return None
    raw = organization.get("preferred_adapter")
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw


def read_packaged_preferred_adapter() -> str | None:
    """Return the validated ``[organization].preferred_adapter`` from the packaged
    ``_data/install-defaults.toml``, or ``None``.

    An absent file, an absent ``[organization]`` table, or an absent/blank
    ``preferred_adapter`` all yield ``None`` (the private-fork pattern — silent
    fall-through, no error).

    A present but invalid value (not in the shipped adapter contract) raises
    :class:`~agentbundle.catalogue.CatalogueError` naming the invalid value and
    the admissible set — fail-closed so a misconfigured org fork is diagnosed at
    install time rather than silently falling through to auto-probe.
    """
    try:
        from importlib.resources import files

        resource = files("agentbundle").joinpath("_data/install-defaults.toml")
        if not resource.is_file():
            return None
        text = resource.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, OSError):
        return None
    raw = _preferred_adapter_from_install_defaults(text)
    if raw is None:
        return None
    from agentbundle.scope import shipped_adapters_from_contract
    shipped = shipped_adapters_from_contract()
    if raw not in shipped:
        raise CatalogueError(
            f"install-defaults.toml: [organization].preferred_adapter {raw!r} is "
            f"not in the shipped adapter contract. Admissible: {sorted(shipped)}. "
            f"Blank the value to disable the org hint."
        )
    return raw


def _load_distribution() -> object | None:
    """Return the ``agentbundle`` distribution, **preferring** one that carries
    a ``direct_url.json`` (the editable record).

    A stale source-tree ``agentbundle.egg-info`` can sit on ``sys.path`` beside
    the venv's ``.dist-info`` after an editable install; a plain
    ``metadata.distribution("agentbundle")`` may then return the egg-info
    (which has no ``direct_url.json``), silently defeating editable detection —
    exactly the gateway-bound-fork case layer 4 exists for. Scanning and
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
    read_org: Callable[[], str | None] | None = None,
    stream: TextIO | None = None,
) -> str:
    """Resolve the catalogue source through the five-layer chain.

    First-match-wins, highest-first: explicit arg (verbatim, unvalidated —
    today's behaviour) › validated ``config_source`` › org Artifactory
    bootstrap (RFC-0072 D2) › editable detection › validated packaged default.
    Raises ``CatalogueError`` naming all recovery paths when no layer yields a
    source. Writes nothing on any path.

    Layer 3 (org Artifactory bootstrap) raises ``CatalogueError`` fail-closed
    when ``enabled = true`` and any field is malformed — it does not fall
    through to Layer 4.

    Pure over its injected environment (``config_source``, ``dist``,
    ``read_packaged``, ``read_org``) so the precedence and validation logic is
    unit-testable without touching the real filesystem or installed metadata.
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

    # Layer 3 — org Artifactory bootstrap (RFC-0072 D2).
    if read_org is None:
        read_org = read_org_bootstrap
    org = read_org()  # None when disabled; raises CatalogueError on fail-closed
    if org is not None:
        return org

    # Layer 4 — editable detection.
    if dist is _UNSET:
        dist = _load_distribution()
    editable = _detect_editable_source(dist, stream=stream)
    if editable is not None:
        return editable

    # Layer 5 — packaged default, validated.
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
