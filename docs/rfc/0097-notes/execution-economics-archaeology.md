# Execution economics archaeology

> Discipline: applied (decision archaeology plus first-party external validation)
>
> External sources retrieved: 2026-08-26

This note reconstructs why RFC-0097 includes pack- and CI-scale optimization, worktrees, state locks, and shared-machine admission. Commit hashes identify repository evidence available on the current refs; they are not presented as universal rules.

## Chronology

| Date | Commit | Observed problem and decision | Durable lesson |
| --- | --- | --- | --- |
| 2026-08-06 | `c2acf82e` | A lint path started roughly 37,000 shell processes. One Python process preserved behavior and improved median runtime by about six times. | Count process and filesystem work before tuning algorithms. |
| 2026-08-08–10 | `a06bf80a`, `7071655b` | Atomic final writes did not protect a read/decide/write state transition. The state lock gained ownership/liveness semantics, including the empty-fresh-lock case. | Treat durable state as a transaction; stale recovery and ownership loss are correctness paths. |
| 2026-08-12 | `02455563` | Pack tests moved to native pytest collection with pack-local ownership and deliberate per-skill process isolation. | Optimize collection without erasing dependency/import boundaries. |
| 2026-08-17 | `823cd174` | CI jobs split behind a stable aggregator, reducing the measured critical path from roughly 430–450 seconds to 185 seconds; splitting stopped when jobs were balanced. | Optimize the critical path, preserve required-check identity, and stop when coordination dominates. |
| 2026-08-17 | `4dd5c4c1` | 337 repeated `git check-ignore` subprocesses became one batched query; a measured path fell from 32.35 seconds to 2.88 seconds and the suite from roughly 306 seconds to 20 seconds. | Batch repeated stable queries at the boundary that owns them. |
| 2026-08-17 | `e0a9c536` | Semgrep inputs were safely batched, while pip-audit batching was rejected because merging manifests changes dependency-environment semantics. | Similar tools do not imply similar batching safety. State the semantic boundary first. |
| 2026-08-17 | `aa8dc687` | Read-only work-loop transition guards moved in-process without changing FSM, state schema, confinement, or mutation verbs. | In-process calls are valuable when the callable contract is explicit and side effects remain bounded. |
| 2026-08-19–21 | worktree hygiene and lease commits including `e2f6da41` | Multiple worktrees exposed shared temp, cache, port, and state ownership. Lease/admission work separated live ownership from stale recovery. | Worktree directory separation is not resource isolation. Attribute every mutable shared resource. |
| 2026-08-21 | `6452e255` | Browser test scheduling was changed at the file/test boundary without blindly raising worker count. | More workers can increase contention; tune the scheduler against real CPU, memory, and browser cost. |
| 2026-08-21 | `03ce84ec` | One Node setup/cache step covered two npm projects and both lockfiles. | Deduplicate setup while retaining complete cache invalidation inputs. |
| 2026-08-22 | ADR-0094 and related implementation | A repository-wide virtual-environment mandate was declined where it would add startup and maintenance cost without solving the measured boundary. | Do not universalize an environment mechanism; require a concrete dependency/isolation need. |
| 2026-08-21–25 | `dc1e9ce`, `e69583ae` and local-CI changes | Duplicate orchestration, interpreter resolution, caches, and shared tests were removed from composed CI while standalone gates remained complete. | Composition may deduplicate; individual public gates must retain their contract. |

## Rationale chain

1. Agent skills frequently invoke deterministic scripts and tests. Their startup and filesystem costs compound across many skills.
2. Pack suites add ownership, dependency, and isolation boundaries; collapsing them indiscriminately can change semantics.
3. Repository CI composes pack suites, linters, security scans, and site/browser tests. The relevant target is the critical path and fleet resource use, not one command in isolation.
4. Developers and agents run these tasks concurrently in multiple Git worktrees or managed sandboxes on shared machines. Temp paths, caches, ports, browsers, and state remain shared unless explicitly attributed.
5. Therefore performance guidance belongs in one retrieval corpus only when it preserves the skill/eval contract across all five scopes. Repository-specific implementation stays with the owning tooling.

## Alternatives and revival conditions

| Alternative | Why it was rejected or bounded | Revisit when |
| --- | --- | --- |
| Put all optimization in a generic pytest guide | Misses Node/browser, CI critical path, worktree, and shared-host interactions | A separate developer-productivity pack has an independent user job and evidence |
| Run every check in one process | Merges dependency environments and failure/isolation boundaries | The relevant owners prove equivalent environments and behavior |
| Run every check in a separate process | Preserves isolation but can make startup dominate | Measurements show a stable callable or batch boundary |
| Maximize CI job count | Queue/startup/cache duplication can exceed parallel benefit | Fleet data shows more parallel slots reduce end-to-end time without instability |
| Raise browser/test workers to machine CPU count | CPU count ignores memory, browser processes, shared VM tenants, and other worktrees | Load/admission evidence supports a higher bounded cap |
| Use Git worktree locks as activity locks | Git locks protect administrative worktree operations, not application state or build execution | Never; use a purpose-built lease/lock for the application resource |
| Rely on atomic rename alone for state | It protects the final write, not concurrent read/decide/write | Never for multi-writer state; use transaction ownership |
| Mandate one environment manager | Runtime and enterprise environments differ; setup cost may not address the real boundary | A skill's dependency contract requires it and the target runtimes support it |

## External validation

- [pytest good practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html) separates import/test layout choices from runner invocation.
- [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html) emphasizes scoped setup/teardown and isolation; [pytest-xdist](https://pytest-xdist.readthedocs.io/en/stable/distribution.html) exposes different distribution semantics rather than one universal parallel mode.
- [GitHub Actions jobs](https://docs.github.com/en/enterprise-cloud@latest/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs), [dependency caching](https://docs.github.com/en/actions/concepts/workflows-and-actions/dependency-caching), and [concurrency](https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency) support explicit dependencies, cache keys, and admission/cancellation groups.
- [Node packages](https://nodejs.org/api/packages.html), [child processes](https://nodejs.org/api/child_process.html), [`npm ci`](https://docs.npmjs.com/cli/commands/npm-ci/), and [Playwright parallelism](https://playwright.dev/docs/test-parallel) show why Node/module/install/worker behavior needs its own knowledge topic.
- [Git worktree](https://git-scm.com/docs/git-worktree.html) documents shared repository administration and the administrative meaning of a worktree lock.
- The [POSIX lock definition](https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap03.html) and [GNU Make job slots](https://www.gnu.org/software/make/manual/html_node/Job-Slots.html) distinguish mutual exclusion from cooperative capacity allocation.

## Proposed corpus rules

- Measure the dominant resource and preserve a named semantic boundary.
- Treat speedup, throughput, resource use, failure attribution, and flake rate as separate outcomes.
- Prefer bounded batching and stable aggregators over broad orchestration rewrites.
- Do not merge dependency or security-analysis environments for convenience.
- Make worktree identity structural in mutable paths and diagnostics.
- Use transaction locks for durable state and admission caps for scarce machine resources; one does not replace the other.
- Assume enterprise policy may narrow tools, network, filesystem, cleanup, and runtime setup. Detect once, degrade explicitly, and never claim local configuration bypasses policy.
