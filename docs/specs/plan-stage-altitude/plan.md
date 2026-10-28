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

Two tasks in one PR. T1 makes every guidance edit and rewrites the roster test
`test_tdd_stub_lifecycle_contract.py` to this contract in the same step, so its
Done when passes at its own end: the sweep, the section-scoped pins, and the
four pack test files whose pins move. T2 then updates the evals, records the
decision, bumps the version, regenerates projections, and adds the eval and
version pins to the same roster file. The riskiest part is the sweep: PLAN-time
stub wording is restated in thirteen files in different words, so the sweep is
parametrized per live source and per retired phrase, and reads each source
whole.

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
| Maintainer procedure | T1 | roster content test green | suite green at the delivery commit |
| User-facing promise | T1 | roster content test green | AC-0021 |
| Current architecture | T1 | roster content test green | AC-0021 |
| Decision rationale | T2 | ADR status line and shape lint | ADR `Accepted` |
| Release history | T2 | version assertion | `catalogue verify` exit 0 |

## Design (LLD)

### Design decisions
<!-- Owned by: T1 -->

**One owner for the red-test procedure.** `references/tdd-stubs.md` keeps the
procedure; SKILL.md step 8 and EXECUTE carry one sentence each and point at it.
The reference keeps stub-fullness (full assertion where the criterion pins
behavior, shape assertion otherwise), earning a red, stack detection, and the
`stub` fence grammar as the optional supervisor form; it drops the PLAN-time
parse/generate/validate/record phases and the `STUB: AC<n>` plan marker. Its
worked example keeps counting the target's import failure as red.

**One marker.** `implementation-discovered` replaces the two `no stub` records
(ADR-0150 D7). Historical specs that carry the old form still contain the new
token, so a reader of an old plan still finds the ledger route. The supervisor
projector's `no_stub` field reads `no stub` text, but no guard consumes it, so
the engine is unaffected.

**Routing row edits, not a new row.** Both exception inputs gain "or a
mechanism claim whose falsehood could move only the chosen mechanism and on
which no protected class depends": in `unstarted-task-method` before its
"**and no test can decide it directly**" clause, in `cheap-with-an-oracle` beside
"cheap, reversible detail". A claim that could also move a criterion, boundary,
task graph, verification strategy, or failure direction still takes the
residual row, because the routing input stays the largest thing its falsehood
could move. The residual row, the reversibility sentence, and every pinned
destination phrase stay byte-identical. `unstarted-task-method`'s destination
gains one sentence sending a mechanism to `## Design (LLD)` with its means
marked `implementation-discovered`. A paragraph after the table names the five
protected classes and the property-versus-means split. `new-spec` step 7's
"protected risk class" is left as it is.

**Ledger record of the red.** The EXECUTE red's command and failing output go to
the verification ledger where a spec exists, which keeps the auditable record the
plan used to hold.

## Tasks

### T1: Guidance and its pins

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/references/tdd-stubs.md`, `packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md`, `packs/core/.apm/agents/quality-engineer.md`, `packs/core/.apm/skills/new-spec/SKILL.md`, `packs/core/.apm/skills/new-spec/assets/plan.md`, `packs/core/.apm/skills/new-spec/assets/spec.md`, `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md`, `guides/core/how-to/plan-and-execute-non-trivial-work.md`, `guides/core/explanation/core-pack.md`, `guides/core/reference/spec-shape-and-lld.md`, `docs/architecture/loop-infrastructure.md`, `docs/architecture/acceptance-centered-work-loop.md`, `tests/roster/test_tdd_stub_lifecycle_contract.py`, `packs/core/tests/skills/new-spec/test_shaping_review.py`, `packs/core/tests/skills/new-spec/test_plan_working_material.py`, `packs/core/tests/skills/work-loop/test_lifecycle_routing_and_plan_digest.py`

**Tests:**
- AC-0001, AC-0002: `test_sweep`, parametrized over the thirteen live sources, each proved present before it is read.
- AC-0003 to AC-0010: section-scoped reads of PLAN step 8, EXECUTE's `Match discipline to verification mode:` list, and `tdd-stubs.md`.
- AC-0011 to AC-0017: reads of the routing section through the same `_flat` and row parse `test_load_bearing_claim_grounding.py` uses; that file and `test_lld_change_preserves_pinned_texts.py` run unedited.
- AC-0018 to AC-0020: section-scoped reads of the two templates.
- AC-0021: one parametrized positive check over the five guide and architecture pages.
- `test_shaping_review.py`: the `stub: true` requirement and the two-dispositions sentence move to the `implementation-discovered` record and the EXECUTE red. `test_plan_working_material.py`: `LEDGER_ROUTE` follows the reworded contract note. `test_lifecycle_routing_and_plan_digest.py`: pins `implementation-discovered`.

**Done when:** `python3 -m pytest tests/roster/test_tdd_stub_lifecycle_contract.py tests/roster/test_load_bearing_claim_routing_surfaces.py tests/roster/test_spec_prose_discipline_guide.py tests/roster/test_verification_ledger_contract.py tests/roster/test_direct_light_documentation_boundary.py tests/roster/test_core_onboarding_documentation.py tools/test_stasis_retirement_claims.py packs/core/tests/skills/new-spec packs/core/tests/skills/work-loop -q` and `python3 tools/validate_guides.py` exit 0.

### T2: Evals, decision, version, projections

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/evals/evals.json`, `packs/core/.apm/skills/new-spec/evals/evals.json`, `tests/roster/test_tdd_stub_lifecycle_contract.py`, `docs/adr/0150-tdd-red-test-is-written-at-execute-and-mechanism-lives-in-the-plan-design.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, self-host projections

**Tests:**
- AC-0022, AC-0023: eval tests added to the roster file; `python3 -m pytest packs/core/tests/skills/work-loop/test_loop_engine.py -q -k evals_json_shape`.
- AC-0027: a version test added to the roster file, comparing both fields with each other and with `git show origin/main:packs/core/pack.toml`.
- AC-0025, AC-0026: the ADR's status line, set by its decision-maker at spec approval, and the shape-lint command.
- AC-0024, AC-0028, AC-0029: the named commands, and `git status --porcelain` after self-host.

**Effects:** none

**Done when:** every command AC-0024 to AC-0029 names exits 0, the roster file passes, and `git status --porcelain` is empty after commit.

## Rollout

Ships with the next core release. Reversible by reverting the PR; no persisted state changes.

## Risks

- The `work-loop-evidence-modes` spec, now in progress on another worktree, edits step 8 and `tdd-stubs.md` and targets the same next patch version; whichever lands second rebases its text and version.

## Changelog
