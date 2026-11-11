# Agentbundle installation preserves dependency, state, and pack integrity

- **Slug:** `agentbundle-install-integrity`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Decomposed:** 2026-11-05 brief

## Outcome

`agentbundle install`, uninstall, and upgrade preserve installed-pack integrity through dependency provenance, serialized state changes, and pre-render pack refusal.

## Opportunity

Required dependencies currently pass on installed name and version without catalogue identity, uninstall and upgrade can overwrite concurrent state updates, and install renders packs without first running `lint_pack`.

## What this absorbs

### pre-existing-install-dependency-source-provenance

Required dependencies are satisfied by installed name and version without proving catalogue source identity. `validate_dependencies_required` in `packages/agentbundle/agentbundle/commands/install.py` builds `installed: dict[str, str] = {}`, a pack-name-to-installed-version map that is range-checked without retaining catalogue identity. Persist canonical catalogue identity, migrate state, and require identity together with name and range. The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC.

### pack-dependency-scope-qualifier

**Dropped 2026-11-05; not delivered by this intent** (see Non-goals). The description stays so a later intent can reopen it.

Dependency validation also unions repository and user installation state, so a repository-scoped dependency can satisfy a user-scoped consumer while remaining unreachable. Add a dependency scope qualifier to the pack contract and require the resolved dependency to be reachable from the consumer's installation scope. The schema and installer changes touch protected `packages/agentbundle/**`; their landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC.

### multi-adapter-state-lock-uninstall-upgrade

Uninstall and upgrade bypass `persist_state_locked`, so concurrent state writers can lose an update. `packages/agentbundle/agentbundle/commands/uninstall.py` serializes previously loaded state with `serialised = dump_state(state)` after mutation; `commands/upgrade.py` likewise serializes with `dump_state` in `_apply_single_row`. Use fresh-state mutate closures and add multi-process install/uninstall/upgrade coverage. The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC.

### untrusted-catalogue-symlink-exfiltration

Install no longer reads through source symlinks, so the exfiltration primitive is closed, but install still renders without first running `lint_pack`. `_run` in `packages/agentbundle/agentbundle/commands/install.py` reaches `repo_projection = render_pack(` without an install-path `lint_pack` gate. Gate install-path `render_pack` with `lint_pack` so malicious packs are refused rather than partially dropped. The install-path change is under protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC.

## Non-goals

- The dependency scope qualifier: dropped by the owner on 2026-11-05, reopened only when an adopter need is recorded.
- Any redesign of the state file format beyond adding catalogue identity.
- Any change to what uninstall or upgrade do, beyond serialising their state writes.

## Assumptions

- **Riskiest assumption:** old state files carry no catalogue identity, so the strict rule could refuse existing installs. It is tested agent-only by a migration fixture: a pre-migration state file still loads, and a dependency row with no identity is refused with a message telling the adopter to reinstall that pack.

- The `Engine-Change-RFC:` trailer applies when the protected-tree change lands, not when this Draft intent is authored.

## Readiness

- **Route:** delivery brief [`agentbundle-install-integrity-delivery`](../briefs/agentbundle-install-integrity-delivery.md), three slices. I1 (lint gate) and I2 (state lock) are each small enough for one `new-spec` or direct-light session; I3 follows I2 because both write state.
- **Verified 2026-11-05 in `packages/agentbundle/agentbundle`:** `persist_state_locked` is called only by `commands/install.py` and `direct_install.py`; `uninstall.py` and `upgrade.py` use `dump_state` directly; `install.py` has no `lint_pack` call; `validate_dependencies_required` keeps a name-to-version dict with no catalogue identity.
- **Authority answer:** the `Engine-Change-RFC:` gate checks only that the trailer is present; `n/a` is accepted for behaviour-neutral work. Each slice cites the RFC governing the command it changes. No umbrella RFC is needed.
- **First slice and agent-only proof:** I2, with a multi-process test that fails today by losing a row.
- **Owner decision, 2026-11-05:** a state row with no catalogue identity does not satisfy a catalogue-qualified dependency (strict), and the install stops, naming the dependency and telling the adopter to reinstall that pack, which writes the catalogue record.
- **Scope qualifier:** dropped by the owner on 2026-11-05; reopen when an adopter need is recorded.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
