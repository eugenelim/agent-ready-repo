# Verification ledger — loop-cohort unknown dependency refusal

## Mutation proof (T3, AC9)

### What was mutated

**File:** `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`

**Lines removed:** 639–644 (the single `detect_unknown_deps` call site inside
`schedule_unfinished_plan`, immediately before the `detect_cycles` call)

**Exact 6 lines deleted:**

```python
    unknown = detect_unknown_deps(plan_text, scan_task_ids=remaining_set)
    if unknown:
        raise ValueError(
            "dependency names no task in the plan: "
            + ", ".join(f"{a}->{b}" for a, b in unknown)
        )
```

### Commands run

```
python3 -m pytest packs/core/tests/skills/work-loop/test_loop_cohort_cli.py -q
python3 -m pytest packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py -q
```

### RED result (call site deleted)

**`test_loop_cohort_cli.py`** — 3 failed, 59 passed, 22 subtests passed in 80.79s

Failing test IDs:
- `packs/core/tests/skills/work-loop/test_loop_cohort_cli.py::LoopCohortCliTest::test_47_schedule_refuses_single_unknown_dep`
- `packs/core/tests/skills/work-loop/test_loop_cohort_cli.py::LoopCohortCliTest::test_48_schedule_refuses_two_unknown_deps_names_both`
- `packs/core/tests/skills/work-loop/test_loop_cohort_cli.py::LoopCohortCliTest::test_50_schedule_unknown_dep_beats_cycle_refusal`

Observed failure messages (one per test):

- `test_47`: `AssertionError: 0 != 1 : args=('schedule', …)` — the CLI exited 0 instead of 1; `stderr=` (empty). The command scheduled waves when it should have refused.
- `test_48`: `AssertionError: 0 != 1 : args=('schedule', …)` — same: exit 0, empty stderr, waves written.
- `test_50`: `AssertionError: 'T3->T99' not found in 'loop-cohort: stop — schedule: dependency cycle among unfinished tasks: T1, T2\n'` — the cycle refusal fired instead of the unknown-dep refusal, proving the precedence guarantee was gone.

**`test_contract_amendment_wave4.py`** — 2 failed, 25 passed in 0.73s

Failing test IDs:
- `packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py::test_schedule_unfinished_plan_raises_for_unknown_dep`
- `packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py::test_schedule_unfinished_plan_ac4_unknown_dep_beats_cycle`

Observed failure messages:

- `test_schedule_unfinished_plan_raises_for_unknown_dep`: `Failed: DID NOT RAISE <class 'ValueError'>` — `schedule_unfinished_plan` returned normally instead of raising on an unknown dependency.
- `test_schedule_unfinished_plan_ac4_unknown_dep_beats_cycle`: `AssertionError: Regex pattern did not match. Expected regex: 'T3->T99', Actual message: 'dependency cycle among unfinished tasks: T1, T2'` — again, cycle refusal fired instead of unknown-dep refusal.

### GREEN result (call site restored)

**`test_loop_cohort_cli.py`** — 62 passed, 22 subtests passed in 83.03s

**`test_contract_amendment_wave4.py`** — 27 passed in 0.73s

### Restoration verification

The call site was restored by editing the file back to its original 6 lines
(identical to commit `99ae37e25`). After restoration:

```
git status
```

Output:
```
On branch eugenelim/loop-dependency-missing-fix
Untracked files:
  (use "git add <file>..." to include in what will be committed)
	docs/specs/loop-cohort-unknown-dependency-refusal/

nothing added to commit but untracked files present (use "git add" to track)
```

```
git diff packs/core/.apm/skills/work-loop/scripts/loop-cohort.py
```

Output: (empty — no diff)

The mutation did not survive. `loop-cohort.py` is byte-identical to its
committed state at `99ae37e25`.

---

## Manual CLI verification (controller-run, T2)

The following matrix was observed by running the real `loop-cohort.py` CLI with
`cwd` inside a temporary git repo after T2 was committed. An earlier run of the
same matrix from the repository root failed all nine cases identically on the
spec-dir confinement guard; the CONTROL row was what revealed the broken
instrument, because a broken instrument would hide that failure silently if the
CONTROL had not been included.

| case | exit | waves | stderr |
|---|---|---|---|
| CONTROL correct | 0 | `[['T1'], ['T2']]` | (none) |
| unknown dep | 1 | `[]` | `stop — schedule: dependency names no task in the plan: T2->T7` |
| two unknown deps | 1 | `[]` | `stop — schedule: dependency names no task in the plan: T1->T8, T2->T7` |
| forward ref | 0 | `[['T2'], ['T1']]` | `warning — forward-reference(s) ... reordered below: T1->T2` |
| cycle | 1 | `[]` | `stop — schedule: dependency cycle among unfinished tasks: T1, T2` |
| both faults | 1 | `[]` | `stop — schedule: dependency names no task in the plan: T1->T9` |
| cross-spec `spec:other/T7` | 0 | `[['T1'], ['T2']]` | (none) |
| cross legacy `` `other` T7 `` | 0 | `[['T1'], ['T2']]` | (none) |
| range absent mid (T1-T3, no T2) | 1 | `[]` | `stop — schedule: dependency names no task in the plan: T3->T2` |

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
