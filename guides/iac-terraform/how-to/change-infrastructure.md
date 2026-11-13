---
title: "Change infrastructure"
summary: "Turn a plain-language infrastructure request into reviewed Terraform or OpenTofu, and keep your environment in sync with it."
pack: iac-terraform
kind: how-to
uses: [iac-terraform]
---

# Change infrastructure

Tell your agent what infrastructure you need, and it stops at a plan for you to read.

Install `iac-terraform` with `agentbundle install --pack iac-terraform` in your
repository. Keep Terraform or OpenTofu on your path. The installer retains its
declared dependencies; core and governance workflows are optional integrations
for authoring.

## Describe what you need

Say what you want in plain words:

```text
Provision an S3 bucket with versioning enabled and a lifecycle policy that moves objects to Glacier after 90 days.
```

The agent runs the `generate-iac` skill and first checks that your team has recorded the decisions that govern this area, such as network exposure or how pipelines get permission. [Deciding before generating](../explanation/deciding-before-generating.md) explains why.

## Confirm the governing sources

Ask the agent to check your repository's instructions, accepted decisions and explicit inputs:

```text
Discover governing sources for the files we will change. Record constraints and source digests in governance-summary.json, run check-summary, and show me any stop result.
```

The agent proceeds only on `ready`. Resolve missing authority, conflicts or open
questions with the owner before continuing. No index, decision template or
bootstrap is needed. Optional integrations cannot override a refusal or permit a
weaker fallback. The [authoring-gate reference](../reference/authoring-gate.md)
lists commands, record fields and every stop code.

## Review the plan

The agent writes the `.tf` files, runs `terraform fmt`, `terraform validate`, a policy check, and a security check, then saves a `terraform plan` with a fingerprint so it cannot change after you read it. Ask to see it:

```text
Show me the plan and anything it will destroy.
```

The agent records evidence for all seven areas of the canonical infrastructure
review checklist and runs `check-review` against the exact plan and checklist
bytes. Missing coverage or an open blocker stops the handoff.

The agent summarises each change and flags anything that deletes data or cannot be undone. A clean plan shows a change will apply, not that the result works. [What the preview cannot tell you](../explanation/what-the-preview-cannot-tell-you.md) covers the gaps. You run `terraform apply` yourself, or your pipeline does. The agent never applies, never reads secrets, and never touches state files.

## Validate the saved-plan bundle

Ask the agent to package the reviewed saved plan and its evidence:

```text
Emit an iac-plan-bundle.v1 with the saved plan, inspection, decision evidence and bound validation, policy, security and review checks. Validate it with scripts/plan_bundle.py validate using my protected evidence root and trusted policy.
```

You get a JSON validation result. Keep sensitive plan bytes in protected storage;
commit references and digests. The [plan-bundle reference](../reference/plan-bundle.md)
gives the terminal command and recovery codes. Validation never runs Terraform
and grants no apply approval. Direct callers need no G4 event.

## Check for drift

Before the next change, or on a schedule, ask whether the real environment still matches your code:

```text
Check whether my infrastructure has drifted from the last plan.
```

The agent runs `reconcile-iac`, checks managed drift or an incoming diff against the same governance summary, and proposes dispositions. Resources absent from state need a separate inventory. You choose, and nothing is applied. [Infrastructure in the release loop](../explanation/infrastructure-in-the-release-loop.md) shows how this fits the rest of your release.

Next, [release the change](../../release-engineering/how-to/run-a-release.md).
