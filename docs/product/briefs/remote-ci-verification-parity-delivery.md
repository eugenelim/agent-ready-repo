# Brief: finish remote verification with a complete-or-partial verdict

- **Slug:** `remote-ci-verification-parity-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/remote-ci-verification-parity.md`](../intents/remote-ci-verification-parity.md), cut into slices on 2026-11-05 from a read of the workflows and a re-count of the dispatch lanes.
- **Parent intent:** intent:remote-ci-verification-parity

## Outcome

A maintainer can dispatch one workflow against a pushed branch and read a single verdict, `ci-complete` or `partial`, naming the commit it proved. `ci-complete` covers everything `make ci` runs plus the jobs `build-check.yml` runs that `make ci` does not reach. It is deliberately narrower than the parent intent's "complete", which also counts the native Windows and macOS contracts. Those stay with `native-platform-verification-coverage`, so the parent Outcome is met only when both items have landed.

## Success metrics

- `gate-sast` runs under the Node version that `web/package.json` declares.
- One named table maps every lane the parent Boundary names except macOS (which stays with `native-platform-verification-coverage`) to its command, runner, timeout and completion label, and a construction test fails when a surface is missing from it. The lanes are build and policy, SAST/SCA, the Python corpus, the site and browser gate, and native Windows (five workflows or jobs, `build-check.yml`, `test-corpus.yml`, `pages.yml`, `build-check-windows.yml` and the SAST job inside `build-check.yml`); macOS is the sixth and belongs to the other intent.
- A composition workflow runs `make ci` undecomposed plus the extra jobs and emits the verdict, with a provisioning probe, a verdict channel the dispatched revision cannot forge, a recorded base revision, and stale-run marking and cancellation.

## Scope / Non-goals

**In scope:** Node parity for the npm SCA leg, the lane-contract table with its test, and the composition workflow with its verdict.

**Non-goals:** native macOS lane and native Windows dispatch (they belong to `native-platform-verification-coverage`), larger or self-hosted runners, the dispatch-only `test-roster.yml` and `pack-javascript.yml` suites, which are outside the table because the parent Boundary names no lane for them, and any change to the required checks or branch protection.

## Proposed slices

Every slice is checked by an agent with no live service, credential, or human reviewer. Dispatch reach for build, SAST, the Python corpus and the site gate already exists (`workflow_dispatch` on `build-check.yml` and `pages.yml`; `test-corpus.yml`, `test-roster.yml` and `pack-javascript.yml` are dispatch-only), so no slice repeats it.

| # | Slice | Agent-only verification | Depends on | Gating |
| --- | --- | --- | --- | --- |
| R1 | Add `actions/setup-node` (version 24, matching `web/package.json` engines) to `gate-sast`, with a posture-test assertion and a mutation that fails it. | `python3 tools/test-build-check-workflow.py` passes and the removed-step mutation fails | none | Own PR; the posture test lives in the required workflow's check |
| R2 | The surface-contract table, plus a construction test over triggers, permissions, runner label and membership. It also names the extra jobs: the jobs in `build-check.yml` that `make -n ci` does not reach, derived by comparing the two (candidates are `gate-export-boundary`, `gate-css-tokens` and `gate-credbroker`; `gate-sast` is reached through the local `make sast` leg, so the comparison confirms it is covered and not duplicated). | The test passes on the real tree; a seeded surface missing from the table fails | none | none |
| R3 | A `ci-full` dispatch workflow: `make ci` undecomposed plus the extra jobs from R2, a provisioning probe for the whole graph, a verdict job whose result a dispatched revision cannot edit (the verdict job runs from a pinned ref or the default branch's copy), the recorded base revision for base-reading checks, and a printed dispatched SHA with `ci-complete` or `partial`. | A construction test proves no phase reachable from `make ci` is omitted; seeded omissions of a target, of the probe and of the base revision each fail it; the test also asserts read-only workflow permissions, `persist-credentials: false` on every checkout, no repository secrets and no `pull_request_target` trigger, as the parent Boundary requires | R2, which supplies the table and the extra-job list | Own PR; a newly added workflow needs a dispatch on the default branch before it can run |
| R4 | Stale-run marking and cancellation for `ci-full`: a concurrency group so a newer dispatch on the same ref cancels an obsolete one, and a receipt line marking a run superseded when the ref has moved. | A construction test over the concurrency block; a seeded removal fails it | R3, which creates the workflow | none |

### Manual or live residue, split off as non-blocking follow-ups

- One recorded dispatch of `ci-full` against a pushed branch after R3 merges. GitHub accepts a manual dispatch only once the workflow exists on the default branch, so this runs after merge.
- Native macOS and Windows lanes: tracked by `native-platform-verification-coverage`.

## Decisions

- 2026-11-05, eugenelim: the verdict stays named `ci-complete`, narrower than the parent's "complete". Native Windows and macOS stay with `native-platform-verification-coverage`, and a full `complete` verdict is added when those lanes land.
- 2026-11-05, eugenelim: R3 and R4 keep every completion-claim obligation (provisioning probe, forge-proof verdict channel, recorded base revision, stale-run marking and cancellation); none is waived.
- 2026-11-05, eugenelim: R3's spec stays Implementing until the post-merge dispatch of `ci-full` is recorded; no waiver.

## Constraints / Appetite

Four sessions: R1 small, R2 small to medium, R3 medium, R4 small.

## Assumptions / Risks

- Riskiest assumption: `make ci` plus the extra jobs fits one hosted-runner job. Measured 2026-11-05 over 12 pull-request runs of `build-check.yml` (`gh api` job records, medians): `gate-main` 878 s, `gate-sast` 202 s, `gate-export-boundary` 244 s, `gate-credbroker` 56 s, `gate-css-tokens` 24 s. `gate-main` already includes the post-build test suite that `make ci` runs, so a serial composition adds the SAST leg that `make build-check` runs locally (about 202 s, the `gate-sast` median, because `make ci` reaches `make sast` unless a caller delegates it) and the three extra jobs: 878 + 202 + 244 + 56 + 24 = 1,404 s (23 minutes). That is under the 25 minute limit `gate-main` carries but leaves little room, so the composition timeout is a provisional bound of 45 minutes (about twice the measured serial sum), to be replaced by a measured value after the first recorded dispatch, or the extra jobs run as parallel jobs in the same workflow. R2 records the surface timeouts in its table; R3 sets the `ci-full` job timeout from the R2 figures.
- Risk: the composition silently omits a target. R3 derives its membership from `make -n ci` and the construction test compares against that output.
- The `docs/specs/remote-gate-dispatch/` directory that `tools/lint-ci-parity.py` and `test-corpus.yml` cite is absent from `docs/specs/`. R2 either restores a short spec there or repoints those citations; this is a docs edit inside R2.

## Ready gaps (Draft only)

- None open.

## Spec map

| Spec | Status |
| --- | --- |
|  |  |

## Provenance

- Parent intent: [`remote-ci-verification-parity.md`](../intents/remote-ci-verification-parity.md).
