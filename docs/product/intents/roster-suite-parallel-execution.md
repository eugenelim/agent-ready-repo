# Make the roster suite safe to run in parallel

- **Status:** Draft
- **Owner:** eugenelim

## Outcome

The roster suite runs in parallel and reports the same result it reports
serially. A contributor or a dispatched job gets the roster's verdict in
roughly a third of the current wall time, and a green parallel run means the
same thing a green serial run means.

## Boundary

- Keep the serial invocation authoritative. `make test` reaches the roster
  through its `tests/` sweep, and that path must keep working unchanged; a
  parallel runner is an additional way to run the suite, not a replacement for
  the one the gate uses.
- Fix isolation in the tests, not by pinning execution order. A suite that only
  passes in one order is the defect this item exists to remove, so a fix that
  constrains ordering has not fixed it.
- Do not reduce coverage to gain parallelism. Every case that runs serially runs
  in parallel, including subtests.
- Declare any runner dependency the change relies on in the owning manifest
  before using it.

## Owner

Repository maintainers.

## Unresolved questions

- **How many roster cases are non-isolated?** One is confirmed. It was found
  because it failed, not because the class was audited, so the true count is
  unknown and could be larger.
- **Is worker-level parallelism the right shape, or job-level sharding?**
  In-process workers share the working tree, which is what breaks the confirmed
  case. Separate jobs do not, but need a stable way to split a flat directory of
  83 files without hand-maintaining a roster.
- **Does the wait profile hold on a GitHub-hosted runner?** The measurements
  below were taken on macOS. A Linux runner's filesystem behaviour differs, and
  the speedup depends on the work being wait-bound.

## Opportunity

**Measured 2026-09-04 on this worktree, `tests/roster/` (83 files):**

| Run | Wall | `user` | `sys` | Result |
| --- | --- | --- | --- | --- |
| serial | 540.07s | 51.04s | 76.96s | 1236 passed, 46 subtests passed |
| `-n 4 --dist loadfile` | 218.45s | 54.72s | 78.74s | **1 failed**, 1235 passed, 42 subtests passed |

Three things follow from those numbers.

**The speedup is real and the headroom is larger than core count.** Wall time
fell 2.5x while `user` and `sys` barely moved, so the suite spends most of its
wall time waiting rather than computing. `sys` exceeding `user` in both runs
points at filesystem work — consistent with contract tests that walk the
repository tree. Waiting overlaps, so the ceiling is not the core count.

**Nothing serialises it.** No roster test takes the coordination lease, so there
is no lock to contend on. Only 19 of the 83 files spawn a subprocess.

**One case is not isolated from the working tree, and that is the blocker.**
`tests/roster/test_workspace_status_projection.py::RealTreeProjectionTests::test_scripts_in_real_tree_projection`
fails under workers and passes alone in 1.06s at the same commit. It walks the
real tree's self-hosted projections and compares them against pack sources, so a
peer worker perturbing the tree mid-read reds a clean checkout. `--dist
loadfile` does not help: the contention is the shared tree, not case ordering
within a module. That test owns exactly 4 subtests, which accounts for the whole
46-to-42 subtest drop — the missing subtests are its own, not a second defect.

Shipping parallel execution before fixing that would produce a surface that goes
red on a clean tree, which teaches people to ignore it. That is worse than the
nine minutes it saves.

## Projection

- Audit `tests/roster/` for cases that read or write the live working tree,
  rather than fixing only the one that failed. The confirmed case is a sample of
  a class.
- Give each such case a snapshot or a temporary tree to read, so its result does
  not depend on what a concurrent worker is doing.
- Prove the fix by running the suite in parallel repeatedly, not once. A single
  green parallel run is compatible with a race that usually loses.
- Decide worker-level versus job-level parallelism after the isolation audit,
  because the audit's result changes which is cheaper.
- `pytest-xdist` 3.8.0 is installed in this environment but declared in no
  repository manifest. Using it in a gate or a workflow means declaring it,
  which the root instructions treat as adding a dependency.

## Assumptions

- Technical: `make test` reaches the roster through `pytest tests/`, a
  directory sweep of the parent, so all 83 files already run serially in the
  local gate (source: the `test-unleased` target).
- Technical: no workflow invokes `make test`, so remotely only the roster files
  named individually inside `build-check.yml` run today (source: the workflow
  files).
- Technical: the repository already records that the roster is sensitive to
  process composition — a `sys.path` leak once made two roster tests fail alone
  and pass in a combined run at the same commit (source:
  `tools/test_import_time_path_leaks.py`).

## Source

Discovered while shaping `remote-gate-dispatch`, the first slice of
[`remote-ci-verification-parity`](remote-ci-verification-parity.md), when the
owner asked whether the roster suite could be offloaded and parallelised. The
offload half needs no work here — a dispatched `make test` already covers the
roster. This item is the parallel half, which measurement showed is blocked
rather than merely unbuilt.
