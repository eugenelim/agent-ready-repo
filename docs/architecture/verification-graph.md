# Verification topology

Two surfaces verify this repository, and neither contains the other. Local
`make ci` is the contributor gate: it reaches repository policy, projections,
lints, scanners, and the complete test corpus, on one machine. The remote
GitHub Actions fleet is the merge gate: it reaches a clean checkout, a fresh
interpreter, native Windows, GitHub-hosted analysis, and the built site, on the
pull request's merge result.

Five remote contexts block a merge. Everything
else the fleet reports is advisory.

This page records measured facts about that topology. Counts and required
contexts are observations dated 2026-11-04; re-measure before relying on one.

Individual gate rules live with the gate:
[ADR-0096](../adr/0096-composed-local-ci-test-target.md) owns the composed test
route, [ADR-0101](../adr/0101-pack-test-isolation-by-default-with-declared-compatibility-classes.md)
owns pack-test isolation, and `tools/lint-ci-parity.py` owns local-to-CI step
correspondence. Section 7 points to a `STATUS: PLANNED` design; sections 1-6 describe
current behavior.

## 1. Local `make ci` is the semantic gate

`make ci` has four direct prerequisites: `lint-ruff`, `lint-mypy`,
`build-check`, and `test-after-build-check`.[^1] A test pins that set, so a
fifth prerequisite cannot be added silently.

`derive_reachable_targets` in `tools/lint-ci-parity.py` reads the target
closure mechanically. It skips variable-named prerequisites and sub-makes
reached through `$(call …)` macros, so a target reachable only that way is
outside its domain.[^2] The individual checks sit below the targets in four
groups: the step list of `build_check()` in `tools/repo/build_gate_chain.py`,
the checks in `tools/catalogue/pre_pr_catalogue.py`, the SAST commands, and the
invocations of the Makefile's `run-test-suite` macro. Read each from source.

### 1.1 Targets play one of four roles

A target's role decides whether a caller may address its contents directly.

| Role | Meaning | Examples |
| --- | --- | --- |
| `PRODUCER` | Writes output a later check reads. Invoke the target; do not substitute its body. | `catalogue build --output dist`; `build-site.py --journeys-only` |
| `STATEFUL-VERIFIER` | Verifies against state a producer wrote, so it carries an ordering edge. | self-host and output drift in `catalogue_tooling/verify.py`; `lint-web-journey-parity.py` |
| `SUITE-DISPATCHER` | Holds no check logic; invokes other checks. | `ci`, `sast`, `test-after-build-check`, `catalogue verify`, `pre_pr_catalogue.py` |
| `SELF-CONTAINED-CHECK` | Reads committed source only. | `lint-ruff`, `lint-mypy`, the chain's lint steps |

### 1.2 Provisioning edges are held by `make` or by the environment

A split of `make ci` fails when it severs an implicit provisioning edge.
`docs/specs/ci-gate-parallelization/spec.md` records four revisions of one
split that each severed a different edge.[^3] The edges divide in two:

- **Ordering edges, held by `make`.** `dist/apm/` from `catalogue build`
  before projected pytest cases; the journeys-only projection before journey
  lints and `test_build_site_routing.py`; verify's temporary build before drift
  checks; both source packages on `PYTHONPATH` for the directory-scoped
  `catalogue-curation` suites; the `pythonpath` entries in pytest
  configuration; `PYTHONDONTWRITEBYTECODE=1` for verify's fresh-output
  comparison; and the `build-check` dependency of `test-after-build-check`. A
  caller that invokes `make ci` whole inherits them.
- **Provisioning edges, held by nothing.** `npm ci --prefix docs-site`;
  `bandit` on `PATH`; full git history for `test-lint-boundary-golden.py`;
  `PyYAML` and `jsonschema`; `cryptography` and `argon2-cffi` for CredBroker
  vault tests; `httpx` for Atlassian suites; a non-editable installed package
  for one provenance-refusal case; and `bandit`, `pip-audit`, `semgrep`, and
  `npm` for the SAST leg.[^4] `make` installs none of them and sets no fetch
  depth.

Two provisioning edges fail open. Without `bandit`, `lint-nosec-form` sets a
caveat and exits 0.

Without `cryptography` or `argon2-cffi`, 21 vault tests and
11 `@requires_crypto` cases skip. The check passes while gating nothing, so an
invoking environment must prove its provisioning by effect.

### 1.3 SAST delegation is a command-line switch

`build-check` chains `make sast` unless `SKIP_SAST` is set (a contributor
shortcut that prints an `INCOMPLETE` banner) or `SAST_DELEGATED` is passed on the
make command line (CI saying another job owns the scan). The origin test is
deliberate: `CI`, `GITHUB_ACTIONS`, `GITHUB_WORKFLOW`, and `RUNNER_ENVIRONMENT`
can each be synthesised by `act` or exported from a shell profile, so none can
tell delegation from ambient state.

An ambient `SAST_DELEGATED` still scans.[^5]
`make ci` with neither switch runs the SAST leg inline.
[ADR-0086](../adr/0086-split-the-sast-gate-into-its-own-ci-job.md) owns the
split; `tools/assert-sast-chain-reachable.py` pins the inline branch because no
CI path executes it.

`gate-sast` runs `make sast` bare. `make sast` guards each tool with
`command -v <tool> || exit 1`, so a green `gate-sast` proves all four tools were
present, and the Python legs share the version bounds in
`tools/requirements-sast.txt`.

The npm audit leg is the exception: no pip
manifest pins it, `gate-sast` runs no `actions/setup-node`, and both
`web/package.json` and `docs-site/package.json` declare `"node": ">=24.0.0"`.
That leg runs on the runner image's default Node, and no check asserts the floor.[^6]

### 1.4 Every scanner runs behind a wrapper with a self-test

Each SAST scanner runs behind a wrapper script, and a self-test runs before the
wrapper.[^7]

| Self-test | Wrapper it precedes |
| --- | --- |
| `tools/test-sast-stderr-gate.py` | `tools/run-bandit-gate.py` |
| `tools/test-audit-requirements.py` | `tools/audit-requirements.py` |
| `tools/test-run-pip-audit-gate.py` | `tools/run-pip-audit-gate.py` |
| `tools/test-audit-npm.py` | `tools/audit-npm.py` |
| `tools/test-semgrep-strict-gate.py` | `tools/run-semgrep-gate.py` |

A scan of healthy input is silent whether the gate works or is broken, so the
self-test runs first to make the difference loud. Self-tests exercise wrapper
logic (filtering, payload handling, canary detection) and stop at the subprocess
boundary: none proves the scanner ran.

Bandit's stderr is a gate signal
([ADR-0084](../adr/0084-nosec-reason-delimiter-and-stderr-as-a-gate.md)).
Semgrep under `--strict --quiet` exits non-zero with empty streams for a
partial-parse or timeout diagnostic, so a bare invocation fails with nothing to
read.

`tools/test-semgrep-argv-boundary.py` runs after the scan and asserts an exact
finding count against a vulnerable fixture and its fixed twin. It covers one of
two custom rule files; `tools/semgrep/env-path-taint.yml` has no fixture and no
self-test. The SCA leg carries no suppressions, and adding one needs a written
diagnosis and an unblock condition.

Known gaps are registered in
[`gates-that-read-clean-while-gating-nothing`](../product/intents/gates-that-read-clean-while-gating-nothing.md):

- A whole-file Semgrep parse failure yields exit 0 with empty output under
  `--strict`.
- `_step_output_drift` in `catalogue_tooling/verify.py` returns no diagnostics
  when the configured output directory is absent, so CAT-V-014 cannot fire in CI
  without `dist/`.
- The `Detect whether SAST-relevant files changed` step in `build-check.yml`
  reads `git diff --name-only` without `-z`. Git C-quotes a path with non-ASCII
  characters, the anchored `^(<dirs>)/` match fails, `skip_sast` is set, and
  `gate-sast` reports success without scanning.
- The parity roster cannot see a command added inside an already-dispositioned
  step (§3.4).

## 2. The remote fleet is the merge gate

The fleet has 18 workflows. Every `uses:` is pinned to a 40-character commit
SHA; `.github/zizmor.yml` requires pinning, and `.github/dependabot.yml`
disables `github-actions` updates for that reason.[^8]

| Workflow | Triggers | Establishes |
| --- | --- | --- |
| `build-check.yml` | `pull_request` and `push` on `main`, `workflow_dispatch` | Five parallel gates (`gate-main`, `gate-sast`, `gate-export-boundary`, `gate-credbroker`, `gate-css-tokens`) joined by an aggregator job displayed as `make build-check`. `gate-main` runs `make build-check … SAST_DELEGATED=1`, ruff, mypy, and curated pytest steps wired in the workflow rather than through a Make target |
| `build-check-windows.yml` | `pull_request`, `push` on `main`, `paths-ignore: docs/**, Makefile, *.md` | Four `windows-latest` jobs and an `ubuntu-latest` aggregate displayed as `make build-check (windows)` |
| `catalogue-tooling-ci-gates.yml` | `pull_request`, `push` | Agentbundle, pack, and hook suites across more than one OS and Python version; supervisor integration; external-catalogue, enterprise-distribution, artifact, disconnected, repo-rewire, and release-impact smokes |
| `ci-security.yml` | `pull_request`, `push` | `gitleaks`; `actionlint`; `zizmor --min-severity high`; an excessive-permissions check |
| `codeql.yml` | `pull_request`, `push`, weekly `schedule` | GitHub-hosted CodeQL analysis for Python |
| `docs.yml` | `pull_request`, `push` | Ten documentation, governance, and hook jobs, including ADR immutability and the intent corpus |
| `pages.yml` | `push` and `pull_request` on `main` (path-filtered), `workflow_dispatch` | Site build, rendered-link audit, plugin suite, web unit suite, browser gate, then deployment ([site publishing](site-publishing.md)) |
| `pack-evals.yml` | weekly `schedule`, `workflow_dispatch` | Report-only activation evaluation against a metered model API ([RFC-0037](../rfc/0037-pack-activation-evals.md)) |
| `pack-javascript.yml` | path-scoped `pull_request`, `workflow_dispatch` | Pack npm installs from lockfiles and render-proof JavaScript suites |
| `iac-release-loop-canary.yml` | `push`, `pull_request`, `workflow_dispatch` | Operational-safety module references |
| `iac-staleness.yml` | weekly `schedule`, `workflow_dispatch` | Terraform and OpenTofu example validation |
| `publish-catalogue.yml` | `workflow_dispatch`, `workflow_call` | Packaging and Artifactory upload |
| `publish-claude-plugins.yml` | `push` on `main` (allowlist of the 16 published pack directories plus every pack's scope manifests), `workflow_dispatch` | Claude plugin publication, gated on the `claude-plugin-publish` environment. `tools/lint-plugin-roster.py` fails when the allowlist and its `PUBLISHED` roster disagree |
| `release-agentbundle.yml` | `push`, `pull_request` | Build, smoke, pre-release gates, PyPI and Artifactory publication |
| `release-credbroker.yml` | `push`, `pull_request` | The same shape for CredBroker |
| `release-jsonl-otlp-exporter.yml` | `pull_request`, tag push `jsonl-otlp-exporter-v*` | Build and wheel smoke on every pull request; tag-gated publish by OIDC trusted publishing |
| `test-corpus.yml` | weekly `schedule`, `workflow_dispatch` | `make test` in four shards, each `make test SHARD=<n> SHARDS=4`, 25-minute timeout |
| `test-roster.yml` | `workflow_dispatch` | The roster suite only, in parallel, 30-minute timeout |

Ten workflows declare `workflow_dispatch`: `build-check`, `iac-release-loop-canary`,
`iac-staleness`, `pack-evals`, `pack-javascript`, `pages`, `publish-catalogue`,
`publish-claude-plugins`, `test-corpus`, and `test-roster`.[^9]

### 2.1 Five contexts block a merge

Branch protection on `main` requires `make build-check`, `gate-main`,
`gate-sast`, `gate-export-boundary`, and `gate-credbroker`. `gate-css-tokens`
runs and feeds the aggregator but is not itself required.

`codeql.yml`,
`build-check-windows.yml`, and `pages.yml` are absent from the set. No repository
ruleset exists.[^10]

Branch protection is repository settings, not repository content. The API is the
source; the in-repository prose records of the set (`build-check.yml` and
`codeql.yml` comments) are incomplete against it.

### 2.2 Automatic checks verify the merge result

For a `pull_request` event, `GITHUB_REF` is `refs/pull/<n>/merge`, and
`actions/checkout` uses it by default. The automatic fleet therefore verifies
the merged result, which GitHub regenerates when the base moves. A head-revision
receipt answers a different question and is distinct evidence.

### 2.3 Workflow-posture tests pin each workflow's security shape

Ten tests assert properties of workflow files. The four on the shared harness
refuse a mutation transform that matches nothing, so a transform that stops
matching fails instead of passing green.[^11]

| Test | Wired through | Driver |
| --- | --- | --- |
| `test-build-check-windows-workflow.py`, `test-ci-security-workflow.py`, `test-codeql-workflow.py` | `build_gate_chain.py` | `tools/posture_harness.py` |
| `test-pack-evals-workflow.py` | `pre_pr_catalogue.py` | `tools/posture_harness.py` |
| `test-build-check-workflow.py`, `test-release-agentbundle-workflow.py` | `build_gate_chain.py` | own driver |
| `test-pages-workflow.py`, `test-pages-concurrency.py` | the Makefile `run-test-suite` macro | own driver |
| `test-pack-javascript-workflow.py` | `pack-javascript.yml` itself | own driver |
| `test-release-jsonl-otlp-exporter-workflow.py` | no caller found in the chain, Makefile, `pre_pr_catalogue.py`, or any workflow | own driver |

`test-corpus.yml` and `test-roster.yml` have no posture test. A change that
widens either file's token, drops its timeout, adds a trigger, or adds a
dispatch input passes every gate except `actionlint` and `zizmor`.

`tools/check-zizmor-excessive-permissions.py` scopes its permissions check to
three workflows: `build-check-windows.yml`, `catalogue-tooling-ci-gates.yml`, and
`codeql.yml`. `ci-security.yml` runs the broad scan at `--min-severity high`,
and `artipacked` (checkout `persist-credentials`) ranks below that floor.

## 3. Coverage gaps run in both directions

### 3.1 Reachable from `make ci`, not from any required remote job

The complete test corpus is the largest gap. `test-corpus.yml` runs it only on a
weekly schedule and on dispatch, so no pull request or push reaches it. No job
runs `make test-after-build-check`.

`gate-main` instead wires curated pytest
paths in the workflow. `catalogue-tooling-ci-gates.yml` narrows the gap with
multi-OS agentbundle, pack, and hook suites, but it is not a required context
and its selection is its own.

### 3.2 Checks the fleet reaches and `make ci` does not

| Check | Why `make ci` excludes it |
| --- | --- |
| `make external-catalogue-smoke` | Not a prerequisite of `ci`; ADR-0096 pins `ci`'s prerequisites |
| `make site-sync`, `site-build`, `site-link-check` | Separate site targets; need `make bootstrap-sites`; build order is load-bearing |
| `make web-browser-gate` | Needs a leased preview port and a downloaded Playwright Chromium |
| `npm test --prefix web` | No Make target; only `pages.yml` runs it |
| Pack npm installation and render-proof suites | No Make target; only the dispatchable `pack-javascript.yml` runs them; `make sast` keeps npm audit |
| `tools/check-site-plugin-offers.py` | No Make target |
| The pack-compatibility characterization (30 subprocesses) | Omitted from local `make test`; `build-check.yml` runs it |
| Windows self-host compatibility | `agentbundle catalogue self-host --check --windows` cannot run on POSIX |
| CodeQL, `gitleaks`, `actionlint`, `zizmor` | GitHub-hosted or workflow-shaped analysis |
| Installed-package suites | The subject hard-exits 3 when CredBroker is not installed |
| Live model evaluation | Metered API; report-only by RFC-0037 |

A green `make ci` says nothing about whether the site builds, its internal links
resolve, or its rendered pages pass the browser gate.

### 3.3 Two rosters keep the local and remote views in step

`tools/lint-ci-parity.py` holds two rosters.[^12]

- `STEP_DISPOSITION` (167 entries) gives every `run:` or `uses:` step of an
  in-scope workflow either a `LOCAL("<target>")` naming a target reachable from
  `make ci`, or a `CI_ONLY("<reason>")`. Both directions fail: an undispositioned
  step, and a disposition naming no step. A second axis names each step's phase
  and dependencies: `PROVISIONING(id=…)` or `CHECK(needs=(…), evidence=…)`.
- `SUITE_DISPOSITION` (149 entries) gives every command of the `run-test-suite`
  macro either `PR_GATED` or `NO_PR_GATE("<reason>")`, so a suite that no pull
  request gates is a written fact.
- `WORKFLOW_SCOPE` classifies all 18 workflows. Only `build-check.yml` is in
  scope; the other 17 carry a stated reason, and a new workflow fails until
  classified.

### 3.4 What the rosters do not prove

A gate added inside a step that already has a disposition is not caught: the
disposition is per step. `roster-residual-hidden-gate-in-known-step` in
`tools/test-lint-ci-parity.py` asserts the residual. A reason string is checked
for presence, never truth.

`PR_GATED_IF` records a condition nobody evaluates.
A declared `_SUITE_SOURCE_EXCEPTIONS` entry asserts coverage by digest-pinned
step body and does not establish that the step executes.

## 4. Platform classification decides what counts as native evidence

Classify a check by what it proves, not where it runs. A second operating system
is warranted only when the classification changes the observable contract.

| Class | Meaning |
| --- | --- |
| `host-neutral` | Identical result on every supported host. |
| `posix-shared` | POSIX semantics shared by Linux and macOS, not Windows. |
| `linux-native` | Depends on Linux. |
| `windows-native` | Depends on Windows APIs, filesystem, locking, ACL, or encoding. |
| `darwin-native` | Depends on macOS: Keychain, system trust, `~/Library`, APFS, BSD process behavior. |
| `platform-simulated` | Forces a platform identifier and passes on any host. |

A `platform-simulated` check is cheap and useful, and it is never evidence for a
native contract.

### 4.1 Darwin: eleven sites, one live native test

The Darwin census is hand-kept; no tool derives it. Sites are named by guard,
not line.[^13]

| # | Site | Darwin-specific behavior |
| --- | --- | --- |
| 1 | `agentbundle/system_trust.py`, `sys.platform != "darwin"` guard | Reads the System keychain, optionally `/etc/ssl/cert.pem`, and runs `/usr/bin/security find-certificate` |
| 2 | `credbroker/_keychain_macos.py`, `SECURITY_BIN` argv builders | Native backend; its argv carry no keychain operand, so every operation targets the default keychain |
| 3 | `credbroker/_core.py`, Tier-2 dispatch | Imports `_keychain_macos` only on live Darwin |
| 4 | `agentbundle/user_config.py`, `darwin` branch | `~/Library/Application Support/agentbundle/config.toml` |
| 5 | `agentbundle/catalogue.py`, `sys.platform` branches | Diagnostics and retry messaging |
| 6 | `tools/repo/worktree_hygiene.py` | `~/Library/Caches/ms-playwright` |
| 7 | `tools/repo/frontend_runtime.py` | The same cache location |
| 8 | `tools/diagnose-tls-trust.py` | Administrator-keychain retry |
| 9 | `packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py` | Selects `_sso_keychain_macos` |
| 10 | `packs/credential-brokers/.apm/shared-libs/credentials_shim.py` | Tier-2 backend selection, two branches |
| 11 | `packs/atlassian/.apm/skills/flow-metrics/scripts/flow_metrics/__init__.py` | `/private` path-prefix normalisation |

A re-measurement must reach `packs/` as well as `packages/` and `tools/`, and
must count the projected copies the build tracks. The APFS filename refusal in
`tools/test-lint-git-ignore.py` is simulated at the encoding seam and is not
admissible as native evidence. Sites 6, 7, and 8 have no live-platform test.

Most Darwin-facing tests are `platform-simulated`. `test_system_trust.py`,
`test_catalogue_trust_fallback.py`, `test_user_config_path.py`, and
`test_trust_fallback_tls.py` force an identifier and pass on Linux. Exactly one
test reads the live platform:
`packs/credential-brokers/tests/pack/test_sso_broker_user_scope.py`.

On a
Darwin host it proves native dispatch. Running the simulated suites on macOS does
not prove a Darwin branch ran. `fcntl.flock` use is `posix-shared`.

### 4.2 Windows: a curated subset with no floor

`build-check-windows.yml` runs four jobs: AgentBundle compatibility
(`agentbundle catalogue self-host --check --windows --root .` plus the work-loop
safe-process suites), CredBroker's full suite, byte-range lock semantics
(`tools/test_windows_lock_semantics.py`, `tools/test_coordination_lease.py`), and
the work-loop supervisor product-ref suites.

Jobs run under `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`. The
workflow declares no collection floor and no expected-skip set, no
`workflow_call`, and no `persist-credentials: false` on its checkouts; two jobs
use `cache: 'pip'`.[^14]

Three native Windows behaviors are covered only by non-native tests: cp1252
broker hardening is source-asserted, unlock reporting injects a
`PermissionError`, and `PureWindowsPath` normalization runs on any host.

### 4.3 A contributor's macOS run is advisory

`make ci` on a Mac is early evidence for `host-neutral` and `posix-shared`
checks. It is not a controlled macOS contract: device management and local
toolchain state can suppress the native behavior it appears to cover. Native
macOS evidence needs a positive assertion that the host is Darwin and the
native path ran.

## 5. Test processes are isolated and floor-guarded

Pack test suites run one pytest process each by default. Grouping needs a
declared compatibility class in `tools/pack_test_compatibility.py`, re-derived
from source by `tools/lint-pack-test-boundary.py`. Five classes exist:
`agent-skill-engineering-contract`, `architect-contract`,
`converters-invocation-contract`, `desk-research-content`, and `linear-intake`.

Two rules bind a caller that addresses a suite directly. A grouped invocation
names every member, because an ancestor path would let a new suite join the
class silently. A floor-bearing suite is the sole target of its invocation,
because `tools/pytest_collection_floor.py` counts the whole session.

Five collection floors exist. Three are Makefile literals: `packages/agentbundle/tests/`
at 3200, `desk-research` at 9, and `desk-research-project-start` at 7.

Two come
from the step table in `tools/repo/build_gate_chain.py`, at 30 and 7. A floor
fails before execution with `{suite}: collected {actual} test(s), expected at
least {minimum}`.

Expected skips fall into five classes: platform-conditional,
optional-dependency-conditional, binary-on-`PATH`-conditional,
environment-conditional, and unconditional `STUB` skips in the workspace-MCP and
loop-events suites. A skip outside those classes is a defect. Every
`run-test-suite` invocation uses bare `-q`, so skip reasons print nowhere except
`build-check.yml`, which passes `-rs`.

## 6. Open gaps are registered as intents

| Gap | Intent |
| --- | --- |
| A gate that reads clean while gating nothing (Semgrep parse, output drift, hidden gate, C-quoted path) | [`gates-that-read-clean-while-gating-nothing`](../product/intents/gates-that-read-clean-while-gating-nothing.md) |
| `gate-main` over its 200-second budget on docs-only pull requests | [`ci-gate-main-runtime-budget`](../product/intents/ci-gate-main-runtime-budget.md) |
| Parity linter covers one of 18 workflows | [`ci-parity-linter-scope`](../product/intents/ci-parity-linter-scope.md) |
| No posture test for `test-corpus.yml` or `test-roster.yml` | [`dispatch-workflow-posture-assertions`](../product/intents/dispatch-workflow-posture-assertions.md) |
| Regex YAML modelling in the build-check posture test; `artipacked` unguarded | [`workflow-posture-harness-consolidation`](../product/intents/workflow-posture-harness-consolidation.md) |
| Windows contract has no floor or skip set; macOS has one native test | [`native-platform-verification-coverage`](../product/intents/native-platform-verification-coverage.md) |
| Required-workflow pinning, Pages required context, deploy ordering | [`required-check-and-deploy-ordering`](../product/intents/required-check-and-deploy-ordering.md) |
| Roster suite not isolated from the working tree | [`roster-suite-parallel-execution`](../product/intents/roster-suite-parallel-execution.md) |
| Untracked plant window in the boundary self-test | [`selftest-untracked-plant-window`](../product/intents/selftest-untracked-plant-window.md) |
| Orphan `tools/test*.py` and e2e specs | [`test-runner-boundary-completion`](../product/intents/test-runner-boundary-completion.md) |
| Scanner suppression and pin hygiene | [`scanner-suppression-and-pin-hygiene`](../product/intents/scanner-suppression-and-pin-hygiene.md) |
| Pack-eval Tier 2-5 rollout and converters gate | [`pack-eval-rollout-completion`](../product/intents/pack-eval-rollout-completion.md) |
| No live-client evidence for Cursor, Claude clean-room, mock MCP, post-merge marketplace | [`live-adapter-and-client-smoke-evidence`](../product/intents/live-adapter-and-client-smoke-evidence.md) |

## 7. Planned: on-demand remote verification

**STATUS: PLANNED.** [`remote-verification.md`](remote-verification.md) holds the dispatchable composition accepted by [`remote-ci-verification-parity`](../product/intents/remote-ci-verification-parity.md). Sections 1-6 describe current behavior.

[^1]: `Makefile` target `ci`; `tools/test-lint-ci-parity.py` case `local-ci-direct-prereqs`.

[^2]: `iter_makefile_rules` and `_sub_make_targets` in `tools/lint-ci-parity.py`.

[^3]: `docs/specs/ci-gate-parallelization/spec.md` and its plan record the severed edges.

[^4]: Skip strings and guards: `tests/roster/test_credential_user_scope_invocation.py`, `tools/repo/build_gate_chain.py`, `tools/repo/editable_install_guard.py`, the Makefile `command -v` guards.

[^5]: The `SAST_DELEGATED` origin test and its comment in the `Makefile`; `tools/assert-sast-chain-reachable.py`.

[^6]: `gate-sast` job in `.github/workflows/build-check.yml`; `tools/requirements-sast.txt`; `tools/check-semgrep-version.py`; `engines.node` in `web/package.json` and `docs-site/package.json`.

[^7]: `sast` target in the `Makefile`; wrapper and self-test scripts under `tools/`.

[^8]: `.github/zizmor.yml`; `.github/dependabot.yml`.

[^9]: `grep -l workflow_dispatch .github/workflows/*` on 2026-11-04 returns the ten files named.

[^10]: `GET /repos/{owner}/{repo}/branches/main/protection` on 2026-11-04 returned the five contexts; `GET …/actions/permissions` and `…/permissions/workflow` returned the four settings recorded in remote-verification.md. The aggregator job `build-check` in `build-check.yml` lists five `needs:`.

[^11]: `tools/posture_harness.py`; the `_script_step` entries in `tools/repo/build_gate_chain.py`; `run-test-suite` in the `Makefile`; `tools/catalogue/pre_pr_catalogue.py`.

[^12]: `STEP_DISPOSITION`, `SUITE_DISPOSITION`, and `WORKFLOW_SCOPE` in `tools/lint-ci-parity.py`; entry counts measured by importing the module on 2026-11-04.

[^13]: Each named module under `packages/`, `tools/`, and `packs/`; the live-platform test is `test_sso_broker_user_scope.py`.

[^14]: `.github/workflows/build-check-windows.yml` job list and steps; `agentbundle/catalogue_tooling/self_host_windows.py` holds the canonical Windows test list.
