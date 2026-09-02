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

The outcome has two halves, and separating them is the point of this brief.

**Reporting.** The loop can be asked, from persisted state, what to do next, and
answers with one bounded record: a single action, the arguments it needs, the
events that complete it, and whether a human gate is open. The answer is derived,
not transcribed, so it cannot drift from the state machine it describes.

**Stopping.** The loop notices when it is not converging and says so, including
during the spec-authoring phase before any code exists. Today it does not: a
contract can spend ten review rounds in the same state with every persisted
counter reading zero, because ordinary pre-EXECUTE results are not recorded.

These are different problems with different owners, and a previous attempt failed
by assuming one artifact could serve both. That failure is the reason this brief
exists and is documented under Rabbit holes.

## Success metrics

- An agent resuming a loop issues one command and acts, rather than reading two
  state files and a prose table.
- The reported action matches what the shipped resumption guidance prescribes,
  for every state the loop can be in — checked by comparing both, not by
  asserting it.
- A non-converging authoring loop stops before a **fourth** findings-bearing
  repair cycle and asks for owner-directed replanning, and that stop survives a
  session restart. Per D1.
- No component gains the ability to declare a review clean that could not
  previously do so.

## Scope / Non-goals

**In scope**

- A read-only query answering from persisted engine and cohort state.
- A published payload contract for that answer, versioned and inventoried.
- Making the shipped resumption guidance and the query agree, by construction.
- Deciding where the authoring-loop stop lives and what state it needs.

**Non-goals**

- Changing the state machine, its transitions, or its guards.
- Any component reading reviewer output, inferring which reviewers ran, or
  treating report prose as state.
- Reducing the always-loaded instruction surface. That depends on this outcome
  and is separate work.
- Rewriting the review protocol's artifact conventions.

## Appetite

Two prior attempts at the reporting half exist; the second consumed ten
pre-EXECUTE review rounds without converging and was abandoned at
`e1bdde746`. Appetite should be set with that in mind rather than from the
apparent simplicity of "emit a JSON record".

The reporting half is well understood and its hard part is already solved (see
Provenance). The stopping half is not yet scoped and may be cheap or may require
a persisted counter and a protocol change; the Ready review should not bundle
them into one appetite.

## Owner decisions

Three load-bearing unknowns were open at Draft creation. All three are now closed
by owner decision, recorded here as the governing rulings.

### D1 — pre-EXECUTE non-convergence is enforced by a durable counter

> Owner decision: pre-EXECUTE non-convergence is enforced by a durable
> `pre_execute_repair_count` owned and updated by the review protocol. One count
> represents one aggregated findings-bearing repair cycle. At three cycles, the
> protocol stops before another reviewer dispatch and requires owner-directed
> replanning. Session restart does not reset it. `next` neither infers nor
> increments this counter.

Counting rules, as decided:

- Increment **once** after an aggregated reviewer round produces at least one
  sustained Blocker or Concern, and **before** revision begins.
- Do **not** increment per reviewer, per finding, for clean or refuted-only
  results, or for evidence-only retries.
- Stop before dispatching another review once the count reaches **3**.
- Persist across sessions.
- Reset only by starting a new run, or by an explicit owner-authorised replan
  recorded in the audit trail.

The name counts failed repair cycles, not reviewer calls. `review_retry_count` is
**not** reused: consuming the implementation-review budget during spec authoring
conflates two different loops.

Whether `next` eventually *displays* that stop is optional projection behaviour.
Enforcement does not belong there.

*Consequence for slicing:* this decision requires a new persisted field in cohort
state with a defined writer, a reset point, and an audit-trail entry — a change to
the review protocol's own state, not to the projection. It is a separate slice
from the reporting half and can be delivered first, because it fixes an
operational failure that is happening now.

### D2 — the read-surface claim is scoped to application-directed I/O

The process-wide claim is rejected. "Opens nothing else" is neither truthful nor
useful: a cold process executing the loop's guard module opens 37 files beyond any
set a contract would name, all interpreter and standard-library loading, and the
natural instrument sees none of them under a test runner.

Two invariants replace it:

> Before `<spec-dir>` confinement succeeds, the verb performs no directory
> enumeration or artifact read beneath the supplied path.

> After confinement, every application-directed operation on a path derived from
> `<spec-dir>` is a named presence probe or flows through the repository's blessed
> readers. Interpreter imports, standard-library loading, and repository-root
> discovery are outside this claim.

"Application-directed" is to be defined mechanically — by call origin or by target
derivation — not by an informal exemption list. Verification must:

- bootstrap all imports **before** starting the application-I/O trace;
- trace opens, stats, enumeration, and symlink resolution **separately**;
- exercise both allowed and forbidden target-derived accesses;
- include a **positive control** proving the detector fails on a planted forbidden
  access.

No exact file count is stated. A count recreates the source-versus-bytecode and
lazy-import drift that consumed several review rounds of the abandoned attempt.

### D3 — output availability follows a trustworthy-record threshold

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

## Assumptions and risks

**Risks**

- **Under-observed convergence.** Whatever owns stopping must count something
  that is actually recorded. U1 exists because the previous attempt did not check
  this before specifying a rescue route.
- **Unbounded invariants.** A confinement claim stated over "all files" is false
  of any Python process and its natural instrument is blind under a test runner.
  U2 exists to bound the claim before it is written.
- **Two owners, one artifact.** Reporting and stopping have different authority
  and different state needs. Merging them costs the read-only property, which is
  the reporting half's most valuable guarantee.

## Rabbit holes

- **Do not let the reporting component observe unrecorded work.** The abandoned
  attempt asserted that its review-budget discriminator could see authoring spin
  and offered a replan route as the rescue. Neither was reachable: the protocol
  does not record ordinary pre-EXECUTE results, so after ten rounds the counters
  still read zero. Ten rounds of clause repair never reached it, because it was a
  model error, not a wording error.
- **Do not verify a contract by parsing its own prose.** The abandoned attempt
  carried a 602-line pre-approval test, eleven of whose assertions read the draft.
  It proved the draft agreed with itself and did not detect the model error in ten
  rounds. Tests that compare a document against *shipped code* are worth building
  early; tests that compare a document against itself are not.
- **Watch the fourth content home.** The same attempt accumulated ~2,700 words of
  explanatory prose inside its normative section — bound by no criterion, cited by
  no task, checked by nothing — and it regenerated consistency defects on every
  edit. Mechanism belongs with the implementation; the evidence that a mechanism is
  right belongs in assumptions, cited once.
- **Repair churn is itself a defect source.** Across the abandoned attempt's last
  four rounds, most blockers found in each round were introduced by the previous
  round's repair. A large repair on a long contract is not free.

## What didn't work

Negative results from the abandoned attempt, recorded so they are not retried.
Each fixed something real. None reached the defect that ended the attempt.

| Approach | What it fixed | What it did not fix |
| --- | --- | --- |
| Prose acceptance criteria for a total state-to-action function | — | Nothing. Four rounds of reviewers attacked the prose, each repair produced fresh prose findings, and the criteria became a test plan |
| Restating the mapping as normative tables, criteria asserting properties of them | The prose-criteria class, permanently. Two reviewers independently re-derived the tables afterwards and they held | Convergence. The drift moved to clause-level mismatch between a criterion and the plan bullet implementing it |
| Splitting content into three homes — outcome, mechanism, grounding | The clause-drift class. Criteria prose fell 21% while the criterion count rose, because grounding left and hidden conjunctions came apart | Convergence, and it introduced a class of its own: criteria citing assumptions that were absent or wrong |
| Mechanising the citation edges — identifier parity, assumption parity, guard-fact binding | Real defects, each on first run. The identifier check caught a criterion outside its own scope; the assumption check caught a dangling citation; the guard-fact check caught an inverted claim | Anything about the model. All three bind the document to itself or to symbol names |
| Tests that parse the draft | Self-consistency | The model. A 602-line pre-approval suite, eleven of whose assertions read the draft, did not detect the unobservable premise in ten rounds |

**The measurements that matter for appetite.**

Sustained findings across ten rounds: 17, 16, 22, 23, 20, 19, 19, 23, 21, 17,
then 18 at the eleventh. Blockers bottomed out at 3 in rounds 6 and 7, then went
back up to 6, 8, 5, 3. The count was a steady state of the review-and-repair
loop, not a distance to done.

Repair size against the next round's blockers:

| Repair closed round | Lines changed in the pair | Blockers found next round |
| ---: | ---: | ---: |
| 7 | 124 | 6 |
| 8 | 377 | 8 |
| 9 | 250 | 5 |
| 10 | 204 | 3 |

By round 10 most blockers found were defects the previous round's repair had
introduced. A large repair on a long contract is a defect source, so the next
attempt should keep each contract small enough that a repair touches little —
which is a reason to slice this brief rather than write one spec.

**The one thing that would have worked** is asking, before writing any criterion,
what observes convergence. Nothing did. That question belongs at brief stage,
which is why this brief exists.

## Decision authority

- Repository maintainers own the shape decision between "reporting stays a pure
  projection" and "one component owns both halves". A prior owner decision
  favoured the former; it was taken against an abandoned draft and should be
  re-confirmed at the Ready review rather than inherited.
- The review protocol's owner decides U1, because a persisted pre-EXECUTE counter
  would be its state, not the query's.

## Ready gaps

Recorded rather than invented. Closed and remaining are both listed, so a Ready
review can see what moved.

**Closed by owner decision (see Owner decisions):**

- ~~U1 — where the authoring stop lives.~~ D1: a durable
  `pre_execute_repair_count` owned by the review protocol, stopping at three
  cycles. This also confirms the shape — `next` neither infers nor increments it.
- ~~U2 — what a read-surface claim can assert.~~ D2: two invariants scoped to
  application-directed I/O; the process-wide claim is rejected and no file count
  is stated.
- ~~U3 — hostile status file behaviour.~~ D3: the trustworthy-record threshold.
- ~~Success metrics unquantified.~~ The stop threshold is three findings-bearing
  repair cycles.

**Remaining for the Ready review:**

- **No appetite is set.** The two halves warrant separate ones: the counter is a
  small protocol change that fixes a live operational failure; the projection is
  larger and has two prior failed attempts behind it.
- **No slices are proposed.** `continue` selects them. D1's counter is the
  natural first slice and can ship independently of the projection.
- **Two bounded observations are still owed**, not as unknowns but as
  documentation the eventual specs need: an application-directed I/O trace with a
  positive control (per D2), and a trace of the current reader's behaviour on
  hostile status files (per D3, to record what the ruling changes).

## Spec map

None. No slices are confirmed and no spec is derived from this brief yet.

## Provenance

- Source: repository origin. This brief is authored from a failed delivery
  attempt in this repository, not from external input.
- The four normative tables — domain, discriminators, ordered preconditions,
  routing, and action attributes — survived independent re-derivation by two
  reviewers across rounds 9 and 10 and are the reusable asset from the abandoned
  attempt. They are preserved at commit `e1bdde746`, together with the record
  shape, the read-only guarantee, and the fail-closed catch-alls.
- The abandoned spec, plan, review history, and pre-approval test were removed
  from the working tree in the same change that created this brief; they remain
  in history at that commit.
