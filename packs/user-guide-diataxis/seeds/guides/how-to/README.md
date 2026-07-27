# How-to guides

> *Task-oriented.* Recipes for solving specific problems the reader
> brought with them. Assumes baseline competence; doesn't teach.

## Writing a how-to

A good how-to:

- **Solves one named problem.** The title is the problem: "Configure
  X for production", "Migrate from Y to Z", "Debug a failing W".
- **Assumes the reader is competent.** Doesn't reteach the basics. Links
  to tutorials for foundational concepts.
- **Is goal-oriented.** Skip context that isn't needed to accomplish the
  goal. The reader is here to *do something*, not to learn.
- **Handles the realistic version.** Cover the common variations and
  pitfalls — that's what makes how-tos different from "just read the
  reference."
- **Is named for what the reader was searching for.** "How to configure
  rate limiting" beats "Rate limiting configuration guide."

## What goes in a how-to

- A clear problem statement at the top.
- Prerequisites and assumptions.
- The steps to accomplish the goal — terser than a tutorial.
- Variations the reader is likely to need.
- Pitfalls and how to recognize them.
- Links to relevant reference material.

## What does NOT go in a how-to

- Step-by-step beginner instruction. That's a tutorial.
- Complete authoritative description of every option. That's reference.
- Why-this-design explanations. That's an explanation page.

## Maintenance

How-tos drift when the product changes underneath them. Make doc updates
part of the spec workflow: when a spec ships, check whether any how-to
references the changed behavior, and update in the same PR.
