---
id: self-host-sweep-respects-state
title: Self-host orphan sweep must not delete state-tracked skills
status: Implementing
type: bug-fix
---

- **Status:** Shipped

Mode: light (no risk trigger fired)

**Objective:** When `agentbundle catalogue self-host --write --force` runs on a repo that also has externally-installed skills (via `agentbundle install`), the orphan sweep in each build adapter must not delete skill directories that are recorded in `.agentbundle-state.toml`. Currently, `_sweep_skill_orphans` (claude_code, kiro) and the inline sweep (codex) build `expected_names` from only the self-host packs; any skill installed from an external catalogue is treated as an orphan and deleted.

## Acceptance criteria

- [x] After `project_packs` runs for any adapter, skill directories whose names are recorded as file paths in `.agentbundle-state.toml` under the skill target directory are not deleted.
- [x] Graceful degradation: if the state file is absent, has an unrecognised schema version, or is malformed TOML, the sweep proceeds as it did before this fix (no error; empty protection set).
- [x] All three adapters — claude_code, kiro, codex — apply the same protection.
- [x] A regression test covers the scenario: state file records an external skill → `project_packs` runs without that pack in its pack list → external skill directory survives.

**Assumptions:**
- Files touched: `build/adapters/claude_code.py`, `build/adapters/kiro.py`, `build/adapters/codex.py`, `tests/integration/test_self_host_sweep_respects_state.py`
- "Done" demonstrated by: regression test passes; skill dir present after `project_packs` call; existing sweep tests still pass
- NOT changing: `direct_directory.py:sweep_orphans` (the spec's "Never do" boundary bars expansion); install-time orphan path; state file schema; any public API

**Declined temptations:**
- Extending `direct_directory.py` with state awareness — "Never do" boundary in spec explicitly bars expansion of that module beyond `sweep_orphans`
- New shared helper module for the state-reading logic — structural change; established "mirror, keep in sync" pattern is already used here
- Filtering state rows by adapter before computing protected names — unnecessary; the target directory is already adapter-specific (`.claude/skills/` is never written by codex, `.agents/skills/` never by claude-code)
