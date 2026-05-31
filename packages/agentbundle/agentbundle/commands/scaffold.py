"""T4: `scaffold` subcommand — drop a pack's seeds/ into --output.

Iterates the pack's `seeds/` subdirectory recursively. For each file:

  - Absent on disk (Tier-1 fast-path):  write the seed.
  - Present, content matches:           no-op (already in sync).
  - Present, content differs (Tier-2):  write a `.upstream.<ext>` companion
                                         next to the original; leave original
                                         untouched.

Every write routes through `safety.write_jailed` (path-jail is non-optional).
`scaffold` does NOT write `.agentbundle-state.toml` — that is `install`'s job.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentbundle import safety
from agentbundle.commands._common import check_spec_version_gate, deliver_seeds
from agentbundle.config import ConfigError, load_pack_toml


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

    # Seed delivery (Tier-1/2/3, composition-fragment handling) is shared with
    # `install`; see ``commands._common.deliver_seeds``. `scaffold` does NOT
    # write `.agentbundle-state.toml` — that is `install`'s job.
    try:
        deliveries = deliver_seeds(seeds_dir, output)
    except safety.PathJailError as exc:
        print(f"scaffold: {exc}", file=sys.stderr)
        return 1

    for rec in deliveries:
        if rec.action == "wrote":
            print(f"{rec.relpath}: wrote (new)")
        elif rec.action == "skipped":
            print(f"{rec.relpath}: up-to-date (skipped)")
        else:  # companion
            print(f"{rec.relpath}: kept original, wrote companion {rec.companion_relpath}")

    return 0
