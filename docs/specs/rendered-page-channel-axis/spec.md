# Spec: Rendered-page inspection channel axis

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them when
> a finding is adjudicated is the reviewing surface's.

## Objective

A team using the `frontend-engineering` pack inspects a rendered page and learns
that a layout rule written for one side of a breakpoint is reaching the other
side, where it does something the author never looked at. The pack's inspection
step permutes viewport height and scroll position, so a complete capture set can
sit entirely on one side of every breakpoint the surface has: a layout rule
scoped to a wide viewport is only ever exercised where it applies, and a rule
scoped to nothing is only ever exercised where it happens to be harmless. The
capture record already carries the viewport width and the judge is already told
it; nothing reads either.

This delivery makes viewport width a completeness axis. A **channel** is a band
of viewport widths, and a capture set is complete only when it covers every
channel the surface has — one on each side of every breakpoint the adopter
declares, or two default bands when they declare none. Each required channel
carries the four height-and-scroll captures the step already requires, so the
floor rises from four captures per route to eight, and to four times the number
of channels a surface's declared breakpoints bound.

Success for the adopter is that an inspection cannot report `completed` while an
entire channel of their surface has never been looked at, and that the report
says which channels were covered and whether they came from declared breakpoints
or from the defaults.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth — rule layer | Applicable — the reference is the executable contract the step and its checks both read | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/rendered-page-inspection.md` | pack maintainer | Channel table, required-capture table, and the generalized pair rule present; rule-reading module derives them rather than restating them | Reference and the checks that read it agree, and deleting a channel rule row from the reference reds the suite |
| Current product truth — adopter-facing skill | Applicable — `SKILL.md` restates the capture contract for the agent that performs it, and `JOURNEY.md:12` declares what the adopter brings. `JOURNEY.md`'s two *manifest* inventories at `:84` and `:169` name `viewports` without stating what the field holds, so those two lines are a deliberate non-edit | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` § 5a and its evidence-manifest table; `packs/frontend-engineering/JOURNEY.md:12` | pack maintainer | Capture table and worked example span more than one channel; the manifest viewports field states channels as width predicates; the journey's input declaration names declared breakpoints; a check fails when the two copies of the capture table disagree | Both copies state one contract, a drift between them is caught mechanically, and the journey names every input the step takes |
| Current product truth — reviewer lens | Applicable — the reviewer is seeded with the capture set and reads the recorded fields | `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` lens 6 | pack maintainer | Lens names `viewport-width` among the fields the reviewer must use | Reviewer reads the width axis as coverage, not as a duplicate discriminator |
| Adopter guidance | Applicable — the shipped how-to walks the step and teaches the capture set by example | `guides/frontend-engineering/how-to/inspect-the-rendered-page.md` | pack maintainer | Guide walks a two-channel capture set against a non-repository surface and states what a fallback run does not cover | An adopter can produce a complete capture set from the guide alone |
| Interface compatibility — superseded criterion | Applicable — this delivery strengthens a criterion the Shipped `rendered-page-visual-inspection` spec carries as met | `docs/specs/rendered-page-visual-inspection/spec.md` `Status:` line pointer | spec owner | A `Status:` line pointer naming this spec as the successor for the pair criterion; the frozen body is not edited | The frozen spec's tick is traceable to the criterion that now supersedes it |
| Execution observation | Applicable — AC-0017 requires four recorded values from a manual gesture, and a session transcript is not a durable home | `docs/specs/rendered-page-channel-axis/notes/verification-ledger.md` | spec owner | The run's observations, result state, verdict, and channel basis | The four recorded values are readable outside the session that produced them |
| Decision rationale | Applicable — "each side of every declared breakpoint" was chosen over fixed device bands, and the reason is not recoverable from the result | this spec's Objective, Acceptance Criteria, and Assumptions | spec owner | The channel criteria state the rule; the Assumptions record what was settled, when, and what the fallback does not reach | A future reader can see why channels are breakpoint-derived rather than device-named |
| Reusable learning — eval harness | Applicable — `packs/AGENTS.md` § *Security and authoring rules* obliges a non-cosmetic pack update to update that pack's eval harness | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json` | pack maintainer | Harness expectation names channel coverage | The harness exercises the shipped axis |
| Release history | Applicable — pack content changes | `packs/frontend-engineering/pack.toml`, `packs/frontend-engineering/.claude-plugin/plugin.json`, `docs/product/changelog.md` | release workflow | Matching version bump in both manifests; a changelog entry led by the pack and that version | Versions and changelog agree with shipped content |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Express a channel as a width predicate with a semantic name. `responsive-layout`
  forbids encoding device names, and a channel named for a device inherits a
  dimension that stops being true.
- Let the shipped tables state every rule, and let the rule-reading module read
  them. A check that supplies its own quantifier asserts behaviour the pack never
  promised an adopter.
- Raise on an absent rule row rather than skipping the rule it governs. A reader
  that skips is fail-open, and a requirement nobody can delete-and-red is not
  shipped content.
- Keep the two copies of the capture contract — the reference and `SKILL.md` — in
  agreement, and make a disagreement between them fail a check rather than a
  reader's attention.
- Record which channel basis a run used, so a breakpoint-grounded inspection is
  distinguishable from one that fell back to the defaults.
- Take the fixtures to the new contract. A fixture that supplies exactly one
  width per height is the premise this delivery exists to remove.

### Ask first

- Changing either required-height band or the scroll-position rule. Those are
  the shipped axes and this delivery adds one beside them; it does not retune them.
- Adding a sixth required field to the capture record.
- Adding a required runtime dependency to the pack, or any new declared
  dependency surface.
- Raising the required-capture floor above four captures per required channel.
- Editing the body of a frozen spec. A superseded criterion takes a `Status:`
  line pointer.

### Never do

- Weaken a fixture, relax a predicate, or narrow a capture set to turn the
  expected red green. The four requirements the current fixtures miss are the
  defect being fixed.
- Name a device as the definition of a channel in shipped pack content.
- Cite this repository, its paths, its records, or the surface that motivated
  this change inside `packs/frontend-engineering/.apm/**`.
- Introduce a new top-level directory, a new module boundary in the pack's test
  tree, or a second rule-reading module. The existing
  `frontend_engineering_rendered_page_rules.py` is the one reader.
- Introduce a screenshot baseline, a stored reference image, or any comparison
  against a previous run.

## Testing Strategy

- **Channel derivation, capture width, and the recorded basis (AC-0001, AC-0002, AC-0003, AC-0004, AC-0008, AC-0024):** TDD in `packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_capture_contract.py`. Each is a compressible invariant over data — a list of declared breakpoints either yields the bands bounded by it or it does not — and every expectation is read from the shipped tables, so AC-0008's mutation is deleting a rule row rather than editing the module.
- **Capture-set completeness (AC-0005, AC-0006, AC-0007):** TDD in `test_rendered_page_capture_contract.py`, `test_rendered_page_unscrollable.py`, and `test_rendered_page_verdict.py`, driven by fixtures that vary viewport width and viewport height independently. The shipped fixture shape — width written as a function of height — misses four requirements under the channel rule, so all three suites need a fixture varying the two independently before any case can assert a complete set.
- **Agreement and prohibition over shipped content (AC-0009, AC-0010, AC-0011, AC-0012, AC-0013):** TDD across `test_rendered_page_capture_contract.py`, `test_rendered_page_shipped_content_limits.py`, and `test_rendered_page_reviewer_sight.py`. AC-0012's scope is fixed by the criterion; its vocabulary is read from the one-column forbidden-token table the reference ships under `## Channels`, so removing that table reds the guard instead of silently emptying it.
- **Eval harness (AC-0016):** TDD in `test_rendered_page_reviewer_sight.py` — a parse of `evals/evals.json` asserting the `assertions` array carries a channel-coverage assertion.
- **Journey promise (AC-0023):** TDD in `test_rendered_page_journey_promise.py`, the suite that already owns assertions about what the journey promises. Named here once; the plan references this placement rather than restating it.
- **Adopter guidance (AC-0018):** goal-based check — a search over the guide for both fallback channel names, the band between them that no fallback capture reaches, and the per-channel floor. Its negative half — that the guide no longer teaches the height-only floor — is **not** a criterion: three review rounds established that no token predicate reds the five pre-change strings while sparing the guide's unscrollable-branch sentence, which must survive. That obligation lives in the plan's design with a content pin on the five strings. Well-formedness and link resolution hold on a guide containing none of it, so the repository's documentation gates stay a separate one-liner.
- **Supersession record (AC-0019):** TDD in `tests/roster/`, not in the pack's suite — the frozen spec belongs to this repository's spec lifecycle, and a pack test that fails when a `docs/specs/**` file moves inverts the pack's own test boundary. The unchanged half is a literal pin on the superseded criterion's sentence rather than a byte comparison against a snapshot, so it needs no committed duplicate of the frozen body and no external binary.
- **Pack delivery (AC-0014, AC-0015):** goal-based checks compare the two manifests' version fields, confirm the changelog entry is this pack's topmost release heading, run `agentbundle catalogue lint --deep` and `catalogue verify`, and compare the pack's declared dependency surfaces before and after to show none was added.
- **The step performed (AC-0017):** visual / manual QA. The step is an agent gesture, so it is verified by performing it against a real surface across two channels and recording what came back. A passing completeness test is not evidence that a second channel found anything.

## Acceptance Criteria

<!-- Channels -->
- [x] **AC-0001.** When the adopter declares breakpoints `b1 < ... < bn` for a surface, the required channels are exactly the bands those breakpoints bound, each stated as a separate lower-bound and upper-bound predicate that a capture must satisfy together, and each boundary value belonging to the wider band: `<b1`, then `>=bk` with `<bk+1` for each adjacent pair, then `>=bn`. An absent bound means unbounded on that side. A declared breakpoint is a positive integer of CSS pixels; a run refuses a value that is not, because the predicate cells the bands become admit whole numbers only. Origin: the breakpoint values as the adopter declares them, in CSS pixels; the boundary convention follows the mobile-first `min-width` semantics the pack's own `responsive-layout` skill states. Construction test: `test_declared_breakpoints_bound_the_required_channels`; fixtures: a one-breakpoint list, a three-breakpoint list whose interior bands are bounded on both sides, and a capture taken at a breakpoint value exactly.
- [x] **AC-0002.** When the adopter declares no breakpoints, the required channels are exactly two — a narrow channel at a viewport width of at most 480 CSS pixels and a wide channel at a viewport width of at least 1024 CSS pixels. These two bands are stated literally in the reference and are not produced by AC-0001's derivation, so their boundary values fall on the opposite side: 480 is narrow under the fallback, while a declared breakpoint at 480 places 480 in the band above it. Origin: the pack's own `--breakpoint-sm` and `--breakpoint-lg` tokens, both compared against the browser viewport's width in CSS pixels. A width between those bounds satisfies neither channel. Construction test: `test_fallback_channels_are_the_two_shipped_bands`; fixtures: widths of 480, 768 and 1024 against the shipped band table.
- [x] **AC-0003.** A run records which of the two channel bases it used, taken from the input rather than inferred from the capture set, and carries it to the surface AC-0011 names. Construction test: `test_the_channel_basis_is_recorded_not_inferred`; fixture: a run supplying no breakpoints and a run supplying them.
- [x] **AC-0004.** The breakpoints a run derives channels from are supplied by the adopter; the step discovers none. Construction test: `test_fallback_channels_are_the_two_shipped_bands`, which asserts the `channel-source` row and that the bands come from the reference; fixture: the shipped channel rule rows.
- [x] **AC-0023.** The journey's `youProvide` declaration names declared breakpoints among the inputs the adopter brings. Construction test: `test_rendered_page_journey_promise.py::test_the_journey_declares_the_breakpoint_input`; fixture: the pre-change declaration, which names routes and viewports and not breakpoints.
- [x] **AC-0005.** For each inspected route, the capture set contains, in every required channel, each of the four height-and-scroll captures the pack's required-capture table names. Construction test: `test_every_required_channel_carries_the_height_and_scroll_matrix`; fixtures: a two-channel set and a one-channel set.
- [x] **AC-0006.** A capture set missing any capture AC-0005 requires yields an incomplete result that cannot satisfy a completed inspection. Construction test: `test_a_single_channel_set_is_incomplete`; fixture: the one-channel set from AC-0005, whose result names each missing channel-and-capture pair.
- [x] **AC-0007.** The scroll-pair obligation the pack already states at every captured viewport height holds instead at every captured `(viewport-width, viewport-height)` pair, including a width or height beyond the required channels and bands. Construction test: `test_every_captured_width_and_height_needs_the_scroll_pair`; fixtures: a third width captured at rest only, and an unscrollable page at a second width.
- [x] **AC-0008.** Removing the channel table, or the generalized pair rule row, from the reference makes the pack's capture-set checks fail rather than skip the rule the removed row governs. Construction test: `test_the_channel_requirement_is_shipped_content` and `test_every_required_rule_row_raises_when_deleted`; fixtures: the reference with each rule row the completeness walk reads removed in turn, and the reference with the whole `## Channels` section removed. Deleting a row must raise, not skip the rule it governs; a row present and set to anything other than `required` is a stated decision and is honoured.

<!-- Shipped content -->
- [x] **AC-0009.** The capture table in `SKILL.md` and the capture table in the reference state the same set of required captures, and the check fails when they state different sets. Both tables carry the same column set after the change, and the comparison normalizes only presentation: `≤` and `≥` to `<=` and `>=`, a trailing ` CSS px`, and backticks. It must still distinguish a changed numeric bound, a changed comparison operator, a changed capture name, and the presence or absence of the scroll rule's unscrollable branch — the two tables differ in every predicate cell today under a literal comparison, and a normalization that compares the name column alone cannot fail on the drift this criterion exists to catch. Construction test: `test_both_copies_of_the_capture_contract_agree`; fixtures: each table with one row perturbed, and one pair differing only in each of the four distinctions named above.
- [x] **AC-0024.** The reference states the width a capture in a channel is taken at: the value of that channel's lower bound where it has one, otherwise the largest integer satisfying its upper bound. This is total over every band the contract produces, including a band unbounded on either side and a band whose upper bound is exclusive. Construction test: `test_every_channel_yields_a_capture_width_inside_itself`; fixtures: the two fallback bands, a one-breakpoint derivation, and a three-breakpoint derivation whose interior bands are bounded on both sides — every width must satisfy both of its own band's bounds, and a declared breakpoint of `1152` must yield `1151` and `1152`.
- [x] **AC-0010.** The capture snippet an adopter copies from `SKILL.md` iterates a channel list of at least two entries and passes the browser the capture width of the entry it is on. Construction test: `test_the_worked_example_binds_width_to_the_channel`; fixture: the shipped snippet, and the pre-change snippet, whose single hard-coded width must red.
- [x] **AC-0011.** The evidence manifest's viewports field in `SKILL.md` records the channels covered, stated as width predicates, and the channel basis AC-0003 requires the run to record. Construction test: `test_manifest_viewports_field_records_channels`; fixture: the shipped required-field table.
- [x] **AC-0012.** The reference states the device-name tokens a channel name may not contain, and no channel name the reference declares contains one of them. The manifest viewports field carries no such token either, and every channel name appearing in shipped `.apm/**` content is one the reference declares — without that second clause the declared-name scope is an assumption rather than a check. Construction test: `test_no_channel_is_named_for_a_device`; fixtures: the shipped band table and the manifest field, plus a seeded device-named channel that must red, plus a seeded channel name absent from the declared set, plus the reference with the forbidden-token row removed, which must red rather than skip.
- [x] **AC-0013.** Lens 6 of the reviewer agent carries an imperative to use the capture's viewport width, alongside its existing "Use the scroll position", stating that the width decides which breakpoint-scoped rules that capture exercised. Construction test: `test_reviewer_lens_reads_the_width_axis`; fixture: the lens section alone, not the whole agent file, with the pre-change lens as the fixture that must red — its field-listing sentence already names viewport width, so a check reading that sentence passes unchanged.

<!-- Delivery -->
- [x] **AC-0014.** `packs/frontend-engineering/pack.toml` and `packs/frontend-engineering/.claude-plugin/plugin.json` both carry `0.2.4`. Origin: `packs/AGENTS.md` § *Version bump rule* yields a patch bump from `0.2.3`, because this delivery changes pack content without adding or removing a primitive.
- [x] **AC-0015.** `docs/product/changelog.md` carries an entry led by the `frontend-engineering` pack at `0.2.4`, and that entry is the topmost release heading for this pack.
- [x] **AC-0016.** The `rendered-page-inspection` case's `assertions` array carries a channel-coverage assertion. Construction test: `test_the_harness_expects_channel_coverage`; fixture: the pre-change case, which must red.
- [x] **AC-0017.** One end-to-end run of the step against a real surface across two channels is recorded, with its observations, its result state, its verdict, and its channel basis, at the destination the Durable Outputs table names.
- [x] **AC-0018.** The shipped how-to states the per-route floor as four captures per required channel, walks a capture set across two channels, and states what a fallback run does not cover.
- [x] **AC-0019.** `docs/specs/rendered-page-visual-inspection/spec.md` carries a `Status:` line pointer naming this spec's AC-0007 as the successor to its height-only pair criterion, and that criterion is still present in its body verbatim and still ticked. Construction test: `tests/roster/test_rendered_page_channel_axis_supersession.py::test_the_status_line_points_at_the_successor` and `::test_the_superseded_criterion_is_still_present_verbatim`; fixture: the frozen file, with the criterion's own sentence as the literal pin.

## Retired identifiers

- `AC-0021`
  - Demoted 2026-09-13 under owner authority. "No assertion or sentence states a
    complete capture set by viewport height alone" has no decidable predicate:
    the harness assertion and guide line it names as must-red carry no
    completeness word, and the token that would red them also reds a sentence
    that must survive. The obligation is plan design material with a content pin.
- `AC-0022`
  - Demoted 2026-09-13 under owner authority, for the reason `AC-0021` records.
- `AC-0025`
  - Demoted 2026-09-13 under owner authority. It obliged shipped adopter content
    to carry a vocabulary no adopter acts on and the step never reads, existing
    only to make the `AC-0021` and `AC-0022` guards writable. With those demoted
    it has no consumer.
- `AC-0020`
  - Retired because `JOURNEY.md` names `viewports` only in a field inventory and
    never states what it holds, so there is no second manifest inventory for the
    drift clause to compare against.

## Follow-ons

Separately scoped, discovered during delivery, and registered in
`workspace.toml` under `[backlog].open` so acting on them does not depend on
anyone rereading this spec's notes.

- **The mapping from written path to gating suite is carried by recall.**
  `packs/frontend-engineering/tests/` is named nowhere in `build-check.yml`, so
  the 292 tests that path collects reach CI only through the dispatch-only
  `test-corpus.yml`. Scoped to the pack suite deliberately: other outcomes of
  this delivery are PR-gated, some by design and some incidentally — AC-0019's
  three supersession cases under `tests/roster/`, and two
  `tests/conformance/test_pack_metadata.py` cases covering AC-0014's version
  match. Nothing connects a written path to the suite
  that reads it except a person's memory, which is the same unfalsifiable-rule
  shape this delivery removed from its own content — and it was paid twice inside
  this delivery, once on `docs/product/changelog.md` and once on `workspace.toml`.
  Owner: the repository's gate chain, not this pack — the work touches
  `build-check.yml` and the Makefile and does not belong in a pack-content
  delivery. Evidence: this spec's `notes/verification-ledger.md`, § *What runs on
  a PR, and what this delivery therefore owes*, whose reach table was corrected
  on 2026-09-14 after the first version overstated the gap.

## Assumptions

- Technical: the contract is markdown tables read by
  `packs/frontend-engineering/tests/skills/frontend-engineering/frontend_engineering_rendered_page_rules.py`.
  `satisfies()` parses one operator and one bound per cell
  (`frontend_engineering_rendered_page_rules.py:141-153`), so it raises on a
  two-sided predicate such as `>=480 <1024` — verified by probe 2026-09-13. The
  per-cell grammar is therefore unchanged and a band row carries **two** predicate
  cells the reader conjoins, rather than one cell holding an interval.
- Technical: the module guards an absent rule row two incompatible ways — a raise
  at `:540-544` and a fail-open `continue` at `:246-248`. The channel reader
  follows the raise, or AC-0008 can never pass.
- Technical: the current fixture shape — one width per height — is `complete`
  under the shipped rule and misses exactly four requirements under the channel
  rule, so the expected red is real and is four requirements wide (read-only probe
  against `evaluate_capture_set`, 2026-09-13).
- Technical: neither edited shipped file is content-hash pinned. The two shipped-
  content guards are prose searches scoped to `.apm/**`, and they differ in where
  their vocabulary lives: the genericity guard states its own identifier set
  (`test_rendered_page_shipped_content_limits.py:195-213`), while the rate guard
  pins its vocabulary to a `## Rate vocabulary` table in the measurement reference
  and asserts the two are equal (`:103-119`). The rate guard is the shape AC-0012
  mirrors.
- Technical: `SKILL.md` is 873 lines against the `CAT-S003` 1,000-line error
  ceiling, so the section edits have headroom
  (`packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py:520`).
- Process: the release surface is `pack.toml` plus `.claude-plugin/plugin.json`,
  both at `0.2.3`, and a `docs/product/changelog.md` heading led by the pack
  (`packs/AGENTS.md` § *Version bump rule*; `docs/product/changelog.md:214`).
- Process: shipped `.apm/` content may not cite this repository's identifiers, so
  the surface that motivated this change cannot be named inside the pack
  (`packs/AGENTS.md` § *Shipped pack content carries no internal-governance
  citations*).
- Product: each required channel carries all four height-and-scroll captures, a
  floor of eight per route (user confirmation 2026-09-13).
- Product: the fallback channels are `narrow` at `<=480` and `wide` at `>=1024`,
  leaving a deliberate dead zone so no single width satisfies both (user
  confirmation 2026-09-13). **What the fallback does not reach:** a surface whose
  real breakpoint sits between 481 and 1023 — the pack's own `--breakpoint-md` at
  768 is the commonest — gets two fallback channels that both sit away from where
  its layout switches, so the defect class this spec names goes undetected on a
  fallback run. Declaring breakpoints is what closes that gap, which is why
  AC-0018 makes the guide say so.
- Product: declared breakpoints are an optional adopter-supplied input; absent
  them the run uses the fallback bands and records that it did (user confirmation
  2026-09-13).
