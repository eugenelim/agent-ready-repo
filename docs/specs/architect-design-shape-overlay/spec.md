# Spec: architect-design system-shape overlay

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0118
- **Brief:** none
- **Discovery:** docs/product/intents/architect-design-conditional-overlays.md
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

An author running `architect-design` loads the system-shape concept whose
coordination mechanism an open decision of their design actually turns on, so a
shape-specific concern reaches the document without the author having to think
of it. The six shapes the corpus already ships become selectable by the router
rather than reachable only when the author happens to name one.

## What Changes

- A system-shape routing axis — `packs/architect/.apm/skills/architect-design/SKILL.md`, in the Stage-0 concept step beside the workload axis, delimited by its own markers.
- A shape-axis eval case — `packs/architect/.apm/skills/architect-design/evals/evals.json`.
- A construction suite for the axis — `packs/architect/tests/skills/architect-design/test_shape_axis_routing.py`.
- A dated erratum homing the cross-slice names — `docs/adr/0118-architect-design-scope-routed-model-first-templates.md`.
- The intent's amendment — `docs/product/intents/architect-design-conditional-overlays.md`. Not a task output: the probe ran in this session and the intent owns its verdict, its validation hooks and the `S2`/`S3` gating.
- The spec's workspace registration — `workspace.toml`. Not a task output; its collection tracks this spec's Status and the engine refuses a mismatch.
- The overlay probe's record, committed as evidence rather than as an output of any task here — `docs/specs/architect-design-shape-overlay/notes/probe/`. The probe is the intent's, per its `## Decomposition`; it ran on 2026-09-20 and the intent's `**Verdict:**` line carries its post-run state. This delivery carries the files so the result is readable beside the axis it was run against — which was T1's working-tree draft of the region, two sentences away from the delivered bytes; `notes/probe/method.md` names both.
- A patch version bump and its release entry — `packs/architect/pack.toml`, `packs/architect/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Release history | A pack content change publishes to adopters, and the `/now/` projection is a pure parser over the changelog's bytes | `docs/product/changelog.md` | architect pack maintainer | A free-standing `##` entry placed as AC-0096 states, with a recorded Highlights decision | The Highlights decision is written, not left to a reader |
| Current product truth | The skill's own procedure is the adopter-facing statement of how routing works | `packs/architect/.apm/skills/architect-design/SKILL.md` | architect pack maintainer | The shape-axis region and its eval case | The eval harness exercises the axis |
| Decision rationale | S3's trigger reads the system shape, so the shape-axis names cross a slice boundary and ADR-0118 is the one place cross-slice names are settled | `docs/adr/0118-architect-design-scope-routed-model-first-templates.md` § Errata | architect pack maintainer | A dated erratum naming the open-decision trigger, the whole-load rule, and the receipt value | A later slice can read all three names without reading this spec |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Delimit the shape axis with its own HTML-comment markers and locate every assertion by those markers, never by a heading or a step number.
- State the shape rule directly in `packs/`, citing no catalogue-internal record.
- Bump `pack.toml` and `.claude-plugin/plugin.json` together under `packs/AGENTS.md` § Version bump rule, then regenerate `marketplace.json` with `FORCE=1 make build-self`.
- Decide the changelog entry's Highlights disposition under `packs/AGENTS.local.md` § Marketplace and release pipeline, step 4, which owns both the decision and where a no-change verdict is recorded.
- Run `python3 -m pytest packs/architect/tests/skills/architect-design/ -q` before pushing, because that path runs on the pull request.
- Update this spec from the overlay probe's findings — the paired-design comparison the intent predeclares, one subsystem design authored twice against one problem, once with the shape overlay active and once without — before T5 releases the pack, and re-run whichever gates that update touches. T5's release is the boundary; T1 landing in the branch is not.

### Ask first

- Any edit to the two equality-pinned ends of the skill description — the opening invocation-and-triggers string, or the closing refusal. Needing one means scope work has grown into routing.

### Never do

- Add an OKF concept file, category, or index. The corpus ontology is pinned by exact equality and the axis is skill routing.
- Edit inside the `agentbundle:output-rendering` markers; `tools/add-rendering-directives.py` regenerates that span byte-for-byte.
- Enumerate the six shape names in `SKILL.md`, in either their file-stem or their index-title form. The generated index owns that list, and a second copy drifts. `test_the_skill_does_not_enumerate_the_shape_names` guards this rail and reds on either form; it discharges no criterion and exists only for this rule.

## Testing Strategy

Each group below maps to one `###` subsection of the criteria. Identifiers are
assigned once and never reflowed.

- **The shape axis in the skill (AC-0084, AC-0085, AC-0086, AC-0087, AC-0088,
  AC-0089): TDD.** Every one is a property of a marker-delimited region of a
  shipped file, so a construction test reds before the region exists and
  passes after. AC-0089 is what makes the other five mean anything: without
  the ordering and single-occurrence assertions, a second region could satisfy
  the text checks while the routed one was deleted.

  **The assertions pin more than the criteria require, deliberately.** Bare
  tokens did not survive a negation of the rule they belong to — `never
  record \`no shape lens selected\`` kept the token while inverting the rule —
  so the shipped assertions pin contiguous phrases and, in places, literals
  the criterion does not name. The consequence is stated rather than
  enumerated, because the enumeration is over an open set and two rounds of
  listing it produced a list that was still incomplete: **a correct rewording
  of the region can red one of these tests, and when that happens the test is
  what changes, not the region.** AC-0084 and AC-0089 are the exceptions —
  each pins exactly the literal its criterion names.

- **The eval harness (AC-0090): TDD.** T2 discharges it with a committed
  assertion in `test_shape_axis_routing.py` that reads the case and checks the
  concept path it names exists on disk, so the check ships with the change
  rather than being run once. Whether a model then routes correctly is what
  the eval itself measures at run time, not what this criterion decides.

  **The assertion pins more than AC-0090 requires, in the same way and for
  the same reason.** It asserts literal substrings the criterion does not
  name, requires a named path in the projected corpus as well as the source
  tree, and selects the case by id. Each catches something real — an
  unopenable path, a later case silently capturing the assertions — and each
  can red an eval file that satisfies AC-0090 as written. It is loose in one
  direction too: the criterion wants one path that exists, so a hallucinated
  path beside a real one passes.

- **The cross-slice names (AC-0099, AC-0101): goal-based check.** One read of
  ADR-0118's `## Errata` section decides whether the names are there, and a
  literal-token comparison against the skill region decides whether the two
  copies agree.
- **Release closure (AC-0094, AC-0095, AC-0096): goal-based check,
  delivery-time only.** Version equality is decided by
  `tests/conformance/test_pack_metadata.py`, `marketplace.json` by
  regeneration, and the changelog entry by three artifacts:
  `test_every_changelog_section_is_separated` and
  `test_no_projected_release_heading_lives_under_an_unreleased_region` in
  `tools/test_build_site_routing.py` for separation and unreleased-nesting,
  and `test_okf_pack_releases_name_themselves_in_the_topmost_changelog_heading`
  in `tests/roster/test_okf_catalogue_discovery.py` for the topmost-architect
  clause, which the other two do not read. Whether a Highlights block is owed is
  decided by nothing mechanical —
  `test_a_released_entry_without_highlights_is_absent_from_now` records that a
  missing block is valid and simply does not publish — so that disposition is
  an Agent Rule under its owning source, not a criterion. None of these
  becomes a committed test: a test pinning this version string would red on
  the next bump.

**Stub tally.** Covered by a red stub: AC-0084–AC-0089 (T1), AC-0090 (T2).
`no stub (goal-based check)`: AC-0094, AC-0095, AC-0096 (T5), AC-0099, AC-0101
(T6). Uncovered: none.

## Acceptance Criteria

### The shape axis in the skill

- [x] **AC-0084.** The shape-axis region of
  `packs/architect/.apm/skills/architect-design/SKILL.md` cites
  `concepts/system-shapes/index.md` as the descent path for the system-shape
  axis.
- [x] **AC-0085.** That region carries the phrase
  `open decision` and states that a shape concept is selected only when an
  open decision of the proposed design turns on that shape's coordination
  mechanism.
- [x] **AC-0086.** That region states that a design
  carrying an open decision in each of several shapes loads every one of them.
- [x] **AC-0087.** That region carries the phrases
  `loads whole` and `no tier selection`, and states that a selected shape
  concept loads whole.
- [x] **AC-0088.** That region states both the trigger and the record: when
  no shape carries an open decision, the working receipt records
  `no shape lens selected`. The shipped assertion pins the value in its
  backticked form, so a region stating it in plain prose conforms and reds —
  one instance of the general tightness recorded in Testing Strategy.
- [x] **AC-0089.** `<!-- shape-axis:start` and
  `<!-- shape-axis:end -->` each appear exactly once in that file,
  `<!-- shape-axis:start` precedes `<!-- shape-axis:end -->`, the region opens
  after `<!-- scope-determination:end -->`, and it closes before
  `<!-- template-selection:start`.

### The eval harness

- [x] **AC-0090.** `packs/architect/.apm/skills/architect-design/evals/evals.json` carries a
  case whose expected output names the system-shape axis, the open-decision
  trigger, and one `system-shapes/` concept path that exists under
  `packs/architect/okf/architecture-lenses/concepts/`. The shipped assertion
  pins the literals `shape axis` and `open decision`; note that the
  criterion's own spelling, "the open-decision trigger", does not contain the
  second, so an expected output written in these words would red — one
  instance of the general tightness recorded in Testing Strategy.

### The cross-slice names

- [x] **AC-0099.** `docs/adr/0118-architect-design-scope-routed-model-first-templates.md`
  carries a dated `## Errata` entry naming the open-decision trigger, the
  whole-load rule, and the `no shape lens selected` receipt value, so a later
  slice reads them without reading this spec.
- [x] **AC-0101.** Each of those three names in the erratum carries the same
  literal token the skill region carries for it — `open decision` for the
  trigger, `loads whole` together with `no tier selection` for the whole-load
  rule, and `no shape lens selected` for the receipt value — so the two copies
  of the cross-slice vocabulary cannot drift apart unnoticed.

### Release closure

- [x] **AC-0094.** `packs/architect/pack.toml` and
  `packs/architect/.claude-plugin/plugin.json` carry the same version, one
  patch above the value each holds on the merge base with the default branch,
  under `packs/AGENTS.md` § Version bump rule.
- [x] **AC-0095.** `.claude-plugin/marketplace.json` carries that same version
  for the architect pack, written by regeneration rather than by hand.
- [x] **AC-0096.** `docs/product/changelog.md` carries a free-standing `##`
  architect release entry, naming the bumped version, as the topmost
  **architect** release entry and not nested under an unreleased region. Not
  the file's topmost release heading: `[core]` is pinned to the slot directly
  beneath `[Unreleased]` by
  `tests/roster/test_verification_ledger_contract.py`, and this file's own
  history already places architect below core.

## Follow-ons

- architect pack maintainer: `docs/product/intents/architect-design-conditional-overlays.md` — the bet behind this axis, everything that follows from the probe returning no verdict, and the gating of `S2` and `S3` are the intent's to carry, not this spec's. It records the verdict, the study that would settle it, and what a later kill costs an already-released axis. This delivery ships the axis and states its own status; it does not restate the intent's.
- architect pack maintainer: `docs/product/intents/architect-design-gate-calibration.md` — `notes/probe/verdict-final.md` adds four re-derivable `DA10` counts to that intent's evidence. The verification-only `needs` edge naming this intent was on the *conditional-overlays* `backlog.open` entry, not on this one. That entry was unregistered on 2026-09-20 when its intent reached `Accepted`, so the edge is gone from `workspace.toml`; the intent's `## De-risk` measurement-dependency paragraph is its only home now.

## Assumptions

- Product: whether routing a shape lens adds concerns rather than bulk is unresolved, and this delivery does not resolve it. The probe ran and returned no verdict; `notes/probe/verdict-final.md` owns the result, its weighting and what would test the bet, and the intent owns what follows for `S2` and `S3` (settled by: the study that record names).
