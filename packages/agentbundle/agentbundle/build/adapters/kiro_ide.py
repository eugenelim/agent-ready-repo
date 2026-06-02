"""kiro-ide adapter — projects primitives for the Kiro VS Code-fork IDE.

Targets the Kiro IDE, not the `kiro` CLI binary. Key differences from kiro-cli:

- Agents project as `.md` (YAML frontmatter + body), loaded by the IDE
  via gray-matter. The `kiro-ide-agent-frontmatter-v0.9` mapping applies IDE
  tool ids (read_file, grep_search, etc.) — not CLI short-names.
- `hook-wiring` is DROPPED. The IDE loader silently drops any agent carrying
  a `hooks` key (RFC-0022 E2). Use kiro-ide-hook instead.
- `kiro-ide-hook` is ACTIVATED. Flat projection path confirmed by Q6 probe
  (no-recursion, yes-extension-filter, 2026-06-01, Kiro 0.12.224):
  `.kiro/hooks/<pack>--<name>.kiro.hook`.

The deprecated `kiro` adapter maps to this module (T4).

Phase order (from phase_order.PHASE_ORDER):
  hook-body → agent → kiro-ide-hook → command → skill
  (hook-wiring is skipped — dropped for kiro-ide).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any, Iterator

from agentbundle.build.phase_order import PHASE_ORDER as _PHASE_ORDER
from agentbundle.build.projections.direct_directory import sweep_orphans
from agentbundle.build.projections.kiro_ide_hook import project as kiro_ide_hook_project

# Import frontmatter helpers from kiro.py (pure functions, no side effects).
from agentbundle.build.adapters.kiro import (
    _split_frontmatter,
    _parse_frontmatter,
    _apply_mapping,
    _project_direct_directory,
    _project_direct_file,
    _project_direct_file_template,
    _resolve_kiro_hook_body_target_dir as _resolve_hook_body_target_dir_from_kiro,
)

_ADAPTER = "kiro-ide"


def project(pack_path: Path, contract: dict, output_root: Path) -> None:
    """Single-pack convenience wrapper. Delegates to `project_packs`."""
    project_packs([pack_path], contract, output_root)


def project_packs(pack_paths: list[Path], contract: dict, output_root: Path) -> None:
    """Project every pack in `pack_paths` using the kiro-ide adapter block."""
    for pack_path in pack_paths:
        _project_single(pack_path, contract, output_root)
    _sweep_skill_orphans(pack_paths, contract, output_root)


def _skill_direct_directory_target(contract: dict, output_root: Path) -> Path | None:
    adapter_block = contract["adapter"][_ADAPTER]
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


def _iter_primitives(contract: dict) -> Iterator[str]:
    """Yield kiro-ide's projected primitive names in phase order.

    Skips hook-wiring (dropped for kiro-ide) and any dropped table-form
    entries. kiro-ide-hook is included when its mode is not dropped.
    """
    adapter_block = contract["adapter"][_ADAPTER]
    array_form = {e["primitive"]: e for e in adapter_block.get("projection", [])}
    table_form = adapter_block.get("projections", {}) or {}

    for primitive_name in _PHASE_ORDER:
        if primitive_name in array_form:
            if array_form[primitive_name].get("mode") == "dropped":
                continue
            yield primitive_name
        elif primitive_name in table_form:
            rule = table_form[primitive_name]
            effective_mode = rule.get("mode")
            if isinstance(effective_mode, dict):
                effective_mode = effective_mode.get("repo")
            if effective_mode == "dropped":
                continue
            yield primitive_name


def _project_single(pack_path: Path, contract: dict, output_root: Path) -> None:
    adapter_block = contract["adapter"][_ADAPTER]
    array_form = {e["primitive"]: e for e in adapter_block.get("projection", [])}
    table_form = adapter_block.get("projections", {}) or {}

    for primitive_name in _iter_primitives(contract):
        # kiro-ide-hook: source dir is implicit (.apm/kiro-ide-hooks/),
        # dispatch to the dedicated projector directly.
        if primitive_name == "kiro-ide-hook":
            rule = table_form.get("kiro-ide-hook", {})
            _dispatch_kiro_ide_hook(pack_path, output_root, rule, contract)
            continue

        prim_def = contract["primitive"].get(primitive_name)
        if prim_def is None:
            continue
        source_dir = pack_path / prim_def["source-path"].rstrip("/")
        if not source_dir.exists():
            continue

        if primitive_name in array_form:
            rule = array_form[primitive_name]
            _dispatch_array_form(primitive_name, source_dir, output_root, rule, contract)
        else:
            rule = table_form[primitive_name]
            _dispatch_table_form(primitive_name, source_dir, output_root, rule)


def _dispatch_array_form(
    primitive_name: str,
    source_dir: Path,
    output_root: Path,
    rule: dict,
    contract: dict,
) -> None:
    mode = rule["mode"]
    if mode == "direct-directory":
        _project_direct_directory(source_dir, output_root / rule["target-path"].rstrip("/"))
    elif mode == "direct-file":
        if primitive_name == "agent":
            _project_agent_as_md(source_dir, output_root, rule, contract)
        else:
            _project_direct_file(source_dir, output_root, rule["target-path"])
    else:
        raise ValueError(f"kiro-ide: unhandled array-form mode {mode!r} for {primitive_name}")


def _dispatch_table_form(
    primitive_name: str,
    source_dir: Path,
    output_root: Path,
    rule: dict,
) -> None:
    mode = rule.get("mode")
    effective_mode = mode["repo"] if isinstance(mode, dict) else mode

    if effective_mode == "direct-file":
        target = rule.get("target")
        target_template = target.get("repo") if isinstance(target, dict) else target
        if target_template:
            _project_direct_file_template(source_dir, output_root, target_template)


def _dispatch_kiro_ide_hook(
    pack_path: Path,
    output_root: Path,
    rule: dict,
    contract: dict,
) -> None:
    """Delegate kiro-ide-hook projection to the dedicated projector.

    Uses the flat target path confirmed by Q6 probe:
    `.kiro/hooks/<pack>--<name>.kiro.hook`
    """
    target = rule.get("target")
    if isinstance(target, dict):
        target_template = target.get("repo")
    else:
        target_template = target
    if not target_template:
        return

    # Resolve hook-body target dir from the kiro-ide adapter block.
    # The kiro-ide block has hook-body in the array form (tools/hooks/)
    # so we look there first.
    adapter_block = contract.get("adapter", {}).get(_ADAPTER, {})
    hook_body_target_dir = "tools/hooks"
    for entry in adapter_block.get("projection", []):
        if entry.get("primitive") == "hook-body" and entry.get("mode") == "direct-file":
            hook_body_target_dir = entry.get("target-path", "tools/hooks/").rstrip("/")
            break

    kiro_ide_hook_project(
        pack_path,
        output_root,
        target_template=target_template,
        hook_body_target_dir=hook_body_target_dir,
    )


# ---------------------------------------------------------------------------
# Agent .md → .md rewrite (kiro-ide specific)
# ---------------------------------------------------------------------------


def _project_agent_as_md(
    source_dir: Path,
    output_root: Path,
    rule: dict,
    contract: dict,
) -> None:
    """Read `.apm/agents/<name>.md` and emit `.kiro/agents/<name>.md`.

    The source format is YAML-style frontmatter (--- fence) + markdown body.
    The output preserves the markdown format but rewrites frontmatter fields
    through the `kiro-ide-agent-frontmatter-v0.9` mapping table (IDE tool ids,
    model aliases). No CLI-only keys (hooks, allowedTools, toolsSettings,
    mcpServers) appear in the output — these are not in the mapping table
    and would cause the IDE loader to silently drop the agent.
    """
    target_dir = output_root / rule["target-path"].rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)

    mapping_name = rule.get("frontmatter-mapping")
    mapping = (
        contract.get("frontmatter-mapping", {}).get(mapping_name, {})
        if mapping_name
        else {}
    )

    for entry in sorted(source_dir.iterdir()):
        if not (entry.is_file() and entry.suffix == ".md"):
            continue
        frontmatter, body = _split_frontmatter(entry.read_text(encoding="utf-8"))
        rewritten = _apply_mapping(frontmatter, mapping)

        # Ensure name is present (derived from filename if not in frontmatter).
        agent_name = rewritten.get("name") or entry.stem
        rewritten["name"] = agent_name

        output_text = _serialize_frontmatter_md(rewritten) + body
        destination = target_dir / entry.name  # preserves .md extension
        destination.write_text(output_text, encoding="utf-8")


def _serialize_frontmatter_md(fields: dict[str, Any]) -> str:
    """Emit a YAML frontmatter block for a kiro-ide .md agent file.

    Produces `--- ... ---\n` wrapping. Strings are plain scalars unless they
    contain YAML-special characters, in which case they are double-quoted.
    Lists are emitted as YAML flow sequences: `[item1, item2]`. The gray-matter
    parser in the Kiro IDE accepts both styles.
    """
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, list):
            items = ", ".join(str(v) for v in value)
            lines.append(f"{key}: [{items}]")
        elif isinstance(value, str):
            # Quote strings that contain YAML-special characters.
            if any(c in value for c in ':#{}[]|>&*!,\'"'):
                escaped = value.replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'{key}: "{escaped}"')
            else:
                lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"
