"""Claude Code adapter — projects every primitive per the contract.

Projection modes used (read from contract["adapter"]["claude-code"]):
  - skill       → direct-directory → .claude/skills/<name>/
  - agent       → direct-file       → .claude/agents/<name>.md
  - hook-body   → direct-file       → tools/hooks/<name>.{sh,py}
  - hook-wiring → merge-json        → .claude/settings.local.json (hooks key)
  - command     → direct-file       → .claude/commands/<name>.md

The merge-json projection is idempotent because we re-serialise with
`sort_keys=True` and re-read the existing file's `hooks` key before
deep-merging the incoming TOML payload.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterator


# Phase order from RFC-0005 § Build-pipeline ordering invariant.
# Uniform across all reference adapters even though Claude Code's
# wiring lands in a settings file (not in agents) — the uniformity
# keeps the phases predictable, which the spec calls for.
from agentbundle.build.phase_order import PHASE_ORDER as _PHASE_ORDER
from agentbundle.build.projections.direct_directory import sweep_orphans
from agentbundle.build.projections.merge_json import project_merge_json


def _iter_primitives(contract: dict) -> Iterator[str]:
    """Yield Claude Code's projected primitive names in phase order."""
    adapter_block = contract["adapter"]["claude-code"]
    array_form = {entry["primitive"]: entry for entry in adapter_block.get("projection", [])}
    for primitive_name in _PHASE_ORDER:
        if primitive_name in array_form and array_form[primitive_name].get("mode") != "dropped":
            yield primitive_name


def project(pack_path: Path, contract: dict, output_root: Path) -> None:
    """Single-pack convenience wrapper. Delegates to `project_packs`."""
    project_packs([pack_path], contract, output_root)


def project_packs(pack_paths: list[Path], contract: dict, output_root: Path) -> None:
    """Project every pack in `pack_paths` in order, then run the
    shared orphan-sweep post-pass on the `skill` target directory.

    Same-name collision rule: pack source order as supplied here; the
    last pack's `<name>` overwrites earlier packs' (`_project_direct_directory`
    `rmtree`s the destination before `copytree`). The orphan sweep
    observes the union of source skill names across the call's pack
    list (not per-pack) so a pack shipping a subset can co-exist with
    another that ships the union complement.
    """
    for pack_path in pack_paths:
        _project_single(pack_path, contract, output_root)
    _sweep_skill_orphans(pack_paths, contract, output_root)


# Mirror of kiro.py:_skill_direct_directory_target — keep in sync.
# A shared helper is barred by the spec's `Never do` boundary (no
# expansion of projections/direct_directory.py beyond `sweep_orphans`).
def _skill_direct_directory_target(contract: dict, output_root: Path) -> Path | None:
    adapter_block = contract["adapter"]["claude-code"]
    for entry in adapter_block.get("projection", []):
        if entry.get("primitive") == "skill" and entry.get("mode") == "direct-directory":
            return output_root / entry["target-path"].rstrip("/")
    return None


def _sweep_skill_orphans(pack_paths: list[Path], contract: dict, output_root: Path) -> None:
    target_dir = _skill_direct_directory_target(contract, output_root)
    if target_dir is None:
        return
    skill_source_path = contract["primitive"]["skill"]["source-path"].rstrip("/")
    expected_names: set[str] = set()
    for pack_path in pack_paths:
        source_dir = pack_path / skill_source_path
        if not source_dir.exists():
            continue
        for entry in source_dir.iterdir():
            if entry.is_dir():
                expected_names.add(entry.name)
    sweep_orphans(target_dir, expected_names)


def _project_single(pack_path: Path, contract: dict, output_root: Path) -> None:
    adapter_block = contract["adapter"]["claude-code"]
    rules_by_primitive = {entry["primitive"]: entry for entry in adapter_block.get("projection", [])}

    for primitive_name in _iter_primitives(contract):
        rule = rules_by_primitive[primitive_name]
        mode = rule["mode"]
        primitive = contract["primitive"][primitive_name]
        source_dir = pack_path / primitive["source-path"].rstrip("/")
        if not source_dir.exists():
            continue

        if mode == "direct-directory":
            _project_direct_directory(source_dir, output_root / rule["target-path"].rstrip("/"))
        elif mode == "direct-file":
            _project_direct_file(source_dir, output_root, rule["target-path"])
        elif mode == "merge-json":
            project_merge_json(source_dir, output_root, rule)
        else:
            raise ValueError(f"claude-code: unhandled mode {mode!r} for {primitive_name}")


def _ignore_symlinks(directory: str, names: list[str]) -> set[str]:
    """`shutil.copytree` ignore callback: skip every symlink member.

    Drops nested symlinks so they are never reproduced in the output
    tree. The top-level `is_symlink()` skip in `_project_direct_directory`
    covers the skill root; this covers the subtree.
    """
    base = Path(directory)
    return {name for name in names if (base / name).is_symlink()}


def _project_direct_directory(source_dir: Path, target_dir: Path) -> None:
    for entry in sorted(source_dir.iterdir()):
        # Defense-in-depth — `lint-packs` rejects packs that ship
        # symlinks, but a direct `project_packs` caller bypasses
        # that gate. A symlink at the skill-root level would be
        # dereferenced by `copytree`.
        if entry.is_symlink():
            continue
        if entry.is_dir():
            destination = target_dir / entry.name
            # Spec § Never do — `shutil.rmtree` is barred against
            # any entry whose `is_symlink()` is true. If a previous
            # run left a symlink at the destination path, unlink it
            # (removes the link, not the target).
            if destination.is_symlink():
                destination.unlink()
            elif destination.exists():
                shutil.rmtree(destination)
            # `ignore=_ignore_symlinks` drops nested symlinks so they are
            # never reproduced in the output tree. A malicious pack with a
            # symlink to /etc/passwd cannot exfiltrate the target.
            shutil.copytree(entry, destination, ignore=_ignore_symlinks)


def _project_direct_file(source_dir: Path, output_root: Path, target_prefix: str) -> None:
    target_dir = output_root / target_prefix.rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source_dir.iterdir()):
        if entry.is_file():
            destination = target_dir / entry.name
            shutil.copy2(entry, destination, follow_symlinks=False)


