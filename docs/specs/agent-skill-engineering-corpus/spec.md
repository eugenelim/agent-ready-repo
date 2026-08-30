# Spec: Agent Skill Engineering Corpus

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`RFC-0097`](../../rfc/0097-agent-skill-engineering.md); [`ADR-0093`](../../adr/0093-okf-reference-corpora-remain-governed-build-time-sources.md); [`ADR-0097`](../../adr/0097-knowledge-access-capability-detected-provider-mediated.md)
- **Brief:** docs/product/briefs/agent-skill-engineering.md
- **Discovery:** none
- **Contract:** none — the semantic provider request/response contract is unchanged by this slice and remains transport-independent with no standalone JSON Schema.
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A skill author or an integrating agent loop asking about skill patterns,
usability, evaluation design, security and authority, or evidence maintenance
retrieves a small, task-shaped set of compiled topics instead of reading a
handbook. Every topic the corpus carries earns its place twice over: it
declares whether each claim group is portable doctrine or observed practice and
carries the evidence that basis requires, and retrieval selects it from at
least two prompts that return it and no other topic. A topic the taxonomy names but the evidence
cannot support is recorded as unpopulated with its reason, rather than written
to fill a slot. The authoring workflow additionally offers
`knowledge-provider`, so an author building a governed corpus, a retrieval or
router skill, or a procedure-to-reference handoff gets the modules that pattern
needs instead of a general framing pass.

Success is measurable at retrieval rather than at word count. No request
returns more than three topics; every prompt that shipped with the foundation
returns exactly the topic set it returned before; a fixed 40-prompt
generic-engineering negative set returns a topic body for no more than 5% of
its prompts; and no file the pack ships names a repository-only path.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | The pack gains topics and one authoring mode, so its own description of what it offers goes stale. | `packs/agent-skill-engineering/README.md` | This spec | README names the admitted topic groups and the four advertised modes; `catalogue lint --deep` clean | README's mode list equals the workflow's advertised modes |
| Current architecture | RFC-0097 requires each delivery spec to update the planned architecture with its slice's implemented names, paths, and verification evidence. | `docs/architecture/agent-skill-engineering.md` §3, §9, §11 | This spec | Topology lists admitted and unpopulated leaves; §11 records this slice's verification date | Architecture stays `PLANNED`; claims no later-slice surface |
| Release history | The pack's version bump is a released-artifact change, and this repository records pack releases. | `docs/product/changelog.md` — a `## [agent-skill-engineering][<version>] — <date>` entry | This spec | Entry present in the same change that bumps the manifests | Entry names the advertised-mode change and the admitted topic groups |
| Interface compatibility | The pack's published surface is consumed externally, and the aggregated marketplace pins the same version. | `packs/agent-skill-engineering/pack.toml`, `.claude-plugin/plugin.json`, and the aggregated `.claude-plugin/marketplace.json` — regenerated, never hand-edited | This spec | Matching version bump per `packs/AGENTS.md`; publication and roster gates green | Both manifests carry the same bumped version |
| Delivery-cut variance | The 2a/2b split and the `runtime-package` deferral depart from RFC-0097's single "Spec — corpus" follow-on and from the brief's slice-2 line. | A distinct `Delivery-cut variances` section in `docs/product/initiatives/ini-009-agent-skill-engineering.md`; the brief's slice table | This spec | Variance record naming both departures and their authority; brief slice table showing 2a and 2b | A reader of the brief's slice 2 reaches the split and the deferral |
| Reusable learning | Work-loop's `spec-approved` and `plan-locked` gates capture spec- and plan-authoring residue. | `project-knowledge` public seam | work-loop | Capture receipts, or the named skip `project-knowledge unavailable` | Receipts distilled at `plan-locked`, or the skip recorded |
| Maintainer / adopter procedure | Not applicable this slice. The public guide is the brief's slice 5 and is written against the finished corpus. | none — `agent-skill-engineering-guide-and-docsurl` stays open in `[backlog].open` | Slice-5 owner | Entry remains open and the `GUIDE_OPTIONAL_PACKS` exemption remains in place | Entry still open with its exemption intact |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Admit a topic only when every claim group declares one basis — `doctrine` or
  `observed-practice` — carries that basis's required fields, and measured
  retrieval selects the topic alone.
- Record a taxonomy-named topic the evidence cannot support as unpopulated,
  with the reason and what would admit it later.
- Keep the census, admission evidence, and every repository-specific citation
  in the pack's non-projected `tests/fixtures/` tree, and keep any test that
  walks outside the owning pack in `tests/roster/`.
- Re-measure the foundation retrieval cases after every corpus change and treat
  a regression in any single case as a defect in the change.
- Record every failure this slice's gate chain observes — wherever it lives —
  with the invocation that reproduces it, the base it was seen on, an
  attribution, and who attributed it. Never absorb a red this change did not
  cause into a green result.
- Regenerate every projection through its owning command rather than editing a
  generated or self-hosted file.
- Close this pack's publication obligations — matching manifest bump, eval
  harness, changelog entry — before the change is proposed for merge.

### Ask first

- Admitting a claim group that declares neither basis, or a `doctrine` group
  that names a promotion class without that class's evidence.
- Changing the router skill's name or its activation description, which a
  recorded measurement pins.
- Widening the advertised mode set beyond `frame`, `create`, `update`, and
  `knowledge-provider`.
- Raising a tolerated-finding ceiling, adding a dependency, or introducing a
  new artifact-kind home or top-level directory.

### Never do

- Advertise `runtime-package`, runtime-profile, plugin, hook, or subagent
  authoring as an available mode; those remain unavailable until the runtime
  profiles that make their claims verifiable exist.
- Cite a repository-only path, an acceptance criterion, or an internal
  governance record anywhere the pack ships.
- Author a language-specific or execution-economics topic body; those belong to
  the successor slice registered by AC15.
- Change the workspace-status engine's code or any `packs/core` surface; the
  executing-clause deletion is a separately routed change. This does not reach
  the engine's tolerated-finding ceilings, which *Ask first* above routes to
  scope-owner sign-off; a ceiling raised without that sign-off is still
  forbidden here.
- Introduce a new module boundary, top-level directory, or dependency to carry
  the corpus; it compiles through the existing governed OKF compiler.
- Derive, infer, or back-fill an evaluation result that was not observed, or
  weaken a declared expectation to make a record agree with itself.
- Read or traverse another pack's raw OKF, or make this pack's raw OKF readable
  at runtime.

## Testing Strategy

- **Census completeness: TDD.** Every authored skill maps to a family or a
  reviewed exception; the predicate is compressible and the fixture declares the
  mapping first. The live-discovery half runs in `tests/roster/`, the only tree
  permitted to walk every pack.
- **Topic admission (AC2, AC4): TDD.** "Admitted implies every claim group
  declares a basis, carries that basis's fields well-formed, and the topic is
  measurably distinguishable" is a predicate over the admission fixture, the
  compiled topic set, and the measured retrieval record. It is the spec's
  load-bearing invariant, and it deliberately stops at form: the erratum
  assigns soundness to the reviewer AC2 names.
- **Taxonomy completeness: TDD.** "Each of the 36 topology leaves is in exactly
  one of two sets" is a predicate over a transcribed enumeration.
- **Retrieval precision, per-case non-regression, and the generic-engineering
  negative set: goal-based check**, exercised as an integration test over the
  staged built tree, because the bars are measured rates against declared sets
  that only prove out once the tree is assembled. The measurement itself is an
  observed run by an independent read-only sub-context, transcribed into the
  recorded fixture with the run named — the same provenance the shipped record
  already declares, and the same category as the behavior evidence below.
- **Determinism, staged-tree confinement, and hostile-metadata refusal:
  goal-based check** — repeated compiles compared byte-for-byte, and a staged
  tree exercised with the checkout unavailable.
- **Body-to-record parity (AC3): TDD.** Comparing a shipped section against a
  fixture is a pure predicate over two files in the owning pack.
- **Unpopulated-topic fallback: goal-based check** over the compiled tree — a
  request naming an unpopulated leaf returns the gap statement and applicable
  admitted topics, and no body for that leaf.
- **Mode contract: TDD.** AC10's claims — four advertised modes, four
  mode-specific modules, read-only entry, explicit transition before write —
  are text assertions over `SKILL.md` and its `references/` tree.
- **Provider-pattern failure surface: goal-based check** against the fixtures
  the governing RFC requires before the mode may be advertised.
- **Mode-availability guard: TDD**, on both halves — the enumeration's count
  floor and a table-driven positive control proving the matcher still detects.
- **Behavior evaluation: visual / manual QA.** Grading is operator-attested by
  contract, so the evidence is an observed run transcribed into the fixture.
- **Portability and published-surface joins: goal-based check.** Each is a
  membership or absence fact one command answers.
- **Workspace, brief, and index records: goal-based check** —
  `lint-spec-status.py`, `lint-brief-coverage.py`, and the workspace
  reconciliation output together answer whether the milestone, the two
  registrations, the Spec-map rows, and the `docs/specs/README.md` Status
  column are current.
- **Delivery-cut variance: goal-based check** — a grep for the variance
  section heading and the brief's slice-table rows.

Seven criteria are verified in TDD mode — AC1, AC2, AC3, AC4, AC5, AC10, and
AC11 — and each carries a compilable red stub in its implementing task. The
remaining ten are goal-based checks or manual QA and record `no stub (mode)`
against the reason. No criterion is left without a declared mode. Seventeen
criteria are numbered AC1–AC16 and AC18: failure attribution is a rule about
how this change is conducted rather than a property of what it ships, so it is
an *Always do* Boundary, and AC18 keeps its number because renumbering it would
edit a completed task section.

## Acceptance Criteria

### Census and admission

- [x] **AC1 — Skill census proves coverage.** A versioned census fixture in the
  pack's non-projected `tests/fixtures/` tree maps every authored skill under
  `packs/*/.apm/skills/` to at least one pattern family or to a reviewed
  exception carrying a role-or-placeholder owner and a rationale, and records
  the population size it was taken against. A test in `tests/roster/` — not in
  any pack's suite, which may not walk outside its owning pack — compares that
  size against live discovery and fails when a skill exists the census does not
  resolve. Its failure message names the owning surface and the command that
  re-takes the census. The census establishes coverage; it does not by itself
  admit any topic.
- [x] **AC2 — Every claim group declares its basis and carries that basis's
  evidence.** Under RFC-0097's 2026-08-28 erratum each compiled topic declares,
  per claim group, exactly one basis, and records it in the non-projected
  admission fixture.
  A `doctrine` group records one of D8's four promotion classes together with
  the evidence that class names — a public contract, naming the specific clause
  that governs the group's claims and the two or more runtimes documenting
  *that clause*; or repeated independent observed failures that share one
  mechanism, named once for the group; or one severe reproducible safety
  failure with its boundary and reproduction; or a controlled measurement with
  its setup, its preserved-semantics record, and a repetition count showing the
  benefit repeats — plus, for every source it cites, that source's identity,
  its `retrieved_at` date, and any exposed version or last-updated date or an
  explicit `none exposed`.
  An `observed-practice` group records the census observations supporting it at
  distinct skill paths in distinct packs, an applicability limit naming that
  population and stating the claim is not established beyond it, and a
  revalidation trigger. It records no promotion class and is never written as
  universal guidance.
  Every claim group, whichever basis it declares, records a revalidation
  trigger, because RFC-0097's carry-list binds that to every admitted concept
  and the erratum narrowed only the promotion basis. Every topic additionally
  records a last-verification date and the reviewer who judged the evidence
  sufficient. The harness asserts that a basis is declared
  and that the declared basis's fields are present and well-formed; it does not
  assert that the evidence supports the claim, which the erratum assigns to that
  named reviewer.
- [x] **AC3 — The shipped body and the admission record agree, per claim
  group.** For every claim group a topic declares, that group's shipped fields
  appear in the topic's provenance-and-lifecycle section and equal the
  admission record field-for-field — source identities and dates for a
  `doctrine` group, the applicability limit for an `observed-practice` group.
  A topic declaring both bases carries both; satisfying one basis's parity does
  not discharge the other's. The reviewer identity stays in the non-projected
  fixture and never reaches the shipped body. The shipped limit names its
  population in portable terms carrying no pack path, so parity does not push
  repository structure across the export boundary. The fixture exists because the harness
  reads structured data; the body exists because a consuming agent reads the
  body and never sees the fixture. Neither can be dropped, so the parity check
  is what keeps them one fact — unlike the unpopulated record, whose single
  home the compiler can produce.
- [x] **AC4 — Admission requires measured distinguishability.** Every admitted
  topic is selected by at least two retrieval cases whose *measured* result is
  that topic and no other, read from the recorded run rather than from declared
  expectations. A topic whose exclusivity is only declared fails.
- [x] **AC5 — Declared unpopulated topics.** The 36 topology leaves RFC-0097 D3
  enumerates are transcribed into a fixture carrying names, a source reference,
  and an asserted count of 36 — and nothing else, so the leaf's state lives in
  one place. Each leaf is in exactly one of the compiled topic set or the
  compiled unpopulated record; a leaf in neither or in both fails. Each
  unpopulated leaf records its reason — including, where it applies, that
  neither basis could be evidenced — and what would admit it. The compiled
  unpopulated record is not itself an admitted topic: the harness excludes it
  by its exact identity — there is one such record, authored at the bundle
  root — and never by a property a topic body could reproduce, such as a marker
  field, a section shape, or a name pattern. The unpopulated side of the
  partition is derived from the leaves that record names, not from whatever the
  harness excluded, so a document cannot both escape iteration and satisfy the
  partition. The fallback is exercised by a declared retrieval case naming an
  unpopulated leaf, whose measured outcome is recorded in the same fixture and
  under the same digest binding as every other retrieval case. That case's
  declared expected set is the applicable admitted topics — it is not a
  zero-expectation case, and reading it as one would collide with the shipped
  assertion that every zero-expectation case returns nothing.

### Retrieval

- [x] **AC6 — Expanded retrieval precision.** The retrieval fixture reaches at
  least 40 cases, covers every admitted topic with at least two exact-set
  cases, and adds near misses for the vocabulary the new topics introduce. At
  least 90% of cases select their exact or pre-approved set, precision and
  recall against the declared sets are each at least 90% — the bars the shipped
  gate already asserts and the governing RFC states — and **no** case returns
  more than three topics, the absolute bound the shipped gate asserts and the
  Objective states. At least half of the 40 are topic-bearing, so the floor
  cannot be reached with near misses and no-topic cases that dilute the
  exact-set rate rather than exercise the corpus. Every bar in this criterion —
  the case floor, the topic-bearing fraction, and the exact-set, precision, and
  recall rates — is computed over the retrieval case list alone. The
  generic-engineering negative set is a separate population with its own
  criterion and its own fixtures, and contributes to no denominator here. Every new case's expected set is
  authored and committed before the run that measures it, so an expectation
  cannot be tuned to what was observed.
- [x] **AC7 — The corpus does not become an encyclopedia.** A fixed 40-prompt
  generic-engineering negative set returns a topic body for no more than 5% of
  its prompts — the falsifier RFC-0097 names for the risk this slice creates.
  The set is synthetic and authored, not transcribed from any session. Its
  prompts and their measured outcomes live in their own pair of fixtures,
  carrying the same source, router, and generated-tree digest triple and the
  same declared evaluation mode as the retrieval record, and the results fixture
  asserts that its result set equals the fixed 40-prompt set, so the 5% bar is
  computed over a record proven complete rather than over whatever was
  transcribed. The measurement is therefore attributable to the tree it
  measured without joining the retrieval case list.
  They stay out of that list deliberately: the shipped suite asserts that every
  zero-expectation case returns no topic at all, which is stricter than this
  criterion's 5% and must not be weakened to accommodate it, and folding 40
  near-certain passes into the retrieval population would dilute the rates
  AC6 computes.
- [x] **AC8 — No foundation regression.** The 24 retrieval cases that shipped
  with the foundation are pinned as `(id, measured_topics)` pairs — named for
  what they hold, since `expected_topics` is the author-declared field and
  these are measurements — derived from
  the recorded run as it stands **before** any corpus change. Every one has a
  measured result equal to its pinned pair, asserted at each point the corpus is
  re-measured rather than only at the end. This is a per-case gate, not a rate:
  no new case can compensate for a foundation case that moves.

  A pin may be re-taken only on explicit scope-owner authority, and only when
  the QA record carries, for that pin, the corpus change that moved it, the
  evidence the new value rests on, and why the original value is judged wrong
  rather than the measurement. A re-pin whose basis lives only in a commit
  message does not satisfy this: the record is the control, and without it the
  fixture stops being able to detect the regression it exists for.
- [x] **AC9 — Determinism, confinement, and portability hold.** Two clean
  compiles are byte-identical; the staged built tree contains no
  authoring-source bytes and no checkout-relative path into that source; every
  retrieval case runs with the checkout unavailable and attempts no read
  outside the staged tree; hostile metadata fixtures produce a non-zero compile
  result or a documented refusal, a stable diagnostic, no output outside the
  declared build directory, and no source mutation; and the provider-side
  security fixtures inherited from the foundation are unchanged and still pass.
  Separately, no file under the pack's `.apm/` export boundary or in the
  compiled reference tree contains a repository-only path, an
  acceptance-criterion citation, or an internal governance record — asserted
  over hand-authored and generated content alike, so a mode module cannot
  introduce what a compiled topic cannot.

### Authoring mode

- [x] **AC10 — `knowledge-provider` available.** The authoring workflow advertises
  `frame`, `create`, `update`, and `knowledge-provider`. Entering
  `knowledge-provider` loads the knowledge-provider pattern, provenance,
  retrieval-evaluation, and security-boundary modules and no other
  *mode-specific* module — the common contract's safety-and-authority module
  continues to govern every read and write — begins read-only, and requires an
  explicit user transition before any write. This is the milestone advance
  RFC-0097 licenses once the provider-pattern fixtures of AC12 pass, not a
  supersession of the foundation's availability criterion.
- [x] **AC11 — Remaining modes stay unavailable.** `runtime-package`,
  runtime-profile, plugin, hook, and subagent authoring receive a stable,
  versioned unavailable response and are absent from both activation
  descriptions. The absence guard derives its vocabulary from the mode fixture
  and keeps an exact-count floor pinned to the reduced enumeration. A durable
  table-driven positive control asserts the matcher still detects every
  forbidden surface form, so weakening the matcher reddens a test rather than
  silently satisfying every absence assertion.
- [x] **AC12 — Provider-pattern fixtures pass first.** Versioned fixtures cover
  the knowledge-provider pattern's failure surface: a corpus with no governed
  source, an ambiguous router selection, a retrieval evaluation that declares
  no negative cases, and a procedure-to-reference handoff that would give the
  generated half mutation authority. Each declares a stable refusal or exit
  class and a bounded diagnostic. The check is fixture conformance — each
  declared response is asserted against the contract's rules, in the shape the
  pack's existing provider-contract suite already uses — not the execution of a
  runtime guard, because the mode is instructions rather than code. All four
  pass before the change advertises the mode.

### Evaluation evidence

- [x] **AC13 — Expanded behavior fixtures.** Versioned behavior fixtures cover
  the foundation's four cases plus cold-start workspace orientation,
  cross-session resumption, progressive result presentation, and a
  knowledge-provider read-only entry — eight of the eleven the governing gate
  requires across M2. Each declares its required
  output markers, applicable checklist items, and seeded defects before
  execution; recorded assertion counts equal declared counts; and each result's
  `source_files` is an exact set.
- [x] **AC14 — Review-case grading is observed.** The durable behavior record
  carries all five values the runner emits for the review cases — `produces_ok`,
  `output_ok`, `assertions_ok`, `errored`, and `passed` — transcribed from one
  graded run driven in the runner's in-harness mode with a supplied report, and
  names the run they came from. No per-marker value is recorded, because the
  runner emits none and inferring one from `output_ok` is the circular
  derivation the predecessor already removed. The `Mode: review` declaration is
  unchanged, and the QA record states that the marker is enforced at run time
  and is not re-checkable from the committed artifact.

### Records

- [x] **AC15 — Workspace, brief, and index records are current.** The
  initiative's milestone string names the slice actually in flight; this spec
  is registered as active work while in flight and moved to shipped work at
  close, in the same commit that sets its status; the successor slice has an
  authored spec and
  plan pair and is registered as queued work canonically with its dependency on
  this spec stated; the brief's Spec-map rows and slice table mirror the linked
  specs; and every row this change touches in `docs/specs/README.md` carries
  that spec's real `Status`, including the foundation row that currently reads
  `Implementing` against a `Shipped` spec.
- [x] **AC16 — Delivery-cut variance is recorded.** The 2a/2b split and the
  `runtime-package` deferral are recorded in a distinct `Delivery-cut
  variances` section of INI-009 with their authority — not appended to the
  backlog-disposition section, whose scope is RFC-0097 D7 — and the brief's
  slice table reflects both.
- [x] **AC18 — Published surfaces stay joined.** The pack satisfies the
  conformance metadata contract, and its membership of the two agent-plugin
  roster enumerations, the catalogue navigation outcome map, and the
  publication roster is verified by running each owning gate. Every test this
  change adds is reachable by a gate CI runs. A `tests/roster/` module already
  is: the Makefile's suite target and the build-check workflow both invoke
  pytest over `tests/`, which collects that tree, so no new wiring is needed and
  none is added. The shared-test command-plan digests are therefore untouched;
  they are re-pinned only if some other part of this change adds or alters a
  command line in either normalized dry-run plan, since the whole line list is
  hashed.

## Follow-ons

- **Process deviation, recorded rather than hidden.** AC8 was amended at the
  ship gate, not through the engine's `contract-amendment` transition. That
  transition is legal only from `CODE-IMPLEMENTATION` and returns the run to
  `SPEC-PLAN-DRAFTING`, re-running both human approval gates, the pre-EXECUTE
  reviews, `approve-plan`, `schedule`, and `plan-locked` for an already
  delivered contract. The scope owner chose the finish-time adjustment with the
  authority and evidence recorded in `qa.md`. The amendment weakened AC8's
  predicate — it now admits an owner-authorised pin re-take — so it is named
  here rather than absorbed into the criterion it changed.
- **Second process deviation, recorded beside the first.** The *Never do*
  above was also amended at the ship gate, by the same finish-time route and for
  the same reason: it hard-forbade changing "its ratchets" while *Ask first*
  routed a tolerated-finding ceiling raise to sign-off, so one Boundaries
  section governed the same action two ways. The raise was taken under the
  *Ask first* reading with recorded approval; the amendment reconciles the text
  to that, and narrows nothing else.
- **Repository owner: the specs index `Status` column is unguarded.** Nothing
  asserts `docs/specs/README.md` against each spec's own `**Status:**`. This
  slice's row silently read `Approved` while the spec read `Implementing`, and
  no gate caught it; an acceptance-criteria pass at the ship gate did. Every
  spec in the repository shares the exposure, so the fix belongs to the index's
  owner and not to this pack.
- Workspace-engine owner: deletion of the `brief_queue.executing` clause in
  `workspace_status_engine.py`, with its core-pack publication tail — measured
  at 0 true positives and 2 false positives, and split out of this slice on
  2026-08-28 because its collateral surface is entirely unrelated to the corpus.
  This slice makes no engine change. It does raise one tolerated-finding
  ceiling — `unsatisfied_dependency` 8 to 9, on the scope-owner sign-off
  recorded in `qa.md` — for the transient 2b-to-2a dependency edge.
- Slice-2b owner: `docs/specs/agent-skill-engineering-languages-and-execution/`
  — Python/pytest and TypeScript/Node depth and the execution-economics topics
  (5 of the 36 topology leaves), their retrieval prompts, and two of the four
  remaining behavior fixtures: the pytest suite and the Node/browser suite.
- Slice-3 owner: the runtime composition profiles slice — the composition and
  runtime-profile leaves (11 of the 36), the `runtime-package` mode those
  profiles make verifiable, and the other two remaining behavior fixtures:
  subagent composition and hook/plugin design.
- Slice-5 owner: `agent-skill-engineering-guide-and-docsurl` in `[backlog].open`
  — the public guide and the site `docsUrl` repoint.
- Guides owner: the `tools/` failures that reproduce on this slice's base
  independently of it —
  `test_guide_typed_asides.py::test_ledger_has_complete_terminal_classifications`
  and `::test_ledger_matches_converted_asides_and_unchanged_quotations`.
  No `Makefile` target this slice runs invokes them, per the Assumption below
  that sources the claim. They are routed against the existing
  `[backlog].open` entry `guide-blockquote-ledger-has-no-regenerator`, whose
  subject is the same ungated ledger; extending that entry's summary adds no
  new legacy-shaped entry, so the ceiling is not reached and no raise is
  proposed.
- Pack suite: four tests in this pack's own suite arrive red from the base,
  from one upstream commit, `c7ed3f910`, by **two** mechanisms, and each
  carries its own disposition. All four
  are attributed `inherited`; `Makefile:471-475` invokes the suite, so this
  slice's gate chain reaches them, and no workflow names it, so they are
  invisible to the PR checks and surface only under `make test`.
  *Mechanism 1 — `c7ed3f910` added an eval case without moving its assertions.*
  `test_contract.py::test_authoring_behavior_evals_cover_frame_and_existing_update`
  and `::test_authoring_behavior_evidence_matches_its_source_digest`: a
  `cognitive-load-output-quality` case entered
  `author-or-update-agent-skill/evals/evals.json` without updating the exact-set
  assertion or the recorded digest. **T12 owns both** — it rewrites that evals
  tree and re-records its digest — so the red clears as a byproduct of work this
  plan already compels, and is reported as inherited-and-fixed-here.
  *Mechanism 2 — the same commit wrote the managed rendering block into this
  pack's skills, moving their bytes.*
  `test_foundation_corpus.py::test_independent_router_results_meet_precision_and_recall_gate`
  pins `router_digest` to `ase-okf-reference/SKILL.md`'s bytes; **T9 owns it**,
  which re-records `router-results.json`.
  `test_pack_boundary.py::test_independent_activation_results_bind_all_queries_and_descriptions`
  pins digests for **both** workflow skills' `SKILL.md` bytes, and `c7ed3f910`
  moved both. It cannot be reconciled by editing — it needs a fresh headless
  observation, which `Never do` forbids back-filling. **T11 owns it**, because
  T11 moves `author-or-update`'s bytes again and so must re-record regardless;
  the run covers `review-or-optimize` too, whose digest is re-recorded from base
  bytes this slice does not otherwise change.

## Assumptions

- Technical: RFC-0097 D3's topology enumerates 36 leaves across 10 groups; the
  foundation shipped 3, this slice's candidate set is 17, the successor slice
  holds 5, and the runtime-composition slice holds 11 (source: probe over
  `docs/rfc/0097-agent-skill-engineering.md:207-254`)
- Technical: admission is evidence-limited, so the number of leaves this slice
  admits is bounded by how many can evidence either basis and is expected
  to be well below the 17-leaf candidate set; the remainder is recorded
  unpopulated under AC5 rather than authored (source: user confirmation
  2026-08-28)
- Technical: the three foundation topics ship with no external source citation
  of any kind, so under the erratum's retroactive clause they are
  `observed-practice` and gain the applicability limits they lack. They are not
  back-filled as `doctrine`: RFC-0097:555 sources the Agent Skills
  specification for a portable `SKILL.md` substrate and for scripts as
  deterministic helpers, which does not govern trigger-quality or
  instruction-density claims, and citing a contract that does not govern a
  claim is the vacuity this admission rule exists to prevent (source: probe over
  `packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/concepts/`;
  RFC-0097 erratum 2026-08-28)
- Technical: this slice takes RFC-0097:582's count floor for the retrieval
  suite while its *topical* coverage — pytest, Node, execution economics,
  subagents, hooks, plugins, runtime profiles — closes across slices 2b and 3;
  the joint-closure arithmetic is stated in the plan (source:
  `docs/rfc/0097-agent-skill-engineering.md:582`)
- Technical: retrieval cases are a flat JSON list, 24 today, covering three
  topics with six no-topic cases (source: probe over
  `packs/agent-skill-engineering/tests/fixtures/router-cases.json`)
- Technical: the mode-absence guard reads its vocabulary from
  `unsupported-mode-cases.json` and pins an exact count as an anti-vacuity
  floor; its matcher `_names_mode` has no positive control anywhere in the pack
  tree; and a sibling contract test asserts the exact six-mode set, the mode's
  absence from the activation description, and the fixture's `reason` and
  `baseline` strings verbatim in `SKILL.md` (source:
  `packs/agent-skill-engineering/tests/pack/test_pack_boundary.py:100-143`,
  `packs/agent-skill-engineering/tests/skills/author_or_update/test_contract.py:55-101`)
- Technical: the OKF compiler's only declared input is the bundle root and every
  managed output is under `.apm/skills/ase-okf-reference/`, so a record the
  harness reads and the pack ships must originate in the bundle root (source:
  `packs/agent-skill-engineering/pack.toml:42-44`,
  `packs/agent-skill-engineering/.okf-generated.json`)
- Technical: `agent-skill-engineering` is not in the self-host include list
  (`core`, `governance-extras`, `product-documentation`, `catalogue-curation`),
  so its `.apm/` edits leave no stale projection (source:
  `packages/agentbundle/agentbundle/build/recipes/self-host.toml:26`)
- Technical: behavior grading reads a driver payload only under the in-harness
  branch, so a run must pass `--mode in-harness` and seed its workspace with
  `--prepare-workspace`; the grade emits `produces_ok`, `output_ok`,
  `assertions_ok`, `errored`, and `passed`, computed as a conjunction, and no
  per-marker data (source:
  `packages/agentbundle/agentbundle/cli.py:1188-1208`,
  `packages/agentbundle/agentbundle/commands/pack_evals.py:922-934, 1235`)
- Technical: registering this spec as active work clears ini-009's
  `impossible_transition` under the existing predicate, and at ship the corpus
  returns to the two instances the existing ceiling already tolerates, so this
  slice requires no engine change (source:
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py:2471-2474`,
  `tests/roster/test_workspace_status_projection.py:1032`)
- Technical: the inherited failure set moves with the base and is therefore
  re-observed rather than assumed, and it has already moved twice
  while this slice was in flight. Two `test_guide_typed_asides.py` ledger tests
  reproduce and are invoked by no `Makefile` line; four tests in this pack's own
  suite reproduce and *are* invoked at `Makefile:471-475`; and
  `test_local_ci_shared_test_deduplication.py`, which an earlier base left red,
  now passes because its owner re-pinned it (source: each gate invocation run
  directly on the rebased base, and a search of the whole `run-test-suite`
  macro, `Makefile:422-537`, for the absence. A whole-directory `pytest tools/`
  run is a non-authoritative probe, because `Makefile:497-499` records the
  per-class split as a stability property; where the two disagree the per-gate
  invocation governs)
- Process: `[backlog].open`'s legacy-shape ceiling of 160 is at its measured
  maximum and its failure message forbids raising it; only entries carrying a
  `path` key are exempt, and those require a real artifact (source:
  `tests/roster/test_workspace_status_projection.py:936-1011`)
- Process: `.apm/` is the projection source of truth; every non-cosmetic pack
  change bumps that pack's `pack.toml` and `.claude-plugin/plugin.json`
  together, updates its eval harness, and records a
  `## [<artifact>][<version>]` entry in `docs/product/changelog.md`; shipped
  pack content carries no repository-only path or internal governance citation;
  and a pack test may not resolve a path outside its owning pack (source:
  `packs/AGENTS.md`, `docs/CONVENTIONS.md:689-693`,
  `tools/lint-pack-test-boundary.py`)
- Process: the governing RFC licenses `knowledge-provider` once the
  provider-pattern fixtures pass, and keeps `runtime-package` unadvertised
  until the runtime-profile gates pass (source:
  `docs/rfc/0097-agent-skill-engineering.md:136`)
- Process: a pointer from a frozen spec belongs in its `Status` field and only
  there and must name an ADR, so this slice records the mode advance in its own
  criteria rather than asserting a reachability the frozen predecessor cannot
  provide (source: `docs/CONVENTIONS.md:138-159`)
- Process: the census assertion reddens for any author who adds or removes a
  skill in any pack; that cross-author obligation is accepted and mitigated by
  a routing failure message rather than by weakening the assertion (source:
  user confirmation 2026-08-28)
- Product: a topic is admitted when each claim group declares `doctrine` or
  `observed-practice` and carries that basis's fields, plus measured retrieval
  distinguishability; the census proves coverage and admits nothing on its own
  (source: RFC-0097 erratum 2026-08-28; user confirmation 2026-08-28)
- Product: the workspace-status engine change is split out of this slice as its
  own change, and its correct form is deletion of the executing clause rather
  than narrowing it, because the clause encodes a false invariant and the
  narrowed form would still fire on no real state (source: user confirmation
  2026-08-28)
- Product: this slice ships alone in its session, and its successor slice is
  authored and registered as queued work at the same time (source: user
  confirmation 2026-08-28)
- Product: `runtime-package` is deferred to the slice that delivers the runtime
  profiles its recommendations depend on (source: user confirmation 2026-08-28)
