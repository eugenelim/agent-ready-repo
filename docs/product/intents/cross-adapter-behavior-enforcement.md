# Cross-adapter behavior enforcement

- **Status:** Draft
- **Level:** product-strategy

## Outcome

Every policy this repository publishes carries a **recorded verdict** for the
work it governs, and a missing or malformed verdict fails a deterministic
check — so a skipped policy is detectable rather than invisible.

**The guarantee is coverage, not obedience** (owner decision, 2026-09-03). No
mechanism can force a model to judge well. What is mechanically decidable is
whether **every registered policy produced a verdict**, because the registry
enumerates what must appear. That binds the output to something outside the
document, which is the only class of mechanism this repository has ever seen
catch a defect on its first run.

**The shape: three layers, with a model in only one.**

**1. Teach.** Policy families are data in a skill directory, which projects to
every host with no special handling — `evals/evals.json` is the existing proof.
Selection is keyed to **`engine-state.json.state`**, the FSM phase, because it
is the only phase signal recorded as tool-written data; `Shape:`, task
verification mode and task flavour are agent-selected prose with no mechanical
reader. Delivery reuses the shipped `Module index → select matching reference →
inline into the brief` pattern.

**2. Act.** The dispatched authoring agent works with the phase-selected
policies in context, enumerates them into a task list of one entry per rule, and
emits a per-policy verdict.

**3. Check, with no model in the path.** Two deterministic checks in the
`CAT-L031` shape — required teaching as data, compliance as data, one place,
`Severity.ERROR`:

- **Coverage:** every family the phase key selected has a verdict in the emitted
  artifact. A missing verdict fails. This closes the measured gap that nothing
  today records or checks that a selected module reached the acting agent.
- **Compliance:** for precise families only, a parse-level predicate over the
  produced artifact. Stylistic families never block.

**Two authoring agents, one machinery.** Every agent in the roster is a
reviewer, adjudicator, retriever, or lead except `implementer`, and **no
spec-authoring agent exists in any
pack** — spec authoring is a skill running in the primary session. So spec
authoring has no dispatch envelope, while review time has agents and does
receive inlined modules, and implementation gained one in U1. The shape needs a
`spec-author` agent keyed to the
`SPEC-PLAN-*` phases alongside `implementer` keyed to execution, carrying
different policy sets over the same delivery and enforcement path.

**A policy needing a reasoned verdict decomposes; it does not stay whole.** The
blocking surface stays precise because most such policies split into a decidable
part and a smaller semantic residue:

| Policy | Decidable part | Semantic residue |
| --- | --- | --- |
| Cognitive load | emphasis-bearing paragraphs per section; near-duplicate paragraphs | "short resumable parts" |
| The razor | whether a bounded search ran, from run provenance | whether the hit found was adequate |
| Repository anchoring | whether the plan's `Repository anchors` entries resolve | whether an anchor is apt |

The readability score is **not** the oracle for cognitive load: the rule scopes
that target to chat prose and states that a score "is not a reason to cut needed
facts".

**The residue is judged, under the survey's conditions.** A model judge may
block only after held-out labels, a per-policy confusion matrix, confidence
bounds, and bias, swap, verbosity, self-preference and drift tests; until then
the family is advisory. Verdicts route by severity — deterministic violations
block, calibrated high-confidence semantic violations block or require review,
low-confidence findings stay advisory, and **an abstention or a disagreement
between validators goes to human review, never to an automatic pass.**
Independence comes from judging across model families: `get_judge(adapter, …)`
is already pluggable and records `judge_adapter`, so codex can judge
claude-code-authored artifacts using the two adapters this intent already
scopes. A prose policy earns its keep only if the ablation in
[`guidance-activation-measurement.md`](../briefs/guidance-activation-measurement.md)
shows it changes behaviour above the mechanical baseline.

**Rejected: extending the finding-adjudicator's envelope as the enforcer.** It
adjudicates disputed reviewer findings, which is a different job from evaluating
a decidable predicate; routing a deterministic check through a model-mediated
step would add a non-deterministic hop where none is needed, and it runs
post-hoc when the preference is prevention. `review-artifact.py` already
validates artifact kinds generically, so a policy-verdict artifact can be
validated directly. The adjudicator keeps its existing job: if a policy finding
is disputed, adjudicating that dispute is already what it does.

**Hooks are deliberately not the mechanism.** They are the least standardized
surface available: a new pre-tool event fails projection on Copilot and Gemini,
drops with only a build log on Cursor, and no host's "nonzero means block"
contract is encoded anywhere. Agents and skill directories are both more
portable than hook events, so the enforcement edge sits on artifact validation
in our own gate chain rather than in a host hook.

## Opportunity

The packs steer behavior almost entirely through prose, and prose is a
probabilistic steering mechanism rather than a portable enforcement layer. A
compatibility claim is only valid for one `pack version x host adapter version
x model snapshot x inference configuration` tuple, so the current public claim
of portability is broader than the mechanism supports. Evidence:
[`cross-model-steering-survey.md`](../research/cross-model-steering-survey.md).

Fourteen shipped controls do not enforce what they appear to, and the pattern
across all of them is one thing: **construction is tested; application is not.**
Block presence is gated while compliance is not; the rule-router's shape is
linted while chain traversal is not; OKF module construction is tested while
inlining is not. Evidence:
[`behavior-controls-inventory.md`](../research/behavior-controls-inventory.md).

The mechanism to fix it is largely present. Hook wiring already projects to all
five hosts, and a structured, schema-validated per-skill artifact already ships
in `evals/evals.json`. What is missing is a policy primitive, a control on the
verdict artifact with a validator, and a detector that can drive a
non-Claude model.

## Assumptions

- Enforcement must bind to an artifact a deterministic script can check.
  Advice written into context is not model-invariant however reliably it is
  delivered, and a host hook cannot be relied on because hook events are the
  least standardized surface we ship to.
- The unit of enforcement is a policy family, not a clause. Per-clause
  validators would demand a 0.039% false-positive rate against 0.427% for a
  dozen families, which is the difference between attainable and not. Evidence:
  [`agent-behavior-oracle-patterns-survey.md`](../research/agent-behavior-oracle-patterns-survey.md).
- A structured policy makes routing, applicability, severity, and calibration
  mechanical. It does not make a semantic property decidable, and that is an
  acceptable limit because the measured failures were selection and invocation
  failures rather than judgment failures.
- No host is yet known to admit a blocking verdict from a shipped hook. Both
  bodies we ship return `0` by design, and Cursor drops an unmapped event with
  only a build log. This is the load-bearing unknown and it should be settled by
  a bounded spike before any capability is confirmed.
- A validated policy registry is itself a control whose application must be
  checked, or it recreates the pattern above one level up.

## De-risk

Reversibility: **one-way door** — a new primitive type projected to five hosts,
adopter-extensible, changing behaviour inside adopters' loops. Approach:
**`validate-first`** (the triage default for a one-way bet).

Riskiest assumption: **routing every plan task through a sequential implementer
activates policy reliably enough to be worth the delivery path.**

The delivery pattern is not in question. Subagents plus an inlined module are a
proven, shipped mechanism, and a **taught-and-checked** policy already blocks in
production: `CAT-L031` is `Severity.ERROR`, requires the broker-specific
teaching phrase, and AST-walks credentialed CLI scripts to reject banned argv
flags, with both halves carried as data. It has been retained, not disabled.

Rejected: a bespoke probe to discover whether a blocking control survives
contact with us. `CAT-L031` already shows one does. The measurement that probe
produced is kept, because it isolates *which* policies survive:

- **A precise policy survives.** `CAT-L031` targets a closed list of argv flags
  and blocks with essentially no false positives.
- **A stylistic policy does not.** Applying "at most one emphasis-bearing
  narrative paragraph per section" to the class `docs/AGENTS.md` governs blocks
  **405 of 1,477 files, 27.4%**, against a 0.4% per-family budget — 68 times
  over.

So the design rule this replaces the probe with: **policy families ship precise
or not at all.** A stylistic family may be advisory; it may not block.

What would have to be true:

- a sequential dispatch envelope exists at implementation time — **delivered by
  U1** for the spec-backed plan-task population;
- the selected module demonstrably reaches the acting agent, which nothing
  currently records or checks;
- the resulting behaviour is measurable, which needs an eval on a
  non-Claude adapter as well as claude-code.

**Kill condition (predeclared 2026-09-03; population narrowed 2026-09-03).**
Kill if, once every **spec-backed plan task** routes through the implementer
once, an eval of the sequential path shows **no improvement in policy adherence
over the current inline path** at a pre-registered effect size, on either
tested adapter.

The antecedent originally read "once every task routes through the
implementer". It was narrowed to the spec-backed plan-task population on
2026-09-03, discharging the amendment
[`universal-implementer-dispatch.md`](../briefs/universal-implementer-dispatch.md)
§ "Proposed slices" recorded as owed upward to this intent. **This is a
scoping, not a weakening:** "every task" was never reachable, for two reasons
that are owner decisions rather than delivery gaps.

- Direct-light implementation stays inline by owner decision. U2 dispatches a
  policy *verdict*, never a build, because dispatching direct-light
  implementation would trip the **Multi-person** risk trigger at
  `packs/core/.apm/skills/work-loop/SKILL.md` lines 73-74 and force full mode
  (line 70: "Risk triggers — any one routes the work to full mode"),
  contradicting the light path's purpose.
- Repair rounds re-entering `CODE-IMPLEMENTATION` also stay inline. Three of
  the four re-entry edges in
  `packs/core/.apm/skills/work-loop/scripts/loop-engine.py` —
  `gates-failed`, `findings-remain`, and `blocker-applied` — carry repair
  rather than a plan task and do not dispatch.

The effect size, the comparison, and the two-adapter requirement are
unchanged; only the population is narrowed, and it is narrowed to what the
delivered mechanism actually covers rather than to what the result turned out
to be.

**This intent owns that comparison; it does not borrow the sibling's.** The two
ablations vary different factors and must not be conflated:
[`guidance-activation-measurement.md`](../briefs/guidance-activation-measurement.md)
varies **the rule** — present, removed, length-matched placebo — to ask whether
a rule binds. This intent varies **the delivery path** — inline versus
dispatched — to ask whether an envelope improves adherence. A single experiment
cannot answer both, and running one while claiming the other would confound the
result.

```
validation_hook:
  assumption: sequential implementer dispatch activates policy more reliably
    than the current inline path
  kill_condition: no improvement at a pre-registered effect size on either
    tested adapter
  activity: run the paired eval across claude-code and codex once every
    spec-backed plan task routes through the implementer, which U1 delivered;
    U2 and U3 are not prerequisites for this eval
```

Verdict: **pending**, and it is now an eval rather than a bespoke probe. Desk
grounding is not validation, so this hook stays `to-validate`.

## Where the lifecycle holds, and where it breaks

Traced against the work-loop FSM as the artifacts are written. **Policy
delivery works at the review phases and, since U1, at `EXECUTE` for the
spec-backed plan-task population — those are the phases with a dispatched
agent. Drafting and routing are the remaining breaks.**

| Phase | Acting surface | Envelope | Policy delivery | Enforcement |
| --- | --- | --- | --- | --- |
| Routing, before `new-spec` | primary session | **none** | **impossible today** | B1's standing lint, at gate time not at routing |
| `SPEC-PLAN-DRAFTING` | `new-spec` skill, primary session | **none** | **blocked on capability 2** | pre-EXECUTE reviewers |
| `SPEC-PLAN-REVIEW` | reviewer agents | yes | works today | adjudication, `review-artifact.py` |
| `SPEC-PLAN-APPROVED` | human gate | n/a | n/a | `approve-plan` status guard |
| `EXECUTE`, code mode, spec-backed plan task | dispatched `implementer` | yes, since U1 | works today | gates |
| `EXECUTE`, code mode, direct-light or repair | inline in `work-loop` | **none** by owner decision | **out of the dispatch population** | gates |
| gates | scripts | n/a, no model | n/a | deterministic, works today |
| post-gates review | reviewer agents | yes | works today | adjudication |
| closeout | `close-work` | n/a | n/a | `lint-spec-status`, coverage lint |

Two breaks remain, each with a named owner: routing has no agent and is the
hardest case, since it precedes every dispatch; spec authoring needs
capability 2. Implementation's break is closed for the spec-backed plan-task
population — capability 1's U1 shipped that envelope — and the remaining
inline cases are owner decisions rather than gaps, as § "De-risk" records.
**Nothing else in the chain is missing** — the review phases already deliver
and enforce, and the gate and closeout phases need no model.

**One capability is partly delivered, and two further slices are unblocked.**
All five capabilities now have briefs —
[`universal-implementer-dispatch`](../briefs/universal-implementer-dispatch.md),
[`spec-author-agent`](../briefs/spec-author-agent.md),
[`phase-scoped-policy-delivery`](../briefs/phase-scoped-policy-delivery.md),
[`policy-arrival-validator`](../briefs/policy-arrival-validator.md), and
[`multi-adapter-eval-runner`](../briefs/multi-adapter-eval-runner.md) — and the
intent → brief → confirmed slice → spec path has been walked once, by
capability 1. Its U1 slice is **shipped**:
[`sequential-implementer-dispatch/spec.md`](../../specs/sequential-implementer-dispatch/spec.md)
carries `Status: Shipped`, merged in `d7cf1b741`. That brief is `Executing`;
every other capability brief is `Draft`.

Two slices are unblocked right now: `spec-author-agent`'s S1, whose envelope
gate U1 discharged, and `phase-scoped-policy-delivery`'s D1, which gates on
nothing.

## Decomposition

The capability level beneath this intent. Capability 1 is confirmed and has one
shipped slice; the rest are unconfirmed. **The order is set by what unblocks
what**, not by dependency alone.

1. `universal-implementer-dispatch` — **the enabler, and unconditional.** Route
   every spec-backed plan task through the implementer agent sequentially
   rather than only on the parallel path, and move implementation logic out of
   `work-loop`'s `SKILL.md`.

   **Status: U1 shipped 2026-09-03** in `d7cf1b741`
   ([`sequential-implementer-dispatch/spec.md`](../../specs/sequential-implementer-dispatch/spec.md)),
   delivering the dispatch envelope. U3 (extraction) and U2 (direct-light
   verdict dispatch) remain unshipped; U2 is unconfirmed.

   The three reasons this ranked first, and what U1 changed:

   - **Implementation had no dispatch envelope.** The implementer ran only on
     the parallel path, which is disabled — `dispatch-decision`, the `worktree`
     verbs and `auto-parallel` exit non-zero
     (`work-loop/references/supervisor-mode.md:3`, still current). Sequential
     work ran inside the skill, so there was no brief to inline a module into,
     and the two inlining precedents — `cloud-implementation-craft` and
     `operational-safety` — sat on a dormant path. **U1 closed this:**
     `work-loop/SKILL.md` now declares sequential dispatch, and craft reaches
     the agent inlined in its brief.
   - **It needed no Phase-2 decision.** Sequential dispatch is one task at a
     time with no concurrency and no worktree merge, so it required neither the
     absent `pending_transition` schema nor the collision gate. ADR-0061 is
     Frozen and deferred *parallel-wave* orchestration; it does not bear on
     single-agent dispatch.
   - **It relieves a live constraint.** `work-loop/SKILL.md` remains above
     `CAT-S003`'s warn tier. Measure the current body count with
     `agentbundle catalogue lint --root . --deep` rather than reading a figure
     here — the count moves with every edit, and `CAT-S003` governs body lines,
     not total lines.

   The bounded contract change this named — `implementer.md` assumed the
   supervisor had created `.worktrees/<task-id>/` — **is delivered**: the
   contract now names the primary working tree and an already-created worktree
   as the two roots the controller supplies.

2. `spec-author-agent` — the missing authoring agent. Core ships six agents and
   five are reviewers or adjudicators; the sixth is `implementer`. Spec
   authoring runs as a skill in the primary session, so `SPEC-PLAN-DRAFTING` is
   the only *authoring* phase with no dispatch envelope — `SPEC-PLAN-REVIEW`
   has one, and routing plus the by-decision inline `EXECUTE` cases remain as
   § "Where the lifecycle holds" records them. This capability gives spec
   authoring a dispatched agent so authoring-time policy has somewhere to
   arrive, reusing the same delivery and enforcement path as the implementer
   rather than a parallel one.

3. `phase-scoped-policy-delivery` — extends the existing mechanism rather than
   inventing one. The `Module index → select matching reference → inline into
   the subagent brief` pattern already exists; the addition is keying selection
   to **`engine-state.json.state`**, the FSM phase, which is the only
   phase signal already recorded as tool-written data. `Shape:`, task
   verification mode and task flavour are all agent-selected prose with no
   mechanical reader. Evidence:
   [`phase-scoped-policy-delivery.md`](../research/phase-scoped-policy-delivery.md).

4. `policy-arrival-validator` — makes delivery provable. Today both selection
   and inlining are prose-directed and **nothing records or checks that the
   selected module reached the acting agent's brief.** Follows the `CAT-L031`
   shape: teaching required as data, compliance checked deterministically, both
   in one place.

5. `multi-adapter-eval-runner` — independent of the rest. Adds a **Codex
   detector**, since `--adapter` and the codex *judge* backend already ship and
   only the detector that drives the authoring is missing; nothing else here can
   claim portability until it exists. **It must not
   change the default or the scheduled workflow** (owner decision, 2026-09-02).
   `.github/workflows/pack-evals.yml` already runs claude-code only, pinned to
   a named CLI version because the activation event's stream shape is
   version-sensitive; it is `schedule` plus `workflow_dispatch` only, so an
   untrusted-fork PR cannot reach the API key; it is report-only via
   `continue-on-error`; and it is already parameterised by a `packs` dispatch
   input. Additional adapters stay local or on-demand, because each one adds a
   vendor secret to a workflow whose posture is security-load-bearing and
   asserted by `tools/test-pack-evals-workflow.py`, and requires every host CLI
   installed and pinned on the runner.

Three capability briefs already exist beneath this intent and are re-gated by
it:

- [`guidance-activation-measurement.md`](../briefs/guidance-activation-measurement.md)
  asks whether a rule adds behavioral value above a mechanical control, varying
  the rule rather than the delivery path. Its compliance test is the policy
  registry's validator,
  so it follows rather than leads.
- [`agent-authoring-input-quality.md`](../briefs/agent-authoring-input-quality.md)
  and
  [`stage-input-readiness.md`](../briefs/stage-input-readiness.md)
  both ship written guidance and wait on that ablation. `stage-input-readiness`'s
  declared-shape gate is mechanical and does not wait.

## Unresolved questions

- Does any host admit a blocking verdict from a shipped hook, and by what exit
  or output contract? Nothing here encodes it.
- Does the public portability claim need amending to the qualification tuple
  above? That is a governance decision rather than a delivery slice, and it
  likely needs an RFC.
- Which policy families ship first, and which tier does each fall into? A
  deterministic family needs no judge; a semantic one needs a calibrated judge
  and a measured false-block rate.
- Does a `policies/` directory extend the blessed skill layout, or do policies
  live under an existing directory? A non-blessed subdirectory warns under
  `CAT-S004`.

## Source

- Mode: repo-origin
- Locator: `docs/product/briefs/guidance-activation-measurement.md`
- Framed 2026-09-02 while reviewing that brief's design, when its compliance
  test proved to be a prerequisite rather than a part of the measurement.
