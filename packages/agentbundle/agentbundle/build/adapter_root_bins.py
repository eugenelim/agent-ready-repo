"""T6: adapter-root-bins/ build-pipeline primitive class.

Source rule: ``packs/<pack>/.apm/adapter-root-bins/*.py``.
Target rule (self-host, repo scope): project each
``adapter-root-bins/*.py`` file byte-identically to
``<working_tree>/.agentbundle/bin/<basename>.py`` with POSIX mode
``0o755`` (Windows inherits the parent DACL — no explicit chmod).
At user-scope install time the install command projects the same
files to ``$HOME/.agentbundle/bin/<basename>.py``; that surface is
the install command's responsibility, not this module's.

This module owns both halves of the build-pipeline contract for the
new primitive class:

- ``apply_projection(working_tree, packs_dir)`` — write the files.
  Called by ``make build-self``.
- ``check_drift(working_tree, packs_dir)`` — read-only gate. Returns
  a list of drift descriptions (empty list == clean). Three outcomes
  Three rules:
    * **modified** — projected file exists but bytes diverge from source
    * **missing** — source exists but projected file absent
    * **orphaned** — projected file present but source has been removed

Inter-pack basename collision is a hard error at ``collect_sources``
time. v1 ships exactly one source (``sso-broker.py`` in
``credential-brokers``); the rail guards against a future collision.

Path-jail compliance: the target (``.agentbundle/``) is fenced by the
v0.7 contract's ``allowed-prefixes.repo`` for the three user-scope
adapters (``claude-code``, ``kiro``, ``codex``). The projection writes
under that prefix and never anywhere else; no PATH manipulation, no
shell-config edits.
"""

from __future__ import annotations

import contextlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from . import shared_libs
from .projection_io import (
    ProjectionTypeError,
    copy_file_atomic_no_follow,
    ensure_directory_no_follow,
    open_directory_no_follow,
    read_regular_file_no_follow,
    render_diagnostic_path,
)

# Pin the source path so a downstream consumer that wants to enumerate
# sources doesn't hardcode the literal repeatedly.
SOURCE_SUBDIR = ".apm/adapter-root-bins"

# Target subtree under the per-scope artifact root. Mirrors the
# `~/.agentbundle/bin/` path at user scope (install-time surface).
TARGET_SUBDIR = Path(".agentbundle") / "bin"

# POSIX mode bits applied after copy: 0o755. Windows
# inherits the DACL from %USERPROFILE% (no explicit chmod call).
EXECUTABLE_MODE = 0o755

# Shim-companion projection. When a pack ships both
# adapter-root-bins/ and shared-libs/credentials_shim.py, the shim is
# projected as a sibling under `bin/` so that per-platform Tier-2
# backend modules under adapter-root-bins/ (e.g. _sso_keychain_macos.py)
# can resolve `from .credentials_shim import Tier2HardFailError`.
SHIM_COMPANION_BASENAME = "credentials_shim.py"

# Content-grep trigger. Any *.py under adapter-root-bins/ whose
# bytes contain this literal substring is considered shim-dependent;
# the pack must then ship .apm/shared-libs/credentials_shim.py or the
# build hard-errors. Literal-substring match has a documented
# false-positive surface (a docstring quoting the line); accepted for
# v1 because the failure mode is benign (the shim is projected
# unnecessarily — no functional or security regression). AST-walk is
# the documented tightening path.
SHIM_IMPORT_GREP = b"from .credentials_shim import"


def _display(path: Path, base: Path) -> str:
    """Render one path relative to its diagnostic base on one line."""
    return render_diagnostic_path(path.relative_to(base))


@dataclass(frozen=True)
class AdapterRootBinProjection:
    """One concrete projection: copy ``source`` to ``target``."""

    source: Path
    target: Path


def collect_sources(packs_dir: Path) -> dict[str, Path]:
    """Return ``{basename → source_path}`` for every
    ``.apm/adapter-root-bins/*.py`` file across every pack.

    Raises ``ValueError`` on inter-pack basename collision — two
    packs shipping the same basename produces non-deterministic
    projection order and silent overwrites; refuse hard at
    enumeration time.
    """
    sources: dict[str, Path] = {}
    for pack in sorted(packs_dir.iterdir()):
        if not pack.is_dir() or pack.name.startswith("_"):
            continue
        if not (pack / "pack.toml").exists():
            continue
        bins = pack / SOURCE_SUBDIR
        if not bins.is_dir():
            continue
        for src in sorted(bins.glob("*.py")):
            if src.name in sources:
                basename = render_diagnostic_path(Path(src.name))
                first_source = _display(sources[src.name], packs_dir.parent)
                second_source = _display(src, packs_dir.parent)
                raise ValueError(
                    f"adapter-root-bins collision: {basename} shipped by both "
                    f"{first_source} and {second_source}"
                )
            sources[src.name] = src
    return sources


def _packs_with_adapter_root_bins(packs_dir: Path) -> list[Path]:
    """Return every pack directory whose ``.apm/adapter-root-bins/``
    contains at least one ``*.py`` source. Sorted for determinism.

    Used by the shim-companion enumeration and by the
    content-grep hard-error rail — both predicate on "the pack ships
    adapter-root-bins/", not on what's inside it.
    """
    out: list[Path] = []
    for pack in sorted(packs_dir.iterdir()):
        if not pack.is_dir() or pack.name.startswith("_"):
            continue
        if not (pack / "pack.toml").exists():
            continue
        bins = pack / SOURCE_SUBDIR
        if not bins.is_dir():
            continue
        if any(bins.glob("*.py")):
            out.append(pack)
    return out


def _assert_shim_companion_present(packs_dir: Path) -> None:
    """Hard-error rail (content-based, generalises past _sso_*).

    For each pack that ships any ``.apm/adapter-root-bins/*.py``,
    content-grep its sources for the literal substring
    ``from .credentials_shim import``; if any match AND the pack does
    not ship ``.apm/shared-libs/credentials_shim.py``, raise
    ``ValueError`` with the broker-agnostic pinned message. Generalises
    so a future ``_oauth_macos.py`` or any other adapter-root-bins
    module with the same dependency is auto-covered.
    """
    for pack in _packs_with_adapter_root_bins(packs_dir):
        shim_source = pack / shared_libs.SOURCE_SUBDIR / SHIM_COMPANION_BASENAME
        if shim_source.is_file():
            continue  # pack ships the companion — no need to grep.
        bins_dir = pack / SOURCE_SUBDIR
        offenders: list[str] = []
        for src in sorted(bins_dir.glob("*.py")):
            try:
                body = src.read_bytes()
            except OSError:
                continue
            if SHIM_IMPORT_GREP in body:
                offenders.append(src.name)
        if offenders:
            offender_list = ", ".join(
                render_diagnostic_path(Path(SOURCE_SUBDIR) / offender)
                for offender in offenders
            )
            raise ValueError(
                f"{offender_list} imports "
                f".credentials_shim but .apm/shared-libs/credentials_shim.py "
                f"is missing in pack {pack.name!r} — the importing module's "
                f"Tier-2 dispatch would degrade silently on macOS/Windows"
            )


def collect_companion_shim(packs_dir: Path) -> dict[str, Path]:
    """Companion projection enumeration.

    Returns ``{basename → source_path}`` for the shim companion when
    at least one pack ships BOTH ``.apm/adapter-root-bins/`` AND
    ``.apm/shared-libs/credentials_shim.py``. Cross-pack basename
    collision on the shim is detected by ``shared_libs.collect_sources``
    (single source of truth — one error shape, one ownership boundary).
    The companion's target is always
    ``<working_tree>/.agentbundle/bin/credentials_shim.py``; callers
    compose ``working_tree`` themselves.
    """
    shim_sources = shared_libs.collect_sources(packs_dir)
    shim_source = shim_sources.get(SHIM_COMPANION_BASENAME)
    if shim_source is None:
        return {}
    for pack in _packs_with_adapter_root_bins(packs_dir):
        pack_shim = pack / shared_libs.SOURCE_SUBDIR / SHIM_COMPANION_BASENAME
        if pack_shim.is_file():
            # At least one pack ships both adapter-root-bins/ and
            # shared-libs/credentials_shim.py. Project the canonical
            # shim source as the companion. Opt-in by ship-both: packs
            # that ship adapter-root-bins/ alone do not get the shim
            # — the hard-error rail catches the case where they
            # *need* it but don't ship it.
            return {SHIM_COMPANION_BASENAME: shim_source}
    return {}


def collect_pack_root_bins(pack_dir: Path) -> dict[str, Path]:
    """Single-pack, companion-aware enumeration for install-time delivery.

    Returns ``{basename → source_path}`` for one already-resolved
    catalogue ``pack_dir``'s ``.apm/adapter-root-bins/*.py`` plus the
    companion ``credentials_shim.py`` when the pack ships BOTH that
    directory (at least one ``*.py``) AND
    ``.apm/shared-libs/credentials_shim.py`` — the same ship-both opt-in as
    :func:`collect_companion_shim`, scoped to one pack.

    Why not :func:`compute_projections` / :func:`collect_sources`? Those
    walk a multi-pack build-time ``packs/`` root and fold a ``working_tree``
    target into each pair. ``agentbundle install`` operates on a single
    resolved catalogue ``pack_dir`` and owns its own per-scope path-jail, so
    it needs basenames + sources for one pack, not absolute targets under a
    build tree (credbroker-user-scope plan T4 — the install-side seam). The
    install caller composes ``.agentbundle/bin/<basename>`` relpaths from
    :data:`TARGET_SUBDIR` and writes via ``safety.write_jailed`` with POSIX
    :data:`EXECUTABLE_MODE`.

    A bare ``adapter-root-bins/*.py`` glob would miss the companion and land
    the per-platform Tier-2 backends (``_sso_keychain_macos.py`` etc.)
    broken on macOS/Windows — they import ``Tier2HardFailError`` from the
    shim. This helper carries it for exactly the ship-both case.

    The ship-both opt-in here is the single-pack twin of
    :func:`collect_companion_shim` (the multi-pack, ``packs/``-walking
    enumeration). The two predicates are intentionally parallel — a change to
    the opt-in rule must update both.
    """
    # Skip symlinks: install resolves ``pack_dir`` from an untrusted catalogue
    # (a downloaded archive / git checkout), and these bytes land executable
    # (``0o755``) under ``~/.agentbundle/bin/``. A symlinked ``*.py`` pointing
    # out of tree (e.g. ``~/.ssh/id_rsa``) would otherwise read that content
    # into the floor. The build-pipeline ``collect_sources`` twin operates on
    # the trusted in-repo ``packs/`` and intentionally does not filter.
    bins_dir = pack_dir / SOURCE_SUBDIR
    # A symlinked primitive *directory* would let glob enumerate the link
    # target's real (non-symlink) files, smuggling out-of-tree content in.
    if not bins_dir.is_dir() or bins_dir.is_symlink():
        return {}
    sources: dict[str, Path] = {
        src.name: src
        for src in sorted(bins_dir.glob("*.py"))
        if src.is_file() and not src.is_symlink()
    }
    if not sources:
        return {}
    shim_source = pack_dir / shared_libs.SOURCE_SUBDIR / SHIM_COMPANION_BASENAME
    if shim_source.is_file() and not shim_source.is_symlink():
        sources[SHIM_COMPANION_BASENAME] = shim_source
    return sources


def compute_projections(
    working_tree: Path, packs_dir: Path
) -> list[AdapterRootBinProjection]:
    """Return the full list of ``(source → target)`` pairs.

    Deterministic order — drift gates depend on it. Includes the
    shim companion when applicable (opt-in by ship-both).
    """
    sources = collect_sources(packs_dir)
    target_dir = working_tree / TARGET_SUBDIR
    projections: list[AdapterRootBinProjection] = [
        AdapterRootBinProjection(source=sources[name], target=target_dir / name)
        for name in sorted(sources)
    ]
    companion = collect_companion_shim(packs_dir)
    for basename in sorted(companion):
        projections.append(
            AdapterRootBinProjection(
                source=companion[basename],
                target=target_dir / basename,
            )
        )
    return projections


def _is_companion_projection(proj: AdapterRootBinProjection) -> bool:
    """True iff ``proj`` is the shim-companion (source rooted in
    ``shared-libs/``), not a primary adapter-root-bins target.

    Drives the ``[adapter-root-bins:shim-companion]`` diagnostic
    prefix in ``check_drift`` so the source-side reference reads
    coherently next to its diagnostic class. Derives the comparison
    leaf-name from ``shared_libs.SOURCE_SUBDIR`` so a future rename of
    that constant propagates here automatically.
    """
    shared_libs_leaf = Path(shared_libs.SOURCE_SUBDIR).name
    return proj.source.parent.name == shared_libs_leaf


def _target_python_names(target_dir: Path, target_fd: int | None) -> list[str]:
    """List non-directory ``*.py`` entries through an already-held directory."""
    if target_fd is None:
        return [
            path.name for path in target_dir.glob("*.py") if not path.is_dir()
        ]
    names: list[str] = []
    for name in os.listdir(target_fd):  # noqa: PTH208 — directory descriptor
        if not name.endswith(".py"):
            continue
        try:
            entry_stat = os.stat(
                name, dir_fd=target_fd, follow_symlinks=False
            )
        except FileNotFoundError:
            continue
        if not stat.S_ISDIR(entry_stat.st_mode):
            names.append(name)
    return names


def apply_projection(working_tree: Path, packs_dir: Path) -> None:
    """Write every projection target and remove orphans.

    Called by ``make build-self``. Idempotent — running twice produces
    the same on-disk state. POSIX mode bits set to ``0o755`` after
    copy. Windows inherits the parent DACL (no explicit chmod).

    Three drift outcomes resolved here:
      * **missing** → file written from source
      * **modified** → file overwritten from source
      * **orphaned** → file removed (source basename no longer
        shipped by any pack)

    Also projects the shim companion when a pack ships both
    ``.apm/adapter-root-bins/`` and ``.apm/shared-libs/credentials_shim.py``.
    The hard-error rail fires before any writes if a pack imports
    the shim but doesn't ship the source.
    """
    _assert_shim_companion_present(packs_dir)
    projections = compute_projections(working_tree, packs_dir)
    expected_targets = {p.target for p in projections}
    ensure_directory_no_follow(working_tree, TARGET_SUBDIR)
    for proj in projections:
        copy_file_atomic_no_follow(
            proj.source,
            proj.target,
            base=working_tree,
            mode=EXECUTABLE_MODE,
        )
    # Orphan removal: any *.py file under <working_tree>/.agentbundle/bin/
    # not claimed by an expected target.
    target_dir = working_tree / TARGET_SUBDIR
    with open_directory_no_follow(working_tree, TARGET_SUBDIR) as target_fd:
        for name in sorted(_target_python_names(target_dir, target_fd)):
            existing = target_dir / name
            if existing in expected_targets:
                continue
            if target_fd is None:
                with contextlib.suppress(FileNotFoundError):  # pragma: no cover
                    existing.unlink()
            else:
                with contextlib.suppress(FileNotFoundError):  # pragma: no cover
                    os.unlink(name, dir_fd=target_fd)


def check_drift(working_tree: Path, packs_dir: Path) -> list[str]:
    """Return drift descriptions for ``make build-check``.

    Three outcomes:
        * **modified** — projected bytes diverge from source
        * **missing** — source exists but projected file absent
        * **orphaned** — projected file present, no source claiming it

    Each description ends with the regeneration command.
    """
    drifts: list[str] = []
    try:
        collect_sources(packs_dir)
    except ValueError as exc:
        drifts.append(f"[adapter-root-bins] {exc}; run: make build-self")
        return drifts
    try:
        _assert_shim_companion_present(packs_dir)
    except ValueError as exc:
        drifts.append(f"[adapter-root-bins:shim-companion] {exc}; run: make build-self")
        return drifts

    target_dir = working_tree / TARGET_SUBDIR
    expected_targets: set[Path] = set()

    current = working_tree
    for part in TARGET_SUBDIR.parts:
        current /= part
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            break
        except OSError as exc:
            drifts.append(
                f"[adapter-root-bins] unreadable: "
                f"{_display(current, working_tree)}: {exc}"
            )
            return drifts
        if not stat.S_ISDIR(current_stat.st_mode):
            kind = (
                "a symlink"
                if stat.S_ISLNK(current_stat.st_mode)
                else "not a directory"
            )
            drifts.append(
                f"[adapter-root-bins] type mismatch: "
                f"{_display(current, working_tree)} is {kind}; "
                f"expected a directory inside the working tree; "
                f"run: make build-self FORCE=1"
            )
            return drifts

    for proj in compute_projections(working_tree, packs_dir):
        expected_targets.add(proj.target)
        prefix = (
            "[adapter-root-bins:shim-companion]"
            if _is_companion_projection(proj)
            else "[adapter-root-bins]"
        )
        try:
            source_bytes = proj.source.read_bytes()
        except OSError as exc:  # pragma: no cover — defensive
            drifts.append(f"{prefix} source unreadable: {exc}")
            continue
        try:
            target_bytes, target_stat = read_regular_file_no_follow(
                proj.target,
                base=working_tree,
            )
        except FileNotFoundError:
            drifts.append(
                f"{prefix} missing: "
                f"{_display(proj.target, working_tree)} "
                f"(source: "
                f"{_display(proj.source, packs_dir.parent)}); "
                f"run: make build-self FORCE=1"
            )
            continue
        except ProjectionTypeError as exc:
            drifts.append(
                f"{prefix} type mismatch: "
                f"{_display(proj.target, working_tree)} {exc}; "
                f"expected a regular projected file; run: make build-self FORCE=1"
            )
            continue
        except OSError as exc:
            drifts.append(
                f"{prefix} unreadable: "
                f"{_display(proj.target, working_tree)}: {exc}"
            )
            continue
        if (
            os.name == "posix"
            and stat.S_IMODE(target_stat.st_mode) != EXECUTABLE_MODE
        ):
            drifts.append(
                f"{prefix} mode drift: "
                f"{_display(proj.target, working_tree)} has "
                f"{oct(stat.S_IMODE(target_stat.st_mode))}, expected "
                f"{oct(EXECUTABLE_MODE)}; run: make build-self FORCE=1"
            )
        if target_bytes != source_bytes:
            drifts.append(
                f"{prefix} modified: "
                f"{_display(proj.target, working_tree)} "
                f"diverges from "
                f"{_display(proj.source, packs_dir.parent)}; "
                f"run: make build-self FORCE=1"
            )

    # Orphan check.
    try:
        with open_directory_no_follow(working_tree, TARGET_SUBDIR) as target_fd:
            target_names = _target_python_names(target_dir, target_fd)
    except FileNotFoundError:
        target_names = []
    except OSError as exc:
        drifts.append(
            f"[adapter-root-bins] unreadable: "
            f"{render_diagnostic_path(TARGET_SUBDIR)}: {exc}; "
            f"run: make build-self FORCE=1"
        )
        target_names = []
    for name in sorted(target_names):
        existing = target_dir / name
        if existing not in expected_targets:
            source_hint = render_diagnostic_path(Path("adapter-root-bins") / name)
            drifts.append(
                f"[adapter-root-bins] orphaned: "
                f"{render_diagnostic_path(existing.relative_to(working_tree))} "
                f"present but no pack ships "
                f"{source_hint}; "
                f"run: make build-self FORCE=1"
            )

    return drifts
