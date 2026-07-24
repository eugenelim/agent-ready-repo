# Spec: xd-design-system-foundations

- **Status:** Approved
- **Owner:** eugenelim
- **Mode:** full (risk triggers: structural change — new public skill; public-interface change — design-system trigger/description rewrite; rename of live skill surface)
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0071 (D3a new skill, D3b alias-free rename, D9 per-spec minor bump), ADR-0038 (alias-free rename precedent), RFC-0047 § Errata (contract-acquisition skill-level rename precedent)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed (skill authoring + pack manifest + guides + site content)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The experience-design pack ships a `design-system` skill that produces a token/scale taxonomy (method only; explicitly refuses to produce values). No skill in the pack bridges "here is our token taxonomy" to "set up the working token foundation for this project" — a phantom handoff that leaves adopters at the boundary between taxonomy derivation and implementation. The `design-system` skill's trigger phrase "set up design tokens" also clashes with the incoming foundation skill, and the skill misdescribes DTCG as "the W3C Design Tokens interchange shape" (DTCG is a W3C Community Group specification, not a W3C Recommendation).

This spec closes the phantom handoff, eliminates the trigger collision, and corrects the DTCG description. It delivers:

1. The `design-system` skill renamed to `design-token-taxonomy` — alias-free per ADR-0038/RFC-0047 § Errata precedent, with updated trigger phrases, a near-miss guard routing "set up / implement design tokens" to `design-system-foundations`, and a corrected DTCG description. A grep-verified sweep of skill-name references (SKILL.md files, references/, quality-floor.md, manifests, pack page, journey page) confirms no stale references to the old skill name remain in structural positions.
2. A new `design-system-foundations` skill that takes the token taxonomy as input and sets up the working token foundation — lightweight mode (semantic colors, typography, spacing, radius, focus, key statuses, responsive breakpoints, core component tokens) and full mode (DTCG 2025.10-compatible token source, light/dark themes, semantic aliases, full component anatomy).
3. An updated FE genre-routing section in the frontend-engineering skill referencing `design-system-foundations` by name.
4. Updated experience-design pack page (`web/src/content/packs/experience-design.md`) and design journey page (`web/src/content/journeys/experience-design.md`) showing the two-step chain (derive taxonomy → apply foundations) and a new how-to guide (lightweight vs. full mode).
5. Pack version bumped `1.2.1 → 1.3.0` (minor — new skill; rename is structural per RFC-0071 D9).

**Done when:** phantom handoff eliminated; `design-token-taxonomy` and `design-system-foundations` have non-overlapping activation triggers verified by a recorded manual disjointness check; the phrase "W3C Design Tokens interchange shape" is absent from all files in `packs/experience-design/`; pack page + journey + how-to guide updated; `workspace.toml` moves `spec/xd-design-system-foundations` from queue to shipped.

## Boundaries

### Always do

- Rename `design-system` → `design-token-taxonomy` alias-free (live surface renamed; no install-time alias; ADR-0038/RFC-0047 § Errata precedent).
- Sweep all bare `design-system` **skill-name references** in structural positions across `packs/experience-design/`: SKILL.md description fields and body routing mentions, `references/*.md` files, `quality-floor.md` authoring-skills list, `pack.toml` description and evals list, `.claude-plugin/plugin.json` description, `README.md`, pack page, journey page. Scope excludes `evals/eval_queries.json` `query` text (which may legitimately contain old skill names as natural-language queries). Verification: `grep -rn "\bdesign-system\b" packs/experience-design/ --include="*.md" --include="*.toml" | grep -v "design-system-foundations" | grep -v "design-systems" | grep -v "design-system-chain" | grep -v "design-token-taxonomy" | grep -v "AGENTS.md"` returns no matches.
- Also sweep the phrase "W3C Design Tokens interchange shape" from all files in `packs/experience-design/`. Verification: `grep -rl "W3C Design Tokens interchange" packs/experience-design/` returns nothing.
- Update `plugin.json` version to match `pack.toml` version in the same commit (CI gate `test_pack_toml_version_matches_plugin_json`).
- Run `python3 tools/check-contract-drift.py --root .` after any change touching ownership fields; verify exit 0.
- Regenerate marketplace.json via `build-self` after the version bump.
- Ensure the union of `design-token-taxonomy` + `design-system-foundations` eval positives covers all 10 old `design-system` positives (retain-or-move, never drop).

### Ask first

- Any change to `design-system-foundations` full-mode scope beyond the RFC-0071 D3a brief (lightweight + full mode outputs as specified).
- Adding `design-system-foundations` to the `pack.first-value` starter-task contract (requires a new first-value entry — human review before adding).
- Extending the FE genre routing table to add new surface types not listed in the current table.

### Never do

- Add an install-time alias mapping `design-system` to `design-token-taxonomy` (ADR-0038 alias-free ruling).
- Add generated platform outputs (Figma variables, iOS Swift UI tokens, Android Material tokens) to `design-system-foundations` full mode in this PR — deferred to follow-on per RFC-0071 OQ1 / Follow-on work.
- Touch any files outside `packs/experience-design/`, `.claude/skills/frontend-engineering/SKILL.md`, `.agents/skills/frontend-engineering/SKILL.md`, `docs/guides/experience-design/`, `web/src/content/packs/experience-design.md`, `web/src/content/journeys/experience-design.md`, `docs/specs/xd-design-system-foundations/`, `docs/specs/README.md`, `docs/product/roadmap.md`, `workspace.toml`, and `.claude-plugin/marketplace.json` (build-self aggregate).
- Add a new top-level dependency or new abstraction layer.
- Change the `design-token-taxonomy` skill's method content (atomic composition, token naming by role, ratio-as-concept) — this rename is a trigger/description update, not a methodology rewrite.
- Move the skill to a different pack.

## Testing Strategy

All ACs use goal-based verification — file existence, JSON validity, grep checks, tool exit codes — except AC2 (disjointness), which is a recorded manual QA check (phrase sets are enumerated and asserted disjoint by inspection, then recorded in plan.md).

| AC | Mode | Mechanism |
|----|------|-----------|
| AC1: skill rename complete | goal-based | `ls design-token-taxonomy/SKILL.md` exits 0; `design-system/` directory absent |
| AC2: trigger non-overlap | manual QA | Both skills' trigger phrases (from description: field, split on `/` and `→`) are enumerated in plan.md and confirmed disjoint; this record is the audit trail |
| AC3: DTCG misdescription absent (pack-wide) | goal-based | `grep -rl "W3C Design Tokens interchange" packs/experience-design/` returns nothing |
| AC4: new skill exists | goal-based | `ls design-system-foundations/SKILL.md` exits 0; `name: design-system-foundations` present |
| AC5: mode content present (8 lightweight + 4 full-mode elements) | goal-based | grep each required term in SKILL.md by specific, unambiguous token |
| AC6: evals valid JSON | goal-based | `python3 -c "import json; json.load(open(path))"` exits 0 for all 4 evals files |
| AC7: query count | goal-based | ≥5 positive, ≥5 negative in `design-system-foundations/evals/eval_queries.json` |
| AC8: evals list updated | goal-based | `pack.toml [pack.evals].skills` has `design-token-taxonomy` + `design-system-foundations`; `design-system` absent |
| AC9: version bump + description fields | goal-based | `1.3.0` in pack.toml + plugin.json version; `\bdesign-system\b(?!-foundations|-token|-chain)` absent from both description fields |
| AC10: skill-name sweep (structural files) | goal-based | grep scoped to `.md` + `.toml` files, excluding `evals/eval_queries.json` query text; pattern `\bdesign-system\b` excluding `-foundations`, `-systems`, `-chain`, `-token` |
| AC11: contract drift | goal-based | `python3 tools/check-contract-drift.py --root .` exits 0 |
| AC12: FE genre routing updated | goal-based | grep `design-system-foundations` in both FE SKILL.md files |
| AC13: how-to guide content | goal-based | guide exists; grep: two-step chain, lightweight, full mode, design-token-taxonomy, design-system-foundations |
| AC14: pack page updated | goal-based | new skill names present; `\bdesign-system\b(?!-foundations|-token|-chain)` absent from file |
| AC15: journey page updated | goal-based | new entries present; `\bdesign-system\b(?!-foundations|-token|-chain)` absent from file |
| AC16: workspace.toml shipped | goal-based | `tomllib.load()` exits 0; `xd-design-system-foundations` in shipped; absent from queue |
| AC17: marketplace regenerated | goal-based | build-self `--dry-run` shows no drift |
| AC18: roadmap updated | goal-based | grep `xd-design-system-foundations` in `docs/product/roadmap.md` |
| AC19: specs/README updated | goal-based | grep `xd-design-system-foundations` in `docs/specs/README.md` |
| AC20: retain-or-move positives | goal-based | each of the 10 old query strings has `should_trigger: true` in `design-token-taxonomy` OR `design-system-foundations` eval_queries.json |

## Acceptance Criteria

- [ ] AC1: `packs/experience-design/.apm/skills/design-token-taxonomy/SKILL.md` exists; `packs/experience-design/.apm/skills/design-system/` directory is absent (alias-free rename complete).
- [ ] AC2: Both skills' trigger phrases (extracted from each `description:` field and split on `/`, `→`, `Do NOT` delimiters) are recorded in plan.md and confirmed disjoint. The phrase "set up design tokens" does not appear in `design-token-taxonomy` description.
- [ ] AC3: `grep -rl "W3C Design Tokens interchange" packs/experience-design/` returns nothing. DTCG is described as "the Design Tokens Community Group (DTCG) specification" (W3C Community Group) in `design-token-taxonomy/SKILL.md` and `references/token-taxonomy-derivation.md`.
- [ ] AC4: `packs/experience-design/.apm/skills/design-system-foundations/SKILL.md` exists with `name: design-system-foundations` in frontmatter. Trigger description does not use "derive a token taxonomy", "name our tokens by semantic role", or "derive our spacing and type scale".
- [ ] AC5: `design-system-foundations` SKILL.md lightweight mode covers all 8 elements: semantic color roles, typography (font family + scale + weight), spacing scale, radius system, focus styles, key statuses (success/warning/error/info), responsive breakpoints, core component tokens (button, input, card, modal base). Full mode additionally covers: DTCG 2025.10-compatible token source (with "where practical" posture), light/dark theme switching (verified by grep for "light/dark" or "light theme" or "light and dark"), semantic alias layer (primitive → semantic → component), full component anatomy. Generated platform outputs are explicitly noted as deferred to follow-on.
- [ ] AC6: `design-system-foundations/evals/eval_queries.json` and `design-system-foundations/evals/evals.json` exist and are valid JSON. `design-token-taxonomy/evals/eval_queries.json` and `design-token-taxonomy/evals/evals.json` are valid JSON.
- [ ] AC7: `design-system-foundations/evals/eval_queries.json` has ≥5 `should_trigger: true` queries and ≥5 `should_trigger: false` queries (including near-miss negatives routing to `design-token-taxonomy`).
- [ ] AC8: `pack.toml [pack.evals].skills` list contains `design-token-taxonomy` and `design-system-foundations`; `design-system` is absent.
- [ ] AC9: `pack.toml` version is `1.3.0`; `plugin.json` version is `1.3.0`; the pattern `\bdesign-system\b(?!-foundations|-token|-chain)` matches nothing in either `pack.toml` or `plugin.json` description fields; "W3C Design Tokens interchange" is absent from both files.
- [ ] AC10: `grep -rn "\bdesign-system\b" packs/experience-design/ --include="*.md" --include="*.toml" | grep -v "design-system-foundations" | grep -v "design-systems" | grep -v "design-system-chain" | grep -v "design-token-taxonomy" | grep -v "AGENTS.md"` returns no matches. (Scope: structural files only — SKILL.md, references, quality-floor.md, manifests, README, pack/journey pages. Excludes `evals/eval_queries.json` query text by including only `.md`/`.toml` extensions.)
- [ ] AC11: `python3 tools/check-contract-drift.py --root .` exits 0.
- [ ] AC12: `.claude/skills/frontend-engineering/SKILL.md` genre routing section references `design-system-foundations` by name; `.agents/skills/frontend-engineering/SKILL.md` carries the same update.
- [ ] AC13: `docs/guides/experience-design/how-to/design-system-chain.md` exists and covers: (a) the two-step chain (derive taxonomy → apply foundations), (b) when to use lightweight vs. full mode, (c) example lightweight token foundation output, (d) example full mode scope.
- [ ] AC14: `web/src/content/packs/experience-design.md` — `design-token-taxonomy` and `design-system-foundations` in skills list and prose; the pattern `\bdesign-system\b(?!-foundations|-token|-chain)` matches nothing in the file.
- [ ] AC15: `web/src/content/journeys/experience-design.md` — `design-token-taxonomy` entry present (name + description updated); `design-system-foundations` entry added; the pattern `\bdesign-system\b(?!-foundations|-token|-chain)` matches nothing in the file.
- [ ] AC16: `workspace.toml` — `spec/xd-design-system-foundations` moved from `["ini-003".work].queue` to `["ini-003".work].shipped` as bare string; `tomllib.load(open("workspace.toml","rb"))` exits 0.
- [ ] AC17: `.claude-plugin/marketplace.json` regenerated; build-self `--dry-run` shows no drift.
- [ ] AC18: `docs/product/roadmap.md` contains a shipped entry for `xd-design-system-foundations`.
- [ ] AC19: `docs/specs/README.md` Shipped section lists `xd-design-system-foundations`.
- [ ] AC20: All 10 positive trigger queries from the pre-rename `design-system/evals/eval_queries.json` (enumerated in plan.md) have `should_trigger: true` in either `design-token-taxonomy/evals/eval_queries.json` or `design-system-foundations/evals/eval_queries.json`. No old positive is silently dropped.

## Assumptions

- Technical: experience-design pack version is `1.2.1` (source: `packs/experience-design/pack.toml`)
- Technical: DTCG is a W3C Community Group specification, not a W3C Recommendation — current skill misdescribes it as "W3C Design Tokens interchange shape" including in `README.md:16` (source: `docs/rfc/0071-digital-experience-doctrine.md:305`; grep confirmed)
- Technical: `tools/check-contract-drift.py` exists at repo root (source: `ls` probe confirmed)
- Technical: frontend-engineering SKILL.md genre routing does not yet reference `design-system-foundations` (source: grep confirmed no match)
- Technical: ~16 sibling skills in `packs/experience-design/` reference `design-system` as a routing target and require sweep (source: adversarial-reviewer finding B1)
- Technical: `tools/run-pack-evals.py` is a probabilistic report-only LLM harness (not a deterministic gate); trigger non-overlap is verified by recorded manual disjointness check, not a live routing run (source: adversarial-reviewer finding B2)
- Technical: some `evals/eval_queries.json` query text legitimately contains the substring "design-system" (e.g., query #9 "Create the foundational design-system rules from our direction") — these are excluded from the structural sweep; AC10 scopes to `.md`/`.toml` files only (source: adversarial-reviewer finding B1 pass 3)
- Process: ADR-0038 alias-free rename policy and RFC-0047 § Errata (contract-acquisition skill-level precedent) apply to skill-level renames inside a pack
- Process: RFC-0071 D9 mandates minor bump for new skill: `1.2.1 → 1.3.0`
- Process: RFC-0071 D3a + D3b are Confirmed: new skill + rename
- Process: DTCG 2025.10 full-mode compatibility is "where practical"; generated platform outputs deferred to follow-on per RFC-0071 OQ1

## Temptations declined

- Tempted to add an install-time alias `design-system → design-token-taxonomy`; declining — ADR-0038 establishes alias-free as the house convention.
- Tempted to generate platform outputs (Figma variables, iOS tokens) in the full mode; declining — explicitly deferred in RFC-0071 Follow-on work.
- Tempted to restructure the `design-token-taxonomy` methodology; declining — this rename is a trigger/description update, not a methodology rewrite.
- Tempted to use `run-pack-evals.py` as the trigger non-overlap gate; declining — it is probabilistic and report-only; static disjointness check recorded in plan.md is the correct mechanism.
- Tempted to scope AC10 grep to all files recursively; declining — `evals/eval_queries.json` query text legitimately contains old skill names as natural language; scope to `.md`/`.toml` extensions only.
