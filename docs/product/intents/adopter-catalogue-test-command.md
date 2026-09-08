# Give catalogue adopters a canonical test command

- **Status:** Draft
- **Level:** feature
- **Authority:** [ADR-0071](../../adr/0071-pack-runtime-export-boundary-and-test-placement.md)

## Outcome

Catalogue adopters can run the tests they receive through one canonical command that discovers pack and conformance suites from the ADR-0071 layout, preserves one process per skill, and keeps test dependencies development-only.

## Opportunity

It is not established from the available local inspection whether that adopter command has already shipped. The command surface and ADR-0071 layout need readable evidence before implementation work is selected.

## What this absorbs

### agentbundle-catalogue-test-command

Give catalogue adopters a canonical way to execute the tests they receive. It must discover pack and conformance suites from the ADR-0071 layout, preserve one process per skill, and keep test dependencies development-only. The protected tree `packages/agentbundle/**` is touched, so its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. This requirement applies at commit time.

Unblocks when: command-surface and ADR-0071 evidence establishes whether the adopter command already shipped.

## Assumptions

- A readable catalogue command surface and ADR-0071 inspection would settle whether the adopter command exists and what remains to implement.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
