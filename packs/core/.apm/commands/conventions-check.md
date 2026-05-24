---
description: Lint AGENTS.md, CLAUDE.md, and .claude/ artifacts against the conventions in this repo
---

Run both repo linters and report findings.

**`python tools/lint-agents-md.py`** — AGENTS.md hygiene:

1. Root `AGENTS.md` is under 250 lines.
2. `CLAUDE.md` is either a symlink to `AGENTS.md` or a byte-identical
   copy of it. (Native Windows checkouts can't materialise symlinks
   without elevation, so an identical regular file is accepted; a
   diverged regular file is not.)
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

**`bash tools/lint-credentialed-skills.sh`** — credentialed-skill rules
(skill-secrets spec § AC26 — see `docs/specs/skill-secrets/spec.md`);
scoped to skills whose `SKILL.md` declares `credentialed: true`:

1. The body contains an `### Security rules (non-negotiable)` heading
   and the three RFC-0006 § 4 substrings inside that section (the
   verbatim "Don't" block).
2. For `primitive-class: credentialed-cli`: no script under the skill's
   `scripts/` directory accepts an `argparse` flag whose normalised
   name (strip leading `-`, casefold, `-` → `_`) is one of
   `{token, api_token, api_key, bearer, pat, password}`. Detection
   handles literal strings AND `"--" + "name"`-style concatenation.
3. No script under a credentialed skill's `scripts/` directory contains
   the substring `.agent-ready/credentials.env` unless the opt-out
   comment `# credentialed-primitive: reads-creds-directly` appears
   on the same line.

If any linter is missing or fails to run, fall back to inspecting the
files directly and report the same checks manually. Don't auto-fix
anything — report findings and let the user decide what to do.
