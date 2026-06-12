"""Adapter registry — keyed by contract adapter name."""

from __future__ import annotations

import warnings
from pathlib import Path
from types import ModuleType
from typing import Callable, Dict, Mapping

from agentbundle.build.adapters import claude_code, codex, copilot, cursor, kiro, kiro_cli, kiro_ide


def _kiro_alias_project(pack_path: Path, contract: dict, output_root: Path) -> None:
    """Deprecated alias: `kiro` → `kiro-ide`. Emits a build-time warning."""
    warnings.warn(
        "kiro: deprecated alias for kiro-ide; update allowed-adapters in pack.toml",
        DeprecationWarning,
        stacklevel=2,
    )
    kiro_ide.project(pack_path, contract, output_root)


# Original callable registry (hyphenated contract names) — preserved for
# F-build's recipe runner which keys recipes by contract names.
ADAPTERS: Dict[str, Callable] = {
    "claude-code": claude_code.project,
    "kiro-ide": kiro_ide.project,
    "kiro-cli": kiro_cli.project,
    "kiro": _kiro_alias_project,  # deprecated alias → kiro-ide (RFC-0022 D1)
    "copilot": copilot.project,
    "cursor": cursor.project,
    "codex": codex.project,
}

# Module-keyed registry — the surface RFC-0003 F-cli AC requires.
# Keys are the Python module names (`claude_code`, etc.) which is what the
# CLI's `list-targets` and the AC's test reference. Values are the adapter
# modules themselves so callers can introspect any future per-adapter
# attribute the sibling spec pins onto `AdapterModule`.
registry: Mapping[str, ModuleType] = {
    "claude_code": claude_code,
    "kiro_ide": kiro_ide,
    "kiro_cli": kiro_cli,
    "kiro": kiro,  # legacy module; use kiro_ide for new code
    "copilot": copilot,
    "cursor": cursor,
    "codex": codex,
}
