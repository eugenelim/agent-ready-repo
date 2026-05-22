"""Kiro adapter — projects skills, agents (with frontmatter mapping),
hook bodies, degrades hook wiring (RFC-0001 Q1), drops commands.

Frontmatter rewrite rules for `agent` primitives come from the contract's
`frontmatter-mapping["kiro-agent-frontmatter-v0.9"]` table — never
hardcoded here. Stdlib only: a minimal YAML-frontmatter parser handles
the leading `---` block of each agent file.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any


def project(pack_path: Path, contract: dict, output_root: Path) -> None:
    rules = contract["adapter"]["kiro"]["projection"]
    rules_by_primitive = {rule["primitive"]: rule for rule in rules}

    for primitive_name, rule in rules_by_primitive.items():
        mode = rule["mode"]
        if mode == "dropped":
            continue
        primitive = contract["primitive"][primitive_name]
        source_dir = pack_path / primitive["source-path"].rstrip("/")
        if not source_dir.exists():
            continue

        if mode == "direct-directory":
            _project_direct_directory(source_dir, output_root / rule["target-path"].rstrip("/"))
        elif mode == "direct-file":
            if primitive_name == "agent":
                _project_agent_with_frontmatter(source_dir, output_root, rule, contract)
            else:
                _project_direct_file(source_dir, output_root, rule["target-path"])
        elif mode == "degraded-info-log":
            _emit_info_log(primitive_name, source_dir)
        else:
            raise ValueError(f"kiro: unhandled mode {mode!r} for {primitive_name}")


def _project_direct_directory(source_dir: Path, target_dir: Path) -> None:
    for entry in sorted(source_dir.iterdir()):
        if entry.is_dir():
            destination = target_dir / entry.name
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(entry, destination)


def _project_direct_file(source_dir: Path, output_root: Path, target_prefix: str) -> None:
    target_dir = output_root / target_prefix.rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source_dir.iterdir()):
        if entry.is_file():
            destination = target_dir / entry.name
            shutil.copy2(entry, destination)


def _project_agent_with_frontmatter(
    source_dir: Path,
    output_root: Path,
    rule: dict,
    contract: dict,
) -> None:
    target_dir = output_root / rule["target-path"].rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    mapping_name = rule.get("frontmatter-mapping")
    mapping = (
        contract.get("frontmatter-mapping", {}).get(mapping_name, {})
        if mapping_name
        else {}
    )
    for entry in sorted(source_dir.iterdir()):
        if entry.is_file() and entry.suffix == ".md":
            frontmatter, body = _split_frontmatter(entry.read_text(encoding="utf-8"))
            rewritten = _apply_mapping(frontmatter, mapping)
            destination = target_dir / entry.name
            destination.write_text(
                _emit_frontmatter(rewritten) + body,
                encoding="utf-8",
            )


def _emit_info_log(primitive_name: str, source_dir: Path) -> None:
    for entry in sorted(source_dir.iterdir()):
        if entry.is_file():
            stem = entry.stem
            print(
                f"[info] kiro: {primitive_name} {stem} not projected — "
                "kiro hook schema unresolved (RFC-0001 Q1)",
                file=sys.stderr,
            )


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
        if value.startswith("[") and value.endswith("]"):
            items = [item.strip() for item in value[1:-1].split(",") if item.strip()]
            result[key.strip()] = items
        else:
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            result[key.strip()] = value
    return result


def _apply_mapping(frontmatter: dict[str, Any], mapping: dict) -> dict[str, Any]:
    rewritten: dict[str, Any] = {}
    for source_key, value in frontmatter.items():
        rule = mapping.get(source_key, {})
        new_key = rule.get("rename", source_key)
        normalize = rule.get("normalize")
        if normalize == "to-list" and not isinstance(value, list):
            value = [value]
        rewritten[new_key] = value
    for source_key, rule in mapping.items():
        default_value = rule.get("default")
        new_key = rule.get("rename", source_key)
        if new_key not in rewritten and default_value is not None:
            rewritten[new_key] = default_value
    return rewritten


def _emit_frontmatter(frontmatter: dict[str, Any]) -> str:
    if not frontmatter:
        return ""
    lines = ["---"]
    for key in sorted(frontmatter.keys()):
        value = frontmatter[key]
        if isinstance(value, list):
            rendered = "[" + ", ".join(value) + "]"
            lines.append(f"{key}: {rendered}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---\n")
    return "\n".join(lines)
