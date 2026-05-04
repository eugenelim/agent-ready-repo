---
description: Lint AGENTS.md and CLAUDE.md against the conventions in this repo
---

Run the AGENTS.md linter and report findings. The linter checks:

1. Root `AGENTS.md` is under 250 lines.
2. `CLAUDE.md` is a symlink to `AGENTS.md` (not a duplicate file).
3. Each section header in `AGENTS.md` is referenced from somewhere — orphan
   sections suggest content that drifted out of date.
4. No subdirectory `AGENTS.md` exceeds 150 lines.
5. Internal links resolve.

Run: `bash tools/lint-agents-md.sh`

If the linter is missing or fails to run, fall back to inspecting the files
directly and report the same checks manually. Don't auto-fix anything —
report findings and let the user decide what to do.
