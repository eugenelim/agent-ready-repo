---
name: aesthetic-direction
description: Use when a designer or stakeholder has a felt "vibe" but no named direction — turning a vague mood into ranked emotional/brand goals and an aesthetic-direction doc the rest of the build references. Triggers on "make it feel premium/calm/playful", "I want it to feel like X", "what's the vibe here", "we need a look and feel", "before we pick colors/type". Runs the interrogation that converges a mood into named goals, then records which goal wins when two goals conflict. Do NOT use to derive a token or scale taxonomy (use `design-system-foundations`), to structure hierarchy and reading flow (use `layout-and-information-architecture`), or to evaluate an existing screen (use `design-critique`).
---

# Skill: aesthetic-direction

Turns a vague "vibe" into a small set of **named, ranked emotional and brand goals** and records them in an aesthetic-direction doc the rest of the build references. The doc is the durable artifact: it lets every later choice point back to a goal instead of re-arguing taste.

## When to invoke

Confirm all three before drafting; if any fails, push back and resolve it first.

1. **There is a real vibe to name** — the user can describe a feeling, an audience, or examples to react to. A blank "make it nice" is not yet a brief; draw out a first felt word before proceeding.
2. **The direction isn't already named** — no current aesthetic-direction doc owns this surface. If one exists, you're amending it, not starting fresh.
3. **You're naming direction, not deriving values** — the moment the ask is spacing, type, or color *values*, hand off to `design-system-foundations`. This skill stops at named goals.

## Procedure

1. **Run the interrogation.** Open from the felt vibe, probe the emotions, associations, and brand attributes behind it, and converge on a short set of named goals — each a noun phrase a non-designer can recall. Sharpen each against its opposite. Load `references/interrogation-sequence.md`.
2. **Rank the goals.** Order them so a tie can break. The top goal is the dominant one that wins when goals conflict.
3. **Record arbitration.** For each likely conflict, name which goal wins and why, so the build doesn't re-litigate it. Load `references/coherence-arbitration.md`.
4. **Capture the doc.** Copy `assets/aesthetic-direction-template.md` into the user's repo and fill it: the ranked goals, what each means and what would violate it, the dominant goal, and open questions.
5. **Hold the floor.** The direction must not fight the shared `quality-floor` checklist (`../design-critique/references/quality-floor.md`) — accessibility is not negotiable against aesthetics. If a goal pulls against the floor, the floor wins; record it as an open question, not a trade-off.
6. **Hand off.** Once the goals are named and ranked, hand to `design-system-foundations` to derive the tokens and scales that express them.

## Anti-patterns to refuse

- **Printing the answer.** No palette, font name, or spacing/timing value here. This skill produces *direction*, not the values that express it — those are `design-system-foundations`' job.
- **Goals nobody can recall.** If a goal isn't a short noun phrase a non-designer remembers, it can't arbitrate a choice later. Rewrite it until it sticks.
- **Unranked goals.** A flat list of equals can't break a tie. Refuse to close without a dominant goal.
- **Copying an example whole.** "Make it like X" is a starting probe, not a direction. Name *which qualities* of X you're after and which you're leaving — see the interrogation reference.
- **Re-deriving taste mid-build.** Once the doc exists, conflicts resolve against it, not against fresh opinion. Amend the doc deliberately; don't quietly drift.
