# Verification ledger — aesthetic-style-direction

Execution observations and the manual-QA verdicts the spec's Testing Strategy
names. Goal-based results live in the PR; this file carries the judgements no
command reaches.

## Manual-QA verdicts

Reviewer: eugenelim (via the orchestrating session). Date: 2026-09-18.

**1. Does each axis cell name a role, classification, or relationship rather
than a value?** — **Pass.** Read all fifteen cells in
`creative-direction-template.md` and all forty-five across the three presets.
Every cell opens with a bracketed classification token and continues in
relational prose ("transformations preserve its reading order", "one dominant
axis with deliberate offset relationships"). No cell names a measurement, a
colour, or a typeface. The pack lint agrees at the literal level, but that only
covers units and stack tokens; this verdict covers the rest.

**2. Do each preset's formal commitments match blueprint §F2.2?** — **Pass with
one note.** Swiss carries all seven §F2.2 commitments including near-zero
ornament and restrained colour. Bauhaus carries all four plus the explicit note
that the primary-colours-and-primitives shorthand is recognisable but not a
rule, which §F2.2 also flags. Editorial carries the rigid column grammar, type
hierarchy, modular story units, rules, and image-caption relationships.
*Note:* a preset's vocabulary column omits `[platform-default]`, diverging from
the template's column. This is deliberate and correct — a preset decides every
axis, so offering the undecided token would be noise — but it means a preset's
vocabulary column is not a byte copy of the template's. The token-agreement
check compares *used* tokens against the template's vocabularies and passes.

**3. Are the divergence audit's comparison rules stated and unambiguous?** —
**Pass.** All four cases the criterion names are stated explicitly: differing
token tuples differ; prose after identical tokens is not compared; matching
`[platform-default]` is not a difference; `[platform-default]` against a decided
token is. The module also states its refusals, which is what stops a composite
score reappearing.

**4. Is the guide sufficient?** — **Pass.** `establish-design-intent.md` covers
all four capabilities in an adopter's terms, explains what `[platform-default]`
means and why structure leads, and states that a preset is a starting direction
needing its own grounding. It declares no new output path.

## Execution observations

- The pack lint (`tools/lint-experience-agnostic.py`) passed on the first
  post-wave run. It was the plan's highest-rated risk and did not materialise:
  none of the preset vocabulary — Swiss, Bauhaus, sans-serif, grid, geometry —
  is matched by its rule set.
- Two regressions came out of the parallel wave and were repaired:
  - The implementer stripped the backticks from `**Writes:**` and
    `**Confinement:**` in `creative-direction/SKILL.md`, failing three roster
    assertions. **Cause: the spec quoted both lines unbackticked**, so the
    worker normalised the file to match the spec. The spec's `Always do` now
    states the backticks are part of the asserted string.
  - The guide implementer added `## Make the direction discriminating` to a
    guidebook-step page, where `##` is reserved for `Run` blocks
    (`tools/lint-guidebook-steps.py` exit 2). Demoted it and its three children
    one level; the step contract is satisfied and the content is unchanged.
- One check in the T1 brief was wrong, not the work: it asked for
  `grep -c 'platform-default'` to reach 33, but `grep -c` counts matching
  *lines*, and the correct answer is 16 (fifteen rows plus the comment). The
  worker surfaced this rather than editing the file to fit; that was right.
- The divergence-audit module initially reprinted the template's empty
  "This direction commits to" column, which is meaningless in a reference
  module. Narrowed to axis and vocabulary.
