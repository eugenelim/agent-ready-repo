# Process mapping — method and grounding

How to produce an internal business process map that bounds the process first,
captures both as-is and to-be states, and surfaces the waste that motivates the
improvement. This page points to the recognized standards and explains the
load-bearing mechanics; it reprints no framework values, PCF category text, or
BPMN XML.

## APQC levels

The APQC Process Classification Framework (PCF) is the vocabulary for naming
what level a process map operates at. Consult the PCF directly at
[apqc.org/pcf](https://www.apqc.org/pcf) — this skill borrows the level
vocabulary without reprinting the framework.

The five APQC levels, from coarsest to finest:

- **L1 Category** — the broadest grouping (e.g. Develop and Manage Products
  and Services).
- **L2 Process Group** — a cluster of related processes within a category.
- **L3 Process** — the named flow: a trigger event, a defined outcome, the
  roles involved, and the high-level steps. **This is the anchor level for
  this skill.** A good L3 scope fits on one swimlane diagram and delivers one
  meaningful outcome.
- **L4 Activity** — the cross-functional handoffs and decision gates within an
  L3 process. **This is the swimlane content.** An L4 activity belongs to one
  actor lane and has a clear input (what arrives), a clear output (what leaves),
  and optionally a decision gate (a binary or multi-way branch).
- **L5 Task** — the individual operations within an L4 activity: keystrokes,
  system lookups, checkbox confirmations. **L5 is SOP and work-instruction
  territory; it is out of scope for this skill.** Stop at the handoff between
  actors, not the sub-steps within one actor's work.

**Why anchor on L3 → L4.** L3 is the grain at which a process has a name a
business stakeholder recognises ("handle a warranty claim", "onboard a new
supplier"). L4 is the grain at which cross-functional handoffs are visible —
which is where the waste and the improvement levers are. L2 is too coarse for
swimlane design; L5 is too fine for strategic analysis.

## SIPOC scoping

Before drawing any swimlane, build the SIPOC table. SIPOC (Suppliers, Inputs,
Process, Outputs, Customers) is the bounding frame for the L3 process. It
answers: what starts this process, what does it consume, what does it produce,
and who receives the output? Getting these right prevents scope creep
(including adjacent processes) and scope truncation (stopping before the real
outcome).

| Column | What to fill in |
| --- | --- |
| **Suppliers** | Who or what provides the key inputs — internal teams, systems, external parties |
| **Inputs** | What arrives at the start of the process — documents, data, requests, physical materials |
| **Process** | The L3 process name (one line — this is the SIPOC's spine) |
| **Outputs** | What the process produces — the deliverables, decisions, or state changes |
| **Customers** | Who receives the output — internal teams, external customers, downstream systems |

The SIPOC is the agreement surface: before mapping a step, you know whether it
is inside or outside the process boundary. A step that uses an input not in the
Inputs column, or produces an output not in the Outputs column, is either
out of scope or a gap to name.

## Capture methods

Synthesize the as-is process from existing documents first, then validate with
SMEs. Document analysis is faster, produces fewer confirmation biases, and
surfaces conflicts between how the process is *described* and how it is *done*.

**Document analysis (primary).** Read job aids, SOPs, work instructions, policy
documents, and system configuration guides. For each step, note: who owns it,
what triggers it, what it produces, and what system or tool it runs in. Flag
cross-source conflicts explicitly — where two documents describe the same step
differently, surface the conflict rather than silently resolving it.

**SME validation.** After the document-derived draft, validate with a subject
matter expert using one of three formats, chosen by the process type:

- **Process walkthrough (default).** Walk through the draft swimlane with the
  process owner or a practitioner step by step. Ask "is this accurate?" and
  "what does actually happen here?" at each handoff and decision gate. Resolve
  conflicts from the document analysis.
- **JAD session (multi-stakeholder or cross-department).** When the process
  crosses multiple teams whose representatives need to agree on the boundary
  and the as-is state before analysis can start, run a Joint Application Design
  session with a facilitator and representatives from each actor lane. Joint
  Application Design is an established elicitation technique defined in the
  BABOK (see below).
- **Gemba walk (high-exception or hands-on process).** When the process is
  physical, involves high rates of exception-handling, or differs significantly
  from what the documentation describes, observe the process as it runs — go to
  where the work happens. Document what is actually done, not what the SOP says
  should be done.

For the BABOK (Business Analysis Body of Knowledge) elicitation techniques
framework, consult the International Institute of Business Analysis at
[iiba.org/babok](https://www.iiba.org/babok-guide/).

## Swimlane and APQC levels

The swimlane flow maps L4 activities across actor lanes. The notation borrows
from BPMN 2.0 (OMG / ISO 19510, see
[omg.org/spec/BPMN](https://www.omg.org/spec/BPMN/)) without reprinting BPMN
XML — the swimlane is authored in mermaid, which gives a markdown-native
diagram at BPMN vocabulary fidelity.

BPMN vocabulary used in this skill:
- **Lane** — one actor (role, team, or system). All activities owned by that
  actor live in its lane.
- **Task** — an L4 activity node: one action with one owner.
- **Gateway** — a decision point: a binary (yes/no) or multi-way branch.
  Named with the question being decided.
- **Sequence flow** — an arrow from one node to the next, representing the
  handoff (the transfer of a work item from one step or actor to the next).

This skill authors diagrams in mermaid `flowchart` syntax with `subgraph`
lanes per actor. Full BPMN XML and metric-rich Value Stream Maps are BPM-tool
territory (e.g. Signavio, Bizagi, Lucidchart) — they are not agent-producible
as markdown. Cross-functional flowchart conventions follow the same lane/gateway
vocabulary and are referenced in the same BPMN standard.

## As-is / to-be and the delta table

A process map earns its analytical value from the side-by-side comparison of
the current state and the target state. The as-is captures what happens today;
the to-be designs what should happen. The delta table is the bridge between
them — it is the analytical output, not just the diagram.

**As-is** — the current process, mapped without idealisation. Include the
handoffs that cause delay, the decision gates that loop back unnecessarily, and
the actors who receive work that doesn't match their role. These are the waste
sources; they belong in the pain/waste register (see below), not corrected
silently.

**To-be** — the target process, designed to eliminate or reduce the wastes
identified in the as-is. Name every structural change: a handoff eliminated
(two steps merged or automated), a decision gate moved earlier (preventing
downstream rework), an actor reassigned (right work, right role).

**Delta table.** For each step or handoff that changes between as-is and to-be,
record a row in the delta table:

| Step | As-is | To-be | Rationale |
| --- | --- | --- | --- |
| The L4 activity name | What happens today | What should happen | Why the change removes waste or improves the outcome |

Steps that are unchanged need not appear in the delta table — only changes.

## Pain/waste register

The pain/waste register bridges the as-is to the to-be. For each pain or waste
source identified in the as-is swimlane, record:

- **Location** — which handoff or step it occurs at (actor lane + step name)
- **Pain / waste type** — the nature of the friction: delay (waiting for
  information or approval), rework (a downstream step returns work to a
  preceding step), duplication (the same information entered in multiple
  systems), handoff loss (information lost or distorted at a transfer), or
  exception volume (a step generates frequent exceptions that require manual
  resolution)
- **Impact** — the observable effect (what it costs the process: time, quality,
  customer outcome, or operator burden)
- **To-be change** — which to-be change addresses this pain (maps to the delta
  table)

The register is the justification for every to-be change. A to-be change
without a pain/waste register entry is either a preference without a basis or
a missing entry.
