# Second contract amendment record — 2026-10-01, post-gates

This note is the durable authority and reason reference for the **second**
`contract-amendment` transition on run `1adcfbc1-0d36-401b-9f3d-ebfc2493790a`.
It is separate from
[`amendment-2026-10-01.md`](amendment-2026-10-01.md), which records the first
amendment and four scoped owner rulings and stays in force unchanged. A second
record exists rather than an appended section so each amendment's authority and
reason references resolve to exactly one place.

It exists for the same structural reason the first one does: the session-local
review artifacts under `.context/reviews/` are gitignored and cannot serve as a
stable reference.

## Owner authority

The scope owner authorized this amendment on 2026-10-01, in session, after being
shown three things: the two sustained findings below, the measured fact that
both repairs move the pinned canonical spec hash, and the three options
available — one amendment cutting both claims; one amendment restating the
AC-0011 justification instead of cutting it; or amending AC-0011 alone and
deferring the AC-0004 nit with its citation. The owner selected the first.

The owner was also told, before work began, that the reschedule re-emits
unfinished tasks and their receipts and wave transitions must be recorded again,
and that the cost is bookkeeping because the code is already written, gated and
green. Measured during the transition rather than assumed: the amendment treats
T4 as completed and requires an evidence binding for it, so only T5 is
re-emitted.

## Reason: two sustained findings in the post-gates review

The post-gates review ran `adversarial-reviewer` and `experience-reviewer`, both
warranted. The experience review sustained nothing of twelve findings. The
adversarial review sustained two of three.

### Sustained concern: AC-0011's cannot-fail justification names the wrong guarantee

AC-0011's rationale asserted that the superseded co-occurrence assertion could
not fail because "the comment already carries `unconfirmed` in AC-0001's
closed-set enumeration". That entailment is false on the bytes, and the defect
is in the justification only — the decision to replace the assertion and the
replacement itself are both sound, verified independently twice.

- AC-0001 pins the enumeration in the template's **frontmatter**.
- The assertion's `comment` is scoped to the `## Approved visual target` section
  comment, via `section.split("-->", 1)[0]`. That span excludes the frontmatter.
- What actually carries `unconfirmed` inside the comment is the comment's own
  enumeration, and **no criterion pins it**: AC-0003 requires only the literal
  `visual_target`, the three line labels, and `bind nothing on their own`.

The sentence was carried in four places, one of them a shipped assertion
message a future author would read as a general rule about comment-scoped
checks. The fourth — the AC-0011 mutation proof's Contrast bullet in
`verification-ledger.md` — was missed by the sweep this amendment performed and
was found by the next pre-EXECUTE pass; it is struck in the follow-up revision
recorded in the plan's Changelog. The count is corrected here rather than left
at three, because a governance record that understates its own sweep invites the
next author to trust an enumeration that is short.

### Sustained nit: AC-0004's uniqueness clause is not what its assertion decides

AC-0004 required the anchor to occur "exactly once in the file", while the
shipped assertion decides `len(blocks) == 1` over blank-line-delimited blocks.
Two occurrences inside one block pass, so the criterion's words forbid a state
its own verification cannot detect.

## What this amendment does

It cuts, rather than explains. That choice is deliberate and is grounded in this
run's own measured history: across the rounds run under the first amendment the
sustained count fell 6, 9, 10, 3, 2, 1, 0, and every sustained finding in rounds
2 through 6 was a defect in the previous round's repair rather than in the work
being governed. The trend turned only when repairs stopped adding obligations
and started dropping or narrowing claims.

1. **AC-0011's false entailment is deleted, not restated.** The rationale keeps
   the part that is true and decidable — that the co-occurrence form reduces the
   criterion to whether `absent` appears anywhere, and that a comment reading
   "an absent target means `none`" would pass while contradicting the
   fail-closed default — and drops the misattribution to AC-0001. The same cut
   is applied to the other carriers: the plan's T5 stub block and the shipped
   assertion message, which stay byte-identical to each other, and — in the
   follow-up revision, after this amendment's sweep missed it — the AC-0011
   mutation proof's Contrast bullet in `verification-ledger.md`.
2. **AC-0004's claim is narrowed to what its assertion decides**: the anchor
   occurs in exactly one paragraph block of the named file. Narrowing rather
   than strengthening the assertion, for two reasons. The weaker property still
   meets the criterion's own stated purpose, that the verification cannot
   silently grade a different occurrence. And the assertion was shipped under
   T2, whose plan section is pinned, so changing it would be a new
   dependency-ordered task rather than an edit.

## What this amendment does not change

- No acceptance criterion is removed or renumbered, and no outcome is narrowed
  beyond AC-0004's uniqueness scope stated above.
- The four scoped rulings in the first amendment record stay in force, including
  the intended-red waiver and its extension to the Lifecycle red.
- T1, T2 and T3's plan sections stay pinned and unedited.
- The refuted findings are not acted on. The guide-caption advisory stays
  deferred, already recorded in two committed files
  (`amendment-2026-10-01.md` and `plan.md`'s Changelog), and the experience
  review's twelve refusals stand, three of which defer to the registered
  successor spec `visual-target-rung-precondition`.

## Authorized state repair, recorded because it broke a standing rule

The first `contract-amendment` call deadlocked the transition, and recovering it
required one hand edit to `state.json` — a file the standing instruction says
never to hand-edit. The owner authorized that edit on 2026-10-01 after being
shown the deadlock and the three available routes: clear the one field; run
`loop-cohort reset`, which unlinks `state.json` outright and would have voided
this run's identity, pins, evidence and review counters; or stop and leave the
branch unshippable with a sustained Concern that cannot be deferred.

What deadlocked, exactly. `contract-amendment` writes its `pending_transition`
marker before it validates that every completed task has an evidence binding.
The first call supplied bindings for T1 to T3 — the contents of
`completed_task_ids` — and refused with `completed task has no evidence
binding: T4`, because the amendment also treats every task in
`schedule_waves[:current_wave_index]` as completed, which with
`current_wave_index` at 1 is T4. The marker persisted with the three-task
argument set. Reissuing the identical command, which is the only recovery the
lifecycle reference documents, failed the same way; reissuing with `T4=` added
refused with `pending transition conflicts with this sequence`, because the
marker's argument identity is compared at the same `pre_transition_sequence`.
The state could not be moved to match the marker either: `wave advance` only
increments `current_wave_index`, and `wave reopen` targets the current wave.

The edit. `pending_transition` was set to `null`. Nothing else changed, and that
was proved rather than asserted: the SHA-256 of the whole state with
`pending_transition` removed is `c2f76383919b31d15691…` both before and after
the write. `run_id` stayed `1adcfbc1-0d36-401b-9f3d-ebfc2493790a`, and the T1 to
T3 section pins and evidence bindings were unchanged. The pre-edit file was kept
outside the repository for the duration of the recovery. The amendment then
fired with T4 bound to `31011ff57`.

This grant is narrow. It authorizes clearing one field on this run, on this
date, to recover this deadlock. It is not a licence to edit cohort state, and a
future deadlock needs its own ruling.

## Completed-task evidence bindings

| Task | Stable evidence reference |
| --- | --- |
| T1 | `f69606cfb` |
| T2 | `2e0348b39` |
| T3 | `15188c387` |
| T4 | `31011ff57` |

T4 is bound to its repair commit rather than to its original release commit
`774f9e5ae`, because `774f9e5ae` is the state in which T4 was committed but
**not met**: the first amendment rewrote its `Done when` so it could not pass
while two shipped artifacts stood non-conforming. `31011ff57` is the commit in
which all five conditions hold.

T5 carries no binding here. Its wave was reopened for this repair round, so the
amendment does not treat it as completed, and the reschedule will emit it.
