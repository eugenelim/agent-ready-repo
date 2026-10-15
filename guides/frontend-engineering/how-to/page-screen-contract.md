---
title: "Build a page or component"
summary: "Build a web page or component that is checked for accessibility, states, and layout before it ships."
pack: frontend-engineering
kind: how-to
journey: frontend-engineering
uses: [frontend-engineering]
---

# Build a page or component

Start by asking your agent how much planning the page or component needs.

## Pick how much to plan

A tooltip and a checkout flow do not need the same amount of planning. Ask the agent to choose:

```text
Pick the risk tier for this page and tell me which contract fields and states it owes.
```

The agent proposes explore, pilot, or production and lists what that tier requires. [Choose the depth](choose-the-depth.md) explains the three tiers.

## Write the contract

A page or screen contract is a short note that settles who the page is for, its main action, what happens on an error, and how it behaves on a small screen. Ask for the right-sized one:

```text
Write the right-sized page/screen contract for this page before implementation.
```

The agent drafts the full 12-field contract for a new route, a few fields for a small change, or a one-line "no contract needed" for a typo fix. It writes no UI code yet. Approve the contract, then keep it in the feature spec.

## Build it

If your team has design work, name the folder, and the agent reads it before writing code ([what it reads](read-the-design-handoff.md)). Then ask for the build:

```text
Build the notification panel from this design brief, with empty, unread, and overflow states.
```

The agent runs the `frontend-engineering` skill in create mode and writes semantic HTML, base CSS, responsive layout, and every state. For a shared component, ask for `component-contract` first so its props, slots, and events are settled before any code.

## Check the result

Ask the agent to verify the page before you ship it:

```text
Verify this page before the release.
```

The agent checks the HTML, accessibility, styles, and the rendered page, then writes an evidence manifest listing what passed and what could not run. To review a page you did not build, [run a frontend audit](run-an-audit.md); to look at how it renders, [inspect the rendered page](inspect-the-rendered-page.md).

Next, [review the pull request](../../core/how-to/review-someone-elses-pr.md).
