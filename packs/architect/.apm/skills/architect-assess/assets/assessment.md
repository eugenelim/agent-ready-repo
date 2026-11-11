# Architecture assessment: <target>

## Part 1: Summary

Read this part to know where the architecture stands, what to do first, and what decision is needed. It takes about two minutes.

### Bottom line

Verdict: <one sentence a sponsor can repeat: what state the architecture is in
for the decision supported>
Confidence: <high | moderate | low, and the one reason>
Working well: <the strongest mechanism worth keeping, in one line, with its evidence>
Main themes: <the two to four themes below, in a few words each>
Do first: <the top-ranked recommendation (R-1), in one line>
Decision needed: <the one human decision, and who owns it>

<Decision-relevant conclusion, strongest evidence, and material uncertainty in
no more than three short paragraphs. Name what was not assessed.>

### How to read this report

This report moves from conclusion to proof, in five parts. Each part opens with
what you can do after reading it. Read as far as your role needs.

- **Sponsors and decision makers:** Part 1 and Part 3.
- **Architects and engineering leads:** add Part 2 and Part 4.
- **Reviewers who want the proof:** add Part 5.

Terms used in this report. The definitions are fixed; they do not change from
one report to the next.

| Term | Meaning |
| --- | --- |
| Finding | A claim about the architecture, with its evidence, mechanism, and consequence. Numbered F-1, F-2, and so on. |
| Theme | A pattern shared by several findings. Themes tell you what the findings mean together. |
| Recommendation | A change or decision proposed to answer one or more findings. Numbered R-1, R-2, and so on, and ranked P1, P2, P3. |
| Wave | A group of recommendations that must be done together or in order. |
| Severity | How much harm a finding can do. `blocker` stops the decision or release. `major` needs action in the planning horizon. `minor` is worth fixing with other work. `advisory` is worth knowing. |
| Confidence | How well the evidence supports a claim. It is separate from severity: a severe finding can have low confidence. |
| Evidence class | How a source knows a fact. `observed`: seen directly. `inferred`: concluded from what was seen. `reported`: stated by a document or person, not checked. `unknown`: not established. |
| Heat | Where to look first. Heat picks the areas to examine. It is not proof of a defect and is not severity. |
| Priority | P1: do now; the risk is active or the work unblocks others. P2: do next. P3: plan or watch. |

## Part 2: What was assessed

Read this part to know what was assessed, what evidence was used, and how the system is built, so you can judge the rest.

### Assessment charter

Target: <repository/system and boundary>
Primary intent: <one of six intents>
Secondary intents: <optional>
Mode: <survey | standard | deep>
Decision supported: <decision and stakeholder>
Permitted evidence: <reads/checks/private retrieval>
Excluded: <explicit non-scope>
Checkpoints: <confirmed | accepted-without-pause>

### Conceptual current state

<Context, deployable/runtime, module/capability, data, interaction,
delivery/operations, and trust/identity views. Label observed, inferred,
reported, and unknown.>

The four views below orient the reader first on the whole system, then on each
subsystem, then on the technology and dependencies, then on the physical
deployment. Each ends with a
`Sources checked` table. `Evidence class` takes one of `observed`, `inferred`,
`reported`, or `unknown`, defined in `references/evidence-method.md`
§ Claim calibration. A view that cannot be assessed begins with the line
`not assessed` on its own, with the reason on the next line, and still ends with
its table.

#### Overall architecture

<The system in one view: what it is, its major parts, and how they relate.>

Sources checked:

| Source | Locator | Evidence class | Limit |
| --- | --- | --- | --- |

#### Architecture by subsystem

<One entry per subsystem: purpose, responsibility, key interfaces, and
dependencies.>

Sources checked:

| Source | Locator | Evidence class | Limit |
| --- | --- | --- | --- |

#### Technology and dependencies

<Languages and runtime versions, build and package tooling, direct dependencies
and whether they are pinned, end-of-life or unmaintained packages, and licences.
Take every version from a manifest or lock file; never from memory. Without a
lock file or dependency graph, write `not assessed` on its own line for the
dependency inventory, then name what is missing.>

Sources checked:

| Source | Locator | Evidence class | Limit |
| --- | --- | --- | --- |

#### Physical architecture

<Where each deployable runs: hosts, clusters, networks, stores, external
services, and the links between them. Without deployment evidence, write
`not assessed` on its own line, then name what is missing; do not invent
components.>

Sources checked:

| Source | Locator | Evidence class | Limit |
| --- | --- | --- | --- |

#### Map checkpoint

<User correction or `continue`; resulting accepted boundary. On a host that
cannot pause, write `not user-confirmed`.>

## Part 3: What matters and what to do

Read this part to see the patterns behind the findings, the ranked actions, and the decision you are asked to make.

### Key themes

<Two to four themes. Each is a full-sentence claim that the findings support
together, not a topic label. Order by importance to the decision supported.>

#### T-<n>: <theme as a claim>

Findings: <F-IDs>
Why it matters: <the stakeholder outcome at stake, in plain words>
Worth keeping: <the strength or non-risk that bounds this theme>
Addressed by: <R-IDs from Prioritized recommendations>

### Prioritized recommendations

<One or two sentences on how the list is ranked: consequence first, then
whether the item unblocks others, then effort, and sorted P1 first. Every recommendation traces to a
finding, and every P1 and P2 finding has a recommendation.>

| ID | Priority | Recommendation | Why now | Addresses | Effort | Wave |
| --- | --- | --- | --- | --- | --- | --- |
| R-1 | P1 | <verb-first action> | <consequence or dependency> | <F-IDs, T-ID> | <S / M / L, with the unit> | <wave number> |

### Action waves

<How the recommendations are sequenced, in one sentence.>

#### Wave <n> — <intended outcome>

Included recommendations: <R-IDs>
Included findings: <F-IDs>
Prerequisites: <dependencies and decisions>
Completion proof: <observable evidence>
Rollback / containment: <safe reversal or temporary control>
Owner class: <team or role class, never invented personal ownership>
Indicative horizon: <optional estimate, objective-based ("before first client connection") or time-based ("1-2 weeks"); omit if unknown>
Non-goals: <work intentionally excluded>

### Next decision

<One human decision, additional evidence request, or routed follow-up.>

## Part 4: Findings in detail

Read this part to check any claim: what was seen, why it matters, how sure we are, and the smallest safe response.

### Findings by area

Every area gets a row, so a reader looking for one finds it. `none found` means
the area was assessed and no finding met the bar. `not assessed` means no
evidence was read for it.

| Area | Status | Findings | Worth keeping | Limit |
| --- | --- | --- | --- | --- |
| Architecture and boundaries | <assessed / partly assessed / not assessed> | <F-IDs or none found> | <strength, or none> | <what stops a stronger statement> |
| Technology and dependencies |  |  |  |  |
| Code quality and testing |  |  |  |  |
| Delivery, security and governance |  |  |  |  |
| Data and contracts |  |  |  |  |
| Documentation and agent readiness |  |  |  |  |

### Findings

Each finding states a claim, how it was established, how sure we are, and the smallest safe response.

#### F-<n>: <finding stated as a claim>

Classification: <defect | risk | constraint | debt | opportunity | non-risk>
Severity: <blocker | major | minor | advisory>
Confidence: <high | moderate | low, with reason>
Theme: <T-ID>
Area: <one of the six areas in Findings by area>
Stakeholder / scenario: <affected outcome or measurable scenario>
Scope: <bounded affected components and paths>
Evidence: <target evidence; enterprise context separately attributed>
Counter-evidence: <what argues against or narrows the finding>
Mechanism: <how the architecture produces the consequence>
Consequence: <why the mechanism matters>
Validation gap: <what would confirm or refute>
Smallest safe response: <contain, prove, decide, or change>

### Strengths and evidence-backed non-risks

<Mechanisms worth retaining, with evidence.>

### Material unknowns

<Unknowns that could change a decision or severity.>

## Part 5: Evidence and method

Read this part to check how the work was done and where its limits are. Its sections start closed.

### Evidence coverage

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

### Attention heat map

**Legend:** Heat selects drill-down priority. It is not proof of a defect and is
not finding severity. Each dimension is `low`, `medium`, `high`, or `unknown`.

| Area | Consequence | Pressure | Concentration / coupling | Verification weakness | Ops/data/security exposure | Confidence | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |

#### Focus checkpoint

<User correction or `continue`; accepted hotspot set. On a host that cannot
pause, write `not user-confirmed`.>

### Hotspot drill-downs

#### H-<n>: <area>

Architectural role: <responsibility and boundary>
Why it surfaced: <raw dimensions, not a score>
Signals and provenance: <target evidence pointers>
Counter-evidence: <strengths or alternative explanation>
Affected journeys/scenarios: <named path or quality scenario>
Unknowns: <uncovered evidence>
Drill-down: <bounded investigation performed or recommended>

### Coverage and confidence

| Lens / concept path | Status | Evidence pointer | Limitation |
| --- | --- | --- | --- |

Target evidence: <coverage statement>
Enterprise context: <surface/areas/authorization/attribution or none>
Pack knowledge: <selected, skipped, unavailable, stale, N/A paths>
Overall confidence: <calibrated statement, not an average score>
