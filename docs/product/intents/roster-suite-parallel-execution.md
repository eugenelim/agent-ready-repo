# Prove the roster suite safe to run in parallel

- **Slug:** `roster-suite-parallel-execution`
- **Level:** feature
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Owner:** eugenelim

## Outcome

A parallel roster run is proven to report what a serial run reports, so a green
parallel run means the same thing a green serial run means. The proof is an
audit of every roster case that reads or writes the live working tree, plus
repeated parallel runs on a hosted runner that agree with the serial verdict.

## Boundary

- Keep the serial invocation authoritative. `make test` reaches the roster
  through its `tests/` sweep, and that path stays unchanged; the parallel
  runner is an additional way to run the suite.
- Fix isolation in the tests, not by pinning execution order. A suite that only
  passes in one order is the defect this item exists to remove.
- Do not reduce coverage to gain parallelism. Every case that runs serially runs
  in parallel, including subtests.
- Declare any runner dependency in the owning manifest before using it.

## Owner

eugenelim, as repository maintainer.

## Delivered context

- `pytest-xdist>=3.8` is declared in `tools/requirements.txt`, and the
  dispatch-only `test-roster.yml` runs `python -m pytest tests/roster/ -q -rs -n auto --dist loadfile`.
- The blocker recorded on 2026-09-04 was a serialization defect, not a shared-tree
  race. `RealTreeProjectionTests::test_scripts_in_real_tree_projection` in
  `tests/roster/test_workspace_status_projection.py` passed a `Path` to
  `unittest.subTest`, and pytest-xdist cannot send that through execnet. Commit
  `ce5342d3f` stringifies the parameter, and a local parallel run then matched the
  serial result (1236 passed, 46 subtests).
- The local timings from that run (540 s serial) were taken at roughly 19x CPU
  oversubscription and do not transfer to a runner. The first hosted run is the
  first honest measurement.

## Remaining work

- Audit the roster (184 test files, of which about 70 spawn processes or write files)
  for cases that read or write the live working tree. `test_scripts_in_real_tree_projection`
  is the known live-tree reader: it compares both self-hosted projections with the
  pack sources, so a peer worker that regenerates the projection mid-read would
  red a clean checkout. Whether any case writes the live tree is unknown, because
  the class was never audited.
- Give each such case a snapshot or a temporary tree to read.
- Prove the fix by running the suite in parallel repeatedly on a hosted runner,
  since a single green run is compatible with a race that usually loses.
- Decide worker-level versus job-level parallelism after the audit. Workers share
  the tree. Job-level sharding does not, but needs a stable way to split a flat
  directory without a hand-maintained roster.

## Unresolved questions

- How many roster cases are non-isolated? The audit answers it.
- Does the wait profile hold on a GitHub-hosted runner? The earlier measurement
  came from macOS, and the speedup depends on the work being wait-bound.
- Is `--dist loadfile` enough, or does a case need its own tree even within a
  module? The workflow keeps `loadfile` because the suite has a recorded
  order-sensitivity history (`tools/test_import_time_path_leaks.py`).

## Source

Discovered while shaping `remote-gate-dispatch`, the first slice of
[`remote-ci-verification-parity`](remote-ci-verification-parity.md), when the
owner asked whether the roster suite could be offloaded and parallelised. The
offload half needs no work here, because a dispatched `make test` already covers
the roster. This item is the isolation proof for the parallel half.

## Non-goals

- The serial invocation stays authoritative; `make test` reaches the roster through its `tests/` sweep unchanged.
- No order pinning is used to make a case pass.
- No case or subtest is dropped to gain parallelism.

**Riskiest assumption:** the three roster files that write under the repository root are the only live-tree writers. Agent-only test: run the suite in parallel several times locally, compare the verdict to the serial run, and compare `git status --porcelain` before and after each run.

## Readiness

Route: new-spec, one session, and it is low priority because `make test` already runs in four shards through `test-corpus.yml`.

Checked 2026-11-05: `tests/roster/` holds 190 files, and three name a write to the repository root: `test_agent_skill_engineering_consumer_integrations.py`, `test_visual_handoff_golden_path.py` and `test_workspace_status_projection.py`. First slice: give those three a temporary tree or snapshot, then run the suite with `-n 8` several times locally and compare to the serial verdict. The hosted-runner repeat is a named, non-blocking follow-up. The captured order-dependence defect `pre-existing-captured-item-link-refusal-order-dependence` is a one-fixture fix that blocks xdist runs and belongs in the same session.
