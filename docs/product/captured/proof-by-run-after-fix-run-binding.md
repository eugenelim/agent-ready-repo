# Proof-by-run after-fix run binding

- **Status:** Open
- **Kind:** design
- **Detail:** docs/specs/proof-by-run-evidence/spec.md
- **Depends on:** spec:proof-by-run-evidence

## Summary

Decide how a full-mode run records the after-fix run of a command-carrying finding, so a `fixed-by` disposition shows the command passing at the replacement subject. The before-fix run already ships as a `proof-by-run.v1` finding-assessment.

## Why the current contracts cannot hold it

- `finding-assessment.v1` binds one record to one `review_subject_fingerprint`. The supervisor writes it at the reviewed subject, before the fix. The store refuses an assessment whose source report is no longer current, so no replacement can carry the after-fix run.
- `finding-disposition.v1` closes the finding with `fixed-by`, but has no evidence field.
- `evidence-receipt.v1` admits only `observation.type`, so it cannot name the finding, the command, or the output digests. An `assess-finding` result also may assert only an assessment.

## Proposed amendment

For the owner of the acceptance-centered work-loop brief and the `structured-review-boundary` contracts:

- Add an optional `evidence_refs` array to `finding-disposition.v1`.
- Have the supervisor require one `proof-run:v1:<commit>:pass:<sha256>` reference, bound to the replacement subject's commit, before it writes `fixed-by` for a finding whose assessment carries `proof-by-run.v1`.
- Readers ship before writers.

## Next step

The contract owner accepts, revises, or declines the amendment. Until then, the FIX step keeps the after-fix run as prose.
