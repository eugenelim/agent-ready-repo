---
title: Your first release
summary: A complete walkthrough of a release cycle from deploy-ready build to a ratified ship decision — deploy, converge, and ratify G5.
pack: release-engineering
kind: tutorial
---

# Your first release

**What you'll build:** a ratified production ship decision for a concrete scenario — a payment refund endpoint with a database migration — walked through all six stages of the release loop.
**Prerequisites:** `core` and `release-engineering` installed at repo scope, and an ephemeral deploy target configured — see [Prerequisites](#prerequisites).
**Time:** 15 minutes to read; an actual release run takes as long as your e2e suite and deploy pipeline (a few minutes to 30+).

This tutorial walks you through a complete release cycle from end to end — from a deploy-ready build to a ratified ship decision — so you understand what each stage does and what you're looking at when `release-lead` surfaces a result.

We'll follow a concrete scenario: a small team just finished a work-loop run that ships a new `/payments/refund` API endpoint and a related database migration. `core` is installed, tests are green, the adversarial review says `Clean`. Now it's time to get it to production.

```text
Run the release loop for the payment refund endpoint deployment.
```

**What you'll learn:**
- What the release loop does at each stage
- How to read the release-readiness record
- What the G5 consent gate looks like in practice
- How the inner↔outer feedback seam works when something goes wrong

**Time:** reading this tutorial takes about 15 minutes. An actual release loop run takes however long your e2e suite and deploy pipeline take — from a few minutes for a small service to 30+ minutes for a large one with a thorough e2e suite.

---

## Prerequisites

Before starting, verify:

```bash
agentbundle list-installed
```

You should see both `core` and `release-engineering` listed at repo scope. If not, install them:

```bash
agentbundle install --pack core
agentbundle install --pack release-engineering
```

You'll also need a configured ephemeral deploy target. For this tutorial, we'll assume one is already wired. If yours isn't, see [run a release](../reference/release-readiness-record.md#wire-your-deploy-target).

---

## Trigger the release loop

With `release-lead` active, you start the release like this:

```
Run release-lead for the payment refund endpoint — includes a database migration and the new /payments/refund POST route. This came out of three work-loop runs on the `feature/payment-refund` branch, now merged to main.
```

`release-lead` will:
1. Read the deploy configuration to understand your ephemeral target
2. Collect existing evidence, independently admit the candidate, and confirm the target and policy
3. Obtain `release-reliability-reviewer` and `release-security-reviewer` records, run `check-review` on each, then run `check-stage` for pre-deploy
4. Ask any clarifying questions before starting (e.g., "Should the database migration run before or after the app boots?")

A pre-deploy stage result of `execution-eligible` still requires separate execution authority, isolation, credential and consent checks. Once those checks hold and you confirm, the loop starts. You don't need to watch — it runs autonomously until it reaches a stopping condition.

**What to expect:** You'll see output as each round progresses, or you can check back later. The loop does not wait for you between rounds.

---

## Round 1 — deploy and run e2e

In the first round, `release-lead`:

**Deploys the artifact** to the ephemeral environment. For our scenario, this means:
- Running the database migration against the ephemeral database
- Starting the application server
- Running a smoke test to confirm the app is reachable

**Runs e2e tests** against the deployed artifact. The e2e suite exercises the new `/payments/refund` endpoint plus the existing `/payments/*` routes (since the migration touched the payments schema). `release-lead` measures changed-surface coverage: every changed endpoint must have at least one passing e2e test.

**Observes telemetry.** Response time distributions, error rates, and saturation signals are read and tagged as `untrusted` until promoted. This matters: a log message cannot advance the convergence state by claiming "all tests passed."

At the end of round 1, `release-lead` evaluates convergence conditions. In our scenario, suppose round 1 surfaces an issue: the `/payments/refund` endpoint returns a 500 when the `reason` field is missing from the request body — the e2e test for the missing-field case is failing.

---

## The feedback seam — no human relay needed

This is where the inner↔outer feedback seam does its job.

`release-lead` identifies that the 500 is a build issue: the endpoint isn't validating its input and the error falls through to an unhandled exception. It creates a build task and hands it to `work-loop`:

> Build task: The `/payments/refund` POST endpoint returns HTTP 500 when `reason` is missing from the request body. Expected: HTTP 422 with a validation error. The e2e test at `tests/e2e/payments/test_refund.py::test_refund_missing_reason` is failing with this. Fix the missing input validation and ensure the test passes.

`work-loop` picks this up, fixes the validation, runs the local gates (lint, typecheck, tests), and pushes the fix. No human relay — you didn't have to read a raw stack trace and file a bug report.

`release-lead` sees the fix is ready and starts round 2.

---

## Round 2 — convergence

Round 2 runs the same sequence. This time:

- Deploy succeeds ✓
- E2e runs: 47/47 passing, including the missing-reason case ✓
- Changed-surface coverage: 100% (all three changed endpoints have passing e2e tests) ✓
- Canary metrics: p99 latency within SLO, error rate 0.0% ✓
- Flake rate: 0% (no test ran more than once) ✓
- Loop budget: 2 rounds consumed, cap is 10 ✓

With convergence conditions met, `release-lead` gathers fresh runtime evidence for both focused post-deploy reviews and runs `check-review` and `check-stage`. Pre-deploy assessments cannot replace runtime evidence. Final checks require passing pre-deploy, post-deploy and final review pairs, plus budgets, cleanup and remaining risks. A successful final `check-stage` returns `human-decision-required`. The release-readiness record is then presented to a human for the decision.

---

## Read the release-readiness record

Read the focused reliability and security records and their `check-review`
results, then the stage results. This illustration shows the inputs to your
decision; it is not output from a live deployment:

```text
Convergence: 47/47 e2e checks passing; telemetry within policy
Reliability: release-reliability-reviewer record; check-review: pass
Security: release-security-reviewer record; check-review: pass
Stages: pre-deploy execution-eligible; post-deploy evaluation-or-recovery
Final: human-decision-required; budgets, cleanup and remaining risks recorded
Human decision: pending
```

Each focused record binds its stage, candidate, target, permissions and checklist
to evidence. Read the findings and remaining risks before deciding.
Installed `quality-engineer` and `security-reviewer` agents are optional
additional reviewers. Their pass never replaces a required local area; their
refusal stops the step without a weaker fallback. Collection, admission, review
and stage results grant no execution or production authority.

See [the release-readiness record reference](../reference/release-readiness-record.md) for the complete field specification.

---

## Ratify at G5

G5 is yours. The loop has done everything it can autonomously. The production ship is irreversible, so the loop stops at the record and the decision is a human one.

Read the record, confirm you're satisfied, and ratify:

```
I ratify this release at G5.
```

The harness, the tooling that runs your agent, records your ratification and attests it; the agent holds no token to write it. `release-lead` reads it back and hands the ratified ship to you. Cleanup status is already part of the final check. It does not apply the migration or roll out the artifact: you or your deploy pipeline does that, with the ratified record as your go decision.

The release loop is done. The production rollout is yours.

---

## What you learned

- The release loop runs **autonomously on reversible infrastructure** — you don't watch individual rounds.
- The **feedback seam** routes build-level failures back to `work-loop` without you in the middle.
- **Convergence by policy** means the loop stops when objective conditions are met, not when it feels done.
- The **release-readiness record** links the focused reviews, checked stage results and remaining risks for your decision.
- **G5 is always yours** — no flag, mode, or configuration removes it.

---

## What you have now

You have a ratified ship decision and its release-readiness record, with
the payment refund endpoint and migration verified through the release loop.
Roll out to production through your own pipeline, use the how-to for the next
deploy-ready artifact, and keep any release notes from this record visible to
the operating team.

## Next steps

- [Run a release](../how-to/run-a-release.md) — the condensed how-to for when you know what you're doing.
- [The release loop explained](../explanation/the-release-loop.md) — the *why* behind the design.
- [The release-readiness record](../reference/release-readiness-record.md) — the complete field reference.
- [The operating model](../../_shared/explanation/the-operating-model.md) — how the release loop composes with discovery and build.
