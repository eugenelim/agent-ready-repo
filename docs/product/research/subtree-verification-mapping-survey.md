# Subtree-to-verification mapping conventions

> Discipline: applied (practitioner-pattern survey)

Commissioned 2026-09-04 while shaping the `remote-gate-dispatch` slice of `docs/product/intents/remote-ci-verification-parity.md`, to test whether a root-level verification map has prior art or merely adds to a crowded namespace. Independent desk research; findings are cited to their sources and labelled by evidence class. Retained so later work can cite it rather than restate it.

**Status: acted on.** This survey decided three things, against the position it was commissioned to check. The proposed name `GATES.md` was rejected — it conflates "runs", "reports" and "blocks", and this repository's own measurement shows most surfaces report without blocking. A hand-maintained hash of each workflow's `on:` block was rejected as the staleness control, because it stays green when a job-level `if:`, a `dorny/paths-filter` decision, a called workflow, or the test command itself changes. Marker-delimited generation with a diff check was adopted instead, which is the mechanism this repository already runs as `make build-self` plus `make build-check`. The surviving conclusion is that the gap is real but narrow: `on: paths:` is a trigger map, not a verification map, so only the judgement half — purpose, local equivalent, blocking status, what a pass does and does not establish — is worth writing by hand.

Related: [`derived-repository-facts-survey.md`](derived-repository-facts-survey.md) covers the general question of deriving repository facts rather than typing them.

---

## Recommendation

### (a) Does a genuine gap exist?

**Yes, but it is narrower than the proposed `GATES.md`.** No established open-source convention combines:

1. changed subtree;
2. verification surface;
3. exact local reproduction command;
4. remote dispatch mechanism;
5. what the surface proves and does not prove.

Large projects usually make the routing mechanically queryable and document the verification semantics elsewhere. Apache Airflow is the closest integrated example, but even it splits the implementation, local query command, explanatory documentation, and agent instructions across several files rather than publishing a root matrix. [moderate]  
Downgrade: `indirectness`—a bounded public-source survey cannot prove universal absence. Evidence: [Airflow selective-check implementation guide](https://github.com/apache/airflow/blob/main/dev/breeze/doc/ci/04_selective_checks.md), [Rust CI guide](https://rustc-dev-guide.rust-lang.org/tests/ci.html), [Chromium buildbot configuration](https://chromium.googlesource.com/chromium/src/testing/+/HEAD/buildbot/README.md), [Prow job routing](https://docs.prow.k8s.io/docs/jobs/), [Nx affected execution](https://nx.dev/docs/features/ci-features/affected).

The strongest objection is correct in part: GitHub Actions `on.<event>.paths` is already a machine-readable **workflow-trigger map**. But it is not a verification map. It says when an entire workflow is considered for execution; it does not describe job-level `if:` routing, `dorny/paths-filter` decisions, reusable-workflow composition, local equivalents, branch-protection status, or the meaning and limitations of a passing job. GitHub defines triggers and jobs as separate workflow components, while `dorny/paths-filter` exists specifically because built-in path filters do not operate at job or step level. [high] Sources: [GitHub workflow concepts](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows), [GitHub path-filter syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax), [`dorny/paths-filter`](https://github.com/dorny/paths-filter), [Airflow’s composite workflow architecture](https://github.com/apache/airflow/blob/main/dev/breeze/doc/ci/05_workflows.md).

### (b) What minimum artifact fills the gap?

Create a short, human-facing verification contract only if it records information that is not safely inferable:

- the verification surface’s purpose;
- the canonical local command and prerequisites;
- the remote workflow/job or dispatch command;
- whether it blocks merging, merely reports, is scheduled, or is manual;
- what a pass establishes;
- explicit non-claims and unavailable-local cases;
- widening rules such as “shared infrastructure change runs every surface.”

Generate or validate everything mechanical:

- workflow names and paths;
- normalized `on:` triggers and path filters;
- job IDs;
- job-level path-filter definitions;
- reusable-workflow call targets;
- task-graph/project membership where the build system exposes it;
- the routing projection or its digest.

A document that hand-copies only `on.paths` adds no durable value. A document that explains why a route exists, how to reproduce it, and what its result means fills a real gap. Airflow demonstrates this split: code decides affected test groups; `breeze ci selective-check` exposes the decision locally; prose explains escalation rules and why groups exist; `AGENTS.md` tells maintainers to update the explanation when the implementation changes. [moderate] Sources: [Airflow selective checks](https://github.com/apache/airflow/blob/main/dev/breeze/doc/ci/04_selective_checks.md), [Airflow agent guidance](https://github.com/apache/airflow/blob/main/AGENTS.md), [Rust local CI reproduction](https://rustc-dev-guide.rust-lang.org/tests/docker.html).

### (c) Name

Use **`VERIFICATION.md`**, linked prominently from `CONTRIBUTING.md` and summarized—not duplicated—in `AGENTS.md`.

This is a recommendation, not an existing convention. `VERIFICATION.md` describes local checks, hosted CI, manual checks, and non-claims without implying that every listed surface is a merge gate. `GATES.md` risks conflating “runs,” “reports,” and “blocks”; `CI.md` excludes local and manual verification; `TESTING.md` is too narrow for formatting, generation, packaging, and policy checks. [low]  
Downgrade: `indirectness`; no surveyed name has established semantics for this artifact. Existing `VERIFICATION.md` files demonstrate the term’s suitability for scoped proof and explicit non-claims, not an ecosystem standard: [agent-memory-system verification guide](https://github.com/rrrrrredy/agent-memory-system/blob/main/docs/verification.md), [Vela verification semantics](https://github.com/vela-science/vela/blob/main/docs/VERIFICATION.md).

### (d) Staleness mechanism

Do **not** make a hand-maintained hash of `on:` the primary control. Instead:

1. Put mechanically derived routing facts in a marker-delimited generated region.
2. Regenerate that region in CI and fail on any diff.
3. Keep purpose, proof, non-proof, prerequisites, and exceptions outside the generated region.
4. Add a structural check requiring every relevant workflow and every declared subtree to be classified, including explicit `global`, `manual`, or `no dedicated surface` cases.

If compact fingerprints are still useful, compute them automatically over the full normalized routing projection—not merely `on:`. At minimum that projection should include triggers, workflow-level paths, in-workflow path filters, job conditions, and reusable-workflow targets. Hashing only `on:` will remain green when the actual test command, `if:` condition, `dorny` filters, or called workflow changes. [moderate] Sources: [GitHub’s separation of triggers, jobs, and steps](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows), [`dorny/paths-filter` job-level routing](https://github.com/dorny/paths-filter), [GitHub Agentic Workflows’ compiled frontmatter hashes](https://github.github.com/gh-aw/reference/glossary/), [Chromium’s generated-output presubmit check](https://chromium.googlesource.com/chromium/src/+/HEAD/infra/config/PRESUBMIT.py).

## Adoption reality of candidate names

| Name | Adoption finding | Assessment |
|---|---|---|
| `CONTRIBUTING.md` | GitHub explicitly recognizes it as a community-health file, surfaces it to issue/PR authors, and searches `.github/`, root, then `docs/`. [high] [GitHub documentation](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file) | The only genuinely conventional candidate—but its scope is the whole contribution process, so a large matrix should be linked from it rather than buried in it. |
| `BUILDING.md` | Used by substantial projects including [Node.js](https://github.com/nodejs/node/blob/main/BUILDING.md), [Eclipse CDT](https://github.com/eclipse-cdt/cdt/blob/main/BUILDING.md), and [GNOME Dia](https://github.com/gnome/dia). [moderate] | A recurring genre name, not a tool-recognized standard. It conventionally means compilation, platforms, and prerequisites—not CI routing. |
| `TESTING.md` | Root examples include [Eclipse CDT](https://github.com/eclipse-cdt/cdt) and [OpenShift HyperShift](https://github.com/openshift/hypershift/blob/main/TESTING.md); LLVM instead publishes a named [Testing Infrastructure Guide](https://www.llvm.org/docs/TestingGuide.html). [moderate] | Familiar, but normally describes test structure, conventions, and execution. Too narrow for non-test gates. |
| `DEVELOPMENT.md` | HyperShift uses it for make targets, multi-module rules, and pre-PR verification, while also retaining separate `TESTING.md` and `HACKING.md`. [low] [HyperShift development guide](https://github.com/openshift/hypershift/blob/main/DEVELOPMENT.md) | Recurring but semantically broad. Its coexistence with the other files shows local taxonomy, not a convention. Downgrade: `single source`. |
| `HACKING.md` | Used in projects such as [GNOME Dia](https://github.com/gnome/dia) and [HyperShift](https://github.com/openshift/hypershift/blob/main/HACKING.md). [low] | A recognizable legacy maintainer-guide label, but informal and project-specific. It gives no CI-map expectation. Downgrade: `indirectness`. |
| `CI.md` | GitHub does not recognize it as a community-health file, and the surveyed large projects put CI documentation in contributor guides, subsystem docs, or executable configuration instead. [low] [GitHub recognized-file list](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file), [Airflow CI docs](https://github.com/apache/airflow/blob/main/dev/breeze/doc/ci/05_workflows.md), [Rust CI guide](https://rustc-dev-guide.rust-lang.org/tests/ci.html) | Functionally dead as a cross-project discovery convention. This does not mean no repository uses the filename; it means a reader cannot reasonably infer that it exists or what it contains. Downgrade: `indirectness`. |

## Prior art for the map

| Repository/ecosystem | Where the mapping lives | Classification |
|---|---|---|
| Kubernetes/Prow | Prow job configuration carries `run_if_changed`, `skip_if_only_changed`, `always_run`, branch rules, and manual rerun commands. Kubernetes test-infra documents where job configs live. [high] [Prow jobs](https://docs.prow.k8s.io/docs/jobs/), [kubernetes/test-infra](https://github.com/kubernetes/test-infra) | Executable config doubles as the map; no single subtree/local/remote/proof document. |
| `rust-lang/rust` | `jobs.yml` defines job parameters; `ci.yml` dynamically obtains the executed matrix; the rustc-dev-guide describes PR, auto, and try jobs and provides `citool run-local`. [high] [`jobs.yml`](https://github.com/rust-lang/rust/blob/main/src/ci/github-actions/jobs.yml), [`ci.yml`](https://github.com/rust-lang/rust/blob/main/.github/workflows/ci.yml), [CI guide](https://rustc-dev-guide.rust-lang.org/tests/ci.html) | Config plus explanatory prose and a local adapter; not organized as subtree rows. |
| Chromium | Starlark/`.pyl` sources define builders and suites; JSON mappings are generated. Presubmit runs the generator in `--check` mode, and hand-editing generated JSON is forbidden. [high] [buildbot README](https://chromium.googlesource.com/chromium/src/testing/+/HEAD/buildbot/README.md), [targets documentation](https://chromium.googlesource.com/chromium/src/+/HEAD/infra/config/targets/README.md), [presubmit check](https://chromium.googlesource.com/chromium/src/+/HEAD/infra/config/PRESUBMIT.py) | Checked generated artifact from canonical config. This is the strongest anti-duplication precedent. |
| LLVM | The testing guide explains `check-all`, `check-llvm`, direct `llvm-lit` execution, directory structure, and platform-specific exclusions. [moderate] [LLVM Testing Guide](https://www.llvm.org/docs/TestingGuide.html) | Hand documentation for test topology and local execution; no unified subtree-to-hosted-workflow map found. Downgrade: `single source`. |
| Bazel-based projects | Bazel CI uses `.bazelci/presubmit.yml`, whose task entries name platforms and build/test targets. Bazel itself exposes reverse dependency queries. [high] [Bazel CI configuration](https://github.com/bazelbuild/continuous-integration), [Bazel query guide](https://bazel.build/query/guide), [Bazel Central Registry policy](https://github.com/bazelbuild/bazel-central-registry/blob/main/docs/bcr-policies.md) | Executable config plus queryable graph. |
| Nx/Turborepo | Nx derives project/task graphs from workspace configuration and source dependencies, then runs affected targets. Turborepo exposes `--affected`, `--dry=json`, and GraphQL queries describing affected packages and reasons. [high] [Nx affected](https://nx.dev/docs/features/ci-features/affected), [Nx graph](https://nx.dev/docs/features/explore-graph), [Turborepo run reference](https://turborepo.dev/docs/reference/run), [Turborepo repository queries](https://turborepo.dev/docs/crafting-your-repository/understanding-your-repository) | Derived, queryable map; static prose maps are unnecessary for mechanical dependency reachability. |
| Apache Airflow | Selective-check code classifies files and chooses test groups; documentation lists groups, escalation rules, workflow purposes, and local reproduction; `AGENTS.md` points agents at the command and requires doc updates with rule changes. [high] [Selective checks](https://github.com/apache/airflow/blob/main/dev/breeze/doc/ci/04_selective_checks.md), [Workflow architecture](https://github.com/apache/airflow/blob/main/dev/breeze/doc/ci/05_workflows.md), [Agent instructions](https://github.com/apache/airflow/blob/main/AGENTS.md) | Closest prior art: hand explanation alongside derivable routing, but deliberately not one root matrix. |
| Eclipse CDT | Root `BUILDING.md` and `TESTING.md` coexist with a workflow whose `dorny/paths-filter` rules control DSF tests and docs artifacts. [moderate] [Repository](https://github.com/eclipse-cdt/cdt), [workflow](https://github.com/eclipse-cdt/cdt/blob/main/.github/workflows/build-test.yml) | Human guides plus config-level partial routing; no complete hand map. Downgrade: `single source`. |

## What can be derived, and what cannot?

Bazel, Nx, and Turborepo can answer graph questions more accurately than a hand-maintained table because their results include dependency propagation rather than simple directory membership. Nx explicitly says its graph stays current by analyzing the workspace; Turborepo’s dry-run JSON includes commands, inputs, dependencies, and dependents. [high] Sources: [Bazel reverse dependencies](https://bazel.build/query/guide), [Nx graph](https://nx.dev/docs/features/explore-graph), [Turborepo dry run](https://turborepo.dev/docs/reference/run).

GitHub path filters and CODEOWNERS provide useful precedents for path-pattern mappings, but both have deliberately narrow meanings: one selects workflow runs, the other assigns reviewers. Neither represents behavioral dependency reachability or verification sufficiency. [high] Sources: [GitHub path filters](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax), [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners), [Nx affected dependency propagation](https://nx.dev/docs/features/ci-features/affected).

The content a generator cannot responsibly invent is judgment:

- why the surface exists;
- what failure class it is intended to catch;
- what a green result excludes;
- environmental or credential prerequisites;
- whether the check gates merging;
- whether CI provides stronger coverage than the local command;
- when a focused result must be widened;
- manual or hardware-dependent acceptance.

Airflow’s explanations of why environment changes force the full matrix and Rust’s warning that local CI reproduction is not trivial are concrete examples of this non-derivable content. [moderate] Sources: [Airflow decision rules](https://github.com/apache/airflow/blob/main/dev/breeze/doc/ci/04_selective_checks.md), [Rust local CI guide](https://rustc-dev-guide.rust-lang.org/tests/docker.html), [LLVM platform-dependent testing](https://www.llvm.org/docs/TestingGuide.html).

## Duplication and failure evidence

Airflow intentionally keeps prose beside derivable selection code because the prose explains audience-facing reasons, examples, escalation behavior, and troubleshooting. Its `AGENTS.md` explicitly says that drift would make CI behavior impossible to reason about. This justifies semantic duplication, but its visible control is an update rule plus implementation tests—not proof that the prose itself is automatically checked. [moderate]  
Downgrade: `single source`. [Airflow agent guidance](https://github.com/apache/airflow/blob/main/AGENTS.md).

A documented stale-copy failure exists in `civitai/cli`: `AGENTS.md` says `make ci` used to be described as mirroring hosted CI even though it omitted the separately pinned lint job; a defect escaped because contributors trusted that equivalence. This is directly analogous to the risk of copying remote surfaces into a hand map. [low]  
Downgrade: `single source`; `survivorship bias`. [Civitai CLI agent guide](https://github.com/civitai/cli/blob/main/AGENTS.md).

Chromium chose the opposite approach for mechanical mappings: generate the builder/test JSON and make presubmit reject edits or drift. That is stronger evidence for generation than for storing fingerprints beside hand-copied facts. [moderate] Sources: [Chromium buildbot README](https://chromium.googlesource.com/chromium/src/testing/+/HEAD/buildbot/README.md), [Chromium presubmit](https://chromium.googlesource.com/chromium/src/+/HEAD/infra/config/PRESUBMIT.py), [Chromium target-source migration](https://chromium.googlesource.com/chromium/src/+/HEAD/infra/config/targets/README.md).

Marker-delimited generation is established practice. `terraform-docs` injects content between `<!-- BEGIN_TF_DOCS -->` and `<!-- END_TF_DOCS -->`; its GitHub Action can fail when regenerated output differs. The mechanism works because generated facts and hand prose have explicit ownership boundaries. [moderate] Sources: [`terraform-docs`](https://github.com/terraform-docs/terraform-docs), [`terraform-docs` GitHub Action and `fail-on-diff`](https://github.com/terraform-docs/gh-actions), [`pre-commit-terraform` marker support](https://github.com/antonbabenko/pre-commit-terraform).

## Agent-facing angle

The emerging `AGENTS.md` convention favors exact build/test commands and nested subtree-specific instructions. Its published example tells agents to inspect `.github/workflows` and run package-filtered commands; it defines no schema or separate verification-map filename. [high] Sources: [AGENTS.md ecosystem site](https://agents.md/), [OpenAI Agents JS instructions](https://github.com/openai/openai-agents-js/blob/main/AGENTS.md), [Apache Airflow instructions](https://github.com/apache/airflow/blob/main/AGENTS.md).

I found no established precedent for a dedicated **agent-only** verification map. Projects inline commands in `AGENTS.md`, use nested `AGENTS.md` files, or point from agent guidance to human CI documentation. Therefore `VERIFICATION.md` should be a shared human-and-agent reference, with `AGENTS.md` containing only the pointer, invocation rule, and any agent-specific safety constraint. [moderate]  
Downgrade: `indirectness`—this is an ecosystem inference rather than an exhaustive census. Evidence: [AGENTS.md recommended contents and nesting](https://agents.md/), [Airflow’s linked CI documentation](https://github.com/apache/airflow/blob/main/AGENTS.md), [OpenAI Agents JS test instructions](https://github.com/openai/openai-agents-js/blob/main/AGENTS.md).

## Minimum proposed shape

A viable `VERIFICATION.md` should have one row per meaningful verification surface, not necessarily one row per physical directory:

| Field | Ownership |
|---|---|
| Paths / affected selector | Generated from workflow, filter, or task-graph configuration |
| Surface and remote workflow/job | Generated |
| Trigger/run modes | Generated |
| Local command and prerequisites | Hand-maintained unless sourced from a canonical task manifest |
| Purpose | Hand-maintained |
| Establishes | Hand-maintained |
| Does not establish | Hand-maintained |
| Merge status: blocking/reporting/manual/scheduled | Validated against an explicit repository declaration; do not infer from workflow YAML alone |

This is a `[synthesis]` from the division used by Airflow, Rust, Chromium, Nx, and Turborepo: machines own routing facts; prose owns operational meaning.

## Known unknowns

- **Known-unknown:** Exact filename prevalence across all public repositories. A GitHub-wide code-search dataset or API census would close this; public search results are sufficient to identify conventions and counterexamples, not calculate adoption rates.
- **Known-unknown:** Whether this repository’s branch protection makes each named workflow a real merge gate. Workflow files do not encode the complete current ruleset; authenticated repository-ruleset data would close it.
- **Known-unknown:** Whether every local command can be derived from an existing canonical task registry in this repository. A later repository-specific design pass could establish that without duplicating commands.
- **Unknowable from public evidence:** Practices inside private enterprise monorepos, which may contain stronger internal CI catalogues.
- **Unknowable as posed:** A universally correct subtree boundary. Build graphs, generated code, shared configuration, and policy files can legitimately make a path affect surfaces outside its lexical subtree.

No repository files were created, edited, or deleted. The mandated safe read of `AGENT_RULES.md` was refused by session policy; the requested desk-research skill and its confidence overlay were read successfully.
