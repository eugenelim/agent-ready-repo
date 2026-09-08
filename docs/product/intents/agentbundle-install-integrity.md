# Agentbundle installation preserves dependency, state, and pack integrity

- **Status:** Draft
- **Level:** feature

## Outcome

`agentbundle install`, uninstall, and upgrade preserve installed-pack integrity through dependency provenance, serialized state changes, and pre-render pack refusal.

## Opportunity

Required dependencies currently pass on installed name and version without catalogue identity, uninstall and upgrade can overwrite concurrent state updates, and install renders packs without first running `lint_pack`.

## What this absorbs

### pre-existing-install-dependency-source-provenance

Required dependencies are satisfied by installed name and version without proving catalogue source identity. `packages/agentbundle/agentbundle/commands/install.py:4487` builds `installed: dict[str, str] = {}`, a pack-name-to-installed-version map that is range-checked without retaining catalogue identity. Persist canonical catalogue identity, migrate state, and require identity together with name and range. The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC.

### multi-adapter-state-lock-uninstall-upgrade

Uninstall and upgrade bypass `persist_state_locked`, so concurrent state writers can lose an update. `packages/agentbundle/agentbundle/commands/uninstall.py:450` serializes previously loaded state with `serialised = dump_state(state)` after mutation; upgrade likewise serializes at `upgrade.py:598`. Use fresh-state mutate closures and add multi-process install/uninstall/upgrade coverage. The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC.

### untrusted-catalogue-symlink-exfiltration

Install no longer reads through source symlinks, so the exfiltration primitive is closed, but install still renders without first running `lint_pack`. `packages/agentbundle/agentbundle/commands/install.py:1185` reaches `repo_projection = render_pack(` without an install-path `lint_pack` gate. Gate install-path `render_pack` with `lint_pack` so malicious packs are refused rather than partially dropped. The install-path change is under protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC.

## Assumptions

- The `Engine-Change-RFC:` trailer applies when the protected-tree change lands, not when this Draft intent is authored.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
