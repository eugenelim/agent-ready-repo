# Per-screen brief — the unit `map-screen-flow` emits

Goal: a brief **self-contained enough to generate one screen in isolation** (feed it to
Claude design / a UI-codegen step), yet **carrying the connective context so the whole
holds together**. The mechanism is a split:

- **Shared design contract** — authored ONCE per product (by `aesthetic-direction` +
  `design-system-foundations` + the navigation model + the handle-all-states floor),
  *referenced* by every screen brief, never copied. This is what keeps N independently-
  generated screens coherent.
- **Per-screen spec** — this screen only (its job, states, data, actions, copy).

Single-screen generation = per-screen spec + a pointer to the shared contract. Coherence
is guaranteed by (a) every brief referencing the *same* contract, (b) the traceability
lint (every action → a named service; every screen → a journey step; shared components
reused, not reinvented), and (c) `design-critique` reviewing each generated screen
against the contract + its neighbours. This is the legitimate per-screen parallel
fan-out (MAST's breadth-first case; the same shape as omnigent/Polly's worktree fan-out).

## Template

```markdown
# Screen brief: <screen-name>   ·   <product-slug>   ·   surface: <web | iOS | Android | cross>

## Place in the whole
- Journey step(s): <which step(s) of the journey this serves>
- Enters from: <screen(s) / entry points>      Exits to: <screen(s) / next actions>
- Traces to outcome: <the outcome/JTBD this screen advances>   (traceability ↑)

## Job
<One sentence: the single job this screen does for the user.>

## States  (handle-all-states floor — every row required)
- empty:        <what it shows with no data>
- loading:      <skeleton / progress>
- error:        <failure framing — blame-free, recoverable>
- success/default: <the normal populated view>
- permission/denied (if gated): <what an unauthorized/locked state shows>

## Data & actions  (each action names its backing service — traceability ↓)
- Shows:   <data fields / entities displayed>
- Actions: <action> → <service/tool from the service blueprint>
           <action> → <service/tool>

## Copy  (from voice-and-microcopy; per state)
- <key strings per state, or: see copy-deck §<screen>>

## Shared contract — REFERENCE, do not restate
- Design system: <pointer to tokens + component set; list the components to REUSE>
- Aesthetic direction: <pointer to the grounded taste reference>
- Navigation / chrome: <the shared nav model + persistent chrome this screen sits in>
- Quality floor: WCAG AA · reduced-motion · the handle-all-states rule

## Consistency invariants
- Reuse (never reinvent): <named shared components — nav bar, list row, etc.>
- Must stay consistent with: <adjacent screens it shares patterns/data with>

## Done
- [ ] all states rendered   [ ] every action wired to a named service
- [ ] copy in per state     [ ] WCAG AA + reduced-motion
- [ ] uses the design system (no off-system components)   [ ] design-critique clean
```

## Anonymized example

```markdown
# Screen brief: learning-review   ·   example-assistant   ·   surface: cross

## Place in the whole
- Journey step(s): "approve learning" (final step of the cycle)
- Enters from: resource-dashboard ("N suggestions") · settings
- Exits to: resource-dashboard (on apply) · audit-log (from this screen)
- Traces to outcome: learning-acceptance rate ↑ (the "improve through approved learning" bet)

## Job
Let the owner review what the assistant proposes to learn, and approve or reject each item.

## States
- empty:        "Nothing to review — the assistant hasn't proposed anything new." (reassuring, not a dead end)
- loading:      list skeleton (3 placeholder rows)
- error:        "Couldn't load proposals. Retry." — no data loss; prior approvals intact
- success:      list of proposals, each with: what · why (evidence) · approve / reject
- permission:   only the owner can approve — others see read-only with a lock note

## Data & actions
- Shows:   proposal text · the evidence/trigger behind it · proposed effect
- Actions: Approve  → learning.approve  (gated Memory write + audit-log append)
           Reject   → learning.reject
           View audit → audit.read

## Copy
- approve confirm: "Approved — the assistant will use this going forward."
- empty: see above. error: blame-free, retry-first.

## Shared contract — REFERENCE
- Design system: tokens + components/v1; REUSE list-row, primary/secondary button, lock-badge
- Aesthetic direction: calm · trustworthy · quiet-competence (the grounded reference) — NOT alarm-heavy
- Navigation / chrome: bottom-tab (mobile) / left-nav (web); this is a leaf under "Insights"
- Quality floor: WCAG AA · reduced-motion · all states above

## Consistency invariants
- Reuse: list-row (same as resource-dashboard), button set, lock-badge
- Must stay consistent with: audit-log (shares the proposal row shape), resource-dashboard

## Done
- [ ] states  [ ] Approve/Reject/ViewAudit wired to learning.approve/reject/audit.read
- [ ] copy  [ ] AA + reduced-motion  [ ] on-system components  [ ] design-critique clean
```

## How it fits the system
- `map-screen-flow` produces the screen inventory (the list + the shared-contract
  pointer) and **emits one of these briefs per screen**.
- Each brief feeds Claude design / UI-codegen to generate **one screen** — fanned out in
  parallel (per-screen is the disjoint-work case).
- The **shared contract** (one per product) is the coherence anchor; the **traceability
  lint** + **`design-critique`** are the coherence enforcers.
- The action→service column is the live tie to `blueprint-service`; the outcome trace is
  the tie up to the brief; so a screen can be built alone without the whole drifting.

## Consistency & prototyping (forward idea — sample of model-thinking)

A model the `discovery-lead` should reach for, not wait to be told: after the briefs
exist, **make them consistent as a set** (a cross-brief consistency pass — shared
components reused, states uniform, copy voice aligned, no contradictory navigation),
*then* optionally **wire them together to test the whole low-fidelity** before any build:
- trigger a **wireframe/prototyping tool via MCP** to assemble the screens into a
  **low-fi clickable prototype**, and walk the journey end-to-end to catch cross-screen
  breaks; or
- when no such tool is available, build a **text-only steel thread** — a scripted walk
  through the screen briefs in journey order (screen → action → next screen) that asserts
  every transition resolves and every action has a backing service.

Either way the point is the same: verify cross-screen coherence *before* G4, cheaply.
This is logged as an example of the kind of modelling to do — envision the verification
mechanism and reach for the right tool — not just a feature request. (Forward idea for
the child-1 experience-pack RFC; cross-linked from the sample-bank, `0048-notes/09`.)
