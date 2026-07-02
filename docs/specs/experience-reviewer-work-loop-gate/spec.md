# Spec: experience-reviewer-work-loop-gate

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0042 (agent additions keyed to loop/work-type); ADR-0014 (rigor scales with risk); backlog items `experience-reviewer-as-work-loop-gate` and `experience-loop-trigger-for-site-changes`
- **Brief:** none
- **Contract:** none
- **Shape:** n/a — methodology/prose change (`work-loop` SKILL.md edit + new ADR); no application LLD

`Mode: full (structural or public-interface change — work-loop REVIEW section)`

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Agents running the `work-loop` on a change that produces a user-facing surface
(a new page, a redesigned screen, a component, a docs page) get an
`experience-reviewer` pass as a conditional specialist reviewer gate — the same
pattern as a security-boundary diff getting a `security-reviewer` pass. Today the
specialist reviewer roster covers code correctness (`adversarial-reviewer`),
security (`security-reviewer`), and quality (`quality-engineer`), but not design
quality. A frontend page can clear all three and still ship with no design sense,
because no reviewer in the roster holds a design lens.

**Trigger scoping decision (ADR-0047):** the experience-reviewer gate applies to
full-mode work only. Net-new pages and substantial redesigns already route to full
mode under the existing "Structural or public-interface change" risk trigger
(publishing new content to a public site IS publishing a public interface). Light-mode
user-facing changes (minor copy edits, small ordering tweaks) get only the
pre-EXECUTE design-intent recommendation, not the mandatory review gate. The ADR
records this decision and the argument explicitly.

Success is: (P1) work-loop documents a pre-EXECUTE design-intent pass for
user-facing surface work (recommend `aesthetic-direction` / `design-critique`
authoring-time skills before writing code); (P2) `experience-reviewer` is added to
the specialist reviewer roster in the REVIEW section, triggered when the diff
crosses a user-facing surface in full-mode work, with the same select-or-note
fallback the other specialist reviewers carry; (P3) the end-of-session checklist
names `experience-reviewer` in the reviewer coverage line; (P4) an ADR records the
decision including the trigger scoping rationale.

## Boundaries

### Always do
- Edit the **source** `packs/core/.apm/skills/work-loop/SKILL.md`. Run
  `make build-self` after to regenerate projections.
- Write ADR-0047 documenting the decision, including the trigger-scoping rationale.
- Update `docs/adr/README.md` table with ADR-0046 (if missing) and ADR-0047.
- Bump core pack to 0.8.0: `packs/core/pack.toml` AND
  `packs/core/.claude-plugin/plugin.json`.
- Add a `docs/product/changelog.md` `[Unreleased]` entry.
- Close backlog items `experience-reviewer-as-work-loop-gate` and
  `experience-loop-trigger-for-site-changes` with shipped tombstones referencing ADR-0047.

### Ask first
- Adding a new risk trigger to the risk-triggers block — the trigger-scoping
  decision (ADR-0047) argues this is not needed; surface if implementation
  reveals a gap the existing "Structural or public-interface change" trigger
  doesn't cover.
- Changing the three core code-review lenses (adversarial-reviewer,
  security-reviewer, quality-engineer) — capped by ADR-0042.
- Creating a new reviewer agent — experience-reviewer already handles
  "generated screens" and this decision is within ADR-0042.

### Never do
- Touch the `<!-- risk-triggers:start --> ... <!-- risk-triggers:end -->` block
  in `packs/core/.apm/skills/work-loop/SKILL.md` or any of its four canonical
  copies. The existing triggers suffice; a new trigger is ADR-gated.
- Make experience-reviewer always-on (that would elevate it to the core-loop
  ceiling; conditional-on-surface is the ADR-0042-safe posture).

## Acceptance Criteria

- [x] **AC1.** Work-loop PLAN section includes a "Pre-EXECUTE design-intent pass
  (user-facing surface trigger)" bullet: recommends running `aesthetic-direction`
  (if no grounded reference exists) and/or `design-critique` before writing code
  for changes that produce a user-facing surface. Applies to both light and full
  mode as a recommendation.
- [x] **AC2.** Work-loop REVIEW section's specialist reviewer roster includes
  `experience-reviewer` after `quality-engineer`.
- [x] **AC3.** The experience-reviewer entry names its trigger: "for diffs that
  change what a reader or adopter sees — a new page, a redesigned screen, a pack
  card, a docs page — in full-mode work."
- [x] **AC4.** The entry carries the standard select-or-note fallback: "fallback
  if no `experience-reviewer` is installed: proceed and note it — absence of the
  experience pack is a named skip, not a silent pass." This matches the pattern
  the `security-reviewer` entry uses.
- [x] **AC5.** The entry names the artifact experience-reviewer receives: the
  orchestrator passes the **rendered output** (a described screen state, a
  screenshot, or a path to the built artifact) **plus the grounded aesthetic
  reference and constraints** (persona, outcome, platform surface) — not the
  code diff. Experience-reviewer's confirm-before-reviewing gate requires the
  grounded reference; the orchestrator must supply it.
- [x] **AC6.** End-of-session checklist reviewer-coverage line includes
  `experience-reviewer on user-facing surface diffs (full mode)`.
- [x] **AC7.** ADR-0047 is written, status Accepted, decision-makers eugenelim,
  and records: the mandatory/recommended split (mandatory for full-mode user-facing
  diffs under select-or-note; recommended for light-mode); why the existing
  "Structural or public-interface change" trigger covers net-new pages; why the
  gate is scoped to full mode; and how the decision clears ADR-0042's value test
  (different work type, forked-context independence, distinct surface/cadence).
- [x] **AC8.** `docs/adr/README.md` table includes ADR-0046 (if previously missing)
  and ADR-0047.
- [x] **AC9.** The risk-triggers block is byte-identical before and after
  `make build-self` across all canonical copies (grep confirms no edit to the
  `risk-triggers:start … risk-triggers:end` span).
- [x] **AC10.** `make lint-packs` passes clean.
- [x] **AC11.** `make build-self` completes without error.

## Testing Strategy

Verification mode: **Visual / manual QA** — this is a prose skill document and
an ADR; correctness is demonstrated by reading the amended work-loop and confirming
the design-intent pass and experience-reviewer gate are correctly wired.

**Scenario A (positive, experience pack installed):** apply the amended `work-loop`
to a full-mode task "add a new docs page for the experience pack." Expected outcome:
PLAN section recommends a design-intent pass (aesthetic-direction / design-critique);
REVIEW section uses experience-reviewer with the rendered page + grounded reference
+ constraints; checklist requires noting the result. Core reviewers unchanged.

**Scenario B (experience pack absent):** apply the amended `work-loop` to the same
full-mode task but experience pack is not installed. Expected outcome: the loop
proceeds and the final summary explicitly names "experience-reviewer: no matching
subagent installed; review skipped" — NOT a silent pass, NOT a loop failure.

**Scenario C (light mode, copy edit):** apply the amended `work-loop` to a
light-mode task "fix a typo on the Ottawa site homepage." Expected outcome: no
experience-reviewer gate fires (light mode → no specialist reviewer run); the
pre-EXECUTE design-intent pass recommendation appears in PLAN but is advisory only.

**No unit tests** — skill and ADR are pure prose.

## Assumptions

1. **Verified:** `experience-reviewer` handles "a generated screen" as a design
   artifact (`packs/experience/.apm/agents/experience-reviewer.md` scope list).
2. **Verified:** The experience-reviewer gate is within ADR-0042 (different
   loop/work-type — experience review vs. code-diff review; forked-context
   independence; distinct surface/cadence).
3. **Verified:** No existing spec or ADR conflicts with adding experience-reviewer
   as a conditional specialist; ADR-0042 explicitly admits this class of reviewer.
4. **Decided:** Trigger scoping is full-mode only. Net-new pages fire the existing
   "Structural or public-interface change" risk trigger → full mode → gate reachable.
   Light-mode changes get the recommendation, not the gate. Recorded in ADR-0047.
5. **Verified:** The risk-triggers block is NOT changed by this spec (grep-equality
   contract from work-loop-light-mode spec is maintained).
6. **Verified:** `packs/core/.claude-plugin/plugin.json` exists and must be bumped
   alongside `pack.toml` (marketplace.json aggregates version from plugin.json).
