# Plan: Spec supervisor core

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md` (request kinds, gates, resume); `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py` and its helpers `_supervisor_gates.py`, `_supervisor_admission.py`, `_loop_guards.py` (the analogue for verbs, attempts, refusals, `_spec_rel` and `safe_spec_path` confinement, the gate digest and the pin check, read and never edited or imported); `packs/core/.apm/skills/work-loop/references/pre-execute-review.md` and `scripts/review-artifact.py` (the review procedure the supervisor encodes); `packs/core/tests/skills/work-loop/` (how a supervisor's verbs, pins and kills are tested). Named uncertainty: the ledger, attempt and store paths are `implementation-discovered`.

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

Build `spec-supervisor.py` as a state machine that derives its state on every call from the ledger, git history and the open attempt, with `work-supervisor.py` as the analogue and never an import. The order is admission and confinement, then manifest, request shapes and roles, then the report path with the ledger and the step-commit check, then the protected-content check with the approval-edit exception and the reviewed-revision binding, then review rounds with the supervisor's own report classifier, then the consent requests with `park`, `gates` and the digest copy, then pins, then the release records and the page 05 update. The riskiest parts are the protected-content check, which must accept foreign commits yet refuse a protected-content change outside its allowed edit, and a kill inside `report`, so both land before any review logic.

## Constraints

- ADR-0162 D1 to D7: six commands, the manifest, `delegate-verb`, a gate or committed status at each boundary, no approval by a sibling, the round cap parked as a `consent` gate, the core pack owning the manifest.
- ADR-0163 D1 to D3: the script lives in `new-spec`, and the sibling shares only the command contract with `work-supervisor.py`; the scope check of AC-0019 cites it.
- ADR-0157 D3 and D4 govern this supervisor's `gates` listing (states `pending`, `stale`, `invalid`) and its refusal to approve: no verb, flag, default or record here approves. ADR-0157 D2 (the `park` that computes digests) governs the delegated `park` of `spec-supervisor-gates`; this supervisor's own `park` only records an open `consent` request and computes no digest of its own beyond the copy AC-0037 pins.
- `packs/AGENTS.md`: shipped pack content carries no internal citation (AC-0042); pack tests load modules under a unique name and never put `scripts/` on `sys.path`; a pack update bumps `pack.toml` and `plugin.json` together; a non-cosmetic update updates the eval harness (deferred to the gates release, which is the first to add text an eval can exercise, so this release adds no `SKILL.md` text); a shipped `.apm/` script that writes to stdout or stderr reconfigures both to UTF-8 before its first print.
- Spec `supervisor-manifest-contract`: the manifest conforms to `supervisor-manifest.v1`, and every request to `supervisor-request-envelope.v1`.
- Round counter and allowance: this spec reads the allowance (AC-0031) and owns nothing that changes it; `spec-supervisor-gates` owns every change to the allowance and the round total after a human decision.

## Construction tests

**Integration tests:** one end-to-end pack test drives `start`, a full review round, a `review-cap` consent and a `park` in a temporary repository, then runs the real installed `work-supervisor.py` `status`, `park` and `start` on the same spec directory with the ledger and a populated store present, including a `start` that admits an Approved pair (AC-0018). It uses the real script, never a stub.
**Manual verification:** none; the live trials belong to `spec-supervisor-gates`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| The supervisor, manifest and policy | T1 to T7 | the pack tests, the manifest validator | the manifest validates and every verb test is green |
| Page 05 | T9 | a read of the page against this spec | no page 05 sentence contradicts this spec |
| Release history | T8 | `tools/changelog.py validate` and the self-host drift check | the changelog validates and `make build-self` is clean |
| Decision rationale | none | ADR-0162, ADR-0163 and ADR-0157 already Accepted | none further |

## Design (LLD)

### Seam decisions

This spec owns each point below, and `spec-supervisor-gates` cites it.

- **Order of release.** This spec releases first with a manifest of five kinds. `spec-supervisor-gates` releases after it and amends the manifest, the exactly-five-kinds criteria, the consent-directly-after-convergence criterion and the no-further-round-after-the-cap criterion (the gates spec lists them). Each release's test asserts that the listed kinds equal the kinds a driven run returns at that release, and validates the manifest against `supervisor-manifest.v1`.
- **Consent issuance.** This spec issues the `spec-approved`, `review-cap` and `review-weak` consent requests. `spec-supervisor-gates` issues the `plan-approved` request and owns every behavior that sits after a consent: answers, decisions, the delegated commands and the allowance.
- **Consent digest.** A consent request's spec and plan digests are the work supervisor's gate digest, computed by a tested copy (the functions and constants AC-0037 names). The supervisor digests the `spec.md` and `plan.md` blobs at `HEAD`. The copy is compared with the real module, loaded by path under a unique name, in the pack tests, and again at closeout and in the corpus suite (`test-corpus.yml`), so drift in the pinned `gate_digest` is caught where the pack tests do not run. The `Status:` token does not move the digest and neither does a plan Changelog approval entry (`_drop_approval_entries` drops it and `canonical_contract` normalises the status token, `_supervisor_gates.py` lines 129 to 205 and `_loop_guards.py` lines 608 to 720), which is why a human's approval commit leaves a parked gate `pending`; only the spec's acceptance-criteria section is digested, which is why AC-0017 binds the whole pair.
- **`park` and `gates` of this supervisor.** `park` records an open `consent` request in the supervisor's own store, and `gates` lists those records. They never call `work-supervisor.py`. The record is `{run_id, request_id, gate, spec_digest, plan_digest, commit, state, parked_at}`, the fields the gates spec reads (the work supervisor's own record has no time, `_RECORD_KEYS` in `_supervisor_gates.py`). The real park of the approval gates is a `delegate-verb` request that `spec-supervisor-gates` adds.
- **Resume at a waiting gate.** An open `consent` request is returned by `next` with the same id and fields until it is parked. A parked request makes `next` refuse `parked`, and `status` names it. A fresh process re-derives this from the ledger, the open attempt and the store, so it reaches the same state. A matching answer record (owned by `spec-supervisor-gates`) is what lets `report` complete the request. No `consent` completes without one (`no-human-answer`).
- **Protected set and allowed edits.** The set is the criterion AC-0013; this table is a reading aid.

| Protected item | Visible to the commit check | Allowed edit |
| --- | --- | --- |
| The ledger | yes | the supervisor's step commit, one appended line (AC-0009) |
| `spec-policy.json`, `supervisor.toml`, pinned scripts | yes | none (AC-0013, AC-0039) |
| Preamble `Status:` lines, plan approval-entry lines | yes | the edit of AC-0014, in the states it names |
| Attempt records and the store | no, they live outside commits | a supervisor verb only; a violation is an accepted risk |
| The answers file and the hand-off record | yes | added by `spec-supervisor-gates` with the edit it states |

Traces to: AC-0004, AC-0013, AC-0014, AC-0015, AC-0031, AC-0034, AC-0035, AC-0036, AC-0037.

Owned by: T2, T4, T6

### Interfaces & contracts

Verbs: `start <spec-dir>`, `next <spec-dir>`, `report <spec-dir> <result-file>`, `status <spec-dir>`, `park <spec-dir>` and `gates`. Output is JSON on stdout; a request is `{"request": {...}}`, a refusal is `{"refusal": {"code", "owner", "detail"}}`, and an ended run answers `{"terminal": true}`, as `work-supervisor.py` does. Traces to: AC-0001, AC-0004, AC-0005, AC-0006, AC-0034, AC-0036.

- Refusal codes the sources fix are used as given: `request-consumed`, `supervisor-changed`, `no-human-answer`, `parked`, `default-branch-refused` and `checkout-dirty`. This spec adds `default-branch-unknown`, `detached-head`, `ledger-foreign-append`, `protected-content-changed`, `reviews-not-ignored` and `report-replayed`. Others are chosen at build time as lowercase-hyphen names.
- The kind-to-stage pairing, the five kinds and the six stages are the criterion AC-0005. `delegating` is reserved for `delegate-verb`, which the gates release adds, and `terminal` is what `status` reports for an ended run.
- Per-kind keys: `review-round` names `role`, `exclude_profile` and the derived report path; `adjudicate` names `exclude_profile`, the round and the derived report path; `revise` names the sustained findings as identifier, checked file reference and a bounded `untrusted` title; `consent` names `gate` and the spec and plan digests, and for `review-cap` and `review-weak` the open findings and the three answers with the fixed consequence text of AC-0032.
- The result file is `{"request_id", "facts"}` with the closed fact sets of AC-0010. The verified facts (classification, finding count, `weak`, identifiers) are computed from the report file and the ledger, never taken from `facts`. `agent_definition` is the only controller text that reaches the ledger, and it passes the identifier grammar of AC-0010 before it can reach a later `exclude_profile`.
- `spec-policy.json` holds `max_review_rounds` (default 3) and nothing else a human does not own. The manifest sits at the skill root and lists five kinds with these modes: `author-spec`, `review-round`, `adjudicate` and `revise` list `headless`, `attach` and `session`, and `consent` lists `human` only. `pinned_files` is derived from the directory listing in the test and holds every file under `scripts/` except `__pycache__` directories (which already hold the two `new-spec` lint scripts), `supervisor.toml` and `spec-policy.json`.

Owned by: T1, T2, T3, T5

### Data & schema

The ledger is append-only JSON lines in the spec directory, one line per step, committed with the step's files. A line holds the step kind, request id, run id, the `previous` recorded commit, the facts the step verified (classification, finding count, identifiers, file references, author and reviewer agent definitions, `weak`, the sha256 of each classified report), the pair identity of AC-0017 for the kinds that carry it, the role set after the step, and, in the admission line only, the pin digests. The ledger path, the attempt-record layout and the store path are `implementation-discovered`; the store root is a directory beside, never inside, `<git-dir>/agentbundle-supervisor/`, because the work supervisor's preflight lists every `run-<hex>` directory there and refuses all verbs on a malformed one. Traces to: AC-0008, AC-0009, AC-0012, AC-0017, AC-0018, AC-0024, AC-0038.

Owned by: T3, T4

### State & control flow

State is derived on every call from the ledger, git history and the open attempt. A request id is a function of the run id and the ledger position, so a fresh clone with no attempt record re-issues the same id. Traces to: AC-0006, AC-0020, AC-0021, AC-0034.

- `next` opens an attempt and returns the request; an open request is returned again unchanged.
- `report` runs, in order: id check, result bounds and the closed fact set, ledger append-only check, step-commit and protected-content check since the last recorded commit, working tree and index check against the kind's allowed set, then the kind's fact checks, then writes the files, the ledger line and one commit, then closes the attempt. A kill before the commit leaves an open attempt, uncommitted allowed files and one appended ledger line that a repeated `report` completes (AC-0016 allows exactly that state); a kill after the commit leaves a commit that the next verb adopts by closing the attempt, after the checks of AC-0009.
- Step order: `author-spec` when no review and no author is recorded; then one `review-round` per required role; `adjudicate` after a `findings` or footer report; `revise` then a further round after a sustained finding while the round total is below the allowance; the `spec-approved` consent on convergence of the reviewed revision, the `review-weak` consent after a weak round, the `review-cap` consent when the round total reaches the allowance. The `plan-approved` consent and every answer-driven transition belong to `spec-supervisor-gates`.
- Reviewed revision: each step line records the pair identity. At every `next` and `report` the supervisor compares the identity of the pair at `HEAD` with the newest recorded one; a difference that no `author-spec` or `revise` step made opens a further round for the new revision and voids earlier convergence (AC-0017). The required role set only grows (AC-0007).
- The round counter after a human decision is not set here. `spec-supervisor-gates` owns the allowance and the round total after each decision, and this spec reads them.

Owned by: T2, T3, T4, T5

### Behavior & rules

Review follows `pre-execute-review.md`. A raw report is classified by the supervisor's own function: `findings` when a finding line parses, `clean` when the sentinel line appears exactly once with only blank lines or a `## Not checked` footer around it, otherwise `invalid` with a reason code from the closed set the real script uses. A `clean` report with the footer is adjudicated, as the reference says. An adjudication classifies as `clean` for refuted-only or the exact clean result, `findings` for a sustained one, and `invalid` with the reason code the real script returns for every other shape (AC-0025 lists them), which stops the run. A round is `weak` when any reviewer's reported agent definition equals the author's. The equivalence corpus is a set of recorded raw reports and adjudications checked into the pack tests, with the real script's output for each computed at test time; the comparison covers the classification, the reason code and the finding count. A finding's file reference is admitted only when it is a repository-relative path to an existing regular file followed by an integer line; otherwise it is dropped. A run that stops is recorded `terminal` with its reason. Traces to: AC-0022 to AC-0032.

Owned by: T5

### Failure, edge cases & resilience

Admission refusals write nothing. `report` refuses each case of AC-0009, AC-0010, AC-0012, AC-0013, AC-0015 and AC-0016, and each writes nothing. A foreign commit that leaves protected content alone and adds no ledger line is accepted, so a user's or the work supervisor's own commit never wedges a run. A foreign commit that adds ledger content is judged by AC-0009; the forged one-line append that passes it is an accepted risk in the spec. Traces to: AC-0002, AC-0003, AC-0009, AC-0010, AC-0012, AC-0013, AC-0015, AC-0016, AC-0020.

Owned by: T1, T3, T4

### Quality attributes (NFRs)

Security posture. Every path is confined with a link-refusing check before any read or write and opened without following links, modelled on `_spec_rel` and `safe_spec_path`. Pins hash the whole `scripts/` tree and load nothing before the pin check passes, with bytecode isolated as the work supervisor does (`__pycache__` is never pinned and never trusted), so a planted `.pyc` cannot run; the spawned alignment lint runs with a scrubbed environment, `-I` and bytecode writing off. Reviewer, author and human text is untrusted in every output field, bounded and neutralised as AC-0033 states. Traces to: AC-0003, AC-0011, AC-0033, AC-0038, AC-0039.

Owned by: T1, T3, T6, T7

## Tasks

### T1: Admission and confinement

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_admission.py`

**Tests:**
- Admission writes one ledger line in one commit that holds the run id, role set, pin digests and pair identity (AC-0001). Mode: TDD over a temporary repository.
- One refusal per member of the AC-0002 set, each writing nothing: the default branch, an unknown default branch, a detached `HEAD`, a modified, a staged and an untracked non-ignored path, a missing `spec.md`, a missing `plan.md`, a second `start` (the ledger, pins and store unchanged), a `max_review_rounds` of 0, -1, `"3"` and 1.5, a dot-file under `scripts/`, and a manifest whose `pinned_files` differs; plus the green cases: an absent key admits with 3, and a value of 1 admits (AC-0002). Mode: TDD.
- One parametrized list per verb for AC-0003: path-shape cases (absolute, `..`, `.`, backslash, a segment starting with `-`, a path inside the git directory), a symlink and a regular-file component, a symlink and a non-regular `spec.md`, `plan.md` and ledger, and a link swapped in after the check and before the open (AC-0003). Mode: TDD.

**Approach:** copy the shape of `_spec_rel`, `safe_spec_path` and the plain-file reader of `work-supervisor.py` into the new script; do not import them.

**Done when:** the T1 tests pass.

### T2: Manifest, policy file, request shapes and roles

**Depends on:** T1, spec:supervisor-manifest-contract/T2

**Touches:** `packs/core/.apm/skills/new-spec/supervisor.toml`, `packs/core/.apm/skills/new-spec/spec-policy.json`, `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_requests.py`

**Tests:**
- The manifest validates against the manifest schema with the validator the manifest-contract tests use, and the listed kinds equal the kinds a driven run returns (AC-0004). Mode: goal-based.
- Each request validates against the envelope schema, its kind and stage are in their sets and paired as the criterion states, and a request with an unlisted kind or stage is rejected by the test's own check (AC-0005). Mode: TDD.
- `next` issues `author-spec` only for a pair with no review and no author, a reported author is recorded, and a reported `human` author is recorded as given (AC-0006). Mode: TDD.
- The role set with and without `security-boundary`, with `destructive`, after a `revise` that adds a trigger (role added) and after one that removes `security-boundary` (role kept) (AC-0007). Mode: TDD.

**Done when:** the T2 tests pass.

### T3: Report, ledger, step commits, working tree, resume and coexistence

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_ledger.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_resume.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_integration.py`

**Tests:**
- One commit and one ledger line per step (AC-0008). Mode: TDD with real commits.
- A foreign commit that appends one well-formed line, one that carries the open request id, one that appends two lines, one whose `previous` is wrong, one that adds a file outside the kind's path set, and one that changes no ledger are each decided as AC-0009 states; the first two are refused only where AC-0009 refuses them, and the residue is the accepted risk (AC-0009). Mode: TDD.
- One refusal per member of the AC-0010 set: a wrong id, a second report, a symlink, a non-regular, a 16 MiB plus one byte, a non-UTF-8, a repeated-key and a 17-level-deep result file, an unknown, a repeated and a missing-per-kind fact key, an `agent_definition` of 65 characters, with a newline and with a path, a `facts` that claims a classification, and a `consent` result with no answer record (`no-human-answer`) (AC-0010). Mode: TDD.
- An `author-spec` report is refused on a wrong spec status, a wrong plan status and a failing alignment lint, and the lint runs with the scrubbed environment (AC-0011). Mode: TDD.
- A line edited, removed, reordered and inserted before the last line each make every verb refuse (AC-0012). Mode: TDD.
- One working-tree and index case per kind, an untracked non-ignored file, a `revise` step that edits `Status:`, a kill between the ledger write and the commit followed by a repeated `report` that completes, and the same state refused when the appended line does not match the open request (AC-0016). Mode: TDD.
- The integration test runs the real installed `work-supervisor.py` `status`, `park` and `start` beside a populated store and a ledger, including a `start` that admits an Approved pair, and compares each answer with the answer without them (AC-0018). Mode: goal-based, integration.
- A fresh process returns the open request's id, and two kill points inside `report` are driven in a child process whose commit function the test replaces before it runs `main`, so no hook ships (AC-0020). `status` writes no file, store record or commit (AC-0021). Mode: TDD.

**Approach:** the fact checks of AC-0011 call the alignment lint as the new-spec script it is, from the pinned `scripts/` directory, through a child process started with `-I -B` and an environment reduced to what the lint needs.

**Done when:** the T3 tests pass.

### T4: Protected content, the approval-edit exception and the reviewed revision

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_protected.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_revision.py`

**Tests:**
- A foreign commit that changes no protected item is accepted, and so is one by the work supervisor (it adds `delivery/approvals.jsonl`); one commit per protected item (the ledger, `spec-policy.json`, `supervisor.toml`, a pinned script, a `Status:` line outside the exception) is refused `protected-content-changed` (AC-0013). Mode: TDD.
- The approval edit is accepted in each named state: an open, a parked and a completed `spec-approved` consent, a `plan-approved` consent, and after an approve answer to `review-cap` and to `review-weak` (the cap path has no converged round), each as an add, a remove and a change of a `Status:` or approval-entry line (AC-0014). Mode: TDD.
- It is refused before any consent, after a later ledger line, with a second `Status:` line inserted, with an approval entry outside the region, with a wrapped entry, and with any other byte changed (AC-0015). Mode: TDD.
- An edit to the Risk triggers, an Agent Rule and an accepted risk outside the acceptance-criteria section after convergence voids it and `next` opens a further round counted in the total; a `review-round` worker that edits `spec.md` and commits is refused by AC-0016 and, if its commit lands, voids convergence; a consent issues only when the identity equals the converged round's, and an approval-only commit leaves the identity unchanged (AC-0017). Mode: TDD.

**Done when:** the T4 tests pass.

### T5: Review rounds, report paths and classification

**Depends on:** T4

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_rounds.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_classifier.py`, `packs/core/tests/skills/new-spec/fixtures/`

**Tests:**
- Required roles with and without `security-boundary`, the request keys, and no later kind before each role reports (AC-0022). Mode: TDD over recorded reports.
- A request whose path differs from the derived one is refused, and `next` refuses `reviews-not-ignored` in a repository where `.context/reviews` is not ignored (AC-0023). A report file that is a link, a non-regular file or 1 MiB plus one byte is refused, and a second report with the same bytes is refused `report-replayed` (AC-0024). Mode: TDD.
- A stop for an unavailable reviewer, an unavailable adjudicator, each classifier reason code a recorded invalid raw report triggers, and each of the seven adjudication codes of AC-0025, each followed by a `next` that issues nothing; the indeterminate and invalid adjudications are recorded as such and never clean (AC-0025). Mode: TDD.
- The classifier equals the real `review-artifact.py` on the recorded raw reports and adjudications, reason codes included (AC-0026). Mode: goal-based, the real script loaded by path under a unique module name.
- A clean report with no footer skips adjudication, a findings report and a clean report with a footer each issue one, the request names the exclude profile, and an adjudication reported with the reviewer's profile is refused (AC-0027). Mode: TDD.
- A reviewer equal to the author makes a weak round that is never converged (AC-0028). A sustained finding below the allowance gives `revise` then a round (AC-0029). A refuted-only round gives the `spec-approved` consent (AC-0030). Mode: TDD.
- The cap after 3 rounds with the key absent and after a configured value, a weak round that is also the last the allowance permits (`review-weak` wins), a non-weak non-converged round at the allowance (`review-cap`, no `revise`), and no further `review-round` or `revise` after either (AC-0031). Mode: TDD over recorded rounds.

**Done when:** the T5 tests pass.

### T6: Consent requests, `park`, `gates` and the digest copy

**Depends on:** T5

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_consent.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_digest.py`

**Tests:**
- The open findings by identifier and checked file reference (a hostile reference is dropped), and the three answers with the fixed text that states the meaning of each (AC-0032). Mode: TDD.
- A consent holds only fixed fields, and hostile reviewer text carrying control, escape, newline and bidirectional characters in each other request field, a refusal detail, a `status` field and relayed lint output is cut to 512 characters, neutralised and marked untrusted (AC-0033). Mode: TDD with injected text.
- A repeated `next` on an open consent writes nothing, `next` on a parked request refuses `parked`, `status` names it, and a fresh process reaches the same state (AC-0034). Mode: TDD.
- `park` records the fields of AC-0035 without a commit or tracked-file change, with the park time from the supervisor's clock (AC-0035). Mode: TDD.
- `gates` lists each parked consent with its state `pending`, `stale` after an edit and `invalid` after a damaged record, includes no reviewer or human text, and writes nothing (AC-0036). Mode: TDD.
- The digest copy equals the real `gate_digest` on the digest corpus of AC-0037, refusals included, with the real module loaded by path; the same test runs in the corpus suite and at closeout (AC-0037). Mode: goal-based.

**Done when:** the T6 tests pass and the end-to-end integration test passes.

### T7: Pins

**Depends on:** T6

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/.apm/skills/new-spec/supervisor.toml`, `packs/core/tests/skills/new-spec/test_spec_supervisor_pins.py`

**Tests:**
- The admission line holds the digests of every file under `scripts/` at any depth except `__pycache__`, the manifest and the policy file, and `pinned_files` equals the directory listing in portable form (AC-0038). Mode: goal-based.
- Every verb that reads an admission line refuses `supervisor-changed` after a modified, added or removed script, a changed manifest and a changed policy file; `start`, `gates` and `answer` compare as AC-0039 states; a planted bytecode file never runs; a `__pycache__` directory is neither pinned nor a refusal; a dot-file added later is `supervisor-changed` (AC-0039). Mode: TDD.
- The supervisor's pin code and the work supervisor's agree on a recorded corpus, the work supervisor's loaded by path (AC-0040). Mode: goal-based.

**Done when:** the T7 tests pass.

### T8: Release records, projections and closeout evidence

**Depends on:** T7

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `.claude/skills/new-spec/`, `.agents/skills/new-spec/`

**Tests:**
- `pack.toml` and `plugin.json` carry the same version, one patch above `main`; `python3 tools/changelog.py validate` passes; the self-host projections are committed and the drift check is clean (AC-0041). Mode: goal-based.
- A scan of the lines this change adds under `packs/`, using the diff against `origin/main`, finds no record citation (AC-0042). Mode: goal-based; the check reads added lines only, so it is a closeout step and not a standing pack test.
- The diff against `origin/main` holds no work-loop pin-set path or projection (AC-0019). Mode: goal-based; a closeout step, because after merge the same diff is empty.
- Closeout evidence, since pack tests run in no PR check: a targeted run of the new pack tests, `make precheck PRECHECK_ARGS="--with-tests --base origin/main"`, and one `test-corpus.yml` dispatch that runs the digest equivalence of AC-0037. Mode: goal-based.

**Done when:** the T8 checks pass and the closeout runs are recorded in the verification ledger.

### T9: Page 05 update

**Depends on:** T8

**Touches:** `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md`

**Tests:**
- Page 05 is edited so that each point below reads as this spec states it. Mode: goal-based, a read of the page against this spec.
  1. Section 5, the spec-state row: `start` writes the first ledger line (not the first `next`), and the rollback column says a step commit is never reverted, because the ledger is append-only; a human who must undo a run removes the ledger in a commit.
  2. Section 5, the closing sentence: a partial migration leaves a ledger that ends early, and the supervisor re-derives from the ledger and git history, not from headers and statuses.
  3. Section 3, "Guard in a session", and section 4, the `--known-commits` row: the sibling's check is a protected-content check that accepts any commit leaving protected content alone, not a moved-`HEAD` check; `--known-commits` stays provisional for `ferryman`.
  4. Sections 2 and 3: `review-cap` and `review-weak` are consent gates beside `spec-approved`; the fixed meaning of their three answers; and the single stage vocabulary `authoring`, `reviewing`, `revising`, `awaiting-human`, `delegating`, `terminal`.
  5. Section 3, `status` and `parked`: this supervisor's own `park` records an open consent request in its store with the fields AC-0035 lists, `gates` lists them with the states AC-0036 names, and a stopped and an ended run are one `terminal` state with a recorded reason.
  6. Sections 3 and 7, review independence: the `weak` control rests on a self-reported agent definition and the supervisor does not prove that a review ran, so the "100% of rounds record a distinct profile" target reads as a flag, not a guarantee.
  7. Section 3, the reviewed revision: each round records the pair identity, a content change outside an `author-spec` or `revise` step voids convergence, the role set never shrinks, and the infra-flavored security role is required for a destructive spec.
  8. Section 8, the last paragraph: the pin set excludes `__pycache__`, treats a dot-file under `scripts/` as a refusal, and a run pinned under another version recovers by reinstalling that version or removing the ledger in a human commit.
  9. Section 3, "Approval in a session": the protected-content check opens an exception for the human's approval and revert commits in the states AC-0014 names, and the forged-line and agent-written-approval paths are accepted risks until the guard and scribe.

**Done when:** the page read finds no contradiction with this spec.

## Rollout

Delivery is one change set with no flag. Rollback removes the new files, since nothing calls the supervisor until `spec-supervisor-gates` and the `work-loop` driver line land. A core pack release carries it to adopters, ahead of the gates release. `work-supervisor.py` and its pin set are unchanged, so its pin is unaffected. No infrastructure or external system is involved.

## Risks

- The protected-content check may refuse a legitimate human approval edit made between steps. Mitigation: the approval-edit exception of AC-0014, tested in every state it names, including the cap and weak approve paths, and the consent request completes only through the answer record.
- The real work supervisor may refuse a spec directory that holds the ledger, or a git directory that holds a sibling store. Mitigation: AC-0018 runs against the real script in T3, before any later task builds on the layout.
- The copied pin code and gate digest may drift from the work supervisor's. Mitigation: the behavior comparisons of AC-0037 and AC-0040 on recorded corpora, run in the pack tests, at closeout and in the corpus suite.
- The forged ledger line, the agent-written approval, the unproven review, the unseen attempt records, the self-pin and a history rewrite are accepted risks, recorded in the spec's Assumptions; the Brief 1 waiver covers identity only and none of them.

## Changelog
