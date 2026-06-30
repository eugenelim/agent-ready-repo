# Per-screen brief — the unit `map-screen-flow` emits per screen

Goal: a brief **self-contained enough to generate one screen in isolation** (feed it
to a generative design tool / a UI-codegen step), yet **carrying the connective
context so the whole flow holds together**. The mechanism is a split:

- **Shared design contract** — authored ONCE per product (by `aesthetic-direction`
  + `design-system-foundations` + the navigation model + `interaction-design`'s
  behavioral conventions + the shared quality floor), *referenced* by every screen
  brief, never copied. This is what keeps N independently-generated screens coherent.
- **Per-screen spec** — this screen only (its job, states, data, actions, copy).

Single-screen generation = per-screen spec + a pointer to the shared contract.
Coherence is guaranteed by every brief referencing the *same* contract, by the
cross-brief consistency pass + the `experience-reviewer`, and — where a sibling
traceability lint is installed — by it checking every action → a named service and
every screen → a journey step.

## Template

```markdown
---
type: screen-flow-brief
screen: <screen-name>
flow: <slug>
surface: <responsive-web | iOS | Android | cross-platform>
---

# Screen brief: <screen-name>   ·   <product-slug>   ·   surface: <responsive-web | iOS | Android | cross-platform>

## Place in the whole
<!-- Traceability marker. The structural-orphan lint reads this exact bold-body
     field (NOT the frontmatter `type:`) to recognize this artifact as a `screen`
     chain node — by marker, not path. Keep the value exactly `screen-brief`. -->
- **Type:** screen-brief
- Journey step(s): <which step(s) of the journey this serves>
- Enters from: <screen(s) / entry points>      Exits to: <screen(s) / next actions>
- Traces to outcome: <the outcome/JTBD this screen advances>   (traceability ↑)

## Job
<One sentence: the single job this screen does for the user.>

## States  (defer to the shared quality floor — name which apply)
- empty:        <what it shows with no data>
- loading:      <skeleton / progress>
- error:        <failure framing — blame-free, recoverable>
- success/default: <the normal populated view>
- partial:      <some data present, some missing — if applicable>
- disabled:     <an action unavailable — make the why recoverable — if applicable>
- permission/denied (if gated): <what an unauthorized/locked viewer sees>

## Data & actions  (each action names its backing service — traceability ↓)
- Shows:   <data fields / entities displayed>
- Actions: <action> → <service/tool from the service blueprint>
           <action> → <service/tool>
           <failed action> → <which screen/state the error/edge flow routes to>

## Interaction & behavior  (from interaction-design — referenced, enriched there)
- <feedback & timing · input/validation flow · the component state machine
  (mermaid stateDiagram-v2) · motion purpose + reduced-motion · gesture — or:
  see interaction-design enrichment>

## Copy  (from voice-and-microcopy; per state)
- <key strings per state, or: see copy-deck §<screen>>

## Shared contract — REFERENCE, do not restate
- Design system: <pointer to tokens + component set; list the components to REUSE>
- Aesthetic direction: <pointer to the grounded taste reference>
- Navigation / chrome: <the shared nav model + persistent chrome this screen sits in>
- Quality floor: WCAG (the level your context requires) · reduced-motion · handle-all-states

## Consistency invariants
- Reuse (never reinvent): <named shared components — nav bar, list row, etc.>
- Must stay consistent with: <adjacent screens it shares patterns/data with>

## Done
- [ ] all applicable states designed   [ ] every action wired to a named service
- [ ] error/edge flows route to a real screen/state   [ ] copy in per state
- [ ] WCAG + reduced-motion honored   [ ] uses the design system (no off-system components)
- [ ] interaction/behavior section enriched   [ ] design-critique clean
```

## How it fits the flow

- `map-screen-flow` sequences the screens (the flow + the inventory spine) and
  **emits one of these briefs per screen**.
- Each brief feeds a generative design tool / UI-codegen to realize **one screen** —
  the legitimate per-screen parallel case (each screen is disjoint work).
- The **shared contract** (one per product) is the coherence anchor; the
  **cross-brief consistency pass** + the **`experience-reviewer`** are the coherence
  enforcers (a sibling traceability lint, where installed, is the mechanical one).
- The action→service column is the live tie to `blueprint-service`; the outcome
  trace is the tie up to `map-customer-journey` — so a screen can be built alone
  without the whole flow drifting.
