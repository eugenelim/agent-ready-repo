# Give catalogue adopters a canonical test command

- **Slug:** `adopter-catalogue-test-command`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [ADR-0071](../../adr/0071-pack-runtime-export-boundary-and-test-placement.md)

## Outcome

Catalogue adopters can run the tests they receive through one canonical command that discovers pack and conformance suites from the ADR-0071 layout, preserves one process per skill, and keeps test dependencies development-only.

## Opportunity

The `agentbundle` CLI exposes no `test` verb. The nearest command is `agentbundle pack evals run`, which runs Tier-A activation evals and does not discover pack or conformance suites. The ADR-0071 layout still needs reading to scope what the command must discover.

## What this absorbs

### agentbundle-catalogue-test-command

Give catalogue adopters a canonical way to execute the tests they receive. It must discover pack and conformance suites from the ADR-0071 layout, preserve one process per skill, and keep test dependencies development-only. The protected tree `packages/agentbundle/**` is touched, so its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. This requirement applies at commit time.

Unblocks when: the ADR-0071 layout evidence scopes what the command discovers and runs.

## Assumptions

- An ADR-0071 inspection will settle what the command must discover and run, since no adopter command exists.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
