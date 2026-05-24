---
description: Lint AGENTS.md, CLAUDE.md, and .claude/ artifacts against the conventions in this repo
---

Run both repo linters and report findings.

**`python tools/lint-agents-md.py`** — AGENTS.md hygiene:

1. Root `AGENTS.md` is under 250 lines.
2. `CLAUDE.md` is a symlink to `AGENTS.md` (not a duplicate file).
3. No subdirectory `AGENTS.md` exceeds 150 lines.
4. Internal links resolve.
5. `docs/CHARTER.md` and the Diátaxis subdirectories exist.

**`python tools/lint-agent-artifacts.py`** — `.claude/` artifact hygiene:

1. Every skill / subagent / command has well-formed YAML frontmatter with
   the required keys (`name`, `description`).
2. Skill directory names match the frontmatter `name`; subagent filenames
   match the frontmatter `name`; kebab-case enforced.
3. Frontmatter has no unknown keys.
4. Skill dirs contain a `SKILL.md` (and no stray `.md` siblings).
5. Internal markdown links inside each artifact resolve.

If either linter is missing or fails to run, fall back to inspecting the
files directly and report the same checks manually. Don't auto-fix
anything — report findings and let the user decide what to do.
