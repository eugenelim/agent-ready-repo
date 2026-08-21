# Reference architecture

> **Normative.** This is the normative sibling of `overview.md`: the latter
> describes the directory map, while this document is the golden path for new
> work. A feature's low-level design reads it as steering, names the building
> blocks and standards it follows, and justifies any deviation. Its role is
> established by [ADR-0010](../adr/0010-reference-architecture-foundation.md).

## Constraints

- `packages/agentbundle/` is Python standard-library-only. Its scripts are
  projected into arbitrary adopter repositories and installed agent runtimes,
  where no third-party dependency can be assumed.
- `packages/credbroker/` is also Python standard-library-only and is the only
  credential path. Credentialed primitives use its public API and never read
  credential stores directly.
- `web/` uses Astro 7.1.0; `docs-site/` uses Astro 7.1.0 with Starlight
  0.41.4.
- Portable contracts are TOML plus JSON Schema in `contracts/`; compatible
  changes preserve both the contract declaration and its schema validation.
- Python quality tooling is pytest, ruff, and mypy. The SAST/SCA floor is
  bandit, semgrep, pip-audit, and npm audit; changes under `tools`, `packs`,
  `packages`, or `tests` run SAST.

## Solution strategy

- Author portable catalogue source in packs and profiles, then use
  `agentbundle` to resolve package builds through distribution routes and direct
  installs through adapter contracts. Pack source remains independent of routes,
  runtime adapters, and targets.
- Keep reusable, portable contracts in `contracts/`, with TOML declarations
  validated by their JSON Schemas.
- Use the Python standard library for `agentbundle` and `credbroker` so their
  projected and installed uses remain portable.
- Keep documentation and site content authored in `docs/`, `guides/`, `web/`,
  and `docs-site/`; site builders consume authored content and contracts.

## Building-block view / component catalogue

- **Pack.** A portable authoring unit that owns primitives, seeds, metadata,
  tests, and its declared dependencies.
- **Profile.** A composition of packs that adds no primitives.
- **Primitive.** A portable unit of one of five kinds: skill, agent,
  hook-body, hook-wiring, or command.
- **Adapter.** A target-runtime implementation of the portable adapter
  contract that selects direct-install projection modes.
- **Distribution route.** A package-format declaration with exactly six
  concerns: identity, package layout, manifest projector, component
  capabilities, marketplace projector, and lifecycle trigger. A route may name
  an adapter projector without transferring package ownership to that adapter.
- **Projection mode.** A build transformation that renders portable source as
  target-runtime files.
- **Broker.** The credential boundary that resolves credentials through
  `credbroker` without exposing secret material to repository source or agent
  context.
- **Seed.** Authored starter content installed or projected with a pack.

Component stereotypes:

- **New pack:** `packs/<pack>/pack.toml`, portable primitives under `.apm/`,
  tests under `packs/<pack>/tests/`, and declared dependencies.
- **New adapter:** declared in `contracts/adapter.toml`, implemented under
  `agentbundle/build/adapters/`, and selects projection modes implemented under
  `agentbundle/build/projections/`.
- **New distribution route:** declared in `contracts/distribution-routes.toml`
  and mapped to a named package projector. Generic registration remains
  unavailable until the accepted route-registry phase.
- **Credentialed primitive:** resolves through `credbroker`, using its public
  API and declared broker configuration; it exposes no secret material to
  repository source or agent context.

Composition follows the allowed dependency edges in `ARCHITECTURE.md`: pack
and profile declarations may depend on declared pack dependencies and
`contracts/`; build orchestration flows through route contracts and named
package projectors, while direct install and optional route adapter projection
flow through adapter contracts and projection implementations. Projections write target-runtime files. No
generated projection is an authoring dependency, packs do not infer
dependencies from other pack directories, and target-runtime files do not
depend on build internals.

## Crosscutting concepts / standards

- Apply the security review framework stack in
  [Security architecture](security.md), including its progressive boundary
  routing and always-on STRIDE + LINDDUN pass.
- Keep builds deterministic and byte-reproducible where repository contracts
  require rendered or bundled artifacts to match their source inputs.
- Preserve source-versus-projection ownership: edit authoring source, never a
  generated projection; a projection is never an authoring dependency.
- Default to no new dependency. Before adding one, record it in the owning
  package instructions or an ADR.
