# Plan: loop-cohort unknown dependency refusal

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - Convention source: [`packs/AGENTS.md`](../../../packs/AGENTS.md) — `.apm/` is
    the projection source; never edit adapter copies; every non-cosmetic pack
    change bumps `pack.toml` and `.claude-plugin/plugin.json` together and
    updates that pack's eval harness.
  - Analogous implementation 1: `detect_cycles` / `detect_forward_refs`
    (`loop-cohort.py:1027,1036`) — pure predicates over the parsed graph whose
    results the `schedule` run path turns into a refusal and a warning
    respectively. The new predicate is the third member of that family.
  - Analogous implementation 2: the forward-reference diagnostic
    (`loop-cohort.py:1391-1397`) — the exact shape a diagnostic takes on the
    `schedule` path, including the `spec_dir.name` prefix and the `a->b` pair
    rendering.
  - Corresponding tests: `packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py`
    (pure-function surface, loaded via `importlib`), `test_loop_cohort_cli.py`
    (subprocess surface against the real script path), and
    `test_contract_amendment_wave4.py`, which is the only file exercising
    `schedule_unfinished_plan` today.
  - Named uncertainty: the two set axes below are easy to conflate, and
    conflating them is how this change breaks amended plans. T1's tests pin each
    axis separately.

> **Plan contract:** this is the implementation strategy.

## Approach

Add one pure predicate and call it from the single place that builds a wave list.
The dependency-ID extraction `parse_depends_on` already performs is lifted
into a small shared helper so the predicate and the parser cannot drift — the
alternative, re-implementing the strip-and-extract sequence in the predicate,
would leave two copies of the cross-spec stripping rule to keep in step.

`parse_depends_on` keeps its signature and its filtering behaviour. `parse_plan`
keeps its arity. Neither raises. The refusal lives at the call sites that own an
exit code, which keeps the parsers usable by anything wanting a best-effort read.

### The two set axes

The predicate uses two different task sets, derived from two different places.
Conflating them is the failure mode this plan exists to avoid.

| Axis | What it is | Where it comes from | Why |
| --- | --- | --- | --- |
| **Resolution set** | IDs a dependency may name | Every `T<n>` heading in the plan file, computed inside the predicate | A dependency on a completed task is met, not unknown (AC7) |
| **Scan set** | Tasks whose declarations are read | Passed by the caller: the unfinished tasks | A completed task's edges cannot affect a remaining wave, and its section is content-pinned (AC7a) |

Neither axis is `remaining_set`. `schedule_unfinished_plan` intersects
dependencies with `remaining_set` so a completed dependency counts as met;
resolving the new predicate against that set would refuse every amended plan.

## Constraints

- Both published signatures are pinned. `spec.md` AC8 is the canonical statement;
  this line points at it rather than restating it.
- The pins are enforced by `test_parse_plan_signature_unchanged` and by six
  `parse_depends_on` tests (`test_loop_cohort_schedule.py:35,39,48,53,60,68`), of
  which exactly one — `test_parse_depends_on_none:36` — asserts the full two-tuple
  by equality; the other five unpack and assert members.
- `.apm/` is the only editable copy; the `.claude/` and `.agents/` projections are
  regenerated, never hand-edited.
- `loop-cohort.py` is a standalone hyphenated script loaded by `importlib`; it
  cannot gain a package-relative import.

## Risks

- **Over-broad predicate.** A legitimate cross-spec form read as a local ID would
  refuse a correct plan. Mitigated by driving the negative cases from the same
  fixture table as the positive ones (AC5, AC6).
- **Golden-stream drift.** `test_loop_guards_parity.py` pins normalized
  stdout/stderr for `schedule check-current` rows. That verb hashes `plan.md` and
  never parses dependencies, so it is not on the changed path; the pre-change
  baseline run (1061 passed, 5 skipped, 22m34s) is the comparison point.

## Design (LLD)

### Interfaces

```python
def _local_dep_ids(field: str) -> set[str]:
    """Every local task ID a `Depends on:` field names, before plan membership filters it."""

def detect_unknown_deps(text: str, scan_task_ids: set[str] | None = None) -> list[tuple[str, str]]:
    """Return (task, dep) pairs naming an ID the plan does not contain.

    Dependencies always resolve against every task in `text`. `scan_task_ids`
    restricts which tasks' declarations are read; None reads all of them.
    """
```

`parse_depends_on` is refactored to call `_local_dep_ids` and then filter, which
is its current behaviour expressed once. `detect_unknown_deps` derives the
resolution set from the headings itself, so no caller can narrow it by mistake.

### Control flow

**Exactly one call site.** `schedule_unfinished_plan` calls
`detect_unknown_deps(plan_text, scan_task_ids=remaining_set)` **immediately
before** its `detect_cycles` call (`loop-cohort.py:609`) and raises `ValueError`
on a non-empty result. It computes `remaining_set` itself, so no caller supplies
the scan set.

Pass it by keyword, never positionally. The variable in scope at that line is
`remaining_set` — the same set this change must not resolve against — so
`scan_task_ids=` is what makes the role visible at the call site and stops a
later reader from "simplifying" it into the resolution set.

`_schedule_run_impl` gets the refusal by delegation and adds no call of its own:

- It reaches `schedule_unfinished_plan` unconditionally (`loop-cohort.py:1388`),
  and that function is the only caller of `detect_cycles` and the only
  non-internal caller of `topological_waves` — it builds no wave list itself.
- The delegated call precedes the first state write (`write_state_atomic`,
  `loop-cohort.py:1421`), so nothing is persisted on refusal.
- The `ValueError` surfaces as `return stop(f"schedule: {exc}")`
  (`loop-cohort.py:1389-1390`): non-zero exit, pairs on stderr.
- Placing it before `detect_cycles` gives the unknown-dependency refusal
  precedence over the cycle refusal at both entry points at once (AC4).

A second call in `_schedule_run_impl` is **forbidden**, not merely unnecessary:
it would be redundant, and deleting it would leave every test green, so the T3
mutation would report a passing proof for a deleted guard (AC9).

## Tasks

### T1: Add the unknown-dependency predicate

**Depends on:** none

**Touches:** packs/core/.apm/skills/work-loop/scripts/loop-cohort.py, packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py

**Tests:**
- Returns `[("T2", "T7")]` for a two-task plan whose T2 declares
  `**Depends on:** T7` (AC1).
- Returns every pair, sorted by declaring task then dependency, for a plan with
  two offending tasks (AC2).
- Returns `[]` for each legitimate form, driven from one fixture table: `none`,
  an in-plan ID, `T1a`, an in-plan range `T1-T3`, `spec:other/T7`,
  `` `other` T7 ``, and `T1 (trailing prose)` (AC5, AC6).
- Returns `[]` for a forward reference, whose dependency *is* in the task set
  (AC3).
- Returns `[("T3", "T2")]` for `**Depends on:** T1-T3` in a plan holding `T1` and
  `T3` but no `T2` — a range names every ID it spans (AC6a).
- **Resolution axis, discriminating case:** for a plan of `T1`, `T2`, `T3` where
  `T3` declares `**Depends on:** T1`, `detect_unknown_deps(plan, {"T3"})` returns
  `[]` — the declaring task is inside the scan set and its dependency target is
  outside it. This is the only shape that separates the axes. Measured against a
  mutant that derives the resolution set from `scan_task_ids`: this case returns
  `[("T3", "T1")]` under the mutant and `[]` under the correct implementation,
  while every other bullet in this task returns the same value under both (AC7).
- **Scan axis:** returns `[]` when the *only* offending declaration belongs to a
  task excluded from `scan_task_ids`, and returns the pair when that same task is
  included — one fixture, two calls, so the axis is proven by difference (AC7a).
- `parse_depends_on("none", LOCAL) == (set(), [])` and `parse_plan(...)` returns a
  2-tuple — both unchanged (AC8).

```python
# stub: true
def test_detect_unknown_deps_names_the_absent_id():
    plan = "## T1: a\n**Depends on:** none\n\n## T2: b\n**Depends on:** T7\n"
    assert lc.detect_unknown_deps(plan) == [("T2", "T7")]
```

**Approach:**
- Extract `_local_dep_ids(field)` from `parse_depends_on`'s body, returning the
  unfiltered ID set.
- Rewrite `parse_depends_on` to `{t for t in _local_dep_ids(field) if t in
  local_task_ids}, cross` — same behaviour, one source for the extraction.
- Add `detect_unknown_deps(text, scan_task_ids=None)` walking `TASK_HEADING_RE`
  matches, collecting `_local_dep_ids(...) - taskset` for each scanned task.

**Done when:** the new tests are green, and `test_parse_plan_signature_unchanged`
plus all six `parse_depends_on` tests still pass unmodified.

### T2: Refuse at the single wave-building call site

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-loop/scripts/loop-cohort.py, packs/core/tests/skills/work-loop/test_loop_cohort_cli.py, packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py

**Tests:**
- Subprocess `loop-cohort schedule <spec-dir>` on a fixture plan with an unknown
  dependency: non-zero exit, stderr names `T2->T7`, and `state.json` bytes are
  unchanged from before the run — reaching the refusal by delegation, with no call
  site of its own (AC1).
- Same, two offending tasks, one refusal listing both (AC2).
- Control: the same fixture with the dependency corrected exits zero and writes
  `schedule_waves` — the case that must show the edge (AC6).
- A plan carrying both an unknown dependency and a cycle emits the
  unknown-dependency refusal (AC4).
- In `test_contract_amendment_wave4.py` (the file that owns this function's
  tests): `schedule_unfinished_plan` raises `ValueError` naming the pair for an
  unknown ID; still returns waves when the dependency is a **completed** task
  (AC7); does not raise when only a completed task's own declaration is stale
  (AC7a); and raises the unknown-dependency error, not the cycle error, for a plan
  carrying both faults (AC4, amendment path).
- The existing forward-ref and cycle tests pass unmodified (AC3, AC4).

Every bullet above except the four in `test_contract_amendment_wave4.py` lands in
`test_loop_cohort_cli.py`.

**Approach:**
- Add the single call inside `schedule_unfinished_plan`, immediately before
  `detect_cycles`, raising `ValueError` with the sorted pairs.
- Add nothing to `_schedule_run_impl`; confirm by reading its body that it holds
  no `detect_unknown_deps` call.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/ -q` reports no
failures and no previously passing test regressing — the count necessarily rises,
because this task and T1 add tests; the baseline run stays in Risks as the
comparison record. The manual run this task once named is dropped: its first
subprocess bullet already asserts the same three things — non-zero exit, the pair
on stderr, and `state.json` bytes unchanged — so a hand run would add an
observation with no declared home rather than new evidence.

### T3: Record the mutation proof

**Depends on:** T2

**Touches:** docs/specs/loop-cohort-unknown-dependency-refusal/notes/verification-ledger.md

**Tests:**
- Deleting the single `detect_unknown_deps` call inside `schedule_unfinished_plan`
  turns red **both** a named CLI test in `test_loop_cohort_cli.py` and a named
  amendment test in `test_contract_amendment_wave4.py`; restoring it turns both
  green (AC9). Two paths, one guard — if either stays green, a redundant second
  call site has crept in and the proof is void.

**Approach:**
- Remove the call site, run the named tests, capture the failure output, restore,
  re-run. Record command, test ids, and observed output in the ledger per
  `references/mutation-proof.md`.

**Done when:** the ledger records the red-on-removal and green-on-restore runs
with their test ids and output.

### T4: Align the documented contract

**Depends on:** T2

**Touches:** packs/core/.apm/skills/work-loop/references/supervisor-mode.md, packs/core/.apm/skills/new-spec/assets/plan.md, packs/core/seeds/docs/CONVENTIONS.md

Edit the seed only. `docs/CONVENTIONS.md` is byte-identical today and is listed in
`PROJECTED_README_OVERRIDES` (`self_host.py:706-708`), so `make build-self` in T5
regenerates it; hand-editing it would be editing a projection.

**Tests:**
- Goal-based, absence exits 0:
  `! grep -rq 'dropped without a diagnostic' packs/core/` (AC10). Scope is the
  whole pack, not just `.apm/`, so the seed is covered.
- Goal-based, positive half: the exact phrase `names no task in the plan is
  refused` appears in **all three** of `references/supervisor-mode.md`, the
  template's `Depends on:` grammar block, and `seeds/docs/CONVENTIONS.md`. Without
  this the absence grep passes when the stale sentence is merely deleted and no
  refusal is stated (AC10).
- Goal-based: `detect_unknown_deps` over the shipped template returns `[]` **and**
  `detect_cycles` over it returns `[]` (AC11).

**Approach:**
- Replace `supervisor-mode.md:15-17`'s "dropped without a diagnostic" sentence
  with the refusal, wording it so it contains the pinned phrase `names no task in
  the plan is refused`, and keeping the cycle and forward-reference sentences as
  they are.
- Extend the template's `Depends on:` grammar block to state the refusal
  alongside the existing cycle and forward-reference sentence.
- Rewrite `seeds/docs/CONVENTIONS.md`'s supervisor-mode paragraph so its
  ill-formed-plan enumeration has all three members, containing the pinned phrase.
- Replace the `<none | T0, ...>` placeholder with
  `<none | comma-separated prior task IDs>`, which names no task ID and so can
  produce neither an unknown dependency nor a self-edge.

**Done when:** all three of T4's checks pass — the absence grep, the
three-surface pinned-phrase check, and the template predicate-plus-cycle run.
Each is decidable at T4's own boundary; nothing here waits on T5.

### T5: Release surface, eval harness, and projections

**Depends on:** T4

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.md, packs/core/.apm/skills/work-loop/evals/evals.json, .claude/skills/work-loop/evals/evals.json, .agents/skills/work-loop/evals/evals.json, .claude/skills/work-loop/scripts/loop-cohort.py, .agents/skills/work-loop/scripts/loop-cohort.py, .claude/skills/work-loop/references/supervisor-mode.md, .agents/skills/work-loop/references/supervisor-mode.md, .claude/skills/new-spec/assets/plan.md, .agents/skills/new-spec/assets/plan.md, packs/core/tests/skills/work-loop/test_step0_eval_contract.py, docs/CONVENTIONS.md

`packs/core/.apm/skills/new-spec/evals/` is deliberately absent: T4 edits that
skill's authored *asset template*, not what the skill does when invoked, and the
eval harness covers invocation behaviour. No new-spec eval entry is owed.

**Tests:**
- Goal-based: `pack.toml` and `plugin.json` carry the same version, and
  `docs/product/changelog.md` has a top-level `## [core][<version>] — <date>`
  section directly beneath `## [Unreleased]`, not nested inside it (AC12).
- Goal-based: after `FORCE=1 make build-self`, each edited `.apm/` file and its
  `.claude/` and `.agents/` copies hash identically (AC13).
- Goal-based: the changelog entry carries a `### Highlights` subsection, for the
  reason AC12 states (AC12).
- Goal-based: `packs/core/.apm/skills/work-loop/evals/evals.json` contains an entry
  with `"id": "schedule-refuses-unknown-dependency"` **and** its `assertions` list
  contains one member matching `refus` and one matching `forward`, asserted by a
  phrase check in the style of `test_step0_eval_contract.py`. The catalogue lint
  only requires assertions to be non-empty strings, so it cannot carry this half.
  Both `agentbundle catalogue lint --root . --deep` and
  `agentbundle catalogue verify --root .` also pass (AC14). This one is a
  **standing test**, not an ad-hoc command: it is added to
  `packs/core/tests/skills/work-loop/test_step0_eval_contract.py`, which already
  owns standing assertions over this same `evals.json`, so the pin survives the
  session that wrote it.

**Approach:**
- Derive the version **immediately before pushing** by reading current
  `pack.toml` and `origin/main`'s `docs/product/changelog.md`, then bump the
  patch. Core is 2.26.6 today, but this repository has collided on a version
  twice in one session and both manifests write identical bytes on a collision,
  so the changelog is the only loud signal.
- Add a `schedule-refuses-unknown-dependency` entry to the `work-loop` skill's
  eval harness, asserting the answer says `schedule` refuses rather than warns and
  distinguishes the forward-reference case.
- Write the `### Highlights` bullets for the changelog entry.
- Run the catalogue commands from the repository tree, not a stale editable
  install: confirm `pip show agentbundle` resolves to this worktree first.
- Run `FORCE=1 make build-self` and require exit 0. This regenerates
  `docs/CONVENTIONS.md` from the seed T4 edited. The seed/projection equality
  needs no check of ours: `diff_against_working_tree` already owns it
  (`self_host.py:1274-1331,1530-1541`), emitting
  `[drift] docs/CONVENTIONS.md: edit <seed>; run: make build-self` and exiting 1,
  and it runs both locally via `make build-self-dry-run` and in CI's build-check,
  whose `paths-ignore` does not filter a `packs/core/**` change. `--force` is what suppresses
  the dirty-tree refusal, so a non-zero exit here is a real failure (a self-host
  check such as `CAT-SH-001`), not the dirty-tree guard. Then compare projected
  copies by hash.

**Done when:** the three release files agree, projections are byte-identical, the
eval harnesses validate, and `make lint-ruff lint-mypy` is green.

## Changelog

- 2026-09-15: Drafted. Owner decision recorded before authoring: refuse at PLAN,
  no opt-out flag, after measuring the blast radius at one template placeholder
  and zero real plans.
- 2026-09-15: Revised from pre-EXECUTE adversarial review, round 5 — 2 findings
  sustained, 0 refuted. Round 4's repair had created a circular obligation: a
  seed/projection `diff` check sat in T4, which edits the seed alone, while the
  `make build-self` that satisfies it runs in T5, which depends on T4 — so the
  check was non-zero by construction at T4's own boundary. Deleted rather than
  relocated: `diff_against_working_tree` already owns that fact and reds on it in
  CI, so moving the check would have created a second home, the same ground that
  refuted round 2's changelog blank-line finding.
- 2026-09-15: Revised from pre-EXECUTE adversarial review, round 4 — 3 findings
  sustained, 0 refuted, no blockers. The one substantive finding was a surface the
  earlier rounds' walk had missed: `seeds/docs/CONVENTIONS.md` enumerates what
  `schedule` does with an ill-formed plan as two members, and this change makes it
  three. AC10's scan widened from `packs/core/.apm/` to `packs/core/`. The seed is
  edited alone because `docs/CONVENTIONS.md` is a projection of it.
- 2026-09-15: Revised from pre-EXECUTE adversarial review, round 3 — 8 findings
  sustained, 0 refuted. The round-2 repair had instantiated its own root cause:
  pinning the predicate inside `schedule_unfinished_plan` made the second call in
  `_schedule_run_impl` redundant, and T3 mutated exactly that redundant call, so
  the mutation proof would have reported success for a deleted guard. Collapsed to
  one call site, which delivers both entry points by delegation and makes the
  mutation falsifiable on both. Also corrected a false blast-radius measurement:
  the inline-fixture count of zero came from a probe whose heading pattern was
  anchored to line start and so could not see indented, quote-prefixed fixtures,
  and which carried no control case. Re-measured from the syntax tree, with a
  control: 2 unknown-dep sites in 1 of 17 files, both unreachable from the
  refusing path.
- 2026-09-15: Revised from pre-EXECUTE adversarial review, round 2 — 9 findings
  sustained, 1 refuted (the changelog blank-line invariant: already enforced by
  `tools/test_build_site_routing.py`, so restating it in an AC would add a second
  home for a fact the test owns). Round 2's blocker on the resolution axis was a
  control that could not fail: all three planned axis assertions returned the same
  value under the correct implementation and under a mutant that derives the
  resolution set from `scan_task_ids`. Measured, then replaced with the one shape
  that discriminates. AC4's precedence was undetermined on the amendment path;
  taken branch (a) of the two the adjudicator named — pin the predicate ahead of
  `detect_cycles` inside `schedule_unfinished_plan` so the refusal behaves
  identically at both entry points, rather than narrowing AC4 to the CLI.
- 2026-09-15: Revised from pre-EXECUTE adversarial review, round 1 — 13 findings
  sustained, 1 refuted. Owner decided the scan axis: only unfinished tasks'
  declarations are examined, resolved against the whole plan's task set. Corrected
  the changelog target from a non-existent root `CHANGELOG.md` to
  `docs/product/changelog.md` directly beneath `## [Unreleased]`.
