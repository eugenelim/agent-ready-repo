#!/usr/bin/env python3
"""Verify contract parity between contracts/ and agentbundle/_data/.

Checks two invariants:
  (1) Every *.schema.json and *.toml file in contracts/ has a byte-identical
      counterpart in agentbundle/_data/, except for the _data/-only allowlist.
  (2) Every file present in both directories is byte-identical.

Detects both forgotten syncs (invariant 1) and drift after edits (invariant 2).

Usage:
  python3 tools/catalogue/check_contract_parity.py   # exits 0 ok / 1 fail

Wired into make build-check via tools/repo/build_gate_chain.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CONTRACTS = _REPO_ROOT / "contracts"
_DATA = _REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data"

def main() -> int:
    failures: list[str] = []

    contract_files = sorted(
        p for p in _CONTRACTS.iterdir()
        if p.is_file() and p.suffix in {".json", ".toml"} and not p.name.startswith(".")
    )

    for src in contract_files:
        dst = _DATA / src.name
        if not dst.exists():
            failures.append(f"  MISSING in _data: contracts/{src.name} has no counterpart")
            print(f"  MISSING in _data: contracts/{src.name}", file=sys.stderr)
            continue
        if src.read_bytes() != dst.read_bytes():
            failures.append(f"  DIFFER: contracts/{src.name} != agentbundle/_data/{src.name}")
            print(f"  DIFFER: contracts/{src.name}", file=sys.stderr)

    if failures:
        print(
            f"check_contract_parity: FAIL — {len(failures)} issue(s) found",
            file=sys.stderr,
        )
        return 1

    print(f"check_contract_parity: ok — {len(contract_files)} contract file(s) synced and byte-identical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
