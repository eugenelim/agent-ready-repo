# Spec: Visual handoff golden path

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0130, ADR-0132
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

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

A pack maintainer gets one executable check that the experience-design →
frontend-engineering visual handoff holds across the pack boundary: authority
resolves to the rung the installed rules name, the concrete values the taxonomy
resolved are the values the build declares, and no designed path reaches the
bundled fallback. Success is a roster test that installs both packs, walks six
fixture paths through the installed rules, and fails when either pack's shipped
contract, the fixtures, or the model-eval cases that grade the same paths drift
apart.

## What Changes

- A cross-pack roster test — `tests/roster/test_visual_handoff_golden_path.py`.
- The seven fixture directories Agent Rules § Ask first names, under
  `tests/roster/fixtures/visual-handoff-golden-path/`.
- Three new golden-path model-eval cases, and `expect` blocks on three existing
  visual-authority cases — `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json`.
- A frontend-engineering patch release — `pack.toml`, `.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, the release pin in
  `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_release.py`,
  and `docs/product/changelog.md`.
- CI registration of the new roster test — `.github/workflows/build-check.yml`,
  `tools/lint-ci-parity.py`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Reusable learning (executable contract) | The cross-pack handoff has no executable check | `tests/roster/test_visual_handoff_golden_path.py` and its fixtures | pack maintainer | the test passes and its mutation controls red | test registered in CI and green |
| Release history | The frontend pack's shipped eval content changes | `docs/product/changelog.md` | pack maintainer | a free-standing `## [frontend-engineering][<version>]` section | entry present at the bumped version |
| User-facing promise | Not applicable: no skill behaviour, guide, or journey changes; eval cases do not change what an adopter is promised | none | — | — | — |
| Current architecture | Not applicable: no module boundary or ownership changes | none | — | — | — |

## Agent Rules

### Always do

- Read every rule the roster test applies from the installed copies of both
  packs, never from `packs/` source.
- Write each golden eval prompt as starting after the design handoff read,
  stating what that read extracted, so the case needs no seeded file.
- Label every rendered-observation fact in the fixtures as fixture data; the
  test claims no visual verification.
- Keep concrete colour, size and timing values out of every file under
  `packs/experience-design/`.

### Ask first

- Any change to `agentbundle pack evals run`, its eval schema, or its fixture
  seeding.
- Any change to a shipped rule, table, template, or skill body in either pack.
- Any fixture directory beyond these seven: `confirmed`, `unconfirmed`,
  `missing-taxonomy`, `unresolved-domain`, `standalone`, `refusal`, and the
  record-only `no-browser`.

### Never do

- Add a browser, image, or third-party dependency, a new module boundary, or a
  new top-level directory.
- Add a visual-observer agent, split `creative-direction`, or restore a
  universal design default.
- Compare renders pixel for pixel, or report visual verification as passed.

## Testing Strategy

- **Authority, gap, refusal and fallback routing (AC-0001, AC-0002, AC-0003,
  AC-0004, AC-0005, AC-0006, AC-0007, AC-0008):** TDD, exercised as an
  integration test across both installed packs, because the routing is a
  compressible function of the installed tables and the fixture tree.
- **Value provenance and consumption (AC-0009, AC-0010, AC-0011, AC-0012,
  AC-0013, AC-0023):** TDD over the fixture taxonomy, incumbent file, and
  golden implementation, with an in-test mutation control proving the
  consumption check can fail.
- **Render, observe, correct, then gates (AC-0014, AC-0015, AC-0016, AC-0017,
  AC-0024):** TDD over run records checked against the installed loop rules,
  with in-test negative records. No render happens; the no-browser path is
  asserted as itself.
- **Golden eval cases (AC-0018, AC-0019, AC-0020):** TDD over the installed
  `evals.json`. Running those cases against a model is report-only and outside
  this contract.
- **Registration and release (AC-0021, AC-0022):** goal-based checks.

## Acceptance Criteria

- [x] **AC-0001.** The roster test installs `experience-design` and
      `frontend-engineering` into one temporary repository through
      `agentbundle install`, and every rule table, template field, refusal
      record, and fallback value it applies is parsed from that installation,
      fallback values from `references/fallback-tokens.md`; a
      table it needs that is absent from the installation fails the test.
- [x] **AC-0002.** On the `confirmed` fixture, the walk records composition from
      `approved-visual-target`, values from `direction-and-taxonomy`, every
      value domain sourced from the taxonomy, and a loaded-file set that
      excludes `references/fallback-tokens.md`.
- [x] **AC-0003.** On the `unconfirmed` fixture, the walk records
      `direction-and-taxonomy` for both composition and values, every value
      domain sourced from the taxonomy, a record that the direction does not
      carry `visual_target: confirmed`, and no fallback loaded.
- [x] **AC-0004.** On the `missing-taxonomy` fixture — a resolved direction, a
      named-skip taxonomy slot, and no incumbent system — the walk holds every
      value domain under operation kind `taxonomy-supply-required`, sources no
      domain from `local-premise` or the fallback, loads no fallback, and keeps
      composition at `direction-and-taxonomy`.
- [x] **AC-0005.** On the `unresolved-domain` fixture, the walk holds exactly
      the domain the taxonomy records unresolved under operation kind
      `domain-completion-required`, sources every other value domain from the
      taxonomy, loads no fallback, and writes each gap record with exactly the
      fields the installed `gap-record-contents` cell names: the axes held and
      the operation kind.
- [x] **AC-0006.** On the `standalone` fixture — no `[design]` section and no
      incumbent system — the walk records the named skip
      `design handoff: no [design] section configured`, reaches `local-premise`,
      loads the fallback, and records each of the installed standalone
      `admits` conditions as true.
- [x] **AC-0007.** On the `refusal` fixture — a non-conforming slug beside a
      direction and taxonomy that would otherwise resolve — the walk records
      the installed slug-refusal record, reaches no rung, sources no value
      domain, extracts no artifact, and loads no fallback.
- [x] **AC-0008.** Rewriting the installed `refusal-demotes` cell to `always`
      makes the `refusal` walk complete without raising and reach a rung, and
      rewriting the installed `approved-visual-target` `Requires` cell to
      `visual_target: none` makes the `confirmed` walk complete without raising
      and resolve composition at `direction-and-taxonomy`; a failure raised by
      the walk's unknown-vocabulary guard satisfies neither control.
- [x] **AC-0009.** In the `confirmed` fixture taxonomy's Authority table, Color
      carries `incumbent-system` and Spacing and rhythm carries
      `approved-direction`; every colour role traces to the fixture incumbent
      file, and every spacing role traces to a ranked goal of the fixture
      direction or a direction-sheet axis whose committed token is not
      `[platform-default]`. Whether those rung choices are the ones
      `design-system` would make is outside this check.
- [x] **AC-0010.** Every value a `confirmed`-fixture role traces to the
      incumbent file appears verbatim in that file.
- [x] **AC-0011.** Every pairing the `confirmed` fixture taxonomy lists under
      Accessibility names an element class from the installed frontend WCAG
      contrast-floor table and reaches that class's minimum ratio, computed
      from the taxonomy's resolved values with the WCAG 2.x relative-luminance
      formula; an absent table fails the test.
- [x] **AC-0012.** Every rung named in the `confirmed` fixture taxonomy's
      Authority table is a rung in the installed `design-system` rung table.
- [x] **AC-0013.** The golden implementation declares every colour and spacing
      role of the `confirmed` fixture taxonomy with exactly the taxonomy's
      value, declares no `--ds-` property, and its markup contains no raw
      colour literal; substituting the value `references/fallback-tokens.md`
      declares for `--ds-color-primary` into `--color-accent-action`, or its
      `--ds-space-3` value into `--space-3`, makes this check fail.
- [x] **AC-0014.** The installed frontend `SKILL.md` places its
      render-and-observe section before its `## GATES phase`, and the
      `confirmed` run record carries exactly one gate event per numbered `###`
      heading under that installed GATES phase, in heading order, every one
      after its last render, observe and correct event; every gate event
      records `ran` as true or false.
- [x] **AC-0015.** The `confirmed` run record holds at most the installed
      `correction-passes` count of corrections, exactly the installed
      `verification-renders-after-correction` count of renders after the
      correction, a correction citing a material gap whose class is in the
      installed divergence-class table, and its remaining divergence recorded
      as residual rather than corrected.
- [x] **AC-0016.** The run-record check rejects each of five negative records
      derived from the `confirmed` one: a gate before the first render, a
      second correction, an observation with no preceding captured render, no
      `primary-state` render, and no render of the conditional state the
      fixture declares applicable.
- [x] **AC-0017.** The `no-browser` run record contains no observe or correct
      event, names the missing capability in `manifest.unverified_items`, and
      carries exactly one gate event per numbered `###` heading under the
      installed `## GATES phase`, in heading order, where every event for a
      heading whose installed text says `requires Chromium` records `ran:
      false` with a non-empty `reason` and the rendered-page inspection event
      carries the installed result state `skipped-no-browser`; the check
      rejects the same record with any of those events set to `ran: true` or
      with any of their reasons emptied.
- [x] **AC-0018.** The frontend skill's `evals.json` carries cases
      `visual-golden-path-confirmed-values`,
      `visual-golden-path-unconfirmed-target` and
      `visual-golden-path-refusal-preserved`, each declaring no `files`, a
      non-empty `expect.output_contains`, an `expect.output_excludes` listing,
      in lower and upper case, the values `references/fallback-tokens.md`
      declares for `--ds-color-primary`, `--ds-color-surface-alt` and
      `--ds-color-on-surface`, at least one assertion beginning `Does not`,
      and at least one that does not.
- [x] **AC-0019.** The installed `expect.output_contains` of the
      `visual-golden-path-confirmed-values` and
      `visual-golden-path-unconfirmed-target` cases lists the `accent.action`
      and `surface.default` values of its own scenario's fixture taxonomy.
- [x] **AC-0020.** The existing cases
      `visual-authority-upstream-gap-missing-taxonomy` and
      `visual-authority-unresolved-domain` carry an `expect.output_excludes`
      listing those same fallback values, and
      `visual-authority-standalone` carries an `expect.output_contains` listing
      `local-premise`.
- [x] **AC-0021.** `build-check.yml` runs the roster test in a named step, and
      `python3 tools/lint-ci-parity.py` exits zero.
- [x] **AC-0022.** `frontend-engineering` carries one patch version above its
      merge-base version — `0.4.2` against today's `0.4.1` — identically in
      `pack.toml`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`
      and a free-standing `docs/product/changelog.md` heading, and
      `agentbundle catalogue lint --root . --deep` and
      `agentbundle catalogue verify --root .` exit zero.
- [x] **AC-0023.** The `confirmed` fixture taxonomy's Accessibility section
      records at least one adaptation — a role whose value moved to clear the
      floor — and that role appears in a pairing AC-0011 checks.
- [x] **AC-0024.** A state is a row of the installed representative-states
      table whose value begins `required`; it is conditional when its value
      begins `required where`. The `confirmed` fixture's `scenario.toml`
      declares at least one conditional state applicable, every render event in
      the `confirmed` run record names a state, and the rendered set includes
      every unconditional state and every declared conditional state.

## Follow-ons

- pack maintainer: `docs/product/intents/cross-pack-experience-eval.md` — the
  multi-pack eval runner and whole-journey harness that would run these paths
  as live agent sessions rather than as a table walk plus per-pack evals.

## Assumptions

- Technical: the golden eval cases are graded report-only and are not run in
  CI — whether an agent actually consumes the taxonomy values rests on those
  runs, not on the roster test.
