---
title: "About the Diátaxis framework"
summary: "The four Diátaxis kinds each get one job, fit inside the nine-stage reader journey, and leave the other stages to other artifacts."
pack: product-documentation
kind: explanation
status: stable
---

:::note
This page is for readers who want the model, not a procedure. To write a page, see [How to write a guide](../how-to/write-a-guide.md).
:::

## The question this page answers

Why split docs into four kinds at all? Why not one folder of pages and a search box? Because a single page rarely serves a single reader. The person learning your product from scratch and the person who already knows it and just needs a fact want opposite things from the same words. Diátaxis ([diataxis.fr](https://diataxis.fr/)) names that tension and resolves it: four kinds, each tuned to one reader posture, never blended.

## The four kinds

What places a page is the reader's posture right now, not their skill level. The same expert lands in a different kind on a different day.

- **Tutorials** — *lessons.* The reader is on rails, learning by doing. They leave with a working artifact and the confidence that they did it. One path, no choices, no theory.
- **How-to** — *recipes.* The reader brought a specific problem and wants it solved. They already know their way around. Skip the basics; cover the realistic variations and the pitfalls.
- **Reference** — *information.* The reader is scanning for an authoritative fact. Dry, complete, consistently structured. No opinion.
- **Explanation** — *discussions.* The reader is away from the keyboard, wanting to understand *why*. Discursive, allowed a voice, allowed to wander a little. This page is one.

## The quadrant matrix

Two axes settle the kind. Is the reader acting or understanding? Are they learning or working a task? The cross gives you four cells.

|  | Practical (you *do* something) | Theoretical (you *understand* something) |
| --- | --- | --- |
| **Learning** (acquiring a skill) | **tutorial** — "Take me through it from the start." | **explanation** — "Help me understand why." |
| **Task** (getting something done) | **how-to** — "Help me solve this specific problem." | **reference** — "Tell me exactly what this does." |

When a page resists placement, it's usually two pages wearing one title. Split it. A topic like "authentication" isn't a page — *learning* it, *configuring* it, *looking up its parameters*, and *understanding why it's cookie-based* are four pages, possibly all four kinds.

## These are contracts, not directories

Diátaxis defines what a page promises its reader, not where files must live. A how-to guide in `docs/how-to/` still follows the how-to contract. A reference page in `docs/reference/` still follows the reference contract.

The `author-product-docs` skill assigns a page kind from the reader's posture and applies the matching contract throughout drafting — without requiring any particular directory structure. Whether your repo groups docs by feature, keeps them in one flat folder, or puts them next to the code, the page still delivers what its kind promises.

## The discipline that makes it work

The matrix is the easy part. The rule that earns the payoff is **link out, don't blend**.

When a tutorial wants to explain *why*, it links to an explanation instead of digressing. When a how-to wants to list every option, it links to the reference. When an explanation wants to walk through setup, it links to the tutorial. The link can be a placeholder until the adjacent page exists, but the urge to blend is the cue to write the other page separately.

Blending is the most common reason docs frustrate everyone. Theory inside a tutorial breaks the reader's flow. Steps inside an explanation bury the idea. Opinion inside reference makes the reader doubt the facts. Each kind stays sharp only by refusing the others' material and pointing at it instead.

Cross-links are also a maintenance pact. When one page rots, its siblings surface the drift. A how-to that links a renamed reference page breaks loudly, and the break tells you both pages need a look.

## Where the four kinds sit in the reader journey

A reader passes through nine stages: discover and evaluate, install, first success, daily tasks, look up, understand, troubleshoot, upgrade, and contribute. Readers do not arrive in that order. A search result or an error message can land them on any page, so the stages are a coverage map, not a reading order.

The four kinds cover four of the nine stages:

| Journey stage | Diátaxis kind |
| --- | --- |
| First success | tutorial |
| Daily tasks | how-to |
| Look up | reference |
| Understand | explanation |

The other five need artifacts Diátaxis does not define:

- **Discover and evaluate** — a README or docs landing page.
- **Install** — an installation guide, or the README's install section.
- **Troubleshoot** — a page organized by symptom, with the exact error text.
- **Upgrade** — a changelog, release notes, and a migration guide for each breaking release.
- **Contribute** — a contributing guide.

When the `author-product-docs` skill audits a doc set, it maps pages to all nine stages and reports each as covered, partial, missing, or not applicable. A set made only of the four kinds can score well on Diátaxis and still leave a reader stranded on install or upgrade day.

## How this differs from ADRs and architecture docs

Same topic, three audiences, three framings. An ADR records *why the team chose* X over Y, frozen for contributors. An architecture doc describes *how X is built today*, for people reading the code. An explanation page describes *what X means for someone using the product*. Don't merge them. The user reading an explanation doesn't want the team's decision log; the contributor reading the architecture doesn't want the user framing.

## See also

- [How to author product docs](../how-to/author-product-docs.md) — audit a doc set and fix the biggest gaps.
- [How to write a guide](../how-to/write-a-guide.md) — document one shipped feature.
- [Getting started](../getting-started.md) — audit your own repository's docs and write the first missing page.
