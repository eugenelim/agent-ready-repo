# Plan: Agent Skill Engineering Languages and Execution

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `docs/rfc/0097-agent-skill-engineering.md` D3 and its
  shared language contracts; `docs/rfc/0097-notes/practice-inventory.md` and
  `docs/rfc/0097-notes/execution-economics-archaeology.md` for the doctrine
  evidence base and its external-validation links;
  `docs/specs/agent-skill-engineering-corpus/` for the prerequisite admission,
  topology, and retrieval baseline, and its `qa.md` for the recorded misses,
  pin re-take record, and circular-derivation history this slice must not
  repeat.
- **Review shape:** DEEP. The change spans corpus content, an admission
  predicate, four independent measurement rounds, and a records layer, so it is
  decomposed into the dependency-ordered tasks below, each independently
  reviewable and each leaving the repository working.

## Approach

1. Roll status and registration together, because rolling one without the other
   trips a ratchet that is already at its ceiling.
2. Close the doctrine-side parity gap the corpus slice left as a deliberate
   loud failure, before any doctrine group exists to trip it.
3. Assemble doctrine evidence per claim group, per the class tables below, and
   author the topic bodies and admission record together, so no body ships a
   doctrinal claim its record does not carry.
4. Reconcile every shipped statement about language-family availability and
   topic count.
5. Regenerate the governed projections through the owning compiler.
6. Re-measure, in contexts held apart from authoring, everything whose pinned
   digest this slice moved: activation, retrieval, the generic negatives, and
   the graded authoring behavior results.
7. Reconcile the records and published surfaces, and close the status and
   registration rolls that T1 opened.

## Promotion class and evidence, per claim group

Evidence is recorded per **claim group**, not per leaf. A group's clause
governs that group's claims, so one clause cannot stand behind a whole
multi-subject topic — the inherited schema takes `claim_groups` as a list
precisely for this. Where a topic makes two distinct doctrinal claims, it
carries two groups.

Two of the four inherited classes are used. `controlled-measurement` is
unreachable (it needs two repetitions; every archaeology row is one dated
decision) and `severe-safety-failure` is unused, so **no group in this slice
declares either**, and T2 carries no mutation proof for them. A third class,
`single-ecosystem-contract`, is added under owner authority recorded in the
spec's Assumptions.

Every clause below was checked against the live published documentation on
2026-08-30. Two verification passes ran: the first refuted all five clauses an
earlier draft had asserted from recollection, and the second refuted all three
drafted to fill the gaps that first pass opened. Eight of eight asserted
clauses failed, so nothing here is cited on recollection — each clause is the
narrowed form its sources were observed to state, and the groups whose clauses
could not be evidenced were dropped rather than reworded into something the
sources do not say.

### Single-ecosystem groups

`single-ecosystem-contract` — the governing RFC's scoped exception for a
language-specific topic, and admissible only for such a topic: it is the
cheapest class by evidence cost, so without that limit it becomes the default
escape from the two-runtime requirement. Required fields: the clause it
licenses, the ecosystem, the authoritative documentation the clause comes from,
the explicit version range the claim is limited to, and the construction or
behavior fixture that exercises it. A group in this class is never generalized
into the portable floor, and the topic body states its
ecosystem-and-version-range limit.

| Topic | Clause | Ecosystem sources | Version range | Fixture |
| --- | --- | --- | --- | --- |
| `python-and-pytest` | Test discovery and importability depend on the configured discovery root and the test directory's Python-package layout. | pytest, `https://docs.pytest.org/en/stable/explanation/pythonpath.html`; CPython `unittest`, `https://docs.python.org/3/library/unittest.html`; plus `https://docs.python.org/3/library/tempfile.html` for the temporary-path subject the body covers | pytest >= 9.1.1, upper bound open; CPython >= 3.14.7, upper bound open | T8 pytest-suite |
| `typescript-node-…` | Each runner provides runner-specific controls for limiting test parallelism. | Node.js test runner, `https://nodejs.org/api/test.html`; Playwright, `https://playwright.dev/docs/test-parallel`; plus `https://nodejs.org/api/packages.html`, `https://nodejs.org/api/child_process.html`, and `https://docs.npmjs.com/cli/v11/commands/npm-ci/` for the package, child-process, and clean-install subjects the body covers | Node.js >= 26.8.1, upper bound open; Playwright >= 1.62, upper bound open | T8 Node/browser suite |

Each topic carries **one** such group. A second group was drafted for each and
both were dropped when verification refuted them: `tempfile` documents context
and object lifetime, not runner-managed per-test lifetime, so pytest's
end-of-test cleanup has no second source; and Node's manifest-interpretation
statement and npm's lockfile-validated install are two different statements
rather than one clause both make.

The remaining RFC-assigned subjects are covered descriptively in the body, not
as further doctrinal claims — coverage is what the criterion requires, and a
subject with no shared contract behind it must not be dressed as one.
Descriptive coverage still needs provenance, so every source the body relies on
is recorded in the group even when it does not carry the group's clause; the
group's clause is what the class licenses, and the wider source list is what
the body may cite without tripping the converse parity limb. Playwright's
documented default of 50% of logical cores and npm's frozen-install behaviour
are body material of exactly this kind.

Version ranges are evidence-backed, not conventional: pytest's changelog states
Semantic Versioning at 9.1.1 (2026-06-19), Playwright's release notes give 1.62
and use explicit "vX and later" wording, and the Node and CPython documentation
each identify their own patch version.

### Two-vendor groups

`two-runtime-public-contract` — one clause stated by two independently governed
projects in different ecosystems.

| Topic | Group | Clause | Source A | Source B |
| --- | --- | --- | --- | --- |
| `pack-and-ci-critical-paths` | job dependencies | Job execution order is declared explicitly by naming prerequisite jobs. | GitHub Actions, `https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax` | GitLab CI, `https://docs.gitlab.com/ci/yaml/needs/` |
| `pack-and-ci-critical-paths` | cache keys | Cache reuse is controlled by an explicit key, which may be derived from file contents. | GitHub Actions, `https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching` | GitLab CI, `https://docs.gitlab.com/ci/caching/` |

This is two groups, not one, because the earlier single clause was a
conjunction: it asserted job dependencies **and** cache keys while the recorded
GitHub page covered only caching and the recorded GitLab page only `needs`. The
class requires each cited runtime to state the **whole** clause, so a
conjunction split across two pages records each vendor asserting half of
something it does not say. Each clause above was verified against each vendor
page individually on 2026-08-30; both returned `both-pages-state-it`, and
neither page exposes a version or last-updated date.

### Repeated-failure groups

`repeated-observed-failures` — at least two **independent** observed failures
sharing one mechanism. Independence is a reviewer judgment no harness can
check; it is recorded per group as distinct subsystems and distinct dates, and
never as an author, which the spec forbids in any recorded evidence field.
These groups cite no external source and keep their evidence in the
non-projected fixture.

| Topic | Shared mechanism | The two independent failures |
| --- | --- | --- |
| `process-and-filesystem-cost` | Per-item process spawning was treated as free. | A lint path spawning roughly 37,000 shell processes (2026-08-06); 337 repeated single-item subprocess queries later batched into one (2026-08-17). Distinct subsystems, eleven days apart. |
| `pack-and-ci-critical-paths` | Duplicated fixed setup and coordination overhead scales with the units it is repeated across, so adding units trades against the work they save. | A CI job split that cut the measured critical path from 430–450s to 185s and stopped when coordination dominated, where the repeated unit is the job (2026-08-17, `build-check.yml` and the catalogue gates, 406+ lines); one Node setup and cache step made to cover two npm projects instead of running twice inside one job, where the repeated unit is the setup step (2026-08-21, `pages.yml`, 24 lines). Different workflows serving different purposes — the build gate and the docs publish — four days and 95 pull requests apart. |
| `worktrees-state-locks-and-shared-host-admission` | A guarantee at one layer was mistaken for a stronger guarantee at another. | An atomic final write that did not protect a read/decide/write transition (2026-08-08 to 08-10); directory-separated worktrees that still shared temp, cache, port, and state ownership (2026-08-19 to 08-21). Distinct subsystems, nine days apart. |

Each mechanism is stated as the conjunct **both** its failures evidence. An
earlier wording carried a causal tail that only one row supported, which the
admission predicate would have forced the other failure to assert.

`pack-and-ci-critical-paths` is the one topic carrying two classes, and it does
so because its two verified public clauses cover declared dependencies and
cache keys respectively, and neither makes a critical-path claim, while the
topic is named for one. Verification found no vendor page stating a
longest-chain duration bound — that is a scheduling model neither GitHub nor
GitLab asserts — so the critical-path claim rests on paired internal failures
instead of being attributed to a contract no one published. This is also why
the converse parity limb is scoped to the group rather than the topic: the
repeated-failure group here must not borrow its sibling's citations.

A group whose evidence does not hold at T3 is surfaced with that finding and
routed through an approved spec amendment — never withdrawn in flight, because
the ship transition requires every criterion checked.

## Tasks

### T1: Roll status and registration together

**Depends on:** none

Set the spec to `Implementing`, move its `workspace.toml` registration from
`["ini-009".work].queue` to `.active`, correct the INI-009 milestone descriptor
so it names this slice rather than the shipped corpus, roll the brief's derived
Spec-map row, and re-pin the brief digest in **both** registrations that carry
it — all in one commit. The milestone edit belongs here, not at close: a
descriptor corrected in the commit that ships the slice names it as in flight
at the moment it stops being so. Rolling the status while the entry stays in
`queue` emits `impossible_transition`, whose tolerated count is already at its
ceiling of 2.

**Tests:**
- `tests/roster/test_workspace_status_projection.py` (AC8) — no stub
  (goal-based)
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
carries internal evidence and must cite no external source — requiring one
would push this repository's own records into shipped content, which the pack
rules forbid. So the check reads the promotion class first and applies the
source floor to the two classes that make an externality claim,
`two-runtime-public-contract` and `single-ecosystem-contract`, and not to the
one that does not.

The repository-internal scan runs over **both** concept roots — the authored
`okf/.../concepts/` tree and the compiled `.apm/` tree — since the existing
portable-file walk reaches only the second. Extend the repository-only pattern
set with a bare-commit-SHA form and with the `\b(?:ADR|RFC)-\d{2,4}\b`
governance-token form the guides linter already treats as repository-only, and
add the host-identifying forms AC3 names — absolute home path, username,
hostname, worktree name. One shared source of pattern strings serves all three
consumers, but it is **partitioned by obligation**, not shared flat: the
host-identifying forms bind every consumer, while the repository-only
*reference* forms bind only the projected trees. Binding the reference forms to
the de-identification check would fire it on the admission record, which is the
sanctioned home for exactly the commit hashes and governance tokens those
patterns match — a recorded fixture already carries a `docs/rfc/` reference the
inherited pattern matches — and the cheapest in-flight repair would be to
weaken the pattern set for all three consumers at once. Confirm before adopting
that the full widened set passes over the already-shipped tree, and that the
host-identifying forms alone pass over the recorded fixtures — the reference
forms must not be run against the fixtures, for the reason just given. The two
repeated-failure leaves take their whole basis from records whose native
identifiers are commit hashes and governance tokens, so this is the form most
likely to leak.

Add `single-ecosystem-contract` to the inherited `DOCTRINE_CLASSES` vocabulary
in this task. Its required-field tuple is the field list defined under
*Single-ecosystem groups* above, not a second list stated here. The per-class
assertions this task adds are: the version range carries an explicit lower and
upper bound; and the declaring topic is one the governing RFC classifies as
language-specific. Eligibility is asserted **against the topic**, never
recorded as a field — a group that declared its own eligibility would be
attesting to its own admissibility, which is vacuous. No other task owns this,
and T3 declares a group in the class, so without it T3's first doctrine-arm
execution fails on an unknown class and the governing RFC's three conditions go
unenforced.

Drive the predicate from constructed inputs as well as the shipped record, so
the doctrine arm is exercised before a real doctrine group exists and its first
exercise is not also its first shipment.

**Tests:**
- `test_doctrine_group_source_parity_holds_in_both_projections` (AC6) — stub:
  true
- `test_doctrine_parity_rejects_a_source_missing_from_one_projection` (AC6) —
  stub: true
- `test_public_contract_group_cites_at_least_one_attributable_source` (AC6) —
  stub: true
- `test_repeated_failure_group_cites_no_external_source` (AC6) — stub: true
- `test_each_doctrine_group_has_its_own_labelled_provenance_block` (AC6) — the
  partition every group-scoped check below depends on; labels come from the
  record's existing per-group `name`, in the bolded-label form the shipped
  bodies already use, and the rejection case is two groups sharing one block —
  stub: true
- `test_body_carries_no_external_reference_the_group_record_does_not_cite`
  (AC6) — group-scoped, not topic-scoped: a topic carrying both a citing and a
  non-citing group must not let the second borrow the first's URLs — stub: true
- `test_every_doctrine_group_projects_its_verification_date_and_trigger` (AC6)
  — the positive limb for a group that cites no source, using record fields
  that already exist — stub: true
- `test_doctrine_parity_rejects_a_repository_internal_source_identity`, over
  both concept roots (AC6) — stub: true
- Mutation proof per limb the doctrine arm actually reaches in this slice:
  promotion-class membership, `two-runtime-public-contract` clause equality,
  `single-ecosystem-contract`'s ecosystem/version-range/fixture fields, the
  `repeated-observed-failures` shared-mechanism check, and source
  attributability. No proof is carried for `controlled-measurement` or
  `severe-safety-failure`, which no group in this slice may declare.
- Mutation proof for the two reviewer-identity assertions this same function
  already carries, which the rewrite must not narrow to one basis: the
  role-or-placeholder scan over both projections, and the recorded `reviewer`
  value over both projections.

**Done when:** each listed mutation is applied, the named test fails, and the
tree is restored by editing rather than by checkout.

### T3: Admit the five leaves as doctrine

**Depends on:** T2

Author the five topic bodies and their admission-record entries together, each
group against the class its evidence satisfies: the two language topics carry
`single-ecosystem-contract` groups with their ecosystem, version range, and
bound behavior fixture; `pack-and-ci-critical-paths` carries
`two-runtime-public-contract` groups confirmed against both vendors; and the
two execution topics carry `repeated-observed-failures` groups whose mechanism
and paired independent failures are confirmed against the archaeology rows,
citing no source. Re-confirm each clause against its recorded sources at
authoring time; treat a clause that no longer reads as stated as a finding to
surface, not a wording to adjust. Remove the five leaves from the
declared-unpopulated register in the same change. The TypeScript/Node topic
covers its seven RFC-assigned subjects and states its maturity limit in
portable terms; the note recording that limit may not itself be cited in
shipped content.

Author each topic's `## Provenance and lifecycle` section with one labelled
block per declared claim group, labelled from that group's `name` in the
bolded-label form the shipped bodies already use. Without that partition the
group-scoped parity checks have no decidable subject, which is the whole reason
they are group-scoped.

Admission opens two hardcoded enumerations that are deliberate anti-vacuity
floors, so both are widened knowingly: `EXPECTED_TOPICS` and `TOPIC_FILES` in
`test_foundation_corpus.py`.

`TOPIC_FILES` may take the glob-and-index-by-stem form this pack already uses,
with its in-file comment updated. `EXPECTED_TOPICS` may **not**: it is compared
against a glob of the authored concept root, so deriving it from that same root
turns the assertion into `set(glob) == set(glob)` and deletes the only
cross-artifact control over admitted topic identity. Derive it instead from an
artifact independent of that root — the admission record's topic list, or the
compiled-root walk the admission suite already performs — so the equality still
crosses two artifacts and can still fail.

**Tests:**
- `test_every_leaf_is_in_exactly_one_set` (AC1)
- `test_admitted_topics_are_topology_leaves` (AC1)
- `test_foundation_corpus_is_exactly_the_admitted_inert_governed_topics` (AC1)
- `test_every_agent_read_concept_is_inert` — regression guard for concept-body
  inertness, not an AC1 falsifier
- `test_every_claim_group_declares_a_basis_and_its_fields` (AC6) — first
  execution of its `doctrine` arm against real input
- `test_each_foundation_topic_carries_its_required_sections`, enumerated over
  the admitted set rather than a parallel literal (AC2) — stub: true
- `test_typescript_node_topic_covers_its_seven_assigned_subjects` (AC2) — stub:
  true
- `test_python_pytest_topic_covers_its_four_required_subjects` (AC2) — the
  symmetric falsifier for AC2's Python conjunct: collection, fixtures, process
  boundaries, and temporary paths — stub: true
- `test_typescript_node_maturity_limit_appears_in_both_projections` (AC2) —
  stub: true
- `test_related_topics_references_resolve_to_admitted_topics` (AC1) — stub:
  true
- `test_each_newly_admitted_topic_declares_a_doctrine_group` (AC1) — the only
  falsifier for AC1's basis conjunct; the inherited basis test accepts either
  basis — stub: true
- `test_recorded_evidence_fields_carry_no_host_identifying_data`, over the
  admission record **and the authored concept root** this task writes (AC3) —
  stub: true. This check is assembled across five tasks, so it carries its own
  anti-vacuity anchor. The anchor is a derived walk with a pinned file floor
  per scanned root, in the shape this pack already runs for the export-boundary
  scan, **not** an equality against the criterion's prose enumeration: a pack
  test cannot read `docs/`, so both sides of such an equality would be in-pack
  literals and a later task adding an artifact would leave them agreeing and
  the walk green — the silent skip this anchor exists to close. Each pattern
  class carries one seeded positive control whose identifier is foreign to the
  running environment, so an implementation that resolved identity from the
  environment fails the control instead of passing everything.

**Done when:** the pack suite is green with twelve admitted topics and
twenty-four register entries, and each new test fails when its subject is
removed.

### T4: Reconcile shipped language-availability statements

**Depends on:** T3

Five shipped sentences become false: the availability statements in
`author-or-update-agent-skill/SKILL.md`,
`review-or-optimize-agent-skill/SKILL.md`, and the language-extension seam
reference, plus both the language-availability paragraph and the topic-count
sentence in the pack README. Restate each against the admitted set and retarget
the integration assertion to that reconciliation.

**Tests:**
- `test_language_extension_families_are_distinct_and_unpopulated`, retargeted
  to assert agreement between every shipped availability-or-count statement and
  the admitted topic set (AC7) — stub: true

**Done when:** no shipped file states a topic count or asserts an absence the
corpus no longer has, and the retargeted test fails when any one of the five
sentences is reverted.

### T5: Regenerate the governed corpus

**Depends on:** T4

Regenerate through the owning compiler; hand-edit no projection.

**Tests:**
- `test_generated_manifest_owns_only_router_outputs` — regression guard for the
  regenerated projection, not an AC1 falsifier — no stub (goal-based)
- `test_generated_concept_index_routes_to_every_topic` (AC1)
- `test_generated_router_is_inert_bounded_and_source_independent` — regression
  guard for the regenerated projection, not an AC1 falsifier
- `test_recorded_evidence_fields_carry_no_host_identifying_data`, re-run over
  the compiled concept root this task regenerates (AC3)

**Done when:** the compiler's `--check` mode reports `OKF000 check clean` on a
second run, and projection parity is green.

### T6: Re-observe activation

**Depends on:** T5

T4 edits both workflow `SKILL.md` bodies, and each body's bytes are pinned in
the activation record. That record cannot be reconciled by editing; it needs a
fresh headless observation. Take one, and discard rather than record any run
the harness reports as unreliable.

**Tests:**
- `test_independent_activation_results_bind_all_queries_and_descriptions` (AC7)
- `test_recorded_evidence_fields_carry_no_host_identifying_data`, extended over
  the activation record this task rewrites (AC3)

**Done when:** a headless run reports every query classified as expected with
zero errored runs and zero exclusivity violations, against the current digests.

### T7: Re-measure retrieval and the generic negatives

**Depends on:** T5

Predeclare solo retrieval cases for each newly admitted topic with margin above
the two-exclusive-result floor, and predeclare near-miss cases for the adjacent
pairs most likely to collide. Measure in a context held apart from authoring.
Both the retrieval record and the generic-negative record are bound to the
digest triple this slice moved, so both are re-measured. The inherited
foundation pins are a non-regression gate: a moved pin is surfaced, never
rewritten.

**Tests:**
- `test_foundation_router_cases_are_predeclared_bounded_and_include_near_misses`
  (AC4)
- `test_independent_router_results_meet_precision_and_recall_gate` (AC4)
- `test_foundation_pins_hold_the_shipped_cases` (AC4)
- `test_admitted_topics_are_measurably_distinguishable` (AC1, AC2, AC4) — the
  only artifact that falsifies AC2's non-collapse conjunct
- `test_generic_negative_record_is_attributable_to_the_tree_it_measured` (AC4)
- `test_corpus_does_not_answer_generic_engineering_requests` (AC3, AC4) — the
  only artifact that falsifies AC3's domain-bounding conjunct
- `test_recorded_evidence_fields_carry_no_host_identifying_data`, extended over
  the retrieval and near-miss cases this task writes **and** the retrieval and
  generic-negative result records it re-measures (AC3)

**Done when:** every inherited pin reproduces, each admitted topic has at least
two exclusive measured results, and the negative set stays within its bar.

### T8: Record the pytest-suite and Node/browser behavior fixtures

**Depends on:** T5

Declare both cases alongside the other representative task fixtures RFC-0097's
M2 measure names, then grade them. Adding them moves the whole-file digest that
every existing graded result in that file pins, so those results are
re-measured rather than re-stamped. Execution, attestation, and authoring stay
in separate contexts. Declare no output marker the skill does not instruct:
that circularity has been found and removed three times in this pack already. A
newly observed miss is recorded as measured; the existing known-miss exemption
set is not extended to absorb one, and adding an exemption needs owner
authority.

The new fixtures — not admission — open three author-skill enumerations, each
widened here rather than in T3: the six-id eval-set equality, the eight-id
behavior-result-set equality, and `AUTHORING_EVAL_IDS`. If a payload ships in a
suffix the export-boundary content scan does not cover, extend that scan's
covered suffixes with each suffix introduced and re-anchor its file floor, so
no shipped payload goes unread.

**Tests:**
- The author-skill contract suite's behavior assertions (AC5)
- Every declared marker appears in captured output from a blind run (AC5)
- `test_shipped_content_names_no_repository_only_reference`, over a scan whose
  suffix set and floor cover every added payload (AC5)
- `test_recorded_evidence_fields_carry_no_host_identifying_data`, extended over
  the eval declarations, their fixture payloads, and the graded behavior result
  records this task re-measures (AC3)

**Done when:** eight graded authoring results are recorded against the current
`evals.json` digest, with any miss recorded as measured rather than exempted,
and every shipped payload falls inside the export-boundary scan.

### T9: Close the records, registration, and status rolls

**Depends on:** T6, T7, T8

Roll the pack version under the pack version-bump rule with its changelog
entry, update the architecture record and the spec index, and restore the
`unsatisfied_dependency` ceiling to 8 — removing the rationale comment that
explains the raise to 9, which becomes false with the value it describes. The
milestone descriptor is not touched here; T1 owns it, so that the string names
this slice while the slice is in flight rather than at the moment it stops
being.

Then close the pair T1 opened: set the spec to `Shipped`, move its registration
from `["ini-009".work].active` to `.shipped`, and re-pin the brief digest in
both registrations a second time, in the same commit that sets the status. A
`work.shipped` entry whose spec does not read `Shipped` emits
`impossible_transition`, and leaving the spec at `Implementing` in
`work.active` would leave AC8 undischarged with every gate green.

**Tests:**
- `tests/roster/test_workspace_status_projection.py` at a ceiling of 8 (AC8)
- Brief-coverage lint, catalogue verify, deep lint, and projection parity (AC8)
  — no stub (goal-based)
- `test_single_ecosystem_fixture_reference_resolves_to_a_graded_fixture` (AC6)
  — the only point after T8's grading where the class's fixture condition can
  be checked rather than asserted — stub: true

**Done when:** both authored manifests carry the same bumped version, the
changelog entry is topmost for the pack, the spec reads `Shipped` in
`work.shipped` with both digests re-pinned, and the roster suite is green at
the restored ceiling.

## Risks

| Risk | Mitigation |
| --- | --- |
| A language claim becomes generic developer guidance | Limit every topic and retrieval case to skills, evaluations, packs, or their execution environments; the generic-negative gate is the falsifier. |
| New topics move a foundation result | Treat the inherited per-case pins as a hard non-regression gate; surface a moved pin rather than re-pinning it. |
| A group's evidence does not hold — a clause its sources do not state, or a mechanism only one of its failures supports | Two verification passes already refuted eight of eight asserted clauses, so treat this as the expected case rather than the unlikely one. Re-confirm at authoring time, drop the group rather than reword it, and if that leaves a leaf unadmissible surface the finding and route it through an approved spec amendment; do not withdraw a leaf in flight, because the ship transition requires every criterion checked. |
| The TypeScript/Node topic fails retrieval distinctness | Its governing note already withholds maturity, and the corpus has withdrawn a leaf for this reason before. Report the measurement and route through the amendment path above rather than rewording cases after seeing results. |
| The re-measured generic-negative set exceeds its bar | Five prompts in the fixed set sit directly on the new subjects: a CI job running unit tests, writing unit tests for a calculator, a flaky integration test, parallelising across worker processes, and a dependency vulnerability audit. If the bar is exceeded, report the measurement and route the offending topic through the amendment path; do not reword a negative prompt. |
| The doctrine arm ships on its first execution | T2 exercises it from constructed inputs and mutation-proves each limb, including the two reviewer-identity assertions it must not narrow. |
| A recorded measurement is re-stamped instead of re-taken | Every digest-bound record whose covered content moved is re-measured; the digest is never edited onto an older observation. |
| A run the harness calls unreliable is recorded | Discard and re-run; an unreliable run is not a measurement. |
