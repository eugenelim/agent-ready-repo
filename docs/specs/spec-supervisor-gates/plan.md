# Plan: Spec supervisor gates and hand-off

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/.apm/skills/work-loop/scripts/` supplies the read-only oracle: `review-artifact.py`, `_supervisor_gates.py`, `_loop_guards.py`, `_supervisor_admission.py` and `work-supervisor.py`.

> **Contract:** Touches, Tests and Done when govern completion. Design and approach are working material; spec contract changes require amendment. Execution evidence belongs in `notes/verification-ledger.md`.

## Approach

Build answer binding and recovery, then protection/decisions, park, start and admission confirmation. Run live trials after T4 and before finalizing the how-to. Ship core amendments and instructions together.

## Constraints

- eugenelim holds every repository, contract, review and risk owner role.
- ADR-0162 defines commands; ADR-0163 forbids work-loop runtime imports and pin-set changes; ADR-0157 D4 reserves approval for humans.
- Pack rules forbid internal citations and require UTF-8 stdout/stderr, matching version bumps and isolated test imports. No added pack line contains internal record citations.
- Core ships five kinds first; gates adds seven-kind behavior through gates AC-0027. Neither release edits work-loop pins.

## Construction tests

T4 drives real park/start and human answers through pseudo-terminals. T9 adds live trials; T7 uses repository-level guide tests because pack tests cannot read guides.

## Durable-output map

T1–T5 deliver interface/records; T6 instructions; T7 guide; T8 release/projections/eval; T9 trial evidence; T10 page 05. Their Done when checks provide closeout evidence.

## Design (LLD)

### Seam with core

Core owns AC-0035/AC-0036 park records and listing, digest equivalence, pair identity, marker, voiding and resume. Gates AC-0027 lists every amendment, including conditional consent completion, approve-after-cap/weak identity and delegated-park voiding.

The seven-kind manifest adds delegate-verb in ferryman-run mode and human-decision in human mode. A session agent fills the controller role; delegates_to names only work-supervisor park/start.

Owned by: T1, T2, T5

### Interfaces & contracts

`answer <spec-dir> <gate> --decision <approve|reject|request-changes> --by <name> [--note <text>]` answers consent. `answer <spec-dir> --option <retry|revise|abandon> --by <name>` answers human-decision, without gate/park checks.

Resolve work-loop beside installed new-spec in both adapters; missing script refuses work-loop-not-found for next and approval-gate answer. The exact commands and sources are AC-0016/AC-0018; use `python '<skill-dir>/scripts/work-supervisor.py'`, not an executable alias.

Delegate results are `{"request_id", "facts": {"command", "exit", "output"}}`, with core bounds. Check command equality before output; human-decision carries the bounded untrusted refusal code and offered options.

AC-0001 owns answer refusals, including observable request mismatch, already-answered and pending-answer-mismatch. Confinement precedes pins; pins precede remaining checks; missing script precedes gate-not-pending.

Owned by: T1, T3, T4

### Data & schema

AC-0004 owns both answer schemas; only the first valid committed answer per request is effective. The newest effective binding answer supplies hand-off values: spec approval before plan park, plan approval before start, or retry after refusal.

Humans commit handoff.json, with AC-0021's four fields and forms. Answer compares approval intent/code_trust with issued park values before binding them; confirmation rechecks displayed values, decision, digests, identity and marker.

Owned by: T1, T2, T3

### State & control flow

ADR-0157 D4 sequence: delegated park, delegate report, consent, own park, human answer, human approval commit, consent report, next command. Real spec park needs Draft; plan park needs Approved/Drafting; work-supervisor listing checks status at the parked commit, so approval alone does not stale it.

Consent report waits approval-commit-pending until the token/entry commit, preserving its edit window. Request-changes/reject and human-decision revise wait revert-pending; humans alone restore Draft/Drafting.

AC-0011–AC-0013 own decisions and counters: reviewed approve preserves the last reviewed identity; unreviewed cap permits only request-changes or reject. Retry binds corrected hand-off values; changed pair content requires fresh review/approval, not retry acceptance.

After each start result, consider only a last approvals.jsonl line added by a commit strictly descending from request issuance. Old records do not mask the refusal returned by start.

Read the pair at the parent of the line-adding commit: start checks working bytes then commits approvals.jsonl alone. Its base remains the first pair's commit; spec_policy_fingerprint omits gate approval-entry dropping, and run_id comes from the same file, so none proves the approved pair.

Compare pair digests, four issued values and absence from real gates. A new mismatched line or an admission claim without one opens admission-mismatch recovery; an actual refusal without a new line retains its own code, even with an older record.

Recovery offers retry/revise/abandon under AC-0023. Handoff-changed and stale-digest from next expose the same recovery through status; invalid hand-off input opens none.

Owned by: T2, T3, T4

### Failure, edge cases & resilience

After append-before-commit interruption, identical answer input commits exactly one answer; different input refuses pending-answer-mismatch and leaves the pending line untouched. A later duplicate/conflicting committed answer refuses already-answered without changing the first decision.

Core handles waiting-gate restart, first-parent protection and net pin restoration. History rewrites and forged records retain the spec's accepted risks.

Owned by: T1, T2, T4

### Behavior & rules

New-spec instructions carry prohibitions, human steps, refusal actions and a manifest-checked kind/result table. The work-loop driver names supervisor, fallback and rules section; no internal citation enters added pack text.

Owned by: T6

## Tasks

### T1: The answer verb and its binding

**Satisfies:** AC-0001, AC-0002, AC-0003, AC-0004, AC-0043, AC-0044, AC-0047, AC-0048

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/scripts/` (the `answer` code, in a new helper module whose name is `implementation-discovered`), `packs/core/tests/skills/new-spec/test_spec_supervisor_answer.py`

**Tests:**

Mode: TDD, real temporary repository, real work-supervisor park, pseudo-terminal answer.

- AC-0001 cases: no terminal; no open request; wrong gate; option during consent; gate answer during human-decision; absent gate; stale listing/differing working, recorded or parked digest; mistyped confirmation; unoffered decision/option; unreviewed approve; invalid/missing hand-off. Stale precedes gate-not-pending; approve-unreviewed precedes option-not-offered.
- Missing work-loop script in both layouts yields work-loop-not-found before gate-not-pending (AC-0001). Worker/argument digests are ignored; recorded digests equal computed/listed values (AC-0002).
- Exact prompt fields, chosen decision, hand-off and both marker values contain no report prose (AC-0003); both answer schemas, 65-character by refusal and single-file commits (AC-0004).
- Confinement precedes pins; changed pins beat terminal/request/digest faults, restored installation passes (AC-0043). Change digest, identity, marker or hand-off while confirmation waits: no answer commit (AC-0044).
- Human-decision options need no gate/digest/park; retry validates and records four values; cap/weak retains its own digest checks.
- Kill after append before commit: same input yields exactly one committed answer; different input yields pending-answer-mismatch with the pending line untouched (AC-0047, AC-0048).

**Done when:** the T1 tests pass.

### T2: Answers protection, report consent rules, waits and decisions

**Satisfies:** AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0046

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/new-spec/scripts/`, `packs/core/tests/skills/new-spec/test_spec_supervisor_consent.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_answers_file.py`

**Tests:**

Mode: TDD with real commits and restarts.

- Edit/remove/reorder/second-line append, answer plus another file, and hand-off plus another file or during delegate all refuse protected-content-changed with answers-altered/handoff-altered cause. Pins precede ledger precede protected records; valid single-file updates pass (AC-0005).
- Consent needs matching run/request/gate/digests and time after parked_at; missing/wrong/earlier-request/pre-park answers refuse no-human-answer regardless of report (AC-0006). Restart preserves status/next/report behavior.
- Human-decision rejects absent/earlier/unoffered answers and accepts each offered option; status shows effective answer (AC-0007, AC-0008).
- For consent and human-decision, duplicate and conflicting answers in separate valid single-file commits refuse already-answered without replacing the first decision; answer refuses a second write (AC-0046).
- Approve waits approval-commit-pending with no ledger write through restart, until matching token/entry commit; window ends at consent ledger line. Request-changes/reject and every human-decision revise, including refused Approved/Approved start, wait revert-pending (AC-0009, AC-0010).
- All reviewed cap/weak decisions, weak-last-round priority, delegated spec park after approve, revise when needed and exactly one further round follow AC-0011/AC-0012. Retry preserves allowance; each revision path uses its specified allowance.
- Unreviewed cap request-changes keeps total, sets allowance total+1, reviews current identity without revise despite old findings; no second round without an answer. Reject ends rejected with counters unchanged.
- Every AC-0013 decision, bounded untrusted note and abandon; every supervisor verb leaves status/approval lines untouched (AC-0014).

**Done when:** the T2 tests pass.

### T3: Hand-off record and delegated park

**Satisfies:** AC-0016, AC-0017, AC-0020, AC-0021, AC-0022, AC-0023, AC-0049

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/new-spec/scripts/`, `packs/core/tests/skills/new-spec/test_spec_supervisor_park.py`

**Tests:**

Mode: TDD against real installed park/gates.

- Each runnable gate command uses hand-off values (AC-0016); missing script in both layouts refuses (AC-0017).
- Absent/malformed/missing/repeated/out-of-form hand-off keys and issue-to-report edits never use defaults/reports (AC-0021). Test authority hex lengths 11/12/64/65 and uppercase.
- Word/quote/trailing-argument differences refuse command-mismatch (AC-0022). Real gate-uncommitted, gate-status-mismatch and intent-mismatch open retry/revise/abandon recovery (AC-0023).
- Each approval answer, including first spec-approved, refuses handoff-changed when valid intent or code_trust differs from issued park values (AC-0049).
- Agent Rules changes during delegated park void it before report/consent: further round below allowance, fresh unreviewed cap at allowance (AC-0016, AC-0019, AC-0027; core AC-0017, AC-0044).
- Early plan approval followed by real refusal and exact revert before a ledger commit permits report/retry; partial restoration, later ledger commit or another protected edit refuses (AC-0023, AC-0027).
- After binding, invalid code_trust returns only hand-off-input-missing without recovery; valid changed value returns handoff-changed with recovery (AC-0020, AC-0021, AC-0023). Retry with corrected values builds a new command matching its answer; invalid retry input refuses.

**Done when:** the T3 tests pass.

### T4: Delegated start, digest re-check and terminal confirmation

**Satisfies:** AC-0018, AC-0019, AC-0024, AC-0025, AC-0026, AC-0040

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/new-spec/scripts/`, `packs/core/tests/skills/new-spec/test_spec_supervisor_start.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_end_to_end.py`

**Tests:**

Mode: TDD against real installed start, plus real end-to-end flow.

- Start's own commit is accepted; command carries two approved digests/four bound values (AC-0018). Post-answer pair edit refuses stale-digest; changed hand-off refuses plan park/start; actual refusal opens recovery (AC-0019, AC-0020, AC-0023).
- Admitted/current/terminal claims with wrong digests, values, pair commit or remaining gate refuse. Real code/spec-plan admission, including a second pair whose base remains the first commit, ends admitted; hand-written matching new line documents forgery risk (AC-0024).
- Check every result, including failure/empty status (AC-0025). New mismatched record or admission claim without a new record yields admission-mismatch; actual refusal without a new record preserves its code (AC-0026).
- Earlier admission line plus a refused start still reports intent-mismatch, not admission-mismatch. Only a line added strictly after request issuance qualifies (AC-0024, AC-0026).
- Real parks, pseudo-terminal answers, human approval commits and real start end terminal/admitted; abandoned fails that assertion (AC-0040).
- Recover next's stale-digest/handoff-changed through restored input+retry, corrected hand-off+retry or revise/revert/review/fresh approval; never reuse old approval for changed pair (AC-0019, AC-0020, AC-0023).
- Risk triggers/Agent Rules/accepted-risk changes invalidate answered consent; identity-only changes also refuse with unchanged gate digest. Unanswered/pre-consent/in-progress changes follow core voiding; unchanged unreviewed request-changes/reject binds current identity, later edit refuses (AC-0019).

**Done when:** the T4 tests pass.

### T5: Manifest and the amended core criteria

**Satisfies:** AC-0015, AC-0027

**Depends on:** T4

**Touches:** `docs/specs/spec-supervisor-core/spec.md`, `packs/core/.apm/skills/new-spec/supervisor.toml`, `packs/core/tests/skills/new-spec/test_spec_supervisor_manifest.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_admission.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_requests.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_rounds.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_consent.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_ledger.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_protected.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_revision.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_resume.py`

**Tests:**

Mode: goal-based manifest/amendment checks and TDD transition tests.

- Manifest validates seven driven kinds and both delegates_to entries (AC-0015).
- Amend all AC-0027 rows: core AC-0002, AC-0004, AC-0005, AC-0010, AC-0013–AC-0017, AC-0029–AC-0032, AC-0034, AC-0044. Core owns outcome enums/facts and classifier-derived invalid/indeterminate stops.
- Core always refuses consent completion; gates adds matching-answer completion, approve-after-cap/weak binding, delegated-park voiding and answer-driven waits. Historical transitions require valid prior request-bound answers; malformed/absent/wrong-run/request answers grant none.
- Per-gate token/entry edits accept blank-line normalization; status suffix/prefix stays identical. Insert/delete/wrong-gate/wrapped/late edits refuse; unanswered and answer-driven reverts pass only in listed windows; cap/weak opens none.
- Delegate facts are exactly command/exit/output; human-decision/consent facts empty and need answers; delegate/human-decision writable paths empty. Replay reads committed ledger and accepts only byte-identical pending recovery.
- Combined faults preserve pin/ledger/protected order; merges use first parents and pin restoration uses net changes (AC-0005, AC-0027).

**Done when:** the T5 tests pass.

### T6: Instruction text and the work-loop driver line

**Satisfies:** AC-0028, AC-0029, AC-0030, AC-0031, AC-0032

**Depends on:** T5

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`, `packs/core/.apm/skills/work-loop/SKILL.md`, `.claude/skills/work-loop/`, `.agents/skills/work-loop/`, `packs/core/tests/skills/new-spec/test_spec_supervisor_instructions.py`

**Tests:**

Mode: goal-based content pins scoped to the owning section.

- Prohibitions (AC-0028), positive rules, all ten action codes including approve-unreviewed, and human steps (AC-0029); kind/result table equals manifest (AC-0030).
- Added-line scan against base excludes existing docs/specs convention text from new-spec/work-loop/eval (AC-0031).
- Work-loop driver names supervisor, fallback and rules section (AC-0032).

**Done when:** the T6 tests pass.

### T7: The how-to and its repository-level check

**Satisfies:** AC-0033, AC-0034, AC-0035, AC-0036

**Depends on:** T6, T9

**Touches:** `guides/core/how-to/` (the new how-to), `tools/test_spec_supervisor_howto.py`, `tools/repo/build_gate_chain.py`, `tools/test_build_gate_chain.py`, the guide index the guide lints read

**Tests:**

Mode: goal-based repository suite, never a pack test reading guides.

- Pin optional/later ferryman, install prerequisites, human hand-off/answer steps and routing (AC-0033–AC-0035).
- Run all three guide lints (AC-0036); register suite in build_gate_chain.py and test_build_gate_chain.py.

**Done when:** the T7 tests pass, and the new `tools/` suite is registered as a step in `tools/repo/build_gate_chain.py` and listed in `tools/test_build_gate_chain.py`, so a CI job runs it.

### T8: Release records, projections, eval and closeout evidence

**Satisfies:** AC-0037, AC-0038, AC-0039, AC-0045

**Depends on:** T7

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `packs/core/.apm/skills/new-spec/evals/`, `.claude/skills/new-spec/`, `.agents/skills/new-spec/`, `.claude/skills/work-loop/`, `.agents/skills/work-loop/`

**Tests:**

Mode: goal-based closeout.

- Versions match one patch above origin/main; changelog validates (AC-0037, AC-0045). Build-self produces no projection diff (AC-0038); eval exercises shipped supervisor instructions, such as never running answer and waiting at no-human-answer (AC-0039).
- Record targeted new-spec pack tests, `make precheck PRECHECK_ARGS="--with-tests --base origin/main"`, one test-corpus.yml dispatch and origin/main diff proving no work-loop pin-set/projection edits (core AC-0019).

**Done when:** the T8 tests pass and the closeout runs are recorded in the verification ledger.

### T9: The live trials

**Satisfies:** AC-0041, AC-0042

**Depends on:** T4

**Touches:** `docs/specs/spec-supervisor-gates/notes/verification-ledger.md`

**Tests:**

Mode: manual QA after T4, before T7.

- Record three different-CLI tries resuming a real parked gate across an answer from status alone, preserving request id/records; fewer than two fail, with any single failure's cause recorded (AC-0041).
- Record a real spec from Draft through both parks, real-terminal answers and delegated start to terminal/admitted (AC-0042).

**Done when:** the AC-0041 pass rule is met across three recorded tries, any single failure’s cause recorded, and the AC-0042 live run is recorded.

### T10: Page 05 update

**Satisfies:** none — Durable Outputs architecture alignment

**Depends on:** T8, T9

**Touches:** `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md`

**Tests:**

Mode: goal-based page-05 read after core's page update.

1. Sections 2/4: ferryman-run is the controller role; exact Python command; park returns parked/current; start needs a new admission record after issuance.
2. Section 3: park/consent/answer/human approval commit/report sequence; approval/revert waits; handoff.json binding.
3. Answer schema includes run/request, both digests, parked commit and bound values; human-decision lacks gate/digests/park; retry binds four values; separate real terminal and decision-bound prompt.
4. Rejection: manual Draft/Drafting reverts; request-changes extends D4; retry/revise/abandon and allowances; first valid answer wins; unreviewed cap rejects approve and permits one review round.
5. Instructions: AC-0028 prohibitions and AC-0029 codes.
6. Work-supervisor pending status uses park commit; approval alone does not stale it; plan park needs Approved/Drafting; consent report closes edit window.
7. Section 8: new admission record proves matching content, not real execution; forgery remains accepted risk.

**Done when:** the page read finds no contradiction with this spec.

## Rollout

Delivery is one change set with no flag, after the core release of `spec:spec-supervisor-core`. Rollback is removing the added files and the driver line, since nothing calls the supervisor until `work-loop` is told to drive it, and that line lands in the same release.

A core pack release carries it to adopters. `work-supervisor.py` is unchanged and its pin is unaffected. No infrastructure or external system is involved.

## Risks

The spec owns accepted risks. T1/T2 check unreviewed and first-answer rules; T4 checks real admission layout and freshness; T7 registers guide checks in CI; T8 runs core digest equivalence and release checks.

## Changelog
