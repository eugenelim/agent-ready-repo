# Catalogue Curation

> A repo-scope toolkit for catalogue operators — ingest primitives from external sources, compile pack-owned knowledge, survey repositories, and propose pack areas.

## Why this pack exists

A catalogue that cannot grow in a governed way becomes a closed system. Without structured intake tooling, adding an external skill means copying files manually with no audit trail, no review gate, and no way to trace where the primitive came from. With this pack, every ingestion produces a structured diff and a linked proposal that records the source, the rationale, and the decision — making the catalogue auditable.

## What it is

**Skills (4):** `assimilate-primitive` (bring a single external skill, subagent, or hook into the catalogue from a local path or URL, producing a reviewable RFC), `assimilate-repo` (survey a whole external repository for ingestion candidates and produce a prioritized RFC with a proposal for each), `propose-catalogue-pack` (justify and scaffold a new pack area, testing the proposal against the catalogue's charter principles and emitting an RFC), `compile-okf` (compile a pack's declared OKF knowledge into deterministic portable Skills, or check committed generated output for drift).

To create a new catalogue or a source-derived enterprise catalogue, use `agentbundle catalogue init` (plain or `--preset self-hosted`). Catalogue derivation is a CLI capability, not a skill.

No subagents. No seeds. No pack dependencies; `compile-okf` needs `pyyaml>=6.0`
when a maintainer runs the authoring compiler.

See the README for the complete manifest table.

## What it is not

- Not a package registry — it does not host packages, resolve versions, or manage transitive dependencies for production workloads.
- Not a CI/CD deployment tool — it manages the catalogue's own content, not application deployments.
- Not an open intake gate — every assimilation produces an RFC that a human must review and accept before the primitive is considered part of the catalogue.
- Not a catalogue-export tool — the old `export-catalogue` skill has been superseded by `agentbundle catalogue init --preset self-hosted`.

## How it relates to other packs

Does not require `core` or `governance-extras` as dependencies — each skill discovers and follows the catalogue's own portable contracts and governance when present. No other packs depend on catalogue-curation.
