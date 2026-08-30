# Plan: Agent Skill Engineering Languages and Execution

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `docs/rfc/0097-agent-skill-engineering.md` D3 and its
  shared language contracts; `docs/rfc/0097-notes/practice-inventory.md` and
  `docs/rfc/0097-notes/execution-economics-archaeology.md` for the doctrine
  evidence base; `docs/specs/agent-skill-engineering-corpus/` for the
  prerequisite admission, topology, and retrieval baseline, and its `qa.md` for
  the recorded misses, pin re-take record, and circular-derivation history this
  slice must not repeat.

## Approach

1. Close the doctrine-side parity gap the corpus slice left as a deliberate
   loud failure, before any doctrine group exists to trip it.
2. Assemble the doctrine evidence for the five leaves from the governing RFC
   notes, then author the topic bodies and admission record together so no body
   ships a claim its record does not carry.
3. Reconcile every shipped statement about language-family availability with
   what the corpus now holds.
4. Regenerate the governed projections through the owning compiler.
5. Re-measure retrieval and behavior evidence in contexts held apart from
   authoring, because admitting a topic moves every digest those records pin.
6. Reconcile the registry surfaces the change touches.

**Status and brief handling.** The spec moves to `Implementing` before the first
source edit and to `Shipped` at the finish checklist. Each move rewrites the
brief's derived Spec-map row, which moves the brief's sha256; that digest is
`source.revision` in **two** `workspace.toml` registrations, so both are re-pinned
in the same step as the roll. This happens twice, once per status move.

## Tasks

### T1: Enforce doctrine-side source parity

**Depends on:** none

Replace the corpus slice's unconditional `AssertionError` in
`test_shipped_body_matches_the_admission_record` with the check that failure
describes: every cited source's `identity` and `retrieved_at` appears in both the
authored and the compiled projection of the citing topic. Drive the predicate
from constructed inputs as well as the shipped record, so the doctrine arm is
exercised before a real doctrine group exists and its first exercise is not also
its first shipment.

**Tests:**
- `test_doctrine_group_source_parity_holds_in_both_projections` (AC6) — stub: true
- `test_doctrine_parity_rejects_a_source_missing_from_one_projection` (AC6) — stub: true
- Mutation proof per newly reached limb of the `doctrine` arm: promotion-class
  membership, `two-runtime-public-contract` clause equality, the
  `repeated-observed-failures` shared-mechanism check, the
  `controlled-measurement` repetition floor, and source attributability.

### T2: Admit the five leaves as doctrine

**Depends on:** T1

Author the five topic bodies and their admission-record entries together. Each
claim group declares a promotion class the inherited predicate admits and cites
sources that name themselves, when they were read, and their version state. Remove
the five leaves from the declared-unpopulated register in the same change, so the
partition never names a leaf twice or not at all. The TypeScript/Node topic records
the maturity limit `practice-inventory.md:139` states.

**Tests:**
- `test_every_claim_group_declares_a_basis_and_its_fields` (AC1, AC3) — first
  execution of its `doctrine` arm against real input
- `test_every_leaf_is_in_exactly_one_set` (AC1)
- `test_admitted_topics_are_topology_leaves` (AC1)
- `test_foundation_corpus_is_exactly_the_admitted_inert_governed_topics` (AC1)
- `test_each_foundation_topic_carries_its_required_sections` (AC2, AC3)
- `test_every_agent_read_concept_is_inert` (AC2, AC3)

### T3: Reconcile shipped language-availability statements

**Depends on:** T2

The shipped language-extension seam tells adopters that neither language family
has a topic body, and an integration test pins that sentence. Both become false
when the language topics ship. Restate availability per family against the
admitted set and retarget the test to that reconciliation.

**Tests:**
- `test_language_extension_families_are_distinct_and_unpopulated`, retargeted to
  assert agreement between the shipped availability statement and the admitted
  topic set (AC7)

### T4: Regenerate the governed corpus

**Depends on:** T3

Regenerate through the owning compiler; hand-edit no projection.

**Tests:**
- `test_generated_manifest_owns_only_router_outputs` (AC1) — goal-based
- `test_generated_concept_index_routes_to_every_topic` (AC1)
- `test_generated_router_is_inert_bounded_and_source_independent` (AC2)
- Done when: the compiler's `--check` mode reports no drift on a second run.

### T5: Re-measure retrieval and the generic negatives

**Depends on:** T4

Predeclare at least two solo retrieval cases per newly admitted topic, then measure
in a context held apart from authoring. Both the retrieval record and the
generic-negative record are bound to the digest triple this slice moved, so both
are re-measured. The 24 inherited foundation pins are a non-regression gate: a
moved pin is surfaced, never rewritten.

**Tests:**
- `test_foundation_router_cases_are_predeclared_bounded_and_include_near_misses` (AC4)
- `test_independent_router_results_meet_precision_and_recall_gate` (AC4)
- `test_foundation_pins_hold_the_shipped_cases` (AC4)
- `test_admitted_topics_are_measurably_distinguishable` (AC1, AC4)
- `test_generic_negative_record_is_attributable_to_the_tree_it_measured` (AC4)
- `test_corpus_does_not_answer_generic_engineering_requests` (AC4)

### T6: Record the pytest-suite and Node/browser behavior fixtures

**Depends on:** T4

Declare both cases alongside the other representative task fixtures RFC-0097's M2
measure names, then grade them. Adding them moves the whole-file digest that every
existing graded result in that file pins, so those results are re-measured rather
than re-stamped. Execution, attestation, and authoring stay in separate contexts.
Declare no output marker the skill does not instruct: that circularity has been
found and removed three times in this pack already.

**Tests:**
- The author-skill contract suite's behavior assertions, including the recorded
  per-`(case, index)` known-miss exemptions (AC5)
- Every declared marker appears in captured output from a blind run (AC5)

### T7: Reconcile the registry surfaces

**Depends on:** T5, T6

Roll the pack version under the pack version-bump rule, correct the INI-009
milestone descriptor now that the corpus has shipped and this slice is in flight,
and restore the `unsatisfied_dependency` ceiling to 8 now that the 2b-to-2a edge
this slice inherited has cleared.

**Tests:**
- `tests/roster/test_workspace_status_projection.py` at a ceiling of 8 (AC1)
- Brief-coverage lint, catalogue verify, and projection parity — goal-based

## Risks

| Risk | Mitigation |
| --- | --- |
| A language claim becomes generic developer guidance | Limit every topic and retrieval case to skills, evaluations, packs, or their execution environments. |
| New topics move a foundation result | Treat the inherited 24 per-case pins as a hard non-regression gate; surface a moved pin rather than re-pinning it. |
| The TypeScript/Node topic fails retrieval distinctness | Its governing note already withholds maturity, and the corpus has withdrawn a leaf for exactly this reason before. Report the measurement and withdraw the topic rather than reword cases after seeing results. |
| The doctrine arm ships on its first execution | T1 exercises it from constructed inputs and mutation-proves each limb before T2 admits a real group. |
| A recorded measurement is re-stamped instead of re-taken | Every digest-bound record whose covered content moved is re-measured; the digest is never edited onto an older observation. |
| A run the harness calls unreliable is recorded | Discard and re-run; an unreliable run is not a measurement. |
