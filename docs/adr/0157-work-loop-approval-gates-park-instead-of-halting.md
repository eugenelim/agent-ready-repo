# ADR-0157: Work-loop approval gates park instead of halting, bound to exact digests

- **Status:** Accepted
- **Date:** 2026-11-04
- **Areas:** work-loop, security
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0099 (§7 keeps every spec-plan and human approval gate, and defines "parked", which this record uses unchanged); ADR-0154 (the per-run supervisor store and product ref that `start` creates once both approvals exist)

## Decision summary

- **Decision:** `spec-approved` and `plan-approved` become parked gates. The controller parks a reviewer-clean spec-plan pair with the supervisor, a read-only `gates` verb lists every parked gate with its exact spec and plan digests, what to read, and what each answer does, and `start` admits only the digests the human approved. While a gate waits, the controller may work other independent specs.
- **Because:** a full-mode run idles at every approval today, and the wait can end without removing or weakening a human gate.
- **Applies to:** the two pre-`start` approvals of a full-mode work-loop run in one checkout. Not light mode, amendments after `start`, merge, or a brief-level runner.
- **Tradeoff accepted:** the supervisor gains two verbs and one local record kind, and `start` gains two arguments it requires whenever it records an approval.
- **Revisit if:** a brief-level runner needs gates from several worktrees in one listing, or approvers routinely re-park because the approval edits change a digest.

## Context

A full-mode run asks for two human approvals before the supervisor's `start`: `spec-approved` (the scope decision) and `plan-approved` (the build-strategy decision). Each approver writes `Status: Approved` and a dated Changelog entry, and the controller then runs `start`. Until both answers arrive, the controller stops. A three-slice brief therefore idles at six approvals.

Three constraints hold:

- **The gates stay.** RFC-0099 §7 keeps every spec-plan and human approval gate, and `AGENTS.md` forbids cutting a required human approval.
- **"Parked" is already defined.** RFC-0099 §7: the controller may preserve observations and the current diff but may not dispatch implementation work.
- **Approved hashes bind approval to exact revisions,** and a stale approved hash may never resume (RFC-0099 §7).

Today `start` pins whatever spec and plan are on disk when it runs: it computes both canonical digests and compares them with themselves. Nothing ties those digests to the revision the human read. A spec edited between the human's answer and `start` is admitted as approved.

## Decision

We will make `spec-approved` and `plan-approved` parked gates: listed, answered asynchronously, bound to exact digests at `start`, and never approved by default.

- **D1:** The two gates and their order are unchanged. Each still needs its own named human's answer, and `start` still records the pair as one `approval-record.v1` and one `initial-plan-review.v1`. Parking changes only what the controller does while it waits.
- **D2:** A gate is parked by the supervisor verb `park <spec-dir> --gate spec-approved|plan-approved`, run by the controller only after every fired pre-EXECUTE reviewer is clean for the current pair. `park` computes the spec and plan gate digests itself, records them with the `HEAD` commit in the checkout's local supervisor store, commits nothing, and refuses exactly when `start` would answer `current`: the latest approval pair carries the envelope fingerprint the spec derives now, the spec's declared terminal intent, and the code trust given to `park`. It also refuses a `plan-approved` gate whose spec is not `Approved`. A gate already parked at the same digests answers `current`. After an amendment, or a change of terminal intent or code trust, the spec parks like one with no pair, so every re-approval is digest-bound.
- **D3:** The read-only verb `gates` lists every parked gate in the checkout. Each entry carries the spec directory, the gate, the recorded spec and plan gate digests, the commit, the files to read at that commit, the consequence of each answer, and its state: `pending` only when the recorded digests equal the gate digests of the files at the recorded commit and of the working-tree files, `stale` otherwise, or `invalid` for a record that fails its field checks. A well-formed record written outside `park` is in the threat model. The files to read and the consequences are fixed text owned by the supervisor; no controller-supplied text appears in the listing. `gates` writes nothing.
- **D4:** The answers are `approve`, `reject`, and no answer. Only `approve` from the gate's named human advances the gate. `reject` returns the pair to drafting under the existing rejected-gate rule. No answer, a timeout, a session end, a `stale` state, a missing or malformed record, or any listing output leaves the gate unapproved. No verb, flag, default, or record turns a parked gate into an approval.
- **D5:** A gate digest is the existing canonical contract digest (line endings, trailing whitespace, the status token, and checkbox contents normalized) taken over the artifact with its `## Changelog` section removed, so an approver's `Status: Approved` and Changelog entry do not change it. Every other edit does.
- **D6:** `start` requires `--approved-spec-digest` and `--approved-plan-digest` whenever it records an approval pair, on a first admission or a re-approval after an amendment: the gate digests the humans approved. A `start` that answers `current` for an admitted run neither needs nor compares them, because in-envelope plan edits after approval change the plan's gate digest. It refuses when either differs from the current gate digest, and keeps its existing refusals. A changed pair makes every earlier approval stale: it is re-reviewed, re-parked, and approved again.
- **D7:** While a gate is parked, the controller dispatches no implementation work for that spec and does not edit its spec or plan except through the rejected-gate route. It may draft, review, or run another spec that does not depend on the parked one, as the delivery brief's Spec map or the spec's `Depends on:` line records. With no such work, it ends its turn with the `gates` listing.

## Decision drivers

- No human approval is removed, merged, or inferred.
- The human's answer binds to the exact revision they read.
- The controller never supplies text the approver reads as fact.
- No run state exists before both approvals.

## Consequences

**Positive:**
- A controller with other independent specs keeps working while approvals wait, and the human can clear several gates in one sitting.
- `start` admits only the revision a human approved, which closes the edit-between-answer-and-start gap.
- The listing is derived from the supervisor's own digests, so a stale gate is visible before anyone answers it.

**Negative:**
- Every `start` call that records an approval gains two arguments; controllers, evals, and the skill's command lines change.
- The listing covers one checkout. Gates parked in another worktree appear only in that worktree's listing.
- An edit inside `## Changelog` that is not an approval entry does not stale a gate. The Changelog is history, not contract, so the gap is accepted.
- The supervisor gains two verbs and one local record kind for its script pins to cover.

**Revisit if:** a brief-level runner needs gates from several worktrees in one listing, or approvers routinely re-park because the approval edits change a digest.

## Confirmation

- **Mode:** lint/CI
- **Signal:** core pack tests prove that no answer, a stale gate, a missing or malformed park record, and a `gates` listing each leave `start` refusing, and that `start` refuses a digest that differs from the current gate digest. A test asserts the listing carries no controller-supplied text.
- **Owner:** core pack maintainers

## Alternatives considered

- **Keep halting at each gate:** meets every driver but leaves the run idle at every approval, which is the problem this record solves. It also leaves the edit-between-answer-and-start gap open.
- **Default a parked gate to approved after a wait:** rejected against "no human approval is removed, merged, or inferred". Silence is not consent, and RFC-0099 §7 forbids it.
- **Derive pending gates from spec and plan statuses, with no `park` record:** rejected against "the human's answer binds to the exact revision they read". A `Draft` spec mid-authoring would list as pending, and nothing records which digests were offered.
- **A controller-written gates file in the repository:** rejected against "the controller never supplies text the approver reads as fact" and "no run state exists before both approvals". A hand-written file can claim digests the artifacts do not have, and a committed record before `start` is history the supervisor does not own.
- **Bind with the whole-file canonical digest:** rejected against "the human's answer binds to the exact revision they read". The approver's own Changelog entry would make every approval stale on arrival.
