#!/usr/bin/env python3
"""Set every JSON-schema member's top-level `$id` to a release version.

The rewrite is a byte splice: only the `$id` value is replaced, or a `$id` /
`$schema` line is inserted after the opening brace when absent. No other byte
changes, and a second run changes nothing. Pure standard library.
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
_ID_BASE = "https://eugenelim.github.io/agent-ready-repo/docs/spec/catalogue/"
_SCHEMA_URL = "https://json-schema.org/draft/2020-12/schema"
_ID_LINE = re.compile(rb'^  "\$id": "[^"]*",?$', re.MULTILINE)
_SCHEMA_LINE = re.compile(rb'^  "\$schema": ', re.MULTILINE)
_DATA_DIR = _REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data"


def _load_inventory():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(
        "sync_contract_inventory", _HERE / "sync_contract_inventory.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def member_id(version: str, file_name: str) -> str:
    """The absolute `$id` of a member file at a release version."""
    return f"{_ID_BASE}{version}/{file_name}"


def rewrite_bytes(data: bytes, url: str) -> bytes:
    """Return `data` with top-level `$id` set to `url` and `$schema` present.

    Raises `ValueError` if the result does not re-parse to an object whose
    `$id` is `url`.
    """
    match = _ID_LINE.search(data)
    if match:
        line = match.group(0)
        start = match.start() + line.index(b'"', line.index(b":")) + 1
        end = data.index(b'"', start)
        out = data[:start] + url.encode() + data[end:]
    else:
        out = data
    inserts = b""
    if not _SCHEMA_LINE.search(out):
        inserts += f'  "$schema": "{_SCHEMA_URL}",\n'.encode()
    if not match:
        inserts += f'  "$id": "{url}",\n'.encode()
    if inserts:
        if not out.startswith(b"{\n"):
            raise ValueError("schema does not open with a brace line")
        out = out[:2] + inserts + out[2:]
    parsed = json.loads(out)
    if not isinstance(parsed, dict) or parsed.get("$id") != url or "$schema" not in parsed:
        raise ValueError(f"splice did not produce $id {url}")
    return out


def rewrite_file(path: Path, version: str, members: set[str]) -> bool:
    """Rewrite one member file in place; refuse a non-member. True if changed."""
    if path.name not in members:
        raise ValueError(f"{path.name}: not a JSON-schema member")
    data = path.read_bytes()
    out = rewrite_bytes(data, member_id(version, path.name))
    if out != data:
        path.write_bytes(out)
    return out != data


def main(
    argv: list[str] | None = None,
    *,
    contracts_dir: Path = _REPO_ROOT / "contracts",
    data_dir: Path = _DATA_DIR,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="release version, for example 0.1")
    args = parser.parse_args(argv)
    inventory = _load_inventory()
    rows = inventory.json_schema_members(contracts_dir)
    names = {Path(row.path).name for row in rows}
    for row in rows:
        for root in (contracts_dir, data_dir):
            path = root / Path(row.path).name
            if rewrite_file(path, args.version, names):
                print(f"rewrite_member_ids: rewrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
