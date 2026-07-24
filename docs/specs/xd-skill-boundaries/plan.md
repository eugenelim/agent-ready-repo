# Plan: xd-skill-boundaries

**Spec:** docs/specs/xd-skill-boundaries/spec.md

## Tasks

### T1 — Add copy-direction near-miss guard to 17 SKILL.md descriptions
**Depends on:** none
**Mode:** goal-based
**Done when:** `grep -l "copy-direction" packs/experience-design/.apm/skills/*/SKILL.md` lists all 17 + content-design + tone-of-voice (19 total; copy-direction itself excluded from this grep).

**Skills receiving the new guard (17):**
- `design-system` — description ends with new guard
- `design-principles` — description ends with new guard
- `informational-design` — description ends with new guard
- `experience-status` — description ends with new guard
- `workspace-design` — description ends with new guard
- `service-blueprint` — description ends with new guard
- `conversion-design` — description ends with new guard
- `analytical-design` — description ends with new guard
- `design-review` — description ends with new guard
- `marketplace-design` — description ends with new guard
- `user-flow` — description ends with new guard
- `information-architecture` — description ends with new guard
- `creative-direction` — description ends with new guard
- `documentation-design` — description ends with new guard
- `journey-mapping` — description ends with new guard
- `process-mapping` — description ends with new guard
- `interaction-design` — description ends with new guard

**Standard guard phrase:**
`Do NOT use to name copy voice goals — use \`copy-direction\` for a specific surface or \`tone-of-voice\` for brand-level register.`

**Already verified (no change):**
- `content-design` — has its own copy-direction guard from M3a
- `tone-of-voice` — has its own copy-direction guard from M3a
- `copy-direction` — guards outward to tone-of-voice/content-design/voice-and-microcopy; no self-referential guard needed

Tests: no stub (goal-based)

---

### T2 — Bump pack.toml and plugin.json to 1.2.1
**Depends on:** none
**Mode:** goal-based
**Done when:** `grep '"1.2.1"' packs/experience-design/pack.toml` and `grep '"1.2.1"' packs/experience-design/.claude-plugin/plugin.json` both exit 0.

Approach: Update `version = "1.2.0"` → `"1.2.1"` in both files.

Tests: no stub (goal-based)

---

### T3 — Update workspace.toml: move spec/xd-skill-boundaries from queue to shipped
**Depends on:** T1, T2
**Mode:** goal-based
**Done when:** the string `"spec/xd-skill-boundaries"` does NOT appear in `["ini-003".work].queue` and DOES appear in `["ini-003".work].shipped`.

Approach: Remove `{path = "spec/xd-skill-boundaries", needs = [...]}` from queue; append `"spec/xd-skill-boundaries"` to shipped list (alongside the other shipped specs). Keep `needs = [...]` references on downstream entries intact.

Tests: no stub (goal-based)

---

### T4 — Run contract drift gate
**Depends on:** T1, T2
**Mode:** goal-based
**Done when:** `python3 tools/check-contract-drift.py --root .` exits 0.

Tests: no stub (goal-based)
