# Spec: product-engineering-shaping-doctrine

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Mode:** Full (risk triggers: structural/public-interface change — 15 SKILL.md files + skill directory rename; multi-feature — PE skills + XD cross-references + web content + guides; destructive/irreversible — alias-free rename, no compatibility alias)
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0071](../../rfc/0071-digital-experience-doctrine.md) (ini-003 M2b, D2, D6), [RFC-0066](../../rfc/0066-experience-pack-surface-genre-and-skill-uplift.md) (D7 — voice-and-microcopy rename deferred here), [ADR-0038](../../adr/0038-rename-design-craft-pack-to-experience.md) (alias-free rename precedent)
- **Brief:** none
- **Shape:** integration — PE shaping skills updated; ux-writing skill renamed; web journey page created; how-to guides added
- **Contract:** Digital Experience Contract `schema-version: "1.0"` (PE section fields populated by updated skills; no schema change to the contract template)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The PE shaping flow produces a complete brief but doesn't require a thin
end-to-end slice, first-success operationalization, or post-launch learning
contract. Gate language uses internal step IDs. The `voice-and-microcopy` skill
name diverges from the three-way copy boundary (`copy-direction` / `ux-writing`
/ `content-design`) settled in RFC-0066/RFC-0071.

This spec delivers:

1. **Expanded `place-bet` betting table** — four new required fields added to
   `bet.md`: `thin-slice` (one user can begin a real task, reach a meaningful
   result, encounter and recover from one material failure, and produce
   instrumentation), `first-success-event` (operationalized: what "adopted"
   looks like for one user 30 days out), `specialist-lenses` (default:
   product/experience/architecture/safety; conditional additions named), and
   `learning-contract` (what to measure, cadence, pivot trigger).

2. **Evidence ladder in `de-risk-intent`** — each assumption in the
   validation-hook is classified on a five-level evidence ladder:
   `observed | supported | inferred | assumed | unknown`. The riskiest
   assumption to test is the one at the lowest evidence level.

3. **Plain-English gate checks in `place-bet`** — anti-pattern additions
   name the specific gate failures by outcome: "options have no first-success
   dimension", "thin-slice missing", "learning contract absent". No internal
   step IDs in gate language.

4. **`voice-and-microcopy` → `ux-writing` rename** — alias-free per ADR-0038.
   The live skill directory, SKILL.md frontmatter, and all operational
   cross-references in PE pack, XD pack, product-strategy pack, web content
   (.md, .toml, .json, .astro), and guides are renamed. Frozen historical
   records (docs/rfc/, closed docs/specs/ entries, prior
   docs/product/changelog.md history) are NOT updated.

5. **PE pack version bump 0.12.2 → 0.13.0** — doctrine additions + rename = minor bump.

6. **Updated evals with weak fixtures** — ux-writing `eval_queries.json` gains
   weak fixtures for two copy-boundary cases: handoffs that say "make it
   intuitive" (a direction, not copy) and structural layout requests without
   copy states. `diverge-solutions` `eval_queries.json` gains weak fixtures for
   trivial-variation option sets and component-layer input. AC5/AC6
   (thin-slice, evidence ladder) are prompt-only presence checks; place-bet
   doctrine coverage requires adding place-bet to `[pack.evals]` which is
   deferred (see Ask first).

7. **New PE journey page** — `web/src/content/journeys/product-engineering.md`
   formatted like `product-strategy.md`. Thin-slice and learning-contract steps
   are visible in the journey body. `whatChanges` frontmatter field references
   the Digital Experience Contract, completing backlog item
   `digital-experience-contract-pe-journey-xref`.

8. **Updated how-to guides** — `place-a-bet.md` gains a `## How to define a
   thin slice` section; new `write-a-post-launch-learning-contract.md` how-to
   added to `docs/guides/product-engineering/how-to/`.

9. **Backlog item closed** — `digital-experience-contract-pe-journey-xref` is
   removed from `[backlog].open` in workspace.toml when the PE journey page ships.

## Boundaries

### Always do

- Rename `packs/product-engineering/.apm/skills/voice-and-microcopy/` →
  `ux-writing/`; update SKILL.md `name:` frontmatter field and `evals.json`
  `skill_name` field
- Update ALL operational cross-references to `voice-and-microcopy` across all
  live file types: `packs/` (.md, .toml, .json), `web/` (.md, .astro),
  `docs/guides/` (.md)
- Leave frozen historical records unchanged: `docs/rfc/`, closed
  `docs/specs/` entries, prior `docs/product/changelog.md` history.
  Descriptive comments in `workspace.toml` that *name* the rename (e.g., the
  ini-003 decision-record comment explaining that `voice-and-microcopy → ux-writing`
  is folded here) are descriptive and may keep the old name — they are not
  operative entries.
- Add all four new betting table fields to `place-bet/SKILL.md`; thin-slice
  definition uses exact wording: "one user can begin a real task, reach a
  meaningful result, encounter and recover from one material failure, and
  produce instrumentation"
- Add evidence-ladder five-level classification to `de-risk-intent/SKILL.md`
  validation-hook format; riskiest-assumption selection criterion references
  "lowest evidence level"
- Add anti-patterns to `place-bet/SKILL.md` that name specific gate failures
  by outcome (no internal step ID references)
- Version bump pack.toml 0.12.2 → 0.13.0; update evals list
  `voice-and-microcopy` → `ux-writing`
- Run `make build-check` and `python3 tools/check-contract-drift.py --root .`;
  both must exit 0
- Add [Unreleased] changelog entry covering ux-writing rename and doctrine changes
- Create `web/src/content/journeys/product-engineering.md` with a `whatChanges`
  frontmatter field that references the Digital Experience Contract
- Remove `digital-experience-contract-pe-journey-xref` from `[backlog].open` in
  `workspace.toml` when the PE journey page ships
- Move `spec/product-engineering-shaping-doctrine` from queue to shipped in
  `workspace.toml`

### Ask first

- Changing Digital Experience Contract schema (PE section field names or
  required-tier annotations) — each change requires re-running the drift check
  across all four packs
- Adding new skills to the PE pack beyond the ux-writing rename
- Changing the canonical thin-slice definition (four-criterion wording is from
  RFC-0071)
- Adding an evals entry for `place-bet` to `[pack.evals]` in pack.toml
  (requires calibration evidence)

### Never do

- Create a compatibility alias or redirect from `voice-and-microcopy` to
  `ux-writing` (alias-free is the ADR-0038 contract)
- Update frozen historical docs (docs/rfc/, prior closed docs/specs/ entries,
  prior changelog history entries)
- Change the Digital Experience Contract template in any pack's references/
  directory (that is spec/digital-experience-contract's domain)
- Add new top-level directories
- Modify pack.toml of packs other than product-engineering (XD/PS version bumps
  belong to their own specs in ini-003 queue)

## Assumptions

- Technical: PE pack version is 0.12.2 (`packs/product-engineering/pack.toml`)
- Technical: 205 occurrences of `voice-and-microcopy` across 44 files
  (grep count 2026-07-23); frozen historical docs are NOT updated per ADR-0038
- Process: ADR-0038 Accepted — alias-free rename precedent; live surface renamed,
  frozen governance bridged, no install-time alias
- Process: RFC-0066 D7 deferred the rename; RFC-0071 D2 confirmed it folds here
- Technical: Digital Experience Contract PE section already defines all contract
  fields this spec's skills populate; no schema change needed
- Technical: `place-bet` betting table currently has 9 fields; 4 new required
  fields added
- Technical: XD inbound files to update per RFC-0066 D7: tone-of-voice SKILL.md
  (3 refs), user-flow SKILL.md (2 refs), user-flow/assets/screen-brief-template.md
  (1), user-flow/assets/design-tool-handover-template.md (1),
  user-flow/references/screen-flow.md (1), design-review/references/quality-floor.md
  (1), content-design SKILL.md (2), experience-design README.md (2)
- Technical: `place-bet` has no evals directory and is not in `[pack.evals]` —
  new weak fixtures go to ux-writing and diverge-solutions evals only
- Technical: `web/src/components/marketing/PackCatalogue.astro` line 22 hard-codes
  `voice-and-microcopy` in the desc string — must be updated
- Technical: `web/src/content/journeys/discovery.md` line 56 has
  `- name: voice-and-microcopy` in the skills list — must be updated
- Technical: `workspace.toml` has no operative (non-comment) entries with
  `voice-and-microcopy` — only descriptive decision-record comments that are
  intentionally preserved

## Acceptance Criteria

- [x] AC1: `packs/product-engineering/.apm/skills/ux-writing/SKILL.md` exists;
  `name: ux-writing` in frontmatter; old path `voice-and-microcopy/` does not exist
- [x] AC2: `packs/product-engineering/.apm/skills/ux-writing/evals/evals.json`
  has `"skill_name": "ux-writing"`; `eval_queries.json` total `"should_trigger": false`
  count ≥ 14 (9 existing + ≥5 new weak fixtures)
- [x] AC3: `packs/product-engineering/pack.toml` version = `"0.13.0"`; evals
  list contains `"ux-writing"` not `"voice-and-microcopy"`; description updated
- [x] AC4: `grep -r "voice-and-microcopy" packs/ web/ docs/guides/ --include="*.md" --include="*.toml" --include="*.json" --include="*.astro" 2>/dev/null` returns 0 matches
- [x] AC5: `place-bet/SKILL.md` betting table includes all four new required
  fields: `thin-slice` (four-criterion definition), `first-success-event`
  (30-day operationalization), `specialist-lenses` (default set named),
  `learning-contract` (three components: measure/cadence/pivot-trigger)
- [x] AC6: `de-risk-intent/SKILL.md` validation-hook format includes
  `evidence_level: observed | supported | inferred | assumed | unknown`; the
  riskiest-assumption selection criterion references "lowest evidence level"
- [x] AC7: `place-bet/SKILL.md` Anti-patterns section names gate failures by
  outcome (thin-slice, first-success, learning-contract); `grep -c "step [0-9]" packs/product-engineering/.apm/skills/place-bet/SKILL.md` = 0 in the Anti-patterns and gate language sections
- [x] AC8: `web/src/content/journeys/product-engineering.md` exists; follows
  `product-strategy.md` frontmatter format; thin-slice and learning-contract
  steps visible in body; `whatChanges` field references the Digital Experience
  Contract
- [x] AC9: `web/src/content/packs/product-engineering.md` lists `ux-writing` in
  the skills array; description updated to jobs-first prose
- [x] AC10: `docs/guides/product-engineering/how-to/place-a-bet.md` has a
  `## How to define a thin slice` section with the four-criterion test
- [x] AC11: `docs/guides/product-engineering/how-to/write-a-post-launch-learning-contract.md`
  exists; covers what to measure, cadence, and pivot triggers
- [x] AC12: `make build-check` exits 0
- [x] AC13: `python3 tools/check-contract-drift.py --root .` exits 0
- [x] AC14: `docs/product/changelog.md` `[Unreleased]` section has an entry for
  PE pack 0.13.0 covering the ux-writing rename and doctrine additions
- [x] AC15: `workspace.toml` has `"spec/product-engineering-shaping-doctrine"` in
  the shipped list; `digital-experience-contract-pe-journey-xref` entry is removed
  from `[backlog].open` (closing the deferred AC from spec/digital-experience-contract)

## Testing Strategy

All tasks use **goal-based check** — this is a doctrine and content change with no
new logic to TDD. Each task's "done" is verified by file existence, grep, or a
one-liner command that exits 0.

- AC1–AC4 (rename sweep): primary verification is AC4's grep returning 0 matches
  on all live file types (.md/.toml/.json/.astro); AC1–AC3 confirm key file-level
  invariants; workspace.toml decision-record comments (descriptive, not operative)
  intentionally retain the old name
- AC5–AC7 (skill doctrine updates): presence checks — verified by reading updated
  SKILL.md sections and confirming required fields and language; AC5/AC6 are
  prompt-only (no behavioral fixture without adding place-bet to `[pack.evals]`)
- AC8–AC9 (web content): `make build-check` must pass (Astro build covers .astro);
  key frontmatter and content fields verified by read
- AC10–AC11 (guides): file existence and section presence
- AC12–AC13 (build gates): run commands; exit 0 is the terminal criterion
- AC14–AC15 (governance): verified by reading updated workspace.toml and changelog
