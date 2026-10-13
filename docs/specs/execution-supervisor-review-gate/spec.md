# Spec: Execution supervisor review gate

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0144, ADR-0042, ADR-0047, ADR-0061
- **Brief:** brief:acceptance-centered-work-loop
- **Discovery:** none
- **Contract:** `contracts/delivery/` (consumes Slice 2's `review-subject.v1`, `review-obligation.v1`, `review-report.v1`, `finding-assessment.v1`, and `finding-disposition.v1` unchanged); `packs/core/.apm/skills/work-loop/review-rules.json` (defined here)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Protected semantic-policy contract.** `Contract`, `Scope and Non-goals`,
> `Durable Outputs`, `Agent Rules`, `Testing Strategy`, `Acceptance Criteria`,
> `Terminal Intent`, and `Accepted Risk` are approval-bound or explicitly
> review-authorized. A change follows its owning amendment, review, or risk
> decision. `Outcome`, `What Changes`, `Follow-ons`, and `Assumptions` are
> working material that may be corrected without changing accepted authority.

## Outcome

Platform Core maintainers get a supervisor review stage that closes only from Slice 2 structured review readiness, selects reviewers from one data file that carries today's roster, boundaries, and mandatory-versus-skippable rules verbatim, and never lets a mandatory reviewer be skipped — while pre-approval and light-mode review keep their finding-adjudication commands, with today's outputs and today's shared review budget, on a script that survives the cutover. Success is unchanged reviewer selection and blocking behavior, a synthetic reviewer that joins with a data edit alone, and policy families that select exactly what they select today.

## What Changes

- The reviewer roster table, each role's boundary and fallback text, the high-risk definition, and the default review budget move into `packs/core/.apm/skills/work-loop/review-rules.json`.
- A resolver turns the rules plus the controller's durable selection record into one Slice 2 review-policy instance whose mandatory and optional kinds match today's blocking rules — `_supervisor_review.py`, `delivery/review-selections.jsonl`.
- The supervisor's review stage closes from `review_readiness`, with reports, assessments, and dispositions in the Slice 2 `EvidenceStore` log.
- `review-artifact.py` gains `classify`, `raw-classify`, `inspect`, and `record`, each matching recorded pre-change output, and the `loop-cohort.py review` verbs delegate to them.
- The policy-family registry gains entries for core's stage set and a declared `PRE-APPROVAL` constant — `references/policy-families.md`.

## Scope and Non-goals

This spec owns reviewer selection data, the policy resolver and selection
record, the supervisor review stage's use of Slice 2 facts, the relocated
finding-adjudication commands and the shared review budget, and policy-family
registry entries. It consumes Slice 2's review contracts and `review_readiness`
unchanged, and `execution-supervisor-core`'s request kinds, step kinds, stage
set, and step loop.

ADR-0144 D8's removal of the `raw-classify` gate applies to the supervisor's
code-review closure; pre-approval and light-mode adjudication keep the relocated
`raw-classify` command. This spec does not rewrite `SKILL.md`, remove
`loop-cohort.py`, or change light-mode procedure; `execution-supervisor-cutover`
does the skill rewrite and removal. Selection judgement for conditional roles
stays with the trusted controller (ADR-0144 D11).

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | ADR-0144's D8 scope, Consequence, and Confirmation must match this design. | `docs/adr/0144-work-loop-supervisor-owns-procedure.md` (Proposed, editable) | Platform Core decision-maker | ADR shape lint | D8 scopes the `raw-classify` removal to code-review closure, and the Confirmation says a reviewer joins through a `review-rules.json` entry and a typed report. |
| Maintainer procedure | The registry gains stage keys. | `packs/core/.apm/skills/work-loop/references/policy-families.md`, `guides/core/reference/phase-scoped-policy-delivery.md` | Core pack maintainers | Registry parity test | Both list the stage keys and the `PRE-APPROVAL` constant. |
| Skill evaluation | Live review commands gain new entry points. | `packs/core/.apm/skills/work-loop/evals/evals.json` | Core pack maintainers | Skill evals | The evals cover the relocated commands. |
| Release history | Live code changes. | Core manifests and `docs/product/changelog.md` | Core pack release maintainers | Version parity | Each task's Core 3.x release carries a changelog line. |

## Agent Rules

### Always do

- Keep reports, assessments, and dispositions in the Slice 2 `EvidenceStore`
  log.
- Copy roster, boundary, and fallback text verbatim, apart from the
  normalizations AC-0005 names.

### Ask first

- Changing which roles are mandatory, conditional, mode-limited, or skippable.
- Accepting risk for a supported material finding.

### Never do

- Encode a reviewer trigger as a path glob or other mechanical predicate.
- Add reviewer prompts, tools, models, session mechanics, or reviewer-session
  retries to the supervisor or `review-rules.json`.
- Change the output of an existing `loop-cohort.py review` verb while that
  script exists.

## Testing Strategy

- **Review closure and dispositions (AC-0001, AC-0002, AC-0003):** goal-based
  integration with findings, repairs, and a risk acceptance.
- **Selection data and enforcement (AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011):**
  goal-based for AC-0004 in a fixture copy of the skill, TDD for the rest over
  the rules file, the live roster, and selection fixtures.
- **Command relocation (AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018):**
  goal-based comparison over the comparison corpus and its recorded pre-change
  outputs.
- **Policy families (AC-0019, AC-0020):** TDD over the registry.

## Acceptance Criteria

### Definitions

- **Role obligation.** A role is mandatory when selected unless its `SKILL.md`
  text allows a named skip, so `security-reviewer` is mandatory whenever it is
  selected, infra work or not; `adversarial-reviewer` is always selected and
  mandatory. A selected role that is not mandatory is optional.
- **Selection record.** One `delivery/review-selections.jsonl` line per
  delivery subject and changed-path digest, holding the selected and omitted
  conditional roles, each omission's reason, and the controller's authority
  reference. The
  resolver supplies every always-selected role itself.
- **Review budget.** `review_retry_count` counts every findings round and every
  evidence retry, as `loop-cohort.py review record` counts them today, against
  `max_review_retries` from the spec's cohort `state.json` when cohort state
  exists and from `review-rules.json` otherwise.
- **Comparison corpus.** Recorded fixtures covering `classify`, `raw-classify`,
  `inspect --adjudication` with and without a previous-round fingerprint match,
  and `record` with each of `--fingerprint`, `--direct-clean-file`,
  `--structural-clean-file`, `--report`, `--all-skipped`,
  `--allow-retry-cap-override`, and an `--operation-id` replay, including a run
  that reaches the budget and a run whose cohort cap was raised by hand, each
  with its output recorded from the pre-change `loop-cohort.py review` verb.

### Criteria

Review closure and dispositions

- [ ] **AC-0001.** A full-mode code run passes the supervisor's review stage
  exactly when Slice 2 review readiness for the current review subject and
  policy is acceptance eligible.
- [ ] **AC-0002.** An admitted `human-decision` result carrying a `risk-owner`
  authority reference records `accept-risk` for a supported material finding,
  readiness then counts that finding as disposed, and no other result records
  `accept-risk`.
- [ ] **AC-0003.** A supported material finding projects repair work, and the
  supervisor records `fixed-by` only when a fresh report for the replacement
  subject closes it.

Selection data and enforcement

- [ ] **AC-0004.** In a fixture copy of the skill without a roster table, a
  synthetic reviewer role added only to `review-rules.json` closes its
  obligation by returning a `review-report.v1`.
- [ ] **AC-0005.** Each roster role in `review-rules.json` holds its roster
  condition, mode limit, role bullet, and fallback text from `SKILL.md`, and the
  file holds the high-risk definition, all matching the live text with only
  these normalizations: a trailing `(full mode)` moves into the mode limit,
  relative links are rewritten relative to the skill root, and a role with no
  bullet holds an empty boundary.
- [ ] **AC-0006.** While `SKILL.md` holds a reviewer roster table, a check fails
  whenever its roster roles' text differs from `review-rules.json`, and whenever
  `assets/state.json`'s `max_review_retries` differs from the rules file's.
- [ ] **AC-0007.** For each roster role, selected and omitted, the resolver's
  Slice 2 kind equals the role obligation.
- [ ] **AC-0008.** The resolver refuses a selection record that omits a
  conditional role without a reason, or names a role absent from
  `review-rules.json`.
- [ ] **AC-0009.** Two selection records that resolve to different roles or kinds
  give different `review_policy_fingerprint` values.
- [ ] **AC-0010.** A second selection record for the same delivery subject and
  changed-path digest is refused unless an admitted `human-decision` result
  carrying an `owner` authority reference authorizes the change.
- [ ] **AC-0011.** The selection record is committed through core's `review`
  step kind.

Command relocation

- [ ] **AC-0012.** For every comparison-corpus case, run as a sequence of calls
  against its seeded cohort state, both `review-artifact.py` and the
  `loop-cohort.py review` verbs return output byte-identical to the recorded
  pre-change output, and with cohort state present `review-artifact.py record`
  updates that state exactly as the pre-change verb did and writes no `record`
  artifact.
- [ ] **AC-0013.** For every comparison-corpus case run with cohort state, the
  `loop-cohort.py review` verbs leave the cohort counter values the pre-change
  verbs left.
- [ ] **AC-0014.** With no cohort state, `review-artifact.py inspect --run-id`
  reads the previous round's fingerprint from that run's persisted `record`
  artifact.
- [ ] **AC-0015.** With no cohort state, `review-artifact.py record` writes one
  `record` artifact per recorded round, counts the budget from `record`
  artifacts only, and refuses the round that would exceed `max_review_retries`
  unless `--allow-retry-cap-override` carries an authority reference.
- [ ] **AC-0016.** A replayed `record` with the same operation id and payload
  returns the first result and writes no second artifact.
- [ ] **AC-0017.** The supervisor's ingest maps every row of Slice 2's
  compatibility corpus to the result that corpus requires.
- [ ] **AC-0018.** `review-artifact.py validate` accepts a `record` artifact
  named `.context/reviews/<run-id>/<round>-record.md` and refuses one under any
  other name.

Policy families

- [ ] **AC-0019.** Every stage in core's stage set and the declared
  `PRE-APPROVAL` constant have a policy-family registry entry, and each
  pre-change engine state maps to a stage or that constant whose entry selects
  the same families.
- [ ] **AC-0020.** While `loop-engine.py` exists, every engine state still
  selects its pre-change families.

## Follow-ons

- Platform Core: `docs/product/briefs/acceptance-centered-work-loop.md` — an
  adopter-owned review-rules source that the skill-shipped default yields to.

## Terminal Intent

`code` — implement the review rules, resolver, selection record, review stage,
command relocation, and stage keys.

## Accepted Risk

none

## Assumptions

none
