# Architecture assessment report rubric

Review the supplied report as a decision artifact. Do not rescan the repository,
run the profiler, execute checks, or repair missing evidence. A citation may be
opened only to verify that it supports the claim it is attached to; it does not
authorize expanding assessment scope.

## Scope fidelity

- [ ] The target, boundary, primary intent, mode, decision, permissions,
      exclusions, and stopping depth match the accepted charter.
- [ ] The conclusion does not generalize from an assessed component to an
      unassessed repository, runtime, store, tenant, or operating environment.
- [ ] Survey output stops at hypotheses and recommended drill-downs rather than
      presenting completed findings or remediation as established.

**Typical severity:** blocker when the conclusion addresses a materially
different system or decision; major for consequential scope overclaim.

## Evidence strength and provenance

- [ ] Documentation, source, tests, manifests, CI/CD, deployment/release/IaC,
      schemas/migrations, runtime configuration, operational evidence, and
      read-only history have explicit coverage states.
- [ ] Material observations have inspectable locators and distinguish observed,
      inferred, reported, and unknown claims.
- [ ] Target evidence, enterprise context, and pack knowledge remain separately
      attributed; generic knowledge is never cited as proof of target behavior.
- [ ] Missing, stale, denied, sensitive, single-source, or contradictory
      evidence visibly lowers the affected confidence.

**Typical severity:** blocker when invented or misattributed evidence supports a
safety/readiness conclusion; major when the report cannot substantiate a
load-bearing finding.

## Current-state model coherence

- [ ] The model distinguishes repositories, deployables, runtimes, components,
      data stores, external systems, interactions, and trust/identity boundaries.
- [ ] Folders are not equated with architecture components without behavioral
      evidence.
- [ ] Important views agree with each other and the evidence ledger; inferred
      boundaries and unknown dependencies are marked.
- [ ] The report retains the Map checkpoint correction or explicitly records
      acceptance.

## Attention heat and hotspot selection

- [ ] Consequence, pressure, concentration/coupling, verification weakness,
      operational/data/security exposure, and confidence remain separately
      inspectable.
- [ ] Heat is used only to select investigation priority; it is not called risk,
      severity, a defect, or an architecture score.
- [ ] Each hotspot gives role, raw signals, provenance, counter-evidence,
      affected journeys/scenarios, unknowns, and a bounded drill-down.
- [ ] The report retains the Focus checkpoint correction or acceptance.

**Typical severity:** major when heat is the sole basis for findings or action;
minor when the legend or one raw dimension is missing but traceability survives.

## Lens and scenario completeness

- [ ] The base lens and every triggered system-shape, workload, quality, and
      enterprise-context lens has `assessed`, `partially assessed`, `not
      assessed`, or `not applicable` plus evidence.
- [ ] Representative happy, high-risk mutation/side-effect, and
      failure/recovery paths are traced when present.
- [ ] Agentic/knowledge readiness does not skip material run-lifecycle,
      identity, model, tool, credential, knowledge, memory, evaluation, or trace
      boundaries.
- [ ] An uncovered lens narrows the conclusion rather than disappearing from the
      report.

## Findings, calibration, and alternative explanations

- [ ] Every finding traces observation → mechanism → consequence for an affected
      stakeholder or measurable quality scenario.
- [ ] Scope, counter-evidence, plausible alternative explanations, confidence,
      validation gap, and smallest safe response are explicit.
- [ ] Severity expresses consequence; confidence expresses evidence strength.
      The two are not averaged or substituted.
- [ ] Strengths and evidence-backed non-risks remain visible and are not erased
      to manufacture a transformation backlog.
- [ ] A standards, dependency, typing, file-size, folder, or code-smell signal is
      not an architecture finding without a traced mechanism and consequence.

## Action traceability and sequencing

- [ ] Every action wave names intended outcome, included finding IDs,
      prerequisites, completion proof, rollback/containment, owner class, and
      non-goals.
- [ ] Active defects are contained and proven before generalized gates; safety
      controls precede broad modernization unless a contrary dependency is
      evidenced.
- [ ] Actions fit the primary intent: hardening, current-outcome optimization,
      growth preparation, transformation, and disposition are not collapsed
      into one generic cleanup backlog.
- [ ] No action exists only because a heat dimension, corpus pattern, or generic
      best practice was present.

**Typical severity:** major when an action plan cannot trace to findings or
completion proof; blocker when the ordering would knowingly leave an active
unsafe defect live or create an irreversible migration without containment.

## Verdict calibration

Use the existing verdict and severity vocabulary. `SHIP IT` means the report is
safe to use for its stated decision, not that the assessed architecture is
defect-free. `WRONG ARTIFACT` applies when the supplied document cannot answer
the requested decision—for example, a backend compliance audit presented as a
whole-platform modernization assessment.
