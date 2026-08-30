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
3. Assemble doctrine evidence — public documented contracts for three leaves,
   paired internal failures for two — and author the topic bodies and admission
   record together, so no body ships a claim its record does not carry.
4. Reconcile every shipped statement about language-family availability and
   topic count.
5. Regenerate the governed projections through the owning compiler.
6. Re-measure, in contexts held apart from authoring, everything whose pinned
   digest this slice moved: activation, retrieval, the generic negatives, and
   the graded authoring behavior results.
7. Reconcile the records and published surfaces, and close the status and
   registration rolls that T1 opened.

## Promotion class and evidence, per leaf

`controlled-measurement` is unreachable here: it requires at least two
repetitions and every row of the archaeology note is a single dated decision.
The two classes that are reachable are used, each where its evidence actually
lies.

Every clause below was verified against the live published documentation on
**2026-08-30**. An earlier draft of this table asserted five clauses from
recollection and **all five were refuted** — one of them, "runner parallelism is
not implied by host CPU count", is contradicted by Playwright's documented
default of 50% of logical cores. The clauses here are the narrowed forms both
sources independently support.

### Public-contract groups

`two-runtime-public-contract`, one clause stated by two independently governed
projects, cited externally so parity projects a resolvable reference.

| Leaf | Clause both sources state | Source A | Source B |
| --- | --- | --- | --- |
| `python-and-pytest` | Test discovery and importability depend on the configured discovery root and the test directory's Python-package layout. | pytest, `docs.pytest.org` (no version exposed) | CPython `unittest` discovery, `docs.python.org` (3.14.7) |
| `typescript-node-and-javascript-test-runners` | Each runner provides runner-specific controls for limiting test parallelism. | Node.js core test runner, `nodejs.org` (v26.8.1) | Playwright, `playwright.dev` (no version exposed) |
| `pack-and-ci-critical-paths` | Both systems provide explicit syntax for job dependencies and for cache keys, including optional file-content-derived cache keys. | GitHub Actions, `docs.github.com` (no version exposed) | GitLab CI, `docs.gitlab.com` (no version exposed) |

Each pair is two distinct projects under separate governance, and neither member
requires the other to run. Where a source exposes no version, the record carries
`none exposed` with the retrieval date, which is the shape the inherited
attributability rule specifies.

### Repeated-failure groups

`repeated-observed-failures`, at least two observed failures sharing one
mechanism. This class needs no external source, so these groups cite none and
keep their evidence in the non-projected admission fixture — shipped content may
not cite this repository's own records. Both were sourced from the archaeology
note's chronology rather than from documentation, which is why the two leaves
whose clauses could not be evidenced externally are admissible at all.

| Leaf | Shared mechanism | The two failures |
| --- | --- | --- |
| `process-and-filesystem-cost` | Per-item process spawning was treated as free, so cost was tuned before it was counted. | A lint path spawning roughly 37,000 shell processes; 337 repeated single-item subprocess queries later batched into one. |
| `worktrees-state-locks-and-shared-host-admission` | Separation at one layer was mistaken for isolation at another. | An atomic final write that did not protect a read/decide/write transition; directory-separated worktrees that still shared temp, cache, port, and state ownership. |

T3 confirms each group against its evidence before authoring the body, and a
group whose evidence does not hold is surfaced with that finding and routed
through an approved spec amendment — never withdrawn in flight, because the ship
transition requires every criterion checked.

Note for T3 authoring: Playwright's CPU-derived default is itself material for
the TypeScript/Node topic's browser-worker-economics subject, so the refuted
clause becomes body content rather than being discarded.

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
explicit `none exposed`. Add the three limbs the criterion needs and the tests
alone would not give: a floor of at least one attributable source for a group
whose class rests on public documentation, so that externality claim cannot be
satisfied by citing nothing; a checkable identity form; and the converse
direction, so a body cannot carry an external reference its record never cited.

The floor is scoped by class deliberately. A `repeated-observed-failures` group
carries internal evidence and must cite no external source — requiring one would
push this repository's own records into shipped content, which the pack rules
forbid. So the check reads the promotion class first and applies the source floor
only to the class that makes an externality claim.

The repository-internal scan runs over **both** concept roots — the authored
`okf/.../concepts/` tree and the compiled `.apm/` tree — since the existing
portable-file walk reaches only the second. Extend its patterns with a
bare-commit-SHA form and with the `\b(?:ADR|RFC)-\d{2,4}\b` governance-token
form the guides linter already treats as repository-only.

Drive the predicate from constructed inputs as well as the shipped record, so the
doctrine arm is exercised before a real doctrine group exists and its first
exercise is not also its first shipment.

**Tests:**
- `test_doctrine_group_source_parity_holds_in_both_projections` (AC6) — stub: true
- `test_doctrine_parity_rejects_a_source_missing_from_one_projection` (AC6) — stub: true
- `test_public_contract_group_cites_at_least_one_attributable_source` (AC6) — stub: true
- `test_repeated_failure_group_cites_no_external_source` (AC6) — stub: true
- `test_body_carries_no_external_reference_the_record_does_not_cite` (AC6) — stub: true
- `test_doctrine_parity_rejects_a_repository_internal_source_identity`, over both
  concept roots (AC6) — stub: true
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
with a `two-runtime-public-contract` group whose clause is confirmed against both
cited sources from the table above. Remove the five leaves from the
declared-unpopulated register in the same change. The TypeScript/Node topic
covers its seven RFC-assigned subjects and states its maturity limit in portable
terms; the note recording that limit may not itself be cited in shipped content.

Admission opens two hardcoded enumerations that are deliberate anti-vacuity
floors, so both are widened knowingly: `EXPECTED_TOPICS` and `TOPIC_FILES` in
`test_foundation_corpus.py`. Replace the two independent literals with the
glob-and-index-by-stem form this pack already uses for exactly this problem,
which keeps the read statically confined without maintaining a second list, and
update the in-file comment that explains why the literal existed.

**Tests:**
- `test_every_leaf_is_in_exactly_one_set` (AC1)
- `test_admitted_topics_are_topology_leaves` (AC1)
- `test_foundation_corpus_is_exactly_the_admitted_inert_governed_topics` (AC1)
- `test_every_agent_read_concept_is_inert` (AC1)
- `test_every_claim_group_declares_a_basis_and_its_fields` (AC6) — first
  execution of its `doctrine` arm against real input
- `test_each_foundation_topic_carries_its_required_sections`, enumerated over the
  admitted set rather than a parallel literal (AC2) — stub: true
- `test_typescript_node_topic_covers_its_seven_assigned_subjects` (AC2) — stub: true
- `test_typescript_node_maturity_limit_appears_in_both_projections` (AC2) — stub: true
- `test_related_topics_references_resolve_to_admitted_topics` (AC1) — stub: true
- `test_recorded_evidence_fields_carry_no_host_identifying_data`, over the
  admission record (AC3) — stub: true

**Done when:** the pack suite is green with twelve admitted topics and
twenty-four register entries, and each new test fails when its subject is removed.

### T4: Reconcile shipped language-availability statements

**Depends on:** T3

Five shipped sentences become false: the availability statements in
`author-or-update-agent-skill/SKILL.md`, `review-or-optimize-agent-skill/SKILL.md`,
and the language-extension seam reference, plus both the language-availability
paragraph and the topic-count sentence in the pack README. Restate each against
the admitted set and retarget the integration assertion to that reconciliation.

**Tests:**
- `test_language_extension_families_are_distinct_and_unpopulated`, retargeted to
  assert agreement between every shipped availability-or-count statement and the
  admitted topic set (AC7) — stub: true

**Done when:** no shipped file states a topic count or asserts an absence the
corpus no longer has, and the retargeted test fails when any one of the five
sentences is reverted.

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
- `test_admitted_topics_are_measurably_distinguishable` (AC1, AC2, AC4) — the
  only artifact that falsifies AC2's non-collapse conjunct
- `test_generic_negative_record_is_attributable_to_the_tree_it_measured` (AC4)
- `test_corpus_does_not_answer_generic_engineering_requests` (AC3, AC4) — the
  only artifact that falsifies AC3's domain-bounding conjunct
- `test_recorded_evidence_fields_carry_no_host_identifying_data`, extended over
  the retrieval and near-miss cases this task writes (AC3)

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

The new fixtures — not admission — open three author-skill enumerations, each
widened here rather than in T3: the six-id eval-set equality, the eight-id
behavior-result-set equality, and `AUTHORING_EVAL_IDS`. If a payload ships in a
suffix the export-boundary content scan does not cover, extend that scan's
covered suffixes with each suffix introduced and re-anchor its file floor, so no
shipped payload goes unread.

**Tests:**
- The author-skill contract suite's behavior assertions (AC5)
- Every declared marker appears in captured output from a blind run (AC5)
- `test_shipped_content_names_no_repository_only_reference`, over a scan whose
  suffix set and floor cover every added payload (AC5)
- `test_recorded_evidence_fields_carry_no_host_identifying_data`, extended over
  the eval declarations and their fixture payloads (AC3)

**Done when:** eight graded authoring results are recorded against the current
`evals.json` digest, with any miss recorded as measured rather than exempted, and
every shipped payload falls inside the export-boundary scan.

### T9: Close the records, registration, and status rolls

**Depends on:** T6, T7, T8

Roll the pack version under the pack version-bump rule with its changelog entry,
update the architecture record and the spec index, correct the INI-009 milestone
descriptor, and restore the `unsatisfied_dependency` ceiling to 8 — removing the
five-line rationale comment that explains the raise to 9, which becomes false
with the value it describes.

Then close the pair T1 opened: set the spec to `Shipped`, move its registration
from `["ini-009".work].active` to `.shipped`, and re-pin the brief digest in both
registrations a second time, in the same commit that sets the status. A
`work.shipped` entry whose spec does not read `Shipped` emits
`impossible_transition`, and leaving the spec at `Implementing` in `work.active`
would leave AC8 undischarged with every gate green.

**Tests:**
- `tests/roster/test_workspace_status_projection.py` at a ceiling of 8 (AC8)
- Brief-coverage lint, catalogue verify, deep lint, and projection parity (AC8)
  — no stub (goal-based)

**Done when:** both authored manifests carry the same bumped version, the
changelog entry is topmost for the pack, the spec reads `Shipped` in
`work.shipped` with both digests re-pinned, and the roster suite is green at the
restored ceiling.

## Risks

| Risk | Mitigation |
| --- | --- |
| A language claim becomes generic developer guidance | Limit every topic and retrieval case to skills, evaluations, packs, or their execution environments; the generic-negative gate is the falsifier. |
| New topics move a foundation result | Treat the inherited per-case pins as a hard non-regression gate; surface a moved pin rather than re-pinning it. |
| A leaf's clause cannot be evidenced from two distinct projects | Confirm each clause against both sources before admission. Surface the finding with its evidence and route it through an approved spec amendment; do not withdraw a leaf in flight, because the ship transition requires every criterion checked. |
| The TypeScript/Node topic fails retrieval distinctness | Its governing note already withholds maturity, and the corpus has withdrawn a leaf for this reason before. Report the measurement and route through the amendment path above rather than rewording cases after seeing results. |
| The re-measured generic-negative set exceeds its bar | Five prompts in the fixed set sit directly on the new subjects: a CI job running unit tests, writing unit tests for a calculator, a flaky integration test, parallelising across worker processes, and a dependency vulnerability audit. If the bar is exceeded, report the measurement and route the offending topic through the amendment path; do not reword a negative prompt. |
| The doctrine arm ships on its first execution | T2 exercises it from constructed inputs and mutation-proves each limb, including the two reviewer-identity assertions it must not narrow. |
| A recorded measurement is re-stamped instead of re-taken | Every digest-bound record whose covered content moved is re-measured; the digest is never edited onto an older observation. |
| A run the harness calls unreliable is recorded | Discard and re-run; an unreliable run is not a measurement. |
