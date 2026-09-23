# Spec: frontend-experience-composition

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the Digital Experience Contract template is pack content,
  not a `contracts/` artifact.
- **Shape:** mixed
- **Depends on:** recorded canonically as this spec's `needs` edge in
  `workspace.toml` under `["ini-003".work]`, and stated here only in prose: the
  three artifacts this spec makes the packs agree about only have addresses once
  `design-output-addressing` ships. The frontend *read* of those artifacts is a
  third spec, `design-handoff-read`, independent of this one; this spec names the
  artifacts in both journeys and does not read them.

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

A team running the `experience-design` and `frontend-engineering` packs gets one
shared answer to "which states must this surface handle, and how much of the
contract do I owe?", instead of two pack vocabularies that never meet. Success is
an adopter who can pick the cheapest depth on either journey, see exactly what
that depth drops, and know that accessibility is never in the dropped set.

## What Changes

- One state-coverage map, mapping all 18 frontend states to risk-tier bands and
  WCAG-bearing flags — the `States and Permissions` section of the Digital
  Experience Contract, in all four pack copies.
- The contract's frontend section owner label, from `core` to
  `frontend-engineering` — the same four copies.
- The contract stops being unread content — `frontend-engineering/SKILL.md` and
  `design-review/SKILL.md` each name their pack-local copy as a file they load.
- A `risk-tier` depth selector, stated as body prose and `####` sub-stages —
  `packs/frontend-engineering/JOURNEY.md` and `packs/experience-design/JOURNEY.md`.
- Per-row optionality, a minimal viable thread, and a reciprocal
  `relatedJourneys` link — `packs/experience-design/JOURNEY.md`.
- The four proportionality allowances the frontend skill already carries, lifted
  into its journey — `packs/frontend-engineering/JOURNEY.md`.
- Two roster test files and their CI registration — `tests/roster/`,
  `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`.
- An ADR recording that the frontend discipline belongs to its own pack, and the
  supersession pointer it earns — `docs/adr/`,
  `docs/specs/digital-experience-contract/`.
- The fifth home for the tier table stops restating counts the contract owns —
  `guides/core/explanation/digital-experience-contract.md`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — adopters choose depth and see the crossing artifacts | both `JOURNEY.md` files, `guides/experience-design/how-to/`, `guides/frontend-engineering/how-to/` | Guide author | Each journey states its tier obligations and its optionality; each new capability has a how-to | The guide lints exit 0 and the tier-count test agrees with the contract |
| Current product truth | Applicable — a fifth home for the tier table is stale today | `guides/core/explanation/digital-experience-contract.md` | Guide author | That page references the contract's annotations rather than restating them | The page states no per-tier field count and no per-tier field list |
| Interface compatibility | Applicable — four packs carry the contract byte-identically | the four `digital-experience-contract.md` copies | Pack maintainer | `check-contract-drift` step in the build-check chain passes | All four copies byte-identical |
| Decision rationale | Applicable — the frontend section's owner label changes on a frozen record | `docs/adr/` | ADR author | An ADR records that the frontend discipline is owned by its own pack | ADR accepted and cited by the superseded spec's Status line |
| Operations | Applicable — two new tests are worthless unless CI runs them | `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py` | Maintainer | Both tests named as steps with matching dispositions | `tools/lint-ci-parity.py` exits 0 |
| Release history | Applicable — four packs bump | `docs/product/changelog.md` | Release author | One released entry per bumped pack, topmost for that artifact | Topmost entry per pack names its new `pack.toml` version |
| Reusable learning | Applicable | `project-knowledge` seam | Work-loop | Receipt or `project-knowledge unavailable` | Recorded at the terminal gate |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Move all four `digital-experience-contract.md` copies in one commit. The
  `check-contract-drift` step compares bytes first, so a partial edit fails the
  build-check chain rather than drifting quietly.
- Keep the `<!-- Required: -->` annotation as the first non-blank line after each
  `###` heading; the drift checker's structural fingerprint reads that position.
- Keep `experience-design` free of value literals — no hex, rgb, hsl, px, ms,
  rem, em, pt, vh, vw, `N:1` ratio, named easing curve, ARIA token, or CSS
  property syntax. The contract copy ships inside that tree too.
- Place any `####` sub-stage after its parent stage's `**Output:**` and
  `**State:**` labels. Both journey lints break their label scan on a line
  starting `##`, so a sub-stage placed first makes the parent's labels
  unreadable. `packs/core/JOURNEY.md:180` is the working precedent.
- Enumerate every existing test assertion over a `JOURNEY.md` before editing it.
  AC-0035 names the suites that carry one; do not restate a count here, because a
  count stated in two places is how this rule came to say three when the measured
  answer is four. One of them is repository-level and pins both journeys.
- Regenerate the committed web journey copy in the same task that edits its
  source `JOURNEY.md`, not at the end. No lint compares the two.

### Ask first

- Editing the byte-exact `PINNED_SKIP_COST` block covering the
  `accept-frontend-evidence` gate in `packs/frontend-engineering/JOURNEY.md`.
  Its own test docstring states a reworded line is a failure by design.
- Adding a journey `contract:` key. Tier is a per-run value and a journey key
  holds only a constant, so this should not be needed; if it seems to be, the
  design is wrong.
- Changing which states a tier band carries after the map is derived and approved.

### Never do

- Never add a new top-level directory, module, or dependency. This change is
  confined to `packs/`, `guides/`, `docs/adr/`, `docs/specs/`, `docs/product/`,
  `.github/workflows/`, `tools/lint-ci-parity.py`, the pack test trees, the
  repository roster suite, and the generated `web/src/content/journeys/`,
  `.claude/`, `.agents/` and `.claude-plugin/marketplace.json` outputs.
- Never let any tier band omit a state whose absence fails WCAG 2.2 AA.
  Accessibility is non-waivable under the root `AGENTS.md`, in the same class as
  trust-boundary validation.
- Never edit the body of a frozen Shipped spec or its plan beyond the `Status`
  field. One exception is authorized for this delivery and no other:
  `docs/specs/digital-experience-contract/plan.md` carries no `Status` field at
  all, and the owner authorized adding that single metadata line so the
  supersession pointer has both ends (owner decision, 2026-09-22). Nothing else
  in either frozen file may move.
- Never edit a lint, test, or checker to make a failing gate pass.

## Testing Strategy

Every acceptance criterion names its own mode and the artifact that decides it,
on the criterion's own line. That placement is the point: three review rounds
found criteria whose mode lived in a separate list that went stale each time the
list grew, so the list is gone and the mode travels with the thing it verifies.
This section defines the three modes and nothing else, so there is no second
enumeration to drift.

- **TDD** — a compressible invariant with a named assertion. Each criterion names
  the assertion that decides it; which of the two new roster files holds that
  assertion is the plan's to schedule, and is not re-enumerated here. Both files
  are repository-level, so both go to the roster suite, and a roster test
  attributes its own failure only when named as a `build-check.yml` step above
  the job's bulk `pytest tests/ -q` step.
- **Goal-based check** — a command whose exit status is the verdict. An absence
  check is written negated and quiet (`! grep -q …`) so that its passing case
  exits 0; a bare `grep` exits 1 on no match, which a harness reads as failure.
- **Review-only** — a reading at the human gate, for a proposition no artifact
  can decide: whether prose references rather than restates, whether two
  sentences contradict, whether a reader is told something, whether an eval case
  is apt. Each such criterion says so on its own line rather than being left to
  look covered.

Two properties of this delivery have no mode because nothing can give them one,
and both are stated rather than hidden. **Tier selection is unmechanizable** —
nothing in the repository knows a change's stakes, so no gate catches a tooltip
run at production depth; what is checkable is that each journey's stated
obligations match the contract's own annotations. **The depth selector sits in a
`####` sub-stage** that both journey lints skip, because their per-stage label
scan stops at the first line starting `##`. Its automated gate is
`test_experience_journey_composition.py`, which parses the ladder and the state
subset; the sub-stage's remaining prose is gated by the Review-only criteria
that name it.

## Acceptance Criteria

Each criterion carries its own verification mode, so a criterion cannot exist
without one. Three modes are in use, defined in Testing Strategy above:
**TDD** names the assertion that decides it, **Goal-based** names the command,
and **Review-only** names a reading at the human gate for a proposition no
artifact can decide.

- [x] **AC-0001.** The `check-contract-drift` step passes: all four `digital-experience-
      contract.md` copies are byte-identical. *Verified by:* Goal-based: `python3
      tools/repo/check_contract_drift.py --root .` exits 0.
- [x] **AC-0002.** The contract's frontend section heading reads `## Frontend
      Engineering [owner: frontend-engineering]`. *Verified by:* Goal-based: the literal
      appears in the frontend copy, which the drift gate makes true of all four.
- [x] **AC-0003.** `docs/adr/` carries a new record for this decision, at the
      ordinal allocated from current repository state, and its `Status` reads
      `Accepted`. *Verified by:* Goal-based:
      `test -f <the ADR> && grep -qE '^- \*\*Status:\*\* Accepted' <the ADR> && python3 .claude/skills/new-adr/scripts/lint-adr-shape.py docs/adr`
      exits 0. The status read is needed because the shape lint's `_STATUS_TOKENS`
      admits `Proposed`, which is what the `new-adr` procedure leaves a new record
      at — so the lint alone would tick an "accepted" claim on an unsigned record.
      The record is named in the command rather than left to the lint's
      whole-directory scan, which exits 0 on the unchanged tree. What that record
      *says* is AC-0047.
- [x] **AC-0004.** `docs/specs/digital-experience-contract/spec.md`'s `Status` field
      reads the convention's supersession form, naming the new ADR, with no other
      change to the file. *Verified by:* Goal-based, two commands because the two
      predicates fail separately:
      `grep -qE '^- \*\*Status:\*\* Shipped \(superseded in part by ADR-[0-9]{4}.*everything else stands\)' docs/specs/digital-experience-contract/spec.md`
      exits 0 for the form — the bare `ADR-NNNN` spelling the anchored
      convention states, which is what T8's approach writes, and `git diff` over that file touches only its
      `Status` line for the scope. A diff-only check passes with that line reading
      anything at all.
- [x] **AC-0005.** `docs/specs/digital-experience-contract/plan.md` gains one `Status`
      metadata line — the field is absent today — carrying the same pointer in the
      `Done (superseded in part by …)` form, with no other change to the file.
      *Verified by:* Goal-based, two commands because the two predicates fail
      separately:
      `grep -qE '^- \*\*Status:\*\* Done \(superseded in part by ADR-[0-9]{4}.*everything else stands\)' docs/specs/digital-experience-contract/plan.md`
      exits 0 for the form — the bare `ADR-NNNN` spelling the anchored
      convention states, which is what T8's approach writes, and `git diff` over that file adds exactly one line,
      which is that `Status` line, for the scope.
- [x] **AC-0006.** `packs/frontend-engineering/.apm/skills/frontend-
      engineering/SKILL.md` names its pack-local `references/digital-experience-
      contract.md` as a file it loads. *Verified by:* Goal-based: the path appears in
      that `SKILL.md` and resolves on disk.
- [x] **AC-0007.** `packs/experience-design/.apm/skills/design-review/SKILL.md` names
      its pack-local `references/digital-experience-contract.md` as a file it loads.
      *Verified by:* Goal-based: the path appears in that `SKILL.md` and resolves on
      disk.
- [x] **AC-0008.** The contract carries a state-coverage map in which each of the 18
      frontend states appears exactly once. *Verified by:* TDD:
      `test_the_map_covers_every_floor_state_exactly_once` and
      `test_the_map_is_the_size_the_floor_states`.
- [x] **AC-0009.** Every state line the screen-brief template carries resolves in the
      map to at least one named member of the 18-state set, including the line that
      names two. *Verified by:* TDD: `test_every_brief_state_line_resolves_in_the_map`
      and `test_the_compound_brief_line_resolves_to_two_states`.
- [x] **AC-0010.** Each of the 18 states is assigned in the map to exactly one risk-tier
      band or is marked conditional on a named trigger. *Verified by:* TDD:
      `test_every_state_is_assigned_to_one_band_or_marked_conditional` and
      `test_a_conditional_state_names_its_trigger`.
- [x] **AC-0011.** Each of `explore`, `pilot`, and `production` carries at least one
      unconditional state. *Verified by:* TDD:
      `test_every_band_carries_at_least_one_unconditional_state`.
- [x] **AC-0012.** The map records, for each of the 18 states, whether its absence fails
      WCAG 2.2 AA. *Verified by:* TDD: `test_every_state_records_a_wcag_flag`, which
      refuses any value but `yes` or `no` so a missing flag cannot read as `no`.
- [x] **AC-0013.** Every state the map records as failing WCAG 2.2 AA when absent cites
      the success criterion that judgement rests on. *Verified by:* TDD:
      `test_an_accessibility_bearing_state_names_its_success_criterion`.
- [x] **AC-0014.** No tier band omits a state the map records as failing WCAG 2.2 AA
      when absent: every such state is assigned to `explore` or to a named conditional
      trigger that binds at every tier. *Verified by:* TDD:
      `test_no_tier_drops_an_accessibility_bearing_state`.
- [x] **AC-0015.** For each of `explore`, `pilot`, and `production`, the contract-field
      count stated in each journey equals the number of `<!-- Required: -->` annotations
      in the contract at that tier or any lower tier. *Verified by:* TDD:
      `test_the_stated_counts_equal_the_contracts_cumulative_obligation`, with
      `test_the_journey_states_the_whole_ladder` first so an omitted tier cannot pass by
      not being compared.
- [x] **AC-0016.** `guides/core/explanation/digital-experience-contract.md` states no
      per-tier field count. *Verified by:* Goal-based:
      `! grep -qiE '\b([0-9]+|one|two|three|four|five|six|seven|eight|nine|ten|twenty-five|thirty-two)[ -]fields?\b' guides/core/explanation/digital-experience-contract.md`
      exits 0. Spelled forms are covered as well as digits, because the page's real
      obligations are 10 / 25 / 32 and a rewrite spelling one of them would pass a
      digits-only pattern.
- [x] **AC-0017.** `guides/core/explanation/digital-experience-contract.md` states no
      per-tier field list, referencing the contract's own annotations instead. *Verified
      by:* Review-only: a reading of that page's three-tier table at the human gate. No
      artifact can decide whether prose references rather than restates.
- [x] **AC-0018.** `packs/experience-design/JOURNEY.md` lists `frontend-engineering` in
      `relatedJourneys`. *Verified by:* TDD:
      `test_each_journey_names_the_other_pack_in_related_journeys`, which checks both
      directions.
- [x] **AC-0019.** Both `JOURNEY.md` files name the three crossing artifacts by their
      `<output_dir>`-relative paths `direction/<slug>.md`, `screens/<slug>/<screen>.md`,
      and `tokens/<slug>.md`. *Verified by:* TDD:
      `test_each_journey_names_the_three_crossing_artifacts`.
- [x] **AC-0020.** Every row of the say-this table in `packs/experience-
      design/JOURNEY.md` carries exactly one of `Required`, `Optional`, or `Choose one`.
      *Verified by:* TDD: `test_every_say_this_row_carries_exactly_one_optionality`,
      which walks every row rather than sampling.
- [x] **AC-0021.** For `design-system` and `content-design`, the optionality marked in
      `packs/experience-design/JOURNEY.md` equals the one marked in the corresponding
      `guides/experience-design/how-to/` table. *Verified by:* TDD:
      `test_the_say_this_optionality_agrees_with_the_how_to_guides`, which reads both
      tables rather than pinning the values.
- [x] **AC-0022.** `packs/experience-design/JOURNEY.md` states the minimal viable thread
      as a named path through the pack. *Verified by:* TDD:
      `test_the_design_journey_names_its_minimal_viable_thread`.
- [x] **AC-0023.** `packs/experience-design/DESIGN.md`'s claim about skipping a step and
      the minimal viable thread it introduces do not contradict each other. *Verified
      by:* Review-only: a reading of those two adjacent passages at the human gate.
      Whether two sentences contradict is not decidable by a parser.
- [x] **AC-0024.** No illustrative state list under `packs/experience-design/` names a
      state outside the 18-state set. *Verified by:* TDD:
      `test_no_illustrative_state_list_names_a_state_outside_the_floor`.
- [x] **AC-0025.** Every illustrative state list under `packs/experience-design/` is a
      subset of the `explore` state subset the journey states. *Verified by:* TDD:
      `test_every_illustrative_state_list_is_within_the_explore_subset`.
- [x] **AC-0026.** `packs/frontend-engineering/JOURNEY.md` states each of the four
      proportionality allowances its skill already carries: a contract proportional to
      risk, omitting inapplicable states, a narrowed retrofit state matrix, and the
      optional CSS token gate. *Verified by:* TDD:
      `test_the_frontend_journey_carries_its_four_proportionality_allowances`, matching
      the words that carry each allowance rather than a fixed sentence.
- [x] **AC-0027.** Each journey states the `explore` tier's contract-field count.
      *Verified by:* TDD: `test_the_journey_states_the_whole_ladder`, which fails
      when a tier is unstated.
- [x] **AC-0028.** Each journey states the `explore` tier's state subset. *Verified by:*
      TDD: `test_the_explore_subset_is_the_maps_explore_band`, which cannot run without
      the stated subset.
- [x] **AC-0029.** The frontend journey states the rendered-page capture count a route
      owes, and that the count does not change with the tier. *Verified by:* Review-
      only: a reading of the depth sub-stage at the human gate. The capture contract is
      channel-derived, so no artifact relates a tier to a count.
- [x] **AC-0030.** The frontend journey states which of the five gates run at the
      `explore` tier. *Verified by:* Review-only: a reading of the depth sub-stage at
      the human gate, against the GATES section of the frontend skill.
- [x] **AC-0031.** Each journey states what the `explore` tier drops relative to
      `production`. *Verified by:* Review-only: a reading of the depth sub-stage at the
      human gate. The sub-stage sits where both journey lints stop scanning.
- [x] **AC-0032.** Each journey's stated `explore` state subset contains every state the
      map records as failing WCAG 2.2 AA when absent and assigns to a tier band.
      *Verified by:* TDD:
      `test_the_explore_subset_keeps_every_accessibility_bearing_state`.
- [x] **AC-0033.** Each journey's stated `explore` state subset equals the map's
      `explore` band exactly. *Verified by:* TDD:
      `test_the_explore_subset_is_the_maps_explore_band`. Asserted beyond containment
      because a superset makes the cheap path more expensive than the contract asks.
- [x] **AC-0034.** Each journey carries a sentence telling a reader that `explore` drops
      no accessibility-bearing state. *Verified by:* Review-only: a reading at the human
      gate. The property itself is covered above; this criterion is about the reader
      being told.
- [x] **AC-0035.** Every existing test assertion over
      `packs/frontend-engineering/JOURNEY.md` still passes, including the
      byte-exact `PINNED_SKIP_COST` block and the assertion that `whatChanges`
      does not contain `independent diff read`.
      *Verified by:* Goal-based: the four suites that assert over that file all
      pass — `test_rendered_page_journey_promise.py`,
      `test_rendered_page_reviewer_sight.py` and `test_rendered_page_verdict.py`
      under `packs/frontend-engineering/tests/skills/frontend-engineering/`, and
      the repository-level `tools/test_journey_editorial_decisions.py`, a named
      `build-check.yml` step that pins every journey's `humanGates` and forbids
      an `eyebrow` key. That set is the exhaustiveness mechanism, and it was
      measured rather than assumed: the other suites reading a `JOURNEY.md` read
      `packs/core/JOURNEY.md`, a fixture journey, or pack names only. One
      invocation of the fourth decides both journeys' pins, so the design
      journey needs no separate criterion.
- [x] **AC-0036.** `tools/lint-pack-journeys.py`, `tools/lint-journey-contract.py`, and
      `tools/lint-web-journey-parity.py` each exit 0. *Verified by:* Goal-based: run
      each.
- [x] **AC-0037.** The committed `web/src/content/journeys/` copies for both packs are
      byte-equal to the output of `python3 tools/build-site.py --journeys-only`.
      *Verified by:* Goal-based: regenerate, then `git diff --exit-code
      web/src/content/journeys/`.
- [x] **AC-0038.** `.github/workflows/build-check.yml` names a step for each of the two
      new tests, each at a lower step index than the job's bulk `pytest tests/ -q` step.
      *Verified by:* Goal-based: a YAML parse of the `gate-main` job comparing step
      indices. The parity lint cannot see placement.
- [x] **AC-0039.** `tools/lint-ci-parity.py` exits 0 with both new step names carrying a
      disposition. *Verified by:* Goal-based: run it. It reads both roster axes, so a
      step registered on only one fails here.
- [x] **AC-0040.** `tools/lint-experience-agnostic.py` exits 0 over
      `packs/experience-design/` after this change, so no edit introduces a value
      literal or platform token into that tree. *Verified by:* Goal-based: run it.
      A preservation criterion: it is green today and must stay green. That the
      state-coverage map is present is AC-0008, and that all four copies carry it
      is AC-0001; the lint decides neither.
- [x] **AC-0041.** `.claude-plugin/marketplace.json` is byte-identical to the output of
      a fresh unforced self-host run. *Verified by:* Goal-based: run unforced `make
      build-self` on a clean tree, then `git diff --exit-code .claude-
      plugin/marketplace.json`.
- [x] **AC-0042.** Each of the four packs carrying a contract copy —
      `product-strategy`, `product-engineering`, `experience-design`,
      `frontend-engineering` — states a `pack.toml` version differing from its
      pre-change value, and its `.claude-plugin/plugin.json` states the same
      version. *Verified by:* Goal-based: for each of the four, compare
      `pack.toml` against `git show origin/main:packs/<pack>/pack.toml` and
      against its `plugin.json`. Quantified over the four by name rather than
      over "each bumped pack", which is satisfied by bumping none.
- [x] **AC-0043.** `agentbundle catalogue verify --root .` exits 0. *Verified by:* Goal-
      based: run it. It reports a stale `.claude/` or `.agents/` projection as
      `CAT-V-015`. Measured: `catalogue self-host --check` also catches a stale
      projection, while `catalogue lint --deep`, `lint-ruff`, `lint-mypy` and the
      pack suites do not. Only `core` has declared host projections in this tree,
      so this delivery's non-core `.apm/` edits produce no `.claude/` or
      `.agents/` delta — the criterion is preservation, not a change this
      delivery makes.
- [x] **AC-0044.** Each of the four contract-carrying packs this change updates
      has an `evals/evals.json` case covering the behaviour the change gives it.
      *Verified by:* Review-only: a reading at the human gate. `catalogue verify`
      validates that manifest's shape, never whether a case is apt. Quantified
      per pack rather than per edited `SKILL.md`, because `packs/AGENTS.md`
      states the eval obligation per pack for any non-cosmetic update — and this
      change bumps all four, which is its own declaration that all four are
      non-cosmetic.
- [x] **AC-0045.** For each of those same four packs, the topmost
      `## [<pack>][<version>] — YYYY-MM-DD` heading in `docs/product/changelog.md`
      names the version its `pack.toml` now states, and that version differs from
      the one the topmost heading named before this change.
      *Verified by:* Goal-based: for each of the four, compare the changelog's
      first `## [<pack>][` line against that pack's `pack.toml` and against
      `git show origin/main:docs/product/changelog.md`. The second half is what
      stops the criterion passing before any bump: all four headings already
      name their pack's current version today.
- [x] **AC-0046.** The changelog headings this change adds are exactly one per
      contract-carrying pack, each sits at `##`, `core`'s own newest
      `## [core][` entry stays first after `[Unreleased]`, and the four follow it
      contiguously and above every older entry.
      *Verified by:* Goal-based: diff the ordered `^## \[<pack>][<version>]` list
      against `git show origin/main:docs/product/changelog.md` to identify the
      added set, then read the order. A baseline is required: the current file
      alone cannot say which headings this change added, and without it the only
      decidable conjunct — `core` first — is already true today.
- [x] **AC-0047.** That ADR's `## Decision` section names the
      `frontend-engineering` pack as the owner of the contract's frontend section.
      *Verified by:* Goal-based:
      `awk '/^## Decision$/{f=1;next} /^## /{f=0} f' <the ADR> | grep -q 'owner: frontend-engineering'`
      exits 0. Section-scoped rather than file-scoped, because an ADR that named the
      pack only in its Context would pass a whole-file match; the shape lint reads
      structure and no part of it reads Decision prose.
- [x] **AC-0048.** Each of the four new changelog entries carries a recorded
      `Highlights` disposition: a `### Highlights` subsection holding at least
      one bullet. Whether a bullet is outcome-led is `docs/product/changelog.md`'s
      own standard and no command decides it, so this criterion does not restate
      it.
      *Verified by:* Goal-based: for each of the four packs, read the **topmost**
      `## [<pack>][` entry and assert its `### Highlights` subsection holds a
      bullet. Topmost, not any entry: three of the four packs already have an
      older entry carrying the subsection, so an unqualified read goes green off
      history. That the topmost entry is the one this change added is AC-0045's
      baseline read, so this criterion does not repeat it. The disposition is
      owed per released entry and nothing downstream makes the call:
      `tools/check-core-release.py` reads `packs/core/pack.toml` and runs in no
      Makefile or workflow target. This delivery's verdict is bullets rather
      than a recorded `none`, because four packs gaining a shared state-coverage
      map and a selectable depth ladder changes what a pack consumer can do.

## Follow-ons

- Pack maintainer: five counts derived by hand from the state-coverage map
  and the `Required:` annotations sit in eight homes and nothing reads them —
  "Explore owns ten states, pilot adds four, production adds two" and
  "drops six of the sixteen banded states and none of the eight marked `yes`"
  in the four contract copies, and "drops 22 contract fields and 6 states" in
  both journeys. Every one is derivable from data the two roster modules
  already parse. A mechanical pin is not available here: AC-0031 assigns the
  journey paragraph to Review-only by owner decision. Re-banding one state
  leaves all five wrong with every gate green.
- Pack maintainer: the committed `web/src/content/journeys/` copies have no
  standing comparison against their source `JOURNEY.md`. AC-0037 checks
  regeneration once at delivery; `lint-web-journey-parity.py` compares only
  skill counts, `build-check.yml` has no regeneration step, and `pages.yml`
  regenerates before building without diffing the committed copies. The only
  thing keeping them honest is an `Always do` rule scoped to this spec, so the
  next editor of either journey gets a green board with a stale copy.
- Pack maintainer: `packs/experience-design/.apm/skills/*/evals/*.json` pin
  literal `docs/design/...` paths. Whether an eval fixture should track a
  configurable default is a design question neither spec settles.
- Pack maintainer: `screens/` holds both `<slug>.md` and `<slug>/` — a file and a
  directory sharing a stem — once `design-output-addressing` corrects the guide
  that assigns the former. Whether `design-review`'s findings list belongs in
  `screens/` at all is a separate decision.
- Pack maintainer, owner-directed and deferred (evidence: owner decision
  2026-09-16): flip `[design] output_dir` from `docs/design` to `docs/ux` and
  migrate this repository's own tree, per `design-output-addressing`'s follow-on.

## Assumptions

- Product: whether a per-state WCAG-bearing flag should be a machine-readable
  field the accessibility gates read, rather than a column a roster test parses —
  it would move the flag from documentation into tooling (settled by: the pack
  maintainer, once a second consumer of the flag exists).
