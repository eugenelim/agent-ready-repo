# Plan: review-record-idempotency

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - Ownership source: `docs/architecture/loop-infrastructure.md` §2-3 makes
    `loop-cohort.py` the sole writer of `state.json`. `packs/AGENTS.md`
    §Version bump rule and §Shipped pack content own the release and portability
    constraints.
  - Analogous implementation — id-keyed idempotency with form validation in the
    same file: `loop-cohort.py:1536-1581` (`cmd_record_attempt`); the
    `<run_id>:<digits>` form check at `:1552-1565`, the early-return no-op at
    `:1566-1572`, and its distinguishing stdout line at `:1567-1571`. Tests: the
    crash-window block from `packs/core/tests/skills/work-loop/test_loop_engine.py:2232`.
  - Field-shape precedents in the same template: `last_record_attempt_cycle_id`
    (an id, default `null`) and `last_review_clean_digest` (a digest, default
    `null`), both in `packs/core/.apm/skills/work-loop/assets/state.json`.
  - Named uncertainty: none. The change mirrors a precedent 350 lines above it in
    the same file.

## Approach

`cmd_review_record` gains one optional flag and one early return. When the
supplied id equals the recorded id and the payload digest matches, the round is
already written and the command says so without touching a counter. When the id
matches and the digest does not, the payload disagrees with what was recorded and
the command refuses.

The caller supplies the id. `loop-cohort.py` reads no engine state today and this
change does not make it start; the writer validates the id's form against
`--expect-run-id`, which the verb already requires.

The digest earns its place on two of four forms. `--all-skipped` has a constant
payload and `--direct-clean-file`'s bytes must equal the clean sentinel before
they are hashed, so neither can present a conflict under a reused id; the id alone
discriminates there. `--fingerprint` and `--report --adjudication` have varying
payloads and are what the digest is for.

The comparison happens after the existing per-form payload resolution, not before
it. That ordering is deliberate and observable: a clean form whose artifact has
been evicted still refuses, because the digest cannot be computed and a completed
write cannot be asserted without one.

The compatibility evidence is captured first, as a per-form delta rather than a
whole file. The template gains two keys, so every post-change run starts from a
29-key state and a whole-file comparison against a 27-key capture could never
pass.

The replay policy is untouched. The shipped resumption rows, their pinned tests,
and the pack's eval expectations all state the human-authorization obligation,
which this contract retains; no task edits them.

## Constraints

- `loop-cohort.py` remains the sole writer of `state.json` and gains no reader of
  `engine-state.json`.
- No runtime dependency is added to any shipped pack script.
- No task edits `packages/agentbundle/`; the protected-tree gate at
  `tools/repo/build_gate_chain.py:305` requires an engine-scoped RFC trailer for
  that tree and nothing here needs it.
- No task edits `references/session-resumption.md`, its two pinned tests
  (`test_findings_remain_skill_prose_present`,
  `test_reviewers_clean_skill_prose_obligations`), or `evals/evals.json`. Those
  surfaces state the replay policy, which this contract retains.
- No task edits an accepted decision record's body or a `Status: Shipped` spec's
  body.
- `packs/core/tests/skills/work-loop/` already runs in `make test`
  (`Makefile:544`), so no CI wiring is added.
- `pytest` and `make build-check` cannot run concurrently in this tree; gate runs
  are serialized.
- `spec.md` and `plan.md` are hashed file-wide once approved; every enumeration an
  implementer needs is here and no task authors one mid-execution.
- A peer session is active in this repository's skill tree; re-check
  `packs/core/.apm/skills/work-loop/` for landed changes before T5.

## Payload digest derivation

The comparison digest is derived at each comparison, never stored. The preimage is
the form's literal name, then `\n`, then the form's payload bytes; the digest is
`sha256` over its UTF-8 encoding. The literal prefix is what stops two forms
colliding.

| Form | Literal | Payload bytes | Derived on a repeat from |
| --- | --- | --- | --- |
| `--fingerprint` | `fingerprint` | the sorted, deduplicated fingerprint list joined by `\n` | `finding_fingerprints` |
| `--direct-clean-file` | `direct-clean` | the lowercase hex sha256 of the artifact's bytes | `last_review_clean_digest`, when `last_review_clean_source` is `direct-clean` |
| `--report --adjudication` | `report` | the lowercase hex sha256 of the report's bytes | `last_review_clean_digest`, when `last_review_clean_source` is `report` |
| `--all-skipped` | `all-skipped` | the empty string | a constant |

The writer already sorts and deduplicates fingerprints at `loop-cohort.py:1939`,
which is what makes a re-ordered or repeated finding set one payload. A round
whose `last_review_clean_digest` is `null` has no derivable digest and reaches R5;
that null is reachable today at `loop-cohort.py:2016`.

## Anchor obligations

Content-anchor checks that this change moves, and the task that owns each. Each
was located by a sweep over `packs/core/tests/`, `tests/`, and `tools/` for
assertions on the files this change touches.

| Anchor | Assertion | Owner |
| --- | --- | --- |
| `test_loop_cohort_cli.py` `EXPECTED_STATE_KEYS` | exact set equality on the bundled template | T4 |
| `test_loop_cohort.py` Phase-1 field check | subset, so unaffected | none |
| `fixtures/golden_cli_streams.json` | pins no `review record` output | none |
| `test_loop_engine.py` two prose tests | require four phrases be *present* in the two rows; adding a flag to a recipe keeps them | T4 |
| `test_finding_adjudication_contract.py:1286,1319` | pins `--fingerprint <validated-adjudication-sha256>` and asserts token *order* | T4 |

## Construction tests

- Every new refusal carries a mutation proof: the invariant, the test catching its
  removal, the exact mutation, the expected failure.
- The compatibility comparison is a baseline artifact captured before the writer
  changes, never a post-change assertion of what the line now says.
- The invocation check names its closed site list, so a site added later is either
  in scope or visibly out of it.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Verification evidence — the flagless baseline | T1 | `notes/flagless-baseline.json` committed before the writer's commit | Artifact present and its commit precedes T2's |
| Current product truth — the skill payload | T2, T4, T5, T8 | `make build-self-dry-run` clean | Source edited, projections regenerated |
| Interface compatibility — the persisted schema | T3 | Field table and template carry the recorded-id field; the reference states the digest's per-form derivation | Reference, template, and writer agree |
| Verification evidence — the QA transcript | T7 | Recorded counters, id, and exit codes | Transcript committed at `notes/qa-transcript.md` |
| User-facing promise — the two core guides | T6 | Both name the flag | Guides describe shipped behavior |
| Decision rationale — the governing decision's disposition | T8 | The Assumptions statement carried to the approval gate | Approver accepts or directs a superseding record |
| Release history — the changelog | T8 | Free-standing dated entry with `### Highlights` | Entry at top level; highlights projection regenerated |
| Reusable learning | T8 | `project-knowledge` receipt or recorded unavailability | Receipt recorded or unavailability named |

## Design (LLD)

### Design decisions

- The flag is optional and attaches outside the existing mutually exclusive group,
  so it composes with all four forms without touching them.
- The id and the counters are written in one atomic write, so a crash cannot
  record the id without the counters or the reverse.
- A flagless recording leaves the recorded id alone. The field names the last
  round recorded under an id, and a resuming session only ever compares it against
  a freshly computed id, so a non-matching value correctly reads as "not
  recorded".
- The AC4 path prints a distinguishing line and the AC5 path a distinguishing
  reason, following the precedent's `(idempotent no-op)` line, because one exit
  code cannot separate three outcomes.

### Data & schema

Two fields, both defaulting to `null`:
One field, `last_review_record_operation_id`, defaulting to `null` and
absent-tolerant on read, so a `state.json` written before this change reads as "no
id-recorded round is current" — the correct answer for a round that predates the
field. The comparison digest is derived, not stored.

### Interfaces & contracts

No payload contract changes. The CLI gains one optional flag.

### Component / module decomposition

No new module and no new file. The `<run_id>:<digits>` form check is extracted
from `cmd_record_attempt` into one helper both verbs call, rather than copied a
second time into the same file.

### State & control flow

Read state, validate the run id, validate the operation id's form, resolve the
form's payload as the command already does, compute the digest, compare against
the recorded pair, then either return early or perform the existing mutation with
the two fields set.

### Failure, edge cases & resilience

A malformed id, a matching id with a differing digest, and a matching id whose
artifact is unreadable each exit non-zero changing nothing. An absent recorded id
is not an error; it is the no-current-round reading.

### Quality attributes (NFRs)

The early return adds no file access beyond the payload resolution the command
already performs.

### Dependencies & integration

None added.

## Tasks

### T1: the flagless behavior is captured before anything changes

**Depends on:** none

**Tests:**
- A committed artifact at `notes/flagless-baseline.json` recording, for each of
  the four forms, the command's stdout line and the delta over the six named
  fields (AC12's comparison value).

**Approach:**
- Record a per-form delta, not the resulting file: T3 adds two template keys, so
  a whole-file comparison could never pass afterwards.
- Normalise resolved paths, digests, and run-id UUIDs the way the existing golden
  support module does, so the comparison stays an equality.

**Done when:** the artifact is committed and replaying the capture against the
unchanged writer reproduces it exactly.

### T2: the writer implements every row of the outcome table

**Depends on:** T1

**Tests:** one case per outcome-table row, plus the digest properties.
- The flag is accepted alongside each of the four forms (AC1).
- R6 malformed id (AC2); R1/R2 same round delta (AC3); R3 replay (AC4); R4
  conflict (AC5); R2 twice (AC6); R5 uncomputable digest on both a first
  application and a repeat (AC7).
- Re-ordered and duplicated fingerprints yield one digest (AC8); no two forms
  share a digest (AC9).
- R3's stdout line is distinct (AC10); R4, R5, and R6 stderr reasons are each
  distinct (AC11).
- The four flagless forms match the baseline and leave the recorded id alone (AC12).
- The field holds the recorded id (AC13) and is `null` before any id-recorded
  round (AC14); no field stores a digest (AC15).
- The R2-then-R1-then-repeat sequence resolves as R3 (AC16).
- `record-attempt`'s two refusal messages and its `(idempotent no-op)` line are
  byte-unchanged after the form check is extracted.
- Mutation proofs: removing the digest comparison makes R4 pass; removing the
  form check makes R6 pass; removing the early return makes R3 increment;
  removing the literal prefix from the preimage makes two forms collide;
  clearing the recorded id on R1 makes AC16 fail; storing the digest instead of
  deriving it makes AC15 fail.

**Approach:**
- Extract the `<run_id>:<digits>` form check from `cmd_record_attempt` into one
  helper both verbs call, preserving each verb's message prefix.
- Compare after the existing per-form payload resolution, so an evicted artifact
  reaches R5 rather than reporting a completed write.
- Derive the recorded round's digest from the fields that round already wrote; do
  not add a second digest field. One artifact keeps one canonical digest.
- Do not touch the recorded id on R1; it names the last round recorded under an
  id, which a flagless round does not become.

**Done when:** all six rows have passing cases and all five mutations flip.

### T3: the persisted schema carries, documents, and re-anchors the field

**Depends on:** T2

**Tests:**
- A pre-change `state.json` is read without error and each of the four forms
  applied to it with the flag exits 0 and writes the field (AC19).
- The bundled template carries the field with `null` (AC20).
- The shipped state-schema reference documents the field, the per-form derivation
  of the comparison digest, and the R3 and R4 outcomes (AC21).
- The template's exact-field-set check asserts the new set (AC22).

**Approach:**
- Add the reference row beside `last_record_attempt_cycle_id`, whose shape it
  mirrors, and state the derivation against `last_review_clean_digest` rather than
  duplicating it.
- Update `EXPECTED_STATE_KEYS` in `test_loop_cohort_cli.py`, the one anchor this
  change moves.

**Done when:** writer, template, reference, and the anchor check agree.

### T4: the shipped statements read the id after the transition and pass it

**Depends on:** T2

**Tests:**
- No command statement in `SKILL.md` or the skill's `references/` tree names the
  cohort script and the `review record` verb without `--operation-id`, where a
  statement extends through trailing-backslash continuations (AC23).
- A fixture naming the verb and a form flag but not the cohort script is not
  counted.
- Every recording statement reads its id after the transition entering the round,
  so a resuming session recomputes the same value (AC17).
- Each replay recipe in the resumption table passes the flag (AC18).
- The two prose tests and the adjudication contract test stay green.
- Mutation proof: removing the flag from one statement reddens the check.

**Approach:**
- The seven statements are `SKILL.md` (4), `references/finding-adjudication.md`
  (2), and `references/pre-execute-review.md` (1). The check's path set is rooted
  at `packs/core/.apm/skills/work-loop/`; the regenerated projections,
  `evals/evals.json`, and the script's own help text are out of scope and the
  check states all three exclusions.
- Four statements are `&&`-chained after a transition, so the id must be read
  after that transition rather than substituted into argv before it. Restructure
  those four onto a line following the transition, as the shipped
  `record-attempt` guidance already does.
- Append `--operation-id` after `--expect-run-id`. A shipped check asserts the
  order of `--fingerprint` and its placeholder, so inserting between them breaks
  it.
- Re-check the peer session's activity in the skill tree before editing.

**Done when:** the check passes over the stated paths, both anchor tests stay
green, and the mutation flips.

### T5: adopters can see what a matching id guarantees

**Depends on:** T2

**Tests:**
- The how-to names `--operation-id` and states that a repeat under a matching id
  leaves the round count unchanged (AC24); the core-pack explanation names the
  flag (AC25); the guides lint passes (AC26).

**Done when:** both guides describe shipped behavior and the lint is green.

### T6: the eval corpus covers the emitted command shape

**Depends on:** T4

**Tests:**
- The harness carries a case exercising the crash window of a recording that
  passes `--operation-id` (AC27).
- The two existing cases' expectations are byte-unchanged (AC28).
- The eval file parses and the pack's eval contract tests stay green.

**Approach:**
- Add one case; do not edit the two existing ones. The pack rule requiring a
  non-cosmetic pack update to update its eval harness is what makes the addition
  owed, and the retained replay policy is what keeps the existing expectations
  valid.

**Done when:** the corpus covers the emitted shape and the existing cases are
untouched.

### T7: a real re-issue records the round once

**Depends on:** T2, T3

**Tests:**
- Visual / manual QA: against a throwaway spec directory, record a round with an
  id, re-issue the identical command, and confirm `review_round_count` advanced
  exactly once. Record the counters, the recorded id, and each exit code at
  `notes/qa-transcript.md` (AC29), and state what the session does not exercise
  (AC30).

**Approach:**
- Exercise `--fingerprint` and `--all-skipped`; state that the two artifact-bearing
  forms and the R5 refusal are covered by unit cases only.
- Remove the throwaway directory afterwards and confirm `git status` is clean.

**Done when:** the transcript is committed and shows one increment.

### T8: the release surface is consistent

**Depends on:** T3, T5, T6, T7

**Tests:**
- A free-standing dated entry at `##` (AC31) with a `### Highlights` block
  (AC32); both version files read the same value, one patch above the base
  branch's (AC33); the drift gate reports no drift (AC34); the highlights
  projection matches the entry (AC35).

**Approach:**
- Re-read the base branch's changelog head and pack version immediately before
  writing, and rebase if the branch has fallen behind: an entry written at the top
  of a stale branch is not topmost after merging, and the highlights projection
  requires topmost.
- Regenerate the projections and the highlights projection rather than editing
  either.
- Run the gate chain with a clean build directory.
- Carry the governing decision's disposition to the approval gate: the primitive
  its revisit clause names now exists, and the policy it recorded is unchanged.

**Done when:** versions agree, the entry sits at top level, both projections are
regenerated, and the disposition is stated to the approver.

## Rollout

- **Delivery:** one PR. The flag is optional and the field defaults to `null`, so
  an existing persisted run keeps working unchanged. No shipped guidance changes
  meaning, because the replay policy is retained.
- **Reversibility:** reverting removes an optional flag, two `null`-defaulting
  fields, and one extracted helper. No persisted state becomes unreadable: the
  reader validates no key set, and the documented forward-field rejection is a
  fixed literal list that does not include either field.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** the version bump and changelog land in T8.

## Risks

- **The compatibility claim rests on a post-change assertion.** T1 captures the
  baseline before the writer is touched, as a per-form delta so the added template
  keys cannot invalidate it.
- **A distinct round is absorbed as a replay.** AC6 requires two ids to produce two
  increments, and the early-return mutation proof requires the matching-digest case
  to increment when the guard is removed.
- **A conflicting payload is silently accepted.** The digest comparison carries its
  own mutation proof, and the § Payload digest derivation table records what each
  form's digest is derived from.
- **A stale id outlives its round.** It cannot mislead: the recorded id is only ever compared against a freshly computed one, and AC16 pins the sequence.
- **An anchor check reddens unexpectedly.** The § Anchor obligations table names
  the one exact-set assertion this change moves and the three it does not.
- **The replay policy drifts.** A Constraint and a Never-do both forbid editing the
  surfaces that state it.
- **A peer worktree takes the version.** Re-checked against the base before commit.
- **A peer session is editing the same skill tree.** Re-checked before T5.
- **Concurrent gate runs void results.** Gates run serialized and never while a
  worker is editing.

## Open findings

- **Review has not returned clean.** Two lanes across two rounds produced 36 then
  13 findings. This draft applies all of them, plus the outcome table the second
  round asked for and two owner decisions taken afterwards, and has not been
  re-reviewed since. The spec-stage gate is unmet; approval should follow a clean
  round, not this note.
- **The replay-policy retention is stated in several places.** The Never-do rail,
  the Follow-on deferral, and the governing-decision disposition each need it; the
  remaining paraphrases are redundant and were left rather than risk another
  renumbering pass. Worth one consolidation before approval.

## Changelog

- 2026-08-31 — Carved out of a larger contract. Four review rounds across two
  earlier shapes produced 30, 43, 19 and 37 findings, with most attributed to the
  previous round's repairs; both reviewers independently identified this slice as
  independently shippable with no dependency on the projection verb.
- 2026-08-31 — Scope reduced on the owner's decision to ship the mechanism and
  retain the human-authorization obligation on a clean-round replay. That removed
  the resumption-row rewrite, its two pinned tests, the eval-harness edits, and
  the disposition of three `Status: Shipped` specs, because all of those surfaces
  state a policy this contract no longer changes.
- 2026-08-31 — The invocation predicate was wrong twice: first scoped to fenced
  code blocks, which missed three directives outside a fence; then defined
  per-line, which matched no real command at all, because every shipped invocation
  splits the verb from its form flag across a trailing-backslash continuation. It
  is now a command statement extending through continuations and requiring the
  cohort script's name, which excludes prose.
- 2026-08-31 — The digest was assumed to discriminate on all four forms. It does
  not: `--all-skipped`'s payload is constant and `--direct-clean-file`'s bytes are
  forced equal to the clean sentinel before hashing, so the id alone discriminates
  there. Recorded rather than papered over.
- 2026-08-31 — The baseline artifact was to record the resulting `state.json`. The
  template gains two keys, so every post-change run starts from a 29-key state and
  a whole-file equality against a 27-key capture could never pass. It records a
  per-form delta instead.
- 2026-08-31 — The version bump was minor. The closest precedent under the same
  rule — a released entry adding a new `review record` form plus two new persisted
  fields — was a patch, so this is a patch.
- 2026-08-31 — `EXPECTED_STATE_KEYS` asserts the bundled template's field set
  exactly and was missing from the affected-anchor inventory. The § Anchor
  obligations table now records it and the three anchors this change does not move.
- 2026-08-31 — Review round 2 found three blockers in one place: what the id is,
  when it is read, and when it is cleared. Resolved by writing the outcome table
  the reviewer asked for — six rows over recorded id, supplied id, and digest —
  and reducing the writer criteria to named rows. The stale-id clearing rule was
  dropped: it broke a legitimate replay after an intervening flagless round and
  contradicted the contract's own rule that omitting the flag changes nothing.
- 2026-08-31 — The id's read point was unspecified. Four shipped statements chain
  the recording after a transition with `&&`, so an id substituted into argv
  before the transition is one lower than the value a resuming session recomputes.
  T4 restructures those four and AC17 pins the read point.
- 2026-08-31 — The scope decision left the mechanism unwired: with the human gate
  retained, the resumption table's replay recipes carried no `--operation-id`, so
  an authorized replay would still have gone down the flagless path. AC18 requires
  the recipes to pass it, and the Ask-first rail was narrowed to permit exactly
  that edit while still forbidding any weakening of what the rows oblige.
- 2026-08-31 — Rebased onto the current base. The branch had fallen 13 commits
  behind during authoring and the core pack had moved 2.17.1 to 2.17.2 on main,
  which would have made the changelog entry non-topmost. All line citations were
  re-verified after the rebase; the seven command-statement sites and every
  `loop-cohort.py` anchor still hold.
- 2026-08-31 — A second content anchor was found and added: the adjudication
  contract test pins `--fingerprint <validated-adjudication-sha256>` and asserts
  token order, so `--operation-id` must be appended after `--expect-run-id` rather
  than inserted between a form flag and its placeholder.
- 2026-08-31 — The payload digest is derived rather than stored, on the owner's
  decision. `state.json` already carries everything needed to recompute it, and a
  second stored digest would give the same report bytes two canonical values that
  can drift. One new field instead of two.
- 2026-08-31 — One eval case is added for the id-carrying crash window, on the
  owner's decision. The corpus otherwise models a flagless command the skill no
  longer emits, and the pack rule requires a non-cosmetic pack update to update
  its eval harness. The two existing cases' expectations stay frozen.
- 2026-08-31 — Two review findings were carried unaddressed and unrecorded, and
  are now fixed: a claim that a documented forward-field rejection list exists
  (it does not — the only forward check is on `schema_version`), and a citation of
  `NON_IMPACTING_PREFIXES` for `guides/`, which that tuple does not contain. The
  conclusion held in both cases; the stated reasons did not.
