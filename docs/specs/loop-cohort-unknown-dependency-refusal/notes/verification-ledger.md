# Verification ledger — loop-cohort unknown dependency refusal

## Mutation proof (T3, AC9) — re-derived against the shipped guard

The first run of this proof was taken before the refusal message gained its
remedy clause, so its recorded line range and snippet described a guard that no
longer shipped. Replaying it would have deleted unrelated control flow. It has
been re-derived against the form that ships, and the record below is the
re-derivation, not the original.

### What was mutated

**File:** `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`

**Revision mutated:** `946370f8b` (the tree as it ships)

**Lines removed:** 650–657 — the single `detect_unknown_deps` call site inside
`schedule_unfinished_plan`, immediately before its `detect_cycles` call. The
three explanatory comment lines above it (647–649) were left in place, so the
deletion is exactly the guard and nothing else.

**Exact 8 lines deleted:**

```python
    unknown = detect_unknown_deps(plan_text, scan_task_ids=remaining_set)
    if unknown:
        raise ValueError(
            "dependency names no task in the plan: "
            + ", ".join(f"{a}->{b}" for a, b in unknown)
            + " — correct the ID in plan.md, or drop it from that task's"
            " `Depends on:` line"
        )
```

### Commands run

```
python3 -m pytest packs/core/tests/skills/work-loop/test_loop_cohort_cli.py -q
python3 -m pytest packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py -q
python3 -m pytest packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_detect_unknown_deps_has_exactly_one_call_site -q
```

### RED result, re-derived (guard deleted from the shipped form)

```
test_loop_cohort_cli.py            exit 1
  FAILED ...::LoopCohortCliTest::test_47_schedule_refuses_single_unknown_dep
  FAILED ...::LoopCohortCliTest::test_48_schedule_refuses_two_unknown_deps_names_both
  FAILED ...::LoopCohortCliTest::test_50_schedule_unknown_dep_beats_cycle_refusal
  3 failed, 59 passed, 22 subtests passed in 94.72s

test_contract_amendment_wave4.py   exit 1
  FAILED ...::test_schedule_unfinished_plan_raises_for_unknown_dep
  FAILED ...::test_schedule_unfinished_plan_ac4_unknown_dep_beats_cycle
  2 failed, 25 passed in 0.64s

test_..._has_exactly_one_call_site  exit 1
  1 failed in 0.26s   (0 call sites, not 1)
```

One deletion, three independent reds: the CLI path, the amendment path, and the
standing guard on the call-site count itself.

#### Observed failures, one per failing test

Quoted from the retained pytest output of the re-derived run, not reconstructed.
These are what confirm each red was the *contracted* red rather than a
collateral error. Only volatile values are elided, marked `…`: per-run temporary
directory paths, generated run UUIDs, and the unchanged tail of the dispatch
notice. Every assertion, expected value, and actual value is verbatim.

`test_47_schedule_refuses_single_unknown_dep` and
`test_48_schedule_refuses_two_unknown_deps_names_both` — expected exit 1, got 0,
and the captured stdout shows the defect itself reproduced:

```
AssertionError: 0 != 1 : args=('schedule', '…/spec1', '--expect-run-id', '…')
stdout=loop-cohort: topological order for spec1 …
  wave 1: T1, T2
loop-cohort: schedule persisted for spec1 (1 wave(s), plan_hash=d0135fafea76…)
stderr=
```

With the guard removed, the plan whose `T2` names an absent `T7` schedules as
**one wave containing both tasks**. That is the collapse this change exists to
prevent, captured in the proof's own output: the dropped edge, the merged wave,
and — because GATES runs per wave — a single gate run where there should be two.

`test_50_schedule_unknown_dep_beats_cycle_refusal` and
`test_schedule_unfinished_plan_ac4_unknown_dep_beats_cycle` — the cycle refusal
fires in the guard's place, which is exactly the AC4 precedence claim:

```
AssertionError: Regex pattern did not match.
  Expected regex: 'T3->T99'
  Actual message: 'dependency cycle among unfinished tasks: T1, T2'
```

`test_schedule_unfinished_plan_raises_for_unknown_dep` — no refusal at all:

```
Failed: DID NOT RAISE <class 'ValueError'>
```

`test_detect_unknown_deps_has_exactly_one_call_site` — the standing guard
observes the deletion directly:

```
AssertionError: detect_unknown_deps must have exactly one call site; found 0: []
assert 0 == 1
+  where 0 = len([])
```

### GREEN result, after restoring by edit

```
test_contract_amendment_wave4.py    27 passed in 0.51s
test_..._has_exactly_one_call_site   1 passed in 0.35s
test_loop_cohort_cli.py             62 passed, 22 subtests passed in 92.79s (exit 0)
```

### Restoration verification

`git diff --stat packs/core/.apm/skills/work-loop/scripts/loop-cohort.py` is
empty: the file is byte-identical to its committed state at `946370f8b`. The
guard was restored by editing the lines back, never by `git checkout`, which the
mutation-proof method forbids.

## Manual CLI verification (controller-run) — re-run against the shipped build

Observed by driving the real `loop-cohort.py` CLI with `cwd` inside a temporary
git repo. Re-run after the refusal message gained its remedy clause, so the
stderr below is what the shipped build prints, not an edited quote of an earlier
run.

An earlier attempt at this same matrix, run from the repository root, failed all
nine cases identically on the spec-dir confinement guard. The CONTROL row is what
revealed that: nine identical refusals read exactly like "the new guard fires on
everything", and without a row that must succeed there was nothing to
distinguish a broken instrument from a broken guard.

| case | exit | waves | stderr |
|---|---|---|---|
| CONTROL correct | 0 | `[['T1'], ['T2']]` | (none) |
| unknown dep | 1 | `[]` | `stop — schedule: dependency names no task in the plan: T2->T7 — correct the ID in plan.md, or drop it from that task's` `` `Depends on:` `` `line` |
| two unknown deps | 1 | `[]` | same form, naming `T1->T8, T2->T7` |
| forward ref | 0 | `[['T2'], ['T1']]` | `warning — forward-reference(s) in <spec-dir> (dep authored later; reordered below): T1->T2` |
| cycle | 1 | `[]` | `stop — schedule: dependency cycle among unfinished tasks: T1, T2` |
| both faults | 1 | `[]` | the unknown-dependency refusal, naming `T1->T9` — not the cycle message |
| cross-spec `spec:other/T7` | 0 | `[['T1'], ['T2']]` | (none) |
| cross legacy `` `other` T7 `` | 0 | `[['T1'], ['T2']]` | (none) |
| range absent mid (`T1-T3`, no `T2`) | 1 | `[]` | the unknown-dependency refusal, naming `T3->T2` |

The forward-reference row is the one to read twice: exit 0 with waves
`[['T2'], ['T1']]` means the dependency was reordered ahead of the task that
declared it, which is the contract this change was required to leave alone.

## Final GATES — one load-induced failure, investigated and cleared (controller)

The final full-suite run of `packs/core/tests/skills/work-loop/` reported
`1 failed, 1082 passed, 5 skipped, 46 subtests passed in 1644.56s`. The failure
was `test_loop_engine.py::test_wave_passed_window_a_advance_before_crash`.

It is not caused by this change. Evidence, in the order it was gathered:

1. **The failure is a subprocess timeout, not an assertion.** The message is
   `spec-dir confinement check failed: could not determine repo root: Command
   ['git', 'rev-parse', '--show-toplevel'] timed out after 20.0 seconds`.
2. **The failing call cannot reach this change.** It fires at the `plan-approved`
   engine transition, before any `schedule` call. This change adds one call
   inside `schedule_unfinished_plan`, on the schedule path only.
3. **The fixture holds no unknown dependency.** Its plan is `T1` (`none`) and
   `T2` (`T1`), so the new predicate returns `[]` for it however it is reached.
4. **Differential run.** A detached worktree at the merge base
   (`c1d4fbf1614c4ac4e173e06a7a623b54d2422343`, confirmed pre-change: zero
   occurrences of `detect_unknown_deps`) passed the same test.
5. **Paired re-runs settle it as load-sensitive, not a regression.** Failures
   occurred only at long wall times; passes were fast, on both trees:

   | tree | run | wall time | result |
   | --- | --- | --- | --- |
   | changed | in full suite | 1644s total | fail |
   | changed | isolated 1 | 113.95s | fail |
   | merge base | isolated 1 | 37.76s | pass |
   | changed | isolated 2 | 36.02s | pass |
   | changed | isolated 3 | 7.92s | pass |
   | merge base | isolated 2 | 5.77s | pass |

6. **Machine conditions.** Load average 33 with 39 users and 33 concurrent
   `claude`/`git` processes, while a lone `git rev-parse --show-toplevel`
   measured 0.06-0.11s. The 20-second timeout starves under contention.

The verdict rests on points 2 and 3 — an unreachable code path — with the
re-runs as corroboration. Three green re-runs alone would not settle it, because
a re-run can launder a real failure into green.

No `[backlog].open` entry was added: the test is green at ordinary load, so a
cold-start reader will not meet it red, and the register already carries the
same class under `semgrep-registry-ruleset-pinning` (load-induced timeout
diagnostics on files absent from any diff).

## Acceptance-criteria verification (controller, pre-ship)

Every criterion re-checked mechanically against the shipped tree immediately
before the status transition, rather than carried forward from a reviewer's
report. The script drives the real `loop-cohort.py` module, reads the real
manifests and changelog, and hashes the real projection copies.

    PASS  AC1    T2->T7
    PASS  AC2    both, sorted
    PASS  AC3    forward ref not refused
    PASS  AC4    unknown@29273 < cycles@29617
    PASS  AC5    both forms inert
    PASS  AC6    none/ID/range/prose
    PASS  AC6a   T3->T2
    PASS  AC7    completed dep counts as met
    PASS  AC7a   proven by difference
    PASS  AC8    parse_plan(text: 'str') parse_depends_on(field: 'str', local_task_ids)
    PASS  AC9    ledger has RED/GREEN; 1 call site
    PASS  AC10   absent=True; phrase in 3 files
    PASS  AC11   template unknown=[] cycles=[]
    PASS  AC12   2.26.8 in all three, Highlights present
    PASS  AC13   4 files x 3 copies identical
    PASS  AC14   entry present, 5 assertions
    
    16/16 acceptance criteria verified

AC4 is verified structurally: the unknown-dependency call precedes the
`detect_cycles` call in the module source, which is what gives the refusal its
precedence at both entry points. AC9 is verified as the conjunction of the
recorded RED/GREEN mutation result and a single call site, since the proof is
only meaningful while that count holds.
