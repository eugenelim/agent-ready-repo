# Plan: Channel minimum width

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (runtime export boundary, pack test
  loader naming, version bump rule, no internal-governance citations in shipped
  content); `packs/frontend-engineering/AGENTS.md`;
  `docs/CONVENTIONS.md` § *Version bump rule* (what counts as an
  adapter-projected primitive).
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
- `make build-self` runs after every `.apm/` edit; `ruff check` before push.
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
| Execution observation | T6 |
| Release history | T7 |

T2 appears in no row: it ships the reader, which is code covered by the rule
layer's own row and reconstructible from the module and its tests.

## Design (LLD)

### Design decisions

**The filter runs after the derivation, not inside it.** Folding the minimum into
the band construction would make every existing derivation case a
minimum-of-`None` case and put two rules in one loop. Separating them means the
shipped five-case derivation tests keep testing the derivation.

**The clamp raises a bound and never lowers one.** A surviving band keeps its
upper bound, and its lower bound becomes the greater of the minimum and its own —
not the minimum outright. Assigning the minimum would lower `wide >=1024` to
`>=600` under a 600 minimum and demand a capture at 600, a width the reference
states satisfies neither fallback channel by deliberate design; raising leaves
that band alone and captures at 1024. Only the lowest survivor can be affected, and
the reason is the ordering, not a property of the bands above it: bands are
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
| `channel-minimum-derivation` | Channels, rule rows | drop-bands-below-clamp-lowest-survivor |
| `channel-minimum-recorded` | Channels, rule rows | `required` — the switch both recording readers consult, and AC-0016's mutation target |

A run with no minimum records the non-empty token `none-declared` rather than an
empty value, so that "no minimum was declared" is a stated value a reader can
assert on, distinct from a field nobody wrote. It is a run-level fact and does
not enter the per-capture `## Capture record` table, which *Never do* forbids.

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
required channels and is recorded on the § 5a manifest row, not in the result. A clamped band is renamed under the shipped convention, so a band
clamped to `>=1280 <1536` is `1280-to-1536` rather than `below-1536`; the walk
names the band in its incomplete report, so a stale name misdescribes what is
missing. Fallback bands keep the names their table rows give them. A band is dropped when its upper bound admits
no width at or above the minimum — `u <= minimum` for `<u`, `u < minimum` for
`<=u`, and never for an empty upper-bound cell, so the operator is load-bearing,
`<=480` survives a 480 minimum, and the unbounded top band survives every
minimum. The
lowest survivor's lower bound becomes `>=max(minimum, its own)`. Breakpoints
strictly below the minimum are collected as they are dropped, so the discarded
list is a by-product of the filter rather than a second pass; a breakpoint equal
to the minimum still bounds a surviving channel and is not discarded.

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
and after (T7).

## Tasks

### T1: The reference states the minimum

**Depends on:** none
**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/references/rendered-page-inspection.md

**Tests:** goal-based check for the rows. AC-0001 through AC-0004, AC-0006 and
AC-0007 are stated here and asserted in T2. AC-0021's sweep lands in T5, after
every surface it reaches has been edited, but four of its seven anchors are in
this file: the fallback sentence, the band enumeration, and the per-route floor
stated a second time in `## Required captures` — a paragraph the earlier
anchor set missed entirely, because its wording is backticked and omits "where
you declare".
`test_the_channel_sweep_reaches_every_file_that_names_a_channel` and
`test_every_shape_still_matches_the_shipped_site_it_was_written_for` are re-run
in-task: the first asserts set equality between the channel names harvested
across `.apm/**` and the two the reference declares, so a worked clamping example
in a three-cell table or prose in the `` `name` at <op> `` shape reds it.

**Approach:** add the two rule rows to the `## Channels` rule-row block and the
prose stating the derivation, the admissible value, and both recorded effects.
State the axis's reason without naming any surface outside the pack.

**Done when:** none of this file's four anchors sits in a **sentence** that fails
to name the minimum, **and each still matches in this file**, so conditioning
rather than rephrasing is what discharges it and a rephrase cannot hide behind a
sibling carrier. The four are the fallback sentence, the band enumeration opener,
the eight-captures-per-route figure, and the n-plus-1 floor in the
required-captures paragraph, quoted exactly in AC-0021; the channel-name sweep is green without its shapes or
expected set being edited; and
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
`channel_capture_width` refuses — and validating it **before** the
`if not declared_breakpoints` early return, not beside the `channel-derivation`
and `channel-boundary-belongs-to` checks that sit after it, which never run on
the fallback path; extend `REQUIRED_RULE_ROWS["Channels"]` with
both keys; add the two recording readers beside `channel_basis`, gated on
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
**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md, packs/frontend-engineering/JOURNEY.md

**Tests:** TDD for AC-0008, AC-0018 and AC-0009. AC-0018 asserts the § 5a
manifest row beside the shipped `test_manifest_viewports_field_records_channels`,
which passes after this delivery without mentioning the minimum. The row is also
pinned by `test_the_manifest_example_is_a_band_set_the_derivation_produces`,
which harvests every backticked predicate in it and compares the set to the
derivation's output — so the new values go in as bare numbers, and that control
is re-run as part of this task rather than discovered later. Of the channel-name sweep's three
shapes, `prose-declaration` and `snippet-name-field` carry § 5a as their live
site and `band-row` does not — its outer matches only a `## Channels` section, so
a three-cell table here is not harvested at all. The edit keeps the literal
`` `narrow` at ≤480 `` phrase, which is `prose-declaration`'s anchor in this
file. Anchors 3, 4, 5 and 8 of AC-0021's sweep are here. Anchor 8 is the JS worked
example: its comment states the inference this delivery falsifies — no
breakpoints declared, therefore two channels — and its array captures at 480.
The block sits in its own paragraph unit, so conditioning the prose around it
does not reach it, and it cannot be deleted either: `snippet-name-field` anchors
on `const channels = [` at this exact site. So it must survive and be edited. The
edit keeps a `const channels = [` array whose `name:` entries are drawn only from
`narrow` and `wide`, because that shape harvests those names into the
set-equality sweep. A single-channel form fits inside that constraint — a
1280-minimum fallback surface clamps `wide` to `>=1280` and keeps its table name,
so one entry named `wide` at width 1280 is correct under AC-0002 and AC-0003 and
safe for the name sweep. AC-0009 goes in
`test_rendered_page_journey_promise.py`, the suite that already owns assertions
about what the journey promises; AC-0008 joins the § 5a assertions in
`test_rendered_page_capture_contract.py`.

**Approach:** § 5a gains the minimum beside the breakpoints input and states its
effect on the required set; the manifest `viewports` row gains the minimum and
the discarded breakpoints. `JOURNEY.md:12`'s `youProvide` gains the supported
minimum width — its two manifest inventories at `:84` and `:169` name the field
without stating what it holds, so the change does not reach them.

**Done when:** `make build-self` leaves no projection diff and the only changed
line in `JOURNEY.md` is `:12`.

### T4: The how-to walks a single-channel surface

**Depends on:** T3
**Touches:** guides/frontend-engineering/how-to/inspect-the-rendered-page.md

**Tests:** goal-based check for AC-0010 — a search over the guide for the minimum
input and the four-capture floor a single channel produces. The repository's
documentation gates stay a separate well-formedness check.

**Approach:** the guide's capture section gains the minimum alongside the
breakpoints it already walks, and states the required set for a surface that
declares one. Both claims in that paragraph are edited. The `n + 1` formula is
wrong whenever a minimum discards a declared breakpoint, and the eight-capture
figure is wrong too: "on the fallback bands" names the basis, which a minimum
leaves unchanged, not the set size, which it changes — a 1280-minimum surface is
on the fallback bands and needs four captures per route. An earlier draft of this
plan exempted the figure on that qualifier, which was the round-5 premise this
delivery itself falsifies.

**Done when:** the guide's links resolve under the repository's documentation
gates, and none of `Declare none and two apply`, `eight captures per route` or
`four times *n + 1* where you declare *n* breakpoints` sits in a **sentence** that
fails to name the minimum, and each still matches in this file. Two of them wrap
across a line break here, so the check normalizes whitespace within a unit after
splitting on blank lines, never before, and splits sentences only after that.

### T5: The harness expects the minimum

**Depends on:** T1, T3, T4
**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json, packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_shipped_content_limits.py

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
criterion lists and sit only in sentences that name the minimum, across
`.apm/**` and the how-to, `catalogue lint --deep` and `catalogue verify` accept the harness, and
`make build-self` leaves no projection diff.

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

### T7: The release surface carries the change

**Depends on:** T1-T6
**Touches:** packs/frontend-engineering/pack.toml, packs/frontend-engineering/.claude-plugin/plugin.json, docs/product/changelog.md

**Tests:** goal-based check for AC-0012 and AC-0013 — compare the two manifests'
version fields, confirm the changelog entry is this pack's topmost release
heading and that `core` remains directly beneath `[Unreleased]`, run
`tools/test_build_site_routing.py` for the separation gate, and compare the
pack's declared dependency surfaces before and after.

**Approach:** bump both manifests to `0.2.5` and lead a changelog entry with the
pack and that version, placed below the `core` block. Diff
`origin/main:packs/frontend-engineering/pack.toml` first so an unpushed peer bump
does not collide silently.

**Done when:** `make build-self` leaves no projection diff and `ruff check` is
clean across the changed Python.

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

- 2026-09-14 — Drafted. Minimum settled as an optional adopter-declared positive
  whole number; derivation as drop-wholly-below then clamp-lowest-survivor;
  recording as two fields beside an unchanged two-value basis.
- 2026-09-14 — Shaping round 9. An eighth carrier, and the worst-placed one:
  § 5a's JS worked example comments "Two here because no breakpoints were
  declared" and captures at 480. It is the block an agent copies, it sits in its
  own paragraph unit so conditioning the surrounding prose misses it, no anchor
  reached it, and `snippet-name-field` anchors on it so it cannot be deleted —
  the delivery could have shipped with all 21 criteria green and that snippet
  telling the agent to capture below the supported width. Anchor 8 added, owned
  by T3 with the name-set constraint spelled out.
  Tightened the predicate from paragraph to sentence scope: naming the minimum
  anywhere in a paragraph is co-location, not conditioning, and appending one
  unrelated sentence was the cheapest way to discharge it — the exact edit shape
  rounds 5 and 6 produced. All eight anchors were walked to confirm each is
  conditionable at sentence scope before adopting the tightening.
  Replaced the per-anchor match count with a per-anchor carrier map. "At least
  once across the swept files" left the two anchors with three carriers each open
  to a rephrase in one of them, passing on the strength of the others while that
  carrier left the control's reach — the failure round 8 added the assertion to
  catch, surviving in weaker form. Map verified exact against the shipped tree:
  each of the eight anchors matches in precisely its listed files and no others.
  Confirmed by the reviewer: no anchor must be removed for the delivery to be
  correct, and the surface enumeration is otherwise clean.
- 2026-09-14 — Shaping round 8. Four findings, all on the new sweep. The anchor
  set missed a sixth carrier — the reference states the per-route floor again in
  `## Required captures`, backticked and without "where you declare", so no
  anchor matched it. The set is now seven anchors, including
  `eight captures per route`, which reaches all three carriers of that figure.
  Fixed the mechanization order: "normalizes whitespace first" would have erased
  every blank-line boundary and collapsed "the enclosing paragraph" to the whole
  file, making the check unfailable on every file this delivery touches; the
  criterion now splits into paragraph units first and normalizes within a unit.
  Added a per-anchor match assertion, without which an edit that rephrases a
  claim rather than conditioning it leaves the sweep matching zero anchors and
  reporting green — and the three demoted criteria had given up their conditional
  clauses on exactly that check. Struck the claim that "on the fallback bands"
  exempts the eight-capture figure: the qualifier names the basis, which a
  minimum leaves unchanged, and AC-0006 fixes that basis at `fallback` for a
  1280-minimum surface, which needs four captures per route and not eight. That
  premise came from round 5 and I carried it into AC-0010 and T4 without testing
  it against this delivery's own criteria.
- 2026-09-14 — Shaping round 7. Replaced the per-surface conditioning clauses
  with one sweep. Four shipped surfaces state some form of "two bands always
  apply" or the `n + 1` floor, and rounds 5, 6 and 7 each found the next instance
  after the previous was closed per-surface — the per-surface form was
  regenerating the defect. AC-0021 is now a superseded-claim sweep over five
  named anchors across `.apm/**` and the how-to, asserting each anchor's
  enclosing paragraph names the minimum; AC-0008, AC-0010 and AC-0011 drop back
  to presence clauses and point at it. Its reach is its anchor list, which is a
  thing a reviewer inspects. Two anchors that this delivery must condition wrap
  across a line break, so the check normalizes whitespace, as the shipped rate
  guard does. Dropped `4(n + 1)` from AC-0008: it is not shipped anywhere — the
  text is `four times *n + 1* where you declare *n* breakpoints` — so a test
  asserting its absence passed on the unedited file. Also dropped AC-0008's claim
  that AC-0010 covered the guide's copy of the sentence; it did not. Corrected
  the *Always do* channel-sweep entry, which over-stated the control's reach:
  `band-row` matches only inside a `## Channels` section, and
  `prose-declaration` needs the word *channel* in the paragraph and a
  lowercase-initial name. T5 now owns the sweep and depends on T1, T3 and T4.
- 2026-09-14 — Shaping round 6. AC-0008 was presence-only, so appending one
  sentence to § 5a discharged it while leaving two claims this delivery falsifies
  standing: "Declare none and two apply" and the `4(n + 1)` per-route floor. It
  now asserts the conditional form on the adapter-projected surface an agent
  performs the step from. AC-0021 added for the reference's own prose, which says
  both fallback bands always apply directly above where the new rule row lands —
  a contradiction no row assertion can see. Recorded the shipped channel-name
  sweep in *Always do* and in T1 and T3: it asserts set equality between the
  names harvested across `.apm/**` and the two the reference declares, so a
  worked clamping example or prose in the `` `name` at <op> `` shape reds it, and
  widening it would narrow the guard carrying the device-name prohibition.
  Realigned T2's `Done when` with AC-0020's pair — it had kept AC-0019's 480
  pairing.
- 2026-09-14 — Shaping round 5. Added AC-0020 for `inspection_result`, the
  outermost consumer, which forwards only the breakpoints — so every criterion
  could pass while the result an adopter records still read `incomplete` for a
  supported surface. Replaced AC-0019's paired fixture, which was byte-for-byte
  the shipped `test_a_single_channel_set_is_incomplete`, with a 480-minimum case,
  and added a declared-breakpoints fixture so the walk's pass-through is pinned
  on both forks. Made AC-0002's 480 fixture assert full name-bearing triples, the
  only input producing a clamped fallback band and so the only place the
  keeps-its-table-name rule can fail. Corrected AC-0010 and T4: the guide already
  conditions its eight-capture figure on the fallback bands, and the falsified
  sentence is `4(n + 1)`. Restated the `none-declared` ground here, which had
  kept round 3's wording after the spec corrected its own. (Entry written in
  round 6 — round 5 edited this plan without logging it.)
- 2026-09-14 — Shaping round 4. Added AC-0019: the completeness walk takes the
  minimum and honours it. Every derivation criterion asserted `required_channels`
  in isolation, so all 18 could pass while `evaluate_capture_set` — the function
  that returns complete or incomplete — derived its bands without the minimum and
  still reported a supported surface incomplete, which is the outcome the
  Objective promises. Paired fixtures with and without the minimum, so the
  criterion measures the minimum's effect rather than the walk's baseline.
  Widened AC-0017's sweep to a cross product, because on any input its siblings
  pin by exact equality disjointness is entailed and the criterion could not
  fail — a repair from round 3 that had instantiated the defect it closed.
  Corrected AC-0006's ground: it cited the per-capture record reader, which
  cannot read a run-level field, and an implementer making that ground true would
  have added the minimum to `## Capture record` and made every existing capture
  unusable; *Never do* now forbids it. Also pinned the clamped band's name, which
  reaches the walk's incomplete report, and the bare-number form the § 5a row
  needs so the shipped worked-example control stays green.
- 2026-09-14 — Shaping round 3. Derivation fixtures now compare full `(lower,
  upper)` band pairs instead of channel counts and capture widths: because the
  capture-width rule reads the lower bound first, a clamp that widened the
  clamped band's upper bound away was invisible to every width assertion, and
  would have made `>=480` and `>=1024` both admit 1024. AC-0017 asserts channel
  disjointness directly. AC-0015 and AC-0016 now cross the basis axis, because
  the derivation returns the fallback bands before validating its rule rows, so
  a check placed beside its siblings left the no-breakpoints path — the
  motivating surface — ungated. AC-0018 added for the § 5a manifest row, the
  surface that carries the record and which no reader criterion reaches. Named
  the `none-declared` token, since the record reader counts an empty value as an
  absent field. Replaced an unsound justification for the lowest-survivor
  invariant with the ordering argument; added the never-drop-an-unbounded-top-band
  case to the drop condition.
- 2026-09-14 — Shaping round 2. Corrected the clamp from an assignment to a
  raise: assigning the minimum lowered `wide >=1024` to `>=600` under a 600
  minimum and demanded a capture inside the fallback bands' deliberate 481–1023
  gap, contradicting shipped reference prose. AC-0003 now states the raise and
  carries the 600 and low-minimum fixtures. Added the inclusive-upper-bound
  fixture to AC-0002 (a filter ignoring the bound's operator wrongly dropped
  `<=480` under a 480 minimum) and the equality fixture to AC-0007, which had
  contradicted AC-0002 on `[768, 1024]` under a 768 minimum. Gave AC-0006
  expected values and an exact-equality basis assertion, closing a
  minimum-conditional basis suffix the inherited control cannot see. AC-0016 now
  binds per reader rather than per row. AC-0005 kept on the reviewer's KEEP
  verdict. Replaced two decaying line citations with test and section names.
- 2026-09-14 — Shaping round 1. Split AC-0005 into presence inheritance plus two
  new criteria (AC-0015, AC-0016) whose mutation edits a row's value cell,
  because the walk's presence loop reds on a deletion regardless of whether any
  code reads the row. Added the both-sides-bounded and equal-bound fixtures to
  AC-0002 and a mixed discarded-set fixture to AC-0007, each closing a case an
  unwanted implementation satisfied. Corrected T1's `Done when` from
  `capture_set_rules`, which cannot reach the `## Channels` section, to
  `channel_rules`. Named the frozen channel-axis spec under `Constrained by`.
