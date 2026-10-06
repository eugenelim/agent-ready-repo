"""Discover npm projects without widening the repository's visible-tree walk.

Ordinary projects come from the historic visible walk, which deliberately
prunes dot directories, ``node_modules``, and linked directories.  Pack skill
projects are a separate, explicit route: ``packs/*/.apm/skills/*/``.  That
route validates every admitted manifest and lockfile before a consumer may
read it, so a linked or otherwise non-regular canonical input fails closed.
"""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path

LOCKFILE_NAME = "package-lock.json"
MANIFEST_NAME = "package.json"
_PRUNED_DIR_NAMES = frozenset({"node_modules"})


class DiscoveryError(Exception):
    """The project inventory cannot be safely determined."""


@dataclass(frozen=True)
class CanonicalProject:
    """One canonical pack skill root and whichever npm inputs it carries."""

    directory: Path
    manifest: Path | None
    lockfile: Path | None


def _entries(directory: Path) -> list[Path]:
    try:
        return list(directory.iterdir())
    except OSError as exc:
        raise DiscoveryError(f"cannot read {directory}: {exc}") from exc


def visible_lockfiles(root: Path) -> list[Path]:
    """Return visible project locks, preserving the existing prune behaviour."""
    found: list[Path] = []
    stack = [root]
    while stack:
        current = stack.pop()
        for entry in _entries(current):
            try:
                is_directory = entry.is_dir()
                is_symlink = entry.is_symlink()
            except OSError as exc:
                raise DiscoveryError(f"cannot classify {entry}: {exc}") from exc
            if is_directory:
                if is_symlink or entry.name in _PRUNED_DIR_NAMES or entry.name.startswith("."):
                    continue
                stack.append(entry)
            elif entry.name == LOCKFILE_NAME:
                found.append(entry)
    return sorted(found)


def _exists_lexically(path: Path) -> bool:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise DiscoveryError(f"cannot inspect {path}: {exc}") from exc
    return True


def _child_directories(directory: Path) -> list[Path]:
    if not _exists_lexically(directory):
        return []
    children: list[Path] = []
    for entry in _entries(directory):
        try:
            if entry.is_dir():
                children.append(entry)
        except OSError as exc:
            raise DiscoveryError(f"cannot classify {entry}: {exc}") from exc
    return sorted(children)


def _canonical_candidates(root: Path) -> list[CanonicalProject]:
    """Find canonical skill roots explicitly; do not use the visible walk."""
    projects: list[CanonicalProject] = []
    for pack in _child_directories(root / "packs"):
        for skill in _child_directories(pack / ".apm" / "skills"):
            manifest_path = skill / MANIFEST_NAME
            lockfile_path = skill / LOCKFILE_NAME
            manifest = manifest_path if _exists_lexically(manifest_path) else None
            lockfile = lockfile_path if _exists_lexically(lockfile_path) else None
            if manifest is not None or lockfile is not None:
                projects.append(CanonicalProject(skill, manifest, lockfile))
    return projects


def _validate_canonical_file(root: Path, path: Path) -> None:
    """Require *path* to be a unique regular in-root file without link segments."""
    try:
        resolved_root = root.resolve(strict=True)
        resolved = path.resolve(strict=True)
        resolved.relative_to(resolved_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise DiscoveryError(
            f"canonical npm input refused: {path}: outside repository root"
        ) from exc

    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise DiscoveryError(
            f"canonical npm input refused: {path}: outside repository root"
        ) from exc
    current = root
    for part in relative.parts:
        current = current / part
        try:
            mode = os.lstat(current).st_mode
        except OSError as exc:
            raise DiscoveryError(
                f"canonical npm input refused: {path}: cannot inspect {current}: {exc}"
            ) from exc
        if stat.S_ISLNK(mode):
            raise DiscoveryError(
                f"canonical npm input refused: {path}: linked path component {current}"
            )
    try:
        info = path.stat()
    except OSError as exc:
        raise DiscoveryError(
            f"canonical npm input refused: {path}: cannot stat file: {exc}"
        ) from exc
    if not stat.S_ISREG(info.st_mode):
        raise DiscoveryError(f"canonical npm input refused: {path}: not a regular file")
    if info.st_nlink != 1:
        raise DiscoveryError(f"canonical npm input refused: {path}: hard-linked file")


def canonical_projects(root: Path) -> list[CanonicalProject]:
    """Return canonical pack projects after validating every admitted input."""
    projects = _canonical_candidates(root)
    for project in projects:
        for path in (project.manifest, project.lockfile):
            if path is not None:
                _validate_canonical_file(root, path)
    return projects


def discover_lockfiles(root: Path) -> list[Path]:
    """Return visible and canonical lockfiles, validating the canonical route."""
    found = set(visible_lockfiles(root))
    for project in canonical_projects(root):
        if project.lockfile is not None:
            found.add(project.lockfile)
    return sorted(found)
