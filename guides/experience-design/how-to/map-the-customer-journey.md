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

## What you will run

| Skill | What it produces | Needed? |
| --- | --- | --- |
| `journey-mapping` | A journey map: outcome phases, emotions, pains, and a proposed screen list. | Required |
| `service-blueprint` | A blueprint connecting frontstage actions to backstage and support work. | Optional |
| `process-mapping` | A SIPOC, as-is and to-be swimlanes, and the delta between them. | Optional |
| `experience-status` | A read-only report of what design artifacts already exist. | Optional |

Prompts go into an AI agent session with this pack installed — the same session
throughout. In every path below, `<output_dir>` is the design output directory
this pack is configured to write to, and `<slug>` is the short name you give
this piece of work.

<!-- rung: packs/experience-design/JOURNEY.md -->

## Run `journey-mapping` — the journey map

**You type:**
<!-- rung: JOURNEY stage 1 -->

```
Map the journey for a new account owner who wants to connect their first data source. The current experience breaks at setup.
```

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

**Where it lands:** `<output_dir>/journeys/<slug>.md`.
<!-- rung: journey-mapping SKILL.md -->

**What it looks like:**
<!-- rung: packs/experience-design/.apm/skills/journey-mapping/assets/journey-map-template.md -->

```markdown
---
type: customer-journey
slug: <slug>
persona: <persona-name-or-role>
outcome: <the outcome the customer is trying to reach>
surface: <responsive-web | iOS | Android | cross-platform>
---

# Journey: <title>

**Persona:** <who the customer is and the relevant context>
**Outcome:** <what done looks like for the customer>
**Surface:** <the platform/surface this journey is designed for>
**Trigger:** <what initiates the journey — the first action or event>
**End state:** <what the customer has achieved when the journey is complete>

---

## Stage 1: <stage name>

| Row | Content |
|-----|---------|
| **Actions** | <what the customer does — frontstage, in the customer's words> |
| **Emotions** | <how the customer feels; mark valence: positive / neutral / negative> |
| **Pains** | <friction, confusion, or gaps — in the customer's words> |
| **Opportunities** | <what would change if the pain were addressed — solution-independent> |
```

*The agent replaces every `<…>`. This is the opening of the template the skill writes from; the artifact continues in the same shape.*

## Run `service-blueprint` — the backstage blueprint

**You type:**
<!-- rung: service-blueprint SKILL.md -->

```
Blueprint the people, services, and systems behind this customer journey.
```

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

**Where it lands:** `<output_dir>/blueprints/<slug>.md`.
<!-- rung: service-blueprint SKILL.md -->

**What it looks like:**
<!-- rung: packs/experience-design/.apm/skills/service-blueprint/assets/service-blueprint-template.md -->

```markdown
---
type: service-blueprint
journey: "<journey name>"
slug: "<kebab-case-slug>"
date: "<YYYY-MM-DD>"
---

# Service Blueprint: <Journey Name>

## Summary

**Journey:** <one-sentence description of the customer journey this blueprint covers>
**Scope:** <start stage> → <end stage>
**Surfaces / channels:** <web | mobile | in-person | …>

---

## Blueprint

<!-- Column headings = journey steps (one per stage/touchpoint).
     Fill each row for every column. Leave no frontstage cell without
     checking the backstage row — a blank backstage against a frontstage
     action is a named gap (see "Column gaps" below). -->

| Row | Step 1: <name> | Step 2: <name> | Step 3: <name> | … |
| --- | --- | --- | --- | --- |
```

*The agent replaces every `<…>`. This is the opening of the template the skill writes from; the artifact continues in the same shape.*

## Run `process-mapping` — the internal process map

**You type:**
<!-- rung: process-mapping SKILL.md -->

```
Map the internal process that supports this experience, from its trigger to its operational outcome.
```

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

**Where it lands:** `<output_dir>/processes/<slug>.md`.
<!-- rung: process-mapping SKILL.md -->

**What it looks like:**
<!-- rung: packs/experience-design/.apm/skills/process-mapping/assets/process-flow-template.md -->

```markdown
---
type: process-flow
process: "<L3 process name>"
slug: "<kebab-case-slug>"
date: "<YYYY-MM-DD>"
---

# Process Map: <L3 Process Name>

## SIPOC

<!-- Bound the process before drawing any swimlane.
     Suppliers and Customers here are internal process participants,
     not the end customer (that is the journey map's domain). -->

| Suppliers | Inputs | Process | Outputs | Customers |
| --- | --- | --- | --- | --- |
| <who/what provides the key inputs — teams, systems, external parties> | <what arrives at the start — documents, data, requests> | **<L3 process name>** | <what the process produces — deliverables, decisions, state changes> | <who receives the output — teams, systems, downstream consumers> |

---

## As-is swimlane

<!-- L4 activities across actor lanes.
     Each subgraph is one actor lane.
     Use decision nodes (diamond shape in mermaid: {Decision?}) for gateways.
```

*The agent replaces every `<…>`. This is the opening of the template the skill writes from; the artifact continues in the same shape.*

## Run `experience-status` — a read of where you are

**You type:**
<!-- rung: experience-status SKILL.md -->

```
Show the current design-thread status.
```

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

**What it looks like:**
<!-- rung: authored -->

```markdown
# Current design-thread status
## Existing artifacts
## Missing artifacts
## Recommended next skill
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Where this leads

**Next:** [Derive the screen flow](derive-the-screen-flow.md).
<!-- rung: authored -->

**Go deeper:** `packs/experience-design/.apm/skills/journey-mapping/SKILL.md`
<!-- rung: authored -->
