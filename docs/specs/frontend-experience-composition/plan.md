# Plan: frontend-experience-composition

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (export boundary, version bump rule,
  eval-harness rule); `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md`
  § *Superseding a frozen document* (the four rules the frozen-record edit obeys);
  `docs/product/changelog.md`'s own header (released-entry level and adjacency).
  Analogous implementations: `packs/core/JOURNEY.md:180` for an optional `####`
  sub-stage both journey lints tolerate, and
  `guides/experience-design/how-to/design-each-screen.md:32-41` for `Choose one`
  and `Required`, and `guides/experience-design/how-to/establish-design-intent.md:34`
  for `Optional` — no single how-to table carries all three values, which is why
  the vocabulary this change adopts is anchored across two. Construction path: the two new tests join the existing journey and
  contract gates; `tools/lint-ci-parity.py:463-467` is the local-axis disposition
  shape a new `build-check.yml` step must match and `:841-914` the
  `_GATE_MAIN_CHECKS` tuple supplying its second axis, and
  `.github/workflows/build-check.yml:560-567` is the step shape and the placement
  precedent. Named uncertainty: the state partition and tier bands are derived in
  T1 against the real artifacts, not settled here.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/frontend-experience-composition/notes/verification-ledger.md`.
> A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan.

## Approach

Ten tasks over a graph that branches at T2 and rejoins at T7. T1 derives the
partition and T2 writes it into the four contract copies; T3, T6, T8 and T9 then
run off T2. Two limbs rejoin at T7: the serial journey spine T3 → T4 → T5, and
T6, which hangs off T3 because it re-runs the assertions T3 builds. T7 waits on both because its assertions compare
the contract against *both* journeys and so cannot be green until each has stated
its ladder. Putting those after both, rather than making them a sibling
obligation of each, is what stops them being checks that are red or vacuous at
every intermediate boundary. The T8 and T9 limbs never reach T7 at all; they
rejoin only at T10, which closes over everything.

T1 is an exploration, not a transcription: it derives the partition from the real
tables rather than implementing a partition stated here. The spec's criteria state
the invariants, so a derivation that moves is expected and costs no amendment;
the move is recorded in the verification ledger.

Review shape is **MIXED**. T1, T2 and T7 are deep; T4 and T5 are prose edits over
files carrying existing byte-exact and negative assertions, which is mechanical
but unforgiving.

## Constraints

- The tier-count test computes each tier's obligation as a *cumulative* sum,
  because `<!-- Required: explore+ -->` means that tier and above. The label
  counts are 10 / 15 / 7 and the obligations are 10 / 25 / 32; a test comparing
  label counts pins a ladder where production is cheaper than pilot.
- `packs/frontend-engineering/JOURNEY.md` is pinned by the suites AC-0035 names,
  one of them repository-level. No count here: this constraint said three for
  nine review rounds while the measured answer was four, and a number with two
  homes is how that survived its own repair. T4 enumerates every assertion
  before editing, not after a failure.
- The `check-contract-drift` step compares bytes across four copies, so T2 writes
  three from the first rather than editing four.
- The state-coverage map ships inside `packs/experience-design/` too, so it may
  carry no value literal. State *names* are safe: `reduced-motion` is legal and
  only `prefers-reduced-motion` matches the lint.
- **Projection ordering, stated once and referenced elsewhere.** `make build-self`
  refuses a dirty tree and this delivery may not pass `FORCE=1`, so every
  regeneration commits its edits first and then runs unforced `make build-self`.
  `packs/AGENTS.local.md` § Marketplace and release pipeline step 2 says to pass
  `FORCE=1`; that contradicts the root `AGENTS.local.md` and is not followed here.
- A released changelog heading sits at `##` directly beneath `[Unreleased]`, and
  `core`'s newest entry must stay adjacent to `[Unreleased]`. The four pack
  entries this delivery adds go immediately below `core`'s newest entry.

## Construction tests

Most construction tests live under **Tasks** below. This top-level section is
only for the cross-cutting assertions that span tasks.

The assertion groups below span two new test files. Both are repository-level —
they read across two packs and the guides — so both go to the roster suite,
which means T7 must wire them into CI above the bulk `pytest tests/ -q` step or
they attribute no failure. No count is stated here: the list is the count, and a
number beside it is what went stale on each of the three review rounds.

- **State-map completeness and totality.** Parses the map, the 18-state table from
  `frontend-engineering/SKILL.md`, and the screen-brief template's state lines.
  Asserts the map's state set equals the 18-state set with no duplicates, and that
  every template state line resolves to at least one member — admitting the one
  line that names two. Fails on an added, dropped, renamed or duplicated state,
  and on a brief state left unmapped.
- **Band assignment.** Asserts every state carries exactly one assignment from
  the closed set `explore | pilot | production | conditional`, that each of the
  three bands carries at least one unconditional state, and that a `conditional`
  row names its trigger. A bare `conditional` is an unassigned state wearing a
  label and would otherwise satisfy the first half.
- **Accessibility preservation.** Asserts the map records a `yes`/`no`
  WCAG-bearing flag for every state, that every state flagged `yes` is assigned
  to `explore` or to a named conditional trigger, and that each `yes` cites the
  success criterion it rests on. The test reads the recorded flag rather than
  judging accessibility, which is what makes the predicate decidable; a missing
  flag would read as `no`, so its presence is asserted separately.
- **Tier-count agreement.** Computes each tier's cumulative `Required:` annotation
  count from the contract and compares it with the count each journey states.
  Fails when a field is re-tiered and a journey's promise goes stale.
- **Explore-subset agreement.** Parses the explore state subset each journey
  states and asserts it contains every state the map flags as WCAG-bearing and
  assigns to a tier band, and separately that it equals the map's explore band
  exactly. The containment half is one-directional by design, so without the
  equality half a journey could satisfy it while listing a state the map owes
  only at `pilot` — a cheap path more expensive than the contract asks.
- **Journey composition.** Asserts `relatedJourneys` names the other pack, that
  both journeys name the three crossing artifacts by their `<output_dir>`-relative
  paths, that the frontend journey names its four proportionality allowances, and
  that the design journey names its minimal viable thread. It also walks every
  illustrative state list under `packs/experience-design/` — the scope AC-0024
  and AC-0025 fix — asserting none
  names a state outside the 18-state set and none exceeds the `explore` subset: the journey's two transcripts and the README's copy
  of one show a five-state list including `default`, which is not a floor state,
  and a depth selector promising ten states two screens above them makes the
  pack argue with itself. No shipped lint reads any of these.

**Integration tests:** none beyond the above.
**Manual verification:** every criterion whose own line reads `*Verified by:*
Review-only`. The spec's criterion list is that record; re-enumerating it here
is what went stale on three review rounds. Each such reading happens at the
human gate. Every other claim this delivery makes is a property of a committed
artifact with a lint, a gate, or one of the assertion groups above.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise — both `JOURNEY.md` files and the two how-to trees | T4, T5, T10 | Each journey states its tier obligations and its optionality; each new capability has a how-to | The guide lints exit 0 and the tier-count test agrees with the contract |
| Current product truth — `guides/core/explanation/digital-experience-contract.md` | T9 | The page's three-tier table references the contract's annotations rather than enumerating them | The page states no per-tier field count and no per-tier field list |
| Interface compatibility — the four contract copies | T2, T6 | `check-contract-drift` exits 0; both `SKILL.md` files name their pack-local copy | All four copies byte-identical |
| Decision rationale — `docs/adr/` | T8 | An ADR records that the frontend discipline is owned by its own pack; `git diff` touches nothing else in either frozen file | ADR accepted and cited by the superseded spec's Status line |
| Operations — `build-check.yml` + `lint-ci-parity.py` | T7 | Both step names registered with a disposition; both steps above the bulk pytest step | `tools/lint-ci-parity.py` exits 0 |
| Release history — `docs/product/changelog.md` | T10 | One `##` entry per bumped pack, beneath `core`'s newest | Topmost entry per pack names its new `pack.toml` version |
| Reusable learning — `project-knowledge` seam | T10 | Receipt or recorded unavailability | Recorded at the terminal gate |

## Design (LLD)

### Design decisions

Traces to: the owner-label, depth-selector, accessibility-flag and supersession
criteria.
<!-- Owned by: T1, T2, T4, T5, T8. -->

**Risk tier keeps one home.** The value lives in the contract artifact's
frontmatter, where the frontend skill's production-tier manifest fields already
key off it. It does not become a journey `contract:` key: every existing key holds
a property of the journey, constant across runs, while tier is a property of one
piece of work, so a journey key could only restate the enum. Owner decision,
re-confirmed at intake: keep the selector in body prose and `####` sub-stages and
do not pay the five-declaration journey-contract schema cost.

**Selection is unmechanizable; consequence is not.** Nothing in the repository
knows a change's stakes, so no gate can catch a tooltip run at production depth.
What is checkable is that each journey's stated obligations match the contract's
own annotations — the drift that makes a depth selector quietly stale.

**The depth selector is a `####` sub-stage, not a human gate.** Choosing the cheap
default is the absence of a human touch, so a gate would inflate the published
`typicalSession.humanTouches` and make the fast path feel heavier than the
thorough one. The cost is that no journey lint can read it, which the spec's
Testing Strategy states rather than hides.

**Accessibility is recorded, not judged.** The map carries a per-state
WCAG-bearing flag naming the success criterion it rests on, so the accessibility
criterion has something a test can read. Without the flag the criterion is an
argument; with it, it is a lookup.

**A WCAG-bearing state may be conditional, and that is still non-waivable.** Two
of the 18 states are conditional on a named trigger rather than assigned to a
band. A conditional state binds at *every* tier when its trigger fires, so the
accessibility invariant is "assigned to `explore`, or conditional", not "assigned
to `explore`". Stating it the narrower way would force a state into a band whose
source artifacts describe it as an extension.

**The owner label needs an ADR because a frozen record points at one.** A ticked
criterion on the Shipped `digital-experience-contract` spec pins the old label.
The convention allows exactly one mutable field on a frozen record — `Status` —
and requires the pointer to name an ADR rather than the implementing spec. Its
sibling `plan.md` carries no `Status` field at all; the owner authorized adding
that one metadata line rather than leaving the pointer with one end.

### Interfaces & contracts

Traces to: the crossing-artifact criterion.
<!-- Owned by: T4, T5. -->

The crossing set is three artifacts under the approved `[design] output_dir`:
`direction/<slug>.md`, `screens/<slug>/<screen>.md`, and `tokens/<slug>.md`, all
addressed by the dependency spec. This spec names them in both journeys so an
adopter can see the handoff, and adds nothing to the read path itself.

### Failure, edge cases & resilience

Traces to: the completeness, totality and at-least-one-unconditional criteria.
<!-- Owned by: T1, T3. -->

- A state in the 18-table with no brief counterpart: expected and recorded as
  frontend-owned rather than treated as a mapping gap. Totality runs
  brief → map, never map → brief.
- The compound `success/default` line: resolves to two members, which the
  totality assertion admits explicitly.
- A tier band left empty by the derivation: fails the at-least-one-unconditional
  criterion, which is the signal the partition is wrong rather than the criterion.

### Quality attributes (NFRs)

Traces to: the WCAG-bearing and no-band-omits criteria.
<!-- Owned by: T1, T2, T3. -->

WCAG 2.2 AA is the bar, and the map's flag names the success criterion each
`yes` rests on, so a reviewer can check the flag rather than re-derive it. The
test reads the flag; a wrong flag is a review finding, not a test failure, and
that boundary is deliberate — a test that judged accessibility would be a test
nobody could make green.

## Tasks

### T1: Derive the state map and the tier bands

**Depends on:** none

**Touches:** docs/specs/frontend-experience-composition/notes/verification-ledger.md

**Tests:**
- No stub (exploration). The output is a recorded derivation, not code.

**Approach:**
- Walk all 18 states in the `### 3. State matrix` table of
  `frontend-engineering/SKILL.md` against the seven state lines in
  `user-flow/assets/screen-brief-template.md` and the six base states plus gated
  extension in `design-review/references/quality-floor.md`.
- Assign each of the 18 to a tier band or mark it conditional on a named trigger,
  and record per state whether its absence fails WCAG 2.2 AA, naming the success
  criterion behind each `yes`.
- Starting hypothesis, expected to move: the states a screen brief already carries
  plus the three WCAG-bearing environment states form the explore band; the
  data-shape and authority states join at pilot; `offline` joins at production;
  `destructive-confirmation` is conditional on an irreversible primary action at
  every tier. Cumulative field obligations 10 / 25 / 32.
- Record what moved from the hypothesis and why.

**Done when:** the verification ledger holds the derived partition, its
per-state WCAG flags with named success criteria, and the delta from the
hypothesis. No test runs here, because the artifact the tests read does not
exist until T2.

### T2: Write the map and the owner label into all four contract copies

**Depends on:** T1

**Touches:** packs/*/.apm/skills/*/references/digital-experience-contract.md

**Tests:**
- Goal-based: `python3 tools/repo/check_contract_drift.py --root .` exits 0 —
  all four copies byte-identical.
- Goal-based: the frontend section heading reads
  `## Frontend Engineering [owner: frontend-engineering]`.
- Goal-based: `python3 tools/lint-experience-agnostic.py` exits 0 (AC-0040), so
  this task introduces no value literal or platform token into that tree. The
  tool takes no arguments and always scans `packs/experience-design`. That the
  map is present is AC-0008 and AC-0001; this command decides neither.

**Approach:**
- Edit one copy, then write it to the other three from that source so byte
  equality is produced rather than hand-matched.
- Place the map under `States and Permissions`, after its existing
  `<!-- Required: -->` annotation so the annotation stays the first non-blank line
  after the heading.

**Done when:** every check this task's `Tests:` declares passes.

### T3: State-map completeness and accessibility tests

**Depends on:** T2

**Touches:** tests/roster/test_experience_state_coverage_map.py, docs/specs/frontend-experience-composition/notes/verification-ledger.md

**Tests:**
- TDD: the completeness-and-totality assertions, proven red against a scratch copy
  of the map with one state removed, one duplicated, and one brief line unmapped.
- TDD: the band-assignment assertions, proven red by emptying a tier band and by
  stripping a conditional row's trigger.
- TDD: the accessibility-preservation assertions, proven red by moving a
  WCAG-flagged state out of `explore`, by blanking a flag, and by dropping a
  success-criterion citation.

**Approach:**
- One roster test file holding all three assertion groups, parsing the contract,
  the 18-state table, and the brief template. It reads the artifacts at their real paths, so a
  mutation is proven against an injected copy of the text rather than by editing
  the tree.

**Done when:** every assertion group this task's `Tests:` declares is green
against the real artifacts and red against its mutations, and the mutation output
is recorded in the verification ledger.

### T4: Frontend journey — depth selector, allowances, crossing artifacts

**Depends on:** T3

**Touches:** packs/frontend-engineering/JOURNEY.md, web/src/content/journeys/frontend-engineering.md, docs/specs/frontend-experience-composition/notes/verification-ledger.md

**Tests:**
- Goal-based: enumerate every existing assertion over
  `packs/frontend-engineering/JOURNEY.md` in the ledger, then run the suites
  AC-0035 names — all four, the repository-level one included — green.
- Goal-based: `tools/lint-pack-journeys.py` and `tools/lint-journey-contract.py`
  exit 0.
- Goal-based: the committed web copy is byte-equal to a fresh
  `python3 tools/build-site.py --journeys-only` run.

**Approach:**
- Enumerate the pins first: the byte-exact `PINNED_SKIP_COST` block over the
  `accept-frontend-evidence` gate, the `- **Reviewer does:**` literals, the
  `review-frontend-implementation` block literal, the `youProvide` breakpoint and
  minimum-width literals, and the negative assertion that `whatChanges` does not
  contain `independent diff read`. If an allowance belongs in a stage carrying the
  skip-cost pin, that edit takes this spec's `Ask first` route.
- Add the depth selector as a `####` sub-stage inside stage 1, after that stage's
  `**State:**` label, stating the explore tier's field count, state subset,
  capture count, gates, and what it drops. Write the state subset as one
  backticked, comma-separated list on a single line, because T7's
  explore-subset assertion parses it.
- Lift the four allowances into the stages that own them; name the three crossing
  artifacts in stage 2, which today asks for "the surface brief" as if from nowhere.
- Regenerate the web copy in this task.

**Done when:** every check this task's `Tests:` declares passes, and the
committed web copy diff is empty.

### T5: Design journey — optionality, minimal thread, reciprocal link

**Depends on:** T4

**Touches:** packs/experience-design/JOURNEY.md, packs/experience-design/DESIGN.md, packs/experience-design/README.md, web/src/content/journeys/experience-design.md, tests/roster/test_experience_journey_composition.py, docs/specs/frontend-experience-composition/notes/verification-ledger.md

**Tests:**
- Goal-based: enumerate every existing assertion over
  `packs/experience-design/JOURNEY.md` in the ledger, then run
  `tools/test_journey_editorial_decisions.py` green. T4's run of it precedes this
  task's edit, so it does not cover this file; the suite pins every journey's
  `humanGates` and the eyebrow and transcript sets.
- Goal-based: the three journey lints exit 0, including parity, which requires the
  frontmatter skill list to stay at twenty entries.
- TDD: every row of the say-this table carries exactly one optionality value,
  proven red by blanking one row's value and by giving another two.
- TDD: the `design-system` and `content-design` rows equal their how-to tables —
  `Optional` and `Required` respectively — read from both tables rather than
  pinned, proven red by flipping one.
- Goal-based: the committed web copy is byte-equal to a fresh regeneration.
- Review-only (AC-0023): `packs/experience-design/DESIGN.md`'s claim about
  skipping a step and the minimal viable thread below it do not contradict each
  other — the skipping sentence names what a shortened thread costs rather than
  asserting that no step may be dropped. Read at the human gate; whether two
  sentences contradict is not parser-decidable.

**Approach:**
- Add a `Needed?` column to the say-this table carrying exactly one of
  `Required`, `Optional`, `Choose one` per row — the table is the structure the
  criterion quantifies over, chosen because it is the one enumeration a check can
  walk and it already lists the skills an adopter types.
- Resolve each optionality toward the guide that owns it, per row.
- Add the minimal viable thread and the depth selector as `####` sub-stages, each
  after its parent stage's `**State:**` label. Write the explore state subset in
  the same single-line backticked form T4 uses, because one parser reads both.
- Add `frontend-engineering` to `relatedJourneys` and name the three crossing
  artifacts.
- Reconcile the sentence in `DESIGN.md` two lines above the minimal thread that
  argues against shortcuts while the section below it names one.
- Align the three illustrative state lists — `JOURNEY.md` twice and
  `README.md` once — with the `explore` subset. All three currently name
  `default`, which the quality floor does not carry, and omit `partial` and
  `disabled`. No test pins them today, which is why the walk reaches all three
  rather than the one the journey edit happens to touch.

**Done when:** every assertion group and check this task's `Tests:` declares is
green — the two say-this assertions included — the web copy diff is empty, and
`DESIGN.md` no longer argues against the thread it names.

### T6: The contract is loaded by a skill in each pack

**Depends on:** T3

<!-- T3, not T2: this task's second `Tests:` bullet runs the state-coverage
     assertions, and T3 is what creates that module. As a bare sibling of T2
     this task could be scheduled into the same wave and gate a file that does
     not exist. T2 stays reachable through T3. The rationale lives here rather
     than on the field itself: the scheduler parses every bare task id in that
     line, so prose naming other tasks reads as extra edges — stating it inline
     made this task depend on itself. -->

**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md, packs/experience-design/.apm/skills/design-review/SKILL.md, docs/specs/frontend-experience-composition/notes/verification-ledger.md

**Tests:**
- Goal-based: each of the two `SKILL.md` files names its pack-local
  `references/digital-experience-contract.md` as a file it loads, at the step that
  uses it.
- Goal-based: the state-coverage-map assertion groups run green after this task's
  edit, and the run is recorded in the ledger. This task writes into
  `### 3. State matrix`, the heading those assertions parse, and it is T3's
  sibling — so T3's own run can precede the last edit to what it asserts over.

**Approach:**
- Name it at the state-matrix step in `frontend-engineering/SKILL.md` and at the
  quality-floor step in `design-review/SKILL.md`, because those are the steps the
  state-coverage map serves.

**Done when:** every check this task's `Tests:` declares passes.

### T7: Tier-count test and CI wiring for both new tests

**Depends on:** T5, T6

**Touches:** tests/roster/test_experience_journey_composition.py, .github/workflows/build-check.yml, tools/lint-ci-parity.py

<!-- T5 creates this module for its say-this assertions; T7 extends it with the
     groups that need both journeys to exist. Splitting it would owe a second
     CI step for assertions sharing the same parses. -->

<!-- Three of the section's assertion groups, one file: every one reads the
     contract and both journeys, so splitting them would duplicate the same
     parses and owe a third CI step. -->

**Tests:**
- TDD: the tier-count agreement assertion, proven red by mutating one journey's
  stated count, green against the real artifacts now both journeys state theirs.
- TDD: the explore-subset assertions, proven red by removing one WCAG-flagged
  state from a journey's stated subset, and again by adding a `pilot` state to it.
- TDD: the journey-composition assertions, proven red by removing the
  `relatedJourneys` entry, a crossing-artifact path, one proportionality
  allowance, and the minimal-thread heading in turn.
- Goal-based: `.github/workflows/build-check.yml` names a step per new test file,
  each above the job's bulk `pytest tests/ -q` step, and
  `python3 tools/lint-ci-parity.py --root .` exits 0.

**Approach:**
- Compute the cumulative sum per tier from the contract; do not store 10 / 25 / 32
  in the test.
- Add one `build-check.yml` step per new test file. Each needs **both** roster
  axes, because `STEP_DISPOSITION` is `set(_LOCAL_STEP_DISPOSITION) | set(_STEP_PHASE)`
  and a step present in one and absent from the other raises
  "has no phase-and-dependency axis entry": a `_LOCAL_STEP_DISPOSITION` entry of
  the `LOCAL("test-after-build-check")` shape, and membership in the
  `_GATE_MAIN_CHECKS` tuple, which synthesizes the phase entry. Neither step is
  in the provisioning matrix, so neither needs a `_CHECK_DEPENDENCIES` or
  `_CHECK_EVIDENCE` entry; adding one would claim a dependency the matrix does
  not record.
- Place both above the bulk step: the bulk step already collects them, so
  placement is what buys failure attribution rather than reach.

**Done when:** every assertion group this task's `Tests:` declares is green and
its mutations red, the parity lint exits 0 with both step names registered, and a
YAML parse confirms both step indices are lower than the bulk step's.

### T8: ADR and the supersession pointer

**Depends on:** T2

**Touches:** docs/adr/, docs/specs/digital-experience-contract/spec.md, docs/specs/digital-experience-contract/plan.md

**Tests:**
- Goal-based: the two form greps AC-0004 and AC-0005 pin, run verbatim from
  those criteria.
- Goal-based: the commands AC-0003 and AC-0047 pin, run verbatim from those
  criteria rather than restated here — the record exists and passes the shape
  lint, and its `## Decision` section names the pack.
- Goal-based: `git diff` over `docs/specs/digital-experience-contract/spec.md`
  touches only its `Status` line, and over its `plan.md` adds exactly one line,
  which is the `Status` line.

**Approach:**
- Use the `new-adr` skill, allocating the number from current repository state.
  The owner has already settled this decision, so the record ships `Accepted`
  rather than `Proposed`; AC-0003 reads the status because the shape lint admits
  either.
- Set `docs/specs/digital-experience-contract/spec.md`'s Status to the
  `Shipped (superseded in part by ADR-NNNN — …; everything else stands)` form and
  its plan's to the `Done (…)` form. Its plan carries no `Status` field, so this
  adds that one metadata line under the owner authorization the spec's `Never do`
  rule records; leave the ticked criterion body untouched.

**Done when:** every check this task's `Tests:` declares passes.

### T9: The fifth tier table

**Depends on:** T2

**Touches:** guides/core/explanation/digital-experience-contract.md

**Tests:**
- Goal-based: the negated grep AC-0016 pins, run verbatim from the criterion
  rather than restated here — two copies of one pattern decided AC-0016
  differently once already. It exits 0 only when the page states no per-tier
  field count.
- Review-only (AC-0017): the three-tier table's `What's required` column
  references the contract's annotations rather than enumerating them. Read at
  the human gate; no parser decides whether prose references or restates.

**Approach:**
- The page says seven fields are required at explore tier where the contract
  annotates ten, and its own Explore row lists ten. Rewrite it to reference the
  contract rather than restate a count, which removes the home rather than
  correcting it and going stale again.
- Retarget its two citations of the deprecated `tools/check-contract-drift.py`
  shim at the real `tools/repo/check_contract_drift.py`.

**Done when:** every check this task's `Tests:` declares passes, the review-only
reading included.

### T10: Guides and release surface

**Depends on:** T1-T9

**Touches:** guides/, packs/*/pack.toml, packs/*/.claude-plugin/plugin.json, packs/*/.apm/skills/*/evals/evals.json, docs/product/changelog.md, .claude-plugin/marketplace.json

**Tests:**
- Goal-based: `tools/lint-guidebook-steps.py` and `tools/check-guide-index.py` exit 0.
- Goal-based: each of the four contract-carrying packs — `product-strategy`,
  `product-engineering`, `experience-design`, `frontend-engineering` — states a
  `pack.toml` version differing from its pre-change value, with `plugin.json`
  agreeing (AC-0042); `marketplace.json` is byte-identical to a fresh unforced
  self-host run (AC-0041).
- Goal-based: `python -m agentbundle catalogue verify --root .` exits 0
  (AC-0043). It and `catalogue self-host --check` are the two commands that see
  a stale `.claude/` or `.agents/` projection; `catalogue lint --deep`,
  `lint-ruff`, `lint-mypy` and the pack suites all pass while it is stale.
- Goal-based: the topmost `##` heading for each of those four packs names the
  version its `pack.toml` now states (AC-0045).
- Goal-based: the topmost-entry read AC-0048 pins, run verbatim from the
  criterion — an unqualified read goes green off an older entry for three of
  the four packs.
- Goal-based: the heading-order read AC-0046 pins, run verbatim from the
  criterion — it diffs against `origin/main` to identify the added set, which
  the current file alone cannot supply.

**Approach:**
- Ship the depth-selection how-to for each pack with its index row.
- Bump `product-strategy`, `product-engineering`, `experience-design` and
  `frontend-engineering` in `pack.toml` and `plugin.json` only, at the patch
  level `packs/AGENTS.md` requires for changed content, then regenerate
  `marketplace.json` under the ordering Constraints states. These are the four
  `PACK_ANCHORS` the drift checker names, which is why the criteria quantify
  over them by name.
- Refresh an `evals/evals.json` case in each of the four contract-carrying
  packs, not only the two whose `SKILL.md` changes (AC-0044): `packs/AGENTS.md`
  states that obligation per pack for any non-cosmetic update, and bumping all
  four declares all four non-cosmetic. For `product-strategy` and
  `product-engineering` the case covers the contract copy their skill reads.
- Run self-host after the pack edits, per `packs/AGENTS.md` § Self-hosting
  projection, and prove the result with `catalogue verify` and
  `catalogue self-host --check` both exiting 0 (AC-0043). Measured: only `core`
  has declared host projections in this tree, so T2's and T6's edits to the four
  non-core packs produce no `.claude/` or `.agents/` delta to commit — appending
  to a `frontend-engineering` `.apm` source leaves both commands at 0. What this
  delivery does owe is the `marketplace.json` regeneration, which reads the
  bumped versions (AC-0041).
- Route learnings through the `project-knowledge` seam.

**Done when:** every check this task's `Tests:` declares passes, including the
heading-order read, and `git status` is clean.

## Rollout

No runtime component and no migration. The contract's four copies move together,
so no adopter sees a partial state. An adopter on the previous pack version keeps
working: the depth selector is additive guidance and the map adds a section to a
template rather than changing a required field. Deployment sequencing is the
commit order alone — the marketplace regeneration must follow the version bumps,
because it reads them.

## Risks

- **The derivation contradicts the hypothesis.** Expected; the criteria state
  invariants and the ledger records the delta.
- **A tier band ends up empty.** Fails the at-least-one-unconditional criterion,
  which is the correct signal.
- **An allowance belongs in a pinned stage.** T4 enumerates the pins first and
  routes a skip-cost edit through `Ask first` rather than discovering it as a
  failure.
- **The map trips the agnosticism lint.** State names clear its patterns, but the
  lint runs first in T2 rather than at the end.
- **A named roster step lands below the bulk pytest step.** It would satisfy the
  parity lint and attribute nothing. T7 verifies placement by index, not by the
  lint's exit code.

## Changelog

<!-- Approvals only. -->

- 2026-09-23: spec approved by eugenelim
- 2026-09-23: plan approved by eugenelim
