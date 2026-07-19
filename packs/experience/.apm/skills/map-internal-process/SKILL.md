---
name: map-internal-process
description: Use when a team needs to understand, document, or improve how an internal business operation works — mapping an APQC L3 process end-to-end as a swimlane flow with as-is and to-be states, a SIPOC scoping table, and a pain/waste register. Triggers on "map our internal process", "document this business process", "what does our current process look like", "as-is to-be process", "process improvement", "how does this workflow actually work", "swimlane diagram for this process", "map the claims process", "map the order fulfilment flow". This is the inside-out operations sibling of `map-customer-journey`. Do NOT use to map what a customer experiences (use `map-customer-journey`), to blueprint how screens tie to backing services (use `blueprint-service`), or to sequence screen transitions (use `map-screen-flow`). Does NOT carry a platform/surface axis — it is actor/swimlane-shaped, not device-shaped.
---

# Skill: map-internal-process

Produces an **internal business process map** — the inside-out sibling of `map-customer-journey`. Where the journey skill maps what a customer experiences frontstage and outside-in, this skill maps what the organisation does backstage and inside-out: the actors, the handoffs, the decision gates, the waste, and the target state. The method is anchored on the APQC L3 process (named flow: trigger → outcome → roles → steps), decomposed to L4 activities (cross-functional handoffs and decision gates — the swimlane content). L5 tasks are work-instruction territory and are out of scope here. See `references/process-mapping.md`.

**Inputs:** job aids, SOPs, or work instructions (primary); SME knowledge elicited inline when no documents are present. Both are standalone-useful without upstream design artifacts. **Consumed by:** `product-engineering`'s `frame-intent` skill — this map is the producer of the "current-state process map" input that `frame-intent` uses as a brownfield constraint. **Cross-reference:** when the process being mapped is triggered by a customer action, cross-reference the service blueprint by name (the `blueprint-service` output for the same journey).

## When to invoke

Confirm all three before drafting; if any fails, resolve it first.

1. **There is a named process to map** — identify the L3 process by its trigger (what starts it), its outcome (what done looks like), and its primary actors. If the team cannot name a trigger and an outcome, elicit them inline before proceeding.
2. **The scope is internal operations** — customer-facing stage flows belong to `map-customer-journey`; the screen↔service tie belongs to `blueprint-service`. This skill covers processes that span actor lanes, may have no customer-visible layer (e.g. "run the monthly close", "process supplier invoices"), or are being captured as a constraint on the solution. **This is your own org's operations, inside-out — the as-is/to-be of how *you* do it.** For *world best-practice, outside-in* — *"the best way to do X, end to end"* for any domain — use `desk-research`'s `methodology` shape instead. The two honestly share a SIPOC scope frame and a process-discovery spine; the boundary rests on source + direction (your ops vs best practice anywhere), so map here when the subject is your own process and route to the methodology shape when it is the general method.
3. **No current process map exists for this L3 process** — if one exists, you are amending it, not starting fresh. Check for an existing artifact at the path resolved in step 1 of the procedure.

## Procedure

1. **Resolve and surface the output path.** Resolve `<parent>` by the canonical three-tier order — `agentbundle-layout.toml`'s `[experience]` table (repo-root file first, user-profile file second) → the pack default `docs/design` → discover-by-marker (scan for the artifacts' frontmatter `type:`). Derive the path as `<parent>/processes/<slug>.md`. Resolve to a full absolute path (`~`-expand, realpath-resolve, reject `..` escapes); a repo-root-sourced `parent` that resolves outside the repo tree is untrusted-origin — confirm before writing. **Surface the resolved path before the first write.** Create the `processes/` directory lazily on first write. See `references/agentbundle-layout.md` for the full schema.

2. **Build the SIPOC.** Before drawing any swimlane, scope the process with a SIPOC table — Suppliers, Inputs, Process (the L3 name), Outputs, Customers. This bounds the process boundary and prevents scope creep into adjacent processes. Load `references/process-mapping.md` § SIPOC scoping.

3. **Elicit or confirm the source material.** Synthesize from job aids, SOPs, and work instructions when present (document analysis — flag cross-source conflicts where the same step is described differently in different documents). When no documents are present, elicit from an SME: use a process walkthrough (default), a JAD session (multi-stakeholder or cross-department process), or a gemba walk (high-exception or hands-on process). Load `references/process-mapping.md` § Capture methods. When the elicitation is a multi-stakeholder session, run it as a **facilitated workshop** — generate silently before discussing, keep the room small, and synthesize before momentum fades; the shared method is in `../map-customer-journey/references/facilitation.md`.

4. **Identify the actors and swimlanes.** Name every role, team, or system that owns at least one L4 activity in this process. Each becomes a lane in the swimlane diagram. Keep lanes to the fewest needed — merge two roles into one lane only when they never have a handoff between them.

5. **Map the as-is state.** For the current process: draw the APQC L4 activities (actions, handoffs, decision gates) across actor lanes as a mermaid flowchart with `subgraph` lanes. Mark decision gates explicitly (a diamond in BPMN vocabulary; a conditional branch in mermaid). Identify pains and waste at each handoff — the friction, delays, rework, or information gaps — and record them in the pain/waste register. Load `references/process-mapping.md` § Swimlane and APQC levels.

6. **Map the to-be state.** Design the target process: which handoffs are eliminated, automated, or resequenced; which decision gates move; which actors change. Draw the to-be swimlane. Build the as-is→to-be delta table (`| Step | As-is | To-be | Rationale |`) — this is the primary analytical output, not just the diagram.

7. **Write the artifact.** Use the template in `assets/process-flow-template.md`. Write to the resolved path with frontmatter `type: process-flow`. Confirm the written path matches the path surfaced in step 1.

8. **Name the seams.** At the end of the map, add a `## Seams` section. If the process is customer-triggered, name the `blueprint-service` artifact that covers the customer-facing layer of the same journey. Name `frame-intent` (in the `product-engineering` pack) as the consumer of this map — it uses it as a brownfield constraint input.

## Anti-patterns to refuse

- **Confusing frontstage and backstage.** This skill maps what the organisation does inside-out. What the customer experiences is `map-customer-journey`'s domain. If a swimlane step is something the customer does, it belongs in the journey map, not here.
- **Descending to L5 tasks.** L5 tasks are SOP and work-instruction territory. The swimlane works at L4 activity grain — cross-functional handoffs and decision gates, not the individual keystrokes or click sequences that make up a task. Stop at the handoff, not the sub-step.
- **Reprinting APQC framework text or full BPMN XML.** Point to APQC PCF and BPMN 2.0 (OMG / ISO 19510) as standards; do not reproduce the PCF table, process categories, or BPMN element XML. The method borrows the vocabulary; the source stays authoritative.
- **Skipping the SIPOC.** A swimlane without a SIPOC has no agreed boundary. The SIPOC is what prevents the map from sprawling into adjacent processes or stopping short of the real outcome. Build it before the first lane.
- **Producing only a diagram without the delta table.** The as-is→to-be delta table is the analytical output — the reason the map earns its keep. A swimlane alone without the delta table leaves the improvement logic implicit.
- **Skipping the output-path surface step.** The resolved path is declared before the first write, every time.
- **Adding a platform/surface axis.** This skill is actor/swimlane-shaped, not device-shaped. Surface axis (`responsive-web | iOS | Android`) has no meaning here — the process actors and handoffs do not change by device. Do not add one.
