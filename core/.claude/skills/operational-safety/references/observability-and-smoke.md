# observability-and-smoke — active end-to-end probe, log access, health, verify-status

> **Loaded when:** the change deploys a service, site, or endpoint a user
> reaches — anything where "created" does not yet mean "works" and the deploy
> needs an active probe plus the telemetry to debug a failed one.
> **Grounded in:** F2.2 ("created" ≠ "works"; smoke / health checks are
> mandatory before promotion); taxonomy follow-up — AWS Well-Architected
> Operational Excellence (understand operational health), Google SRE monitoring
> as a first-class practice.
> **Delegation legend:** `tool` = scanner / CI-gate-owned · `hybrid` = gate
> surfaces the signal, you judge the fix · `reason` = reviewer-only judgment.

A provisioned resource is not a working one. This module is the operational
extension of the work-loop's visual/manual-QA doctrine ("exercise the real
built artifact end-to-end") to a deployed system — and the observability that
lets the agent **debug a failed smoke itself** rather than relay errors to a
human.

## Implementation checks

- `reason` **Active end-to-end smoke, not a status check.** The verification is
  a multi-hop probe: seed test / mock users → load the **real** CDN / site URL
  → assert it actually renders → on failure, pull access / error logs and debug
  → tear down. A single "stack status: CREATE_COMPLETE" is not a smoke test —
  flag a deploy whose only post-apply check is resource status.
- `reason` **A verify-status signal exists.** There is a defined signal that
  answers "did the deploy report healthy?" — a health endpoint, a post-apply
  runtime assertion — distinct from the provisioning tool's own exit code.
- `hybrid` **Access / error logs are reachable for debugging.** When the smoke
  fails, the logs needed to diagnose it (access logs, error logs, the
  application's own telemetry) are accessible to the agent driving the deploy —
  log-driven debugging is the loop, not a human relaying the error back.
- `reason` **Health / telemetry is designed in, not bolted on.** The service
  exposes the operational health signals (health endpoint, the key
  golden-signal metrics) the smoke and ongoing operation depend on. Missing
  observability is a reliability finding, not a nice-to-have.
- `reason` **Seed + teardown bracket the probe.** The smoke seeds the test data
  / mock users it needs and tears them (and any ephemeral resources) down after
  — so the probe is repeatable and leaves no residue (this meets
  `cost-and-teardown`).

## Symptom→layer log playbook (failure localization)

When a smoke or a live request fails, **localize before deep-reading** — the
field report shows a facade-emitted timeout chased dozens of times in the
*backend* log because no map said which layer emits which symptom. The method:

- `reason` **Enumerate the path's log groups up front.** Before debugging, list
  every log source along the request / deploy path (edge / CDN, proxy / facade,
  authorizer, handler, datastore) so you know where to look, not just where you
  looked last.
- `reason` **Match the symptom against a failure-signature → likely-cause
  catalog *first*.** A runbook-style match resolves many investigations before
  any deep log reading. Examples (illustrative, not exhaustive): `ROLLBACK_COMPLETE`
  → stack must be **recreated**, not updated (a convergence case, see
  [`state-and-idempotency`](state-and-idempotency.md)); a **cold-start 504** →
  **retry / poll**, not a code bug; **conditional-write contention** → it's
  *contention*, expected under concurrency, not an error to "fix."
- `reason` **Map the failing status to the *emitting* layer.** **504 / timeout
  → proxy / facade** (the front door gave up, not necessarily the backend);
  **403 → authorizer / IAM** (the call was rejected before logic ran);
  **500 → handler** (logic failed). Read the layer that *emits* the symptom
  first, not the layer you assume owns the logic.
- `hybrid` **Bisect the chain.** When the emitting layer isn't obvious, halve
  the request path — confirm the call reaches the midpoint healthy, then narrow
  to the failing half — rather than scanning every log linearly.
- `reason` **Carry a correlation id.** A request / deploy carries an id that
  threads every layer's logs, so a single failure can be followed across the
  chain instead of guessed at per-layer.

## Established-pattern bypass

Resolve the repo's sanctioned smoke / observability harness — the end-to-end
probe script, the health-endpoint convention, the log-access path the deploy
pipeline already wires — and flag a deploy that declares success on
provisioning status alone, with no active probe and no reachable logs.

*Illustrative only (never normative):* a post-apply HTTP assertion against the
live URL plus structured access/error logs, or a deploy-validate-undeploy probe
harness, exhibit this shape — but the check is the *property* (active
end-to-end probe + reachable telemetry), not any one tool.
