# Spec: visual-target field

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0131](../../adr/0131-visual-target-confirmation-is-an-explicit-state.md)
- **Brief:** none
- **Discovery:** [`visual-target-confirmation/notes/carrier-inventory.md`](../visual-target-confirmation/notes/carrier-inventory.md)
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`,
> `What Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working
> material.

## Outcome

A direction artifact records its visual target's disposition in one closed
frontmatter field, `visual_target`, whose values are `none`, `unconfirmed` and
`confirmed`. `creative-direction` writes that field, and writes a target's
binding claim and its compositional commitments only where a human has
confirmed the target. No consumer reads the field yet, so no rung moves and no
existing behaviour changes.

## What Changes

- The direction template gains the `visual_target` frontmatter key and a
  `**Confirmation record:**` line, and its `## Approved visual target` comment
  names the frontmatter key as the canonical disposition and states the
  absent-field reading.
- `converge` writes the disposition, and writes compositional commitments only
  for a confirmed target.
- `visualize` and `creative-direction`'s own output contract scope their
  binding-boundaries instruction to a target a human has confirmed.
- The `creative-direction` eval harness covers the new field.
- The byte-pinned template excerpt inside `establish-design-intent.md` is
  re-derived so the guidebook lint stays green.

## Durable Outputs

| Semantic role | Destination | Owner | Evidence | Closeout condition |
| --- | --- | --- | --- | --- |
| Interface compatibility | `packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md` | eugenelim | The template carries the field and its closed set | AC-0001 to AC-0003 and AC-0011 hold |
| Current product truth | `guides/experience-design/how-to/establish-design-intent.md` | eugenelim | Its excerpt matches the template verbatim and carries the new material | AC-0008 and AC-0012 hold |
| Behavioural coverage | `packs/experience-design/.apm/skills/creative-direction/evals/` | eugenelim | The harness exercises the new field | AC-0013 holds |
| Release history | `packs/experience-design/pack.toml`, its `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md` | eugenelim | Matching versions above this slice's own baseline, and one release entry this slice authored | AC-0009 and AC-0010 hold |

Retention class: repository-durable.

## Agent Rules

### Always do

- Use the exact field name `visual_target` and the exact values `none`,
  `unconfirmed` and `confirmed`.
- Treat an absent `visual_target` as `unconfirmed`. That is the fail-closed
  default ADR-0131 fixes.
- Re-derive the guide's template excerpt in the same change as any template
  edit.

### Ask first

- Before changing the `status` field's vocabulary or meaning.
- Before adding a `visual_target` value beyond the three named here.

### Never do

- Never make any consumer read the field in this slice; that is the successor's
  contract, and shipping both at once is what four review rounds rejected. An
  instruction that tells a producer when to *write* the field is not a consumer
  read.
- Never write a sidecar file beside the direction artifact.
- Never add a dependency, module boundary, or top-level directory.
- Never record a person's name, handle, or contact detail in the confirmation
  record.

## Testing Strategy

- **TDD — the template carries the state and its provenance (AC-0001, AC-0002,
  AC-0003, AC-0011).** The template's bytes parse; asserted from
  `packs/experience-design/tests/skills/creative-direction/test_contract.py`.
- **TDD — the producing surfaces are scoped to a confirmed target (AC-0004,
  AC-0005, AC-0006, AC-0007).** Each asserts an exact literal inside a bounded
  unit — one sentence, or one list item — of a shipped `creative-direction`
  file, from the same suite. Asserting the literal inside the bounded unit, not
  anywhere in the file, is what makes removing the scope red rather than pass
  on some other occurrence of the same word.
- **TDD — the eval harness covers the field (AC-0013).** Asserted from the same
  suite over the harness JSON.
- **Goal-based check — the pinned excerpt still matches and carries the new
  material (AC-0008, AC-0012).**
  `python3 tools/lint-guidebook-steps.py guides/experience-design` is the
  one-liner for AC-0008; AC-0012 is a contract-suite assertion over the guide's
  bytes, because the lint cannot see whether the excerpt gained the new lines.
- **Goal-based check — the release surface stays consistent (AC-0009,
  AC-0010).** `tests/conformance/test_pack_metadata.py` covers intra-tree
  agreement. The baseline comparison is a **recorded manual check**: run
  `git show $(git merge-base HEAD origin/main):packs/experience-design/pack.toml | grep '^version'`
  and `git show HEAD:packs/experience-design/pack.toml | grep '^version'` at the
  start of the work, and record both observed values in the plan's Changelog.
  The slice-start baseline is `4.1.1`, not the version on `origin/main`.

## Acceptance Criteria

- [ ] **AC-0001.** `creative-direction-template.md`'s frontmatter carries a
  `visual_target` key whose placeholder enumerates exactly `none`,
  `unconfirmed` and `confirmed`.
- [ ] **AC-0002.** That template's `## Approved visual target` section carries a
  `**Confirmation record:**` line whose placeholder names the confirmation's
  date and where it was recorded, and contains none of the literals `who`,
  `name`, `handle`, `email` — so the placeholder cannot invite the content the
  `Never do` rail forbids.
- [ ] **AC-0003.** That section's comment contains the literal `visual_target`,
  names the `**Target:**`, `**Binding:**` and `**Confirmation record:**` lines,
  and contains the literal `bind nothing on their own`.
- [ ] **AC-0004.** `references/converge.md` contains the literal `visual_target:
  confirmed` in the instruction that writes the disposition, and the literal
  `visual_target: unconfirmed` in the instruction covering a target present
  without a recorded human confirmation.
- [ ] **AC-0005.** In `references/converge.md`, the single sentence containing
  the literal `compositional commitments into the doc` also contains the literal
  `visual_target: confirmed`.
- [ ] **AC-0006.** In `references/visualize.md`, the single sentence containing
  the literal `record its identity and three boundaries` also contains the
  literal `the human has confirmed`. The condition is the confirmation
  determination that operation already holds — `visualize` runs before
  `converge` writes the field, so it has no field to read.
- [ ] **AC-0007.** In `creative-direction`'s `SKILL.md`, the single list item
  beginning `- **Approved visual target**` contains the literal `the human has
  confirmed`.
- [ ] **AC-0008.** `python3 tools/lint-guidebook-steps.py guides/experience-design`
  exits zero.
- [ ] **AC-0009.** `packs/experience-design/pack.toml`, its
  `.claude-plugin/plugin.json`, and its entry in `.claude-plugin/marketplace.json`
  carry the same version, strictly greater than `4.1.1` — the version this
  branch already carried before this slice began, which a sibling slice
  released. Comparing against `origin/main` would pass on that sibling's bump
  and let this slice ship no bump at all.
- [ ] **AC-0010.** `docs/product/changelog.md` carries a free-standing `##`
  release entry for that version, with a `### Highlights` subsection, whose
  body names the `visual_target` field. The existing `4.1.1` entry does not
  satisfy this: its Highlights describe the `frame`/`inherit` scoping fix.
- [ ] **AC-0011.** That section's comment states that an absent `visual_target`
  reads `unconfirmed`.
- [ ] **AC-0012.** `guides/experience-design/how-to/establish-design-intent.md`
  contains both the `visual_target` frontmatter key and the
  `**Confirmation record:**` line, so the re-derived excerpt demonstrably
  carries the new material rather than merely remaining a valid verbatim run.
- [ ] **AC-0013.** `packs/experience-design/.apm/skills/creative-direction/evals/`
  exercises the new field: at least one case asserts the `visual_target`
  disposition a run is expected to write.

## Follow-ons

- eugenelim: `visual-target-rung-precondition` — not yet authored — makes the
  `approved-visual-target` rung require the field and removes the superseded
  prose reading from every carrier.

## Assumptions

none
