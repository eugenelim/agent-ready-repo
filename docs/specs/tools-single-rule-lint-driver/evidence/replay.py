#!/usr/bin/env python3
"""Replay the T1 corpus against the current tree and diff it byte-for-byte."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

SPD = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("capture", SPD / "capture.py")
cap = importlib.util.module_from_spec(spec)
sys.argv = ["capture", sys.argv[1] if len(sys.argv) > 1 else "."]
spec.loader.exec_module(cap)
import fixtures  # noqa: E402

REPO = Path(sys.argv[1]).resolve()
before = json.loads((SPD / "corpus-before.json").read_text())

# No per-rule filter on purpose: sys.argv is rewritten above for capture.py,
# and replaying all 48 every time also catches a migration that regresses a
# rule other than the one just touched.
bad, checked = [], 0
for rule in cap.RULES:
    now = {"clean": cap.invoke(rule, REPO, REPO, clean=True)}
    for mode, present in (("empty", True), ("absent", False)):
        now[mode] = cap.invoke(rule, cap.fixture_root(rule, present), REPO)
    root = cap.fixture_root(rule, True)
    fixtures.build(rule, root)
    now["violation"] = cap.invoke(rule, root, REPO)

    for mode, got in now.items():
        want = before[rule][mode]
        checked += 1
        for field in ("exit", "stdout", "stderr"):
            if got[field] != want[field]:
                bad.append((rule, mode, field, want[field], got[field]))

print(f"replayed {checked} case(s)")
if not bad:
    print("IDENTICAL — every replayed case matches the pre-refactor capture")
    sys.exit(0)
for rule, mode, field, want, got in bad:
    print(f"\n✖ {rule} [{mode}] {field}")
    print(f"   want: {want!r}"[:400])
    print(f"   got : {got!r}"[:400])
sys.exit(1)
