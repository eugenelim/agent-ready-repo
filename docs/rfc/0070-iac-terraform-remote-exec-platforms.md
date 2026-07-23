# RFC-0070: Remote execution platforms for `iac-terraform`

<!-- Written for a cold reader who has not read RFC-0065. Coined terms are
glossed on first use inline. -->

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-23
- **Date closed:** 2026-07-23
- **Decision weight:** standard <!-- credential guidance crosses a security-adjacent
  boundary, but the credentials themselves are never generated or stored by the
  pack — it only documents what the adopter must set. The spike (OQ1) is deferred
  with a documented justification. `heavy` was considered and declined: the change
  is reversible (platform = none default), no frozen ADR is reversed, and no
  long-lived secret is generated. -->
- **Related:** [RFC-0065](0065-iac-terraform-pack.md) (the `iac-terraform` pack —
  the accepted RFC that introduced the pack and explicitly deferred remote
  execution platform support as a follow-on in §8)

---

## Reviewer brief

- **Decision:** Extend the `iac-terraform` pack (an opt-in Terraform/OpenTofu
  code-generation pack — "the pack") to support HCP Terraform and Scalr as
  remote execution backends alongside the existing cloud-native state backends.
- **Recommended outcome:** Accept — all five decisions below were confirmed
  by the author in the same session.
- **Change if accepted:**
  - New `references/remote-exec/` directory with two platform references
    (`hcp-terraform.md`, `scalr.md`) — each covers config block, auth, dynamic
    credential guidance, bootstrap, and CI trigger notes.
  - `generate-iac` skill gains a new `remote_exec_platform` clarify input
    (`none | hcp-terraform | scalr`); `hcp-terraform` is blocked when
    `engine = opentofu`.
  - `generate-iac` emits a `REMOTE_EXEC_SETUP.md` for remote-exec targets,
    leading with dynamic provider credentials / OIDC federation as the preferred
    credential model.
  - `reconcile-iac` gains backend-type detection and flags legacy
    `backend "remote" { hostname = "app.terraform.io" }` for migration.
- **Affected surface:** `packs/iac-terraform` only — skill files and new
  reference files. No change to `core`, `governance-extras`, or any other pack.
  (`core` and `governance-extras` are the two packs `iac-terraform` depends on;
  naming them confirms they are out of scope.)
- **Stakes:** Reversible — `platform = none` is the default; adopters not on
  these platforms are unaffected.
- **Review focus:** Credential guidance model (§3) — leads with dynamic
  credentials / OIDC federation, not static keys.
- **Not in scope:** Atlantis, Spacelift, env0, Terrateam; autonomous apply;
  direct API scripting; multi-workspace fan-out.

---

## The ask

**Recommendation (BLUF — Bottom Line Up Front):** Add `hcp-terraform` and
`scalr` as first-class remote execution platform options to `generate-iac` and
`reconcile-iac`. The change is additive — `platform = none` (vanilla CI with
cloud-native state backend) remains the default and is unchanged.

**Why now (SCQA — Situation / Complication / Question / Answer):** The pack
generates Terraform/OpenTofu with cloud-native state backends (S3, GCS, Azure
Blob) and vanilla CI pipelines. Many adopter organisations run **HCP Terraform**
(HashiCorp's managed remote-execution SaaS, formerly Terraform Cloud) or
**Scalr** (a compatible open-alternative SaaS with a hierarchical policy model)
as their execution platform. Without pack support, adopters on these platforms
either generate the wrong backend config or manually patch the output — neither
is safe. RFC-0065 §8 explicitly called this out as a planned follow-on. The
design decisions have now been researched and confirmed.

**Decisions requested — all confirmed by Approver in the authoring session:**

| ID | Question | Decision | Rationale |
| -- | -------- | --------- | --------- |
| D1 | RFC form — new RFC or errata on RFC-0065? | New RFC-0070 + Errata entry on RFC-0065 §8 | Errata = corrections to a frozen RFC; this is a new feature. RFC-0065 §8 anticipated it as a follow-on. |
| D2 | Reference structure — 2 files in `references/remote-exec/` (config+CI+bootstrap combined) vs 4 files split across `remote-exec/` + `pipeline/`? | 2 files in `references/remote-exec/` | Platform IS the execution layer; the CI trigger is a thin delta, not a full pipeline. Mirrors `providers/` pattern (one file per target, loaded conditionally). |
| D3 | Credential guidance — generated `REMOTE_EXEC_SETUP.md` vs inline comments? | Generated `REMOTE_EXEC_SETUP.md` | Mirrors `backend.hcl.example` precedent (a file generated alongside `backend.tf` for vanilla CI); credentials-not-forwarded is the top foot-gun for remote exec. |
| D4 | Bootstrap narrative — inline in each platform reference vs new `bootstrap-sequence.md` section? | Inline in each platform reference | Remote-exec bootstrap differs per platform and is short (≤5 steps); `bootstrap-sequence.md` stays scoped to the object-store case. |
| D5 | `reconcile-iac` scope — detect backend type and flag legacy TFC config for migration? | In scope | One detection case; excluding it means a follow-on RFC for a 5-line addition. |

---

## Problem & goals

### Problem

The pack generates a `backend.tf` that always points to a cloud-native object
store (S3, GCS, Azure Blob). When an adopter's organisation uses HCP Terraform
or Scalr as its execution platform:

1. The generated backend config is wrong — neither platform uses an object-store
   backend block.
2. The correct config form differs between platforms: HCP Terraform uses a
   `cloud {}` block (Terraform ≥ 1.1); Scalr uses a `backend "remote"` block
   with `hostname = "<account>.scalr.io"`.
3. **Credentials for the cloud provider (AWS, GCP, etc.) must be set as workspace
   environment variables inside the platform — they are not forwarded from the
   local or CI runner environment.** This is the most common foot-gun.
4. HCP Terraform's `cloud {}` block is incompatible with OpenTofu (the alternative
   open-source Terraform fork); Scalr's `backend "remote"` is compatible with both
   engines. Without an enforced gate, an adopter can generate an HCP Terraform
   config for an OpenTofu target and discover the incompatibility only at
   `terraform init`.

### Goals

- Extend `generate-iac` with a `remote_exec_platform` clarify input
  (`none | hcp-terraform | scalr`), defaulting to `none`.
- When `platform = hcp-terraform`, emit a `cloud {}` block and enforce that
  `engine` must be `terraform` (not `opentofu`).
- When `platform = scalr`, emit a `backend "remote"` block and surface the
  `organization` = environment-name trap (see Proposal §1).
- For both platforms, emit a `REMOTE_EXEC_SETUP.md` that leads with dynamic
  provider credentials / OIDC federation (the preferred model) and names static
  workspace variables only as a fallback.
- Extend `reconcile-iac` to detect the backend type and flag legacy
  `backend "remote" { hostname = "app.terraform.io" }` for migration to
  `cloud {}`.

### Non-goals

- **Atlantis, Spacelift, env0, Terrateam** — deferred. RFC-0065 §8 deferred
  commercial platform configs generically; this RFC delivers the HCP Terraform
  and Scalr portion. GitOps platforms (Atlantis emits `atlantis.yaml`, not a
  `backend.tf`) warrant their own RFC.
- **API-driven run scripting** — the pack generates Terraform HCL; the
  `terraform` / `tofu` CLI handles platform API calls transparently when the
  correct block is present.
- **Multi-workspace fan-out** — one `generate-iac` invocation targets one
  workspace. Fan-out is a `release-loop` concern. (`release-loop` is a separate
  pack that orchestrates deploy → converge cycles; it is not modified by this RFC.)
- **Autonomous apply** — unchanged; the G4 handoff (the fourth gate in the
  project's loop arc, a digest-pinned `terraform plan`) and human-gated apply
  are pack invariants regardless of platform.
- **Platform workspace creation** — the pack documents what to configure in an
  existing workspace; it does not provision the workspace via the `hashicorp/tfe`
  or `scalr/scalr` Terraform providers.

---

## Proposal

### 1. New reference directory: `references/remote-exec/`

Two new files under
`packs/iac-terraform/.apm/skills/generate-iac/references/remote-exec/`.
(`.apm/` is the skills directory consumed by the agent bundle installer; all
pack skill content lives under it.)

Each file is a **progressive reference** — `generate-iac` loads it on demand
during the PLAN stage when the platform is selected; adopters who choose
`platform = none` never see it.

**`hcp-terraform.md`** covers:

- **Config block** — the `cloud {}` block (all fields + env-var overrides):
  - `TF_TOKEN_app_terraform_io` — the API token for `app.terraform.io`
    (replaces interactive `terraform login`)
  - `TF_CLOUD_ORGANIZATION` — org name, overrides `cloud.organization`
  - `TF_CLOUD_HOSTNAME` — for Terraform Enterprise (self-hosted HCP); defaults
    to `app.terraform.io`
  - `TF_WORKSPACE`, `TF_CLOUD_PROJECT` — workspace and project name overrides
- **Token-type scoping guard** — organisation tokens cannot trigger runs or create
  configuration versions; team or user token required. Generates a named warning
  in `REMOTE_EXEC_SETUP.md`.
- **Dynamic Provider Credentials** — HCP Terraform's OIDC (OpenID Connect —
  identity federation) integration with cloud providers; lets the remote runner
  exchange a short-lived JWT for cloud credentials without any static key. This
  is the preferred credential model (aligns with the pack's no-long-lived-keys
  invariant). Named alongside the workspace-variable fallback.
- **Remote operations model** — local env vars not forwarded; the static-key
  fallback requires workspace environment variables set inside HCP Terraform.
- **Run states** — `needs_confirmation` and `policy_override` require agent or
  human action; documented so adopters know to handle them.
- **Policy enforcement** — OPA (Open Policy Agent, the pack's mandated open-source
  policy tool, used via Conftest) is separate from HCP Terraform's native policy
  evaluation. Both can coexist: Conftest runs in the CI pipeline before the
  remote run; HCP Terraform can also run OPA natively (paid tier). Sentinel
  (HCP Terraform's proprietary policy language) is Terraform + paid-tier only
  and must NOT be emitted by this pack.
- **CI trigger notes** — when `cloud {}` is present, `terraform plan` run in CI
  proxies to HCP Terraform; CI emits no OIDC to a state backend (state lives in
  the platform). Cloud-provider OIDC trust policy is still required if Dynamic
  Provider Credentials is not configured. The remote-exec reference provides the
  *platform delta* only; it composes with the existing
  `references/pipeline/<ci>.md` which remains the source of truth for the
  CI pipeline structure.
- **Bootstrap narrative** — create workspace → configure Dynamic Provider
  Credentials (or set workspace variables as fallback) → run `terraform init` →
  first plan runs remotely.

**`scalr.md`** covers:

- **Config block** — `backend "remote"` block:
  ```hcl
  terraform {
    backend "remote" {
      hostname     = "<account-name>.scalr.io"
      organization = "<environment-name>"   # NOTE: not the account name
      workspaces { name = "<workspace-name>" }
    }
  }
  ```
  Critical naming trap: the `organization` field takes the **Scalr environment
  name** (not the account name). The account name is encoded in `hostname`. This
  is the most common misconfiguration when porting TFC configs to Scalr.
- **Auth** — `TF_TOKEN_<account-name>_scalr_io` (dots → underscores, same
  `TF_TOKEN_*` pattern as HCP Terraform). Service-account or personal token; no
  equivalent of HCP Terraform's organisation-token restriction.
- **Provider integrations** (preferred credential model) — Scalr's native
  cloud-provider credential management injects credentials at run time via OIDC
  federation, without workspace environment variables. This is the preferred
  model; workspace env vars are the fallback for organisations that have not yet
  configured provider integrations.
- **Three-tier hierarchy** — **account** (top-level; manages RBAC — Role-Based
  Access Control — and OPA policies) → **environment** (team-level grouping,
  e.g. `production` / `dev`) → **workspace** (execution unit). Variables, OPA
  policies, and credentials cascade downward; any level can mark a value `final`
  to prevent override by lower scopes. This hierarchical governance model is a
  structural differentiator from HCP Terraform's flat org/workspace model.
- **OpenTofu compatibility** — `backend "remote"` is a standard Terraform backend
  protocol, not a HashiCorp proprietary extension; Scalr is the recommended
  remote execution option when `engine = opentofu`.
- **OPA policy enforcement** — pre-plan and post-plan; Sentinel is not supported
  by Scalr.
- **CI trigger notes** — same pattern as HCP Terraform; the platform delta
  composes with `references/pipeline/<ci>.md`.
- **Bootstrap narrative** — create account → create environment → create workspace
  → configure provider integrations (or set env-level variables as fallback) →
  run `terraform init`.

### 2. `generate-iac` skill changes

**Background:** `generate-iac` is the pack's authoring skill. It runs in stages:
ADR gate → SPECIFY → CLARIFY (collect inputs) → PLAN (load references, draft
layout) → WRITE TF (emit HCL files) → VERIFY (fmt/validate/plan/policy) → G4
handoff. An **ADR** (Architecture Decision Record) is a short document recording
a team's infrastructure decision; the pack gates generation on these to ensure
every Terraform config has a governance record.

**CLARIFY stage — new input row:**

| Input | Default | Note |
| ----- | ------- | ---- |
| Remote execution platform | `none` | `none \| hcp-terraform \| scalr`. If `engine = opentofu`, only `none` and `scalr` are valid — `hcp-terraform` requires the `cloud {}` block, which is Terraform-only. |

The `engine` input already exists in the CLARIFY table (Terraform or OpenTofu).
The constraint is enforced: if `engine = opentofu` and `platform = hcp-terraform`
is requested, the skill surfaces the incompatibility and re-asks.

**PLAN stage:** when `platform ≠ none`, load
`references/remote-exec/<platform>.md` alongside `references/providers/<cloud>.md`
and `references/pipeline/<ci>.md`.

**WRITE TF stage — backend generation branching:**

| Platform | Generated files |
| -------- | --------------- |
| `none` (default) | `backend.tf` with cloud-native backend + `backend.hcl.example` (a template for per-environment backend values, populated by the adopter at `terraform init`) |
| `hcp-terraform` | `versions.tf` with `cloud {}` block; no `backend.hcl.example` (unused); no `backend.tf` |
| `scalr` | `backend.tf` with `backend "remote"` block; `hostname = "<account>.scalr.io"`; `organization = "<env-name>"`; no `backend.hcl.example` |

**WRITE OUTPUT stage:** when `platform ≠ none`, emit `REMOTE_EXEC_SETUP.md`
(§3 below).

**Hard rules to add to the never-emit list** (the existing list of patterns the
skill must not generate under any circumstance):
- Never emit `backend "remote"` pointing to `app.terraform.io` (deprecated TFC
  form; generate `cloud {}` for HCP Terraform targets instead).
- Never emit an HCP Terraform config for an `engine = opentofu` target.
- Never emit Sentinel policy guidance (already banned; reinforce with a
  remote-exec callout — Sentinel is Terraform + HCP paid tier only).

### 3. Generated `REMOTE_EXEC_SETUP.md`

Emitted into the project root when `platform ≠ none`. Six sections, leading
with the dynamic / OIDC-federated credential model to align with the pack's
no-long-lived-keys invariant:

1. **Platform auth token** — how to set `TF_TOKEN_app_terraform_io` (HCP
   Terraform) or `TF_TOKEN_<account>_scalr_io` (Scalr) so `terraform login` is
   not needed in CI.
2. **Dynamic provider credentials (preferred)** — for HCP Terraform: Dynamic
   Provider Credentials (OIDC trust between HCP Terraform and the cloud provider;
   no static keys). For Scalr: provider integrations (equivalent OIDC mechanism).
   Named with setup links. This is the model that satisfies the pack's invariant.
3. **Static workspace variables (fallback)** — named list of the workspace
   environment variables to set in the platform for the target cloud if dynamic
   credentials are not yet configured (e.g. AWS: `AWS_ACCESS_KEY_ID` +
   `AWS_SECRET_ACCESS_KEY`; GCP: `GOOGLE_CREDENTIALS`). Labelled as a fallback
   and marked for migration to dynamic credentials.
4. **Platform-specific traps** — HCP Terraform: organisation tokens cannot
   trigger runs (use team/user token). Scalr: `organization` field = Scalr
   environment name, not account name; `final` flag prevents workspace-level
   override of environment/account-scoped values.
5. **Variable inheritance (Scalr only)** — account → environment → workspace
   cascade; prefer setting shared credentials at environment level so all
   workspaces in the environment inherit them.
6. **OpenTofu note** — `hcp-terraform` is not available for OpenTofu targets;
   Scalr's `backend "remote"` is compatible with both `terraform` and `opentofu`.

### 4. `reconcile-iac` skill additions

`reconcile-iac` is the pack's drift-audit skill. It runs `terraform plan
-detailed-exitcode` and audits the result. A **backend-type detection step** is
added to its pre-audit preamble (the initial read of the project before running
`plan`):

1. Inspect `versions.tf` for a `cloud {}` block → platform = `hcp-terraform`.
2. Inspect `backend.tf` for `backend "remote"` → inspect `hostname`:
   - `app.terraform.io` → legacy TFC config; flag for migration to `cloud {}`
     and surface a migration note.
   - `*.scalr.io` → platform = `scalr`.
   - Anything else → unknown remote backend; note in report.
3. No `cloud {}` and no `backend "remote"` → platform = `none`.

The platform type is recorded in the audit report header. For remote-exec
platforms, a note is added: "plan runs remotely on `<platform>`; resources
created entirely outside Terraform are invisible to `plan` — the blind-spot
caveat applies as with local execution."

**Cross-reference:** `references/providers/hashicorp-platform.md` documents the
`hashicorp/hcp` Terraform provider for provisioning HCP resources (Vault, Consul,
HCP Terraform workspaces) as infrastructure. That is distinct from this RFC's
concern, which is using HCP Terraform as the *execution backend* for the
`iac-terraform` pack itself. The two files serve different purposes and should
not be conflated.

---

## Options considered

### D2: Reference file structure (axis: granularity of new files)

| Option | Files | Trade-off |
| ------ | ----- | --------- |
| **`references/remote-exec/<platform>.md` (confirmed)** | 2 new | Mirrors `providers/` pattern. Platform IS the execution layer; CI trigger is a thin platform delta, not a full pipeline. |
| Split: `remote-exec/` (config) + `pipeline/` (CI trigger) | 4 new | Splits a tight concern; the CI trigger for remote-exec is too thin to warrant a separate reference file per platform. |
| Conditional sections in existing `pipeline/github-actions.md` etc. | 0 new | Wrong categorisation — platform is orthogonal to CI trigger system. |
| Do nothing | 0 | Adopters generate wrong configs; RFC-0065 §8 already deferred this once. |

### D3: Credential guidance form (axis: discoverability vs. file count)

| Option | Form | Trade-off |
| ------ | ---- | --------- |
| **`REMOTE_EXEC_SETUP.md` (confirmed)** | 1 generated file | Mirrors `backend.hcl.example` precedent; table-formatted, shows up in directory listing. |
| Inline comments in `versions.tf` / `backend.tf` | 0 new files | Too truncated for structured variable lists. |
| No guidance | 0 | Credentials-not-forwarded is the top foot-gun; omitting it is a known-bad outcome. |

### D4: Bootstrap narrative location (axis: cohesion vs. file count)

| Option | Where | Trade-off |
| ------ | ----- | --------- |
| **Inline in each `references/remote-exec/<platform>.md` (confirmed)** | Platform reference | Platform-specific, short (≤5 steps); keeps `bootstrap-sequence.md` scoped to the object-store case. |
| New section in `bootstrap-sequence.md` | Existing file | Conflates the object-store bootstrap with the SaaS platform bootstrap. |
| New `references/remote-exec/bootstrap.md` | 1 new file | Overengineered for ≤10 lines per platform. |

### D5: `reconcile-iac` scope (axis: include vs. defer)

| Option | Trade-off |
| ------ | --------- |
| **In scope (confirmed)** | One detection case (grep + hostname check); excluding it means a follow-on RFC for a 5-line addition. |
| Out of scope / follow-on RFC | Cleaner scope boundary; smaller RFC; the migration nudge is low-urgency. |
| Do nothing | Legacy TFC adopters get no migration nudge; silent misconfiguration persists. |

---

## Risks & what would make this wrong

**Pre-mortem:**

1. **Scalr `cloud {}` support ships.** If Scalr adds `cloud {}` support, the
   `backend "remote"` recommendation becomes a legacy path. *Mitigation:*
   reference files are versioned; a future pack bump can update `scalr.md`
   without changing the RFC.
2. **HCP Terraform token scoping changes.** If HashiCorp adds run-triggering
   capability to organisation tokens, the org-token warning becomes stale.
   *Mitigation:* low probability (architectural restriction); the staleness CI
   job (a weekly scheduled GitHub Actions workflow that re-runs `terraform
   validate` on the pack's worked examples against the latest provider release)
   already re-validates provider contracts.
3. **Scalr `organization` field semantics change.** If Scalr renames environments
   to organisations, the named trap becomes confusing. *Mitigation:* `reconcile-iac`
   would surface the misconfiguration.
4. **Dynamic Provider Credentials / provider integrations not yet available to all
   adopters.** If an adopter's HCP Terraform or Scalr plan tier doesn't support
   dynamic credentials, they must fall back to static workspace vars — exactly
   what §3 documents. *Mitigation:* the fallback path is present; the preferred
   path is clearly marked as preferred, not mandatory.

**Key assumptions (falsifiable):**

- Scalr does not support the `cloud {}` block — only `backend "remote"`. *Evidence:*
  Scalr documentation uses `backend "remote"` exclusively; no `cloud {}` examples
  found. ([docs.scalr.io/docs/cli](https://docs.scalr.io/docs/cli))
- `backend "remote"` works with OpenTofu. *Evidence:* `opentofu-differences.md`
  lists only `cloud {}` blocks (not `backend "remote"`) as Terraform-only;
  OpenTofu's compatibility documentation confirms standard backends are supported.
  ([Scalr introduction](https://docs.scalr.io/docs/introduction) confirms OpenTofu
  support.)

**Drawbacks:**

- Adds a new CLARIFY input — adopters who don't use remote execution platforms
  see one more question; the default (`none`) means zero friction unless they
  read the options.
- `REMOTE_EXEC_SETUP.md` requires manual action from the adopter; the pack
  cannot automate credential injection.

---

## Evidence & prior art

**Spike / de-risk result:** Both key assumptions verified against live
documentation. A live-account Scalr spike is retained as OQ1 with a documented
justification for proceeding without it.

**Repo precedent:**
- RFC-0065 §8 — defers "commercial platform configs" as a planned follow-on.
- `references/opentofu-differences.md` line 75 — "HCP Terraform cloud blocks —
  OpenTofu uses standard backends" — the `cloud {}` incompatibility is already
  documented; this RFC enforces it as a CLARIFY gate.
- `references/terraform-standard.md` lines 38–48 — private module registry
  (`app.terraform.io/<org>/…`) — the only existing TFC reference in generated
  output; orthogonal to this RFC's backend-and-execution concern.
- `references/providers/hashicorp-platform.md` — documents the `hashicorp/hcp`
  provider for provisioning HCP resources. Orthogonal to this RFC; see §4
  cross-reference note.

**External prior art (citations fetched and confirmed):**
- [HCP Terraform `cloud {}` block settings](https://developer.hashicorp.com/terraform/cli/cloud/settings) — `cloud {}` current since Terraform 1.1; `backend "remote"` deprecated.
- [HCP Terraform API token types](https://developer.hashicorp.com/terraform/cloud-docs/users-teams-organizations/api-tokens) — organisation tokens cannot start runs.
- [HCP Terraform remote operations](https://developer.hashicorp.com/terraform/cloud-docs/workspaces/run/remote-operations) — local env vars not forwarded.
- [Scalr CLI workspace docs](https://docs.scalr.io/docs/cli) — `backend "remote"` with Scalr hostname; `organization` = environment name.
- [Scalr introduction](https://docs.scalr.io/docs/introduction) — confirms OpenTofu support.
- [Scalr OPA policy enforcement](https://scalr.com/learning-center/policy-enforcement-for-terraform-opentofu-with-opa-and-scalr/) — OPA only; no Sentinel.

---

## Open questions

1. **Live-account spike for Scalr.** Both the `backend "remote"` form and the
   `organization` = environment-name mapping were verified from documentation, not
   a live account. *Recommended default:* proceed without; a wrong backend block
   produces a clear `terraform init` error rather than silent misbehaviour.
   · owner: eugenelim · decide-by: before merging `scalr.md`.

2. **HCP Terraform Dynamic Provider Credentials tier availability.** Dynamic
   Provider Credentials may require a paid HCP Terraform plan. *Recommended
   default:* document in `hcp-terraform.md` that it requires HCP Terraform Plus
   or higher; workspace env vars are the free-tier fallback. Confirm against the
   current [HCP Terraform pricing page](https://developer.hashicorp.com/terraform/cloud-docs/overview) before merging.
   · owner: eugenelim · decide-by: before merging `hcp-terraform.md`.

3. **Scalr provider integrations scope.** Scalr's provider integrations (preferred
   dynamic credential model) may not be available for all cloud providers on all
   plan tiers. *Recommended default:* document the supported providers and tiers
   in `scalr.md`; fall back to workspace env vars for unsupported combinations.
   Confirm against the current [Scalr provider integrations docs](https://docs.scalr.io) before merging.
   · owner: eugenelim · decide-by: before merging `scalr.md`.

---

## Follow-on artifacts

- **ADR:** Record the remote-exec platform support decision (engine/platform gate,
  reference structure, `REMOTE_EXEC_SETUP.md` convention).
- **Implementation:** `packs/iac-terraform` changes per Proposal above.
- **Errata on RFC-0065:** One-line entry pointing to RFC-0070 (already added in
  the same PR as this RFC).
