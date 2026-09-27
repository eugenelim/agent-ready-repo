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

## T3 — execution observations

**The byte-equality extension is red here, and that is its correct state.**
`test_every_editorial_quality_gates_copy_is_byte_identical` globs
`*/references/editorial-quality-gates.md`, which currently returns four copies.
The two surviving ones — `content-design`'s and `information-architecture`'s —
are byte-identical at
`1308734c18d8ec49592408dff5e15e74751645ba8efae2ef0f5900bbcb506f77`. The
assertion fails naming exactly `['copy-direction', 'tone-of-voice']`, the two
directories T6 deletes. T3 owns the extension's existence; T6 owns its GREEN.
A green result at this position would mean the glob was narrowed or a deletion
happened outside T3's `Touches:`.

**The verification map's selector does not match the mandated test name.**
`plan.md`'s byte-equality block runs
`-k editorial_quality_gates_copies_are_byte_identical`, while T3's `Tests:`
mandates the name `test_every_editorial_quality_gates_copy_is_byte_identical`.
`-k` matches substrings, and the map's string is not a substring of the
mandated name, so the map's selector exits **5** — "no tests ran" — even now
that the extension exists. The map reads exit 5 as "the extension has not
landed yet", so as written it can never observe this test at all.

The contract-mandated name is authoritative and is what shipped; the map's
selector is the inconsistent copy of the same value, the same drift this pair
was reconciled against elsewhere. The working selector is
`-k every_editorial_quality_gates_copy_is_byte_identical`, and the whole-file
run reaches it unconditionally. Recorded here rather than by editing the sealed
plan.
