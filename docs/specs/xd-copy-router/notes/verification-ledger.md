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

## T5 — execution observations

**The surviving-skill sweep has two forms, and only the precise one is
satisfiable.** The verification map runs two checks over `content-design`:

1. A registration/path-position grep —
   `skills/(copy-direction|tone-of-voice)`, a backticked bare name, or
   "<name> skill". This one is **clean**.
2. A broader "strip the discriminators, then search what is left" grep, whose
   pattern is the bare `\b(copy-direction|tone-of-voice)\b`.

Form 2 cannot reach zero, and the spec is why. It requires the relocated assets
to be named exactly `content-design/assets/copy-direction-template.md` and
`content-design/assets/tone-of-voice-template.md`, and the bare pattern matches
inside both filenames. It also matches "a copy-direction record", the artifact
name, which appears inside the frontmatter `description` that T9 pins
byte-identical to the tested probe candidate — so that occurrence cannot be
edited at all without reopening T1.

Measured after the merge, form 2 returns exactly three kinds of hit and nothing
else: `copy-direction record` ×4 (artifact name, one inside the pinned
description), `copy-direction-template.md` ×2, and `tone-of-voice-template.md`
×2. Every one is an artifact name or a spec-mandated asset filename; none is a
registration, a routing target, or a path into a removed skill directory.

The spec's own wording settles which reading governs: it scopes the check to
"the removed names in registration or path position — `skills/copy-direction`,
"the `tone-of-voice` skill", a routing target". Form 1 implements that scope and
passes. Recorded here rather than by editing the sealed plan.

Two genuine registration hits were found and retargeted, both named by the plan:
`content-design/SKILL.md`'s legacy-artifact branch described "the old per-surface
tone-of-voice behaviour", now "the old per-surface brand-voice behaviour of
experience-design 1.x"; and `references/communication-modes.md` routed
downstream work to a removed skill, now to this skill's per-surface acquisition
copy goals mode.

**The pooled corpus matches the spec's figures exactly.** 29 distinct positive
and 32 distinct negative queries, zero opposite-`should_trigger` collisions,
with the `ux-writing` and `creative-direction` negatives retained. All eight
eval definitions from the three sources carry into one `evals.json`, re-prefixed
by mode because `content-design` and `tone-of-voice` both used the ids `1` and
`2`. Both source `evals/files/` trees carry: their `agentbundle-layout.toml`
fixtures are byte-identical and land as one, and `sample-brief.md` had only one
source.

## T6 — eval-harness disposition, per source

Four source items existed at the merge-base under the two deleted directories.
Each gets its own disposition; one surviving `content-design/evals/` directory
does not prove both sources were handled.

copy-direction/evals/evals.json: carried - its four eval definitions are in
content-design/evals/evals.json, re-prefixed `surface-` because two sources both
used the ids `1` and `2`.

copy-direction/evals/files: carried - both fixtures landed in
content-design/evals/files/. `sample-brief.md` had only this source;
`agentbundle-layout.toml` was byte-identical to the other source's copy and the
two merged into one file.

tone-of-voice/evals/evals.json: carried - its two eval definitions are in
content-design/evals/evals.json, re-prefixed `register-`.

tone-of-voice/evals/files: carried - its only member, `agentbundle-layout.toml`,
is byte-identical to `copy-direction`'s and is present as the single merged copy
in content-design/evals/files/.

Nothing was dropped, so no drop reason is owed. The pooled `eval_queries.json`
carries 29 distinct positives and 32 distinct negatives with no query appearing
under both `should_trigger` values.

## T6 — the byte-equality assertion is GREEN here

`test_every_editorial_quality_gates_copy_is_byte_identical` passes now that the
glob returns exactly the two surviving copies. It was red from T3, correctly, and
this is the task that clears it — the transition T3's record predicted.

## T6 — execution observations

**The deletion left no empty directory shells.** Both directories are gone from
the working tree as well as the index, so the sibling genre fold's outcome —
where a managed filesystem refused `rmdir` and left six empty shells behind — did
not recur here.

**T6's `Touches:` was narrower than its own assertion needed.** The task asserts
no removed name survives as a registration anywhere under `.apm/skills/`, and it
may do so because every matching file is its own or an ancestor's. But repairing
the hits required editing six files outside its declared `Touches:`:
`experience-status/SKILL.md` (a "what to run next" suggestion list naming both
removed skills as routing targets), `content-design/assets/copy-direction-template.md`
and `assets/tone-of-voice-template.md` (each opening "Written by the `<name>`
skill" — a registration inside a shipped template), `content-design/evals/evals.json`
and `evals/files/sample-brief.md`, and
`information-architecture/references/conversion-design.md`.

All six are surfaces an ancestor installed or that the genre fold created, and
all are inside the assertion's stated scope; none belongs to an unordered
sibling, so no two tasks contend for them. The gap is that the reconciliation
gave this task authority over the four paths it deletes and rewrites, not over
the ancestor-installed files its own sweep obliges it to clean. Recorded rather
than resolved by editing the sealed plan.

One occurrence is deliberately kept: `content-design/evals/eval_queries.json`
contains the positive query "Write a tone-of-voice doc for our whole product".
That is a user's phrasing, not a registration — users will keep asking in the
old vocabulary, and the corpus exists to prove the surviving skill still answers.

**Two guide-agreement assertions go red at T6 and T7a clears them.**
`tests/roster/test_experience_design_guide_agreement.py` fails with
"`derive-the-screen-flow.md` runs `tone-of-voice`, which this pack does not
ship". The guide tree is T7a's `Touches:` and T7a depends on T6, so no ordering
makes this green here. It is the same shape as the byte-equality assertion's red
between T3 and T6: the suite is correct, and it is reporting work a descendant
owns.
