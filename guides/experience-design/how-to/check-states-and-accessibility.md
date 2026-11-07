---
title: Check a screen for states and accessibility
summary: Review a screen, flow, or mockup against the pack's quality floor, which holds every state designed, the accessibility floor cleared, and motion that honors reduced-motion.
pack: experience-design
kind: how-to
---

# Check a screen for states and accessibility

Review a screen, flow, or mockup for missing states, accessibility gaps, and motion problems before it ships, using the `design-review` skill. You need [the `experience-design` pack installed](../../_shared/how-to/install-packs.md) and something concrete to review: a screen, flow, mockup, or a written description of one. Name the user and their goal, because the review rates each problem against whose task it blocks.

## Ask for the review

Name the screen, the user, and the checks you want:

```text
Review the checkout payment screen for usability problems. The user is a first-time buyer completing a purchase. Check every state and the accessibility floor.
```

The agent runs the quality-floor pass, the pack's shared checklist for states, accessibility, and motion, first, then a usability review of the screen, and returns findings rated blocker, major, minor, or advisory, worst first, each with one recommendation. Nothing is written to your files.

## Narrow the review to one part

Ask for one part of the floor when you only need that:

```text
Check only the empty, loading, and error states of the checkout payment screen.
```

The agent limits the findings to those states. The floor has three parts, and a choice that cannot meet one is reported as a finding, not deferred.

- **States.** Every state the screen can be in is designed: empty (first run and no results), loading, error, success, partial, and disabled, plus permission denied on a gated screen, one that needs permission to view.
- **Accessibility.** The design meets WCAG, the Web Content Accessibility Guidelines, at the level your context requires: readable contrast, every action reachable by keyboard with visible focus, meaning never carried by color alone, accessible names for controls and images, and forgiving targets and timing.
- **Motion.** Every animation tells the user something, and the design honors reduced-motion settings.

## What this job does not do

The skill reviews a screen, flow, mockup, or described surface; a Figma file is not read directly, so give it an exported image of the frame or a written description. It is a review with you in the same session, not an independent one. For a fresh-context pass after you author, ask for the `experience-reviewer` agent. Reviewing code defects belongs to frontend engineering.

Next, [choose how much design a screen owes](choose-the-depth.md).
