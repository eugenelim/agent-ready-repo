---
title: "Release a change"
summary: "Deploy a finished change to a test environment, check it works, and ship it to production when you approve."
pack: release-engineering
kind: how-to
uses: [release-engineering, core]
---

# Release a change

Name the change you are releasing, and your agent runs the release loop on it.

## Start the release

Describe what you are releasing. The agent needs a way to create and tear down a temporary environment; [wire your deploy target](../reference/release-readiness-record.md#wire-your-deploy-target) first if it has none:

```text
Run the release loop for the v2.3.0 payment service deployment.
```

The `release-lead` agent deploys the build to a temporary environment, runs the end-to-end tests, and reads the metrics and logs. If a check fails, it hands the problem back to the build loop and redeploys.

## Read the readiness record

When the checks hold, the agent shows a release-readiness record. Ask for it in plain words if it is not on screen:

```text
Show me the release-readiness record.
```

The record shows how many rounds it took, the operational review, the security review, and the budget used. The operational and security reviews each end in PASS, PASS-WITH-NOTES, or FAIL. PASS-WITH-NOTES does not block you. FAIL does. [The record reference](../reference/release-readiness-record.md) lists every field.

## Approve or hold

The ship to production is always your decision, and the agent asks you for it. To approve the ship, say so:

```text
I approve shipping v2.3.0 to production.
```

Your approval is recorded by the tooling, so the agent cannot give it for itself. To stop, say "Hold the release" and give a reason. The agent records your choice, tears down the temporary environment, and keeps the build so you can try again.

If the loop runs out of rounds or budget, [the record reference](../reference/release-readiness-record.md#when-the-loop-runs-out-of-rounds) says what to do.

Next, [measure delivery](../../atlassian/how-to/measure-flow-and-dora-metrics.md).
