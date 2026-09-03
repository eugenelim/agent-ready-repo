# IaC Terraform Azure worked example

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0065 D5](../../rfc/0065-iac-terraform-pack.md)

## Outcome

The `iac-terraform` Azure provider has a worked example that passes its documented Terraform validation gate.

## Opportunity

Azure shipped contract-complete in `iac-terraform` v1 with four provider files and `providers/azure.md`, but it has no worked example that has passed `terraform init -backend=false`, `fmt -check`, and `validate`.

## What this absorbs

### iac-terraform-azure-validation

The provider index entry is stamped `experimental — not validated in v1.` Author `examples/azure/` to match `examples/aws/` and `examples/gcp/`. Run `terraform init -backend=false && fmt -check && validate`. Remove the experimental stamp from `providers/azure.md` and bump the provider-index entry to validated. The target is `packs/core/.apm/skills/iac-terraform/`, specifically `examples/azure/` and `providers/azure.md`. Unblocks when the Azure worked example is authored and passes the three-command gate.

The record also reports that four tests failed locally because `credbroker` was not installed and required `pip install -e ./packages/credbroker`; this was pre-existing on origin/main, confirmed 2026-07-27, with RFC-0065 D5 source-author review dated 2026-07-18. Current local evidence is required to confirm the test count and dependency state before treating that observation as current.

## Assumptions

- Current local evidence must establish the `credbroker` dependency state and any failing-test count.
- Current validation evidence must establish that all three Terraform commands pass for the authored Azure example.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
