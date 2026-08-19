#!/usr/bin/env python3
"""Score OKF router routing attempts against the frozen expected-path key.

Report-only per RFC-0087 Errata E1: top-1 and fabricated-path counts are
published, not gated. Security-critical attempts remain a hard gate.

Deterministic and network-free. The valid answer space is derived from the
BUNDLE ON DISK, not from the case file — otherwise a fabricated path that
happens to appear as some case's expected answer would score as real.

Usage: score.py <caller> <bundle_dir> <attempts1.json> <attempts2.json> ...
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path.cwd()  # run from the repository root


def bundle_inventory(bundle: Path) -> set[str]:
    """Every concept path that actually exists, as `concepts/<name>.md`."""
    return {
        f"concepts/{p.name}"
        for p in (bundle / "concepts").glob("*.md")
        if p.name != "index.md"
    }


def main(argv: list[str]) -> int:
    caller, bundle_dir, *attempt_files = argv
    bundle = Path(bundle_dir)
    inventory = bundle_inventory(bundle)
    cases = {
        c["id"]: c
        for c in json.loads(
            (REPO / f"docs/rfc/0087-notes/pilot-cases/{caller}.json").read_text(encoding="utf-8")
        )["cases"]
    }

    runs: list[dict] = []
    for f in attempt_files:
        loaded = json.loads(Path(f).read_text(encoding="utf-8"))
        # Accept either a bare {case_id: path} attempts file or a committed
        # measurement record, which wraps the runs alongside its harness
        # metadata. Without this the committed evidence cannot re-score itself.
        if isinstance(loaded, dict) and isinstance(loaded.get("runs"), list):
            runs.extend(loaded["runs"])
        else:
            runs.append(loaded)
    per_case: dict[str, list[str]] = {cid: [] for cid in cases}
    for run in runs:
        for cid, sel in run.items():
            if cid in per_case:
                per_case[cid].append(sel)

    attempts = fabricated = forbidden_hits = 0
    top1_hits = 0
    sec_total = sec_pass = 0
    misses: list[str] = []

    for cid, case in cases.items():
        expected = case["expected_path"]
        forbidden = set(case.get("forbidden_paths", []))
        for sel in per_case[cid]:
            attempts += 1
            if sel not in inventory:
                fabricated += 1
            if sel in forbidden:
                forbidden_hits += 1
            ok = sel == expected
            top1_hits += ok
            if case.get("security_critical"):
                sec_total += 1
                sec_pass += ok
            if not ok:
                misses.append(f"{cid}: got {sel!r}, key {expected!r}")

    top1 = top1_hits / attempts if attempts else 0.0
    sec_rate = sec_pass / sec_total if sec_total else None

    print(f"caller               {caller}")
    print(f"runs                 {len(runs)}")
    print(f"attempts             {attempts}")
    print(f"top-1 vs key         {top1:.3f}  ({top1_hits}/{attempts})")
    print(f"fabricated paths     {fabricated}")
    print(f"forbidden-path hits  {forbidden_hits}")
    if sec_rate is not None:
        print(f"security-critical    {sec_rate:.3f}  ({sec_pass}/{sec_total})  [HARD GATE]")
    if misses:
        print("misses:")
        for m in misses:
            print(f"  {m}")
    # Report-only: a low top-1 does not fail. A security-critical miss does.
    return 1 if (sec_rate is not None and sec_rate < 1.0) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
