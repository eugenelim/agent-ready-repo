# RFC-0072: Release-loop deploy doctrine — G4 artifact format and progressive delivery

<!-- Written for a cold reader who has not read the related RFCs. Coined terms
are glossed on first use inline. -->

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-27
- **Date closed:** 2026-07-27
- **Decision weight:** heavy <!-- Specifies the work-loop/release-loop handoff interface and the release-loop's deploy mechanics; concrete defaults that constrain implementing agents; changes to a shipped skill and spec. Non-trivial to revise once adopters build against the G4 schema and canary thresholds. -->
- **Related:**
  - [RFC-0048](0048-autonomous-product-team-operating-model.md) (operating model foundation — gate arc, sidecar substrate, **Accepted 2026-06-30**)
  - [RFC-0049](0049-the-release-loop-and-company-os.md) (release-loop parent RFC — **Accepted 2026-06-30**; minimum-regret carve, G4→G5 arc, progressive delivery named as a reversibility primitive)
  - [RFC-0073](0073-slo-authoring-and-error-budget.md) (sibling — SLO-authoring capability and error-budget PRR integration; the `error-budget` field in the PRR depends on this RFC's G4 package schema)
  - [ADR-0044](../adr/0044-inner-outer-loop-split-and-minimum-regret-deploy-carve.md) (records the inner/outer loop split and the minimum-regret carve as an architectural decision)
  - [`docs/specs/release-loop/spec.md`](../specs/release-loop/spec.md) (the implementing spec — AC5, AC6, AC7, AC10(e) reference behaviors this RFC fills in)

---

## Reviewer brief

- **Decision:** Whether to specify — as harness-neutral doctrine extensions to the `release-loop`
  skill — (a) a G4 handoff package schema, (b) a four-phase deploy ordering protocol,
  (c) concrete canary analysis defaults and outcome protocol, (d) a six-state feature flag
  lifecycle, (e) service vs. IaC rollback procedures with a verification protocol, and
  (f) a provenance verification step before deploy.
- **Recommended outcome:** Accept D1–D6.
- **Change if accepted:**
  - The `release-loop` skill gains a **G4 handoff package** section: a `release-handoff.yaml`
    schema that the inner loop commits at G4 and the outer loop validates on receipt (D1).
  - The skill gains a **deploy ordering** section: four canonical phases
    (infra-apply → service-deploy → smoke → canary) with conditions, gate types, and
    failure actions encoded in the G4 package (D2).
  - The skill gains a **canary analysis** section: concrete traffic step defaults
    (5% → 25% → 50% → 100%), threshold defaults by service class, and a four-outcome
    protocol (PROMOTE / ROLLBACK / PAUSE / HALT) (D3).
  - The skill gains a **feature flag lifecycle** section: six states
    (created → deployed-off → enabled-pct → full-rollout → deprecated → removed) and
    four flag types with expected lifetimes; the deploy→release decoupling invariant
    is expressed as a state-transition rule (D4).
  - The skill gains a **rollback** section: service rollback (automatic; digest re-deploy)
    vs. IaC rollback (non-automatic; consent-gated git-revert + re-apply), with a
    three-step verification protocol (D5).
  - The skill gains a **provenance verification** section: SLSA L2 minimum + cosign-keyless
    or equivalent harness guarantee before deploy; failure is a consent gate crossing (D6).
  - `docs/specs/release-loop/spec.md` AC5, AC6, AC7, and AC10(e) receive cross-references
    to this RFC as the source of the doctrine those ACs require — no AC text changes
    (the ACs already mandate the behaviors; this RFC fills in the "how").
- **Affected surfaces:**
  - `packs/release-engineering/.apm/skills/release-loop/SKILL.md` — six new doctrine
    sections added; no changes to existing sections
  - `docs/specs/release-loop/spec.md` — note added to AC5, AC6, AC7, AC10(e)
    cross-referencing this RFC
  - `packs/release-engineering/pack.toml` + `.claude-plugin/plugin.json` — minor version bump
  - `docs/product/changelog.md` — `[Unreleased]` entry
- **Stakes:** Non-trivial once adopters build against the G4 schema and canary thresholds.
  The G4 schema is the inner/outer loop interface — revising it requires a coordinated bump
  across both loops. The canary thresholds create anchor points that influence operational
  decisions under pressure.
- **Review focus:** All decisions resolved in authoring session (D1–D6). Confirm or
  redirect any.
- **Not in scope:** The SLO-authoring skill or error-budget PRR integration (RFC-0073).
  Changes to `work-loop` or `discovery-loop`. New reviewer agents (three-reviewer ceiling
  holds). New top-level directories. The operate/incident loop (a future sibling RFC).

---

## The ask

**Recommendation:** Extend the `release-loop` skill with six concrete doctrine sections that
turn its three named reversibility primitives — ephemeral environments, feature flags,
auto-rollback — into a fully-specified deploy mechanics protocol.

**Why now (SCQA — Situation / Complication / Question / Answer):**

*Situation:* The `release-loop` skill shipped with the `release-engineering` pack (RFC-0049,
Accepted 2026-06-30). It names canary metric analysis (success / error / latency) as the
convergence policy (AC6), names canary + feature flags + auto-rollback as the reversibility
primitives that make autonomous outer-loop operation possible (AC5), and states that the
digest-pinned artifact "is detectable" if substituted between G4 and deploy (AC7). The
skill is coherent and accepted.

*Complication:* Three gaps remain that block an implementing agent from running the loop
without re-deriving fundamentals on each cycle:

- **G4 format gap.** The handoff package has no schema — the inner loop has nothing
  to emit, and the outer loop has nothing to validate. AC7's provenance check is
  nominal until the package exists.
- **Progressive delivery gap.** Traffic percentages, metric thresholds, outcome conditions,
  feature flag state transitions, and the distinction between automatic service rollback
  and consent-gated IaC rollback are all named but not specified. An implementing
  `release-lead` agent must derive these under time pressure, producing inconsistent
  canaries and incorrect rollback decisions.
- **Provenance gap.** AC7 says a substituted artifact "is detectable," but the
  verification step — when it runs, what it checks, what failure means — is absent.

*Question:* Can these mechanics be specified as harness-neutral doctrine (no runtime,
no new reviewer, no executable) that fits inside the skill's content-only constraint
(AC9, ADR-0031)?

*Answer:* Yes. The ecosystem has converged on concrete, interoperable defaults for all
three gaps. Argo Rollouts, Flagger, and Spinnaker all publish conservative floor
thresholds with explicit tightening guidance. OCI digest + SLSA provenance + sigstore
cosign keyless signing have become the de facto supply-chain integrity stack. Unleash,
LaunchDarkly, and OpenFeature together produce a harness-neutral six-state flag lifecycle.
None of these require a runtime — they are decision protocols that map onto file edits
and policy checks, the same form the loop already uses.

---

## Decisions requested

| ID | Question | Recommendation | Rationale | Decide by | Reviewer action |
|----|----------|----------------|-----------|-----------|-----------------|
| D1 | G4 handoff package format: (A) a version-controlled `release-handoff.yaml` with a defined schema committed at G4, or (B) an unstructured artifact manifest with no schema constraint? | **A — versioned `release-handoff.yaml` with defined schema** | A schema is the interface contract between the inner and outer loops. Without it the outer loop cannot validate what it received and the provenance check (D6) has no artifact reference. The schema must be harness-neutral YAML — not a JFrog Release Bundle CRD, Argo Application, or Flux `OCIRepository` (all are toolchain-specific). A `schema_version` field enables independent evolution of the two loops. The G4 package commits alongside the built artifact at G4 and is read-only from that point onward. | This review | Confirmed |
| D2 | Deploy ordering: (A) four canonical phases (infra-apply → service-deploy → smoke → canary) encoded in the G4 package as an ordered phase list, or (B) ordering left entirely to adopter toolchain? | **A — four canonical phases in the G4 package** | The infra-apply → service-deploy ordering is not an adopter preference — services reference infra outputs (database URLs, IAM role ARNs, VPC IDs). Smoke must precede canary. Encoding these as a phase list in the G4 package makes the ordering explicit, auditable, and visible to the outer loop before it executes. The `tool` field is a hint (terraform / argocd-sync / helm-upgrade / kubectl-apply); adopters substitute their orchestrator. The four phases are the non-waivable ordering floor; adopters may add phases between or after them. | This review | Confirmed |
| D3 | Canary analysis defaults: (A) concrete floor defaults (5% → 25% → 50% → 100%; success rate ≥ 95%; error rate ≤ 5%; p99 latency ≤ 500 ms) with a four-outcome protocol and explicit service-class tightening tiers, or (B) no defaults — leave all thresholds to adopter? | **A — concrete floor defaults with service-class tiers and explicit override instruction** | The ecosystem evidence (Argo Rollouts documentation, Flagger docs, Spinnaker best-practices guide) uniformly recommends starting defaults and tightening per service class. Option B forces every adopter to derive thresholds from first principles under time pressure, producing inconsistent and under-specified canaries. The proposed defaults are conservative floors — a 5% error ceiling catches the most common failure modes; tightening to 1% for stateful or payment-path services and ≤ 200 ms p99 for interactive APIs is documented inline. The four-outcome protocol (PROMOTE / ROLLBACK / PAUSE-for-human / HALT) maps onto the tool primitives (Argo Rollouts `failureLimit` / Spinnaker marginal band / oscillation circuit breaker). | This review | Confirmed |
| D4 | Feature flag lifecycle: (A) specify a six-state harness-neutral lifecycle (created → deployed-off → enabled-pct → full-rollout → deprecated → removed) plus four flag type categories with expected lifetimes, or (B) leave flag lifecycle entirely to the adopter's flag management system? | **A — six-state lifecycle and four flag types** | The deploy→release decoupling invariant — code deploys behind a flag in `deployed-off` state; the flag transitions to `enabled-pct` only after smoke passes — requires a shared vocabulary the skill can reference when instructing an implementing agent. Without named states the skill cannot specify when to advance or clean up a flag. OpenFeature (CNCF incubating project) provides the harness-neutral API layer; the six lifecycle states sit above it and are independent of any specific flag management system. Flag type categories (release ≤ 90 days, operational indefinite, experiment ≤ 90 days, permission service-dependent) constrain expected cleanup windows and prevent flag debt. | This review | Confirmed |
| D5 | Rollback procedure: (A) specify service rollback (automatic; re-deploy previous digest) and IaC rollback (non-automatic; consent-gated git-revert + re-apply) as distinct procedures with a three-step rollback verification protocol, or (B) treat all rollback as a single automatic procedure? | **A — two distinct procedures with separate gate types** | Service rollback re-deploys an immutable artifact; it is always safe to attempt and can be automatic. IaC rollback re-converges to a prior desired state — it may not be achievable if real-world state diverged (data was written, a managed cert was provisioned, a DNS record propagated). Making IaC rollback automatic would violate the minimum-regret carve: it is potentially irreversible (one-way-door) and must be a consent gate. The three-step verification protocol (traffic weight to stable = 100%, error rate recovery over two analysis intervals, smoke probe passes) is the minimum evidence that a rollback succeeded and is consistent with Flagger's post-rollback observation practice. | This review | Confirmed |
| D6 | Artifact provenance verification: (A) require provenance verification before deploy (SLSA L2 minimum; cosign-keyless or equivalent harness guarantee; failure = consent gate crossing), or (B) treat provenance as advisory — proceed even on failure? | **A — provenance verification required; failure is a consent gate crossing** | Option B means AC7's "detectable" claim is nominal — the control exists in doctrine but has no execution path. SLSA L2 is achievable on any hosted CI platform (GitHub Actions, GitLab CI, Google Cloud Build) without custom tooling. Cosign keyless signing (OIDC-backed Fulcio certificate + Rekor transparency log) removes the key distribution problem that made earlier signing adoption slow. A failed provenance check is a supply-chain integrity failure and falls under AC10(g)'s deploy-credential tiering + AC3's isolation-as-carve-precondition: the outer loop must not deploy an artifact whose provenance chain is broken — surface to the human, do not proceed. | This review | Confirmed |

*Default if no objection: adopt D1–D6 and proceed to implementation.*

---

## Problem and goals

### The G4 boundary is underspecified

`release-loop` AC7 states: "The outer loop deploys the digest-pinned artifact the inner loop
verified. A substituted or rebuilt artifact between G4 and deploy is detectable (artifact
provenance across the handoff — OWASP 2025 supply-chain), not assumed identical."

The spec implies a handoff package with a pinned artifact reference and a provenance
assertion. Neither the package schema nor the verification step exists.

### The convergence policy has thresholds without values

AC6 specifies: "canary metric analysis (success / error / latency SLOs)." AC5 names
canary + feature flags + auto-rollback as the reversibility primitives. AC10(e) specifies
an oscillation circuit-breaker. None of the following are specified:

- canary traffic percentages and step duration
- success rate, error rate, and latency thresholds
- the failure limit that triggers automatic rollback
- the marginal / ambiguous band that triggers a human pause
- feature flag state transitions and the deploy→release coupling rule
- the distinction between automatic service rollback and consent-gated IaC rollback

### Goals

- Specify a concrete G4 handoff package schema as the inner/outer loop interface.
- Specify the canonical deploy phase ordering and conditions.
- Specify concrete canary analysis defaults with an explicit four-outcome protocol.
- Specify a harness-neutral feature flag lifecycle aligned with the deploy→release
  decoupling invariant.
- Distinguish service rollback (automatic) from IaC rollback (consent-gated) with a
  three-step verification protocol.
- Specify the provenance verification step that fulfills AC7's "detectable" claim.

---

## Evidence

### G4 artifact format — OCI + SLSA provenance

**OCI digest conventions.** The canonical digest-pinned form is
`registry/repo:tag@sha256:<64-hex>` — a combined tag (human-readable) plus digest
(cryptographically immutable). A tag-only reference is mutable; a digest-only reference
is opaque to humans. The combined form satisfies both requirements and is the G4
component manifest's required image reference format.

**SLSA provenance (v1.2).** An SLSA provenance attestation is an in-toto DSSE (Dead
Simple Signing Envelope)-wrapped JSON with `buildDefinition` (buildType,
externalParameters, resolvedDependencies) and `runDetails` (builder.id,
metadata.invocationId, timestamps). L2 requires a hosted build platform and
cryptographic signing (GitHub Actions + cosign keyless satisfies this: the OIDC-backed
ephemeral Fulcio certificate is platform-issued). L3 additionally requires an isolated
build environment where the signing key is inaccessible to build steps.

**Cosign keyless signing.** Cosign stores signatures and attestations as OCI referrers
(OCI 1.1 referrers API, March 2024). The `cosign verify-attestation` command checks the
DSSE signature, the payload digest, and the Sigstore transparency log (Rekor) entry.
Keyless signing (Fulcio certificate + Rekor inclusion) removes key distribution from the
adopter's scope — the signing identity is the CI job's OIDC token; verification requires
only the Sigstore root of trust.

**JFrog Release Bundle v2 and Flux `OCIRepository`** both confirm the ecosystem's
convergence on DSSE-signed, digest-pinned artifact packages as the deploy-ready
handoff format.

### Canary analysis — ecosystem convergence

| Parameter | Argo Rollouts examples | Flagger defaults | Spinnaker guidance |
|---|---|---|---|
| Traffic steps | 20% → 40% → 60% → 80% → 100% (examples vary) | `stepWeight: 10, maxWeight: 50` | Not fixed |
| Success rate floor | ≥ 95% | Analysis-dependent | ≥ 95% (passThreshold) |
| Latency p99 ceiling | ≤ 1 s | Analysis-dependent | Service-dependent |
| Failure limit | `failureLimit: 3` | `threshold: 10` | Score &lt; marginalThreshold |
| Marginal / pause | No native state; use `pause: {}` step | No native state | 75–95 score → human decision |
| Auto-promote | `successCondition` met each step | Copies canary→primary | Score ≥ passThreshold |

Conservative floor synthesis (this RFC): 5% → 25% → 50% → 100%; success rate ≥ 95%;
error rate ≤ 5%; p99 ≤ 500 ms; failure limit 3 consecutive; oscillation circuit-breaker
at 3 consecutive promote↔rollback cycles (AC10(e)). Tightening tiers: stateful and
payment-path services → ≥ 99% success, ≤ 1% errors, ≤ 200 ms p99; interactive APIs → 
≥ 99%, ≤ 1%, ≤ 200 ms p99.

### Feature flag lifecycle — harness-neutral convergence

Unleash (5 states) and LaunchDarkly (6 states) converge on the same pattern: flags
must reach an end state that removes them from code, not merely "archived" in the
management system. "Stuck in cleanup" is the primary indicator of flag debt. OpenFeature
(CNCF incubating project) provides the harness-neutral provider API;
lifecycle state management sits above it.

This RFC's six-state synthesis: created → deployed-off → enabled-pct → full-rollout →
deprecated → removed. The deploy→release decoupling invariant expressed as a state-
transition rule: code merges to main with the flag at `deployed-off`; the flag advances
to `enabled-pct` only after smoke passes (not at deploy time — at convergence time).

### IaC rollback — no native rollback command

Terraform has no native rollback command. HashiCorp's official rollback guidance:
emergency mechanism is restoring a previous versioned state file from the backend (S3,
GCS, Terraform Enterprise), then re-aligning config + running `terraform plan` before
`terraform apply`. Spacelift's guide confirms: always plan before apply on any rollback
path. Rollback involving resource deletions, DNS changes, certificate provisioning, or
data modifications may not be achievable even with a prior state file — this is a
categorically different risk profile from re-deploying a container image.

---

## The G4 handoff package schema (D1 elaboration)

The `release-handoff.yaml` file is committed to the repository by `work-loop` at G4,
alongside the deploy-ready artifact. It is read-only from that point. Mandatory fields:

```yaml
schema_version: "1.0"           # semver; outer loop reads this first
built_at: <RFC3339>              # timestamp of the inner loop's G4 completion
built_by: <CI run identifier>    # e.g. "github-actions/runs/12345" — harness-neutral opaque string

component_manifest:              # one entry per deployable component
  - name: <string>
    image_ref: "<registry>/<repo>:<tag>@sha256:<64-hex>"   # combined form, always

provenance_ref:                  # reference to the SLSA attestation
  type: oci-referrer             # "oci-referrer" | "file"
  subject_digest: "sha256:<hex>" # the image manifest digest the attestation covers
  # for type: file —
  # path: path/to/provenance.jsonl

iac_plan_ref:                    # reference to the IaC plan snapshot
  type: file                     # "file" | "artifact-url"
  path: path/to/plan.json        # Terraform JSON plan or CDK diff output

test_evidence_summary:           # pass/fail record from the inner loop at G4
  unit: pass | fail
  integration: pass | fail
  lint: pass | fail
  security_scan: pass | fail

changelog_delta:                 # structured list since last release tag
  since_ref: <git tag or SHA>
  entries:
    - id: <issue/PR id>
      summary: <one line>

deploy_phases:                   # see D2 — ordered phase list
  - phase: infra-apply
    tool: terraform               # hint; adopter overrides
    gate: auto
    condition: "plan_digest_matches_handoff"
    on_failure: surface           # IaC failure = consent gate
  - phase: service-deploy
    tool: argocd-sync
    gate: auto
    depends_on: [infra-apply]
  - phase: smoke
    tool: <test runner>
    gate: auto
    on_failure: rollback          # service rollback automatic
    depends_on: [service-deploy]
  - phase: canary
    gate: auto                    # metric-gated; or "manual" for explicit human step
    depends_on: [smoke]
```

The outer loop reads `schema_version` first; if the version is unknown it flags the
discrepancy and surfaces to the human rather than failing silently. Adopters may add
fields; the outer loop ignores unknown fields (tolerant reader).

---

## Drawbacks

- **Threshold anchor-bias risk.** Specifying concrete floor defaults creates anchor bias —
  adopters may copy-paste without tightening for their service class. Mitigated by pairing
  every default with a service-class tightening table and an explicit "conservative floor,
  not a production value" callout in the skill.
- **G4 schema version fragility.** A versioned interface between the two loops creates a
  coordination surface. If the schema evolves, both loops must be bumped. Mitigated by the
  tolerant-reader pattern (unknown fields ignored; unknown version → surface, not crash) and
  the `schema_version` field enabling soft migration.
- **IaC rollback consent gate frustrates autonomy.** Requiring human consent for IaC
  rollbacks means the outer loop cannot fully auto-recover from infra failures. This is
  correct behavior (IaC changes are potentially irreversible), but it violates the
  "autonomous loop" promise for that failure class. The skill must name this trade-off
  explicitly so adopters understand their infra design choices affect the autonomy envelope.
- **Four-phase ordering may not fit all topologies.** The canonical four phases assume a
  single-component deploy. Multi-component or microservice topologies may need parallel
  service-deploy steps or component-specific smoke phases. Mitigated by the "adopters
  may add phases" rule — the four are a floor, not a ceiling.

## Follow-on artifacts

On acceptance:
- **Implementing spec:** `docs/specs/release-loop/spec.md` — add a notes entry
  cross-referencing this RFC for AC5, AC6, AC7, and AC10(e); no AC text changes.
- **Skill update:** `packs/release-engineering/.apm/skills/release-loop/SKILL.md` —
  add six new sections per D1–D6 as described in the Reviewer brief.
- **Pack version bump:** `packs/release-engineering/pack.toml` +
  `.claude-plugin/plugin.json` — minor version bump.
- **Changelog:** `docs/product/changelog.md` — `[Unreleased]` entry.
