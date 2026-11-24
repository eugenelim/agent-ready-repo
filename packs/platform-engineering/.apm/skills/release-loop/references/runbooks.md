# Release-loop runbooks

Operational procedures and defaults for the release loop. These are load-bearing
controls named by the skill body — read the section that applies to the phase you
are executing. Every floor stated here is a minimum; adopters may tighten, never
waive.

## Collection and admission before action

Follow the parent skill's collection, admission and focused review procedure
before any deploy phase. `prepare-release-handoff` gathers existing evidence;
`ready` still needs independent `admit` and `verify`. An incomplete collection
names gaps and next actions; never execute missing build, test or plan work
implicitly. The caller supplies the trusted policy. Candidates may come from
CI, a human or another workflow without core or a work-loop G4 event.

Dispatch `release-reliability-reviewer` and `release-security-reviewer`, each
with only its own role reference in this directory. Those references alone own
the checklists. Save the records, run `check-review`, then `check-stage` using
the parent skill's stage table. Installed core reviewers are optional additional
reviewers after the direct checks. Their pass never replaces a local area;
their refusal or failed check stops the step, with no weaker fallback.

## Stage and repair routing

The parent skill's stage table governs admission, pre-deploy, post-deploy,
recovery and final. A pre-deploy assessment cannot substitute for runtime
evidence. Post-deploy evidence must be strictly newer than every pre-deploy
evidence time and never cited pre-deploy. Same-stage, later-stage and self review
citations cannot serve as evidence. Changed artifact, target, permissions or
state assumptions require reassessment, even if the image digest is unchanged.
Final requires passing pre-deploy, post-deploy and final reliability and security
records, plus budgets, cleanup and remaining risks. Successful `check-stage`
returns `human-decision-required`; include the focused records and their
`check-review` results in the release-readiness record.
A commit-ready verdict is not release proof. No stage outcome grants execution
or production authority; isolation, credential and consent checks still apply.

For a failed deployed check, run the parent skill's `repair-handoff` command.
Route its bounded redacted output to the candidate's recorded `repair_owner`;
use a callable route only when recorded, otherwise human-handoff or pause.
Never silently skip a check when automation is absent. A replacement re-enters
collection, admission with `--replaces`, review and stage checks. Keep inherited
attempt limits and the cycle's cost budget. Refusals stop the affected step.

## Deploy ordering protocol

The `deploy_phases` field encodes the canonical deploy ordering as an ordered list
the outer loop executes phase-by-phase. The **four standard phases** are the
non-waivable ordering floor:

| Phase | Tool hint | Gate | `on_failure` |
|---|---|---|---|
| `infra-apply` | terraform / pulumi / cdk | auto | surface (IaC rollback is non-automatic — see Rollback) |
| `service-deploy` | argocd-sync / helm-upgrade / kubectl-apply | auto | rollback |
| `smoke` | \<test runner\> | auto | rollback |
| `canary` | \<traffic controller\> | auto (metric-gated) or manual | rollback |

The ordering is not arbitrary: services reference infra outputs (database URLs, IAM role
ARNs, VPC IDs) — `infra-apply` must precede `service-deploy`. Smoke gates the canary.
These are invariants of the deploy topology, not adopter preferences.

The `tool` field is a **hint** — the outer loop translates it to the actual orchestrator
at deploy time. Adopters may add phases before, between, or after the standard four; they
may not reorder the standard four relative to each other. Each phase's `depends_on` list
(optional) makes multi-component fan-out explicit.

## Canary analysis defaults

Progressive traffic shift is what turns the canary phase from a one-shot deploy into a
two-way door. The following are **conservative floors — not production baselines**.
Tighten per service class before going to prod.

**Traffic steps (default):** 5% → 25% → 50% → 100%

**Pause per step:** 2 min minimum; 5 min recommended (catches issues that manifest under
sustained load).

**Analysis thresholds by service class:**

| Metric | Default | Stateful / Payment | Interactive API |
|---|---|---|---|
| Success rate floor | ≥ 95% | ≥ 99% | ≥ 99% |
| Error rate ceiling | ≤ 5% | ≤ 1% | ≤ 1% |
| Latency p99 ceiling | ≤ 500 ms | ≤ 200 ms | ≤ 200 ms |

Thresholds derive from SLO targets where a `define-slo` document is present — tighten
to match the service's defined reliability objective.

**Failure limit:** 3 consecutive analysis failures per step → automatic ROLLBACK.

**Four canary outcomes:**

- **PROMOTE** — all metric checks pass for the full step duration; no failure-limit hit.
  Advance to the next traffic step automatically.
- **ROLLBACK** — failure limit (≥ 3 consecutive) reached, or a `critical` metric
  immediately breaches. Revert traffic to 0% canary. Trigger rollback procedure.
- **PAUSE-for-human** — metric score falls in the ambiguous band (75–95 Spinnaker-equivalent
  percentile), or the phase list contains an explicit `pause: {}` step. Resume only on
  human `approve` — this is a consent gate (control (a)).
- **HALT** — oscillation circuit-breaker: **N ≥ 3 consecutive promote↔rollback cycles**.
  Halt promotion entirely; write a stall record to the decision log; surface to human;
  count against the cost cap. A cheap flapping canary that stays under budget
  is still bounded by attempt count.

## Feature flag lifecycle

Feature flags are the mechanism that decouples **deploy** (code ships to servers) from
**release** (users see the feature). The deploy→release decoupling invariant:

> Code is merged to main behind a flag in `deployed-off` state. The flag advances to
> `enabled-pct` only **after smoke passes** — not at deploy time, at convergence time.
> Full rollout (100%) happens after canary promotion.

**Six lifecycle states (harness-neutral):**

| State | Meaning | Transition trigger |
|---|---|---|
| `created` | Flag defined in management system; code not yet deployed | Flag registered |
| `deployed-off` | Code deployed; flag evaluates to `false`/default; no user exposure | Code merged behind flag |
| `enabled-pct` | Flag enabled for N% of users (progressive rollout) | Smoke passed; canary begins |
| `full-rollout` | Flag enabled for 100% of users | Canary promoted |
| `deprecated` | Feature is live; flag no longer needed; code cleanup begun | Decision to remove |
| `removed` | Flag and all code references deleted | Code references confirmed gone |

**Four flag types with expected lifetimes:**

- **release** (progressive delivery): ≤ 90 days created → removed. The primary flag type
  for this loop.
- **experiment** (A/B / metrics-gated): ≤ 90 days. Cleaned up when the experiment
  concludes.
- **operational** (kill-switch / circuit-breaker): indefinite; must be explicitly tagged
  `permanent`. These are not release flags — they are always-on infrastructure controls.
- **permission** (user/role scoped): service-dependent lifetime; must be documented in
  the SLO document or a companion policy record.

OpenFeature provides the harness-neutral provider API (Sources: see the pack README). The lifecycle
states above are independent of any specific flag management system (LaunchDarkly,
Unleash, or a custom system). **A `release` flag stuck at `deprecated` beyond 90 days
is flag debt — surface it in the PRR.**

## Rollback procedure

Rollback is not one thing. Service rollback and IaC rollback have different safety
profiles and different gate types.

### Service rollback (automatic)

Re-deploying a previous immutable digest is always safe to attempt.

1. **Trigger:** ROLLBACK outcome from canary analysis, or smoke failure.
2. **Action:** Route 100% traffic back to the stable image; re-deploy the previous
   image digest from the admitted candidate's component evidence (or the most
   recent prior release tag's manifest).
3. **Rollback verification (three-step, non-waivable):**
   - **Step 1 — Traffic confirmed.** Canary weight = 0%, stable = 100%. Observable
     via service mesh telemetry or load-balancer metrics within seconds.
   - **Step 2 — Metric recovery.** Monitor error rate and latency for 2 full analysis
     intervals (minimum 2 × pause-per-step) to confirm the recovery curve.
   - **Step 3 — Smoke probe passes.** Run the smoke phase against the stable endpoint;
     every smoke assertion must pass. A failed smoke after rollback = surface to human.

### IaC rollback (non-automatic — consent-gated)

IaC rollback is **re-convergence to a prior desired state**, not a re-deploy. Terraform,
Pulumi, and CDK have no native rollback command. The mechanism is `git revert` of the
config commit + `apply`. This may not be achievable if real-world state diverged (data
was written, a managed certificate was provisioned, a DNS record propagated). **IaC
rollback is a `one-way-door` reversibility class — it requires a human consent gate.**

Protocol:
1. Surface to human with the IaC plan snapshot from `iac_plan_ref` for review.
2. Human confirms the prior state is achievable (no destructive or irreversible resource
   changes in the diff).
3. `git revert` the config commit. Run `plan` first; review the plan output. Only apply
   after the plan confirms intent matches.
4. Rollback verification: run `plan` again after `apply` — output should show no changes
   (converged). Run smoke phase.

**Always plan before apply on any IaC rollback path.** An IaC rollback that involves
deletions, DNS changes, certificate renewals, or data modifications is itself a
`one-way-door` — escalate to the human, never proceed autonomously.

## Artifact provenance verification

Before the outer loop deploys, verify that the admitted artifact has not been
substituted or tampered with since admission. This is what makes artifact
substitution detectable. A failed verification is a supply-chain integrity failure — it is a
**consent gate crossing**, not a warning.

For an image component, use the three-step verification below before its first
deploy phase. Here `image_ref` and `provenance_ref` refer to the admitted
component's image reference and resolved provenance evidence; the legacy adapter
uses `component_manifest[].image_ref`. A Terraform-only candidate has no image
step: verify the plan bundle's digest, provenance and target instead. Never
invent an image requirement for a plan-only candidate.

**Three-step image verification:**

1. **Digest re-check.** Re-fetch the image manifest from the registry using the
   `image_ref` digest. Confirm the fetched manifest digest equals the digest in
   `component_manifest[].image_ref`. A mismatch means the registry content changed after
   admission — surface immediately; do not deploy.

2. **Provenance assertion.** Verify the SLSA provenance attestation at `provenance_ref`:
   - If `type: oci-referrer`: verify via cosign/keyless or equivalent — e.g.
     `cosign verify-attestation --type slsaprovenance \
       --certificate-identity <workflow-identity-san> \
       --certificate-oidc-issuer https://token.actions.githubusercontent.com \
       <registry>/<repo>@<image_ref_digest>`
     (or the harness's equivalent guarantee). The verification checks the DSSE
     signature against the Sigstore root of trust, the payload digest, and the
     Rekor transparency log entry.
   - If `type: file`: verify the DSSE envelope signature independently.
   - The attestation's `subject[].digest` must match `component_manifest[].image_ref`.

3. **Level check.** Confirm the attestation meets **SLSA v1.0 Build L2 minimum**: a
   hosted build platform must itself generate the provenance, with verifiable
   authenticity — e.g. via `actions/attest-build-provenance` or the
   slsa-github-generator, not a local workstation. Cosign keyless signing (step 2
   above) verifies the artifact's signature; it does not generate SLSA provenance
   and does not by itself satisfy L2 — treat it as a complementary, separate
   control. **SLSA L3** (isolated build environment + signing key inaccessible to
   build steps) raises the bar further and is the aspiration for prod-bound
   artifacts. If the attestation is absent, is not build-platform-generated, or is
   L1-only, surface to human with severity `one-way-door` — the human decides
   whether to override.

**Failure action:** Write a `status: provenance-check-failed` entry to the decision log;
surface to human with the specific mismatch detail (which check failed, what the digests
were); do not proceed to `infra-apply`. Override requires explicit human consent and is
recorded in the decision log with `ratified_by: human` via the control-(a) attested channel.

## Ephemeral environment qualification

Run this qualification step at outer-loop cycle start — before the collect phase (or before
`infra-apply` in the single-component case). The check is a precondition for entering the
autonomous zone; a single `false` is a consent-gate crossing.

**The L5 floor.** An ephemeral environment must meet **L5** (dedicated cloud account /
project, or an L4/L4+ k8s namespace or vCluster that has passed the three-dimension policy
audit below) for the "reversible" label to hold under the minimum-regret carve. An environment
below this floor is a consent-gate crossing — surface to human; do not proceed with
autonomous deploy.

**The three-dimension qualification test:**

| Dimension | Condition | How to test |
|-----------|-----------|-------------|
| **Prod reachability** | No route from the ephemeral env to prod endpoints, prod databases, or prod identity stores | Network policy or security group audit: no ingress/egress to prod CIDR / prod account; credential scoping: session cannot assume prod IAM roles |
| **Data isolation** | No real user data accessible from the ephemeral env | Data classification review: env storage contains only synthetic, anonymized, or purpose-generated data; no prod snapshot was restored here |
| **Inter-env isolation** | This ephemeral env cannot affect other running ephemeral or shared staging envs | Env resources (namespaces, accounts, VPCs, state backends) are unique to this cycle; no shared mutable state with other concurrent envs |

**Provability classification — cost of the qualification step:**

- **Self-evident (L0–L3):** isolation is structural; the test passes trivially. Not relevant
  to the outer loop's ephemeral envs, but noted for the inner/outer boundary.
- **Requires policy audit (L4 namespace, L4+ vCluster):** NetworkPolicy + RBAC must be
  verified per deployment. A namespace without verified NetworkPolicy is not qualified —
  treat as a consent gate. The implementing agent reads and confirms the policy config
  before each cycle.
- **Programmatically auditable (L5 dedicated account/project):** SCP/org policies enforcing
  the account/project boundary are queryable via API. Run the policy check at cycle start.

**L4/L4+ conditional path:** an L4 or L4+ environment qualifies only after the three-dimension
policy audit passes. "Namespace isolation" without a confirmed NetworkPolicy is L2-equivalent
blast radius — it does not qualify. If the audit has not been performed this cycle, surface to
human before proceeding.

An installed `operational-safety` fidelity-ladder reference is optional additional
context. The qualification floor above stands on its own without that reference.

## Polyrepo topology

In a **single-product monorepo** the build repo is the integrated whole: no fleet manifest,
no e2e host repo. Use the single candidate through collection, admission and
focused review; no fleet assembly is needed.

In a **polyrepo / value-stream topology** — multiple component repos each producing their
own candidate — use the artifacts and steps below.

### Fleet manifest (`release-fleet.yaml`)

The fleet manifest is the cross-component release coordination artifact. It lives in the
e2e host repo, is committed by a bot PR from each component repo's CI, and is read-only
from merge time onward. It is the "courier snapshot" from the courier snapshot pattern applied to the
release loop: each component's admitted candidate binds its evidence;
the fleet manifest carries versioned references without forking the candidates.
The image-fleet example below retains the legacy `g4_package_ref` field as an
adapter locator, not a required G4 event. Direct candidates use the same pinned
locator; plan-only candidates follow collection and admission without an image
fleet manifest.

Mandatory schema:

```yaml
schema_version: "1.0"           # outer loop reads this first; unknown version → surface to human
fleet_name: <string>             # e.g. "billing-platform"
assembled_at: <RFC3339>          # timestamp of fleet assembly

components:                      # one entry per deployable component
  - name: <string>               # e.g. "auth-service"
    repo: <org/repo>             # harness-neutral identifier
    g4_package_ref: <path or URL> # path to the component's release-handoff.yaml at the pinned commit
    image_ref: "<registry>/<repo>:<tag>@sha256:<hex>"  # must match g4_package's component_manifest

deploy_sequence:                 # optional; defaults to parallel if absent
  - component: auth-service
    depends_on: []
    gate: auto
  - component: billing-api
    depends_on: [auth-service]   # waits for auth-service's gate to pass
    gate: auto
  - component: web-frontend
    depends_on: [billing-api]
    gate: manual                 # explicit human gate before this component advances

e2e_suite_ref:                   # reference to the e2e test suite in this host repo
  path: tests/e2e/
  runner: <string>               # hint: "playwright" | "cypress" | "k6" | "karate"
```

Schema compatibility: the outer loop reads `schema_version` first. Tolerant reader rule:
unknown fields are ignored; adopters may extend with additional fields.

### Canonical e2e host repo

**Must contain:**
- `release-fleet.yaml` (fleet manifest — outer loop entry point).
- A composition file (`docker-compose.yaml`, Helm umbrella chart, or Kustomize overlay)
  referencing image digests from the fleet manifest.
- An e2e test suite treating the composed system as a black box (every assertion goes through
  service APIs or UI surfaces, never internal component APIs).
- CI configuration triggering the outer loop on fleet manifest merge or registry-event webhook.

**Must NOT contain:**
- Component application source code (any component source).
- Per-component unit or integration tests (those belong in the component repo's inner loop).
- Credentials or secrets in source (all secrets are broker-mediated).

**Release capability:** each participating repo needs the release collector,
validator, admission and focused reviewer capabilities at its execution scope.
The direct path does not require core or repo-governance. Installed build
reviewers may supplement it but cannot replace either local release role.

### Five-term harness-neutral vocabulary

| Term | Definition | ArgoCD | Flux | Spinnaker / GHA |
|------|-----------|--------|------|-----------------|
| **Component** | A deployable unit with its own repo and version stream | `Application` | `Kustomization` / `HelmRelease` | stage target / service |
| **Stage** | A named deploy target (staging, canary, production) | project / cluster | namespace | pipeline environment |
| **Gate** | A blocking decision point (automated or human) | health check / sync status | readiness gate | `Check Preconditions` / `Manual Judgment` |
| **Depends-on** | Component B must not deploy until component A passes its gate in the same stage | sync wave ordering | `HelmRelease.spec.dependsOn` | Pipeline sub-stage + wait |
| **Release manifest** | A file recording the pinned version of every component for this release | `Application` image tag | image policy marker | `Release` artifact |

The `deploy_sequence[].depends_on` field in the fleet manifest carries the intent; the
adopter's orchestrator translates it to tool-specific primitives.

### Collect-then-validate pre-deploy step

Before `infra-apply`, run a **collect phase** for each component in the fleet manifest:

```
Collect phase (before infra-apply):
  for each component in fleet_manifest.components:
    1. Resolve its candidate and existing evidence into confined local files
       through an authorized caller; never fetch from the collector script.
    2. Collect, admit and verify with the caller's trusted policy and expected target.
    3. Run both focused reviews, check-review and check-stage pre-deploy.
    4. Verify component artifact pins and provenance against the fleet snapshot.
    5. On any refusal: stop, name the code and route to the recorded owner.
  On all-pass: check action authority, isolation and consent before infra-apply.
```

In the monorepo/single-component case fleet iteration is unnecessary; collection,
admission and focused review still run.

### Triggering conventions

(a) **Bot PR approach:** each component repo's CI opens a PR bumping
`components[N].image_ref` to the new digest; the adopter's merge policy merges it.
(b) **Scheduled reconciliation:** a scheduled loop queries each component registry for the
latest passing-gate version and assembles a new fleet manifest. Use (b) when components
release continuously.

The trigger implementation is adopter toolchain — the doctrine does not prescribe
`repository_dispatch` or any specific mechanism.

### Distinction from meta-repo feature coordination

Meta-repo coordination covers the **product-engineering meta-repo** — feature coordination
across repos, per-component brief slicing, and shared contract versioning (the upstream
discovery/build layer). This mechanism covers the **release-loop's cross-repo coordination** —
fleet assembly, version validation, and deploy sequencing after candidates are admitted.
The two are parallel, not redundant. Both apply the "reference-by-version + read-only
courier snapshot" pattern to different layers.
