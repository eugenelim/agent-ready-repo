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
empty value, because the record reader counts a field absent when its value is
`None` or empty.

`REQUIRED_RULE_ROWS["Channels"]` goes from six keys to eight. Its equality
control compares that constant against what `channel_rules` reads, so the two
move together or the control reds.

### Behavior & rules

`required_channels(markdown, declared_breakpoints, minimum=None)` derives bands
as today, then applies the filter. A band is dropped when its upper bound admits
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

**Tests:** goal-based check — this task ships content T2's assertions read.
AC-0001 through AC-0004 and AC-0006 and AC-0007 are stated here and asserted
there; nothing in this task asserts them itself.

**Approach:** add the two rule rows to the `## Channels` rule-row block and the
prose stating the derivation, the admissible value, and both recorded effects.
State the axis's reason without naming any surface outside the pack.

**Done when:** `channel_rules(read_rules())` returns eight keys including
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
AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0015, AC-0016 and
AC-0017. The
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

**Done when:** a repository-wide search for `required_channels` returns no caller
still passing two positional arguments where three are meaningful, and the
control `test_the_required_rule_rows_match_what_the_tables_state` is green with
eight keys.

### T3: `SKILL.md` and the journey state the input

**Depends on:** T1
**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md, packs/frontend-engineering/JOURNEY.md

**Tests:** TDD for AC-0008, AC-0018 and AC-0009. AC-0018 asserts the § 5a
manifest row beside the shipped `test_manifest_viewports_field_records_channels`,
which passes after this delivery without mentioning the minimum. AC-0009 goes in
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
declares one. The existing eight-capture floor becomes the floor for two
channels rather than the floor unconditionally.

**Done when:** the guide's links resolve under the repository's documentation
gates.

### T5: The harness expects the minimum

**Depends on:** T1
**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json

**Tests:** TDD for AC-0011 in `test_rendered_page_reviewer_sight.py`, which
already parses this file for the channel-coverage assertion.

**Approach:** the `rendered-page-inspection` case gains an assertion naming the
declared minimum and what it removes from the required set.

**Done when:** `catalogue lint --deep` and `catalogue verify` accept the harness
and `make build-self` leaves no projection diff.

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
