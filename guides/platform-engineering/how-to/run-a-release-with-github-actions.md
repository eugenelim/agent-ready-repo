---
title: Run a release with GitHub Actions
summary: Prepare and review a release, approve its exact digest, and check the protected job's deployment and cleanup evidence.
pack: platform-engineering
kind: how-to
uses: [platform-engineering]
---

# Run a release with GitHub Actions

Prepare and review a release, approve its exact digest, and check the protected job's deployment and cleanup evidence.

## Install and set up the sandbox

In your repository, install with [agentbundle](../../_shared/how-to/install-agentbundle.md):

```sh
agentbundle install --pack platform-engineering
```

Core is optional; release checks need no Core event or Terraform.
You need Python 3.11+, GitHub.com Actions, and an owner who can configure GitHub
and AWS. Follow [setup and prerequisites](../reference/release-admission.md#github-actions-prerequisites)
to install the three workflows, owner-authored controls and protected sandbox.

## Check captured settings

Ask your agent to read the captured settings without changing remote controls:

```text
Run release-loop's GitHub Actions readiness check with my controls, snapshot and three workflow files. Report each unmet code and pause deploy and teardown unless every control is met.
```

Authoring, collection, admission and review remain usable when readiness blocks.
[Capture recipes](../reference/release-admission.md#github-actions-captures)
write local evidence; the protected job repeats capture before mutation.

## Prepare and review

Ask the agent to dispatch prepare on the protected release branch:

```text
Run release-prepare.yml. Download its single release-candidate artifact, obtain focused reliability and security pre-deploy reviews, then check-stage --stage pre-deploy against its admission. Stop on refusal.
```

Prepare collects and admits without cloud credentials. Preserve its run id,
admission digest and both review records. Prepare again if workflow, controls
or candidate bytes change.

## Dispatch and approve

Ask the agent to dispatch with the reviewed inputs:

```text
Dispatch release-deploy.yml with prepare_run_id, admission_sha256 and pre_deploy_reviews. Show me the exact admission digest and wait for the required independent human reviewer.
```

That reviewer checks the inputs and approves in GitHub with
`admission:<64-character SHA-256>` in the comment. The reviewer must differ
from the triggering actor and agent. Approval binds this run and digest only.
The agent never approves or changes a gate.

## Check execution and cleanup

Ask the agent to report the protected job's evidence:

```text
Check verify-admission, bind, credentials, budget, audit, recheck, mutate-object, observe, guarded teardown, summary and terminal ops. Require an in-job audited summary. Run post-deploy and final reviews and stage checks; record achieved stage, cleanup and remaining risks for my decision.
```

The job uploads a `release-records` artifact (binding, decision, receipt, ops,
observation and summary) whenever binding succeeded; reconciliation reads it.
Budget refusal writes no decision. Teardown needs successful recheck and matching
effect bytes and marker. A failed, cancelled or unknown run needs
[reconciliation](../reference/release-admission.md#github-actions-recovery-and-limits)
before retry. Re-runs are refused; each retry needs a new approved dispatch within
the same limit. Never use a weaker fallback. This path grants no production
authority and cannot prove exactly-once effects.

Next: [Release admission](../reference/release-admission.md#github-actions-execution).
