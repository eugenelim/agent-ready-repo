---
title: "Release a change"
summary: "Deploy a finished change to a test environment, check it works, and ship it to production when you approve."
pack: release-engineering
kind: how-to
uses: [release-engineering, core]
---

# Release a change

Ask your agent to run the release loop on a finished change. It deploys to a temporary environment, tests it, and stops for your approval before anything reaches production.

## Start the release

Describe what you are releasing:

```text
Run the release loop for the v2.3.0 payment service deployment.
```

The `release-lead` agent deploys the build to a temporary environment, runs the end-to-end tests, and reads the metrics and logs. If a check fails, it hands the problem back to the build loop and redeploys.

## Wire your deploy target

The agent needs a way to create and tear down the temporary environment. If it cannot find one, it tells you what it looked for. Ask it what to add:

```text
Which deploy target do you need, and what is missing?
```

The agent names the missing deploy, test, or teardown step for your platform, such as a Kubernetes namespace, a cloud preview environment, or a Docker Compose file.

## Read the readiness record

When the checks hold, the agent shows a release-readiness record. Ask for it in plain words if it is not on screen:

```text
Show me the release-readiness record.
```

The record gives each result as PASS, PASS-WITH-NOTES, or FAIL: how many rounds it took, the operational review, the security review, and the budget used. PASS-WITH-NOTES does not block you. FAIL does. [The record reference](../reference/release-readiness-record.md) lists every field.

## Approve or hold

The ship to production is always your decision, and the agent asks for it on a choice card. To ship, approve there or say so:

```text
I ratify shipping v2.3.0 to production.
```

Your approval is recorded by the tooling, so the agent cannot give it for itself. To stop, say "Hold the release" and give a reason. The agent records your choice, tears down the temporary environment, and keeps the build so you can try again.

If the loop runs out of rounds or budget before the checks hold, the agent reports what failed and the likely fix. Fix the build and re-enter the loop, loosen a policy that is too strict for a known flaky test, or decide not to ship this version.

Next, [measure delivery](../../atlassian/how-to/measure-flow-and-dora-metrics.md).
