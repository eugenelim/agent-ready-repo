---
name: design-critique
description: "Use to evaluate an existing screen, flow, or mockup — an interactive, authoring-time heuristic critique that reviews against recognized usability principles, maps each issue to the principle it violates, rates severity, and returns a prioritized findings list with a fix per finding. Also supports a taste mode, an evidence-grounded critique of a screen against the grounded aesthetic reference (from aesthetic-direction) and platform fit. Triggers on 'critique this design', 'review this screen', 'what is wrong with this mockup', 'do a heuristic eval', 'is this usable', 'does this fit our aesthetic', 'does this feel right for the platform'. Do NOT use to name a felt direction (use aesthetic-direction), to derive tokens or scales (use design-system-foundations), or to structure hierarchy and reading flow (use layout-and-information-architecture)."
---

# Skill: design-critique

Runs a structured evaluation of a screen, flow, or mockup and returns a **prioritized, severity-rated findings list** — each issue mapped to the recognized usability principle or aesthetic reference it violates, with one concrete, portable recommendation. The list is the artifact: it turns "this feels off" into something a stakeholder can argue and a builder can act on.

Three modes, always run in this order:

1. **Quality-floor pass** — mandatory; checks all states, accessibility, and reduced-motion.
2. **Heuristic evaluation** — walks the surface against recognized usability principles.
3. **Taste critique** (when a grounded aesthetic reference is present) — checks the screen against the grounded aesthetic reference and platform fit.

> **Authoring-time self-review.** This skill is an **interactive, authoring-time** tool — it runs in the session, with the author. It is **not** a fresh-context pass and **not** an adversarial reviewer; a same-session critique marks its own homework. The genuine fresh-context UX review is the forked-context **`experience-reviewer`** agent — invoke it for an independent pass after the authoring session.

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
5. **Run the taste critique** (when a grounded aesthetic reference from `aesthetic-direction` is available). See `references/taste-critique.md` for the full method. In brief:
   a. **Check aesthetic alignment** — for each named goal in the grounded reference, ask whether the screen advances, is neutral to, or contradicts it. Ground each verdict in the recorded referent (persona + precedent + standards), never in a fresh opinion.
   b. **Check platform fit** — verify the screen respects the platform surface's (responsive-web / iOS / Android / cross-platform) conventions; point to the platform standard as the warrant, never reprint its values.
   c. **Map and rate taste findings** — each taste finding maps to the aesthetic goal it contradicts or the platform convention it violates; rate 0–4 by the same severity rubric (frequency × impact × persistence), with 0 reserved for genuine disagreement where the referent does not clearly resolve the call.
6. **Prioritize and recommend.** Merge all findings from all three modes. Sort worst-first across modes, lead with a count-by-severity headline, and give each finding one concrete, portable recommendation expressed as design intent — never a stack-specific implementation. Label the source mode (floor / heuristic / taste) so the reader knows which lens each finding came from.

## Anti-patterns to refuse

- **Claiming to be a fresh-context reviewer.** This skill is authoring-time self-review. The genuine fresh-context UX review is the forked-context `experience-reviewer` agent — it runs independently, between sessions, and does not mark its own homework.
- **Reprinting the aesthetic reference values.** The taste critique points to the grounded referent; it never reprints palette entries, type scales, spacing values, or any literal from the reference. See `references/taste-critique.md`.
- **Unrated opinions.** A finding without a severity and a violated principle or aesthetic goal is taste, not a critique. Map it or drop it.
- **Skipping the floor.** The `quality-floor` pass is mandatory, not optional polish. A surface can clear all ten heuristics and still fail the floor.
- **Prescribing the stack.** Recommendations name the *what* and *why* as design intent. The moment you reach for a framework, value, or property, you've left the method.
- **Burying the catastrophe.** A flat or alphabetized list hides the blocker. Worst-first, always, with the headline up top.
