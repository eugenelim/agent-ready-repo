"""T10: `init-state` subcommand.

Given a working tree that already contains a pack's projection (e.g. from a
manual install or a `make build-self`), hash the on-disk projected files and
write `.agent-ready-state.toml` with their SHA-256s. This is the recovery
path: produce a state file for a tree that doesn't have one.

Algorithm:
  1. Locate `<packs_dir>/<pack>/`; render in-memory via `render.render_pack`
     to learn the projection's relpath set.
  2. For each projected relpath:
     - Compute on-disk SHA at `<root>/<relpath>`.
     - If absent on disk, skip with a warning to stderr.
     - Otherwise add to `PackState.files[relpath] = {sha, from-pack-version}`.
  3. Load existing `.agent-ready-state.toml` (may be absent).
     Replace only `[pack.<args.pack>]`; leave other packs untouched.
  4. Write via `safety.write_jailed(args.root, ".agent-ready-state.toml", ...)`.
  5. Print summary to stdout.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentbundle import config, render, safety
from agentbundle.commands._common import check_spec_version_gate


def run(args: argparse.Namespace) -> int:
    """Entry point called by the CLI dispatcher. Returns exit code."""
    root = Path(args.root).resolve()
    packs_dir = Path(getattr(args, "packs_dir", "packs"))
    if not packs_dir.is_absolute():
        packs_dir = root / packs_dir
    pack_name: str = args.pack
    pack_path = packs_dir / pack_name

    if not pack_path.is_dir():
        print(
            f"error: pack directory not found: {pack_path}",
            file=sys.stderr,
        )
        return 1

    # Read the pack version from pack.toml; refuse if absent (state file with
    # empty version cascades into useless install/uninstall comparisons).
    pack_toml_path = pack_path / "pack.toml"
    try:
        pack_meta = config.load_pack_toml(pack_toml_path)
    except config.ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    gate = check_spec_version_gate(pack_meta)
    if gate is not None:
        return gate

    pack_version = pack_meta.get("pack", {}).get("version")
    if not pack_version:
        print(
            f"error: pack {pack_name!r} has no [pack] version; "
            f"refusing to init-state without a known version anchor",
            file=sys.stderr,
        )
        return 1

    # Render in-memory to get the relpath set.
    try:
        rendered: dict[str, bytes] = render.render_pack(pack_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: render failed for pack '{pack_name}': {exc}", file=sys.stderr)
        return 1

    # Hash on-disk files; skip absent ones with a warning.
    files: dict[str, dict[str, str]] = {}
    skipped = 0
    for relpath in sorted(rendered):
        on_disk = root / relpath
        if not on_disk.exists():
            print(
                f"warning: projected file absent on disk, skipping: {relpath}",
                file=sys.stderr,
            )
            skipped += 1
            continue
        sha = safety.sha256_file(on_disk)
        files[relpath] = {"sha": sha, "from-pack-version": pack_version}

    # Load existing state (may be absent) and replace only this pack's table.
    state_path = root / ".agent-ready-state.toml"
    existing_state = config.load_state(state_path)

    new_pack_state = config.PackState(
        installed_version=pack_version,
        files=files,
    )
    existing_state.packs[pack_name] = new_pack_state

    serialised = config.dump_state(existing_state)
    try:
        safety.write_jailed(root, ".agent-ready-state.toml", serialised)
    except safety.PathJailError as exc:
        print(f"init-state: {exc}", file=sys.stderr)
        return 1

    hashed_count = len(files)
    print(
        f"init-state: {hashed_count} file(s) hashed"
        + (f", {skipped} skipped (absent)" if skipped else "")
        + f" → {state_path}"
    )
    return 0
