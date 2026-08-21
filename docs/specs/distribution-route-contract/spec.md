# Spec: Distribution route contract

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0092](../../rfc/0092-first-class-distribution-routes.md)
  - [ADR-0090](../../adr/0090-distribution-routes-separate-from-runtime-adapters.md)
- **Brief:** docs/product/briefs/distribution-routes-programme.md
- **Discovery:** none
- **Contract:** `contracts/distribution-routes.toml`; `contracts/distribution-routes.schema.json`; removes route ownership from `contracts/adapter.toml` and `contracts/adapter.schema.json`
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A catalogue maintainer can identify the APM and Claude plugin package formats as
distribution routes owned independently of runtime adapters. Each route has one
schema-validated declaration, each build recipe names its route explicitly, and a
minimal fail-closed resolver selects the existing named projector. Direct
`agentbundle` installation keeps its existing adapter semantics, while the complete
APM and Claude plugin output trees remain byte-for-byte identical.

## Boundaries

### Always do

- Keep the complete `dist/apm/` and `dist/claude-plugins/` trees byte-identical to
  their checked-in pre-migration golden fixtures, including file contents, relative
  paths, symlinks, and executable modes.
- Keep every canonical route and adapter TOML/schema file byte-identical to its
  packaged `agentbundle/_data/` copy and list every new public contract in the
  packaged contract inventory.
- Use only Python's standard library, validate the route contract before dispatch,
  resolve recipes by explicit route identity, and fail closed on unknown,
  incomplete, or inconsistent route declarations.
- Keep `contracts/README.md`, the route/adapter architecture vocabulary, and
  AgentBundle release records synchronized with the contract.

### Ask first

- Add a read-through compatibility alias or deprecation window if an external
  consumer of `adapter.toml`'s `install-routes` field is discovered.
- Add any dependency, top-level directory, or public command/flag.
- Add Phase 1 behavior: a new package route, a new canonical primitive, a new
  output directory, or a changed support claim.

### Never do

- Build the generic distribution-route registry; Phase 2 owns generic dispatch.
- Emit portable Agent Plugin, Codex plugin, or Kiro Power packages, or add MCP
  authoring/install behavior.
- Infer a route from a recipe name, adapter name, output path, or comment, or let
  generated output become an authoring source.
- Change the direct-install route identity recorded by existing install markers,
  or model direct `agentbundle install` as a distribution route.

## Testing Strategy

- **TDD** covers route-contract schema validation, recipe parsing, minimal route
  resolution, projector selection, and every malformed/unknown/mismatched input.
  These behaviors have compact invariants and must refuse before writing output.
- **Goal-based integration checks** compare complete APM and Claude plugin builds
  against golden trees captured from the unmodified implementation. The comparison
  includes paths, regular-file bytes, symlink targets, and mode bits; a summary or
  selected-file assertion is insufficient.
- **Goal-based checks** enforce canonical/bundled contract parity, public-contract
  inventory parity, documentation references, coordinated package versions, and
  the normal repository gates.
- **Manual QA** runs the normal catalogue build once through the CLI and records
  that only the existing `apm`, `claude-plugins`, and marketplace outputs appear.
  No external client or browser check is required because this slice changes no
  client-facing package bytes.
- **Construction-test coverage:** materialized red Python tests cover AC1,
  AC3-AC6, AC8-AC9, and AC14; goal-based checks for AC2, AC7, and AC10-AC13
  are recorded in their owning plan tasks and intentionally have no standalone
  stub.

## Acceptance Criteria

- [x] **AC1 — route-owned public contract.**
  `contracts/distribution-routes.toml` declares exactly the existing `apm` and
  `claude-plugins` distribution routes, and
  `contracts/distribution-routes.schema.json` validates it as a closed shape.
  Every route declaration contains exactly the six RFC-0092 concerns:
  `identity`, `package-layout`, `manifest-projector`,
  `component-capabilities`, `marketplace-projector`, and
  `lifecycle-trigger`. The capability map has exactly the nine Phase 0 canonical
  primitives: `skill`, `agent`, `command`, `hook-body`, `hook-wiring`,
  `kiro-ide-hook`, `shared-libs`, `adapter-root-bins`, and `user-libs`. It records
  the actual pre-migration output: APM is `native` for all nine; Claude plugins
  are `native` for `skill`, `agent`, `command`, `hook-body`, and `hook-wiring`,
  and `dropped` for `kiro-ide-hook`, `shared-libs`, `adapter-root-bins`, and
  `user-libs`. Values with no projector or trigger use an explicit closed
  sentinel rather than omission or `unknown`. `manifest-projector` is a closed object containing `name`,
  `adapter-projector`, and `admission-policy`: it is the one field that permits
  the optional runtime-adapter projector and selects `all-packs` for APM or the
  existing user-publishable/consent admission policy for Claude plugins.
- [x] **AC2 — route ownership leaves adapters.** `install-routes` and the
  Claude-plugin-only `plugin-target-path` / `plugin-mode` fields are absent from
  `contracts/adapter.toml`, absent from `contracts/adapter.schema.json`, and
  absent from their bundled copies. The contract tests that pin those fields are
  rewritten to assert route ownership and adapter-route separation; no regression
  test is deleted merely because the old assertion becomes false.
- [x] **AC3 — explicit recipe identity.** `Recipe` has a required `route` for
  distribution recipes. The bundled APM per-pack recipe declares
  `route = "apm"`; the Claude per-pack and marketplace recipes declare
  `route = "claude-plugins"`. A route-bearing
  recipe may name an adapter projector only when its route declaration permits
  that adapter; missing routes, unknown routes, adapter mismatches, and non-route
  recipes carrying route-only fields fail with diagnostics naming the recipe and
  offending field before any output directory is created.
- [x] **AC4 — minimal resolver, not a registry.** A single minimal resolver reads
  the validated route declaration and maps `apm` and `claude-plugins` to their
  existing named projectors. No declared route becomes generically buildable, no
  plug-in registration API exists, and route-specific build code remains named
  until the Phase 2 registry slice.
- [x] **AC5 — APM is route-owned.** APM package-writer selection, package layout,
  and install-marker injection are selected through the `apm` route declaration;
  no `adapter == "apm"` bypass or fabricated APM runtime adapter remains. The
  emitted marker command and its `--install-route apm` value are unchanged.
- [x] **AC6 — Claude packaging is route-owned.** Claude plugin layout,
  component-mode overrides, publishability filtering, hook compilation, marker
  injection, and marketplace selection are selected through the
  `claude-plugins` route declaration. Runtime Claude direct-install projections
  remain in the adapter contract and route code does not mutate adapter contract
  rows in memory.
- [x] **AC7 — direct installation is unchanged.** Every existing direct
  `agentbundle install` adapter, scope, output path, seed behavior, and install
  marker value behaves as before. `cli` remains the existing marker/install
  identity and is not declared as a distribution route.
- [x] **AC8 — byte-for-byte route parity.** Deterministic pre-migration golden
  fixtures cover complete representative APM and Claude plugin output trees,
  including a user-publishable pack with skills, agents, commands, hooks, marker,
  manifest, README, and seeds plus a repo-only exclusion case. The post-migration
  build matches the fixtures exactly by relative path, bytes, symlink target, and
  mode. A second build produces the same comparison result.
- [x] **AC9 — negative coverage is exhaustive at the boundary.** Tests reject an
  unknown route, a route missing each of the six required concerns, an unknown
  support status, a capability-map omission, an unknown projector, a recipe with
  no route when it invokes a default distribution projector, a route/adapter
  mismatch, and a route whose layout, admission, or lifecycle declaration
  conflicts with its named projector. Non-distribution overlay, composite, and
  self-host recipes remain valid without `route`. Every refusal happens before
  output mutation and names the route or recipe.
- [x] **AC10 — public contract packaging is synchronized.** The two new contract
  files have byte-identical copies under
  `packages/agentbundle/agentbundle/_data/`, appear in
  `public-contracts.txt`, and pass `tools/catalogue/check_contract_parity.py`.
  `contracts/README.md` and the current architecture reference identify routes
  and adapters as sibling consumers of the normalized pack model. RFC-0092 P6
  carries an approver-signed erratum correcting the three Claude library/binary
  cells that claimed `native` despite no corresponding Phase 0 projection; the
  erratum points to the golden evidence and changes no behavior.
- [x] **AC11 — bounded release.** The AgentBundle package receives the next
  available minor version consistently in `pyproject.toml` and `version.py`, with
  package and product changelog entries describing the new public route contract
  and explicitly stating that direct-install and published route outputs are
  unchanged. No pack version or marketplace entry version changes.
- [x] **AC12 — Phase 0 stays Phase 0.** The diff adds no portable or native plugin
  package output, MCP primitive, generic registry, Codex/Kiro/Copilot route,
  publisher workflow, external dependency, or generated-authoring input. The
  normal catalogue build emits no new top-level output directory.
- [x] **AC13 — verification gates.** Focused route-contract/build tests, the full
  `packages/agentbundle` test suite, contract parity, Ruff, build-self drift,
  build-check, and spec-status lint pass. The implementing commit carries the
  package-scoped `Engine-Change-RFC: RFC-0092` footer required by package
  instructions.
- [x] **AC14 — route resolution preserves the filesystem safety boundary.**
  Route and adapter contracts are decoded only with `tomllib` / `json`, validated
  before use, and never interpreted as code. Route-owned package layout is the
  sole output-path authority: recipe layout fields must match it exactly, closed
  route values cannot introduce arbitrary destinations, and every derived output
  remains confined beneath the caller-selected output root before mutation. The
  APM writer continues to preserve confined relative source symlinks as links
  without reading their targets; both route writers refuse symlinked copy roots
  and absolute or escaping nested source links before output mutation. Claude
  projection continues to refuse or skip unsafe links at its established read
  boundaries. Phase 0 neither dereferences links into package bytes nor changes
  the established hard-link/reparse-point behavior. Tests cover traversal,
  absolute and symlink-parent route-layout attempts, source-root and nested-link
  escapes, refusal before output mutation, and the characterized safe-link
  semantics.

## Assumptions

- Technical: APM and Claude plugin packaging are currently dispatched through
  adapter-shaped special cases, and `Recipe` has no route field (source:
  `packages/agentbundle/agentbundle/build/main.py` and bundled recipe TOML files,
  inspected 2026-08-21).
- Technical: `install-routes`, `plugin-target-path`, and `plugin-mode` are owned by
  the Claude adapter contract and its closed schema (source:
  `contracts/adapter.toml`, `contracts/adapter.schema.json`, and
  `packages/agentbundle/tests/build_pipeline/test_contract.py`, inspected
  2026-08-21).
- Technical: catalogue contracts are published TOML/JSON-Schema interfaces with
  mandatory byte-identical packaged copies (source: `contracts/README.md`,
  `tools/catalogue/check_contract_parity.py`, and `ARCHITECTURE.md`).
- Technical: AgentBundle production code is standard-library-only and this slice
  spans data, service, and integration behavior (source:
  `packages/agentbundle/AGENTS.md`; repository inspection 2026-08-21).
- Process: RFC-0092 and ADR-0090 settle the route/adapter separation and defer the
  generic registry until three real routes exist (source:
  `docs/rfc/0092-first-class-distribution-routes.md` and
  `docs/adr/0090-distribution-routes-separate-from-runtime-adapters.md`).
- Governance conflict: RFC-0092 P6 labels Claude plugin `shared-libs`,
  `adapter-root-bins`, and `user-libs` as `native`, while the Claude adapter
  projection array and projector emit none of those primitives. The
  user-confirmed zero-output Phase 0 boundary makes the current output the
  contract and requires an approver-signed RFC erratum rather than implementation
  by surprise (source: `contracts/adapter.toml`,
  `packages/agentbundle/agentbundle/build/adapters/claude_code.py`, adversarial
  review, and user confirmation 2026-08-21).
- Product: Phase 0 is independently shippable, changes no Claude/APM output, and
  excludes portable projection, MCP, and registry work (source: user confirmation
  2026-08-21).
- Contract: the durable public contract is
  `contracts/distribution-routes.toml` plus
  `contracts/distribution-routes.schema.json` (source: user confirmation
  2026-08-21).
- Boundaries: byte parity and contract parity are mandatory; aliases,
  dependencies, and Phase 1 behavior require approval; generic registry and new
  route/primitive/install behavior are prohibited (source: user confirmation
  2026-08-21).
