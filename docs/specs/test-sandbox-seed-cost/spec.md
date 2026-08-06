# Spec: test-sandbox-seed-cost

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Mode:** light (no risk trigger fired)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Cut the wall-clock cost of `tools/test-pre-pr.sh` by removing the per-file
subprocess spawns in `seed_sandbox`, without changing what any case asserts and
without weakening per-case isolation.

Measurement (this machine, serial, nothing else running) established the cause:

| Measurement | Result |
| --- | --- |
| Bare process spawn (`/bin/echo` × 3,109) | 80.2s → **25.8ms per spawn** |
| `seed_sandbox` bash copy loop (`mkdir -p` + `cp -P` per file, 2 spawns/file) | 268.2s |
| Same copy, one Python process (`shutil.copy2(follow_symlinks=False)`) | 23.6s |
| `git init` + `add -A` + `commit` on the copied tree | 7.4s |
| `pre-pr-catalogue.py` against a seeded sandbox | 47.6s |
| **`bash tools/test-pre-pr.sh` end-to-end — before** | **1663s / 2204s** (n=2; 28–37 min) |
| **`bash tools/test-pre-pr.sh` end-to-end — after** | **215s / 301s / 494s** (n=3 serial; 4–8 min) |

This machine is noisy — repeat runs of identical code vary by more than 2×, so
both ends are reported as ranges rather than single figures, and a fourth "after"
run (542s) is excluded because another gate was running concurrently. Comparing
medians gives **~6× faster**; the most conservative pairing (slowest after vs
fastest before) still gives **~3.4×**. Roughly 20–30 minutes back per run.

`seed_sandbox` runs 6 times (1 baseline + 5 corruption cases), so the copy loop
alone spent 6 × 3,109 × 2 = **37,308 process spawns ≈ 16 min of pure spawn
overhead**. Spawn cost is a property of the machine, not of any agent sandbox:
measured 26.06ms/spawn with sandboxing disabled vs 25.8ms with it enabled.

The fix is to stop spawning per file. Everything else about the harness — which
files are seeded, the symlink semantics, the real-git-repo requirement, and the
one-fresh-tree-per-case isolation model — is unchanged.

## Boundaries

### Always do

- Seed exactly `git ls-files` plus `git ls-files --others --exclude-standard`.
- Preserve symlinks as symlinks, and assert it at the point of construction.
- Give every corruption case a freshly seeded tree.

### Ask first

- Any change to which suites CI runs, or to `packages/agentbundle`'s published
  surface — both are outside this spec and trip a full-mode risk trigger.

### Never do

- **Never change what a case asserts, or narrow what runs, to make it faster.**
- **Never weaken per-case isolation.** A fast suite that lies is worse than a
  slow one; a shared or partially-unwound sandbox produces order-dependent passes.
- Never seed with `git clone --local` or `git archive` — both carry committed
  state only and silently drop untracked projections (the CAT-V-015 failure).

## Out of scope

- **The pytest `_seed_sandbox` fixture** (`packs/core/tests/hooks/test_pre_pr_py.py`).
  It already does the in-process copy this spec adds to the bash side; measured
  at ~15s × 3 tests = ~45s of a 947s suite. Converting it to a session-scoped
  pristine tree plus per-test clone measured *worse* than leaving it alone, and
  would trade away function-scoped `tmp_path` isolation for nothing.
- **Diff-scoped test selection.** CI is not the bottleneck: the full PR critical
  path is 190s, Gate A's Linux job runs all 3,603 tests in 108–154s, and its four
  `pip install` steps total 9–12s (~8%). Gate A's Linux job is not on the critical
  path — `build-check-windows` (190s) and Gate A Windows (183s) are, and the
  Windows job already runs a curated subset. Selection would buy ~0s of PR wall
  clock while adding a mapping that can silently under-select.
- **`self_host.py`'s shadow-tree clone.** It does not share this code path, it is
  a published-package surface, and touching it trips the structural trigger.

## Testing Strategy

Goal-based check plus a construction-time invariant assertion:

1. `bash tools/test-pre-pr.sh` still reports `✓ Self-test: passed (6 cases).`
   — the same 6 cases, the same expected failure substrings, unchanged.
2. `tools/seed_test_sandbox.py` verifies every symlink it copies landed as a
   symlink, pinning the K-0002 regression class at the point where the copy
   mechanism changed. Verified by mutation: a variant that dereferences file
   symlinks exits 1 with `FAIL [seed]: 'CLAUDE.md' was dereferenced…`.
3. Before/after wall clock recorded for `tools/test-pre-pr.sh` (table above).

## Acceptance Criteria

- [x] `seed_sandbox` spawns a constant number of processes, independent of file count
- [x] The seeded set is unchanged: `git ls-files` plus `git ls-files --others --exclude-standard`
- [x] Symlinks are preserved as symlinks, not dereferenced (invariant 2 / K-0002)
- [x] The symlink check is derived from what is actually copied, not a hardcoded list
- [x] The sandbox is still a real git repo with a `baseline` commit (invariant 3)
- [x] Untracked-but-not-ignored files are still present in the sandbox (invariant 1)
- [x] Each corruption case still starts from a byte-identical pristine tree (invariant 4)
- [x] The `rm -rf` retry tolerance for the GitHub-runner race is retained (invariant 6),
      including destination-clobber tolerance the old `cp -P` provided
- [x] No case's assertion, expected substring, or corruption command changes
- [x] A seeder failure fails the script loudly rather than yielding a partial tree
- [x] `bash tools/test-pre-pr.sh` passes; before/after timings recorded

## Assumptions

- `python3` is already a hard dependency of this script (it invokes
  `python3 tools/pre-pr-catalogue.py` on every case), so using it for the copy
  adds no new prerequisite.
- The script is repo-internal: consumers are `tools/test-all.py` and the
  `docs.yml` "Lifecycle hooks" job. It is not projected into `packs/`, so there
  is no adopter-facing surface and no pack changelog entry is owed. Gate G
  classes `tools/` as non-release-impacting.
