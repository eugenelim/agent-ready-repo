#!/usr/bin/env python3
"""Synchronize the packaged public-contract inventory from contracts/."""

# No `from __future__ import annotations`: check_contract_parity.py loads this
# file by path without registering it in sys.modules, which @dataclass needs
# when annotations are strings.
import argparse
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONTRACTS = _REPO_ROOT / "contracts"
_MANIFEST = "catalogue-spec.toml"
_INVENTORY = (
    _REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data" / "public-contracts.txt"
)


class ManifestError(Exception):
    """The catalogue specification manifest is malformed."""


_ROLES = ("member", "bundled", "vendored")


@dataclass(frozen=True)
class ContractRow:
    """One `[[contract]]` row of the manifest."""

    path: str
    role: str
    upstream: str | None

    @property
    def data_name(self) -> str:
        """Name of this contract's packaged copy under `_data/`."""
        if self.role == "vendored":
            return self.path
        return PurePosixPath(self.path).name


def _check_path(index: int, path: object, contracts_dir: Path) -> str:
    label = f"contract row {index}"
    if not isinstance(path, str) or not path:
        raise ManifestError(f"{label}: path must be a non-empty string")
    label = f"{label} ({path})"
    if (
        path.startswith("/")
        or ".." in PurePosixPath(path).parts
        or "\\" in path
        or re.match(r"^[A-Za-z]:", path)
    ):
        raise ManifestError(
            f"{label}: path must be relative, without '..', backslash or drive letter"
        )
    root = contracts_dir.resolve()
    resolved = (contracts_dir / path).resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ManifestError(f"{label}: path must resolve to a regular file inside contracts/")
    return path


def load_manifest(contracts_dir: Path) -> list[ContractRow]:
    """Parse and validate `catalogue-spec.toml`, raising `ManifestError`."""
    try:
        with (contracts_dir / _MANIFEST).open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ManifestError(f"{_MANIFEST}: cannot read manifest: {exc}") from exc
    if not isinstance(data.get("release"), list):
        raise ManifestError(f"{_MANIFEST}: top-level 'release' key must be an array")
    raw_rows = data.get("contract", [])
    if not isinstance(raw_rows, list):
        raise ManifestError(f"{_MANIFEST}: 'contract' must be an array of tables")
    rows: list[ContractRow] = []
    seen_paths: set[str] = set()
    seen_names: dict[str, str] = {}
    for index, raw in enumerate(raw_rows):
        if not isinstance(raw, dict):
            raise ManifestError(f"contract row {index}: must be a table")
        path = _check_path(index, raw.get("path"), contracts_dir)
        label = f"contract row {index} ({path})"
        role = raw.get("role")
        if role not in _ROLES:
            raise ManifestError(f"{label}: unknown role {role!r}")
        upstream = raw.get("upstream")
        if role == "vendored":
            if not isinstance(upstream, str) or not upstream.startswith("https://"):
                raise ManifestError(f"{label}: vendored row needs an https:// upstream")
            try:
                schema_id = json.loads((contracts_dir / path).read_text(encoding="utf-8")).get(
                    "$id"
                )
            except (ValueError, AttributeError) as exc:
                raise ManifestError(f"{label}: cannot read $id: {exc}") from exc
            if upstream != schema_id:
                raise ManifestError(f"{label}: upstream differs from the file's $id")
        else:
            upstream = None
        if path in seen_paths:
            raise ManifestError(f"{label}: duplicate path")
        seen_paths.add(path)
        row = ContractRow(path, role, upstream)
        if role != "vendored":
            if row.data_name in seen_names:
                raise ManifestError(
                    f"{label}: file name {row.data_name!r} already used by "
                    f"{seen_names[row.data_name]}"
                )
            seen_names[row.data_name] = path
        rows.append(row)
    return rows


def _render(contracts_dir: Path = _CONTRACTS) -> str:
    """Sorted `_data/` names of the member and bundled rows, one per line."""
    names = sorted(row.data_name for row in load_manifest(contracts_dir) if row.role != "vendored")
    return "".join(f"{name}\n" for name in names)


def main(
    argv: list[str] | None = None,
    *,
    contracts_dir: Path = _CONTRACTS,
    inventory: Path = _INVENTORY,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    try:
        expected = _render(contracts_dir)
    except ManifestError as exc:
        print(f"sync_contract_inventory: FAIL - {exc}", file=sys.stderr)
        return 1
    if args.write:
        inventory.write_text(expected, encoding="utf-8")
        print(f"sync_contract_inventory: wrote {inventory}")
        return 0

    try:
        actual = inventory.read_text(encoding="utf-8")
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
