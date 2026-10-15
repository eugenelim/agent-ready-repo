---
title: "Run the build loop"
summary: "Take a feature, fix, refactor, migration, or upgrade from a request to merged, closed work."
pack: core
kind: how-to
uses: [core]
aliases:
  - guides/core/how-to/write-the-contract
  - guides/core/how-to/run-the-loop
  - guides/core/how-to/close-it-out
---

# Run the build loop

Ask your agent to build a change and it works through four stages: route the request, write down what done means, build and check it, then close it out. The same loop handles features, fixes, refactors, migrations, and upgrades.

## Route the request

Describe the work in your own words, however vague:

```text
I need to make the login test deterministic. Route this request.
```

The agent runs `work-intake`, picks the skill that owns the request, and tells you why.

## Write the contract

Ask for a spec, a short document that says what done means, with a plan for how to get there:

```text
Write a spec for making the login test deterministic.
```

The agent writes `docs/specs/<slug>/spec.md` and `plan.md`, each acceptance criterion paired with a check that can fail. Read the spec and approve it before building. For work that spans several specs, ask for a brief first with `author-brief`.

## Run the loop

Point the agent at the approved spec:

```text
Run the work loop on this spec.
```

The agent plans, builds, runs your checks, and sends the change to independent reviewers, pausing wherever it needs your decision. If a check fails, it goes back and fixes the build before review.

## Close it out

When the change is merged, ask for the record:

```text
Close this work out.
```

The agent runs `close-work`, writes `docs/lifecycle/<slug>.md` with what shipped, what did not and why, and updates the workspace. Anything you want to keep, ask for it with `project-knowledge`.

Next, [release the change](../../release-engineering/how-to/run-a-release.md).
