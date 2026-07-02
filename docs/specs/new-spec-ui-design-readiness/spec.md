# Spec: new-spec-ui-design-readiness

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0042 (agent additions keyed to loop/work-type); ADR-0047 (experience-reviewer trigger scoping)
- **Brief:** none
- **Contract:** none
- **Shape:** n/a — methodology/prose change (`new-spec` SKILL.md amendment); no application LLD

`Mode: full (structural or public-interface change — shipped skill procedure change)`

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

When a `new-spec` author confirms `Shape: ui`, the skill has no guidance for
baking design intent into the spec before the Acceptance Criteria are written.
The result: UI feature specs routinely ship with only functional ACs — observable
behavior the code must produce, but no design-intent criteria the rendered surface
must satisfy. A spec like this drives an implementation that clears lint, tests,
and adversarial review, yet ships with no design sense.

The `work-loop` pre-EXECUTE design-intent pass (added in core 0.8.0) catches this
at PLAN time — but only after the spec has already locked in functional-only ACs.
This spec closes the earlier gap: add a conditional step 4d to `new-spec` that fires
on `Shape: ui`, establishes design-readiness (grounded reference + existing-surface
audit) before the ACs are written, and makes design-intent ACs mandatory for ui-shaped
specs. The result is a spec that starts with design sense, not one that has to acquire
it mid-implementation.

Success is: (P1) a new step 4d in `new-spec` that fires on `Shape: ui`; (P2) step 4d
checks for a grounded aesthetic reference and offers `aesthetic-direction` if absent;
(P3) step 4d offers `design-critique` on existing affected surfaces; (P4) step 4d
requires at least one design-intent AC in the spec; (P5) select-or-note fallback for
when the experience pack is absent.

## Boundaries

### Always do
- Edit the **source** `packs/core/.apm/skills/new-spec/SKILL.md`. Run
  `make build-self` after to regenerate projections.
- Insert step 4d between step 4c and step 5 — same conditional-step pattern as 4b
  (contract authoring) and 4c (shape + stack).
- The step must reference the `work-loop` pre-EXECUTE pass as the later-stage
  analogue, so adopters understand the two-stage relationship.
- Bump core pack to 0.9.0: `packs/core/pack.toml` AND
  `packs/core/.claude-plugin/plugin.json`.
- Add a `docs/product/changelog.md` `[Unreleased]` entry.

### Ask first
- Adding a canonical output path for `aesthetic-direction` docs — the skill does
  not currently specify where the doc lives; adding a convention is an ADR-level
  decision.
- Making `aesthetic-direction` a mandatory prerequisite (the spec calls it
  select-or-note, not mandatory; changing the posture is a separate decision).

### Never do
- Touch the risk-triggers block in `work-loop`.
- Change when or how `work-loop`'s pre-EXECUTE design-intent pass fires — step 4d
  and that pass are complementary, not substitutes.
- Make step 4d fire for `Shape: service`, `data`, `integration`, or `mixed` — the
  design lens applies to user-facing surfaces only.

## Acceptance Criteria

- [x] **AC1.** `new-spec` SKILL.md contains a step 4d that fires when `Shape: ui`
  is confirmed in step 4c.
- [x] **AC2.** Step 4d checks whether a grounded aesthetic reference exists (by
  searching for a file matching `# Aesthetic direction:` in the repo) and offers to
  run `aesthetic-direction` if none is found.
- [x] **AC3.** Step 4d checks whether existing screens or flows are affected and
  offers to run `design-critique` on existing surfaces before ACs are written.
- [x] **AC4.** Step 4d requires the spec Objective to name the primary user task
  and an aesthetic goal from the grounded reference.
- [x] **AC5.** Step 4d requires at least one design-intent AC — observable from the
  rendered surface, not derivable from code — with concrete example shapes provided.
- [x] **AC6.** Step 4d carries the select-or-note fallback: if the experience pack
  is absent, note it in Assumptions and proceed.
- [x] **AC7.** Step 4d references `work-loop`'s pre-EXECUTE design-intent pass as
  the later-stage analogue, naming the shared failure mode both target.
- [x] **AC8.** `make lint-packs` passes clean.
- [x] **AC9.** `make build-self` completes without error and marketplace.json shows
  `"version": "0.9.0"` for the core pack.

## Testing Strategy

Verification mode: **Visual / manual QA** — this is a prose skill document;
correctness is demonstrated by reading the amended skill and confirming step 4d
would prompt the right behavior on a sample scenario.

**Scenario A (experience pack installed, no existing reference):** run `new-spec`
for "agent-docs-overhaul" with Shape: ui. Expected outcome: step 4d fires; agent
checks for `# Aesthetic direction:` and finds nothing; agent offers to run
`aesthetic-direction`; user confirms they'll handle it separately; agent notes the
design intent is ungrounded and suggests the Objective name at least one aesthetic
goal; final ACs include at least one design-intent criterion.

**Scenario B (experience pack installed, reference exists):** run `new-spec` for
"homepage-redesign" with Shape: ui. An `aesthetic-direction` doc exists. Expected
outcome: step 4d fires; agent finds the reference; skips the offer; proceeds to
ask whether existing screens are affected; writes at least one design-intent AC
grounded in the named aesthetic goal.

**Scenario C (experience pack absent):** run `new-spec` for a ui-shaped feature
with no experience pack installed. Expected outcome: step 4d fires; agent notes
experience pack absent in Assumptions; skips the offers; proceeds with functional
ACs only. No silent pass.

**Scenario D (Shape: service):** run `new-spec` for a backend service feature.
Expected outcome: step 4d does NOT fire. Only steps 4a–4c and 4b run as applicable.

**No unit tests** — skill is pure prose.

## Assumptions

1. **Verified:** `new-spec` step 4c already resolves `Shape:` before step 4d fires —
   the trigger is clean (`packs/core/.apm/skills/new-spec/SKILL.md` step 4c).
2. **Verified:** `aesthetic-direction` is in the experience pack and produces a doc
   whose first heading is `# Aesthetic direction:` (confirmed from template).
3. **Verified:** `design-critique` is in the experience pack and accepts an existing
   surface as input.
4. **Decided:** select-or-note posture for experience-pack absence matches ADR-0047
   and the security-reviewer / experience-reviewer pattern already in `work-loop`.
5. **Decided:** step 4d does not add an ADR — it follows the same rationale as
   ADR-0047 (experience-reviewer as conditional specialist for user-facing surface
   work) and extends it to spec-authoring time. No new architectural decision.
