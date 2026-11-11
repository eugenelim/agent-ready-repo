# Plan: Spec supervisor gates and hand-off

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md`, `05b-approval-integrity-and-trusted-configuration.md` and `14-installation-and-adoption-experience.md` (gates, session approval, instruction rules, how-to); `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `_supervisor_gates.py`, `_supervisor_admission.py`, `_policy_import.py` and `_loop_guards.py` (the real `park`, `gates` and `start`, read and not edited) with their tests under `packs/core/tests/skills/work-loop/`; `packs/core/.apm/skills/work-loop/SKILL.md` (the runnable command form) and `references/supervisor.md` (Parked gates). Read in the code: the parked digests are in `gates[].spec_digest` and `gates[].plan_digest`, no read-only field shows an admitted pair, and the committed `delivery/approvals.jsonl` does (see Design). Named uncertainty: the helper module name for `answer` is `implementation-discovered`.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (`Agent Rules`, `Testing Strategy`, `Acceptance Criteria`, and
> the accepted risks under `Assumptions`) or its `Terminal Intent`. A change
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

Add the human gate and hand-off layer to `spec-supervisor.py` after `spec:spec-supervisor-core` supplies admission, requests, resume, the ledger, protected-content checks, the digest copy and the `consent` requests. The order is the human `answer` verb and its binding first, then the answers-file and hand-off protection with the `report` rules, wait states and decisions that read answers, then the hand-off record and delegated `park`, then delegated `start` with the terminal confirmation and the end-to-end test, then the manifest and the core amendments, then the instruction text and driver line, then the how-to, then release records and the page 05 update; the live trials run immediately after the end-to-end test. The riskiest part is binding an answer to the exact bytes and values the human saw, so the binding is built before any request logic reads an answer.

## Constraints

- eugenelim holds every owner role, including repository, contract, review and risk ownership.

- ADR-0162 D1 to D7: the six commands, `delegate-verb`, a gate or committed status at every phase boundary, and no approval by a sibling.
- ADR-0163 D3: no file under `work-loop/scripts/` and no policy JSON in its pin set changes; the driver line edits `work-loop/SKILL.md`, which the work supervisor does not hash (`work-supervisor.py` hashes `scripts/` and its policy files).
- ADR-0157 D2 to D6: `park` computes digests itself and commits nothing, `gates` lists `pending`, `stale` or `invalid`, only `approve` from the named human advances a gate, and `start` refuses digests that differ from the current ones. Conformance claim and its one extension: `request-changes` is offered at `spec-approved` and `plan-approved` beyond the `approve`, `reject` and no-answer set of D4, and it advances no gate, so D4's rule that only `approve` advances a gate holds.
- ADR-0144: `work-supervisor.py` and its pin set are not edited.
- `packs/AGENTS.md`: shipped pack content carries no internal citation, a pack update bumps `pack.toml` and `plugin.json` together, a non-cosmetic update updates the pack's eval harness, a pack test reads only its own pack (`tools/lint-pack-test-boundary.py`), and a shipped script reconfigures stdout and stderr to UTF-8 (core owns the script).
- `spec:spec-supervisor-core` owns admission, requests, resume at a waiting gate, the ledger, the protected set and its allowed edits (including the approval-edit exception for the states AC-0014 of core names), the digest copy, review rounds, the allowance read, pins, `park`, `gates` and the `consent` requests for `spec-approved`, `review-cap` and `review-weak`; this plan cites them by name and copies none. This spec owns the `plan-approved` consent request, every behavior that sits after a consent, and the allowance and round total after each human decision.

## Construction tests

**Integration tests:** one end-to-end pack test in a temporary repository runs the real installed `work-supervisor park` for both gates and `start`, with the human's `answer` runs and approval commits between them (AC-0040). The `answer` tests run through a pseudo-terminal.
**Manual verification:** the live trials of AC-0041 and AC-0042 in T9 depend on T4 and run before T7 finalises the how-to.
**Repository-level check:** a suite under `tools/` reads the how-to, because a pack test may not read another source tree and guides sit outside packs.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| How-to for a session | T7 | the `tools/` suite and the guide lints | the how-to matches the shipped commands |
| The `answer` verb, records and hand-off | T1 to T5 | the pack tests and the end-to-end test | every verb test is green |
| Instruction text and driver line | T6 | the content-pin tests and the added-line scan | both files name the supervisor and `work-loop` names the fallback |
| Release history | T8 | `tools/changelog.py validate` and the self-host drift check | the changelog validates and `make build-self` is clean |
| Verification record | T9 | two ledger entries | both trials recorded |
| Current architecture | T10 | a read of page 05 against this spec | no contradiction remains |

## Design (LLD)

### Seam with core

This plan adds to what `spec:spec-supervisor-core` decides and does not restate it.

- **Manifest.** Core releases first with five kinds. This release adds `delegate-verb` (mode `ferryman-run`, which names the controller role the session agent fills in a session), `human-decision` (mode `human`) and `delegates_to` entries `{supervisor = "work-supervisor", command = "park"}` and `{supervisor = "work-supervisor", command = "start"}`, which the manifest schema requires exactly when `delegate-verb` is listed. The manifest test validates against `supervisor-manifest.v1` and compares the listed kinds with a driven run (AC-0015).
- **Core-owned records.** Read core AC-0035 and AC-0036 for the park record, confined spec-directory field and listing. The gates release does not redefine them. `answer` reads the consent park time there and, for approval gates, reads the work supervisor's pending entry through its `gates` command (AC-0002, AC-0006).
- **Digest and reviewed identity.** Core AC-0037 owns digest equivalence and core AC-0017 owns the reviewed pair identity, last-round binding and voiding. Gate answers compare working-tree, parked-commit and parked digests (AC-0001, AC-0002), then recheck the confirmation binding (AC-0044). A cap/weak approve proceeds on that same last reviewed revision; it does not assert convergence. Answered consent uses AC-0019 before voiding; open or parked unanswered consent follows core AC-0017 and AC-0034.
- **Amendments.** AC-0027's Core amendment table is the complete list. T5 changes the named core criteria and matching tests in the gates release; this authoring pass changes neither sibling file.
- **Resume at a waiting gate.** Not restated; the gates tests kill a process at a parked consent and check that `status`, `next` and, after an answer, `report` behave as `spec:spec-supervisor-core` AC-0034, AC-0020 and AC-0021 state.

Traces to: AC-0002, AC-0006, AC-0015, AC-0027.

Owned by: T1, T2, T5

### Interfaces & contracts

The verbs are the six of ADR-0162 D1 plus the human-run `answer`, which sits outside the manifest. `answer <spec-dir> <gate> --decision <approve|reject|request-changes> --by <name> [--note <text>]` serves the gates, and `answer <spec-dir> --option <retry|revise|abandon> --by <name>` serves a `human-decision` request with no gate or park record. The answer names the open request by reading it from the supervisor's state, and refuses when the human's chosen gate is not the open request's gate. Traces to: AC-0001, AC-0004, AC-0007.

- Refusal codes this spec defines: `no-tty` (no controlling terminal; run `answer` yourself in a separate terminal), `no-human-answer` (a consent or human-decision has no matching answer record; stop and wait for the human), `stale-digest` (binding differs; use the recovery path below), `supervisor-changed` (`answer` checks pins first under AC-0043; stop and restore the pinned installation under core AC-0039), `approval-commit-pending` (the human has answered approve and has not yet committed the approval; wait), `revert-pending` (the human has answered request-changes or reject and has not yet reverted the pair to Draft and Drafting; wait), `handoff-changed` (the hand-off record differs from the bound values; restore them or re-answer through the recovery gate), `hand-off-input-missing`, plus `request-not-open`, `gate-not-pending`, `digest-not-confirmed`, `option-not-offered`, `handoff-altered`, `answers-altered`, `command-mismatch`, `admission-mismatch` and `work-loop-not-found`. For committed protected-record violations, `answers-altered` and `handoff-altered` are diagnostic causes under the single outer `protected-content-changed` refusal (AC-0005). The instruction text lists the codes of AC-0029 with their actions.
- The delegated `park` command is `python '<skill-dir>/scripts/work-supervisor.py' park <spec-dir> --gate <gate> --intent <code|spec-plan> --code-trust <trusted|untrusted>`, the form `work-loop/SKILL.md` gives, because `work-supervisor` is not an executable. The delegated `start` command is `python '<skill-dir>/scripts/work-supervisor.py' start <spec-dir> --intent ... --code-trust ... --authority-ref <owner:hex> --review-authority-ref <plan-reviewer[:hex]> --approved-spec-digest <hex> --approved-plan-digest <hex>`, with authority hex of 12 to 64 lowercase digits, validated before issuance (AC-0021). `<skill-dir>` is the work-loop skill directory that sits beside the installed `new-spec` skill directory (`../work-loop` from the supervisor's skill root), the same in the `.claude/skills/` and `.agents/skills/` layouts the repository self-hosts; `answer` finds the script the same way for its `work-supervisor gates` call, and `work-loop-not-found` is refused when it is absent.
- Source of each argument: `--gate` from the open request, the digests from the answer lines (the spec digest from the `spec-approved` line and the plan digest from the `plan-approved` line), and `--intent`, `--code-trust`, `--authority-ref` and `--review-authority-ref` from the hand-off record only, checked against the values the newest binding answer line recorded. The work supervisor refuses an intent that differs from the spec's declared Terminal Intent and an authority ref that differs from its policy roles, so a wrong value surfaces as its refusal and the `human-decision` of AC-0023.
- The result of a delegated command is `{"request_id", "facts": {"command", "exit", "output"}}` with the work supervisor's JSON as `output`, bounded as core bounds a result. `report` compares `command` with the issued command word for word before it reads `output`.
- The `human-decision` request names the refusal code (bounded and marked untrusted) and the three options. Every option needs an answer line that names the request.

Owned by: T1, T3, T4

### Data & schema

The two answer-line variants are AC-0004's closed schema. A human-decision answer binds the open run/request and option, without a gate, digests, park record or `gate-not-pending` check. A `retry` line also binds the four validated hand-off values shown in the prompt. Consent answers, including cap/weak, use their own park record and the normal digest checks. `answer` writes one line and commits that file alone. The `by` field records an unverified identity; eugenelim holds every owner role.

The human-owned `handoff.json` carries the four keys and forms of AC-0021; no default or worker report supplies them. The newest binding line is the newest answer in the run carrying those values: spec approval before the plan park, plan approval before start, or retry after refusal. Traces to: AC-0004, AC-0005, AC-0018, AC-0020, AC-0021, AC-0044.

Owned by: T1, T2, T3

### State & control flow

State stays derived from the repository, as core defines. This plan adds the transitions that read an answer line. Traces to: AC-0006, AC-0007, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0016, AC-0018, AC-0019, AC-0020, AC-0023, AC-0024, AC-0025, AC-0026.

- **Plain-session sequence for each approval gate (ADR-0157 D4).** (1) `next` issues delegated `park`; the real park requires spec Draft for spec-approved, and spec Approved with plan Drafting for plan-approved. (2) The real park records the gate without committing; `report` records the delegate result. (3) `next` issues consent and the agent calls this supervisor's `park`. (4) The human runs `answer` in a separate terminal. (5) The human commits the gate's status token and dated approval entry. (6) The agent reports the consent, closing its approval-edit window with the ledger line. (7) `next` proceeds to plan park or start only after AC-0009 is satisfied. Reporting before the approval commit refuses `approval-commit-pending` without a ledger line, preserving the edit window until the human commits and the consent report succeeds.

  Answer then commit binds the reviewed values before the human records approval. It is not caused by a gate turning stale at HEAD: the work supervisor's pending check reads statuses at the recorded commit. The actual status refusal is at park: plan-approved park refuses `gate-status-mismatch` unless the spec reads Approved and the plan Drafting. An early approval is reverted through AC-0027's revert window before retry. No supervisor writes an approval or revert.
- **Decision table for AC-0013.**

| Gate | `approve` | `request-changes` | `reject` |
| --- | --- | --- | --- |
| `spec-approved` | wait (AC-0009), then delegated `park` of `plan-approved` | wait (AC-0010), then `revise` with the note untrusted | wait (AC-0010), then `human-decision`: `revise`, `abandon` |
| `plan-approved` | wait (AC-0009), then delegated `start` | wait (AC-0010), then `revise` with the note untrusted | wait (AC-0010), then `human-decision`: `revise`, `abandon` |

  For `request-changes` and `reject` the human reverts the pair to `Draft` and `Drafting` by hand and commits, which core's approval-edit exception accepts. Every `human-decision` answered `revise` first waits under AC-0010, including a refused start with an Approved/Approved pair; `abandon` ends the run and leaves the revert-direction window available. After a `revise` that a human decision caused, review runs again (new rounds against the new revision) and ends at `spec-approved` again.
- **`review-cap` and `review-weak` and the allowance (AC-0011, AC-0012).** The allowance and the round total change only here. `approve` accepts the residue and changes neither; it leads to the `spec-approved` gate, whose first request is the delegated `park`. `request-changes` issues `revise` first when a sustained finding is open (a `revise` is not a round), sets the allowance to the round total plus 1, then issues one round set, after which a round that did not converge, or was weak, issues the gate again. `reject` ends the run `rejected`. AC-0012 sets the allowance for every human-decision revision, including refused-start recovery; retry changes neither allowance nor round total.
- **Terminal confirmation (AC-0024, AC-0025, AC-0026).** After every delegated `start` result, whatever its status field says (`admitted`, `current`, `terminal`, or anything else), the supervisor reads the work supervisor's committed state and compares it with the approved digests and the issued values. The real output carries no admitted digest pair in `status <spec-dir> --json` or in `gates`: `status` shows `run.run_id`, `run.active`, `run.stage`, `terminal` and `verification` only, and `gates` omits a gate once `start` has admitted it (`{"gates": []}`). The confirmation reads the last line of `<spec-dir>/delivery/approvals.jsonl` at `HEAD`. Its `base` is the first pair's commit and later pairs copy `approvals[0]["base"]` (`_supervisor_admission.py`), so `base` is not the pair's commit. The pair that line recorded is `spec.md` and `plan.md` in the commit before the commit that added the line, because `start` digests the working bytes (`prechecked`), refuses when they change, and commits only `approvals.jsonl`. The check requires: the gate digests of that pair, by the core copy, equal the approved spec and plan digests; the line's `code_trust`, `terminal_intent`, `authority_ref` and `review_authority_ref` equal the values in the issued `start` command; and `gates` lists no entry for the spec directory. It does not compare `approval.spec_policy_fingerprint`, because that is the canonical digest of the spec with no approval-entry drop (`_policy_import.py`, `_loop_guards.py`) and differs from the gate digest for any spec carrying an approval entry, and it does not use `initial_plan_review.plan_hash` or `run_id` as proof (the work supervisor reads `run.run_id` from the first line of the same file, so that comparison is circular). For a `spec-plan` intent `start` appends the line and then commits the terminal state at once, so the same check applies. The check proves that a well-formed admission record exists for those digests and values; it does not prove that a real `start` ran, which is an accepted risk. Equality ends the subject (`terminal`, reason `admitted`). A mismatched admission record, or a claim of admission with no record, produces `admission-mismatch` and AC-0026 recovery. A real start refusal with no admission record follows AC-0023 with the actual refusal code.
- **Refused `park` or `start`.** The delegate result carries the refusal code, and `next` issues a `human-decision` naming the code and offering `retry`, `revise` and `abandon`. `retry` builds a new command from its answer line after AC-0019, AC-0020 and AC-0021; it never copies the refused command. Its prompt shows all four values and invalid input refuses `hand-off-input-missing`. The approval commits stay in history; after choosing `revise`, the human reverts the pair while `next` waits `revert-pending` (AC-0010).

- **Recovery from `next` refusals.** `handoff-changed` and `stale-digest` open a recovery human-decision visible in `status`, without issuing a delegated command. `answer <spec-dir> --option retry` binds the corrected hand-off values, or retries after the human restores the reviewed pair. A changed pair cannot pass the stale check through retry: `--option revise` waits for the human revert, applies AC-0012, then reaches review and a fresh parked approval consent. Thus every refusal has an existing answer-verb route; no new verb or implicit acceptance of stale approval is needed (AC-0019, AC-0020, AC-0023).


Owned by: T2, T3, T4

### Failure, edge cases & resilience

Every `answer` refusal writes nothing and commits nothing. A kill between the answers-file write and its commit leaves a dirty tree that core's admission rules refuse, and the human re-runs `answer`. A kill at a waiting gate leaves the consent request open, so a fresh process re-takes it. Protected-record changes follow AC-0005 and the core refusal ordering. Pinned-file recovery uses the net change since the last recorded commit (core AC-0039), so reinstalling the pinned version restores the run; it is not rejected merely because an intervening commit touched a pinned path. A history rewrite between steps is not detected (an accepted risk in the spec). Traces to: AC-0001, AC-0005, AC-0006, AC-0026.

Owned by: T1, T2, T4

### Behavior & rules

The shipped instruction text lives in the `new-spec` skill and carries the session rules, the defined refusal codes, the human's steps for `handoff.json` and `answer`, and one compact table of request kinds with their result-fact shapes, generated from or checked against the manifest. The work-loop driver line is one added sentence in the spec-plan instructions that names the supervisor, the fallback and the rules section. Traces to: AC-0028, AC-0029, AC-0030, AC-0031, AC-0032.

Owned by: T6

## Tasks

### T1: The answer verb and its binding

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/scripts/` (the `answer` code, in a new helper module whose name is `implementation-discovered`), `packs/core/tests/skills/new-spec/test_spec_supervisor_answer.py`

**Tests:**
- Mode: TDD over a temporary repository with a parked gate made by the real `work-supervisor park`, driving `answer` through a pseudo-terminal so the terminal rule is exercised for real. One refusal case per member of the AC-0001 set: no terminal, a request that is not the open one, a gate absent from `gates`, a gate listed `stale`, each of the three digests differing in turn, a mistyped digest, a decision or option not offered, and an absent, malformed and invalid `handoff.json` for each approval gate (AC-0001).
- A report or an `answer` argument that supplies a wrong digest is ignored, and the recorded digests equal the listing's (AC-0002). The exact prompt bytes, with the hand-off values and no report text in them (AC-0003). The line fields, a `by` of 65 characters refused, and the single-file commit (AC-0004).

- Pin changes combined with bad terminal, request and digest inputs return only `supervisor-changed`; a restored pinned installation succeeds (AC-0043). Mode: TDD.
- Confirmation shows and binds the decision/option; edit the working-tree digest, reviewed identity or hand-off values while the terminal prompt waits and assert no answer commit (AC-0044). Mode: TDD.
- Human-decision answers with no gate or park succeed for each offered option; no digest or pending-gate check runs. Retry rejects missing or invalid hand-off input and records the four shown values. Cap/weak answers retain their own park's digest checks (AC-0001, AC-0002, AC-0003, AC-0004).

**Done when:** the T1 tests pass.

### T2: Answers protection, report consent rules, waits and decisions

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/new-spec/scripts/`, `packs/core/tests/skills/new-spec/test_spec_supervisor_consent.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_answers_file.py`

**Tests:**
- Mode: TDD over real commits. A commit that edits, removes, reorders or appends a second line to `answers.jsonl`, an append beside another file, and a `handoff.json` change beside another file and while a `delegate-verb` request is open are each refused `protected-content-changed` with the corresponding diagnostic cause; pin changes take precedence, then ledger alterations, then these changes. A single-file append and a single-file hand-off change with no request open are accepted (AC-0005).
- Mode: TDD with real commits. `report` advances on a matching line and refuses `no-human-answer` for no line, a line naming another run or request, a line for an earlier request of the same gate, a line naming another gate, a digest other than the park's and a time before the consent park's `parked_at`, whatever decision the result states (AC-0006). A killed process followed by `status`, `next` and `report` after an answer behaves as the core resume rule states.
- A `human-decision` result with no line, with a line for an earlier request, with an option not offered, and with `revise`, `abandon` and `retry` on a matching line (AC-0007). `status` shows each answer and decision (AC-0008).
- After an `approve` answer, `next` and consent `report` refuse `approval-commit-pending` without a ledger line until the commit lands for each gate, including each gate’s corresponding approval entry and the window closing at the next ledger line, and issues the next request after it (AC-0009). After `request-changes` and `reject`, `next` refuses `revert-pending` until the revert lands; every human-decision revise, including after Approved/Approved start refusal, waits too (AC-0010).
- The three decisions on `review-cap` and `review-weak`, including the approve path to the delegated `park` of `spec-approved`, `revise` before the one further round, and no second round before a further answer (AC-0011). The allowance and round total after each decision, including a weak last round, unchanged retry allowance, and revision allowances after either approval gate and refused start (AC-0012).
- Each cell of the decision table, the untrusted note cut to 512 characters, and `abandon` (AC-0013). No commit made by a supervisor verb touches a `Status:` or approval-entry line, checked over every verb in a driven run (AC-0014).

**Done when:** the T2 tests pass.

### T3: Hand-off record and delegated park

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/new-spec/scripts/`, `packs/core/tests/skills/new-spec/test_spec_supervisor_park.py`

**Tests:**
- Mode: TDD against the real installed `work-supervisor park` and `gates` in a temporary repository. The `park` command for each gate in the runnable form, with the record's values (AC-0016); the work-loop script absent in each of the two layouts (AC-0017); the hand-off record absent, malformed, missing each key in turn, repeating a key, holding an out-of-form value, and edited between `next` and `report`, none supplied by a default or a report (AC-0021); a result whose command differs by one word, one quote or one trailing argument (AC-0022); the real `park` refusals `gate-uncommitted`, `gate-status-mismatch` and `intent-mismatch` routed to the `human-decision` with its three options, and `retry` re-issuing after the hand-off is corrected (AC-0023); a hand-off value that differs from the park record's refuses `handoff-changed` (AC-0020).

- Retry with changed hand-off values emits a newly built command equal to the values on the retry answer, not the previous command; retry prompt rejects missing input (AC-0021, AC-0023). Test authority hex lengths 11, 12, 64 and 65 and uppercase hex; the parser rejects the first invalid length before issuance (AC-0021).

**Done when:** the T3 tests pass.

### T4: Delegated start, digest re-check and terminal confirmation

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/new-spec/scripts/`, `packs/core/tests/skills/new-spec/test_spec_supervisor_start.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_end_to_end.py`

**Tests:**
- Mode: TDD against the real installed `work-supervisor start`, which makes its own commit, accepted by the next verb. The command carries both digests and the four bound values (AC-0018); an edit between answer and `start` refuses `stale-digest` with no `start` request (AC-0019); a hand-off edit after the answers refuses `handoff-changed` for the `park` of `plan-approved` and for `start` (AC-0020); a real `start` refusal routes to the human-decision (AC-0023).
- A reported `admitted`, `current` or `terminal` with a record that names other digests, other issued values, a pair read at the wrong commit or a gate still listed is refused, a hand-written approvals line is accepted by the check and recorded as the accepted risk, and a real admission for a `code` and a `spec-plan` intent, including a second pair whose `base` is the first pair's commit, ends the subject (AC-0024). The check runs on a start result that claims failure and on one that claims nothing (AC-0025). A mismatched record returns `admission-mismatch` even when the result claims failure; a false admission claim with no record also refuses. An actual refused start with no record retains its own refusal code under AC-0023 (AC-0026).
- Mode: end-to-end over a temporary repository with no stub: both real `park` calls, the human's `answer` runs through a pseudo-terminal, human-written approval commits, and the real `start`, ending `terminal` with the reason `admitted`, and a variant ending `abandoned` that fails the assertion (AC-0040).

- For `stale-digest` and `handoff-changed` returned by `next`, drive both recovery routes to a new delegated request: restore bound input and answer retry; bind changed hand-off values through retry; or answer revise, wait for reversion, then review and answer a fresh parked approval gate for a changed pair, with no old answer reused (AC-0019, AC-0020, AC-0023).
- Changed Risk triggers, Agent Rules or accepted risks after an answer refuse even when the gate digest is unchanged; changed unanswered consent and in-progress round follow core AC-0017 and AC-0034 (AC-0019).

**Done when:** the T4 tests pass.

### T5: Manifest and the amended core criteria

**Depends on:** T4

**Touches:** `docs/specs/spec-supervisor-core/spec.md`, `packs/core/.apm/skills/new-spec/supervisor.toml`, `packs/core/tests/skills/new-spec/test_spec_supervisor_manifest.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_requests.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_rounds.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_consent.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_ledger.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_protected.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_revision.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_resume.py`

**Tests:**
- Mode: goal-based. The manifest validates, lists `delegate-verb`, `human-decision` and the two `delegates_to` entries, and equals a driven run's kinds (AC-0015).
- Mode: goal-based. The core spec and matching tests cover every row of AC-0027: core AC-0004, AC-0005, AC-0010, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0029, AC-0030, AC-0031, AC-0032, AC-0034. No amendment silently relies on unchanged core wording. Core AC-0010 remains the source for review-round and adjudication outcome enums and author/revise fact sets; core AC-0025 remains the source for the complete invalid-adjudication stop set, including unreadable and unavailable adjudication.
- Mode: TDD. The per-gate token and corresponding dated entry accept normal blank-line-plus-entry edits after gate normalisation; the rest of the status line is byte-identical. Inserted/deleted status lines, the other gate's token/entry, wrapped entries and edits after a later ledger line refuse. Reverts work before park, after request-changes/reject, and after human-decision revise/abandon; cap/weak has no separate window (AC-0027).
- Mode: TDD. Delegate facts are exactly command/exit/output; human-decision and consent facts are empty, with no-human-answer enforced for both. Delegate and human-decision have no writable paths. Core replay and request-consumed use the ledger at the last recorded commit: a kill resumes only when the pending line matches the newly computed line byte for byte (AC-0027).
- Mode: TDD. Combined pin, ledger and protected-record changes return one code in core precedence order; merge history uses first parents or net changes from the last recorded commit (AC-0005, AC-0027).


**Done when:** the T5 tests pass.

### T6: Instruction text and the work-loop driver line

**Depends on:** T5

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`, `packs/core/.apm/skills/work-loop/SKILL.md`, `.claude/skills/work-loop/`, `.agents/skills/work-loop/`, `packs/core/tests/skills/new-spec/test_spec_supervisor_instructions.py`

**Tests:**
- Mode: goal-based content pins over the shipped skill text, scoped to the section that carries the rules so a second copy elsewhere cannot satisfy them: the prohibitions (AC-0028), the positive rules, the nine defined codes and the human's steps (AC-0029), and the table compared with the manifest's kinds (AC-0030).
- A scan of the lines this change adds under `packs/`, taken from the diff against the base, finds no record citation; the existing `docs/specs/<feature>/` convention text in `new-spec/SKILL.md`, `work-loop/SKILL.md` and the eval file is not counted (AC-0031).
- The driver line is pinned in `work-loop/SKILL.md`, with the pointer to the rules section (AC-0032).

**Done when:** the T6 tests pass.

### T7: The how-to and its repository-level check

**Depends on:** T6, T9

**Touches:** `guides/core/how-to/` (the new how-to), `tools/test_spec_supervisor_howto.py`, `tools/repo/build_gate_chain.py`, `tools/test_build_gate_chain.py`, the guide index the guide lints read

**Tests:**
- Mode: goal-based. The `tools/` suite reads the how-to and pins the `ferryman` statement (AC-0033), the prerequisites and the human's steps (AC-0034), and the routing (AC-0035). The three guide lints run over the tree (AC-0036). No pack test reads `guides/`, because `tools/lint-pack-test-boundary.py` forbids it.

**Done when:** the T7 tests pass, and the new `tools/` suite is registered as a step in `tools/repo/build_gate_chain.py` and listed in `tools/test_build_gate_chain.py`, so a CI job runs it.

### T8: Release records, projections, eval and closeout evidence

**Depends on:** T7

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `packs/core/.apm/skills/new-spec/evals/`, `.claude/skills/new-spec/`, `.agents/skills/new-spec/`, `.claude/skills/work-loop/`, `.agents/skills/work-loop/`

**Tests:**
- Mode: goal-based. Both version files match and sit one patch above `origin/main`, (AC-0037), and the changelog validates (AC-0045). `make build-self` leaves no diff (AC-0038). The eval file holds a case whose assertions name behavior the shipped text of T6 produces, such as refusing to run `answer` and stopping at `no-human-answer` (AC-0039).
- Closeout evidence: a targeted run of the pack tests under `packs/core/tests/skills/new-spec/`, `make precheck PRECHECK_ARGS="--with-tests --base origin/main"`, one `gh workflow run test-corpus.yml --ref "$B"` dispatch, and the diff of the change set against `origin/main` showing no work-loop pin-set path or projection, the check of core AC-0019 applied to this change set.

**Done when:** the T8 tests pass and the closeout runs are recorded in the verification ledger.

### T9: The live trials

**Depends on:** T4

**Touches:** `docs/specs/spec-supervisor-gates/notes/verification-ledger.md`

**Tests:**
- Mode: manual QA, recorded in the ledger, run as soon as the end-to-end test passes and before the how-to is final. Three tries on different CLIs resume a real run at a parked gate across a recorded answer from `status` alone, under the brief's pass rule (AC-0041), and one real spec goes from Draft through both real `park` calls, the human's `answer` runs and the delegated `start` to `terminal` with the reason `admitted` (AC-0042).

**Done when:** the AC-0041 trial passes with all three tries and any single failure’s cause recorded, and the AC-0042 live run is recorded.

### T10: Page 05 update

**Depends on:** T8, T9

**Touches:** `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md`

**Tests:**
- Mode: goal-based, a read of the page against this spec and `spec:spec-supervisor-core`. The core spec's update task lands first; this task edits only the points below and leaves the core points as they stand.
  1. Section 2, the spec request table, `delegate-verb` row, and section 4, the `delegate-verb` row: the mode `ferryman-run` names the controller role that a session agent fills in a session; the command form is `python '<skill-dir>/scripts/work-supervisor.py' ...`; `park` answers `parked` or `current` and `start` is confirmed by the admission record, not by its status field.
  2. Section 3, "Approval in a session": the plain-session sequence of this plan (delegated `park`, consent, `answer`, the human's approval commit, report, then the next delegated command), the `approval-commit-pending` and `revert-pending` waits, and the `handoff.json` record and its binding.
  3. Section 3, the `answer` paragraph: the answer line carries the run id, request id, both digests, the commit and the bound hand-off values, not `{gate, decision, digest, by, time}`; the gate answer prompt shows hand-off values and the chosen decision; a human-decision answer instead has no gate, parked commit or digests, and retry binds the four values; `answer` runs in a separate real terminal.
  4. Section 3, "Rejection" and "Rejection in a session": the human reverts to `Draft` and `Drafting` by hand and `next` waits for it; `request-changes` at the two approval gates is an extension of ADR-0157 D4's answer set; the `human-decision` offers `retry`, `revise` and `abandon`; the allowance rules of AC-0012.
  5. Section 3, "Instruction text": the five rules gain the forbids of AC-0028 and the codes of AC-0029.
  6. Section 3, the sequence diagram note: under a session the human's approval commit follows the answer, and `start` follows the plan approval commit. The pending check reads the parked commit, not HEAD; remove any claim that the approval commit itself turns the listing stale. The real plan park requires Approved/Drafting, and the approval-edit window closes at the consent report ledger line.
  7. Section 8, evidence: the terminal confirmation reads `delivery/approvals.jsonl`, and its limit (a forged record is not detected).

**Done when:** the page read finds no contradiction with this spec.

## Rollout

Delivery is one change set with no flag, after the core release of `spec:spec-supervisor-core`. Rollback is removing the added files and the driver line, since nothing calls the supervisor until `work-loop` is told to drive it, and that line lands in the same release. A core pack release carries it to adopters. `work-supervisor.py` is unchanged and its pin is unaffected. No infrastructure or external system is involved.

## Risks

- A session agent can answer through a pseudo-terminal or write a well-formed answer line, hand-off record, approval commit or admission record, because the supervisor checks lines and timing and not authorship. Mitigation: the instruction text, the committed files that show a forged line in history, the bindings of AC-0018 to AC-0022, and the live trial; the spec records each path as an accepted risk.
- The confirmation reads the work supervisor's admission record, whose layout is not a published contract. Mitigation: T4 drives the real `start` for both intents and a second pair, and a layout change fails that test before release.
- The core digest copy may drift from the work supervisor's. Mitigation: core's equivalence test on a recorded corpus, run at closeout and in the corpus suite.
- A new `tools/` suite and a pack version bump each need CI registrations. Mitigation: T7 names `tools/repo/build_gate_chain.py` and `tools/test_build_gate_chain.py` in Done when, and T8 carries the closeout dispatch.

## Changelog
