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

Describe the change you want, and your agent takes it through four stages, one section each below.

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

Before completing a change, the work-loop checks all active `Parent intent:` and `Brief:` fields in each artifact the change adds or modifies. A typed pointer must name an existing target of the field's type. A body-only edit still selects that artifact for checking.

## Close it out

When the change is merged, ask for the record:

```text
Close this work out.
```

The agent runs `close-work`, writes `docs/lifecycle/<slug>.md` with what shipped, what did not and why, and updates the workspace. To keep a lesson for later sessions, ask for `project-knowledge`, which saves what this work taught the project into the repository.

Next, [release the change](../../release-engineering/how-to/run-a-release.md).
