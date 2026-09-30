# Spec: visual-target confirmation

- **Status:** Archived (decomposed 2026-09-29 into `creative-direction-inherit-scope`, `visual-target-field` and `visual-target-rung-precondition`; not approved, not implemented) <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0131; [ADR-0130](../../adr/0130-design-to-build-handoff-is-conditional-and-gap-routed.md); [ADR-0128](../../adr/0128-design-system-one-skill-resolves-project-values.md); [`design-to-build-value-handoff`](../design-to-build-value-handoff/spec.md); [`frontend-visual-authority`](../frontend-visual-authority/spec.md); [`design-system-values`](../design-system-values/spec.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the crossing artifact is a pack-declared adopter path, not a `contracts/` record.
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author
> corrects them in place as the work teaches, without an amendment and without a
> review round. A review finding against working material is advisory — it
> cannot block, because nothing gates the text it cites.
>
> **This contract is capability-scoped.** No criterion below names a specific
> adopter repository or product.

## Why this contract was decomposed

This contract is retained as the record of four pre-EXECUTE review rounds, not
as work to be built. Its criteria were never approved and no code was written
against them.

Each round discovered carriers of the rule the previous round had not listed —
one in round 2, two in round 3, five in round 4 — and raw findings across both
reviewers ran 26, 19, 14, then 24, with blockers at their highest in the last
round. A measured sweep afterwards put the true extent at 59 loci across 25
files, recorded in [`notes/carrier-inventory.md`](notes/carrier-inventory.md).

Three mechanisms were tried and each failed the same way: presence checks left
the superseded reading alive, a closed retired-phrase set could not enumerate an
English reading, and a closed surface set could not enumerate surfaces not yet
found. All three assumed the author already knew the extent.

The successors split at the seam the findings drew: the inherit repair shares no
surface with the rest and ships alone; the field is additive within one pack;
and the rung precondition, where every round's findings concentrated, gets its
own contract with the inventory above as up-front discovery.

## Outcome

A direction artifact records whether its visual target is human-confirmed as
composition authority in one closed field, `visual_target`, separate from the
`status` field that records whether the direction itself was selected. The
`approved-visual-target` rung is available to a build only when that field reads
`confirmed`; every other reading, including a field that is absent, resolves
composition from `direction-and-taxonomy` or below. An unconfirmed target's
compositional commitments are not written into the direction artifact, so it
cannot bind composition from the rung below either.

## What Changes

- The direction template gains a `visual_target` frontmatter field with the
  closed set `none | unconfirmed | confirmed`, and its `## Approved visual
  target` section gains a `**Confirmation record:**` line carrying the
  confirmation's date and where it was recorded.
- `converge` writes the disposition explicitly, never writes `confirmed`
  without a recorded human confirmation, and writes compositional commitments
  only for a confirmed target.
- `frontend-engineering`'s authority-precedence table names `visual_target:
  confirmed` as the top rung's requirement, and a new rule table states the
  closed states, the absent-field reading, and what confirmation binds.
- `design-system`'s authority table names the same field as the rung's source.
- The public how-to guide for the handoff read describes the field and the
  absent-field reading.
- `creative-direction`'s `frame` operation scopes its interrogation instruction
  so the `inherit` route no longer contradicts the route table.
- The shipped eval case that states the top rung's precondition in prose is
  restated against the field, and five cases are added.
- Both packs' `pack.toml`, `.claude-plugin/plugin.json`, and the generated
  `.claude-plugin/marketplace.json` carry matching bumps, with a changelog
  release entry per pack.
- The `frontend-visual-authority` spec records that this change supersedes part
  of the criterion that fixes its top rung's `requires` value.

## Durable Outputs

| Semantic role | Destination | Owner | Evidence | Closeout condition |
| --- | --- | --- | --- | --- |
| Decision rationale | `docs/adr/0131-visual-target-confirmation-is-an-explicit-state.md` | eugenelim | The ADR states the decision and its alternatives | ADR is Accepted and cited by this spec |
| Interface compatibility | `packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md` | eugenelim | The template carries the field and its closed set | Contract test asserts the field and values |
| Current product truth | `guides/frontend-engineering/how-to/read-the-design-handoff.md` | eugenelim | The guide states the field and the absent-field reading | Roster test asserts the guide surface |
| Interface compatibility | `docs/specs/frontend-visual-authority/spec.md` | eugenelim | Its `Status` field carries the supersession annotation | AC-0027 holds |
| Release history | `pack.toml`, `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` for both packs, and `docs/product/changelog.md` | eugenelim | Matching versions and one release entry per pack | AC-0022, AC-0023 and AC-0030 hold |

Retention class: repository-durable. Every destination above is a tracked file
in this repository, readable by any reviewer, worktree, or CI job.

## Agent Rules

### Always do

- Treat an absent `visual_target` field as `unconfirmed`, never as `confirmed`.
- Use the exact field name `visual_target` and the exact values `none`,
  `unconfirmed`, and `confirmed` on every surface that names the state.
- Keep the confirmation's binding to composition, proportion, and spatial
  relationships.

### Ask first

- Before raising the `frontend-engineering` `SKILL.md` body-line budget above
  968, the ceiling AC-0013 of the Shipped `design-to-build-value-handoff` spec
  sets and `test_visual_authority_entrypoint.py` pins. Additions to that file
  under this spec are in-place edits paid for within the ceiling.
- Before changing the `status` field's own vocabulary or meaning, which this
  spec does not touch.
- Before adding a `visual_target` value beyond the three named here.

### Never do

- Never add a new module boundary, top-level directory, or dependency: no
  image-analysis, browser, or design-tool dependency enters either pack.
- Never write a sidecar file beside the direction artifact to carry this state.
- Never let the confirmation supply a colour, typography, spacing, radius, depth,
  or motion value.
- Never treat `status: selected` as evidence that a visual target was confirmed.
- Never record a person's name, handle, or contact detail in the confirmation
  record.

## Testing Strategy

- **TDD — the artifact schema carries the state (AC-0001, AC-0002, AC-0004,
  AC-0024, AC-0025, AC-0026).** The template and `converge.md` are shipped files
  whose bytes parse, so an assertion reds on a missing, misnamed, or ungated
  field. Asserted from the experience-design pack's own suite.
- **TDD — the frontend rung tables name the field (AC-0006, AC-0007, AC-0008,
  AC-0009, AC-0010).** These five read `references/visual-observation.md`, which
  is what the shipped `observation_table` and `rule` helpers open, so a drifted
  cell reds against the parsed table rather than a transcription of it.
- **TDD — the other two frontend surfaces name the field (AC-0012, AC-0013).**
  The rung bullet and the evidence-manifest row live in the frontend
  `SKILL.md`, which those helpers never open, so these are assertions over that
  file's own text.
- **TDD — the design-system table names the field (AC-0011).** Asserted from the
  experience-design pack's `test_design_system_contract.py`, because the
  pack-test boundary forbids a frontend suite from reading that tree.
- **TDD — the route no longer contradicts its operation (AC-0014).** The
  scoping is a literal in one sentence of one shipped file.
- **TDD — the reader-facing guide states the rule (AC-0015).** Asserted from
  `tests/roster/`, because a pack suite may not read the guide tree.
- **TDD — the field name cannot drift between the two packs (AC-0017).**
  Asserted from `tests/roster/`, the only place allowed to read both trees, so
  renaming the key on one side reds instead of leaving both suites green.
- **TDD — the superseded criterion is annotated (AC-0027).** An assertion over
  the frozen spec's `Status` field text.
- **TDD — the superseded reading is replaced on every surface that carries it
  (AC-0031, AC-0032, AC-0033, AC-0034).** Every other criterion is a presence
  check, and a tree carrying both the new field rule and the old "records a
  human confirming the composition" reading satisfies all of them. These four
  work over a closed, enumerated set of surfaces rather than a guessed phrase
  list: two state the rung-1 and rung-2 conditions against the field, one
  forbids the retired readings the plan's recorded sweep found, and one scopes
  the producing instruction that records a binding claim.
- **Visual / manual QA — the model-behaviour decisions (AC-0018, AC-0019,
  AC-0020, AC-0021, AC-0028, AC-0029).** Scenario routing is model behaviour, so
  the recorded gesture is an eval case and the observable result is the rung or
  state it names.
- **Goal-based check — the release surface stays consistent (AC-0022, AC-0023,
  AC-0030).** `tests/conformance/test_pack_metadata.py` plus a version
  comparison against `origin/main`, which is what makes a missing bump
  observable rather than merely self-consistent.

## Acceptance Criteria

- [ ] **AC-0001.** `creative-direction-template.md`'s frontmatter carries a
  `visual_target` key whose placeholder enumerates exactly `none`,
  `unconfirmed`, and `confirmed`.
- [ ] **AC-0002.** `creative-direction-template.md`'s `## Approved visual target`
  section carries a `**Confirmation record:**` line.
- [ ] **AC-0004.** `references/converge.md` contains the literal `visual_target:
  confirmed` in the instruction that writes the disposition, and the literal
  `visual_target: unconfirmed` in the instruction covering a target present
  without a recorded human confirmation.
- [ ] **AC-0006.** In `visual-observation.md`'s `## Authority precedence` table,
  the `approved-visual-target` row's `requires` cell reads `visual_target:
  confirmed`.
- [ ] **AC-0007.** `visual-observation.md` carries a `## Visual-target
  confirmation` rule table whose row keys, in order, are `field`, `states`,
  `absent-field`, `binds`, and `never-binds`.
- [ ] **AC-0008.** That table's `absent-field` row states that an artifact
  without the field reads as `unconfirmed`.
- [ ] **AC-0009.** That table's `states` row enumerates exactly `none`,
  `unconfirmed`, and `confirmed`.
- [ ] **AC-0010.** That table's `never-binds` row names colour, typography,
  spacing, radius, depth, and motion.
- [ ] **AC-0011.** In `design-system`'s `## Design authority` table, the
  `approved-visual-target` row's source cell names `visual_target: confirmed`.
- [ ] **AC-0012.** `frontend-engineering`'s `SKILL.md` names `visual_target:
  confirmed` where it describes the `approved-visual-target` rung.
- [ ] **AC-0013.** `frontend-engineering`'s evidence-manifest entry for visual
  authority records the artifact's `visual_target` reading.
- [ ] **AC-0014.** In `creative-direction`'s `SKILL.md`, the sentence containing
  the literal `Run the interrogation` also contains the literal `inherit` and
  excludes that route from the instruction.
- [ ] **AC-0015.** `guides/frontend-engineering/how-to/read-the-design-handoff.md`
  states the field, its three values, and the absent-field reading.
- [ ] **AC-0017.** A `tests/roster/` assertion makes two comparisons: the set of
  `visual_target` values declared in `creative-direction-template.md`'s
  frontmatter equals the set enumerated in `visual-observation.md`'s `states`
  row exactly; and every value captured by a whitespace-normalized match of
  `visual_target:` followed by a value, anywhere in `visual-observation.md`,
  `design-system`'s `SKILL.md`, `converge.md` or `visualize.md`, is a member of
  that declared set. Renaming a value on any one surface reds it.
- [ ] **AC-0018.** `creative-direction`'s evals carry a case whose expected output
  records `visual_target: none` for a direction with no visual target.
- [ ] **AC-0019.** `frontend-engineering`'s shipped `visual-authority-direction-only`
  eval case states its precondition as the artifact's explicit
  `visual_target: unconfirmed` reading rather than as prose about what the
  artifact records, and its expected output still resolves to
  `direction-and-taxonomy`.
- [ ] **AC-0020.** `frontend-engineering`'s evals carry a case whose prompt states
  that the artifact carries no `visual_target` key and whose expected output
  resolves to `direction-and-taxonomy`.
- [ ] **AC-0021.** `creative-direction`'s evals carry a case whose expected output
  runs no interrogation on the `inherit` route.
- [ ] **AC-0022.** `packs/experience-design/pack.toml`, its
  `.claude-plugin/plugin.json`, and its entry in `.claude-plugin/marketplace.json`
  carry the same version, and that version is strictly greater than the one on
  `origin/main`.
- [ ] **AC-0023.** `packs/frontend-engineering/pack.toml`, its
  `.claude-plugin/plugin.json`, and its entry in `.claude-plugin/marketplace.json`
  carry the same version, and that version is strictly greater than the one on
  `origin/main`.
- [ ] **AC-0024.** `creative-direction-template.md`'s compositional-commitments
  comment gates that section on `visual_target: confirmed`.
- [ ] **AC-0025.** `references/converge.md` instructs writing compositional
  commitments only where `visual_target` reads `confirmed`.
- [ ] **AC-0026.** `creative-direction-template.md`'s `## Approved visual target`
  comment contains the literal `visual_target`, names the section's `**Target:**`,
  `**Binding:**` and `**Confirmation record:**` lines, and contains the literal
  `bind nothing on their own`.
- [ ] **AC-0027.** `docs/specs/frontend-visual-authority/spec.md`'s `Status`
  field names all three superseded parts — ADR-0130's body budget, and ADR-0131's
  of both the `requires` value `recorded-human-confirmation` and the Always-do
  rule that a rung condition is a property the pack defines rather than an
  upstream template's value — and contains no whitespace-normalized match for
  the literal `everything else stands`.
- [ ] **AC-0028.** `frontend-engineering`'s shipped `visual-authority-approved-target`
  eval case states its precondition as the artifact's `visual_target: confirmed`
  reading rather than as prose about a human-confirmed composition.
- [ ] **AC-0029.** `creative-direction`'s evals carry a case whose expected output
  records `visual_target: unconfirmed` for a selected direction with a named
  target that no human confirmed.
- [ ] **AC-0030.** `docs/product/changelog.md` carries a free-standing `##`
  release entry for each pack's new version, each with a `### Highlights`
  subsection beneath it. Both entries owe one: the change alters what a consumer
  of either pack can do, because an adopter must now write a field that did not
  exist and an artifact that omits it loses a binding it previously had.
- [ ] **AC-0031.** Each surface in the confirmation-reading set states the top
  rung's precondition as the literal `visual_target: confirmed`. The set is
  closed and enumerated here: the rung-1 bullet and the evidence-manifest
  row in `frontend-engineering`'s `SKILL.md`; `visual-observation.md`'s
  `## Why the top rung needs a recorded confirmation` section; the
  `visual-authority-approved-target` and `visual-authority-direction-only` eval
  cases; `packs/frontend-engineering/.apm/agents/frontend-reviewer.md`; and the
  rung-1 clause of `guides/frontend-engineering/how-to/read-the-design-handoff.md`.
- [ ] **AC-0032.** Each surface in that set that states rung 2's condition states
  it as a `visual_target` reading other than `confirmed`, rather than as the
  absence of a recorded confirmation.
- [ ] **AC-0034.** `references/visualize.md`'s instruction to record a target's
  binding boundaries is scoped to the confirmed reading, so an unconfirmed
  target records its identity and disposition without a `**Binding:**` claim.
- [ ] **AC-0033.** No surface in that set contains a whitespace-normalized match
  for any member of the retired-reading set, which the plan enumerates from a
  recorded sweep of both trees rather than from a guessed phrase list.

## Retired identifiers

- `AC-0003`
- `AC-0005`
- `AC-0016`

## Follow-ons

none

## Assumptions

none
