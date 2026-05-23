"""``agentbundle install`` — constrained-network pack installer.

Steps:
  1. Resolve the catalogue URI to a local directory (``catalogue.resolve_catalogue``).
  2. Locate the pack directory inside the catalogue.
  3. Spec-version gate: refuse if pack's major spec version != CLI's major.
  4. Render the pack projection in memory (``render.render_pack``).
  5. Walk each (relpath, bytes) pair:
       - Classify against existing state + on-disk content.
       - Tier-1 (or absent): write via ``safety.write_jailed``; record SHA.
       - Tier-2: write companion via ``safety.write_companion``; leave original.
       - Tier-3: skip entirely.
  6. Merge new pack table into existing ``.agent-ready-state.toml`` leaving
     other packs untouched; write atomically via ``safety.write_jailed``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

    from agentbundle.config import State
    from agentbundle.safety import Tier


def run(args: "argparse.Namespace") -> int:
    """Entry point for ``agentbundle install``.

    Args:
        args.pack       — pack name to install (required).
        args.catalogue  — catalogue URI (local path or git+https://...).
        args.output     — destination root directory (default '.').

    Returns 0 on success, non-zero on any failure.
    """
    from agentbundle.catalogue import CatalogueError, resolve_catalogue
    from agentbundle.commands._common import check_spec_version_gate
    from agentbundle.config import (
        ConfigError,
        PackState,
        dump_state,
        load_pack_toml,
        load_state,
    )
    from agentbundle.render import render_pack
    from agentbundle import safety

    pack_name: str = args.pack
    catalogue_uri: str = args.catalogue
    output_root = Path(args.output).resolve()

    # ── Step 1: Resolve catalogue ─────────────────────────────────────────────
    try:
        catalogue_dir = resolve_catalogue(catalogue_uri)
    except CatalogueError as exc:
        print(f"install: {exc}", file=sys.stderr)
        return 1

    # ── Step 2: Locate the pack directory ─────────────────────────────────────
    pack_dir = _locate_pack(catalogue_dir, pack_name)
    if pack_dir is None:
        print(
            f"install: pack {pack_name!r} not found in catalogue at {catalogue_dir}; "
            "expected packs/<pack>/ or <catalogue>/<pack>/",
            file=sys.stderr,
        )
        return 1

    # ── Step 3: Spec-version gate ─────────────────────────────────────────────
    try:
        pack_toml = load_pack_toml(pack_dir / "pack.toml")
    except ConfigError as exc:
        print(f"install: {exc}", file=sys.stderr)
        return 1

    gate = check_spec_version_gate(pack_toml)
    if gate is not None:
        return gate

    # ── Step 4: Render projection in memory ───────────────────────────────────
    try:
        projection = render_pack(pack_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"install: render failed for pack {pack_name!r}: {exc}", file=sys.stderr)
        return 1

    # ── Step 5: Load existing state (for Tier classification) ─────────────────
    state_path = output_root / ".agent-ready-state.toml"
    try:
        state = load_state(state_path)
    except ConfigError as exc:
        print(f"install: {exc}", file=sys.stderr)
        return 1

    # Build a fresh PackState for the pack being installed; we populate
    # ``files`` as we walk the projection.
    pack_version: str = pack_toml.get("pack", {}).get("version", "0.0.0")
    # Carry forward per-primitive mixed-version overrides from a prior
    # install/upgrade so a re-install doesn't silently drop the warning
    # that a subsequent whole-pack upgrade should surface (AC #10's
    # second clause).
    prior = state.packs.get(pack_name)
    new_pack_state = PackState(
        installed_version=pack_version,
        source="agent-ready-repo",
        install_route="cli",
        primitives=_collect_primitives(pack_dir),
        files={},
        primitive_versions=dict(prior.primitive_versions) if prior else {},
    )

    # ── Step 5 (walk) ─────────────────────────────────────────────────────────
    for relpath, content in sorted(projection.items()):
        # Classify this projected path against the *current* on-disk state:
        #   - If the path is already in state (from a prior install of this
        #     same pack) and the on-disk SHA matches → Tier-1 (safe overwrite).
        #   - If the path is already in state and the SHA has drifted → Tier-2
        #     (adopter has edited; write companion only).
        #   - If the path is not in any pack's state yet, but exists on disk
        #     with content that doesn't match the bundle → Tier-2 (same rule:
        #     something is there that the CLI didn't put there).
        #   - If not on disk at all OR matches bundle content → Tier-1.
        #
        # Note: we do NOT use safety.classify() here because that function's
        # Tier-3 branch is "not in state.projected_paths()" — which would
        # incorrectly mark every newly-installed path as Tier-3 on a fresh
        # install. The install command's contract is different: EVERY path in
        # the incoming projection is adapter-contract space; we just need to
        # know whether it's safe to overwrite or not.
        tier = _classify_for_install(
            relpath, output_root, content, state, pack_name=pack_name,
        )

        if tier is safety.Tier.TIER_2:
            # Adopter has edited — write companion, leave original untouched.
            try:
                safety.write_companion(output_root, relpath, content)
            except safety.PathJailError as exc:
                print(f"install: {exc}", file=sys.stderr)
                return 1
            # Record the bundle's SHA in state; the file itself is adopter-owned.
            new_pack_state.files[relpath] = {
                "sha": safety.sha256_bytes(content),
                "from-pack-version": pack_version,
            }
        else:
            # Tier-1 (including absent or not-yet-in-state): write outright.
            try:
                safety.write_jailed(output_root, relpath, content)
            except safety.PathJailError as exc:
                print(f"install: {exc}", file=sys.stderr)
                return 1
            new_pack_state.files[relpath] = {
                "sha": safety.sha256_bytes(content),
                "from-pack-version": pack_version,
            }

    # ── Step 6: Merge state — add/replace this pack's table ───────────────────
    state.packs[pack_name] = new_pack_state
    state_toml_content = dump_state(state)
    try:
        safety.write_jailed(output_root, ".agent-ready-state.toml", state_toml_content)
    except safety.PathJailError as exc:
        print(f"install: {exc}", file=sys.stderr)
        return 1

    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _classify_for_install(
    relpath: str,
    root: Path,
    incoming_content: bytes,
    state: "State",
    *,
    pack_name: str = "",
) -> "Tier":
    """Classify a projected relpath for the install command.

    Unlike ``safety.classify``, this function treats every incoming projected
    path as adapter-contract space (never Tier-3). The distinction is only
    whether the on-disk copy is safe to overwrite:

      - Not on disk OR content matches incoming bundle → Tier-1.
      - On disk with content that matches the *recorded* SHA (from a prior
        install of the same pack at the same version) → Tier-1.
      - On disk with content that differs from the bundle AND from the
        recorded SHA → Tier-2 (adopter has edited).
    """
    from agentbundle import safety as _safety

    on_disk = root / relpath
    if not on_disk.exists():
        return _safety.Tier.TIER_1

    on_disk_sha = _safety.sha256_file(on_disk)
    incoming_sha = _safety.sha256_bytes(incoming_content)

    # If the on-disk file is already the bundle's content → Tier-1 (idempotent).
    if on_disk_sha == incoming_sha:
        return _safety.Tier.TIER_1

    # Check if it matches a recorded SHA in *any* pack (i.e. it's a prior
    # Tier-1 install that was not edited by the adopter). If the match
    # comes from a different pack than the one being installed, warn —
    # silent overwrite of another pack's content would hide a real
    # projection conflict.
    for other_pack_name, ps in state.packs.items():
        recorded = ps.file_sha(relpath)
        if recorded and on_disk_sha == recorded:
            if pack_name and other_pack_name and other_pack_name != pack_name:
                import sys
                print(
                    f"install: warning: {relpath!r} is also recorded under "
                    f"pack {other_pack_name!r}; the two packs project the same path",
                    file=sys.stderr,
                )
            return _safety.Tier.TIER_1

    # On disk, different from the bundle, and no matching prior-install SHA —
    # the adopter has edited it.
    return _safety.Tier.TIER_2


def _locate_pack(catalogue_dir: Path, pack_name: str) -> Path | None:
    """Find the pack directory inside the resolved catalogue.

    Tries two layouts:
      1. ``<catalogue_dir>/packs/<pack_name>/`` — standard catalogue layout.
      2. ``<catalogue_dir>/<pack_name>/``         — catalogue is a pack root.

    Returns ``None`` if neither exists.
    """
    candidate_a = catalogue_dir / "packs" / pack_name
    if candidate_a.is_dir() and (candidate_a / "pack.toml").exists():
        return candidate_a
    candidate_b = catalogue_dir / pack_name
    if candidate_b.is_dir() and (candidate_b / "pack.toml").exists():
        return candidate_b
    return None


def _collect_primitives(pack_dir: Path) -> list[str]:
    """Enumerate which primitive types exist under ``.apm/``."""
    apm = pack_dir / ".apm"
    if not apm.exists():
        return []
    names = []
    for subdir_name, ptype in (
        ("skills", "skill"),
        ("agents", "agent"),
        ("hooks", "hook-body"),
        ("hook-wiring", "hook-wiring"),
        ("commands", "command"),
    ):
        if (apm / subdir_name).exists():
            names.append(ptype)
    return names
