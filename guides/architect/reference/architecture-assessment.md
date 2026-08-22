---
title: Architecture assessment reference
summary: Look up assessment intents, modes, stages, evidence surfaces, permissions, output fields, confidence, and profiler limits.
pack: architect
kind: reference
---

# Architecture assessment reference

`architect-assess` evaluates an implemented repository or system. It returns a
correctable current-state model, evidence coverage, attention hotspots, bounded
investigations, findings, and action waves. It does not design the future state,
draw a diagram as the main outcome, or review an already supplied artifact.

## Intent index

| Intent | Decision supported |
| --- | --- |
| Baseline / understanding | What exists, how it works, and where uncertainty remains |
| Hardening / risk reduction | Which mechanisms threaten a required safety, reliability, privacy, or readiness outcome |
| Optimize current outcomes | Where the current mission loses latency, cost, operability, or delivery performance |
| Growth / scale readiness | Whether the architecture can absorb future load, product, data, or team pressure |
| Transformation / modernization | Which retained, incremental, replatform, re-architect, or rewrite path fits the evidence |
| Rationalization / disposition / due diligence | Whether to retain, invest, consolidate, acquire/integrate, replace, or retire |

One intent is primary. Secondary intents are explicit. Changing intent changes
required decision data, not facts already observed.

## Modes and stopping points

| Mode | Stages | Result |
| --- | --- | --- |
| Survey | Frame → Map → Focus | Corrected model, evidence ledger, attention heat, hypotheses, recommended drill-downs; no completed findings or action plan |
| Standard | All six stages | Bounded path investigations, findings/strengths/unknowns, and traced action waves |
| Deep | Standard plus approved evidence | Adds named runtime, operational, stakeholder, production-data, or experimental evidence |

Standard is the default for “assess architecture and provide an action plan.”

## Human decisions

Map checkpoint: correct boundaries, responsibilities, or missing dependencies;
`continue` accepts the model.

Focus checkpoint: add, remove, or redirect hotspots; `continue` accepts the
recommended drill-down set.

Close: decide whether evidence is sufficient, which action wave to accept, what
additional proof is needed, and whether to save or route into design.

## Evidence surfaces

Every run status-labels:

| Surface | Typical evidence |
| --- | --- |
| Documentation | Architecture descriptions, ADRs, runbooks, maintained guides |
| Source | Implemented components, boundaries, policies, state transitions |
| Tests | Contracts, construction checks, integration/fault/recovery behavior |
| Manifests/dependencies | Package/workspace manifests, locks, platform contracts |
| CI/CD | Build, test, release, policy, and promotion paths |
| Deployment/release/IaC | Deployables, topology, identity, configuration, rollback |
| Schemas/migrations | Data ownership, compatibility, lifecycle, migration safety |
| Runtime configuration | Environment-specific switches and binding behavior |
| Operational evidence | SLOs, traces, incidents, recovery exercises, cost/capacity |
| Read-only history | Current local-ref churn and decision/change context |

Status values are `observed`, `missing`, `unavailable`, `denied`, `out of
scope`, or `not applicable`. Absence is never reported as “green.”

## Knowledge planes

Target evidence establishes target observations. Enterprise context supplies
attributed local facts and constraints. Pack knowledge supplies reusable
questions, mechanisms, counter-evidence, and confirmation scenarios. The three
remain separate in the final coverage statement.

## Enterprise knowledge

Eligible surfaces: in-repo documentation or an exposed, pre-authenticated,
connector-scoped capability with a governed destination and authorization
boundary.

Rejected surfaces: public web search, generic browser/fetch, arbitrary URLs,
repository-supplied URLs, unknown destinations, or any path that requires the
skill to discover credentials or authenticate.

Before private retrieval, the agent names the surface and the smallest selected
subset of: business/domain meaning; current landscape; interfaces/contracts;
operational reality; constraints/standards; local patterns/reference
architectures; decisions/rationale; in-flight work/roadmap. The user authorizes
the query.

Each retained result records area, claim, surface/locator, retrieval date,
authority/freshness, applicability, confidence/corroboration, sensitivity, and
conflict. Empty, denied, stale, sensitive, malformed, conflicting, or
single-source context lowers affected coverage.

## Reads, execution, network, and writes

Reads without asking: ordinary repository files inside the accepted boundary
and current local Git metadata/history, subject to the active permission
profile.

Asks first: repository code/build/test execution, migrations, deployment,
project-native analyzers, private knowledge queries, runtime or operational
access, stakeholder evidence, experiments, production data, and any write.

Never reads: credentials, browser profiles, protected secret configuration, or
out-of-root link targets. It creates no connector or authentication mechanism.

Writes: none by default. On explicit approval, an assessment may be saved as
`<architecture output_dir>/<topic-slug>/assessment.md`; approved profiler output
may sit beside it or in an explicitly approved workspace/temporary root.

## Current-state and attention output

Current-state views cover context; deployable/runtime; module/capability; data;
interaction; delivery/operations; and trust/identity. Elements are labeled
observed, inferred, reported, or unknown.

Heat dimensions are consequence, pressure, concentration/coupling,
verification weakness, operational/data/security exposure, and evidence
confidence. Values are `low`, `medium`, `high`, or `unknown`. They are never
summed into a composite score. Heat chooses investigation priority; it does not
prove a defect or assign severity.

## Finding and action fields

A finding records classification; stakeholder or quality scenario; scope;
evidence and counter-evidence; mechanism; consequence; severity; confidence;
validation gap; and smallest safe response. Strengths and evidence-backed
non-risks remain alongside problems.

An action wave records intended outcome; included finding IDs; prerequisites;
completion proof; rollback or containment; owner class; and non-goals.

## Lens coverage

Each applicable base, intent, shape, workload, quality, and enterprise lens is
`assessed`, `partially assessed`, `not assessed`, or `not applicable` with an
evidence pointer. A missing or invalid generated knowledge corpus lowers lens
coverage but does not block the repository-grounded method.

Agentic and knowledge platforms must cover material run lifecycle, identity,
model access, tools/credentials, knowledge provenance/isolation, memory,
evaluation, and traces before receiving a readiness conclusion.

## Profiler contract and limits

The optional `profile_repo.py` helper is standard-library-only. It accepts an
explicit root, defaults to stdout, executes no repository code, follows no
link-like entry, reads no special file, accesses no network, and emits only
repository-relative paths. It inventories evidence surfaces, content tags, file
concentration, bounded current-ref Git churn, and exact Python AST imports. It
produces no architecture model, severity, or composite score.

Credential-like paths and browser-profile classes are excluded before
classification or content reads and appear only as redacted exclusions. Paths
with unsafe control, terminal, Markdown-delimiter, or invalid Unicode forms are
also redacted rather than emitted. One shared deadline covers directory
enumeration, semantic reads and AST parsing, and Git collection.

| Limit | Default |
| --- | ---: |
| Files inspected | 20,000 |
| Directory entries enumerated | 200,000 |
| Bytes read from one semantic source file | 1,048,576 |
| Elapsed total profiler work | 30 seconds |
| Current local Git commits considered | 200 |
| Git output bytes retained | 4,194,304 |
| Distinct Git paths retained | 50,000 |

Reaching a limit returns `partial` with the uncovered scope. Unsupported
languages retain generic evidence. An explicit output needs both `--output` and
`--approved-output-root`; otherwise output remains on stdout. Approved writes
use a descriptor-confined temporary file and atomic replacement; a platform
without that primitive fails closed and can still use stdout.

## Saved report order

1. Bottom line
2. Assessment charter
3. Conceptual current state
4. Evidence coverage
5. Attention heat map
6. Hotspot drill-downs
7. Findings, strengths, and unknowns
8. Action waves
9. Coverage and confidence
10. Next decision

For the task flow and realistic repository variations, see
[Assess a repository and turn evidence into action](../how-to/assess-a-repository.md).
