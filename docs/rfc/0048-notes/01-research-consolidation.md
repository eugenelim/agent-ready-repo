# Autonomous product-team overlay — consolidated research

Research feeding a prospective RFC: enhance every pack so the catalogue acts as
an autonomous product team, vision → shipped code, with gates that let agents
iterate as long as possible and surface to the human only at critical points.

## The two findings that constrain the design

1. **MAST (UC Berkeley, 2025; 1,642 traces, 7 frameworks): a single agent that
   can hold the task in one context almost always beats a coordinating team.**
   Multi-agent failure rates 41–86%; the largest failure cluster is system-design
   (44%). Multi-agent is net-positive *only* when the task genuinely exceeds one
   context window or when parallelism saves enough wall-clock to pay the
   coordination overhead. Coding is *not* very parallelizable (Anthropic research
   system: parallel wins for breadth-first independent retrieval, not for build).

2. **What works vs. thrashes.** Typed artifacts on a shared blackboard +
   explicit termination beats freeform chat (MetaGPT typed pub-sub > ChatDev
   freeform). Termination needs a hard cap AND a stability/saturation check
   (ChatDev: two identical outputs = stable, else 10-round cap; MetaGPT: 3 debug
   retries). Human-in-the-loop is first-class in the systems that work (LangGraph
   checkpointers pause at any node; AG2 ManualPattern). CrewAI hierarchical
   auto-manager thrashes (executes all tasks, last-write-wins overwrite).

3. **Roles agent systems consistently MISS:** UX/product design (ChatDev's
   "designer" is name-only; MetaGPT/Devin have none), security review (no system
   instantiates one by default), observability/SRE, eval/QA beyond unit tests,
   stakeholder representation, governance/compliance. Real product teams center
   the trio (PM + design + eng); everything else is satellite/on-demand.

## Industry artifact chain (real names)

Vision → Strategy/OKR → **Opportunity Solution Tree** (discovery) → **Brief /
Shape-Up pitch** → **PRD** + **Figma design** + **journey map / service
blueprint / story map** + **C4 / ADR / OpenAPI** → build → launch.
Human gates: opportunity selection, brief approval, design sign-off, PRD
approval, architecture review, security sign-off, Definition of Ready,
Definition of Done, go/no-go launch. Irreversible (always human): data
migration, public-API breaking change, payment/billing, security-arch change,
regulated-data surface.

The connective tissue best-in-class teams use:
- **Story map** = product↔UX spine (journey backbone × release slices).
- **Service blueprint** = UX↔tech spine (frontstage screen ↔ backstage service
  across the line of visibility). This is the artifact whose whole job is "tie
  screens to tech."
- **Traceability chain:** Outcome → Opportunity → Capability → Journey step →
  Screen + Action → Service/Tool → Contract → Spec → Code. Orphans are defects,
  mechanically lintable (extend receive-brief's spec→brief coverage lint).

## Pragmatic principle (per user steering)

**The deliverable is the human's; the state is the agents'.** Agents coordinate
through a typed blackboard + open-questions queue that needs to be *consistent*,
not pretty. At a gate, that state is *rendered* into a human-readable deliverable
(journey map, screen inventory, decision brief, brief, spec, ADR) for consent
or audit. Keep the human deliverables; don't make agents produce
human-coordination overhead they don't need (sprint backlog, standup, RACI,
launch/GTM brief).

## What the catalogue ALREADY has (reuse as satellite seats)

| Product-team seat | Existing pack/skill |
| --- | --- |
| Strategist / PM (discovery, OST, brief) | product-engineering: frame-intent, de-risk-intent, decompose-intent |
| Analyst / UX researcher | research pack (+ saturation stop-signal in research-project-check) |
| Architect (C4 / ADR / design doc) | architect: architect-design, architect-diagram, architect-review |
| Engineer + delivery gates | core: work-loop, implementer, loop-cohort (supervisor mode = sequential DAG + parallel disjoint fan-out, caps already) |
| QA / eval | quality-engineer |
| Security | security-reviewer (+ security-checklists, operational-safety) |
| UX writer | product-engineering: voice-and-microcopy (words only) |
| Decision scribe | new-adr, new-rfc |
| Build intake | core: receive-brief, new-spec, brief template |

## The genuine missing spine (only two things)

1. **The Experience/design discipline** — the confirmed gap (both research
   streams). Candidate skills:
   - `map-customer-journey` — journey map from outcomes/JTBD.
   - `blueprint-service` — service blueprint (frontstage/backstage); the UX↔tech tie.
   - `map-screen-flow` — screen inventory + per-screen state matrix
     (empty/loading/error/success/permission) from the journey.
   - (`map-story` — story map; likely folds into decompose-intent's slicing.
     Defer until it earns its own skill.)

2. **The convergence engine + gate overlay** — the "tie it together" mechanism:
   - Typed blackboard artifact set + **open-questions queue** (the channel agents
     "answer each other" through).
   - **Traceability lint** over the chain above (orphan = defect).
   - **Saturation stop-signal** (reuse research-project-check pattern) + hard cap.
   - **Gate ladder** G0 Intake / G1 Strategy / **G1.5 Domain&MVP** / G2 Convergence /
     G3 Spec / G4 Build / G5 Ship, with **surfacing predicate**: a gate surfaces iff
     (a) one-way door, (b) irreducible tension logged, (c) stall at cap, (d)
     load-bearing assumption with no evidence — else auto-advance + record decision.
     Consent gates always: G0, G1.5, G2, G5. (Erratum: an earlier draft of this note
     omitted G1.5 and listed consent gates as G0/G2/G5; the canonical ladder is the
     7-gate G1.5-bearing form used in notes 02–05 and RFC-0048 §The ask.)

## Agent topology decision (the answer to "is it time for parallel agents")

Apply MAST. The cross-discipline convergence loop runs in **one context as
skill-lenses** the orchestrator switches between (product / UX / tech / reconcile)
— NOT as subagents arguing, which is exactly the 41–86% thrash case. Spin up
**parallel subagents only where the MAST bar is met**: independent breadth-first
work — per-screen state specs (once inventory frozen), per-service contract drafts
(once service list frozen), per-hypothesis research. That is precisely
work-loop supervisor mode's existing shape, lifted to the artifact altitude.

## Deliberately NOT building (charter + overhead)

- PMM / launch / go-to-market layer (out of a code-building catalogue's charter).
- Data-analyst / instrumentation pack (success metrics already live in the brief).
- Sprint ceremony / RACI / standup analogs (human-coordination overhead).
- A 1:1 agent-per-role org chart (MAST: fewer agents win).

## Key sources

- MAST — Why Do Multi-Agent LLM Systems Fail? https://arxiv.org/pdf/2503.13657
- MetaGPT (ICLR 2024) https://arxiv.org/html/2308.00352v6
- ChatDev https://arxiv.org/html/2307.07924v5
- Anthropic multi-agent research system https://www.anthropic.com/engineering/multi-agent-research-system
- TheAgentCompany (CMU) https://arxiv.org/html/2412.14161v2
- Generative Agents (Park et al., UIST 2023) https://3dvar.com/Park2023Generative.pdf
- SVPG product operating model https://www.svpg.com/the-product-operating-model-an-introduction/
- Torres opportunity solution trees https://www.producttalk.org/opportunity-solution-trees/
- NN/g service blueprints https://www.nngroup.com/articles/service-blueprints-definition/
- Jeff Patton story mapping https://jpattonassociates.com/the-new-backlog/
- Shape Up https://basecamp.com/shapeup/shape-up.pdf
