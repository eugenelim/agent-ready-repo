# RFC-0088 follow-on governance records exist

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0088 Follow-on artifacts](../../rfc/0088-web-pilot-foundation.md)

## Outcome

RFC-0088's required broker, adapter-artifact, and browser-session governance records are available for the authorized foundation implementation.

## Opportunity

RFC-0088 is Accepted, yet its required ADRs and the `auth: browser-session` convention amendment have not been created.

## What this absorbs

### rfc0088-adr-broker-deployment-model

- Record the ADR that chooses the broker deployment unit: a library-owned broker plus bound Playwright CLI.
- Unblocks when: an approver separately authorises implementation of the named item.

### rfc0088-adr-immutable-adapter-artifacts

- Record the ADR that establishes immutable adapter artifacts with no remote adapter catalogue in v1.

### rfc0088-convention-browser-session-lint

- Amend `docs/CONVENTIONS.md` with the `auth: browser-session` taxonomy and its pack-lint contract.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
