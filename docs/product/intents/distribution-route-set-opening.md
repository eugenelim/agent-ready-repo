# Distribution route set opening

- **Status:** Draft
- **Level:** feature

## Outcome

A new distribution route, and a new canonical primitive on an existing route, are
each declared in `contracts/distribution-routes.toml` alone and are built, validated,
and published without a schema edit — with every value the schema pins today still
refused, and every path-shaped value that becomes free-form confined.

## Opportunity

`contracts/distribution-routes.schema.json` declares `route.additionalProperties`
as `false` and `route.required` as exactly the three shipped routes, and
`build/main.py:1297` validates the contract against the bundled copy. A fourth
route therefore cannot reach the resolver, so no test can prove the dispatch layer
is generic against a route that does not already exist — genericity is currently
provable only by the absence of route-name branches, not by adding a route.

## Assumptions

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

## Before starting this

- The dispatch extraction and surface completion ship first, in
  `docs/specs/distribution-route-registry/`. This intent is what remains after that
  slice deliberately excluded schema genericization.

## Source

- Mode: repo-origin
- Locator: docs/product/briefs/distribution-routes-programme.md
- Revision: sha256-bytes-v1:b8daba8a937964f1cc37233cd613cdc8993d53bdcf64bc580ea7799e4741829d
