# Spec: Catalogue Tooling — Documentation

- **Status:** Draft
- **Owner:** eugenelim
- **Initiative:** ini-005 AgentBundle Portable Catalogue Tooling
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ini-005 brief Buckets 10, 11; spec/catalogue-tooling-verify;
  spec/catalogue-tooling-rewire
- **Shape:** service

> **Spec contract:** this document defines what "done" means.

## Objective

After the engine and rewiring land, three guidance surfaces need to reflect the
new reality: (1) `packs/AGENTS.md` still references home-repository tools as the
primary workflow and lacks the full pack schema map and primitive layout; (2)
`AGENTS.local.md` has no section explaining release coupling implications for
catalogue engine changes; (3) `docs/guides/` lacks canonical documentation for
the new command surface, catalogue.toml, and the corrected Flow E.

This spec updates all three surfaces and adds the canonical guide docs for
external catalogue authors, the migration guide from old commands, and the
corrected Flow E for fully-disconnected hosts.

## Boundaries

### Always do

- Update `packs/AGENTS.md` to stay at or below 150 lines:
  - Replace home-repository command references with `agentbundle catalogue lint /
    verify / self-host` as the primary workflow.
  - Keep `make build-check` as the additional home-repository gate with a clear
    explanation that it's not required for external catalogues.
  - Add the full pack layout map (all directories from Bucket 10 §Pack Layout Map).
  - Add the full pack.toml schema map (all top-level tables from Bucket 10).
  - Add skill/primitive authoring guidance (from Bucket 10 §Skill and Primitive Authoring).
  - Add the concise pack design model (intent → journey → stage → capability).
  - Derive primitive directory list from adapter contract — do not hardcode.
- Add a "Release Coupling" section to `AGENTS.local.md` explaining the Bucket 10
  §AGENTS.local.md Release Awareness content: what requires an AgentBundle release
  vs what doesn't; data-driven config preferred; portable mechanics belong in
  agentbundle; internal policy under tools/.
- Do NOT add the release-coupling section to `AGENTS.md`, `packs/core/seeds/AGENTS.md`,
  or any projected primitive.
- Add or update `docs/guides/` pages for:
  - catalogue.toml reference (all fields, valid values, examples)
  - creating an external catalogue
  - catalogue lint (command reference)
  - catalogue verify (source + archive modes)
  - catalogue build and self-host
  - catalogue packaging
  - archive verification
  - migration from old commands (table: old → new)
  - enterprise app-store packaging
  - release-coupling boundary
  - Flow E (fully disconnected — CORRECTED per Bucket 11)
- Flow E must document exactly the tested flow: connected host packages →
  transfer archive+sidecar → disconnected host verifies → extracts → uses as
  local catalogue. Must NOT claim local channel-descriptor resolution unless
  implemented. Correct all output-name and output-path examples to match the
  real nested layout.
- Update source docs and regenerate site copies through the normal pipeline.
  Do not hand-edit generated copies.
- All existing tests pass.

### Ask first

- Removing any existing documentation page (only additive changes in this spec).
- Changing the 150-line limit for `packs/AGENTS.md`.

### Never do

- Place release-coupling guidance in `AGENTS.md`, `packs/core/seeds/AGENTS.md`,
  or any projected pack primitive.
- Hand-edit generated site copies (always source-edit, then regenerate).
- Claim commands or behaviors that don't exist yet (no aspirational docs).
- Make external catalogue authors dependent on `tools/` in the guide docs.

## Testing Strategy

- **TDD** for Bucket 14 documentation contract tests:
  - `packs/AGENTS.md` ≤ 150 lines
  - `packs/AGENTS.md` mentions all primitive source directories from adapter contract
  - `packs/AGENTS.md` schema map covers all major tables in pack.schema.json
  - `packs/AGENTS.md` uses canonical catalogue commands
  - `packs/AGENTS.md` does not reference tools/ as required for external authors
  - `AGENTS.local.md` contains the release-coupling boundary section
  - projected AGENTS.md and packs/core/seeds/AGENTS.md do NOT contain the
    release-coupling guidance
  - CLI help examples in docs correspond to real parser surfaces
  - Flow E does not claim local channel-descriptor resolution
- **Goal-based** for guide pages existence: `ls docs/guides/reference/catalogue-*`
  returns expected files.

## Acceptance Criteria

- [ ] AC1: `packs/AGENTS.md` is ≤ 150 lines.
- [ ] AC2: `packs/AGENTS.md` lists all primitive directories from the adapter
  contract (`docs/contracts/adapter.toml`) — no hardcoded list that can drift.
- [ ] AC3: `packs/AGENTS.md` contains a pack.toml schema map covering all major
  tables: `[pack]`, `[pack.adapter-contract]`, recipes, dependencies, conflicts,
  seeds, per-scope layout, first-value metadata, adaptation inference,
  substitutions, augmentation points.
- [ ] AC4: `packs/AGENTS.md` primary workflow references `agentbundle catalogue
  lint`, `agentbundle catalogue verify`, `agentbundle catalogue self-host --write`.
- [ ] AC5: `packs/AGENTS.md` contains the pack design model (intent → journey
  → stage → capability → output).
- [ ] AC6: `AGENTS.local.md` contains a section titled "Release Coupling"
  (or equivalent) explaining what does/doesn't require an AgentBundle release.
- [ ] AC7: `packs/core/seeds/AGENTS.md` and `AGENTS.md` do NOT contain the
  release-coupling section (test: grep both files for the section heading).
- [ ] AC8: A `docs/guides/` migration page exists documenting the old → new
  command mapping in a table.
- [ ] AC9: A Flow E guide exists and correctly states: (a) channel-descriptor
  resolution from a local directory is NOT supported; (b) transfer archive +
  sidecar only; (c) verify before extraction; (d) configure local catalogue path.
- [ ] AC10: CLI examples in guide docs use `agentbundle catalogue lint/verify/build/
  self-host/package` (not old `python -m agentbundle.build` forms, except in the
  migration table).
- [ ] AC11: The Bucket 14 contract tests pass (a new test file asserts all
  structural invariants programmatically).
- [ ] AC12: All existing tests pass.

## Assumptions

1. `packs/AGENTS.md` is currently 76 lines; additions must keep it under 150 lines
   total.

   Per-section line budget: the additions this spec makes (Release Coupling
   reference, adapter-contract derivation note) should together add no more than
   20 lines, keeping the total comfortably under 150.
2. `docs/guides/` uses the existing Diátaxis organization (tutorial/how-to/reference/
   explanation); new pages are how-to or reference pages.
3. The adapter contract at `docs/contracts/adapter.toml` lists primitive directories
   authoritatively; `packs/AGENTS.md` will reference the contract path rather than
   copy the list.
4. The site generation pipeline (`tools/build-site.py`) is not modified by this spec;
   only source docs are updated.
