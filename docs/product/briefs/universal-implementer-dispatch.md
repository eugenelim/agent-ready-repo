# Brief: every spec-backed implementation task gets a sequential implementer envelope

- **Slug:** `universal-implementer-dispatch`
- **Received:** 2026-09-03
- **Owner:** Repository maintainers
- **Status:** Ready
- **Source / provenance:** [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md)
- **Parent intent:** [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md)

## Outcome

On `claude-code` and `codex`, every **spec-backed** implementation task accepted
by `work-loop` runs through a dispatched `implementer` agent, including the
normal sequential path, whenever the projected `implementer` is installed. The
primary session keeps lifecycle, ordering, gates, review, and recovery
authority. Task-implementation procedure moves out of `work-loop/SKILL.md`,
apart from the bundled-fixes carve-out named in § "Constraints", leaving that
skill as the controller rather than a second implementation surface. **That
extraction is U3, not U1** — see § "Proposed slices" for why the two separated.

Direct-light is **not** an exception carved out of that sentence; it is a
different envelope. U2 dispatches a policy verdict, never a build, so
direct-light implementation stays inline in the primary session. § "Proposed
slices" gives the reason.

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
- **(U3)** The extracted task-implementation procedure has exactly one
  normative home, and extraction adds no second copy. The bundled-fixes
  carve-out is an explicit carve-out from this metric.
- **(U3)** The post-change deep-lint body count for `work-loop/SKILL.md` falls,
  measured against a baseline re-taken **after U1 lands**. The direction is the
  metric; no absolute threshold is claimed. U1 adds a dispatch declaration and
  therefore raises the count, so the 822 recorded below is U1's starting point,
  not U3's.
- The dispatch path emits a signal that distinguishes `inline` from
  `dispatched` and names the selected adapter, so the parent's paired eval has
  something to read. This capability does not claim improved adherence, and does
  not own the eval runner — that is a non-goal. Because direct-light
  implementation stays inline, the eval's population is the spec-backed path
  only; the parent's predeclared kill condition is read against that population,
  not against every task `work-loop` accepts.

## Current-state evidence

- **[Measured]** `implementer` is reached only when a plan has multiple tasks
  declaring `Depends on: none`; that restriction is in
  [`implementer.md`](../../../packs/core/.apm/agents/implementer.md), line 3.
- **[Measured]** The only documented implementer dispatch is the parallel
  supervisor path, while `dispatch-decision`, `worktree`, and `auto-parallel`
  are disabled and exit non-zero in
  [`supervisor-mode.md`](../../../packs/core/.apm/skills/work-loop/references/supervisor-mode.md),
  lines 3–7 and 83–87. The Phase-1 attribution for sequential execution is at
  lines 3–7 and 229–232; lines 9–14 state the unattributed default
  ("topological order, single-agent, on every adapter").
- **[Measured]** A sequential-execution procedure already has an owner, and it
  contradicts this outcome. `supervisor-mode.md` § "Phase 1 supervisor
  procedure" (lines 223–236) says "Execute sequentially" with no implementer
  dispatch, line 11 says tasks run **single-agent**, and § "Single-agent
  fallback" (lines 238–243) tells the controller to "execute the independent
  tasks yourself" when no `implementer`-matching subagent is installed. A fourth
  text surface repeats it:
  [`evals.json`](../../../packs/core/.apm/skills/work-loop/evals/evals.json)
  line 42 expects "Run tasks one at a time in wave order" and names no agent.
  U1 amends an existing owner; it does not design a new one.
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

- **[Measured]** `work-loop/SKILL.md` is 832 total lines and **822 body lines**
  — the body count is the one `CAT-S003` governs, and it is the pre-change
  baseline the success metric above compares against:

  ```bash
  wc -l packs/core/.apm/skills/work-loop/SKILL.md
  # 832 packs/core/.apm/skills/work-loop/SKILL.md

  PYTHONPATH=packages/agentbundle:packages/credbroker \
    python3 -m agentbundle catalogue lint --root . --deep
  # [CAT-S003] WARN packs/core/.apm/skills/work-loop/SKILL.md
  #   body exceeds 500 lines (got 822); the spec recommends staying under 500
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

- Sequential implementer dispatch for spec-backed `CODE-IMPLEMENTATION` **plan
  tasks** — the first pass over each task in the schedule.
- **Repair rounds stay inline.** `CODE-IMPLEMENTATION` has four re-entry edges
  in
  [`loop-engine.py`](../../../packs/core/.apm/skills/work-loop/scripts/loop-engine.py).
  Three carry repair work rather than a plan task and do **not** dispatch:
  `gates-failed` (line 550), `findings-remain` (552), and `blocker-applied`
  (554). The fourth, `wave-passed` (548), re-enters with the next wave's plan
  tasks and **does** dispatch. The existing rule already points this way:
  `supervisor-mode.md` lines 163–165 say "Do not redispatch the same implementer
  on the same task — the assumption that produced the failure is what needs
  revising, not the attempt." That sentence sits on the currently dormant
  parallel path, so it is corroboration rather than authority. "Universal"
  therefore means every plan task, once; it does not mean every entry into the
  state.
- Direct-light **policy-verdict** dispatch: the dispatched agent evaluates the
  phase-selected policy and returns a verdict, and the primary session remains
  the sole builder. Direct-light implementation is not dispatched, which is what
  keeps the path light and spec-less.
- The smallest change to `implementer.md` that accepts an explicit execution
  root in the primary working tree or an already-created worktree, **and**
  re-states the agent's own use condition at
  [`implementer.md`](../../../packs/core/.apm/agents/implementer.md) line 3
  ("Used by `work-loop` when a plan has multiple tasks declaring
  `Depends on: none`") so it no longer restricts the agent to the multi-task
  parallel case. This is a contract-consistency change, not a selection-
  mechanism change: [`catalogue-curation/spec.md`](../../specs/catalogue-curation/spec.md)
  line 91 records that "skills activate by description, **agents are dispatched
  by the loop**", so the field steers no automatic selection. It is still
  load-bearing, because leaving it unchanged ships an agent whose own contract
  restricts it to a case the controller no longer dispatches it for, and the
  controller and every human reader take the agent contract at its word.
- **(U3)** Moving task implementation procedure out of `work-loop/SKILL.md`
  while keeping lifecycle and orchestration authority in the skill.
- Construction and projection coverage for `claude-code` and `codex` only.
- Updating the adopter guide that explains what happens during EXECUTE.

**Non-goals:**

- Re-enabling parallel fan-out, implementing Phase 2, adding
  `pending_transition`, creating or merging worktrees, or changing the
  collision gate.
- Changing task order, plan `Depends on:` semantics, retry caps, human gates,
  final gates, reviewer routing, or closeout.
- Adding the `spec-author` agent; capability 2 owns that envelope.
- Delivering policy selection, policy-arrival validation, **durable** verdict
  artifacts and their validation (capability 4), deterministic policy
  predicates, or the multi-adapter eval runner. U2's dispatched agent returns a
  verdict as an in-session value; it creates no durable artifact.
- Supporting or making compatibility claims for Cursor, Copilot, Gemini, Kiro,
  or any other untested host.

## Constraints / Appetite

The appetite is **two near-term slices and one gated follow-on**. U1 makes
spec-backed dispatch universal on the two named adapters; U3 removes duplicate
implementation procedure from the controller. U2 is not near-term: it waits on
U1 plus three named slices — D1, V1, D3 — whose own closure reaches D2 and the
whole of capability 2, because
[`policy-arrival-validator.md`](policy-arrival-validator.md) line 166 gates V1
"after D2 emits the framed digest; end-to-end dispatch proof also waits on
capabilities 1 and 2". That is four slices across three briefs. This is not an
orchestration rewrite.

- Dispatch is sequential: one task, one bounded agent brief, one returned
  report, then the next task.
- Existing lifecycle and safety gates remain in the primary session. The
  implementer does not transition state, merge, review itself, or declare the
  overall loop complete.
- **"Universal" is bounded by installation.** It means every spec-backed task
  dispatches *whenever the projected `implementer` is installed*. The shipped
  escape hatch at
  [`supervisor-mode.md`](../../../packs/core/.apm/skills/work-loop/references/supervisor-mode.md)
  lines 238–243 is the honest bound, not a defect. The slice spec must state
  whether U1 retains, re-points, or deletes it; silently leaving it operative
  next to a "universal" claim is the failure mode.
- **The implementer holds no Git authority in the primary working tree.** It
  creates no branch and mutates no index or commit unless the slice spec
  explicitly grants it. The specific choice of who commits is owed at slice
  confirmation; this bound is not, because the Outcome claims recovery authority
  for the primary session.
- **Extraction must not orphan a mirror.** The bundled-fixes carve-out at
  `work-loop/SKILL.md` lines 417–429 is a marked canonical site with two
  pointers into it —
  [`implementer.md`](../../../packs/core/.apm/agents/implementer.md) lines 52–55
  and
  [`adversarial-reviewer.md`](../../../packs/core/.apm/agents/adversarial-reviewer.md)
  lines 197–200. Any extraction either leaves that block in `SKILL.md` or
  re-points all three sites in the same slice. Collapsing the three copies into
  one home is separate work and is not admitted here.
- No hard per-criterion word budget may be proposed. That form is rejected by
  the Shipped criterion in
  [`shaping-review-contracts/spec.md`](../../specs/shaping-review-contracts/spec.md),
  line 230, by
  [`RFC-0099`](../../rfc/0099-cut-before-adding-and-artifact-shaping.md), line
  901, by `new-spec/SKILL.md`, line 505, and by
  [`agent-authoring-input-quality.md`](agent-authoring-input-quality.md) §
  "Sizing discipline".
- A policy family later carried by this envelope ships precise or advisory,
  never between those states. The rule and its supporting measurement are owned
  by the parent's § "De-risk"; see
  [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md),
  lines 160–166. This capability does not implement that policy layer.

## Proposed slices

No slice is confirmed and no spec is authored. Each AC number below is a
**ceiling and a stall threshold, never a floor** — the single statement of that
rule for this brief. Fewer independently testable criteria are correct when
they cover the slice; reaching the ceiling triggers a split or an explicit
owner decision.

| # | Slice | Primary owning surface | Verification | Guide | AC ceiling | Gating |
| --- | --- | --- | --- | --- | --- | --- |
| U1 | Spec-backed sequential implementer dispatch: the declaration, the explicit-main-tree envelope, one commit owner per root, inlined craft delivery, and the contradiction sweep across the four surfaces that deny it | `packs/core/.apm/agents/implementer.md` | Dispatch-declaration and single-active-agent contract tests; `implementer` envelope assertions; contradiction-set negative and positive halves; Claude Code and Codex agent projection test | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | 11 (raised from 8 by owner decision 2026-09-03) | none |
| U3 | Extraction of task-implementation procedure from `work-loop/SKILL.md` into its own normative home | `packs/core/.apm/skills/work-loop/SKILL.md` | Sole-home assertion over a recorded extracted set; migrated anchor assertions; deep skill lint with reported body count | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | 8 | after U1 |
| U2 | Direct-light **policy-verdict** dispatch: the dispatched agent receives the phase-selected policy and returns a verdict; the primary session performs every write | `packs/core/.apm/skills/work-loop/SKILL.md` | Direct-light verdict-dispatch test on `claude-code` and `codex`; missing-context refusal; proof that no spec, plan, workspace entry, or loop state is created, and that the dispatched agent performs no write | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | 6 | after U1, D1's `DIRECT-LIGHT` selection, V1's validation, and D3's assembly (or U2's own, pending the amendment below) |

**U1 and U3 separated at slice confirmation, on measured evidence.** The
original cut bundled dispatch and extraction because both serve the "no second
normative implementation surface" half of the outcome. Authoring the U1 spec
found that six of the nine candidate statements cannot move, for independent
reasons: `verification-modes.md` and `infra-verification.md` each declare that
`SKILL.md` keeps their load-bearing one-liner; the contract-grounding statement
is a gate scoped "(universal — light and full)" and serves the inline
direct-light path; the TDD line is pinned by an ordered assertion in
`tests/roster/test_tdd_stub_lifecycle_contract.py`; the `notes/` routing names a
real documented artifact; and the frontend row is converted in place rather than
removed. What remains movable is roughly three lines. Extraction therefore needs
anchor-test migration, two reference-header reconciliations, and an owner
decision on moving a gate — a slice, not a task. U1 does not depend on it, and
neither do the sibling slices, which gate on the envelope.

**U2's prerequisites are named, because the light path has no engine state.**
Selection comes from `phase-scoped-policy-delivery`'s reserved `DIRECT-LIGHT`
token in D1; the verdict artifact is validated by `policy-arrival-validator`'s
V1; and the assembly that puts the selected policy *into* a dispatch brief is
D3. U2 owns the dispatch and the controller boundary only; it owns neither
selection, assembly, nor validation.

**D3's scope, as written, does not cover U2's case — that is a second owed
amendment.** `phase-scoped-policy-delivery.md` line 159 scopes D3 to "every
sequential **implementer** brief", verified by a fixture that "enters each
**implementation-bearing state**". Direct-light matches neither: U2's
dispatched agent is not an implementer, it returns a verdict and writes
nothing, and the light path creates no engine state at all — which is why D1
reserves a separate `DIRECT-LIGHT` token. So the sibling supplies selection for
the light path but no slice supplies assembly for a stateless verdict brief.
Before U2 is confirmed, either D3's scope must be widened to cover it, or U2
admits light-path assembly and this brief drops "assembly" from the sentence
above. Both options are open; neither is chosen here, and neither touches U1.

**U2 and D3 deadlock as both briefs are written today. This brief does not
resolve that unilaterally; it records the obligation.**
[`phase-scoped-policy-delivery.md`](phase-scoped-policy-delivery.md) gates D3
"after V1 and capability 1" at line 159 and repeats it at lines 204–206:
"D3 cannot name its final callable surface or end-to-end fixture until
`universal-implementer-dispatch` **lands**." That names this brief whole, and
U2 is part of it, so D3 waits on U2 while U2 waits on D3.

The substantive fix is narrow — D3 needs the *envelope*, which is U1's
deliverable, not U2's — and the precedent already exists:
[`spec-author-agent.md`](spec-author-agent.md) line 149 gates S1 "after **U1**
defines the shared envelope contract", referencing this brief at slice
granularity. But an edge recorded only on the consuming side is not resolved,
because D3's spec author reads the sibling, not this file.

**Reconciliation obligation, owed before U2 is confirmed and not before U1:**
`phase-scoped-policy-delivery.md` lines 159 and 204–206 must be amended from
"capability 1" to "U1", matching `spec-author-agent.md` line 149. That
amendment is owned by the sibling brief's owner. If they disagree, the parent
intent arbitrates; U2 stays unconfirmed until it is settled. U1 is unaffected —
nothing in U1 depends on D3.

**A third amendment is owed upward, to the parent.** Narrowing the eval
population to the spec-backed path (§ "Success metrics") also narrows the
antecedent of the parent's predeclared kill condition, which reads "once **every
task** routes through the implementer" at
[`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md)
lines 176–179. This brief does not re-scope a predeclared kill condition by
assertion: the parent owes an amendment to "every spec-backed plan task", owned
by the parent's owner, on the same footing as the two sibling amendments above.

There is no `U1 → D1` edge: `phase-scoped-policy-delivery.md` line 157 gates D1
`none`. Once the amendment above lands, **no backward edge runs from D3 to
U2** — until then the cycle is real, which is why U2 is unconfirmed.

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

- **[Owner decision, 2026-09-03]** The parent's “every plan task” does **not**
  reach direct-light by wording — direct-light skips `new-spec` and keeps its
  task in-session with no durable plan file. Coverage comes from the owner's
  decision to include it anyway, recorded in § "Ready gaps", not from the
  parent's text. That is also why U2's envelope differs in kind from U1's: with
  no plan task to hand over, the only thing worth dispatching is a verdict.
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

## Ready gaps

- **Closed 2026-09-03.** A revision-bound clean shaping review and the owner's
  explicit Ready confirmation are both on the record. The review ran three
  finding rounds — resolving a contradiction between the Outcome and U2, an
  extraction search that could not falsify its own conclusion, a cross-brief
  deadlock with `phase-scoped-policy-delivery`, and two success metrics that
  could not fail — followed by a scoped verification pass that returned `Clean`
  bound to this revision.
- **Settled — U2 is in scope** (owner decision, 2026-09-03). Direct-light skips
  `new-spec` and carries only a session-local task, so "every plan task" does
  not reach it by wording. It dispatches anyway: direct-light is the path small
  changes take, so excluding it would leave the most common changes with no
  phase-scoped policy, reproducing the gap this work exists to remove. U2 must
  keep its own ceremony minimal, because the light path exists to be light.
- **Owed at U3's slice confirmation** (settled out of U1 on 2026-09-03) — the exact extraction destination is unchosen. U3's spec must identify one
  existing or new file inside `work-loop/references/`, then prove that
  `SKILL.md` retains only routing and controller invariants.

  An earlier bounded search reported no existing owner. **That result was
  wrong**, and the corrected search is recorded here so the spec does not
  inherit the error. The earlier search required both tokens on one line:

  ```bash
  rg -n 'sequential.*implementer|implementer.*sequential' packs/core/.apm/skills/work-loop packs/core/.apm/agents
  ```

  No line in the repository is written that way, so the search could not
  falsify its own conclusion. Anchoring on headings and on the execution verb
  instead:

  ```bash
  rg -n '^#{1,3} .*(sequential|Phase 1|fallback|supervisor procedure)' -i \
    packs/core/.apm/skills/work-loop packs/core/.apm/agents
  rg -n 'sequentially|single-agent|topological order' \
    packs/core/.apm/skills/work-loop packs/core/.apm/agents
  ```

  This finds the real owner: `supervisor-mode.md` § "Phase 1 supervisor
  procedure" (lines 223–236) and § "Single-agent fallback" (lines 238–243), with
  the default at line 11 and a fourth text surface at `evals/evals.json` line
  42. `supervisor-mode.md` is therefore the leading destination candidate, and
  the spec must accept or reject it on the record rather than defaulting to a
  new file.
- **Closed 2026-09-03 by U1's spec** (AC11 and § "Testing Strategy") — the runtime dispatch assertion shape for `claude-code` and `codex` was not yet
  selected. Existing adapter tests prove projection, not that every work-loop
  task invokes the projected agent once. The absence search was:

  ```bash
  rg -n 'implementer|dispatch' packages/agentbundle/tests/build_pipeline/test_adapter_claude_code.py packages/agentbundle/tests/build_pipeline/test_adapter_codex.py
  # exit 1; no matches
  ```

  The slice spec must name the construction-test seam before approval.
- **Closed 2026-09-03 by U1's spec** (AC4) — the main-tree report and commit contract was not yet settled. Current
  `implementer.md` requires the agent to commit inside a worktree (lines 74–77),
  while the primary-session controller owns the shared checkout. The spec must
  decide who commits on the sequential path without expanding into parallel
  merge behavior. The *bound* on that decision is not owed — § "Constraints"
  already denies the implementer Git authority in the primary tree unless the
  spec explicitly grants it.

## Rabbit holes

- Re-enabling any Phase-2 verb to obtain sequential dispatch.
- Treating a projected agent file as proof that the runtime dispatched it.
- Copying all of EXECUTE into a new reference while leaving the same procedure
  operative in `SKILL.md`.
- Moving a marked canonical site out from under the pointers that cite it by
  name, leaving `implementer.md` and `adversarial-reviewer.md` aimed at a hole.
- Leaving the single-agent fallback operative and unmentioned beside a
  "universal dispatch" claim.
- Letting the implementer own state transitions, final gates, review, or
  closeout because it now edits the primary working tree.
- Claiming support for a host outside `claude-code` and `codex` without a later
  host-specific probe.

## Spec map

| Spec | Status |
| --- | --- |
| sequential-implementer-dispatch | Draft |

[`sequential-implementer-dispatch`](../../specs/sequential-implementer-dispatch/spec.md)
delivers U1. The Status column is auto-derived — do not hand-edit it. U3 and U2
are unconfirmed and have no spec.

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
