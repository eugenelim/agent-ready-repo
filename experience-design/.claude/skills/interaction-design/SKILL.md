---
name: interaction-design
description: Use when a screen or component needs its behavioral layer designed — how it responds to actions, validates input, transitions between states, and guides users through gesture and cognitive fit. Triggers on "design how this form behaves", "what happens when the user taps submit", "design the loading and error states", "map the state machine for this component", "design the micro-interactions", "how should this feel to use". Do NOT use to structure hierarchy or wayfinding (use `information-architecture`), to name aesthetic direction (use `creative-direction`), to map cross-screen navigation routes (use `user-flow`), or to enumerate which states exist (that enumeration belongs to the shared quality floor).
---

# Skill: interaction-design

Designs **how a screen or component behaves** — the feedback an action produces, the timing of validation, the state machine that drives a component, the motion that communicates change, and the cognitive fit that makes it feel obvious. The output enriches the **interaction/behavior section** of a per-screen brief; it does not emit its own file-per-slug artifact.

**Three state homes — the load-bearing carve.** The shared quality floor (at `../design-review/references/quality-floor.md`) owns the state *set* — the enumeration of which states must be designed (empty, loading, error, success, partial, disabled). `user-flow` owns *cross-screen* routing — which screens follow which, and the macro-level error/edge paths across the journey. This skill owns the *in-component* state machine — the transitions and guards *within* a single screen or component — plus the motion, feedback timing, and input flow that animate those transitions. Macro-flow vs. micro-behavior is the line; never re-enumerate the state set or route across screens here.

## When to invoke

Confirm all three before enriching the brief; if any fails, resolve it first.

1. **There is a screen or component with interactive behavior to design** — a form, a button with async action, a search surface, a wizard step, an animated transition. A purely static layout with no state or action is not yet a candidate.
2. **The state set is already known** — the shared quality floor's handle-all-states section (empty/loading/error/success/partial/disabled) has been consulted for this surface. If it hasn't, load the floor first (`../design-review/references/quality-floor.md`).
3. **You are designing within a screen, not across screens** — if the ask is "which screen comes after this one on error," that is `user-flow`'s territory. Bring the cross-screen routing already decided and design the in-component behavior on top of it.

## Procedure

1. **Identify the behavioral scope.** Name the screen or component and the actions it accepts. List the states the quality floor requires for it; confirm the cross-screen routing from the screen flow. This is ground truth for the state machine you will model.
2. **Model the in-component state machine.** Draw the finite state model as a mermaid `stateDiagram-v2` — states, events, transitions, and guards. Use Harel statechart / FSM vocabulary as the agnostic referent (see `references/interaction-pillars.md`). Embed the diagram directly in the brief's interaction section. Name every guard and every terminal state. Do not reach for a state-management library or reprint its API.
3. **Design feedback and timing.** For each action, specify what the user sees and when — the perceived-performance lens grounded in the Doherty Threshold (see `references/interaction-pillars.md`). Distinguish skeleton vs. spinner, optimistic-update eligibility, and the slow/degraded-connectivity path as designed states, not afterthoughts. Name the feedback *intent*, not a millisecond value.
4. **Design the input and validation flow.** For forms and input surfaces: map the field sequence and tab order as design intent; decide inline-validation timing (on-blur vs. on-submit) and the error-recovery path; apply progressive disclosure where not all fields belong on first view. See `references/interaction-pillars.md`.
5. **Decide whether to animate, then design motion with purpose.** First ask *should this animate at all* — let frequency decide: a frequent, repeated, or keyboard-initiated action gets no motion (a motionless, instant response is the right default); reserve standard motion for the occasional surface and delight for the rare/first-run moment. For motion that survives that gate, name what state change or spatial relationship it communicates (cut it if nothing), and shape it by intent — easing by the motion's job and never one that delays its start, asymmetric timing (slow where the user decides, fast where the system responds), never appearing from nothing, growing from its source not an arbitrary center. Point to platform motion guidance (`references/interaction-pillars.md`). Honor the quality floor's reduced-motion rule: every animated state change must have a still or gentle alternative that preserves the information the motion carried. Express all of this as design intent; name no duration, easing, or scale value.
6. **Carry the gesture and pointer surface.** For the target platform (responsive-web / iOS / Android / cross-platform), name the primary interaction gesture and pointer conventions, pointing to Apple HIG or Material 3 gesture guidance. State target-size intent as design rationale, not a pixel value.

   *Surface-specific mobile notes:* On marketing surfaces, CTA targets in vertical navigation drawers must span the full drawer width — compact inline chips in a vertical list context are an anti-pattern regardless of their desktop treatment. On documentation surfaces, code blocks are interactive elements on mobile (scroll, copy) and require sufficient vertical breathing room above and below for targeting.

7. **Check cognitive-law fit.** Review the design against the cognitive laws in `references/interaction-pillars.md` (Fitts's, Hick's, Miller's, Doherty, Jakob's) and the usability heuristics in `../design-review/references/heuristics.md`. Note where the design follows and where it requires a deliberate trade-off.
8. **Reference relevant pattern families.** If onboarding or search-interaction surfaces are in scope, invoke the relevant pattern family from `references/pattern-families.md` — name the pattern and point to it; do not author a bespoke alternative when a recognized pattern fits.
9. **Write the interaction section.** Commit the state machine diagram, feedback-timing intent, input/validation flow, motion rationale, gesture conventions, and cognitive-law notes into the brief's interaction/behavior section. Make it the durable design record — not a comment, a complete specification of how the surface behaves.
10. **Hold the floor.** Before closing, verify the interaction design does not fight the shared quality floor. If a behavioral choice conflicts with the accessibility or reduced-motion commitments, name it as an open question, not a silent trade-off.

## Anti-patterns to refuse

- **Re-enumerating the state set.** The quality floor owns which states must be handled. Do not maintain a private list; reference the floor.
- **Routing across screens.** "On error, go to the retry screen" is `user-flow`'s territory. Name the cross-screen destination from the screen flow and design the in-component behavior that reaches it.
- **Naming a state-management library.** The state machine is modeled as an FSM/statechart (Harel). No library API, no Redux action name, no XState config reprinted — only the behavioral model.
- **Printing motion values.** Duration, easing curve, spring constant — none of these belong here. Motion is designed as principle and purpose; the build derives the value from the platform's motion system.
- **Reprinting the quality floor.** Cross-reference it sibling-relative; do not copy it. One file, one truth.
- **Authoring standalone pattern skills.** Onboarding and search-interaction are pattern *families* a brief invokes by name (see `references/pattern-families.md`). Do not author a bespoke one-off or a new standalone skill.
- **Prescribing a layout.** Where things sit is `information-architecture`'s domain. How moving through them behaves is this skill's. They are complementary; do not conflate them.
- **Animating a frequent or keyboard-initiated action.** Motion on a high-frequency interaction reads as a delay the user pays every time. The default is no motion; motion is the exception that earns its place — decide *whether* before *how*.
- **Offering an option instead of a good default.** Most users never change a setting, so the default timing, feedback, and motion are the design for almost everyone. A list of options is the absence of a decision, not a substitute for one — design the one excellent default; expose a knob only when a real second use case differs.
- **Letting the interaction personality drift.** Feedback and motion across the product should feel like one hand made them, tuned to the grounded aesthetic direction. A screen of individually-reasonable but mismatched behaviors is incoherent; decide the personality once and hold every screen to it.
