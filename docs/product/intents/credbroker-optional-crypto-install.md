# Credential broker crypto installation is safely optional

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/credbroker-user-scope Boundaries](../../specs/credbroker-user-scope/spec.md)

## Outcome

An adopter can deliberately install `credbroker[crypto]` through `agentbundle install --with-credbroker` with correct interpreter and virtual-environment targeting.

## Opportunity

The vendored floor already supplies full Tier-1, Tier-2, and Tier-3 resolution with zero `pip`, but `agentbundle install --with-credbroker` does not auto-run `pip install credbroker[crypto]` to enable the encrypted `[crypto]` vault.

## What this absorbs

### active-with-credbroker-pip

`spec/credbroker-user-scope` deferred auto-running `pip` from the install command in its Boundaries → Ask first section. This is not an unmet acceptance criterion. The remaining risk is interpreter and virtual-environment targeting: which Python receives `pip` could silently install the package where the skill cannot import it. **Unblocks when:** a concrete adopter need surfaces and the interpreter/venv-resolution question is settled. `docs/specs/credbroker-user-scope/spec.md:42` records the same deliberate deferral.

## Assumptions

- The vendored floor remains the baseline credential-resolution path; optional crypto installation requires both an adopter need and settled interpreter/venv resolution.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
