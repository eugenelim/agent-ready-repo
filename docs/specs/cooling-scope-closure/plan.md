# Plan: Cooling scope closure

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/work-intake-and-artifact-routing.md`
  and `docs/CONVENTIONS.md`. Two analogous production implementations: Wave 6's
  cooling projection — `_resolve_cooled_state`, `_cooling_projection`, and
  `_closeout_projection` in
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` — which
  fixes the cooled-set resolution this delivery reuses unchanged and the
  `closeout` block whose derivation it changes; and the migration-effects
  fixture at `packs/core/tests/skills/workspace-status/test_work_intake_migration_effects.py`,
  which is the only builder that produces the authorization, legacy entry,
  selection and confirmation shape AC19-AC22 need. Named uncertainty: none —
  both changed expressions are single lines resolved by symbol, and the cooled
  set is Wave 5's helper called unchanged.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially, note why in the changelog at
> the bottom. Once it is `Done` and the spec is `Shipped`, the directory freezes
> as a unit.

## Approach

Two expressions become one, and one decision gets pinned.

`_closeout_projection` computes `all_specs_shipped` from
`not (initiative.work.queue or initiative.work.active)`, and the
`initiatives[]` builder computes `queue_empty` from `len(ini.work.queue) == 0`.
Wave 6's reverted repair filtered the first and not the second, which is why the
two disagreed inside one response. Both now read one cooled-exclusion helper
that takes the initiative and the resolved cooled set and returns the surviving
queue and active lists. Neither derivation's *shape* changes, which is what AC5
pins.

Withholding the affirmative needs no new guard. `project_closeout_status`
already computes `eligible = all_specs_shipped and not blockers and not paused`
and emits `invoke-close-work` only when eligible, so appending
`cooling-context-incomplete` to `closeout_blockers` does the whole job. An
earlier draft added a second `cooling_context_visible` guard on top; it is cut
under the ladder's first rung.

The repair and migration half is tests only. Six control-run identities pin
`repair-plan`, `repair-apply`, and the migration planning, application,
recovery, and rollback paths as unaffected, and one source-shape criterion pins
the single-argument call sites. No production line changes there.

The riskiest part is the shipped Wave 6 roster assertion this delivery retires.
It is named by file and function in T4 and replaced in place, with AC13 bounding
the change to that one function.

## Constraints

- **RFC-0096 §7** keeps cooling outside ordinary orientation; **§9** scopes
  Wave 7. **RFC-0099 §7**, as recorded in RFC-0096's Errata, makes a
  post-sealing criterion change a material amendment requiring reapproval and
  resealing.
- **`status-projection-and-context-exclusion`** (frozen) owns the cooled-set
  resolution, the `cooling` and `closeout` blocks, and the emission gate.
- **`thirty-day-cooling-and-retirement`** (frozen) owns `cooling.is_due`,
  `cooling.load_record`, and the record schema; its AC24 test forbids new
  cooling keys in `workspace.toml`.
- **`docs/CONVENTIONS.md`** freezes a shipped spec directory as a unit, and its
  non-supersession Status pointer is licensed only for a deleted
  `workspace.toml [backlog].open` anchor — which is why this delivery edits
  neither frozen dependency at all.

## Construction tests

**Two shapes, decided by measurement.** Every stub was written and run against
the unchanged tree, and each red was read to confirm it failed on its assertion
rather than on a fixture error. The observed verdicts:

| Criterion | Verdict | Failing assertion |
| --- | --- | --- |
| AC1 | RED | `assert False is True` |
| AC2 | GREEN | preservation |
| AC3 | RED | `assert False != False` |
| AC4 | RED | `assert False is True` |
| AC5 | GREEN | preservation |
| AC6 | RED | `assert False is True` |
| AC7 | GREEN | preservation |
| AC8 | RED | `assert 'unshipped-specs' not in ['unshipped-specs']` |
| AC9 | RED | `assert 'cooling-context-incomplete' in [...]` |
| AC10 | RED | `assert 'settle-closeout-blockers' == 'invoke-close-work'` |
| AC11 | GREEN | preservation |
| AC12 | RED | the retired function name is still defined |
| AC13 | GREEN | preservation — 67 `test_` functions today |
| AC14 | RED | the exclusion sentence is absent |
| AC15 | RED | the rationale sentence is present |
| AC16 | RED | the withholding sentence is absent |
| AC17 | GREEN | preservation — `repair-plan` calls `analyze(..., cooling_enabled=False)` |
| AC18 | GREEN | preservation |
| AC19 | GREEN | preservation |
| AC20 | GREEN | preservation |
| AC21 | GREEN | preservation |
| AC22 | GREEN | preservation |
| AC23 | GREEN | preservation — all six digests match |
| AC24 | GREEN | preservation — exactly two single-argument calls |
| AC25 | GREEN | preservation |
| AC26 | RED | `assert 'Wave 7a-i closes' in ...` |
| AC27 | RED | the guide sentence is absent |
| AC28 | GREEN | preservation — the §9 range digest matches |
| AC29 | RED | no erratum entry exists |
| AC30 | RED | no erratum entry exists |
| AC32 | GREEN | preservation — both conditions present today |
| AC33 | RED | the closure sentence is absent |

17 red, 15 preservation, 1 `no stub (mode)` — 33. AC13 and AC32 were predicted
the other way round and corrected from the run; AC17-AC24 and AC28 carried no
recorded verdict in the previous draft and were classified by inference, which
this table replaces.

**Both invocations, per criterion.** The spec measures every derivation criterion
on `status` **and** `reconcile`, so AC1-AC11's tests are parametrized over the
pair rather than covered by one integration run each. The two differ materially:
`status` uses `analyze_bounded` with no Type 1 scan while `reconcile` uses
`analyze`, and `_closeout_projection` draws its blockers from
`result.reconciliation`. Wave 6's suite parametrizes the same way. The verdict
table above records the `status` result; the `reconcile` result is recorded
alongside it when the tests are authored.

**Manual verification:** T8.

### Mutation table

Each row is an **obligation**: the mutation is applied by editing the source, its
named test is confirmed red, the observed red is recorded here, and the file's
digest is re-asserted after restore. None is verified yet.

| Mutation | Must redden |
| --- | --- |
| exclude cooled entries from `queue_empty` only | AC3 |
| exclude cooled entries from `all_specs_shipped` only | AC3 |
| widen `queue_empty` to span queue and active | AC5 |
| exclude every queue entry, cooled or not | AC2, AC7 |
| build the cooled membership test from `record.locator` alone | AC4 |
| project a paused initiative into `initiatives[]` | AC11 |
| delete or add one `test_`-prefixed function in Wave 6's roster file | AC13 |
| delete any one of the three wave statements, or add the negated string | AC25 |
| add a cooled filter to `repair-plan`'s reconciliation | AC17 |
| add a cooled filter to `repair-apply`'s revalidation | AC18 |
| add a cooled filter to migration planning | AC19 |
| add a cooled filter to the migration apply path | AC20 |
| add a cooled filter to the migration recovery branch | AC21 |
| add a cooled filter to the migration rollback path | AC22 |
| change one byte of any file in AC23's digest table | AC23 |
| pass any second argument to either single-argument call site | AC24 |
| change one byte inside RFC-0096 §9's body | AC28 |

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `runtime-coordination` derivation | T2, T3 | AC1-AC11 | Both consumers read one helper; AC5 shows neither widened |
| Wave 6 roster assertion | T4 | AC12, AC13 | Replaced in place; 67 functions still |
| `user-documentation` / workspace-status SKILL.md | T5 | AC14, AC15, AC16 | Gate matches the projection |
| `user-documentation` / work-intake reference | T5 | AC27 | Literal present |
| `current-architecture` / work-intake routing | T5 | AC25, AC26 | Three strings, absent string, four slices |
| Repair and migration decision | T6 | AC17-AC24 | Control-run identity, no production diff in T6's file set |
| `decision-record` / RFC-0096 Errata | T7 | AC28, AC29, AC30 | Both corrections and the three slugs recorded; §9 digest holds |
| `capability-evidence` / frozen dependencies | T7 | AC23 | Every listed digest holds |
| `release-history` / changelog | T8 | AC31 | Three surfaces agree |
| `project-knowledge` | T8 | Gate receipt or not-applicable finding | One of the two |

## Design (LLD)

### Design decisions

- **One helper, two callers, unchanged shapes.** The alternative — widening
  `queue_empty` to span queue and active so the two values become equal — passes
  every movement criterion while silently changing what a shipped emitted field
  counts, which the spec's Ask-first rail reserves for human sign-off. AC5 is
  the criterion that rejects it. Traces to: AC1, AC3, AC5.
- **Cooled membership is decided through the cooled set's own resolution.** Two
  independently written filters can agree on a record's `locator` and disagree
  on its `aliases`; the cooled set is built from both, so the membership test
  reuses it rather than re-deriving. Traces to: AC4.
- **The blocker alone withholds the affirmative.** No second guard is added; the
  shipped eligibility expression already consumes the blocker list. Traces to:
  AC9, AC10.
- **The repair and migration decision is "unchanged", so its deliverable is
  control runs.** An assertion that no filter exists would pass against an
  implementation that added one and ignored it. Traces to: AC17-AC22.
- **`cooling-context-incomplete` gets no documentation row.** The finding-code
  documentation gate is scoped to `engine._FINDING_NEXT_ACTIONS`; this literal is
  a `closeout_blockers` member, and no repository surface documents any blocker
  literal today. Traces to: AC9.

### Data & schema

No schema change and no new persistent representation. `workspace.toml` gains no
key, `docs/lifecycle/` gains no writer, and both frozen dependency directories
are byte-pinned by AC23 · contracts: none.

### Behavior & rules

The cooled-exclusion helper takes the initiative and the resolved cooled set and
returns `(surviving_queue, surviving_active)`. `all_specs_shipped` is
`not (surviving_queue or surviving_active)`; `queue_empty` is
`len(surviving_queue) == 0`. Traces to: AC1-AC7.

### Failure, edge cases & resilience

- A paused projected initiative has a `closeout` block and no `initiatives[]`
  entry, so the movement criteria are measured on an `active` projection; AC11
  pins the paused shape and probe 2 records the observed output.
- A lifecycle record that cannot be read appends the blocker, which withholds
  the affirmative rather than presenting a partial exclusion as complete.

Traces to: AC9, AC11.

## Tasks

### T1: The fixture harness builds cooled, alias-cooled, and migration fixtures

**Depends on:** none

**Verification mode:** goal-based check. `no stub (mode)`.

**Approach:**
- Add the cooled-initiative builder to the new suite
  `tests/roster/test_cooling_scope_closure.py`, reusing the record-writing and
  injected-instant helpers in
  `tests/roster/test_status_projection_and_context_exclusion.py`.
- The builder takes the queue, active and shipped lists, the initiative status,
  whether to write the record, whether the entry is named by `locator` or by
  `aliases`, and whether to add an unreadable record — so each control pair
  differs by exactly one argument.
- For AC19-AC22, reuse the authorization/legacy-entry/selection/confirmation
  builder at
  `packs/core/tests/skills/workspace-status/test_work_intake_migration_effects.py`
  rather than authoring a second one. Assert the fixture is real with a
  **pair**, not a single run: the cooled artifact is present in
  `canonical.ready` with `docs/lifecycle/` removed and absent with it present. A
  single absence assertion passes when the artifact was never dispatchable, and
  `_cooled_locators` requires `member.exists()` — so a record naming a
  nonexistent path yields an *empty* cooled set and a byte-identical pair while a
  one-sided guard still passes.
- For AC17 and AC18 the queued spec's `Status` is `Shipped`, so a Type-2
  automatic operation exists and `repair-apply` actually writes. AC18 asserts
  `workspace.toml` changes in **both** runs before comparing them; otherwise a
  fixture with nothing to repair makes the pair identical for the wrong reason
  and the cooled-filter mutation cannot redden it.

**Done when:** each fixture's `status` run parses, the cooled and uncooled
variants differ only by `docs/lifecycle/`, the migration fixture's realness pair
holds, and the AC17 fixture produces a non-empty `repair-plan`.

### T2: The two closeout consumers read one cooled-exclusion helper

**Depends on:** T1

**Verification mode:** TDD. Six red stubs (AC1, AC3, AC4, AC6, AC8, AC10) and
four preservation criteria (AC2, AC5, AC7, AC11).

**Tests:**

```python
# STUB: AC1 — a cooled queue entry counts toward neither consumer.
# [observed RED: assert False is True]
def test_ac1_cooled_queue_entry_counts_toward_neither(tmp_path):
    d = _status(_cooled(tmp_path))
    assert d["closeout"]["all_specs_shipped"] is True
    assert d["initiatives"][0]["queue_empty"] is True


# STUB: AC3 — both consumers move together.  [observed RED: assert False != False]
def test_ac3_both_consumers_move_together(tmp_path):
    cooled = _status(_cooled(tmp_path / "a"))
    plain = _status(_cooled(tmp_path / "b", on=False))
    assert (cooled["closeout"]["all_specs_shipped"]
            != plain["closeout"]["all_specs_shipped"])
    assert (cooled["initiatives"][0]["queue_empty"]
            != plain["initiatives"][0]["queue_empty"])


# STUB: AC4 — an alias-cooled entry moves both consumers.
# [observed RED: assert False is True]
def test_ac4_alias_cooled_entry_moves_both(tmp_path):
    d = _status(_cooled(tmp_path, alias=True))
    assert d["closeout"]["all_specs_shipped"] is True
    assert d["initiatives"][0]["queue_empty"] is True


# STUB: AC5 — queue_empty still counts the queue alone.  [observed GREEN]
def test_ac5_queue_empty_counts_the_queue_alone(tmp_path):
    d = _status(_active_only(tmp_path))
    assert d["closeout"]["all_specs_shipped"] is False
    assert d["initiatives"][0]["queue_empty"] is True
```

`stub: true` for AC1, AC3, AC4; AC5 is preservation with its own mutation row.
All compiled clean and every verdict above was observed, not inferred.

**Approach:**
- Add the cooled-exclusion helper and have `_closeout_projection` and the
  `initiatives[]` builder both call it. Resolve both anchors by symbol.
- Decide cooled membership through the resolution the cooled set used, so an
  alias-named entry is treated as its locator-named equivalent.
- Add nothing else: no guard, no field, no key.

**Done when:** AC1-AC8, AC10 and AC11 pass, and
`packs/core/tests/skills/close-work/` still passes including Wave 5's AC24
workspace-key test.

### T3: An incomplete cooled reading appends the blocker

**Depends on:** T2

**Verification mode:** TDD. One red stub.

**Tests:**

```python
# STUB: AC9 — an incomplete cooled reading withholds the affirmative.
# [observed RED: assert 'cooling-context-incomplete' in [...]]
def test_ac9_incomplete_reading_withholds_affirmative(tmp_path):
    c = _status(_cooled(tmp_path, unreadable=True))["closeout"]
    assert c["cooling_context_visible"] is True
    assert "cooling-context-incomplete" in c["closeout_blockers"]
    assert c["next_action"] != "invoke-close-work"
```

`stub: true`. Its fixture is AC1's fully cooled initiative **plus** one
unreadable record, so `unshipped-specs` is absent and the appended blocker is
the only thing withholding the affirmative. An earlier draft used an uncooled
fixture, where `unshipped-specs` already withheld it and the criterion proved
nothing.

**Approach:**
- Append `cooling-context-incomplete` to the blocker list passed to
  `project_closeout_status` when the cooled reading is incomplete. Add no guard
  on the affirmative: the shipped eligibility expression already consumes the
  blocker list.

**Done when:** AC9 passes and AC10 still passes.

### T4: Wave 6's residual assertion is replaced and the change is bounded

**Depends on:** T2

**Verification mode:** TDD. Two criteria: AC12 red, AC13 preservation.

**Tests:**

```python
# STUB: AC12 — Wave 6's residual assertion is replaced.  [observed RED]
def test_ac12_wave6_residual_assertion_is_replaced():
    text = _read("tests/roster/test_status_projection_and_context_exclusion.py")
    assert "def test_a_fully_cooled_initiative_still_reports_unshipped_specs" not in text
    assert 'projection["closeout"]["all_specs_shipped"] is True' in text


# STUB: AC13 — the rest of that file is undisturbed.  [observed GREEN: 67 today]
def test_ac13_wave6_roster_file_function_count_is_unchanged():
    text = _read("tests/roster/test_status_projection_and_context_exclusion.py")
    assert sum(1 for line in text.splitlines()
               if line.startswith("def test_")) == 67
```

`stub: true` for AC12. The pinned literal is the one the in-place inversion
actually produces — that file's idiom is
`projection["closeout"]["all_specs_shipped"] is True`, not a bare
`all_specs_shipped is True`, which an earlier draft's stub searched for and
which the intended edit would never contain.

**Approach:**
- Rename `test_a_fully_cooled_initiative_still_reports_unshipped_specs` and
  invert its two assertions in place, keeping its third
  (`canonical.ready == []`) and adding a docstring line naming this spec as the
  delivery that retired the residual. Change no other function, so the count
  stays 67.

**Done when:** AC12 and AC13 pass and that file's full suite passes.

### T5: The three documented surfaces match the projection

**Depends on:** T3

**Verification mode:** goal-based check — each criterion is a
whitespace-normalized literal search over a file this task writes. AC14, AC15,
AC16, AC26, AC27 red; AC25 preservation.

**Approach:**
- Rewrite the closeout-check paragraph in
  `packs/core/.apm/skills/workspace-status/SKILL.md`. Conditions (3) and (4) and
  the rationale are **one sentence**, so deleting it deletes condition (3) and
  the only check that catches a path in both `queue` and `shipped`. Edit the
  clause instead: drop "raw" and the "authoritative" claim, say the flag
  excludes entries named by a lifecycle record, keep both conditions verbatim,
  and add that the affirmative is not offered while `closeout_blockers` is
  non-empty. AC32 pins the two retained conditions.
- Add the literal AC27 requires to
  `guides/core/reference/work-intake-routing-and-lifecycle.md`.
- Add the four slices and what each owns to
  `docs/architecture/work-intake-and-artifact-routing.md`, without touching the
  three pinned statements or introducing the negated string.

**Done when:** AC14, AC15, AC16, AC25, AC26, AC27 and AC32 pass and
`tests/roster/test_wave4_durable_outputs_and_release.py` still passes.

### T6: The repair and migration paths are pinned as unaffected

**Depends on:** T2

**Verification mode:** TDD. Preservation throughout; every criterion carries a
mutation row.

**Tests:**
- AC17-AC22 are control-run identities over the cooled and uncooled fixture
  pair. AC20, AC21 and AC22 generate their own opaque operation and confirmation
  identifiers inside the test; no confirmation file is authored by hand.
- AC21 exists because the apply path reaches
  `_migration_rollback_workspace_bytes` only in its recovery branch — an
  ordinary first apply takes `legacy_workspace_bytes = workspace_bytes` and
  never calls it — so AC20 alone does not exercise the single-argument sites.
- AC23 is one predicate over an enumerated five-file table; AC24 parses the CLI
  module and counts single-argument calls.

**Approach:**
- Tests only. This task adds no production line. If one turns out to be needed,
  the decision the spec records is wrong and the spec changes first under
  RFC-0099 §7.

**Done when:** AC17-AC24 pass, the diff for this task touches only files under
`tests/` and `tools/`, and each mutation row naming AC17-AC24 has its observed
red recorded in the table.

### T7: The governance surfaces record the corrections without a frozen edit

**Depends on:** T5

**Verification mode:** TDD for AC29, AC30 and AC33 — each is a literal search
over the RFC and each was observed red. AC23 and AC28 are preservation digests
with mutation rows.

**Approach:**
- Append one dated, signed erratum to RFC-0096 § Errata carrying: the four-slice
  split with the objective each slice owns; the three open follow-on slugs with
  their owning slices; the corrected `cooling-brief-child-scope` basis; that
  `cooling-closeout-eligibility` and `cooling-repair-migration-scope` were closed
  by `cooling-scope-closure`; and that Wave 6's
  `wave6-dependency-scoped-completion-receipts` is registered here as
  `rfc0096-wave7a-ii-completion-receipts`. Do not touch §9.
- Edit neither frozen dependency: the erratum is the durable record of closure,
  and AC23 pins all six files in its table byte-for-byte, including both frozen
  plans.

**Done when:** AC23, AC28, AC29, AC30 and AC33 pass and
`python 'packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py' --root .`
exits 0.

### T8: The release surface agrees and the CLI shows the new behaviour

**Depends on:** T2-T7

**Verification mode:** goal-based check for AC31; visual / manual QA for the
invocation. `no stub (mode)`.

**Approach:**
- Re-derive the version from `git show origin/main:packs/core/pack.toml`
  immediately before committing. This is a process step, not an assertion: a
  test reading `origin/main` at assertion time depends on fetch state and
  re-baselines exactly as a merge-base comparison does.
- Bump `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`, and
  add the topmost dated `[core]` changelog heading.
- Regenerate the three `workspace_status.py` copies and the three
  workspace-status `SKILL.md` copies — `packs/core/.apm/`, `.claude/`, and
  `.agents/` — through the gate chain. Those are the files this delivery
  mutates; only `workspace_status_engine.py` has a fourth, packaged `_data/`
  copy, and this delivery does not touch it.
- Refresh the generated `/now/` projection with `python3 tools/build-site.py`
  and run `python3 -m pytest tools/test_build_site_routing.py`, because the new
  changelog heading is staleness-checked there and `make build-check` is not the
  invocation that regenerates it.
- In a scratch fixture outside the repository tree, build a fully cooled
  initiative and invoke the real CLI's `status` and `reconcile`; record stdout,
  the exit code, and the emitted `closeout` and `initiatives[]` values in
  `notes/manual-qa.md`, plus the stop point and any behaviour documented but not
  exercised.

**Done when:** AC31 passes, `SKIP_SAST=1 make build-check` exits 0 on a clean
`build/` and `dist/`, the three `workspace_status.py` and three `SKILL.md`
copies are byte-identical, `tools/test_build_site_routing.py` passes, and
`notes/manual-qa.md` records both invocations with their exit codes.

## Rollout

Pure-logic and documentation change. No flag, no persistent representation, no
mixed-version window: a repository with no `docs/lifecycle/` records sees
identical output before and after. Rollback is a revert.

## Risks

- **The projection files have three copies, not four.**
  `workspace_status.py` and the workspace-status `SKILL.md` each exist at
  `packs/core/.apm/`, `.claude/` and `.agents/`; only the engine has a packaged
  `_data/` fourth. An earlier draft named the four-copy set for files that have
  three, which would have left a projection stale with every test green.
- **`pytest` and `build-check` cannot run concurrently**: `pytest` writes
  `.apm/__pycache__` that `build-check` rejects. T8 cleans `build/` and `dist/`
  and runs the two in sequence.
- **Retiring a shipped assertion is a visible reversal.** T4 replaces it in
  place with a docstring line naming this spec, and AC13 bounds the change to
  that one function.
- **A cooled entry now counts toward closeout eligibility.** The residual is
  that an unverified lifecycle record moves an initiative closer to a closeout
  recommendation; the `cooling-context-incomplete` blocker bounds it to runs
  where the cooled set resolved cleanly, and nothing here disposes of anything.
- **The migration fixture can go vacuous.** If its lifecycle record names a path
  no artifact occupies, the cooled and uncooled runs are identical for the wrong
  reason and AC19-AC22's mutation rows stop reddening. T1's realness assertion
  is the guard.

## Changelog

- 2026-09-01: initial plan, authored after Wave 7a was split into a cooling half
  and a completion-receipt half.
- 2026-09-01: reworked from the first review round on this contract (two
  adjudicated reports; findings dominated by pre-existing rather than
  repair-introduced conditions). Nine changes of substance. **(1)** Added AC5:
  widening `queue_empty` to span queue and active — the alternative the design
  decision refuses — passed every other criterion. **(2)** Added AC4: two
  filters can agree on a record's locator and disagree on its aliases, so
  agreement needed a membership criterion as well as a movement one. **(3)**
  Added AC16: the agent-rendered gate consulted neither the blocker list nor the
  visibility flag, so the rendered surface would still have offered closeout on
  an incomplete reading. **(4)** Cut the `cooling_context_visible` guard as
  redundant — the shipped eligibility expression already consumes the blocker
  list. **(5)** Dropped the Wave 6 `**Status:**` edit entirely: the convention's
  non-supersession pointer is licensed for a deleted `[backlog].open` anchor, and
  Wave 6 registered these follow-ons in RFC §9, so no licence applies and the
  erratum is the record. That removed a criterion, a digest-region rule, and a
  risk class. **(6)** AC9's fixture became the fully cooled one; the earlier
  uncooled fixture already withheld the affirmative via `unshipped-specs`.
  **(7)** AC12's pinned literal became the one the intended edit actually
  produces. **(8)** Added AC21 for the migration recovery branch: the apply path
  reaches the single-argument call sites only there, so an earlier claim that
  AC20 exercised them was false. **(9)** T6 now depends on T2, because the
  preservation criteria were otherwise verified against the pre-change tree.
  Two coordinate corrections: the §9 body edit was `bfd6ad428`, not `20c0ba50e`
  which only appended the Errata section; and the rootless call sites are kept
  because they consume memberships only, not because a root would supply a
  cooled set — root and cooled are independent parameters.
