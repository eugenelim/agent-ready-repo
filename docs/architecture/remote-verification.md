# On-demand remote verification

> **STATUS: PLANNED.** This page describes the surface accepted by
> [`remote-ci-verification-parity`](../product/intents/remote-ci-verification-parity.md).
> No `remote-verify.yml` exists, and `build-check-windows.yml` declares no
> `workflow_call`. Current verification topology:
> [`verification-graph.md`](verification-graph.md).

A maintainer dispatches one named lane or the complete composition against a
pull request whose head is a branch in this repository. The run resolves the
head to an immutable SHA, checks out exactly that SHA, and reports it.

A
selective run is partial evidence. Only the composition may claim completion.

**The composition runs `make ci` itself, undecomposed.** No partition can omit a
target and no roster can drift from the graph, because the composition invokes
the one target whose definition is the coverage. This follows from [verification-graph § 1.2](verification-graph.md#12-provisioning-edges-are-held-by-make-or-by-the-environment): `make`
holds the ordering edges, and a whole invocation inherits them.

With neither
`SKIP_SAST` nor `SAST_DELEGATED`, the SAST leg runs inline, so one invocation
covers `gate-main` and `gate-sast`. Three further jobs cover what `make ci`
does not reach ([§ 3.2](verification-graph.md#32-checks-the-fleet-reaches-and-make-ci-does-not)): native Windows, native macOS, and the site and browser
gate. Selective lanes are accelerators that may change without changing what a
complete run means.

## Existing capability the design builds on[^2]

| Capability | Present state |
| --- | --- |
| Security scan, separately runnable | `gate-sast` runs `make sast` on its own runner; any `build-check.yml` dispatch reaches it |
| Site and browser gate, dispatchable | `pages.yml` declares `workflow_dispatch` |
| Build and policy chain, dispatchable | `build-check.yml` declares `workflow_dispatch` |
| Complete corpus, runnable remotely | `test-corpus.yml` (weekly and dispatch, four shards) and `test-roster.yml` (dispatch); both are scoped evidence, not required checks |

A dispatched `build-check.yml` scans: its relevance detector runs only on
`pull_request`, so on a dispatch its output is empty and `Run make sast`
executes.

## Job roster

Composition membership and individual dispatchability are independent properties.

| Job | Kind | Command | Runner |
| --- | --- | --- | --- |
| `resolve` | scaffolding | Resolve the head SHA; refuse a foreign head, an unreadable pull request, a non-SHA response, or an expected-SHA mismatch. No checkout of the revision under test | `ubuntu-latest` |
| `verify-make-ci` | evidence | Provisioning probe, then `make ci` | `ubuntu-latest` |
| `windows-native` | evidence | `build-check-windows.yml`[^3] through a `./`-relative `workflow_call` | `windows-latest` ×4 plus `ubuntu-latest` |
| `macos-native` | evidence | Checks classified `darwin-native` that have a live-platform test, under a scratch keychain and a `RUNNER_TEMP`-confined `HOME` | `macos-15` |
| `site-browser` | evidence | Site build, rendered-link audit, `web` unit suite, `web` browser gate. The plugin suite is not repeated | `ubuntu-latest` |
| `receipt` | scaffolding | Re-resolve the head and emit the receipt. No checkout of the revision under test | `ubuntu-latest` |

Individually dispatchable lanes: `build-policy`, `sast-sca`, `pytest-corpus`,
`site-browser`, `windows-native`, `macos-native`. The last three are also
composition members; the first three are dispatchable only because `make ci`
already contains their content. `macos-latest` is unused because `-latest`
labels move between stable images.

## Receipt and staleness

The receipt is one fenced `json remote-verify-receipt.v1` block in the job
summary, a closed object with ten keys: `schema_version`, `state`, `lane`,
`pull_request`, `head_sha`, `base_revision`, `draft`, `dispatch_ref`,
`dispatched_by`, and `job_results`.

| `state` | Meaning |
| --- | --- |
| `partial` | One named lane ran. Evidence about that lane only. |
| `complete` | Every composition job ran and succeeded; the head is unchanged. |
| `incomplete` | Every composition job ran, at least one did not succeed; the head is unchanged. |
| `superseded` | The head moved, or re-resolution failed. The evidence does not describe the current head. |

`base_revision` is recorded because `make ci` depends on the base:
`lint-catalogue-curation-guard.py` and `tools/repo/branch_added_paths.py` resolve
`origin/main` at run time. `resolve` pins the SHA, every job checks out that SHA
and refuses to run on a mismatch, and `receipt` re-resolves it. A dispatch run's
check runs attach to the dispatch ref, not the pull request, so the receipt is
read from the run page.

## Trust boundary

A job executes repository code from the selected pull request, so dispatching is
a trust decision. The controls:

- Same-repository heads only; fork pull requests are out of scope.
- Dispatch requires write access, and the receipt records who dispatched.
- Top-level `permissions: contents: read`, `pull-requests: read` on `resolve`
  only, no write scope under any spelling.
- No Actions cache in any job with a foreign revision checked out, including the
  called Windows workflow (its two `cache: 'pip'` steps need explicit handling).
- `persist-credentials: false` on every checkout the composition causes.
- No `secrets.` context, no `pull_request_target`, dispatch inputs reach shells
  only through `env:`, every `uses:` is a SHA already in the fleet, and runners
  are standard hosted labels written as literals.
- Artifacts are diagnostic, bounded by `retention-days`, and no verdict reads one.

**Accepted residual.** Dispatch from any branch runs the
selected ref's copy of the workflow file, including its `permissions:` block, and
no required check has reviewed that copy. The effective bound is the
dispatcher's write authority plus any enforced organization or enterprise
maximum, which is unestablished.

Repository settings read on 2026-11-04[^1]:
`default_workflow_permissions` is `read`, `can_approve_pull_request_reviews` is
`false`, `allowed_actions` is `all`, `sha_pinning_required` is `false`. Re-price
the residual when any of those change, when an organization Actions policy
changes, when a ruleset or bypass actor changes who may push to a dispatchable
ref, or when dispatch is granted below write. A ruleset restricting unreviewed
workflow-file changes on dispatchable refs is unevaluated.

## Concurrency, bounds, activation

The concurrency group keys on the pull request and lane, with
`cancel-in-progress: true`, and its prefix differs from every prefix in the
fleet because job and workflow groups share one namespace. Every job declares
`timeout-minutes` with a recorded origin. Standard macOS concurrency is capped at
5 jobs on Free and Pro plans.

GitHub accepts a manual dispatch only when the definition exists on the default
branch, so rollout has two stages. Pre-merge proves construction (construction
tests and the automatic checks). Post-merge proves operation: one selective run,
one complete run against the same SHA, and one run that receives a push in
flight and returns `superseded`.

Out of scope: release, publication, deployment, signing, simulators, Xcode,
nested virtualization, live model evaluation, larger or self-hosted runners,
fork pull requests, billing or runner policy, and weakening any local gate or
required check.

[^1]: `GET /repos/{owner}/{repo}/actions/permissions` and `…/permissions/workflow` on 2026-11-04.
[^2]: `.github/workflows/build-check.yml` (`gate-sast`, `workflow_dispatch`), `.github/workflows/pages.yml`, `.github/workflows/test-corpus.yml`, `.github/workflows/test-roster.yml`.
[^3]: `.github/workflows/build-check-windows.yml` job list: four `windows-latest` jobs and one `ubuntu-latest` aggregate.
