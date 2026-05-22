"""Adapter registry.

Each adapter module (claude_code, kiro, copilot, codex) exports a
`project(pack_path, contract, output_root)` function. The build
pipeline dispatches on a recipe's declared `target` to one of these.
Adapters land in T2–T5; this stub provides the dispatch surface only.
"""

from __future__ import annotations

from typing import Callable

# Adapter registry — filled in by T2–T5. The pipeline imports `ADAPTERS`
# and looks up by target name; an unknown target is an explicit error.
ADAPTERS: dict[str, Callable] = {}
