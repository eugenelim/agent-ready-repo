# Composed end-to-end walkthrough — `example-assistant` across the whole landed series

**Purpose.** RFC-0048's discharge requires pressure-testing the *composed* operating
model — not each child in isolation, but the whole flow vision → shipped code running
through **every landed RFC's mechanism at once**. Note 02 traced the flow to find the
gaps; the [0053 spike](../0053-notes/01-spike-report.md) walked G0→G2 to confirm the
coordinator; the [release-loop spec](../../specs/release-loop/spec.md) (AC12) walks one
outer cycle. **None of them walked the continuous arc G0→G5 across 0048 *and* 0049 with
the actual artifact products** (the spike produced sidecar *state*, not the journey map /
service blueprint / screen briefs / backlog / spec themselves). This note does that: it
yields the **concrete example artifact at each stage**, so the claim "the composed set is
one coherent operating system" is checkable against artifacts, not assertions.

It is also the instrument that surfaced the drift the discharge folds back into RFC-0048.
Where the walk hit a seam that did not hold, it is marked **▶ DRIFT-x** and forward-points
to the matching [RFC-0048 § Amendments](../0048-autonomous-product-team-operating-model.md#amendments)
(2026-06-26, the discharge reconciliation) entry.

Subject (anonymized, verbatim from [note 02](02-worked-example-flow-trace.md)): *a secure
personal-assistant agent — `example-assistant` — that helps an owner plan recurring tasks,
track item/resource state, generate a derived list, and improve through approved learning.*

Driver legend: **DL** = `discovery-lead` (product-engineering) · **WL** = `work-loop`
supervisor (core) · **RL** = `release-lead` (release-engineering) · **H** = human.

---

## Stage 0 · G0 Intake — the intent  [consent gate]

**Driver:** DL · **Skill:** `frame-intent` (product-engineering) · **Human:** ratifies.

**EXAMPLE ARTIFACT — `docs/product/intents/example-assistant.md` (the product-vision intent):**

```markdown
---
type: intent
level: product-vision
slug: example-assistant
scale: app
appetite: small-batch (one cycle to a usable single-owner MVP)
---
# Intent: example-assistant

**Outcome.** A single owner plans a recurring cycle of tasks with less waste and less
time-to-plan, and the assistant gets better at it through learning the owner *approves*.

**Opportunity.** Owners re-plan the same cycle by hand every period; resource state drifts;
"what do I need" is re-derived each time. A trustworthy assistant that proposes the cycle,
tracks coarse state, and only learns what the owner signs off on removes that toil.

**Load-bearing terms (flagged for ratification):**
- *secure* — single-owner identity boundary; no third party reads the owner's plan/state.
- *approved learning* — the assistant proposes; the owner approves before anything is
  written to durable memory. (This is a security boundary, not just a feature — see G1.5.)
```

**H ratifies** (decision-log r1): scale = app, appetite = small-batch single-owner MVP,
the two load-bearing terms confirmed. Auto-advance to G1.

---

## Stage 1 · G1 Strategy — capabilities + de-risk  [auto unless one-way-door / tension]

**Driver:** DL · **Skills:** `de-risk-intent`, `decompose-intent` (PE); `research`
subroutine (research) on the memory-pattern assumption.

**EXAMPLE ARTIFACTS** (capability intents + assumption test, abbreviated):

```markdown
# Capabilities (decompose-intent, one level down from product-vision)
- cap:task-planning      — propose the cycle's tasks (store + variety + threshold)
- cap:resource-state     — coarse, drift-tolerant item/resource tracking
- cap:derived-list       — needs − store → a derived acquisition list
- cap:approved-learning  — owner-approved writes to durable memory
- cap:identity-security  — single-owner auth boundary

# Assumption test (riskiest assumptions + kill conditions)
- A1: owner *approves* learning rather than ignoring the prompt.
      Kill if approval-acceptance rate < threshold in the prototype walk.
- A2: coarse state stays useful without burdensome manual entry.
      Kill if the MVP loop demands precision to be correct.
```

Auto-advances (no scope one-way-door yet; the fulfillment temptation surfaces at G1.5).

---

## Stage 2 · G1.5 Domain & MVP — Domain Framing + Scope Boundary  [consent gate]

**Driver:** DL · **Skill:** `frame-domain` (PE) wrapping `research` applied mode (+
`decision-archaeology` if brownfield — greenfield here, so the current-system half is omitted and the
Domain Framing says so, per [frame-domain spec AC3](../../specs/frame-domain/spec.md)).
This stage produces **two** typed artifacts: the **Domain Framing** (the grounding) and the
**Scope Boundary** (the MVP appetite + out-of-scope register).

**EXAMPLE ARTIFACT — `docs/discovery/example-assistant/domain-framing.md`** (the grounding
components fixed by the [frame-domain spec](../../specs/frame-domain/spec.md)
AC2; the activity content is note 02's domain grounding, now shaped into the typed artifact):

```markdown
---
type: domain-framing
slug: example-assistant
---
# Domain Framing: example-assistant

## Real-world-activity half  (research applied mode — grounded, not intuited)
- Runs on a cadence/horizon (e.g. weekly); the high-deliberation slice is a subset — the
  MVP anchors on that slice, not everything.
- The plan is **not** followed exactly — substitutions, skips, carry-overs. "Planned" ≠
  "actually done" → the plan must be editable and "mark what you did" is first-class.
- Carry-over is first-class (do once, benefit twice) — affects next-cycle planning *and*
  resource decrement.
- Quantities scale to the owner's context.
- Binding constraints: preferences, exclusions, variety (no repeats), use-what-you-have /
  use-before-threshold (the lever for the waste-↓ outcome).
- Resource state **drifts**; owners will not maintain precise inventory — demanding
  precision is why such tools fail (A2). MVP loop: mark done → coarse decrement + one
  "anything run out/low?" prompt → accept approximate state + surface uncertainty.
- Naive-design failure modes: precise-inventory capture; auto-ordering without consent;
  treating "planned" as "done".

## Current-system half
- N/A — greenfield. (Stated explicitly per AC3.)

## Residual assumptions (could not ground — surfaced for the human, AC5)
- The right managed-platform memory pattern for approved-learning writes (routed to a
  platform skill at G1; remains a build-time tech-lens question).
```

**EXAMPLE ARTIFACT — `docs/discovery/example-assistant/scope-boundary.md`** (the MVP appetite
+ out-of-scope register — the upstream G1.5 scope-creep guard the brief inherits and refines at G3):

```markdown
---
type: scope-boundary
slug: example-assistant
---
# Scope Boundary: example-assistant

## MVP out-of-scope register  (each with its appetite reason — AC4)
- third-party fulfillment / external-service integration — a one-way door (spend, IAM,
  third-party contract); out of a single-owner MVP appetite.
- precise inventory capture — contradicts A2; the failure mode itself.
- analytics / optimization — second-order; no in-appetite outcome roots it.
- multi-user collaboration — single-owner is the security boundary.
- budget optimization, large-scale external import — beyond appetite.
```

**H ratifies the MVP boundary** (decision-log r2 region). The Scope Boundary's out-of-scope register is now
the referent the scope guard and the human use to reject the fulfillment temptation.

---

## Stage 3 · Discovery convergence — the lens-team on the blackboard

**Driver:** DL as controller; **solo** here (small discovery — the spike ran solo), with
the design-time lenses switched in one context per [RFC-0053 D5](../0053-the-discovery-loop.md).
The sidecar (schema carried in `discovery-loop`, not `core`, [RFC-0053 D2](../0053-the-discovery-loop.md)) threads it.

### 3a · Product lens — features
`decompose-intent`: `cap:resource-state` → features add/edit/view item, auto-decrement on
completion. (Feature intents land as blackboard slots.)

### 3b · UX lens — the connective layer (the experience pack, RFC-0050)

**EXAMPLE ARTIFACT — `journey-map`** (`map-journey`; surface: cross — [RFC-0050 D3](../0050-the-experience-pack.md)):

```markdown
---
type: journey-map
slug: example-assistant
surface: cross-platform
---
# Journey: plan → act → learn
| Stage      | Action                         | Emotion         | Pain                  | Opportunity |
|------------|--------------------------------|-----------------|-----------------------|-------------|
| Onboard    | set up context, seed store     | hopeful/unsure  | precision pressure    | seed *rough* |
| Plan       | review proposed cycle          | evaluating      | "is this right for me"| store+variety+threshold |
| Adjust     | swap / regenerate items        | in-control      | rigid plans           | editable, mark-what-you-did |
| List       | see derived acquisition list   | relieved        | re-derive by hand     | needs − store |
| Act        | mark tasks done                | satisfied       | drift, over-precision | coarse decrement + 1 prompt |
| Learn      | approve a proposed learning    | cautious/trust  | silent self-modify    | owner-gated memory write |
```

▶ **Note (no drift):** journey/screen artifacts produced *inside this initiative* are
written under `docs/discovery/example-assistant/`, **not** `docs/design/` — the in-initiative
home. The two homes are reconciled at **DRIFT-D**.

**EXAMPLE ARTIFACT — `service-blueprint`** (`blueprint-service`; the slicing instrument):

```markdown
---
type: service-blueprint
slug: example-assistant
---
# Service blueprint  (frontstage screen ↔ backstage component; line of visibility)
| Frontstage (screen)   | Line of visibility | Backstage (component / tool)        | Support |
|-----------------------|--------------------|-------------------------------------|---------|
| plan-review           | —                  | planner.propose (api-service)       | store   |
| resource-dashboard    | —                  | resource.read / resource.decrement  | data-store |
| derived-list          | —                  | list.derive (api-service)           | store   |
| learning-review       | —                  | learning.propose / learning.approve | worker (learning pipeline) |
| audit-log             | —                  | audit.read                          | data-store |
```

Backstage column → the slicing instrument: each backstage component becomes a `Component:`
(web-app · api-service · data-store · worker); cross-component edges → `depends_on`.

**EXAMPLE ARTIFACT — `screen-inventory` + one per-screen brief**
(`inventory-screens`; states **defer to the shared handle-all-states floor**, RFC-0050 D2/D4;
brief template = [note 07](07-screen-brief-format.md)):

```markdown
---
type: screen-inventory
slug: example-assistant
surface: cross-platform
---
# Screen inventory
plan-review · resource-dashboard · derived-list · learning-review · audit-view
(per-screen briefs under screens/<name>.md; states from the quality-floor floor:
 empty/loading/error/success/partial/disabled + permission/denied where gated)
```

```markdown
# Screen brief: learning-review   ·   example-assistant   ·   surface: cross
## Place in the whole
- Journey step(s): Learn
- Enters from: resource-dashboard · Exits to: audit-view
- Traces to outcome: learning-acceptance
## Job
Let the owner review one proposed learning and approve or reject it before it is written.
## States
- empty: no proposals pending
- loading: fetching proposals (skeleton)
- error: proposal fetch failed — blame-free, retry
- success/default: a proposal with its evidence + Approve / Reject
- permission/denied (if gated): only the owner can approve
## Data & actions
- Shows: the proposed learning + the evidence that produced it
- Actions: Approve → learning.approve (gated Memory write + audit-log append)
           Reject  → learning.reject
           View audit → audit.read
## Copy
- see copy-deck §learning-review (voice-and-microcopy, consuming this state matrix)
## Shared contract — REFERENCE, do not restate
- Design system: tokens + component set; reuse list-row, button set, lock-badge
- Aesthetic direction: pointer to the grounded taste reference
- Navigation / chrome: shared nav model
- Quality floor: WCAG AA · reduced-motion · handle-all-states
## Consistency invariants
- Reuse (never reinvent): list-row, button set, lock-badge
- Must stay consistent with: audit-log, resource-dashboard
## Done
[ ] all states rendered  [ ] every action wired to a named service
[ ] copy in per state    [ ] WCAG AA + reduced-motion
[ ] uses the design system  [ ] design-critique clean
```

### 3c · Design lens
`aesthetic-direction` (grounded in persona + precedent + standards + platform — RFC-0050 D5),
`design-critique` taste mode, `voice-and-microcopy` (PE) consuming the per-screen state matrix.

▶ **DRIFT-F (persona).** `aesthetic-direction` consumes a persona "from the Domain Framing,
or **elicited inline if absent**" (RFC-0050 D5). The frame-domain spec fixes the Domain Framing schema at
its grounding components and excludes persona. So in this walk the persona is **elicited inline by
its first consumer**, not produced as a separate typed artifact. Note 04 lists persona with a
producer "(in Domain Framing)" — that producer claim is the drift; reconciled at **DRIFT-F**.

### 3d · Tech lens
`architect-design` / `architect-diagram` (architect) + a managed-agent-platform skill +
`api`/`event-contract` (contracts): domain model (Store, Item, TaskTemplate, Plan,
DerivedList, **LearningProposal**, Owner); events (TaskCompleted, PlanApproved,
**LearningApproved**); platform primitives — tools, Memory (store + approved-learnings),
Identity, Guardrails. Designs the *runtime* learning loop (human-approved durable write).

### 3e · Reconcile lens + the answer-each-other ripple

Lenses bounce off each other **through the open-questions queue + blackboard**, never chat
(MAST guardrail by topology). The reconcile lens runs `security-reviewer` + `quality-engineer`
in their **design-artifact mode** ([RFC-0048 O5 / Decision 2](../0048-autonomous-product-team-operating-model.md)).

▶ **DRIFT-E (reviewer roster).** The security lens that fires here is the **same
`security-reviewer` agent in design-artifact mode** — *not* a fourth agent. RFC-0048 D7/D8
and RFC-0053 D5 call it "a different agent from `work-loop`'s code `security-reviewer`,"
which collides with Decision 2's "a mode, not a new agent." Reconciled at **DRIFT-E** (same
agent definition; different *invocation/lens*, design-time over the blackboard).

**EXAMPLE ARTIFACT — the OQ ripple on the blackboard** (from the [spike](../0053-notes/01-spike-report.md),
the connectedness pressure test):

```
inventory-screens emits screen:learning-review
  → blueprint-service must back it → tech: "gated Memory write"
  → SECURITY LENS FIRES (security-reviewer, design-artifact mode):
       unapproved input writing to agent memory = prompt-injection self-modification
       (OWASP LLM-01/08)
  → OQ-3 routed to product → decompose-intent: "what makes a learning approvable + who audits"
  → tech: approval aggregate + audit log, contract:learning-approval@2
  → inventory-screens: adds screen:audit-view
  → voice-and-microcopy: approval/audit copy
  → ripple settles → service:learning-approval no longer orphaned → CONVERGED
```

The traceability slot's `check_sidecar` lint flags `service:learning-approval` +
`service:fulfillment` as orphans **pre-ripple**, reports CONVERGED after — connectedness is
checkable in ~60 lines, no engine ([RFC-0053 D2](../0053-the-discovery-loop.md)).

▶ **DRIFT-G (Discovery edge).** The chain the lint walks closes the *discovery* edges here.
But the **`spec → discovery` up-edge** (the `Discovery:` header on the eventual spec) is
authored by no skill in this walk — it is [note 09 O8](09-gap-resolutions.md)'s `new-spec`
`Discovery:` header, owed by a named follow-on. Until it ships, the lint degrades past that
edge — so the G3 backstop is only as strong as that follow-on. Assigned at **DRIFT-G**.

### The fulfillment over-scope rejection — O11 cascade-invalidation

OQ-2 ("is external-fulfillment in appetite?") is a **scope/value call** — not
referent-settled — so the surfacing predicate **surfaces it** at G1.5; **H rejects**.
Recovery, in the controller's context, no engine ([RFC-0053 D3](../0053-the-discovery-loop.md)):
mark `cap:external-fulfillment` rejected → **cascade-invalidate** `screen:fulfillment` +
`service:fulfillment` stale by walking the traceability out-edges → drop their edges → re-run
only the UX lens. The edge set scopes the blast radius. A markdown+JSON edit, not a framework call.

---

## Stage 4 · G2 Convergence — the decision brief  [consent gate]

**Driver:** DL renders the blackboard · **Human:** ratifies the "what"; adjudicates conflicts.

Saturation (O6): no open/routed OQ + traceability closed + a full pass with no invalidating
edit → CONVERGED (the spike: round 4 of 12, $6.40 of $25 — the O12 cap *modelled*, not hit).

**EXAMPLE ARTIFACT — `docs/discovery/example-assistant/decision-brief.md`:**

```markdown
---
type: decision-brief
slug: example-assistant
gate: G2
---
# Decision brief — the "what" (ratified)
## Journey + screens
Plan → Adjust → List → Act → Learn; screens plan-review, resource-dashboard, derived-list,
learning-review, audit-view (+ per-screen briefs).
## Architecture sketch
api-service (planner/list/learning tools) · data-store (store/audit) · worker (learning
pipeline) · web-app (screens). Contracts: contract:learning-approval@2.
## Tension / assumption ledger
- A1 (approval uptake), A2 (coarse state) — to validate in build + the outer loop.
- OWASP LLM-01/08 (memory self-modify) — controlled by owner-gated write + audit.
## One-way doors before build
- external-fulfillment — REJECTED at G1.5 (out of appetite).
- durable memory schema — reversible in MVP (ephemeral-first); revisit at deploy.
```

**H ratifies** (decision-log: G2, ratified-by human, reversible). OQ-2 was already adjudicated
at G1.5, so no open conflict remains at G2.

---

## Stage 5 · The backlog bridge — decision brief → ordered work items

**Driver:** DL decomposes; the **service blueprint is the slicing instrument**; `loop-cohort`
will order it ([note 08](08-artifact-layout-and-backlog.md)).

**EXAMPLE ARTIFACT — `docs/discovery/example-assistant/backlog.md`** (note 08 work-item schema):

```yaml
- id: WI-001
  title: single-owner identity boundary
  components: [api-service]
  brief: docs/product/briefs/identity-security.md
  depends_on: []
  traces_to: outcome=secure · decision-brief §architecture
  status: todo
- id: WI-002
  title: coarse resource-state (read / decrement / drift-tolerant)
  components: [api-service, data-store]
  brief: docs/product/briefs/resource-state.md
  depends_on: [WI-001]
  traces_to: outcome=waste-down · decision-brief §journey(Act)
  status: todo
- id: WI-003
  title: approve a proposed learning  (owner-gated memory write + audit)
  components: [api-service, web-app, worker, data-store]
  brief: docs/product/briefs/approved-learning.md
  depends_on: [WI-001]                # identity before learning
  traces_to: outcome=learning-acceptance · decision-brief §learning
  status: todo
```

▶ **DRIFT-H (backlog producer + loop-cohort fit).** This artifact is asserted (note 08) and
ordered by `loop-cohort` — but **no AC in any landed spec verifies the decomposition step or
that `loop-cohort` ingests the cross-component work-item shape** (it schedules *within-spec*
tasks today). Owed as ACs at RFC-0053's implementing spec; assigned at **DRIFT-H**.

---

## Stage 6 · G3 handoff → per-component work-loop (inner) — a spec

**Driver:** WL · **Skills:** `receive-brief` → `new-spec` (core); `security-reviewer` at
spec stage (identity + memory writes = security boundary → full mode). `work-loop` pulls
**WI-003** (after WI-001).

**EXAMPLE ARTIFACT — `docs/specs/approved-learning/spec.md` (excerpt):**

```markdown
# Spec: approved-learning
- Status: Draft
- Discovery: docs/discovery/example-assistant/decision-brief.md §learning   # ◀ the G3 up-edge (DRIFT-G)
- Brief: docs/product/briefs/approved-learning.md
- Component: api-service + web-app + worker + data-store
- Shape: mixed

## Acceptance Criteria
- [ ] A proposed learning is written to durable memory ONLY after an owner Approve.
- [ ] Every approve/reject is appended to an audit log the owner can read.
- [ ] Unapproved input cannot write durable memory (OWASP LLM-01/08 — the ripple finding).
- [ ] The learning-review screen handles all states (per the per-screen brief).
```

The spec's `Discovery:` header is the G3 traceability up-edge — **the producer DRIFT-G
assigns**. The LLD consumes the service blueprint + the per-screen brief (closing note 02's
GAP-O8 by the same edge). Risk triggers fire → full mode + `security-reviewer` spec-stage.

---

## Stage 7 · G4 Build — a built component

**Driver:** WL supervisor → `implementer` fan-out (per-screen / per-tool — legit disjoint
parallel); `contract-acquisition` + the platform skill at EXECUTE; `adversarial-reviewer` /
`security-reviewer` / `quality-engineer` at REVIEW; the **self-coverage gate** (RFC-0051)
runs at REVIEW→DECIDE as the pre-done coverage pass.

**EXAMPLE ARTIFACT — the component increment** (`packages/api-service/` + `packages/web-app/`):
- `api-service`: `learning.propose`, `learning.approve` (owner-gated durable write),
  `audit.read`; the approval aggregate; durable-memory write guarded behind an attested
  owner-approval (the ripple's control, now code).
- `web-app`: the `learning-review` screen (all states), the `audit-view` screen.
- Local verification via the fidelity ladder (RFC-0049 D3): fakes → contract tests
  (`contract:learning-approval@2`) → Testcontainers for the data-store. Tests are the verifier;
  gates green. **Inner loop ends at the locally-built, deploy-ready, digest-pinned artifact.**

---

## Stage 8 · Release loop (outer, ephemeral) — the e2e / canary result

**Driver:** RL (release-engineering) · **Skill:** `release-loop` · reuses `operational-safety`
+ `quality-engineer` + `security-reviewer`; consumes the **same sidecar schema**
([release-loop spec](../../specs/release-loop/spec.md) AC7). Minimum-regret carve: autonomous
on ephemeral envs, human-gated at the irreversible exits.

**EXAMPLE ARTIFACT — the e2e / canary result** (one outer cycle, release-loop spec AC12 shape):

```markdown
# Release cycle — approved-learning  (round 1 of N)
## Deploy
ephemeral env eph-pr-142 (network/data-isolated from prod, no real data, cannot reach
prod state — the AC3 isolation conditions; "reversible" earns its name only under them).
Deploys the digest-pinned artifact the inner loop verified (AC7 provenance).
## e2e on the changed surface
- approve-flow: propose → owner Approve → durable write present + audit row appended  PASS
- reject-flow:  propose → Reject → no durable write, audit row appended                PASS
- injection probe: unapproved input attempts a memory write → blocked                  PASS
- changed-surface coverage: 4/4 changed endpoints have ≥1 passing e2e assertion         PASS
## Canary (non-prod tier)
success 100% · error 0% · p95 latency within SLO · flake 0% (< 2% bar)                  PASS
## Convergence-by-policy verdict
canary OK + changed-surface covered + flake < 2% → CONVERGED to the human gate.
## Decision-log
finding→task feedback (none this round); env torn down on cycle end (AC10f).
```

▶ **DRIFT-I (sidecar schema).** Both this loop and the traceability lint *consume* the
sidecar schema (carried in `discovery-loop`, not `core`), which exists only as **prose
field-lists** in RFC-0053 D2 — no implementing spec lands the carried schema reference yet.
Three consumers, a prose producer. Assigned at **DRIFT-I**.

---

## Stage 9 · G5 Ship — prod  [consent gate, irreversible]

**Driver:** RL surfaces the option card · **Human:** ratifies the prod ship (irreversible:
first real users/data, spend, IAM). The verdict is written through a **harness-attested
channel the agent holds no token for** (release-loop AC10a; the credential tiering of AC10g
makes it *inability*, not prohibition). Decision-log records the irreversible ratification.

```markdown
# Decision-log (final)
| ts | gate | decision | ratified-by | reversibility-class | rationale |
| …  | G5   | ship approved-learning to prod | human | one-way-door | A1/A2 validated in the outer loop; canary clean |
```

**Shipped.** The arc G0→G5 ran as content + plain typed files + lint/policy checks across
three loop-teams; the only executables were `check_sidecar`/the traceability lint and the
canary policy check — **no engine** (the load-bearing claim, demonstrated continuous here,
not just per-child).

---

## What the composed walk demonstrates — and what it surfaced

**Held together (the spine is coherent):**
- The **gate arc** G0→G5 runs continuously; consent gates G0/G1.5/G2 (discovery) + G5 (release)
  fire exactly where 0048+0049 say; the release outer loop sits in the G4→G5 gap (a loop, not
  a numbered gate).
- The **sidecar** threads all three loops as the one connectedness verifier; the **handoffs**
  (G3 brief→spec, deploy work→release, G5 release→prod) each have a named owner.
- The **no-engine** claim is carried end-to-end, not just per child.
- The **artifact chain** closes from `outcome` to a built `component` and a prod ship.

**Surfaced drift (folded into [RFC-0048 § Amendments](../0048-autonomous-product-team-operating-model.md#amendments), 2026-06-26):**
DRIFT-A (chain terminus `component`) · DRIFT-B (sidecar store `_state/` vs harness) ·
DRIFT-C (`docs/discovery/` layout key owner) · DRIFT-D (experience artifacts in-initiative
home) · DRIFT-E (reviewer = mode not new agent) · DRIFT-F (persona elicit-inline) ·
DRIFT-G (`Discovery:` up-edge producer) · DRIFT-H (backlog producer + `loop-cohort` fit) ·
DRIFT-I (carried sidecar schema reference owed — in `discovery-loop`, not `core`).

Every drift is a **seam/wiring/owner-assignment** item, not a structural flaw — which is why
the foundation is **frozen after** these reconciliations, the exact job the provisional period
exists to do.
