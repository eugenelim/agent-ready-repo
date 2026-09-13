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

## T6 — the documentation pin, after a sustained review finding

The first implementation of AC6's check pinned an exact long sentence,
`"copy the staged \`docs/knowledge/\` tree into \`docs/knowledge/\`"`, and split
the section on an exact heading string. The `quality-engineer` pass raised it as
a Concern, independently of the supervisor having flagged the same thing: AC6
requires the promotion *sequence*, not particular wording, and a control that
reds on ordinary clarity edits gets deleted rather than maintained. T6's own
plan bullet had said exactly that, so the implementation contradicted its own
stated mechanism.

Repaired by matching each step on the action it names: a case-insensitive
regex heading, the two literal CLI flags, a line-scoped pattern requiring the
copy step to name both a staged source and the `docs/knowledge/` destination,
and a word-boundary match on the commit.

Loosening a control earns the burden of proving it can still fail. Four
mutations, run 2026-09-13 against `SKILL.md`, each reverted by editing:

| Mutation | Expected | Observed |
| --- | --- | --- |
| Delete the whole migration section | red | `1 failed` |
| Move the commit step after activate | red | `1 failed` |
| Replace the copy step with "Promote the staged tree." (drops source and destination) | red | `1 failed` |
| Reword the copy and commit steps innocuously, sequence intact | **pass** | `1 passed` |

The fourth is the point of the repair: the check now survives editing it should
survive, and still reds on every semantic break AC6 names.

### T6, second repair — the loosened pattern did not require the destination

The `quality-engineer` re-review of the first repair sustained a further
Concern, and it was correct. The pattern
`copy\b[^\n]*\bstaged\b[^\n]*docs/knowledge/` requires only **one**
`docs/knowledge/` operand, which the *source* already supplies. So
"Copy the staged `docs/knowledge/` tree to a backup" passed, and AC6's
destination was not actually required by the check.

The first repair's mutation set missed it because every mutation there removed
the copy step wholesale — "Promote the staged tree." drops `copy` and `staged`
together, so no case isolated the destination. A predicate has to be walked
against every case that distinguishes it, not the one case that happens to come
to mind. The reviewer named the exact input; it was reproduced before repairing.

The step now requires the destination to follow a directional word:

```
copy\b[^\n]*\bstaged\b[^\n]*\b(?:into|onto|over|to)\b[^\n]*docs/knowledge/
```

Walked against all eight distinguishing cases, 0 mismatches:

| Input | Expected | Observed |
| --- | --- | --- |
| shipped `SKILL.md` line | match | match |
| shipped seed line | match | match |
| reworded, destination named ("over your `docs/knowledge/` directory") | match | match |
| reworded with "onto" | match | match |
| "…tree to a backup." (the reviewer's case) | no match | no match |
| "…tree." (destination removed) | no match | no match |
| "Copy the files into `docs/knowledge/`." (no staged source) | no match | no match |
| "…into `docs/archive/`." (wrong destination) | no match | no match |

End to end against both real shipped surfaces, each mutation reverted by
editing: backup destination **red**, destination removed **red**, wrong
destination **red**, unmutated **pass**.

### T6, third round — the operand claim was unmechanizable, so it was cut

The `quality-engineer` re-review of the second repair returned two inputs, both
reproduced before acting:

| Input | Should be | Was |
| --- | --- | --- |
| "Do not copy the staged `docs/knowledge/` tree into `docs/knowledge/`." | no match | **match** |
| "Copy the staged `docs/knowledge/` tree, replacing the current `docs/knowledge/` directory." | match | **no match** |

A predicate that admits a negation and refuses a valid synonym is not measuring
the property it names. The reviewer's verdict was SHRINK, and it is right:
regex cannot decide prose-level operand semantics, and a third tightening would
have produced a fourth hole.

The copy step is now matched on its action alone. The check decides what it can
decide — that the four steps are present and ordered — and the plan no longer
claims it validates operands. Whether the copy step names the right source and
destination rests on review, against the wording AC6 states. AC6 itself is
unchanged: it is a documentation-content criterion, and both shipped surfaces
do carry the sequence it specifies.

Mutations after the shrink, each reverted by editing:

| Mutation | Expected | Observed |
| --- | --- | --- |
| unmutated | pass | `1 passed` |
| delete the migration section | red | `1 failed` |
| replace the copy step with "Promote the tree." | red | `1 failed` |
| move the commit step after activate | red | `1 failed` |
| reword with "replacing the current `docs/knowledge/` directory" | pass | pass |

Three rounds on one control is itself the finding: the first two rounds moved
the control between too tight and too loose, and only the third asked whether
the property was decidable at all. Ask that question earlier.
