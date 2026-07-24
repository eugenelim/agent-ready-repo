# Spec: digital-experience-contract

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0071](../../rfc/0071-digital-experience-doctrine.md) (Area A, D1, D6), [RFC-0062](../../rfc/0062-content-design-and-copy-direction-skills.md) (Accepted — referenced by contract; implementation in spec/xd-copy-direction)
- **Brief:** none
- **Contract:** Digital Experience Contract schema `schema-version: "1.0"` — this spec authors the schema. The contract is an adopter-facing markdown artifact template; the schema version is the governance handle for future breaking field changes.
- **Shape:** integration — new cross-pack shared primitive (template in four packs' skill references/) + new `tools/` lint

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Four packs cover the digital product lifecycle. Each pack individually passes its own rubric; no shared artifact enforces continuity across disciplines. An outcome defined in `product-strategy` can silently disappear before `core` ships. This spec implements the **Digital Experience Contract** — a lightweight shared schema that connects strategy → PE → XD → frontend engineering.

The deliverable is:

1. A **canonical markdown template** (`digital-experience-contract.md`) placed as a pack-local reference in each of the four affected packs' skill anchor directories. The template carries `schema-version: "1.0"` in its frontmatter; defines three risk-adaptive tiers (explore / pilot / production) with field-level Required annotations; and maps every field to its owning discipline.

2. A **deterministic drift check** (`tools/check-contract-drift.py`, pure stdlib Python) that: first does a byte comparison of all four copies (exit 0 immediately if identical); on any divergence, falls back to a structural fingerprint comparison (schema-version + section headers + Required annotations) to produce a named diagnosis (which pack, which field or section). Exit 0 = no drift. Exit 1 = drift detected with named diagnosis.

3. A **self-test** (`tools/test-check-contract-drift.py`) covering all meaningful drift modes.

4. An **explanation guide** (`docs/guides/core/explanation/digital-experience-contract.md`) — a Diátaxis explanation page describing the contract, its three risk tiers, and the ownership map.

5. **Cross-reference notes** added to the `whatChanges` field of the three existing affected journey pages (`web/src/content/journeys/product-strategy.md`, `experience-design.md`, `core.md`). The PE journey page (`product-engineering.md`) does not exist; its cross-reference is deferred to `spec/product-engineering-shaping-doctrine` (deferred: digital-experience-contract-pe-journey-xref).

6. **`make build-self FORCE=1`** — after placing the core pack's template, the new `packs/core/.apm/skills/frontend-engineering/references/digital-experience-contract.md` projects to `.claude/skills/frontend-engineering/references/digital-experience-contract.md`. The projected artifact is committed in this PR.

The contract template is additive — it ships alongside existing skills without changing any SKILL.md file. Downstream doctrine specs (M2a–M4) update skills to reference and populate the contract; this spec ships the shared schema they will reference.

## Boundaries

### Always do

- Place the identical template at all four anchor paths (defined in ACs); all four must be byte-for-byte identical at ship time
- Include `schema-version: "1.0"` in the YAML frontmatter of every copy
- Annotate every field subsection with exactly one `<!-- Required: <tier>+ -->` comment on the line immediately following the h3 header
- Make `tools/check-contract-drift.py` pure stdlib Python; follow `tools/lint-profiles.py` structure (shebang, module docstring, argparse `--root .`, exit 0/1)
- Run `make build-self FORCE=1` after placing the core copy; commit the projected `.claude/skills/frontend-engineering/references/digital-experience-contract.md`
- Run the drift check against the four freshly-placed copies and confirm exit 0 before shipping
- Write the explanation guide as a Diátaxis explanation (not a how-to or tutorial) — describes the concept, the tiers, and the ownership map; does not prescribe a step-by-step fill procedure (that belongs in downstream how-to guides)
- Use absolute path form (`/docs/guides/core/explanation/digital-experience-contract/`) for any journey page links, never relative paths from the `web/src/content/journeys/` directory
- Add a contract cross-reference sentence to the `whatChanges` field in each of the three existing journey pages (product-strategy, experience-design, core)

### Ask first

- Adding, removing, or renaming any field in the contract template (each change is a schema change; the drift check enforces schema-version parity)
- Changing the anchor skill path for any pack (the anchor paths are defined in ACs and the drift check hardcodes them)
- Adding the contract to SKILL.md files — that is the job of downstream doctrine specs; do not pre-empt them here
- Promoting the drift check to a build-check gate — it runs on demand; promotion to gate requires calibration evidence (deferred: contract-drift-check-gate-promotion)

### Never do

- Modify any existing SKILL.md, pack.toml, or evals file — those belong to downstream specs
- Ship different template content to different packs — all four copies must be byte-equivalent for the drift check to pass
- Add a `yaml` or other non-stdlib import to the drift check
- Create new top-level directories (the template files go inside existing anchor skill directories)
- Include any project-specific content in the template (the template ships with placeholder text only; adopters fill it in their own project's docs/)

## Template Schema

The canonical template content is defined here as the authoritative source; all four pack copies must match it byte-for-byte. The drift check does a byte comparison as the primary check; structural fingerprint comparison produces the diagnosis if bytes diverge.

### RFC-0071 tier mapping

This table shows how the 32 fields implement RFC-0071 Area A's tier requirements. Items not named explicitly in the RFC tier table are derived from the Area A ownership map and the three-tier principle ("explore-mode work is not buried in production-level ceremony").

| RFC-0071 Explore required | Contract field |
|---|---|
| Target user | Strategy: Target User and Context |
| Whole problem | Strategy: Diagnosis and Strategic Choices + PE: Opportunity and Bet |
| User outcome | Strategy: Adoption Hypothesis |
| First-success event | Strategy: Adoption Hypothesis + PE: First-Success Operationalization |
| Primary journey | Experience Design: Primary Journey |
| Core assumptions | Strategy: Assumptions and Kill Criteria |
| Prototype/representation | Frontend Engineering: Prototype or Representation |

| RFC-0071 Pilot adds | Contract field |
|---|---|
| States | Experience Design: States and Permissions |
| Permissions | Experience Design: States and Permissions |
| Accessibility requirements | Frontend Engineering: Accessibility Evidence |
| Instrumentation | Frontend Engineering: Instrumentation |
| Support plan | PE: Rollout and Recovery Plan |
| Rollout + recovery | PE: Rollout and Recovery Plan |

| RFC-0071 Production adds | Contract field |
|---|---|
| Complete a11y evidence | Frontend Engineering: Accessibility Evidence (production level) |
| Browser matrix | Frontend Engineering: Browser Behavior |
| CWV results | Frontend Engineering: Performance |
| Security + privacy | Frontend Engineering: Security and Privacy |
| Reliability | Frontend Engineering: Reliability |
| Cross-channel continuity | Experience Design: Responsive Behavior |
| Measurement dashboard | Frontend Engineering: Instrumentation (production level) |

**Value loop** (RFC-0071 D8, Area B — named explicitly as an adoption-hypothesis component): appears as Strategy: Value Loop (explore+), a separate field from Adoption Hypothesis.

**Metric Tree at `pilot+` is deliberate.** RFC-0071 Alt 5's rationale frames the metric tree as the signal that confirms the adoption hypothesis — the coupling is real. The tier assignment is nonetheless `pilot+` because at explore stage the adoption hypothesis is validated by a qualitative success signal (defined in First-Success Operationalization), not a formal metric set; explore-tier teams may not yet have instrumentation infrastructure. The Metric Tree formalizes measurement for when real users are available. This diverges from Alt 5's framing but is consistent with the "explore-mode work is not buried in production-level ceremony" principle.

### Frontmatter

```yaml
---
schema-version: "1.0"
risk-tier: explore     # explore | pilot | production
product-slug: <replace-with-product-slug>
---
```

### Section structure and Required tiers

The table below defines every field, its owning discipline, and its minimum tier. The order must match the template exactly; the drift check validates header order.

| Section (h2) | Field (h3) | Owner | Required |
|---|---|---|---|
| Strategy | Target User and Context | product-strategy | explore+ |
| Strategy | Diagnosis and Strategic Choices | product-strategy | explore+ |
| Strategy | Adoption Hypothesis | product-strategy | explore+ |
| Strategy | Value Loop | product-strategy | explore+ |
| Strategy | Metric Tree | product-strategy | pilot+ |
| Strategy | Differentiation | product-strategy | pilot+ |
| Strategy | Assumptions and Kill Criteria | product-strategy | explore+ |
| Product Engineering | Opportunity and Bet | product-engineering | explore+ |
| Product Engineering | Evidence Ladder | product-engineering | explore+ |
| Product Engineering | First-Success Operationalization | product-engineering | explore+ |
| Product Engineering | Thin Slice | product-engineering | pilot+ |
| Product Engineering | Capabilities | product-engineering | pilot+ |
| Product Engineering | Rollout and Recovery Plan | product-engineering | pilot+ |
| Product Engineering | Learning Plan | product-engineering | pilot+ |
| Experience Design | Primary Journey | experience-design | explore+ |
| Experience Design | Surface Map | experience-design | pilot+ |
| Experience Design | Information Architecture | experience-design | pilot+ |
| Experience Design | Content Hierarchy | experience-design | pilot+ |
| Experience Design | Product Objects | experience-design | pilot+ |
| Experience Design | Interaction and Attention Model | experience-design | production+ |
| Experience Design | States and Permissions | experience-design | pilot+ |
| Experience Design | Responsive Behavior | experience-design | production+ |
| Experience Design | Design System Reference | experience-design | pilot+ |
| Frontend Engineering | Prototype or Representation | core | explore+ |
| Frontend Engineering | Implemented Behavior | core | production+ |
| Frontend Engineering | Accessibility Evidence | core | pilot+ |
| Frontend Engineering | Browser Behavior | core | production+ |
| Frontend Engineering | Performance | core | production+ |
| Frontend Engineering | Security and Privacy | core | production+ |
| Frontend Engineering | Reliability | core | production+ |
| Frontend Engineering | Instrumentation | core | pilot+ |
| Frontend Engineering | Rendered Evidence | core | pilot+ |

**Total: 32 fields** (7 Strategy + 7 Product Engineering + 9 Experience Design + 9 Frontend Engineering)

**Graceful capability detection note (inline in template):** A skill that attempts to populate a section owned by an unavailable discipline must: (1) perform the smallest safe fallback, (2) label the result `[provisional — <owner-pack> not installed]`, (3) state what specialist work remains. No phantom handoff may ship — every handoff either resolves to an installed skill or degrades explicitly.

## Testing Strategy

- **Drift check correctness:** TDD — `tools/test-check-contract-drift.py` (subprocess invocation against fixture trees, following `tools/test-lint-profiles.py` pattern). Test trees:
  - Tree A — four identical files → exit 0
  - Tree B — schema-version mismatch in one copy → exit 1, output names the differing pack
  - Tree C — tier annotation present but different value (e.g. `explore+` changed to `pilot+`) → exit 1, names the field and the differing tier
  - Tree D — one copy missing a `<!-- Required:` annotation for one field → exit 1, names the missing annotation
  - Tree E — one copy has an extra h3 header not in the others → exit 1, names the extra header
  - Tree F — one copy has a missing h3 header → exit 1, names the missing field
  - Tree G — one file missing entirely at its expected path → exit 1, names the missing path
  - Tree H — one copy has fields in different order (reordered h3s) → exit 1, names the position mismatch
  - Tree I — one copy has no parseable frontmatter (no `---` block or no schema-version key) → exit 1, clean error (no AttributeError / uncaught exception)
- **Template field presence:** goal-based — `grep -c "^###" <one-copy-path>` returns 32
- **All four copies exist:** goal-based — `find packs/*/\.apm -name "digital-experience-contract.md" | wc -l` returns 4
- **Drift check passes on fresh copies:** goal-based — `python tools/check-contract-drift.py --root .` exits 0
- **Projected artifact committed:** goal-based — `ls .claude/skills/frontend-engineering/references/digital-experience-contract.md` exists
- **Explanation guide exists with required sections:** goal-based — `grep "^## " docs/guides/core/explanation/digital-experience-contract.md` returns lines for: The contract, The three tiers, The ownership map, Graceful capability detection
- **Journey page cross-references present:** goal-based — `grep "Digital Experience Contract"` hits in each of the three updated journey pages
- **No SKILL.md, pack.toml, or evals modified:** goal-based — `git diff --name-only` contains none of those file types (except in the paths explicitly authorized by this spec)

## Acceptance Criteria

- [x] Template file exists at all four anchor paths (exact paths below; all new):
  - `packs/product-strategy/.apm/skills/synthesize-stakeholder-research/references/digital-experience-contract.md`
  - `packs/product-engineering/.apm/skills/frame-intent/references/digital-experience-contract.md`
  - `packs/experience-design/.apm/skills/design-review/references/digital-experience-contract.md`
  - `packs/core/.apm/skills/frontend-engineering/references/digital-experience-contract.md`
- [x] All four copies are byte-for-byte identical. `diff` between any pair exits 0.
- [x] Each copy's frontmatter contains exactly: `schema-version: "1.0"`, `risk-tier: explore`, `product-slug: <replace-with-product-slug>`.
- [x] Each copy contains all 32 field subsections (h3 headers) in the order defined in the Template Schema table, each with a `<!-- Required: <tier>+ -->` comment on the line immediately following the h3 header.
- [x] Each copy's four discipline sections are h2 headers in this order: `## Strategy [owner: product-strategy]`, `## Product Engineering [owner: product-engineering]`, `## Experience Design [owner: experience-design]`, `## Frontend Engineering [owner: core]`.
- [x] `tools/check-contract-drift.py` exists; pure stdlib Python (no non-stdlib imports); `#!/usr/bin/env python3` shebang; argparse `--root .`; exit 0/1; implements byte-compare-first then structural-fingerprint-for-diagnosis algorithm.
- [x] `tools/test-check-contract-drift.py` exists; covers Trees A–I (nine test cases); `python tools/test-check-contract-drift.py` exits 0.
- [x] `python tools/check-contract-drift.py --root .` exits 0 on the freshly-placed copies.
- [x] `make build-self FORCE=1` ran; `.claude/skills/frontend-engineering/references/digital-experience-contract.md` exists and matches the pack copy; committed in this PR.
- [x] `docs/guides/core/explanation/digital-experience-contract.md` exists; contains h2 sections: The contract, The three tiers, The ownership map, Graceful capability detection.
- [x] `web/src/content/journeys/product-strategy.md` `whatChanges` field contains the phrase "Digital Experience Contract".
- [x] `web/src/content/journeys/experience-design.md` `whatChanges` field contains the phrase "Digital Experience Contract".
- [x] `web/src/content/journeys/core.md` `whatChanges` field contains the phrase "Digital Experience Contract".
- [x] No SKILL.md, pack.toml, or eval file is modified.
- [x] `workspace.toml` passes `python3 -c "import tomllib; tomllib.load(open('workspace.toml','rb'))"` after any workspace.toml edit.
- [ ] (deferred: digital-experience-contract-pe-journey-xref) PE journey page cross-reference — deferred to `spec/product-engineering-shaping-doctrine` where the PE journey page will be authored.
- [ ] (deferred: contract-drift-check-gate-promotion) Promotion of drift check to a build-check gate — deferred pending calibration evidence from at least two passes on the live repo.

## Assumptions

- The anchor skill in each pack has an existing `references/` directory (PS: `synthesize-stakeholder-research/references/` ✓, PE: `frame-intent/references/` ✓, XD: `design-review/references/` ✓); only core's `frontend-engineering/references/` is new. Verified by directory listing.
- `make build-self FORCE=1` is the correct invocation for a forced self-host projection. Verified by reading Makefile line 53.
- The four template copies are blank forms — adopters create their own filled instance in their project's `docs/` directory. The pack-local copy is the schema reference only.
- Pure-stdlib Python works for frontmatter parsing — the frontmatter block is delimited by `---` markers, and `schema-version` is on its own line; a simple `re.search` suffices.
- The drift check `PACK_ANCHORS` dict paths are relative to `--root` (the repo root), following the `lint-profiles.py` `--root` convention.

## Boundaries — site, guide, journey

Per ini-003 phase-slice doctrine, this spec ships its own guide and journey updates:
- **Guide:** `docs/guides/core/explanation/digital-experience-contract.md` — Diátaxis explanation of what the contract is, its three tiers, and the ownership map. Cross-links use absolute `/docs/guides/core/explanation/digital-experience-contract/` form. Does not duplicate RFC-0071 — one paragraph summary with a pointer to the RFC for governance detail.
- **Journey pages:** brief cross-reference sentence appended at end of the `whatChanges` YAML field value in three existing journey pages (product-strategy, experience-design, core). Not a rewrite of the `whatChanges` prose.
- **Site (site/ — MkDocs docs site):** no change in this spec — explanation guides project to the docs site naturally; no explicit docs-site config change needed.
- **PE journey page:** deferred to `spec/product-engineering-shaping-doctrine` (deferred: digital-experience-contract-pe-journey-xref).
