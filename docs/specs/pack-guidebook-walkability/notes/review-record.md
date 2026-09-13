# Pre-EXECUTE review record

All rounds ran on Codex `gpt-5.6-sol` at `model_reasoning_effort="medium"`, each
in a fresh session. The author reviewed nothing it wrote. Every finding was
verified against the repository before any repair; none was refuted.

## Finding trend, split by origin

The split is what the stop decision rests on. An undivided count cannot tell a
contract still yielding defects from one whose findings are churn its own
repairs introduced, and those call for opposite decisions.

| Round | Scope | Blockers | Concerns | In settled text | In the round's own repairs |
| --- | --- | --- | --- | --- | --- |
| 1 — adversarial | spec, plan, records | 8 | 4 | 8 | 0 |
| 2 — adversarial | the same, plus round-1 repairs | 6 | 3 | 2 | 4 |
| 3 — adversarial | the same, plus round-2 repairs | 6 | 1 | 0 | 6 |
| 4 — narrow verification | round-3 repairs only | 1 open of 7 | — | 0 | 1 |
| Design gate | design intent against three governing artifacts | 1 | 3 majors | 4 | 0 |
| 5 — narrow verification | design-gate repairs only | 1 open of 4 | — | 0 | 1 |

**Why review stopped.** By round 3 no finding came from text the reviews had
not already changed, and round 3's own reviewer recommended making the bounded
propagation fixes and then building. Rounds 4 and 5 were therefore narrow
verifications of specific repairs rather than fresh broad rounds, and each
closed every item but one, which was then fixed and confirmed directly. The
contract has stopped yielding defects in settled text.

## The one deep finding, and what it cost

Round 1's review did not find the slice's real defect — that came from a
read-only decision-adviser turn before authoring, which established that the
inherited "three whole-pack handoffs" premise was false against the packs' own
Shipped contracts. Rounds 1 to 3 then spent most of their findings on
**incomplete propagation of that one correction** into criteria, oracles, task
prose and sibling records. The lesson is recorded in
[`walk-premise-correction.md`](walk-premise-correction.md): a premise change is
not one edit, and the rounds after it are where its companions are found still
stating the retired model.

## Responses used

Of the eight available responses, this review used five. Naming them mattered,
because the default pull was to repair everything.

| Response | Used for |
| --- | --- |
| Repair the artifact | most findings |
| Narrow the claim to what its check reaches | AC-0004 (optionality correctness is a review call), AC-0012 (declared rules, not visual distinction), AC-0017 (a pinned axis, not semantic non-overlap), and the Objective's exclusion promise |
| Cut the item | the guaranteed-outcome promise, which no criterion authorised |
| Repair the generator, not the instance | the seam model was fixed once in the Objective, and the criteria re-derived from it, rather than patched one at a time |
| Route to an owner that already covers it | the marketing-home entry, the Claude Desktop route, the pack-source parity gate, the guide-affordance sweep, and `packs/experience-design/DESIGN.md`'s stale skill name |

One **dismissal was made and then withdrawn**: AC-0001's non-count-preserving
red input was defended on the grounds that its observer parses per step. Round 2
showed the argument rested on a stub that returned only cleanly parsed blocks,
which makes a deleted field invisible. The stub was repaired and the dismissal
retracted. A dismissal defended by prose rather than by the artifact is the
shape to distrust.

## Instrument corrections

The mechanical set-level sweep is a control, so it was itself proved. Two of its
checks were found unable to fail and were corrected, each then killed by a
mutation:

- the coverage-back check tested only that a criterion id appeared with an
  arrow, so drift in the arrow's *target* passed. It now validates the target
  against the declared outcome and boundary ids. Proved by two mutations —
  dropping a criterion from the trace, and pointing one at an undeclared
  outcome.
- the one-group-per-criterion check counted raw string occurrences, so a prose
  mention inside a group read as a second group. It now parses the parenthesised
  id list of each group's leading bold segment. Proved by two mutations — a
  criterion in two groups, and a criterion in none.

A third finding was raised against the sweep and rejected on inspection: the
sweep reported AC-0017 in two Testing Strategy groups, which was the checker's
defect and not the spec's. The spec was left alone and the instrument fixed.

## Not checked at this gate

- **No security review.** The change is documentation, page copy and tests; it
  crosses no trust boundary, changes no authority, and handles no untrusted
  input. Recorded rather than silently skipped.
- **No frontend pre-flight.** Named skip: the primary output is Markdown and
  copy, not HTML, CSS or JS craft. The two `index.astro` edits are text inside
  existing markup.
- **No rendered-output experience review.** It cannot run before EXECUTE,
  because nothing is built. It is owed after T2 and T4 and is the pass S6
  lacked; the design gate above reviewed intent, not rendering.
