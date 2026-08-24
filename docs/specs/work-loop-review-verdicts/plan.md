# Plan: work-loop review verdicts

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document may change while its status is `Drafting` or `Executing`.

## Approach

Extend the existing reviewer and progressive-depth surfaces rather than adding
roles or analysis infrastructure. First pin construction tests for the new
prompt and skill contracts. Then add impact tracing to the adversarial reviewer,
route persistent-state changes to expanded operational-safety depth for the
quality reviewer, define the optional adjudication handoff and exact verdict
record in `work-loop`, and add work-loop skill eval cases for precedence. Finally,
queue the graph benchmark through `work-intake`, bump and project the core pack,
and run the catalogue gates.

The verdict is a strict structured output contract in work-loop doctrine, not a
weighted scorer and not a new cohort/FSM mutation. This avoids changing the
Phase-1 crash semantics while still giving humans and downstream consumers an
exact, machine-readable record. The riskiest point is the concurrent
`findings-adjudicator` work: implementation reads the working tree immediately
before editing and binds only to a stable exposed contract; otherwise it ships
the named-unavailable branch without touching that primitive.

## Constraints

- ADR-0042 preserves the three-lens core review ceiling.
- ADR-0031 routes operational reliability through `quality-engineer` and
  progressive operational-safety depth, not a new reviewer.
- ADR-0061 keeps Phase-1 cohort/FSM side-effect and crash-recovery semantics;
  this change does not alter or replay `review record`.
- The evidence survey supports adaptive targeted retrieval, not mandatory graph
  construction; graph efficacy remains an experiment.
- `.apm/` is source; self-hosted adapter outputs are projections.
- The other session owns `findings-adjudicator`; overlapping edits are refused.

## Construction tests

**Integration tests:** focused core-pack construction tests assert that the
adversarial prompt, work-loop doctrine, operational-safety router/modules, and
quality-reviewer consumer agree on triggers and authority. Work-loop eval cases
exercise end-to-end reasoning for verdict precedence and adjudication failure.

**Manual verification:** inspect the projected work-loop, reviewer prompts, and
operational-safety references after self-hosting; inspect the queued benchmark
intent and canonical workspace status; inspect a sample structured verdict for
each of the four states.

## Design (LLD)

### Design decisions

- Extend existing lenses, not roster: AC1–AC6.
- Use adaptive impact tracing with optional graph evidence: AC2–AC3.
- Use a closed categorical verdict record, not weights: AC7–AC10.
- Keep the graph benchmark a separate non-dispatchable intent: AC11.

### Component / module decomposition

- `adversarial-reviewer.md` owns non-local correctness impact tracing.
- `operational-safety/SKILL.md` owns persistent-state trigger routing;
  `state-and-idempotency`, `drift-and-rollback`, and
  `observability-and-smoke` own the migration checks.
- `quality-engineer.md` remains the consumer of inlined migration depth.
- `work-loop/SKILL.md` owns adjudication sequencing, verdict precedence, record
  fields, light/full interpretation, and human-gate authority.
- `work-loop/evals/evals.json` and focused pack tests pin those contracts.

### State & control flow

```text
reviewers produce immutable findings
        ↓
optional findings-adjudicator (stable contract only)
        ↓ preserves originals + records outcome/rationale
work-loop intent-fit disposition
        ↓
required gates and reviewer conditions
        ↓
categorical verdict record
        ↓
existing human gate decides merge
```

No edge mutates reviewer prose in place. No verdict state advances the existing
cohort or engine state machine.

### Behavior & rules

- Verdict precedence is fail-closed and non-compensating: `BLOCKED` dominates
  `CHANGES_REQUIRED`, which dominates either ready state.
- `READY_WITH_RESIDUAL_RISK` is a transparency state, not a weaker way to pass a
  blocker.
- Adjudication changes the recorded disposition of a finding only with
  preserved source, rationale, and provenance; it cannot redefine gate policy.

### Failure, edge cases & resilience

- Missing/unstable adjudicator contract → named unavailable branch.
- Missing graph provider → normal repository-native tracing, not degraded core
  review.
- Dynamic dispatch, generation, reflection, runtime configuration, databases,
  and cross-service edges → named blind spots where tools cannot prove them.
- Invalid or incomplete mandatory review, failed gate, or silent suppression →
  `BLOCKED`.

### Quality attributes (NFRs)

- Portability: all doctrine remains tool-neutral; tool names are examples of
  available repository-native evidence.
- Auditability: original findings and all transformations remain visible.
- Maintainability: trigger and precedence definitions each have one canonical
  home and projections are generated.

### Dependencies & integration

- Optional integration only when exactly one discoverable primitive declares
  `findings-adjudication.v1` with the input/output fields in AC6. Missing,
  duplicate, malformed, differently versioned, or conflicting surfaces select
  the named-unavailable branch.
- Optional graph evidence provider; never required.

## Tasks

### T1: Reviewer-depth construction tests fail before doctrine changes

**Depends on:** none

**Touches:** `packs/core/tests/pack/`

**Mode:** TDD, integration construction test.

**Artifact / stub:** `packs/core/tests/pack/test_review_depth_and_verdict_contract.py`
starts with failing assertions for the canonical `.apm/` sources.

**Tests:**
- Integration construction tests fail until AC1–AC6 trigger, provenance,
  authority, migration, and no-new-reviewer clauses exist at their canonical
  source locations.
- Tests assert concepts and exact closed-state tokens without mirroring whole
  paragraphs.

**Approach:**
- Add one focused test module that reads canonical `.apm/` sources and asserts
  the cross-file reviewer-depth contract.

**Done when:** the focused test fails for the intended missing clauses and no
unrelated test changes are required.

### T2: Adversarial review traces non-local impact

**Depends on:** T1

**Touches:** `packs/core/.apm/agents/adversarial-reviewer.md`

**Mode:** TDD, integration construction test from T1.

**Artifact / stub:** `test_review_depth_and_verdict_contract.py` impact-trace
assertions; no additional stub.

**Tests:**
- The T1 impact-trigger, evidence-provenance, optional-provider, and blind-spot
  assertions pass (AC1–AC3).

**Approach:**
- Add a compact implementation-stage impact-trace check keyed to the seven
  change shapes in AC2.
- Require hypothesis-driven traversal and evidence provenance; explicitly
  reject completeness claims from partial search/graph evidence.

**Done when:** the reviewer can distinguish when impact tracing fires, what it
must inspect, and what it may not claim.

### T3: Quality review receives persistent-state migration depth

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/operational-safety/SKILL.md`, `packs/core/.apm/skills/operational-safety/references/state-and-idempotency.md`, `packs/core/.apm/skills/operational-safety/references/drift-and-rollback.md`, `packs/core/.apm/skills/operational-safety/references/observability-and-smoke.md`, `packs/core/.apm/agents/quality-engineer.md`

**Mode:** TDD, integration construction test from T1.

**Artifact / stub:** `test_review_depth_and_verdict_contract.py` migration-route
and module assertions; no additional stub.

**Tests:**
- T1 assertions cover every AC4 trigger and every AC5 compatibility/backfill,
  validation, rollback, mixed-version, observability, and loss-boundary check.
- Tests confirm the route loads only matching modules and preserves the
  reliability/security carve.

**Approach:**
- Broaden the existing `stateful migration` routing entry into an explicit
  persistent-state compatibility trigger.
- Place write-path/backfill checks in `state-and-idempotency`, divergence and
  data-rollback checks in `drift-and-rollback`, and rollout telemetry/recovery
  checks in `observability-and-smoke`.
- Add only the minimal consumer cue to `quality-engineer`; do not duplicate the
  module content in its prompt.

**Done when:** a stateful rollout receives the full focused checklist and an
ordinary stateless code change records the named non-trigger.

### T4: Work-loop defines adjudication and categorical verdict records

**Depends on:** T2, T3

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/evals/evals.json`

**Mode:** TDD for the closed work-loop text contract plus goal-based JSON/eval
shape checks.

**Artifact / stub:** `test_review_depth_and_verdict_contract.py` verdict and
authority assertions; new cases in `work-loop/evals/evals.json`; JSON syntax is
checked with `python3 -m json.tool`.

**Tests:**
- Add eval cases for a blocker plus high positive scores, an unresolved
  concern, accepted named residuals, a clean run, silent suppression, and an
  unavailable adjudicator (AC6–AC10).
- Add one case for each adjudication outcome (`upheld`, `refuted`, `duplicate`,
  `downgrade_recommended`, `uncertain`) asserting preserved original text and
  severity, the explicit-acceptance boundary, resulting `status` and
  `effective_severity`, and verdict-precedence effect (AC6).
- Construction tests assert the four exact states, fail-closed precedence,
  required record fields, non-authoritative score rule, and unchanged human
  gate.

**Approach:**
- Insert the optional adjudication step between immutable reviewer output and
  intent-fit disposition only when exactly one primitive declares
  `findings-adjudication.v1` and the complete AC6 fields. Any missing,
  duplicate, malformed, differently versioned, or concurrent-conflict case
  selects the named-unavailable branch; never edit that primitive.
- Define the closed `json review-verdict.v1` handoff/PR carrier, schema, null
  rules, residual eligibility, and state precedence in DECIDE; require it in
  the finish checklist and handoff.
- Keep all cohort/FSM commands and clean-report authority unchanged.

**Done when:** each eval scenario produces exactly one authorized categorical
state with its supporting evidence and no score can override precedence.

### T5: Code-graph benchmark is captured through work-intake

**Depends on:** none

**Touches:** `docs/product/intents/code-graph-review-benchmark.md`, `workspace.toml`

**Mode:** goal-based check; no test stub.

**Artifact / command:** the `work-intake` transaction result plus
`python3 .agents/skills/workspace-status/scripts/workspace_status.py explain
--root . --item code-graph-review-benchmark`.

**Tests:**
- The work-intake guard/router accepts a normalized `remember` envelope with
  repo-origin provenance and no sensitive content.
- Workspace status reports the resulting item as non-dispatchable backlog work.
- The intent cites the evidence survey and scopes the comparison to controlled
  A/B measurement, not graph adoption (AC11).

**Approach:**
- Use the public work-intake transaction path to materialize the minimal intent
  and register the canonical five-field workspace entry.

**Done when:** canonical workspace analysis shows the benchmark as remembered,
non-dispatchable work with no implementation processor.

### T6: Core release, projections, docs, and gates are consistent

**Depends on:** T2, T3, T4, T5

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`, the changelog-derived `/now/` projection, generated self-host projections

**Mode:** goal-based checks; no test stub.

**Artifact / commands:** focused `pytest`, `python3 -m json.tool`,
`make build-self`, catalogue lint/verify, and `git diff --check` exits.

**Tests:**
- Focused reviewer-depth tests and work-loop eval-schema validation pass.
- `make build-self`, catalogue lint/verify, and relevant core tests pass.
- Projection checks show generated adapters match `.apm/` sources.
- Version and changelog assertions pass (AC12).
- The released core-pack changelog entry contains a concise `Highlights`
  outcome and the generated `/now/` page publishes it.

**Approach:**
- Patch-bump core and matching plugin metadata, add a released changelog entry
  with a `/now/`-eligible `Highlights` outcome, run self-host and site
  projections, then run focused and repository gates.

**Done when:** all runnable required gates are green, environment-blocked gates
are explicitly deferred, regenerated projections match their `.apm/` sources,
and the diff contains no hand-edited generated drift or unrelated cleanup.

## Rollout

- **Delivery:** one reversible core-pack doctrine release; no runtime service,
  database, or external system changes.
- **Infrastructure:** none.
- **External-system integration:** optional adjudicator and graph providers are
  capability-detected; neither is required.
- **Deployment sequencing:** reviewer/migration sources and tests land before
  verdict doctrine; projection and version updates follow all source edits.

## Risks

- **Concurrent adjudicator work:** another session may edit overlapping work-loop
  integration points. Mitigation: inspect the live diff immediately before T4;
  do not overwrite or invent its contract; surface an overlap that cannot be
  reconciled safely.
- **Prompt bloat:** extra checklists can dilute findings. Mitigation: impact and
  migration depth are trigger-keyed and operational modules stay selectively
  loaded.
- **False completeness:** graphs and textual searches both miss dynamic edges.
  Mitigation: provenance and explicit blind spots are part of the verdict record.
- **Verdict-state confusion:** `READY_WITH_RESIDUAL_RISK` could become a softer
  pass. Mitigation: exact precedence, fail-closed tests, and unchanged human
  authority.
- **Projection drift:** self-hosted copies may diverge. Mitigation: edit `.apm/`
  only and run self-host plus catalogue verification.

## Changelog

- 2026-08-23: initial plan from the evidence survey and confirmed owner assumptions.
