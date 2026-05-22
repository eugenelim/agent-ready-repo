"""T4: `scaffold` subcommand — drop a pack's seeds/ into --output.

Iterates the pack's `seeds/` subdirectory recursively. For each file:

  - Absent on disk (Tier-1 fast-path):  write the seed.
  - Present, content matches:           no-op (already in sync).
  - Present, content differs (Tier-2):  write a `.upstream.<ext>` companion
                                         next to the original; leave original
                                         untouched.

Every write routes through `safety.write_jailed` (path-jail is non-optional).
`scaffold` does NOT write `.agent-ready-state.toml` — that is `install`'s job.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentbundle import safety
from agentbundle.commands._common import check_spec_version_gate
from agentbundle.config import ConfigError, State, load_pack_toml, load_state


def run(args: argparse.Namespace) -> int:
    """Entry point for `agentbundle scaffold`.

    Returns 0 on success, 1 on error.
    """
    packs_dir = Path(args.packs_dir)
    pack_name = args.pack
    output = Path(args.output)

    pack_dir = packs_dir / pack_name
    seeds_dir = pack_dir / "seeds"

    pack_toml_path = pack_dir / "pack.toml"
    if pack_toml_path.exists():
        try:
            gate = check_spec_version_gate(load_pack_toml(pack_toml_path))
        except ConfigError as exc:
            print(f"scaffold: {exc}", file=sys.stderr)
            return 1
        if gate is not None:
            return gate

    if not seeds_dir.is_dir():
        print(f"no seeds/ in pack {pack_name}", file=sys.stderr)
        return 1

    # Load existing state from the output dir (may be absent — returns empty State).
    state_path = output / ".agent-ready-state.toml"
    state: State = load_state(state_path)

    for seed_file in sorted(seeds_dir.rglob("*")):
        if not seed_file.is_file():
            continue

        relpath = seed_file.relative_to(seeds_dir).as_posix()
        content = seed_file.read_bytes()

        on_disk = output / relpath
        if not on_disk.exists():
            # Absent → Tier-1 fast-path: write the seed.
            safety.write_jailed(output, relpath, content)
            print(f"{relpath}: wrote (new)")
        elif on_disk.read_bytes() == content:
            # Present, content matches → already in sync, no-op.
            print(f"{relpath}: up-to-date (skipped)")
        else:
            # Present, content differs → Tier-2 fast-path: drop companion.
            safety.write_companion(output, relpath, content)
            companion = safety.companion_path(Path(relpath))
            print(f"{relpath}: kept original, wrote companion {companion.as_posix()}")

    return 0
