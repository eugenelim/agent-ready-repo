"""Copilot adapter — projects skills as first-class Agent Skills
(`.github/skills/<name>/SKILL.md`), agents as `.agent.md`, hook-wiring as
per-file JSON, hook bodies straight through; drops only `command`
(copilot-cli#618/#1113).

Skills use the shared `direct-directory` passthrough (docs/specs/copilot-skills-and-web
/ RFC-0024 § Errata E2): Copilot reads `.github/skills/<name>/SKILL.md` and
accepts our canonical Claude `SKILL.md` verbatim, so the source tree is copied
byte-for-byte — the same mode claude-code/codex/kiro use. Agent + hook-wiring
serialisation live in the sibling `copilot_agent_md` / `copilot_hooks_json`
projection modules (RFC-0024 / docs/specs/copilot-full-parity); this adapter
only dispatches to them.

The adapter is scope-agnostic: it emits repo-relpaths (`.github/…`) at every
scope. The divergent user-scope home (`~/.copilot/…`) is produced by the
install handler's post-render prefix rewrite, not here.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterator


# RFC-0005 § Build-pipeline ordering invariant — uniform across adapters.
from agentbundle.build.phase_order import PHASE_ORDER as _PHASE_ORDER
from agentbundle.build.projections.direct_directory import sweep_orphans
from agentbundle.build.projections.copilot_agent_md import (
    project_copilot_agent_md,
)
from agentbundle.build.projections.copilot_hooks_json import (
    project_copilot_hooks_json,
)


def _ignore_symlinks(directory: str, names: list[str]) -> set[str]:
    """`shutil.copytree` ignore callback: skip every symlink member.

    Drops nested symlinks so they are never reproduced in the output
    tree. The top-level `is_symlink()` skip in `_project_direct_directory`
    covers the skill root; this covers the subtree.
    """
    base = Path(directory)
    return {name for name in names if (base / name).is_symlink()}


def _iter_primitives(contract: dict) -> Iterator[str]:
    """Yield Copilot's projected primitive names in phase order."""
    adapter_block = contract["adapter"]["copilot"]
    array_form = {entry["primitive"]: entry for entry in adapter_block.get("projection", [])}
    for primitive_name in _PHASE_ORDER:
        if primitive_name in array_form and array_form[primitive_name].get("mode") != "dropped":
            yield primitive_name


def project(pack_path: Path, contract: dict, output_root: Path) -> None:
    adapter_block = contract["adapter"]["copilot"]
    rules_by_primitive = {entry["primitive"]: entry for entry in adapter_block.get("projection", [])}

    for primitive_name in _iter_primitives(contract):
        rule = rules_by_primitive[primitive_name]
        mode = rule["mode"]
        primitive = contract["primitive"][primitive_name]
        source_dir = pack_path / primitive["source-path"].rstrip("/")
        if not source_dir.exists():
            continue

        if mode == "direct-directory":
            _project_direct_directory(source_dir, output_root, rule, primitive_name)
        elif mode == "direct-file":
            _project_direct_file(source_dir, output_root, rule["target-path"])
        elif mode == "copilot-agent-md":
            mapping_name = rule["frontmatter-mapping"]
            mapping = contract.get("frontmatter-mapping", {}).get(mapping_name, {})
            project_copilot_agent_md(source_dir, output_root, rule, mapping)
        elif mode == "copilot-hooks-json":
            project_copilot_hooks_json(source_dir, output_root, rule)
        else:
            raise ValueError(f"copilot: unhandled mode {mode!r} for {primitive_name}")


def _project_direct_file(source_dir: Path, output_root: Path, target_prefix: str) -> None:
    target_dir = output_root / target_prefix.rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source_dir.iterdir()):
        if entry.is_file():
            shutil.copy2(entry, target_dir / entry.name, follow_symlinks=False)


def _project_direct_directory(
    source_dir: Path,
    output_root: Path,
    rule: dict,
    primitive_name: str,
) -> None:
    """Copy each `<name>/` source tree to the target directory verbatim, then
    sweep orphaned target dirs no longer backed by a source.

    A symlink at the entry root is skipped (defense-in-depth — `lint-packs`
    already refuses symlinked packs, but a direct `project()` caller bypasses
    that gate). `ignore=_ignore_symlinks` drops nested symlinks so they are
    never reproduced in the output tree. A destination symlink is `unlink`ed
    (never `rmtree`d) before the copy. The orphan sweep is **bounded to the
    `skill` primitive's** expected source names, so it can never delete sibling
    `.github/agents/` or `.github/hooks/` content.
    """
    target_dir = output_root / rule["target-path"].rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    expected_names: set[str] = set()
    for entry in sorted(source_dir.iterdir()):
        if entry.is_symlink():
            continue
        if entry.is_dir():
            expected_names.add(entry.name)
            destination = target_dir / entry.name
            if destination.is_symlink():
                destination.unlink()
            elif destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(entry, destination, ignore=_ignore_symlinks)
    if primitive_name == "skill":
        sweep_orphans(target_dir, expected_names)
