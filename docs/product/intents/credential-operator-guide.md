# Credential operators have a setup guide

- **Status:** Draft
- **Level:** feature
- **Authority:** [credential architecture](../../architecture/credentials.md)

## Outcome

An operator can store a credential by following a dedicated credential-broker setup guide.

## Opportunity

`guides/credential-brokers/` has the author-facing `how-to/add-a-credentialed-skill.md`, whose line 2 summary says `"Build a lint-clean authenticated skill ..."`, but it has no guide for the operator who must store a credential. The credential-setup skill already ships without that guide.

## What this absorbs

### credential-operator-setup-guide

Create the missing operator setup guide. `docs/architecture/credentials.md` distinguishes the authoring guidance from operator setup, and `guides/credential-brokers/how-to/add-a-credentialed-skill.md` remains author-facing. **Unblocks when:** ready now — the skill it documents already ships.

## Assumptions

- The guide documents the shipped credential-setup skill rather than changing credential-broker behavior.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
