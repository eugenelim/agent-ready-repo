# Verification facts

**This is a facts document, not a design document.** Almost every claim here is
a measurement of what currently exists — the target set `make ci` reaches, the
workflow fleet and its triggers, which contexts block a merge, which checks one
surface reaches and the other does not, and how many tests actually exercise a
second operating system. Where it explains rather than measures, it says so:
sections 2.1, 2.2 and 2.3 carry the reasoning a measurement cannot supply.

That distinction matters because **a measured fact typed by hand goes stale
silently.** Three platform censuses in this document's own history were wrong,
and section 3.2 records two in-repository prose claims about required contexts
that are still incomplete today. Prefer re-measuring over trusting a number
here, and treat every count as dated rather than invariant. The standing
question of which of these facts should be generated instead of written is
surveyed in
[`../product/research/derived-repository-facts-survey.md`](../product/research/derived-repository-facts-survey.md).

Decisions live in [ADRs](../adr/); proposals live in [RFCs](../rfc/). Section 7
is **PLANNED** and carries its own banner; sections 1-6 and 8 describe current
behavior.

Citations name a symbol or a literal string where one exists, and a line number
only where nothing stabler is available. Line numbers move; the code they point
at is what the claim rests on.

## 1. Purpose and boundary

Two surfaces verify this repository, and they prove different things.

- **Local `make ci`** is the contributor gate. It is authoritative for semantic
  coverage: repository policy, projections, lints, scanners, and the complete
  test corpus. It runs on one contributor machine, so it proves nothing about
  another operating system and nothing about an installed-package layout.
- **The remote GitHub Actions fleet** is the merge gate. It is authoritative for
  environment: a clean checkout, a fresh interpreter, native Windows, and
  GitHub-hosted analysis. Its automatic jobs are path-filtered and verify the
  pull request's *merge result*, not its head revision.

Neither surface is a superset of the other. Section 4 inventories the gap in
both directions.

This document owns the verification topology. It does not own the rules of any
individual gate: `tools/lint-ci-parity.py` owns local-to-CI step correspondence,
[ADR-0096](../adr/0096-composed-local-ci-test-target.md) owns the composed test
route, and [ADR-0101](../adr/0101-pack-test-isolation-by-default-with-declared-compatibility-classes.md)
owns pack-test isolation.

## 2. The `make ci` semantic graph

`make ci` has exactly four direct prerequisites:

```make
ci: build-check lint-ruff lint-mypy test-after-build-check
```

That set is pinned. `tools/test-lint-ci-parity.py`'s `local-ci-direct-prereqs`
case asserts it verbatim, so a fifth prerequisite cannot be added silently.

Read its target closure mechanically rather than by eye —
`derive_reachable_targets` in `tools/lint-ci-parity.py` exposes the reader:

```python
derive_reachable_targets(Path("Makefile").read_text(), entrypoint="ci")
# {'build-check', 'build-check-unleased', 'ci', 'lint-editable-install',
#  'lint-mypy', 'lint-ruff', 'sast', 'sast-unleased',
#  'test-after-build-check', 'test-after-build-check-unleased'}
```

That reader is useful but not total. `iter_makefile_rules` drops any
prerequisite token beginning with `$`, `_sub_make_targets` drops any `$(MAKE)`
operand containing `=` or beginning with `$`, and the recipe scan for `$(MAKE)`
does not expand `$(call …)` macros — so a variable-named prerequisite, or a
sub-make reached only through a Make macro, is outside the computed domain.
`ci`'s own recipe is `$(call gate_verdict,make ci)`.

Underneath those targets sit the individual checks, in four groups:
`build_check()`'s step list in `tools/repo/build_gate_chain.py` (whose first
step, `catalogue verify`, is itself a step table), the checks in
`tools/catalogue/pre_pr_catalogue.py`, the SAST leg's commands, and the
invocations in the Makefile's `run-test-suite` macro. Read each from its source;
a count here would be wrong by the next commit that touches one.

### 2.1 Invocation role — why the pieces are not independently substitutable

A `make` target here plays one of four roles, and the role decides whether a
caller may address the target's contents directly.

| Role | What it means | Examples |
| --- | --- | --- |
| `PRODUCER` | Writes repository or build output that a later check reads. Invoke the target; do not substitute its body. | `catalogue build --output dist`; `build-site.py --journeys-only` inside `pre_pr_catalogue.py` |
| `STATEFUL-VERIFIER` | Verifies against state a `PRODUCER` must already have written, so it carries an implicit ordering edge. | self-host drift and output drift in `catalogue_tooling/verify.py`; journey parity in `lint-web-journey-parity.py`; the projected cases in `pytest tests/` |
| `SUITE-DISPATCHER` | Carries no verification logic of its own; it only invokes other checks. | `ci`; `sast` / `sast-unleased`; `test-after-build-check` / `-unleased`; `catalogue verify`; `pre_pr_catalogue.py` |
| `SELF-CONTAINED-CHECK` | Reads only committed source and needs no prior step. | `lint-ruff`; `lint-mypy`; the lint and self-test steps in the chain |

Two dispatchers have no per-check callable name. `catalogue verify`'s steps
are internal callables with no CLI or Make entry point, and
`test-after-build-check`'s invocations are addressable by path but have no
per-suite Make target.

### 2.2 Provisioning and ordering edges

The graph carries implicit edges that a naive split severs.
`docs/specs/ci-gate-parallelization/spec.md` records why: it is "a 56-step
sequence with **implicit, order-dependent provisioning**, built so each step
inherits everything before it, and no manifest exists." Four revisions of that
split each severed a different edge, and its plan records the conclusion —
"Reconstruction by inspection kept missing edges."

The edges a caller must reproduce **if it decomposes the graph**:

| # | Consumer that fails | Missing provisioning | Recorded evidence |
| --- | --- | --- | --- |
| 1 | projected cases in `pytest tests/` | `dist/apm/` from `catalogue build` | `pytest.skip("dist/apm/ absent — run make build-self")` in `tests/roster/test_credential_user_scope_invocation.py` |
| 2 | journey parity, pack-journey and journey-contract lints, `test_build_site_routing.py` | the journeys-only projection outputs | `… is stale — run python3 tools/build-site.py --journeys-only` |
| 3 | generated-manifest and drift checks | the temporary-directory build from verify's build step | `catalogue_tooling/verify.py` |
| 4 | `npm run test:plugins --prefix docs-site` | `npm ci --prefix docs-site` | `make test: docs-site deps missing` in the Makefile |
| 5 | `lint-nosec-form` | Bandit on `PATH` — without it the check "sets a caveat and exits 0, dropping its unknown-id check" | `tools/repo/build_gate_chain.py` |
| 6 | `test-lint-boundary-golden.py` | full git history | `empty stdout — fetch full history` |
| 7 | the two directory-scoped `catalogue-curation` suites | both source packages on `PYTHONPATH` after the `cwd` change | `tools/repo/build_gate_chain.py` |
| 8 | bare root and `tools/` collection | `pythonpath = [".", "packages/agentbundle", "packages/credbroker"]` | `ModuleNotFoundError: No module named 'tools'` |
| 9 | verify's fresh-output comparison | `PYTHONDONTWRITEBYTECODE=1` | stale `__pycache__` fails it "on a clean tree too" |
| 10 | deep catalogue lint, guide validation | `PyYAML`, `jsonschema` | `tools/requirements.txt` |
| 11 | CredBroker vault semantics | `cryptography>=42`, `argon2-cffi>=23` | 21 vault tests and 11 `@requires_crypto` cases skip silently |
| 12 | Atlassian suites | `httpx>=0.27` | `tools/lint-ci-parity.py` |
| 13 | one provenance-refusal case in the AgentBundle suite | a non-editable installed package | `tools/repo/editable_install_guard.py` |
| 14 | the SAST leg | `bandit`, `pip-audit`, `semgrep`, `npm`/Node | the Makefile's four `command -v` guards |
| 15 | `test-after-build-check-unleased` run alone | the `build-check` dependency edge, which owns the checks it therefore skips | ADR-0096 |

Edges 5 and 11 are the dangerous class: absent provisioning makes the check pass
while gating nothing.

**The operative lesson splits the table in two.** The *ordering* edges — 1, 2,
3, 7, 8, 9 and 15 — are held by `make` itself, so a caller that invokes
`make ci` whole inherits them and cannot sever them. That is why section 7's
composition does not decompose.

The *provisioning* edges — 4, 5, 10, 11, 12, 13 and 14, plus full history — are
not held by anything. `make` installs no `bandit`, no `cryptography`, no
`pytest`, and sets no fetch depth. An invoking environment must supply them, and
six of these are the fail-open class: the check passes while gating nothing.
Invoking `make ci` whole is therefore necessary and not sufficient — the
environment is a separate obligation, and section 7 discharges it with a probe
of effect rather than a list of install steps.

### 2.3 The SAST delegation switch

`build-check` chains `make sast` unless one of two things holds:

- `SKIP_SAST` is set — a contributor shortcut that prints an `INCOMPLETE` banner.
- `SAST_DELEGATED` is passed **on the make command line**, which is how CI says
  "another job owns the scan."

The command-line origin test is deliberate. The Makefile records why: `CI`,
`GITHUB_ACTIONS`, `GITHUB_WORKFLOW` and `RUNNER_ENVIRONMENT` are each either
synthesised by `act` or exportable from a shell profile, so none can distinguish
a deliberate delegation from ambient environment state. An ambient
`SAST_DELEGATED` runs the scan.

[ADR-0086](../adr/0086-split-the-sast-gate-into-its-own-ci-job.md) owns the
split and keeps the Makefile chain intact so a contributor machine still scans.
`tools/assert-sast-chain-reachable.py` pins that branch, because after the split
no CI path executes it and nothing else would notice its deletion.

A consequence that section 7 relies on: `make ci` invoked with **neither**
switch runs the SAST leg inline, so one undecomposed invocation covers both
`gate-main`'s and `gate-sast`'s semantic content.

**Tool parity between `gate-sast` and a local `make sast` is enforced for three
legs of four.** `gate-sast` runs the target bare — it passes no
`SAST_DELEGATED`, so it executes the same undelegated code path a contributor
machine runs. `make sast` guards each tool with `command -v <tool> || exit 1`,
so an absent tool fails the target rather than skipping a leg silently; a green
`gate-sast` therefore proves all four were present. Versions agree for the
Python legs because the job installs `tools/requirements-sast.txt`, the same
manifest `tools/check-semgrep-version.py` reads its bounds from.

The npm SCA leg is the exception. `make sast` requires `command -v npm`, but
`tools/requirements-sast.txt` is a pip manifest and cannot pin it, and
`gate-sast` runs no `actions/setup-node` step. That leg therefore executes
against the runner image's default Node, while `docs-site/package.json` and
`web/package.json` both declare `"node": ">=24.0.0"` for local work. No check
asserts the runner satisfies that floor, so this is the one leg on which a
remote scan and a local scan can disagree without either reporting a version
problem.

## 3. The remote workflow fleet

Fourteen workflows. Every `uses:` in the fleet is pinned to a 40-character
commit SHA; `.github/zizmor.yml` requires pinning rather than suppressing
`unpinned-uses`, and `.github/dependabot.yml` records that `github-actions`
updates are deliberately disabled for that reason.

| Workflow | Triggers | What it establishes |
| --- | --- | --- |
| `build-check.yml` | `pull_request`, `push` on `main` | Four parallel gates — `gate-main`, `gate-sast`, `gate-export-boundary`, `gate-credbroker` — aggregated by a job displayed as `make build-check`. `gate-main` runs `make build-check … SAST_DELEGATED=1` plus ruff and mypy, **and further pytest steps wired directly in the workflow rather than through a Make target** |
| `build-check-windows.yml` | `pull_request`, `push` on `main`, `paths-ignore: docs/**, Makefile, *.md` | Three `windows-latest` jobs plus an `ubuntu-latest` aggregate displayed as `make build-check (windows)` |
| `catalogue-tooling-ci-gates.yml` | `pull_request`, `push` | Gates A-G. **`Gate A-tests` and `Gate A-packs` run agentbundle, pack and hook suites across more than one operating system and Python version** — the largest existing remote pytest coverage, though not a required context, and each leg set is deliberately asymmetric (read the matrices in the file; they are not the cross product). Gates B-G cover external-catalogue portability, enterprise distribution, artifact smoke, disconnected smoke, repo rewire, release impact |
| `ci-security.yml` | `pull_request`, `push` | `gitleaks` secret scan; `actionlint` + `zizmor --min-severity high`, plus an excessive-permissions checker |
| `codeql.yml` | `pull_request`, `push`, `schedule` | GitHub-hosted CodeQL analysis for Python |
| `docs.yml` | `pull_request`, `push` | Nine documentation and governance lints, including ADR immutability |
| `pages.yml` | `push`, `pull_request` on `main` (path-filtered), `workflow_dispatch` | Site build, rendered-link audit, docs-site plugin suite, web unit suite, Playwright browser gate, then deployment |
| `pack-evals.yml` | `schedule`, `workflow_dispatch` | Report-only activation evaluation against a metered model API; [RFC-0037](../rfc/0037-pack-activation-evals.md) keeps it off the pull-request path |
| `iac-release-loop-canary.yml` | `push`, `pull_request`, `workflow_dispatch` | Operational-safety module references |
| `iac-staleness.yml` | weekly `schedule`, `workflow_dispatch` | Terraform and OpenTofu example validation |
| `publish-catalogue.yml` | `workflow_dispatch`, `workflow_call` | Packaging and Artifactory upload |
| `publish-claude-plugins.yml` | `push` on `main`, `workflow_dispatch` | Claude plugin publication |
| `release-agentbundle.yml` | `push`, `pull_request` | Build, smoke, pre-release gates, PyPI and Artifactory publication |
| `release-credbroker.yml` | `push`, `pull_request` | The same shape for CredBroker |

### 3.1 Workflow-posture tests

Seven tests assert properties of workflow files, wired in **three** places:

- Four as `_script_step` entries in `build_check()` —
  `test-build-check-windows-workflow.py`, `test-build-check-workflow.py`,
  `test-ci-security-workflow.py`, `test-codeql-workflow.py`.
- Two in the `run-test-suite` macro, so they run via `make test` —
  `test-pages-workflow.py` and `test-pages-concurrency.py`.
- One in `pre_pr_catalogue.py` — `test-pack-evals-workflow.py`.

Four of them share `tools/posture_harness.py` — the windows, ci-security,
codeql and pack-evals tests — which drives an in-process mutation matrix,
refuses a transform whose literal is not present exactly once, and fails an
assertion family that is evaluated but never mutated.
`tools/test-build-check-workflow.py` carries its own mutation driver instead,
and records why such a matrix ships rather than being run once: a transform that silently stopped matching still printed a
green result, and "a verification that cannot produce a negative is not a
verification."

### 3.2 Required contexts

Branch protection is repository settings rather than repository content, so no
file here is authoritative. It is readable through the authenticated API, and
`GET /repos/{owner}/{repo}/branches/main/protection` returned this required set
on 2026-09-04:

```
make build-check   gate-main   gate-sast   gate-export-boundary   gate-credbroker
```

**Both in-repository prose records are incomplete against that set.**
`build-check.yml` names `gate-main`, `gate-sast` and `gate-export-boundary` —
three of the five, omitting `gate-credbroker`. `codeql.yml` says branch
protection requires only `"make build-check"`, which is one of the five rather
than the whole set. `gate-credbroker` is required by the ruleset and named by
neither record.

Read this table as a dated observation, not an invariant: settings change
outside version control, and a stale copy here is the failure mode the
divergence above demonstrates. Treat the API as the source and re-read it
before relying on the set.

`tools/test-pages-workflow.py` records that `pages.yml` is *not* a required
merge context, which the API confirms — `codeql.yml`,
`build-check-windows.yml` and `pages.yml` are all absent from the required set,
so most surfaces in the fleet report without blocking.

### 3.3 What an automatic pull-request check verifies

For the `pull_request` event, `GITHUB_SHA` is the last merge commit and
`GITHUB_REF` is `refs/pull/<n>/merge`. `actions/checkout` uses `GITHUB_REF` by
default, so the automatic fleet verifies the **merged result**, not the head
revision, and that merge ref is regenerated whenever the base branch moves.

This is the right default for a merge gate and the reason a head-revision
receipt is distinct evidence: the two answer different questions.

## 4. Coverage inventory: local versus remote

### 4.1 Reachable from `make ci` but not from any required remote job

**The complete test corpus.** No job in the fleet runs `make test` or
`make test-after-build-check`. `gate-main` runs `make build-check … SAST_DELEGATED=1`
plus ruff and mypy, and `build-check.yml` then wires curated
pytest paths directly rather than invoking the Makefile's test route. The
accepted intent records the same gap: "the required workflow does not cover the
complete local `make ci` test corpus."

`catalogue-tooling-ci-gates.yml`'s two Gate A legs narrow it considerably — they
run agentbundle test discovery and the pack and hook suites across two operating
systems and two Python versions — but that workflow is not a required context
and its selection is its own, not the Makefile's.

`tools/lint-ci-parity.py` holds a disposition per `build-check.yml` step: each
declares the make target that covers it locally, or why no local gate can. Its
own limitation bounds what a clean run proves:

> A gate added inside a step that already has a disposition is not caught: the
> disposition is per step, so a second command on a later line of an existing
> step changes nothing the roster sees.

Only `build-check.yml` is in scope for that linter. `WORKFLOW_SCOPE` classifies
the other thirteen as out of scope, each with a reason, and fails on an
unclassified new workflow.

### 4.2 Semantic checks in the repository that `make ci` does not reach

| Check | Why `make ci` excludes it |
| --- | --- |
| `make external-catalogue-smoke` | "Deliberately NOT a prerequisite of `ci`" — ADR-0096 pins `ci`'s direct prerequisites, so chaining it would need a frozen-spec amendment |
| `make site-sync`, `site-build`, `site-link-check` | Separate site-generation targets; require `make bootstrap-sites`, and build order is load-bearing because the web build cleans `build/` before docs write `build/docs/` |
| `make web-browser-gate` | Needs a leased preview port and a downloaded Playwright Chromium |
| `npm test --prefix web` (unit suite) | No Make target invokes it; only `pages.yml` runs it |
| `tools/check-site-plugin-offers.py` | No Make target invokes it |
| The 30-subprocess pack-compatibility characterization | Deliberately omitted from local `make test`; `build-check.yml` runs it instead |
| Windows self-host compatibility | `agentbundle catalogue self-host --check --windows --root .` cannot be reproduced by a POSIX `make ci` |
| CodeQL, `gitleaks`, `actionlint`, `zizmor` | GitHub-hosted or workflow-shaped analysis with no local equivalent |
| Installed-package suites | The subject hard-exits 3 when CredBroker is not installed, so the behavior requires an installed layout |
| Live model evaluation | Metered API; report-only by RFC-0037 |

The site and browser column is the largest gap: a green `make ci` says nothing
about whether the site builds, its internal links resolve, or the rendered pages
pass their quality gate.

## 5. Platform classification

Classify a check by what it proves, not by where it happens to run. A second
operating system is warranted only when the classification changes the
observable contract.

| Class | Meaning |
| --- | --- |
| `host-neutral` | The result is identical on every supported host. |
| `posix-shared` | Depends on POSIX semantics shared by Linux and macOS, but not Windows. |
| `linux-native` | Depends on Linux specifically. |
| `windows-native` | Depends on Windows APIs, filesystem, locking, ACL, or encoding behavior. |
| `darwin-native` | Depends on macOS: Keychain, system trust, `~/Library` layout, APFS, or BSD process behavior. |
| `platform-simulated` | Forces or parametrises a platform identifier and passes on any host. |

A `platform-simulated` check is useful and cheap, and it is never evidence for a
native contract. That distinction is the whole reason the classification exists.

### 5.1 Darwin census

The table below is a **copy**. `tools/lint-platform-census.py` derives the
canonical set from the repository and fails when this copy disagrees, following
the canonical-versus-duplicate shape of `tools/lint-knowledge-surface-parity.py`.
Do not hand-edit a row to fix a lint failure; re-derive.

The derivation must reach `packs/` as well as `packages/` and `tools/`. Two
hand-written drafts of this census missed the live Darwin dispatch in
`packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py`,
`packs/credential-brokers/.apm/shared-libs/credentials_shim.py` and
`packs/atlassian/.apm/skills/flow-metrics/scripts/flow_metrics/__init__.py`,
which is why the census is derived rather than proofread.

Each site is named by its guard rather than by line number.

| # | Site | What is Darwin-specific |
| --- | --- | --- |
| 1 | `agentbundle/system_trust.py`, guarded by `if sys.platform != "darwin"` | Reads `/Library/Keychains/System.keychain`, optionally `/etc/ssl/cert.pem` or `SystemRootCertificates.keychain`, and invokes `/usr/bin/security find-certificate -a -p <keychain>` |
| 2 | `credbroker/_keychain_macos.py`, the `SECURITY_BIN` argv builders | The native `/usr/bin/security` backend. Its `add-generic-password`, read and delete argv carry **no keychain operand**, so every operation targets the *default* keychain |
| 3 | `credbroker/_core.py`, the Tier-2 dispatch | Imports `_keychain_macos` only on live Darwin; labels Tier 2 `"macOS Keychain"` |
| 4 | `agentbundle/user_config.py`, the `p == "darwin"` branch | `~/Library/Application Support/agentbundle/config.toml` |
| 5 | `agentbundle/catalogue.py`, its `sys.platform` branches | Diagnostics and retry messaging differ on Darwin |
| 6 | `tools/repo/worktree_hygiene.py`, the Playwright cache resolver | `~/Library/Caches/ms-playwright` |
| 7 | `tools/repo/frontend_runtime.py`, the Playwright cache resolver | The same cache location |
| 8 | `tools/diagnose-tls-trust.py`, the administrator-keychain retry | A retry path taken only on Darwin |
| 9 | `packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py`, its `sys.platform == "darwin"` dispatch | Selects `_sso_keychain_macos` on Darwin |
| 10 | `packs/credential-brokers/.apm/shared-libs/credentials_shim.py`, its two `sys.platform == "darwin"` branches | Tier-2 backend selection in the shipped shim |
| 11 | `packs/atlassian/.apm/skills/flow-metrics/scripts/flow_metrics/__init__.py`, its `sys.platform == "darwin"` branch | `/private` path-prefix normalisation, which only Darwin applies |

Plus one filesystem assumption the census tracks separately: the APFS filename
refusal in `tools/test-lint-git-ignore.py`, which is simulated at the encoding
seam because the filename cannot be planted on APFS. Being necessarily
simulated, it is not admissible as native evidence.

Three sites carry no live-platform test today — site 6 and site 7 have test
files with no platform reference, and site 8 has no test file at all. They are
recorded here as `darwin-native` with no native coverage, which is a stated gap
rather than an unmet promise.

**Most Darwin-facing tests are `platform-simulated`, but not all.**
`test_system_trust.py`, `test_catalogue_trust_fallback.py`,
`test_user_config_path.py` and `test_trust_fallback_tls.py` force a platform
identifier or substitute an anchor, and pass on Linux. A search for a
Darwin-only skip marker across every test and `conftest.py` returns nothing.

The exception matters, because it is the evidence a macOS job most wants:
`packs/credential-brokers/tests/pack/test_sso_broker_user_scope.py` branches on
the *live* `sys.platform` and asserts the Darwin backend is the one selected. It
forces nothing, so on a Darwin host it proves native dispatch.

The consequence matters: running these suites on a macOS host does not by itself
prove a Darwin branch executed, because the simulated cases pass either way.
Native macOS evidence needs a positive assertion that the host is Darwin and the
native path was taken.

`fcntl.flock` usage in `frontend_runtime.py`, `coordination_lease.py` and
`test_sso_profile_lock.py` is `posix-shared`, not `darwin-native`.

### 5.2 Windows census

Native Windows behavior is broad — `msvcrt` byte-range locking, Credential
Manager `ctypes` bindings, ACL verification via `icacls … /findsid`, the
CredBroker environment allowlist, path normalization, and process termination.

`build-check-windows.yml` covers a curated subset: the Windows self-host
compatibility command, the full CredBroker suite, `test_windows_lock_semantics.py`,
`test_coordination_lease.py`, and `test_loop_cohort_cli.py`, all under
`PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`. It asserts no collection floor and
no expected-skip set.

Three native Windows behaviors are represented only by non-native tests, and are
recorded here so the gap is visible rather than assumed closed: cp1252 broker
hardening is source-asserted; Windows unlock reporting injects a `PermissionError`
rather than exercising the platform; and `PureWindowsPath` separator
normalization runs on any host.

### 5.3 Contributor macOS is advisory

A contributor running `make ci` on a Mac produces useful early evidence for
`host-neutral` and `posix-shared` checks, and incidentally exercises some Darwin
branches. It is not a controlled macOS contract: it proves nothing about the
Ubuntu runner, it cannot substitute for a controlled macOS runner, and
enterprise device management or local toolchain state may suppress the very
native behavior it appears to cover.

## 6. Process isolation and collection floors

Pack test suites run one pytest process each by default
([ADR-0101](../adr/0101-pack-test-isolation-by-default-with-declared-compatibility-classes.md)).
Grouping requires an explicitly declared compatibility class in
`tools/pack_test_compatibility.py`, re-derived from source on every run by
`tools/lint-pack-test-boundary.py`. Five classes are declared:
`agent-skill-engineering-contract`, `architect-contract`,
`converters-invocation-contract`, `desk-research-content`, and `linear-intake`.

Two constraints bind any caller that addresses a suite directly:

- A grouped invocation must name **every** member. An ancestor path would let a
  future suite join the class silently, and `lint-pack-test-boundary.py` refuses
  it.
- A floor-bearing suite must be the **sole** target of its invocation, because
  `tools/pytest_collection_floor.py` counts the whole pytest session while
  `--collection-floor-suite` is only a label.

Five collection floors exist. Three are Makefile literals —
`packages/agentbundle/tests/` at 3200, `desk-research` at 9,
`desk-research-project-start` at 7. Two are supplied by
`tools/repo/build_gate_chain.py`, which formats `--minimum-collected={floor}`
from its own step table rather than carrying literals inline. A floor fails
before execution with `{suite}: collected {actual} test(s), expected at least
{minimum}`.

Expected skips are real and load-bearing. They fall into five classes:
platform-conditional, optional-dependency-conditional (covering `httpx`,
`credbroker`, the `[crypto]` extra, `docx`, `openpyxl`, `pptx`, Pillow, `build`,
`setuptools`, PyYAML, `cryptography`, `argon2`), binary-on-`PATH`-conditional
(`mmdc`, `node`, `openssl`, `git`), environment-conditional, and unconditional
`STUB` skips concentrated in the workspace-MCP and loop-events suites. A skip
outside those classes is a defect, not a fact about the host.

One reporting constraint bounds what a caller can observe: every invocation in
the `run-test-suite` macro is bare `-q`, and pytest's default reporting prints
no skip *reasons*. The repository's one place that needs them passes `-rs`
explicitly, in `build-check.yml`.

## 7. PLANNED: on-demand remote verification

> **STATUS: PLANNED.** This section describes the future-state surface accepted
> by [`remote-ci-verification-parity`](../product/intents/remote-ci-verification-parity.md).
> It is not a statement of current repository behavior — no `remote-verify.yml`
> exists yet, and `build-check-windows.yml` declares no `workflow_call`. Keep
> this banner until every job, the receipt contract, and the construction tests
> described here are implemented and verified, then update it to **CURRENT** and
> fold the roster into section 3.

### 7.0 Measured starting state

Most of what an on-demand surface needs already exists. These four facts were
measured against the fleet on 2026-09-04 and should be treated as the baseline
rather than re-derived:

| Capability | Current state | Remaining work |
| --- | --- | --- |
| Security scan, separately runnable | `build-check.yml`'s `gate-sast` job already runs `make sast` on its own runner | none — it is reached by any dispatch of that workflow |
| Site and browser gate, dispatchable | `pages.yml` already declares `workflow_dispatch` | none |
| Build and policy chain, dispatchable | `build-check.yml` declares only `pull_request` and `push: branches: [main]` | add `workflow_dispatch` |
| Complete test corpus, runnable remotely | no job runs it; `build-check.yml` invokes roughly twenty individually named, file-targeted `pytest` commands | a corpus job is genuinely new |

Two supporting facts follow from the same measurement:

- **A dispatched `build-check.yml` scans.** Its SAST relevance detector is
  `if: github.event_name == 'pull_request'`, and its consumer is
  `if: steps.changes.outputs.skip_sast != 'true'`. On a dispatch the detector
  never runs, so the output is empty and the comparison is true. The detector
  fails open toward scanning.
- **`workflow_dispatch` is established practice here, not a new pattern.** Six
  workflows already declare it: `iac-release-loop-canary.yml`,
  `iac-staleness.yml`, `pack-evals.yml`, `pages.yml`,
  `publish-catalogue.yml`, and `publish-claude-plugins.yml`.

The gap a dispatch surface closes is therefore narrower than it first appears:
every non-release workflow triggers on `push: branches: [main]` only, so
pushing a feature branch fires nothing, while opening a pull request already
fires the decomposed gate set in parallel.

### 7.1 Outcome

A maintainer selects a pull request whose head is a branch in this repository
and dispatches one named lane or the complete composition. The run resolves that
pull request's head to an immutable commit SHA, checks out exactly that SHA, and
reports it. A selective run is labelled partial evidence. Only the composition
may claim completion.

### 7.2 Completeness is definitional, not proven

The composition runs **`make ci` itself, undecomposed**, on the checked-out
revision. There is no partition to omit a target from and no roster that can
drift from the graph it claims to cover, because the composition does not
enumerate targets — it invokes the one target whose definition *is* the
coverage.

This is the direct lesson of section 2.2. Four revisions of a comparable split
each severed a provisioning edge, and the record concludes that reconstruction
by inspection kept missing them. `make` already holds those edges; a caller that
invokes `make ci` whole inherits every one.

Two properties follow without further machinery:

- `make ci` invoked with neither `SKIP_SAST` nor `SAST_DELEGATED` runs the SAST
  leg inline (§2.3), so one invocation covers `gate-main` and `gate-sast`.
- `test-after-build-check` omits only the checks `build-check` already ran
  (ADR-0096), so the union across `make ci` is the complete test macro.

Three further jobs cover what `make ci` does not reach at all, per §4.2: native
Windows, native macOS, and the site and browser gate.

The selective lanes are **accelerators**. They carry partial evidence, make no
completeness claim, and may be added, split or removed without changing what a
complete run means.

### 7.3 Job roster

**Composition membership and dispatchability are independent properties.** A
job can be in the composition, individually dispatchable, both, or neither, and
conflating them is how a roster starts contradicting itself.

Composition — two scaffolding jobs and four evidence jobs. Runner labels follow
the fleet's `ubuntu-latest` idiom — no job in it pins a versioned Ubuntu; timeout
origins are stated per §7.7.

| Job | Kind | Command | Runner |
| --- | --- | --- | --- |
| `resolve` | scaffolding | resolve the head SHA and refuse a foreign head, a non-default dispatch ref, an unreadable pull request, a non-SHA response, or an expected-SHA mismatch. Does not check out the revision under test | `ubuntu-latest` |
| `verify-make-ci` | evidence | the provisioning probe, then `make ci` | `ubuntu-latest` |
| `windows-native` | evidence | `build-check-windows.yml` via a `./`-relative `workflow_call` — its three `windows-latest` jobs plus its `ubuntu-latest` aggregate, four jobs in total | `windows-latest` x3 + `ubuntu-latest` |
| `macos-native` | evidence | the checks the census classifies `darwin-native` for which a live-platform test exists, under a scratch keychain and a `RUNNER_TEMP`-confined `HOME` | `macos-15` |
| `site-browser` | evidence | the site build, rendered-link audit, `web` unit suite and `web` browser gate. The docs-site plugin suite is **not** repeated — `make ci` already runs it | `ubuntu-latest` |
| `receipt` | scaffolding | re-resolve the head and emit the receipt. Does not check out the revision under test | `ubuntu-latest` |

Individually dispatchable — the six surfaces the accepted intent requires, each
carrying partial evidence only: `build-policy`
(`make build-check … SAST_DELEGATED=1`, `make lint-ruff`, `make lint-mypy`),
`sast-sca` (`make sast`), `pytest-corpus` (`make test`), `site-browser`,
`windows-native`, `macos-native`.

Three of those — `site-browser`, `windows-native`, `macos-native` — are both
dispatchable and composition members. The other three are dispatchable only:
their semantic content is inside `make ci`, so the composition reaches it
without running them, and removing one weakens no completeness claim.

`macos-latest` is deliberately unused: it currently resolves to arm64 macOS 26
and GitHub documents that `-latest` labels move between stable images.

### 7.4 Verdict vocabulary

The receipt is one fenced `json remote-verify-receipt.v1` block in the run's
job summary, following the closed-object shape `review-verdict.v1` establishes.

```json remote-verify-receipt.v1
{
  "schema_version": "remote-verify-receipt.v1",
  "state": "complete",
  "lane": "composition",
  "pull_request": 0,
  "head_sha": "<40 hex>",
  "base_revision": "<40 hex>",
  "draft": true,
  "dispatch_ref": "refs/heads/main",
  "dispatched_by": "<actor>",
  "job_results": {}
}
```

A closed object with exactly those ten keys. `state` is one of exactly four
values, and the set is total over the outcome space — a composition run in which
a job failed has a state, which a three-token vocabulary did not provide.

| State | Meaning |
| --- | --- |
| `partial` | One named lane ran. Evidence about that lane only, never completion, whatever its result. |
| `complete` | Every composition job ran and succeeded, and the head is unchanged since it was pinned. |
| `incomplete` | Every composition job ran, at least one did not succeed, and the head is unchanged. `job_results` names each one. |
| `superseded` | The head moved during the run, or the re-resolution could not be performed. The evidence does not describe the current head. |

`base_revision` is load-bearing, not decoration: `make ci` is **not** a function
of the head alone. `lint-catalogue-curation-guard.py` defaults its diff base to
`origin/main` and `tools/repo/branch_added_paths.py` resolves
`origin/main`/`origin/HEAD`, both at run time — so the same pinned head can
verify against different bases on two dispatches. Recording the base is what
makes a `complete` reproducible.

A dispatch run's check runs attach to the dispatch ref's head, not to the pull
request's, so the receipt is read from the run's own page. It is not visible in
the pull request's checks list, and posting it back would need
`pull-requests: write`, which the posture forbids.

### 7.5 Revision identity and staleness

- The head SHA is resolved once, in `resolve`, and passed to every job.
- Every job checks out that SHA and refuses to run a check if the checked-out
  commit differs from it.
- `receipt` re-resolves the head. A changed value, or a re-resolution that
  cannot be performed, yields `superseded` and fails the run — so a push during
  the run cannot leave a stale receipt reading as current proof.
- An optional expected-SHA input fails the run closed on mismatch.
- The receipt records the pull request number, the pinned SHA, the draft state,
  and the dispatch ref.

### 7.6 Trust boundary and security posture

**A job executes repository code from the selected pull request.** `make ci`
runs the checked-out revision's Makefile, its test suites, its `npm ci` lifecycle
scripts and its build. Dispatching is therefore a trust decision, and the
maintainer procedure records it as one.

Two residuals follow from that and are accepted rather than mitigated. Every job
carries the Actions cache service endpoint and runtime token in its environment
whether or not a step declares a cache, so forbidding declared cache writes
bounds the declared surface and not the capability. And a dispatched run is free
compute on standard runners with nothing bounding concurrent dispatches across
pull requests. The control for both is the same: dispatch requires a maintainer
with write access, and the receipt records which one.

Two constraints bound that decision:

- **Same-repository heads only.** The run fails when the resolved pull request's
  head repository is not this repository, so every executed revision comes from
  someone who already holds write access. Fork pull requests are out of scope.
- **Default-branch dispatch only — WITHDRAWN 2026-09-04.** This constraint said
  the run fails when the dispatch ref is not the default branch, which made the
  posture below a property of the ref that actually ran rather than an
  assumption about it. It is incompatible with the accepted purpose of
  dispatch — reaching verification from a worktree branch — so it is withdrawn
  deliberately rather than quietly.

  **What the withdrawal costs.** `workflow_dispatch` resolves the workflow from
  the selected ref, so a dispatched run executes that ref's copy of the workflow
  file, including its `permissions:` block. Every control asserted by
  `tools/test-build-check-workflow.py` is evaluated only as a step of the
  aggregator job — on a pull request to the default branch, and on a push to it.
  It never evaluates the copy a dispatch of a feature branch runs. So a branch
  whose workflow declares broader `permissions:` can be dispatched, and no
  required check will have reviewed it.

  **The measured basis for accepting it.** Read from the API on 2026-09-04, all
  four values:

  | Setting | Value |
  | --- | --- |
  | `default_workflow_permissions` | `read` |
  | `can_approve_pull_request_reviews` | `false` |
  | `allowed_actions` | `all` |
  | `sha_pinning_required` | `false` |

  An unmodified workflow therefore receives a read-only token. **A read default
  is not a ceiling** — an explicit `permissions:` block can still request write —
  but requesting it takes a push, which takes write access. And `pull_request`
  also resolves the workflow from the head ref, so an actor with write access can
  already run a modified workflow by opening a pull request. **The withdrawal
  therefore removes reviewability, not capability**: what dispatch adds is that
  the modified file runs without a pull request to show it.

  `allowed_actions: all` and `sha_pinning_required: false` mean the dispatched
  ref may also introduce an unpinned third-party action. `ci-security.yml`'s
  scanner reports unpinned actions, but on the reviewed pull-request copy — not
  on a later unreviewed rewrite of the selected ref.

  No in-workflow control closes this. A step that verifies the workflow's own
  permissions is deleted by the same edit that would widen them, so it cannot
  observe its own absence.

  **Residual, accepted by the repository owner on 2026-09-04:** a dispatch runs
  a workflow file that no required check has reviewed.

  **The effective bound is the dispatcher's write authority**, plus any enforced
  enterprise, organization, or repository maximum. It is *not* the token
  default: that default governs only a workflow which declines to declare its
  own permissions, so it bounds the honest case and not the case this residual
  is about. Whether an enforced maximum exists above this repository is
  **unestablished** — it needs the effective enterprise and organization Actions
  policy payloads, which are not readable from this working environment.

  Re-price this on any of: a change to any of the four values above; an
  organization or enterprise Actions-policy change; a ruleset or bypass-actor
  change affecting who may push to a dispatchable ref; or dispatch being granted
  to a role weaker than write.

  One control was identified as possibly helping without defeating branch
  dispatch, and is **not** yet evaluated: a ruleset that externally restricts
  unreviewed changes to workflow files on every dispatchable ref. An environment
  with required reviewers does *not* suffice on its own, because the selected
  ref's workflow can delete its own `environment:` declaration.

The remaining controls:

- **No Actions cache in any job with a foreign revision checked out**, and none
  in a workflow the composition calls. A dispatch run's `GITHUB_REF` is the
  default branch, so a cache save would write the default-branch scope that the
  required Windows gate and the Pages build later restore from. This is why
  `build-check-windows.yml`'s two `cache: 'pip'` steps need explicit handling on
  the `workflow_call` path.
- `permissions: contents: read` at the top level, `pull-requests: read` added
  only on `resolve`, and no write on any scope under any spelling.
- Every checkout the composition causes — including inside the called workflow —
  sets `persist-credentials: false`. The pinned `actions/checkout` (v4.4.0)
  defaults it to `true`.
- No `secrets.` context and no `pull_request_target` trigger.
- Dispatch inputs reach shell bodies only through `env:` bindings.
- Every `uses:` is a 40-character SHA already present in the fleet, so the change
  adds no supply-chain edge.
- Standard hosted runner labels only, as literals. Larger runners are "always
  charged for, even when used by public repositories."
- Artifacts are diagnostic only, bounded by `retention-days`, and no verdict
  reads one.

The accepted residual: a dispatched run is free compute on standard runners, and
nothing bounds concurrent dispatches across pull requests. The control is that
dispatch requires a maintainer with write access.

### 7.7 Concurrency and bounds

The concurrency group keys on the pull request and the selected lane, with
`cancel-in-progress: true`, so an obsolete run neither consumes capacity nor
masquerades as current proof. Job and workflow concurrency share one namespace,
so the group prefix must differ from every prefix already in the fleet.

Every job declares `timeout-minutes`, and every value records an origin: an
existing repository job budget the job reproduces; that budget scaled for a
named runner-class difference; or a recorded workflow-duration median and tail
scaled by a stated factor. Per-job timeouts are what keep the composition inside
GitHub's 6-hour job ceiling. Standard macOS concurrency is capped at 5
concurrent jobs on Free and Pro plans.

### 7.8 Activation boundary

GitHub requires a `workflow_dispatch` definition to exist on the default branch
before it will accept a manual dispatch. Rollout therefore has two stages:

1. **Pre-merge** proves *construction* — the construction tests plus the
   existing automatic pull-request checks. Manual dispatch is unavailable.
2. **Post-merge** proves *operation* — one selective run and one complete run
   against the same immutable head SHA, plus one run that receives a push while
   in flight and returns `superseded`.

That activation proof is rollout evidence for this surface, not a dependency on
another queued item.

### 7.9 Out of scope

Release, publication, deployment, code signing, simulators, Xcode builds, nested
virtualization, live model evaluation, larger or self-hosted runners, custom
runner images, fork pull requests, changes to organization billing or runner
policy, and any weakening of a local gate, test, security control, or existing
required check.

## 8. Provenance

The shaping intents behind this document, most recent first. All six were
recorded on 2026-09-03; within that date the accepted intent leads and the
drafts follow alphabetically.

| Intent | Status | What it shapes here |
| --- | --- | --- |
| [`remote-ci-verification-parity`](../product/intents/remote-ci-verification-parity.md) | Accepted | Section 7 in full: the dispatch surface, the partial-versus-complete contract, the platform coverage contract, and the activation boundary |
| [`ci-parity-linter-scope`](../product/intents/ci-parity-linter-scope.md) | Draft | Informational only. Concerns local-correspondence checks for newly admitted workflows — §4.1's disposition roster. Not a dependency of section 7 |
| [`pack-javascript-ci-workflow`](../product/intents/pack-javascript-ci-workflow.md) | Draft | The JavaScript coverage gap named in §4.2 |
| [`scanner-suppression-and-pin-hygiene`](../product/intents/scanner-suppression-and-pin-hygiene.md) | Draft | Suppression and pin integrity for the SAST leg in §2.3 |
| [`test-runner-boundary-completion`](../product/intents/test-runner-boundary-completion.md) | Draft | The no-runner contracts behind §4.2 |
| [`workflow-posture-harness-consolidation`](../product/intents/workflow-posture-harness-consolidation.md) | Draft | The shared harness described in §3.1, which section 7's construction tests extend |
