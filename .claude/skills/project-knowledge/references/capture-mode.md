# Capture Mode

Validate one captured-observation producer request and hand it to `capture_observation`.

This mode reads one strict JSON request from standard input, writes only the derived captured-observation journal partition, and returns the capture receipt. It cannot read topics, query observation journals, or choose storage paths.

## Recovering a capture timeout

Only when the capture diagnostic has both `reason_code=deadline_exceeded` and
`retryable=true`, announce user-visible recovery: “Capture timed out; I will
make one retry with the same request.” Resubmit the same request once through
the public capture path. Preserve its exact bytes, including all identity-bearing
fields, provenance, timestamps, and privacy attestation; do not regenerate them.

If the retry returns a capture receipt, report that receipt, including a replay
receipt when the first attempt already stored the observation. If the retry
fails, stop and report: “Capture recovery failed; the observation is not
confirmed retained.” Do not claim a successful write or create a fallback store.
Do not retry a non-retryable refusal, a lock diagnostic, or any other reason
code. Existing admission checks still apply. This is one visible caller retry;
the CLI keeps zero internal automatic retries.

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
