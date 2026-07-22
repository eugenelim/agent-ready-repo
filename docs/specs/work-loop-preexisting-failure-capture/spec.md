# Spec: work-loop pre-existing failure capture + progressive disclosure

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Contract:** none
- **Shape:** methodology/prose change (skill source edits + new reference files); no application code

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `work-loop` skill has two open gaps: (1) when a gate fails on a pre-existing
broken test or lint violation (one that predated the session), the loop correctly
identifies it as out of scope but has nowhere to put the observation — it
disappears at session end and gets rediscovered cold next time; (2) three
sections of the SKILL.md carry inline detail that already has a full reference
file, inflating the skill's resident token cost without enabling new behavior.

Success is: (1) a clean capture path from discovered gate failure to
`[backlog].open`, with a reference that covers the schema and heuristics fully;
(2) three targeted collapses that shrink the inline content without removing any
doctrine, each backed by a reference the agent is explicitly told to load.

## Acceptance Criteria

- [x] AC1. `references/pre-flight-failures.md` exists in the source and contains: entry schema with `slug`/`source` fields and cold-start-sufficient comment format; the three-condition known-skip heuristic; stash-check and HEAD-compare detection methods; "made it worse" test; deduplication procedure; worked examples for a test failure and a lint error.
- [x] AC2. SKILL.md GATES step contains a "Pre-existing failure triage" paragraph (≤8 sentences) that: states the file-not-in-diff primary heuristic; names the known-skip and "made it worse" branches; references `references/pre-flight-failures.md` for full schema.
- [x] AC3. `references/self-coverage/protocol.md` exists and contains the full six-step protocol currently inline in the self-coverage gate section (pre-mortem hook through done-checklist refusal, with their existing light/full mode applicability note).
- [x] AC4. The self-coverage gate section in SKILL.md is collapsed to ≤8 lines; the three net-new obligations (conditional domain-grounding, disposition record, done-checklist refusal) are named explicitly in the collapsed text; the non-skippability statement is preserved.
- [x] AC5. The infra/deploy multi-artifact preflight paragraph (source lines 296–304: "For **infra/deploy** the mechanism is rarely one artifact…") is removed from SKILL.md; the existing pointer to `references/infra-verification.md` (naming "multi-artifact preflight" explicitly) remains and is the only reference an agent on infra-flavored work needs.
- [x] AC6. All progressive disclosure trigger text passes the activation test: an agent reading only the trimmed inline can still take the correct next action; the trigger states when to load the reference and what it adds.
- [x] AC7. The `risk-triggers:start` / `risk-triggers:end` block is unchanged — byte-identical to the block in `packs/core/seeds/AGENTS.md` (grep-equality maintained).
- [x] AC8. `make build-self FORCE=1` exits 0 and the projected copies (`.claude/skills/work-loop/SKILL.md`, `.agents/skills/work-loop/SKILL.md`, and the new reference files) match the sources.
- [x] AC9. `make build-check` exits 0.
- [x] AC10. Core pack version bumped in `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` (non-cosmetic prose change).

## Testing Strategy

Goal-based verification throughout — no application code to test.

- AC1–5: grep/read the edited files after `make build-self`.
- AC6: manual activation trace: for each trimmed section, walk the inline → reference path and confirm the inline names the loading trigger clearly.
- AC7: `grep -A1 "risk-triggers:start" packs/core/.apm/skills/work-loop/SKILL.md packs/core/seeds/AGENTS.md` — blocks must match.
- AC8–9: `make build-self FORCE=1 && make build-check`.
- AC10: read pack.toml version field after bump.

## Assumptions

- The source SKILL.md (`packs/core/.apm/skills/work-loop/SKILL.md`) is byte-identical to the projected copy (no unreported drift). *Verified by reading source lines 51–82, 296–304, 533–544 — confirmed identical.*
- `references/self-coverage/` exists in the source references directory. *Verified.*
- `infra-verification.md` contains the full multi-artifact preflight doctrine at its own section. *Verified at line 114.*
- The user reviewed the design in the prior conversation turn and approved the three progressive disclosure targets (self-coverage gate collapse, infra/deploy multi-artifact paragraph removal, GATES triage paragraph addition).

## Boundaries

### Always do
- Edit `packs/core/.apm/skills/work-loop/SKILL.md` (source), not the projected copy.
- Run `make build-self FORCE=1` after all edits are applied (not between edits — build-self runs a full pipeline that can revert intermediate edits).
- Run `make build-check` before committing.
- Preserve the `risk-triggers:start` / `risk-triggers:end` block byte-for-byte.

### Never do
- Edit `.claude/skills/work-loop/SKILL.md` or `.agents/skills/work-loop/SKILL.md` directly.
- Remove any operational dispatch instructions from the specialist reviewers section (activation risk too high per line).
- Add internal governance citations (RFC/ADR numbers, spec paths) to the skill or reference files.
