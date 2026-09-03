# Brief: every implementation task gets a sequential implementer envelope

- **Slug:** `universal-implementer-dispatch`
- **Received:** 2026-09-03
- **Owner:** Repository maintainers
- **Status:** Draft
- **Source / provenance:** [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md)
- **Parent intent:** [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md)

## Outcome

On `claude-code` and `codex`, every implementation task accepted by
`work-loop` runs through a dispatched `implementer` agent, including the normal
sequential path. The primary session keeps lifecycle, ordering, gates, review,
and recovery authority. Implementation procedure moves out of
`work-loop/SKILL.md`, leaving that skill as the controller rather than a second
implementation surface.

This brief supplies capability 1 of the parent intent. The parent owns the
lifecycle placement and the three-layer enforcement shape; this brief does not
restate either contract.

## Success metrics

- A construction test for each supported adapter proves the dispatch path is
  **wired**: the controller procedure names the projected agent, the task order
  is declared, and at most one implementer is authorised at a time.
- **Behavioural proof is not claimed here.** Whether a running agent actually
  invokes the projected implementer for every task is discretionary at runtime,
  and cross-adapter projection tests prove projection rather than honouring. The
  paired dispatch-versus-inline comparison in
  [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md)
  owns that claim. A construction test asserting runtime honouring would be a
  control with no seam to observe.
- The dispatched task carries the bounded task body, repository root, spec and
  plan paths when they exist, verification mode, and applicable execution
  context. Missing required context fails before the first implementation
  write.
- The main working tree and an explicitly supplied worktree are both valid
  execution roots. The agent never infers or creates either root.
- `work-loop` remains the sole owner of state transitions, task scheduling,
  final gates, review dispatch, retry decisions, and closeout.
- Implementation procedure has one normative home outside
  `work-loop/SKILL.md`. A deep skill lint reports the post-change body count,
  and the change does not add a second copy to compensate for extraction.
- The parent intent's paired `inline` versus `dispatched` eval can identify the
  selected adapter and delivery path. This capability does not claim improved
  adherence before that eval runs.

## Current-state evidence

- **[Measured]** `implementer` is reached only when a plan has multiple tasks
  declaring `Depends on: none`; that restriction is in
  [`implementer.md`](../../../packs/core/.apm/agents/implementer.md), line 3.
- **[Measured]** The only documented implementer dispatch is the parallel
  supervisor path, while `dispatch-decision`, `worktree`, and `auto-parallel`
  are disabled and exit non-zero in
  [`supervisor-mode.md`](../../../packs/core/.apm/skills/work-loop/references/supervisor-mode.md),
  lines 3–7 and 83–87. The same file states that Phase 1 runs tasks
  sequentially in topological order at lines 9–14.
- **[Measured]** The agent contract assumes a supervisor-created
  `.worktrees/<task-id>/` and forbids edits in the primary worktree in
  [`implementer.md`](../../../packs/core/.apm/agents/implementer.md), lines
  48–51. Admitting an explicitly supplied main working tree is the bounded
  agent-contract change.
- **[Cited]** ADR-0061 defers parallel-wave orchestration at line 28 and records
  the missing `pending_transition` schema at lines 30 and 47–49. Its erratum
  freezes the decision at line 69. Sequential single-agent dispatch uses no
  parallel worktree merge or collision decision, so **[inferred]** it needs no
  Phase-2 decision. See
  [`ADR-0061`](../../adr/0061-loop-infrastructure-phase-1.md).
- **[Measured]** `pending_transition` is absent from both the Phase-1 state
  schema and state asset. The bounded search was:

  ```bash
  rg -n 'pending_transition' packs/core/.apm/skills/work-loop/references/state-schema.md packs/core/.apm/skills/work-loop/assets/state.json
  # exit 1; no matches
  ```

- **[Measured]** `work-loop/SKILL.md` is 832 total lines:

  ```bash
  wc -l packs/core/.apm/skills/work-loop/SKILL.md
  # 832 packs/core/.apm/skills/work-loop/SKILL.md
  ```

  `CAT-S003` counts body lines, warns above 500, and errors above 1,000 in
  [`skill_spec_lint.py`](../../../packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py),
  lines 516–527. Moving implementation procedure out is therefore part of the
  outcome, even if other work is needed later to clear the warning threshold.
- **[Cited]** The compatibility and oracle limits remain those in
  [`cross-model-steering-survey.md`](../research/cross-model-steering-survey.md)
  and
  [`agent-behavior-oracle-patterns-survey.md`](../research/agent-behavior-oracle-patterns-survey.md).

## Scope / Non-goals

**In scope:**

- Sequential implementer dispatch for spec-backed `CODE-IMPLEMENTATION` tasks.
- Sequential implementer dispatch for direct-light implementation tasks, while
  retaining direct-light's session-local and spec-less boundary.
- The smallest change to `implementer.md` that accepts an explicit execution
  root in the primary working tree or an already-created worktree.
- Moving task implementation procedure out of `work-loop/SKILL.md` while
  keeping lifecycle and orchestration authority in the skill.
- Construction and projection coverage for `claude-code` and `codex` only.
- Updating the adopter guide that explains what happens during EXECUTE.

**Non-goals:**

- Re-enabling parallel fan-out, implementing Phase 2, adding
  `pending_transition`, creating or merging worktrees, or changing the
  collision gate.
- Changing task order, plan `Depends on:` semantics, retry caps, human gates,
  final gates, reviewer routing, or closeout.
- Adding the `spec-author` agent; capability 2 owns that envelope.
- Delivering policy selection, policy-arrival validation, verdict artifacts,
  deterministic policy predicates, or the multi-adapter eval runner.
- Supporting or making compatibility claims for Cursor, Copilot, Gemini, Kiro,
  or any other untested host.

## Constraints / Appetite

The appetite is the minimum two-slice change that makes dispatch universal on
the two named adapters and removes duplicate implementation procedure from the
controller. It is not an orchestration rewrite.

- Dispatch is sequential: one task, one bounded agent brief, one returned
  report, then the next task.
- Existing lifecycle and safety gates remain in the primary session. The
  implementer does not transition state, merge, review itself, or declare the
  overall loop complete.
- An acceptance-criterion count is a ceiling and stall threshold, never a
  floor. Fewer independently testable criteria are correct when they cover the
  slice.
- No hard per-criterion word budget may be proposed. That form is rejected by
  the Shipped criterion in
  [`shaping-review-contracts/spec.md`](../../specs/shaping-review-contracts/spec.md),
  line 230, by
  [`RFC-0099`](../../rfc/0099-cut-before-adding-and-artifact-shaping.md), line
  901, by `new-spec/SKILL.md`, line 505, and by
  [`agent-authoring-input-quality.md`](agent-authoring-input-quality.md) §
  "Sizing discipline".
- A policy family later carried by this envelope ships precise or advisory,
  never between those states. Precise predicates may block; stylistic
  predicates remain advisory. The parent records why: the tested stylistic
  predicate blocked 405 of 1,477 governed files, 27.4%, against a 0.4%
  per-family budget. This capability does not implement that policy layer.

## Proposed slices

No slice is confirmed and no spec is authored. Each AC number below is a
ceiling and a stall threshold, not a required count.

| # | Slice | Primary owning surface | Verification | Guide | AC ceiling | Gating |
| --- | --- | --- | --- | --- | --- | --- |
| U1 | Spec-backed sequential implementer dispatch, including the explicit-main-tree envelope and extraction of the spec-backed implementation procedure | `packs/core/.apm/skills/work-loop/SKILL.md` | Task-order and single-active-agent contract tests; `implementer` envelope assertions; Claude Code and Codex projection tests; deep skill lint with reported body count | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | 8 | none |
| U2 | Direct-light **policy-verdict** dispatch: the dispatched agent receives the phase-selected policy and returns a verdict; the primary session performs every write | `packs/core/.apm/skills/work-loop/SKILL.md` | Direct-light verdict-dispatch test on `claude-code` and `codex`; missing-context refusal; proof that no spec, plan, workspace entry, or loop state is created, and that the dispatched agent performs no write | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | 6 | after U1, D1's `DIRECT-LIGHT` selection, and V1's validation |

**U2's prerequisites are named, because the light path has no engine state.**
Selection comes from `phase-scoped-policy-delivery`'s reserved `DIRECT-LIGHT`
token in D1, and the verdict artifact is validated by
`policy-arrival-validator`'s V1, whose consumers include this path. U2 owns the
dispatch and the controller boundary only; it owns neither selection nor
validation.

**U2 dispatches a verdict, not a build, and that is what keeps direct-light
light.** Sending implementation to a second builder would mean "another builder
needs a contract they can read without this session", which is a risk trigger
that forces full mode and therefore a spec — contradicting the path's whole
purpose. Narrowing U2 so the dispatched agent only evaluates policy and returns
a verdict leaves the primary session as the sole builder, so the trigger does
not fire, no durable artifact is created, and the light path still receives
phase-scoped policy. This is why U2's owning surface is the controller rather
than the agent contract.

Both slices change adopter-visible workflow behavior, so both name the same
existing how-to guide. The guide should explain the universal dispatch result
once and preserve its current statement that parallel fan-out is disabled.

## Assumptions / Risks

- **[Inferred]** The parent's “every plan task” includes direct-light's
  session-local implementation task. `work-loop/SKILL.md` records a direct-light
  verification plan before EXECUTE but has no durable plan file; U2 keeps this
  interpretation visible for owner confirmation.
- **[Measured]** Both scoped adapters project pack agents:
  `test_adapter_claude_code.py` covers `.claude/agents/*.md`, and
  `test_adapter_codex.py` covers `.codex/agents/*.toml`. **[Inferred]**
  projection alone does not prove identical runtime dispatch behavior; the
  slices need adapter-specific execution-contract tests.
- **[Inferred]** A main-tree implementer can remain bounded if the controller
  supplies the resolved root and keeps all scheduling and state mutation.
  Ambiguous or missing roots must fail before edits.
- Dispatch adds context and latency to every task. The parent-owned paired eval
  may show no adherence gain; its predeclared kill condition remains decisive.
- Moving too little procedure leaves two normative implementation surfaces;
  moving lifecycle authority into the agent breaks recovery and auditability.

## Ready gaps (Draft only)

- A revision-bound clean shaping review and the owner's explicit Ready
  confirmation have not happened.
- **Settled — U2 is in scope** (owner decision, 2026-09-03). Direct-light skips
  `new-spec` and carries only a session-local task, so "every plan task" does
  not reach it by wording. It dispatches anyway: direct-light is the path small
  changes take, so excluding it would leave the most common changes with no
  phase-scoped policy, reproducing the gap this work exists to remove. U2 must
  keep its own ceremony minimal, because the light path exists to be light.
- **Owed at slice confirmation, not at Ready** — the exact extraction destination is unchosen. The spec must identify one
  existing or new file inside `work-loop/references/` or the agent contract,
  then prove that `SKILL.md` retains only routing and controller invariants.
  The bounded search for a current sequential-dispatch procedure was:

  ```bash
  rg -n 'sequential.*implementer|implementer.*sequential' packs/core/.apm/skills/work-loop packs/core/.apm/agents
  ```

  No existing normative sequential implementer procedure was found.
- **Owed at slice confirmation, not at Ready** — the runtime dispatch assertion shape for `claude-code` and `codex` is not yet
  selected. Existing adapter tests prove projection, not that every work-loop
  task invokes the projected agent once. The absence search was:

  ```bash
  rg -n 'implementer|dispatch' packages/agentbundle/tests/build_pipeline/test_adapter_claude_code.py packages/agentbundle/tests/build_pipeline/test_adapter_codex.py
  # exit 1; no matches
  ```

  The slice spec must name the construction-test seam before approval.
- **Owed at slice confirmation, not at Ready** — the main-tree report and commit contract is not yet settled. Current
  `implementer.md` requires the agent to commit inside a worktree, while the
  primary-session controller owns the shared checkout. The spec must decide
  who commits on the sequential path without expanding into parallel merge
  behavior.

## Rabbit holes

- Re-enabling any Phase-2 verb to obtain sequential dispatch.
- Treating a projected agent file as proof that the runtime dispatched it.
- Copying all of EXECUTE into a new reference while leaving the same procedure
  operative in `SKILL.md`.
- Letting the implementer own state transitions, final gates, review, or
  closeout because it now edits the primary working tree.
- Claiming support for a host outside `claude-code` and `codex` without a later
  host-specific probe.

## Spec map

| Spec | Status |
| --- | --- |
|  |  |

## Provenance

- Product-strategy parent:
  [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md),
  capability 1 in § "Decomposition".
- Research basis:
  [`cross-model-steering-survey.md`](../research/cross-model-steering-survey.md),
  [`behavior-controls-inventory.md`](../research/behavior-controls-inventory.md),
  [`agent-behavior-oracle-patterns-survey.md`](../research/agent-behavior-oracle-patterns-survey.md),
  and
  [`phase-scoped-policy-delivery.md`](../research/phase-scoped-policy-delivery.md).
