#!/usr/bin/env python3
"""Synchronize the packaged public-contract inventory from contracts/."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONTRACTS = _REPO_ROOT / "contracts"
_INVENTORY = (
    _REPO_ROOT
    / "packages"
    / "agentbundle"
    / "agentbundle"
    / "_data"
    / "public-contracts.txt"
)


def _render() -> str:
    names = []
    names.extend(
        path.name
        for path in _CONTRACTS.iterdir()
        if path.is_file()
        and path.suffix in {".json", ".toml"}
        and not path.name.startswith(".")
    )
    names.extend(
        path.name
        for path in (_CONTRACTS / "jsonschema").glob("knowledge-*.schema.json")
        if path.is_file() and not path.name.startswith(".")
    )
    names = sorted(names)
    return "".join(f"{name}\n" for name in names)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    expected = _render()
    if args.write:
        _INVENTORY.write_text(expected, encoding="utf-8")
        print(f"sync_contract_inventory: wrote {_INVENTORY.relative_to(_REPO_ROOT)}")
        return 0

    try:
        actual = _INVENTORY.read_text(encoding="utf-8")
    except FileNotFoundError:
        actual = ""
    if actual != expected:
        print(
            "sync_contract_inventory: FAIL — run with --write",
            file=sys.stderr,
        )
        return 1
    print("sync_contract_inventory: ok — public-contract inventory is current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
