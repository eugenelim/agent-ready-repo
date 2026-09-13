---
title: "Route it to work"
summary: "Turn the direction into team OKRs, expose the gaps, and hand them to the people who will build."
pack: product-strategy
kind: how-to
order: 3
---

# Route it to work

**Step 3 of 3 — Route it to work**
<!-- rung: packs/product-strategy/JOURNEY.md -->

**What changes:** Direction becomes queued work in `workspace.toml`, plus the UX and content anchors the design pack reads.
<!-- rung: packs/product-strategy/JOURNEY.md -->

**What you need first:** Company OKRs and an approved direction.
<!-- rung: authored -->

*Skipping costs:* Strategy stays a document, and product engineers pick up nothing.
<!-- rung: authored -->

**Concepts:**
<!-- rung: authored -->

- [Why strategy is its own seat](../explanation/why-strategy-is-its-own-seat.md) explains why this layer sits upstream of product discovery rather than inside it.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `run-okr-cascade` | Company OKRs and an approved direction | Team OKRs, the gaps they expose, and entries in the shaping queue. | Required |
| `define-ux-strategy` | An approved direction | The UX vision, its goals and measures, and the plan layer. | Required |
| `define-content-strategy` | An approved direction | Content purpose, process, structure and governance. | Required |

Prompts go into an AI agent session with this pack installed — the same session
throughout. Every artifact below commits to `docs/product/shaping/`, which is the
path downstream packs read by name, so the filenames are fixed rather than
project-specific.

<!-- rung: packs/product-strategy/JOURNEY.md -->

## Run `run-okr-cascade` — turn direction into work

**You type:**
<!-- rung: packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md -->

```
Cascade our company OKRs to team level, identify the gaps, and route them to the shaping queue.
```

**Agent returns:**
<!-- rung: packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md -->

> **Agent:** Done — I've written team-level OKRs derived from the company set, the strategic gaps they expose, and gap entries appended to `workspace.toml` to `docs/product/shaping/okr-cascade.md`.

**You push back:**
<!-- rung: packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md -->

> **You:** Two of these team objectives restate the company objective with our team name on it. Derive what we would actually have to do differently.
>
> **Agent:** I replaced both with objectives naming a change in our own work, and one of them exposed a gap I have added to the queue.

**Output varies** with how specific the company OKRs are and how much of the work already exists.
<!-- rung: packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md -->

**You decide:** Approve the cascade before the gaps become work — the pack's `approve-okr-cascade` gate. This writes to `workspace.toml`, where product engineers pick the items up.
<!-- rung: packs/product-strategy/JOURNEY.md -->

**Check (sufficient-for-next):** Ask what a product engineer would do first with each gap entry; this surfaces gaps too vague to start.
<!-- rung: packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md -->

**Watch out for:** This skill writes to `workspace.toml`, so a vague gap becomes a queued item someone else has to interpret. Read the appended entries before approving, not just the OKRs.
<!-- rung: packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md -->

**Where it lands:** `docs/product/shaping/okr-cascade.md`.
<!-- rung: packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md -->

**What it looks like:**
<!-- rung: docs/product/pack-walks/samples/product-strategy/okr-cascade.md -->

```markdown
---
type: okr-cascade
---
# OKR cascade — FY27 H1

## Company OKRs

### O1: Win the Midwest corridor spot market

- KR1.1 Spot-market win rate in corridor — baseline 11% → target 25%
- KR1.2 Carrier retention, corridor — baseline 68% → target 80%

### O2: Reduce cost to serve per load

- KR2.1 Support minutes per load — baseline 14 → target 6

## Team OKRs

### Booking — rolls up to O1

- **Objective:** Make a quote something a shipper can act on in the moment
- KR Median quote latency — 40 min → under 60 s
```

*A real artifact, not a section list: the opening of one produced by running the skill against a fictional scenario. Yours will differ in content and follow the same form.*

## Run `define-ux-strategy` — the experience anchor

**You type:**
<!-- rung: packs/product-strategy/.apm/skills/define-ux-strategy/SKILL.md -->

```
Define the UX strategy for this direction — vision, goals and measures, then the plan.
```

**Agent returns:**
<!-- rung: packs/product-strategy/.apm/skills/define-ux-strategy/SKILL.md -->

> **Agent:** Done — I've written a vision layer, goals with measures, and a plan layer, with the upstream and downstream positions named to `docs/product/shaping/ux-strategy.md`.

**You push back:**
<!-- rung: packs/product-strategy/.apm/skills/define-ux-strategy/SKILL.md -->

> **You:** The vision would fit any product in our category. Tie it to the specific customer situation the PRFAQ named.
>
> **Agent:** I rewrote the vision against that situation and re-derived the goals from it, which changed two of the measures.

**Output varies** with how specific the approved direction is and what customer evidence exists.
<!-- rung: packs/product-strategy/.apm/skills/define-ux-strategy/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (testable):** Apply the vision to two plausible design choices and ask which it rules out; this surfaces a vision that permits everything.
<!-- rung: packs/product-strategy/.apm/skills/define-ux-strategy/SKILL.md -->

**Watch out for:** A UX vision that no design choice could violate is decoration. Notice goals with no measure, or measures nobody currently collects.
<!-- rung: packs/product-strategy/.apm/skills/define-ux-strategy/SKILL.md -->

**Where it lands:** `docs/product/shaping/ux-strategy.md`.
<!-- rung: packs/product-strategy/.apm/skills/define-ux-strategy/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
---
type: ux-strategy
---
# UX strategy — <product>

## Vision

<The end state the experience must reach, and the differentiation it delivers.>

## Four-tenets check

| Tenet | Current strength | Gap this strategy must close |
| --- | --- | --- |
| Business strategy | <strong | weak> | <gap> |
| Value innovation | | |
| Validated user research | | |
| Killer UX design | | |

## Goals and measures

- **Goal:** <UX objective> · <leading measure> / <lagging measure> → <target>

## Plan

1. <Initiative> — closes <measure>, hands off to `journey-mapping`.
```

*Section shape only. The vision / goals / plan spine is the common UX-strategy layering; the four tenets are Levy's **definition** of UX strategy rather than a document structure, which is why they appear here as a quality check and not as four sections. This pack ships no template — confirm the shape against what you get back.*

## Run `define-content-strategy` — the content anchor

**You type:**
<!-- rung: packs/product-strategy/.apm/skills/define-content-strategy/SKILL.md -->

```
Define the content strategy — purpose, process, structure, governance — and the hand-off to content-design.
```

**Agent returns:**
<!-- rung: packs/product-strategy/.apm/skills/define-content-strategy/SKILL.md -->

> **Agent:** Done — I've written purpose, process, structure and governance, plus an explicit hand-off to `content-design` to `docs/product/shaping/content-strategy.md`.

**You push back:**
<!-- rung: packs/product-strategy/.apm/skills/define-content-strategy/SKILL.md -->

> **You:** Governance says content is reviewed but not by whom. Name the role that owns each decision, or it is not governance.
>
> **Agent:** I named an owning role for each decision type and noted which ones currently have no owner.

**Output varies** with how much content you already have and how many people touch it.
<!-- rung: packs/product-strategy/.apm/skills/define-content-strategy/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (observable):** Ask who decides when two content owners disagree; this surfaces governance with no arbiter.
<!-- rung: packs/product-strategy/.apm/skills/define-content-strategy/SKILL.md -->

**Watch out for:** Governance sections attract passive voice, which hides the absence of an owner. Notice "content is reviewed" and ask by whom.
<!-- rung: packs/product-strategy/.apm/skills/define-content-strategy/SKILL.md -->

**Where it lands:** `docs/product/shaping/content-strategy.md`.
<!-- rung: packs/product-strategy/.apm/skills/define-content-strategy/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
---
type: content-strategy
---
# Content strategy — <organization>

## Purpose

<Why this organization's content exists — for the business and for the audience.>

## Process

<Who makes content and how: roles, lifecycle from create to archive.>

## Structure

<Content types, the metadata each carries, and the taxonomy.>

## Governance

<Standards, review cadence, deprecation triggers. Owner: <named role>.>
```

*Section shape only. These four are this pack's own composite — not either published content-strategy quad, which name different sections. This pack ships no template — confirm the shape against what you get back.*

## Where this leads

**Done with this step:** You are done when a product engineer could start on each gap entry without asking what it means.
<!-- rung: authored -->

Stage 3 of three. The gap entries appear in `workspace.toml`, where the product-engineering pack picks them up.

**Next:** [Frame the intent](../../product-engineering/how-to/frame-the-intent.md) — in the `product-engineering` guidebook. Each gap entry this step queued arrives there as a problem to frame; the gap slug becomes the intent slug, which is how the thread stays traceable across the two packs.
<!-- rung: authored -->

**Go deeper:** [the `product-strategy` frameworks and artifacts reference](../reference/frameworks-and-artifacts.md) — every framework this step runs, and the artifact it commits.
<!-- rung: authored -->
