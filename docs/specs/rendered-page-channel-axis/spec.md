# Spec: Rendered-page inspection channel axis

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
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
| Current product truth — adopter-facing skill | Applicable — `SKILL.md` restates the capture contract for the agent that performs it, and `JOURNEY.md` restates the manifest inventory | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` § 5a and its evidence-manifest table; `packs/frontend-engineering/JOURNEY.md` manifest inventory | pack maintainer | Capture table and worked example span more than one channel; both manifest inventories state channels as width predicates; a check fails when the two copies of the capture table disagree | All copies state one contract and a drift between them is caught mechanically |
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
- Keep the copies of the capture contract — the reference, `SKILL.md`, and the
  journey's manifest inventory — in agreement, and make a disagreement between
  them fail a check rather than a reader's attention.
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

- **Channel derivation and the recorded basis (AC-0001, AC-0002, AC-0003, AC-0004, AC-0008):** TDD in `packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_capture_contract.py`. Each is a compressible invariant over data — a list of declared breakpoints either yields the bands bounded by it or it does not — and every expectation is read from the shipped tables, so AC-0008's mutation is deleting a rule row rather than editing the module.
- **Capture-set completeness (AC-0005, AC-0006, AC-0007):** TDD in the same module and in `test_rendered_page_unscrollable.py`, driven by fixtures that vary viewport width and viewport height independently. The shipped fixture shape — width written as a function of height — misses four requirements under the channel rule, so each of the three suites needs a fixture varying the two independently before any case can assert a complete set.
- **Agreement and prohibition over shipped content (AC-0009, AC-0010, AC-0011, AC-0012, AC-0013):** TDD across `test_rendered_page_capture_contract.py`, `test_rendered_page_shipped_content_limits.py`, and `test_rendered_page_reviewer_sight.py`. AC-0012 is a universal claim over authored prose, so the criterion itself fixes both its vocabulary and its scope rather than deferring either to the check.
- **Eval harness (AC-0016):** TDD in `test_rendered_page_reviewer_sight.py` — a parse of `evals/evals.json` asserting channel coverage among the expected behaviours.
- **Adopter guidance (AC-0018):** goal-based check — a search over the guide asserting it names both fallback channels and states the band between them that no fallback capture reaches. Well-formedness and link resolution hold on a guide containing neither, so the repository's documentation gates stay a separate one-liner rather than this criterion's evidence.
- **Supersession record (AC-0019):** TDD in `test_rendered_page_capture_contract.py` — a comparison of the frozen spec against its pre-change bytes, asserting the pointer landed on the `Status:` line and nothing below it moved. The body-unchanged half is what makes this more than a grep for a filename.
- **Pack delivery (AC-0014, AC-0015):** goal-based checks compare the two manifests' version fields, confirm the changelog entry is this pack's topmost release heading, run `agentbundle catalogue lint --deep` and `catalogue verify`, and compare the pack's declared dependency surfaces before and after to show none was added.
- **The step performed (AC-0017):** visual / manual QA. The step is an agent gesture, so it is verified by performing it against a real surface across two channels and recording what came back. A passing completeness test is not evidence that a second channel found anything.

## Acceptance Criteria

<!-- Channels -->
- [ ] **AC-0001.** When the adopter declares breakpoints `b1 < ... < bn` for a surface, the required channels are exactly the bands those breakpoints bound, each stated as a separate lower-bound and upper-bound predicate that a capture must satisfy together, and each boundary value belonging to the wider band: `<b1`, then `>=bk` with `<bk+1` for each adjacent pair, then `>=bn`. An absent bound means unbounded on that side. Origin: the breakpoint values as the adopter declares them, in CSS pixels; the boundary convention follows the mobile-first `min-width` semantics the pack's own `responsive-layout` skill states. Construction test: `test_declared_breakpoints_bound_the_required_channels`; fixtures: a one-breakpoint list, a three-breakpoint list whose interior bands are bounded on both sides, and a capture taken at a breakpoint value exactly.
- [ ] **AC-0002.** When the adopter declares no breakpoints, the required channels are exactly two — a narrow channel at a viewport width of at most 480 CSS pixels and a wide channel at a viewport width of at least 1024 CSS pixels. These two bands are stated literally in the reference and are not produced by AC-0001's derivation, so their boundary values fall on the opposite side: 480 is narrow under the fallback, while a declared breakpoint at 480 places 480 in the band above it. Origin: the pack's own `--breakpoint-sm` and `--breakpoint-lg` tokens, both compared against the browser viewport's width in CSS pixels. A width between those bounds satisfies neither channel. Construction test: `test_fallback_channels_are_the_two_shipped_bands`; fixtures: widths of 480, 768 and 1024 against the shipped band table.
- [ ] **AC-0003.** A run records which of the two channel bases it used, taken from the input rather than inferred from the capture set. Construction test: `test_channel_basis_is_recorded_not_inferred`; fixture: a run supplying no breakpoints and a run supplying them.
- [ ] **AC-0004.** The breakpoints a run derives channels from are supplied by the adopter; the step discovers none. Construction test: `test_breakpoints_are_adopter_supplied`; fixture: the shipped channel rule rows.
- [ ] **AC-0005.** For each inspected route, the capture set contains, in every required channel, each of the four height-and-scroll captures the pack's required-capture table names. Construction test: `test_every_required_channel_carries_the_height_and_scroll_matrix`; fixtures: a two-channel set and a one-channel set.
- [ ] **AC-0006.** A capture set missing any capture AC-0005 requires yields an incomplete result that cannot satisfy a completed inspection. Construction test: `test_a_single_channel_set_is_incomplete`; fixture: the one-channel set from AC-0005, whose result names each missing channel-and-capture pair.
- [ ] **AC-0007.** The scroll-pair obligation the pack already states at every captured viewport height holds instead at every captured `(viewport-width, viewport-height)` pair, including a width or height beyond the required channels and bands. Construction test: `test_every_captured_width_and_height_needs_the_scroll_pair`; fixtures: a third width captured at rest only, and an unscrollable page at a second width.
- [ ] **AC-0008.** Removing the channel table, or the generalized pair rule row, from the reference makes the pack's capture-set checks fail rather than skip the rule the removed row governs. Construction test: `test_channel_requirement_is_shipped_content`; fixtures: the reference with the channel table removed, and the reference with the pair rule row removed.

<!-- Shipped content -->
- [ ] **AC-0009.** The capture table in `SKILL.md` and the capture table in the reference state the same set of required captures, and the check fails when they state different sets. Construction test: `test_both_copies_of_the_capture_contract_agree`; fixture: each table with one row perturbed.
- [ ] **AC-0010.** In the capture snippet an adopter copies from `SKILL.md`, the viewport width passed to the browser is bound to the channel the snippet iterates, and no numeric width literal appears in that viewport object. Construction test: `test_the_worked_example_binds_width_to_the_channel`; fixture: the shipped snippet.
- [ ] **AC-0011.** The evidence manifest's viewports field records the channels covered, stated as width predicates, in both `SKILL.md` and the journey's manifest inventory, and the two inventories state the same channel set. The check fails when they differ. Construction test: `test_manifest_viewports_field_records_channels`; fixture: both shipped inventories, and both with one perturbed.
- [ ] **AC-0012.** The reference states the device-name tokens a channel name may not contain, and no channel name in the shipped band table and no value in either manifest viewports field contains one of them. Construction test: `test_no_channel_is_named_for_a_device`; fixtures: the shipped band table and both manifest fields, plus a seeded device-named channel that must red, plus the reference with the forbidden-token row removed, which must red rather than skip.
- [ ] **AC-0013.** Lens 6 of the reviewer agent carries an imperative to use the capture's viewport width, alongside its existing "Use the scroll position", stating that the width decides which breakpoint-scoped rules that capture exercised. Construction test: `test_reviewer_lens_reads_the_width_axis`; fixture: the lens section alone, not the whole agent file, with the pre-change lens as the fixture that must red — its field-listing sentence already names viewport width, so a check reading that sentence passes unchanged.

<!-- Delivery -->
- [ ] **AC-0014.** `packs/frontend-engineering/pack.toml` and `packs/frontend-engineering/.claude-plugin/plugin.json` both carry `0.2.4`. Origin: `packs/AGENTS.md` § *Version bump rule* yields a patch bump from `0.2.3`, because this delivery changes pack content without adding or removing a primitive.
- [ ] **AC-0015.** `docs/product/changelog.md` carries an entry led by the `frontend-engineering` pack at `0.2.4`, and that entry is the topmost release heading for this pack.
- [ ] **AC-0016.** The pack's eval harness names channel coverage among the behaviours it expects of a completed inspection.
- [ ] **AC-0017.** One end-to-end run of the step against a real surface across two channels is recorded, with its observations, its result state, its verdict, and its channel basis, at the destination the Durable Outputs table names.
- [ ] **AC-0018.** The shipped how-to walks a capture set across two channels and states what a fallback run does not cover.
- [ ] **AC-0019.** `docs/specs/rendered-page-visual-inspection/spec.md` carries a `Status:` line pointer naming this spec's AC-0007 as the successor to its height-only pair criterion, and its body below that line is byte-identical to the version this delivery started from. Construction test: `test_superseded_pair_criterion_is_pointed_at`; fixture: that file before and after.

## Follow-ons

None identified at authoring time.

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
- Technical: neither edited shipped file is content-hash pinned; the two shipped-
  content guards are prose searches scoped to `.apm/**`
  (`test_rendered_page_shipped_content_limits.py:33-38,60-70`).
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
