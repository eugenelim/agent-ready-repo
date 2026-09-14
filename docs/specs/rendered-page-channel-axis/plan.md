# Plan: Rendered-page inspection channel axis

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (runtime export boundary, pack test
  loader naming, version bump rule, no internal-governance citations in shipped
  content); `packs/frontend-engineering/AGENTS.md` (pack scope);
  `guides/_shared/reference/catalogue-authoring-standards.md` (skill authoring).
  Analogous implementation: the shipped height-and-scroll axis in
  `.apm/skills/frontend-engineering/references/rendered-page-inspection.md`
  § *Required captures*, its reader `required_captures()` /
  `evaluate_capture_set()` in
  `packs/frontend-engineering/tests/skills/frontend-engineering/frontend_engineering_rendered_page_rules.py`,
  and the suites that drive it (`test_rendered_page_capture_contract.py`,
  `test_rendered_page_unscrollable.py`). The channel axis is built as a third
  dimension of that same table-plus-reader shape; no new mechanism is introduced.

## Approach

The axis is added where the existing two axes live: as shipped table rows the
rule-reading module reads, never as a quantifier the module supplies. Three
mechanical facts shape the order of work.

A width predicate needs no new parsing — `satisfies()` already handles the five
comparison forms, so the channel table reuses the cell grammar the height column
uses. The completeness walk gains an outer loop over required channels, which
turns `required_captures()`'s two-tuple into a channel-keyed structure; every
caller of that function moves with it.

The fixtures are the substantive work. Three suites build a capture by writing
width as a function of height, which is exactly the premise the delivery removes;
each needs a fixture that varies the two independently. That change is what makes
the new requirement observable, so it lands with the rule rather than after it.

## Constraints

- The runtime export boundary is `.apm/`. Tests never live there, and the pack's
  test modules carry pack and skill in their names.
- `frontend_engineering_rendered_page_rules.py` is the single rule reader. A
  second reader, or a rule restated in a suite, is out of bounds.
- Shipped `.apm/` content cites nothing from this repository.
- `make build-self` runs after every `.apm/` edit; `ruff check` runs before push.

## Construction tests

Per-task, below. **Integration tests:** none beyond per-task tests — the pack has
no integration tier. **Manual verification:** one end-to-end capture run across
two channels against a real surface, its observations recorded (T8).

## Durable-output map

| Durable output (spec) | Tasks |
| --- | --- |
| Rule layer — reference | T1, T2, T3 |
| Adopter-facing skill | T4, T5 |
| Reviewer lens | T6 |
| Adopter guidance — how-to | T7 |
| Interface compatibility — superseded criterion | T9 |
| Execution observation | T8 |
| Decision rationale | spec body; no task |
| Eval harness | T6 |
| Release history | T9 |

## Design (LLD)

### Design decisions

**The height-only floor is removed by hand and pinned, not asserted by a
predicate.** `AC-0021`, `AC-0022` and `AC-0025` were demoted on 2026-09-13 under
owner authority; the spec's Retired identifiers section records why. The
obligation stands and this is where it lives. Five shipped strings state the
superseded floor and all five are rewritten:

| Artifact | Site | Text |
| --- | --- | --- |
| `evals/evals.json` | `assertions[0]` | "Captures at a viewport height of at most 600 CSS pixels and at least 900, each at rest and scrolled" |
| `evals/evals.json` | `expected_output` | opening sentence, "The capture set covers both required viewport heights…" |
| the how-to | `:45` | "Take four captures per route: two viewport heights, each at rest and scrolled." |
| the how-to | `:47-52` | the height-keyed capture table |
| the how-to | `:59` | "Extra heights are welcome and none beyond these two is required" |

The protection is a content pin asserting those five strings are absent, not a
general predicate. No token list decides the class: three of the five carry no
completeness word at all, and the token that would red them also reds the guide's
`:62-64` unscrollable-branch sentence, which must survive. A criterion claiming
the general property would be a control that cannot fail on the class it names.

The spec's Objective and Assumptions own why the axis is breakpoint-derived and
why the fallback bands leave a dead zone. What is not recoverable from there:

**The capture width is the band's edge, and that is a deliberate trade.** AC-0024
returns the lower bound where a band has one, so a declared `[480, 768, 1024]`
yields 479, 480, 768 and 1024 — two of them one pixel apart. Every band gets
exactly one capture, so every band keeps an uncaptured remainder:

| Band | Captured | Uncaptured |
| --- | --- | --- |
| `<480` | 479 | 0–478 |
| `>=480 <768` | 480 | 481–767 |
| `>=768 <1024` | 768 | 769–1023 |
| `>=1024` | 1024 | 1025 and above |

The first band is the exception in direction, not in kind: with no lower bound to
read, the rule takes the largest width its upper bound admits, so its uncaptured
region sits below its capture rather than above it. The edge is chosen because the defect class this delivery names is a
rule scoped to one side of a breakpoint reaching the other, and only widths
straddling the breakpoint exercise both scopes: a declared 1152 yields 1151 and
1152. What it gives up is a rule that misbehaves anywhere in a band other than at the
pixel captured — the whole of each uncaptured remainder above. That is a
different defect class from the one this delivery names, and it stays invisible. One operational caveat for the implementer:
a scrollbar-inclusive layout viewport can put a media query on the other side of
the number the driver was handed, so a capture taken at the boundary needs its
attained width read back from the page, the way the attained scroll offset
already is.

**The absent-row guard is the raise, not the skip.** The rule reader guards an
absent row two incompatible ways today — `inspection_result` raises
(`frontend_engineering_rendered_page_rules.py:540-544`, whose own comment says a
default "makes this module state the rule"), while the pair-rule consumer skips
the whole rule (`:246-248`). The channel reader follows the raise. Under the skip
shape, deleting the channel row leaves the checks green, and AC-0008 cannot pass.

### Data & schema

The reference gains a `## Channels` section and generalizes one existing rule
row. Two row keys are shipped content the suites read by name:

| Row key | Table | States |
| --- | --- | --- |
| `every-captured-width-and-height-needs-the-pair` | Required captures, rule rows | replaces `every-captured-height-needs-the-pair` |
| `channel-basis-recorded` | Channels, rule rows | the AC-0003 record |
| `channel-name-forbids` | Channels, rule rows | `required` — the switch AC-0012's guard reads before enforcing |
| `channel-capture-width` | Channels, rule rows | the AC-0024 derivation |

The forbidden device-name tokens ship as a **one-column table** under their own
heading, mirroring the `## Rate vocabulary` table the measurement reference
already carries and the guard at
`test_rendered_page_shipped_content_limits.py:115` already parses with
`^\| ([a-z][a-z -]+) \|$`. A comma-separated cell would invent a grammar nothing
else in the reference uses and would forfeit `unique_keyed`'s duplicate rejection
over the tokens.

The `## Channels` section carries **three-cell band rows** — name, lower bound,
upper bound, either bound cell empty for unbounded — and two-cell rule rows. Cell
width separates them, which is how `capture_set_rules()` already separates the
rule rows under `Required captures` from that table's three-cell rows
(`:485-502`). Heading separation would not work: `table_rows()` returns only the
first pipe table under a `## ` heading and breaks at the first non-pipe line once
rows have started (`:51-59`), so a second block under one heading is unreachable
and a `###` sub-heading is invisible to it.

Two cells rather than one because `satisfies()` parses one operator and one bound
per cell (`:143`) and raises on `>=480 <1024`. The reader conjoins the pair; the
per-cell grammar is untouched.

`required_captures()`'s return shape gains the channel dimension; its three
callers in the module migrate with it.

### Behavior & rules

Completeness is evaluated per route, then per required channel, then per required
height-and-scroll row — the existing two-level walk gains one level. The pair
rule's grouping key moves from the height alone to the width-and-height pair;
grouping by band instead would let two widths in one band each carry half a pair
and read as coverage.

### Failure, edge cases & resilience

A surface declaring one breakpoint yields two channels — the same count as the
fallback, at different bands. A declared breakpoint at or below the narrowest
capture, or above the widest, still bounds a channel the set must cover; an
uncoverable channel is an incomplete result, not a waived one.

### Dependencies & integration

No new dependency. The pack's declared dependency surfaces are compared before
and after (T9).

## Tasks

### T1: The reference states the channel axis

**Depends on:** none
**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/references/rendered-page-inspection.md

**Tests:** goal-based check — this task ships content that T2's assertions read.
AC-0001, AC-0002, AC-0003, AC-0004 and AC-0024 are stated here and asserted
there; nothing in this task asserts them itself.

**Approach:** add a `## Channels` section to the reference carrying the fallback
band table (name, lower bound, upper bound), and the breakpoint-derived rule, the
capture-width rule and the channel-basis recording rule as two-cell rule rows in
the established shape, plus the forbidden device-name tokens as their own
one-column table — the only shape in this reference that holds a token list.
Generalize the `every-captured-height-needs-the-pair` row and the prose stating
the required set. State the axis's reason without naming any surface outside the
pack.

**Done when:** the reference's new tables satisfy `table_rows`'s cell-count rule
and `unique_keyed`'s duplicate-key rule, and a search for the literal
`every-captured-height-needs-the-pair` across `packs/frontend-engineering/`
returns no remaining site. The search output is the enumeration — do not write a
count here and check against it. A run of that search on 2026-09-13 returned
seven sites across three files, where an earlier hand-written count in this same
Done-when said two.

### T2: The rule reader derives the channel requirement from the reference

**Depends on:** T1
**Touches:** packs/frontend-engineering/tests/skills/frontend-engineering/frontend_engineering_rendered_page_rules.py, packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_verdict.py

**Tests:** TDD, in `test_rendered_page_capture_contract.py`, covering AC-0001,
AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008 and AC-0024.

This task also owns `test_rendered_page_verdict.py`'s
`test_no_check_enforces_a_capture_rule_the_pack_does_not_state`. Its `md.replace`
of the old row key becomes a no-op under the rename, so it fails with a message
about something else; and its `evaluate_capture_set(without, extra)[0] ==
"complete"` assertion ratifies the fail-open skip AC-0008 exists to replace with
a raise. Its intent is re-decided here, not its literal: the case must assert
that an absent rule row raises. The mutation that
must red is deleting the channel requirement from the reference, not editing the
module — the criterion is that the requirement is shipped. Assert the derived
channels for a declared-breakpoint list, for the empty list, and that
`evaluate_capture_set` reports the four missing requirements a one-width-per-height
set produces.

**Approach:** add a channel reader beside `required_captures()`; widen
`evaluate_capture_set`'s per-route walk with the channel loop; move the pair
rule's grouping key to the width-and-height pair. Source every rule from the
markdown and raise on an absent row as `inspection_result` does at `:540` — the
`:246-248` `continue` is the fail-open shape this task avoids, because under it
AC-0008's mutation leaves the checks green.

**Done when:** a repository-wide search for the `required_captures` symbol returns
no consumer still indexing the two-tuple — the search reaches
`test_rendered_page_unscrollable.py:24,130-138`, which imports it and which the
module's own call sites do not count.

### T3: The fixtures vary width and height independently

**Depends on:** T2
**Touches:** packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_capture_contract.py, packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_verdict.py, packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_unscrollable.py

**Tests:** TDD for AC-0005, AC-0006 and AC-0007. The three suites' existing cases
are the tests; they go red at T2
and green here. A case that needs a complete set gets one built across both
channels; a case asserting incompleteness names which channel it is short of.

**Approach:** replace the `390 if height <= 600 else 1280` fixture helper in each
suite with one taking width and height as separate arguments. Do not narrow an
assertion to accommodate a set that is now short — the expected red is the defect.

**Done when:** no capture set in the pack's test tree writes its width as a
function of its height. That reaches both encodings of the premise — the
`390 if height <= 600 else 1280` helper, and
`test_rendered_page_capture_contract.py:59-64`, which writes the same pairing out
as four literals and which no search for the helper expression finds.

### T4: `SKILL.md` states the channel axis and teaches it by example

**Depends on:** T1
**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md

**Tests:** TDD for AC-0009 and AC-0010, in `test_rendered_page_capture_contract.py` —
a parse of both copies of the capture contract and an equality assertion between
them, plus a parse of the worked snippet. The drift guard reads both tables, not one.

**Approach:** update § 5a's capture table and surrounding prose to the channel
axis, and rewrite the worked capture snippet so the viewport it opens is
parameterised over channel and height rather than hard-coded to one width. Keep
the section inside the `CAT-S003` body ceiling.

**Done when:** § 5a's body stays inside the `CAT-S003` ceiling, measured rather
than assumed, and `make build-self` leaves no projection diff.

### T5: The evidence manifest records channels

**Depends on:** T4
**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md, packs/frontend-engineering/JOURNEY.md

**Tests:** TDD for AC-0011 and AC-0012, in
`test_rendered_page_shipped_content_limits.py`. AC-0023 is verified in the suite
the spec's Testing Strategy names for it, not here. The guard **reads** the forbidden
token list from the reference rather than stating it, which is what makes AC-0012
delete-and-red the way AC-0008 requires of the other rows. The shape already
exists in this module: `test_the_rate_vocabulary_matches_what_the_pack_states`
(`:103-119`) parses a `## Rate vocabulary` section out of the measurement
reference and asserts the module's list equals it. Mirror that for the
`channel-name-forbids` row. The genericity guard beside it legitimately states
its own list, because repository identifiers are not a rule an adopter is held to.

**Approach:** restate the `viewports` row of `SKILL.md`'s evidence-manifest
required-field table as channels covered, given as width predicates. It currently
names three devices and is inside AC-0012's scope, so it is rewritten here rather
than left. Add declared breakpoints to `JOURNEY.md:12`'s `youProvide`, which today
names routes and viewports and not the new input. `JOURNEY.md`'s two *manifest*
mentions (`:84`, `:169`) stay untouched: they name the `viewports` field in an
inventory and never state what it holds, so the axis change does not reach them.

**Done when:** the `viewports` row of `SKILL.md`'s evidence-manifest
required-field table no longer names a device, and the only changed line in
`JOURNEY.md` is `:12`.

### T6: The reviewer and the eval harness read the width axis

**Depends on:** T1
**Touches:** packs/frontend-engineering/.apm/agents/frontend-reviewer.md, packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json

**Tests:** TDD for AC-0013 and AC-0016, in `test_rendered_page_reviewer_sight.py`.
Rewriting the harness's two height-only strings is this task's work and is pinned
by the content pin in § Design decisions, not by a criterion.
Scope the lens read to the lens section rather than the whole agent file, the way
that suite already scopes its reads; the whole-file read passes on the shared
output-rendering block. AC-0016 parses `evals/evals.json` in the same module.

**Approach:** extend lens 6 so the width joins the scroll position as a field the
reviewer must use, and recheck the "differ only by that field" sentence against
the widened axis. In the harness, add the channel-coverage assertion **and**
rewrite the first assertion and the opening `expected_output` sentence, which
today define a complete set by height alone — after this delivery a run matching
them exactly is `incomplete`.

**Done when:** `catalogue lint --deep` and `catalogue verify` accept the edited
agent and harness, and `make build-self` leaves no projection diff for either.

### T7: The how-to walks a two-channel capture set

**Depends on:** T4
**Touches:** guides/frontend-engineering/how-to/inspect-the-rendered-page.md

**Tests:** goal-based check for AC-0018 — a search over the guide for both
fallback channel names, the band between them that no fallback capture reaches,
and the per-channel floor. The negative half is the content pin in § Design
decisions over the guide's three height-only strings; it is not a criterion,
because no predicate reds those three while sparing `:62-64`. The repository's
documentation gates stay a separate well-formedness check.

**Approach:** take the guide's worked walk across both channels — its capture
table and the prose under it (`:45-65`), and its capture-record table (`:74-77`) —
and state what a reader records when no breakpoints are declared, plus the band
between the two fallback channels that no fallback capture reaches. The three
guide lines that state the superseded floor are `:45` ("Take four captures per
route"), the height-keyed table at `:47-52`, and `:59` ("none beyond these two
is required"); all three are in the content pin recorded in § Design decisions,
and the guide's `:62-64` unscrollable-branch sentence must survive the rewrite.

**Done when:** the guide's links resolve under the repository's documentation
gates.

### T8: The step is performed end to end across two channels

**Depends on:** T3, T4
**Touches:** docs/specs/rendered-page-channel-axis/notes/verification-ledger.md

**Tests:** visual / manual QA for AC-0017 — a recorded gesture. A passing
completeness test is not evidence that a second channel found anything.

**Approach:** run the capture against a real surface at both channels and both
heights, route the images to a judge, and record the observations and the channel
basis.

**Done when:** `docs/specs/rendered-page-channel-axis/notes/verification-ledger.md`
exists and carries the four values AC-0017 names.

### T9: The release surface carries the change

**Depends on:** T1-T8
**Touches:** packs/frontend-engineering/pack.toml, packs/frontend-engineering/.claude-plugin/plugin.json, docs/product/changelog.md, docs/specs/rendered-page-visual-inspection/spec.md, tests/roster/test_rendered_page_channel_axis_supersession.py

**Tests:** AC-0019 is TDD in
`tests/roster/test_rendered_page_channel_axis_supersession.py` — the frozen spec
belongs to this repository's spec lifecycle, not the pack's, so the assertion
lives in the repository's own suite. AC-0014 and AC-0015 are a goal-based check —
compare the two manifests' version fields, confirm
the changelog entry is this pack's topmost release heading, and compare the pack's
declared dependency surfaces before and after to show none was added.

**Approach:** bump both manifests to `0.2.4` and lead a changelog entry with the
pack and that version. Diff `origin/main:packs/frontend-engineering/pack.toml`
first so an unpushed peer bump does not collide silently. Add the `Status:` line
pointer on `docs/specs/rendered-page-visual-inspection/spec.md` naming AC-0007 as
the successor to its height-only pair criterion; that spec is frozen, so the
pointer is the only edit it takes.

**Done when:** `make build-self` leaves no projection diff and `ruff check` is
clean across the changed Python.

## Rollout

- **Delivery:** big bang within the pack, behind a version bump. Reversible by
  reverting the pack content and the manifests together.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** the reference (T1) leads, because every other task
  reads it.
- **Adopter impact:** an adopter's existing capture set becomes incomplete at the
  new version. That is the intended signal, and the changelog entry states it.

## Risks

- **The pair rule's new grouping key makes an extra captured width noisy.** A
  route captured at three widths now owes a scroll pair at each. Accepted: it is
  the same obligation the height axis already carries, and the alternative —
  grouping by band — lets two widths in one band each carry half a pair.
- **`SKILL.md` headroom.** 873 of 1,000 body lines. The § 5a edits are small, but
  T4 measures rather than assumes.
- **Three suites go red at T2 and stay red until T3.** The wave order keeps that
  window inside one task boundary; a gate run between them is expected to fail.

## Changelog

- 2026-09-13 — Adversarial round 2: 9 findings, 3 blockers, two of them round 1's
  own repairs failing. The rename Done-when had replaced a sweep with a
  hand-written count of two against seven real sites. The AC-0021/AC-0022
  predicate could not red three of the five fixtures those criteria named. Owner
  demoted AC-0021, AC-0022 and AC-0025; the obligation is now design material
  plus a content pin, which is the rung the spec template prescribes for an
  obligation whose only check is that a sentence exists.
- 2026-09-13 — Adversarial spec-mode review, adjudicated: 11 findings, all
  sustained, none refuted. Three blockers. The rename breaks two pins in
  `test_rendered_page_verdict.py` that no task owned, and one of them ratifies
  the fail-open skip AC-0008 abolishes — the anchor-test sweep PLAN step 8a asks
  for was not run. A channel was a name plus two bounds with no rule turning it
  into an integer width, so AC-0010 was unsatisfiable; AC-0024 states the
  derivation and a probe shows it total across fallback, one-breakpoint and
  three-breakpoint bands.
- 2026-09-13 — Shaping review round 4, with the four previously unread surfaces
  seeded: 6 findings, no blocker. Three existed only because those files were
  finally opened. The harness and the how-to both define completeness by height
  alone, so an additive criterion on either would have left two contradictory
  floors in one artifact; AC-0021 and AC-0022 are the negative halves. The
  deletion pass had also generalized a claim about two manifest lines to the whole
  journey file, missing `:12`'s input declaration.
- 2026-09-13 — Deletion pass over the criteria review added. AC-0020 cut and
  `JOURNEY.md` dropped from the change: its two manifest mentions name the
  `viewports` field in an inventory and never state what it holds, so the axis
  does not reach them. Round 1's finding 10 offered this branch and the wider one
  was taken without opening the file.
- 2026-09-13 — Shaping review round 3: 5 findings, no blocker, all taken. Three
  were companion statements left stale by round 2's repairs; one moved AC-0019's
  check out of the pack suite, which has no business asserting on this
  repository's spec lifecycle.
- 2026-09-13 — Shaping review round 2: 10 findings, all taken; eight were
  consequences of round 1's own repairs. The Blocker was the repaired AC-0001
  needing a two-sided interval that `satisfies()` raises on, fixed by three-cell
  band rows the reader conjoins.
- 2026-09-13 — Shaping review round 1: 17 findings, all taken. Blockers were a
  self-contradicting AC-0003, an unstated band-boundary convention, and a T2
  guard instruction pointing at the module's fail-open shape.
- 2026-09-13 — Drafted. Channel axis settled as breakpoint-derived with a
  two-band fallback, four height-and-scroll captures per required channel, and
  declared breakpoints as an optional adopter-supplied input.
