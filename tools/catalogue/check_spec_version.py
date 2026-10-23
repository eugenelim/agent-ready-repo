#!/usr/bin/env python3
"""Check 2 of the catalogue release gate: member `$id`s agree with the releases.

Every JSON-schema member's `$id` must name one version V. When the member bytes
equal the latest release's snapshot, V must be that latest release. When they
differ, V must be an unreleased version that has no snapshot yet. Fix a failure
by running `tools/catalogue/rewrite_member_ids.py --version <V>`.

Usage:
  python3 tools/catalogue/check_spec_version.py   # exits 0 ok / 1 fail

Wired into make build-check via tools/repo/build_gate_chain.py. Pure stdlib.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_CONTRACTS = _HERE.parents[1] / "contracts"
_ID_FORM = re.compile(
    r"^https://eugenelim\.github\.io/agent-ready-repo/docs/spec/catalogue/"
    r"([0-9]+\.[0-9]+)/([^/]+)$"
)
_FIX = "run tools/catalogue/rewrite_member_ids.py --version <V> to set the member $ids"


def _load_generator():  # type: ignore[no-untyped-def]
    """Load the sibling generator by explicit path, independent of sys.path."""
    path = _HERE / "sync_contract_inventory.py"
    spec = importlib.util.spec_from_file_location("sync_contract_inventory", path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load contract inventory generator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_generator = _load_generator()


def _member_versions(contracts_dir: Path, names: list[str]) -> tuple[set[str], list[str]]:
    """Versions named by the members' `$id`s, and a failure per malformed `$id`."""
    versions: set[str] = set()
    failures: list[str] = []
    for name in names:
        try:
            value = json.loads((contracts_dir / name).read_text(encoding="utf-8")).get("$id")
        except (OSError, ValueError, AttributeError) as exc:
            failures.append(f"  {name}: cannot read $id ({exc})")
            continue
        match = _ID_FORM.match(value) if isinstance(value, str) else None
        if match is None or match.group(2) != name:
            failures.append(f"  {name}: $id {value!r} is not a versioned catalogue $id")
        else:
            versions.add(match.group(1))
    return versions, failures


def check(contracts_dir: Path = _CONTRACTS) -> list[str]:
    """Every version-consistency failure for the tree under `contracts_dir`."""
    names = [Path(r.path).name for r in _generator.json_schema_members(contracts_dir)]
    versions, failures = _member_versions(contracts_dir, names)
    if failures:
        return failures
    if len(versions) != 1:
        return [f"  member $ids name more than one version: {sorted(versions)}"]
    (version,) = versions
    releases, _ = _generator.load_releases(contracts_dir)
    latest = _generator.latest_release(releases)
    released = {row.version for row in releases}
    unchanged = latest is not None and all(
        (snap := _generator.snapshot_dir(contracts_dir, latest.version) / name).is_file()
        and snap.read_bytes() == (contracts_dir / name).read_bytes()
        for name in names
    )
    if unchanged and latest is not None:
        if version != latest.version:
            return [
                f"  member bytes equal release {latest.version} but $ids name {version}",
            ]
        return []
    if version in released or _generator.snapshot_dir(contracts_dir, version).exists():
        return [
            f"  member bytes differ from the latest release but $ids name {version}, "
            "a released version",
        ]
    return []


def main(*, contracts_dir: Path = _CONTRACTS) -> int:
    """Print failures to stderr and return 0 or 1."""
    try:
        failures = check(contracts_dir)
    except _generator.ManifestError as exc:
        print(f"check_spec_version: FAIL - {exc}", file=sys.stderr)
        return 1
    if failures:
        print("\n".join(failures), file=sys.stderr)
        print(f"check_spec_version: FAIL - {_FIX}", file=sys.stderr)
        return 1
    print("check_spec_version: ok - member $ids agree with the release snapshots.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
