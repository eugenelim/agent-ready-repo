# Spec: plan-stage altitude

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0150
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

A full-mode `work-loop` plan reaches approval carrying test intent — behavior, boundary, verification mode — rather than test code, and the red test is written and proven red at EXECUTE. A spec settles a mechanism before approval only when a protected class (security boundary, data loss or durability, migration or persisted state, public interface, irreversible operation) depends on it; every other mechanism lives in the plan's design, where a post-approval correction is a verification-ledger observation rather than an amendment.

## What Changes

- `work-loop` PLAN step 7's TDD bullet, step 8, EXECUTE's TDD line, and DECIDE's ledger routing — the red test moves to EXECUTE; a `stub` fence stays optional for supervisor red proof; `implementation-discovered` is the one marker.
- `work-loop/references/tdd-stubs.md` — rewritten around writing and proving the red test at EXECUTE; the `stub` fence grammar is kept as the optional supervisor form.
- `work-loop/references/delivery-contract-lifecycle.md` — the ledger route keys on `implementation-discovered` for a seam or a design means.
- `new-spec` SKILL.md — the claim-routing table sends an unprotected mechanism to its two exception rows and defines the protected classes once; the Testing Strategy pointer drops plan-owned stub code.
- `new-spec/assets/plan.md` and `assets/spec.md` — `## Design (LLD)` owns mechanism and the marker; Agent Rules excludes mechanism; the task template drops the required stub.
- `new-spec/references/spec-and-plan-contract.md` and `agents/quality-engineer.md` — their restatements of the PLAN-time stub follow.
- Guides, `docs/architecture/loop-infrastructure.md`, and the TDD row of `docs/architecture/acceptance-centered-work-loop.md` — they teach the same timing.
- ADR-0150 records the change to RFC-0028's timing decision.
- Tests whose pins move: `tests/roster/test_tdd_stub_lifecycle_contract.py` (rewritten to this contract), `packs/core/tests/skills/new-spec/test_shaping_review.py` (dispositions and `stub: true` pins), `packs/core/tests/skills/new-spec/test_plan_working_material.py` (`LEDGER_ROUTE`), and `packs/core/tests/skills/work-loop/test_lifecycle_routing_and_plan_digest.py` (the marker).
- Eval cases, the core pack version, and the self-hosted projections.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | The skills and agent are the procedure an agent follows | `packs/core/.apm/skills/work-loop/`, `packs/core/.apm/skills/new-spec/`, `packs/core/.apm/agents/quality-engineer.md` | core pack maintainers | content contract tests and eval records | tests green; projections regenerated |
| User-facing promise | Adopters read when the red test is written | `guides/core/how-to/plan-and-execute-non-trivial-work.md`, `guides/core/explanation/core-pack.md`, `guides/core/reference/spec-shape-and-lld.md` | core pack maintainers | roster content test | guides state EXECUTE-time red |
| Current architecture | Two architecture pages describe the stub boundary | `docs/architecture/loop-infrastructure.md`, `docs/architecture/acceptance-centered-work-loop.md` | core pack maintainers | roster content test | page states EXECUTE-time red |
| Decision rationale | Accepted RFC-0028 decided the PLAN-time timing | `docs/adr/0150-tdd-red-test-is-written-at-execute-and-mechanism-lives-in-the-plan-design.md` | eugenelim | ADR shape lint | ADR `Accepted` (AC-0016) |
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

- **Guidance content (AC-0001 to AC-0012):** goal-based, by pytest content assertions in `tests/roster/test_tdd_stub_lifecycle_contract.py`, which this change extends to read every live source and which CI already runs. Guidance has no runtime to drive, so a section-scoped phrase plus a whitespace-flattened forbidden-phrase sweep is the check that can red.
- **Regression (AC-0013):** goal-based, by the full pack and roster trees.
- **Evals and release (AC-0014, AC-0015):** goal-based, by the same roster file and `test_evals_json_shape`; running the eval cases against a model is not part of this delivery.
- **Decision and projection (AC-0016 to AC-0018):** goal-based, by the ADR status line and command exit status.

## Acceptance Criteria

**Live sources** are these files: `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/references/tdd-stubs.md`, `packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md`, `packs/core/.apm/skills/new-spec/SKILL.md`, `packs/core/.apm/skills/new-spec/assets/plan.md`, `packs/core/.apm/skills/new-spec/assets/spec.md`, `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md`, `packs/core/.apm/agents/quality-engineer.md`, `guides/core/how-to/plan-and-execute-non-trivial-work.md`, `guides/core/explanation/core-pack.md`, `guides/core/reference/spec-shape-and-lld.md`, `docs/architecture/loop-infrastructure.md`, and `docs/architecture/acceptance-centered-work-loop.md`. A phrase check on a live source compares case-insensitively after collapsing every whitespace run to one space.

### No PLAN-time stub code

- [ ] **AC-0001.** No live source contains any of: `exact stub code`, `exact test code`, `approved stub`, `approved TDD block`, `approved block`, `approved code unchanged`, `land committed red stubs`, `planning proof`, `stub: true`, `no stub (mode)`, or `no stub (implementation-discovered)`.
- [ ] **AC-0002.** No live source other than `references/tdd-stubs.md` contains `byte identity`.

### work-loop

- [ ] **AC-0003.** `work-loop` PLAN step 8, from `8. **Design construction tests` to `8a.`, states that a TDD task's `Tests:` names the behavior, the boundary it is checked at, and the verification mode.
- [ ] **AC-0004.** The same step states that the red test is written and proven red at EXECUTE.
- [ ] **AC-0005.** `work-loop` EXECUTE's TDD line states that the red test is written at the real test location and fails for the intended reason before production code changes.
- [ ] **AC-0006.** `references/tdd-stubs.md` states that a collection, import or setup error, or a timeout is not red, and that where a spec exists the command and its failing output go to the verification ledger.
- [ ] **AC-0007.** `references/tdd-stubs.md` states that the `stub` fence is optional, that the supervisor materializes a fence unchanged and proves it red, and that a supervisor task without one gets no engine-observed red proof while EXECUTE's red-first rule still applies.

### Mechanism routing

- [ ] **AC-0008.** `new-spec`'s claim-routing section, from the `load-bearing-claim-routing` anchor to `**Resolve repository anchors`, names the five protected classes: security boundary, data loss or durability, migration or persisted state, public interface, irreversible operation.
- [ ] **AC-0009.** In that section, both exception rows' inputs admit a mechanism no protected class depends on, so such a claim never takes `reaches-the-contract`; the three rows, their keys, and the residual sentence stay as they are.
- [ ] **AC-0010.** In that section, a claim about a protected class's property settles before approval, and the means that delivers it lives in the plan's `## Design (LLD)`.
- [ ] **AC-0011.** `assets/plan.md`'s `## Design (LLD)` section, up to `### Design decisions`, states that mechanism lives there, that a means no code grounds yet is marked `implementation-discovered`, and that its chosen means and any correction go to the verification ledger.
- [ ] **AC-0012.** `assets/spec.md`'s `## Agent Rules` section, up to `### Always do`, states that a syscall, flag, helper name, or exact write order is mechanism that belongs in the plan's `## Design (LLD)`.

### Regression, evals, decision, release

- [ ] **AC-0013.** `python3 -m pytest packs/core/tests tests/roster tools/test_stasis_retirement_claims.py -q` passes.
- [ ] **AC-0014.** The eval records `tdd-stub-replaces-prose-or-records-no-stub-reason` and `tdd-stub-uses-the-stub-fence` (work-loop) and `tdd-stub-proof-belongs-to-work-loop-plan` (new-spec) each expect the red test written at EXECUTE, and `python3 -m pytest packs/core/tests/skills/work-loop/test_loop_engine.py -q -k evals_json_shape` passes.
- [ ] **AC-0015.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same version, one patch above the base commit's.
- [ ] **AC-0016.** ADR-0150 reads `Status: Accepted`, and `python3 -m pytest tests/roster/test_lint_adr_shape_corpus.py -q` passes.
- [ ] **AC-0017.** `agentbundle catalogue lint --root . --deep`, `agentbundle catalogue verify --root .`, and `python3 tools/validate_guides.py` exit 0.
- [ ] **AC-0018.** `agentbundle catalogue self-host --root . --write` leaves no tracked change after the delivery commit.

## Follow-ons

- eugenelim: the uncommitted `work-loop-evidence-modes` spec restates the PLAN-time plan stub in its AC-0003 and AC-0020; its author rewords them on rebase.

## Assumptions

none
