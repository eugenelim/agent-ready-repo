# Delivery-contract lifecycle

This reference owns the work-loop details for controlled contract amendments and
the bounded evidence handoff to `close-work`. The main skill owns when these gates
fire; this page owns their complete payload and recovery rules.

## What a delivery contract binds, and for how long

A spec and plan bind this delivery, not the repository forever: living while the
plan is drafting, partly protected from plan approval (the spec's protected sections
and its terminal intent), frozen once the spec is `Shipped`,
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

A spec or plan rejected at a human gate has no run to reset: `start` has not run,
and the supervisor holds no pre-approval state. Revise the pair, set the spec and
plan back to `Draft` and `Drafting`, run the pre-EXECUTE reviewers again, and
take both approvals again before `start`. A run that was already admitted is not
rejected; it is amended, below.

## Controlled full-mode contract amendment

Which plan changes need an amendment depends on what the approval covers. The
approval covers the protected spec sections — contract, scope and non-goals,
durable outputs, agent rules, testing strategy, acceptance criteria, accepted
risk — and the terminal intent. A change to any of them needs an amendment. A
change to tasks, tests, stubs, design, or approach does not: it is a
working-plan edit, made by the controller only while no attempt is open
([`supervisor.md`](supervisor.md#the-open-attempt-rule--when-the-plan-may-change)).

When implementation proves an accepted item is genuinely separable, do not leave
an open acceptance criterion or narrow the outcome because the session, retry
budget, or review round ended. First obtain explicit scope-owner authority and
materialize the separated follow-on through `work-intake`, or obtain its stable
external evidence reference.

Then amend the protected sections: set the spec and
plan back to `Draft` and `Drafting`, amend the bounded outcome, final AC set,
`Follow-ons`, and any unfinished tasks, and follow the ordinary pre-EXECUTE
reviews and both human approvals. Write `Implementing` and `Executing` again and
run `python '<skill-dir>/scripts/work-supervisor.py' start <spec-dir> ...` with
the approvers' authority references: it appends a new approval pair under the
same run. Until it does, `next` refuses a protected edit with its owner named
(`criteria-changed`, `scope-changed`, `terminal-intent-changed`, and the like).

Completed tasks stay complete: the supervisor derives completion from the commits
and receipts for each task's current revision, so a correction that touches a
finished task is a new revision, which is a new unfinished task to run. Required
accepted work remains `Implementing`; session end, retry cap, stasis, or model
judgment never invokes this transition or creates a follow-on. The retry count never
resets.

## Verification ledger

Execution observations belong in a verification ledger, normally
`docs/specs/<feature>/notes/verification-ledger.md` or the adopter's equivalent
spec-directory layout. Create it only when execution produces an observation;
it holds observed mutation reds, stub verdicts, assertion text, digest
comparisons, manual-QA output, and any deviation from a task row's literal
method.

The approved `spec.md` and `plan.md` retain obligations only: acceptance
criteria and task rows. The ledger is outside the reviewed envelope, so recording
an observation there needs no amendment and no plan edit. A genuine
specification or plan error is different: it is corrected as the sections above
say.

A declared discovery is not an execution observation: it changes the plan. When
a plan recorded a seam or a design means as `implementation-discovered`, the
grounding that arrives during implementation, and each later correction to it, is
a controller edit of the plan's `## Design (LLD)`. Make it as an in-envelope
working-plan change; the supervisor commits it as one `replan` with no approval,
and every task completed before it stays complete. A worker attempt that learns a
seam reports what it found, and the controller writes it into the design. The
ledger keeps what execution observed.

A falsified settled decision is an error. When approval settled a design
decision and execution falsifies it, the plan is wrong: Surface the evidence,
obtain the owner's agreement, and correct the plan. A correction that stays
inside tasks, tests, stubs, design, and approach is a working-plan edit; one
that reaches a protected spec section or the
terminal intent takes the amendment above.

## When the design shape is wrong

The paragraph above covers one approved decision that the build disproves.
That is a plan error on its own, and one is enough. A `design-misfit`
deviation whose assumption is a settled decision in the approved
`## Design (LLD)` is that case: take the steps below at once, without waiting
for a second sign. A verification-ledger entry may record it, but never
resolves it; only a corrected plan does.

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
3. If the owner agrees the shape is wrong, correct the plan as the section
   above says: a working-plan edit, or the controlled amendment when it
   reaches a protected section. Redesign from what was actually built, as if the constraints the
   build revealed had been known from the start. Do not patch only the line
   the build disproved.
4. Make the new design smaller than the old one before it grows. Removing or
   merging the parts that existed only to work around the old shape comes
   first, as new unfinished tasks; a finished task stays finished.

Light mode has no amendment, whether its plan is a spec on disk or,
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
2. `work-supervisor.py status --check` exits non-zero: 3 names the
   implementation retry cap, 1 a refusal. A finding the supervisor's review
   readiness keeps raising is Surfaced, not a stop; it bounds nothing.
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
