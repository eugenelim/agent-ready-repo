# RFC-0075: Polyrepo / value-stream release topology

<!-- Written for a cold reader who has not read the related RFCs. Coined terms
are glossed on first use inline. -->

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-27
- **Date closed:** 2026-07-27
- **Decision weight:** standard <!-- Adds doctrine and extends the release-loop
  skill; no adopter interface is frozen in v1 (the fleet manifest format carries
  schema_version). The deploy-sequencing vocabulary is the most load-bearing
  claim — it constrains how adopters declare inter-component dependencies. -->
- **Related:**
  - [RFC-0049](0049-the-release-loop-and-company-os.md) (release-loop parent RFC —
    **Accepted 2026-06-30**; OQ1 names the polyrepo topology and references
    ADR-0022 for cross-repo artifact referencing; AC9 names the "value-stream
    cross-repo mechanism (reference-by-version + the read-only courier snapshot)"
    that this RFC specifies)
  - [RFC-0072](0072-release-loop-deploy-doctrine.md) (sibling — **Accepted 2026-07-27**;
    D1 specifies the G4 handoff package that this RFC extends for the multi-component
    case with the fleet manifest)
  - [ADR-0022](../adr/0022-value-stream-meta-repo-cross-component-layer.md) (the
    product-engineering cross-component layer — reference-by-version + courier snapshot;
    this RFC applies the same pattern to release-loop coordination)
  - [`docs/specs/release-loop/spec.md`](../specs/release-loop/spec.md) (AC9 references
    the "value-stream cross-repo mechanism" this RFC specifies)

---

## Reviewer brief

- **Decision:** Whether to specify — as harness-neutral doctrine extensions to the
  `release-loop` skill — (a) a fleet manifest format for multi-component release
  coordination, (b) a canonical e2e host repo definition, (c) a five-term harness-neutral
  vocabulary for multi-service deploy sequencing, (d) the courier snapshot as the
  cross-repo component version lock mechanism, and (e) a "collect-then-validate" pre-deploy
  step that the outer loop runs in a polyrepo topology before entering the standard four
  deploy phases.
- **Recommended outcome:** Accept D1–D5.
- **Change if accepted:**
  - The `release-loop` skill gains a **Polyrepo topology** section with the fleet
    manifest schema, the e2e host repo definition, the deploy sequencing vocabulary, and
    the collect-then-validate pre-deploy step (D1–D5).
  - `docs/specs/release-loop/spec.md` AC9 receives a cross-reference to this RFC as
    the source of the cross-repo mechanism — no AC text changes (AC9 already mandates
    the behaviors; this RFC fills in the "how").
  - `packs/release-engineering/pack.toml` + `.claude-plugin/plugin.json` — patch
    version bump.
  - `docs/product/changelog.md` — `[Unreleased]` entry.
- **Affected surfaces:**
  - `packs/release-engineering/.apm/skills/release-loop/SKILL.md` — new Polyrepo
    topology section added; no changes to existing sections
  - `docs/specs/release-loop/spec.md` — cross-reference note on AC9
  - `packs/release-engineering/pack.toml` + `.claude-plugin/plugin.json` — patch
    version bump
  - `docs/product/changelog.md` — `[Unreleased]` entry
- **Stakes:** Moderate. The fleet manifest format is an extension of the G4 handoff
  package (RFC-0072 D1) — it carries `schema_version` for independent evolution. The
  sequencing vocabulary is the most load-bearing claim: adopters who declare
  `depends_on` in the fleet manifest are making an explicit ordering commitment. Revising
  the vocabulary requires a coordinated bump, but the v1 scope is deliberately minimal
  to keep that surface small.
- **Review focus:** All decisions resolved in authoring session (D1–D5). D3 (vocabulary)
  is the most judgment-sensitive — confirm it maps onto real orchestrator primitives
  without being too narrow.
- **Not in scope:** Building any cross-repo orchestration runtime. Specifying ArgoCD,
  Flux, or Spinnaker configuration (adopter toolchain). Changing `work-loop` (the inner
  loop produces per-component G4 packages unchanged). Replacing ADR-0022 (which covers
  the product-engineering meta-repo; this RFC covers the release-loop's cross-repo
  coordination, a parallel but distinct concern). The operate/incident loop.

---

## The ask

**Recommendation:** Extend the `release-loop` skill with a Polyrepo topology section that
fills in the "value-stream cross-repo mechanism" AC9 references but does not yet specify.

**Why now (SCQA — Situation / Complication / Question / Answer):**

*Situation:* The `release-loop` skill (AC9) acknowledges that in a polyrepo / value-stream
topology each component repo and the cross-component e2e host repo must install `core` +
`release-engineering`, and states that "cross-repo artifact referencing uses the
value-stream cross-repo mechanism (reference-by-version + the read-only courier
snapshot)." RFC-0049 OQ1 names ADR-0022 (reference-by-version + courier snapshot) as the
cross-repo mechanism for artifact referencing.

*Complication:* ADR-0022 specifies the **product-engineering** cross-component layer: a
meta-repo for feature coordination, per-component brief slicing, and a shared contract
referenced by version. This is the upstream discovery/build coordination pattern. The
release loop needs a **parallel but distinct** cross-repo mechanism: a way to assemble
multiple component G4 packages into a jointly-validated fleet, declare inter-component
deploy ordering, and coordinate the cross-component e2e suite — none of which ADR-0022
addresses. Without this specification, three things are undefined:

1. The fleet manifest: what the e2e host repo collects from component repos to declare
   "these versions, deployed together, are what we validated."
2. The e2e host repo: what it is allowed to contain, what it installs, and what triggers
   its outer loop.
3. Multi-service deploy sequencing: how inter-component ordering is declared in a
   harness-neutral way that maps onto ArgoCD, Flux, Spinnaker, or GitHub Actions without
   locking to any one tool.

*Question:* Can the cross-component release coordination mechanism be specified as
harness-neutral doctrine that extends the G4 handoff package pattern without building a
new runtime or coordinator?

*Answer:* Yes. The ecosystem has converged on a release manifest (version lock file) as the
cross-component coordination artifact, and on a canonical e2e host repo shape (composition
+ tests + CI config; no component source). The five-term deploy sequencing vocabulary
(Component, Stage, Gate, Depends-on, Release manifest) maps onto every major orchestrator
without locking to one. The "collect-then-validate" pre-deploy step re-uses the outer
loop's existing G4 validation logic applied once per component before the fleet is
assembled. None of these require a runtime — they are file edits and policy checks, the
same form the loop already uses.

---

## Decisions requested

| ID | Question | Recommendation | Rationale | Decide by | Reviewer action |
|----|----------|----------------|-----------|-----------|-----------------|
| D1 | Fleet manifest format: (A) a version-controlled `release-fleet.yaml` file in the e2e host repo, with a defined schema that enumerates component versions + deploy ordering + phase overrides, extending the G4 handoff package pattern from RFC-0072 D1, or (B) leave fleet coordination format entirely to adopter toolchain? | **A — versioned `release-fleet.yaml` in the e2e host repo** | The G4 handoff package (RFC-0072 D1) is the per-component artifact; the fleet manifest is the multi-component assembly. Without it, the outer loop has no single artifact that records "these component versions, validated together." The courier snapshot pattern from ADR-0022 (reference the authority, carry a snapshot, never fork) applies directly: each component's G4 package is the authority; the fleet manifest carries versioned references to them. | This review | Confirmed |
| D2 | E2e host repo definition: (A) specify a canonical e2e host repo structure (composition file + test suite + CI config; no component source; must install `core` + `release-engineering` at repo scope; consumes component artifacts from a registry, not source), or (B) leave e2e host repo structure entirely to adopter discretion? | **A — specify the canonical e2e host repo shape** | AC9 says the cross-component e2e host repo "must itself install `core` + `release-engineering`" — this is already doctrine. What's missing is what else it may and must NOT contain. Without specifying that it holds no component source (only registry coordinates), adopters may couple the host repo to component source trees, which defeats the version-independence that the fleet manifest provides. | This review | Confirmed |
| D3 | Deploy sequencing vocabulary: (A) adopt a five-term harness-neutral vocabulary (Component, Stage, Gate, Depends-on, Release manifest) encoded in the fleet manifest's `deploy_sequence` field, or (B) use an orchestrator-specific vocabulary (ArgoCD sync waves, Spinnaker stage dependencies, Flux reconciliation ordering)? | **A — five-term harness-neutral vocabulary** | The ecosystem has three dominant orchestrators (ArgoCD, Flux, Spinnaker) with mutually incompatible DSLs for ordering (sync waves, HelmRelease `dependsOn`, sub-pipeline invocation). A doctrine RFC that locks to one of these excludes the other two. The five-term vocabulary maps onto all three: `depends_on` maps to ArgoCD sync waves, Flux `HelmRelease.spec.dependsOn`, and Spinnaker's `Pipeline` + `Check Preconditions` stage; `gate` maps to health checks, metric thresholds, or manual judgments in each tool. | This review | Confirmed |
| D4 | Courier snapshot: (A) specify that the fleet manifest's component references use the same "reference-by-version + read-only courier snapshot" pattern as ADR-0022 — each component entry references its `image_ref` digest + G4 package path; the fleet manifest is the courier snapshot for the assembled fleet, committed alongside and read-only from that point, or (B) reference ADR-0022 without specifying the release-loop form? | **A — specify the release-loop form** | ADR-0022 specifies the product-engineering form (contract version + courier snapshot). The release-loop form is parallel but distinct: the "authority" is the per-component G4 package; the "courier snapshot" is the fleet manifest. Pointing at ADR-0022 without specifying the release-loop form leaves the adopter to derive the adaptation themselves. | This review | Confirmed |
| D5 | Collect-then-validate pre-deploy step: (A) the outer loop runs a "collect" phase before the standard four deploy phases (infra-apply → service-deploy → smoke → canary) in which it reads each component's G4 package from the fleet manifest, validates each package (provenance check + digest re-check per RFC-0072 D6), and confirms the fleet manifest is consistent with the current registry state — only then advancing to infra-apply, or (B) leave the multi-component validation ordering to adopter judgment? | **A — explicit collect phase before the four standard phases** | RFC-0072 D6 (provenance verification) specifies the per-component validation step. In the polyrepo case, running that step for each component is the minimum before any deploy begins — otherwise, the fleet could deploy a subset of validated components and mix them with unvalidated ones. Making the collect phase explicit in the fleet manifest's `deploy_sequence` makes the multi-component ordering legible and auditable. | This review | Confirmed |

*Default if no objection: adopt D1–D5 and proceed to implementation.*

---

## Problem and goals

### AC9's cross-repo mechanism is named but not specified

`release-loop` AC9 states: "In a polyrepo / value-stream topology each component repo and
the cross-component-e2e host repo must themselves install `core` + `release-engineering`;
absent that install the per-repo reuse is not sound and the loop surfaces the gap (fail-
closed). Cross-repo artifact referencing (other components' contracts / specs / built
versions) uses the value-stream cross-repo mechanism (reference-by-version + the read-only
courier snapshot), not a new coordinator."

RFC-0049 OQ1 adds: "the cross-component e2e runs in its `core`-bearing host repo" and
references ADR-0022 (reference-by-version + the read-only courier snapshot) as the
artifact-referencing mechanism. ADR-0022 specifies the product-engineering form — a
meta-repo for feature coordination, brief slicing, and contract versioning — not the
release-loop form. The release-loop's cross-repo mechanism needs its own specification:
what the fleet manifest is, what the e2e host repo contains, and how multi-service deploy
ordering is declared.

### Goals

- Specify the fleet manifest format as the cross-component release coordination artifact.
- Specify the canonical e2e host repo structure.
- Specify the five-term deploy sequencing vocabulary.
- Specify the collect-then-validate pre-deploy step for the polyrepo outer loop.
- Cross-reference the result from AC9 of the release-loop spec.

---

## Evidence

### The fleet manifest / release manifest pattern

The ecosystem has converged on a version lock file (release manifest) as the
cross-component coordination artifact. Examples: `release-please` manifest
(`release-please-config.json` + `.release-please-manifest.json`), Renovate's
dependency lock, and the Git-ops config-repo pattern (Flux, ArgoCD). The common pattern:

- Each component repo's CI produces an immutable versioned artifact (OCI image with digest,
  Helm chart in OCI registry) and pushes it to a registry.
- A config / integration repo holds a manifest file recording the pinned version of every
  component: `{"auth-service": "1.4.2@sha256:...", "billing-api": "2.0.0@sha256:..."}`.
- CI in each component repo opens a bot PR against the config repo to bump its entry.
- The integration pipeline validates the manifest by composing those versions and running
  the e2e suite.

This file is the "courier snapshot" from ADR-0022's pattern applied to the release loop:
it captures the exact component set that was jointly validated, immutably.

### The e2e host repo pattern

The settled structure for cross-component testing (Codefresh, CircleCI, and GitHub Actions
cross-repo dispatch documentation; confirmed by practitioner survey across integration
testing guides):

- **Composition file** — a Docker Compose file, Helm umbrella chart, or Kustomize overlay
  that references versioned artifacts (images by digest, charts by version) from the fleet
  manifest. Component source is never imported — only registry coordinates.
- **Test suite** — end-to-end tests treating the composed system as a black box (Cypress,
  Playwright, k6, Karate). No per-component unit or integration tests.
- **CI configuration** — a workflow triggered by the fleet manifest PR merge, or by a
  `repository_dispatch` event from a component repo's CI carrying the new component version.
- **No component source.** The host repo installs nothing from component repos at the code
  level — it consumes only registry-published artifacts.

### Harness-neutral deploy sequencing vocabulary

The five terms map onto the three dominant orchestrators:

| Term | Definition | ArgoCD | Flux | Spinnaker / GHA |
|------|-----------|--------|------|-----------------|
| **Component** | A deployable unit with its own repo and version stream | `Application` | `Kustomization` / `HelmRelease` | stage target / service |
| **Stage** | A named deploy target (staging, canary, production) | project / cluster | namespace | pipeline environment |
| **Gate** | A blocking decision point (automated or human) | health check / sync status | readiness gate | `Check Preconditions` / `Manual Judgment` |
| **Depends-on** | Component B must not deploy until component A passes its gate in the same stage | sync wave ordering | `HelmRelease.spec.dependsOn` | `Pipeline` sub-stage + wait |
| **Release manifest** | A file recording the pinned version of every component for this release | `Application` image tag | image policy marker | `Release` artifact |

### Multi-service deploy ordering — ArgoCD sync waves

ArgoCD's native inter-child ordering mechanism is the `argocd.argoproj.io/sync-wave`
annotation. Sync waves are integer values — lower numbers sync first; wave N+1 starts only
after all resources in wave N are healthy. This maps directly onto `depends_on` in the
fleet manifest's `deploy_sequence` field: a component with `depends_on: [auth-service]`
is assigned a higher sync wave than `auth-service`. The fleet manifest declares the intent;
the adopter's orchestrator translates it to tool-specific primitives (sync waves for ArgoCD,
`dependsOn` for Flux, `Pipeline` sub-stages for Spinnaker, `needs:` for GitHub Actions).

### Cross-repo dispatch limitations

GitHub Actions' `repository_dispatch` (API-triggered, `GITHUB_TOKEN` cannot fire it — a
PAT or GitHub App token is required) does not provide a native "wait for remote workflow"
primitive. Teams implement it via polling. This is widely used but not stable for
high-stakes release pipelines at scale. The doctrine does not prescribe `repository_dispatch`
as the triggering mechanism — the fleet manifest PR merge, a registry event webhook, or
a scheduled reconciliation loop are all valid signals. The dispatch implementation is
adopter toolchain.

---

## The fleet manifest schema (D1 elaboration)

The `release-fleet.yaml` file is committed to the e2e host repo by the release coordinator
(a bot PR from each component repo's CI bumping its entry, or a human-authored fleet
cut). It is read-only from merge time onward. Mandatory fields:

```yaml
schema_version: "1.0"           # semver; outer loop reads this first
fleet_name: <string>             # e.g. "billing-platform"
assembled_at: <RFC3339>          # timestamp of fleet assembly

components:                      # one entry per deployable component
  - name: <string>               # e.g. "auth-service"
    repo: <org/repo>             # harness-neutral identifier; adopter fills in the URL
    g4_package_ref: <path or URL> # path to the component's release-handoff.yaml in the
                                  # component repo at the pinned commit
    image_ref: "<registry>/<repo>:<tag>@sha256:<hex>"  # combined form; must match
                                                         # g4_package's component_manifest

deploy_sequence:                 # optional; defaults to parallel if absent
  - component: auth-service
    depends_on: []               # no dependency; deploys first
    gate: auto
  - component: billing-api
    depends_on: [auth-service]   # waits for auth-service's gate to pass
    gate: auto
  - component: web-frontend
    depends_on: [billing-api]
    gate: manual                 # explicit human gate before this component advances

e2e_suite_ref:                   # reference to the e2e test suite in this host repo
  path: tests/e2e/               # relative path in the host repo
  runner: <string>               # hint: "playwright" | "cypress" | "k6" | "karate"
```

**Schema compatibility:** the outer loop reads `schema_version` first. An unknown version
surfaces to the human; the tolerant reader rule (unknown fields ignored) applies. Adopters
may extend the schema with additional fields.

**Courier snapshot discipline:** each `g4_package_ref` is a version-pinned, read-only
reference to the component's authority (its G4 package). The fleet manifest is the courier
snapshot — it records the assembly for audit purposes. Neither the fleet manifest nor the
host repo forks the component's G4 package; the package remains the component repo's
authority.

---

## The e2e host repo specification (D2 elaboration)

**Must contain:**
- `release-fleet.yaml` (the fleet manifest — this is the outer loop's entry point).
- A composition file (`docker-compose.yaml`, Helm umbrella chart, or Kustomize overlay)
  that reads image references from the fleet manifest and composes the deployed fleet
  locally or against a cluster.
- An e2e test suite that treats the composed system as a black box — every test assertion
  goes through service APIs or UI surfaces, never through internal component APIs.
- CI configuration that triggers the outer loop on fleet manifest merge or
  `repository_dispatch` / registry-event webhook.

**Must NOT contain:**
- Component application source code (any component source).
- Per-component unit or integration tests (those belong in the component repo's inner loop).
- Credentials or secrets in source (all secrets are broker-mediated per AC10(g)).

**Must install:** `core` + `release-engineering` at repo scope — the same precondition
as any component repo that runs the outer loop (AC9). This is what makes the reuse of
`quality-engineer` and `security-reviewer` sound in the host repo.

**Triggering convention (harness-neutral):** the fleet manifest is updated by one of:
(a) a bot PR from each component repo's CI (opens a PR bumping `components[N].image_ref`
to the new digest), merged by the adopter's merge policy; or (b) a scheduled
reconciliation loop that queries each component registry for the latest passing-gate
version and assembles a new fleet manifest. Option (a) is the more common pattern; option
(b) is appropriate when components release continuously. The trigger implementation is
adopter toolchain.

---

## The collect-then-validate pre-deploy step (D5 elaboration)

In the polyrepo outer loop, the standard four deploy phases (infra-apply → service-deploy →
smoke → canary from RFC-0072 D2) are preceded by a **collect phase**:

```
Collect phase (before infra-apply):
  for each component in fleet_manifest.components:
    1. Read the component's g4_package_ref and fetch its release-handoff.yaml.
    2. Run RFC-0072 D6 provenance verification against the component's image_ref.
    3. Confirm the image_ref in the fleet manifest matches the image_ref in the
       component's G4 package (the fleet manifest's courier snapshot must be
       consistent with the current registry state).
    4. If any component fails steps 1–3: surface to human with the specific mismatch;
       do not proceed to infra-apply.
  On all-pass: advance to infra-apply with the verified fleet.
```

The collect phase is the fleet-level equivalent of the per-artifact provenance check from
RFC-0072 D6. In the single-component case the collect phase is a no-op (one component in
the fleet manifest; equivalent to the standard G4 validation). In the multi-component case
it ensures that all component versions in the fleet are jointly provenance-verified before
any deploy begins.

---

## The monorepo case

In a single-product monorepo the build repo *is* the integrated whole, so there is no e2e
host repo and no fleet manifest — the single-component G4 package (RFC-0072 D1) is
sufficient. The collect phase is a no-op (one component). The monorepo case is the
minimum; the polyrepo fleet manifest is the generalization. Adopters start with the
minimum and adopt the fleet manifest only when they have multiple component repos that
must deploy jointly.

---

## Drawbacks

- **Fleet manifest version bumps require coordination.** When a component changes its G4
  package schema (RFC-0072 D1 schema), the fleet manifest's `g4_package_ref` entries may
  need updating. Mitigated by the tolerant reader pattern (unknown G4 package fields
  ignored) and the `schema_version` field enabling soft migration.
- **Bot PR approach creates merge queue pressure.** If many components release frequently,
  the bot PR approach generates a high volume of PRs against the host repo. Mitigated by
  batching fleet manifest bumps (one PR per release window) or adopting the scheduled
  reconciliation approach (option b in the triggering convention).
- **No native cross-repo ordering in some orchestrators.** GitHub Actions `repository_dispatch`
  has no native "wait for remote workflow" primitive. Teams polling for completion introduce
  latency and fragility. Mitigated by the doctrine not prescribing `repository_dispatch` as
  the triggering mechanism — registry-event webhooks or the fleet manifest PR merge are
  more reliable signals.
- **The collect phase adds latency.** Verifying provenance for N components before
  any deploy begins adds clock time. Mitigated by the fact that each per-component check
  is a registry API call (seconds, not minutes) and that the alternative — deploying
  unverified components — violates AC10(g) supply-chain integrity.
- **ADR-0022 vs. RFC-0075 confusion risk.** ADR-0022 covers the product-engineering
  cross-component layer; this RFC covers the release-loop's cross-repo coordination.
  The two are parallel, not redundant, but adopters may conflate them. Mitigated by
  naming the distinction explicitly in the skill section and in the AC9 cross-reference.

## Follow-on artifacts

On acceptance:
- **Skill update:** `packs/release-engineering/.apm/skills/release-loop/SKILL.md` — new
  Polyrepo topology section per D1–D5 as described in the Reviewer brief. The section
  includes the fleet manifest schema, the e2e host repo definition, the deploy sequencing
  vocabulary table, and the collect phase specification.
- **Spec update:** `docs/specs/release-loop/spec.md` — cross-reference note on AC9
  pointing to this RFC as the source of the value-stream cross-repo mechanism.
- **Pack version bump:** `packs/release-engineering/pack.toml` +
  `.claude-plugin/plugin.json` — patch version bump.
- **Changelog:** `docs/product/changelog.md` — `[Unreleased]` entry.
- **Future:** When the operate/incident loop ships, the fleet manifest should carry an
  `on_call_owner` field per component — the incident loop's equivalent of the
  release-readiness record's operational-safety verdicts. Noting the hook point here so
  the fleet manifest schema is designed with that extension in mind.
