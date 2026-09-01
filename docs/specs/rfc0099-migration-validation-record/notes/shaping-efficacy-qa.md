# Manual QA: seeded shaping-review detection efficacy

Run on 2026-08-31 using the method recorded in
`docs/specs/shaping-review-contracts/notes/qa.md`: each mode received a fresh,
isolated reviewer context and an unchanged seeded artifact. The prior QA run's
unseeded targets and finding totals were not reused as evidence.

Expected-result keys were kept outside the reviewed fixture bodies. Every raw
reviewer report was persisted under the work-loop's ignored `.context/` review
directory and passed through an independent `finding-adjudicator` before
classification. The maintained
[`shaping-evidence.md`](shaping-evidence.md) is a non-authoritative data-only
extract of the six adjudicated identifications; it does not commit the
model-authored report pairs. The check is defect identification, not an exact
raw or sustained finding total.

## Canonical efficacy runs

| Mode | Target and reviewed SHA-256 | Expected-result keys | Adjudicated identification | Evidence pair |
| --- | --- | --- | --- | --- |
| `intent` | `fixtures/intent-fast-status.md` — `f7d35ac168bf0cdd5932f82f3ad2afc32e56da840bb134491fe3f06d9edd97df` | `SHAPE-UNNECESSARY-INTENT`; `SHAPE-UNSAFE-SIMPLIFICATION` | Both sustained: the reviewer rejected the needless intent/wrapper skill and the deferred confinement/reconciliation controls. | `shaping-evidence.md` rows for `intent` |
| `delivery-brief` | `fixtures/delivery-brief-flag-rename.md` — `c196a0208c4da2d3ae63bf66ab5fe5bde5d5bd6d39f57c9816b3f94344846bd1` | `SHAPE-WRAPPER-BRIEF`; `SHAPE-SPECULATIVE-SLICES` | Both sustained: the reviewer rejected a one-team, one-slice wrapper brief and the three unsupported future slices. | `shaping-evidence.md` rows for `delivery-brief` |
| `spec` | `fixtures/spec-improve-intake.md` — `23c44e9d6298c44611e22b0446f76e5eeae2ae3424210ab439cb233ca8c9af85` | `SHAPE-VAGUE-SPEC-OBJECTIVE`; `SHAPE-MISSING-BOUNDARIES` | Both sustained: the reviewer rejected the subjective objective and the decision to defer scope and mutable-surface boundaries until coding. | `shaping-evidence.md` rows for `spec` |

## Additional report adjudication

Earlier bounded attempts are retained because every reviewer report requires
adjudication before its findings can be classified:

- report `13` sustained the wrapper-brief finding and refuted a migration-detail
  finding that belonged at spec altitude;
- report `14` was refuted because the target existed and was readable, so its
  missing-evidence finding could not support classification; and
- report `15` sustained speculative-slice, premature-materialization, deferred-
  scope, and readiness findings and refuted an out-of-rubric source-traceability
  finding.

These attempts do not replace the canonical three runs above. They demonstrate
the adjudication gateway, not extra expected defects or deterministic counts.

## Scope boundary

The runs prove that the shipped rubric can identify the six seeded defects in
fresh contexts. They do not establish adopter comprehension, a fixed model
finding count, or that an arbitrary future artifact will receive identical
wording or severity.
