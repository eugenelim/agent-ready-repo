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

> **Contract:** Agent Rules, Testing Strategy, Acceptance Criteria and accepted risks govern completion; changes require amendment. Other sections are working context.

## Outcome

A human answers parked gates with bindings to the reviewed pair and hand-off values. Delegated park/start carry the approved pair to work-supervisor; only a matching new admission record ends the subject. This proves record existence, not authorship or execution.

## What Changes

- `packs/core/.apm/skills/new-spec/`: answer, records, hand-off, delegation, decisions, manifest and session instructions.
- Work-loop driver sentence outside its pin set; how-to under `guides/core/how-to/` with registered `tools/` tests.
- Pack tests, release records, projections, eval, trials and page 05. Core amendments follow AC-0027; scope ends at hand-off, before `author-brief`.

## Durable Outputs

eugenelim owns all outputs and repository, contract, review and risk roles.

| Output | Destination | Closeout evidence |
| --- | --- | --- |
| Interface/instructions | `new-spec`, work-loop driver | verb and content-pin tests |
| User promise | `guides/core/how-to/` | guide tests/lints |
| Release | core versions, changelog, projections, eval | T8 checks |
| Trials | `notes/verification-ledger.md` | AC-0041, AC-0042 |
| Architecture | page 05 | T10 consistency |

ADRs retain decision rationale.

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

- **T1 (AC-0001, AC-0002, AC-0003, AC-0004, AC-0043, AC-0044, AC-0047, AC-0048):** TDD, real commits and bounded inputs; cases in plan T1.
- **T2 (AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0046):** TDD, real commits and bounded inputs; cases in plan T2.
- **T3 (AC-0016, AC-0017, AC-0020, AC-0021, AC-0022, AC-0023, AC-0049):** TDD, real commits and bounded inputs; cases in plan T3.
- **T4 (AC-0018, AC-0019, AC-0024, AC-0025, AC-0026, AC-0040):** TDD, real commits and bounded inputs; cases in plan T4.
- **T5 (AC-0015, AC-0027):** TDD, real commits and bounded inputs; cases in plan T5.
- **T6 (AC-0028, AC-0029, AC-0030, AC-0031, AC-0032):** TDD, real commits and bounded inputs; cases in plan T6.
- **T7 (AC-0033, AC-0034, AC-0035, AC-0036):** goal-based checks; cases in plan T7.
- **T8 (AC-0037, AC-0038, AC-0039, AC-0045):** goal-based checks; cases in plan T8.
- **T9 (AC-0041, AC-0042):** manual live trials; cases in plan T9.

## Acceptance Criteria

- [ ] **AC-0001.** `answer` refuses without writes for this closed set: no terminal (`no-tty`); no open request, wrong gate, option during consent or gate answer during human-decision (`request-not-open`); unreviewed-cap approve (`approve-unreviewed`, before `option-not-offered`); other unoffered choice (`option-not-offered`); failed confirmation (`digest-not-confirmed`); already answered request (`already-answered`, before binding checks); mismatched pending answer (`pending-answer-mismatch`); consent digest mismatch among working tree, parked commit and valid record (`stale-digest`, before `gate-not-pending`); otherwise absent pending gate (`gate-not-pending`); approval-gate missing script (`work-loop-not-found`, before `gate-not-pending`) or changed valid park values (`handoff-changed`); invalid/missing hand-off for approval or retry (`hand-off-input-missing`).
- [ ] **AC-0002.** Recorded consent digests equal computed spec/plan digests at the parked commit and the owning supervisor’s pending listing: work-supervisor for approval gates, spec-supervisor for cap/weak; worker reports and answer arguments supply none.
- [ ] **AC-0003.** The answer prompt contains only its closed schema: run/request, chosen decision/option, confirmation instructions; consent also shows gate, computed digests, park commit, files and fixed unreviewed marker/text; approval/retry also shows four validated HEAD hand-off values.
- [ ] **AC-0004.** Each answer commit appends only one answers.jsonl line matching this closed schema: run_id, request_id, by (at most 64 characters), at, identity: unverified; consent adds gate, decision, both digests, parked commit and optional request-changes note; human-decision instead adds option without gate/digests/park; approval/retry adds the four displayed hand-off values.
- [ ] **AC-0005.** Next/report apply core AC-0013 precedence to protected records: answers.jsonl permits one well-formed append in a single-file commit; handoff.json permits single-file commits only without an open delegate; attempt/answer records permit supervisor-owned writes only; violations return protected-content-changed with answers-altered/handoff-altered as applicable diagnostic cause.
- [ ] **AC-0006.** Consent report advances only on an answer matching run/request, park gate/digests and time after this request’s own parked_at, otherwise refusing no-human-answer regardless of reported decision.
- [ ] **AC-0007.** `report` on a `human-decision` request refuses `no-human-answer` unless the answers file holds a line that names this run and that request and an option the request offered, for each of the options `revise`, `abandon` and `retry`.
- [ ] **AC-0008.** `status` shows, for each answered request, its first valid committed answer and decision or option.
- [ ] **AC-0009.** After approval-gate approve, next/consent report refuse approval-commit-pending without requests/ledger commits until HEAD contains the matching Approved token and dated Changelog entry: spec token/spec-entry for spec-approved, plan token/plan-entry for plan-approved.
- [ ] **AC-0010.** `next` refuses `revert-pending` without issuing the next request until `HEAD` reads spec `Draft` and plan `Drafting` after any approval-gate `request-changes` or `reject`, or any human-decision choice of `revise`, including one after a refused start.
- [ ] **AC-0011.** Cap/weak decisions follow this map: unreviewed request-changes opens one round on current identity without revise; reviewed approve leads to delegated spec-approved park; reviewed request-changes revises if sustained findings remain then opens one round; reject ends terminal/rejected without requests; no second round opens without another answer.
- [ ] **AC-0012.** The allowance transition equals this closed decision map, with the round total unchanged: reviewed cap/weak `approve`, cap/weak `reject` and delegated `retry` keep the allowance; cap/weak `request-changes`, including unreviewed `review-cap`, sets it to round total plus 1; a revision after an approval-gate decision or a human-decision `revise`, including after refused start, sets it to round total plus `max_review_rounds`.
- [ ] **AC-0013.** After an answer to `spec-approved` or `plan-approved`, `next` follows this table once the wait of AC-0009 or AC-0010 has ended: `approve` leads to the delegated `park` of `plan-approved` or to the delegated `start`, `request-changes` leads to a `revise` request that carries the human's note, cut to 512 characters and marked untrusted, `reject` leads to a `human-decision` request that offers `revise` and `abandon`, and an `abandon` answer ends the run at stage `terminal` with the reason `abandoned`.
- [ ] **AC-0014.** No commit a supervisor verb makes changes a `Status:` line or a plan approval-entry line.
- [ ] **AC-0015.** The manifest matches the closed release schema: `supervisor-manifest.v1`, the seven emitted kinds (core AC-0005 as amended by AC-0027), and exactly the `work-supervisor` `park` and `start` entries in `delegates_to`.
- [ ] **AC-0016.** For each of `spec-approved` and `plan-approved`, `next` issues a `delegate-verb` request before its `consent` request, whose command is `python '<skill-dir>/scripts/work-supervisor.py' park <spec-dir> --gate <gate> --intent <intent> --code-trust <trust>` with `<skill-dir>` the resolved installed work-loop skill directory, and with `<intent>` and `<trust>` equal to the values in the hand-off record at `HEAD`.
- [ ] **AC-0017.** `next` refuses `work-loop-not-found` and issues no `delegate-verb` request when `scripts/work-supervisor.py` is not a regular file in the work-loop skill directory that sits beside the installed `new-spec` skill directory, in the `.claude/skills/` layout and the `.agents/skills/` layout.
- [ ] **AC-0018.** The delegated `start` command is `python '<skill-dir>/scripts/work-supervisor.py' start <spec-dir>` with `--approved-spec-digest` equal to the spec digest in the `spec-approved` answer, `--approved-plan-digest` equal to the plan digest in the `plan-approved` answer, and `--intent`, `--code-trust`, `--authority-ref` and `--review-authority-ref` equal to the four values the newest effective binding answer line recorded.
- [ ] **AC-0019.** Answered consent refuses stale-digest in answer/report/next without advancing when current pair identity differs from its bound reviewed/unreviewed identity or an answer digest differs from current gate digest; unanswered/pre-consent (including delegated park)/in-progress changes instead follow core AC-0044 before report advancement or consent issuance.
- [ ] **AC-0020.** `next` refuses `handoff-changed` without issuing a delegated request only after AC-0021 validation succeeds, when a valid hand-off value at `HEAD` differs from the newest effective binding answer, or, before the first binding answer, from the issued park values; recovery follows AC-0023.
- [ ] **AC-0021.** Before the binding comparison of AC-0020, `next` refuses `hand-off-input-missing` without issuing a delegated request or opening AC-0023 recovery for each member of the closed invalid-input set: absent hand-off record at `HEAD`, invalid JSON, missing or repeated key, or value outside `intent` in `{code, spec-plan}`, `code_trust` in `{trusted, untrusted}`, `authority_ref` matching `owner:[0-9a-f]{12,64}`, and `review_authority_ref` matching `plan-reviewer` optionally followed by `:[0-9a-f]{12,64}`.
- [ ] **AC-0022.** `report` on a `delegate-verb` request refuses `command-mismatch`, and writes nothing, when the result's `command` is not, word for word, the command the request issued.
- [ ] **AC-0023.** Recovery follows this closed map after core AC-0014’s exact early-approval restoration exception: refused park/start or next’s handoff-changed/stale-digest opens a status-visible human-decision; retry rebuilds from its four bound values after AC-0019–AC-0021 pass; revise follows AC-0010/AC-0012 toward fresh review/approval; abandon ends abandoned. Retry permits restored bound inputs or corrected hand-off values, never approval of changed pair content.
- [ ] **AC-0024.** Terminal/admitted requires the last delivery/approvals.jsonl line at HEAD, added in a commit strictly descending from this start request’s issuance commit, to match approved gate digests of the pair before that adding commit and issued code_trust/terminal_intent/authority_ref/review_authority_ref, with no work-supervisor gates entry for the directory.
- [ ] **AC-0025.** The check of AC-0024 runs on every `start` result, whatever the result's status field says.
- [ ] **AC-0026.** Start recovery reports admission-mismatch for a new AC-0024 record failing remaining checks, regardless of reported status, or admitted/current/terminal claims without a new record; actual refusal without a new record retains start’s refusal code under AC-0023, even with an older admission line.
- [ ] **AC-0027.** The core spec and its matching tests implement every amended reading in the closed Core amendment table below.
- [ ] **AC-0028.** Shipped instructions forbid agents to run answer; write answers, handoff, ledger, attempts, policy, pins, delivery/approvals.jsonl, either store/park record, Approved status or approval entries; change answer-commit identity; or run any work-supervisor command other than the issued command word for word.
- [ ] **AC-0029.** The shipped rules include this closed instruction set: read decisions from status; one command per verb; file tool “Write, apply_patch or equivalent”; actions for no-tty, no-human-answer, stale-digest, supervisor-changed, approval-commit-pending, revert-pending, handoff-changed, hand-off-input-missing, admission-mismatch and approve-unreviewed (request-changes to review or reject to stop); four hand-off keys/forms; human answer in a separate controlling terminal.
- [ ] **AC-0030.** The compact table of request kinds in the shipped instruction text lists exactly the kinds in the supervisor's manifest, each with its result-fact shape.
- [ ] **AC-0031.** Added pack lines contain no ADR-/RFC-/docs/adr/docs/rfc/docs/architecture or spec-directory citation; existing docs/specs convention text in skills/evals is excluded from the added-line scan.
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

- [ ] **AC-0043.** `answer` checks the admission pins after core AC-0003 confinement and before every other check and refuses `supervisor-changed` without writing when the installed scripts, manifest or policy differ from the admission pins, with recovery governed by core AC-0039.
- [ ] **AC-0044.** A committed answer’s typed confirmation matches the shown choice and current binding: consent working-tree digests, bound pair identity and unreviewed marker; approval/retry’s four displayed hand-off values.
- [ ] **AC-0045.** `python3 tools/changelog.py validate` passes with this release's changelog fragment.

- [ ] **AC-0046.** The first valid committed answer to a request remains its only effective answer; any later duplicate or conflicting answer is refused `already-answered` with no effect on that decision.
- [ ] **AC-0047.** Rerunning `answer` with the same input after interruption between append and commit leaves exactly one committed answer for that request.
- [ ] **AC-0048.** Rerunning `answer` with input that differs from the pending uncommitted answer refuses `pending-answer-mismatch` with that line untouched.
- [ ] **AC-0049.** `answer` refuses `handoff-changed` for an approval gate when valid `intent` or `code_trust` at `HEAD` differs from the values issued with that gate’s delegated park.

### Core amendment table

Each row is an amendment in the gates release, after core ships; core owns the base behavior. eugenelim owns both contracts and every approval or review owner role.

| Core criterion | Amended reading |
| --- | --- |
| AC-0002 | Historical admission permits only a transition authorised by a prior answer whose schema meets AC-0004 and whose binding meets AC-0006 for consent or AC-0007 for human-decision, under the decision and allowance rules AC-0011, AC-0012, AC-0013 and AC-0023; absent, malformed, wrong-run or wrong-request answers confer no bypass. |
| AC-0004, AC-0005 | Five kinds become seven: `delegate-verb` pairs with `delegating`; `human-decision` pairs with `awaiting-human`; AC-0015 governs the manifest. |
| AC-0010 | Consent completion requires AC-0006’s matching answer; no-human-answer becomes conditional and also covers human-decision. Add command-mismatch and protected-record diagnostics answers-altered/handoff-altered under AC-0005’s outer code. Facts add delegate-verb: {command, exit, output} and human-decision: {}; consent remains {}, and existing fact sets stay core-owned. |
| AC-0013 | The protected set gains the records and allowed edits of AC-0005, under core's existing pin, ledger, then protected-content precedence. |
| AC-0014, AC-0015 | Approval windows run from reviewed-consent issuance to the next ledger commit: spec-approved permits spec token/spec-entry; plan-approved permits plan token/plan-entry; cap/weak opens none. Existing status-line bytes except the token remain identical; dated entries occupy the last exact Changelog region with core’s blank normalization. Draft/Drafting reverts and entry removal are permitted for unanswered gates, request-changes/reject and human-decision revise/abandon; core’s exact early-approval restoration exception also applies to refused-delegate report/retry, excusing no other protected edit. |
| AC-0016 | `delegate-verb` and `human-decision` have no worker-writable paths; the core exact-line ledger replay exception still applies. |
| AC-0017, AC-0034, AC-0044 | Answered-consent changes use AC-0019 first, then waits/decisions AC-0009–AC-0011 and AC-0013; unanswered/pre-consent/in-progress changes retain core voiding, including voiding an open delegated park before consent. Spec-approved after cap/weak approve binds the same last reviewed revision; other issuance retains core’s reviewed/current-unreviewed binding map and marker. AC-0001 refuses unreviewed approve; AC-0011/AC-0012 own legal decisions and allowance. |
| AC-0029 | A human-requested revision follows AC-0010's revert wait. |
| AC-0030 | Convergence leads to delegated park and then the spec-approved consent under AC-0016. |
| AC-0031 | The no-further-round rule gains AC-0012's retry/revise allowance transitions without resetting the round total. |
| AC-0032 | Reviewed cap/weak approve leads to the spec-approved gate whose first request is delegated park (AC-0011). Unreviewed cap permits only request-changes or reject under core AC-0032; AC-0001 refuses approve as `approve-unreviewed`. |

## Follow-ons

eugenelim owns `ferryman` guard/scribe, unattended driving and trusted hand-off configuration, stronger human attribution, and later `author-brief`/`brief-ready` support.

## Assumptions

eugenelim settles every default and accepts every risk below.

- Defaults: `delegate-verb` uses manifest mode `ferryman-run`; a session agent fills that controller role. The work-loop skill is the installed sibling in both adapters; commands use repository-relative paths inside the repository and absolute paths outside it.
- Defaults: humans commit `handoff.json`; answer commits `answers.jsonl`. First valid answer wins; names, schema, refusals, note, recovery options and allowances are defined above.
- Defaults: request-changes extends ADR-0157 D4 at approval gates without advancing approval. Each consent answer holds both digests; each approval supplies its own artifact's digest to start.
- Defaults: admission uses the pair before the line-adding commit, not `base` (which remains the first pair's commit). Neither spec_policy_fingerprint nor run_id proves the admitted pair; no read-only work-supervisor field exposes it.
- Accepted risk: an agent can use a pseudo-terminal or forge answers, hand-off and approval commits; instructions are the mitigation until guard/scribe.
- Accepted risk: checks cannot prove approval authorship or commit identity; command and hand-off binding catch only visible changes.
- Accepted risk: a forged new admission line meeting AC-0024 can end the subject without a real start; work-supervisor admission and guard provide the later boundary.
- Accepted risk: history rewrites lack a signed anchor.
- Accepted risk: review independence, weak flags and adjudicator exclusion depend on self-reported profiles and supplied files.

The Brief 1 waiver covers unchecked `by` identity only, not these risks.
