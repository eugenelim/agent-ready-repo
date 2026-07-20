# Spec: spec-D-pack-workflow-guide

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0067](../../rfc/0067-session-arc-conventions-and-pack-workflow-guide.md) — driving RFC; Change D defines the guide's seven sections, the CONTRIBUTING.md step 0, and the author-a-skill.md intro link
  - [ADR-0054](../../adr/0054-session-arc-verb-taxonomy-and-pack-type-classification.md) — four-type pack classification and verb taxonomy are the normative content for the guide's archetype section
  - [Spec A](../spec-A-workspace-status-rename/spec.md) — `author-a-skill.md` changes are Spec A's scope: AC7 is the `## Naming your skill` section; AC8 is the intro link to the guide. This spec authors the guide itself and the CONTRIBUTING.md step 0; it does not touch `author-a-skill.md`.
- **Contract:** none — documentation authoring only; no API contract.
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A pack author who reads `docs/guides/_shared/explanation/pack-workflow-design.md` before writing their first skill can make all five arc-design decisions (workflow type, arc-stage mapping, skill naming, vault-path shape, workspace-status registration) without consulting a reviewer. `CONTRIBUTING.md`'s "Adding a new pack" section has a step 0 that directs authors to the guide before opening an RFC. The guide is framed at archetype level (episodic/sustained-project/sustained-derived/stateless from ADR-0054) so it remains stable as new packs land.

## Boundaries

### Always do

- Structure the guide's seven sections as specified in RFC-0067 §D1.
- Frame every section at archetype level (ADR-0054 four-type classification), not at individual skill level — individual skill names within archetypes may change; the archetype shape does not.
- Use the `workspace-design` session-arc vocabulary (Arrive → Orient → Work → Persist → Collaborate) as the design language throughout.
- Cite `journey-mapping` as the canonical vault-path pattern example (RFC-0067 §D1 Step 4).
- Add the CONTRIBUTING.md step 0 exactly as RFC-0067 §D2 specifies (verbatim paragraph + step 1 amendment).

### Ask first

- Restructuring the guide into more or fewer sections than the RFC-0067 §D1 seven.
- Adding a fifth pack archetype to the guide's reference section.
- Changing the step 0 paragraph wording in CONTRIBUTING.md beyond correcting a typo.

### Never do

- Touch `author-a-skill.md` in any way — all changes to that file belong to Spec A (AC7: naming section; AC8: intro link). This spec authors only the guide and the CONTRIBUTING.md step 0.
- Include RFC/ADR/spec references in the guide body — the guide is adopter-surface content; governance citations belong in ADRs and specs (source: `feedback_no_governance_citations_in_shipped_pack_content.md`).
- Enumerate individual skill names in the guide (beyond examples) — archetype-level framing is the stability guarantee.

## Testing Strategy

All criteria use **goal-based check**: each section's presence and content are verifiable by reading the guide. No compiled artifact. One **manual QA** step: a reader unfamiliar with the catalogue should be able to follow the five steps in the guide and classify a hypothetical new pack without external help.

## Acceptance Criteria

- [ ] **AC1.** `docs/guides/_shared/explanation/pack-workflow-design.md` exists.
- [ ] **AC2.** The guide contains all seven RFC-0067 §D1 sections: (1) What a pack is + session-arc vocabulary, (2) Step 1 — Characterize workflow type (decision tree), (3) Step 2 — Map the arc, (4) Step 3 — Name your skills, (5) Step 4 — Decide vault-path shape, (6) Step 5 — Register with workspace-status, (7) Reference: three worked archetypes (Episodic, Sustained-project, Sustained-derived) plus a stateless reserved-category note.
- [ ] **AC3.** Section 2 (Step 1) contains a decision tree leading to one of the four ADR-0054 types: episodic, sustained-project, sustained-derived, stateless.
- [ ] **AC4.** Section 3 (Step 2) walks each arc stage (Arrive, Orient, Work, Persist, Collaborate) with guiding questions for the pack author.
- [ ] **AC5.** Section 4 (Step 3) references the verb taxonomy from ADR-0054 and cites the banned-label list; it cross-links to `docs/guides/_shared/how-to/author-a-skill.md` for the full taxonomy table.
- [ ] **AC6.** Section 5 (Step 4) covers: single `output_dir` base per pack, skill-specific subdirectories, and cites `journey-mapping` as the canonical vault-path example.
- [ ] **AC7.** Section 6 (Step 5) covers: `shaping_queue` type, routing to `workspace-status`, and the fallback if experience-design is not installed.
- [ ] **AC8.** Section 7 (Reference) contains worked archetypes for: Episodic (product-strategy), Sustained-project (desk-research), Sustained-derived (experience-design). Stateless: ADR-0054 classifies no current catalogue pack as stateless (converters and architect are Episodic); the guide notes this as a reserved category for hypothetical future packs with no current worked example.
- [ ] **AC9.** `CONTRIBUTING.md` "Adding a new pack" section gains step 0 (before the current step 1) with the RFC-0067 §D2 paragraph verbatim (or equivalent in the file's voice).
- [ ] **AC10.** `CONTRIBUTING.md` step 1 ("Open an RFC") gains the sentence: "The RFC should include your arc mapping from step 0 — which skills cover which arc stages, and why."
- [ ] **AC11.** The guide contains no governance citations (no RFC/ADR/spec references in the guide body text) — per Diátaxis link-out discipline: explanation pages link out to reference/how-to content, not to internal governance artifacts. (Governance provenance lives in this spec's `Constrained by:` header, not in the guide.)
- [ ] **AC12.** `scripts/lint-spec-status.py` exits 0 on this spec; `git status` clean.

## Assumptions

- Technical: `CONTRIBUTING.md` has an "Adding a new pack" section with numbered steps; the step 0 addition prepends before the current step 1 (source: RFC-0067 §D2 assumes this structure).
- Technical: `docs/guides/_shared/explanation/` directory exists (source: `ls docs/guides/_shared/explanation/` confirmed at spec-authoring time — directory contains README.md, file-safety-contract.md, install-routes.md, pack-catalogue.md, shaping-a-new-engagement.md, the-three-loops.md).
- Process: no governance citations in the guide body — the guide is adopter-surface explanation content; ADR/RFC provenance belongs in this spec's "Constrained by" header, not in the guide itself (source: `feedback_no_governance_citations_in_shipped_pack_content.md`).
- Product: the four-type classification (ADR-0054) is stable enough to anchor the guide at archetype level; new pack archetypes will trigger an ADR-0054 revision before the guide needs updating.
