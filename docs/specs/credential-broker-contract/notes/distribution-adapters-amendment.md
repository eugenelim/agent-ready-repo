# Copy-paste source for AC45 (`distribution-adapters/spec.md` amendment)

Per `spec.md` AC45 (round-2-revised), a single Changelog bullet lands under the `## Changelog` heading at `docs/specs/distribution-adapters/spec.md:1344` — matching the per-bump pattern set by the existing v0.4 → v0.5 bullet at line 1347.

Substitute `YYYY-MM-DD` with the cleanup PR's merge date.

## Changelog entry (copy verbatim)

```
- YYYY-MM-DD: contract bumps v0.6 → v0.7 per `docs/specs/credential-broker-contract/spec.md` — header-comment update naming RFC-0013; `.agentbundle/` prefix non-regression pinned across the three user-scope adapters (claude-code, kiro, codex). Two new build-pipeline primitive classes registered: `shared-libs/` (many-to-many byte-identical projection into consumer skills' `scripts/` directories gated by `metadata.auth: creds`; drift gate per `credential-broker-contract` AC23; inter-pack basename collision is hard-error) and `adapter-root-bins/` (single-target projection to `$HOME/.agentbundle/bin/<basename>.py` at user scope, POSIX mode `0o755`; path-jail compliance per `credential-broker-contract` AC22). No conformance-suite addition to `distribution-adapters/spec.md` — per its own scope statement at `distribution-adapters/spec.md:1030` that "*full* per-adapter conformance suite is RFC-0003's work"; the two primitive classes are pinned by `credential-broker-contract`'s own ACs (AC20–AC23 for `shared-libs/`; AC22 for `adapter-root-bins/`).
```

## Why no separate conformance-suite section, version-table section, or per-section restructure

`distribution-adapters/spec.md` does not carry a "Adapter contract version table" section or a "Conformance suite" section as standalone surfaces. Version bumps are recorded as one-line Changelog bullets at `## Changelog`; the spec explicitly states (line 1030) it ships *unit-level* conformance and defers the *full* suite to RFC-0003. AC45 lands a Changelog bullet only; the round-2 review correctly caught the earlier shape's structural error.
