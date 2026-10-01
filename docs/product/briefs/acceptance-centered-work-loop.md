# Brief: Make acceptance criteria the center of a runtime-neutral work loop

- **Slug:** `acceptance-centered-work-loop`
- **Received:** 2026-09-30
- **Owner:** Platform Core
- **Status:** Draft
- **Cut-closed:** <!-- Set only after the final slice cut and its evidence are confirmed. -->
- **Source / provenance:** Repository architecture set rooted at [`docs/architecture/acceptance-centered-work-loop.md`](../../architecture/acceptance-centered-work-loop.md), including its authority-migration and runtime-crosswalk children, at Git revision `61624180b808f9adca70eab2ed2305adee645ce9`. That revision passed baseline compatibility review at its recorded pin and the repository design-reviewer with no findings.

## Outcome

Maintainers use one acceptance-centered work loop whose completion can be
rehydrated from approved criteria, Git history, evidence, review facts, and
explicit decisions. Runtime adapters may vary in sophistication, but they
cannot change delivery meaning; tasks, phases, cohorts, workspaces, and journals
remain replaceable means rather than competing sources of truth.

The existing `work-loop` skill remains the adoption surface. Its policy becomes
smaller as procedure moves into a bundled runtime-neutral supervisor,
verification becomes evidence for accepted properties, review becomes an
opaque typed boundary, security becomes infrastructure, and knowledge capture
becomes a separate lifecycle.

## Success metrics

- The same approved criteria and admissible facts produce the same acceptance
  verdict under the sequential reference runtime and every supported adapter.
- Deleting task projections, phase state, cohort state, or mechanical journals
  cannot change accepted scope, durable evidence, review facts, or the derived
  verdict.
- The public `work-loop` invocation remains stable while each slice passes its
  stated parity, recovery, and reversal proof before authority moves.
- A synthetic reviewer integrates without adding reviewer-specific work-loop
  logic, and a mandatory obligation is satisfied only by a current typed report
  and complete finding disposition.
- Knowledge tooling can be absent or unavailable without changing delivery
  readiness; a pull scan reproduces every eligible observation from durable
  facts.
- Pi can execute the repository through the neutral provider contract without
  becoming a required runtime.
- Parallel and sequential executions yield the same product tree and acceptance
  verdict, while unproven isolation falls back to sequential execution.
- The legacy workflow engine can be removed after cache-deletion rehydration,
  reversal, and engine-removal rehearsals pass.

## Scope / Non-goals

**In scope:**

- Acceptance criteria as stable property identities, with approval-bound
  evidence policies and a verdict derived from durable facts.
- Revisioned plan guidance whose tasks can be regenerated without changing
  accepted scope or erasing integrated history.
- A bundled service layer that the current engine can call before the same
  artifact becomes the procedure-owning execution supervisor.
- Shared capability, filesystem/process confinement, containment-refusal, and
  control-plane denial primitives before any supervisor or native provider
  cutover.
- Opaque reviewer selection, typed reports, actual-failure assessment, and
  finding disposition.
- Stateless projection of reusable observations into an independently owned
  knowledge lifecycle.
- Runtime-neutral execution, recovery, result integration, security
  capabilities, and a sequential capability floor.
- Pi as the first native execution provider and proven isolation as the only
  basis for infrastructure parallelism.
- Staged migration, reverse readers, parity checks, and final legacy removal.
- Explicit governance supersession before current FSM, cohort, approval, or
  parallelism authorities move.

**Non-goals:**

- Replacing the `work-loop` skill as the public adoption surface.
- Making Pi, `agentbundle`, a daemon, an always-on service, or parallel
  execution mandatory at runtime.
- Standardizing reviewer prompts, models, internal checklists, or retry logic.
- Making tasks, plans, gates, phases, cohorts, journals, or stored verdicts the
  authority for delivery completion.
- Giving delivery ownership of a knowledge queue, cursor, retry, admission,
  acknowledgement, skip log, retention, or revocation state.
- Treating tmux or a same-process adapter as a security boundary.
- Changing closeout ownership, repository-selected test frameworks, or the
  meaning of an accepted product criterion.

## Constraints / Appetite

This is an eight-slice migration, not a big-bang rewrite. Each slice must be
independently reviewable, reversible within its declared window, and leave the
current work-loop usable. A slice cannot assume the authority transfer owned by
a later slice, and shared contracts must deploy compatible readers before
writers.

The implementation cuts before adding: reuse the current skill facade, current
engine as a compatibility host, Git as durable product history, existing
repository safety primitives, and the self-contained script packaging pattern.
New mechanisms earn their place only when the current mechanism cannot satisfy
the slice's acceptance boundary.

## Assumptions / Risks

- **Assumption:** The current engine can call slice services before surrendering
  orchestration ownership. Slice 1 and slice 4 parity evidence must disconfirm
  this if the compatibility seam is not real.
- **Assumption:** The current approved spec and plan digests can be
  canonicalized with exact parity and imported atomically as separate
  spec-policy and plan-revision decisions without changing approved scope.
- **Risk:** Acceptance, evidence, review, and content-safety contracts could
  recreate the old state machine under new names. Each stored record therefore
  needs an independent semantic reason to survive rehydration.
- **Risk:** A bundled supervisor can become a mandatory platform runtime in
  practice. The clean-environment import fence and sequential provider contract
  must prove that installation remains skill-first and runtime-neutral.
- **Risk:** Moving result authority to a protected Git ref can lose work or
  accept ambient worktree drift. It remains a later slice with shadow parity,
  compare-and-swap, conflict, crash, and reversal evidence.
- **Risk:** Parallel execution can admit undeclared reads and produce a result
  that differs from sequential execution. Missing or incomplete read proof must
  serialize rather than degrade the invariant.
- **Risk:** Security or content-safety rules can drift into work-loop prose.
  Callers receive versioned capabilities and typed decisions; the primitive
  implementations remain outside delivery policy.
- **Risk:** Retiring the FSM can erase the `spec-plan` no-artifact boundary or
  materialize unapproved TDD bytes. Slice 4 must make terminal intent, scratch
  proof, byte identity, and red-before-green ordering enforceable contracts.
- **Risk:** A knowledge record can enter through Git without intake validation.
  Slice 3 retains close-time `work-item` capture and adds read-side quarantine
  without giving delivery any knowledge lifecycle state.
- **Risk:** Implementation can appear to supersede accepted FSM, cohort, or
  parallelism decisions. Each affected cutover refuses until its named
  superseding governance record is accepted.
- **Risk:** The architecture set is reviewed but still Draft. Human
  ratification and durable revision identity are required before this brief can
  become Ready.

## Rabbit holes

- Do not build another general workflow engine or encode
  `PLAN → EXECUTE → ESTABLISH SUPPORT → REVIEW → DECIDE` as stored phase
  authority. It is a query over durable facts.
- Do not split semantic and mechanical concerns by sending all mechanics to an
  external tool. Keep the neutral supervisor contract and let adapters vary.
- Do not move reviewer internals, finding taxonomies, or reviewer-specific
  orchestration into work-loop.
- Do not create delivery-owned knowledge handoff state. Durable delivery facts
  are the replay source; project-knowledge owns its lifecycle.
- Do not introduce protected-ref result authority during supervisor inversion.
  Prove the new procedure owner against the legacy result boundary first.
- Do not enable parallelism from declared write sets alone. Require enforced
  read allowlisting or a complete trace, otherwise serialize.
- Do not repeat filesystem-confinement algorithms in skills or loop prompts.
  Call the shared infrastructure primitive.

## Proposed delivery slices

This table records the eight candidate spec boundaries and their dependency
order. It does not create or register child delivery artifacts.

| Slice and proposed spec slug | Independently shippable outcome | Hard predecessor | Exit proof |
| --- | --- | --- | --- |
| 1. `acceptance-authority-and-evidence` | Accepted criteria, atomic import of approved spec-policy and plan-revision decisions, shared security primitives, legacy subject projection, evidence transactions, content safety, and a derived verdict become callable services without moving orchestration | none | Canonical digest and atomic-import parity, plan reprojection, subject/verdict parity, evidence recovery, capability intersection, confinement/refusal, control-plane denial, and content-safety conformance pass |
| 2. `structured-review-boundary` | Work-loop sees only selected obligations, current typed reviewer reports, actual-failure assessments, and dispositions | Slice 1 | A synthetic reviewer integrates without work-loop changes; mandatory-obligation and finding truth tables pass |
| 3. `delivery-knowledge-projection` | A stateless fact feed and projector replace reusable capture gates; project-knowledge owns lifecycle and read quarantine while explicit close-time `work-item` capture remains | Slices 1–2 | Dropped notification recovers by pull scan; invalid merged records quarantine; unavailable knowledge tooling never changes readiness |
| 4. `execution-supervisor-inversion` | The bundled supervisor becomes procedure owner, preserves the legacy result boundary, and enforces `spec-plan` no-dispatch plus approved TDD stub materialization | Slices 1–3 | Command, readiness, interruption, terminal-mode, byte-identity, red-before-green, acknowledged-result, containment, and control-plane-forgery parity pass |
| 5. `canonical-result-integration` | Successful results advance a protected product ref through one compare-and-swap integration boundary, and the subject provider switches after parity | Slice 4 | Legacy and protected-ref providers yield the same manifest; sequential conflict and crash recovery pass |
| 6. `pi-execution-provider` | Pi implements the neutral provider protocol behind the unchanged skill facade | Slice 5 | Shared sequential, recovery, authority, and interruption conformance suites pass through Pi |
| 7. `verified-infrastructure-parallelism` | After explicit ADR supersession, concurrency is admitted only with enforced read allowlisting or complete tracing and otherwise degrades to the sequential floor | Slices 5–6 | Missing governance or read coverage serializes; undeclared reads deny or expand the attested set; schedule permutations equal the sequential product tree and verdict |
| 8. `legacy-engine-cutover` | New semantic paths become authoritative and obsolete FSM/cohort writers, compatibility paths, and engine code are removed | Slices 1–7 | Parity, cache deletion, reverse-reader provenance, full reversal, and engine-removal rehearsals pass |

Slice 1 owns the shared acceptance boundary even though its plan may span
several implementation tasks or pull requests. Slices 2 and 3 stay separate
because review facts can block acceptance while knowledge capture cannot.
Slices 4 and 5 stay separate so procedure ownership proves parity before the
canonical product authority changes.

## Spec map

| Spec | Status |
| --- | --- |

## Design artifacts

- [Acceptance-centered work-loop architecture and implementation order](../../architecture/acceptance-centered-work-loop.md)
- [Authority and accepted-record migration](../../architecture/work-loop-authority-migration.md)
- [Acceptance and evidence](../../architecture/work-loop-acceptance-evidence.md)
- [Execution supervisor](../../architecture/work-loop-execution-supervisor.md)
- [Product result integration](../../architecture/work-loop-result-integration.md)
- [Review and disposition](../../architecture/work-loop-review-disposition.md)
- [Runtime security primitives](../../architecture/runtime-security-primitives.md)
- [Delivery content safety](../../architecture/delivery-content-safety.md)
- [Delivery-to-knowledge projection](../../architecture/work-loop-knowledge-handoff.md)
- [Runtime adapter crosswalk](../../architecture/runtime-adapter-crosswalk.md)
