# Distribution route registry extraction

- **Status:** Draft
- **Level:** feature

## Outcome

Every surface that consumes distribution routes takes its route set from
`contracts/distribution-routes.toml`, and no shared build-time code selects behavior by
a route's name — so the `agent-plugin` route, which one of fifteen such surfaces carries
today, is present on all of them.

## Opportunity

Route dispatch is spread across route-name branches and hand-maintained route lists in
the build pipeline, the CLI, the install and upgrade surfaces, the catalogue verifier,
the lint pass, and the build-check. Every one of those lists predates the portable
route, so a route that ships still has to be added to fourteen places by hand, and
`catalogue verify` does not check its output tree at all. Three of the six resolved
contract fields are read into `ResolvedDistributionRoute` and barely used, while
`packages/agentbundle/agentbundle/build/main.py:1256` re-states two of them as literal
dictionaries keyed on route name.

Admitting a route the contract has not declared is a separate concern: the route schema
is closed, so it is [[distribution-route-set-opening]] that makes a route declarable
without a schema entry. This intent is bounded to dispatch and completion over the three
declared routes.

## Assumptions

- Phase 1A supplied the third real route (`agent-plugin`) and has shipped, so
  D1's gate is met. Phase 1B adds a canonical *primitive*, not a route, and does
  not advance that gate. Extraction runs before 1B per the
  [RFC-0092 erratum](../../rfc/0092-first-class-distribution-routes.md#errata).
- "Generic" means the six fields select a **named handler** — manifest projector,
  admission policy, marketplace projector, lifecycle implementation, safety and
  diagnostic profile — not that all route behavior collapses into six string
  values. Route-specific code survives behind a registered handler; what must not
  survive is a route-name conditional in shared code.
- Some current behavior is not expressible by the six fields as they stand and
  needs either a registered handler or a new contract field. Known cases:
  default-build recipe membership and order; recipe names and the CLI
  adapter-target mapping; legacy `--emit-install-routes` inclusion; canonical
  primitive source paths; route-specific filesystem and sanitized-diagnostic
  policy; the Claude manifest, seed, and marker artifact paths; and build-check
  lifecycle-artifact expectations.
- `apm` and `claude-plugins` both declare `lifecycle-trigger =
  "session-start-install-marker"` yet need different commands, roots, and scope
  detection — `packages/agentbundle/templates/install-marker.py:825` branches on
  route name to tell them apart. The declared value alone cannot select the
  implementation, so the registry must key lifecycle on a handler, or the
  contract must distinguish the two triggers.
- Published bytes do not change. The Claude and APM golden fixtures the brief
  requires across Phase 0 and Phase 2, and the Agent Plugin determinism the
  Phase 1A spec established, all still hold afterwards.
- The registry must fail closed on an unknown projector, policy, or handler name
  and on an inconsistent route declaration, rather than falling through to a
  default.

## Source

- Mode: repo-origin
- Locator: docs/product/briefs/distribution-routes-programme.md
- Revision: sha256-bytes-v1:b8daba8a937964f1cc37233cd613cdc8993d53bdcf64bc580ea7799e4741829d
