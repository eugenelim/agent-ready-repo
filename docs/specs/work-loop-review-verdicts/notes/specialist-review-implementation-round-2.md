## Blockers

**1. Mandatory named skips still take the clean transition.** `packs/core/.apm/skills/work-loop/SKILL.md:671`. REVIEW still says all warranted reviewers being clean or named skips can write `Status: Shipped`, fire `reviewers-clean`, and use the `--all-skipped` path, so a mandatory named skip can advance the loop before verdict precedence blocks it. Fix: mandatory named skips block before `Status: Shipped`; only non-mandatory skips may use the residual or all-skipped path.
