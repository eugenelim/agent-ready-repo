# Plan: Spec supervisor gates and hand-off

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md`, `05b-approval-integrity-and-trusted-configuration.md` and `14-installation-and-adoption-experience.md` (gates, session approval, instruction rules, how-to); `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `_supervisor_gates.py` and `_supervisor_admission.py` (the real `park`, `gates` and `start`, read and not edited) with their tests under `packs/core/tests/skills/work-loop/`; `packs/core/.apm/skills/work-loop/references/supervisor.md` (Parked gates). Read in a scratch repository: the parked digests are in `gates[].spec_digest` and `gates[].plan_digest`, no read-only field shows an admitted pair, and the committed `delivery/approvals.jsonl` does (see Design). Named uncertainty: the helper module name for `answer` is `implementation-discovered`.

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

Add the human gate and hand-off layer to `spec-supervisor.py` after `spec:spec-supervisor-core` supplies admission, requests, resume, the ledger, protected-content checks, the digest copy and the `consent` requests. The order is the human `answer` verb and its digest binding first, then the answer records and the `report` rules that read them with the decision mapping, then the hand-off record and delegated `park`, then delegated `start` with terminal confirmation and the end-to-end test, then the instruction text and driver line, then the how-to, then release records and the live trials. The riskiest part is binding an answer to the exact bytes the human read, so digest binding is built before any request logic reads an answer.

## Constraints

- ADR-0162 D1 to D7: the six commands, `delegate-verb`, a gate or committed status at every phase boundary, and no approval by a sibling.
- ADR-0163 D3: no file under `work-loop/scripts/` and no policy JSON in its pin set changes; the driver line edits `work-loop/SKILL.md`, which the work supervisor does not hash (`work-supervisor.py` hashes `scripts/` and its policy files).
- ADR-0157 D2 to D6: `park` computes digests itself and commits nothing, `gates` lists `pending`, `stale` or `invalid`, only `approve` from the named human advances a gate, and `start` refuses digests that differ from the current ones.
- ADR-0144: `work-supervisor.py` and its pin set are not edited.
- `packs/AGENTS.md`: shipped pack content carries no internal citation, a pack update bumps `pack.toml` and `plugin.json` together, a non-cosmetic update updates the pack's eval harness, and a pack test reads only its own pack (`tools/lint-pack-test-boundary.py`).
- `spec:spec-supervisor-core` owns admission, requests, resume at a waiting gate, the ledger, the protected set and its allowed edits, the digest copy, review rounds, the cap, pins, `park`, `gates` and the `consent` requests for `spec-approved`, `plan-approved`, `review-cap` and `review-weak`; this plan cites them by name and copies none. Its resume rule at a waiting gate (an open `consent` returns unchanged until parked, then `next` refuses `parked`) is tested here only through the answer path.

## Construction tests

**Integration tests:** one end-to-end pack test in a temporary repository runs the real installed `work-supervisor park` for both gates and `start`, with human-written approval commits between them (AC-0026). The `answer` tests run through a pseudo-terminal.
**Manual verification:** the live trials of AC-0027 and AC-0028.
**Repository-level check:** a suite under `tools/` reads the how-to, because a pack test may not read another source tree and guides sit outside packs.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| How-to for a session | T6 | the `tools/` suite and the guide lints | the how-to matches the shipped commands |
| The `answer` verb, records and hand-off | T1 to T4 | the pack tests and the end-to-end test | every verb test is green |
| Instruction text and driver line | T5 | the content-pin tests and the pin-set diff | both files name the supervisor and `work-loop` names the fallback |
| Release history | T7 | `tools/changelog.py validate` and the self-host drift check | the changelog validates and `make build-self` is clean |
| Verification record | T7 | two ledger entries | both trials recorded |
| Current architecture | T7 | a read of page 05 against this spec | no contradiction remains |

## Design (LLD)

### Seam with core

This plan adds to what `spec:spec-supervisor-core` decides and does not restate it.

- **Manifest.** Core releases first with five kinds. This release adds `delegate-verb` (mode `ferryman-run`), `human-decision` (mode `human`) and `delegates_to` entries `{supervisor = "work-supervisor", command = "park"}` and `{supervisor = "work-supervisor", command = "start"}`, which the manifest schema requires exactly when `delegate-verb` is listed. The manifest test validates against `supervisor-manifest.v1` and compares the listed kinds with a driven run (AC-0010).
- **Digest.** Every digest here is the core digest copy over the blobs at `HEAD`, the same value the work supervisor's `park` records. `answer` computes the digest of the working-tree files, of the blobs at the parked commit and reads the parked digest, and refuses `stale-digest` unless all three are equal. For `spec-approved` and `plan-approved` it also runs `work-supervisor gates` and requires the entry for the spec directory and gate to be `pending` with equal `spec_digest` and `plan_digest`. For `review-cap` and `review-weak` no work-supervisor park exists, so the same checks read this supervisor's own `gates` entry.
- **Protected set.** This release adds two items to core's table: the answers file (an appended well-formed line, in a commit that changes only that file) and the hand-off record (a commit that changes only that file while no `delegate-verb` request is open).
- **Resume at a waiting gate.** Not restated; the gates tests kill a process at a parked consent and check that `status`, `next` and, after an answer, `report` behave as `spec:spec-supervisor-core` AC-0025 and AC-0015 state.

Traces to: AC-0002, AC-0004, AC-0010.

Owned by: T1, T4

### Interfaces & contracts

The verbs are the six of ADR-0162 D1 plus the human-run `answer`, which sits outside the manifest. `answer <spec-dir> <gate> --decision <approve|reject|request-changes> --by <name> [--note <text>]` serves the gates, and `--option <value>` takes the place of `--decision` for a `human-decision` request. Traces to: AC-0001, AC-0004, AC-0006.

- Refusal codes this spec defines: `no-tty` (no controlling terminal; run `answer` yourself in a terminal), `no-human-answer` (a consent or human-decision has no matching answer record; stop and wait for the human), `stale-digest` (digests disagree; re-park and re-review), `supervisor-changed` (raised by core's pin check; stop and report, never edit), plus `gate-not-pending`, `digest-not-confirmed`, `option-not-offered` and `hand-off-input-missing`. The instruction text lists the first four with their actions.
- The delegated `park` command is `work-supervisor park <spec-dir> --gate <gate> --intent <code|spec-plan> --code-trust <trusted|untrusted>`. The delegated `start` command is `work-supervisor start <spec-dir> --intent ... --code-trust ... --authority-ref <owner[:hex]> --review-authority-ref <plan-reviewer[:hex]> --approved-spec-digest <hex> --approved-plan-digest <hex>`, as the real script's argument parser requires.
- Source of each argument: `--gate` from the open request, the digests from the answer lines (the spec digest from the `spec-approved` line and the plan digest from the `plan-approved` line), and `--intent`, `--code-trust`, `--authority-ref` and `--review-authority-ref` from the hand-off record only. The work supervisor refuses an intent that differs from the spec's declared Terminal Intent and an authority ref that differs from its policy roles, so a wrong value surfaces as its refusal and AC-0015's `human-decision`.
- The result of a delegated command is `{"request_id", "facts": {"command", "exit", "output"}}` with the work supervisor's JSON as `output`, bounded as core bounds a result.

Owned by: T1, T3, T4

### Data & schema

The answers file `answers.jsonl` is append-only, one JSON line per answer: `gate`, `decision`, `digest` (the spec and plan gate digests), `by`, `at`, `identity` (the value `unverified`), and for a human-decision the `option`, and for `request-changes` an optional `note`. `answer` writes the line and commits the file alone, so the author, time and parent of the commit make a forged line visible in history. The hand-off record `handoff.json` is human-owned and holds `intent`, `code_trust`, `authority_ref` and `review_authority_ref` in the argument form `work-supervisor` takes. It is on the instruction text's never-write list. Traces to: AC-0004, AC-0011, AC-0012, AC-0013.

Owned by: T1, T3

### State & control flow

State stays derived from the repository, as core defines. This plan adds the transitions that read an answer line. Traces to: AC-0005 to AC-0016.

- **Plain-session sequence.** For each approval gate: `next` issues the delegated `park`, the real `park` records the gate and commits nothing, `next` issues the `consent`, the session agent calls this supervisor's `park` on it, the human runs `answer`, the human writes `Status: Approved` and the dated plan Changelog line and commits, and the agent runs `next` and `report`. The real `park` of `plan-approved` refuses unless the spec is `Approved` and the plan `Drafting`, so the human's spec commit precedes it. After the plan answer the human writes the plan approval and commits, and `next` re-checks digests and issues `start`.
- **Decision table for AC-0009.**

| Gate | `approve` | `request-changes` | `reject` |
| --- | --- | --- | --- |
| `spec-approved` | delegated `park` of `plan-approved` | `revise` with the note untrusted | `human-decision`: `revise`, `abandon` |
| `plan-approved` | delegated `start` | `revise` with the note untrusted | `human-decision`: `revise`, `abandon` |

  For `request-changes` and `reject` the human reverts the pair to `Draft` and `Drafting` by hand and commits, which core's approval-edit exception accepts. A `human-decision` answered `revise` leads to a `revise` request, and answered `abandon` ends the run.
- **`review-cap` and `review-weak`.** The mapping of AC-0008 is core's round counter: `approve` accepts the residue, `request-changes` allows exactly one further round, `reject` stops the run.
- **Terminal confirmation.** After a delegated `start` result carries `admitted`, `current` or `terminal` (the last for a `spec-plan` intent, which a probe showed ends terminal at once), the supervisor reads the work supervisor's state and compares it with the approved digests. The real output carries no admitted digest pair in `status <spec-dir> --json` or in `gates`: `status` shows `run.run_id`, `run.active`, `run.stage`, `terminal` and `verification` only, and `gates` omits a gate once `start` has admitted it (`{"gates": []}`). The parked digests are in `gates[].spec_digest` and `gates[].plan_digest` with `gates[].state`. The confirmation therefore reads the committed admission record instead: the last line of `<spec-dir>/delivery/approvals.jsonl` at `HEAD`, whose `base` is the commit the pair was read from, `run_id` names the run, and `approval.spec_policy_fingerprint` equals the spec gate digest. It requires all of these: `run_id` equals `status --json` `run.run_id`; the gate digests of `spec.md` and `plan.md` at `base`, by the core copy, equal the approved spec and plan digests; `approval.spec_policy_fingerprint` equals the approved spec digest; and `gates` lists no entry for the spec directory. It does not use `initial_plan_review.plan_hash`, because a probe showed it differs from the plan gate digest. Equality ends the subject (`terminal`, reason `admitted`), and anything else leaves it non-terminal.
- **Refused `park` or `start`.** The delegate result carries the refusal code, and `next` issues a `human-decision` naming the code and offering `revise` and `abandon`. The approval commits stay in history, and the human reverts the pair as for `request-changes`.

Owned by: T2, T3, T4

### Failure, edge cases & resilience

Every `answer` refusal writes nothing and commits nothing. A kill between the answers-file write and its commit leaves a dirty tree that core's admission rules refuse, and the human re-runs `answer`. A kill at a waiting gate leaves the consent request open, so a fresh process re-takes it. A history rewrite between steps is not detected (an accepted risk in the spec). Traces to: AC-0001, AC-0005, AC-0016.

Owned by: T1, T2, T4

### Behavior & rules

The shipped instruction text lives in the `new-spec` skill and carries the session rules, the four defined refusal codes and one compact table of request kinds with their result-fact shapes, generated from or checked against the manifest. The work-loop driver line is one added sentence in the spec-plan instructions. Traces to: AC-0017 to AC-0022.

Owned by: T5

## Tasks

### T1: The answer verb and digest binding

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/scripts/` (the `answer` code, in a new helper module whose name is `implementation-discovered`), `packs/core/tests/skills/new-spec/test_spec_supervisor_answer.py`

**Tests:**
- Mode: TDD over a temporary repository with a parked gate made by the real `work-supervisor park`, driving `answer` through a pseudo-terminal so the terminal rule is exercised for real. One refusal case per member of the AC-0001 set: no terminal, a gate absent from `gates`, a gate listed `stale`, each of the three digests differing in turn, a mistyped digest, and a decision or option not offered (AC-0001).
- A report or an `answer` argument that supplies a wrong digest is ignored, and the recorded digest equals the listing's (AC-0002). The exact prompt bytes, and no report text in them (AC-0003). The line fields and the single-file commit, which `next` and `report` accept (AC-0004).

**Done when:** the T1 tests pass.

### T2: Report consent rules, status and decisions

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/new-spec/scripts/`, `packs/core/tests/skills/new-spec/test_spec_supervisor_consent.py`

**Tests:**
- Mode: TDD with real commits. `report` advances on a matching line and refuses `no-human-answer` for no line, a line naming another gate, a digest other than the current park's and a time before the park, whatever decision the result states (AC-0005). A killed process followed by `status`, `next` and `report` after an answer behaves as the core resume rule states.
- A `human-decision` result with no line, with an option not offered, and with `revise` and `abandon` on a matching line (AC-0006). `status` shows each answer and decision (AC-0007).
- The three decisions on `review-cap` and `review-weak`, including no second round before a further answer (AC-0008), and each cell of the decision table, the untrusted note and `abandon` (AC-0009).

**Done when:** the T2 tests pass.

### T3: Hand-off record and delegated park

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/new-spec/scripts/`, `packs/core/.apm/skills/new-spec/supervisor.toml`, `packs/core/tests/skills/new-spec/test_spec_supervisor_park.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_manifest.py`

**Tests:**
- Mode: goal-based. The manifest validates, lists `delegate-verb`, `human-decision` and the two `delegates_to` entries, and equals a driven run's kinds (AC-0010).
- Mode: TDD against the real installed `work-supervisor park` and `gates` in a temporary repository. The `park` command for each gate, with the record's values (AC-0011); the hand-off record absent, malformed, missing each key in turn, holding an out-of-form value, and edited between `next` and `report`, none supplied by a default or a report (AC-0013); a human approval commit accepted, and no supervisor commit touching `Status:` or an approval entry (AC-0014); the real `park` refusals `gate-uncommitted` and `gate-status-mismatch` routed to the `human-decision` (AC-0015).

**Done when:** the T3 tests pass.

### T4: Delegated start, digest re-check and terminal confirmation

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/new-spec/scripts/`, `packs/core/tests/skills/new-spec/test_spec_supervisor_start.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_end_to_end.py`

**Tests:**
- Mode: TDD against the real installed `work-supervisor start`, which makes its own commit, accepted by the next verb. The command carries both digests and the four record values (AC-0012); an edit between answer and `start` refuses `stale-digest` with no `start` request (AC-0012); a real `start` refusal routes to the human-decision (AC-0015).
- A reported `admitted` with a record that names other digests, another run id or a gate still listed is refused, and a real admission, for a `code` and a `spec-plan` intent, ends the subject (AC-0016).
- Mode: end-to-end over a temporary repository with no stub: both real `park` calls, human-written approval commits, and the real `start` (AC-0026).

**Done when:** the T4 tests pass.

### T5: Instruction text and the work-loop driver line

**Depends on:** T4

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`, `packs/core/.apm/skills/work-loop/SKILL.md`, `.claude/skills/work-loop/`, `.agents/skills/work-loop/`, `packs/core/tests/skills/new-spec/test_spec_supervisor_instructions.py`

**Tests:**
- Mode: goal-based content pins over the shipped skill text, scoped to the section that carries the rules so a second copy elsewhere cannot satisfy them: the prohibitions (AC-0017), the positive rules and the four defined codes (AC-0018), the table compared with the manifest's kinds (AC-0019), and a citation scan over the files this spec changes under `packs/` (AC-0020). The driver line is pinned in `work-loop/SKILL.md` (AC-0021).
- Mode: goal-based `git diff --exit-code <base> --` over `packs/core/.apm/skills/work-loop/scripts/`, `supervisor-policy.json` and `review-rules.json`, with the test loading the real work supervisor's digest listing to show `SKILL.md` is outside it (AC-0022).

**Done when:** the T5 tests pass.

### T6: The how-to and its repository-level check

**Depends on:** T5

**Touches:** `guides/core/how-to/` (the new how-to), `tools/test_spec_supervisor_howto.py`, the guide index the guide lints read

**Tests:**
- Mode: goal-based. The `tools/` suite reads the how-to and pins the `ferryman` statement, the prerequisites and the routing (AC-0023). The three guide lints run over the tree (AC-0024). No pack test reads `guides/`, because `tools/lint-pack-test-boundary.py` forbids it.

**Done when:** the T6 tests pass, and the new `tools/` suite is registered wherever a new `tools/` suite must be.

### T7: Release records, projections, eval, page 05 and the live trials

**Depends on:** T6

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `packs/core/.apm/skills/new-spec/evals/`, `.claude/skills/new-spec/`, `.agents/skills/new-spec/`, `.claude/skills/work-loop/`, `.agents/skills/work-loop/`, `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md`, `docs/specs/spec-supervisor-gates/notes/verification-ledger.md`

**Tests:**
- Mode: goal-based. Both version files match and sit one patch above `origin/main`, the changelog validates, `make build-self` leaves no diff, and the eval file holds the supervisor case (AC-0025).
- Mode: manual QA, recorded in the ledger. Three tries on different CLIs resume a real run from `status` alone (AC-0027), and one real spec goes from Draft to plan-approved through the real `park` (AC-0028).
- Closeout evidence: a targeted run of the pack tests under `packs/core/tests/skills/new-spec/`, `make precheck PRECHECK_ARGS="--with-tests --base origin/main"`, and one `gh workflow run test-corpus.yml --ref "$B"` dispatch, because pack tests run in no PR check. Page 05 is edited where it departs from this spec and `spec:spec-supervisor-core`.

**Done when:** the T7 tests pass and both ledger entries exist.

## Rollout

Delivery is one change set with no flag, after the core release of `spec:spec-supervisor-core`. Rollback is removing the added files and the driver line, since nothing calls the supervisor until `work-loop` is told to drive it, and that line lands in the same release. A core pack release carries it to adopters. `work-supervisor.py` is unchanged and its pin is unaffected. No infrastructure or external system is involved.

## Risks

- A session agent can answer through a pseudo-terminal or write a well-formed answer line or hand-off record, because the terminal check does not separate a human from an agent. Mitigation: the instruction text, the committed files that show a forged line in history, and the live trial; the spec records this as an accepted risk.
- The confirmation reads the work supervisor's admission record, whose layout is not a published contract. Mitigation: T4 drives the real `start` for both intents, and a layout change fails that test before release.
- The core digest copy may drift from the work supervisor's. Mitigation: core's equivalence test on a recorded corpus.
- A new `tools/` suite and a pack version bump each need CI registrations. Mitigation: T6 and T7 carry them in Done when and in the closeout dispatch.

## Changelog
