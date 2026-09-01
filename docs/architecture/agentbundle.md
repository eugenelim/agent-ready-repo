# AgentBundle

## 1. Purpose and boundary

`agentbundle` is the reference CLI and build runtime for catalogue packs. It
reads pack source, validates route and adapter contracts, builds package-route
artifacts, and installs adapter projections into an adopter target.

It does not make generated projections authoring source. Pack source remains
under `packs/`; generated output is rebuilt from it.

## 2. Entrypoints

`agentbundle show --format json` is the pre-release OKF catalogue-discovery
surface for one selected pack. `list-packs` remains the catalogue inventory
surface.

The CLI verbs are `adapt`, `catalogue`, `config`, `diff`, `docs`,
`init-state`, `install`, `lint`, `list-installed`, `list-packs`,
`list-profiles`, `list-targets`, `oplog`, `pack`, `pack-config`,
`package-catalogue`, `reconcile`, `render`, `scaffold`, `show`,
`uninstall`, `upgrade`, and `validate`.

`catalogue` provides `lint`, `verify`, `build`, `self-host`,
`package`, `sync-defaults`, `init`, and `contracts`.

## 3. Owned state and write authority

The build writes Claude marketplace output and `catalogue-index.json` as
cross-pack generated artifacts. `show --format json` discovery data is excluded
from both outputs.

| State | Location | Write authority | Readers |
| --- | --- | --- | --- |
| Pack source | `packs/<pack>/` | Pack maintainers | Catalogue and build commands |
| Portable contracts | `contracts/` | Contract maintainers | Validators and build runtime |
| Projection output | `dist/`, `.claude/`, `.codex/`, `.agents/` | Catalogue build and self-host commands | Install routes and agent runtimes |
| Install state | `.agentbundle-state.toml` | Install, upgrade, uninstall, and init-state commands | List, diff, reconcile, and upgrade |
| Direct-source provenance | `.agentbundle-state.toml` (schema 0.5) | Direct install and upgrade | List, show, and upgrade re-consent |
| Adaptation marker | `.adapt-install-marker.toml` | `agentbundle install` or `install-marker.py` | Core session-start and adapt workflows |

## 4. Dependencies and allowed edges

Commands call catalogue tooling and the build runtime. Package builds read
`contracts/distribution-routes.toml`, select an existing named package
projector, and optionally invoke the route's declared adapter projector. Direct
installation reads `contracts/adapter.toml`, then runs adapters and projection
modes.

The adapter layer contains Claude Code, Codex, Copilot, Cursor, Gemini, Kiro,
Kiro CLI, and Kiro IDE adapters. Projection implementations write target-runtime
files; target-runtime files do not depend on build internals.

Install and upgrade commands write only their target, state, and permitted
configuration. The catalogue source is read-only to consumer commands.

## 5. Primary flows

1. Catalogue build discovers pack manifests, validates explicit recipe route
   identity, and renders APM or Claude package artifacts through the named route
   projector into `dist/`. Self-host and direct install remain adapter-owned.
2. Install projects selected pack content into the resolved target and records
   scope-specific install state. Repository scope may also deliver seeds;
   local scope deliberately does not.
3. Direct repository-scope install writes an adaptation marker and chains the
   deterministic `adapt` command. Local scope writes neither. Package-route
   hooks may write the same marker only when the active runtime projects and
   executes them. A successful direct core install emits an explicit manual
   `adapt-to-project` next action independently of hook execution.
4. Upgrade, uninstall, diff, reconcile, and init-state operate against recorded
   install state and target content.

## 6. Failure and recovery behavior

Contract or manifest validation failure stops projection. File-safety rules
preserve protected target content during install, upgrade, and uninstall.

`diff` reports projection drift. `reconcile` reports user-scope orphaned
configuration without applying changes. `adapt` reports upstream companions
instead of silently overwriting them.

## 7. Observability and evidence

`list-installed`, `show`, `diff`, `reconcile`, and `validate` expose
installed state, source content, drift, orphaned configuration, and conformance.

Build output, self-host projections, manifests, and install-state files provide
the durable evidence record.

## 8. Mechanical invariants

- `agentbundle catalogue verify` verifies projected agent artifacts and
  adapter conformance.
- The self-host drift gate raises `CAT-V-015` for source/projection drift and
  `CAT-V-014` for generated `dist/` drift.
- `tools/catalogue/check_contract_parity.py` requires portable contract schemas
  and TOML to match their `agentbundle/_data/` counterparts.
- Distribution-route golden tests pin complete APM and Claude package trees by
  path, bytes, link target, and mode across the route/adapter ownership split.
- `agentbundle lint packs` (`make lint-packs`) checks pack conformance.
- `tools/lint-adapter-layer-boundary.py` holds the adapter/projection edge
  direction: a projection may not import an adapter, and neither layer may be
  imported by pack source or by a target-runtime file.
- `tools/lint-generated-path-ownership.py` requires each canonical generated
  projection path to have exactly one declared producer and refuses a
  hand-authored file occupying one. It reads the producer set from the self-host
  recipe and the target roots from `contracts/adapter.toml`, so a pack leaving
  the recipe changes the expected set rather than passing on an empty scan.

## 9. Relevant ADRs

- [ADR-0002 — Per-pack install scope](../adr/0002-install-scope-per-pack-default-and-allowance.md)

## 10. Last verified against commit

`c8cf4b37`
