# Brief: spec drafting gets the same sequential authoring envelope

- **Slug:** `spec-author-agent`
- **Received:** 2026-09-03
- **Owner:** Repository maintainers
- **Status:** Draft
- **Source / provenance:** [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md)
- **Parent intent:** [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md)

## Outcome

On `claude-code` and `codex`, spec and plan drafting runs through a dispatched
`spec-author` agent instead of being authored in the primary session. The
`new-spec` and `work-loop` skills keep intake, lifecycle, independent review,
human approval, state, and registration authority.

This is capability 2 of the parent intent. It reuses the sequential envelope,
controller/actor boundary, host scope, policy precision rule, and AC discipline
defined by
[`universal-implementer-dispatch.md`](universal-implementer-dispatch.md). The
parent intent remains the authority for lifecycle placement and the shared
three-layer enforcement shape.

## Success metrics

- A construction test for each supported adapter proves that every in-scope
  drafting turn dispatches one `spec-author` with a bounded artifact and
  authority envelope.
- The author can create or revise only the named `spec.md` and `plan.md`. It
  cannot approve them, register workspace state, classify its own review, or
  advance the work-loop FSM.
- Standalone `new-spec` authoring and `SPEC-PLAN-DRAFTING` repair turns use the
  same agent contract rather than parallel authoring paths.
- Existing `shaping-reviewer`, `adversarial-reviewer`, human-gate, and
  adjudication boundaries remain independent of the author.
- The new agent projects and is invocable on `claude-code` and `codex`; no
  result is generalized to another host.

## Current-state evidence

- **[Measured]** Core ships exactly six agents:
  `adversarial-reviewer`, `finding-adjudicator`, `implementer`,
  `quality-engineer`, `security-reviewer`, and `shaping-reviewer`.

  ```bash
  rg --files --hidden packs/core/.apm/agents | wc -l
  # 6
  rg --files --hidden packs/core/.apm/agents | sort
  ```

- **[Measured]** No pack contains a spec-authoring agent. The bounded search
  was:

  ```bash
  rg -n --hidden -i -g '*/.apm/agents/*.md' 'spec[- ]author|author.*spec' packs
  # exit 1; no matches
  ```

- **[Measured]** `new-spec` is a skill that creates `spec.md` and `plan.md`;
  its current agent calls are review calls, including `shaping-reviewer` at
  line 488 and `adversarial-reviewer` at line 512 of
  [`new-spec/SKILL.md`](../../../packs/core/.apm/skills/new-spec/SKILL.md).
  No author-agent dispatch is defined there, so **[inferred]** drafting remains
  in the primary skill session.
- **[Measured]** The work-loop FSM names `SPEC-PLAN-DRAFTING`,
  `SPEC-PLAN-REVIEW`, and `SPEC-PLAN-APPROVED` in
  [`state-schema.md`](../../../packs/core/.apm/skills/work-loop/references/state-schema.md),
  line 92. Review already has dispatched reviewers and approval is a human
  gate, so **[inferred]** the missing acting envelope belongs to drafting turns,
  not to every phase bearing the prefix.
- **[Cited]** The absence and intended `spec-author` role are capability 2 in
  the parent intent's § "Decomposition". The underlying portability limits are
  in
  [`cross-model-steering-survey.md`](../research/cross-model-steering-survey.md).

## Scope / Non-goals

**In scope:**

- A core `spec-author` agent with a bounded create/revise artifact contract.
- Sequential dispatch from standalone `new-spec` authoring.
- Sequential dispatch for work-loop turns acting in
  `SPEC-PLAN-DRAFTING`, including revision after sustained review findings.
- Explicit separation between author output and controller-owned review,
  approval, workspace registration, and FSM transitions.
- Construction and projection coverage for `claude-code` and `codex` only.
- Updating the adopter guide that describes what happens during spec and plan
  authoring.

**Non-goals:**

- Changing spec or plan semantics, templates, acceptance criteria, review
  rubrics, approval gates, or the Ready definition.
- Making `spec-author` review, adjudicate, approve, register, execute, or
  close its own work.
- Re-enabling parallel fan-out or taking any Phase-2 orchestration decision.
- Implementing policy delivery, verdict validation, deterministic predicates,
  or the multi-adapter eval runner.
- Supporting or making compatibility claims for any host other than
  `claude-code` and `codex`.

## Constraints / Appetite

The appetite is two feature slices over one shared agent contract: first the
standalone authoring path, then work-loop drafting and repair. The shared
dispatch rules, rejection of hard per-criterion word budgets, AC-ceiling
semantics, precise-versus-advisory policy boundary, and 405-of-1,477
false-block measurement are inherited by citation from
[`universal-implementer-dispatch.md`](universal-implementer-dispatch.md) rather
than repeated here.

- The primary session remains the lifecycle controller and the only surface
  that can ask for human approval.
- The agent receives named files and bounded source context. It does not search
  for another feature to author or widen the accepted slice.
- An AC ceiling is a stall threshold, never a floor. Each slice may ship with
  fewer criteria.
- A hard per-criterion word budget is forbidden; semantic atomicity and
  testability remain the gate.

## The controller-to-author contract

Without these states an acceptance criterion cannot say what the author returns
or what the controller accepts, so the contract is stated here rather than left
to the spec.

| Element | Contract |
| --- | --- |
| Request | the confirmed slice context, the target `docs/specs/<slug>/` path, the phase-selected policy families, and the governing spec and plan templates |
| Permitted actions | write `spec.md` and `plan.md` under the named slug; read repository evidence; nothing else |
| Forbidden | registering work, mutating `workspace.toml`, initialising or advancing `loop-engine`, invoking a reviewer, or declaring completeness |
| Elicitation | the author cannot ask a human directly; an unresolved assumption is returned as a named `unresolved` item and the **controller** relays it |
| Return states | `drafted` with the two paths, `blocked` with the exact missing input, or `refused` with the reason |
| Continuity | a repair request carries the prior revision plus the sustained findings only, so the author never re-derives a settled decision |
| Controller validation | the controller verifies both files exist, carry the required metadata, and that every returned `unresolved` item is either answered or recorded, before any transition fires |
| Lifecycle ownership | the controller owns registration, status, and every FSM transition; the author owns only the two documents |

**The author never advances the loop.** That keeps `loop-engine`'s guard
enforcement in one place and matches how every existing dispatched agent in this
repository is bounded.

## Proposed slices

No slice is confirmed and no spec is authored. Each AC number below is a
ceiling and a stall threshold, not a required count.

| # | Slice | Primary owning surface | Verification | Guide | AC ceiling | Gating |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | Standalone `new-spec` dispatch through the new `spec-author` contract for both direct requests and confirmed delivery-brief slices | `packs/core/.apm/agents/spec-author.md` | Author write-boundary tests; reviewer-independence assertions; Claude Code and Codex agent projection and dispatch tests | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | 8 | after U1 defines the shared envelope contract |
| S2 | Work-loop `SPEC-PLAN-DRAFTING` and sustained-finding repair through the same `spec-author`, with FSM and human gates retained by the controller | `packs/core/.apm/skills/work-loop/SKILL.md` | Drafting-state dispatch and return tests; refusal outside drafting; proof that review, approval, registration, and state transitions remain controller-owned on both adapters | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | 8 | after S1 |

Both slices change adopter-visible authoring behavior, so they update the
existing end-to-end how-to rather than inventing a second guide.

**S1 owns every initial dispatch; S2 owns only repair.** The boundary is the
request kind, not the caller: S1 handles a create request from any caller,
including work-loop's first drafting entry, and S2 handles only a repair request
carrying sustained findings. An earlier reading split them by caller, which
overlapped at work-loop's initial drafting and left neither independently
bounded.

## Assumptions / Risks

- **[Inferred]** One `spec-author` contract can serve initial drafting and
  sustained-finding repair if the controller supplies the allowed operation,
  named artifact paths, and accepted finding set.
- Separating authoring from lifecycle control may lose context that currently
  sits in the primary session. The envelope must make missing context visible
  rather than letting the agent rediscover or invent it.
- The author may appear independent while receiving the controller's preferred
  solution. Independent review remains mandatory and must receive the authored
  artifacts, not the author's self-assessment.
- Adapter projection is already tested generically, but projection does not
  prove runtime dispatch or equivalent write boundaries.

## Ready gaps (Draft only)

- A revision-bound clean shaping review and the owner's explicit Ready
  confirmation have not happened.
- The exact `spec-author` write and tool boundary is not defined. No existing
  pack agent provides a spec-authoring precedent, as established by the
  pack-agent search in § "Current-state evidence". The slice spec must name
  the minimum files and actions the agent may perform.
- The controller-to-author handoff schema is not defined. It must distinguish
  initial create from repair, bind artifact paths, and carry only adjudicated
  findings on a repair turn.
- The ownership split for workspace registration and the transition from
  standalone `new-spec` into work-loop state needs one explicit contract. The
  current skill performs both authoring and lifecycle work. The bounded search
  for an author-agent dispatch was:

  ```bash
  rg -n -i 'spec-author agent|matching.*spec-author|dispatch.*spec-author' packs/core/.apm/skills/new-spec/SKILL.md packs/core/.apm/skills/work-loop/SKILL.md
  # exit 1; no matches
  ```

  S1 must settle where the author returns and the controller resumes.
- Runtime dispatch assertions for `claude-code` and `codex` do not yet exist
  for this role. The role itself is absent by the pack-agent search above;
  generic projection tests are insufficient. The slice specs must select
  construction-test seams before approval.

## Rabbit holes

- Giving `spec-author` approval, reviewer, adjudicator, workspace, or FSM
  authority because those operations currently sit near drafting in the skill.
- Creating separate agents for initial draft, plan draft, and repair before one
  bounded role has failed to serve them.
- Repeating the implementer brief's envelope and policy rules here instead of
  sharing them by reference.
- Claiming that a projected file proves the agent was invoked or obeyed.
- Extending the role to a third host without a later host-specific probe.

## Spec map

| Spec | Status |
| --- | --- |
|  |  |

## Provenance

- Product-strategy parent:
  [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md),
  capability 2 in § "Decomposition".
- Shared dispatch-envelope contract:
  [`universal-implementer-dispatch.md`](universal-implementer-dispatch.md).
- Research basis:
  [`cross-model-steering-survey.md`](../research/cross-model-steering-survey.md),
  [`behavior-controls-inventory.md`](../research/behavior-controls-inventory.md),
  [`agent-behavior-oracle-patterns-survey.md`](../research/agent-behavior-oracle-patterns-survey.md),
  and
  [`phase-scoped-policy-delivery.md`](../research/phase-scoped-policy-delivery.md).
