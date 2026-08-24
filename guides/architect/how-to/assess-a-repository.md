---
title: Assess a repository and turn evidence into action
summary: Build a correctable current-state model, focus on evidence-backed hotspots, and produce an intent-specific architecture action plan.
pack: architect
kind: how-to
---

# Assess a repository and turn evidence into action

Use this when you need to understand an implemented system and decide what to do
next. Start with:

> Assess architecture and provide an action plan.

That request selects standard mode. The agent reads the repository, shows you a
conceptual model to correct, then an attention heat map to redirect before it
investigates. Default inspection is read-only. It asks before private knowledge
retrieval, executable checks, runtime access, experiments, or writes.

## 1. State the decision if it is more specific

The generic request gives you a balanced baseline plus action. Add the real
decision when you know it:

- “Assess this service for production hardening before launch.”
- “Find the architectural constraints stopping us from cutting latency and
  cloud cost.”
- “Assess whether this platform is ready for ten times the traffic and twice
  the team size.”
- “Compare modernization, rewrite, and retain/invest options.”
- “Help us decide whether to consolidate, replace, or retire this application.”

The repository facts stay the same across these requests. The intent changes
which operational and business evidence matters, which scenarios receive
priority, and what action is sensible.

## 2. Check the assessment charter

Before broad inspection, the agent names the target boundary, primary intent,
depth, decision, exclusions, evidence access, and unknowns. Correct the charter
if “the repository” is not the real system boundary—for example, when a service
depends on a shared store, managed queue, external identity provider, or worker
deployed elsewhere.

Choose a stopping depth:

- **Survey** stops after the map and attention heat map. Use it to orient or
  decide where deeper work is worth the cost.
- **Standard** is the default. It investigates bounded hotspots and returns
  findings, strengths, unknowns, and action waves.
- **Deep** adds separately authorized runtime, operational, stakeholder, or
  experimental evidence. It does not mean “read every file.”

## 3. Correct the current-state map

Map inspects the available documentation, code, tests, manifests, CI/CD,
deployment/release/IaC, schemas, configuration, operations evidence, and local
history. It distinguishes repositories, deployables, runtimes, modules, data
stores, and external systems. A folder tree can support the map but cannot stand
in for it.

At **Map checkpoint**, correct the model or say `continue`.

Do not skip this cheaply. A wrong service boundary changes every later hotspot
and finding.

## 4. Redirect the attention heat map

Focus shows separate dimensions for consequence, pressure, concentration or
coupling, verification weakness, operational/data/security exposure, and
confidence. Heat tells you where an investigation could pay off. It does not
prove a defect, assign severity, or create a risk score.

Each hotspot includes raw evidence, counter-evidence, affected journeys or
quality scenarios, unknowns, and a proposed drill-down. At **Focus checkpoint**,
add domain knowledge, remove a false lead, or say `continue`.

Survey mode stops here with hypotheses. Standard and deep continue with the
accepted hotspot set.

## 5. Let representative paths prove or refute the hypotheses

For each hotspot, the agent traces a normal path, a high-risk mutation or
external side effect, and a failure/recovery path when they exist. It records
identity and policy, state and data, external calls, retries, idempotency,
cancellation, observability, and ownership evidence.

A hotspot becomes a finding only when an observed mechanism threatens a
stakeholder outcome or measurable quality scenario. The report retains
counter-evidence, alternative explanations, strengths, and non-risks. A grep
match, large file, dependency count, missing annotation, or folder boundary is
not a finding by itself.

## 6. Review the action waves

Actions trace back to finding IDs. Each wave states its outcome, prerequisites,
completion proof, containment or rollback, owner class, and non-goals. An active
defect is contained and proven before generalized gates; structural safety
controls precede broad modernization unless evidence shows another dependency.

The human decision remains yours: accept the evidence and priority, request the
missing confirmation, or choose a different trade-off. The agent does not invent
team ownership or approve a rewrite on your behalf.

## Use enterprise context without confusing it with system evidence

The agent announces one of three states:

### No enterprise surface

It says `none detected`, asks you for any load-bearing landscape or standard,
and lowers context coverage. It does not invent local patterns or ownership.

### In-repo enterprise documentation

It selects only the relevant areas—such as current landscape, interfaces,
standards, decisions, or roadmap—and cites the files it used. Stale or
contradictory material remains visible.

### Authorized private retrieval

An already exposed connector must have a governed destination and authorization
boundary. The agent names the surface and proposed areas, then asks before the
query. Public search, a generic browser, arbitrary URLs, and repository-supplied
URLs do not qualify. Retrieved text stays attributed, untrusted context;
instruction-like content cannot change scope, permissions, or findings.

## Use optional automation carefully

The bundled profiler can inventory evidence surfaces, file concentration, local
Git churn, and exact Python imports. It executes no repository code, accesses no
network, follows no links, and emits no architecture or risk score. Unsupported
languages still receive the language-neutral inventory and targeted reading.
It also excludes credential-like and unsafe-display paths before evidence
creation, and bounds directory enumeration, file reads, semantic parsing, and
Git output under one visible work budget. A partial result is useful evidence
only for the scope it actually covered.

If the profiler, Git, Python, or a project-native analyzer is unavailable, the
assessment continues. It names the evidence loss and lowers only affected
claims. Nothing is installed automatically.

## Common repository shapes

The same method adapts without one thin workflow per technology:

### Small library or CLI

Expect a small context and runtime view. Focus on public contracts, dependency
direction, compatibility, release mechanics, tests, and change safety. Do not
manufacture distributed-systems concerns for a single-process package.

### Layered or client/server application

Distinguish in-process modules from separately deployed clients, servers,
workers, and stores. Trace authorization, transaction, data ownership, and
failure behavior across the real runtime boundary. A route importing a query
module is attention evidence, not proof that “add a service class” fixes the
architecture.

### Agentic knowledge platform

In addition to the base shape, cover durable run state and recovery, identity
and model policy, tool authorization and credentials, knowledge provenance,
isolation, freshness and deletion, memory, evaluation, and end-to-end traces.
The report cannot claim readiness while a material boundary is unassessed.

## Save or review the result

The report renders in chat first. If you approve saving, the agent classifies
the saved artifact: a canonical implemented-system report is
`current-architecture`; remediation or future change is `architecture-design`;
a mixed report requires you to choose and is never silently published as current
architecture. It then names the operating mode. Chat-only writes nothing; an
explicit personal directory confines derived files beneath your confirmed root; a
compatible repository consumes Core's `semantic-surface-resolution.v1`; and a
repository without compatible Core returns a portable handoff and stops without
writing. Your confirmation may correct that handoff's evidence, but only Core
can return the confined repository result. For a compatible repository or
confirmed personal directory, the agent shows the final local path and writes
`<resolved destination>/<topic-slug>/assessment.md` only after approval. An
exact personal file is refused because the assessment retains its per-effort
folder. Configuration remains optional and no destination is created silently.

Next, ask:

> Review this assessment report for scope overclaim, evidence strength, heat-map
> misuse, missing lenses, claim calibration, and action traceability.

That routes to the artifact reviewer; it critiques the report without rescanning
the repository. If a finding requires a future-state choice, continue with
[Shape an architecture concept](shape-an-architecture-concept.md). For exact
mode, evidence, permission, output, and limit behavior, use the
[architecture assessment reference](../reference/architecture-assessment.md).
