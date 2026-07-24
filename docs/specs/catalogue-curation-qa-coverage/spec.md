# Spec: catalogue-curation-qa-coverage

- **Status:** Approved
- **Owner:** eugenelim
- **Constrained by:** [`spec/catalogue-curation`](../catalogue-curation/spec.md) — parent spec (Shipped); this spec closes the four deferred ACs.
- **Brief:** none
- **Shape:** quality

Mode: light (QA exercise + fixture authoring for four deferred catalogue-curation paths; no code change to the skill itself)

> **Spec contract:** this document defines what "done" means. The implementing PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `catalogue-curation` pack shipped with four acceptance-criteria paths not yet exercised in QA, each deferred explicitly in the parent spec with a backlog slug. This spec closes those four paths:

1. **`resync-rfc-routing`** — When a previously-assimilated source RFC is re-synced, the skill must route the record correctly: Amendment (Open RFC), Erratum (Frozen + genuine correction), or new RFC (Frozen + new decisions). The routing logic is implemented but was not exercised in any QA session.

2. **`antipattern-steering`** — Assimilation detects known misuse patterns in ingested primitives (scripts triggering other skills, agents reviewing their own output, flooding prompts) and either reshapes or rejects, naming the anti-pattern and its correction. Not yet exercised.

3. **`propose-catalogue-pack`** — Given a proposed pack area, the skill tests additivity + fit against the local CHARTER and the four CHARTER principles, scaffolds a pack shell on pass, and emits an RFC. No QA session has been run.

4. **`hook-confirm`** — An ingested hook or script (executable code) is flagged distinctly and requires explicit human confirm before landing. The QA session exercised skill ingest only; the hook-ingest path was not exercised.

The autonomous portion of this work — authoring fixture files and documenting expected-behavior transcripts — can be done without a live session. The QA sessions themselves require a human operator running the skills interactively. This spec owns both: fixture authoring (implementable autonomously) and the QA session gate (requires human confirmation).

## Acceptance Criteria

### Autonomous: fixture preparation

- [x] **AC1 (`antipattern-steering` fixtures).** At least three fixture primitives exist under `docs/specs/catalogue-curation-qa-coverage/fixtures/antipatterns/`, each representing a known misuse pattern:
  - `skill-triggers-skill.md` — a skill that directly invokes another skill by name (scripts-triggering-skills pattern)
  - `agent-reviews-own-output.md` — an agent skill whose SKILL.md instructs the agent to review its own output
  - `flooding-prompt.md` — a skill with an excessively verbose or repetitive prompt that floods context without value
  Each fixture is a realistic, ingestible primitive exhibiting the misuse pattern only — shaped like a real skill/agent file a curator would encounter (frontmatter + SKILL.md body). The `## Why this is rejected` and `## Reshaped form` analysis belongs in `notes/antipattern-steering.md` (AC3), not in the fixture files themselves. This separation ensures AC5's live QA session exercises real detection, not fixture-embedded answers.

- [x] **AC2 (`hook-confirm` fixture).** A fixture hook file exists under `docs/specs/catalogue-curation-qa-coverage/fixtures/hook-confirm/` that represents a realistic hook that would trigger during ingest:
  - `sample-hook.sh` — a bash hook that runs on git pre-commit (or equivalent agent event)
  - `sample-hook-notes.md` — documents what the hook does, why it requires explicit operator confirm, and what the expected confirm prompt should look like.

- [x] **AC3 (expected-behavior transcripts).** A `notes/` directory contains one transcript-capture document per deferred path:
  - `notes/resync-rfc-routing.md` — documents the three routing cases (Open → Amendment, Frozen+correction → Erratum, Frozen+new → new RFC) with example inputs and expected skill outputs for each case.
  - `notes/antipattern-steering.md` — documents the three anti-pattern cases with example inputs, expected detection messages, and expected corrective re-shaping outputs.
  - `notes/propose-pack.md` — documents the additivity+fit test flow with a sample pack proposal, the scaffold output, and the RFC template the skill would produce.
  - `notes/hook-confirm.md` — documents the hook-ingest flow: detection trigger, confirm prompt text, post-confirm landing path.

### Human-gated: live QA sessions

- [ ] **AC4 (`resync-rfc-routing` QA).** A live QA session exercises all three routing forms against the `agent-commander` RFC-0001 produced in the 2026-07-22 `assimilate-repo` QA session (the prior-QA source RFC). Session outcome is recorded as a `| Date | Skill | Exercise | Outcome |` row in `docs/specs/catalogue-curation/spec.md`'s QA log table (matching the existing table column format exactly).

- [ ] **AC5 (`antipattern-steering` QA).** A live QA session runs assimilation against at least one of the three anti-pattern fixture files (AC1). The skill detects the pattern and either reshapes or rejects with a named reason. Session outcome recorded in parent spec QA log.

- [ ] **AC6 (`propose-catalogue-pack` QA).** A live QA session runs `propose-catalogue-pack` with a real or sample pack proposal. The skill tests additivity + fit and either rejects (non-additive) or passes and scaffolds a pack shell + RFC. Session outcome recorded in parent spec QA log.

- [ ] **AC7 (`hook-confirm` QA).** A live QA session ingests the `sample-hook.sh` fixture (AC2). The skill flags it as executable code, issues the confirm prompt, and — on operator confirm — lands it. Session outcome recorded in parent spec QA log.

### Gate

- [ ] **AC8.** Once each QA session passes (AC4–AC7), the corresponding deferred-AC item in `docs/specs/catalogue-curation/spec.md` is flipped from `- [ ] … (deferred: <slug>)` to `- [x] …` with the `(deferred: <slug>)` annotation removed. All four deferred lines must be checked before this AC is complete.

- [ ] **AC9.** The four backlog slugs (`catalogue-curation-resync-rfc-routing`, `catalogue-curation-antipattern-steering`, `catalogue-curation-propose-pack`, `catalogue-curation-hook-confirm`) are removed from `workspace.toml [backlog].open` in the same PR that flips the parent spec checkboxes (AC8). Leaving them in the register after the work is done creates the same drift the parent spec closure is meant to resolve.

## Boundaries

### Always do

- Keep all fixture files under `docs/specs/catalogue-curation-qa-coverage/fixtures/` — not under `packs/` (fixtures are spec support material, not pack assets).
- Record every QA session outcome in the parent spec's QA log, not in this spec.
- Mark AC4–AC7 as done only after a human operator has confirmed the session ran and passed.

### Never do

- Modify the `catalogue-curation` skill source (`packs/core/.apm/skills/catalogue-curation/`) as part of this spec — if a QA session reveals a bug, open a separate bug PR.
- Auto-invoke `propose-catalogue-pack` from `assimilate-repo` (existing Never-do from parent spec).
- Invent fictional QA session outcomes — AC4–AC7 require real runs.

### Ask first

- Adding a fourth anti-pattern fixture type beyond the three specified.
- Changing the fixture format if the skill's ingest format has evolved since the parent spec shipped.

## Testing Strategy

- **AC1–AC3 (fixtures + transcripts):** Goal-based — files exist and contain the required sections. Verification: `ls docs/specs/catalogue-curation-qa-coverage/fixtures/antipatterns/`, `ls fixtures/hook-confirm/`, `ls notes/`, spot-check headers.
- **AC4–AC7 (live QA):** Manual QA — human operator runs each skill path; records outcome. Not automatable; the QA session is the verification.
- **AC8 (parent spec checkboxes):** Goal-based two-part check: (1) `grep "deferred: catalogue-curation" docs/specs/catalogue-curation/spec.md` returns zero matches (all four `(deferred: <slug>)` annotations removed); (2) manually verify in the PR diff that each of the four affected lines now shows `- [x]` (checkbox flipped). Both parts must pass — part 1 confirms annotation removal; part 2 confirms the flip happened.
- **AC9 (register cleanup):** Goal-based — `grep "catalogue-curation-resync-rfc-routing\|catalogue-curation-antipattern-steering\|catalogue-curation-propose-pack\|catalogue-curation-hook-confirm" workspace.toml` returns no matches. Each backlog entry's preceding comment block (the explanatory `# …` lines immediately above the `{slug = "…"}` line) is removed alongside the slug line — leaving stale comment blocks is the same drift AC9 exists to prevent.

## Assumptions

- Technical: The four deferred AC paths are implemented in the shipped `catalogue-curation` skill — the QA sessions exercise existing code, not new code. (Source: parent spec QA log, read 2026-07-23.)
- Technical: `docs/specs/catalogue-curation-qa-coverage/fixtures/antipatterns/` and `fixtures/hook-confirm/` directories were created in a prior session — verify before creating.
- Process: The parent spec's QA log table format is `| Date | Skill | Exercise | Outcome |` (four columns, no separate PASS/FAIL column — the Outcome cell carries PASS/FAIL). Follow this exactly when recording new sessions.
- Process: AC4–AC7 require human in the loop; they cannot be completed autonomously in an unattended run.
- Process: The parent spec (`docs/specs/catalogue-curation/spec.md`) is Shipped (Frozen). Editing its body to flip deferred-AC checkboxes and append QA-log rows is the sanctioned closure mechanism for deferred ACs — these are the defined update surfaces (Status field + spec body for QA-log rows) rather than general-purpose body edits. The four deferred ACs were explicitly marked `(deferred: <slug>)` to be closed by this follow-on spec; flipping them is the intended resolution path.

## Tasks

1. **Author anti-pattern fixtures** (AC1) — Write `fixtures/antipatterns/skill-triggers-skill.md`, `agent-reviews-own-output.md`, `flooding-prompt.md` as realistic ingestible primitives (no answer-key sections in the fixture files).
   - **Depends on:** none
2. **Author hook fixture** (AC2) — Write `fixtures/hook-confirm/sample-hook.sh` and `sample-hook-notes.md`.
   - **Depends on:** none
3. **Author expected-behavior transcripts** (AC3) — Write `notes/resync-rfc-routing.md`, `notes/antipattern-steering.md`, `notes/propose-pack.md`, `notes/hook-confirm.md`. The antipattern notes include the `## Why this is rejected` and `## Reshaped form` analysis (the answer key that must not appear in the fixture files).
   - **Depends on:** none
4. **Live QA sessions** (AC4–AC7) — Human-in-loop; depends on Tasks 1–3 being complete. Each session is a separate step.
   - **Depends on:** Tasks 1–3
5. **Mark parent spec ACs and clean register** (AC8, AC9) — Flip the four deferred lines in `docs/specs/catalogue-curation/spec.md` to `- [x]` (removing `(deferred: …)` annotation); remove the four slugs and their preceding comment blocks from `workspace.toml [backlog].open`.
   - **Depends on:** Task 4

## Declined

- Automated regression tests for the four paths — these are human-judgment paths (routing decisions, anti-pattern detection, CHARTER fit assessment, hook risk evaluation); the QA session is the right verification modality.
- Merging the four deferred paths into a single QA session — separate sessions give cleaner records and avoid conflating outcomes.
