# Plan: frontend-experience-composition

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (export boundary, version bump rule,
  eval-harness rule) and `docs/CONVENTIONS.md` § 5b, § Phase-slice planning
  (:1128), and the frozen-record rules at :111 and :149-176. Analogous
  implementations: `packs/core/JOURNEY.md:180` for an optional `####` sub-stage
  that both journey lints tolerate, and `guides/experience-design/how-to/establish-design-intent.md:30-34`
  for the `Required | Optional | Choose one` column vocabulary this change adopts
  into a journey. Construction path: the two new tests join the existing journey
  and contract gates, with `tools/lint-ci-parity.py:360-372` as the disposition
  shape a new `build-check.yml` step must match. Named uncertainty: the state
  partition and tier bands are derived in T1 against the real artifacts, not
  settled here.

> **Plan contract:** implementation strategy. It may change substantively only
> while Status is `Drafting`. Execution observations belong in
> `notes/verification-ledger.md`.

## Approach

Ten tasks in one chain. The order is forced by the two new tests: the state-map
test can close as soon as the map exists, but the tier-count test compares the
contract against *both* journeys, so it cannot be green until both have stated
their counts. Putting it after both, rather than making it a sibling obligation
of each, is what stops it being a check that is red or vacuous at every
intermediate boundary.

T1 is an exploration, not a transcription: it derives the partition from the real
tables rather than implementing a partition stated here. The criteria state the
invariants, so a derivation that moves is expected and costs no amendment.

Review shape is **MIXED**. T1, T2 and T6 are deep; T4 and T5 are prose edits over
files with thirteen existing assertions between them, which is mechanical but
unforgiving.

## Constraints

- The tier-count test computes each tier's obligation as a *cumulative* sum,
  because `<!-- Required: explore+ -->` means that tier and above. The label
  counts are 10 / 15 / 7 and the obligations are 10 / 25 / 32; a test comparing
  label counts pins a ladder where production is cheaper than pilot.
- `packs/frontend-engineering/JOURNEY.md` is pinned by thirteen assertions across
  three suites. T4 enumerates them before editing, not after a failure.
- The `check-contract-drift` step compares bytes across four copies, so T2 writes
  three from the first rather than editing four.
- The state-coverage map ships inside `packs/experience-design/` too, so it may
  carry no value literal. State *names* are safe: `reduced-motion` is legal and
  only `prefers-reduced-motion` matches the lint.

## Construction tests

Three assertions across two new test files. Both files are repository-level —
they read across two packs and the guides — so they go to the roster suite, which
means T7 must wire them into CI or they run on no pull request.

- **State-map completeness and totality.** Parses the map, the 18-state table from
  `frontend-engineering/SKILL.md`, and the screen-brief template's state lines.
  Asserts the map's state set equals the 18-state set with no duplicates, and that
  every template state line resolves to at least one member — admitting the one
  line that names two. Fails on an added, dropped, renamed or duplicated state,
  and on a brief state left unmapped.
- **Accessibility preservation.** Asserts the map records a WCAG-bearing flag for
  every state, and that no tier band omits a state flagged true. The test reads
  the recorded flag rather than judging accessibility, which is what makes the
  predicate decidable.
- **Tier-count agreement.** Computes each tier's cumulative `Required:` annotation
  count from the contract and compares it with the count each journey states.
  Fails when a field is re-tiered and a journey's promise goes stale.

## Durable-output map

| Durable output | Tasks | Evidence |
| --- | --- | --- |
| User-facing promise | T4, T5, T10 | Journey lints; tier-count test; guide lints |
| Current product truth | T9 | No tier claim contradicts the contract |
| Interface compatibility | T2, T6 | `check-contract-drift` passes; both skills name their copy |
| Decision rationale | T8 | ADR accepted; frozen spec's Status cites it |
| Operations | T7 | `tools/lint-ci-parity.py` exits 0 with both step names |
| Release history | T10 | Topmost entry per bumped pack |
| Reusable learning | T10 | `project-knowledge` receipt or recorded unavailability |

## Design (LLD)

### Design decisions

**Risk tier keeps one home.** The value lives in the contract artifact's
frontmatter, where the frontend skill already reads it. It does not become a
journey `contract:` key: every existing key holds a property of the journey,
constant across runs, while tier is a property of one piece of work, so a journey
key could only restate the enum.

**Selection is unmechanizable; consequence is not.** Nothing in the repository
knows a change's stakes, so no gate can catch a tooltip run at production depth.
What is checkable is that each journey's stated obligations match the contract's
own annotations — the drift that makes a depth selector quietly stale.

**The depth selector is a `####` sub-stage, not a human gate.** Choosing the cheap
default is the absence of a human touch, so a gate would inflate the published
`typicalSession.humanTouches` and make the fast path feel heavier than the
thorough one. The cost is that no journey lint can read it, which the Testing
Strategy states rather than hides.

**Accessibility is recorded, not judged.** The map carries a per-state
WCAG-bearing flag so the accessibility criterion has something a test can read.
Without the flag the criterion is an argument; with it, it is a lookup.

**The owner label needs an ADR because a frozen record points at one.** A ticked
criterion on the Shipped `digital-experience-contract` spec pins the old label.
The convention allows exactly one mutable field on a frozen record — `Status` —
and requires the pointer to name an ADR rather than the implementing spec.

### Interfaces & contracts

The crossing set is three artifacts under the approved `[design] output_dir`:
`direction/<slug>.md`, `screens/<slug>/<screen>.md`, and `tokens/<slug>.md`, all
addressed by the dependency spec. This spec names them in both journeys so an
adopter can see the handoff, and adds nothing to the read path itself.

### Failure, edge cases & resilience

- A state in the 18-table with no brief counterpart: expected and recorded as
  frontend-owned rather than treated as a mapping gap.
- The compound `success/default` line: resolves to two members, which the
  totality assertion admits explicitly.
- A tier band left empty by the derivation: fails the at-least-one-unconditional
  criterion, which is the signal the partition is wrong rather than the criterion.

## Tasks

### T1: Derive the state map and the tier bands

**Depends on:** none

**Tests:**
- No stub (exploration). The output is a recorded derivation, not code.

**Approach:**
- Walk all 18 states in `frontend-engineering/SKILL.md:225-242` against the seven
  state lines in `user-flow/assets/screen-brief-template.md:45-52` and the six
  base states plus gated extension in `design-review/references/quality-floor.md:17-45`.
- Assign each of the 18 to a tier band or mark it conditional on a named trigger,
  and record per state whether its absence fails WCAG 2.2 AA.
- Starting hypothesis, expected to move: the states a screen brief already carries
  plus the three WCAG-bearing environment states form the explore band; the
  data-shape and authority states join at pilot; `offline` joins at production;
  `destructive-confirmation` is conditional on an irreversible primary action at
  every tier. Cumulative field obligations 10 / 25 / 32.
- Record what moved from the hypothesis and why.

**Done when:** the verification ledger holds the derived partition, its
per-state WCAG flags, and the delta from the hypothesis. No test runs here,
because the artifact the tests read does not exist until T2.

### T2: Write the map and the owner label into all four contract copies

**Depends on:** T1

**Tests:**
- Goal-based: the `check-contract-drift` step passes — all four copies byte-identical.
- Goal-based: the frontend section heading names `frontend-engineering` as owner.
- Goal-based: `tools/lint-experience-agnostic.py` exits 0 with the map present.

**Approach:**
- Edit one copy, then write it to the other three from that source so byte
  equality is produced rather than hand-matched.
- Place the map under `States and Permissions`, after its existing
  `<!-- Required: -->` annotation so the annotation stays the first non-blank line
  after the heading.

**Done when:** the drift step and the agnosticism lint both pass.

### T3: State-map completeness and accessibility tests

**Depends on:** T2

**Tests:**
- TDD: the completeness-and-totality assertion, proven red against a scratch copy
  of the map with one state removed.
- TDD: the accessibility-preservation assertion, proven red against a scratch copy
  with a WCAG-flagged state dropped from a band.

**Approach:**
- One roster test file holding both assertions, parsing the contract, the 18-state
  table, and the brief template.

**Done when:** both assertions are green against the real artifacts and red
against their mutations.

### T4: Frontend journey — depth selector, allowances, crossing artifacts

**Depends on:** T3

**Tests:**
- Goal-based: enumerate the thirteen existing assertions over
  `packs/frontend-engineering/JOURNEY.md` and run all three pinning suites green.
- Goal-based: `tools/lint-pack-journeys.py` and `tools/lint-journey-contract.py` pass.
- Goal-based: the committed web copy is byte-equal to a fresh
  `build-site.py --journeys-only` run.

**Approach:**
- Enumerate the pins first: the byte-exact `PINNED_SKIP_COST` block over the
  `accept-frontend-evidence` gate, the `- **Reviewer does:**` literals, the
  `review-frontend-implementation` block literal, the `youProvide` breakpoint and
  minimum-width literals, and the negative assertion that `whatChanges` does not
  contain `independent diff read`. If an allowance belongs in a stage carrying the
  skip-cost pin, that edit takes this spec's `Ask first` route.
- Add the depth selector as a `####` sub-stage inside stage 1, after that stage's
  `**State:**` label, stating the explore tier's field count, state subset,
  capture count, and which gates run.
- Lift the four allowances into the stages that own them; name the three crossing
  artifacts in stage 2, which today asks for "the surface brief" as if from nowhere.
- Regenerate the web copy in this task.

**Done when:** all three pinning suites and both journey lints pass, and the web
copy diff is empty.

### T5: Design journey — optionality, minimal thread, reciprocal link

**Depends on:** T4

**Tests:**
- Goal-based: the three journey lints pass, including parity, which requires the
  frontmatter skill list to stay at twenty entries.
- Goal-based: `design-system` and `content-design` carry the same optionality as
  their how-to tables.
- Goal-based: the committed web copy is byte-equal to a fresh regeneration.

**Approach:**
- Add a `Needed?` column to the say-this table carrying exactly one of
  `Required`, `Optional`, `Choose one` per row — the table is the structure the
  criterion quantifies over, chosen because it is the one enumeration a check can
  walk and it already lists the skills an adopter types.
- Resolve both contradictions toward the guides, which mark them Optional.
- Add the minimal viable thread and the depth selector as `####` sub-stages, each
  after its parent stage's `**State:**` label.
- Add `frontend-engineering` to `relatedJourneys` and name the three crossing
  artifacts.
- Reconcile the sentence in `DESIGN.md` two lines above the minimal thread that
  argues against shortcuts.

**Done when:** the three lints pass and the web copy diff is empty.

### T6: The contract is loaded by a skill in each pack

**Depends on:** T2

**Tests:**
- Goal-based: each of the two `SKILL.md` files names its pack-local
  `references/digital-experience-contract.md` as a file it loads.

**Approach:**
- `frontend-engineering/SKILL.md` and `experience-design`'s `design-review/SKILL.md`
  each name their copy at the step that uses it, so the file stops being guarded
  content nothing reads.

**Done when:** both names resolve to an existing pack-local path.

### T7: Tier-count test and CI wiring for both new tests

**Depends on:** T5, T6

**Tests:**
- TDD: the tier-count agreement assertion, proven red by mutating one journey's
  stated count, green against the real artifacts now both journeys state theirs.
- Goal-based: `.github/workflows/build-check.yml` names a step per new test file
  and `tools/lint-ci-parity.py` exits 0.

**Approach:**
- Compute the cumulative sum per tier from the contract; do not store 10 / 25 / 32
  in the test.
- Add one `build-check.yml` step per new test file with a matching
  `STEP_DISPOSITION` entry of the `LOCAL("test-after-build-check")` shape. Without
  both, a roster test runs under `pytest tests/` and on no pull request.

**Done when:** the tier-count test is green, its mutation red, and the parity lint
exits 0 with both step names registered.

### T8: ADR and the supersession pointer

**Depends on:** T2

**Tests:**
- Goal-based: the frozen spec's and plan's `Status` fields match the convention's
  exact form and name the new ADR.
- Goal-based: `git diff` shows no change to either frozen file outside its
  `Status` line.

**Approach:**
- Author the ADR recording that the contract's frontend discipline is owned by its
  own pack rather than `core`.
- Set `docs/specs/digital-experience-contract/spec.md`'s Status to
  `Shipped (superseded in part by ADR-NNNN — the frontend section's owner label; everything else stands)`
  and its plan's to the `Done (…)` form. Leave the ticked criterion body untouched:
  the convention permits no body edit, including an appended line.

**Done when:** both Status lines carry the pointer and the diff touches nothing else.

### T9: The fifth tier table

**Depends on:** T2

**Tests:**
- Goal-based: no tier claim in `guides/core/explanation/digital-experience-contract.md`
  contradicts the contract's annotations.

**Approach:**
- That page says seven fields are required at explore tier where the contract
  annotates ten, and its own Explore row lists ten. Rewrite it to reference the
  contract rather than restate a count, which removes the home rather than
  correcting it and going stale again.
- Correct its two citations of `tools/check-contract-drift.py` to the real
  `tools/repo/check_contract_drift.py`.

**Done when:** the page states no count the contract owns.

### T10: Guides and release surface

**Depends on:** T1 through T9

**Tests:**
- Goal-based: `tools/lint-guidebook-steps.py` and `tools/check-guide-index.py` exit 0.
- Goal-based: for each bumped pack, `pack.toml` and `plugin.json` state the same
  version; `marketplace.json` is byte-identical to a fresh self-host run.
- Goal-based: `agentbundle catalogue verify --root .` exits 0.
- Goal-based: the topmost heading per bumped pack names its new version.

**Approach:**
- Ship the depth-selection how-to with its index row.
- Bump the four packs carrying a contract copy in `pack.toml` and `plugin.json`
  only; regenerate `marketplace.json` by self-host. Refresh every edited skill's
  `evals/evals.json`.
- Route learnings through the `project-knowledge` seam.

**Done when:** the four checks pass and `git status` is clean.

## Rollout

No runtime component and no migration. The contract's four copies move together,
so no adopter sees a partial state. An adopter on the previous pack version keeps
working: the depth selector is additive guidance and the map adds a section to a
template rather than changing a required field.

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

## Changelog

- 2026-09-16 — Initial plan. This is the composition and depth half of a two-spec
  split; the addressing half is `docs/specs/design-output-addressing/`, which this
  spec depends on for the three crossing artifacts' addresses. Task order was set
  so the tier-count test lands after both journeys state their counts, rather than
  being a sibling obligation of each — the defect that made the combined plan's
  equivalent check red or vacuous at every intermediate boundary.
