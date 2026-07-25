# Release coupling — what requires an AgentBundle release

Not every change to the catalogue needs an AgentBundle release. This page explains the boundary.

## The boundary

AgentBundle ships as a Python package on PyPI. Its public surface — what adopters call — is the
`agentbundle catalogue *` command group and the `catalogue.toml` / `pack.toml` schema. Anything
that changes that surface is a release-boundary change. Anything that stays inside repo-local tooling
or does not alter observable CLI behaviour is not.

## Changes that require an AgentBundle release

| Change | Why |
|--------|-----|
| Adding a new `agentbundle catalogue <sub>` command | Adopters need to call it; it can't exist until released |
| Removing or renaming a `catalogue` sub-command | Callers break |
| Changing required CLI flags or flag semantics | Callers break |
| Changing the output layout of `dist/` or archive file names | Downstream tools expect a fixed layout |
| Changing `catalogue.toml` or `pack.toml` schema in a way that invalidates previously-valid files | Adopter catalogues fail validation |
| Adding a required field to either schema | Existing catalogues fail until updated |

## Changes that do not require a release

| Change | Why |
|--------|-----|
| Refactoring internal helpers that preserve observable CLI behaviour | Callers see no difference |
| Adding optional CLI flags with backward-compatible defaults | Callers not using the flag are unaffected |
| Updating `docs/guides/` or `tools/` without touching the package | No installed code changes |
| Improving error messages (without changing exit codes) | Observable behaviour is exit code + stdout schema |
| Adding or changing tests | Never reaches the installed surface |
| Updating Makefile targets that delegate to existing commands | Repo governance, not a public interface |

## The data-driven config preference

When possible, drive variation through `catalogue.toml` configuration rather than new CLI flags or
sub-commands. Data-driven config changes are cheaper: they don't require a release if the field is
optional and backward-compatible, and adopters can adjust without updating their tooling.

## Portable mechanics vs internal policy

The split between `packages/agentbundle/` and `tools/` is a design boundary:

- `packages/agentbundle/agentbundle/` — portable mechanics; installed in every adopter's environment; release-gated.
- `tools/` — repo-internal policy; runs only in this checkout; no release required.

When a new capability is purely repo-governance (a new lint check, a new gate), put it in `tools/`.
When it is something every catalogue author needs in their own CI pipeline, put it in `packages/agentbundle/` — and plan a release.
