# AGENTS.local.md — `packages/` (insider context; not exported with catalogue init)

**Read before modifying `packages/`:** version bump rule is in [`packages/AGENTS.md`](AGENTS.md#version-bump-rule); PyPI release coupling is below.

## Local installs go in a per-workspace venv, never global

`pip install -e packages/<pkg>` records one absolute path, so with several Conductor workspaces on
this repo the global interpreter resolves the package from whichever workspace installed it last —
not the one you are in. Local gates then exercise a different checkout, and when that workspace is
deleted the import fails outright.

Install into the workspace's own `.venv` (already gitignored) and drive every local gate through it:

```bash
.venv/bin/python -m pip install -e packages/agentbundle -e 'packages/credbroker[crypto]' ruff mypy pytest
.venv/bin/python -m pip install -r tools/requirements.txt
.venv/bin/python -c "import agentbundle, credbroker; print(agentbundle.__file__, credbroker.__file__)"  # must name this workspace
```

Keep the global interpreter on PyPI builds. `pip list` shows a path for editable installs, and
`site-packages/<pkg>-<ver>.dist-info/direct_url.json` carries `{"dir_info": {"editable": true}}`.

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

Every release-bearing change under `packages/` must update that package's `README-pypi.md`; do not tag while the checked-in PyPI description still describes the prior release.

The version-bump PR may mark its spec `Shipped` and plan `Done`; update `workspace.toml` after publication is confirmed.

## No internal-governance markers in source

Everything here is adopter-visible — the sdist ships source, and the repo is public. Do not add
`RFC-0NNN` / `ADR-0NNN` ordinals, our spec ACs, or `docs/specs/<our-slug>` paths to comments,
docstrings, argparse `help=` text, or runtime messages. State the rule instead of citing where it
was decided. Before committing:

```bash
grep -rnE '\b(RFC|ADR)-0[0-9]{3}\b|\bACs?\s*-?#?\s*[0-9]+[a-z]?(\([a-z]\))?\b|docs/(specs|rfc|adr|contracts)/[a-z0-9]' \
  packages/ --exclude='AGENTS*.md' --exclude='CHANGELOG.md'
```

Three traps:

- **IETF RFCs stay** (`RFC 9106` in `credbroker/_vault.py`). Ours are zero-padded four digits; IETF
  numbers never start with `0`.
- **Keep the AC pattern loose.** Two under-matches have each produced a false "clean" report.
  `\bAC-?[0-9]+\b` misses `AC6a` — the trailing `\b` cannot follow a digit with a letter after it.
  Adding `[a-z]?` fixes that but still misses the spaced and hashed forms `AC #7`, `AC 4`,
  `ACs 1-15`, which hid 31 sites in a single sweep. The pattern above matches all of them.
- **Runtime message text is pinned by tests.** A marker inside a user-facing string is often asserted
  on verbatim (`assertIn("…dist-tree files", stderr)`). Grep the test suite for the literal before
  editing it and change both together, or the rename lands red.

`credbroker/_sso.py` is byte-identical to `packs/credential-brokers/.apm/user-libs/credbroker/_sso.py`
— edit both or neither.

## Engine-Change-RFC requirement

Any changeset touching `packages/agentbundle/agentbundle/` (engine behaviour) or `packs/credential-brokers/**` must include the literal string `Engine-Change-RFC:` somewhere in its commit messages — without it, `tools/lint-catalogue-curation-guard.py --base origin/main` fails in CI. Whitespace-only passes are still subject to the gate; add the marker to the commit message even when the change carries no logic.
