# Plan: Spec supervisor core

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md` (request kinds, gates, resume); `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py` and its helpers (the analogue for verbs, attempts, refusals, `_spec_rel` confinement and the pin check, read and never edited or imported); `packs/core/.apm/skills/work-loop/references/pre-execute-review.md` and `scripts/review-artifact.py` (the review procedure the supervisor encodes); `packs/core/tests/skills/work-loop/` (how a supervisor's verbs, pins and kills are tested). Named uncertainty: the ledger, attempt and store paths, and how the default branch is read, are `implementation-discovered`.

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

Build `spec-supervisor.py` as a state machine that derives its state on every call from the ledger, git history and the open attempt, with `work-supervisor.py` as the analogue and never an import. The order is admission and confinement, then manifest and request shapes, then the report path with the ledger, allowed-path and protected-content checks and the resume cases, then review rounds with the supervisor's own report classifier, then the consent requests with `park`, `gates` and the digest copy, then pins, then the release records and the page 05 update. The riskiest parts are the protected-content check, which must accept foreign commits yet refuse a protected-content change outside its allowed edit, and a kill inside `report`, so both land before any review logic.

## Constraints

- ADR-0162 D1 to D7: six commands, the manifest, `delegate-verb`, a gate or committed status at each boundary, no approval by a sibling, the round cap parked as a `consent` gate, the core pack owning the manifest.
- ADR-0163 D1 to D3: the script lives in `new-spec`, and the sibling shares only the command contract with `work-supervisor.py`; the scope guard of AC-0014 cites it.
- ADR-0157 D2 to D4: `park` computes the gate digests and commits nothing, `gates` lists `pending`, `stale` or `invalid`, and only an `approve` from the gate's named human advances a gate, so no verb, flag, default or record here approves.
- `packs/AGENTS.md`: shipped pack content carries no internal citation, pack tests load modules under a unique name and never put `scripts/` on `sys.path`, a pack update bumps `pack.toml` and `plugin.json` together, and a non-cosmetic update updates the eval harness.
- Spec `supervisor-manifest-contract`: the manifest conforms to `supervisor-manifest.v1`, and every request to `supervisor-request-envelope.v1`.

## Construction tests

**Integration tests:** one end-to-end pack test drives `start`, a full review round, a `review-cap` consent and a `park` in a temporary repository, then runs the real installed `work-supervisor.py` `status`, `park` and `start` on the same spec directory with the ledger and a populated store present (AC-0013). It uses the real script, never a stub.
**Manual verification:** none; the live trials belong to `spec-supervisor-gates`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| The supervisor, manifest and policy | T1 to T6 | the pack tests, the manifest validator | the manifest validates and every verb test is green |
| Page 05 | T7 | a read of the page against this spec | no page 05 sentence contradicts this spec |
| Release history | T7 | `tools/changelog.py validate` and the self-host drift check | the changelog validates and `make build-self` is clean |
| Decision rationale | none | ADR-0162, ADR-0163 and ADR-0157 already Accepted | none further |

## Design (LLD)

### Seam decisions

This spec owns each point below, and `spec-supervisor-gates` cites it.

- **Order of release.** This spec releases first with a manifest of five kinds. `spec-supervisor-gates` releases after it and amends the manifest (AC-0004 here; the gates spec has its own manifest criterion). Each release's test asserts that the listed kinds equal the kinds a driven run returns at that release, and validates the manifest against `supervisor-manifest.v1`.
- **Consent digest.** A consent request's spec and plan digests are the work supervisor's gate digest, computed by a tested copy (`gate_digest` of `_supervisor_gates.py`, with its approval-entry drop, its hidden-character check and the canonicaliser `_loop_guards.canonical_contract` it calls), because the work-loop scripts are not importable by name. The supervisor digests the `spec.md` and `plan.md` blobs at `HEAD`. The digest corpus holds inputs that cover a plain file, an approval-entry line, a changed `Status:` line, CRLF text, a hidden character and invalid UTF-8, and the test loads the real module by path under a unique name. The `Status:` line does not move the digest (a probe against the real `park` showed the spec digest unchanged across `Draft` and `Approved`), which is why a human's approval commit leaves a parked gate `pending`.
- **`park` and `gates` of this supervisor.** `park` records an open `consent` request in the supervisor's own store, and `gates` lists those records. They never call `work-supervisor.py`. The real park of the approval gates is a `delegate-verb` request that `spec-supervisor-gates` adds.
- **Resume at a waiting gate.** An open `consent` request is returned by `next` with the same id and fields until it is parked. A parked request makes `next` refuse `parked`, and `status` names it. A fresh process re-derives this from the ledger, the open attempt and the store, so it reaches the same state. A matching answer record (owned by `spec-supervisor-gates`) is what lets `report` complete the request. No `consent` completes without one (`no-human-answer`).
- **Protected set and allowed edits.** The protected set and the one edit each item allows:

| Protected item | Allowed edit |
| --- | --- |
| The ledger | the supervisor's step commit, one appended line |
| Attempt records and the store | a supervisor verb only |
| The pin digests in the admission line, `spec-policy.json` | none |
| The `Status:` lines and plan approval-entry lines | after the ledger records a converged round, a commit that changes only those lines (a human approval, or a revert to `Draft` and `Drafting`) |
| The answers file and the hand-off record | added by `spec-supervisor-gates`, with the edit it states |

Traces to: AC-0004, AC-0011, AC-0025, AC-0026, AC-0027.

Owned by: T2, T3, T5

### Interfaces & contracts

Verbs: `start <spec-dir>`, `next <spec-dir>`, `report <spec-dir> <result-file>`, `status <spec-dir>`, `park <spec-dir>` and `gates`. Output is JSON on stdout; a request is `{"request": {...}}`, a refusal is `{"refusal": {"code", "owner", "detail"}}`, and an ended run answers `{"terminal": true}`, as `work-supervisor.py` does. Traces to: AC-0001, AC-0004, AC-0005, AC-0006, AC-0025, AC-0026.

- Refusal codes the sources fix are used as given: `request-consumed`, `supervisor-changed`, `no-human-answer`, `parked`, `default-branch-refused` and `checkout-dirty`. Others are chosen at build time as lowercase-hyphen names.
- Each request carries the five envelope keys. Kind and stage pair as follows: `author-spec` is `authoring`; `review-round` and `adjudicate` are `reviewing`; `revise` is `revising`; `consent` is `awaiting-human`. `delegating` is reserved for `delegate-verb`, and `terminal` is what `status` reports for an ended run. The kinds are `author-spec`, `review-round`, `adjudicate`, `revise` and `consent` at this release.
- Per-kind keys: `review-round` names `role` and `exclude_profile`; `adjudicate` names `exclude_profile` and the round; `revise` names the sustained findings as identifier, file reference and a bounded `untrusted` title; `consent` names `gate` and the spec and plan digests, and for `review-cap` and `review-weak` the open findings and the three answers with fixed consequence text. The fixed text for `approve` says it accepts the residue and leads to the `spec-approved` consent request, for `request-changes` that it continues exactly one further round, and for `reject` that it stops the run with no further request.
- The result file is `{"request_id", "facts"}`. `facts` for `author-spec` carries `agent_definition`; for `review-round` the `agent_definition`, the reviewer outcome and the persisted raw-report path; for `adjudicate` the `agent_definition` and the adjudication path. Report paths resolve under `.context/reviews/` and the supervisor reads them as bounded regular files.
- `spec-policy.json` holds `max_review_rounds` (default 3) and nothing else a human does not own. The manifest sits at the skill root and lists five kinds with these modes: `author-spec`, `review-round`, `adjudicate` and `revise` list `headless`, `attach` and `session`, and `consent` lists `human` only. `pinned_files` is derived from the directory listing in the test and holds every file under `scripts/` (which already holds the two `new-spec` lint scripts), `supervisor.toml` and `spec-policy.json`.

Owned by: T1, T2, T5

### Data & schema

The ledger is append-only JSON lines in the spec directory, one line per step, committed with the step's files. A line holds the step kind, request id, run id, the previous recorded commit, the facts the step verified (classification, finding count, identifiers, file references, author and reviewer agent definitions, `weak`), and, in the admission line only, the pin digests. The ledger path, the attempt-record layout and the store path are `implementation-discovered`; the store root is a directory beside, never inside, `<git-dir>/agentbundle-supervisor/`, because the work supervisor's preflight lists every `run-<hex>` directory there and refuses all verbs on a malformed one. Traces to: AC-0007, AC-0010, AC-0013, AC-0028.

Owned by: T3

### State & control flow

State is derived on every call from the ledger, git history and the open attempt. A request id is a function of the run id and the ledger position, so a fresh clone with no attempt record re-issues the same id. Traces to: AC-0006, AC-0015, AC-0025.

- `next` opens an attempt and returns the request; an open request is returned again unchanged.
- `report` runs, in order: id check, result bounds, ledger append-only check, protected-content check since the last recorded commit, working tree and index check against the kind's allowed set, then the kind's fact checks, then writes the files, the ledger line and one commit, then closes the attempt. A kill before the commit leaves an open attempt and uncommitted allowed files that a repeated `report` completes; a kill after the commit leaves a commit that the next verb adopts by closing the attempt.
- The closed path set of a kind: `spec.md` and `plan.md` for `author-spec` and `revise`, with every protected line unchanged, and no path for `review-round`, `adjudicate` and `consent`.
- Step order: `author-spec` when no review and no author is recorded; then one `review-round` per required role; `adjudicate` after a `findings` or footer report; `revise` then a further round after a sustained finding; the `spec-approved` consent on convergence. The `plan-approved` consent and the answer-driven transitions belong to `spec-supervisor-gates`.
- Round counter: a round is one `review-round` per required role against one revision of the pair, and `rounds_run` counts them across the run. A human decision on `review-cap` or `review-weak` leaves `rounds_run` unchanged. `approve` leads to the `spec-approved` consent. `request-changes` sets the allowance to `rounds_run + 1`, issues `revise` first when a sustained finding is open (a `revise` is not a round), then one round, after which a round that did not converge, or was weak, issues the gate again. `reject` ends the run. The answer handling is built by `spec-supervisor-gates`; this counter is the rule it builds against.

Owned by: T2, T3, T4, T5

### Behavior & rules

Review follows `pre-execute-review.md`. A raw report is classified by the supervisor's own function: `findings` when a finding line parses, `clean` when the sentinel line appears exactly once with only blank lines or a `## Not checked` footer around it, otherwise `invalid` with a reason code from the closed set the real script uses. A `clean` report with the footer is adjudicated, as the reference says. An adjudication classifies as `clean` for refuted-only or the exact clean result, `findings` for a sustained one, and `invalid` with `indeterminate-present` for an indeterminate one, which stops the run. A round is `weak` when any reviewer's reported agent definition equals the author's. The equivalence corpus is a set of recorded raw reports and adjudications checked into the pack tests, with the real script's output for each computed at test time. A run that stops is recorded `terminal` with its reason. Traces to: AC-0016 to AC-0023.

Owned by: T4, T5

### Failure, edge cases & resilience

Admission refusals write nothing. `report` refuses each case of AC-0008, AC-0010, AC-0011 and AC-0012, and each writes nothing. A foreign commit that leaves protected content alone is accepted, so a user's or the work supervisor's own commit never wedges a run. Traces to: AC-0002, AC-0003, AC-0008 to AC-0012, AC-0015.

Owned by: T1, T3

### Quality attributes (NFRs)

Security posture. Every path is confined with a link-refusing check before any read or write, modelled on `_spec_rel`. Pins hash the whole `scripts/` tree and load nothing before the pin check passes, with bytecode isolated as the work supervisor does, so a planted `.pyc` cannot run. Reviewer and human text is untrusted: consent requests carry no free text, and any other field is cut to 512 characters and marked untrusted. Traces to: AC-0003, AC-0024, AC-0028, AC-0029.

Owned by: T1, T5, T6

## Tasks

### T1: Admission and confinement

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_admission.py`

**Tests:**
- Admission writes one ledger line in one commit (AC-0001). Mode: TDD over a temporary repository.
- One refusal per member of the AC-0002 set, each writing nothing: the default branch, a dirty tree, a missing `spec.md`, a missing `plan.md`, a second `start` (the ledger, pins and store unchanged), and a `max_review_rounds` of 0, -1, `"3"` and 1.5. Mode: TDD.
- One parametrized list per verb for AC-0003: path-shape cases (absolute, `..`, `.`, backslash), a symlink and a regular-file component, and a symlink and a non-regular `spec.md`, `plan.md` and ledger. Mode: TDD.

**Approach:** copy the shape of `_spec_rel` and the plain-file reader of `work-supervisor.py` into the new script; do not import them.

**Done when:** the T1 tests pass.

### T2: Manifest, policy file and request shapes

**Depends on:** T1, spec:supervisor-manifest-contract/T2

**Touches:** `packs/core/.apm/skills/new-spec/supervisor.toml`, `packs/core/.apm/skills/new-spec/spec-policy.json`, `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_requests.py`

**Tests:**
- The manifest validates against the manifest schema with the validator the manifest-contract tests use, and the listed kinds equal the kinds a driven run returns (AC-0004). Mode: goal-based.
- Each request validates against the envelope schema and its kind and stage are in their sets (AC-0005). Mode: TDD.
- `next` issues `author-spec` only for a pair with no review and no author, a reported author is recorded, and a reported `human` author is recorded as given (AC-0006). Mode: TDD.

**Done when:** the T2 tests pass.

### T3: Report, ledger, allowed paths, protected content and resume

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_ledger.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_resume.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_integration.py`

**Tests:**
- One commit and one ledger line per step (AC-0007). Mode: TDD with real commits.
- One refusal per member of the AC-0008 set: a wrong id, a second report, a symlink, a non-regular, a 16 MiB plus one byte and a non-UTF-8 result file, and a `consent` result with no answer record (`no-human-answer`). Mode: TDD.
- An `author-spec` report is refused on a wrong spec status, a wrong plan status and a failing alignment lint (AC-0009). Mode: TDD.
- A line edited, removed, reordered and inserted before the last line each make every verb refuse (AC-0010). Mode: TDD.
- A foreign commit that changes no protected item is accepted, and so is one by the work supervisor (it adds `delivery/approvals.jsonl`); one commit per protected item (the ledger, an attempt record, a pin, `spec-policy.json`, a `Status:` line before convergence) is refused; the approval-edit exception is accepted after a converged round and refused before it (AC-0011). Mode: TDD.
- One working-tree and index case per kind, an `author-spec` and a `revise` step that edits `Status:` and a plan approval-entry line (AC-0012). Mode: TDD.
- The integration test runs the real installed `work-supervisor.py` `status`, `park` and `start` beside a populated store and a ledger and compares each answer with the answer without them (AC-0013). Mode: goal-based, integration.
- The diff against `main` holds nothing under the work-loop scripts or its two policy files (AC-0014). Mode: goal-based.
- A fresh process returns the open request's id, `status` writes nothing, and two kill points inside `report`, driven in a child process whose commit function the test replaces before it runs `main`, so no hook ships (AC-0015). Mode: TDD.

**Approach:** the fact checks of AC-0009 call the alignment lint as the new-spec script it is, from the pinned `scripts/` directory.

**Done when:** the T3 tests pass.

### T4: Review rounds and report classification

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_rounds.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_classifier.py`, `packs/core/tests/skills/new-spec/fixtures/`

**Tests:**
- Required roles with and without `security-boundary`, the request keys, and no later kind before each role reports (AC-0016). Mode: TDD over recorded reports.
- A stop for an unavailable reviewer, for each classifier reason code a recorded invalid report triggers, and for an indeterminate adjudication, each followed by a `next` that issues nothing; the indeterminate one is recorded and never clean (AC-0017). Mode: TDD.
- The classifier equals the real `review-artifact.py` on the recorded raw reports and adjudications (AC-0018). Mode: goal-based, the real script loaded by path under a unique module name.
- A clean report with no footer skips adjudication, a findings report and a clean report with a footer each issue one, the request names the exclude profile, and an adjudication reported with the reviewer's profile is refused (AC-0019). Mode: TDD.
- A reviewer equal to the author makes a weak round that is never converged (AC-0020), a sustained finding gives `revise` then a round, and a refuted-only round gives the `spec-approved` consent (AC-0021). Mode: TDD.

**Done when:** the T4 tests pass.

### T5: Consent requests, `park`, `gates` and the digest copy

**Depends on:** T4

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_consent.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_digest.py`

**Tests:**
- The cap after 3 rounds with the key absent and after a configured value, the weak gate after a weak round that is also the last the cap allows, and no further `review-round` or `revise` after either (AC-0022). Mode: TDD over recorded rounds.
- The open findings by identifier and file reference, and the three answers with the fixed text (AC-0023). Mode: TDD.
- A consent holds only fixed fields, and hostile reviewer text in each other request field is cut to 512 characters and marked untrusted (AC-0024). Mode: TDD with injected text.
- A repeated `next` on an open consent writes nothing, `park` records without a commit, `next` then refuses `parked`, `status` names it, and a fresh process reaches the same state (AC-0025). Mode: TDD.
- `gates` lists each parked consent with the fixed text, includes no reviewer or human text, and writes nothing (AC-0026). Mode: TDD.
- The digest copy equals the real `gate_digest` on the digest corpus, refusals included, with the real module loaded by path (AC-0027). Mode: goal-based.

**Done when:** the T5 tests pass and the end-to-end integration test passes.

### T6: Pins

**Depends on:** T5

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/.apm/skills/new-spec/supervisor.toml`, `packs/core/tests/skills/new-spec/test_spec_supervisor_pins.py`

**Tests:**
- The admission line holds the digests of every file under `scripts/` at any depth, the manifest and the policy file, and `pinned_files` equals the directory listing (AC-0028). Mode: goal-based.
- Every verb refuses `supervisor-changed` after a modified, added or removed script, a changed manifest and a changed policy file; a planted bytecode file never runs (AC-0029). Mode: TDD.
- The supervisor's pin code and the work supervisor's agree on a recorded corpus, the work supervisor's loaded by path (AC-0029). Mode: goal-based.

**Done when:** the T6 tests pass.

### T7: Release records, projections, eval, page 05 and closeout evidence

**Depends on:** T6

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `packs/core/.apm/skills/new-spec/evals/`, `.claude/skills/new-spec/`, `.agents/skills/new-spec/`, `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md`

**Tests:**
- `pack.toml` and `plugin.json` carry the same version, one patch above `main`; `python3 tools/changelog.py validate` passes; the self-host projections are committed and the drift check is clean; a `new-spec` eval case covers the supervisor path (AC-0030). Mode: goal-based.
- Page 05 says `start` writes the first ledger line, names the `review-cap` and `review-weak` consent gates, replaces the session moved-`HEAD` check with the protected-content check, and states the meanings of `park`, `gates` and the ended-run answer. Mode: goal-based, a read of the page against this spec.
- Closeout evidence, since pack tests run in no PR check: a targeted run of the new pack tests, `make precheck PRECHECK_ARGS="--with-tests --base origin/main"`, and one `test-corpus.yml` dispatch. Mode: goal-based.

**Done when:** the T7 checks pass, the page read finds no contradiction, and the three closeout runs are recorded in the verification ledger.

## Rollout

Delivery is one change set with no flag. Rollback removes the new files, since nothing calls the supervisor until `spec-supervisor-gates` and the `work-loop` driver line land. A core pack release carries it to adopters, ahead of the gates release. `work-supervisor.py` and its pin set are unchanged, so its pin is unaffected. No infrastructure or external system is involved.

## Risks

- The protected-content check may refuse a legitimate human approval edit made between steps. Mitigation: the approval-edit exception in the protected-set table, tested before and after convergence, and the consent request completes only through the answer record.
- The real work supervisor may refuse a spec directory that holds the ledger, or a git directory that holds a sibling store. Mitigation: AC-0013 runs against the real script in T3, before any later task builds on the layout.
- The copied pin code and gate digest may drift from the work supervisor's. Mitigation: the behavior comparisons of AC-0027 and AC-0029 on recorded corpora.
- The `weak` flag, the self-pin, agent-written files before a guard exists and a history rewrite between steps are accepted risks, recorded in the spec's Assumptions; the Brief 1 waiver covers identity only and none of them.

## Changelog
