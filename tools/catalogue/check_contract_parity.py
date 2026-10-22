#!/usr/bin/env python3
"""Verify contract parity between contracts/ and agentbundle/_data/.

The catalogue specification manifest (contracts/catalogue-spec.toml) names
every contract file and its role. This gate enforces, from that manifest:
  (1) Every member and bundled row has a byte-identical `_data/` copy.
  (2) The packaged inventory equals the generator's rendering of the manifest.
  (3) Every top-level contracts/*.json and *.toml file, other than the manifest
      itself, has a manifest row.
  (4) contracts/README.md lists each member, bundled and vendored row under its
      own role heading, and no repository-only or notice path is a manifest row.

Usage:
  python3 tools/catalogue/check_contract_parity.py   # exits 0 ok / 1 fail

Wired into make build-check via tools/repo/build_gate_chain.py.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path


def _load_generator():
    """Load the sibling generator module by explicit path.

    Loaded this way rather than by plain import so the gate does not depend
    on how the interpreter seeded ``sys.path`` for this script.
    """
    generator = Path(__file__).resolve().parent / "sync_contract_inventory.py"
    spec = importlib.util.spec_from_file_location("sync_contract_inventory", generator)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load contract inventory generator: {generator}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_generator = _load_generator()
load_manifest = _generator.load_manifest
_render = _generator._render

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CONTRACTS = _REPO_ROOT / "contracts"
_DATA = _REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data"
_README = _CONTRACTS / "README.md"
_MANIFEST = "catalogue-spec.toml"

_ROLE_HEADINGS = {
    "member": "Specification members",
    "bundled": "Bundled, not members",
    "vendored": "Vendored",
}
_NON_MANIFEST_HEADINGS = ("Vendored notices", "Repository only")
_CELL = re.compile(r"^\|\s*`([^`]+)`")


def _unlisted_top_level(contracts_dir: Path, rows: list) -> list[str]:
    """Failures for top-level contract files that have no manifest row."""
    listed = {row.path for row in rows}
    return [
        f"  UNLISTED: contracts/{p.name} has no row in {_MANIFEST}"
        for p in sorted(contracts_dir.iterdir(), key=lambda path: path.name)
        if p.is_file()
        and p.suffix in {".json", ".toml"}
        and not p.name.startswith(".")
        and p.name != _MANIFEST
        and p.name not in listed
    ]


def _readme_sections(readme: Path) -> dict[str, set[str]]:
    """First backticked cell of each table row, keyed by `###` heading."""
    sections: dict[str, set[str]] = {}
    current: str | None = None
    in_files = False
    for line in readme.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_files = line.strip() == "## Files"
            current = None
        elif in_files and line.startswith("### "):
            current = line[4:].strip()
            sections.setdefault(current, set())
        elif in_files and current is not None:
            match = _CELL.match(line)
            if match:
                sections[current].add(match.group(1))
    return sections


def _readme_role_mismatches(readme: Path, rows: list) -> list[str]:
    """Failures where the README sections disagree with the manifest roles."""
    sections = _readme_sections(readme)
    failures: list[str] = []
    for role, heading in _ROLE_HEADINGS.items():
        expected = {row.path for row in rows if row.role == role}
        actual = sections.get(heading, set())
        for path in sorted(expected - actual):
            failures.append(f"  README: {path} ({role}) is missing from '{heading}'")
        for path in sorted(actual - expected):
            failures.append(f"  README: {path} under '{heading}' is not a {role} row")
    manifest_paths = {row.path for row in rows}
    for heading in _NON_MANIFEST_HEADINGS:
        for path in sorted(sections.get(heading, set()) & manifest_paths):
            failures.append(f"  README: manifest row {path} is listed under '{heading}'")
    return failures


def main(
    *,
    contracts_dir: Path = _CONTRACTS,
    data_dir: Path = _DATA,
    readme: Path = _README,
) -> int:
    """Run every parity rule; print failures to stderr and return 0 or 1."""
    try:
        rows = load_manifest(contracts_dir)
        expected_inventory = _render(contracts_dir)
    except _generator.ManifestError as exc:
        print(f"check_contract_parity: FAIL - {exc}", file=sys.stderr)
        return 1

    failures: list[str] = []
    synced = [row for row in rows if row.role != "vendored"]
    for row in synced:
        src = contracts_dir / row.path
        dst = data_dir / row.data_name
        if not dst.is_file():
            failures.append(f"  MISSING in _data: contracts/{row.path} has no {row.data_name}")
        elif src.read_bytes() != dst.read_bytes():
            failures.append(f"  DIFFER: contracts/{row.path} != _data/{row.data_name}")

    try:
        actual_inventory = (data_dir / "public-contracts.txt").read_text(encoding="utf-8")
    except FileNotFoundError:
        actual_inventory = ""
    if actual_inventory != expected_inventory:
        failures.append("  DIFFER: public-contracts.txt inventory is stale")

    failures += _unlisted_top_level(contracts_dir, rows)
    failures += _readme_role_mismatches(readme, rows)

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        print(
            f"check_contract_parity: FAIL - {len(failures)} issue(s) found",
            file=sys.stderr,
        )
        return 1

    print(f"check_contract_parity: ok - {len(synced)} contract file(s) synced and byte-identical.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.exit(main())
