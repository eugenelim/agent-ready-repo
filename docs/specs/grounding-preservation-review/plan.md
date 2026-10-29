# Plan: Preservation through typed review

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** the review-module chain exercised end to end by
  `packs/core/tests/skills/work-loop/test_review_bridge.py::test_supported_assessment_commits_complete_receipts_and_replays_projection`
  (persist a report, assess, bridge, evaluate `contradicted`); the
  plan-resident map fixture of
  `packs/core/tests/skills/work-loop/test_consumer_map_disposable.py`; the
  property and receipt helpers of
  `packs/core/tests/skills/work-loop/test_preservation_contract_proof.py`;
  `new-spec`'s `references/shared-substrate-preservation.md` (criterion shape,
  contradiction statement) and `work-loop`'s `references/preservation-evidence.md`
  (the four kinds of incomplete evidence); the eval-construction pin of
  `packs/core/tests/skills/work-loop/test_repository_grounding_eval.py`.

## Approach

Reviewer guidance changes first, because the eval cases and graded runs test
it. The deterministic suite comes next and needs no guidance: it proves that a
typed finding already reaches the right criterion through shipped code, so the
guidance only has to make reviewers produce that shape. Release and graded runs
come last, against the rebuilt projections.

## Constraints

- `packs/AGENTS.md` § Shipped pack content carries no internal-governance
  citations, § Version bump rule, and § Self-hosting projection.
- `tools/lint-pack-test-boundary.py`: a pack test reads nothing above its pack.
- The supervisor cutover's T2 deletes `_review_compat.py`, `loop-engine.py`,
  and `loop-cohort.py`. No C3 test loads them.
- C0's recorded evaluator limits: the verdict reads only term, outcome, and
  acceptance fingerprint, and a fresh `supported-review-failure` receipt
  outranks a satisfying receipt when the contradiction rule names it.
- Re-check Core's version on origin/main just before pushing and again before
  merge.

## Construction tests

**Integration tests:** T2's module is the integration test.
**Manual verification:** the graded runs in T5.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise — the how-to guide sentence | T1 | Sentence in § REVIEW | Sentence present |
| Current product truth — brief Spec map row | T4 | Row added; spec `Brief:` line | Row derives `Shipped` |
| Release history — the Core patch AC-0023 states | T4 | Manifests and fragment | AC-0023, AC-0024 |
| Reusable learning — verification ledger | T5 | Graded and baseline runs recorded | The spec's Reusable learning closeout condition |

## Design (LLD)

### Behavior & rules

The typed-report section, identical in both reviewer files, is a new
`## Typed report` section placed immediately before
`## Vague feedback is unhelpful feedback`, a heading both files carry. It says:

1. It governs only the modes that return a findings block; the property
   decides, so the section names no mode, and intent mode falls outside it.
   AC-0003 owns the rule for a request that names no spec. Without a request, the findings block or clean line is the whole output and
   the shipped raw classifier reads it as before. When the caller asks for a
   typed report, the reviewer returns only one fenced `json` block holding
   `terminal_status` and `findings`, which the caller completes and passes to
   the typed review path rather than to the raw classifier. That return is not
   the file's `adversarial-review-complete` or `quality-review-complete` gate,
   whose text stays unchanged; the typed obligation decision governs it.
2. `clean`, `unable`,
   and `indeterminate` carry no findings; `findings` carries one or more. The
   caller fills the report's `schema_version`, `report_id`, `role`, `subject`,
   and `lineage`.
3. The typed report carries only material findings, defined in the section
   itself so `quality-engineer` can decide it without the adversarial
   reviewer's severity text: a Blocker or Concern whose defect something
   outside the finding establishes. The shipped evidence store writes a
   review-failure receipt for every supported finding whatever its `material`
   value, so a typed non-material finding would contradict its criterion.
   Leaving it out keeps Nits and judgement calls non-blocking, at the cost
   that a typed-report return does not show them: a review that completes
   with no material finding returns `clean`. `unable` and
   `indeterminate` keep their meanings. The "keep flagging both" rule still holds
   for the findings block, which a caller asks for when it wants them.
4. Each finding carries the nine finding fields. `rule_ref` names the rule or
   criterion broken; `observation`, `reachable_path`, and `actual_failure`
   carry the predicate self-check's observation, path, and consequence;
   `evidence_refs` carries the `file:line` citations; `material` is `true`.
5. `affected_acceptance_criteria` lists identifiers the caller-named spec
   contains, at least one. When any material finding has none to name, the
   status is `indeterminate` with no findings. The review then stops for owner
   direction instead of losing the finding or inventing an identifier.

The lens checks continue the existing numbering:

- **`adversarial-reviewer`, check 6 of `### Spec-stage checks`**, with check 10
  of `### Implementation-stage checks` applying it to the diff. It fires only when the change adds or alters
  a member of a shared substrate. For each consumer class reachable from the
  changed member, the reviewer finds the accepted preservation criterion that
  covers it. A missed class is a finding. It names the covering criterion, or
  the criterion whose change reaches the consumer, with an amendment as the
  fix. A consumer reached only through an explicit filter raises nothing.
- **`quality-engineer`, check 35 in a new `### Preservation evidence`
  subsection after `### Performance ergonomics`.** It sits beside the strength
  judgment the adversarial reviewer already leaves to this lens. For each accepted preservation criterion, the evidence is current, its
  expected side does not come from the code under test, and its oracle fails
  on a named mutation. Missing, stale, tautological, and feature-only evidence
  each make a finding against that criterion.

Traces to: AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0022 · none.

Owned by: T1.

### Data & schema

T2's fixture builds the three properties with the C0 helper shape: one
`test-result` term each, `all` satisfaction, and a `supported-review-failure`
contradiction rule. Their receipts go through `EvidenceStore.append_receipt`.
The delivery subject is projected with `_subject_source.project_legacy_subject`
over a temporary git repository, as in C1's fixture. The review subject is
projected with `_review_selection.project_review_subject` from that delivery
subject and the product's changed paths, which exclude the spec directory.
Obligations come from `select_review_obligations` with a two-role mandatory
policy, and `decide_review_obligation` decides AC-0009, AC-0011, and AC-0015: the `indeterminate`
tip gives reason `report-unable`, and no persisted report gives
`denied-no-current-report` from `_review_contracts.select_current_report`. Reports persist through
`_review_persistence.append_current_review_report`. Assessments come from
`_review_assessment.assess_finding_actual_failure` and are recorded through
`_review_bridge.append_finding_assessment_bridge`. Each finding's
`affected_acceptance_criteria` holds its property's ID, so the store's
routing binds the receipt.

The eval fixture under `work-loop/evals/files/preservation-review/` is one
small graph package:

- `spec.md`: an excerpt reading `Status: Approved`, with `CRIT-1` (value nodes are created), `CRIT-2`
  (ordinary calls resolve to no value node), and `CRIT-3` (default search and
  listing exclude value nodes).
- `graph.py`: a model with the new value kind, a `search` path that filters
  values behind an explicit `include_values` flag, and a listing consumer that
  iterates every node unfiltered.
- `test_graph.py`: an ordinary-calls test whose expected side calls the code
  under test.

The missed-consumer prompt names the change and asks for a typed review; the
weak-evidence prompt asks for a typed quality review of the tests.

Traces to: AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017 ·
`contracts/delivery/review-report.v1.schema.json`,
`contracts/delivery/finding.v1.schema.json`.

Owned by: T2, T3.

## Tasks

### T1: Reviewer guidance

**Depends on:** none

**Touches:** packs/core/.apm/agents/adversarial-reviewer.md, packs/core/.apm/agents/quality-engineer.md, guides/core/how-to/plan-and-execute-non-trivial-work.md, packs/core/tests/pack/test_preservation_review_guidance.py

**Mode:** TDD. The content pins fail while the sections are absent.

**Tests:**
- AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008 as content pins in
  `test_preservation_review_guidance.py`.
- The existing suites that read the two reviewer files pass:
  `test_review_depth_and_verdict_contract.py`,
  `test_exploration_consumer_boundary.py`,
  `test_finding_adjudication_contract.py`, `test_ride_along_admission_test.py`,
  `test_reviewer_project_knowledge_boundary.py`, `test_spec_authority_scoping.py`,
  `test_shaping_review_contract.py`, `skills/new-spec/test_shaping_review.py`,
  and under `skills/work-loop/`
  `test_evidence_modes_contract.py`, `test_non_gating_nits.py`,
  `test_reviewer_lens_ownership.py`, `test_repository_idiom_delta.py`; and
  `skills/new-spec/test_artifact_prose_discipline.py`.
- `tests/roster/test_tdd_stub_lifecycle_contract.py`, through the dispatched
  `test-roster.yml` run after push.

**Done when:** both `Tests:` bullets pass and the guide sentence is present.

### T2: Typed reports through the generic path

**Depends on:** none

**Touches:** packs/core/tests/skills/work-loop/test_preservation_review.py

**Mode:** goal-based.

**Tests:**
- AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016 in `test_preservation_review.py`, loading
  `_review_contracts`, `_review_selection`, `_review_persistence`,
  `_review_assessment`, `_review_bridge`, `_evidence_store`, `_acceptance`,
  `_subject_source`, `_loop_guards`, and `_security_capability` by path under
  pack-and-skill-qualified names.
- AC-0021 as an `import` scan over the new modules.

**Done when:** the module passes.

### T3: Reviewer eval cases

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-loop/evals/evals.json, packs/core/.apm/skills/work-loop/evals/files/preservation-review/*, packs/core/tests/skills/work-loop/test_preservation_review_eval.py

**Mode:** TDD. The construction pins fail while the cases are absent.

**Tests:**
- AC-0017 in `test_preservation_review_eval.py`.
- `test_repository_grounding_eval.py` and `test_step0_eval_contract.py` pass.

**Done when:** both `Tests:` bullets pass.

### T4: Release, projection, and registration

**Depends on:** T1, T2, T3

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.d/*, docs/product/briefs/repository-grounding-preservation.md, workspace.toml, .agents/**, .claude/**

**Mode:** goal-based.

**Tests:**
- AC-0018, AC-0019, AC-0020, AC-0023, and AC-0024 commands.
- `agentbundle catalogue self-host --root . --write --force` leaves no diff on
  re-run.
- `make lint-ruff lint-mypy` is clean.

**Done when:** every `Tests:` bullet passes.

### T5: Graded runs against the rebuilt and base projections

**Depends on:** T4

**Touches:** docs/specs/grounding-preservation-review/notes/verification-ledger.md

**Mode:** visual / manual QA of the rebuilt agent artifacts.

**Tests:**
- AC-0022's five graded runs, and one baseline graded run per case against the
  base revision's projection, recorded in `notes/verification-ledger.md`. The
  base projection has no reviewer eval cases, so their baselines run the same
  prompt and files against the base reviewer definitions.

**Done when:** the ledger records all ten runs, each with the pack version it
ran against, and every AC-0022 run holds all its assertions.

## Changelog

none
