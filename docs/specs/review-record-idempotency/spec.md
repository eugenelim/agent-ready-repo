# Spec: review-record-idempotency

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0061
- **Brief:** none
- **Discovery:** none
- **Contract:** none — no interface payload changes; the CLI gains one optional flag
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

`loop-cohort review record` accepts an `--operation-id` naming the round it
records, persists that id with a digest of the payload recorded under it, and
treats a repeat of the same id carrying the same payload as a completed write
rather than a new round. A repeat carrying a different payload under that id is
refused.

A maintainer reading `state.json` can see which round the counters belong to. An
agent that re-issues a recording after losing its own record of whether the write
landed gets one write, not two. The record is a decision aid for a session
resuming inside that round, not a durable audit log: once the run takes its next
transition, the recorded id names a round the loop has already moved past.

The existing human-authorization obligation on a clean-round replay is unchanged.
This contract supplies the mechanism that makes such a replay safe; it does not
change who may authorize one. A caller that omits the flag observes the same
behavior as before.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | Applicable — the writer, the bundled state template, and the shipped invocations change | `packs/core/.apm/skills/work-loop/**` and its regenerated projections | Repository maintainer | `make build-self-dry-run` reports no drift | Source edited, projections regenerated, drift gate clean |
| Interface compatibility | Applicable — `state.json` is a persisted schema two tools read | The shipped state-schema reference and `assets/state.json` | Repository maintainer | Field table and template carry both fields, and the reference states the digest's per-form preimage | Reference, template, and writer agree |
| Verification evidence | Applicable — the flagless-baseline comparison must exist independently of the change | `docs/specs/review-record-idempotency/notes/flagless-baseline.json` | Implementing agent | Per-form state delta and stdout line, captured before the writer changes | Artifact committed before the writer's commit |
| Verification evidence | Applicable — the re-issue sequence is only observable by running it | `docs/specs/review-record-idempotency/notes/qa-transcript.md` | Implementing agent | Recorded counters, the recorded id, and per-command exit codes | Transcript committed at that path |
| User-facing promise | Applicable — adopters drive this command by hand | `guides/core/how-to/plan-and-execute-non-trivial-work.md`, `guides/core/explanation/core-pack.md` | Repository maintainer | Both surfaces name the flag and what a matching id guarantees | Guides describe shipped behavior |
| Release history | Applicable — a new flag and two persisted fields are user-visible | `docs/product/changelog.md` free-standing dated entry with a `### Highlights` block | Repository maintainer | Entry at top level, not nested under `[Unreleased]` | Entry present at `##`, highlights projection regenerated |
| Decision rationale | Applicable — this lands the primitive a governing decision named as its revisit trigger while deliberately leaving that decision's policy intact | The governing decision's disposition, recorded in this spec's Assumptions and carried to the approval gate | Repository maintainer | An explicit statement of what the trigger does and does not change | The approver accepts the disposition or directs a superseding record |
| Operations | Applicable — the pack's eval corpus must cover the command shape the skill emits | `packs/core/.apm/skills/work-loop/evals/evals.json` | Repository maintainer | One added case for the id-carrying crash window; existing expectations unchanged | Corpus covers the emitted shape |
| Reusable learning | Applicable — the id-plus-digest decidability pattern generalises | Routed through `project-knowledge` at the loop's capture gates | Implementing agent | Capture receipt, or a recorded `project-knowledge unavailable` | Receipt recorded or unavailability named |
| Current architecture | Not applicable — no entrypoint, ownership, or state-authority boundary changes | — | — | — | — |
| Maintainer procedure | Not applicable — no maintainer runbook changes | — | — | — | — |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit `packs/core/.apm/skills/work-loop/**` as the source and regenerate the
  adapter skill trees with `make build-self`.
- Capture the flagless baseline as a committed artifact before changing the
  writer, so the compatibility comparison value exists independently of the
  change.
- Keep each execution wave green and shippable on its own.

### Ask first

- Changing an existing exit code, output line, or flag on any `loop-cohort` verb.
- Adding a field to `state.json` beyond the two this spec names.
- Editing any file under `packages/agentbundle/`, which a protected-tree gate
  covers.
- Removing or reordering any of the seven phrases the two pinned resumption-row
  tests require — three in the `findings-remain` row, four in the
  `reviewers-clean` row — or changing an existing eval case's expectations. Adding
  `--operation-id` to a replay recipe, qualifying a row's audit-risk sentence, and
  adding one eval case are all in scope and required; weakening what a row or an
  existing case obliges is not.

### Never do

- Add a third work-loop CLI, a new module boundary, or a new top-level directory.
- Add a runtime dependency to any shipped pack script.
- Introduce a reader of `engine-state.json` inside `loop-cohort.py`; the caller
  supplies the id and the writer validates its form.
- Make `--operation-id` required, or change behavior for a caller that omits it.
- Let a recording run after a refused transition. The transition carries the
  retry-cap guard and the recording does not, so the conditionality must survive
  however the statement is shaped.
- Retire, weaken, or bypass the existing human-authorization obligation on a
  clean-round replay.
- Edit the body of an accepted decision record or of a spec at `Status: Shipped`.
- Insert `--operation-id` between a form flag and its value placeholder in shipped
  content; append it after `--expect-run-id`, because a shipped check asserts the
  order of those tokens.
- Put a repository-only path, `ADR-NNNN`, or `RFC-NNNN` token into `packs/**` or
  `guides/**` content.
- Hand-edit a generated projection.

## Testing Strategy

Each behavior names its mode; the plan names the suite and the mutation that must
kill each check.

- **Replay, conflict refusal, id-form refusal, and the never-undecidable
  guarantee: TDD.** Each is an exact before-and-after assertion over `state.json`,
  mirroring the existing crash-window tests for the recorded implementation
  attempt.
- **Unchanged behavior for a caller that omits the flag: goal-based check**
  against a baseline captured before the writer changes, because the comparison
  value must exist independently of the change.
- **Unchanged existing per-form validation: TDD**, reusing the shipped cases that
  already pin each form's refusals.
- **Tolerance of a pre-change `state.json`: TDD**, because it is a concrete input
  with one correct reading.
- **The bundled template, its pinned anchor, and the state-schema reference:
  goal-based check**, a parse and a grep.
- **The shipped instructions and resumption guidance: goal-based check** over an
  enumerated site list, covering the id's recomputability, the transition guard,
  and the pinned obligations.
- **The eval corpus: goal-based check**, a parse plus an id lookup.
- **The adopter guides: goal-based check**, one grep each.
- **The command as a user runs it: visual / manual QA.** This is a CLI a user
  invokes, and a green unit suite does not establish that the assembled sequence
  behaves.
- **The release surface: goal-based check**, one command per member.

## Acceptance Criteria

**Operation id.** An operation id is `<run_id>:<transition_sequence>`, read after
the transition that entered the round being recorded. The caller supplies it, the
same division the shipped instructions already use for a recorded implementation
attempt; `loop-cohort` validates its form and never reads engine state.

The plan carries the mechanism these outcomes are met by — the per-form digest
preimage, the field names, the exit codes, and the case table the writer
implements. Where a criterion below does not fix a detail, the build chooses it
and the plan's mutation proofs keep the choice honest.

### Behavior

- [ ] **AC1.** A recording re-issued with the same operation id and the same
  payload leaves every review counter, fingerprint list, and clean-round
  provenance field exactly as the first application left them, and says the round
  was already recorded.
- [ ] **AC2.** A recording presented with a recorded operation id and a different
  payload is refused, and `state.json` is byte-identical to its state before the
  attempt.
- [ ] **AC3.** Recordings under different operation ids each count as a distinct
  review round.
- [ ] **AC4.** A recording that omits `--operation-id` produces the same
  observable result as it does today, for each of the four recording forms,
  measured against a baseline captured before the writer changes.
- [ ] **AC5.** A malformed operation id is refused with `state.json` unchanged.
- [ ] **AC6.** No round is recorded under an operation id unless a comparison
  value for a later repeat is recorded with it, so a repeat is never undecidable.
- [ ] **AC7.** An operator can tell the refusal outcomes apart — a payload
  conflict, a missing comparison value, and a malformed id — from the command's
  output alone.
- [ ] **AC8.** Each recording form's existing payload validation is unchanged:
  what refuses today still refuses, with the same result.

### Persisted state

- [ ] **AC9.** `state.json` records which round the counters belong to, and a
  session resuming before the run's next transition judges a repeat of that round
  correctly from it.
- [ ] **AC10.** A `state.json` written before this change is read without error
  and every recording form operates on it.
- [ ] **AC11.** The shipped state-schema reference and the bundled template
  describe the recorded state accurately, including how a repeat is judged.
- [ ] **AC12.** Every shipped check that pins the template's field set matches the
  shipped template.

### Shipped surfaces

- [ ] **AC13.** Every shipped recording instruction supplies an operation id that
  a session resuming at that point recomputes identically.
- [ ] **AC14.** A refused transition never reaches a recording.
- [ ] **AC15.** The shipped resumption guidance says when a replay is safe and
  when it is not, and every obligation its pinned tests require is intact.
- [ ] **AC16.** The pack's eval corpus exercises the command shape the skill
  emits, and the expectations of its two existing crash-window cases are
  unchanged.
- [ ] **AC17.** An adopter reading the core guides can find what the flag
  guarantees.

### Release

- [ ] **AC18.** The release surface is consistent: a dated free-standing changelog
  entry carrying a highlights block, both version files reading one patch above
  the base branch, and no projection drift.

## Follow-ons

- Repository maintainer: retiring the human-authorization obligation on a
  clean-round replay is a separate decision, owed its own record, and is
  deliberately excluded here. The obligation stays in force; this contract only
  makes the replay it guards mechanically safe.
- Repository maintainer: `docs/specs/work-loop-next-projection/` — a
  `loop-engine next --json` projection that would read the recorded id to decide a
  resuming session's next action. Drafted, not approved: four review rounds
  established that its routing contract needs expressing as a total
  state-to-action table rather than as prose criteria. This spec is a prerequisite
  and delivers standalone value without it.

## Assumptions

- Technical: id-keyed idempotency already works in this file — `record-attempt`
  no-ops on a repeated cycle id and validates its `<run_id>:<digits>` form
  against `--expect-run-id` (source:
  `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py:1552-1575`)
- Technical: a payload digest is needed beyond the id, because `record-attempt`'s
  payload *is* its id while a review round's payload varies across four forms
  (source: `loop-cohort.py:1912-2035` shows four distinct payload shapes)
- Technical: the digest is degenerate for two forms and useful for two. For
  `--all-skipped` the payload is constant, and for `--direct-clean-file` the raw
  bytes must equal the clean sentinel before they are hashed, so neither form can
  present a conflicting payload under a reused id; the id alone discriminates
  there. The digest earns its place on `--fingerprint` and
  `--report --adjudication`, whose payloads vary (source: `loop-cohort.py:1981`
  forces byte equality with the sentinel before `:1986` hashes it)
- Technical: an unreadable clean artifact is refused before the state comparison
  today, which is why a repeat whose artifact is gone refuses rather than
  reporting a completed write; the artifacts live under a gitignored session path,
  so this is reachable on a resume (source: `loop-cohort.py:1971-1978`;
  `.gitignore:88`)
- Technical: `--operation-id` composes with all four existing forms because it
  attaches outside the mutually exclusive group, and `review record` already
  requires `--expect-run-id`, so validating the id's form introduces no read of
  `engine-state.json` (source: `loop-cohort.py:2224-2257`)
- Technical: `loop-cohort.py` reads `engine-state.json` nowhere today, which is
  why the caller supplies the id — the same division the shipped instructions
  already use for a recorded implementation attempt, where the agent reads
  `transition_sequence` from `loop-engine status` (source: `loop-cohort.py`
  contains `engine-state` only in one comment)
- Technical: a caller-supplied id with a separately recorded digest is chosen over
  deriving the id from the payload digest, because a resuming session must be able
  to reconstruct the id from state it can still read, and a payload-derived id
  cannot be reconstructed once the payload is gone. A derived-id precedent exists
  elsewhere in the catalogue for a case where the payload is always available
  (source: `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`
  pairs an operation id with an operation digest and derives the id from it)
- Technical: `state.json` already carries two adjacent precedents for the field
  shapes — `last_record_attempt_cycle_id` for an id and `last_review_clean_digest`
  for a digest — both defaulting to `null` (source:
  `packs/core/.apm/skills/work-loop/assets/state.json`, 27 fields, becoming 29)
- Technical: the digest must be stored rather than derived on read, because
  `state.json` stops describing a round's payload as soon as the next round lands:
  the fingerprint and all-skipped branches each overwrite `finding_fingerprints`
  and return without touching `last_review_clean_source` or
  `last_review_clean_digest`, which are written only in the clean branch and are
  therefore stale after any other form. No field records which form closed a
  round, so a read-time derivation cannot select its own rule (source:
  `loop-cohort.py:1925-1935`, `:1937-1950`, `:2024-2025`)
- Technical: the transition increments `transition_sequence`, and four shipped
  statements chain the recording to that transition with `&&`, so an id
  substituted before the transition is one lower than the value a resuming session
  recomputes; the chain must be preserved because the transition carries the
  retry-cap guard and the recording does not (source: `loop-engine.py:1421`
  computes `new_seq`; `SKILL.md:615-616` states the guard; `:617-619` chains)
- Technical: adding an eval case trips no contract test — the case-count check is
  a floor and every other consumer indexes by id (source:
  `test_loop_engine.py:2219`)
- Technical: one shipped check asserts the bundled template's exact field set, so
  adding fields to the template requires updating it. The reader validates no key
  set at all, and the only forward check is on `schema_version`, so an added field
  is not itself rejected (source:
  `packs/core/tests/skills/work-loop/test_loop_cohort_cli.py:245` asserts
  `set(template) == EXPECTED_STATE_KEYS`; `_loop_guards.read_state` delegates to
  `read_managed_json` with no key validation)
- Technical: every runnable `review record` command in the shipped skill splits
  the verb from its form flag across a trailing-backslash continuation, which is
  why a command statement is defined across continuations rather than per line; a
  per-line rule matches only prose (source: `SKILL.md:563-564`, `:567-568`,
  `:571-572`, `:618-619`; `references/finding-adjudication.md:168-169`,
  `:264-265`; `references/pre-execute-review.md:141-142`)
- Technical: new tests under `packs/core/tests/skills/work-loop/` run in
  `make test`, which names that directory, so no CI wiring is added (source:
  `Makefile:544`)
- Process: the governing decision that deferred idempotency keys names this change
  as its revisit trigger and records the Phase-1 non-idempotency as an accepted
  tradeoff. This contract lands the primitive and leaves the policy intact: the
  human-authorization obligation on a clean-round replay stays in force, the
  shipped resumption rows keep stating it, and no accepted record or shipped spec
  body is edited. Whether the tradeoff's mechanical half now warrants a
  superseding record is carried to the approval gate as an open decision rather
  than resolved here (source: `docs/adr/0061-loop-infrastructure-phase-1.md:12-13`;
  `docs/specs/loop-infrastructure-phase-1/spec.md:34`)
- Process: no RFC is owed. Nothing published is withdrawn — the authorization
  obligation is retained, not retired — so the reserved list's withdrawal clause
  does not fire (source: `docs/CONVENTIONS.md:338-349`)
- Process: editing any file under `packages/agentbundle/` outside `build/recipes/`
  or a `tests/` path trips a protected-tree gate requiring an engine-scoped RFC
  trailer, so no task here edits that tree (source:
  `tools/lint-catalogue-curation-guard.py`; the gate runs at
  `tools/repo/build_gate_chain.py:305`)
- Process: no release indicator beyond the changelog is required, because no path
  this change touches matches a release-impacting prefix; `contracts/` is the
  prefix that would have required one, and this change does not touch it (source:
  `tools/repo/check_release_impact.py` `is_release_impacting` returns False for
  `guides/`, `packs/`, and `docs/` paths)
- Process: the core pack bumps patch rather than minor, because the closest
  precedent under the same rule — a released entry adding a new `review record`
  form together with two new persisted `state.json` fields — was a patch, and the
  rule reserves minor for a new pack primitive (source:
  `docs/product/changelog.md` records `[core][2.17.1]` for that change;
  `packs/AGENTS.md:44-46`)
- Process: shipped pack content and adopter guides state rules directly and cite
  no repository-only path (source: `packs/AGENTS.md:49-52`,
  `tools/lint-guides-no-repo-only-refs.py`)
- Process: the changelog entry is free-standing at `##` and never nested under
  `[Unreleased]`, or the highlights projection never sees it (source:
  `docs/product/changelog.md:11-19`)
- Process: `packs/core/.apm/**` is the source and the adapter skill trees are
  regenerated projections, byte-identical to source today (source:
  `Makefile:67-78`, `diff -q` between source and the Claude projection)
- Product: this contract delivers a mechanism and a persisted record, not a change
  to who may authorize a replay (source: user confirmation 2026-08-31)
