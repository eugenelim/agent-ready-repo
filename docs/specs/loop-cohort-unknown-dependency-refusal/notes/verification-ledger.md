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
