---
title: "Catalogue Authoring Scaffold"
status: Shipped
---

# Catalogue Authoring Scaffold

**Status:** Shipped
**Mode:** Full (multi-feature, structural change, new module boundary)

## Objective

Establish a complete, portable catalogue-authoring scaffold at the natural catalogue source locations (`packs/README.md`, `packs/_example/`, `profiles/README.md`, `profiles/AGENTS.md`, `profiles/_example/`). Add human-facing and agent-facing orientation. Create validated example pack and profile assets. Introduce a deterministic `_` reserved-path convention that excludes authoring assets from all discovery, installation, packaging, and marketplace surfaces. Project the portable scaffold into AgentBundle package data for a future `agentbundle catalogue init`. Make this repository dogfood the scaffold as normal source.

## Acceptance Criteria

- [x] AC1: `packs/README.md` exists and is portable — no host release workflow, no Make targets as requirements, no RFC/ADR references, no internal CI workflow references.
- [x] AC2: `packs/AGENTS.md` is portable (host-only content moved to `packs/AGENTS.local.md`), stays within the 150-line CI limit, and instructs agents to read `packs/AGENTS.local.md` when present.
- [x] AC3: Host-only pack guidance (Make targets, release workflow, SAST gates, changelog path, marketplace pipeline) lives in `packs/AGENTS.local.md`.
- [x] AC4: `packs/_example/` is complete: `README.md`, `pack.toml`, `.claude-plugin/plugin.json`, `.apm/skills/example-skill/SKILL.md`, `evals/eval_queries.json`.
- [x] AC5: After copying `packs/_example` → `packs/example-pack` (no other substitutions), `agentbundle catalogue verify --root .` passes on a test catalogue.
- [x] AC6: `profiles/README.md` exists and is portable.
- [x] AC7: `profiles/AGENTS.md` exists and covers the full current profile schema contract.
- [x] AC8: `profiles/_example/profile.toml` and `profiles/_example/README.md` exist; `profiles/_example` does not appear in `agentbundle list-profiles`.
- [x] AC9: Reserved `_` prefix assets excluded from all discovery: `list-packs`, `list-profiles`, `agentbundle catalogue build`, `lint`, `verify`, `self-host`, `package`, marketplace generation, `_project_seeds`, and the `_profile_load_packs` helper.
- [x] AC10: A blank authoring catalogue (0 installable packs, 0 profiles, `packs/_example/` + `profiles/_example/` present, empty marketplace) passes `agentbundle catalogue lint` and `agentbundle catalogue verify` without errors.
- [x] AC11: Scaffold projected deterministically into `packages/agentbundle/agentbundle/_data/catalogue-scaffold/` with a `manifest.json` containing SHA-256 per file and deterministic ordering.
- [x] AC12: `tools/catalogue/sync_authoring_scaffold.py --check` exits nonzero on drift without mutation; `--write` refreshes package data deterministically; two consecutive `--write` runs produce byte-identical output.
- [x] AC13: Internal `agentbundle.scaffold` module provides `load_manifest()`, `list_files()`, `read_file()`, `verify_hashes()`, and `materialize_to()` — stdlib only.
- [x] AC14: `pyproject.toml` package-data glob includes the scaffold; the built wheel and standalone artifact carry the scaffold files.
- [x] AC15: All new tests pass; all existing tests pass.
- [x] AC16: Docs generation is clean; `agentbundle catalogue lint --root .` on this repo passes.
- [x] AC17: Release-impact policy for scaffold changes documented in `AGENTS.local.md`.

## Boundaries

**In scope:** `packs/README.md`, `packs/AGENTS.md`, `packs/_example/` subtree, `profiles/README.md`, `profiles/AGENTS.md`, `profiles/_example/` subtree, `_data/catalogue-scaffold/` projection, `agentbundle.scaffold` module, `sync_authoring_scaffold.py`, discovery filter across all call sites.

**Out of scope:** `agentbundle catalogue init` command, CLI surface changes, new top-level directories, local-overlay (`AGENTS.local.md`) files (host-only, never in package data), CI workflow templates.

**Affected surfaces:** `build/main.py`, `commands/list_packs.py`, `catalogue_tooling/lint.py`, `catalogue_tooling/verify.py`, `catalogue_tooling/skill_spec_lint.py`, `catalogue_tooling/package.py`, `build/self_host.py`, `pyproject.toml`.

## Testing Strategy

- Integration: reserved-path exclusion across all discovery call sites
- Integration: copy `packs/_example` → `packs/example-pack`, run `lint` + `verify`
- Integration: copy `profiles/_example/profile.toml` → `profiles/example-profile.toml`, run `list-profiles`
- Integration: blank catalogue lint + verify + list-packs + list-profiles (expect 0, success)
- Integration: `--check` detects drift; `--write` restores; idempotency
- Integration: wheel contains scaffold; loader validates hashes
- Goal-based: `agentbundle catalogue lint --root .` on this repo → clean

## Assumptions

1. Profile `_example` is already invisible to `list_profiles` because it uses a subdir (`profiles/_example/profile.toml`) and the glob is `profiles/*.toml`.
2. `Engine-Change-RFC:` commit marker required for all changes under `packages/agentbundle/agentbundle/`.
3. The `packs/AGENTS.md` 150-line CI limit is enforced by `make build-check`; current file is at ~144 lines.
4. The example pack's `pack.toml` uses `adapter-contract` (v0.8+) which requires `[pack.install]`.
5. A blank catalogue still needs `packs/` dir and `.claude-plugin/marketplace.json` for lint to pass.

## Declined

- `agentbundle catalogue init` command — non-goal this phase.
- `--preset self-hosted` — non-goal.
- New `new-pack` / `new-profile` CLI commands — non-goal.
- CI workflow generators or templates — non-goal.
- Movement of central guides into pack directories — non-goal.
- Documentation-source binding system — non-goal.
