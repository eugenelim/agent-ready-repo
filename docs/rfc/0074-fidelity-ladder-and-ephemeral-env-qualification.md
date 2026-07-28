# RFC-0074: Inner-loop fidelity ladder and outer-loop ephemeral environment qualification

<!-- Written for a cold reader who has not read the related RFCs. Coined terms
are glossed on first use inline. -->

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-27
- **Date closed:** 2026-07-27
- **Decision weight:** standard <!-- Adds doctrine and a new reference module;
  no adopter-facing interfaces are frozen. The isolation floor for the
  "reversible" label is the most load-bearing claim — it constrains what
  counts as an autonomous-zone action. -->
- **Related:**
  - [RFC-0049](0049-the-release-loop-and-company-os.md) (release-loop parent RFC —
    **Accepted 2026-06-30**; Decision 3 explicitly defers the fidelity-ladder /
    local-infra-equivalents to build packs as "a separate effort"; the outer loop's
    isolation requirements are in AC3/AC10(h))
  - [RFC-0072](0072-release-loop-deploy-doctrine.md) (sibling — G4 artifact format and
    progressive delivery; **Accepted 2026-07-27**; the outer loop this RFC qualifies
    ephemeral environments for)
  - [RFC-0073](0073-slo-authoring-and-error-budget.md) (sibling — SLO-authoring;
    **Accepted 2026-07-27**)
  - [`docs/specs/release-loop/spec.md`](../specs/release-loop/spec.md) (AC3 / AC10(h)
    — the "reversible" label conditioned on isolation; this RFC fills in the
    qualification criteria those ACs require)
  - `packs/core/.apm/skills/operational-safety/references/environment-isolation.md`
    (the existing REVIEW module on isolation; this RFC adds a companion
    EXECUTE/QUALIFY module to the same directory)
  - `packs/core/.apm/skills/work-loop/SKILL.md` (the inner loop; gains a
    fidelity-ladder section per D3)

---

## Reviewer brief

- **Decision:** Whether to (a) adopt a seven-level inner-loop fidelity ladder specifying
  what local-infra-equivalents each level provides, (b) specify the minimum outer-loop
  ephemeral environment qualification level required for the "reversible" label to hold
  under the minimum-regret carve, (c) home the ladder guidance in a new
  `fidelity-ladder` EXECUTE/QUALIFY reference module added to `operational-safety`
  (alongside the existing `environment-isolation` REVIEW module), and (d) surface that
  home in both the `work-loop` and `release-loop` skills as doctrine cross-references.
- **Recommended outcome:** Accept D1–D5.
- **Change if accepted:**
  - A new **`fidelity-ladder.md`** reference module lands in
    `packs/core/.apm/skills/operational-safety/references/` (D1 / D2 / D4). It is an
    EXECUTE/QUALIFY module (parallel to `cloud-implementation-craft`) — constructive
    guidance for what to build, not a review checklist; the existing
    `environment-isolation` module remains the REVIEW checklist.
  - The **`work-loop` skill** gains a fidelity-ladder section: a seven-level ladder with
    expected local-infra-equivalent coverage and a "push up the ladder" heuristic (D3).
  - The **`release-loop` skill** gains an ephemeral environment qualification section:
    the minimum isolation level, the qualification test, and the consequence of falling
    below it (consent-gate crossing) (D2 / D5).
  - `docs/specs/release-loop/spec.md` AC3 and AC10(h) receive a cross-reference note
    to this RFC — no AC text changes.
  - `packs/core/pack.toml` + `.claude-plugin/plugin.json` — patch version bump.
  - `docs/product/changelog.md` — `[Unreleased]` entry.
- **Affected surfaces:**
  - New: `packs/core/.apm/skills/operational-safety/references/fidelity-ladder.md`
  - `packs/core/.apm/skills/work-loop/SKILL.md` — new fidelity-ladder section
  - `packs/release-engineering/.apm/skills/release-loop/SKILL.md` — new ephemeral
    environment qualification section
  - `docs/specs/release-loop/spec.md` — cross-reference notes on AC3 / AC10(h)
  - `packs/core/pack.toml` + `.claude-plugin/plugin.json` — patch version bump
  - `docs/product/changelog.md` — `[Unreleased]` entry
- **Stakes:** Moderate. The "minimum qualification level for the reversible label" claim
  in D2 constrains adopter behavior — environments that don't meet the floor are consent
  gates, not autonomous-zone actions. This is correct behavior but must be stated clearly
  so adopters understand the autonomy envelope.
- **Review focus:** All decisions resolved in authoring session (D1–D5). D2 is the
  most load-bearing — confirm the isolation floor is correctly drawn.
- **Not in scope:** Building any local infra tooling or automation (the ladder is
  doctrine, not a runtime). Specifying Testcontainers, LocalStack, or Docker Compose
  configuration in detail (adopter-toolchain config). The `iac-terraform` pack's own
  workspace isolation (a Terraform concern, not a fidelity-ladder concern). The
  operate/incident loop.

---

## The ask

**Recommendation:** Add a `fidelity-ladder` EXECUTE/QUALIFY reference module to
`operational-safety` (in `core`) and cross-reference it from both the `work-loop` and
`release-loop` skills, closing the gap RFC-0049 D3 deferred.

**Why now (SCQA — Situation / Complication / Question / Answer):**

*Situation:* The operating model has an inner loop (`work-loop`, local build) and an outer
loop (`release-loop`, ephemeral deploy + e2e). The outer loop's autonomy rests on a single
claim: the ephemeral environment is "reversible" — network- and data-isolated from prod,
holds no real user data, cannot reach prod state (AC3 / AC10(h)). The inner loop's
autonomy rests on a parallel claim: the local build is "self-sufficient" — it runs and
verifies locally without the real deployed infra, using local-infra-equivalents.

*Complication:* Neither claim has a specification of how to achieve it:

- **Inner-loop gap (RFC-0049 D3 unfulfilled).** The inner loop's local-infra-equivalents
  are the build pack's obligation (RFC-0049 D3: "fakes → contract tests → Testcontainers →
  LocalStack → docker-compose"). But no build pack has shipped a fidelity-ladder reference.
  An implementing `work-loop` agent must re-derive the ladder on every run — deciding
  whether to use a fake, a container, or an emulator without principled guidance.
- **Outer-loop gap (AC3 / AC10(h) underspecified).** The release-loop spec says an
  environment that "cannot be proven isolated is itself a consent-gate crossing." It does
  not say how to prove isolation. An implementing `release-lead` agent cannot classify a
  k8s namespace, a LocalStack instance, or a dedicated cloud account as "proven isolated"
  or "consent-gate" without criteria.

*Question:* Can the ecosystem's settled fidelity-ladder patterns be expressed as
harness-neutral doctrine that specifies the qualification criteria without prescribing
a toolchain?

*Answer:* Yes. The ecosystem has converged on a stable seven-level ladder from in-memory
fakes through dedicated cloud sandbox accounts. Each level has deterministic isolation
properties against the three qualifying dimensions (prod reachability, data isolation,
inter-environment contamination). The qualification criteria map directly onto the
outer loop's three "proven isolated" conditions, producing a clear floor: L5 (dedicated
cloud account or equivalent — a k8s namespace or vCluster must additionally pass a
three-dimension policy audit) is the minimum for the outer loop's "reversible" label.

---

## Decisions requested

| ID | Question | Recommendation | Rationale | Decide by | Reviewer action |
|----|----------|----------------|-----------|-----------|-----------------|
| D1 | Inner-loop fidelity ladder: (A) adopt a seven-level ladder (L0 in-memory → L1 contract → L2 docker-compose → L3 container-emulated → L4 k8s-namespace → L4+ vCluster → L5 cloud sandbox → L6 staging) with defined local-infra-equivalent coverage and provability classification per level, or (B) leave the ladder entirely to adopter judgment? | **A — seven-level ladder** | RFC-0049 D3 adopted the fidelity-ladder obligation; the levels are the ecosystem's settled vocabulary (Testcontainers, LocalStack, Docker Compose, k8s namespace-per-PR documentation all use this progression). Option B repeats the gap: every adopter re-derives the ladder independently. | This review | Confirmed |
| D2 | Outer-loop qualification floor: (A) specify L5 (dedicated cloud account / project, or k8s namespace/vCluster that passes a policy audit) as the minimum for the carve's "reversible" label, with a three-dimension qualification test and a provability classification (self-evident / requires-audit / programmatically-auditable), or (B) leave qualification to adopter discretion? | **A — L5 floor with a three-dimension qualification test** | The minimum-regret carve's "reversible" claim is load-bearing (it is what justifies autonomous outer-loop operation). Without a floor, an adopter could run the outer loop against a k8s namespace with no network policy (L2-equivalent isolation) and treat it as "reversible." The consequence of miscategorisation is incorrect autonomy — the loop acts as if the env is expendable when prod reachability remains. L4 (namespace) qualifies conditionally — only after a policy audit — which is the "requires-audit" provability class. | This review | Confirmed |
| D3 | Inner-loop skill home: (A) add a fidelity-ladder section to the `work-loop` skill cross-referencing the new `fidelity-ladder` reference module, or (B) leave `work-loop` unchanged and wait for a build pack to carry it? | **A — `work-loop` skill gains the ladder section** | RFC-0049 D3 named the inner loop's fidelity ladder as a build pack obligation, but no build pack has shipped. Waiting further leaves the gap open indefinitely. Adding a section to `work-loop` is the inner-loop skill — it owns local build doctrine. When a build pack ships a deeper reference, it extends rather than replaces this section. | This review | Confirmed |
| D4 | Reference module home: (A) a new `fidelity-ladder.md` EXECUTE/QUALIFY module in `operational-safety/references/` (alongside `environment-isolation.md`), or (B) a section inside the existing `environment-isolation.md` module, or (C) a new standalone skill? | **A — new `fidelity-ladder.md` in `operational-safety/references/`** | Option B conflates REVIEW (does this env meet the bar?) with EXECUTE (how to build an env that meets the bar) — the existing `environment-isolation` module is a REVIEW checklist and should remain so. Option C is premature (one reference file doesn't warrant a skill). A new module in the same directory follows `cloud-implementation-craft`'s EXECUTE precedent in `operational-safety`. | This review | Confirmed |
| D5 | Outer-loop skill cross-reference: (A) the `release-loop` skill gains an "Ephemeral environment qualification" section with the L5 floor (and the L4/L4+ conditional path via policy audit), the three qualification dimensions, the provability classification, the agent-applicable test, and the consequence of falling below the floor, or (B) leave the consequence implicit in AC3/AC10(h)? | **A — explicit qualification section in `release-loop`** | AC3/AC10(h) state the consequence ("consent-gate crossing") but not the test. An implementing `release-lead` agent needs the test — a concrete, apply-once qualification step — not a prose reminder. The section is harness-neutral: the test is expressed as three boolean properties and a provability classification, not a tool invocation. | This review | Confirmed |

*Default if no objection: adopt D1–D5 and proceed to implementation.*

---

## Problem and goals

### The inner-loop gap: RFC-0049 D3 has no implementing artifact

RFC-0049 D3 adopted "local-infra-equivalents a build-loop obligation — the fidelity
ladder (fakes → contract tests → Testcontainers → LocalStack → docker-compose)." The
decision was confirmed and the implementing spec was not required because it was a
build-pack obligation, not a `core` obligation. But the `iac-terraform` pack — the
only shipped build-adjacent pack — does not carry a fidelity-ladder reference. The
`work-loop` skill has no ladder section. An implementing `work-loop` agent reads
"push the inner loop as high up the fidelity ladder as a sub-5-min budget tolerates"
(RFC-0049 Proposal) without knowing what the ladder is.

### The outer-loop gap: the qualification test is absent

`release-loop` AC3 states: "A deploy target that cannot be proven isolated is itself a
consent-gate crossing (it is no longer reversible)." `release-loop` AC10(h) states: "The
autonomous-zone isolation conditions (no prod reachability, no real data, isolated from
other ephemeral envs) are the security floor under the 'reversible' label, not just a
reviewer lens."

Both ACs state the consequence without specifying the test. An implementing `release-lead`
must determine at runtime whether a given environment satisfies the three isolation
conditions. Without a qualification checklist, this judgment is free-form and inconsistent
across adopters and agents.

### Goals

- Specify the seven-level inner-loop fidelity ladder with defined coverage per level.
- Specify the three qualification dimensions and the L5 floor for the outer loop.
- Home the ladder guidance in `operational-safety/references/fidelity-ladder.md`.
- Surface the ladder in `work-loop` and the qualification test in `release-loop`.

---

## Evidence

### The inner-loop fidelity ladder — ecosystem convergence

The ecosystem has converged on a layered vocabulary that appears consistently across
Testcontainers documentation, LocalStack documentation, Docker Compose usage patterns,
and the inner-dev-loop tools (Tilt, Skaffold, Telepresence). No single canonical document
(DORA, Google SRE, CNCF) publishes the full ladder; the most explicit practitioner
articulations are the NashTech ".NET Fidelity Ladder" series and Martinfowler's practical
test pyramid. The levels below are a harness-neutral synthesis.

**The inner/outer loop boundary** is the git push / PR-open event. Everything before it
(L0–L3) is inner-loop territory; everything after it (L4 and above, post-push CI-managed
ephemeral environments) is outer-loop territory. Tools like Tilt and Skaffold that sync
code live to a remote cluster straddle this boundary but are conventionally called
"inner-loop tools" because the developer retains interactive control.

| Level | Name | Technology examples | Coverage | Isolation provability |
|-------|------|--------------------|-----------|-----------------------|
| L0 | In-memory fake | Hand-rolled stubs, in-process fakes, sqlite-in-memory | Single-process; no network; no external API | **Self-evident** — process boundary |
| L1 | Contract / protocol test | Pact CDC, JSON Schema validation, gRPC reflection | Provider/consumer contract only; no running service; protocol boundary | **Self-evident** — no network stack |
| L2 | Compose-isolated | Docker Compose multi-service, devcontainer | Multi-service network; host filesystem; no cloud API emulation | **Self-evident** — Docker bridge prevents external routing |
| L3 | Container-emulated | Testcontainers (per-test container lifecycle) + LocalStack / Microcks / WireMock | Per-test isolation; cloud API emulation; SDK calls intercepted before leaving process | **Self-evident** — SDK endpoint override captures all cloud API calls |
| L4 | k8s namespace-isolated | Namespace-per-PR in a shared cluster with explicit NetworkPolicy + RBAC | Real Kubernetes primitives; shared control plane | **Requires policy audit** — no network policy = shared blast radius with other namespaces |
| L4+ | Virtual cluster | vCluster (Loft Labs), dedicated API server inside host cluster | Stronger than namespace; softer than dedicated cluster | **Requires audit** — host cluster egress policy must be verified |
| L5 | Cloud sandbox | Dedicated non-prod cloud account / project (AWS account-per-stage, GCP project-per-env); Terraform workspace with isolated state backend + no prod credential path | Real cloud APIs; real billing (throttled); separate IAM boundary; no prod credentials reachable | **Programmatically auditable** — SCP/org policies enforce the boundary; state backend isolation verifiable |
| L6 | Staging/pre-prod | Production-mirror environment; may carry anonymised production data | Near-prod fidelity; human-gated; not an autonomous-zone target | Human-supervised; never autonomous |

**Inner-loop budget heuristic:** Run as high up the ladder as a sub-5-minute local budget
tolerates. L0–L1: milliseconds (always in-loop floor). L2–L3: seconds to 2 minutes
(comfortable inner ceiling). L4–L4+ straddle the inner/outer boundary — they run in CI,
not locally. L5 and above are the outer loop's domain.

**LocalStack license note:** LocalStack ended its Community Edition for commercial use in
March 2024. Teams running LocalStack in a commercial context must use LocalStack Pro
(paid) or choose an OSS alternative (Moto, Localstack-OSS forks) with narrower API
coverage. The doctrine references LocalStack as a technology example, not a mandatory
tool; adopters choose their emulator. This fidelity-ladder reference is intentionally
harness-neutral.

**LocalStack / Testcontainers fidelity gaps (expected, not defects):** LocalStack emulates
AWS service APIs at the HTTP layer; behavioral fidelity gaps exist (particularly for
complex IAM conditions, cross-service event propagation timing, and managed service
internals). These gaps are why the outer loop exists — they surface what the inner loop
cannot catch.

### The outer-loop qualification test — three dimensions

The outer loop's "reversible" label requires all three isolation conditions to hold
simultaneously. Each maps to a concrete, testable boolean:

| Dimension | Condition | How to test |
|-----------|-----------|-------------|
| Prod reachability | No route from the ephemeral env to prod endpoints, prod databases, or prod identity stores | Network policy or security group audit confirms no ingress/egress to prod CIDR / prod account; credential scoping confirms the session cannot assume prod IAM roles |
| Data isolation | No real user data accessible from the ephemeral env | Data classification review confirms the env's database/storage contains only synthetic, anonymized, or purpose-generated data; no prod snapshot was restored here |
| Inter-env isolation | This ephemeral env cannot affect other running ephemeral envs or shared staging envs | Env resources (namespaces, accounts, VPCs, state backends) are unique to this cycle; no shared mutable state with other concurrent envs |

**L5 as the minimum floor for the outer loop:** An environment at L5 (dedicated cloud
account / project, or a k8s namespace with verifiable network policies, RBAC boundary,
and isolated state backend) satisfies all three dimensions if correctly configured. An
environment at L3 (container-emulated, LocalStack) is typically self-evidently isolated
for the inner loop but does **not** satisfy the outer-loop isolation claim for arbitrary
deploys — a LocalStack instance running in CI may share a Docker network with
prod-credential-bearing processes. An environment at L4 / L4+ (k8s namespace or vCluster)
requires explicit policy audit; the outcome of the audit determines whether it qualifies.

**The qualification test is boolean, not scored:** The outer loop does not score
environments against a fidelity rubric. It applies the three-dimension test at cycle start
as a precondition for entering the autonomous zone. A single `false` is a consent-gate
crossing — surface to human; do not proceed with autonomous deploy.

### The isolation provability classification

This classification drives the cost of the qualification step at cycle start:

- **Self-evident** (L0–L3): isolation is structural. The process boundary, Docker bridge,
  or SDK endpoint-override prevents external routing by construction. No policy audit
  needed — the qualification test passes trivially.
- **Requires policy audit** (L4 namespace, L4+ vCluster): isolation depends on network
  policies and RBAC that must be verified per deployment. The qualification test requires
  reading and confirming the policy configuration is present and correctly scoped.
- **Programmatically auditable** (L5 dedicated account/project): isolation is enforced by
  cloud org policies (SCPs, GCP Org Policy) and IAM boundaries that can be queried via API
  before each cycle. The qualification test is a policy API call, not a human review.

The outer loop's qualification step should apply the test appropriate to the
environment's provability class. A "requires policy audit" environment that hasn't been
audited in this cycle is not qualified — surface to human before proceeding.

---

## The fidelity-ladder specification (D1 elaboration)

This is the content that lands in `operational-safety/references/fidelity-ladder.md`.
Levels L0–L3 are inner-loop (pre-push); L4 and above are outer-loop (post-push, CI-managed).

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
Level: L4+ — Virtual cluster (vCluster) (requires policy audit)
Coverage:  own Kubernetes API server and control plane inside a host cluster
Isolation: requires audit (stronger than namespace; host cluster egress policy still
           applies; isolation claims are self-reported by vCluster project)
Gaps:      host cluster egress policy is a shared blast radius; limited independent
           security audit of isolation boundary in public literature
Use when:  teams who need stronger-than-namespace isolation without dedicated cluster cost
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
Gaps:      may share blast radius with prod-adjacent services; cross-env contamination risk
           if anonymisation is incomplete
Use when:  human-supervised regression, load, or soak testing only
Budget:    n/a (human-gated; not an outer-loop target)
```

---

## Drawbacks

- **L5 floor may be too high for small teams.** A dedicated cloud sandbox account is an
  IaC and billing overhead many small teams won't provision. Mitigated by naming k8s
  namespace isolation with verifiable network policies + RBAC as a conditionally-qualifying
  alternative (L4/L4+ via policy audit), lowering the bar for teams already running Kubernetes.
- **Qualification test is manual on first use.** An implementing agent applies the
  three-dimension test by reading network policy and IAM configuration — not by running a
  tool. On first cycle, this is a human-assisted step. Mitigated by making the test
  explicit (boolean, observable) rather than implicit (trust the adopter's assertion).
- **L3/L4 blur creates judgment calls.** As noted above, k8s namespace isolation spans
  the boundary. The qualification test resolves it, but there is one judgment call at the
  network-policy audit step. Mitigated by the three-dimension test being specific enough
  to guide the judgment deterministically in most cases.
- **Inner-loop ladder section in `work-loop` is not a substitute for a build pack.**
  Adding the ladder to `work-loop` closes the vocabulary gap but not the scaffolding
  gap — an implementing agent still must choose and configure the tools. When a build
  pack ships a fidelity-ladder reference with scaffold templates, that replaces this
  section. This RFC names that handoff explicitly.

## Follow-on artifacts

On acceptance:
- **New reference module:** `packs/core/.apm/skills/operational-safety/references/fidelity-ladder.md` — the seven-level ladder + the three-dimension qualification test per D1/D2.
- **`work-loop` skill update:** new fidelity-ladder section cross-referencing the module, per D3.
- **`release-loop` skill update:** new ephemeral environment qualification section (three-dimension test + L5 floor + consequence) per D5.
- **Spec update:** `docs/specs/release-loop/spec.md` — cross-reference notes on AC3 and AC10(h) pointing to this RFC.
- **Pack version bump:** `packs/core/pack.toml` + `.claude-plugin/plugin.json` — patch version bump (new reference module in `core`).
- **Changelog:** `docs/product/changelog.md` — `[Unreleased]` entry.
- **Future:** When a build pack ships a fidelity-ladder scaffold reference (Testcontainers config templates, LocalStack bootstrap, Docker Compose service templates), the `work-loop` ladder section should link to it — naming the handoff point explicitly so the build pack knows where to hook in.
