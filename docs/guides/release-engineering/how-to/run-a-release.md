# Run a release

This guide walks through running a release from a deploy-ready artifact to a ratified prod ship. It assumes:

- `core` is installed in the repo
- `release-engineering` is installed in the repo
- The inner loop (`work-loop`) has already run and its output is a deploy-ready artifact
- You have a configured ephemeral deploy target (see below)

---

## Before you start

**Check your ephemeral deploy target is configured.** `release-lead` looks for deploy, smoke-test, and teardown artifacts that your platform tooling provides. Run `release-lead` and ask it to show its current deploy configuration — it will either confirm the target is wired or name exactly what's missing.

**Check your convergence policy.** The defaults (2% flake threshold, SLO-based canary gate, 100% changed-surface e2e coverage) work for most teams. If your app has specific SLO targets, configure them before the first run so the record reflects real thresholds, not defaults.

**Confirm `core` is at the same repo scope.** Run `agentbundle list-installed` and verify `core` appears as a repo-scope install. `release-engineering` hard-depends on `core` and will surface an error if it can't find `core`'s reviewer agents.

---

## Run the release loop

Trigger `release-lead` with a description of what you're releasing:

```
Run release-lead for the v2.3.0 deployment — the payment service refactor from the last three work-loop runs.
```

`release-lead` takes it from there. You do not need to monitor individual rounds — the loop runs autonomously until it reaches a stopping condition.

**What `release-lead` does:**

1. **Deploy** — deploys the artifact to the configured ephemeral environment.
2. **E2E** — runs the e2e suite against the deployed artifact. Measures changed-surface coverage.
3. **Observe** — reads telemetry, canary metrics, and logs. Tags all signals `untrusted` until promoted.
4. **Evaluate** — checks all convergence conditions: SLOs, e2e coverage, flake rate, error budget.
5. **If not converged:**
   - If the failure is a build issue, creates a build task for `work-loop` and waits for a fix, then redeploys.
   - If the failure is an infra or configuration issue, surfaces it to you with a specific question.
6. **If converged:** surfaces the release-readiness record and waits at G5.

---

## Review the release-readiness record

When convergence is reached, `release-lead` surfaces a **release-readiness record** — a structured assessment of the release's health. Read it before ratifying G5.

The record includes:
- **Convergence result** — how many rounds it took, which conditions were met, flake rate
- **Operational verdict** — `PASS`, `PASS-WITH-NOTES`, or `FAIL` from `quality-engineer` in operational mode
- **Security verdict** — `PASS`, `PASS-WITH-NOTES`, or `FAIL` from `security-reviewer` on the deployment config
- **Budget status** — rounds consumed vs. cap, cost consumed vs. threshold

A `PASS-WITH-NOTES` verdict means convergence was reached but the reviewer noted observations worth tracking. These do not block the release — they're surfaced for awareness. A `FAIL` verdict blocks the release: the loop has not converged cleanly and G5 is not available until the failure is addressed.

See [the release-readiness record reference](../reference/release-readiness-record.md) for the full field list and how to interpret each verdict.

---

## Ratify at G5

G5 is the prod-ship consent gate. It is always a human decision — the loop never auto-advances past it. You ratify by telling `release-lead`:

```
G5 ratified. Ship to production.
```

`release-lead` records your ratification (harness-attested — it cannot be forged) and proceeds with the prod ship sequence as configured by your platform tooling.

If you decide not to ship:

```
G5 declined. Hold the release — [reason].
```

The ratification record captures your decision and reason. The ephemeral environment is torn down. The artifact remains available to re-enter the release loop when you're ready to try again.

---

## Handling non-convergence

If the loop hits the round cap or cost budget before converging:

`release-lead` will surface:
- The current state of each convergence condition
- How many rounds were consumed
- What failed in the last round
- A recommendation for the most likely path to convergence

Your options:
- Fix the build issue and re-enter the loop
- Adjust the convergence policy (e.g., a flake threshold that's too strict for a known-flaky test)
- Investigate an infrastructure issue with your platform team
- Decide not to release this version

---

## Configuring an ephemeral deploy target

If `release-lead` surfaces a gap at startup — "I would look for a deploy artifact at X, but I don't see one" — you need to wire your platform tooling. The exact steps depend on your stack:

- **Kubernetes:** configure the `release-loop.deploy-target` to point to a namespace-provisioning script and a manifest apply step.
- **Cloud preview environments:** configure the deploy target to call your platform's preview-create API and output the preview URL for e2e targeting.
- **Docker Compose:** configure the deploy target to run `docker compose up -d` against a compose file scoped to the test environment.

When a platform pack is installed that covers your stack, wiring is automatic. Ask `release-lead` what platform packs are available for your stack, or check the catalogue.
