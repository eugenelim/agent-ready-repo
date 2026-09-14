# Spec: DECIDE ladder follow-ons

- **Status:** Implementing
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** `docs/product/findings/roadmap-intents.md`
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
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Objective

The four open DECIDE-ladder findings in the roadmap register have one bounded
delivery. A claim that reaches beyond its check keeps its obligation when some
check can reach it and narrows only when none can; repair guidance requires the
check to assert the property itself. Review repairs use both a literal sweep and
a semantic walk, and rerun the anchor-test sweep over every file the repair
touches.

An upstream demotion may use revision-bound lifecycle invalidation as its pin.
`Opportunity` is material to intent review, while `Rabbit holes` and `Design
artifacts` are material to delivery-brief review. Downstream demotions continue
to use content tests.

Mutation-proof guidance has one routed owner. A proof restores the pre-fix
implementation by editing, exercises an exact mutation against a stated
invariant, and records the expected and observed failure. It links to the
existing verification-ledger owner instead of copying that owner's placement
rule.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | The response ladder and post-repair traversal are shipped guidance | `packs/core/.apm/skills/work-loop/SKILL.md` | core pack | Region-scoped content tests and the post-edit body-line count | DECIDE carries the three bounded refinements without changing the answer set, names, or order |
| Shaping lifecycle | Upstream demotion pins depend on revision-bound invalidation | `packs/core/.apm/skills/intake-intent/SKILL.md`; `packs/core/.apm/skills/author-delivery-brief/SKILL.md` | core pack | Destination-specific lifecycle tests | Guidance classifies all three destinations as material and carries the demotion instruction |
| Mutation-proof procedure | The pack lacks one owner for the proof discipline | `packs/core/.apm/skills/work-loop/references/mutation-proof.md` | core pack | Routing-table and obligation content tests, with observed mutation reds in the verification ledger | The reference is reachable from conditional-reference routing and links to the ledger owner |
| Skill eval registers | Each non-cosmetic change to work-loop, intake-intent, and author-delivery-brief updates that skill's eval harness | Each changed skill's `evals/evals.json` | core pack | Catalogue structural lint and one content pin per new eval entry | All three changed skills carry a structurally valid eval case for their changed guidance; no claim is made that the register entries executed |
| Product truth | Exactly four roadmap rows enter this delivery, and R4's evidence needs correction | `docs/product/findings/roadmap-intents.md` | product maintainer | Four dispositions point to this spec; R4 names all three non-state-change occurrences | The four rows are closed without adjacent register cleanup |
| Release history | The change alters shipped core-pack guidance | `docs/product/changelog.md` | release maintainer | A new `core` 2.25.25 section and grounded highlight | No released section is edited |

No architecture, public interface, or operations output applies. The change is
portable guidance, its lifecycle rules, their tests, and generated self-host
projections.

## Boundaries

### Always do

- Keep the answer set, answer tokens, and axis order unchanged.
- Protect each new prose rule with a region-wide class guard, a named exception,
  and a mutation test that proves the old or naive guard stays green while the
  new guard turns red.
- Bump `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`
  together from 2.25.24 to 2.25.25, then regenerate self-host projections from
  a clean source commit.

### Ask first

- Changing which answers are in the set, their names, or their order.
- Giving `response` or `reason` any effect on verdict state, readiness, or
  scoring.
- Making `response` or `reason` required.

### Never do

- Add a new ladder answer or treat R1 as an eleventh answer.
- Add an acceptance criterion for the R1, R2, or R4 guidance. The authoring
  protocol intent owns the deferred criteria and permits the prose to ship only
  with content pins.
- Add a top-level directory, a dependency, or an edit to any released changelog
  section.
- Put this catalogue's acceptance-criterion identifiers, decision-record
  ordinals, or repository-only governance paths into shipped pack prose.

## Testing Strategy

- **Intent `Opportunity` materiality (AC-0001): TDD.**
  `test_intent_opportunity_edit_is_material_lifecycle_change` mechanically
  extracts the intent materiality region and checks the destination-specific
  lifecycle classification. Its mutation removes only `Opportunity` and must
  red while the prior broad assertion remains green.
- **Brief `Rabbit holes` materiality (AC-0002): TDD.**
  `test_rabbit_holes_edit_is_material_lifecycle_change` checks the named
  destination against the complete brief materiality region. Its mutation
  removes only that destination and must red while the prior broad assertion
  remains green.
- **Brief `Design artifacts` materiality (AC-0003): TDD.**
  `test_design_artifacts_edit_is_material_lifecycle_change` uses the same
  region-wide oracle with an independent single-destination mutation.
- **R1 claim/check choice and direct-property repair: TDD content pin, no
  criterion.** The DECIDE test enumerates every Cut answer, admits the other
  three named answers as exceptions, and proves the pre-change
  `narrow-the-claim` text still satisfies the old guard but fails the two-way
  discriminator.
- **R2 dual traversal and post-repair rerun: TDD content pin, no criterion.**
  The DECIDE test inspects every traversal-instrument statement in its bounded
  region, names the frontier and termination statements as non-instrument
  exceptions, and proves the pre-change one-mode sentence passes the old quote
  guard but fails the literal-plus-semantic oracle. A second isolated mutation
  removes only the touched-file anchor-test rerun; the traversal-only guard
  stays green while the complete oracle reds.
- **R4 mutation-proof discipline and routing: TDD content pin, no criterion.**
  The reference test checks every proof obligation, names ledger placement as
  the linked external-owner exception, and proves a keyword-only guard accepts
  a mutation that permits a do-nothing stub while the obligation oracle rejects
  it.
- **Changed-skill eval harnesses: structural checks, no criterion.** Catalogue
  lint validates all three `evals.json` registers, and content pins require one
  changed-guidance case in each register. These checks do not claim that an eval
  runner executed the registered cases.
- **Projection and release coupling: goal-based checks.** The two roster tests
  named in the plan run after `make build-self`; version parity and the new
  release section are checked before the source commit.
- **PLAN stub coverage:** T1 covers 3/3 named tests, T2 covers 4/4, and T3
  covers 3/3. T4 through T7 are goal-based checks and therefore carry no
  stubs.

## Acceptance Criteria

- [ ] **AC-0001.** Intent guidance classifies an edit to `Opportunity` as
      material and instructs that a material edit invalidates prior review
      evidence and returns an accepted intent to `Draft` before a fresh review.
- [ ] **AC-0002.** Delivery-brief guidance classifies an edit to `Rabbit holes`
      as material and instructs that a material edit invalidates prior review
      evidence and returns a ready brief to `Draft` before a fresh review.
- [ ] **AC-0003.** Delivery-brief guidance classifies an edit to `Design
      artifacts` as material and carries the same demotion instruction.

## Follow-ons

None. Adjacent ladder, review, lifecycle, and mutation-testing changes remain
outside this four-row slice.

## Assumptions

- Technical: DECIDE has ten answers in four ordered axes, and
  `narrow-the-claim` currently preserves only the narrowing direction (source:
  `packs/core/.apm/skills/work-loop/SKILL.md`, user-confirmed investigation
  2026-09-13)
- Technical: `test_finding_response_fields.py` is the existing DECIDE content-pin
  suite; R2 necessarily changes its exact-sentence assertion while R1 can retain
  the existing narrowing clause (source: user-confirmed investigation
  2026-09-13)
- Technical: intent and delivery-brief materiality tests do not currently see
  the three destination omissions (source: user-confirmed investigation
  2026-09-13)
- Technical: the R4 register row's occurrence claim is inaccurate; the three
  non-state-change occurrences are `SKILL.md:528`,
  `references/delivery-contract-lifecycle.md:71`, and
  `scripts/_loop_guards.py:578`, while the absence of a mutation-proof
  obligation still holds (source: user-confirmed investigation 2026-09-13)
- Process: `docs/product/intents/spec-authoring-protocol-measured-before-shipping.md`
  owns deferred AC-0023 through AC-0027, including R1's AC-0024 discriminator,
  and its Boundary permits editing and shipping pinned prose without promoting
  it to a criterion (source: named intent and user confirmation 2026-09-13)
- Process: the owner has approved upstream lifecycle invalidation as the R3
  demotion pin and has not approved any change to the ladder answer set, names,
  order, or gating effect (source: user confirmation 2026-09-13)
- Product: this delivery contains exactly roadmap rows R1 through R4 and no
  adjacent cleanup (source: user confirmation 2026-09-13)
