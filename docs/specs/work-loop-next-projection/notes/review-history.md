# Review history — work-loop-next-projection

Round-by-round repair history and superseded reasoning for this contract, moved
out of `plan.md` so the active review packet carries the current contract rather
than the path to it.

**This note is not part of the contract and is not reviewer input.** Nothing in
it binds an implementer. Every load-bearing assumption, constraint, residual
risk, routing rule, acceptance criterion, and implementation obligation lives in
[`../spec.md`](../spec.md) and [`../plan.md`](../plan.md); if something here
appears to contradict either, those win. A reviewer brief for this contract names
the spec and the plan, and does not name this file.

It exists so the audit trail survives: four pre-EXECUTE review rounds sustained
78 findings across two reviewer lanes, and the reasoning for several current
table cells is only legible against what they replaced.

## What was moved, and what was audited and kept

Moved here: the detailed round-by-round repair history and superseded reasoning
that was `plan.md`'s Changelog section. Nothing else.

**`spec.md`'s Assumptions were audited and retained in full — 0 words moved.**
That is a reviewed-and-retained result, not an unexamined section. All 27 bullets
were read against the test "is this history, or is it grounding the current
contract depends on". Every one fell on the grounding side, and four are the
reason the section cannot shrink:

| Kept | Why it is not history |
| --- | --- |
| The unlocked two-file read | An accepted residual risk, with the bound on what `run_id` does and does not cover |
| The unreset-`Approved` auto-fire across both human gates | An accepted residual risk, and the only record that the projection mirrors rather than introduces it |
| The 331-byte widest-record measurement | The derivation of the 1024-byte bound; without it the bound has a value but no origin |
| The light-mode marker's corpus validation | The evidence that P3's regex matches exactly the specs carrying a real marker, with no misses and no over-matches |

The rest are single-sentence grounded facts, each carrying the source that makes
an assertion about a named repository target checkable.

Context efficiency is subordinate to decision integrity here: moving an accepted
residual or a measured derivation out of the active contract would buy words by
deleting the basis of a decision, which is a worse trade than the words are
worth.

## Round-by-round


- 2026-08-31 — Split out of a larger contract that also carried an authored-word
  ceiling and a prose cut. Two review rounds on the combined contract produced 30
  then 43 findings, most attributed to the previous round's own repairs, and both
  reviewers independently identified the size as structural. The combined plan's
  dependency graph refuted its own atomicity claim.
- 2026-08-31 — Three fields the loop advances on — `complete_with`, `human_wait`,
  `sequence` — were unconstrained through two review rounds; an emitter returning
  empty values satisfied the whole contract. All now have derivation criteria and
  constant-value mutation proofs.
- 2026-08-31 — The automatic recording branch was cut: the projection cannot know
  a round's warranted reviewer roster, so requiring every warranted reviewer's
  payload was unverifiable by construction. An absent id now stops.
- 2026-08-31 — Review round 3 named the root defect as an unsettled record field
  set: criteria had been added requiring the record to carry a reset description
  and an artifact path, which no key could hold. Resolved by ruling that the
  record carries identifiers and scalars only and every reason goes to stderr, so
  the nine keys stand unchanged and no path-shaped value enters the record.
- 2026-08-31 — The runtime over-length refusal was dropped. A refusal would leave
  a live loop with no next action, and the invariant it guarded is already covered
  by the no-state-dump criterion; the size bound is now a suite assertion.
- 2026-09-01 — Restructured after four review rounds (30 → 43 → 19 → 37 findings)
  failed to converge. The diagnosis: the spec was specifying a total
  state-to-action function in prose acceptance criteria, so every round's repair
  of one row's wording opened a gap in another's. The mapping moved into tables in
  `spec.md` and the criteria became properties of those tables, taking the
  contract from 62 ACs and 17 tasks to its current 26 and 12.
- 2026-09-01 — Wave 3 was deleted rather than rewritten. `--operation-id`, its
  form check, replay and conflict behaviour, the two `state.json` fields, the
  state-schema reference, and the shipped invocations all landed in
  `docs/specs/review-record-idempotency/` (core 2.18.2, PR #1192). Ten criteria
  describing that mechanism were removed as already shipped; what remains of the
  recording branch became two Routing rows, now R21 and R22.
- 2026-09-01 — The `CODE-HUMAN-GATE` changes-requested criteria were dropped. They
  described a record for a branch `next` cannot observe: the human's merge
  decision is not in either state file, so that state has one row and the replay
  detail stays in the shipped resumption row, which already carries it.
- 2026-09-01 — Wave position stopped being an input dimension. It discriminates no
  row's action; it enters the record only as `cohort.wave-advance`'s `from_index`.
- 2026-09-01 (round 1 repair) — The restructure's own totality criterion was a
  control that could not fail. The domain was crossed with "each row set's
  discriminator values", read out of the same Routing table totality was checked
  against, so deleting a discriminator-bearing row deleted the members that would
  have exposed it: only 10 of 22 rows reddened. A Discriminators table now fixes
  each value set from a source outside Routing — the Status vocabularies
  `lint-spec-status.py` enforces, the `state.json` field domains, and a boolean —
  and the domain is a derivable 54 members with the count stated once. Re-checked
  after the repair: 0 uncovered, 0 ambiguous, and every Routing row in the spec's table reddening.
- 2026-09-01 (round 1 repair) — Three ways the contract could be satisfied while
  still handing an agent attacker-controlled text. Stderr was unbounded while the
  record was tightly bounded, and the guard module had already been through this:
  a 100 KB `run_id` produced a 100,055-character reason. `run_id` reached the
  record with no form check. Artifact reads were named by filename with no
  confinement or reader. AC14, P4, and AC15 close the three, all by reusing
  controls that already exist rather than inventing bounds.
- 2026-09-01 (round 1 repair) — Two holes the routing tables could not see. An
  off-table `(state, last_event)` pair — a valid state carrying an event that
  never targets it — was excluded from the domain by construction, so no criterion
  reached it; P7 now covers it. `mode` appeared in no precondition while Routing
  keyed on it, and P6's old "differs" test passed vacuously on two absent
  `run_id`s; P4 and the restated P6 close both. The precondition table went from
  six rows and three exit codes to seven and four.
- 2026-09-01 (round 1 repair) — `P1`'s light-mode marker was undecidable. The
  literal appears across `docs/specs/` in six header spellings plus HTML comments,
  acceptance-criterion mentions, and one negated prose occurrence, and no Python
  in the repository parses it. The condition is now a single regex over the
  pre-`##` zone with comments stripped, validated against the corpus: it matches
  exactly the 37 specs carrying a real marker, with no misses and no over-matches.
- 2026-09-01 (round 1 repair) — AC3 could not be distinguished from the roster
  equality test, leaving the discriminator resolver — 12 of 22 rows — with no
  coverage. AC3 now sources its expectation from the spec's Discriminator column
  and names the R7/R8 exchange as its mutation; that mutation changes four domain
  members' actions while changing no row's action or coverage.
- 2026-09-01 (round 1 repair) — Three smaller gaps closed: `complete_with` now
  states that it names events rather than invocations and that `wave-passed` and
  `contract-amendment` take arguments the record does not supply; the unlocked
  two-file read is recorded as an accepted Assumption with what P6 does and does
  not bound; and AC19 states that its comparison set is the union across both
  modes, without which its exactness claim had no quantifier.
- 2026-09-01 (round 2 repair) — Round 2 sustained 16 findings against round 1's
  own repairs, which is the non-convergence signature this contract already has a
  history of. Rather than patch again, one premise was inverted. Round 1 had
  claimed each discriminator's value set was "sourced outside the Routing table",
  and that claim was false twice over: the citation for `plan.md`'s vocabulary
  named a script whose docstring puts `plan.md` out of scope, and the canonical
  reader enforces no vocabulary at all — it returns `draft`, `Frobnicate`, an
  empty string, or nothing, four outcomes the declared sets did not contain, so
  totality was again passing over a restricted domain. Independence now comes from
  closure, not citation: D1 and D2 name two values each and fold every other
  possible reader outcome into `other`. The domain fell from 54 to 44 and needs no
  external source. Re-verified: 0 uncovered, 0 ambiguous, every Routing row in the spec's table caught by
  the deletion mutation.
- 2026-09-01 (round 2 repair) — Three defects in round 1's own repairs. AC15
  required the crash artifacts to be read through guard readers while P5 forbade
  opening them, making its hostile-fixture clause unsatisfiable; the read targets
  and the presence probes are now separate criteria under their two distinct
  roots. The precondition order shadowed the crash-artifact row for the
  interrupted `init` it existed to catch, because that state has a temporary and
  no `engine-state.json`; it is now P1. And the plan put AC3's live drive in the
  pack suite, which may not read `spec.md`.
- 2026-09-01 (round 2 repair) — `reset-and-reinit` was removed from the action
  vocabulary. R22 had answered a finished spec-plan run with a destructive action
  conditioned on "if implementation is later requested" — a human decision neither
  state file records, which is the same unobservability that collapsed
  `CODE-HUMAN-GATE` to one row. Spec-plan `DONE` now answers `complete`, the reset
  stays a human-initiated path in the shipped row's prose, and no action in this
  contract is destructive. `human_wait` is now exactly `kind == "wait"`.
- 2026-09-01 (round 2 repair) — Four checks that could not fail, and one that
  could not be implemented one way. AC11 never said whether its character class
  was a runtime refusal or a suite assertion, and `from_index` is the one
  `parameters` value taken from a state field no precondition form-checks — it is
  now a runtime refusal. AC23's grep passed before the edit, because "next"
  already appears twice in the guide. AC20 named no file, so the consumer control
  could land in a reference the consumer never loads. The four exit codes were
  only required distinct from each other, not from the engine's existing exit 1
  and argparse's 2. And the marker regex (now P3's) admitted `Modelight` and `light-weight`,
  both now rejected while the 37 real markers still match.
- 2026-09-01 (owner scope change) — The unhappy paths were missing. The contract
  routed the forward walk and the two `halt` branches, but answered the three ways
  a run goes *backwards* with a single `spec.draft`, and answered an exhausted
  review budget by asking for another review round. Four cases, worked in as rows
  rather than criteria: a rejected gate now routes to `spec.reset-and-revise`,
  which owes a status reset before `spec-ready`; a contract amendment routes to
  `spec.amend`, which owes authority, completed-task pins, reapproval, and
  rescheduling; a spent review budget or a stasis fingerprint match routes to
  `await-replan-decision`; and splitting the contract into separate specs is named
  as one of that wait's replanning options rather than as an action, because which
  option applies is not in either state file. The cap case was the dangerous one:
  the engine refuses `findings-remain` at the cap, leaving `reviewers-clean` as the
  only event it still accepts, so a projection answering `run-review` there made
  declaring a false clean the only escape. No new engine transition was needed —
  two paths already had edges and the rest resolve to a human decision, so the verb
  stays read-only. 22 rows became 26, the domain 44 members became 47, and the
  action vocabulary 17 became 20. Re-verified: 0 uncovered, 0 ambiguous, all 26
  rows caught by the deletion mutation. No acceptance criterion changed shape,
  which is the property the table restructure was for.
- 2026-09-01 (round 3 repair) — Round 3 sustained 22 findings across both lanes,
  and three of the five blockers were defects in the unhappy-path work added
  hours earlier. The worst: D5's stasis test compared the two fingerprint fields
  without the non-empty qualifier the shipped detector carries, and both default
  to `[]`, so a fresh run compared equal and **every loop's first `next` call
  would have answered `await-replan-decision`** — worse at the spec stage, where
  ordinary pre-EXECUTE rounds never call `review record`, so both lists stay empty
  for the whole spec-plan loop and `spec.review` was unreachable. Reproduced
  against this run's own `state.json`. Fixed by reusing the shipped predicate,
  non-empty-and-equal over the sorted-unique canonical form, with a criterion that
  drives the fresh-run and two-consecutive-clean-round cases.
- 2026-09-01 (round 3 repair) — Two more of the same shape: reusing a control's
  inputs instead of its semantics. D5 declared two values where the blessed cap
  path is three-outcome — its integer helper returns a refusal, not a boolean, for
  a malformed counter — so a planted `"5"` resolved to `within-budget` and routed
  straight into the false-clean funnel R5 and R25 exist to close. And AC11 admitted
  "or is a boolean", which in Python admits `True` as an integer, on the one
  `parameters` value taken from an unchecked state field. Both now resolve through
  the guard module's helper. D3 gained the `malformed` catch-all D1 and D2 already
  had, so every discriminator is now total over what its source can produce.
- 2026-09-01 (round 3 repair) — The replanning options were not just incomplete,
  they were prohibited. The lifecycle reference this row loads states that an
  outcome is not narrowed because a retry budget or review round ended, and that a
  retry cap or stasis never invokes the amendment or creates a follow-on — so
  "narrow" and "split" contradicted the file `await-replan-decision` points at.
  Meanwhile the two continuations the engine's own refusal names were absent.
  `exhausted` split into `cap-reached` and `stasis` because their legal
  continuations differ: at the cap only reset or the paired human-directed
  `--allow-retry-cap-override`, under stasis a repaired round. Splitting a contract
  is a scope-owner decision outside this loop, not something a spent budget
  authorises.
- 2026-09-01 (round 3 repair) — `complete_with` was half-fixed. AC10 emits the
  unguarded edge set, so a `cap-reached` record still advertised `reviewers-clean`
  — the one event the engine accepts at the cap, and nothing guards it. AC10 now
  carries one declared exception. Also closed: a Precondition for an unreadable
  `spec.md` before the marker test (it previously fell through and was reported as
  an ambiguous mode); AC20 repointed to the always-loaded skill body after the row
  insert falsified its placement argument, plus a fifth statement that stderr is
  diagnostic and a `wait` authorises nothing; AC24 given a redaction check; AC19
  corrected to twelve of fifteen with T8 amending the one shipped row whose prose
  contradicts its new identifier; and the unreset-`Approved` auto-fire recorded as
  an accepted, pre-existing residual.
- 2026-09-01 (round 3 repair) — Row references across both documents were
  renumbered against the 29-row table. Two were load-bearing rather than
  editorial: AC3's mutation and AC1's deletion proof are specified *by row number*,
  and the plan named a pair that no longer carries a discriminator, so an
  implementer would have mutated the wrong rows and shipped the resolver with a
  proof that could not fail. 26 rows became 29, the domain 47 members became 55.
  Re-verified: 0 uncovered, 0 ambiguous, all 29 rows caught by the deletion
  mutation, closure over 20 actions.
- 2026-09-01 (round 2, refuted) — Nine findings were tested and not sustained.
  Notably: `halt` carrying no `load` is a deliberate table cell, not a gap; the
  duplicated row counts cannot drift silently because both documents are hashed
  once approved; and AC9's malformed-`run_id` clause is redundant with AC6 plus
  AC7 but redundancy between two criteria that both hold is not a coverage gap.
- 2026-09-01 (round 1, refuted) — Four findings were tested and not sustained, and
  the artifact is unchanged on each: AC12 is not dominated by AC5/AC7/AC11,
  because a 64-character fingerprint satisfies all three while violating it, so it
  stays and T5 now drives that exact case; the extra base keys are already sourced;
  per-task verification modes were already derivable from the Testing Strategy,
  though they are now stated per task anyway; and T8's test location was already
  fixed by the Constraints section.
