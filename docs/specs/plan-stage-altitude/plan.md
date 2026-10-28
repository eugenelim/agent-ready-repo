# Plan: plan-stage altitude

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (version bump, self-host, eval harness, no internal citations in shipped content); `tests/roster/test_tdd_stub_lifecycle_contract.py` as the existing owner of lifecycle content pins; uncertainty — none, the change is prose plus tests.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material.

## Approach

Three guidance edits, then one decision-and-release task, in one PR. The roster
test `test_tdd_stub_lifecycle_contract.py` is rewritten to this contract: one
sweep test parametrized by live source, plus one section-scoped test per
criterion, each test name prefixed by the source family it reads (`work_loop`,
`new_spec`, `docs`). Each guidance task selects its own family with `-k`, so its
Done when passes in full before the next task starts. The riskiest part is the
sweep: PLAN-time stub wording is restated in thirteen files in different words,
so T1 lands the whole parametrized sweep and marks the not-yet-edited families
`xfail(strict=True)`; T2 and T3 each remove their family's mark.

## Constraints

- ADR-0150 D1 to D7.
- `packs/AGENTS.md`: bump `pack.toml` and `plugin.json` together; update the eval harness; self-host after `.apm/` edits; no internal record citations under `packs/` (ADR-0150 is cited only from `docs/` and tests).
- `work-loop` PLAN step 7 is also edited by the in-progress `work-loop-evidence-modes` spec; this change touches only the TDD bullet's stub clause in step 7.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Maintainer procedure | T1, T2 | roster `work_loop` and `new_spec` tests green | suite green at the delivery commit |
| User-facing promise | T3 | roster `docs` tests green | guides read as stated |
| Current architecture | T3 | roster `docs` tests green | pages read as stated |
| Decision rationale | T4 | ADR status line and shape lint | ADR `Accepted` |
| Release history | T4 | version assertion | `catalogue verify` exit 0 |

## Design (LLD)

### Design decisions
<!-- Owned by: T1, T2 -->

**One owner for the red-test procedure.** `references/tdd-stubs.md` keeps the
procedure; SKILL.md step 8 and EXECUTE carry one sentence each and point at it.
The reference keeps stub-fullness (full assertion where the criterion pins
behavior, shape assertion otherwise), earning a red, stack detection, and the
`stub` fence grammar as the optional supervisor form; it drops the PLAN-time
parse/generate/validate/record phases and the `STUB: AC<n>` plan marker.

**One marker.** `implementation-discovered` replaces `no stub
(implementation-discovered)` and `no stub (mode)` (ADR-0150 D7). Historical
specs that carry the old form still contain the new token, so a reader of an
old plan still finds the ledger route. The supervisor projector's `no_stub`
field reads `no stub` text but no guard consumes it, so the engine is unaffected.

**Routing row edits, not a new row.** An unprotected mechanism is admitted to
both exception inputs: `unstarted-task-method` gains "or a mechanism no
protected class depends on" before its "**and no test can decide it
directly**" clause, and `cheap-with-an-oracle` gains the same phrase beside
"cheap, reversible detail". The residual row, the reversibility sentence, the
three keys, and every pinned destination phrase stay byte-identical, so
`test_load_bearing_claim_grounding.py` and `test_lld_change_preserves_pinned_texts.py`
stay unedited. `unstarted-task-method`'s destination gains one sentence sending a
mechanism to `## Design (LLD)` with its means marked `implementation-discovered`.
A paragraph after the table defines the five protected classes and the
property-versus-means split. `new-spec` step 7's "protected risk class" links
to that paragraph's anchor.

**Ledger record of the red.** The EXECUTE red's command and failing output go to
the verification ledger where a spec exists, which keeps the auditable record the
plan used to hold.

## Tasks

### T1: work-loop timing and the sweep

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/references/tdd-stubs.md`, `packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md`, `packs/core/.apm/agents/quality-engineer.md`, `tests/roster/test_tdd_stub_lifecycle_contract.py`, `packs/core/tests/skills/work-loop/test_lifecycle_routing_and_plan_digest.py`

**Tests:**
- AC-0001, AC-0002: `test_sweep[<source>]`, parametrized over the thirteen live sources, each proved present first; `new_spec` and `docs` sources carry `xfail(strict=True)`.
- AC-0003, AC-0004: `test_work_loop_step_8_*`, reading step 8 from `8. **Design construction tests` to `8a.`.
- AC-0005: `test_work_loop_execute_*`, reading EXECUTE's `Match discipline to verification mode:` list.
- AC-0006, AC-0007: `test_work_loop_tdd_stubs_*`.
- `test_lifecycle_routing_and_plan_digest.py` pins `implementation-discovered` in place of the old record.

**Done when:** `python3 -m pytest tests/roster/test_tdd_stub_lifecycle_contract.py packs/core/tests/skills/work-loop -q` passes.

### T2: new-spec routing and templates

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`, `packs/core/.apm/skills/new-spec/assets/plan.md`, `packs/core/.apm/skills/new-spec/assets/spec.md`, `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md`, `tests/roster/test_tdd_stub_lifecycle_contract.py`, `packs/core/tests/skills/new-spec/test_shaping_review.py`, `packs/core/tests/skills/new-spec/test_plan_working_material.py`

**Tests:**
- AC-0001, AC-0002: the `new_spec` sweep cases lose their `xfail`.
- AC-0008 to AC-0010: `test_new_spec_routing_*`, reading from the `load-bearing-claim-routing` anchor to `**Resolve repository anchors`; `test_load_bearing_claim_grounding.py` and `test_lld_change_preserves_pinned_texts.py` run unedited.
- AC-0011: `test_new_spec_plan_design_*`, reading `## Design (LLD)` to `### Design decisions`.
- AC-0012: `test_new_spec_agent_rules_*`, reading `## Agent Rules` to `### Always do`.
- `test_shaping_review.py`: the `stub: true` requirement and the two-dispositions sentence move to the `implementation-discovered` record and the EXECUTE red. `test_plan_working_material.py`: `LEDGER_ROUTE` follows the reworded contract note.

**Done when:** `python3 -m pytest tests/roster/test_tdd_stub_lifecycle_contract.py packs/core/tests/skills/new-spec packs/core/tests/skills/work-loop -q` passes.

### T3: guides and architecture

**Depends on:** T1

**Touches:** `guides/core/how-to/plan-and-execute-non-trivial-work.md`, `guides/core/explanation/core-pack.md`, `guides/core/reference/spec-shape-and-lld.md`, `docs/architecture/loop-infrastructure.md`, `docs/architecture/acceptance-centered-work-loop.md`, `tests/roster/test_tdd_stub_lifecycle_contract.py`

**Tests:**
- AC-0001, AC-0002: the `docs` sweep cases lose their `xfail`; `test_docs_*` asserts each guide and page names EXECUTE as where the red test is written.

**Done when:** `python3 -m pytest tests/roster/test_tdd_stub_lifecycle_contract.py tests/roster/test_load_bearing_claim_routing_surfaces.py tests/roster/test_spec_prose_discipline_guide.py tests/roster/test_verification_ledger_contract.py tests/roster/test_direct_light_documentation_boundary.py tests/roster/test_core_onboarding_documentation.py tools/test_stasis_retirement_claims.py -q` and `python3 tools/validate_guides.py` exit 0.

### T4: decision, evals, version, projections

**Depends on:** T1, T2, T3

**Touches:** `docs/adr/0150-tdd-red-test-is-written-at-execute-and-mechanism-lives-in-the-plan-design.md`, `packs/core/.apm/skills/work-loop/evals/evals.json`, `packs/core/.apm/skills/new-spec/evals/evals.json`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, self-host projections

**Tests:**
- AC-0014: `test_evals_*` in the roster file, and the `evals_json_shape` command.
- AC-0015: `test_version_*` in the roster file.
- AC-0016: the ADR's status line is set to `Accepted` by its decision-maker at spec approval; the shape-lint command.
- AC-0013, AC-0017, AC-0018: the named commands, and `git status --porcelain` after self-host.

**Effects:** none

**Done when:** every command AC-0013 to AC-0018 names exits 0 and `git status --porcelain` is empty after commit.

## Rollout

Ships with the next core release. Reversible by reverting the PR; no persisted state changes.

## Risks

- The `work-loop-evidence-modes` spec, now in progress on another worktree, edits step 8 and `tdd-stubs.md` and targets the same next patch version; whichever lands second rebases its text and version.

## Changelog
