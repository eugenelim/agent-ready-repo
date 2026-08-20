#!/usr/bin/env python3
"""Enforce the build adapter/projection dependency boundary.

Build orchestration depends on the adapter contract, adapters implement that
contract, and projections implement the output details.  Letting projections
depend on adapters reverses that direction; letting pack source or a target
runtime depend on either layer leaks build-time concerns into portable source.

This lint uses ``ast`` rather than grep because paths and import examples occur
in documentation and fixture prose.  Relative imports are resolved from the
importing module's package, since otherwise the closest and most important
projection-to-adapter edge can evade the rule.  A file that cannot be decoded
or parsed fails: skipping it would create a bypass precisely where this control
needs to be reliable.
"""

from __future__ import annotations

import argparse
import ast
import os
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

ROOT = Path(__file__).resolve().parents[1]
ADAPTERS = Path("packages/agentbundle/agentbundle/build/adapters")
PROJECTIONS = Path("packages/agentbundle/agentbundle/build/projections")

# Neither holds reviewable source, and walking them was most of this gate's
# wall clock. Pruning is safe because a violation cannot live in either.
_PRUNED_DIRECTORIES = frozenset({"__pycache__", "node_modules", ".git"})
ADAPTER_MODULE = "agentbundle.build.adapters"
PROJECTION_MODULE = "agentbundle.build.projections"
# Floors carry headroom rather than pinning the current count. A floor equal to
# today's inventory turns every legitimate addition or removal into a build
# break, which trains a maintainer to bump the number without reading why it
# moved — the opposite of the deliberate update the message asks for. Measured:
# retiring one skill upstream took the counts below exact-count floors and
# reddened this gate for a change that was entirely correct. These values are
# set to catch a scan collapsing, which is the failure they exist for, and
# `tools/lint-no-direct-check-ignore.py` sets SCANNED_FLOOR the same way.
ADAPTER_FLOOR = 7
PROJECTION_FLOOR = 9


@dataclass
class AuditResult:
    """The Python files inspected and findings produced while inspecting them."""

    scanned: list[Path] = field(default_factory=list)
    adapters: list[Path] = field(default_factory=list)
    projections: list[Path] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)


def _walk_python(base: Path, root: Path, findings: list[str]) -> list[Path]:
    """Collect ``*.py`` under ``base`` in one traversal, refusing symlinked dirs.

    `Path.rglob` does not descend through a directory symlink, so content
    under one is invisible to this scan — a blind spot rather than an error.
    A violating file parked outside the scanned set and reached through a
    link inside it would never be inspected, so refuse the link instead of
    scanning around it. The repository already refuses link-like roots
    elsewhere.

    Detection is fused into the SAME walk that collects the files rather
    than run as a second pass: a separate traversal more than doubled this
    gate's wall clock, and ADR-0087 makes lint cost a first-class concern.
    `followlinks=False` keeps the walk from following what it reports, and
    the pruned directories are skipped because no reviewable source lives
    in either.
    """
    if base.is_symlink():
        # Checked before `is_dir()`, which a symlink to a directory satisfies.
        # Without this the walk descends the link's target and finds no
        # symlinked *children*, so the link it should have refused — the walk's
        # own root — reads clean.
        findings.append(
            f"{base.relative_to(root).as_posix()}: symlinked directory in a "
            "scanned tree; refusing to scan around it"
        )
        return []
    if not base.is_dir():
        return []
    files: list[Path] = []
    for current, dirnames, filenames in os.walk(base, followlinks=False):
        current_path = Path(current)
        kept: list[str] = []
        for name in dirnames:
            if name in _PRUNED_DIRECTORIES:
                continue
            child = current_path / name
            if child.is_symlink():
                findings.append(
                    f"{child.relative_to(root).as_posix()}: symlinked "
                    "directory in a scanned tree; refusing to scan around it"
                )
                continue
            kept.append(name)
        dirnames[:] = kept
        for name in filenames:
            if not name.endswith(".py"):
                continue
            candidate = current_path / name
            # `os.walk` lists every non-directory entry, so a FIFO or socket
            # named `x.py` would arrive here and reading it could block the
            # gate. `is_file()` keeps the previous `rglob` behaviour: regular
            # files only, following a symlink to a real file, excluding a
            # dangling one.
            if candidate.is_file():
                files.append(candidate)
    return sorted(set(files))


def _python_files(root: Path, relative: Path,
                  findings: list[str] | None = None) -> list[Path]:
    """Python files below one scoped directory, in stable order."""
    return _walk_python(root / relative, root, [] if findings is None else findings)


def _pack_source_files(root: Path, findings: list[str]) -> list[Path]:
    """Pack Python sources, excluding exactly ``packs/*/tests/**``."""
    packs = root / "packs"
    files: list[Path] = []
    for path in _walk_python(packs, root, findings):
        parts = path.relative_to(packs).parts
        if len(parts) >= 2 and parts[1] == "tests":
            continue
        files.append(path)
    return sorted(files)


# `dist/` is a build output rather than an adapter target, so no contract entry
# names it. It is listed here because a projection copied into a release tree is
# still a target-runtime file.
_EXTRA_RUNTIME_ROOTS = (Path("dist"),)

CONTRACT_PATH = Path("contracts/adapter.toml")


def _contract_runtime_roots(root: Path, findings: list[str]) -> list[Path]:
    """Target-runtime roots, read from the adapter contract rather than fixed.

    Hard-coding `.claude`, `.codex`, `.agents` covers only the adapters this
    repository happens to project today. `contracts/adapter.toml` is where an
    adapter declares its `target-path`, so reading it means a newly declared
    adapter's tree is policed the moment the contract names it, instead of
    silently escaping the rule. Every adapter in the contract is read, not only
    the self-hosted ones: the boundary is about where projected files may land,
    not about which adapter this repository builds for itself.

    A missing or unparseable contract FAILS. Falling back to a fixed list would
    quietly shrink the scanned set to whatever was hard-coded, which is the
    failure this function exists to remove.
    """
    contract = root / CONTRACT_PATH
    try:
        parsed = tomllib.loads(contract.read_text(encoding="utf-8"))
    except FileNotFoundError:
        findings.append(f"{CONTRACT_PATH.as_posix()}: missing; cannot resolve runtime roots")
        return []
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        findings.append(f"{CONTRACT_PATH.as_posix()}: unreadable: {exc}")
        return []
    roots: set[Path] = set()
    for adapter in (parsed.get("adapter") or {}).values():
        if not isinstance(adapter, dict):
            continue
        for entry in adapter.get("projection") or []:
            target = entry.get("target-path") if isinstance(entry, dict) else None
            if not isinstance(target, str) or not target:
                continue
            candidate = Path(target)
            if candidate.is_absolute() or ".." in candidate.parts:
                findings.append(
                    f"{CONTRACT_PATH.as_posix()}: refusing target-path {target!r}"
                )
                continue
            # A merged config file (`.claude/settings.local.json`) names a file,
            # not a directory; take its parent so the tree is still scanned.
            roots.add(candidate if target.endswith("/") else candidate.parent)
    # A bare-filename target-path yields a parent of ".", which would scan the
    # whole repository; drop it rather than widening the scan silently.
    roots = {item for item in roots if item.as_posix() != "."}
    if not roots:
        # A contract that parses but declares no target-path leaves R3
        # scanning nothing, so a target-runtime file importing an adapter
        # would pass. An empty resolution is a broken contract, not an
        # empty rule.
        findings.append(
            f"{CONTRACT_PATH.as_posix()}: resolved zero target-runtime "
            "roots; R3 must not pass vacuously"
        )
    return sorted(roots)


def _target_runtime_files(root: Path, findings: list[str]) -> list[Path]:
    """Python files in runtime-owned directories, in stable order."""
    files: list[Path] = []
    for relative in list(_contract_runtime_roots(root, findings)) + list(_EXTRA_RUNTIME_ROOTS):
        files.extend(_python_files(root, relative, findings))
    return sorted(set(files))


def _package_for(path: Path, root: Path) -> list[str]:
    """Return the package containing ``path`` as inferred from its repository path."""
    parts = list(path.relative_to(root).with_suffix("").parts)
    # ``packages/agentbundle`` is the distribution's source root, not part of
    # its import name.  Keeping it here would turn ``from ..adapters`` in a
    # projection into ``packages.agentbundle.agentbundle.build.adapters`` and
    # silently miss the R1 edge.
    if parts[:2] == ["packages", "agentbundle"]:
        parts = parts[2:]
    if parts and parts[-1] == "__init__":
        return parts[:-1]
    return parts[:-1]


def _relative_module(node: ast.ImportFrom, package: list[str]) -> str:
    """Resolve an ``ImportFrom`` module against its importing package."""
    if node.level == 0:
        return node.module or ""
    kept = len(package) - (node.level - 1)
    base = package[:max(kept, 0)]
    if node.module:
        base.extend(node.module.split("."))
    return ".".join(base)


def _is_layer(module: str, layer: str) -> bool:
    """Whether a module names a layer package or one of its descendants."""
    return module == layer or module.startswith(f"{layer}.")


def _import_targets(node: ast.Import | ast.ImportFrom, package: list[str]) -> list[str]:
    """Fully qualified targets represented by one import statement."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]

    module = _relative_module(node, package)
    targets = [module] if module else []
    # ``from agentbundle.build import adapters`` names the layer through its
    # imported binding rather than the ImportFrom.module field.
    for alias in node.names:
        if alias.name != "*" and module:
            targets.append(f"{module}.{alias.name}")
    return targets


def _rule_for(path: Path, root: Path) -> str | None:
    """The boundary rule which owns a policed file, if any."""
    rel = path.relative_to(root)
    if rel.is_relative_to(PROJECTIONS):
        return "R1"
    if rel.parts and rel.parts[0] == "packs":
        return "R2"
    return "R3"


def _scan_source(path: Path, root: Path, rule: str) -> list[str]:
    """Return findings for one source, including read and parse failures."""
    rel = path.relative_to(root).as_posix()
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [f"{rel}:1: read-error cannot be read ({exc}); the gate refuses "
                "to skip a file it cannot inspect"]
    try:
        tree = ast.parse(source, filename=rel)
    except (SyntaxError, ValueError) as exc:
        return [f"{rel}:{getattr(exc, 'lineno', None) or 1}: parse-error cannot "
                f"be parsed ({exc}); the gate refuses to skip a file it cannot "
                "inspect"]

    findings: list[str] = []
    package = _package_for(path, root)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        targets = _import_targets(node, package)
        imports_adapter = any(_is_layer(target, ADAPTER_MODULE) for target in targets)
        imports_projection = any(
            _is_layer(target, PROJECTION_MODULE) for target in targets
        )
        violated = (
            (rule == "R1" and imports_adapter)
            or (rule in {"R2", "R3"} and (imports_adapter or imports_projection))
        )
        if violated:
            layer = "adapter" if imports_adapter else "projection"
            findings.append(
                f"{rel}:{node.lineno}: {rule} imports {layer} module "
                f"({', '.join(targets)})"
            )
    return findings


def audit(root: Path) -> AuditResult:
    """Inspect the Python files in the boundary's four owned path sets.

    `__pycache__`, `node_modules` and `.git` are pruned. That is safe rather
    than convenient: the first two are gitignored, so a violation cannot be
    committed inside them, and nothing can be tracked inside `.git` at all — no
    tracked `.py` exists under any of the three. Walking them was most of this
    gate's wall clock.
    """
    result = AuditResult()
    result.adapters = _python_files(root, ADAPTERS, result.findings)
    result.projections = _python_files(root, PROJECTIONS, result.findings)
    scoped: list[tuple[Path, str]] = []
    scoped.extend((path, "R1") for path in result.projections)
    scoped.extend((path, "R2") for path in _pack_source_files(root, result.findings))
    scoped.extend((path, "R3") for path in _target_runtime_files(root, result.findings))
    # Adapter sources are scanned for parse/read failures, but their imports of
    # projections are deliberately legal and they have no forbidden edge here.
    scoped.extend((path, "adapter") for path in result.adapters)
    for path, rule in sorted(scoped, key=lambda item: item[0]):
        result.scanned.append(path)
        if rule == "adapter":
            result.findings.extend(_scan_source(path, root, rule))
        else:
            result.findings.extend(_scan_source(path, root, rule))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Enforce adapter/projection dependency direction.",
    )
    parser.add_argument("--root", default=None, metavar="PATH",
                        help="repository root to audit (default: this repository)")
    args = parser.parse_args(argv)
    root = ROOT if args.root is None else Path(args.root).resolve()
    result = audit(root)

    if not result.adapters and not result.projections:
        print("✖ no adapter/projection sources found to scan — this must not pass "
              "vacuously", file=sys.stderr)
        return 1
    if args.root is None and (len(result.adapters) < ADAPTER_FLOOR
                              or len(result.projections) < PROJECTION_FLOOR):
        print(
            f"✖ scanned {len(result.adapters)} adapter and {len(result.projections)} "
            "projection sources, below the recorded floors of "
            f"{ADAPTER_FLOOR} and {PROJECTION_FLOOR}. Either the scan silently "
            "narrowed or a floor needs a deliberate update.",
            file=sys.stderr,
        )
        return 1
    if result.findings:
        for finding in result.findings:
            print(f"FAIL: {finding}", file=sys.stderr)
        print(f"✖ lint-adapter-layer-boundary: {len(result.findings)} "
              "violation(s)", file=sys.stderr)
        return 1

    print(f"ok   [adapter-layer-boundary] ({len(result.scanned)} files scanned)")
    print("✓ lint-adapter-layer-boundary: passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
