# Plan: jira-brief-intake

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Pure prose-choreography, modelled file-for-file on the pack's existing
`jira-defect-flow` skill. The work is: author one new skill directory under
`packs/atlassian/.apm/skills/jira-brief-intake/` (`SKILL.md`, `manifest.json`,
`references/examples.md`), then sweep the four docs that enumerate the pack's
skills, bump `pack.toml`, add a changelog entry, and regenerate
`.claude-plugin/marketplace.json` via `make build`.

The riskiest part is **not** code — there is none — it is *boundary
discipline*: keeping the skill thin so it doesn't bleed into the two skills it
composes. The SKILL.md must (a) route every Jira read through the `jira` skill
by name, (b) hand elicitation/decomposition/execution to `receive-brief` by
name, and (c) own only the Jira→brief mapping in between. The
graceful-degradation path is the one place the skill carries
`receive-brief`-shaped knowledge (a compact brief shape + a decompose/execute
instruction); that is a deliberate, bounded duplication for the core-absent
case, not a reimplementation — it hands the job to the agent rather than doing
it inline.

The brief mapping is the substance: a Jira epic becomes a **Shape B** brief
(story-list), its children become `US-n` stories each tagged with the source
Jira key, and the epic key drops into the `Epic:` provenance pointer. This
gives a full traceability chain Jira key ↔ `US-n` ↔ spec AC (`receive-brief`
stamps `Satisfies: US-n` on derived spec ACs downstream).

## Constraints

- No governance constraint (no ADR/RFC governs the atlassian pack's workflow
  skills). The binding precedent is the in-pack `jira-defect-flow` skill: same
  cross-skill-by-name contract, same manifest `deps` shape, same
  reference-docs layout.
- atlassian is user-scope-default — gate is `lint-packs` + `validate` +
  `build` + package pytest (see spec Assumptions).

## Construction tests

No new executable logic ships, so there are no per-task unit tests. Verification
is goal-based + manual QA (see spec Testing Strategy).

**Integration tests:** none beyond the pack gate (`lint-packs`, `validate`,
`build`, agentbundle pytest), which validates skill well-formedness and
marketplace-drift.
**Manual verification:**
1. Reading-level dry-run of `SKILL.md` against a representative epic (e.g.
   `PROJ-100` with children `PROJ-101..103`): confirm every dispatched `jira`
   subcommand (`get-issue`, `search`) exists in `jira/SKILL.md`; confirm the
   produced brief conforms to the carried shape (Outcome from epic, `US-n` from
   children with Jira keys, `Epic: PROJ-100`); confirm hand-off to
   `receive-brief` by name.
2. Core-absent path: confirm the degraded branch inlines a decompose/execute
   instruction, does not stop, **and** records the note that downstream
   `new-spec` / `work-loop` may likewise be absent.
3. Single-non-epic-issue path: confirm the skill recommends `new-spec` and asks
   before proceeding.
4. `jira`-prerequisite path: confirm the skill probes `jira: check` first and,
   on exit 2, tells the user to run `credential-setup` and stops (no reads
   dispatched into an auth failure).

## Tasks

### T1: jira-brief-intake skill authored and well-formed

**Depends on:** none

**Tests:**
- `lint-packs` passes for the atlassian pack (skill frontmatter + structure
  well-formed). Verifies spec AC1.
- `grep` confirms no raw Jira REST call and no Jira write verb
  (`create-issue|update-issue|delete-issue|transition|comment|attach`) appears
  anywhere in the skill directory — `SKILL.md` **and** `references/`, including
  "don't do this" examples. Verifies spec AC2.
- `grep` confirms the skill names `receive-brief` and `jira` by name and the
  manifest `deps.skills` lists both. Verifies spec AC4.
- Reading-level dry-run (Manual verification 1–3). Verifies spec AC3, AC5, AC6.

**Approach:**
- Create `packs/atlassian/.apm/skills/jira-brief-intake/SKILL.md` mirroring
  `jira-defect-flow`'s structure: frontmatter (`name`, trigger `description`,
  `metadata.version`), a "choreography not invention" preamble, a
  "cross-skill invocation by name" section, Prerequisites (incl. the
  `receive-brief`-present probe that drives graceful degradation), a Lifecycle
  with stages (Intake → enumerate children with the flavor-correct
  `parent = $KEY` / `"Epic Link" = $KEY` query + fallback → Map to brief
  (Shape B) → Hand off to receive-brief by name → Graceful-degradation
  core-absent branch carrying a brief shape + decompose/execute instruction),
  Don't, Edge cases (incl. single-non-epic-issue → recommend new-spec), Examples
  pointer.
- Create `manifest.json` mirroring `jira-defect-flow`'s, with `deps.skills` =
  `jira` (this pack) + `receive-brief` (core; degrade gracefully if absent),
  the runtime-by-name `_runtime_contract` note, `input`/`output` blocks.
- Create `references/examples.md` with worked patterns: an epic-with-children
  happy path, a JQL/board selection, the single-non-epic-issue→new-spec case,
  and the core-absent degraded path.

**Done when:** the skill directory exists, `lint-packs` is green for atlassian,
and the greps + dry-run above hold.

### T2: pack metadata bumped and marketplace regenerated

**Depends on:** T1

**Tests:**
- `agentbundle validate` passes for the atlassian pack. Verifies spec AC8 (part).
- `make build` regenerates `.claude-plugin/marketplace.json` with no remaining
  drift (`git diff` shows only the intended additions). Verifies spec AC8.

**Approach:**
- Bump `packs/atlassian/pack.toml` `[pack].version` and extend its
  `description` to name the new workflow skill.
- Sync `packs/atlassian/.claude-plugin/plugin.json` (version + description) —
  it is tracked and hand-mirrors `pack.toml`; build aggregates it into
  `marketplace.json`.
- Run `make build` to refresh `.claude-plugin/marketplace.json`.

**Done when:** `validate` is green and `marketplace.json` matches the bumped
pack with no drift.

### T3: docs enumerations + changelog updated

**Depends on:** T1

**Touches:** packs/atlassian/README.md, docs/guides/atlassian/README.md, docs/guides/atlassian/reference/atlassian-skills.md, docs/guides/atlassian/explanation/atlassian-pack.md, docs/architecture/overview.md, docs/guides/README.md, docs/product/changelog.md

**Tests:**
- `grep` for `jira-brief-intake` hits all six enumeration docs. Verifies spec AC7.
- Each doc's skill enumeration is **internally consistent** after the edit:
  count words and role groupings ("seven skills", "three workflow skills",
  "Three skills compose") match the actual skill set — hand-checked, since this
  is prose no lint enforces. Verifies spec AC7.
- `grep` for the new skill in `docs/product/changelog.md` `[Unreleased]`.
  Verifies spec AC9.
- The reference-guide section mirrors the skill's frontmatter `description`
  (hand-checked byte-for-byte against `SKILL.md`).

**Approach:**
- `packs/atlassian/README.md`: add the skill to the workflow-skills sentence
  and the "What's inside" bullets (de-count rather than bump a hardcoded count,
  per the no-brittle-counts convention, where the edit already touches the line).
- `docs/guides/atlassian/README.md`: add to the skill enumeration.
- `docs/guides/atlassian/reference/atlassian-skills.md`: add a
  `## jira-brief-intake` section (Purpose / Primary inputs / Outputs / Source)
  mirroring the frontmatter.
- `docs/guides/atlassian/explanation/atlassian-pack.md`: add a one-line bullet.
- `docs/architecture/overview.md`: add the skill to the atlassian row's skill list.
- `docs/guides/README.md`: add the skill to the atlassian pack-index row.
- `docs/product/changelog.md`: add an `[Unreleased] → Added` entry.

**Done when:** all six enumeration docs and the changelog name the skill, and
the reference section mirrors the frontmatter.

## Rollout

Pure catalogue content — no infra, no migration, no deployment sequencing. The
skill ships when the PR merges; adopters get it on their next `agentbundle
install`/`upgrade` of the atlassian pack. Fully reversible (revert the PR).

## Risks

- **Boundary bleed** — the skill drifts into reimplementing `jira` reads or
  `receive-brief` elicitation. Mitigated by the spec's Never-do rules and the
  pre-EXECUTE + diff adversarial passes, which check exactly this against the
  `jira-defect-flow` precedent.
- **Marketplace drift** — forgetting `make build` leaves `marketplace.json`
  stale and red-fails CI. Mitigated by T2's explicit build + drift check.
- **Reference-guide frontmatter drift** — the reference section is
  hand-maintained and invisible to `lint-packs`/`build`; only adversarial
  review catches a mismatch. Mitigated by hand-checking it byte-for-byte in T3.
- **Carried brief-shape drift** — the degraded core-absent path carries a
  compact brief shape inside `SKILL.md`, invisible to `lint-packs`/`build`, so
  it can silently drift from the canonical
  `packs/core/seeds/docs/product/briefs/_template.md` as that template evolves
  (same class as the frontmatter-drift risk above). Mitigated by keeping the
  carried shape minimal (section headings + the `US-n` line format only, not a
  full copy) so the drift surface is small, and by adversarial review.

## Changelog

- 2026-06-15: initial plan.
