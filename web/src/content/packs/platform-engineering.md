---
name: Platform Engineering
pluginInstallable: false
scope: repo
tagline: "Plan infrastructure. Review releases. Validate before shipping."
skills:
  - generate-iac
  - reconcile-iac
  - prepare-release-handoff
  - release-loop
  - define-slo
installCommand: "agentbundle install --pack platform-engineering"
docsUrl: /docs/guides/platform-engineering/
journeyUrl: /journeys/platform-engineering/
---

Platform Engineering turns infrastructure intent into reviewed Terraform or OpenTofu, audits managed-resource drift, and collects existing evidence into release candidates. The release loop admits candidates, obtains focused reliability and security reviews, and runs authorized protected GitHub Actions execution in temporary environments. Terraform authoring stops at a saved plan; it never applies. Release checks stop before your production decision. Core and Repository Governance are optional integrations. Release-only work needs no Terraform tooling.
