# Distribution route set opening

- **Slug:** `distribution-route-set-opening`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:first-class-distribution-routes
- **Depends on:** spec:distribution-route-registry

## Outcome

A new distribution route, and a new canonical primitive on an existing route, are
each declared in `contracts/distribution-routes.toml` alone and are built, validated,
and published without a schema edit — with every value the schema pins today still
refused, and every path-shaped value that becomes free-form confined.

## Opportunity

`contracts/distribution-routes.schema.json` declares `route.additionalProperties`
as `false` and `route.required` as exactly the three shipped routes, and
`build/main.py` validates the contract against the bundled copy of the schema. A fourth
route therefore cannot reach the resolver, so no test can prove the dispatch layer
is generic against a route that does not already exist — genericity is currently
provable only by the absence of route-name branches, not by adding a route.

## Boundary

This feature owns making the route set open while preserving the existing
confinement and compatibility authority.

It does not make route handlers self-authorizing, change shipped route behavior,
or add a real fourth route.

## Assumptions

- **Riskiest assumption:** the closed schema's compatibility guarantees can move to an independent authority without letting a handler widen its own accepted values.
- The three per-route schema blocks are structurally identical once enum values are
  erased, so one reusable shape can replace them. Measured 2026-09-02.
- Of the 35 enum sites per route, 33 are single-value pins. They are the declarative
  enforcement behind four of the eight refusal classes the shipped
  `distribution-route-contract` spec fixes: an unknown support status, a
  capability-map omission, an unknown projector, and a layout, admission, or
  lifecycle declaration conflicting with its named projector.
- Replacing those pins with handler-declared compatibility metadata was attempted in
  design across three review rounds and rejected each time. The recurring defect is
  that a handler declaring its own compatibility is self-authorizing, so it can widen
  what the contract accepts. An independent compatibility authority is required.
- Opening the set makes several currently-pinned values free-form and therefore
  newly attackable: a capability `target-path` and a `package-layout.output-subdir`
  become path-shaped inputs needing canonicalization and confinement, and a route's
  declared `identity` can diverge from its table key.
- Dynamic handler discovery becomes necessary once a route can appear without a code
  edit, which introduces an import-time trust boundary the closed-set slice does not
  have.
- Two proofs are the point of the slice and neither is possible before it: a synthetic
  fourth route resolving and building through the production loader, and a synthetic
  tenth capability projecting on every declared route. The capability half is the one
  makes a later canonical primitive arrive as a contract entry plus a projector rather
  than an edit to each per-route schema block. Whether any particular later slice waits
  on that is the brief's sequencing decision, not this intent's to assert.
- **Knowledge surface:** In-repository RFC-0092, distribution-routes programme brief, shipped registry contract, and review history.

## Before starting this

- The dispatch extraction and surface completion ship first, in
  `docs/specs/distribution-route-registry/`. This intent is what remains after that
  slice deliberately excluded schema genericization.

## Readiness

- **Route:** `new-spec`, full mode, with a security review. It changes a trust boundary: handler discovery and path-shaped values.
- **Verified 2026-11-05:** a fourth route copied from `apm` into `contracts/distribution-routes.toml` is refused by the schema with `Additional properties are not allowed ('fourth' was unexpected)`. The base contract validates with zero errors. The set is still closed.
- **Design answer to the riskiest assumption:** keep the compatibility pins in the contract layer, not in handlers. One reusable route schema shape holds the structure. A separate compatibility table in the contract, owned by the route-contract spec and not by any handler, holds the per-projector value pins. A handler can then name which table row it uses but cannot add values.
- **First slice and its agent-only proof:** write the two failing proofs first. (1) A synthetic fourth route resolves and builds through the production loader. (2) A synthetic tenth capability projects on every declared route. Then add confinement fixtures for `target-path`, `output-subdir`, and an `identity` that differs from its table key. All run offline in `pytest`.
- **Authority:** RFC-0092 governs. Recent engine commits on `route_claude_plugins.py` cite RFC-0092 in their `Engine-Change-RFC:` trailer.
- **Size:** two sessions (schema and loader, then confinement and discovery trust boundary).
- **Order in the programme:** parallel with FEAT-0021. It is required by FEAT-0022 and makes FEAT-0023 simpler.

## Source

- Mode: repo-origin
- Locator: docs/product/briefs/distribution-routes-programme.md
- Revision: sha256-bytes-v1:b8daba8a937964f1cc37233cd613cdc8993d53bdcf64bc580ea7799e4741829d
