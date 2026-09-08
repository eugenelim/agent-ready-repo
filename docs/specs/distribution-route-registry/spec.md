# Spec: Distribution route registry

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0092](../../rfc/0092-first-class-distribution-routes.md)
  - [ADR-0090](../../adr/0090-distribution-routes-separate-from-runtime-adapters.md)
  - [`distribution-route-contract`](../distribution-route-contract/spec.md) (Shipped)
  - [`portable-agent-plugin-projection`](../portable-agent-plugin-projection/spec.md) (Shipped)
- **Brief:** docs/product/briefs/distribution-routes-programme.md
- **Intent:** docs/product/intents/distribution-route-registry.md
- **Discovery:** none
- **Contract:** `contracts/distribution-routes.toml` (read; not modified)
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Every surface that consumes distribution routes takes its route set from
`contracts/distribution-routes.toml`, and no shared build-time code selects behavior
by a route's name.

The `agent-plugin` route is therefore complete: every one of the fifteen surfaces
carries it, each because it reads the contract rather than a hand-maintained list, so
the same omission cannot recur for a later route.
[`notes/agent-plugin-surface-gaps.md`](notes/agent-plugin-surface-gaps.md) enumerates
the fifteen surfaces and which carry the route before this change.

Published output, refusal behavior, admission decisions, and install state are
unchanged. The route contract and its JSON Schema are read, never modified.

## Boundaries

### Always do

- Keep the complete `dist/apm/`, `dist/claude-plugins/`, and `dist/agent-plugins/`
  trees byte-identical, compared on paths, regular-file bytes, symlink targets, and
  mode bits.
- Take every route attribute from `contracts/distribution-routes.toml`. A value the
  contract carries is read, not re-stated in code.
- Preserve each route's existing filesystem, symlink, and diagnostic behavior. Where
  routes differ today — the Agent Plugin path uses the blessed
  `agentbundle.catalogue_tooling.file_safety` helpers, the generic path does not —
  each route keeps its own, and the stricter is never lowered to the weaker.

### Ask first

- Change any published package byte, output path, marketplace envelope, or
  install-state route identity.
- Add a dependency, a top-level directory, or a public command or flag.
- Change the `--install-route` values the install-marker template accepts.

### Never do

- Modify `contracts/distribution-routes.schema.json`. Opening the route set is a
  separate slice; see Follow-ons.
- Add MCP authoring, validation, install, or projection behavior.
- Emit a Codex plugin package, a Kiro Power profile, or any fourth route.
- Change the bytes or runtime behavior of
  `packages/agentbundle/templates/install-marker.py`. It ships inside both package
  trees and already-installed clients execute it.
- Infer a route from a recipe name, adapter name, output path, or comment.
- Let a generated manifest, marketplace, or projection become an authoring source.
- Delete a regression test because the change makes its assertion false; rewrite it.
- Regenerate a golden fixture after its capture commit.

## Testing Strategy

- **Preservation is proved by existing tests staying green, unmodified.** For every
  behavior this slice relocates rather than changes — refusals, path and symlink
  controls, diagnostics, admission, install state — the shipped tests are the oracle.
  Enumerating those behaviors again here would restate them in a second place that
  can drift, and would risk describing them wrongly.
- **Completion is proved by set equality.** Each surface's route set is compared
  against the contract's declared set, so the assertion holds for any declared route
  rather than naming three.
- **Byte invariance** compares complete built trees for all three routes against
  goldens captured before the change, on paths, bytes, symlink targets, and modes.
- **TDD** covers the new lookup and the surfaces being derived. **Goal-based checks**
  cover the branch inventory, contract parity, and `make build-check`. **Manual QA**
  runs one full catalogue build through the CLI.

## Acceptance Criteria

- [x] **AC1 — every route-consuming surface's route set equals the declared set.** For
  each surface below, the routes it recognises are compared against the set declared
  in `contracts/distribution-routes.toml`, so the assertion is about agreement with
  the contract rather than about three particular names. Before this change
  `agent-plugin` appeared on the first row only; the sites below are its
  pre-change locations, which is how the audit found them.

  | Surface | Site |
  | --- | --- |
  | Default build recipes | `build/main.py:402` |
  | Pack-declarable recipes | `commands/validate.py:37` |
  | Install-route emission | `commands/install.py:59` |
  | Install route discovery | `commands/install.py:1908` |
  | Install pack subtree paths | `commands/install.py:2451` |
  | Install subtree roots | `commands/install.py:2591` |
  | Install subtree iteration | `commands/install.py:2619` |
  | Install dist-tree detection | `commands/install.py:1380` |
  | Diff dist-tree detection | `commands/diff.py:160` |
  | Upgrade dist-tree detection | `commands/upgrade.py:84` |
  | Render targets | `commands/render.py:136` |
  | Catalogue verification roots | `catalogue_tooling/verify.py:1348` |
  | Build-check output checks | `build/self_host.py:1607` |
  | Route capability lint | `build/lint_packs.py:517` |
  | Byte-invariance goldens | `tests/fixtures/distribution-routes/golden.json` |

  Surfaces that also carry non-route members — `commands/render.py:136` admits
  runtime-adapter targets — are compared on their route-derived members only, with
  the others pinned unchanged. `templates/install-marker.py` is excluded because
  `agent-plugin` declares `lifecycle-trigger = "none"`; the test derives that
  exclusion from the contract rather than hard-coding it.

- [x] **AC2 — no shared build-time code selects behavior by a route's name.** Every
  route decision in shipped, non-test code is obtained from the contract. Route-specific
  code is permitted only in a module that serves exactly one route, and shared code
  reaches it through the contract-derived lookup rather than by naming the route.

  Two properties must both hold, and a check that establishes only the first is
  insufficient: no shared module names a route, **and** each relocated decision
  demonstrably comes from the contract — a decision that compares a contract-derived
  value in shared code is the same defect without the literal. The evidence must be
  reproducible against a recorded pre-change baseline, and must fail if a route
  decision is reintroduced into shared code by either form. How that evidence is
  produced is a build-time choice recorded in the plan.

  The evidence is a bounded static check, and its bound is part of this criterion
  rather than a defect in it. The literal form is covered wherever it is written. The
  contract-derived-value form is covered where the route types are annotated, which is
  module-local: a route value handed across a module boundary reaches its consumer
  untainted. The check records that bound in its own `limits`, and closing it is the
  separate `route-decision-analysis-depth` intent — attempting it inside this slice
  produced four review rounds whose findings were dominated by the previous round's
  fixes. What this criterion requires is that both forms fail the check within the
  stated bound, that every exemption the check grants is derived from a declaration
  rather than a maintained list, and that the bound is recorded rather than implied.

- [x] **AC3 — each surface's observable change is completion, and is pinned.** Taking a
  route set from the contract changes what several surfaces do for `agent-plugin`,
  because they currently exclude it. Every such change is recorded before and after, and
  each is an *inclusion* of an already-declared route — never a change to what a surface
  does for `apm` or `claude-plugins`, and never a new capability.

  The implementing PR states, per surface it derives, whether the route set it exposes
  changes and what the before and after sets are. At minimum: a pack declaring the
  portable recipe is rejected before and accepted after; the install-route emission
  gains an entry while its existing outputs stay byte-identical; the render target set
  gains the portable target with its adapter targets unchanged; `catalogue verify`
  reports a defect planted in the `agent-plugins` tree that it ignores before; and the
  install, diff, and upgrade dist-tree detections recognise a portable install that they
  do not recognise before. Any further surface whose route set changes is recorded the
  same way rather than left unstated.

- [x] **AC4 — published bytes are unchanged for all three routes.** Goldens captured
  before any change pin the complete `dist/apm/`, `dist/claude-plugins/`, and
  `dist/agent-plugins/` trees on paths, regular-file bytes, symlink targets, and mode
  bits. The shipped `tests/fixtures/distribution-routes/golden.json` covers only the
  first two, so the Agent Plugin tree is captured and the comparison extended. Two
  conditions make that capture meaningful. First, the goldens are shown to reproduce
  from production code that predates every behavioral change — the implementing PR
  names the base commit and the re-runnable procedure that demonstrates it, since this
  slice lands as one unit and so has no per-task capture commit to cite. Second, the
  witness corpus admits at least one portable-eligible pack whose eligibility is
  intentional rather than incidental: `repo-only` is admitted today and contributes
  two entries, so a non-empty tree alone would not show that the route's admission was
  exercised on purpose. Killing mutation: alter one byte of any pinned output.

- [x] **AC5 — every behavior this slice relocates is unchanged, proved by its own
  shipped tests.** The refusals of the shipped `distribution-route-contract`, the
  filesystem, symlink, and diagnostic controls of the shipped
  `portable-agent-plugin-projection`, the admission outcomes of
  `pack_is_publishable`, and the recorded install-state route identities all keep
  their existing tests, which run unmodified against the relocated code and stay
  green. A relocation that requires editing one of those tests to pass fails this
  criterion; the test is the contract and the diff must not move it.

  Green alone is not the evidence — an unchanged tree is also green. The criterion binds
  to the sites the pre-change enumeration records: for each decision this slice
  relocates, the implementing PR names the shipped test that proves the behavior and
  shows that test exercising the relocated path, not the path it replaced. A behavior
  whose site moved but whose test never reaches the new path is unproven and fails this
  criterion.

  One class is carved out, because it asserts a boundary this slice supersedes rather
  than a behavior it preserves: a shipped test whose subject is the *absence* of the
  dispatch layer this slice adds. `test_distribution_routes_have_no_registration_surface`
  at `test_distribution_route_resolution.py:170` is such a test — it asserts
  `build_main` exposes no `ROUTE_REGISTRY` or `register_distribution_route`, which the
  shipped `distribution-route-contract` spec wrote as a Phase-0 boundary while naming
  this slice as generic dispatch's owner. It is **rewritten, not deleted**, to assert
  the boundary that now applies: registration is explicit and internal, and no handler
  is discovered dynamically. The implementing PR names every test it rewrites under this
  carve-out and why the assertion it replaces is superseded; a behavioral or refusal
  test never qualifies.

- [x] **AC6 — a route's own controls survive relocation intact.** Where controls differ
  between routes, each route keeps its own. The implementing PR records, per route,
  which existing control it inherits and the shipped test that proves it, and a mutation
  pointing one route at another route's weaker control must fail that test.

- [x] **AC7 — a build that cannot resolve a route produces no output.** Route behavior
  for every route the build will process is resolved before the build creates its first
  output artifact, so an unresolvable route cannot leave a partially written tree behind.
  The test drives the default build with resolution failing for the route processed
  last, and asserts the output root is unchanged — including any route that would
  otherwise have been written first. A sentinel placed in the output root beforehand is
  untouched.

## Follow-ons

Out of scope by decision, not deferred at implementation time.

- **Opening the route set** — generalizing
  `contracts/distribution-routes.schema.json` so a route needs no schema entry, and
  proving extensibility with a synthetic fourth route and a synthetic capability.
  That work cannot be done here: `route.additionalProperties` is `false` and
  `route.required` names exactly the three shipped routes, and
  `build/main.py:1297` validates against the bundled schema, so no synthetic route can
  reach the production resolver while the schema is closed. Opening it also removes 33
  single-value pins per route that four of the eight shipped refusals rest on, which
  carries its own confinement and compatibility obligations. Owner: eugenelim; tracked
  by `docs/product/intents/distribution-route-set-opening.md`. It lands before Phase 3.
- **Canonical primitive source paths** (`build/main.py:101` and the skill skip at
  `:495`) map a primitive to its authoring source, which is primitive ownership rather
  than route dispatch. Owner: eugenelim; tracked by
  `docs/product/intents/canonical-mcp-install-parity.md`.

## Assumptions

- Technical: fifteen surfaces consume route names and fourteen omit `agent-plugin`
  (source: `notes/agent-plugin-surface-gaps.md`).
- Technical: the resolver restates contract values as literals, and three of the six
  resolved concerns are stored and barely consumed (source:
  `build/main.py:1238-1345`).
- Technical: `apm` and `claude-plugins` declare the same `lifecycle-trigger` while
  needing different build-time behavior (source:
  `contracts/distribution-routes.toml:13,50`; `templates/install-marker.py:807,825`).
- Technical: the route schema is closed — `route.additionalProperties` is `false`,
  `route.required` is exactly the three shipped routes, and the resolver validates
  against the bundled copy at `build/main.py:1297`.
- Technical: `golden.json` covers `apm` and `claude-plugins` only, and
  `test_distribution_route_golden.py:124` asserts exactly those two keys.
- Technical: `pack_is_publishable` at `build/main.py:1476` returns a boolean, so an
  excluded pack is skipped rather than failing the build, and hook consent applies
  only through `check_hooks` when a pack carries hooks needing it (`:1490`).
- Technical: filesystem controls differ per route (source: `build/main.py:486,1365,1407`).
- Governance: the shipped `distribution-route-contract` places the generic registry
  under *Never do* and names this slice as its owner.
- Governance: RFC-0092 D1 gates extraction on three real routes, and its 2026-09-03
  erratum orders this slice before the canonical MCP slice on `agent-plugin`
  completion grounds.
