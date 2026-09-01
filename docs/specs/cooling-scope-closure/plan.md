# Plan: Cooling scope closure

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/work-intake-and-artifact-routing.md`
  and `docs/CONVENTIONS.md`. One analogous production implementation: Wave 6's
  cooling projection — `_resolve_cooled_state`, `_cooling_projection`, and
  `_closeout_projection` in
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` — which
  fixes the cooled-set resolution this delivery reuses unchanged and the
  `closeout` block whose derivation it changes. Its tests are
  `tests/roster/test_status_projection_and_context_exclusion.py` and
  `tools/test_workspace_status_cli.py`. Named uncertainty: none — both changed
  expressions are single lines resolved by symbol, and the cooled set is Wave 5's
  helper called unchanged.

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
queue and active lists. Neither derivation's *shape* changes — `all_specs_shipped`
still spans queue and active, `queue_empty` still spans queue alone — so the two
still legitimately differ, which is why the spec's agreement criterion compares
movement rather than value.

The affirmative instruction gains one guard on Wave 6's already-emitted
`cooling_context_visible`, and `closeout_blockers` gains one literal.

The repair and migration half is tests only. Five control-run identities pin
`repair-plan`, `repair-apply`, and the migration planning, application, and
rollback paths as unaffected, and two source-shape criteria pin the rootless
call sites. No production line changes there; if one turns out to be needed, the
decision the spec records is wrong and the spec changes first under RFC-0099 §7.

The riskiest part is the shipped Wave 6 roster assertion this delivery must
retire. It is named by file and function in T3 and replaced in place, not
deleted.

## Constraints

- **RFC-0096 §7** keeps cooling outside ordinary orientation; **§9** scopes
  Wave 7. **RFC-0099 §7**, as recorded in RFC-0096's Errata, makes a
  post-sealing criterion change a material amendment requiring reapproval and
  resealing.
- **`status-projection-and-context-exclusion`** (frozen) owns the cooled-set
  resolution, the `cooling` and `closeout` blocks, and the emission gate; its
  AC33 owns `cooling_context_visible`.
- **`thirty-day-cooling-and-retirement`** (frozen) owns `cooling.is_due`,
  `cooling.load_record`, and the record schema; its AC24 test forbids new
  cooling keys in `workspace.toml`.
- **`docs/CONVENTIONS.md`** freezes a shipped spec directory as a unit.

## Construction tests

**Two shapes, decided by measurement.** Every stub in the spec's tally was
written and run against the unchanged tree before this plan was finished. 12 are
red and specify new behaviour; 15 are preservation criteria that are green by
construction and carry a mutation row below instead; 4 are `no stub (mode)`.
Two criteria drafted as red stubs (AC4, AC21) moved to preservation because the
run showed them green, and one (AC3) passed vacuously until strengthened. The
per-criterion observed result is recorded in each task.

**Integration tests:** one CLI-level run per emitting subcommand (`status`,
`reconcile`, `repair-plan`) over a fixture carrying a cooled queue entry, an
uncooled sibling, and a shipped entry — added to
`tools/test_workspace_status_cli.py`. The engine-level suites cannot catch a
derivation changed in one builder and not the other, which is the exact defect
Wave 6 reverted.

**Manual verification:** T7.

### Mutation table

Every preservation criterion has one mutation verified to redden it. Each is
applied by editing the source, its named test is confirmed red, and the file's
digest is re-asserted after restore.

| Mutation | Reddens |
| --- | --- |
| exclude cooled entries from `queue_empty` only | AC3 |
| exclude every queue entry, cooled or not | AC4 |
| add a cooled filter to `repair-plan`'s reconciliation | AC12 |
| add a cooled filter to `repair-apply`'s revalidation | AC13 |
| add a cooled filter to migration planning | AC14 |
| add a cooled filter to the migration apply path | AC15 |
| add a cooled filter to the migration rollback path | AC16 |
| pass `workspace_path.parent` to either rootless call site | AC17 |
| pass a `cooled` keyword to either rootless call site | AC18 |
| change one byte of `cooling.py` | AC19 |
| change one byte of `delivery-lifecycle-record.schema.json` | AC20 |
| delete any one of the three wave statements, or add the negated string | AC21 |
| change one byte inside RFC-0096 §9's body | AC24 |
| change one byte of Wave 6's `spec.md` outside its `**Status:**` block | AC27 |
| change one byte of Wave 5's `spec.md` | AC29 |
| change one byte of Wave 6's `plan.md` | AC30 |

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `runtime-coordination` derivation | T2 | AC1-AC8 red stubs turning green | Both consumers read one helper |
| Wave 6 roster assertion | T3 | AC9 | Replaced in place, other tests unchanged |
| `user-documentation` / workspace-status SKILL.md | T4 | AC10, AC11 | Gate paragraph matches the derivation |
| `user-documentation` / work-intake reference | T4 | AC23 | Statement present |
| `current-architecture` / work-intake routing | T4 | AC21 preserved, AC22 added | Three strings, absent string, split named |
| Repair and migration decision | T5 | AC12-AC20 control-run identities | No diff outside test files |
| `decision-record` / RFC-0096 Errata | T6 | AC24-AC26 | Both corrections recorded, §9 digest unchanged |
| `capability-evidence` / Wave 6 Status block | T6 | AC27, AC28, AC30 | Digests hold, pointer resolves |
| `release-history` / changelog | T7 | AC31 | Three surfaces agree |
| `project-knowledge` | T7 | Gate receipt or not-applicable finding | One of the two |

## Design (LLD)

### Design decisions

- **One helper, two callers, unchanged shapes.** The alternative — making
  `queue_empty` span queue and active so the two values become equal — changes
  what a shipped emitted field counts, which the spec's Ask-first rail governs
  and no criterion authorizes. Traces to: AC1, AC3.
- **The affirmative is gated on `cooling_context_visible`, not on a new field.**
  That flag is already emitted and is `false` only when the cooled set resolved
  cleanly, which is exactly the objection that reverted Wave 6's repair. Traces
  to: AC6, AC7.
- **The repair and migration decision is "unchanged", so its deliverable is
  control runs.** An assertion that no filter exists would pass against an
  implementation that added one and ignored it. Traces to: AC12-AC16.
- **`cooling-context-incomplete` gets no documentation row.** The finding-code
  documentation gate is scoped to `engine._FINDING_NEXT_ACTIONS`; this literal
  is a `closeout_blockers` member, and no repository surface documents any
  blocker literal today. Traces to: AC6.

### Data & schema

No schema change and no new persistent representation. `workspace.toml` gains no
key; `docs/lifecycle/` gains no writer; the record schema is pinned byte-for-byte
by AC20. Traces to: AC19, AC20 · contracts: none.

### Behavior & rules

The cooled-exclusion helper takes the initiative and the resolved cooled set and
returns `(surviving_queue, surviving_active)`. `all_specs_shipped` is
`not (surviving_queue or surviving_active)`; `queue_empty` is
`len(surviving_queue) == 0`. Membership in the cooled set is decided by the path
each entry already carries, resolved through the same confinement the cooled set
used — no second resolution. Traces to: AC1-AC5.

### Failure, edge cases & resilience

- A paused projected initiative has a `closeout` block and no `initiatives[]`
  entry, so the agreement criterion is measured only where the projection is
  `active`. AC8 pins the paused shape; probe 2 records the observed output.
- A lifecycle record that cannot be read flips `cooling_context_visible` to
  `true`, which withholds the affirmative instruction rather than degrading to a
  partial exclusion presented as complete.

Traces to: AC6, AC8.

## Tasks

### T1: The fixture harness builds a cooled initiative

**Depends on:** none

**Verification mode:** goal-based check. `no stub (mode)`.

**Tests:**
- None. The deliverable is the shared fixture helper the 12 red stubs consume.

**Approach:**
- Add the cooled-initiative fixture builder to the new suite
  `tests/roster/test_cooling_scope_closure.py`, reusing the record-writing and
  injected-instant helpers in
  `tests/roster/test_status_projection_and_context_exclusion.py` rather than
  authoring a second builder.
- The builder takes the queue, active, and shipped entry lists, the initiative
  status, and whether to write the lifecycle record, so the cooled and uncooled
  control pair differs by exactly one argument.

**Done when:** the builder produces a fixture whose `status` run parses, and the
cooled and uncooled variants differ only by the presence of
`docs/lifecycle/<delivery_id>.json`.

### T2: The two closeout consumers read one cooled-exclusion helper

**Depends on:** T1

**Verification mode:** TDD.

**Tests:** eight red stubs, all observed red against the unchanged tree.

```python
# STUB: AC1 — a cooled queue entry counts toward neither consumer.  [observed RED]
def test_ac1_cooled_queue_entry_counts_toward_neither(tmp_path):
    d = _status(_cooled_queue(tmp_path, cooled=True))
    assert d["closeout"]["all_specs_shipped"] is True
    assert d["initiatives"][0]["queue_empty"] is True


# STUB: AC3 — both consumers move together.  [observed RED after strengthening]
def test_ac3_both_consumers_move_together(tmp_path):
    cooled = _status(_cooled_queue(tmp_path / "c1", cooled=True))
    plain = _status(_cooled_queue(tmp_path / "c2", cooled=False))
    moved_shipped = (cooled["closeout"]["all_specs_shipped"]
                     != plain["closeout"]["all_specs_shipped"])
    moved_empty = (cooled["initiatives"][0]["queue_empty"]
                   != plain["initiatives"][0]["queue_empty"])
    # Both must move. `moved_shipped == moved_empty` passed vacuously today,
    # because neither moves before the change.
    assert moved_shipped and moved_empty


# STUB: AC6 — an incomplete cooled reading withholds the affirmative.  [observed RED]
def test_ac6_incomplete_reading_withholds_affirmative(tmp_path):
    root = _cooled_queue(tmp_path, cooled=False)
    _unreadable_record(root, "broken")
    c = _status(root)["closeout"]
    assert c["cooling_context_visible"] is True
    assert c["next_action"] != "invoke-close-work"
    assert "cooling-context-incomplete" in c["closeout_blockers"]


# STUB: AC8 — a paused projected initiative emits closeout without queue_empty.  [observed RED]
def test_ac8_paused_projection_has_no_queue_empty(tmp_path):
    d = _status(_workspace(tmp_path, status="paused"))
    assert d["closeout"]["paused"] is True
    assert d["closeout"]["next_action"] == "resume-or-keep-paused"
    assert d["initiatives"] == []
```

`stub: true`. All four compiled clean and observed red; AC2, AC5, AC7 follow the
same shapes and were also observed red. AC4 was observed **green** and is a
preservation criterion with a mutation row.

**Approach:**
- Add the cooled-exclusion helper and have `_closeout_projection` and the
  `initiatives[]` builder both call it. Resolve both anchors by symbol.
- Add the `cooling_context_visible` guard to the affirmative next action and
  append `cooling-context-incomplete` to the blocker list when it is `true`.

**Done when:** AC1-AC8 pass, and `packs/core/tests/skills/close-work/` still
passes including Wave 5's AC24 workspace-key test.

### T3: Wave 6's residual assertion is replaced, not deleted

**Depends on:** T2

**Verification mode:** TDD.

**Tests:**
- One red stub, observed red.

```python
# STUB: AC9 — Wave 6's residual assertion is replaced, not deleted.  [observed RED]
def test_ac9_wave6_residual_assertion_is_replaced():
    text = _read("tests/roster/test_status_projection_and_context_exclusion.py")
    assert "test_a_fully_cooled_initiative_still_reports_unshipped_specs" not in text
    assert "all_specs_shipped is True" in text
```

`stub: true`. Compiled clean; observed red.

**Approach:**
- In `tests/roster/test_status_projection_and_context_exclusion.py`, rename
  `test_a_fully_cooled_initiative_still_reports_unshipped_specs` and invert its
  two assertions in place, with a comment naming this spec as the delivery that
  retired the residual. Do not delete the function and do not touch any other
  test in that file.

**Done when:** AC9 passes and that file's other test functions are unchanged, as
shown by a per-function diff.

### T4: The three documented surfaces match the shared derivation

**Depends on:** T2

**Verification mode:** TDD for the string assertions; the criteria are their own
gate.

**Tests:** four stubs — AC10, AC11, AC22, AC23 observed red; AC21 observed
green and carried as preservation.

**Approach:**
- Rewrite the closeout-check paragraph in
  `packs/core/.apm/skills/workspace-status/SKILL.md` against the shared
  derivation, removing the sentence that calls raw queue emptiness the
  authoritative check.
- Add the cooled-exclusion statement to
  `guides/core/reference/work-intake-routing-and-lifecycle.md`.
- Add the four-slice split to
  `docs/architecture/work-intake-and-artifact-routing.md` without touching the
  three pinned statements or introducing the negated string.

**Done when:** AC10, AC11, AC21, AC22, AC23 pass and
`tests/roster/test_wave4_durable_outputs_and_release.py` still passes.

### T5: The repair and migration paths are pinned as unaffected

**Depends on:** T1

**Verification mode:** TDD. Preservation throughout — AC12-AC20 are green before
the change and each carries a mutation row.

**Tests:**
- AC12-AC16 are control-run identities over the cooled and uncooled fixture
  pair. AC15 and AC16 generate their own opaque operation and confirmation
  identifiers inside the test; no confirmation file is authored by hand.
- AC17 and AC18 parse
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` and
  assert the call shape, so the count and the argument absence are read from the
  file rather than restated. Both sites are inside
  `_migration_rollback_workspace_bytes`, which the migration apply and rollback
  paths both reach, so AC15 and AC16 exercise them behaviourally as well.
- AC19 and AC20 are literal digest assertions.

**Approach:**
- Tests only. No production change belongs to this task.

**Done when:** AC12-AC20 pass with no diff outside test files, and each mutation
named in the table above reddens its case.

### T6: The governance surfaces record both corrections without a frozen-body edit

**Depends on:** T4

**Verification mode:** goal-based check. `no stub (mode)` for AC25, AC26, AC28;
AC24, AC27, AC29, AC30 are preservation digests.

**Tests:**
- AC24, AC27, AC29 and AC30 are literal pinned digests computed in the new
  roster suite, so each holds after the branch is gone. AC27 excludes the whole
  `**Status:**` block — the `- **Status:**` line plus every following line up to
  but excluding the next line beginning `- **` — because a per-line filter would
  be reddened by this delivery's own wrapped pointer.

**Approach:**
- Append one dated, signed erratum to RFC-0096 § Errata carrying the four-slice
  split and the corrected `cooling-brief-child-scope` basis. Do not touch §9.
- Amend only the `**Status:**` block of Wave 6's `spec.md`, in the convention's
  non-supersession pointer form, naming the two slugs this delivery closes and
  linking this spec.

**Done when:** AC24-AC30 pass and
`python 'packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py' --root .`
exits 0.

### T7: The release surface agrees and the CLI shows the new behaviour

**Depends on:** T2-T6

**Verification mode:** goal-based check for AC31; visual / manual QA for the
invocation. `no stub (mode)`.

**Tests:**
- AC31 reads all three values, asserts they are equal, and asserts the parsed
  tuple exceeds `(2, 18, 2)`.

**Approach:**
- Re-derive the version from `git show origin/main:packs/core/pack.toml`
  immediately before committing. This is a process step, not an assertion: a
  test reading `origin/main` at assertion time depends on fetch state and
  re-baselines exactly as a merge-base comparison does.
- Bump `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`, add
  the topmost dated `[core]` changelog heading, and regenerate the four engine
  projections through the gate chain rather than by hand.
- In a scratch fixture outside the repository tree, build a fully cooled
  initiative and invoke the real CLI's `status` and `reconcile`; record stdout,
  the exit code, and the emitted `closeout` and `initiatives[]` values in
  `notes/manual-qa.md`, plus the stop point and any behaviour documented but not
  exercised.

**Done when:** AC31 passes, `SKIP_SAST=1 make build-check` exits 0 on a clean
`build/` and `dist/`, the four engine copies are byte-identical, and
`notes/manual-qa.md` records both invocations with their exit codes.

## Rollout

Pure-logic and documentation change. No flag, no persistent representation, no
mixed-version window: a repository with no `docs/lifecycle/` records sees
identical output before and after. Rollback is a revert.

## Risks

- **The engine has four copies** — the pack source, two projected skill trees,
  and the packaged `_data/` tree. A hand-edited copy passes local tests and
  fails the packaged-runtime pair check, so T7 regenerates through the gate
  chain.
- **`pytest` and `build-check` cannot run concurrently**: `pytest` writes
  `.apm/__pycache__` that `build-check` rejects. T7 cleans `build/` and `dist/`
  and runs the two in sequence.
- **Retiring a shipped assertion is a visible reversal.** T3 replaces it in
  place with a comment naming this spec, so a later reader sees the decision
  rather than an unexplained inversion.
- **A cooled entry now counts toward closeout eligibility.** The residual is
  that an unverified lifecycle record moves an initiative closer to a closeout
  recommendation; the `cooling_context_visible` guard bounds it to runs where the
  cooled set resolved cleanly, and nothing in this delivery disposes of anything.

## Changelog

- 2026-09-01: initial plan, authored after Wave 7a was split. The combined
  receipt-and-cooling contract drew 52 sustained findings in round 1 and 29 in
  round 2, of which 19 were caused by the round-1 repair; the cooling half drew
  3 across both rounds. The receipt is now `rfc0096-wave7a-ii-completion-receipts`
  with its own contract. Every stub in this plan was run before the plan was
  finished, which moved AC4 and AC21 to preservation and caught AC3 passing
  vacuously.
