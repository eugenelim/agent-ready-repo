# Product & design artifact inventory

The artifacts the autonomous product-team flow produces/consumes, vision → spec.
Status: ✓ exists · ✦ new (to build) · ⊕ enhance existing. The target state is that
each artifact has a producing skill and a named consumer (**no orphans**) — the
traceability lint (RFC-0048 D6) enforces it once the `Discovery:` up-edge and the
discovery `type:` markers land (RFC-0048 § Amendments DRIFT-G); the persona row's
producer was reconciled to elicit-inline (DRIFT-F). Agents produce design **intent
specifications** (markdown/mermaid/tables), NOT pixel comps — that's what makes
them agent-producible and build-consumable (design-craft's own framing).

## Product artifacts (product-engineering + core)

| Artifact | What it is | Skill | Consumed by |
| --- | --- | --- | --- |
| **Intent** (level-tagged) | outcome+opportunity at product-vision / strategy / capability / feature; the recursive backbone | frame-intent ✓ | decompose-intent; rendered → brief |
| **Opportunity tree** | the intent recursion viewed whole = the OST (outcome → opportunities → solutions → assumption tests) | frame+decompose ✓ | human at G1; orients discovery |
| **Assumption test** | riskiest assumption · kill condition · prototype-approach · survive/kill verdict | de-risk-intent ✓ | G1.5; reshapes intent if killed |
| **Domain Framing** | real-life activity grounding + best practice + naive-failure modes + brownfield current-system half | frame-domain ✦ (wraps research applied ✓) | UX + tech lenses; correctness/anti-hallucination |
| **Scope Boundary** | MVP/appetite scope + out-of-scope register; the upstream G1.5 scope-creep guard | frame-domain ✦ (same skill, second artifact) | scope-creep guard; **brief inherits/refines at G3** |
| **Persona** | who it's for; the referent taste + UX fit derive from | *elicited inline by the first consumer* (not a separate produced artifact in the current child set — RFC-0048 § Amendments DRIFT-F; the frame-domain spec excludes it; promoting it to a produced artifact is a deferred option) | aesthetic-direction; map-journey |
| **Outcomes & metrics** | North Star + input metrics | frame/decompose ✓ | traceability root; post-build review |
| **Brief** | the core handoff: outcome, metrics, scope/non-goals, appetite, stories, spec map | decompose-intent writes ✓; template core ✓ | receive-brief |
| **Spec** | per-feature contract (Shape + LLD + ACs) — the product/tech boundary artifact | new-spec ✓ | work-loop |

## Design / experience artifacts (experience pack = renamed design-craft + connective + content)

**Connective (UX flow / service design) — the missing layer:**

| Artifact | What it is | Skill | Consumed by |
| --- | --- | --- | --- |
| **Journey map** | stages × actions / emotions / pains / opportunities (frontstage) | map-journey ✦ | inventory-screens; blueprint-service |
| **Service blueprint** | frontstage / line-of-visibility / backstage / support — the screen↔service tie | blueprint-service ✦ | architect (backstage→services); spec LLD |
| **Screen inventory + state matrix** | the screen list; per-screen states (empty/loading/error/success/permission) | inventory-screens ✦ (states defer to handle-all-states ✓) | design-craft skills; voice-and-microcopy |

**Craft (existing design-craft skills):**

| Artifact | What it is | Skill | Consumed by |
| --- | --- | --- | --- |
| **Aesthetic direction** | visual tone/mood — **grounded** in persona + precedent + standards (the taste reference) | aesthetic-direction ⊕ (ground it) | design-critique; layout |
| **Design-system foundations** | tokens (color/type/space) + component vocabulary; points to W3C tokens | design-system-foundations ✓ | layout; build |
| **Layout & IA** | sitemap/nav + per-screen layout structure | layout-and-information-architecture ✓ | build; design-critique |
| **Design critique** | findings vs quality floor + **grounded taste reference** (fresh-context) | design-critique ⊕ (taste mode) | the producing lens (iterate) |
| **Quality-floor checklist** | handle-all-states · accessibility floor · reduced-motion | design-craft shared ✓ | every screen design |

**Content design** (`voice-and-microcopy` is **resident in `product-engineering`**, not the
`experience` pack — RFC-0050 D5/§ cross-pack edit; listed here for the seat, not the home):

| Artifact | What it is | Skill | Consumed by |
| --- | --- | --- | --- |
| **Voice characterization** | product voice axes | voice-and-microcopy ✓ | copy deck; design-critique |
| **Copy deck / microcopy** | per-screen-state strings, blame-free + actionable | voice-and-microcopy ✓ (wire to screen inventory ⊕ GAP-C1) | build |

## Handoff boundary (design intent → tech)

Two edges cross into the tech packs (architect / contracts / core) — not enumerated here:
- **Service blueprint → architect** — each backstage service becomes C4 + a contract (api-contract / event-contract).
- **Brief + blueprint + screen inventory → spec** — the spec's LLD references them (close GAP-O8 so they don't orphan).

## Cross-cutting gate artifacts (wrap the above, not product/design per se)

- **Coverage/pre-mortem record** — the self-coverage gate output (domain-grounding table, pre-mortem, taxonomy walk, saturation declaration, fresh-context findings). Gates "converged."
- **Decision brief** — at G2, the journey + screen inventory + arch sketch + tension/assumption ledger rendered for human ratification.

## Deliberately NOT artifacts (MVP discipline)

- No encyclopedic PRD — the **brief** is the lean PRD.
- No pixel comps / Figma files — agents author design **intent specs**; a human designer or UI-codegen realizes them.
- No competitive teardown unless the taste loop needs a precedent refresh.
- No sprint backlog / RACI / launch-GTM brief — human-coordination overhead an autonomous team doesn't need.
