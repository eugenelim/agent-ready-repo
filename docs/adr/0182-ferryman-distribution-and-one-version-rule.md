# ADR-0182: Ferryman reaches users from PyPI or a clone, under one version and compatibility rule

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** packaging, install
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0115 (the proposal this records); ADR-0171 (repository copy of supervisors and detection; it points here for the version rule); ADR-0172 (the approval-fields contract); `packages/AGENTS.md` (a new package pairs `version.py` with `pyproject.toml` and ships package tests that read no repository path)

## Context

`ferryman` is a Python package that drives work and stays in use. The Claude plugin route serves packs and not packages, so it needs its own channel. A core upgrade can also strand it if the supervisor skill version is outside what it was tested with.

## Decision

We will publish `ferryman` to PyPI, support install from a clone, and apply one `major.minor` compatibility rule. This record decides the version rule, and page 02 of the architecture set holds the detail.

- **D1:** `ferryman` reaches users from PyPI into a virtual environment, as an isolated tool install, and from a clone. The clone serves offline and restricted networks. The plugin route serves packs, not packages.
- **D2:** The name is re-checked, with trademark, npm and PATH checks, before the first publish. Unverified: no reproducible PyPI lookup exists. A lookup of 2026-11-07 found no `ferryman` package, and a later fetch was blocked by a client challenge.
- **D3:** A descriptor is keyed by `major.minor` and lists the patch versions tested. `ferryman` accepts a patch inside a tested minor, refuses outside the declared range, and stops on an unknown version with `unknown-descriptor`. It never warns.
- **D4:** Descriptors are built in, one per skill version. No descriptor file ships beside the supervisor yet. Revisit after the supervisor's pinned file set is read.
- **D5:** The skill version is read from `packs/core/pack.toml` or the installed plugin manifest, and from the install-state row if that row carries one. The install-state source is unverified until the file is read.
- **D6:** A `fields_version` mismatch of `approval-fields.v1` between a `ferryman` release and a core release refuses. ADR-0172 owns the contract.

## Consequences

**Positive:**
- One rule decides every supervisor skill version check.
- The isolated install needs no shared Python, since `ferryman` imports no `agentbundle`.

**Negative:**
- Every supported core minor needs a descriptor in a `ferryman` release.
- The name is still unchecked for trademark, npm and PATH collisions.

**Revisit if:** the supervisor's pinned file set allows a descriptor beside the script, or the name check fails.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** a manual name and trademark check, with npm and PATH checks, before the first publish. A range test for patch accept, minor refuse and unknown stop, a drift test for `fields_version`, and install fixtures for the virtual environment and clone paths.
- **Owner:** eugenelim

## Alternatives considered

- **An exact-version pin per skill release:** every patch release would strand `ferryman`.
- **A descriptor shipped beside the script:** it frees `ferryman`'s release but changes the skill directory the manifest records.
- **The plugin route only:** it serves packs and not packages.

## References

- `docs/architecture/unattended-delivery-runner/14-installation-and-adoption-experience.md` (Distribution)
- `docs/architecture/unattended-delivery-runner/02-install-trust-and-detection.md` (descriptors and the version rule)
- `docs/architecture/unattended-delivery-runner/10d-folded-decisions-and-defaults.md` (D51, D53)
- `docs/architecture/unattended-delivery-runner/10c-review-decisions.md` (D50)
- `packages/AGENTS.md`
