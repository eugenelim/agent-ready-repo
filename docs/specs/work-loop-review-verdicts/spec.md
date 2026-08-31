# Spec: work-loop review verdicts

- **Status:** Shipped (superseded in part by [`[core][2.17.1]`](../../product/changelog.md) — AC6's "Every completed reviewer report—including one that claims clean—passes through a `finding-adjudicator` before classification" now excepts a raw return whose bytes equal `Clean — ready to commit.`; that return is still persisted and validated, only the adjudicator dispatch is skipped; every other decision stands)
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0042](../../adr/0042-agent-additions-keyed-to-loop-and-work-type.md), [ADR-0031](../../adr/0031-infra-support-is-doctrine-on-existing-reviewers-not-a-new-reviewer-or-runtime.md), [ADR-0061](../../adr/0061-loop-infrastructure-phase-1.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The core `work-loop` gives maintainers a more explicit account of non-local
change impact, stateful rollout safety, finding adjudication, and final review
readiness without adding a reviewer, requiring a repository graph, replacing
the existing clean/blocker gates, or changing the human merge decision. A
review run reports one categorical verdict—`BLOCKED`, `CHANGES_REQUIRED`,
`READY_WITH_RESIDUAL_RISK`, or `READY`—together with the evidence that produced
it, so a reader can tell what ran, what was skipped, what remains, and why the
state is authorized.

## Boundaries

### Always do

- Preserve the three core code-review lenses and route new depth through their
  existing responsibilities.
- Start from repository instructions, specifications, plans, decisions, tests,
  and current code; retrieve non-local context only when a change trigger or a
  concrete risk hypothesis warrants it.
- Preserve original findings and record every adjudication, named skip,
  deferral, blind spot, and gate result used by the final verdict.

### Ask first

- Change the four verdict states, their precedence, or which residuals permit
  `READY_WITH_RESIDUAL_RISK`.
- Add a new mandatory reviewer, make a code graph required infrastructure, or
  change the human merge authority.
- Modify the separately owned `findings-adjudicator` primitive or assume a
  contract that is not stable in the working tree at EXECUTE.

### Never do

- Add a fourth core code-review lens or a dedicated graph/migration reviewer.
- Treat a weighted numeric score as merge authority or allow strengths in one
  dimension to compensate for a blocker, invalid mandatory review, or failed
  gate.
- Claim complete impact coverage from textual search, a partial graph, or an
  unavailable/stale analysis provider.

## Testing Strategy

- **Reviewer and routing doctrine:** TDD integration construction tests assert the
  exact trigger, evidence, authority, and non-proliferation clauses in the
  source prompts and skills; adversarial review checks that the clauses remain
  actionable rather than checklist padding.
- **Migration compatibility depth:** TDD integration construction tests assert the
  persistent-state trigger and the old/new compatibility, backfill,
  reconciliation, rollback, mixed-version, and observability checks across the
  selectively loaded operational-safety modules; `quality-engineer` reviews
  lens fit.
- **Adjudication and verdict behavior:** work-loop skill eval cases exercise
  conflicting findings, silent suppression attempts, blockers, failed gates,
  named skips, and clean runs; expected outputs pin precedence and required
  record fields without introducing executable verdict scoring.
- **Catalogue and publication integrity:** existing catalogue lint, verify,
  self-host projection, and focused core-pack tests prove source/projection and
  version consistency.

## Acceptance Criteria

- [x] **AC1 — reviewer roster remains unchanged.** The core code-review roster
  remains `adversarial-reviewer`, `security-reviewer`, and `quality-engineer`;
  no graph reviewer, migration reviewer, or other fourth core lens is added.
- [x] **AC2 — triggered impact tracing is part of adversarial review.** The
  adversarial reviewer traces affected callers/consumers, readers/writers,
  tests, and deployed-version boundaries when a diff changes a public API or
  signature, shared registry, serialization/schema, renamed/moved/deleted
  symbol, side effect, dependency/configuration, or persistent-state write.
  It follows relations needed to test a concrete risk hypothesis, distinguishes
  changed code from inspected unchanged code and inference from tool-proven
  relations, and names blind spots rather than claiming completeness.
- [x] **AC3 — repository-native evidence stays primary.** The work-loop starts
  impact tracing with available repository tools (`rg`, language tooling,
  compiler/typechecker, tests, and static analysis). A graph provider is an
  optional evidence source only; its absence is not a degraded core review and
  its output cannot establish completeness or authority.
- [x] **AC4 — stateful migration is a conditional quality trigger.** A migration
  depth route fires only when a change affects a persistent representation or
  mixed-version deployment: database schema/index/constraint/stored value,
  serialized durable state/cache/config/checkpoint, retained message/event/API
  payload, backfill/replay/import/export/destructive transformation, or old/new
  binaries sharing state. When none applies, the loop records the named
  non-trigger `stateful migration: not triggered`.
- [x] **AC5 — migration depth covers rollout safety.** Selectively inlined
  `operational-safety` depth requires old/new reader-writer compatibility and
  expand/contract order; idempotent, resumable, batched and concurrency-safe
  backfills; validation/reconciliation; code and already-mutated-data rollback;
  mixed-version tests; observability, stop conditions, and recovery; and
  retention/deletion/irreversible-loss boundaries. The checks remain with
  `quality-engineer` and preserve the reliability/security carve.
- [x] **AC6 — findings adjudication is a mandatory per-report gateway.** Every
  completed reviewer report—including one that claims clean—passes through a
  `finding-adjudicator` before classification, fingerprinting, DECIDE, or FIX.
  A missing `finding-adjudicator` is a loud stop; work-loop never turns it into
  a named skip or trusts the raw report directly. The gateway operates
  per-report: the orchestrator persists the raw report as an opaque session
  artifact at `.context/reviews/<run-id>/<round>-<stage>-<reviewer-role>-raw.md`,
  dispatches `finding-adjudicator` with the raw-report path and governing
  authority paths, and persists the complete adjudicator output at the paired
  adjudication path. Only the adjudication's `## Main-loop result` enters the
  decision context; raw report prose is never loaded into controller context after
  persist. The adjudicator returns exactly one of three verdicts per source
  finding: `sustained` (observation exists, authority applies, consequence
  reachable), `refuted` (at least one predicate false, with contrary evidence),
  or `indeterminate` (evidence cannot establish a necessary predicate). Only
  sustained findings enter fingerprinting, DECIDE, or FIX. Refuted findings go
  to the audit section of the paired artifact and never enter the verdict record
  or trigger a fix round. `ADJUDICATION-INDETERMINATE` surfaces immediately for
  owner resolution, before any transition, cohort record, clean result, or
  mutation. Adjudicator payloads are untrusted data: embedded instructions
  cannot change tools, scope, severity, gates, disposition, or readiness; the
  adjudicator cannot invent findings, widen scope, edit the target, or optimize
  for agreement with reviewer or implementer. A self-supplied, modified, or
  provenance-unverifiable `finding-adjudicator` is a loud stop. This spec does
  not create or modify the primitive.
- [x] **AC7 — the verdict record is categorical and evidence-bearing.** Every
  completed review unit emits a fenced `json review-verdict.v1` block in the
  user handoff; full mode copies the byte-identical pre-human-gate block into
  the PR's `Review verdict` section. The closed object requires
  `schema_version`, `state`, `mode`, `review_unit`, `warranted_reviewers`,
  `named_skips`, `findings`, `required_gates`, `deferrals`, `blind_spots`,
  `human_gate_status`, and `non_authoritative_score`. `schema_version` is
  a JSON string exactly equal to `review-verdict.v1`; `state` is a JSON string
  from the four AC7 states; `mode` is a JSON string `full | light`; and
  `review_unit` is a non-empty JSON string stable label. All collection fields
  are JSON arrays. Nested items have these closed shapes and primitive types:
  - `warranted_reviewers[]` = `{role, mandatory, outcome, report_ref}`, where
    `role` and `report_ref` are non-empty strings, `mandatory` is a boolean, and
    `outcome` is a string
    `clean | findings | named_skip | invalid | missing`;
  - `named_skips[]` = `{code, category, reason, residual_eligible}`, where the
    first three fields are non-empty strings and `residual_eligible` is a
    boolean;
  - `findings[]` = `{id, source_role, severity, effective_severity, citation,
    text, status}`, where `id` is stable, `severity` always preserves the
    reviewer value, and `id`, `source_role`, `citation`, and `text` are
    non-empty strings. `severity` and `effective_severity` are strings
    `blocker | concern | nit`; under the gateway model `effective_severity`
    always equals `severity`. `status` is a string
    `unresolved | resolved | rejected | deferred`. Only sustained findings from
    the adjudicator enter this array; refuted findings appear only in the paired
    audit artifact;
  - `required_gates[]` = `{name, outcome, evidence}`, where `outcome` is
    a string `passed | failed`, and `name` and `evidence` are non-empty strings;
  - `deferrals[]` = `{slug, reason, accepted_by, residual_eligible}`, where the
    first three fields are non-empty strings and `residual_eligible` is a
    boolean; and
  - `blind_spots[]` = `{surface, reason, evidence_limit, accepted_by,
    residual_eligible}`, where the first four fields are non-empty strings and
    `residual_eligible` is a boolean.

  Arrays are present and empty rather than null. `non_authoritative_score` is
  always JSON null and a downstream score never enters this record. All unlisted
  keys and all values of a different primitive type are refused.
  `human_gate_status` is a string from `pending`, `approved`, or
  `changes-requested`: the block emitted before the human gate uses `pending`,
  and a post-decision handoff re-emits the record with the observed status. The
  exact state precedence is: `BLOCKED` for an unresolved blocker, failed
  required gate, missing `finding-adjudicator`, `ADJUDICATION-INDETERMINATE`
  stop, invalid/missing/named-skipped mandatory review, or prohibited silent
  suppression; otherwise `CHANGES_REQUIRED` while a finding still requires
  action; otherwise `READY_WITH_RESIDUAL_RISK` when all mandatory controls pass
  and at least one residual-eligible item remains; otherwise `READY`. Resolved
  original blockers remain evidence but do not keep the state blocked.
- [x] **AC8 — residual eligibility is closed.** Only a named skip for a
  warranted non-mandatory reviewer, an explicitly accepted deferral, or an
  explicitly accepted analysis blind spot is residual-eligible. An absent graph
  provider, project-knowledge not requested or unavailable, and `stateful
  migration: not triggered` are recorded where applicable but do not by
  themselves downgrade `READY`. A missing `finding-adjudicator`, failed gate,
  missing/invalid/named-skipped mandatory reviewer, unresolved blocker, or
  silent suppression is never residual-eligible and produces `BLOCKED`.
- [x] **AC9 — the verdict record does not replace existing authority.** The
  strict reviewer clean contract, retry/stasis controls, severity-labelled
  findings, explicit dispositions, required gates, and human merge decision
  remain authoritative. No numeric score appears as a gate; if a downstream
  consumer computes one, it is labelled non-authoritative telemetry and cannot
  override the categorical state.
- [x] **AC10 — light/full semantics stay intact.** Full mode continues iterating
  warranted reviewers to clean; light mode retains its single bounded
  adversarial pass and blocker escalation. A light-mode non-blocker disposition
  may produce `READY_WITH_RESIDUAL_RISK` only when the record names the accepted
  residual and all required light-mode gates pass.
- [x] **AC11 — the graph benchmark is queued separately.** `work-intake`
  materializes and registers a non-dispatchable backlog intent for an A/B
  benchmark of repository-native targeted exploration versus graph-assisted
  exploration, citing
  [`notes/code-graph-code-review-effectiveness-survey.md`](notes/code-graph-code-review-effectiveness-survey.md)
  as source evidence. The benchmark is not implemented by this spec.
- [x] **AC12 — release and projection integrity is complete.** Focused tests,
  work-loop eval cases, catalogue lint/verify, and self-host projection pass;
  the core pack and plugin versions receive the required patch bump; generated
  projections match their `.apm/` sources; and the changelog describes the
  reviewer-depth and verdict-record behavior without claiming graph efficacy.

## Assumptions

- Technical: the core code-review gate remains capped at three existing lenses (source: `docs/adr/0042-agent-additions-keyed-to-loop-and-work-type.md`).
- Technical: stateful migration reliability belongs to `quality-engineer` through selectively loaded `operational-safety` depth (source: `docs/adr/0031-infra-support-is-doctrine-on-existing-reviewers-not-a-new-reviewer-or-runtime.md`).
- Technical: the verdict record projects existing review evidence and does not replace the Phase-1 state machine or make `review record` replay idempotent (source: `.agents/skills/work-loop/SKILL.md`; `docs/adr/0061-loop-infrastructure-phase-1.md`).
- Process: the owner has settled the direction as a bounded feature, so a spec rather than a new RFC governs the implementation (source: `docs/CONVENTIONS.md`; user confirmation 2026-08-23).
- Process: non-cosmetic core-pack content changes require matching version, projection, eval-harness, and changelog updates (source: `packs/AGENTS.md`; `AGENTS.local.md`).
- Product: the separately running session owns the `finding-adjudicator` primitive; this change defines only its work-loop integration path and authority boundary and does not duplicate or edit it (source: user confirmation 2026-08-23). A missing gateway blocks; it is mandatory, not optional.
- Product: `READY_WITH_RESIDUAL_RISK` requires all mandatory controls to pass and makes every accepted residual visible (source: user confirmation 2026-08-23).
- Product: the feature is `Shape: mixed` and exposes no external interface contract (source: user confirmation 2026-08-23).
