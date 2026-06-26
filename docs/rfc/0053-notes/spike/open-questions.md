# Open-questions queue — example-assistant

> SPIKE ARTIFACT (RFC-0053 Decision-7 prototype). The typed open-questions slot of the
> sidecar. Schema (RFC-0048 D7): `{id, raised-by, target-discipline, question, status,
> resolution, round}`. This is the channel lenses "answer each other" through (note 02
> §"the answer-each-other ripple"). `status ∈ open | routed | resolved | surfaced`.
> **Saturation rule (O6):** converged iff no `open`/`routed` rows remain *and* the
> traceability matrix has no orphan *and* a full pass produced no invalidating edit.

| id | raised-by | target-discipline | question | status | resolution | round |
| --- | --- | --- | --- | --- | --- | --- |
| OQ-1 | research (domain-anchor) | product | Owners will not maintain precise inventory — does the resource-state model tolerate approximate state? | resolved | tech adopts coarse decrement + one "anything run out?" prompt; precision is a non-goal (domain-anchor). | 1 |
| OQ-2 | product (scope guard) | controller | `intent:cap.external-fulfillment` proposed — is it in appetite? | surfaced | **Surfaced at G1.5** (out-of-appetite is a value/scope call, not referent-settled). Human rejected. Triggered cascade-invalidation of `screen:fulfillment` + `service:fulfillment`. | 2 |
| OQ-3 | ux (inventory-screens) | tech | The learning-review screen implies a gated Memory write — what backs it, and is it safe? | resolved | **The answer-each-other ripple.** security lens fired: unapproved input writing to agent memory = prompt-injection self-modification (OWASP LLM-01/08). Routed to product -> `decompose-intent` defined "what makes a learning approvable + who audits" -> tech added an approval aggregate + audit log -> ux added `screen:audit-view` -> voice wrote approval/audit copy. Ripple settled. | 2->3 |
| OQ-4 | security/compliance lens | controller | Single-owner identity — is any multi-user/sharing path in MVP? | resolved | No (domain-anchor OOS register: multi-user collaboration is out-of-MVP). Referent-settled; not surfaced. | 1 |
| OQ-5 | tech | product | Does "carry-over" affect both next-cycle planning and resource decrement? | resolved | Yes — carry-over is first-class (domain-anchor); both the plan-service and store-service consume it. | 3 |

**Audit of the queue at G2:** 0 `open`, 0 `routed`. One row `surfaced` (OQ-2, the
value/scope call the predicate correctly routed to the human, not a stall). All others
`resolved` with a cited referent. Saturation rule's OQ clause is satisfied.
