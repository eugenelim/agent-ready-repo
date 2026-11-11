# Spec: Spec supervisor gates and hand-off

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0162, ADR-0163, ADR-0157, RFC-0115
- **Brief:** brief:everyday-supervisors-delivery
- **Discovery:** none
- **Depends on:** spec:spec-supervisor-core
- **Contract:** none — the interface is the six commands of ADR-0162 D1 plus the human-run `answer` verb, and the manifest of spec supervisor-manifest-contract
- **Shape:** service
- **Risk triggers:** security-boundary, structural-interface, persistent-representation
<!-- If this spec intentionally has no criteria, remove the section below and add `- **Acceptance Criteria:** none — <one-line reason>` to the metadata header. -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria`, and the accepted risks under `Assumptions` are contract-tier: a completion gate reads them, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> other `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A human approver answers each parked gate of the spec supervisor through a human-run `answer` verb that shows, and binds the answer to, the digests, commit, intent, code trust and authority references the delegated commands will use, and the supervisor advances a gate only on an answer record that names the open request. After both approvals the supervisor hands the approved pair to `work-supervisor` through delegated `park` and `start` commands and ends the subject only when a well-formed admission record exists for exactly the approved digests and issued values; that check proves a record exists and not that a real `start` ran (see the accepted risks under Assumptions).

## What Changes

- The `answer` verb, answer records, the `report` consent rules, the wait states after a decision and the human-decision mapping, added to `spec-supervisor.py` (owned by `spec:spec-supervisor-core`) — `packs/core/.apm/skills/new-spec/scripts/`
- The hand-off record, a human-written file that supplies the values of the real `park` and `start` — `<spec-dir>/handoff.json`
- The delegated `park` and `start` requests with their runnable command form and argument sources, the `plan-approved` consent request, the digest and hand-off re-check and the terminal confirmation — `packs/core/.apm/skills/new-spec/scripts/`
- The manifest, extended with `delegate-verb`, `human-decision` and `delegates_to` — `packs/core/.apm/skills/new-spec/supervisor.toml`
- The core criteria and tests this release amends, named in AC-0027 and in task T5
- The session instruction text and the compact request-kind table — `packs/core/.apm/skills/new-spec/SKILL.md`
- The spec-plan driver line — `packs/core/.apm/skills/work-loop/SKILL.md`, a file outside the work supervisor's pin set
- A how-to for driving the spec supervisor in a session, with a repository-level check — `guides/core/how-to/` and a suite under `tools/` registered in `tools/repo/build_gate_chain.py` and `tools/test_build_gate_chain.py`
- Pack tests for the verb, the rules and the real `park` and `start` — `packs/core/tests/skills/new-spec/`
- A core pack release after the core release of `spec:spec-supervisor-core`, with changelog fragment, self-host projections and a `new-spec` eval update — `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `packs/core/.apm/skills/new-spec/evals/`
- Scope runs from `author-spec` through `plan-approved` and the hand-off, and stops short of `author-brief` and `brief-ready`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | A user drives spec approval through a supervisor in a session | a how-to under `guides/core/how-to/` | eugenelim | the how-to exists, passes the guide lints and is checked by a repository-level test | the how-to matches the shipped commands |
| Interface compatibility | The `answer` verb, the answer record, the hand-off record and the refusal codes are read by a controller later | the supervisor script, the manifest and the shipped instruction text | eugenelim | the verb, gate and end-to-end tests green | the instruction text defines `no-tty`, `no-human-answer`, `stale-digest` and `supervisor-changed` |
| Maintainer procedure | The session rules and the spec-plan driver line direct a session agent | `new-spec` and `work-loop` instruction text | eugenelim | the content-pin tests green | both files name the supervisor, `work-loop` names the fallback and points at the rules |
| Release history | A core pack file changes | `packs/core/pack.toml`, `plugin.json` and `docs/product/changelog.d/` | eugenelim | the changelog validates and the core release check passes | the core version is one patch above `main` at merge |
| Verification record | The live trials are manual evidence | `docs/specs/spec-supervisor-gates/notes/verification-ledger.md` | eugenelim | one ledger entry per trial | each trial entry exists |
| Current architecture | Page 05 of the unattended-delivery-runner set describes the gates | `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md` | eugenelim | the page reads the same as this spec where they overlap | no contradiction remains |
| Decision rationale | ADR-0162, ADR-0163 and ADR-0157 record the contract, the placement and approval | `docs/adr/` | eugenelim | the ADRs Accepted | none further |

## Agent Rules

### Always do

- Run the pack tests for the supervisor before reporting a task done.
- Run the answer verb tests through a pseudo-terminal, never by stubbing the terminal check.
- Keep the supervisor stdlib-only, as `work-supervisor.py` is.
- Cite ADR-0157 D4 in the plan wherever the supervisor stops at an approval, and keep every internal record citation out of anything added under `packs/`.

### Ask first

- Adding a request kind, a command, an answer-record field or a refusal code.
- Changing where the hand-off record or the answers file lives.
- Changing the options a `human-decision` request offers or the meaning of a decision.
- Widening an allowed edit of the answers file, the hand-off record, a status token or an approval-entry line.

### Never do

- Edit `work-supervisor.py` or any file in its pin set.
- Give the supervisor a verb, flag or default that writes `Status: Approved` or a Changelog approval line.
- Supply code trust, an authority ref or an intent from a supervisor default or from an agent's report.
- Add a new top-level dependency or a runtime import of a third-party package.
- Let a worker or the session agent write an answer record, the hand-off record, the ledger, an attempt record, `delivery/approvals.jsonl` or either supervisor's store or park records: only the supervisor, the human-run `answer` verb, the work supervisor's own `start` and the human write them.

## Testing Strategy

- **Answer verb (AC-0001, AC-0002, AC-0003, AC-0004, AC-0043, AC-0044):** TDD over a temporary repository with a parked gate made by the real `work-supervisor park`, driving `answer` through a pseudo-terminal, because each refusal is a compressible invariant on bytes and a terminal.
- **Answers file and hand-off protection (AC-0005):** TDD over real commits that alter, remove and append answer lines and that change `handoff.json` beside another file and while a delegate request is open.
- **Report consent rules, status, waits and decisions (AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014):** TDD over a temporary repository with real commits and recorded answers, killing and restarting the process at a waiting gate, because each decision and wait is a state transition.
- **Manifest (AC-0015):** goal-based, the schema validator and a driven run.
- **Delegated park, hand-off and command binding (AC-0016, AC-0017, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023):** TDD against the real installed `work-supervisor park`, because the argument and status refusals live in that script.
- **Delegated start and terminal confirmation (AC-0018, AC-0024, AC-0025, AC-0026):** TDD against the real installed `work-supervisor start`, because admission is that script's decision.
- **Amended core criteria (AC-0027):** goal-based, the amended core tests run in this change set.
- **Instruction text and driver line (AC-0028, AC-0029, AC-0030, AC-0031, AC-0032):** goal-based content pins in pack tests and a scan of added lines.
- **How-to (AC-0033, AC-0034, AC-0035, AC-0036):** goal-based, a repository-level suite and the guide lints, because guides sit outside every pack.
- **Release records (AC-0037, AC-0038, AC-0039, AC-0045):** goal-based, the changelog validator, the core release check, the self-host drift check and an eval-file check.
- **Whole flow (AC-0040):** an end-to-end pack test over a temporary repository that runs the real `park` and `start`.
- **Live trials (AC-0041, AC-0042):** manual QA in live sessions, recorded in the verification ledger.

## Acceptance Criteria

- [ ] **AC-0001.** `answer` refuses without a write or commit on each member of the closed answer-refusal set: no controlling terminal (`no-tty`), a run or request identity other than the open request (`request-not-open`), an unoffered decision or option (`option-not-offered`), or a failed typed confirmation (`digest-not-confirmed`); for a consent answer only, no pending parked gate (`gate-not-pending`) or unequal working-tree, recorded-commit and parked digests (`stale-digest`); for an approval-gate answer or a `retry` option, absent or invalid hand-off input (`hand-off-input-missing`).
- [ ] **AC-0002.** The digests on a recorded consent answer line equal the gate digests the supervisor computes from the `spec.md` and `plan.md` blobs at the parked commit, which equal the digests in the `pending` entry of the listing the gate's owner gives (the work supervisor's read-only `gates` for `spec-approved` and `plan-approved`, this supervisor's `gates` for `review-cap` and `review-weak`), and no digest in a worker report or an `answer` argument is read.
- [ ] **AC-0003.** The supervisor-owned `answer` prompt contains exactly the applicable fields of the closed prompt schema: run and open request identity, chosen decision or option, and confirmation instructions; for a consent, gate, both computed digests, parked commit and files to read; for `spec-approved`, `plan-approved` or `retry`, the four validated hand-off values at `HEAD`; no report, request prose or artifact prose appears in the prompt.
- [ ] **AC-0004.** Each answer commit changes only `answers.jsonl` by appending one line conforming to the closed answer schema: `run_id`, `request_id`, `by` (at most 64 characters, rejected before writing at 65), `at` and `identity: unverified`; a consent line additionally holds `gate`, `decision`, both digests and parked `commit`, with an optional `note` for `request-changes`; a human-decision line instead holds `option` and has no gate, digest or parked commit; approval-gate and `retry` lines additionally hold the four hand-off values shown to the human.
- [ ] **AC-0005.** `next` and `report` apply core AC-0013 refusal precedence to each member of the closed protected-record set: `answers.jsonl` permits only one well-formed appended line in a commit changing only that file, `handoff.json` permits only a single-file commit while no `delegate-verb` request is open, and attempt/answer records permit only their supervisor-owned writes; a detected violation returns `protected-content-changed`, with `answers-altered` or `handoff-altered` as the diagnostic cause for the corresponding file.
- [ ] **AC-0006.** `report` advances a `consent` request only when the answers file holds a line that names this run and the open request id, whose gate and digests equal those of the request's park record and whose time is after the park time this supervisor's own `park` recorded for that request, and refuses `no-human-answer` otherwise, whatever decision the result states.
- [ ] **AC-0007.** `report` on a `human-decision` request refuses `no-human-answer` unless the answers file holds a line that names this run and that request and an option the request offered, for each of the options `revise`, `abandon` and `retry`.
- [ ] **AC-0008.** `status` shows, for each request that has an answer line, the answer and its decision or option.
- [ ] **AC-0009.** After an approval-gate `approve` answer, `next` and consent `report` refuse `approval-commit-pending` without issuing a request or committing a ledger line until the human approval commit is at `HEAD`: `spec-approved` requires the existing spec status token `Approved` and the dated spec-approval entry in the plan Changelog; `plan-approved` requires the existing plan status token `Approved` and the dated plan-approval entry there.
- [ ] **AC-0010.** `next` refuses `revert-pending` without issuing the next request until `HEAD` reads spec `Draft` and plan `Drafting` after any approval-gate `request-changes` or `reject`, or any human-decision choice of `revise`, including one after a refused start.
- [ ] **AC-0011.** After an answer to `review-cap` or `review-weak`, `next` follows this meaning: `approve` accepts the residue and leads to the `spec-approved` gate, whose first request is the delegated `park`; `request-changes` issues `revise` when a sustained finding is open and then exactly one further `review-round` set, and no second one until a further answer is recorded; `reject` ends the run at stage `terminal` with the reason `rejected` and no further request.
- [ ] **AC-0012.** The allowance transition equals this closed decision map, with the round total unchanged: cap/weak `approve` and delegated `retry` keep the allowance; cap/weak `request-changes` sets it to round total plus 1; a revision after an approval-gate decision or a human-decision `revise`, including after refused start, sets it to round total plus `max_review_rounds`.
- [ ] **AC-0013.** After an answer to `spec-approved` or `plan-approved`, `next` follows this table once the wait of AC-0009 or AC-0010 has ended: `approve` leads to the delegated `park` of `plan-approved` or to the delegated `start`, `request-changes` leads to a `revise` request that carries the human's note, cut to 512 characters and marked untrusted, `reject` leads to a `human-decision` request that offers `revise` and `abandon`, and an `abandon` answer ends the run at stage `terminal` with the reason `abandoned`.
- [ ] **AC-0014.** No commit a supervisor verb makes changes a `Status:` line or a plan approval-entry line.
- [ ] **AC-0015.** The manifest matches the closed release schema: `supervisor-manifest.v1`, the seven emitted kinds (core AC-0005 as amended by AC-0027), and exactly the `work-supervisor` `park` and `start` entries in `delegates_to`.
- [ ] **AC-0016.** For each of `spec-approved` and `plan-approved`, `next` issues a `delegate-verb` request before its `consent` request, whose command is `python '<skill-dir>/scripts/work-supervisor.py' park <spec-dir> --gate <gate> --intent <intent> --code-trust <trust>` with `<skill-dir>` the resolved installed work-loop skill directory, and with `<intent>` and `<trust>` equal to the values in the hand-off record at `HEAD`.
- [ ] **AC-0017.** `next` refuses `work-loop-not-found` and issues no `delegate-verb` request when `scripts/work-supervisor.py` is not a regular file in the work-loop skill directory that sits beside the installed `new-spec` skill directory, in the `.claude/skills/` layout and the `.agents/skills/` layout.
- [ ] **AC-0018.** The delegated `start` command is `python '<skill-dir>/scripts/work-supervisor.py' start <spec-dir>` with `--approved-spec-digest` equal to the spec digest in the `spec-approved` answer, `--approved-plan-digest` equal to the plan digest in the `plan-approved` answer, and `--intent`, `--code-trust`, `--authority-ref` and `--review-authority-ref` equal to the four values the newest binding answer line recorded.
- [ ] **AC-0019.** For an answered consent, `answer`, `report` and `next` refuse `stale-digest` without advancing or issuing a delegated request when the current pair identity differs from the last reviewed identity or a bound answer digest differs from the current gate digest; unanswered-consent and in-progress-round changes follow core AC-0017 and AC-0034 instead.
- [ ] **AC-0020.** `next` refuses `handoff-changed` without issuing a delegated request when a hand-off value at `HEAD` differs from the newest binding answer, or, before the first binding answer, from the issued park values; recovery follows AC-0023.
- [ ] **AC-0021.** `next` refuses `hand-off-input-missing` without issuing a delegated request for each member of the closed invalid-input set: absent hand-off record at `HEAD`, invalid JSON, missing or repeated key, or value outside `intent` in `{code, spec-plan}`, `code_trust` in `{trusted, untrusted}`, `authority_ref` matching `owner:[0-9a-f]{12,64}`, and `review_authority_ref` matching `plan-reviewer` optionally followed by `:[0-9a-f]{12,64}`.
- [ ] **AC-0022.** `report` on a `delegate-verb` request refuses `command-mismatch`, and writes nothing, when the result's `command` is not, word for word, the command the request issued.
- [ ] **AC-0023.** Recovery follows the closed transition table: a refused delegated park or start opens a human-decision offering `retry`, `revise`, `abandon`; `retry` builds a new command from the four values bound by its answer after AC-0019, AC-0020 and AC-0021 pass; `revise` follows AC-0010 and AC-0012; `abandon` ends the run `abandoned`; `next` refusals `handoff-changed` and `stale-digest` open the same recovery human-decision, visible in `status`, where the human restores the bound input and answers `retry`, binds corrected hand-off values by answering `retry` again, or answers `revise` to reach review and a fresh approval gate for a changed pair under core AC-0017.
- [ ] **AC-0024.** The subject becomes `terminal` with the reason `admitted` only when the last line of `<spec-dir>/delivery/approvals.jsonl` at `HEAD` records, for the pair it recorded (`spec.md` and `plan.md` at the commit before the commit that added that line), digests equal to the approved digests under the core digest copy, and a `code_trust`, `terminal_intent`, `authority_ref` and `review_authority_ref` equal to the values in the issued `start` command, and the work supervisor's read-only `gates` lists no entry for the spec directory.
- [ ] **AC-0025.** The check of AC-0024 runs on every `start` result, whatever the result's status field says.
- [ ] **AC-0026.** A delegated start result produces `admission-mismatch` and opens recovery without ending the subject `admitted` when an admission record exists but fails AC-0024, regardless of reported status, or when no admission record exists despite a claim of `admitted`, `current` or `terminal`; recovery offers `retry`, `revise`, `abandon` under AC-0023.
- [ ] **AC-0027.** The core spec and its matching tests implement every amended reading in the closed Core amendment table below.
- [ ] **AC-0028.** The shipped instruction text states that the agent never runs `answer`, never writes an answer record, the hand-off record, the ledger, an attempt record, the policy file, a pinned file, `delivery/approvals.jsonl`, either supervisor's store or park records, `Status: Approved` or a Changelog approval line, never changes the git identity an answer commit carries, and never runs a `work-supervisor` command other than the issued one, word for word.
- [ ] **AC-0029.** The shipped rules section contains each member of the closed session-instruction set: read the decision from `status`; run one command per verb; name the file-write tool as “Write, apply_patch or equivalent”; define the action for each of `no-tty`, `no-human-answer`, `stale-digest`, `supervisor-changed`, `approval-commit-pending`, `revert-pending`, `handoff-changed`, `hand-off-input-missing`, `admission-mismatch`; show the four hand-off keys and accepted values; tell the human to run `answer` in a separate controlling terminal.
- [ ] **AC-0030.** The compact table of request kinds in the shipped instruction text lists exactly the kinds in the supervisor's manifest, each with its result-fact shape.
- [ ] **AC-0031.** No line this change adds to a file under `packs/` matches a record citation (`ADR-`, `RFC-`, a path under `docs/adr`, `docs/rfc` or `docs/architecture`, or the name of a spec directory under `docs/specs/`); the scan reads added lines only, so the `docs/specs/<feature>/` convention text already in `new-spec/SKILL.md`, `work-loop/SKILL.md` and the eval file is not counted.
- [ ] **AC-0032.** The spec-plan driver sentence in `work-loop` names `spec-supervisor` when installed, `references/pre-execute-review.md` otherwise, and the rules section of `new-spec/SKILL.md`.
- [ ] **AC-0033.** The how-to states that `ferryman` is later and optional.
- [ ] **AC-0034.** The how-to names the install prerequisites for driving the spec supervisor in a session and the human's steps for writing `handoff.json` and running `answer` in a separate terminal.
- [ ] **AC-0035.** The how-to names the routing: a user keeps invoking `new-spec` or `work-loop`, and `work-loop` drives the supervisor when it is installed.
- [ ] **AC-0036.** The guide lints `lint-guide-titles.py`, `check-guide-index.py` and `lint-guides-no-repo-only-refs.py` pass with the how-to present.
- [ ] **AC-0037.** Both release version files, `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`, carry the version one patch above `main`.
- [ ] **AC-0038.** `make build-self` leaves no diff in the `new-spec` and `work-loop` projections under `.claude/skills/` and `.agents/skills/`.
- [ ] **AC-0039.** The `new-spec` eval file holds a case whose expected behavior is one this release's shipped instruction text produces, and which drives the supervisor path.
- [ ] **AC-0040.** An end-to-end pack test runs the real installed `work-supervisor park` for both gates and `work-supervisor start`, with the human's `answer` runs and approval commits between them, and ends with the subject `terminal` with the reason `admitted`.
- [ ] **AC-0041.** The recorded three-try live resume trial across different CLIs meets the brief’s pass rule: fewer than two tries fail to resume a parked gate across a recorded answer from `status` alone with the same request id and no lost record, and any single failed try has its cause recorded before the brief closes.
- [ ] **AC-0042.** The verification ledger records one real spec reaching `terminal` with reason `admitted` in a live session through Draft, both real parks, human answers in a real terminal and delegated start.

- [ ] **AC-0043.** `answer` checks the admission pins before every other check and refuses `supervisor-changed` without writing when the installed scripts, manifest or policy differ from the admission pins, with recovery governed by core AC-0039.
- [ ] **AC-0044.** An answer is committed only when its accepted typed confirmation names the shown decision or option and still matches the displayed binding: for consents the working-tree digests and reviewed pair identity are rechecked at confirmation, and for approval gates or `retry` the four shown hand-off values are rechecked then.
- [ ] **AC-0045.** `python3 tools/changelog.py validate` passes with this release's changelog fragment.

### Core amendment table

Each row is an amendment in the gates release, after core ships; core owns the base behavior. eugenelim owns both contracts and every approval or review owner role.

| Core criterion | Amended reading |
| --- | --- |
| AC-0004, AC-0005 | Five kinds become seven: `delegate-verb` pairs with `delegating`; `human-decision` pairs with `awaiting-human`; AC-0015 governs the manifest. |
| AC-0010 | The refusal set adds `command-mismatch`, `answers-altered`, `handoff-altered`, and `no-human-answer` for `human-decision`; protected-record mutations retain the outer code of AC-0005. The fact sets add `delegate-verb: {command, exit, output}` and `human-decision: {}`; consent remains `{}`. Core's existing review, adjudication, author and revise fact sets remain core-owned. |
| AC-0013 | The protected set gains the records and allowed edits of AC-0005, under core's existing pin, ledger, then protected-content precedence. |
| AC-0014, AC-0015 | The approve-direction window is per gate, from issuance for the current reviewed revision until a later ledger line commits: only the existing first preamble status token changes, with the rest of the line byte-identical, and the corresponding dated entry in the plan's last `## Changelog` region changes. `spec-approved` covers the spec token and spec-approval entry; `plan-approved` covers the plan token and plan-approval entry. Compare the Changelog region after gate-digest normalisation (blank-run folding and trailing blanks). Revert to Draft/Drafting and remove entries whenever a gate is unanswered, including early approval before park, after request-changes/reject, and after human-decision revise/abandon. Cap/weak has no separate approval window. |
| AC-0016 | `delegate-verb` and `human-decision` have no worker-writable paths; the core exact-line ledger replay exception still applies. |
| AC-0017, AC-0034 | Answered-consent content changes use AC-0019 before any voiding; unanswered consent and in-progress round changes keep core AC-0017's voiding precedence. All consent issuance retains core AC-0017's last-round binding. |
| AC-0029 | A human-requested revision follows AC-0010's revert wait. |
| AC-0030 | Convergence leads to delegated park and then the spec-approved consent under AC-0016. |
| AC-0031 | The no-further-round rule gains AC-0012's retry/revise allowance transitions without resetting the round total. |
| AC-0032 | Cap/weak approve leads to the spec-approved gate whose first request is delegated park (AC-0011). |

## Follow-ons

- eugenelim: `ferryman` driving this supervisor with the scribe and the approval-fields guard — phase P0 of brief `ferryman-local-delivery`.
- eugenelim: `author-brief` and the `brief-ready` consent — they follow with the intake flow, and this spec stops at `plan-approved` and the hand-off.
- eugenelim: a stronger human-attribution check than `answer --by`, and a check of who commits an answer, a hand-off record or an approval — the Brief 1 owner waiver ends when `ferryman`'s guard and scribe run the supervisors.
- eugenelim: under `ferryman`, the hand-off values move to its trusted configuration set, and the `handoff.json` file stays the session-level source.

## Assumptions

- Defaulted: Technical: the manifest contract allows `ferryman-run` as the only mode of `delegate-verb`, and in a session the session agent fills the controller role that `ferryman-run` names, so no amendment to `spec:supervisor-manifest-contract` is made — default: that reading; if wrong: that spec amends its mode set (settled by: repository owner, eugenelim).
- Defaulted: Technical: the hand-off record is `handoff.json` in the spec directory with the keys `intent`, `code_trust`, `authority_ref` and `review_authority_ref`, written and committed by a human and never by a supervisor verb, a default or an agent — the sources say only that an authority reference comes from the human and never from a worker's output, and are silent on `--intent` and `--code-trust`; `next` reads the committed bytes at `HEAD` each time it issues a delegate request, and a change to it is accepted only in a commit that changes no other file while no `delegate-verb` request is open — default: that file; if wrong: the path and the instruction text change, or the values move to a trusted-configuration file (settled by: repository owner, eugenelim).
- Defaulted: Technical: the answers file is `answers.jsonl` in the spec directory and `answer` commits it itself; AC-0005 owns its permitted edits and refusal precedence — default: that file and one commit per answer; if wrong: the path and the commit rule change, and AC-0004 and AC-0005 follow (settled by: repository owner, eugenelim).
- Defaulted: Technical: a consent `answer` line holds both gate digests the park recorded, and the `spec-approved` answer supplies the spec digest to `start` while the `plan-approved` answer supplies the plan digest, as the work supervisor's reference says each approver's own answer supplies its digest — default: both values on each line; if wrong: AC-0018 reads one value per answer (settled by: repository owner, eugenelim).
- Defaulted: Technical: the refusal codes `request-not-open`, `gate-not-pending`, `digest-not-confirmed`, `option-not-offered`, `hand-off-input-missing`, `handoff-changed`, `handoff-altered`, `answers-altered`, `approval-commit-pending`, `revert-pending`, `command-mismatch`, `admission-mismatch` and `work-loop-not-found` are this spec's own names, while `no-tty`, `no-human-answer`, `stale-digest`, `parked` and `supervisor-changed` come from the sources — default: these names; if wrong: the criteria, the instruction text and the tests rename them (settled by: repository owner, eugenelim).
- Defaulted: Technical: `request-changes` is offered at `spec-approved` and `plan-approved` as well as the gates ADR-0157 D4 fixes (`approve`, `reject`), and it advances no gate, because page 05 names the decision and the sources give no other way to ask for a revision — default: offered, as an extension of the three-decision set; if wrong: the answer set at those gates reduces to `approve` and `reject` (settled by: repository owner, eugenelim).
- Defaulted: Technical: an optional `--note <text>` on `answer` carries the human's note for `request-changes` and is recorded on the answer line, because the sources name the note and not how it arrives — default: `--note`; if wrong: AC-0013's source for the note changes (settled by: repository owner, eugenelim).
- Defaulted: Technical: a refused `park` or `start` leads to a `human-decision` offering `retry`, `revise` and `abandon`, because three refusal codes (`intent-mismatch`, `invalid-authority-ref`, `gate-uncommitted`) are fixed by the human editing the hand-off record or committing, not by editing the spec — default: those three; if wrong: the option set and AC-0023 change (settled by: repository owner, eugenelim).
- Defaulted: Technical: the `human-decision` option `abandon` ends the run at stage `terminal` with the reason `abandoned`, and the option `revise` leads to a `revise` request after the wait of AC-0010 — default: those effects; if wrong: AC-0013 changes (settled by: repository owner, eugenelim).
- Defaulted: Technical: the work-loop skill directory is the sibling of the installed `new-spec` skill directory in each adapter layout the repository self-hosts (`.claude/skills/` and `.agents/skills/`), shown in a command as a repository-relative POSIX path when it lies inside the repository and as an absolute path otherwise — default: that resolution; if wrong: the criterion pins another resolution rule (settled by: repository owner, eugenelim).
- Defaulted: Technical: the supervisor confirms admission by reading the record `work-supervisor start` commits, because no field of its read-only `status` or `gates` output carries an admitted digest pair; the record's `base` is the first pair's commit for every later pair, so the pair is read at the commit before the commit that added the last line, and the record's `spec_policy_fingerprint` is not compared because it hashes the spec without the approval-entry drop that the gate digest applies — default: the record read AC-0024 describes; if wrong: the work supervisor gains a read-only field in a separate change, which this repository's pin rules make a release event (settled by: repository owner, eugenelim).
- Defaulted: Technical: the `run_id` of an admission record is not compared as proof, because the work supervisor takes `run.run_id` from the first line of the same file and the comparison is circular — default: no run id comparison; if wrong: a later work-supervisor field supplies an independent run id (settled by: repository owner, eugenelim).
- Accepted risk: the terminal check does not separate a human from an agent, because an agent can spawn a pseudo-terminal, run `answer`, and write a well-formed answer record, hand-off record or approval commit; the shipped instruction text is the only mitigation until `ferryman`'s guard and scribe exist. The Brief 1 owner waiver covers an unchecked identity only, and does not cover an agent that forges a record or answers through a pseudo-terminal (settled by: repository owner, eugenelim; not covered by the Brief 1 owner waiver).
- Accepted risk: the supervisor checks the timing and lines of an approval commit and not its author, so an agent can write `Status: Approved` and the approval entry, run delegate commands with changed arguments, or change the git identity an answer commit carries; `command-mismatch` and the binding of AC-0018 and AC-0020 close the cases where the supervisor sees the command or the hand-off value (settled by: repository owner, eugenelim; not covered by the Brief 1 owner waiver).
- Accepted risk: a forged admission record goes undetected: a hand-written `delivery/approvals.jsonl` line that meets AC-0024 ends the subject `admitted` without a real `start`, because the file is committed content outside the protected set and the check proves that a well-formed record exists for those digests and not that a real `start` ran (settled by: repository owner, eugenelim; not covered by the Brief 1 owner waiver; closed by the work supervisor's own admission check and `ferryman`'s guard).
- Accepted risk: a history rewrite between steps is not detected by this supervisor, because it compares digests and commits but keeps no signed anchor (settled by: repository owner, eugenelim; not covered by the Brief 1 owner waiver).
- Accepted risk: the `review-weak` flag, the independence of a review and the adjudicator-profile refusal rest on self-reported agent definitions and agent-supplied report files, as `spec:spec-supervisor-core` states (settled by: repository owner, eugenelim; not covered by the Brief 1 owner waiver).
- Product: the Brief 1 owner waiver covers an unchecked identity only (the `by` name is not verified) and covers no other control or risk named here.
