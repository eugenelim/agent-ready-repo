# AGENTS.local.md — `packages/` (insider context; not exported with catalogue init)

## Release Coupling

Changes to `packages/agentbundle/` that alter a public CLI verb, add or remove a subcommand, or change
an output format visible to callers require a version bump in `version.py` + `pyproject.toml` and a
PyPI release before downstream repos can consume them.

**What always requires a release:**
- Adding, removing, or renaming a `agentbundle catalogue <sub>` or `agentbundle pack <sub>` command.
- Changing required CLI flags or their semantics for any published command.
- Changing the output layout of `dist/` or archive/sidecar file names.
- Changing `catalogue.toml` or `pack.toml` schema in a way that invalidates existing valid files.

**What does not require a release:**
- Internal refactors that preserve observable CLI behaviour.
- Adding optional flags with backward-compatible defaults.
- Updating `docs/guides/` or `tools/` without touching the package.
- Adding tests or improving error messages without changing exit codes.

After bumping: tag `agentbundle-vX.Y.Z` and push to PyPI via the standard release process.

## Engine-Change-RFC requirement

Any changeset touching `packages/agentbundle/agentbundle/` (engine behaviour) or `packs/credential-brokers/**` must include the literal string `Engine-Change-RFC:` somewhere in its commit messages — without it, `tools/lint-catalogue-curation-guard.py --base origin/main` fails in CI. Whitespace-only passes are still subject to the gate; add the marker to the commit message even when the change carries no logic.
