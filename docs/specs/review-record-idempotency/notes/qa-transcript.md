# Manual QA — `review record --operation-id`

Driven by hand against the shipped CLI on a throwaway spec directory under the
gitignored `.context/`, removed afterwards. A green unit suite does not establish
that the assembled command behaves, which is why this exists.

Run id elided as `<run>`; `count` is `review_round_count` read from `state.json`
after each command.

| # | Command | Exit | `count` | Observed |
| --- | --- | --- | --- | --- |
| 1 | *(initial state)* | — | 0 | `last_review_record_operation_id` is `None` |
| 2 | `review record --fingerprint <a> --fingerprint <b> --operation-id <run>:12` | 0 | 1 | `review record (findings) round=1 retry=1 fingerprints=2` |
| 3 | **identical command re-issued** | 0 | **1** | `already recorded for operation '<run>:12' (idempotent no-op)` |
| 4 | same id, different payload (`--fingerprint <c>`) | non-zero | 1 | `stop — … already recorded with a different payload; a replay must carry the payload it recorded` |
| 5 | `--fingerprint <c> --operation-id <run>:13` | 0 | 2 | `review record (findings) round=2 retry=2 fingerprints=1` |
| 6 | `--operation-id nope` | non-zero | 2 | `stop — --operation-id must be '<expect-run-id>:<decimal-sequence>' (got 'nope')` |
| 7 | `--all-skipped`, no `--operation-id` | 0 | 3 | recorded id unchanged across the round: `<run>:13` before and after |

## What this establishes

Step 3 is the contract's reason for existing: a session that re-issues a
recording because it never learned whether the first one landed gets one round,
not two. Step 4 shows the id alone is not enough — a different payload under a
used id is refused rather than silently absorbed. Step 7 shows a flagless round
does not displace the recorded pair, so the pair keeps naming the last round
recorded *under an id*.

The three refusal and no-op messages in steps 3, 4 and 6 are mutually distinct,
so an operator can tell a completed write from a payload conflict from a
malformed id without reading `state.json`.

## What this session does not exercise

- **`--direct-clean-file` and `--report --adjudication`.** Covered by unit cases
  only. Both need a persisted artifact, and their behaviour differs from
  `--fingerprint` solely in which payload the digest is taken over.
- **The uncomputable-digest refusal.** Its only production trigger is a report
  becoming unreadable between classification and hashing, which cannot be induced
  from a shell. Covered by a direct test of the gate.
- **A real crash.** Step 3 re-issues the command deliberately rather than killing
  a process mid-write; the writer's single atomic write is what makes those
  equivalent, and that atomicity is the sibling suite's to prove, not this one's.
