# Derived repository facts for agent loops

> Discipline: applied (practitioner-pattern survey)

Commissioned 2026-09-04 while shaping the `remote-gate-dispatch` slice of `docs/product/intents/remote-ci-verification-parity.md`. Independent desk research; findings are cited to their sources and labelled by evidence class. Retained so later work can cite it rather than restate it.

**Status: starting point, not a decision.** No pattern here is adopted. The repository has no derived-fact machinery today, and the survey records that effectiveness across these patterns is largely asserted rather than measured — so this is the input to a later decision about whether to build our own derivation or adopt a tool, not that decision.

---

The field’s vocabulary is fragmented: **code intelligence**, **semantic indexing**, **repository maps**, **dependency/build graphs**, **change-impact analysis**, **generated metadata**, and **software knowledge graphs** all cover parts of the idea.

The central finding is:

> A derived artifact replaces silent transcription drift with a reproducible computation, but it is durable only when the derivation is bound to a repository revision, tool/configuration version, and enforced refresh mechanism.

Derivation does not guarantee truth. Static analysis can omit dependencies resolved only during builds; Nx allows manually declared dependencies when static inference is insufficient; and Graphify explicitly distinguishes extracted from inferred edges. Those are semantic limitations rather than transcription errors. [GitHub’s dependency-graph documentation establishes the build-time blind spot](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-graph-data); [Nx documents the need for manual dependencies where static deduction fails](https://nx.dev/docs/reference/project-configuration); [Graphify documents extracted versus inferred edges](https://github.com/Graphify-Labs/graphify). **[high; synthesis from three independent implementations]**

## 1. What “graphify” appears to mean

### Specific current tool

**[high]** The strongest exact match is [Graphify Labs’ `graphify`](https://github.com/Graphify-Labs/graphify), a repository-to-knowledge-graph CLI aimed directly at coding agents. Its documentation establishes that it:

- Parses code locally with tree-sitter.
- Builds a graph of code, documentation, configuration, and relationships.
- Emits `graphify-out/graph.json`, an HTML visualization, and `GRAPH_REPORT.md`.
- Marks relationships as `EXTRACTED` or `INFERRED`.
- Intends `graphify-out/` to be committed so collaborators and agents receive the graph with the repository.
- Exposes graph queries through MCP.
- Supports `update`, `--watch`, and optional post-commit/post-checkout hooks.

Its [product description](https://graphify.com/what-is-graphify) establishes the vendor’s intended category: a persistent repository knowledge graph for development tools and agents. Its [MCP documentation](https://graphify.com/docs/mcp-tools) establishes the agent-facing query interface.

### Ambiguity

**[moderate; naming ambiguity]** “Graphify” is also an ordinary verb for converting data into a graph, and unrelated projects have used the name. Without a repository or URL from the task owner, the identification cannot be definitive. The Graphify Labs tool is nevertheless the closest match because its documented purpose is precisely agent-oriented repository graph generation.

The nearest named concepts are:

- **Repository map** — Aider’s term for a compact, agent-prompt representation of important symbols and relationships. [Aider documents tree-sitter extraction, reference edges, graph ranking, and prompt-time inclusion](https://aider.chat/docs/repomap.html).
- **Code intelligence index** — SCIP, LSIF, Kythe, Glean, and Sourcegraph terminology for machine-produced symbol/reference facts.
- **Repository Intelligence Graph** — a recent research term for a deterministic build/test-centred repository representation. [The RIG paper defines components, runners, tests, packages, and dependency/coverage edges](https://arxiv.org/abs/2601.10112).
- **Code Property Graph** — an AST/control-flow/data-flow graph used principally for analysis and security. [The CPG specification describes its graph schema and Joern lineage](https://cpg.joern.io/).

## 2. Taxonomy of derived repository facts

| Fact kind | Representative tools | Derived artifact | Confidence |
|---|---|---|---|
| Symbols, definitions, references, calls, inheritance | SCIP indexers, LSIF indexers, Kythe, Glean, Sourcegraph, Aider | SCIP Protobuf documents; LSIF newline-delimited JSON graph; Kythe nodes/edges/facts; Glean predicate facts; Aider’s ranked prompt map | **[high]** |
| Package and dependency relationships | GitHub dependency graph, package managers, SBOM generators | Hosted dependency graph/snapshots, CLI trees or JSON, SPDX/CycloneDX documents | **[high]** |
| Ownership and review routing | CODEOWNERS, gitStream `codeExperts`, checkOwners | Authored ownership rules; dynamically ranked reviewers; generated CODEOWNERS/JSON/DOT | **[moderate]** |
| Tests related to changed code | Launchable, Nx affected, Bazel queries, Meta predictive test selection, RIG | Ranked test list, affected project/task graph, target graph, component-to-test coverage edges | **[high]** |
| Build targets and actions | Bazel, Gazelle, Buck2, Nx, CMake File API | BUILD files, target/action DAGs, DOT/XML/JSON, CMake codemodel JSON | **[high]** |
| CI/workflow topology | ravelact, GitHub/GitLab visualizers, Nx Cloud affected graph | GitHub Actions IR, Mermaid/JSON/workflow traces; per-run job DAGs; affected project graph | **[moderate]** |
| Security-analysis facts | CodeQL, Joern/CPG, SARIF-producing analyzers | CodeQL database, code-property graph, SARIF result log | **[high]** |
| Provenance and software inventory | SPDX, CycloneDX, SLSA provenance | Versioned JSON/XML/RDF/Protobuf documents containing components, relationships, digests, and build claims | **[high]** |

### Symbol and reference graphs

**[high]** [SCIP defines a language-agnostic Protobuf index format](https://scip-code.org/) containing per-document occurrences, symbols, definitions, references, and relationships. The project lists independently maintained indexers for Java, TypeScript, Rust, Clang-based languages, Python, .NET, Dart, PHP, and others, and consumers including Sourcegraph, Searchfox, rust-analyzer, and Glean. This establishes both the artifact shape and multi-implementation adoption.

**[high]** [LSIF defines a graph representation for precomputed code navigation](https://microsoft.github.io/language-server-protocol/) and [Microsoft’s `lsif-node` documentation establishes newline-separated JSON output](https://github.com/microsoft/lsif-node/blob/main/README.md). LSIF chiefly precomputes definition/reference-style operations that remain meaningful without an active language server.

**[high]** [Kythe defines language-independent nodes, edges, and fact entries](https://kythe.io/docs/kythe-storage.html); its [schema includes references, calls, inheritance, dependencies, and documentation relationships](https://kythe.io/docs/schema/). Kythe explicitly prefers incomplete facts over incorrect ones, demonstrating that deterministic extraction still has a completeness boundary. [Kythe’s overview establishes that design principle](https://kythe.io/docs/kythe-overview.html).

**[high]** [Glean stores typed, uniquely keyed predicate facts in databases](https://glean.software/docs/schema/basic/). Its [introduction establishes definitions, callers, inheritance, and arbitrary schema queries](https://glean.software/docs/introduction/).

**[high]** [Aider’s repository map](https://aider.chat/docs/repomap.html) is a compact on-demand artifact: tree-sitter extracts definitions and references; files and identifiers become a graph; a ranking algorithm selects important signatures and source lines for the model’s token budget.

### Dependency graphs

**[high]** [GitHub’s dependency graph](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-graph) derives dependencies from manifests and lockfiles and stores them in an external repository service. [Dependency-submission documentation](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-graph-data) establishes that build-resolved dependencies can instead be submitted as snapshots associated with a commit SHA.

**[high]** Package-manager reports are ephemeral derivations. [`npm ls` produces a logical dependency tree and supports JSON](https://docs.npmjs.com/commands/npm-ls/); [Gradle’s dependency-insight report identifies dependency paths and selection reasons](https://docs.gradle.org/current/dsl/org.gradle.api.tasks.diagnostics.DependencyInsightReportTask.html).

### Ownership and review routing

**[high]** GitHub CODEOWNERS is not itself a derived fact: it is an authored mapping from path patterns to owners which GitHub uses for review requests and protections. [GitHub’s CODEOWNERS documentation establishes that declarative model](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners).

**[moderate; vendor-defined algorithm]** gitStream derives prospective reviewers from Git history. Its [`codeExperts` documentation establishes blame/commit history and recency-based scoring](https://docs.gitstream.cm/filter-functions/), while its [execution model establishes reevaluation on pull-request events and new commits](https://docs.gitstream.cm/execution-model/). The result is a PR assignment or comment, not a committed ownership map.

**[low; young single-project evidence]** [`checkOwners`](https://github.com/KenGraph/checkOwners) reports that it infers ownership from `git log` and blame, emits CODEOWNERS/JSON/DOT, and offers drift and synchronization commands. This is a direct example of turning historical evidence into a committed ownership artifact, but the evidence is limited to the project’s own documentation.

### Test-to-code mapping

**[high]** [Nx constructs a project graph and task graph](https://nx.dev/docs/concepts/mental-model), combines those graphs with changed files, and derives affected projects and tasks. The artifact is a graph or machine-readable affected set rather than a static handwritten test map.

**[high]** [Bazel query supports `deps`, reverse dependencies, and graph output](https://bazel.googlesource.com/bazel/%2Bshow/master/site/en/query/quickstart.md), allowing tests and their transitive code/build relationships to be derived from BUILD definitions.

**[moderate; vendor implementation with explicit model description]** [Launchable describes predictive test selection](https://help.launchableinc.com/features/predictive-test-selection/how-launchable-selects-tests/) as an external model trained from test outcomes, changed-file correlations, paths, and test/change characteristics. Its artifact is a ranked subset, not a durable one-to-one mapping.

**[moderate; recent author-run study]** [RIG derives explicit component-to-test coverage edges from build and test definitions](https://arxiv.org/abs/2601.10112), producing a JSON repository graph.

### Build and target graphs

**[high]** Bazel exposes loading, configured-target, and action graphs through `query`, `cquery`, and `aquery`; its [query-language reference establishes graph, XML, and textual outputs](https://bazel.googlesource.com/bazel/%2B/3b9ed6e9d3570a0c67e0d59e65b3785bbc1fad99/site/en/query/language.md).

**[high]** Gazelle is the clearest committed-artifact prior art. Its [architecture documents loading source, generating rules, resolving imports to labels, and writing BUILD files](https://github.com/bazel-contrib/bazel-gazelle/blob/master/how-gazelle-works.md). Its [reference establishes that it creates or updates BUILD files and can emit a unified diff without writing](https://github.com/bazel-contrib/bazel-gazelle/blob/master/gazelle-reference.md).

**[high]** [CMake’s File API emits versioned JSON codemodel objects](https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html), including targets and dependencies. [LLVM’s JSON Compilation Database specification](https://clang.llvm.org/docs/JSONCompilationDatabase.html) defines per-translation-unit compile commands and names producers including CMake, Clang fragments, Bear, and a Bazel extractor.

### CI and pipeline topology

**[moderate; young single-project tool]** [`ravelact`](https://github.com/wadackel/ravelact) directly derives a GitHub Actions estate graph from workflow and local-action YAML. It can:

- Trace event → entry workflow → reusable workflow/action calls.
- Evaluate branch, tag, and path filters for a supplied path.
- Export the IR as JSON or the call graph as Mermaid.
- Find callers, orphaned definitions, permissions propagation, and wiring defects.
- Query which entry workflows are affected when a workflow or local action changes.

Its documentation also establishes important limits: arbitrary application files are not nodes in its `impact` graph; unknown paths are skipped there, and dynamic dispatches may require annotations. Its path-query facility therefore answers “which workflow’s declared trigger matches this path,” while its impact facility answers changes inside the workflow/action estate.

## 3. Committed artifact, external service, or computed on demand

| Approach | Examples | Currency boundary | Stated or evidenced trade-off |
|---|---|---|---|
| Committed derived artifact | Graphify output, Gazelle BUILD files, generated CODEOWNERS, checked-in generated code/SBOMs | Must be regenerated and compared with the index | Visible in review and available offline, but duplicates derivable state and creates merge/churn risk |
| External indexed service | Sourcegraph precise navigation, GitHub dependency graph, Glean deployment, Launchable, CodeQL on GitHub | Service associates an index/snapshot with a commit and refreshes on push or schedule | Avoids repository bulk and enables cross-repository queries, but readers need service access and must know index freshness |
| Computed on demand | Aider repo map, Bazel/Nx queries, npm/Gradle reports, ravelact | Invocation reads current checkout; caches need valid invalidation | No committed drift, but startup cost and tool availability move to every consumer |

### Committed artifacts

**[high]** [Graphify says `graphify-out/` is intended to be committed](https://github.com/Graphify-Labs/graphify). Its JSON, report, and visualization make the derived state reviewable in a normal diff. The same documentation warns that generated graph changes inside the workspace can invalidate Claude prompt caches, establishing a concrete downside.

**[high]** Gazelle’s committed BUILD-file model is stronger prior art because the generated result also drives the build. [Gazelle documents deterministic source scanning, rule generation, dependency resolution, and file update/diff modes](https://github.com/bazel-contrib/bazel-gazelle/blob/master/gazelle-reference.md). Here the generated artifact is not merely documentation: consumers execute it.

**[moderate]** Go’s generation model makes the rationale explicit: generation is deliberately invoked by maintainers, while generated output may be checked in so downstream users do not need the generator. [The Go project’s `go generate` article establishes this producer/consumer separation](https://go.dev/blog/generate).

### Why large semantic indexes are usually external

**[high]** [Meta’s Glean account](https://engineering.fb.com/2024/12/19/developer-tools/glean-open-source-code-indexing/) says indexes are sufficiently large that centralized pre-indexing and shared querying are preferable to transferring or rebuilding them for every user. It stores immutable database layers and computes incremental updates.

**[moderate; Sourcegraph-authored comparison]** [The SCIP design discussion describes LSIF graph JSON as large, memory-hungry, slow to process, and difficult to debug](https://github.com/scip-code/scip-rfc-old/blob/main/rfc-519-lsif-typed.md). This supports the practical reason semantic indexes gravitate toward compressed artifacts and services, though the comparison was written by the team promoting SCIP.

**[high; synthesis]** Review-visible committed output is most common where the artifact is reasonably small, stable, and already part of execution—BUILD files, generated source, manifests, ownership files. Full symbol/reference indexes are more often uploaded or reconstructed because their size and revision specificity make source-control review less useful.

## 4. Currency: how derived facts stay current

| Mechanism | Tool/example | What keeps it current | Confidence |
|---|---|---|---|
| Regenerate, then fail if output differs | Kubernetes code generation | `verify-codegen.sh` runs generation and reports that generated files need updating | **[high]** |
| Guard test against fresh generation | Go compiler | Test regenerates output into a temporary location and compares it with checked-in source | **[high]** |
| Pre-commit/post-checkout hook | Graphify | Optional hooks start background graph refresh after commits and branch switches | **[moderate]** |
| Watch or explicit incremental update | Graphify | `--watch` or `graphify update` re-extracts changed files | **[high]** |
| Push-triggered snapshot | GitHub dependency graph | Dependency snapshot is associated with a commit SHA; automatic submission runs a workflow | **[high]** |
| Service re-indexing | Sourcegraph | Indexing jobs clone, analyze, and upload indexes for selected commits | **[high]** |
| Incremental immutable database layers | Glean | Re-index changed units and affected fanout into stacked immutable DBs | **[high]** |
| Content-hash/Merkle invalidation | Cursor | Client Merkle tree detects changed files; chunks and embeddings are cached by content | **[moderate; vendor description]** |
| Cached project-graph recomputation | Nx | Cached graph is partially recomputed for changed files | **[high]** |
| Recompute on each invocation/request | Aider, Bazel queries | Current checkout is parsed or queried when the consumer asks | **[high]** |
| Re-run command; no live refresh | ravelact browser | Graph is built at server start; documentation says to restart after workflow edits | **[high]** |

### The committed-output guard pattern

**[moderate; naming varies by ecosystem]** There is no single standardized name. Common names are:

- **generated-files-up-to-date check**
- **generated-code verification**
- **regenerate-and-diff**
- **generation drift check**
- **clean-tree check after generation**

Kubernetes uses a `verify-*` convention: [`hack/verify-codegen.sh`](https://github.com/kubernetes/kubernetes/blob/master/hack/verify-codegen.sh) regenerates and fails when generated files differ. The Go compiler uses a literal [`TestGeneratedFilesUpToDate`](https://go.dev/src/cmd/compile/internal/ssa/generate_test.go), regenerating and comparing output. These establish the pattern but also show that its name is conventional, not formal.

A **golden test** is adjacent terminology, but usually compares runtime output with an approved fixture. It is not necessarily the same as regenerating an entire committed projection and requiring a clean Git diff.

### Limits of each currency mechanism

**[high]** Graphify’s hooks provide eventual local refresh, not a hard repository invariant: its documentation says updates may lag for seconds, that a missing result may require `graphify update`, and that pull/merge updates require explicit handling. [The Graphify README establishes these behaviours](https://github.com/Graphify-Labs/graphify).

**[high]** External services avoid a committed-file mismatch only if every query is tied to the correct revision. [GitHub binds dependency snapshots to a commit SHA](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-graph-data). [Sourcegraph models uploads against repository commits and acknowledges asynchronous commit-graph/index state](https://sourcegraph.com/docs/code-navigation/explanations/uploads).

**[moderate; vendor description]** [Cursor describes a Merkle tree over repository files, periodic divergence checks, and embedding reuse keyed by chunk content](https://prod.cursor.com/blog/secure-codebase-indexing). This is strong evidence for its mechanism but not independent verification of its completeness or timing.

**[high; synthesis]** A derived fact avoids silent staleness only when freshness is enforceable:

1. Its inputs and tool/configuration version are identifiable.
2. Its result is tied to a commit or content digest.
3. A hook, CI guard, service event, or on-demand invocation actually reruns it.
4. Failure or lag is visible.

Without those conditions, a generated file can go stale exactly like a handwritten one; it merely has a known repair function.

## 5. Standards and formats

### Formal or open specifications with independent implementations

| Format | Status | What it standardizes | Evidence and confidence |
|---|---|---|---|
| SPDX | ISO/IEC 5962:2021; open specification | Software inventory, packages/files, licensing, relationships, checksums | [SPDX identifies the ISO standard and ecosystem](https://spdx.dev/). **[high]** |
| CycloneDX | ECMA-424; OWASP/Ecma specification | Components, services, dependencies, compositions, vulnerabilities and attestations in JSON/XML/Protobuf | [CycloneDX’s specification overview establishes the formats, model, and tool ecosystem](https://cyclonedx.org/specification/overview/). **[high]** |
| SARIF 2.1 | OASIS standard | Static-analysis result interchange: rules, findings, locations, fixes and provenance | [The OASIS SARIF 2.1 specification establishes the normative format](https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/sarif-v2.1.0-os.html). **[high]** |
| SCIP | Open protocol with multiple indexers and consumers; not a standards-body standard | Symbol occurrences, definitions, references and relationships | [SCIP publishes the schema and implementation list](https://scip-code.org/). **[high]** |
| LSIF | Microsoft-led open specification; not a standards-body standard | Graph-form precomputed language-server/navigation results | [The LSP site identifies LSIF](https://microsoft.github.io/language-server-protocol/); [`lsif-node` establishes an implementation and NDJSON representation](https://github.com/microsoft/lsif-node/blob/main/README.md). **[moderate]** |
| JSON Compilation Database | LLVM/Clang-defined de facto interchange format | Exact compiler invocation per translation unit | [LLVM documents the format and independent producers](https://clang.llvm.org/docs/JSONCompilationDatabase.html). **[high]** |

SCIP, LSIF, and the compilation database are therefore real interoperable specifications, but they do not have the same standards-body status as SPDX, CycloneDX, or SARIF.

### Open schemas or platforms, not independent standards

**[high]** Kythe supplies an open graph schema and storage model, but it is a Google-led code-indexing architecture rather than a standards-body specification. [Kythe’s storage documentation establishes its entry model](https://kythe.io/docs/kythe-storage.html).

**[high]** The Code Property Graph specification describes itself as a suggestion for an open standard and reflects Joern’s implementation. [Its specification establishes that status](https://cpg.joern.io/). It is a useful common model, but should not be represented as a ratified interoperability standard.

**[high]** Glean predicates and schemas are open and extensible within the Glean platform, not a repository-fact interchange standard. [Glean’s schema documentation establishes the platform-specific fact model](https://glean.software/docs/schema/basic/).

### Vendor- or tool-specific formats

**[high]** A [CodeQL database](https://codeql.github.com/docs/codeql-overview/about-codeql/) is a database representation of one language at a particular point in time, including syntax, control-flow, and data-flow facts. It is a GitHub/CodeQL analysis format, not a vendor-neutral repository-index standard.

**[high]** Bazel query graphs, Nx `ProjectGraph`, Graphify `graph.json`, Glean databases, and ravelact’s JSON IR are tool-owned schemas. Their being documented or open-source does not by itself make them standards.

### Adjacent CI standards do not fill the topology gap

**[high]** [CDEvents](https://github.com/cdevents/spec/blob/main/spec.md) standardizes CI/CD lifecycle events. Its [core model says pipeline and task definitions are authoring concepts without corresponding definition events](https://github.com/cdevents/spec/blob/main/core.md); it models runs, not a static repository-path-to-pipeline graph.

**[high]** [OpenTelemetry CI/CD semantic conventions](https://opentelemetry.io/docs/specs/semconv/cicd/) describe runtime spans, metrics, and logs, not repository trigger topology.

**[high]** [SLSA provenance](https://github.com/slsa-framework/slsa/blob/main/spec/build-provenance.md) records build definitions, resolved dependencies, digests, and run details for an artifact. It answers “how was this built?”, not “which workflows cover this subtree?”

## 6. Does anyone derive CI or pipeline topology?

### Direct prior art found

**[moderate; exact but young and provider-specific]** Yes: [`ravelact`](https://github.com/wadackel/ravelact) is a direct example for GitHub Actions. It parses workflow and action YAML into an intermediate representation and derives:

- Trigger event → matching entry workflows.
- Declared branch/tag/path filters.
- Reusable-workflow and local-action call edges.
- Reverse callers and transitive reachability.
- Mermaid, JSON, Markdown, and interactive graph views.
- For a queried repository path, which entry workflows’ authored path filters would match.

It is computed locally and cached outside the repository. Its browser graph must be rebuilt after edits; generated Mermaid or JSON can be exported, but committed output is not its default currency model.

### Close but materially different systems

**[high]** [GitHub’s visualization graph](https://docs.github.com/en/actions/how-tos/monitor-workflows/use-the-visualization-graph) shows jobs and `needs` dependencies for one workflow run. It does not produce a repository-tree coverage map.

**[high]** [GitHub Actions path filters](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) are handwritten trigger rules. GitHub evaluates them; it does not derive which paths ought to be covered.

**[high]** [GitLab’s pipeline editor](https://docs.gitlab.com/ci/pipeline_editor/) expands configuration and visualizes stages, jobs, and `needs` relationships, but not a derived tree-to-pipeline map.

**[high]** [CircleCI dynamic configuration](https://circleci.com/docs/guides/orchestrate/using-dynamic-configuration/) and [Buildkite’s monorepo guidance](https://buildkite.com/docs/pipelines/best-practices/working-with-monorepos) select workflows from authored path rules. Buildkite explicitly notes that its `monorepo-diff` plugin does not understand a project dependency graph.

**[high]** [Nx Cloud’s affected-project graph](https://nx.dev/blog/ci-affected-graph) derives which projects are affected during a CI execution, but its nodes are workspace projects/tasks rather than CI workflow definitions.

### Bounded absence finding

**[moderate; absence cannot be exhaustive]** I found one narrow, recent, GitHub-Actions-specific tool, ravelact, but no established cross-provider specification or mature mainstream system that emits a durable generated artifact of:

> repository subtree or file → CI workflow/pipeline → jobs/tasks transitively run.

Mainstream products expose either:

1. An authored path-to-workflow rule.
2. A runtime job DAG.
3. A build/project dependency graph.
4. A workflow/action call graph.
5. An affected project/test set.

The unification of all five remains a gap. Ravelact covers workflow triggers and workflow/action calls but not general code/build dependencies; Nx/Bazel cover code/build impact but not the complete CI orchestration estate. No standard surveyed in section 5 defines that combined topology.

## 7. Evidence that derived facts accelerate an agent

### Measured results

**[high for the reported benchmark; limited external validity]** The peer-reviewed [RepoGraph ICLR 2025 paper](https://proceedings.iclr.cc/paper_files/paper/2025/file/4a4a3c197deac042461c677219efd36c-Paper-Conference.pdf) added a tree-sitter-derived line-level definition/reference graph to four SWE-bench Lite methods. Reported resolution-rate improvements were:

- RAG: 2.67% → 5.33%.
- Agentless: 27.33% → 29.67%.
- AutoCodeRover: 19.00% → 21.33%.
- SWE-agent: 18.33% → 20.33%.

The same tables show token use or monetary cost increasing in several configurations, although SWE-agent’s average turns decreased. This is evidence of higher task success, not a general proof of lower token or compute cost. The benchmark is limited to SWE-bench Lite, predominantly Python repositories, and the models/tooling used in that study.

**[moderate; author-run, small and partly synthetic]** The [RIG/SPADE preprint](https://arxiv.org/abs/2601.10112) reports experiments across three commercial agents, eight repositories—seven synthetic and one real—and structured repository questions. It reports mean accuracy improving by 12.2%, elapsed time falling by 53.9%, and seconds per correct answer falling by 57.8% when agents had the deterministic repository graph. This is direct acceleration evidence, but the small, author-constructed corpus and question format limit generalization to real code-change tasks.

**[moderate; vendor production case study, not specifically LLM agents]** [Meta’s predictive test-selection report](https://engineering.fb.com/2018/11/21/developer-tools/predictive-test-selection/) says its system caught more than 99.9% of regressions before trunk while running about one-third of the transitively dependent tests, and approximately doubled test-infrastructure efficiency. This measures acceleration of the development/test loop, not acceleration caused by giving repository facts to an LLM.

### Vendor measurements and claims

**[low; vendor-run and indirect]** [Graphify’s benchmark](https://github.com/Graphify-Labs/graphify/blob/v8/BENCHMARKS.md) reports results on LOCOMO and LongMemEval-style memory retrieval tasks under a published harness. Those results concern retrieval and conversational memory, not repository editing, issue resolution, or CI understanding. They do not establish agent-loop acceleration for software-engineering work.

**[low; vendor-internal, methodology not independently exposed]** [Cursor reports improved response accuracy from codebase indexing](https://prod.cursor.com/blog/secure-codebase-indexing), but the evidence is a vendor account without enough public experimental detail to separate indexing effects from product/model changes.

**[low; design rationale rather than evaluation]** [Aider explains why it supplies a compact ranked repository map](https://aider.chat/2023/10/22/repomap.html), but the cited material does not present a controlled comparison demonstrating faster completion or higher repository-task success.

**[low; adoption evidence, not acceleration measurement]** [Meta documents Glean use for code navigation, test coverage, test selection, and RAG](https://engineering.fb.com/2024/12/19/developer-tools/glean-open-source-code-indexing/), but does not publish a controlled agent benchmark there.

### Overall evidentiary judgment

**[moderate]** The honest state is:

- There is credible measured evidence that structural repository graphs can improve benchmark success and, in one small study, reduce elapsed time.
- There is strong non-LLM evidence that derived dependency/change-impact facts reduce unnecessary test execution.
- There is not yet broad independent evidence that committed repository-fact artifacts outperform fresh on-demand or service indexes.
- Most commercial claims about agent acceleration remain vendor-reported.
- No evidence found isolates “review-visible committed graph in the diff” as the causal accelerator.

## Known unknowns

- **[moderate]** “Graphify” may refer to a private/internal tool or a different project; the Graphify Labs identification is the closest public exact match.
- **[moderate]** ravelact is very recent. Its existence defeats a categorical “nobody derives CI topology” conclusion, but its adoption, stability, and completeness are not yet established.
- **[moderate]** Closed-source internal developer platforms may already unify source, build, test, ownership, and CI graphs without publishing their schemas.
- **[moderate]** The CI-topology absence finding is bounded by discoverable English-language public documentation as of 2026-09-04; it is not proof of universal nonexistence.
- **[high]** None of the surveyed freshness mechanisms eliminates extractor bugs, unsupported languages, dynamic configuration, generated-at-build behaviour, or incorrect inference. They make the claim reproducible and its age inspectable; they do not make it infallible.
