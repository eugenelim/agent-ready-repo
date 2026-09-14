# Plan: Rendered-page inspection channel axis

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
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

The spec's Objective and Assumptions own why the axis is breakpoint-derived and
why the fallback bands leave a dead zone. What is not recoverable from there:

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
| `channel-name-forbids` | Channels, rule rows | the AC-0012 token list |

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
AC-0001, AC-0002, AC-0003 and AC-0004 are stated here and asserted there; nothing
in this task asserts them itself.

**Approach:** add a `## Channels` section to the reference carrying the fallback
band table (name, lower bound, upper bound), and the breakpoint-derived rule, the
channel-basis recording rule, and the forbidden device-name tokens as two-cell
rule rows in the established shape.
Generalize the `every-captured-height-needs-the-pair` row and the prose stating
the required set. State the axis's reason without naming any surface outside the
pack.

**Done when:** the reference's new tables satisfy `table_rows`'s cell-count rule
and `unique_keyed`'s duplicate-key rule — no row is silently reshaped or dropped.

### T2: The rule reader derives the channel requirement from the reference

**Depends on:** T1
**Touches:** packs/frontend-engineering/tests/skills/frontend-engineering/frontend_engineering_rendered_page_rules.py

**Tests:** TDD, in `test_rendered_page_capture_contract.py`, covering AC-0001,
AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007 and AC-0008. The mutation that
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

**Done when:** all three `required_captures()` callers in the module read the
channel-keyed shape, with no caller left on the two-tuple.

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

**Done when:** each of the three suites builds a capture from separate width and
height arguments, and no call site of the `390 if height <= 600 else 1280` helper
remains anywhere in the pack's test tree.

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
`test_rendered_page_shipped_content_limits.py`. The guard **reads** the forbidden
token list from the reference rather than stating it, which is what makes AC-0012
delete-and-red the way AC-0008 requires of the other rows; stating it in the test
module would be the self-supplied quantifier the spec's `Always do` forbids. The
two existing guards in this module state their own vocabularies because theirs
describe repository policy, not a rule an adopter is held to.

**Approach:** restate the manifest `viewports` field as channels covered, given as
width predicates, in `SKILL.md` and in the journey's manifest inventory — AC-0011
reaches both. `SKILL.md`'s current example line names three devices and is inside
AC-0012's scope, so it is rewritten here rather than left.

**Done when:** `SKILL.md:783`'s three-device example line no longer names a
device, and the journey's manifest inventory states the same channel set as
`SKILL.md`'s.

### T6: The reviewer and the eval harness read the width axis

**Depends on:** T1
**Touches:** packs/frontend-engineering/.apm/agents/frontend-reviewer.md, packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json

**Tests:** TDD for AC-0013 and AC-0016, in `test_rendered_page_reviewer_sight.py`.
Scope the lens read to the lens section rather than the whole agent file, the way
that suite already scopes its reads; the whole-file read passes on the shared
output-rendering block. AC-0016 parses `evals/evals.json` in the same module.

**Approach:** extend lens 6 so the width joins the scroll position as a field the
reviewer must use, and recheck the "differ only by that field" sentence against
the widened axis. Add channel coverage to the harness's expected behaviours.

**Done when:** `catalogue lint --deep` and `catalogue verify` accept the edited
agent and harness, and `make build-self` leaves no projection diff for either.

### T7: The how-to walks a two-channel capture set

**Depends on:** T4
**Touches:** guides/frontend-engineering/how-to/inspect-the-rendered-page.md

**Tests:** goal-based check for AC-0018 — the guide is prose against a
non-repository surface, and the repository's documentation gates are the one-liner.

**Approach:** take the guide's worked walk across both channels and state what a
reader records when no breakpoints are declared.

**Done when:** the guide's links resolve and its walk names both channels and the
fallback gap, under the repository's documentation gates.

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
**Touches:** packs/frontend-engineering/pack.toml, packs/frontend-engineering/.claude-plugin/plugin.json, docs/product/changelog.md, docs/specs/rendered-page-visual-inspection/spec.md

**Tests:** AC-0019 is TDD in `test_rendered_page_capture_contract.py`, comparing
the frozen spec to its pre-change bytes so the body-unchanged half is observed
rather than assumed. AC-0014 and AC-0015 are a goal-based check — compare the two
manifests' version fields, confirm
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
