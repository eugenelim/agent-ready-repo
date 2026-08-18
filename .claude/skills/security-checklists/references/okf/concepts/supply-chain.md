---
title: "supply-chain"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "repo-original"
boundaries:
  - filesystem_read_untrusted
---
# supply-chain

Use when dependencies, lockfiles, package manifests, build artifact fetches, or
build trust boundaries change.

## Spec-stage

Require a dependency decision that justifies why the component is needed and
why an existing maintained path is insufficient.

## Implementation checks

- `tool` Confirm SCA runs against the lockfile or pinned requirements.
- `reason` Check for typosquat and dependency-confusion risks.
- `reason` Require pins, lockfiles, and integrity where the ecosystem supports them.
- `reason` Judge maintenance, provenance, and unverified fetch steps.
- `reason` Note disproportionate transitive footprint.

## Established-helper bypass

Resolve the sanctioned dependency-addition path and flag raw third-party adds
outside it when a blessed mechanism or equivalent already exists.
