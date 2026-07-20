# Plan: product-strategy-pack (v1)

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. When it changes
> substantially, note why in the changelog at the bottom.

## Approach

A pure-markdown, opt-in, user-scope pack — no code, no infra, no seeds. Scaffold the pack and register it (T1), then author 9 skills across 3 pillars (T2–T10); T2–T10 are all independent of one another after T1 lands and can be dispatched in parallel. The ADR (T11) and the layout/sweep tasks (T12–T13) close the loop.

The riskiest part of each skill is **restraint**: keeping each SKILL.md under 100 lines while referencing (not reprinting) the canonical frameworks. The `lint-skill-spec.py` gate enforces the ceiling mechanically. The cross-pack routing contract in `run-okr-cascade` (T6) is the most behavior-dense skill — it must write to `[shaping_queue].backlog` and emit the absent-PE-pack diagnostic; it has its own `references/cross-pack-routing.md` for depth.

**Verification:** goal-based (file presence, lint gates, line counts) + manual QA per skill (cold-invoke and record the artifact shape). No TDD — there is no runtime logic.

## Constraints

- **RFC-0063** (Accepted 2026-07-19) — the binding proposal; D1–D10 are settled; growth strategy (OQ1) and experience mapping (OQ2) are deferred and must not appear in v1 skills.
- **ADR-0024** — pure-markdown guardrail; no values tables, no stack tokens, no framework text verbatim.
- **RFC-0004 Rail A** — user-scope pack, no `seeds/` directory.
- **RFC-0040** — pack declares artifact output via `[pack.layout.repo] parent = "docs/product/shaping"` in `pack.toml`; each skill ships `references/agentbundle-layout.md` documenting the adopter-owned `[product-strategy]` section they may configure. The adopter's `agentbundle-layout.toml` is never edited by this pack.
- **RFC-0037 / ADR-0028** — each skill ships `evals/eval_queries.json` + `evals/evals.json`; registered in `[pack.evals] skills`.
- **AGENTS.md CHARTER.md** — no hooks, no engines, no new subagent; habits-shaped.

## Construction tests

All verification is goal-based or manual QA per the spec's Testing Strategy. There is no unit-testable runtime logic; the spec's testing table maps to the per-task `Done when:` conditions below.

**Integration sweep (T13):** `make lint-packs`, `make validate`, `make build`, `tools/lint-skill-spec.py` all green; grep of `packs/product-strategy/` shows no `hooks/`, `agents/`, `*.py` validators, or `seeds/` directory.

**Manual QA sweep (T13):** cold-invoke each of the 9 skills; record that the output contains the named artifact path, the framework reference, and (for `run-okr-cascade`) a shaping-queue entry and the absent-PE-pack diagnostic.

## Design (LLD)

This is a content/skill pack; there is no code architecture. The design is the file layout and the per-skill artifact schema.

### File layout

```
packs/product-strategy/
├── pack.toml
├── README.md
└── .claude-plugin/
│   └── plugin.json
└── .apm/
    └── skills/
        ├── run-swot/
        │   ├── SKILL.md
        │   ├── references/
        │   │   └── agentbundle-layout.md
        │   └── evals/
        │       ├── eval_queries.json
        │       └── evals.json
        ├── run-porters-five-forces/       (same shape)
        ├── run-pestle-analysis/            (same shape)
        ├── run-bcg-matrix/                 (same shape)
        ├── run-okr-cascade/
        │   ├── SKILL.md
        │   ├── references/
        │   │   ├── agentbundle-layout.md
        │   │   └── cross-pack-routing.md   ← routing contract depth
        │   └── evals/
        ├── write-prfaq/                    (same shape as run-swot)
        ├── synthesize-stakeholder-research/ (same shape)
        ├── define-ux-strategy/             (same shape)
        └── define-content-strategy/        (same shape)
```

### Skill SKILL.md shape (all 9)

Frontmatter: `name:`, `description:`, `triggers:` (elicitation phrases). Body: `## When to invoke`, `## Procedure` (≥5 numbered steps ending with committed artifact), `## Anti-patterns` (what the skill does NOT do). `<100` lines; depth in `references/`.

### Cross-pack routing (run-okr-cascade only)

The `run-okr-cascade` skill's Procedure step 4 writes each identified gap as a `{type = "strategy", slug = "<gap-slug>"}` entry (no `needs` field — no-dependency entries omit it) to the appropriate initiative's `[shaping_queue].backlog` in `workspace.toml`. Step 5 surfaces the PE pack absent diagnostic if `frame-situation` is not found. Full contract detail in `references/cross-pack-routing.md`.

`check-workspace` line 98 is updated as part of T6: the `strategy` row changes from "run product-strategy pack skill" to "route through `frame-situation` (PE pack — M2); if not yet available, run `frame-intent` as interim" — matching the progressive-disclosure pattern already used for the `shape` type.

### Artifact commit convention (all artifact-writing skills)

Each skill's Procedure closes with: *"Commit artifact to `docs/product/shaping/<artifact-name>.md` (or the path in the adopter's `[product-strategy]` section of their own `agentbundle-layout.toml` if configured)."* Three-tier resolution: config → default (`docs/product/shaping/`) → discover-by-marker (`type: <artifact-type>` frontmatter). The adopter's `agentbundle-layout.toml` is never shipped with the catalogue pack.

## Tasks

### T1: Pack scaffold + marketplace and layout registration

**Depends on:** none
**Touches:** `packs/product-strategy/pack.toml`, `packs/product-strategy/.claude-plugin/plugin.json`, `packs/product-strategy/README.md`, `.claude-plugin/marketplace.json`

**Tests:**
- Goal-based: `make lint-packs` and `make validate` pass with the new pack present (AC1).
- Goal-based: `make build` green; `marketplace.json` lists `product-strategy` with name + description + version (AC1).
- Goal-based: `packs/product-strategy/pack.toml` contains a `[pack.layout.repo]` table with `parent = "docs/product/shaping"` (AC3 — pack.toml, not a central agentbundle-layout.toml; that file is adopter-owned and never shipped).

**Approach:**
- Mirror `packs/experience-design/pack.toml`: `name = "product-strategy"`, `version = "0.1.0"`, `description` (3-pillar summary), `default-scope = "user"`, `allowed-scopes = ["user", "repo"]`, `adapter-contract.version = "0.12"`, adapters list matching experience-design, `[pack.layout.repo] parent = "docs/product/shaping"`.
- `plugin.json`: `{"name": "product-strategy", "version": "0.1.0", "description": "..."}`.
- `README.md`: what the pack is, the three pillars, install snippet, what is NOT in this pack (growth strategy, primary research, per-surface content design), upstream/downstream pack chain diagram.
- Add `product-strategy` entry to `.claude-plugin/marketplace.json` in alphabetical order (after `product-engineering`), category `product-management`. This file is hand-authored; verify with `make build` but do not run `build-self` (pack is user-scope, not in self-host projection scope).
- `[pack.evals] skills = []` — populated by T2–T10 as skills land, or set all 9 slugs upfront if authoring in one PR.

**Done when:** `lint-packs`, `validate`, `build` green; `marketplace.json` updated; `pack.toml` contains `[pack.layout.repo] parent = "docs/product/shaping"`. (No `agentbundle-layout.toml` edit — that file is adopter-owned.)

---

### T2: `run-swot` skill

**Depends on:** T1
**Touches:** `packs/product-strategy/.apm/skills/run-swot/**`

**Tests:**
- Goal-based: `lint-skill-spec.py` exits 0; `SKILL.md` < 100 lines (AC4).
- Goal-based: `evals/` contains both JSON files; slug in `[pack.evals] skills` (AC6).
- Manual QA: cold-invoke with a sample organization context; confirm output names `swot-analysis.md` artifact path, SWOT quadrant structure (Strengths/Weaknesses/Opportunities/Threats), and no verbatim SWOT definition text.

**Approach:**
- `SKILL.md`: When to invoke ("I need a situation synthesis before setting strategy"); Procedure — elicit context (org/product/market scope) → author four quadrants → identify strategic implications → commit `swot-analysis.md` to `docs/product/shaping/`; Anti-patterns (not a substitute for market data; must have a defined scope).
- `references/agentbundle-layout.md`: three-tier artifact path resolution.
- `evals/eval_queries.json`: 3–5 trigger phrases (e.g., "I need to understand our competitive position", "run a SWOT analysis on...").
- `evals/evals.json`: Tier-4 LLM-judge rubric — checks artifact name, quadrant structure, and framework name cited without verbatim framework text.

**Done when:** `lint-skill-spec` green; `SKILL.md` < 100 lines; eval files present; manual-QA walk recorded.

---

### T3: `run-porters-five-forces` skill

**Depends on:** T1
**Touches:** `packs/product-strategy/.apm/skills/run-porters-five-forces/**`

**Tests:**
- Goal-based: `lint-skill-spec.py` exits 0; `SKILL.md` < 100 lines (AC4).
- Goal-based: eval files present; slug in `[pack.evals] skills` (AC6).
- Manual QA: cold-invoke with a sample industry; confirm output names `competitive-landscape.md`, references five forces by name (Supplier Power, Buyer Power, Threat of New Entrants, Threat of Substitutes, Competitive Rivalry), and does not reprint Michael Porter's framework text.

**Approach:**
- `SKILL.md`: When to invoke ("I need to understand the competitive landscape"); Procedure — establish industry boundary → assess each force (elicit evidence for each) → synthesize strategic implications → commit `competitive-landscape.md`.
- `references/agentbundle-layout.md`, `evals/` — same pattern as T2.

**Done when:** same gate pattern as T2.

---

### T4: `run-pestle-analysis` skill

**Depends on:** T1
**Touches:** `packs/product-strategy/.apm/skills/run-pestle-analysis/**`

**Tests:**
- Goal-based: `lint-skill-spec.py` exits 0; `SKILL.md` < 100 lines; eval files present (AC4, AC6).
- Manual QA: cold-invoke; confirm output names `macro-environment.md`, six PESTLE dimensions named (Political, Economic, Social, Technological, Legal, Environmental).

**Approach:**
- `SKILL.md`: When to invoke ("I need to understand the macro environment"); Procedure — establish scope (geography + time horizon) → assess each dimension → prioritize implications by impact and time-horizon → commit `macro-environment.md`.
- Anti-patterns: PESTLE is a scan, not a forecast; each dimension requires grounding in observable fact.

**Done when:** same gate pattern as T2.

---

### T5: `run-bcg-matrix` skill

**Depends on:** T1
**Touches:** `packs/product-strategy/.apm/skills/run-bcg-matrix/**`

**Tests:**
- Goal-based: `lint-skill-spec.py` exits 0; `SKILL.md` < 100 lines; eval files present (AC4, AC6).
- Manual QA: cold-invoke with a sample product portfolio; confirm output names `portfolio-position.md`, references four quadrants by name (Stars, Cash Cows, Question Marks, Dogs), does not mandate specific market-share metrics the user has not supplied.

**Approach:**
- `SKILL.md`: When to invoke ("I need to assess portfolio position"); Procedure — elicit portfolio (list of products/offerings) → estimate relative market share and market growth for each (elicit or estimate with caveats) → map to quadrants → derive investment implications → commit `portfolio-position.md`.
- Anti-patterns: BCG assumes market share data; the skill surfaces caveats when data is estimated.

**Done when:** same gate pattern as T2.

---

### T6: `run-okr-cascade` skill

**Depends on:** T1
**Touches:** `packs/product-strategy/.apm/skills/run-okr-cascade/**`, `packs/core/.apm/skills/check-workspace/SKILL.md` (line 98 routing fix — decided)

**Tests:**
- Goal-based: `lint-skill-spec.py` exits 0; `SKILL.md` < 100 lines; eval files present (AC4, AC6).
- Goal-based: `grep -r "shaping_queue" packs/product-strategy/.apm/skills/run-okr-cascade/` returns a hit (AC7 cross-pack routing).
- Goal-based: `grep -r "frame-situation not found" packs/product-strategy/.apm/skills/run-okr-cascade/` returns the diagnostic string (AC7).
- Goal-based: `grep "frame-situation" packs/core/.apm/skills/check-workspace/SKILL.md` returns a hit on the `strategy` row confirming the routing was updated (AC7 check-workspace fix).
- Manual QA: cold-invoke with sample company OKRs; confirm output includes `okr-cascade.md` artifact, at least one `{type = "strategy"}` shaping-queue entry, and the absent-PE-pack diagnostic is described in the skill.

**Approach:**
- `SKILL.md`: When to invoke ("I need to cascade company OKRs and identify gaps"); Procedure — elicit company OKRs (or read from `docs/product/shaping/`) → derive team-level OKRs → identify gaps between current state and OKR targets → commit `okr-cascade.md` → resolve target initiative (single active `["ini-NNN"]` section auto-resolved; if multiple active, elicit from user) → append each gap as `{type = "strategy", slug = "<gap-slug>"}` to the initiative's `[shaping_queue].backlog` in `workspace.toml` → if `frame-situation` not found emit the diagnostic.
- `packs/core/.apm/skills/check-workspace/SKILL.md` line 98: change `strategy` row from `"run product-strategy pack skill (requires product-strategy pack — M4)"` to `"route through frame-situation (PE pack — M2); if not yet available, run frame-intent as interim"`. One-line edit only.
- `references/cross-pack-routing.md`: full contract detail — the seven-step sequence, `{type = "strategy", slug = "..."}` entry format (no `needs` field), the initiative-resolution logic, the check-workspace routing fix rationale, the graceful-absent diagnostic, and the co-install note.
- `references/agentbundle-layout.md`: artifact path resolution.
- Anti-patterns: OKR cascade is org-wide alignment, not per-feature goal-setting (distinct from Pillar 2's Gothelf/Seiden OKR-linked UX framing); do not author feature-level OKRs here.

**Done when:** `lint-skill-spec` green; `SKILL.md` < 100 lines; routing contract greps pass; check-workspace grep passes; eval files present; manual-QA walk recorded.

---

### T7: `write-prfaq` skill

**Depends on:** T1
**Touches:** `packs/product-strategy/.apm/skills/write-prfaq/**`

**Tests:**
- Goal-based: `lint-skill-spec.py` exits 0; `SKILL.md` < 100 lines; eval files present (AC4, AC6).
- Manual QA: cold-invoke with a sample product idea; confirm output names `prfaq.md`, contains a press-release section and a FAQ section, references the Amazon PRFAQ format by name without reprinting it.

**Approach:**
- `SKILL.md`: When to invoke ("I need to write the press release before the product", "I need an altitude-0 forcing function"); Procedure — elicit product concept + target customer + problem → author press release (headline, sub-headline, problem, solution, call to action, quote) → author FAQ (customer-facing then internal) → commit `prfaq.md`.
- Anti-patterns: PRFAQ is not a spec; it is an altitude-0 direction artifact; the skill does not produce a backlog.

**Done when:** same gate pattern as T2.

---

### T8: `synthesize-stakeholder-research` skill

**Depends on:** T1
**Touches:** `packs/product-strategy/.apm/skills/synthesize-stakeholder-research/**`

**Tests:**
- Goal-based: `lint-skill-spec.py` exits 0; `SKILL.md` < 100 lines; eval files present (AC4, AC6).
- Goal-based: `grep -r "desk-research project first" packs/product-strategy/.apm/skills/synthesize-stakeholder-research/` returns the absent-input diagnostic string (AC8).
- Manual QA: cold-invoke with a description of existing stakeholder research outputs; confirm output names `stakeholder-synthesis.md`, organizes by strategic theme (not by stakeholder), surfaces the absent-input diagnostic when no research inputs are described.

**Approach:**
- `SKILL.md`: When to invoke ("I need to turn stakeholder research into strategic direction"); Procedure — discover research inputs (look for desk-research outputs in `docs/research/` or adopter-supplied paths; surface the absent-input diagnostic if none found) → identify strategic themes across stakeholder perspectives (executive, user, regulator) → author synthesis narrative per theme → commit `stakeholder-synthesis.md`.
- Anti-patterns: does not produce raw research; does not conduct interviews; does not write discussion guides (those are desk-research pack capabilities).

**Done when:** same gate pattern as T2; absent-input diagnostic grep passes.

---

### T9: `define-ux-strategy` skill

**Depends on:** T1
**Touches:** `packs/product-strategy/.apm/skills/define-ux-strategy/**`

**Tests:**
- Goal-based: `lint-skill-spec.py` exits 0; `SKILL.md` < 100 lines; eval files present (AC4, AC6).
- Manual QA: cold-invoke with a sample product + business goal; confirm output names `ux-strategy.md`; references NN/g three-layer model (vision → goals+measures → plan), Jaime Levy four tenets, and Gothelf/Seiden OKR-linked UX framing by name; does not reprint their framework text; documents its position upstream of `experience-design`'s `journey-mapping`.

**Approach:**
- `SKILL.md`: When to invoke ("I need to set the experience strategy before design begins"); Procedure — establish the vision layer (what the end-to-end experience should achieve; aligned with market strategy) → define goals and measures (what signals tell us the vision is being realized) → author the plan (initiatives the design work must deliver; sequenced, time-horizoned) → commit `ux-strategy.md`.
- Framework references (by name, not verbatim): NN/g three-layer model for document structure; Levy four tenets as a quality check (business strategy + value innovation + validated user research + killer UX); Gothelf/Seiden OKR-linked UX framing for the goals+measures layer.
- Anti-patterns: `define-ux-strategy` is upstream of journey mapping; it does not produce a customer journey map (that is `journey-mapping` in the experience-design pack).

**Done when:** same gate pattern as T2; framework names appear in SKILL.md (grep-checked).

---

### T10: `define-content-strategy` skill

**Depends on:** T1
**Touches:** `packs/product-strategy/.apm/skills/define-content-strategy/**`

**Tests:**
- Goal-based: `lint-skill-spec.py` exits 0; `SKILL.md` < 100 lines; eval files present (AC4, AC6).
- Manual QA: cold-invoke with a sample organization/product; confirm output names `content-strategy.md`; references Halvorson content strategy quad (Purpose, Process, Structure, Governance) by name; documents the organizational/governance-layer vs. per-surface execution distinction.

**Approach:**
- `SKILL.md`: When to invoke ("I need to set the content strategy before content design begins"); Procedure — establish Purpose (what content exists and why; connected to org goals) → Process (how content is created, governed, maintained; who owns it) → Structure (content models, metadata architecture, taxonomy) → Governance (standards for consistency, accuracy, and relevance) → commit `content-strategy.md`.
- Framework reference (by name): Halvorson/Brain Traffic content strategy quad (2018 revision).
- Anti-patterns: content strategy is the organizational/governance layer; per-surface content design is the `content-design` skill in the experience-design pack; this skill does not produce per-surface briefs.
- Hand-off: `content-strategy.md` is consumed by the experience-design pack's `content-design` skill and the design-thread `map-screen-flow` step.

**Done when:** same gate pattern as T2; Halvorson quad named in SKILL.md.

---

### T11: ADR-0053 — product-strategy pack scope and discipline boundaries

**Depends on:** T1 (scaffold confirms pack name); can be authored concurrently with T2–T10
**Touches:** `docs/adr/0053-product-strategy-pack-scope-and-discipline-boundaries.md`

**Tests:**
- Goal-based: file exists at the exact path; frontmatter status is `Accepted`; body references all 10 RFC-0063 decisions (D1–D10) — verified by `grep -c "D[0-9]" docs/adr/0053-*.md` returning ≥ 10 (AC11).

**Approach:**
- Author from the `new-adr` skill template. Key sections:
  - **Context:** The catalogue gap (strategist has no skills upstream of experience-design or product-engineering); RFC-0063 as the decision record.
  - **Decision:** Create `product-strategy` pack (D1); market/UX/content-strategy as three pillars (D2/D3); growth strategy deferred (D4/OQ1 resolved); full 9-skill v1 set (D5/D6/D7); stakeholder research as Pillar-1 capstone, not a fourth pillar (D8); agent-mediated OKR → `frame-situation` routing via `[shaping_queue]` (D9); market intelligence as a named concept, not a separate skill (D10).
  - **Cross-pack routing contract:** the seven-step sequence and boundary (product-strategy writes; PE reads; neither calls the other directly).
  - **Growth strategy deferral:** operational character of AARRR/PLG/PMF warrants a separate `growth` pack; v1 excludes it.
  - **Experience mapping deferral:** closer in character to journey-mapping in experience-design; deferred to a follow-on RFC extending RFC-0050/RFC-0066.
  - **Consequences:** new top-level pack (approved by RFC-0063); no change to existing packs beyond cross-reference notes.

**Done when:** file exists; status Accepted; D1–D10 all referenced.

---

### T12: Cross-reference sweep, backlog update, and RFC-0062 reconciliation

**Depends on:** T1 (pack name confirmed)
**Touches:** `docs/backlog.md`, `packs/product-engineering/README.md`, `packs/experience-design/README.md`, `docs/product/journeys/product-strategist-sets-direction.md` (read-only verify: `docs/rfc/0062-content-design-and-copy-direction-skills.md` — no edit expected)

**Tests:**
- Goal-based: `grep "product-strategy pack" docs/rfc/0062-content-design-and-copy-direction-skills.md` returns ≥ 2 hits confirming the file already uses `product-strategy pack` (no edit expected; test confirms pre-condition) (AC12).
- Goal-based: `grep "growth-strategy" docs/backlog.md` returns a hit in a new open entry (AC12).
- Goal-based: `grep "experience-mapping" docs/backlog.md` returns a hit in a new open entry (AC12).
- Goal-based: `grep "product-strategy" packs/product-engineering/README.md` and `packs/experience-design/README.md` each return a hit in a new cross-reference note (AC13).

**Approach:**
1. **RFC-0062 verification:** `grep "product-strategist" docs/rfc/0062-*.md` — if it returns zero hits, no edit is needed; record in the PR as "RFC-0062 already uses `product-strategy pack` — no edit required." If it returns hits, apply the two-word rename as an erratum-class correction per RFC-0055. (Based on spec-time inspection, no edit is expected.)
2. **Backlog.md:** Under `content-strategy-and-marketing-copy-lens`, mark the content-strategy thread as resolved (shipped via RFC-0063). Add two new open entries: `### growth-strategy-pack` (deferred from RFC-0063 OQ1; follow-on RFC when product-strategy v1 is in implementation) and `### experience-mapping-extension` (deferred from RFC-0063 OQ2; extend experience-design via follow-on RFC extending RFC-0050/RFC-0066).
3. **Cross-reference notes:** Add a brief "Upstream: product-strategy" note to `packs/product-engineering/README.md` (in a pack-chain section) and a similar note to `packs/experience-design/README.md`, summarizing the cross-pack routing contract and feed relationships (one paragraph each).
4. **Journey file:** Read `docs/product/journeys/product-strategist-sets-direction.md`; verify the 9-skill set, staging table, and cross-pack routing contract detail match the shipped skills. No status change needed (already `planned`). Record any corrections found as fixes in the implementing PR.

**Done when:** RFC-0062 verified (or corrected if needed); backlog entries present; cross-reference notes added; journey file verified.

---

### T13: Full gate sweep + changelog

**Depends on:** T1–T12
**Touches:** `docs/product/changelog.md`, `docs/specs/README.md`, `packs/product-strategy/pack.toml` (final `[pack.evals] skills` list if not already complete)

**Tests:**
- Goal-based: `make lint-packs`, `make validate`, `make build`, `tools/lint-skill-spec.py`, and the package `pytest` suite all green (AC15).
- Goal-based (structural Never): `find packs/product-strategy -name "*.py" -o -name "hooks" -o -name "agents" | head -1` returns empty; `find packs/product-strategy -name "seeds" | head -1` returns empty (AC15).
- Goal-based: every `SKILL.md` under `packs/product-strategy/` is `< 100` lines (`wc -l packs/product-strategy/.apm/skills/*/SKILL.md | grep -v total | awk '{if ($1 >= 100) print $0}'` returns empty) (AC15).
- Goal-based: `grep "product-strategy" docs/product/changelog.md` returns an `[Unreleased]` entry (AC14).
- Goal-based: `grep "product-strategy-pack" docs/specs/README.md` returns a hit (spec registered in index) (AC — spec index registration).

**Approach:**
1. Finalize `[pack.evals] skills` list in `pack.toml` to include all 9 slugs.
2. Add `[Unreleased]` entry to `docs/product/changelog.md`: "Add `product-strategy` pack (v0.1.0) — 9 skills across 3 pillars (market/competitive strategy, UX strategy, content strategy); implements RFC-0063 M4."
3. Add `product-strategy-pack` to `docs/specs/README.md` active list.
4. Run full local gate sweep; fix any lint findings.

**Done when:** all gates green; changelog + spec index updated; structural Never greps empty.

## Rollout

- **Delivery:** additive, opt-in, user-scope pack. No flag, no migration, fully reversible (delete the pack dir + marketplace.json entry). Nothing irreversible. (No `agentbundle-layout.toml` entry was added — that file is adopter-owned.)
- **Infrastructure:** none.
- **External-system integration:** none — the `workspace.toml` write in `run-okr-cascade` is agent-authored markdown; no live API.
- **Deployment sequencing:** T1 first (pack scaffold must exist for linters to pass); T2–T10 parallelizable; T11–T12 parallelizable after T1; T13 after all.

## Risks

- **SKILL.md over the 100-line ceiling** — the most common failure mode for a framework-reference-heavy skill. Mitigation: push all framework depth into `references/` from the first draft; the `lint-skill-spec.py` gate catches it mechanically.
- **Framework text creep (ADR-0024 violation)** — temptation to paste the Halvorson quad, Porter forces, etc. verbatim. Mitigation: `lint-experience-agnostic.py`-style enforcement if applicable; manual review in T13 gate sweep.
- **Cross-pack routing contract drift** — the `run-okr-cascade` routing contract is the most behavior-dense part; if the workspace.toml `[shaping_queue]` format changes, the skill becomes wrong. Mitigation: document the format in `references/cross-pack-routing.md` with a pointer to the workspace.toml specification so a future change triggers a skill update.
- **ADR number collision** — a concurrent PR may claim 0053. Mitigation: verify `ls docs/adr/ | sort | tail -3` at T11 start and renumber if needed.

## Changelog

- 2026-07-19: initial plan. Scope: 9-skill pack (RFC-0063 D5/D6/D7 Accepted), full mode (structural change + multi-feature).
