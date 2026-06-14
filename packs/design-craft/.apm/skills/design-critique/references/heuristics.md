# Heuristic evaluation: principles, severity, and findings

The method `design-critique` runs. It is a structured **heuristic
evaluation**: review a surface against a recognized set of usability
principles, name the principle each problem violates, rate how badly it
hurts, and hand back a list ordered worst-first with one fix per finding.
The principle names are the shared vocabulary — they turn "this feels off"
into "this violates *visibility of system status*," which a stakeholder can
argue with and a builder can act on.

## The principles (Nielsen's 10 usability heuristics)

These are the canonical anchor. Every finding maps to exactly one of them
as its *primary* violation; note secondary ones only when they sharpen the
fix.

1. **Visibility of system status** — the surface keeps the user informed
   about what is going on, through timely feedback.
2. **Match between system and the real world** — speaks the user's
   language and follows real-world conventions, not internal jargon.
3. **User control and freedom** — clearly marked exits, undo, and redo;
   no dead ends or traps.
4. **Consistency and standards** — same word, same action, same place;
   follows platform and product convention so nothing surprises.
5. **Error prevention** — designs out the slip before it happens, rather
   than only catching it after.
6. **Recognition rather than recall** — makes options, actions, and the
   information needed visible, so the user need not remember across steps.
7. **Flexibility and efficiency of use** — serves both the novice and the
   expert; accelerators and shortcuts that don't block the beginner.
8. **Aesthetic and minimalist design** — every element earns its place;
   nothing competes with what matters.
9. **Help users recognize, diagnose, and recover from errors** — error
   messages in plain language, naming the problem and the way out.
10. **Help and documentation** — when help is needed, it is findable,
    task-focused, and concrete.

A surface that clears all ten can still fail the **`quality-floor`**
(see `quality-floor.md`): unhandled states, an accessibility gap, or motion
that ignores a reduced-motion preference. Run the floor checklist first;
its misses are findings too, mapped to the floor commitment they breach.

## Severity rating

Rate each finding on a 0–4 scale. Severity is not how ugly the issue is —
it is how much it costs the user.

- **0 — Not a problem.** Disagreement on taste with no usability cost.
  Record only if it was raised; do not invent these.
- **1 — Cosmetic.** Noticed but doesn't impede a task. Fix if time allows.
- **2 — Minor.** Slows or mildly frustrates users; an easy workaround
  exists. Low-priority fix.
- **3 — Major.** Users struggle, take a wrong path, or give up on a
  secondary task. Important to fix; schedule it.
- **4 — Catastrophic.** Users cannot complete a core task, lose data, or
  are actively misled. Fix before ship.

### How to decide the level

Weigh three factors together — a problem rises when more of them stack:

- **Frequency** — does it hit every user on every visit, or a rare edge
  path? Common beats rare.
- **Impact** — once hit, is it a shrug or a wall? A blocker beats an
  annoyance.
- **Persistence** — does the user learn around it once, or trip on it
  every single time? A recurring trap beats a one-time stumble.

A rare-but-fatal issue and a constant-but-trivial one can land at the same
level; say which factors drove the rating so the score is defensible. Any
finding that violates the `quality-floor` accessibility commitment starts
at **3** and rises from there — the floor is not negotiable against taste.

## Mapping an observed issue to its principle

1. **State what you observed**, concretely — the surface, the step, the
   user's likely goal, what happened. No verdict yet.
2. **Ask which expectation broke.** "The user couldn't tell the save
   worked" → status. "The Cancel button vanished mid-flow" → control and
   freedom. "Two screens label the same action differently" → consistency.
3. **Pick the single best-fit principle.** If two fit, choose the one the
   user feels first; note the second only if it changes the fix.
4. **Check the floor.** If the observation is an unhandled state, an
   access barrier, or unmotivated/unstoppable motion, map it to the
   `quality-floor` commitment instead — those are floor findings.

## Turning findings into a prioritized list

Each finding is one row with five parts:

- **Severity** (0–4) and the factors that set it.
- **Principle violated** (or `quality-floor` commitment).
- **Observation** — what happens, where, to whom.
- **Why it costs the user** — the consequence, in their terms.
- **Recommendation** — one concrete, portable change that resolves it,
  expressed as design intent (the *what* and *why*), never a stack-specific
  *how*. If a quick mitigation and a deeper fix differ, name both.

Sort the list by severity descending; break ties by frequency. Lead with a
one-line headline — the count by severity — so the reader knows the shape
before the detail. Catastrophic and major findings go at the top where they
won't be missed; keep cosmetic ones, but clearly demoted, so nobody mistakes
the long tail for the headline.
