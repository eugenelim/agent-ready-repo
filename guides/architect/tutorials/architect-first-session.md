---
title: Your first architecture session
summary: Complete a bounded, read-only survey of an existing repository and choose the first evidence-backed drill-down.
pack: architect
kind: tutorial
---

# Your first architecture session

You will finish with a corrected current-state map, evidence coverage, an
attention heat map, and one selected next investigation. Start with this exact
request:

```text
Assess architecture and provide an action plan in survey mode, stopping after the attention heat map without creating files.
```

The survey reads the repository but does not run its code or change it. You make
two decisions: whether the conceptual map is right, and which hotspot deserves
deeper evidence.

**Prerequisite:** the `architect` pack is installed.

## 1. Read the assessment charter

The first response should bound the repository or system, name
baseline/understanding as the primary intent, select survey mode, and list what
the agent can read. It should say whether it found an in-repo or private
enterprise knowledge surface.

You should not see a score, defect list, or rewrite plan yet.

## 2. Correct the conceptual map

The agent inspects documentation, source, tests, manifests, CI/CD, deployment
definitions, schemas, configuration, operations files, and current local
history where available. It then describes context, runtime/deployables,
modules/capabilities, data, interactions, delivery/operations, and trust or
identity boundaries.

At **Map checkpoint**, compare the model with what you know. Correct a boundary
in plain language:

> The worker and API are separate deployables, but they share the same database.

If the map is accurate, reply `continue`.

The assessment must record your correction or acceptance before it focuses the
investigation.

## 3. Choose where to look deeper

Next you see an attention heat map by system area. It keeps consequence,
pressure, coupling or concentration, verification weakness,
operational/data/security exposure, and confidence separate. The legend should
say that heat selects drill-down priority; it is not proof of a defect or
severity.

Each proposed hotspot should explain its architectural role, raw signals,
counter-evidence, affected journey or quality scenario, unknowns, and the next
check. At **Focus checkpoint**, redirect the set or reply `continue`.

Because this tutorial asked for survey mode, the agent now stops. It should call
the hotspots hypotheses, not completed findings, and report:

`Result: chat only; no file was created.`

## 4. Verify the result

Your completed survey contains:

- a bounded assessment charter;
- a conceptual model that reflects your correction;
- a status for every required evidence surface, including missing ones;
- an attention heat map with raw dimensions;
- bounded hotspot cards and recommended drill-downs;
- coverage limits and the next human decision.

It fails this tutorial if it returns only a folder map, dependency list,
compliance checklist, code-smell inventory, or confident action plan without
investigation.

## 5. Continue with one hotspot

Pick a hotspot and ask for standard depth:

> Continue in standard mode. Investigate H-2, trace the normal, side-effect, and
> failure/recovery paths, then propose only actions supported by findings.

The agent asks before any executable check, private knowledge query, runtime
access, experiment, or write. When the current-state evidence points to a
future-state choice, move to [Shape an architecture concept](../how-to/shape-an-architecture-concept.md).
If you want a durable normative foundation rather than an assessment, follow
[Create and use your `reference.md`](create-your-reference-architecture.md) as a
separate journey.

## What you have now

You have a chat-only survey with a corrected current-state map, evidence
coverage, and selected hotspots. Choose one hotspot for standard-depth
investigation, or begin a separate reference-architecture journey.
