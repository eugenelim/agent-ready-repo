#!/usr/bin/env python3
"""Probe: how many recorded paths does a run's own modes fail to plan?

The replayed set is mode-dependent; the recorded set is not. A run whose modes
plan fewer paths than the derivation did sees the difference as stale, and the
removal guard's sha256 check admits every one the adopter has not edited. This
measures the gap per mode, and how much of it any named subtree exclusion
would cover.

Run from the repository root:
    python3 docs/specs/catalogue-sync-apply/notes/grounding/probe-mode-asymmetry.py
"""
from __future__ import annotations

import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "packages" / "agentbundle"))

from agentbundle.catalogue_tooling.initialise_self_hosted import (  # noqa: E402
    SelfHostedInitConfig,
    replay_derivation,
)

# The two subtrees the write-set definition names as deferred to phase 4.
NAMED_EXCLUSIONS = (".agentbundle/tooling/agentbundle/", "packages/credbroker/")


def planned(**modes: str) -> set[str]:
    base = {"tooling": "external", "attribution": "white-label", "guides": "selected"}
    base.update(modes)
    with tempfile.TemporaryDirectory() as tmp:
        cfg = SelfHostedInitConfig(
            target=Path(tmp) / "derived",
            source=Path.cwd(),
            name="probe",
            display_name="Probe",
            description="probe",
            owner_name="Probe",
            owner_email="probe@example.invalid",
            dry_run=True,
            **base,
        )
        return set(replay_derivation(cfg, interactive=False).file_bytes)


def main() -> int:
    # sync's own defaults, from catalogue_sync.run.
    default = planned()
    print(f"a default sync run plans {len(default)} paths")
    print("(sync defaults: attribution=white-label, tooling=external, guides=selected)\n")

    for label, modes in (
        ("--tooling vendored", {"tooling": "vendored"}),
        ("--guides-mode none", {"guides": "none"}),
        ("--guides-mode selected", {"guides": "selected"}),
    ):
        built = planned(**modes)
        orphaned = built - default
        print(f"tree derived with {label}: {len(built)} recorded")
        print(f"  orphaned by a default sync run: {len(orphaned)}")
        if orphaned:
            covered = {
                path for path in orphaned if path.startswith(NAMED_EXCLUSIONS)
            }
            print(f"    covered by a named subtree exclusion: {len(covered)}")
            print(f"    covered by nothing:                   {len(orphaned - covered)}")
            for prefix, count in sorted(
                Counter(
                    "/".join(p.split("/")[:4]) for p in (orphaned - covered)
                ).items()
            ):
                print(f"      {count:5}  {prefix}/")
    print(
        "\nthe hazard is mode asymmetry, not a missing subtree: naming subtrees "
        "repairs the measured instance and leaves the class"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
