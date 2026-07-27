# ADR-0056: catalogue_tooling as the portable catalogue engine module

**Status:** Accepted  
**Date:** 2026-07-27  
**Deciders:** eugenelim

## Context

The repository accumulated six standalone `tools/lint-*.py` scripts and one
`tools/run-pack-evals.py`, each implementing a discrete catalogue-level check
(agent-artifact lint, plugin-manifest validation, profile lint, credentialed-skill
lint, first-value contract, seeds lint, pack activation evals). Consumers — CI
jobs, `pre_pr_catalogue.py`, and Makefile targets — invoked these as subprocesses
with no shared abstraction or discoverable CLI surface.

ini-005 ("AgentBundle Portable Catalogue Tooling", milestone M1) specified that
the engine should expose these as first-class `agentbundle catalogue` subcommands
backed by a coherent Python module, so any adopter running `agentbundle` gets the
same checks without forking repo tooling scripts.

## Decision

Add `agentbundle/catalogue_tooling/` to the engine as the portable catalogue layer,
and expose it through the `agentbundle catalogue {lint,verify,self-host,build,
package,sync-defaults}` and `agentbundle pack evals run` CLI subcommands.

The module boundary: `catalogue_tooling/` owns all portable, schema-driven checks
that are correct for any repo using the agentbundle adapter contract. Repo-specific
gates (RFC/ADR-numbered policy lints, SAST, spec-state linters) stay in `tools/`
and are layered on top by `tools/repo/build_gate_chain.py`.

`agentbundle` version bumps to **0.13.0** (first public release carrying this
surface; prior 0.x versions are internal to this repo).

## Consequences

- Fourteen standalone `tools/lint-*.py` scripts and `tools/run-pack-evals.py`
  deleted; their CI call sites and Makefile targets rewired to the CLI.
- Old `tools/` entry points converted to thin shims so existing shell scripts /
  CI cache misses don't hard-fail before the cycle rolls over.
- The `catalogue_tooling/` module is engine behaviour; it is therefore subject to
  the `Engine-Change-RFC:` path-gate (RFC-0059 D6). This ADR is the exemption
  carrier for the initial landing PR.
- Adopters running `pip install agentbundle` gain the portable checks without any
  tools/ dependency.

## Alternatives considered

**Keep scripts in `tools/`, add thin wrappers.** Discarded — wrapping without
moving leaves duplicated logic and no discoverable public surface.

**Separate package (agentbundle-catalogue).** Discarded — the checks are tightly
coupled to the adapter contract already shipped in `agentbundle._data`; a second
package would require keeping them in sync with no benefit at the current user scale.
