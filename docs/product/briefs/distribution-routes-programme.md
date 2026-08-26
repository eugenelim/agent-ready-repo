# Brief: Land the distribution-route layer accepted by RFC-0092

- **Slug:** `distribution-routes-programme`
- **Received:** 2026-08-20
- **Owner:** Platform Core (`ini-002`)
- **Status:** Executing

## Outcome

Packaging a pack for an external plugin ecosystem is a named, contract-declared
**distribution route**, owned separately from the **runtime adapter** that installs
components into a live agent's directories. A maintainer can add a package format by
declaring a route rather than by editing another vendor's adapter contract, and every
route states honestly which canonical primitives it carries, which it drops, and
whether it can trigger repository-aware adaptation at all.

Canonical primitives added for a distribution route are not route-only features.
The same delivery slice must add normalized pack-model support and direct
`agentbundle` install parity for every runtime adapter that declares support for
the primitive. A slice is incomplete if the plugin package can carry a canonical
primitive but `agentbundle install` cannot project it through the applicable
adapter and scope.

## Success metrics

- `install-routes` is declared in a route-owned contract, not under
  `[adapter."claude-code"]`, and the vendor-neutral `apm` route is no longer a child of
  the Claude adapter.
- The Claude and APM package outputs are byte-identical across the contract move, proved
  by golden fixtures rather than asserted.
- A conforming portable Agent Plugin package is emitted for every pack that has no
  portable-excluded primitive — 13 of the 21 buildable packs at time of writing.
- Every newly added canonical primitive is validated once in the normalized pack
  model and, in the same delivery slice, is supported by direct `agentbundle`
  installation for each capable runtime adapter and by every distribution route
  whose capability map claims it. Route-only support does not satisfy parity.
- Every route's per-primitive status is machine-readable and drives both build
  diagnostics and the published support matrix; no route claims `runtime-verified`
  without a recorded per-client test naming client, version, surface, and OS.
- Claude and Codex each publish a native marketplace manifest derived from the
  same catalogue source. Their publication workflows share the route's
  user-scope eligibility rule and do not schedule publication for unrelated
  commits; changes to an eligible user-scope pack or to the marketplace
  build/publication contract remain publication inputs.
- A pack declaring a required semantic that a route cannot preserve **fails the build**
  for that route rather than emitting a silently degraded package.

## Scope / Non-goals

**In scope:**

- The route contract and the minimal route resolver (Phase 0); the portable Agent Plugin
  projection (Phase 1A); the canonical MCP primitive with direct `agentbundle` install
  parity and route projections (Phase 1B); registry extraction once three real routes
  exist (Phase 2); the native Codex route and its marketplace, plus user-scope
  trigger parity for both Claude and Codex publishers (Phase 3); the Kiro Power
  route profile (Phase 4); Claude-manifest migration and public-matrix updates
  (Phase 5).
- The hook semantic-compatibility model, and the support-claim and runtime-verification
  record that the matrix reads from.
- A same-wave parity invariant for every new canonical primitive: source and schema,
  normalized pack model, applicable direct-install adapter projections, claimed route
  projections, diagnostics, and documentation ship together.
- Carrying the Claude route *forward* through every phase — each phase records what the
  Claude route gains, rather than migrating it to a legacy path.

**Non-goals:**

- Implementing a Copilot route. It is inventoried and the abstraction is stress-tested
  against it, deliberately, so the design is not Claude-and-Codex-shaped.
- A universal agents, commands, or rules format. Portable v1 excludes all three and its
  1.1.0 working draft explicitly keeps excluding them.
- Replacing `agentbundle install`. Direct installation remains the only route that can do
  everything; plugin routes are additive.
- Moving seeds into portable packages, or claiming adaptation or seed parity on any route
  whose client documents no lifecycle trigger.
- Treating route-specific manifest metadata or reverse-domain extension content as a
  canonical primitive merely to force direct-install parity. The parity invariant applies
  when the pack model promotes a component to a canonical primitive.
- MCP servers acquired from package registries. Deferred to its own RFC, and **already
  closed at the build boundary** rather than merely postponed — see Rabbit holes.
- Making any generated manifest an authoring source.

## Appetite

A bounded, ordered programme of six phases, sequenced by dependency rather than by
product. Phase 1 contains two independently shippable slices: the portable package
baseline (1A), followed by the canonical MCP primitive and its end-to-end install parity
(1B). A phase that requires a new dependency, a new authoring surface, or a public
compatibility break leaves this programme until an approved amendment moves the boundary.

## Rabbit holes

- Do not build the generic route registry before three real routes exist. A spike drafted
  it and argued against itself: four of six candidate routes would contribute placeholder
  lifecycle and consent fields, and a registry that encodes `unknown` as an authoritative
  field name hides missing contract acquisition instead of removing special cases.
- Do not treat the `apm` re-parenting as free. It touches a closed enum in
  `contracts/adapter.schema.json`, a byte-identical bundled copy under a parity gate, and
  two contract tests — one of which asserts that *no other adapter* carries
  `install-routes` and must be rewritten rather than deleted.
- Do not let the MCP admission rule reject remote servers. The bundled-command and
  launcher prohibitions apply to `stdio` only; `streamable-http` and `sse` have no
  `command` and are admitted on endpoint controls instead.
- Do not rely on schema conformance to protect credentials. A secret-bearing
  `Authorization` header validates cleanly against the official portable schema; the
  boundary is refusing the server, and the lint is defence in depth.
- Do not assume ADR-0079 covers a new executable route. Its decision is scoped to one
  exact ref, and the publisher branch name is hard-coded. Each executable route lands its
  own equivalent control as an acceptance condition.
- Do not claim a control lives where it does not. The build does **not** currently use the
  blessed `file_safety` helpers; symlink handling is partial and inconsistent across
  build modules.
- Do not project Kiro steering from an invented source. `dev.kiro/steering/` has no source
  in `.apm/` today; ship the extension point empty rather than fabricate content.
- Do not promote any client claim on documentation alone. Every external-client behavior
  in RFC-0092 is documentation-verified, never runtime-verified.

## Instrumentation

- Golden fixtures pinning Claude and APM outputs byte-for-byte across Phase 0 and Phase 2.
- Offline schema validation against vendored portable schemas, with licence and provenance
  recorded alongside; no network access during a normal build.
- Determinism, path containment, symlink behavior, file ordering, line endings, executable
  modes, multi-pack marketplace generation, duplicate identity, and component collision
  all fixture-pinned.
- A per-client runtime-verification record — client, version, surface, OS, install route,
  components tested, date, evidence, limitations — gating every support claim above
  `documentation-verified`.

## Decision authority

Architecture is settled by [RFC-0092](../../rfc/0092-first-class-distribution-routes.md)
(Accepted) and recorded durably by
[ADR-0090](../../adr/0090-distribution-routes-separate-from-runtime-adapters.md) and
[ADR-0091](../../adr/0091-kiro-power-route-supersedes-rejection.md). This brief sequences
delivery; it does not reopen those decisions. RFC-0092 carries two owned open questions
(the Claude-manifest deprecation window, and whether Kiro steering becomes a canonical
authoring primitive) which their phases resolve.

## Confirmed delivery slices

The brief uses no user-story list; coverage is spec-granular. The confirmed cut is
dependency-ordered, and each slice includes the guide and verification evidence needed
to ship independently.

| Slice | Ships | Hard predecessor |
| --- | --- | --- |
| Phase 0 — route contract | Route-owned contract, minimal resolver, APM re-parenting, unchanged Claude/APM golden output | — |
| Phase 1A — portable projection | Vendored portable schemas, deterministic Agent Plugin manifest and skills projection, extension namespaces | Phase 0 |
| Phase 1B — canonical MCP parity | Canonical MCP source/model, direct `agentbundle` install projections for capable adapters, portable and claimed native-route projections, fail-closed security controls | Phase 1A |
| Phase 2 — registry extraction | Generic six-field route registry extracted from three real routes | Phase 1B |
| Phase 3 — native Codex route | Native package and marketplace manifest, hook translation, shared user-scope publication eligibility with Claude, unrelated-commit trigger suppression, honest components-only claim until adaptation prerequisites exist | Phase 2 |
| Phase 4 — Kiro Power profile | Portable-package route profile, Kiro admission and activation semantics, empty extension point unless separately approved | Phase 3 |
| Phase 5 — migration and claims | Claude-manifest residue migration, public support matrices, compatibility-alias expiry and programme closeout | Phase 4 |

The parity rule is evaluated in the slice that introduces a canonical primitive,
not deferred to a later route or cleanup phase. Phase 1B is the first application:
MCP must work through direct `agentbundle` installation and the routes that claim MCP
support before that slice can ship.

## Spec map

Status is derived from each linked delivery spec rather than maintained
independently here. Remaining confirmed slices stay as typed backlog intents until
`new-spec` promotes them.

| Spec | Status |
| --- | --- |
| `distribution-route-contract` | Shipped |
| `portable-agent-plugin-projection` | Shipped |

## Derived work

Each confirmed slice materializes its own spec through `new-spec`; Phase 0 is the
first such delivery contract and remains non-dispatchable until human approval.
Phase 1 deliberately produces separate portable projection and canonical MCP
parity specs. The follow-on artifacts RFC-0092 names are the
distribution-route contract, the portable projection, the canonical MCP primitive, the
Codex route, hook semantic compatibility, generalized project adaptation, marketplace
projection, the Claude-manifest migration, and the runtime-verification/support-matrix
contract — plus a separate RFC for MCP-from-package-registries.
