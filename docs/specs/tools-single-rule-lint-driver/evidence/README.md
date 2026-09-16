# Behaviour-preservation evidence

The claim this change rests on is that the twelve migrated lints behave
identically to before. This directory holds the instrument and the recorded
corpus so that claim can be re-checked rather than taken on trust.

## Re-running it

From the repository root:

    PYTHONPATH=docs/specs/tools-single-rule-lint-driver/evidence \
      python3 docs/specs/tools-single-rule-lint-driver/evidence/replay.py .

It replays 48 cases — twelve rules across four input modes (clean tree, a
fixture holding a violation, a target directory that exists but is empty, and
a target directory that is absent) — and compares raw stdout, stderr and exit
status against `corpus-before.json`.

## Expected result

One case differs, and it is not the refactor:

    lint-nosec-form [clean] stdout:  "... in 1216 tracked file(s) ..."
                                  -> "... in 1219 tracked file(s) ..."

Both SAST-form lints print a repo-wide count of the files they scanned, so any
commit that adds a tracked file moves that number; this change adds three. With
those three untracked the replay reports IDENTICAL for all 48. `BASELINES.md`
records that differential and why there are two baselines.

## Files

- `capture.py` — records the corpus. Its rule table also documents each lint's
  real invocation, which is not uniform: `--root` means the repository root for
  three of them and the *target directory* for `lint-guide-titles`, and
  `lint-nosec-form` / `lint-nosemgrep-form` resolve their scan root from their
  own file location so argv cannot move it.
- `fixtures.py` — builds a minimal violating tree per rule.
- `replay.py` — re-runs the capture and diffs it against the recorded corpus.
- `corpus-before.json` — the recorded baseline (harnesses present, no rule
  migrated).
- `corpus-pristine.json` — the same capture taken before anything changed.
- `BASELINES.md` — why there are two baselines, and the one field that moves.
