# Agent-driven IaC / Terraform generation — applied survey

> Discipline: applied (practitioner-pattern survey)

Scope: prior art + best practice + failure modes for the pattern RFC-0065's
`iac-terraform` pack implements — an AI agent turning a plain-language intent into
governed Terraform + a human-gated pipeline. Confidence tags: `[high]` /
`[moderate]` / `[low]` / `[uncertain]`; downgrade reasons named. Practitioner
independence is calibrated per the applied overlay (same vendor / same employer /
re-blogs of one post count as one source).

---

## 1. Spec-driven development applied to infrastructure

- **The intent → spec → plan → tasks → implement loop is a named, shipped
  methodology (GitHub Spec Kit), whose stated philosophy is "code serves
  specifications" with generated artifacts treated as regenerable.** `[high]`
  Ambiguity is forced open via `[NEEDS CLARIFICATION]` markers and a
  "constitution" of standards acts as a compliance gate. (Primary: github/spec-kit
  `spec-driven.md`.) This is the exact shape the pack's `generate-iac` skill
  encodes — independent validation that the *shape* is sound.
- **Spec Kit itself is application-development-focused and does not mention IaC or
  Terraform; IaC adaptations exist but are experimental and low-adoption.**
  `[moderate]` IBM/iac-spec-kit (`/iac.specify → plan → tasks → implement`) and
  dotlabshq/spec-ops extend it to Terraform, but both are forks of the same
  template (one lineage, tens of stars, explicitly experimental). (Primary: the
  two repos; secondary: Mamezou practitioner writeup.) Downgrade: low adoption,
  single lineage, <1 year old (`stale prior art` inverse — too *new* to be proven).
- **Independent practitioner + analyst sources converge on one failure mode:
  spec/plan/constitution phase boundaries leak in practice, and infrastructure
  reality flows *backward* (specs get updated to match already-running state)
  against SDD's forward spec→code assumption.** `[moderate]` (Mamezou blog; InfoQ
  "fifth-generation" framing calling generator reliability a "supply-chain
  problem" and this "bounded autonomy"; The New Stack on infra working backward.)
  Three independent voices → meaningful. **Design implication:** the Stage-0 gate
  + mandatory record-citation must be *enforced structurally*, not assumed; and
  drift / existing-resource reconciliation is a first-class concern, not an edge
  case — which is exactly why the pack reuses `core`'s drift/state depth rather
  than re-inventing it.

## 2. Terraform best practices that matter for machine generation

All six practices the RFC names are corroborated by primary vendor docs:

- **Layered / isolated remote state per unit + environment, for blast-radius
  isolation.** `[high]` (Primary: HashiCorp standard-module-structure, AWS
  Prescriptive Guidance; secondary/independent: Gruntwork infrastructure-live,
  terraform-best-practices.com.) Gruntwork advises *against* workspaces as the
  isolation boundary — but this is **contested**: HashiCorp officially supports
  workspaces for lightweight env splitting. Treat "avoid workspaces" as a
  practitioner opinion, not settled consensus. `[moderate]`
- **Reusable modules (no provider blocks, no hardcoded env values, output
  everything) vs. root/live configs that own env + backend + auth.** `[high]` AWS
  guidance explicitly warns against thin single-resource wrapper modules — a
  known over-abstraction failure in generated code. (Primary: HashiCorp + AWS.)
- **Version pinning: `required_version`, `~>` provider constraints, pinned module
  `source` refs, and committing `.terraform.lock.hcl`.** `[high]` HashiCorp frames
  the lockfile as trust-on-first-use; commit-hash module pinning is a named
  supply-chain defense. (Primary: HashiCorp dependency-lock + version-constraint
  docs, AWS guidance.) **Especially load-bearing for agents** — an unpinned
  agent `init` can silently pull a newer or malicious provider — though note this
  agent-specific sharpening is *our inference*, not a cited vendor claim. `[moderate]`
- **Least-privilege IAM per layer; build policies bottom-up from empty; no
  god-role.** `[high]` (Primary: AWS Prescriptive Guidance security chapter;
  independent practitioner corroboration exists but several were unverified.)
- **Provider-level `default_tags` (AWS provider ≥ v3.38) as the primary tagging
  mechanism; resource tags override provider defaults; ASGs are a known
  exception.** `[high]` (Primary: HashiCorp blog + AWS guidance.) `default_tags`
  alone doesn't stop an agent omitting the provider block — hence policy
  enforcement on top.
- **State locking: native S3 lockfile (`use_lockfile = true`, GA Terraform 1.11)
  now supersedes the DynamoDB table; DynamoDB locking is deprecated.** `[high]`
  **Recency flag:** any guidance recommending DynamoDB as *the* locking mechanism
  predates Terraform 1.11 and is stale. Seeds must not hardcode DynamoDB. (Primary:
  HashiCorp S3 backend docs.)

## 3. Policy-as-code / policy-on-plan as a CI gate

- **Evaluate the machine-readable plan JSON (`terraform show -json`), not the HCL
  — because HCL values (vars, modules, dynamic blocks) aren't resolved until plan
  time.** `[high]` (Primary: HashiCorp JSON-output-format docs; OPA Terraform
  docs.) **Caveat, stated in OPA's own docs:** plan JSON has limits — unknown
  values and dynamic blocks may still be unresolved at plan time, so policies must
  tolerate absent fields. `[high]`
- **OPA/Conftest against plan JSON runs in any CI without cloud credentials;
  Checkov adds 750–1000+ built-in policies with a plan-scanning mode; the two
  layer (scanner breadth + custom org rules).** `[moderate]` (Primary: OPA docs,
  Checkov docs. Complementarity framing is practitioner-synthesis from vendors
  who sell adjacent platforms — env0, Spacelift — so somewhat commercially
  motivated; downgrade for that.) Directly supports the RFC's **mechanism-level,
  not tool-level** stance.
- **tfsec is legacy — Aqua merged it into Trivy (announced 2023-02-18); new rule
  work lands in Trivy, tfsec ships only dependency bumps.** `[high]` **Cite Trivy,
  not tfsec.** (Primary: Aqua/tfsec `#1994` discussion.)
- **HashiCorp Sentinel is a real between-plan-and-apply gate with advisory /
  soft-mandatory / hard-mandatory levels, but is paywalled — tied to HCP Terraform
  Standard/Premium; Free tier caps at one 5-policy set.** `[moderate]` (Primary:
  HashiCorp Sentinel docs.) A vendor-lock consideration vs. open OPA/Checkov.

## 4. OIDC / workload identity federation + human-gated apply

- **OIDC / workload-identity-federation is the cross-vendor consensus for CI→cloud
  auth, replacing long-lived static keys with short-lived per-run scoped tokens;
  the pattern is structurally identical across AWS (`AssumeRoleWithWebIdentity`),
  Azure (federated identity credential), and GCP (workload identity pool).**
  `[high]` Three independent cloud vendors converge → strong. (Primary: GitHub,
  AWS, Microsoft, Google docs + official actions.)
- **Recency gotcha (live, dated):** GitHub changed the OIDC `sub` claim format for
  repos created **on/after 15 July 2026** to an immutable form with numeric
  org/repo IDs; trust policies written against the legacy name-only `sub` silently
  fail `AssumeRoleWithWebIdentity` for those repos. `[high]` Given today is
  2026-07-17, seeds/docs must flag this. (Primary: GitHub docs.)
- **"Environment as the gate object" is the cross-vendor convergence for
  human-gated apply** — GitHub Environments (required reviewers, wait timer,
  prevent-self-review), GitLab protected-environments + deployment_approvals,
  Azure DevOps environment approvals/checks + ManualValidation. `[high]` (Primary:
  GitHub, GitLab, Microsoft docs.) **Licensing caveat:** GitHub Environments
  protection rules need Team/Enterprise on private repos.
- **"Plan on PR → gated apply on merge" is the recommended default but not a
  universal law** — some GitOps/preview-env models intentionally apply
  before merge and reconcile after. `[moderate]` State as default-with-exception.
  (Secondary counterpoint: Terramate.) Note HashiCorp's own automation tutorial
  leans on native PR review as the gate and is thinner on an explicit
  approval-before-apply step than the platform docs — cite the platform docs for
  that specific control. Hardening the plan/apply binding (apply *exactly* the
  reviewed plan artifact) is practitioner guidance, not emphasized by HashiCorp. `[moderate]`

## 5. Agent skills + LLM-Terraform failure modes (the load-bearing evidence)

- **AGENTS.md is a real, multi-tool open convention (now stewarded by the Linux
  Foundation's Agentic AI Foundation, 25–30+ compatible tools); Claude Code
  `SKILL.md` skills supersede legacy commands and add autonomous invocation.**
  `[moderate]` (Primary: agents.md, Anthropic SDK docs. Everything beyond the two
  primaries is a cluster of same-genre 2026 SEO comparison blogs — tertiary.) The
  **"engine is the repo, not the model"** framing is a defensible *inference* from
  these mechanics, **not a sourced principle** — no vendor/academic source names
  it. Downgrade: thin, young, unstudied efficacy.
- **Hallucinated resource types / arguments is a real, peer-reviewed failure mode
  of LLM-generated Terraform.** `[moderate]` directionally, `[low]` on specific
  numbers (corrected by the devil's-advocate pass —
  [`iac-terraform-pack-counterpoints.md`](iac-terraform-pack-counterpoints.md)).
  The **peer-reviewed anchor is IaC-Eval (Kon et al., NeurIPS 2024 Datasets &
  Benchmarks Track)** — an **AWS-only** benchmark (curated AWS Terraform tasks) on
  which LLMs frequently emit resource/argument identifiers absent from the provider
  schema; best models score low pass@1. **Correction:** the widely-quoted "~29% of
  runs / 46-pp generation→validation drop" figures do **not** come from IaC-Eval or
  from arXiv 2512.14792 — they trace to an **unverifiable ResearchGate paper**
  ("Hallucinated Resources, Brittle Oracles…", no arXiv, no confirmed peer review);
  treat them as **unverified**. No independent Azure/GCP replication exists.
- **Schema/config-grounded retrieval is the best-evidenced mitigation.** `[moderate]`
  Nekrasov et al. (arXiv 2512.14792, Dec 2025 — preprint) raised **technical
  validation to 75.3%** by injecting structured configuration knowledge
  (progressive → Graph RAG). **Correction:** the "27%→75%" framing conflates two
  metrics — 27.1% is the *overall-success* baseline, 75.3% the *technical-validation*
  endpoint; it is not a clean before/after of one measure. The directional signal
  (grounding materially helps) holds. **This is the empirical case for the pack
  reusing `core`'s contract-acquisition oracle — "acquire the platform's contract,
  never guess a flag or schema."**
- **`terraform validate` / `plan` are argued necessary but insufficient as
  correctness oracles — "plan-clean ≠ correct."** `[low]` TerraProbe (arXiv
  2606.26590, non-frontier models) shows LLM "fixes" can pass both `validate` and
  `plan` while being semantically wrong ("deceptive fixes"). **Counter the review
  surfaced:** a follow-on found only **59% of IaC-Eval's own ground-truth passes
  `terraform plan`** — so some apparent oracle-insufficiency may be **benchmark
  oracle-artifact noise**, not an LLM-specific property. The prudent reading —
  *don't over-trust any single oracle* — still **supports** `core`'s phased-oracle
  discipline and keeping the human apply-gate.
- A general "Correctness-Congruence Gap" persists: grounding fixes syntax/schema
  hallucination but *not* intent-alignment. `[moderate]` Grounding is necessary,
  not sufficient; human review of intent stays load-bearing.

## Synthesis — what the evidence says about RFC-0065's design

1. The workflow *shape* (intent→spec→plan→tasks→implement) is validated prior art,
   but its known failure mode (leaking phase gates; infra flowing backward) argues
   for **structural enforcement of Stage-0 + drift-awareness**, both of which the
   pack gets by reusing `core`.
2. The six Terraform practices are primary-doc best practice; two **recency
   corrections** land in the seeds: native S3 locking (not DynamoDB), and the
   GitHub OIDC `sub`-claim format change.
3. Policy-on-plan-JSON is the right mechanism; **cite Trivy not tfsec**, note the
   plan-JSON unknown-values caveat, and note Sentinel's paywall.
4. OIDC + "environment-as-gate" human approval are cross-vendor consensus — the
   RFC's two-apply-boundary design is well-grounded.
5. The strongest, most decision-relevant evidence: **schema-grounded generation is
   the best-evidenced fix for hallucinated Terraform, and `plan`/`validate` are
   insufficient oracles.** Both are already `core` doctrine (contract-acquisition;
   phased oracle fidelity) — so the pack's "reuse core, don't re-ship doctrine"
   choice is not just charter-hygiene, it is what the empirical evidence recommends.

## Known unknowns

- **Known-unknown:** Does the spec-driven-IaC loop actually reduce hallucination /
  drift *in production at scale*? Would be closed by: a controlled study or a named
  adopter post-mortem running SDD-generated Terraform in prod — none exists yet
  (all IaC adaptations are <1 year, experimental).
- **Known-unknown:** Do the failure-mode benchmark numbers (46pp drop; 27%→75%
  with RAG) hold on Azure/GCP and on current-generation models? Would be closed
  by: cross-provider, cross-lab replication — the benchmarks are AWS-centric,
  single-lab, and un-replicated.
- **Known-unknown:** Does AGENTS.md/skill-carried standards actually make agents
  behave more deterministically, and by how much? Would be closed by: an efficacy
  study — none found; the claim rests on first-party mechanics.
- **Unknowable (as posed):** Whether "code serves specifications" is the right
  paradigm for infrastructure vs. infra's backward-flowing reality — this is a
  contested design-philosophy tension (SDD forward-flow vs. reconcile-from-reality)
  that both camps argue well under different conditions; no evidence settles it. It
  belongs in a tension, not a finding.

## Citations (deduplicated, primacy-tagged)

**Primary.** github/spec-kit `spec-driven.md`; IBM/iac-spec-kit; dotlabshq/spec-ops;
HashiCorp standard-module-structure, dependency-lock, version-constraints, S3
backend, JSON-output-format, Sentinel, default_tags, GitHub-Actions automation
tutorial; AWS Prescriptive Guidance (structure, security); OPA Terraform docs;
Checkov docs + repo; Aqua/tfsec `#1994`; GitHub OIDC (AWS/Azure/GCP) + Environments +
reviewing-deployments docs; AWS "IAM roles for GitHub Actions" + configure-aws-credentials;
Microsoft Entra workload-identity-federation + Azure DevOps approvals; Google WIF +
google-github-actions/auth; GitLab protected-environments + deployment_approvals;
agents.md; Anthropic Claude Code SDK slash-commands; arXiv 2512.14792, 2606.26590,
2601.08734, 2509.22202, 2404.00971.

**Secondary (practitioner / vendor blog).** Mamezou Spec-Kit-IaC; InfoQ SDD; The New
Stack SDD-for-infra; Gruntwork infrastructure-live + state blog; terraform-best-practices.com;
Spacelift, OSO, env0, TachTech (policy comparison, vendor-motivated); Terramate
(apply-before-merge counterpoint); ITNEXT IaC-Eval summary; TerraShark (single-maintainer OSS).

**Fetch-blocked / unverified.** ResearchGate "Hallucinated Resources, Brittle
Oracles…" (403; specific 49%/20%/42% numbers from search snippet only — provisional).
