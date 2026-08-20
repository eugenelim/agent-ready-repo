# docs/product/findings/

Structured governance registers for this repo. This directory holds
registers that surface work and decisions that overflow the normal
`docs/specs/` → ADR pipeline.

**Purpose (per CONVENTIONS.md §5b):** governance registers — candidate
RFCs surfaced by owner-requested capture and `frame-situation` escalations, and
deferred roadmap items that are not yet specs.

## Registers (coming in M3)

The following register files are created by M3:

- `rfc-candidates.md` — candidate RFCs surfaced by owner-requested capture and
  `frame-situation` escalations.
- `roadmap-intents.md` — deferred roadmap items.

Their column schemas and initial content are M3 deliverables. Do not add
column schemas or data rows here; this README is the Batch 5 placeholder.

Both files are seeded and populated by M3. Do not create them here;
this `README.md` is the Batch 5 placeholder that establishes the
directory's purpose ahead of that work.

## How entries get here

- **`work-loop`:** an out-of-scope finding reaches a register only when its
  owner explicitly decides to record it; otherwise the PR acknowledges the
  exclusion without a durable follow-on.
  A `frame-situation` escalation or a pattern that warrants an RFC is
  promoted into `rfc-candidates.md` (M3).
- **`workspace-status`** (after M3 ships): surfaces the candidate count
  at session start — "N rfc candidates · M roadmap intents".

## Supporting evidence

Registers cite evidence; the evidence itself lives beside them when it was
produced by a repo-governance question rather than a product question.

- `adaptive-planning-survey.md` — applied survey behind the RFC-0083 delivery-plan
  erratum: how governance artifacts stay revisable without losing decision
  traceability. Confidence-tagged, with an explicit Known-unknowns section.
