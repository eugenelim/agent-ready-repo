# Brief: Land the distribution-route layer accepted by RFC-0092

- **Slug:** `distribution-routes-programme`
- **Received:** 2026-08-20
- **Owner:** Platform Core (`ini-002`)
- **Status:** Draft

## Outcome

Packaging a pack for an external plugin ecosystem is a named, contract-declared
**distribution route**, owned separately from the **runtime adapter** that installs
components into a live agent's directories. A maintainer can add a package format by
declaring a route rather than by editing another vendor's adapter contract, and every
route states honestly which canonical primitives it carries, which it drops, and
whether it can trigger repository-aware adaptation at all.

## Success metrics

- `install-routes` is declared in a route-owned contract, not under
  `[adapter."claude-code"]`, and the vendor-neutral `apm` route is no longer a child of
  the Claude adapter.
- The Claude and APM package outputs are byte-identical across the contract move, proved
  by golden fixtures rather than asserted.
- A conforming portable Agent Plugin package is emitted for every pack that has no
  portable-excluded primitive — 13 of the 21 buildable packs at time of writing.
- Every route's per-primitive status is machine-readable and drives both build
  diagnostics and the published support matrix; no route claims `runtime-verified`
  without a recorded per-client test naming client, version, surface, and OS.
- A pack declaring a required semantic that a route cannot preserve **fails the build**
  for that route rather than emitting a silently degraded package.

## Scope / Non-goals

**In scope:**

- The route contract and the minimal route resolver (Phase 0); the portable Agent Plugin
  projection and the canonical MCP primitive (Phase 1); registry extraction once three
  real routes exist (Phase 2); the native Codex route (Phase 3); the Kiro Power route
  profile (Phase 4); Claude-manifest migration and public-matrix updates (Phase 5).
- The hook semantic-compatibility model, and the support-claim and runtime-verification
  record that the matrix reads from.
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
- MCP servers acquired from package registries. Deferred to its own RFC, and **already
  closed at the build boundary** rather than merely postponed — see Rabbit holes.
- Making any generated manifest an authoring source.

## Appetite

A bounded, ordered programme of six phases, sequenced by dependency rather than by
product. A phase that requires a new dependency, a new authoring surface, or a public
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

## Derived work

Each phase materializes its own spec through `new-spec`; none exist yet, which is why this
brief is `Draft` and non-dispatchable. The follow-on artifacts RFC-0092 names are the
distribution-route contract, the portable projection, the canonical MCP primitive, the
Codex route, hook semantic compatibility, generalized project adaptation, marketplace
projection, the Claude-manifest migration, and the runtime-verification/support-matrix
contract — plus a separate RFC for MCP-from-package-registries.
