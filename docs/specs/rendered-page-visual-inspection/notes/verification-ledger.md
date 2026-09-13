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

The spec hash covers the Acceptance Criteria section only
(`sha256_canonical_contract` passes `ac_section_only=True` for `spec.md`), so
moving the spec's `**Status:**` from `Approved` to `Implementing` before the
first code change does not disturb it. Ticking acceptance criteria at ship time
does, as intended.

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

This count is a local measurement with this judge and these viewport sizes. It is
not a rate, and it is not published in any shipped pack content.

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
