"""``agentbundle upgrade`` — whole-pack or per-primitive upgrade.

Two shapes:

1. **Whole-pack upgrade** (no ``--skill`` / ``--agent`` / ``--hook`` /
   ``--seed`` / ``--command`` flag):

   - Resolve the catalogue URI to the new pack version directory.
   - Run the spec-version gate.
   - Render the new projection in memory.
   - Walk every (relpath, content) pair; apply the Tier-1/2/3 contract via
     ``safety.classify`` + ``safety.write_jailed``/``safety.write_companion``.
   - Update ``PackState.installed_version`` to ``args.to_version``.
   - If the current state has any ``primitive_versions`` for this pack, emit
     a warning to stderr *before* proceeding (mixed-version surface).

2. **Per-primitive upgrade** (exactly one of the five primitive flags set):

   - Identify the named primitive's file set from the rendered projection
     using a path-segment heuristic (see ``_filter_for_primitive``).
   - Validate that the primitive exists (non-empty filter result → exists).
   - Apply Tier-1/2/3 contract for the filtered file set only.
   - Record ``PackState.primitive_versions[<ptype>][<name>] = args.to_version``.
   - Leave ``PackState.installed_version`` unchanged.

Writes go through ``safety.write_jailed`` — path-jail is non-optional.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

    from agentbundle.config import State


# Mapping from CLI flag attribute name → (primitive-type key, source-dir segment).
# The source-dir segment is the subdirectory name under ``.apm/`` that holds
# the primitive (used by ``_filter_for_primitive`` to scope path matches).
_PRIMITIVE_FLAG_MAP: dict[str, tuple[str, str]] = {
    "skill":   ("skill",        "skills"),
    "agent":   ("agent",        "agents"),
    "hook":    ("hook-body",    "hooks"),
    "seed":    ("seed",         "seeds"),
    "command": ("command",      "commands"),
}


def run(args: "argparse.Namespace") -> int:
    """Entry point for ``agentbundle upgrade``.

    Args:
        args.pack        — pack name (required).
        args.catalogue   — catalogue URI (local path or git+https://...).
        args.to_version  — target version string (required, from ``--to``).
        args.skill       — primitive name for a skill-only upgrade (optional).
        args.agent       — primitive name for an agent-only upgrade (optional).
        args.hook        — primitive name for a hook-only upgrade (optional).
        args.seed        — primitive name for a seed-only upgrade (optional).
        args.command     — primitive name for a command-only upgrade (optional).
        args.root        — repo root (default ``'.'``).

    Returns 0 on success, non-zero on any failure.
    """
    from agentbundle.catalogue import CatalogueError, resolve_catalogue
    from agentbundle.commands._common import check_spec_version_gate
    from agentbundle.config import (
        ConfigError,
        dump_state,
        load_pack_toml,
        load_state,
    )
    from agentbundle.render import render_pack
    from agentbundle import safety

    pack_name: str = args.pack
    catalogue_uri: str = args.catalogue
    to_version: str = args.to_version
    root = Path(args.root).resolve()

    # ── Detect per-primitive flag ─────────────────────────────────────────────
    prim_flag: str | None = None
    prim_name: str | None = None
    for flag_attr, (ptype, _src_dir) in _PRIMITIVE_FLAG_MAP.items():
        val = getattr(args, flag_attr, None)
        if val:
            prim_flag = flag_attr
            prim_name = val
            break

    is_per_primitive = prim_flag is not None

    # ── Resolve catalogue ─────────────────────────────────────────────────────
    try:
        catalogue_dir = resolve_catalogue(catalogue_uri)
    except CatalogueError as exc:
        print(f"upgrade: {exc}", file=sys.stderr)
        return 1

    # ── Locate pack dir ───────────────────────────────────────────────────────
    pack_dir = _locate_pack(catalogue_dir, pack_name)
    if pack_dir is None:
        print(
            f"upgrade: pack {pack_name!r} not found in catalogue at {catalogue_dir}; "
            "expected packs/<pack>/ or <catalogue>/<pack>/",
            file=sys.stderr,
        )
        return 1

    # ── Spec-version gate ─────────────────────────────────────────────────────
    try:
        pack_toml = load_pack_toml(pack_dir / "pack.toml")
    except ConfigError as exc:
        print(f"upgrade: {exc}", file=sys.stderr)
        return 1

    gate = check_spec_version_gate(pack_toml)
    if gate is not None:
        return gate

    # ── Load current state ────────────────────────────────────────────────────
    state_path = root / ".agent-ready-state.toml"
    try:
        state = load_state(state_path)
    except ConfigError as exc:
        print(f"upgrade: {exc}", file=sys.stderr)
        return 1

    if pack_name not in state.packs:
        print(f"upgrade: pack {pack_name!r} not installed", file=sys.stderr)
        return 1

    pack_state = state.packs[pack_name]

    # ── Mixed-version warning (whole-pack only) ────────────────────────────────
    if not is_per_primitive and pack_state.primitive_versions:
        mixed_parts: list[str] = []
        for ptype, pv_map in sorted(pack_state.primitive_versions.items()):
            for pname, ver in sorted(pv_map.items()):
                mixed_parts.append(f"{ptype}/{pname}@{ver}")
        print(
            f"warning: pack {pack_name!r} has mixed-version primitives: "
            f"{mixed_parts}; proceeding with whole-pack upgrade",
            file=sys.stderr,
        )

    # ── Render new projection in memory ──────────────────────────────────────
    try:
        projection = render_pack(pack_dir)
    except Exception as exc:
        print(f"upgrade: render failed for pack {pack_name!r}: {exc}", file=sys.stderr)
        return 1

    # ── Per-primitive: validate and filter ────────────────────────────────────
    if is_per_primitive:
        ptype, src_dir = _PRIMITIVE_FLAG_MAP[prim_flag]
        filtered = _filter_for_primitive(projection, prim_name, src_dir)
        # --hook is atomic over hook-body + matching hook-wiring of the
        # same name (per spec AC #10 — wiring co-moves with body so a
        # per-hook upgrade can never land a torn pair).
        if prim_flag == "hook":
            filtered.update(
                _filter_for_primitive(projection, prim_name, "hook-wiring")
            )
        if not filtered:
            print(
                f"primitive {prim_name!r} not in pack {pack_name}",
                file=sys.stderr,
            )
            return 1
        work_projection = filtered
    else:
        work_projection = projection

    # ── Walk projection; apply Tier contract ──────────────────────────────────
    for relpath, content in sorted(work_projection.items()):
        tier = safety.classify(relpath, root, state)

        if tier is safety.Tier.TIER_3:
            # Path is in the new pack but not yet in state (first upgrade to a
            # newly-added file). Treat as Tier-1 — the upgrade contract is the
            # same as install for new paths.
            tier = safety.Tier.TIER_1

        if tier is safety.Tier.TIER_2:
            try:
                safety.write_companion(root, relpath, content)
            except safety.PathJailError as exc:
                print(f"upgrade: {exc}", file=sys.stderr)
                return 1
            pack_state.files[relpath] = {
                "sha": safety.sha256_bytes(content),
                "from-pack-version": to_version,
            }
        else:
            try:
                safety.write_jailed(root, relpath, content)
            except safety.PathJailError as exc:
                print(f"upgrade: {exc}", file=sys.stderr)
                return 1
            pack_state.files[relpath] = {
                "sha": safety.sha256_bytes(content),
                "from-pack-version": to_version,
            }

    # ── Update state ──────────────────────────────────────────────────────────
    if is_per_primitive:
        # Record per-primitive version override; leave installed_version alone.
        ptype, _src_dir = _PRIMITIVE_FLAG_MAP[prim_flag]
        if ptype not in pack_state.primitive_versions:
            pack_state.primitive_versions[ptype] = {}
        pack_state.primitive_versions[ptype][prim_name] = to_version
    else:
        pack_state.installed_version = to_version

    state_toml_content = dump_state(state)
    try:
        safety.write_jailed(root, ".agent-ready-state.toml", state_toml_content)
    except safety.PathJailError as exc:
        print(f"upgrade: {exc}", file=sys.stderr)
        return 1

    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _locate_pack(catalogue_dir: Path, pack_name: str) -> Path | None:
    """Find the pack directory inside the resolved catalogue.

    Tries two layouts:
      1. ``<catalogue_dir>/packs/<pack_name>/`` — standard catalogue layout.
      2. ``<catalogue_dir>/<pack_name>/``         — catalogue is a pack root.
    """
    candidate_a = catalogue_dir / "packs" / pack_name
    if candidate_a.is_dir() and (candidate_a / "pack.toml").exists():
        return candidate_a
    candidate_b = catalogue_dir / pack_name
    if candidate_b.is_dir() and (candidate_b / "pack.toml").exists():
        return candidate_b
    return None


def _filter_for_primitive(
    projection: dict[str, bytes],
    prim_name: str,
    src_dir: str,
) -> dict[str, bytes]:
    """Return the subset of ``projection`` that belongs to the named primitive.

    Heuristic (v1):
      A projected relpath is considered part of primitive ``prim_name`` of
      source-dir type ``src_dir`` when the relpath contains a path segment
      that starts with ``/<src_dir>/<prim_name>/`` (directory primitive) or
      ``/<src_dir>/<prim_name>.`` (single-file primitive).

    For example, skill ``work-loop`` under source dir ``skills`` matches:
      - ``apm/core/.apm/skills/work-loop/SKILL.md``
      - ``claude-plugins/core/.claude/skills/work-loop/SKILL.md``

    Hook ``pre-commit`` under source dir ``hooks`` matches:
      - ``apm/core/.apm/hooks/pre-commit.sh``
      - ``apm/core/.apm/hooks/pre-commit.py``
      - ``claude-plugins/core/tools/hooks/pre-commit.sh``

    This heuristic intersects naturally with the adapter projection because
    every adapter mirrors the source-dir tree structure from the pack root.
    The heuristic is documented here rather than in a more general schema so
    that a future pack.toml ``source-path`` field can replace it without
    touching test or command logic — just update this function.

    Limitation: two primitives of the same type sharing a name prefix may
    both match (e.g. skill ``work`` and skill ``work-loop``). This is a known
    v1 trade-off; pack authors should use distinct names.
    """
    dir_segment = f"/{src_dir}/{prim_name}/"
    file_segment = f"/{src_dir}/{prim_name}."

    result: dict[str, bytes] = {}
    for relpath, content in projection.items():
        norm = relpath if relpath.startswith("/") else "/" + relpath
        if dir_segment in norm or file_segment in norm:
            result[relpath] = content
    return result
