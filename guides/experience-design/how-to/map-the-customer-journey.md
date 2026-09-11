---
title: Map the customer journey
summary: Map the customer outcome, its supporting service and process context, and the current design-thread position.
pack: experience-design
kind: how-to
order: 1
---

# Map the customer journey

**Step 1 of 5 — Map the customer journey**
<!-- rung: JOURNEY stage 1 -->

**What changes:** The customer outcome, breakpoints, supporting service context, and internal process context become explicit before screens are named.
<!-- rung: JOURNEY stage 1 -->

**What you need first:** A user, their intended outcome, the surface you are designing, and any evidence you already hold.
<!-- rung: journey-mapping SKILL.md -->

*Skipping costs:* Later choices rest on an untested account of the customer’s path.
<!-- rung: JOURNEY stage 1 -->

**Concepts:**
<!-- rung: authored -->

- [The experience thread](../explanation/the-experience-thread.md) explains the customer journey, screen flow, and shared quality floor.

Service blueprinting and process mapping can run in parallel with this stage. They add context; neither is a gate for moving to the screen flow.

#### Run `journey-mapping`

**You type:** `Map the journey for a new account owner who wants to connect their first data source. The current experience breaks at setup.`
<!-- rung: JOURNEY stage 1 -->

**Agent returns:**
<!-- rung: JOURNEY stage 1 -->

> **Agent:** A journey map with stages, actions, emotions, pains, opportunities, and a proposed screen list.

**You push back:**
<!-- rung: journey-mapping SKILL.md -->

> “You made one stage per screen. Regroup these as coarse phases of the customer outcome, then derive screens later.” The agent replaces the screen-shaped stages with outcome phases and keeps the proposed screens separate.

**Output varies** with the user, outcome, evidence level, surface, and surface genre.
<!-- rung: journey-mapping SKILL.md -->

**You decide:** Approve the journey map before screens are derived from it.
<!-- rung: JOURNEY stage 1 -->

**Check (grounded):** Ask whether each proposed screen traces to the customer outcome or a named failure moment; this surfaces screens copied from the current product or added as a wish list.
<!-- rung: JOURNEY stage 1 -->

**Watch out for:** A polished map may present assumed emotions and pains with the same confidence as observed evidence. Check the `evidence-level`; label unsupported lines as assumptions, then correct the user, outcome, or failing moment and re-run the skill.
<!-- rung: journey-mapping SKILL.md -->

**Where it lands:** `<output_dir>/journeys/<slug>.md`, where both bracketed segments are replaced for this project.
<!-- rung: journey-mapping SKILL.md -->

**Expect these headings:**
<!-- rung: packs/experience-design/.apm/skills/journey-mapping/assets/journey-map-template.md -->

- `Journey: <title>`
- `Stage 1: <stage name>`
- `Stage 2: <stage name>`
- `Stage 3: <stage name>`
- `Frontstage actions`
- `Emotional arc`
- `Handoff notes`

#### Run `service-blueprint`

**You type:** `Blueprint the people, services, and systems behind this customer journey.`
<!-- rung: service-blueprint SKILL.md -->

**Agent returns:**
<!-- rung: service-blueprint SKILL.md -->

> **Agent:** A five-row service blueprint connecting evidence of service and frontstage actions to backstage and support work.

**You push back:**
<!-- rung: service-blueprint SKILL.md -->

> “The support system runs in parallel with the employee action, but your column makes it happen afterward. Align both beneath the same frontstage action.” The agent corrects the column without changing the journey sequence.

**Output varies** with the journey touchpoints, screen inventory, named services, and available evidence.
<!-- rung: service-blueprint SKILL.md -->

**You decide:** Approve named service boundaries only when they help the later architecture work.
<!-- rung: authored -->

**Check (observable):** Follow one frontstage action down its column; this surfaces missing employee, system, or support work behind what the customer encounters.
<!-- rung: service-blueprint SKILL.md -->

**Watch out for:** A confident blueprint may invent backstage services when evidence is thin. Notice service names with no source or owner, mark those general-pattern guesses first, and replace them with known context or an open question.
<!-- rung: service-blueprint SKILL.md -->

**Where it lands:** `<output_dir>/blueprints/<slug>.md`, with both bracketed segments replaced for this project.
<!-- rung: service-blueprint SKILL.md -->

**Expect these headings:**
<!-- rung: packs/experience-design/.apm/skills/service-blueprint/assets/service-blueprint-template.md -->

- `Service Blueprint: <Journey Name>`
- `Summary`
- `Blueprint`
- `Column gaps`
- `Named backstage services`
- `Hand-off`
- `Open questions`

#### Run `process-mapping`

**You type:** `Map the internal process that supports this experience, from its trigger to its operational outcome.`
<!-- rung: process-mapping SKILL.md -->

**Agent returns:**
<!-- rung: process-mapping SKILL.md -->

> **Agent:** A SIPOC, as-is and to-be swimlanes, a pain register, and the delta between current and target operations.

**You push back:**
<!-- rung: process-mapping SKILL.md -->

> “You put the customer’s click in an internal swimlane and skipped the SIPOC. Move the customer action back to the journey context and bound this process before drawing lanes.” The agent rebuilds the map around internal actors and handoffs.

**Output varies** with the actors, source material, handoffs, and operational evidence.
<!-- rung: process-mapping SKILL.md -->

**You decide:** Choose whether the internal process belongs in this design thread.
<!-- rung: authored -->

**Check (falsifiable):** Ask which named actor owns each handoff and decision gate; this surfaces orphaned activities and branches with no accountable lane.
<!-- rung: process-mapping SKILL.md -->

**Watch out for:** The map can look complete while mixing customer stages with internal work. Notice customer actions inside actor lanes or a swimlane with no SIPOC boundary; move the former to the journey and add the latter before continuing.
<!-- rung: process-mapping SKILL.md -->

**Where it lands:** `<output_dir>/processes/<slug>.md`, with both bracketed segments replaced for this project.
<!-- rung: process-mapping SKILL.md -->

**Expect these headings:**
<!-- rung: packs/experience-design/.apm/skills/process-mapping/assets/process-flow-template.md -->

- `Process Map: <L3 Process Name>`
- `SIPOC`
- `As-is swimlane`
- `As-is pain/waste register`
- `To-be swimlane`
- `As-is → to-be delta`
- `Seams`
- `Open questions`

#### Run `experience-status`

**You type:** `Show the current design-thread status.`
<!-- rung: experience-status SKILL.md -->

**Agent returns:**
<!-- rung: experience-status SKILL.md -->

> **Agent:** A read-only account of existing journey maps, screen flows, per-screen briefs, and service blueprints, followed by the next fitting skill.

**You push back:**
<!-- rung: experience-status SKILL.md -->

> “The design output is not configured; do not report its artifacts as missing.” The agent changes the result to “not configured,” recommends `journey-mapping`, and leaves the filesystem unchanged.

**Output varies** with the configured design output directory and the artifacts found there.
<!-- rung: experience-status SKILL.md -->

**You decide:** Whether the reported state matches the work you intend to continue.
<!-- rung: authored -->

**Check (observable):** Compare one reported count and path with the configured output directory; this surfaces stale locations and files that do not carry the expected artifact marker.
<!-- rung: experience-status SKILL.md -->

**Watch out for:** “Missing” and “not configured” require different moves. If no output directory is configured, the report says so and stops; run `journey-mapping` to establish it instead of asking this read-only skill to write configuration.
<!-- rung: experience-status SKILL.md -->

**Writes no artifact.** It reports in the agent session and does not change files.
<!-- rung: experience-status SKILL.md -->

**Expect these headings:**
<!-- rung: experience-status SKILL.md -->

- `Current design-thread status`
- `Existing artifacts`
- `Missing artifacts`
- `Recommended next skill`

**Next:** [Derive the screen flow](derive-the-screen-flow.md).
<!-- rung: authored -->

**Go deeper:** `packs/experience-design/.apm/skills/journey-mapping/SKILL.md`
<!-- rung: authored -->
