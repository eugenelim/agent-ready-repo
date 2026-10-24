#!/usr/bin/env python3
"""Check 4 of the catalogue release gate: the CLI ships only a version the site serves.

RFC-0109 D7 check 4. It runs in the tag-push run of ``release-agentbundle.yml``,
in a job both publish jobs need. It reads V, the specification version, from the
``$id`` of each bundled JSON-schema member, then fails unless:

  * the tagged commit holds a snapshot directory and a release row for V;
  * every member the V release row names is bundled with bytes equal to that
    snapshot -- the compared set is the key set of the row's ``members`` table
    (all of the members), taken from the row alone, never from the bundled
    inventory, because the build-check chain that holds that inventory to the
    manifest does not run in this workflow. The row's ``pages`` table is not
    compared: the package bundles no page sources;
  * the bundled inventory lists exactly the JSON-schema subset of that key set,
    each side reduced to its base file name (an absent, unreadable or empty
    inventory fails);
  * the DEPLOYED index lists V with the same member digests as the bundled bytes.

The fetch is check 3's: the opener, bounds and index-acceptance predicate are
imported from ``tools/check-deployed-release-parity.py``, not copied.

Usage:
  python3 tools/catalogue/check_release_gate.py   # exits 0 ok / 1 fail

Pure stdlib.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import urllib.request
from pathlib import Path, PurePosixPath

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
_CONTRACTS = _ROOT / "contracts"
_DATA = _ROOT / "packages" / "agentbundle" / "agentbundle" / "_data"
_INVENTORY = "catalogue-members.txt"
_ID_VERSION = re.compile(r"^https://[^/]+/(?:.+/)?docs/spec/catalogue/(\d+\.\d+)/([^/]+)$")


def _load(name: str, path: Path):  # type: ignore[no-untyped-def]
    """Load a sibling tool by explicit path, independent of sys.path."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_generator = _load("sync_contract_inventory", _HERE / "sync_contract_inventory.py")
parity = _load(
    "check_deployed_release_parity", _ROOT / "tools" / "check-deployed-release-parity.py"
)


class GateError(Exception):
    """The release gate failed; the message names why."""


def _base_name(raw: str, where: str) -> str:
    """Reduce a listed path to its base file name, refusing anything not of that form."""
    base = PurePosixPath(raw).name
    if base in ("", ".", "..") or "\\" in raw or "\x00" in raw:
        raise GateError(f"{where}: {raw!r} does not reduce to a base file name")
    return base


def _bundled(data_dir: Path, base: str) -> bytes:
    path = data_dir / base
    if path.is_symlink() or not path.is_file():
        raise GateError(f"bundled member missing: _data/{base}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise GateError(f"bundled member unreadable: _data/{base}: {exc}") from None


def read_inventory(data_dir: Path) -> list[str]:
    """Base names listed by the bundled inventory; fails when absent, unreadable or empty."""
    try:
        text = _bundled(data_dir, _INVENTORY).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GateError(f"bundled inventory unreadable: _data/{_INVENTORY}: {exc}") from None
    names = [
        _base_name(line.strip(), f"_data/{_INVENTORY}")
        for line in text.splitlines()
        if line.strip()
    ]
    if not names:
        raise GateError(f"bundled inventory empty: _data/{_INVENTORY}")
    return names


def read_version(data_dir: Path, names: list[str]) -> str:
    """V: the one version named by the `$id` of every bundled JSON-schema member."""
    versions: set[str] = set()
    for name in names:
        try:
            document = json.loads(_bundled(data_dir, name))
        except ValueError:
            raise GateError(f"bundled member unreadable: _data/{name}") from None
        identifier = document.get("$id") if isinstance(document, dict) else None
        match = _ID_VERSION.match(identifier) if isinstance(identifier, str) else None
        if match is None or match.group(2) != name:
            raise GateError(f"bundled member has no usable $id: _data/{name}")
        versions.add(match.group(1))
    if len(versions) != 1:
        raise GateError(f"bundled members disagree on the version: {sorted(versions)}")
    return versions.pop()


def check_bundle(contracts_dir: Path, data_dir: Path) -> tuple[str, dict[str, str]]:
    """Local half. Returns V and `{member base name: sha256 of the bundled bytes}`."""
    inventory = read_inventory(data_dir)
    version = read_version(data_dir, inventory)
    try:
        releases, _ = _generator.load_releases(contracts_dir)
    except _generator.ManifestError as exc:
        raise GateError(f"release rows unusable: {exc}") from None
    row = next((r for r in releases if r.version == version), None)
    if row is None:
        raise GateError(f"the tagged commit has no release row for {version}")
    snapshot = _generator.snapshot_dir(contracts_dir, version)
    if snapshot.is_symlink() or not snapshot.is_dir():
        raise GateError(f"the tagged commit has no snapshot for {version}")
    # The compared set comes from the row alone, never from the inventory.
    members = {key: _base_name(key, f"release {version} members") for key in row.members}
    if len(set(members.values())) != len(members):
        raise GateError(f"release {version} members collide after reducing to base names")
    schemas = {base for base in members.values() if base.endswith(".json")}
    repeated = sorted({base for base in inventory if inventory.count(base) > 1})
    if repeated:
        raise GateError(f"bundled inventory lists {repeated} more than once")
    if set(inventory) != schemas:
        raise GateError(
            "bundled inventory does not list exactly the JSON-schema members of "
            f"release {version}: extra {sorted(set(inventory) - schemas)}, "
            f"missing {sorted(schemas - set(inventory))}"
        )
    digests: dict[str, str] = {}
    for key, base in sorted(members.items()):
        snap = snapshot / key
        if snap.is_symlink() or not snap.is_file():
            raise GateError(f"snapshot {version} lacks member {key}")
        data = _bundled(data_dir, base)
        if data != snap.read_bytes():
            raise GateError(f"bundled {base} differs from the {version} snapshot")
        digests[key] = hashlib.sha256(data).hexdigest()
    return version, digests


def check_deployed(version: str, digests: dict[str, str], releases: list[object]) -> None:
    """The deployed index must list V with exactly the bundled member digests."""
    entry = next(
        (e for e in releases if isinstance(e, dict) and e.get("version") == version), None
    )
    if entry is None:
        raise GateError(f"the deployed index does not list release {version}")
    if entry.get("members") != digests:
        raise GateError(f"the deployed index member digests for {version} differ from the bundle")


def run(
    contracts_dir: Path = _CONTRACTS,
    data_dir: Path = _DATA,
    url: str = parity.INDEX_URL,
    opener: urllib.request.OpenerDirector | None = None,
) -> int:
    """Run the gate; return the process exit status."""
    try:
        version, digests = check_bundle(contracts_dir, data_dir)
        releases = parity.fetch_releases(
            url, opener if opener is not None else parity.build_opener()
        )
        check_deployed(version, digests, releases)
    except (GateError, parity.ParityError) as exc:
        print(f"check_release_gate: FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"check_release_gate: OK (the deployed index serves release {version})")
    return 0


def main(argv: list[str]) -> int:
    """CLI entry point. The URL is neither an argument nor an environment input."""
    if argv:
        print("usage: check_release_gate.py (takes no arguments)", file=sys.stderr)
        return 2
    return run()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
