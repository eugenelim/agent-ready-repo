---
name: review-database-migration
description: Use when the user asks to review a database migration plan before execution.
metadata:
  boundaries: [filesystem_read_untrusted]
---

# Review database migration

Read the named migration plan. Report unsafe ordering, missing rollback steps,
and verification gaps. Do not execute the migration or modify files.
