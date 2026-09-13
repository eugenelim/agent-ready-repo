# Verification ledger — knowledge-zero-row-migration

Execution observations. The spec and plan are pinned; this file is where what
actually happened gets recorded.

## T4 — mutation proof of the zero-row coverage

Run 2026-09-13 against the sealed baseline, on Python 3.13.13. Both mutations
were applied and reverted **by editing**; no `git checkout`, `git reset`, or
`git stash` was used, because the stash stack is shared across worktrees here.

### Mutation 1 — delete the statement (verifies AC5)

Removing `stage_knowledge.mkdir(parents=True, exist_ok=True)` restores the
staging behaviour shipped in 2.25.18, where the stage root exists only as a side
effect of `_write_staged_topic`.

Observed: `3 failed, 13 deselected in 1.52s`. All three zero-row cases failed,
each with the same cause:

```
FileNotFoundError: [Errno 2] No such file or directory:
  '.../docs/knowledge/.migration-stage/docs/knowledge/topics.index.json'
  pathlib/_local.py:537
```

Failing cases: `test_ac1_ac2_zero_byte_legacy_corpus_stages_canonical_empty_map`,
`test_ac3_all_refused_legacy_corpus_stages_canonical_empty_map`, and
`test_ac4_zero_row_migration_activates_and_clears_stage`.

AC5 is satisfied: the coverage reds against the defect it was written for.

### Mutation 2 — move the statement above the `try` (recorded negative result)

Observed: `16 passed in 26.69s`, exit 0. The suite does not discriminate
placement, which is what the plan predicted rather than a surprise.

Why nothing reds: `_clear_staged_migration_unlocked` removes the stage root
whoever created it, so the `except Exception:` cleanup still covers a directory
created one line earlier. Of the three injected failures, `privacy` and
`accounting` refuse before the statement is reached, and
`interrupted_staged_write` refuses after it, inside the `try`.

The placement the spec's Boundaries require is still correct. It closes the
window where `mkdir(parents=True)` creates an intermediate directory and then
fails, leaving residue outside cleanup coverage. No current hook reaches that
window, so **the placement rests on review, not on a check.** Recorded here
rather than answered by inventing a hook that would exist only to be proven by.

## Suite results at the sealed baseline

| Suite | Result |
| --- | --- |
| `test_migration.py` | 16 passed, exit 0, 23.37s |
| `packs/core/tests/skills/project-knowledge/` | 212 passed, exit 0, 5m42s |

## Environment note — the worker's blocked run

The Codex implementation worker reported `WORKER_BLOCKED` with 11 passed and 5
failed. That was a correct report of its sandbox, not a defect: under
`--sandbox workspace-write`, `shutil.rmtree()` of a `.migration-stage` directory
raises `PermissionError: [Errno 1] Operation not permitted`. The same five cases
pass when the supervisor runs them. Per the supervisor protocol, a command the
worker cannot run is not a stop condition — Claude runs it.
