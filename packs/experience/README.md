# experience

The design/UX seat for a product team — the grown-up successor to
`design-craft`. It carries the **whole design thread** as one walkable flow:
from a customer journey, through the screens that journey implies and the
services behind them, to how each screen looks and behaves, to an independent
review and a hand-off to realization. For interaction and visual designers,
design-eng hybrids, and any agent or person authoring the **design intent** a
UI build consumes (the design-side twin of `product-engineering`'s product
intent).

Every skill ships portable **method**, not your stack: no UI-framework code,
no styling-language syntax, no animation library, and **no values tables** (no
fixed spacing, timing, color, motion-curve, or breakpoint cheat-sheets, no
fixed token set, no pixel comps). The skills point to the recognized
standards — WCAG, the W3C Design Tokens interchange shape, Apple HIG, Material
3, APQC, BPMN — and ship the method to *derive* your design, never the values.

## What's inside

**The connective thread** — map the flow from outcome to realization:

- `map-customer-journey` — a customer/end-user journey map (stages × actions /
  emotions / pains / opportunities), carrying the platform/surface axis.
- `map-screen-flow` — the journey's screens *sequenced*, with transitions,
  error/edge flows, the per-screen state matrix, and **one per-screen brief per
  screen**; ends in a cross-brief consistency pass and a whole-journey steel
  thread that never degrades to nothing. Optionally hands off to a generative
  design tool.
- `blueprint-service` — a service blueprint (frontstage / line-of-visibility /
  backstage / support); its backstage column is the slicing instrument handed
  to `architect` / `contracts` by-name.
- `map-internal-process` — the inside-out sibling: an internal business process
  flow (APQC L3→L4, as-is + to-be, SIPOC, swimlane, pain/waste register).

**The craft** — design each screen, held to one shared floor:

- `aesthetic-direction` — turn a vague "vibe" into named goals **grounded** in
  persona + precedent + standards + platform conventions; coherence arbitration.
- `design-system-foundations` — derive a token/scale taxonomy from intent.
- `layout-and-information-architecture` — hierarchy, reading flow, wayfinding.
- `interaction-design` — how a screen *behaves*: feedback & timing, input &
  forms, component state machines, purposeful motion, navigation-as-behavior,
  gesture, cognitive-law fit. Enriches the per-screen brief.
- `design-critique` — interactive, authoring-time heuristic + taste critique;
  maps each issue to the principle it violates and rates severity.
- A shared **`quality-floor` checklist** — handle all states, the
  accessibility floor (WCAG pointed-to), and "motion communicates state, honor
  reduced-motion." One floor, referenced by every consuming skill.

**The independent review:**

- `experience-reviewer` — a forked-context, read-only reviewer agent that gives
  the design step an independent design-time review (the grounded aesthetic
  reference + platform fit + cross-brief coherence + the full quality floor),
  so design can run autonomously between human-value-add gates.

## Install

`experience` is **user-scope by default** — design method is portable, not
project-specific.

```
agentbundle install --pack experience <catalogue>
```

It projects to every shipped adapter that supports the skill primitive
(Claude Code, Codex, Copilot, Cursor, Gemini, Kiro).

## Usage

Ask your agent, for example:

- "Map the customer journey for our onboarding, then derive the screen flow."
- "Blueprint the services behind this journey's screens."
- "Map our internal claims-handling process, current-state and target-state."
- "Design how this form behaves — feedback, validation, and its state machine."
- "Run a heuristic critique of this screen and rank the findings by severity."
- "Have the experience-reviewer review this journey and screen flow."

## Where output lives

The artifact-writing skills resolve their durable output path through the
`[experience]` table of the adopter-owned `agentbundle-layout.toml`
(repo-root over user-profile), falling back to the pack default `docs/design`,
then discover-by-marker. Each skill surfaces the resolved path before its first
write. See any artifact-writing skill's `references/agentbundle-layout.md`.

## What's NOT in this pack

- **No stack specifics or values tables.** No UI-framework code, no
  styling-language syntax, no animation library, no fixed
  spacing/timing/color/motion-curve/breakpoint table, no fixed token set, and
  no pixel comps. The pack ships the method to derive your design; you choose
  your tools. The optional design-tool handover is *instructions*, never pixels,
  and names tool categories, never a winner.
- **No `seeds/`.** Templates (the aesthetic-direction doc, the per-screen brief,
  the handover) ride as skill `assets/` and are copied into your repo at
  runtime, so the pack stays user-scope (RFC-0004 Rail A).
- **No hook, engine, in-pack validator, daemon, or runtime.** This pack is
  habits, not infrastructure. `design-critique` is an interactive
  authoring-time **skill**, not a `work-loop` reviewer subagent; the independent
  fresh-context review is the `experience-reviewer` **agent**, which reviews
  design artifacts (journeys / screen flows / briefs / aesthetics), never code
  diffs and never architecture design docs.

## Cross-pack: `product-engineering`

The **words** a user reads in the UI are the `product-engineering` pack's
`voice-and-microcopy` skill's domain — the design seat's content layer. Pass
`map-screen-flow`'s per-screen state matrix to `voice-and-microcopy` and it
writes copy keyed to every screen × state cell. See the
[`product-engineering` pack README](../product-engineering/README.md).

---

→ **Go deeper:** the [`experience` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/docs/guides/experience/).
