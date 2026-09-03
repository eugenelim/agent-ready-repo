# Agentbundle installation supports importable markers and mergeable YAML policies

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/engine-export-boundary Product boundary](../../specs/engine-export-boundary/spec.md)
- **Authority:** [spec/pack-script-root-boundary-validation deferred YAML merge](../../specs/pack-script-root-boundary-validation/spec.md)

## Outcome

`agentbundle install` preserves compatible installation artifacts without pack conflicts.

## Opportunity

The install marker's historical importability concern requires an explicit packaging decision, and `agentbundle install` has no YAML-merge mode for policy files.

## What this absorbs

### agentbundle-install-marker-importable-path

The stated wheel concern was that `agentbundle/_data/install-marker.py` was non-importable and `check-wheel-contents` reported W004. Current code instead documents at `packages/agentbundle/agentbundle/build/main.py:236` that ``<package>/_data/install-marker.py`` works through `importlib.resources`, and `packages/agentbundle/pyproject.toml:40` includes `"_data/*"`, so the marker is shipped as package data and read through `importlib.resources`. Move it to an importable path or package it explicitly as data, if the remaining packaging contract requires it. The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC.

### agentbundle-install-yaml-merge

Add a YAML-merge conflict mode to `agentbundle install` so packs can ship mergeable `.snyk` and other YAML policy files without clobbering each other. `docs/specs/pack-script-root-boundary-validation/spec.md:50` records that `agentbundle install` has no YAML-merge mode. The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC.

## Assumptions

- The marker is currently shipped as package data and read with `importlib.resources`; the stated non-importable path and W004 condition need current wheel-check evidence to establish whether any gap remains.
- The `Engine-Change-RFC:` trailer applies when the protected-tree change lands, not when this Draft intent is authored.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
