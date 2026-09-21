# Measurement spike — 2026-09-21

## Question

Does applying every packet-decidable acceptance criterion to the 148 intents in
`docs/product/intents/` refuse any value the corpus legitimately carries, or
does it identify only migration work? The measurement read only the preamble
block: the run of `- **Field:**` lines before the first `## ` heading.

## Results

| Criterion | Refusals | Nature |
| --- | ---: | --- |
| AC-0001 missing `Owner:` | 143 | absent field |
| AC-0001 missing `Slug:` | 122 | absent field |
| AC-0001 missing `Level:` | 10 | absent field |
| AC-0001 missing `Status:` | 2 | absent field |
| AC-0009 retired name `Authority` | 54 occurrences across 45 files | needs rename to `Governed by:` |
| AC-0025 repeated preamble field | 8 files, every one `Authority` x2 or x3 | see below |
| AC-0009 `Type` / `Raised` / `Stage` / `Parent` / `Source` | 1 each | single-file drift |
| AC-0002 `Status` value | **0** | no legitimate value refused |
| AC-0022 `Kind` / `Scale` / `Maturity` values | **0** | no legitimate value refused |
| AC-0031 `Governed by:` form, applied to the 54 `Authority` values | **0** | no legitimate value refused |
| AC-0032 `Parent intent:` form, applied to all 31 values | **0** | no legitimate value refused |
| AC-0005 / AC-0006 progress fields | **0** | no intent carries one yet |

1. **No criterion refuses a value the corpus legitimately carries.** Every
   refusal is an absent field or a retired field name: migration work, not a
   contract defect.
2. **AC-0002 refused zero `Status` values even though two intents carry a
   `- **Status:** Run 2026-09-09; killed on …` line.** Those lines sit below the
   first `## ` heading, inside a de-risk record, so AC-0011's preamble-bounding
   rule excluded them. The measurement demonstrates the rule.

## Earlier measurements

These measurements predate the 2026-09-21 spike and were not re-run:

- The two writers diverge: core's `intake-intent` and product-engineering's
  `frame-intent` share exactly one preamble field, `Level:`.
- `Authority` has three distinct usages: a bolded preamble governance pointer;
  a bolded `## Source` owner attribution; and an unbolded `## Source`
  provenance token whose values are `repo-origin` (27) and
  `transferred-to-repository` (4).
