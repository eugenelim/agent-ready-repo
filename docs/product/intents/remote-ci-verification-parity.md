# Offload full and selective verification to remote CI

- **Status:** Accepted
- **Level:** feature

## Outcome

For any pushed branch in this repository, a maintainer can independently dispatch named remote verification surfaces or a complete remote run; each run reports the exact revision it used and an unambiguous partial-or-complete verdict, and a complete pass covers every semantic check that `make ci` would run at that revision plus the repository's declared native Windows and macOS portability contracts.

## Boundary

- Deliver independently with no prerequisite on `ci-parity-linter-scope`, an unimplemented brief, or any other backlog item.
- Provide independently dispatchable lanes for the Ubuntu build and repository-policy chain, SAST/SCA, the complete Python test corpus, the complete site and browser gate, native Windows portability, and native macOS portability, plus a full composition that runs every lane.
- Treat each selective lane as partial evidence and label it accordingly. Only the full composition may claim remote CI completion.
- Make the full composition cover local-only lints and every other semantic check in `make ci` by invoking repository-owned commands directly or sharing named Make targets. Retain remote-only platform, installed-package, CodeQL, secret-scan, and workflow-security checks as additional evidence without claiming contributor-machine environment identity.
- Allow pytest selection only at named repository-owned suite boundaries that preserve process isolation, collection floors, skip detection, source resolution, and standalone `make test` behavior. Any target extraction needed to establish those boundaries belongs to this feature.
- Report the exact revision a run used. A dispatch names a ref and GitHub pins it to an immutable SHA and records it, so no resolver is required and nothing needs to fail closed on an unprovable revision — that requirement belonged to the withdrawn draft-pull-request design.
- Make a superseded run visibly stale, and define cancellation so obsolete runs do not consume capacity or masquerade as current proof. **Both belong to `remote-ci-completion-claim`**: they exist to stop an obsolete run being read as current proof, which matters only once a run may claim completion. A partial-evidence dispatch makes no such claim.
- Keep every on-demand lane informational and non-required. Preserve the current automatic pull-request workflows, required check names, branch protection, and merge behavior.
- Run this feature only on standard GitHub-hosted runners. Paid larger runners, self-hosted capacity, custom runner images, and changes to organization billing or runner policy require separate approval and are not prerequisites for parity.
- Use least-privilege read-only workflow permissions, non-persisted checkout credentials, no repository secrets, and no `pull_request_target` execution path.
- Exclude release, publication, deployment, live-model evaluation, and any weakening of local gates, tests, security controls, or existing required checks.

### Platform coverage contract

| Evidence | Runner and role | Required coverage | Explicit limitation |
| --- | --- | --- | --- |
| Ubuntu baseline | Standard Ubuntu x64 image selected by the spec; authoritative semantic parity lane | Every target and phase reachable from `make ci`, SAST/SCA, complete pytest corpus, and site/browser verification | Does not prove Windows APIs, Windows filesystem or locking semantics, macOS Keychain/system trust, APFS behavior, or BSD-specific process behavior |
| Windows native | Existing standard Windows x64 contract, made selectively dispatchable and reusable by the full composition | Existing AgentBundle compatibility command, CredBroker suite, byte-range lock measurement, coordination-lease assertions, Windows encoding, path, ACL, and curated portability checks | Does not duplicate the complete Ubuntu corpus or scanners that do not support Windows; simulated Windows-path tests on Ubuntu do not replace this lane |
| macOS native | One standard, version-pinned macOS image and architecture selected by the spec | Only tests whose result depends on Darwin: scratch-Keychain and system-trust integration, Darwin platform dispatch, APFS/path and symlink assumptions, and BSD process/filesystem behavior identified by the platform census | Does not duplicate host-neutral pytest, SAST, or site/browser work merely to create a three-OS matrix; simulated `sys.platform = "darwin"` tests on Ubuntu do not prove native integration |
| Contributor macOS | Local `make ci` on a developer Mac | Useful early evidence for host-neutral gates and incidental Darwin behavior | Advisory only: it neither proves the Ubuntu runner contract nor substitutes for the controlled remote macOS lane, and enterprise restrictions or local toolchain state may suppress native behavior |

- Classify checks by what they prove, not where they happen to run: host-neutral, POSIX-shared, Linux-native, Windows-native, Darwin-native, or platform-simulated. Add a second operating system only when that classification changes the observable contract.
- Keep Ubuntu authoritative for complete semantic coverage. Keep Windows and macOS as focused native-portability lanes whose owned checks participate in the full composition and whose expected skips are explicit and fail closed when a required native test is not collected.
- Reuse the existing Windows workflow commands and guards rather than constructing a second Windows definition. Any extraction needed to make those commands callable belongs to this feature and must preserve their current automatic triggers and aggregate status.
- Establish the macOS lane from the current repository census, not by copying the Ubuntu job or inheriting unrelated historical commitments. Admit only native checks owned by this feature's platform contract.

## Owner

- eugenelim

## Decomposition

The feature level beneath this intent, none confirmed. **The order is set by
what costs a contributor time today**, not by what completes the Outcome
sentence — and the Projection's "one independently shippable change unless
implementation discovery proves that unsafe" is exercised here, because
discovery did.

1. `remote-gate-dispatch` — **the offload, and unconditional.** Make the
   build-and-repository-policy, SAST/SCA, Python-corpus, and site-and-browser
   gates triggerable against **a pushed branch**, each labelled partial
   evidence, and tell repository guidance to dispatch them rather than spend
   local CPU on them.

   **Amended 2026-09-04 — the revision subject changed.** This slice originally
   read "a pinned pull-request head revision", and the Outcome and Boundary
   described resolving a selected *draft pull request's* head. The owner's
   accepted shape is dispatching a branch pushed from a worktree, which has no
   pull request to pin a head from, so the two could not both hold. Branch
   dispatch wins; draft-PR pinning is withdrawn as an artifact of the earlier
   design. The obligations that hung off it are reassigned rather than dropped:

   - **Reporting the revision stays in this slice**, discharged by a run receipt
     recording the dispatched commit, the target invoked, the provisioning
     result, and the first failing command. GitHub already resolves a dispatch
     ref to an immutable SHA and records it, so no resolution machinery is
     needed — only that the run states which SHA it proved.
   - **Staleness marking and cancellation move to
     `remote-ci-completion-claim`.** Both exist to stop an obsolete run
     masquerading as current proof, which matters only once a run may claim
     completion. A partial-evidence dispatch makes no such claim.
   - **Fail-closed revision proof is withdrawn.** It answered "can the head we
     resolved be trusted", a question branch dispatch does not raise: the
     dispatcher names the ref and GitHub pins it.

   The Outcome, Boundary, Unresolved questions and Projection sections were
   rewritten to match on the same date, so no section still states the
   withdrawn design.

   Three reasons it leads:

   - **It is the value.** Each of those four gates costs a contributor
     wall-clock time on their own machine, and the lease in the local chain
     serialises them against every peer worktree on the same box. Dispatching
     one is the whole benefit; the completion claim is not.
   - **It needs no completeness contract.** Partial evidence is what the
     Boundary already asks a selective lane to carry, so this slice makes no
     claim a reviewer must audit for coverage — which is the claim that
     generated most of the authoring risk.
   - **It carries the security surface either way.** A dispatched job executes
     the selected revision's code, so the trust boundary, the same-repository
     restriction and the least-privilege posture must be right in this slice
     regardless of what later slices add.

2. `remote-ci-completion-claim` — **what makes the Outcome sentence true.** Run
   `make ci` undecomposed in a composition and emit a `complete` verdict, so a
   maintainer can ask whether everything the local gate would run passed at that
   revision.

   Deferred behind slice 1 because completeness is the part that needs an
   argument rather than a command: a provisioning probe for the whole graph,
   because `make` holds the graph's ordering but installs nothing; a verdict
   channel a dispatched revision cannot forge; and a recorded base revision,
   because the graph's base-ref-reading checks resolve at run time. Until it
   lands, this intent is `Accepted` and unfulfilled.

Slice 1 is smaller than its description implies. Measured against the fleet on
2026-09-04: `build-check.yml`'s `gate-sast` job already runs `make sast` on its
own runner, so the SAST/SCA gate needs no new job; `pages.yml` already declares
`workflow_dispatch`, so the site-and-browser gate is already triggerable; and
`build-check.yml` needs only a `workflow_dispatch` trigger, a pattern six
workflows in this repository already use. Only the Python corpus is new work —
no job runs it, because `build-check.yml` invokes roughly twenty individually
named, file-targeted `pytest` commands instead. The pull-request event already
fires the decomposed gate set in parallel; what is missing is a way to reach it
without opening a pull request, since every non-release workflow triggers on
`push: branches: [main]` alone.

One parity gap surfaced while measuring, pre-existing and not created by this
intent: `make sast` requires `npm` for its SCA leg, but `tools/requirements-sast.txt`
is a pip manifest that cannot pin it and `gate-sast` runs no `actions/setup-node`,
so that leg scans under the runner's default Node while the repository declares
`"node": ">=24.0.0"` locally. Three of the four SAST legs have enforced version
parity; this one has none. It becomes more visible once contributors dispatch
`build-check.yml` deliberately rather than receiving it through a pull request.

Native Windows and macOS coverage is **carved out** of this intent to
[`native-platform-verification-coverage`](native-platform-verification-coverage.md).
Measured: exactly one test in the repository reads a live Darwin identifier, so
a macOS runner today would execute one meaningful native assertion; three
hand-written platform censuses were each wrong; and the classification the
Projection asks to be mechanically checked is a judgement a lint cannot decide.
The Platform coverage contract above therefore describes the eventual state
across both items, not this intent alone.

## Unresolved questions

Narrowings confirmed by the owner while the implementation contract was being
authored. They are recorded here because this document is the product authority;
a reader must not have to find them downstream.

- **Same-repository refs only.** Dispatch runs a ref in this repository, so
  every executed revision comes from someone who already holds write access.
  Fork pull requests are out of scope. This replaces a same-repository *head*
  check that belonged to the withdrawn draft-pull-request design. The Boundary's least-privilege and no-secrets
  requirements are unchanged; this additionally means no job executes code from
  an account without write access.
- **No pull request required.** This question is **resolved and withdrawn**
  (2026-09-04). It asked which pull-request states could carry a dispatch, and
  the answer is that none is needed: a dispatch names a branch. There is no
  `draft` field to record, because there is no pull request in the mechanism.
- **The composition runs `make ci`, not every lane.** The Boundary asks for "a
  full composition that runs every lane". The composition instead invokes
  `make ci` undecomposed, plus the three jobs `make ci` does not reach. The
  semantic coverage is the same or greater; what changes is that completeness is
  definitional rather than proved over a partition. The six lanes remain
  individually dispatchable.
- **Timeout inputs are median-based, not tail-based.** The Projection asks for
  observed frequency, median duration and tail duration. No tail measurement was
  collected, and the Opportunity's own baseline records medians only, so the
  admissible timeout origins are an existing job budget, that budget scaled for
  a named runner-class difference, or a provisional bound the post-merge
  demonstration replaces with a measured one. Confirmed 2026-09-04.

## Projection

- Fix, for each dispatch surface, its repository command, setup dependencies, timeout, runner label, platform-sensitive reason, expected-skip policy, completion label, and whether it participates in the full composition. A single lane-contract table in one spec was the original shape; the decomposition below supersedes it, and the surface-to-contract mapping is registered as `remote-verification-contract`.
- Keep the feature in one spec and one independently shippable change unless implementation discovery proves that unsafe. **Discovery proved it unsafe** — see the Decomposition amendment of 2026-09-04. The original sequence assumed an immutable-revision spine and a draft-PR demonstration, both withdrawn with that design. The superseding order is: dispatch reach for the surfaces that lack it; then the surface-to-contract mapping; then Node parity for the npm SCA leg; then the composition and its verdict. This is an implementation order, not permission to ship a partial-completion claim.
- Refresh the recent-workflow baseline when authoring the spec and use observed frequency, median duration, and tail duration to set lane timeouts and validate the sequence. Treat trigger-filtered run counts as operational activity, not as a direct measure of maintainer demand.
- Account for GitHub's [manual-dispatch activation boundary](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow): a `workflow_dispatch` definition must exist on the default branch before GitHub will accept a manual dispatch. Require pre-merge construction proof for newly introduced workflows, then a post-merge dispatch of each newly reachable surface against a pushed branch. A dispatch-only workflow runs on no pull request, so automatic pull-request proof is unavailable for one and must not be required of it. Treat that activation proof as rollout evidence for this feature, not as a dependency on another backlog item — and keep the owning spec `Implementing` until every dispatch is recorded.
- Require the spec to prove by construction that the full composition cannot omit a phase or semantic target reachable from `make ci`, while separately inventorying remote-only evidence and keeping `docs/product/intents/ci-parity-linter-scope.md` informational rather than a dependency.
- Require the spec to define exact-revision receipts, stale-result handling, concurrency and cancellation, least-privilege permissions, dependency and skip probes, and failure attribution for each lane.
- Require a mechanically checked platform census that maps every remote command to host-neutral, POSIX-shared, Linux-native, Windows-native, Darwin-native, or platform-simulated evidence. The census must reject unexplained cross-OS duplication and reject a native contract that is represented only by monkeypatching a platform identifier on another operating system.
- Require the macOS lane to use an isolated scratch Keychain and temporary HOME, never the runner's login Keychain or a repository secret. Pin its OS version and architecture, prove every dependency and action supports that architecture, and keep Xcode builds, signing identities, simulators, nested virtualization, and Apple deployment outside this feature.
- Require construction tests for workflow triggers, inputs, permissions, runner selection, command ownership, surface-to-composition membership, and local-to-remote coverage, followed by one recorded dispatch of each newly reachable surface against a pushed branch.

## Opportunity

The existing Actions fleet parallelizes substantial verification, but the build, SAST, and pytest surfaces are not independently dispatchable, the required workflow does not cover the complete local `make ci` test corpus, and selective existing runs do not produce a shared partial-versus-complete evidence contract. Native Windows coverage exists but is not selectively dispatchable; native macOS coverage does not exist in the current workflow fleet. The separate parity-linter intent concerns local correspondence for additional workflows; it does not deliver this execution surface.

Recent evidence supports a single feature with ordered construction rather than unrelated lane projects. In the latest 100 workflow runs observed on 2026-09-03, `build-check` appeared 15 times with a 306-second median, `catalogue-tooling-ci-gates` 14 times with a 199-second median, `codeql` 14 times with a 137-second median, `docs` 12 times with a 188-second median, and Pages 9 times with a 282-second median. These are automatic, path-filtered workflow observations, so they establish operational weight and timeout inputs, not user preference. The prior `ci-gate-parallelization` record also reports that four attempts to split a serial workflow missed implicit provisioning or ordering edges; surface extraction therefore needs construction tests and empirical dispatch proof even when the implementation is mostly workflow YAML.

## Assumptions

- Verified on 2026-09-03: this repository is public and non-archived, GitHub Actions is enabled, and its current verification workflows use standard GitHub-hosted runner labels. GitHub documents [standard hosted-runner use as free and unlimited for public repositories](https://docs.github.com/en/billing/concepts/product-billing/github-actions), so this feature has no Actions-minutes dependency when it stays on those runners. “Unlimited” applies to billable minutes, not instantaneous capacity.
- Standard-runner concurrency remains plan-dependent—currently 20 concurrent jobs on Free, 40 on Pro, 60 on Team, or 500 on Enterprise—and GitHub may rate-limit scaled use. Each hosted job is limited to six hours, each workflow run to 35 days, each matrix to 256 jobs, and each workflow file to 500 KB. The spec must stay well below these [Actions limits](https://docs.github.com/en/actions/reference/limits) through explicit timeouts, bounded matrices, cancellation, and `max-parallel` where appropriate rather than assuming every lane starts immediately.
- GitHub currently offers [standard public-repository Ubuntu, Windows, and macOS runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners). The public `macos-latest` label is currently an arm64 M1 image with less CPU and memory than the public Ubuntu and Windows x64 images, standard macOS concurrency is capped at five jobs on Free, Pro, and Team plans, and `-latest` labels can move between stable images. The spec therefore selects a versioned macOS image and architecture deliberately and budgets it as a focused lane rather than a full three-platform matrix.
- Artifact and cache storage remain finite even though public-repository runner minutes are free. Receipts must be available from bounded checks and logs; retained artifacts or caches may improve diagnosis or speed but cannot be required for correctness or allowed to grow without an explicit retention bound.
- [Larger GitHub-hosted runners](https://docs.github.com/en/actions/concepts/runners/larger-runners) are billed even for public repositories and require eligible organization configuration. They are an optional future optimization, not part of the parity claim or its capacity model.
- Draft pull requests are an acceptable carrier for the exact branch-head revision under test.
- The intended equivalence is semantic coverage on the supported remote environment, with remote CI as a deliberate superset of local CI.

## Source

- Mode: chat-only
- Locator: chat/remote-ci-uplift
- Revision: 2026-09-03
- Authority: transferred-to-repository
