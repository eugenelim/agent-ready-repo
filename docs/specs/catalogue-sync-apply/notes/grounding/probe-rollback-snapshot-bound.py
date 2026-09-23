#!/usr/bin/env python3
"""Probe: how large is the in-memory rollback snapshot the apply path holds?

The plan's named uncertainty. The snapshot holds the prior bytes of every
write-set path that exists, alongside the replay's own `file_bytes`. If the
peak is large enough to matter, the plan's mechanism is wrong.

Run from the repository root:
    python3 docs/specs/catalogue-sync-apply/notes/grounding/probe-rollback-snapshot-bound.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path.cwd()
sys.path.insert(0, str(REPO_ROOT / "packages" / "agentbundle"))

from agentbundle.catalogue_tooling.initialise_self_hosted import (  # noqa: E402
    SelfHostedInitConfig,
    replay_derivation,
)


def mib(n: int) -> str:
    return f"{n / 1024 / 1024:.1f} MiB"


for tooling in ("external", "vendored"):
    with tempfile.TemporaryDirectory() as tmp:
        cfg = SelfHostedInitConfig(
            target=Path(tmp) / "derived",
            source=REPO_ROOT,
            tooling=tooling,
            attribution="white-label",
            guides="selected",
            name="probe",
            display_name="Probe",
            description="probe",
            owner_name="Probe",
            owner_email="probe@example.invalid",
            dry_run=True,
        )
        replay = replay_derivation(cfg, interactive=False)
        total = sum(len(b) for b in replay.file_bytes.values())
        largest = max(len(b) for b in replay.file_bytes.values())
        print(f"tooling={tooling}")
        print(f"  planned paths      : {len(replay.file_bytes)}")
        print(f"  replay file_bytes  : {mib(total)}")
        print(f"  largest single file: {mib(largest)}")
        print(f"  worst-case peak    : {mib(total * 2)} "
              f"(replay + a full-run snapshot)")
