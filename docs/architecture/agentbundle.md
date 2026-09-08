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
`contracts/distribution-routes.toml`, look up the behavior registered for each
declared route, and optionally invoke the route's declared adapter projector.
Direct installation reads `contracts/adapter.toml`, then runs adapters and
projection modes.

### Distribution-route dispatch

Shared build-time code never names a distribution route. Every route-dependent
decision comes from `contracts/distribution-routes.toml`, through two readers in
`agentbundle/build/route_lookup.py`:

- `read_route_declarations()` returns each route's declared facts — output
  subdirectory, admission policy, adapter projector, marketplace projector,
  lifecycle trigger, and component capabilities. Shared code that needs a *set*
  reads it here, so a surface's route set equals the declared set by
  construction rather than by a maintained list.
- `resolve_route_behaviors()` returns exactly one registered behavior per
  declared route. Shared code that needs *behavior* calls through it.

Route-specific code lives only in a module serving exactly one route:
`build/route_apm.py`, `build/route_claude_plugins.py`, and
`build/route_agent_plugin.py`. Each recognises its own declaration by projector
semantics rather than by route name, and owns what the contract cannot state —
its filesystem controls, its diagnostics, its install-marker path, and its
position in a default build.

Build order is one such route-owned fact and it is load-bearing: a route that
can refuse a pack runs before any route that writes one, so a refused build
leaves no partial output tree behind.

**Adding a route** touches four things, in this order:

1. Declare it in `contracts/distribution-routes.toml` and admit it in
   `contracts/distribution-routes.schema.json`, then sync both into
   `agentbundle/_data/`. The contract-parity gate requires the two copies to
   match byte for byte.
2. Add its per-pack recipe TOML under `build/recipes/`, declaring the new
   `route`. `DEFAULT_RECIPES` is derived from these declarations, so without one
   the route is declared but never built.
3. Add a `build/route_<name>.py` module whose `behavior_from_declaration()`
   recognises that declaration and returns its behavior, including the
   route-owned facts the contract cannot state — its build order, its
   filesystem controls, and its install-marker path if it declares one.
4. Register that factory in `route_lookup.py`. Registration is explicit because
   the route set is closed; nothing is discovered at import.

No *consuming surface* changes: every surface reads the route set from the
contract. The byte goldens do change, because they pin the complete built tree
for every declared route.

`tools/check_distribution_route_decisions.py` fails if a later change
reintroduces a route decision into shared code.

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
- Distribution-route golden tests pin complete APM, Claude, and Agent Plugin
  package trees by path, bytes, link target, and mode across the route/adapter
  ownership split.
- `tools/check_distribution_route_decisions.py --check` reports shared
  build-time code that decides by route — whether it spells a route name or
  compares a contract-derived route value — and refuses unclassified route-value
  flow rather than treating it as clean. It is a bounded static check: the
  literal form is covered everywhere, the value form where the route types are
  annotated, and the script's own `limits` list records what it does not follow.
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
