# Spec: Pack JavaScript CI workflow

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0083
- **Discovery:** intent:pack-javascript-ci-workflow
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

A maintainer changing JavaScript in a pack gets a dedicated remote check that installs every canonical pack npm project from a committed lockfile and runs the pack's JavaScript suites without adding JavaScript work to an existing CI job or default local gate. The same workflow can be dispatched on demand, while the existing `make sast` gate remains the sole npm-audit owner and reports advisories for those lockfiles under ADR-0083.

## What Changes

- Pack npm dependency state — each `packs/*/.apm/skills/*/package.json` has a committed sibling lockfile and an exact `allowScripts` declaration.
- Npm project discovery — the existing audit and install-script policy tools admit canonical pack skill roots without traversing arbitrary hidden directories or dependency residue.
- Pack npm inventory — a repository-only check rejects a canonical manifest without a lockfile and a canonical lockfile without a manifest.
- Pack JavaScript execution — a new path-scoped GitHub Actions workflow installs pack projects and runs the render-proof JavaScript suites.
- Pack test coverage accounting — the boundary lint recognizes the JavaScript workflow as a runner and no longer carries the render-proof no-runner exemption.
- Maintainer and architecture records — the dispatch command, verification topology, release history, and run evidence describe the shipped route.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture truth | Applicable — the verification topology owns workflow triggers, responsibility, and coverage | [`docs/architecture/verification-graph.md`](../../architecture/verification-graph.md) | Repository maintainers | Workflow roster and coverage text match the shipped file | The new workflow is described as path-scoped, dispatchable, and separate from `make sast` |
| Maintainer procedure | Applicable — remote dispatch is the preferred full JavaScript verification route | [`AGENTS.md`](../../../AGENTS.md) | Repository maintainers | A branch-safe dispatch command and evidence caveat | The command names the shipped workflow and labels its verdict accurately |
| Release history | Applicable — committed pack content requires a Converters version bump | [`docs/product/changelog.md`](../../product/changelog.md) | Converters maintainers | Free-standing Converters release entry and an explicit Highlights disposition | Version pair, marketplace projection, and release entry agree |
| Delivery evidence | Applicable — manual dispatch activates only after the workflow exists on the default branch | [`notes/verification-ledger.md`](notes/verification-ledger.md) | Implementer and close-work | Local construction gates, automatic pull-request run, existing SAST evidence, and post-merge dispatch reference | Every acceptance criterion has stable evidence and no required remote run remains outstanding |
| Decision rationale | Not applicable — ADR-0083 remains in force and no new architectural decision is introduced | — | — | Existing ADR cited by this spec and plan | No implementation artifact claims that the new workflow owns npm audit |

## Agent Rules

### Always do

- Keep `npm audit` in the existing `make sast` gate; extend its discovery only enough to admit canonical pack npm projects.
- Run the filename-only npm-configuration check and verify the effective registry values before any npm command that can fetch package metadata; run manifest/lockfile parity, lockfile provenance, npm configuration, and install-script policy checks before dependency installation and before packaging.
- Use Node 24, committed lockfiles, `npm ci --ignore-scripts --no-audit`, exact versioned `allowScripts` keys, and SHA-pinned GitHub Actions.
- Keep every installed dependency tree job-local and preserve archive exclusions for `node_modules` and cache directories.

### Ask first

- Ask before adding a JavaScript install, JavaScript test, or new step to an existing workflow or default local gate.
- Ask before changing a direct dependency range, allowing an install script that is absent from the generated lockfile, approving another registry origin or repository npm configuration surface, or removing `--ignore-scripts` from CI installation.
- Ask before adding an automatic event other than the path-scoped pull-request event or widening its paths beyond files that can change the workflow's verdict.
- Ask before waiving the pack eval-harness update required by `packs/AGENTS.md`; record an approved waiver in the verification ledger.

### Never do

- Never run `npm audit` from the new workflow or move, duplicate, or weaken ADR-0083's `make sast` leg.
- Never discover arbitrary dot-directories, symlinked directories, or `node_modules` while admitting `.apm/skills/` pack projects.
- Never fetch or package a canonical pack lockfile entry resolved from git, file, link, non-HTTPS, another host, or without integrity metadata.
- Never read or log an npm configuration file's contents; its presence inside the repository is a fail-closed policy result.
- Never use `npm install`, audit-enabled dependency installation, an unpinned action, a self-hosted or larger runner, a cache, a secret, `pull_request_target`, or write-scoped workflow permissions in this workflow.
- Never remove the render-proof `_NO_RUNNER` entry until the boundary lint recognizes and verifies the real JavaScript runner.

## Testing Strategy

- **Canonical project parity (AC-0004): goal-based construction check.** Synthetic trees exercise zero projects, missing peers, matched peers, future projects, and unrelated hidden projects against the completed parity boundary.
- **Policy discovery coverage (AC-0005, AC-0006): goal-based construction checks.** Synthetic trees exercise the accepted `.apm/skills/` shape, visible non-pack projects, unrelated hidden directories, `node_modules`, symlinked directories, and unreadable inputs against both existing policy tools.
- **Lock and install-script policy (AC-0007): goal-based check.** The existing policy checker compares lockfile `hasInstallScript` entries with exact `name@version` manifest keys after lock generation.
- **Lockfile provenance (AC-0014): goal-based construction check.** Synthetic lockfiles cover the approved npm registry origin and reject git, file, link, non-HTTPS, another host, missing locator, and missing-integrity entries before install or packaging.
- **Npm configuration freeze (AC-0015): goal-based construction check.** Filename-only fixtures reject repository `.npmrc` surfaces without reading them, and workflow construction checks pin and verify the effective registry and registry-host replacement behavior before fetch.
- **Workflow runner accounting (AC-0010): TDD.** A standalone construction test proves the existing boundary parser misses an explicit Node test runner before the parser is extended.
- **Workflow triggers, isolation, posture, and parity disposition (AC-0001, AC-0002, AC-0003, AC-0011): goal-based construction checks.** The focused construction test reads the workflow, carries negative mutations, and runs only in the new workflow or as a focused local test.
- **Dependency installation and JavaScript behavior (AC-0008, AC-0009): goal-based integration check.** The remote job installs every discovered pack project, then runs each existing render-proof suite from its documented working directory.
- **Packaging cleanliness (AC-0012): goal-based check.** Catalogue artifact inspection proves lockfiles ship while installed trees and caches do not.
- **Remote operation and advisory coverage (AC-0013): visual / manual QA.** A successful automatic pull-request run, the existing `gate-sast` result, and a successful post-merge dispatch are recorded because local execution cannot prove GitHub trigger activation.

TDD stub census: one task-level stub is planned. It compiles and has an intended-red result for the workflow-runner parser. All other criteria are goal-based or manual-QA and carry `no stub (mode)` in the plan.

## Acceptance Criteria

- [ ] **AC-0001.** The new workflow declares exactly `workflow_dispatch` with no inputs and `pull_request` with `paths`; it declares no `push`, `schedule`, `workflow_call`, or `pull_request_target` event. Its pull-request paths admit each of these verdict-changing classes: canonical pack JavaScript source, pack JavaScript tests, canonical pack manifests and lockfiles, repository npm configuration filenames, `.gitignore`, the workflow itself, canonical npm-project discovery, parity and provenance code, install-script policy code, pack-test runner accounting, and their focused tests. Every path pattern maps to one or more of those classes and matches no unrelated neighbor; negative fixtures cover unrelated pack source, skill documentation, non-JavaScript tests, unrelated tooling, and unrelated documentation.
- [ ] **AC-0002.** No pre-existing workflow, Make target, or default local gate gains a pack dependency installation or JavaScript-suite invocation, and no pre-existing workflow calls the new workflow. Extending the inputs seen by the existing npm-audit and install-script-policy steps is permitted; adding a step is not.
- [ ] **AC-0003.** The workflow has top-level `permissions: contents: read`, an `ubuntu-latest` job with a finite timeout, SHA-pinned actions, and checkout with `persist-credentials: false`. Concurrency uses only platform-issued values: pull-request runs group by pull-request number and cancel a superseded run for that same pull request, while each manual dispatch groups by its unique run ID and cannot cancel another evidence run; no fork-controlled value contributes to either key. The workflow contains no secret reference, cache action or setup-node cache, artifact upload, write permission, expression-valued runner, self-hosted label, or larger-runner label.
- [ ] **AC-0004.** A repository check derives canonical pack npm projects from `packs/*/.apm/skills/*/` and exits non-zero when any discovered `package.json` lacks a sibling `package-lock.json`, when any discovered lockfile lacks a sibling manifest, or when no canonical pack npm project exists. A new canonical project joins the checked set without editing a roster.
- [ ] **AC-0005.** `tools/audit-npm.py` discovers lockfiles in canonical pack npm projects as well as visible repository projects, while a lockfile below an unrelated dot-directory, `node_modules`, or a symlinked directory remains undiscovered; each accepted and refused class has a self-test.
- [ ] **AC-0006.** `tools/lint-npm-allow-scripts.py` applies the same canonical-pack admission and hidden-directory refusals as AC-0005, and its real-repository assertion proves that every canonical pack lockfile is checked.
- [ ] **AC-0007.** Every canonical pack manifest and lockfile pair passes `tools/lint-npm-allow-scripts.py`: its `allowScripts` map is present, contains exactly the lockfile entries whose package records set `hasInstallScript`, uses exact `name@version` keys, maps each key to `true`, and contains no stale key.
- [ ] **AC-0008.** Under Node 24, the workflow installs every project returned by canonical pack npm discovery with `npm ci --ignore-scripts --no-audit`; it contains no `npm install`, does not name the current projects as an install roster, and fails before JavaScript execution when parity or install-script policy fails.
- [ ] **AC-0009.** From `packs/converters/tests/skills/render-proof/`, the workflow runs `renderer.test.js`, `security.test.js`, and `pipeline.test.js` as three explicit Node invocations, and a failure in any invocation fails the job.
- [ ] **AC-0010.** `tools/lint-pack-test-boundary.py` recognizes the new workflow's Node invocations as a runner for `packs/converters/tests/skills/render-proof`, its `_RUNNER_FILES` inventory names the workflow, and `_NO_RUNNER` contains no entry for that directory. Removing the recognized runner while leaving the exemption absent makes the lint fail; restoring an exemption while the runner exists also makes it fail.
- [ ] **AC-0011.** `tools/lint-ci-parity.py` classifies the new workflow in `WORKFLOW_SCOPE` with an explicit remote-only, path-scoped JavaScript reason rather than the `IN_SCOPE` sentinel, exits 0, and adds no local counterpart.
- [ ] **AC-0012.** A built Converters catalogue artifact contains each canonical pack `package-lock.json` beside its manifest and contains no `node_modules`, npm cache, or dependency-cache entry; the source tree remains clean apart from the authored files after the build output is removed.
- [ ] **AC-0013.** Completion evidence records one successful automatic pull-request run of the new workflow, one successful existing `gate-sast` run whose npm-audit output names the canonical pack lockfiles, and one successful `workflow_dispatch` run after the workflow exists on the default branch. The new workflow's own log contains no npm-audit invocation.
- [ ] **AC-0014.** Before dependency installation and before packaging, the canonical pack-project check exits non-zero unless every non-root package entry in each canonical lockfile has an HTTPS `resolved` URL on `registry.npmjs.org`, non-empty integrity metadata, and no link marker. Git, file, link, non-HTTPS, another host, missing-locator, and missing-integrity entries fail closed; approving another origin requires a spec amendment.
- [ ] **AC-0015.** Before any npm command that can fetch package metadata, before dependency installation, and before packaging, the canonical pack-project check exits non-zero when any `.npmrc` exists inside the repository, detecting filenames without reading or logging file contents. Lock generation and the workflow set `NPM_CONFIG_REGISTRY=https://registry.npmjs.org/` and `NPM_CONFIG_REPLACE_REGISTRY_HOST=never`, verify both effective values before fetch, and fail before npm proceeds if either differs; changing this freeze requires a spec amendment.

## Follow-ons

- JavaScript SAST coverage remains owned by `sast-scanner-coverage-expansion`; dependency auditing and behavior execution do not claim it.
- Dependabot wiring remains separate from this delivery.

## Assumptions

none.
