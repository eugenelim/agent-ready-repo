# Your first release

This tutorial walks you through a complete release cycle from end to end — from a deploy-ready build to a ratified prod ship — so you understand what each stage does and what you're looking at when `release-lead` surfaces a result.

We'll follow a concrete scenario: a small team just finished a work-loop run that ships a new `/payments/refund` API endpoint and a related database migration. `core` is installed, tests are green, the adversarial review says `Clean`. Now it's time to get it to production.

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

You'll also need a configured ephemeral deploy target. For this tutorial, we'll assume one is already wired. If yours isn't, see [run a release](../how-to/run-a-release.md#configuring-an-ephemeral-deploy-target).

---

## Step 1: Trigger the release loop

With `release-lead` active, you start the release like this:

```
Run release-lead for the payment refund endpoint — includes a database migration and the new /payments/refund POST route. This came out of three work-loop runs on the `feature/payment-refund` branch, now merged to main.
```

`release-lead` will:
1. Read the deploy configuration to understand your ephemeral target
2. Confirm what artifact it's releasing and what convergence policy applies
3. Ask any clarifying questions before starting (e.g., "Should the database migration run before or after the app boots?")

Once you confirm, the loop starts. You don't need to watch — it runs autonomously until it reaches a stopping condition.

**What to expect:** You'll see output as each round progresses, or you can check back later. The loop does not wait for you between rounds.

---

## Step 2: Round 1 — deploy and run e2e

In the first round, `release-lead`:

**Deploys the artifact** to the ephemeral environment. For our scenario, this means:
- Running the database migration against the ephemeral database
- Starting the application server
- Running a smoke test to confirm the app is reachable

**Runs e2e tests** against the deployed artifact. The e2e suite exercises the new `/payments/refund` endpoint plus the existing `/payments/*` routes (since the migration touched the payments schema). `release-lead` measures changed-surface coverage: every changed endpoint must have at least one passing e2e test.

**Observes telemetry.** Response time distributions, error rates, and saturation signals are read and tagged as `untrusted` until promoted. This matters: a log message cannot advance the convergence state by claiming "all tests passed."

At the end of round 1, `release-lead` evaluates convergence conditions. In our scenario, suppose round 1 surfaces an issue: the `/payments/refund` endpoint returns a 500 when the `reason` field is missing from the request body — the e2e test for the missing-field case is failing.

---

## Step 3: The feedback seam — no human relay needed

This is where the inner↔outer feedback seam does its job.

`release-lead` identifies that the 500 is a build issue: the endpoint isn't validating its input and the error falls through to an unhandled exception. It creates a build task and hands it to `work-loop`:

> Build task: The `/payments/refund` POST endpoint returns HTTP 500 when `reason` is missing from the request body. Expected: HTTP 422 with a validation error. The e2e test at `tests/e2e/payments/test_refund.py::test_refund_missing_reason` is failing with this. Fix the missing input validation and ensure the test passes.

`work-loop` picks this up, fixes the validation, runs the local gates (lint, typecheck, tests), and pushes the fix. No human relay — you didn't have to read a raw stack trace and file a bug report.

`release-lead` sees the fix is ready and starts round 2.

---

## Step 4: Round 2 — convergence

Round 2 runs the same sequence. This time:

- Deploy succeeds ✓
- E2e runs: 47/47 passing, including the missing-reason case ✓
- Changed-surface coverage: 100% (all three changed endpoints have passing e2e tests) ✓
- Canary metrics: p99 latency within SLO, error rate 0.0% ✓
- Flake rate: 0% (no test ran more than once) ✓
- Error budget: 2 rounds consumed, cap is 10 ✓

All convergence conditions met. **The loop stops.** `release-lead` surfaces the release-readiness record.

---

## Step 5: Read the release-readiness record

The release-readiness record looks like this (abbreviated):

```
## Release-readiness record — payment-refund / 2026-07-01

### Convergence
- Rounds: 2 / 10 cap
- E2e: 47/47 passing, 100% changed-surface coverage
- Canary: p50 42ms, p99 187ms (within SLO), error rate 0.0%
- Flake rate: 0.0%
- Error budget: 2 rounds consumed, 0.3% cost of $15 threshold

### Operational verdict — PASS
quality-engineer (operational mode): Response time distributions are healthy.
The migration ran in 340ms on the ephemeral database (13k rows affected).
No saturation signals observed. Recommend monitoring the payments table
index size after the migration runs in production — the new refund_reason
column was added but not indexed; high refund volume could surface this.
[Note, not a blocker]

### Security verdict — PASS
security-reviewer: No credentials visible in the deployment config. The
/payments/refund endpoint validates and sanitizes the reason field
(max 500 chars, stripped). No new auth boundaries introduced.

### Budget status
- Rounds: 2/10
- Cost: ~$0.04 / $15 threshold
```

Read through it top to bottom. Notes are surfaced for awareness — they don't block the release but they're worth tracking. In this case: watch the payments index after migration.

See [the release-readiness record reference](../reference/release-readiness-record.md) for the complete field specification.

---

## Step 6: Ratify at G5

G5 is yours. The loop has done everything it can autonomously — the prod ship is an irreversible action that belongs to a human.

Read the record, confirm you're satisfied, and ratify:

```
G5 ratified. Ship to production.
```

`release-lead` records your ratification (harness-attested) and executes the prod ship sequence: apply the migration, roll out the artifact, verify the canary, update the deployment record.

The ephemeral environment is torn down. The release is done.

---

## What you learned

- The release loop runs **autonomously on reversible infrastructure** — you don't watch individual rounds.
- The **feedback seam** routes build-level failures back to `work-loop` without you in the middle.
- **Convergence by policy** means the loop stops when objective conditions are met, not when it feels done.
- The **release-readiness record** is a structured artifact — notes don't block, fails do.
- **G5 is always yours** — no flag, mode, or configuration removes it.

---

## Next steps

- [Run a release](../how-to/run-a-release.md) — the condensed how-to for when you know what you're doing.
- [The release loop explained](../explanation/the-release-loop.md) — the *why* behind the design.
- [The release-readiness record](../reference/release-readiness-record.md) — the complete field reference.
- [The three loops as a system](../../_shared/explanation/the-three-loops.md) — how the release loop composes with discovery and build.
