---
title: "Release a change"
summary: "Deploy a finished change to a test environment, check it works, and record your approval to ship it to production."
pack: release-engineering
kind: how-to
uses: [release-engineering, core]
---

# Release a change

Name the change you are releasing, and your agent runs the release loop on it.

## Validate a direct candidate

For an image-only CI candidate or reviewed infrastructure bundle, ask:

```text
Validate my schema "2.0" release-handoff.yaml with scripts/release_handoff.py validate using my protected evidence root and trusted policy. Report gaps before starting a release.
```

You get a JSON result without deploying. A direct caller needs no G4 event;
validation checks bytes and bindings, not producer authenticity or ship approval.
The [handoff reference](../reference/release-handoff.md) lists commands and fields.

## Import a v1 handoff

To create a separate v2 candidate, ask:

```text
Use scripts/release_handoff.py import-v1 with my trusted policy and a fresh output under my protected root. Preserve the v1 input bytes and report missing facts; use only actual bound evidence from my supplement.
```

You get a new candidate and named gaps. Resolve incomplete evidence before release;
existing v1 runs can keep the tolerant-reader path.

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

The harness, the tooling that runs your agent, records your approval, so the agent cannot give it for itself. The agent stops there and does not ship: you or your deploy pipeline rolls out to production with the approved record in hand. To stop, say "Hold the release" and give a reason. The harness records your choice, and the agent tears down the temporary environment and keeps the build so you can try again.

If the loop runs out of rounds or budget, [the record reference](../reference/release-readiness-record.md#when-the-loop-runs-out-of-rounds) says what to do.

Next, [measure delivery](../../atlassian/how-to/measure-flow-and-dora-metrics.md).
