"""T3 (credbroker-user-scope): user-libs/ build-pipeline primitive class.

Vendors the stdlib-base ``credbroker`` package source as a ``sys.path``
*floor* — the lowest-precedence import target a consumer bootstrap
appends (``~/.agentbundle/lib`` at user scope). A pip-installed
``credbroker`` in site-packages always wins; the floor answers only when
nothing else did (spec ``credbroker-user-scope`` Layer 1).

Source of truth: ``packages/credbroker/credbroker/`` (the package whose
wheel the layer-2/3 release ships). This module projects that source,
byte-faithfully, to two committed targets:

- **Pack-vendored copy** — ``packs/credential-brokers/.apm/user-libs/credbroker/``.
  The catalogue-visible primitive: ``build/main.py`` copytrees the whole
  ``.apm/`` tree into each dist pack, so this flows pack→catalogue→install
  (T4 reads it to deliver ``~/.agentbundle/lib/credbroker/``).
- **Self-host floor staging** — ``<working_tree>/.agentbundle/lib/credbroker/``.
  Mirrors the ``adapter-root-bins`` ``.agentbundle/bin/`` staging — committed
  to the repo and drift-gated like it.

Both targets are byte-faithful projections of the package source,
excluding ``__pycache__`` and any ``tests`` subtree. The base import graph
reaches no third-party module (``_vault`` imports ``cryptography``/``argon2``
lazily under the ``[crypto]`` extra) — preserved by copying the package
source verbatim and asserted by the purity test against the vendored copy.

This module owns both halves of the build-pipeline contract for the new
primitive class:

- ``apply_projection(working_tree, packs_dir)`` — write the files. Called by
  ``make build-self``. Files land with **default** mode (importable Python,
  no exec bit — unlike ``adapter-root-bins``' ``0o755``).
- ``check_drift(working_tree, packs_dir)`` — read-only gate. Returns a list
  of drift descriptions (empty list == clean), with the same three outcomes
  ``adapter-root-bins`` resolves: **modified** / **missing** / **orphaned**.

Like ``adapter-root-bins``/``shared-libs``, ``user-libs`` is a
build-pipeline-only primitive: it has no per-adapter projection rules (its
target is ``.agentbundle/lib/``, fenced by ``allowed-prefixes.<scope>``, not
a per-adapter target path), so adding it does **not** bump the
adapter-contract version (precedent: the credential-broker change added
both build-only
primitives within v0.7 — see ``de790fe``).

**Non-monorepo invocation.** The package source only ever exists in the
development monorepo. When it is absent (``packs_dir.parent`` is not the
repo root — e.g. a fixture packs dir, or a packaged ``agentbundle`` run
outside the monorepo) the projection is a no-op: there is nothing to
compare against, and the floor is only meaningful where the source-of-truth
package is on disk. Real ``make build-self`` / ``make build-check`` always
run with ``packs_dir == <repo>/packs`` so the gate is live in CI.

Path-jail compliance: the target (``.agentbundle/``) is fenced by the
contract's ``allowed-prefixes`` for the user-scope adapters — the same
prefix ``adapter-root-bins`` writes under. No PATH manipulation, no
shell-config edits.
"""

from __future__ import annotations

import contextlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from .projection_io import (
    ProjectionTypeError,
    copy_file_atomic_no_follow,
    ensure_directory_no_follow,
    open_directory_no_follow,
    read_regular_file_no_follow,
    render_diagnostic_path,
    unlink_file_no_follow,
)

# The vendored package: repo-relative source leaf and the module name it
# resolves under on a consumer's ``sys.path``.
PACKAGE_SUBPATH = Path("packages") / "credbroker" / "credbroker"
VENDORED_MODULE = "credbroker"

# Pack that carries the catalogue-visible vendored copy.
PACK_NAME = "credential-brokers"
PACK_TARGET_SUBDIR = Path(".apm") / "user-libs"

# Self-host floor staging under the per-scope artifact root. Mirrors the
# ``~/.agentbundle/lib/`` path at user scope (install-time surface, T4).
TARGET_SUBDIR = Path(".agentbundle") / "lib"

# Directory names never vendored: bytecode caches and any test tree
# (``tests`` is forward-looking — the package ships none today; it guards a
# future in-package test tree). The orphan scan skips them too — importing the
# floor (e.g. the purity test) writes ``__pycache__/`` that must not register
# as drift.
EXCLUDED_DIR_NAMES = frozenset({"__pycache__", "tests"})


@dataclass(frozen=True)
class UserLibProjection:
    """One concrete projection: copy ``source`` to ``target``."""

    source: Path
    target: Path


def _package_source_dir(packs_dir: Path) -> Path:
    """Locate ``packages/credbroker/credbroker/`` relative to the repo root.

    ``packs_dir`` is ``<repo>/packs`` in every real ``make build-self`` /
    ``make build-check`` invocation, so its parent is the repo root.
    """
    return packs_dir.parent / PACKAGE_SUBPATH


def _is_excluded(rel: Path) -> bool:
    """True iff any path segment names an excluded subtree."""
    return any(part in EXCLUDED_DIR_NAMES for part in rel.parts)


def collect_sources(source_dir: Path) -> dict[str, Path]:
    """Return ``{posix-relpath → source_path}`` for every file under
    ``source_dir``, excluding ``__pycache__`` and ``tests`` subtrees.

    Empty mapping when ``source_dir`` is absent — see the module docstring's
    non-monorepo note. The package carries no symlinks; a plain ``rglob``
    walk is safe here.
    """
    sources: dict[str, Path] = {}
    if not source_dir.is_dir():
        return sources
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(source_dir)
        if _is_excluded(rel):
            continue
        sources[rel.as_posix()] = path
    return sources


def _target_roots(working_tree: Path, packs_dir: Path) -> list[Path]:
    """The two vendored-copy roots: the pack copy and the floor staging."""
    return [
        packs_dir / PACK_NAME / PACK_TARGET_SUBDIR / VENDORED_MODULE,
        working_tree / TARGET_SUBDIR / VENDORED_MODULE,
    ]


def _target_root_specs(
    working_tree: Path, packs_dir: Path
) -> list[tuple[Path, Path]]:
    """Return trusted base + owned relative directory for each target root."""
    return [
        (
            packs_dir,
            Path(PACK_NAME) / PACK_TARGET_SUBDIR / VENDORED_MODULE,
        ),
        (working_tree, TARGET_SUBDIR / VENDORED_MODULE),
    ]


def _target_root_for(
    target: Path, working_tree: Path, packs_dir: Path
) -> Path:
    """Return the owned projection root containing ``target``."""
    for root in _target_roots(working_tree, packs_dir):
        if target.is_relative_to(root):
            return root
    raise ValueError(f"user-lib target is outside owned roots: {target}")


def _target_path_problem(
    base: Path, relative: Path
) -> tuple[Path, str, str] | None:
    """Return the first unreadable/non-directory component, no-follow."""
    current = base
    for part in relative.parts:
        current /= part
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            return None
        except OSError as exc:
            return current, "unreadable", str(exc)
        if stat.S_ISDIR(current_stat.st_mode):
            continue
        kind = "a symlink" if stat.S_ISLNK(current_stat.st_mode) else "not a directory"
        return current, "type mismatch", kind
    return None


def _target_path_problem_drift(
    problem: tuple[Path, str, str], working_tree: Path, packs_dir: Path
) -> str:
    """Format one target ancestor problem as an actionable drift."""
    path, category, detail = problem
    display = _display(path, working_tree, packs_dir)
    if category == "unreadable":
        return (
            f"[user-libs] unreadable: {display}: {detail}; "
            f"run: make build-self FORCE=1"
        )
    return (
        f"[user-libs] type mismatch: {display} is {detail}; expected an "
        f"owned directory; run: make build-self FORCE=1"
    )


def compute_projections(
    working_tree: Path, packs_dir: Path
) -> list[UserLibProjection]:
    """Return the full ``(source → target)`` list across both targets.

    Deterministic order — drift gates depend on it. Empty when the package
    source is absent (non-monorepo invocation; see the module docstring).
    """
    sources = collect_sources(_package_source_dir(packs_dir))
    # No sources → no projections. This covers the non-monorepo case (the
    # documented no-op) AND whole-package retirement: if the package source
    # were ever deleted, the gate goes silent, so retiring credbroker must
    # hand-remove both committed targets (the floor + the pack copy).
    if not sources:
        return []
    pack_dir, floor_dir = _target_roots(working_tree, packs_dir)
    projections: list[UserLibProjection] = []
    for rel in sorted(sources):
        src = sources[rel]
        projections.append(UserLibProjection(source=src, target=pack_dir / rel))
        projections.append(UserLibProjection(source=src, target=floor_dir / rel))
    return projections


def _orphan_files(
    root: Path, expected: set[Path], *, base: Path
) -> list[Path]:
    """Files under ``root`` not in ``expected``, skipping excluded subtrees."""
    orphans: list[Path] = []
    try:
        with open_directory_no_follow(base, root.relative_to(base)) as root_fd:
            if root_fd is None:
                for existing in sorted(root.rglob("*")):
                    try:
                        existing_stat = existing.lstat()
                    except FileNotFoundError:  # pragma: no cover — race-only
                        continue
                    if stat.S_ISDIR(existing_stat.st_mode) or existing in expected:
                        continue
                    if not _is_excluded(existing.relative_to(root)):
                        orphans.append(existing)
                return orphans

            for dirpath, dirnames, filenames, directory_fd in os.fwalk(
                ".", topdown=True, follow_symlinks=False, dir_fd=root_fd
            ):
                relative_dir = Path() if dirpath == "." else Path(dirpath)
                kept_directories: list[str] = []
                for name in dirnames:
                    try:
                        entry_stat = os.stat(
                            name, dir_fd=directory_fd, follow_symlinks=False
                        )
                    except FileNotFoundError:
                        continue
                    if stat.S_ISDIR(entry_stat.st_mode):
                        kept_directories.append(name)
                    else:
                        filenames.append(name)
                dirnames[:] = kept_directories
                for name in filenames:
                    existing = root / relative_dir / name
                    if existing in expected:
                        continue
                    if not _is_excluded(existing.relative_to(root)):
                        orphans.append(existing)
    except FileNotFoundError:
        return []
    return orphans


def apply_projection(working_tree: Path, packs_dir: Path) -> None:
    """Write every projection target and remove orphans.

    Called by ``make build-self``. Idempotent — running twice produces the
    same on-disk state. Files are written with **default** mode (importable
    Python, no exec bit). No-op when the package source is absent.

    Three drift outcomes resolved here:
      * **missing** → file written from source
      * **modified** → file overwritten from source
      * **orphaned** → file removed (no longer in the vendored source)
    """
    projections = compute_projections(working_tree, packs_dir)
    if not projections:
        return
    expected_targets = {p.target for p in projections}
    for base, relative in _target_root_specs(working_tree, packs_dir):
        ensure_directory_no_follow(base, relative)
    for proj in projections:
        target_base = (
            working_tree if proj.target.is_relative_to(working_tree) else packs_dir
        )
        ensure_directory_no_follow(
            target_base,
            proj.target.parent.relative_to(target_base),
        )
        copy_file_atomic_no_follow(
            proj.source,
            proj.target,
            base=target_base,
        )
    for base, relative in _target_root_specs(working_tree, packs_dir):
        root = base / relative
        for existing in _orphan_files(root, expected_targets, base=base):
            with contextlib.suppress(FileNotFoundError):  # pragma: no cover
                unlink_file_no_follow(existing, base=base)


def _display(path: Path, working_tree: Path, packs_dir: Path) -> str:
    """Render ``path`` relative to the repo root for a drift message."""
    for base in (working_tree, packs_dir.parent):
        try:
            return render_diagnostic_path(path.relative_to(base))
        except ValueError:
            continue
    return render_diagnostic_path(path)  # pragma: no cover — defensive


def check_drift(working_tree: Path, packs_dir: Path) -> list[str]:
    """Return drift descriptions for ``make build-check``.

    Three outcomes — **modified** / **missing** / **orphaned** — across both
    committed targets (pack copy + floor staging), each compared byte-wise to
    the package source. Empty when the package source is absent (nothing to
    compare). Each description ends with the regeneration command.
    """
    drifts: list[str] = []
    projections = compute_projections(working_tree, packs_dir)
    if not projections:
        return drifts

    invalid_roots: set[Path] = set()
    for base, relative in _target_root_specs(working_tree, packs_dir):
        problem = _target_path_problem(base, relative)
        if problem is None:
            continue
        root = base / relative
        invalid_roots.add(root)
        drifts.append(_target_path_problem_drift(problem, working_tree, packs_dir))

    expected_targets: set[Path] = set()
    reported_parent_mismatches: set[Path] = set()
    for proj in projections:
        expected_targets.add(proj.target)
        if any(proj.target.is_relative_to(root) for root in invalid_roots):
            continue
        target_root = _target_root_for(proj.target, working_tree, packs_dir)
        parent_problem = _target_path_problem(
            target_root, proj.target.parent.relative_to(target_root)
        )
        if parent_problem is not None:
            path, _category, _detail = parent_problem
            if path not in reported_parent_mismatches:
                reported_parent_mismatches.add(path)
                drifts.append(
                    _target_path_problem_drift(
                        parent_problem, working_tree, packs_dir
                    )
                )
            continue
        target_display = _display(proj.target, working_tree, packs_dir)
        source_display = render_diagnostic_path(
            proj.source.relative_to(packs_dir.parent)
        )
        try:
            source_bytes = proj.source.read_bytes()
            source_stat = proj.source.stat()
        except OSError as exc:  # pragma: no cover — defensive
            drifts.append(f"[user-libs] source unreadable: {exc}")
            continue
        target_base = (
            working_tree if proj.target.is_relative_to(working_tree) else packs_dir
        )
        try:
            target_bytes, target_stat = read_regular_file_no_follow(
                proj.target,
                base=target_base,
            )
        except FileNotFoundError:
            drifts.append(
                f"[user-libs] missing: {target_display} "
                f"(source: {source_display}); run: make build-self FORCE=1"
            )
            continue
        except ProjectionTypeError as exc:
            drifts.append(
                f"[user-libs] type mismatch: {target_display} {exc}; "
                f"expected a regular projected file; run: make build-self FORCE=1"
            )
            continue
        except OSError as exc:
            drifts.append(f"[user-libs] unreadable: {target_display}: {exc}")
            continue
        if os.name == "posix":
            source_mode = stat.S_IMODE(source_stat.st_mode)
            target_mode = stat.S_IMODE(target_stat.st_mode)
            if target_mode != source_mode:
                drifts.append(
                    f"[user-libs] mode drift: {target_display} has "
                    f"{oct(target_mode)}, expected {oct(source_mode)}; "
                    f"run: make build-self FORCE=1"
                )
        if target_bytes != source_bytes:
            drifts.append(
                f"[user-libs] modified: {target_display} "
                f"diverges from {source_display}; run: make build-self FORCE=1"
            )

    for base, relative in _target_root_specs(working_tree, packs_dir):
        root = base / relative
        if root in invalid_roots:
            continue
        try:
            orphan_files = _orphan_files(root, expected_targets, base=base)
        except OSError as exc:
            drifts.append(
                f"[user-libs] unreadable: "
                f"{_display(root, working_tree, packs_dir)}: {exc}"
            )
            continue
        for existing in orphan_files:
            existing_display = _display(existing, working_tree, packs_dir)
            drifts.append(
                f"[user-libs] orphaned: "
                f"{existing_display} "
                f"present but not in the vendored credbroker source; "
                f"run: make build-self FORCE=1"
            )

    return drifts
