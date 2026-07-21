# experience-design

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

**Correctness is the floor, not the ceiling.** Accessibility compliance,
information hierarchy, and usability heuristics (WCAG, Nielsen, Laws of UX)
are non-negotiable — but meeting them alone produces correct-but-tasteless
work. The `creative-direction` skill is the gate between the two: it grounds
goals in persona, precedent, *and* visual voice — surface treatment, type scale
ambition, color philosophy, and elevation philosophy. A direction doc that only
names correctness goals has not cleared the gate.

## What's inside

**The connective thread** — map the flow from outcome to realization:

- `journey-mapping` — a customer/end-user journey map (stages × actions /
  emotions / pains / opportunities), carrying the platform/surface axis.
- `user-flow` — the journey's screens *sequenced*, with transitions,
  error/edge flows, the per-screen state matrix, and **one per-screen brief per
  screen**; ends in a cross-brief consistency pass and a whole-journey steel
  thread that never degrades to nothing. Optionally hands off to a generative
  design tool.
- `service-blueprint` — a service blueprint (frontstage / line-of-visibility /
  backstage / support); its backstage column is the slicing instrument handed
  to `architect` / `contracts` by-name.
- `process-mapping` — the inside-out sibling: an internal business process
  flow (APQC L3→L4, as-is + to-be, SIPOC, swimlane, pain/waste register).

**The craft** — design each screen, held to one shared floor:

- `creative-direction` — turn a vague "vibe" into named goals **grounded** in
  persona + precedent + standards + platform conventions; coherence arbitration.
- `design-system` — derive a token/scale taxonomy from intent.
- `information-architecture` — hierarchy, reading flow, wayfinding.
- `interaction-design` — how a screen *behaves*: feedback & timing, input &
  forms, component state machines, purposeful motion, navigation-as-behavior,
  gesture, cognitive-law fit. Enriches the per-screen brief.
- `design-review` — interactive, authoring-time heuristic + taste critique;
  maps each issue to the principle it violates and rates severity.
- A shared **`quality-floor` checklist** — handle all states, the
  accessibility floor (WCAG pointed-to), and "motion communicates state, honor
  reduced-motion." One floor, referenced by every consuming skill.

**Genre-specific Direct skills** — surface-typed structural IA used when a
screen has a known surface genre (run before `interaction-design` in place of
the general `information-architecture` skill):

- `analytical-design` — structural specification for analytical and dashboard
  surfaces: widget hierarchy, role-based view architecture,
  business-question-to-layout map.
- `conversion-design` — structural specification for marketing and acquisition
  surfaces: above-fold contract, scroll story, social-proof architecture.
- `documentation-design` — structural specification for documentation surfaces:
  content hierarchy, navigation strategy, TTFV architecture; Diátaxis content
  typing.
- `informational-design` — structural specification for informational and
  editorial surfaces: typographic hierarchy, reading-pattern calibration,
  editorial grid.
- `marketplace-design` — structural specification for marketplace surfaces:
  listing card IA, filter and facet architecture, transaction bridge.
- `workspace-design` — structural specification for workspace and productivity
  surfaces: context-persistence architecture, attention zone layout, interrupt
  design.

**The independent review:**

- `experience-reviewer` — a forked-context, read-only reviewer agent that gives
  the design step an independent design-time review (the grounded aesthetic
  reference + platform fit + cross-brief coherence + the full quality floor),
  so design can run autonomously between human-value-add gates.

**Session orientation:**

- `experience-status` — orients to the current design thread at a glance: reads
  design artifacts from the configured output directory and surfaces what exists,
  what's missing, and which skill to run next.

## Install

`experience-design` is **user-scope by default** — design method is portable, not
project-specific.

```
agentbundle install --pack experience-design <catalogue>
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
`[design]` table of the adopter-owned `agentbundle-layout.toml`
(repo-root first, then user-profile; two-branch elicitation when neither
resolves — never a silent default). Each skill surfaces the resolved path before
its first write. See any artifact-writing skill's `references/agentbundle-layout.md`.

## What's NOT in this pack

- **No stack specifics or values tables.** No UI-framework code, no
  styling-language syntax, no animation library, no fixed
  spacing/timing/color/motion-curve/breakpoint table, no fixed token set, and
  no pixel comps. The pack ships the method to derive your design; you choose
  your tools. The optional design-tool handover is *instructions*, never pixels,
  and names tool categories, never a winner.
- **No `seeds/`.** Templates (the creative-direction doc, the per-screen brief,
  the handover) ride as skill `assets/` and are copied into your repo at
  runtime, so the pack stays user-scope (RFC-0004 Rail A).
- **No hook, engine, in-pack validator, daemon, or runtime.** This pack is
  habits, not infrastructure. `design-review` is an interactive
  authoring-time **skill**, not a `work-loop` reviewer subagent; the independent
  fresh-context review is the `experience-reviewer` **agent**, which reviews
  design artifacts (journeys / screen flows / briefs / aesthetics), never code
  diffs and never architecture design docs.

## Cross-pack: `product-strategy`

The `product-strategy` pack is the **upstream strategic input** this pack builds on. Before `journey-mapping` or `user-flow` run, a strategist using the `product-strategy` pack may have committed `ux-strategy.md` (vision → goals+measures → plan) and `content-strategy.md` (Halvorson quad: Purpose + Process + Structure + Governance) to `docs/product/shaping/`. When present:

- `journey-mapping` reads `ux-strategy.md` as the strategic anchor for the journey's stated rationale.
- `content-design` (downstream skill) reads `content-strategy.md` for organizational governance intent — content-design is execution-layer (per-surface); content strategy is governance-layer (organizational intent).

These are optional inputs; the skills degrade gracefully when the upstream artifacts are absent. See the [`product-strategy` pack README](../product-strategy/README.md).

## Cross-pack: `product-engineering`

The **words** a user reads in the UI are the `product-engineering` pack's
`voice-and-microcopy` skill's domain — the design seat's content layer. Pass
`user-flow`'s per-screen state matrix to `voice-and-microcopy` and it
writes copy keyed to every screen × state cell. See the
[`product-engineering` pack README](../product-engineering/README.md).

---

→ **Go deeper:** the [`experience-design` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/docs/guides/experience-design/).
