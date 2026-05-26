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

# Pin the source path so a downstream consumer that wants to enumerate
# sources doesn't hardcode the literal repeatedly.
SOURCE_SUBDIR = ".apm/adapter-root-bins"

# Target subtree under the per-scope artifact root. Mirrors the
# `~/.agentbundle/bin/` path at user scope (install-time surface).
TARGET_SUBDIR = Path(".agentbundle") / "bin"

# POSIX mode bits applied after copy. AC22 pins 0o755; Windows
# inherits the DACL from %USERPROFILE% (no explicit chmod call).
EXECUTABLE_MODE = 0o755


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


def compute_projections(
    working_tree: Path, packs_dir: Path
) -> list[AdapterRootBinProjection]:
    """Return the full list of ``(source → target)`` pairs.

    Deterministic order — drift gates depend on it.
    """
    sources = collect_sources(packs_dir)
    target_dir = working_tree / TARGET_SUBDIR
    return [
        AdapterRootBinProjection(source=sources[name], target=target_dir / name)
        for name in sorted(sources)
    ]


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
    """
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

    target_dir = working_tree / TARGET_SUBDIR
    expected_targets: set[Path] = set()

    for proj in compute_projections(working_tree, packs_dir):
        expected_targets.add(proj.target)
        try:
            source_bytes = proj.source.read_bytes()
        except OSError as exc:  # pragma: no cover — defensive
            drifts.append(f"[adapter-root-bins] source unreadable: {exc}")
            continue
        if not proj.target.exists():
            drifts.append(
                f"[adapter-root-bins] missing: "
                f"{proj.target.relative_to(working_tree).as_posix()} "
                f"(source: "
                f"{proj.source.relative_to(packs_dir.parent).as_posix()}); "
                f"run: make build-self FORCE=1"
            )
            continue
        if proj.target.read_bytes() != source_bytes:
            drifts.append(
                f"[adapter-root-bins] modified: "
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
