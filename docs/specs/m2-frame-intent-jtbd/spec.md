# Spec: m2-frame-intent-jtbd

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

`frame-intent` shapes a raw idea, request, or strategy signal into a level-tagged
`intent` artifact (outcome + opportunity). Step 5 of the skill procedure says "The
default outside-in lens is a JTBD job map" but gives no elicitation structure —
there are no prompts for the functional, emotional, or social dimensions of the job,
and the intent template's Opportunity section is free-form prose. Practitioners skip
the emotional and social dimensions by default because nothing surfaces them.

The enriched `frame-intent` runs a three-tier JTBD intake pass at step 5. The skill
explicitly elicits a **functional job** (what the user is trying to accomplish), an
**emotional job** (how they want to feel during or after the job), a **social job**
(how they want to be perceived by others), and the **struggling moment** (the
friction point where the current situation fails them). The intent template's
Opportunity section carries four corresponding structured sub-fields. A new
`references/jtbd-job-categories.md` grounds the vocabulary, keeping it consistent
with `identify-opportunities`. The existing
`docs/guides/product-engineering/how-to/shape-a-feature-intent.md` guide carries
a JTBD enrichment subsection (phase-slice doctrine — guide ships with the capability).

The scope boundary with `identify-opportunities` holds: `frame-intent` elicits all
three job dimensions without scoring or ranking. Full Ulwick opportunity scoring and
a prioritised job list belong to `identify-opportunities`.

## Boundaries

### Always do

- Keep the three-tier vocabulary (functional / emotional / social) identical to
  `identify-opportunities`' definitions — both skills share `jtbd-job-categories.md`
  as the common reference
- Mark the four JTBD sub-fields as optional in the intent template comment so an
  Opportunity section written as free-form prose (existing intents) remains valid
  without migration
- Include a step-5 handoff pointer to `identify-opportunities` for practitioners
  who want full job scoring after framing

### Ask first

- Adding the eight-stage linearised job map to `jtbd-job-categories.md` — scope
  extension beyond the three-tier intake pass
- Switching the Opportunity sub-fields from bullet labels (`- Functional job:`) to
  Markdown sub-headers — default is bullet label style

### Never do

- Add Ulwick opportunity scoring, importance/satisfaction ratings, or a ranked job
  list to `frame-intent` — that boundary belongs to `identify-opportunities`
- Make the four JTBD sub-fields mandatory in the template; an intent with free-form
  prose in the Opportunity section must remain valid with no migration
- Change the intent output path, filename convention, or template outer structure —
  this is an additive enrichment only
- Add a dependency outside the PE pack

## Testing Strategy

All changes are skill procedure text, template markdown, a reference file, and a
guide update — no compiled artefact, no runtime executable.

**Goal-based checks** (grep / file-existence probes) cover structural presence:

- **Step 5 elicitation structure:** `grep` for "Functional job", "Emotional job",
  "Social job", "struggling moment" in `SKILL.md` — all four must be present.
- **Handoff line present:** `grep "identify-opportunities"` in `SKILL.md` in the
  step 5 context — must be present.
- **Template sub-fields:** `grep` for all four field labels in `intent-template.md`
  — all must be present.
- **Optional marker present in Opportunity section:** `awk '/## Opportunity/,/## Product-vision fields/' packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md | grep -i "optional"` — must match (scoped to the Opportunity section; pre-existing "optional" elsewhere in the template does not satisfy this check).
- **Reference file exists and defines all three categories:** file present at
  `references/jtbd-job-categories.md`; `grep` for "Functional", "Emotional",
  "Social" — all three must appear.
- **Reference cross-references `identify-opportunities`:** `grep "identify-opportunities"` in `jtbd-job-categories.md` — must be present.
- **No Ulwick scoring in skill body:** `grep -i "ulwick\|opportunity score\|importance.*satisfaction"` in `SKILL.md` — zero hits. For `jtbd-job-categories.md`,
  the same grep applied only to lines outside the "Going deeper" cross-reference
  section — zero hits there; the cross-reference section may name the scoring
  formula as a pointer to `identify-opportunities`, nowhere else.
- **Guide JTBD section present:** `grep -i "functional job\|jtbd"` in
  `shape-a-feature-intent.md` — must be present.
- **Pack version bumped:** `grep -m1 "^version"` in `packs/product-engineering/pack.toml`
  — must read `version = "0.12.0"` (the `[pack]` version; the `[pack.adapter-contract]`
  version under the `[pack.adapter-contract]` section header is distinct and must not change). `grep '"version"'` in
  `packs/product-engineering/.claude-plugin/plugin.json` — must read `"version": "0.12.0"`.
  Marketplace: `grep -A15 '"name": "product-engineering"' .claude-plugin/marketplace.json | grep -m1 '"version"'` — must read `0.12.0`.
- **Changelog updated:** `grep -i "jtbd" docs/product/changelog.md` — must be
  present (the string "jtbd" does not pre-exist in the file; any hit confirms the
  new entry landed).
- **RFC-0064 M2.7 marked complete:** `grep "\[x\].*JTBD framing embedded in.*frame-intent" docs/rfc/0064-ini-001-ai-native-ecosystem.md` — must match (discriminating: does not match the M2.2 or table rows for the same slug).

**Manual QA** covers prose-quality sub-clauses that greps cannot verify: run
`frame-intent` on a sample feature description; confirm the skill prompts for
all four dimensions with one-line guidance each; confirm the emitted intent artifact
contains all four Opportunity sub-fields populated (not empty template labels);
verify vocabulary matches `identify-opportunities`' category names; verify the
guide examples are concrete (one per dimension).

## Acceptance Criteria

- [x] `packs/product-engineering/.apm/skills/frame-intent/SKILL.md` step 5
  explicitly elicits all three JTBD job dimensions — functional, emotional, and
  social — plus the struggling moment, with one-line guidance per dimension
- [x] Step 5 includes a handoff line routing to `identify-opportunities` for
  practitioners who want full opportunity scoring after framing
- [x] `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md`
  Opportunity section has four structured sub-fields: `- Functional job:`,
  `- Emotional job:`, `- Social job:`, `- Struggling moment:` — each with a
  one-line inline comment prompt
- [x] The four sub-fields are marked optional in the template comment block so an
  Opportunity section written as free-form prose remains a valid intent artefact
  with no migration required
- [x] `packs/product-engineering/.apm/skills/frame-intent/references/jtbd-job-categories.md`
  exists and defines all three job categories using vocabulary consistent with
  `identify-opportunities`
- [x] `jtbd-job-categories.md` cross-references `identify-opportunities` as the
  skill for deep job discovery and Ulwick scoring
- [x] `docs/guides/product-engineering/how-to/shape-a-feature-intent.md` includes
  a JTBD enrichment subsection covering the three job categories and struggling
  moment, with at least one concrete example per dimension
- [x] When `frame-intent` step 5 is run and the practitioner provides JTBD
  responses, the emitted `intents/<slug>.md` artifact's Opportunity section
  contains all four populated sub-fields — the skill writes the elicited answers,
  not just the empty template labels
- [x] `packs/product-engineering/pack.toml` `[pack]` version field reads `0.12.0`
  (the `[pack.adapter-contract]` version is unchanged); `packs/product-engineering/.claude-plugin/plugin.json` version field reads `0.12.0`; `make build-self FORCE=1`
  regenerates `.claude-plugin/marketplace.json` with the updated version
- [x] No Ulwick scoring formula, importance/satisfaction rating, or opportunity
  ranking appears in `SKILL.md` or in `jtbd-job-categories.md` outside the
  "Going deeper" cross-reference section
- [x] `docs/product/changelog.md` `[Unreleased]` block contains an entry
  describing the frame-intent JTBD enrichment (three-tier elicitation in step 5)
  and the PE pack v0.12.0 bump
- [x] RFC-0064 AC [M2.7] (`- [x] JTBD framing embedded in frame-intent…`)
  marked complete (`- [x]`) in `docs/rfc/0064-ini-001-ai-native-ecosystem.md`

## Assumptions

- Technical: `frame-intent` SKILL.md is at `packs/product-engineering/.apm/skills/frame-intent/SKILL.md`; step 5 says "The default outside-in lens is a JTBD job map" with no functional/emotional/social breakdown (source: `packs/product-engineering/.apm/skills/frame-intent/SKILL.md:78`)
- Technical: `assets/intent-template.md` Opportunity section is free-form prose — no structured JTBD fields (source: `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md:29-37`)
- Technical: No `docs/product/intents/` directory exists — zero back-compat burden on already-authored intent files (source: bash probe, directory absent)
- Technical: PE pack is currently v0.11.1; this is a feature addition → bump to v0.12.0 (source: `packs/product-engineering/pack.toml`)
- Technical: `identify-opportunities` owns the full three-tier JTBD model with Ulwick scoring; `frame-intent` must not re-implement scoring (source: `packs/product-engineering/.apm/skills/identify-opportunities/SKILL.md`)
- Technical: The guide to update is `docs/guides/product-engineering/how-to/shape-a-feature-intent.md` — covers the frame-intent flow but has no JTBD section (source: file read)
- Process: RFC-0064 M2.7 scopes this work as a shipped-skill modification with its own spec; `Constrained by: RFC-0064` (source: `docs/rfc/0064-ini-001-ai-native-ecosystem.md:116, 482`)
- Process: No new RFC required — scoped modification within the RFC-0064 boundary (source: `docs/CONVENTIONS.md §When NOT to open an RFC`)
- Product: JTBD grain is medium — all three job dimensions plus struggling moment elicited in step 5, no scoring (source: user confirmation 2026-07-21)
- Product: Structured template fields preferred over prose guidance only (source: user confirmation 2026-07-21)
- Product: Guide ships in same PR per phase-slice doctrine (source: user confirmation 2026-07-21)
- Product: Template sub-fields use singular labels ("Functional job", "Emotional job", "Social job") while `identify-opportunities` uses plural headings ("Functional jobs", etc.) — the singular/plural divergence is deliberate: frame-intent elicits one primary job per dimension as an intake pass; `identify-opportunities` surfaces all jobs in each tier as a discovery list (source: design decision; not a vocabulary inconsistency)
