#!/usr/bin/env python3
"""work-loop activation hook: prints a per-prompt reminder to use the
work-loop skill for non-trivial work.

Wired to the per-prompt event of each tool's hook surface — Claude Code
`UserPromptSubmit`, the Codex equivalent in `.codex/hooks.json`, and the
Copilot / Cursor / Gemini equivalents. Kiro IDE gets the same nudge via a
companion `promptSubmit` hook that carries the *same* instruction as a
prompt (the IDE drops hook-wiring and `runCommand` does not feed the
agent), so keep the two messages semantically aligned (both must mention
`work-loop`). See `tools/hooks/README.md` § Wiring for what lands where.

Pure-stdlib, input-free: prints a fixed reminder to stdout and exits 0.
It deliberately does not parse the prompt or classify triviality — that
judgment is the agent's, governed by the work-loop skill's own
"When this skill applies". Reading no stdin/env/files keeps it off every
security boundary.
"""

from __future__ import annotations

import sys

# Spec work-loop-activation-hook AC1: keep this reminder <= 6 lines (the
# focused test asserts the bound; the companion .kiro.hook prompt mirrors it).
REMINDER = """\
=== work-loop ===
Before non-trivial work (a feature, a multi-file fix, a refactor, a
migration, anything beyond a one-line edit), load the work-loop skill
and run plan -> execute -> verify -> review with mechanical gates.
Pick the mode by risk: light by default, full when a risk trigger fires.
Skip only for a genuine one-line edit."""


def main() -> int:
    print(REMINDER)
    return 0


if __name__ == "__main__":
    sys.exit(main())
