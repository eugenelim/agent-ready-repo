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

# Phase order from the build-pipeline ordering invariant.
# Uniform across all reference adapters even though Claude Code's
# wiring lands in a settings file (not in agents) — the uniformity
# keeps the phases predictable, which the spec calls for.
from agentbundle.build.phase_order import PHASE_ORDER as _PHASE_ORDER
from agentbundle.build.projection_io import copy_projected_file, ensure_directory_no_follow
from agentbundle.build.projections.direct_directory import (
    ignore_absolute_symlinks,
    sweep_orphans,
)
from agentbundle.build.projections.merge_json import project_merge_json


def _iter_primitives(contract: dict) -> Iterator[str]:
    """Yield Claude Code's projected primitive names in phase order."""
    adapter_block = contract["adapter"]["claude-code"]
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
    """Single-pack convenience wrapper. Delegates to `project_packs`."""
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
        _project_single(
            pack_path,
            contract,
            output_root,
            preserve_existing_metadata=preserve_existing_metadata,
        )
    _sweep_skill_orphans(pack_paths, contract, output_root)


# Mirror of kiro.py:_skill_direct_directory_target — keep in sync.
# A shared helper is barred by the spec's `Never do` boundary (no
# expansion of projections/direct_directory.py beyond `sweep_orphans`).
def _resolve_target(output_root: Path, target_path: str) -> Path:
    """Join a contract ``target-path`` onto ``output_root``, confined.

    ``target-path`` is contract *data*. An absolute value discards the base entirely on join
    (``Path("/a/b") / "/etc/x"`` is ``/etc/x``) and a ``..``-bearing one walks
    out of it — and because the orphan sweep resolves the same value, an
    escaped target becomes the root of a ``shutil.rmtree``. Confine after
    resolution rather than trusting the string (CWE-73, not just CWE-22).
    """
    candidate = output_root / target_path.rstrip("/")
    root_resolved = output_root.resolve()
    try:
        candidate.resolve().relative_to(root_resolved)
    except ValueError:
        raise ValueError(
            f"claude-code: target-path {target_path!r} escapes the output root "
            f"{output_root}"
        ) from None
    return candidate


def _skill_direct_directory_target(contract: dict, output_root: Path) -> Path | None:
    adapter_block = contract["adapter"]["claude-code"]
    for entry in adapter_block.get("projection", []):
        if entry.get("primitive") == "skill" and entry.get("mode") == "direct-directory":
            return _resolve_target(output_root, entry["target-path"])
    return None


# Mirror of kiro.py:_installed_skill_names — keep in sync.
def _installed_skill_names(output_root: Path, target_dir: Path) -> set[str]:
    """Return skill dir names recorded in the repo state file under target_dir.

    Protects skills installed via `agentbundle install` from the orphan
    sweep when `project_packs` runs in self-host mode. Degrades to an empty
    set on absent, legacy, or malformed state so the sweep is unchanged.
    """
    from agentbundle.config import ConfigError, load_state
    try:
        state = load_state(output_root / ".agentbundle-state.toml")
    except ConfigError:
        return set()
    skill_dir_rel = target_dir.relative_to(output_root)
    names: set[str] = set()
    for ps in state.packs.values():
        if ps.scope != "repo":
            continue
        for relpath in ps.files:
            try:
                remainder = Path(relpath).relative_to(skill_dir_rel)
            except ValueError:
                continue
            if remainder.parts:
                names.add(remainder.parts[0])
    return names


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
    expected_names |= _installed_skill_names(output_root, target_dir)
    sweep_orphans(target_dir, expected_names)


def _project_single(
    pack_path: Path,
    contract: dict,
    output_root: Path,
    *,
    preserve_existing_metadata: bool,
) -> None:
    adapter_block = contract["adapter"]["claude-code"]
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
                source_dir, _resolve_target(output_root, rule["target-path"])
            )
        elif mode == "direct-file":
            _resolve_target(output_root, rule["target-path"])  # confinement check
            _project_direct_file(
                source_dir,
                output_root,
                rule["target-path"],
                preserve_existing_metadata=preserve_existing_metadata,
                strip_agent_metadata=primitive_name == "agent",
            )
        elif mode == "merge-json":
            project_merge_json(source_dir, output_root, rule)
        else:
            raise ValueError(f"claude-code: unhandled mode {mode!r} for {primitive_name}")


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
            # symlinks=True preserves relative nested symlinks; absolute
            # targets are filtered out by ignore_absolute_symlinks.
            shutil.copytree(
                entry, destination,
                symlinks=True,
                ignore=ignore_absolute_symlinks,
            )


def _project_direct_file(
    source_dir: Path,
    output_root: Path,
    target_prefix: str,
    *,
    preserve_existing_metadata: bool,
    strip_agent_metadata: bool,
) -> None:
    """Project direct files, omitting source-only metadata from agents only."""
    target_dir = output_root / target_prefix.rstrip("/")
    ensure_directory_no_follow(output_root, target_dir.relative_to(output_root))
    for entry in sorted(source_dir.iterdir()):
        if entry.is_file():
            destination = target_dir / entry.name
            if strip_agent_metadata:
                copy_projected_file(
                    entry,
                    destination,
                    base=output_root,
                    metadata="stat",
                    preserve_existing_metadata=preserve_existing_metadata,
                    transform=lambda content: _strip_agent_metadata(
                        content.decode("utf-8")
                    ).encode("utf-8"),
                )
                continue
            copy_projected_file(
                entry,
                destination,
                base=output_root,
                metadata="stat",
                preserve_existing_metadata=preserve_existing_metadata,
            )


def _strip_agent_metadata(text: str) -> str:
    """Remove the source-only top-level ``metadata`` mapping from frontmatter."""
    if not text.startswith("---\n"):
        return text
    lines = text.splitlines(keepends=True)
    result = [lines[0]]
    skipping_metadata = False
    in_frontmatter = True
    for line in lines[1:]:
        content = line.rstrip("\r\n")
        if in_frontmatter and content == "---":
            in_frontmatter = False
            skipping_metadata = False
            result.append(line)
            continue
        if not in_frontmatter:
            result.append(line)
            continue
        indent = len(content) - len(content.lstrip())
        if skipping_metadata:
            if not content or indent > 0:
                continue
            skipping_metadata = False
        if indent == 0 and content.partition(":")[0] == "metadata":
            skipping_metadata = True
            continue
        result.append(line)
    return "".join(result)
