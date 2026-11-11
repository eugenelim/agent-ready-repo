# Agentbundle installation merges shared YAML policy files when a pack first needs one

- **Slug:** `agentbundle-install-artifact-layout`
- **Status:** Withdrawn
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [spec/engine-export-boundary Product boundary](../../specs/engine-export-boundary/spec.md); [spec/pack-script-root-boundary-validation deferred YAML merge](../../specs/pack-script-root-boundary-validation/spec.md)

## Disposition — withdrawn 2026-11-05, no consumer exists

No pack ships a mergeable YAML policy file, and none is planned: the only seeded YAML is single-owner (`packs/repo-governance/seeds/governance/manifest.example.yaml`), and `contracts/adapter.toml` still defines only `merge-json` and `user-merge-json`. Reopen with a new intent when a pack needs two owners for one YAML file. The marker half is already closed: `package-data` includes `_data/*`, so the wheel ships `install-marker.py`.

## Outcome

`agentbundle install` lets two packs ship the same YAML policy file, such as a shared `.snyk`, without one clobbering the other.

## Trigger

Unscheduled. The work starts when the first pack needs to ship a mergeable YAML policy file. Until then this intent records the need and its cost, and no slice, spec or brief is planned.

## Opportunity

`agentbundle install` has no YAML-merge mode, so two packs that each ship a YAML policy file such as `.snyk` would overwrite each other. The need is hypothetical: no adopter has hit it, and no pack ships or plans such a file.

## Context

- **Origin.** The [`pack-script-root-boundary-validation`](../../specs/pack-script-root-boundary-validation/spec.md) spec, in its section on why suppression is unavailable, names three suppression routes for a CWE-23 finding. `# nosec` reaches Bandit only. A Semgrep rule exclusion reaches this repository's gate only. A `.snyk` policy file would reach an adopter's Snyk, but no pack ships one and none can without a YAML-merge mode. The spec parked the merge mode as the backlog slug `agentbundle-install-yaml-merge` and chose source fixes as the remediation that reaches every adopter.
- **Why suppression does not reach adopters.** Each adopter organisation runs its own scanner with its own ignore store, so a suppression file in a pack helps only an adopter whose scanner reads that file.
- **Merge modes today.** The adapter contract defines `merge-json` and `user-merge-json` for hook wiring and similar files, and no YAML mode (`contracts/adapter.toml`).
- **No consumer.** The only YAML a pack seeds is a single-owner example, `packs/repo-governance/seeds/governance/manifest.example.yaml`. `.snyk` appears only in guidance text under `packs/catalogue-curation/`. No RFC, spec or roadmap item plans a YAML policy file that install must merge.
- **Cost.** The change touches protected `packages/agentbundle/**`, so its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC, and it needs a design for YAML conflict semantics. That trailer applies when the protected-tree change lands, not while this intent is a Draft.

## What this absorbs

### agentbundle-install-marker-importable-path (closed; no remaining work)

The original wheel concern was that `agentbundle/_data/install-marker.py` is not importable and `check-wheel-contents` reports W004. Neither half holds: the `package-data` table of `packages/agentbundle/pyproject.toml` includes `"_data/*"`, so the marker ships as package data, and no workflow, Makefile target or tool runs `check-wheel-contents`, so nothing reports W004. Reopen this only if a wheel check is added that fails on the marker.

### agentbundle-install-yaml-merge

The remaining work: add a YAML-merge conflict mode to `agentbundle install`. It starts at the trigger above.

## Assumptions

- No pack ships a YAML policy file today, so the YAML-merge need is a stated future conflict, not a present one.
- A source fix stays the preferred remediation for scanner findings, as the origin spec decided. A shared policy file would add to it and never replace it.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
