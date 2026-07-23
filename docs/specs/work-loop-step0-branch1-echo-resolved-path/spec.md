# Spec: work-loop-step0-branch1-echo-resolved-path

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0067 §Change C (spec-C-workloop-argless-resume)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: light (no risk trigger fired)

## Objective

When `work-loop`'s argless Step 0 resolves to Branch 1 (exactly one active
spec across all active initiatives), the agent silently begins without stating
which spec it resolved to. A stale `.active` entry pointing at the wrong spec
goes undetected until PLAN is well under way. This spec adds a one-line
resolved-path echo to the Branch 1 orientation block, matching the explicitness
Branch 3 already provides when it lists all active paths.

The fix touches: `packs/core/.apm/skills/work-loop/SKILL.md` (the source)
and `docs/specs/spec-C-workloop-argless-resume/spec.md` (AC2). Running
`make build-self FORCE=1` propagates the source change to the projected copy.

## Boundaries

### Always do

- Edit the work-loop source in `packs/core/.apm/skills/work-loop/SKILL.md`; run `make build-self FORCE=1` to propagate.
- Update `docs/specs/spec-C-workloop-argless-resume/spec.md` AC2 Branch 1 clause to reflect the echo.
- Keep the echo line concise: one line in the orientation block, e.g. "Beginning on `docs/specs/<slug>/spec.md`".

### Ask first

- Any change to how the path is formatted (e.g. including `plan.md` alongside `spec.md` in the echo).

### Never do

- Change Branch 2 or Branch 3 behavior.
- Add new output fields to the orientation block beyond the path echo.
- Change how the argless invocation path resolves the spec (resolution logic is unchanged).

## Testing Strategy

**Goal-based check** — the change is a content edit to a Markdown skill file.
No runtime logic changes; verification is: (a) the correct text appears in
the source SKILL.md and the shipped spec AC2, and (b) `make build-self FORCE=1`
and `make build-check` exit 0.

## Acceptance Criteria

- [x] **AC1.** `packs/core/.apm/skills/work-loop/SKILL.md` Step 0 Branch 1 bullet
  (the "Exactly one →" bullet inside the Active spec point) instructs the agent
  to state the resolved spec path in the orientation block — e.g.
  "Beginning on `docs/specs/<slug>/spec.md`" — before proceeding to PLAN.
- [x] **AC2.** The closing resolution paragraph in Step 0
  (`"if exactly one active item, strip the \`spec/\` prefix, then read..."`)
  is updated to include the same echo instruction, keeping the bullet and the
  paragraph consistent.
- [x] **AC3.** `docs/specs/spec-C-workloop-argless-resume/spec.md` AC2 Branch 1
  clause is updated to reflect that the resolved path is stated in the orientation
  block before beginning (replacing "begin the loop on that spec without asking"
  with language that includes the echo).
- [x] **AC4.** `make build-self FORCE=1` exits 0 (the projected
  `.claude/skills/work-loop/SKILL.md` matches the updated source).
- [x] **AC5.** `make build-check` exits 0.

## Assumptions

- Technical: the work-loop SKILL.md source is at `packs/core/.apm/skills/work-loop/SKILL.md`; `make build-self FORCE=1` propagates it to `.claude/skills/work-loop/SKILL.md` (source: CONVENTIONS §Pack source-of-truth split, verified by prior specs).
- Technical: no test file asserts on the SKILL.md text content; the only gate is `build-check`, which checks the projected copy for drift (source: `make build-check` chain in `tools/build_gate_chain.py`).
- Process: the quality-engineer flagged this gap (stale `.active` entry undetected) in the `spec-C-workloop-argless-resume` review; the fix is a prose-only clarification, no new activation surface (source: `workspace.toml [backlog].open` entry `work-loop-step0-branch1-echo-resolved-path`).
