# fidelity-ladder — inner-loop levels and outer-loop environment qualification

> **Loaded when:** the task needs a local-infra-equivalent (inner loop) or must
> qualify an ephemeral environment for autonomous outer-loop operation.
> **Module role:** EXECUTE/QUALIFY — constructive guidance for choosing and
> qualifying environments. The companion module
> [`environment-isolation.md`](environment-isolation.md) is the REVIEW checklist
> (auditing whether an existing environment meets the bar); this module specifies
> how to build or choose one that does. Load both when both questions are live.
> **Grounded in:** Testcontainers documentation, LocalStack documentation, Docker
> Compose usage patterns, inner-dev-loop tools (Tilt, Skaffold), Argo Rollouts,
> k8s NetworkPolicy and RBAC references, AWS multi-account-per-stage pattern
> (SCP/org-policy enforcement), vCluster (Loft Labs) documentation.

---

## The seven-level fidelity ladder

Levels L0–L3 are **inner-loop** (pre-push, developer-controlled). L4 and above
are **outer-loop** (post-push, CI-managed). The boundary is the git push / PR-open
event.

| Level | Name | Technology examples | Coverage | Isolation provability |
|-------|------|---------------------|----------|-----------------------|
| L0 | In-memory fake | Hand-rolled stubs, in-process fakes, sqlite-in-memory | Single-process; no network; no external API | **Self-evident** — process boundary |
| L1 | Contract / protocol test | Pact CDC, JSON Schema validation, gRPC reflection | Provider/consumer contract only; no running service | **Self-evident** — no network stack |
| L2 | Compose-isolated | Docker Compose multi-service, devcontainer | Multi-service network; host filesystem; no cloud API emulation | **Self-evident** — Docker bridge prevents external egress |
| L3 | Container-emulated | Testcontainers + LocalStack / Microcks / WireMock | Per-test isolation; cloud API emulation; SDK calls intercepted | **Self-evident** — SDK endpoint override captures all cloud API calls |
| L4 | k8s namespace-isolated | Namespace-per-PR on a shared cluster (NetworkPolicy + RBAC required) | Real Kubernetes primitives; shared control plane | **Requires policy audit** — no network policy = shared blast radius |
| L4+ | Virtual cluster | vCluster (Loft Labs) — dedicated API server inside host cluster | Stronger than namespace; softer than dedicated cluster | **Requires audit** — host cluster egress policy must be verified |
| L5 | Cloud sandbox | Dedicated non-prod cloud account / project + isolated state backend | Real cloud APIs; real IAM; real billing (throttled); no prod credential path | **Programmatically auditable** — SCP/org policies verifiable via API |
| L6 | Staging / pre-prod | Production-mirror; may carry anonymised prod data | Near-prod fidelity | **Human-supervised; never autonomous-zone** |

---

## Per-level descriptors

```
Level: L0 — In-memory fake
Coverage:  single-process logic only
Isolation: self-evident (process boundary — no network stack)
Gaps:      no persistence, no real API, no multi-service behavior
Use when:  testing a single function / adapter boundary in isolation
Budget:    < 1 s; always in-loop
```

```
Level: L1 — Contract / protocol test
Coverage:  provider–consumer protocol agreement (Pact CDC, gRPC reflection, JSON Schema)
Isolation: self-evident (no running service; no network calls made)
Gaps:      no behavioral fidelity beyond the protocol boundary
Use when:  verifying two components agree on the API shape without running both
Budget:    < 10 s; always in-loop
```

```
Level: L2 — Compose-isolated multi-service
Coverage:  multi-service network topology; realistic routing between services
Isolation: self-evident (Docker bridge prevents external egress by default)
Gaps:      cloud API calls fail or are stubbed; shared containers across tests unless
           explicit teardown
Use when:  testing multi-service interactions that don't require real cloud APIs
Budget:    < 60 s; inner-loop ceiling for most services
```

```
Level: L3 — Container-emulated (Testcontainers + LocalStack / Microcks / WireMock)
Coverage:  cloud API emulation (AWS S3, SQS, DynamoDB, etc.); per-test container lifecycle;
           SDK calls intercepted before leaving the process
Isolation: self-evident (SDK endpoint override captures all cloud API calls before they
           reach a real endpoint)
Gaps:      behavioral fidelity gaps (complex IAM conditions, cross-service event timing,
           managed service internals); LocalStack commercial license required for production
           use post-March 2024 (OSS alternatives: Moto, LocalStack-OSS forks, Microcks)
Use when:  inner-loop tests that need cloud API behavior without a real account
Budget:    30 s – 3 min; inner-loop ceiling for cloud-dependent services
Note:      L3 is the inner-loop ceiling; fidelity gaps here are expected and are exactly
           what the outer loop exists to catch
```

```
Level: L4 — k8s namespace-isolated (requires policy audit)
Coverage:  real Kubernetes primitives; per-PR namespace on a shared cluster
Isolation: requires policy audit (shared control plane; NetworkPolicy + RBAC must be
           present and verified per deployment — absent policies = L2-equivalent isolation)
Gaps:      shared control plane blast radius; host-cluster egress policy applies to all
           namespaces; not equivalent to account-level isolation
Use when:  teams already running Kubernetes that want per-PR ephemeral environments
           without dedicated cluster provisioning costs
Qualification: qualifies for the outer loop only after the three-dimension policy audit
               passes — "namespace isolation" without verified NetworkPolicy does not qualify
```

```
Level: L4+ — Virtual cluster / vCluster (requires policy audit)
Coverage:  own Kubernetes API server and control plane inside a host cluster
Isolation: requires audit (stronger than namespace; host cluster egress policy still
           applies; isolation claims are self-reported by vCluster project)
Gaps:      host cluster egress policy is a shared blast radius; limited independent
           security audit of isolation boundary in public literature
Use when:  teams who need stronger-than-namespace isolation without dedicated cluster cost
Qualification: same three-dimension audit required as L4; host cluster egress policy
               must be verified in addition to the virtual cluster's own isolation
```

```
Level: L5 — Cloud sandbox (the outer-loop qualification floor)
Coverage:  real cloud APIs; real IAM; real networking; real billing (throttled/capped)
Isolation: programmatically auditable (dedicated account/project boundary + isolated state
           backend + no prod credential reachable; SCP/org policies verifiable via API)
Gaps:      real billing cost; setup/teardown time (minutes); real data risk if
           misconfigured (data isolation is not free — it must be enforced)
Use when:  the outer release loop (autonomous zone); ephemeral environments
Budget:    minutes to hours; outer-loop territory; teardown on cycle end mandatory
           (see cost-and-teardown module)
Note:      The `iac-terraform` pack's generate-iac skill scaffolds the account/workspace
           boundary — the provisioning detail for this level lives there
Qualification: satisfies all three outer-loop isolation dimensions when:
               (a) the account/project has no VPC peering to prod,
               (b) all data is synthetic / purpose-generated,
               (c) state backends are isolated and not shared with other envs
```

```
Level: L6 — Staging / pre-prod
Coverage:  production-equivalent topology; may carry anonymised production data
Isolation: human-supervised; never autonomous-zone
Gaps:      may share blast radius with prod-adjacent services; cross-env contamination
           risk if anonymisation is incomplete
Use when:  human-supervised regression, load, or soak testing only
Budget:    n/a (human-gated; not an outer-loop target)
```

---

## Inner-loop budget heuristic

**Push up the ladder as high as a sub-5-minute local budget tolerates.**

- **L0–L1:** milliseconds — always in-loop; never skip these.
- **L2–L3:** seconds to 3 minutes — the inner-loop ceiling for most services.
- **L4 and above:** CI-managed; these are outer-loop territory, not local builds.

When a task's dependency cannot be represented at L0–L3 within budget, that is the signal
to defer the integration test to the outer loop (the CI-managed ephemeral environment)
rather than lowering the budget or cutting the test.

---

## Outer-loop qualification: the three-dimension test

The outer loop's "reversible" label requires all three isolation conditions to hold
simultaneously. Each maps to a concrete, testable boolean:

| Dimension | Condition | How to test |
|-----------|-----------|-------------|
| **Prod reachability** | No route from the ephemeral env to prod endpoints, prod databases, or prod identity stores | Network policy or security group audit confirms no ingress/egress to prod CIDR / prod account; credential scoping confirms the session cannot assume prod IAM roles |
| **Data isolation** | No real user data accessible from the ephemeral env | Data classification review confirms env storage contains only synthetic, anonymized, or purpose-generated data; no prod snapshot was restored here |
| **Inter-env isolation** | This ephemeral env cannot affect other running ephemeral or shared staging envs | Env resources (namespaces, accounts, VPCs, state backends) are unique to this cycle; no shared mutable state with other concurrent envs |

**The test is boolean, not scored.** A single `false` is a consent-gate crossing — surface
to human; do not proceed with autonomous deploy.

---

## Isolation provability classification

| Class | Levels | What this means | Cost at cycle start |
|-------|--------|-----------------|---------------------|
| **Self-evident** | L0–L3 | Isolation is structural — process boundary, Docker bridge, or SDK endpoint-override prevents external routing by construction | None — test passes trivially |
| **Requires policy audit** | L4, L4+ | Isolation depends on network policies and RBAC that must be verified per deployment | Read and confirm the policy config is present and correctly scoped before each cycle |
| **Programmatically auditable** | L5 | Isolation enforced by cloud org policies (SCPs, GCP Org Policy) and IAM boundaries queryable via API | Policy API call at cycle start; automation-friendly |

A "requires policy audit" environment that hasn't been audited this cycle is **not
qualified** — surface to human before proceeding autonomously.

---

## LocalStack licensing note

LocalStack ended its Community Edition for commercial use in March 2024. Teams running
LocalStack in a commercial context must use LocalStack Pro (paid) or choose an OSS
alternative (Moto, LocalStack-OSS forks, Microcks) with narrower API coverage. This
module references LocalStack as a technology example, not a mandatory tool; the doctrine
is intentionally harness-neutral. Choose the emulator that fits your license posture.

---

## Build-pack handoff

When a build pack ships a fidelity-ladder scaffold reference — Testcontainers configuration
templates, LocalStack bootstrap scripts, Docker Compose service templates — the
`work-loop` skill's ladder summary section should link to it. This module is the canonical
level-descriptor reference; the build pack's scaffold reference extends it with
tool-specific setup detail.
