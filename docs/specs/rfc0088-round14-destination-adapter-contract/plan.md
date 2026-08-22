# Plan: rfc0088-round14-destination-adapter-contract

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

## Approach

Seven tasks in dependency order, delivered as one review unit. The ordering is forced by
a single fact: **the fixture pair cannot be specified before it is measured.** T1 and T2
are candidate elimination and measurement; everything the spec says about the pair is
downstream of what they observed. Writing the RFC amendment first would have meant
naming a candidate that does not start.

Row counts, closure tallies and residual counts are deliberately absent from this
Approach. Their canonical homes are `workspace.toml [backlog].open` and the digest's
disposition block; restating them here would drift at the first edit to either.

The round's shape differs from round 13's. Round 13 was mostly *disposition* over
existing evidence. Round 14 is one measurement plus one governance amendment, and the
measurement exists to make the amendment honest rather than the other way round.

## Constraints

- No new repository dependency, no compile step, no production interface change.
- No real credential, live account, or captured response anywhere in the repository or
  in a results artifact.
- No third-party contact from the repository. The reference-consumer probe is an
  operator-run, read-only observation outside the repository's execution path.
- Every RFC hunk below the `## Amendments` anchor. The body is frozen.
- No file matching a follow-on-artifact shape is created.
- The evidence apparatus stays out of tree at its existing location. Nothing about it is
  recreated.

## Tasks

### T1 — Eliminate or confirm the leading candidate

**Depends on:** none
**Verification mode:** goal-based check
**Tests:** no stub (goal-based). *Done when:* the candidate's server has been started
in a container and its outcome recorded — either it serves a login surface, or it
refuses and the refusal is the recorded reason for elimination.

**Approach:** pull the image, invoke the API server with no cluster configuration, and
read what it does. A documentation-confirmed authentication shape is worth nothing if
the component cannot start the way the fixture contract requires, and that is only
visible by trying.

**Outcome:** eliminated. The server exits fatal on a missing cluster configuration, so
it would be a control plane rather than a pinned container.

### T2 — Stand up the fixture pair and measure token landing and cache-control

**Depends on:** T1
**Verification mode:** visual / manual QA, then goal-based
**Tests:** no stub (manual QA first). *Done when:* both containers serve a login
surface, a real browser login succeeds against each, and the login document's render
shape, the issuing response's cache directive, the token's storage location, and the
closed profile's at-rest contents are each observed rather than inferred.

**Approach:** exploratory probe first, to learn the shapes without committing them to a
row inventory. Record the raw observation before designing the assertions around it —
designing assertions first is how a measurement gets calibrated to the answer it
expected.

**Outcome:** pair selected. The SPA half's login document arrives with no `<form>` and
no password input and acquires both under script; the contrast half's arrives with each
already present. The token-issuing response carries no cache directive, and the token
reaches browser user-data at rest through the destination's own web-storage write.

### T2a — Probe the reference consumer's unauthenticated surface

**Depends on:** none
**Verification mode:** goal-based check
**Tests:** no stub (goal-based). *Done when:* the note records the probe date, each
surface probed, and the status code observed for each.

**Authorisation:** pre-authorised by the RFC approver, who commissioned this probe by
name as one of the round's three named checks. Recorded here because an Ask-first tier
whose only instance ran with no recorded ask is a tier that permits everything.

**Approach:** a handful of unauthenticated read-only requests against documented public
endpoints, to establish which surfaces need the session. This is the round's only
third-party contact and it sits under the spec's **Ask first** tier: it is operator-run,
outside the repository's execution path, and never enters CI. Probing identifiers until
a private one is found is refused rather than asked about — that is enumeration against
a third party.

**Outcome:** the public variant is open, an account-scoped surface is gated, and the
private variant is recorded as unmeasured with the one input that would close it.

### T3 — Build the measurement arm

**Depends on:** T2
**Verification mode:** TDD-shaped via the mutation harness
**Tests:** the mutation harness is the test. Each declared row has a case asserting the
row's *flipped* outcome under mutation; the no-op case asserts a clean run reports
clean. Red state: a row with no case, or a case whose anchor is not unique within the
mutable region, throws.

**Approach:** follow the round-12 page-resident driver's construction — declared row
inventory checked against emitted rows, mutable region below an explicit marker, anchor
uniqueness asserted over the region the replacement actually uses. Back up the driver
and the baseline results before the first mutation run: a harness killed mid-run leaves
the mutant in place, and an untracked file does not show up in `git status`.

Two rows are declared failing and mutate *toward passing*. A privacy row asserts over
the serialized artifact bytes rather than over the code that built them, in two passes,
with the second gating the write.

**Outcome:** eleven rows, twelve mutation cases — one row is a conjunction and carries a
case per load-bearing conjunct. Baseline and harness both clean, no stale mutants, and
the harness summary persisted beside the results artifact.

### T4 — Amend open question 3 and record the decision records

**Depends on:** T2
**Verification mode:** goal-based check
**Tests:** no stub (goal-based). *Done when:* `r13-decision-surface.py` reports one
record per open question with every hunk inside the evidence layer, and
`r13-digest-coverage.py` reports no prohibited apparatus figure in the round-13 section.

**Approach:** rewrite the superseded question-3 ruling in place rather than appending a
second one, so the RFC never carries two answers. Leave question 4's ruling untouched.
Append the decision records as a new same-level amendment bullet, which also bounds the
preceding section correctly for the decision-surface reader.

**Outcome:** done, and a stale row in the Current Experimental state table that this
round contradicted outright was corrected in the same pass.

### T5 — Write the note and its digest entry

**Depends on:** T2a, T3, T4
**Verification mode:** goal-based check
**Tests:** no stub (goal-based). *Done when:* `r13-digest-coverage.py` passes with the
new note enumerated and covered by exactly one entry above its substance floor.

**Approach:** append the digest entry rather than inserting it. Keep prohibited
apparatus figures out of both the entry and the note's headline claims; the figure
boundary module is the authority, not judgement about what reads like a headline.

**Outcome:** done. The note describes the reference consumer by shape rather than by
name, endpoint vocabulary included — a provider's API terminology identifies it as
surely as its name does.

### T6 — Register the spec and run the gate chain

**Depends on:** T5
**Verification mode:** goal-based check
**Tests:** no stub (goal-based). *Done when:* the spec has a workspace entry, the
governance controls pass, and the repository gate chain reports no new failure against
its pre-round state.

**Outcome:** registered in `["ini-002".work].shipped`; governance controls, inherited
apparatus controls, the privacy sweep, `lint-spec-status`, the documentation-entry link
tests and `SKIP_SAST=1 make build-check` all clean.

## Rollout and recovery

Single branch, single review unit, squash-merged. Recovery is `git revert` of one
commit range: nothing in this round is consumed by another artifact at build time, and
the evidence apparatus is out of tree, so reverting the repository side leaves no
dangling reference. The apparatus arm is additive — removing it disables one arm and
affects no other harness, since it extends no shared verifier and shares no corpus.

## Risks

- **The fixture pair drifts.** Closed: both halves are pinned by image digest in the
  note, which is what AD-4 requires and what makes a re-run comparable. The tag is kept
  beside the digest for readability only. What remains open is the registry the pull
  contacts on a cold cache; AD-4 names it as an allowlisted egress rather than pretending
  a pinned container has none.
- **The measurement generalises further than it should.** Two destinations establish
  that the accommodation's precondition is not universal; they do not establish a
  population. The note and the amendment both say so.
- **The note is unregistered in the figure-verifier corpus**, so its figures are carried
  by the results artifact rather than by claim accounting. Stated as a limit in the note
  rather than silently accepted.
