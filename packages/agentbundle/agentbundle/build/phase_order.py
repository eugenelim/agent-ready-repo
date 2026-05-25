"""Build-pipeline phase order (RFC-0005 § Build-pipeline ordering invariant).

Single source of truth for the order primitives project within each
pack: ``hook-body`` → ``agent`` → ``hook-wiring`` → ``kiro-ide-hook``
→ ``command`` → ``skill``.

Two real dependencies drive the order:

  1. **hook-wiring ← agent.** Kiro's ``merge-into-agent-json``
     projection reads the agent JSON the agent projection wrote.
  2. **kiro-ide-hook ← hook-body** (RFC-0005 § Substitution rules,
     v0.4). The ``kiro-ide-hook`` projector expands
     ``${hook-body:<name>}`` placeholders in ``then.command`` to
     the projected hook-body path. The hook-body files must already
     exist (or at least be enumerable) when the substitution runs.

Every other ordering — ``hook-body`` → ``agent``, ``hook-wiring`` →
``kiro-ide-hook``, ``command`` and ``skill`` relative to anything
else — is a **tiebreak**, not a dependency. The strict serial order
above is the picked tiebreak, pinned for *operational* determinism
(log ordering, partial-state-on-failure semantics, rollback
target). RFC-0005 § Substitution rules → *Why serial rather than
DAG-parallel* spells this out.

Each reference adapter (``claude_code``, ``kiro``, ``copilot``,
``codex``) imports ``PHASE_ORDER`` from this module so a future
contract revision changes one line, not four.
"""

from __future__ import annotations


PHASE_ORDER: tuple[str, ...] = (
    "hook-body",
    "agent",
    "hook-wiring",
    "kiro-ide-hook",
    "command",
    "skill",
)
