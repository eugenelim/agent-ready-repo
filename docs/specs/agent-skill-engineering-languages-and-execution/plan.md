# Plan: Agent Skill Engineering Languages and Execution

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `docs/rfc/0097-agent-skill-engineering.md` D3 and its
  shared language contracts; `docs/rfc/0097-notes/practice-inventory.md` and
  `docs/rfc/0097-notes/execution-economics-archaeology.md` for the doctrine
  evidence base and its external-validation links;
  `docs/specs/agent-skill-engineering-corpus/` for the prerequisite admission,
  topology, and retrieval baseline, and its `qa.md` for the recorded misses, pin
  re-take record, and circular-derivation history this slice must not repeat.
- **Review shape:** DEEP. The change spans corpus content, an admission
  predicate, four independent measurement rounds, and a records layer, so it is
  decomposed into the dependency-ordered tasks below, each independently
  reviewable and each leaving the repository working.

## Approach

1. Roll status and registration together, because rolling one without the other
   trips a ratchet that is already at its ceiling.
2. Close the doctrine-side parity gap the corpus slice left as a deliberate loud
   failure, before any doctrine group exists to trip it.
3. Assemble doctrine evidence from public documented contracts and author the
   topic bodies and admission record together, so no body ships a claim its
   record does not carry.
4. Reconcile every shipped statement about language-family availability.
5. Regenerate the governed projections through the owning compiler.
6. Re-measure, in contexts held apart from authoring, everything whose pinned
   digest this slice moved: activation, retrieval, the generic negatives, and
   the graded authoring behavior results.
7. Reconcile the records and published surfaces.

**Promotion class per leaf.** Every group uses `two-runtime-public-contract`,
because `controlled-measurement` is unreachable here: it requires at least two
repetitions and every row of the archaeology note is a single dated decision.
Each group names one clause and at least two runtimes whose public documentation
states that same clause. Candidate sources are the note's external-validation
links; T3 confirms each against the source before citing it, and a leaf whose
two-runtime clause cannot be evidenced returns to the register rather than
lowering the rule.

## Tasks

### T1: Roll status and registration together

**Depends on:** none

Set the spec to `Implementing`, move its `workspace.toml` registration from
`["ini-009".work].queue` to `.active`, roll the brief's derived Spec-map row, and
re-pin the brief digest in **both** registrations that carry it — all in one
commit. Rolling the status while the entry stays in `queue` emits
`impossible_transition`, whose tolerated count is already at its ceiling of 2.

**Tests:**
- `tests/roster/test_workspace_status_projection.py` (AC8) — no stub (goal-based)
- `lint-brief-coverage.py --root .` (AC8) — no stub (goal-based)

**Done when:** the roster suite is green with `impossible_transition` no higher
than 2, and brief-coverage exits 0.

### T2: Enforce doctrine-side source parity

**Depends on:** T1

Replace the corpus slice's unconditional `AssertionError` in
`test_shipped_body_matches_the_admission_record` with the check that failure
describes: for a doctrine group, the group's shipped fields appear in the
topic's provenance-and-lifecycle section and equal the record field-for-field —
source identities and dates, including each source's exposed version or its
explicit `none exposed`. Bound the projected identity to an externally
resolvable form, and extend the pack's repository-only patterns with a
bare-commit-SHA form, since the existing patterns catch a `docs/rfc/` path but
not a bare hash. Drive the predicate from constructed inputs as well as the
shipped record, so the doctrine arm is exercised before a real doctrine group
exists and its first exercise is not also its first shipment.

**Tests:**
- `test_doctrine_group_source_parity_holds_in_both_projections` (AC6) — stub: true
- `test_doctrine_parity_rejects_a_source_missing_from_one_projection` (AC6) — stub: true
- `test_doctrine_parity_rejects_a_repository_internal_source_identity` (AC6) — stub: true
- Mutation proof per newly reached limb of the `doctrine` arm: promotion-class
  membership, `two-runtime-public-contract` clause equality, the
  `repeated-observed-failures` shared-mechanism check, the
  `controlled-measurement` repetition floor, and source attributability.
- Mutation proof for the two reviewer-identity assertions this same function
  already carries, which the rewrite must not narrow to one basis: the
  role-or-placeholder scan over both projections, and the recorded `reviewer`
  value over both projections.

**Done when:** each listed mutation is applied, the named test fails, and the
tree is restored by editing rather than by checkout.

### T3: Admit the five leaves as doctrine

**Depends on:** T2

Author the five topic bodies and their admission-record entries together, each
with a `two-runtime-public-contract` group whose clause is confirmed against
both cited sources. Remove the five leaves from the declared-unpopulated register
in the same change. The TypeScript/Node topic covers its seven RFC-assigned
subjects and states its maturity limit in portable terms; the note recording that
limit may not itself be cited in shipped content.

Admission opens five hardcoded enumerations that are deliberate anti-vacuity
floors, so each is widened knowingly, not incidentally: `EXPECTED_TOPICS` and
`TOPIC_FILES` in `test_foundation_corpus.py`, and in
`author_or_update/test_contract.py` the six-id set, the eight-id set, and
`AUTHORING_EVAL_IDS`. Bind `TOPIC_FILES` to `EXPECTED_TOPICS` rather than
maintaining two independent literals, so section coverage is enumerated over
exactly the admitted set.

**Tests:**
- `test_every_leaf_is_in_exactly_one_set` (AC1)
- `test_admitted_topics_are_topology_leaves` (AC1)
- `test_foundation_corpus_is_exactly_the_admitted_inert_governed_topics` (AC1)
- `test_every_agent_read_concept_is_inert` (AC1)
- `test_every_claim_group_declares_a_basis_and_its_fields` (AC6) — first
  execution of its `doctrine` arm against real input
- `test_each_foundation_topic_carries_its_required_sections`, over a
  `TOPIC_FILES` now derived from `EXPECTED_TOPICS` (AC2) — stub: true
- `test_typescript_node_topic_covers_its_seven_assigned_subjects` (AC2) — stub: true
- `test_typescript_node_maturity_limit_appears_in_both_projections` (AC2) — stub: true
- `test_related_topics_references_resolve_to_admitted_topics` (AC1) — stub: true
- `test_recorded_evidence_fields_carry_no_host_identifying_data` (AC3) — stub: true

**Done when:** the pack suite is green with twelve admitted topics and
twenty-four register entries, and each new test fails when its subject is removed.

### T4: Reconcile shipped language-availability statements

**Depends on:** T3

Four shipped statements assert these families are unpopulated or future, and all
four become false: `author-or-update-agent-skill/SKILL.md`,
`review-or-optimize-agent-skill/SKILL.md`, the language-extension seam
reference, and the pack README. Restate availability per family against the
admitted set and retarget the integration assertion to that reconciliation.

**Tests:**
- `test_language_extension_families_are_distinct_and_unpopulated`, retargeted to
  assert agreement between the shipped availability statements and the admitted
  topic set (AC7) — stub: true

**Done when:** no shipped file asserts an absence the corpus no longer has, and
the retargeted test fails when any one of the four statements is reverted.

### T5: Regenerate the governed corpus

**Depends on:** T4

Regenerate through the owning compiler; hand-edit no projection.

**Tests:**
- `test_generated_manifest_owns_only_router_outputs` (AC1) — no stub (goal-based)
- `test_generated_concept_index_routes_to_every_topic` (AC1)
- `test_generated_router_is_inert_bounded_and_source_independent` (AC1)

**Done when:** the compiler's `--check` mode reports `OKF000 check clean` on a
second run, and projection parity is green.

### T6: Re-observe activation

**Depends on:** T5

T4 edits both workflow `SKILL.md` bodies, and each body's bytes are pinned in
the activation record. That record cannot be reconciled by editing; it needs a
fresh headless observation. Take one, and discard rather than record any run the
harness reports as unreliable.

**Tests:**
- `test_independent_activation_results_bind_all_queries_and_descriptions` (AC7)

**Done when:** a headless run reports every query classified as expected with
zero errored runs and zero exclusivity violations, against the current digests.

### T7: Re-measure retrieval and the generic negatives

**Depends on:** T5

Predeclare solo retrieval cases for each newly admitted topic with margin above
the two-exclusive-result floor, and predeclare near-miss cases for the adjacent
pairs most likely to collide. Measure in a context held apart from authoring.
Both the retrieval record and the generic-negative record are bound to the digest
triple this slice moved, so both are re-measured. The inherited foundation pins
are a non-regression gate: a moved pin is surfaced, never rewritten.

**Tests:**
- `test_foundation_router_cases_are_predeclared_bounded_and_include_near_misses` (AC4)
- `test_independent_router_results_meet_precision_and_recall_gate` (AC4)
- `test_foundation_pins_hold_the_shipped_cases` (AC4)
- `test_admitted_topics_are_measurably_distinguishable` (AC1, AC4)
- `test_generic_negative_record_is_attributable_to_the_tree_it_measured` (AC4)
- `test_corpus_does_not_answer_generic_engineering_requests` (AC4)

**Done when:** every inherited pin reproduces, each admitted topic has at least
two exclusive measured results, and the negative set stays within its bar.

### T8: Record the pytest-suite and Node/browser behavior fixtures

**Depends on:** T5

Declare both cases alongside the other representative task fixtures RFC-0097's M2
measure names, then grade them. Adding them moves the whole-file digest that every
existing graded result in that file pins, so those results are re-measured rather
than re-stamped. Execution, attestation, and authoring stay in separate contexts.
Declare no output marker the skill does not instruct: that circularity has been
found and removed three times in this pack already. A newly observed miss is
recorded as measured; the existing known-miss exemption set is not extended to
absorb one, and adding an exemption needs owner authority.

**Tests:**
- The author-skill contract suite's behavior assertions (AC5)
- Every declared marker appears in captured output from a blind run (AC5)

**Done when:** eight graded authoring results are recorded against the current
`evals.json` digest, with any miss recorded as measured rather than exempted.

### T9: Reconcile records and published surfaces

**Depends on:** T6, T7, T8

Roll the pack version under the pack version-bump rule with its changelog entry,
update the architecture record and the spec index, correct the INI-009 milestone
descriptor, and restore the `unsatisfied_dependency` ceiling to 8 — removing the
five-line rationale comment that explains the raise to 9, which becomes false
with the value it describes.

**Tests:**
- `tests/roster/test_workspace_status_projection.py` at a ceiling of 8 (AC8)
- Brief-coverage lint, catalogue verify, deep lint, and projection parity (AC8)
  — no stub (goal-based)

**Done when:** both manifests carry the same bumped version, the changelog entry
is topmost for the pack, and the roster suite is green at the restored ceiling.

## Risks

| Risk | Mitigation |
| --- | --- |
| A language claim becomes generic developer guidance | Limit every topic and retrieval case to skills, evaluations, packs, or their execution environments. |
| New topics move a foundation result | Treat the inherited per-case pins as a hard non-regression gate; surface a moved pin rather than re-pinning it. |
| The TypeScript/Node topic fails retrieval distinctness | Its governing note already withholds maturity, and the corpus has withdrawn a leaf for exactly this reason before. Report the measurement and withdraw the topic rather than reword cases after seeing results. |
| The re-measured generic-negative set exceeds its bar | Five prompts in the fixed set sit directly on the new subjects — a CI job running unit tests, a flaky integration test, parallelising across workers, and a dependency vulnerability audit. If the bar is exceeded, withdraw the topic whose routing answered them and report the measurement; do not reword a negative prompt. |
| A two-runtime clause turns out to rest on one runtime | Confirm each clause against both cited sources before admission; return the leaf to the register rather than weakening the class. |
| The doctrine arm ships on its first execution | T2 exercises it from constructed inputs and mutation-proves each limb, including the two reviewer-identity assertions it must not narrow. |
| A recorded measurement is re-stamped instead of re-taken | Every digest-bound record whose covered content moved is re-measured; the digest is never edited onto an older observation. |
| A run the harness calls unreliable is recorded | Discard and re-run; an unreliable run is not a measurement. |
