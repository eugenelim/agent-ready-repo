# Code graphs in AI code review: evidence survey

## Decision question

Should `work-loop` add an always-on code graph or a graph-specialist reviewer to
match code-review products that advertise repository-graph context? Relatedly,
does their named “data migration” lens expose a missing reviewer in our roster?

This survey distinguishes four claims that are easy to blur together:

1. vendors use repository graphs;
2. graphs help code navigation or issue resolution;
3. graph-derived context improves defect detection in code review; and
4. a separate graph or migration persona improves the review system.

Only the third and fourth claims could justify changing our reviewer topology.
The relevant comparator is our repo-grounded, tool-using review—not diff-only
review.

## Verdict

Do **not** add a code-graph specialist, mandate graph construction, or add a
data-migration reviewer. Strengthen the existing reviewers with a triggered
**impact-trace protocol** and make graph lookup an optional evidence provider.
Route stateful migrations through `quality-engineer` using expanded
`operational-safety` depth. [moderate]

That recommendation is based on several independent results, but confidence is
not high because direct, controlled evidence about graphs in *defect-oriented
code review* remains scarce. Research shows both benefit and harm from added
repository context; the outcome depends on the retrieval method, model, task,
and amount of irrelevant context.

## Findings

### 1. Repository graphs are a real industry technique, not evidence of superiority

Greptile documents a graph of files, functions, calls, imports, and dependencies;
Bito advertises a live knowledge graph; and CodeRabbit/CodeAtlas-style systems
advertise callers, dependents, entry points, and tests as review context. These
independent first-party descriptions establish adoption. They do not establish
causal effectiveness because the vendors change models, prompts, agent loops,
retrieval, and validation together. [high]

Sources: [Greptile graph-based context](https://www.greptile.com/docs/how-greptile-works/graph-based-codebase-context),
[Bito product description](https://bito.ai/new-homepage-bito/), and
[CodeAtlas research benchmark](https://www.codeatlas.live/research).

### 2. Direct code-review evidence says context selection matters more than context volume

AACR-Bench evaluates repository-context retrieval on 200 pull requests from 50
repositories and finds no universally beneficial strategy. Naive BM25 or
embedding retrieval can add harmful noise; effects vary by model and language.
Its agentic retrieval condition achieves much higher precision but very low
recall, which the authors describe as contextual tunnel vision. [moderate]

SWE-PRBench reports monotonic degradation across eight models when moving from
diff-only context to file/execution context and then to structured context that
includes AST extraction, an import graph, and test signatures. This is unusually
direct counter-evidence, but it is a recent preprint, uses a model judge, and
does not test every possible graph representation. [moderate]

LAURA is an important moderator: its context-enriched retrieval and review
knowledge improve generated review-comment quality, and its ablations find
positive contributions from all components. It evaluates comment generation,
not systematic defect recall, and does not isolate graph structure. It therefore
supports *curated context*, not an always-on graph. [moderate]

Sources: [AACR-Bench](https://arxiv.org/html/2601.19494v3),
[SWE-PRBench](https://arxiv.org/abs/2603.26130), and
[LAURA, ASE 2025](https://arxiv.org/abs/2512.01356).

### 3. The strongest graph results are adjacent to code review, not code review itself

RepoGraph, published at ICLR 2025, reports an average relative improvement of
32.8% when its repository graph is plugged into four SWE-bench software-
engineering systems. LocAgent and CodexGraph likewise report gains in repository
localization or issue resolution. These results show that structured dependency
navigation can help an agent find code needed to implement a known task. They do
not show that it improves the open-ended search for unknown defects, preserves
precision, or warrants a separate reviewer. Transferring the result to code
review would be an inference across tasks. [moderate]

Sources: [RepoGraph, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/4a4a3c197deac042461c677219efd36c-Paper-Conference.pdf),
[LocAgent](https://arxiv.org/abs/2503.09089), and
[CodexGraph](https://arxiv.org/abs/2408.03910).

### 4. Demand-driven exploration plus validation is better supported than graph dumping

RepoAudit explores data flow on demand along feasible paths and validates facts
and path conditions; it reports 78.43% precision on its benchmark and 174 of 185
newly found bugs confirmed or fixed. Greptile also says its newer architecture
replaced a fixed context step with recursive search and nested-call exploration.
AACR-Bench independently recommends adaptive context and active auditing rather
than passive ingestion. These systems differ substantially, so this is design
direction rather than a measured head-to-head verdict. [moderate]

Sources: [RepoAudit](https://arxiv.org/abs/2501.18160),
[Greptile v3](https://www.greptile.com/blog/greptile-v3-agentic-code-review), and
[AACR-Bench](https://arxiv.org/html/2601.19494v3).

### 5. Vendor graph benchmarks do not isolate the graph

CodeAtlas reports a large improvement over raw-diff Claude, but its graph-assisted
result selects the highest-recall output from five runs while the baseline is a
single run. Its context bundle also combines graph relations, entry points,
callers, dependents, tests, and a windowed diff. That demonstrates a promising
system configuration, not the graph's causal contribution. Bito's published
knowledge-graph gain is on SWE-bench-style issue resolution, not code review.
The claims are useful hypotheses for our benchmark, not adoption evidence.
[low]

Sources: [CodeAtlas methodology](https://www.codeatlas.live/research) and
[Bito](https://bito.ai/new-homepage-bito/).

## What to do about our reviewers

Our present structure is already closer to the evidence-supported shape than
the panel comparison suggests:

- `adversarial-reviewer` is the general defect, drift, edge-case, and assumption
  challenger, iterated to clean in full mode;
- `quality-engineer` owns reliability, testability, observability, and
  maintainability, with progressive operational depth;
- `security-reviewer` remains conditional on a security boundary;
- repository instructions, the spec, plan, ADRs, tests, compiler/typechecker,
  and code search are the normal grounding surface; optional knowledge packs are
  additive rather than required authority; and
- adjudication belongs after findings are produced. A `findings-adjudicator`
  can suppress weak findings but cannot recover defects that no reviewer found.

The missing control is not another persona. It is an explicit requirement to
trace impact when the change shape predicts non-local consequences. Add the
following protocol to the existing adversarial review, with the quality reviewer
checking the associated tests and rollout properties:

1. Trigger on public API/signature changes, shared registries, serialization or
   schema changes, renamed/moved/deleted symbols, side-effect changes,
   dependency/config changes, or persistent-state writes.
2. Identify callers, consumers, readers/writers, tests, and deployed-version
   boundaries using the repository's available tools (`rg`, language servers,
   compiler/typechecker, tests, and static analysis).
3. Follow only relations needed to accept or reject a concrete risk hypothesis.
4. Preserve provenance: distinguish changed code, inspected unchanged code,
   inferred relationships, and tool-proven relationships.
5. Never claim completeness from textual search or a partial graph. Treat stale,
   dynamically dispatched, generated, reflective, and cross-service edges as
   explicit blind spots.

A graph provider may answer step 2 when available, but it should not change the
reviewer roster or become mandatory repo infrastructure. [moderate]

Local basis: [`work-loop`](../../../../packs/core/.apm/skills/work-loop/SKILL.md) already routes
specialists by risk, and [`operational-safety`](../../../../packs/core/.apm/skills/operational-safety/SKILL.md)
already uses selective, orchestrator-loaded depth rather than new reviewers.

## What the “data migration lens” actually is

The useful lens is narrower and more precise than “the code is changing, do
schemas change?” It is **persistent-state compatibility during a rollout where
old and new representations or old and new code may coexist**.

Trigger it when a change affects any of:

- database schemas, indexes, constraints, or stored values;
- serialized files, durable caches, configuration state, or checkpoints;
- message/event/API payload versions retained beyond one request;
- backfills, replays, imports, exports, or destructive transformations; or
- rolling deployments in which old and new binaries share state.

Then check:

- expand/contract order and the old-reader/new-writer compatibility matrix;
- backfill idempotency, resumability, batching, locks, and concurrency;
- validation/reconciliation of transformed data;
- rollback semantics for both code and already-mutated data;
- observability, stop conditions, recovery, and mixed-version tests; and
- retention, deletion, or irreversible-loss boundaries.

If neither persistent representation nor mixed-version deployment changes,
record a named non-trigger and move on. This belongs to `quality-engineer` via
`state-and-idempotency`, `drift-and-rollback`, and
`observability-and-smoke`—not a fourth reviewer. The current
[`state-and-idempotency` module](../../../../packs/core/.apm/skills/operational-safety/references/state-and-idempotency.md)
already names stateful migrations, but it is infra-shaped and does not yet spell
out the reader/writer compatibility, backfill, and data-validation checks above.
That is the concrete reviewer-depth gap. [high]

## Verdict mechanism: their score versus our gate

The proposed deterministic 0–100 score is clearer as a dashboard, but weaker as
the authority that decides whether work may proceed. A weighted score introduces
three false assurances:

- **false precision:** pinned weights make identical inputs reproducible, not
  the weights objectively correct;
- **compensation:** several strong dimensions can numerically conceal a severe
  defect unless every non-compensable condition is separately capped; and
- **unstable calibration:** a score's meaning shifts with reviewer recall,
  finding deduplication, severity inflation, and the number of lenses run.

Their survived-blocker cap correctly acknowledges that some conditions must not
be averaged. Once that rule exists, however, the real decision mechanism is the
categorical blocker gate; the number is a secondary presentation layer.

Our full-mode mechanism has the sounder control semantics: warranted reviewers
must return a strict clean verdict, findings are severity-labelled and
dispositioned, fixes return through gates and review, repeated fingerprints
detect stasis, retry limits stop infinite convergence, and the human retains the
merge decision. It says what remains wrong and what must happen next instead of
compressing heterogeneous risk into one scalar. The running findings-adjudicator
can improve finding validity before disposition, provided it cannot suppress a
finding silently or redefine the merge policy. [high]

Our mechanism still has two clarity problems:

1. “Clean” is a reviewer assertion, not a calibrated estimate of residual risk
   or proof of complete coverage.
2. The final record should make warranted lenses, named skips, findings,
   adjudications, unresolved blockers, gates, and blind spots visible in one
   machine-readable summary.

Therefore keep the categorical gate and add a **verdict record**, not a verdict
score. A useful result has four states:

- `BLOCKED`: at least one unresolved accepted blocker, invalid/missing mandatory
  review, failed required gate, or prohibited silent suppression;
- `CHANGES_REQUIRED`: accepted non-blocking findings still require action;
- `READY_WITH_RESIDUAL_RISK`: all required controls passed, with at least one
  residual-eligible non-mandatory-reviewer skip, accepted deferral, or accepted
  analysis blind spot visible;
- `READY`: all warranted controls passed and all findings are resolved.

This is explanatory shorthand. The closed schema, residual-eligibility rules,
and state precedence in [`../spec.md`](../spec.md) are the controlling contract.

If consumers still want 0–100 for sorting, compute it only as explicitly
non-authoritative telemetry beside this record. Never let it override a blocker,
a missing mandatory lens, an invalid review, or a failed gate. [high]

Local basis: [`work-loop`](../../../../packs/core/.apm/skills/work-loop/SKILL.md) already records
finding fingerprints, retry/stasis behavior, dispositions, required reviewers,
and the human gate; the improvement is to project that evidence into a clearer
summary rather than replace it with weights.

## Evidence-gated graph experiment

Before adopting a graph dependency, run an A/B evaluation with the same model,
reviewer instructions, defect corpus, and findings-adjudication policy:

| Arm | Navigation available |
|---|---|
| A | Current targeted search, repository docs, tests, compiler/typechecker |
| B | Arm A plus graph queries for callers, callees, imports, and dependents |

Stratify defects by public API, cross-file call path, configuration, dynamic
dispatch, serialization/schema, and stateful rollout. Measure adjudicated defect
recall, precision, cross-file recall, reviewer overlap, time, tokens, tool
failures, graph freshness, and unsupported completeness claims. Run multiple
samples per PR; the CodeAtlas comparison demonstrates why best-of-N versus
single-run comparisons are not credible.

Pre-register an adoption rule: graph assistance must produce a repeatable gain
on cross-file defects after adjudication without a material precision, latency,
or operating-cost regression. Set the numeric threshold from the baseline and
product budget rather than inventing one before measurement.

## Known unknowns

- No public benchmark found cleanly ablates *graph queries versus equally
  capable active textual/symbol search* on defect-oriented pull-request review.
- Dynamic-language, reflection, generated-code, macro, runtime configuration,
  database, and cross-service edges may be absent or stale in static graphs.
- Existing studies vary in models, prompts, context budgets, defect definitions,
  judges, and sampling; their absolute scores are not comparable.
- Most graph evidence concerns fixing a known issue. Review starts without a
  known issue and may have different exploration economics.
- We do not yet have our own reviewer-level measurements for recall, precision,
  overlap, cost, or migration-defect coverage.

## Confidence method and scope limits

Confidence labels follow a standard evidence discipline: independent primary or
peer-reviewed sources raise confidence; vendor self-evaluation, task indirectness,
methodological confounds, and inconsistent results lower it. The search covered
recent primary research and first-party product methodology available through
public web retrieval as of 2026-08-23. It did not inspect proprietary customer
data or unpublished benchmark corpora.
