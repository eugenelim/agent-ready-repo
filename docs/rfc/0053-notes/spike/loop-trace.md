# discovery-loop trace — example-assistant

> SPIKE ARTIFACT (RFC-0053 Decision-7 prototype). The gate-by-gate walk a single
> reasoning context (`discovery-lead`) executed, maintaining the four sidecar files by
> hand. It demonstrates the three transitions RFC-0048 D7 said the spike must confirm
> empirically: the **answer-each-other ripple**, the **gate rejection/recovery** with
> cascade-invalidation (O11), and the **outer cap** (O12). Read alongside
> `blackboard.json`, `open-questions.md`, `traceability.json`, `decision-log.md`.

## Round 1 — G0 → G1 → G1.5 (the descent)

- **G0 Intake** [consent]. `frame-intent` reads the one-line vision; Scale=app,
  altitude=product-vision; flags "secure" + "approved learning" as load-bearing. Human
  ratifies (decision-log r1). Blackboard slot `intent:vision` -> `ratified`.
- **O1 descent**: `discovery-lead` recursively applies `decompose-intent` from the vision
  to capability leaves (task-planning / resource-state / derived-list / approved-learning /
  identity-security). No new runtime — recursion is the controller calling one skill
  repeatedly in one context.
- **G1 Strategy** [auto]. `de-risk-intent` predeclares kill conditions. Predicate did not
  fire (no scope one-way-door, no logged conflict) -> auto-advance (decision-log r1).
- **G1.5 Domain & MVP** [consent]. `frame-domain` (wrapping `research` applied) grounds
  the real recurring-planning activity + the approximate-state MVP (`domain-framing`) and
  registers the **out-of-scope register** (`scope-boundary`: third-party fulfillment,
  precise inventory, multi-user, analytics). OQ-1 (approximate state) resolved against
  `domain-framing` and OQ-4 (single-owner) against `scope-boundary` — referent-settled,
  not surfaced. Human ratifies the MVP boundary (decision-log r1).

At end of round 1 the blackboard holds the intent ladder + domain-framing + scope-boundary
+ persona; the
traceability matrix has the upstream edges; the OQ queue has 2 resolved rows.

## Round 2 — convergence opens; two defects appear

The product lens runs `decompose-intent` at feature altitude and the UX lens runs
`map-journey` -> `inventory-screens` -> `blueprint-service`. Two things go wrong — exactly
the two failure modes RFC-0048 names:

1. **Over-scope.** A `cap.external-fulfillment` capability and a `screen:fulfillment` get
   proposed (the myopic-greedy-commitment / scope-creep mode). The traceability matrix at
   this point is `traceability.preconverge.json`.
2. **An unbacked security-sensitive screen.** `inventory-screens` emits a
   `learning-review` screen whose backing service has no contract yet — `OQ-3` opens.

Running the checker on the round-2 snapshot (reproducible):

```
$ python3 check_sidecar.py traceability.preconverge.json
== traceability: traceability.preconverge.json ==
   18 nodes, 21 edges
   ORPHANS (2):
     - service:learning-approval [service]: no consumer (down-edge)
     - service:fulfillment [service]: no consumer (down-edge)
== SATURATION: NOT converged ==
```

The typed state made both defects **mechanically visible** — this is the connectedness
claim, demonstrated, not asserted.

### O11 — gate rejection / recovery (the fulfillment cascade)

`OQ-2` ("is external-fulfillment in appetite?") is **not referent-settled** — out-of-
appetite is a scope/value call — so the predicate **surfaces** it (it does not resolve it
silently). At G1.5 the human rejects it (decision-log r2). The recovery transition then
runs, in the controller's own context, with no engine:

1. Mark `intent:cap.external-fulfillment` -> `rejected` (blackboard).
2. **Cascade-invalidate downstream slots via the traceability edges**: walk out-edges from
   the rejected node -> `screen:fulfillment`, `service:fulfillment` -> mark `stale`.
3. Drop the stale subtree's edges from the active matrix (-> `traceability.json`).
4. Re-run only the affected lens (UX) on the reduced surface. No other slot is touched —
   the edge set *scopes* the blast radius, which is the whole reason the matrix is typed.

This is the LangGraph-checkpointer / plan-mode reject→revise shape (note 09 O11), realized
as a markdown+JSON state edit, not a framework call.

### The answer-each-other ripple (OQ-3)

`OQ-3` routes UX -> tech. The tech lens answers "gated Memory write", which **fires the
security/compliance lens**: unapproved input writing to agent memory = prompt-injection
self-modification (OWASP LLM-01/08). The ripple (note 02) settles across lenses, each hop
a queue status change + a blackboard edit:

- security -> product: "define what makes a learning approvable + who audits" (`OQ-3` routed)
- product (`decompose-intent`): approval criteria + auditor = the owner
- tech (`architect-design`): adds an approval aggregate + an audit log; `contract:
  learning-approval@2`
- UX (`inventory-screens`): adds `screen:audit-view`
- design (`voice-and-microcopy`): writes approval/audit microcopy

`OQ-3` -> `resolved`. The new nodes + edges close the dangling `service:learning-approval`.
**No agent-to-agent chat** happened: every hop was the controller switching lenses and
writing the blackboard/queue. This is the MAST guardrail honored by topology (note 09).

## Round 3 — reconverge

UX re-runs on the reduced surface; the reconcile lens runs the live `security-reviewer` +
`quality-engineer` **design-artifact mode** (O5) over the journey/blueprint. OQ-5
(carry-over) resolved against the anchor. The matrix is now the converged
`traceability.json`.

## Round 4 — saturation, G2, handoff

Saturation check (O6, generalizing `research-project-check`): a full pass surfaces no new
OQ, the traceability matrix has no orphan, and no edit invalidates a prior slot. Run:

```
$ python3 check_sidecar.py traceability.json open-questions.md
== traceability: traceability.json ==  ->  no orphans
== open-questions: open-questions.md ==  ->  0 unsettled
== SATURATION: CONVERGED ==
```

- **G2 Convergence** [consent]. `discovery-lead` renders the blackboard into the
  **decision-brief**. The one value/scope call (OQ-2) was already adjudicated at G1.5, so
  there is **no open conflict to adjudicate** at G2 — the human ratifies the "what"
  (decision-log r4).
- **Backlog + G3 handoff**: decompose the package into ordered work items (the
  service-blueprint is the slicing instrument); `loop-cohort` topologically orders them;
  `work-loop` pulls one at a time -> brief -> `new-spec` -> build. The loops meet here and
  must not be conflated (D8).

## The cap path (O12) — modelled, not hit on the happy path

The happy run converged at **round 4 of a 12-round cap**, **$6.40 of a $25.00 budget**
(blackboard `meta`). Neither bound was approached, so the stall transition was not
exercised live. It is defined as: if `round == round_cap` (or `cost_spent >= cost_budget`)
**with any OQ still `open`/`routed` or any orphan remaining**, the loop **does not loop
forever** — it writes a stall record to the decision log (`status: stalled-at-cap`) and
**surfaces to the human** (surfacing predicate clause c — "a substitutable judgment's
referent failed / the loop cannot converge"). Worked sub-case: had `OQ-3` been a genuine
*value* conflict (security says never store learnings; a hypothetical growth lens says
share them for personalization) with no referent to settle it, the predicate would have
surfaced it to the human at G2 immediately — and if instead it had been a churning
*factual* loop, the cap would have caught it. Both paths terminate; neither needs a
runtime — the counter is a field in `meta` the controller increments per round.

## What the trace shows about "no engine"

Every transition above — descent, ripple, cascade-invalidation, saturation, the cap — was
performed by **one reasoning context editing four plain files**, with a ~60-line lint as
the only executable, and that lint is a *check* (child-4's shape), not a coordinator. The
harness (omnigent) supplied the runner, the worktree the files live in, the policy gates,
and the option-card consent UI; it did **not** supply, and did not need to supply, a
convergence engine. That is the empirical confirmation Decision 7 asked for.
