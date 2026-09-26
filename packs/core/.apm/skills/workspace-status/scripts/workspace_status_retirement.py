#!/usr/bin/env python3
"""Area inference and fail-closed reading for spec-retirement eligibility projection.

This module provides two capability groups:

**Area inference** (T3) — pure functions with no I/O that derive a top-level
namespace set from a tracked file list and attribute a spec body to one of those
namespaces (or to ``"unscoped"``).  Callers supply already-read data.

**Fail-closed reading** (T0c) — confinement-enforcing file readers that produce
distinguishable refusal codes and suppress candidate eligibility at the corpus
level.  An unread input produces no scan blockers, so suppression is a property
of the corpus being read in full, never of the blockers the scan happened to yield.

Every repository read must route through :func:`confined_read_bytes`.  The
higher-level wrappers (:func:`read_confined_substrate`, :func:`read_toml_substrate`,
:func:`read_json_substrate`, :func:`read_text_substrate`) apply corpus-level
suppression on any read or parse failure.
"""
from __future__ import annotations

import dataclasses
import json
import os
import re
import stat
import tomllib
from collections.abc import Iterable
from pathlib import Path

if False:  # pragma: no cover — type-checking import only
    pass

# ---------------------------------------------------------------------------
# Confinement constants and injectable seam
# ---------------------------------------------------------------------------

#: Hard read limit per file.  The largest file in the corpus is 144 KB, so
#: this bound fires only on a pathological input, not on a large real one.
_READ_LIMIT: int = 8 * 1024 * 1024  # 8 MiB

#: Module-level injectable for tests.  ``confined_read_bytes`` calls this to
#: open a file descriptor; replacing it with a stub that fails proves a refused
#: path never reaches an ``open()`` call.
_OPEN_FUNC = os.open


# ---------------------------------------------------------------------------
# Refusal types
# ---------------------------------------------------------------------------


class ConfinementRefusal(Exception):
    """Raised when a repository path read is refused before or during the guarded open.

    Every refusal reason is produced at the point of detection — from the
    result of the step that detected the problem — and never from a second
    filesystem call on a path already refused (which would re-walk an
    attacker-controlled path outside the guard).

    Attributes:
        code:   Refusal code, e.g. ``"path-escapes-root"``, ``"input-unreadable"``,
                ``"spec-unreadable"``, ``"input-too-large"``, ``"input-unparseable"``.
        path:   The repository-relative path, as written, never resolved.
        detail: Optional bounded detail string for additional context.
    """

    def __init__(self, *, code: str, path: str, detail: str = "") -> None:
        super().__init__(f"{code}: {path}")
        self.code = code
        self.path = path
        self.detail = detail


@dataclasses.dataclass
class Refusal:
    """A corpus-level refusal that withholds eligibility from named candidates.

    Suppression is corpus-level, not blocker-level: an unread input produces
    no scan blockers, so keying suppression on the blockers a scan yielded
    would suppress nothing.  Each :class:`Refusal` names every candidate whose
    eligibility it withholds.

    Attributes:
        code:       Refusal code emitted in the output document.
        path:       The input that could not be read or parsed.
        suppresses: Candidate slugs suppressed by this refusal.
    """

    code: str
    path: str
    suppresses: list[str]


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------


def _is_retirement_path(value: object) -> bool:
    """Return ``True`` for a non-empty, bounded, repository-relative path.

    Rejects absolute paths, Windows-drive prefixes, backslashes, control
    characters (ASCII 0–31 and DEL), and any component that is ``..``, ``.``,
    or empty (which a split on ``"/"`` would expose as ``""``).

    This check fires before any OS call in :func:`confined_read_bytes`, so a
    path that fails here never touches the filesystem.
    """
    if not isinstance(value, str) or not 1 <= len(value) <= 1000:
        return False
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return False
    if "\\" in value:
        return False
    if any(ord(c) <= 31 or ord(c) == 127 for c in value):
        return False
    parts = value.split("/")
    return ".." not in parts and "." not in parts and "" not in parts


# ---------------------------------------------------------------------------
# Confinement reader
# ---------------------------------------------------------------------------


def confined_read_bytes(
    root: Path,
    rel_path: str,
    *,
    spec_body: bool = False,
) -> bytes:
    """Read a repository-relative regular file with full confinement guarantees.

    The five-step check order is load-bearing:

    1. **Path format** — rejects absolute, traversal, and control-character
       paths before any OS call, so an invalid path never touches the filesystem.
    2. **Component walk** — ``lstat()`` each path component; refuse any symlink
       or reparse point before opening.  The refusal code is set at the point of
       detection, not from a second call on the refused path.
    3. **Resolution check** — the resolved path must stay within ``root``.
    4. **Guarded open** — ``O_NOFOLLOW``; ``fstat()`` confirms a regular file
       on the opened descriptor; device/inode re-check detects a path swapped
       between the ``stat()`` and the ``open()``.  Every reason code in this
       region comes from the descriptor result, never from a second path stat.
    5. **Bounded read** — stops at :data:`_READ_LIMIT`; refuses as
       ``"input-too-large"`` (stopping is the refusal, not measuring afterwards).

    :data:`_OPEN_FUNC` is module-level and injectable so tests can verify that
    a refused path never triggers an ``open()`` call.

    Args:
        root:      Repository root directory (resolved or resolvable).
        rel_path:  Repository-relative path; must pass :func:`_is_retirement_path`.
        spec_body: When ``True``, unreadable files are refused as
                   ``"spec-unreadable"`` instead of ``"input-unreadable"``.

    Returns:
        Raw bytes of the file contents.

    Raises:
        ConfinementRefusal: With ``code`` set to the applicable refusal code.
    """
    unread_code = "spec-unreadable" if spec_body else "input-unreadable"

    # Step 1 — path format validation.  No OS call before this passes.
    if not _is_retirement_path(rel_path):
        raise ConfinementRefusal(code="path-escapes-root", path=rel_path)

    try:
        root_resolved = root.resolve(strict=True)
    except OSError as exc:
        raise ConfinementRefusal(code=unread_code, path=rel_path) from exc

    # Step 2 — component-by-component symlink / reparse-point check.
    # Each lstat is on an intermediate path component, not on a path already
    # refused.  The refusal reason comes from the lstat result at detection.
    cursor = root_resolved
    for part in rel_path.split("/"):
        cursor = cursor / part
        try:
            info = cursor.lstat()
        except OSError:
            # Component does not exist yet; the open in step 4 will refuse it.
            break
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        is_link = stat.S_ISLNK(info.st_mode) or bool(
            reparse_flag and getattr(info, "st_file_attributes", 0) & reparse_flag
        )
        if is_link:
            # A link is refused only when its target leaves the root.  Refusing
            # every link refuses this repository's own CLAUDE.md files, which
            # point at a sibling AGENTS.md and escape nothing — and one such
            # file in a scanned corpus withholds eligibility from the whole
            # report.  The refusal reason is still derived here, from this
            # lstat plus one resolve of the same component; no second walk of
            # an already-refused path.
            try:
                target = cursor.resolve()
                target.relative_to(root_resolved)
            except (OSError, RuntimeError, ValueError) as exc:
                raise ConfinementRefusal(
                    code="path-escapes-root", path=rel_path
                ) from exc

    # Step 3 — resolution confinement: resolved path must not escape root.
    try:
        resolved = (root_resolved / rel_path).resolve()
        resolved.relative_to(root_resolved)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ConfinementRefusal(code="path-escapes-root", path=rel_path) from exc

    # Step 4 — guarded open.  Every refusal in this region is produced from
    # a descriptor result or an errno value, never from a second path-based call.
    try:
        before = resolved.stat()
    except OSError as exc:
        raise ConfinementRefusal(code=unread_code, path=rel_path) from exc

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = _OPEN_FUNC(resolved, flags)
    except OSError as exc:
        raise ConfinementRefusal(code=unread_code, path=rel_path) from exc

    try:
        opened = os.fstat(fd)
        # Regular-file confirmation from the descriptor, not from a second stat().
        if not stat.S_ISREG(opened.st_mode):
            raise ConfinementRefusal(code=unread_code, path=rel_path)
        # Device/inode re-check: a path swapped between stat() and open() is refused.
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise ConfinementRefusal(code=unread_code, path=rel_path)
        # Step 5 — bounded read.
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            total += len(chunk)
            if total > _READ_LIMIT:
                raise ConfinementRefusal(code="input-too-large", path=rel_path)
            chunks.append(chunk)
        return b"".join(chunks)
    except ConfinementRefusal:
        raise
    except OSError as exc:
        raise ConfinementRefusal(code=unread_code, path=rel_path) from exc
    finally:
        os.close(fd)


# ---------------------------------------------------------------------------
# Corpus-level suppression
# ---------------------------------------------------------------------------


def apply_refusals(
    candidates: dict[str, dict],
    refusals: list[Refusal],
) -> None:
    """Apply corpus-level refusals to ``candidates``, marking suppressed ones.

    For every slug in each refusal's ``suppresses`` list:
    - Sets ``candidate["eligible"] = False``.
    - Appends ``"evidence-unread"`` to ``candidate["blockers"]`` if not present.

    Suppression is corpus-level: an unread input produces no scan blockers, so
    a candidate with an empty blocker list is still suppressed when the corpus
    that would prove its absence cannot be read in full.

    Mutates ``candidates`` in place.
    """
    for refusal in refusals:
        for slug in refusal.suppresses:
            candidate = candidates.get(slug)
            if candidate is None:
                continue
            candidate["eligible"] = False
            blockers: list = candidate.setdefault("blockers", [])
            if "evidence-unread" not in blockers:
                blockers.append("evidence-unread")


# ---------------------------------------------------------------------------
# Fail-closed substrate wrappers
# ---------------------------------------------------------------------------


def read_confined_substrate(
    root: Path,
    rel_path: str,
    candidates: dict[str, dict],
    *,
    spec_body: bool = False,
) -> bytes | None:
    """Read a substrate file; suppress named candidates on any read failure.

    This is the fail-closed wrapper every corpus read in the pipeline must use.
    The ``except ConfinementRefusal`` block is the load-bearing fail-closed
    branch: removing it lets an unreadable corpus produce no suppression — the
    fail-open hole this task exists to close.  Deleting that block turns the
    construction tests red.

    Args:
        root:       Repository root directory.
        rel_path:   Repository-relative path to the substrate file.
        candidates: Candidates dict, mutated in place on failure.
        spec_body:  When ``True``, propagates ``spec_body=True`` to
                    :func:`confined_read_bytes`.

    Returns:
        Raw bytes on success, or ``None`` after mutating ``candidates``.
    """
    try:
        return confined_read_bytes(root, rel_path, spec_body=spec_body)
    except ConfinementRefusal as exc:
        refusal = Refusal(
            code=exc.code,
            path=rel_path,
            suppresses=list(candidates),
        )
        apply_refusals(candidates, [refusal])
        return None


def read_toml_substrate(
    root: Path,
    rel_path: str,
    candidates: dict[str, dict],
) -> dict | None:
    """Read and parse a TOML substrate; suppress candidates on any failure.

    Returns the parsed ``dict`` on success, or ``None`` after mutating
    ``candidates`` with an ``"input-unreadable"`` or ``"input-unparseable"``
    refusal.
    """
    raw = read_confined_substrate(root, rel_path, candidates)
    if raw is None:
        return None
    try:
        return tomllib.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        apply_refusals(
            candidates,
            [Refusal(code="input-unparseable", path=rel_path, suppresses=list(candidates))],
        )
        return None


def read_json_substrate(
    root: Path,
    rel_path: str,
    candidates: dict[str, dict],
) -> dict | None:
    """Read and parse a JSON substrate; suppress candidates on any failure.

    Returns the parsed ``dict`` on success, or ``None`` after mutating
    ``candidates`` with an ``"input-unreadable"`` or ``"input-unparseable"``
    refusal.
    """
    raw = read_confined_substrate(root, rel_path, candidates)
    if raw is None:
        return None
    try:
        return json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        apply_refusals(
            candidates,
            [Refusal(code="input-unparseable", path=rel_path, suppresses=list(candidates))],
        )
        return None


def read_text_substrate(
    root: Path,
    rel_path: str,
    candidates: dict[str, dict],
    *,
    spec_body: bool = False,
) -> str | None:
    """Read a text substrate as UTF-8; suppress candidates on any failure.

    Returns the decoded ``str`` on success, or ``None`` after mutating
    ``candidates`` with an ``"input-unreadable"``, ``"spec-unreadable"``, or
    ``"input-unparseable"`` refusal.
    """
    raw = read_confined_substrate(root, rel_path, candidates, spec_body=spec_body)
    if raw is None:
        return None
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        apply_refusals(
            candidates,
            [Refusal(code="input-unparseable", path=rel_path, suppresses=list(candidates))],
        )
        return None


def infer_namespaces(tracked_files: Iterable[str]) -> frozenset[str]:
    """Derive the set of top-level namespace directories from tracked file paths.

    Each path whose first ``/``-separated component is non-empty names a
    top-level directory.  Files at the repository root (no ``/``) contribute no
    namespace.

    The return type is ``frozenset`` so that two calls over the same input
    always compare equal and the result is safely hashable.

    Args:
        tracked_files: Repository-relative file paths, e.g. from ``git ls-files``.

    Returns:
        A frozenset of top-level directory names such as ``{"packs", "docs",
        "tools"}``.  Never contains empty strings.
    """
    namespaces: set[str] = set()
    for path in tracked_files:
        # Only the first component before the first slash names a directory.
        # A path with no slash is a root file and contributes nothing.
        slash = path.find("/")
        if slash > 0:
            namespaces.add(path[:slash])
    return frozenset(namespaces)


def attribute_spec(body: str, namespaces: frozenset[str]) -> str:
    """Attribute a spec body to a top-level namespace, or to ``"unscoped"``.

    Searches *body* for occurrences of ``<namespace>/`` patterns.  Returns the
    namespace that appears most often.  Ties are broken alphabetically so the
    result is deterministic.  Returns ``"unscoped"`` when no namespace appears.

    The algorithm treats a namespace as named when its directory prefix (i.e.
    the string ``<namespace>/``) occurs anywhere in the text.  This matches
    repository path references in spec prose such as ``"packs/core/..."`` or
    ``"widgets/foo"``.

    Args:
        body:       Spec body text (and optionally concatenated plan text).
        namespaces: The frozenset produced by :func:`infer_namespaces`.

    Returns:
        A namespace string from *namespaces*, or ``"unscoped"``.
    """
    counts: dict[str, int] = {}
    for ns in namespaces:
        # Match the namespace as a path prefix: "<namespace>/"
        pattern = re.compile(re.escape(ns) + r"/")
        n = len(pattern.findall(body))
        if n > 0:
            counts[ns] = n

    if not counts:
        return "unscoped"

    # Most-cited namespace wins; alphabetical order breaks ties deterministically.
    return min(counts, key=lambda ns: (-counts[ns], ns))
