# Plan: Sealed-baseline replacement

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `docs/architecture/loop-infrastructure.md`,
  `packs/core/.apm/skills/work-loop/scripts/{loop-engine,loop-cohort,_loop_guards}.py`,
  `packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md`,
  and `packs/core/tests/skills/work-loop/`; analogous
  `docs/specs/loop-approved-spec-state/` and
  `docs/specs/work-loop-in-process-guards/`.

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; the approved baseline is immutable after sealing.

> **Rewritten 2026-08-30 with the spec amendment.** Five tasks became two. T1's
> completion ledger, T2's two extra source states and materiality enum, T3's
> `invalidate-baseline` verb, and T4's `resolve-vs-surface.py` helper were all
> cut: the first three already ship inside `contract-amendment`, and the fourth
> belongs to work-loop self-coverage. See the spec's
> [Removed from this contract](spec.md#removed-from-this-contract).

## Approach

Extend the shipped `contract-amendment` route rather than adding one beside it.
Two changes, in dependency order.

First, the drift crossing. The engine's plan-current guard currently refuses
before the amendment branch is reached. Give `contract-amendment` — and only it
— a crossing that requires observed spec and plan hashes plus an owner
confirmation bound to the run ID, then thread those observed hashes into the
existing `apply_contract_amendment` snapshot beside the sealed ones it already
records. No new event, state, cohort verb, or persistent structure: the
snapshot gains two fields and the transition gains three arguments.

Second, the shaping gate. Re-drafting after an amendment lands in
`SPEC-PLAN-DRAFTING`, which is driven in-loop rather than through `new-spec`,
so the gate `new-spec` gained in `shaping-review-contracts` does not cover it.
Add the gate to the work-loop's re-drafting sequence and to the lifecycle
reference that documents it.

## Constraints

- RFC-0099, including its 2026-08-27 and 2026-08-30 Errata, and RFC-0096's
  ordinary Paused semantics are normative.
- `loop-engine` remains the only `engine-state.json` writer; `loop-cohort`
  remains the only `state.json` writer. The engine delegates the cohort
  mutation and does not write cohort or artifact files itself.
- Existing locks, confined bounded reads, atomic writes, run identity, event
  recovery, retry caps, review history, and status parsers remain
  authoritative.
- `contract-amendment` is the sole plan-current-guard exception, and no
  observed hash becomes authoritative at any point.
- New state fields are additive and default safely for existing state; no
  destructive migration and no direct generated-projection edit.
- Direct-light, spec-plan-only mode, and current reviewer authority remain
  unchanged.

## Construction tests

**Integration tests:** real subprocess lifecycles enter the amendment from a
drifted plan under owner confirmation, refuse every incomplete binding, resume
through shaping review and both human gates, reseal, and schedule only
unfinished work. Crash injection covers the cohort-mutation boundary and
verifies the existing replay path still resumes without a second snapshot.

**Manual verification:** record one drifted-plan run end to end — engine and
cohort JSON before and after, artifact statuses, preserved history, human
gates, new hashes, remaining waves, and return to `CODE-IMPLEMENTATION`. Use
generic fixtures and redact repository and user details.

## Design (LLD)

### Data & schema

The `amendment_history` snapshot gains `observed_spec_hash` and
`observed_plan_hash`, populated only on a drift crossing and absent otherwise.
Existing readers ignore them; new readers default them to `None`. No other
state field changes. Traces to AC1, AC4.

### Interfaces & contracts

- Engine: `transition --event contract-amendment` gains
  `--observed-spec-hash`, `--observed-plan-hash`, and `--drift-mismatch
  spec|plan|both`. Supplying any one requires all three plus the existing
  `--owner-authority-ref`; supplying none preserves today's behaviour exactly.
  The plan-current guard is crossed only when all are present and the observed
  hashes match what the guard actually read. Traces to AC1, T1.
- Cohort: `apply_contract_amendment` gains two keyword-only observed-hash
  parameters, defaulted, recorded in the snapshot and nowhere else. Traces to
  AC1, T1.
- Work-loop: the re-drafting sequence gains shaping review ahead of adversarial
  review, and `references/delivery-contract-lifecycle.md` states it. Traces to
  AC2, T2.

### State & control flow

Unchanged from what ships: the engine validates, mutates the cohort, then
writes engine state last, so a crash always leaves the cohort ahead and the
existing replay branch recovers it. The drift crossing is a guard decision made
before that sequence begins and adds no new window. Traces to AC1, AC3.

### Failure, edge cases & resilience

A partial binding, a hash that does not match what the guard read, a mismatch
value outside the closed set, or a confirmation bound to another run refuses
with a stable diagnostic and no write. The replay branch's existing
plan-still-matches check is what prevents a drift crossing from laundering an
edited completed-task section into the baseline; keep it ahead of the cohort
mutation. Traces to AC1, AC3.

### Quality attributes (NFRs)

Recovery stays deterministic and fail-closed; the mutation stays idempotent per
amendment identity; history stays bounded and sanitized — observed hashes are
fixed-width digests, not content. No operation widens the existing lock hold or
filesystem authority. Traces to AC3, AC4.

## Tasks

### T1: A drifted pinned artifact crosses the guard under owner confirmation

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/{loop-engine,loop-cohort,_loop_guards}.py, packs/core/.apm/skills/work-loop/references/state-schema.md, packs/core/tests/skills/work-loop/{test_loop_engine,test_loop_cohort,test_loop_concurrency}.py`

**Tests:**
- `stub: true` — `packs/core/tests/skills/work-loop/test_baseline_replacement_contract.py` (`STUB: AC1`).
  Created at EXECUTE start, not carried on `main`: a red stub cannot land in a
  merged PR, so the first implementation commit adds it. It asserts the
  observed-hash arguments and the snapshot parameters this task introduces, and
  a fourth case that guards the shipped route and passes from the outset.
- TDD: the crossing succeeds only with all three drift arguments plus owner
  authority; each omission, a hash mismatching what the guard read, a
  `--drift-mismatch` value outside `spec|plan|both`, and a confirmation bound to
  another run each refuse byte-identically (AC1).
- TDD: the snapshot records both observed hashes beside the sealed ones, and no
  resealed baseline ever adopts an observed hash (AC1).
- TDD: with no drift arguments, every existing amendment path behaves exactly as
  before — legality, idempotency, history fields, preservation (AC3).
- TDD: a crash between the cohort mutation and the engine-state write still
  resumes through the existing replay branch, and that branch's
  plan-still-matches check still runs ahead of the mutation (AC3).

**Approach:**
- Add the crossing at the guard registration site; do not add an FSM entry, a
  state, or a cohort verb.
- Thread two defaulted keyword-only parameters into
  `apply_contract_amendment` and record them in the snapshot only.

**Done when:** a drifted plan reaches `SPEC-PLAN-DRAFTING` under a complete
owner confirmation, every incomplete binding refuses without a write, and the
non-drift path is byte-identical to today.

### T2: Re-drafting enters shaping review, and the docs match

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md, packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md, docs/architecture/loop-infrastructure.md, packs/core/{pack.toml,.claude-plugin/plugin.json}, docs/product/changelog.md, packs/core/tests/skills/work-loop/**, packs/core/tests/pack/**`

**Tests:**
- `stub: true` — `packs/core/tests/skills/work-loop/test_baseline_replacement_contract.py` (`STUB: AC2`, `STUB: AC3`), added by T1.
- TDD/integration: one real code-mode amendment run reaches `plan-locked` only
  after shaping review, adversarial review, and both human approvals; a shaping
  `Clean` recorded against the prior baseline does not satisfy the gate (AC2).
- Goal-based: the lifecycle reference, `SKILL.md` resumption guidance, the
  state-schema reference, architecture, and CLI help describe the same evidence
  fields, refusals, and gate order (`no stub (goal-based)`) (AC2, AC4).
- Goal-based: spec-status lint, Core evals, catalogue lint and verify, version
  parity, changelog, and self-host and build projections are clean (AC4).
- Security/quality: review the guard crossing, concurrency, recovery, and
  history retention against the current diff.

**Approach:**
- Insert the gate into the existing re-drafting sequence; add no reviewer and no
  new gate machinery.
- Bump Core once for the combined change and regenerate owned projections.

**Done when:** AC1–AC4 and all full-mode gates are green with no unresolved
recovery or security finding.

## Rollout

Ship the crossing, the gate, and their tests in one Core release. Existing state
files remain readable through absent-field defaults. Rollback returns to the
prior pack only before a drift crossing is recorded; after use, the new version
remains the supported recovery reader because older work-loop cannot interpret
the observed-hash fields.

## Risks

- A drift crossing could launder an edited completed-task section into the
  baseline. The replay branch's existing plan-still-matches check is the
  control; T1 must keep it ahead of the cohort mutation and test that ordering
  directly rather than assuming it.
- Owner confirmation could decay into a rubber stamp. The binding to run ID and
  to both observed hashes is what makes a stale or copied confirmation refuse.
- Adding a gate to the re-drafting sequence could deadlock an amendment when the
  reviewer is unavailable. The gate follows the existing missing-reviewer rule:
  a mandatory reviewer's absence blocks and is recorded, never skipped silently.
- Two observed-hash fields could grow unbounded history. They are fixed-width
  digests; the existing state-size ceiling still applies.

## Changelog

- 2026-08-27: initial plan from accepted RFC-0099; chose one existing-state
  transition plus an idempotent cohort verb, and declined reset, a second state
  machine, a nonmaterial shortcut, and guessed completion.
- 2026-08-30: rewritten with the spec amendment. Five tasks became two after
  `shaping-reviewer` found the contract scoped against a repository state that
  no longer exists; `contract-amendment` already ships the route the original
  plan proposed to build.
