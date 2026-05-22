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

import json
import shutil
import tomllib
from pathlib import Path
from typing import Any


def project(pack_path: Path, contract: dict, output_root: Path) -> None:
    """Project a single pack into `output_root` per the Claude Code adapter rules."""
    rules = contract["adapter"]["claude-code"]["projection"]
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
            _project_direct_file(source_dir, output_root, rule["target-path"])
        elif mode == "merge-json":
            _project_merge_json(source_dir, output_root, rule)
        else:
            raise ValueError(f"claude-code: unhandled mode {mode!r} for {primitive_name}")


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


def _project_merge_json(source_dir: Path, output_root: Path, rule: dict) -> None:
    target_path = output_root / rule["target-path"].lstrip("/")
    managed_key = rule.get("managed-key", "hooks")

    incoming: dict[str, Any] = {}
    for entry in sorted(source_dir.iterdir()):
        if entry.is_file() and entry.suffix == ".toml":
            payload = tomllib.loads(entry.read_text(encoding="utf-8"))
            for key, value in payload.get(managed_key, {}).items():
                incoming[key] = value
    if not incoming:
        return

    existing: dict[str, Any] = {}
    if target_path.exists():
        existing = json.loads(target_path.read_text(encoding="utf-8"))

    merged_hooks = dict(existing.get(managed_key, {}))
    merged_hooks.update(incoming)
    existing[managed_key] = merged_hooks

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(existing, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
