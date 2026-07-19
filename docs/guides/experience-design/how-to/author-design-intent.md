# Thread a feature from journey to screens

> **How-to** — task-oriented. Run the `experience-design` thread end to end, from a
> customer journey to a reviewed set of per-screen briefs. Assumes the pack is
> installed (see [`../_shared/`](../../_shared/)). For *why* the thread is shaped
> this way, read [The experience thread](../explanation/the-experience-thread.md).

You drive each skill by asking your agent in natural language; the skill's
trigger phrases route the request. You don't need to name the skill — but you
can. Each skill is standalone-useful, so you can also enter the thread at any
step and it will elicit what it needs inline.

## 1. Map the journey

Start from the customer, even roughly:

> "Map the customer journey for onboarding a new user to our personal-finance
> dashboard."

`journey-mapping` divides the journey into a few named stages and, for
each, captures actions, emotions, pains, and opportunities — outside-in, in the
customer's words. It carries a **surface** (responsive-web / iOS / Android /
cross-platform) that changes what it asks. The pains-to-opportunities column is
the output the rest of the thread points back to.

## 2. Derive the screen flow and the per-screen briefs

> "Turn that journey into a screen flow — sequence the screens, route the error
> cases, and give me a brief per screen."

`user-flow` sequences the screens the journey implies, draws the
transitions and the **error/edge flows** (where a failed or denied action
lands), records which quality-floor states each screen handles, and emits **one
self-contained brief per screen** — split into a shared design contract
(referenced, not copied) and a per-screen spec. Each action names its backing
service; each screen names its journey step.

It finishes by walking the whole journey: a low-fi prototype if a design-tool
MCP is connected, otherwise a **text-only steel thread** that asserts every
transition resolves and every action has a backing service. It never stops at
"briefs emitted."

## 3. Blueprint the backing services

> "Blueprint the services behind these screens."

`service-blueprint` lays out frontstage / line-of-visibility / backstage /
support. The backstage column is the slicing instrument you hand to `architect`
and `contracts` by-name — or, when those aren't installed, it names the services
textually so the thread still holds.

## 4. Design each screen from its brief

With a brief in hand, run the craft skills against it:

> "Name the aesthetic direction for this dashboard, grounded in our persona and
> platform." → `creative-direction` (each goal grounded in a stable referent)
> "Derive a token and scale taxonomy from those goals." → `design-system`
> "Structure this screen's hierarchy and reading flow." → `information-architecture`
> "Design how this form behaves — feedback, validation, and its state machine." → `interaction-design`

`interaction-design` enriches the brief's interaction section: feedback and
timing, input/validation flow, a component **state machine** (a mermaid
`stateDiagram-v2`), purposeful motion that honors reduced-motion, navigation
behavior, gesture, and cognitive-law fit. It designs how the screen *behaves* —
the macro flow across screens stays `user-flow`'s.

## 5. Critique as you author

> "Run a critique of this screen — heuristics and taste — and rank the findings."

`design-review` applies the shared **`quality-floor`** (all states, the
accessibility floor, reduced-motion), evaluates against usability heuristics,
and runs a **taste mode** against the grounded aesthetic reference and platform
fit. Each finding maps to the principle it violates, gets a 0–4 severity, and
comes with one concrete recommendation. This is authoring-time self-review — not
the independent pass.

## 6. Get the independent review

> "Have the experience-reviewer review this journey and screen flow."

`experience-reviewer` is a forked-context agent that reviews the set
independently — the grounded aesthetic reference, platform fit, cross-brief
coherence, and the full quality floor including accessibility — and returns a
verdict with severity-tagged findings. It marks no homework of its own: it never
saw the authoring. Use it as the design gate that runs without a human in the
loop.

## 7. (Optional) Hand off to realization

> "Emit a design-tool handover for these screens."

`user-flow` can emit a handover keyed to each brief — instructions a
generative design tool consumes, never a comp. If a design-tool MCP is
connected, it triggers the tool; otherwise it writes a `.handover.md` you paste
into whichever tool you use.

## What you end up with

Durable design-intent artifacts in your repo — a journey map, a screen flow with
per-screen briefs, a service blueprint, a grounded aesthetic direction, and a
critique — each framework-agnostic, each steering the build, none of them a
values cheat-sheet tied to one stack, and the whole thread proved walkable by the
steel thread.

> Mapping an **internal** process instead of a customer-facing one? Use
> `process-mapping` — the inside-out sibling (APQC L3→L4, as-is/to-be,
> SIPOC, swimlane, pain/waste). It carries no surface axis.
