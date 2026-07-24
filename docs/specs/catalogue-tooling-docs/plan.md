# Plan: Catalogue Tooling — Documentation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

## Approach

Three parallel streams: (A) update `packs/AGENTS.md` and `AGENTS.local.md`;
(B) write guide docs (catalogue.toml reference, external catalogue, migration,
Flow E, commands); (C) write Bucket 14 contract tests. Streams A and B can
proceed simultaneously. Stream C is last (tests the state after A+B complete).

## Constraints

- `packs/AGENTS.md` must stay ≤ 150 lines — use concise tables.
- Primitive directory list derives from `docs/contracts/adapter.toml`, not hardcoded.
- Release-coupling section goes ONLY in `AGENTS.local.md`.
- No aspirational docs — document only what the shipped commands actually do.
- Flow E must not claim local channel-descriptor resolution.
- Source docs edited; generated site copies regenerated via normal pipeline.

## Construction tests

- `test_agents_md_line_count`: `len(packs/AGENTS.md lines) <= 150`
- `test_agents_md_primitive_dirs`: extract primitive dirs from adapter.toml;
  for each, assert it appears in `packs/AGENTS.md`.
- `test_agents_md_schema_tables`: for each major pack.schema.json top-level key,
  assert it appears in `packs/AGENTS.md`.
- `test_agents_md_canonical_commands`: assert `agentbundle catalogue lint`,
  `agentbundle catalogue verify` appear; assert `tools/build_gate_chain.py`
  does NOT appear as primary workflow.
- `test_agents_local_has_release_coupling`: grep `AGENTS.local.md` for
  "release" + ("AgentBundle" or "catalogue"); assert present.
- `test_projected_agents_no_release_coupling`: grep `AGENTS.md` and
  `packs/core/seeds/AGENTS.md` for the AGENTS.local.md section heading;
  assert absent.
- `test_flow_e_no_local_descriptor_claim`: grep Flow E guide for
  "channel descriptor" + ("local" or "directory"); assert the text does NOT
  claim local-descriptor resolution as a supported flow.

## Design (LLD)

### packs/AGENTS.md restructure

Target structure (table-heavy for density):
```markdown
# Authoring packs

## Pack layout
| Path | Source? | Projected? | Ships? | Scope |
|------|---------|-----------|--------|-------|
| pack.toml | ✓ | — | ✓ | — |
| .claude-plugin/plugin.json | ✓ | — | ✓ | — |
| .apm/skills/<skill>/SKILL.md | ✓ | — | ✓ | — |
...

## pack.toml schema map
[pack] required: name, version, description, adapter-contract
[pack] optional: display-name, categories, keywords, maintainers, links, ...
...

## Primitive authoring rules
(concise bullets, not prose)

## Pack design model
intent → user journey → stage → capability → output

## Primary workflow (any catalogue)
agentbundle catalogue lint --root .
agentbundle catalogue verify --root .
agentbundle catalogue self-host --root . --write

## Home-repository additional gate
make build-check   # includes repo governance — not required for external catalogues
```

### Guide doc structure

```
docs/guides/reference/
  catalogue-toml.md          — all fields, valid values, examples
  catalogue-commands.md      — lint/verify/build/self-host/package/sync-defaults
  catalogue-migration.md     — old → new command table
  catalogue-archive.md       — archive format + verify

docs/guides/how-to/
  create-external-catalogue.md   — from zero to verifiable external catalogue
  enterprise-app-store.md        — Artifactory workflow
  flow-e-disconnected.md         — CORRECTED fully-disconnected host flow

docs/guides/explanation/
  release-coupling.md            — what requires an AgentBundle release
```

### Flow E corrected outline

1. On connected host: `agentbundle catalogue verify` + `agentbundle catalogue package`
2. Output layout: `dist/artifactory/catalogues/engineering/releases/.../`
3. Transfer: archive + `.sha256` sidecar (channel.json is audit context only)
4. On disconnected host: `agentbundle catalogue verify --archive ... --sha256-file ...`
5. Safe extraction to `/opt/company/agentbundle/catalogues/...`
6. Confirm `packs/` + `.claude-plugin/marketplace.json` present
7. `agentbundle config set source /opt/.../extracted-root`
8. `agentbundle list-packs`
9. Note: moving from Artifactory source to local path is a source change; follow
   source-migration or reinstall process
10. Explicit "NOT supported" note: local directory with only stable.json + archive
    is NOT the same as an extracted local catalogue

---

## Tasks

### T1: packs/AGENTS.md + AGENTS.local.md

**Verification mode:** TDD (contract tests written first, then edit docs to pass)

**Tests:**
Write all Bucket 14 contract tests FIRST in
`tests/unit/test_catalogue_tooling_docs.py`, then edit the docs to pass them.

**Approach:** Read current `packs/AGENTS.md`. Replace the primary workflow
section. Add pack layout table (derive primitive dirs from adapter.toml at test
time using `tomllib.loads(adapter_toml.read_text())`). Add schema map table.
Add design model section. Trim prose that only explains what the code already
names. Add "Release Coupling" section to `AGENTS.local.md`.

**Depends on:** all Wave 1-4 specs shipped (need final command names confirmed)

---

### T2: Guide docs

**Verification mode:** Goal-based check

**Tests:**
- `test_guide_files_exist`: glob for each expected guide file; assert present.
- `test_flow_e_no_local_descriptor_claim`
- `test_guide_commands_match_cli_parser`: for each example command in guide docs,
  check that `agentbundle <verb> --help` exits 0 (not 1).

**Approach:** Write each guide doc in docs/guides/ from scratch. Command examples
are taken directly from CLI `--help` output (not invented). Flow E follows the
exact tested steps from spec/catalogue-tooling-package-enhanced and verify.
Migration table maps every old command to its new canonical form.

**Depends on:** T1 (for correct command names), all Wave 1-4 shipped

---

### T3: Bucket 14 contract tests

**Verification mode:** TDD

**Tests:** All 8 `test_` functions listed in Construction tests above.

**Approach:** Write tests first (they'll fail until T1+T2 complete). Each test
is a pure file-content check — no subprocess, no imports from the docs themselves.
Tests use `REPO_ROOT` to find files. Add to `tests/unit/test_catalogue_tooling_docs.py`.

**Depends on:** T1 (so test failures are meaningful from the start)

## Changelog
