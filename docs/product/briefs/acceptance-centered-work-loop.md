# Brief: Make acceptance criteria the center of a runtime-neutral work loop

- **Slug:** `acceptance-centered-work-loop`
- **Received:** 2026-09-30
- **Owner:** Platform Core
- **Status:** Executing
- **Cut-closed:** <!-- Set only after the final slice cut and its evidence are confirmed. -->
- **Source / provenance:** Repository architecture set rooted at [`docs/architecture/acceptance-centered-work-loop.md`](../../architecture/acceptance-centered-work-loop.md), including its authority-migration and runtime-crosswalk children, at content revision `sha256-set-v1:0ca1b837a37254fdf6279e18f4ed01c6ff96ea8fd1d207b8c780e6aa4d994d02`. The amended set received a `SHIP IT` architecture review, the refreshed brief received its independent shaping review, and the owner explicitly confirmed this Ready transition on 2026-10-01.
- **Executing from 2026-10-03.** `acceptance-authority-and-evidence` moved to `Implementing`, and a `Ready` brief cannot have a child carrying execution evidence. The Ready confirmation above stands as the record of that gate; this line records the transition off it.

## Outcome

Maintainers use one acceptance-centered work loop whose completion can be
rehydrated from approved criteria, Git history, evidence, review facts, and
explicit decisions. Runtime adapters may vary in sophistication, but they
cannot change delivery meaning; tasks, phases, cohorts, workspaces, and journals
remain replaceable means rather than competing sources of truth.

One initial plan review confirms strategy, safety constraints, dependencies,
and scope alignment against a derived execution envelope, and explicitly
authorizes terminal intent. The envelope fingerprints separately authorized
criteria and evidence policy, scope and non-goals, security and authority
decisions, public contracts, durable outputs, and accepted risk. Tasks can
change without reapproval while that fingerprint and terminal intent stay
fixed. A protected change routes to its owner and requires fresh initial review
before execution resumes.

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
- Reordering, splitting, replacing, or changing the local method of plan tasks
  inside the reviewed envelope requires no approval, preserves integrated
  history and fresh evidence, and cancels only unintegrated predecessor work.
- The public `work-loop` invocation remains stable while each slice passes its
  stated parity, recovery, and reversal proof before authority moves.
- A synthetic reviewer integrates without adding reviewer-specific work-loop
  logic, and a mandatory obligation is satisfied only by a current typed report
  and complete finding disposition.
- A supported review finding contributes contradictory evidence to each
  affected criterion; accepting risk can close the review obligation but
  cannot make a false acceptance property true.
- Knowledge tooling can be absent or unavailable without changing delivery
  readiness; a pull scan reproduces every eligible observation from durable
  facts.
- A separately installed Pi extension can execute the repository through the
  neutral protocol while Core imports, bundles, installs, and selects no Pi
  runtime; removing Pi changes no default work-loop behavior.
- Journal loss around an unknown external effect never causes an automatic
  repeat; a durable named-human resolution is required before reconstruction,
  stop, or one explicitly authorized retry.
- Parallel and sequential executions yield the same product tree and acceptance
  verdict, while unproven isolation falls back to sequential execution.
- The legacy workflow engine can be removed after cache-deletion rehydration,
  reversal, and engine-removal rehearsals pass.

## Scope / Non-goals

**In scope:**

- Acceptance criteria as stable property identities, with approval-bound
  evidence policies and a verdict derived from durable facts.
- One initial plan review plus mutable working-plan and task projections that
  can change without approval inside the reviewed execution envelope.
- A derived execution-envelope contract that binds task projection to current
  approved semantic, safety, contract, output, and risk facts without
  becoming a new approval authority.
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
- Pi as an optional external compatibility target, with proven isolation as
  the only basis for infrastructure parallelism regardless of runtime.
- Staged migration, reverse readers, parity checks, and final legacy removal.
- Explicit governance supersession before current FSM, cohort, approval, or
  parallelism authorities move.

**Non-goals:**

- Replacing the `work-loop` skill as the public adoption surface.
- Making Pi, `agentbundle`, a daemon, an always-on service, or parallel
  execution mandatory at runtime.
- Importing, bundling, installing, or selecting Pi from the Core work-loop or
  putting Pi compatibility on the supervisor, parallelism, or cutover critical
  path.
- Standardizing reviewer prompts, models, internal checklists, or retry logic.
- Making tasks, plans, gates, phases, cohorts, journals, or stored verdicts the
  authority for delivery completion.
- Requiring approval for in-envelope task order, decomposition, replacement,
  test shape, or local implementation method changes after initial review.
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

Pi remains optional at runtime, but Slice 6's compatibility proof is part of
this brief's outcome. It may ship independently after the neutral supervisor
protocol exists; Slices 7 and 8 neither depend on Pi nor require that proof.

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
  canonicalized with exact parity and imported atomically as one authoritative
  spec-policy decision plus an initial-plan review that grants no continuing
  authority to task content or methods.
- **Risk:** Acceptance, evidence, review, and content-safety contracts could
  recreate the old state machine under new names. Each stored record therefore
  needs an independent semantic reason to survive rehydration.
- **Risk:** A bundled supervisor can become a mandatory platform runtime in
  practice. The clean-environment import fence and sequential provider contract
  must prove that installation remains skill-first and runtime-neutral.
- **Risk:** An optional Pi conformance path can become a hidden dependency.
  Clean Core environments, dependency inspection, and default-selection tests
  must pass with Pi absent.
- **Risk:** Mutable tasks can smuggle a semantic or safety change past review.
  The replan guard compares the current derived envelope fingerprint with the
  one bound by initial review, separately checks its authorized terminal intent,
  and refuses a change or unresolved authority reference before projection.
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
  materialize task-local TDD bytes without current scratch proof. Slice 4 must
  make terminal intent, task revision, byte identity, and red-before-green
  ordering enforceable contracts without making test shape human-approved.
- **Risk:** A knowledge record can enter through Git without intake validation.
  Slice 3 retains close-time `work-item` capture and adds read-side quarantine
  without giving delivery any knowledge lifecycle state.
- **Risk:** Implementation can appear to supersede accepted FSM, cohort, or
  parallelism decisions. Each affected cutover refuses until its named
  superseding governance record is accepted.
- **Risk:** The three in-flight Draft specs began from the superseded brief.
  Each must reconcile against the amended architecture before approval; their
  current Draft content is not evidence that this brief is Ready.

## Rabbit holes

- Do not build another general workflow engine or encode
  `PLAN → EXECUTE → ESTABLISH SUPPORT → REVIEW → DECIDE` as stored phase
  authority. It is a query over durable facts.
- Do not replace whole-plan locking with approved plan revisions. Review the
  initial envelope once, then treat in-envelope tasks as mutable projections.
- Do not split semantic and mechanical concerns by sending all mechanics to an
  external tool. Keep the neutral supervisor contract and let adapters vary.
- Do not ship, import, install, or default-select Pi in Core. A Pi extension is
  an external consumer of the same neutral protocol as any other runtime.
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

## Architecture coverage

| Architecture owner | Brief obligation | Delivery slices |
| --- | --- | --- |
| [Parent architecture and order](../../architecture/acceptance-centered-work-loop.md) | Acceptance-centered outcome, initial-review/mutable-task boundary, eight-slice order, parity, reversal, and legacy removal | 1–8 |
| [Authority migration](../../architecture/work-loop-authority-migration.md) | Atomic legacy import, explicit governance before writer cutover, protected-boundary refusal, downgrade approval, and reverse readers | 1, 4, 7, 8 |
| [Acceptance and evidence](../../architecture/work-loop-acceptance-evidence.md) | Criteria and evidence policy own completion; a derived envelope binds separately approved protected facts; initial plan review does not pin tasks; evidence is fresh, admissible, and rehydratable | 1 |
| [Review and disposition](../../architecture/work-loop-review-disposition.md) | Opaque reviewer reports, actual-failure assessment, mandatory obligations, review-to-evidence contradiction, and risk-disposition separation | 2 |
| [Knowledge projection](../../architecture/work-loop-knowledge-handoff.md) | Stateless delivery projection, pull recovery, read quarantine, independent lifecycle, and retained explicit `work-item` capture | 3 |
| [Execution supervisor](../../architecture/work-loop-execution-supervisor.md) | Bundled sequential floor, mutable task projection, terminal/TDD guard, leases, recovery, unknown-effect resolution, and neutral extension protocol | 4, 6, 7 |
| [Product result integration](../../architecture/work-loop-result-integration.md) | Protected product ref, compare-and-swap, conflict/cancellation handling, provider parity, and crash recovery | 5 |
| [Runtime security primitives](../../architecture/runtime-security-primitives.md) | Capability intersection, filesystem/process confinement, containment refusal, effect brokering, audit, and control-plane denial | 1, 4, 7 |
| [Delivery content safety](../../architecture/delivery-content-safety.md) | Shared classification/redaction profiles and inert-data handling at every semantic boundary | 1 |
| [Runtime adapter crosswalk](../../architecture/runtime-adapter-crosswalk.md) | Sequential floor plus optional host mechanisms; Pi is reference-only compatibility and never a Core dependency | 4, 6, 7 |

## Proposed delivery slices

This table records the eight candidate spec boundaries and their dependency
order. It does not create or register child delivery artifacts.

| Slice and proposed spec slug | Independently shippable outcome | Hard predecessor | Exit proof |
| --- | --- | --- | --- |
| 1. `acceptance-authority-and-evidence` | Accepted criteria and evidence policy become durable authority; a derived envelope fingerprints every separately approved protected fact; the current approved pair imports atomically as one spec-policy decision plus an initial-plan review record that grants no continuing authority to task order, decomposition, test shape, or local method; shared security, subject, evidence, content-safety, and verdict services become callable without moving orchestration | none | Canonical digest and atomic-import parity, derived-envelope and mutation-classification truth tables, plan-task non-authority, subject/verdict parity, evidence recovery, capability intersection, confinement/refusal, control-plane denial, and content-safety conformance pass |
| 2. `structured-review-boundary` | Work-loop sees only selected obligations, current typed reviewer reports, actual-failure assessments, dispositions, and criterion-bound contradictory evidence for supported findings | Slice 1 | A synthetic reviewer integrates without work-loop changes; mandatory-obligation and finding truth tables pass; risk acceptance closes review without turning a contradicted criterion true |
| 3. `delivery-knowledge-projection` | A stateless fact feed and projector replace reusable capture gates; project-knowledge owns lifecycle and read quarantine while explicit close-time `work-item` capture remains | Slices 1–2 | Dropped notification recovers by pull scan; invalid merged records quarantine; unavailable knowledge tooling never changes readiness |
| 4. `execution-supervisor-inversion` | The bundled supervisor becomes procedure owner, preserves the legacy result boundary, reprojects in-envelope tasks without approval, refuses protected-boundary changes, enforces `spec-plan` no-dispatch and current-task red-before-green proof, and resolves unknown external effects durably | Slices 1–3 | Command, readiness, interruption, task-replan/cancellation, boundary-refusal, terminal-mode, byte-identity, red-before-green, journal-loss/effect-resolution, acknowledged-result, containment, and control-plane-forgery parity pass |
| 5. `canonical-result-integration` | Successful results advance a protected product ref through one compare-and-swap integration boundary, and the subject provider switches after parity | Slice 4 | Legacy and protected-ref providers yield the same manifest; sequential conflict and crash recovery pass |
| 6. `pi-runtime-compatibility` | A separately installed Pi extension consumes the neutral supervisor protocol behind the unchanged skill facade; Core contains no Pi dependency, bundled adapter, or default selection | Slice 4 | Shared sequential, recovery, authority, interruption, containment, and forgery suites pass from a Pi-hosted environment; clean Core dependency and default-selection checks pass with Pi absent |
| 7. `verified-infrastructure-parallelism` | After explicit ADR supersession, provider-neutral concurrency is admitted only with enforced read allowlisting or complete tracing and otherwise degrades to the sequential floor | Slice 5 | Missing governance or read coverage serializes; undeclared reads deny or expand the attested set; schedule permutations equal the sequential product tree and verdict with Pi absent |
| 8. `legacy-engine-cutover` | New semantic paths become authoritative and obsolete FSM/cohort writers, compatibility paths, and engine code are removed; optional Pi compatibility is not a prerequisite | Slices 1–5 and 7 | Parity, cache deletion, reverse-reader provenance, approved downgrade snapshot, full reversal, and engine-removal rehearsals pass in a clean environment with Pi absent |

Slice 1 owns the shared acceptance boundary even though its plan may span
several implementation tasks or pull requests. Slices 2 and 3 stay separate
because review facts can block acceptance while knowledge capture cannot.
Slices 4 and 5 stay separate so procedure ownership proves parity before the
canonical product authority changes.
Slice 6 proves that optional compatibility and does not gate parallelism or
legacy removal, although the brief cannot close until the compatibility outcome
also ships.

## Spec map

| Spec | Status |
| --- | --- |
| `acceptance-authority-and-evidence` | <auto> |
| `structured-review-boundary` | <auto> |
| `delivery-knowledge-projection` | <auto> |

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
