# Architecture

Directory map: [`docs/architecture/overview.md`](docs/architecture/overview.md).
Normative golden path: `docs/architecture/reference.md`.

## 1. Systems

| System | Responsibility |
| --- | --- |
| Catalogue and pack authoring | Defines packs, profiles, primitives, seeds, and pack metadata. |
| Pack projection and distribution | Resolves declared distribution routes and renders pack sources into package artifacts and release outputs. |
| Installation and upgrade | Installs, upgrades, reconciles, or removes projected content under the file-safety contract. |
| Adapter and runtime integration | Applies the adapter contract to project primitives into each supported agent runtime. |
| Repository governance and context | Holds contributor context, decisions, proposals, specifications, and current-state documentation. |
| Work intake and coordination | Normalizes incoming work and routes it into the repository artifact lifecycle. |
| Execution harness and review | Runs supervised work, records its progress, invokes gates, and hands work to review. |
| Project knowledge | Captures observations, distils them into durable knowledge, and supports explicit enquiry. |
| Credentials and trust boundaries | Resolves credentials outside repository content and confines credentialed operations. |
| Documentation and site publishing | Authors and publishes current documentation; binder publishing is STATUS: PLANNED. |

## 2. Responsibilities

`packs/` owns portable authoring source. `profiles/` composes packs without
adding primitives. `contracts/` defines portable schemas, distribution-route
contracts, and direct-install adapter contracts.

`packages/agentbundle/` owns the catalogue CLI, build pipeline, adapters,
projection modes, install commands, and install state. `packages/credbroker/`
owns in-process credential resolution and local credential storage access.

`docs/`, `guides/`, and `web/` own authored documentation and site content.
`tools/` owns repository-only validation and publication support.

The core pack provides the session hooks and skills that connect adaptation,
work intake, knowledge capture, execution, and review in an installed repo.

## 3. Allowed dependency edges

- Pack and profile declarations → declared pack dependencies and `contracts/`.
- `agentbundle` commands → catalogue tooling and build orchestration.
- Build orchestration → distribution-route contract → named package projectors.
- Direct installation and an optional route adapter projector → adapter contract
  → adapter implementations → projection implementations.
- Install and upgrade commands → rendered artifacts and install-state writers.
- Adapter projections → target-runtime files. Target-runtime files do not
  depend on build internals.
- Credentialed primitives → `credbroker` public API and declared broker
  configuration. They do not read credential stores directly.
- Work-intake adapters → normalized intake → canonical repository artifacts.
- Execution and review workflows → canonical work artifacts and recorded run
  state.
- Site builders and repository tools → authored content and contracts.

No generated projection is an authoring dependency. No pack may infer a
dependency from another pack's directory. No runtime adapter may become a
dependency of pack source or of a target runtime.

## 4. State ownership

| State | Location | Write authority | Readers |
| --- | --- | --- | --- |
| Pack source and metadata | `packs/<pack>/` | Owning pack maintainers | Catalogue tooling, builders, reviewers |
| Profile composition | `profiles/` | Profile maintainers | Catalogue and install commands |
| Portable contracts | `contracts/` | Contract maintainers | Builders, validators, package data projection |
| Release and self-host projections | `dist/`, `.claude/`, `.codex/`, `.agents/` | `agentbundle` build and self-host commands | Install routes, local agent runtimes, checks |
| Catalogue configuration | `catalogue.toml` | Catalogue maintainers | Catalogue tooling and self-host build |
| Installed-content state | install target and `.agentbundle-state.toml` | `agentbundle` install, upgrade, uninstall, and init-state commands | List, diff, reconcile, and upgrade commands |
| Adaptation marker | `.adapt-install-marker.toml` | `agentbundle install`; `install-marker.py` for plugin and APM routes | `core` session-start hook and `adapt-to-project` |
| Governance records | `docs/adr/`, `docs/rfc/`, and `docs/specs/` | `new-adr`, `new-rfc`, and `new-spec` | Contributors and reviewers |
| Canonical work artifacts | `docs/product/` and `docs/specs/` | The workflow that creates the artifact | Workflows, contributors, reviewers |
| Lifecycle index | `workspace.toml` | `work-intake` and its selected workflow | `workspace-status`, execution, review |
| Tracker provenance | Canonical artifact and its index entry | The accepting intake workflow | Refresh and reconciliation workflows |
| Harness phase state | `docs/specs/**/engine-state.json` (gitignored) | `loop-engine.py` | Harness operators |
| Harness cohort state | `docs/specs/**/state.json` (gitignored) | `loop-cohort.py` | Harness operators |
| Harness events | `.loop-run/events.jsonl` (ephemeral) | `loop-engine.py` | Harness operators and workspace MCP |
| Knowledge records | `docs/knowledge/` | `project-knowledge/scripts/knowledge_store.py` | Capture, enquiry, review, and research workflows |
| Credential material | OS credential store and `~/.agentbundle/credentials.env` | `credbroker` write API | Credential brokers in the invoking process |
| Authored site content | `guides/`, `web/`, and `docs-site/` | Content maintainers | Site build and documentation checks |
| Published site output | site build output | Site build | Link, contrast, and publication checks |

## 5. Major flows

1. **Pack source → projection → install.** A pack's `pack.toml`, `.apm/`,
   plugin metadata, and seeds are discovered by `agentbundle catalogue build`
   or `agentbundle render`. The build pipeline resolves explicit recipes against
   `contracts/distribution-routes.toml`, then applies its named package projector
   and any declared runtime-adapter projector. `agentbundle install`, APM, or a plugin route writes the
   projected content into its target scope.
2. **Install marker → adaptation.** An install route writes
   `.adapt-install-marker.toml`. The `core` `session-start.py` hook reads it on
   a later session and directs the agent to `adapt-to-project`. The
   `agentbundle adapt` command resolves adaptation markers and reports upstream
   companions.
3. **Work intake → context resolution → execution → handoff.** A tracker or
   local request enters `work-intake`, which classifies it into canonical
   artifacts and lifecycle membership. `workspace-status` and the execution
   harness resolve context, `work-loop` performs approved work and gates, then
   hands the diff and evidence to reviewers or the requesting contributor.
4. **Scratch → knowledge capture → enquiry.** `project-knowledge` capture
   admits a strict observation from scratch material. Its distill mode
   reconciles pending observations into topics under `docs/knowledge/`. Its
   enquire mode reads committed topics for an explicit question.
5. **Source change → lint/test/build → publication.** Maintainers change
   source or authored content. `make ci` lints, tests, and validates the
   repository. `make build-check` validates projections and repository gates.
   The site build renders publication output, which publication consumes.

## 6. Extension points

- A new pack adds a `packs/<pack>/pack.toml`, portable primitives, tests, and
  declared dependencies.
- A profile composes existing packs without owning new primitives.
- An adapter is declared in `contracts/adapter.toml` and implemented through
  the build adapter and projection interfaces.
- A distribution route is declared in `contracts/distribution-routes.toml` with
  package identity, layout, manifest projector, component capabilities,
  marketplace projector, and lifecycle trigger. Until the route-registry phase,
  each route maps to an existing named projector in build orchestration.
- A projection mode is implemented under `agentbundle.build.projections` and
  selected by an adapter contract.
- A credential broker implements the credentialed-primitive contract without
  exposing secret material to repository source or agent context.
- A work-intake adapter may acquire a source, but it must route content through
  the normalized intake boundary before repository writes.
- A site surface is authored in `guides/` or `web/` and published through the
  existing site build.

## 7. Mechanically enforced invariants

- `agentbundle catalogue verify` verifies projected agent artifacts and adapter
  conformance.
- `make build-check` verifies that the self-host projection matches its source
  inputs.
- `tools/catalogue/check_contract_parity.py` verifies that portable contracts
  and bundled contract copies remain byte-identical where required.
- `tools/lint-pack-test-boundary.py` keeps pack test content out of projected
  runtime content and keeps pack tests in their owning pack tree.
- `tools/lint-plugin-membership.py` and `tools/lint-plugin-roster.py` enforce
  the user-scope plugin publication boundary.
- `tools/lint-sso-config.py` requires shipped SSO configuration to remain
  placeholder-shaped and opt-in.
- `tools/lint-agents-md.py` requires `CLAUDE.md` to remain a symlink to the
  canonical root `AGENTS.md`.
- `tools/check-rendered-site-links.py` validates internal links and fragments
  in rendered site output.
- `tools/lint-adapter-layer-boundary.py` enforces the section 3 edge direction
  for the build layers: a projection may not import an adapter, and neither
  layer may be imported by pack source or by a target-runtime file.
- `tools/lint-pack-dependency-declaration.py` requires a pack that reaches into
  another pack's directory from executable content to declare that pack, and
  fails a declared dependency whose owning pack contributes no referenced
  primitive.
- `tools/lint-generated-path-ownership.py` requires every canonical generated
  projection path to have exactly one declared producer, and refuses a
  hand-authored file occupying one.

## 8. Deeper current-state pages

- [Directory map](docs/architecture/overview.md)
- [Catalogue](docs/architecture/catalogue.md) and
  [pack layout](docs/architecture/pack-layout.md)
- [Skill and pack format](docs/architecture/skill-and-pack-format.md) and
  [pack manifest](docs/architecture/pack-manifest.md)
- [AgentBundle](docs/architecture/agentbundle.md)
- [Credentials](docs/architecture/credentials.md)
- [Work intake and artifact routing](docs/architecture/work-intake-and-artifact-routing.md)
- [Loop infrastructure](docs/architecture/loop-infrastructure.md) and
  [workspace MCP](docs/architecture/workspace-mcp/design.md)
- [Knowledge capture](docs/architecture/knowledge-capture.md)
- [Security architecture](docs/architecture/security.md)
- [Documentation architecture index](docs/architecture/README.md)

### Planned architecture

- **STATUS: PLANNED** — [Binder publishing](docs/architecture/binder-publishing/README.md)
  is designed but not implemented. [ADR-0073](docs/adr/0073-zensical-as-the-v1-binder-renderer.md)
  governs its renderer decision.

## 9. Last verified against commit

`4e81d407`
