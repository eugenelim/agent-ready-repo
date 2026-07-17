---
description: Check AGENTS.md, CLAUDE.md, and the projected agent artifacts (skills, subagents, commands) against the repo's conventions
---

Verify the conventions below and report findings. If your project ships
linters that cover any of these, run them; otherwise inspect the files
directly and report each check by hand. Don't auto-fix — report findings and
let the user decide.

## AGENTS.md hygiene

1. Root `AGENTS.md` is under 250 lines.
2. `CLAUDE.md` is a symlink to `AGENTS.md`, or a byte-identical copy of it.
   (Native Windows checkouts can't materialise symlinks without elevation, so
   an identical regular file is accepted; a diverged regular file is not.)
3. No subdirectory `AGENTS.md` exceeds 150 lines.
4. Internal links resolve.
5. `docs/CHARTER.md` and the Diátaxis guide subdirectories exist.

## Agent-artifact hygiene (skills, subagents, commands)

1. Every skill, subagent, and command has well-formed YAML frontmatter with
   the required keys (`name`, `description`).
2. Skill directory names match the frontmatter `name`; subagent and command
   filenames match their `name`; all kebab-case.
3. Frontmatter carries no unknown keys.
4. Each skill dir contains a `SKILL.md` and no stray `.md` siblings.
5. Internal markdown links inside each artifact resolve.

## Credentialed-skill rules

Scoped to skills whose `SKILL.md` declares `metadata.credentialed: true`
(project-specific fields live under `metadata:` per the agentskills.io spec):

1. The body contains a `### Security rules (non-negotiable)` heading and the
   three required security substrings inside that section (the verbatim
   "Don't" block).
2. For `metadata.primitive-class: credentialed-cli`: no script under the
   skill's `scripts/` directory accepts an `argparse` flag whose normalised
   name (strip leading `-`, casefold, `-` → `_`) is one of `{token, api_token,
   api_key, bearer, pat, password}`. This covers literal strings and
   `"--" + "name"`-style concatenation.
3. No script under a credentialed skill's `scripts/` directory contains the
   substring `.agentbundle/credentials.env` unless the opt-out comment
   `# credentialed-primitive: reads-creds-directly` appears on the same line.

If you inspect by hand because no linter covers a check, report the same
findings manually. Don't auto-fix anything — report and let the user decide.
