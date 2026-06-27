# Worked example — end-to-end flow trace + gap inventory

Anonymized worked example: *a secure personal-assistant agent — `example-assistant` —
that helps an owner plan recurring tasks, track item/resource state, generate a derived
list, and improve through approved learning.*

Purpose: trace every **human → agent → skill → artifact** hop, mark each gate, and
record where the chain BREAKS (a break = a producer with no consumer, or a consumer
with no producer = a gap). Two loops must not be conflated:
- **Build-time convergence loop** (us, designing/building the product).
- **Runtime learning loop** (the product itself improving through approved learning)
  — this is a *designed feature*, an output of the tech lens, not our build loop.

Legend: ✓ exists · ✗ missing (build) · ~ exists-but-not-wired (connection gap)

---

## G0 — Intake  [HUMAN CONSENT GATE — always surfaces]

| Hop | Detail |
| --- | --- |
| Human | Supplies the one-line vision. |
| Agent | `frame-intent` ✓ → resolves Scale=app, altitude=product-vision; flags "secure" + "approved learning" as load-bearing. |
| Surface | "Read as single-owner agentic app on a managed agent platform; appetite? confirm the two load-bearing terms." Human confirms/corrects. |
| Artifact | `docs/product/intents/example-assistant.md` (product-vision intent). |

Connected. **Gap: nothing drives repeated descent** vision→strategy→capabilities;
`decompose-intent` is one-level, human-triggered. → **GAP-O1 (altitude-descent driver)**.

## G1 — Strategy  [auto unless scope one-way-door / tension]

| Hop | Detail |
| --- | --- |
| Agent | `de-risk-intent` ✓ → riskiest assumptions: (a) owner approves learning vs ignores it; (b) resource state stays accurate without burdensome manual entry. Predeclares kill conditions. |
| Agent | `decompose-intent` ✓ → capabilities: task-planning · resource-state · derived-list · approved-learning · identity-security. |
| Subroutine | On assumption needing evidence (the right managed-platform memory pattern for approved learning) → `research` ✓ / a platform skill, fold back. |
| Artifact | child intents + outcomes/metrics (waste/error ↓, time-to-plan ↓, learning-acceptance rate). |

## G1.5 — Domain & MVP anchor  [HUMAN CONSENT GATE — always surfaces]

**The deepest failure mode: the agent cannot reason through a real-life domain it
doesn't know, so it hallucinates the domain and over-scopes** (e.g. proposes a
third-party fulfillment integration). This gate exists to anchor BEFORE any screen or
architecture is drawn.

| Hop | Detail | Status |
| --- | --- | --- |
| Agent | `research` applied mode ✓ — grounds the real-life activity (how owners actually plan/act/restock) + best practice + naive-design failure modes. | exists, **not wired as a mandatory pre-convergence gate → GAP-P4** |
| Agent | Produce a **Domain Framing artifact** the UX/tech lenses MUST consume; reconcile lens flags any screen/service that contradicts it. | typed artifact shape missing → **GAP-P4** |
| Agent | Bound **appetite/MVP** via the **Scope Boundary artifact**: anything not rooted in an in-appetite outcome is scope creep. | appetite in brief ✓ + frame-intent ✓, but **no scope-creep guard → GAP-O10** |
| Surface | Assumptions research could NOT resolve → surfaced here. MVP boundary → human confirms in/out. | — |

### Domain Framing + Scope Boundary — the recurring activity (MVP-scoped) — *worked example of GAP-P4 output*

*How the activity is really done (the real activity, not a fantasy of it):*
- It runs on a **cadence/horizon** (e.g. weekly), and the high-deliberation slice is a
  subset — the MVP anchors on that slice, not everything.
- The plan is **not followed exactly** — substitutions, skips, carry-overs. "Planned"
  and "actually done" diverge → the plan must be editable and "mark what you did" is a
  first-class action.
- **Carry-over** is first-class (do once, benefit twice) — affects both next-cycle
  planning and resource decrement.
- Quantities **scale** to the owner's context.
- Constraints that bind real choices: **preferences, exclusions, variety (no repeats),
  use-what-you-have / use-before-threshold** (the last is the lever for the waste-↓
  outcome).

*How resource state updates after each completed task (the genuinely hard part):*
- State **drifts** — consumption is in amounts that don't match acquisition units.
- Owners **will not maintain precise inventory** — demanding precision is why such tools
  fail (exactly the de-risk assumption flagged at G1).
- MVP loop: mark a task **done** → **coarse** decrement + one prompt "anything run
  out / low?" → accept **approximate** state and surface uncertainty → acquisition
  **replenishes**. Precision is explicitly a non-goal.

*MVP end-to-end:* set up context → seed the store (rough) → agent proposes the cycle's
tasks (store + variety + threshold) → review/swap/regenerate → derived list (needs −
store) → **external fulfillment is manual / out of MVP** → mark done → coarse decrement
+ carry-over prompt → approve learning.

*Explicitly OUT of MVP (appetite guard must reject these):* **third-party fulfillment /
external-service integration**, precise inventory capture, analytics/optimization,
multi-user collaboration, budget optimization, large-scale external import.

> Honest note: parts of this anchor are reasoning; a real run does `research` applied
> mode against the domain's best practice + behavior studies, and surfaces the residue
> it can't ground as assumptions at this gate. **That is the primitive.**

## Convergent loop @ capability/feature altitude  [THE BLACKBOARD]

Lenses the coordinator switches between in ONE context (per MAST — not arguing subagents):

**Product lens** — `decompose-intent` ✓: resource-state → features (add/edit/view item, auto-decrement on completion).

**UX lens:**
| Step | Skill | Artifact | Status |
| --- | --- | --- | --- |
| Journey map (onboard→setup→plan→review/swap→list→fulfill→complete→approve-learning) | `map-journey` | journey map | **✗ GAP-P1** |
| Service blueprint (frontstage screen ↔ backstage service, line of visibility) | `blueprint-service` | service blueprint | **✗ GAP-P2** |
| Screen inventory + per-screen state matrix (empty/loading/error/success/permission) | `inventory-screens` | screen inventory | **✗ GAP-P3** |
| Microcopy per screen-state | `voice-and-microcopy` | copy deck | ~ exists, **not wired to consume a screen inventory → GAP-C1** |

**Tech lens** — `architect-design`/`architect-diagram` ✓ + a managed-agent-platform skill:
domain model (Store, Item, TaskTemplate, Plan, DerivedList, **LearningProposal**, Owner);
events (TaskCompleted, PlanApproved, **LearningApproved**); platform primitives —
task/lookup **tools**, store + approved-learnings in **Memory**, owner **Identity**, **Guardrails**.
Designs the *runtime* learning loop (human-approved write to long-term Memory).

**Reconcile lens:**
| Step | Skill | Artifact | Status |
| --- | --- | --- | --- |
| Shared typed state all lenses read/write | blackboard | blackboard | **✗ GAP-O2** |
| Channel lenses "answer each other" through | open-questions queue | OQ queue | **✗ GAP-O3** |
| Orphan detection outcome→opportunity→capability→screen→action→service→contract→spec→component | traceability lint | matrix | **✗ GAP-O4** |

### The "answer each other" ripple (connectedness pressure test)

`inventory-screens` emits *learning-approval screen* → `blueprint-service` must back it
→ tech lens: "gated Memory write" → **security lens fires**: unapproved input writing to
agent memory = prompt-injection self-modification (OWASP LLM-01/08) → OQ routed to product
→ `decompose-intent` defines "what makes a learning approvable + who audits" → tech adds
approval aggregate + audit log → `inventory-screens` adds audit view → `voice-and-microcopy`
writes approval/audit copy. **Ripple settles → converged.**

> **GAP-O5 (live lens invocation):** `security-reviewer` ✓ and `quality-engineer` ✓ today
> run at *gates on a spec/diff*, not as live lenses on the *blackboard* (journey/blueprint).
> To participate in the ripple they must be invokable mid-loop on a non-code artifact.

## G2 — Convergence  [HUMAN CONSENT GATE — always surfaces]

| Hop | Detail | Status |
| --- | --- | --- |
| Agent | Saturation check: no new OQ + traceability closed; else stall-at-cap. | `research-project-check` pattern exists but research-scoped → **GAP-O6 (generalize stop-signal)** |
| Agent | Render blackboard → **decision brief**: journey + screens + arch sketch + tension/assumption ledger + one-way doors before build. | depends on GAP-O2 |
| Human | Approves the "what" before any "how". | — |
| Agent | Per feature: `decompose-intent` leaf → writes `docs/product/briefs/<slug>.md`. | ✓ |

> **GAP-O7 (cross-feature DAG):** vision yields *N* briefs/features; `receive-brief` ✓
> chains slices within ONE brief, `loop-cohort` ✓ does task-DAG within ONE spec. Nothing
> sequences *N features* in dependency order (identity before approved-learning, etc.).

## G3 — Spec  [auto unless risk trigger]

| Hop | Detail | Status |
| --- | --- | --- |
| Agent | `receive-brief` ✓ → `new-spec` ✓ per brief. Risk triggers fire (identity, memory writes, user input = security boundary) → full mode + `security-reviewer` at spec stage. | ✓ |
| Link | Spec LLD should *consume* the service blueprint + screen inventory + arch artifacts. | new-spec is description-driven; only optional `Brief:` back-link. UX/arch artifacts would **orphan** → **GAP-O8 (spec ← convergence-artifact linkage)** |

## G4 — Build  [auto — mechanical gates]

| Hop | Detail | Status |
| --- | --- | --- |
| Agent | `work-loop` ✓ per spec; supervisor mode fans disjoint plan tasks to `implementer` ✓ subagents (legit parallel: per-screen, per-tool). | ✓ |
| Subroutine | EXECUTE on the managed-agent-platform SDK → `contract-acquisition` ✓ + a platform skill. | ✓ |
| Review | `adversarial-reviewer` ✓, `security-reviewer` ✓, `quality-engineer` ✓. | ✓ |

## G5 — Ship  [HUMAN CONSENT GATE — always surfaces]

| Hop | Detail | Status |
| --- | --- | --- |
| Agent | Deploy (IaC) — one-way door: spend, IAM, cloud resources. | infra/operational skills ✓ |
| Boundary | `work-loop` ends at merged code, not a running agent. Deploy-as-product may be adopter infra, out of a code-catalogue's charter. | **GAP-O9 (build→deploy boundary) — decision, maybe out of scope** |

---

## Validated gap inventory

**Primitive gaps (build first — each usable standalone):**
- **GAP-P4 frame-domain** — wire `research` applied mode as a mandatory pre-convergence gate + a typed Domain Framing artifact lenses must consume. (The single biggest correctness lever: stops the agent hallucinating the domain.)
- GAP-P1 `map-journey` · GAP-P2 `blueprint-service` · GAP-P3 `inventory-screens` (experience pack)
- GAP-C1 wire `voice-and-microcopy` to consume a screen inventory
- GAP-O4 traceability lint (tool) · GAP-O6 generalize saturation stop-signal

**Orchestration gaps (build second — the coordinator):**
- GAP-O1 altitude-descent driver
- GAP-O2 blackboard (typed shared state) · GAP-O3 open-questions queue
- GAP-O5 live lens invocation on non-code artifacts (security/quality mid-loop)
- GAP-O7 cross-feature DAG · GAP-O8 spec←convergence-artifact linkage
- **GAP-O10 scope/appetite guard** — make the traceability lint bidirectional: any node not rooted in an in-appetite outcome = scope creep (this is what rejects the out-of-MVP integration), surfaced via predicate. *Note: the lint catches structural orphans; semantic over-scoping stays a human call at G1.5.*
- gate ladder + surfacing predicate (G0/G1.5/G2/G5 consent; predicate: one-way door / tension / stall / unevidenced-assumption / out-of-appetite)

**Decision (not necessarily build):** GAP-O9 build→deploy boundary.

## Sequencing: primitives → orchestrated team
1. **frame-domain wiring (P4)** + **Experience pack** (P1–P3) + GAP-C1 — standalone, immediately useful; P4 first because every later lens consumes its output.
2. **Convergence primitives** — blackboard schema (O2), OQ queue (O3), traceability lint with scope-creep direction (O4+O10), generalized saturation (O6), gate-ladder + predicate definitions.
3. **Coordinator/orchestrator** — drives descent (O1), runs the blackboard loop with live lenses (O5), cross-feature DAG (O7), spec linkage (O8), renders decision briefs at consent gates. Last because it depends on 1+2.
