---
title: Frontend Engineering guides
summary: Find the create, retrofit, audit, verification, contract, and evidence workflows used to deliver a frontend surface.
pack: frontend-engineering
kind: explanation
---

# Frontend Engineering guides

Need the shortest path? Say: "Build this dashboard screen from the brief and produce the frontend evidence for release review." Start at the [pack overview](/packs/frontend-engineering/), then open the [frontend engineering journey](/journeys/frontend-engineering/) to see how create, retrofit, audit, and verify work from mode choice through evidence and independent review.

Use this index when you have found the `frontend-engineering` pack and need the next documentation path by task, not by skill name.

## Choose your path

| Current task | Open this | Result |
|---|---|---|
| Confirm what the pack is for | [Pack overview](/packs/frontend-engineering/) | The four jobs, expected outputs, install command, and route into this guide tree |
| See the end-to-end workflow before starting | [Frontend engineering journey](/journeys/frontend-engineering/) | Mode choice, contract approval, implementation or audit path, gates, evidence manifest, and frontend review in order |
| Decide whether a new or changed surface needs a contract | [Write a page or screen contract](how-to/page-screen-contract.md) | A full 12-field contract, proportional subset, or explicit no-contract decision |
| Set or verify performance policy | [Performance targets](reference/performance-targets.md) | Fixed CWV targets, prioritized asset-budget categories, and project-specific numeric-ceiling decisions |
| Audit an existing page or component without writing code | [Run a frontend audit](how-to/run-an-audit.md) | A findings report and baseline evidence manifest for the existing surface |
| Learn the workflow from a small worked example | [Scaffold a component from a screen brief](tutorials/scaffold-a-component.md) | A gate-passing component and completed evidence manifest |
| Look up every skill and the reviewer boundary | [Frontend Engineering Pack reference](reference/frontend-engineering.md) | The nine installed skills, their triggers, near misses, and the `frontend-reviewer` scope |

## What this pack holds you to

The shared frontend quality floor is state coverage, WCAG 2.2 AA, token discipline, and an evidence manifest for completed create, retrofit, or verify work.

The pack does not claim to replace security or reliability review. Frontend review routes auth, secrets, user input, reliability, and broader product-design concerns to the appropriate reviewer or owner.

## Install with the design pack

Install the frontend pack first:

```bash
agentbundle install --pack frontend-engineering --scope user
```

For full genre routing in the pre-flight, also install `experience-design`:

```bash
agentbundle install --pack experience-design --scope user
```
