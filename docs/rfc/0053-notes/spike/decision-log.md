# Decision log — example-assistant

> SPIKE ARTIFACT (RFC-0053 Decision-7 prototype). The typed decision-log slot.
> Schema (canonical field order): `{ts, gate, decision, ratified-by, reversibility-class, rationale}`.
> A decision *record*; it becomes the audit trail the high-stakes / regulated case needs
> (RFC-0048 D1 stakes-density) only with the integrity properties named in RFC-0053
> § Security & integrity contract (append-only · attested ratifier · tamper-evidence ·
> trusted timestamp) — a plain mutable file is not yet an audit trail.
> `ratified-by ∈ human | discovery-lead (auto-advance)`. Consent gates
> are G0, G1.5, G2, G5; the rest auto-advance unless a risk trigger fires.

| ts | gate | decision | ratified-by | reversibility-class | rationale |
| --- | --- | --- | --- | --- | --- |
| r1 | G0 Intake | Read as single-owner agentic app; appetite = small; "secure" + "approved learning" load-bearing | human (consent) | reversible | value origination — only the human can ratify the vision (predicate: value act) |
| r1 | G1 Strategy | Capabilities = task-planning, resource-state, derived-list, approved-learning, identity-security | discovery-lead (auto-advance) | reversible | no scope one-way-door, no logged conflict -> predicate did not fire |
| r1 | G1.5 Domain & MVP | Ratify the approximate-state MVP boundary (precision is a non-goal) | human (consent) | reversible | irreducible MVP-boundary value call; domain-anchor grounded the rest |
| r2 | G1.5 (recovery) | **Reject `intent:cap.external-fulfillment`** as out-of-appetite | human (consent) | reversible | OQ-2 surfaced; out-of-appetite is a scope/value call, not referent-settled. Triggered O11 cascade-invalidation (see loop-trace.md). |
| r3 | Convergence | Approval aggregate + audit log added; `screen:audit-view` created | discovery-lead (auto-advance) | reversible | OQ-3 security ripple resolved by referents (OWASP LLM-01/08) -> no surface needed |
| r4 | G2 Convergence | **Ratify the "what"** — decision-package (journey + screens + arch + ledger); no open conflict to adjudicate | human (consent) | reversible | saturation met (0 open OQ, 0 orphan, full pass clean); the one value/scope call (OQ-2) already adjudicated at G1.5 |
| r4 | G2->G3 | Emit briefs per feature; hand off to work-loop at G3 | discovery-lead (auto-advance) | reversible | backlog decomposed; loop-cohort orders it; work-loop pulls one at a time |

**Note on the cap (O12):** the loop converged at round 4 of a 12-round cap; cost spent
$6.40 of a $25.00 budget. Neither bound was approached. The stall-surfaces-to-human
transition (predicate c) was therefore not exercised on the happy path; it is modelled in
loop-trace.md §"the cap path" against a hypothetical unresolved value-conflict.
