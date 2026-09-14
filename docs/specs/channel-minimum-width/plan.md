# Plan: Channel minimum width

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (runtime export boundary, pack test
  loader naming, version bump rule, no internal-governance citations in shipped
  content); `packs/frontend-engineering/AGENTS.md`;
  `docs/CONVENTIONS.md` § *Pack source-of-truth split* (what counts as an
  adapter-projected primitive; the bump rule itself is `packs/AGENTS.md`
  § *Version bump rule*, which names the term without defining it).
  Analogous implementation: the channel axis itself — the `## Channels` rule rows
  in `.apm/skills/frontend-engineering/references/rendered-page-inspection.md`,
  their reader `required_channels()` in
  `packs/frontend-engineering/tests/skills/frontend-engineering/frontend_engineering_rendered_page_rules.py`,
  and its construction tests in `test_rendered_page_capture_contract.py`. This
  delivery adds an input to that same table-plus-reader shape; no new mechanism.

## Approach

The minimum is a filter over the bands the existing derivation already produces,
applied after them rather than inside them. `required_channels` keeps deriving
`<b1`, `>=bk <bk+1`, `>=bn` from the breakpoints; a second pass drops a band
whose whole range is below the minimum and raises the lowest survivor's lower
bound to the minimum where its own bound sits below it. Keeping the two separable is what lets the existing
five-case derivation tests stand unchanged and the new cases test only the
filter.

Three mechanical facts shape the order of work. The filter needs no new
predicate grammar, because a clamped band is two cells the existing `satisfies()`
already parses. Two new rule rows join the six the walk requires present, so
`REQUIRED_RULE_ROWS` and its equality control move in the same task as the rows.
And the recorded effects are two fields rather than one, so `channel_basis`
keeps its two-value vocabulary and gains siblings instead of a third value.

## Constraints

- `.apm/` is the runtime export boundary. Tests never live there, and the pack's
  test modules carry pack and skill in their names.
- `frontend_engineering_rendered_page_rules.py` is the single rule reader.
- Shipped `.apm/` content cites nothing from this repository.
- After every `.apm/` edit, run `FORCE=1 make build-self`: the plain target
  refuses a dirty tree, which is the state each task leaves behind, so the bare
  invocation cannot serve as a task's own evidence. `ruff check` before push.
- `build-self` is `agentbundle catalogue self-host` and writes adapter
  projections only — it never writes under `web/`. The committed web journey copy
  is produced by `python3 tools/build-site.py --journeys-only`, the command the
  build's own staleness message names, and by no gate-chain step. A task that
  changes `JOURNEY.md` owes that second invocation.
- A mutation proof mutates by editing and restores by editing. `git checkout`,
  `git reset` and `git stash` are not restoration here: a failed restore leaves a
  dirty tree that the next gate reads as a defect.

## Construction tests

Per-task, below. **Integration tests:** none beyond per-task tests — the pack has
no integration tier. **Manual verification:** one end-to-end capture run against
a real single-channel surface with a minimum declared (T6).

## Durable-output map

One row per Durable Outputs row in the spec, using that table's semantic-role
strings verbatim.

| Semantic role (spec) | Tasks |
| --- | --- |
| Current product truth — rule layer | T1 |
| Current product truth — adopter-facing skill | T3 |
| Current product truth — journey input | T3 |
| Adopter guidance | T4 |
| Decision rationale | none — the spec's own Objective, Acceptance Criteria and Assumptions are the destination, and shaping wrote them |
| Reusable learning — eval harness | T5 |
| Interface compatibility — superseded criterion | T7 |
| Execution observation | T6 |
| Release history | T8 |

T2 appears in no row: it ships the reader, which is code covered by the rule
layer's own row and reconstructible from the module and its tests.

## Design (LLD)

### Design decisions

**The filter runs after the derivation, not inside it.** Folding the minimum into
the band construction would make every existing derivation case a
minimum-of-`None` case and put two rules in one loop. Separating them means the
shipped five-case derivation tests keep testing the derivation.

**The clamp raises a bound and never lowers one.** AC-0003 states the rule and
its 600-minimum fixture. What the criterion does not carry is why only the lowest
survivor can be affected, and the reason is the ordering, not a property of the bands above it: bands are
ordered and non-overlapping, so a band above the lowest survivor has a lower
bound at or above that survivor's upper bound, which already admits a width at
or above the minimum. That holds for the contiguous breakpoint bands and for the
fallback pair's 481-1023 gap alike. The
capture-width rule then needs no special case, since it reads the lower bound
first.

**The clamped band keeps its own upper bound.** The capture-width rule reads the
lower bound first, so once a band is clamped its upper bound stops influencing
any capture width — which means a clamp that widened the upper bound away would
be invisible to a width-based assertion. Two channels at `>=480` and `>=1024`
would then both admit 1024, and one capture would satisfy both. AC-0017 asserts
the disjointness directly for that reason, and the derivation fixtures compare
full bound pairs rather than capture widths.

**Two recorded fields, not a third basis value.** A minimum composes with either
basis, so a third value could not express a surface that declares both. The
vocabulary `channel_basis` pins stays two values; the minimum and the discarded
breakpoints are separate records.

### Data & schema

Two new rule rows, both read by the walk and therefore both in the set it proves
present before running:

| Row key | Table | States |
| --- | --- | --- |
| `channel-minimum-derivation` | Channels, rule rows | the token AC-0015 pins; not restated here |
| `channel-minimum-recorded` | Channels, rule rows | `required` — the switch both recording readers consult, and AC-0016's mutation target |

The none-token literal and its ground are AC-0006's; the `## Capture record`
prohibition is *Never do*'s. Neither is restated here.

`REQUIRED_RULE_ROWS["Channels"]` goes from six keys to eight. Its equality
control compares that constant against what `channel_rules` reads, so the two
move together or the control reds.

### Behavior & rules

`required_channels(markdown, declared_breakpoints, minimum=None)` derives bands
as today, then applies the filter, and `evaluate_capture_set` grows the same
parameter and passes it through, as does `inspection_result` above it — the
chain is `inspection_result` → `evaluate_capture_set` → `required_channels`, and
a minimum that stops anywhere short of the top is unreachable from the result an
adopter records, which is the whole outcome. `inspection_result` deliberately
does not echo the basis back, and the minimum follows that same rule: it selects
required channels and is recorded on the § 5a manifest row, not in the result. The clamped-band naming rule and its two templates are stated in AC-0002 and
AC-0003, with the fallback exception; the walk prints that name in its incomplete
report, which is why it is contract rather than detail. AC-0002 and AC-0003 are canonical for the drop
condition and the clamp; this plan states the mechanism they imply rather than
the rules themselves, so a correction to either lands in one place. The
mechanism: one pass that drops a band
whose upper bound admits no width at or above the minimum, then raises the lowest
survivor's lower bound to `max(minimum, its own)`, collecting breakpoints
strictly below the minimum as it goes, so the discarded list is a by-product
rather than a second pass.

### Failure, edge cases & resilience

A minimum below every breakpoint drops no band and is not an error, and it still
raises the lowest band's lower bound to the minimum — with breakpoints
`[400, 800]` and a minimum of 100 the lowest band becomes `>=100 <400`, captured
at 100 rather than 399. A minimum that falls in the fallback bands' deliberate
481–1023 gap drops `narrow` and leaves `wide` untouched, so no capture lands in
the gap and the reference's gap sentence stays true. A minimum above every band
leaves exactly one channel, and every discarded breakpoint is recorded. A minimum
equal to a declared breakpoint leaves that breakpoint's band intact and discards
nothing, because the boundary belongs to the wider band.

### Dependencies & integration

No new dependency. The pack's declared dependency surfaces are compared before
and after (T8).

## Tasks

### T1: The reference states the minimum

**Depends on:** none
**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/references/rendered-page-inspection.md

**Tests:** goal-based check for the rows. AC-0001 through AC-0004, AC-0006 and
AC-0007 are stated here and asserted in T2. AC-0021's sweep lands in T5, after
every surface it reaches has been edited, but four of its eight anchors are in
this file, and the `Done when` below is their one enumeration rather than a
second list that can drift from it. One of the four is the per-route floor stated
a second time in `## Required captures`, a paragraph the earlier anchor set
missed entirely because its wording is backticked and omits "where you declare".
`test_the_channel_sweep_reaches_every_file_that_names_a_channel` and
`test_every_shape_still_matches_the_shipped_site_it_was_written_for` are re-run
in-task: the first asserts set equality between the channel names harvested
across `.apm/**` and the two the reference declares, so a worked clamping example
in a three-cell table or prose in the `` `name` at <op> `` shape reds it.

**Approach:** add the two rule rows to the `## Channels` rule-row block and the
prose stating the derivation, the admissible value, and both recorded effects.
State the axis's reason without naming any surface outside the pack.

**Done when:** each of this file's four anchors sits in a **sentence** carrying
that anchor's conditioning literal, **and each still matches in this file**, so conditioning
rather than rephrasing is what discharges it and a rephrase cannot hide behind a
sibling carrier. The four are the fallback sentence, the band enumeration opener,
the eight-captures-per-route figure, and the n-plus-1 floor in the
required-captures paragraph, quoted exactly in AC-0021; the channel-name sweep is green without its shapes or
expected set being edited, and `fallback_channels` still returns exactly `narrow`
and `wide` with `test_fallback_channels_are_the_two_shipped_bands` green — that
control, not the sweep, is what reds a band row added to this file, because the
sweep derives its own expected set from these same rows; and
`channel_rules(read_rules())` returns eight keys including
`channel-minimum-derivation` and `channel-minimum-recorded`, and `unique_keyed`
rejects a duplicate key, run from a scratch probe. Not `capture_set_rules`: it
splits on `\n## Required captures\n` and cannot reach the `## Channels` section
at all, so a probe against it would pass with neither row present.

### T2: The reader derives and records the minimum

**Depends on:** T1
**Touches:** packs/frontend-engineering/tests/skills/frontend-engineering/frontend_engineering_rendered_page_rules.py, packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_capture_contract.py

`_rule_in_force`'s docstring classifies each row by what an *off* position means,
naming `channel-basis-recorded` as admitting none. AC-0016 puts
`channel-minimum-recorded` in that same group, so the docstring's enumeration is
part of this task's edit — left alone it ships a shorter list than the code
implements.

**Tests:** TDD in `test_rendered_page_capture_contract.py`, covering AC-0001,
AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0015, AC-0016, AC-0017,
AC-0019 and AC-0020. The
parametrized `test_every_required_rule_row_raises_when_deleted` already derives
its key set from `REQUIRED_RULE_ROWS`, so the two new rows arrive in it without a
second list, which discharges AC-0005 and nothing more.

AC-0015 and AC-0016 are the criteria that make the rows load-bearing, and their
mutation rewrites the row's **value cell** with the row still present. Deletion
cannot serve here: the walk proves every required row present before it runs, so
a deletion reds through the presence loop whether or not the filter or the
recorder ever consults the row. The module says this in the comment above
`REQUIRED_RULE_ROWS` — "Not all of them are read by the walk … the walk proves
them present". A value-cell mutation is the only fixture that separates *read*
from *present*.

**Approach:** add the minimum parameter and the filter to `required_channels`,
reading `channel-minimum-derivation` and refusing an unrecognised value the way
`channel_capture_width` refuses. Both the rule-token check **and** the minimum's
own value check go **before** the `if not declared_breakpoints` early return —
the value check especially, because the shipped breakpoint validation loop sits
after that return, so a minimum validated beside it would leave a fractional or
negative minimum unchecked on the no-breakpoints path, which is this delivery's
motivating surface. That is AC-0001's two-breakpoint-state obligation, and it is
the same fork AC-0015 and AC-0016 name. Neither check goes beside the
`channel-derivation` and `channel-boundary-belongs-to` checks, which sit after
the early return and never run on the fallback path. Then extend
`REQUIRED_RULE_ROWS["Channels"]` with both keys; add the two recording readers beside `channel_basis`, gated on
`channel-minimum-recorded` through `_rule_in_force`, without widening the basis
vocabulary.

**Done when:** `inspection_result` over the four-capture single-channel set at
1280 with a 1280 minimum returns `{"state": "completed", "verdict": "pass"}` and
`is_completed_inspection_result` returns `True`, while the same set with no
minimum stays `incomplete` and `is_completed_inspection_result` returns `False`
— AC-0020's own pair, not AC-0019's 480 pair; and
`test_the_required_rule_rows_match_what_the_tables_state` is green with eight
keys. The walk, not the helper, is the observable: every derivation criterion
asserts `required_channels` in isolation, so an implementation can satisfy all of
them while the walk still derives its bands without the minimum.

### T3: `SKILL.md` and the journey state the input

**Depends on:** T1
**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md, packs/frontend-engineering/JOURNEY.md, web/src/content/journeys/frontend-engineering.md, packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_capture_contract.py, packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_journey_promise.py

**Tests:** TDD for AC-0008, AC-0018 and AC-0009. AC-0018 asserts the § 5a
manifest row beside the shipped `test_manifest_viewports_field_records_channels`,
which passes after this delivery without mentioning the minimum. The row is also
pinned by `test_the_manifest_example_is_a_band_set_the_derivation_produces`,
which harvests every backticked predicate in it and compares the set to the
derivation's output — so the new values go in as bare numbers, and that control
is re-run as part of this task rather than discovered later. This task also
extends it to parse the row's stated minimum and pass it to `required_channels`;
today it calls the derivation with no minimum, so a stated minimum and the
predicates beside it can disagree with the control green. Of the channel-name sweep's three
shapes, `prose-declaration` and `snippet-name-field` carry § 5a as their live
site and `band-row` does not — its outer matches only a `## Channels` section, so
a three-cell table here is not harvested at all. The edit keeps the literal
`` `narrow` at ≤480 `` phrase, which is `prose-declaration`'s anchor in this
file. Anchors 3, 4, 5 and 8 of AC-0021's sweep are here, and anchors 4 and 5 currently
share one sentence — "That makes eight captures per route with the default bands,
and four times *n + 1* where you declare *n* breakpoints." Their conditioners
differ, so that sentence is split in two, one claim each, before either is
conditioned. Conditioning it in place cannot satisfy the criterion. Anchor 8 is the JS worked
example: its comment states the inference this delivery falsifies — no
breakpoints declared, therefore two channels — and its array captures at 480.
The block sits in its own paragraph unit, so conditioning the prose around it
does not reach it, and it cannot be deleted either: `snippet-name-field` anchors
on `const channels = [` at this exact site. So it must survive and be edited, and the
edit is the comment alone. The array keeps both entries at 480 and 1024: it is a
correct example *of a surface with no declared minimum*, and the comment is the
part that teaches the falsified inference. A one-entry array is not available
here — AC-0021's carrier map requires the anchor
`Two here because no breakpoints were declared` to keep matching in this file,
and removing a carrier is an amendment to that map rather than a green run, so
"Two here" and a single entry cannot both be true. The comment gains the
conditioning literal `no declared minimum` and a clause saying that declaring one
drops the bands below it. `name:` entries stay drawn from `narrow` and `wide`,
which is what `snippet-name-field` harvests into the set-equality sweep. AC-0009 goes in
`test_rendered_page_journey_promise.py`, the suite that already owns assertions
about what the journey promises; AC-0008 joins the § 5a assertions in
`test_rendered_page_capture_contract.py`.

**Approach:** § 5a gains the minimum beside the breakpoints input and states its
effect on the required set; the manifest `viewports` row gains the minimum and
the discarded breakpoints. `JOURNEY.md:12`'s `youProvide` gains the supported
minimum width — its two manifest inventories at `:84` and `:169` name the field
without stating what it holds, so the change does not reach them.

**Done when:** `FORCE=1 make build-self` leaves no projection diff, `:12` is the
only changed line in `packs/frontend-engineering/JOURNEY.md`, **and**
`python3 tools/build-site.py --journeys-only` has been run so that
`web/src/content/journeys/frontend-engineering.md:13` carries the same new
sentence. That command, not `build-self`, is what writes the web copy — the
`build-self` target never touches `web/`, so without it this clause would be
dischargeable only by the hand-edit the next sentence forbids. That second
file is committed, not ignored, and no shipped lint compares its `youProvide`
against the pack's — `lint-web-journey-parity.py` only counts skills and
`lint-pack-journeys.py` skips generated files for its ownership check — so a
stale web copy publishes the old input list with every gate green.

### T4: The how-to walks a single-channel surface

**Depends on:** T3
**Touches:** guides/frontend-engineering/how-to/inspect-the-rendered-page.md, packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_verdict.py

**Tests:** TDD for AC-0010 in `test_rendered_page_verdict.py`, the one pack module
that already reads the shipped how-to — a literal search over the guide for the
minimum input and the four-capture floor a single channel produces. Not a
goal-based check: the criterion names a test, and a mode that names a test is
TDD. The repository's documentation gates stay a separate well-formedness check.

**Approach:** the guide's capture section gains the minimum alongside the
breakpoints it already walks, and states the required set for a surface that
declares one. Both claims in that paragraph are edited, and because anchors 4
and 5 share one sentence here too, that sentence is split in two before either
clause is conditioned — their conditioning literals differ and one sentence
cannot carry both. The `n + 1` formula is
wrong whenever a minimum discards a declared breakpoint, and the eight-capture
figure is wrong too: "on the fallback bands" names the basis, which a minimum
leaves unchanged, not the set size, which it changes — a 1280-minimum surface is
on the fallback bands and needs four captures per route. An earlier draft of this
plan exempted the figure on that qualifier, which was the round-5 premise this
delivery itself falsifies.

**Done when:** the guide's links resolve under the repository's documentation
gates, and none of `Declare none and two apply`, `eight captures per route` or
`four times *n + 1* where you declare *n* breakpoints` sits in a **sentence** that
lacks that anchor's conditioning literal, and each still matches in this file. Two of them wrap
across a line break here, so the check normalizes whitespace within a unit after
splitting on blank lines, never before, and splits sentences only after that.

### T5: The harness expects the minimum

**Depends on:** T1, T3, T4
**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json, packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_shipped_content_limits.py, packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_reviewer_sight.py

**Tests:** TDD for AC-0011 in `test_rendered_page_reviewer_sight.py`, which
already parses this file for the channel-coverage assertion, plus AC-0021's
sweep in `test_rendered_page_shipped_content_limits.py`. The sweep lands here
because it is the last task to touch a surface it reaches; its seventh anchor is
this file's coverage expectation. The carrier-set assertion is the half that
keeps the sweep honest: a bare existential check lets a rephrase in one of three
carriers pass on the strength of the other two, while putting that carrier
outside the control's reach entirely.

**Approach:** the `rendered-page-inspection` case gains an assertion naming the
declared minimum and what it removes from the required set.

**Done when:** all eight AC-0021 anchors match in exactly the carrier files the
criterion lists and each sits in a sentence carrying its conditioning literal,
across `.apm/**` and the how-to, `catalogue lint --deep` and `catalogue verify` accept the harness, and
`FORCE=1 make build-self` leaves no projection diff.

### T6: The step is performed against a single-channel surface

**Depends on:** T2, T3
**Touches:** docs/specs/channel-minimum-width/notes/verification-ledger.md

**Tests:** visual / manual QA for AC-0014 — a recorded gesture. A passing
completeness test is not evidence that one channel was enough to judge the page.

**Approach:** run the capture against a real surface with a minimum declared,
route the images to a judge, and record the observations, the result state, the
verdict, the minimum in force, and any discarded breakpoint.

**Done when:** `docs/specs/channel-minimum-width/notes/verification-ledger.md`
carries the five values AC-0014 names.

### T7: The predecessor's superseded criteria carry their pointer

**Depends on:** T2
**Touches:** docs/specs/rendered-page-channel-axis/spec.md, tests/roster/test_channel_minimum_width_supersession.py

**Tests:** TDD for AC-0022 in `tests/roster/test_channel_minimum_width_supersession.py`,
copying all three cases of `tests/roster/test_rendered_page_channel_axis_supersession.py`
rather than inventing a shape — that file is the predecessor's own supersession
test, written for exactly this obligation one delivery earlier. Its pin is a
whole criterion block held in a module constant, and this one follows: each
superseded criterion's entire `- [x]` line, not a quoted fragment.

**Approach:** add a `Status:` line pointer to
`docs/specs/rendered-page-channel-axis/spec.md`, naming a successor per
superseded criterion as AC-0022 states it: AC-0002 and AC-0003 supersede that
spec's AC-0001, and AC-0002 alone supersedes its AC-0002, since the clamp cannot
change a channel count. Edit nothing else in that
file: its *Ask first* admits a `Status:`-line pointer and forbids editing a
frozen body, and both criteria stay present verbatim and still ticked. Depends on
T2 because the successor criteria must be real before anything points at them.

**Done when:** the pointer names both superseded criteria and both successors,
`git diff` against `docs/specs/rendered-page-channel-axis/spec.md` touches the
`Status:` line and nothing else, and all three roster cases pass — the pointer,
the two criteria's entire unedited lines, and the successors still holding the
obligation.

### T8: The release surface carries the change

**Depends on:** T1-T7
**Touches:** packs/frontend-engineering/pack.toml, packs/frontend-engineering/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md

**Tests:** goal-based check for AC-0012 and AC-0013 — compare all three version
pins, confirm the changelog entry is this pack's topmost release
heading and that `core` remains directly beneath `[Unreleased]`, run
`tools/test_build_site_routing.py` for the separation gate, and compare the
pack's declared dependency surfaces before and after.

**Approach:** the pack release pipeline in `packs/AGENTS.local.md`, in its stated
order. Diff `origin/main:packs/frontend-engineering/pack.toml` first so an
unpushed peer bump does not collide silently. Bump `pack.toml` and `plugin.json`
to the patch above it. Then run `FORCE=1 make build-self` to regenerate the root
`.claude-plugin/marketplace.json`, which carries this pack's version a third time
— it reads `0.2.4` today and is committed, so leaving it behind ships a
marketplace entry disagreeing with the pack it points at. Then lead a changelog
entry with the pack and that version, placed below the `core` block. Then decide
the `Highlights` disposition in the same step rather than leaving it to a
reviewer: this delivery changes what an adopter can do, so it takes a
`### Highlights` subsection of outcome-led bullets. Those bullets are what
publish at `/now/`, and the projection is a pure parser — an unwritten block is a
release the public page never mentions.

**Done when:** all three version pins read the same value, that value is one
patch above `origin/main`'s, the changelog entry carries either a
`### Highlights` subsection or the recorded none-verdict, `FORCE=1 make
build-self` leaves no projection diff, and `ruff check` is clean across the
changed Python.

## Rollout

- **Delivery:** big bang within the pack, behind a version bump. Reversible by
  reverting the pack content and the manifests together.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** the reference (T1) leads, because every other task
  reads it.
- **Adopter impact:** none for a surface that declares no minimum — the required
  set is unchanged. A surface that declares one gets a smaller required set, so
  no existing capture set becomes incomplete.

## Risks

- **The filter's drop condition is the load-bearing line.** A band is dropped on
  its upper bound alone, so an off-by-one there silently drops a band that
  should survive. The mutation for it is removing the filter, which the probe
  showed yields unsatisfiable bands. The two cases that catch an off-by-one are
  now AC-0002 fixtures rather than prose here: a band bounded on both sides
  lying wholly below the minimum, and a minimum equal to a band's bound.
- **`REQUIRED_RULE_ROWS` grows from six to eight.** Its equality control reds
  until both are added, which is the control working; the risk is reading that
  red as a defect rather than as the reminder it is.
- **`SKILL.md` headroom.** 899 of 1,000 body lines at `0.2.4`. T3 measures
  rather than assumes.

## Changelog

Ten shaping rounds and one adversarial round shaped this contract. Only the
decisions that still bind are recorded here; the round-by-round account is in the
commit history, where a superseded premise cannot be read as a current
instruction.

- **The clamp raises a bound and never lowers one.** Assigning the minimum would
  lower `wide >=1024` to `>=600` under a 600 minimum and demand a capture inside
  the fallback bands' deliberate 481-1023 gap. Raising leaves that band alone.
- **The filter runs after the derivation, not inside it**, so the shipped
  five-case derivation tests keep testing the derivation.
- **Two recorded fields, not a third basis value**, and the minimum is a
  run-level fact that never enters the per-capture `## Capture record` table.
- **The criteria pin the outermost observable.** `inspection_result` forwards to
  `evaluate_capture_set` forwards to `required_channels`; a minimum that stops
  short of the top is unreachable from what an adopter records. Every frame is
  asserted.
- **Value-cell mutation, not row deletion**, proves a rule row is read: the walk
  proves every required row present before it runs, so a deletion reds whether or
  not any code consults the row.
- **One superseded-claim sweep, not a clause per surface.** Eight carriers state
  some form of "two bands always apply" or the `n + 1` floor across four files,
  including a JS worked example. Per-surface clauses regenerated a new instance
  every round; an anchor-and-carrier map with a named conditioning literal is
  what a reviewer can inspect.
- **The predecessor is `Shipped` and takes a `Status:`-line pointer**, never a
  body edit, for the two criteria this delivery falsifies.
