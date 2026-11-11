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

> **Contract:** Agent Rules, Testing Strategy, Acceptance Criteria and accepted risks govern completion; changes require amendment. Other sections are working context.

## Outcome

Core drives a drafted pair through review to consent and resumes without lost or repeated steps. It ships five request kinds before gates adds answers and delegation; core never completes consent. Content checks prove neither human authorship nor independent review.

## What Changes

- `packs/core/.apm/skills/new-spec/`: supervisor script, manifest, policy and digest copy.
- `packs/core/tests/skills/new-spec/`: behavior and equivalence tests.
- Core release records, projections and architecture page 05; instruction text and evals belong to gates.

## Durable Outputs

eugenelim owns every output and every repository, contract, review and risk role.

| Output | Destination | Closeout evidence |
| --- | --- | --- |
| Interface | `new-spec` script, manifest, policy | manifest and verb tests pass |
| Architecture | `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md` | T9 points agree |
| Release | core version files, changelog, projections | AC-0041 passes |

ADRs hold decision rationale; gates owns user guidance. No deployment changes.

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

- **T1 (AC-0001, AC-0002, AC-0003):** TDD, real commits and bounded inputs; cases in plan T1.
- **T2 (AC-0004, AC-0005, AC-0006, AC-0007, AC-0046, AC-0047):** TDD, real commits and bounded inputs; cases in plan T2.
- **T3 (AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0016, AC-0018, AC-0020, AC-0021, AC-0045):** TDD, real commits and bounded inputs; cases in plan T3.
- **T4 (AC-0013, AC-0014, AC-0015, AC-0017, AC-0043, AC-0044):** TDD, real commits and bounded inputs; cases in plan T4.
- **T5 (AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, AC-0029, AC-0030, AC-0031):** TDD, real commits and bounded inputs; cases in plan T5.
- **T6 (AC-0032, AC-0033, AC-0034, AC-0035, AC-0036, AC-0037):** TDD, real commits and bounded inputs; cases in plan T6.
- **T7 (AC-0038, AC-0039, AC-0040):** goal-based checks; cases in plan T7.
- **T8 (AC-0019, AC-0041, AC-0042):** goal-based checks; cases in plan T8.

## Acceptance Criteria

- [ ] **AC-0001.** `start <spec-dir>` admits a tracked, non-ignored `spec.md` and `plan.md` pair on a clean non-default branch with one committed admission line containing the run id, required role set, pin digests and pair identity of AC-0017.
- [ ] **AC-0002.** `start` refuses, and writes nothing, in each case of this closed set: the current branch is the default branch (`default-branch-refused`), the default branch cannot be determined (`default-branch-unknown`), `HEAD` is detached (`detached-head`), the working tree holds a modified, staged or untracked non-ignored path (`checkout-dirty`), `spec.md` is missing, `plan.md` is missing, either pair file or an existing ledger is untracked or ignored, the subject is already admitted or ended, the subject’s history holds an earlier run’s ledger and admission reduces its role set, resets its allowance, or bypasses an unanswered cap/weak consent (core refuses these historical bypasses even with a purported answer record; gates AC-0027 adds answer-authorised transitions), `max_review_rounds` is present in `spec-policy.json` and is not an integer of at least 1, a file under `scripts/` has a name outside the portable pin form of AC-0038, or `pinned_files` of `supervisor.toml` differs from the installed listing.
- [ ] **AC-0003.** Every verb that takes `<spec-dir>` refuses, and writes nothing, in each case of this closed set: the argument is not a repository-relative POSIX path whose every segment matches `[A-Za-z0-9._][A-Za-z0-9._-]*` and is neither `.` nor `..`, the path lies inside the git directory, a component of it is a symlink or not a directory, or `spec.md`, `plan.md` or the ledger inside it is a symlink or not a regular file, whether the link exists at the check or appears before the open.
- [ ] **AC-0004.** The manifest passes the release contract check: validation against `supervisor-manifest.v1` with its request-kind listing equal to the kinds observed across a driven run of this release.
- [ ] **AC-0005.** Every request `next` returns carries `schema_version` 1, `request_id`, `run_id`, `kind` and `stage`, validates against `supervisor-request-envelope.v1`, has a `kind` in `author-spec`, `review-round`, `adjudicate`, `revise`, `consent` and a `stage` in `authoring`, `reviewing`, `revising`, `awaiting-human`, `delegating`, `terminal`, and pairs them as `author-spec` with `authoring`, `review-round` and `adjudicate` with `reviewing`, `revise` with `revising`, and `consent` with `awaiting-human`.
- [ ] **AC-0006.** `next` issues `author-spec` exactly when the admitted pair has neither a recorded review round nor an author recorded from the first reported `author-spec` result.
- [ ] **AC-0007.** The required role set at each round opening equals the union of all roles recorded earlier in this subject’s run history and the roles selected from the pair at `HEAD`: `adversarial` always, plus `security` for `security-boundary` or `destructive`.
- [ ] **AC-0008.** Each completed step adds exactly one commit, and that commit holds exactly one new ledger line and the files the step changed.
- [ ] **AC-0009.** A ledger-changing commit is accepted as a step commit exactly when it adds one well-formed line of this run with `previous` equal to the last recorded commit (the newest earlier ledger-changing commit on first-parent history), the kind and request id equal to the open request when completing it, and no changed path outside that kind’s path set; other ledger changes refuse `ledger-altered` under AC-0013.
- [ ] **AC-0010.** `report` refuses without writing for each member of the closed invalid-result set: a request id other than the open one; a completed request according to the ledger at the last recorded commit (`request-consumed`); a result file that is a symlink, non-regular, over 16 MiB, non-UTF-8 JSON, has duplicate keys or nesting deeper than 16; missing or extra facts outside the exact per-kind sets (`author-spec` and `revise`: `{agent_definition}`; `review-round` and `adjudicate`: `{agent_definition, outcome, report_path}`; `consent`: `{}`); `outcome` outside `{available, unavailable}`; `agent_definition` outside `human` or `[A-Za-z0-9._-]{1,64}`; or any consent result (`no-human-answer`, the only consent outcome in core, which never completes a consent request).
- [ ] **AC-0011.** `report` on `author-spec` refuses when `spec.md` does not read `Status: Draft`, when `plan.md` does not read `Status: Drafting`, or when `lint-contract-item-alignment.py`, run with a scrubbed environment and bytecode writing off, does not exit 0 on the spec directory.
- [ ] **AC-0012.** Every verb refuses `ledger-altered` without writing when the ledger differs from the ledger at the last recorded commit other than by one appended well-formed step line, subject to the precedence of AC-0013.
- [ ] **AC-0013.** For each checked input, the protected-content check yields exactly the first applicable refusal in this ordered closed set: pinned scripts, manifest or policy differ from admission pins (`supervisor-changed`); ledger changes fail AC-0009 or AC-0012 (`ledger-altered`); status or approval-entry changes fall outside AC-0014, or an observable attempt/store mutation is outside a supervisor verb (`protected-content-changed`); otherwise no protected-content refusal. Commits since the last recorded commit are judged along first parents, with pinned-file recovery judged by the net change since that commit and only the early-approval restoration exception of AC-0014 applied to approval history.
- [ ] **AC-0014.** The accepted approval-edit set contains only these changes on existing first preamble status tokens (other line bytes unchanged) and dated entries in the plan’s last exact `## Changelog`: spec-approved permits spec token/spec-entry approval from reviewed-consent issuance until the next ledger commit; unanswered gates permit reversion to Draft/Drafting and entry removal, including before park; an early token/entry approval followed by exact restoration before another ledger commit is exempt from historical refusal, but no other protected edit is exempt; entry comparison folds blank runs and removes trailing blanks.
- [ ] **AC-0015.** Every protected status or approval-entry edit outside the closed allowed set of AC-0014 refuses `protected-content-changed`, subject to AC-0013 precedence.
- [ ] **AC-0016.** `report` accepts working-tree and index differences only within the closed per-kind path sets: `spec.md` and `plan.md` with protected lines unchanged for `author-spec` and `revise`; no pair paths for `review-round`, `adjudicate` and `consent`; and the ledger for every kind only when its single pending appended line equals byte for byte the line computed from the report file, the ledger at the last recorded commit and the open request. Untracked non-ignored paths count as differences.
- [ ] **AC-0017.** Consent identity follows this binding map: after AC-0044 voiding at allowance, review-cap binds the current unreviewed pair with `unreviewed: true`; otherwise consent binds the last round with `unreviewed: false`, using the converged round for spec-approved and last completed round for cap/weak. Identity is each whole file’s sha256 with only its first preamble status token masked and plan approval entries dropped under AC-0014 normalization; author/revision/review/adjudication lines carry it.
- [ ] **AC-0018.** With a populated supervisor store and the ledger present, the real `work-supervisor.py` `status`, `park` and `start` answer as they do with neither, including a `start` that admits an Approved pair.
- [ ] **AC-0019.** At closeout, the diff of the change set against `origin/main` holds no path in the work-loop pin set (`packs/core/.apm/skills/work-loop/scripts/`, `supervisor-policy.json`, `review-rules.json`) and none of its projections under `.claude/skills/work-loop/` and `.agents/skills/work-loop/` that rewrite them.
- [ ] **AC-0020.** After a fresh process, and after a process killed at either of two points inside `report` (step files and ledger line written before the commit, commit made before the attempt closes), `next` or a repeated `report` returns the open request id or completes the step with no ledger line lost or repeated and no more than one commit for the step.
- [ ] **AC-0021.** `status` writes no file, store record or commit, and names the stage, the open request id and, for an ended run, the recorded reason.
- [ ] **AC-0022.** `next` issues one `review-round` request for each required role of AC-0007, naming the role and, as `exclude_profile`, the author's agent definition, and issues no later request kind until each has reported.
- [ ] **AC-0023.** Each report-path operation meets its path contract: the supervisor derives `.context/reviews/<run_id>/<round>-<role>-<raw|adjudication>.md`, `report` accepts only that path, and `next` refuses `reviews-not-ignored` before issuing a report-bearing request unless `git check-ignore -q .context/reviews` succeeds.
- [ ] **AC-0024.** An accepted report is a link-free regular file of at most 1 MiB for one open, unconsumed request; a second answer to that request refuses `request-consumed`, while identical bytes in distinct request files remain valid across roles and rounds.
- [ ] **AC-0025.** The run ends with no further request for an unavailable reviewer/adjudicator, invalid raw report, or any invalid/indeterminate adjudication reason returned by real `review-artifact.py`.
- [ ] **AC-0026.** On each recorded raw report and each recorded adjudication in the equivalence corpus, the supervisor's classifier returns the classification, the reason code of an invalid input, and for a raw report the finding count and `## Not checked` flag, that `review-artifact.py` returns.
- [ ] **AC-0027.** The next adjudication action matches the closed classification table: a clean raw report without `## Not checked` records the reviewer clean directly; every other non-invalid report issues `adjudicate` with the reviewer’s agent definition as `exclude_profile`, which cannot be accepted as the adjudicator’s definition.
- [ ] **AC-0028.** A round in which any reviewer's agent definition equals the author's is recorded `weak`, and a weak round is never recorded as converged.
- [ ] **AC-0029.** After a non-weak round that did not converge and left a sustained finding open, with the round total below the allowance of AC-0031, `next` issues `revise` and then a further round.
- [ ] **AC-0030.** After a non-weak round that meets AC-0043 and in which every adjudicated finding is refuted or none exists, `next` issues the `consent` request for `spec-approved` and no `revise` or further round.
- [ ] **AC-0031.** The next request after a completed round follows the closed priority table, subject to AC-0017 voiding: a weak round yields `review-weak`; otherwise a non-converged round at the allowance yields `review-cap`; either consent blocks further `review-round` and `revise` requests in this release. The allowance is `max_review_rounds` (default 3), with answer-driven changes owned by gates AC-0012.
- [ ] **AC-0032.** Every cap/weak consent follows this fixed prompt map: `unreviewed: false` offers approve (accept residue, then spec-approved), request-changes (revise if sustained findings exist, then one round), reject (terminal rejection); `unreviewed: true` states “This current revision is unreviewed” and offers request-changes (one round on current revision without revise) or reject. Findings appear only as assigned ids with optional valid references: AC-0003 path grammar, confined existing link-free regular file, ASCII line 1–2147483647; invalid references disappear.
- [ ] **AC-0033.** Every user-visible text field meets the untrusted-output policy: consent text contains only fixed text, digests, assigned identifiers and checked references; other reviewer, author or human text in requests, refusal details, status, stdout, stderr or relayed lint output is cut to 512 characters, neutralises at least every character rejected by the copied `is_hidden_char` or `_unsafe` (including controls, escapes, line separators, format and bidirectional characters), and is marked `"untrusted": true`.
- [ ] **AC-0034.** For an unchanged pair identity, the unanswered-consent waiting response is stable: `next` returns an open consent unchanged with no attempt record or commit, or refuses `parked` for a parked consent named by `status`; identity changes instead follow AC-0044 before either response. Core never completes a consent; gates AC-0027 adds answered-consent transitions.
- [ ] **AC-0035.** `park` records only the open consent in the supervisor’s store, with no commit or tracked-file change, as `{run_id, request_id, gate, spec_dir, spec_digest, plan_digest, commit, state, parked_at, unreviewed}`, where `spec_dir` meets AC-0003, `commit` is `HEAD`, `state` is `pending`, `unreviewed` equals the open consent’s marker and `parked_at` comes from the supervisor’s clock.
- [ ] **AC-0036.** The read-only gates listing contains each parked record’s identifiers, gate, confined directory, digests, commit, time, marker and fixed AC-0032 answer text, with state `invalid` for invalid fields, otherwise `stale` for AC-0044 voiding or digest mismatch at the run branch tip, otherwise `pending`, and no reviewer/human text.
- [ ] **AC-0037.** On every input in the digest equivalence corpus, the consent digests and refusal outcome equal the real work supervisor’s `gate_digest` outcome for the same bytes.
- [ ] **AC-0038.** The admission ledger line records the sha256 of every file under the supervisor's `scripts/` directory at any depth, of `supervisor.toml` and of `spec-policy.json`, leaving out only directories named `__pycache__`, and the `pinned_files` of `supervisor.toml` list the same files, each in the portable form of `supervisor-manifest.v1` (no segment starting with `.`).
- [ ] **AC-0039.** Admission-reading verbs check pins after AC-0003 confinement and before other refusals: next/report/status/park use admission pins, gates uses each parked directory’s admission, start uses the installed listing; changed/added/removed pins yield `supervisor-changed`, with no planted bytecode loaded.
- [ ] **AC-0040.** On a recorded corpus of directory trees, the supervisor's pin code and the work supervisor's pin code return the same digests for every file both pin, and the supervisor's differs from it only in refusing the entries AC-0002 refuses.
- [ ] **AC-0041.** Each check in the closed release-check set exits 0: the version assertion that `pack.toml` and `plugin.json` match at one patch above `main`, `python3 tools/changelog.py validate` with this release’s fragment, and the self-host drift check of the `new-spec` projections after `make build-self`.
- [ ] **AC-0042.** No line this change adds to a file under `packs/` matches a record citation (`ADR-`, `RFC-`, a path under `docs/adr`, `docs/rfc` or `docs/architecture`, or the name of a spec directory under `docs/specs/`); the scan reads added lines only, so text already in a changed file is not counted.

- [ ] **AC-0043.** A round qualifies as converged only when every review and adjudication line records the same pair identity bound when that round issues, with `report` comparing the current identity before recording each line.
- [ ] **AC-0044.** `next` applies this voiding table to content changes outside steps: open/parked consent or completed-round/pre-consent state becomes a further round below allowance, or fresh review-cap bound to current unreviewed identity at allowance; otherwise an in-progress round is voided and re-run.
- [ ] **AC-0045.** Each recorded classification, finding count and `weak` value is computed from the report file and committed ledger rather than supplied result facts.

- [ ] **AC-0046.** Each request contains the required payload for its kind: `author-spec` has no additional required fields; `review-round` has `role`, `exclude_profile`, `report_path`; `adjudicate` has `exclude_profile`, `round`, `report_path`; `revise` has `findings`, each with an assigned `id`, a bounded untrusted `title` and a checked `reference` when valid; `consent` has `gate`, `spec_digest`, `plan_digest`, `unreviewed`, and cap/weak consents also have `findings` and `answers` with AC-0032's consequence text.
- [ ] **AC-0047.** JSON responses use the applicable wrapper: requests are `{"request": {...}}`, refusals are `{"refusal": {"code": ..., "owner": "eugenelim", "detail": ...}}`, and ended-run responses are `{"terminal": true}`.

## Follow-ons

eugenelim owns gates (answers, delegation, plan approval, hand-off, instructions, guides, evals and trials), `ferryman` guard/scribe and unattended driving, and later `author-brief`/`brief-ready` support.

## Assumptions

eugenelim settles every default and accepts every risk below.

- Defaults: `origin/HEAD` names the default branch; missing means refusal. Ledger, attempt and sibling-store paths are implementation-discovered; first-parent history supplies the last recorded commit.
- Defaults: human authors report `human`; security review covers every destructive spec. Adjudicator/reviewer profile equality refuses; stops and ended runs share `terminal` with a reason.
- Defaults: core owns the six stages, fixed bounds, tested digest copy and pair identity defined above. Reinstalling pinned bytes restores a run; no repin flag exists; portable names exclude dot-files, while bytecode remains untrusted and excluded.
- Accepted risk: a forged single-line ledger step can pass AC-0009, including a clean report for the open request; content checks do not prove authorship.
- Accepted risk: agents can write approval fields or admission records; core never completes consent, and gates requires an answer record without proving its author.
- Accepted risk: agent-supplied reports and self-reported profiles do not prove independent review or adjudication.
- Accepted risk: uncommitted attempt/store deletion or forgery may be invisible.
- Accepted risk: editing the checker and pins defeats self-pinning; only a controller release comparison closes this.
- Accepted risk: a history rewrite preserving the ledger extension is undetected.

The Brief 1 waiver covers unchecked identity only, not these risks. `ferryman` guard/scribe closes the ledger, approval and store gaps; phase P0 also owns release comparison.
