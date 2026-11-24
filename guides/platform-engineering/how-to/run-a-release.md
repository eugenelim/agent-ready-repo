---
title: Release a change
summary: Deploy a finished change to a test environment, check it works, and record your approval to ship it to production.
pack: platform-engineering
kind: how-to
uses: [platform-engineering]
---

# Release a change

Gather release evidence, check the candidate, and prepare a release-readiness record for your decision.

## Install the release pack

In your repository, install with [agentbundle](../../_shared/how-to/install-agentbundle.md):

```sh
agentbundle install --pack platform-engineering
```

Core is optional; collection and admission need no Core workflow event.

## Collect existing evidence

Give your agent the evidence directory, request file and trusted policy:

```text
Prepare a release handoff from request.json under my protected evidence root, using trusted-policy.json. Write candidate.yaml only when ready. Report all gaps unchanged; do not run missing work.
```

The agent hashes local files and validates the candidate; it reports gaps without building, testing, planning or fetching. Resolve those gaps with the named owner before retrying. For older input, use the separate [v1 import path](../reference/release-handoff.md#import-gaps).

## Admit and review the candidate

Ask the agent to pin the candidate and check both focused reviews:

```text
Admit candidate.yaml for the expected staging environment and account using my trusted policy. Write admission.json under the evidence root. Run reliability and security review against that admission and check the pre-deploy stage. Stop on any refusal.
```

The agent checks the bytes again, then writes the admission record. Both local reviewer roles must pass; optional Core reviewers cannot replace them. A Core refusal stops the step without a weaker fallback. See [Release admission](../reference/release-admission.md) for commands, codes and records.

## Validate the deployed change

With [deploy, smoke and teardown procedures](../reference/release-readiness-record.md#wire-your-deploy-target) available, ask:

```text
Run the release loop for this admitted candidate within the agreed authority and budget. Check post-deploy reviews using fresh runtime evidence. Route failed checks to the repair owner and preserve the attempt limit.
```

The agent gathers deployed evidence and checks stage progression. A replacement candidate re-enters collection, admission and review.

## Decide whether to ship

Ask for the evidence before making your decision:

```text
Show the final release-readiness record with budgets, cleanup and remaining risks. Hold production until I decide.
```

The final stage requires passing pre-deploy and post-deploy reviews and complete final facts. Collection readiness, admission, a review pass and stage progression grant no execution or production authority. You or your authorized deploy pipeline carries out the ship decision.

Next: [Release admission](../reference/release-admission.md).
