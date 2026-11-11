# Plan: Spec supervisor

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md` (request kinds, gates, resume, session rules); `packs/core/.apm/skills/work-loop/scripts/` (`work-supervisor.py` and its helpers, the analogue for verbs, attempts and pins, read and not edited); `packs/core/.apm/skills/work-loop/references/pre-execute-review.md` and `scripts/review-artifact.py` (the review procedure the supervisor encodes); `packs/core/tests/skills/work-loop/` (how a supervisor's verbs are tested). Named uncertainty: how the work supervisor tolerates a sibling's gate records, and the exact ledger path, are `implementation-discovered`.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open, and
> the run continues with every finished task still finished. Execution
> observations belong in `docs/specs/<feature>/notes/verification-ledger.md` (or
> the adopter's equivalent). A genuine error in a protected section follows the
> controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are working
> material the controller corrects in place, before or after approval, while no
> attempt is open. After approval, grounding for a seam or design means recorded
> as `implementation-discovered`, and each later correction, is a controller edit
> of the plan's `## Design (LLD)`, never a ledger line; a settled design decision
> that execution falsified is a plan error the owner agrees to, corrected the same
> way unless it reaches a protected section. A TDD task's `stub` fence is likewise
> written by the controller at task start, not carried in the approved plan.
> Treating working material as contract is how a review spends a round on prose
> no gate consumes — the measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

<!-- Existing plans without this field remain valid. Treat its absence as a
named assurance gap during structural review, not a universal lint failure. -->

<!-- **Durable-plan fill.** This template is the implementation and verification
strategy for a durable delivery slice. Fill Approach, Constraints, Risks,
Design, Tasks, and Changelog to the depth the durable work requires. Its sibling
spec is the durable behavior contract. Eligible direct-light work does not
create this artifact. -->

## Approach

Build `spec-supervisor.py` as a state machine derived from the spec directory's ledger, the git history and the open attempt, one verb at a time, with `work-supervisor.py` as the analogue and never an import. The order is state and admission first, then requests and resume, then the ledger commit rule, then review rounds, then gates and the human `answer` verb, then the delegated `start`, then the instruction text and how-to, then the release records and the live trial. The riskiest part is resume across a killed process, so the ledger and attempt record are built before any review logic.

## Constraints

- ADR-0162 D1 to D7: the six commands, the manifest, `delegate-verb`, a gate or committed status at every phase boundary, no approval by a sibling, the round cap, and the core pack owning the manifest.
- ADR-0163: the script lives in `new-spec`, `work-loop` stays the front door, and no work-loop pin file changes.
- ADR-0157 D4: only an `approve` from the gate's named human advances a gate, and no verb, flag, default or record approves.
- ADR-0144: `work-supervisor.py` and its pin set are not edited.
- `packs/AGENTS.md`: shipped pack content carries no internal citation, a pack update bumps `pack.toml` and `plugin.json` together, and a non-cosmetic update updates the pack's eval harness.
- Spec `supervisor-manifest-contract`: the manifest conforms to `supervisor-manifest.v1`.

## Construction tests

**Integration tests:** one end-to-end pack test drives `start`, rounds, both gates and the delegated `start` against a stub `work-supervisor` in a temporary repository.
**Manual verification:** the live resume trial of AC-0027, three tries on three CLIs.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| How-to for a session | T7 | the guide lint and a content check | the how-to matches the shipped commands |
| The supervisor, manifest and policy | T1 to T6 | the pack tests | the manifest validates and every verb test is green |
| Instruction text and driver line | T7 | the content-pin test | both files name the supervisor and the fallback |
| Release history | T8 | `tools/changelog.py validate` and the self-host drift check | the changelog validates and `make build-self` is clean |

## Design (LLD)

### Interfaces & contracts

The six verbs are `start`, `next`, `report`, `status`, `park` and `gates`, plus the human `answer`. Traces to: AC-0001 to AC-0021.

- Output is JSON on stdout. A refusal is `{"refusal": {"code": <name>, "detail": <text>}}` and a request is `{"request": {...}}`, as the architecture examples show.
- A request carries `schema_version` 1, `request_id`, `run_id`, `kind` and `stage`, plus per-kind keys: a `review-round` names `role` and `exclude_profile`, a `delegate-verb` names `command`, and a `consent` and a `human-decision` name the gate and the digest.
- Refusal names that the sources fix are used as given: `request-consumed`, `result-fact-refused`, `supervisor-changed`, `no-human-answer`, `no-tty`, `stale-digest`, `parked`, `default-branch-refused` and `checkout-dirty`. Any other refusal gets a lowercase-hyphen name chosen at build time and listed in the instruction text's table.
- `spec-policy.json` holds `max_review_rounds` (default 3) and nothing the human does not own; a controller never edits it.
- The manifest `supervisor.toml` sits at the `new-spec` skill root and lists the seven request kinds, their modes (`headless` or `attach` for `author-spec`, `revise`, `review-round` and `adjudicate`; `ferryman-run` for `delegate-verb`; `human` for `consent` and `human-decision`), `delegates_to` with `work-supervisor` `park` and `start`, and `pinned_files` for the script, its helpers and the policy file.

Owned by: T1, T2, T6

### State & control flow

State is derived, never held: the supervisor reads the ledger, the open attempt and the git history on every call. Traces to: AC-0006 to AC-0009, AC-0012 to AC-0016, AC-0020 to AC-0021.

- A request is opened by `next` writing an attempt record and closed by `report` writing the result and one commit. A fresh process that finds an open attempt re-issues the same request id.
- The step order is `author-spec` (when the spec has no review yet), then `review-round` per reviewer role, then `adjudicate`, then `revise` or the `spec-approved` consent, then the `plan-approved` consent, then the delegated `start`. A round is weak when its reviewer's agent definition equals the author's, and a weak round never counts toward convergence.
- The cap gate and the weak-round gate are `human-decision` requests with the options `continue`, `accept-residue` and `stop`. `continue` adds exactly one round, and `accept-residue` leads to the consent request, which a human still answers.
- `implementation-discovered`: the attempt record's file layout and the ledger's path inside the spec directory, settled when the first test needs them and recorded here.

Owned by: T2, T3, T4, T5

### Data & schema

The ledger is append-only, one JSON line per step, committed with the step's files in one commit. The answer record is one JSON line with `gate`, `decision`, `digest`, `by`, `at` and a field stating the identity is unverified, written only by `answer`. Traces to: AC-0008, AC-0017. The supervisor writes gate records only under its own store, never into the work supervisor's `gates/` directory, whose tolerance of foreign records is unverified.

Owned by: T3, T5

### Failure, edge cases & resilience

Admission refusals write nothing. `report` refuses a foreign commit, a wrong request id and a second report on one id. A killed process leaves either an open attempt, which resume re-issues, or a committed step, which the ledger shows. Traces to: AC-0002, AC-0003, AC-0007, AC-0009.

Owned by: T1, T2, T3

## Tasks

### T1: Admission, manifest and pins

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/.apm/skills/new-spec/supervisor.toml`, `packs/core/.apm/skills/new-spec/spec-policy.json`, `packs/core/tests/skills/new-spec/test_spec_supervisor_admission.py`

**Tests:**
- `start` admits a good directory (AC-0001), refuses on the default branch and on a dirty tree (AC-0002), and refuses a directory with no `spec.md` or no `plan.md` (AC-0003). The manifest validates against the E0 schema and its kinds equal the kinds `next` can return (AC-0005). The pinned digests are taken at `start` and a changed file refuses `supervisor-changed` (AC-0022). The diff touches nothing under the work-loop scripts or policy JSON (AC-0023). Mode: TDD over a temporary repository.

**Done when:** the T1 tests for AC-0001 to AC-0003, AC-0005, AC-0022 and AC-0023 pass.

### T2: Requests, resume and the open attempt

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_resume.py`

**Tests:**
- Every request carries the envelope keys and an allowed kind and stage (AC-0004). A killed process followed by `status` and `next` returns the same request id with no ledger line lost or repeated (AC-0006). `report` refuses a wrong id and a second report (AC-0007). `status` shows each gate's answer and decision, and `next` returns `parked` while a gate waits (AC-0019). Mode: TDD, with a process killed between steps.

**Done when:** the T2 tests for AC-0004, AC-0006, AC-0007 and AC-0019 pass.

### T3: Ledger and commit-per-step

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_ledger.py`

**Tests:**
- Each completed step adds exactly one commit with one new ledger line and the step's files, and an earlier line never changes (AC-0008). `report` refuses when a foreign commit has landed since the request was issued (AC-0009). Mode: TDD with real commits.

**Done when:** the T3 tests for AC-0008 and AC-0009 pass.

### T4: Review rounds, weakness and the cap

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_rounds.py`

**Tests:**
- A `review-round` names a role and the author's agent definition to exclude, and none goes to the author's definition (AC-0010). A weak round yields the `human-decision` gate and no spec-approved consent (AC-0011). A converged non-weak round yields the spec-approved consent (AC-0012). A sustained finding yields `revise` then a further round (AC-0013). After the cap the `human-decision` gate appears, with the cap read from the policy file and a default of 3 (AC-0014). `continue`, `accept-residue` and `stop` each do exactly what the criterion says (AC-0015). Mode: TDD over recorded reviewer reports.

**Done when:** the T4 tests for AC-0010 to AC-0015 pass.

### T5: Gates and the `answer` verb

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_gates.py`

**Tests:**
- `answer` refuses without a controlling terminal, refuses a gate that is not pending or a stale digest, and otherwise records one answer line that states the identity is unverified (AC-0017). `report` refuses a `consent` result with no answer record and no verb, flag or default approves (AC-0018). `request-changes` yields `revise` with the note labelled untrusted, and `reject` yields the `human-decision` offering `revise` or `abandon` (AC-0020). Mode: TDD, driving `answer` through a pseudo-terminal.

**Done when:** the T5 tests for AC-0017, AC-0018 and AC-0020 pass.

### T6: The delegated park and start

**Depends on:** T4, T5

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_delegation.py`

**Tests:**
- For each of the two gates `next` issues the `delegate-verb` `park` on `work-supervisor` and then the human-only `consent` (AC-0016). After both approvals `next` issues the delegated `start` with both digests, and the subject is terminal once `start` answers `admitted` (AC-0021). Mode: TDD against a stub `work-supervisor`.

**Done when:** the T6 tests for AC-0016 and AC-0021 pass, and the integration test passes.

### T7: Instruction text, driver line and how-to

**Depends on:** T6

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`, `packs/core/.apm/skills/work-loop/SKILL.md`, `guides/core/how-to/`, `packs/core/tests/skills/new-spec/test_spec_supervisor_instructions.py`

**Tests:**
- The work-loop spec-plan instructions name `spec-supervisor` when installed and `pre-execute-review.md` otherwise (AC-0024). The shipped instruction text carries the five session rules (AC-0025). The how-to exists, states `ferryman` is later and optional, and names prerequisites and routing, and passes the guide lints (AC-0026). Mode: goal-based content pins and a guide lint.

**Done when:** the T7 tests for AC-0024 to AC-0026 pass.

### T8: Release records, projections, eval and the live trial

**Depends on:** T7

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `packs/core/.apm/skills/new-spec/evals/`, `.claude/skills/new-spec/`, `.agents/skills/new-spec/`

**Tests:**
- `python3 tools/changelog.py validate` passes, the core release check accepts the version with both version files matching, the self-host projections are committed and clean, and a `new-spec` eval case covers the supervisor path. In three live sessions on different CLIs a fresh session resumes a real run from `status` alone and the results are recorded in the verification ledger (AC-0027). Mode: goal-based, with manual QA for the trial.

**Done when:** the T8 checks pass and AC-0027 holds with its recorded evidence.

## Rollout

Delivery is one change set with no flag. Rollback is removing the new files, since nothing calls the supervisor until `work-loop` is told to drive it, and that driver line lands in the same release, so a revert removes both. A core pack release carries it to adopters. `work-supervisor.py` is unchanged and its pin is unaffected. No infrastructure or external system is involved.

## Risks

- A session agent may not resume cleanly from `status` alone, which is the brief's kill condition. Mitigation: the live trial of AC-0027 is a task, and a failed trial stops the brief.
- Committing one commit per step lands the supervisor's commits on the user's branch. Mitigation: the default-branch and dirty-tree refusals, and commits that carry only the ledger line and the step's files.
- The work supervisor's tolerance of a sibling's gate records is unverified. Mitigation: the sibling writes only under its own store, and the live trial runs against the real work supervisor.
- A session agent may not dispatch a distinct reviewer unprompted. Mitigation: the `weak` flag and the instruction text, with a weak round never counting toward convergence.

## Changelog
