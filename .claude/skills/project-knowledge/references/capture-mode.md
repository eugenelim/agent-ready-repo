# Capture Mode

Validate one captured-observation producer request and hand it to `capture_observation`.

This mode reads one strict JSON request from standard input, writes only the derived captured-observation journal partition, and returns the capture receipt. It cannot read topics, query observation journals, or choose storage paths.

## Work-loop producer profile

Use `project-knowledge --capture --producer-profile work-loop --semantic-gate
<spec-approved|plan-locked> --artifact docs/specs/<slug>/<spec.md|plan.md>`.
Standard input supplies only `lesson`, `kind`, `project_scope`,
`competency_facets`, `destination_hint`, `provenance`, and
`privacy_attestation` (plus optional `friction` and `verification_route`). The
profile rejects supplied deterministic fields and derives the contract version,
work-loop producer/version, gate/artifact, observation time, and artifact-byte
freshness anchor before the ordinary strict validation path runs.

At `plan-locked`, terminal distillation uses `--distill --pending` with the
same producer profile and gate. Its input is only the full capture receipts
returned by captures at that gate; it refuses other-gate receipts, guessed
identifiers, and `direct-maintainer-pending`.
