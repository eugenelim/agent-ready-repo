#!/usr/bin/env python3
"""Probe: does safety.write_jailed's portable-name gate admit every path a real
replay plans?

The apply path routes every file write through `safety.write_jailed`, which
calls `assert_portable_name` first. If that gate rejects any path the replay
actually produces, the mechanism is wrong and the plan must change. Replays
this repository as the source with no recorded recipe, which selects every
shipped pack — a superset of any real adopter selection.

Run from the repository root:
    python3 docs/specs/catalogue-sync-apply/notes/grounding/\
        probe-jailed-write-admits-planned-paths.py
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
from agentbundle.safety import assert_portable_name, companion_path  # noqa: E402

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
        planned = sorted(replay.file_bytes)
        rejected_direct: list[tuple[str, str]] = []
        rejected_companion: list[tuple[str, str]] = []
        for rel in planned:
            try:
                assert_portable_name(rel)
            except Exception as exc:
                rejected_direct.append((rel, f"{type(exc).__name__}: {exc}"))
            try:
                assert_portable_name(str(companion_path(Path(rel))))
            except Exception as exc:
                rejected_companion.append((rel, f"{type(exc).__name__}: {exc}"))
        print(f"tooling={tooling}: {len(planned)} planned paths")
        print(f"  rejected as a direct write:    {len(rejected_direct)}")
        for rel, why in rejected_direct[:5]:
            print(f"    {rel} -> {why}")
        print(f"  rejected as a companion write: {len(rejected_companion)}")
        for rel, why in rejected_companion[:5]:
            print(f"    {rel} -> {why}")
        subtrees = sorted({rel.split("/")[0] for rel in planned})
        print(f"  top-level entries: {subtrees}")
