# Spec: frontend-engineering-doctrine-update

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0071](../../rfc/0071-digital-experience-doctrine.md) D5 (four modes in one SKILL.md), D9 (per-spec minor version bump)
- **Brief:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: full (structural change — reorganizes a public-interface SKILL.md; multi-task; multi-feature)

## Objective

The `frontend-engineering` skill in the `core` pack operates today as a single implicit create mode: design pre-flight, craft rules, and a GATES verification checklist, all written for greenfield work. An agent working on an existing surface has no brownfield inspection step. An agent claiming FE work done has no required evidence manifest. The accessibility baseline is WCAG 2.1 AA; there is no declared browser policy or Core Web Vitals target. The state matrix has six states; twelve relevant states are absent. Multi-surface products (marketing site + app + docs) have no shared-token, navigation, or terminology contract.

This spec restructures the skill around four explicit modes — **create** (new surface), **retrofit** (improving an existing surface), **audit** (reviewing without writing code), **verify** (running the full gate suite) — as conditional sections in one SKILL.md (RFC-0071 D5). It adds the 12-field page/screen contract as a required gate before significant UI code in create mode. It completes the state coverage to 18 states. It declares WCAG 2.2 AA as the explicit baseline and Baseline Widely Available as the browser policy. It sets CWV targets (LCP ≤2.5s / INP ≤200ms / CLS ≤0.1 at p75) with seven asset budget categories. It adds a brownfield inspection checklist to retrofit mode. It introduces the evidence manifest as a required output. It adds a multi-surface shell contract section covering shared tokens, navigation, and terminology for multi-surface products (RFC-0071 Area E).

The card-use check named in the ini-003 problem statement is an XD-discipline concern addressed by M3c (XD IA/Archetypes/Objects).

Companion deliverables: a how-to guide for filling the page/screen contract, a performance targets quick-reference, and updates to the core pack description (both web/src/content/packs/core.md and packs/core/README.md) and the core journey page.

## 18-state canonical definition

The FE SKILL.md defines the state matrix with these 18 states as distinct top-level states. This is the canonical enumeration for M4:

**6 existing FE states (retained):** loading, empty, error, partial, disabled, content

**4 from XD quality-floor not yet in FE:** success, first-run, no-results, permission/denied

**8 new states:** offline, blocked, destructive-confirmation, long-content, large-data-set, high-zoom, reduced-motion, keyboard-only

Note: the XD quality-floor treats first-run and no-results as sub-distinctions of empty; this FE spec promotes them to distinct top-level states matching the digital-experience-contract.md "18-state set" reference. The content state is FE-specific (the happy-path loaded state distinct from success). These are not contradictions — the quality-floor is a design discipline checklist; this is an FE implementation state matrix.

## Boundaries

### Always do

- Keep all four modes as `### Mode: <mode>` sections inside **one** `SKILL.md` (RFC-0071 D5)
- Preserve the existing pre-mode content (aesthetic reference, seed tokens, HTML/CSS/accessibility craft rules, anti-patterns, GATES) — modes extend the skill; they do not replace the craft rules; however, any hard-coded 6-state or 4-state enumerations inside craft rules (visual-QA checklist, red flags) must be generalized to reference the 18-state matrix rather than naming a fixed subset
- Update the WCAG references: set "WCAG 2.2 AA" as the declared baseline in the general accessibility statement; reword the legal-frameworks compliance line to read "WCAG 2.2 AA is our baseline — it exceeds the WCAG 2.1 minimum currently cited by EU EAA, ADA, and AODA" rather than performing a blind replacement (the legal frameworks currently cite 2.1, not 2.2, so the old wording was factually accurate about the frameworks — the new wording must remain accurate)
- Run `python3 tools/check-contract-drift.py --root .` before the PR merges; the four `digital-experience-contract.md` copies must remain byte-identical
- Run `make build-check` and confirm it passes
- Bump `packs/core/pack.toml` version from `0.13.7` to `0.14.0`
- Update `workspace.toml` to move the M4 entry from `["ini-003".work].queue` to `["ini-003".work].shipped` as a bare string `"spec/frontend-engineering-doctrine-update"`
- In the same PR: flip `spec.md` Status to `Shipped` and `plan.md` Status to `Done`; check all 24 ACs as `[x]` in spec.md (or note each deferred item)

### Ask first

- Adding or removing a field from the 12-field page/screen contract
- Adding or removing a field from the evidence manifest
- Removing any state from the 18-state set
- Changing the CWV numeric targets or asset budget categories

### Never do

- Create separate SKILL.md files for each mode — RFC-0071 D5 explicitly rejects this
- Modify the canonical `digital-experience-contract.md` template (governed by `spec/digital-experience-contract`)
- Add a new external dependency
- Add a new top-level directory to the repo

## Testing Strategy

The SKILL.md change is a documentation/skill restructure. All ACs are verifiable without runtime code tests.

**Goal-based** (grep / file-exists / command-exits-0): AC1–AC12, AC14, AC18–AC24 — mode sections, contract fields, state names, standards declarations, guide file existence, pack version, build-check, drift check, workspace.toml.

**Manual QA**: AC13 (verify mode runs GATES suite — structural check), AC15–AC17 — guide content quality and page update coherence, read as a cold practitioner picking a mode for the first time.

## Acceptance Criteria

- [x] AC1: `packs/core/.apm/skills/frontend-engineering/SKILL.md` contains a `### Mode: create` section
- [x] AC2: SKILL.md contains a `### Mode: retrofit` section
- [x] AC3: SKILL.md contains a `### Mode: audit` section
- [x] AC4: SKILL.md contains a `### Mode: verify` section
- [x] AC5: SKILL.md's create mode section requires the page/screen contract before significant UI code; the contract template names all 12 fields: target user, primary job, primary action, expected result, next action, first-screen content, product proof, read/write consequence, critical states, responsive behavior, a11y requirements, measurement event
- [x] AC6: SKILL.md's retrofit mode section includes a brownfield inspection checklist covering all six items: what-to-preserve, duplicated-systems, hard-coded values, a11y-debt, responsive-debt, visual-regression-risk
- [x] AC7: SKILL.md declares `WCAG 2.2 AA` as the accessibility baseline; no occurrence of `WCAG 2.1 AA` remains as a standalone baseline claim; tooling-ceiling note explicitly marks WCAG 2.2-only success criteria (2.4.11, 2.5.8) as requiring manual verification; the legal-frameworks compliance line accurately states that WCAG 2.2 AA exceeds the current legal minimum
- [x] AC8: SKILL.md names the Baseline Widely Available browser policy
- [x] AC9: SKILL.md states CWV targets: LCP ≤2.5s, INP ≤200ms, CLS ≤0.1 at p75, evaluated separately for mobile and desktop where field data exists (literal values verifiable by grep; mobile/desktop dimension verifiable by read)
- [x] AC10: SKILL.md's performance section lists all seven asset budget categories: JS, images, fonts, third-party scripts, hydration, route-level, long tasks
- [x] AC11: SKILL.md's state matrix covers all 18 states: loading, empty, error, partial, disabled, content (existing 6) + success, first-run, no-results, permission/denied (from XD quality-floor, 4) + offline, blocked, destructive-confirmation, long-content, large-data-set, high-zoom, reduced-motion, keyboard-only (new 8) — each with a treatment description; matrix has exactly 18 data rows
- [x] AC12: SKILL.md defines the evidence manifest with all 11 required fields: routes, viewports, browsers, states, screenshots, a11y result, perf result, console/network result, analytics events, known exceptions, unverified items
- [x] AC13: SKILL.md's verify mode section explicitly references the full GATES suite (manual QA: read the verify mode section cold as a practitioner)
- [x] AC14: SKILL.md includes conditional public-surface guidance (for publicly indexed surfaces) covering: metadata, canonical URLs, sitemaps, structured data, search indexing intent
- [x] AC15: `docs/guides/core/how-to/page-screen-contract.md` exists; covers when the contract is required (proportional to risk/scope — not for trivial components); explains each of the 12 fields; includes at least two proportional application examples (lightweight single-component vs. significant new page)
- [x] AC16: `docs/guides/core/reference/performance-targets.md` exists; lists CWV values (LCP/INP/CLS at p75) and asset budgets by surface type
- [x] AC17: `web/src/content/journeys/core.md` names the page/screen contract, evidence manifest, and CWV gate as identifiable items in the frontend-engineering workflow description
- [x] AC18: `web/src/content/packs/core.md` describes the four-mode structure of the frontend-engineering skill
- [x] AC19: `packs/core/README.md` describes the four-mode structure of the frontend-engineering skill (this feeds `site/docs/packs/core.md` via `tools/build-site.py`)
- [x] AC20: `packs/core/pack.toml` version field reads `0.14.0`
- [x] AC21: `python3 tools/check-contract-drift.py --root .` exits 0
- [x] AC22: `make build-check` exits 0
- [x] AC23: `workspace.toml` `["ini-003".work].shipped` list includes `"spec/frontend-engineering-doctrine-update"`
- [x] AC24: SKILL.md includes a multi-surface shell contract section defining shared tokens, navigation patterns, and terminology requirements for multi-surface products (RFC-0071 Area E)

## Assumptions

- Technical: `packs/core/.apm/skills/frontend-engineering/SKILL.md` is the canonical skill file; `build-self` projects it to `.claude/skills/` (source: `packs/core/pack.toml`)
- Technical: four copies of `digital-experience-contract.md` exist at `packs/core/.apm/skills/frontend-engineering/references/`, `packs/experience-design/.apm/skills/design-review/references/`, `packs/product-engineering/.apm/skills/frame-intent/references/`, and `packs/product-strategy/.apm/skills/synthesize-stakeholder-research/references/` — must stay byte-identical; `tools/check-contract-drift.py` enforces this (source: find command confirmed four paths; tool present)
- Technical: `packs/core/pack.toml` version is currently `0.13.7` (source: `packs/core/pack.toml` line 3)
- Technical: `docs/guides/core/how-to/` and `docs/guides/core/reference/` directories exist (source: directory listing)
- Technical: `packs/core/README.md` is the source for `site/docs/packs/core.md` — generated by `tools/build-site.py` which copies `packs/*/README.md` → `site/docs/packs/<name>.md` (source: `tools/build-site.py`)
- Technical: SKILL.md currently has WCAG 2.1 AA references and a tooling audit that caps at `wcag21aa`; the spec updates the general accessibility baseline to WCAG 2.2 AA and the legal-frameworks compliance line to state 2.2 exceeds the legal 2.1 minimum; the tooling ceiling is annotated as a manual-verification gap (source: SKILL.md lines 383-385, 419)
- Technical: the 18 FE states are as enumerated in the "18-state canonical definition" section above; this spec is the canonical enumeration; the XD quality-floor.md uses sub-distinctions under empty rather than separate states — these are complementary, not contradictory (source: digital-experience-contract.md "18-state set" reference; workspace.toml M4 Deliver)
- Process: four modes in ONE SKILL.md per RFC-0071 D5 (source: `docs/rfc/0071-digital-experience-doctrine.md` D5 row)
- Process: minor version bump for significant doctrine change per RFC-0071 D9 (source: RFC-0071 D9 row)
- Process: workspace.toml queue move, spec Status flip, and AC checkbox completion happen atomically in the same PR per work-loop DECIDE conventions (source: `work-loop` SKILL.md DECIDE section; CONVENTIONS §4a/4b)
- Product: page/screen contract is proportional to risk — not required for trivial components (source: workspace.toml M4 Deliver)
- Product: card-use check is XD-discipline concern (M3c), not M4 FE scope (source: workspace.toml M3c entry)
- Product: multi-surface shell contract is an RFC-0071 Area E (FE) deliverable; workspace.toml M4 Deliver excluded it but it is included in this spec as AC24 to close the RFC-0071 gap (source: RFC-0071 line 338; workspace.toml M4 Deliver omission)
