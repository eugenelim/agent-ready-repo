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
surface a live-intent rule belongs on.** Read on `ab4dd5a30`, over every
occurrence in `intent_shape.py` of the rule or its vocabulary:

- **Lines 14–22, module docstring** — the statement itself. Canonical.
- **Lines 447, 503, 545, 562** — `validate_supersession`,
  `_check_state_coherence`, `validate_corpus_scoped` and
  `_check_supersession_pair` each read "See the module docstring's surface
  placement rule." Pointers, not restatements.
- **Line 499** — `_check_state_coherence` says its verdicts depend on
  `Status`, a different field from the one constrained, "the same reason
  ``validate_supersession`` stays off the shared surface." Judged an
  *application* of the rule to this function's own case, not a second
  statement of it: it states where these rules sit and why, and states no
  general dichotomy. It is followed immediately by the pointer at line 503.

Judged by eugenelim. The earlier draft that made this an acceptance criterion
(`AC-0015`) was withdrawn during spec review as unfalsifiable, which is why
the obligation is carried here instead.
