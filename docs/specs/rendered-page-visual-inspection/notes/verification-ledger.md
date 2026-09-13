# Verification ledger — rendered-page visual inspection

Execution observations for this feature. The approved `spec.md` and `plan.md`
hold obligations only; recording an observation here needs no amendment to
either.

## 2026-09-13 — approved baseline carried across a mode change

The spec and plan were authored and approved in a `spec-plan` run that reached
`DONE`. Implementation needs a `code`-mode run, and `work-loop` reads an existing
`engine-state.json` as a resume, so that run's state had to be reset and
re-initialised. The reset deletes `state.json`, which is where the approved
baseline lived. These are the values it held, recorded before the reset so the
re-seal can be checked against them rather than trusted.

| Field | Value |
| --- | --- |
| Run id (spec-plan run) | `65a3b79d-735c-406c-b079-b5e5612002c4` |
| Engine mode / state / last event | `spec-plan` / `DONE` / `plan-locked`, transition sequence 13, 2026-09-13T16:26:16Z |
| `plan_review_status` | `approved` |
| `approved_spec_hash` | `0b0bc534813b1ae32896bfcc5b37e1146c56afdd915e6356c172a337af642e0b` |
| `approved_plan_hash` | `b7ec25fe236a57c5112eef06ec496ae46a195985a6d791f7ccc201d3cb0c4b76` |

**Observation.** Immediately before the reset, both hashes were recomputed from
the files on disk with the cohort's own `sha256_canonical_contract` — the same
function `approve-plan` uses — and both reproduced the sealed values byte for
byte. The contracts had not drifted since approval, so re-running the G-plan
sequence after re-init re-seals the identical baseline. It is not a fresh
approval of different content, and it reopens neither the scope decision nor the
build-strategy decision.

Moving the spec's `**Status:**` from `Approved` to `Implementing` before the
first code change does not disturb the hash, because `canonical_contract`
normalizes the preamble status token to a placeholder. Ticking acceptance
criteria at ship time does disturb it, as intended, because it normalizes only
the *bracket contents* of a checkbox in the Acceptance Criteria section.

**Corrected 2026-09-13.** An earlier version of this paragraph said the hash
"covers the Acceptance Criteria section only". That is wrong, and it is the kind
of wrong that licenses a bad edit. `ac_section_only=True`
(`_loop_guards.py:739-795`) selects only *which checkboxes count as bookkeeping*
— a spec's progress marks live under Acceptance Criteria, whereas a checkbox
under `## Boundaries` is a `Never do` item the pin must protect. The hash itself
covers the **whole normalized file**. Any edit anywhere in `spec.md` moves it,
Testing Strategy included; that was proven by making such an edit and watching
the hash move off the sealed value.

**Authorisation.** The owner authorised the destructive reset pair
(`loop-cohort reset`, then `loop-engine reset`) and the re-init under
`--mode code` on 2026-09-13, after being shown the state above.

## 2026-09-13 — re-seal outcome

The `code`-mode run is `6bdc571b-85f8-4ece-8724-598567efb6a4`. `approve-plan`
re-derived `approved_spec_hash=0b0bc534813b…` and
`approved_plan_hash=b7ec25fe236a…` — identical to the values the spec-plan run
sealed, which is the check this ledger entry exists to make possible.

Pre-EXECUTE review was not re-run. It was discharged in the spec-plan run against
this same byte-identical content: `adversarial-reviewer` returned a direct clean
at round 5 (`.context/reviews/65a3b79d-735c-406c-b079-b5e5612002c4/5-pre-execute-adversarial-reviewer-raw.md`),
and `security-reviewer` reached an adjudicated clean at round 4, its single
Concern refuted against recorded owner decision 1
(`.../4-pre-execute-security-reviewer-adjudication.md`). Round 5 ran no security
pass because security was already clean at round 4.

`schedule` produced 7 waves: T0; T1; T2; T3 and T4; T5; T6; T7. The T3/T4 wave
reports `predicted-disjoint: unknown`, so those two run serially.

## 2026-09-13 — T0: the three measurements

T0 writes no content. It measures the three things that would have invalidated
the task breakdown if they were discovered mid-execution. All three were measured
against this tree, not recalled.

### 1. Where a new pack test suite must be registered to actually run

**Answer: a runner line in the root `Makefile`, inside the `run-test-suite`
define.** Creating `packs/frontend-engineering/tests/…` does not register it.

Evidence. `tools/lint-pack-test-boundary.py` runs eight checks; check 7 is
`every-suite-dir-has-a-runner` — "every skill test directory is named by a runner
or declared in `_NO_RUNNER` with a reason. Without this, 'which suites actually
run' has no living home and the next directory is unrun by default"
(`tools/lint-pack-test-boundary.py:37-39`). The files it accepts a runner from are
`_RUNNER_FILES` at `:1227` — exactly `Makefile`,
`.github/workflows/build-check.yml`,
`.github/workflows/catalogue-tooling-ci-gates.yml`, and
`.github/workflows/docs.yml`. Pack suites live in the `Makefile`: every existing
pack suite is an explicit `$(PYTHON) -m pytest packs/<pack>/tests/… -q` line in
the `run-test-suite` define (`Makefile:514-576`).

The Makefile states the rule directly at `:488-507`: a pack test suite gets its
own process by default, because suites share test basenames across skills and
pytest refuses duplicates. Grouped invocations are compatibility classes declared
in `tools/pack_test_compatibility.py`, and "**Adding a suite directory does not
add it to a class**" (`Makefile:501`).

`frontend-engineering` appears in neither `_NO_RUNNER`
(`tools/lint-pack-test-boundary.py:1259-1271`) nor
`tools/pack_test_compatibility.py` — searched both, zero hits. It also owns no
`tests/` directory today, unlike the 14 packs that do.

**Consequence for T1.** The new suite takes its own single-target `Makefile`
line. A single-directory invocation needs no compatibility-class declaration, so
`tools/pack_test_compatibility.py` stays untouched. This confirms the plan's task
breakdown; no amendment is needed.

### 2. Size headroom in `SKILL.md`

**Answer: `CAT-S003` governs, and the body is at 699 of a 1,000-line hard
ceiling — 301 body lines of headroom.**

The mechanism is `_check_body` in
`packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py:516-527`:
body above 1,000 lines is an error, above 500 a warning, counted on
`body.splitlines()` with frontmatter excluded. It runs under
`catalogue lint --deep`, not under ordinary `catalogue verify`.

Measured, not recalled — `catalogue lint --root . --deep --pack
frontend-engineering` reports:

```
[CAT-S003] WARN packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md
  body exceeds 500 lines (got 699); the spec recommends staying under 500
```

Exit code 0: one finding, warning tier. The pack is already above the 500-line
advisory and that is the pre-existing state, not something this delivery causes.
The blocking threshold is the one at 1,000. The sections T2, T3 and T4 add are
well inside 301 lines, so content placement is unaffected and no amendment is
needed.

No content hash pins this file: the only `SKILL.md` body mechanism `catalogue
lint --deep` applies is `CAT-S003` plus its absolute-path, install-path and
reference-depth line checks.

### 3. The pack's declared dependency surfaces

**Answer: five surfaces, four of them empty today.** This is the comparison set
T7's no-new-dependency check runs against.

| # | Surface | State before this delivery |
| --- | --- | --- |
| 1 | `packs/frontend-engineering/pack.toml` → `[pack.dependencies]` (`required`, `recommended`, `conflicts`; each entry `{catalogue, pack, version}` per `pack.schema.json`) | Table absent entirely |
| 2 | `packs/frontend-engineering/pack.toml` → `[pack.first-value].prerequisites` | `[]` |
| 3 | `packs/frontend-engineering/.claude-plugin/plugin.json` | Carries no dependency field — `name`, `version`, `description` only |
| 4 | Skill frontmatter `allowed-tools` and `metadata` (permitted by `skill.schema.json`, whose top-level properties are `allowed-tools`, `compatibility`, `description`, `license`, `metadata`, `name`) | Unused: all 9 skills declare only `name` and `description` |
| 5 | Python import surface under the pack | Empty — the pack ships no `.py` file and no `scripts/` directory |

Surfaces 4 and 5 were enumerated by search over the whole pack, not assumed.
Surface 5 is what makes the plan's "no script is added to the pack" decision
checkable: any new `.py` file under `packs/frontend-engineering/` is itself the
signal, independent of what it imports.

Note that `[pack.dependencies]` expresses pack-to-pack dependencies only. A
runtime tool the skill invokes — the pack already directs `npx pa11y` and `npx
html-validate` — is not declared in any manifest, which is why this delivery
adding no script and reusing the headless Chromium the accessibility step already
requires is the thing that keeps the criterion true.

**T0 verdict: no amendment required.** All three answers confirm the task
breakdown as written.

## 2026-09-13 — T1: rule tables, their suite, and the proof both can fail

Files: `packs/frontend-engineering/.apm/skills/frontend-engineering/references/rendered-page-inspection.md`
(new), `packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_inspection_rules.py`
(new, first suite in this pack's first test tree), and one runner line in
`Makefile`.

The severity scale is the pack's existing Blocker / Major / Minor / Note
(`SKILL.md:334`, `frontend-reviewer.md:153-163`) rather than a parallel one. The
criterion's word "blocking" is that scale's `Blocker`.

**Suite result:** 4 passed in 0.17s.

**The assertions were shown to fail, not assumed to.** Green on a rule table
proves little by itself, so each check was run against a mutated copy of the
reference. All six mutations went red and the unmutated control passed all three
checks:

| Mutation | Result |
| --- | --- |
| `clipped-at-rest-top` severity changed Blocker → Major | RED — "at-rest top clipping maps to 'Major'; the contract requires it to map to blocking" |
| `judge-supplied-severity` changed `discarded` → `honoured` | RED — judge's label reached the result |
| `severity-source` changed `finding-class` → `judge` | RED — "the reference no longer derives severity from the class" |
| `overflow` severity changed to `Critical`, outside the pack scale | RED — not one of the pack's severities |
| A duplicate `crowding` row added | RED — "a finding class appears more than once" |
| The `clipped-at-rest-top` class renamed away | RED — class absent from the mapping |

The judge-severity check is not hard-coded to the right answer: `resolve_severity`
reads the `Severity resolution` table and would return the judge's label if that
table stopped saying it is discarded. That is what mutation 2 demonstrates.

The plan's required mutation — a row holding a recognized class name with an
empty severity field — is a test in the suite itself, spelled out as a literal
row rather than derived from the mapping's own keys, so the case stays
representable.

**Registration was verified by removing it.** With the `Makefile` runner line
deleted, `tools/lint-pack-test-boundary.py` fails:

```
FAIL: packs/frontend-engineering/tests/skills/frontend-engineering holds a suite
that no runner names. Wire it, or add it to _NO_RUNNER with the reason — a suite
nobody runs must be declared, not discovered.
```

With the line present, all 8 checks pass and the run reports 15 packs owning
tests (up from 14) and 64 runner destinations. The suite is a single-directory
invocation, so it needed no `tools/pack_test_compatibility.py` class, exactly as
T0 predicted.

**Gates:** `catalogue lint --root . --deep --pack frontend-engineering` exit 0
(one finding: the pre-existing `CAT-S003` 699-line warning, unchanged — this task
did not touch `SKILL.md`); `catalogue verify --root .` exit 0.

## 2026-09-13 — T2: capture set, capture record, and the step split

The rule tables gained four sections — `Required captures`, `Capture record`,
`Judgement request`, `Step separation` — and `SKILL.md` gained section 5, the
capture and judgement steps written against them. The shared table readers moved
into `frontend_engineering_rendered_page_rules.py`, named for pack and skill per
`packs/AGENTS.md` § *Writing pack tests*, so neither suite imports the other
under a bare name.

**Suite result:** 21 passed for the capture contract, 25 passed for the directory
(0.23s). The plan's eleven assertions are covered; the case count is higher
because the scroll-position and missing-field checks are parametrized rather than
written once.

The scroll-position check runs at **both** heights, not one. Driving it at a
single height would leave the rule for the other height unasserted.

**Nine mutations of the reference, all detected:**

| Mutation | Detected by |
| --- | --- |
| `short-at-rest` height bound `<=600` → `<=2000` | A tall-only set stopped reading as missing the short capture |
| `tall-at-rest` bound `>=900` → `>=100` | A short-only set stopped reading as missing the tall capture |
| `short-scrolled` scroll `>0` → `>=0` | A set with no scrolled capture stopped reading as incomplete |
| `tall-scrolled` row deleted | Absent from the required-capture set |
| `Capture record` → `scroll-position` demoted to `no` | Four-field check |
| `Judgement request` → `scroll-position` demoted to `no` | Four-field check |
| `capture-step-invokes-judge` → `yes` | Step-separation check |
| `judgement-step-produces-captures` → `yes` | Step-separation check |
| Record with `route` removed | Yields no finding, and is reported unusable |

Control: the unmutated reference evaluates a complete set as `complete` with
nothing missing, and both field tables carry all four fields.

**Gates:** `catalogue lint --root . --deep --pack frontend-engineering` exit 0.
`CAT-S003` moved 699 → **773** body lines as section 5 landed; the hard ceiling is
1,000, so **227 lines of headroom remain** for T3, T4 and T7. Still the warn tier,
which the pack was already in before this delivery.

## 2026-09-13 — T3: the manifest field and the seven result states

The reference gained `Result states`, `Result surfaces` and `Observations
field`. `SKILL.md` gained section 5c and the `inspection observations` row in the
evidence-manifest table.

**Suite result:** 19 passed for result recording, 44 for the directory (0.57s).

**The manifest's own field counts were stale and are now correct.** The table
said "all 11 must be present" and "2 more, 13 in total"; adding a twelfth field
made both false. They now read 12 and 14, and a test asserts the heading count
equals the number of rows, so the next person to add a field cannot leave the
surface contradicting itself.

**Eleven mutations, all detected:**

| Mutation | Detected by |
| --- | --- |
| `inspection observations` renamed out of the manifest | Field-presence check |
| Field-count heading left at 11 while the table holds 12 | Count-matches-table check |
| `filenames-only` `rejected` → `accepted` | A bare filename list started passing |
| `skipped-no-browser` marked a completed inspection | Skip-distinguishability check |
| `failed-navigation` marked completed | Failure check |
| `failed-capture` marked completed | Failure check |
| `failed-judgement` marked completed | Failure check |
| `incomplete` also marked completed | Exactly-one-pass-state check |
| `step-output` stops carrying the result state | Three-surface check |
| `acceptance-gate-input` row deleted | Three-surface check |
| Skip row stops naming the missing capability | Capability-naming check |

**One check was rewritten after it failed for the wrong reason.** It first
asserted a sentence from `SKILL.md` ("no Chromium reachable"), which broke
because the prose wraps across lines. That is the brittleness the plan's design
decision exists to avoid, so the check now reads the `skipped-no-browser` row in
both the reference and the skill's result table. Rows do not rewrap; sentences do.

### Self-host produced no diff, and that is the correct outcome

`catalogue self-host --root . --write` returned ok with an empty `git diff`.
This is not a skipped step: **`frontend-engineering` has no in-repo projection.**
Neither `.claude/skills/frontend-engineering/` nor
`.agents/skills/frontend-engineering/` exists — this repository self-hosts only
the core, catalogue-curation and governance-extras skills, 26 in total. A pack
with no projection has nothing for self-host to regenerate.

So for this pack the projection gates that carry weight are `catalogue lint
--deep` and `catalogue verify`, both green, not a self-host diff. T4's identical
Done-when clause resolves the same way.

Recorded because it is a trap: a zero diff from self-host reads like the command
did nothing, and the wrong conclusion is to go looking for the projection that
failed to update.

`catalogue self-host --write` also **refuses a dirty tree** ("working tree is
dirty — refusing to write. Pass --force to override"), so T0–T3 were committed
first, at `05d5ca2fa`.

**Gates:** deep lint exit 0 (`CAT-S003` now **800** body lines, 200 of headroom
left); `catalogue verify --root .` ok.

## 2026-09-13 — T4: the judge boundary

The reference gained `Route recording`, `Judging captured content` and
`Capturing a signed-in or sensitive view`. `SKILL.md` gained the matching clauses
in sections 5a and 5b.

**Suite result:** 62 passed for the directory (0.26s).

**A check that could not fail was found and fixed.** The first version asserted
`"data, not instruction authority"` against the whole of `SKILL.md`. It passed —
but not because the judgement section said it. `SKILL.md` carries the shared
output-rendering block, which already contains that exact phrase at line 32. The
check would have stayed green with the new clause deleted outright.

The mutation battery is what caught it: mutation 9 came back GREEN when every
other mutation went red. The fix is `inspection_section()`, which narrows the
haystack to section 5 — 6,250 characters of the file's 46,880. All three
skill-prose checks are now scoped to it, and all three go red when their clause
is removed from the section while the boilerplate stays put.

**Route exclusion is checked independently for each part.** `recorded_route`
splits path, query and fragment and reassembles only what the table keeps.
Stripping one on the way to the other would have dropped the fragment as a side
effect of the query rule, and a mutation re-admitting it would have gone
unnoticed. Verified: flipping `route-query-string` alone leaks
`/orders/2481?token=abc`; flipping `route-fragment` alone leaks
`/orders/2481#receipt`.

**Eleven mutations, all detected** (after the fix above):

| Mutation | Detected by |
| --- | --- |
| `route-query-string` `excluded` → `kept` | Recorded route retained `?token=abc` |
| `route-fragment` `excluded` → `kept` | Recorded route retained `#receipt` |
| Either flip, on the judgement-request route | Asserted separately from the recorded route |
| `route-source` → `discovered` | Adopter-supplied check |
| `captured-content-instruction-authority` → `full` | Authority check |
| `captured-content` → `trusted` | Untrusted-evidence check |
| `sensitive-view-capture` → `automatic` | Adopter-decision check |
| `The page as rendered` exposure row deleted | Exposure-named check |
| Untrusted-data clause cut from section 5 | Scoped skill check |
| Adopter-routes sentence cut from section 5 | Scoped skill check |
| Adopter's-decision sentence cut from section 5 | Scoped skill check |

Control: the five leaky routes strip to their paths, three already-clean routes
pass through unchanged (the rule removes secrets without mangling ordinary
routes), and every rule row reads as authored.

**Gates:** deep lint exit 0 (`CAT-S003` **822** body lines, 178 of headroom left
for T7); `catalogue verify --root .` ok; `lint-pack-test-boundary` 8 of 8. The
self-host clause in this task's Done-when resolves as recorded under T3 — this
pack has no in-repo projection.

## 2026-09-13 — T5: the journey promise, and a stale projection that hid a failure

`JOURNEY.md` step 4 now names the rendered-page inspection, its observations
output, and its named skip; the `accept-frontend-evidence` gate's `whatToCheck`
now names the `inspection observations` field and what does not satisfy it.

**Suite result:** 71 passed for the directory (0.31s).

**Written red first.** The guard suite was authored before the journey was
touched: its five skip-cost pins passed (confirming the baseline was captured
correctly) and its four promise assertions failed. Both halves moved for the
right reason.

### The skip cost is byte-pinned, and the pin holds

The spec lists "changing what a named skip costs at the
`accept-frontend-evidence` gate" under `Ask first`, and **nothing else reads that
text** — not `catalogue verify`, not the journey lints. Without a pin the
boundary could be crossed with no signal. Four strings are pinned byte-exact: the
gate's `whatGoodLooksLike`, `whatBadLooksLike`, `consequence`, and the
known-exceptions clause, plus the `unverified items` manifest row.

All four mutations go red (rewording the consequence, rewording
`whatGoodLooksLike`, cutting the known-exceptions clause, removing the gate
itself), and the unmutated control passes. The pin is deliberately brittle: a
reworded line is a failure by design, and the response is to get the decision
made and then update the constant.

This delivery makes a skip **visible**. It does not make it cost more.

### A stale web projection hid a real lint failure

`web/src/content/journeys/frontend-engineering.md` is generated from the pack's
`JOURNEY.md` by `tools/build-site.py --journeys-only`. After editing the pack
journey, all three journey lints passed — **against the stale projection**.

Regenerating turned one red immediately:

```
lint-journey-contract: structural violations:
  frontend-engineering.md: stage '### 4. Run verification gates':
  unknown label `Named skip` (not in the fixed set)
```

`tools/lint-journey-contract.py:45-52` holds a closed label set — `You provide`,
`<Actor> does`, `You do`, `You decide`, `Output`, `State` — in fixed order. The
`**Named skip:**` bullet was a new label and not permitted. The named-skip text
now sits inside `Output`, which is where a result belongs anyway.

Note that `lint-web-journey-parity.py` would never have caught this: it compares
**skill counts only**, not bodies, so a body-level drift between a pack journey
and its web projection is invisible to it.

The sequence that matters: edit `packs/<pack>/JOURNEY.md` → run
`tools/build-site.py --journeys-only` → *then* run the journey lints. Linting
before regenerating grades the old file.

**Gates:** `lint-journey-contract` all 20 conform; `lint-pack-journeys` all 14
valid; `lint-web-journey-parity` all 20 in parity; `catalogue verify --root .`
ok; 71 tests pass.

## 2026-09-13 — T6: the end-to-end run found a defect the unit tests could not

This is the manual-QA observation the spec's Testing Strategy requires, and the
reason it requires one.

### The run

8 fixtures × 4 required capture states = **32 captures**, driven with headless
Chromium through Playwright against `file://` URLs. The capture step produced the
images and their records and never called a judge; the judgement step then read a
capture set it had not produced. Both halves of the separability rule held in
practice, not just in the tables.

**Detection — 4 of 4 defect fixtures produced a finding naming their recorded
defect:**

| Fixture | Recorded defect | Observed at short-at-rest |
| --- | --- | --- |
| defect-occlusion.html | occlusion | The blue announcement bar sits across the h1, cutting "scales with you" in half — unreadable |
| defect-overflow.html | overflow | `ws-8f41c2ae-…` runs past the right edge of its card and off the viewport; the end is unreadable |
| defect-clipped-at-rest-top.html | clipped-at-rest-top | The page opens on "A receipt is on its way…" — the h1 and order number are above the content area at rest |
| defect-target-undersized.html | target-undersized | The three dismiss controls render at roughly 10 CSS px square |

**False positives — 0 of 4 known-clean fixtures produced a finding.** Denominator
4, matching the shipped known-clean set. `clean-nav.html` was the one to watch: it
has a sticky header, the same structure that makes `defect-occlusion.html` fail,
and its content area is offset by the header's own height, so nothing is covered
at rest or scrolled.

**The configuration this was measured with**, because the shipped procedure's
step 6 requires the result be written next to it, and a count without it cannot
be reproduced or compared:

| | |
| --- | --- |
| Judge | Claude Opus 5 (`claude-opus-5`), reading each capture directly as an image, one capture per judgement, with the capture's recorded fields stated alongside it |
| Browser | Chromium 149.0.7827.55, headless, driven by Playwright 1.61.0 (Python) |
| Short viewport | 390 × 600 CSS px, at scroll 0 and scroll 400 |
| Tall viewport | 1280 × 900 CSS px, at scroll 0 and scroll 400 |
| Platform | macOS, Darwin 25.5.0, arm64 |
| Fixture source | `file://` URLs, the shipped set unchanged |

These counts are a local measurement with that judge and those viewport sizes.
They are not a rate, they do not transfer to a different judge, and they are not
published in any shipped pack content.

### The defect the run exposed

**17 of the 32 captures could not reach a non-zero scroll position**, because the
fixture is shorter than the viewport and there is nothing to scroll to. Affected:
all four known-clean fixtures at the tall height, three of the four defect
fixtures, and `clean-form.html` at both heights.

Under the `Required captures` rule as T2 shipped it, `*-scrolled` requires
`scroll-position > 0`, so **every one of those pages is permanently
`incomplete`** and can never satisfy a completed inspection.

The unit suite did not catch this and could not have: its `complete_set()` fixture
asserts `scroll-position: 800` unconditionally, so nothing in it modelled a page
that cannot scroll. A passing test for the record shape is not evidence that the
inspection works — which is exactly what the spec's Testing Strategy says about
this step.

The consequence is not confined to these fixtures. Adopters routinely inspect
surfaces shorter than a viewport — a sign-in form, a 404, a settings panel — and
the shipped contract would mark each one incomplete forever.

### Owner decision and amendment

Surfaced to the owner with the numbers above. **Authorised 2026-09-13:** amend the
acceptance criterion so that a height at which the page does not scroll satisfies
the scrolled requirement, recorded explicitly rather than inferred.

- The capture record gains `page-scrollable`.
- The `*-scrolled` required captures read `>0, or page-scrollable: no`.
- The AC gains "…or the page is recorded as not scrollable at that height."

A page with nothing below the fold has no scrolled view to inspect, so the
requirement is vacuously satisfied rather than unmeetable. Recording it keeps the
distinction visible: "did not scroll because the page does not scroll" is a
different fact from "nobody scrolled", and only the first is acceptable.

Declined alternatives, for the record: making the fixtures taller alone would
have hidden the defect behind a kit that no longer exercises it, and deferring it
would have shipped a contract that fails on ordinary short pages.

Completed-task evidence at the point of amendment: T0–T3 at commit `05d5ca2fa`,
T4–T5 at commit `efa7dec06`.

The amendment was fired as `contract-amendment` (seq 16), which pinned the prior
approved contract and the completed task sections, then the ordinary sequence
re-ran: `spec-ready`, `reviewers-clean`, `spec-approved`, `plan-approved`,
`approve-plan`, `schedule`, `plan-locked`. The re-sealed baseline is
`approved_spec_hash=86287a46196b…`, `approved_plan_hash=4337e364778b…` — different
from the pre-amendment values, as it should be, because the contract changed.
Rescheduling emitted **only the unfinished tasks**: T6, T6a, T7. T0–T5 stayed
completed and their sections were not edited; T6a is the dependency-ordered
correction rather than a rewrite of T2.

### The guide destination decision

The spec carried this as an unresolved closeout blocker to be decided in T6
against the tree as it then stands. Decided: **a new how-to page**,
`guides/frontend-engineering/how-to/inspect-the-rendered-page.md`, with a row in
the guide index.

The tree holds two how-to pages (`run-an-audit`, `page-screen-contract`), two
reference pages and one tutorial, and the index is keyed by task rather than by
skill. The inspection is its own task with its own procedure and a measurement
step. Folding it into `run-an-audit` would bury a step that has to be findable on
its own, and the reference pages are lookup surfaces, not walkthroughs. A new
how-to is what the tree's own shape asks for.

Guide gates: `lint-guides-no-repo-only-refs` OK, `lint-guide-titles` OK across
230 files, `check-guide-index` OK across 21 active packs, and the 40 guide
authoring/index tests pass. `check-guidebook-walk` needs `build/docs` and belongs
to the site build, not to a local run.

## 2026-09-13 — T6a: the amendment implemented, and the run repeated

Rule tables: the two `*-scrolled` required captures now read `>0, or
page-scrollable: no`, and `page-scrollable` joined both the capture record and
the judgement request.

**Why it is on the judgement request too.** It is not only a completeness field.
On a page that does not scroll, content meeting the bottom edge is cut off; on a
page that does, the same pixels mean the content continues below the fold. Those
are the same picture, so the judge needs the value to tell them apart. The four
fields the criterion names are still all stated.

**The branch is recorded, never inferred.** `_scroll_rule_met` honours the value
written on the capture and refuses to read it off a scroll position of 0, because
a page nobody scrolled sits at 0 too.

**Suite result:** 168 passed (0.48s), including 9 new cases for the amendment.

**Five mutations, all detected:**

| Mutation | Result |
| --- | --- |
| `page-scrollable: no` branch removed from `short-scrolled` | The original defect returns — unscrollable page reads `incomplete` |
| Same branch removed from `tall-scrolled` | Same, at the height where most of the run's misses were |
| `page-scrollable` dropped from the capture record | Field no longer required |
| A **scrollable** page with its scrolled captures missing | Stays `incomplete` — the amendment excuses the unscrollable case only |
| `page-scrollable` left unrecorded on an unscrollable page | Stays `incomplete` — not inferred from scroll 0 |

### The end-to-end run, repeated against the amended rule

| Fixture | Captures | page-scrollable | Result |
| --- | --- | --- | --- |
| clean-article.html | 3 | no/yes | complete |
| clean-card-grid.html | 3 | no/yes | complete |
| clean-form.html | 2 | no | complete |
| clean-nav.html | 3 | no/yes | complete |
| defect-clipped-at-rest-top.html | 2 | no | complete |
| defect-occlusion.html | 3 | no/yes | complete |
| defect-overflow.html | 2 | no | complete |
| defect-target-undersized.html | 2 | no | complete |

**8 of 8 fixtures reach a complete capture set**, against 0 of 8 before the
amendment. Total captures dropped 32 → 20, because a capture that cannot exist is
no longer demanded.

The measurement procedure's arithmetic moved with it: it now states **at most**
8 × 4 = 32 captures and explains why a fixture may produce fewer, rather than
asserting a flat 32 that the shipped fixtures contradict. The test that checks
the arithmetic was updated to match and to require the explanation, so the
procedure cannot silently drift back to a number that is wrong.

## 2026-09-13 — T7: release surface, and the dependency-surface comparison

### The no-new-dependency check, against T0's enumerated surfaces

Each of the five surfaces T0 named was re-measured, not assumed:

| # | Surface | Before | After |
| --- | --- | --- | --- |
| 1 | `pack.toml` → `[pack.dependencies]` | Table absent | Table absent — 0 occurrences |
| 2 | `pack.toml` → `[pack.first-value].prerequisites` | `[]` | `[]` |
| 3 | `.claude-plugin/plugin.json` | No dependency field | No dependency field |
| 4 | Skill frontmatter `allowed-tools` / `metadata` | Unused across all 9 skills | Unused — still only `name` and `description` |
| 5 | Shipped Python import surface | Empty | Empty — **0** `.py` files and **0** `scripts/` directories under `.apm/` |

**No newly required dependency.**

Surface 5 needed care rather than a raw count. `find packs/frontend-engineering
-name '*.py'` now returns 9 files, which looks like a change until you see they
are all under `tests/`, outside the `.apm/` runtime export boundary and therefore
not shipped. The correct measurement is scoped to `.apm/`, and there it is still
zero. Their imports are `re`, `pathlib`, `__future__`, the local sibling module,
and `pytest` — already the repository's test runner, not a new dependency.

This is what the plan's "no script is added to the pack" decision bought: the
check is a file-existence question under one directory rather than a judgement
about what some script imports.

### Release surface

`pack.toml` and `.claude-plugin/plugin.json` both moved 0.2.2 → **0.2.3**, patch
per `packs/AGENTS.md` § *Version bump rule* — changed content, and no new
primitive, since this adds references and fixtures to an existing skill rather
than a new skill, agent, command or hook. `origin/main` was confirmed at 0.2.2
first, so the bump does not collide with an unpushed one.

The changelog entry is free-standing directly beneath `[Unreleased]`, not nested
inside it, and carries a `### Highlights` block because the release changes what
an adopter can do. The `/now/` projection was therefore regenerated in the same
change: `web/src/lib/now-highlights.generated.json` moved from 138 released
highlights in 98 groups to **141 in 99**, and
`test_build_site_routing.py -k now` passes, which is the check that fails on a
changelog edit committed without it.

Eval harness: three trigger queries added to `eval_queries.json` (23 → 26) and a
`rendered-page-inspection` behavioural eval added to `evals.json` (1 → 2 evals),
with seven assertions covering the capture set, the recorded fields, route
exclusion, severity derivation, the manifest entry and the named skip.

### Correcting the T3 self-host note

T3 recorded that this pack has no in-repo projection. That is true of **skill**
projections and remains the reason the earlier self-host runs produced no diff.
It is not true in general: self-host after the version bump rewrote
`.claude-plugin/marketplace.json`, which carries each pack's version. So the pack
does have exactly one in-repo projection, and it is the one a version bump
touches. A content-only change leaves it alone; a release does not.

**Gates:** `catalogue lint --root . --deep` exit 0 across the catalogue (70
findings, all pre-existing warnings in other packs); for this pack, one finding —
`CAT-S003` at **829** body lines against the 1,000 hard ceiling, **171 of
headroom left**, in the warn tier the pack already occupied before this delivery.
`catalogue verify --root .` ok. `lint-pack-test-boundary` 8 of 8. Suite: 168
passed in 0.47s.

## 2026-09-13 — Review round 1: 9 findings, 6 sustained, 3 refuted

Reviewer: Codex (`codex-cli` 0.154.0), read-only, against the merged diff.
Artifacts at `.context/reviews/6bdc571b-85f8-4ece-8724-598567efb6a4/`.

Three were refuted on current evidence: that the unscrollable branch trusts a
forgeable string (it accepts a literal recorded `no` only, and `yes`/`YES`/
`true`/`maybe`/`""` are already pinned as leaving the set incomplete); that the
reference's "all four of these" contradicts the amendment (it names four capture
*requirements*, not four images, as the paragraph below it states); and that the
portability guard should cover `packs/AGENTS.md` (the Testing Strategy fixes the
guard's reach as the stated identifier set, and the criterion scopes it to sites,
routes, build directory and test harness).

### The Blocker was real, and reproduced before fixing

`evaluate_capture_set` ran a flat `any()` over every capture with no route key.
Two cases, both confirmed returning `("complete", [])` before the fix:

- `/a` captured only at the short height and `/b` only at the tall height. The
  set looks complete because both bands appear somewhere, though **neither route
  was inspected at both**. The criterion says "for each inspected route".
- A 750px at-rest capture with no scrolled counterpart. The old rule walked only
  the four table rows, so a height the adopter actually captured was never
  checked. The criterion says "for each viewport height captured".

Completeness is now evaluated per route, and within each route at every distinct
height that route captured — not only the two named bands. Both cases now fail,
and four green paths hold: one complete route, two complete routes, an
unscrollable short page, and an extra height once it is paired. An empty capture
set is incomplete, so the rule is true on empty state.

### The two Nits were both controls that could not fail

Finding 8 is the sharper lesson. The `or True` line was removed earlier in the
session — or so the ledger would have said. The edit was applied to the wrong
file's contents by a patch script operating on the wrong variable, so it
silently no-opped and the assertion stayed. **A patch that reports success is not
evidence the edit landed**; only re-reading the target is. The reviewer caught
what the session's own account had already written off.

Finding 9 removed two assertions comparing module constants to each other, and
re-derived the failure-family distinctness from the shipped `Result states`
table rather than from a list this module builds out of distinct literals.

### The rate guard now tolerates punctuation, in one direction only

Finding 5 was sustained narrowly: the vocabulary's reach is accepted as-is, but a
miss on a term *inside* it is a defect. `The false-positive rate, measured
locally, is 4%` escaped a `\s+`-only window.

Widening both directions immediately produced a **false positive on real shipped
content**: the measurement reference's own "Known-clean fixtures — 4" heading
sits six words above "the false-positive rate is measured over", and that 4 is a
count. So the window is now asymmetric — wide after a term, tight before it,
since a rate is normally written term-first and "4% false-positive rate" needs
only a tight before-window. Ten planted rates are caught, including punctuated,
parenthesised, em-dashed, colon and number-first forms; four legitimate
count-bearing sentences still pass.

### Finding 7: the measurement is now reproducible

The shipped procedure's step 6 requires a result be written next to the judge and
viewport sizes it was measured with, and the ledger said only "this judge and
these viewport sizes". The T6 entry above now names the judge, the browser build,
the Playwright version, both viewport dimensions with their scroll offsets, and
the platform.

**Suite after fixes:** 176 passed.

## 2026-09-13 — T0's registration answer was incomplete: a second surface

Running the wider repository guards after the review fixes turned one red:

```
FAILED tools/test_local_ci_shared_test_deduplication.py::
  test_effective_make_recipes_apply_exact_composition_and_fail_on_mutation
  — approved standalone command plan drift
```

**T0 named one registration surface; there are two.** The `Makefile` runner line
is what makes a suite *run*, and `tools/lint-pack-test-boundary.py` check 7 is
what refuses a suite with no runner. But
`tools/test_local_ci_shared_test_deduplication.py` additionally pins the
**effective command plan** of `make test` behind two digests,
`APPROVED_STANDALONE_PLAN_DIGEST` and `APPROVED_COMPOSED_PLAN_DIGEST`. Adding a
runner line changes that plan, so the digests must be re-pinned in the same
change. Nothing in the Makefile's own commentary points at this file, which is
why T0's bounded search over the Makefile and the boundary lint did not reach it.

This is a genuine gap in T0's answer rather than a change of circumstance, and it
would have been cheaper to find at T0 than at review time. The general shape: a
"where does this get registered" question is not closed by finding the surface
that *executes* the thing; something may also *pin* it.

### The re-pin followed the protocol the file itself states

That constants block requires two dispositions, and both were produced through
`_effective_composition_errors` rather than a hand-rolled recomputation:

1. **Sole cause.** The same path run against this worktree's `Makefile` and
   against `05d5ca2fa~1:Makefile` moves each plan by exactly one line —
   standalone 62 → 63, composed 61 → 62 — inserting
   `<PYTHON> -m pytest packs/frontend-engineering/tests/skills/frontend-engineering/ -q`
   at index 31 in both. Deleting that single line from the new plan reproduces
   the old plan element for element, and it occurs exactly once. Every later
   index differs only by the shift; nothing was reordered or dropped.
2. **Prior pins were current.** With the superseded digests still in place, the
   same path over the pre-change Makefile reports no drift at all, reproducing
   `7fadaf20…` and `e48c8b01…`. So this re-pin is not sitting on a move someone
   else had already made and left unrecorded.

New values: standalone `8f32abf234db…`, composed `de0cadbf5e92…`.

`tools/test_local_ci_shared_test_deduplication.py` — 27 passed. The other three
guards run alongside it were already green: `test_pack_test_compatibility.py`,
`test_pack_test_class_characterization.py` and `test_build_gate_chain.py`, 95
passed with 28 subtests across the batch.

## 2026-09-13 — Review round 2: 5 findings, 2 sustained, 3 refuted

Three were refuted with reasons worth keeping:

- **Completeness does not consult record usability.** True as an observation —
  `evaluate_capture_set` never calls `evaluate_record` — but no criterion folds
  the two together. The capture-set criterion is scoped to the height-and-scroll
  combinations; usability is a separate axis already tested parametrically over
  every required field, and `unusable-capture` is its own result state.
- **The measurement configuration contradicts the run.** The table sits under
  "The configuration this was measured with" and states the *requested* offsets,
  which is true of the run; the attained state is recorded eleven lines later,
  naming all 17 captures that could not reach a non-zero position. Nothing
  reports 400 as attained.
- **Tautologies remain.** Both cited assertions are genuinely incapable of
  failing, but each sits immediately beside one that carries the criterion and
  can. No criterion rests on them, and no rule prohibits a redundant assertion
  next to a load-bearing one.

### The rate guard: SHRINK, after two rounds of opposite complaints

Round 1 said the guard was too loose. Round 2 said it was simultaneously too
loose (`4%—the false-positive rate` missed) and too tight (`The false-positive
rate uses 4 known-clean fixtures.` falsely rejected). Both were true by
construction.

A control drawing opposite complaints in consecutive rounds is measuring
something its medium cannot decide: a regex over prose cannot separate a
published rate from an ordinary count. The adjudicator was asked to rule
KEEP / SHRINK / CUT and ruled **SHRINK**, which is what was applied:

- `_GAP_BEFORE` now uses the same punctuation class `_GAP_AFTER` already had, so
  *which punctuation* sits between a number and its term stops deciding the
  outcome. That is one character-class change at an existing seam.
- `_GAP_AFTER` was deliberately **not** hardened. Constraining it to
  "rate-bearing syntax" would ask the regex to make the same semantic judgement
  from the other side, which is how the oscillation started.
- The word budget before a term stays at two, because widening it is what made
  the shipped "Known-clean fixtures — 4" heading read as a rate.

Verified: the three punctuation-separated forms are now caught, all six round-1
forms are still caught, and four legitimate count-bearing sentences — including
the exact shipped heading that caused the earlier false positive — still pass.

**The claim was narrowed in the test module, not in the spec.** The
adjudicator's `Fix:` also directed stating the reach in the spec's Testing
Strategy bullet. That edit was made, and then reverted, because it moved
`approved_spec_hash` off its sealed value: the hash covers the whole normalized
spec file, not just its criteria (see the correction at the top of this ledger).
Narrowing an approved contract is the owner's call and the controlled-amendment
path's job, not a repair to slip in during a review round. The narrowed reach is
fully stated in
`packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_shipped_content_limits.py`,
which is the artifact a reviewer actually inspects.

**Owner decision, 2026-09-13: leave the spec unchanged; keep the narrowing in
the test module.** No second amendment, and `approved_spec_hash` stays at
`86287a46196b…`. The accepted cost is recorded rather than hidden: the spec's
Testing Strategy still describes the guard's reach as the vocabulary alone, so
it understates the blind spot slightly against the test module, which states
both the vocabulary and the adjacency window. A future reader who takes the
spec's wording as the whole reach will overestimate what the guard catches.

### The disclosure fix

`page-scrollable` is transmitted to the judge but was absent from the
`Carried to the judge` enumeration, which the prose presents as complete. The
browser-state row now names it. The minimal fix was taken; the finding's
suggested completeness assertion against `judgement_request_fields` was declined
as over-broad, on the adjudicator's own reading.

**Suite:** 176 passed. Deep lint exit 0 (`CAT-S003` 830 lines, 170 of headroom).
`catalogue verify` ok.

## 2026-09-13 — workspace registration

The spec was in no `workspace.toml` entry, so canonical preflight returned
`unregistered_work` and refused to dispatch. The owner assigned ini-003 (Digital
Experience Doctrine), which already owns this pack's other spec,
`docs/specs/frontend-engineering-doctrine-update/spec.md`.

The entry went to `["ini-003".work] queue`, not `active`. `work.active` admits a
spec whose status is `Implementing` only; an `Approved` spec placed there
reconciles as `impossible_transition`, which was observed once and corrected.
From `queue`, the entry evaluates as `canonical.ready` with `dispatchable: true`
and no findings. It moves to `active` when EXECUTE bumps the spec to
`Implementing`.

## 2026-09-13 — Specialist reviews, and an owner-authorised scope expansion

### What the specialists found

`security-reviewer` (Codex, routed to the `llm-agent` and `agentic-skills`
boundary modules): 2 findings, **1 sustained**.

- **Sustained — the prompt-injection boundary never reaches the judge.** The
  pack states that captured content is untrusted evidence with no instruction
  authority, but that binds the agent *reading the skill*. The judgement request
  carries five fields and no such declaration, and the spec deliberately supports
  routing captures to a separate adopter-chosen judge that never reads the skill.
  `llm-agent.md:39-42` (LLM01) requires untrusted content to be delimited **and**
  the prompt to instruct the model not to treat it as instructions. Blast radius
  is capped — a steered judge cannot change classes or severity — but it can
  return *no* findings, producing a `completed` inspection over a broken page.
- **Refuted — pin `npx playwright`.** The identical unpinned `npx` pattern is
  pre-existing accepted pack content (`html-validate`, `pa11y`, `axe`), the line
  is explicitly an example, and pinning would require an adopter-installed driver
  — colliding with the `Ask first` on runtime dependencies *and* the release
  criterion that dependency surfaces gain nothing. Recorded because this session
  had called it a real finding before adjudication; it is not.

`quality-engineer` (spec-level pass): 4 findings, **3 sustained**.

- **Blocking — a Blocker finding does not stop the surface completing.** See
  below; this is the headline gap.
- **Blocking — the every-captured-height rule is enforced but never shipped.**
  This one is self-inflicted. Fixing round 1's Blocker put Rule 2 inside
  `evaluate_capture_set`, which checks "every height this route actually
  captured". The shipped reference never says that, and still says "Further
  heights are welcome and none are required". So the control authors the rule it
  checks — contradicting this module's own "Nothing in this module states a rule"
  docstring and the plan's design decision that rules are data the checks read.
  **A repair instantiated the exact defect class the delivery exists to prevent.**
- **Advisory — the rule-table reader accepts malformed tables silently.** A
  duplicate class row is collapsed by a dict comprehension, so "every class has
  exactly one severity" cannot fail on that mutation; a literal pipe shifts a
  cell; a repeated heading is read only once.
- **Refuted — required diagnostic context on every failure state.** The criteria
  oblige distinguishability and naming the missing capability, "and no other".

### The Objective-to-criteria gap

Three adversarial rounds checked *criteria → checks*. None checked *Objective →
criteria*. The Objective promises "a completion signal that cannot be green while
the page is visibly broken" (`spec.md:27-28`) and **no acceptance criterion
implemented it**: every "cannot satisfy a completed inspection" rule is about
execution failure — a missing capture, an unusable record, a navigation, capture
or judgement error — never about findings. A run that captures all four states,
judges them, finds an `occlusion` Blocker and records it reports `completed`.

### Owner decision, 2026-09-13: take all four parts

The owner authorised a scope expansion covering the whole holistic fix, which
takes three items the spec routes to `Ask first`:

1. **Consequence.** An unresolved reader-visible finding of blocking severity
   yields a state that is not a completed inspection, with execution state kept
   separate from the inspection verdict.
2. **Reviewer seed.** `frontend-reviewer` is seeded with the capture set and the
   observations, so the independent check can see the page. This was Follow-on 3.
3. **Reviewer lens.** A sixth lens for reader-visible layout failure, taking
   severity from the shipped class table so reviewer and step agree.
4. **Capture-time independence.** `frontend-reviewer` gains Bash so it captures
   its own evidence rather than trusting the author's.

Residual risk recorded rather than hidden: part 4 puts a Bash-capable reviewer in
the loop, and this repository has been bitten by reviewers mutating the tree. The
agent definition will constrain it to capture-only invocation against
adopter-named routes and state that it must not write to the repository. That is
a mitigation, not a guarantee.

### Discovery for the new scope, measured

| Question | Measured |
| --- | --- |
| Is `.claude/skills/work-loop/SKILL.md` editable? | No — a projection, byte-identical to `packs/core/.apm/skills/work-loop/SKILL.md`. The dispatch line is a **core pack** edit, so this delivery ships **two** pack releases |
| Room in that file? | `CAT-S003` at **874 of 1,000** — 126 lines of headroom |
| Does anything pin `frontend-reviewer`'s tools? | No. Two core tests name it — one lists reviewer roles, one tests finding-format parsing. Neither asserts tools |
| Is `frontend-reviewer` projected here? | No; the pack source is the only copy |
| What regenerates? | `.claude/skills/work-loop/` and `.agents/skills/work-loop/` |

### Also folded in

The session's own visual-fuzz pass (24 generated pages, 87 captures, zero
invariant failures) surfaced one thing the eight hand-written fixtures cannot:
**no class-precedence rule**. Each shipped fixture declares exactly one failure
by construction, but a real page carries several — `fuzz-002` shows occlusion and
overflow together. Nothing says which class wins, and they carry different
severities. That was cosmetic before; under part 1 severity decides whether the
gate passes, so it becomes load-bearing and is in scope.

## 2026-09-13 — Review round 4, and the defect this delivery kept reproducing

Three reviewers ran against the amendment. 14 findings, **9 sustained**, 4
refuted, 1 indeterminate settled on supplied evidence.

### The blocking one, found by two reviewers independently

**The inspection verdict reached no human surface.** T8 put it in the reference
rule table and in the test helper. `SKILL.md` § 5c graded `completed` by state
alone, the `inspection observations` manifest row recorded only the state, and
the `accept-frontend-evidence` gate checked observations and state and never the
verdict. T8's own Done-when named the gate assertion; no test made it.

So the amendment that existed to make the Objective's promise true left the
promise untrue on every surface an adopter reads — and 200 tests stayed green,
because they exercised the helper rather than the shipped contract.

**This is the third instance of one defect class in this delivery:** a rule
living where the check can see it and the adopter cannot. The round-1 Blocker
repair introduced it, T10 was written to close it, and T8 reproduced it one task
later. Writing the task did not inoculate the next task. The durable lesson is
mechanical, not attitudinal: **a check that reads a helper proves nothing about
shipped content, so every rule now needs an assertion that opens the shipped
artifact.** Five such assertions were added, one per surface, plus a walk that
fails if the verdict is missing from any of the three.

### What was fixed

| Finding | Fix |
| --- | --- |
| Verdict absent from shipped surfaces | § 5c states both axes; the `completed` row is conditional on the verdict; the manifest row carries it; the gate checks it and says what `fail` obliges |
| Reviewer's global diff-confirmation rule voided Lens 6 | Confirmation scoped per lens — diff for 1-5, a capture for 6, with the reason stated so the next editor does not re-impose it |
| Two surviving "five lenses" statements | Corrected; "The other five lenses" inside Lens 6 is accurate and kept |
| Journey still described a diff-only reviewer | Reviewer step and review gate name the captures and the new lens |
| Target-size reachable from two lenses at two severities | The finding-class table wins for an overlapping control, one finding emitted; the glossary no longer grades target size |
| Seeded observations reached a Bash-capable reviewer as trusted input | The untrusted-data clause now covers the observations field, capture records and routes — LLM05, model output as untrusted input to the next sink |
| `verdict-blocking-severity` read with a default | Fails closed; deleting the row raises |
| `capture_set_rules` bypassed duplicate rejection | Routed through `unique_keyed` |
| Precedence expectation shared `SEVERITY_ORDER` with its implementation | The expected order is parsed from the reference's own sentence, and the module constant is asserted against it; a reorder now fails, proven by a mutation |

### Refuted, with reasons worth keeping

- **`Bash` has no portable containment.** The containment gap is the
  platform's, not this delivery's. Every Bash-capable agent in this repository
  carries generic `Bash` with no sandbox, and the two peer reviewers carry no
  no-write clause at all — `frontend-reviewer` is the strictest of them. No
  browser-specific capture capability exists in the declared tool vocabulary.
  **This corrects a claim made earlier in this session** that the risk was one
  this change introduced.
- **An undisclosed second recipient.** `frontend-reviewer` is a forked subagent
  inside the adopter's own work-loop, not the adopter's judge; nothing leaves
  the environment on that hop.
- **Capture paths need confinement.** The reviewer already holds `Read` over the
  tree, so no marginal disclosure exists, and routing shipped pack content
  through this repository's own helper would violate `packs/AGENTS.md`.
- **An incomplete run labelled `pass`.** The verdict is not a completion signal
  alone; `is_completed_inspection_result` already refuses an incomplete state.
  Collapsing the axes would undo the distinction the amendment created.
- **The version was reused.** Settled on supplied git evidence: `origin/main`
  carries 0.2.2 in both manifests and zero 0.2.3 changelog entries; 0.2.3 was
  first set by this delivery at `8b95e6a99` and is unreleased. Further content
  from the same unreleased change accumulates into it correctly.

### T8-T12 completion evidence

**Suite:** 213 passed. **Gates:** `catalogue lint --deep --pack
frontend-engineering` exit 0, one finding — `CAT-S003` at **848** body lines
against the 1,000 ceiling, **152 of headroom**. `catalogue verify` ok.
`lint-pack-test-boundary` 8 of 8. `lint-journey-contract` all 20 conform;
`lint-web-journey-parity` all 20 in parity. Self-host regenerated the work-loop
projections from `packs/core/.apm`, and a test asserts projection and source
match.

**Dependency surfaces, re-measured against T0's set:** `[pack.dependencies]`
absent; `first-value.prerequisites` `[]`; `plugin.json` fields
`description, name, version`; skill frontmatter still only `name`/`description`;
**0** `.py` and **0** `scripts/` under either pack's `.apm/`. No new dependency.

**The end-to-end rerun the adjudication required**, over the 20 real captures
from the shipped fixtures with the judgements recorded earlier in this session:

| Fixture | State | Verdict | Completed inspection? |
| --- | --- | --- | --- |
| clean-article / card-grid / form / nav | completed | pass | yes |
| defect-occlusion | completed | **fail** | **no** |
| defect-clipped-at-rest-top | completed | **fail** | **no** |
| defect-overflow | completed | pass | yes |
| defect-target-undersized | completed | pass | yes |

Both `Blocker`-class defects now stop the surface completing while still
reporting that the step ran. The two `Major` defects are reported and do not
block, which is the intended gradient — a step that blocked on every finding
would be turned off, and the intent's guardrail names that outcome directly.

## 2026-09-13 — Round 5, a mechanical sweep, and the end of the review budget

### The sweep, run because one-at-a-time fixing was not converging

The same defect class — a rule living where the check can see it and the adopter
cannot — had recurred through rounds 1, 4 and 8 of implementation. Instead of
reading for a fourth instance, it was tested mechanically in three directions.

1. **Delete each shipped rule row; does anything fail?** 42 two-cell rows.
   **41 caught, 1 survivor.** This also disproved a code-reading hypothesis: six
   `.get()` calls with fallbacks looked like live fail-open holes, but the tests
   assert row values directly, so a deleted row fails anyway. Recorded because
   the reading was wrong and the measurement corrected it.
2. **Corrupt each rule's value to garbage.** **39 of 42 caught**, 3 survivors —
   all rows of the sensitive-capture exposure table, the only table checked by
   phrase rather than by value.
3. **Is each rule's substance on the surfaces an adopter reads?** Two apparent
   gaps were false positives and were eliminated rather than reported: the
   untrusted-evidence rule is in § 5c under different words, and the filename
   rule is in the manifest row, outside the section window the check used.

A later, wider sweep over all 59 rows found four more deletable. Two are real —
`incomplete` and `unusable-capture` carry acceptance criteria and are now pinned
by name. Two are **not defects**: no criterion requires the `clipped` or
`illegible` classes to exist, and the one-severity-per-class rule governs the
rows present rather than which classes a pack ships. Recorded so the next sweep
does not re-raise them.

### Round 5, and what it converged with

Two reviewers, 9 findings. Several matched the sweep independently; two did not,
and both were things the sweep could not see:

- **`ruff` reported 24 errors and `make lint-ruff` had never been run.** The
  merged `CLAUDE.md` states plainly that ruff and mypy *are* the local gate.
  Fixed; both now pass, 139 source files clean under mypy.
- **The new shipped-surface checks accepted negated contracts.** They required
  only the word `verdict` to appear, so "yes regardless of verdict" or "verdict
  not recorded" would pass. The checks now assert the *relationship* — the
  completion cell must be conditional, name a pass, and not negate it — with
  four negation mutations pinned.

### What was fixed

| Finding | Fix |
| --- | --- |
| `Result surfaces` required state only | The table now carries a verdict column; all three surfaces require both axes. This is the row that governs the other three, so fixing them individually had left the contract state-only |
| Precedence stated nowhere the agent reads | Now in § 5b where the agent classifies, and in the guide |
| The guide never mentioned the verdict | Section 3 carries both axes; its `completed` row is conditional on a pass |
| The guide omitted the judge-side declaration | Step 2 tells the adopter to declare the capture untrusted in the request itself |
| The guide omitted the extra-height rule | Section 1 carries it |
| The reviewer's "review against the diff alone" fallback | Lens 6 cannot be answered by a diff, so the no-evidence path is now capture-it-yourself, else a named skip. A silently dropped lens reads as a clean one |
| Journey metadata advertised a diff-only reviewer | `whatChanges` names the rendered captures |
| Journey step-4 output carried state only | Carries the verdict |
| The spec's Objective still called reviewer seeding a follow-on | Records that it was taken into scope by owner decision |
| Exposure table corruptible | All three rows pinned by value, with per-row deletion mutations |
| `incomplete` / `unusable-capture` deletable | Criterion-bearing states pinned by name |

**Suite: 235 passed.** `ruff` and `mypy` clean. `catalogue lint --deep` exit 0
(`CAT-S003` 851 of 1,000). `catalogue verify` ok. All journey and guide lints
pass.

### The review budget, and what ships unreviewed

`review_retry_count` reached 5 of 5 with this round. The owner was shown the
position before the retry was spent and chose: fix round 5, then stop reviewing
and ship.

**So the round-5 repairs above are unreviewed.** That is the delivery's largest
residual risk and it is stated here and in the PR rather than left implicit.
Mitigating it: every fix is pinned by a check that was driven against a mutated
source, the two sweeps were re-run after the fixes, and the suite grew 213 → 235.

The recurring defect class is the lesson worth carrying out of this delivery,
and it is mechanical rather than attitudinal: **a check that reads a helper
proves nothing about shipped content.** The sweep that finds it takes six
minutes and should run after any change to a rule layer, not after five review
rounds.
