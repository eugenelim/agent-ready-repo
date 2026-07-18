# Spec: m1-work-queue

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064
- **Brief:** none
- **Contract:** none
- **Shape:** n/a — skill prose extension; no application LLD

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Agents running `work-loop` are automatically oriented to the current initiative
and work queue at session start, and the queue is automatically updated when a
spec ships. At step 0 of every work-loop invocation (before PLAN begins), the
skill reads `workspace.toml` from the working directory and surfaces the active
initiative name, current milestone, and the spec path currently listed under
`[<slug>.work].active` — eliminating the need to read multiple files manually
before planning. When all gates pass and review is clean (the ship step), the
skill instructs the agent to edit `workspace.toml` in the working directory,
moving the current spec path from `[<slug>.work].active` to
`[<slug>.work].shipped`, and surfaces a one-line reminder to update
`docs/product/roadmap.md`.

If `workspace.toml` is absent from the working directory, both touch points
degrade to no-ops: existing work-loop behavior is completely unchanged — no
error, no diagnostic, no halt. The work queue is live end-to-end once this
batch ships: specs are claimed, executed, marked shipped, and the next ready
item surfaces automatically.

This spec covers RFC-0064 Batch 3 (milestone label M1.7). The change is
delivered by editing the `core` pack source SKILL.md for `work-loop` and
running `make build-self` to regenerate projected copies. No new executable
code, skill file, or artifact type is added.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit the work-loop **source** at
  `packs/core/.apm/skills/work-loop/SKILL.md`; run `make build-self` to
  regenerate the projected copy at `.claude/skills/work-loop/SKILL.md`.
  The two files must be byte-identical after build-self.
- Keep the degradation path (absent `workspace.toml`) as a first-class
  condition in both the step 0 section and the ship-step section — stated
  explicitly, not implied by silence.
- Keep all existing work-loop behavior (PLAN → EXECUTE → GATES → REVIEW →
  DECIDE → FIX, every anti-pattern, every reference section link) byte-identical
  to the pre-change version except for the two new touch points.
- Run all lint surfaces before declaring done: `make build-check`,
  `python tools/lint-agent-artifacts.py`, and
  `python tools/lint-agents-md.py`.

### Ask first

- Any change to the `workspace.toml` schema (the schema is owned by Batch 2
  and governed by RFC-0064 D2–D4; this spec consumes the schema, never changes
  it).
- Any extension beyond the two named behaviors (step 0 read, ship-step write)
  — for example, moving an entry from `[work].queue` to `[work].active` (that
  transition is `check-workspace`'s job, not work-loop's; not in scope for
  this batch).
- Treating the roadmap reminder as anything more than a surfaced one-liner
  (no auto-edits to `docs/product/roadmap.md` in this batch).

### Never do

- **Add executable code, a new skill, or a new artifact type as the feature
  mechanism.** The vehicle is SKILL.md prose additions only. No new Python
  script, no new tool, no hook that auto-runs.
- **Manage the `queue → active` transition.** That is `check-workspace`'s
  responsibility. work-loop reads `[work].active` as-is; it does not pop from
  `queue` or claim a spec.
- **Emit an error or halt the loop when `workspace.toml` is absent.** Silent
  no-op is the specified degradation path.
- **Edit the projected `.claude/` copy directly.** `make build-self` reverts
  it; the source is always the fix point.

## Testing Strategy

This change is skill-file prose — no executable logic — so verification is
**goal-based** plus **manual QA**; no TDD (nothing carries a compressible
invariant the language runtime can check).

- **Projection correctness** (source → projected path byte-identical after
  build-self; lint gates clean): goal-based — `make build-self` then
  `make build-check`, `tools/lint-agent-artifacts.py`, and
  `tools/lint-agents-md.py` all exit 0.
- **Content presence** (step 0 section present in the projected SKILL.md;
  ship-step addition present; absent-file degradation stated in both;
  existing step numbering and section structure unaltered): goal-based —
  `grep` checks on the projected `SKILL.md`.
- **Behavioral correctness** (step 0 surfaces initiative context when
  `workspace.toml` is present; existing behavior is unchanged when absent;
  ship-step edit instruction is present and correct; roadmap reminder
  surfaces): manual QA — exercise the built skill artifact end-to-end through
  its documented workflow, observe the actual output, and record it.

## Acceptance Criteria

- [x] At **step 0** of work-loop (before PLAN begins), if `workspace.toml`
  is present in the working directory, the skill reads it and surfaces, in
  a clearly labelled orientation block, the active initiative name (from
  `[<slug>].name`), the current milestone (from `[<slug>].milestone`), and
  the spec path currently listed in `[<slug>.work].active` (if the array is
  non-empty). The block is bounded so the agent can identify and act on the
  context without ambiguity.

- [x] When `workspace.toml` is absent from the working directory, step 0 is
  a no-op: the loop enters PLAN immediately, with no error, no diagnostic,
  and no behavioral change relative to the pre-change skill.

- [x] When `workspace.toml` is present but `[<slug>.work].active` is empty
  (no spec currently claimed), step 0 surfaces the initiative name and
  milestone only, and does not emit an error.

- [x] At the **ship step** (all GATES green, REVIEW clean, end-of-session
  checklist reached), if `workspace.toml` is present and
  `[<slug>.work].active` contains a spec path matching the current work, the
  skill instructs the agent to edit `workspace.toml` in the working
  directory: move that spec path from `[<slug>.work].active` to
  `[<slug>.work].shipped`, and stage the file change as part of the
  shipping PR diff.

- [x] After the `workspace.toml` edit instruction, the skill surfaces a
  one-line reminder: update `docs/product/roadmap.md` to reflect the shipped
  spec.

- [x] When `workspace.toml` is absent at ship time, the ship step completes
  normally — no workspace.toml edit attempted, no roadmap reminder surfaced.

- [x] All existing work-loop behavior (PLAN, EXECUTE, GATES, REVIEW, DECIDE,
  FIX, termination, capture-learnings, context hygiene, unattended loops,
  anti-patterns, and every reference-section link) is unaltered; a `diff`
  between the pre-change and post-change source shows only the additions at
  step 0 and the ship step.

- [x] After `make build-self`, the source at
  `packs/core/.apm/skills/work-loop/SKILL.md` and the projected copy at
  `.claude/skills/work-loop/SKILL.md` are byte-identical.

- [x] `make build-check`, `python tools/lint-agent-artifacts.py`, and
  `python tools/lint-agents-md.py` all exit 0.

## Assumptions

- Technical: work-loop source is `packs/core/.apm/skills/work-loop/SKILL.md`;
  its projected copy at `.claude/skills/work-loop/SKILL.md` is byte-identical
  before and after build-self (source: `diff` between the two files returned
  no output).
- Technical: `workspace.toml` is committed to repo root (Batch 2 shipped); its
  `["ini-002".work]` sub-table has exactly three arrays: `active`, `shipped`,
  and `queue` (source: `workspace.toml` lines 41–43).
- Technical: this spec's path `spec/m1-work-queue` is already pre-seeded in
  `workspace.toml` queue (source: `workspace.toml` lines 44–46).
- Technical: `make build-self` target exists and runs
  `tools/build_gate_chain.py build-self` to regenerate projected artifacts
  (source: `Makefile` lines 44–55).
- Process: this spec is constrained by RFC-0064 Batch 3 AC; no separate ADR
  governs this change; RFC-0064 is the governing authority (source: RFC-0064
  § Acceptance Criteria, Batch 3).
- Process: the `queue → active` transition is out of scope for this batch;
  `check-workspace` (Batch 2) is the skill that surfaces and claims work items
  (source: RFC-0064 queue-unlock table, M1.7 row).
