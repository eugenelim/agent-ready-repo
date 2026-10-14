# Plan: Execution supervisor core

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** [ADR-0144](../../adr/0144-work-loop-supervisor-owns-procedure.md)
  governs.
  - **Design:** [`work-loop-execution-supervisor.md`](../../architecture/work-loop-execution-supervisor.md),
    amended by ADR-0144 D2, D7, D10, and D11.
  - **Production analogues:** the path-loaded sibling pattern in
    `work-loop/scripts/loop-engine.py`, and the Slice 1/2 services
    `_acceptance.py`, `_policy_import.py`, `_evidence_store.py`, and
    `_review_disposition.py`. `import_policy` needs a grant, an issuer, an audit
    sink, and both identities.
  - **Tests:** `packs/core/tests/skills/work-loop/` and `tests/roster/`.
  - **Spike:** a throwaway prototype of this protocol, about 570 lines, ran the
    crash corpus on 2026-10-12. Of 66 kill and journal-deletion variants, 63
    matched the uninterrupted run byte for byte. The other 3 differed only by an
    effect dispatch line, and none needed a human decision. The prototype is not
    committed. Its protocol is recorded in Design below.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`. After approval, execution
> observations belong in
> `docs/specs/execution-supervisor-core/notes/verification-ledger.md`.

## Approach

1. Build the pure parts first: contracts (T1), references and projection (T2),
   and admission (T3).
2. The step loop (T4) carries the commit builder, derivation, recovery, events,
   and `run.json`.
3. The TDD guard (T5), readiness and counts (T6), and effects (T7) run inside
   the step loop.
4. The dark-launch checks (T8) close the work.

Every task that changes `.apm/` bumps the Core patch version and adds a
changelog line. T2 moves the plan parser out of `loop-cohort.py` behind
unchanged entry points. Everything else adds code that nothing calls yet.

## Constraints

- ADR-0144 D1–D11 govern. D2: standard library and `work-loop/scripts/` only.
  D11: the controller is trusted, and owns the rule that one worker writes to
  the execution root at a time.
- ADR-0061 D7: the retry cap fires when the count reaches the cap. ADR-0061 D5
  and ADR-0005 keep execution sequential.
- RFC-0028: stubs stay in the task's `Tests:` subsection.
- Slice 1 and Slice 2 contracts are reused unchanged. The task grammar is
  `### Tn:`, `**Depends on:**`, `**Touches:**`, the new optional `**Effects:**`,
  and stub fences.
- `packs/AGENTS.md`: every `.apm/` change bumps the Core version.

## Construction tests

**Integration tests:**

- **VI-4901 (AC-0015, AC-0016, AC-0017, AC-0018, AC-0026, AC-0032):** the crash corpus,
  ported from the spike to the real modules.
  - **Kill points:** the spec's Kill points definition.
  - **Each kill point runs twice:** once killed and restarted, and once with the
    journal deleted.
  - **Extra scenarios:** journal deleted during a live lease, a supervisor
    commit during a lease, `next` during a lease with residue, and a rebase.
  - **Pinned clock:** yes.
- **VI-4902 (AC-0019):** the effect corpus, including the unknowable rows,
  `resolve-effect`, a double crash around the intent commit, a later task's
  commit after a receipt, and a rebase after a push. These are the cases the
  spike did not model.

**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility | T1, T4 | VI-4001, VI-4002, VI-4034 | Five schemas registered; `run.json` fields stated |
| Maintainer procedure — stub fence and `**Effects:**` | T5, T7 | Link check; new-spec evals | Both grammars stated |
| Release history | every `.apm/` task | Version parity | One changelog line per release |
| Design facts below | `execution-supervisor-cutover` | Supervisor reference and `loop-infrastructure.md` | Owned by the cutover's architecture row |

## Design (LLD)

### Design decisions

Each identity is derived from committed facts reachable from `HEAD`. None is
ever read from the journal.

- **Run id.** It comes from the first line of `approvals.jsonl`. A re-approval
  appends a line that carries the same run id.
- **Attempt id.** The implementation attempt id is
  `impl:<task>:<revision>:<n>`, where `n` is one plus the count of `gate-fail`
  evidence lines for that task and revision. The stub attempt id is
  `stub:<task>:<stub digest>`. Because ids are deterministic, `next` re-issues
  the current attempt instead of starting a second one.
- **Commit trailers.** Every supervisor commit carries `Supervisor-Run`,
  `Supervisor-Step: <deterministic step id>`, and `Supervisor-Operation`, whose
  value is exactly one of the spec's step kinds. Implement and stub commits also carry
  `Supervisor-Task` and `Supervisor-Task-Revision`.

  Completion is an `implement` commit for the current revision. Red is a `stub`
  or `red` commit for the stub digest. The retry count is the number of
  run-wide `gate-fail` lines.
- **Commit builder.** Each commit follows the same four steps:
  1. Build the commit in a private index, from `HEAD` plus the admitted
     change-set paths plus appended `delivery/` lines.
  2. Skip the whole step if its step id is already reachable.
  3. Advance `HEAD` with `git update-ref HEAD <new> <old>`.
  4. Only then write the `delivery/` working copies, refresh the real index for
     the committed paths from the private index, and append the event.

  The working tree's `delivery/` files are never read as input. At entry, a
  file that is a strict prefix of its `HEAD` version is lagging; it is
  rewritten from `HEAD`, and the real index is refreshed from `HEAD` for every
  path the last supervisor commit touched. Any other difference is a foreign
  edit.
- **Change set.** The change set is what `git add -A` would stage against the
  current `HEAD`. It excludes ignored files, and it always excludes
  `<spec>/.supervisor/`, `.loop-run/`, and `<spec>/delivery/`.
- **Events.** Events are a projection of supervisor commits. Each `next` appends
  a line for any reachable step id that has none. This gives one line per step,
  and it survives a rebase.
- **Effect key.** The key follows the spec's Effect key definition: run and a
  plan-unique effect name for task effects; run, effect name, and the terminal
  `HEAD` for `finish` effects. Replans, commits, and rebases never
  reopen a task effect.
  - **Dispatch lines:** each dispatch records a `dispatch k` line, and
    `Absent` re-dispatches up to three.
  - **Unknowable results:** these use `effect-resolution.v1` decisions.
- **Stub fence.** The info string is
  `stub path=<repo-relative> run="<command>" red-exit=<codes>`, where `{path}`
  expands and `red-exit` defaults to `1`. A collection or setup error exits
  with another code and is not red.
- **Red proof.** It belongs to `(task, stub digest)`. When the stub bytes are
  already in `HEAD` and their test fails on a scratch copy of `HEAD`, the
  supervisor writes a `red` commit itself. A `no stub` TDD task needs no red
  proof.
- **Admission.** `start` creates an in-process Slice 1 `CapabilityIssuer` and a
  writer grant scoped to `delivery/`. Its audit sink appends to
  `<spec>/.supervisor/security-events.jsonl`, a local log, so audit writes
  never change `delivery/`.
- **Envelope references.** References are built per section with
  `_loop_guards.canonical_contract`. Each value is
  `<name>:sha256(<name> + heading + content)`.
- **Rejected alternatives:**
  - Measuring the change set against `HEAD` at dispatch is rejected, because supervisor commits during a lease pollute it.
  - Lease expiry is rejected, because it stalls after a kill and allows a second attempt.
  - Journal-based record recovery is rejected, because the private-index commit removes the window it covered.
  - A tree-based effect key is rejected, because it reopens on unrelated commits and rebases.

Owned by: T2, T3, T4, T5, T6, T7.

### Interfaces & contracts

Commands, all as `python '<skill-dir>/scripts/work-supervisor.py' <verb> <spec-dir> …`:

| Verb | Effect |
| --- | --- |
| `start --intent code\|spec-plan --code-trust trusted\|untrusted --authority-ref <owner ref> --review-authority-ref <plan-reviewer ref>` | Commit the approval pair. Under `spec-plan`, a second commit carries the terminal step. |
| `next` | Derive, sync lagging `delivery/` files, reconcile events, and print the current request, a refusal, or terminal. |
| `report <result.json>` | Re-derive, refuse unless the result is for the current attempt, check, then commit. |
| `status [--json] [--check]` | Show the stage, readiness, projection, decisions, and count. `--check` exits 3 at the cap, 1 on refusal, and 2 on a usage error, with 3 taking precedence. |
| `resolve-effect --operation <key> --decision <d> --authority-ref <effect-authority ref>` | Commit one `effect-resolution.v1`. |

The test seam is `main(argv)`, run in-process.

Owned by: T1, T3, T4, T7.

### Data & schema

| Fact | Location | Durability |
| --- | --- | --- |
| Approval pairs, run id, code trust, authority references | `<spec>/delivery/approvals.jsonl` | Committed |
| Evidence, `gate-fail`, red receipts | `<spec>/delivery/evidence.jsonl` via `EvidenceStore` | Committed |
| Effect intents, dispatch lines, receipts, resolutions, claims | `<spec>/delivery/effect-resolutions.jsonl` | Committed |
| Review selection records (written by `execution-supervisor-review-gate`) | `<spec>/delivery/review-selections.jsonl` | Committed |
| Audit events | `<spec>/.supervisor/security-events.jsonl` | Local |
| Completion, red, replans, steps | Supervisor commit trailers | Git history |
| Advisory journal; `run.json`; locks | `<spec>/.supervisor/` | Local, deletable |
| Run events | `.loop-run/events.jsonl` | Local, append-only |
| Implementation retry cap (5) and authority roles, mirroring the spec's stated values | `work-loop/supervisor-policy.json` | Skill data |

Owned by: T3, T4, T7.

### State & control flow

`next` runs these steps in order:

1. Derive, with no writes: the approval check, then the envelope check. Refuse
   on failure, writing only `run.json`.
2. Sync lagging `delivery/` files, and reconcile events.
3. Commit pending controller edits to `spec.md`, `plan.md`, or cited records as
   one `replan` step.
4. Derive the current request, in this order:
   1. the cap;
   2. the first incomplete task — its red commit, `write-stub`, or
      `implement-task`;
   3. the open effects of completed tasks;
   4. gates, review, or repair;
   5. terminal.
5. Write `run.json`, and append an advisory journal line.

`report` runs these steps in order:

1. Re-derive, and refuse unless the result is for the current attempt.
2. Refuse on a foreign `delivery/` edit, or on a change set that touches the
   spec directory or any cited record.
3. Apply the stub, `no stub`, and gate rules.
4. Commit through the builder.

A refused `report` writes nothing. A `human-decision` comes only from `next`.

Owned by: T4.

### Failure, edge cases & resilience

- **Crash at any kill point:** the step-id skip, the `HEAD` compare-and-swap,
  and lag sync converge, as the spike showed.
- **Two concurrent controllers:** `HEAD`'s compare-and-swap and step ids prevent
  duplicate commits. The rule that one worker writes to the execution root at a
  time belongs to the controller (D11).

Owned by: T4.

## Tasks

### T1: Five supervisor schemas are canonical and parity-tested

- **Depends on:** none
- **Spec behavior:** Interface compatibility; TDD.
- **Touches:** `contracts/delivery/*.v1.schema.json`, `contracts/REGISTRY.md`, `tests/roster/`
- **Verification mode:** TDD
- **Tests:**
  - **VI-4001:** `tests/roster/test_delivery_contract_bundle.py` admits the five
    schemas, and its no-copy rule holds.
  - **VI-4002:** a roster parity suite checks one valid and one invalid fixture
    per schema, and one request per request kind.
- **Done when:** VI-4001 and VI-4002 pass.

### T2: Envelope references and task projection are pure and deterministic

- **Depends on:** T1
- **Spec behavior:** AC-0005, AC-0006, AC-0007, AC-0009; TDD.
- **Touches:** new `_supervisor_projector.py`; `loop-cohort.py` (parser moved out and re-imported); tests; Core manifests and changelog
- **Verification mode:** TDD
- **Tests:**
  - **VI-4010 (AC-0007, AC-0009):** each replan-corpus fixture is classified,
    with its named owner. The in-envelope fixtures raise no approval request.
  - **VI-4011 (AC-0005):** every bookkeeping edit leaves the fingerprint
    byte-identical.
  - **VI-4012 (AC-0006):** a template-shaped spec passes `import_policy` with
    six distinct values.
  - **VI-4013:** renumbering, reordering, and editing `Approach:` leave the
    revision unchanged. Editing `Tests:` changes it. Every plan under
    `docs/specs/` projects.
- **Done when:** VI-4010 through VI-4013 pass, and the `loop-cohort` suites still pass.

### T3: Start commits the approval pair atomically

- **Depends on:** T2
- **Spec behavior:** AC-0001, AC-0002, AC-0003, AC-0004, AC-0012, AC-0021; TDD.
- **Touches:** new `work-supervisor.py`, new `_supervisor_admission.py`, new `work-loop/supervisor-policy.json`; Core manifests and changelog
- **Verification mode:** TDD
- **Tests:**
  - **VI-4020 (AC-0001, AC-0002):** a clean start makes one commit. A fault at
    each kill point inside `start` leaves no readable partial line, and a
    rerun completes.
  - **VI-4021 (AC-0003, AC-0004):** checks the status and intent table, and the
    role-to-flag bindings. `owner:0123456789ab` is accepted. `jdoe`, an
    email-shaped value, and `plan-reviewer` given as `--authority-ref` are
    refused.
  - **VI-4022 (AC-0012):** a `spec-plan` run gives zero requests, zero
    projections, and one commit touching only `delivery/`.
  - **VI-4023 (AC-0021):** with legacy state files present, a read audit shows
    neither opened.
- **Done when:** VI-4020 through VI-4023 pass.

### T4: The step loop derives, commits, and recovers

- **Depends on:** T3
- **Spec behavior:** AC-0008, AC-0010, AC-0011, AC-0015, AC-0016, AC-0017, AC-0018, AC-0026, AC-0030, AC-0031, AC-0032; TDD plus goal-based.
- **Touches:** `work-supervisor.py`, new `_supervisor_commit.py`, new `_supervisor_loop.py`, new `_supervisor_journal.py`; Core manifests and changelog
- **Verification mode:** TDD for rules; goal-based for VI-4901.
- **Tests:**
  - **VI-4030 (AC-0008):** each refusal row, as an uncommitted edit and as a
    committed one, leaves `HEAD`, refs, tracked files, the journal, and events
    unchanged. `run.json`'s `refusal` names the code and owner.
  - **VI-4031 (AC-0010, AC-0011):** renumbering and a `Depends on:` rewrite
    re-request nothing. A content edit, a split, and a merge re-request the
    task, and the old commits stay.
  - **VI-4035 (AC-0030, AC-0031):** a protected edit, amendment, and second
    `start` keep the run id, completion, receipts, and count. A worker edit to a
    cited ADR's `## Decision` is refused at `report` with no commit.
  - **VI-4034 (AC-0026):** at each step, `run.json` holds the defined fields,
    and `gate_pending` tracks the open `human-decision`.
  - **VI-4036 (AC-0032):** after each supervisor commit and sync in a fixture
    run, `git diff --cached` is empty.
  - **VI-4901 (AC-0015, AC-0016, AC-0017, AC-0018, AC-0026, AC-0032)**, cross-cutting.
- **Done when:** VI-4030, VI-4031, VI-4034, VI-4035, VI-4036, and VI-4901 pass.

### T5: The TDD guard admits only red-proven stubs

- **Depends on:** T4
- **Spec behavior:** AC-0013, AC-0014; TDD.
- **Touches:** new `_supervisor_tdd.py`; `_supervisor_loop.py`; `references/tdd-stubs.md`; Core manifests and changelog
- **Verification mode:** TDD
- **Tests:**
  - **VI-4040 (AC-0013, AC-0014):** each TDD-corpus case runs:
    - a one-stub task;
    - a two-stub task;
    - a `no stub` task, admitted with no red proof;
    - a task revised after its stub commit, which gets a supervisor `red`
      commit;
    - a revised completed TDD task, which gets `stub-not-red` and then a
      `no stub` replan;
    - a production edit before red, which is refused.
- **Done when:** VI-4040 passes, and VI-4901 includes the TDD task.

### T6: Readiness and counts derive from durable facts

- **Depends on:** T4
- **Spec behavior:** AC-0022, AC-0023, AC-0024, AC-0025, AC-0034; TDD.
- **Touches:** new `_supervisor_readiness.py`; Core manifests and changelog
- **Verification mode:** TDD
- **Tests:**
  - **VI-4045 (AC-0022, AC-0023):** one fixture per Readiness row. Deleting the
    journal and every derived index changes no answer.
  - **VI-4047 (AC-0034):** after the uninterrupted crash-corpus run,
    `_evidence_store.replay_admitted_frames` over `delivery/evidence.jsonl`
    returns every evidence frame the run admitted.
  - **VI-4046 (AC-0024, AC-0025):** the cap is checked at count minus one and at
    the count, before and after journal deletion, and after a split. Exit 1 and
    exit 2 are covered, and exit 3 wins over a refusal.
- **Done when:** VI-4045, VI-4046, and VI-4047 pass.

### T7: External effects never repeat

- **Depends on:** T4
- **Spec behavior:** AC-0019, AC-0020, AC-0033; TDD plus a two-process check.
- **Touches:** new `_supervisor_effects.py`; `_effect_broker.py` called for grant and audit; `packs/core/.apm/skills/new-spec/assets/plan.md` (`**Effects:**` grammar); Core manifests and changelog
- **Verification mode:** TDD
- **Tests:**
  - **VI-4050 (AC-0020):** a two-process race writes exactly one claim line and
    produces one dispatch.
  - **VI-4051 (AC-0033):** a plan with two `**Effects:**` lines naming `push` is
    refused at projection.
  - **VI-4902 (AC-0019)**, cross-cutting.
- **Done when:** VI-4050, VI-4051, and VI-4902 pass.

### T8: The core stays dark and leaves the engine untouched

- **Depends on:** T5, T6, T7
- **Spec behavior:** AC-0027, AC-0028, AC-0029; goal-based.
- **Touches:** tests only
- **Verification mode:** goal-based
- **Tests:**
  - **VI-4060 (AC-0027):** an `-I` run, with `sys.path` limited to `scripts/`,
    completes the uninterrupted crash-corpus run.
  - **VI-4061 (AC-0028):** a search finds no invocation outside the supervisor
    modules.
  - **VI-4062 (AC-0029):** the work-loop suites at the recorded merge-base pass.
- **Done when:** VI-4060 through VI-4062 pass.

## Rollout

- **Delivery:** each task ships in a Core 3.x patch release. Nothing
  adopter-visible changes until `execution-supervisor-cutover`.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** task order.

## Risks

- **Revision scope:** a pinned-field edit re-runs a completed task.
  Mitigation: `Approach:` and other working fields are outside the revision.
- **Unmodelled spike cases:** unknowable effect rows, `resolve-effect`, and
  double crashes. Mitigation: VI-4902 covers them before T7 is done.

## Changelog

<!-- Approvals only. -->
- 2026-10-13: spec approved by owner
- 2026-10-13: plan approved by owner
