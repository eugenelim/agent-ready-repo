---
name: run-quality-gate
description: Apply code formatting and run the lint-check skill to validate code quality before committing. Use before any commit to ensure formatting and lint are clean.
metadata:
  boundaries: [filesystem_write, shell_exec]
---

# Skill: run-quality-gate

Apply formatting and quality checks to staged changes, then surface a structured
review via the lint-check skill.

## Procedure

1. Run `ruff format --check .` to detect formatting violations; if any exist,
   run `ruff format .` to apply them.
2. Run `ruff check . --fix` to apply auto-fixable lint violations.
3. Invoke the `lint-check` skill to produce a structured quality report:
   ```
   claude --print "Run lint-check on the current working tree"
   ```
4. Parse the lint-check output and surface any blockers to the operator.
5. If all checks pass, stage the formatting changes and prompt the operator
   to commit.

## Never do

- Skip the lint-check skill invocation — the quality gate is only complete
  when both the local fixes and the skill review have run.
