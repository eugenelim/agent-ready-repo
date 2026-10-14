# Plan: Execution supervisor cutover

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
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

- ADR-0144 D1, D7, D8, D9, and D10.
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
| Decision rationale | T3 | ADR shape lint | ADR-0125 `Superseded` |
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
  - `gate_question` passes through `_content_safety.wrap_as_untrusted` before
    display.
- **Hooks:** both hooks discover runs from committed `delivery/approvals.jsonl`,
  not from the deletable `run.json`. They fail on any non-zero `status --check`
  exit, which preserves today's fail-on-any-error rule.
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
- **Backlog entries:** the open entries in `workspace.toml` that target
  `loop-cohort.py` are dispositioned through `close-work`, as superseded by this
  cutover or rewritten against the supervisor.

Owned by: T1, T2.

## Tasks

### T1: The bridge and the pre-PR hooks understand supervisor runs

- **Depends on:** spec:execution-supervisor-core/T6
- **Spec behavior:** AC-0013, AC-0014, AC-0015, AC-0017, AC-0018; goal-based.
- **Touches:**
  - `packages/agentbundle/agentbundle/workspace_mcp.py` and its tests;
  - `packs/core/.apm/hooks/pre-pr.py`, `tools/hooks/pre-pr.py`, and
    `tools/test-pre-pr.sh`;
  - Core manifests and changelog.
- **Verification mode:** goal-based
- **Tests:**
  - **VI-7001 (AC-0013, AC-0014):** a supervisor run binds the id and active
    signal. A `human-decision` shows the gate pending with its question, and the
    gate clears after resolution.
  - **VI-7002 (AC-0015):** a `gate_question` holding instruction-shaped text is
    displayed inside inert framing.
  - **VI-7003 (AC-0017, AC-0018):** six cases for both hooks. Exit 3 fails.
    Exit 1 fails. All runs at 0 pass. A terminal run at the cap passes. No
    `approvals.jsonl` passes. A deleted `run.json` still runs the check.
- **Done when:** VI-7001 through VI-7003 pass, the existing bridge and hook suites pass, and security-reviewer returns clean.

### T2: The skill drives the supervisor and the old engine is gone

- **Depends on:** T1; spec:execution-supervisor-core/T8; spec:execution-supervisor-attempt-security/T5; spec:execution-supervisor-review-gate/T4; ADR-0144 Accepted; Slice 3 shipped
- **Spec behavior:** AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0016, AC-0019, AC-0020, AC-0021; goal-based.
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
  - **Tests:** the test suites named in Design.
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
  - **VI-7901 (AC-0011, AC-0021)**, cross-cutting.
- **Done when:** every test above passes, `make lint-ruff lint-mypy` is clean, the Windows job passes, and security-reviewer returns clean.

### T3: Architecture, decisions, and coordination describe the shipped supervisor

- **Depends on:** T2
- **Spec behavior:** Durable Outputs rows for decision, architecture, and coordination; goal-based.
- **Touches:** the architecture pages named in the spec, including the knowledge pages; `workspace.toml`
- **Verification mode:** goal-based
- **Tests:**
  - **VI-7020:** a bounded search of the named architecture pages finds no
    current-state mention of a removed script, `legacy-result-ack.v1`, a
    `tools/` builder, or a `packages/agentbundle/` supervisor home.
  - **VI-7030:** the ADR shape lint, the brief-coverage lint, and workspace
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
