# Plan: Execution supervisor cutover

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0144 governs.
  - **Procedure:** `packs/core/.apm/skills/work-loop/SKILL.md` and `references/`.
  - **Callers:**
    - `packs/core/.apm/hooks/pre-pr.py`, which runs `loop-cohort.py check` and
      fails on any non-zero exit;
    - `tools/hooks/pre-pr.py`;
    - `packages/agentbundle/agentbundle/workspace_mcp.py`, which binds the run
      id from `engine-state.json` and marks gates on `*-HUMAN-GATE` targets.
  - **Generated copies:** produced by `make build-self`.
  - **Supervisor modules and the `run.json` field set:** these come from the
    sibling specs.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`. After approval, execution
> observations belong in
> `docs/specs/execution-supervisor-cutover/notes/verification-ledger.md`.

## Approach

T1 makes the bridge and the pre-PR hooks supervisor-aware alongside the engine.
It ships in a Core 3.x patch with its own version bump.

T2 rewrites the skill, removes the old engine, the wave-decision contract, and
`full-mode-engine.md`, and repoints every caller found by a repository-wide
search. T3 refreshes architecture, decisions, and coordination. T2 and T3 ship
in the next Core major, under the gate stated in the spec's Scope.

## Constraints

- ADR-0144 D1, D3, D7, D8, D9, D10, and D11.
- ADR-0151 D1 to D4, which replace ADR-0150 D3 and D5 and narrow ADR-0144 D3
  and D11 when T2 ships.
- ADR-0064 D3, D4, and D7 stay in force; only the run-id source changes.
- ADR-0014 D5: light mode starts no supervisor.
- `packs/AGENTS.md`: shipped text cites no internal records, and every `.apm/`
  change bumps the version.

## Construction tests

**Integration tests:**

- **VI-7901 (AC-0011, AC-0021):** copy the installed skill into an empty
  directory, then run a synthetic full code run under `python -I` with
  `sys.path` limited to `scripts/` and project-knowledge absent. An import hook fails on any module outside the standard library
  and that directory. T2 owns this test.

**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale | T3 | ADR shape lint | ADR-0125 `Superseded`; ADR-0151 `Accepted` |
| Interface compatibility | T2 | VI-7013 | Schema and rows gone |
| User and maintainer procedure | T2 | VI-7010, VI-7011 | Every engine-owned action routed |
| Planning contract | T2 | VI-7012 | new-spec states the in-envelope rule |
| Current architecture | T3 | Architecture review in the ledger | Pages describe the supervisor |
| Guides and sibling packs | T2 | VI-7013 | Search empty |
| Release history | T1, T2 | Version parity | 3.x line and major entry |
| Product coordination | T2, T3 | VI-7030 | Backlog dispositions in the ledger |

## Design (LLD)

### Design decisions

- **Bridge:**
  - It reads core's `run.json` fields when the file exists, and falls back to
    `engine-state.json` until T2 removes that path.
  - `run.json` is read with `read_confined_regular_file` and a 64 KiB bound.
  - `gate_question` is checked with `check_content_safety` under the
    `review-report` profile, then wrapped with `wrap_as_untrusted`; a rejected
    question shows a fixed placeholder. The status field and the gate-pending
    notification share one helper. `_content_safety.py` joins self-host's
    packaged-runtime copies in `agentbundle._data`, so the existing self-host
    drift check keeps it byte-identical to the pack source. The bridge imports
    only `agentbundle._data._content_safety`, with no repository or skill
    candidate in any mode; it does not reuse `_load_workspace_status_engine`'s
    candidate list.
- **Hooks:** both hooks discover runs from committed `delivery/approvals.jsonl`,
  not from the deletable `run.json`, through `list_confined_regular_files`. They
  fail on any non-zero `status --check` exit, which preserves today's
  fail-on-any-error rule, and fail rather than skip when an approved run exists
  but the supervisor script is missing.
- **Search terms for T2:** `loop-engine`, `loop-cohort`, `engine-state.json`,
  `_compat_facade`, `_review_compat`, `assets/state.json`,
  `full-mode-engine`, `loop-cohort-wave-decision`, and bare `review <verb>`
  forms. The search covers the whole repository outside the spec's history
  paths.
- **Tests that exercise removed files:** these suites are retired or rewritten,
  and each change is recorded in the ledger:
  - `test_review_boundary_policy.py`, which runs the engine and loads
    `_review_compat.py`;
  - `test_review_depth_and_verdict_contract.py`, which reads
    `full-mode-engine.md`;
  - `test_plan_records_its_approval.py`;
  - `test_loop_*`;
  - the roster suites named by the search.
- **Fact feed:** `_delivery_feed.py` changes its source from
  `<spec>/.shadow-acceptance/shadow-evidence.log` to the committed
  `<spec>/delivery/evidence.jsonl`, read through the same
  `replay_admitted_frames` reader, and drops its shadow-services gate. Its
  `delivery-fact-feed.v1` output is unchanged.
- **Capture gates:** the rewritten skill keeps the `spec-approved` capture step
  before `start` and the `plan-locked` step at `start`, because project-knowledge
  accepts work-loop producer captures only under those names.
- **Post-lock plan routes:** one supervisor change is needed, for a fence that
  is not red; the rest is guidance and pins. The shipped supervisor already commits a controller edit to `plan.md` as one `replan`
  step, keeps a task's `Tests:` and the plan's `## Design (LLD)` outside the
  reviewed envelope, includes stub fences in the task revision so a new fence
  must be proven red before `implement`, and refuses a worker result that
  touches the spec directory.
  - **Timing:** `next` opens an attempt and records the plan's bytes with it,
    and any plan change before that request's result is reported refuses it
    with `attempt-residue`. So the controller writes a task-start fence after
    reporting the previous request and before the `next` that issues the
    task's first request, and writes a design correction after reporting the
    open attempt and before the next `next`.
  - **Not-red recovery:** today a `stub-not-red` refusal on a `write-stub`
    result leaves that request open, so the fence fix the refusal asks for is
    itself refused as `attempt-residue`, and reverting it only repeats the
    refusal. T2 makes that refusal close the attempt with nothing committed,
    but only after the attempt checks pass. Because a surviving launch child
    can still write after closure, the next trusted-file change opens a
    `human-decision` with its diff instead of committing on the controller's
    word. How the closure is recorded, how the human-decision is shaped, and
    what happens to files the attempt left behind are
    `implementation-discovered`; the required property is AC-0026. The
    second change is in `report`: today it refuses any `human-decision` result
    while the spec directory has uncommitted edits. Only the post-closure
    confirmation is exempt, and only when the change set is exactly the files
    and bytes its digest binds. The core Replan
    corpus fixtures involve no not-red closure, so its no-approval assertion
    stays true.
  - **Guidance T2 changes:** `tdd-stubs.md` and `SKILL.md` EXECUTE state the
    task-start revision and the timing in place of the approved-plan fence;
    `SKILL.md`'s DECIDE routing, `delivery-contract-lifecycle.md`, new-spec's
    `assets/plan.md`, its plan contract, and any other live source the T2
    search finds send `implementation-discovered` seam or means grounding to
    the plan's design instead of the ledger; the ledger keeps execution
    observations.
  - **Pins T2 changes:** `tests/roster/test_tdd_stub_lifecycle_contract.py`
    widens its live sources to every file under the work-loop and new-spec
    skill sources and swaps its required and refused phrases;
    `test_supervisor_tdd.py` gains the cases VI-7023 names.
- **Backlog entries:** the open entries in `workspace.toml` that target
  `loop-cohort.py` are dispositioned through `close-work`, as superseded by this
  cutover or rewritten against the supervisor.

Owned by: T1, T2.

## Tasks

### T1: The bridge and the pre-PR hooks understand supervisor runs

- **Depends on:** spec:execution-supervisor-core/T6
- **Spec behavior:** AC-0013, AC-0014, AC-0015, AC-0017, AC-0018; goal-based.
- **Touches:**
  - `packages/agentbundle/agentbundle/workspace_mcp.py` and its tests, the
    packaged `_content_safety.py` projection with its self-host registration in
    `packages/agentbundle/agentbundle/build/self_host.py` and its
    `.gitattributes` `merge=regen` entry, and the package version;
  - `packs/core/.apm/hooks/pre-pr.py`, `tools/hooks/pre-pr.py`, and
    `tools/test-pre-pr.sh`;
  - Core manifests and changelog.
- **Verification mode:** goal-based
- **Tests:**
  - **VI-7001 (AC-0013, AC-0014):** a supervisor run binds the id and active
    signal. A `human-decision` shows the gate pending with its question, and the
    gate clears after resolution. No bridge tool or handler writes under
    `.supervisor/` or `delivery/`, or calls a supervisor verb other than
    `status`.
  - **VI-7002 (AC-0015):** a `gate_question` holding instruction-shaped text is
    displayed inside inert framing in both the status field and the
    notification; a rejected or oversized question shows only the placeholder.
    A planted repository-side `_content_safety.py` under `.claude/skills/` is
    not loaded.
  - **VI-7004 (AC-0013):** a symlinked, oversized, or malformed `run.json`
    leaves the bridge with no run and no gate.
  - **VI-7003 (AC-0017, AC-0018):** eight cases for both hooks. Exit 3 fails.
    Exit 1 fails. All runs at 0 pass. A terminal run at the cap passes. No
    `approvals.jsonl` passes. A deleted `run.json` still runs the check. A
    missing `work-supervisor.py` with an approved run fails. A symlinked spec
    directory is not discovered.
- **Done when:** VI-7001 through VI-7004 pass, the existing bridge and hook suites pass, and security-reviewer returns clean.

### T2: The skill drives the supervisor and the old engine is gone

- **Depends on:** T1; spec:execution-supervisor-core/T8; spec:execution-supervisor-attempt-security/T5; spec:execution-supervisor-review-gate/T4; ADR-0144 Accepted; Slice 3 shipped
- **Spec behavior:** AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0016, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026; goal-based, and TDD for AC-0026.
- **Touches:** every file the T2 search returns at the start of the task. That
  includes:
  - **Skill:** `SKILL.md`, `references/`, `evals/evals.json`,
    `profiles/work-loop.toml`, and `scripts/` (including `_delivery_feed.py`
    and its tests).
  - **Core:** `packs/core/seeds/.gitignore`, `packs/core/DESIGN.md`, and the
    Core manifests.
  - **Root:** `.gitignore`, `.workspace-prune-protected.toml`, `Makefile`, and
    `.github/workflows/`.
  - **Tools:** the tools named in the search.
  - **`agentbundle`:** `packages/agentbundle/tests/unit/test_catalogue_skill_spec_lint.py`.
  - **Other packs:** `packs/frontend-engineering/tests/` and the sibling-pack
    files.
  - **Guides:** `guides/`.
  - **new-spec:** `assets/plan.md` and `references/spec-and-plan-contract.md`.
  - **Contracts:** the wave-decision schema and `contracts/README.md`.
  - **Tests:** the test suites named in Design, including
    `tests/roster/test_tdd_stub_lifecycle_contract.py` and
    `packs/core/tests/skills/work-loop/test_supervisor_tdd.py`.
  - **Coordination:** `workspace.toml`.
  - **Generated copies:** via `make build-self`.
- **Verification mode:** goal-based
- **Tests:**
  - **VI-7010 (AC-0001, AC-0002, AC-0010):** three source checks: each
    engine-owned action maps to a supervisor verb, the role and condition
    pairing search is empty, and the close step names `work-item` capture.
  - **VI-7011:** the rewritten work-loop evals pass, and every reference link
    resolves.
  - **VI-7012:** the new-spec evals pass with the rewritten plan contract.
  - **VI-7013 (AC-0006, AC-0007, AC-0008, AC-0009):** removed files are absent
    from the source and the generated copies. The search is empty. Every kept
    script has a caller.
  - **VI-7014 (AC-0003, AC-0004, AC-0005):** direct-light and durable light runs
    leave no `.supervisor/` and no supervisor invocation. The light-mode text
    diff against the base commit shows only command swaps, and no bare
    `review <verb>` remains. The two named suites pass.
  - **VI-7015 (AC-0012):** `build-check-windows.yml` runs the synthetic run, and
    it reaches readiness.
  - **VI-7016 (AC-0016):** a fixture repository without the ignore rules
    finishes a full run, and no supervisor commit touches `.supervisor/` or
    `.loop-run/`.
  - **VI-7018:** the dispatched roster suites pass. Each retired or rewritten
    test is listed in the ledger.
  - **VI-7019 (AC-0019):** a synthetic run through the rewritten skill
    requests one `spec-approved` and one `plan-locked` capture, and Slice 3's
    AC-0006 capture fixtures pass.
  - **VI-7021 (AC-0020):** the Slice 3 feed suite, repointed at
    `delivery/evidence.jsonl` with the shadow setting unset, passes, and a
    supervisor run's review-failure receipt yields one candidate.
  - **VI-7022 (AC-0022, AC-0024):** the repinned
    `test_tdd_stub_lifecycle_contract.py` passes. It reads every file under
    the work-loop and new-spec skill sources (`SKILL.md`, `references/`,
    `assets/`, and `evals/`), requires the task-start revision, the
    open-attempt timing, and the working-plan route, and refuses the
    approved-plan fence requirement and the ledger route.
  - **VI-7023 (AC-0023, AC-0025):** with `WORK_SUPERVISOR_INTEGRATION=1`,
    `test_supervisor_tdd.py` runs four cases through the installed skill. A
    controller-added fence yields `replan`, then `stub` or `red`, then
    `implement`, with no approval request. A worker-added fence is refused
    with nothing committed. A design-only edit while no attempt is open
    yields one `replan` and keeps completed tasks complete. The same edit
    while an attempt is open refuses it with `attempt-residue`.
  - **VI-7024 (AC-0026):** TDD in `test_supervisor_tdd.py`. A `write-stub`
    result whose stub passes is refused with `stub-not-red` and commits
    nothing and closes the attempt. A controller edit that then removes or
    changes the fence raises no `attempt-residue`, opens a `human-decision`
    bound to its bytes, and is committed as one `replan` step only after
    confirmation; that confirmation is reported and admitted while the edit is
    still uncommitted. Each recovery is followed through the task's next
    admitted step: with the fence removed, the admitted `implement` commit
    holds none of the refused result's files; with the fence moved to a new
    path or changed at the same path, the next `write-stub` result is not
    refused because of them. A not-red launch that also writes
    `plan.md` stays refused for residue and does not close. Deleting the
    journal, `run.json`, and `security-events.jsonl` after closure, and again
    after a decline, leaves the attempt closed and the next trusted-file change
    still opens a bound confirmation. A trusted-file
    write between showing the diff and committing it commits nothing and opens
    a new decision. The recorded decision names its authority reference. A
    declined confirmation commits nothing, `next` refuses until the trusted
    files are restored, and the controller's next fence edit opens a new
    confirmation. Another `human-decision` kind reported over uncommitted
    plan edits is refused, and so is a confirmation reported while an extra
    path is also changed. The red test is written and proven red at
    EXECUTE against the current supervisor, which leaves the request open.
  - **VI-7901 (AC-0011, AC-0021)**, cross-cutting.
- **Done when:** every test above passes, `make lint-ruff lint-mypy` is clean, the Windows job passes, and security-reviewer returns clean.

### T3: Architecture, decisions, and coordination describe the shipped supervisor

- **Depends on:** T2
- **Spec behavior:** Durable Outputs rows for decision, architecture, and coordination; goal-based.
- **Touches:** the architecture pages named in the spec, including the knowledge pages; ADR-0151's status; `workspace.toml`
- **Verification mode:** goal-based
- **Tests:**
  - **VI-7020:** a bounded search of the named architecture pages finds no
    current-state mention of a removed script, `legacy-result-ack.v1`, a
    `tools/` builder, or a `packages/agentbundle/` supervisor home.
  - **VI-7030:** ADR-0151 is `Accepted`, and the ADR shape lint, the brief-coverage lint, and workspace
    reconcile pass.
- **Done when:** VI-7020 and VI-7030 pass, and the architecture review is recorded.

## Rollout

- **Delivery:** T1 ships in a Core 3.x patch. T2 and T3 ship in the next Core
  major. Rollback is reinstalling the prior major (ADR-0144 D7).
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** per the spec's Scope gate.

## Risks

- **Review size of T2:** mostly deletion and prose. Mitigation: the supervisor's
  behavior is proven by the sibling specs.

## Changelog

<!-- Approvals only. -->

- 2026-10-29: spec approved by eugenelim
- 2026-10-29: plan approved by eugenelim
