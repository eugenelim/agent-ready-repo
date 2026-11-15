# Release Engineering

Your agent can test your built change in a temporary deployed environment, fix what it finds, and hand you a release-readiness record for the production decision.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install it from inside the repository where your agent built the change:

```bash
cd path/to/your-repo
agentbundle install --pack release-engineering
```

## What your agent can do

- Deploy the integrated whole to an ephemeral environment and run end-to-end tests.
- Watch telemetry, route deployed findings to the recorded repair owner or a human handoff, and re-admit reviewed replacements before redeployment.
- Stop and present a release-readiness record, a snapshot of the checked release evidence, for you to approve.
- Write a Service Level Objective document, with an error budget policy, for a service.
- Name the deploy, smoke, and teardown artifacts it needs and offer to scaffold them when your repository has none.

## Skills

- **`prepare-release-handoff`** — Collects existing evidence into a candidate or reports named gaps. It runs no build, test, plan or fetch.
- **`release-loop`** — Drives deployed end-to-end validation, with a round cap, a cost budget, and security controls on the deploy.
- **`define-slo`** — Writes an OpenSLO YAML file at `slos/<service>.yaml` that the release loop reads for error-budget status.

Subagents: **`release-lead`** runs the release loop; **`release-reliability-reviewer`** and **`release-security-reviewer`** check the admitted candidate against their focused checklists. The release lead works beside the build loop's supervisor.

## Works with

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, and Kiro IDE. Installation requires [Core](../core/README.md). The direct evidence path accepts CI, human-supplied and other workflow builds without a core event. Core reviewers are optional additions after the required focused checks; their refusal stops the step without a weaker fallback. [IaC (Terraform)](../iac-terraform/README.md) covers the infrastructure change. See [Release a change](../../guides/release-engineering/how-to/run-a-release.md) and [Measure delivery](../../guides/atlassian/how-to/measure-flow-and-dora-metrics.md).

Collect evidence, admit the candidate, then run `check-review` on both focused review records and `check-stage` before advancing stages. Final requires both roles at pre-deploy, post-deploy and final, plus budgets, cleanup and remaining risks; success returns `human-decision-required`. A `ready`, `admitted`, review `pass` or stage progression grants no execution or production authority. See [Release admission](../../guides/release-engineering/reference/release-admission.md) for commands, refusal codes and the stage table.

## Questions

**Does it ship to production?** No. The production ship is always yours. The agent stops at the release-readiness record.

**What does it do on its own?** Reversible work: the build loop, and deploy, test, observe, iterate, and tear down on ephemeral environments. Real users or data, data migrations, spend over an agreed limit, and security changes wait for you.

**Does it ship my deploy pipeline?** No. It has no runtime engine and no canary analyzer. It uses the deploy, smoke, and teardown artifacts you have, or names the ones it is missing.

**Does it tie a release to a Jira issue?** No. The release pack makes no Jira call and keeps no live link to an issue. An issue id appears only as plain text in a changelog delta entry, taken from the commits or written there, with no lookup or live link.

**Why repo scope only?** Its evidence, policy and deployment procedures belong to the target repository.

## Details

Scope: repo (default) · Version: 0.3.0 · Source: [packs/release-engineering](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/release-engineering)
