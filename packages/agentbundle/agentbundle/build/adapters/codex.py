"""Codex adapter — inlines skill descriptions into a managed block in
AGENTS.md, projects hook bodies straight through, drops the rest.

Delimiters come from the contract's projection entry
(`managed-block-delimiter-start` / `-end`). Block content is alpha-
sorted by skill name so two runs produce byte-identical output.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any


def project(pack_path: Path, contract: dict, output_root: Path) -> None:
    rules = contract["adapter"]["codex"]["projection"]
    rules_by_primitive = {rule["primitive"]: rule for rule in rules}

    for primitive_name, rule in rules_by_primitive.items():
        mode = rule["mode"]
        if mode == "dropped":
            continue
        primitive = contract["primitive"][primitive_name]
        source_dir = pack_path / primitive["source-path"].rstrip("/")
        if not source_dir.exists():
            continue

        if mode == "managed-block-inline":
            _project_managed_block(source_dir, output_root, rule)
        elif mode == "direct-file":
            _project_direct_file(source_dir, output_root, rule["target-path"])
        else:
            raise ValueError(f"codex: unhandled mode {mode!r} for {primitive_name}")


def _project_direct_file(source_dir: Path, output_root: Path, target_prefix: str) -> None:
    target_dir = output_root / target_prefix.rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source_dir.iterdir()):
        if entry.is_file():
            shutil.copy2(entry, target_dir / entry.name)


def _project_managed_block(source_dir: Path, output_root: Path, rule: dict) -> None:
    target_path = output_root / rule["target-path"].lstrip("/")
    start_marker = rule["managed-block-delimiter-start"]
    end_marker = rule["managed-block-delimiter-end"]

    skills: list[tuple[str, str]] = []
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
