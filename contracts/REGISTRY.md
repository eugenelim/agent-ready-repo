# `contracts/` backward-traceability registry

Every spec that names a contract carries a forward pointer: the `- **Contract:**`
header in its `spec.md`. This file carries the matching backward pointer for the
contracts that cannot carry one themselves.

A contract in a format with vendor extensions — `.yaml`, `.yml`, `.json` — records
its defining specs inline, in an `x-spec` key. Every other format has nowhere to
put that key: TOML contracts here validate against closed schemas that reject an
unknown top-level key, and the Markdown files under `contracts/vendor/` are
vendored upstream text this repository does not modify. Those contracts are
listed below instead.

## How this file is read

`lint-spec-status.py` invariant (v) checks each spec's `Contract:` header against
this table. A back-reference counts only when **one row** names the contract token
and that spec's directory. Two things in a row are therefore load-bearing:

- the contract path appears exactly as the spec's header writes it, and
- the spec directory carries its trailing `/`.

Without the trailing slash, `docs/specs/foo` would be satisfied by a row naming
`docs/specs/foo-bar/`; this repository has 12 such spec-directory prefix pairs.

The lint itself is layout-tolerant: the table pipes, the backticks and the column
order carry no meaning for it, and a bullet holding the same pair reads the same.
**This repository's own copy is pinned tighter than the lint requires.**
`tests/roster/test_contract_backward_registry.py` parses only the two-cell
backticked table row above, so a row written in any other layout is invisible to
it and the run reports the pair as missing. Adopters who copy this convention
inherit the lint's tolerance; this file does not use it.

One contract may appear on several rows, once per spec that names it. The finding
is warn-only: a missing row reports, it does not fail the run.

## Adding a row

Add one when a spec's `Contract:` header names a contract whose extension is not
`.yaml`, `.yml` or `.json`. Do not hand-write the pair set — derive it, as
`tests/roster/test_contract_backward_registry.py` does, from the same
`contract_header_refs` parser the lint uses. That test fails when this table and
the spec corpus disagree.

## Pairs

| Contract | Spec |
| --- | --- |
| `contracts/README.md` | `docs/specs/catalogue-wave1-contract-convergence/` |
| `contracts/adapter.toml` | `docs/specs/claude-plugin-hook-parity/` |
| `contracts/adapter.toml` | `docs/specs/distribution-route-contract/` |
| `contracts/adapter.toml` | `docs/specs/enriched-pack-manifest/` |
| `contracts/agent-plugin-extension-namespaces.toml` | `docs/specs/portable-agent-plugin-projection/` |
| `contracts/distribution-routes.toml` | `docs/specs/distribution-route-contract/` |
| `contracts/distribution-routes.toml` | `docs/specs/distribution-route-registry/` |
| `contracts/distribution-routes.toml` | `docs/specs/portable-agent-plugin-projection/` |
| `contracts/vendor/agent-plugins/1.0.0/LICENSE.md` | `docs/specs/portable-agent-plugin-projection/` |
| `contracts/vendor/agent-plugins/1.0.0/PROVENANCE.md` | `docs/specs/portable-agent-plugin-projection/` |
