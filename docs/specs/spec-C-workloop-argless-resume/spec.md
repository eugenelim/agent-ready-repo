# Spec: spec-C-workloop-argless-resume

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0067](../../rfc/0067-session-arc-conventions-and-pack-workflow-guide.md) — driving RFC; Change C defines the description triggers, the three-branch Step 0 behavior, and the reconciliation with existing Step 0 text
  - [RFC-0025](../../rfc/0025-work-loop-light-mode-and-risk-based-escalation.md) — no-new-skill precedent: description + body changes to `work-loop` are sufficient when no new activation surface is needed
  - [ADR-0054](../../adr/0054-session-arc-verb-taxonomy-and-pack-type-classification.md) — "resume" is an activation phrase, not a skill name; argless work-loop resume is the correct implementation surface
  - [Spec B](../spec-B-pack-status-skills/spec.md) — implementation sequencing: AC7's near-miss routing references `desk-research-project-status`, which Spec B creates; Spec C should ship after or with Spec B so the named skill exists
- **Contract:** none — SKILL.md body and description edit only; no API contract.
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A user who invokes `work-loop` without a spec path argument — or who types "resume", "continue", "keep going", "pick up where I left off", or "let's get going" — gets context-appropriate guidance without manual lookup. When exactly one spec is active across all initiatives, the loop begins on that spec. When zero specs are active, the user is pointed to `workspace-status`. When more than one spec is active, the loop lists them all and asks the user to pick. The existing "auto-pick the first path" behavior is removed. No new skill is created.

## Boundaries

### Always do

- Implement as a description + body change to the `work-loop` SKILL.md only — per RFC-0025 no-new-skill precedent.
- Replace the first-path auto-pick language at the affected Step 0 lines (SKILL.md ~line 166 "the first path in `["<slug>".work].active`" and lines ~176–177 singular framing) with the three-branch logic defined in RFC-0067 §Change C.
- Apply the disambiguation behavior consistently: "more than one active item" fires whether from a single initiative's multi-element `.active` array or across multiple initiatives.
- Keep the projected copy of `work-loop` SKILL.md in sync via `make build-self`.

### Ask first

- Changing the exact wording of the zero-active-items message (beyond correcting a typo relative to RFC-0067 §C).
- Changing the disambiguation behavior for the "more than one" branch (e.g., auto-pick by initiative priority rather than list-and-ask).
- Adding a fourth branch (e.g., handling malformed `workspace.toml` sections).

### Never do

- Create a new `workspace-resume` skill or any other new skill for this change — per RFC-0025 precedent and ADR-0054 (resume is an activation phrase, not a skill name).
- Auto-pick the first path when multiple active items exist — list-and-ask is the ADR-0054-normative behavior.
- Remove the explicit spec-path argument behavior — argless resume is an additive Step 0 branch; explicit spec arguments continue to work unchanged.

## Testing Strategy

All criteria use **goal-based check**: the SKILL.md body is read against the spec's three-branch contract and the removed first-path language. The change is to a markdown skill body; no compiled artifact. **Manual QA** — five invocation scenarios:
1. `workspace.toml` present, one active spec → loop begins without asking.
2. `workspace.toml` present, zero active specs → "No active spec found…" message.
3. `workspace.toml` present, two active specs in one initiative → list presented, user asked to pick.
4. `workspace.toml` present, two active specs across two initiatives → list presented (same Branch 3 path as scenario 3).
5. `workspace.toml` absent → PLAN begins immediately, no error (AC6).
6. Explicit spec path passed (e.g. `work-loop docs/specs/foo/spec.md`) → three-branch logic skipped entirely (AC5).

## Acceptance Criteria

- [x] **AC1.** `work-loop` SKILL.md `description:` field includes all five RFC-0067 §C trigger phrases: "resume", "continue", "keep going", "pick up where I left off", "let's get going".
- [x] **AC2.** The three-branch logic governs only the **argless invocation path** (no spec path argument passed to `work-loop`). When `workspace.toml` is absent, the existing skip behavior is preserved: Step 0 exits silently and PLAN begins immediately, as today. When `workspace.toml` is present and the active array logic runs, the three branches are:
  - Branch 1 (exactly one active item across all `["ini-NNN"]` sections with `status = "active"`): begin the loop on that spec without asking.
  - Branch 2 (zero active items, `workspace.toml` present): surface "No active spec found — run `workspace-status` to see what's ready to start."
  - Branch 3 (more than one active item, from a single initiative's multi-element `.active` array or across multiple initiatives): list all active paths and ask the user to pick before beginning.
- [x] **AC3.** The first-path auto-pick language is removed: the phrase "the first path in `[\"<slug>\".work].active`" (or equivalent) no longer appears in Step 0.
- [x] **AC4.** The singular framing ("The active spec path tells you which spec you are expected to be working on") is updated to handle the pending-user-pick state (zero or multi-item cases) — the language no longer implies exactly one active spec always exists.
- [x] **AC5.** Explicit spec-path argument invocations (user passes a path to `work-loop`) are unaffected — the three-branch logic is conditional on no path argument being provided.
- [x] **AC6.** The `workspace.toml`-absent skip behavior is explicitly preserved in the Step 0 prose: when no `workspace.toml` is present in the working directory, Step 0 does not error and PLAN begins immediately.
- [x] **AC7.** The work-loop `description:` field or evals near-miss cases distinguish bare "resume" / "continue" (routes to `work-loop`) from named-project phrasing "resume the X project" / "resume the X investigation" (routes to `desk-research-project-status`, not `work-loop`).
- [x] **AC8.** The projected copy of `work-loop` SKILL.md (`.claude/skills/work-loop/SKILL.md` and any adapter-projected equivalents) is updated via `make build-self`; `make build-check` exits 0.
- [x] **AC9.** `scripts/lint-spec-status.py` exits 0 on this spec.

## Assumptions

- Technical: `work-loop` SKILL.md's Step 0 contains the exact first-path auto-pick language at approximately lines 166 and 176–177 (source: RFC-0067 §Change C "Reconciliation" paragraph); the implementing agent must read the current SKILL.md to find the exact lines before editing.
- Technical: the `work-loop` SKILL.md is a source file under `packs/core/.apm/skills/work-loop/` (or equivalent source path); its projected copy is regenerated by `make build-self` (source: CONVENTIONS §Pack source-of-truth split).
- Process: no new skill is needed — per RFC-0025 precedent, a description + body change is sufficient when the change adds no new activation surface beyond work-loop itself (source: RFC-0067 §Options considered, Change C axis).
