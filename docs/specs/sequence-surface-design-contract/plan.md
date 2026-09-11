# Plan: the sequence surfaces carry their design contract

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

**The implementation already exists.** This slice was created to govern
behaviour that shipped under S6 without a criterion, after an independent review
found that reopening two frozen specs was the wrong way to record it. The tasks
below are what was actually done; the tests were written or strengthened as part
of closing the review's findings.

## Tasks

| # | Task | Criteria | Notes |
| --- | --- | --- | --- |
| T1 | Give each group its own card modifier with a distinct at-rest rule | AC-0001 | Accent bar plus numeral for the sequence, muted bar for the loops, hairline for optional additions |
| T2 | Route the sequence group onward to the guides path | AC-0002 | `withBase('/docs/guides/#…')`, the repo's cross-site convention |
| T3 | Place the alternative beside the step it replaces, on a non-overlapping selection axis | AC-0003, AC-0004 | `P2b`, directly after `P2`, with `P2` pointing to it |
| T4 | Teach the walkthrough cases what a stage is | AC-0005 | `STAGE_LABEL = /^p\d+\s*·/i` in `rendered-output.test.ts`. The **test** changes; the frozen spec's body does not |
| T5 | Restore both frozen spec bodies | — | `four-discipline-sequence` back to Shipped with 22 criteria, `install-to-ship-walkthrough` unamended |

### T1 — Tests

1. `each group carries its own signature, and the three differ` — for each of
   the three groups, assert every card carries that group's modifier and none of
   the other two, **scoped to the group**; then extract each modifier's at-rest
   rule from the inlined style and assert the three are distinct. (AC-0001)

### T2 — Tests

2. `routes onward from the sequence to the guides path that walks it` — assert
   the anchor's `href` equals the path's exact target. (AC-0002)

## Mutation proofs

Every guard here failed at least one mutation before it passed. That is recorded
because two of the three assertions were written, believed correct, and then
shown by mutation to be unable to fail.

| Guard | Mutation | Observed |
| --- | --- | --- |
| AC-0001 — at-rest signal | keep the `--loop` class, delete its **base** rule, leaving only `:hover` | **First version passed** — it matched any rule containing the modifier, so a card identical at rest satisfied it. Tightened to require a selector with no pseudo-class; now fails |
| AC-0001 — scoped to the group | swap the `--loop` and `--optional` modifiers between their groups | **First version passed** — it only checked that every card carried exactly one modifier from the set, which a swap preserves. Scoped each modifier to its own group; now fails |
| AC-0001 — signatures differ | replace all three at-rest rules with `position: relative` | fails on the distinctness assertion; before it existed, three identical treatments passed |
| AC-0002 — exact target | — | the first version asserted `toContain('/docs/guides/')` and `toContain('#p2b')`, which a different path sharing those fragments satisfies. Replaced with an equality assertion |
| AC-0005 — the stage contract | add `### P6 · Mutation probe` inside the walkthrough section | `install-to-ship-walkthrough` AC2 and AC6 both fail, with the alternative still present |

All restored by editing.

## Sequencing

T5 first — the frozen bodies must be restored before anything claims to govern
their behaviour. T1–T4 are already implemented.
