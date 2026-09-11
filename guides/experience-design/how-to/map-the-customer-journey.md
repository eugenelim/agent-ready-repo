---
title: Map the customer journey
summary: Map the customer outcome, its supporting service and process context, and the current design-thread position.
pack: experience-design
kind: how-to
order: 1
---

# Map the customer journey

**Step 1 of 5 — Map the customer journey**

Start with the customer outcome and the points where the experience breaks. This stage produces the outside-in map that frames the rest of the thread.

**You need:** a user, their intended outcome, and the surface you are designing.

*Skipping costs:* later choices rest on an untested account of the customer’s path.

**Concepts:**

- [The experience thread](../explanation/the-experience-thread.md) explains the customer journey, screen flow, and shared quality floor.

Service blueprinting and process mapping run in parallel with this stage. They are useful context, not gates for moving to the screen flow.

#### Run `journey-mapping`

**You type:** `journey-mapping` — describe the user, the goal, and where the current experience breaks down.
<!-- rung: JOURNEY stage 1 -->

**Agent returns:**

> **Agent:** a journey map with stages, actions, emotions, pains, opportunities, and a proposed screen list.
<!-- rung: JOURNEY stage 1, separately attributed from your request -->

**Output varies** with the user, outcome, evidence, and surface.
<!-- rung: authored -->

**You decide:** approve the journey map before screens are derived from it.
<!-- rung: JOURNEY stage 1 -->

**Check (grounded):** Can you trace the proposed screens to the stated customer outcome and its failure modes?
<!-- rung: authored -->

**If it fails:** correct the user, outcome, or failing journey moment, then re-prompt with that case.
<!-- rung: authored -->

**You now hold:** `<output_dir>/journeys/<slug>.md`.
<!-- rung: SKILL.md -->

**Expect these headings:**

- `Journey: <title>`
- `Stage 1: <stage name>`
- `Stage 2: <stage name>`
- `Stage 3: <stage name>`
- `Frontstage actions`
- `Emotional arc`
- `Handoff notes`

*Source:* `../../../packs/experience-design/.apm/skills/journey-mapping/assets/journey-map-template.md`
<!-- rung: asset template -->

#### Run `service-blueprint`

**You type:** `Blueprint the services behind this customer journey.`
<!-- rung: SKILL.md description -->

**Agent returns:**

> **Agent:** a service blueprint that connects frontstage actions to backstage and support work.
<!-- rung: SKILL.md -->

**Output varies** with the journey touchpoints and named services.
<!-- rung: authored -->

**You decide:** approve the named service boundaries only if they are useful for later architecture work.
<!-- rung: authored -->

**Check (observable):** Does each frontstage action have enough backstage context to explain how it is supported?
<!-- rung: authored -->

**If it fails:** add the missing touchpoint or service context and re-prompt.
<!-- rung: authored -->

**You now hold:** `<output_dir>/blueprints/<slug>.md`.
<!-- rung: SKILL.md -->

**Expect these headings:**

- `Service Blueprint: <Journey Name>`
- `Summary`
- `Blueprint`
- `Column gaps`
- `Named backstage services`
- `Hand-off`
- `Open questions`

*Source:* `../../../packs/experience-design/.apm/skills/service-blueprint/assets/service-blueprint-template.md`
<!-- rung: asset template -->

#### Run `process-mapping`

**You type:** `Map the internal process behind this experience.`
<!-- rung: SKILL.md description -->

**Agent returns:**

> **Agent:** an as-is and to-be process map for the internal operation.
<!-- rung: SKILL.md -->

**Output varies** with the actors, handoffs, and operational evidence.
<!-- rung: authored -->

**You decide:** choose whether the internal process is in scope for this design thread.
<!-- rung: authored -->

**Check (falsifiable):** Can a named actor and decision gate explain every material handoff?
<!-- rung: authored -->

**If it fails:** supply the missing actor, activity, or exception and re-prompt.
<!-- rung: authored -->

**You now hold:** `<output_dir>/processes/<slug>.md`.
<!-- rung: SKILL.md -->

**Expect these headings:**

- `Process Map: <L3 Process Name>`
- `SIPOC`
- `As-is swimlane`
- `As-is pain/waste register`
- `To-be swimlane`
- `As-is → to-be delta`
- `Seams`
- `Open questions`

*Source:* `../../../packs/experience-design/.apm/skills/process-mapping/assets/process-flow-template.md`
<!-- rung: asset template -->

#### Run `experience-status`

**You type:** `Show the current design-thread status.`
<!-- rung: SKILL.md description -->

**Agent returns:**

> **Agent:** a read-only account of what design artifacts exist, what is missing, and which skill fits next.
<!-- rung: SKILL.md -->

**Output varies** with the configured design output directory.
<!-- rung: authored -->

**You decide:** whether the reported state matches the work you intend to continue.
<!-- rung: authored -->

**Check (observable):** Does the status distinguish existing artifacts from missing ones?
<!-- rung: authored -->

**If it fails:** configure the output location or name the artifact you expect, then re-run it.
<!-- rung: authored -->

**Writes no artifact.** It reports to the chat and leaves nothing on disk, so there is no path to hold.
<!-- rung: SKILL.md -->

**Expect these headings:**

- `Current design-thread status`
- `Existing artifacts`
- `Missing artifacts`
- `Recommended next skill`

*Source:* `authored`
<!-- rung: authored; this skill reports status rather than writing a document -->

**Next:** [derive the screen flow](derive-the-screen-flow.md).
<!-- rung: authored -->
