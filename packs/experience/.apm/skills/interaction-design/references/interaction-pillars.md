# Interaction design: pillars and referents

The method `interaction-design` draws on. Each pillar names its recognized referent — a standard, a body of research, or a documented principle set. Point to these; do not reprint their values, tables, or specifications.

## 1. Feedback and response — perceived performance

Every action a user takes must produce a perceptible, proportionate response. The design question is not "does it respond?" but "when does it respond, and what does the user see while waiting?"

**The Doherty Threshold** is the design-time anchor: responses within roughly 400 ms keep the user in a flow state; beyond that, the system must communicate that work is in progress. This is the *perceived-performance* lens — design-time reasoning about response shape and timing intent, not a runtime measurement target. Runtime performance (Core Web Vitals and similar) is an engineering and delivery concern, outside the design charter here.

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

Motion earns its place by communicating state and causality. The design question is always: **what does this tell the user?** If the answer is "nothing," cut it.

What purposeful motion communicates:
- **State change** — the element moved from one state to another; the motion makes the change perceptible.
- **Spatial relationship** — where a panel came from, where a dismissed element went; orientation continuity across a transition.
- **Causality** — the user's action caused this; the system confirms it through movement.
- **Affordance** — a hover state or press-response that confirms the element is interactive.

**Reduced-motion commitment (from the shared quality floor).** Every animated state change must have a reduced-motion alternative that preserves the *information* the motion carried without the movement. This is a design-intent requirement, not a runtime configuration detail. Express it as: "on this transition, if reduced motion is preferred, replace [motion] with [instant or gentle state change that preserves [the information the motion communicates]]." The build maps this to the platform's own reduced-motion signal.

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
- **Doherty Threshold** — systems that respond within ~400 ms engage users; delays break the flow (see § 1, above).
- **Jakob's Law** — users spend most of their time on other sites; they expect your design to work like the ones they already know. Depart from convention only when the benefit is clear and demonstrable.

**Nielsen's usability heuristics** are the complementary principle set for finding and framing usability problems. They live in `../design-critique/references/heuristics.md` — cross-reference them; do not duplicate them here.
