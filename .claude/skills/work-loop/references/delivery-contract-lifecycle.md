# Delivery-contract lifecycle

This reference owns the work-loop details for controlled contract amendments and
the bounded evidence handoff to `close-work`. The main skill owns when these gates
fire; this page owns their complete payload and recovery rules.

## What a delivery contract binds, and for how long

A spec and plan bind this delivery, not the repository forever: living while the
plan is drafting, pinned from plan approval, frozen once the spec is `Shipped`,
when the code becomes the truth. A frozen spec no longer constrains how the system
behaves: later work that contradicts one is recorded in the code, and in a
decision record when it reverses a decision, never by rewriting the shipped
spec — though its status line still takes the two pointers that contract
licenses, and the deferral anchors its body names still have to resolve.
Full contract: the `new-spec` skill's `references/spec-and-plan-contract.md` —
`**Lifecycle:**` and § *A spec directory freezes as a unit, when the spec ships*
for the three stages, § *Superseding a frozen document* for the status line's
two pointers, and § *Spec metadata contract* → **Historical deferral token** for
the anchors a frozen body still owes.

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

## Verification ledger

Execution observations belong in a verification ledger, normally
`docs/specs/<feature>/notes/verification-ledger.md` or the adopter's equivalent
spec-directory layout. Create it only when execution produces an observation;
it holds observed mutation reds, stub verdicts, assertion text, digest
comparisons, manual-QA output, and any deviation from a task row's literal
method.

The approved `spec.md` and `plan.md` retain obligations only: acceptance
criteria and task rows. The ledger is not hash-pinned, so recording an
observation there needs no amendment to either approved artifact. A genuine
specification or plan error is different and still follows the controlled
amendment procedure above.

A declared discovery is an observation, not an error. When a plan recorded a
seam as `no stub (implementation-discovered)`, grounding that arrives during
implementation goes in the verification ledger. The plan predicted the
discovery, so recording it amends neither approved artifact.

A falsified settled decision is an error. When approval settled a design
decision and execution falsifies it, the plan is wrong and takes the controlled
amendment procedure above. The verification ledger is not a route for a
settled decision that execution falsified.

## When the design shape is wrong

The paragraph above covers one approved decision that the build disproves.
That is a plan error on its own, and one is enough. A `design-misfit`
deviation whose assumption is a settled decision in the approved
`## Design (LLD)` is that case: take the steps below at once, without waiting
for a second sign. A verification-ledger entry may record it, but never
resolves it; only the amendment does.

This section also covers the harder case. Each deviation looks local, yet a
run of them shares a cause, which means the design itself has the wrong
shape. Fixing each instance on its own hides that.

Look for these signs after each task's gates pass, and again before review:

- The same workaround appears in tasks that have nothing else in common.
- Unrelated cases each need their own special-case branch.
- Code compiles only through escape hatches: casts, untyped values, or
  optional fields that are always set in practice.
- A lock, retry, or sync step appears around state the design called private
  or single-owner.
- A caller works only if it knows rules the interface was meant to hide.
- Two or more `design-misfit` deviations name the same cause.

An implementer report of `blocked` that carries a `design-misfit` counts as a
sign as soon as it arrives, even though its task never merged. Do not answer
it by revising only that task.

One sign in one place is not enough. Some problems are messy by nature: a
branch that mirrors a real case in the domain is not a design fault. Act when
a sign repeats across unrelated tasks, or when different signs trace back to
one design decision.

When the pattern holds:

1. Stop starting new tasks. More code on the same shape only adds to what has
   to be undone.
2. Surface the evidence: each sign, where it appeared, and the design decision
   they share. When the plan has a `## Design (LLD)`, name the sub-section and
   the assumption it rested on. Wait for the owner.
3. If the owner agrees the shape is wrong, take the controlled amendment
   above. Redesign from what was actually built, as if the constraints the
   build revealed had been known from the start. Do not patch only the line
   the build disproved.
4. Make the new design smaller than the old one before it grows. Removing or
   merging the parts that existed only to work around the old shape comes
   first, as new unfinished tasks; the amendment rule above keeps completed
   task sections sealed.

Light mode has no amendment event, whether its plan is a spec on disk or,
for direct-light, held only in the session. Its one task is the whole change,
so watch for signs inside it: the same workaround across its files, escape
hatches, or an unplanned lock. When they appear, or when the build disproves
a settled decision in an on-disk plan, Surface the evidence and wait instead
of taking steps 3 and 4. If the redesign fires a risk trigger, the work moves
to full mode by the usual rule.

The owner may decide the shape stands. Record that decision and the signs it
covered in the resolve-vs-surface disposition record, so a later round does
not raise them again.

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
decision record, temporary plan, gates, and review result. A session-local
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

1. What the accepted intent requires is done, verification passes, no
   unresolved Blocker or Concern remains, the diff is coherent, and review is
   clean. Proceed to the finish checklist. **Do not continue searching for
   additional improvements.** A clean or merged unit does not complete the
   accepted intent while work that intent requires remains.
2. `loop-cohort.py check` exits non-zero, other than the expected pending plan
   review that triggers pre-EXECUTE reviewers. Implementation/review retry caps
   identify their condition. A repeated finding fingerprint from `review inspect`
   is Surfaced, not a stop; it bounds nothing.
3. The diff is shrinking but findings are not. Stop spot-fixing and return to the
   plan/root cause.

Condition 1 is a stop, not a checkpoint to look past. Meeting it ends the
iteration even when you can see something else worth doing; that something
else is a scope change for the owner, not a reason to keep going. Three
things reopen the work and nothing else does: a finding showing this change
is incorrect or unsafe; any obligation the accepted intent requires — the
trusted request, a contract obligation, a stated acceptance criterion — found
incomplete; and a mandatory finish-checklist duty not yet satisfied. Use the
same definition of required that DECIDE uses. An improvement no obligation
names is not one of them.

If the work is incomplete, record what was learned and re-plan. Retry caps, review
stasis, and a clean intermediate unit never complete intent or create follow-ons.
