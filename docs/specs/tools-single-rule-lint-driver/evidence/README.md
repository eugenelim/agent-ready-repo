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

`IDENTICAL`, exit 0, with zero behavioural differences. It will also report one
or two `count-only:` lines, and those are expected:

    count-only: lint-nosec-form [clean] stdout: 1216 tracked file(s) -> 1221 tracked file(s)
    count-only: lint-nosemgrep-form [clean] stdout: 2986 UTF-8 text file(s) -> 2988 UTF-8 text file(s)

Both SAST-form lints end a clean run with a repo-wide count of the files they
scanned, so *any* commit anywhere that adds a tracked file moves that number —
including rebasing onto a moved `main`. The replay therefore reports a
difference that is only that integer separately from a behavioural one, rather
than pinning integers that go stale on the next rebase.

The substitution is deliberately narrow — it rewrites the digits in that one
phrase and nothing else — so it cannot excuse a real change. Verified by
mutation: renaming that line's `OK` to `FINE` is reported as a behavioural
difference and exits 1, even while the count is also moving; restoring it exits
0. Re-run that check before trusting this instrument after changing it.

`BASELINES.md` records why there are two baselines.

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
