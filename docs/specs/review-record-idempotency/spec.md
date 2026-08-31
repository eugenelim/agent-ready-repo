# Spec: review-record-idempotency

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
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
landed gets one write, not two.

The existing human-authorization obligation on a clean-round replay is unchanged.
This contract supplies the mechanism that makes such a replay safe; it does not
change who may authorize one. A caller that omits the flag observes the same
behavior as before.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | Applicable — the writer, the bundled state template, and the shipped invocations change | `packs/core/.apm/skills/work-loop/**` and its regenerated projections | Repository maintainer | `make build-self-dry-run` reports no drift | Source edited, projections regenerated, drift gate clean |
| Interface compatibility | Applicable — `state.json` is a persisted schema two tools read | The shipped state-schema reference and `assets/state.json` | Repository maintainer | Field table and template carry both fields with their derivation | Reference, template, and writer agree |
| Verification evidence | Applicable — the flagless-baseline comparison must exist independently of the change | `docs/specs/review-record-idempotency/notes/flagless-baseline.json` | Implementing agent | Per-form state delta and stdout line, captured before the writer changes | Artifact committed before the writer's commit |
| Verification evidence | Applicable — the re-issue sequence is only observable by running it | `docs/specs/review-record-idempotency/notes/qa-transcript.md` | Implementing agent | Recorded counters, the recorded id, and per-command exit codes | Transcript committed at that path |
| User-facing promise | Applicable — adopters drive this command by hand | `guides/core/how-to/plan-and-execute-non-trivial-work.md`, `guides/core/explanation/core-pack.md` | Repository maintainer | Both surfaces name the flag and what a matching id guarantees | Guides describe shipped behavior |
| Release history | Applicable — a new flag and two persisted fields are user-visible | `docs/product/changelog.md` free-standing dated entry with a `### Highlights` block | Repository maintainer | Entry at top level, not nested under `[Unreleased]` | Entry present at `##`, highlights projection regenerated |
| Decision rationale | Applicable — this lands the primitive a governing decision named as its revisit trigger while deliberately leaving that decision's policy intact | The governing decision's disposition, recorded in this spec's Assumptions and carried to the approval gate | Repository maintainer | An explicit statement of what the trigger does and does not change | The approver accepts the disposition or directs a superseding record |
| Reusable learning | Applicable — the id-plus-digest decidability pattern generalises | Routed through `project-knowledge` at the loop's capture gates | Implementing agent | Capture receipt, or a recorded `project-knowledge unavailable` | Receipt recorded or unavailability named |
| Operations | Not applicable — no deployed runtime, endpoint, or on-call surface changes | — | — | — | — |
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
- Changing the shipped resumption table's routing prose, its pinned tests, or the
  pack's eval expectations; this contract leaves the replay policy alone and
  those surfaces state it.

### Never do

- Add a third work-loop CLI, a new module boundary, or a new top-level directory.
- Add a runtime dependency to any shipped pack script.
- Introduce a reader of `engine-state.json` inside `loop-cohort.py`; the caller
  supplies the id and the writer validates its form.
- Make `--operation-id` required, or change behavior for a caller that omits it.
- Retire, weaken, or bypass the existing human-authorization obligation on a
  clean-round replay.
- Edit the body of an accepted decision record or of a spec at `Status: Shipped`.
- Put a repository-only path, `ADR-NNNN`, or `RFC-NNNN` token into `packs/**` or
  `guides/**` content.
- Hand-edit a generated projection.

## Testing Strategy

- **Replay, conflict refusal, and id-form refusal: TDD.** Each is an exact
  before-and-after assertion over named `state.json` fields, mirroring the
  existing crash-window tests for the recorded implementation attempt.
- **Flagless compatibility: goal-based check** against a baseline artifact
  captured before the writer changes, because the comparison value must exist
  independently of the change.
- **Absent-field tolerance: TDD**, because a pre-change `state.json` is a concrete
  input with one correct reading.
- **The bundled template and the state-schema reference: goal-based check**, a
  parse and a grep.
- **The shipped invocations: goal-based check** over an enumerated site list.
- **The two adopter guides: goal-based check**, one grep each for the flag name.
- **The command as a user runs it: visual / manual QA.** Re-issue a recording
  against a throwaway spec directory and record the observed counters and exit
  codes. This is a CLI a user invokes, and a green unit suite does not establish
  that the assembled sequence behaves.
- **Projection drift and release consistency: goal-based check**, one command
  each.

## Acceptance Criteria

**Operation id.** An operation id is `<run_id>:<transition_sequence>`, the pair
the caller reads from `loop-engine status` — the same value and the same division
of labour the shipped instructions already use for a recorded implementation
attempt. `loop-cohort` validates the form and never reads engine state.

### The writer

- [ ] **AC1.** `review record --operation-id <id>` is accepted alongside each of
  the four existing recording forms: `--fingerprint`, `--direct-clean-file`,
  `--report --adjudication`, and `--all-skipped`.
- [ ] **AC2.** `review record --operation-id <id>` exits non-zero and changes no
  field of `state.json` when `<id>` does not match
  `<expect-run-id>:<decimal-sequence>`.
- [ ] **AC3.** A first application carrying `--operation-id` produces, for each of
  the four forms, the same delta over `review_round_count`,
  `review_retry_count`, `finding_fingerprints`,
  `previous_finding_fingerprints`, `last_review_clean_source`, and
  `last_review_clean_digest` as the same form without the flag.
- [ ] **AC4.** A repeat carrying the recorded id and a payload whose digest
  matches the recorded digest exits 0 and leaves those six fields unchanged from
  the first application.
- [ ] **AC5.** A repeat carrying the recorded id and a payload whose digest
  differs from the recorded digest exits non-zero and leaves `state.json`
  byte-identical to its state before the attempt.
- [ ] **AC6.** Two applications carrying different operation ids each increment
  `review_round_count`.
- [ ] **AC7.** A repeat carrying the recorded id whose payload digest cannot be
  computed, because the artifact a clean form names is unreadable, exits non-zero
  and leaves `state.json` byte-identical.
- [ ] **AC8.** Re-ordering or duplicating the fingerprints supplied to
  `--fingerprint` yields the same digest, so the same finding set under the same
  id is one payload.
- [ ] **AC9.** Two different recording forms never produce the same digest.
- [ ] **AC10.** The stdout line on the AC4 path states that the round was already
  recorded, distinctly from the line a first application prints.
- [ ] **AC11.** The stderr reason on the AC5 path states that a different payload
  was recorded under that id, distinctly from the AC2 reason.
- [ ] **AC12.** `review record` invoked without `--operation-id` produces, for
  each of the four forms, the per-form state delta and the stdout line recorded in
  the committed flagless baseline artifact.

### The persisted schema

- [ ] **AC13.** `state.json` carries `last_review_record_operation_id`, holding
  the id of the round most recently recorded under an id.
- [ ] **AC14.** `state.json` carries `last_review_record_payload_digest`, holding
  the digest of the payload recorded under that id.
- [ ] **AC15.** A recording that carries no `--operation-id` sets both fields to
  `null`, so the pair never names a round other than the most recent.
- [ ] **AC16.** Both fields hold `null` before any round is recorded under an id,
  and a `null` in `last_review_record_operation_id` means no id-recorded round is
  current rather than that a digest was uncomputable.
- [ ] **AC17.** A `state.json` written before this change, carrying neither field,
  is read without error, and each of the four forms applied to it exits 0 and
  writes both fields.
- [ ] **AC18.** `packs/core/.apm/skills/work-loop/assets/state.json` carries both
  fields with a `null` value.
- [ ] **AC19.** The shipped state-schema reference documents both fields, the
  digest's derivation per recording form, and that a repeated id with a matching
  digest is a completed write while a repeated id with a differing digest is
  refused.
- [ ] **AC20.** Every shipped check that asserts the bundled template's exact
  field set asserts the field set including both new fields.

### The shipped invocations and guides

- [ ] **AC21.** Every `review record` command statement in `SKILL.md` and in the
  skill's `references/` tree passes `--operation-id`. A command statement is a
  line naming the cohort script together with the `review record` verb, extended
  through any trailing-backslash continuations. A mention that does not name the
  cohort script is prose, not a command statement.
- [ ] **AC22.** `guides/core/how-to/plan-and-execute-non-trivial-work.md` names
  `--operation-id` and states that a repeat under a matching id leaves the round
  count unchanged.
- [ ] **AC23.** `guides/core/explanation/core-pack.md` names `--operation-id`.
- [ ] **AC24.** No file under `guides/**` gains a repository-only path,
  `ADR-NNNN` token, or `RFC-NNNN` token.

### The release surface

- [ ] **AC25.** Re-issuing a recording with the same id against a throwaway spec
  directory advances `review_round_count` exactly once, with the observed
  counters, the recorded id, and each command's exit code captured at the
  destination the Durable Outputs table names.
- [ ] **AC26.** That transcript states which recording forms and which conditions
  the session does not exercise.
- [ ] **AC27.** `docs/product/changelog.md` carries a free-standing
  `## [core][<version>] — YYYY-MM-DD` entry at top level rather than nested under
  `[Unreleased]`.
- [ ] **AC28.** That entry contains a `### Highlights` block.
- [ ] **AC29.** `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json` read the same version, one patch above
  the value on the base branch at commit time.
- [ ] **AC30.** `make build-self-dry-run` reports no projection drift.
- [ ] **AC31.** The generated highlights projection matches the changelog entry.

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
  `packs/core/.apm/skills/work-loop/assets/state.json`, 27 fields)
- Technical: one shipped check asserts the bundled template's exact field set, so
  adding fields to the template requires updating it; the reader itself validates
  no key set, and the documented forward-field rejection is a fixed literal list
  that does not include either new field (source:
  `packs/core/tests/skills/work-loop/test_loop_cohort_cli.py:245` asserts
  `set(template) == EXPECTED_STATE_KEYS`; `_loop_guards.read_state` performs no
  key validation)
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
- Process: no release indicator beyond the changelog is required, because this
  change touches only `packs/`, `docs/`, and `guides/`, all non-impacting prefixes
  (source: `tools/repo/check_release_impact.py` `NON_IMPACTING_PREFIXES`)
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
