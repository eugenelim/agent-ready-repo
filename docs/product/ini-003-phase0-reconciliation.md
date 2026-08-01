# ini-003 Phase 0 Reconciliation — Parity Report

**Audit date:** 2026-08-01  
**Starting commit:** 50396f5f5aceb2b88266ecac255c435115b621a5  
**Branch:** eugene/puebla-v1 (at origin/main HEAD)  
**Scope:** Phase 0A (AgentBundle version-contract normalization) + Phase 0B (Digital Experience Doctrine acceptance-criteria parity)

---

## Evidence hierarchy used

1. Canonical skill, agent, command, reference, and script source
2. Executable tests, evals, fixtures, validators
3. Pack manifests, journey contracts, guide metadata
4. Generated projections and rendered output
5. README and guide claims
6. workspace.toml comments and queue status
7. Commit messages

---

## Phase 0A — Version-contract normalization

**Current AgentBundle version:** `0.27.1` (both `packages/agentbundle/pyproject.toml` and `agentbundle/version.py` `CLI_VERSION`)

**Wave 2 reference version:** `0.27.0` (shipped; subsequent patch bump to `0.27.1` on a separate branch)

### Wave 3 — catalogue-wave3-enterprise-authoring-discovery (Status: Approved)

**Version rule (AC25):** "bumped to the next available AgentBundle minor version after inspecting current HEAD at implementation time (Wave 2 shipped as `0.27.0`; the next minor is `0.28.0` unless another branch has claimed it — verify before opening the PR)"

**Assumptions:** "Verify before opening the PR that no other in-flight branch has claimed this version number."

**Classification:** merge-order-safe. The "verify before opening the PR" guard is authoritative. No version is permanently reserved. The planning note (`0.28.0`) is non-normative (conditional on rebase-time check).

**Action:** No change. Phase 0A verified — Wave 3 is merge-order-safe.

### Wave 4 — catalogue-wave4-semantic-contracts-index (Status: Approved)

**Version rule (AC29):** "next available AgentBundle minor version after inspecting current HEAD at implementation time (Wave 2 shipped as `0.27.0`; Wave 3 targets `0.28.0`; Wave 4 takes the next unclaimed minor after both — verify before opening the PR)"

**Assumptions:** "Wave 4 (catalogue index) takes the next unclaimed minor version after both predecessor waves have merged. Verify which version is available before opening the Wave 4 PR — do not open with a version that has already been claimed by another in-flight or shipped branch."

**Classification:** merge-order-safe. "Next unclaimed minor" is the normative rule; the in-text numbers are non-normative planning context.

**Action:** No change. Phase 0A verified — Wave 4 is merge-order-safe.

### Phase 0A result

| Item | Result |
|---|---|
| Current agentbundle version | `0.27.1` (pyproject.toml + CLI_VERSION) — unchanged |
| Wave 3 future-version rule | Merge-order-safe ("verify before opening the PR") |
| Wave 4 future-version rule | Merge-order-safe ("next unclaimed minor after both merged") |
| Contradictory normative fixed-version ACs | None found |
| Version bump required | No |
| Lockfile change | No |

---

## Phase 0B — ini-003 AC parity matrix

### ini-003 shipped work (baseline)

| Spec | Status | Shipped |
|---|---|---|
| spec/rfc-digital-product-experience-doctrine | Shipped | 2026-07-23 |
| spec/digital-experience-contract | Shipped | 2026-07-23 |

Both M1 items are shipped. ini-003 milestone updated from "M1 · Contract + Governance" to "M2 · Adoption + Shaping Doctrine".

### Queue item classifications

#### M2a — Product Strategy Adoption Doctrine

| Field | Value |
|---|---|
| Path | spec/product-strategy-adoption-doctrine |
| Needs | work:spec/digital-experience-contract (SHIPPED — unblocked) |
| Spec.md | Not authored |
| Classification | **C. Genuinely Open** |

**Evidence:** Product-strategy pack has 9 skills (`synthesize-stakeholder-research`, `write-prfaq`, `define-content-strategy`, `define-ux-strategy`, `run-bcg-matrix`, `run-okr-cascade`, `run-pestle-analysis`, `run-porters-five-forces`, `run-swot`). No adoption-hypothesis skill, no causal-metric-tree requirement, no anti-pattern review, no strategy-to-experience handoff doctrine, no weak fixtures for choice-free strategies.

**Canonical evidence:** `packs/product-strategy/.apm/skills/` — skills exist but do not own the 14-point strategy output structure, adoption hypothesis, or causal metric tree required by the ini-003 M2a description.

**Missing delta:** Full M2a description in workspace.toml lines 296–308 is unimplemented.

**Roadmap action:** Keep in queue. Spec not yet authored.

---

#### M2b — Product Engineering Shaping Doctrine

| Field | Value |
|---|---|
| Path | spec/product-engineering-shaping-doctrine |
| Needs | work:spec/digital-experience-contract (SHIPPED — unblocked) |
| Spec.md | Not authored |
| Classification | **C. Genuinely Open** |

**Evidence:** Product-engineering pack has skills including `discovery-loop`, `frame-intent`, `place-bet`, `frame-situation`, `map-capabilities`, `diverge-solutions` etc. No first-success operationalization doctrine, no thin-slice requirement, no evidence ladder, no post-launch learning contract, no weak fixtures.

**Canonical evidence:** `packs/product-engineering/.apm/skills/` — no 19-field shaping output structure. `packs/product-engineering/JOURNEY.md` exists (journey authored independently) but no shaping-doctrine update has been applied.

**Missing delta:** Full M2b description in workspace.toml lines 318–332 is unimplemented.

**Roadmap action:** Keep in queue. Spec not yet authored.

---

#### XD prerequisite — xd-copy-direction (RFC-0062 implementation)

| Field | Value |
|---|---|
| Path | spec/xd-copy-direction |
| Needs | work:spec/digital-experience-contract (SHIPPED — unblocked) |
| Spec.md | Not authored |
| Classification | **C. Genuinely Open** |

**Evidence:** Experience-design pack has 19 skills. No `copy-direction` SKILL.md found (`ls packs/experience-design/.apm/skills/`). The three-way copy boundary (copy-direction / ux-writing / content-design) is not established in frontmatter.

**Missing delta:** Full xd-copy-direction description in workspace.toml lines 340–352 is unimplemented.

**Roadmap action:** Keep in queue. Spec not yet authored. Unblocks M3a (xd-skill-boundaries).

---

#### M3a — XD Skill Boundaries

| Field | Value |
|---|---|
| Path | spec/xd-skill-boundaries |
| Needs | digital-experience-contract (SHIPPED) + xd-copy-direction (OPEN) |
| Spec.md | Not authored |
| Classification | **C. Genuinely Open** (blocked on xd-copy-direction) |

**Missing delta:** Full M3a description in workspace.toml lines 356–371 is unimplemented.

**Roadmap action:** Keep in queue. Blocked until xd-copy-direction ships.

---

#### M3b — XD Design Token Taxonomy rename + Design System Foundations

| Field | Value |
|---|---|
| Path | spec/xd-design-system-foundations |
| Needs | digital-experience-contract (SHIPPED) + xd-skill-boundaries (OPEN) |
| Spec.md | Not authored |
| Classification | **C. Genuinely Open** (blocked on xd-skill-boundaries) |

**Evidence:** XD pack has `design-system` skill (method only; explicitly refuses values). No `design-system-foundations` skill exists in `packs/experience-design/.apm/skills/`. The FE SKILL.md already routes to `design-system-foundations` in its genre-routing table (forward reference — skill not yet delivered).

**Missing delta:** Full M3b description in workspace.toml lines 374–397 is unimplemented.

**Roadmap action:** Keep in queue. Blocked until xd-skill-boundaries ships.

---

#### M3c — XD Information Architecture, Page Archetypes, Product Objects

| Field | Value |
|---|---|
| Path | spec/xd-ia-archetypes-objects |
| Needs | digital-experience-contract (SHIPPED) + xd-skill-boundaries (OPEN) |
| Spec.md | Not authored |
| Classification | **C. Genuinely Open** (blocked on xd-skill-boundaries) |

**Missing delta:** Full M3c description in workspace.toml lines 399–422 is unimplemented.

**Roadmap action:** Keep in queue. Blocked until xd-skill-boundaries ships.

---

#### M3d — XD State Coverage, Experience Reviewer Three Passes, Evals

| Field | Value |
|---|---|
| Path | spec/xd-state-reviewer-doctrine |
| Needs | xd-skill-boundaries (OPEN) + xd-ia-archetypes-objects (OPEN) |
| Spec.md | Not authored |
| Classification | **C. Genuinely Open** (blocked on two upstream items) |

**Evidence:** `packs/experience-design/.apm/agents/experience-reviewer.md` exists. The experience-reviewer description explicitly states: "Does NOT fire on content briefs, tone-of-voice docs, or other direction artifacts." The current reviewer does not perform three passes (cold-read / task-completion / contract). No 18-state set in quality-floor.md (state coverage is incomplete).

**Missing delta:** Full M3d description in workspace.toml lines 424–447 is unimplemented.

**Roadmap action:** Keep in queue. Blocked until xd-skill-boundaries + xd-ia-archetypes-objects ship.

---

#### M4 — Frontend Engineering Doctrine Update

| Field | Value |
|---|---|
| Path | spec/frontend-engineering-doctrine-update |
| Needs | work:spec/digital-experience-contract (SHIPPED — unblocked) |
| Spec.md | Not authored |
| Classification | **B. Partially Implemented** |

**Implemented baseline (canonical source: `packs/frontend-engineering/` v0.1.3):**

| Component | Evidence | Status |
|---|---|---|
| 4-mode structure (create/retrofit/audit/verify) | `SKILL.md` frontmatter + mode-selection table | ✅ Present |
| 12-field page/screen contract | `SKILL.md` §"Page/screen contract" (step 0) | ✅ Present |
| WCAG 2.2 AA default | `SKILL.md` §"Default baseline" + `a11y-engineering` skill | ✅ Present |
| CWV targets (LCP ≤2.5s / INP ≤200ms / CLS ≤0.1) with asset budgets | `SKILL.md` §"Core Web Vitals" | ✅ Present |
| Brownfield inspection checklist | `SKILL.md` §retrofit mode | ✅ Present |
| Evidence manifest (required for completion) | `SKILL.md` §"Evidence manifest" | ✅ Present |
| Activation evals | `evals/eval_queries.json` in multiple FE skills | ✅ Present |
| Specialist skills (a11y, component-contract, css-arch, fe-perf, rendering, responsive, token-arch) | `packs/frontend-engineering/.apm/skills/` | ✅ Present |
| frontend-reviewer agent | `packs/frontend-engineering/.apm/agents/` | ✅ Present |
| DEC reference | `SKILL.md references/digital-experience-contract.md` | ✅ Present |

**Missing delta (site/guide surfaces):**

| Component | Status |
|---|---|
| FE JOURNEY.md (pack-level journey file) | ❌ Not present |
| web/src/content/journeys/frontend-engineering.md | ❌ Not present (core.md is unrelated) |
| FE pack page on marketing site (web/) with four-mode description + jobs-first layout | ❌ Not verified present |
| Page-contract how-to guide | ❌ Not present (guides/frontend-engineering/ has how-to/run-an-audit.md and tutorials/scaffold-a-component.md but no page-contract guide) |
| Performance targets quick-reference | ❌ Not present (guides/frontend-engineering/reference/frontend-engineering.md exists; scope TBD) |

**Roadmap action:** Keep in queue. workspace.toml comment updated to describe remaining delta only (site/guide surfaces). Spec not yet authored. Do not mark shipped without journey, pack page, and guide surfaces.

---

#### M5 — Cross-Pack Experience Eval

| Field | Value |
|---|---|
| Path | spec/cross-pack-experience-eval |
| Needs | All of M2a, M2b, M3a–M3d, M4 (all OPEN) |
| Spec.md | Not authored |
| Classification | **C. Genuinely Open** (blocked on all upstream specs) |

**Evidence:** No executable cross-pack golden-path eval exists. Individual pack evals exist but are independent per-pack evaluations; they do not test the strategy → PE → XD → FE → rendered → measurement arc. Not confused with the per-pack activation evals.

**Roadmap action:** Keep in queue. Blocked until all M2–M4 specs ship.

---

#### M6 — Cross-Pack Integrative Guides

| Field | Value |
|---|---|
| Path | spec/digital-product-guides-update |
| Needs | work:spec/cross-pack-experience-eval (OPEN) |
| Spec.md | Not authored |
| Classification | **C. Genuinely Open** (blocked on cross-pack-experience-eval) |

**Evidence:** No end-to-end digital-product tutorial exists in guides/. Pack-level guides exist per discipline but no cross-pack intent index or integrative tutorial covers the full arc.

**Roadmap action:** Keep in queue. Blocked until cross-pack-experience-eval ships.

---

### Classification summary by discipline

| Discipline | Spec | Classification | Blocked on |
|---|---|---|---|
| Product Strategy | product-strategy-adoption-doctrine | C. Genuinely Open | — (unblocked) |
| Product Engineering | product-engineering-shaping-doctrine | C. Genuinely Open | — (unblocked) |
| XD (prerequisite) | xd-copy-direction | C. Genuinely Open | — (unblocked) |
| XD | xd-skill-boundaries | C. Genuinely Open | xd-copy-direction |
| XD | xd-design-system-foundations | C. Genuinely Open | xd-skill-boundaries |
| XD | xd-ia-archetypes-objects | C. Genuinely Open | xd-skill-boundaries |
| XD | xd-state-reviewer-doctrine | C. Genuinely Open | xd-skill-boundaries + xd-ia-archetypes-objects |
| Frontend Engineering | frontend-engineering-doctrine-update | **B. Partially Implemented** | — (unblocked; site/guide surfaces missing) |
| Cross-pack eval | cross-pack-experience-eval | C. Genuinely Open | All M2–M4 |
| Guides + profile | digital-product-guides-update | C. Genuinely Open | cross-pack-experience-eval |

---

## Backlog item status

### design-system-foundations-skill-gap

**Current state:** `needs = "ini-003:work:spec/xd-design-system-foundations"` — accurate. The XD skill does not exist; spec/xd-design-system-foundations is genuinely open. Note: FE SKILL.md already routes to `design-system-foundations` as a forward reference.

**Action:** Retain. Comment is accurate. Close when spec/xd-design-system-foundations ships.

---

### experience-reviewer-content-brief-scope

**Current state:** Open. Marked "Ready — RFC-0062 content-design-skill spec is Shipped."

**Evidence:** experience-reviewer.md frontmatter: "Does NOT fire on content briefs, tone-of-voice docs, or other direction artifacts." The reviewer explicitly excludes content briefs.

**Action:** Retain. Content-brief support is not implemented. Requires a follow-on RFC extending RFC-0062.

---

### digital-experience-contract-pe-journey-xref

**Current state (before reconciliation):** Comment claimed "No product-engineering journey page exists." This was stale.

**Evidence:** `web/src/content/journeys/product-engineering.md` EXISTS (`generated: true`). PE journey `whatChanges` field does not reference the Digital Experience Contract.

**Action:** Backlog comment corrected (2026-08-01) to note the journey exists but lacks the DEC cross-reference. File pointer corrected to the canonical source `packs/product-engineering/JOURNEY.md` — the generated web file (`web/src/content/journeys/product-engineering.md`) must not be edited directly; `build-self` projects from the pack source. `needs` edge to spec/product-engineering-shaping-doctrine retained — the shaping doctrine spec will update the PE journey, making it the natural point to add the DEC note coherently. Retain item.

---

### contract-drift-check-gate-promotion

**Current state (before reconciliation):** Tool path reference was stale (`tools/check-contract-drift.py`; relocated to `tools/repo/check_contract_drift.py` by ini-005 Wave 5 reorganisation; compat shim retained at old path until next minor).

**Evidence:** Tool exists at `tools/repo/check_contract_drift.py`. Compat shim at `tools/check-contract-drift.py` confirmed (docstring: "Shim → tools/repo/check_contract_drift.py (ini-005 Wave 5 reorganisation)"). One clean pass recorded 2026-08-01 on origin/main HEAD (exit 0, no output). No CI history of prior qualifying runs found. Two qualifying passes required; one recorded.

**Action:** Backlog comment corrected (2026-08-01): stale path reference fixed, move attributed to ini-005 Wave 5 (not Phase 0), compat shim noted, clean-run log added. Retain item. Unblocks after one more qualifying clean pass.

---

### digital-product-profile

**Current state:** `needs = "ini-003:work:spec/digital-product-guides-update"` — accurate. spec/digital-product-guides-update is genuinely open (blocked on cross-pack-experience-eval).

**Action:** Retain. Dependency chain is accurate. Profile creation deferred until all ini-003 specs ship and guide contract is complete.

---

## workspace.toml changes summary

| Change | File | Description |
|---|---|---|
| ini-003 milestone | workspace.toml | Updated "M1 · Contract + Governance" → "M2 · Adoption + Shaping Doctrine" with milestone advance note |
| ini-003 M4 comment | workspace.toml | Added parity baseline section; updated remaining delta to site/guide surfaces only |
| digital-experience-contract-pe-journey-xref | workspace.toml | Corrected stale "no journey page exists" claim; noted journey exists without DEC xref |
| contract-drift-check-gate-promotion | workspace.toml | Fixed stale tool path; added clean-run log entry (1 pass, 2026-08-01) |

---

## Final ini-003 state

| Field | Before | After |
|---|---|---|
| status | active | active (unchanged) |
| milestone | "M1 · Contract + Governance" | "M2 · Adoption + Shaping Doctrine" |
| work.shipped | 2 items | 2 items (unchanged) |
| work.queue | 10 items | 10 items (unchanged) |
| work.active | [] | [] (unchanged) |

---

## Known limitations and unexecuted checks

- No pack evals were run (PS, PE, XD, FE) — eval infrastructure confirmed present but LLM-judge runs require ANTHROPIC_API_KEY in CI.
- Cross-pack experience eval does not exist; not executable.
- Guide and journey builds were not run (no build server invoked).
- CI history for contract-drift clean runs not exhaustively searched; git log did not surface named entries.
- FE guides/frontend-engineering/reference/frontend-engineering.md content not fully reviewed to determine if it satisfies "performance reference quick-reference."
- XD skill boundary frontmatter not exhaustively reviewed — near-miss guards may be partially present in some skills.
- PS and PE skill frontmatter not exhaustively reviewed — some doctrine language may be partially present.

---

## Reviewer decisions

**Phase 0A:** Version contracts verified merge-order-safe without changes.

**Phase 0B:** 9 of 10 queue items classified genuinely open; 1 (FE doctrine) classified partially implemented with substantial core skill implementation present. No spec incorrectly marked complete. No spec was marked shipped.

---

## Final binary conclusion

**PHASE 0 COMPLETE**

All reconciliation actions are complete:
- Wave 3 and Wave 4 version contracts verified merge-order-safe (no changes needed).
- All 10 ini-003 queue items dynamically discovered and classified with evidence.
- ini-003 milestone corrected to reflect the first genuinely unfinished milestone.
- Two stale backlog comments corrected (PE journey claim, contract-drift tool path).
- M4 (FE doctrine) correctly identified as partially implemented; workspace.toml queue comment updated to remaining delta.
- No missing doctrine implementation was pulled into this reconciliation.
- No AgentBundle version or pack version changed.
- No spec was marked shipped without executable evidence.

---

## Phase 0B addendum — spec-index verification (2026-08-01)

**Verification commit:** d2f74a5e (`feat(site-design-system-spec): design token reference doc + zone-violation lint`)  
**Branch:** eugene/baton-rouge (at origin/main HEAD)  
**Trigger:** AC24 — "docs/specs/README.md accurately reflects real spec status."

Two post-Phase-0 commits landed before this verification run:
- `ef5f9a68` — workspace-status progressive read modes: adds core spec (not ini-003). No ini-003 queue item classification affected.
- `d2f74a5e` — site-design-system-spec design token reference + zone-violation lint: closes a site spec (not ini-003). No ini-003 queue item classification affected.

### Spec-index corrections

`docs/specs/README.md` is a hand-maintained active-spec index. At verification, 13 entries showed a status that differed from the spec.md on disk. All 13 were stale (README showed Draft, Implementing, or Approved; spec.md showed Shipped). Corrected in this PR:

| Slug | README had | Corrected to |
|------|-----------|-------------|
| site-ui-primitives | Draft | Shipped |
| jira-activation-reframe | Draft | Shipped |
| agentbundle-first-value-handoff | Draft | Shipped |
| m3-experience-design-rename | Draft | Shipped |
| m3-desk-research-rename | Draft | Shipped |
| m1-brief-queue | Implementing | Shipped |
| m1-governance-integration | Implementing | Shipped |
| catalogue-runtime-inventory | Draft | Shipped |
| platform-site | Implementing | Shipped |
| extraction-higher-tiers | Draft | Shipped |
| extraction-msg-to-markdown-python-contract | Draft | Shipped |
| render-proof | Approved | Shipped |
| m1-work-queue | Implementing | Shipped |

Post-correction verification: all 13 corrected entries (and all other listed entries) match spec.md on disk — 0 row-level mismatches. Note: index completeness (active specs absent from the index entirely) is a separate, deferred concern; four specs were found missing from the index (`catalogue-curation-qa-coverage`, `catalogue-wave3-enterprise-authoring-discovery`, `catalogue-wave4-semantic-contracts-index`, `catalogue-wave8-readme-contributing`).

### copy-direction-skill nuance

`docs/specs/copy-direction-skill/spec.md` — Status: Shipped. However, the spec's acceptance criteria assert that `packs/experience-design/.apm/skills/copy-direction/SKILL.md` exists; that file does not exist on disk. No copy-direction guidance was added to `tone-of-voice` either. This is pre-existing spec drift (the spec is marked Shipped with an unmet AC) outside the scope of this PR — registered here for follow-up.

The ini-003 queue item `xd-copy-direction` (tracked as `spec/xd-copy-direction`) refers to the full copy-direction skill designed by RFC-0062 (accepted by RFC-0071, per `workspace.toml`). No `copy-direction/` skill directory exists in `packs/experience-design/.apm/skills/`. Classification remains **C (genuinely open, ready to start)** — the `copy-direction-skill` spec is not a fulfillment of the xd-copy-direction queue item.
