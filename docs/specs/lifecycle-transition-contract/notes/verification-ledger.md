# Verification ledger — lifecycle-transition-contract

Execution observations. The approved `spec.md` and `plan.md` carry obligations;
this file carries what running them produced. Not hash-pinned, so recording an
observation here amends neither approved artifact.

## T3 — delivered, and accepted as not machine-recorded (2026-09-24)

**Delivered** in commit `d00f39e34`. The pre-rule derivation reported both sets
the spec's § What Changes names: **14 artifacts refused and 10 never `Accepted`**
before the migration, **0 and 0** after. `notes/migration-record.md` carries one
entry per artifact in the second set, naming the branch taken and the owner
waiver it rests on.

**Accepted risk — read this before scheduling a wave.** The cohort's
`completed_task_ids` is empty, because this run's engine was initialised fresh
and the `contract-amendment` transition that populates that field is reachable
only from `CODE-IMPLEMENTATION`. No `loop-cohort` verb writes it, and the skill
forbids hand-editing `state.json`. **So a resumed run will schedule T3 again.**
The owner accepted this on 2026-09-24 in preference to a hand edit or a
re-entered no-op wave.

If a wave emits T3: **do not re-execute it.** Its pre-rule derivation now passes
vacuously on the corpus it produced, so the task has no check that can fail.
Verify instead by reading `notes/migration-record.md` and commit `d00f39e34`,
then record a dispatch-receipt.

## Current-architecture closeout judgement (2026-09-24) — PASS

`## Durable Outputs` routes half of this closeout to a human, because no
control catches a reworded restatement of the placement rule: a content pin
would catch a copied one and pass a pointer, but not a paraphrase. The other
half, that the docstring names every refusal class this spec adds, is AC-0013
and a test decides it.

**Verdict: the module docstring is the module's only statement of which
surface a live-intent rule belongs on.** Re-read after the review round, over
every occurrence in `intent_shape.py` of the rule or its vocabulary. The
enumeration below is the whole list, not a sample — an earlier draft of this
entry claimed a complete read and then listed six of the eight occurrences,
which review caught.

- **Lines 14–20, module docstring** — the statement itself, and the only
  place the general dichotomy is stated. Canonical. (Counted twice: an earlier
  draft cited 15–22, which starts mid-sentence and runs into the next
  paragraph, and a reviewer's correction to 14–19 stopped one line short of
  `location in the same artifact.`)
- **Lines 446–447, 503, 551, 568** — `validate_supersession`,
  `_check_state_coherence`, `validate_corpus_scoped` and
  `_check_supersession_pair` each read "See the module docstring's surface
  placement rule." Pointers, one per line number. Every application
  below is followed by one of these.
- **Lines 445, 497, 499, 567** — four *application* sentences, each saying
  where one function's own rules sit and why. `validate_supersession`: "the
  pairing rule depends on a different field's value". `_check_state_coherence`:
  its verdicts depend on `Status`, "the same reason `validate_supersession`
  stays off the shared surface". `_check_supersession_pair`: "its verdict
  depends on a different field's value". Each applies the dichotomy to one
  case and states no general rule, and each is followed by a pointer at the
  canonical statement.

The line between an application and a second statement is whether it would
tell a reader where a *new* rule belongs. None of the four would; all four
say only where the rule in front of them sits. On that reading the verdict is
clean. An independent reviewer reached the same reading on the same lines.

**Where the class-pairing swap stops.** Three levels were closed during
review: exchanging the classes at the use sites, exchanging the two literal
values at their definitions, and exchanging the two descriptions in this
docstring. All three now red on `test_each_refusal_carries_the_class_that_
matches_its_kind`. Recorded so a later reviewer does not re-find the third as
open.

Judged by eugenelim. The earlier draft that made this an acceptance criterion
(`AC-0015`) was withdrawn during spec review as unfalsifiable — no control can
tell a pointer from a paraphrase — which is why the obligation is carried here
as a recorded human judgement instead.
