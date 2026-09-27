# Verification ledger — xd-copy-router

This file records judgement-based evidence and execution observations that the
mechanical gates cannot settle. The approved `spec.md` and `plan.md` hold the
obligations.

## T2 — the genre fold's post-condition, verified rather than assumed

Checked 2026-09-26 against merge-base `71b0055ee335d90eab77cfd52c9adb638ae7436f`.

| Check | Result |
| --- | --- |
| `information-architecture/references/editorial-quality-gates.md` exists | **Pass** |
| Byte-identical to `conversion-design`'s copy at the merge-base | **Pass** — both `481b6c496e3c769a2ddf1e35a906794582fcb19e7b977b9eb70b212bc69f806a` |
| `information-architecture/SKILL.md` cites it | **Pass** — line 69, in the `marketing` genre row |

The comparison is made against the merge-base deliberately. The genre fold has
already landed on this branch and deleted `conversion-design/`, so a
`git show HEAD:` comparison would fail with "path does not exist" and read as
"bytes differ" rather than as a missing precondition.

This slice does not create the shared file. A second author of a shared file is
how the three-way drift this delivery reconciles began. Had either check failed,
the slice would stop here and the genre fold would be amended before it resumed.

**Verdict: the precondition holds. T3 may begin.**

## Pre-existing state this delivery inherits

`agentbundle catalogue verify` fails before this delivery changes anything. The
self-host projection is out of date: `.claude-plugin/marketplace.json` reads
`experience-design 2.0.9` against a `pack.toml` of `3.0.0`, and
`frontend-engineering 0.3.2` against `0.3.3`. Both were left by earlier
deliveries that bumped a manifest without committing a regenerated projection.
T10 regenerates it and clears both. A pre-T10 `catalogue verify` failure naming
only those two entries is this inherited state; a third name is a real finding.
