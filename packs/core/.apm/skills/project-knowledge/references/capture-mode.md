# Capture Mode

Validate one captured-observation producer request and hand it to `capture_observation`.

This mode reads one strict JSON request from standard input, writes only the derived captured-observation journal partition, and returns the capture receipt. It cannot read topics, query observation journals, or choose storage paths.

## Work-loop producer profile

The `work-loop` producer profile serves enquiries only. `--capture` and
`--distill` with `--producer-profile work-loop` are refused with exit 2 and
`reason_code` `strict_parse`, and write nothing; submit a capture through the raw full-request path.

## Capturing from a delivery candidate

A candidate printed by `--candidates` is a suggestion, not a request. Write the
`lesson` and give the `privacy_attestation` yourself, cite repository-relative
provenance, and submit the request through this mode like any other. Capture
never reads the candidate frame, and its validation, identity rule, and time
window do not change.
