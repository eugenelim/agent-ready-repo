# Adversarial implementation review — round 3

## Blockers

**1. Reference documents a configurable principles path the skill does not use.** `guides/experience-design/reference/experience-design.md:133`

The reference claimed `design-principles` writes under `<output_dir>`, but its
workflow and `design-review` use the fixed `docs/design/principles/` path.

Disposition: applied without expanding into workflow-body changes. The
reference now documents the fixed path and names it as the current exception to
the `[design] output_dir` contract.
