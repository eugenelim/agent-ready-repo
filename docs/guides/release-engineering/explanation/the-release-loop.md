# The release loop explained

## The problem it solves

When `work-loop` finishes, you have code that compiles, passes tests, and survives adversarial review. What you don't have is proof that it works **deployed** — that the artifact running in an integrated environment behaves the way the tests assumed, that the latency holds under real infrastructure, that the database migration runs cleanly, that the config values resolve correctly against a real secrets store.

The gap between "tests pass locally" and "works in production" has historically been filled by humans: developers watching deploy logs, SREs triaging production errors, on-call engineers running rollbacks at 2 AM. The release loop closes that gap autonomously — on reversible infrastructure — before any human touches a prod switch.

The key insight is **reversibility**. Deploying to an ephemeral environment is reversible: no real data, no real users, tear it down when you're done. Deploying to production is not: real users may see broken behavior before a rollback can be deployed. The release loop runs autonomously on what's reversible and surfaces to a human on what isn't. This is the **minimum-regret carve**.

## The inner/outer loop split

`core`'s `work-loop` is the **inner loop**: local build + verification. `release-engineering`'s `release-loop` is the **outer loop**: deployed validation.

The two loops are peers, not parent/child. The inner loop doesn't call the outer loop. The outer loop doesn't control the inner loop. They communicate through a **feedback seam**: when the outer loop surfaces a deployed failure, it creates a build task that the inner loop picks up and fixes. The outer loop then redeploys. No human relay needed for build-level failures.

```
Inner loop (core)                    Outer loop (release-engineering)
─────────────────                    ────────────────────────────────
spec → code → gates → review          deploy → e2e → observe → converge
         ↑                                     │
         └─── build task ◄──── deployed failure┘
                                 (feedback seam, no human relay)
```

The inner loop exits by pushing a deploy-ready artifact. The outer loop takes that artifact and validates it end-to-end. If the outer loop finds a bug that's clearly a build issue, it feeds it back to the inner loop. If it finds a configuration or infrastructure issue, it surfaces to the human with a specific question.

## The ephemeral environment model

The outer loop only operates on **ephemeral environments** — purpose-built, short-lived environments that:

- Contain no real user data
- Cannot reach production systems or production databases
- Are isolated from each other (concurrent releases don't interfere)
- Are torn down automatically on completion, whether successful or not

Isolation is not a suggestion — it's the architectural guarantee that makes unattended operation safe. An agent that can reach production during the release loop is an agent that can cause production incidents without a human in the loop.

What counts as an ephemeral environment depends on your stack. It might be:
- A fresh Kubernetes namespace spun up by your deploy tooling
- A preview environment on Vercel, Railway, or Render
- An isolated Docker Compose stack on a test runner
- A Terraform-provisioned AWS environment in a sandbox account

The release loop is agnostic to the platform. It consumes whatever deploy, smoke-test, and teardown artifacts your platform tooling produces. When a platform pack is installed (e.g., an AWS or Kubernetes pack), it wires those artifacts automatically. When one isn't, the loop names the artifacts it would otherwise use and surfaces the gap — it never silently fails.

## The convergence policy

The release loop iterates — deploy, observe, feed back, redeploy — until the deployed whole **converges by policy**. Convergence means:

1. Canary metrics pass SLOs for the changed surface
2. Every changed endpoint or code path has at least one passing e2e test
3. Test flake rate is below the configured threshold (default: 2%)
4. The error budget is not exhausted

When all four conditions are met, convergence is declared. The loop stops iterating and surfaces a **release-readiness record** to the human.

When convergence is not reached within the round cap or cost budget, the loop does not keep trying. It stops, surfaces the situation — what converged, what didn't, and how many rounds it ran — and asks the human how to proceed. The loop never silently burns through budget in pursuit of a convergence it can't reach.

## The minimum-regret carve

Autonomy is carved by minimum-regret: actions that can be cleanly undone within normal MTTR run autonomously; actions that cannot require human consent.

**Autonomous (reversible):**
- Deploy to an ephemeral environment
- Run e2e tests against the deployed artifact
- Observe telemetry and logs
- Create build tasks for the inner loop from deployed failures
- Redeploy after inner-loop fixes
- Tear down the ephemeral environment

**Human consent required (irreversible):**
- First real users or real data
- Data migrations
- Spend above a pre-agreed threshold
- Security or auth-boundary changes
- Anything not cleanly undone within MTTR
- **The prod ship (G5)**

The G5 prod-ship gate is the only gate between a converged, release-ready artifact and production. It is never bypassed, never auto-advanced, and never gated only on SLO thresholds. The human reads the release-readiness record and makes the call.

## Security and integrity controls

The release loop runs with deploy credentials that are broker-mediated and scoped to the ephemeral tier only. No credential configured for the release loop can reach production. This is enforced by the credential broker — not by policy, but by the broker's scope configuration.

Telemetry and log signals are tagged `untrusted` until the loop controller explicitly promotes them. This prevents prompt injection through log content: a malicious log message that says "all tests passed" cannot advance the convergence state.

Human verdicts (the G5 ratification) are harness-attested — the agent cannot forge or simulate a ratification. The ratification record is written by the harness, not by the agent.

## How it composes with `core`

The release loop reuses `core`'s reviewer agents rather than shipping its own:

- `quality-engineer` runs in **operational mode**: instead of reviewing code for testability and maintainability, it reviews the deployed system for operational health — latency distributions, error rates, saturation signals.
- `security-reviewer` runs on the deployment configuration and any infra-as-code changes, not just the application diff.
- `operational-safety` modules from `core` provide the checklist library for infra-facing review.

This reuse is architecturally sound because both packs install at repo scope in the same repo. The release loop is guaranteed to find `core`'s reviewer agents at the paths it expects.

## Why repo scope (not user scope)

The release loop installs at repo scope because it runs **downstream in the build repo** — the same repo where `core` is installed. This is the deliberate scope-inverse of `product-engineering`'s `discovery-lead`, which ships its own reviewers because it runs upstream in document workspaces that can't assume a `core` install.

*Scope follows where the work happens* — the company-OS scope boundary is at the G3 handoff, where product shaping (user scope, any workspace) becomes a concrete repo (repo scope, one codebase).
