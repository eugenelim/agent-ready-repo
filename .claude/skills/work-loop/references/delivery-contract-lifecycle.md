# Delivery-contract lifecycle

This reference owns the work-loop details for controlled contract amendments and
the bounded evidence handoff to `close-work`. The main skill owns when these gates
fire; this page owns their complete payload and recovery rules.

## Rejected planning gates

If the spec is rejected, fire `spec-rejected` from `SPEC-HUMAN-GATE` to return to
`SPEC-PLAN-DRAFTING`. Revise the pair, set the spec and plan to `Draft` and
`Drafting`, then fire `spec-ready`:

```text
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> spec-rejected
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> spec-ready
```

If the plan is rejected, fire `plan-rejected` from `PLAN-HUMAN-GATE` and apply the
same status reset, revision, and `spec-ready` sequence:

```text
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> plan-rejected
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> spec-ready
```

## Controlled full-mode contract amendment

When implementation proves an accepted item is genuinely separable, do not leave
an open acceptance criterion or narrow the outcome because the session, retry
budget, or review round ended. First obtain explicit scope-owner authority and
materialize the separated follow-on through `work-intake`, or obtain its stable
external evidence reference.

From code mode `CODE-IMPLEMENTATION`, before editing the spec or plan, run:

```text
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> contract-amendment \
    --owner-authority-ref <stable-owner-approval-ref> \
    --reason-ref <stable-follow-on-artifact-or-external-ref> \
    --completed-evidence-ref T1=<stable-gate-or-review-ref> \
    --completed-evidence-ref T2=<stable-gate-or-review-ref>
```

The event pins the prior approved spec/plan and every completed task section,
preserves completed evidence bound to task IDs, review counters, and run identity,
clears only the remaining approval/schedule baseline, and returns to
`SPEC-PLAN-DRAFTING`. Repeat `--completed-evidence-ref Tn=<stable-ref>` so every
completed task has at least one evidence binding; no evidence flags are needed when
no tasks have completed. Evidence from earlier amendments remains bound unless the
current transition adds another reference for that task.

An interrupted call is recovered by reissuing the exact same command. Changed
authority, reason, or evidence facts refuse instead of creating another amendment.

Then set the spec/plan to `Draft`/`Drafting`, amend the bounded outcome, final AC
set, `Follow-ons`, and unfinished tasks, and follow the ordinary `spec-ready`,
pre-EXECUTE reviews, human spec/plan gates, `approve-plan`, `schedule`, and
`plan-locked` sequence. Completed task sections cannot be edited, removed, or
renamed; a correction is a new dependency-ordered unfinished task. Rescheduling
emits only unfinished tasks and treats preserved completed dependencies as met.

The event is unavailable in spec-plan mode and outside `CODE-IMPLEMENTATION`.
Required accepted work remains `Implementing`; session end, retry cap, stasis, or
model judgment never invokes this transition or creates a follow-on.

## Completion evidence handoff

Before declaring an implementation review unit complete, prepare a bounded handoff
for `close-work` containing:

- delivery ID or session identity;
- accepted outcome and authority source;
- implemented scope and verification evidence;
- each durable output's status and stable evidence references;
- non-goals and independently scoped follow-ons;
- unresolved obligations and dependencies;
- the completion-event candidate; and
- independent source, write, and deletion authority facts.

Tests and implementation evidence are capability proof. They do not own product
intent, decision rationale, ownership, operational promises, or authority.

The handoff is evidence, not closeout. `work-loop` does not declare
Closeout-pending or Post-closeout, select a disposition, compact coordination, or
authorize deletion. `close-work` alone inventories lasting facts, owns those
lifecycle projections and policy decisions, and performs any separately confirmed
effect.

Direct-light completion uses the same evidence shape from its active-session
decision record, temporary plan, gates, and bounded review result. A session-local
plan is not a closeout record and is not resumable after context loss. If the plan is local-only or PR-only, the
handoff must name a stable evidence owner outside the temporary record before that
record can be disposed.

For full-mode work approved as local-only, PR-only, or repository-durable, carry
forward the approved retention class, exact locator and fingerprint, required
readers, stable post-closeout evidence owner, and intended retention or
immediate-disposition boundary. Completion may report drift in those facts; it cannot
silently change the approved retention decision.

Spec-plan mode ends after approved planning and has no implementation-completion
handoff. A later code-mode run produces it after implementation and verification;
the planning run never invents delivery evidence for work it did not perform.

## Implementation-loop termination

Stop the current iteration when any of these is true:

1. Gates are green and the mode's review requirements are satisfied for the
   current review unit. Proceed to the finish checklist. A clean or merged unit
   does not complete accepted intent while matching work remains.
2. `loop-cohort.py check` exits non-zero, other than the expected pending plan
   review that triggers pre-EXECUTE reviewers. Implementation/review retry caps
   identify their condition. A repeated finding fingerprint from `review inspect`
   is stasis and stops immediately for human replanning; it is not another review
   round.
3. The diff is shrinking but findings are not. Stop spot-fixing and return to the
   plan/root cause.

If the work is incomplete, record what was learned and re-plan. Retry caps, review
stasis, and a clean intermediate unit never complete intent or create follow-ons.
