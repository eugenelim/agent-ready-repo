#!/usr/bin/env python3
"""Enforce exclusive ownership of generated projection paths.

Architecture.md section 3 says that no generated projection is an authoring
dependency.  CAT-V-014 and CAT-V-015 already prove that a projection with a
source has matching content and that ``dist/`` matches a fresh build.  They do
not catch two declared producers for one destination, nor a hand-authored file
in a generated root which has no source at all; this lint closes that hole.

The producer list comes from the self-host recipe and projection roots come
from the adapter contract, rather than hard-coded pack or root inventories, so
changes in either source of truth change the audit.  File primitives compare by
stem because adapters may change extensions (for example ``x.md`` to
``x.toml``); skill primitives compare directory names.  Seed collisions fail
even if their present contents are identical: they are still two producers,
and the next edit would make projection order decide the result.

**Scope: the top-level entry of a generated root, not what is inside it.** This
lint answers "does this destination have exactly one declared producer, and is
anything squatting on it" — an ownership question. It deliberately does not walk
into a projected skill directory to compare its contents, because that is
already covered: `agentbundle catalogue self-host --check` reports
`[drift] ".claude/skills/<name>/SKILL.md" (missing on disk)` for a projected file
removed from inside a retained directory, and widening this lint to match would
duplicate the drift gate rather than close a hole. So "missing projection" here
means the projected *entry* is absent, and content inside a present entry is the
drift gate's to answer.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

ROOT = Path(__file__).resolve().parents[1]
RECIPE_PATH = Path("packages/agentbundle/agentbundle/build/recipes/self-host.toml")
CONTRACT_PATH = Path("contracts/adapter.toml")
PRIMITIVES = ("skill", "agent", "command", "hook-body")
# Floors carry headroom rather than pinning the current count. A floor equal to
# today's inventory turns every legitimate addition or removal into a build
# break, which trains a maintainer to bump the number without reading why it
# moved — the opposite of the deliberate update the message asks for. Measured:
# retiring one skill upstream took the counts below exact-count floors and
# reddened this gate for a change that was entirely correct. These values are
# set to catch a scan collapsing, which is the failure they exist for, and
# `tools/lint-no-direct-check-ignore.py` sets SCANNED_FLOOR the same way.
SKILL_FLOOR = 18
PACK_FLOOR = 3
ROOT_FLOOR = 5

# Exact paths only: a pattern here would silently widen the authoring escape
# hatch.  Every exemption is checked for staleness on the real repository.
EXEMPTIONS: dict[str, str] = {
    "tools/hooks/README.md": (
        "hand-authored guide to the projected hooks; no pack ships "
        "`.apm/hooks/README.md`."
    ),
}


@dataclass(frozen=True)
class ProjectionRoot:
    """One adapter/primitive projection directory resolved from the contract."""

    adapter: str
    primitive: str
    path: Path


@dataclass
class AuditResult:
    """Inventory and failures accumulated without skipping uncertain inputs."""

    packs: list[str] = field(default_factory=list)
    roots: list[ProjectionRoot] = field(default_factory=list)
    owners: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)

    @property
    def primitive_count(self) -> int:
        """Number of distinct recipe-pack primitive names, by kind."""
        return sum(len(names) for names in self.owners.values())


def _symlinked_directories(base: Path, root: Path) -> list[str]:
    """Repository-relative symlinked directories beneath ``base``.

    `Path.rglob` does not descend through a directory symlink, so anything under
    one is invisible to the scans below. That makes a symlink a blind spot
    rather than an error: content parked outside the scanned set and reached
    through a link inside it would never be inspected. The repository already
    refuses link-like roots elsewhere, so refuse them here rather than scan
    around them.
    """
    found: list[str] = []
    stack = [base]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_symlink():
                if entry.is_dir():
                    found.append(entry.relative_to(root).as_posix())
                continue
            if entry.is_dir():
                stack.append(entry)
    return found


def _refuse_symlinks(base: Path, root: Path, findings: list[str]) -> None:
    """Record a finding for every symlinked directory in a scanned tree.

    The base itself is checked first. A symlink to a directory satisfies
    `is_dir()`, so a caller that guards with `is_dir()` and then walks would
    descend into the link's target and find no symlinked *children* — the link
    it should have refused is the walk's own root, and the tree reads clean.
    """
    if base.is_symlink():
        findings.append(
            f"{base.relative_to(root).as_posix()}: symlinked directory in a "
            "scanned tree; refusing to scan around it"
        )
        return
    for link in _symlinked_directories(base, root):
        findings.append(
            f"{link}: symlinked directory in a scanned tree; "
            "refusing to scan around it"
        )


def _read_toml(path: Path, label: str, result: AuditResult) -> dict[str, object] | None:
    """Load one source-of-truth TOML file, making unreadability a finding."""
    try:
        with path.open("rb") as handle:
            loaded = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        result.findings.append(
            f"{label} {path.as_posix()} is missing or unreadable ({exc}); "
            "this audit must not pass vacuously"
        )
        return None
    if not isinstance(loaded, dict):
        result.findings.append(
            f"{label} {path.as_posix()} has no TOML table; this audit must not "
            "pass vacuously"
        )
        return None
    return loaded


def _recipe_values(recipe: dict[str, object], result: AuditResult) -> tuple[list[str], list[str]]:
    """Read pack includes and adapter targets from the declared recipe shape."""
    recipe_table = recipe.get("recipe")
    packs_table = recipe_table.get("packs") if isinstance(recipe_table, dict) else None
    adapters_table = recipe_table.get("adapters") if isinstance(recipe_table, dict) else None
    include = packs_table.get("include") if isinstance(packs_table, dict) else None
    targets = adapters_table.get("targets") if isinstance(adapters_table, dict) else None
    packs = []
    if isinstance(include, list):
        for item in include:
            if isinstance(item, str) and _safe_relative(item) is not None:
                packs.append(item)
            else:
                result.findings.append(
                    f"invalid recipe pack name {item!r}; paths must remain relative"
                )
    adapters = (
        [item for item in targets if isinstance(item, str)]
        if isinstance(targets, list)
        else []
    )
    if not packs:
        result.findings.append(
            "recipe pack include list is empty or invalid; this audit must not "
            "pass vacuously"
        )
    if not adapters:
        result.findings.append(
            "recipe adapter target list is empty or invalid; this audit must not "
            "pass vacuously"
        )
    return packs, adapters


def _safe_relative(value: str) -> Path | None:
    """Return a non-escaping relative path, or reject an out-of-root value."""
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts or path.as_posix() == ".":
        return None
    return path


def _projection_roots(
    contract: dict[str, object], adapters: list[str], result: AuditResult,
) -> list[ProjectionRoot]:
    """Resolve projected primitive directories only for recipe-selected adapters."""
    adapter_table = contract.get("adapter")
    if not isinstance(adapter_table, dict):
        return []
    roots: list[ProjectionRoot] = []
    for adapter in adapters:
        definition = adapter_table.get(adapter)
        projections = definition.get("projection") if isinstance(definition, dict) else None
        if not isinstance(projections, list):
            continue
        for projection in projections:
            if not isinstance(projection, dict):
                continue
            primitive = projection.get("primitive")
            mode = projection.get("mode")
            target = projection.get("target-path")
            target_path = _safe_relative(target) if isinstance(target, str) else None
            if (not isinstance(primitive, str) or primitive not in PRIMITIVES
                    or not isinstance(target, str) or not target.endswith("/")
                    or mode in {"merge-json", "dropped"}):
                continue
            if target_path is None:
                result.findings.append(
                    f"invalid generated target path {target!r}; paths must remain relative"
                )
                continue
            roots.append(ProjectionRoot(adapter, primitive, target_path))
    return roots


def _source_directory(primitive: str) -> str:
    """The .apm subdirectory which owns this primitive kind."""
    return {
        "skill": "skills",
        "agent": "agents",
        "command": "commands",
        "hook-body": "hooks",
    }[primitive]


def _owned_names(root: Path, pack: str, primitive: str, result: AuditResult) -> list[str]:
    """List one pack's declared primitive names, preserving malformed input as a failure."""
    directory = root / "packs" / pack / ".apm" / _source_directory(primitive)
    if not directory.exists():
        return []
    if not directory.is_dir():
        result.findings.append(f"{directory.relative_to(root).as_posix()}: expected a directory")
        return []
    names: list[str] = []
    try:
        entries = sorted(directory.iterdir())
    except OSError as exc:
        result.findings.append(f"{directory.relative_to(root).as_posix()}: cannot be read ({exc})")
        return []
    for entry in entries:
        if entry.is_symlink():
            # A symlinked source primitive points ownership somewhere this
            # audit does not follow, so the producer it declares would be a
            # path outside the scanned tree.
            result.findings.append(
                f"{entry.relative_to(root).as_posix()}: symlinked source "
                "primitive; a declared producer must be a real file or directory"
            )
            continue
        if primitive == "skill":
            if entry.is_dir():
                names.append(entry.name)
            elif entry.exists():
                result.findings.append(
                    f"{entry.relative_to(root).as_posix()}: a skill producer must be a directory"
                )
        elif entry.is_file():
            names.append(entry.stem)
        elif entry.exists():
            result.findings.append(
                f"{entry.relative_to(root).as_posix()}: a {primitive} producer must be a file"
            )
    return names


def _collect_owners(root: Path, packs: list[str], result: AuditResult) -> None:
    """Collect recipe-pack producers and flag ambiguous primitive ownership."""
    for primitive in PRIMITIVES:
        by_name: dict[str, list[str]] = {}
        for pack in packs:
            for name in _owned_names(root, pack, primitive, result):
                by_name.setdefault(name, []).append(pack)
        result.owners[primitive] = by_name
        for name, owner_packs in by_name.items():
            if len(owner_packs) > 1:
                result.findings.append(
                    f"ambiguous ownership for {primitive!r} {name!r}: "
                    + ", ".join(owner_packs)
                )


def _seed_collisions(root: Path, result: AuditResult) -> None:
    """Flag every relative seed file path supplied by more than one pack."""
    packs_root = root / "packs"
    try:
        pack_dirs = sorted(path for path in packs_root.iterdir() if path.is_dir())
    except OSError as exc:
        result.findings.append(f"packs: cannot enumerate seed owners ({exc})")
        return
    owners: dict[str, list[str]] = {}
    for pack_dir in pack_dirs:
        seeds = pack_dir / "seeds"
        if not seeds.is_dir():
            continue
        _refuse_symlinks(seeds, root, result.findings)
        try:
            files = sorted(path for path in seeds.rglob("*") if path.is_file())
        except OSError as exc:
            result.findings.append(f"{seeds.relative_to(root).as_posix()}: cannot be read ({exc})")
            continue
        for path in files:
            owners.setdefault(path.relative_to(seeds).as_posix(), []).append(pack_dir.name)
    for relative, owner_packs in owners.items():
        if len(owner_packs) > 1:
            result.findings.append(
                f"seed collision at {relative!r}: " + ", ".join(owner_packs)
            )


def _entry_name(entry: Path, primitive: str) -> str:
    """Projection matching key: a skill directory name, otherwise a file stem."""
    return entry.name if primitive == "skill" else entry.stem


def _audit_projection_roots(root: Path, result: AuditResult) -> None:
    """Check each configured root in both directions against recipe ownership."""
    for projection in result.roots:
        directory = root / projection.path
        relative_directory = projection.path.as_posix().rstrip("/")
        expected = set(result.owners.get(projection.primitive, {}))
        try:
            entries = sorted(directory.iterdir())
        except OSError as exc:
            result.findings.append(
                f"{relative_directory}: generated root cannot be read ({exc})"
            )
            entries = []
        present: set[str] = set()
        for entry in entries:
            relative = entry.relative_to(root).as_posix()
            if entry.is_symlink():
                # Checked before the exemption test on purpose: an exemption
                # naming a symlink would hand the escape hatch a target this
                # audit never follows, so a link can never be exempted.
                result.findings.append(
                    f"{relative}: symlink in a generated root; a projected "
                    "entry must be a real file or directory"
                )
                continue
            if relative in EXEMPTIONS:
                continue
            name = _entry_name(entry, projection.primitive)
            present.add(name)
            if name not in expected:
                result.findings.append(
                    f"orphan in generated root: {relative} has no declared "
                    f"{projection.primitive} producer"
                )
        for name in sorted(expected - present):
            result.findings.append(
                f"missing projection: {relative_directory}/{name} has a declared "
                f"{projection.primitive} producer"
            )


def audit(root: Path, enforce_floors: bool) -> AuditResult:
    """Run both ownership checks against a repository or a small fixture tree."""
    result = AuditResult()
    recipe = _read_toml(root / RECIPE_PATH, "recipe", result)
    contract = _read_toml(root / CONTRACT_PATH, "contract", result)
    if recipe is None or contract is None:
        return result
    packs, adapters = _recipe_values(recipe, result)
    result.packs = packs
    result.roots = _projection_roots(contract, adapters, result)
    if not result.roots:
        result.findings.append(
            "contract resolved zero generated roots; this audit must not pass "
            "vacuously"
        )
    _collect_owners(root, packs, result)
    if result.primitive_count == 0:
        result.findings.append(
            "recipe packs contain zero primitives; this audit must not pass "
            "vacuously"
        )
    _seed_collisions(root, result)
    if result.roots:
        _audit_projection_roots(root, result)
    if enforce_floors:
        if len(result.packs) < PACK_FLOOR:
            result.findings.append(
                f"recipe has only {len(result.packs)} packs, below the recorded floor "
                f"of {PACK_FLOOR}. Either the scan silently narrowed or the floor "
                "needs a deliberate update."
            )
        if len(result.roots) < ROOT_FLOOR:
            result.findings.append(
                f"resolved only {len(result.roots)} generated roots, below the recorded "
                f"floor of {ROOT_FLOOR}. Either the scan silently narrowed or the floor "
                "needs a deliberate update."
            )
        skill_count = len(result.owners.get("skill", {}))
        if skill_count < SKILL_FLOOR:
            result.findings.append(
                f"projected only {skill_count} skills, below the recorded floor of "
                f"{SKILL_FLOOR}. Either the scan silently narrowed or the floor needs "
                "a deliberate update."
            )
        for path, reason in EXEMPTIONS.items():
            target = root / path
            if not target.exists():
                result.findings.append(
                    f"stale exemption: {path} no longer exists ({reason})"
                )
                continue
            if target.is_symlink():
                # The generated-root scan already refuses a symlink before it
                # consults this table, so ordering alone protects the boundary.
                # Asserting it here as well makes the guarantee independent of
                # that ordering: an exemption may never name a path whose target
                # this audit does not follow, however the checks are arranged.
                result.findings.append(
                    f"exempt path is a symlink: {path} ({reason}); an exemption "
                    "must name a real file or directory"
                )
                continue
            if not target.is_file():
                result.findings.append(
                    f"exempt path is not a regular file: {path} ({reason})"
                )
    return result


def main(argv: list[str] | None = None) -> int:
    """Parse the root selector, report every finding, and return a CI status."""
    parser = argparse.ArgumentParser(
        description="Enforce exclusive ownership of generated projection paths."
    )
    parser.add_argument("--root", default=None, metavar="PATH",
                        help="repository root to audit (default: this repository)")
    args = parser.parse_args(argv)
    root = ROOT if args.root is None else Path(args.root).resolve()
    result = audit(root, enforce_floors=args.root is None)
    # `tools/hooks/` is the hook-body target of more than one adapter, so the
    # same root is audited once per adapter and an orphan there is found twice.
    # Deduplicate on the message, order-preserving: one defect must read as one
    # finding, and the printed count is what a reviewer compares against.
    findings = list(dict.fromkeys(result.findings))
    if findings:
        for finding in findings:
            print(f"FAIL: {finding}", file=sys.stderr)
        print(f"✖ lint-generated-path-ownership: {len(findings)} violation(s)",
              file=sys.stderr)
        return 1
    print(f"ok   [generated-path-ownership] ({len(result.roots)} roots, "
          f"{len(result.packs)} packs, {result.primitive_count} primitives)")
    print("✓ lint-generated-path-ownership: passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
