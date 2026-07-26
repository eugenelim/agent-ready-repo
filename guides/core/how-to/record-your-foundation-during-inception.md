# Decide and record your foundation during inception

**Use this when:** You are at the foundation step of `init-project` and need to choose a stack, record the rationale as an ADR, and instantiate `docs/architecture/reference.md`.
**Prerequisites:** A stated business value and MVP (the value gate's output) and the `init-project` skill running at the foundation step.
**Result:** An ADR in `docs/adr/` and a seeded `docs/architecture/reference.md` — the golden path that steers every spec that follows.

This guide is for someone running the greenfield front door (`init-project`) who has reached the **foundation** step and needs to choose the stack and record it well. It assumes you've already passed the value gate — you can state the business value and the MVP — and you know what a `reference.md` is for. If you don't, read [About foundation vs. map](../explanation/foundation-vs-map.md) first.

If you're starting from the very beginning, walk [From idea to a walking skeleton](../tutorials/start-a-new-project.md) instead — this guide zooms in on one step of that flow.

## Before you start

You need:

- A stated business value and MVP (the value gate's output — the first brief).
- The `init-project` skill running, at the foundation step.

## Steps

1. **Decide only the load-bearing choices.** Name the few decisions that shape most of the codebase — the runtime and language, how the system is partitioned, where state lives, the transport. Leave everything a future feature can decide later *to* that feature.
2. **Write the ADR.** Record *what* you chose, *why*, the *alternatives* you weighed, and a *re-evaluation date*. The ADR is the thing that survives after the reasoning leaves your head — a stack chosen with no recorded rationale is the gap this step exists to close.
3. **Instantiate `reference.md` from the arc42 template.** Fill `docs/architecture/reference.md` forward from the decision you just made — the **Solution strategy** section at minimum (your stack and the one-line reason each choice won). The template is the same golden-path one the `adapt-to-project` skill bundles; here you fill it from a decision rather than harvesting it from existing code.
4. **Hand the foundation forward.** The walking-skeleton spec, and every feature after it, reads `reference.md` as steering. You don't need to fill every section now — name what you've actually decided and leave the rest.

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
