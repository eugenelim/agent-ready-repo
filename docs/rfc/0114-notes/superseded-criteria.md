# Shipped criteria that RFC-0114 touches

Input for the ADR and the spec that follow RFC-0114. Found by reading the repository on 2026-11-06 and by two adversarial reviews. The ADR must confirm each row against the current text, since the specs are frozen and a later edit to a test can move a number.

## Superseded by the ADR

| Spec or test | Criterion | What changes |
| --- | --- | --- |
| `new-rfc-two-humans` | AC2 | The template no longer has a `## Reviewer brief`. |
| `new-rfc-two-humans` | AC3 | The decisions are no longer a table in "The ask". |
| `new-rfc-two-humans` | AC6, the clause that the completeness checklist's YES/NO items "survive verbatim" | "Approver named" becomes "who decides is clear". |
| `new-rfc-two-humans` | AC7 | The how-to guide stops describing the Reviewer brief and the decisions table. |
| `new-rfc-two-humans` | AC9, the eval assertions about the old template (not its Decision-weight assertion, which is kept below) | The first eval is rewritten for the new template. |
| `new-rfc-readability` | AC3, only the clause "fuller explanation living in 'The ask'". The short-title cue in `assets/rfc.md` stays. | There is no "The ask". |
| `new-rfc-governance` | AC-0065 and the test that pins it (`test_governance_section_pins_ac_0065`): "Put `GOVERNANCE.md` next to the charter when one exists, and at the repository root otherwise." | An existing governance file at an allowed location is the target. |
| `new-rfc-governance` | The "governance draft" term (three owned-path names) | Governance mode's default text and the seeded starter become one text, so the draft check is relaxed. |

## Already superseded elsewhere

- `new-rfc-two-humans` AC5 (the heavy tier's Approver sign-off) and AC6's rule that no tier drops a check: superseded by ADR-0089. RFC-0054 D1's tier text is likewise replaced by ADR-0089.

## Kept, so the new template and guide must still satisfy them

| Spec | Criterion | Requirement |
| --- | --- | --- |
| `rfc-correction-convention` | the fourth criterion (its criteria are unnumbered) | The template carries the commented Errata/Amendments scaffold. |
| `new-rfc-fresh-context` | AC1 | The template carries the cold-reader cue comment. |
| `new-rfc-readability` | AC6 | The guide's Step 4 keeps its "readiness summary" and "proof" wording. |
| `new-rfc-fresh-context` | AC6 | The guide still describes the fresh-context check. |
| `new-rfc-fresh-context` | AC7(a) | The first eval keeps its assertion that the RFC "reads from zero prior context". |
| `new-rfc-two-humans` | AC1 and the Decision-weight assertion that AC9 added to the first eval | The optional `Decision weight` line and its cue (default `standard`) stay, and the rewritten eval still asserts the field. |
| `new-rfc-governance` | AC-0044 | Every copy of `file_safety.py` stays byte-identical to the blessed helper. A seeded copy beside `rfc.py` counts. |

## Skill text and tooling to check

- The `new-rfc` skill's "Recording corrections" section says whole-RFC supersession is recorded as an Errata entry naming the superseding RFC. RFC-0114 adds the graph's header lines as the primary record, so the spec must align that sentence and any test that pins it.
- The decision graph (`navigate-decisions`) reads `Supersedes`, `Supersedes in part`, `Superseded by` and `Superseded in part` on RFCs as well as ADRs. A lineage edge is checked only when both records carry matching lines with equal scopes. A one-sided declaration is shown as declared, and the graph does not traverse it.

- Numbering. The skill's RFC numbering moves from `next-ordinal.py` to `rfc.py next`. Any shipped criterion or test that pins `next-ordinal.py` for RFCs needs the same check, including `new-rfc-governance` AC-0044 if it lists the script copies.

## Not contradicted

- `open-rfc-format-retrofit` records a one-time retrofit of five RFCs that stay untouched.
