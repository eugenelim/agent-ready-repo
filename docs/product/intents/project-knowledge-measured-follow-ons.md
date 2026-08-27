# Project-knowledge measured follow-ons

- **Status:** Draft
- **Level:** capability

## Outcome

Adoption-closeout evidence determines whether any project-knowledge scale or
durability extension is worth activating, while the portable repository-first
baseline remains authoritative by default.

## Opportunity

RFC-0077 identifies four plausible follow-ons whose cost, privacy, and
operational boundaries are not justified until repository growth, enquiry
latency, capture loss, and cross-project demand are measured.

## Assumptions

- Engineering and operational integration completes before adoption closeout.
- Absence of measured pressure closes a candidate without implementation.
- External durability and multi-project sharing require separate RFCs if
  activated.

## Decomposition

- `project-knowledge-observation-retention-policy` — activate only when closed
  partitions have terminal dispositions and measured repository growth
  justifies retention or compaction. Scope any policy to a whole partition:
  deleting individual observations would break the append-only evidence model,
  and Git retains the history regardless. Affected surface is the `docs/knowledge/`
  observation journals and `project-knowledge --distill`.
- `project-knowledge-derived-index-scaling` — activate only when corpus size or
  enquiry latency exceeds the published portable budgets. Any index must stay
  rebuildable, disposable, gitignored, and never authoritative or committed; the
  committed body-free topic map and bounded lexical routing remain the portable
  baseline, and no database or embedding dependency is presumed.
- `project-knowledge-external-capture-backend` — activate only when closeout
  demonstrates material pre-gate or uncommitted-capture loss and a supported
  durable capability exists. **No implicit probing and no fallback store.**
  Requires its own RFC governing project identity, privacy, deletion,
  availability, and reconciliation with the repository journal.
- `multi-project-knowledge-bank` — activate only when closeout supplies real
  tenancy, audience, privacy, ownership, and deletion requirements. **Only
  reviewed, sanitized topics may be explicitly exported; observations and
  scratch never cross the boundary.** The receiving project must treat imported
  material as untrusted evidence and adopt it through its own distillation
  boundary.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0077-distill-knowledge.md
- Revision: sha256-bytes-v1:94de8754c752838d99562a6b5bbcfbaf64ed688072d0e26149063f5fbac81016
