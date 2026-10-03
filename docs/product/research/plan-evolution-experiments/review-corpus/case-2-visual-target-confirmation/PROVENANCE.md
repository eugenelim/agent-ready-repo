# Review artifact provenance

Persistence is unconditional under the finding-adjudication gateway. Five of the
eight reports were not persisted at completion. All five were recovered from
their subagent transcripts on 2026-09-30 and are now on disk. This note records
the gap and the recovery rather than hiding either.

| Report | On disk | How captured | Adjudicated |
| --- | --- | --- | --- |
| adversarial round 1 | yes | at completion | yes — 10 sustained / 4 refuted / 0 indeterminate |
| shaping round 1 | yes | at completion | n/a — lifecycle-owner gate |
| adversarial round 2 | yes | at completion | yes — 8 sustained / 2 refuted / 0 indeterminate |
| shaping round 2 | yes | recovered from transcript | n/a |
| adversarial round 3 | yes | recovered from transcript | **no** |
| shaping round 3 | yes | recovered from transcript | n/a |
| adversarial round 4 | yes | recovered from transcript | **no** |
| shaping round 4 | yes | recovered from transcript | n/a |

## What "recovered from transcript" means

The five recovered files hold the subagent's own final report bytes, extracted
programmatically from the session transcript — the last assistant text block for
rounds 2 and 3, and the `SubagentHandback` message payload for round 4, which is
where that round's reports were returned. They are not a controller
transcription and were not reconstructed from conversation memory.

The transcripts remain the upstream source. They live outside the repository
under the session's task output directory and are not reproduced here.

## Two departures from the normal path

1. `review raw-classify` was run once against a shaping report and refused it
   `sentinel-absent`. That instrument owns adversarial-reviewer grammar; the
   shaping gate is resolved by the lifecycle owner. The refusal says nothing
   about that report.
2. **Rounds 3 and 4 were never adjudicated.** Round 3 reached the
   surface-to-human threshold in `new-spec` and its findings were resolved by
   direct controller verification against the cited files; round 4 produced the
   decomposition decision and its findings were never repaired. Direct
   verification is a weaker evidence chain than adjudication. Do not present
   either round's findings as adjudicated.

## Stopped-revision bytes

Case 2's stopped revision is the exact revision both round-4 reviewers graded.
Of its three artifacts, `plan.md` (`4bffb807…`) and ADR-0131 (`23749bdc…`)
survive unchanged at the delivery branch HEAD. `spec.md` (`82e2c2cf…`) does not:
archiving the contract rewrote its `Status` line and inserted a
`## Why this contract was decomposed` section.

Those two edits are exactly reversible, and the reversal reproduces
`82e2c2cf0041695ee51b4d233e18d64eeb7eb0a923ce2524f61cf36c7b7e1e30` — verified,
not assumed. A reconstruction is therefore byte-exact and self-checking against
the recorded digest.
