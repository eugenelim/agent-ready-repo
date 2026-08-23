# Repository architecture assessment methodology

> Discipline: applied (practitioner-pattern survey)

This methodology defines how an agent should assess the architecture embodied by
an unfamiliar software repository and produce a risk-ranked action plan. It is
designed for repositories whose real system may be a library, CLI, modular
monolith, client/server application, distributed service estate, event-driven
system, data or ML platform, or GenAI/agentic knowledge platform. It treats those
as composable lenses rather than mutually exclusive templates because production
systems commonly combine several of them. [synthesis]

The central distinction is between an **artifact review**, a **code-compliance
audit**, and an **architecture assessment**. An artifact review judges a design
doc or diagram. A compliance audit checks implementation against already-known
rules. An architecture assessment reconstructs the implemented system, identifies
its stakeholders and architectural drivers, tests how its structures respond to
quality-attribute scenarios, evaluates shape-specific risks, and turns evidence
into sequenced decisions and work. ISO/IEC/IEEE 42010 distinguishes an entity's
architecture from the description that expresses it; ISO/IEC 25010 supplies a
quality model for evaluation; and the SEI's ATAM evaluates architecture relative
to quality-attribute goals, scenarios, risks, sensitivity points, and tradeoffs.
[high]

Evidence: [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html),
[ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html), and the
[SEI ATAM collection](https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/).

# 1. Scope frame

| SIPOC element | Repository architecture assessment |
| --- | --- |
| Suppliers | Repository owners, maintainers, users, operators, security and platform teams; source, configuration, schemas, tests, deployment definitions, telemetry, history, and architecture records |
| Inputs | Assessment question, repository boundary, business purpose, stakeholder concerns, constraints, desired depth, available evidence, and permission to run bounded checks |
| Process | Frame, inventory, reconstruct, identify drivers, analyze structures and boundaries, apply triggered lenses, validate scenarios, synthesize findings, and sequence action |
| Outputs | Scope and confidence statement, evidence map, current-state system model, quality-driver and scenario set, risk register, strengths and constraints, unknowns, and a dependency-aware action plan |
| Customers | Maintainers deciding what to fix, preserve, redesign, investigate, or explicitly accept |

The entity of interest must be named before inspection: one repository is not
necessarily one deployable system, and one deployable system may span several
repositories. The assessment records repository boundaries, runtime boundaries,
external dependencies, environments, and excluded systems separately. This
follows ISO/IEC/IEEE 42010's distinction between an entity and an architecture
description and the cloud frameworks' workload-scoped review posture. [moderate]
Downgrade: `indirectness` because the sources define description and workload
scope, while the repository-to-runtime reconciliation is this methodology's
application of those concepts.

Evidence: [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html),
[AWS Well-Architected definitions](https://docs.aws.amazon.com/wellarchitected/latest/framework/definitions.html),
and the [Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework).

Every assessment starts with four explicit boundaries. [synthesis]

- **Decision boundary:** what decision will the assessment enable: production
  containment, modernization, scaling, platform readiness, acquisition due
  diligence, design conformance, or general health?
- **System boundary:** which repositories, deployables, data stores, external
  services, user journeys, environments, and organizational owners are included?
- **Evidence boundary:** static repository evidence only, or also executable
  tests, deployment state, telemetry, incidents, and stakeholder interviews?
- **Depth boundary:** `survey`, `standard`, or `deep`, with a named time or
  evidence ceiling and a stop condition.

The output is not a maturity score detached from consequences. It is a set of
evidence-backed findings tied to affected stakeholders, failed or threatened
quality scenarios, architectural decisions, confidence, and the smallest safe
next action. [synthesis]

# 2. Stage spine

## Stage 1 — Elicit the decision and calibrate depth

- Restate the decision the user needs, the entity of interest, known constraints,
  and what “good enough” means. Ask only for missing facts that would materially
  change scope, risk, or evidence access. [synthesis]
- Select one progressive mode. `Survey` provides a bounded structural map and
  hypotheses from repository evidence. `Standard` adds traceable findings,
  scenario analysis, and targeted executable checks. `Deep` adds runtime and
  operational evidence, failure injection or representative experiments,
  stakeholder perspectives, and independent challenge. Each deeper mode retains
  the preceding outputs rather than starting a different method. [synthesis]
- Refuse a whole-system verdict when the evidence boundary covers only one
  subsystem. A backend-layer audit may be valuable, but its title, verdict, and
  claims must stay at backend-layer scope. [synthesis]

The need to name stakeholders, concerns, views, quality goals, and scenarios is
well established across architecture-description, product-quality, and
scenario-based evaluation standards. Progressive depth is a delivery choice in
this methodology, not a claim that those standards define these three labels.
The underlying lightweight-to-comprehensive progression is supported by the
SEI's ARID method, which provides a lightweight scenario-based suitability
review without complete architecture documentation, and ATAM, whose full
evaluation gathers stakeholders around quality goals, scenarios, risks, and
tradeoffs. [high]

Evidence: [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html),
[ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html), and
[SEI ARID](https://www.sei.cmu.edu/library/active-reviews-for-intermediate-design-arid/),
and [SEI ATAM](https://www.sei.cmu.edu/library/atam-method-for-architecture-evaluation/).

## Stage 2 — Build an evidence ledger before drawing conclusions

- Inventory authoritative and observed evidence: root and scoped agent
  instructions, manifests, entry points, dependency declarations, schemas,
  configuration, migrations, public interfaces, tests, deployment definitions,
  operations docs, ADRs/RFCs, ownership, telemetry, incidents, and change history.
  Record each source's scope and freshness. [synthesis]
- Distinguish **declared**, **implemented**, **exercised**, and **observed**
  architecture. Documentation declares intent; code and configuration implement
  structures; tests and builds exercise paths; telemetry and incidents observe
  production behavior. Contradictions become findings or unknowns rather than
  being silently reconciled. [synthesis]
- Maintain a claim ledger with `claim`, `evidence`, `counter-evidence`, `scope`,
  `confidence`, and `validation needed`. Do not allow repository-wide counts,
  folder names, or grep hits to stand in for traced execution paths. [synthesis]
- Mark generated projections, vendored code, fixtures, examples, and dead paths
  so they do not distort the system model. Confirm live entry points before
  treating a pattern as active architecture. [synthesis]

Architecture documentation is valuable only when it remains useful and current,
and assessment questions must be grounded in a specific workload and its quality
goals. These sources converge on combining documented intent with operational and
measurement evidence, but the four-part evidence ledger is a synthesis. [moderate]
Downgrade: `indirectness`.

Evidence: [Google Cloud's documentation principle](https://docs.cloud.google.com/architecture/framework#document_your_architecture),
[AWS Well-Architected definitions](https://docs.aws.amazon.com/wellarchitected/latest/framework/definitions.html),
and [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html).

## Stage 3 — Reconstruct the current system in multiple views

- Produce the smallest useful set of views: context and external actors;
  deployable/container topology; code/module dependencies; runtime interactions
  for critical journeys; data ownership and lifecycle; deployment and operations;
  and trust/identity boundaries. Omit a view only with an explicit reason.
  [synthesis]
- Reconcile static and runtime boundaries. A package boundary that shares a
  database and deployment lifecycle is not an independently operable service;
  two directories may be one runtime, while one directory may build several
  deployables. [synthesis]
- Trace three kinds of path: a representative happy path, the highest-risk
  mutation or side-effect path, and a failure/recovery path. For each, record
  identity, state, data, policy, external calls, retry/cancellation behavior,
  observability, and ownership as applicable. [synthesis]
- State the dominant architectural style and every material secondary style.
  Architecture styles impose constraints and tradeoffs; hybrid systems require
  multiple lenses rather than being forced into one label. [moderate]
  Downgrade: `vendor-blogged` because the cross-style source is provider-authored,
  though it is official practitioner guidance.

Evidence: [Azure Architecture Styles](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/),
[ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html), and the
[Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework).

## Stage 4 — Identify architectural drivers and measurable scenarios

- Derive the top quality attributes from business impact multiplied by
  architectural risk; do not give every quality equal weight. Cover at least
  functional suitability, reliability, security/privacy, performance,
  operability, maintainability/changeability, compatibility/interoperability,
  and cost where relevant, then add workload-specific qualities. [synthesis]
- Express each priority as a scenario: source, stimulus, artifact, environment,
  response, and response measure. Examples include recovery after worker death,
  tenant isolation during retrieval, change lead time for a high-churn module,
  or cancellation during an irreversible tool action. [synthesis]
- Build a utility tree or equivalent ranked scenario set. Trace each scenario to
  the responsible structures and mechanisms; identify risks, non-risks,
  sensitivity points, and tradeoffs. [high]

Evidence: [SEI ATAM collection](https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/),
[ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html), and
[AWS Well-Architected definitions](https://docs.aws.amazon.com/wellarchitected/latest/framework/definitions.html).

## Stage 5 — Analyze base architecture invariants

- **Purpose and domain fit:** system responsibilities, domain boundaries,
  ownership, external contracts, and whether structural complexity is justified
  by the problem. [synthesis]
- **Dependency and change structure:** allowed edges, cycles, unstable
  dependencies, public interfaces, build/deploy coupling, change hotspots, and
  whether boundaries enable independent testing and evolution. [synthesis]
- **State and data:** source of truth, ownership, schemas, consistency model,
  transactions, retention/deletion, migration, cache/index derivation, backup,
  recovery, and provenance. [synthesis]
- **Execution and failure:** synchronous and asynchronous paths, concurrency,
  timeouts, retries, idempotency, cancellation, backpressure, partial failure,
  recovery, and side-effect containment. [synthesis]
- **Trust and policy:** identities, tenant/actor context, authorization,
  secrets/credentials, untrusted inputs, external destinations, audit, and
  fail-open/fail-closed behavior. [synthesis]
- **Delivery and operations:** configuration, environments, build/release,
  observability, SLOs, incident recovery, capacity, cost, and ownership.
  [synthesis]
- **Maintainability:** cohesion, duplication, complexity, test seams, type and
  schema contracts, documentation drift, dependency freshness, and the safety
  of incremental change. [synthesis]

The base lens intentionally combines the ISO product-quality model with the
operational, security, reliability, performance, cost, and sustainability
pillars that independently recur in AWS and Google Cloud guidance. Pillars are
question families, not a checklist whose items all receive equal priority.
[high]

Evidence: [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html),
[AWS Well-Architected pillars](https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html),
and the [Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework).

## Stage 6 — Load only the repository and workload lenses that trigger

- Classify the system on independent axes: artifact shape, code organization,
  runtime topology, data behavior, deployment model, tenancy, criticality, and
  autonomy. A system may load several rows below. [synthesis]

| Triggered lens | Evidence to trace | Characteristic questions |
| --- | --- | --- |
| Library, SDK, plugin, or CLI | Public API/commands, packaging, versioning, compatibility tests, extension points | Is the public contract explicit and evolvable? Are host/runtime assumptions, errors, and upgrade paths controlled? |
| Modular or layered monolith | Module graph, application/domain/data edges, transaction boundaries, shared state | Do boundaries encode business capability or merely folders? Are bypasses live? Can high-risk responsibilities change independently? |
| Client/server or full-stack application | Browser/mobile/backend contracts, session state, caches, API evolution, offline behavior | Where are trust, validation, compatibility, latency, accessibility, and user-visible failure states enforced? |
| Background, queue, workflow, or event-driven | Producers, consumers, schemas, delivery semantics, ordering, deduplication, leases, replay, DLQ, backpressure | What happens after partial success, duplicate delivery, cancellation, restart, schema evolution, or a poisoned event? |
| Distributed services or microservices | Service/data ownership, sync call graph, discovery, contracts, consistency, traces, deployability | Are services autonomous or a distributed monolith? How are partial failure, compatibility, observability, and cross-service change handled? |
| Serverless, edge, or managed-runtime | Binding quotas, duration/cold-start limits, identity/network model, concurrency, event sources, local parity | Does any critical path depend on a non-configurable platform contract? Is sync versus async viable under real limits? |
| Data, analytics, or ML platform | Source-to-serving lineage, batch/stream semantics, schemas, quality, feature/model versions, drift, retention | Can a result be traced and reproduced? Are late data, backfills, deletion, skew, drift, and quality failures controlled? |
| GenAI, agentic, or knowledge platform | Run/step state, model gateway, tool gateway, knowledge pipeline, memory, approvals, evaluations, end-to-end traces | Can untrusted content alter goals or policy? Are model, tool, identity, knowledge, memory, and side effects separately governed and correlated? |
| Infrastructure, platform, or monorepo tooling | Ownership, dependency and generation graph, state, install/upgrade, adapters, blast radius, recovery | Are source and generated artifacts distinct? Are extension and state-ownership contracts explicit? Can a partial operation be safely resumed or rolled back? |

Official practitioner frameworks support style-specific concerns: layered,
web/worker, microservice, event-driven, and big-data styles have different
dependency and failure properties, while cloud frameworks apply cross-pillar
perspectives to specific technologies or domains. The exact lens table above is
a portable synthesis that also covers non-cloud repository forms. [moderate]
Downgrade: `indirectness`; `vendor-blogged`.

Evidence: [Azure Architecture Styles](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/),
[Google Cloud pillars and perspectives](https://docs.cloud.google.com/architecture/framework#well-architected_framework_pillars_and_perspectives),
and [AWS Well-Architected definitions](https://docs.aws.amazon.com/wellarchitected/latest/framework/definitions.html).

For GenAI/agentic knowledge platforms, the assessment must treat identity,
model access, tool execution, knowledge access, and memory as distinct platform
contracts joined by one traceable execution context. It traces the full
knowledge lifecycle—ingestion, parsing/chunking, metadata/ACLs, embedding,
indexing, retrieval, reranking, context assembly, generation, citation,
revocation/deletion, and caches—and separately traces agent planning, approvals,
tool authorization, credentials, side effects, retries, cancellation, and audit.
This is necessary because current authoritative guidance identifies risks and
controls at each of those boundaries rather than at the model client alone.
[moderate]
Downgrade: `vendor-blogged`; `heterogeneity` because the sources organize the
boundaries differently.

Evidence: [NIST AI RMF Generative AI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence),
[OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/),
[AWS agentic enterprise architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/govern-architect-agentic-ai/enterprise-architecture.html),
and [Azure secure multitenant RAG architecture](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/secure-multitenant-rag).

## Stage 7 — Validate the highest-risk claims at the strongest available layer

- Use an evidence ladder: declaration/documentation → static structure → build
  and unit/contract tests → integration with real policy or provider semantics →
  end-to-end execution → fault injection/load/security tests → production
  telemetry and incident evidence. Record the highest layer actually reached.
  [synthesis]
- Validate risks, not every file. Choose checks by scenario severity,
  uncertainty, propagation/blast radius, and reversibility. A critical but
  uncertain cross-tenant or duplicate-side-effect risk earns a real integration
  or failure test before a broad style cleanup. [synthesis]
- Test controls where they execute. Grep and folder scans can freeze a known
  pattern temporarily, but durable conformance requires structural checks,
  construction boundaries, runtime guards, contract tests, or platform policy
  tests that fail closed. [synthesis]
- Record what a passing check proves and does not prove. Annotation lint does not
  establish type consistency; an import rule does not prove runtime policy
  coverage; a unit test with a fake does not prove a database security policy;
  a request-path trace does not cover background entry points. [synthesis]

The need to measure quality, exercise recovery, load test architectural choices,
and validate controls throughout the lifecycle recurs in ISO, AWS, and Google
guidance. The evidence ladder and risk-selection rule are this methodology's
portable synthesis. [moderate]
Downgrade: `indirectness`.

Evidence: [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html),
[AWS Well-Architected questions and best practices](https://docs.aws.amazon.com/wellarchitected/latest/framework/appendix.html),
and the [Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework).

## Stage 8 — Synthesize findings before prescribing solutions

- Each finding includes: title; affected scenario/stakeholder; scope; observed
  evidence and counter-evidence; architectural mechanism; consequence; severity;
  confidence; validation gap; and the smallest safe response. [synthesis]
- Separate **active defect**, **architectural risk**, **constraint/debt**,
  **missing evidence**, **accepted tradeoff**, and **strength/non-risk**. Do not
  label a missing document as a production defect or a code smell as a platform
  risk without a threatened scenario. [synthesis]
- Test alternative explanations. A direct import may be a harmful boundary
  bypass, a deliberate local optimization, dead code, or evidence that the
  supposed boundary is fictional. The finding is not complete until the live
  path and intended ownership are known. [synthesis]
- Run a completeness check against the scope, views, base lens, triggered
  overlays, priority scenarios, and evidence ledger. A document cannot claim
  “platform readiness” when material platform lenses remain unassessed.
  [synthesis]

## Stage 9 — Build a dependency-aware action plan

- Sequence by **containment before generalization**: stop active unsafe behavior,
  prove the fix, freeze expansion of the unsafe pattern, make the safety
  property structural, migrate existing paths, then optimize or modernize.
  [synthesis]
- Rank work using impact, likelihood/exposure, propagation/blast radius,
  reversibility, confidence, and prerequisite relationships. Keep urgency
  separate from implementation size. [synthesis]
- Give every wave an intended outcome, included findings, prerequisites, proof
  of completion, rollback/containment strategy, owner class, and explicit
  non-goals. [synthesis]
- Prefer coverage metrics that prove the control boundary—such as percentage of
  protected operations receiving validated context or zero unmanaged provider
  invocations—over counts that merely track symptoms, such as current bypasses
  or files above a line limit. [synthesis]
- Put modernization debt on a risk-ranked burn-down with no-growth rules and
  characterization tests. Do not force a large refactor into an urgent defect
  fix unless the fix cannot be made safe inside the present structure.
  [synthesis]

ATAM's outputs include risks, non-risks, sensitivity points, and tradeoffs, while
well-architected frameworks explicitly connect review findings to prioritized
improvement. The specific containment-to-modernization wave ordering is a
methodological synthesis derived from incident response and safe-change logic,
not a named step in those frameworks. [moderate]
Downgrade: `indirectness`.

Evidence: [SEI ATAM collection](https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/),
[AWS Well-Architected Tool overview](https://docs.aws.amazon.com/wellarchitected/latest/userguide/waf.html),
and the [Google Cloud design-for-change principle](https://docs.cloud.google.com/architecture/framework#design_for_change).

## Stage 10 — Report the verdict with calibrated limits

- Lead with a one-paragraph bottom line answering the user's decision, then the
  current-state model, priority findings, strengths/non-risks, action waves,
  evidence confidence, and known unknowns. [synthesis]
- State the assessed scope and mode in the title or first screen. Use
  “Backend Invariant Audit” when that is what was done; reserve “Platform
  Architecture Assessment” for evidence that covers the platform's material
  structures and triggered lenses. [synthesis]
- Include a coverage matrix: each required view/lens is `assessed`, `partially
  assessed`, `not assessed`, or `not applicable`, with an evidence pointer.
  [synthesis]
- End with the next decision or validation step, not a generic request to “add
  more tests.” [synthesis]

# 3. Contingency branches

| Situation | How the spine changes |
| --- | --- |
| User asks a broad question with no business context | Run Stage 1 with a short elicitation: decision, production status, critical journeys, known pain, and allowed evidence. If unanswered, proceed in `survey` mode and label hypotheses. |
| Tiny library or CLI | Keep the full spine but compress views; emphasize public contract, dependency direction, packaging, compatibility, state/filesystem/network boundaries, and release safety. Do not force cloud pillars. |
| Monorepo with many unrelated products | Partition the entity of interest before inventory; build a coarse repo map, choose the risk-bearing subsystem or journey, and report uncovered areas rather than averaging them. |
| Sparse or stale architecture documentation | Reconstruct from manifests, entry points, build/deploy definitions, tests, schemas, and live paths; mark the declared-vs-implemented gap. Do not stop merely because diagrams are absent. |
| Strong architecture docs but little executable evidence | Use docs as declared intent, verify representative dependency and runtime paths, and downgrade behavioral claims that remain unexercised. |
| Production incident or active critical defect | Interrupt broad assessment long enough to contain and prove the defect; preserve the broader assessment as a separately scoped continuation. Do not wait for generalized architecture gates. |
| Layered monolith with many bypasses | Baseline live violations, block new ones structurally, risk-rank migration by side effects/security/churn, and verify that proposed application boundaries own decisions rather than pass calls through. |
| Distributed or event-driven system | Expand Stage 3 to message schemas and runtime sequence/state views; expand Stage 7 to duplicate delivery, ordering, partition, timeout, cancellation, replay, and recovery scenarios. |
| Data, ML, or knowledge platform | Add source-to-serving lineage, access decisions, schema/model/index versions, quality/freshness, deletion propagation, reproducibility, and evaluation datasets. |
| GenAI without tool use | Load model and knowledge lenses plus evaluation, provenance, privacy, safety, cost, and observability; do not load autonomous side-effect controls that are truly absent. |
| Agentic system with tools or computer use | Add durable run/step state, execution context, tool authorization, credential resolution, approval, action audit, budget/step limits, cancellation, prompt-injection defenses, and duplicate-side-effect fault tests. |
| Multi-tenant system | Trace tenant and actor context through every synchronous, asynchronous, cache, index, model, knowledge, and tool boundary; test at least two tenants with overlapping identifiers/content. |
| Managed cloud critical path | Ground load-bearing service limits and identity/network behavior in current official contracts before judging viability. |
| Static access only | Stay in `survey`; clearly separate verified structure from runtime hypotheses and list the exact executable evidence needed to advance confidence. |
| Deep mode would be unsafe or destructive | Use non-production replicas, read-only telemetry, contract or simulation tests, and bounded fault models; record the untested production behavior as a known-unknown. |
| Assessment finds no significant risks | Report the evidence-backed non-risks and residual unknowns; do not manufacture findings to justify the exercise. |

These branches instantiate situational method engineering: the stable spine
remains, while evidence depth and loaded lenses change with system shape,
criticality, and access. [synthesis]

# 4. Maturity ladder

The progression applies both to the assessor's practice and to the depth offered
to a user. It is deliberately cumulative: a deeper assessment must preserve the
scope discipline and evidence ledger of the earlier levels. [synthesis]

| Level | Assessment capability | Exit signal |
| --- | --- | --- |
| 0 — Unstructured opinion | Reads prominent files and emits generic strengths, smells, and recommendations | Cannot trace claims to live paths, name scope gaps, or distinguish defects from debt. |
| 1 — Survey | Frames the entity and decision; inventories evidence; reconstructs coarse context/module/runtime/data views; identifies dominant shapes and hypotheses | User needs actionable priorities or confidence above static inference. |
| 2 — Standard | Adds priority quality scenarios, base and triggered lenses, traced representative paths, structural checks, calibrated findings, coverage matrix, and sequenced action waves | Highest-impact claims depend on runtime/provider behavior, failure modes, or stakeholder evidence. |
| 3 — Deep | Adds real integration semantics, telemetry/incidents, representative load/security/fault tests, change-history and ownership analysis, and independent challenge | Residual uncertainty is explicit and closing it would require production change, prolonged observation, or unavailable stakeholders. |
| 4 — Continuous fitness | Converts accepted high-value invariants into automated structural/runtime fitness functions, monitors drift, and periodically refreshes scenarios and risk acceptance | Assessment becomes an operating habit; point-in-time review remains for new decisions and novel risks. |

- **Novice assessor:** follows a checklist and overweights visible code smells.
  Moves up by maintaining a claim/evidence ledger and refusing scope overclaim.
- **Advanced beginner:** reconstructs multiple views and spots broken boundaries,
  but treats all findings alike. Moves up by tying findings to ranked quality
  scenarios and distinguishing defect, risk, debt, unknown, and non-risk.
- **Competent:** composes lenses by system shape, validates high-risk claims at
  appropriate evidence layers, and sequences action by dependency. Moves up by
  actively seeking counter-evidence and sensitivity/tradeoff points.
- **Proficient:** adapts depth and validation to criticality, recognizes hybrid
  architectures, and knows when repository evidence cannot support a platform
  verdict. Moves up by designing failure experiments and structural controls
  that prove the architectural property.
- **Expert:** uses the method as a decision instrument, not a report template;
  compresses low-risk areas, drills into load-bearing uncertainty, preserves
  valid constraints and strengths, and leaves the organization with executable
  fitness functions for the risks that recur. [synthesis]

# 5. Failure modes

- **Wrong artifact:** a design-doc critique or backend lint audit is presented as
  a repository architecture assessment · easy to miss because both use
  architecture vocabulary · guard: state entity, decision, mode, evidence
  boundary, and coverage matrix before the verdict. [synthesis]
- **Folder-shape architecture:** directories and imports are treated as the
  system without tracing deployables, state, data, and runtime paths · easy to
  miss because static scans are fast and countable · guard: reconcile code,
  runtime, data, deployment, and trust views. [synthesis]
- **Checklist flattening:** every pillar and smell receives equal weight · easy
  to miss because comprehensive lists look rigorous · guard: rank measurable
  quality scenarios by business impact and architectural risk. [high]
  Evidence: [SEI ATAM collection](https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/),
  [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html), and
  [AWS Well-Architected definitions](https://docs.aws.amazon.com/wellarchitected/latest/framework/definitions.html).
- **One-style assumption:** the repo is labeled “monolith,” “microservices,” or
  “agentic” and receives only that checklist · easy to miss because labels
  simplify reporting · guard: classify independent architecture axes and compose
  all triggered lenses. [synthesis]
- **Static proof inflation:** a grep, annotation lint, mock unit test, or import
  rule is claimed to prove runtime policy or provider behavior · easy to miss
  because the check is green · guard: record what each evidence layer proves and
  validate high-risk mechanisms where they execute. [synthesis]
- **Inventory without reachability:** every matching file is counted as an
  active violation · easy to miss in large repos with fixtures, generated code,
  and dead paths · guard: trace entry points and callers before assigning impact.
  [synthesis]
- **Missing-overlay blindness:** general backend concerns crowd out agent
  lifecycle, tool authorization, knowledge access, or data lineage · easy to
  miss because familiar code smells are easier to inspect · guard: trigger
  workload lenses from observed capabilities and mark every uncovered lens.
  [moderate]
  Downgrade: `vendor-blogged`.
  Evidence: [NIST AI RMF Generative AI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence),
  [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/),
  and [AWS agentic enterprise architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/govern-architect-agentic-ai/enterprise-architecture.html).
- **Convention proposed as control:** comments, folders, or review expectations
  are prescribed for a safety property that must fail closed · easy to miss
  because policy prose sounds decisive · guard: prefer mandatory execution
  context, centralized gateways/runners, structural dependency checks, runtime
  guards, and exception registries with expiry. [synthesis]
- **Gate before containment:** an active production defect waits for a generalized
  scanner or framework · easy to miss when the review is framed as architecture
  improvement · guard: contain, prove, freeze expansion, structuralize, migrate.
  [synthesis]
- **Solution-shaped finding:** “add a service class,” “split the file,” or “add
  tests” appears without the failed scenario or mechanism · easy to miss because
  it is immediately actionable · guard: findings precede solutions and name the
  threatened quality response. [synthesis]
- **Metric substitution:** file counts, bypass counts, or line limits become
  acceptance criteria for identity, isolation, reliability, or maintainability
  · easy to miss because counts are easy to trend · guard: measure control
  coverage and scenario outcomes; use count baselines only as supporting signals.
  [synthesis]
- **Modernization mixed with safety repair:** broad layering, typing, and file
  decomposition inflate a critical-fix wave · easy to miss because all findings
  are real · guard: separate containment and structural safety from risk-ranked
  modernization unless a prerequisite forces them together. [synthesis]
- **No counter-evidence:** the assessment confirms its first architectural story
  · easy to miss when repository documentation is confident · guard: test at
  least one alternative explanation for each high-severity finding and list
  contradictory evidence. [synthesis]
- **False completeness:** uncovered runtime, organization, or external-system
  evidence disappears from the report · easy to miss because absence looks like
  cleanliness · guard: first-class known-unknowns and a lens coverage matrix.
  [synthesis]

# 6. Evidence & confidence

This methodology is a synthesis of three stable families: architecture
description and product quality standards; scenario-based architecture
evaluation; and practitioner well-architected/style-specific frameworks. The
base spine is well-supported, while the exact progressive-mode names, evidence
ledger, composable lens taxonomy, and containment-to-modernization action
sequence are original synthesis intended for an agent operating against
repositories. [moderate]
Downgrade: `indirectness` because no single source specifies repository-agent
assessment in this exact form.

Evidence: [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html),
[ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html),
[SEI ATAM collection](https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/),
[Azure Architecture Styles](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/),
[AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html),
and the [Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework).

The agentic and knowledge-platform overlay is newer and more volatile. NIST,
OWASP, AWS, and Azure converge on lifecycle risk management, separate model/tool/
knowledge controls, provenance, authorization, and workload-specific evaluation,
but their taxonomies and product assumptions differ. Treat the overlay as
`[moderate]`, refresh it more frequently than the base method, and ground any
provider-specific contract at assessment time. [moderate]
Downgrade: `heterogeneity`; `vendor-blogged`.

Evidence: [NIST AI RMF Generative AI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence),
[OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/),
[AWS agentic enterprise architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/govern-architect-agentic-ai/enterprise-architecture.html),
[AWS secure RAG access guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture-generative-ai/gen-ai-agents.html),
and [Azure secure multitenant RAG architecture](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/secure-multitenant-rag).

## Productization implication — separate workflow from knowledge

The assessment sequence, evidence rules, correction points, and report contract
are workflow procedure. Quality techniques, architecture-shape questions, and
workload lenses are a reusable knowledge corpus with a different change cadence.
Package them separately behind hierarchical, trigger-based retrieval so design,
assessment, and review can share neutral concepts without sharing procedures.
Corpus knowledge says what to investigate; it is never evidence that a target
system implements a pattern or suffers a failure. [synthesis]

In this catalogue, the experimental pack-local OKF projection is a suitable
authoring and delivery candidate for that corpus: it provides provenance,
lifecycle metadata, hierarchical indexes, deterministic generated Skill
delivery, and offline drift checks. The workflow must still own deterministic
trigger selection and explicit coverage because a semantic router alone cannot
guarantee that a required lens fired. This is a productization conclusion from
the repository's current capability, not a claim that OKF is required by the
assessment methodology. [repository-grounded synthesis]

The corpus itself needs an evidence discipline. Build each concept from a typed
desk-research source packet rather than model recall or copied checklists:
standards and original method sources establish durable foundations; independent
provider/framework owners triangulate common quality and workload guidance; and
applied practitioner research supplies case patterns, failure modes, and
counterexamples with survivorship and freshness downgrades. Each packet records
material claims, disagreement, false positives, known unknowns, licensing,
provenance, and whether the concept needs a freshness horizon. The shipped
concept is a concise synthesis; the source packet remains implementation and
maintenance evidence. [synthesis]

Enterprise grounding is a separate composition path. The reusable corpus may
carry the neutral knowledge-area taxonomy, retrieval questions, common
operating-model patterns, and confidence/conflict rules. An adopter's actual
landscape, standards, ownership, operations, decisions, and roadmap must be
retrieved from an authorized internal knowledge surface or supplied by the user,
attributed as enterprise context, and never written back into the portable
corpus. See the
[decision-intent and corpus survey](architecture-assessment-intents-survey.md).
[synthesis]

## Known unknowns

- **Known-unknown:** which progressive mode names and time budgets produce the
  best activation and completion behavior across supported agents. Would be
  closed by: skill evals using small library, monolith, distributed/event-driven,
  and agentic/knowledge fixtures at each depth.
- **Known-unknown:** how much of a deep assessment can be safely and portably
  automated when runtimes expose different shell, browser, deployment, and
  telemetry capabilities. Would be closed by: adapter-specific capability trials
  and a degradation contract exercised across supported adapters.
- **Known-unknown:** whether one portable, hierarchical lens corpus remains
  concise and routes accurately across assessment, design, and review consumers.
  Would be closed by: frozen cross-shape concept-path cases, no-fabrication and
  no-flat-load checks, adapter delivery verification, and guide-driven dogfood.
- **Known-unknown:** whether users need a separate saved current-state system map
  before the assessment report, or whether an embedded view and evidence ledger
  are sufficient. Would be closed by: first-run transcripts and artifact-use
  feedback.
- **Known-unknown:** how the new assessment capability should integrate with the
  existing `reference.md` first-value journey without making that snapshot a
  second architecture source of truth. Would be closed by: pack journey design
  and routing evals.
- **Unknowable:** a universal fixed checklist that is complete for every future
  repository shape. Why not: architecture concerns depend on the entity,
  stakeholders, quality drivers, technologies, and evolving workload classes;
  the method therefore requires a stable base plus extensible triggered lenses.
- **Unknowable:** production behavior that repository, test, deployment,
  telemetry, incident, and stakeholder evidence never recorded. Why not: static
  reconstruction can identify hypotheses but cannot recreate absent operational
  history.
