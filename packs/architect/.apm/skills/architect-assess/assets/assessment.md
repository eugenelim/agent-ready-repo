# Architecture assessment: <target>

## Bottom line

<Decision-relevant conclusion, strongest evidence, material uncertainty, and
the next decision in no more than four short paragraphs.>

## Assessment charter

Target: <repository/system and boundary>
Primary intent: <one of six intents>
Secondary intents: <optional>
Mode: <survey | standard | deep>
Decision supported: <decision and stakeholder>
Permitted evidence: <reads/checks/private retrieval>
Excluded: <explicit non-scope>
Checkpoints: <confirmed | accepted-without-pause>

## Conceptual current state

<Context, deployable/runtime, module/capability, data, interaction,
delivery/operations, and trust/identity views. Label observed, inferred,
reported, and unknown.>

The three subsections below orient the reader first on the whole system, then
on each subsystem, then on the physical deployment. Each ends with a
`Sources checked` table. `Evidence class` takes one of `observed`, `inferred`,
`reported`, or `unknown`, defined in `references/evidence-method.md`
§ Claim calibration. A subsection that cannot be assessed begins with the line
`not assessed` followed by a reason and still ends with its table. A survey-mode
report uses that form for any subsection it did not reach.

### Overall architecture

<The system in one view: what it is, its major parts, and how they relate.>

Sources checked:

| Source | Locator | Evidence class | Limit |
| --- | --- | --- | --- |

### Architecture by subsystem

<One entry per subsystem: purpose, responsibility, key interfaces, and
dependencies.>

Sources checked:

| Source | Locator | Evidence class | Limit |
| --- | --- | --- | --- |

### Physical architecture

<Where each deployable runs: hosts, clusters, networks, stores, external
services, and the links between them. Without deployment evidence, write
`not assessed` and name what is missing; do not invent components.>

Sources checked:

| Source | Locator | Evidence class | Limit |
| --- | --- | --- | --- |

### Map checkpoint

<User correction or `continue`; resulting accepted boundary. On a host that
cannot pause, write `not user-confirmed`.>

## Evidence coverage

| Surface | Status | Evidence pointer | Confidence / limit |
| --- | --- | --- | --- |
| Documentation |  |  |  |
| Source |  |  |  |
| Tests |  |  |  |
| Manifests/dependencies |  |  |  |
| CI/CD |  |  |  |
| Deployment/release/IaC |  |  |  |
| Schemas/migrations |  |  |  |
| Runtime configuration |  |  |  |
| Operational evidence |  |  |  |
| Read-only history |  |  |  |

## Attention heat map

**Legend:** Heat selects drill-down priority. It is not proof of a defect and is
not finding severity. Each dimension is `low`, `medium`, `high`, or `unknown`.

| Area | Consequence | Pressure | Concentration / coupling | Verification weakness | Ops/data/security exposure | Confidence | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |

### Focus checkpoint

<User correction or `continue`; accepted hotspot set. On a host that cannot
pause, write `not user-confirmed`.>

## Hotspot drill-downs

### H-<n>: <area>

Architectural role: <responsibility and boundary>
Why it surfaced: <raw dimensions, not a score>
Signals and provenance: <target evidence pointers>
Counter-evidence: <strengths or alternative explanation>
Affected journeys/scenarios: <named path or quality scenario>
Unknowns: <uncovered evidence>
Drill-down: <bounded investigation performed or recommended>

## Findings, strengths, and unknowns

### F-<n>: <finding title>

Classification: <defect | risk | constraint | debt | opportunity | non-risk>
Stakeholder / scenario: <affected outcome or measurable scenario>
Scope: <bounded affected components and paths>
Evidence: <target evidence; enterprise context separately attributed>
Counter-evidence: <what argues against or narrows the finding>
Mechanism: <how the architecture produces the consequence>
Consequence: <why the mechanism matters>
Severity: <blocker | major | minor | advisory>
Confidence: <high | moderate | low, with reason>
Validation gap: <what would confirm or refute>
Smallest safe response: <contain, prove, decide, or change>

### Strengths and evidence-backed non-risks

<Mechanisms worth retaining, with evidence.>

### Material unknowns

<Unknowns that could change a decision or severity.>

## Action waves

### Wave <n> — <intended outcome>

Included findings: <F-IDs>
Prerequisites: <dependencies and decisions>
Completion proof: <observable evidence>
Rollback / containment: <safe reversal or temporary control>
Owner class: <team or role class, never invented personal ownership>
Non-goals: <work intentionally excluded>

## Coverage and confidence

| Lens / concept path | Status | Evidence pointer | Limitation |
| --- | --- | --- | --- |

Target evidence: <coverage statement>
Enterprise context: <surface/areas/authorization/attribution or none>
Pack knowledge: <selected, skipped, unavailable, stale, N/A paths>
Overall confidence: <calibrated statement, not an average score>

## Next decision

<One human decision, additional evidence request, or routed follow-up.>
