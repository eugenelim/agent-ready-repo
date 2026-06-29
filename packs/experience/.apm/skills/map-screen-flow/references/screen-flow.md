# The screen-flow method

How to turn a customer journey into the screens that realize it — sequenced,
routed, and briefed. The deliverable is the *flow across screens*, not the list;
the list is only the spine.

## Platform/surface axis

The `surface` value changes the navigation model the flow assumes and the chrome
each screen sits in. Point to the platform's own conventions; never reprint their
values.

- **iOS** — consult Apple HIG for navigation patterns (tab bars, navigation
  stacks, modal presentation), gestures, and platform affordances.
- **Android** — consult Material 3 for its navigation components and
  adaptive-layout guidance.
- **responsive-web** — consult responsive-layout and progressive-disclosure
  conventions (MDN) and, where installable, PWA navigation patterns.
- **cross-platform** — sequence the journey and the screen inventory *once*
  (they are shared); name the per-surface adaptations to chrome, navigation, and
  gestures rather than forking the whole flow.

## The screen inventory — the spine

Walk the journey stages and list the screens each implies. Name a screen by the
**job it does** for the user ("review proposals," "confirm payment"), not by a
widget or a layout. Keep it coarse — one screen per job, not one per state. This
inventory is the spine the flow is drawn over; it is never the deliverable on its
own.

## Sequencing and edge routing

Draw the screens in journey order and make the connections explicit:

- **Transitions out** — for each screen, what the user does and which screen it
  takes them to. Name the trigger (the action), not just the arrow.
- **Error / edge flows** — when an action **fails, is denied, or times out**,
  which screen or state the user lands in. This is the work that distinguishes a
  screen flow from a happy-path sketch: a flow that only draws the success path
  has not been designed for the states products actually feel broken in.
- **Entry and exit points** — where the user can arrive from and leave to,
  including out-of-flow entries (a deep link, a notification, a return visit).

Author the flow as a mermaid `flowchart` so the routing is legible and
diffable. Every node is a screen from the inventory; every edge is a named
transition or an error/edge route.

## The per-screen state matrix

For each screen, name which floor states apply. The state **set** lives once in
the shared quality floor (`../design-critique/references/quality-floor.md`) —
empty / loading / error / success / partial / disabled, plus `permission/denied`
when the screen is gated. The matrix records *which* of those each screen must
handle; it does not restate what each state means, and it does not design the
*behavior between* them (that is `interaction-design`'s in-component state
machine).

## Consistency pass

Once every brief exists, review the set as a whole — independently-written briefs
drift:

- **Shared components reused, never reinvented** — the same list row, the same
  primary button, the same empty-state pattern across screens.
- **States uniform** — a loading state means the same thing everywhere; an error
  is framed the same blame-free way.
- **Copy voice aligned** — one voice across the flow (hand to `voice-and-microcopy`).
- **Navigation non-contradictory** — no two screens disagree about where "back"
  goes or what the persistent chrome is.

A set of briefs that each read well but contradict each other as a set is not a
finished screen flow.

## The steel thread

The whole-journey verification that **always runs** — the flow's guarantee that
it holds end-to-end. It degrades by fidelity but never to nothing:

1. **Prototype walk (preferred).** If a wireframe/prototyping MCP tool is
   connected, assemble the briefs into a low-fi clickable prototype and walk the
   journey end-to-end, catching cross-screen breaks by clicking through them.
2. **Text-only steel thread (the floor).** When no such tool is present, script
   a walk through the briefs in journey order — screen → action → next screen —
   and assert, for the whole journey:
   - **every transition resolves** — each action routes to a screen that exists
     in the inventory (no dangling edge, no dead end);
   - **every action has a backing service** — each action names a service from
     the blueprint (or a textually-named service when `blueprint-service` is
     absent).

   Walk the **error/edge routes too**, not just the happy path: a denied action
   that routes nowhere is exactly the gap the steel thread exists to catch.

The steel thread is **non-droppable**. Prototype → text-only is the only
permitted degradation; "skip it" is not. If a transition does not resolve or an
action has no backing service, that is a finding to surface and fix before
hand-off — not a detail to defer.

## The seams the flow carries

The briefs carry the traceability edges even though this pack ships no lint to
enforce them (that is a sibling effort): **every action → a named service**
(down to `blueprint-service`) and **every screen → a journey step** (up to
`map-customer-journey`). The cross-brief consistency pass and the
`experience-reviewer` check these by reading; a traceability lint, when present,
checks them mechanically.
