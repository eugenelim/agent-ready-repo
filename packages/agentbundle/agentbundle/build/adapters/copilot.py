"""Copilot adapter — projects skills as first-class Agent Skills
(`.github/skills/<name>/SKILL.md`), agents as `.agent.md`, hook-wiring as
per-file JSON, hook bodies straight through; drops only `command`
(copilot-cli#618/#1113).

Skills use the shared `direct-directory` passthrough: Copilot reads
`.github/skills/<name>/SKILL.md` and
accepts our canonical Claude `SKILL.md` verbatim, so the source tree is copied
byte-for-byte — the same mode claude-code/codex/kiro use. Agent + hook-wiring
serialisation live in the sibling `copilot_agent_md` / `copilot_hooks_json`
projection modules; this adapter
only dispatches to them.

The adapter is scope-agnostic: it emits repo-relpaths (`.github/…`) at every
scope. The divergent user-scope home (`~/.copilot/…`) is produced by the
install handler's post-render prefix rewrite, not here.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterator

# Build-pipeline ordering invariant — uniform across adapters.
from agentbundle.build.phase_order import PHASE_ORDER as _PHASE_ORDER
from agentbundle.build.projection_io import copy_projected_file, ensure_directory_no_follow
from agentbundle.build.projections.copilot_agent_md import (
    project_copilot_agent_md,
)
from agentbundle.build.projections.copilot_hooks_json import (
    project_copilot_hooks_json,
)
from agentbundle.build.projections.direct_directory import sweep_orphans


def _ignore_symlinks(directory: str, names: list[str]) -> set[str]:
    """`shutil.copytree` ignore callback: skip every symlink member and
    Python bytecode cache directories.

    Drops nested symlinks so they are never reproduced in the output
    tree. The top-level `is_symlink()` skip in `_project_direct_directory`
    covers the skill root; this covers the subtree. __pycache__ is excluded
    because .pyc files embed absolute source paths and would cause drift.
    """
    base = Path(directory)
    return {name for name in names if name == "__pycache__" or (base / name).is_symlink()}


def _iter_primitives(contract: dict) -> Iterator[str]:
    """Yield Copilot's projected primitive names in phase order."""
    adapter_block = contract["adapter"]["copilot"]
    array_form = {entry["primitive"]: entry for entry in adapter_block.get("projection", [])}
    for primitive_name in _PHASE_ORDER:
        if primitive_name in array_form and array_form[primitive_name].get("mode") != "dropped":
            yield primitive_name


def project(
    pack_path: Path,
    contract: dict,
    output_root: Path,
    *,
    preserve_existing_metadata: bool = False,
) -> None:
    """Single-pack convenience wrapper. Delegates to ``project_packs``."""
    project_packs(
        [pack_path],
        contract,
        output_root,
        preserve_existing_metadata=preserve_existing_metadata,
    )


def project_packs(
    pack_paths: list[Path],
    contract: dict,
    output_root: Path,
    *,
    preserve_existing_metadata: bool = False,
) -> None:
    """Project all packs, then sweep skills against their source union."""
    for pack_path in pack_paths:
        _project_single(
            pack_path,
            contract,
            output_root,
            preserve_existing_metadata=preserve_existing_metadata,
        )
    _sweep_skill_orphans(pack_paths, contract, output_root)


def _project_single(
    pack_path: Path,
    contract: dict,
    output_root: Path,
    *,
    preserve_existing_metadata: bool,
) -> None:
    adapter_block = contract["adapter"]["copilot"]
    rules_by_primitive = {
        entry["primitive"]: entry
        for entry in adapter_block.get("projection", [])
    }

    for primitive_name in _iter_primitives(contract):
        rule = rules_by_primitive[primitive_name]
        mode = rule["mode"]
        primitive = contract["primitive"][primitive_name]
        source_dir = pack_path / primitive["source-path"].rstrip("/")
        if not source_dir.exists():
            continue

        if mode == "direct-directory":
            _project_direct_directory(
                source_dir,
                output_root,
                rule,
                primitive_name,
            )
        elif mode == "direct-file":
            _project_direct_file(
                source_dir,
                output_root,
                rule["target-path"],
                preserve_existing_metadata=preserve_existing_metadata,
            )
        elif mode == "copilot-agent-md":
            mapping_name = rule["frontmatter-mapping"]
            mapping = contract.get("frontmatter-mapping", {}).get(mapping_name, {})
            project_copilot_agent_md(source_dir, output_root, rule, mapping)
        elif mode == "copilot-hooks-json":
            project_copilot_hooks_json(source_dir, output_root, rule)
        else:
            raise ValueError(f"copilot: unhandled mode {mode!r} for {primitive_name}")


def _project_direct_file(
    source_dir: Path,
    output_root: Path,
    target_prefix: str,
    *,
    preserve_existing_metadata: bool,
) -> None:
    target_dir = output_root / target_prefix.rstrip("/")
    ensure_directory_no_follow(output_root, target_dir.relative_to(output_root))
    for entry in sorted(source_dir.iterdir()):
        if entry.is_file():
            copy_projected_file(
                entry,
                target_dir / entry.name,
                base=output_root,
                metadata="stat",
                preserve_existing_metadata=preserve_existing_metadata,
            )


def _project_direct_directory(
    source_dir: Path,
    output_root: Path,
    rule: dict,
    primitive_name: str,
) -> None:
    """Copy each ``<name>/`` source tree to the target directory verbatim.

    A symlink at the entry root is skipped (defense-in-depth — `lint-packs`
    already refuses symlinked packs, but a direct `project()` caller bypasses
    that gate). `ignore=_ignore_symlinks` drops nested symlinks so they are
    never reproduced in the output tree. A destination symlink is `unlink`ed
    (never `rmtree`d) before the copy. ``primitive_name`` retains the helper's
    established call contract; the pack-union orphan sweep now runs once after
    all packs are projected.
    """
    del primitive_name
    target_dir = output_root / rule["target-path"].rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source_dir.iterdir()):
        if entry.is_symlink():
            continue
        if entry.is_dir():
            destination = target_dir / entry.name
            if destination.is_symlink():
                destination.unlink()
            elif destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(entry, destination, ignore=_ignore_symlinks)


def _sweep_skill_orphans(
    pack_paths: list[Path],
    contract: dict,
    output_root: Path,
) -> None:
    skill_rule = next(
        (
            rule
            for rule in contract["adapter"]["copilot"].get("projection", [])
            if rule.get("primitive") == "skill"
            and rule.get("mode") == "direct-directory"
        ),
        None,
    )
    if skill_rule is None:
        return
    source_path = contract["primitive"]["skill"]["source-path"].rstrip("/")
    expected_names: set[str] = set()
    for pack_path in pack_paths:
        source_dir = pack_path / source_path
        if not source_dir.exists():
            continue
        expected_names.update(
            entry.name
            for entry in source_dir.iterdir()
            if not entry.is_symlink() and entry.is_dir()
        )
    target_dir = output_root / skill_rule["target-path"].rstrip("/")
    expected_names |= _installed_skill_names(output_root, target_dir)
    sweep_orphans(target_dir, expected_names)


def _installed_skill_names(output_root: Path, target_dir: Path) -> set[str]:
    """Return repo-scope installed skill names recorded beneath target_dir."""
    from agentbundle.config import ConfigError, load_state

    try:
        state = load_state(output_root / ".agentbundle-state.toml")
    except ConfigError:
        return set()
    skill_dir_rel = target_dir.relative_to(output_root)
    names: set[str] = set()
    for pack_state in state.packs.values():
        if pack_state.scope != "repo":
            continue
        for relpath in pack_state.files:
            try:
                remainder = Path(relpath).relative_to(skill_dir_rel)
            except ValueError:
                continue
            if remainder.parts:
                names.add(remainder.parts[0])
    return names
