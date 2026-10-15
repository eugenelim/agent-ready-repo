---
title: "Roll out across an enterprise"
summary: "Widen adoption one stage at a time, with a named owner deciding at each step."
pack: _shared
kind: how-to
---

# Roll out across an enterprise

Widen adoption from one pilot to the whole organization one stage at a time, with a named owner deciding at each step: pilot, team wave, then organization-wide.

## Prepare the pilot

Ask your agent to check the pilot with you before you begin:

```text
Help me prepare a pilot for a task the participant already knows and can verify in minutes. Ask me to confirm the rollout track, reads and writes, human controls, artifact recipient, measures, rollback, and stop condition before we begin. Do not widen the rollout until the named owners accept the stage evidence.
```

The agent asks for each item until the pilot is fully described. Choose the track from who takes part: technical for engineers and technical product managers, enterprise for clients working with a forward-deployed engineer, and non-technical for knowledge workers and designers.

## Name the owners

Four roles hand work forward in order: the champion, the CTO or executive sponsor, the platform team, and the people who use the workflow. Each role accepts the handoff by name, and none accepts another role's decision.

## Decide at each stage

Each stage ends with a decision record, and you review it with the owners:

```text
Review this stage decision with the sponsor, platform owner, and participants. Challenge missing evidence, then return exactly one verdict without widening the recorded scope.
```

The verdict is `stop`, `revise`, `hold`, or `advance`, and `advance` covers only the scope written in the record. The [enterprise rollout playbook](../reference/enterprise-rollout-playbook.md) has the checklist, the fields for each stage, and the record templates.

Next, [import and curate skills](../../catalogue-curation/how-to/survey-a-repo.md). For the technical side of distribution, see [Set enterprise defaults](configure-catalogue-enterprise-distribution.md), [Build a pack](build-an-org-stack-pack.md), and the [live demo](../../core/how-to/run-a-live-demo.md).
