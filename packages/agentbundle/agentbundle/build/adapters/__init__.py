"""Adapter registry — keyed by contract adapter name."""

from __future__ import annotations

from typing import Callable, Dict

from agentbundle.build.adapters import claude_code, codex, copilot, kiro

ADAPTERS: Dict[str, Callable] = {
    "claude-code": claude_code.project,
    "kiro": kiro.project,
    "copilot": copilot.project,
    "codex": codex.project,
}
