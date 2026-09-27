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

## T7 — `xd-state-reviewer-doctrine.md`: confirmed unaffected

The intent is not edited by this delivery, and the check is satisfied by this
record rather than by the update branch.

The intent asks for the `experience-reviewer` quality floor to cover a wider
state set and to be restructured into cold-read, task-completion and
contract-review passes. This delivery's two edits to
`.apm/agents/experience-reviewer.md` are a sync citation, retargeted from the
deleted `tone-of-voice` copy of `references/editorial-quality-gates.md` to the
surviving canonical copy under `content-design`, and an artifact-exclusion
clause, which now names the surviving artifact type `type: tone-of-voice`
instead of a skill name.

Neither touches the reviewer's pass structure, its state coverage, or its
quality floor, so nothing the intent asks for is changed, satisfied, or
invalidated. `xd-state-reviewer-doctrine.md` is confirmed unaffected.

## T7a — `workspace.toml` classification

Three lines still match the removed-name pattern. None is a skill registration,
and none is reconciled by edit:

- The `xd-copy-router` queue entry's own `summary`, which describes this
  delivery as folding `content-design`, `copy-direction` and `tone-of-voice`
  into one skill. That is an accurate statement of what the delivery does; the
  names appear as the subject of the work, not as skills the catalogue is told
  exist.
- `docs/specs/xd-copy-direction/spec.md`, a different delivery whose **slug**
  contains the substring. It is a spec path, not a skill name.
- A `ref` to `docs/rfc/0062-content-design-and-copy-direction-skills.md`, a
  frozen decision record whose filename contains the substring permanently.

These are the same third and fourth classes the final sweep rubric names.

## T10 — a contract conflict, resolved against the enforced control

**The spec's changelog placement criterion cannot be satisfied.** It requires a
free-standing `## [experience-design][4.0.0]` entry **directly beneath
`[Unreleased]`**, and `plan.md`'s changelog validator asserts exactly that
adjacency. But `tests/roster/test_verification_ledger_contract.py::test_the_core_release_heading_sits_directly_beneath_unreleased`
requires the heading directly beneath `[Unreleased]` to be `[core]` at core's
shipped version. Both cannot hold: the position admits one heading.

The conflict is not theoretical on this branch. The sibling
`creative-direction-modes` delivery placed its release heading in that position,
CI's gate-main failed on this same test, and commit `e1164adeb` exists only to
move it back out.

**Resolved in favour of the enforced test.** The entry is free-standing at `##`
and sits immediately below the `[core]` block. What the criterion is actually
protecting is preserved: `packs/AGENTS.local.md` requires a release entry to be
free-standing at `##` and **never nested under `[Unreleased]`**, "where it could
never publish", because `tools/build-site.py` withholds a nested entry as
unreleased and still exits 0. This entry is not nested, so it publishes.

The "directly beneath" wording is the part that is wrong, and it is wrong in the
spec and in the plan's validator together. The obligation it was reaching for —
free-standing, not nested, therefore publishable — is met. Recorded here rather
than by editing the sealed contract, and surfaced to the owner rather than
resolved silently.

## T10 — `FORCE=1` was not needed

The spec lists passing `FORCE=1` to `make build-self` under **Ask first**,
because `packs/AGENTS.local.md` instructs the release pipeline to use it while
the root `AGENTS.local.md` says never to pass it from automation.

The question did not have to be asked. `make build-self` refuses only a **dirty**
working tree, and says so: "working tree is dirty — refusing to write. Pass
--force to override (the dirty-tree check only)." Committing the version bumps
first made the tree clean, and the unforced run then succeeded with exit 0. The
standing conflict is therefore untouched by this delivery.

The regeneration also cleared the two inherited stale projection entries recorded
above: `experience-design` moved 2.0.9 → 4.0.0 and `frontend-engineering`
0.3.2 → 0.3.3. Every pack's projection entry now equals its own `pack.toml`.

## T11 — the delivery-wide registration sweep

Run 2026-09-27 over the five trees, `workspace.toml`, and the five in-scope
`docs/` files, with the generated `now-highlights` projection excluded. It
returns **14 files**, and every hit classifies:

| Class | Files | Disposition |
| --- | ---: | --- |
| 1 — registration | **0** | Must be zero. It is. |
| 2 — counted discriminator | 10 | Required to survive, at the occurrence counts the two carve-out tables record |
| 3 — release history | 1 | `docs/product/changelog.md`, permanent: the 4.0.0 entry is obliged to name both removed skills |
| 4 — frozen decision record | 2 | Both RFCs, permanent: `Accepted`, amendable only by erratum, and RFC-0062's own filename and title contain a removed name |

`workspace.toml` is the one file the four-class rubric does not cleanly reach,
and its three hits are none of the four. They are record mentions of the same
kind as classes 3 and 4: this delivery's own queue summary, which describes the
fold and names what it folds; a different delivery whose **slug**
(`xd-copy-direction`) contains the substring; and a `ref` to RFC-0062's
filename. None tells the catalogue a skill exists, so none is a registration.
The rubric enumerating four classes rather than five is a gap in the plan, not a
defect in the tree.

## T11 — install and update behaviour for a removed skill directory

Established by read-only inspection of the exact code path rather than by a
local fixture, because the mechanism is decidable from the source and a fixture
adds a flake without adding evidence.

`agentbundle.commands.upgrade._apply_single_row` is the whole-pack update path.
Across its 191 lines it walks only the **new** projection, writes those paths,
and records them. It contains no `unlink`, no `rmtree`, no prune, and no
old-minus-new comparison. Its single removal call, `_unproject_removed_rows`,
reconciles user-scope **hook-wiring rows** — not skill files.

The contrast that makes this conclusive is still present: the separate
direct-skill update contract explicitly plans removals, asserted by
`test_direct_skill_upgrade_plans_writes_and_removals_without_catalogue` in the
agentbundle integration suite.

**A whole-pack `agentbundle upgrade` therefore leaves a retired skill directory
resident**, with its `SKILL.md` registration still active, so a copy task could
still route to a skill this pack no longer ships. The `experience-design` 4.0.0
changelog entry carries the adopter action under `### Removed`: remove the
`copy-direction` and `tone-of-voice` directories from the installation's skills
directory after upgrading.

## T11 — manual-QA verdicts

| # | Judgement | Verdict | Reviewer | Date |
| --- | --- | --- | --- | --- |
| 1 | Each reconciliation preserved the rule the surviving modes need | **Pass, re-signed after a failed first signing.** Verified per file against both sources, not by reading the result. For the two scope-borne rewrites every heading and every distinctive rule from both variants was checked present by string match; the only heading not carried is `copy-direction`'s scope-bound title, which the scope parameter replaces. `notes/reference-reconciliation.md` records the disposition of every substantive difference. | Claude (implementer) | 2026-09-27 |
| 2 | No rule present in either variant was silently dropped | **Pass, re-signed after a failed first signing. Three dropped items, none silent.** `audience-jtbd.md` ceases to exist as a basename — recorded, with the reason that `creative-direction` holds a third file of that name which this delivery must not touch. The three-copy duplication note on `editorial-quality-gates.md` is deleted — recorded, and `DESIGN.md` states what supersedes it. Two differences that a naive merge would have dropped were caught and kept: `copy-direction`'s literal VoC flag string, and its wider jargon-check escape hatch. | Claude (implementer) | 2026-09-27 |
| 3 | The three modes remain distinguishable to a reader | **Pass.** `SKILL.md` opens with a three-row table binding each mode to its scope, artifact and path, then a two-question rubric decidable from the request with no reference loaded. Each mode section states what it produces, where it lands, and what it must not do, and the shared anti-patterns close with an explicit refusal to cross the mode boundary mid-run. A reader can answer "which mode is this?" without reading a procedure. | Claude (implementer) | 2026-09-27 |
| 4 | The guide is sufficient | **Pass.** `copy-boundary.md` was rewritten rather than retargeted: its premise is no longer a four-way choice between skills but a mode selection the skill makes, with one real boundary left because it crosses packs. It states that folding the registrations did not merge the outputs and lists all three artifact paths, so the claim is checkable rather than reassuring. All four guide gates exit 0. | Claude (implementer) | 2026-09-27 |

**Verdicts 1 and 2 were signed once on a method that could not see the defect,
and are re-signed here.** A post-gates review found a rule dropped from the
merged `interrogation-sequence.md`: Stage 1's "Capture the raw words verbatim…
Do not translate them yet." It is byte-identical in both pre-fold variants.

The first signing verified completeness by string-matching the *distinctive*
rules each variant carried — that is, the rules the **diff** between them
surfaced. Content identical in both sides never appears in a diff, so it was
never in the set being checked. The method could prove nothing contested was
lost and said nothing about what both sides agreed on. That is a flaw in the
check, not an unlucky miss, and it is why the verdicts were wrong rather than
merely optimistic.

The re-signing rests on a different check: every paragraph of both pre-fold
sources compared against each merged file, across all six reconciled
references, scored for best match. Exactly one paragraph in the whole set had no
counterpart — the one above. It is restored, and the reconciliation note carries
its row. Verdict 2's dropped-item count rises from two to three, all three
recorded with reasons: `audience-jtbd.md` as a basename, the three-copy
duplication note, and this paragraph, which is restored rather than dropped.

A second post-gates finding is also closed here: the `copy-grounding.md` verdict
that `copy-direction`'s literal VoC flag wins was applied at the recording
checklist but not at the elicitation step, leaving the two sites disagreeing —
the exact drift the verdict was written to prevent, reproduced inside one file.
Both sites now carry the literal.

**Fifth verdict — the `brand-register` slug refusal survives.** **Pass.** The
per-surface mode's step 6 stops when `<surface-slug>` is `brand-register`,
states that the path is reserved for the brand-level register mode, and asks the
user for a different slug. It refuses rather than repairing: the text says so
explicitly ("Do not repair the request by renaming it silently"). The
`copy-boundary.md` guide states the same refusal to the adopter. This is
recorded as a fifth entry rather than as one of the four, because the Testing
Strategy enumerates four judgements and this is not among them.
