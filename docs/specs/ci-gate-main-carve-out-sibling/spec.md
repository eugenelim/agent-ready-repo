# Spec: gate-main's catalogue-test carve-out runs in a sharded sibling job

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0101, ADR-0122, RFC-0082,
  [`docs/specs/ci-gate-parallelization/`](../../specs/ci-gate-parallelization/)
  (the aggregator contract),
  [`docs/specs/test-corpus-sharding/`](../../specs/test-corpus-sharding/)
  (the shard pattern)
- **Brief:** none
- **Discovery:** intent:ci-gate-main-runtime-budget
- **Depends on:** none
- **Contract:** none — no runtime contract changes. One required status check
  (`make build-check`, the aggregator) gains a dependency; no check is added,
  removed, or weakened.
- **Shape:** service
- **Risk triggers:** security-boundary, structural-interface

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A maintainer merging to `main` waits on a `gate-main` job whose docs-only median
runtime sits at or below 600 seconds, because its two heaviest test steps run in
a sharded sibling job in parallel instead of serially inside it. Every check
that gated a pull request before the move still runs, and a failure in the
sibling blocks the pull request exactly as a `gate-main` failure does.

## What Changes

- The RFC-0082 catalogue-test carve-out step leaves `gate-main`; its invocations
  run verbatim inside a single per-shard dispatch step of a new matrix job,
  `gate-catalogue-tests`, whose run body holds every invocation in a
  shard-keyed `case` dispatch — `.github/workflows/build-check.yml`
- The shared-test dedup guard step leaves `gate-main` and runs as one invocation
  inside the dispatch body's shard branch — `.github/workflows/build-check.yml`
- The aggregator (`make build-check`) waits on the sibling and requires its
  result exactly as it does the five existing gates — `.github/workflows/build-check.yml`
- The posture test models the sibling job, pins its checkout and its dispatch
  body, gains mutations for the sibling's aggregator wiring, and updates its
  recorded empty-matrix safety reason for a job outside branch protection — `tools/test-build-check-workflow.py`
- The parity rosters re-point the two moved steps and every suite they gate at
  the sibling's dispatch step, keeping each entry's `PR_GATED` kind — `tools/lint-ci-parity.py`
- The workflow's per-job local-reproduction map and the placement comments that
  referenced the carve-out's position inside `gate-main` are rewritten for the
  two-job layout — `.github/workflows/build-check.yml`,
  `.github/workflows/test-corpus.yml` (one stale header line)
- The verification graph records the sibling job and what it runs —
  `docs/architecture/verification-graph.md`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture truth | Applicable — the CI gate graph gains a job and `gate-main` loses two steps | [`docs/architecture/verification-graph.md`](../../../architecture/verification-graph.md) | Repository maintainers | Updated prose naming the sibling, its shards, and the aggregator edge | Statement matches the shipped workflow |
| Maintainer procedure | Applicable — the workflow's per-job local-reproduction map is the documented parity surface | `.github/workflows/build-check.yml` (header comment block) | Repository maintainers | A `gate-catalogue-tests` entry beside the map's existing entries (gate-main, gate-sast, gate-export-boundary, gate-credbroker, and the aggregator; `gate-css-tokens` has no map entry today, and gaining one is outside this slice) | Each named local command reproduces its job's checks |
| Decision rationale | Not applicable — no ADR decision is reversed; ADR-0122's scope simply loses two steps | — | — | — | — |
| User-facing documentation | Not applicable — repository-internal CI; no adopter-visible surface changes | — | — | — | — |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Update `tools/test-build-check-workflow.py` and `tools/lint-ci-parity.py` in
  the same commit as any `.github/workflows/build-check.yml` edit — their
  equality pins redden on every workflow change, by design.
- Move each invocation byte-identical: one pytest process per invocation, no
  merging of invocations, no splitting of one across shards (ADR-0101
  compatibility-class discipline).
- Give the sibling its own fail-closed provisioning probe that runs before the
  dispatch step, so a missing dependency reddens the job instead of letting
  suites silently skip (the test-corpus pattern).
- Check out with `fetch-depth: 0` and `persist-credentials: false` in the
  sibling: the `tests/` tree reaches git-history-dependent cases, and the
  posture test pins every checkout's `with:` mapping.

### Ask first

- Changing any branch-protection rule or required status check.
- Adding suites to, or removing suites from, the pull-request-gated set — the
  moved set is exactly the two steps' invocations, no more and no fewer.
- Editing the Makefile's `run-test-suite` define or any `MAKE_BASELINE_DIGESTS`
  entry.

### Never do

- Drop, skip, weaken, or narrow any check to save time.
- Move any `gate-main` step other than the two named steps.
- Merge two pytest invocations into one process or split one invocation across
  shards.
- Add a step-level `if:` to the sibling's steps, or select tests by a diff,
  changed-file list, or any content-derived predicate.
- Change `runs-on` away from the exact literal `ubuntu-latest`.
- Touch SAST configuration, `gate-export-boundary` behavior, the aggregator's
  handling of the five existing gates (the sibling is strictly additive to
  `needs` and the guard), or branch protection.

## Testing Strategy

- **Command-set preservation (AC-0001) — goal-based check.** The migration
  fact — every invocation survives, none added — is proven once by a mechanical
  comparison of the two steps' before-listing against the invocations inside
  the sibling's dispatch body, recorded in `notes/verification-ledger.md`. The
  standing control is the posture test's equality pin on the dispatch body, so
  later drift reddens.
- **Aggregator fail-closed wiring (AC-0002, AC-0003) — TDD.** The posture
  test's mutation matrix gains the sibling mutations; each is proven red
  against the mutated workflow by `--self-test`, the same mechanism that pins
  the five existing gates.
- **Structural wiring and roster coverage (AC-0004, AC-0005, AC-0006) —
  goal-based check.** `tools/test-build-check-workflow.py` and
  `tools/lint-ci-parity.py` exit 0 against the shipped workflow and exit 1
  naming the missing piece when a moved step, disposition, or suite entry is
  absent, stale, or downgraded from `PR_GATED`.
- **Shard shape and provisioning probe (AC-0007, AC-0008) — goal-based
  check.** The posture test asserts the matrix and `fail-fast: false`
  (one red shard must not cancel the others), cross-pins the matrix shard
  set against the dispatch body's case-branch set (either-direction
  mismatch reddens, the test-corpus matrix↔`SHARDS` discipline), and pins
  the probe's checks by equality with mutations proving they bite: a
  removed probe step, an emptied or short-circuited probe body, and a
  dropped probed dependency each redden.
- **Runtime target — measurement, post-merge.** The ≤ 600 s docs-only median
  is confirmed by a `gh api` re-measurement after merge; the intent marks it a
  non-blocking follow-up, so it is a Follow-on here, not a blocking criterion.

## Acceptance Criteria

- [ ] **AC-0001.** Every invocation in the two moved steps' `run` bodies runs
  in exactly one shard branch of the sibling's dispatch step after the move,
  and no invocation is added or removed. A mechanical before/after comparison
  recorded in `notes/verification-ledger.md` shows the one-to-one match over
  the closed set of invocations the two steps ran before the move.
- [ ] **AC-0002.** Removing the sibling from the aggregator's `needs` reddens
  the posture test. `tools/test-build-check-workflow.py` exits 1 against a
  workflow whose aggregator `needs` omits the sibling job, and `--self-test`
  reports that mutation caught.
- [ ] **AC-0003.** The aggregator requires the sibling's result.
  `tools/test-build-check-workflow.py` exits 1 when the `Require every gate`
  step lacks the sibling's env-var binding or its guard statement, and
  `--self-test` reports a caught mutation for each.
- [ ] **AC-0004.** `gate-main` runs neither moved step.
  `tools/test-build-check-workflow.py` exits 1 when either moved step name
  appears in the `gate-main` job. The presence half — the invocations running
  in the sibling — is AC-0001's after-listing, taken from the dispatch body.
- [ ] **AC-0005.** Every `gate-catalogue-tests` step carries a
  `STEP_DISPOSITION` entry on both axes. `tools/lint-ci-parity.py` exits 1,
  naming the step, when a sibling step lacks one.
- [ ] **AC-0006.** Every `SUITE_DISPOSITION` entry that gated a moved suite
  keeps its `PR_GATED` kind and names the sibling's dispatch step.
  `tools/lint-ci-parity.py` exits 1 when such an entry names a step the
  workflow no longer carries, and its self-test carries a case whose mutation
  flips one such entry to `NO_PR_GATE` and reddens.
- [ ] **AC-0007.** The sibling is a shard matrix that does not cancel its
  siblings on a red, and the matrix shard set matches the dispatch body's
  case-branch set exactly. `tools/test-build-check-workflow.py` exits 1
  unless the `gate-catalogue-tests` job declares a matrix with at least two
  shard entries and `fail-fast: false`, and exits 1 on any mismatch — in
  either direction — between the matrix shard set and the dispatch body's
  case-branch set (a shrunken matrix silently un-runs a branch's suites;
  an extra matrix entry hits the `*)` fail-closed branch).
- [ ] **AC-0008.** The sibling probes its provisioning before any suite
  runs, and the probe's checks are pinned and mutation-proven like the
  dispatch body. `tools/test-build-check-workflow.py` exits 1 when the
  provisioning-probe step is absent from the `gate-catalogue-tests` job,
  when the probe's body is emptied or short-circuited, or when a probed
  dependency is dropped from its pinned checks, and `--self-test` reports
  a caught mutation for each.

## Follow-ons

- eugenelim: post-merge `gh api` re-measurement of `gate-main`'s docs-only
  median (run records over the merged branch) — confirms the ≤ 600 s target
  from the intent; non-blocking by the intent's own framing.

## Assumptions

- Defaulted: Technical: three shards — default: the heaviest single invocation
  (`pytest tests/`, ~90 s in the shard weights table) sets the floor and the
  ~287 s combined median splits to roughly 100 s per shard; if wrong: the shard
  count is a mechanical recount with no contract change (settled by: eugenelim).
  This line is the canonical statement of the shard count; the plan references
  it rather than restating it.
- Defaulted: Technical: job id `gate-catalogue-tests` — default: names the
  moved content (the RFC-0082 catalogue-test carve-out) in the existing
  `gate-*` family; if wrong: a rename is mechanical (settled by: eugenelim).
- Defaulted: Technical: the sibling's exact provisioning set — default:
  checkout with `fetch-depth: 0` and `persist-credentials: false`, Python 3.11,
  pytest, `tools/requirements.txt`, editable `agentbundle`, `httpx`, and a
  fail-closed probe, with the exact set discovered at implementation by a
  skip-aware procedure (the moved invocations run locally in an environment
  no richer than the sibling's candidate provisioning set — a richer
  environment hides a missing dependency as a green run — with skip
  reporting enabled and every skipped test accounted for, so a dependency
  whose absence manifests as a pytest skip — which exits green — feeds into
  the probe rather than shipping silently); if wrong: the probe reddens the
  job for any dependency the discovery found — the probe covers the
  discovered set, and the discovery, not the probe, is what must be
  skip-audited (settled by: implementation). This line is the canonical
  statement of the provisioning starting point; the plan references it
  rather than restating it.
