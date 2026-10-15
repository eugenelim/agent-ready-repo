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
- Watch telemetry, feed deployed findings back to the build loop without you relaying them, and redeploy until the result is stable.
- Stop and present a release-readiness record, a structured go or no-go recommendation, for you to approve.
- Write a Service Level Objective document, with an error budget policy, for a service.
- Name the deploy, smoke, and teardown artifacts it needs and offer to scaffold them when your repository has none.

## Skills

- **`release-loop`** — Drives deployed end-to-end validation, with a round cap, a cost budget, and security controls on the deploy.
- **`define-slo`** — Writes an OpenSLO YAML file at `slos/<service>.yaml` that the release loop reads for error-budget status.

Subagent: **`release-lead`** runs the release loop. It works beside the build loop's supervisor and is not a mode of it.

## Works with

Works with Claude Code, Kiro IDE, Codex, Copilot, Cursor, and Gemini CLI. It requires [Core](../core/README.md), after `work-loop` reports the build done. [IaC (Terraform)](../iac-terraform/README.md) covers the infrastructure change. See [Release a change](../../guides/release-engineering/how-to/run-a-release.md) and [Measure delivery](../../guides/atlassian/how-to/measure-flow-and-dora-metrics.md).

## Questions

**Does it ship to production?** No. The production ship is always yours. The agent stops at the release-readiness record.

**What does it do on its own?** Reversible work: the build loop, and deploy, test, observe, iterate, and tear down on ephemeral environments. Real users or data, data migrations, spend over an agreed limit, and security changes wait for you.

**Does it ship my deploy pipeline?** No. It has no runtime engine and no canary analyzer. It uses the deploy, smoke, and teardown artifacts you have, or names the ones it is missing.

**Why repo scope only?** It runs in the repository where the build happened and reuses Core's reviewers there.

## Details

Scope: repo (default) · Version: 0.1.11 · Source: [packs/release-engineering](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/release-engineering)
