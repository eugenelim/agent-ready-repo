"""Shared `merge-json` projection — claude-code's settings.local.json
and codex's hooks.json share this implementation.

Both adapters' hook-wiring lands in a JSON file with the same
``{ "<managed-key>": { "<event>": [...handlers...] } }`` shape; the
build-pipeline dispatcher in each adapter calls this function for any
projection rule with ``mode == "merge-json"``.

Originally private to ``adapters/claude_code.py`` as
``_project_merge_json``; lifted to this sibling module by
docs/specs/dropped-primitives-coverage (T2) so codex.py can reuse the
exact same code path without re-implementing.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any


def project_merge_json(source_dir: Path, output_root: Path, rule: dict) -> None:
    """Merge TOML hook-wiring source files into a JSON target file.

    Reads every ``*.toml`` under ``source_dir`` (sorted), pulls the
    payload at ``rule["managed-key"]`` (default ``"hooks"``), and
    merges into ``output_root / rule["target-path"]``'s managed key.
    Existing non-managed keys in the JSON target are preserved.

    Output is serialised with ``indent=2, sort_keys=True`` and a
    trailing newline — idempotent across re-runs.
    """
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

    merged = dict(existing.get(managed_key, {}))
    merged.update(incoming)
    existing[managed_key] = merged

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(existing, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
