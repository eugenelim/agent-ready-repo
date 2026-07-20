# Plan: spec-C-workloop-argless-resume

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Two focused edits to a single SKILL.md: the `description:` frontmatter and the Step 0 body. The shape: read the current `work-loop` SKILL.md, locate the precise line ranges for the first-path auto-pick language, replace them with the three-branch logic, and update the description. Then run `make build-self` to propagate the change to the projected copy.

The riskiest part is finding the exact first-path auto-pick language in the live SKILL.md (RFC-0067 references "line ~166" and "lines ~176–177", but these may have shifted since the RFC was written). The approach step must read the file before editing, not rely on the RFC's line numbers.

## Constraints

- RFC-0067 §Change C: the three-branch logic is normative; the "more than one active item" branch uses list-and-ask, not auto-pick by any heuristic.
- RFC-0025: no new skill; description + body change only.
- ADR-0054: "resume" is an activation phrase, not a skill name; this change makes `work-loop` respond to it.
- CONVENTIONS §Pack source-of-truth split: edit the source file (`packs/core/.apm/skills/work-loop/SKILL.md` or equivalent), not the projected copy; `make build-self` propagates.

## Construction tests

**Integration tests:** none beyond per-task goal-based checks.

**Manual QA (cross-cutting, runs at T3):**
Three invocation scenarios to verify the three branches:
1. `workspace.toml` with one active spec → loop begins without asking.
2. `workspace.toml` with zero active specs → "No active spec found — run `workspace-status`..." message.
3. `workspace.toml` with two or more active specs (or one initiative with a multi-element `.active` array) → list presented, user asked to pick.

## Tasks

### T1: Locate source file and exact first-path language

**Depends on:** none
**Touches:** packs/core/.apm/skills/work-loop/SKILL.md (read-only in this task)

**Tests:**
- Goal-based (precondition): the source SKILL.md file path is confirmed; the first-path auto-pick language and the singular-framing language are located at their exact line numbers before any edit.

**Approach:**
- Find the work-loop SKILL.md source path: `find packs/ -path "*/work-loop/SKILL.md"`.
- Read Step 0 in the SKILL.md to locate:
  - The "first path" auto-pick language (RFC-0067 references ~line 166).
  - The singular framing language ("The active spec path tells you which spec you are expected to be working on", RFC-0067 references ~lines 176–177).
- Note the exact line numbers for use in T2.

**Done when:** source path confirmed; first-path and singular-framing language located by line number.

---

### T2: Edit `description:` and Step 0 body

**Depends on:** T1
**Touches:** packs/core/.apm/skills/work-loop/SKILL.md (write)

**Tests:**
- Goal-based (AC1): `description:` field includes "resume", "continue", "keep going", "pick up where I left off", "let's get going" and explicitly notes that "resume the X project" (named-project phrasing) routes to `desk-research-project-status` rather than `work-loop`.
- Goal-based (AC2): Step 0 body contains the three-branch logic with the RFC-specified messages, gated on the argless invocation path.
- Goal-based (AC3): the first-path auto-pick language is absent from Step 0.
- Goal-based (AC4): the singular framing is updated to handle zero/multi-active states.
- Goal-based (AC5): the explicit spec-path argument path is unaffected (verify by reading that conditional branch).
- Goal-based (AC6): when `workspace.toml` is absent, Step 0 prose states the skip behavior ("no workspace.toml → PLAN begins immediately, no error").
- Goal-based (AC7): the description or evals note that "resume the X project" (named-project phrasing) disambiguates to `desk-research-project-status`, not `work-loop`.

**Approach:**
1. **Description update:** add the five trigger phrases to the `description:` frontmatter field (integrate with existing description text; do not replace existing triggers). Add a disambiguation note: bare "resume" / "continue" / "keep going" → this skill; "resume the X project" / "resume the X investigation" (named project) → `desk-research-project-status`.
2. **Step 0 body update:**
   - Add explicit `workspace.toml`-absent skip prose: "If no `workspace.toml` is present in the working directory, skip this step — PLAN begins immediately with no error."
   - Replace the existing Step 0 active-item logic (argless path only) with the three-branch implementation:
     ```
     Collect all active spec paths: for every ["ini-NNN"] section whose status =
     "active", collect every path in [work].active. Then:
     - Exactly one active item → begin the loop on that spec without asking.
     - Zero active items → "No active spec found — run `workspace-status` to see
       what's ready to start."
     - More than one active item → list all active paths and ask the user to pick
       before beginning.
     ```
   - Remove the first-path auto-pick language (the "first path in..." phrase).
   - Update the singular framing to acknowledge the multi/zero-item states (e.g., "When exactly one spec is active, the active spec path tells you which spec you are expected to be working on. When zero or more than one exist, Step 0 resolves which to begin before the rest of PLAN proceeds.").
3. Confirm the explicit-path-argument conditional (the branch where a user passes a spec path directly) is untouched.

**Done when:** AC1–AC7 hold when re-reading the edited SKILL.md.

---

### T3: Build-self + manual QA + gates

**Depends on:** T2
**Touches:** .claude/skills/work-loop/SKILL.md (generated)

**Tests:**
- Goal-based (AC8): `make build-self` exits 0; `.claude/skills/work-loop/SKILL.md` description and Step 0 reflect the edits; `make build-check` exits 0.
- Goal-based (AC9): `scripts/lint-spec-status.py` exits 0 on this spec.
- Manual QA: three-scenario verification (zero/one/multi active items) as specified in Construction tests above.

**Approach:**
- Run `make build-self` (with `FORCE=1` if needed).
- Read `.claude/skills/work-loop/SKILL.md` (projected) and confirm description and Step 0 match the source edits.
- Run `make build-check`.
- Run `scripts/lint-spec-status.py`.
- Run adversarial review; address any Blockers.

**Done when:** AC8 + AC9 hold; adversarial-reviewer returns `Clean — ready to commit.`

## Rollout

Edit to a single source SKILL.md + projected-tree rebuild. No pack manifest change (no new skill added to the skills array). No external dependency. Backward-compatible: existing `work-loop skill <path>` invocations with an explicit path argument are unaffected; only the argless (no-path-argument) case gains the three-branch behavior.

## Risks

- Line numbers in the RFC (~166, ~176–177) may have shifted since RFC-0067 was written. Mitigation: T1 reads the current file before editing and locates the language by content, not line number.
- The description field update may interact with the existing `description:` content in unexpected ways if the SKILL.md uses a multi-line YAML description block. Mitigation: T1 includes reading the description field format before T2 edits it.

## Changelog

- 2026-07-20: initial plan, authored alongside the spec for RFC-0067 spec/plan/ADR follow-on work.
