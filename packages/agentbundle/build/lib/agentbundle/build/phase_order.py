"""Build-pipeline phase order (RFC-0005 § Build-pipeline ordering invariant).

Single source of truth for the order primitives project within each
pack: ``hook-body`` → ``agent`` → ``hook-wiring`` → ``command`` →
``skill``. The order matters because Kiro's ``merge-into-agent-json``
projection reads the agent JSON the agent projection wrote, so agents
must land first.

Each reference adapter (``claude_code``, ``kiro``, ``copilot``,
``codex``) imports ``PHASE_ORDER`` from this module so a future
contract revision changes one line, not four.
"""

from __future__ import annotations


PHASE_ORDER: tuple[str, ...] = (
    "hook-body",
    "agent",
    "hook-wiring",
    "command",
    "skill",
)
