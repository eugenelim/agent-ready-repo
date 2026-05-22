"""Self-host build mode — `make build --self` and `make build --check`.

Renders projections to a temp directory, optionally diffs against
on-disk paths in the working tree, and (for the real-write `--self`
flow) resolves `<adapt:NAME>` markers against `.adapt-discovery.toml`
as a final step. Marker resolution is the ONE place install-time
substitution happens — every other build mode copies markers through
unchanged (spec § Boundaries — Never do).

The `.adapt-discovery.toml` *materialisation* (turning this repo's
concrete values into the toml file) lives in the `adapt-to-project`
skill, out of scope here. T7 ships only the consumer.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

from agentbundle.build.adapters import ADAPTERS
from agentbundle.build.contract import load as load_contract
from agentbundle.build.main import (
    CONTRACT_PATH,
    discover_packs,
    validate_pack_uniqueness,
)

ADAPT_MARKER_RE = re.compile(r"<adapt:([A-Za-z0-9_-]+)>")


def is_dirty_tree(working_tree: Path) -> bool:
    """Return True if `git status --porcelain` against working_tree is non-empty."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=working_tree,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False
    return bool(result.stdout.strip())


def resolve_markers(root: Path, discovery: dict[str, str]) -> int:
    """Walk every text file under root and substitute <adapt:NAME> markers.

    Returns the number of files modified. Binary files are skipped
    (UnicodeDecodeError treated as binary).
    """
    modified = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "<adapt:" not in text:
            continue
        replaced = ADAPT_MARKER_RE.sub(
            lambda match: discovery.get(match.group(1), match.group(0)),
            text,
        )
        if replaced != text:
            path.write_text(replaced, encoding="utf-8")
            modified += 1
    return modified


def project_to_temp(
    working_tree: Path,
    packs_dir: Path,
    contract: dict,
) -> Path:
    """Render every adapter against every pack into a fresh temp dir.

    Returns the temp dir path; caller cleans up.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="agentbundle-self-"))
    packs = discover_packs(packs_dir)
    for pack in packs:
        validate_pack_uniqueness(pack)
    for adapter_name, project in ADAPTERS.items():
        if adapter_name not in contract["adapter"]:
            continue
        adapter_output = temp_dir / adapter_name
        adapter_output.mkdir()
        for pack in packs:
            project(pack.path, contract, adapter_output)
    return temp_dir


def diff_against_working_tree(temp_dir: Path, working_tree: Path) -> list[str]:
    """Return a list of per-file drift lines comparing rendered output
    against the corresponding paths in the working tree."""
    drifts: list[str] = []
    # We compare adapter-by-adapter so each rendered file maps to the
    # working tree's path 1:1 (the adapter wrote into temp_dir/<adapter>/
    # and the working tree carries the same relative path).
    for adapter_root in sorted(temp_dir.iterdir()):
        if not adapter_root.is_dir():
            continue
        for rendered in adapter_root.rglob("*"):
            if not rendered.is_file():
                continue
            relative = rendered.relative_to(adapter_root)
            on_disk = working_tree / relative
            if not on_disk.exists():
                drifts.append(f"missing: {relative}")
                continue
            try:
                if rendered.read_bytes() != on_disk.read_bytes():
                    drifts.append(f"drift: {relative}")
            except OSError as exc:
                drifts.append(f"unreadable: {relative} ({exc})")
    return drifts


def run_self_host(
    working_tree: Path,
    packs_dir: Path,
    dry_run: bool,
    force: bool,
    contract: dict | None = None,
) -> int:
    """Execute `make build --self` (or `--self --dry-run`).

    Returns an exit code: 0 on success/clean diff, non-zero on
    refusal/drift.
    """
    if contract is None:
        contract = load_contract(CONTRACT_PATH)

    if not dry_run and is_dirty_tree(working_tree) and not force:
        print(
            "self-host: working tree is dirty — refusing to write. "
            "Pass --force to override (the dirty-tree check only).",
            file=sys.stderr,
        )
        return 2

    temp_dir = project_to_temp(working_tree, packs_dir, contract)
    try:
        if dry_run:
            drifts = diff_against_working_tree(temp_dir, working_tree)
            if drifts:
                print(
                    f"self-host: dry-run found {len(drifts)} drift(s):",
                    file=sys.stderr,
                )
                for drift in drifts:
                    print(f"  {drift}", file=sys.stderr)
                return 1
            return 0

        # Real write: copy rendered output into the working tree, then
        # resolve markers as the final step.
        for adapter_root in temp_dir.iterdir():
            if not adapter_root.is_dir():
                continue
            for rendered in adapter_root.rglob("*"):
                if not rendered.is_file():
                    continue
                relative = rendered.relative_to(adapter_root)
                destination = working_tree / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(rendered, destination)
        discovery_path = working_tree / ".adapt-discovery.toml"
        if discovery_path.exists():
            discovery_data = tomllib.loads(discovery_path.read_text(encoding="utf-8"))
            discovery_flat = {
                str(key): str(value)
                for key, value in discovery_data.get("adapt", {}).items()
            }
            resolve_markers(working_tree, discovery_flat)
        return 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def cmd_self(args) -> int:
    return run_self_host(
        working_tree=Path(args.output_dir).resolve(),
        packs_dir=Path(args.packs_dir).resolve(),
        dry_run=args.dry_run,
        force=args.force,
    )


def cmd_check(args) -> int:
    """`make build --check` — strict dry-run against the working tree."""
    args.dry_run = True
    args.force = False
    return run_self_host(
        working_tree=Path(args.output_dir).resolve(),
        packs_dir=Path(args.packs_dir).resolve(),
        dry_run=True,
        force=False,
    )
