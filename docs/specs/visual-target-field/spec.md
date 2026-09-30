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
binding claim and its compositional commitments only where the field reads
`confirmed`. No consumer reads the field yet, so no rung moves and no existing
behaviour changes.

## What Changes

- The direction template gains the `visual_target` frontmatter key and a
  `**Confirmation record:**` line, and its `## Approved visual target` comment
  names the frontmatter key as the canonical disposition.
- `converge` writes the disposition, and gates compositional commitments on the
  confirmed reading.
- `visualize` and `creative-direction`'s own output contract scope their
  binding-boundaries instruction to the confirmed reading.
- The byte-pinned template excerpt inside `establish-design-intent.md` is
  re-derived so the guidebook lint stays green.

## Durable Outputs

| Semantic role | Destination | Owner | Evidence | Closeout condition |
| --- | --- | --- | --- | --- |
| Interface compatibility | `packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md` | eugenelim | The template carries the field and its closed set | AC-0001 to AC-0003 hold |
| Current product truth | `guides/experience-design/how-to/establish-design-intent.md` | eugenelim | Its excerpt matches the template verbatim | AC-0008 holds |
| Release history | `packs/experience-design/pack.toml`, its `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md` | eugenelim | Matching versions and one release entry | AC-0009 and AC-0010 hold |

Retention class: repository-durable.

## Agent Rules

### Always do

- Use the exact field name `visual_target` and the exact values `none`,
  `unconfirmed` and `confirmed`.
- Re-derive the guide's template excerpt in the same change as any template
  edit.

### Ask first

- Before changing the `status` field's vocabulary or meaning.
- Before adding a `visual_target` value beyond the three named here.

### Never do

- Never make any consumer read the field in this slice; that is the successor's
  contract, and shipping both at once is what four review rounds rejected.
- Never write a sidecar file beside the direction artifact.
- Never add a dependency, module boundary, or top-level directory.
- Never record a person's name, handle, or contact detail in the confirmation
  record.

## Testing Strategy

- **TDD — the template carries the state and its provenance (AC-0001, AC-0002,
  AC-0003).** The template's bytes parse; asserted from
  `packs/experience-design/tests/skills/creative-direction/test_contract.py`.
- **TDD — the producing surfaces gate on the confirmed reading (AC-0004,
  AC-0005, AC-0006, AC-0007).** Each is a literal in a shipped
  `creative-direction` file, asserted from the same suite.
- **Goal-based check — the pinned excerpt still matches (AC-0008).**
  `python3 tools/lint-guidebook-steps.py guides/experience-design` is the
  one-liner.
- **Goal-based check — the release surface stays consistent (AC-0009,
  AC-0010).** `tests/conformance/test_pack_metadata.py` plus a version
  comparison against `origin/main`.

## Acceptance Criteria

- [ ] **AC-0001.** `creative-direction-template.md`'s frontmatter carries a
  `visual_target` key whose placeholder enumerates exactly `none`,
  `unconfirmed` and `confirmed`.
- [ ] **AC-0002.** That template's `## Approved visual target` section carries a
  `**Confirmation record:**` line.
- [ ] **AC-0003.** That section's comment contains the literal `visual_target`,
  names the `**Target:**`, `**Binding:**` and `**Confirmation record:**` lines,
  and contains the literal `bind nothing on their own`.
- [ ] **AC-0004.** `references/converge.md` contains the literal `visual_target:
  confirmed` in the instruction that writes the disposition, and the literal
  `visual_target: unconfirmed` in the instruction covering a target present
  without a recorded human confirmation.
- [ ] **AC-0005.** `references/converge.md`'s compositional-commitments
  instruction is gated on the `confirmed` reading.
- [ ] **AC-0006.** `references/visualize.md`'s instruction to record a target's
  binding boundaries is gated on the `confirmed` reading.
- [ ] **AC-0007.** `creative-direction`'s `SKILL.md` output-contract entry for
  the approved visual target is gated on the `confirmed` reading.
- [ ] **AC-0008.** `python3 tools/lint-guidebook-steps.py guides/experience-design`
  exits zero.
- [ ] **AC-0009.** `packs/experience-design/pack.toml`, its
  `.claude-plugin/plugin.json`, and its entry in `.claude-plugin/marketplace.json`
  carry the same version, strictly greater than the one on `origin/main`.
- [ ] **AC-0010.** `docs/product/changelog.md` carries a free-standing `##`
  release entry for that version with a `### Highlights` subsection.

## Follow-ons

- eugenelim: [`visual-target-rung-precondition`](../visual-target-rung-precondition/spec.md)
  — makes the `approved-visual-target` rung require the field and removes the
  superseded prose reading from every carrier.

## Assumptions

none
