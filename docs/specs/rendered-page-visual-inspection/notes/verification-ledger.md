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
