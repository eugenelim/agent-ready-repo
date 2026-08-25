---
title: Decide and record your foundation during inception
summary: Select a stack, record the rationale, and seed the normative reference architecture before the walking skeleton.
pack: core
kind: how-to
---

# Decide and record your foundation during inception

**Use this when:** You are at the foundation step of `init-project` and need to choose a stack, record the rationale as an ADR, and instantiate the repository's normative current-architecture foundation.
**Prerequisites:** A stated business value and MVP (the value gate's output) and the `init-project` skill running at the foundation step.
**Result:** A decision record and a seeded current-architecture golden path at the adopter-owned destinations Core resolves for those distinct roles.

This guide is for someone running the greenfield front door (`init-project`) who has reached the **foundation** step and needs to choose the stack and record it well. It assumes you've already passed the value gate — you can state the business value and the MVP — and you know what a `reference.md` is for. If you don't, read [About foundation vs. map](../explanation/foundation-vs-map.md) first.

If you're starting from the very beginning, walk [From idea to a walking skeleton](../tutorials/start-a-new-project.md) instead — this guide zooms in on one step of that flow.

## Before you start

You need:

- A stated business value and MVP (the value gate's output — the first brief).
- The `init-project` skill running, at the foundation step.

## Steps

1. **Decide only the load-bearing choices.** Name the few decisions that shape most of the codebase — the runtime and language, how the system is partitioned, where state lives, the transport. Leave everything a future feature can decide later *to* that feature.
2. **Resolve the two destinations.** `init-project` requests
   `decision-record` and `current-architecture` independently through
   `work-intake`. A repository's explicit, policy-declared, conventional, or
   external destination wins when policy permits it. `docs/adr/` and
   `docs/architecture/reference.md` are catalogue fallback candidates, not
   required locations. Resolve both before directories, ADR numbering, indexes,
   or files are created.
3. **Write the ADR.** Hand the resolved `decision-record` destination to
   `new-adr`, then record *what* you chose, *why*, the *alternatives* you weighed,
   and a *re-evaluation date*. Its existing preview and confirmation gate still
   applies.
4. **Instantiate the golden path from the arc42 template.** Fill the resolved
   `current-architecture` destination forward from the decision you just made —
   the **Solution strategy** section at minimum (your stack and the one-line
   reason each choice won). The template is the same one `adapt-to-project`
   bundles; here you fill it from a decision rather than harvesting it from code.
5. **Hand the foundation forward.** The walking-skeleton spec, and every feature after it, reads the resolved golden path as steering. You don't need to fill every section now — name what you've actually decided and leave the rest.

## Variations

Real inceptions branch. Cover the cases you're likely to hit:

- **If the idea is still thin:** you may only be able to fill **Solution strategy** and **Constraints**. That's fine — fill what you've decided and leave the building-block and standards sections for when those decisions become real. An under-filled `reference.md` beats an invented one.
- **If a stack pack matches your choice:** install it and let it deliver a pre-filled `reference.md` as a seed, then edit it to be *true* for your repo. See [Establish your repo's reference architecture](../../architect/how-to/establish-reference-architecture.md) for the stack-pack route.
- **If building the skeleton later proves the foundation wrong:** go back and amend it. The inception phases are fluid, not a waterfall — record the change (a superseding ADR) rather than quietly editing the decision away.

## Common pitfalls

- **Choosing a stack with no ADR.** The skill should stop you before the skeleton is authored. If you skipped it, write the ADR now — the *why* is the whole point, and it's cheapest to capture while it's fresh.
- **Over-filling `reference.md` with invented constraints.** A foundation that prescribes standards nobody agreed to manufactures drift. Record only decisions you've actually made; the document's power comes from every line being one a reviewer could hold a pull request to.
- **Treating `reference.md` as the map.** It's the normative golden path, not a description of what exists — that's `overview.md`'s job. Keep them separate.

## See also

- [`reference.md` sections and the stack-pack contract](../../architect/reference/reference-architecture.md) — the authoritative section list.
- [About foundation vs. map](../explanation/foundation-vs-map.md) — why `reference.md` and `overview.md` stay separate.
- [Why a walking skeleton beats a throwaway prototype](../explanation/walking-skeleton-vs-throwaway.md) — what the foundation steers next.
