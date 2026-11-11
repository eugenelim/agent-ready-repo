---
title: "Design the experience"
summary: "Go from a customer's goal to reviewed screens that are ready to build."
pack: experience-design
kind: how-to
uses: [experience-design]
aliases:
  - guides/experience-design/how-to/derive-the-screen-flow
  - guides/experience-design/how-to/design-each-screen
  - guides/experience-design/how-to/review-independently
---

# Design the experience

Start with what a customer is trying to do, and the agent writes each file into your design folder and tells you the path.

## Map the journey

A journey map follows one customer through their goal, step by step. To write one, ask:

```text
Map the journey for a new account owner who wants to connect their first data source. The current experience breaks at setup.
```

The agent writes `journeys/<slug>.md` with actions, emotions, and pains, and marks the best, worst, and final moments.

## Say what each screen says

To decide the message before any layout, ask:

```text
Define what this account-setup surface should say, for whom, and to what objective.
```

The agent writes a content brief at `content/<slug>.md`.

## Turn it into screens

To get the screens and the routes between them, ask:

```text
Turn the journey into screens, transitions, failure routes, and one brief per screen.
```

The agent writes `screens/<slug>-flow.md` and one short brief per screen in `screens/<slug>/`. You approve the journey and the screen list before design continues.

## Set the design direction

To turn the pains into rules and a look, ask for principles first:

```text
Turn these journey pains and peak moments into three to five design principles.
```

The agent writes `principles/<slug>.md`. Ask `creative-direction` for `direction/<slug>.md`, and `design-system` for `tokens/<slug>.md` when your product has no system that covers the work. You approve the aesthetic direction before screens are designed. [Establish design intent](establish-design-intent.md) shows each prompt and when the design system is required.

## Design each screen

To lay out a screen around its main task, ask:

```text
Organize this screen around its primary task, content rank, recovery paths, and wayfinding.
```

The agent writes `screens/<slug>-ia.md`.

## Add the behavior

To fill in how a screen responds, ask:

```text
Design the behavior for <screen>, including feedback, validation, recovery, and motion.
```

The agent fills in that screen's brief.

## Review the design

To check your own work first, ask:

```text
Review this design set against its user task, principles, quality floor, genre rubric, and grounded aesthetic direction.
```

The agent lists findings by severity and writes nothing to disk. You review the designs and decide which findings to fix. For a cold read in a fresh context, run `experience-reviewer` on a screen brief such as `docs/design/screens/onboarding-flow.md`.

Next, [write the contract](../../core/how-to/start-the-work.md) for the reviewed design.
