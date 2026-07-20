# Spec: product-strategy-pack (v1)

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0063 (D1–D10, OQ1 resolved: growth deferred, OQ2 resolved: experience mapping deferred to experience-design), ADR-0024 (pure-markdown guardrail extended by analogy — same posture as experience-design), RFC-0040 (consolidated-pack-layout: pack declares default output path via `[pack.layout.repo]` in `pack.toml` and ships per-skill `references/agentbundle-layout.md`; adopter's `agentbundle-layout.toml` is their own file, never shipped with the catalogue), RFC-0004 Rail A (user-scope: no `seeds/`, skill assets only)
- **Brief:** none
- **Contract:** none — pure-markdown skills + skill assets; no API/event/RPC interface. All committed artifacts are markdown documents written to `docs/product/shaping/`; no machine contract is published.
- **Shape:** new pack — a new top-level `packs/product-strategy/` directory; 9 SKILL.md files across 3 pillars; pack registration in `marketplace.json`; `pack.toml [pack.layout.repo]` table (declares default artifact parent — no adopter-owned `agentbundle-layout.toml` is edited); ADR recording D1–D10; cross-reference sweep.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A product strategist — a CPO, senior PM, or founder wearing the strategy hat — installs the `product-strategy` pack and gets a disciplined, recognizable set of skills for the upstream work that neither the `experience-design` nor `product-engineering` pack covers: competitive landscape analysis, OKR cascade, PRFAQ, UX strategy, and content strategy. Running the skills produces a committed set of altitude-0 artifacts in `docs/product/shaping/` that feed the product-engineering pack's `frame-situation` shaping queue and the experience-design pack's journey-mapping entry point.

v1 delivers three pillars (D2, D3): 7 Pillar-1 market/competitive skills, 1 Pillar-2 UX-strategy skill, 1 Pillar-3 content-strategy skill — 9 skills total (D5, D6, D7). Growth strategy is deferred to a follow-on `growth` pack (OQ1). Experience mapping is deferred to the experience-design pack as an upstream extension (OQ2).

Success: the strategist runs `run-swot`, `run-okr-cascade`, or any of the other skills cold, receives a named artifact in `docs/product/shaping/`, and — after the OKR cascade — has gap entries in `workspace.toml`'s `[shaping_queue].backlog` ready for the product engineer's `frame-situation` step.

## Boundaries

### Always do

- Scaffold the pack at `packs/product-strategy/` with `pack.toml` (including `[pack.layout.repo] parent = "docs/product/shaping"`), `.claude-plugin/plugin.json`, `README.md`; register in `.claude-plugin/marketplace.json`. Do NOT edit the adopter-owned `agentbundle-layout.toml` — it is never shipped with the catalogue.
- Keep every `SKILL.md` **under 100 lines**; push depth (framework detail, artifact schema, worked examples) into `references/`, loaded on demand.
- Keep the pack **pure markdown** and **habits-shaped**: skills + `references/` + skill `assets/` only — no seeds, no hooks, no engines (RFC-0004 Rail A; ADR-0024 extended by analogy).
- Commit all artifacts to `docs/product/shaping/` by default; document the three-tier layout resolution (config → default → discover-by-marker) in each artifact-writing skill's `references/agentbundle-layout.md`.
- Name skills using the verb-noun convention established by the pack chain: `run-<framework>` for analysis skills, `write-<artifact>` for narrative skills, `synthesize-<input>` for synthesis skills, `define-<discipline>` for strategy-direction skills.
- Ship `evals/eval_queries.json` + `evals/evals.json` under each skill directory per RFC-0037 (pack-activation-evals); register each skill in `[pack.evals] skills` in `pack.toml`.
- Author the cross-pack routing contract (`run-okr-cascade` → `[shaping_queue].backlog`) exactly as specified in RFC-0063 §Cross-pack routing contract — agent-mediated, no mechanical cross-pack call; absent PE pack → named diagnostic.
- Author ADR-0053 recording D1–D10, the cross-pack routing contract design, and the growth/experience-mapping deferral reasoning.

### Ask first

- Before adding any skill beyond the 9 in D5/D6/D7.
- Before adding a `seeds/` directory (would change the scope to repo-scope under RFC-0004 Rail A; this pack is user-scope).
- Before introducing a new adapter-contract version beyond the current baseline.
- Before adding any agent definition (no subagent is chartered in RFC-0063; it would hit the 3-reviewer ceiling in CHARTER.md).

### Never do

- **Never** ship a hook, engine, validator/linter script, or new subagent in this pack (habits, not infrastructure; ADR-0024).
- **Never** produce primary research — no discussion guides, interview scripts, or survey templates; `synthesize-stakeholder-research` consumes existing `desk-research` pack outputs; it does not produce raw research (RFC-0063 §Stakeholder research and market intelligence scope).
- **Never** reprint the text of Porter's Five Forces, Halvorson quad, NN/g model, Jaime Levy tenets, BCG Matrix, PESTLE, SWOT, or PRFAQ templates verbatim — name and reference them; never quote them wholesale (ADR-0024 framework-agnosticism guardrail).
- **Never** make a mechanical cross-pack call to `frame-situation`; the routing contract is agent-mediated via `[shaping_queue]` (RFC-0063 D9).
- **Never** add a values table, stack token, or platform primitive to any SKILL.md (ADR-0024).
- **Never** produce analytics frameworks, CRO tooling, SEO keyword plans, or growth experiment designs — those are out of scope for v1 (OQ1 deferred).

## Testing Strategy

This is a content/skill pack (an LLM workflow), not application code, so there is no compressible-invariant logic to TDD. Verification is **goal-based** for structure and **manual QA** for judgment and artifact shape.

- **Pack scaffold + registration: goal-based.** `make lint-packs`, `make validate`, `make build` pass; `marketplace.json` lists `product-strategy` with name + description + version; `pack.toml` contains a `[pack.layout.repo]` table with `parent = "docs/product/shaping"`; a `lint-skill-spec.py` pass on every `SKILL.md` exits 0. Note: `marketplace.json` is **aggregated by `make build-self`** from every pack's `.claude-plugin/plugin.json` — create `packs/product-strategy/.claude-plugin/plugin.json`, then run `make build-self` (with `FORCE=1` if the tree is dirty) to register the pack. Skills are user-scope and not projected into the self-host skill scope, but marketplace aggregation runs for all packs regardless.
- **SKILL.md structural shape: goal-based.** Each of the 9 files: frontmatter includes `name:` and a non-empty `description:`; `## Procedure` section has ≥5 numbered steps; `<100` lines (wc -l); `lint-skill-spec.py` exits 0.
- **Eval files: goal-based.** `find packs/product-strategy/.apm/skills/<skill>/evals/ -name "*.json"` returns both `eval_queries.json` and `evals.json` for every skill; each skill is listed in `[pack.evals] skills` in `pack.toml`.
- **Artifact path contract: goal-based.** `grep -r "docs/product/shaping" packs/product-strategy/` returns a hit in each artifact-writing skill's `references/agentbundle-layout.md` or SKILL.md.
- **Cross-pack routing contract: goal-based.** `grep -r "shaping_queue" packs/product-strategy/.apm/skills/run-okr-cascade/` returns a hit in SKILL.md or a `references/` file; `grep -r "frame-situation not found" packs/product-strategy/` returns the diagnostic string.
- **`check-workspace` routing fix: goal-based.** `grep -n "strategy.*frame-situation" packs/core/.apm/skills/check-workspace/SKILL.md` returns hits on both the output template row (line 65) and the routing table row (line 98), confirming both were updated.
- **Manual QA — skill invocation.** Cold-prompt each of the 9 skills with a minimal context. Record that the output contains:
  - The named artifact type (e.g., `swot-analysis.md`, `competitive-landscape.md`)
  - The correct framework reference (framework name cited, not reproduced verbatim)
  - The target artifact path under `docs/product/shaping/`
  - For `run-okr-cascade`: at least one `{slug = "...", type = "strategy"}` entry landing under `["ini-NNN".shaping_queue].backlog` (not a top-level `[shaping_queue]` table), and the PE pack absent diagnostic when no `frame-situation` is installed.
- **ADR-0053: goal-based.** The file exists at `docs/adr/0053-<slug>.md` with status Accepted and references all 10 RFC-0063 decisions (D1–D10).
- **Linter and gate sweep: goal-based.** `make lint-packs`, `make validate`, `make build`, `tools/lint-skill-spec.py`, and the package `pytest` suite all green after all tasks land.

## Acceptance Criteria

- [x] A new pack exists at **`packs/product-strategy/`** with `pack.toml` (`name = "product-strategy"`, `version = "0.1.0"`, `default-scope = "user"`, `allowed-scopes = ["user", "repo"]`), `.claude-plugin/plugin.json`, and a `README.md` describing the three pillars, install snippet, and what is NOT in this pack (growth strategy, primary research production, per-surface content design).
- [x] The pack is **registered in `.claude-plugin/marketplace.json`** (name `product-strategy`, with description, version, and category `product-management`), inserted in alphabetical order.
- [x] **`packs/product-strategy/pack.toml`** includes a `[pack.layout.repo]` table with `parent = "docs/product/shaping"` following the `product-engineering` and `experience-design` precedent. No central `agentbundle-layout.toml` is edited — that file is adopter-owned and never shipped with the catalogue (RFC-0040 / ADR-0030).
- [x] **9 SKILL.md files** ship, one per skill slug, at their conventional paths (`packs/product-strategy/.apm/skills/<slug>/SKILL.md`), each: `<100` lines; valid frontmatter with `name:` and `description:`; `## Procedure` with ≥5 numbered steps; `lint-skill-spec.py` exits 0. Skill slugs (D5/D6/D7): `run-swot`, `run-porters-five-forces`, `run-pestle-analysis`, `run-bcg-matrix`, `run-okr-cascade`, `write-prfaq`, `synthesize-stakeholder-research`, `define-ux-strategy`, `define-content-strategy`.
- [x] Each skill ships a **`references/agentbundle-layout.md`** documenting the `docs/product/shaping/<artifact-name>.md` default artifact path and the three-tier resolution contract (config → default → discover-by-marker).
- [x] Each skill ships **eval files** at `evals/eval_queries.json` (activation trigger phrases) and `evals/evals.json` (Tier-4 LLM-judge rubric per RFC-0037); each skill slug is listed in `[pack.evals] skills` in `pack.toml`.
- [x] **`run-okr-cascade`** names and implements the cross-pack routing contract (RFC-0063 §Cross-pack routing contract): commits `okr-cascade.md` to `docs/product/shaping/`; appends gap entries as `{slug = "<gap-slug>", type = "strategy"}` (no `needs` field — no-dependency entries omit it; RFC-0063's literal `needs = "nothing"` is a malformed value superseded by this spec) to the appropriate initiative's `["ini-NNN".shaping_queue].backlog` in `workspace.toml` — the per-initiative nested form is required (not a top-level `[shaping_queue]` table); "active" means `status = "active"` in the `["ini-NNN"]` section header; resolves the single active section automatically; if multiple are active, elicits from the user; emits `"frame-situation not found — install PE pack to route OKR gaps into the shaping sequence"` when `frame-situation` is absent; documents the full contract in `references/cross-pack-routing.md`. Verification: `grep -r "shaping_queue" packs/product-strategy/.apm/skills/run-okr-cascade/` returns a hit; manual QA confirms the entry targets `["ini-NNN".shaping_queue].backlog` (not a top-level table). Note: `frame-situation` is an M2 deliverable and does not exist yet; only the absent-diagnostic branch can be exercised at M4 ship time.
- [x] **`check-workspace` lines 65 and 98 are updated** to fix the routing for `type = "strategy"` entries. Both lines currently route strategy-type to running a product-strategy pack skill; after OKR cascade ships, `{type = "strategy"}` entries are OKR gaps ready for PE framing (not items that still need strategy work). Both lines are updated to route through `frame-situation` (PE pack — M2); if not yet available, run `frame-intent` as interim — matching the existing `shape`-type progressive-disclosure pattern. The exact on-disk text replaced: line 65 cell `run product-strategy pack skill (requires product-strategy pack)` and line 98 cell `product-strategy pack skill (requires product-strategy pack — M4)`. Zero existing `type = "strategy"` entries in `workspace.toml` are affected — the type was defined in anticipation of M4.
- [x] **`synthesize-stakeholder-research`** surfaces `"run desk-research project first — no research inputs found"` when no desk-research outputs are found; documents the input boundary (consumes desk-research outputs; does not produce primary research) in SKILL.md.
- [x] **`define-ux-strategy`** references the NN/g three-layer model, Jaime Levy four-tenets framework, and Gothelf/Seiden OKR-linked UX framing by name (not verbatim text); documents the upstream-of-`journey-mapping` position; commits `ux-strategy.md`.
- [x] **`define-content-strategy`** references the Halvorson content strategy quad (Purpose + Process + Structure + Governance) by name (not verbatim text); documents the organizational/governance-layer vs. per-surface execution distinction (Pillar 3 ≠ content-design); commits `content-strategy.md`.
- [x] **ADR-0053** exists at `docs/adr/0053-product-strategy-pack-scope-and-discipline-boundaries.md` with status `Accepted`; body records decisions D1–D10, the cross-pack routing contract design rationale, and the growth-strategy/experience-mapping deferral reasoning.
- [x] **`docs/backlog.md`** is updated: the `content-strategy-and-marketing-copy-lens` entry's content-strategy thread is marked resolved (shipped in RFC-0063); a new `growth-strategy-pack` open entry is added; a new `experience-mapping-extension` open entry (to extend experience-design) is added.
- [x] **RFC-0062** is verified: confirm both references in RFC-0062 already read `product-strategy pack` (not `product-strategist pack`); no edit is needed (the file was already updated prior to this spec). Record the verification in the PR as a note, not a diff.
- [x] **`docs/product/journeys/product-strategist-sets-direction.md`** is verified (no status change needed — it is already `planned`): the Prerequisites table, 9-skill list, staging steps, and cross-pack routing contract detail match the final shipped skills. Record any discrepancy found during verification as a correction in the implementing PR.
- [x] **`docs/specs/README.md`** is updated to include `product-strategy-pack` in the active spec list (index hygiene).
- [x] **Cross-reference notes** are added to `packs/product-engineering/README.md` and `packs/experience-design/README.md` naming the `product-strategy` pack as the upstream provider and summarizing the cross-pack routing contract and feed relationships.
- [x] **`docs/product/changelog.md`** carries an `[Unreleased]` entry recording the new `product-strategy` pack.
- [x] `make lint-packs`, `make validate`, `make build`, `tools/lint-skill-spec.py`, and the package `pytest` suite are **green**; every shipped `SKILL.md` is `<100` lines; no `hooks/`, `agents/`, or `*.py` validator exists in the pack tree (grep-verified); no seed directory exists under `packs/product-strategy/` (Rail A; user-scope).

## Assumptions

- **Technical:** Pack shape mirrors `packs/experience-design/` and `packs/product-engineering/`: `pack.toml` + `.claude-plugin/plugin.json` + `.apm/skills/<slug>/` + `README.md`; no `seeds/` (RFC-0004 Rail A, user-scope default). (source: packs/experience-design/ + packs/product-engineering/ tree inspection 2026-07-19)
- **Technical:** Adapter-contract version follows `experience-design` at `0.12` (pure-markdown SKILL.md surface; no adapter-specific primitives). (source: packs/experience-design/pack.toml, 2026-07-19)
- **Technical:** Evals shape mirrors `packs/experience-design/.apm/skills/<skill>/evals/` — `eval_queries.json` (activation trigger phrases) + `evals.json` (Tier-4 LLM-judge rubric). (source: RFC-0037, ADR-0028; pack inspection 2026-07-19)
- **Technical:** `agentbundle-layout.toml` is adopter-owned and never shipped with the catalogue (RFC-0040 / ADR-0030). The pack declares its default artifact parent via `[pack.layout.repo] parent = "docs/product/shaping"` in `pack.toml`, and ships per-skill `references/agentbundle-layout.md` documenting the adopter-owned `[product-strategy]` section. (source: packs/product-engineering/pack.toml §pack.layout.repo; RFC-0040; ADR-0030)
- **Technical:** `docs/adr/0053-*.md` is the next available ADR number (last filed: `0052-nine-experience-pack-skill-renames.md`). Verify at ADR time that no concurrent PR has claimed 0053. (source: docs/adr/ listing 2026-07-19)
- **Technical:** `tools/lint-skill-spec.py` validates frontmatter `name:`, `description:`, and `## Procedure` step count for all SKILL.md files under `packs/`; the new pack will be picked up automatically by the glob. (source: packs/product-engineering spec inspection; tools/lint-skill-spec.py behavior)
- **Process:** RFC-0063 D1–D10 are all Accepted (2026-07-19); OQ1 (growth) and OQ2 (experience mapping) are resolved as deferred. The spec does not re-litigate these decisions. (source: docs/rfc/0063-product-strategy-pack.md)
- **Process:** The implementing PR(s) will run `make build-self` only if this pack's projection is included in the build-self scope. User-scope packs that are not projected into this repo's working tree skip `build-self`; the gate is `lint-packs + validate + build + pytest` (per `project_self_host_pack_scope` memory). (source: memory reference_self_host_projected_readme_allowlist.md)
- **Product:** The `workspace.toml` `[shaping_queue]` format is nested per-initiative: `["ini-NNN".shaping_queue].backlog`. The `run-okr-cascade` skill must resolve which initiative to append under — the implementation resolves the single active initiative automatically, and elicits from the user when multiple are active. The skill does not mandate workspace.toml's presence — graceful absence is the fallback. (source: workspace.toml inspection 2026-07-19; RFC-0063 §Cross-pack routing contract)
- **Design:** The `check-workspace` `type = "strategy"` routing fix (line 98) is **decided** — update to route strategy-type entries to `frame-situation` (M2) / `frame-intent` (interim), matching the `shape`-type progressive-disclosure pattern. Zero existing `type = "strategy"` entries in `workspace.toml` are affected. T6 adds `packs/core/.apm/skills/check-workspace/SKILL.md` to its Touches. (source: packs/core/.apm/skills/check-workspace/SKILL.md:98; owner direction 2026-07-19)
