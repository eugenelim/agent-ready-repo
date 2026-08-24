## Blockers

**1. The adversarial dispatch fallback still treats missing mandatory review as summary-only.** `packs/core/.apm/skills/work-loop/SKILL.md:617`. Fix: record mandatory adversarial review as missing, emit `BLOCKED`, and stop readiness; retain named skips only for non-mandatory reviewers.
