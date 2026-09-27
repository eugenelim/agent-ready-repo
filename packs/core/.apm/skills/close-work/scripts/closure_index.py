#!/usr/bin/env python3
"""Per-decision in-memory descendant index for the closure eligibility check.

Module-private construction: only the closure check's entry point may call
``_build_descendant_closure``. A test enumerates its callers (AC-0026, T4).

**Nothing in this module writes to disk or to environment variables.** The
returned dict is built inside the caller's frame and garbage-collected when
that frame ends (AC-0023). No state persists across decisions (AC-0021).

**Each artifact file is opened at most once per decision** (AC-0024). A
visited set tracks physically opened paths; a field cache stores preamble
fields so that subsequent membership checks use the cache rather than
re-reading the file. The diamond case — one file encountered as a candidate
in two separate collection scans — is handled by returning cached fields on
the second encounter without calling the reader.

**Discovery is driven exclusively by the ``Decomposed:`` terminus at each
level** (AC-0025). A terminus names one of three collections: ``children``
maps to the intents directory, ``brief`` maps to the briefs directory (plus
the specs directory for that brief's specs), and ``spec`` maps to the specs
directory. No other directory is enumerated. A collection-directory cache
ensures dir_lister is called at most once per directory per decision.

**Reads per decision are bounded by the summed size of the named
collections** (AC-0037). Because each artifact in each named collection is
physically read at most once, the reader call count cannot exceed the total
file count across the collections the termini name.

Projection note: ``TERMINUS_VOCABULARY`` is a local projection of
``intent_shape.DECOMPOSITION_TERMINI``. A cross-skill relative import is
forbidden by the catalogue authoring standards; the upstream is stated as a
comment and the parity check that keeps them in sync lives in T4's caller-
enumeration test.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

# ── Terminus vocabulary (projection of intent_shape.DECOMPOSITION_TERMINI) ────
# Upstream: packs/core/.apm/skills/work-intake/scripts/intent_shape.py
# :: DECOMPOSITION_TERMINI
# Cross-skill imports are banned; T4's caller-enumeration test asserts the
# construction is reached only through the approved entry point.

TERMINUS_VOCABULARY: tuple[str, ...] = (
    "children",
    "brief",
    "spec",
    "direct-light",
    "closed-empty",
)

# Termini that name artifact collections and therefore trigger collection reads.
_COLLECTION_TERMINI: frozenset[str] = frozenset({"children", "brief", "spec"})


# ── Artifact record ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DescendantRecord:
    """One artifact in the descendant closure of a single decision.

    ``slug``: declared identity (``Slug:`` preamble field).
    ``kind``: one of ``"intent"``, ``"brief"``, or ``"spec"``.
    ``status``: ``Status:`` field value; empty string when absent.
    ``terminus``: the artifact's own ``Decomposed:`` terminus, or ``""``
        when absent or the value is ``no``.
    """

    slug: str
    kind: str
    status: str
    terminus: str


# ── Injectable seam types ─────────────────────────────────────────────────────

Reader = Callable[[Path], str]
DirLister = Callable[[Path], Iterable[Path]]


# ── Field-parsing helpers (no cross-skill import) ────────────────────────────

_COMMENT_SUFFIX = re.compile(r"\s*<!--.*?-->\s*$", re.DOTALL)
_FIELD_LINE = re.compile(r"^- \*\*([^*:]+):\*\*\s*(.*)$")
_HEADING_PREFIX = "## "
_DECOMPOSED_TERMINUS = re.compile(r"^\d{4}-\d{2}-\d{2}\s+(\S+)")
_MARKDOWN_LINK_TARGET = re.compile(r"^\[.*?\]\((.+?)\)\s*$")


def _normalize(raw: str) -> str:
    """Strip trailing HTML comment then surrounding backticks; order is the contract."""
    value = raw.strip()
    value = _COMMENT_SUFFIX.sub("", value).strip()
    if len(value) >= 2 and value[0] == "`" and value[-1] == "`":
        value = value[1:-1].strip()
    return value


def _preamble(text: str) -> dict[str, str]:
    """Return first-occurrence preamble fields as ``{name: normalized_value}``."""
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith(_HEADING_PREFIX):
            break
        m = _FIELD_LINE.match(line)
        if m:
            name = m.group(1).strip()
            if name not in fields:
                fields[name] = _normalize(m.group(2))
    return fields


def _terminus_from_decomposed(value: str) -> str:
    """Extract the terminus token from a ``Decomposed:`` value, or ``""``."""
    if not value or value == "no":
        return ""
    m = _DECOMPOSED_TERMINUS.match(value)
    return m.group(1) if m else ""


def _resolve_discovery_path(value: str, root: Path) -> Path | None:
    """Resolve a ``Discovery:`` field value to a filesystem path.

    Handles three corpus forms: markdown link, backtick-quoted bare path,
    and bare path. Returns ``None`` for ``none``, empty, or unparseable values.
    """
    if not value or value.lower() == "none":
        return None
    m = _MARKDOWN_LINK_TARGET.match(value)
    path_str = m.group(1).strip() if m else value
    # Strip backticks that _normalize didn't touch (they surround the path
    # rather than the whole value in some corpus forms).
    if len(path_str) >= 2 and path_str[0] == "`" and path_str[-1] == "`":
        path_str = path_str[1:-1].strip()
    return root / path_str if path_str else None


# ── Collection directory helpers ──────────────────────────────────────────────


def _intents_dir(root: Path) -> Path:
    """``docs/product/intents/`` relative to root."""
    return root / "docs" / "product" / "intents"


def _briefs_dir(root: Path) -> Path:
    """``docs/product/briefs/`` relative to root."""
    return root / "docs" / "product" / "briefs"


def _specs_dir(root: Path) -> Path:
    """``docs/specs/`` relative to root."""
    return root / "docs" / "specs"


# ── Default implementations of the injectable seams ──────────────────────────


def _default_reader(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _default_dir_lister(d: Path) -> Iterable[Path]:
    """Return artifact files for a collection directory.

    - Intents and briefs: flat ``.md`` files in the directory.
    - Specs: ``spec.md`` files one level under the directory, one per
      feature subdirectory.
    Files whose names start with ``_`` are excluded (internal artefacts).
    """
    if not d.is_dir():
        return []
    results: list[Path] = []
    for child in sorted(d.iterdir()):
        if child.name.startswith("_"):
            continue
        if child.is_file() and child.suffix == ".md":
            results.append(child)
        elif child.is_dir():
            spec_file = child / "spec.md"
            if spec_file.is_file():
                results.append(spec_file)
    return results


# ── The per-decision index builder ────────────────────────────────────────────


def _build_descendant_closure(
    ancestor_slug: str,
    ancestor_terminus: str,
    root: Path,
    *,
    _reader: Reader | None = None,
    _dir_lister: DirLister | None = None,
) -> dict[str, DescendantRecord]:
    """Build the full descendant closure for one decision.

    Returns ``slug → DescendantRecord`` for every artifact in the closure.
    Each call builds a fresh index; nothing is cached between calls (AC-0021).

    ``_reader`` and ``_dir_lister`` are test seams. Production callers pass
    neither and the defaults read from the real filesystem.

    **AC-0024**: each artifact is physically opened at most once. The
    ``visited`` set prevents the reader from being called twice for the same
    path. When a path is encountered again (e.g. in a second collection scan),
    the cached fields are returned without calling the reader.

    **AC-0025**: dir_lister is called only for collection directories named by
    the termini encountered along the closure. No other directory is listed.
    The ``dir_cache`` prevents a second dir_lister call for the same directory.

    **AC-0037**: because each file is read at most once and only named
    collections are enumerated, the total reader call count cannot exceed the
    summed file count across those collections.

    **AC-0023**: no file is written and no environment variable is set. The
    returned dict is the sole output; its lifetime is the caller's frame.
    """
    reader: Reader = _reader if _reader is not None else _default_reader
    dir_lister: DirLister = _dir_lister if _dir_lister is not None else _default_dir_lister

    # Per-decision state — all local, none persisted.
    visited: set[Path] = set()  # resolved paths physically opened (AC-0024)
    field_cache: dict[Path, dict[str, str]] = {}  # preamble fields per opened path
    dir_cache: dict[Path, list[Path]] = {}  # collection dir → file list (AC-0025)
    result: dict[str, DescendantRecord] = {}

    def _list_dir(d: Path) -> list[Path]:
        """List a collection directory at most once; subsequent calls use the cache."""
        key = d.resolve()
        if key not in dir_cache:
            dir_cache[key] = list(dir_lister(d))
        return dir_cache[key]

    def _get_fields(path: Path) -> dict[str, str]:
        """Return preamble fields for a path, reading it at most once (AC-0024).

        If the path is already in ``visited``, returns cached fields without
        calling the reader. This is the mechanism that prevents double-opens
        in the diamond case: a file encountered as a candidate in two separate
        collection scans is physically read only on the first encounter.
        """
        key = path.resolve()
        if key not in visited:
            visited.add(key)
            try:
                text = reader(path)
            except OSError:
                text = ""
            field_cache[key] = _preamble(text)
        return field_cache.get(key, {})

    def _resolve_discovery_slug(discovery_value: str) -> str | None:
        """Return the slug the ``Discovery:`` value names, or ``None``.

        Resolves the path and reads the target artifact at most once.
        """
        target = _resolve_discovery_path(discovery_value, root)
        if target is None:
            return None
        fields = _get_fields(target)
        return fields.get("Slug") or None

    def _add_descendant(slug: str, kind: str, fields: dict[str, str]) -> None:
        """Add an artifact to the result and enqueue further descent if needed."""
        if slug in result:
            return  # already found (handles diamond: same slug via two paths)
        status = fields.get("Status", "")
        raw_decomposed = fields.get("Decomposed", "")
        terminus = _terminus_from_decomposed(raw_decomposed)
        result[slug] = DescendantRecord(
            slug=slug, kind=kind, status=status, terminus=terminus
        )
        if terminus in _COLLECTION_TERMINI:
            queue.append((slug, terminus))

    queue: list[tuple[str, str]] = [(ancestor_slug, ancestor_terminus)]

    while queue:
        parent_slug, terminus = queue.pop(0)

        if terminus not in _COLLECTION_TERMINI:
            continue

        if terminus == "children":
            # Invert ``Parent intent: intent:<parent_slug>`` over the intents collection.
            for path in _list_dir(_intents_dir(root)):
                fields = _get_fields(path)
                slug = fields.get("Slug", "")
                if not slug:
                    continue
                if fields.get("Parent intent", "") == f"intent:{parent_slug}":
                    _add_descendant(slug, "intent", fields)

        elif terminus == "brief":
            # Phase 1: invert ``Parent intent:`` over briefs.
            found_brief_slugs: set[str] = set()
            for path in _list_dir(_briefs_dir(root)):
                fields = _get_fields(path)
                slug = fields.get("Slug", "")
                if not slug:
                    continue
                if fields.get("Parent intent", "") == f"intent:{parent_slug}":
                    status = fields.get("Status", "")
                    # Briefs carry no ``Decomposed:`` field; they do not drive
                    # further descent from their own terminus.
                    if slug not in result:
                        result[slug] = DescendantRecord(
                            slug=slug, kind="brief", status=status, terminus=""
                        )
                    found_brief_slugs.add(slug)

            # Phase 2: invert ``Brief: brief:<brief_slug>`` over specs.
            if found_brief_slugs:
                for path in _list_dir(_specs_dir(root)):
                    fields = _get_fields(path)
                    slug = fields.get("Slug", "")
                    if not slug:
                        continue
                    brief_ptr = fields.get("Brief", "")
                    # ``Brief:`` format is ``brief:<slug>``.
                    if (
                        brief_ptr.startswith("brief:")
                        and brief_ptr[len("brief:"):] in found_brief_slugs
                    ):
                        _add_descendant(slug, "spec", fields)

        elif terminus == "spec":
            # Invert ``Discovery:`` over specs: find specs whose Discovery: resolves
            # to the parent slug.
            for path in _list_dir(_specs_dir(root)):
                fields = _get_fields(path)
                slug = fields.get("Slug", "")
                if not slug:
                    continue
                discovery_val = fields.get("Discovery", "")
                resolved_slug = _resolve_discovery_slug(discovery_val)
                if resolved_slug == parent_slug:
                    _add_descendant(slug, "spec", fields)

    return result
