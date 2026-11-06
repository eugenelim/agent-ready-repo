# Record installed-skill governance evidence

- **Slug:** `installed-skill-governance-inventory`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim

## Outcome

Installed skills have a declared governance record that accounts for content identity, scan status, and the skill version that instructed an agent action.

## Opportunity

Direct-install state now records a SHA-256 content hash for each installed file, but it does not provide scan-status fields or a logged execution trail that ties an agent action to the skill version that instructed it.

## What this absorbs

### skill-governance-inventory-gap

AST09 requires an auditable inventory of per-skill version, content hash, and scan status for the installed set, plus a logged-execution trail tying an agent action to the skill version that instructed it. `agentbundle` install markers and state files remain a partial record. The original premise that they carried no per-skill content hash has changed: `_record_direct_rows` in `packages/agentbundle/agentbundle/direct_install.py` records `relpath: {"sha": _hashlib.sha256(payload).hexdigest()}`. No scan-status or execution-trail field was found.

The recorded fix options are to extend the install-marker schema with content hash and scan status per skill, or document that the install marker is the sanctioned governance surface and flag the missing hash field as the AST09 closure condition in `agentic-skills.md`. The changed evidence means the closure choice must account for the existing per-file SHA-256 record rather than claim the hash is absent.

Unblocks when: a governance RFC or install-marker schema extension closes the gap.

## Decision

Close the gap by documentation, not by a state-schema field. A scan-status field has no producer in this repository, and an execution trail that ties an agent action to a skill version is a host feature that `agentbundle` cannot write. The per-file SHA-256 in direct-install state already covers content identity. The closure is a short statement in the security checklist's AST09 entry (`packs/core/.apm/skills/security-checklists/references/agentic-skills.md`, line 100) that names the install marker plus state file as the inventory surface and names scan status and the execution trail as host-owned.

## Non-goals

- No scan-status field, scanner, or install-marker schema change: scan status has no producer in this repository.
- No execution trail written by `agentbundle`: tying an agent action to a skill version is a host feature.
- No change to the per-file SHA-256 that direct install already records.

## Assumptions

- **Riskiest assumption:** the install marker plus the per-file SHA-256 in state is an adequate AST09 inventory without a scan-status field, because scan status and the execution trail are host-owned. Agent-only test: a fixture install shows the recorded hash, and the closure text in the checklist reference is read against the AST09 wording to confirm it names both host-owned parts.
- The premise changed: direct-install state has per-file SHA-256 hashes; scan-status and execution-trail fields still need authoritative confirmation or closure.

## Readiness

- **Route:** direct-light, one session. It is a documentation edit to that reference plus, if cheap, a `list-installed` view that shows each skill's recorded content hash.
- **Verified 2026-11-05:** `_record_direct_rows` in `packages/agentbundle/agentbundle/direct_install.py` records a SHA-256 per installed file; the AST09 entry in `agentic-skills.md` still asks for scan status and an execution trail.
- **Agent-only proof:** the reference text names the surface and the host-owned parts; if the `list-installed` view is added, a fixture install shows the hash.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
