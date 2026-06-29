# Author design intent for a feature

> **How-to** — task-oriented. Run the `design-craft` loop end to end, from a
> vague vibe to a severity-rated critique. Assumes the pack is installed (see
> [`../_shared/`](../../_shared/)). For *why* the loop is shaped this way, read
> [The design-craft loop](../explanation/the-design-craft-loop.md).

You drive each skill by asking your agent in natural language; the skill's
trigger phrases route the request. You don't need to name the skill — but you
can.

## 1. Name the direction

Start from the feeling, even a rough one:

> "We're building a personal-finance dashboard. It should feel calm but
> premium — help me turn that into named design goals."

`aesthetic-direction` interrogates the vibe, converges on a few **named, ranked
goals** (each a noun phrase you can recall), records which goal wins when two
conflict, and copies an **aesthetic-direction doc** into your repo. That doc is
the durable artifact the rest of the loop — and the build — reads.

Stop here until the goals are named and ranked. Everything downstream points
back to them.

## 2. Derive the system

With direction in hand:

> "Derive a token and scale taxonomy from these goals — don't pick values yet."

`design-system-foundations` hands back the **method and a symbolic shape**:
tokens named by semantic role, a spacing and type scale organized around a
single ratio-as-concept (expressed as `step −1, base, step +1`, never numbers),
accessibility as a floor, and an atomic-composition model. You resolve the
symbolic shape to real values for your medium — the skill teaches the
derivation; it never prints a palette.

## 3. Structure the screen

> "Structure the dashboard's information architecture and reading flow."

`layout-and-information-architecture` ranks the content
(primary / secondary / tertiary), picks a reading pattern from the surface's
job, stages complexity with progressive disclosure, shapes the navigation tree,
and designs **wayfinding** so the user always knows where they are and how to
get back — all as concepts, no markup. It also walks the surface's states
(empty, loading, error) because those change the IA.

## 4. Critique the result

When you have a screen or mockup:

> "Run a heuristic critique of this screen and rank the findings by severity."

`design-critique` applies the shared **`quality-floor`** first (all states, the
accessibility floor, the reduced-motion principle), then evaluates against
recognized usability principles. Each finding maps to the principle it
violates, gets a **0–4 severity**, and comes with one concrete recommendation.
The output is worst-first, with a count-by-severity headline — a list a
stakeholder can argue and a builder can act on.

## 5. Loop back as needed

A catastrophic critique finding often sends you back to direction or structure.
That's the loop working. Re-open the relevant skill, amend the artifact
deliberately (don't quietly drift), and re-run the critique.

## What you end up with

Durable design-intent artifacts in your repo — an aesthetic-direction doc, a
token-taxonomy rationale, an information architecture, and a critique — each
framework-agnostic, each steering the build, none of them a values cheat-sheet
tied to one stack.
