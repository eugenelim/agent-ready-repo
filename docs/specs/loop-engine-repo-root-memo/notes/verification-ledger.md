# Verification ledger — loop-engine repo-root memoisation

Execution observations for `docs/specs/loop-engine-repo-root-memo/`. The
acceptance criteria are in `spec.md`; nothing here is contract.

## Measurement — paired, same machine, back to back

One probe, run twice with nothing else changing: drive a real run to
`CODE-IMPLEMENTATION` through the CLI, then execute the final `wave-complete`
in-process with `subprocess.run` wrapped to count and time every spawn. Median
over 11 repetitions each. The cache was disabled by editing one line, measured,
re-enabled by editing it back (`loop-engine.py` compared byte-identical after),
and measured again immediately — so both readings share one machine state.

| | Cache disabled | Cache enabled | Change |
| --- | ---: | ---: | ---: |
| `git rev-parse` calls per transition | 3 | **1** | exact |
| Total spawns per transition | 3 | **1** | exact |
| `rev-parse` wall time (median) | 131.6 ms | 58.4 ms | −55.6% |
| `main()` wall time (median) | 175.7 ms | 90.2 ms | −48.6% |

**Why this supersedes the first reading.** An earlier before/after put the
baseline at 314.8 ms and the result at 242.3 ms, a 23% improvement. Those two
numbers were taken hours apart under very different machine load, which is not
a comparison — the same unchanged code measured 175.7 ms in the paired run and
314.8 ms in the first. Only the call count was trustworthy across that gap. The
paired figures above are the ones to quote.

**Read the call count first.** The 3 → 1 reduction is exact and reproducible on
any machine; it is what `AC6` pins. The wall-clock pair is a real effect
measured honestly, but it is one machine on one day, not a portable constant.

## Mutation proof — three guards, three kills

Each mutation was applied by editing the source, the named case was run, and
the source was restored by editing back. After every restore,
`loop-engine.py` compared byte-identical to its pre-mutation state. No
`git checkout`, `reset`, or `stash` was used.

| Mutation | Case that must fail | Result |
| --- | --- | --- |
| Key the cache on a constant instead of the working directory | `test_get_repo_root_follows_the_working_directory` | 1 failed |
| Store a sentinel in the cache on the failure path | `test_get_repo_root_does_not_cache_a_failure` | 1 failed |
| Derive the key above the `try` instead of inside it | `test_get_repo_root_raises_value_error_on_an_unreadable_cwd` | 1 failed |

## Deviation from the sealed plan

`plan.md` § *Design decisions* D1 says the key is `os.getcwd()`. The
implementation spells it `str(Path.cwd())`, because `tools/lint-ruff.py`
enforces `PTH109` (`os.getcwd()` should be replaced by `Path.cwd()`) and failed
the gate on the first spelling. `Path.cwd()` calls `os.getcwd()` and raises the
same `FileNotFoundError` on an unlinked working directory, so the design
decision, its failure mode, and the criterion that pins it are all unchanged.
Recorded here rather than amended into the plan: the plan is sealed, and this
is the lint-mandated spelling of the same call, not a different decision.

## Stub validation defect caught before approval

The first intended-red pass reported four failures; two were a defect in the
stubs, not a real red. `mod.subprocess` is the same module object the test file
imports, so patching `mod.subprocess.run` counted every spawn in the process —
including the fixture's own `git init`. A `_rev_parse()` filter narrowed the
counts to the calls the criteria are about, after which the honest pre-change
result was 3 failed / 3 passed: AC1, AC5 and AC6 genuinely red, and AC2, AC3
and AC4 green because nothing caches yet.
