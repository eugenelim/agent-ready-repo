# Spec: Spec supervisor core

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0162, ADR-0163, ADR-0157, RFC-0115
- **Brief:** brief:everyday-supervisors-delivery
- **Discovery:** none
- **Depends on:** spec:supervisor-manifest-contract
- **Contract:** none — the interface is the six commands of ADR-0162 D1 and the manifest of spec supervisor-manifest-contract
- **Shape:** service
- **Risk triggers:** security-boundary, structural-interface, persistent-representation

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` and accepted risks under `Assumptions` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> the remaining `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A user or controller drives a drafted spec and plan from admission through review rounds to the `spec-approved`, `review-cap` and `review-weak` consent requests with six commands, and a fresh process resumes from the repository with no step lost or repeated. Core owns admission, requests, resume, ledger, protected content, review rounds, cap and weak gates, pins, the digest copy, and park records and listings. Gates owns the extension in gates AC-0027, answers, delegated commands, plan approval, hand-off, instruction text, how-to, release and live trials. Core ships first with the five request kinds of AC-0005. The supervisor approves nothing, binds each consent to the revision the reviewers read, and accepts a step only when protected content is untouched; it checks content, not who committed it, and it does not prove that an independent review ran (see the accepted risks under Assumptions).

## What Changes

- `spec-supervisor.py`, its manifest `supervisor.toml` and `spec-policy.json` — `packs/core/.apm/skills/new-spec/` (the script under `scripts/`, the other two at the skill root)
- The six commands `start`, `next`, `report`, `status`, `park` and `gates`, from admission to the consent requests of `spec-approved`, `review-cap` and `review-weak`
- A committed append-only ledger in the spec directory, with one commit per step
- The review procedure of `pre-execute-review.md`, encoded as `review-round`, `adjudicate` and `revise` requests, with its own report classifier
- A copy of the work supervisor's gate digest, so a consent request carries the digest the work supervisor's `park` records
- Pack tests for each rule — `packs/core/tests/skills/new-spec/`
- Page 05 of the unattended-delivery architecture, where it differs from this spec — `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md`
- A core pack release, shipped before `spec-supervisor-gates`, with its changelog fragment and self-host projections — `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`. The `new-spec/` eval case waits for the gates release, because this release adds no `SKILL.md` text for an eval to exercise.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | The six commands, the request kinds and the manifest are read by a controller later | the supervisor script, `supervisor.toml` and `spec-policy.json` | eugenelim | the manifest, request and verb tests green | the manifest validates against `supervisor-manifest.v1` |
| Current architecture | Page 05 differs from this spec in the points its update task lists | `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md` | eugenelim | the page names each listed point as this spec states it | no page 05 sentence contradicts this spec |
| Release history | A core pack file changes | `packs/core/pack.toml`, `plugin.json` and `docs/product/changelog.d/` | eugenelim | the changelog validates and the core release check passes | the core version is one patch above `main` at merge |
| Decision rationale | ADR-0162, ADR-0163 and ADR-0157 record the contract, the placement and approval | `docs/adr/` | eugenelim | the ADRs Accepted | none further |
| User promise, maintainer procedure | not applicable here: the instruction text, the how-to and the session rules belong to `spec-supervisor-gates` | none | none | none | none |
| Operations | not applicable: no deployment changes | none | none | none | none |

## Agent Rules

### Always do

- Run the pack tests for the supervisor before reporting a task done.
- Keep the supervisor stdlib-only, as `work-supervisor.py` is.
- Reconfigure stdout and stderr to UTF-8 before the supervisor's first print.
- Stop at an approval only by issuing a consent request: no verb of the supervisor stops at an approval any other way.
- Treat reviewer, author and human text as untrusted data: carry identifiers and grammar-checked file references, bound any text, neutralise control, escape and bidirectional characters, and mark it untrusted.

### Ask first

- Adding a request kind, a stage value or a command to the supervisor.
- Changing a default in `spec-policy.json`.
- Adding a path to the set a request kind may change, or an item to the protected set.
- Widening an allowed edit of a protected item, or removing an item from the protected set.

### Never do

- Change any file in the work-loop pin set: no file in the work-loop pin set changes (ADR-0163 D3, ADR-0144).
- Import, or load at run time, any work-loop script.
- Give the supervisor a verb, flag or default that approves a gate.
- Add a new top-level dependency or a runtime import of a third-party package.
- Write the ledger, an attempt record or the store from anywhere but a supervisor verb.
- Place the supervisor's store inside `<git-dir>/agentbundle-supervisor/`.
- Put an internal record citation in a file shipped under `packs/`.

## Testing Strategy

- **Admission and confinement (AC-0001, AC-0002, AC-0003):** TDD over a temporary repository, because each refusal is a compressible invariant and each closed list is a parametrized case set. The confinement case includes a link swapped in between a check and the open.
- **Manifest, requests and roles (AC-0004, AC-0005, AC-0006, AC-0007):** TDD for the request shapes, the author rule and the role set, and goal-based for the manifest, which a schema validator decides.
- **Report, ledger and protected content (AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0043, AC-0044, AC-0045):** TDD over a temporary repository with real commits, including foreign commits landed between steps, a forged one-line append, first-parent merge history, net pin restoration and edits outside the allowed paths.
- **Coexistence and scope (AC-0018, AC-0019):** goal-based, an integration test against the real installed `work-supervisor.py`, never a stub, and a diff check against the work-loop pin set at closeout.
- **Resume (AC-0020, AC-0021):** TDD with a process killed at named points and a fresh process started after.
- **Review procedure (AC-0022, AC-0023, AC-0024, AC-0025, AC-0027, AC-0028, AC-0029, AC-0030, AC-0031, AC-0032):** TDD over recorded reviewer reports, because rounds, weakness and stops are state transitions.
- **Classifier equivalence (AC-0026):** goal-based, a behavior comparison against the real `review-artifact.py` over recorded reports, since ADR-0163 D3 forbids sharing its code.
- **Consent, park, gates and untrusted text (AC-0033, AC-0034, AC-0035, AC-0036):** TDD over a temporary repository, with injected hostile report text.
- **Consent digest (AC-0037):** goal-based, a behavior comparison with the work supervisor's gate digest on the same inputs, run in the pack tests and at closeout.
- **Pins (AC-0038, AC-0039, AC-0040):** goal-based digest comparisons, TDD for the refusals, and a behavior comparison with the work supervisor's pin code on the same inputs.
- **Release and shipped text (AC-0041, AC-0042):** goal-based, the changelog validator, the core release check, the self-host drift check and a citation scan of added lines.

## Acceptance Criteria

- [ ] **AC-0001.** `start <spec-dir>` admits a tracked, non-ignored `spec.md` and `plan.md` pair on a clean non-default branch with one committed admission line containing the run id, required role set, pin digests and pair identity of AC-0017.
- [ ] **AC-0002.** `start` refuses, and writes nothing, in each case of this closed set: the current branch is the default branch (`default-branch-refused`), the default branch cannot be determined (`default-branch-unknown`), `HEAD` is detached (`detached-head`), the working tree holds a modified, staged or untracked non-ignored path (`checkout-dirty`), `spec.md` is missing, `plan.md` is missing, either pair file or an existing ledger is untracked or ignored, the subject is already admitted or ended, the subject’s history holds an earlier run’s ledger and admission reduces its role set, resets its allowance, or bypasses an unanswered cap/weak consent without an authorising answer record, `max_review_rounds` is present in `spec-policy.json` and is not an integer of at least 1, a file under `scripts/` has a name outside the portable pin form of AC-0038, or `pinned_files` of `supervisor.toml` differs from the installed listing.
- [ ] **AC-0003.** Every verb that takes `<spec-dir>` refuses, and writes nothing, in each case of this closed set: the argument is not a repository-relative POSIX path whose every segment matches `[A-Za-z0-9._][A-Za-z0-9._-]*` and is neither `.` nor `..`, the path lies inside the git directory, a component of it is a symlink or not a directory, or `spec.md`, `plan.md` or the ledger inside it is a symlink or not a regular file, whether the link exists at the check or appears before the open.
- [ ] **AC-0004.** The manifest passes the release contract check: validation against `supervisor-manifest.v1` with its request-kind listing equal to the kinds observed across a driven run of this release.
- [ ] **AC-0005.** Every request `next` returns carries `schema_version` 1, `request_id`, `run_id`, `kind` and `stage`, validates against `supervisor-request-envelope.v1`, has a `kind` in `author-spec`, `review-round`, `adjudicate`, `revise`, `consent` and a `stage` in `authoring`, `reviewing`, `revising`, `awaiting-human`, `delegating`, `terminal`, and pairs them as `author-spec` with `authoring`, `review-round` and `adjudicate` with `reviewing`, `revise` with `revising`, and `consent` with `awaiting-human`.
- [ ] **AC-0006.** `next` issues `author-spec` exactly when the admitted pair has neither a recorded review round nor an author recorded from the first reported `author-spec` result.
- [ ] **AC-0007.** The required role set at each round opening equals the union of all roles recorded earlier in this subject’s run history and the roles selected from the pair at `HEAD`: `adversarial` always, plus `security` for `security-boundary` or `destructive`.
- [ ] **AC-0008.** Each completed step adds exactly one commit, and that commit holds exactly one new ledger line and the files the step changed.
- [ ] **AC-0009.** A ledger-changing commit is accepted as a step commit exactly when it adds one well-formed line of this run with `previous` equal to the last recorded commit (the newest earlier ledger-changing commit on first-parent history), the kind and request id equal to the open request when completing it, and no changed path outside that kind’s path set; other ledger changes refuse `ledger-altered` under AC-0013.
- [ ] **AC-0010.** `report` refuses without writing for each member of the closed invalid-result set: a request id other than the open one; a completed request according to the ledger at the last recorded commit (`request-consumed`); a result file that is a symlink, non-regular, over 16 MiB, non-UTF-8 JSON, has duplicate keys or nesting deeper than 16; missing or extra facts outside the exact per-kind sets (`author-spec` and `revise`: `{agent_definition}`; `review-round` and `adjudicate`: `{agent_definition, outcome, report_path}`; `consent`: `{}`); `outcome` outside `{available, unavailable}`; `agent_definition` outside `human` or `[A-Za-z0-9._-]{1,64}`; or a consent with no matching human answer (`no-human-answer`).
- [ ] **AC-0011.** `report` on `author-spec` refuses when `spec.md` does not read `Status: Draft`, when `plan.md` does not read `Status: Drafting`, or when `lint-contract-item-alignment.py`, run with a scrubbed environment and bytecode writing off, does not exit 0 on the spec directory.
- [ ] **AC-0012.** Every verb refuses `ledger-altered` without writing when the ledger differs from the ledger at the last recorded commit other than by one appended well-formed step line, subject to the precedence of AC-0013.
- [ ] **AC-0013.** For each checked input, the protected-content check yields exactly the first applicable refusal in this ordered closed set: pinned scripts, manifest or policy differ from admission pins (`supervisor-changed`); ledger changes fail AC-0009 or AC-0012 (`ledger-altered`); status or approval-entry changes fall outside AC-0014, or an observable attempt/store mutation is outside a supervisor verb (`protected-content-changed`); otherwise no protected-content refusal. Commits since the last recorded commit are judged along first parents, with pinned-file recovery judged by the net change since that commit.
- [ ] **AC-0014.** The accepted approval-edit set consists only of token changes on an existing first preamble status line (all other bytes of that line identical) and dated approval-entry edits in the plan’s last exact `## Changelog` region, compared after gate-digest region normalisation (blank-run folding and trailing-blank removal): the approve-direction window starts at consent issuance for the current reviewed revision and ends at the next committed ledger line, and permits the spec token plus spec-approval entry for `spec-approved`, or the plan token plus plan-approval entry for `plan-approved`; the revert-direction window permits tokens back to `Draft` / `Drafting` and removal of approval entries whenever a gate is unanswered, including early approval before parking and reversion after `request-changes`, `reject`, or a human-decision choice of `revise` or `abandon`.
- [ ] **AC-0015.** Every protected status or approval-entry edit outside the closed allowed set of AC-0014 refuses `protected-content-changed`, subject to AC-0013 precedence.
- [ ] **AC-0016.** `report` accepts working-tree and index differences only within the closed per-kind path sets: `spec.md` and `plan.md` with protected lines unchanged for `author-spec` and `revise`; no pair paths for `review-round`, `adjudicate` and `consent`; and the ledger for every kind only when its single pending appended line equals byte for byte the line computed from the report file, the ledger at the last recorded commit and the open request. Untracked non-ignored paths count as differences.
- [ ] **AC-0017.** A consent is issued only when the current pair identity equals the identity recorded for the last round: `spec-approved` uses the converged round, `review-cap` and `review-weak` use the last round run, and `spec-approved` after an approve answer to either uses that same last reviewed revision. Pair identity is the sha256 of each whole file after masking only its first preamble status token and dropping plan approval entries with the region normalisation of AC-0014; every author, revision, review and adjudication line records it. The voiding precedence is AC-0044.
- [ ] **AC-0018.** With a populated supervisor store and the ledger present, the real `work-supervisor.py` `status`, `park` and `start` answer as they do with neither, including a `start` that admits an Approved pair.
- [ ] **AC-0019.** At closeout, the diff of the change set against `origin/main` holds no path in the work-loop pin set (`packs/core/.apm/skills/work-loop/scripts/`, `supervisor-policy.json`, `review-rules.json`) and none of its projections under `.claude/skills/work-loop/` and `.agents/skills/work-loop/` that rewrite them.
- [ ] **AC-0020.** After a fresh process, and after a process killed at either of two points inside `report` (step files and ledger line written before the commit, commit made before the attempt closes), `next` or a repeated `report` returns the open request id or completes the step with no ledger line lost or repeated and no more than one commit for the step.
- [ ] **AC-0021.** `status` writes no file, store record or commit, and names the stage, the open request id and, for an ended run, the recorded reason.
- [ ] **AC-0022.** `next` issues one `review-round` request for each required role of AC-0007, naming the role and, as `exclude_profile`, the author's agent definition, and issues no later request kind until each has reported.
- [ ] **AC-0023.** Each report-path operation meets its path contract: the supervisor derives `.context/reviews/<run_id>/<round>-<role>-<raw|adjudication>.md`, `report` accepts only that path, and `next` refuses `reviews-not-ignored` before issuing a report-bearing request unless `git check-ignore -q .context/reviews` succeeds.
- [ ] **AC-0024.** `report` accepts a report file only when it is read through a link-refusing regular-file open bounded to 1 MiB and its sha256 is absent from this run’s ledger at the last recorded commit; a repeated sha256 there refuses `report-replayed`.
- [ ] **AC-0025.** The run records a terminal stop with no further request for each member of the closed stop set: an unavailable reviewer, an unavailable adjudicator, an invalid raw report, or an adjudication with a reason in `{unreadable, envelope-headings, prose-before-envelope, audit-numbered-finding, indeterminate-present, indeterminate-audit-not-none, sustained-line-shape, legacy-report, finding-unanchored, no-actionable-result}` returned by the real classifier; invalid or indeterminate adjudication never counts as clean.
- [ ] **AC-0026.** On each recorded raw report and each recorded adjudication in the equivalence corpus, the supervisor's classifier returns the classification, the reason code of an invalid input, and for a raw report the finding count and `## Not checked` flag, that `review-artifact.py` returns.
- [ ] **AC-0027.** The next adjudication action matches the closed classification table: a clean raw report without `## Not checked` records the reviewer clean directly; every other non-invalid report issues `adjudicate` with the reviewer’s agent definition as `exclude_profile`, which cannot be accepted as the adjudicator’s definition.
- [ ] **AC-0028.** A round in which any reviewer's agent definition equals the author's is recorded `weak`, and a weak round is never recorded as converged.
- [ ] **AC-0029.** After a non-weak round that did not converge and left a sustained finding open, with the round total below the allowance of AC-0031, `next` issues `revise` and then a further round.
- [ ] **AC-0030.** After a non-weak round that meets AC-0043 and in which every adjudicated finding is refuted or none exists, `next` issues the `consent` request for `spec-approved` and no `revise` or further round.
- [ ] **AC-0031.** The next request after a completed round follows the closed priority table, subject to AC-0017 voiding: a weak round yields `review-weak`; otherwise a non-converged round at the allowance yields `review-cap`; either consent blocks further `review-round` and `revise` requests in this release. The allowance is `max_review_rounds` (default 3), with answer-driven changes owned by gates AC-0012.
- [ ] **AC-0032.** Every `review-cap` or `review-weak` consent uses the fixed residue prompt: open sustained findings appear only as supervisor-assigned identifiers with an optional confined reference (AC-0003 path grammar, existing repository-confined regular file with no symlink component, and an ASCII integer line from 1 through 2147483647; other references are dropped), and the offered answers are `approve` (accept residue and lead to `spec-approved` consent), `request-changes` (revision when a sustained finding exists, then exactly one further round), and `reject` (terminal rejection with no further request).
- [ ] **AC-0033.** Every user-visible text field meets the untrusted-output policy: consent text contains only fixed text, digests, assigned identifiers and checked references; other reviewer, author or human text in requests, refusal details, status, stdout, stderr or relayed lint output is cut to 512 characters, neutralises at least every character rejected by the copied `is_hidden_char` or `_unsafe` (including controls, escapes, line separators, format and bidirectional characters), and is marked `"untrusted": true`.
- [ ] **AC-0034.** For an unchanged pair identity, the waiting-consent response is stable: `next` returns an open consent unchanged with no attempt record or commit, or refuses `parked` for a parked consent named by `status`; identity changes instead follow AC-0017 before either response.
- [ ] **AC-0035.** `park` records only the open consent in the supervisor’s store, with no commit or tracked-file change, as `{run_id, request_id, gate, spec_dir, spec_digest, plan_digest, commit, state, parked_at}`, where `spec_dir` meets AC-0003, `commit` is `HEAD`, `state` is `pending` and `parked_at` comes from the supervisor’s clock.
- [ ] **AC-0036.** The read-only `gates` listing contains each parked record’s run id, request id, gate, confined spec directory, both digests, commit, park time, fixed answer text and derived state: `pending` when recorded digests equal gate digests of the files at the recorded commit, `stale` when they differ, or `invalid` when record field checks fail; no reviewer or human text is included.
- [ ] **AC-0037.** On every input in the digest equivalence corpus, the consent digests and refusal outcome equal the real work supervisor’s `gate_digest` outcome for the same bytes.
- [ ] **AC-0038.** The admission ledger line records the sha256 of every file under the supervisor's `scripts/` directory at any depth, of `supervisor.toml` and of `spec-policy.json`, leaving out only directories named `__pycache__`, and the `pinned_files` of `supervisor.toml` list the same files, each in the portable form of `supervisor-manifest.v1` (no segment starting with `.`).
- [ ] **AC-0039.** Every core verb that reads an admission line checks pins before other refusal checks: `next`, `report`, `status` and `park` compare the installed files with that line, `gates` compares against each parked record’s spec-directory admission line, and `start` compares against the installed listing; a changed, added or removed pinned file yields `supervisor-changed`, and no verb loads planted bytecode.
- [ ] **AC-0040.** On a recorded corpus of directory trees, the supervisor's pin code and the work supervisor's pin code return the same digests for every file both pin, and the supervisor's differs from it only in refusing the entries AC-0002 refuses.
- [ ] **AC-0041.** Each check in the closed release-check set exits 0: the version assertion that `pack.toml` and `plugin.json` match at one patch above `main`, `python3 tools/changelog.py validate` with this release’s fragment, and the self-host drift check of the `new-spec` projections after `make build-self`.
- [ ] **AC-0042.** No line this change adds to a file under `packs/` matches a record citation (`ADR-`, `RFC-`, a path under `docs/adr`, `docs/rfc` or `docs/architecture`, or the name of a spec directory under `docs/specs/`); the scan reads added lines only, so text already in a changed file is not counted.

- [ ] **AC-0043.** A round qualifies as converged only when every review and adjudication line records the same pair identity bound when that round issues, with `report` comparing the current identity before recording each line.
- [ ] **AC-0044.** For a content change no step makes, voiding follows this ordered closed state table: an answered consent refuses `stale-digest` at report (answer handling belongs to gates AC-0019); an open or parked consent is voided and `next` opens a further round below the allowance or issues `review-cap` afresh for the new revision at the allowance; with no consent open, an in-progress round is voided and re-run.
- [ ] **AC-0045.** Each recorded classification, finding count and `weak` value is computed from the report file and committed ledger rather than supplied result facts.

## Follow-ons

- eugenelim: `docs/specs/spec-supervisor-gates/` — the human `answer` verb and the answers file, what each human decision does (including the allowance and round counter after each), the delegated `park` and `start`, the `plan-approved` consent request, the hand-off record, the `human-decision` request, the instruction text, the how-to, the `new-spec` eval case and the live trials; it also amends `supervisor.toml` to list `delegate-verb`, `human-decision` and `delegates_to` once `next` emits them, amends the core criteria it names, and releases after this spec.
- eugenelim: `ferryman` driving this supervisor unattended, the scribe, the approval-fields guard and `--known-commits` — phase P0 of brief `ferryman-local-delivery`.
- eugenelim: `author-brief` and the `brief-ready` consent — they follow with the intake flow, and this supervisor starts at `author-spec`.
- eugenelim: a stronger human-attribution check than a name, and a check of who made a commit — the Brief 1 waiver ends when `ferryman`'s guard and scribe run the supervisors.

## Assumptions

- Defaulted: Technical: `park` records an open `consent` request as handed to a human in the supervisor's own store with no commit, `gates` lists those records, and `next` refuses `parked` while one waits — the sources fix a sibling store root, a parked `consent` gate and a `parked` refusal, and leave the record's fields, the park time and the refusal's timing open; the record carries the fields `spec-supervisor-gates` reads, and the park time is the supervisor's own clock because the work supervisor's park record has no time field — default: these meanings; if wrong: they change before the gates spec builds on them (settled by: repository owner, eugenelim).
- Defaulted: Technical: a stopped run and an ended run are one state: `status` reports stage `terminal` with a recorded reason (a reviewer or classifier stop reason, `rejected`, `abandoned` or `admitted`), and `next` answers `{"terminal": true}` as `work-supervisor.py` does — default: that merge; if wrong: a stopped run gets its own stage and recovery verb (settled by: repository owner, eugenelim).
- Defaulted: Technical: the six stage values of AC-0005, because page 05 leaves each sibling's `stage` enum to the sibling — default: those six; if wrong: the enum changes in the manifest-listed request shapes (settled by: repository owner, eugenelim).
- Defaulted: Technical: a human-drafted pair starts at `author-spec` like any other, and its author reports the agent definition `human`; the `--author-human` flag of an earlier draft is not built — default: no flag; if wrong: a start flag records the author (settled by: repository owner, eugenelim).
- Defaulted: Technical: the reviewer roles are `adversarial` always and `security` for `security-boundary` or `destructive`, because the spec-stage review requires the infra security pass for a destructive trigger plus an infrastructure-as-code match and this supervisor cannot classify the match, so it requires the pass for every destructive spec; design-intent and frontend roles are not driven — default: two roles; if wrong: the role table gains rows or the destructive rule narrows (settled by: repository owner, eugenelim).
- Defaulted: Technical: an adjudication reported with the reviewer's own agent definition is refused, not recorded weak — default: refuse; if wrong: it is recorded and the run parks (settled by: repository owner, eugenelim).
- Defaulted: Technical: the 512-character text bound, the 16 MiB result bound that matches `work-supervisor.py`, a 1 MiB report bound, a 16-level nesting bound and the 64-character agent-definition bound — default: those values; if wrong: the constants change (settled by: repository owner, eugenelim).
- Defaulted: Technical: the digest copy carries the closure and corpus recorded in the plan’s Digest copy and equivalence corpus, because the work-loop scripts are not importable by name — default: a tested copy, compared at closeout and in the corpus suite; if wrong: the copy changes while retaining everything `gate_digest` reaches (settled by: repository owner, eugenelim).
- Defaulted: Technical: the pair identity of AC-0017 hashes each file with only the status token masked and the approval-entry region normalised as AC-0014 defines, because a full-byte hash would void convergence on the human's own approval commit; every other byte outside that normalisation is hashed — default: that identity; if wrong: the mask narrows or the approval commit re-enters review (settled by: repository owner, eugenelim).
- Defaulted: Technical: the last recorded commit is derived from git history as the newest first-parent commit that changed the ledger, and the store holds no copy that a check trusts, because a fresh clone must resume from the repository alone — default: history-derived; if wrong: a signed anchor replaces it under `ferryman` (settled by: repository owner, eugenelim).
- Defaulted: Technical: the default branch is read from `origin/HEAD`, and a repository without it refuses `default-branch-unknown` — default: refuse; if wrong: a policy key names the branch (settled by: repository owner, eugenelim).
- Defaulted: Technical: a run pinned under another installed version refuses every admission-reading verb `supervisor-changed`, and the recovery is to reinstall the pinned version with net-change comparison against the last recorded commit; removing the ledger does not bypass the historical admission restrictions of AC-0002; the work supervisor keeps its pins in a per-run local store and this supervisor commits them in the ledger — default: no migration of a run across versions; if wrong: a `--repin` flag lands in a later spec (settled by: repository owner, eugenelim).
- Defaulted: Technical: a dot-file, or any name outside the portable pin form, under `scripts/` refuses `start` and, when it appears later, is `supervisor-changed`, while `__pycache__` directories are never pinned, never trusted and never a refusal because bytecode writing and loading are off — default: that rule everywhere the pin set is stated; if wrong: the form widens with a new manifest version (settled by: repository owner, eugenelim).
- Technical: the ledger, attempt and store paths — `implementation-discovered`, settled when the first test needs them (settled by: eugenelim during the implementing task).
- Accepted risk: a commit that appends exactly one well-formed ledger line is accepted as a step commit, so the supervisor cannot tell its own step commit from a foreign commit that forges such a line, including a `clean` review line that carries the open request id; the checks of AC-0009 and AC-0016 narrow what a forged line can do and do not close it (settled by: repository owner, eugenelim; not covered by the Brief 1 owner waiver; closed by `ferryman`'s guard and scribe in phase P0 of brief `ferryman-local-delivery`).
- Accepted risk: an agent with write access can write `Status: Approved`, an approval entry or a hand-written `delivery/approvals.jsonl` line before any human answer, because the protected-content check judges a change by its lines and its timing, not by its author; only the answer record gates this supervisor (settled by: repository owner, eugenelim; not covered by the Brief 1 owner waiver; closed by `ferryman`'s approval-fields guard).
- Accepted risk: independent review is not proven: every raw report and adjudication is a file the session agent supplies, the supervisor enforces the order of the procedure and not that a review ran, the `weak` flag rests on the agent definition the controller reports about itself, and the refusal of an adjudication made with the reviewer's definition rests on the same self-report (settled by: repository owner, eugenelim; not covered by the Brief 1 owner waiver).
- Accepted risk: attempt records and the store live outside commits, so the commit-based check cannot see a deleted park record or a forged attempt record, although both are supervisor-written items (settled by: repository owner, eugenelim; not covered by the Brief 1 owner waiver; closed by `ferryman`'s guard).
- Accepted risk: the supervisor's pins are its own digests, so an agent that edits the checker, or the pinned files together with the record, defeats the self-pin; only a controller's release-time comparison closes that (settled by: repository owner, eugenelim; not covered by the Brief 1 owner waiver; closed in phase P0 of brief `ferryman-local-delivery`).
- Accepted risk: a history rewrite between steps is caught only through the append-only ledger check, and a rewrite that keeps the ledger extension intact is not detected (settled by: repository owner, eugenelim; not covered by the Brief 1 owner waiver).
- Product: the Brief 1 owner waiver in `docs/product/briefs/everyday-supervisors-delivery.md` covers an unchecked identity only, and covers no other control or risk named here.
