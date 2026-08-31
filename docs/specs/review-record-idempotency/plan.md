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
- The replay policy is retained, so no edit may weaken what a resumption row or an
  existing eval case obliges, and the seven phrases the two pinned row tests
  require all stay present. Adding `--operation-id` to a replay recipe, qualifying
  a row's audit-risk sentence, and adding one eval case are in scope.
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

## Payload digest preimage

The digest is computed at record time and stored. The preimage is the form's
literal name, then `\n`, then the form's payload bytes; the digest is `sha256`
over its UTF-8 encoding. The literal prefix is what stops two forms colliding.

| Form | Literal | Payload bytes |
| --- | --- | --- |
| `--fingerprint` | `fingerprint` | the sorted, deduplicated fingerprint list joined by `\n` |
| `--direct-clean-file` | `direct-clean` | the lowercase hex sha256 of the artifact's bytes |
| `--report --adjudication` | `report` | the lowercase hex sha256 of the report's bytes |
| `--all-skipped` | `all-skipped` | the empty string |

The writer already sorts and deduplicates fingerprints at `loop-cohort.py:1939`,
which makes a re-ordered or repeated finding set one payload. A report that
becomes unreadable between classification and hashing yields no digest
(`loop-cohort.py:2011-2016`); that round is refused rather than recorded, which is
what keeps every recorded id paired with a digest.

## Anchor obligations

Content-anchor checks that this change moves, and the task that owns each. Each
was located by a sweep over `packs/core/tests/`, `tests/`, and `tools/` for
assertions on the files this change touches.

| Anchor | Assertion | Owner |
| --- | --- | --- |
| `test_loop_cohort_cli.py` `EXPECTED_STATE_KEYS` | exact set equality on the bundled template | T4 |
| `test_loop_cohort.py` Phase-1 field check | subset, so unaffected | none |
| `fixtures/golden_cli_streams.json` | pins no `review record` output | none |
| `test_loop_engine.py` two prose tests | require seven phrases be *present* — three in the `findings-remain` row, four in the `reviewers-clean` row; adding a flag or a qualifying clause keeps them | T4 |
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
| Interface compatibility — the persisted schema | T3 | Field table and template carry both fields; the reference states the per-form digest preimage | Reference, template, and writer agree |
| Verification evidence — the QA transcript | T7 | Recorded counters, id, and exit codes | Transcript committed at `notes/qa-transcript.md` |
| User-facing promise — the two core guides | T6 | Both name the flag | Guides describe shipped behavior |
| Decision rationale — the governing decision's disposition | T8 | The Assumptions statement carried to the approval gate | Approver accepts or directs a superseding record |
| Release history — the changelog | T8 | Free-standing dated entry with `### Highlights` | Entry at top level; highlights projection regenerated |
| Reusable learning | T8 | `project-knowledge` receipt or recorded unavailability | Receipt recorded or unavailability named |

## Design (LLD)

### Design decisions

- The flag is optional and attaches outside the existing mutually exclusive group,
  so it composes with all four forms without touching them.
- The id, the digest, and the counters are written in one atomic write, so no
  observable state has one set without the others.
- A flagless recording leaves the recorded id alone. The field names the last
  round recorded under an id, and a resuming session only ever compares it against
  a freshly computed id, so a non-matching value correctly reads as "not
  recorded".
- The AC4 path prints a distinguishing line and the AC5 path a distinguishing
  reason, following the precedent's `(idempotent no-op)` line, because one exit
  code cannot separate three outcomes.

### Data & schema

Two fields, `last_review_record_operation_id` and
`last_review_record_payload_digest`, both defaulting to `null` and absent-tolerant
on read, so a `state.json` written before this change reads as "no id-recorded
round is current". The digest is stored rather than derived because the next round
overwrites the inputs a derivation would need.

### Interfaces & contracts

No payload contract changes. The CLI gains one optional flag.

### Component / module decomposition

No new module and no new file: one flag, one early return, and two fields in
`cmd_review_record`. The `<run_id>:<digits>` form check is duplicated rather than
extracted, so `cmd_record_attempt` — shipped, Phase-1 idempotency — is not
touched.

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
  fields. This is AC12's comparison value.
- The artifact's commit precedes the commit that changes the writer (AC38),
  checkable with `git log`.

**Approach:**
- Record a per-form delta, not the resulting file: T3 adds two template keys, so a
  whole-file comparison could never pass afterwards.
- Normalise resolved paths, digests, and run-id UUIDs the way the existing golden
  support module does, so the comparison stays an equality.

**Done when:** the artifact is committed ahead of the writer and replaying the
capture against the unchanged writer reproduces it exactly.

### T2: the writer implements every row of the outcome table

**Depends on:** T1

**Tests:** one case per row, plus the cross-row properties.
- The flag is accepted alongside each of the four forms (AC1).
- R6 malformed id (AC2); R1/R2 same round delta for every digest-computable form
  (AC3); R3 replay (AC4); R4 conflict (AC5); R2 twice (AC6); R5 uncomputable
  digest (AC7).
- Re-ordered and duplicated fingerprints yield one digest (AC8); no two forms
  share a digest (AC9).
- R3's stdout line is distinct (AC10); R4, R5, and R6 stderr reasons are each
  distinct (AC11).
- The four flagless forms match the baseline and leave the pair alone (AC12).
- Both fields hold the recorded pair (AC13), are `null` beforehand (AC14), and are
  written in the same atomic write as the round delta (AC15).
- The R2-then-R1-then-repeat sequence resolves as R3 (AC16).
- Mutation proofs: removing the digest comparison makes R4 pass; removing the form
  check makes R6 pass; removing the early return makes R3 increment; removing the
  literal prefix from the preimage makes two forms collide; recording an id when
  the digest is uncomputable makes R5 pass.

**Approach:**
- Store the digest at record time. Do not derive it on read: the next round
  overwrites `finding_fingerprints` and no field records which form closed a
  round, so a derivation has nothing sound to read.
- Duplicate the `<run_id>:<digits>` form check rather than extracting it; the
  shipped `record-attempt` verb stays untouched.
- Do not touch the pair on R1.
- R5's only reachable trigger is the report becoming unreadable between
  `_classify_report`'s read and the re-read at `loop-cohort.py:2011-2016`. Induce
  it by replacing the report between the two reads. `--fingerprint` and
  `--all-skipped` always compute a digest, and `--direct-clean-file` refuses at
  `:1974-1978` before any digest logic, so neither exercises R5.

**Done when:** all six rows have passing cases and all five mutations flip.

### T3: the persisted schema carries, documents, and re-anchors both fields

**Depends on:** T2

**Tests:**
- A pre-change `state.json` is read without error and each of the four forms
  applied to it with the flag exits 0 and writes both fields (AC17).
- The bundled template carries both fields with `null` (AC18).
- The shipped state-schema reference documents both fields, the per-form digest
  preimage, and the R3 and R4 outcomes (AC19).
- The template's exact-field-set check asserts the new set (AC20).

**Approach:**
- Add the reference rows beside `last_record_attempt_cycle_id` and
  `last_review_clean_digest`, whose shapes they mirror.
- Update `EXPECTED_STATE_KEYS` in `test_loop_cohort_cli.py`, the one anchor this
  change moves. The template goes from 27 keys to 29.

**Done when:** writer, template, reference, and the anchor check agree.

### T4: the shipped statements and rows carry the flag without losing their guard

**Depends on:** T2

**Tests:**
- In every recording statement, the operation id comes from a read that executes
  after the transition, not from a value substituted beforehand (AC21).
- Every recording statement is conditional on its transition having succeeded
  (AC22).
- Each `review record` replay recipe passes the flag and names the id's source
  (AC23).
- The clean-replay row states that the double-increment risk applies to a replay
  without a matching id and keeps its four pinned phrases (AC24); the
  `findings-remain` row keeps its three (AC25).
- No command statement in `SKILL.md` or the skill's `references/` tree omits the
  flag, where a statement extends through trailing-backslash continuations
  (AC26).
- A fixture naming the verb and a form flag but not the cohort script is not
  counted.
- Both pinned row tests and the adjudication contract test stay green.
- Mutation proofs: removing the flag from one statement reddens AC26's check;
  making one recording unconditional on its transition reddens AC22's check;
  substituting a literal sequence before the transition reddens AC21's check.

**Approach:**
- Eight sites: the seven command statements — `SKILL.md` (4),
  `references/finding-adjudication.md` (2), `references/pre-execute-review.md`
  (1) — plus the `review record` replay recipes in
  `references/session-resumption.md`.
- The transition already prints its new sequence on its success line
  (`loop-engine.py:1508-1511`), so the id's source is that output. Four statements
  are `&&`-chained today; either keep the chain and resolve the sequence inside it
  with a command substitution, or split the statement and state the
  transition-succeeded precondition explicitly, as the shipped `record-attempt`
  guidance does. Both satisfy AC21 and AC22; pick one and use it at all four.
- Append `--operation-id` after `--expect-run-id`. A shipped check asserts the
  order of `--fingerprint` and its placeholder, so inserting between them breaks
  it.
- The check's path set is rooted at `packs/core/.apm/skills/work-loop/`; the
  regenerated projections, `evals/evals.json`, and the script's own help text are
  out of scope and the check states all three exclusions.
- Re-check the peer session's activity in the skill tree before editing.

**Done when:** all six checks pass, the anchor tests stay green, and the three
mutations flip.

### T5: adopters can see what a matching id guarantees

**Depends on:** T2

**Tests:**
- The how-to names `--operation-id` and states that a repeat under a matching id
  leaves the round count unchanged (AC27); the core-pack explanation names the
  flag (AC28); the guides lint stays green.

**Done when:** both guides describe shipped behavior and the lint is green.

### T6: the eval corpus covers the emitted command shape

**Depends on:** T4

**Tests:**
- The harness carries a case exercising the crash window of a recording that
  passes `--operation-id` (AC29).
- The expectations of `phase1-surface-ambiguous-review-record` and
  `phase1-explicit-auth-clean-record-replay` are byte-unchanged (AC30).
- The eval file parses and the pack's eval contract tests stay green.

**Approach:**
- Add one case; do not edit those two. The new case's id must not start with
  `cognitive-load-`, which a repository-contract filter keys on.

**Done when:** the corpus covers the emitted shape and the two named cases are
untouched.

### T7: a real re-issue records the round once

**Depends on:** T2, T3

**Tests:**
- Visual / manual QA: against a throwaway spec directory, record a round with an
  id, re-issue the identical command, and confirm `review_round_count` advanced
  exactly once. Record the counters, the recorded id, and each exit code at
  `notes/qa-transcript.md` (AC31), and state what the session does not exercise
  (AC32).

**Approach:**
- Exercise `--fingerprint` and `--all-skipped`; state that the two artifact-bearing
  forms and the R5 refusal are covered by unit cases only.
- Remove the throwaway directory afterwards and confirm `git status` is clean.

**Done when:** the transcript is committed and shows one increment.

### T8: the release surface is consistent

**Depends on:** T3, T4, T5, T6, T7

**Tests:**
- A free-standing dated entry at `##` (AC33) with a `### Highlights` block
  (AC34); both version files read the same value, one patch above the base
  branch's (AC35); the drift gate reports no drift (AC36); the highlights
  projection matches the entry (AC37).

**Approach:**
- Re-read the base branch's changelog head and pack version immediately before
  writing, and rebase if the branch has fallen behind.
- Regenerate the projections and the highlights projection rather than editing
  either.
- Run the gate chain with a clean build directory.
- Carry the governing decision's disposition to the approval gate.

**Done when:** versions agree, the entry sits at top level, both projections are
regenerated, and the disposition is stated to the approver.

## Rollout

- **Delivery:** one PR. The flag is optional and both fields default to `null`, so
  an existing persisted run keeps working unchanged. Shipped guidance gains the
  flag and one qualifying clause; what the rows oblige is unchanged.
- **Reversibility:** reverting removes an optional flag and two `null`-defaulting
  fields. No persisted state becomes unreadable: the
  reader validates no key set and the only forward check is on `schema_version`,
  so an added field is not rejected.
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
  own mutation proof, and the § Payload digest preimage table fixes what each form
  hashes.
- **A stale pair outlives its round.** It cannot mislead: the pair records the
  earlier round's payload rather than describing current state, and AC16 pins the
  sequence that would otherwise break.
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
- **The per-form digest preimage is stated in three places** — this plan's table,
  the spec's § Payload digest, and the shipped state-schema reference AC19
  requires. The plan's table is canonical; the other two should point at it rather
  than restate it.
- **The flagless baseline artifact may duplicate existing coverage.**
  `test_loop_cohort_cli.py` already pins per-form exit codes and counter deltas;
  the only dimension it misses is the stdout line. Adding those four assertions to
  the existing tests would remove T1, its artifact, and its normalization harness.
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
  T4 restructures those four and a criterion pins the read point.
- 2026-08-31 — The scope decision left the mechanism unwired: with the human gate
  retained, the resumption table's replay recipes carried no `--operation-id`, so
  an authorized replay would still have gone down the flagless path. A criterion
  now requires the recipes to pass it, and the Ask-first rail was narrowed to permit exactly
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
- 2026-08-31 — The digest was briefly changed to derive-on-read and then reverted
  to stored. Derivation is unsound here: the fingerprint and all-skipped branches
  overwrite `finding_fingerprints` and never touch `last_review_clean_source`, and
  no field records which form closed a round, so `state.json` stops describing a
  round's payload as soon as the next round lands. Storing the digest captures it
  at the only moment it is knowable.
- 2026-08-31 — One eval case is added for the id-carrying crash window, on the
  owner's decision. The corpus otherwise models a flagless command the skill no
  longer emits, and the pack rule requires a non-cosmetic pack update to update
  its eval harness. The two existing cases' expectations stay frozen.
- 2026-08-31 — Two review findings were carried unaddressed and unrecorded, and
  are now fixed: a claim that a documented forward-field rejection list exists
  (it does not — the only forward check is on `schema_version`), and a citation of
  `NON_IMPACTING_PREFIXES` for `guides/`, which that tuple does not contain. The
  conclusion held in both cases; the stated reasons did not.
