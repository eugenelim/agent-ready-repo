# Adversarial implementation review — round 2

## Blockers

**1. Reference still exposes a non-canonical design output placeholder.** `guides/experience-design/reference/experience-design.md:229`

Two copy entries used `<design_output_dir>` while other skill contracts used
`<parent>`, and the layout section did not define the canonical resolved value
of `[design] output_dir` consistently.

Disposition: applied. Every artifact path now uses `<output_dir>`, and the
layout section defines it as the resolved `[design] output_dir` value.
