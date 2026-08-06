# Plan: test-sandbox-seed-cost

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

## Approach

Measure first, then cut the one cost the measurement actually indicts. Profiling
showed process spawn costs ~26ms on this machine, so `seed_sandbox`'s two spawns
per file across 6 seedings dominated the script. Replace that loop with a single
Python process; leave the seed set, the symlink semantics, the git-repo
requirement, and the per-case fresh tree exactly as they are.

A seed-once-into-a-pristine-tree-then-restore-per-case variant was measured and
rejected: restoring with `cp -a` (15.8s) only tied a plain re-seed (15.2s) while
adding 61 MB of disk and a BSD-vs-GNU flag question, and restoring with
`shutil.copytree` (52.1s) was 3.4× worse. Re-seeding per case is both the fastest
option and the one that leaves the isolation semantics untouched.

## Tasks

1. **Extract the copy into `tools/seed_test_sandbox.py`.** Depends on: none.
   Mode: goal-based. Done when: `python3 tools/lint-ruff.py` passes and the file
   is stdlib-only (AGENTS.md § "New tool scripts: Python, not bash" keeps new
   `tools/` logic under the Python gates, which a shell heredoc escapes).
2. **Verify symlink preservation from what is copied, not a hardcoded list.**
   Depends on: 1. Mode: TDD-by-mutation. Done when: a variant that dereferences
   file symlinks exits 1 naming the offending path, and the unmutated script
   passes. The literal list was already stale — it omitted `docs-site/CLAUDE.md`,
   added in `8238167a`.
3. **Fail loudly on a seeder error.** Depends on: 1. Mode: goal-based. Done when:
   the call site checks the exit status explicitly (`set -e` is not in effect at
   that point — line 10 sets only `-uo pipefail`).
4. **Wire the new script into the `docs.yml` path trigger.** Depends on: 1.
   Mode: goal-based. Done when: `tools/seed_test_sandbox.py` appears in the
   workflow `paths:` list, so editing the seeder still runs the job that uses it.
5. **Re-run the gates and record before/after timings.** Depends on: 1–4.
   Mode: goal-based. Done when: the four gates pass and the spec's measurement
   table carries the end-to-end numbers. Timings are paired (the pre-change
   script re-run from `git show HEAD:` under the same conditions) and reported
   as ranges — repeat runs of identical code on this machine vary by over 2×,
   so a single before/after pair would overstate the result.

## Changelog

- Initial plan. Scope narrowed to `tools/test-pre-pr.sh` after measurement showed
  CI was not a bottleneck (190s PR critical path) and the pytest fixture was
  ~45s of a 947s suite — neither worth touching.
- Task 1 grew to a file extraction (rather than an inline heredoc) on review:
  29 lines of Python inside a `.sh` heredoc are invisible to `ruff` and `mypy`.
