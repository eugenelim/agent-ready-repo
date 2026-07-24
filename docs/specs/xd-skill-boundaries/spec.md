# Spec: xd-skill-boundaries

**Status:** Shipped
**Mode:** full (risk triggers: structural/public-interface change — boundary guards across 20 skills; multi-feature — guards + version bump)
**Constrained by:** RFC-0071 (D9 version-bump rules, D10 intra-pack reference hygiene)

## Objective

Add explicit `copy-direction` near-miss guards to the 17 XD skills that lack them (now that copy-direction is shipped and the three-way copy boundary is settled). Bump the pack to `1.2.1` (PATCH — mechanical boundary updates per RFC-0071 D9). Regenerate the marketplace aggregate. Move `spec/xd-skill-boundaries` from queue to shipped in `workspace.toml`.

**Design-system rename is deferred to `spec/xd-design-system-foundations` (M3b) — do NOT touch the design-system skill directory or its skill name.**

## Boundaries

**In scope:**
- `copy-direction` near-miss guards added to the 17 skills that lack them (content-design and tone-of-voice are verified; copy-direction already guards outward to tone-of-voice/content-design/voice-and-microcopy — no self-referential guard needed)
- 2 near-miss routing eval queries added to `copy-direction/evals/eval_queries.json` to make guard effectiveness observable (surface → copy-direction routing, not just string presence)
- `pack.toml` and `plugin.json` version bump to `1.2.1`
- Marketplace aggregate regeneration (`build-self`) to keep marketplace.json in sync with the version bump
- `workspace.toml` — move spec from queue to shipped

**Out of scope:**
- Design-system rename (deferred to spec/xd-design-system-foundations / M3b)
- New design-system-foundations skill (M3b)
- Any reference to `design-system-foundations` (forward reference; not shipped)
- Any files outside `packs/experience-design/`, `docs/specs/xd-skill-boundaries/`, `workspace.toml`, and `.claude-plugin/marketplace.json` (build-self aggregate)
- voice-and-microcopy (lives in product-engineering pack, not in scope)

## Testing Strategy

| AC | Mode | Mechanism |
|----|------|-----------|
| copy-direction guards | goal-based | grep `copy-direction` in 17 SKILL.md description fields |
| content-design/tone-of-voice verified | goal-based | grep confirms existing guards intact |
| copy-direction guards outward | goal-based | grep confirms copy-direction description guards intact |
| Version bump | goal-based | grep `1.2.1` in pack.toml and plugin.json |
| Near-miss eval queries | goal-based | 2 new `should_trigger: true` queries in copy-direction evals |
| Contract drift | goal-based | `python3 tools/check-contract-drift.py --root .` exits 0 |
| workspace.toml | goal-based | xd-skill-boundaries absent from queue, present in shipped |
| design-system not renamed | goal-based | diff shows no directory rename or name: field change in `design-system/SKILL.md` |

## Assumptions

1. `copy-direction` skill is shipped (it is — merged in M3a / spec/xd-copy-direction).
2. `content-design` and `tone-of-voice` already have copy-direction guards from M3a — verify, do not change.
3. `copy-direction` description already guards outward (to tone-of-voice, content-design, voice-and-microcopy) — verify, no self-referential guard needed.
4. `design-system` is NOT renamed here — it stays as-is; rename is M3b.
5. PATCH bump is correct per RFC-0071 D9: mechanical boundary/trigger updates = patch.

## Temptations declined

- Tempted to rename design-system → design-token-taxonomy in passing — declining; that is M3b scope (spec/xd-design-system-foundations). Landing the rename without design-system-foundations creates a phantom-reference window that violates D10.
- Tempted to add a guard pointing to `design-system-foundations` — declining; the skill does not yet exist.
- Tempted to update web/ + site/ pack page — declining; pack-page update is in M3a's charter but requires a separate web/ commit; left as explicit deferral below.

## Deferred

- **experience-design pack page (web/ + site/)**: Charter calls for updating trigger language and near-miss guards on the pack page. Deferred to a follow-on PR — same PR would need web/ changes outside the `packs/experience-design/` scope gate. Backlog: `xd-pack-page-trigger-language-update`.
- **reference guide description sync** (`docs/guides/experience-design/reference/experience-design.md`): The guide's sync contract ("if a description changes, update this page in the same PR") applies here — 17 skill entries need the copy-direction guard added. Deferred because the guide already has pre-existing debt (copy-direction skill unlisted, M3a guards not present in tone-of-voice/content-design entries) that would entangle this PR if included. Fixing the guide is a clean follow-on. Backlog: `xd-reference-guide-description-sync`.

## Acceptance Criteria

- [x] **AC1** — All 17 XD SKILL.md descriptions that previously lacked a `copy-direction` guard now include a `Do NOT use to name copy voice goals — use \`copy-direction\` for a specific surface or \`tone-of-voice\` for brand-level register.` guard (or equivalent phrasing).
- [x] **AC2** — `content-design/SKILL.md` description still contains its copy-direction guard (unchanged from M3a).
- [x] **AC3** — `tone-of-voice/SKILL.md` description still contains its copy-direction guard (unchanged from M3a).
- [x] **AC4** — `copy-direction/SKILL.md` description still contains its outward guards to `tone-of-voice`, `content-design`, and `voice-and-microcopy` (unchanged).
- [x] **AC5** — `design-system` skill is not renamed and not moved (directory name and `name:` field in SKILL.md are still `design-system`; the description may have the standard copy-direction guard added like all other skills).
- [x] **AC6** — `pack.toml` version is `"1.2.1"`.
- [x] **AC7** — `plugin.json` version is `"1.2.1"`.
- [x] **AC8** — `copy-direction/evals/eval_queries.json` includes at least 2 `should_trigger: true` queries sourced from adjacent-skill contexts (analytics, onboarding journey) to verify cross-skill routing is observable.
- [x] **AC9** — `python3 tools/check-contract-drift.py --root .` exits 0.
- [x] **AC10** — `workspace.toml` has `spec/xd-skill-boundaries` in the shipped list (not queue).
- [x] **AC11** — No file outside `packs/experience-design/`, `docs/specs/xd-skill-boundaries/`, `workspace.toml`, and `.claude-plugin/marketplace.json` (the marketplace aggregate regenerated by `build-self`) is modified.
