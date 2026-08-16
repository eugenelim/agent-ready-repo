#!/usr/bin/env python3
"""Verify contract parity between contracts/ and agentbundle/_data/.

Checks three invariants:
  (1) Every *.schema.json and *.toml file in contracts/ has a byte-identical
      counterpart in agentbundle/_data/, except for the _data/-only allowlist.
  (2) Every file present in both directories is byte-identical.
  (3) The packaged positive inventory exactly names the canonical contracts.

Detects both forgotten syncs (invariant 1) and drift after edits (invariant 2).

Usage:
  python3 tools/catalogue/check_contract_parity.py   # exits 0 ok / 1 fail

Wired into make build-check via tools/repo/build_gate_chain.py.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_render():
    """Load ``_render`` from the sibling generator by explicit path.

    Loaded this way rather than by plain import so the gate does not depend
    on how the interpreter seeded ``sys.path`` for this script.
    """
    generator = Path(__file__).resolve().parent / "sync_contract_inventory.py"
    spec = importlib.util.spec_from_file_location("sync_contract_inventory", generator)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load contract inventory generator: {generator}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._render


_render = _load_render()

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CONTRACTS = _REPO_ROOT / "contracts"
_DATA = _REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data"
_INVENTORY = _DATA / "public-contracts.txt"


def main() -> int:
    failures: list[str] = []

    # Import the generator's own renderer so "the canonical contract set" has
    # exactly one definition. Sorting Path objects here instead would diverge
    # on macOS/Windows, where PurePath ordering is case-folded and the
    # generator's plain string sort is not — `--write` could then produce an
    # inventory this gate rejects.
    expected_inventory = _render()
    contract_files = sorted(
        (
            p
            for p in list(_CONTRACTS.iterdir())
            + list((_CONTRACTS / "jsonschema").glob("knowledge-*.schema.json"))
            if p.is_file()
            and p.suffix in {".json", ".toml"}
            and not p.name.startswith(".")
        ),
        key=lambda path: path.name,
    )

    try:
        actual_inventory = _INVENTORY.read_text(encoding="utf-8")
    except FileNotFoundError:
        actual_inventory = ""
    if actual_inventory != expected_inventory:
        failures.append("  DIFFER: public-contracts.txt inventory is stale")
        print("  DIFFER: public-contracts.txt inventory is stale", file=sys.stderr)

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

    n = len(contract_files)
    print(f"check_contract_parity: ok — {n} contract file(s) synced and byte-identical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
