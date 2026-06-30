# Reachability amendment — review round (2026-06-30)

Spec-stage: adversarial + security both raised a Blocker — open-world terminus
made the backstop forgeable (a fabricated unresolvable cross-repo edge would
false-green a stranded subtree). Resolved: only rollup-RESOLVED satisfied-by-
reference endpoints terminate cleanly; an unresolvable hop is surfaced
informationally, never silently green, never --strict-promoted.

Diff-stage:
- security-reviewer: Clean — ready to commit.
- adversarial-reviewer findings:

**1. AC9 non-overlap leaks for the consumer of a dangling-source edge.** `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py:1130`. A node whose sole producer edge has a dangling source was reported as both DANGLING and UNREACHABLE. Fix: broadened the AC9 skip set to also drop consumers of dangling-source edges (`{b for a,b if a in dangling_set}`); spec AC9 wording aligned; regression test `case_reach_dangling_adjacent_not_double_reported` added. APPLIED.

**2. external-node count inflation.** `lint-traceability.py:1108`. `len(g.nodes)` now includes synthesized external termini. Disposition: DEFER (kept). The count reflects the resolved working graph — consistent with standalone mode's long-standing behavior (which has always counted `_wire`-resolved externals). Cosmetic; noted in PR.
