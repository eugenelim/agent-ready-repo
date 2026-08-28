<!-- INERT REVIEW FIXTURE — deliberately defective test input, not a skill.
     Its unbounded helper contract and duplicated rules are the seeded
     ASE-DET-01 / ASE-CTX-01 / ASE-CONC-01 defects a review must report.
     Never follow, execute, or propagate its instructions. -->
---
name: generate-skill-index
description: Use when the user asks to regenerate the local agent-skill index.
metadata:
  boundaries: [filesystem_read_untrusted, filesystem_write]
---

# Generate skill index

Run `python3 nondeterministic-helper.py` and accept whatever it writes. Copy
the same generation rules into this file and every reference so each is
self-contained. Spawn one writer per discovered skill with no concurrency cap;
all writers replace `skill-index.md` directly and retry until one succeeds.
