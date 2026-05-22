"""Self-host build mode — `make build --self` and `make build --check`.

Real-write (`--self` without `--dry-run`) projects adapters **directly
into the working tree**, so the adapters' merge / splice logic operates
against the working tree's existing content — that's what makes
`merge-managed-key-only` (Claude Code) and `preserve-outside-block`
(Codex) correct against the adopter's actual files.

Dry-run (`--self --dry-run`, and `--check`) clones the adapter target
subtree (`.claude/`, `tools/hooks/`, `.github/`, `AGENTS.md`) into a
fresh temp dir first, projects into the clone, then diffs the clone
against the working tree. The clone-then-project pattern keeps the
existing-content merge semantics intact under dry-run too.

Marker resolution (`<adapt:NAME>` → discovery value) is the ONE place
install-time substitution happens — every other build mode copies
markers through unchanged (spec § Boundaries — Never do). The
`.adapt-discovery.toml` *materialisation* lives in the
`adapt-to-project` skill, out of scope here. T7 ships only the
consumer.
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

# The adapter-target subtree — paths every adapter could touch. Used
# to clone working-tree state into a dry-run shadow.
TARGET_PATHS = (
    Path(".claude"),
    Path("tools") / "hooks",
    Path(".github") / "instructions",
    Path("AGENTS.md"),
)


def is_dirty_tree(working_tree: Path) -> bool:
    """Return True if `git status --porcelain` against working_tree is non-empty.

    Fail-closed semantics — if git is missing, the directory isn't a
    git repo, or the call fails for any reason, return True so the
    destructive `--self` write still requires `--force`. The operator
    who knows the directory is safe can always pass `--force`; the
    operator who doesn't know what's there is protected.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=working_tree,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print(
            f"self-host: warning — `git` binary not on PATH; treating "
            f"{working_tree} as dirty.",
            file=sys.stderr,
        )
        return True
    if result.returncode != 0:
        print(
            f"self-host: warning — `git status` failed in {working_tree} "
            f"(exit {result.returncode}); treating as dirty.",
            file=sys.stderr,
        )
        return True
    return bool(result.stdout.strip())


def resolve_markers(root: Path, discovery: dict[str, str]) -> int:
    """Walk adapter-target paths under root and substitute <adapt:NAME>.

    Scope is restricted to TARGET_PATHS (the adapter-target subtree the
    build owns) — not the entire working tree. This avoids silently
    rewriting adopter-private files outside the bundle's owned region.
    """
    modified = 0
    candidates: list[Path] = []
    for relative in TARGET_PATHS:
        target = root / relative
        if target.is_file():
            candidates.append(target)
        elif target.is_dir():
            candidates.extend(p for p in target.rglob("*") if p.is_file())
    for path in candidates:
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


def _clone_target_subtree(working_tree: Path, destination: Path) -> None:
    """Copy adapter-target paths from working_tree into destination."""
    for relative in TARGET_PATHS:
        source = working_tree / relative
        if not source.exists():
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)


def _project_all_adapters(
    output_root: Path,
    packs_dir: Path,
    contract: dict,
) -> None:
    """Run every contract-declared adapter against every discovered pack."""
    packs = discover_packs(packs_dir)
    for pack in packs:
        validate_pack_uniqueness(pack)
    for adapter_name, project in ADAPTERS.items():
        if adapter_name not in contract["adapter"]:
            continue
        for pack in packs:
            project(pack.path, contract, output_root)


def diff_against_working_tree(shadow: Path, working_tree: Path) -> list[str]:
    """Compare every file in `shadow` against the corresponding path in
    `working_tree`. Returns per-file drift lines."""
    drifts: list[str] = []
    for rendered in shadow.rglob("*"):
        if not rendered.is_file():
            continue
        relative = rendered.relative_to(shadow)
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
    """Execute `make build --self` (or `--self --dry-run`)."""
    if contract is None:
        contract = load_contract(CONTRACT_PATH)

    if not dry_run and is_dirty_tree(working_tree) and not force:
        print(
            "self-host: working tree is dirty — refusing to write. "
            "Pass --force to override (the dirty-tree check only).",
            file=sys.stderr,
        )
        return 2

    if dry_run:
        with tempfile.TemporaryDirectory(prefix="agentbundle-shadow-") as shadow_str:
            shadow = Path(shadow_str)
            _clone_target_subtree(working_tree, shadow)
            _project_all_adapters(shadow, packs_dir, contract)
            drifts = diff_against_working_tree(shadow, working_tree)
            if drifts:
                print(
                    f"self-host: dry-run found {len(drifts)} drift(s):",
                    file=sys.stderr,
                )
                for drift in drifts:
                    print(f"  {drift}", file=sys.stderr)
                return 1
            return 0

    # Real write: project directly into the working tree so adapter
    # merge/splice logic sees existing content.
    _project_all_adapters(working_tree, packs_dir, contract)
    discovery_path = working_tree / ".adapt-discovery.toml"
    if discovery_path.exists():
        discovery_data = tomllib.loads(discovery_path.read_text(encoding="utf-8"))
        discovery_flat = {
            str(key): str(value)
            for key, value in discovery_data.get("adapt", {}).items()
        }
        resolve_markers(working_tree, discovery_flat)
    return 0


def cmd_self(args) -> int:
    return run_self_host(
        working_tree=Path(args.output_dir).resolve(),
        packs_dir=Path(args.packs_dir).resolve(),
        dry_run=args.dry_run,
        force=args.force,
    )


def cmd_check(args) -> int:
    """`make build --check` — strict dry-run against the working tree."""
    return run_self_host(
        working_tree=Path(args.output_dir).resolve(),
        packs_dir=Path(args.packs_dir).resolve(),
        dry_run=True,
        force=False,
    )


# Re-export project_to_temp for any external caller that still relies
# on the older API (tests previously imported this helper). The new
# self-host implementation uses _project_all_adapters internally
# against the working tree (or a shadow clone of it).
def project_to_temp(working_tree: Path, packs_dir: Path, contract: dict) -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="agentbundle-self-"))
    _clone_target_subtree(working_tree, temp_dir)
    _project_all_adapters(temp_dir, packs_dir, contract)
    return temp_dir
