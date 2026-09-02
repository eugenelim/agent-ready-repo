# Brief: One authoritative next action per work-loop turn

- **Slug:** `work-loop-next-action`
- **Received:** 2026-09-01
- **Owner:** Repository maintainers (`ini-002`)
- **Status:** Draft

## Outcome

An agent advancing or resuming a full-mode work-loop currently reconstructs "what
do I do next" from two state dumps and a fifteen-row prose routing table, on every
turn. An adopter driving the loop by hand does the same reconstruction manually.
Both should instead ask the loop once and get one authoritative answer.

The loop can be asked, from persisted state, what to do next, and answers with
one bounded record: a single action, the arguments it needs, the events that
complete it, and whether a human gate is open. The answer is derived, not
transcribed, so it cannot drift from the state machine it describes.

**This brief covers reporting only.** A prior attempt also tried to make the same
artifact notice when a review loop was not converging, and failed partly by
assuming one thing could do both. Detecting and responding to non-convergence is
a separate, and much less settled, problem: it is shaped at
[`agent-authoring-input-quality.md`](../intents/agent-authoring-input-quality.md) and [`agent-loop-escalation-recovery.md`](../intents/agent-loop-escalation-recovery.md),
where the response is still competing hypotheses rather than a decision. Nothing
in this brief waits on it.

## Success metrics

- An agent resuming a loop issues one command and acts, rather than reading two
  state files and a prose table.
- The reported action matches what the shipped resumption guidance prescribes,
  for every state the loop can be in — checked by comparing both, not by
  asserting it.
- No component gains the ability to declare a review clean that could not
  previously do so — checked by enumerating who can emit that event before and
  after, not by asserting the absence. An absence with nothing to compare it
  against is the shape that passes while the control is missing.

## Scope / Non-goals

**In scope**

- A read-only query answering from persisted engine and cohort state.
- A published payload contract for that answer, versioned and inventoried.
- Making the shipped resumption guidance and the query agree, by construction.

**Non-goals**

- Changing the state machine, its transitions, or its guards.
- Any component reading reviewer output, inferring which reviewers ran, or
  treating report prose as state.
- Reducing the always-loaded instruction surface. That depends on this outcome
  and is separate work.
- Rewriting the review protocol's artifact conventions.
- Detecting or responding to a non-converging review loop. Separate shaping items,
  linked above. This brief must not acquire a claim about review passes the loop
  did not record — that assumption is what ended the prior attempt.

## Appetite

Two prior attempts at the reporting half exist; the second consumed ten
pre-EXECUTE review rounds without converging and was abandoned at
`e1bdde746`. Appetite should be set with that in mind rather than from the
apparent simplicity of "emit a JSON record".

The hard part is already solved: the state-to-action mapping survived
independent re-derivation and is preserved (see Provenance). What consumed ten
rounds was not the mapping but everything authored around it.

## Constraints carried from the prior attempts

Two technical rulings survive from the abandoned work. They are constraints on
how this outcome may be built, not part of the outcome, and they are here
because re-deriving them would cost rounds.

### The read-surface claim is scoped to application-directed I/O

The process-wide claim is rejected. "Opens nothing else" is neither truthful nor
useful: a cold process executing the loop's guard module opens many files beyond
any set a contract would name, all of them interpreter and standard-library
loading, and the natural instrument sees none of them under a test runner. No
count is stated here, including a comparative one: the figure moved between a
warm and a cold measurement of the same code, and it varies with the
interpreter.

Two invariants replace it:

> Before `<spec-dir>` confinement succeeds, the verb performs no directory
> enumeration or artifact read beneath the supplied path.

> After confinement, every application-directed operation on a path derived from
> `<spec-dir>` is a named presence probe or flows through the repository's blessed
> readers. Interpreter imports, standard-library loading, and repository-root
> discovery are outside this claim.

"Application-directed" needs a mechanical definition — call origin or target
derivation are the two candidates — rather than an informal exemption list. That
it *can* be defined mechanically is unproven, and proving it is part of the work:
if two attempts at the predicate are each defeated by a different surface, the
property is a judgment and the response is to split it, not to widen the
definition a third time. Verification must:

- bootstrap all imports **before** starting the application-I/O trace;
- trace opens, stats, enumeration, and symlink resolution **separately**;
- exercise both allowed and forbidden target-derived accesses;
- include a **positive control** proving the detector fails on a planted forbidden
  access.

No exact file count is stated. A count recreates the source-versus-bytecode and
lazy-import drift that consumed several review rounds of the abandoned attempt.

### Output availability follows a trustworthy-record threshold

> Owner decision: output availability follows the trustworthy-record threshold.
> Failures before confined authoritative engine identity is established return
> non-zero with no stdout. Failures in supporting artifacts after that threshold
> return a zero-exit halt record when its fields can be constructed without
> trusting the failed artifact.

Applied:

| Situation | Outcome |
| --- | --- |
| No engine state, plus a symlinked, FIFO, or oversized `spec.md` | Hard refusal — non-zero, nothing on stdout |
| Valid engine state, plus a hostile status file needed for the next decision | Zero-exit halt record |
| Unreadable cohort state after valid engine identity | Zero-exit halt record, matching existing behaviour for the right reason |

A hostile value is **never** copied into the record. It reaches stderr only, as a
bounded and escaped diagnostic.

The ruling comes from the trust threshold, not from mechanically mirroring
whatever the current reader happens to do. A trace still documents current reader
behaviour so the eventual spec knows what it is changing.

## Risks

- **A criterion over an unverified claim about the world.** This is what ended the
  prior attempt: it asserted what the system observes and never checked. Any
  criterion resting on a claim about live behaviour needs its oracle named before
  the criterion is written, not after a reviewer asks.
- **An invariant no instrument can hold.** A claim stated over "all files" is
  false of any Python process, and the obvious instrument is blind in the
  environment the tests run in. The Constraints above bound the two known cases;
  the habit generalises.
- **Reporting quietly re-acquiring the stopping problem.** They have different
  authority and different state needs, and merging them costs the read-only
  property that is this outcome's most valuable guarantee. The non-goal above is
  the guard.

## Rabbit holes

- **Do not let the reporting component observe unrecorded work.** The abandoned
  attempt asserted that its review-budget discriminator could see authoring spin
  and offered a replan route as the rescue. Neither was reachable: the protocol
  does not record ordinary pre-EXECUTE results, so after ten rounds the counters
  still read zero. Ten rounds of clause repair never reached it, because it was a
  model error, not a wording error.
- **Do not verify a contract by parsing its own prose.** The abandoned attempt
  carried a large pre-approval test, much of which read the draft's own prose.
  It proved the draft agreed with itself and did not detect the model error in ten
  rounds. Tests that compare a document against *shipped code* are worth building
  early; tests that compare a document against itself are not.
- **Watch the fourth content home.** The same attempt accumulated a quarter of
  its spec as explanatory prose inside the normative section — bound by no criterion, cited by
  no task, checked by nothing — and it regenerated consistency defects on every
  edit. Mechanism belongs with the implementation; the evidence that a mechanism is
  right belongs in assumptions, cited once.
- **Repair churn is itself a defect source.** Across the abandoned attempt's last
  four rounds, most blockers found in each round were introduced by the previous
  round's repair. A large repair on a long contract is not free.

## What didn't work

Approach-level negative results, so they are not retried. Stated directionally on
purpose: the per-round measurements behind them live in the non-convergence
shaping item, which is where they are the subject rather than supporting detail.

| Approach | What it fixed | What it did not fix |
| --- | --- | --- |
| Prose criteria for a total state-to-action function | Nothing. Reviewers attacked the prose, each repair produced fresh prose findings, and the criteria became a test plan | — |
| Restating the mapping as normative tables, criteria asserting properties of them | The prose-criteria class, permanently. The tables then survived independent re-derivation | Convergence. Drift moved to mismatch between a criterion and the task implementing it |
| Splitting content into outcome, mechanism, and grounding homes | The cross-document drift class, measurably | Convergence, and it introduced criteria citing grounding that was absent or wrong |
| Mechanising the document's internal edges — identifier and citation parity, binding claims to live symbols | Real defects, each on its first run | Anything about the model. All of it binds the document to itself |
| Tests that parse the draft | Self-consistency | The model. The pre-approval suite never detected the false premise |

**The pattern underneath all five.** Each round's repair was itself a defect
source: by the end, most blockers found were introduced by the previous round's
fix. Every attempt at precision added claims, and claims are what the next round
falsifies. A contract that demands exhaustive precision about its own prose grows
its attack surface faster than it closes it.

That is the argument for slicing this brief small, and for the authoring
constraints below.

## How to author from this brief

Not process boilerplate — these are the three habits that produced the failure.

- **Criteria state outcomes, never mechanism.** If a criterion names a helper, a
  call sequence, a file count, or an instrument, it belongs in the plan. A
  criterion that a reviewer can only check by reading the implementation is not a
  criterion.
- **Plan tasks name what to verify, not how.** "Verify the read discipline holds
  against a planted access, with a control proving the detector can fail" is a
  task. A bullet that spells out the assertion, the fixture, and the expected
  message is pseudo-code, and it will be reviewed as code while being unable to
  run. The abandoned plan was largely the latter.
- **Prefer a claim you will not have to defend.** Where a number does not change
  a decision, do not state it. Where it does, name its oracle and expect to
  re-measure it. Two figures in this brief's own first draft moved within a day.

A rubric of the specific shapes that have produced findings in this repository —
criteria that cannot fail, that are unsatisfiable, that decay, that are too big,
and that are not mechanizable at all — is in the authoring-quality shaping item
linked above, together with what to write instead of each. Read it before
authoring criteria, not after a reviewer cites one.

**These three habits are themselves rules, and rules here have a track record of
not activating.** The cognitive-load simplification and the cut-before-adding
razor were both in the authoring agent's context throughout the abandoned
attempt, and several gates enforce them — over the packs, the root guidance, the
seeds, and the changelog. The progressive-disclosure lint explicitly excludes an
authored `docs/specs/<feature>/spec.md`. So the guidance was loaded at every turn
and enforced nowhere near the point where it would have bound.

Whoever authors from this brief should assume the same of the three habits above:
state them, and then find the point in the loop where something actually changes
if they are ignored. If this work adds any guidance of its own, it ships with an
activation point and a way to tell activation from presence, or it does not ship.
The general problem is shaped in the authoring-quality item linked above.

## Decision authority

- Repository maintainers own the shape decision between "reporting stays a pure
  projection" and "one component owns both halves". A prior owner decision
  favoured the former; it was taken against an abandoned draft and should be
  re-confirmed at the Ready review rather than inherited.
- Anything about detecting or responding to non-convergence is decided in the
  shaping items, not here. If a Ready review finds itself ruling on that, the
  split has leaked and the ruling belongs on the other side of it.

## Ready gaps

Recorded rather than invented. A Ready review must resolve these.

**Settled, and why they are no longer gaps:**

- The read-surface claim and the hostile-artifact behaviour are ruled on, in
  Constraints above. Both were open questions at Draft creation; both are now
  constraints on the build rather than things to decide.
- Non-convergence left this brief entirely. It is a shaping item with an
  undefined outcome, not a gap in this one.

**Remaining:**

- **No appetite is set.**
- **No slices are proposed.** `continue` selects them. The natural cut is the
  projection itself, the published payload contract, and the shipped-surface
  parity — the last of which touches a skill tree a peer session may be editing.
- **Two bounded observations are owed** before the slices that depend on them:
  an application-directed I/O trace with a positive control, and a trace of the
  current reader's behaviour on hostile status files so the eventual spec records
  what the ruling changes. Neither is an unknown any more; both are documentation
  the constraints above already decided the shape of.

## Spec map

None. No slices are confirmed and no spec is derived from this brief yet.

## Provenance

- Source: repository origin. This brief is authored from a failed delivery
  attempt in this repository, not from external input.
- The four normative tables — domain, discriminators, ordered preconditions,
  routing, and action attributes — survived independent re-derivation by more than
  one reviewer and are the reusable asset from the abandoned attempt. They are
  preserved at commit `e1bdde746`, together with the record shape, the read-only
  guarantee, and the fail-closed catch-alls. Read them there rather than trusting
  this summary of them.
- The abandoned spec, plan, review history, and pre-approval test were removed
  from the working tree in the same change that created this brief; they remain
  in history at that commit.