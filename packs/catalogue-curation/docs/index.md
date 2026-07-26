# Catalogue Curation

> A repo-scope toolkit of four skills for catalogue operators — ingest primitives from external sources, survey repositories, propose pack areas, and export redistributable derivatives.

## Why this pack exists

A catalogue that cannot grow in a governed way becomes a closed system. Without structured intake tooling, adding an external skill means copying files manually with no audit trail, no review gate, and no way to trace where the primitive came from. With this pack, every ingestion produces a structured diff and a linked proposal that records the source, the rationale, and the decision — making the catalogue auditable and forkable.

## What it is

**Skills (4):** `assimilate-primitive` (bring a single external skill, subagent, or hook into the catalogue from a local path or URL, producing a reviewable RFC), `assimilate-repo` (survey a whole external repository for ingestion candidates and produce a prioritized RFC with a proposal for each), `propose-catalogue-pack` (justify and scaffold a new pack area, testing the proposal against the catalogue's charter principles and emitting an RFC), `export-catalogue` (produce a redistributable derivative of the catalogue in white-label mode — zero upstream trace — or attributed mode, with a fail-closed identity-leak check).

No subagents. No seeds.

See the README for the complete manifest table.

## What it is not

- Not a package registry — it does not host packages, resolve versions, or manage transitive dependencies for production workloads.
- Not a CI/CD deployment tool — it manages the catalogue's own content, not application deployments.
- Not an open intake gate — every assimilation produces an RFC that a human must review and accept before the primitive is considered part of the catalogue.

## How it relates to other packs

Requires `core` (the build loop that governs implementation of any work the intake process surfaces) and `governance-extras` (the RFC workflow that every assimilation and proposal runs through). No other packs depend on catalogue-curation.
