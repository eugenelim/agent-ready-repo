# Interaction design: pillars and referents

The method `interaction-design` draws on. Each pillar names its recognized referent — a standard, a body of research, or a documented principle set. Point to these; do not reprint their values, tables, or specifications.

## 1. Feedback and response — perceived performance

Every action a user takes must produce a perceptible, proportionate response. The design question is not "does it respond?" but "when does it respond, and what does the user see while waiting?"

**The response to the *touch* is separate from the response to the *result*.** Direct manipulation deserves an *immediate* acknowledgement — a pressable element confirms the press the instant it happens (a slight, immediate tactile response), well before any network work returns. Designing only the result-feedback and leaving the press itself silent is the most common way an interface feels dead under the finger.

**The Doherty Threshold** is the design-time anchor: responses within the sub-perceptual threshold the Doherty research names keep the user in a flow state; beyond that, the system must communicate that work is in progress. Read the threshold value from the source — design to the principle, not a reprinted number. This is the *perceived-performance* lens — design-time reasoning about response shape and timing intent, not a runtime measurement target. Runtime performance (Core Web Vitals and similar) is an engineering and delivery concern, outside the design charter here.

Three response shapes to decide:
- **Skeleton screen vs. spinner** — a skeleton preserves layout and signals "content is coming"; a spinner signals "this will take a moment." Neither is wrong; the choice depends on how predictable the content shape is and how long the wait is.
- **Optimistic update** — show the success state immediately, roll back on error. Suitable when the action is nearly always successful and the rollback path is clear and recoverable.
- **Slow / degraded path** — the long wait and the network-unavailable state are designed states, not afterthoughts. Name what the user sees and can do in each.

**Reference:** the Doherty Threshold is documented in IBM Systems Journal (1982) and widely cited in HCI literature; see also research at [NN/g on response time limits](https://www.nngroup.com/articles/response-times-3-important-limits/).

## 2. Input and forms

Input surfaces are sequences, not inventories. Design the flow — the order of fields, when validation fires, how errors recover — before laying out the visual form.

- **Field sequence and tab order** — expressed as design intent for focus management; the build maps it to the platform's own focus model.
- **Inline-validation timing** — validate on-blur (when the user leaves a field) for correctness constraints, on-submit for cross-field constraints. Early on-change validation for password-strength or character-count feedback is appropriate when the rule is continuously improving (not binary pass/fail).
- **Error recovery** — the error message names the problem in user terms and the corrective action; it appears adjacent to the field that caused it (see Nielsen heuristic 9 in `../design-critique/references/heuristics.md`). Recovery is always possible; never a dead end.
- **Progressive disclosure** — reveal fields only when a prior choice makes them relevant. Keep the first view minimal; expand contextually.

## 3. Component / screen state machines

A component or screen with stateful behavior is modeled as a **finite state machine (FSM)** — a set of states, a set of events, and a transition function with optional guards. This is the *dynamic* complement to the quality floor's static state *set*.

**Modeling convention.** Author the state machine as a **mermaid `stateDiagram-v2`** embedded in the brief's interaction section. A form, for example:

```
stateDiagram-v2
    [*] --> idle
    idle --> validating : submit
    validating --> invalid : validation_failed
    validating --> submitting : validation_passed
    invalid --> validating : resubmit
    submitting --> success : response_ok
    submitting --> error : response_failed
    error --> submitting : retry
    success --> [*]
```

Name every guard condition in prose beside the diagram when guards affect the transition logic (e.g., "the submit event fires only when all required fields are non-empty").

**The agnostic referent.** The FSM / Harel statechart formalism is the modeling language; never a state-management library. David Harel's statechart paper (Harel, 1987, *Science of Computer Programming*) and the W3C SCXML specification are the academic anchors. The [XState docs on statecharts](https://stately.ai/docs/what-are-statecharts) are a readable introduction to the formalism — the *concepts* apply; the library API does not ship here.

## 4. Motion and micro-animations

**The first question is not how to animate, but whether to.** Most motion that ships should not have. Decide in this order:

**Should this animate at all? — let frequency decide.** The more often a user sees an interaction, the less it should move. A frequent, repeated, or keyboard-initiated action (a shortcut, a list step, a repeated toggle) should have **no** motion — an animation the user triggers dozens of times a day reads as a delay between them and their goal. Reserve standard motion for the *occasional* (a modal, a drawer, a toast) and any expressive delight for the *rare or first-run* moment (onboarding, a celebration). A motionless interface that responds instantly is the right default; motion is the exception that must justify itself.

**Does it have a purpose?** If it animates, it earns its place by communicating — the design question is always **what does this tell the user?** If the answer is "nothing," cut it. Purposeful motion communicates:
- **State change** — the element moved from one state to another; the motion makes the change perceptible.
- **Spatial relationship** — where a panel came from, where a dismissed element went; orientation continuity across a transition.
- **Causality** — the user's action caused this; the system confirms it through movement.
- **Affordance** — a press-response or focus change that confirms the element is interactive.

**How should it move? — craft principles (intent, never values).** Express each as design intent; the build resolves the curve, duration, and distance. Reprint no easing names, curves, durations, or scale numbers.
- **Easing by the motion's job.** An element *entering or leaving* wants a responsive shape that starts fast and settles — it should feel like it's already on its way. An element *moving or morphing on screen* wants a shape that accelerates then decelerates naturally. **Never an easing that delays the start of the motion** — a slow beginning reads as sluggish exactly when the user is watching most closely, no matter the total duration.
- **Asymmetric timing — slow where the user decides, fast where the system responds.** A deliberate, reversible action (a hold-to-confirm) should be slow enough to feel weighty and cancellable; the system's acknowledgement on release should be quick. Match the pace to who is acting.
- **Never appear from nothing.** An element should not animate in from full invisibility or zero size — nothing in the real world does. Start from a nearly-final state (a hair of offset or transparency) so the arrival reads as natural, not as a thing blinking into existence.
- **Animate from the source, not an arbitrary center.** A popover or menu should grow from the control that opened it, so the motion explains where it came from; a centered modal is the deliberate exception (it has no single on-screen origin).

**Reduced-motion commitment (from the shared quality floor).** Reduced motion drops movement and position change but keeps the information-bearing transition — an instant swap, a fade, a color change — never stripping the meaning along with the movement (the floor's "instant or gentle" alternative). Every animated state change must have a reduced-motion alternative that preserves the *information* the motion carried without the movement. Express it as design intent: "on this transition, if reduced motion is preferred, replace [motion] with [an instant or gentle state change that preserves [the information the motion communicates]]." The build maps this to the platform's own reduced-motion signal.

**Platform motion guidance** — point to these; do not reprint values, timing, or curves from them:
- [Material Design: Motion](https://m3.material.io/styles/motion/overview) — Google's system for purposeful, responsive motion on Android and cross-platform.
- [Apple HIG: Motion](https://developer.apple.com/design/human-interface-guidelines/motion) — Apple's guidance on animation and transition intent for iOS, iPadOS, and macOS.

## 5. Navigation as behavior

Navigation is a behavior, not only a structure. `layout-and-information-architecture` places the navigation elements and defines the wayfinding structure; this pillar designs how *moving through* that structure behaves.

- **Transition semantics** — what animates when the user navigates forward vs. backward? Does the UI preserve orientation (the user can tell where they came from)?
- **Back / undo semantics** — what does "back" mean here? Does it undo the last action, restore the previous screen, or collapse a panel? Name it explicitly; inconsistency here is a major usability failure (Nielsen heuristic 3 — user control and freedom).
- **Orientation continuity** — shared elements between screens (a header, a persistent panel, a tab bar) should not re-animate on every transition; they anchor the user's spatial model.

## 6. Gesture and pointer affordances (platform axis)

Carry gesture and pointer conventions on the platform/surface axis declared for the product: `responsive-web | iOS | Android | cross-platform`.

**References — point to these; never reprint gesture tables or target-size values:**
- [Apple HIG: Gestures](https://developer.apple.com/design/human-interface-guidelines/gestures) — canonical iOS / iPadOS gesture conventions.
- [Material 3: Interaction](https://m3.material.io/foundations/interaction/overview) — Android and cross-platform gesture and touch conventions.
- [MDN: Pointer Events](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_Events) — the web pointer model (mouse, touch, stylus as a unified abstraction).

Design target-size intent as a rationale ("the target is sized for confident one-handed thumb reach on a phone-form-factor device"), not a pixel dimension.

## 7. Cognitive-law fit

Interaction design is grounded in the cognitive science of how users perceive and decide. These laws are the referent; cross-reference them rather than re-deriving them.

**[Laws of UX](https://lawsofux.com/) — the curated referent for applied cognitive fit:**
- **Fitts's Law** — the time to acquire a target is a function of distance and size; make frequent targets large and close.
- **Hick's Law** — decision time grows with the number and complexity of choices; minimize cognitive load at decision points.
- **Miller's Law** — working memory holds roughly seven items (plus or minus two); chunk information to respect this limit.
- **Doherty Threshold** — systems that respond within the threshold the research names engage users; delays break the flow (see § 1, above — read the value from the source).
- **Jakob's Law** — users spend most of their time on other sites; they expect your design to work like the ones they already know. Depart from convention only when the benefit is clear and demonstrable.

**Nielsen's usability heuristics** are the complementary principle set for finding and framing usability problems. They live in `../design-critique/references/heuristics.md` — cross-reference them; do not duplicate them here.

## 8. Good defaults over options; cohesion

Three principles cut across every pillar above — they decide how the behavior is *shaped*, not which behavior it is.

- **Design the one excellent default; don't offload taste to configuration.** Most users never change a setting, so the default timing, feedback, and motion *are* the design for almost everyone. A pile of options is not a substitute for a good default — it is the absence of one. Spend the judgment on getting the default right; expose an option only when a real second use case needs to differ (the same discipline the build holds for flags).
- **Cohesion over individual tweaks — the behavior's personality matches the product.** The feedback and motion across a product should feel like one hand made them, tuned to the grounded aesthetic direction: crisp and fast for a professional tool, softer and livelier for a playful one. A screen full of individually-reasonable animations that don't share a personality reads as incoherent. Decide the interaction personality once (with `aesthetic-direction`) and hold every screen to it.
- **Handle the edge cases invisibly.** The polish users *feel* but never consciously name lives in the states no one demos: pausing a timer when the tab is hidden, preserving focus and scroll across a transition, absorbing a double-tap, not re-animating shared chrome. Designing these is what separates an interface that feels considered from one that feels brittle.

**A refinement practice.** Interaction quality hides at full speed. Review the behavior with fresh eyes on a later pass (imperfections invisible while authoring become obvious), and judge gesture and motion on a real device, not a description — the feel is the deliverable, and the feel only shows in the running thing.
