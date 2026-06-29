---
name: design-critique
description: Use to evaluate an existing screen, flow, or mockup — an interactive, authoring-time heuristic critique that reviews against recognized usability principles, maps each issue to the principle it violates, rates severity, and returns a prioritized findings list with a fix per finding. Triggers on "critique this design", "review this screen", "what's wrong with this mockup", "do a heuristic eval", "is this usable". Do NOT use to name a felt direction (use `aesthetic-direction`), to derive tokens or scales (use `design-system-foundations`), or to structure hierarchy and reading flow (use `layout-and-information-architecture`).
---

# Skill: design-critique

Runs a structured heuristic evaluation of a screen, flow, or mockup and returns a **prioritized, severity-rated findings list** — each issue mapped to the recognized usability principle it violates, with one concrete, portable recommendation. The list is the artifact: it turns "this feels off" into something a stakeholder can argue and a builder can act on.

## When to invoke

Confirm all three before drafting; if any fails, resolve it first.

1. **There is something concrete to review** — a screen, flow, mockup, or described surface. A vibe with no artifact isn't ready; route to `aesthetic-direction`.
2. **You know whose task you're judging** — a critique needs a user and a goal. Without them, severity is unanchored guesswork; draw out the primary task first.
3. **You're evaluating, not creating** — the ask is "is this good," not "make this." If it's deriving values or structuring a layout, hand to `design-system-foundations` or `layout-and-information-architecture`.

## Procedure

1. **Frame the surface.** Name the user, the primary task, and each step under review. This anchors every severity call that follows.
2. **Apply the shared floor first.** Run the `quality-floor` checklist at `references/quality-floor.md` against the surface — handle all states, the accessibility floor, the reduced-motion principle. Each miss is a finding mapped to the floor commitment it breaches; accessibility misses start at major.
3. **Run the heuristic evaluation.** Walk the surface against the recognized usability principles in `references/heuristics.md`. For each problem, record what you observed before you judge it.
4. **Map and rate.** Map each finding to the single best-fit principle (or floor commitment) and assign a 0–4 severity, naming the frequency × impact × persistence factors that set it. See `references/heuristics.md`.
5. **Prioritize and recommend.** Sort worst-first, lead with a count-by-severity headline, and give each finding one concrete, portable recommendation expressed as design intent — never a stack-specific implementation.

## Anti-patterns to refuse

- **Being a `work-loop` reviewer.** This is an interactive, authoring-time skill — the design-side counterpart to a code-review skill, not a forked-context reviewer subagent. It runs in the conversation, with the author, not as an automated gate.
- **Unrated opinions.** A finding without a severity and a violated principle is taste, not a critique. Map it or drop it.
- **Skipping the floor.** The `quality-floor` pass is mandatory, not optional polish. A surface can clear all ten heuristics and still fail the floor.
- **Prescribing the stack.** Recommendations name the *what* and *why* as design intent. The moment you reach for a framework, value, or property, you've left the method.
- **Burying the catastrophe.** A flat or alphabetized list hides the blocker. Worst-first, always, with the headline up top.
