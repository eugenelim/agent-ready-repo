# IaC ADR topics (infra mode)

> **Load this when `new-adr` is invoked with `mode: infra` or when the user
> asks for an infrastructure-specific ADR.** These seven topics correspond to
> the `generate-iac` governance-index domains. Each topic produces one ADR.

For each topic below:
1. Invoke `new-adr` normally — the topic description is the framing question.
2. Title the ADR declaratively: name the decision, not the domain.
   ("State backend: S3 with native lockfile" not "State backend decision")
3. After accepting, reference the ADR number in the governance-index manifest
   (`docs/governance-index.yaml`, domain row `adrs: [ADR-NNNN]`).

## The seven IaC ADR topics

### 1. State backend and locking (`state`)

**Framing question:** Where does Terraform state live, which remote backend
is used, and how is concurrent access locked?

Decision content to capture:
- Backend service choice (S3, GCS, AzureRM, etc.) and why
- Locking mechanism (native S3 lockfile `use_lockfile = true`, GCS metadata
  locks, AzureRM blob lease)
- Encryption at rest (KMS key, CMEK, CMK — document the key ID strategy)
- Per-environment state isolation (separate bucket vs shared with key prefix)
- `Revisit if:` S3 DynamoDB locking is re-instated upstream, or a new backend
  type is standardized for the cloud

---

### 2. Layered layout (`layout`)

**Framing question:** How is Terraform organized into layers, stacks, and
modules? Which units deploy independently?

Decision content to capture:
- Layer structure (bootstrap → foundation → platform → app or custom)
- Whether modules are sourced from the public registry or are local
- Version pinning policy for registry modules (exact tag/commit, never floating)
- How layers reference each other (remote state, hard-coded outputs, input vars)
- `Revisit if:` the number of managed resources exceeds ~200 per state file,
  or a new platform team takes over a layer

---

### 3. Identity and access model (`iam`)

**Framing question:** What IAM identity model applies — federated workload
identity, service account keys, or managed identities?

Decision content to capture:
- Workload identity primitive (OIDC via GitHub/ADO/GitLab, Direct WIF on GCP,
  Federated Identity Credentials on Azure)
- Static credential policy (prohibited in CI, prohibited in checked-in config)
- Least-privilege scoping: what actions each identity can perform, and the
  mechanism that enforces it (SCPs, IAM Conditions, Azure RBAC)
- Per-environment role separation: ephemeral CI role must not assume prod role
- `Revisit if:` the identity provider changes, or a compliance requirement
  mandates a different attestation model

---

### 4. Tagging and labeling (`tagging`)

**Framing question:** Which resource tags/labels are mandatory, and how are
they enforced?

Decision content to capture:
- Mandatory key set (at minimum: `environment`, `owner`, `cost-center`,
  `managed-by`, `system`, `data-classification`)
- Enforcement mechanism (AWS `default_tags`, OPA/Conftest policy, Azure Policy,
  GCP Organization Policy)
- Cloud-specific constraints (GCP lowercase-only label values, Azure 512/256
  char limits)
- `Revisit if:` the FinOps team changes the cost-attribution key set, or a new
  cloud with different label constraints is added

---

### 5. Network topology (`networking`)

**Framing question:** Is the workload deployed in a public or private network?
Who owns the VPC/VNet, and what are the ingress and egress controls?

Decision content to capture:
- VPC/VNet ownership (team-owned vs platform-provided)
- Public vs private subnet allocation
- Ingress path (ALB, API Gateway, Front Door, Cloud Armor)
- Private service access mechanism (VPC endpoints, Private Service Connect,
  Private Link)
- Cross-environment network isolation
- `Revisit if:` the platform team centralizes network management, or a zero-trust
  overlay replaces the perimeter model

---

### 6. CI pipeline authentication (`pipeline_auth`)

**Framing question:** How does the CI pipeline authenticate to the cloud
provider to run `terraform plan` and `terraform apply`?

Decision content to capture:
- Auth mechanism (OIDC via GitHub Actions / ADO / GitLab — preferred; AppRole;
  service account key as last resort)
- OIDC `sub` claim format and any repo-specific constraints (GitHub 2026-07-15
  sub format change for new repos)
- Environment-separation: plan role vs apply role; ephemeral-env role vs
  prod-deploy role
- Token lifetime and rotation policy
- `Revisit if:` the CI provider changes its OIDC issuer, or the cloud provider
  deprecates the current workload identity primitive

---

### 7. Remediation and autonomous apply (`remediation`)

**Framing question:** Can the system self-heal or auto-apply Terraform changes
without human approval?

Decision content to capture:
- Human approval requirement for production apply (yes — default; document any
  exception and the scope it is limited to)
- Ephemeral-environment exception: autonomous apply is allowed on isolated
  ephemeral environments only (no shared state, no prod data, spend-bounded)
- Drift remediation policy: automatic reconcile vs alert + manual action
- `Revisit if:` a GitOps controller (Atlantis, env0, Spacelift) is adopted and
  takes over the reconcile loop
