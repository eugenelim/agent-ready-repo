---
**Title:** frontend-engineering — delete core resident, add pack to self-host
**Status:** Shipped
**Mode:** full (structural/public-interface change trigger)
**Related:** ADR-0056 (`docs/adr/0056-frontend-engineering-pack-promotion.md`), ADR-0057 (new, amends ADR-0056's "not deleted" clause), `backlog:frontend-engineering-pack-split`
---

## Objective

Delete core's `frontend-engineering` skill and add the `frontend-engineering` pack to the self-host recipe. This eliminates the path conflict that the footprint gate enforces (which prevents the pack's skill from installing alongside core's at the same relpath), gives self-hosted repos the full 660-line pack skill instead of the 443-line resident, and removes the duplication entirely.

## Background

ADR-0056 promoted `frontend-engineering` to a first-class pack (660-line expanded skill) while explicitly keeping the core resident skill as a baseline for users without the pack. That decision created a latent conflict: both skills claim the same install path (`frontend-engineering`), so the footprint gate (`packages/agentbundle/agentbundle/config.py:229-286`) classifies any attempt to install the pack alongside core as `REFUSE` — the pack cannot coexist with core's resident skill. Pack users who hit this gate cannot get the pack's richer skill.

Deletion is the clean resolution: once core no longer owns the path, the footprint gate clears, and the pack's skill installs without conflict. The previously-committed projected copies (`.claude/skills/frontend-engineering/` and `.agents/skills/frontend-engineering/`) are removed via `git rm -r`; the `frontend-engineering` pack is not added to the self-host recipe — users who want FE craft guidance install the pack explicitly.

## Boundaries

**In scope:**
- `packs/core/.apm/skills/frontend-engineering/SKILL.md` — **deleted**
- `.claude/skills/frontend-engineering/` and `.agents/skills/frontend-engineering/` — previously-committed projected copies removed via `git rm -r`; the `frontend-engineering` pack is NOT added to the self-host recipe
- `packs/core/.apm/skills/work-loop/SKILL.md` — update the HTML/CSS/JS pre-EXECUTE gate row and footnote to name the pack requirement and provide a named-skip fallback
- `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md` — DXC template copy moved from the deleted core FE path to the pack
- `docs/adr/0057-frontend-engineering-core-skill-deletion.md` — new ADR amending ADR-0056
- `docs/adr/0056-frontend-engineering-pack-promotion.md` — status field amended (content unchanged)
- `workspace.toml [backlog].open` — `frontend-engineering-pack-split` entry removed (resolved)
- `docs/specs/digital-experience-contract/spec.md` and `plan.md` — anchor-path references updated from deleted core path to new FE pack path; projected-artifact AC annotated as superseded
- `web/src/content/journeys/core.md` and `web/src/content/packs/core.md` — `frontend-engineering` skill entry removed (drift prevention: core no longer ships the skill)
- `packs/frontend-engineering/README.md` — "Relation to resident skill" section updated to reflect sole ownership (ADR-0057)
- `guides/core/explanation/digital-experience-contract.md` — ownership map row updated from `core` to `frontend-engineering`; prose updated to reflect deleted resident

**Out of scope:**
- Pack's `frontend-engineering/SKILL.md` — unchanged; it is already the canonical content
- `spec/frontend-engineering-doctrine-update` (ini-003 queue) — now targets the pack's skill; update when the spec is authored (noted in PR)

## Assumptions

1. The pack's 660-line skill is a strict superset of the core resident; no craft guidance is lost.
2. Users who had core installed but not the pack will now see no `frontend-engineering` skill when doing FE work. This is the honest outcome — the craft rules are in the pack.
3. Removing the projected copies is safe: users who need FE craft guidance install the `frontend-engineering` pack explicitly; this repo does not need the pack projected into its working tree.
4. Removing the projected copies is safe: users who need FE craft guidance install the `frontend-engineering` pack explicitly; this repo does not need the pack projected into its working tree.

**Declined:** Tempted to write a thin stub for non-pack users. Declining — the footprint gate makes the stub's delegation instruction point at a non-existent path; an honest "absent" is better than a broken redirect.

## Acceptance Criteria

- [x] AC1: `packs/core/.apm/skills/frontend-engineering/SKILL.md` does not exist.
- [x] AC2: `git ls-files .claude/skills/frontend-engineering/ .agents/skills/frontend-engineering/` returns empty (projected copies removed from git tracking).
- [x] AC3: `packages/agentbundle/agentbundle/build/recipes/self-host.toml` `include` array does NOT contain `"frontend-engineering"` (pack is not self-hosted).
- [x] AC4: `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md` exists (DXC template copy migrated from the deleted core FE path to the pack).
- [x] AC5: `packs/core/.apm/skills/work-loop/SKILL.md` no longer says `Frontend pre-flight (mandatory)` for the HTML/CSS/JS row; it names the pack requirement and provides a named-skip fallback.
- [x] AC6: `git diff --exit-code -- packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` exits 0 (pack skill is unchanged).
- [x] AC7: `docs/adr/0057-frontend-engineering-core-skill-deletion.md` exists and explicitly amends ADR-0056's "not modified or deleted" clause.
- [x] AC8: ADR-0056's `Status:` line includes `Amended by ADR-0057`.
- [x] AC9: `workspace.toml [backlog].open` has no entry with `slug = "frontend-engineering-pack-split"`.

## Testing Strategy

**Verification mode: goal-based check** — the artifact is a file tree; correctness is verified by checking file presence, absence, and content markers.

**Done when:**
- `test -f packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 1 (file deleted)
- `git ls-files .claude/skills/frontend-engineering/ .agents/skills/frontend-engineering/` returns empty (projected copies removed)
- `grep '"frontend-engineering"' packages/agentbundle/agentbundle/build/recipes/self-host.toml` exits 1 (pack NOT in self-host)
- `test -f packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md` exits 0 (DXC copy in pack)
- `grep "frontend-engineering.*mandatory" packs/core/.apm/skills/work-loop/SKILL.md` exits 1
- `git diff --exit-code -- packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` exits 0
