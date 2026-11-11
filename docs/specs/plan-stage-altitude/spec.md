# Spec: plan-stage altitude

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0150, ADR-0144
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A full-mode `work-loop` plan reaches approval carrying test intent — behavior, boundary, verification mode — rather than test code, and the red test is written and proven red at EXECUTE. A mechanism claim whose falsehood could move only the mechanism, and on which no protected class (security boundary, data loss or durability, migration or persisted state, public interface, irreversible operation) depends, lives in the plan's design when no test can decide it, where a post-approval correction is a verification-ledger observation rather than an amendment, and is settled in code when a test can decide it and undoing it is reversible; every other load-bearing claim still settles before approval.

## What Changes

- `work-loop` PLAN step 7's TDD bullet, step 8, EXECUTE's TDD line, and DECIDE's ledger routing — the red test moves to EXECUTE; a `stub` fence is not required in the approved plan but still feeds supervisor red proof; `implementation-discovered` is the one marker.
- `work-loop/references/tdd-stubs.md` — rewritten around writing and proving the red test at EXECUTE; the `stub` fence grammar is kept as the supervisor's red-proof input, carried in the approved task.
- `work-loop/references/delivery-contract-lifecycle.md` — the ledger route keys on `implementation-discovered` for a seam or a design means.
- `new-spec` SKILL.md — the claim-routing table sends a mechanism-only, unprotected claim to its two exception rows and defines the protected classes once; the Testing Strategy pointer drops plan-owned stub code.
- `new-spec/assets/plan.md` and `assets/spec.md` — `## Design (LLD)` owns mechanism and the marker; Agent Rules excludes mechanism; the task template drops the required stub.
- `new-spec/references/spec-and-plan-contract.md` and `agents/quality-engineer.md` — their restatements of the PLAN-time stub follow.
- Guides, `docs/architecture/loop-infrastructure.md`, and the TDD row of `docs/architecture/acceptance-centered-work-loop.md` — they teach the same timing.
- ADR-0150 records the change to RFC-0028's timing decision.
- Tests whose pins move: `tests/roster/test_tdd_stub_lifecycle_contract.py` (rewritten to this contract), `packs/core/tests/skills/new-spec/test_shaping_review.py` (dispositions and `stub: true` pins), `packs/core/tests/skills/new-spec/test_plan_working_material.py` (`LEDGER_ROUTE`), and `packs/core/tests/skills/work-loop/test_lifecycle_routing_and_plan_digest.py` (the marker). `packs/core/tests/skills/new-spec/test_load_bearing_claim_grounding.py` and `test_lld_change_preserves_pinned_texts.py` pin the routing table and run unedited.
- Eval cases, the core pack version, and the self-hosted projections.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | The skills and agent are the procedure an agent follows | `packs/core/.apm/skills/work-loop/`, `packs/core/.apm/skills/new-spec/`, `packs/core/.apm/agents/quality-engineer.md` | core pack maintainers | content contract tests and eval records | tests green; projections regenerated |
| User-facing promise | Adopters read when the red test is written | `guides/core/how-to/plan-and-execute-non-trivial-work.md`, `guides/core/explanation/core-pack.md`, `guides/core/reference/spec-shape-and-lld.md` | core pack maintainers | roster content test | AC-0021 |
| Current architecture | Two architecture pages describe the stub boundary | `docs/architecture/loop-infrastructure.md`, `docs/architecture/acceptance-centered-work-loop.md` | core pack maintainers | roster content test | page states EXECUTE-time red |
| Decision rationale | Accepted RFC-0028 decided the PLAN-time timing | `docs/adr/0150-tdd-red-test-is-written-at-execute-and-mechanism-lives-in-the-plan-design.md` | eugenelim | ADR shape lint | ADR `Accepted` (AC-0025) |
| Release history | A non-cosmetic pack change ships under a new version | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` | core pack maintainers | both files read the same new patch version | catalogue verify passes |

## Agent Rules

### Always do

- Cut a restatement before adding text; where an owner exists, point at it.
- Keep the protected classes settling before approval, through `new-spec`'s `reaches-the-contract` route.
- Bump `pack.toml` and `.claude-plugin/plugin.json` together, and regenerate projections with self-host rather than editing them.

### Ask first

- Changing what PLAN step 7 lists as verification modes, or any reviewer agent other than `quality-engineer`'s timing note.
- Changing the RFC-0028 body or erratum.

### Never do

- No change to `work-loop` scripts, the supervisor engine, or the approval digest.
- No new skill, agent, script, test-file CI wiring, or dependency, and no new top-level directory.
- No edit to an adapter projection except through self-host.

## Testing Strategy

- **Guidance content (AC-0001 to AC-0021):** goal-based, by pytest content assertions in `tests/roster/test_tdd_stub_lifecycle_contract.py`, which this change extends to read every live source and which CI already runs. Guidance has no runtime to drive, so a section-scoped phrase plus a whitespace-flattened forbidden-phrase sweep is the check that can red.
- **Evals (AC-0022, AC-0023):** goal-based, by the same roster file and `test_evals_json_shape`; running the eval cases against a model is not part of this delivery.
- **Regression, decision, release, projection (AC-0024 to AC-0029):** goal-based, by command exit status, the ADR status line, and the two version fields.

## Acceptance Criteria

**Live sources** are these files: `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/references/tdd-stubs.md`, `packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md`, `packs/core/.apm/skills/new-spec/SKILL.md`, `packs/core/.apm/skills/new-spec/assets/plan.md`, `packs/core/.apm/skills/new-spec/assets/spec.md`, `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md`, `packs/core/.apm/agents/quality-engineer.md`, `guides/core/how-to/plan-and-execute-non-trivial-work.md`, `guides/core/explanation/core-pack.md`, `guides/core/reference/spec-shape-and-lld.md`, `docs/architecture/loop-infrastructure.md`, and `docs/architecture/acceptance-centered-work-loop.md`. **Retired phrases** are: `exact stub code`, `exact test code`, `approved stub`, `approved-stub`, `approved TDD block`, `approved block`, `approved code unchanged`, `proposed test bytes`, `land committed red stubs`, `in-PLAN stub generation`, `PLAN's TDD-stub generation`, `planning proof`, `stub: true`, `no stub (mode)`, `no stub (implementation-discovered)`, and `` `no stub` disposition ``. A phrase check compares case-insensitively after collapsing every whitespace run to one space.

### No PLAN-time stub code

- [x] **AC-0001.** No live source contains a retired phrase.
- [x] **AC-0002.** No live source contains `byte identity` or `byte-identity`, except `references/tdd-stubs.md` and the TDD row of `docs/architecture/acceptance-centered-work-loop.md`, where each occurrence names the supervisor's `stub` fence in the same sentence or table cell.

### work-loop

- [x] **AC-0003.** `work-loop` PLAN step 8, from `8. **Design construction tests` to `8a.`, states that a TDD task's `Tests:` names the behavior, the boundary it is checked at, and the verification mode.
- [x] **AC-0004.** The same step states that the red test is written and proven red at EXECUTE.
- [x] **AC-0005.** `work-loop` EXECUTE's TDD line states that the red test is written at the real test location and fails for the intended reason before production code changes.
- [x] **AC-0006.** `references/tdd-stubs.md` states that an import failure of the not-yet-written target counts as red, and that any other collection, import, or setup error, or a timeout, does not.
- [x] **AC-0007.** `references/tdd-stubs.md` states that, where a spec exists, the red's command and failing output go to the verification ledger.
- [x] **AC-0008.** `references/tdd-stubs.md` states that the approved plan does not require a `stub` fence.
- [x] **AC-0009.** `references/tdd-stubs.md` states that, where a supervisor run executes a TDD task, the plan author carries its fence in the approved task.
- [x] **AC-0009b.** `references/tdd-stubs.md` states that a supervisor task without a fence gets no engine-observed red proof and that EXECUTE's red-first rule still applies to it.
- [x] **AC-0010.** `references/tdd-stubs.md` states that a fence the supervisor refuses as `stub-not-red` is either made to fail for the intended reason or removed.

### Mechanism routing

In this group, "the routing section" is `new-spec` SKILL.md from the `load-bearing-claim-routing` anchor to `**Resolve repository anchors`.

- [x] **AC-0011.** The routing section names the five protected classes: security boundary, data loss or durability, migration or persisted state, public interface, irreversible operation.
- [x] **AC-0012.** In the routing section, the `unstarted-task-method` input admits a mechanism claim whose falsehood could move only the chosen mechanism and on which no protected class depends.
- [x] **AC-0013.** In the routing section, the `cheap-with-an-oracle` input admits the same claim only when it is also reversible, by the reversibility sentence that row already states.
- [x] **AC-0014.** The routing section's table has exactly three rows, keyed `reaches-the-contract`, `unstarted-task-method`, and `cheap-with-an-oracle`.
- [x] **AC-0014a.** The `reaches-the-contract` input keeps the sentence `no load-bearing claim is unrouted`.
- [x] **AC-0015.** In the routing section, the `unstarted-task-method` destination sends a mechanism to the plan's `## Design (LLD)` with its means marked `implementation-discovered`.
- [x] **AC-0016.** The routing section states that a claim about a protected class's property settles before approval.
- [x] **AC-0017.** The routing section states that the means delivering a protected property lives in the plan's `## Design (LLD)`.
- [x] **AC-0018.** `assets/plan.md`'s `## Design (LLD)` section, up to `### Design decisions`, states that mechanism lives there.
- [x] **AC-0019.** The same section states that a means no code grounds yet is marked `implementation-discovered` and that its chosen means and any correction go to the verification ledger.
- [x] **AC-0020.** `assets/spec.md`'s `## Agent Rules` section, up to `### Always do`, states that a syscall, flag, helper name, or exact write order is mechanism that belongs in the plan's `## Design (LLD)`.

### Guides and architecture

- [x] **AC-0021.** Each of the three guides and two architecture pages in the live-source list states that the red test is written at EXECUTE.

### Evals

- [x] **AC-0022.** Neither `packs/core/.apm/skills/work-loop/evals/evals.json` nor `packs/core/.apm/skills/new-spec/evals/evals.json` contains a retired phrase.
- [x] **AC-0023.** The records `tdd-stub-replaces-prose-or-records-no-stub-reason` and `tdd-stub-uses-the-stub-fence` (work-loop) and `tdd-stub-proof-belongs-to-work-loop-plan` (new-spec) each expect the red test written at EXECUTE.

### Regression, decision, release

- [x] **AC-0024.** `python3 -m pytest packs/core/tests tests/roster tools/test_stasis_retirement_claims.py -q` passes.
- [x] **AC-0025.** ADR-0150 reads `Status: Accepted`.
- [x] **AC-0026.** `python3 -m pytest tests/roster/test_lint_adr_shape_corpus.py -q` passes.
- [x] **AC-0027.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same version, one patch above the version `packs/core/pack.toml` carries on `main` at merge.
- [x] **AC-0028.** `agentbundle catalogue lint --root . --deep`, `agentbundle catalogue verify --root .`, and `python3 tools/validate_guides.py` exit 0.
- [x] **AC-0029.** `agentbundle catalogue self-host --root . --write` leaves no tracked change after the delivery commit.

## Follow-ons

- Resolved: `execution-supervisor-cutover` owns both post-lock routes as its AC-0022 to AC-0025, and ADR-0151 supersedes ADR-0150 D3 and D5 in part when that cutover's skill rewrite ships.
- eugenelim: the supervisor's `stub-not-red` refusal and the module docstring in `packs/core/.apm/skills/work-loop/scripts/_supervisor_tdd.py` still ask for a `no stub` disposition; rewording them to "remove the fence or make it fail" is a script change this spec does not make.
- eugenelim: the in-progress `work-loop-evidence-modes` spec restates the PLAN-time plan stub in its AC-0003 and AC-0020; its author rewords them on rebase.

## Assumptions

none
