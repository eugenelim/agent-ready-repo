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
  per RFC-0013 § 4d / spec AC22-AC23:
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

import os
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path

from . import shared_libs

# Pin the source path so a downstream consumer that wants to enumerate
# sources doesn't hardcode the literal repeatedly.
SOURCE_SUBDIR = ".apm/adapter-root-bins"

# Target subtree under the per-scope artifact root. Mirrors the
# `~/.agentbundle/bin/` path at user scope (install-time surface).
TARGET_SUBDIR = Path(".agentbundle") / "bin"

# POSIX mode bits applied after copy. AC22 pins 0o755; Windows
# inherits the DACL from %USERPROFILE% (no explicit chmod call).
EXECUTABLE_MODE = 0o755

# AC22b: shim-companion projection. When a pack ships both
# adapter-root-bins/ and shared-libs/credentials_shim.py, the shim is
# projected as a sibling under `bin/` so that per-platform Tier-2
# backend modules under adapter-root-bins/ (e.g. _sso_keychain_macos.py)
# can resolve `from .credentials_shim import Tier2HardFailError`.
SHIM_COMPANION_BASENAME = "credentials_shim.py"

# AC22b content-grep trigger. Any *.py under adapter-root-bins/ whose
# bytes contain this literal substring is considered shim-dependent;
# the pack must then ship .apm/shared-libs/credentials_shim.py or the
# build hard-errors. Literal-substring match has a documented
# false-positive surface (a docstring quoting the line); accepted for
# v1 because the failure mode is benign (the shim is projected
# unnecessarily — no functional or security regression). AST-walk is
# the documented tightening path.
SHIM_IMPORT_GREP = b"from .credentials_shim import"


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
        if not pack.is_dir() or not (pack / "pack.toml").exists():
            continue
        bins = pack / SOURCE_SUBDIR
        if not bins.is_dir():
            continue
        for src in sorted(bins.glob("*.py")):
            if src.name in sources:
                raise ValueError(
                    f"adapter-root-bins collision: '{src.name}' shipped by both "
                    f"{sources[src.name]} and {src}"
                )
            sources[src.name] = src
    return sources


def _packs_with_adapter_root_bins(packs_dir: Path) -> list[Path]:
    """Return every pack directory whose ``.apm/adapter-root-bins/``
    contains at least one ``*.py`` source. Sorted for determinism.

    Used by the AC22b shim-companion enumeration and by the
    content-grep hard-error rail — both predicate on "the pack ships
    adapter-root-bins/", not on what's inside it.
    """
    out: list[Path] = []
    for pack in sorted(packs_dir.iterdir()):
        if not pack.is_dir() or not (pack / "pack.toml").exists():
            continue
        bins = pack / SOURCE_SUBDIR
        if not bins.is_dir():
            continue
        if any(bins.glob("*.py")):
            out.append(pack)
    return out


def _assert_shim_companion_present(packs_dir: Path) -> None:
    """AC22b hard-error rail (content-based, generalises past _sso_*).

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
            offender_list = ", ".join(offenders)
            raise ValueError(
                f"adapter-root-bins/{{{offender_list}}} imports "
                f".credentials_shim but .apm/shared-libs/credentials_shim.py "
                f"is missing in pack {pack.name!r} — the importing module's "
                f"Tier-2 dispatch would degrade silently on macOS/Windows"
            )


def collect_companion_shim(packs_dir: Path) -> dict[str, Path]:
    """AC22b companion projection enumeration.

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
            # — the AC22b hard-error rail catches the case where they
            # *need* it but don't ship it.
            return {SHIM_COMPANION_BASENAME: shim_source}
    return {}


def collect_pack_root_bins(pack_dir: Path) -> dict[str, Path]:
    """Single-pack, companion-aware enumeration for install-time delivery.

    Returns ``{basename → source_path}`` for one already-resolved
    catalogue ``pack_dir``'s ``.apm/adapter-root-bins/*.py`` plus the AC22b
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

    Deterministic order — drift gates depend on it. Includes the AC22b
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
    """True iff ``proj`` is the AC22b shim-companion (source rooted in
    ``shared-libs/``), not a primary adapter-root-bins target.

    Drives the ``[adapter-root-bins:shim-companion]`` diagnostic
    prefix in ``check_drift`` so the source-side reference reads
    coherently next to its diagnostic class. Derives the comparison
    leaf-name from ``shared_libs.SOURCE_SUBDIR`` so a future rename of
    that constant propagates here automatically.
    """
    shared_libs_leaf = Path(shared_libs.SOURCE_SUBDIR).name
    return proj.source.parent.name == shared_libs_leaf


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

    AC22b: also projects the shim companion when a pack ships both
    ``.apm/adapter-root-bins/`` and ``.apm/shared-libs/credentials_shim.py``.
    AC22b hard-error rail fires before any writes if a pack imports
    the shim but doesn't ship the source.
    """
    _assert_shim_companion_present(packs_dir)
    projections = compute_projections(working_tree, packs_dir)
    expected_targets = {p.target for p in projections}
    for proj in projections:
        proj.target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(proj.source, proj.target)
        if os.name == "posix":
            os.chmod(proj.target, EXECUTABLE_MODE)
    # Orphan removal: any *.py file under <working_tree>/.agentbundle/bin/
    # not claimed by an expected target.
    target_dir = working_tree / TARGET_SUBDIR
    if target_dir.is_dir():
        for existing in sorted(target_dir.glob("*.py")):
            if existing not in expected_targets:
                try:
                    existing.unlink()
                except FileNotFoundError:  # pragma: no cover — race-only
                    pass


def check_drift(working_tree: Path, packs_dir: Path) -> list[str]:
    """Return drift descriptions for ``make build-check``.

    Three outcomes per RFC-0013 § 4d / spec AC22-AC23:
        * **modified** — projected bytes diverge from source
        * **missing** — source exists but projected file absent
        * **orphaned** — projected file present, no source claiming it

    Each description ends with the regeneration command.
    """
    drifts: list[str] = []
    try:
        sources = collect_sources(packs_dir)
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
        if not proj.target.exists():
            drifts.append(
                f"{prefix} missing: "
                f"{proj.target.relative_to(working_tree).as_posix()} "
                f"(source: "
                f"{proj.source.relative_to(packs_dir.parent).as_posix()}); "
                f"run: make build-self FORCE=1"
            )
            continue
        if proj.target.read_bytes() != source_bytes:
            drifts.append(
                f"{prefix} modified: "
                f"{proj.target.relative_to(working_tree).as_posix()} "
                f"diverges from "
                f"{proj.source.relative_to(packs_dir.parent).as_posix()}; "
                f"run: make build-self FORCE=1"
            )

    # Orphan check.
    if target_dir.is_dir():
        for existing in sorted(target_dir.glob("*.py")):
            if existing not in expected_targets:
                drifts.append(
                    f"[adapter-root-bins] orphaned: "
                    f"{existing.relative_to(working_tree).as_posix()} "
                    f"present but no pack ships "
                    f"adapter-root-bins/{existing.name}; "
                    f"run: make build-self FORCE=1"
                )

    return drifts
