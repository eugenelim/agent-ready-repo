# Spec: Execution supervisor core

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0144, ADR-0061, ADR-0005, RFC-0028
- **Brief:** brief:acceptance-centered-work-loop
- **Discovery:** none
- **Contract:** `contracts/delivery/` (canonical bundle; this spec adds `task-contract.v1`, `execution-request.v1`, `execution-result.v1`, `mechanical-journal.v1`, and `effect-resolution.v1`); `contracts/jsonschema/loop-run-event.schema.json` (consumed unchanged); `<spec>/.supervisor/run.json` fields (defined here)
- **Shape:** service
- **Depends on:** spec:acceptance-authority-and-evidence, spec:structured-review-boundary

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

Platform Core maintainers get a skill-shipped supervisor that can execute an approved spec end to end on synthetic runs — admitting the approved pair, reprojecting tasks inside the reviewed envelope without approval, refusing protected changes, guarding red-before-green, and never repeating an external effect — while the current engine stays the only procedure owner adopters reach. Success is that every variant of the crash corpus converges to the uninterrupted run's result, and that no effect in the effect corpus runs twice.

## What Changes

- `work-supervisor.py` and `_supervisor_*.py` siblings arrive in `packs/core/.apm/skills/work-loop/scripts/`, called by nothing in the skill yet.
- Admission commits the approval pair to `docs/specs/<feature>/delivery/approvals.jsonl`, and envelope references are derived from approved spec sections.
- Tasks project from the existing plan grammar, which gains an optional `**Effects:**` line and a stub fence; in-envelope replans need no approval.
- Completion, red proof, the retry count, and effect state re-derive from supervisor commits and `delivery/` records; the journal is a deletable cache.
- The supervisor writes `.loop-run/events.jsonl` lines and a `run.json` status file for the workspace bridge.

## Scope and Non-goals

This spec owns the supervisor's procedure: admission, terminal handling, task
projection and replanning, the TDD guard, sequential dispatch through
controller-executed requests, recovery, the implementation retry count,
external-effect resolution, derived readiness, the stage set, `run.json`, and
event lines. It consumes Slice 1's acceptance, approval, envelope,
change-classification, evidence, verdict, subject, and content-safety
contracts and Slice 2's `review_readiness` without redefining them.

Sibling specs own the rest of Slice 4: worker-attempt checks and Windows process
control (`execution-supervisor-attempt-security`), reviewer selection, review
counters, and policy wiring (`execution-supervisor-review-gate`), and the skill
switch, old-engine removal, and sole-producer rule for the event file
(`execution-supervisor-cutover`). This spec changes no adopter-visible procedure
and does not move the product result off the execution-root worktree.

Trust follows ADR-0144 D11: worker attempts are untrusted, the controller is
trusted, and named-human decisions are recorded with authority references.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | The supervisor writes five new portable records and a status file the bridge reads. | `contracts/delivery/`, `contracts/REGISTRY.md`; `run.json` fields in this spec | `agentbundle` contract maintainers | Schema validation, the no-copy bundle check, and emitted-record parity | Each record has one canonical schema, a registry row, and a backward spec pointer. |
| Maintainer procedure | Plan authors need the stub fence and `**Effects:**` grammar. | `packs/core/.apm/skills/work-loop/references/tdd-stubs.md`; `packs/core/.apm/skills/new-spec/assets/plan.md` | Core pack maintainers | Reference link check and new-spec evals | Both grammars are stated where plan authors read them. |
| Release history | Core gains unused supervisor code. | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md` | Core pack release maintainers | Version parity | Each Core 3.x release carrying a task has a maintainer-facing changelog line. |

## Agent Rules

### Always do

- Cite the Slice 1 and Slice 2 contracts for every rule they own; do not
  restate them.
- Persist semantic records only under `docs/specs/<feature>/delivery/` through
  the existing evidence and confined-mutation ports.
- Keep supervisor modules importing only the standard library and siblings in
  `work-loop/scripts/`.

### Ask first

- Any implementation choice that departs from an ADR-0144 decision.
- Changing a value this spec states.

### Never do

- Make `SKILL.md` or any reference invoke the supervisor.
- Change `loop-engine.py` or `loop-cohort.py` behavior.
- Add a top-level directory, an external dependency, or a supervisor module
  outside `work-loop/scripts/`.

## Testing Strategy

- **Admission (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0021):**
  TDD over import, status, intent, authority-reference, bookkeeping-edit, and
  legacy-directory fixtures, because each case has one closed result.
- **Replanning and terminal intent (AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012):**
  TDD over the replan corpus, because a wrongly admitted change or a re-run of
  finished work must make a fixture fail.
- **TDD guard (AC-0013, AC-0014):** TDD over the TDD corpus in a temporary Git
  repository.
- **Recovery and sequencing (AC-0015, AC-0016, AC-0017, AC-0018):** goal-based
  runs of the crash corpus, because recovery is visible only across a whole
  run.
- **Effects (AC-0019, AC-0020):** goal-based runs of the effect corpus plus a
  two-process claim race.
- **Re-approval, worker edits, effect names, and feed compatibility (AC-0030, AC-0031, AC-0032, AC-0033, AC-0034):** TDD over
  re-approval, cited-record, and index fixtures.
- **Readiness, counts, and status (AC-0022, AC-0023, AC-0024, AC-0025, AC-0026):**
  TDD over the Readiness truth table and status fixtures.
- **Packaging and dark launch (AC-0027, AC-0028, AC-0029):** goal-based
  clean-environment and search checks.

## Acceptance Criteria

### Definitions

- **Protected references.** Each of Slice 1's six envelope references is the
  reference name joined to a digest over that name and its owning content as it
  stands in the working tree, each section prefixed by its heading,
  canonicalized as Slice 1 canonicalizes the approved spec:
  - `spec_policy`: `Acceptance Criteria`, `Testing Strategy`, and `Agent Rules`;
  - `scope_and_non_goals`: `Scope and Non-goals`;
  - `authority_and_security`: the `Constrained by:` value plus each cited
    record's `## Decision` section for an ADR, `## Proposal` section for an
    RFC, and whole file otherwise or when that section is missing;
  - `public_contracts`: the `Contract:` value;
  - `durable_outputs`: `Durable Outputs`;
  - `accepted_risk`: `Accepted Risk`.
  A missing spec section contributes empty content.
- **Bookkeeping edit.** A change to `Outcome`, `What Changes`, `Follow-ons`, or
  `Assumptions`; an acceptance-criterion checkbox; a `Status:` token; spec
  metadata other than `Constrained by:` and `Contract:`; plan text; or a cited
  record outside its contributing section.
- **Authority reference.** A role, optionally followed by `:` and 12 to 64
  lowercase hexadecimal characters. `start --authority-ref` accepts `owner`,
  `start --review-authority-ref` accepts `plan-reviewer`, `resolve-effect`
  accepts `effect-authority`, and a risk decision accepts `risk-owner`.
- **Run.** Everything from a spec's first admitted `start` onward; later
  re-approvals keep its run id.
- **Task identity.** A task's `### Tn:` title with its number removed; a title
  edit makes a new task.
- **Effect key.** For a task effect, the run id and the effect name, which must
  be unique across the plan's `**Effects:**` lines; for a `finish` effect, the
  run id, the effect name, and the `HEAD` commit when terminal was first reached
  for that tree. No replan of the declaring task changes a task effect's key.
- **Task revision.** A digest over the task's title without its number and its
  pinned fields — `Tests:` with its stub fences, `Touches:`, `Done when:`, and
  `Effects:` — so renumbering, reordering, and edits to working fields such as
  `Approach:` leave it unchanged.
- **Stub digest.** A digest over a task's stub fences; a red proof belongs to the
  task and its stub digest.
- **Stage set.** `admitted`, `implementing`, `gating`, `reviewing`,
  `awaiting-human`, and `terminal`.
- **`run.json`.** `<spec>/.supervisor/run.json` holding `run_id`, `active`,
  `stage`, `gate_pending`, `gate_question`, and `refusal`. `active` is true from
  the first admitted `start` until terminal. `stage` is `admitted` before the
  first task request, `implementing` for task requests, `gating` for
  `run-gates`, `reviewing` for `review-role` and `assess-finding`,
  `awaiting-human` while a `human-decision` is open or a refusal stands,
  `terminal` after terminal, `implementing` for `write-stub`,
  `external-effect`, and `effect-query`, and `gating` for `regenerate`. `gate_pending` is true exactly while a
  `human-decision` is open, with its question in `gate_question`. `refusal`
  names the current refusal code and owner, or is empty.
- **Step kinds.** Each supervisor commit carries exactly one operation:
  `approval`, `replan`, `stub`, `red`, `implement`, `evidence`, `gate-fail`,
  `review`, `effect-intent`, `effect-dispatch`, `effect-receipt`, `claim`,
  `resolution`, or `terminal`. Each is one supervisor step and emits one event whose `event`
  field is the operation.
- **Kill points.** After each journal append; after a supervisor commit is
  built and before `HEAD` moves; after `HEAD` moves and before working copies
  sync; after working copies sync and before the event append; and between an
  effect dispatch and its receipt.
- **Request kinds.** The closed set `implement-task`, `write-stub`, `run-gates`,
  `review-role`, `assess-finding`, `external-effect`, `effect-query`,
  `regenerate`, and `human-decision`.
- **Replan corpus.** One fixture per Replan truth-table row, plus renumbering
  tasks, rewriting another task's `Depends on:`, revising a completed task,
  splitting and merging tasks, and editing `## Terminal Intent` mid-run.
- **TDD corpus.** A one-stub task, a two-stub task, a `no stub` task, a task
  revised after its stub commit, a revised completed TDD task, and an attempt
  that changes a production file before red.
- **Crash corpus.** A synthetic three-task code run — one TDD task, one task
  declaring an external effect, one plain task — with one review round with a
  finding, run once uninterrupted and then once per variant: the supervisor is
  killed at each kill point, the journal is deleted at each kill point, the journal is deleted during a live lease, a supervisor commit lands
  during a live lease, `next` runs during a live lease with worker files present,
  and the branch is rebased with messages preserved.
- **Effect corpus.** The crash corpus's effect task plus a `finish` push, run
  through every Effect truth-table row, a later task's commit after a receipt, a
  rebase after a push, a crash between dispatch and receipt, and a revision,
  renumbering, retitle, replacement, split, and merge of the effect task both
  before and after its receipt.

### Replan truth table

| Change after initial review | Supervisor result |
| --- | --- |
| A bookkeeping edit, or any edit that leaves every protected reference and the terminal intent unchanged — including reordering, renumbering, splitting, merging, replacing, or deleting tasks and changing a task's tests, stubs, effects, or local method | New task projection; no approval request; unintegrated attempts of superseded tasks cancel; supervisor commits and `delivery/` records stay |
| Edit accepted criteria, testing strategy, or agent rules | Refuse; name the spec-amendment owner |
| Edit scope or non-goals | Refuse; name the spec-amendment owner |
| Edit the `Constrained by:` value or a cited record's contributing section | Refuse; name the decision owner |
| Edit the `Contract:` value | Refuse; name the contract owner |
| Edit durable outputs | Refuse; name the spec-amendment owner |
| Edit accepted risk | Refuse; name the risk owner |
| Edit `## Terminal Intent` so it differs from the current pair | Refuse; name the plan-review authority |
| A protected section heading repeats, or a cited record cannot be read | Refuse; name the ambiguous or unreadable reference |

### Readiness truth table

| Approval and initial review | Criteria verdict | Slice 2 review readiness | Readiness |
| --- | --- | --- | --- |
| Current pair, envelope and terminal intent match | Every criterion supported by fresh admissible evidence | Acceptance eligible | Ready |
| Current pair, envelope and terminal intent match | Any criterion insufficient, stale, or contradicted | Any | Not ready; the run projects repair or evidence work |
| Current pair, envelope and terminal intent match | Every criterion supported | Not eligible | Not ready; the run projects review or repair work |
| No pair | Any | Any | Not ready; refuse with `no-approval` |
| Envelope or terminal intent mismatch | Any | Any | Not ready; refuse per the Replan table |

### Effect truth table

`Absent` means the effect source definitively lacks the operation, so a
re-dispatch cannot repeat an effect.

| Durable record for the operation | Effect source query (controller-run) | Current `effect-resolution.v1` | Supervisor result |
| --- | --- | --- | --- |
| Receipt | Not run | Any | Done; never repeat |
| None | Not run | None | Record the intent, then dispatch the first attempt |
| Intent, no receipt | Attempt still running | Any | Dispatch nothing |
| Intent, no receipt | Present | Any | Record the receipt; never repeat |
| Intent, no receipt | Absent | None, with fewer than 3 recorded dispatches | Record a dispatch, then dispatch again |
| Intent, no receipt | Absent | None, with 3 recorded dispatches | Request a `human-decision`; dispatch nothing |
| Intent, no receipt | Absent | `retry-authorized` unclaimed | Claim one retry, then dispatch it |
| Intent, no receipt | Absent | `retry-authorized` already claimed | Dispatch nothing; a new decision is required |
| Intent, no receipt | Absent | `do-not-retry` | End the operation |
| Intent, no receipt | Absent | `effect-confirmed` | Request a `human-decision`; dispatch nothing |
| Intent, no receipt | Unknowable | None | Request a `human-decision`; dispatch nothing |
| Intent, no receipt | Unknowable | `effect-confirmed` | Record the receipt; never repeat |
| Intent, no receipt | Unknowable | `do-not-retry` | End the operation |
| Intent, no receipt | Unknowable | `retry-authorized` unclaimed | Claim one retry, then dispatch it |
| Intent, no receipt | Unknowable | `retry-authorized` already claimed | Dispatch nothing; a new decision is required |

### Criteria

Admission

- [x] **AC-0001.** A completed `start` commits exactly one line to
  `delivery/approvals.jsonl` holding one `approval-record.v1` and one
  `initial-plan-review.v1`, bound to the envelope fingerprint, terminal intent,
  code-trust classification, run id, and both authority references.
- [x] **AC-0002.** After an interrupted or refused `start`, no partial line is
  readable from `delivery/approvals.jsonl`, no task is projected, and the next
  `start` or `next` completes without a human decision.
- [x] **AC-0003.** `start` refuses unless the spec's `Status:` is `Approved` or
  `Implementing`, the plan's is `Approved` or `Executing`, and `--intent` equals
  the spec's `## Terminal Intent` value when that section exists.
- [x] **AC-0004.** `start` and `resolve-effect` refuse any value that is not an
  authority reference accepted for that flag.
- [x] **AC-0005.** After any bookkeeping edit, the approval pair stays current
  and the envelope fingerprint is unchanged.
- [x] **AC-0006.** A spec lacking every optional protected section imports with
  six distinct reference values.

Replanning and terminal intent

- [x] **AC-0007.** Every row of the Replan truth table returns its stated result
  for every replan-corpus fixture that reaches it.
- [x] **AC-0008.** A refusal row writes no commit, ref, lease, journal line,
  event, or tracked file; its code and owner reach the controller through
  `next`'s output and `run.json`'s `refusal` field.
- [x] **AC-0009.** No replan-corpus fixture in the first Replan row produces an
  approval request.
- [x] **AC-0010.** Renumbering or reordering tasks, or rewriting another task's
  `Depends on:`, never re-requests a completed task.
- [x] **AC-0011.** A completed task whose own content changes, or that is split
  or merged into new tasks, is requested again, and its earlier commits stay in
  history.
- [x] **AC-0012.** Under `spec-plan` intent the run ends with a terminal receipt
  after the initial review, emits no execution request, projects no task, and
  makes exactly two commits — `approval` then `terminal` — touching only the
  spec's `delivery/` directory.

TDD guard

- [x] **AC-0013.** In every TDD-corpus case, no production change for a
  stub-declaring task is admitted before the supervisor has itself observed
  each stub for the task's current stub digest fail with an exit code its fence
  declares as red (default `1`), byte-identical to the plan; any other exit is
  not red.
- [x] **AC-0014.** In every TDD-corpus case, the task reaches completion: a
  `no stub` task without a red proof, and a stub task whose stubs already pass
  through a `stub-not-red` refusal naming the `no stub` replan.

Recovery and sequencing

- [x] **AC-0015.** Every crash-corpus variant reaches the uninterrupted run's
  completed tasks by identity, revision, and committed tree, and its
  `delivery/` records with timestamps normalized and effect dispatch lines
  excluded, with no duplicate record, and the synthetic effect source records
  exactly one run of each effect.
- [x] **AC-0016.** Every crash-corpus variant reaches terminal without a
  `human-decision` the uninterrupted run did not need.
- [x] **AC-0017.** In every crash-corpus variant, `next` issues a new attempt
  only after the current attempt is reported or superseded, and otherwise
  re-issues the current attempt unchanged.
- [x] **AC-0018.** Every crash-corpus variant's `.loop-run/events.jsonl` holds
  one validating line per supervisor step, with the step kinds defined above and
  no duplicate step id.

Effects

- [x] **AC-0019.** Every effect-corpus case executes each declared effect
  exactly once, and every row of the Effect truth table returns its stated
  result.
- [x] **AC-0020.** Of two processes claiming one authorized retry, exactly one
  records the claim and at most one dispatch occurs.

Legacy runs

- [x] **AC-0033.** Projection refuses a plan in which two `**Effects:**` lines
  declare the same effect name.
- [x] **AC-0030.** After a protected-edit refusal, an amendment, and a second
  `start`, the run id, completed tasks, effect receipts, and implementation
  retry count are unchanged.
- [x] **AC-0031.** `report` refuses, before any commit, a result whose change
  set changes the spec directory or any cited record.
- [x] **AC-0032.** After every supervisor commit and working-copy sync,
  `git diff --cached` shows no change.
- [x] **AC-0034.** Slice 3's `replay_admitted_frames` reads the supervisor's
  `delivery/evidence.jsonl` and returns every admitted evidence frame the run
  wrote.
- [x] **AC-0021.** `start` on a spec directory holding `engine-state.json` or a
  cohort `state.json` never reads either file.

Readiness, counts, and status

- [x] **AC-0022.** Every row of the Readiness truth table returns its stated
  result.
- [x] **AC-0023.** The supervisor reads no stored criterion verdict or readiness
  answer as input.
- [x] **AC-0024.** On an admitted, non-terminal run with no refusal,
  `status --check` exits 3 when the implementation retry count has reached 5,
  and 0 below it, before and after journal deletion and across any replan; a
  terminal run exits 0.
- [x] **AC-0025.** On a non-terminal run, `status --check` exits 1 when the run
  is refused, and 3 takes precedence when both a refusal and the cap apply; any
  run exits 2 on a usage error.
- [x] **AC-0026.** `run.json` reports the stage and gate fields defined above at
  every step of the crash corpus.

Packaging and dark launch

- [x] **AC-0027.** `work-supervisor.py` completes the crash corpus's
  uninterrupted run with only the standard library and the skill's `scripts/`
  directory importable.
- [x] **AC-0028.** No file in the skill other than the supervisor's own modules
  invokes `work-supervisor.py`.
- [x] **AC-0029.** The work-loop test suites present at the merge-base with
  `main` when this spec's first task starts pass unchanged.

## Follow-ons

none — the sibling specs named in Scope own the rest of Slice 4.

## Terminal Intent

`code` — implement the dark supervisor core only.

## Accepted Risk

none

## Assumptions

none
