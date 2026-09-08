# Record installed-skill governance evidence

- **Status:** Draft
- **Level:** feature

## Outcome

Installed skills have a declared governance record that accounts for content identity, scan status, and the skill version that instructed an agent action.

## Opportunity

Direct-install state now records a SHA-256 content hash for each installed file, but it does not provide scan-status fields or a logged execution trail that ties an agent action to the skill version that instructed it.

## What this absorbs

### skill-governance-inventory-gap

AST09 requires an auditable inventory of per-skill version, content hash, and scan status for the installed set, plus a logged-execution trail tying an agent action to the skill version that instructed it. `agentbundle` install markers and state files remain a partial record. The original premise that they carried no per-skill content hash has changed: `packages/agentbundle/agentbundle/direct_install.py:943` records `relpath: {"sha": _hashlib.sha256(payload).hexdigest()}`. No scan-status or execution-trail field was found.

The recorded fix options are to extend the install-marker schema with content hash and scan status per skill, or document that the install marker is the sanctioned governance surface and flag the missing hash field as the AST09 closure condition in `agentic-skills.md`. The changed evidence means the closure choice must account for the existing per-file SHA-256 record rather than claim the hash is absent.

Unblocks when: a governance RFC or install-marker schema extension closes the gap.

## Assumptions

- The premise changed: direct-install state has per-file SHA-256 hashes; scan-status and execution-trail fields still need authoritative confirmation or closure.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
