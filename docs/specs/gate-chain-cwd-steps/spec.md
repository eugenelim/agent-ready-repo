# Spec: gate-chain-cwd-steps

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** the local gate chain gains a step kind. No published interface
  changes; `tools/` is non-release-impacting.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. Risk trigger: structural — a new step kind in the gate chain
changes what `make build-check` runs, and relaxes an assertion that guards
Windows portability. -->

## Objective

A suite that must run from its own directory could not be expressed in the local
gate chain, so it ran only in CI. `make build-check` silently skipped it.

## Acceptance Criteria

- [x] **AC1 — the chain can express "run from here".** `_pytest_step_cwd(label,
  cwd, *targets)` uses `subprocess`'s own `cwd=`, so there is no `cd &&`, no
  shell, and no POSIX-only quoting — the argv stays a plain list and the step
  stays Windows-clean.

- [x] **AC2 — the catalogue-curation gates are now locally covered.** Both
  `assimilate-primitive` (30 tests) and `assimilate-repo` (7) move from
  `CI_ONLY` to `LOCAL("build-check")`; `lint-ci-parity` reports 31 locally
  covered where it reported 30.

  These are the step kind's callers, and picking them was a correction. The
  entry named the credential-setup suite, and I wired that first — CI rejected
  it twice. Its blocker was never the step vocabulary: it spawns `setup.py` as a
  subprocess, and that script hard-exits 3 unless credbroker is **installed**; a
  source path on `PYTHONPATH` does not satisfy it. Recorded as
  `gate-chain-credential-setup-provisioning`, since it is a question about what
  `make build-check` provisions.

- [x] **AC3 — the parity linter can see a cwd-scoped target.** Its reachability
  scan matches literal repo-root paths, and this step's targets are bare
  filenames. The extractor joins `cwd` and target, so the gate is not reported
  CI-only while it is in fact wired locally.

- [x] **AC4 — the relaxed assertion still asserts the thing that matters.**
  `test_script_steps_are_windows_clean` pinned argv *length*, which was only ever
  a proxy for "nothing clever is going on" — and the proxy had become the
  constraint. It now checks the claim directly: no `bash`/`sh`/`-c`, no `.sh`, no
  shell metacharacter in any token, and any `cwd` is a real absolute path.

- [x] **AC5 — the new step kind is itself covered.** A test asserts a cwd-scoped
  step exists, runs from the expected directory, and passes bare filenames rather
  than repo-root paths.

- [x] **AC6 — the gap is demonstrated, not asserted.** From the repo root the
  suite collects nothing ("no tests ran"); from its directory, 16 pass. That
  difference is the entire reason the vocabulary was needed.

- [x] **AC7 — the step kind carries a collected-count floor.** A
  directory-scoped run with no filenames exits 0 when it collects **nothing**, so
  a suite that fails to land — renamed, moved, broken import — would reduce the
  count and the gate would still pass. CI asserts a floor with a shell subshell
  and `grep -c`; the step kind does it as a count in Python, so it stays
  Windows-clean. Verified both ways: floor 7 on a 7-test suite passes; floor 999
  fails with a message naming the directory and both counts.

- [x] **AC8 — the step supplies the repo's source packages on `PYTHONPATH`.**
  Moving the cwd out of the repo root is what makes this necessary: a suite that
  imports `agentbundle` finds it by path rather than by install, so the chain
  takes on no provisioning. Appended after any caller `PYTHONPATH`, so a real
  installed copy still wins.

- [x] **AC9 — a linter bug found on the way is fixed, with regression cases.**
  Declaring the catalogue-curation step `LOCAL` surfaced a phantom prefix:
  `lint-ci-parity`'s `cd` resolver guards `dest.startswith("$")`, but that step's
  helper writes `cd "$dir"` — the quoted token starts with `"`, so the guard
  missed it and composed the target `"$dir"/`. That is the exact hazard the
  resolver's own docstring warns about, reached by the form a careful shell
  author is most likely to write. Three cases added (double-quoted variable,
  single-quoted variable, and a quoted *literal* which must still resolve);
  mutation-verified — reverting the fix fails 5 of 102 cases.

## Boundaries

### Never do

- Never express a cwd with `cd &&` or a shell string. AC1 is the reason the step
  kind exists.
- Never re-pin argv length as the Windows-cleanliness proxy. AC4.

## Testing Strategy

- **TDD** for AC4/AC5; **goal-based** for AC2/AC3/AC6 (linter output and a real
  run from each directory).
