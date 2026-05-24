"""Codex adapter — inlines skill descriptions into a managed block in
AGENTS.md, projects hook bodies straight through, drops the rest.

Delimiters come from the contract's projection entry
(`managed-block-delimiter-start` / `-end`). Block content is alpha-
sorted by skill name so two runs produce byte-identical output.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Iterator


# RFC-0005 § Build-pipeline ordering invariant — uniform across adapters.
from agentbundle.build.phase_order import PHASE_ORDER as _PHASE_ORDER


def _iter_primitives(contract: dict) -> Iterator[str]:
    """Yield Codex's projected primitive names in phase order."""
    adapter_block = contract["adapter"]["codex"]
    array_form = {entry["primitive"]: entry for entry in adapter_block.get("projection", [])}
    for primitive_name in _PHASE_ORDER:
        if primitive_name in array_form and array_form[primitive_name].get("mode") != "dropped":
            yield primitive_name


def project(pack_path: Path, contract: dict, output_root: Path) -> None:
    project_packs([pack_path], contract, output_root)


def project_packs(pack_paths: list[Path], contract: dict, output_root: Path) -> None:
    adapter_block = contract["adapter"]["codex"]
    rules_by_primitive = {entry["primitive"]: entry for entry in adapter_block.get("projection", [])}

    for primitive_name in _iter_primitives(contract):
        rule = rules_by_primitive[primitive_name]
        mode = rule["mode"]
        primitive = contract["primitive"][primitive_name]
        source_dirs = [
            pack_path / primitive["source-path"].rstrip("/")
            for pack_path in pack_paths
        ]
        source_dirs = [source_dir for source_dir in source_dirs if source_dir.exists()]
        if not source_dirs:
            continue

        if mode == "managed-block-inline":
            _project_managed_block(source_dirs, output_root, rule)
        elif mode == "direct-file":
            for source_dir in source_dirs:
                _project_direct_file(source_dir, output_root, rule["target-path"])
        else:
            raise ValueError(f"codex: unhandled mode {mode!r} for {primitive_name}")


def _project_direct_file(source_dir: Path, output_root: Path, target_prefix: str) -> None:
    target_dir = output_root / target_prefix.rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source_dir.iterdir()):
        if entry.is_file():
            shutil.copy2(entry, target_dir / entry.name, follow_symlinks=False)


def _project_managed_block(
    source_dirs: list[Path],
    output_root: Path,
    rule: dict,
) -> None:
    target_path = output_root / rule["target-path"].lstrip("/")
    start_marker = rule["managed-block-delimiter-start"]
    end_marker = rule["managed-block-delimiter-end"]

    skills: list[tuple[str, str]] = []
    for source_dir in source_dirs:
        for skill_dir in sorted(source_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                md_candidates = sorted(skill_dir.glob("*.md"))
                if not md_candidates:
                    continue
                skill_md = md_candidates[0]
            description = _extract_description(skill_md.read_text(encoding="utf-8"))
            # Refuse either the directory name or the description carrying a
            # delimiter literal — both land in the managed block via
            # f"- **{name}** — {description}" and either would break the
            # splice on the next idempotent run.
            for field_name, field_value in (
                ("name", skill_dir.name),
                ("description", description),
            ):
                if start_marker in field_value or end_marker in field_value:
                    raise ValueError(
                        f"codex: skill {skill_dir.name!r} {field_name} contains a "
                        f"managed-block delimiter — refusing to splice."
                    )
            skills.append((skill_dir.name, description))

    skills.sort()
    block_lines = [start_marker]
    for name, description in skills:
        block_lines.append(f"- **{name}** — {description}")
    block_lines.append(end_marker)
    managed_block = "\n".join(block_lines) + "\n"

    existing = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
    new_content = _splice_managed_block(existing, start_marker, end_marker, managed_block)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(new_content, encoding="utf-8")


def _extract_description(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith("---"):
        for index in range(1, len(lines)):
            if lines[index].startswith("---"):
                break
            stripped = lines[index].strip()
            if stripped.startswith("description:"):
                value = stripped.partition(":")[2].strip()
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]
                return value
    for line in lines:
        if line.strip() and not line.startswith("#"):
            return line.strip()
    return ""


def _splice_managed_block(
    existing: str,
    start_marker: str,
    end_marker: str,
    managed_block: str,
) -> str:
    if start_marker in existing and end_marker in existing:
        start_index = existing.index(start_marker)
        end_index = existing.index(end_marker) + len(end_marker)
        if end_index < len(existing) and existing[end_index] == "\n":
            end_index += 1
        return existing[:start_index] + managed_block + existing[end_index:]
    if existing and not existing.endswith("\n"):
        existing += "\n"
    return existing + managed_block
