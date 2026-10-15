---
title: "Change infrastructure"
summary: "Turn a plain-language infrastructure request into reviewed Terraform or OpenTofu, and keep your environment in sync with it."
pack: iac-terraform
kind: how-to
uses: [iac-terraform]
---

# Change infrastructure

Describe the infrastructure you need, and your agent writes Terraform or OpenTofu for it and stops at a reviewed plan. You run the apply, so nothing changes in your cloud until you say so.

## Describe what you need

Say what you want in plain words:

```text
Provision an S3 bucket with versioning enabled and a lifecycle policy that moves objects to Glacier after 90 days.
```

The agent runs the `generate-iac` skill and first checks that your team has recorded the decisions that govern this area, such as network exposure or how pipelines get permission. [Deciding before generating](../explanation/deciding-before-generating.md) explains why.

## Approve the decision

If nothing governs the area yet, the agent stops and asks instead of inventing a policy. Answer its question, then approve:

```text
Record that decision as an ADR and continue.
```

The agent writes the decision record, such as `docs/adr/0042-vpc-design.md`, and moves on to the code.

## Review the plan

The agent writes the `.tf` files, runs `terraform fmt`, `terraform validate`, a policy check, and a security check, then saves a `terraform plan` with a fingerprint so it cannot change after you read it. Ask to see it:

```text
Show me the plan and anything it will destroy.
```

The agent summarises each change and flags anything that deletes data or cannot be undone. A clean plan shows a change will apply, not that the result works. [What the preview cannot tell you](../explanation/what-the-preview-cannot-tell-you.md) covers the gaps.

## Apply it

You run `terraform apply` yourself, or your pipeline does. The agent never applies, never reads secrets, and never touches state files. Treat deleting a resource or migrating data as a decision for a person every time.

## Check for drift

Before the next change, or on a schedule, ask whether the real environment still matches your code:

```text
Check whether my infrastructure has drifted from the last plan.
```

The agent runs `reconcile-iac`, lists each drifted resource, and proposes to accept, correct, or defer it. You choose, and nothing is applied. [Infrastructure in the release loop](../explanation/infrastructure-in-the-release-loop.md) shows how this fits the rest of your release.

Next, [release the change](../../release-engineering/how-to/run-a-release.md).
