# Spec: frontend-experience-composition

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the Digital Experience Contract template is pack content,
  not a `contracts/` artifact.
- **Shape:** mixed
- **Depends on:** [`docs/specs/design-output-addressing/`](../design-output-addressing/spec.md)
  — the three artifacts this spec makes the packs agree about only have addresses
  once that spec ships. The frontend *read* of those artifacts is a third spec,
  [`docs/specs/design-handoff-read/`](../design-handoff-read/spec.md), independent
  of this one; this spec names the artifacts in both journeys and does not read them.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: an author corrects them in place as the work teaches.

## Objective

The two packs agree about states and about depth. One shared state-coverage map
says how each state line a screen brief carries relates to the eighteen states
the frontend quality floor enumerates, and both packs cite that one map instead
of each keeping its own vocabulary. The contract that carries the map is loaded
by a skill in each pack rather than guarded as content nothing reads, and its
frontend section names the pack that owns it rather than the pack that used to.

Depth is selectable and cheap by default. Both journeys surface the `risk-tier`
value the shared contract already defines and the frontend skill already
consumes, state what the cheapest tier drops, and mark each step Required,
Optional, or Choose one in the vocabulary the how-to guides already use. Tier
obligations are stated once and checked against the contract's own annotations,
so a depth ladder cannot silently go stale. Accessibility is not part of what a
tier drops at any level.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — adopters choose depth and see the crossing artifacts | both `JOURNEY.md` files, `guides/experience-design/how-to/`, `guides/frontend-engineering/how-to/` | Guide author | Each journey states its tier obligations and its optionality; each new capability has a how-to | The guide lints exit 0 and the tier-count test agrees with the contract |
| Current product truth | Applicable — a fifth home for the tier table is stale today | `guides/core/explanation/digital-experience-contract.md` | Guide author | That page's tier claims agree with the contract's annotations, or it references rather than restates them | No tier claim contradicts the contract |
| Interface compatibility | Applicable — four packs carry the contract byte-identically | the four `digital-experience-contract.md` copies | Pack maintainer | `check-contract-drift` step in the build-check chain passes | All four copies byte-identical |
| Decision rationale | Applicable — the frontend section's owner label changes on a frozen record | `docs/adr/` | ADR author | An ADR records that the frontend discipline is owned by its own pack | ADR accepted and cited by the superseded spec's Status line |
| Operations | Applicable — two new tests are worthless unless CI runs them | `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py` | Maintainer | Both tests named as steps with matching dispositions | `tools/lint-ci-parity.py` exits 0 |
| Release history | Applicable — four packs bump | `docs/product/changelog.md` | Release author | One released entry per bumped pack, topmost for that artifact | Topmost entry per pack names its new `pack.toml` version |
| Reusable learning | Applicable | `project-knowledge` seam | Work-loop | Receipt or `project-knowledge unavailable` | Recorded at the terminal gate |

## Boundaries

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
  `packs/frontend-engineering/JOURNEY.md` carries thirteen across three suites,
  including one byte-exact block and one negative assertion a positive-only
  check cannot catch.
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
  `.github/workflows/`, `tools/lint-ci-parity.py`, the pack test trees, and the
  generated `web/src/content/journeys/` copies.
- Never let any tier band omit a state whose absence fails WCAG 2.2 AA.
  Accessibility is non-waivable under the root `AGENTS.md`, in the same class as
  trust-boundary validation.
- Never edit the body of a frozen Shipped spec, including appending a line. The
  only mutable field is `Status`.
- Never edit a lint, test, or checker to make a failing gate pass.

## Testing Strategy

- **The four contract copies stay identical, and the annotation position holds** —
  goal-based check. The `check-contract-drift` step in the build-check chain
  compares bytes and exits non-zero on any divergence, so the gate is the check.
- **The state-coverage map is complete, disjoint, and total over the brief** —
  TDD. A compressible invariant over two closed sets parsed from the artifacts:
  the 18-state table and the screen-brief template's state lines. This is the
  property a reviewer cannot verify by eye without recounting.
- **Tier obligations agree with the contract's annotations** — TDD. The test
  computes each tier's cumulative annotation count from the contract and compares
  it with the count each journey states. Cumulative, because the annotation form
  is `<tier>+` and means that tier and above.
- **A tier band never drops an accessibility-bearing state** — TDD, as a separate
  check from the count comparison. The map records, per state, whether its
  absence fails WCAG 2.2 AA; the test reads that field rather than judging it, so
  the predicate is decidable.
- **Journey optionality renders and the existing pins survive** — goal-based
  check. The three journey lints plus the thirteen existing assertions over
  `packs/frontend-engineering/JOURNEY.md`.
- **The depth selector is not covered by the journey lints** — stated here
  explicitly because it sits in a `####` sub-stage those lints cannot read. Its
  only gate is the tier-count agreement test.
- **The two new tests actually execute** — goal-based check. A roster test runs
  under `pytest tests/` but on no pull request unless named as a `build-check.yml`
  step with a matching `lint-ci-parity.py` disposition.

## Acceptance Criteria

- [ ] The `check-contract-drift` step passes: all four
      `digital-experience-contract.md` copies are byte-identical.
- [ ] The contract's frontend section heading reads
      `## Frontend Engineering [owner: frontend-engineering]`.
- [ ] An ADR records that the contract's frontend discipline is owned by the
      `frontend-engineering` pack rather than `core`.
- [ ] `docs/specs/digital-experience-contract/spec.md`'s `Status` field reads
      `Shipped (superseded in part by ADR-NNNN — <what changed>; everything else stands)`,
      naming that ADR, with no other change to the file.
- [ ] `docs/specs/digital-experience-contract/plan.md`'s `Status` field carries the
      same pointer in the `Done (superseded in part by …)` form, with no other
      change to the file.
- [ ] `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` names
      its pack-local `references/digital-experience-contract.md` as a file it loads.
- [ ] `packs/experience-design/.apm/skills/design-review/SKILL.md` names its
      pack-local `references/digital-experience-contract.md` as a file it loads.
- [ ] The contract carries a state-coverage map in which each of the 18 frontend
      states appears exactly once.
- [ ] Every state line the screen-brief template carries resolves in the map to at
      least one named member of the 18-state set, including the line that names two.
- [ ] Each of the 18 states is assigned in the map to exactly one risk-tier band
      or is marked conditional on a named trigger.
- [ ] Each of `explore`, `pilot`, and `production` carries at least one
      unconditional state.
- [ ] The map records, for each of the 18 states, whether its absence fails
      WCAG 2.2 AA.
- [ ] No tier band omits a state the map records as failing WCAG 2.2 AA when absent.
- [ ] For each of `explore`, `pilot`, and `production`, the contract-field count
      stated in each journey equals the number of `<!-- Required: -->` annotations
      in the contract at that tier or any lower tier.
- [ ] No tier claim in `guides/core/explanation/digital-experience-contract.md`
      contradicts the contract's annotations.
- [ ] `packs/experience-design/JOURNEY.md` lists `frontend-engineering` in
      `relatedJourneys`.
- [ ] Both `JOURNEY.md` files name the three crossing artifacts by their
      `<output_dir>`-relative paths.
- [ ] Every row of the say-this table in `packs/experience-design/JOURNEY.md`
      carries exactly one of `Required`, `Optional`, or `Choose one`.
- [ ] For `design-system` and `content-design`, the optionality marked in
      `packs/experience-design/JOURNEY.md` equals the one marked in the
      corresponding `guides/experience-design/how-to/` table.
- [ ] `packs/experience-design/JOURNEY.md` states the minimal viable thread as a
      named path through the pack.
- [ ] `packs/frontend-engineering/JOURNEY.md` states each of the four
      proportionality allowances its skill already carries: a contract
      proportional to risk, omitting inapplicable states, a narrowed retrofit
      state matrix, and the optional CSS token gate.
- [ ] Each journey states, for the `explore` tier, the contract-field count, the
      state subset, the rendered-page capture count, and which gates run.
- [ ] Every existing test assertion over `packs/frontend-engineering/JOURNEY.md`
      still passes, including the byte-exact `PINNED_SKIP_COST` block and the
      assertion that `whatChanges` does not contain `independent diff read`.
- [ ] `tools/lint-pack-journeys.py`, `tools/lint-journey-contract.py`, and
      `tools/lint-web-journey-parity.py` each exit 0.
- [ ] The committed `web/src/content/journeys/` copies for both packs are
      byte-equal to the output of `python3 tools/build-site.py --journeys-only`.
- [ ] `.github/workflows/build-check.yml` names a step for each of the two new
      tests, and `tools/lint-ci-parity.py` exits 0 with both step names carrying
      a disposition.
- [ ] `tools/lint-experience-agnostic.py` exits 0 over `packs/experience-design/`
      with the state-coverage map present in its contract copy.
- [ ] `.claude-plugin/marketplace.json` is byte-identical to the output of a fresh
      self-host run and names each bumped pack's new version.
- [ ] `agentbundle catalogue verify --root .` exits 0.
- [ ] Each skill whose `SKILL.md` this change edits has an `evals/evals.json` case
      covering the behaviour this change gives it.
- [ ] For each bumped pack, the topmost `## [<pack>][<version>] — YYYY-MM-DD`
      heading in `docs/product/changelog.md` names that pack's new `pack.toml`
      version, at the level directly beneath `[Unreleased]`.

## Follow-ons

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

- Technical: the four contract copies must be byte-identical, and the
  `check-contract-drift` step is registered in the build-check chain, so this is
  a CI-blocking gate rather than a manual tool
  (source: `tools/repo/check_contract_drift.py:194`; `tools/repo/build_gate_chain.py:566-567`)
- Technical: the drift checker's structural fingerprint reads the first non-blank
  line after each `###` heading, so inserting content after the `Required:`
  annotation preserves it (source: `tools/repo/check_contract_drift.py:75-93`)
- Technical: `<!-- Required: <tier>+ -->` is cumulative — the owning explanation
  states Pilot as "Everything in Explore, plus:" and Production as "Everything in
  Pilot, plus:" — so the fields owed are the annotations at that tier and below
  (source: `guides/core/explanation/digital-experience-contract.md:22-28`)
- Technical: the contract carries 10 `explore+`, 15 `pilot+`, and 7 `production+`
  annotations across 32 sections, so the cumulative obligations are 10, 25 and 32
  (source: `grep -c` over the annotations)
- Technical: `guides/core/explanation/digital-experience-contract.md:14` and `:30`
  say seven fields are required at explore tier, where the contract annotates ten,
  and that page sits outside the drift checker's four copies
  (source: read of that file against the annotation count)
- Technical: the screen-brief template carries seven state lines — `empty`,
  `loading`, `error`, `success/default`, `partial`, `disabled`, and
  `permission/denied (if gated)` — and `success/default` is a compound resolving
  to two members of the 18-state set; `quality-floor.md` states the same set as
  six base states plus a named gated extension
  (source: `packs/experience-design/.apm/skills/user-flow/assets/screen-brief-template.md:45-52`;
  `.../design-review/references/quality-floor.md:17-45`)
- Technical: the five-state list at `packs/experience-design/JOURNEY.md:182` is an
  illustrative transcript, not a registry: it names `default`, which is not a
  floor state, and omits `partial` and `disabled` (source: read of that line)
- Technical: the frontend quality floor enumerates exactly 18 states
  (source: `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md:225-242`)
- Technical: `risk-tier` is already consumed by the frontend skill for its
  production-only manifest fields, and appears in no journey or guide
  (source: `.../frontend-engineering/SKILL.md:851-856`; `grep -rn "risk-tier" packs/*/JOURNEY.md guides/`)
- Technical: both journey lints break their per-stage label scan on a line
  starting `##`, so a `####` sub-stage placed after the parent's labels is
  invisible to them (source: `tools/lint-pack-journeys.py:108-110`;
  `tools/lint-journey-contract.py:145`)
- Technical: `packs/frontend-engineering/JOURNEY.md` is pinned by thirteen
  assertions across `test_rendered_page_journey_promise.py`,
  `test_rendered_page_reviewer_sight.py`, and `test_rendered_page_verdict.py`,
  including a byte-exact `PINNED_SKIP_COST` block and a negative assertion on
  `whatChanges` (source: read of all three suites)
- Technical: a roster test runs under `pytest tests/` but on no pull request
  unless named as a `build-check.yml` step with a matching `lint-ci-parity.py`
  disposition (source: `tests/AGENTS.md`; `tools/AGENTS.md`; `tools/lint-ci-parity.py:360-372`)
- Technical: a frozen Shipped spec takes a supersession pointer in its `Status`
  field and only there, in a fixed form, pointing at the ADR rather than at the
  implementing spec, and no body edit is permitted
  (source: `docs/CONVENTIONS.md:149-176`)
- Technical: `docs/specs/digital-experience-contract/spec.md` is `Shipped` and a
  ticked criterion pins the four discipline headings including
  `## Frontend Engineering [owner: core]` (source: read of that spec)
- Technical: `.claude-plugin/marketplace.json` is generated by the
  `composite-marketplace` recipe from each pack's `plugin.json`; neither pack in
  scope has a projected skill tree
  (source: `packages/agentbundle/agentbundle/build/recipes/self-host.toml:26,51-54`)
- Technical: `experience-design` rejects every value literal and platform token,
  CI-blocking, and all 18 state names clear its patterns — `reduced-motion` is
  legal, only `prefers-reduced-motion` matches
  (source: `tools/lint-experience-agnostic.py`; `.github/workflows/build-check.yml:836`)
- Process: every non-cosmetic pack-content change bumps matching versions and
  updates that pack's eval harness (source: `packs/AGENTS.md`)
- Process: each phase ships its guide (source: `docs/CONVENTIONS.md:1130`)
- Process: a changelog entry is owed in the PR that bumps a released artifact, and
  a released heading sits directly beneath `[Unreleased]` (source: `docs/CONVENTIONS.md:717-726`)
- Product: the depth selector rides in body prose and a `####` sub-stage rather
  than a journey contract key, because tier is a per-run value and a journey key
  holds only a constant (source: user confirmation 2026-09-16)
- Product: the state map and tier ladder are derived during execution against the
  real artifacts rather than argued at review; the criteria state the invariants
  and the plan carries the partition as a starting hypothesis
  (source: user confirmation 2026-09-16)
- Product: this spec is the composition and depth half of a two-spec split and
  depends on `design-output-addressing` (source: user confirmation 2026-09-16)
