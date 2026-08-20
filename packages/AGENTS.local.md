# AGENTS.local.md — `packages/`

Applies to `packages/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

## Local environment

`pytest packages/agentbundle/tests/` self-resolves through its conftest and pytest
rootdir. `pytest packages/credbroker` needs
`PYTHONPATH=packages/agentbundle:packages/credbroker`.

## Release Coupling

See [`docs/guides/explanation/release-coupling.md`](../docs/guides/explanation/release-coupling.md).
Release when a public CLI verb, required flag semantics, published output layout,
or a schema change invalidates previously valid files.

## Source markers

IETF RFC numbers never start with `0`; this catalogue's internal ordinals are
zero-padded. Runtime message text is often pinned by tests, so rename the message
and its assertion together.

## Engine-Change-RFC requirement

Changes under `packages/agentbundle/agentbundle/` or `packs/credential-brokers/**`
need an `Engine-Change-RFC:` commit footer; `tools/lint-catalogue-curation-guard.py`
enforces it in CI.
