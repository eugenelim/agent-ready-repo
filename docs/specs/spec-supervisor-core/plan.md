# Plan: Spec supervisor core

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md` (request kinds, gates, resume); `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py` and its helpers `_supervisor_gates.py`, `_supervisor_admission.py`, `_loop_guards.py` (the analogue for verbs, attempts, refusals, `_spec_rel` and `safe_spec_path` confinement, the gate digest and the pin check, read and never edited or imported); `packs/core/.apm/skills/work-loop/references/pre-execute-review.md` and `scripts/review-artifact.py` (the review procedure the supervisor encodes); `packs/core/tests/skills/work-loop/` (how a supervisor's verbs, pins and kills are tested). Named uncertainty: the ledger, attempt and store paths are `implementation-discovered`.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (`Agent Rules`, `Testing Strategy`, `Acceptance Criteria` and accepted
> risks under `Assumptions`). A change
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

- eugenelim holds every owner role, including repository, contract, review and risk ownership.

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

- **Order of release.** This spec releases first with a manifest of five kinds. `spec-supervisor-gates` releases after it and amends the manifest, the core criteria named in gates AC-0027, with matching core tests and the core spec in that amendment task’s Touches. Core extension points are AC-0004, AC-0005, AC-0010, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0029, AC-0030, AC-0031, AC-0032, AC-0034 and AC-0044. Each release's test asserts that the listed kinds equal the kinds a driven run returns at that release, and validates the manifest against `supervisor-manifest.v1`.
- **Consent issuance.** This spec issues the `spec-approved`, `review-cap` and `review-weak` consent requests and owns their fixed `unreviewed` marker. After voiding at the allowance, the fresh cap consent binds the current revision with `unreviewed: true`; all other consents bind the last reviewed revision with `unreviewed: false`. `spec-supervisor-gates` issues the `plan-approved` request and owns every behavior that sits after a consent: answers, decisions, the delegated commands and the allowance.
- **Consent digest.** A consent request's spec and plan digests are the work supervisor's gate digest, computed by a tested copy (the closure in Digest copy and equivalence corpus). The supervisor digests the `spec.md` and `plan.md` blobs at `HEAD`. The copy is compared with the real module, loaded by path under a unique name, in the pack tests, and again at closeout and in the corpus suite (`test-corpus.yml`), so drift in the pinned `gate_digest` is caught where the pack tests do not run. The `Status:` token does not move the digest and neither does a plan Changelog approval entry (`_drop_approval_entries` drops it and `canonical_contract` normalises the status token, `_supervisor_gates.py` lines 129 to 205 and `_loop_guards.py` lines 608 to 720), which is why a human's approval commit leaves a parked gate `pending`; only the spec's acceptance-criteria section is digested, which is why AC-0017 binds the whole pair.
- **`park` and `gates` of this supervisor.** `park` records an open `consent` request in the supervisor's own store, and `gates` lists those records. They never call `work-supervisor.py`. The record is `{run_id, request_id, gate, spec_dir, spec_digest, plan_digest, commit, state, parked_at, unreviewed}`, the fields the gates spec reads (the work supervisor's own record has no time, `_RECORD_KEYS` in `_supervisor_gates.py`). The real park of the approval gates is a `delegate-verb` request that `spec-supervisor-gates` adds.
- **Resume at a waiting gate.** For an unchanged pair, AC-0034 governs the waiting response. AC-0044 takes precedence when the pair changes. A fresh process re-derives this from the ledger, the open attempt and the store, so it reaches the same state. A matching answer record (owned by `spec-supervisor-gates`) is what lets `report` complete the request. No `consent` completes without one (`no-human-answer`).
- **Protected set and allowed edits.** The set is the criterion AC-0013; this table is a reading aid.

| Protected item | Visible to the commit check | Allowed edit |
| --- | --- | --- |
| The ledger | yes | the supervisor's step commit, one appended line (AC-0009) |
| `spec-policy.json`, `supervisor.toml`, pinned scripts | yes | none (AC-0013, AC-0039) |
| Preamble `Status:` lines, plan approval-entry lines | yes | the edit of AC-0014, in the states it names |
| Attempt records and the store | no, they live outside commits | a supervisor verb only; observable changes refuse under AC-0013, while undetectable forgery or deletion remains an accepted risk |
| The answers file and the hand-off record | yes | gates AC-0005 owns their rules; core adds no record contract |

Traces to: AC-0004, AC-0013, AC-0014, AC-0015, AC-0031, AC-0034, AC-0035, AC-0036, AC-0037.

Owned by: T2, T4, T6

### Digest copy and equivalence corpus

The copy carries `gate_digest`, `_drop_approval_entries`, `_APPROVAL_ENTRY_RE`, `_unsafe`, `_LINE_SEPARATORS`, `_INVISIBLE_CAP`, `canonical_contract`, and the helpers they call from the lint scripts (`is_hidden_char`, `_RUN_CHARS`, `_MAX_ADJACENT_INVISIBLE`, `invisible_budget`, `_HTML_COMMENT_RE`, `_SECTION_HEADING_RE`, `_STATUS_RE`, `extract_status_token`); the corpus holds a plain file, an approval-entry line with each optional suffix and the final period, a wrapped entry, a last exact `## Changelog` among several, a heading or fence after it, blank-run folding, dropped trailing blanks, trailing whitespace on the heading, a changed `Status:` token, a comment before `Status:`, checkbox normalisation in the acceptance section and plan-wide, a fence inside the acceptance section, a lowercase `criteria` heading, edits outside the acceptance section, a missing and a repeated acceptance heading, CRLF, a lone CR, a BOM, a NUL, NFC and NFD forms, no final newline, invalid UTF-8, a hidden-character run at and over the budget, a zero-width joiner run, and 200 seeded generated inputs.

The copy closure includes everything `gate_digest` reaches, including later upstream dependencies. The corpus compares successful digests and refusal outcomes against the real implementation. Traces to: AC-0037.

Owned by: T6

### Interfaces & contracts

Verbs: `start <spec-dir>`, `next <spec-dir>`, `report <spec-dir> <result-file>`, `status <spec-dir>`, `park <spec-dir>` and `gates`. Output is JSON on stdout; a request is `{"request": {...}}`, a refusal is `{"refusal": {"code", "owner", "detail"}}`, and an ended run answers `{"terminal": true}`, as `work-supervisor.py` does. Traces to: AC-0001, AC-0004, AC-0005, AC-0006, AC-0034, AC-0036.

- Refusal codes the sources fix are used as given: `request-consumed`, `supervisor-changed`, `no-human-answer`, `parked`, `default-branch-refused` and `checkout-dirty`. This spec adds `default-branch-unknown`, `detached-head`, `ledger-altered`, `protected-content-changed`, `reviews-not-ignored` and `report-replayed`. The closed invalid-result set is AC-0010; gates AC-0027 extends that set and the per-kind facts and paths in its release.
- The kind-to-stage pairing, the five kinds and the six stages are the criterion AC-0005. `delegating` is reserved for `delegate-verb`, which the gates release adds, and `terminal` is what `status` reports for an ended run.
- Per-kind keys: `review-round` names `role`, `exclude_profile` and the derived report path; `adjudicate` names `exclude_profile`, the round and the derived report path; `revise` names the sustained findings as identifier, checked file reference and a bounded `untrusted` title; `consent` names `gate`, the spec and plan digests and the fixed `unreviewed` marker, and for `review-cap` and `review-weak` the open findings and the applicable answer set with the fixed consequence text of AC-0032. An unreviewed cap offers only request-changes or reject; its text states that the current revision is unreviewed.
- The result file is `{"request_id", "facts"}` with the closed fact sets of AC-0010. The verified facts (classification, finding count, `weak`, identifiers) are computed from the report file and the ledger, never taken from `facts`. `agent_definition` passes AC-0010 before it can reach a later `exclude_profile`; `outcome` uses `{available, unavailable}`. Classification, count and weakness follow AC-0045.
- `spec-policy.json` holds `max_review_rounds` (default 3) and nothing else a human does not own. The manifest sits at the skill root and lists five kinds with these modes: `author-spec`, `review-round`, `adjudicate` and `revise` list `headless`, `attach` and `session`, and `consent` lists `human` only. `pinned_files` is derived from the directory listing in the test and holds every file under `scripts/` except `__pycache__` directories (which already hold the two `new-spec` lint scripts), `supervisor.toml` and `spec-policy.json`.

Owned by: T1, T2, T3, T5

### Data & schema

The ledger is append-only JSON lines in the spec directory, one line per step, committed with the step's files. A line holds the step kind, request id, run id, the `previous` recorded commit, the facts the step verified (classification, finding count, identifiers, file references, author and reviewer agent definitions, `weak`, the sha256 of each classified report), the pair identity of AC-0017 for the kinds that carry it, the role set after the step, and, in the admission line only, the pin digests. The ledger path, the attempt-record layout and the store path are `implementation-discovered`; the store root is a directory beside, never inside, `<git-dir>/agentbundle-supervisor/`, because the work supervisor's preflight lists every `run-<hex>` directory there and refuses all verbs on a malformed one. Traces to: AC-0008, AC-0009, AC-0012, AC-0017, AC-0018, AC-0024, AC-0038.

Owned by: T3, T4

### State & control flow

State is derived on every call from the ledger, git history and the open attempt. A request id is a function of the run id and the ledger position, so a fresh clone with no attempt record re-issues the same id. Traces to: AC-0006, AC-0020, AC-0021, AC-0034.

- `next` opens an attempt for a non-consent request and returns it; AC-0034 governs waiting consents, subject to AC-0044.
- `report` runs, in order: pin checks, ledger checks, protected-content checks with AC-0013 precedence, id check, result bounds and the closed fact set, working tree and index check against the kind's allowed set, then the kind's fact checks, then writes the files, the ledger line and one commit, then closes the attempt. A kill before the commit leaves an open attempt, uncommitted allowed files and one appended ledger line that a repeated `report` completes only when byte-identical to its recomputed line (AC-0016); replay and consumed-request checks read the ledger at the last recorded commit; a kill after the commit leaves a commit that the next verb adopts by closing the attempt, after the checks of AC-0009.
- Step order: `author-spec` when no review and no author is recorded; then one `review-round` per required role; `adjudicate` after a `findings` or footer report; `revise` then a further round after a sustained finding while the round total is below the allowance; the `spec-approved` consent on convergence of the reviewed revision, the `review-weak` consent after a weak round, the `review-cap` consent when the round total reaches the allowance. The `plan-approved` consent and every answer-driven transition belong to `spec-supervisor-gates`.
- Reviewed revision: AC-0017 binds each consent to the last round or, after voiding at the allowance, the current revision marked `unreviewed: true`, AC-0043 prevents mixed-identity convergence, and AC-0044 owns voiding precedence. The pair identity is bound when a request issues and compared before `report` records it. The role set is recomputed from the pair at `HEAD` whenever a round opens and never shrinks (AC-0007).

- The round counter after a human decision is not set here. `spec-supervisor-gates` owns the allowance and the round total after each decision, and this spec reads them.

Owned by: T2, T3, T4, T5

### Behavior & rules

Review follows `pre-execute-review.md`. A raw report is classified by the supervisor's own function: `findings` when a finding line parses, `clean` when the sentinel line appears exactly once with only blank lines or a `## Not checked` footer around it, otherwise `invalid` with a reason code from the closed set the real script uses. A `clean` report with the footer is adjudicated, as the reference says. An adjudication classifies as `clean` for refuted-only or the exact clean result, `findings` for a sustained one, and `invalid` with the reason code the real script returns for every other shape (AC-0025 lists them), which stops the run. A round is `weak` when any reviewer's reported agent definition equals the author's. The equivalence corpus is a set of recorded raw reports and adjudications checked into the pack tests, with the real script's output for each computed at test time; the comparison covers the classification, the reason code and the finding count. A finding’s file reference follows AC-0032’s confined grammar and bounded line number; invalid references are dropped. A run that stops is recorded `terminal` with its reason. Traces to: AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, AC-0029, AC-0030, AC-0031, AC-0032, AC-0043, AC-0045.

Owned by: T5

### Failure, edge cases & resilience

Admission refusals write nothing. `report` refuses each case of AC-0009, AC-0010, AC-0012, AC-0013, AC-0015 and AC-0016, and each writes nothing. First-parent history decides merge commits. Pinned-file restoration compares the net change since the last recorded commit, so reinstalling the pinned version restores the run. A foreign commit that leaves protected content alone and adds no ledger line is accepted, so a user's or the work supervisor's own commit never wedges a run. A foreign commit that adds ledger content is judged by AC-0009; the forged one-line append that passes it is an accepted risk in the spec. Traces to: AC-0002, AC-0003, AC-0009, AC-0010, AC-0012, AC-0013, AC-0015, AC-0016, AC-0020.

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
- One refusal per member of the AC-0002 set, each writing nothing: the default branch, an unknown default branch, a detached `HEAD`, a modified, a staged and an untracked non-ignored path, a missing `spec.md`, a missing `plan.md`, an untracked or ignored pair file or ledger, removal of an earlier run’s ledger followed by attempted role shrink, allowance reset or bypass of an unanswered cap/weak gate, a second `start` (the ledger, pins and store unchanged), a `max_review_rounds` of 0, -1, `"3"` and 1.5, a dot-file under `scripts/`, and a manifest whose `pinned_files` differs; plus the green cases: an absent key admits with 3, and a value of 1 admits, and a prior answer record authorises the corresponding historical transition (AC-0002). Mode: TDD.
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
- The role set with and without `security-boundary`, with `destructive`, at a round opening after a committed trigger addition (role added) and after a commit that removes `security-boundary` (role kept) (AC-0007). Mode: TDD.

**Done when:** the T2 tests pass.

### T3: Report, ledger, step commits, working tree, resume and coexistence

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_ledger.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_resume.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_integration.py`

**Tests:**
- One commit and one ledger line per step (AC-0008). Mode: TDD with real commits.
- A foreign commit that appends one well-formed line, one that carries the open request id, one that appends two lines, one whose `previous` is wrong, one that adds a file outside the kind's path set, and one that changes no ledger are each decided as AC-0009 states; the first two are refused only where AC-0009 refuses them, and the residue is the accepted risk (AC-0009). Mode: TDD.
- One refusal per member of the AC-0010 set: a wrong id, a second report, a symlink, a non-regular, a 16 MiB plus one byte, a non-UTF-8, a repeated-key and a 17-level-deep result file, an unknown, a repeated and a missing-per-kind fact key, an `agent_definition` of 65 characters, with a newline and with a path, a `facts` that claims a classification, and a `consent` result with no answer record (`no-human-answer`) (AC-0010). Mode: TDD. Both reviewer and adjudicator results exercise `available`, `unavailable`, missing outcome and an unknown outcome; supplied classifications, counts and weakness never determine recorded values (AC-0045).
- An `author-spec` report is refused on a wrong spec status, a wrong plan status and a failing alignment lint, and the lint runs with the scrubbed environment (AC-0011). Mode: TDD.
- A line edited, removed, reordered and inserted before the last line each make every verb refuse `ledger-altered` after pin precedence (AC-0012). Mode: TDD.
- One working-tree and index case per kind, an untracked non-ignored file, a `revise` step that edits `Status:`, a kill between the ledger write and the commit followed by a repeated `report` that completes, and the same state refused when the appended line matches the request but differs by one byte from the line recomputed from the report and committed ledger (AC-0016). Mode: TDD.
- The integration test runs the real installed `work-supervisor.py` `status`, `park` and `start` beside a populated store and a ledger, including a `start` that admits an Approved pair, and compares each answer with the answer without them (AC-0018). Mode: goal-based, integration.
- A fresh process returns the open request's id, and two kill points inside `report` are driven in a child process whose commit function the test replaces before it runs `main`, so no hook ships (AC-0020). `status` writes no file, store record or commit (AC-0021). Mode: TDD.

**Approach:** the fact checks of AC-0011 call the alignment lint as the new-spec script it is, from the pinned `scripts/` directory, through a child process started with `-I -B` and an environment reduced to what the lint needs.

**Done when:** the T3 tests pass.

### T4: Protected content, the approval-edit exception and the reviewed revision

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_protected.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_revision.py`

**Tests:**
- A foreign commit that changes no protected item, including the work supervisor’s `delivery/approvals.jsonl` commit, is accepted. Combined faults select one code: changed pin wins over ledger and status faults, ledger fault wins over status faults, and an out-of-window status edit or observable foreign attempt/store mutation yields `protected-content-changed`; merges use first parents and reinstalling pinned bytes clears a net pin change (AC-0013). Mode: TDD.
- Token-only edits on the existing first status line and the gate-specific dated entry are accepted from consent issuance until the next ledger line; spec approval edits the spec token and spec-approval entry, plan approval edits the plan token and plan-approval entry. A blank line plus dated entry passes region normalisation. Reverting tokens and removing entries passes for an unanswered gate before park, after request-changes or reject, and after human-decision revise or abandon. Cap/weak approval alone opens no approve-direction window; the subsequent spec-approved consent does (AC-0014). Mode: TDD.
- Approve-direction edits before issuance or after a later ledger line, a changed status-line prefix or suffix, a removed first status line, a second status line, the wrong gate’s entry, an entry outside the last Changelog, a wrapped entry and any other content change are refused. Early-approval reverts remain accepted (AC-0015). Mode: TDD.
- Consent binding covers convergence, cap, weak and approve-after-cap/weak, using the last reviewed identity with `unreviewed: false`, plus the sole exception: after voiding at the allowance the fresh cap binds the current identity with `unreviewed: true`; approval-only edits preserve either binding (AC-0017). A round cannot converge with mixed review/adjudication identities, including edits between issue and report (AC-0043). For changes to Risk triggers, Agent Rules or accepted risks, test the closed voiding table with answered, open and parked consents below and at the allowance, plus an in-progress round with no consent; stale answered consent refuses before a parked response, open/parked consent is voided, below the allowance a further round opens, at the allowance a fresh cap binds the new revision as unreviewed without opening a round, and a voided round is re-run. A second change at the allowance voids and reissues the marked cap for the newest revision (AC-0044). Mode: TDD.

**Done when:** the T4 tests pass.

### T5: Review rounds, report paths and classification

**Depends on:** T4

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_rounds.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_classifier.py`, `packs/core/tests/skills/new-spec/fixtures/`

**Tests:**
- Required roles with and without `security-boundary`, the request keys, and no later kind before each role reports (AC-0022). Mode: TDD over recorded reports.
- A request whose path differs from the derived one is refused, and `next` refuses `reviews-not-ignored` in a repository where `.context/reviews` is not ignored (AC-0023). A report file that is a link, a non-regular file or 1 MiB plus one byte is refused, and a second report with the same bytes is refused `report-replayed` (AC-0024). Mode: TDD. A pending identical uncommitted ledger line after a kill does not trigger replay; a committed matching report does (AC-0024, AC-0020).
- A stop for an unavailable reviewer, an unavailable adjudicator, each classifier reason code a recorded invalid raw report triggers, and every adjudication reason, including `unreadable`, `finding-unanchored` and `no-actionable-result`, in the closed set of AC-0025, each followed by a `next` that issues nothing; the indeterminate and invalid adjudications are recorded as such and never clean (AC-0025). Mode: TDD.
- The classifier equals the real `review-artifact.py` on the recorded raw reports and adjudications, reason codes included (AC-0026). Mode: goal-based, the real script loaded by path under a unique module name.
- A clean report with no footer skips adjudication, a findings report and a clean report with a footer each issue one, the request names the exclude profile, and an adjudication reported with the reviewer's profile is refused (AC-0027). Mode: TDD.
- A reviewer equal to the author makes a weak round that is never converged (AC-0028). A sustained finding below the allowance gives `revise` then a round (AC-0029). A refuted-only round gives the `spec-approved` consent (AC-0030). Mode: TDD.
- The cap after 3 rounds with the key absent and after a configured value, a weak round that is also the last the allowance permits (`review-weak` wins), a non-weak non-converged round at the allowance (`review-cap`, no `revise`), and no further `review-round` or `revise` after either except the voiding precedence of AC-0044 (AC-0031). Mode: TDD over recorded rounds.

**Done when:** the T5 tests pass.

### T6: Consent requests, `park`, `gates` and the digest copy

**Depends on:** T5

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_consent.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_digest.py`

**Tests:**
- The open findings by identifier and checked file reference (a hostile reference is dropped), and each closed prompt case: reviewed cap/weak shows `unreviewed: false` and three answers; unreviewed cap shows `unreviewed: true`, states that the current revision is unreviewed, and offers only request-changes for one round on that revision without revise, or reject (AC-0032). Mode: TDD. References test absolute paths, traversal, hidden and escape characters, symlink components, non-regular files, line 0, line 1, line 2147483647 and line 2147483648; only grammar-valid confined references with in-range ASCII lines survive (AC-0032).
- A consent holds only fixed fields, and hostile reviewer text carrying control, escape, newline and bidirectional characters in each other request field, a refusal detail, a `status` field and relayed lint output is cut to 512 characters, neutralised and marked untrusted (AC-0033). Mode: TDD with injected text. The character corpus covers every rejected character class of `is_hidden_char` and `_unsafe` in stdout and stderr too, with lengths 512 and 513 exercising the output bound (AC-0033).
- For an unchanged identity, a repeated `next` on an open consent writes nothing, `next` on a parked request refuses `parked`, `status` names it, and a fresh process reaches the same state (AC-0034). Mode: TDD. Changed identities follow AC-0044 before the waiting response (AC-0034).
- `park` records the fields of AC-0035 without a commit or tracked-file change, with the park time from the supervisor’s clock and the consent’s `unreviewed` marker preserved (AC-0035). Mode: TDD.
- `gates` lists each parked consent with its state `pending`, `stale` after recorded-commit digest mismatch (a working-tree-only edit does not change listing state) and `invalid` after a damaged record, preserves the marker and its fixed human-facing text for both reviewed and unreviewed consents, includes no reviewer or human text, and writes nothing (AC-0036). Mode: TDD.
- The digest copy equals the real `gate_digest` on the digest corpus in Design, with the behavioral equality of AC-0037, refusals included, with the real module loaded by path; the same test runs in the corpus suite and at closeout (AC-0037). Mode: goal-based.

**Done when:** the T6 tests pass and the end-to-end integration test passes.

### T7: Pins

**Depends on:** T6

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/.apm/skills/new-spec/supervisor.toml`, `packs/core/tests/skills/new-spec/test_spec_supervisor_pins.py`

**Tests:**
- The admission line holds the digests of every file under `scripts/` at any depth except `__pycache__`, the manifest and the policy file, and `pinned_files` equals the directory listing in portable form (AC-0038). Mode: goal-based.
- Every verb that reads an admission line refuses `supervisor-changed` after a modified, added or removed script, a changed manifest and a changed policy file; `start` and `gates` compare as AC-0039 states; a planted bytecode file never runs; a `__pycache__` directory is neither pinned nor a refusal; a dot-file added later is `supervisor-changed` (AC-0039). Mode: TDD. Combined faults confirm pins are checked first, and a changed-then-restored pinned file passes by net comparison (AC-0039).
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
  1. Section 5, the spec-state row: `start` writes the first ledger line (not the first `next`), and the rollback column says a step commit is never reverted, because the ledger is append-only; removing the ledger does not reset historical roles, allowance or unanswered cap/weak gates without an authorising answer (AC-0002).
  2. Section 5, the closing sentence: a partial migration leaves a ledger that ends early, and the supervisor re-derives from the ledger and git history, not from headers and statuses.
  3. Section 3, "Guard in a session", and section 4, the `--known-commits` row: the sibling's check is a protected-content check that accepts any commit leaving protected content alone, not a moved-`HEAD` check; `--known-commits` stays provisional for `ferryman`.
  4. Sections 2 and 3: `review-cap` and `review-weak` are consent gates beside `spec-approved`; the fixed meaning of their answer sets, including the unreviewed cap’s two legal answers; and the single stage vocabulary `authoring`, `reviewing`, `revising`, `awaiting-human`, `delegating`, `terminal`.
  5. Section 3, `status` and `parked`: this supervisor's own `park` records an open consent request in its store with the fields AC-0035 lists, `gates` lists them with the states AC-0036 names, and a stopped and an ended run are one `terminal` state with a recorded reason.
  6. Sections 3 and 7, review independence: the `weak` control rests on a self-reported agent definition and the supervisor does not prove that a review ran, so the "100% of rounds record a distinct profile" target reads as a flag, not a guarantee.
  7. Section 3, the reviewed revision: each round records the pair identity, a content change outside a step follows AC-0044 precedence, the role set never shrinks, and the infra-flavored security role is required for a destructive spec.
  8. Section 8, the last paragraph: the pin set excludes `__pycache__`, treats a dot-file under `scripts/` as a refusal, and a run pinned under another version recovers by reinstalling that version by net-change comparison, while ledger removal remains constrained by AC-0002.
  9. Section 3, "Approval in a session": the protected-content check opens an exception for the human's approval and revert commits in the states AC-0014 names, and the forged-line and agent-written-approval paths are accepted risks until the guard and scribe.

**Done when:** the page read finds no contradiction with this spec.

## Rollout

Delivery is one change set with no flag. Rollback removes the new files, since nothing calls the supervisor until `spec-supervisor-gates` and the `work-loop` driver line land. A core pack release carries it to adopters, ahead of the gates release. `work-supervisor.py` and its pin set are unchanged, so its pin is unaffected. No infrastructure or external system is involved.

## Risks

- An unreviewed cap can be mistaken for acceptance of reviewed residue. Mitigation: T4 checks its current-revision binding and T6 checks the fixed marker and two-answer prompt; gates owns `approve-unreviewed` and the one-round allowance after request-changes.
- The protected-content check may refuse a legitimate human approval edit made between steps. Mitigation: the approval-edit exception of AC-0014, tested in every state it names, including the spec-approved consent that follows a cap or weak approve answer, and the consent request completes only through the answer record.
- The real work supervisor may refuse a spec directory that holds the ledger, or a git directory that holds a sibling store. Mitigation: AC-0018 runs against the real script in T3, before any later task builds on the layout.
- The copied pin code and gate digest may drift from the work supervisor's. Mitigation: the behavior comparisons of AC-0037 and AC-0040 on recorded corpora, run in the pack tests, at closeout and in the corpus suite.
- The forged ledger line, the agent-written approval, the unproven review, the unseen attempt records, the self-pin and a history rewrite are accepted risks, recorded as contract-tier items in the spec's Assumptions; the Brief 1 waiver covers identity only and none of them.

## Changelog
