---
title: "Write the contract"
summary: "Turn the routed work into a spec whose acceptance criteria can actually fail."
pack: core
kind: how-to
order: 2
---

# Write the contract

**Step 2 of 4 — Write the contract**
<!-- rung: packs/core/JOURNEY.md -->

**What changes:** Intent becomes a spec with observable acceptance criteria, a testing strategy, and a plan.
<!-- rung: packs/core/JOURNEY.md -->

**What you need first:** One bounded, independently shippable piece of work.
<!-- rung: authored -->

*Skipping costs:* The loop builds against criteria nothing can falsify, and review has no contract to check against.
<!-- rung: authored -->

**Concepts:**
<!-- rung: authored -->

- [The two-room model](../explanation/two-room-model.md) explains why shaping and building are separate rooms.
- [Why work begins with an artifact](../explanation/why-work-begins-with-an-artifact.md) explains why the loop refuses to start from a chat message.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `new-spec` | A bounded, shippable feature | A spec with acceptance criteria and a testing strategy, plus its plan. | Required |
| `author-brief` | Work spanning several specs | A brief holding work that several specs will deliver. | Optional |

Prompts go into an AI agent session with this pack installed — the same session
throughout. `<slug>` is the short kebab-case name for this piece of work; it
names the spec directory and stays the same until the work closes.

<!-- rung: packs/core/JOURNEY.md -->

## Run `new-spec` — the contract for one feature

**You type:**
<!-- rung: packs/core/.apm/skills/new-spec/SKILL.md -->

```
Write a spec for making the login test deterministic — one independently shippable change.
```

**Agent returns:**
<!-- rung: packs/core/.apm/skills/new-spec/SKILL.md -->

> **Agent:** Done — I've written a spec with acceptance criteria and a testing strategy, and a sibling plan to `docs/specs/<slug>/spec.md`.

**You push back:**
<!-- rung: packs/core/.apm/skills/new-spec/SKILL.md -->

> **You:** Two acceptance criteria have no observer — nothing could tell whether they held. Give each one something that can fail.
>
> **Agent:** I gave both an observer, and one turned out to be unobservable as written so I narrowed it to the part that is.

**Output varies** with how bounded the feature is and how much of the contract already exists.
<!-- rung: packs/core/.apm/skills/new-spec/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (testable):** Ask what would make each acceptance criterion fail; this surfaces criteria nothing could falsify.
<!-- rung: packs/core/.apm/skills/new-spec/SKILL.md -->

**Watch out for:** A criterion with no observer reads as a requirement and gates nothing. Notice any criterion you could not write a failing test for.
<!-- rung: packs/core/.apm/skills/new-spec/SKILL.md -->

**Where it lands:** `docs/specs/<slug>/spec.md`.
<!-- rung: packs/core/.apm/skills/new-spec/SKILL.md -->

**What it looks like:**
<!-- rung: packs/core/.apm/skills/new-spec/assets/spec.md -->

```markdown
# Spec: <feature name>

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** <github-handle>
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** <!-- ADR-NNNN, RFC-NNNN, or "none" -->
- **Brief:** <!-- optional: the delivery brief this spec was derived from (`docs/product/briefs/<slug>.md`); stamped by author-delivery-brief continue. Omit, or "none", for a spec authored directly. Distinct from Constrained by: this is product provenance, not a governance constraint. -->
- **Discovery:** <!-- optional: the upstream discovery artifact this spec descended from (a decision brief / intent produced by an upstream discovery process), named by its stable id; the discovery-side sibling of Brief: (the spec→discovery up-edge a traceability check walks). Omit, or "none", for a spec authored without an upstream discovery. -->
- **Contract:** <!-- contracts/<type>/<name> this spec defines or touches (see new-spec step 4b / CONVENTIONS § 4 Contracts), or "none" for a non-API feature. A contract surface is not just a synchronous REST API — an event interface or a backend-for-frontend (BFF) boundary is a contract too; name it here and author it under contracts/<type>/. -->
- **Shape:** <!-- optional: ui | service | data | integration | mixed — selects which `## Design (LLD)` sub-sections scaffold in plan.md (e.g. ui pulls in component decomposition + state & control flow; service pulls in interfaces & contracts + data & schema + resilience — the plan template carries the authoritative map). Omit, or "mixed", when the feature spans several or you're unsure; the plan then scaffolds the full set and you prune. Stack-neutral: it names the *kind* of work, never a framework. -->
<!-- If this spec intentionally has no criteria, remove the section below and add `- **Acceptance Criteria:** none — <one-line reason>` to the metadata header. -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
```

*The agent replaces every `<…>`. This is the template the skill writes from; the artifact continues in the same shape.*

## Run `author-brief` — coordinate across specs

**You type:**
<!-- rung: packs/core/.apm/skills/author-brief/SKILL.md -->

```
Author a delivery brief for this — it spans three specs and two repos.
```

**Agent returns:**
<!-- rung: packs/core/.apm/skills/author-brief/SKILL.md -->

> **Agent:** Done — I've written a brief naming the outcome, the specs it decomposes into, and the dependencies between them to `docs/product/briefs/<slug>.md`.

**You push back:**
<!-- rung: packs/core/.apm/skills/author-brief/SKILL.md -->

> **You:** The dependencies are listed but not directional. Say which must ship before which, or the sequence is unstated.
>
> **Agent:** I made each dependency directional, which exposed one cycle I have flagged rather than resolved.

**Output varies** with how many specs the work spans and how coupled they are.
<!-- rung: packs/core/.apm/skills/author-brief/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (observable):** Ask which spec could ship first on its own; this surfaces a brief with an unstated or circular order.
<!-- rung: packs/core/.apm/skills/author-brief/SKILL.md -->

**Watch out for:** A brief that lists dependencies without direction reads as coordinated and is not. Notice undirected edges, and treat a cycle as a finding rather than a detail.
<!-- rung: packs/core/.apm/skills/author-brief/SKILL.md -->

**Where it lands:** `docs/product/briefs/<slug>.md`.
<!-- rung: packs/core/.apm/skills/author-brief/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# Brief: <outcome>

- **Status:** Draft
- **Specs:** `<slug>`, `<slug>`

## Outcome

## Decomposition

| Spec | Delivers | Depends on |
| --- | --- | --- |
| `<slug>` | <part of the outcome> | <slug, or none> |
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Where this leads

**Done with this step:** You can move on when you could write a failing test for every acceptance criterion.
<!-- rung: authored -->

Stage 2 of four. The spec is what every later gate and review round is measured against.

**Next:** [Run the loop](run-the-loop.md).
<!-- rung: authored -->

**Go deeper:** [the `core` pack reference](../explanation/core-pack.md) — how the loop, the gates and the reviewers fit together.
<!-- rung: authored -->
