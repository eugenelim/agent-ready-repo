"""Copilot adapter — projects skills as per-file instructions, hook
bodies straight through, drops everything else.

Skill instruction frontmatter (`applyTo: "**"` etc.) comes from the
contract's `frontmatter-default["copilot-instruction"]` table — never
hardcoded.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Iterator


# RFC-0005 § Build-pipeline ordering invariant — uniform across adapters.
from agentbundle.build.phase_order import PHASE_ORDER as _PHASE_ORDER


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

        if mode == "instruction-file":
            _project_instruction_file(source_dir, output_root, rule, contract)
        elif mode == "direct-file":
            _project_direct_file(source_dir, output_root, rule["target-path"])
        else:
            raise ValueError(f"copilot: unhandled mode {mode!r} for {primitive_name}")


def _project_direct_file(source_dir: Path, output_root: Path, target_prefix: str) -> None:
    target_dir = output_root / target_prefix.rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source_dir.iterdir()):
        if entry.is_file():
            shutil.copy2(entry, target_dir / entry.name, follow_symlinks=False)


def _project_instruction_file(
    source_dir: Path,
    output_root: Path,
    rule: dict,
    contract: dict,
) -> None:
    target_dir = output_root / rule["target-path"].rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    default_name = rule.get("frontmatter-default")
    defaults = (
        contract.get("frontmatter-default", {}).get(default_name, {})
        if default_name
        else {}
    )

    for skill_dir in sorted(source_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            md_candidates = sorted(skill_dir.glob("*.md"))
            if not md_candidates:
                continue
            skill_md = md_candidates[0]
        frontmatter, body = _split_frontmatter(skill_md.read_text(encoding="utf-8"))
        for key, value in defaults.items():
            frontmatter.setdefault(key, value)
        destination = target_dir / f"{skill_dir.name}.instructions.md"
        destination.write_text(_emit_frontmatter(frontmatter) + body, encoding="utf-8")


def _split_frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines(keepends=True)
    if not lines or not lines[0].startswith("---"):
        return {}, text
    end_index = None
    for index in range(1, len(lines)):
        if lines[index].startswith("---"):
            end_index = index
            break
    if end_index is None:
        return {}, text
    frontmatter_lines = lines[1:end_index]
    body = "".join(lines[end_index + 1 :])
    return _parse_frontmatter(frontmatter_lines), body


def _parse_frontmatter(lines: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in lines:
        stripped = line.rstrip("\n")
        if not stripped.strip() or stripped.lstrip().startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        result[key.strip()] = value
    return result


def _emit_frontmatter(frontmatter: dict[str, Any]) -> str:
    if not frontmatter:
        return ""
    lines = ["---"]
    for key in sorted(frontmatter.keys()):
        value = frontmatter[key]
        lines.append(f'{key}: "{value}"')
    lines.append("---\n")
    return "\n".join(lines)
