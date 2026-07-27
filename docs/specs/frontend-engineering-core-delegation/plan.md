---
**Spec:** `docs/specs/frontend-engineering-core-delegation/spec.md`
**Status:** Done
---

## Tasks

### Task 1 — Delete core's frontend-engineering skill

**Depends on:** none
**Verification mode:** goal-based check
**Done when:** `test -f packs/core/.apm/skills/frontend-engineering/SKILL.md` exits 1

**Approach:**
Delete `packs/core/.apm/skills/frontend-engineering/SKILL.md`. No replacement file; this is a clean deletion. The pack's version becomes the sole owner.

### Task 2 — Remove committed projected copies

**Depends on:** Task 1
**Verification mode:** goal-based check
**Done when:** `git ls-files .claude/skills/frontend-engineering/ .agents/skills/frontend-engineering/` returns empty

**Approach:**
Run `git rm -rf .claude/skills/frontend-engineering/ .agents/skills/frontend-engineering/` to remove the committed projected copies (SKILL.md and references/digital-experience-contract.md from each). The `frontend-engineering` pack is NOT added to the self-host recipe — users install the pack explicitly. Also move the DXC template copy from the deleted core path to `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`.

### Task 3 — Update work-loop FE pre-flight gate

**Depends on:** none
**Verification mode:** goal-based check
**Done when:** `grep "frontend-engineering.*mandatory" packs/core/.apm/skills/work-loop/SKILL.md` exits 1; file contains named-skip text for the FE pre-flight.

**Approach:**
In `packs/core/.apm/skills/work-loop/SKILL.md`:
1. Line 300: change `Frontend pre-flight (mandatory)` to `Frontend pre-flight (`frontend-engineering` pack required)`.
2. Footnote (line 304): extend to note the skill is in the pack, not core, and instruct a named skip when absent.
3. Lines 373-377: add conditional "if the pack is installed" language to the "Frontend-triggered work" paragraph.

### Task 4 — Verify projected copies are removed; update check_contract_drift.py

**Depends on:** Task 2
**Verification mode:** goal-based check
**Done when:** `git ls-files .claude/skills/frontend-engineering/ .agents/skills/frontend-engineering/` returns empty; `python tools/repo/check_contract_drift.py --root .` exits 0.

**Approach:**
Update `tools/repo/check_contract_drift.py` — rename `PACK_ANCHORS["core"]` to `PACK_ANCHORS["frontend-engineering"]` and point it at `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`. This ensures the drift check finds the moved DXC copy.

### Task 5 — Author ADR-0057 and amend ADR-0056 status

**Depends on:** none
**Verification mode:** goal-based check
**Done when:** `docs/adr/0057-frontend-engineering-core-skill-deletion.md` exists; `grep "Amended by ADR-0057" docs/adr/0056-frontend-engineering-pack-promotion.md` exits 0.

### Task 6 — Resolve workspace.toml backlog entry

**Depends on:** none
**Verification mode:** goal-based check
**Done when:** `grep 'frontend-engineering-pack-split' workspace.toml` exits 1.
