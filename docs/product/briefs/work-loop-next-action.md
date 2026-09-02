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
- A non-converging authoring loop is surfaced to a human within a bounded number
  of passes, by whichever component owns stopping.
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

## Assumptions and risks

**Load-bearing unknowns.** Each needs an observation against code or a governing
decision before the dependent work can be specified. None is settled by review
opinion, and each invalidates a section of any spec written over it.

| # | Unknown | Oracle | Invalidates if answered the other way |
| --- | --- | --- | --- |
| U1 | Is there a durable signal an authoring-loop stop can count? The pre-EXECUTE ordinal is not persisted in either state file and no script writes it; it survives only as a command argument reconstructible from a gitignored session root. | The persisted field sets of both state files, and every writer in the cohort and engine scripts | The entire stopping half, and any claim that it can be delegated to a component that already tracks passes |
| U2 | What can a read-surface bound over the query honestly assert? A cold process executing the loop's own guard module opens 37 files beyond any set a contract would name, all interpreter and standard-library loading. | A cold-process open trace, partitioned into files the component names versus module loading | Any confinement criterion phrased as "opens no file outside a declared set", and the instrument meant to check it |
| U3 | For a hostile artifact status file — symlinked, non-regular, oversized — is the contract's answer a zero-exit stop record or a non-zero refusal? The two are both defensible and produce different caller-visible behaviour. | The canonical reader's raise behaviour, the discriminator catch-all's routing, and the existing precedence rules | The hostile-input criteria, and consistency with the row that already gives an unreadable cohort state file a zero-exit stop record |

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

## Decision authority

- Repository maintainers own the shape decision between "reporting stays a pure
  projection" and "one component owns both halves". A prior owner decision
  favoured the former; it was taken against an abandoned draft and should be
  re-confirmed at the Ready review rather than inherited.
- The review protocol's owner decides U1, because a persisted pre-EXECUTE counter
  would be its state, not the query's.

## Ready gaps

Recorded rather than invented. A Ready review must resolve these:

- **U1, U2 and U3 are open.** They are acquisition work, not specification work,
  and should be closed before slices are cut.
- **The shape decision is unconfirmed** for this brief, as above.
- **No appetite is set**, and the two halves may warrant separate ones.
- **Success metrics are unquantified.** "A bounded number of passes" needs a
  number, and that number depends on U1.
- **No slices are proposed.** Create mode does not author them; `continue` selects
  them after the gaps above are closed.

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
