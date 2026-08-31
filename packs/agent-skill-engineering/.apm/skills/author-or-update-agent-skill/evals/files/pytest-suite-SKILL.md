---
name: check-migration-plan
description: Review a database migration plan for reversibility and blast radius before it is applied.
metadata:
  boundaries: [filesystem_read_untrusted]
---

# check-migration-plan

Read the supplied migration plan and report reversibility, blast radius, and
the rollback path. Do not modify the plan.

## Verification

The skill ships a Python test suite under `tests/`. Tests import the checker by
bare module name and rely on the suite's working directory being the skill root.
Temporary fixture directories are created in the repository tree and removed at
the end of the session. Parallel runs share one fixture directory to keep the
suite fast.
