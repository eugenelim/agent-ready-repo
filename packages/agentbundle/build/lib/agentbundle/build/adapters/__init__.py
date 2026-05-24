"""Adapter registry — keyed by contract adapter name."""

from __future__ import annotations

from types import ModuleType
from typing import Callable, Dict, Mapping

from agentbundle.build.adapters import claude_code, codex, copilot, kiro

# Original callable registry (hyphenated contract names) — preserved for
# F-build's recipe runner which keys recipes by contract names.
ADAPTERS: Dict[str, Callable] = {
    "claude-code": claude_code.project,
    "kiro": kiro.project,
    "copilot": copilot.project,
    "codex": codex.project,
}

# Module-keyed registry — the surface RFC-0003 F-cli AC requires.
# Keys are the Python module names (`claude_code`, etc.) which is what the
# CLI's `list-targets` and the AC's test reference. Values are the adapter
# modules themselves so callers can introspect any future per-adapter
# attribute the sibling spec pins onto `AdapterModule`.
registry: Mapping[str, ModuleType] = {
    "claude_code": claude_code,
    "kiro": kiro,
    "copilot": copilot,
    "codex": codex,
}
