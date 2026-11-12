# Record installed-skill governance evidence

- **Slug:** `installed-skill-governance-inventory`
- **Status:** Fulfilled
- **Fulfilled:** 2026-11-12 eugenelim: both maintained AST09 sources distinguish recorded install hashes from scanner/host evidence and preserve missing-evidence gaps, proven by two source contracts in the passing 1172-test targeted batch.
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim

## Outcome

The AST09 checklist documents which installed-skill evidence install state
provides and which evidence must come from a scanner or host. Missing scan or
execution records remain explicit governance gaps; assigning ownership does not
prove compliance.

## Opportunity

Direct-install state now records a SHA-256 content hash for each installed file, but it does not provide scan-status fields or a logged execution trail that ties an agent action to the skill version that instructed it.

## What this absorbs

### skill-governance-inventory-gap

Direct-install state groups per-file SHA-256 hashes under each installed skill’s
row, with recorded identity and provenance. That provides content identity, not
scan results or a trace linking an agent action to its instructing skill version.
Both the runtime AST09 checklist and canonical OKF concept need the same
ownership clarification. No new state-schema field or command is needed.

## Decision

Clarify both maintained sources:
`packs/core/.apm/skills/security-checklists/references/agentic-skills.md` and
`packs/core/okf/security-checklists/concepts/agentic-skills.md`. Name install
marker plus state file as the recorded identity/provenance and per-file hash
surface. Require scan status from the scanner or host and execution evidence
from the host. Missing evidence is still a finding. Compile the canonical OKF
bundle during integration; generated copies are not authoring sources.

## Non-goals

- No scan-status field, scanner, or install-marker schema change: scan status has no producer in this repository.
- No execution trail written by `agentbundle`: tying an agent action to a skill version is a host feature.
- No change to the per-file SHA-256 that direct install already records.

## Assumptions

- **Riskiest assumption:** naming evidence owners helps a reviewer distinguish
  recorded hashes from missing scan and execution records. Content pins check
  both maintained sources without claiming host evidence exists.
- `_record_direct_rows` in `packages/agentbundle/agentbundle/direct_install.py`
  computes SHA-256 from installed bytes. This is source evidence, not a claim
  that a fixture install or host audit was run in this slice.

## Readiness

- **Route:** direct-light documentation and pack-local contract pins only.
- **Proof:** both maintained sources name install identity/provenance, per-file
  content hashes, scanner/host scan status, host execution evidence, and the gap
  when those records are missing.
- The optional `list-installed` enhancement is outside this slice.
- `security-checklists` is excluded from activation evals; content pins cover
  this reference clarification without inventing an activation suite.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
