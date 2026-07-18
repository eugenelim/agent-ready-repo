# Plan: m1-governance-integration

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Four coherent content changes in one PR: (1) remove the orphaned
`"spec/m1-shaping-seeds"` entry from `workspace.toml` (the pre-split is
collapsed into this spec); (2) create three new `docs/product/` directories
with seed files (`projects/`, `findings/`, `initiatives/`); (3) write
`docs/product/workspace-toml-deps.md` as the dependency model reference doc;
(4) extend the `new-rfc` skill's "After acceptance" section to add the
workspace queue-write step.

All four are pure content changes — TOML edit and new markdown files plus a
skill prose edit. No code, no tests, no build step changes beyond the skill
projection (`make build-self`). The implementation order is tasks-first by
dependency: workspace.toml cleanup first (T0), seed files and reference doc
next (T1–T4, no dependencies on each other), then the skill edit that
references the reference doc (T5), then the README housekeeping (T6).

The riskiest part is the `new-rfc` skill edit: the "After acceptance" section
must be augmented without disturbing the existing follow-on artifact list, and
the degradation path (absent `workspace.toml`) must be written clearly enough
that a harness-agent follows it without ambiguity.

## Constraints

- **RFC-0064** — governs the M1 Workspace Foundation design; this spec
  implements Batch 5 ACs exactly. Any divergence requires an RFC-0064 erratum
  in the same PR.
- **CONVENTIONS.md §5b** — defines the expected content and purpose of each
  `docs/product/` subdirectory; seed files must conform to those definitions.
  The findings seed does NOT include the register column schema (M3 owns that
  per RFC-0064 M3 ACs).
- **RFC-0064 D7 and D9** — D7 defines the `{path/slug, needs}` inline object
  format and the three cross-queue prefix forms (`work:`, `shape:`, `brief:`);
  D9 defines the shaping-type prefix forms (`research:`, `strategy:`). The
  reference doc must reflect both faithfully.

## Construction tests

**Integration tests:** none (no cross-task integration surfaces; each task is
independently verifiable by file presence or grep).

**Manual verification:**
1. With an existing `workspace.toml` in the repo root (ini-002 section
   present), invoke `new-rfc` on a scratch RFC stub, walk it to the Accepted
   state, and verify: (a) the prompt "Add implementation specs to
   `workspace.toml` queue?" appears; (b) answering yes produces a correct
   `{path = "...", needs = "..."}` append in `["ini-002".work].queue`;
   (c) answering no leaves `workspace.toml` unchanged and continues to the
   follow-on artifact list.
2. Rename `workspace.toml` to `workspace.toml.bak`, repeat the flow, and
   verify: (a) the prompt still appears; (b) the literal skip note "workspace.toml
   not found — add the entry manually when Batch 2 lands" appears; (c) no
   error is raised. Restore the file afterward.
3. With `workspace.toml` present but the ini-002 section removed, repeat
   the flow and verify: the skill confirms the initiative slug with the user
   and offers to create the section with an empty `[work].queue` before
   appending — it does not silently skip and does not auto-create.

## Design (LLD)

### Dependencies & integration

The `new-rfc` skill edit references `workspace.toml` by path convention
(`./workspace.toml` relative to the repo root). No import, no library, no
TOML parser is introduced — the skill is read by an LLM that can follow prose
instructions to read and write TOML. The skill must state clearly:
- Check for `workspace.toml` in the working directory before attempting any
  write.
- If present: read the target initiative section, append to `[work].queue`,
  and stage the file.
- If absent: emit the exact skip note "workspace.toml not found — add the
  entry manually when Batch 2 lands" and continue.

The reference doc (`workspace-toml-deps.md`) is a standalone markdown file
with no dependencies. It links to RFC-0064 (D7 and D9) and to `workspace.toml`
as a lived example.

### Failure, edge cases & resilience

- **`workspace.toml` absent:** prompt appears; the literal skip note is
  emitted; no exception.
- **`workspace.toml` present but target initiative section absent:** the skill
  asks the user to confirm the initiative slug and offers to create the section
  with an empty `[work].queue` before appending; no silent skip, no
  auto-create. (RFC-0064 explicitly names blank-file and empty-sections as
  valid states — `rfc:209`, `rfc:246-250`.)
- **Initiative slug unknown:** the skill asks the user to confirm the initiative
  slug (e.g. `ini-002`) before appending; it does not guess.
- **`[work].queue` already contains the entry:** the skill surfaces the
  duplicate and asks the user whether to add anyway or skip; it does not
  silently de-duplicate.
- **Multiple active initiatives in `workspace.toml`:** the skill asks which
  initiative's queue to append to.

## Tasks

### T0: Remove `"spec/m1-shaping-seeds"` from `workspace.toml`

**Depends on:** none

**Touches:** `workspace.toml`

**Tests:**
- `grep "m1-shaping-seeds" workspace.toml` exits non-zero — entry absent (AC2).

**Approach:**
- Edit `workspace.toml`: remove the `"spec/m1-shaping-seeds"` line from
  `["ini-002".work].queue` (the pre-split entry that this spec collapses).
- Leave all other queue entries untouched.

**Done when:** `grep workspace.toml` for `m1-shaping-seeds` returns non-zero.

---

### T1: Create `docs/product/projects/_template.md`

**Depends on:** none

**Touches:** `docs/product/projects/_template.md`

**Tests:**
- `find docs/product/projects -name "_template.md"` exits 0 and returns one
  file (AC2).
- File contains `outcome`, `appetite`, `milestone`, and `brief` fields (AC2).
- File references `workspace.toml` as the queue coordination artifact (AC2).

**Approach:**
- Create `docs/product/projects/` directory.
- Write `_template.md` with: a YAML-style frontmatter block using the four
  required fields; a `## Milestone map` skeleton; a `## Briefs` table skeleton;
  and a note pointing to `check-workspace` as the session-start tool.
- Content is minimal: schema + guidance, no live project data.

**Done when:** `find docs/product/projects -name "_template.md"` returns one
result; file contains the four frontmatter fields and a `workspace.toml`
reference.

---

### T2: Create `docs/product/findings/` seed

**Depends on:** none

**Touches:** `docs/product/findings/`

**Tests:**
- `ls docs/product/findings/` exits 0 (directory exists; AC2).
- At least one seed file exists in `docs/product/findings/` (AC2).
- Seed file states it is awaiting M3's `rfc-candidates.md` and
  `roadmap-intents.md` register files (AC2).
- Seed file contains **no** column schema and **no** register entries (AC2 /
  Never do boundary).

**Approach:**
- Create `docs/product/findings/` directory.
- Write `README.md` explaining that `rfc-candidates.md` and
  `roadmap-intents.md` will be created by M3; describe the directory purpose
  per CONVENTIONS §5b ("structured governance registers"); do NOT include the
  register column schema (that is M3's deliverable per RFC-0064 M3 ACs).

**Done when:** directory exists; README.md present; no column schema or
register rows in any file in the directory.

---

### T3: Create `docs/product/initiatives/_template.md`

**Depends on:** none

**Touches:** `docs/product/initiatives/_template.md`

**Tests:**
- `find docs/product/initiatives -name "_template.md"` exits 0 (AC2).
- Template contains fields for altitude-1 initiative brief: outcome statement,
  appetite (quarters), cross-repo scope, and a link to the `workspace.toml`
  initiative section (AC2).

**Approach:**
- Create `docs/product/initiatives/` directory.
- Write `_template.md` with: a header block for the initiative name and ID
  (`INI-NNN`); fields per CONVENTIONS §5b's initiative brief definition;
  a `## Links` section with a `workspace.toml` initiative section pointer.
  This is the canonical seed that M2.6 will use.

**Done when:** file exists and contains the initiative brief fields.

---

### T4: Write `docs/product/workspace-toml-deps.md`

**Depends on:** none

**Touches:** `docs/product/workspace-toml-deps.md`

**Tests:**
- File exists at `docs/product/workspace-toml-deps.md` (AC3).
- `grep "work:" docs/product/workspace-toml-deps.md` matches (cross-queue; AC3).
- `grep "shape:" docs/product/workspace-toml-deps.md` matches (cross-queue; AC3).
- `grep "brief:" docs/product/workspace-toml-deps.md` matches (cross-queue; AC3).
- `grep "research:" docs/product/workspace-toml-deps.md` matches (shaping-type; AC3).
- `grep "strategy:" docs/product/workspace-toml-deps.md` matches (shaping-type; AC3).
- `grep -E "ini-[0-9]{3}:work:" docs/product/workspace-toml-deps.md` matches
  (cross-initiative prefix present in worked example; AC3 — cannot be satisfied
  by the RFC filename `ini-001` in a link).
- File mentions `check-workspace` as the display surface (AC3).
- File states that `work-loop` DAG enforcement is deferred to post-M1 (AC3).
- File links to RFC-0064 (AC3).

**Approach:**
- Write the reference doc covering, in order:
  1. String vs. inline-object entry format with examples.
  2. **Cross-queue prefix forms** (for deps in `[work]` queue): three prefixes —
     `"work:<path>"`, `"shape:<slug>"`, `"brief:<path>"` — with a one-line
     explanation each (RFC-0064 D7).
  3. **Shaping-type prefix forms** (for deps in `[shaping_queue]` across
     types): two prefixes — `"research:<slug>"`, `"strategy:<slug>"` — with a
     one-line explanation each (RFC-0064 D9).
  4. Cross-initiative prefix with a worked example (the ini-003 example from
     RFC-0064 § Proposed design).
  5. A "Display surface" section: `check-workspace` resolves the DAG and
     surfaces ready/blocked/parallel; agents do not enforce.
  6. A "Deferred" section: `work-loop` enforcement of the DAG is post-M1
     backlog; the doc explains what that means for current behavior.
  7. A link back to RFC-0064 D7 and D9, and to `workspace.toml` as a lived
     example.

**Done when:** all ten grep tests above pass.

---

### T5: Extend `new-rfc` skill — Accepted-path workspace prompt

**Depends on:** T4

**Touches:** source skill file in `packs/governance-extras/.apm/skills/new-rfc/SKILL.md`
(projected to `.claude/skills/new-rfc/SKILL.md`)

**Tests:**
- `grep "Add implementation specs to" .claude/skills/new-rfc/SKILL.md` matches
  the exact prompt text (AC1).
- `grep "workspace.toml not found" .claude/skills/new-rfc/SKILL.md` matches the
  exact skip-note text (AC1 — deterministically confirms the absent-file branch).
- Skill prose contains the missing-initiative-section edge case (confirm slug /
  offer to create section / no auto-create); verified by reading the section
  (AC1 bullet 4).
- Skill's "After acceptance" section still lists ADRs, specs, and CONVENTIONS
  edits (AC1 — existing follow-on list preserved; verified by reading the section).
- Manual verification steps 1–3 from Construction Tests above pass (AC1
  end-to-end; step 3 covers the missing-initiative-section scenario).

**Approach:**
- Edit the source skill file at `packs/governance-extras/.apm/skills/new-rfc/SKILL.md`
  (not the projected `.claude/` copy).
- In the "After acceptance" section, prepend a new step before the follow-on
  artifact list:
  - Step: check for `workspace.toml` in the working directory.
  - If present: ask the user which initiative slug and which spec paths to add;
    append entries in `{path = "...", needs = "..."}` format to
    `["<slug>".work].queue`; reference `docs/product/workspace-toml-deps.md`
    for the entry format.
  - If absent: emit the literal note "workspace.toml not found — add the entry
    manually when Batch 2 lands" and continue to the follow-on artifact list.
- Run `make build-self` (or equivalent projection step) to propagate the
  source edit to the projected `.claude/skills/new-rfc/SKILL.md`.

**Done when:** both grep tests above pass; manual verification (both with and
without `workspace.toml`) passes; projection is clean (`make build-self`
exits 0).

---

### T6a: Amend RFC-0064 — shaping-seed no-op + M2.6 sole-ownership

**Depends on:** none

**Touches:** `docs/rfc/0064-ini-001-ai-native-ecosystem.md`

**Tests:**
- RFC-0064 Batch 5 table row no longer implies a shaping-directory seed;
  wording explicitly notes `docs/product/shaping/` is untouched (AC4).
- RFC-0064 Batch 5 AC bullet (~line 407) matches the amended table row (AC4).
- RFC-0064 M2.6 JIT table row (~line 115) reads as *using* the Batch 5-seeded
  template, not creating it (AC4).
- RFC-0064 M2 AC (~line 418) also reads as *using* the Batch 5-seeded template
  (AC4 — sole ownership unambiguous across both sites).
- RFC-0064 Bootstrap example queue (~line 324) no longer lists
  `"spec/m1-shaping-seeds"` — the collapsed spec is removed (AC4 + T0
  consistency).

**Approach:**
- RFC-0064 is `Status: Draft`; direct body edits are permitted per CONVENTIONS
  §3 (Frozen rules apply only to Accepted/Rejected RFCs; no RFC-0055 erratum
  ceremony required).
- **Amendment 1 (Batch 5 shaping-seed):** edit the Batch 5 table row for
  "Shaping + initiative artifact seeds" to read: "`findings/` and
  `initiatives/` directory seeds; `shaping/` intentionally untouched (its
  content is M2-produced by PE skills, not seeded by this batch)." Edit the
  corresponding Batch 5 AC bullet (~line 407) to match.
- **Amendment 2 (M2.6 sole-ownership):** two sites to edit:
  (a) RFC line ~115 (M2.6 JIT table) "Initiative brief artifact +
  `docs/product/initiatives/_template.md` seed" → "Initiative brief artifact
  using the `docs/product/initiatives/_template.md` seeded in Batch 5 (do not
  recreate)."
  (b) RFC line ~418 (M2 acceptance criterion) `- [ ] Initiative brief artifact
  + docs/product/initiatives/_template.md seed` → same "using the Batch 5-seeded
  template" wording, so both the JIT table and the AC agree.
- **Amendment 3 (remove collapsed spec from worked example):** edit RFC line
  ~324 in § Proposed design's Bootstrap example queue — remove the
  `"spec/m1-shaping-seeds"` line so the example reflects the actual single-spec
  Batch 5 delivery.
- **rfc:139 ("New initiative and shaping artifact seeds") is left unchanged.**
  That line is the Reviewer brief's Change-if-accepted summary, which refers
  to M2's shaping artifact seeds (vision docs, capability maps, opportunity
  assessments produced by PE skills at M2) — not a `docs/product/shaping/`
  directory seed. The wording is ambiguous but does not contradict this batch's
  no-op decision; amending it would require re-reading M2's full scope.
  Record in the PR description why it was left.

**Done when:** all T6a test assertions pass by reading the amended RFC.

---

### T6: Update `docs/specs/README.md`

**Depends on:** T0, T1, T2, T3, T4, T5, T6a

**Touches:** `docs/specs/README.md`

**Tests:**
- `grep "m1-governance-integration" docs/specs/README.md` matches (registry
  housekeeping — no backing AC; this task is outside the spec's AC coverage
  but is required by project convention to keep the spec registry current).

**Approach:**
- Verify `m1-governance-integration` is present in the Active specs table
  (already added during spec authoring). Confirm the row is accurate and update
  status from Draft to whatever the current state is.

**Done when:** spec appears in the active list.

## Rollout

Pure content change — no infrastructure, no migration, no flag, no external
integration. Reversible: all changes are markdown; reverting is a PR revert.
The `new-rfc` skill edit is projected by `make build-self`; the projection
step is the deployment.

Ship order within the PR: T0 (workspace cleanup) can merge first; T1–T4
(seeds + reference doc) are independent; T5 (skill edit) depends on T4 and
should be the last authored task; T6 (README) depends on all and is the
final housekeeping step.

## Risks

- **Projection drift:** editing the source skill without running `make
  build-self` leaves the projected copy stale. Mitigated by: T5's "Done when"
  condition requires the projection to be clean.
- **Prompt text disagreement:** adopters reading the `new-rfc` skill may have
  cached the old "After acceptance" prose. Mitigated by: the change is
  additive (the existing list is preserved); no breaking change.
- **`workspace.toml` parse ambiguity:** the skill is read by an LLM, not a
  TOML parser; if the prose instructions for the queue append are ambiguous,
  the agent may produce malformed TOML. Mitigated by: the skill prose includes
  a worked example using the exact `{path = "...", needs = "..."}` format from
  RFC-0064 D7; the reference doc (T4) is cited inline.
- **initiatives/ double-ownership with M2.6:** RFC-0064 M2.6 also lists
  `docs/product/initiatives/_template.md` as a seed. Since Batch 5 ships
  before M2 begins, the file exists before M2.6 runs; M2.6 must use this
  file, not recreate it. This is explicitly noted in the spec Assumptions
  and is a candidate for an RFC-0064 erratum in the PR.

## Changelog

- 2026-07-18: initial plan
- 2026-07-18: round 1 adversarial review — added T0 (workspace.toml cleanup);
  fixed T4 prefix enumeration (D7 cross-queue vs D9 shaping-type); scoped T2
  to directory-only seed (no column schema — M3 owns that); aligned skip-note
  literal in T5; added T6 traces to AC2
- 2026-07-18: round 2 adversarial review — removed discoverability clause from
  Objective (blocker: no AC/task backed it and Boundaries contradicted it);
  added edge case for present-but-missing-initiative-section to failure/edge
  cases and AC1; added T6a to amend RFC-0064 Batch 5 AC (RFC is Draft —
  direct edit, no erratum); aligned Testing Strategy grep to `ini-`
- 2026-07-18: round 3 adversarial review — added manual QA step 3 for
  missing-initiative-section (blocker: AC1 bullet 4 had no verification);
  fixed T4 cross-initiative grep to `grep -E "ini-[0-9]{3}:work:"` (concern:
  `ini-` matched RFC filename); updated Assumption + added AC4 for RFC
  amendments (concern: spec said optional erratum, plan said required direct
  edit); extended T6a to amend M2.6 sole-ownership; fixed "post-M1 backlog"
  phrasing to "post-M1 milestone per RFC-0064 D7"; fixed Objective "four seeds
  land" to "four cases handled (three seeded, one left)"
- 2026-07-18: rounds 4–5 adversarial review — extended T6a Amendment 2 to
  also cover rfc:418 (M2 AC, not just M2.6 JIT table) and noted rfc:139 is
  left unchanged with rationale; added Batch 5 AC-bullet (rfc:407) to T6a
  tests; updated Testing Strategy AC4 bullet to include rfc:407 and rfc:418;
  fixed T6 AC citation from false "AC2" to "registry housekeeping, no AC"
- 2026-07-18: rounds 6–7 adversarial review — added T6a Amendment 3 to remove
  `"spec/m1-shaping-seeds"` from the RFC Bootstrap example queue (~line 324)
  to match T0's live workspace.toml removal; added corresponding test, AC4
  bullet, and Testing Strategy item (e); changed "all four T6a" to "all T6a"
  (dropped brittle count)
