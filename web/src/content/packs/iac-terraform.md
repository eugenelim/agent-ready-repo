---
name: IaC (Terraform)
scope: repo
tagline: "Intent → governed Terraform. Stops at plan."
skills:
  - generate-iac
  - reconcile-iac
installCommand: "agentbundle install --pack iac-terraform"
docsUrl: /docs/guides/iac-terraform/
journeyUrl: /journeys/iac-terraform/
---

IaC (Terraform) turns a plain-language infrastructure intent into governed, best-practice, cloud-agnostic Terraform plus a human-gated CI/CD pipeline. `generate-iac` runs a mandatory Stage-0 ADR gate, a vocabulary-firewalled spec, schema-grounded generation, and a policy-as-code and security preflight — then stops at a digest-pinnable `terraform plan` for G4 handoff. `reconcile-iac` audits plan-visible drift and proposes a per-resource disposition. The agent never runs `terraform apply`; it produces and pins the plan, and release-loop (or the generated pipeline) routes it to the real account. Depends on `core` and `governance-extras`.
